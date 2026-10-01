# `notebooks/` — tutorials

| notebook | content | run time |
|---|---|---|
| `01_gauge_wave.ipynb` | first run, comparison with the exact solution, convergence test, kuibit | ~1 min |
| `02_perturbed_black_hole.ipynb` | perturbed Schwarzschild, Ψ₄ multipoles, why ADM fails | ~10 min |

Run locally:

```bash
source .venv/bin/activate         # from the repository root (see docs/installation.md)
pip install -e ".[notebook]"
python -m ipykernel install --user --name pynr --display-name "Python (pyNR .venv)"
cd notebooks && jupyter lab       # or open the .ipynb in VS Code -> Select Kernel -> Python (pyNR .venv)
```

Each notebook starts with a **Settings** cell: `OUTPUT_ROOT` (default
`<repo>/simulations`, the same folder `pynr run` writes to) and
`RUN_SIMULATIONS`. You can run a parameter file in a terminal and only plot in
the notebook, or run from the notebook; both read and write
`simulations/<run name>/`. The notebooks use relative paths (`../par/...`), so
start Jupyter in this folder. Online: see `docs/running-online.md`.
