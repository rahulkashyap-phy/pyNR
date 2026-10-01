# `pynr/` — the Python package

| folder | role (ET analogue) | README |
|---|---|---|
| [`cactus/`](cactus/) | the flesh: parfile, parameters, schedule, grid, main loop | [cactus/README.md](cactus/README.md) |
| [`thorns/`](thorns/) | physics, analysis and I/O modules (thorns) | [thorns/README.md](thorns/README.md) |
| [`kernels/`](kernels/) | Numba compute kernels + NumPy reference | [kernels/README.md](kernels/README.md) |
| [`utils/`](utils/) | generic numerical methods | [utils/README.md](utils/README.md) |
| `backends.py` | picks kernel implementation (`Driver::backend`) | — |
| `__main__.py` | CLI: `pynr run`, `pynr thorns` | — |
| `paths.py` | output root shared by the CLI and notebooks (`run_dir`, `list_runs`) | — |

## Install and check

```bash
pip install -e ".[viz,test]"      # from the repository root
python -m pynr thorns             # lists thorns -> package imports fine
python -m pynr run par/gauge_wave.par   # -> simulations/gauge_wave (see paths.py)
```

## Use from Python

```python
from pynr import Simulation
sim = Simulation.from_parfile("par/gauge_wave.par",
                              overrides={"Cactus::cctk_final_time": 1.0})
sim.run()
U = sim.thorn("ADMBase").U     # ADM state, shape (16, nx, ny, nz)
```

Dependency direction: `thorns → kernels, utils → numpy/numba`. `cactus`
knows nothing about physics, and `kernels`/`utils` know nothing about
thorns or parameters, so they can be imported and used on their own.
