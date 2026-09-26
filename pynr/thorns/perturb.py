r"""Perturb: add a Gaussian :math:`(\ell, m)` shell perturbation to the metric.

After the background initial data are set, the spatial metric is rescaled

.. math::
    \gamma_{ij} \to \left(1 + \epsilon(r,\theta,\phi)\right)\gamma_{ij},\qquad
    \epsilon = A\, e^{-(r-r_0)^2/\sigma^2}\, Y_{\ell m}(\theta,\phi),

with a real spherical harmonic :math:`Y_{\ell m}` (``m >= 0`` uses
:math:`\mathrm{Re}\,Y_{\ell m}`, ``m < 0`` uses :math:`\mathrm{Im}\,Y_{\ell |m|}`),
centred on ``Perturb::center_*``. :math:`K_{ij}` is left unchanged.

.. warning::
   This perturbation does **not** solve the Hamiltonian constraint; it
   violates it at :math:`\mathcal{O}(A)`. It is a quick way to "ring" a black
   hole: the gauge/constraint-violating part propagates away or stays near the
   shell, while the physical part excites quasi-normal modes. Monitor
   ``ADMConstraints::H`` and keep :math:`A \lesssim 10^{-3}`. Solving the
   constraint for the perturbed data (Brill waves / conformal thin sandwich)
   is a good project once the elliptic solver lands.

Physics check: for :math:`M = 1`, :math:`\ell = 2` the dominant Schwarzschild
quasi-normal mode is :math:`M\omega = 0.3737 - 0.0890\,i`
(period :math:`\approx 16.8M`, e-folding time :math:`\approx 11.2M`).
"""

import numpy as np

from pynr.cactus import Param, Thorn, register_thorn
from pynr.utils.swsh import sYlm


@register_thorn
class Perturb(Thorn):
    name = "Perturb"
    requires = ("ADMBase",)
    parameters = {
        "amplitude": Param(0.0, "Amplitude A (0 disables)"),
        "radius": Param(5.0, "Shell radius r0"),
        "width": Param(1.0, "Gaussian width sigma"),
        "l": Param(2, "Multipole l"),
        "m": Param(0, "Multipole m"),
        "center_x": Param(0.0, "Centre x"),
        "center_y": Param(0.0, "Centre y"),
        "center_z": Param(0.0, "Centre z"),
    }

    def schedule(self, S):
        S.add("INITIAL", self.perturb, after=["Exact::initial_data", "ADMBase::initial_flat"])

    def shape_function(self, X, Y, Z):
        p = self.p
        x, y, z = X - p.center_x, Y - p.center_y, Z - p.center_z
        r = np.sqrt(x**2 + y**2 + z**2)
        th = np.arccos(np.clip(z / np.maximum(r, 1e-300), -1, 1))
        ph = np.arctan2(y, x)
        Y = sYlm(0, p.l, abs(p.m), th, ph)
        ang = Y.real if p.m >= 0 else Y.imag
        return p.amplitude * np.exp(-((r - p.radius) ** 2) / p.width**2) * ang

    def perturb(self):
        if self.p.amplitude == 0.0:
            return
        U = self.sim.thorn("ADMBase").U
        eps = self.shape_function(*self.sim.grid.meshgrid())
        U[0:6] *= 1.0 + eps
        self.info(f"added l={self.p.l} m={self.p.m} perturbation, max |eps| = {np.abs(eps).max():.3e}")
