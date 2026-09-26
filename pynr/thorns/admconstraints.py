r"""ADMConstraints: Hamiltonian and momentum constraints.

.. math::
    H \equiv R + K^2 - K_{ij}K^{ij} = 16\pi\rho = 0,\qquad
    M_i \equiv D_j K^j{}_i - D_i K = 8\pi S_i = 0 .

The evolution equations preserve the constraints only in the continuum; on
the grid they converge to zero at the order of the scheme (4th here). A
convergence test on :math:`\|H\|_2` is the single most useful check of an NR
code. Grid functions ``H``, ``M1``, ``M2``, ``M3`` are computed on demand
(only when output asks for them). Inside an excision region
(``ADMEvolve::excision_radius``) they are set to zero so that norms measure
the evolved domain only.
"""

from pynr.backends import get_kernel
from pynr.cactus import Param, Thorn, register_thorn


@register_thorn
class ADMConstraints(Thorn):
    name = "ADMConstraints"
    requires = ("ADMBase",)
    parameters = {"compute": Param(True, "Register the constraint grid functions")}

    def setup(self):
        grid = self.sim.grid
        self.H = grid.empty()
        self.M = grid.empty(3)
        self.sim.gf.register(self.name, "H", self.H, update=self.compute)
        for a in range(3):
            self.sim.gf.register(self.name, f"M{a + 1}", self.M[a], update=self.compute)
        self.sim.gf.register_group(self.name, "ham", ["H"])
        self.sim.gf.register_group(self.name, "mom", ["M1", "M2", "M3"])

    def compute(self):
        g = self.sim.grid
        get_kernel("adm_constraints", self.sim.backend)(
            self.sim.thorn("ADMBase").U, self.H, self.M, g.idx, g.nghost)
        excised = getattr(self.sim.thorns.get("admevolve"), "excised", None)
        if excised is not None:
            self.H[excised] = 0.0
            self.M[:, excised] = 0.0
