# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
r"""Multipole: spin-weighted multipole decomposition on geodesic spheres.

For each extraction radius $R$ the complex field
$f = f_r + i f_i$ (e.g. $\Psi_4$) is interpolated to the points
of a geodesic sphere (:mod:`pynr.utils.geodesic`) and projected

$$
    f^{\ell m}(t, R) = \oint f\;{}_s\bar Y_{\ell m}\,d\Omega
                    \approx \sum_i w_i\, f(R\hat n_i)\;{}_s\bar Y_{\ell m}(\hat n_i).
$$ (eq-multipole-projection)

Output files use the ET Multipole ASCII format, which kuibit reads directly::

    mp_Psi4_l2_m0_r20.00.asc      # columns: time  Re  Im

``Multipole::variables`` follows the ET syntax::

    Multipole::variables = "WeylScal4::Psi4r{sw=-2 cmplx='WeylScal4::Psi4i' name='Psi4'}"

Choosing radii: the sphere must lie inside the grid (away from the outer
boundary by a few wavelengths) and far enough from the source that the
wave zone is reached, $R \gtrsim 10\text{-}20\,M$ for teaching runs.
Finite-radius $\Psi_4$ differs from the value at infinity by
$\mathcal{O}(1/R)$; extrapolate in $R$ or use kuibit's
Nakano perturbative extrapolation.
"""

from __future__ import annotations

import os
import re

import numpy as np

from pynr.cactus import Param, Thorn, register_thorn
from pynr.utils.geodesic import angles, geodesic_sphere
from pynr.utils.interpolation import interpolate
from pynr.utils.swsh import modes, sYlm

_VAR = re.compile(r"(?P<var>[\w:]+)\s*(?:\{(?P<opts>[^}]*)\})?")
_OPT = re.compile(r"(\w+)\s*=\s*('([^']*)'|\S+)")


def parse_variables(spec: str):
    """Parse ET Multipole ``variables`` strings into ``(real, imag|None, spin, name)``."""
    out = []
    for m in _VAR.finditer(spec):
        opts = {k: (q if q else v) for k, v, q in _OPT.findall(m.group("opts") or "")}
        real = m.group("var")
        out.append((real, opts.get("cmplx"), int(opts.get("sw", 0)),
                    opts.get("name", real.split("::")[-1])))
    return out


@register_thorn
class Multipole(Thorn):
    name = "Multipole"
    parameters = {
        "variables": Param("", "Variables to decompose (ET syntax)"),
        "nradii": Param(1, "Number of extraction radii"),
        "radius": Param(10.0, "Extraction radii", size=16),
        "l_max": Param(4, "Highest l"),
        "out_every": Param(1, "Output every N iterations (0 = never)"),
        "geodesic_level": Param(4, "Refinement level of the geodesic sphere (10*4^n+2 points)"),
        "interpolator_order": Param(3, "Lagrange interpolation order"),
        "center_x": Param(0.0, "Sphere centre x"),
        "center_y": Param(0.0, "Sphere centre y"),
        "center_z": Param(0.0, "Sphere centre z"),
    }

    def setup(self):
        p = self.p
        self.vars = parse_variables(p.variables)
        self.radii = [float(r) for r in p.radius[: p.nradii]]
        unit, _, self.weights = geodesic_sphere(p.geodesic_level)
        self.theta, self.phi = angles(unit)
        self.unit = unit
        g = self.sim.grid
        lo = g.origin + (g.nghost + p.interpolator_order) * g.dx
        hi = g.origin + (np.array(g.shape) - 1 - g.nghost - p.interpolator_order) * g.dx
        c = np.array([p.center_x, p.center_y, p.center_z])
        for R in self.radii:
            if np.any(c - R < lo) or np.any(c + R > hi):
                raise ValueError(f"Multipole radius {R} does not fit inside the grid interior")
        self._Ybar = {}
        for _, _, s, _ in self.vars:
            for lm in modes(p.l_max, s):
                self._Ybar[(s, *lm)] = np.conj(sYlm(s, lm[0], lm[1], self.theta, self.phi))
        self._files: set[str] = set()

    def schedule(self, S):
        S.add("ANALYSIS", self.analyse)

    def analyse(self):
        p, sim, g = self.p, self.sim, self.sim.grid
        if p.out_every <= 0 or sim.iteration % p.out_every:
            return
        c = np.array([p.center_x, p.center_y, p.center_z])
        for real, imag, s, name in self.vars:
            fields = [sim.gf.get(real, fresh=True)]
            if imag:
                fields.append(sim.gf.get(imag, fresh=True))
            F = np.stack(fields)
            for R in self.radii:
                vals = interpolate(F, g.origin, g.dx, c + R * self.unit, p.interpolator_order)
                f = vals[0] + (1j * vals[1] if imag else 0.0)
                for l, m in modes(p.l_max, s):
                    coef = np.sum(self.weights * f * self._Ybar[(s, l, m)])
                    self._write(f"mp_{name}_l{l}_m{m}_r{R:.2f}.asc", sim.time, coef)

    def _write(self, fname, t, coef):
        path = os.path.join(self.sim.out_dir, fname)
        first = path not in self._files
        with open(path, "w" if first else "a") as fh:
            if first:
                fh.write("# Multipole output created by pyNR\n# 1:time 2:Re 3:Im\n")
                self._files.add(path)
            fh.write(f"{t:.15e} {coef.real:.15e} {coef.imag:.15e}\n")
