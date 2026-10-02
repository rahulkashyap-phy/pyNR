# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
"""Sphinx configuration for the pyNR documentation (HTML site and PDF lecture notes).

HTML:  sphinx-build -b html docs docs/_build/html          (root document: index)
PDF:   make -C docs latexpdf                               (root document: lecture_notes)
"""

import os
import re as _re
import shutil
import subprocess
import sys

DOCS = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.dirname(DOCS)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(DOCS, "_ext"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "arch"))

import pynr  # noqa: E402

BUILDING_LATEX = any(a in ("latex", "latexpdf") for a in sys.argv) or os.environ.get("PYNR_DOCS_LATEX") == "1"
HAVE_DOT = shutil.which("dot") is not None


# --- branch, commit and the personal-branch banner ------------------------------------------
def _git(*args):
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


BRANCH = (os.environ.get("PYNR_DOCS_BRANCH") or os.environ.get("GITHUB_REF_NAME")
          or os.environ.get("CI_COMMIT_REF_NAME") or _git("rev-parse", "--abbrev-ref", "HEAD") or "unknown")
COMMIT = _git("describe", "--always", "--dirty") or "unknown"
# The single place to change the banner's colour or text (decision D-031).
BRANCH_BANNERS = {
    "rkdev": {"bg": "#b45309", "fg": "#ffffff",
              "text": "⚠ Personal development branch <b>rkdev</b> of Rahul Kashyap. Work in progress, "
                      "not the released documentation."},
    "_other": {"bg": "#b45309", "fg": "#ffffff",
               "text": "⚠ Development branch <b>{branch}</b>. Not the released documentation."},
}
BANNER = None if BRANCH == "main" else BRANCH_BANNERS.get(BRANCH, BRANCH_BANNERS["_other"])

# --- generated content: figures, architecture, API index -----------------------------------
import make_doc_figures  # noqa: E402

make_doc_figures.render_all()

try:
    import render as _arch_render  # arch/render.py

    _arch_render.render_all()
    import check_drift as _drift

    _drift.run(BRANCH if BRANCH == "main" else None)  # writes the "Architecture health" report
except Exception as _err:  # noqa: BLE001 -- never break the docs build; the report says why
    os.makedirs(os.path.join(DOCS, "_generated", "arch"), exist_ok=True)
    with open(os.path.join(DOCS, "_generated", "arch", "drift_report.md"), "w") as _fh:
        _fh.write(f":::{{warning}}\nArchitecture rendering failed in this build: `{_err}`\n:::\n")
    print("[arch] rendering failed:", _err)

if not HAVE_DOT:  # Graphviz missing: replace figures by a note (the build still succeeds)
    for _f in __import__("glob").glob(os.path.join(DOCS, "_generated", "arch", "*.md")):
        with open(_f) as _fh:
            _t = _fh.read()
        _t = _re.sub(r"```\{graphviz\}.*?```", ":::{note}\nDiagram not rendered: Graphviz (`dot`) is not "
                     "installed in this build.\n:::", _t, flags=_re.S)
        with open(_f, "w") as _fh:
            _fh.write(_t)


def _write_api_index():
    """Autosummary tables of every public class/function, one per module (no duplicate pages)."""
    import importlib
    import inspect
    import pkgutil

    out = []
    mods = ["pynr"] + sorted(m.name for m in pkgutil.walk_packages(pynr.__path__, "pynr.")
                             if not m.name.endswith("__main__"))
    for name in mods:
        try:
            mod = importlib.import_module(name)
        except Exception:  # noqa: BLE001
            continue
        members = []
        for attr, obj in vars(mod).items():
            if attr.startswith("_"):
                continue
            home = getattr(getattr(obj, "py_func", obj), "__module__", None)
            if home == name and (inspect.isclass(obj) or callable(obj)):
                members.append(f"{name}.{attr}")
        summary = (mod.__doc__ or "").strip().splitlines()[0] if mod.__doc__ else ""
        out += [f"## `{name}`", "", summary, ""]
        if members:
            out += ["```{eval-rst}", ".. autosummary::", "   :nosignatures:", ""]
            out += [f"   {m}" for m in members] + ["```", ""]
    os.makedirs(os.path.join(DOCS, "_generated"), exist_ok=True)
    with open(os.path.join(DOCS, "_generated", "api_index.md"), "w") as fh:
        fh.write("\n".join(out))


_write_api_index()

# --- PDF lecture notes on the HTML site ---------------------------------------------------------
# `make -C docs all` builds the PDF first and stages it in _generated/pdf/; the HTML build then serves it
# at the site root and the front page links it. Without a built PDF the front page says how to make one.
PDF_NAME = "pyNR-lecture-notes.pdf"
PDF_STAGED = os.path.join(DOCS, "_generated", "pdf", PDF_NAME)


def _write_pdf_link():
    os.makedirs(os.path.join(DOCS, "_generated"), exist_ok=True)
    if os.path.exists(PDF_STAGED):
        import datetime

        size = os.path.getsize(PDF_STAGED) / 2**20
        when = datetime.datetime.fromtimestamp(os.path.getmtime(PDF_STAGED)).strftime("%Y-%m-%d %H:%M")
        text = (":::{only} html\n:::{admonition} PDF lecture notes\n:class: tip\n"
                f'<a href="{PDF_NAME}"><b>Download the lecture notes as PDF</b></a> '
                f"({size:.1f} MB, built {when} from {BRANCH}@{COMMIT}). Typeset with LaTeX from the same "
                "sources as this site: theory, problems, notes, architecture, API.\n:::\n:::\n")
    else:
        text = (":::{only} html\n:::{note}\nThe PDF lecture notes are built with LaTeX from the same sources: "
                "`make -C docs all` (PDF + this site) or `make -C docs latexpdf`.\n:::\n:::\n")
    with open(os.path.join(DOCS, "_generated", "pdf_link.md"), "w") as fh:
        fh.write(text)


if not BUILDING_LATEX:
    _write_pdf_link()

# --- project ---------------------------------------------------------------------------------
project = "pyNR"
author = "Rahul Kashyap"
copyright = ("2026, Rahul Kashyap (Indian Institute of Technology Bombay). Apache-2.0; attribution required, "
             f"see NOTICE · built from {BRANCH}@{COMMIT}")
version = release = pynr.__version__

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.graphviz",
    "sphinx_copybutton",
    "docgraph",
]
try:
    import sphinxcontrib.mermaid  # noqa: F401

    extensions.append("sphinxcontrib.mermaid")
except ImportError:
    pass

myst_enable_extensions = ["dollarmath", "amsmath", "colon_fence", "deflist", "attrs_inline"]
myst_heading_anchors = 3
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
exclude_patterns = ["_build", "README.md", "**/README.md", "data", "figures", "_generated"]
if BUILDING_LATEX:  # the PDF is rooted at lecture_notes; the HTML site at index (no page in two toctrees)
    root_doc = "lecture_notes"
    exclude_patterns += ["index.md", "installation.md", "running-online.md", "utilities.md",
                         "theory/index.md", "reference/index.md", "rkdev/**"]
else:
    root_doc = "index"
    exclude_patterns += ["lecture_notes.md"]
suppress_warnings = ["toc.glob", "toc.empty_glob"]  # `plans/*` and `rkdev/*` are empty on main

autodoc_member_order = "bysource"
autodoc_default_options = {"members": True, "undoc-members": False}
autosummary_generate = False  # the API index uses tables only (see _write_api_index)

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "scipy": ("https://docs.scipy.org/doc/scipy", None),
    "kuibit": ("https://sbozzolo.github.io/kuibit", None),
}

# Numbered equations, tables and figures, referenced by number:
#   Markdown:   $$ ... $$ (eq-label)   {eq}`eq-label`   {numref}`tab-label`
#   docstrings: $$ ... $$ (eq-label)   :eq:`eq-label`   :numref:`tab-label`
numfig = True
math_numfig = True
numfig_secnum_depth = 0
numfig_format = {"figure": "Fig. %s", "table": "Table %s", "code-block": "Listing %s"}
math_eqref_format = "({number})"  # write "Eq. {eq}`label`" in the text

graphviz_output_format = "svg"
graphviz_dot_args = ["-Gfontname=Helvetica"]

# --- HTML --------------------------------------------------------------------------------------
html_theme = "furo"
html_title = f"pyNR {version}" + (f" ({BRANCH})" if BANNER else "")
html_static_path = ["_static", "_generated/arch/static"]
html_extra_path = ["_generated/pdf"] if os.path.exists(os.path.join(DOCS, "_generated", "pdf")) else []
html_css_files = ["banner.css"]
html_theme_options = {
    "source_repository": "https://github.com/rahulkashyap-phy/pyNR",
    "source_branch": "main",
    "source_directory": "docs/",
}
if BANNER:
    html_theme_options["announcement"] = (
        f'<div class="pynr-branch-banner" style="--pynr-banner-bg:{BANNER["bg"]};'
        f'--pynr-banner-fg:{BANNER["fg"]}">{BANNER["text"].format(branch=BRANCH)} '
        f'<span class="pynr-branch-commit">({BRANCH}@{COMMIT})</span></div>')

# --- LaTeX / PDF lecture notes -------------------------------------------------------------------
latex_engine = "lualatex"
latex_documents = [("lecture_notes", "pyNR-lecture-notes.tex", "pyNR: lecture notes",
                    "Rahul Kashyap\\\\Indian Institute of Technology Bombay", "manual")]
latex_toplevel_sectioning = "part"
_watermark = ""
if BANNER:
    _watermark = (r"\definecolor{pynrwatermark}{rgb}{0.98,0.85,0.70}"
                  r"\usepackage[text={" + BRANCH + r" — personal branch}, scale=0.45, color=pynrwatermark]"
                  r"{draftwatermark}")
latex_elements = {
    "papersize": "a4paper",
    "pointsize": "11pt",
    "preamble": r"""
\usepackage{amsmath,amssymb}
\numberwithin{equation}{chapter}
""" + _watermark,
    "maketitle": r"""
\sphinxmaketitle
\begin{center}\small
pyNR \textbf{""" + version + r"""} --- built from \texttt{""" + BRANCH + "@" + COMMIT + r"""}\\[4pt]
Copyright 2026 Rahul Kashyap, Indian Institute of Technology Bombay. Apache License 2.0;\\
attribution required (NOTICE). Please cite pyNR as given in CITATION.cff.
""" + (r"\\[8pt]\fcolorbox[rgb]{0.71,0.33,0.04}{0.99,0.93,0.85}{\parbox{0.8\textwidth}{\centering "
       r"\textbf{Personal development branch \texttt{" + BRANCH + r"}} — work in progress, "
       r"not the released lecture notes.}}" if BANNER else "") + r"""
\end{center}
""",
}


# --- $...$ / $$...$$ math in docstrings ---------------------------------------
# Docstrings write math the Markdown way: $inline$ and $$display$$ blocks
# (each $$ on its own line). A display block may end with a MyST-style label,
# ``$$ (eq-adm-evolution)``; unlabelled blocks get an automatic label so that
# every displayed equation is numbered. Autodoc parses docstrings as
# reStructuredText, so translate to :math:`...` and ``.. math::`` before
# parsing. ``literal`` text (e.g. ``$parfile``) is left untouched.
import re as _re

_LITERAL = _re.compile(r"``.*?``")
_INLINE = _re.compile(r"(?<![\\$])\$(?!\$)(.+?)(?<![\\$])\$(?!\$)")


def _inline_math(line: str) -> str:
    parts, last = [], 0
    for m in _LITERAL.finditer(line):  # never touch ``literal`` spans
        parts.append(_INLINE_sub(line[last:m.start()]))
        parts.append(m.group(0))
        last = m.end()
    parts.append(_INLINE_sub(line[last:]))
    return "".join(parts)


def _INLINE_sub(text: str) -> str:
    def rep(m):
        pre = text[m.start() - 1] if m.start() > 0 else " "
        post = text[m.end()] if m.end() < len(text) else " "
        out = f":math:`{m.group(1)}`"
        if pre.isalnum():
            out = "\\ " + out
        if post.isalnum():
            out = out + "\\ "
        return out
    return _INLINE.sub(rep, text)


_CLOSE = _re.compile(r"^(.*?)\$\$\s*(?:\(([\w:.-]+)\))?\s*$")


def _dollar_math(app, what, name, obj, options, lines):
    out, i, n_auto = [], 0, 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        indent = line[: len(line) - len(line.lstrip())]
        if stripped.startswith("$$"):
            rest = stripped[2:]
            m = _CLOSE.match(rest)
            if m:  # whole equation on one line: $$ x $$ (label)
                block, label = [m.group(1).strip()], m.group(2)
                i += 1
            else:
                block = [rest] if rest else []
                i += 1
                while i < len(lines) and not _CLOSE.match(lines[i].strip()):
                    block.append(lines[i].strip())
                    i += 1
                label = None
                if i < len(lines):
                    m = _CLOSE.match(lines[i].strip())
                    if m.group(1).strip():
                        block.append(m.group(1).strip())
                    label = m.group(2)
                    i += 1
            if not label:
                n_auto += 1
                label = f"eq-{name.replace('.', '-')}-{n_auto}"
            out += [f"{indent}.. math::", f"{indent}   :label: {label}", ""]
            out += [f"{indent}    {b}" if b else "" for b in block]
            out.append("")
            continue
        out.append(_inline_math(line))
        i += 1
    lines[:] = out


# --- "Architecture" box in the autodoc page of every module that a component owns ---------------
def _component_of_module():
    try:
        import extract

        model = extract.load_model()
        cmap = extract.component_map(model)
        return model, {f[:-3].replace("/", ".").removesuffix(".__init__"): c for f, c in cmap.items()}
    except Exception:  # noqa: BLE001
        return None, {}


_MODEL, _MOD2COMP = _component_of_module()


def _architecture_box(app, what, name, obj, options, lines):
    if what != "module" or name not in _MOD2COMP or _MODEL is None:
        return
    comp = _MOD2COMP[name]
    c = _MODEL["components"][comp]
    box = ["", ".. rubric:: Architecture", "",
           f"Component **{comp}** ({c.get('kind')}, layer *{c.get('layer')}*) in ``arch/model.yaml``: "
           f"{c.get('summary', '')}", ""]
    if HAVE_DOT:
        box += [f".. graphviz:: /_generated/arch/component_{comp}.dot", ""]
    for field, label in (("uses", "Uses (calls)"), ("requires", "Requires"), ("reads", "Reads the state of")):
        if c.get(field):
            box.append(f"- *{label}:* " + ", ".join(f"``{b}``" for b in c[field]))
    for r in c.get("registers", []):
        box.append(f"- *Registers* ``{', '.join(r['functions'])}`` *into* ``{r['into']}`` "
                   f"*({r.get('stage')}); {r['into']} calls them back.*")
    if c.get("equations"):
        box.append("- *Equations:* " + ", ".join(f":eq:`{e}`" for e in c["equations"]))
    box.append("")
    lines.extend(box)


def setup(app):
    app.connect("autodoc-process-docstring", _dollar_math)
    app.connect("autodoc-process-docstring", _architecture_box, priority=600)
