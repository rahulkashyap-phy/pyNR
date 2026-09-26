r"""Kreiss-Oliger artificial dissipation.

Centred finite differences do not damp modes at the grid scale; nonlinear
terms feed them and they grow. Kreiss-Oliger dissipation adds a
higher-derivative term, of order higher than the scheme, to every RHS:

.. math::

    \partial_t u \mathrel{+}= \frac{\epsilon}{64}\sum_{d} h_d^{5}\,\partial_d^{6} u
    \approx \frac{\epsilon}{64}\sum_d \frac{1}{h_d}
    \left(u_{-3} - 6u_{-2} + 15u_{-1} - 20u_0 + 15u_{+1} - 6u_{+2} + u_{+3}\right).

For a Fourier mode :math:`e^{ikx}` the stencil gives :math:`-(2-2\cos kh)^3 \le 0`,
so the term only damps, and most strongly at :math:`kh=\pi`. It is
:math:`\mathcal{O}(h^5)`, below the 4th-order accuracy of the derivatives.
Stability needs :math:`0 \le \epsilon \lesssim 1` (with CFL factor 0.25).
"""

from numba import njit, prange


@njit(parallel=True, fastmath=True, cache=True)
def add_ko_dissipation(U, rhs, idx, ng, eps, vars_mask):
    nv, nx, ny, nz = U.shape
    c0 = eps / 64.0
    for i in prange(ng, nx - ng):
        for c in range(nv):
            if not vars_mask[c]:
                continue
            for j in range(ng, ny - ng):
                for k in range(ng, nz - ng):  # contiguous index innermost -> SIMD
                    sx = (U[c, i - 3, j, k] - 6.0 * U[c, i - 2, j, k] + 15.0 * U[c, i - 1, j, k]
                          - 20.0 * U[c, i, j, k] + 15.0 * U[c, i + 1, j, k]
                          - 6.0 * U[c, i + 2, j, k] + U[c, i + 3, j, k])
                    sy = (U[c, i, j - 3, k] - 6.0 * U[c, i, j - 2, k] + 15.0 * U[c, i, j - 1, k]
                          - 20.0 * U[c, i, j, k] + 15.0 * U[c, i, j + 1, k]
                          - 6.0 * U[c, i, j + 2, k] + U[c, i, j + 3, k])
                    sz = (U[c, i, j, k - 3] - 6.0 * U[c, i, j, k - 2] + 15.0 * U[c, i, j, k - 1]
                          - 20.0 * U[c, i, j, k] + 15.0 * U[c, i, j, k + 1]
                          - 6.0 * U[c, i, j, k + 2] + U[c, i, j, k + 3])
                    rhs[c, i, j, k] += c0 * (sx * idx[0] + sy * idx[1] + sz * idx[2])
