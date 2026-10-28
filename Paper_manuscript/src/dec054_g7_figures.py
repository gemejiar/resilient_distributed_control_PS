"""DEC-054 G7 figures (from stored artefacts; no TDS).  Writes figures_main/IEEE39_DEC054_{jump_vs_slow,security_cost_pareto,prospective_comparison}.png (exclusive)."""
from __future__ import annotations

import csv
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import dec054_common as COM

COL = {"M0": "tab:red", "M1": "tab:orange", "M2": "tab:blue", "M3": "tab:green"}
LIM_PMAX = np.array([10.4, 6.5, 6.82, 6.97, 8.65, 11.0, 7.5, 5.64, 5.5, 5.95])


def savefig(fig, name):
    path = COM.FIG / name
    with open(path, "xb") as f:
        fig.savefig(f, dpi=150, format="png")
    plt.close(fig)


def main():
    frozen = json.loads((COM.ART / "IEEE39_DEC054_design_frozen.json").read_text(encoding="utf-8"))
    summ = json.loads((COM.ART / "IEEE39_DEC054_prospective_summary.json").read_text(encoding="utf-8"))["summary"]
    g4 = json.loads((COM.ART / "IEEE39_DEC054_g4_design_summary.json").read_text(encoding="utf-8"))["states"]
    rows = list(csv.DictReader(open(COM.ART / "IEEE39_DEC054_prospective_tests.csv", encoding="utf-8")))
    # 1. jump vs slow excursion: SG31 and SG35 on bus 12 (largest observed SG31 excess under M0)
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
    for k, (u, i) in enumerate((("SG31", 1), ("SG35", 3))):
        for m in ("M0", "M2", "M3"):
            z = np.load(COM.RUNS_DIR / f"P3-C_bus12P_{m}" / "series.npz")
            t, P = z["t"], z["P"][:, i]
            ax[k].plot(t, P, c=COL[m], lw=1, label=m)
        ax[k].axhline(LIM_PMAX[i], c="k", ls="--", lw=1)
        ax[k].set(xlim=(4.9, 12), xlabel="t (s)", ylabel="P (pu, system base)", title=f"{u}, P step at bus 12 (frozen dispatches)")
        ax[k].legend(fontsize=7)
        ax[k].annotate("Pmax", (11, LIM_PMAX[i]), fontsize=7)
    fig.tight_layout()
    savefig(fig, "IEEE39_DEC054_jump_vs_slow.png")
    # 2. security-cost
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
    grid = sorted([(g["rho"], g["describe"]["J"], g["describe"]["n_violated_margins"], g["describe"]["redispatch_MW_abs_sum"]) for k in ("m1", "m1b") for g in g4[k]["grid"] if "describe" in g])
    ax[0].plot([g[1] for g in grid], [g[2] for g in grid], "o-", c=COL["M1"], label="M1 grid (predicted violated margins)")
    for g in grid:
        ax[0].annotate(f"{g[0]:g}", (g[1], g[2]), fontsize=6)
    for m in ("M0", "M2", "M3"):
        d = g4[m.lower()]["describe"]
        ax[0].scatter([d["J"]], [d["n_violated_margins"]], c=COL[m], s=60, label=f"{m} (predicted)")
    ax[0].set(xlabel="design cost J (identical objective)", ylabel="predicted violated margins (8 design events)", xscale="log", title="design set: security vs cost")
    ax[0].legend(fontsize=7)
    for m in COL:
        ax[1].scatter([summ[m]["design_J"]], [summ[m]["violating_pairs_P"]], c=COL[m], s=90, label=m)
        ax[1].annotate(f"{summ[m]['violating_pairs_P']} pairs", (summ[m]["design_J"], summ[m]["violating_pairs_P"]), fontsize=8, xytext=(4, 4), textcoords="offset points")
    ax[1].set(xlabel="design cost J", ylabel="observed (scenario, unit) P violations, 6 prospective scenarios", xscale="log", title="prospective cohort (frozen dispatches)")
    ax[1].legend(fontsize=7)
    fig.tight_layout()
    savefig(fig, "IEEE39_DEC054_security_cost_pareto.png")
    # 3. prospective comparison: min Pmax margin of SG31 and SG35 per scenario and method
    sc = [s["name"] for s in frozen["scenarios_test"]["scenarios"]]
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
    for k, u in enumerate(("SG31", "SG35")):
        x = np.arange(len(sc))
        for j, m in enumerate(("M0", "M1", "M2", "M3")):
            v = [float(r["min_margin_Pmax_pu"]) for s in sc for r in rows if r["method"] == m and r["scenario"] == s and r["unit"] == u]
            ax[k].bar(x + (j - 1.5) * 0.2, v, 0.2, color=COL[m], label=m)
        ax[k].axhline(0, c="k", lw=0.8)
        ax[k].set_xticks(x, [s.replace("P", "") for s in sc], fontsize=8)
        ax[k].set(ylabel="min (Pmax - P) after the event (pu)", title=f"{u}: observed minimum margin, prospective cohort")
        ax[k].legend(fontsize=7)
    fig.tight_layout()
    savefig(fig, "IEEE39_DEC054_prospective_comparison.png")
    print("figures written")


if __name__ == "__main__":
    main()
