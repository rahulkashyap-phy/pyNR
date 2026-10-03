(sec-software-engineering)=
# Architecture, modularity and software engineering

This chapter describes how pyNR is built as software, and why. The physics is in the lecture-note chapters.

## Design

pyNR follows the Cactus/Einstein Toolkit split:
- the **flesh**, {mod}`pynr.cactus`, knows nothing about physics. It reads parameter files, holds parameters, the
  schedule and grid functions, and runs the main loop;
- **thorns**, {mod}`pynr.thorns`, contain the physics, analysis and I/O. Each declares parameters, registers grid
  functions and schedules routines;
- **kernels**, {mod}`pynr.kernels`, are the only code that loops over grid points, in Numba with a NumPy reference;
- **utils**, {mod}`pynr.utils`, are generic numerical methods.

Because thorns only meet through grid functions, parameters and a few hooks, any one of them can be replaced
without touching the others. Swapping the initial data, the formulation, the integrator, the kernel backend or the
output format is a local change ({numref}`fig-arch-full`, [Framework](framework.md)).

## Modularity rules

The [architecture model](architecture.md) makes the dependencies explicit and checks them:
- four typed, directed edges: `uses`, `requires`, `reads`, `registers` ({numref}`tab-edge-types`);
- layers, which restrict who may call whom ({numref}`tab-layers`);
- inversion of control through exactly four hooks: schedule bins, `MoL.register_evolved`, `MoL.add_rhs_hook`, and
  on-demand grid functions;
- data flow recorded per schedule bin, separately from code dependencies.

The rules for keeping this true while the code changes are in the [developer guide](developer-guide.md)
({numref}`tab-dev-rules`).

## Backends and performance engineering

Every hot loop exists twice: a Numba kernel ({mod}`pynr.kernels.adm`) and a vectorised NumPy reference
({mod}`pynr.kernels.adm_numpy`). The test suite checks that the two agree, and {mod}`pynr.backends` selects one
at run time. The optimisation history (direction-specialised stencils, the contracted Ricci tensor, loop order for
dissipation) and the remaining gap to C++ are measured on a stated machine in [Performance](performance.md). The next
step, row-vectorised kernels, is on the [roadmap](roadmap/index.md).

## Verification and validation

- **Unit tests:** parameter-file parsing, schedule ordering, interpolation, quadrature, spin-weighted harmonics.
- **Convergence tests against exact solutions:** the Kerr-Schild right-hand side and constraints, and the gauge wave,
  all at 4th order (Eq. {eq}`eq-convergence-order`, {numref}`fig-gauge-wave`).
- **Cross-implementation:** Numba ≡ NumPy.
- **Physics conventions pinned by tests:** $\Psi_4$ of a linear plane wave (Eq. {eq}`eq-psi4-tetrad`).
- **Format compatibility:** kuibit reads pyNR runs (round-trip test).
- **Failure handling:** runs abort on NaN or blow-up, instead of producing garbage.
- **Honest negative results:** the problem set documents what plain ADM cannot do, with measurements.

## Reproducibility

- Every run writes its parameter file, the full `parameters.par` and `pynr.log`. The log includes the machine block:
  CPU, cores, RAM, OS, library versions and threads ({mod}`pynr.machine`).
- One output root (`simulations/`, {mod}`pynr.paths`) is shared by the command line and the notebooks.
- Documentation figures are drawn from stored data at build time, each with a settings table, and with a placeholder
  when the data are missing ([Reproducing the figures](reproducing-figures.md)).
- Costs always state the machine they were measured on ({numref}`tab-problem-cost`).
- At each release the extracted architecture graph is snapshotted, so structural changes can be diffed.

## Documentation as code

- Docstrings are the lecture notes. Math is written as `$…$` / `$$…$$ (label)`; equations, tables and figures are
  numbered and cross-referenced.
- The same sources build the HTML site and the PDF lecture notes.
- The architecture drift check and the per-problem workflows keep diagrams, code and text consistent.
- The roadmap records plans and decisions, and who made them ([decision log](roadmap/decisions.md)).

## Process

- Development happens on `rkdev`. The public `main` branch is updated from it by the maintainer.
- CI runs the tests (Linux and macOS, several Python versions), the drift check, and the HTML build, which it deploys to GitHub Pages. The PDF lecture notes are built locally with `make -C docs all`.
- Releases are tagged on `main`; PyPI and Zenodo releases are planned.
- License: Apache-2.0. Attribution is required through `NOTICE` and the per-file headers, and citation through
  `CITATION.cff` ([License](license.md)).

## Known limitations and technical debt

- **Plain ADM only:** it is weakly hyperbolic, so black-hole runs last tens of $M$.
- **No moving punctures:** isotropic punctures fail early.
- **One state block:** MoL integrates a single state block.
- **One node:** a uniform grid with no mesh refinement, and no MPI or GPU yet.
- **Kernel speed:** the kernels are 3–5× slower than tuned C++.

Each of these is a [roadmap](roadmap/index.md) item with an acceptance test.
