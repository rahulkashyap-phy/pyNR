# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
r"""Outer boundary conditions on the ghost zones.

Two kinds of operation:

* **RHS conditions** set $\partial_t u$ on ghost points during each
  MoL substep:

  - ``static``: $\partial_t u = 0$ (ghosts keep their initial values);
  - ``radiative``: Sommerfeld outgoing-wave condition (ET's *NewRad*)

    $$
        \partial_t u = -\frac{v}{r}\left[x^i\partial_i u + (u - u_\infty)\right],
    $$ (eq-sommerfeld)

    for $u = u_\infty + f(t-r)/r$, with $v = 1$ and
    second-order one-sided differences pointing into the grid.

* **State conditions** overwrite ghost values after each substep:

  - ``periodic``: copy from the periodic image;
  - ``flat``: copy the nearest interior value (zeroth-order extrapolation).
"""

import numpy as np
from numba import njit, prange

_JIT = dict(fastmath=True, cache=True)


@njit(inline="always")
def _one_sided(f, i, j, k, d, idx, lo, hi):
    """Derivative along ``d`` at a point: centred if possible, otherwise one-sided inward."""
    n = f.shape[d]
    p = (i, j, k)[d]
    if p < lo:  # lower ghost region -> forward difference
        s = 1
    elif p >= n - hi:
        s = -1
    else:
        s = 0
    if d == 0:
        if s == 0:
            return (f[i + 1, j, k] - f[i - 1, j, k]) * 0.5 * idx[0]
        return s * (-3.0 * f[i, j, k] + 4.0 * f[i + s, j, k] - f[i + 2 * s, j, k]) * 0.5 * idx[0]
    if d == 1:
        if s == 0:
            return (f[i, j + 1, k] - f[i, j - 1, k]) * 0.5 * idx[1]
        return s * (-3.0 * f[i, j, k] + 4.0 * f[i, j + s, k] - f[i, j + 2 * s, k]) * 0.5 * idx[1]
    if s == 0:
        return (f[i, j, k + 1] - f[i, j, k - 1]) * 0.5 * idx[2]
    return s * (-3.0 * f[i, j, k] + 4.0 * f[i, j, k + s] - f[i, j, k + 2 * s]) * 0.5 * idx[2]


@njit(parallel=True, **_JIT)
def rhs_boundary(U, rhs, idx, ng, x, y, z, u_inf, radiative, vars_mask):
    """Apply static (``radiative=False``) or Sommerfeld RHS on all ghost points."""
    nv, nx, ny, nz = U.shape
    for i in prange(nx):
        for j in range(ny):
            for k in range(nz):
                ghost = (i < ng or i >= nx - ng or j < ng or j >= ny - ng
                         or k < ng or k >= nz - ng)
                if not ghost:
                    continue
                r = np.sqrt(x[i] ** 2 + y[j] ** 2 + z[k] ** 2)
                for c in range(nv):
                    if not vars_mask[c]:
                        continue
                    if not radiative:
                        rhs[c, i, j, k] = 0.0
                        continue
                    f = U[c]
                    xdu = (x[i] * _one_sided(f, i, j, k, 0, idx, ng, ng)
                           + y[j] * _one_sided(f, i, j, k, 1, idx, ng, ng)
                           + z[k] * _one_sided(f, i, j, k, 2, idx, ng, ng))
                    rhs[c, i, j, k] = -(xdu + (U[c, i, j, k] - u_inf[c])) / r


def sync_periodic(U, ng, nphys, periodic):
    """Fill ghosts (and the duplicated end point) from periodic images.

    Physical index ``p = I - ng`` maps to ``p mod (nphys - 1)`` because the
    last physical point is the image of the first.
    """
    for d in range(3):
        if not periodic[d]:
            continue
        n = U.shape[d + 1]
        period = nphys[d] - 1
        src = (np.arange(n) - ng) % period + ng
        dst = np.nonzero(src != np.arange(n))[0]
        idx = [slice(None)] * 4
        idx_s = [slice(None)] * 4
        idx[d + 1] = dst
        idx_s[d + 1] = src[dst]
        U[tuple(idx)] = U[tuple(idx_s)]


def sync_flat(U, ng):
    """Copy the outermost interior value into the ghost zones."""
    if ng == 0:
        return
    for d in range(3):
        n = U.shape[d + 1]
        lo = [slice(None)] * 4
        src = [slice(None)] * 4
        lo[d + 1], src[d + 1] = slice(0, ng), slice(ng, ng + 1)
        U[tuple(lo)] = U[tuple(src)]
        lo[d + 1], src[d + 1] = slice(n - ng, n), slice(n - ng - 1, n - ng)
        U[tuple(lo)] = U[tuple(src)]
