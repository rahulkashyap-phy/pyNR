# `pynr/thorns/` — thorns

Each file defines one or more thorns: parameters, grid functions and
scheduled routines. Activate them in a parfile with `ActiveThorns = "..."`.

| thorn | file | role |
|---|---|---|
| Cactus, CoordBase, Driver, Time, IO | `core.py` | always active: termination, grid extent, ghosts/backend, time step, output dir |
| ADMBase | `admbase.py` | ADM variables and initial-data / gauge selectors |
| Exact | `exact.py` | analytic spacetimes: gauge wave, linear wave, Schwarzschild (isotropic), Kerr (Kerr-Schild) |
| Perturb | `perturb.py` | Gaussian $(\ell,m)$ metric perturbation |
| ADMEvolve | `admevolve.py` | ADM evolution, slicing, boundaries, excision |
| MoL | `mol.py` | Runge-Kutta time integration, RHS hooks, blow-up abort |
| Dissipation | `dissipation.py` | Kreiss-Oliger dissipation |
| ADMConstraints | `admconstraints.py` | Hamiltonian / momentum constraints |
| WeylScal4 | `weylscal4.py` | $\Psi_4$ |
| Multipole | `multipole.py` | spin-weighted multipoles on geodesic spheres |
| IOHDF5, IOScalar, IOBasic | `io.py` | Carpet-format output, stdout table |

## Run one thorn's functionality on its own

```python
# analytic solutions (plain NumPy, no simulation needed)
import numpy as np
from pynr.thorns.exact import kerr_schild, gauge_wave
x = np.linspace(2, 4, 5)
g, K, alp, beta = kerr_schild(0.0, x, 0.0, 0.0, M=1.0, spin=0.5)
print(alp)

# every parameter of every thorn
#   python -m pynr thorns --markdown
```

Minimal parfiles that exercise a thorn: see `par/` (e.g. `gauge_wave.par`
for ADMEvolve/MoL/IO, and `schwarzschild_perturbed.par` for Perturb, WeylScal4 and Multipole).

Writing a new thorn: see `docs/framework.md`. Import your module before
building the `Simulation`, so that `@register_thorn` runs.
