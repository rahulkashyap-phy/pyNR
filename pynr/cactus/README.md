# `pynr/cactus/` — the flesh

Thorn-independent core, mirroring the Cactus flesh.

| file | contents |
|---|---|
| `parfile.py` | reader for ET `.par` syntax (`ActiveThorns`, `Thorn::p[i]`, `$parfile`, comments, multi-line strings) |
| `params.py` | `Param` declarations (the `param.ccl` analogue) and the typed parameter store |
| `thorn.py` | `Thorn` base class and the `@register_thorn` registry |
| `schedule.py` | schedule bins (`STARTUP … TERMINATE`) with `before`/`after` ordering |
| `gridfunctions.py` | grid-function and group registry, with lazy `update` callbacks |
| `grid.py` | `UniformGrid`: extent, spacing, ghost/boundary points, coordinates |
| `simulation.py` | `Simulation`: activation → parameters → grid → setup → schedule → main loop |

## Try each piece on its own

```python
# parse a parameter file (no thorns needed)
from pynr.cactus.parfile import parse_parfile
print(parse_parfile("par/gauge_wave.par"))

# a grid
from pynr.cactus.grid import UniformGrid
g = UniformGrid((-1, -1, -1), (1, 1, 1), (0.1, 0.1, 0.1), nghost=3)
print(g, g.coords1d[0][:5])

# the schedule
from pynr.cactus.schedule import Schedule
S = Schedule(); S.add("INITIAL", lambda: print("hi"), name="Me::hi"); S.run("INITIAL")

# a minimal simulation (core thorns only, no evolution)
from pynr import Simulation
Simulation.from_string('ActiveThorns = "ADMBase IOBasic"', name="empty").run()
```

Tests: `pytest tests/test_framework.py`.
