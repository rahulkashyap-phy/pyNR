"""Time the ADM right-hand side and the dissipation kernel.

    python scripts/benchmark.py 96              # all threads
    NUMBA_NUM_THREADS=1 python scripts/benchmark.py 64
"""

import sys
import time

import numba
import numpy as np

from pynr.kernels import adm, dissipation
from pynr.thorns import exact

n = int(sys.argv[1]) if len(sys.argv) > 1 else 96
h = 0.5
ax = [h * (np.arange(n) - n / 2 + 0.5)] * 3
X, Y, Z = np.meshgrid(*ax, indexing="ij")
g, K, a, b = exact.kerr_schild(0, X, Y, Z, 1.0, 0.5)
U = np.empty((16, n, n, n))
U[:6], U[6:12], U[12], U[13:] = g, K, a, b
rhs = np.zeros_like(U)
idx = np.array([1 / h] * 3)

adm.adm_rhs(U, rhs, idx, 3, 2, True, *ax, 1.0)  # compile / load cache
reps = 3
t0 = time.perf_counter()
for _ in range(reps):
    adm.adm_rhs(U, rhs, idx, 3, 2, True, *ax, 1.0)
dt = (time.perf_counter() - t0) / reps
pts = (n - 6) ** 3
nt = numba.get_num_threads()
print(f"ADM RHS  n={n}^3 threads={nt}: {dt * 1e3:7.1f} ms  "
      f"{dt / pts * 1e9:6.1f} ns/point  {dt / pts * 1e9 * nt:6.0f} ns/point/thread")

mask = np.ones(16, dtype=np.bool_)
dissipation.add_ko_dissipation(U, rhs, idx, 3, 0.1, mask)
t0 = time.perf_counter()
dissipation.add_ko_dissipation(U, rhs, idx, 3, 0.1, mask)
dt = time.perf_counter() - t0
print(f"KO diss. n={n}^3 threads={nt}: {dt * 1e3:7.1f} ms  {dt / pts / 16 * 1e9:6.2f} ns/point/var")
