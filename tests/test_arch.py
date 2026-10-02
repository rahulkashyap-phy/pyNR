# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
"""The architecture model (arch/model.yaml) must agree with the code: see docs/developer-guide.md."""

import os
import sys

import pytest

ARCH = os.path.join(os.path.dirname(__file__), "..", "arch")
pytest.importorskip("yaml")
sys.path.insert(0, ARCH)


def test_architecture_has_no_drift(tmp_path, monkeypatch):
    import check_drift

    monkeypatch.setenv("PYNR_OUTPUT_DIR", str(tmp_path))
    rep = check_drift.run(write_report=False)
    msgs = "\n".join(f"[{r}] {w}: {m} -> {f}" for r, w, m, f in rep.fails)
    assert not rep.fails, "architecture drift:\n" + msgs


def test_extracted_edges_have_direction():
    import extract

    ext = extract.extract(with_runs=False)
    types = {e["type"] for e in ext["edges"]}
    assert {"uses", "requires", "reads", "registers"} <= types
    regs = [e for e in ext["edges"] if e["type"] == "registers" and e["from"] == "ADMEvolve" and e["to"] == "MoL"]
    assert regs and set(regs[0]["functions"]) == {"rhs", "post", "rhs_final"}
