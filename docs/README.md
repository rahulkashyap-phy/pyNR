# `docs/` — documentation site (Sphinx + MyST)

Build locally:

```bash
pip install -e ".[docs]"                                   # from the repository root
python -m pynr thorns --markdown > docs/reference/parameters.md   # generated, git-ignored
sphinx-build -b html docs docs/_build/html
open docs/_build/html/index.html
```

| folder / file | content |
|---|---|
| `index.md`, `installation.md`, `running-online.md`, `visualization.md` | user guide |
| `problems/` | the problem set: equations, how to run, measured results, exercises |
| `theory/` | lecture notes, rendered from the module docstrings (`automodule`) |
| `notes/` | notes imported from TiddlyWiki (`python scripts/tiddlywiki2md.py …`) |
| `framework.md`, `utilities.md`, `performance.md`, `roadmap.md` | code design |
| `devlog/` | development log, one dated entry per milestone |
| `reference/` | parameter reference (generated) and API |
| `conf.py` | Sphinx configuration |

The GitHub Actions workflow `.github/workflows/docs.yml` builds the site and
deploys it to GitHub Pages on every push to `main`.
