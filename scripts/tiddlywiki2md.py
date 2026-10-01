# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
"""Convert TiddlyWiki tiddlers to Markdown pages for the documentation site.

Inputs (any of):
  * a JSON export  (TiddlyWiki: "Export all" -> JSON file),
  * a folder of ``.tid`` files (Node.js TiddlyWiki ``tiddlers/`` folder),
  * a single-file wiki ``.html`` (tiddlers are read from its JSON store).

Usage::

    python scripts/tiddlywiki2md.py ~/wiki/tiddlers docs/notes --tag pyNR
    python scripts/tiddlywiki2md.py mywiki.html docs/notes --tag lecture

Only tiddlers carrying one of the ``--tag`` values are exported (all non-system
tiddlers if no tag is given). Each becomes ``docs/notes/<slug>.md`` with the
tiddler's tags and dates in a front-matter block, and ``docs/notes/index.md``
gets a table of contents. The conversion handles the common WikiText
subset: headings, bold/italic/underline/strike, inline and block code,
bulleted/numbered lists, block quotes, tables, ``[[links]]``, external links,
images, and ``$$...$$`` math (KaTeX plugin syntax, which MyST understands).
Macros, widgets and transclusions are left as-is inside an HTML comment so
nothing is silently lost.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path


def slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "untitled"


# ------------------------------------------------------------------ readers
def read_tid(path: Path) -> dict:
    head, _, body = path.read_text(encoding="utf-8").partition("\n\n")
    t = {"text": body}
    for line in head.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            t[k.strip()] = v.strip()
    return t


def read_source(src: Path) -> list[dict]:
    if src.is_dir():
        return [read_tid(p) for p in sorted(src.rglob("*.tid"))]
    text = src.read_text(encoding="utf-8")
    if src.suffix == ".json":
        return json.loads(text)
    m = re.search(r'<script class="tiddlywiki-tiddler-store" type="application/json">(.*?)</script>',
                  text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    raise SystemExit(f"Cannot find tiddlers in {src}")


def parse_tags(s: str) -> list[str]:
    return [a or b for a, b in re.findall(r"\[\[([^\]]+)\]\]|(\S+)", s or "")]


# ------------------------------------------------------------------ WikiText -> Markdown
def convert(text: str, titles: dict[str, str]) -> str:
    out, in_code = [], False
    for line in text.splitlines():
        if line.startswith("```"):
            in_code = not in_code
            out.append(line)
            continue
        if in_code:
            out.append(line)
            continue
        m_list = re.match(r"^([*#]+)\s+(.*)", line)  # WikiText lists: * bullet, # numbered
        m_head = re.match(r"^(!{1,6})\s*(.*)", line)
        if m_list:
            marks = m_list.group(1)
            bullet = "-" if marks[-1] == "*" else "1."
            line = "   " * (len(marks) - 1) + f"{bullet} {m_list.group(2)}"
        elif m_head:
            line = "#" * (len(m_head.group(1)) + 1) + " " + m_head.group(2)  # page title is H1
        elif line.startswith(">"):
            line = re.sub(r"^>\s?", "> ", line)
        if line.startswith("|") and line.rstrip().endswith("|h"):
            cells = line.rstrip()[:-1]
            out.append(cells)
            out.append("|" + "---|" * (cells.count("|") - 1))
            continue
        line = inline(line, titles)
        out.append(line)
    return "\n".join(out) + "\n"


def inline(s: str, titles: dict[str, str]) -> str:
    s = re.sub(r"''(.+?)''", r"**\1**", s)
    s = re.sub(r"(?<!:)//(.+?)//", r"*\1*", s)
    s = re.sub(r"__(.+?)__", r"<u>\1</u>", s)
    s = re.sub(r"~~(.+?)~~", r"~~\1~~", s)
    s = re.sub(r"\[img\[([^\]|]+)\|?([^\]]*)\]\]",
               lambda m: f"![{m.group(1) if m.group(2) else ''}]({m.group(2) or m.group(1)})", s)

    def link(m):
        label, target = (m.group(1).split("|", 1) + [None])[:2]
        if target is None:
            target = label
        if re.match(r"https?://", target):
            return f"[{label}]({target})"
        if target in titles:
            return f"[{label}]({titles[target]}.md)"
        return label  # link to a tiddler that is not exported

    s = re.sub(r"\[\[([^\]]+)\]\]", link, s)
    s = re.sub(r"(<<[^>]+>>|\{\{[^}]+\}\})", r"<!-- tiddlywiki: \1 -->", s)
    return s


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", type=Path)
    ap.add_argument("dest", type=Path, nargs="?", default=Path("docs/notes"))
    ap.add_argument("--tag", action="append", default=[], help="export tiddlers with this tag")
    args = ap.parse_args()

    tiddlers = [t for t in read_source(args.source)
                if not t.get("title", "").startswith("$:/")
                and (not args.tag or set(parse_tags(t.get("tags", ""))) & set(args.tag))]
    titles = {t["title"]: slug(t["title"]) for t in tiddlers}
    args.dest.mkdir(parents=True, exist_ok=True)
    for t in tiddlers:
        body = convert(html.unescape(t.get("text", "")), titles)
        tags = parse_tags(t.get("tags", ""))
        front = (f"---\ntiddler: \"{t['title']}\"\ntags: {json.dumps(tags)}\n"
                 f"modified: \"{t.get('modified', '')}\"\n---\n\n")
        (args.dest / f"{titles[t['title']]}.md").write_text(front + f"# {t['title']}\n\n" + body,
                                                             encoding="utf-8")
    index = ["# Notes", "", "Imported from TiddlyWiki with `scripts/tiddlywiki2md.py`.", "",
             "```{toctree}", ":maxdepth: 1", ""]
    index += sorted(titles.values()) + ["```", ""]
    (args.dest / "index.md").write_text("\n".join(index), encoding="utf-8")
    print(f"wrote {len(tiddlers)} notes to {args.dest}")


if __name__ == "__main__":
    main()
