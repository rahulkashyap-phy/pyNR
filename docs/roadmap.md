# Roadmap

Capabilities are added one at a time. Each step must pass convergence tests
before the next one starts.

**v0.1 (this release)**

- [x] Flesh: parfiles, parameters, schedule, grid functions
- [x] Uniform 3D grid; static, radiative, flat and periodic boundaries
- [x] ADM evolution; static, harmonic and 1+log slicing; static shift
- [x] Exact data: gauge wave, linear wave, Schwarzschild (isotropic), Kerr (Kerr-Schild)
- [x] Gaussian $(\ell,m)$ metric perturbation
- [x] $\Psi_4$ and multipoles on geodesic spheres
- [x] Carpet-format output read by kuibit
- [x] Codespaces/Binder, Sphinx docs, PyPI packaging

**Next**

1. **Performance.** Vectorise the ADM kernel along rows of `k` (SIMD). The
   target is ≤ 200 ns/point/core (see [Performance](performance.md)).
2. **BSSN** (then **Z4c**), strongly hyperbolic, with the Gamma-driver shift:
   moving punctures, and long stable black-hole evolutions.
3. **Apparent-horizon finder** (fast-flow or spectral), with mass and spin.
4. **Elliptic solver** (PyAMG multigrid): Brill waves, Bowen-York /
   TwoPunctures-style binary initial data, constraint-satisfying perturbations.
5. **Mesh refinement** (fixed nested boxes first, Berger-Oliger time stepping).
6. **GPU backend** (CuPy or JAX) using the NumPy reference kernels as the template.
7. **MPI** domain decomposition with `mpi4py`.
8. Matter: hydro thorn (Valencia formulation, HLLE and reconstruction) — TOV star.
