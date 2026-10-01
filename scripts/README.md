# `scripts/` — tools

| script | usage |
|---|---|
| `benchmark.py` | `python scripts/benchmark.py 96` — time the ADM RHS and KO kernels (set `NUMBA_NUM_THREADS` to vary threads) |
| `make_doc_figures.py` | `save --runs <dir>`: copy run data into `docs/data/`; `plot`: redraw `docs/figures/*.png` and their run-settings tables from `docs/data/` only (see `docs/data/README.md`) |
| `tiddlywiki2md.py` | `python scripts/tiddlywiki2md.py <tiddlers/ \| wiki.html \| export.json> docs/notes --tag pyNR` — import notes into the docs |

Both need only an installed `pynr` (`pip install -e .` from the repository root).
