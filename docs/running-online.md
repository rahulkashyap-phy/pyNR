# Running online (Codespaces, Binder)

## GitHub Codespaces (recommended)

A Codespace is a cloud VM with VS Code and JupyterLab. The repository ships
a `.devcontainer/` that installs pyNR, kuibit and JupyterLab, then warms the
Numba cache so the first run is fast.

1. Open the repository on GitHub and choose **Code → Codespaces → Create codespace on main**.
2. Wait about 3 minutes for the first build. Later starts take seconds. The
   build installs pyNR into the container's Python (`pip install -e .`),
   registers that Python as the Jupyter kernel **Python (pyNR)**, and compiles
   the kernels once.
3. Run something in the terminal: `pynr run par/gauge_wave.par`.

(sec-codespaces-jupyter)=
### Jupyter in a Codespace, with the same environment

The terminal, `pynr run` and the notebooks all use the **same Python
environment**: the container's Python, where the Codespace build installed
pyNR, kuibit and JupyterLab. There is nothing to activate. Two ways to open
the notebooks:

- **In the Codespace editor (VS Code in the browser, simplest).** Open
  `notebooks/01_gauge_wave.ipynb`, click **Select Kernel** (top right) and
  choose **Jupyter Kernel… → Python (pyNR)**. If that entry is missing, choose
  **Python Environments… → Python 3.12 (/usr/local/bin/python)**; it is the
  same interpreter.
- **JupyterLab in a separate browser tab.** In the terminal:
  ```bash
  jupyter lab --ip 0.0.0.0 --no-browser
  ```
  Codespaces forwards port 8888 and offers **Open in Browser**. Alternatively,
  click the `http://127.0.0.1:8888/lab?token=…` link printed in the terminal;
  Codespaces rewrites it to your private forwarded address. Then pick the
  **Python (pyNR)** kernel. Forwarded ports are private to your GitHub
  account unless you make them public.

(sec-output-location)=
### Where the output goes, and plotting it in Jupyter

Every run, from the terminal or a notebook, is written to one folder,
**`<repository>/simulations/<run name>/`**. The run name is the parameter-file
name unless `IO::out_dir` says otherwise:

| started from | command | output |
|---|---|---|
| terminal (any folder of the checkout) | `pynr run par/gauge_wave.par` | `simulations/gauge_wave/` |
| notebook in `notebooks/` | `Simulation.from_parfile("../par/gauge_wave.par").run()` | `simulations/gauge_wave/` |
| either, custom name | `IO::out_dir = "my_test"` or `--out my_test` | `simulations/my_test/` |

So you can run in the terminal (for long runs, use `nohup pynr run … &` or a
second terminal tab) and **only plot in the notebook**:

```python
from kuibit.simdir import SimDir
from pynr.paths import run_dir, list_runs

print(list_runs())                        # runs found under simulations/
sd = SimDir(run_dir("gauge_wave"))
alp = sd.ts.maximum["alp"]                # time series
psi4 = sd.gws[6.0][(2, 0)]                # Psi4 multipole (perturbed-BH run)
```

Each notebook starts with a **Settings** cell that controls this:

```python
OUTPUT_ROOT = paths.output_root()         # default: <repo>/simulations, same as `pynr run`
# OUTPUT_ROOT = os.path.expanduser("~/pynr_runs")   # or any folder
RUN_SIMULATIONS = True                    # False: only plot existing runs
os.environ["PYNR_OUTPUT_DIR"] = OUTPUT_ROOT
```

If you change `OUTPUT_ROOT` in a notebook, point the terminal at the same
folder with `pynr run par/gauge_wave.par --output-root ~/pynr_runs` (or
`export PYNR_OUTPUT_DIR=~/pynr_runs`). Outputs in `simulations/` are
git-ignored. In a Codespace they persist until the Codespace is deleted;
download them by right-clicking the folder in the file explorer.

### Free hours through GitHub Education

- **Students.** Verify at <https://education.github.com/pack>. The Student
  Developer Pack includes GitHub Pro, and Pro includes a monthly allowance of
  Codespaces core-hours and storage. A 4-core machine uses 4 core-hours per
  wall-clock hour.
- **Teachers.** Verify at <https://education.github.com/teachers>. Use
  **GitHub Classroom** to hand out pyNR-based assignments. Each student gets
  a private copy that opens directly in a Codespace.
- Choose a **4-core** machine type for the black-hole problems. The 1D
  tests (gauge wave, linear wave) run fine on 2 cores.
- **Stop** the Codespace when you are done, because idle time counts too.
  Codespaces stop automatically after 30 min idle by default.

:::{note}
Allowances and machine types change. Check the current numbers on
<https://docs.github.com/en/billing/managing-billing-for-github-codespaces/about-billing-for-github-codespaces>.
:::

## Binder

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/rahulkashyap-phy/pyNR/main?labpath=notebooks)

Binder is free and needs no account, but it is small (1–2 cores, ~2 GB RAM)
and sessions are deleted when idle. Notebooks work as described in
{ref}`sec-output-location`; runs go to `simulations/` inside the session. It is good for the 1D tests and small
black-hole grids ($\lesssim 64^3$).

## Your own machine or cluster

See [Installation](installation.md). pyNR runs on one node with shared-memory
threads (Numba). MPI domain decomposition is on the [roadmap](roadmap/index.md).
