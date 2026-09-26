"""Sphinx configuration for the pyNR documentation."""

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

import pynr  # noqa: E402

project = "pyNR"
author = "Rahul Kashyap"
copyright = "2026, Rahul Kashyap"
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
exclude_patterns = ["_build", "README.md"]

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

html_theme = "furo"
html_title = f"pyNR {version}"
html_theme_options = {
    "source_repository": "https://github.com/rahulkashyap-phy/pyNR",
    "source_branch": "main",
    "source_directory": "docs/",
}
