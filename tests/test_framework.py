# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
import pytest

from pynr import Simulation
from pynr.cactus.parfile import parse_parfile_text
from pynr.cactus.schedule import Schedule

PAR = """
# a comment line
ActiveThorns = "ADMBase Exact
   MoL"
Cactus::cctk_itlast = 3   # trailing comment
CoordBase::dx = 1d-1
Multipole::radius[1] = 20
IO::out_dir = $parfile
IOBasic::outInfo_vars = "ADMBase::alp
  ADMBase::gxx"
Driver::backend = "numba"
ADMEvolve::advect_lapse = no
"""


def test_parfile_parser():
    e = parse_parfile_text(PAR, "mysim")
    assert e["activethorns"] == ["ADMBase", "Exact", "MoL"]
    assert e["cactus::cctk_itlast"] == 3
    assert e["coordbase::dx"] == pytest.approx(0.1)
    assert e["multipole::radius"] == {1: 20}
    assert e["io::out_dir"] == "mysim"
    assert e["admevolve::advect_lapse"] is False
    assert "ADMBase::gxx" in e["iobasic::outinfo_vars"]


def test_unknown_parameter_is_an_error(tmp_outdir):
    with pytest.raises(KeyError):
        Simulation.from_string('ActiveThorns = "ADMBase"\nADMBase::no_such_param = 1', verbose=False)
    with pytest.raises(KeyError):  # thorn not active
        Simulation.from_string("Exact::exact_model = \"Minkowski\"", verbose=False)


def test_bad_keyword_is_an_error(tmp_outdir):
    with pytest.raises(ValueError):
        Simulation.from_string('ActiveThorns = "ADMBase"\nADMBase::initial_lapse = "banana"',
                               verbose=False)


def test_schedule_ordering():
    S, calls = Schedule(), []
    S.add("INITIAL", lambda: calls.append("b"), name="T::b", after=["T::a"])
    S.add("CCTK_INITIAL", lambda: calls.append("a"), name="T::a")
    S.add("INITIAL", lambda: calls.append("c"), name="T::c", before=["T::a"])
    S.run("INITIAL")
    assert calls == ["c", "a", "b"]


def test_output_root_shared_by_cli_and_notebooks(tmp_path, monkeypatch):
    """Relative out_dirs resolve to <checkout>/simulations from any folder; env var overrides."""
    import os

    from pynr import paths

    monkeypatch.delenv("PYNR_OUTPUT_DIR", raising=False)
    checkout = paths.find_checkout(__file__)
    assert checkout and os.path.isfile(os.path.join(checkout, "pyproject.toml"))
    par = os.path.join(checkout, "par", "gauge_wave.par")
    for cwd in (checkout, os.path.join(checkout, "notebooks")):
        monkeypatch.chdir(cwd)
        assert paths.resolve_out_dir("gauge_wave", par) == os.path.join(checkout, "simulations", "gauge_wave")
    monkeypatch.setenv("PYNR_OUTPUT_DIR", str(tmp_path))
    assert paths.run_dir("x", par) == os.path.join(str(tmp_path), "x")
    assert paths.resolve_out_dir("/abs/run") == "/abs/run"
