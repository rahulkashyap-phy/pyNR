r"""Vectorised NumPy reference implementation of the ADM right-hand side.

This is the *readable* version of :func:`pynr.kernels.adm.adm_rhs`: every
tensor equation is one ``einsum`` over whole-grid arrays, so the code reads
like the equations on the blackboard. It is used

* as the ``numpy`` backend (``Driver::backend = "numpy"``),
* in the tests, to cross-check the Numba kernel.

It is written only against the array API used by NumPy (slicing, ``einsum``,
``linalg.inv``), so passing ``xp=cupy`` or ``xp=jax.numpy`` should run it on
a GPU — treat that as experimental.

It is typically 5-20x slower than the Numba kernel and needs a few GB of
temporaries for 128^3 grids — the price of readability.
"""

import numpy as np

from pynr.kernels.adm import ALP, BETAX, KXX, NVARS, PAIR


def _sl(shape, ng, ax=None, off=0, ax2=None, off2=0):
    s = []
    for d in range(3):
        o = (off if d == ax else 0) + (off2 if d == ax2 else 0)
        s.append(slice(ng + o, shape[d] - ng + o))
    return tuple(s)


def d1(f, ax, idx, ng):
    """4th-order first derivative on the interior ``[ng, n-ng)``."""
    sh = f.shape
    return (f[_sl(sh, ng, ax, -2)] - 8 * f[_sl(sh, ng, ax, -1)]
            + 8 * f[_sl(sh, ng, ax, 1)] - f[_sl(sh, ng, ax, 2)]) * (idx[ax] / 12.0)


def d2(f, a, b, idx, ng):
    """4th-order second derivative on the interior."""
    sh = f.shape
    if a == b:
        return (-f[_sl(sh, ng, a, -2)] + 16 * f[_sl(sh, ng, a, -1)] - 30 * f[_sl(sh, ng)]
                + 16 * f[_sl(sh, ng, a, 1)] - f[_sl(sh, ng, a, 2)]) * (idx[a] ** 2 / 12.0)
    c = {-2: 1.0, -1: -8.0, 1: 8.0, 2: -1.0}
    out = 0.0
    for p, cp in c.items():
        for q, cq in c.items():
            out = out + cp * cq * f[_sl(sh, ng, a, p, b, q)]
    return out * (idx[a] * idx[b] / 144.0)


def _sym(U, first, fn, xp=np):
    """Build a symmetric (3,3,...) tensor from 6 packed components via ``fn(component)``."""
    comps = [fn(U[first + c]) for c in range(6)]
    rows = [[None] * 3 for _ in range(3)]
    for c, (a, b) in enumerate(PAIR):
        rows[a][b] = rows[b][a] = comps[c]
    return xp.stack([xp.stack(r) for r in rows])


def geometry(U, idx, ng, xp=np):
    """Metric, inverse, Christoffels and Ricci tensor on the interior."""
    core = _sl(U.shape[1:], ng)
    g = _sym(U, 0, lambda f: f[core], xp)
    dg = xp.stack([_sym(U, 0, lambda f, m=m: d1(f, m, idx, ng), xp) for m in range(3)])
    ddg = xp.stack([xp.stack([_sym(U, 0, lambda f, m=m, n=n: d2(f, m, n, idx, ng), xp)
                              for n in range(3)]) for m in range(3)])
    gu = xp.moveaxis(xp.linalg.inv(xp.moveaxis(g, (0, 1), (-2, -1))), (-2, -1), (0, 1))

    Gl = 0.5 * (xp.einsum("alb...->lab...", dg) + xp.einsum("bla...->lab...", dg) - dg)
    G = xp.einsum("kl...,lab...->kab...", gu, Gl)
    dgu = -xp.einsum("kp...,lq...,mpq...->mkl...", gu, gu, dg)
    dGl = 0.5 * (xp.einsum("malb...->mlab...", ddg) + xp.einsum("mbla...->mlab...", ddg)
                 - ddg)
    dG = (xp.einsum("mkl...,lab...->mkab...", dgu, Gl)
          + xp.einsum("kl...,mlab...->mkab...", gu, dGl))
    R = (xp.einsum("kkab...->ab...", dG) - xp.einsum("bkka...->ab...", dG)
         + xp.einsum("kkl...,lab...->ab...", G, G) - xp.einsum("kbl...,lka...->ab...", G, G))
    return g, gu, dg, G, R


def adm_rhs(U, rhs, idx, ng, lapse_method, advect_lapse, x, y, z, excision_r2, xp=np):
    """Same contract as :func:`pynr.kernels.adm.adm_rhs`."""
    core = _sl(U.shape[1:], ng)
    g, gu, dg, G, R = geometry(U, idx, ng, xp)
    K = _sym(U, KXX, lambda f: f[core], xp)
    dK = xp.stack([_sym(U, KXX, lambda f, m=m: d1(f, m, idx, ng), xp) for m in range(3)])
    alp = U[ALP][core]
    beta = xp.stack([U[BETAX + a][core] for a in range(3)])
    dalp = xp.stack([d1(U[ALP], m, idx, ng) for m in range(3)])
    ddalp = xp.stack([xp.stack([d2(U[ALP], a, b, idx, ng) for b in range(3)]) for a in range(3)])
    dbeta = xp.stack([xp.stack([d1(U[BETAX + a], m, idx, ng) for a in range(3)])
                      for m in range(3)])  # dbeta[m, a] = d_m beta^a

    trK = xp.einsum("ab...,ab...->...", gu, K)
    Km = xp.einsum("am...,mb...->ab...", gu, K)  # K^a_b
    DDalp = ddalp - xp.einsum("mab...,m...->ab...", G, dalp)

    def lie(T, dT):
        return (xp.einsum("m...,mab...->ab...", beta, dT)
                + xp.einsum("mb...,am...->ab...", T, dbeta)
                + xp.einsum("am...,bm...->ab...", T, dbeta))

    dt_g = -2 * alp * K + lie(g, dg)
    dt_K = (-DDalp + alp * (R + trK * K - 2 * xp.einsum("am...,mb...->ab...", K, Km))
            + lie(K, dK))

    for c, (a, b) in enumerate(PAIR):
        rhs[c][core] = dt_g[a, b]
        rhs[KXX + c][core] = dt_K[a, b]
    adv = xp.einsum("m...,m...->...", beta, dalp) if advect_lapse else 0.0
    if lapse_method == 1:
        rhs[ALP][core] = -alp**2 * trK + adv
    elif lapse_method == 2:
        rhs[ALP][core] = -2 * alp * trK + adv
    else:
        rhs[ALP][core] = 0.0
    for a in range(3):
        rhs[BETAX + a][core] = 0.0
    if excision_r2 > 0:
        X, Y, Z = np.meshgrid(x[core[0]], y[core[1]], z[core[2]], indexing="ij")
        mask = X**2 + Y**2 + Z**2 < excision_r2
        for c in range(NVARS):
            rhs[c][core][mask] = 0.0
