# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
"""Core thorns that are always active: Cactus, CoordBase, Driver, Time, IO."""

from pynr.cactus import Param, Thorn, register_thorn


@register_thorn
class Cactus(Thorn):
    name = "Cactus"
    parameters = {
        "terminate": Param("iteration", "Condition for ending the run",
                           keywords=("never", "iteration", "time", "either")),
        "cctk_itlast": Param(10, "Final iteration (terminate = iteration/either)"),
        "cctk_final_time": Param(-1.0, "Final time (terminate = time/either)"),
    }


@register_thorn
class CoordBase(Thorn):
    name = "CoordBase"
    parameters = {
        **{f"{a}{e}": Param(v, f"{'Lower' if e == 'min' else 'Upper'} {a} boundary of the physical domain")
           for a in "xyz" for e, v in (("min", -1.0), ("max", 1.0))},
        **{f"d{a}": Param(0.1, f"Grid spacing in {a}") for a in "xyz"},
        **{f"periodic_{a}": Param(False, f"Periodic in {a} (period = {a}max - {a}min)") for a in "xyz"},
    }


@register_thorn
class Driver(Thorn):
    name = "Driver"
    parameters = {
        "ghost_size": Param(3, "Ghost/boundary points on each side (3 needed for KO dissipation)"),
        "backend": Param("numba", "Kernel implementation", keywords=("numba", "numpy")),
    }


@register_thorn
class Time(Thorn):
    name = "Time"
    parameters = {
        "timestep_method": Param("courant_static", "How dt is chosen",
                                 keywords=("courant_static", "given")),
        "dtfac": Param(0.25, "Courant factor: dt = dtfac * min(dx)"),
        "timestep": Param(0.0, "dt when timestep_method = given"),
    }


@register_thorn
class IO(Thorn):
    name = "IO"
    parameters = {
        "out_dir": Param("", "Output directory (default: parameter-file name)"),
    }
