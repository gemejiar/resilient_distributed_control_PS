"""DEC-066 P0/P1: paper tables T1 (experiments and dispatches), T2 (observed safety), T3 (predictor accuracy and horizon sweep) from EXISTING data; 0 TDS.
Sources: backups/DEC054_g4_state, DEC055_state, DEC059_state (dispatch states), IEEE39_DEC062_TEST_results.json (54 runs), IEEE39_DEC066_P1_windows_*.csv and *_traj_*.npz (window-resolved prediction), IEEE39_DEC054_prospective_*.
Writes IEEE39_DEC066_T1_dispatches.csv, IEEE39_DEC066_T2_observed_safety.csv, IEEE39_DEC066_T2b_cells.csv, IEEE39_DEC066_T3_predictor.csv, IEEE39_DEC066_T3b_horizon_sweep.csv exclusively with 'write'."""
from __future__ import annotations

import csv
import glob
import json
import sys

import numpy as np

import dec054_common as C54
import dec055_common as C55
import dec062_r5 as R5

STATE = C54.RUNS_DIR.parent
U_D8 = 0.0109
MW = 100.0


def klass(m):
    return "SAFE" if m >= U_D8 else "UNSAFE" if m <= -U_D8 else "INDET"


def jl(p):
    return json.loads((STATE / p).read_text(encoding="utf-8"))


def z_of(d):
    return np.asarray(d["z"] if "z" in d else d["describe"]["z"], float)


def t1():
    rows = []
    # DEC-054 (design set of DEC-054; same plant as OC1)
    g = {k: jl(f"DEC054_g4_state/{k}.json") for k in ("m0", "m2", "m3")}
    m1 = jl("DEC054_g4_state/m1.json")["grid"] + jl("DEC054_g4_state/m1b.json")["grid"]
    m1sel = min(m1, key=lambda e: abs(e["J"] - 3.321))
    z0 = z_of(g["m0"])
    entries = [("DEC054", "OC1-eq", "M0", g["m0"]), ("DEC054", "OC1-eq", "M1 (rho=%.3f)" % m1sel["rho"], m1sel), ("DEC054", "OC1-eq", "M2", g["m2"]), ("DEC054", "OC1-eq", "M3", g["m3"])]
    for src, oc, lab, d in entries:
        z = z_of(d)
        desc = d.get("describe", {})
        rows.append({"source": src, "oc": oc, "method": lab, "design_set": "DEC-054 design set", "status": d.get("status", "FEASIBLE_PREDICTED"), "J": d.get("J"), "sumdP_MW_vs_M0": float(np.abs(z[:9] - z0[:9]).sum() * MW),
                     "sumdP_MW_vs_case_recorded": desc.get("redispatch_MW_abs_sum"), "pred_min_margin_design": desc.get("pred_margin_min"), "n_violating_events_pred": desc.get("n_violating_events"),
                     "kkt": d.get("kkt"), "seconds": d.get("seconds"), "plant_evaluations": d.get("plant_evaluations"), "event_tasks": d.get("event_tasks"), "state_file": "DEC054_g4_state"})
    # DEC-055 / DEC-059..061 designs
    for oc in ("OC1", "OC2"):
        d0 = jl(f"DEC055_state/m0_{oc}.json")
        z0 = z_of(d0)
        lst = [("DEC055", "M0", d0, "none"), ("DEC055", "M3", jl(f"DEC055_state/m3_{oc}.json"), "DEC-055 design set")]
        lst.append(("DEC059", "M3+OS", jl(f"DEC059_state/m3os_{oc}.json"), "DEC-059 design set + OS"))
        if oc == "OC1":
            lst += [("DEC060", "M3+OS cut", jl("DEC059_state/m3os_cut_OC1.json"), "DEC-060 (+b20 cut cell)"), ("DEC061", "M3+OS rev3", jl("DEC059_state/m3os_rev3_OC1.json"), "DEC-061 (+b20 S3; 16 events)")]
        for src, lab, d, ds in lst:
            z = z_of(d)
            mm = None
            if "margins_all_cells" in d:
                mm = float(min(v["min_up"] for v in d["margins_all_cells"].values()))
            rows.append({"source": src, "oc": oc, "method": lab, "design_set": ds, "status": d.get("status"), "J": d.get("J"), "sumdP_MW_vs_M0": float(np.abs(z[:9] - z0[:9]).sum() * MW),
                         "sumdP_MW_vs_case_recorded": d.get("redispatch_MW_abs_sum_vs_case"), "pred_min_margin_design": mm, "n_violating_events_pred": None, "kkt": d.get("kkt"), "seconds": d.get("seconds"),
                         "plant_evaluations": d.get("plant_evaluations"), "event_tasks": d.get("event_tasks"), "state_file": "DEC055_state/DEC059_state"})
    return rows


def load_p1():
    rows = []
    for f in sorted(glob.glob(str(C55.ART / "IEEE39_DEC066_P1_windows_*.csv"))):
        for r in csv.DictReader(open(f, encoding="utf-8")):
            rows.append(r)
    return rows


def window_of(t):
    t = float(t)
    return "JUMP/first sample" if t <= 3e-4 else "FAST 0-50 ms" if t <= 0.05 else "MID 0.05-10 s" if t <= 10.0 else "SLOW 10-195 s"


def t2():
    res = json.loads((C55.ART / "IEEE39_DEC062_TEST_results.json").read_text(encoding="utf-8"))
    cells = []
    p1 = {(r["oc"], r["dispatch"], r["cell"]): r for r in load_p1()}
    for key, v in res["A"].items():
        oc, m = key.split("_", 1)
        for c in v["cells"]:
            cell = c["run_id"].split("_")[-2] + "_" + c["run_id"].split("_")[-1]
            r = p1[(oc, m, cell)]
            mg = c["margins"]
            qsv_viol = int(mg["qmax_margin_min"] < 0) + int(mg["qmin_margin_min"] < 0) + int(mg["s_margin_min"] < 0) + int(mg["V_bus_min"] < 0.95 or mg["V_bus_max"] > 1.05)
            cells.append({"oc": oc, "dispatch": m, "cell": cell, "severity": cell.split("_")[1], "bus": int(cell[1:].split("P")[0]), "class_observed": c["class"], "class_pred_50ms": c["pred_class"], "false_SAFE_50ms": c["false_SAFE"],
                          "admissible_at_jump_pred": c["admissible_at_jump_pred"], "m_jump_first_sample": float(r["tds_jump_margin"]), "m_fast_0_50ms": float(r["tds_fast_margin"]), "m_slow_50ms_195s": float(r["tds_slow_margin"]),
                          "m_all": float(r["tds_all_margin"]), "limiting_unit": r["tds_all_unit"], "t_peak_after_event_s": float(r["tds_all_t"]), "peak_window": window_of(r["tds_all_t"]),
                          "qsv_violating_checks": qsv_viol, "reasons": ";".join(c.get("reasons", []))})
    summ = []
    for oc in ("OC1", "OC2"):
        for m in sorted({c["dispatch"] for c in cells if c["oc"] == oc}):
            for sev in ("S1", "S2", "S3", "ALL"):
                sub = [c for c in cells if c["oc"] == oc and c["dispatch"] == m and (sev == "ALL" or c["severity"] == sev)]
                n = len(sub)
                summ.append({"oc": oc, "dispatch": m, "severity": sev, "n": n, "SAFE": sum(c["class_observed"] == "SAFE" for c in sub), "INDET": sum(c["class_observed"] == "NUMERICALLY_INDETERMINATE" for c in sub),
                             "UNSAFE": sum(c["class_observed"] == "UNSAFE" for c in sub), "false_SAFE_50ms": sum(bool(c["false_SAFE_50ms"]) for c in sub),
                             "inadmissible_at_jump_pred": sum(c["admissible_at_jump_pred"] is False for c in sub), "worst_margin": min(c["m_all"] for c in sub),
                             "peak_window_JUMP": sum(c["peak_window"].startswith("JUMP") for c in sub), "peak_window_FAST": sum(c["peak_window"].startswith("FAST") for c in sub),
                             "peak_window_MID": sum(c["peak_window"].startswith("MID") for c in sub), "peak_window_SLOW": sum(c["peak_window"].startswith("SLOW") for c in sub),
                             "qsv_violating_cells": sum(c["qsv_violating_checks"] > 0 for c in sub)})
    return summ, cells


def t3():
    rows = load_p1()
    out, sweep = [], []
    groups = {"OC1 M0": ("OC1", "M0"), "OC1 rev3": ("OC1", "M3REV3"), "OC2 M0": ("OC2", "M0"), "OC2 M3+OS": ("OC2", "M3OS"), "ALL 36": None}
    for lab, g in groups.items():
        sub = [r for r in rows if g is None or (r["oc"], r["dispatch"]) == g]
        e50 = np.array([float(r["tds_fast_margin"]) - float(r["pred50_margin"]) for r in sub])           # observed - predicted, 0-50 ms (>0: predictor conservative)
        eF = np.array([float(r["tds_all_margin"]) - float(r["predF_margin"]) for r in sub])              # observed - predicted, full horizon
        eFc = eF[np.array([abs(float(r["predF_margin"])) < 1.0 for r in sub])]                          # excluding divergent 195 s predictions (|margin| >= 1 pu)
        def st(e):
            return {"n": len(e), "bias": float(e.mean()) if len(e) else None, "MAE": float(np.abs(e).mean()) if len(e) else None, "RMSE": float(np.sqrt((e ** 2).mean())) if len(e) else None,
                    "p95_abs": float(np.percentile(np.abs(e), 95)) if len(e) else None, "min": float(e.min()) if len(e) else None, "max": float(e.max()) if len(e) else None}
        s50, sF, sFc = st(e50), st(eF), st(eFc)
        cm = lambda a, b: {"false_SAFE": sum(r[a] == "SAFE" and r[b] != "SAFE" for r in sub), "false_UNSAFE": sum(r[a] == "UNSAFE" and r[b] != "UNSAFE" for r in sub), "agree": sum(r[a] == r[b] for r in sub)}
        c50, cF = cm("class_pred50", "class_tds_all"), cm("class_predF", "class_tds_all")
        out.append({"group": lab, "n": len(sub), **{f"e50_{k}": v for k, v in s50.items() if k != "n"}, **{f"eF_{k}": v for k, v in sF.items() if k != "n"}, "eF_n_excl_divergent": sFc["n"], "eF_excl_RMSE": sFc["RMSE"],
                    "pred50_false_SAFE": c50["false_SAFE"], "pred50_false_UNSAFE": c50["false_UNSAFE"], "pred50_agree": c50["agree"], "predF_false_SAFE": cF["false_SAFE"], "predF_false_UNSAFE": cF["false_UNSAFE"], "predF_agree": cF["agree"],
                    "U_D8": U_D8, "note": "e = observed - predicted margin (>0 conservative); class vs TDS over [t_e, 195 s]"})
    # retrospective horizon sweep on the saved trajectories (exploratory: horizon chosen after seeing DEC-062; NOT blind)
    for oc, m in (("OC1", "M0"), ("OC1", "M3REV3"), ("OC2", "M0"), ("OC2", "M3OS")):
        for r in [x for x in rows if x["oc"] == oc and x["dispatch"] == m]:
            z = np.load(C55.ART / f"IEEE39_DEC066_P1_traj_{oc}_{m}_{r['cell']}.npz")
            t, Pp, pmax = z["t"], z["P_pred"], z["pmax"]
            for Tc in (0.05, 1.0, 10.0, 60.0, 195.0):
                w = t <= Tc + 1e-9
                mg = float((pmax[:, None] - Pp[:, w]).min())
                sweep.append({"oc": oc, "dispatch": m, "cell": r["cell"], "T_c_s": Tc, "pred_margin": mg, "class_pred": klass(mg), "class_tds_all": r["class_tds_all"]})
    return out, sweep


def sweep_summary(sweep):
    rows = []
    for g in ("ALL", "OC1 M0", "OC1 M3REV3", "OC2 M0", "OC2 M3OS"):
        for Tc in (0.05, 1.0, 10.0, 60.0, 195.0):
            s = [x for x in sweep if x["T_c_s"] == Tc and (g == "ALL" or f"{x['oc']} {x['dispatch']}" == g)]
            rows.append({"group": g, "T_c_s": Tc, "n": len(s), "agree": sum(x["class_pred"] == x["class_tds_all"] for x in s), "false_SAFE": sum(x["class_pred"] == "SAFE" and x["class_tds_all"] != "SAFE" for x in s),
                         "false_UNSAFE": sum(x["class_pred"] == "UNSAFE" and x["class_tds_all"] != "UNSAFE" for x in s), "INDET_pred": sum(x["class_pred"] == "INDET" for x in s)})
    return rows


def wr(name, rows):
    with open(C55.ART / name, "x", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main(write=False):
    r1 = t1()
    s2, c2 = t2()
    r3, sw = t3()
    ss = sweep_summary(sw)
    for r in r1:
        print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items() if k in ("source", "oc", "method", "status", "J", "sumdP_MW_vs_M0", "sumdP_MW_vs_case_recorded", "pred_min_margin_design", "kkt", "seconds")})
    for r in s2:
        if r["severity"] == "ALL":
            print({k: r[k] for k in ("oc", "dispatch", "n", "SAFE", "INDET", "UNSAFE", "false_SAFE_50ms", "inadmissible_at_jump_pred", "peak_window_JUMP", "peak_window_FAST", "peak_window_MID", "peak_window_SLOW", "qsv_violating_cells")})
    for r in r3:
        print({k: (round(v, 5) if isinstance(v, float) else v) for k, v in r.items() if k in ("group", "n", "e50_bias", "e50_RMSE", "eF_bias", "eF_RMSE", "eF_excl_RMSE", "pred50_false_SAFE", "predF_false_SAFE", "predF_false_UNSAFE", "pred50_agree", "predF_agree")})
    for r in ss:
        if r["group"] == "ALL":
            print(r)
    if write:
        wr("IEEE39_DEC066_T1_dispatches.csv", r1)
        wr("IEEE39_DEC066_T2_observed_safety.csv", s2)
        wr("IEEE39_DEC066_T2b_cells.csv", c2)
        wr("IEEE39_DEC066_T3_predictor.csv", r3)
        wr("IEEE39_DEC066_T3b_horizon_sweep.csv", ss)
        wr("IEEE39_DEC066_T3c_horizon_sweep_cells.csv", sw)


if __name__ == "__main__":
    main("write" in sys.argv)
