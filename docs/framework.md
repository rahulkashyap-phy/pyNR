# The framework: an Einstein Toolkit in miniature

pyNR copies the architecture of Cactus and the Einstein Toolkit. If you know
the ET, you already know how pyNR is organised. If you don't, what you learn
here carries over directly.

## Flesh and thorns

| Cactus / ET | pyNR | where |
|---|---|---|
| flesh | `Simulation`, `Schedule`, `Parameters`, `GridFunctions` | `pynr/cactus/` |
| thorn | a `Thorn` subclass registered with `@register_thorn` | `pynr/thorns/` |
| `param.ccl` | `Thorn.parameters = {"name": Param(default, doc, keywords=...)}` | |
| `interface.ccl` | `Thorn.setup()` → `sim.gf.register(...)`, `register_group(...)` | |
| `schedule.ccl` | `Thorn.schedule(S)` → `S.add("INITIAL", self.fn, after=[...])` | |
| `cctkGH` | the `Simulation` object: `sim.grid`, `sim.time`, `sim.iteration`, `sim.dt` | |
| PUGH / Carpet | `UniformGrid` (uniform, single node) | `pynr/cactus/grid.py` |
| MoL | `MoL` thorn + `pynr.utils.integrators` | |
| `.par` files | same syntax, incl. `ActiveThorns`, `Thorn::p[i]`, `$parfile` | |

### Lifecycle

```text
activate thorns (+ requirements) → declare parameters → read parfile
→ build grid → setup() every thorn → schedule() every thorn
→ STARTUP, BASEGRID, INITIAL, POSTINITIAL, ANALYSIS, OUTPUT      (iteration 0)
→ loop { PRESTEP, EVOL, POSTSTEP, ANALYSIS, OUTPUT }
→ TERMINATE
```

`pynr run file.par` prints the resolved schedule at start-up, and
`<out_dir>/parameters.par` records every parameter value used.

## Writing a thorn

A complete example that outputs $\sqrt{\gamma}$ for each run:

```python
import numpy as np
from pynr.cactus import Param, Thorn, register_thorn

@register_thorn
class SqrtDet(Thorn):
    name = "SqrtDet"
    requires = ("ADMBase",)
    parameters = {"enabled": Param(True, "Compute sqrt(det gamma)")}

    def setup(self):                       # interface.ccl
        self.out = self.sim.grid.empty()
        self.sim.gf.register(self.name, "sqrtdet", self.out, update=self.compute)

    def compute(self):                     # called on demand by output thorns
        U = self.sim.thorn("ADMBase").U
        gxx, gxy, gxz, gyy, gyz, gzz = U[0:6]
        det = (gxx*(gyy*gzz - gyz**2) - gxy*(gxy*gzz - gyz*gxz)
               + gxz*(gxy*gyz - gyy*gxz))
        self.out[...] = np.sqrt(det)
```

After importing the module, `ActiveThorns = "... SqrtDet"` and
`IOScalar::outScalar_vars = "SqrtDet::sqrtdet"` work like any other thorn.
If the loop matters for performance, move it into a Numba kernel in
`pynr/kernels/` and call that kernel from the thorn.

## Swapping components

Components talk only through grid functions, parameters and a few services,
so each one can be replaced on its own:

| what | how to swap |
|---|---|
| initial data | a new thorn that fills `ADMBase` in `INITIAL` (e.g. a future `TwoPunctures`) |
| formulation | a new evolution thorn registering with `MoL` (e.g. `BSSN`, `Z4c`) |
| time integrator | `MoL::ODE_Method`, or add a function to `pynr.utils.integrators.METHODS` |
| kernel implementation | `Driver::backend` (`numba`, `numpy`), register more in `pynr.backends` |
| interpolation, quadrature | functions in `pynr.utils` (e.g. SciPy's `RegularGridInterpolator`) |
| output format | an I/O thorn (HDF5 Carpet format today; openPMD/ADIOS2 possible) |
