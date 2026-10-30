"""DEC-066 paper figures from EXISTING data (0 TDS): F1 M0 vs M3+OS classes and margins, F2 critical transients, F3 predictor validity (jump / 50 ms / 195 s vs TDS), F5 safety vs dispatch effort, F6 dispatch by resource.
Inputs: IEEE39_DEC066_T2b_cells.csv, IEEE39_DEC066_P1_traj_*.npz (predicted and stored TDS series), dispatch/prediction JSONs, DEC-054 prospective summary.  Output: figures_main/DEC066_F*.{pdf,png} (exclusive).
RMS/phasor (ANDES) results, not EMT.  Run: <venv python> dec066_paper_figures.py <f1|f2|f3|f5|f6|all> [preview]"""
from __future__ import annotations

import csv
import json
import os
import sys

import numpy as np

import dec054_common as C54
import dec055_common as C55
import dec059_figs as F59

BLUE, ORANGE, AQUA, YELLOW, INK, INK2, GRID = F59.BLUE, F59.ORANGE, F59.AQUA, F59.YELLOW, F59.INK, F59.INK2, F59.GRID
U_D8 = 0.0109
TE = 5.0
UNITS = C55.UNITS
STATE = C54.RUNS_DIR.parent
OUT = C55.FIG


def save(fig, name):
    prev = os.environ.get("DEC066_PREVIEW")
    if prev:
        fig.savefig(os.path.join(prev, f"{name}.png"), dpi=110, bbox_inches="tight")
        return
    for ext, kw in (("pdf", {}), ("png", {"dpi": 300})):
        with open(OUT / f"DEC066_{name}.{ext}", "xb") as f:
            fig.savefig(f, format=ext, bbox_inches="tight", **kw)


def traj(oc, m, cell):
    return np.load(C55.ART / f"IEEE39_DEC066_P1_traj_{oc}_{m}_{cell}.npz")


def cells():
    return list(csv.DictReader(open(C55.ART / "IEEE39_DEC066_T2b_cells.csv", encoding="utf-8")))


def margin_tds(z, unit):
    i = UNITS.index(unit)
    t = z["t_tds"] - TE
    return t, z["pmax"][i] - z["P_tds"][:, i]


# ------------------------------------------------------------------------------------------------------------------------------------------------ F1
def f1():
    plt = F59._plt()
    cs = cells()
    fig, ax = plt.subplots(1, 3, figsize=(7.4, 2.9), gridspec_kw={"width_ratios": [1.0, 1.5, 1.0]})
    groups = [("OC1", "M0", "OC1\nM0"), ("OC1", "M3REV3", "OC1\nM3+OS rev3"), ("OC2", "M0", "OC2\nM0"), ("OC2", "M3OS", "OC2\nM3+OS")]
    bot = np.zeros(len(groups))
    for cls, col in (("SAFE", BLUE), ("NUMERICALLY_INDETERMINATE", YELLOW), ("UNSAFE", ORANGE)):
        v = np.array([sum(c["class_observed"] == cls for c in cs if c["oc"] == o and c["dispatch"] == m) for o, m, _ in groups])
        ax[0].bar(range(len(groups)), v, bottom=bot, color=col, label={"NUMERICALLY_INDETERMINATE": "INDET."}.get(cls, cls), width=0.7)
        for i, (x, b0) in enumerate(zip(v, bot)):
            if x:
                ax[0].text(i, b0 + x / 2, str(x), ha="center", va="center", fontsize=7, color=INK)
        bot += v
    ax[0].set_xticks(range(len(groups)))
    ax[0].set_xticklabels([g[2] for g in groups], fontsize=6)
    ax[0].set(ylabel="blind cells (n = 9 per bar)", title="(a) observed class (TDS, 0-195 s)")
    ax[0].legend(fontsize=6, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.0), frameon=False)
    ax[0].set_ylim(0, 11)
    cells1 = [(b, s) for b in (21, 31, 39) for s in ("S1", "S2", "S3")]
    x = np.arange(9)
    for m, col, lab, off in (("M0", ORANGE, "M0", -0.12), ("M3REV3", BLUE, "M3+OS rev3", 0.12)):
        y = [float(next(c["m_all"] for c in cs if c["oc"] == "OC1" and c["dispatch"] == m and c["cell"] == f"b{b}P_{s}")) for b, s in cells1]
        ax[1].scatter(x + off, y, color=col, s=18, label=lab, zorder=3)
    for i, (b, s) in enumerate(cells1):
        y0 = float(next(c["m_all"] for c in cs if c["oc"] == "OC1" and c["dispatch"] == "M0" and c["cell"] == f"b{b}P_{s}"))
        y1 = float(next(c["m_all"] for c in cs if c["oc"] == "OC1" and c["dispatch"] == "M3REV3" and c["cell"] == f"b{b}P_{s}"))
        ax[1].plot([i - 0.12, i + 0.12], [y0, y1], color=GRID, lw=0.8, zorder=2)
    ax[1].axhspan(-U_D8, U_D8, color=GRID, zorder=0)
    ax[1].axhline(0, color=INK2, lw=0.6)
    ax[1].set_xticks(x)
    ax[1].set_xticklabels([f"b{b}\n{s}" for b, s in cells1], fontsize=6)
    ax[1].set(ylabel="worst observed Pmax margin (pu)", title="(b) OC1, same events, two dispatches")
    ax[1].legend(fontsize=6, loc="lower left")
    ax[1].annotate("b31: inadmissible at the jump\n(both dispatches)", xy=(4.0, -0.27), xytext=(2.1, -0.02), fontsize=6, arrowprops=dict(arrowstyle="-", color=INK2, lw=0.6))
    ax[1].text(8.4, -0.33, "redispatch of M3+OS rev3:\n101.07 MW vs M0\n(99.35 MW vs case dispatch)", fontsize=6, ha="right", va="center", color=INK)
    y = {}
    for m, col, off in (("M0", ORANGE, -0.12), ("M3OS", BLUE, 0.12)):
        yy = [float(next(c["m_all"] for c in cs if c["oc"] == "OC2" and c["dispatch"] == m and c["cell"] == f"b{b}P_{s}")) for b, s in cells1]
        ax[2].scatter(x + off, yy, color=col, s=14, zorder=3)
    ax[2].axhline(0, color=INK2, lw=0.6)
    ax[2].set_xticks(x)
    ax[2].set_xticklabels([f"{b}{s[1]}" for b, s in cells1], fontsize=5.5, rotation=90)
    ax[2].set(ylabel="worst observed Pmax margin (pu)", title="(c) OC2: dispatches differ by 0.06 MW")
    for a in ax:
        a.title.set_fontsize(7)
    fig.tight_layout()
    save(fig, "F1_M0_vs_M3OS")


# ------------------------------------------------------------------------------------------------------------------------------------------------ F2
def f2():
    plt = F59._plt()
    ev = [("b21P_S2", "SG35", "OC1 b21 S2 (M0 unsafe, rev3 safe)"), ("b39P_S2", "SG31", "OC1 b39 S2 (M0 false SAFE at 50 ms)"), ("b31P_S2", "SG31", "OC1 b31 S2 (inadmissible at the jump)")]
    wins = [(-0.002, 0.05, "0-50 ms"), (-0.1, 10.0, "0-10 s"), (-1.0, 195.0, "0-195 s")]
    fig, ax = plt.subplots(3, 3, figsize=(7.4, 6.0))
    for r, (cell, unit, title) in enumerate(ev):
        z0, z3 = traj("OC1", "M0", cell), traj("OC1", "M3REV3", cell)
        for c, (a0, a1, lab) in enumerate(wins):
            a = ax[r, c]
            for z, col, name in ((z0, ORANGE, "M0"), (z3, BLUE, "M3+OS rev3")):
                t, mg = margin_tds(z, unit)
                w = (t >= a0) & (t <= a1)
                a.plot(t[w], mg[w], color=col, lw=1.2, label=name)
            a.axhline(0, color=INK2, lw=0.7)
            a.axhspan(-U_D8, U_D8, color=GRID, zorder=0)
            a.set_xlim(a0 if a0 > 0 else a0, a1)
            if r == 0:
                a.set_title(f"time after event: {lab}", fontsize=7)
            if c == 0:
                a.set_ylabel(f"{unit} Pmax - P (pu)", fontsize=7)
                a.text(0.02, 0.97, title, transform=a.transAxes, fontsize=6.5, va="top", color=INK)
            if r == 2:
                a.set_xlabel("t - t_e (s)", fontsize=7)
    ax[0, 0].legend(fontsize=6, loc="lower right")
    fig.suptitle("Delivered power margin of the limiting unit, stored TDS series (ANDES RMS/phasor), t_e = 5 s; grey band: U_D8 = 0.0109 pu", fontsize=7.5)
    fig.tight_layout()
    save(fig, "F2_critical_transients")


# ------------------------------------------------------------------------------------------------------------------------------------------------ F3
def f3(m="M0", name="F3_predictor_validity"):
    plt = F59._plt()
    fig, ax = plt.subplots(2, 3, figsize=(7.4, 4.4))
    wins = [(-0.002, 0.05, "0-50 ms"), (-0.1, 10.0, "0-10 s"), (-1.0, 195.0, "0-195 s")]
    for r, cell in enumerate(("b39P_S2", "b39P_S3")):
        z = traj("OC1", m, cell)
        for c, (a0, a1, lab) in enumerate(wins):
            a = ax[r, c]
            for unit, ls in (("SG31", "-"), ("SG35", "--")):
                i = UNITS.index(unit)
                t, mg = margin_tds(z, unit)
                w = (t >= a0) & (t <= a1)
                a.plot(t[w], mg[w], color=INK, lw=1.1, ls=ls, label=f"{unit} TDS")
                tg = z["t"]
                wg = tg <= a1
                a.plot(tg[wg], (z["pmax"][i] - z["P_pred"][i])[wg], color=BLUE, lw=1.1, ls=ls, label=f"{unit} predictor 0-195 s")
                a.plot(z["t50"], z["pmax"][i] - z["P_pred50"][i], color=ORANGE, lw=1.4, ls=ls, label=f"{unit} dense 50 ms")
                a.scatter([0.0], [z["pmax"][i] - z["P_jump"][i]], color=AQUA, s=14, zorder=4, label="algebraic jump" if unit == "SG31" else None)
            a.axhline(0, color=INK2, lw=0.7)
            a.axhspan(-U_D8, U_D8, color=GRID, zorder=0)
            a.set_xlim(a0, a1)
            if m == "M0":
                a.set_ylim(-0.5, 0.2) if c == 2 else a.set_ylim(-0.1, 0.1)
            if r == 0:
                a.set_title(f"time after event: {lab}", fontsize=7)
            if c == 0:
                a.set_ylabel(f"OC1 {m} {cell[:3]} {cell[-2:]}: Pmax - P (pu)", fontsize=7)
            if r == 1:
                a.set_xlabel("t - t_e (s)", fontsize=7)
    h, l = ax[0, 0].get_legend_handles_labels()
    fig.legend(h, l, fontsize=6, ncol=4, loc="lower center", bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    save(fig, name)


# ------------------------------------------------------------------------------------------------------------------------------------------------ F6
def f6():
    plt = F59._plt()
    pm = {m: json.loads((C55.ART / f"IEEE39_DEC059_pred_OC1_{m}_test.json").read_text(encoding="utf-8"))["pre_event"]["P"] for m in ("M0", "M3REV3")}
    pmax = traj("OC1", "M0", "b21P_S1")["pmax"]
    d = (np.array(pm["M3REV3"]) - np.array(pm["M0"])) * 100
    hr0, hr3 = (pmax - np.array(pm["M0"])) * 100, (pmax - np.array(pm["M3REV3"])) * 100
    fig, ax = plt.subplots(1, 2, figsize=(7.4, 2.9))
    x = np.arange(10)
    ax[0].bar(x, d, color=[ORANGE if v < 0 else BLUE for v in d], width=0.7)
    ax[0].axhline(0, color=INK2, lw=0.6)
    ax[0].set_xticks(x)
    ax[0].set_xticklabels(UNITS, rotation=60, fontsize=6)
    ax[0].set(ylabel="pre-event P: rev3 - M0 (MW)", title="(a) pre-event P, rev3 - M0 (9 decision units: 101.1 MW; SG39 = slack)")
    ax[1].bar(x - 0.18, hr0, width=0.36, color=ORANGE, label="M0")
    ax[1].bar(x + 0.18, hr3, width=0.36, color=BLUE, label="M3+OS rev3")
    ax[1].set_xticks(x)
    ax[1].set_xticklabels(UNITS, rotation=60, fontsize=6)
    ax[1].set(ylabel="pre-event headroom Pmax - P (MW)", title="(b) headroom before the event")
    ax[1].legend(fontsize=6)
    for a in ax:
        a.title.set_fontsize(7)
    fig.tight_layout()
    save(fig, "F6_dispatch_by_unit")


# ------------------------------------------------------------------------------------------------------------------------------------------------ F5
def f5():
    plt = F59._plt()
    T1 = list(csv.DictReader(open(C55.ART / "IEEE39_DEC066_T1_dispatches.csv", encoding="utf-8")))
    s54 = json.loads((C55.ART / "IEEE39_DEC054_prospective_summary.json").read_text(encoding="utf-8"))["summary"]
    fig, ax = plt.subplots(1, 2, figsize=(7.4, 2.9))
    for lab, col in (("M0", ORANGE), ("M1", AQUA), ("M2", YELLOW), ("M3", BLUE)):
        r = next(x for x in T1 if x["source"] == "DEC054" and x["method"].startswith(lab))
        ax[0].scatter(float(r["sumdP_MW_vs_M0"]), s54[lab]["scenarios_with_P_violation"], color=col, s=34, zorder=3)
        ax[0].annotate(lab, (float(r["sumdP_MW_vs_M0"]), s54[lab]["scenarios_with_P_violation"]), textcoords="offset points", xytext=(5, 4), fontsize=7)
    ax[0].set(xlabel="sum |dP| vs M0 (MW)", ylabel="scenarios with Pmax violation (of 6)", title="(a) DEC-054 cohort: 6 buses, S2, 24 TDS", ylim=(-0.5, 6.7))
    cs = cells()
    for m, col, lab in (("M0", ORANGE, "M0"), ("M3REV3", BLUE, "M3+OS rev3")):
        n = sum(c["class_observed"] == "UNSAFE" for c in cs if c["oc"] == "OC1" and c["dispatch"] == m)
        mw = 0.0 if m == "M0" else float(next(x["sumdP_MW_vs_M0"] for x in T1 if x["method"] == "M3+OS rev3"))
        ax[1].scatter(mw, n, color=col, s=34, zorder=3)
        ax[1].annotate(lab, (mw, n), textcoords="offset points", xytext=(5, 4), fontsize=7)
    ax[1].set(xlabel="sum |dP| vs M0 (MW)", ylabel="UNSAFE cells (of 9)", title="(b) DEC-062 OC1: 9 blind cells (b31 inadmissible)", ylim=(-0.5, 9.5), xlim=(-8, 130))
    for a in ax:
        a.title.set_fontsize(7)
    fig.tight_layout()
    save(fig, "F5_safety_vs_dispatch_effort")


if __name__ == "__main__":
    w = sys.argv[1] if len(sys.argv) > 1 else "all"
    for k, f in (("f1", f1), ("f2", f2), ("f3", f3), ("f5", f5), ("f6", f6)):
        if w in (k, "all"):
            f()
    if w in ("f3b", "all"):
        f3("M3REV3", "F3b_predictor_validity_rev3")
