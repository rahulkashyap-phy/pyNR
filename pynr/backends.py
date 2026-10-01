# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
"""Kernel backends: pick the implementation of each compute kernel by name.

``Driver::backend`` selects one of:

* ``"numba"`` (default) — fused, multithreaded loops compiled to machine code;
* ``"numpy"`` — vectorised reference implementation, readable and
  array-API style (a starting point for CuPy/JAX GPU backends).

Thorns ask for kernels via :func:`get_kernel` instead of importing them, so
adding a backend means registering functions here — no thorn changes.
"""

from __future__ import annotations

from collections.abc import Callable

_REGISTRY: dict[str, dict[str, Callable]] = {}


def register(backend: str, name: str, func: Callable) -> None:
    _REGISTRY.setdefault(backend, {})[name] = func


def get_kernel(name: str, backend: str = "numba") -> Callable:
    """Return kernel ``name`` for ``backend``, falling back to Numba if missing."""
    _load()
    impl = _REGISTRY.get(backend, {}).get(name)
    if impl is None:
        impl = _REGISTRY["numba"][name]
    return impl


def available() -> list[str]:
    _load()
    return sorted(_REGISTRY)


_loaded = False


def _load() -> None:
    global _loaded
    if _loaded:
        return
    from pynr.kernels import adm, adm_numpy

    register("numba", "adm_rhs", adm.adm_rhs)
    register("numba", "adm_constraints", adm.adm_constraints)
    register("numba", "weyl_psi4", adm.weyl_psi4)
    register("numpy", "adm_rhs", adm_numpy.adm_rhs)
    _loaded = True
