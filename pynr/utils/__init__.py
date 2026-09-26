"""Generic numerical methods used by the thorns.

=====================================  ==========================================  ==========================
task                                   pyNR module                                 library underneath
=====================================  ==========================================  ==========================
finite differences (4th order)         :mod:`pynr.kernels.fd`                      Numba
method-of-lines time integration       :mod:`pynr.utils.integrators`               NumPy in-place updates
interpolation grid -> points           :mod:`pynr.utils.interpolation`             Numba (Lagrange)
quadrature on spheres                  :mod:`pynr.utils.geodesic`                  NumPy
spin-weighted spherical harmonics      :mod:`pynr.utils.swsh`                      NumPy
small ODE systems (geodesics, TOV)     :func:`scipy.integrate.solve_ivp`           SciPy
elliptic solves (future: puncture ID)  :mod:`scipy.sparse.linalg` / PyAMG          SciPy / PyAMG
spectral methods (future)              :mod:`numpy.fft`, ``scipy.fft``             NumPy / SciPy
HDF5 output                            :mod:`pynr.thorns.io`                       h5py
analysis & plotting                    kuibit                                      kuibit / matplotlib
=====================================  ==========================================  ==========================
"""
