(sec-developer-guide)=
# Developer guide: changing the code without breaking the architecture

The [architecture](architecture.md) diagrams, the per-problem workflows and the "Architecture" boxes in the API
pages are generated from `arch/model.yaml` and from the code. They stay correct only if the code is written so that
its structure can be extracted, and the model is updated in the same commit as the code. `python arch/check_drift.py`
checks every rule below. CI runs it on every push, and it fails with a message naming the rule, the file and the fix.

```bash
python arch/check_drift.py           # before every commit; also part of `pytest` (tests/test_arch.py)
python arch/render.py --readme       # after changing flows/components: refresh the README diagram
```

## The rules

```{table} Rules for code that keeps the architecture graph maintainable, and the check that enforces each.
:name: tab-dev-rules

| # | rule | enforced by |
|---|---|---|
| 1 | **Every module and every thorn belongs to a component.** A new module goes into an existing component's `src:` or into a new component entry (with `kind`, `layer`, `src`, `thorns`, `doc`, `equations`, `summary`). | `coverage` |
| 2 | **Calls go downwards (layers).** cli → driver → registry → thorns → backends → kernels / utils; thorns build on the flesh API. Kernels and utils take arrays and scalars only and never import `pynr.cactus` or thorns. | `layer` |
| 3 | **Write cross-component access literally**, so it can be extracted: plain `from pynr.x import y` (no `importlib`, `__import__` or computed module names); `sim.thorn("ADMBase")` with a literal name, never a variable; grid functions by literal full name `"Thorn::var"`, and groups declared in `setup()`. | `edge` (an unextractable access is invisible, so the model would drift) |
| 4 | **Inversion of control only through the documented hooks:** `Schedule.add` in `Thorn.schedule`; `MoL.register_evolved`; `MoL.add_rhs_hook`; `GridFunctions.register(update=...)`. No monkey-patching, and no storing another thorn's bound methods. | `edge` (registers) |
| 5 | **Record every edge on the component that initiates it, with the right type:** `uses` (I call it); `requires` (it must be active); `reads` (I read its state); `registers` (it calls me back). Never write the reverse direction; the docs derive "used by" and "called back by". | `edge` |
| 6 | **Data passed between thorns goes into `flows`**, with the grid-function names and the schedule `stage` (or `on demand`). | `flow` |
| 7 | **Equations and notes.** Label every displayed equation `$$ … $$ (eq-name)` and list it in the component's `equations:`. Renaming a label, file or section anchor updates `arch/model.yaml` in the same commit. | `pointer`; `docs` (uncited equations warn) |
| 8 | **Moving files.** Update `src:`, or state ownership in the file itself with `# @component: Name` in its first lines. | `pointer`, `coverage` |
| 9 | **Type-only imports go under `if TYPE_CHECKING:`.** They are not runtime dependencies and are ignored. | `edge` |
| 10 | **Every parameter file has a problem page** that includes its generated workflow (`{include} ../_generated/arch/workflow_<name>.md`). | `problem` |
| 11 | **Releases** snapshot the extracted graph into `arch/snapshots/vX.Y.Z.json`, so architecture changes between versions can be diffed. | release checklist |
```

## Worked example: adding a BSSN thorn

1. Write `pynr/thorns/bssn.py`. Import only the flesh API and the kernels:
   ```python
   from pynr.cactus import Param, Thorn, register_thorn
   from pynr.kernels.bssn import bssn_rhs            # new kernel component, layer: kernels
   ```
   In `setup()`, get ADMBase with a literal name, and register with MoL:
   ```python
   self.U = self.sim.thorn("ADMBase").U
   self.sim.thorn("MoL").register_evolved(self.name, self.W, self.rhs, self.post, rhs_final=self.rhs_final)
   ```
2. Running `python arch/check_drift.py` now fails, telling you what is missing:
   ```text
   FAIL [coverage] pynr/thorns/bssn.py: module belongs to no component
   FAIL [coverage] pynr/thorns/bssn.py: thorn `BSSN` is claimed by no component
   ```
3. Add the component to `arch/model.yaml`:
   ```yaml
   BSSN:
     kind: physics
     layer: thorns
     src: [pynr/thorns/bssn.py]
     thorns: [BSSN]
     doc: docs/theory/bssn.md
     equations: [eq-bssn-evolution]
     uses: [flesh, kernels.bssn]
     requires: [ADMBase, MoL]
     reads: [ADMBase, MoL]
     registers:
       - {into: MoL, via: register_evolved, stage: EVOL, functions: [rhs, post, rhs_final]}
   kernels.bssn:
     kind: kernel
     layer: kernels
     src: [pynr/kernels/bssn.py]
     uses: [kernels.fd, numba, numpy]
   ```
   Add flows too, e.g. `{from: ADMBase, to: BSSN, stage: POSTINITIAL, data: [ADMBase::metric, ADMBase::curv]}`.
4. Run the check again. It passes, and the new thorn appears in every view, in the explorer, in the API box of
   `pynr.thorns.bssn`, and in the workflow of any parameter file that activates it.

## Branches

All development happens on the `rkdev` branch. The public `main` branch is updated from it by its maintainer. Please
open contributions against `rkdev`.
