"""Dissipation: Kreiss-Oliger dissipation on every MoL-evolved variable.

See :mod:`pynr.kernels.dissipation` for the operator. ``Dissipation::epsdis``
is the strength :math:`\\epsilon` (same name and meaning as in the ET).
"""

from pynr.cactus import Param, Thorn, register_thorn
from pynr.kernels.dissipation import add_ko_dissipation


@register_thorn
class Dissipation(Thorn):
    name = "Dissipation"
    requires = ("MoL",)
    parameters = {"epsdis": Param(0.1, "Kreiss-Oliger strength epsilon")}

    def setup(self):
        if self.sim.grid.nghost < 3:
            raise ValueError("Dissipation needs Driver::ghost_size >= 3")
        self.sim.thorn("MoL").add_rhs_hook(self.add)

    def add(self, U, dU, mask):
        if self.p.epsdis > 0:
            add_ko_dissipation(U, dU, self.sim.grid.idx, self.sim.grid.nghost, self.p.epsdis, mask)
