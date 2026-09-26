"""End-to-end runs: convergence against exact solutions, and kuibit compatibility."""

import os

import numpy as np
import pytest

from pynr import Simulation
from pynr.kernels.adm import ALP

PAR = os.path.join(os.path.dirname(__file__), "..", "par")


def _gauge_wave_error(dx, t_final=0.5):
    sim = Simulation.from_parfile(
        os.path.join(PAR, "gauge_wave.par"),
        overrides={
            "CoordBase::dx": dx, "CoordBase::dy": dx, "CoordBase::dz": dx,
            "CoordBase::ymin": -dx, "CoordBase::ymax": dx,
            "CoordBase::zmin": -dx, "CoordBase::zmax": dx,
            "Cactus::cctk_final_time": t_final,
            "IOBasic::outInfo_every": 0, "IOScalar::outScalar_every": 0, "IOHDF5::out2D_every": 0,
        },
        verbose=False,
    ).run()
    X, Y, Z = sim.grid.meshgrid()
    _, _, alp, _ = sim.thorn("Exact").solution(sim.time, X, Y, Z)
    U = sim.thorn("ADMBase").U
    return np.abs(U[ALP] - alp)[sim.grid.interior].max()


def test_gauge_wave_converges_4th_order(tmp_outdir):
    e1, e2 = _gauge_wave_error(0.04), _gauge_wave_error(0.02)
    assert np.log2(e1 / e2) > 3.5, (e1, e2)


def test_numpy_backend_runs(tmp_outdir):
    sim = Simulation.from_parfile(
        os.path.join(PAR, "gauge_wave.par"),
        overrides={"Driver::backend": "numpy", "Cactus::terminate": "iteration",
                   "Cactus::cctk_itlast": 4, "IOBasic::outInfo_every": 0},
        verbose=False,
    ).run()
    assert np.isfinite(sim.thorn("ADMBase").U).all()


def test_output_readable_by_kuibit(tmp_outdir):
    kuibit = pytest.importorskip("kuibit.simdir")
    sim = Simulation.from_parfile(
        os.path.join(PAR, "schwarzschild_perturbed.par"),
        overrides={"Cactus::terminate": "iteration", "Cactus::cctk_itlast": 4,
                   "CoordBase::xmin": -8.1, "CoordBase::xmax": 8.1,
                   "CoordBase::ymin": -8.1, "CoordBase::ymax": 8.1,
                   "CoordBase::zmin": -8.1, "CoordBase::zmax": 8.1,
                   "CoordBase::dx": 0.6, "CoordBase::dy": 0.6, "CoordBase::dz": 0.6,
                   "Multipole::radius": {0: 4.0}, "Multipole::nradii": 1,
                   "Multipole::out_every": 2,
                   "Perturb::radius": 3.0, "ADMEvolve::excision_radius": 1.2,
                   "IOHDF5::out_every": 2, "IOHDF5::out_vars": "ADMBase::alp",
                   "IOHDF5::out2D_every": 2, "IOScalar::outScalar_every": 1,
                   "IO::out_dir": "kuibit_run", "IOBasic::outInfo_every": 0},
        verbose=False,
    ).run()
    sd = kuibit.SimDir("kuibit_run")
    alp3 = sd.gf.xyz["alp"]
    assert alp3.available_iterations == [0, 2, 4]
    data = alp3[4].get_level(0)
    assert tuple(data.shape) == sim.grid.shape
    np.testing.assert_allclose(data.x0, sim.grid.origin)
    np.testing.assert_allclose(data.data, sim.thorn("ADMBase").U[ALP])
    assert "gxx" in sd.gf.xy and "Psi4r" in sd.gf.xz
    assert sd.gf.xy["gxx"][2].get_level(0).shape[0] == sim.grid.shape[0]
    ts = sd.ts.maximum["gxx"]
    assert len(ts) == 5
    psi4 = sd.gws[4.0][(2, 0)]
    assert len(psi4) == 3


def test_blowup_aborts_run(tmp_outdir):
    """A run that blows up stops with a message instead of stepping on garbage."""
    sim = Simulation.from_parfile(
        os.path.join(PAR, "gauge_wave.par"),
        overrides={"Cactus::terminate": "iteration", "Cactus::cctk_itlast": 50,
                   "MoL::check_nan_every": 1, "IOBasic::outInfo_every": 0,
                   "IOScalar::outScalar_every": 0, "IOHDF5::out2D_every": 0},
        verbose=False,
    )
    sim.initialize()
    sim.thorn("ADMBase").U[0, 10, 4, 4] = np.nan
    sim.evolve()
    assert sim.aborted and "blow-up" in sim.aborted
    assert sim.iteration < 50
