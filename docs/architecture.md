(sec-architecture)=
# Architecture

pyNR's structure is described twice, in plain text:

- **The curated model**, `arch/model.yaml`, written by hand. It records the meaning: components, what each one is
  for, which equations it implements, which documentation and notes explain it, the typed edges between components,
  and the data that flows between thorns at each schedule bin.
- **The extracted graph**, generated from the code at every build by `arch/extract.py`. It records what the code
  actually does: imports, `Thorn.requires`, runtime accesses (`sim.thorn("X")`), callback registrations, and the
  schedule, grid functions and output files of every parameter file.

`arch/check_drift.py` compares the two, and CI fails when they disagree (§ {ref}`sec-arch-health`). Every diagram on
this page, in the API pages and in the problem workflows is rendered from the model, so code, documentation and
lecture notes change together. The rules for changing the code are in the [developer guide](developer-guide.md).

## Edge types

Each edge is written on the component that **initiates** it, and always points from that component:

```{table} Edge types of the architecture model.
:name: tab-edge-types

| field on component A | meaning | arrow in the diagrams |
|---|---|---|
| `uses: [B]` | A imports B and **calls B's functions** (A is the caller) | grey solid, A → B |
| `requires: [B]` | thorn B must be active whenever A is | dotted, A → B |
| `reads: [B]` | A reads B's state at runtime without importing it (`sim.thorn("B")`) | blue dashed, A → B |
| `registers: [{into: B, …}]` | A hands functions to B, and **B calls them later** (inversion of control) | orange dashed, **B → A**, labelled "calls f" |
| `flows` (separate list) | data passed from A to B in a schedule bin (grid functions) | thick, coloured by bin |
```

"Used by" and "called back by" are derived from these edges. Nobody writes them by hand.

## Views

```{include} _generated/arch/view_physics.md
```

```{include} _generated/arch/view_runtime.md
```

```{include} _generated/arch/view_code.md
```

```{include} _generated/arch/view_full.md
```

**Legend.** Boxes are components, coloured by kind; clusters are layers. Arrows:
- **grey solid** — *uses*: the tail imports and calls the head;
- **dotted** — *requires*: the head must be active;
- **blue dashed** — *reads*: the tail reads the head's state;
- **orange dashed** — *callback*: the tail calls functions that the head registered;
- **thick coloured** — *data flow*, coloured by schedule bin: INITIAL blue, POSTINITIAL teal, EVOL red, POSTSTEP
  purple, ANALYSIS green, OUTPUT yellow, on-demand grey.

In the HTML version, click a box to open its documentation.

## Interactive explorer

:::{only} html
<iframe src="_static/arch/explorer.html" style="width:100%; height:720px; border:1px solid #e5e7eb; border-radius:6px"></iframe>

[Open the explorer full screen](_static/arch/explorer.html). It lets you filter by kind, toggle edge types, search,
and click a component to see its source, docs, notes and equations.
:::

:::{only} latex
The interactive explorer (Cytoscape.js) is part of the HTML documentation, at `_static/arch/explorer.html`.
:::

## Components

```{include} _generated/arch/components.md
```

## Layers

Code may only call "downwards". A component in one layer may `use` only the layers listed for it (and external
libraries). The drift check enforces this.

```{table} Allowed uses between layers.
:name: tab-layers

| layer | may use |
|---|---|
| cli | driver, registry, flesh |
| driver | driver, registry, flesh |
| registry | thorns |
| thorns | flesh, backends, kernels, utils |
| backends | kernels |
| kernels | kernels |
| utils | utils |
| flesh | flesh |
```

Thorns never import each other. They cooperate through `requires`, `reads`, registered callbacks and grid functions,
as in the Einstein Toolkit.

(sec-arch-health)=
## Architecture health

The result of `arch/check_drift.py` at the time these docs were built:

```{include} _generated/arch/drift_report.md
```
