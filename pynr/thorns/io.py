"""Output thorns writing Einstein Toolkit (Carpet) formats, so kuibit reads pyNR runs as-is.

IOHDF5 — grid functions (CarpetIOHDF5 layout)
    One file per variable: ``alp.xyz.h5`` (3D) and ``alp.xy.h5``,
    ``alp.xz.h5``, ``alp.yz.h5`` (2D planes through the point nearest the
    origin). Each output time is a dataset named
    ``"ADMBASE::alp it=<it> tl=0 rl=0 c=0"`` with attributes ``origin``,
    ``delta``, ``time``, ``timestep``, ``level``, ``iorigin``,
    ``cctk_nghostzones``. Data are stored with ``x`` fastest-varying, as
    Carpet does (C-order array ``[z, y, x]``). The files include the outer
    boundary (ghost) points, as Carpet files include ET boundary points.

IOScalar — reductions (CarpetIOScalar ASCII)
    ``alp.maximum.asc``, ``alp.minimum.asc``, ``alp.norm2.asc`` with columns
    ``iteration time value``. Reductions use interior points only.

IOBasic — a progress table on stdout.

Reading a run with kuibit::

    from kuibit.simdir import SimDir
    sd = SimDir("gauge_wave")
    alp = sd.gf.xyz["alp"]            # 3D
    sd.ts.maximum["alp"]              # time series
    sd.gws[20.0][(2, 2)]              # Psi4 multipole at r = 20
"""

from __future__ import annotations

import os

import h5py
import numpy as np

from pynr.cactus import Param, Thorn, register_thorn


def _every(n: int, it: int) -> bool:
    return n > 0 and it % n == 0


@register_thorn
class IOHDF5(Thorn):
    name = "IOHDF5"
    parameters = {
        "out_every": Param(0, "3D output every N iterations (0 = off)"),
        "out_vars": Param("", "Variables/groups for 3D output"),
        "out2D_every": Param(0, "2D output every N iterations (0 = off)"),
        "out2D_vars": Param("", "Variables/groups for 2D output"),
        "out2D_planes": Param("xy xz yz", "Which planes to write"),
    }

    def setup(self):
        gf = self.sim.gf
        self._written: set[str] = set()
        self.vars3d = gf.expand(self.p.out_vars) if self.p.out_vars else []
        self.vars2d = gf.expand(self.p.out2D_vars) if self.p.out2D_vars else []

    def schedule(self, S):
        S.add("OUTPUT", self.output)

    def _open(self, fname):
        path = os.path.join(self.sim.out_dir, fname)
        if path in self._written:
            return h5py.File(path, "a")
        self._written.add(path)
        fh = h5py.File(path, "w")
        # Carpet stores the run's parameters here; kuibit reads it to decide
        # whether ghost zones are in the file. Our ghost points are outer
        # boundary points (which Carpet always writes), not inter-process ghosts.
        grp = fh.create_group("Parameters and Global Attributes")
        grp.attrs["nioprocs"] = np.int32(1)
        pars = self.sim.params.dump() + 'CarpetIOHDF5::output_ghost_points = "no"\n'
        grp.create_dataset("All Parameters", data=np.frombuffer(pars.encode(), dtype=np.uint8))
        return fh

    def _dataset(self, fh, full, data, origin, delta, iorigin):
        thorn, var = full.split("::")
        name = f"{thorn.upper()}::{var} it={self.sim.iteration} tl=0 rl=0 c=0"
        if name in fh:
            del fh[name]
        ds = fh.create_dataset(name, data=np.ascontiguousarray(data.T))
        ds.attrs["origin"] = np.asarray(origin, float)
        ds.attrs["delta"] = np.asarray(delta, float)
        ds.attrs["iorigin"] = np.asarray(iorigin, np.int32)
        ds.attrs["time"] = float(self.sim.time)
        ds.attrs["timestep"] = np.int32(self.sim.iteration)
        ds.attrs["level"] = np.int32(0)
        ds.attrs["cctk_nghostzones"] = np.zeros(len(origin), np.int32)
        ds.attrs["cctk_bbox"] = np.ones(2 * len(origin), np.int32)
        ds.attrs["name"] = np.bytes_(f"{thorn.upper()}::{var}")

    def output(self):
        sim, g = self.sim, self.sim.grid
        if _every(self.p.out_every, sim.iteration):
            for full in self.vars3d:
                arr = sim.gf.get(full, fresh=True)
                with self._open(f"{full.split('::')[1]}.xyz.h5") as fh:
                    self._dataset(fh, full, arr, g.origin, g.dx, [0, 0, 0])
        if _every(self.p.out2D_every, sim.iteration):
            centre = [g.nearest_index(0.0, d) for d in range(3)]
            for full in self.vars2d:
                arr = sim.gf.get(full, fresh=True)
                for plane in self.p.out2D_planes.split():
                    dims = ["xyz".index(c) for c in plane]
                    normal = ({0, 1, 2} - set(dims)).pop()
                    sl = [slice(None)] * 3
                    sl[normal] = centre[normal]
                    with self._open(f"{full.split('::')[1]}.{plane}.h5") as fh:
                        self._dataset(fh, full, arr[tuple(sl)], g.origin[dims], g.dx[dims],
                                      [0, 0])


@register_thorn
class IOScalar(Thorn):
    name = "IOScalar"
    parameters = {
        "outScalar_every": Param(0, "Reduction output every N iterations (0 = off)"),
        "outScalar_vars": Param("", "Variables/groups to reduce"),
        "outScalar_reductions": Param("minimum maximum norm2", "Reductions to compute"),
    }
    REDUCTIONS = {
        "minimum": np.min,
        "maximum": np.max,
        "norm1": lambda a: np.mean(np.abs(a)),
        "norm2": lambda a: np.sqrt(np.mean(a * a)),
        "norm_inf": lambda a: np.max(np.abs(a)),
        "average": np.mean,
    }

    def setup(self):
        self.vars = self.sim.gf.expand(self.p.outScalar_vars) if self.p.outScalar_vars else []
        self.reds = self.p.outScalar_reductions.split()
        for r in self.reds:
            if r not in self.REDUCTIONS:
                raise ValueError(f"Unknown reduction '{r}'")
        self._written: set[str] = set()

    def schedule(self, S):
        S.add("OUTPUT", self.output)

    def output(self):
        sim = self.sim
        if not _every(self.p.outScalar_every, sim.iteration):
            return
        for full in self.vars:
            thorn, var = full.split("::")
            data = sim.gf.get(full, fresh=True)[sim.grid.interior]
            for r in self.reds:
                path = os.path.join(sim.out_dir, f"{var}.{r}.asc")
                first = path not in self._written
                with open(path, "w" if first else "a") as fh:
                    if first:
                        fh.write(f"# Scalar ASCII output created by pyNR\n# {thorn.upper()}::{var}\n"
                                 f"# 1:iteration 2:time 3:data\n# data columns: 3:{var}\n")
                        self._written.add(path)
                    fh.write(f"{sim.iteration} {sim.time:.15e} {self.REDUCTIONS[r](data):.15e}\n")


@register_thorn
class IOBasic(Thorn):
    name = "IOBasic"
    parameters = {
        "outInfo_every": Param(1, "Print every N iterations (0 = off)"),
        "outInfo_vars": Param("ADMBase::alp", "Variables whose min/max are printed"),
    }

    def setup(self):
        self.vars = self.sim.gf.expand(self.p.outInfo_vars) if self.p.outInfo_vars else []

    def schedule(self, S):
        S.add("OUTPUT", self.output)

    def output(self):
        sim = self.sim
        if not _every(self.p.outInfo_every, sim.iteration):
            return
        if sim.iteration == 0:
            head = f"{'it':>7} | {'t':>9}" + "".join(
                f" | {v.split('::')[1] + ' min':>12} {'max':>12}" for v in self.vars)
            sim.log(head)
            sim.log("-" * len(head))
        row = f"{sim.iteration:7d} | {sim.time:9.4f}"
        for v in self.vars:
            d = sim.gf.get(v, fresh=True)[sim.grid.interior]
            row += f" | {d.min():12.5e} {d.max():12.5e}"
        sim.log(row)
