# `docs/` — documentation site (Sphinx + MyST)

Build locally (needs Graphviz `dot`; the PDF needs a TeX Live installation with `lualatex` and `latexmk`):

```bash
pip install -e ".[docs]"                                          # from the repository root
python -m pynr thorns --markdown > docs/reference/parameters.md   # generated, git-ignored
make -C docs all          # PDF lecture notes (LaTeX) + HTML site that serves the PDF and links it on the front page
make -C docs html         # HTML only
make -C docs latexpdf     # PDF only: docs/_build/latex/pyNR-lecture-notes.pdf
open docs/_build/html/index.html
```

Equations, tables and figures are numbered. In Markdown pages write
`$$ ... $$ (eq-label)`, then cite with ``Eq. {eq}`eq-label` `` and ``{numref}`tab-label` ``.
In docstrings use `$...$`/`$$...$$ (eq-label)`; `docs/conf.py` translates them.

```bash
open docs/_build/html/index.html
```

| folder / file | content |
|---|---|
| `index.md`, `installation.md`, `running-online.md`, `visualization.md` | user guide |
| `problems/` | the problem set: equations, how to run, measured results, exercises |
| `theory/` | lecture notes, rendered from the module docstrings (`automodule`) |
| `notes/` | notes imported from TiddlyWiki (`python scripts/tiddlywiki2md.py …`) |
| `framework.md`, `utilities.md`, `performance.md`, `architecture.md`, `developer-guide.md`, `software-engineering.md` | code design |
| `roadmap/` | roadmap, decision log, open suggestions, templates; `roadmap/plans/` (rkdev only) |
| `rkdev/` | personal workflow: branches and promotion (rkdev only) |
| `lecture_notes.md` | root of the PDF lecture notes (`make -C docs latexpdf`) |
| `data/` | the simulation data behind every figure (kuibit-readable); see `data/README.md` |
| `figures/` | figures (`*.png`) and the settings of the runs that made them (`*_settings.md`, included by the pages); redraw from `data/` with `python scripts/make_doc_figures.py plot` |
| `devlog/` | development log, one dated entry per milestone |
| `reference/` | parameter reference (generated) and API |
| `conf.py` | Sphinx configuration |

The GitHub Actions workflow `.github/workflows/docs.yml` builds the site and
deploys it to GitHub Pages on every push to `main`.
