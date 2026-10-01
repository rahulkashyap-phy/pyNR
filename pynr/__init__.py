# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
"""pyNR — numerical relativity in Python, organised like the Einstein Toolkit.

The package mirrors the Cactus/Einstein Toolkit (ET) architecture:

* :mod:`pynr.cactus` is the *flesh*: parameter files, parameters, the
  schedule, grid functions and the main evolution loop.
* :mod:`pynr.thorns` holds the *thorns*: self-contained modules (initial data,
  evolution, analysis, I/O) that declare parameters and schedule functions.
* :mod:`pynr.kernels` holds the compute kernels (Numba, with pure NumPy
  reference versions) — the only place where performance matters.
* :mod:`pynr.utils` holds generic numerical methods (finite differences,
  time integrators, interpolation, quadrature on the sphere, ...).

Running a simulation::

    from pynr import Simulation
    sim = Simulation.from_parfile("par/gauge_wave.par")
    sim.run()

or from the shell: ``pynr run par/gauge_wave.par``.
"""

__version__ = "0.1.0.dev0"

from pynr.cactus.simulation import Simulation

__all__ = ["Simulation", "__version__"]
