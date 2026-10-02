# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
"""Render diagrams and documentation snippets from arch/model.yaml (+ the extracted graph).

    python arch/render.py            # everything into docs/_generated/arch/
    python arch/render.py --readme   # also rewrite the README block between <!-- arch:begin/end -->

Called by docs/conf.py at every docs build. Outputs:

* ``view_<name>.md``          numbered Graphviz figure of a model view (HTML + PDF)
* ``component_<name>.dot``     neighbourhood graph of one component (used in the autodoc "Architecture" box)
* ``components.md``            component table (src, doc, notes, equations, derived "used by"/"called by")
* ``workflow_<problem>.md``    per-problem workflow: figure, schedule table, settings, outputs, how to run, cost
* ``problem_matrix.md``        problem x thorn matrix and the cost (machine) table
* ``static/arch_model.json``   data for the Cytoscape explorer (docs/_static/arch/explorer.html)
* README.md block              Mermaid physics view (GitHub renders it)
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract as X  # noqa: E402

ROOT = X.ROOT
GEN = X.GEN
GITHUB = "https://github.com/rahulkashyap-phy/pyNR/blob/main/"

KIND_COLOR = {"physics": "#dbeafe", "analysis": "#dcfce7", "io": "#fef3c7", "numerics": "#ede9fe",
              "kernel": "#f3e8ff", "flesh": "#e5e7eb", "infrastructure": "#f1f5f9", "external": "#ffffff"}
STAGE_COLOR = {"INITIAL": "#2563eb", "POSTINITIAL": "#0891b2", "EVOL": "#dc2626", "POSTSTEP": "#9333ea",
               "ANALYSIS": "#16a34a", "OUTPUT": "#ca8a04", "on demand": "#64748b"}
EDGE_STYLE = {"uses": 'color="#6b7280"', "requires": 'style=dotted, color="#374151"',
              "reads": 'style=dashed, color="#2563eb"', "registers": 'style=dashed, color="#ea580c"'}
PROBLEM_PAGE = {"schwarzschild_perturbed": "perturbed_bh"}
PROBLEM_NOTEBOOK = {"gauge_wave": "notebooks/01_gauge_wave.ipynb",
                    "schwarzschild_perturbed": "notebooks/02_perturbed_black_hole.ipynb"}
PROBLEM_FIGURE = {"gauge_wave": "fig-gauge-wave", "kerr_schild": "fig-kerr-constraints",
                  "schwarzschild_perturbed": "fig-perturbed-psi4"}


def _q(s):
    return '"' + str(s).replace('"', r"\"") + '"'


def _id(name):
    return re.sub(r"\W", "_", name)


# --------------------------------------------------------------------------- doc page lookup
def module_pages():
    """module dotted name -> docs page (html path) that autodocuments it."""
    pages = {}
    rx = re.compile(r"\.\.\s+auto(?:module|function|class)::\s+([\w.]+)")
    for f in glob.glob(os.path.join(ROOT, "docs", "**", "*.md"), recursive=True):
        if "_build" in f or "_generated" in f:
            continue
        with open(f) as fh:
            for m in rx.finditer(fh.read()):
                mod = m.group(1)
                pages.setdefault(mod, os.path.relpath(f, os.path.join(ROOT, "docs"))[:-3] + ".html")
    return pages


def component_url(name, c, pages):
    for s in c.get("src", []):
        if s.endswith(".py"):
            mod = s[:-3].replace("/", ".").removesuffix(".__init__")
            if mod in pages:
                return f"{pages[mod]}#module-{mod}"
    if c.get("doc"):
        return c["doc"].removeprefix("docs/")[:-3] + ".html"
    return None


# --------------------------------------------------------------------------- graphviz
def _node(name, c, pages, url_prefix="../"):
    kind = c.get("kind", "external")
    url = component_url(name, c, pages)
    shape = "box" if kind != "external" else "ellipse"
    attrs = [f"label={_q(name)}", f"shape={shape}", "style=\"rounded,filled\"",
             f"fillcolor={_q(KIND_COLOR.get(kind, '#fff'))}", f"tooltip={_q(c.get('summary', name))}"]
    if url:
        attrs.append(f"URL={_q(url_prefix + url)}")
        attrs.append('target="_top"')
    return f"  {_id(name)} [{', '.join(attrs)}];"


def _short(data):
    out = []
    for d in data:
        out.append(d.split("::")[1] if "::" in d else d)
    s = ", ".join(out)
    return s if len(s) < 34 else s[:31] + "…"


def view_dot(model, view, pages):
    comps = model["components"]
    v = model["views"][view]
    edges_wanted = v.get("edges", ["uses"])
    keep = set(comps)
    if "include_kinds" in v:
        keep = {n for n, c in comps.items() if c.get("kind") in v["include_kinds"]}
    if "exclude_kinds" in v:
        keep -= {n for n, c in comps.items() if c.get("kind") in v["exclude_kinds"]}
    keep -= set(v.get("hide", []))
    if "flows" in edges_wanted:
        for f in model.get("flows", []):
            if f["from"] in keep or f["to"] in keep:
                keep |= {f["from"], f["to"]}
    hidden_to = set(v.get("hide_edges_to", []))
    lines = ["digraph arch {", '  rankdir=LR; nodesep=0.25; ranksep=0.55;',
             '  node [fontname="Helvetica", fontsize=10]; edge [fontname="Helvetica", fontsize=8, arrowsize=0.6];']
    layers = {}
    for n in sorted(keep):
        layers.setdefault(comps[n].get("layer", "external"), []).append(n)
    for layer, names in layers.items():
        lines.append(f'  subgraph cluster_{_id(layer)} {{ label={_q(layer)}; color="#d1d5db"; fontcolor="#6b7280"; fontsize=9;')
        lines += ["  " + _node(n, comps[n], pages) for n in names]
        lines.append("  }")
    for n in sorted(keep):
        c = comps[n]
        for t in ("uses", "requires", "reads"):
            if t in edges_wanted:
                for b in c.get(t, []):
                    if b in keep and b != n and b not in hidden_to:
                        lab = "" if t == "uses" else f", label={_q(t)}"
                        lines.append(f"  {_id(n)} -> {_id(b)} [{EDGE_STYLE[t]}{lab}];")
        if "registers" in edges_wanted:
            for r in c.get("registers", []):
                if r["into"] in keep and r["into"] != n and r["into"] != "flesh":
                    lines.append(f"  {_id(r['into'])} -> {_id(n)} [{EDGE_STYLE['registers']}, "
                                 f"label={_q('calls ' + ', '.join(r['functions']))}];")
    if "flows" in edges_wanted:
        for f in model.get("flows", []):
            if f["from"] in keep and f["to"] in keep:
                col = STAGE_COLOR.get(f.get("stage"), "#111")
                lines.append(f"  {_id(f['from'])} -> {_id(f['to'])} [color={_q(col)}, penwidth=1.6, "
                             f"fontcolor={_q(col)}, label={_q(_short(f.get('data', [])) + ' [' + f.get('stage', '') + ']')}];")
    lines.append("}")
    return "\n".join(lines)


def legend_md():
    stages = " · ".join(f'<span style="color:{c}">■ {s}</span>' for s, c in STAGE_COLOR.items())
    return ("**Legend.** Boxes are components, coloured by kind; clusters are layers. Grey solid arrow: **uses**, "
            "where the tail imports and calls the head. Dotted: **requires** (activation). Blue dashed: **reads** "
            "(the tail reads the head's state). Orange dashed: a **callback**, where the tail calls functions the "
            "head registered. Thick coloured arrow: **data flow**, coloured by schedule bin. Click a box to open "
            "its documentation.\n\n" + stages + "\n")


def write_views(model, pages):
    for view, v in model["views"].items():
        dot = view_dot(model, view, pages)
        with open(os.path.join(GEN, f"view_{view}.dot"), "w") as fh:
            fh.write(dot)
        md = [f"```{{graphviz}} _generated/arch/view_{view}.dot", f":caption: {v.get('title', view)}.",
              f":name: fig-arch-{view}", ":align: center", "```", ""]
        with open(os.path.join(GEN, f"view_{view}.md"), "w") as fh:
            fh.write("\n".join(md))


# --------------------------------------------------------------------------- derived relations
def derived(model):
    """used_by / required_by / read_by / calls_back per component."""
    rel = {n: {"used_by": set(), "required_by": set(), "read_by": set(), "calls_back": set(),
               "flows_in": [], "flows_out": []} for n in model["components"]}
    for n, c in model["components"].items():
        for b in c.get("uses", []):
            if b in rel:
                rel[b]["used_by"].add(n)
        for b in c.get("requires", []):
            if b in rel:
                rel[b]["required_by"].add(n)
        for b in c.get("reads", []):
            if b in rel:
                rel[b]["read_by"].add(n)
        for r in c.get("registers", []):
            if r["into"] in rel:
                rel[r["into"]]["calls_back"].add(f"{n}.{'/'.join(r['functions'])} [{r.get('stage')}]")
    for f in model.get("flows", []):
        if f["from"] in rel:
            rel[f["from"]]["flows_out"].append(f)
        if f["to"] in rel:
            rel[f["to"]]["flows_in"].append(f)
    return rel


def component_dot(model, name, pages):
    comps, rel = model["components"], derived(model)
    c = comps[name]
    nodes = {name}
    edges = []
    for t in ("uses", "requires", "reads"):
        for b in c.get(t, []):
            if comps.get(b, {}).get("layer") == "external":
                continue
            nodes.add(b)
            lab = "" if t == "uses" else f", label={_q(t)}"
            edges.append(f"  {_id(name)} -> {_id(b)} [{EDGE_STYLE[t]}{lab}];")
    for a in sorted(rel[name]["used_by"] | rel[name]["required_by"] | rel[name]["read_by"]):
        if a == "registry":
            continue
        nodes.add(a)
        t = "uses" if a in rel[name]["used_by"] else ("requires" if a in rel[name]["required_by"] else "reads")
        lab = "" if t == "uses" else f", label={_q(t)}"
        edges.append(f"  {_id(a)} -> {_id(name)} [{EDGE_STYLE[t]}{lab}];")
    for r in c.get("registers", []):
        if r["into"] != "flesh":
            nodes.add(r["into"])
            edges.append(f"  {_id(r['into'])} -> {_id(name)} [{EDGE_STYLE['registers']}, "
                         f"label={_q('calls ' + ', '.join(r['functions']) + ' [' + r.get('stage', '') + ']')}];")
    for f in rel[name]["flows_in"] + rel[name]["flows_out"]:
        nodes |= {f["from"], f["to"]}
        col = STAGE_COLOR.get(f.get("stage"), "#111")
        edges.append(f"  {_id(f['from'])} -> {_id(f['to'])} [color={_q(col)}, penwidth=1.4, fontcolor={_q(col)}, "
                     f"label={_q(_short(f.get('data', [])) + ' [' + f.get('stage', '') + ']')}];")
    lines = ["digraph c {", "  rankdir=LR; nodesep=0.2; ranksep=0.4;",
             '  node [fontname="Helvetica", fontsize=9]; edge [fontname="Helvetica", fontsize=7, arrowsize=0.5];']
    for n in sorted(nodes):
        line = _node(n, comps.get(n, {"kind": "external"}), pages, url_prefix="../")
        if n == name:
            line = line.replace("];", ', penwidth=2.2, color="#b91c1c"];')
        lines.append(line)
    lines += sorted(set(edges)) + ["}"]
    return "\n".join(lines)


def write_component_graphs(model, pages):
    for name, c in model["components"].items():
        if c.get("layer") == "external":
            continue
        with open(os.path.join(GEN, f"component_{name}.dot"), "w") as fh:
            fh.write(component_dot(model, name, pages))


def components_table(model, pages):
    rel = derived(model)
    rows = ["```{table} Components of the architecture model (arch/model.yaml). \"Used by\" and \"called back by\" "
            "are derived from the edges written on the initiating component.", ":name: tab-arch-components", "",
            "| component | kind / layer | summary | source | docs, notes, equations | uses | used by | called back by |",
            "|---|---|---|---|---|---|---|---|"]
    for n, c in model["components"].items():
        if c.get("layer") == "external":
            continue
        src = ", ".join(f"[`{s}`]({GITHUB}{s})" for s in c.get("src", []))
        links = []
        if c.get("doc"):
            links.append(f"`{c['doc'][5:]}`")
        if c.get("notes"):
            links.append(f"notes: `{c['notes'][5:]}`")
        eqs = ", ".join("{eq}`" + e + "`" for e in c.get("equations", []))
        if eqs:
            links.append("Eq. " + eqs)
        rows.append(f"| **{n}** | {c.get('kind')} / {c.get('layer')} | {c.get('summary', '')} | {src} | "
                    f"{'; '.join(links)} | {', '.join(c.get('uses', []))} | "
                    f"{', '.join(sorted(rel[n]['used_by']))} | {'; '.join(sorted(rel[n]['calls_back']))} |")
    with open(os.path.join(GEN, "components.md"), "w") as fh:
        fh.write("\n".join(rows + ["```", ""]))


# --------------------------------------------------------------------------- per-problem workflows
def _comp_of(model):
    return {t: n for n, c in model["components"].items() for t in c.get("thorns", [])}


def timings():
    """problem -> {wall_time_s, machine, aborted} from arch/timings.yaml."""
    import yaml

    path = os.path.join(ROOT, "arch", "timings.yaml")
    if not os.path.exists(path):
        return {}
    with open(path) as fh:
        return yaml.safe_load(fh) or {}


def _fmt_time(s):
    return f"{s:.0f} s" if s < 90 else f"{s / 60:.1f} min"


def workflow_dot(model, name, prob, pages):
    comps, t2c = model["components"], _comp_of(model)
    active = {t2c.get(t) for t in prob["active_thorns"]} - {None, "CoreThorns"}
    bins = ["INITIAL", "POSTINITIAL", "EVOL", "POSTSTEP", "ANALYSIS", "on demand", "OUTPUT"]
    # each component sits in its *primary* bin: EVOL for the time-stepping engine and anything that plugs into it,
    # then INITIAL, ANALYSIS, OUTPUT; housekeeping bins (POSTINITIAL, POSTSTEP) only if nothing else applies
    priority = ["EVOL", "INITIAL", "ANALYSIS", "OUTPUT", "POSTINITIAL", "POSTSTEP"]
    routines = {}
    for b in bins:
        for item in prob["schedule"].get(b, []):
            th, fn = item.split("::")
            c = t2c.get(th)
            if c in active:
                routines.setdefault(c, []).append((b, th, fn))
    place = {}
    for c in active:
        regs = comps[c].get("registers", [])
        mine = {b for b, _, _ in routines.get(c, [])}
        if any(r["into"] == "MoL" for r in regs):
            mine.add("EVOL")
        place[c] = next((b for b in priority if b in mine), "on demand")
    lines = ["digraph w {", "  rankdir=LR; compound=true; nodesep=0.25; ranksep=0.5;",
             '  node [fontname="Helvetica", fontsize=9]; edge [fontname="Helvetica", fontsize=7, arrowsize=0.55];',
             f'  par [label={_q("par/" + name + ".par")}, shape=note, style=filled, fillcolor="#fff7ed"];']
    for b in bins:
        members = sorted(c for c, pb in place.items() if pb == b)
        if not members:
            continue
        col = STAGE_COLOR.get(b, "#111")
        lines.append(f'  subgraph cluster_{_id(b)} {{ label={_q(b)}; color={_q(col)}; fontcolor={_q(col)}; fontsize=9;')
        for c in members:
            here = sorted({fn for rb, _, fn in routines.get(c, []) if rb == b})
            thorns_here = sorted({th for rb, th, _ in routines.get(c, []) if rb == b})
            other = [f"{fn} @{rb}" for rb, _, fn in routines.get(c, []) if rb != b]
            lab = c
            if here:
                lab += "\\n" + ", ".join(here) + (f" ({', '.join(thorns_here)})" if len(thorns_here) > 1 else "")
            if other:
                lab += "\\n(" + ", ".join(dict.fromkeys(other)) + ")"
            node = _node(c, comps[c], pages).replace(f"label={_q(c)}", f'label="{lab}"')
            lines.append("  " + node)
        lines.append("  }")
    first = [c for c, b in place.items() if b == "INITIAL"]
    for c in sorted(first):
        lines.append(f"  par -> {_id(c)} [color=\"#9ca3af\"];")
    for f in model.get("flows", []):
        if f["from"] in active and f["to"] in active:
            col = STAGE_COLOR.get(f.get("stage"), "#111")
            lines.append(f"  {_id(f['from'])} -> {_id(f['to'])} [color={_q(col)}, penwidth=1.4, fontcolor={_q(col)}, "
                         f"label={_q(_short(f.get('data', [])))}];")
    for c in sorted(active):
        for r in comps[c].get("registers", []):
            if r["into"] in active and r["into"] != c:
                lines.append(f"  {_id(r['into'])} -> {_id(c)} [{EDGE_STYLE['registers']}, "
                             f"label={_q('calls ' + ', '.join(r['functions']))}];")
    outs = [o for o in prob["outputs"] if not o.endswith(".par") and o != "pynr.log"]
    out_label = "simulations/" + name + "/\\n" + "\\n".join(outs[:6]) + ("\\n…" if len(outs) > 6 else "")
    lines.append(f'  files [label="{out_label}", shape=folder, style=filled, fillcolor="#fefce8", fontsize=8];')
    for c in ("IO", "Multipole"):
        if c in active:
            lines.append(f'  {_id(c)} -> files [color="#ca8a04"];')
    lines.append('  analysis [label="kuibit SimDir / notebook\\n→ plots", shape=box, style="rounded,filled", '
                 'fillcolor="#ecfeff"];')
    lines.append('  files -> analysis [color="#0891b2"];')
    lines.append("}")
    return "\n".join(lines)


def workflow_md(model, name, prob, pages, tim):
    page = PROBLEM_PAGE.get(name, name)
    dot = workflow_dot(model, name, prob, pages)
    with open(os.path.join(GEN, f"workflow_{name}.dot"), "w") as fh:
        fh.write(dot)
    md = [f"(sec-workflow-{name.replace('_', '-')})=", "## Workflow", "",
          "Generated from the parameter file and the architecture model at every docs build, so it always shows "
          "what the code actually runs.", "",
          f"```{{graphviz}} ../_generated/arch/workflow_{name}.dot",
          f":caption: Workflow of `par/{name}.par`. Clusters are schedule bins in execution order; thick arrows are "
          "data flows (grid functions), orange dashed arrows are callbacks (who calls whom); the output folder and "
          "its analysis close the chain.",
          f":name: fig-workflow-{name.replace('_', '-')}", ":align: center", "```", "",
          "```{table} Schedule: routines per bin, in execution order (the equivalent of the Einstein Toolkit's "
          "schedule printout).", f":name: tab-schedule-{name.replace('_', '-')}", "",
          "| bin | routines (Thorn::routine) |", "|---|---|"]
    for b, items in prob["schedule"].items():
        md.append(f"| {b} | " + " → ".join(f"`{i}`" for i in items) + " |")
    md += ["```", "",
           "```{table} Key settings and output files of this problem.", f":name: tab-settings-run-{name.replace('_', '-')}", "",
           "| setting | value |", "|---|---|"]
    md.append(f"| active thorns | {', '.join(t for t in prob['active_thorns'] if t not in ('Cactus', 'CoordBase', 'Driver', 'Time', 'IO'))} |")
    for k, v in prob["settings"].items():
        md.append(f"| `{k}` | `{v}` |")
    md.append(f"| output files | {', '.join('`' + o + '`' for o in prob['outputs'])} |")
    t = tim.get(name)
    if t:
        cost = f"{_fmt_time(t['wall_time_s'])}{' (aborted on blow-up)' if t.get('aborted') else ''} on {t['machine']}"
        md.append(f"| cost (machine) | {cost} |")
    md += ["```", "", "**Run and analyse it**", "",
           "```bash", f"pynr run par/{name}.par          # → simulations/{name}/", "```", "",
           "```python", "from kuibit.simdir import SimDir", "from pynr.paths import run_dir",
           f'sd = SimDir(run_dir("{name}"))', "```", ""]
    extras = []
    if name in PROBLEM_NOTEBOOK:
        extras.append(f"notebook `{PROBLEM_NOTEBOOK[name]}` (Settings cell: `RUN_SIMULATIONS = False` to only plot)")
    if name in PROBLEM_FIGURE:
        extras.append(f"figure {{numref}}`{PROBLEM_FIGURE[name]}` and its dataset "
                      "({ref}`sec-figure-data`)")
    if extras:
        md += ["See also: " + "; ".join(extras) + ".", ""]
    with open(os.path.join(GEN, f"workflow_{name}.md"), "w") as fh:
        fh.write("\n".join(md))
    return page


def problem_matrix(model, problems, tim):
    t2c = _comp_of(model)
    thorns = [t for t in ("ADMBase", "Exact", "Perturb", "ADMEvolve", "MoL", "Dissipation", "ADMConstraints",
                          "WeylScal4", "Multipole", "IOHDF5", "IOScalar", "IOBasic")]
    md = ["```{table} Which thorns each problem activates (from its parameter file).", ":name: tab-problem-thorns", "",
          "| problem | " + " | ".join(thorns) + " |", "|---|" + "---|" * len(thorns)]
    for name, p in problems.items():
        page = PROBLEM_PAGE.get(name, name)
        md.append(f"| [{name}]({page}.md) | " + " | ".join("✓" if t in p["active_thorns"] else "" for t in thorns) + " |")
    md += ["```", "", "```{table} Cost of each problem and the machine it was measured on.",
           ":name: tab-problem-cost", "", "| problem | grid (incl. ghosts) | cost | machine |", "|---|---|---|---|"]
    for name, p in problems.items():
        t = tim.get(name)
        page = PROBLEM_PAGE.get(name, name)
        if t:
            cost = _fmt_time(t["wall_time_s"]) + (" (aborts)" if t.get("aborted") else "")
            md.append(f"| [{name}]({page}.md) | {t.get('grid', '')} | {cost} | {t['machine']} |")
        else:
            md.append(f"| [{name}]({page}.md) | | not recorded | — |")
    md += ["```", "", "Costs and machines are read from each run's `pynr.log` and stored in `arch/timings.yaml` "
           "(`python arch/extract.py --record-timing simulations/<problem>`). Cost scales with grid points × time steps. A 4-core Codespace is roughly 2.5–3× slower "
           "than the 12-core reference machine.", ""]
    _ = t2c
    with open(os.path.join(GEN, "problem_matrix.md"), "w") as fh:
        fh.write("\n".join(md))


# --------------------------------------------------------------------------- explorer + README
def explorer_json(model, ext, pages):
    comps, rel = model["components"], derived(model)
    nodes, edges = [], []
    for layer in sorted({c.get("layer", "external") for c in comps.values()}):
        nodes.append({"data": {"id": "layer:" + layer, "label": layer, "kind": "layer"}})
    for n, c in comps.items():
        url = component_url(n, c, pages)
        nodes.append({"data": {
            "id": n, "label": n, "kind": c.get("kind", "external"), "parent": "layer:" + c.get("layer", "external"),
            "summary": c.get("summary", ""), "doc": ("../../" + url) if url else None,
            "src": [GITHUB + s for s in c.get("src", [])], "notes": c.get("notes"),
            "equations": c.get("equations", []), "used_by": sorted(rel.get(n, {}).get("used_by", []))}})
    i = 0
    for n, c in comps.items():
        for t in ("uses", "requires", "reads"):
            for b in c.get(t, []):
                i += 1
                edges.append({"data": {"id": f"e{i}", "source": n, "target": b, "type": t}})
        for r in c.get("registers", []):
            if r["into"] in comps and r["into"] != n:
                i += 1
                edges.append({"data": {"id": f"e{i}", "source": r["into"], "target": n, "type": "callback",
                                       "label": ", ".join(r["functions"]) + f" [{r.get('stage')}]"}})
    for f in model.get("flows", []):
        i += 1
        edges.append({"data": {"id": f"e{i}", "source": f["from"], "target": f["to"], "type": "flow",
                               "stage": f.get("stage"), "label": _short(f.get("data", [])),
                               "color": STAGE_COLOR.get(f.get("stage"), "#111")}})
    out = {"elements": {"nodes": nodes, "edges": edges}, "stage_colors": STAGE_COLOR,
           "kind_colors": KIND_COLOR, "views": model["views"]}
    os.makedirs(os.path.join(GEN, "static"), exist_ok=True)
    with open(os.path.join(GEN, "static", "arch_model.json"), "w") as fh:
        json.dump(out, fh, indent=1)


def readme_block(model=None):
    """Mermaid physics view for the README (deterministic text)."""
    model = model or X.load_model()
    comps = model["components"]
    keep = [n for n, c in comps.items() if c.get("kind") in ("physics", "analysis", "io", "numerics")
            and c.get("layer") == "thorns"]
    lines = ["```mermaid", "flowchart LR"]
    for n in keep:
        lines.append(f"  {_id(n)}[{n}]")
    lines.append("  kuibit([kuibit])")
    for f in model.get("flows", []):
        a, b = f["from"], f["to"]
        if (a in keep or a == "kuibit") and (b in keep or b == "kuibit"):
            lines.append(f"  {_id(a)} -->|{f.get('stage')}| {_id(b)}")
    for n in keep:
        for r in comps[n].get("registers", []):
            if r["into"] in keep:
                lines.append(f"  {_id(r['into'])} -. calls {'/'.join(r['functions'])} .-> {_id(n)}")
    lines += ["```", "",
              "*Thorns and the data flow between them, by schedule bin. Dotted arrows are callbacks. Generated "
              "from `arch/model.yaml`; the full interactive model is on the Architecture page of the docs.*", ""]
    return "\n".join(lines)


def update_readme():
    path = os.path.join(ROOT, "README.md")
    with open(path) as fh:
        text = fh.read()
    block = "<!-- arch:begin -->\n" + readme_block() + "<!-- arch:end -->"
    if "<!-- arch:begin -->" in text:
        text = re.sub(r"<!-- arch:begin -->\n.*?<!-- arch:end -->", lambda m: block, text, flags=re.S)
    else:
        text = text.replace("## Layout", "## Architecture\n\n" + block + "\n\n## Layout", 1)
    with open(path, "w") as fh:
        fh.write(text)


# --------------------------------------------------------------------------- entry
def render_all(log=print, with_runs=True):
    os.makedirs(GEN, exist_ok=True)
    model = X.load_model()
    ext_path = os.path.join(GEN, "extracted.json")
    ext = X.extract(model, with_runs=with_runs)
    X.write(ext, ext_path)
    pages = module_pages()
    write_views(model, pages)
    write_component_graphs(model, pages)
    components_table(model, pages)
    tim = timings()
    for name, prob in ext["problems"].items():
        workflow_md(model, name, prob, pages, tim)
    problem_matrix(model, ext["problems"], tim)
    explorer_json(model, ext, pages)
    log(f"[arch] rendered {len(model['views'])} views, {len(ext['problems'])} workflows into docs/_generated/arch")
    return model, ext


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--readme", action="store_true", help="rewrite the README architecture block")
    args = ap.parse_args()
    render_all()
    if args.readme:
        update_readme()
        print("README.md architecture block updated")


if __name__ == "__main__":
    main()
