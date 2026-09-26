"""Parameter declarations (the pyNR equivalent of ``param.ccl``).

Each thorn declares its parameters as a dict of :class:`Param` objects::

    parameters = {
        "lapse_evolution": Param("static", "Slicing condition",
                                 keywords=("static", "harmonic", "1+log")),
        "epsdis": Param(0.1, "Kreiss-Oliger dissipation strength"),
        "radius": Param(0.0, "Extraction radii", size=10),
    }

The type of a parameter is the type of its default. Keyword parameters are
matched case-insensitively. Like Cactus, setting a parameter that no active
thorn declares is an error, so typos never pass silently.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Param:
    """Declaration of a single thorn parameter."""

    default: Any
    doc: str = ""
    keywords: tuple[str, ...] | None = None
    size: int | None = None  # array parameter of this length

    def cast(self, value: Any) -> Any:
        """Convert a parfile value to the declared type, validating keywords."""
        kind = type(self.default)
        if kind is bool:
            if isinstance(value, str):
                low = value.lower()
                if low not in ("yes", "no", "true", "false", "1", "0"):
                    raise ValueError(f"'{value}' is not a boolean")
                return low in ("yes", "true", "1")
            return bool(value)
        if kind is int:
            if isinstance(value, float) and not value.is_integer():
                raise ValueError(f"{value} is not an integer")
            return int(value)
        if kind is float:
            return float(value)
        value = str(value)
        if self.keywords is not None:
            for kw in self.keywords:
                if kw.lower() == value.lower():
                    return kw
            raise ValueError(f"'{value}' not one of {self.keywords}")
        return value

    def default_value(self) -> Any:
        return [self.default] * self.size if self.size else self.default


class ThornParams:
    """Attribute-style access to one thorn's parameters (``p.xmin``)."""

    def __init__(self, thorn: str, values: dict):
        object.__setattr__(self, "_thorn", thorn)
        object.__setattr__(self, "_values", values)

    def __getattr__(self, name):
        try:
            return self._values[name.lower()]
        except KeyError:
            raise AttributeError(f"{self._thorn} has no parameter '{name}'") from None

    def __setattr__(self, name, value):
        raise AttributeError("Parameters are read-only after startup")

    def as_dict(self) -> dict:
        return dict(self._values)


class Parameters:
    """Registry of declared parameters and their values for a simulation."""

    def __init__(self):
        self._decl: dict[str, tuple[str, dict[str, tuple[str, Param]]]] = {}
        self._values: dict[str, dict[str, Any]] = {}

    def declare(self, thorn: str, params: dict[str, Param]) -> None:
        key = thorn.lower()
        decl = {n.lower(): (n, p) for n, p in params.items()}
        self._decl[key] = (thorn, decl)
        self._values[key] = {n: p.default_value() for n, (_, p) in decl.items()}

    def set(self, full_name: str, value: Any) -> None:
        thorn, name = full_name.lower().split("::")
        if thorn not in self._decl:
            raise KeyError(f"Parameter '{full_name}': thorn '{thorn}' is not active")
        decl = self._decl[thorn][1]
        if name not in decl:
            raise KeyError(f"Thorn '{self._decl[thorn][0]}' has no parameter '{name}'")
        p = decl[name][1]
        if p.size:
            if not isinstance(value, dict):
                value = {0: value}
            arr = self._values[thorn][name]
            for i, v in value.items():
                if i >= p.size:
                    raise IndexError(f"{full_name}[{i}] out of range (size {p.size})")
                arr[i] = p.cast(v)
        else:
            self._values[thorn][name] = p.cast(value)

    def get(self, thorn: str, name: str) -> Any:
        return self._values[thorn.lower()][name.lower()]

    def of(self, thorn: str) -> ThornParams:
        return ThornParams(thorn, self._values[thorn.lower()])

    def dump(self) -> str:
        """Return all parameter values in parfile syntax (written to the output dir)."""
        lines = []
        for key, (tname, decl) in self._decl.items():
            for pname, (orig, p) in decl.items():
                val = self._values[key][pname]
                vals = enumerate(val) if p.size else [(None, val)]
                for i, v in vals:
                    idx = f"[{i}]" if i is not None else ""
                    if isinstance(v, bool):
                        s = "yes" if v else "no"
                    elif isinstance(v, str):
                        s = f'"{v}"'
                    else:
                        s = repr(v)
                    lines.append(f"{tname}::{orig}{idx} = {s}")
        return "\n".join(lines) + "\n"
