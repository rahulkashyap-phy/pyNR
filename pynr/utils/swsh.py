# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
r"""Spin-weighted spherical harmonics ${}_sY_{\ell m}(\theta,\phi)$.

Gravitational radiation is decomposed as

$$
    \Psi_4(t, r, \theta, \phi) = \sum_{\ell\ge2}\sum_{m=-\ell}^{\ell}
        \Psi_4^{\ell m}(t, r)\; {}_{-2}Y_{\ell m}(\theta,\phi),
    \qquad
    \Psi_4^{\ell m} = \oint \Psi_4\, {}_{-2}\bar Y_{\ell m}\, d\Omega .
$$ (eq-swsh-decomposition)

We use Goldberg et al. (1967) with the phase convention of the Einstein
Toolkit's ``Multipole`` thorn, for which
${}_{-2}Y_{22} = \sqrt{5/64\pi}\,(1+\cos\theta)^2 e^{2i\phi}$:

$$
    {}_sY_{\ell m} = (-1)^{s}\sqrt{\frac{2\ell+1}{4\pi}
        \frac{(\ell+m)!(\ell-m)!}{(\ell+s)!(\ell-s)!}}
        \sum_r \binom{\ell-s}{r}\binom{\ell+s}{r+s-m}(-1)^{\ell-r-s+m}\,
        \sin^{2\ell-k}(\theta/2)\cos^{k}(\theta/2)\, e^{im\phi},
    \quad k = 2r + s - m .
$$ (eq-swsh-goldberg)

"""

from __future__ import annotations

from math import comb, factorial, pi, sqrt

import numpy as np


def sYlm(s: int, l: int, m: int, theta, phi):
    """Spin-weighted spherical harmonic evaluated at arrays ``theta, phi``."""
    if l < abs(s) or abs(m) > l:
        return np.zeros(np.broadcast(theta, phi).shape, dtype=complex)
    theta = np.asarray(theta, float)
    pref = (-1) ** s * sqrt((2 * l + 1) / (4 * pi) * factorial(l + m) * factorial(l - m)
                            / (factorial(l + s) * factorial(l - s)))
    sh, ch = np.sin(theta / 2), np.cos(theta / 2)
    total = np.zeros_like(theta)
    for r in range(l - s + 1):
        if r + s - m < 0 or r + s - m > l + s:
            continue
        k = 2 * r + s - m
        total = total + (comb(l - s, r) * comb(l + s, r + s - m) * (-1) ** (l - r - s + m)
                         * sh ** (2 * l - k) * ch ** k)
    return pref * total * np.exp(1j * m * np.asarray(phi))


def modes(lmax: int, s: int = -2):
    """All ``(l, m)`` with ``|s| <= l <= lmax``."""
    return [(l, m) for l in range(abs(s), lmax + 1) for m in range(-l, l + 1)]
