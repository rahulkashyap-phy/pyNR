# `pynr/kernels/` — compute kernels

Everything that loops over grid points. Kernels take plain arrays and
scalars, so they can be used without the framework.

| file | kernel(s) |
|---|---|
| `fd.py` | 4th-order stencils `d1, d2` and direction-specialised `dx … dyz, grad, hess` |
| `adm.py` | `adm_rhs`, `adm_constraints`, `weyl_psi4` (Numba, parallel) + variable indices |
| `adm_numpy.py` | vectorised NumPy reference `adm_rhs` (readable; used to cross-check the Numba kernel) |
| `boundary.py` | static/radiative RHS boundary, periodic and flat state syncs |
| `dissipation.py` | Kreiss-Oliger dissipation |

State layout: `U[16, nx, ny, nz]` = `gxx gxy gxz gyy gyz gzz kxx … kzz alp betax betay betaz`.

## Run a kernel on its own

```python
import numpy as np
from pynr.kernels import adm
from pynr.thorns.exact import kerr_schild

h = 0.1
ax = [c + h * np.arange(-10, 11) for c in (3.0, 1.0, 2.0)]
X, Y, Z = np.meshgrid(*ax, indexing="ij")
g, K, alp, beta = kerr_schild(0, X, Y, Z, 1.0, 0.7)
U = np.empty((16, *X.shape)); U[:6], U[6:12], U[12], U[13:] = g, K, alp, beta
rhs = np.zeros_like(U)
adm.adm_rhs(U, rhs, np.array([1/h]*3), 3, 0, True, *ax, 0.0)
print("max |dU/dt| (truncation error, should be small):", np.abs(rhs[:, 3:-3, 3:-3, 3:-3]).max())
```

Benchmark: `python scripts/benchmark.py 96`. Threads: `NUMBA_NUM_THREADS`.
Tests: `pytest tests/test_kernels.py`. The first call compiles (~10 s), and
the compiled code is cached in `__pycache__/`.
