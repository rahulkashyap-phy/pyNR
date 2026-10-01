# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
"""Grid-function registry (variables and groups declared in ``interface.ccl``).

Grid functions are plain NumPy arrays. A thorn registers each variable with
its full name ``Thorn::var`` and may bundle variables into groups
(``ADMBase::metric``). Several variables are often *views* into one
contiguous block (e.g. all ADM variables live in a single ``(16, nx, ny, nz)``
array) so that Numba kernels get one array with good memory locality.

A variable can be registered with an ``update`` callback. Output thorns call
:meth:`GridFunctions.get` with ``fresh=True``; the callback then computes the
variable on demand (at most once per iteration). This is how ``WeylScal4``
computes ``Psi4`` only when something actually needs it.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np


class GridFunctions:
    def __init__(self, sim):
        self._sim = sim
        self._vars: dict[str, tuple[str, np.ndarray, Callable | None]] = {}
        self._groups: dict[str, list[str]] = {}
        self._updated_at: dict[Callable, int] = {}

    def register(self, thorn: str, name: str, array: np.ndarray, update: Callable | None = None):
        full = f"{thorn}::{name}"
        self._vars[full.lower()] = (full, array, update)
        return array

    def register_group(self, thorn: str, group: str, names: list[str]):
        self._groups[f"{thorn}::{group}".lower()] = [f"{thorn}::{n}".lower() for n in names]

    def expand(self, spec: str) -> list[str]:
        """Expand a space-separated list of variables/groups to full variable names."""
        out = []
        for tok in spec.split():
            key = tok.lower()
            if key in self._groups:
                out += [self._vars[v][0] for v in self._groups[key]]
            elif key in self._vars:
                out.append(self._vars[key][0])
            else:
                raise KeyError(f"Unknown grid function or group '{tok}'")
        return out

    def get(self, name: str, fresh: bool = False) -> np.ndarray:
        full, arr, update = self._vars[name.lower()]
        if fresh and update is not None:
            it = self._sim.iteration
            if self._updated_at.get(update) != it:
                update()
                self._updated_at[update] = it
        return arr

    def full_name(self, name: str) -> str:
        return self._vars[name.lower()][0]

    def __contains__(self, name: str) -> bool:
        return name.lower() in self._vars

    def names(self) -> list[str]:
        return [v[0] for v in self._vars.values()]
