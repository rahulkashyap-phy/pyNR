# pyNR

**Numerical relativity in Python, organised like the Einstein Toolkit.**

pyNR is a teaching and prototyping code. It solves Einstein's equations in 3+1
form on a uniform 3D grid, with the lecture notes written into the code
documentation. You read the equations on these pages and the lines that
implement them sit right next to each other.

- **Einstein Toolkit structure.** Parameter files use the ET `.par` syntax.
  Physics lives in *thorns* (`ADMBase`, `Exact`, `MoL`, `WeylScal4`,
  `Multipole`, ...) that plug into schedule bins, so a thorn can be replaced
  without touching the others.
- **Fast Python.** The grid-point loops are Numba kernels (`parallel`,
  `fastmath`, cached), and a readable NumPy reference implementation
  cross-checks them.
- **ET-compatible output.** HDF5 grid functions, scalar reductions and
  $\Psi_4$ multipoles are written in Carpet formats, so
  [kuibit](https://sbozzolo.github.io/kuibit) reads a pyNR run as it reads an
  ET run.
- **Runs in the browser.** GitHub Codespaces (free hours for verified
  students and teachers through GitHub Education) and Binder.

```{toctree}
:maxdepth: 2
:caption: Getting started

installation
running-online
problems/index
visualization
```

```{toctree}
:maxdepth: 2
:caption: Lecture notes

theory/index
notes/index
```

```{toctree}
:maxdepth: 2
:caption: The code

framework
utilities
performance
roadmap
devlog/index
reference/index
```
