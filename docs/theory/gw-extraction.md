# Gravitational-wave extraction

## The Weyl scalar $\Psi_4$

```{eval-rst}
.. automodule:: pynr.thorns.weylscal4
   :no-members:
```

```{eval-rst}
.. autofunction:: pynr.kernels.adm.weyl_psi4
```

## Geodesic spheres

```{eval-rst}
.. automodule:: pynr.utils.geodesic
   :no-members:
```

## Spin-weighted spherical harmonics

```{eval-rst}
.. automodule:: pynr.utils.swsh
   :no-members:
```

## Interpolation to the sphere

```{eval-rst}
.. automodule:: pynr.utils.interpolation
   :no-members:
```

## Multipole decomposition

```{eval-rst}
.. automodule:: pynr.thorns.multipole
   :no-members:
```

## From $\Psi_4$ to strain, energy and momentum

kuibit integrates $\Psi_4^{\ell m}$ twice in the frequency domain
("fixed-frequency integration", Reisswig & Pollney 2011):

$$ h^{\ell m}(\omega) = -\frac{\Psi_4^{\ell m}(\omega)}{\max(\omega, \omega_0)^2}, $$ (eq-ffi)

where $\omega_0$ is set below the lowest physical frequency (the `pcut`
argument). The radiated power is

$$ \frac{dE}{dt} = \frac{r^2}{16\pi}\sum_{\ell m}\left|\int_{-\infty}^t \Psi_4^{\ell m}\,dt'\right|^2 . $$ (eq-gw-power)
