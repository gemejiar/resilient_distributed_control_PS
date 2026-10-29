"""DEC-059 TUNE analysis (Addendum B): per cell, the pre-TDS prediction (dec059_pred), the TDS metrics and class (dec059_metrics), the three error sources kept apart
(OS predictor error, U_D8 band, physical margin), the B5' conditions (G-R3) and the gate G3 per OC.  Writes IEEE39_DEC059_TUNE_results.json exclusively with 'write'.
  <venv python> dec059_tune.py [write]"""
from __future__ import annotations

import json
import sys

import numpy as np

import dec054_common as C54
import dec055_common as C55
import dec059_metrics as M
import dec059_tds as T

U_D8 = M.U_D8
EPS_FLOOR = 1e-3


def cell_rows(oc, lim):
    pr = json.loads((C55.ART / f"IEEE39_DEC059_pred_{oc}_M3OS_tune.json").read_text(encoding="utf-8"))
    rows = []
    for c in pr["cells"]:
        run = f"D59TUNE_B5P_{oc}_M3OS_b{c['bus']}P_{c['severity']}"
        m = M.metrics(run, lim)
        m["G_R3"] = M.gr3(m)
        cls, why = M.classify(m)
        eligible = c["severity"] == "S2" or (c["severity"] == "S3" and c.get("admissible_at_jump", False))
        row = {"cell": c["name"], "run_id": run, "eligible_for_G3": bool(eligible), "label": None, "pred": {k: c.get(k) for k in ("jump_pmax_margin_min", "pred_pmax_margin_min", "pred_pmax_unit", "pred_class_pmax", "pred_class_all", "admissible_at_jump")},
               "tds": {"m50": m["pmax_margin_min_50ms"], "m_after_50ms": m["pmax_margin_min_after_50ms"], "class": cls, "reasons": why, "pmin_margin": m["pmin_margin_min"], "qmax_margin": m["qmax_margin_min"],
                       "s_margin": m["s_margin_min"], "V_min": m["V_bus_min"], "V_max": m["V_bus_max"]},
               "errors": {"OS_predictor_error_pmax_margin(tds-pred)": m["pmax_margin_min_50ms"] - c["pred_pmax_margin_min"], "D8_band_U": U_D8, "physical_margin_m50": m["pmax_margin_min_50ms"]},
               "regulation": {k: m.get(k) for k in ("f_coi_nadir_hz", "rocof_100ms_hz_s", "f_err_120s_hz", "f_err_200s_hz", "settle_0p01Hz_s", "unit_V_err_end_vs_setpoint", "unit_V_err_end_vs_1pu", "sharing_std_free_units_end")},
               "b5": m.get("b5"), "target_labels": m.get("target_labels"), "target": m.get("target"), "G_R3": m["G_R3"]}
        row["label"] = ("INADMISSIBLE_AT_EVENT" if not c.get("admissible_at_jump", False) else
                        ("STRESS_EXPLORATORY" if not eligible else cls))
        row["predictor_within_tolerance"] = bool(abs(row["errors"]["OS_predictor_error_pmax_margin(tds-pred)"]) <= EPS_FLOOR)
        rows.append(row)
    return rows


def g3(rows):
    el = [r for r in rows if r["eligible_for_G3"]]
    c = {"i_no_eligible_UNSAFE": not any(r["tds"]["class"] == "UNSAFE" for r in el),
         "ii_no_TDS_failure": not any(r["tds"]["class"] == "TDS_NUMERICAL_FAILURE" for r in rows),
         "iii_OS_predictor_within_1e-3": all(r["predictor_within_tolerance"] for r in rows if r["tds"]["class"] != "TDS_NUMERICAL_FAILURE"),
         "iv_B5_conditions_GR3": all(all(v for k, v in r["G_R3"].items() if not (k.startswith("converged") or k.startswith("sharing")) or (r["target_labels"] or {}).get("H5_continuous", False))
                                     for r in rows)}
    return {"criteria": c, "pass": all(c.values()), "n_eligible": len(el), "eligible_cells": [r["cell"] for r in el],
            "n_SAFE": sum(r["tds"]["class"] == "SAFE" for r in el), "n_INDETERMINATE": sum(r["tds"]["class"] == "NUMERICALLY_INDETERMINATE" for r in el),
            "n_UNSAFE": sum(r["tds"]["class"] == "UNSAFE" for r in el), "unsafe_eligible_cells": [r["cell"] for r in el if r["tds"]["class"] == "UNSAFE"]}


def main(write=False):
    import dec055_oc as OCM
    out = {"stage": "DEC-059 TUNE (R4), B5' frozen parameters at the M3+OS dispatch, local dt/16"}
    for oc in ("OC1", "OC2"):
        lim = OCM.make_plant(oc).limits
        rows = cell_rows(oc, lim)
        out[oc] = {"cells": rows, "G3": g3(rows)}
        print(oc, "G3", out[oc]["G3"]["pass"], out[oc]["G3"]["criteria"], "UNSAFE eligible:", out[oc]["G3"]["unsafe_eligible_cells"])
        for r in rows:
            print(" ", r["cell"], r["label"], "pred", round(r["pred"]["pred_pmax_margin_min"], 4), "tds m50", round(r["tds"]["m50"], 4), r["tds"]["class"], "err", round(r["errors"]["OS_predictor_error_pmax_margin(tds-pred)"], 5),
                  "f200", r["regulation"].get("f_err_200s_hz"))
    if write:
        with open(C55.ART / "IEEE39_DEC059_TUNE_results.json", "x", encoding="utf-8") as f:
            json.dump(out, f, indent=1, default=float)
    return out


if __name__ == "__main__":
    main("write" in sys.argv)
