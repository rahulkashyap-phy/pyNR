# `arch/` — architecture model, extraction, drift check, rendering

| file | role |
|---|---|
| `model.yaml` | **curated model** (hand-written, committed): components, typed edges (`uses`, `requires`, `reads`, `registers`), data `flows`, `layers`, `views`, and links to source, docs, notes and equations |
| `extract.py` | **extracted graph** from the code (`ast` imports, `Thorn.requires`, `sim.thorn(...)`, callback registrations) plus, for every `par/*.par`, the schedule, grid functions, settings and output files → `docs/_generated/arch/extracted.json` |
| `check_drift.py` | compares the two and fails on drift (pointers, coverage, edges, layers, flows, problem pages, README block; `--branch main` also forbids rkdev-only paths) |
| `render.py` | Graphviz views, component neighbourhoods, per-problem workflows, problem × thorn matrix, cost table, Cytoscape data, README Mermaid block |
| `timings.yaml` | measured cost of each problem with the machine it ran on (`python arch/extract.py --record-timing simulations/<problem>`) |
| `snapshots/` | extracted graph at each release tag, for diffing the architecture between versions |

```bash
python arch/check_drift.py              # run before committing (also part of pytest)
python arch/render.py --readme          # regenerate diagrams + the README block
python arch/extract.py --print          # inspect the extracted edges
```

The editing rules are in [docs/developer-guide.md](../docs/developer-guide.md). In short:
- write each edge on the component that initiates it;
- keep cross-component access literal (`sim.thorn("X")`, `"Thorn::var"`);
- respect the layers;
- update the model in the same commit as the code.

Optional pre-commit hook (`.git/hooks/pre-commit` in the worktree):

```bash
#!/bin/sh
exec .venv/bin/python arch/check_drift.py
```
