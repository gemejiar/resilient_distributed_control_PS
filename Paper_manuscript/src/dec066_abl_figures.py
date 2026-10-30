"""DEC-066 A1: preliminary F4 (OPF-level ablation, 0 TDS) from IEEE39_DEC066_ablation_raw.json and the T4* CSV files.  Writes figures_main/DEC066_F4_prelim.{pdf,png} and
artifacts/IEEE39_DEC066_F4_data.csv (the numbers plotted).  Run: <venv python> dec066_abl_figures.py write"""
from __future__ import annotations

import csv
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import dec055_common as C55

ART = C55.ART
FIG = ART.parent / "figures_main"
U_D8 = 0.0109
COL = {"A": "#4d4d4d", "B": "#0072B2", "C": "#56B4E9", "D": "#D55E00", "E": "#009E73"}
LAB = {"A": "A  M3", "B": "B  +dense", "C": "C  +dense+$\\varepsilon_{OS}$", "D": "D  M3+OS", "E": "E  $U_{D8}$ only"}


def main(write=False):
    raw = json.loads((ART / "IEEE39_DEC066_ablation_raw.json").read_text(encoding="utf-8"))
    t4 = list(csv.DictReader(open(ART / "IEEE39_DEC066_T4_OPF_ablation.csv", encoding="utf-8")))
    reg = {r["event"]: r for r in csv.DictReader(open(ART / "IEEE39_DEC066_T4c_prediction_register.csv", encoding="utf-8"))}
    units, pmax = raw["units"], np.array(raw["pmax"])
    des = [i for i, e in enumerate(raw["events"]) if e["role"] == "design"]
    K = "ABCDE"
    fig, ax = plt.subplots(2, 2, figsize=(10.5, 7.4))
    # (a) effort
    a = ax[0, 0]
    x = np.arange(5)
    a.bar(x, [float(r["sumdP_vs_case_MW"]) for r in t4], color=[COL[k] for k in K])
    a.set_xticks(x, [k for k in K]); a.set_ylabel("$\\sum|\\Delta P|$ vs case dispatch (MW)")
    a.set_ylim(50, 63)
    a2 = a.twinx(); a2.plot(x, [float(r["J"]) for r in t4], "ko-", ms=4); a2.set_ylabel("J (normalised cost)"); a2.set_ylim(1.66, 1.78)
    a.set_title("(a) Redispatch effort and cost (bars: MW, line: J)", fontsize=9)
    # (b) common external margin
    b = ax[0, 1]
    v = [float(r["ext_min_margin_dense_noeps"]) for r in t4]
    g = [float(r["ext_min_margin_gridonly"]) for r in t4]
    b.bar(x - 0.18, g, 0.36, color="#bbbbbb", label="grid only (M3 view)")
    b.bar(x + 0.18, v, 0.36, color=[COL[k] for k in K], label="dense + grid, no $\\varepsilon$")
    b.axhline(0, color="k", lw=0.8); b.axhspan(-U_D8, U_D8, color="#dddddd", alpha=0.5, lw=0)
    b.set_xticks(x, [k for k in K]); b.set_ylabel("min predicted margin (pu)")
    b.set_title("(b) Common external diagnostic (band: $\\pm U_{D8}$, numerical)", fontsize=9); b.legend(fontsize=7, loc="upper left")
    # (c) predicted 0-50 ms margin in discriminating evaluation events
    c = ax[1, 0]
    evs = ["b21P_S3", "b15P_S3", "b21P_S2", "b18P_S3"]
    w = 0.16
    for i, k in enumerate(K):
        c.bar(np.arange(len(evs)) + (i - 2) * w, [float(reg[e][f"{k}_m50ms"]) for e in evs], w, color=COL[k], label=LAB[k])
    c.axhline(0, color="k", lw=0.8); c.axhspan(-U_D8, U_D8, color="#dddddd", alpha=0.5, lw=0)
    c.set_xticks(range(len(evs)), [e.replace("P_", " ") for e in evs]); c.set_ylabel("predicted 0-50 ms Pmax margin (pu)")
    c.set_title("(c) Evaluation events: predicted only, no TDS", fontsize=9); c.legend(fontsize=6.5, ncol=2)
    # (d) dense gain per unit/event (max over events by unit, variant A) and active constraints
    d = ax[1, 1]
    names = [(raw["events"][i]["name"], j) for i in des for j in range(10)]
    ev = raw["rows"]["A"]["events"]
    dE = np.array([[max(ev[i]["E_dense_up"][j] - ev[i]["E_grid_up"][j], 0.0) for j in range(10)] for i in des])
    byu = dE.max(axis=0)
    ord_ = np.argsort(-byu)[:6]
    d.barh(range(len(ord_)), byu[ord_], color="#0072B2")
    d.set_yticks(range(len(ord_)), [units[j] for j in ord_]); d.invert_yaxis()
    d.set_xlabel("max $\\Delta E_{dense}=\\max(0,E_{dense}-E_{grid})$ over design events (pu)")
    d.set_title("(d) Where the 0-50 ms term changes the constraint (variant A)", fontsize=9)
    fig.suptitle("F4 (preliminary, OPF level, 0 TDS): ablation of the M3+OS components (predictions, not observations)", fontsize=10)
    fig.tight_layout()
    if write:
        fig.savefig(FIG / "DEC066_F4_prelim.pdf"); fig.savefig(FIG / "DEC066_F4_prelim.png", dpi=300)
        with open(ART / "IEEE39_DEC066_F4_data.csv", "x", newline="", encoding="utf-8") as fh:
            w_ = csv.writer(fh)
            w_.writerow(["variant", "sumdP_vs_case_MW", "J", "ext_margin_dense_noeps", "ext_margin_gridonly"])
            for r in t4:
                w_.writerow([r["variant"], r["sumdP_vs_case_MW"], r["J"], r["ext_min_margin_dense_noeps"], r["ext_min_margin_gridonly"]])
        print("max dE by unit:", {units[j]: round(float(byu[j]), 4) for j in ord_})


if __name__ == "__main__":
    main("write" in sys.argv)
