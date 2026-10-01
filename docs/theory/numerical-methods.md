# Numerical methods

## Grid

```{eval-rst}
.. automodule:: pynr.cactus.grid
   :no-members:
```

## Finite differences

```{eval-rst}
.. automodule:: pynr.kernels.fd
   :no-members:
```

## Method of lines and Runge-Kutta

```{eval-rst}
.. automodule:: pynr.utils.integrators
   :no-members:
```

```{eval-rst}
.. automodule:: pynr.thorns.mol
   :no-members:
```

## Artificial dissipation

```{eval-rst}
.. automodule:: pynr.kernels.dissipation
   :no-members:
```

## Boundary conditions

```{eval-rst}
.. automodule:: pynr.kernels.boundary
   :no-members:
```

## Convergence testing

For a scheme of order $p$, the error at resolution $h$ is $E(h) \approx C h^p$.
With runs at $h$ and $h/2$,

$$ p \approx \log_2 \frac{E(h)}{E(h/2)} . $$ (eq-convergence-order)

Without an exact solution, use three resolutions $h, h/2, h/4$:

$$ \frac{u_h - u_{h/2}}{u_{h/2} - u_{h/4}} \approx 2^p . $$ (eq-self-convergence)

The test suite applies Eq. {eq}`eq-convergence-order` to the gauge wave and
the Kerr-Schild RHS (`tests/`), and expects $p \approx 4$. {numref}`fig-gauge-wave`
(right) shows the same check visually.
