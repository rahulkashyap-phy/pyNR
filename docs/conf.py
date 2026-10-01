# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
"""Sphinx configuration for the pyNR documentation."""

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

import pynr  # noqa: E402

# --- documentation figures ------------------------------------------------------
# Each figure is a generated snippet docs/figures/<name>.md: the real figure and
# its run-settings table when docs/data/ has the data, otherwise a placeholder
# pointing to the "Reproducing the documentation figures" section.
sys.path.insert(0, os.path.abspath("../scripts"))
import make_doc_figures  # noqa: E402

make_doc_figures.render_all()

project = "pyNR"
author = "Rahul Kashyap"
copyright = "2026, Rahul Kashyap (Indian Institute of Technology Bombay). Apache-2.0; attribution required, see NOTICE"
version = release = pynr.__version__

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
]

myst_enable_extensions = ["dollarmath", "amsmath", "colon_fence", "deflist", "attrs_inline"]
myst_heading_anchors = 3
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
exclude_patterns = ["_build", "README.md", "**/README.md", "data", "figures"]  # figure snippets are {include}d

autodoc_member_order = "bysource"
autodoc_default_options = {"members": True, "undoc-members": False}
# Numba-compiled functions are documented through their Python docstrings.
autodoc_mock_imports = []

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

html_theme = "furo"
html_title = f"pyNR {version}"
html_theme_options = {
    "source_repository": "https://github.com/rahulkashyap-phy/pyNR",
    "source_branch": "main",
    "source_directory": "docs/",
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


def setup(app):
    app.connect("autodoc-process-docstring", _dollar_math)
