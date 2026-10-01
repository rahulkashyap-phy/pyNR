# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
"""MoL: method-of-lines time integration.

Evolution thorns do not step in time themselves. They *register* an evolved
state array with a RHS function and a post-stage boundary function::

    mol = sim.thorn("MoL")
    mol.register_evolved("ADMEvolve", U, rhs, post=apply_bcs, evolved_mask=mask,
                         rhs_final=apply_rhs_bcs)

and MoL advances all registered state in the ``EVOL`` bin with the chosen
Runge-Kutta method (:mod:`pynr.utils.integrators`). Other thorns can add terms
to every RHS with :meth:`MoL.add_rhs_hook` — that is how :mod:`Dissipation
<pynr.thorns.dissipation>` works without the evolution thorn knowing about it.

One RHS evaluation is therefore::

    rhs(t, U, dU)            # evolution thorn: interior points
    hook(U, dU, mask) ...    # other thorns: dissipation, sources, ...
    rhs_final(t, U, dU)      # evolution thorn: boundary conditions, excision
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from pynr.cactus import Param, Thorn, register_thorn
from pynr.utils.integrators import METHODS


@dataclass
class Evolved:
    owner: str
    U: np.ndarray
    rhs: Callable
    post: Callable
    evolved_mask: np.ndarray
    rhs_final: Callable | None = None


@register_thorn
class MoL(Thorn):
    name = "MoL"
    parameters = {
        "ODE_Method": Param("RK4", "Time integrator", keywords=tuple(METHODS)),
        "check_nan_every": Param(10, "Abort if the evolved state has NaN/Inf or exceeds "
                                     "abort_above, checked every N iterations (0 = never); "
                                     "like the ET's NaNChecker"),
        "abort_above": Param(1e10, "Treat |u| larger than this as a blow-up"),
    }

    def __init__(self, sim):
        super().__init__(sim)
        self.evolved: list[Evolved] = []
        self._hooks: list[Callable] = []
        self._scratch: dict = {}

    def register_evolved(self, owner, U, rhs, post=lambda U: None, evolved_mask=None,
                         rhs_final=None):
        if self.evolved:
            raise NotImplementedError("MoL currently integrates a single state block")
        mask = np.ones(U.shape[0], dtype=np.bool_) if evolved_mask is None else evolved_mask
        self.evolved.append(Evolved(owner, U, rhs, post, mask, rhs_final))

    def add_rhs_hook(self, hook: Callable[[np.ndarray, np.ndarray, np.ndarray], None]):
        """``hook(U, dU, evolved_mask)`` is called after each RHS evaluation."""
        self._hooks.append(hook)

    def schedule(self, S):
        S.add("EVOL", self.step)
        S.add("POSTINITIAL", self.post_initial)
        S.add("POSTSTEP", self.check_nan)

    def post_initial(self):
        for e in self.evolved:
            e.post(e.U)

    def step(self):
        integrate = METHODS[self.p.ODE_Method]
        for e in self.evolved:
            def rhs(t, U, dU, e=e):
                e.rhs(t, U, dU)
                for h in self._hooks:
                    h(U, dU, e.evolved_mask)
                if e.rhs_final is not None:
                    e.rhs_final(t, U, dU)

            integrate(e.U, self.sim.time, self.sim.dt, rhs, e.post, self._scratch)

    def check_nan(self):
        n = self.p.check_nan_every
        if n <= 0 or self.sim.iteration % n:
            return
        for e in self.evolved:
            big = np.abs(e.U).max(axis=(1, 2, 3))  # NaN propagates into max
            bad = np.nonzero(~(big <= self.p.abort_above))[0]
            if bad.size:
                raise FloatingPointError(
                    f"blow-up (NaN/Inf or |u| > {self.p.abort_above:g}) in variables "
                    f"{bad.tolist()} of {e.owner} at iteration {self.sim.iteration}, "
                    f"t = {self.sim.time:g}")
