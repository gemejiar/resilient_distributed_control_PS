"""DEC-059 figures (exclusive PNG writes in figures_main/).  Palette: the validated default categorical order (blue, orange, aqua, yellow); one y-axis per panel.
  os      F4  sub-cycle overshoot: dense post-jump model vs TDS (dt/16) vs the dt grid of M3; margin errors on the 18 calibration cells
  smoke   F7  B5' smoke OC1/OC2 M0 b8P_S2: f_COI, unit-voltage error to the target, Lyapunov value V(t), reference margin min c_j(t)
  oc3     F5  OC3 M0 outside the T2 hypotheses: SG30 Qset deviation from the target vs exp(+0.0207 t); rightmost non-null eigenvalue of every target"""
from __future__ import annotations

import json
import sys

import numpy as np

import dec054_common as C54
import dec055_common as C55

BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
TE = C54.EVENT_T
RUNS = C54.RUNS_DIR.parent / "DEC059_runs"
ST = C54.RUNS_DIR.parent / "DEC059_state"


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 8, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True,
                         "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 1.6, "legend.frameon": False})
    return plt


def _save(fig, name):
    import os
    if os.environ.get("DEC059_FIG_PREVIEW"):                  # inspection copy (overwritable) before the exclusive final write
        fig.savefig(os.path.join(os.environ["DEC059_FIG_PREVIEW"], f"{name}.png"), dpi=200, bbox_inches="tight")
        return
    with open(C55.FIG / f"IEEE39_DEC059_{name}.png", "xb") as f:
        fig.savefig(f, dpi=200, format="png", bbox_inches="tight")


def fig_os():
    import dec054_opf as OPF
    import dec054_predictor as PRD
    import dec055_oc as OCM
    import dec057_tds as T7
    plt = _plt()
    cal = json.loads((C55.ART / "IEEE39_DEC059_OS_calibration.json").read_text(encoding="utf-8"))
    z = np.array(json.loads((C54.RUNS_DIR.parent / "DEC056_state" / "oc3_seeded_full.json").read_text(encoding="utf-8"))["z"])
    plant = OCM.make_plant("OC3")
    S = OPF.Scenario("b8P_S3", 8, "P", 0.87846)
    jp = plant.jump(z, S)
    A, f, Cm = plant.affine(z, S)
    td, Dd, _ = PRD.propagate(A, f, Cm, [[0.0, 0.05, C54.DT / 64, "exact"]])
    tg, Dg, _ = PRD.propagate(A, f, Cm, [[0.0, 0.05, C54.DT, "trap"]])
    s = np.load(T7.RUNS / "D57M3V_B2_b8P_S3" / "series.npz")
    k = (s["t"] >= TE - C54.DT) & (s["t"] <= TE + 0.05)
    i = 1                                                       # SG31
    pmax = plant.limits["pmax"][i]
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.7))
    a = ax[0]
    a.plot((s["t"][k] - TE) * 1e3, s["P"][k][:, i], color=BLUE, marker="o", ms=2.5, lw=1.0, label="TDS, trapezoid dt/16")
    a.plot(td * 1e3, jp["P_plus"][i] + Dd[i], color=ORANGE, lw=1.6, label="post-jump linear model, dense")
    a.plot(tg * 1e3, jp["P_plus"][i] + Dg[i], color=AQUA, marker="s", ms=3, lw=1.0, label="same model on the M3 grid (dt)")
    a.axhline(pmax, color=INK2, lw=0.8, ls="--")
    a.text(50, pmax, "Pmax", color=INK2, ha="right", va="bottom", fontsize=7)
    a.set(xlabel="time after the event (ms)", ylabel="SG31 active power (pu)", title="(a) OC3 M3, DESIGN b8P_S3")
    a.legend(fontsize=6.5, loc="lower right")
    b = ax[1]
    cells = cal["cells"]
    x = np.arange(len(cells))
    b.scatter(x, cal["summary"]["pmax_margin_error_dtgrid_minus_tds"], s=14, color=AQUA, label="M3 grid (dt) - TDS")
    b.scatter(x, cal["summary"]["pmax_margin_error_dense_minus_tds"], s=14, color=ORANGE, label="dense model - TDS")
    b.axhline(0, color=INK2, lw=0.8)
    b.set(xlabel="calibration cell (DESIGN / TUNE)", ylabel="min Pmax margin error (pu)", title="(b) predicted minus simulated margin")
    b.legend(fontsize=6.5)
    fig.tight_layout()
    _save(fig, "F4_overshoot_model")


def fig_smoke():
    plt = _plt()
    fig, ax = plt.subplots(2, 2, figsize=(7.2, 4.8))
    for run, col, lab in (("D59S2_B5P_OC1_M0_b8P_S2", BLUE, "OC1"), ("D59S3_B5P_OC2_M0_b8P_S2", ORANGE, "OC2")):
        z = np.load(RUNS / run / "series.npz", allow_pickle=True)
        cfg = json.loads((RUNS / run / "config.json").read_text(encoding="utf-8"))
        Tg = dict(np.load(cfg["b5"]["post_target"]))
        t = z["t"]
        fc = z["f_coi_hz"]
        ax[0, 0].plot(t, (fc - 60.0) * 1e3, color=col, label=lab)
        vu = z["V"][:, [b - 1 for b in C54.UNIT_BUS]]
        kk = t >= TE
        ax[0, 1].semilogy(t[kk], np.abs(vu[kk] - Tg["V"][None, :]).max(axis=1), color=col, label=lab)
        V = z["b5_V"]
        ok = np.isfinite(V)
        ax[1, 0].semilogy(z["b5_t"][ok], V[ok], color=col, label=lab)
        ax[1, 1].plot(z["b5_t"], z["b5_c_min"], color=col, label=lab)
    ax[0, 0].set(xlim=(0, 60), xlabel="time (s)", ylabel="f_COI - 60 Hz (mHz)", title="(a) frequency, event at 5 s")
    ax[0, 1].set(xlabel="time (s)", ylabel="max |V_i - V_i*| (pu)", title="(b) unit-bus voltage error to the target")
    ax[1, 0].set(xlabel="time (s)", ylabel="V(e) (quotient Lyapunov value)", title="(c) Lyapunov value after the target switch")
    ax[1, 1].set(xlabel="time (s)", ylabel="min_j c_j(u_k) (pu)", title="(d) reference-set margin (T1: never negative)")
    for a in ax.ravel():
        a.axvline(TE, color=INK2, lw=0.6, ls=":")
        a.legend(fontsize=7)
    fig.tight_layout()
    _save(fig, "F7_B5prime_smoke")


def fig_oc3():
    plt = _plt()
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.7))
    z = np.load(RUNS / "D59S4_B5P_OC3_M0_b8P_S2" / "series.npz", allow_pickle=True)
    cfg = json.loads((RUNS / "D59S4_B5P_OC3_M0_b8P_S2" / "config.json").read_text(encoding="utf-8"))
    Tg = dict(np.load(cfg["b5"]["post_target"]))
    ct = z["cmd_t"]
    dq = np.abs(z["cmd_qset"][:, 0] - Tg["u"][10])
    a = ax[0]
    a.semilogy(ct, np.maximum(dq, 1e-8), color=BLUE, label="B5', |Qset SG30 - Qset*|")
    k = (ct > 60) & (ct < 190)
    j = np.where(k)[0][0]
    a.semilogy(ct[k], dq[j] * np.exp(0.0207 * (ct[k] - ct[j])), color=ORANGE, ls="--", label="exp(+0.0207 t), target eigenvalue")
    a.set(xlabel="time (s)", ylabel="deviation (pu)", title="(a) OC3 M0 b8P_S2: target unstable (H4/H5 fail)")
    a.legend(fontsize=6.5)
    b = ax[1]
    tags = ["r2_OC1_M0_d0", "r2_OC1_M0_b8P_0.58564", "r2_OC2_M0_d0", "r2_OC2_M0_b8P_0.58564", "r2_OC3_M0_d0", "r2_OC3_M0_b8P_0.58564"]
    re = [json.loads((ST / f"target_{t}.json").read_text(encoding="utf-8"))["T2"]["H5_continuous"]["rightmost_excl_null"][0][0] for t in tags]
    lab = ["OC1 d0", "OC1 b8S2", "OC2 d0", "OC2 b8S2", "OC3 d0", "OC3 b8S2"]
    b.barh(lab, re, color=[BLUE if r < 0 else ORANGE for r in re], height=0.6)
    b.axvline(0, color=INK2, lw=0.8)
    for y, r in enumerate(re):
        b.text(max(r, 0.0) + 0.0003, y, f"{r:+.4f}", va="center", ha="left", fontsize=6.5, color=INK)
    b.set(xlabel="rightmost non-null eigenvalue, Re (1/s)", title="(b) closed-loop spectrum at the targets")
    fig.tight_layout()
    _save(fig, "F5_targets_OC3")


if __name__ == "__main__":
    {"os": fig_os, "smoke": fig_smoke, "oc3": fig_oc3}[sys.argv[1]]()
