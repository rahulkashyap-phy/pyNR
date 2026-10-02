# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
"""Where simulation output goes, so the shell and Jupyter see the same runs.

A relative ``IO::out_dir`` (the default is the parameter-file name) is
resolved against one *output root*, not against the current directory:

1. ``$PYNR_OUTPUT_DIR``, if set;
2. otherwise ``<checkout>/simulations`` when the parameter file (or, for
   runs built from a string, the current directory) lies inside a pyNR
   source checkout;
3. otherwise the current directory, as in the Einstein Toolkit.

So ``pynr run par/gauge_wave.par`` from the repository root, and
``Simulation.from_parfile("../par/gauge_wave.par")`` from ``notebooks/``,
both write ``<checkout>/simulations/gauge_wave``. A notebook finds a run with
:func:`run_dir`. Absolute ``IO::out_dir`` values are used as given.
"""

from __future__ import annotations

import os


def find_checkout(start: str | os.PathLike | None = None) -> str | None:
    """Closest ancestor of ``start`` that is a pyNR source checkout, or ``None``."""
    d = os.path.abspath(start or os.getcwd())
    if os.path.isfile(d):
        d = os.path.dirname(d)
    while True:
        if os.path.isfile(os.path.join(d, "pyproject.toml")) and os.path.isfile(
                os.path.join(d, "pynr", "__init__.py")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def output_root(near: str | os.PathLike | None = None) -> str:
    """The directory that relative ``IO::out_dir`` values are resolved against."""
    env = os.environ.get("PYNR_OUTPUT_DIR")
    if env:
        return os.path.abspath(os.path.expanduser(env))
    checkout = find_checkout(near)
    if checkout:
        return os.path.join(checkout, "simulations")
    return os.getcwd()


def resolve_out_dir(out_dir: str, near: str | os.PathLike | None = None) -> str:
    """Absolute output directory for an ``IO::out_dir`` value."""
    out_dir = os.path.expanduser(out_dir)
    if os.path.isabs(out_dir):
        return out_dir
    return os.path.join(output_root(near), out_dir)


def run_dir(name: str, near: str | os.PathLike | None = None) -> str:
    """Path of the run called ``name`` (e.g. ``"gauge_wave"``), for kuibit's ``SimDir``.

    Example (in a notebook)::

        from kuibit.simdir import SimDir
        from pynr.paths import run_dir
        sd = SimDir(run_dir("gauge_wave"))
    """
    return resolve_out_dir(name, near)


def list_runs(near: str | os.PathLike | None = None) -> list[str]:
    """Names of the runs (folders with a ``pynr.log``) under the output root."""
    root = output_root(near)
    if not os.path.isdir(root):
        return []
    return sorted(d for d in os.listdir(root)
                  if os.path.isfile(os.path.join(root, d, "pynr.log")))


def display_path(path: str | os.PathLike) -> str:
    """Path for logs and docs without local user details.

    Relative to the pyNR checkout if inside it, else relative to the home
    directory as ``~/...``, else unchanged. Keeps ``pynr.log`` files free of
    ``/Users/<name>`` when they are published as documentation data.
    """
    p = os.path.abspath(path)
    checkout = find_checkout(p)
    if checkout and (p == checkout or p.startswith(checkout + os.sep)):
        return os.path.relpath(p, checkout)
    home = os.path.expanduser("~")
    if p.startswith(home + os.sep):
        return "~" + p[len(home):]
    return p
