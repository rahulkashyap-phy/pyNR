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
