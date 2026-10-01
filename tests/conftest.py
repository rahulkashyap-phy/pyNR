# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
import numpy as np
import pytest

from pynr.kernels.adm import ALP, BETAX, KXX, NVARS
from pynr.thorns import exact


def state_from_model(model, x, y, z, t=0.0, **kw):
    """Pack an exact solution into a (16, nx, ny, nz) ADM state array."""
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    g, K, alp, beta = model(t, X, Y, Z, **kw)
    U = np.empty((NVARS, *X.shape))
    U[0:6] = g
    U[KXX:KXX + 6] = K
    U[ALP] = alp
    U[BETAX:BETAX + 3] = beta
    return U


@pytest.fixture
def kerr_state():
    def make(h, center=(2.5, 1.5, 2.0), half=0.6, spin=0.7):
        axes = [c + h * np.arange(-int(half / h) - 3, int(half / h) + 4) for c in center]
        return state_from_model(exact.kerr_schild, *axes, M=1.0, spin=spin), axes

    return make


@pytest.fixture
def tmp_outdir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path
