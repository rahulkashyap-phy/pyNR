# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
"""Sphinx extension: the documentation dependency graph.

After all pages are read, it collects from the build environment:

* ``contains``  toctree parent page -> child page
* ``cites``     page -> page that defines a referenced label ({numref}, {ref}, {eq}, :mod:)
* ``documents`` page -> architecture component whose module the page autodocuments

It writes ``docs/_generated/docgraph.json`` and renders a Graphviz figure wherever the ``docgraph`` directive is
used. The figure is built at write time, so it always reflects the current build (HTML and LaTeX).
"""

from __future__ import annotations

import json
import os

from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.ext.graphviz import graphviz

PART_COLOR = {"theory": "#dbeafe", "problems": "#dcfce7", "reference": "#f3f4f6", "roadmap": "#fef3c7",
              "devlog": "#fde68a", "notes": "#ede9fe", "rkdev": "#fcd9b6", "": "#ffffff"}


class docgraph_node(nodes.General, nodes.Element):
    pass


class DocGraph(Directive):
    has_content = False
    option_spec = {"caption": str, "name": str}

    def run(self):
        node = docgraph_node()
        node["caption"] = self.options.get("caption", "")
        node["name"] = self.options.get("name", "")
        return [node]


def _module_component():
    try:
        import sys

        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "arch"))
        import extract

        model = extract.load_model()
        cmap = extract.component_map(model)
        return {f[:-3].replace("/", ".").removesuffix(".__init__"): c for f, c in cmap.items()}
    except Exception:  # noqa: BLE001
        return {}


def collect(app, env):
    std = env.get_domain("std")
    math = env.get_domain("math")
    py = env.get_domain("py")
    label_doc = {lab: v[0] for lab, v in std.labels.items()}
    label_doc.update({lab: v[0] for lab, v in std.anonlabels.items()})
    eq_doc = {lab: v[0] for lab, v in math.equations.items()}
    mod_doc = {m: v.docname for m, v in py.modules.items()}
    mod_comp = _module_component()
    edges, docs = set(), set(env.found_docs)
    for parent, children in env.toctree_includes.items():
        for ch in children:
            edges.add((parent, ch, "contains"))
    for doc in sorted(docs):
        try:
            tree = env.get_doctree(doc)
        except Exception:  # noqa: BLE001
            continue
        for ref in tree.findall(lambda n: n.tagname in ("pending_xref", "number_reference")):
            typ, target = ref.get("reftype"), (ref.get("reftarget") or "").lower()
            dst = None
            if typ in ("ref", "numref"):
                dst = label_doc.get(target)
            elif typ == "eq":
                dst = eq_doc.get(ref.get("reftarget"))
            elif typ == "mod":
                dst = mod_doc.get(ref.get("reftarget"))
            if dst and dst != doc:
                edges.add((doc, dst, "cites"))
    for mod, doc in mod_doc.items():
        comp = mod_comp.get(mod)
        if comp:
            edges.add((doc, "component:" + comp, "documents"))
    env.pynr_docgraph = {"pages": sorted(docs), "edges": sorted(edges)}
    out = os.path.join(app.srcdir, "_generated")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "docgraph.json"), "w") as fh:
        json.dump({"pages": sorted(docs), "edges": [{"from": a, "to": b, "type": t} for a, b, t in sorted(edges)]},
                  fh, indent=1)


def _dot(data, with_components=True):
    pages = [p for p in data["pages"] if not p.startswith("_")]
    parts = {}
    for p in pages:
        parts.setdefault(p.split("/")[0] if "/" in p else "", []).append(p)
    q = lambda s: '"' + s.replace('"', r"\"") + '"'  # noqa: E731
    lines = ["digraph docs {", "  rankdir=LR; nodesep=0.12; ranksep=0.9; concentrate=true;",
             '  node [fontname="Helvetica", fontsize=8, shape=box, style="rounded,filled"];',
             '  edge [arrowsize=0.4];']
    for part, ps in sorted(parts.items()):
        lines.append(f"  subgraph cluster_{part or 'top'} {{ label={q(part or 'top level')}; color=\"#d1d5db\"; fontsize=9;")
        for p in sorted(ps):
            lines.append(f"    {q(p)} [label={q(p.split('/')[-1])}, fillcolor={q(PART_COLOR.get(part, '#fff'))}];")
        lines.append("  }")
    comps = sorted({b for a, b, t in data["edges"] if t == "documents"})
    if with_components and comps:
        lines.append('  subgraph cluster_components { label="code components (arch/model.yaml)"; color="#fca5a5"; fontsize=9;')
        for c in comps:
            lines.append(f'    {q(c)} [label={q(c.split(":", 1)[1])}, shape=ellipse, fillcolor="#fee2e2"];')
        lines.append("  }")
    style = {"contains": 'color="#9ca3af"', "cites": 'color="#2563eb", style=dashed',
             "documents": 'color="#dc2626"'}
    for a, b, t in data["edges"]:
        if a in pages and (b in pages or (with_components and b.startswith("component:"))):
            lines.append(f"  {q(a)} -> {q(b)} [{style[t]}];")
    lines.append("}")
    return "\n".join(lines)


def render(app, doctree, docname):
    data = getattr(app.env, "pynr_docgraph", None)
    for node in list(doctree.findall(docgraph_node)):
        if not data:
            node.replace_self(nodes.paragraph(text="(documentation graph not available in this build)"))
            continue
        g = graphviz()
        g["code"] = _dot(data)
        g["options"] = {}
        g["align"] = "center"
        fig = nodes.figure("", g)
        fig["align"] = "center"
        if node["caption"]:
            fig += nodes.caption("", node["caption"])
        if node["name"]:
            fig["ids"].append(node["name"])
            app.env.get_domain("std").labels  # noqa: B018  (label registered via the page's (label)= target)
        node.replace_self(fig)


def setup(app):
    app.add_node(docgraph_node)
    app.add_directive("docgraph", DocGraph)
    app.connect("env-check-consistency", collect)
    app.connect("doctree-resolved", render)
    return {"version": "0.1", "parallel_read_safe": True, "parallel_write_safe": True}
