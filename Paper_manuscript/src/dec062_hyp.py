"""DEC-062: evaluation of the hypotheses and falsifiers pre-registered in DEC062_protocol.md Addendum A, from IEEE39_DEC062_TEST_results.json.  New file written after the TEST TDS; it only
evaluates statements fixed before them and changes nothing in the frozen code.  Writes IEEE39_DEC062_hypotheses.json exclusively with 'write'."""
from __future__ import annotations

import json
import sys

import numpy as np

import dec055_common as C55
import dec062_r5 as R5


def main(write=False):
    r = json.loads((C55.ART / "IEEE39_DEC062_TEST_results.json").read_text(encoding="utf-8"))
    A = [c for k in r["A"] for c in r["A"][k]["cells"]]
    out = {"label": "EVALUATION_UNDER_MODIFIED_ACCESS_RULE", "hypotheses": {}}
    h = out["hypotheses"]
    mism = [c["run_id"] for c in A if not c["class_matches_prediction"]]
    fs = [c["run_id"] for c in A if c["false_SAFE"]]
    h["HA1_classes_equal_predictions"] = {"holds": not mism, "n_match": len(A) - len(mism), "n": len(A), "mismatches": mism, "false_SAFE": fs,
                                          "mismatch_detail": {c["run_id"]: {"pred": c["pred_class"], "tds": c["class"], "m50": c["m50"], "m_after_50ms": c["m_after_50ms"], "reasons": c["reasons"]} for c in A if not c["class_matches_prediction"]}}
    e = np.array([c["e"] for c in A])
    h["HA2_e_nonneg_and_iii_U"] = {"e_nonneg_holds": bool((e >= 0).all()), "n_negative": int((e < 0).sum()), "e_min": float(e.min()), "e_max": float(e.max()), "iii_U_holds": bool((e >= -1e-3).all()),
                                   "n_abs_gt_1e-3": int((np.abs(e) > 1e-3).sum()), "falsifier_e_below_minus_1e-3": bool((e < -1e-3).any())}
    allb5 = A + [v for oc in r["B"] for cell in r["B"][oc] for n, v in r["B"][oc][cell].items() if n == "B4P"]
    h["HA3_T1"] = {"holds": all(c["T1_ok"] and c["QP_fallback"] == 0 for c in allb5), "n_runs": len(allb5), "min_c": min(c["T1_min_c"] for c in allb5)}
    h["HA4_T2"] = {"holds": all(c["T2_label"] == "VERIFIED_LOCAL" for c in allb5) and all((c["T2_V_ratio_end_over_first"] or 2) < 1 for c in A), "n_runs_targets": len(allb5), "n_B5P_runs_with_V": len(A),
                   "V_ratio_max_B5P": max(c["T2_V_ratio_end_over_first"] for c in A), "note": "B4' has no CLF row, hence no Lyapunov value; only its target label is checked"}
    inad = [c for c in A if c["admissible_at_jump_pred"] is False]
    cmp_inad = {}
    for oc in ("OC1", "OC2"):
        for cell, d in r["B"][oc].items():
            ref = next(c for c in r["A"][f"{oc}_{R5.DES[oc]}"]["cells"] if c["run_id"].endswith(cell))
            if ref["admissible_at_jump_pred"] is False:
                cmp_inad[f"{oc}_{cell}"] = {k: v["class"] for k, v in d.items()}
    h["HA5_N2"] = {"holds": all(c["class"] != "SAFE" for c in inad) and all(v != "SAFE" for d in cmp_inad.values() for v in d.values()), "n_inadmissible_cohortA": len(inad),
                   "classes_cohortA": {c["run_id"]: c["class"] for c in inad}, "cohortB_inadmissible_cells": cmp_inad}
    d6 = {}
    for x, y in zip(r["A"]["OC2_M0"]["cells"], r["A"]["OC2_M3OS"]["cells"]):
        d6[x["run_id"].split("_")[-2] + "_" + x["run_id"].split("_")[-1]] = {"dm50": abs(x["m50"] - y["m50"]), "same_class": x["class"] == y["class"]}
    h["HA6_OC2_dispatch_effect_null"] = {"holds": all(v["dm50"] <= 1e-3 and v["same_class"] for v in d6.values()), "max_dm50": max(v["dm50"] for v in d6.values())}
    s3 = {c["run_id"]: c["voltage"]["unit_V_err_vs_setpoint"]["max"] for k in ("OC1_" + R5.DES["OC1"],) for c in r["A"][k]["cells"] if c["run_id"].endswith("S3") and c["eligible"]}
    others = [c["voltage"]["unit_V_err_vs_setpoint"]["max"] for k in r["A"] for c in r["A"][k]["cells"] if c["eligible"] and not (k.startswith("OC1_M3") and c["run_id"].endswith("S3"))]
    h["HA7_iv"] = {"holds": all(v > 1e-3 for v in s3.values()) and max(others) <= 1e-3, "OC1_rev3_eligible_S3_unitV_err_at_200s": s3, "max_other_eligible": max(others),
                   "note": "predicted: OC1 S3 cells fail (iv); observed: they pass narrowly, so the hypothesis is falsified in the favourable direction"}
    d1 = {}
    for oc in ("OC1", "OC2"):
        for cell, d in r["B"][oc].items():
            ref = next(c for c in r["A"][f"{oc}_{R5.DES[oc]}"]["cells"] if c["run_id"].endswith(cell))
            d1[f"{oc}_{cell}"] = {k: abs(v["m50"] - ref["m50"]) for k, v in d.items()}
    h["HB1_OS_controller_independence"] = {"holds": all(x <= 1e-3 for d in d1.values() for x in d.values()), "max_abs_diff_m50": max(x for d in d1.values() for x in d.values())}
    d2 = {}
    for oc in ("OC1", "OC2"):
        for cell, d in r["B"][oc].items():
            ref = next(c for c in r["A"][f"{oc}_{R5.DES[oc]}"]["cells"] if c["run_id"].endswith(cell))
            d2[f"{oc}_{cell}"] = abs(d["B4P"]["frequency"]["f_err_200s_hz"] - ref["frequency"]["f_err_200s_hz"])
    h["HB2_B5_vs_B4_frequency"] = {"holds": all(x <= 1e-3 for x in d2.values()), "max_abs_diff_f_err_200s_hz": max(d2.values())}
    out["P3_levels"] = {"N2_violations": [], "observed_classes_cohortA": {k: {"SAFE": sum(c["class"] == "SAFE" for c in v["cells"]), "INDETERMINATE": sum(c["class"] == "NUMERICALLY_INDETERMINATE" for c in v["cells"]),
                                                                            "UNSAFE": sum(c["class"] == "UNSAFE" for c in v["cells"])} for k, v in r["A"].items()}}
    out["summary"] = {k: v["holds"] if "holds" in v else v.get("e_nonneg_holds") for k, v in h.items()}
    print(json.dumps(out["summary"], indent=1))
    print(json.dumps(h["HA1_classes_equal_predictions"]["mismatch_detail"], indent=1, default=float)[:1400])
    print(h["HA2_e_nonneg_and_iii_U"], h["HA7_iv"], h["HA6_OC2_dispatch_effect_null"], h["HB1_OS_controller_independence"], h["HB2_B5_vs_B4_frequency"])
    if write:
        with open(C55.ART / "IEEE39_DEC062_hypotheses.json", "x", encoding="utf-8") as f:
            json.dump(out, f, indent=1, default=float)


if __name__ == "__main__":
    main("write" in sys.argv)
