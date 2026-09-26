r"""Explicit Runge-Kutta time integrators for the method of lines (MoL).

After spatial discretisation the PDEs become a large ODE system
:math:`\partial_t \mathbf u = \mathbf F(t, \mathbf u)`. We integrate it with
explicit Runge-Kutta methods written as in-place array updates, so memory
traffic is a few passes over the state per stage — no Python loop over
grid points.

======== ===== ============================================================
method   order notes
======== ===== ============================================================
Euler    1     unstable for centred differences — for demonstrations only
RK2      2     Heun / midpoint
ICN      2     iterated Crank-Nicolson (2 iterations), classic in NR
RK3      3     strong-stability-preserving (Shu-Osher)
RK4      4     classic; default, as in most ET BSSN runs
======== ===== ============================================================

``rhs(t, U, dU)`` must fill ``dU``; ``post(U)`` applies state boundary
conditions (periodic sync etc.) after every stage.

Why not :func:`scipy.integrate.solve_ivp`? It is excellent for small ODE
systems (we use it e.g. for geodesics and TOV-type problems), but it flattens
and copies the state and adapts the step globally, which is wasteful for
:math:`10^7`-variable hyperbolic PDEs where the CFL condition fixes
:math:`\Delta t` anyway.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

Rhs = Callable[[float, np.ndarray, np.ndarray], None]
Post = Callable[[np.ndarray], None]


def _noop(U):
    pass


def _buf(scratch, name, U):
    """Reuse work arrays between steps (allocation is not free at 10^7 points)."""
    if scratch is None:
        return np.zeros_like(U)
    b = scratch.get(name)
    if b is None or b.shape != U.shape:
        b = scratch[name] = np.zeros_like(U)
    return b


def euler(U, t, dt, rhs: Rhs, post: Post = _noop, scratch=None):
    k = _buf(scratch, "k", U)
    rhs(t, U, k)
    U += dt * k
    post(U)


def rk2(U, t, dt, rhs: Rhs, post: Post = _noop, scratch=None):
    """Heun's method: U1 = U0 + dt F(U0); U = (U0 + U1 + dt F(U1)) / 2."""
    k = _buf(scratch, "k", U)
    U0 = _buf(scratch, "U0", U)
    U0[...] = U
    rhs(t, U, k)
    U += dt * k
    post(U)
    rhs(t + dt, U, k)
    U[...] = 0.5 * (U0 + U + dt * k)
    post(U)


def icn(U, t, dt, rhs: Rhs, post: Post = _noop, scratch=None, iterations=2):
    """Iterated Crank-Nicolson: U* = U0 + dt/2 (F(U0) + F(U*)), iterated."""
    k0 = _buf(scratch, "k0", U)
    k = _buf(scratch, "k", U)
    U0 = _buf(scratch, "U0", U)
    U0[...] = U
    rhs(t, U0, k0)
    U[...] = U0 + dt * k0
    post(U)
    for _ in range(iterations):
        rhs(t + dt, U, k)
        U[...] = U0 + 0.5 * dt * (k0 + k)
        post(U)


def rk3(U, t, dt, rhs: Rhs, post: Post = _noop, scratch=None):
    """SSP-RK3 (Shu & Osher 1988)."""
    k = _buf(scratch, "k", U)
    U0 = _buf(scratch, "U0", U)
    U0[...] = U
    rhs(t, U, k)
    U += dt * k
    post(U)
    rhs(t + dt, U, k)
    U[...] = 0.75 * U0 + 0.25 * (U + dt * k)
    post(U)
    rhs(t + 0.5 * dt, U, k)
    U[...] = (U0 + 2.0 * (U + dt * k)) / 3.0
    post(U)


def rk4(U, t, dt, rhs: Rhs, post: Post = _noop, scratch=None):
    """Classic 4th-order Runge-Kutta with one accumulator and one stage buffer."""
    k = _buf(scratch, "k", U)
    U0 = _buf(scratch, "U0", U)
    U0[...] = U
    acc = _buf(scratch, "acc", U)
    rhs(t, U0, k)
    acc[...] = k
    np.multiply(k, 0.5 * dt, out=U)
    U += U0
    post(U)
    rhs(t + 0.5 * dt, U, k)
    acc += 2.0 * k
    np.multiply(k, 0.5 * dt, out=U)
    U += U0
    post(U)
    rhs(t + 0.5 * dt, U, k)
    acc += 2.0 * k
    np.multiply(k, dt, out=U)
    U += U0
    post(U)
    rhs(t + dt, U, k)
    acc += k
    np.multiply(acc, dt / 6.0, out=U)
    U += U0
    post(U)


METHODS = {"Euler": euler, "RK2": rk2, "ICN": icn, "RK3": rk3, "RK4": rk4}
