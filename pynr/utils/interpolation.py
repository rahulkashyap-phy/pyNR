# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
r"""Lagrange interpolation from a uniform grid to arbitrary points.

This is what the ET's ``AEILocalInterp`` does for the ``Multipole`` thorn.
Along each axis we use the ``order+1`` grid points around the target and
Lagrange basis polynomials

$$
    \ell_m(\xi) = \prod_{n\ne m}\frac{\xi - \xi_n}{\xi_m - \xi_n},
$$ (eq-lagrange)

and the 3D weight is the tensor product
$w_{abc} = \ell_a(\xi)\ell_b(\eta)\ell_c(\zeta)$. The error is
$\mathcal{O}(h^{\mathrm{order}+1})$. Several fields are interpolated in
one pass since the weights are shared.

Alternatives: :func:`scipy.interpolate.RegularGridInterpolator` (linear or
cubic spline, simpler but slower, and splines are global rather than local).
"""

import numpy as np
from numba import njit, prange


@njit(parallel=True, fastmath=True, cache=True)
def _interp(fields, origin, dx, pts, order, out):
    nf, nx, ny, nz = fields.shape
    npts = pts.shape[0]
    m = order + 1
    for p in prange(npts):
        w = np.empty((3, m))
        base = np.empty(3, dtype=np.int64)
        for d in range(3):
            n = (nx, ny, nz)[d]
            s = (pts[p, d] - origin[d]) / dx[d]
            b = int(np.floor(s)) - (m - 1) // 2
            b = min(max(b, 0), n - m)
            base[d] = b
            xi = s - b
            for a in range(m):
                v = 1.0
                for q in range(m):
                    if q != a:
                        v *= (xi - q) / (a - q)
                w[d, a] = v
        for f in range(nf):
            acc = 0.0
            for a in range(m):
                for b in range(m):
                    wab = w[0, a] * w[1, b]
                    for c in range(m):
                        acc += wab * w[2, c] * fields[f, base[0] + a, base[1] + b, base[2] + c]
            out[f, p] = acc


def interpolate(fields, origin, dx, points, order: int = 3) -> np.ndarray:
    """Interpolate ``fields`` (``(nf, nx, ny, nz)`` or ``(nx, ny, nz)``) to ``points`` (``(N, 3)``).

    ``origin`` is the coordinate of index ``(0, 0, 0)``. Returns ``(nf, N)``
    (or ``(N,)`` for a single field).
    """
    single = fields.ndim == 3
    F = fields[None] if single else fields
    out = np.empty((F.shape[0], len(points)))
    _interp(np.ascontiguousarray(F), np.asarray(origin, float), np.asarray(dx, float),
            np.ascontiguousarray(points, dtype=float), int(order), out)
    return out[0] if single else out
