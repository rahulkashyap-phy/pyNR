# 2. Linear gravitational wave

**File:** `par/linear_wave.par`

## Physics

A small ($A = 10^{-8}$) plane wave travelling along $x$ in TT gauge,

$$ \gamma_{yy} = 1 + b,\quad \gamma_{zz} = 1 - b,\quad b = A\sin\frac{2\pi(x-t)}{d},\qquad
K_{ij} = -\tfrac12\partial_t\gamma_{ij},\quad \alpha = 1,\ \beta^i = 0. $$

This is a solution of the linearised Einstein equations, and so of the full
equations up to $\mathcal{O}(A^2) \sim 10^{-16}$.

## Expected results

- $\gamma_{yy} - 1$ keeps its amplitude $A$ and returns to its initial
  profile at every crossing time $t = n d$. Measured: $\max(\gamma_{yy}) - 1 = 9.980\times10^{-9}$
  at $t = 0, 1, \dots, 5$, unchanged to 4 digits (the grid-sampled peak of $A = 10^{-8}$).
- $\Psi_4$ on the $+x$ axis. There the tetrad has $e_\theta = -\hat z$ and
  $e_\phi = \hat y$, so $h_+ = -b$ and
  $$\Psi_4 = \ddot h_+ - i\ddot h_\times = A\left(\tfrac{2\pi}{d}\right)^2\sin\frac{2\pi(x-t)}{d},\qquad \operatorname{Im}\Psi_4 = 0.$$
  This is the unit test `tests/test_kernels.py::test_psi4_linear_wave`, and it
  fixes the sign conventions of `WeylScal4`.

## Exercises

1. Plot `Psi4r.xy.h5` at several times and verify the propagation speed.
2. Rotate the wave: which components of $\Psi_4$ change if the wave travels
   along $z$ (the polar axis of the tetrad)?
