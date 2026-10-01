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

The notebooks use relative paths (`../par/...`), so start Jupyter in this
folder. Online: open the repository in GitHub Codespaces or on Binder (see
`docs/running-online.md`). Outputs are written next to the notebooks and are
git-ignored.
