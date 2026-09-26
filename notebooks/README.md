# `notebooks/` — tutorials

| notebook | content | run time |
|---|---|---|
| `01_gauge_wave.ipynb` | first run, comparison with the exact solution, convergence test, kuibit | ~1 min |
| `02_perturbed_black_hole.ipynb` | perturbed Schwarzschild, Ψ₄ multipoles, why ADM fails | ~10 min |

Run locally:

```bash
pip install -e ".[notebook]"      # from the repository root
cd notebooks && jupyter lab
```

The notebooks use relative paths (`../par/...`), so start Jupyter in this
folder. Online: open the repository in GitHub Codespaces or on Binder (see
`docs/running-online.md`). Outputs are written next to the notebooks and are
git-ignored.
