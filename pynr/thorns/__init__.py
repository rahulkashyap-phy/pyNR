# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
"""All thorns shipped with pyNR. Importing this package registers them.

.. table:: Thorns shipped with pyNR and their ET counterparts.
   :name: tab-thorns

   =================  ==================================================  ==========================
   thorn              role                                                ET counterpart
   =================  ==================================================  ==========================
   Cactus             run control (termination)                           flesh
   CoordBase          domain extent and grid spacing                      CoordBase
   Driver             ghost zones, kernel backend                         PUGH / Carpet
   Time               time step (Courant factor)                          Time
   IO                 output directory                                    IOUtil
   ADMBase            ADM variables and initial-data selectors            ADMBase
   Exact              analytic spacetimes (Minkowski waves, BHs)          Exact
   Perturb            add a Gaussian l-pole metric perturbation           (NoiseBase-like)
   ADMEvolve          ADM evolution equations + slicing                   ADM (legacy)
   MoL                method-of-lines time integration                    MoL
   Dissipation        Kreiss-Oliger dissipation                           Dissipation
   ADMConstraints     Hamiltonian & momentum constraints                  ML_ADMConstraints
   WeylScal4          Newman-Penrose Psi4                                 WeylScal4
   Multipole          l,m decomposition on geodesic spheres               Multipole
   IOHDF5             3D/2D grid functions in Carpet HDF5 format          CarpetIOHDF5
   IOScalar           reductions (min/max/norm2) in Carpet ASCII          CarpetIOScalar
   IOBasic            progress table on stdout                            IOBasic
   =================  ==================================================  ==========================
"""

from pynr.thorns import (  # noqa: F401
    admbase,
    admconstraints,
    admevolve,
    core,
    dissipation,
    exact,
    io,
    mol,
    multipole,
    perturb,
    weylscal4,
)
