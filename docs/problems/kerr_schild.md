# 5. Kerr black hole in Kerr-Schild coordinates

**File:** `par/kerr_schild.par`

## Physics

The Kerr metric in Kerr-Schild form, $g_{\mu\nu} = \eta_{\mu\nu} + 2H l_\mu l_\nu$
(Eq. {eq}`eq-kerr-schild`),
with mass $M = 1$ and spin $\chi = a/M = 0.6$ (horizon at $r_+ = M(1+\sqrt{1-\chi^2}) = 1.8M$) (see the `Exact` thorn for all
formulae). These coordinates cross the horizon smoothly, so the interior
can be *excised*. With the exact lapse and shift the data are stationary:
$\partial_t\gamma_{ij} = \partial_t K_{ij} = 0$ in the continuum.

## Expected results

- At $t = 0$ the numerical $\partial_t\gamma_{ij}$, $\partial_t K_{ij}$ and the
  constraints are pure truncation error. They converge to zero at 4th order
  (`tests/test_kernels.py::test_kerr_schild_is_stationary_4th_order`,
  `test_constraints_vanish_for_kerr`).
- During the evolution $\|H\|_2$ is roughly constant at first. Then the
  plain ADM system's constraint-violating mode, seeded near the excision
  boundary, grows and the run fails. For Schwarzschild ($\chi = 0$),
  {numref}`tab-ks-lifetime` shows the measured failure times:

  ```{table} Failure time of Schwarzschild (Kerr-Schild, static gauge) runs versus resolution, excision radius and dissipation.
  :name: tab-ks-lifetime

  | $\Delta x$ | excision radius | $\epsilon$ (KO) | fails at |
  |---|---|---|---|
  | 0.5 | 1.2 M | 0.2 | $t \approx 7M$ |
  | 0.5 | 1.6 M | 0.2 | $t \approx 26M$ |
  | 0.5 | 1.8 M | 0.3 | $t \approx 19M$ |
  | 0.25 | 1.6 M | 0.2 | $t \approx 29M$ |
  | 0.25 | 1.8 M | 0.3 | stable to $t \ge 40M$ |
  ```

  {numref}`fig-kerr-constraints` shows the spinning case as shipped
  ($\chi = 0.6$, excision radius $\approx 0.9\,r_+$; full settings in
  {numref}`tab-settings-kerr-constraints`). $\max|H|$ starts at the
  truncation-error level, stays roughly flat for about $10M$, then grows
  exponentially until the run aborts at $t \approx 24M$.

  Resolving the region between the excision boundary and the horizon
  matters, and so does dissipation. The lifetime does not grow without
  bound with resolution, because the instability is a property of the
  continuum ADM system.

```{include} ../figures/kerr_constraints.md
```

```{include} ../_generated/arch/workflow_kerr_schild.md
```

## Exercises

1. Reproduce the table (use `--set`, e.g.
   `pynr run par/kerr_schild.par --set ADMEvolve::excision_radius=1.6`).
2. Plot $\gamma_{xx}$ in the $xz$ plane. Where does the error first appear?
3. Why must the excision region lie inside the horizon? (Hint: in which
   direction do the characteristic speeds point there?)
