"""DEC-062 TEST analysis (protocol ops/sted/DEC062_protocol.md section 7): per-run metrics, M3V-1 classes, predictions vs TDS, T1/T2/P3 checks, original and alternative criteria reported
separately, comparison tables (controller effect, dispatch effect, CLF effect).  Pure post-processing of stored runs; changes nothing.
  <venv python> dec062_test.py [write]            writes IEEE39_DEC062_TEST_results.json exclusively
  <venv python> dec062_test.py selftest            runs the pipeline on stored TUNE runs (no TEST data) to debug the code before the TEST TDS"""
from __future__ import annotations

import json
import sys

import numpy as np

import dec054_common as C54
import dec055_common as C55
import dec059_metrics as M
import dec059_tds as T
import dec059_tune as TU
import dec062_r5 as R5

TE = C54.EVENT_T
U_D8 = M.U_D8


def effort(run):
    z = np.load(T.RUNS / run / "series.npz", allow_pickle=True)
    t = z["cmd_t"]
    k = t >= TE
    out = {}
    for name in ("cmd_pset", "cmd_qset"):
        a = np.asarray(z[name])[k]
        tt = t[k]
        d = np.abs(np.diff(a, axis=0))
        dt = np.maximum(np.diff(tt), 1e-9)
        out[name[4] + "_total_variation"] = float(d.sum())
        out[name[4] + "_peak_rate"] = float((d / dt[:, None]).max()) if d.size else 0.0
    return out


def v_settle(run, tol=1e-3):
    """Time after t_e from which every unit-bus voltage stays within tol of its value at the end of the run (controller independent)."""
    z = np.load(T.RUNS / run / "series.npz", allow_pickle=True)
    t = z["t"]
    vu = z["V"][:, [b - 1 for b in C54.UNIT_BUS]]
    vend = vu[t >= t[-1] - 2].mean(axis=0)
    e = np.abs(vu - vend[None, :]).max(axis=1)
    bad = np.where((e > tol) & (t >= TE))[0]
    return float(t[bad[-1]] - TE) if bad.size else 0.0


def record(run, lim, pred, kind):
    m = M.metrics(run, lim)
    cls, why = M.classify(m)
    has_b5 = "b5" in m
    if has_b5:
        m["G_R3"] = M.gr3(m)
    adm = None if pred is None else bool(pred.get("admissible_at_jump", False))
    sev = None if pred is None else pred["severity"]
    e = None if pred is None else m["pmax_margin_min_50ms"] - pred["pred_pmax_margin_min"]
    tl = m.get("target_labels")
    r = {"run_id": run, "kind": kind, "class": cls, "reasons": why, "eligible": None if pred is None else bool(sev in ("S1", "S2") or adm), "admissible_at_jump_pred": adm,
         "pred_margin": None if pred is None else pred["pred_pmax_margin_min"], "pred_class": None if pred is None else pred["pred_class_all"], "pred_unit": None if pred is None else pred["pred_pmax_unit"],
         "m50": m["pmax_margin_min_50ms"], "m_after_50ms": m["pmax_margin_min_after_50ms"], "e": e, "iii_H": None if e is None else abs(e) <= TU.EPS_FLOOR, "iii_U": None if e is None else e >= -TU.EPS_FLOOR,
         "class_matches_prediction": None if pred is None else pred["pred_class_all"] == cls, "false_SAFE": None if pred is None else bool(pred["pred_class_all"] == "SAFE" and cls == "UNSAFE"),
         "margins": {k: m[k] for k in ("pmin_margin_min", "qmax_margin_min", "qmin_margin_min", "s_margin_min", "V_bus_min", "V_bus_max")},
         "frequency": {k: m.get(k) for k in ("f_coi_nadir_hz", "rocof_100ms_hz_s", "f_err_120s_hz", "f_err_200s_hz", "settle_0p01Hz_s")},
         "voltage": {"unit_V_err_vs_setpoint": m["unit_V_err_end_vs_setpoint"], "unit_V_err_vs_1pu": m["unit_V_err_end_vs_1pu"], "settle_1e-3_s": v_settle(run)},
         "sharing_std": m.get("sharing_std_free_units_end", m.get("sharing_std_all_units_end")), "effort": effort(run), "b5": m.get("b5") if has_b5 else None, "target_labels": tl,
         "G_R3": m.get("G_R3"), "T2_label": None if tl is None else ("VERIFIED_LOCAL" if tl.get("E4") and all(tl.get(k) for k in ("H1_root", "H2_smooth", "H3_interior", "H4_sampled", "H5_continuous")) else "TARGET_UNSTABLE_OR_NOT_VERIFIED")}
    if has_b5:
        r["T1_min_c"] = m["b5"]["c_min"]
        r["T1_ok"] = bool(m["b5"]["c_min"] >= 0)
        r["QP_fallback"] = m["b5"]["paths"][2]
        r["T2_V_ratio_end_over_first"] = m["b5"].get("V_ratio_end_over_first_valid")
    return r


def load_pred(oc, m):
    p = json.loads((C55.ART / f"IEEE39_DEC059_pred_{oc}_{m}_test.json").read_text(encoding="utf-8"))
    return {c["name"]: c for c in p["cells"]}


def p3_row(r):
    """P3: N2 (predicted admissibility) and the observed class; V (verified local target) and the observed outcome.  Consistency checks only."""
    chk = {}
    if r["admissible_at_jump_pred"] is False:
        chk["N2_inadmissible_implies_not_SAFE"] = r["class"] != "SAFE"
    return {"N2_admissible_pred": r["admissible_at_jump_pred"], "V_label": r["T2_label"], "O_class": r["class"], "checks": chk}


def g3(rows):
    el = [r for r in rows if r["eligible"]]
    gr = lambda r: all(v for k, v in (r["G_R3"] or {}).items() if not (k.startswith("converged") or k.startswith("sharing")) or (r["target_labels"] or {}).get("H5_continuous", False))
    return {"n_cells": len(rows), "n_eligible": len(el), "i_no_eligible_UNSAFE": not any(r["class"] == "UNSAFE" for r in el), "ii_no_TDS_failure": not any(r["class"] == "TDS_NUMERICAL_FAILURE" for r in rows),
            "iii_H_two_sided": all(r["iii_H"] for r in rows if r["class"] != "TDS_NUMERICAL_FAILURE"), "iii_U_one_sided": all(r["iii_U"] for r in rows if r["class"] != "TDS_NUMERICAL_FAILURE"),
            "iv_GR3": all(gr(r) for r in el), "unsafe_eligible": [r["run_id"] for r in el if r["class"] == "UNSAFE"], "indeterminate": [r["run_id"] for r in rows if r["class"] == "NUMERICALLY_INDETERMINATE"],
            "iii_H_violating": [r["run_id"] for r in rows if r["iii_H"] is False], "iii_U_violating": [r["run_id"] for r in rows if r["iii_U"] is False],
            "iv_failing": [r["run_id"] for r in el if not gr(r)], "n_SAFE": sum(r["class"] == "SAFE" for r in rows), "n_UNSAFE": sum(r["class"] == "UNSAFE" for r in rows),
            "n_class_match": sum(bool(r["class_matches_prediction"]) for r in rows), "n_false_SAFE": sum(bool(r["false_SAFE"]) for r in rows)}


def main(write=False):
    import dec055_oc as OCM
    out = {"label": "EVALUATION_UNDER_MODIFIED_ACCESS_RULE", "stage": "DEC-062 TEST results", "A": {}, "B": {}}
    for oc in ("OC1", "OC2"):
        lim = OCM.make_plant(oc).limits
        for m in ("M0", R5.DES[oc]):
            pr = load_pred(oc, m)
            rows = [record(f"D62TEST_B5P_{oc}_{m}_b{b}P_{s}", lim, pr[f"b{b}P_{s}"], "B5P") for b in R5.TEST for s in R5.SEV]
            for r in rows:
                r["P3"] = p3_row(r)
            out["A"][f"{oc}_{m}"] = {"cells": rows, "G3_style_criteria": g3(rows)}
        for b in R5.TEST:
            pred = load_pred(oc, R5.DES[oc])[f"b{b}P_S2"]
            out["B"].setdefault(oc, {})[f"b{b}P_S2"] = {c: record(f"D62CMP_{c}_{oc}_{R5.DES[oc]}_b{b}P_S2", lim, pred, c) for c in ("B2", "B1S", "B4P")}
    # comparison tables
    cmp_ = {}
    for oc in ("OC1", "OC2"):
        for b in R5.TEST:
            cell = f"b{b}P_S2"
            base = next(r for r in out["A"][f"{oc}_{R5.DES[oc]}"]["cells"] if r["run_id"].endswith(f"b{b}P_S2"))
            m0 = next(r for r in out["A"][f"{oc}_M0"]["cells"] if r["run_id"].endswith(f"b{b}P_S2"))
            row = {"B5P@M3+OS": base, "B5P@M0": m0, **out["B"][oc][cell]}
            cmp_[f"{oc}_{cell}"] = {k: {"class": v["class"], "m50": v["m50"], "f_nadir": v["frequency"]["f_coi_nadir_hz"], "rocof": v["frequency"]["rocof_100ms_hz_s"], "f_err_200s": v["frequency"]["f_err_200s_hz"],
                                        "f_settle_s": v["frequency"]["settle_0p01Hz_s"], "unitV_err_vs_setpoint_max": v["voltage"]["unit_V_err_vs_setpoint"]["max"], "unitV_err_vs_1pu_max": v["voltage"]["unit_V_err_vs_1pu"]["max"],
                                        "V_settle_s": v["voltage"]["settle_1e-3_s"], "sharing_std": v["sharing_std"], "P_TV": v["effort"]["p_total_variation"], "Q_TV": v["effort"]["q_total_variation"],
                                        "P_peak_rate": v["effort"]["p_peak_rate"], "Q_peak_rate": v["effort"]["q_peak_rate"]} for k, v in row.items()}
    out["comparison"] = cmp_
    allb5 = [r for k in out["A"] for r in out["A"][k]["cells"]] + [r for oc in out["B"] for c in out["B"][oc] for n, r in out["B"][oc][c].items() if n == "B4P"]
    out["T1_summary"] = {"n_runs": len(allb5), "min_c_over_runs": min(r["T1_min_c"] for r in allb5), "n_negative": sum(not r["T1_ok"] for r in allb5), "n_QP_fallback": sum(r["QP_fallback"] > 0 for r in allb5)}
    out["T2_summary"] = {"n_targets_verified": sum(r["T2_label"] == "VERIFIED_LOCAL" for r in allb5), "n_runs": len(allb5), "V_ratio_max": max((r["T2_V_ratio_end_over_first"] or 0) for r in allb5)}
    out["P3_summary"] = {"N2_violations": [r["run_id"] for k in out["A"] for r in out["A"][k]["cells"] if r["P3"]["checks"] and not all(r["P3"]["checks"].values())],
                         "n_inadmissible_pred": sum(r["admissible_at_jump_pred"] is False for k in out["A"] for r in out["A"][k]["cells"])}
    for k, v in out["A"].items():
        print(k, {a: b for a, b in v["G3_style_criteria"].items() if a not in ("iii_H_violating", "iii_U_violating", "iv_failing", "eligible_cells")})
    print("T1", out["T1_summary"], "T2", out["T2_summary"], "P3", out["P3_summary"])
    if write:
        with open(C55.ART / "IEEE39_DEC062_TEST_results.json", "x", encoding="utf-8") as f:
            json.dump(out, f, indent=1, default=float)
    return out


def selftest():
    """Pipeline check on stored TUNE runs (no TEST data): record() on one B5P and one comparison-free run, g3() on the OC2 TUNE cells."""
    import dec055_oc as OCM
    lim = OCM.make_plant("OC2").limits
    pr = json.loads((C55.ART / "IEEE39_DEC059_pred_OC2_M3OS_tune.json").read_text(encoding="utf-8"))
    pm = {c["name"]: c for c in pr["cells"]}
    rows = [record(f"D59TUNE_B5P_OC2_M3OS_{n}", lim, pm[n], "B5P") for n in pm]
    for r in rows:
        r["P3"] = p3_row(r)
    print(json.dumps({k: v for k, v in g3(rows).items() if k.startswith(("i", "n_"))}, indent=1))
    print(json.dumps({k: rows[0][k] for k in ("class", "e", "frequency", "voltage", "effort", "T1_min_c", "T2_label", "T2_V_ratio_end_over_first")}, indent=1, default=float))


if __name__ == "__main__":
    selftest() if sys.argv[1:] == ["selftest"] else main("write" in sys.argv)
