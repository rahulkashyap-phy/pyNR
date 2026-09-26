# `pynr/utils/` — numerical methods

General-purpose tools with no dependence on thorns or parameters.

| file | contents |
|---|---|
| `integrators.py` | Euler, RK2, ICN, SSP-RK3, RK4 for `dU/dt = F(t, U)`, in place with reusable buffers |
| `interpolation.py` | Lagrange interpolation from a uniform 3D grid to arbitrary points (Numba) |
| `geodesic.py` | icosahedral geodesic spheres and quadrature weights (sum = 4π) |
| `swsh.py` | spin-weighted spherical harmonics ${}_sY_{\ell m}$ (ET Multipole convention) |

## Examples

```python
import numpy as np

# integrate an ODE with the MoL integrators
from pynr.utils.integrators import rk4
u = np.array([1.0]); t, dt = 0.0, 0.1
for _ in range(10):
    rk4(u, t, dt, lambda t, U, dU: dU.__setitem__(slice(None), -U)); t += dt
print(u, np.exp(-1.0))

# quadrature + harmonics: orthonormality of -2Y_lm on a geodesic sphere
from pynr.utils.geodesic import geodesic_sphere, angles
from pynr.utils.swsh import sYlm
pts, _, w = geodesic_sphere(4); th, ph = angles(pts)
print(np.sum(w * abs(sYlm(-2, 2, 2, th, ph))**2))    # ~ 1

# interpolation
from pynr.utils.interpolation import interpolate
x = np.linspace(-1, 1, 21); X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
print(interpolate(np.sin(X) * Y, (-1, -1, -1), (0.1,)*3, np.array([[0.33, 0.5, 0.0]])))
```

Tests: `pytest tests/test_kernels.py -k "geodesic or interpolation"`.
