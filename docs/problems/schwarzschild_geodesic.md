# 3. Geodesic slicing of Schwarzschild — and the puncture problem

**File:** `par/schwarzschild_geodesic.par`

## Physics

The time-symmetric Schwarzschild slice in isotropic coordinates,

$$ \gamma_{ij} = \psi^4\delta_{ij},\quad \psi = 1 + \frac{M}{2r},\quad K_{ij} = 0, $$

is evolved with $\alpha = 1$ and $\beta^i = 0$ (*geodesic slicing*). The
coordinate observers are then freely falling. The observer at the throat
$r = M/2$ (areal radius $R = 2M$) starts at rest. On the cycloid

$$ R = M(1+\cos\eta),\qquad \tau = M(\eta + \sin\eta) $$

it reaches the singularity at $\tau = \pi M$, so a *perfect* code would
crash at $t = \pi M$. A 1D spherical code with a well-resolved throat shows
this (Alcubierre, *Introduction to 3+1 Numerical Relativity*, §4.2).

## What pyNR shows

The 3D run fails much earlier, at **$t \lesssim 0.7M$, and refining the grid
makes it worse**:

| $\Delta x$ | $\max|K_{xx}| > 10^6$ at |
|---|---|
| 0.2 | $t = 0.70M$ |
| 0.1 | $t = 0.70M$ |
| 0.05 | $t = 0.30M$ |

The failure starts at the grid point nearest the puncture $r = 0$ (for
$\Delta x = 0.2$: $r = 0.33M$, where $\gamma_{xx} \approx 40$). Close to
$r = 0$ the conformal factor behaves as $\psi \sim M/2r$, so the metric
varies on the scale $r$ itself. Finite differences cannot represent that,
and the numerical Ricci tensor there is ~30 times too large. Refining the
grid does not help: a finer grid has a point even closer to the puncture,
where the metric is even steeper.

This is the **puncture problem**. It explains why modern black-hole codes

- factor out the singular conformal factor analytically (BSSN / Z4c
  "moving punctures", on the roadmap), or
- use horizon-penetrating coordinates and *excise* the interior (problems 5
  and 6, Kerr-Schild).

Excision cannot rescue this setup. With $\alpha = 1$, $\beta^i = 0$ the
light cones at any excision surface point both ways, so information would
have to flow *out of* the frozen region
(try `--set ADMEvolve::excision_radius=0.4`: the crash moves only to $t \approx 1.2M$).

## Exercises

1. Confirm the table, and use the snippet below to watch where
   $|K_{xx}|$ peaks.
2. Compute the exact $\partial_t K_{xx} = R_{xx}$ at $t = 0$ for $r = 0.33M$
   (hint: in an orthonormal frame the tidal components are $\sim M/R^3$) and
   compare with the numerical RHS.
3. Why is the time-symmetric throat nonetheless *well* resolved by the
   same grid (plot the error of $R_{ij}$ against $r$)?

```python
import numpy as np
from pynr import Simulation
sim = Simulation.from_parfile("par/schwarzschild_geodesic.par",
                              overrides={"Cactus::cctk_itlast": 0}, verbose=False)
sim.initialize()
U, g = sim.thorn("ADMBase").U, sim.grid
for _ in range(14):
    sim.step()
    K = np.abs(U[6])[g.interior]
    print(f"t={sim.time:.2f}  max|kxx|={K.max():.3e}")
```
