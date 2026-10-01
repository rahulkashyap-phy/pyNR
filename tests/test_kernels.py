# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
"""Tests of the numerical kernels against exact solutions."""

import numpy as np
import pytest
from conftest import state_from_model

from pynr.kernels import adm, adm_numpy
from pynr.thorns import exact
from pynr.utils.geodesic import angles, geodesic_sphere
from pynr.utils.interpolation import interpolate
from pynr.utils.swsh import modes, sYlm


def _rhs_max(U, axes, h, lapse=0, backend=adm.adm_rhs):
    rhs = np.zeros_like(U)
    idx = np.array([1 / h] * 3)
    backend(U, rhs, idx, 3, lapse, True, *axes, 0.0)
    return np.abs(rhs[:, 3:-3, 3:-3, 3:-3]).max()


@pytest.mark.parametrize("spin", [0.0, 0.7])
def test_kerr_schild_is_stationary_4th_order(kerr_state, spin):
    """Kerr-Schild data with its exact lapse/shift must have dt(U) -> 0 at O(h^4)."""
    e = []
    for h in (0.1, 0.05):
        U, axes = kerr_state(h, spin=spin)
        e.append(_rhs_max(U, axes, h))
    order = np.log2(e[0] / e[1])
    assert e[1] < 1e-4
    assert order > 3.5, f"convergence order {order:.2f}, errors {e}"


def test_schwarzschild_isotropic_is_static():
    e = []
    for h in (0.1, 0.05):
        axes = [c + h * np.arange(-9, 10) for c in (2.0, 1.0, 1.5)]
        U = state_from_model(exact.schwarzschild_isotropic, *axes, M=1.0)
        e.append(_rhs_max(U, axes, h))
    assert np.log2(e[0] / e[1]) > 3.5


def test_numba_matches_numpy(kerr_state):
    U, axes = kerr_state(0.1, spin=0.5)
    rng = np.random.default_rng(1)
    U[6:12] += 1e-3 * rng.standard_normal(U[6:12].shape)  # generic K_ij
    for lapse in (0, 1, 2):
        r1, r2 = np.zeros_like(U), np.zeros_like(U)
        idx = np.array([10.0] * 3)
        adm.adm_rhs(U, r1, idx, 3, lapse, True, *axes, 0.0)
        adm_numpy.adm_rhs(U, r2, idx, 3, lapse, True, *axes, 0.0)
        np.testing.assert_allclose(r1, r2, rtol=1e-9, atol=1e-9)


def test_constraints_vanish_for_kerr(kerr_state):
    e = []
    for h in (0.1, 0.05):
        U, axes = kerr_state(h, spin=0.6)
        H = np.zeros(U.shape[1:])
        M = np.zeros((3, *U.shape[1:]))
        adm.adm_constraints(U, H, M, np.array([1 / h] * 3), 3)
        e.append(max(np.abs(H).max(), np.abs(M).max()))
    assert e[1] < 1e-4 and np.log2(e[0] / e[1]) > 3.5


def test_psi4_linear_wave():
    """For h_yy = -h_zz = b(x - t) on the +x axis, Psi4 = -b'' (tetrad: e_theta = -z)."""
    A, d, h = 1e-6, 4.0, 0.05
    x = 5.0 + h * np.arange(-20, 21)
    y = z = h * np.arange(-3, 4)
    U = state_from_model(exact.linear_wave, x, y, z, A=A, d=d)
    re, im = np.zeros(U.shape[1:]), np.zeros(U.shape[1:])
    adm.weyl_psi4(U, re, im, np.array([1 / h] * 3), 3, x, y, z)
    k = 2 * np.pi / d
    expect = A * k**2 * np.sin(k * x[3:-3])
    np.testing.assert_allclose(re[3:-3, 3, 3], expect, atol=1e-4 * A * k**2)
    assert np.abs(im[3:-3, 3, 3]).max() < 1e-4 * A * k**2


def test_geodesic_quadrature_orthonormal_swsh():
    pts, _, w = geodesic_sphere(4)
    assert w.sum() == pytest.approx(4 * np.pi, rel=1e-12)
    th, ph = angles(pts)
    ms = modes(4, -2)
    Y = np.array([sYlm(-2, l, m, th, ph) for l, m in ms])
    G = (Y * w) @ Y.conj().T
    assert np.abs(G - np.eye(len(ms))).max() < 5e-3


def test_interpolation_order():
    h = 0.1
    ax = [h * np.arange(-10, 11)] * 3
    X, Y, Z = np.meshgrid(*ax, indexing="ij")
    f = np.sin(X) * np.cos(2 * Y) * np.exp(0.3 * Z)
    pts = np.array([[0.123, -0.271, 0.333], [0.5, 0.05, -0.44]])
    v = interpolate(f, (-1, -1, -1), (h, h, h), pts, order=3)
    exact_v = np.sin(pts[:, 0]) * np.cos(2 * pts[:, 1]) * np.exp(0.3 * pts[:, 2])
    np.testing.assert_allclose(v, exact_v, atol=2e-5)
