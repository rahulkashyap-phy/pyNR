(sec-decisions)=
# Decision log

Each decision records **who decided**:

- **Rahul**: decided by Rahul Kashyap;
- **Claude → Rahul**: suggested by Claude (the AI assistant used during development) and accepted by Rahul;
- **Claude (impl.)**: an implementation detail chosen by Claude while implementing an agreed goal, recorded so it can
  be revisited.

New decisions are appended with the next number; superseded ones are marked, never deleted. Template:
[templates](templates.md).

```{table} Decisions taken during development.
:name: tab-decisions

| id | date | decision | decided by | why / alternatives | consequences |
|---|---|---|---|---|---|
| D-001 | 2026-09-26 | Structure pyNR like the Einstein Toolkit: flesh + thorns, ET `.par` syntax, schedule bins | Rahul | familiar to ET users and students; components replaceable | `pynr/cactus`, `pynr/thorns`, [Framework](../framework.md) |
| D-002 | 2026-09-26 | Staged scope: uniform grid → ADM → BH initial data → perturbation → $\Psi_4$ on geodesic spheres | Rahul | learn 3+1 first, add capabilities one at a time | [Roadmap](index.md) |
| D-003 | 2026-09-26 | Performance through Numba, "as close to C++ as possible" | Rahul | stays Python, compiled loops | `pynr/kernels`, [Performance](../performance.md) |
| D-004 | 2026-09-26 | NumPy reference kernels next to the Numba ones | Claude → Rahul | readable lecture version; cross-check in tests; GPU starting point | `adm_numpy.py`, `test_numba_matches_numpy` |
| D-005 | 2026-09-26 | Output in Carpet formats (HDF5, CarpetIOScalar, Multipole ASCII) so kuibit reads runs unchanged | Rahul | reuse kuibit and its plotting scripts | [Visualisation](../visualization.md) |
| D-006 | 2026-09-26 | Lecture notes live in docstrings; notes imported from TiddlyWiki | Rahul | code, docs and notes evolve together | `scripts/tiddlywiki2md.py` |
| D-007 | 2026-09-26 | Sphinx + MyST (not mkdocs, not Quarto) | Claude → Rahul | autodoc of RST/math docstrings; LaTeX/PDF builder; numbered refs | `docs/conf.py` |
| D-008 | 2026-09-26 | Codespaces (GitHub Education) + Binder for running online | Rahul | students run without installing | `.devcontainer/`, `binder/` |
| D-009 | 2026-09-26 | Kerr-Schild + excision for black holes; isotropic punctures kept as documented failures | Claude → Rahul | measured: puncture fails at $t\lesssim0.7M$ for any $\Delta x$ | problems 3–6 |
| D-010 | 2026-09-26 | Defaults: 4th-order FD, KO dissipation (order 6), RK4, CFL 0.25 | Claude (impl.) | standard, robust choices for ADM teaching runs | `kernels/fd.py`, `MoL` |
| D-011 | 2026-09-26 | $\Psi_4 = -(E-iB)\bar m\bar m$ with the WeylScal4/kuibit sign; ET Multipole SWSH phase | Claude (impl.) | compatible with ET and kuibit; pinned by tests | `test_psi4_linear_wave` |
| D-012 | 2026-09-26 | Icosahedral geodesic spheres for extraction quadrature | Claude (impl.) | user asked for a geodesic grid; no pole singularity | `utils/geodesic.py` |
| D-013 | 2026-09-26 | Ricci from contracted $\partial\Gamma$ only; direction-specialised stencils | Claude (impl.) | fewer operations; numba ≡ numpy test guards it | `kernels/adm.py` |
| D-014 | 2026-09-26 | Abort runs on NaN/Inf or $\lvert u\rvert > 10^{10}$ (`MoL::abort_above`) | Claude (impl.) | stop instead of stepping on garbage | `MoL::check_nan_every` |
| D-015 | 2026-10-01 | Apache-2.0 + NOTICE + CITATION.cff + per-file SPDX headers | Claude → Rahul | attribution kept in every redistribution and derived work; GPL-3.0 §7(b) and MIT considered | `LICENSE`, `NOTICE`, [License](../license.md) |
| D-016 | 2026-10-01 | Math in docstrings as `$…$` / `$$…$$ (label)`; numbered equations, tables, figures | Rahul | readable source; book-like references | `docs/conf.py` hook |
| D-017 | 2026-10-01 | Figures drawn from stored data (92 KB tracked) with run-settings tables and placeholders | Rahul | reproducible figures; docs build without data | `scripts/make_doc_figures.py`, [Reproducing figures](../reproducing-figures.md) |
| D-018 | 2026-10-01 | Bare repo + worktrees at `rmwt/<remote>/<branch>`; `main` → origin + rkpvt, `rkdev` → rkpvt only | Rahul | same layout as the other `gwt_*` repos; dev history private | — |
| D-019 | 2026-10-01 | Commit identity Rahul Kashyap <rahulkashyap@iitb.ac.in>; history rewritten | Rahul | consistent public authorship | — |
| D-020 | 2026-10-02 | No Claude/Anthropic attribution in commits; existing trailers removed | Rahul | sole authorship of the code | — |
| D-021 | 2026-10-02 | One output root `simulations/` shared by CLI and notebooks (`PYNR_OUTPUT_DIR`, `--output-root`) | Claude → Rahul | run in a terminal, plot in Jupyter | `pynr/paths.py` |
| D-022 | 2026-10-02 | Notebooks control their own output (Settings cell: `OUTPUT_ROOT`, `RUN_SIMULATIONS`) | Rahul | — | `notebooks/` |
| D-023 | 2026-10-02 | Docs CI: HTML artifact while private; Pages only when public; matplotlib in docs extra | Claude → Rahul | deploy failed on the private repo | `docs.yml` |
| D-024 | 2026-10-02 | Architecture model with typed, directed edges (`uses`/`requires`/`reads`/`registers`), flows, layers, drift check | Claude → Rahul | Rahul required the direction of "depends on" to be explicit | `arch/`, [Architecture](../architecture.md) |
| D-025 | 2026-10-02 | Custom YAML model + Mermaid/Graphviz/Cytoscape; not LikeC4/Structurizr | Claude → Rahul | keeps physics fields (equations, stages, grid functions) | `arch/render.py` |
| D-026 | 2026-10-02 | Developer rules for maintainable graphs (literal names, documented hooks, edges on the initiator) | Rahul | graph must stay maintainable as the code changes | [Developer guide](../developer-guide.md) |
| D-027 | 2026-10-02 | PDF lecture notes, documentation graph, full API list, software-engineering section | Rahul | — | `docs/lecture_notes.md` |
| D-028 | 2026-10-02 | Per-problem workflows; costs always state the machine | Rahul | — | problem pages, `pynr/machine.py` |
| D-029 | 2026-10-02 | Roadmap section with plans, this decision log and open suggestions | Rahul | keep the reasoning next to the code | this section |
| D-030 | 2026-10-02 | rkdev-only content; `main` updated only by tree promotion (rkdev tree − `.rkdev-only`, parent `main`) | Rahul (option suggested by Claude) | private material never enters `main`'s public history; repeated squash merges conflict | `scripts/promote_to_main.sh` (rkdev) |
| D-031 | 2026-10-02 | Amber banner and PDF watermark on rkdev docs | Rahul | make the personal branch unmistakable | `BRANCH_BANNERS` in `docs/conf.py` |
| D-032 | 2026-10-02 | Promotion rules and `CLAUDE.md` are themselves rkdev-only | Rahul | — | `.rkdev-only` |
```
