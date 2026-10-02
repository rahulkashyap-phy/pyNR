# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
"""Describe the machine a run used, so every reported cost states its hardware.

:func:`machine_info` collects the CPU model, core counts (performance and
efficiency cores on Apple silicon), the Numba thread count, RAM, OS and
library versions. It never records a hostname or user name. Every
``pynr.log`` starts with :func:`machine_block`, and the docs quote
:func:`machine_line` next to wall times.
"""

from __future__ import annotations

import os
import platform
import subprocess


def _sysctl(key: str) -> str | None:
    try:
        return subprocess.run(["sysctl", "-n", key], capture_output=True, text=True,
                              timeout=2).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def machine_info() -> dict:
    """Hardware and software of this machine (no hostname, no user name)."""
    info: dict = {"os": f"{platform.system()} {platform.release()}", "arch": platform.machine()}
    cpu, ram, p_cores, e_cores = None, None, None, None
    if platform.system() == "Darwin":
        cpu = _sysctl("machdep.cpu.brand_string")
        mem = _sysctl("hw.memsize")
        ram = int(mem) if mem and mem.isdigit() else None
        p, e = _sysctl("hw.perflevel0.physicalcpu"), _sysctl("hw.perflevel1.physicalcpu")
        p_cores = int(p) if p and p.isdigit() else None
        e_cores = int(e) if e and e.isdigit() else None
        mac = platform.mac_ver()[0]
        if mac:
            info["os"] = f"macOS {mac}"
    elif os.path.exists("/proc/cpuinfo"):
        with open("/proc/cpuinfo") as fh:
            for line in fh:
                if line.lower().startswith("model name"):
                    cpu = line.split(":", 1)[1].strip()
                    break
        try:
            with open("/proc/meminfo") as fh:
                ram = int(fh.readline().split()[1]) * 1024
        except (OSError, ValueError, IndexError):
            pass
    info["cpu"] = cpu or platform.processor() or "unknown CPU"
    info["cores"] = os.cpu_count()
    if p_cores and e_cores:
        info["cores_split"] = f"{p_cores}P+{e_cores}E"
    info["ram_gb"] = round(ram / 2**30) if ram else None
    info["python"] = platform.python_version()
    try:
        import numba
        import numpy

        info["numpy"], info["numba"] = numpy.__version__, numba.__version__
        info["threads"] = numba.get_num_threads()
    except Exception:  # noqa: BLE001
        pass
    try:
        from pynr import __version__

        info["pynr"] = __version__
    except Exception:  # noqa: BLE001
        pass
    return info


def machine_line(info: dict | None = None) -> str:
    """One line, e.g. ``Apple M3 Pro, 12 cores (6P+6E), 18 GB, macOS 27.0, Numba 0.67.0, 12 threads``."""
    i = info or machine_info()
    cores = f"{i.get('cores')} cores" + (f" ({i['cores_split']})" if i.get("cores_split") else "")
    parts = [i.get("cpu"), cores]
    if i.get("ram_gb"):
        parts.append(f"{i['ram_gb']} GB")
    parts.append(i.get("os"))
    if i.get("numba"):
        parts.append(f"Numba {i['numba']}, {i.get('threads')} threads")
    return ", ".join(str(p) for p in parts if p)


def machine_block(backend: str | None = None) -> str:
    """Multi-line block for the top of ``pynr.log`` (parsed back by :func:`parse_machine_block`)."""
    i = machine_info()
    if backend:
        i["backend"] = backend
    lines = ["# machine: " + machine_line(i)]
    lines += [f"# machine.{k} = {v}" for k, v in i.items() if v is not None]
    return "\n".join(lines)


def parse_machine_block(log_text: str) -> dict:
    """Recover :func:`machine_info` fields (and ``line``) from a ``pynr.log``."""
    out = {}
    for line in log_text.splitlines():
        if line.startswith("# machine: "):
            out["line"] = line[len("# machine: "):]
        elif line.startswith("# machine.") and " = " in line:
            k, v = line[len("# machine."):].split(" = ", 1)
            out[k] = v
    return out
