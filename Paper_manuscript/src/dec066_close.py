"""DEC-066 closure products (post-processing only; 0 TDS):
  T8   every simulated cell (34 TDS) with its sealed prediction, window-matched observed margin (0-10 s), pre-event headroom, observed excursion, class and evidence role
       (design-set / previously observed / out-of-design / step test)              -> artifacts/IEEE39_DEC066_T8_all_cells.csv
  T7c  observed equal-effort contrasts (D vs EQ1, DQ1 vs E, ...) at b8 S3 and b21 S3  -> artifacts/IEEE39_DEC066_T7c_equal_effort_observed.csv
  F8   final figure of the equal-effort comparison and of the headroom attribution     -> figures_main/DEC066_F8_equal_effort.{pdf,png}
Run: <venv python> dec066_close.py write"""
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
U_D8 = 0.0109
ROLE = {"b8": "design-set (in-sample)", "b23": "design-set (in-sample)", "b21": "previously observed bus (blind TEST of DEC-055; used here retrospectively)", "b31": "previously observed bus (blind TEST of DEC-055)",
        "b39": "previously observed bus (TEST of DEC-055); counter-condition", "b15": "previously observed bus (DEC-054 TEST)", "b18": "out-of-design (no TDS before DEC-066)"}
COL = {"A": "#4d4d4d", "B": "#0072B2", "C": "#56B4E9", "D": "#D55E00", "E": "#009E73", "EQ1": "#CC79A7", "DQ1": "#F0E442"}


def rd(n):
    return list(csv.DictReader(open(ART / n, encoding="utf-8")))


def preds():
    P = {}
    e1a = json.loads((ART / "IEEE39_DEC066_E1a_plan.json").read_text(encoding="utf-8"))["predictions"]["predicted"]
    for v, x in e1a.items():
        P[(v, "b8P_S3")] = x
    for k, x in json.loads((ART / "IEEE39_DEC066_E1b_plan.json").read_text(encoding="utf-8"))["predictions"]["cells"].items():
        v, b, s = k.split("_")
        P[(v, f"{b}P_{s}")] = x["pred_min_margin_0_10s"]
    for lot in ("F2", "F3"):
        for k, x in json.loads((ART / f"IEEE39_DEC066_{lot}_pred.json").read_text(encoding="utf-8"))["predictions"].items():
            v, ev = k.split("_", 1)
            P[(v, ev)] = x["pred_min_margin_0_10s"]
    return P


def cells():
    P = preds()
    out = []
    for n, tag in (("IEEE39_DEC066_T5_observed.csv", ""), ("IEEE39_DEC066_T5_F2_observed.csv", "F2"), ("IEEE39_DEC066_T5_F3_observed.csv", "F3"), ("IEEE39_DEC066_T5_F4_observed.csv", "F4"), ("IEEE39_DEC066_T5_F5_observed.csv", "F5")):
        for r in rd(n):
            rid = r["run_id"]
            lot = rid[3:rid.index("_")]
            rest = rid.split("OC1_", 1)[1]                         # e.g. A_b8P_S3 or A_b8P_S3_dt2
            v, ev = rest.split("_", 1)[0], "_".join(rest.split("_")[1:3])
            suffix = "_".join(rest.split("_")[3:])
            m010 = min(float(r["mPmax_0_50ms"]), float(r["mPmax_50ms_10s"]))
            pre = None
            row = {"run_id": rid, "lot": lot, "design": v, "event": ev, "step": suffix or "nominal (dt, local dt/16)",
                   "evidence_role": "step-sensitivity test" if suffix else ROLE[ev.split("P")[0]],
                   "pred_0_10s": P.get((v, ev), ""), "obs_0_50ms": round(float(r["mPmax_0_50ms"]), 5), "obs_50ms_10s": round(float(r["mPmax_50ms_10s"]), 5), "obs_0_10s": round(m010, 5),
                   "obs_10_195s": round(float(r["mPmax_10_195s"]), 5), "limiting_unit_0_50ms": r["unit_0_50ms"], "t_peak_ms": round(1e3 * float(r["t_0_50ms_s"]), 2),
                   "class_rule_M3V1": ("UNSAFE" if m010 <= -U_D8 else "SAFE" if m010 >= U_D8 else "NUMERICALLY_INDETERMINATE") if tag != "F4" else "(20 s horizon: margins only)",
                   "physical_violation": float(r["max_excess_pu"]) > 0, "max_excess_pu": round(float(r["max_excess_pu"]), 5), "duration_ms_approx": round(1e3 * float(r["duration_below_limit_s_approx"]), 2),
                   "pre_headroom_limiting": round(float(r.get("pre_headroom_limiting_unit") or "nan"), 5) if r.get("pre_headroom_limiting_unit") else "",
                   "excursion_obs": round(float(r.get("excursion_observed_0_50ms") or "nan"), 5) if r.get("excursion_observed_0_50ms") else "",
                   "pmin_margin": round(float(r["pmin_margin_min"]), 4), "qmax_margin": round(float(r["qmax_margin_min"]), 4), "s_margin": round(float(r["s_margin_min"]), 4),
                   "V_min": round(float(r["V_bus_min"]), 4), "f_nadir_hz": round(float(r["f_nadir_hz"]), 4)}
            row["error_obs_minus_pred"] = round(m010 - float(row["pred_0_10s"]), 5) if row["pred_0_10s"] != "" and not suffix else ""
            out.append(row)
    return out


def main(write=False):
    rows = cells()
    # the E1/E2 T5 file has no pre-headroom column: fill it from the lot files written by dec066_obs2 for F-lots only; for E-lots recompute here
    import dec066_obs2 as O2
    import dec055_oc as OCM
    import dec066_tds as D66
    import dec054_common as C54
    lim = OCM.make_plant("OC1").limits
    pmax = np.asarray(lim["pmax"], float)
    for r in rows:
        if r["pre_headroom_limiting"] == "":
            z = np.load(D66.RUNS / r["run_id"] / "series.npz", allow_pickle=True)
            t, P = z["t"], z["P"]
            pre = P[np.searchsorted(t, C54.EVENT_T - 1e-9) - 1]
            j = C55.UNITS.index(r["limiting_unit_0_50ms"])
            r["pre_headroom_limiting"] = round(float(pmax[j] - pre[j]), 5)
            r["excursion_obs"] = round(r["pre_headroom_limiting"] - r["obs_0_50ms"], 5)
    rows.sort(key=lambda r: (r["event"], r["design"], r["step"]))
    nom = [r for r in rows if r["error_obs_minus_pred"] != ""]
    err = np.array([r["error_obs_minus_pred"] for r in nom if r["event"] != "b31P_S2"])
    print("cells", len(rows), "with registered prediction", len(nom), "err (excl. b31 S2 jump case): n", err.size, "mean", err.mean().round(5), "min", err.min(), "max", err.max(), "n outside [0,0.0025]", int(((err < 0) | (err > 0.0025)).sum()))
    for r in nom:
        if r["error_obs_minus_pred"] < 0 or r["error_obs_minus_pred"] > 0.0025:
            print("  outside [0,+0.0025]:", r["run_id"], r["pred_0_10s"], r["obs_0_10s"], r["error_obs_minus_pred"])
    O = {(r["design"], r["event"]): r for r in rows if r["step"].startswith("nominal")}
    t7 = []
    for ev in ("b8P_S3", "b21P_S3"):
        for a, b, what in (("D", "EQ1", "dense+eps_OS+U vs uniform U (effort of D)"), ("DQ1", "E", "dense+eps_OS (small U) vs uniform U (effort of E)"), ("D", "E", "full OS vs uniform U (OS +2.4 MW)"), ("EQ1", "DQ1", "uniform U (large) vs dense+eps_OS (small)")):
            x, y = O[(a, ev)], O[(b, ev)]
            dm = x["obs_0_10s"] - y["obs_0_10s"]
            dh = x["pre_headroom_limiting"] - y["pre_headroom_limiting"]
            t7.append({"event": ev, "contrast": f"{a} - {b}", "meaning": what, "d_obs_margin": round(dm, 5), "d_pre_headroom": round(dh, 5), "d_excursion": round(x["excursion_obs"] - y["excursion_obs"], 5),
                       "margin_diff_explained_by_headroom": abs(dm - dh) < 0.0025, "verdict_0.0025": ("CONFIRMED a>b" if dm >= 0.0025 else "CONFIRMED b>a" if dm <= -0.0025 else "NOT DISTINGUISHABLE"),
                       "class_a": x["class_rule_M3V1"], "class_b": y["class_rule_M3V1"], "viol_a": x["physical_violation"], "viol_b": y["physical_violation"]})
    for r in t7:
        print(r)
    # ---- F8
    fig, ax = plt.subplots(1, 3, figsize=(12.5, 3.9))
    ks = ["A", "E", "DQ1", "EQ1", "D"]
    for q, ev in enumerate(("b8P_S3", "b21P_S3")):
        w = 0.15
        for i, k in enumerate(ks):
            if (k, ev) in O:
                ax[0].bar(q + (i - 2) * w, O[(k, ev)]["obs_0_10s"], w, color=COL[k], label=k if q == 0 else None, edgecolor="k", lw=0.4)
                if O[(k, ev)]["pred_0_10s"] != "":
                    ax[0].plot(q + (i - 2) * w, O[(k, ev)]["pred_0_10s"], "kD", ms=3)
    ax[0].axhline(0, color="k", lw=0.8); ax[0].axhspan(-U_D8, U_D8, color="#dddddd", alpha=0.5, lw=0)
    ax[0].set_xticks([0, 1], ["b8 S3", "b21 S3"]); ax[0].set_ylabel("observed min Pmax margin 0-10 s (pu)"); ax[0].legend(fontsize=6.5, ncol=3)
    ax[0].set_title("(a) Observed (bars) vs predicted (diamonds); band $\\pm U_{D8}$", fontsize=9)
    for q, ev in enumerate(("b8P_S3", "b21P_S3")):
        hs = [O[(k, ev)]["pre_headroom_limiting"] for k in ks if (k, ev) in O]; ex = [O[(k, ev)]["excursion_obs"] for k in ks if (k, ev) in O]; kk = [k for k in ks if (k, ev) in O]
        x = np.arange(len(kk)) + q * (len(ks) + 1)
        ax[1].bar(x, hs, 0.6, color=[COL[k] for k in kk], edgecolor="k", lw=0.4)
        ax[1].plot(x, ex, "k_", ms=14, mew=2)
    ax[1].set_xticks([2, 8], ["b8 S3 (SG31)", "b21 S3 (SG33)"]); ax[1].set_ylim(0.15, 0.33)
    ax[1].set_ylabel("headroom (bars), excursion (ticks), pu")
    ax[1].set_title("(b) Headroom differs between designs, excursion does not", fontsize=9)
    ok = [r for r in rows if r["error_obs_minus_pred"] != "" and r["event"] != "b31P_S2" and r["step"].startswith("nominal")]
    for r in ok:
        ax[2].plot(float(r["pred_0_10s"]), r["obs_0_10s"], "o", color=COL[r["design"]], ms=4, mec="k", mew=0.3)
    lo = min(float(r["pred_0_10s"]) for r in ok) - 0.01; hi = max(float(r["pred_0_10s"]) for r in ok) + 0.01
    ax[2].plot([lo, hi], [lo, hi], "k--", lw=0.8); ax[2].set_xlabel("predicted (sealed) margin (pu)"); ax[2].set_ylabel("observed margin (pu)")
    ax[2].set_title(f"(c) Predicted vs observed, {len(ok)} cells (excl. b31 S2)", fontsize=9)
    fig.suptitle("F8: equal-effort comparison and attribution to preventive headroom (OC1, B5', ANDES RMS)", fontsize=10); fig.tight_layout(rect=(0, 0, 1, 0.95))
    if write:
        for n, rr in (("IEEE39_DEC066_T8_all_cells.csv", rows), ("IEEE39_DEC066_T7c_equal_effort_observed.csv", t7)):
            with open(ART / n, "x", newline="", encoding="utf-8") as fh:
                w_ = csv.DictWriter(fh, fieldnames=list(rr[0].keys())); w_.writeheader(); w_.writerows(rr)
        fig.savefig(ART.parent / "figures_main/DEC066_F8_equal_effort.pdf"); fig.savefig(ART.parent / "figures_main/DEC066_F8_equal_effort.png", dpi=300)


if __name__ == "__main__":
    main("write" in sys.argv)
