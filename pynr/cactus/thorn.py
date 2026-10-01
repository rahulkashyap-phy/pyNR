# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
"""Base class and registry for thorns.

A thorn is a class that

1. declares its parameters (``parameters`` — the ``param.ccl`` analogue),
2. allocates/registers grid functions in :meth:`Thorn.setup`
   (the ``interface.ccl`` analogue), and
3. adds functions to schedule bins in :meth:`Thorn.schedule`
   (the ``schedule.ccl`` analogue).

Thorns only talk to each other through grid functions, parameters and the
small set of services other thorns publish (e.g. ``MoL.register_evolved``).
That is what makes a thorn replaceable: a new initial-data thorn only has to
fill the ``ADMBase`` grid functions; nothing else changes.

Minimal example::

    @register_thorn
    class Hello(Thorn):
        name = "Hello"
        parameters = {"greeting": Param("hello world", "What to say")}

        def schedule(self, S):
            S.add("STARTUP", self.say_hello)

        def say_hello(self):
            print(self.p.greeting)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from pynr.cactus.params import Param

if TYPE_CHECKING:
    from pynr.cactus.schedule import Schedule
    from pynr.cactus.simulation import Simulation

THORNS: dict[str, type[Thorn]] = {}


def register_thorn(cls: type[Thorn]) -> type[Thorn]:
    """Class decorator making a thorn available to ``ActiveThorns``."""
    THORNS[cls.name.lower()] = cls
    return cls


class Thorn:
    """Base class for all thorns."""

    #: Thorn name as used in parameter files (``Name::param``).
    name: ClassVar[str] = "Thorn"
    #: Other thorns that must be active for this one to work.
    requires: ClassVar[tuple[str, ...]] = ()
    #: Parameter declarations.
    parameters: ClassVar[dict[str, Param]] = {}

    def __init__(self, sim: Simulation):
        self.sim = sim

    @property
    def p(self):
        """This thorn's parameters (read-only, attribute access)."""
        return self.sim.params.of(self.name)

    def setup(self) -> None:
        """Allocate and register grid functions. Called after the grid exists."""

    def schedule(self, S: Schedule) -> None:
        """Add this thorn's routines to schedule bins."""

    def info(self, msg: str) -> None:
        self.sim.log(f"INFO ({self.name}): {msg}")
