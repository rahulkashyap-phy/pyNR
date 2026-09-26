"""Uniform Cartesian grid (the role PUGH/Carpet play in the ET, without AMR).

Layout convention
-----------------
The *physical* domain is ``[xmin, xmax]`` sampled with spacing ``dx`` (points
``xmin + i*dx``, both ends included). ``nghost`` extra points are added on
each side for the outer boundary / periodic images, exactly like ET boundary
points. All arrays have shape ``(nx, ny, nz)`` with ``x`` as the first index.

For a *periodic* direction the period is ``xmax - xmin``; the point at
``xmax`` is the image of the point at ``xmin``.

To avoid placing a grid point on a puncture at the origin, choose ``xmin``
and ``dx`` so that ``0`` falls between points ("staggered" grid), e.g.
``xmin = -10.1, dx = 0.2``.
"""

from __future__ import annotations

import numpy as np


class UniformGrid:
    def __init__(self, xmin, xmax, dx, nghost=3, periodic=(False, False, False)):
        self.xmin = np.asarray(xmin, dtype=float)
        self.xmax = np.asarray(xmax, dtype=float)
        self.dx = np.asarray(dx, dtype=float)
        self.nghost = int(nghost)
        self.periodic = tuple(bool(p) for p in periodic)
        nphys = np.rint((self.xmax - self.xmin) / self.dx).astype(int) + 1
        if np.any(np.abs((nphys - 1) * self.dx - (self.xmax - self.xmin)) > 1e-8 * self.dx):
            raise ValueError("(xmax - xmin) must be an integer multiple of dx in each direction")
        self.nphys = nphys
        self.shape = tuple(int(n + 2 * self.nghost) for n in nphys)
        #: Coordinates of array index (0, 0, 0) (a ghost point).
        self.origin = self.xmin - self.nghost * self.dx
        self.coords1d = tuple(self.origin[d] + self.dx[d] * np.arange(self.shape[d]) for d in range(3))
        g = self.nghost
        self.interior = (slice(g, -g),) * 3 if g > 0 else (slice(None),) * 3

    @property
    def idx(self) -> np.ndarray:
        """Inverse grid spacings, the form kernels want."""
        return 1.0 / self.dx

    def meshgrid(self):
        """Full 3D coordinate arrays ``X, Y, Z`` (allocates 3 grid functions)."""
        return np.meshgrid(*self.coords1d, indexing="ij")

    def empty(self, nvars: int | None = None) -> np.ndarray:
        shp = self.shape if nvars is None else (nvars, *self.shape)
        return np.zeros(shp, dtype=np.float64)

    def nearest_index(self, x: float, d: int) -> int:
        return int(np.clip(np.rint((x - self.origin[d]) / self.dx[d]), 0, self.shape[d] - 1))

    def __repr__(self):
        return (
            f"UniformGrid(shape={self.shape}, xmin={self.xmin.tolist()}, "
            f"xmax={self.xmax.tolist()}, dx={self.dx.tolist()}, nghost={self.nghost})"
        )
