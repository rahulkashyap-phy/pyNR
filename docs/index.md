# pyNR

**Numerical relativity in Python, organised like the Einstein Toolkit.**

*Rahul Kashyap, Indian Institute of Technology Bombay* · <rahulkashyap@iitb.ac.in>
· Apache-2.0, attribution required: [how to cite and credit](license.md)

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
- **Architecture you can see.** A curated model of the code is checked against the code on every build, and
  rendered as diagrams, an interactive explorer and per-problem workflows ([Architecture](architecture.md)).
- **PDF lecture notes** from the same sources: `make -C docs latexpdf`.
- **Runs in the browser.** GitHub Codespaces (free hours for verified
  students and teachers through GitHub Education) and Binder.

```{include} _generated/pdf_link.md
```

```{toctree}
:maxdepth: 2
:caption: Getting started

installation
license
running-online
problems/index
visualization
reproducing-figures
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
architecture
developer-guide
software-engineering
utilities
performance
devlog/index
docgraph
reference/index
```

```{toctree}
:maxdepth: 2
:caption: Roadmap

roadmap/index
```

```{toctree}
:maxdepth: 2
:caption: rkdev: personal workflow
:glob:

rkdev/index
```
