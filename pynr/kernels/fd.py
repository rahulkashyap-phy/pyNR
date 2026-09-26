r"""Fourth-order centred finite-difference stencils (Numba, pointwise).

For a grid function :math:`f` sampled with spacing :math:`h`,

.. math::

    \partial_x f \approx \frac{f_{i-2} - 8 f_{i-1} + 8 f_{i+1} - f_{i+2}}{12 h},
    \qquad
    \partial_x^2 f \approx \frac{-f_{i-2} + 16 f_{i-1} - 30 f_i + 16 f_{i+1} - f_{i+2}}{12 h^2},

and mixed derivatives :math:`\partial_x\partial_y f` are the tensor product of
two first-derivative stencils. All three have truncation error
:math:`\mathcal{O}(h^4)` and need two points on each side, so a kernel using
them can update points ``[2, n-2)``; dissipation needs three (see
:mod:`pynr.kernels.dissipation`), which is why ``Driver::ghost_size = 3``.

The helpers act on a 4D state array ``U[var, i, j, k]`` and are
``inline="always"`` so Numba fuses them into the calling loop — the generated
machine code is what a C++ compiler would produce for hand-written stencils.
"""

from numba import njit

_C1 = (1.0, -8.0, 8.0, -1.0)  # weights for offsets -2, -1, +1, +2
_O1 = (-2, -1, 1, 2)


@njit(inline="always")
def d1(U, c, i, j, k, d, idx):
    """:math:`\\partial_d U_c` at ``(i, j, k)``; ``idx`` holds inverse spacings."""
    if d == 0:
        return (U[c, i - 2, j, k] - 8.0 * U[c, i - 1, j, k] + 8.0 * U[c, i + 1, j, k]
                - U[c, i + 2, j, k]) * (idx[0] / 12.0)
    if d == 1:
        return (U[c, i, j - 2, k] - 8.0 * U[c, i, j - 1, k] + 8.0 * U[c, i, j + 1, k]
                - U[c, i, j + 2, k]) * (idx[1] / 12.0)
    return (U[c, i, j, k - 2] - 8.0 * U[c, i, j, k - 1] + 8.0 * U[c, i, j, k + 1]
            - U[c, i, j, k + 2]) * (idx[2] / 12.0)


@njit(inline="always")
def d2(U, c, i, j, k, a, b, idx):
    """:math:`\\partial_a \\partial_b U_c` at ``(i, j, k)``."""
    if a == b:
        if a == 0:
            s = (-U[c, i - 2, j, k] + 16.0 * U[c, i - 1, j, k] - 30.0 * U[c, i, j, k]
                 + 16.0 * U[c, i + 1, j, k] - U[c, i + 2, j, k])
        elif a == 1:
            s = (-U[c, i, j - 2, k] + 16.0 * U[c, i, j - 1, k] - 30.0 * U[c, i, j, k]
                 + 16.0 * U[c, i, j + 1, k] - U[c, i, j + 2, k])
        else:
            s = (-U[c, i, j, k - 2] + 16.0 * U[c, i, j, k - 1] - 30.0 * U[c, i, j, k]
                 + 16.0 * U[c, i, j, k + 1] - U[c, i, j, k + 2])
        return s * (idx[a] * idx[a] / 12.0)
    s = 0.0
    for p in range(4):
        for q in range(4):
            ii, jj, kk = i, j, k
            op, oq = _O1[p], _O1[q]
            if a == 0:
                ii += op
            elif a == 1:
                jj += op
            else:
                kk += op
            if b == 0:
                ii += oq
            elif b == 1:
                jj += oq
            else:
                kk += oq
            s += _C1[p] * _C1[q] * U[c, ii, jj, kk]
    return s * (idx[a] * idx[b] / 144.0)


# --- direction-specialised versions -------------------------------------------
# Numba cannot always prove that a loop index ``d`` is a constant, so the
# generic ``d1``/``d2`` above keep a branch in the innermost loop. The hot
# kernels call these fixed-direction variants instead, which compile to
# straight-line code (~2x faster for the ADM RHS).


@njit(inline="always")
def dx(U, c, i, j, k, idx):
    return (U[c, i - 2, j, k] - 8.0 * U[c, i - 1, j, k] + 8.0 * U[c, i + 1, j, k]
            - U[c, i + 2, j, k]) * (idx[0] / 12.0)


@njit(inline="always")
def dy(U, c, i, j, k, idx):
    return (U[c, i, j - 2, k] - 8.0 * U[c, i, j - 1, k] + 8.0 * U[c, i, j + 1, k]
            - U[c, i, j + 2, k]) * (idx[1] / 12.0)


@njit(inline="always")
def dz(U, c, i, j, k, idx):
    return (U[c, i, j, k - 2] - 8.0 * U[c, i, j, k - 1] + 8.0 * U[c, i, j, k + 1]
            - U[c, i, j, k + 2]) * (idx[2] / 12.0)


@njit(inline="always")
def dxx(U, c, i, j, k, idx):
    return (-U[c, i - 2, j, k] + 16.0 * U[c, i - 1, j, k] - 30.0 * U[c, i, j, k]
            + 16.0 * U[c, i + 1, j, k] - U[c, i + 2, j, k]) * (idx[0] * idx[0] / 12.0)


@njit(inline="always")
def dyy(U, c, i, j, k, idx):
    return (-U[c, i, j - 2, k] + 16.0 * U[c, i, j - 1, k] - 30.0 * U[c, i, j, k]
            + 16.0 * U[c, i, j + 1, k] - U[c, i, j + 2, k]) * (idx[1] * idx[1] / 12.0)


@njit(inline="always")
def dzz(U, c, i, j, k, idx):
    return (-U[c, i, j, k - 2] + 16.0 * U[c, i, j, k - 1] - 30.0 * U[c, i, j, k]
            + 16.0 * U[c, i, j, k + 1] - U[c, i, j, k + 2]) * (idx[2] * idx[2] / 12.0)


@njit(inline="always")
def dxy(U, c, i, j, k, idx):
    return (dy(U, c, i - 2, j, k, idx) - 8.0 * dy(U, c, i - 1, j, k, idx)
            + 8.0 * dy(U, c, i + 1, j, k, idx) - dy(U, c, i + 2, j, k, idx)) * (idx[0] / 12.0)


@njit(inline="always")
def dxz(U, c, i, j, k, idx):
    return (dz(U, c, i - 2, j, k, idx) - 8.0 * dz(U, c, i - 1, j, k, idx)
            + 8.0 * dz(U, c, i + 1, j, k, idx) - dz(U, c, i + 2, j, k, idx)) * (idx[0] / 12.0)


@njit(inline="always")
def dyz(U, c, i, j, k, idx):
    return (dz(U, c, i, j - 2, k, idx) - 8.0 * dz(U, c, i, j - 1, k, idx)
            + 8.0 * dz(U, c, i, j + 1, k, idx) - dz(U, c, i, j + 2, k, idx)) * (idx[1] / 12.0)


@njit(inline="always")
def grad(U, c, i, j, k, idx, out):
    """First derivatives of ``U[c]`` into ``out[0:3]``."""
    out[0] = dx(U, c, i, j, k, idx)
    out[1] = dy(U, c, i, j, k, idx)
    out[2] = dz(U, c, i, j, k, idx)


@njit(inline="always")
def hess(U, c, i, j, k, idx, out):
    """Second derivatives of ``U[c]`` into the symmetric 3x3 ``out``."""
    out[0, 0] = dxx(U, c, i, j, k, idx)
    out[1, 1] = dyy(U, c, i, j, k, idx)
    out[2, 2] = dzz(U, c, i, j, k, idx)
    out[0, 1] = out[1, 0] = dxy(U, c, i, j, k, idx)
    out[0, 2] = out[2, 0] = dxz(U, c, i, j, k, idx)
    out[1, 2] = out[2, 1] = dyz(U, c, i, j, k, idx)
