"""Compute kernels.

Everything that touches every grid point lives here, written with Numba
(``@njit(parallel=True, fastmath=True, cache=True)``). Thorns call kernels;
kernels never know about thorns, parameters or I/O. Swapping the
implementation (e.g. the NumPy reference in :mod:`pynr.kernels.adm_numpy`,
or a future CuPy/JAX one) is done in :mod:`pynr.backends`.

Threads: Numba uses ``NUMBA_NUM_THREADS`` (default: all cores). Set it
before starting Python to control parallelism.
"""
