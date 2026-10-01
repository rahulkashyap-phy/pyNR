# `par/` — example parameter files (the problem set)

Each file runs on its own:

```bash
pynr run par/<file>.par                         # output in ./<file>/
pynr run par/<file>.par --set CoordBase::dx=0.1 --out mydir
```

| file | problem | run time (12 cores) | expected result (measured, see header) |
|---|---|---|---|
| `gauge_wave.par` | AwA gauge wave, harmonic slicing | ~10 s | α stays within [√0.9, √1.1]; 4th-order convergence |
| `linear_wave.par` | AwA linear plane GW | ~10 s | amplitude constant; Ψ₄ = ḧ₊ − iḧ× |
| `schwarzschild_geodesic.par` | geodesic slicing, isotropic puncture | < 1 min | fails at t≈0.7 M (puncture problem; physical πM) |
| `schwarzschild_1plog.par` | 1+log slicing, pre-collapsed lapse | ~1 min | lapse collapses, then fails at t≈4.5 M |
| `kerr_schild.par` | Kerr χ=0.6, excision, static gauge | ~1 min | stationary until the ADM mode grows; fails at t≈24 M |
| `schwarzschild_perturbed.par` | ℓ=2 perturbation + Ψ₄ extraction | ~15 min | burst at r=6 at t≈8–10 M; ringdown hidden by the ADM mode |

The header of each file describes the physics and the measured outcome.
Full write-ups: `docs/problems/`. Analyse the output with kuibit:
`SimDir("<file>")`. Parameter reference: `python -m pynr thorns --markdown`.
