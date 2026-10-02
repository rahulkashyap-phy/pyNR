(sec-figure-data)=
# Reproducing the documentation figures

The figures in these pages are drawn from simulation data stored in
`docs/data/`. The data are **not** part of the repository. When they are
missing, the build shows a placeholder for each figure that links here.

## What is needed

```{table} Data needed by the documentation figures.
:name: tab-figure-data

| figure | produced by | files used for the plot | size |
|---|---|---|---|
| {numref}`fig-gauge-wave` | `par/gauge_wave.par` at $\Delta x = 0.02$ ($t=10$) and $\Delta x = 0.04, 0.02, 0.01$ ($t=1$) | `gauge_wave/*/alp_profile.dat`, `parameters.par`, `pynr.log` | ≈ 50 KB |
| {numref}`fig-kerr-constraints` | `par/kerr_schild.par` | `kerr_schild/H.norm2.asc`, `H.maximum.asc`, `parameters.par`, `pynr.log` | ≈ 25 KB |
| {numref}`fig-perturbed-psi4` | `par/schwarzschild_perturbed.par` | `schwarzschild_perturbed/mp_Psi4_l{2,4}_m0_r6.00.asc`, `parameters.par`, `pynr.log` | ≈ 20 KB |
```

The plots need about **92 KB** of data. `save` stores all ASCII outputs of
each run (every reduction and every $\Psi_4$ multipole at both radii), about
**0.9 MB**, so the stored runs can also be analysed with kuibit. The rendered
PNGs add about 0.2 MB. The 2D/3D HDF5 outputs (~30 MB) are never stored.

## Generating the data

```bash
source .venv/bin/activate                     # see Installation
mkdir -p runs && cd runs
pynr run ../par/kerr_schild.par               # 57 s on an Apple M3 Pro, 12 cores (6P+6E)
pynr run ../par/schwarzschild_perturbed.par   # ~10 min on an Apple M3 Pro, 12 cores (6P+6E)
cd ..
python scripts/make_doc_figures.py save --runs runs   # copies the data, runs the gauge-wave cases (~10 s)
sphinx-build -b html docs docs/_build/html            # figures are rendered from docs/data
```

`python scripts/make_doc_figures.py plot` renders the figures without
building the docs. Every docs build also runs it automatically, through
`docs/conf.py`.

## Layout of `docs/data/`

| folder | contents |
|---|---|
| `gauge_wave/<tag>/` | `alp_profile.dat` (columns: $x$, $\alpha$, $\alpha_\text{exact}$), `parameters.par`, `pynr.log` |
| `kerr_schild/` | `*.asc` reductions, `parameters.par`, `pynr.log`, `kerr_schild.par` |
| `schwarzschild_perturbed/` | `mp_Psi4_l*_m*_r*.asc`, `*.asc` reductions, metadata |

`kerr_schild/` and `schwarzschild_perturbed/` are kuibit-readable run
directories: `SimDir("docs/data/schwarzschild_perturbed").gws[6.0][(2, 0)]`.

Each rendered figure comes with a numbered table of its run settings. The
table is read from the stored `parameters.par` and `pynr.log`, so the
figure and the settings it shows always match.
