r"""Exact: analytic spacetimes as initial data (and reference solutions).

Select with ``ADMBase::initial_data = "exact"`` and ``Exact::exact_model``.
``ADMBase::initial_lapse`` / ``initial_shift = "exact"`` take the lapse/shift
from the same model. Each model is a function ``(t, x, y, z) -> (g6, K6, alp, beta3)``
so tests can compare an evolution with the exact solution at any time.

Models
------

**Minkowski/gauge wave** (Apples-with-Apples test; Alcubierre et al. 2004).
Flat space in a time-dependent slicing:

.. math::
    ds^2 = -H dt^2 + H dx^2 + dy^2 + dz^2,\qquad
    H = 1 - A\sin\frac{2\pi(x-t)}{d},

so :math:`\alpha=\sqrt H`, :math:`\gamma_{xx}=H`,
:math:`K_{xx} = -\frac{\pi A}{d}\cos\frac{2\pi(x-t)}{d}/\sqrt H`.
Evolve with harmonic slicing; the exact solution is known for all time.

**Minkowski/linear wave** (AwA). A linearised plane gravitational wave in TT gauge,
:math:`\gamma_{yy} = 1 + b`, :math:`\gamma_{zz} = 1 - b`,
:math:`b = A\sin\frac{2\pi(x-t)}{d}`, :math:`K_{ij} = -\tfrac12\partial_t\gamma_{ij}`.
For it :math:`\Psi_4 = \ddot h_+ - i \ddot h_\times` with :math:`h_+ = b` along :math:`x`.

**Schwarzschild/isotropic**. Time-symmetric slice in isotropic coordinates,

.. math::
    \gamma_{ij} = \psi^4\delta_{ij},\quad \psi = 1 + \frac{M}{2r},\quad K_{ij}=0,

with ``exact`` lapse :math:`\alpha = (1 - M/2r)/(1 + M/2r)` (static solution;
it vanishes at the horizon :math:`r=M/2`), or ``psi^-2`` ("pre-collapsed"
lapse used for moving-puncture runs), or ``one`` (geodesic slicing — the
slice hits the singularity at :math:`t=\pi M`).

**Kerr/Kerr-Schild**. Horizon-penetrating coordinates for a Kerr black hole
of mass :math:`M` and spin :math:`a = \chi M` along :math:`z`:
:math:`g_{\mu\nu} = \eta_{\mu\nu} + 2H\,l_\mu l_\nu` with

.. math::
    H = \frac{M r^3}{r^4 + a^2 z^2},\quad
    l_\mu = \left(1, \frac{rx + ay}{r^2+a^2}, \frac{ry - ax}{r^2+a^2}, \frac{z}{r}\right),

giving :math:`\gamma_{ij} = \delta_{ij} + 2Hl_il_j`, :math:`\alpha = (1+2H)^{-1/2}`,
:math:`\beta^i = 2Hl^i/(1+2H)`. Since the data are stationary,
:math:`K_{ij} = (D_i\beta_j + D_j\beta_i)/2\alpha`; we evaluate it by 4th-order
differencing of the analytic metric with step :math:`10^{-4}`, not on the grid.
:math:`\chi = 0` is Schwarzschild in ingoing Eddington-Finkelstein coordinates.
The singularity is inside the horizon; use ``ADMEvolve::excision_radius``.
"""

from __future__ import annotations

import numpy as np

from pynr.cactus import Param, Thorn, register_thorn
from pynr.kernels.adm import ALP, BETAX, KXX, PAIR

MODELS = ("Minkowski", "Minkowski/gauge wave", "Minkowski/linear wave",
          "Schwarzschild/isotropic", "Kerr/Kerr-Schild")


def _flat(shape):
    g = np.zeros((6, *shape))
    g[0] = g[3] = g[5] = 1.0
    return g


def minkowski(t, x, y, z):
    shp = np.broadcast(x, y, z).shape
    return _flat(shp), np.zeros((6, *shp)), np.ones(shp), np.zeros((3, *shp))


def gauge_wave(t, x, y, z, A=0.1, d=1.0):
    x, y, z = np.broadcast_arrays(x, y, z)
    ph = 2 * np.pi * (x - t) / d
    H = 1 - A * np.sin(ph)
    g, K, _, beta = minkowski(t, x, y, z)
    g[0] = H
    K[0] = -np.pi * A / d * np.cos(ph) / np.sqrt(H)
    return g, K, np.sqrt(H), beta


def linear_wave(t, x, y, z, A=1e-8, d=1.0):
    x, y, z = np.broadcast_arrays(x, y, z)
    ph = 2 * np.pi * (x - t) / d
    b = A * np.sin(ph)
    db_dt = -A * 2 * np.pi / d * np.cos(ph)
    g, K, alp, beta = minkowski(t, x, y, z)
    g[3] = 1 + b
    g[5] = 1 - b
    K[3] = -0.5 * db_dt
    K[5] = 0.5 * db_dt
    return g, K, alp, beta


def schwarzschild_isotropic(t, x, y, z, M=1.0):
    x, y, z = np.broadcast_arrays(x, y, z)
    r = np.sqrt(x**2 + y**2 + z**2)
    psi = 1 + M / (2 * r)
    g, K, _, beta = minkowski(t, x, y, z)
    g[0] = g[3] = g[5] = psi**4
    alp = (1 - M / (2 * r)) / (1 + M / (2 * r))
    return g, K, alp, beta


def _kerr_schild_metric(x, y, z, M, a):
    rho2 = x**2 + y**2 + z**2
    r2 = 0.5 * (rho2 - a**2) + np.sqrt(0.25 * (rho2 - a**2) ** 2 + a**2 * z**2)
    r = np.sqrt(r2)
    H = M * r**3 / (r2**2 + a**2 * z**2)
    l = np.array([(r * x + a * y) / (r2 + a**2), (r * y - a * x) / (r2 + a**2), z / r])
    g = _flat(x.shape)
    for c, (i, j) in enumerate(PAIR):
        g[c] += 2 * H * l[i] * l[j]
    beta_low = 2 * H * l
    return g, beta_low, H, l


def kerr_schild(t, x, y, z, M=1.0, spin=0.0, eps=1e-4):
    x, y, z = (np.asarray(v, float) for v in np.broadcast_arrays(x, y, z))
    a = spin * M
    g, bl, H, l = _kerr_schild_metric(x, y, z, M, a)
    alp = 1 / np.sqrt(1 + 2 * H)
    beta_up = 2 * H * l / (1 + 2 * H)

    # d_m g_ab and d_m beta_a by 4th-order differencing of the analytic functions
    dg = np.empty((3, 6, *x.shape))
    dbl = np.empty((3, 3, *x.shape))
    for m in range(3):
        acc_g, acc_b = 0.0, 0.0
        for s, w in ((-2, 1), (-1, -8), (1, 8), (2, -1)):
            X = [x, y, z]
            X[m] = X[m] + s * eps
            gs, bs, _, _ = _kerr_schild_metric(*X, M, a)
            acc_g = acc_g + w * gs
            acc_b = acc_b + w * bs
        dg[m] = acc_g / (12 * eps)
        dbl[m] = acc_b / (12 * eps)

    def dgm(m, i, j):  # d_m g_ij from packed storage
        return dg[m, _packed(i, j)]

    K = np.empty((6, *x.shape))
    for c, (i, j) in enumerate(PAIR):
        # Gamma^k_ij beta_k = Gamma_kij beta^k with Gamma_kij = (d_i g_kj + d_j g_ki - d_k g_ij)/2
        gb = 0.0
        for k in range(3):
            Gk = 0.5 * (dgm(i, k, j) + dgm(j, k, i) - dgm(k, i, j))
            gb = gb + Gk * beta_up[k]
        K[c] = (dbl[i, j] + dbl[j, i] - 2 * gb) / (2 * alp)
    return g, K, alp, beta_up


def _packed(i, j):
    return int(((0, 1, 2), (1, 3, 4), (2, 4, 5))[i][j])


@register_thorn
class Exact(Thorn):
    name = "Exact"
    requires = ("ADMBase",)
    parameters = {
        "exact_model": Param("Minkowski", "Analytic spacetime", keywords=MODELS),
        "Minkowski_gauge_wave__amplitude": Param(0.1, "Gauge-wave amplitude A"),
        "Minkowski_gauge_wave__lambda": Param(1.0, "Gauge-wave wavelength d"),
        "Minkowski_linear_wave__amplitude": Param(1e-8, "Linear-wave amplitude A"),
        "Minkowski_linear_wave__lambda": Param(1.0, "Linear-wave wavelength d"),
        "Schwarzschild_isotropic__mass": Param(1.0, "Mass M"),
        "Kerr_KerrSchild__mass": Param(1.0, "Mass M"),
        "Kerr_KerrSchild__spin": Param(0.0, "Dimensionless spin chi = a/M (along z)"),
        "position_x": Param(0.0, "Black-hole x position"),
        "position_y": Param(0.0, "Black-hole y position"),
        "position_z": Param(0.0, "Black-hole z position"),
    }

    def solution(self, t, x, y, z):
        """Evaluate the selected model at coordinates ``x, y, z`` (arrays) and time ``t``."""
        p, m = self.p, self.p.exact_model
        x, y, z = x - p.position_x, y - p.position_y, z - p.position_z
        if m == "Minkowski":
            return minkowski(t, x, y, z)
        if m == "Minkowski/gauge wave":
            return gauge_wave(t, x, y, z, p.Minkowski_gauge_wave__amplitude,
                              p.Minkowski_gauge_wave__lambda)
        if m == "Minkowski/linear wave":
            return linear_wave(t, x, y, z, p.Minkowski_linear_wave__amplitude,
                               p.Minkowski_linear_wave__lambda)
        if m == "Schwarzschild/isotropic":
            return schwarzschild_isotropic(t, x, y, z, p.Schwarzschild_isotropic__mass)
        return kerr_schild(t, x, y, z, p.Kerr_KerrSchild__mass, p.Kerr_KerrSchild__spin)

    def schedule(self, S):
        S.add("INITIAL", self.initial_data, after=["ADMBase::initial_flat"])

    def initial_data(self):
        adm = self.sim.params.of("ADMBase")
        U = self.sim.thorn("ADMBase").U
        X, Y, Z = self.sim.grid.meshgrid()
        g, K, alp, beta = self.solution(0.0, X, Y, Z)
        if adm.initial_data == "exact":
            U[0:6] = g
            U[KXX:KXX + 6] = K
            self.info(f"initial data from '{self.p.exact_model}'")
        if adm.initial_lapse == "exact":
            U[ALP] = alp
        elif adm.initial_lapse == "psi^-2":
            U[ALP] = U[0] ** -0.5  # gxx = psi^4 for conformally flat data
        if adm.initial_shift == "exact":
            U[BETAX:BETAX + 3] = beta
