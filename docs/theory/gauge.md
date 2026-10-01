# Gauge: lapse and shift

```{eval-rst}
.. automodule:: pynr.thorns.admevolve
   :no-members:
```

## Exercises

1. Run `par/schwarzschild_geodesic.par` and find the time of the crash.
   Compare it with $\pi M$, the proper time for free fall from rest at
   the throat to the singularity.
2. Run `par/schwarzschild_1plog.par` and plot `alp.minimum.asc`. Explain the
   "collapse of the lapse". Then plot `gxx.maximum.asc`: this growth is *slice
   stretching*.
3. Evolve the gauge wave with `lapse_evolution_method = "1+log"` instead of
   `"harmonic"`. Why is the solution no longer the exact one?
