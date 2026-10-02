# 4. 1+log slicing of a Schwarzschild puncture

**File:** `par/schwarzschild_1plog.par`

## Physics

The same initial slice as problem 3, now with the singularity-avoiding
Bona-Massó "1+log" slicing

$$ \partial_t\alpha = -2\alpha K, $$ (eq-1plog-slicing)

a pre-collapsed initial lapse $\alpha = \psi^{-2}$ and zero shift. Where the
slice would focus ($K > 0$) the lapse collapses, so proper time stops
advancing there and the slice never reaches the singularity.

## Expected physics

- **Collapse of the lapse:** $\min\alpha$ (at the puncture) drops towards
  zero within a few $M$. The slice stops advancing inside the horizon.
- **Slice stretching:** with zero shift, $\gamma_{xx}$ develops a growing peak near
  the horizon. Moving-puncture gauges (the Gamma-driver shift) and BSSN/Z4c
  cure this.

## What pyNR v0.1 shows (measured, $\Delta x = 0.2$)

```{table} Lapse extrema in the 1+log puncture run ($\Delta x = 0.2$).
:name: tab-1plog-lapse

| $t/M$ | $\min\alpha$ | $\max\alpha$ |
|---|---|---|
| 0 | 0.066 | 0.945 |
| 1 | 0.023 | 1.20 |
| 2 | −0.13 | 1.06 |
| 4 | −0.08 | 2.11 |
| ≈4.5 | run aborts (NaN) | |
```

The lapse does start to collapse. Near the puncture it then overshoots to
*negative* values, $\max\alpha$ rises above 1 (unphysical), and the run fails
at $t \approx 4.5M$. Excising $r < 0.3M$ does not help (failure at
$t \approx 3.5M$). The cause is the same **puncture problem** as in
[problem 3](schwarzschild_geodesic.md): the ADM variables are singular at
$r = 0$ and cannot be finite-differenced there. The pre-collapsed lapse only
delays the failure. Slice stretching never gets a chance to appear.

This problem becomes the acceptance test for the BSSN + moving-puncture
milestone. There the same parfile (with `evolution_method = "BSSN"` and a
Gamma-driver shift) should run for hundreds of $M$, with $\min\alpha \to 0.3$
at the puncture.

```{include} ../_generated/arch/workflow_schwarzschild_1plog.md
```

## Exercises

1. Plot `alp.minimum.asc` and `alp.maximum.asc`. Where is $\alpha$ largest
   when it exceeds 1 (use the 2D output)? How does the failure time depend on $\Delta x$?
2. Use `lapse_evolution_method = "harmonic"` instead. Harmonic slicing is
   only marginally singularity-avoiding — what changes?
