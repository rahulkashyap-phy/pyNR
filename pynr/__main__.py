# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
"""Command line interface.

::

    pynr run par/gauge_wave.par                 # run a parameter file
    pynr run par/kerr.par --set Cactus::cctk_itlast=20 --backend numpy
    pynr run par/gauge_wave.par --output-root ~/pynr_runs   # -> ~/pynr_runs/gauge_wave
    pynr thorns                                 # list thorns
    pynr thorns --markdown > docs/reference/parameters.md
"""

from __future__ import annotations

import argparse
import sys


def _value(s: str):
    from pynr.cactus.parfile import _convert

    return _convert(s, "")


def cmd_run(args):
    from pynr import Simulation

    overrides = {}
    for kv in args.set or []:
        k, v = kv.split("=", 1)
        overrides[k.strip()] = _value(v.strip())
    if args.backend:
        overrides["Driver::backend"] = args.backend
    if args.out:
        overrides["IO::out_dir"] = args.out
    if args.output_root:
        import os

        os.environ["PYNR_OUTPUT_DIR"] = args.output_root
    Simulation.from_parfile(args.parfile, overrides=overrides).run()


def cmd_thorns(args):
    import pynr.thorns  # noqa: F401
    from pynr.cactus.thorn import THORNS

    for cls in sorted(THORNS.values(), key=lambda c: c.name.lower()):
        doc = (cls.__module__ and sys.modules[cls.__module__].__doc__ or "").strip().splitlines()
        summary = doc[0] if doc else ""
        if args.markdown:
            print(f"## {cls.name}\n\n{summary}\n")
            if cls.requires:
                print(f"Requires: {', '.join(cls.requires)}\n")
            if cls.parameters:
                print(f"```{{table}} Parameters of the {cls.name} thorn.\n"
                      f":name: tab-params-{cls.name.lower()}\n")
                print("| parameter | default | description |\n|---|---|---|")
                for n, p in cls.parameters.items():
                    d = f"{p.default!r}" + (f" (array, size {p.size})" if p.size else "")
                    kw = f" One of: {', '.join(f'`{k}`' for k in p.keywords)}." if p.keywords else ""
                    print(f"| `{cls.name}::{n}` | `{d}` | {p.doc}.{kw} |")
                print("```\n")
        else:
            print(f"{cls.name:16s} {summary}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pynr", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run a parameter file")
    r.add_argument("parfile")
    r.add_argument("--set", action="append", metavar="Thorn::param=value",
                   help="override a parameter (repeatable)")
    r.add_argument("--backend", choices=["numba", "numpy"])
    r.add_argument("--out", help="output directory name (relative: under the output root)")
    r.add_argument("--output-root", help="output root for relative output directories "
                   "(default: $PYNR_OUTPUT_DIR, else <checkout>/simulations, else .)")
    r.set_defaults(func=cmd_run)
    t = sub.add_parser("thorns", help="list thorns and parameters")
    t.add_argument("--markdown", action="store_true", help="full parameter reference in Markdown")
    t.set_defaults(func=cmd_thorns)
    args = ap.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
