# Scientific-computing toolbox

Each numerical task in pyNR is done by one well-tested, popular library,
behind a small pyNR function so it can be swapped.

| task | used now | alternatives worth knowing |
|---|---|---|
| array storage and algebra | **NumPy** | CuPy (NVIDIA GPU), JAX (GPU/TPU, autodiff) |
| compiled grid loops | **Numba** (`@njit(parallel=True, fastmath=True)`) | Cython, Pythran, JAX `jit`, Taichi |
| finite differences | `pynr.kernels.fd` (4th order, hand-written stencils) | `findiff` (arbitrary stencils) |
| time integration of PDEs (MoL) | `pynr.utils.integrators` (RK4, RK3, ICN, RK2) | — (write your own; it's 20 lines) |
| small ODE systems (geodesics, TOV, ID radial ODEs) | **SciPy** `solve_ivp` (DOP853, LSODA) | `diffrax` (JAX) |
| elliptic PDEs (constraints / initial data) | *planned:* SciPy sparse + **PyAMG** multigrid | PETSc via `petsc4py`, spectral (`Kadath`) |
| spectral methods | NumPy/SciPy FFT | `dedalus`, `shenfun` |
| interpolation grid → points | `pynr.utils.interpolation` (Lagrange, Numba) | SciPy `RegularGridInterpolator`, `map_coordinates` |
| quadrature on spheres | `pynr.utils.geodesic` (icosahedral) | Lebedev (`quadpy`), HEALPix (`healpy`) |
| spin-weighted harmonics | `pynr.utils.swsh` | `spherical_functions`, `spherical` (Mike Boyle) |
| root finding (horizons) | *planned:* SciPy `optimize` | — |
| I/O | **h5py** (Carpet HDF5 layout) | openPMD-api, ADIOS2 |
| analysis & plots | **kuibit**, matplotlib | yt, VisIt, ParaView (read the HDF5 directly) |
| parallelism | Numba threads (one node) | `mpi4py` domain decomposition (planned) |

## Rules of thumb for fast Python

1. **No Python loops over grid points.** Write a Numba kernel, or use whole-array NumPy.
2. **Fuse.** One Numba loop that computes the full RHS per point beats many
   NumPy array expressions. Each NumPy expression streams the whole grid
   through memory, and allocates temporaries.
3. **Loop order matches memory order.** Arrays are C-ordered `[var, i, j, k]`,
   so `k` goes innermost and `prange` goes over `i`.
4. **Allocate once.** Keep work arrays between steps (see the `scratch` dict in `MoL`).
5. **Use `cache=True`**, so the JIT cost is paid once per machine, not per run.
6. **Check correctness against a slow, obvious implementation** (`pynr.kernels.adm_numpy`).
