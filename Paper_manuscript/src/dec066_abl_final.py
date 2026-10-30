"""DEC-066: final ablation products from the observed TDS (T5 CSV), the registered predictions (E1a/E1b/E2 plans) and the OPF-level tables.
  T5b  predicted vs observed minimum Pmax margin per (design, event)          -> artifacts/IEEE39_DEC066_T5b_pred_vs_obs.csv
  T6   observed marginal contrasts B-A, C-B, D-C, E-A, D-E                    -> artifacts/IEEE39_DEC066_T6_contrasts.csv
  F4   definitive figure (4 panels), F7 superposed transients (b8 S3 A-E; b21 S3 A,B,D,E) -> figures_main/DEC066_F4_final.*, DEC066_F7_transients.*
Run: <venv python> dec066_abl_final.py write   (writes exclusively)"""
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
import dec055_oc as OCM
import dec066_tds as D66

ART = C55.ART
FIG = ART.parent / "figures_main"
U_D8 = 0.0109
TE = C54.EVENT_T
COL = {"A": "#4d4d4d", "B": "#0072B2", "C": "#56B4E9", "D": "#D55E00", "E": "#009E73"}
LAB = {"A": "A  M3", "B": "B  +dense", "C": "C  +dense+$\\varepsilon_{OS}$", "D": "D  M3+OS", "E": "E  $U_{D8}$ only"}


def rd(n):
    return list(csv.DictReader(open(ART / n, encoding="utf-8")))


def wr(n, rows):
    with open(ART / n, "x", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


def main(write=False):
    obs = [r for r in rd("IEEE39_DEC066_T5_observed.csv") if "_dt" not in r["run_id"]]
    O = {(r["design"], f"b{r['bus']}_{'S3' if abs(float(r['amp']) - 0.87846) < 1e-4 else 'S2'}"): r for r in obs}
    pred = {}
    for lot in ("E1a", "E1b"):
        p = json.loads((ART / f"IEEE39_DEC066_{lot}_plan.json").read_text(encoding="utf-8"))["predictions"]
        if lot == "E1a":
            for v, x in p["predicted"].items():
                pred[(v, "b8_S3")] = x
        else:
            for k, x in p["cells"].items():
                v, b, s = k.split("_")
                pred[(v, f"{b[1:] and 'b' + b[1:]}_{s}".replace("bb", "b"))] = x["pred_min_margin_0_10s"]
    t4 = {r["variant"]: r for r in rd("IEEE39_DEC066_T4_OPF_ablation.csv")}
    rows = []
    for (v, ev), pv in sorted(pred.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        o = O[(v, ev)]
        om = float(o["mPmax_0_50ms"])
        rows.append({"event": ev, "design": v, "pred_min_margin": round(float(pv), 5), "obs_min_margin_0_50ms": round(om, 5), "error_obs_minus_pred": round(om - float(pv), 5), "obs_class": o["class"],
                     "obs_physical_violation_mP_lt_0": float(o["max_excess_pu"]) > 0, "max_excess_pu": round(float(o["max_excess_pu"]), 5), "duration_below_limit_ms_approx": round(1e3 * float(o["duration_below_limit_s_approx"]), 2),
                     "limiting_unit": o["unit_all"], "t_peak_ms": round(1e3 * float(o["t_all_s"]), 2), "obs_margin_50ms_10s": round(float(o["mPmax_50ms_10s"]), 5), "obs_margin_10_195s": round(float(o["mPmax_10_195s"]), 5),
                     "f_nadir_hz": round(float(o["f_nadir_hz"]), 5), "V_bus_min": round(float(o["V_bus_min"]), 5), "V_bus_max": round(float(o["V_bus_max"]), 5)})
    err = np.array([r["error_obs_minus_pred"] for r in rows if r["event"] != "b31_S2"])
    print("pred-vs-obs error (excluding b31 S2 jump case): n", len(err), "bias", err.mean(), "max|e|", np.abs(err).max())
    t6 = []
    for ev in ("b8_S3", "b21_S3", "b15_S3", "b23_S3", "b21_S2", "b31_S2"):
        for a, b, what in (("A", "B", "dense"), ("B", "C", "eps_OS"), ("C", "D", "U_D8 | dense+eps_OS"), ("A", "E", "U_D8 alone"), ("E", "D", "dense+eps_OS | U_D8"), ("A", "D", "full OS")):
            if (a, ev) in O and (b, ev) in O:
                ma, mb = float(O[(a, ev)]["mPmax_0_50ms"]), float(O[(b, ev)]["mPmax_0_50ms"])
                t6.append({"event": ev, "contrast": f"{b}-{a}", "component": what, "obs_margin_a": round(ma, 5), "obs_margin_b": round(mb, 5), "d_margin_obs": round(mb - ma, 5),
                           "class_a": O[(a, ev)]["class"], "class_b": O[(b, ev)]["class"], "viol_a": float(O[(a, ev)]["max_excess_pu"]) > 0, "viol_b": float(O[(b, ev)]["max_excess_pu"]) > 0,
                           "d_sumdP_vs_case_MW": round(float(t4[b]["sumdP_vs_case_MW"]) - float(t4[a]["sumdP_vs_case_MW"]), 3), "dJ": round(float(t4[b]["J"]) - float(t4[a]["J"]), 5)})
    # ---------------- figures
    fig, ax = plt.subplots(2, 2, figsize=(10.5, 7.6))
    K = "ABCDE"; x = np.arange(5)
    a = ax[0, 0]
    a.bar(x, [float(t4[k]["sumdP_vs_case_MW"]) for k in K], color=[COL[k] for k in K]); a.set_ylim(50, 63)
    a.set_xticks(x, list(K)); a.set_ylabel("$\\sum|\\Delta P|$ vs case (MW)")
    a2 = a.twinx(); a2.plot(x, [float(t4[k]["J"]) for k in K], "ko-", ms=4); a2.set_ylabel("J"); a2.set_ylim(1.66, 1.78)
    a.set_title("(a) Redispatch effort (bars) and cost J (line)", fontsize=9)
    b = ax[0, 1]
    ob = [float(O[(k, "b8_S3")]["mPmax_0_50ms"]) for k in K]; pr = [float(pred[(k, "b8_S3")]) for k in K]
    b.bar(x, ob, color=[COL[k] for k in K]); b.plot(x, pr, "kD", ms=5, label="predicted (registered)")
    b.axhline(0, color="k", lw=0.8); b.axhspan(-U_D8, U_D8, color="#dddddd", alpha=0.5, lw=0)
    b.set_xticks(x, list(K)); b.set_ylabel("observed min Pmax margin (pu)"); b.legend(fontsize=7, loc="upper left")
    b.set_title("(b) Event b8 S3: observed (bars) vs predicted; band $\\pm U_{D8}$", fontsize=9)
    c = ax[1, 0]
    evs = [("b21_S3", "b21 S3"), ("b15_S3", "b15 S3"), ("b23_S3", "b23 S3"), ("b21_S2", "b21 S2")]
    w = 0.19
    for i, k in enumerate("ABDE"):
        c.bar(np.arange(4) + (i - 1.5) * w, [float(O[(k, e)]["mPmax_0_50ms"]) if (k, e) in O else np.nan for e, _ in evs], w, color=COL[k], label=LAB[k])
    c.axhline(0, color="k", lw=0.8); c.axhspan(-U_D8, U_D8, color="#dddddd", alpha=0.5, lw=0)
    c.set_xticks(range(4), [n for _, n in evs]); c.set_ylabel("observed min Pmax margin (pu)"); c.legend(fontsize=6.5, ncol=2)
    c.set_title("(c) Other events (E and B only where run)", fontsize=9)
    d = ax[1, 1]
    pp = np.array([r["pred_min_margin"] for r in rows if r["event"] != "b31_S2"]); oo = np.array([r["obs_min_margin_0_50ms"] for r in rows if r["event"] != "b31_S2"])
    for r in rows:
        if r["event"] != "b31_S2":
            d.plot(r["pred_min_margin"], r["obs_min_margin_0_50ms"], "o", color=COL[r["design"]], ms=5)
    lo, hi = min(pp.min(), oo.min()) - 0.01, max(pp.max(), oo.max()) + 0.01
    d.plot([lo, hi], [lo, hi], "k--", lw=0.8); d.set_xlim(lo, hi); d.set_ylim(lo, hi)
    d.set_xlabel("predicted margin (pu)"); d.set_ylabel("observed margin (pu)")
    d.set_title("(d) Predicted vs observed (b31 S2 excluded: jump case)", fontsize=9)
    fig.suptitle("F4: ablation of M3+OS components (OC1, B5', 17 simulations; ANDES RMS/phasor)", fontsize=10)
    fig.tight_layout()
    # transients
    lim = OCM.make_plant("OC1").limits
    pmax = dict(zip(C55.UNITS, np.asarray(lim["pmax"], float)))
    f2, ax2 = plt.subplots(1, 3, figsize=(11.5, 3.6))
    for a_, (ev, unit, bus, sev, vs, xl) in zip(ax2, [("b8_S3", "SG31", 8, "S3", "ABCDE", 20), ("b21_S3", "SG33", 21, "S3", "ABDE", 20), ("b31_S2", "SG31", 31, "S2", "AD", 100)]):
        for v in vs:
            s = np.load(D66.RUNS / f"D66{'E1a' if ev == 'b8_S3' else 'E1b'}_B5P_OC1_{v}_b{bus}P_{sev}" / "series.npz", allow_pickle=True)
            t, P = s["t"], s["P"]
            k = (t >= TE - 0.002) & (t <= TE + xl * 1e-3)
            a_.plot((t[k] - TE) * 1e3, pmax[unit] - P[k][:, C55.UNITS.index(unit)], color=COL[v], marker=".", ms=3, lw=1, label=LAB[v])
        a_.axhline(0, color="k", lw=0.8); a_.axhspan(-U_D8, U_D8, color="#dddddd", alpha=0.5, lw=0)
        a_.set_xlabel("time after event (ms)"); a_.set_ylabel(f"Pmax $-$ P, {unit} (pu)"); a_.set_title(ev.replace("_", " "), fontsize=9)
        if ev == "b31_S2":
            a_.set_ylim(-0.15, 0.05)
    ax2[0].legend(fontsize=6.5)
    f2.suptitle("F7: delivered-power margin of the limiting unit, designs A-E (TDS, local step dt/16)", fontsize=10)
    f2.tight_layout()
    if write:
        wr("IEEE39_DEC066_T5b_pred_vs_obs.csv", rows); wr("IEEE39_DEC066_T6_contrasts.csv", t6)
        fig.savefig(FIG / "DEC066_F4_final.pdf"); fig.savefig(FIG / "DEC066_F4_final.png", dpi=300)
        f2.savefig(FIG / "DEC066_F7_transients.pdf"); f2.savefig(FIG / "DEC066_F7_transients.png", dpi=300)
    for r in rows:
        print(r["event"], r["design"], r["pred_min_margin"], r["obs_min_margin_0_50ms"], r["error_obs_minus_pred"], r["obs_class"], r["max_excess_pu"], r["duration_below_limit_ms_approx"])


if __name__ == "__main__":
    main("write" in sys.argv)
