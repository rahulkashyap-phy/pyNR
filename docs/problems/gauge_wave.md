# 1. Gauge wave

**File:** `par/gauge_wave.par`

## Physics

Minkowski spacetime in the coordinates

$$ ds^2 = -H\,dt^2 + H\,dx^2 + dy^2 + dz^2,\qquad H = 1 - A\sin\frac{2\pi(x-t)}{d}. $$ (eq-gauge-wave-metric)

Equation {eq}`eq-gauge-wave-metric` is flat space, but the lapse $\alpha = \sqrt{H}$, the metric
$\gamma_{xx} = H$ and the curvature $K_{xx} = -\frac{\pi A}{d}\cos\frac{2\pi(x-t)}{d}/\sqrt{H}$
all travel along $x$. The harmonic slicing $\partial_t\alpha = -\alpha^2 K$ is
consistent with this exact solution. It is test 1 of the "Apples with Apples"
suite (Alcubierre et al. 2004).

## Setup

The grid is periodic in all directions and effectively 1D (3 points in $y$
and $z$). The amplitude is $A = 0.1$, the wavelength $d = 1$, and the run lasts
ten crossing times. {numref}`tab-settings-gauge-wave` lists the complete
settings of the reference run, read from its `parameters.par`.

## Expected results

```{include} ../figures/gauge_wave.md
```

- $\max\alpha$ stays at $\sqrt{1.1} = 1.0488$ and $\min\alpha$ at $\sqrt{0.9} = 0.9487$.
  The measured values drift by about $10^{-4}$ over 10 crossings.
- $H = 0$ to round-off, because the metric only depends on $x$.
- **Convergence:** the error in $\alpha$ against the exact solution falls by
  $\approx 16$ each time $\Delta x$ is halved (4th order). This is checked by
  `tests/test_evolution.py::test_gauge_wave_converges_4th_order` and shown in
  {numref}`fig-gauge-wave` (right) and `notebooks/01_gauge_wave.ipynb`.

```{include} ../_generated/arch/workflow_gauge_wave.md
```

## Exercises

1. $A = 0.5$: run to $t = 100$. The ADM system is known to be unstable on
   large-amplitude gauge waves, so measure when the run fails.
2. Measure the convergence order with `MoL::ODE_Method = "RK2"`.
