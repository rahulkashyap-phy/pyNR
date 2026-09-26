r"""WeylScal4: the Newman-Penrose scalar :math:`\Psi_4` on the grid.

Far from the source, :math:`\Psi_4` carries the outgoing radiation,

.. math::
    \Psi_4 = \ddot h_+ - i\,\ddot h_\times \quad (r\to\infty),

so the strain follows by integrating twice in time (kuibit does this with
fixed-frequency integration, Reisswig & Pollney 2011). Formulae and tetrad:
:func:`pynr.kernels.adm.weyl_psi4`. Grid functions ``Psi4r``, ``Psi4i`` are
computed on demand, i.e. only at iterations where ``Multipole`` or I/O use them.
"""

from pynr.backends import get_kernel
from pynr.cactus import Param, Thorn, register_thorn


@register_thorn
class WeylScal4(Thorn):
    name = "WeylScal4"
    requires = ("ADMBase",)
    parameters = {
        "offset_x": Param(0.0, "Tetrad origin x"),
        "offset_y": Param(0.0, "Tetrad origin y"),
        "offset_z": Param(0.0, "Tetrad origin z"),
    }

    def setup(self):
        grid = self.sim.grid
        self.psi4 = grid.empty(2)
        self.sim.gf.register(self.name, "Psi4r", self.psi4[0], update=self.compute)
        self.sim.gf.register(self.name, "Psi4i", self.psi4[1], update=self.compute)
        self.sim.gf.register_group(self.name, "Psi4", ["Psi4r", "Psi4i"])

    def compute(self):
        g, p = self.sim.grid, self.p
        x, y, z = g.coords1d
        get_kernel("weyl_psi4", self.sim.backend)(
            self.sim.thorn("ADMBase").U, self.psi4[0], self.psi4[1], g.idx, g.nghost,
            x - p.offset_x, y - p.offset_y, z - p.offset_z)
