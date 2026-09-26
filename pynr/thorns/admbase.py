r"""ADMBase: the 3+1 variables every other thorn agrees on.

The line element in 3+1 form is

.. math::
    ds^2 = -\alpha^2 dt^2 + \gamma_{ij}(dx^i + \beta^i dt)(dx^j + \beta^j dt),

with lapse :math:`\alpha`, shift :math:`\beta^i`, spatial metric
:math:`\gamma_{ij}` and extrinsic curvature
:math:`K_{ij} = -\frac{1}{2\alpha}(\partial_t\gamma_{ij} - \mathcal{L}_\beta\gamma_{ij})`.

Like the ET's ADMBase, this thorn only *owns* the variables and the
parameters that select who sets them; it contains no physics. Initial data
thorns (e.g. :mod:`~pynr.thorns.exact`) fill them in ``INITIAL``; evolution
thorns (e.g. :mod:`~pynr.thorns.admevolve`) update them in ``EVOL``.

Grid functions (groups in brackets): ``gxx gxy gxz gyy gyz gzz`` [metric],
``kxx kxy kxz kyy kyz kzz`` [curv], ``alp`` [lapse], ``betax betay betaz`` [shift].
They are views into one array ``ADMBase.U`` of shape ``(16, nx, ny, nz)``.
"""

from pynr.cactus import Param, Thorn, register_thorn
from pynr.kernels.adm import ALP, BETAX, GXX, GYY, GZZ, KXX, NVARS, VARNAMES


@register_thorn
class ADMBase(Thorn):
    name = "ADMBase"
    parameters = {
        "initial_data": Param("Cartesian Minkowski", "Who sets gamma_ij and K_ij",
                              keywords=("Cartesian Minkowski", "exact")),
        "initial_lapse": Param("one", "Who sets the initial lapse",
                               keywords=("one", "exact", "psi^-2")),
        "initial_shift": Param("zero", "Who sets the initial shift", keywords=("zero", "exact")),
        "evolution_method": Param("static", "Who evolves gamma_ij and K_ij",
                                  keywords=("static", "ADMEvolve")),
        "lapse_evolution_method": Param("static", "Slicing condition",
                                        keywords=("static", "harmonic", "1+log")),
        "shift_evolution_method": Param("static", "Shift condition", keywords=("static",)),
    }

    def setup(self):
        self.U = self.sim.grid.empty(NVARS)
        for c, n in enumerate(VARNAMES):
            self.sim.gf.register(self.name, n, self.U[c])
        self.sim.gf.register_group(self.name, "metric", list(VARNAMES[0:6]))
        self.sim.gf.register_group(self.name, "curv", list(VARNAMES[6:12]))
        self.sim.gf.register_group(self.name, "lapse", ["alp"])
        self.sim.gf.register_group(self.name, "shift", list(VARNAMES[13:16]))

    def schedule(self, S):
        S.add("INITIAL", self.initial_flat)

    def initial_flat(self):
        """Minkowski data, unit lapse, zero shift: the default everyone overwrites."""
        U = self.U
        U[:] = 0.0
        U[GXX] = U[GYY] = U[GZZ] = 1.0
        U[ALP] = 1.0
        U[BETAX:BETAX + 3] = 0.0
        U[KXX:KXX + 6] = 0.0
