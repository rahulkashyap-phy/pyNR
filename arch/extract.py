# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
"""Extract pyNR's code graph: what the code actually does, for comparison with arch/model.yaml.

    python arch/extract.py                      # writes docs/_generated/arch/extracted.json
    python arch/extract.py --print              # also print a summary
    python arch/extract.py --record-timing simulations/gauge_wave   # add a run's cost to arch/timings.yaml

Edges are typed and directed exactly like the curated model:

``uses``       A imports B (A is the caller of B's functions)          -- ast: import statements
``requires``   thorn A needs thorn B active                            -- Thorn.requires
``reads``      A reads B's state at runtime                            -- ast: sim.thorn("B"), thorns.get("b")
``registers``  A hands callbacks to B, which B calls later             -- ast: S.add, register_evolved,
                                                                          add_rhs_hook, gf.register(update=)

Per parameter file it also records the active thorns, the schedule (bin -> routines in order), the registered
grid functions and groups, the key settings and the output files the run writes.
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import json
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "docs", "_generated", "arch")
EXTERNAL = {"numpy", "numba", "scipy", "h5py", "kuibit", "matplotlib", "yaml"}
_TAG = re.compile(r"^#\s*@component:\s*([\w.\-]+)", re.M)


def load_model(path=None):
    import yaml

    with open(path or os.path.join(ROOT, "arch", "model.yaml")) as fh:
        return yaml.safe_load(fh)


# --------------------------------------------------------------------------- module -> component
def python_files():
    out = []
    for d, _, files in os.walk(os.path.join(ROOT, "pynr")):
        if "__pycache__" in d:
            continue
        out += [os.path.relpath(os.path.join(d, f), ROOT) for f in files if f.endswith(".py")]
    return sorted(out)


def component_map(model):
    """Map every pynr/*.py file to a component (longest `src` match; `# @component:` tags override)."""
    rules = []
    for name, c in model["components"].items():
        for s in c.get("src", []):
            rules.append((s, name))
    rules.sort(key=lambda r: -len(r[0]))
    mapping = {}
    for f in python_files():
        with open(os.path.join(ROOT, f)) as fh:
            m = _TAG.search(fh.read(2000))
        if m:
            mapping[f] = m.group(1)
            continue
        for src, name in rules:
            if f == src or (src.endswith("/") and f.startswith(src)) or fnmatch.fnmatch(f, src):
                mapping[f] = name
                break
    return mapping


def _exists_exact(rel):
    """Case-sensitive existence check (macOS file systems are case-insensitive)."""
    d = ROOT
    for part in rel.split("/"):
        try:
            if part not in os.listdir(d):
                return False
        except (FileNotFoundError, NotADirectoryError):
            return False
        d = os.path.join(d, part)
    return True


def module_file(modname):
    """pynr.kernels.adm -> pynr/kernels/adm.py (or the package __init__)."""
    rel = modname.replace(".", "/")
    for cand in (rel + ".py", rel + "/__init__.py"):
        if _exists_exact(cand):
            return cand
    return None


# --------------------------------------------------------------------------- static scan
def _literal(node):
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _func_name(node):
    """self.rhs -> 'rhs'; rhs -> 'rhs'."""
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return None


def scan_file(f):
    """Imports, thorn accesses and callback registrations in one file."""
    with open(os.path.join(ROOT, f)) as fh:
        tree = ast.parse(fh.read(), filename=f)
    imports, reads, regs = [], [], []
    # imports under `if TYPE_CHECKING:` exist only for type hints, not at runtime: not a `uses` edge
    type_only = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and "TYPE_CHECKING" in ast.unparse(node.test):
            type_only |= {id(n) for b in node.body for n in ast.walk(b)}
    for node in ast.walk(tree):
        if id(node) in type_only:
            continue
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".")[0] == "pynr":
                base = node.module
                for a in node.names:  # `from pynr.kernels import adm` imports a submodule
                    sub = module_file(f"{base}.{a.name}")
                    imports.append((sub or module_file(base), node.lineno))
            elif node.module.split(".")[0] in EXTERNAL:
                imports.append(("ext:" + node.module.split(".")[0], node.lineno))
        elif isinstance(node, ast.Import):
            for a in node.names:
                top = a.name.split(".")[0]
                if top == "pynr":
                    imports.append((module_file(a.name), node.lineno))
                elif top in EXTERNAL:
                    imports.append(("ext:" + top, node.lineno))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            attr, args, kw = node.func.attr, node.args, {k.arg: k.value for k in node.keywords}
            if attr == "thorn" and args and _literal(args[0]):
                reads.append((_literal(args[0]), node.lineno, f'sim.thorn("{_literal(args[0])}")'))
            elif attr == "get" and isinstance(node.func.value, ast.Attribute) \
                    and node.func.value.attr == "thorns" and args and _literal(args[0]):
                reads.append((_literal(args[0]), node.lineno, f'thorns.get("{_literal(args[0])}")'))
            elif attr == "add" and len(args) >= 2 and _literal(args[0]):  # S.add("BIN", self.fn)
                regs.append(("Schedule", "add", _literal(args[0]).upper().removeprefix("CCTK_"),
                             [_func_name(args[1])], node.lineno))
            elif attr == "register_evolved":
                fns = [_func_name(a) for a in args[2:4]] + [_func_name(kw[k]) for k in kw
                                                             if k in ("rhs_final", "post")]
                regs.append(("MoL", "register_evolved", "EVOL", [x for x in fns if x], node.lineno))
            elif attr == "add_rhs_hook" and args:
                regs.append(("MoL", "add_rhs_hook", "EVOL", [_func_name(args[0])], node.lineno))
            elif attr == "register" and "update" in kw:
                regs.append(("GridFunctions", "register(update=)", "on demand",
                             [_func_name(kw["update"])], node.lineno))
    return imports, reads, regs


# --------------------------------------------------------------------------- runtime introspection
def thorn_table():
    sys.path.insert(0, ROOT)
    import pynr.thorns  # noqa: F401
    from pynr.cactus.thorn import THORNS

    return {c.name: {"module": os.path.relpath(sys.modules[c.__module__].__file__, ROOT),
                     "requires": list(c.requires)} for c in THORNS.values()}


def _coarsen(entries):
    """Keep the domain, use at most 24 cells per direction (the schedule does not depend on dx)."""
    over = {}
    for a in "xyz":
        lo, hi = entries.get(f"coordbase::{a}min", -1.0), entries.get(f"coordbase::{a}max", 1.0)
        d = entries.get(f"coordbase::d{a}", 0.1)
        n = round((hi - lo) / d)
        if n > 24:
            over[f"CoordBase::d{a}"] = (hi - lo) / 24
    return over


SETTINGS = ["ADMBase::initial_data", "Exact::exact_model", "ADMBase::initial_lapse", "ADMBase::initial_shift",
            "ADMBase::evolution_method", "ADMBase::lapse_evolution_method", "ADMEvolve::bound",
            "ADMEvolve::excision_radius", "MoL::ODE_Method", "Dissipation::epsdis", "Perturb::amplitude",
            "Perturb::l", "Perturb::m", "Multipole::l_max", "Cactus::cctk_final_time"]


def problem_runs():
    """Build (but do not run) a Simulation for every par/*.par: schedule, grid functions, outputs."""
    sys.path.insert(0, ROOT)
    from pynr.cactus.parfile import parse_parfile
    from pynr.cactus.schedule import BINS
    from pynr.cactus.simulation import Simulation

    out = {}
    tmp = tempfile.mkdtemp(prefix="pynr-extract-")
    old = os.environ.get("PYNR_OUTPUT_DIR")
    os.environ["PYNR_OUTPUT_DIR"] = tmp
    try:
        for par in sorted(os.listdir(os.path.join(ROOT, "par"))):
            if not par.endswith(".par"):
                continue
            name = par[:-4]
            path = os.path.join(ROOT, "par", par)
            entries = parse_parfile(path)
            over = {"IO::out_dir": name, **_coarsen(entries)}
            sim = Simulation.from_parfile(path, overrides=over, verbose=False)
            if sim._logfile:
                sim._logfile.close()
            p = sim.params
            settings = {}
            for k in SETTINGS:
                t, n = k.split("::")
                if sim.has_thorn(t):
                    settings[k] = p.get(t, n)
            if sim.has_thorn("Multipole"):
                mp = p.of("Multipole")
                settings["Multipole::radius"] = [float(r) for r in mp.radius[: mp.nradii]]
            out[name] = {
                "parfile": f"par/{par}",
                "active_thorns": [t.name for t in sim.thorns.values()],
                "schedule": {b: [it.name for it in sim.schedule.items(b)] for b in BINS
                             if sim.schedule.items(b)},
                "gridfunctions": sim.gf.names(),
                "groups": sorted(sim.gf._groups),
                "settings": settings,
                "outputs": predicted_outputs(sim, name),
            }
    finally:
        if old is None:
            os.environ.pop("PYNR_OUTPUT_DIR", None)
        else:
            os.environ["PYNR_OUTPUT_DIR"] = old
    return out


def predicted_outputs(sim, name):
    files = ["pynr.log", "parameters.par", f"{name}.par"]
    if sim.has_thorn("IOHDF5"):
        t = sim.thorn("IOHDF5")
        if t.p.out_every > 0:
            files += [f"{v.split('::')[1]}.xyz.h5" for v in t.vars3d]
        if t.p.out2D_every > 0:
            files += [f"{v.split('::')[1]}.{pl}.h5" for v in t.vars2d for pl in t.p.out2D_planes.split()]
    if sim.has_thorn("IOScalar"):
        t = sim.thorn("IOScalar")
        if t.p.outScalar_every > 0:
            files += [f"{v.split('::')[1]}.{r}.asc" for v in t.vars for r in t.reds]
    if sim.has_thorn("Multipole"):
        t = sim.thorn("Multipole")
        files += [f"mp_{n}_l*_m*_r{R:.2f}.asc" for (_, _, _, n) in t.vars for R in t.radii]
    return files


# --------------------------------------------------------------------------- assemble
def extract(model=None, with_runs=True):
    model = model or load_model()
    cmap = component_map(model)
    thorns = thorn_table()
    thorn_comp = {}
    for name, c in model["components"].items():
        for t in c.get("thorns", []):
            thorn_comp[t.lower()] = name

    def comp_of_thorn(t):
        return thorn_comp.get(t.lower(), f"?thorn:{t}")

    edges = []
    for f in python_files():
        src = cmap.get(f, f"?module:{f}")
        imports, reads, regs = scan_file(f)
        for target, line in imports:
            if target is None:
                continue
            dst = target[4:] if target.startswith("ext:") else cmap.get(target, f"?module:{target}")
            if dst != src:
                edges.append({"from": src, "to": dst, "type": "uses", "file": f, "line": line,
                              "detail": target})
        for t, line, detail in reads:
            dst = comp_of_thorn(t)
            if dst != src:
                edges.append({"from": src, "to": dst, "type": "reads", "file": f, "line": line,
                              "detail": detail})
        for into, via, stage, fns, line in regs:
            dst = comp_of_thorn(into) if into == "MoL" else "flesh"
            if dst != src:
                edges.append({"from": src, "to": dst, "type": "registers", "file": f, "line": line,
                              "detail": f"{via} {','.join(x for x in fns if x)} [{stage}]",
                              "via": via, "stage": stage, "functions": fns})
    for t, info in thorns.items():
        for r in info["requires"]:
            a, b = comp_of_thorn(t), comp_of_thorn(r)
            if a != b:
                edges.append({"from": a, "to": b, "type": "requires", "file": info["module"],
                              "line": 0, "detail": f"{t}.requires = {r}"})
    return {"modules": cmap, "thorns": thorns, "edges": edges,
            "problems": problem_runs() if with_runs else {}}


def write(data, path=None):
    os.makedirs(GEN, exist_ok=True)
    path = path or os.path.join(GEN, "extracted.json")
    with open(path, "w") as fh:
        json.dump(data, fh, indent=1, sort_keys=True)
    return path


def record_timing(run_dir):
    """Store a run's wall time and machine (from its pynr.log) in arch/timings.yaml."""
    import yaml

    sys.path.insert(0, ROOT)
    from pynr.machine import parse_machine_block

    with open(os.path.join(run_dir, "pynr.log")) as fh:
        log = fh.read()
    m = re.search(r"Done: iteration (\d+), t = ([0-9.e+-]+), wall time ([0-9.]+) s", log)
    if not m:
        raise SystemExit(f"{run_dir}/pynr.log has no 'Done:' line (run not finished?)")
    mach = parse_machine_block(log)
    if not mach:
        raise SystemExit(f"{run_dir}/pynr.log has no machine block (run made before pyNR recorded machines)")
    name = os.path.basename(os.path.normpath(run_dir))
    path = os.path.join(ROOT, "arch", "timings.yaml")
    data = {}
    if os.path.exists(path):
        with open(path) as fh:
            data = yaml.safe_load(fh) or {}
    g = re.search(r"shape=\(([^)]*)\)", log)
    data[name] = {"wall_time_s": float(m.group(3)), "iterations": int(m.group(1)),
                  "grid": " × ".join(g.group(1).split(", ")) if g else "",
                  "final_time": float(m.group(2)), "machine": mach.get("line"),
                  "aborted": "ABORT:" in log}
    with open(path, "w") as fh:
        yaml.safe_dump(data, fh, sort_keys=True, allow_unicode=True)
    print(f"recorded {name}: {m.group(3)} s on {mach.get('line')}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--print", action="store_true")
    ap.add_argument("--no-runs", action="store_true", help="skip building Simulations from par files")
    ap.add_argument("--record-timing", metavar="RUN_DIR", nargs="+")
    args = ap.parse_args()
    if args.record_timing:
        for d in args.record_timing:
            record_timing(d)
        return
    data = extract(with_runs=not args.no_runs)
    path = write(data)
    if args.print:
        for e in data["edges"]:
            print(f"{e['type']:9s} {e['from']:>16s} -> {e['to']:<16s} {e['file']}:{e['line']} {e['detail']}")
        for p, info in data["problems"].items():
            print(p, info["active_thorns"])
    print("wrote", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
