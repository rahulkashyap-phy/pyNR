# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
"""The *flesh*: the thorn-independent core of pyNR.

In Cactus the flesh knows nothing about physics. It reads the parameter file,
activates thorns, builds the schedule from what each thorn asks for, allocates
grid functions and then steps through the schedule bins. pyNR keeps the same
separation so that thorns (and the libraries they use) can be swapped without
touching the rest of the code.

.. table:: Cactus/ET concepts and their pyNR counterparts.
   :name: tab-flesh-mapping

   =========================  ==========================================
   Cactus / ET                pyNR
   =========================  ==========================================
   ``*.par`` parameter file   :mod:`pynr.cactus.parfile` (same syntax)
   ``param.ccl``              ``Thorn.parameters`` (:class:`~pynr.cactus.params.Param`)
   ``interface.ccl``          ``Thorn.setup`` registering grid functions
   ``schedule.ccl``           ``Thorn.schedule`` adding to schedule bins
   ``cctkGH``                 :class:`~pynr.cactus.simulation.Simulation`
   Driver (PUGH/Carpet)       :class:`~pynr.cactus.grid.UniformGrid`
   =========================  ==========================================
"""

from pynr.cactus.params import Param
from pynr.cactus.thorn import Thorn, register_thorn

__all__ = ["Param", "Thorn", "register_thorn"]
