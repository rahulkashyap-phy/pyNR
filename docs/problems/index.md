# Problem set

Each problem is a parameter file in `par/`. Run it with

```bash
pynr run par/<problem>.par [--set Thorn::param=value ...]
```

The output goes to `./<problem>/`. Analyse it with kuibit (see [Visualisation](../visualization.md)).

```{table} The problem set.
:name: tab-problems

| # | problem | physics | cost |
|---|---|---|---|
| 1 | [Gauge wave](gauge_wave.md) | gauge dynamics in flat space; convergence | seconds |
| 2 | [Linear wave](linear_wave.md) | gravitational plane wave; $\Psi_4$ | seconds |
| 3 | [Geodesic slicing of Schwarzschild](schwarzschild_geodesic.md) | why gauge matters | < 1 min |
| 4 | [1+log slicing of a puncture](schwarzschild_1plog.md) | lapse collapse, slice stretching | minutes |
| 5 | [Kerr black hole in Kerr-Schild coordinates](kerr_schild.md) | stationarity, excision, constraint growth | minutes |
| 6 | [Perturbed black hole and GW extraction](perturbed_bh.md) | quasi-normal ringing, $\Psi_4$ multipoles | ~30 min |
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
