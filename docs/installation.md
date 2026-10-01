# Installation

pyNR needs Python ≥ 3.10. It depends on NumPy, Numba, SciPy and h5py.
Visualisation uses kuibit and matplotlib.

*pyNR is written by Rahul Kashyap (Indian Institute of Technology Bombay,
<rahulkashyap@iitb.ac.in>) and licensed under Apache-2.0 with required
attribution. See [License, attribution and citation](license.md).*

## From PyPI

```bash
python -m venv .venv && source .venv/bin/activate
pip install "pynr[viz]"          # add ,notebook for JupyterLab
pynr thorns                       # list the available thorns
```

## From source (recommended for the course)

```bash
git clone https://github.com/rahulkashyap-phy/pyNR.git
cd pyNR
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"           # viz + notebook + docs + test tools
pytest                            # ~20 s the first time (Numba compiles), ~2 s after
```

With conda/mamba instead of a venv:

```bash
mamba create -n pynr python=3.12 numpy numba scipy h5py matplotlib jupyterlab
mamba activate pynr
pip install -e ".[viz,test]"
python -m ipykernel install --user --name pynr --display-name "Python (pyNR conda)"
```

## Using the virtual environment

A virtual environment (`.venv`) is a private Python installation for pyNR.
*Activate* it in every new terminal before using pyNR:

```bash
source .venv/bin/activate        # prompt shows (.venv); `which python` points into .venv
pynr thorns                      # works only while the venv is active
deactivate                       # leave it
```

Without activating, call its programs by path, e.g. `.venv/bin/pynr run …`
or `.venv/bin/python script.py`.

## Jupyter notebooks

The notebook kernel needs `ipykernel` inside the environment. Register the
environment once as a named kernel:

```bash
source .venv/bin/activate
pip install ipykernel ipywidgets        # included in pip install -e ".[notebook]"
python -m ipykernel install --user --name pynr --display-name "Python (pyNR .venv)"
```

- **VS Code:** open a notebook (e.g. `notebooks/01_gauge_wave.ipynb`), click
  **Select Kernel** (top right) and choose **Jupyter Kernel… → Python (pyNR .venv)**
  or **Python Environments… → .venv**. You don't need to activate anything in
  a terminal. VS Code runs the notebook in its own folder, so the relative
  paths (`../par/...`) work.
- **JupyterLab in the browser:**
  ```bash
  source .venv/bin/activate
  pip install jupyterlab                # once
  cd notebooks && jupyter lab
  ```
  then pick the *Python (pyNR .venv)* kernel.
- **Any other Jupyter installation** on the machine also lists the
  *Python (pyNR .venv)* kernel after the `ipykernel install` step.

## Running

```bash
pynr run par/gauge_wave.par                               # output goes to ./gauge_wave/
pynr run par/gauge_wave.par --set CoordBase::dx=0.01      # override a parameter
pynr run par/kerr_schild.par --backend numpy              # use the NumPy reference kernels
```

From Python or a notebook:

```python
from pynr import Simulation
sim = Simulation.from_parfile("par/gauge_wave.par",
                              overrides={"Cactus::cctk_final_time": 2.0})
sim.run()
U = sim.thorn("ADMBase").U          # the ADM state, shape (16, nx, ny, nz)
```

## Threads and the Numba cache

- Numba uses every core by default. Set `NUMBA_NUM_THREADS=4` to use fewer.
- The first run compiles the kernels (~10–20 s) and caches them in
  `__pycache__`. Later runs start at once.
- On a shared cluster, set `NUMBA_CACHE_DIR` to a writable directory.

## The kuibit fork

pyNR output is readable by upstream kuibit (`pip install kuibit`). Course
extensions live on a branch of the fork
[rahulkashyap-phy/kuibit](https://github.com/rahulkashyap-phy/kuibit):

```bash
pip install "git+https://github.com/rahulkashyap-phy/kuibit.git@<branch>"
```
