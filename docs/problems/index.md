# Problem set

Each problem is a parameter file in `par/`. Run it with

```bash
pynr run par/<problem>.par [--set Thorn::param=value ...]
```

The output goes to `simulations/<problem>/`. Analyse it with kuibit (see [Visualisation](../visualization.md)).
Every problem page ends with its **workflow**, generated from the parameter file: which thorns run in which
schedule bin, what data flows between them, the settings, the output files, and how to analyse them.

```{table} The problem set.
:name: tab-problems

| # | problem | physics | workflow | cost (machine) |
|---|---|---|---|---|
| 1 | [Gauge wave](gauge_wave.md) | gauge dynamics in flat space; convergence | {numref}`fig-workflow-gauge-wave` | see {numref}`tab-problem-cost` |
| 2 | [Linear wave](linear_wave.md) | gravitational plane wave; $\Psi_4$ | {numref}`fig-workflow-linear-wave` | see {numref}`tab-problem-cost` |
| 3 | [Geodesic slicing of Schwarzschild](schwarzschild_geodesic.md) | why gauge matters | {numref}`fig-workflow-schwarzschild-geodesic` | see {numref}`tab-problem-cost` |
| 4 | [1+log slicing of a puncture](schwarzschild_1plog.md) | lapse collapse, slice stretching | {numref}`fig-workflow-schwarzschild-1plog` | see {numref}`tab-problem-cost` |
| 5 | [Kerr black hole in Kerr-Schild coordinates](kerr_schild.md) | stationarity, excision, constraint growth | {numref}`fig-workflow-kerr-schild` | see {numref}`tab-problem-cost` |
| 6 | [Perturbed black hole and GW extraction](perturbed_bh.md) | quasi-normal ringing, $\Psi_4$ multipoles | {numref}`fig-workflow-schwarzschild-perturbed` | see {numref}`tab-problem-cost` |
```

## Thorns and cost per problem

```{include} ../_generated/arch/problem_matrix.md
```

```{toctree}
:hidden:

gauge_wave
linear_wave
schwarzschild_geodesic
schwarzschild_1plog
kerr_schild
perturbed_bh
```
