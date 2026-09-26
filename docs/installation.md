# Installation

pyNR needs Python ≥ 3.10. It depends on NumPy, Numba, SciPy and h5py.
Visualisation uses kuibit and matplotlib.

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

With conda/mamba:

```bash
mamba create -n pynr python=3.12 numpy numba scipy h5py matplotlib jupyterlab
mamba activate pynr
pip install -e ".[viz,test]"
```

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
