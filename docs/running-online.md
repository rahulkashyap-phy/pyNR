# Running online (Codespaces, Binder)

## GitHub Codespaces (recommended)

A Codespace is a cloud VM with VS Code and JupyterLab. The repository ships
a `.devcontainer/` that installs pyNR, kuibit and JupyterLab, then warms the
Numba cache so the first run is fast.

1. Open the repository on GitHub and choose **Code → Codespaces → Create codespace on main**.
2. Wait about 3 minutes for the first build. Later starts take seconds.
3. In the terminal, run `pynr run par/gauge_wave.par`. You can also open
   `notebooks/01_gauge_wave.ipynb` in VS Code, or run `jupyter lab` (port
   8888 is forwarded).

### Free hours through GitHub Education

- **Students.** Verify at <https://education.github.com/pack>. The Student
  Developer Pack includes GitHub Pro, and Pro includes a monthly allowance of
  Codespaces core-hours and storage. A 4-core machine uses 4 core-hours per
  wall-clock hour.
- **Teachers.** Verify at <https://education.github.com/teachers>. Use
  **GitHub Classroom** to hand out pyNR-based assignments. Each student gets
  a private copy that opens directly in a Codespace.
- Choose a **4-core** machine type for the black-hole problems. The 1D
  tests (gauge wave, linear wave) run fine on 2 cores.
- **Stop** the Codespace when you are done, because idle time counts too.
  Codespaces stop automatically after 30 min idle by default.

:::{note}
Allowances and machine types change. Check the current numbers on
<https://docs.github.com/en/billing/managing-billing-for-github-codespaces/about-billing-for-github-codespaces>.
:::

## Binder

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/rahulkashyap-phy/pyNR/main?labpath=notebooks)

Binder is free and needs no account, but it is small (1–2 cores, ~2 GB RAM)
and sessions are deleted when idle. It is good for the 1D tests and small
black-hole grids ($\lesssim 64^3$).

## Your own machine or cluster

See [Installation](installation.md). pyNR runs on one node with shared-memory
threads (Numba). MPI domain decomposition is on the [roadmap](roadmap.md).
