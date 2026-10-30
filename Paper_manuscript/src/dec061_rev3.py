"""DEC-061 protocol v2.0: OC1 design revision 3 -- TDS lot D61 (8 TDS), analysis and independent gate G-v2.  DESIGN/TUNE buses only; TEST never touched.
  plan             writes IEEE39_DEC061_D61_plan.json exclusively (ledger block D61; sealed and committed before any TDS): the eight OC1 TUNE cells with B5P (frozen) at the rev3 dispatch
  analyse [write]  per-cell classes, signed errors, criteria C1-C6, alternatives; writes IEEE39_DEC061_D61_results.json
  gate             writes IEEE39_DEC061_gate_TEST.json exclusively (acta: protocol-v2 compliance / alternative results / post-TUNE changes); never opens TEST
Run the TDS with:  dec059_tds.py run D61"""
from __future__ import annotations

import glob
import json
import sys

import numpy as np

import dec054_common as C54
import dec055_common as C55
import dec059_gate as G
import dec059_metrics as M
import dec059_tds as T
import dec059_tune as TU
import dec060_recheck as R0

M_, OC = "M3REV3", "OC1"
CUT_PRED = "IEEE39_DEC059_pred_OC1_M3CUT_tune.json"


def plan():
    runs = []
    for bus in C55.TUNE:
        for sev in C55.TUNE_SEVERITIES:
            amp = round(C55.oc_amp(sev), 5)
            runs.append(T.b5_run(OC, {"bus": bus, "kind": "P", "amp": amp}, f"D61RV3_B5P_{OC}_{M_}_b{bus}P_{sev}",
                                 f"DEC-061 rev3 cell b{bus}P_{sev}, OC1, B5P (frozen parameters), local dt/16; pre-registered in DEC061_protocol.md", f"r2_{OC}_{M_}_d0", f"r2_{OC}_{M_}_b{bus}P_{amp:.5f}", m=M_))
    p = {"stage": "DEC-061 lot D61 plan: OC1 design revision 3, TUNE cells (sealed before any TDS of the lot)", "block": "D61", "runs": runs,
         "protocol_sha256": C54.sha_file(C55.ROOT / "ops/sted/DEC061_protocol.md"), "rev3_sha256": C54.sha_file(T.ST59 / "m3os_rev3_OC1.json"),
         "pred_sha256": {s: C54.sha_file(C55.ART / f"IEEE39_DEC059_pred_OC1_M3REV3_{s}.json") for s in ("design", "tune")},
         "criterion_iii_sha256": C54.sha_file(C55.ART / "IEEE39_DEC061_criterion_iii.md"),
         "code_sha256": {f: C54.sha_file(C55.SRC / f) for f in ("dec059_b5.py", "dec059_eq.py", "dec059_tds.py", "dec059_os.py", "dec059_pred.py", "dec059_metrics.py", "dec059_tune.py", "dec060_recheck.py",
                                                                "dec061_design.py", "dec061_rev3.py", "dec061_settling.py")}}
    T.plan("D61", p)


def pre_event_g1p(run):
    z = np.load(T.RUNS / run / "series.npz", allow_pickle=True)
    t = z["t"]
    k = t < C54.EVENT_T - 1e-9
    f, V = z["f_bus_hz"][k], z["V"][k]
    g = {"max_abs_df_hz": float(np.abs(f - f[0]).max()), "max_abs_dV_pu": float(np.abs(V - V[0]).max()), "V_min": float(V.min()), "V_max": float(V.max()), "t_window_s": float(t[k][-1])}
    g["pass"] = bool(g["t_window_s"] >= 4.99 and g["max_abs_df_hz"] <= 0.005 and g["max_abs_dV_pu"] <= 1e-3 and g["V_min"] >= 0.95 and g["V_max"] <= 1.05)
    return g


def analyse(write=False):
    import dec055_oc as OCM
    lim = OCM.make_plant(OC).limits
    pr = json.loads((C55.ART / f"IEEE39_DEC059_pred_{OC}_{M_}_tune.json").read_text(encoding="utf-8"))
    pc = {c["name"]: c for c in json.loads((C55.ART / CUT_PRED).read_text(encoding="utf-8"))["cells"]}
    rows = []
    for c in pr["cells"]:
        run = f"D61RV3_B5P_{OC}_{M_}_b{c['bus']}P_{c['severity']}"
        m = M.metrics(run, lim)
        m["G_R3"] = M.gr3(m)
        cls, why = M.classify(m)
        adm = bool(c.get("admissible_at_jump", False))
        el = c["severity"] == "S2" or (c["severity"] == "S3" and adm)
        e = m["pmax_margin_min_50ms"] - c["pred_pmax_margin_min"]
        gr = all(v for k, v in m["G_R3"].items() if not (k.startswith("converged") or k.startswith("sharing")) or (m.get("target_labels") or {}).get("H5_continuous", False))
        rows.append({"cell": c["name"], "run_id": run, "eligible": bool(el), "admissible_at_jump_pred": adm,
                     "pred": {k: c.get(k) for k in ("jump_pmax_margin_min", "pred_pmax_margin_min", "pred_pmax_unit", "pred_class_all")},
                     "tds": {"m50": m["pmax_margin_min_50ms"], "m_after_50ms": m["pmax_margin_min_after_50ms"], "class": cls, "reasons": why, "qmax_margin": m["qmax_margin_min"], "s_margin": m["s_margin_min"],
                             "V_min": m["V_bus_min"], "V_max": m["V_bus_max"]},
                     "e": e, "iii_H_two_sided": abs(e) <= TU.EPS_FLOOR, "iii_U_one_sided": e >= -TU.EPS_FLOOR, "class_matches_prediction": c.get("pred_class_all") == cls,
                     "pred_margin_change_vs_cut_dispatch": c["pred_pmax_margin_min"] - pc[c["name"]]["pred_pmax_margin_min"],
                     "iv_G_R3": bool(gr), "G_R3": m["G_R3"], "unit_V_err_200s": m["unit_V_err_end_vs_setpoint"], "target_labels": m.get("target_labels"),
                     "regulation": {k: m.get(k) for k in ("f_coi_nadir_hz", "f_err_200s_hz", "settle_0p01Hz_s")}, "b5": m.get("b5"), "V_tail_diagnostic": R0.vtail(run), "G1P_pre_event": pre_event_g1p(run)})
    tj = {}
    for f in sorted(glob.glob(str(T.ST59 / f"target_r2_{OC}_{M_}_*.json"))):
        js = json.loads(open(f, encoding="utf-8").read())
        tj[f.split("target_r2_")[1][:-5]] = {"E4": js["E4"]["pass"], "T2": {k: v["pass"] for k, v in js["T2"].items()}, "H5_rightmost": js["T2"]["H5_continuous"]["rightmost_excl_null"][0][0]}
    rev = json.loads((T.ST59 / "m3os_rev3_OC1.json").read_text(encoding="utf-8"))
    mon_ok = all(r["pred_margin_change_vs_cut_dispatch"] >= -1e-3 for r in rows if r["cell"] in ("b7P_S2", "b7P_S3", "b16P_S2", "b24P_S2"))
    el = [r for r in rows if r["eligible"]]
    C = {"C1_design": bool(rev["status"] == "FEASIBLE_PREDICTED" and "b20P_S3" in rev["design_events"] and rev["init_ok"] and mon_ok),
         "C2_targets_E4_H1H5": bool(len(tj) == 9 and all(v["E4"] and all(v["T2"].values()) for v in tj.values())),
         "C3_G1P_reduced": all(r["G1P_pre_event"]["pass"] for r in rows),
         "C4i_no_eligible_UNSAFE": not any(r["tds"]["class"] == "UNSAFE" for r in el),
         "C4ii_no_TDS_failure": not any(r["tds"]["class"] == "TDS_NUMERICAL_FAILURE" for r in rows),
         "C5_iii_U_one_sided": all(r["iii_U_one_sided"] for r in rows),
         "C6_iv_GR3_unitV_1e-3_at_200s": all(r["iv_G_R3"] for r in el)}
    out = {"stage": "DEC-061 D61 results (OC1 rev3, TUNE cells)", "cells": rows, "targets": tj, "criteria": C, "pass": all(C.values()),
           "historical_iii_H_two_sided": {"pass": all(r["iii_H_two_sided"] for r in rows), "violating": [r["cell"] for r in rows if not r["iii_H_two_sided"]]},
           "unsafe_eligible": [r["cell"] for r in el if r["tds"]["class"] == "UNSAFE"], "indeterminate": [r["cell"] for r in rows if r["tds"]["class"] == "NUMERICALLY_INDETERMINATE"],
           "iv_failing": [r["cell"] for r in el if not r["iv_G_R3"]], "design": {k: rev[k] for k in ("status", "J", "redispatch_MW_abs_sum_vs_case", "seconds", "event_tasks", "plant_evaluations")}}
    print(json.dumps({k: out[k] for k in ("criteria", "pass", "historical_iii_H_two_sided", "unsafe_eligible", "indeterminate", "iv_failing")}, indent=1))
    for r in rows:
        print(" ", r["cell"], "pred", round(r["pred"]["pred_pmax_margin_min"], 4), "tds", round(r["tds"]["m50"], 4), r["tds"]["class"], "e", round(r["e"], 5), "Verr200", round(r["unit_V_err_200s"]["max"], 6),
              "G1P", r["G1P_pre_event"]["pass"], "dpred_vs_cut", round(r["pred_margin_change_vs_cut_dispatch"], 5))
    if write:
        with open(C55.ART / "IEEE39_DEC061_D61_results.json", "x", encoding="utf-8") as f:
            json.dump(out, f, indent=1, default=float)
    return out


def gate():
    rk = json.loads((C55.ART / "IEEE39_DEC061_D61_results.json").read_text(encoding="utf-8"))
    blockers = [c for c in rk["unsafe_eligible"]] + ([] if rk["criteria"]["C2_targets_E4_H1H5"] else ["E4/H1-H5 target failure"]) + ([] if rk["criteria"]["C4ii_no_TDS_failure"] else ["TDS failure"])
    acta = {"gate": "G-v2 (DEC-061 protocol v2.0): OC1 revision 3, TUNE -> TEST", "ledger_used": T.Ledger(T.LEDGER).used(),
            "1_protocol_v2_compliance": {"criteria": rk["criteria"], "pass": rk["pass"], "iv_failing_cells": rk["iv_failing"], "unsafe_eligible": rk["unsafe_eligible"], "indeterminate": rk["indeterminate"]},
            "2_alternative_and_historical_results_not_in_the_verdict": {"iii_H_two_sided_historical": rk["historical_iii_H_two_sided"], "V_tail_diagnostic": {r["cell"]: r["V_tail_diagnostic"] for r in rk["cells"]},
                                                                       "note": "(iii-U) applied to new TDS but proposed after TUNE; it is NOT validated (IEEE39_DEC061_criterion_iii.md)"},
            "3_post_TUNE_changes": ["rev3 design set (b20 S3)", "criterion (iii-U)", "M3REV3 in dispatch/dispatch_z", "ledger block D61, R6 -> 0", "G1-P reduced form", "scan artefact replaced after an indexing bug"],
            "OC2": "no new design or TDS in this protocol; its DEC-059 verdict (G3 fail on (iii)) stands; no TEST cohort", "mandatory_safety_blocker": {"present": bool(blockers), "items": blockers},
            "registry": G.registry(), "dec061_code_sha256": {f: G.sha(C55.SRC / f) for f in ("dec061_design.py", "dec061_rev3.py", "dec061_settling.py")},
            "design_sha256": C54.sha_file(T.ST59 / "m3os_rev3_OC1.json"), "protocol_v2_sha256": C54.sha_file(C55.ROOT / "ops/sted/DEC061_protocol.md"), "TEST_intact": G.tests_intact(), "test_opened": False}
    ok = rk["pass"] and not blockers and acta["TEST_intact"]["pass"]
    acta["verdict"] = "APPROVED_FREEZE_REQUIRED" if ok else "REJECTED_TEST_SEALED"
    acta["TEST_cohort_OCs"] = ["OC1"] if ok else []
    with open(C55.ART / "IEEE39_DEC061_gate_TEST.json", "x", encoding="utf-8") as f:
        json.dump(acta, f, indent=1, default=float)
    print(acta["verdict"], acta["ledger_used"], rk["criteria"], "intact", acta["TEST_intact"]["pass"])


if __name__ == "__main__":
    {"plan": plan, "analyse": lambda: analyse("write" in sys.argv), "gate": gate}[sys.argv[1]]()
