# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
"""Schedule bins (the ``schedule.ccl`` analogue).

The main loop visits bins in this order (``CCTK_`` prefixes are accepted)::

    STARTUP  BASEGRID  INITIAL  POSTINITIAL  ANALYSIS  OUTPUT      (iteration 0)
    loop:   PRESTEP  EVOL  POSTSTEP  ANALYSIS  OUTPUT
    TERMINATE

Within a bin, routines run in the order they were added unless ``before`` /
``after`` constraints say otherwise (names are ``"Thorn::routine"``).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

BINS = (
    "STARTUP",
    "BASEGRID",
    "INITIAL",
    "POSTINITIAL",
    "PRESTEP",
    "EVOL",
    "POSTSTEP",
    "ANALYSIS",
    "OUTPUT",
    "TERMINATE",
)


@dataclass
class ScheduleItem:
    name: str
    func: Callable[[], None]
    before: list[str] = field(default_factory=list)
    after: list[str] = field(default_factory=list)


class Schedule:
    def __init__(self):
        self._bins: dict[str, list[ScheduleItem]] = {b: [] for b in BINS}
        self._sorted: dict[str, list[ScheduleItem]] = {}

    @staticmethod
    def _bin(name: str) -> str:
        b = name.upper().removeprefix("CCTK_")
        if b not in BINS:
            raise KeyError(f"Unknown schedule bin '{name}'")
        return b

    def add(self, bin_name, func, name=None, before=(), after=()):
        """Schedule ``func`` (a zero-argument callable) in ``bin_name``."""
        if name is None:
            thorn = getattr(getattr(func, "__self__", None), "name", "?")
            name = f"{thorn}::{func.__name__}"
        self._bins[self._bin(bin_name)].append(
            ScheduleItem(name, func, [b.lower() for b in before], [a.lower() for a in after])
        )
        self._sorted.clear()

    def items(self, bin_name) -> list[ScheduleItem]:
        b = self._bin(bin_name)
        if b not in self._sorted:
            self._sorted[b] = self._toposort(self._bins[b])
        return self._sorted[b]

    def run(self, bin_name) -> None:
        for item in self.items(bin_name):
            item.func()

    @staticmethod
    def _toposort(items: list[ScheduleItem]) -> list[ScheduleItem]:
        names = {it.name.lower(): i for i, it in enumerate(items)}
        deps = {i: set() for i in range(len(items))}  # i must run after deps[i]
        for i, it in enumerate(items):
            for a in it.after:
                if a in names:
                    deps[i].add(names[a])
            for b in it.before:
                if b in names:
                    deps[names[b]].add(i)
        order, done = [], set()
        while len(order) < len(items):
            ready = [i for i in range(len(items)) if i not in done and deps[i] <= done]
            if not ready:
                raise RuntimeError("Cyclic before/after constraints in schedule")
            order.append(ready[0])
            done.add(ready[0])
        return [items[i] for i in order]

    def describe(self) -> str:
        lines = []
        for b in BINS:
            its = self.items(b)
            if its:
                lines.append(f"  {b}:")
                lines += [f"      {it.name}" for it in its]
        return "\n".join(lines)
