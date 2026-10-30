"""DEC-062 figures (exclusive PNG writes in figures_main/; preview mode via DEC059_FIG_PREVIEW).  Palette: validated default categorical order (blue, orange, aqua, yellow).
  margins   F8   TEST: min Pmax margin in the first 50 ms per cell, TDS vs prediction, M0 vs M3+OS, per OC (U_D8 band, INADMISSIBLE cells marked)
  compare   F9   controller comparison on the S2 TEST cells: f_COI and unit-voltage error in time for one reference cell, control effort and final voltage error for all cells
  t1t2      F10  T1 (min reference margin c_j) and T2 (Lyapunov value ratio) over every B5'/B4' run
  pred      F11  predicted vs TDS margin on all TEST runs of cohort A and the predicted/observed class table (P3 level O)
  <venv python> dec062_figs.py <name>"""
from __future__ import annotations

import json
import sys

import numpy as np

import dec054_common as C54
import dec055_common as C55
import dec059_figs as F59
import dec059_tds as T
import dec062_r5 as R5

BLUE, ORANGE, AQUA, YELLOW = F59.BLUE, F59.ORANGE, F59.AQUA, F59.YELLOW
INK, INK2, GRID = F59.INK, F59.INK2, F59.GRID
TE = C54.EVENT_T
U_D8 = 0.0109


def _res():
    return json.loads((C55.ART / "IEEE39_DEC062_TEST_results.json").read_text(encoding="utf-8"))


def _save(fig, name):
    import os
    if os.environ.get("DEC059_FIG_PREVIEW"):
        fig.savefig(os.path.join(os.environ["DEC059_FIG_PREVIEW"], f"{name}.png"), dpi=200, bbox_inches="tight")
        return
    with open(C55.FIG / f"IEEE39_DEC062_{name}.png", "xb") as f:
        fig.savefig(f, dpi=200, format="png", bbox_inches="tight")


def fig_margins():
    plt = F59._plt()
    r = _res()
    fig, ax = plt.subplots(1, 2, figsize=(7.4, 3.2), sharey=False)
    for a, oc in zip(ax, ("OC1", "OC2")):
        cells = r["A"][f"{oc}_M0"]["cells"]
        names = [c["run_id"].split("_")[-2] + " " + c["run_id"].split("_")[-1] for c in cells]
        x = np.arange(len(cells))
        for off, m, col, lab in ((-0.18, "M0", ORANGE, "M0"), (0.18, R5.DES[oc], BLUE, "M3+OS")):
            cs = r["A"][f"{oc}_{m}"]["cells"]
            y = np.array([c["m50"] for c in cs])
            a.scatter(x + off, y, s=16, color=col, label=f"{lab} TDS", zorder=3)
            a.scatter(x + off, [c["pred_margin"] for c in cs], s=60, facecolors="none", edgecolors=col, marker="s", linewidths=0.8, zorder=2)
            for xi, c in zip(x + off, cs):
                if c["admissible_at_jump_pred"] is False:
                    a.scatter([xi], [c["m50"]], s=70, facecolors="none", edgecolors=INK, linewidths=0.9, zorder=4)
        a.axhspan(-U_D8, U_D8, color=GRID, zorder=0)
        a.axhline(0, color=INK2, lw=0.6)
        a.set_xticks(x)
        a.set_xticklabels(names, rotation=90, fontsize=6)
        a.set(ylabel="min Pmax margin, first 50 ms (pu)", title=oc)
        a.title.set_fontsize(7)
    ax[0].legend(fontsize=6.5, loc="lower left")
    fig.suptitle("TEST (blind, modified access rule): Pmax margin in the first 50 ms. Dots TDS, squares prediction, rings inadmissible at the jump", fontsize=7.5)
    fig.tight_layout()
    _save(fig, "F8_TEST_margins")


def _series(run):
    z = np.load(T.RUNS / run / "series.npz", allow_pickle=True)
    t = z["t"]
    vu = z["V"][:, [b - 1 for b in C54.UNIT_BUS]]
    fc = z["f_coi_hz"] if "f_coi_hz" in z and len(z["f_coi_hz"]) == len(t) else z["f_bus_hz"].mean(axis=1)
    return t, fc, np.abs(vu - vu[0][None, :]).max(axis=1)


def fig_compare():
    plt = F59.plt if hasattr(F59, "plt") else F59._plt()
    plt = F59._plt()
    r = _res()
    oc, b = "OC1", 21
    runs = {"B5'": f"D62TEST_B5P_{oc}_{R5.DES[oc]}_b{b}P_S2", "B4'": f"D62CMP_B4P_{oc}_{R5.DES[oc]}_b{b}P_S2", "B2": f"D62CMP_B2_{oc}_{R5.DES[oc]}_b{b}P_S2", "B1s": f"D62CMP_B1S_{oc}_{R5.DES[oc]}_b{b}P_S2"}
    cols = {"B5'": BLUE, "B4'": AQUA, "B2": ORANGE, "B1s": YELLOW}
    fig, ax = plt.subplots(2, 2, figsize=(7.4, 5.2))
    for k, run in runs.items():
        t, fc, ev = _series(run)
        ax[0, 0].plot(t, (fc - 60) * 1e3, color=cols[k], label=k, lw=1.3)
        ax[0, 1].semilogy(t[t >= TE], np.maximum(ev[t >= TE], 1e-6), color=cols[k], label=k, lw=1.3)
    ax[0, 0].set(xlim=(4, 60), xlabel="time (s)", ylabel="f_COI - 60 Hz (mHz)", title=f"(a) {oc} TEST b{b} S2, {R5.DES[oc]}")
    ax[0, 1].set(xlabel="time (s)", ylabel="max |V - V(0)| over units (pu)", title="(b) unit-voltage deviation")
    for a in ax[0]:
        a.legend(fontsize=6.5)
        a.axvline(TE, color=INK2, lw=0.6, ls=":")
    cmpd = r["comparison"]
    keys = list(cmpd)
    x = np.arange(len(keys))
    for i, (k, lab) in enumerate((("B5P@M3+OS", "B5'"), ("B4P", "B4'"), ("B2", "B2"), ("B1S", "B1s"))):
        ax[1, 0].bar(x + (i - 1.5) * 0.2, [cmpd[c][k]["P_TV"] for c in keys], width=0.2, color=cols[lab], label=lab)
        ax[1, 1].bar(x + (i - 1.5) * 0.2, [cmpd[c][k]["unitV_err_vs_setpoint_max"] * 1e3 for c in keys], width=0.2, color=cols[lab])
    for a in ax[1]:
        a.set_xticks(x)
        a.set_xticklabels([k.replace("_", " ") for k in keys], rotation=45, ha="right", fontsize=6)
    ax[1, 0].set(ylabel="P set-point total variation (pu)", title="(c) control effort")
    ax[1, 1].set(ylabel="unit-V error to set-point, 200 s (mpu)", title="(d) end-of-run voltage offset")
    fig.tight_layout()
    _save(fig, "F9_TEST_controller_comparison")


def fig_t1t2():
    plt = F59._plt()
    r = _res()
    rows = [c for k in r["A"] for c in r["A"][k]["cells"]] + [v for oc in r["B"] for cell in r["B"][oc] for n, v in r["B"][oc][cell].items() if n == "B4P"]
    fig, ax = plt.subplots(1, 2, figsize=(7.4, 2.9))
    x = np.arange(len(rows))
    ax[0].scatter(x, [c["T1_min_c"] for c in rows], s=12, color=BLUE)
    ax[0].axhline(0, color=INK2, lw=0.8)
    ax[0].set(xlabel="B5'/B4' run", ylabel="min_j c_j(u_k) over all samples (pu)", title="(a) T1: reference margins never negative")
    withv = [i for i, c in enumerate(rows) if c["T2_V_ratio_end_over_first"] is not None]          # B4' has no CLF row, hence no Lyapunov value
    ax[1].semilogy(withv, [rows[i]["T2_V_ratio_end_over_first"] for i in withv], "o", ms=3.5, color=ORANGE)
    ax[1].axhline(1, color=INK2, lw=0.8)
    ax[1].set(xlabel="B5' run (B4' has no CLF row)", ylabel="V(end) / V(first valid)", title="(b) T2: Lyapunov value decays (local statement)")
    fig.tight_layout()
    _save(fig, "F10_T1_T2_checks")


def fig_pred():
    plt = F59._plt()
    r = _res()
    rows = [c for k in r["A"] for c in r["A"][k]["cells"]]
    fig, ax = plt.subplots(1, 2, figsize=(7.4, 3.2))
    a = ax[0]
    lo, hi = min(min(c["pred_margin"], c["m50"]) for c in rows) - 0.03, max(max(c["pred_margin"], c["m50"]) for c in rows) + 0.03
    a.axvspan(-U_D8, U_D8, color=GRID, zorder=0)
    a.axhspan(-U_D8, U_D8, color=GRID, zorder=0)
    a.plot([lo, hi], [lo, hi], color=INK2, lw=0.8, ls="--")
    for c in rows:
        a.scatter(c["pred_margin"], c["m50"], s=20, color=BLUE if c["admissible_at_jump_pred"] else ORANGE, edgecolor=INK if c["class"] == "UNSAFE" else "none", linewidth=0.8)
    a.set(xlim=(lo, hi), ylim=(lo, hi), xlabel="predicted min Pmax margin (pu)", ylabel="TDS min Pmax margin, 50 ms (pu)", title="(a) blue admissible, orange inadmissible; outline UNSAFE")
    a.title.set_fontsize(7)
    b = ax[1]
    labs = ["SAFE", "NUMERICALLY_INDETERMINATE", "UNSAFE"]
    M = np.zeros((3, 3), int)
    for c in rows:
        M[labs.index(c["pred_class"]), labs.index(c["class"])] += 1
    b.imshow(M, cmap="Blues")
    for i in range(3):
        for j in range(3):
            b.text(j, i, str(M[i, j]), ha="center", va="center", color=INK, fontsize=9)
    b.set_xticks(range(3))
    b.set_xticklabels(["SAFE", "INDET", "UNSAFE"], fontsize=7)
    b.set_yticks(range(3))
    b.set_yticklabels(["SAFE", "INDET", "UNSAFE"], fontsize=7)
    b.set(xlabel="class observed in TDS", ylabel="class predicted before TDS", title="(b) cohort A, 36 cells")
    b.grid(False)
    fig.tight_layout()
    _save(fig, "F11_TEST_prediction_vs_TDS")


if __name__ == "__main__":
    {"margins": fig_margins, "compare": fig_compare, "t1t2": fig_t1t2, "pred": fig_pred}[sys.argv[1]]()
