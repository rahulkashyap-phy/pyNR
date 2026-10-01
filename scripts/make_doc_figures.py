# Copyright 2026 Rahul Kashyap (Indian Institute of Technology Bombay)
# SPDX-License-Identifier: Apache-2.0 -- see LICENSE and NOTICE (attribution required)
"""Save simulation data for the documentation, and render the figures from it.

    python scripts/make_doc_figures.py save --runs <dir with finished runs>
    python scripts/make_doc_figures.py plot          # (default) from docs/data/

``save`` copies the plot-relevant outputs of each run into ``docs/data/<run>/``:
all ASCII time series (``*.asc``: reductions and Psi4 multipoles), the run's
``parameters.par``, ``pynr.log`` and ``.par`` file. For the gauge wave it runs
four short simulations itself (~10 s) and stores the alpha(x) profiles.

``plot`` (also called automatically by ``docs/conf.py`` at every docs build)
writes, for each figure, ``docs/figures/<name>.md``: a MyST snippet that the
documentation pages include. If the data for the figure exist, the snippet
contains the figure (``docs/figures/<name>.png``), its caption and a numbered
table of run settings read from the stored ``parameters.par``/``pynr.log``.
If not, it contains a placeholder image and a pointer to the section
"Reproducing the documentation figures" (label ``sec-figure-data``), keeping
the same figure/table labels so cross-references still resolve.
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import shutil

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAR = os.path.join(ROOT, "par")
OUT = os.path.join(ROOT, "docs", "figures")
DATA = os.path.join(ROOT, "docs", "data")
GW_RUNS = {"dx0.02_t10": (0.02, 10.0), "dx0.04_t1": (0.04, 1.0),
           "dx0.02_t1": (0.02, 1.0), "dx0.01_t1": (0.01, 1.0)}

COMMON = ["Exact::exact_model", "CoordBase::xmin", "CoordBase::xmax", "CoordBase::ymin",
          "CoordBase::ymax", "CoordBase::dx", "Driver::ghost_size", "Driver::backend",
          "Time::dtfac", "MoL::ODE_Method", "Dissipation::epsdis",
          "ADMBase::initial_lapse", "ADMBase::initial_shift", "ADMBase::lapse_evolution_method",
          "ADMEvolve::bound", "ADMEvolve::excision_radius", "Cactus::cctk_final_time"]


# --------------------------------------------------------------------------- figure registry
# label, caption (MyST), parameter file, data files needed (relative to docs/data),
# run directory whose settings are tabulated, extra settings keys, note, width
FIGURES = {
    "gauge_wave": dict(
        title="gauge-wave",
        label="fig-gauge-wave", width="100%", parfile="gauge_wave.par",
        settings_run="gauge_wave/dx0.02_t10",
        needs=[f"gauge_wave/{t}/alp_profile.dat" for t in GW_RUNS]
        + ["gauge_wave/dx0.02_t10/parameters.par", "gauge_wave/dx0.02_t10/pynr.log"],
        keys=["Exact::Minkowski_gauge_wave__amplitude", "Exact::Minkowski_gauge_wave__lambda",
              "CoordBase::periodic_x"],
        caption="Gauge wave. Left: the lapse after ten crossing times (dashed) on top of the "
                "exact solution of Eq. {eq}`eq-gauge-wave-metric` (grey). Right: the error in "
                "$\\alpha$ at $t = 1$ for $\\Delta x = 0.04, 0.02, 0.01$, each multiplied by "
                "$(0.04/\\Delta x)^4$. The three curves coincide, which is 4th-order convergence.",
        note="The right panel repeats the run with $\\Delta x = 0.04, 0.02, 0.01$ (and "
             "$\\Delta y = \\Delta z = \\Delta x$) up to $t = 1$; everything else is as in the "
             "table. Data: `docs/data/gauge_wave/`."),
    "kerr_constraints": dict(
        title="Kerr-Schild constraint",
        label="fig-kerr-constraints", width="75%", parfile="kerr_schild.par",
        settings_run="kerr_schild",
        needs=["kerr_schild/H.norm2.asc", "kerr_schild/H.maximum.asc",
               "kerr_schild/parameters.par", "kerr_schild/pynr.log"],
        keys=["Exact::Kerr_KerrSchild__mass", "Exact::Kerr_KerrSchild__spin"],
        caption="Hamiltonian constraint (Eq. {eq}`eq-constraints`) for the $\\chi = 0.6$ Kerr "
                "black hole evolved with plain ADM in the exact stationary gauge. The flat part "
                "is truncation error. The exponential growth is the constraint-violating mode "
                "of the ADM system.",
        note="Data: `docs/data/kerr_schild/` (`H.norm2.asc`, `H.maximum.asc`)."),
    "perturbed_psi4": dict(
        title="perturbed-black-hole",
        label="fig-perturbed-psi4", width="85%", parfile="schwarzschild_perturbed.par",
        settings_run="schwarzschild_perturbed",
        needs=["schwarzschild_perturbed/mp_Psi4_l2_m0_r6.00.asc",
               "schwarzschild_perturbed/mp_Psi4_l4_m0_r6.00.asc",
               "schwarzschild_perturbed/parameters.par", "schwarzschild_perturbed/pynr.log"],
        keys=["Exact::Kerr_KerrSchild__mass", "Exact::Kerr_KerrSchild__spin",
              "Perturb::amplitude", "Perturb::radius", "Perturb::width", "Perturb::l",
              "Perturb::m", "Multipole::radius", "Multipole::l_max",
              "Multipole::geodesic_level", "Multipole::out_every"],
        caption="$|\\mathrm{Re}\\,\\Psi_4^{20}|$ and $|\\mathrm{Re}\\,\\Psi_4^{40}|$ on the inner "
                "extraction sphere. The dashed line is the decay rate of the $\\ell = 2$ "
                "quasi-normal mode, Eq. {eq}`eq-qnm-220`. After the burst the signal does not "
                "follow it. It grows, and $\\ell = 4$ overtakes $\\ell = 2$: this is the ADM "
                "instability of {numref}`fig-kerr-constraints`, not physics.",
        note="Data: `docs/data/schwarzschild_perturbed/` (`mp_Psi4_l*_m*_r*.asc`; readable with "
             "`kuibit.simdir.SimDir`)."),
}


# --------------------------------------------------------------------------- settings tables
def read_params(run_dir):
    vals = {}
    with open(os.path.join(run_dir, "parameters.par")) as fh:
        for line in fh:
            if "=" in line:
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip()
    return vals


def run_summary(run_dir):
    """Grid shape, dt, final time and wall time from ``pynr.log``."""
    info = {}
    with open(os.path.join(run_dir, "pynr.log")) as fh:
        log = fh.read()
    m = re.search(r"shape=\(([^)]*)\).*?dt = ([0-9.e+-]+)", log, re.S)
    if m:
        info["grid points (incl. ghosts)"] = " × ".join(m.group(1).split(", "))
        info["time step dt"] = m.group(2)
    m = re.search(r"Done: iteration (\d+), t = ([0-9.e+-]+), wall time ([0-9.]+) s", log)
    if m:
        info["iterations / final t"] = f"{m.group(1)} / {m.group(2)}"
        info["wall time"] = f"{float(m.group(3)):.0f} s"
    m = re.search(r"ABORT: blow-up.* at iteration (\d+), t = ([0-9.e+-]+)", log)
    if m:
        info["ended by"] = f"blow-up abort (MoL::check_nan_every) at t = {m.group(2)}"
    return info


def settings_rows(run_dir, keys):
    vals = read_params(run_dir)
    rows = []
    for k in COMMON + keys:
        if k in vals:
            rows.append((k, vals[k]))
        elif f"{k}[0]" in vals:  # array parameter: list the used entries
            n = int(vals.get("Multipole::nradii", 1)) if k == "Multipole::radius" else None
            items, i = [], 0
            while f"{k}[{i}]" in vals and (n is None or i < n):
                items.append(vals[f"{k}[{i}]"])
                i += 1
            rows.append((k, ", ".join(items)))
    return rows + list(run_summary(run_dir).items())


def _table(name, caption, rows):
    def esc(t):
        return str(t).replace("|", "\\|")

    md = [f"```{{table}} {caption}", f":name: tab-settings-{name.replace('_', '-')}", "",
          "| setting | value |", "|---|---|"]
    md += [f"| `{k}` | `{esc(v)}` |" if "::" in k else f"| {k} | {esc(v)} |" for k, v in rows]
    return md + ["```", ""]


def _figure(fig, image, caption):
    return [f"```{{figure}} {image}", f":name: {fig['label']}", f":width: {fig['width']}", "",
            caption, "```", ""]


# --------------------------------------------------------------------------- plotting
def _plt():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"figure.dpi": 130, "font.size": 10, "axes.grid": True, "grid.alpha": 0.3})
    return plt


def plot_gauge_wave(path):
    plt = _plt()

    def load(tag):
        return np.loadtxt(os.path.join(DATA, "gauge_wave", tag, "alp_profile.dat"), unpack=True)

    fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
    x, a, ae = load("dx0.02_t10")
    ax[0].plot(x, ae, "k-", lw=2.5, alpha=0.35, label="exact")
    ax[0].plot(x, a, "C0--", label=r"pyNR, $\Delta x = 0.02$")
    ax[0].set(xlabel="$x$", ylabel=r"$\alpha$", title="lapse after 10 crossing times")
    ax[0].legend()
    for tag, c in (("dx0.04_t1", "C1"), ("dx0.02_t1", "C2"), ("dx0.01_t1", "C3")):
        dx = GW_RUNS[tag][0]
        x, a, ae = load(tag)
        ax[1].plot(x, (a - ae) * (0.04 / dx) ** 4, c,
                   label=rf"$\Delta x={dx}$, error $\times (0.04/\Delta x)^4$")
    ax[1].set(xlabel="$x$", ylabel=r"scaled error in $\alpha$", title="4th-order convergence ($t = 1$)")
    ax[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_kerr_constraints(path):
    plt = _plt()
    run = os.path.join(DATA, "kerr_schild")
    fig, ax = plt.subplots(figsize=(5.5, 3.4))
    for f, lab in (("H.norm2.asc", r"$\|H\|_2$"), ("H.maximum.asc", r"$\max H$")):
        t, h = np.loadtxt(os.path.join(run, f), usecols=(1, 2), unpack=True)
        ok = np.isfinite(h) & (np.abs(h) < 1e6)
        ax.semilogy(t[ok], np.abs(h[ok]), label=lab)
    ax.set(xlabel="$t/M$", ylabel="Hamiltonian constraint",
           title=r"Kerr-Schild, $\chi=0.6$, $\Delta x=0.25$ (plain ADM)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_perturbed_psi4(path):
    """Reads the Multipole ASCII files directly (columns: t, Re, Im)."""
    plt = _plt()
    run = os.path.join(DATA, "schwarzschild_perturbed")
    r = 6.0
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    for l, c in ((2, "C0"), (4, "C3")):  # noqa: E741
        t, re_, _ = np.loadtxt(os.path.join(run, f"mp_Psi4_l{l}_m0_r{r:.2f}.asc"), unpack=True)
        ax.semilogy(t, np.abs(re_), c, lw=1, label=rf"$|\mathrm{{Re}}\,\Psi_4^{{{l}0}}|$")
    t0 = 10.0
    tt = np.linspace(t0, 36, 50)
    ax.semilogy(tt, 5e-4 * np.exp(-0.0890 * (tt - t0)), "k--", lw=1,
                label=r"QNM decay $e^{-0.089\,t/M}$")
    ax.set(xlabel="$t/M$", ylabel=r"$|\Psi_4^{\ell 0}|$ at $r = %g M$" % r, ylim=(1e-8, 1e-1),
           title="Perturbed Schwarzschild: extraction works, ADM mode grows")
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


PLOTTERS = {"gauge_wave": plot_gauge_wave, "kerr_constraints": plot_kerr_constraints,
            "perturbed_psi4": plot_perturbed_psi4}


# --------------------------------------------------------------------------- render
def missing_data(name):
    return [f for f in FIGURES[name]["needs"] if not os.path.exists(os.path.join(DATA, f))]


def render(name, log=print):
    """Write ``docs/figures/<name>.md`` (and the PNG when the data exist).

    Returns ``True`` if the real figure was produced, ``False`` for a placeholder.
    """
    fig = FIGURES[name]
    os.makedirs(OUT, exist_ok=True)
    tab = f"tab-settings-{name.replace('_', '-')}"
    caption_tab = f"Run settings for the {fig['title']} figure."
    missing = missing_data(name)
    reason = f"missing {', '.join(missing[:2])}{' …' if len(missing) > 2 else ''}"
    if not missing:
        try:
            PLOTTERS[name](os.path.join(OUT, f"{name}.png"))
            rows = [("parameter file", f"`par/{fig['parfile']}`")]
            rows += settings_rows(os.path.join(DATA, fig["settings_run"]), fig["keys"])
            md = _figure(fig, f"../figures/{name}.png", fig["caption"] + f" Settings: {{numref}}`{tab}`.")
            md += _table(name, caption_tab, rows) + [fig["note"], ""]
            _write(name, md)
            log(f"[doc figures] {name}: rendered from docs/data")
            return True
        except Exception as err:  # noqa: BLE001 -- never break the docs build
            reason = f"plotting failed: {err}"
    md = _figure(fig, "../_static/figure-placeholder.svg",
                 fig["caption"] + " **Placeholder: the data for this figure are not part of "
                 "this build; see {ref}`sec-figure-data`.**")
    md += [":::{note}",
           f"This figure is drawn from simulation data in `docs/data/`, which this build does "
           f"not have ({reason}). Follow {{ref}}`sec-figure-data` to generate the dataset: run "
           f"`par/{fig['parfile']}`, then `python scripts/make_doc_figures.py save --runs <dir>`, "
           "and rebuild the docs.", ":::", ""]
    md += _table(name, caption_tab, [("parameter file", f"`par/{fig['parfile']}`"),
                                     ("run settings", "not available: dataset not generated")])
    _write(name, md)
    log(f"[doc figures] {name}: PLACEHOLDER ({reason})")
    return False


def _write(name, lines):
    with open(os.path.join(OUT, f"{name}.md"), "w") as fh:
        fh.write("\n".join(lines))


def render_all(log=print):
    return {name: render(name, log) for name in FIGURES}


# --------------------------------------------------------------------------- save
def save_gauge_wave():
    """Run the gauge wave at four settings; store alpha(x), alpha_exact(x) and metadata."""
    from pynr import Simulation

    for tag, (dx, t_final) in GW_RUNS.items():
        out = os.path.join(DATA, "gauge_wave", tag)
        shutil.rmtree(out, ignore_errors=True)
        over = {"CoordBase::dx": dx, "CoordBase::dy": dx, "CoordBase::dz": dx,
                "CoordBase::ymin": -dx, "CoordBase::ymax": dx,
                "CoordBase::zmin": -dx, "CoordBase::zmax": dx,
                "Cactus::cctk_final_time": t_final, "IOBasic::outInfo_every": 0,
                "IOScalar::outScalar_every": 0, "IOHDF5::out2D_every": 0, "IO::out_dir": out}
        sim = Simulation.from_parfile(os.path.join(PAR, "gauge_wave.par"), overrides=over,
                                      verbose=False).run()
        X, Y, Z = sim.grid.meshgrid()
        _, _, ae, _ = sim.thorn("Exact").solution(sim.time, X, Y, Z)
        g = sim.grid.nghost
        prof = np.column_stack([sim.grid.coords1d[0][g:-g], sim.thorn("ADMBase").U[12][g:-g, g, g],
                                ae[g:-g, g, g]])
        np.savetxt(os.path.join(out, "alp_profile.dat"), prof,
                   header=f"gauge wave, dx = {dx}, t = {sim.time:g}\n1:x 2:alpha 3:alpha_exact")
        print("saved", out)


def save_run(src, name):
    """Copy the ASCII outputs and metadata of a finished run into docs/data/<name>."""
    if not os.path.isdir(src):
        print(f"skip {name}: no run directory {src}")
        return
    out = os.path.join(DATA, name)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    files = glob.glob(os.path.join(src, "*.asc")) + glob.glob(os.path.join(src, "*.par"))
    files.append(os.path.join(src, "pynr.log"))
    for f in files:
        shutil.copy2(f, out)
    print(f"saved {len(files)} files to {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", nargs="?", default="plot", choices=["save", "plot", "all"])
    ap.add_argument("--runs", default=".", help="(save) directory containing finished runs")
    args = ap.parse_args()
    if args.step in ("save", "all"):
        save_gauge_wave()
        save_run(os.path.join(args.runs, "kerr_schild"), "kerr_schild")
        save_run(os.path.join(args.runs, "schwarzschild_perturbed"), "schwarzschild_perturbed")
    if args.step in ("plot", "all"):
        render_all()


if __name__ == "__main__":
    main()
