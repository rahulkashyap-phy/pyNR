(sec-docgraph)=
# Documentation graph

How the pages of this documentation depend on each other and on the code:

- **grey arrows** — `contains`: the table of contents;
- **blue dashed** — `cites`: a page references a figure, table, equation, section or module defined on another page;
- **red** — `documents`: a page autodocuments the modules of an architecture component.

It is collected from the build itself (`docs/_ext/docgraph.py`) and also written as `_generated/docgraph.json`. The
explorer on the [Architecture](architecture.md) page links components to their pages through the same data.

(fig-docgraph)=
```{docgraph}
:caption: Pages (clustered by section), the architecture components they document, and the citations between them.
```
