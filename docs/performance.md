# Performance

## How the kernels are built

- **One fused loop per physics operation.** `adm_rhs` computes the metric
  derivatives, the Christoffel symbols, the Ricci tensor and all 16
  right-hand sides point by point, in a single pass over memory.
- `@njit(parallel=True, fastmath=True, cache=True, error_model="numpy")`:
  threads over the outer `i` index, LLVM optimisations as in `-O3 -ffast-math`,
  and on-disk caching of the machine code.
- Direction-specialised stencils (`pynr.kernels.fd.dx, dxy, ...`). Numba
  then emits straight-line code with no branches on the direction index.
- The Ricci tensor needs only the two contractions of $\partial\Gamma$, not all
  162 components (see `pynr.kernels.adm`).
- Kreiss-Oliger dissipation loops with the contiguous index innermost, so it
  vectorises (SIMD).

## Measured (Apple M-series laptop, 12 threads, Python 3.14, Numba 0.67)

| kernel | grid | time | per point |
|---|---|---|---|
| ADM RHS, 1 thread | $64^3$ | 131 ms | 670 ns |
| ADM RHS, 12 threads | $96^3$ | 78 ms | 107 ns (≈1.3 µs·thread) |
| KO dissipation, 16 vars, 12 threads | $96^3$ | 8.5 ms | 0.7 ns / var |

Reproduce with `python scripts/benchmark.py 96`.

A full RK4 step of problem 6 ($135^3$ points, ADM + dissipation + boundaries)
takes 1.4 s on this laptop: 576 steps in 823 s.

## Where the remaining factor lies

A hand-tuned C++ ADM kernel would be roughly 3–5× faster per core. The gap
comes from the per-point scratch arrays (`g`, `gu`, `dg`, ...): LLVM cannot
prove they don't alias one another, so it keeps them in memory instead of
registers, and it cannot vectorise across grid points. The planned fix, the
first item on the [roadmap](roadmap.md), is to process a whole row of `k` at a
time, with every tensor operation as a short, SIMD-friendly loop over `k`.
This is the layout that code generators such as Kranc/McLachlan emit.
