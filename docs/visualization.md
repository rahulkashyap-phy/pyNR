# Visualisation with kuibit

pyNR writes the same files as the Einstein Toolkit's Carpet I/O. Every kuibit
tool, including `SimDir` and the `kuibit` plotting scripts, works on a pyNR
output directory unchanged.

| pyNR output | ET equivalent | kuibit access |
|---|---|---|
| `alp.xyz.h5`, `alp.xy.h5`, ... | CarpetIOHDF5 | `sd.gf.xyz["alp"]`, `sd.gf.xy["alp"]` |
| `alp.maximum.asc`, `.minimum`, `.norm2` | CarpetIOScalar | `sd.ts.maximum["alp"]` |
| `mp_Psi4_l2_m2_r20.00.asc` | Multipole | `sd.gws[20.0][(2, 2)]`, `sd.multipoles["Psi4"]` |
| `parameters.par` | the `.par` in the output | — |

```python
from kuibit.simdir import SimDir
import kuibit.visualize_matplotlib as viz
import matplotlib.pyplot as plt

sd = SimDir("schwarzschild_perturbed")

# 2D slice of the metric at the last iteration
gxx = sd.gf.xy["gxx"]
it = gxx.available_iterations[-1]
viz.plot_color(gxx[it], x0=[-15, -15], x1=[15, 15], shape=[300, 300], colorbar=True)

# Hamiltonian-constraint violation versus time
H = sd.ts.norm2["H"]
plt.figure(); plt.semilogy(H.t, H.y)

# Psi4 (l, m) = (2, 0) at r = 15, and the strain
psi4 = sd.gws[15.0][(2, 0)]
plt.figure(); plt.plot(psi4.t, psi4.real())
h = sd.gws[15.0].get_strain_lm(2, 0, pcut=60)   # fixed-frequency integration
```

The kuibit command-line scripts (`plot_grid_var.py`, `plot_psi4_lm.py`,
`plot_constraints.py`, ...) accept `--datadir <pyNR out_dir>` as they would
for an ET simulation.

## The kuibit fork

Course-specific additions, such as pyNR metadata and convenience plots for
the problems in these notes, live on a branch of
[rahulkashyap-phy/kuibit](https://github.com/rahulkashyap-phy/kuibit). The
pyNR output format stays compatible with upstream kuibit, and the test suite
checks this (`tests/test_evolution.py::test_output_readable_by_kuibit`).
