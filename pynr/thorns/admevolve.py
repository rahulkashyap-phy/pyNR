r"""ADMEvolve: evolve the ADM equations (see :mod:`pynr.kernels.adm` for the equations).

Activated with ``ADMBase::evolution_method = "ADMEvolve"``. The slicing is set
by ``ADMBase::lapse_evolution_method``:

==============  ===============================================  =============================
keyword         equation                                          typical use
==============  ===============================================  =============================
``static``      :math:`\partial_t\alpha = 0`                      stationary tests
``harmonic``    :math:`\partial_t\alpha = -\alpha^2 K`            gauge wave; singularity avoiding
``1+log``       :math:`\partial_t\alpha = -2\alpha K`             black holes (Bona-Massó family)
==============  ===============================================  =============================

Outer boundaries (``ADMEvolve::bound``): ``static``, ``radiative`` or
``flat``; periodic directions from ``CoordBase::periodic_*`` are always
synchronised.

Excision: with ``excision_radius > 0`` every point with
:math:`r <` ``excision_radius`` gets :math:`\partial_t u = 0` (after dissipation
is added), so the region is frozen at its initial values; non-finite initial
values there (e.g. at :math:`r = 0`) are replaced by flat space. This is the
simplest possible excision. It is legitimate only if the excised region lies
inside the horizon, where all characteristics point inward, and if the
stencils of points outside never reach deep into it. In practice choose the
excision radius between about 0.5 and 0.9 times the horizon radius, and at
least 4 grid points wide.
"""

import numpy as np

from pynr.backends import get_kernel
from pynr.cactus import Param, Thorn, register_thorn
from pynr.kernels.adm import ALP, BETAX, NVARS
from pynr.kernels.boundary import rhs_boundary, sync_flat, sync_periodic

LAPSE = {"static": 0, "harmonic": 1, "1+log": 2}
U_INF = np.array([1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0], dtype=float)


@register_thorn
class ADMEvolve(Thorn):
    name = "ADMEvolve"
    requires = ("ADMBase", "MoL")
    parameters = {
        "bound": Param("static", "Outer boundary condition", keywords=("static", "radiative", "flat")),
        "advect_lapse": Param(True, "Include beta^i d_i alpha in the lapse RHS"),
        "excision_radius": Param(0.0, "Freeze evolution for r < excision_radius (0 = off)"),
    }

    def setup(self):
        adm = self.sim.params.of("ADMBase")
        if adm.evolution_method != "ADMEvolve":
            return
        grid = self.sim.grid
        self.U = self.sim.thorn("ADMBase").U
        self.lapse_method = LAPSE[adm.lapse_evolution_method]
        self.kernel = get_kernel("adm_rhs", self.sim.backend)
        self.x, self.y, self.z = grid.coords1d
        mask = np.ones(NVARS, dtype=np.bool_)
        mask[BETAX:BETAX + 3] = False
        mask[ALP] = self.lapse_method != 0
        self.sim.thorn("MoL").register_evolved(self.name, self.U, self.rhs, self.post, mask,
                                               rhs_final=self.rhs_final)
        self._all = np.ones(NVARS, dtype=np.bool_)
        self.excised = None
        if self.p.excision_radius > 0:
            X, Y, Z = grid.meshgrid()
            self.excised = X**2 + Y**2 + Z**2 < self.p.excision_radius**2

    def schedule(self, S):
        if self.sim.params.get("ADMBase", "evolution_method") == "ADMEvolve":
            S.add("POSTINITIAL", self.sanitize_excision, before=["MoL::post_initial"])

    def sanitize_excision(self):
        """Replace non-finite values inside the excision region by flat space."""
        if self.excised is None:
            return
        U = self.U
        bad = self.excised & ~np.all(np.isfinite(U), axis=0)
        U[:, bad] = U_INF[:, None]
        if np.any(~np.isfinite(U)):
            raise FloatingPointError("Non-finite initial data outside the excision region")

    def rhs(self, t, U, dU):
        g = self.sim.grid
        self.kernel(U, dU, g.idx, g.nghost, self.lapse_method, self.p.advect_lapse,
                    self.x, self.y, self.z, self.p.excision_radius**2)

    def rhs_final(self, t, U, dU):
        """Excision and outer boundary, applied after all RHS hooks (e.g. dissipation)."""
        g = self.sim.grid
        if self.excised is not None:
            dU[:, self.excised] = 0.0
        if not all(g.periodic) and self.p.bound != "flat":
            rhs_boundary(U, dU, g.idx, g.nghost, self.x, self.y, self.z, U_INF,
                         self.p.bound == "radiative", self._all)

    def post(self, U):
        g = self.sim.grid
        if self.p.bound == "flat":
            sync_flat(U, g.nghost)
        if any(g.periodic):
            sync_periodic(U, g.nghost, g.nphys, g.periodic)
