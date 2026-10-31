"""DEC-066 T7 (equal-effort comparison, 0 TDS): D vs EQ1 (uniform band U tuned to the redispatch of D) and E vs DQ1 (dense+eps_OS with a smaller band tuned to the redispatch of E),
all evaluated with the same external predictor (grid+dense excursion, no eps margin) over the same 12 design + 16 evaluation events.
Inputs: IEEE39_DEC066_ablation_raw.json (A..E), IEEE39_DEC066_budget_raw.json (EQ1, DQ1), design states.  Outputs (exclusive): IEEE39_DEC066_T7_equal_effort.csv (design level),
IEEE39_DEC066_T7b_equal_effort_events.csv (per event), IEEE39_DEC066_F8_prelim.{pdf,png}.   Run: <venv python> dec066_t7.py write"""
from __future__ import annotations

import csv
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import dec054_common as C54
import dec055_common as C55

ART = C55.ART
ST = C54.RUNS_DIR.parent
U_D8 = 0.0109
STATE = {"A": ST / "DEC055_state/m3_OC1.json", "D": ST / "DEC059_state/m3os_OC1.json", "E": ST / "DEC066_state/abl_E_OC1.json", "EQ1": ST / "DEC066_state/bud_EQ1_OC1.json", "DQ1": ST / "DEC066_state/bud_DQ1_OC1.json"}
COL = {"A": "#4d4d4d", "D": "#D55E00", "EQ1": "#CC79A7", "E": "#009E73", "DQ1": "#0072B2"}
LAB = {"A": "A  M3", "D": "D  M3+OS (U=0.0109)", "EQ1": "EQ1  U only, U=0.0193 (effort of D)", "E": "E  U only, U=0.0109", "DQ1": "DQ1  dense+eps_OS, U=0.0044 (effort of E)"}


def load():
    a = json.loads((ART / "IEEE39_DEC066_ablation_raw.json").read_text(encoding="utf-8"))
    b = json.loads((ART / "IEEE39_DEC066_budget_raw.json").read_text(encoding="utf-8"))
    return a, b


def margins(raw, k, pmax):
    ev = raw["rows"][k]["events"]
    g = lambda key: np.array([e[key] for e in ev])
    Pp, Eg, Ed = g("P_plus"), g("E_grid_up"), g("E_dense_up")
    ok = np.array([e["pred_ok"] for e in ev])
    full = pmax - Pp - np.maximum(Eg, Ed)                    # external margin, grid + dense excursion, no eps
    gridonly = pmax - Pp - Eg
    return full, gridonly, ok, Pp


def wr(name, rows):
    with open(ART / name, "x", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


def main(write=False):
    a, b = load()
    units = a["units"]; pmax = np.array(a["pmax"])
    names = [e["name"] for e in a["events"]]; role = [e["role"] for e in a["events"]]
    assert names == [e["name"] for e in b["events"]]
    src = {"A": a, "D": a, "E": a, "EQ1": b, "DQ1": b}
    st = {k: json.loads(p.read_text(encoding="utf-8")) for k, p in STATE.items()}
    zref = np.array(json.loads((ST / "DEC055_state/m0_OC1.json").read_text(encoding="utf-8"))["z_ref"])
    M = {k: margins(src[k], k, pmax) for k in STATE}
    des = [i for i, r in enumerate(role) if r == "design"]
    rows = []
    for k in STATE:
        full, grid, ok, Pp = M[k]
        z = np.array(st[k]["z"])
        i, j = np.unravel_index(full[des].argmin(), full[des].shape)
        allm = np.where(ok, full.min(axis=1), np.nan)
        rows.append({"design": k, "label": LAB[k], "status": st[k]["status"], "J": round(st[k]["J"], 5), "kkt": round(float(st[k]["kkt"]), 4), "sumdP_vs_case_MW": round(float(np.abs(z[:9] - zref[:9]).sum() * 100), 3),
                     "dJ_vs_A": round(st[k]["J"] - st["A"]["J"], 5), "ext_min_margin_design": round(float(full[des].min()), 5), "ext_unit": units[j], "ext_event": names[des[i]],
                     "n_events_margin_lt_0": int(np.nansum(allm < 0)), "n_events_margin_lt_minUD8": int(np.nansum(allm < -U_D8)), "n_events_margin_lt_UD8": int(np.nansum(allm < U_D8)), "n_events": int(ok.sum())})
    ev_rows = []
    for e, n in enumerate(names):
        r = {"event": n, "role": role[e]}
        for k in STATE:
            full, grid, ok, Pp = M[k]
            r[f"{k}_m"] = round(float(full[e].min()), 5) if ok[e] else ""
            r[f"{k}_unit"] = units[int(full[e].argmin())] if ok[e] else ""
        ev_rows.append(r)
    for r in rows:
        print(r)
    sel = [r for r in ev_rows if r["event"] in ("b8P_S3", "b21P_S3", "b15P_S3", "b23P_S3", "b18P_S2", "b18P_S3", "b31P_S2", "b21P_S2")]
    for r in sel:
        print({k: v for k, v in r.items() if k.endswith("_m") or k == "event"})
    # contrast summary: positive = second design has larger margin
    for x, y in (("D", "EQ1"), ("EQ1", "D"), ("E", "DQ1"), ("DQ1", "E")):
        dm = np.array([float(r[f"{x}_m"]) - float(r[f"{y}_m"]) for r in ev_rows if r[f"{x}_m"] != "" and r[f"{y}_m"] != ""])
        print(f"margin({x}) - margin({y}) over {dm.size} events: min {dm.min():.5f}  median {np.median(dm):.5f}  max {dm.max():.5f}  n({x}>{y}) {(dm > 0).sum()}")
    ks = list(STATE)
    fig, ax = plt.subplots(1, 3, figsize=(12, 3.8))
    x = np.arange(len(ks))
    ax[0].bar(x, [r["sumdP_vs_case_MW"] for r in rows], color=[COL[k] for k in ks]); ax[0].set_ylim(50, 64); ax[0].set_xticks(x, ks); ax[0].set_ylabel("$\\sum|\\Delta P|$ vs case (MW)")
    a2 = ax[0].twinx(); a2.plot(x, [r["J"] for r in rows], "ko-", ms=4); a2.set_ylabel("J"); a2.set_ylim(1.66, 1.80); ax[0].set_title("(a) Effort (bars) and cost J (line)", fontsize=9)
    evs = ["b8P_S3", "b21P_S3", "b15P_S3", "b23P_S3", "b18P_S2", "b18P_S3"]
    w = 0.16
    for q, k in enumerate(ks):
        ax[1].bar(np.arange(len(evs)) + (q - 2) * w, [float(next(r for r in ev_rows if r["event"] == e)[f"{k}_m"]) for e in evs], w, color=COL[k], label=LAB[k])
    ax[1].axhline(0, color="k", lw=0.8); ax[1].axhspan(-U_D8, U_D8, color="#dddddd", alpha=0.5, lw=0)
    ax[1].set_xticks(range(len(evs)), [e.replace("P_", " ") for e in evs], fontsize=7); ax[1].set_ylabel("predicted ext. margin (pu), dense"); ax[1].set_title("(b) Predicted margin per event", fontsize=9)
    ax[1].legend(fontsize=5.5)
    for k in ks:
        ax[2].scatter(rows[ks.index(k)]["sumdP_vs_case_MW"], rows[ks.index(k)]["ext_min_margin_design"], color=COL[k], s=40)
        ax[2].annotate(k, (rows[ks.index(k)]["sumdP_vs_case_MW"], rows[ks.index(k)]["ext_min_margin_design"]), fontsize=8, xytext=(3, 3), textcoords="offset points")
    ax[2].set_xlabel("$\\sum|\\Delta P|$ vs case (MW)"); ax[2].set_ylabel("min predicted margin, 12 design events (pu)"); ax[2].set_title("(c) Margin vs effort", fontsize=9)
    fig.suptitle("F8 (preliminary): equal-effort comparison, OC1 (predicted, 0 TDS)", fontsize=10); fig.tight_layout()
    if write:
        wr("IEEE39_DEC066_T7_equal_effort.csv", rows); wr("IEEE39_DEC066_T7b_equal_effort_events.csv", ev_rows)
        fig.savefig(ART.parent / "figures_main/DEC066_F8_prelim.pdf"); fig.savefig(ART.parent / "figures_main/DEC066_F8_prelim.png", dpi=300)


if __name__ == "__main__":
    main("write" in sys.argv)
