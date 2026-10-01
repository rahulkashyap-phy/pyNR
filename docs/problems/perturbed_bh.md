# 6. Perturbed black hole and gravitational-wave extraction

**File:** `par/schwarzschild_perturbed.par` · **Notebook:** `notebooks/02_perturbed_black_hole.ipynb`

## Physics

A Schwarzschild black hole in Kerr-Schild coordinates, with the metric
multiplied by $1 + \epsilon$ (Eq. {eq}`eq-perturbation`), with the profile

$$ \epsilon = A\,e^{-(r-r_0)^2/\sigma^2}\,Y_{20}(\theta),\qquad A = 10^{-3},\ r_0 = 4M,\ \sigma = M. $$ (eq-perturbation-profile)

Part of the pulse falls into the hole and part escapes. The hole rings down
in its quasi-normal modes, $\Psi_4^{\ell m} \propto e^{-i\omega t}$, and for
$\ell = 2$ the fundamental mode is

$$ M\omega_{220} = 0.3737 - 0.0890\,i \quad (\text{period } 16.8M,\ \text{decay time } 11.2M). $$ (eq-qnm-220)

$\Psi_4$ comes from the electric and magnetic parts of the Weyl tensor
(`WeylScal4`, Eq. {eq}`eq-psi4-tetrad`). It is interpolated to geodesic spheres of radius $6M$ and $8M$
and projected onto ${}_{-2}Y_{\ell m}$ (`Multipole`, Eq. {eq}`eq-multipole-projection`).

## Expected results

Measured with the parfile as shipped. {numref}`tab-settings-perturbed-psi4`
lists the full settings, and {numref}`fig-perturbed-psi4` shows the extracted
signal.

```{include} ../figures/perturbed_psi4.md
```

- **Symmetry.** Only $m = 0$ modes are excited. $\operatorname{Im}\Psi_4^{20} \sim 10^{-16}$ and
  odd-$\ell$ modes $\sim 10^{-12}$ (round-off), as expected for an axisymmetric,
  equatorially symmetric perturbation.
- **Arrival time.** The burst reaches $r = 6M$ at $t \approx 8$–$10M$ and $r = 8M$ about $2M$ later.
- **Stability.** $\max|H|$ is $\sim 10^{-2}$ until $t \approx 15M$, then grows
  exponentially (e-folding $\approx 7M$) to $O(1)$ by $t = 36M$. The growing
  part oscillates with a period of ~3–4$M$, and $\ell = 4$ overtakes $\ell = 2$.
  This is the ADM constraint-violating mode from problem 5 ({numref}`fig-kerr-constraints`), not physics.
- **No clean quasi-normal ringdown yet.** The $\ell = 2$ QNM period ($16.8M$) is too
  long for the ~$15M$ window between the burst and the instability, and fits
  of $e^{-t/\tau}\cos\omega t$ do not return $\omega_{220}$. With $A = 10^{-2}$
  the physical signal is 10× larger, but the run fails at $t \approx 26M$.

What this problem demonstrates today is the **extraction machinery**:
$\Psi_4$ on the grid, interpolation to geodesic spheres, ${}_{-2}Y_{\ell m}$
projection and kuibit-compatible output. Validating the physics (the QNM
frequency) needs a formulation that stays stable for $\gtrsim 100M$. That is
the BSSN/Z4c milestone on the [roadmap](../roadmap.md), and this problem is
its acceptance test.

## Caveats

- The perturbation violates the Hamiltonian constraint at $\mathcal{O}(A)$.
- Finite extraction radius: $\Psi_4(r)$ differs from $\Psi_4(\infty)$ at
  $\mathcal{O}(M/r)$.
- The ADM system limits the useful part of the run to $t \lesssim 20M$ (see problem 5).
