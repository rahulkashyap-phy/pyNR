"""Reader for Cactus/Einstein Toolkit parameter files.

pyNR reads the same ``.par`` syntax as the Einstein Toolkit, so a parameter
file looks like::

    ActiveThorns = "ADMBase ADMEvolve Exact MoL IOHDF5"

    CoordBase::xmin = -10.0     # comments start with '#'
    ADMBase::initial_data = "exact"
    Multipole::radius[0] = 20.0
    IO::out_dir = $parfile

Supported value forms: quoted strings (may span lines), ``yes/no/true/false``,
integers, floats (``1e-3`` and Fortran-style ``1d-3``) and the ``$parfile``
substitution (parameter-file name without ``.par``).
"""

from __future__ import annotations

import os
import re

_ENTRY = re.compile(
    r"""
    (?P<key>[A-Za-z_]\w*(?:::\w+)?(?:\[\s*\d+\s*\])?)   # thorn::param[idx]
    \s*=\s*
    (?P<val>"(?:[^"\\]|\\.)*"|[^\s#"]+)                  # "string" or bare token
    """,
    re.VERBOSE | re.DOTALL,
)


def _strip_comments(text: str) -> str:
    """Remove ``#`` comments that are not inside a quoted string."""
    out, in_str = [], False
    for line in text.splitlines():
        buf = []
        for ch in line:
            if ch == '"':
                in_str = not in_str
            if ch == "#" and not in_str:
                break
            buf.append(ch)
        out.append("".join(buf))
    return "\n".join(out)


def _convert(token: str, parfile_stem: str):
    if token.startswith('"'):
        return token[1:-1].replace('\\"', '"')
    if token == "$parfile":
        return parfile_stem
    low = token.lower()
    if low in ("yes", "true"):
        return True
    if low in ("no", "false"):
        return False
    try:
        return int(token)
    except ValueError:
        pass
    try:
        return float(low.replace("d", "e"))
    except ValueError:
        return token


def parse_parfile_text(text: str, parfile_stem: str = "simulation") -> dict:
    """Parse the text of a parameter file.

    Returns a dict mapping ``"thorn::param"`` (lower-case) to a value, or to a
    ``{index: value}`` dict for array parameters. ``ActiveThorns`` is returned
    under the key ``"activethorns"`` as a list of thorn names.
    """
    entries: dict = {}
    active: list[str] = []
    for m in _ENTRY.finditer(_strip_comments(text)):
        key, val = m.group("key"), _convert(m.group("val"), parfile_stem)
        if key.lower() == "activethorns":
            active.extend(str(val).split())
            continue
        if "::" not in key:
            raise ValueError(f"Parameter '{key}' must be written as Thorn::name")
        idx = None
        if "[" in key:
            key, idx = key.split("[")
            idx = int(idx.rstrip("]").strip())
        key = key.lower()
        if idx is None:
            entries[key] = val
        else:
            entries.setdefault(key, {})[idx] = val
    entries["activethorns"] = active
    return entries


def parse_parfile(path: str | os.PathLike) -> dict:
    """Parse a parameter file from disk (see :func:`parse_parfile_text`)."""
    stem = os.path.splitext(os.path.basename(str(path)))[0]
    with open(path) as fh:
        return parse_parfile_text(fh.read(), stem)
