"""The simulation object and main loop (the ``cctkGH`` + flesh driver).

Lifecycle (compare with the Cactus flesh):

1. Activate the core thorns plus ``ActiveThorns`` (and whatever they require).
2. Declare every active thorn's parameters and apply the parfile values.
3. Build the grid (``CoordBase``/``Driver`` parameters) and the time step.
4. ``setup()`` each thorn (allocate grid functions), then ``schedule()``.
5. Run ``STARTUP .. POSTINITIAL``, then ``ANALYSIS``/``OUTPUT`` at iteration 0.
6. Loop ``PRESTEP, EVOL, POSTSTEP, ANALYSIS, OUTPUT`` until termination.
7. Run ``TERMINATE`` and print a timing summary.
"""

from __future__ import annotations

import os
import time as _time

from pynr.cactus.grid import UniformGrid
from pynr.cactus.gridfunctions import GridFunctions
from pynr.cactus.params import Parameters
from pynr.cactus.parfile import parse_parfile, parse_parfile_text
from pynr.cactus.schedule import Schedule
from pynr.cactus.thorn import THORNS, Thorn

CORE_THORNS = ("Cactus", "CoordBase", "Driver", "Time", "IO")


class Simulation:
    """A configured simulation. Build one with :meth:`from_parfile`."""

    def __init__(self, entries: dict, name: str = "simulation", parfile_text: str | None = None,
                 verbose: bool = True):
        import pynr.thorns  # noqa: F401  (registers all thorns)

        self.name = name
        self.verbose = verbose
        self.iteration = 0
        self.time = 0.0
        self.aborted: str | None = None
        self.params = Parameters()
        self.schedule = Schedule()
        self.gf = GridFunctions(self)
        self._timers: dict[str, float] = {}
        self._logfile = None

        # 1. activation --------------------------------------------------
        self.thorns: dict[str, Thorn] = {}
        for tname in (*CORE_THORNS, *entries.get("activethorns", [])):
            self._activate(tname)

        # 2. parameters -----------------------------------------------------
        for key, val in entries.items():
            if key != "activethorns":
                self.params.set(key, val)

        # 3. grid, time step, backend, output dir ---------------------------
        cb, drv = self.params.of("CoordBase"), self.params.of("Driver")
        self.grid = UniformGrid(
            (cb.xmin, cb.ymin, cb.zmin), (cb.xmax, cb.ymax, cb.zmax), (cb.dx, cb.dy, cb.dz),
            nghost=drv.ghost_size, periodic=(cb.periodic_x, cb.periodic_y, cb.periodic_z),
        )
        tm = self.params.of("Time")
        self.dt = tm.timestep if tm.timestep_method == "given" else tm.dtfac * float(self.grid.dx.min())
        self.backend = drv.backend

        self.out_dir = self.params.get("IO", "out_dir") or name
        os.makedirs(self.out_dir, exist_ok=True)
        self._logfile = open(os.path.join(self.out_dir, "pynr.log"), "w")
        if parfile_text is not None:
            with open(os.path.join(self.out_dir, f"{name}.par"), "w") as fh:
                fh.write(parfile_text)
        with open(os.path.join(self.out_dir, "parameters.par"), "w") as fh:
            fh.write(self.params.dump())

        # 4. setup + schedule ----------------------------------------------
        for t in self.thorns.values():
            t.setup()
        for t in self.thorns.values():
            t.schedule(self.schedule)

        self.log(f"pyNR simulation '{name}': {len(self.thorns)} thorns active")
        self.log(f"  {self.grid}, dt = {self.dt:g}, backend = {self.backend}")
        self.log("Schedule:\n" + self.schedule.describe())

    # ------------------------------------------------------------------ #
    @classmethod
    def from_parfile(cls, path, overrides: dict | None = None, **kw) -> Simulation:
        """Create a simulation from a ``.par`` file.

        ``overrides`` maps ``"Thorn::param"`` to values that replace the file's
        (handy in notebooks and tests, e.g. ``{"Cactus::cctk_itlast": 10}``).
        """
        entries = parse_parfile(path)
        for k, v in (overrides or {}).items():
            entries[k.lower()] = v
        name = os.path.splitext(os.path.basename(str(path)))[0]
        with open(path) as fh:
            text = fh.read()
        return cls(entries, name=name, parfile_text=text, **kw)

    @classmethod
    def from_string(cls, text: str, name: str = "simulation", overrides: dict | None = None, **kw):
        entries = parse_parfile_text(text, name)
        for k, v in (overrides or {}).items():
            entries[k.lower()] = v
        return cls(entries, name=name, parfile_text=text, **kw)

    def _activate(self, tname: str) -> None:
        key = tname.lower()
        if key in self.thorns:
            return
        if key not in THORNS:
            raise KeyError(f"Unknown thorn '{tname}'. Available: {sorted(c.name for c in THORNS.values())}")
        cls = THORNS[key]
        for req in cls.requires:
            self._activate(req)
        self.params.declare(cls.name, cls.parameters)
        self.thorns[key] = cls(self)

    def thorn(self, name: str) -> Thorn:
        return self.thorns[name.lower()]

    def has_thorn(self, name: str) -> bool:
        return name.lower() in self.thorns

    # ------------------------------------------------------------------ #
    def log(self, msg: str) -> None:
        if self.verbose:
            print(msg, flush=True)
        if self._logfile:
            self._logfile.write(msg + "\n")
            self._logfile.flush()

    def _run_bin(self, b: str) -> None:
        t0 = _time.perf_counter()
        self.schedule.run(b)
        self._timers[b] = self._timers.get(b, 0.0) + _time.perf_counter() - t0

    def initialize(self) -> None:
        for b in ("STARTUP", "BASEGRID", "INITIAL", "POSTINITIAL", "ANALYSIS", "OUTPUT"):
            self._run_bin(b)

    def step(self) -> None:
        self._run_bin("PRESTEP")
        self._run_bin("EVOL")  # MoL integrates from self.time to self.time + dt
        self.iteration += 1
        self.time += self.dt
        for b in ("POSTSTEP", "ANALYSIS", "OUTPUT"):
            self._run_bin(b)

    def done(self) -> bool:
        c = self.params.of("Cactus")
        by_it = self.iteration >= c.cctk_itlast
        by_t = self.time >= c.cctk_final_time - 1e-10 * self.dt
        return {"never": False, "iteration": by_it, "time": by_t, "either": by_it or by_t}[c.terminate]

    def run(self) -> Simulation:
        """Set up initial data, then :meth:`evolve` to the end."""
        self._t0 = _time.perf_counter()
        self.initialize()
        return self.evolve()

    def evolve(self) -> Simulation:
        """Step until termination (or a blow-up), then run ``TERMINATE``.

        Call it yourself after :meth:`initialize` to modify the initial data
        in between (e.g. in a notebook).
        """
        t0 = getattr(self, "_t0", None) or _time.perf_counter()
        try:
            while not self.done():
                self.step()
        except FloatingPointError as err:
            self.log(f"ABORT: {err}")
            self.aborted = str(err)
        self._run_bin("TERMINATE")
        wall = _time.perf_counter() - t0
        self.log(f"Done: iteration {self.iteration}, t = {self.time:g}, wall time {wall:.2f} s")
        for b, t in self._timers.items():
            self.log(f"  {b:12s} {t:9.3f} s")
        if self._logfile:
            self._logfile.close()
            self._logfile = None
        self._t0 = None
        return self
