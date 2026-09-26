# `tests/` — test suite

```bash
pip install -e ".[test,viz]"     # from the repository root
pytest                           # all (~20 s the first time while Numba compiles, then ~2 s)
pytest tests/test_kernels.py     # kernels only
pytest -k kuibit                 # output-format compatibility only
```

| file | checks |
|---|---|
| `test_framework.py` | parfile parsing, parameter validation, schedule ordering |
| `test_kernels.py` | 4th-order convergence of the ADM RHS and constraints (Schwarzschild, Kerr), Numba ≡ NumPy, Ψ₄ of a linear wave, SWSH orthonormality, interpolation |
| `test_evolution.py` | gauge-wave convergence, NumPy backend, kuibit reads the output, blow-up abort |
| `conftest.py` | helpers: pack exact solutions into ADM state arrays; temporary output directories |
