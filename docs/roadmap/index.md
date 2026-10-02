(sec-roadmap)=
# Roadmap

Capabilities are added one at a time. Each step must pass its acceptance test, usually a problem from the
[problem set](../problems/index.md), before the next one starts. This section holds what *will* be done and *why*
things were decided. The [development log](../devlog/index.md) records what *was* done.

```{toctree}
:maxdepth: 1

decisions
suggestions
templates
```

## Status

```{table} Roadmap items, status and acceptance tests.
:name: tab-roadmap

| # | item | status | acceptance test |
|---|---|---|---|
| 0 | v0.1: flesh, uniform grid, ADM, exact data, perturbation, $\Psi_4$ on geodesic spheres, Carpet output, docs, packaging | **done** (2026-09-26) | problems 1–6 run; tests pass |
| 1 | Architecture model, drift check, diagrams, PDF lecture notes, documentation graph, per-problem workflows, branch promotion | **in progress** (plan *wobbly-stirring-wren*, 2026-10) | `arch/check_drift.py` passes; HTML + PDF build without warnings |
| 2 | Performance: vectorise the ADM kernel along rows of `k` (SIMD) | planned | ≤ 200 ns/point/thread on the reference machine ([Performance](../performance.md)) |
| 3 | **BSSN** (then **Z4c**) with the Gamma-driver shift: moving punctures | planned | problem 4 runs ≥ 500 $M$ with $\min\alpha\to\approx0.3$; problem 6 shows the $\ell=2$ QNM ($\omega$ within 1 %, $\tau$ within 5 %) |
| 4 | Apparent-horizon finder (fast-flow or spectral): mass and spin | planned | Kerr $\chi=0.6$: irreducible mass and spin within 0.1 % |
| 5 | Elliptic solver (PyAMG): Brill waves, Bowen-York / TwoPunctures-style data, constraint-satisfying perturbations | planned | $H$ at $t=0$ converges to zero |
| 6 | Mesh refinement (fixed nested boxes, Berger-Oliger time stepping) | planned | extraction at $r \ge 50M$ |
| 7 | GPU backend (CuPy/JAX) from the NumPy reference kernels; MPI with `mpi4py` | planned | numba ≡ GPU to round-off |
| 8 | Matter: Valencia hydro (HLLE, reconstruction), TOV star | planned | TOV oscillation frequencies |
```

## Development plans

Approved plans are stored verbatim, one page each. Plans exist only on the `rkdev` branch; on `main` this list is
empty.

```{toctree}
:maxdepth: 1
:glob:

plans/*
```

```{table} Plans and their status.
:name: tab-plans

| plan | date | owner | status | covers roadmap item |
|---|---|---|---|---|
| `wobbly-stirring-wren` | 2026-10-02 | Rahul Kashyap | approved → in progress | 1 |
```
