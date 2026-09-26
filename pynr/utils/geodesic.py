r"""Geodesic (icosahedral) grids on the sphere and their quadrature weights.

A geodesic grid starts from the 12 vertices of an icosahedron; each
refinement splits every triangle into four and projects the new vertices to
the unit sphere. Level :math:`n` has :math:`10\cdot4^n + 2` nearly uniformly
spaced points (level 4: 2562, level 5: 10242) and **no pole singularity**,
unlike a :math:`(\theta,\phi)` grid where points bunch up at the poles.

Quadrature: each spherical triangle's area :math:`A_t` (from
:math:`\tan(A/2) = |a\cdot(b\times c)| / (1 + a\cdot b + b\cdot c + c\cdot a)`,
Van Oosterom & Strackee 1983) is split equally among its three vertices, so
:math:`\sum_i w_i = 4\pi` exactly and

.. math::
    \oint f\,d\Omega \approx \sum_i w_i f(\hat n_i),

with second-order convergence in the point spacing. For smooth
integrands of low multipole order (GW extraction with :math:`\ell \le 8`)
level 4-5 gives relative errors :math:`\sim 10^{-4}-10^{-5}`.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np


def _icosahedron():
    t = (1.0 + np.sqrt(5.0)) / 2.0
    v = np.array([
        [-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0],
        [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
        [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1],
    ], dtype=float)
    f = np.array([
        [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
        [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
        [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
        [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1],
    ])
    return v / np.linalg.norm(v, axis=1)[:, None], f


@lru_cache(maxsize=8)
def geodesic_sphere(level: int):
    """Return ``(points, triangles, weights)`` for a unit geodesic sphere.

    ``points`` is ``(N, 3)``, ``triangles`` ``(M, 3)`` vertex indices,
    ``weights`` ``(N,)`` with ``weights.sum() == 4*pi``.
    """
    verts, faces = _icosahedron()
    verts = list(verts)
    for _ in range(level):
        cache: dict[tuple[int, int], int] = {}

        def mid(a, b):
            key = (a, b) if a < b else (b, a)
            if key not in cache:
                m = verts[a] + verts[b]
                verts.append(m / np.linalg.norm(m))
                cache[key] = len(verts) - 1
            return cache[key]

        new = []
        for a, b, c in faces:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            new += [[a, ab, ca], [b, bc, ab], [c, ca, bc], [ab, bc, ca]]
        faces = np.array(new)
    pts = np.array(verts)
    a, b, c = pts[faces[:, 0]], pts[faces[:, 1]], pts[faces[:, 2]]
    num = np.abs(np.einsum("ij,ij->i", a, np.cross(b, c)))
    den = 1.0 + np.einsum("ij,ij->i", a, b) + np.einsum("ij,ij->i", b, c) + np.einsum("ij,ij->i", c, a)
    area = 2.0 * np.arctan2(num, den)
    w = np.zeros(len(pts))
    for k in range(3):
        np.add.at(w, faces[:, k], area / 3.0)
    return pts, faces, w


def angles(points: np.ndarray):
    """Polar and azimuthal angles ``(theta, phi)`` of unit vectors."""
    theta = np.arccos(np.clip(points[:, 2], -1.0, 1.0))
    phi = np.arctan2(points[:, 1], points[:, 0])
    return theta, phi
