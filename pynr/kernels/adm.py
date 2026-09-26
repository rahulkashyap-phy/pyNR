r"""Numba kernels for the ADM (3+1) equations in vacuum.

Variables
---------
All ADM variables live in one contiguous array ``U[16, nx, ny, nz]``:

=====  ==============================  ==============================
index  variable                        meaning
=====  ==============================  ==============================
0-5    ``gxx gxy gxz gyy gyz gzz``     spatial metric :math:`\gamma_{ij}`
6-11   ``kxx kxy kxz kyy kyz kzz``     extrinsic curvature :math:`K_{ij}`
12     ``alp``                         lapse :math:`\alpha`
13-15  ``betax betay betaz``           shift :math:`\beta^i`
=====  ==============================  ==============================

Evolution equations (Arnowitt-Deser-Misner / York form)
-------------------------------------------------------

.. math::

    \partial_t \gamma_{ij} &= -2\alpha K_{ij} + \mathcal{L}_\beta \gamma_{ij}, \\
    \partial_t K_{ij} &= -D_i D_j \alpha
        + \alpha\left(R_{ij} + K K_{ij} - 2 K_{ik} K^k{}_j\right)
        + \mathcal{L}_\beta K_{ij},

with :math:`\mathcal{L}_\beta T_{ij} = \beta^k\partial_k T_{ij}
+ T_{kj}\partial_i\beta^k + T_{ik}\partial_j\beta^k` and
:math:`D_iD_j\alpha = \partial_i\partial_j\alpha - \Gamma^k_{ij}\partial_k\alpha`.

The Ricci tensor is computed from its definition,

.. math::

    R_{ij} = \partial_k \Gamma^k_{ij} - \partial_j \Gamma^k_{ki}
           + \Gamma^k_{kl}\Gamma^l_{ij} - \Gamma^k_{jl}\Gamma^l_{ki},

expanding the derivatives of the Christoffel symbols pointwise with
:math:`\partial_m\gamma^{kl} = -\gamma^{ka}\gamma^{lb}\partial_m\gamma_{ab}`
and :math:`\Gamma^k_{ki} = \partial_i \ln\sqrt{\gamma}`:

.. math::

    \partial_k\Gamma^k_{ij} &= (\partial_k\gamma^{kl})\Gamma_{lij}
      + \tfrac12\gamma^{kl}(\partial_k\partial_i\gamma_{lj}
      + \partial_k\partial_j\gamma_{li} - \partial_k\partial_l\gamma_{ij}),\\
    \partial_j\Gamma^k_{ki} &= \tfrac12\left(\partial_j\gamma^{kl}\,\partial_i\gamma_{kl}
      + \gamma^{kl}\partial_i\partial_j\gamma_{kl}\right).

Only first and second derivatives of the metric are needed: no extra storage
and a single pass over the grid. (The NumPy reference
:mod:`pynr.kernels.adm_numpy` forms the full :math:`\partial_m\Gamma^k_{ij}`
instead — an independent check of this algebra.)

Slicing (``lapse_method``): 0 static, 1 harmonic
(:math:`\partial_t\alpha = -\alpha^2 K`), 2 "1+log"
(:math:`\partial_t\alpha = -2\alpha K`); with ``advect_lapse`` the term
:math:`\beta^k\partial_k\alpha` is added. The shift is kept static.

The plain ADM system is only weakly hyperbolic — it is the right place to
*learn* 3+1 but it will eventually go unstable for black holes. That is a
feature for teaching; BSSN/Z4c come later.

Performance notes
-----------------
Loops are ``prange`` over ``i`` (threads) with ``j, k`` inner; ``k`` is the
contiguous index, so stencil loads stream through cache. Per-point scratch
arrays are allocated once per ``i`` plane. Compile with ``fastmath`` and
``cache=True`` so the first-run JIT cost is paid only once per machine.
"""

import numpy as np
from numba import njit, prange

from pynr.kernels.fd import grad, hess

GXX, GXY, GXZ, GYY, GYZ, GZZ = range(6)
KXX, KXY, KXZ, KYY, KYZ, KZZ = range(6, 12)
ALP = 12
BETAX, BETAY, BETAZ = 13, 14, 15
NVARS = 16
VARNAMES = ("gxx", "gxy", "gxz", "gyy", "gyz", "gzz",
            "kxx", "kxy", "kxz", "kyy", "kyz", "kzz",
            "alp", "betax", "betay", "betaz")

SYM = np.array([[0, 1, 2], [1, 3, 4], [2, 4, 5]], dtype=np.int64)  # (a,b) -> packed index
PAIR = np.array([[0, 0], [0, 1], [0, 2], [1, 1], [1, 2], [2, 2]], dtype=np.int64)

_JIT = dict(fastmath=True, cache=True, error_model="numpy")


@njit(**_JIT)
def _geometry(U, i, j, k, idx, g, gu, dg, ddg, Gl, G, dgu, W, R, t1, t2):
    """Fill metric, inverse, Christoffels, their derivatives and Ricci at a point.

    Returns ``det(gamma)``. Arrays: ``dg[m,a,b] = d_m g_ab``,
    ``ddg[m,n,a,b] = d_m d_n g_ab``, ``Gl[l,a,b] = Gamma_{lab}``,
    ``G[k,a,b] = Gamma^k_ab``, ``dgu[m,k,l] = d_m g^kl``, ``R[a,b]``
    (``W`` is scratch).
    """
    for c in range(6):
        a, b = PAIR[c, 0], PAIR[c, 1]
        v = U[c, i, j, k]
        g[a, b] = v
        g[b, a] = v
        grad(U, c, i, j, k, idx, t1)
        hess(U, c, i, j, k, idx, t2)
        for m in range(3):
            dg[m, a, b] = t1[m]
            dg[m, b, a] = t1[m]
            for n in range(3):
                ddg[m, n, a, b] = t2[m, n]
                ddg[m, n, b, a] = t2[m, n]

    det = (g[0, 0] * (g[1, 1] * g[2, 2] - g[1, 2] * g[1, 2])
           - g[0, 1] * (g[0, 1] * g[2, 2] - g[1, 2] * g[0, 2])
           + g[0, 2] * (g[0, 1] * g[1, 2] - g[1, 1] * g[0, 2]))
    idet = 1.0 / det
    gu[0, 0] = (g[1, 1] * g[2, 2] - g[1, 2] * g[1, 2]) * idet
    gu[0, 1] = (g[0, 2] * g[1, 2] - g[0, 1] * g[2, 2]) * idet
    gu[0, 2] = (g[0, 1] * g[1, 2] - g[0, 2] * g[1, 1]) * idet
    gu[1, 1] = (g[0, 0] * g[2, 2] - g[0, 2] * g[0, 2]) * idet
    gu[1, 2] = (g[0, 1] * g[0, 2] - g[0, 0] * g[1, 2]) * idet
    gu[2, 2] = (g[0, 0] * g[1, 1] - g[0, 1] * g[0, 1]) * idet
    gu[1, 0] = gu[0, 1]
    gu[2, 0] = gu[0, 2]
    gu[2, 1] = gu[1, 2]

    # Gamma_{lab} = (d_a g_lb + d_b g_la - d_l g_ab) / 2 ; Gamma^k_ab = g^kl Gamma_lab
    for l in range(3):
        for a in range(3):
            for b in range(3):
                Gl[l, a, b] = 0.5 * (dg[a, l, b] + dg[b, l, a] - dg[l, a, b])
    for kk in range(3):
        for a in range(3):
            for b in range(3):
                s = 0.0
                for l in range(3):
                    s += gu[kk, l] * Gl[l, a, b]
                G[kk, a, b] = s

    # d_m g^kl = -g^kp g^lq d_m g_pq, via W[m,p,l] = d_m g_pq g^ql
    for m in range(3):
        for p in range(3):
            for l in range(3):
                s = 0.0
                for q in range(3):
                    s += dg[m, p, q] * gu[q, l]
                W[m, p, l] = s
        for kk in range(3):
            for l in range(kk, 3):
                s = 0.0
                for p in range(3):
                    s -= gu[kk, p] * W[m, p, l]
                dgu[m, kk, l] = s
                dgu[m, l, kk] = s

    # Ricci needs only two contractions of d Gamma:
    #   d_k Gamma^k_ab = (d_k g^kl) Gamma_lab + g^kl (d_k d_a g_lb + d_k d_b g_la - d_k d_l g_ab)/2
    #   d_b Gamma^k_ka = (d_b g^kl d_a g_kl + g^kl d_a d_b g_kl)/2      [Gamma^k_ka = d_a ln sqrt(det)]
    # which is ~3x cheaper than forming all 162 components of d_m Gamma^k_ab.
    for l in range(3):
        W[0, 0, l] = dgu[0, 0, l] + dgu[1, 1, l] + dgu[2, 2, l]  # d_k g^kl (reuse W)
    for a in range(3):
        for b in range(a, 3):
            s = 0.0
            for l in range(3):
                s += W[0, 0, l] * Gl[l, a, b]
                for kk in range(3):
                    s += 0.5 * (gu[kk, l] * (ddg[kk, a, l, b] + ddg[kk, b, l, a]
                                             - ddg[kk, l, a, b] - ddg[a, b, kk, l])
                                - dgu[b, kk, l] * dg[a, kk, l])
                    s += G[l, l, kk] * G[kk, a, b] - G[l, b, kk] * G[kk, l, a]
            R[a, b] = s
            R[b, a] = s
    return det


@njit(parallel=True, **_JIT)
def adm_rhs(U, rhs, idx, ng, lapse_method, advect_lapse, x, y, z, excision_r2):
    """Right-hand side of the ADM equations on interior points ``[ng, n-ng)``.

    Points with :math:`x^2+y^2+z^2 < ` ``excision_r2`` get zero RHS (frozen,
    "poor man's excision"). Ghost points are left untouched — boundary
    conditions fill them (:mod:`pynr.kernels.boundary`).
    """
    nx, ny, nz = U.shape[1], U.shape[2], U.shape[3]
    for i in prange(ng, nx - ng):
        g = np.empty((3, 3))
        gu = np.empty((3, 3))
        dg = np.empty((3, 3, 3))
        ddg = np.empty((3, 3, 3, 3))
        Gl = np.empty((3, 3, 3))
        G = np.empty((3, 3, 3))
        dgu = np.empty((3, 3, 3))
        W = np.empty((3, 3, 3))
        R = np.empty((3, 3))
        t1 = np.empty(3)
        t2 = np.empty((3, 3))
        K = np.empty((3, 3))
        Km = np.empty((3, 3))
        dalp = np.empty(3)
        beta = np.empty(3)
        dbeta = np.empty((3, 3))
        ddalp = np.empty((3, 3))
        dKc = np.empty(3)
        for j in range(ng, ny - ng):
            for k in range(ng, nz - ng):
                if excision_r2 > 0.0 and x[i] ** 2 + y[j] ** 2 + z[k] ** 2 < excision_r2:
                    for c in range(NVARS):
                        rhs[c, i, j, k] = 0.0
                    continue
                _geometry(U, i, j, k, idx, g, gu, dg, ddg, Gl, G, dgu, W, R, t1, t2)
                alp = U[ALP, i, j, k]
                grad(U, ALP, i, j, k, idx, dalp)
                hess(U, ALP, i, j, k, idx, ddalp)
                for a in range(3):
                    beta[a] = U[BETAX + a, i, j, k]
                    grad(U, BETAX + a, i, j, k, idx, t1)
                    for m in range(3):
                        dbeta[m, a] = t1[m]  # d_m beta^a
                for c in range(6):
                    a, b = PAIR[c, 0], PAIR[c, 1]
                    K[a, b] = U[KXX + c, i, j, k]
                    K[b, a] = K[a, b]
                trK = 0.0
                for a in range(3):
                    for b in range(3):
                        trK += gu[a, b] * K[a, b]
                        s = 0.0
                        for m in range(3):
                            s += gu[a, m] * K[m, b]
                        Km[a, b] = s  # K^a_b

                for c in range(6):
                    a, b = PAIR[c, 0], PAIR[c, 1]
                    lie_g = 0.0
                    lie_K = 0.0
                    DDa = ddalp[a, b]
                    KK = 0.0
                    grad(U, KXX + c, i, j, k, idx, dKc)
                    for m in range(3):
                        lie_g += (beta[m] * dg[m, a, b] + g[m, b] * dbeta[a, m]
                                  + g[a, m] * dbeta[b, m])
                        lie_K += (beta[m] * dKc[m]
                                  + K[m, b] * dbeta[a, m] + K[a, m] * dbeta[b, m])
                        DDa -= G[m, a, b] * dalp[m]
                        KK += K[a, m] * Km[m, b]
                    rhs[c, i, j, k] = -2.0 * alp * K[a, b] + lie_g
                    rhs[KXX + c, i, j, k] = (-DDa + alp * (R[a, b] + trK * K[a, b] - 2.0 * KK)
                                             + lie_K)

                adv = 0.0
                if advect_lapse:
                    for m in range(3):
                        adv += beta[m] * dalp[m]
                if lapse_method == 1:
                    rhs[ALP, i, j, k] = -alp * alp * trK + adv
                elif lapse_method == 2:
                    rhs[ALP, i, j, k] = -2.0 * alp * trK + adv
                else:
                    rhs[ALP, i, j, k] = 0.0
                rhs[BETAX, i, j, k] = 0.0
                rhs[BETAY, i, j, k] = 0.0
                rhs[BETAZ, i, j, k] = 0.0


@njit(inline="always")
def _covariant_dK(U, i, j, k, idx, G, K, dK, DK, t1):
    """``DK[c,a,b] = D_c K_ab`` (needs ``G`` and ``K`` filled)."""
    for cc in range(6):
        a, b = PAIR[cc, 0], PAIR[cc, 1]
        grad(U, KXX + cc, i, j, k, idx, t1)
        for m in range(3):
            dK[m, a, b] = t1[m]
            dK[m, b, a] = t1[m]
    for c in range(3):
        for a in range(3):
            for b in range(3):
                s = dK[c, a, b]
                for m in range(3):
                    s -= G[m, c, a] * K[m, b] + G[m, c, b] * K[a, m]
                DK[c, a, b] = s


@njit(parallel=True, **_JIT)
def adm_constraints(U, H, M, idx, ng):
    r"""Hamiltonian and momentum constraints (vacuum).

    .. math::
        H = R + K^2 - K_{ij}K^{ij}, \qquad
        M_i = D_j K^j{}_i - D_i K = \gamma^{jk}(D_k K_{ji} - D_i K_{jk}).
    """
    nx, ny, nz = U.shape[1], U.shape[2], U.shape[3]
    for i in prange(ng, nx - ng):
        g = np.empty((3, 3))
        gu = np.empty((3, 3))
        dg = np.empty((3, 3, 3))
        ddg = np.empty((3, 3, 3, 3))
        Gl = np.empty((3, 3, 3))
        G = np.empty((3, 3, 3))
        dgu = np.empty((3, 3, 3))
        W = np.empty((3, 3, 3))
        R = np.empty((3, 3))
        t1 = np.empty(3)
        t2 = np.empty((3, 3))
        K = np.empty((3, 3))
        dK = np.empty((3, 3, 3))
        DK = np.empty((3, 3, 3))
        for j in range(ng, ny - ng):
            for k in range(ng, nz - ng):
                _geometry(U, i, j, k, idx, g, gu, dg, ddg, Gl, G, dgu, W, R, t1, t2)
                for c in range(6):
                    a, b = PAIR[c, 0], PAIR[c, 1]
                    K[a, b] = U[KXX + c, i, j, k]
                    K[b, a] = K[a, b]
                _covariant_dK(U, i, j, k, idx, G, K, dK, DK, t1)
                trR = 0.0
                trK = 0.0
                KK = 0.0
                for a in range(3):
                    for b in range(3):
                        trR += gu[a, b] * R[a, b]
                        trK += gu[a, b] * K[a, b]
                        for c in range(3):
                            for d in range(3):
                                KK += gu[a, c] * gu[b, d] * K[a, b] * K[c, d]
                H[i, j, k] = trR + trK * trK - KK
                for a in range(3):
                    s = 0.0
                    for b in range(3):
                        for c in range(3):
                            s += gu[b, c] * (DK[c, b, a] - DK[a, b, c])
                    M[a, i, j, k] = s


@njit(parallel=True, **_JIT)
def weyl_psi4(U, psi4re, psi4im, idx, ng, x, y, z):
    r"""Newman-Penrose :math:`\Psi_4` from 3+1 data (vacuum).

    With the electric and magnetic parts of the Weyl tensor

    .. math::
        E_{ij} = R_{ij} + K K_{ij} - K_{ik}K^k{}_j, \qquad
        B_{ij} = \epsilon_{(i}{}^{kl} D_{|k|} K_{l\,j)},

    and an orthonormal triad :math:`(e_r, e_\theta, e_\phi)` built by
    Gram-Schmidt from the coordinate radial, :math:`\theta` and :math:`\phi`
    directions, :math:`\bar m = (e_\theta - i e_\phi)/\sqrt2`, we compute

    .. math::
        \Psi_4 = -(E_{ij} - i B_{ij})\,\bar m^i \bar m^j,

    normalised so that for an outgoing linear wave :math:`\Psi_4 = \ddot h_+ - i\ddot h_\times`
    (the convention used by the ET's WeylScal4 and by kuibit).
    """
    nx, ny, nz = U.shape[1], U.shape[2], U.shape[3]
    for i in prange(ng, nx - ng):
        g = np.empty((3, 3))
        gu = np.empty((3, 3))
        dg = np.empty((3, 3, 3))
        ddg = np.empty((3, 3, 3, 3))
        Gl = np.empty((3, 3, 3))
        G = np.empty((3, 3, 3))
        dgu = np.empty((3, 3, 3))
        W = np.empty((3, 3, 3))
        R = np.empty((3, 3))
        t1 = np.empty(3)
        t2 = np.empty((3, 3))
        K = np.empty((3, 3))
        dK = np.empty((3, 3, 3))
        DK = np.empty((3, 3, 3))
        E = np.empty((3, 3))
        B = np.empty((3, 3))
        e = np.empty((3, 3))  # rows: e_r, e_theta, e_phi (contravariant)
        for j in range(ng, ny - ng):
            for k in range(ng, nz - ng):
                det = _geometry(U, i, j, k, idx, g, gu, dg, ddg, Gl, G, dgu, W, R, t1, t2)
                for c in range(6):
                    a, b = PAIR[c, 0], PAIR[c, 1]
                    K[a, b] = U[KXX + c, i, j, k]
                    K[b, a] = K[a, b]
                _covariant_dK(U, i, j, k, idx, G, K, dK, DK, t1)
                trK = 0.0
                for a in range(3):
                    for b in range(3):
                        trK += gu[a, b] * K[a, b]
                for a in range(3):
                    for b in range(3):
                        s = 0.0
                        for m in range(3):
                            for n in range(3):
                                s += K[a, m] * gu[m, n] * K[n, b]
                        E[a, b] = R[a, b] + trK * K[a, b] - s
                # B_ab = eps_a^{cd} D_c K_db, eps_{aef} = sqrt(det) [aef]
                sq = np.sqrt(det)
                for a in range(3):
                    for b in range(3):
                        s = 0.0
                        for e1 in range(3):
                            for f1 in range(3):
                                if e1 == a or f1 == a or e1 == f1:
                                    continue
                                lc = 0.5 * (a - e1) * (e1 - f1) * (f1 - a)  # Levi-Civita
                                for c in range(3):
                                    for d in range(3):
                                        s += lc * gu[e1, c] * gu[f1, d] * DK[c, d, b]
                        B[a, b] = sq * s
                for a in range(3):
                    for b in range(a + 1, 3):
                        v = 0.5 * (B[a, b] + B[b, a])
                        B[a, b] = v
                        B[b, a] = v

                # triad: radial, theta-like, phi-like, then Gram-Schmidt w.r.t. gamma
                xx, yy, zz = x[i], y[j], z[k]
                e[0, 0], e[0, 1], e[0, 2] = xx, yy, zz
                e[1, 0], e[1, 1], e[1, 2] = xx * zz, yy * zz, -(xx * xx + yy * yy)
                e[2, 0], e[2, 1], e[2, 2] = -yy, xx, 0.0
                for r in range(3):
                    for q in range(r):
                        dot = 0.0
                        for a in range(3):
                            for b in range(3):
                                dot += g[a, b] * e[r, a] * e[q, b]
                        for a in range(3):
                            e[r, a] -= dot * e[q, a]
                    nrm = 0.0
                    for a in range(3):
                        for b in range(3):
                            nrm += g[a, b] * e[r, a] * e[r, b]
                    nrm = 1.0 / np.sqrt(nrm)
                    for a in range(3):
                        e[r, a] *= nrm

                Ett = Epp = Etp = Btt = Bpp = Btp = 0.0
                for a in range(3):
                    for b in range(3):
                        tt = e[1, a] * e[1, b]
                        pp = e[2, a] * e[2, b]
                        tp = e[1, a] * e[2, b]
                        Ett += E[a, b] * tt
                        Epp += E[a, b] * pp
                        Etp += E[a, b] * tp
                        Btt += B[a, b] * tt
                        Bpp += B[a, b] * pp
                        Btp += B[a, b] * tp
                psi4re[i, j, k] = -0.5 * (Ett - Epp - 2.0 * Btp)
                psi4im[i, j, k] = -0.5 * (Bpp - Btt - 2.0 * Etp)
