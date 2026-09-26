# Notes

Notes imported from the course TiddlyWiki. To refresh them:

```bash
# Node.js wiki:            path to its tiddlers/ folder
# single-file wiki:        path to the .html file
# or "Export all" → JSON:  path to the .json file
python scripts/tiddlywiki2md.py <wiki source> docs/notes --tag pyNR
```

Only tiddlers tagged `pyNR` (repeat `--tag` for more) are exported. The
script rewrites this page with a table of contents. Commit the generated
`docs/notes/*.md`, and the docs workflow publishes them with the rest of the
site.

```{toctree}
:maxdepth: 1
:glob:

*
```
