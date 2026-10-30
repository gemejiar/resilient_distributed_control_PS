"""DEC-060 D1: formal audit of the sign of the OS predictor error and evaluation of a one-sided alternative to criterion (iii).  No TDS: pure post-processing of stored runs.
Sign convention: margin m = Pmax - P (positive = safe).  error e = m_TDS - m_pred.  e > 0: the prediction is pessimistic (conservative); e < 0: optimistic.
  (a) independent recomputation of the 50-ms minimum Pmax margin from the raw series of every TUNE run (vs the stored metric);
  (b) signed errors of the 16 TUNE cells and of the 18 calibration cells (dense model and dt-grid model);
  (c) counterfactual: criterion (iii) one-sided (e >= -floor) applied to the dt-grid predictor of M3 (known optimistic) and to the dense predictor;
  (d) false-SAFE bound of the one-sided criterion (analytic, then checked on the data).
The original two-sided criterion (iii) remains the primary TUNE result; this file is a post-TUNE amendment study (declared) and is never used to declare (iii) met.
  <venv python> dec060_audit.py [write]"""
from __future__ import annotations

import json
import sys

import numpy as np

import dec054_common as C54
import dec055_common as C55
import dec055_oc as OCM
import dec059_tds as T

U_D8, FLOOR = 0.0109, 1e-3
TE = C54.EVENT_T


def recompute_m50(run, pmax):
    z = np.load(T.RUNS / run / "series.npz", allow_pickle=True)
    t, P = z["t"], z["P"]
    k = (t >= TE - 1e-12) & (t <= TE + 0.05 + 1e-12)
    m = pmax[None, :] - P[k]
    return float(m.min()), int(k.sum()), int(np.unravel_index(m.argmin(), m.shape)[1])


def main(write=False):
    tr = json.loads((C55.ART / "IEEE39_DEC059_TUNE_results.json").read_text(encoding="utf-8"))
    out = {"stage": "DEC-060 D1 sign audit (no TDS)", "convention": "m = Pmax - P; e = m_TDS - m_pred; e > 0 conservative, e < 0 optimistic", "tune": {}, "calibration": {}}
    allerr = []
    for oc in ("OC1", "OC2"):
        pmax = OCM.make_plant(oc).limits["pmax"]
        rows = []
        for r in tr[oc]["cells"]:
            m_re, nsamp, iu = recompute_m50(r["run_id"], pmax)
            e = r["tds"]["m50"] - r["pred"]["pred_pmax_margin_min"]
            rows.append({"cell": r["cell"], "pred_m": r["pred"]["pred_pmax_margin_min"], "tds_m50_stored": r["tds"]["m50"], "tds_m50_recomputed": m_re, "recompute_abs_diff": abs(m_re - r["tds"]["m50"]),
                         "n_samples_50ms": nsamp, "e": e, "sign": "conservative" if e > 0 else "optimistic", "abs_e_gt_1e-3": abs(e) > FLOOR, "e_ge_minus_floor": e >= -FLOOR,
                         "pred_class": r["pred"]["pred_class_all"], "tds_class": r["tds"]["class"], "eligible": r["eligible_for_G3"]})
            allerr.append(e)
        out["tune"][oc] = rows
    e = np.array(allerr)
    out["tune_summary"] = {"n": len(e), "n_conservative": int((e > 0).sum()), "n_optimistic": int((e < 0).sum()), "min": float(e.min()), "max": float(e.max()), "n_abs_gt_floor": int((np.abs(e) > FLOOR).sum()),
                           "n_one_sided_violations": int((e < -FLOOR).sum()), "max_recompute_abs_diff": max(r["recompute_abs_diff"] for oc in out["tune"] for r in out["tune"][oc])}
    cal = json.loads((C55.ART / "IEEE39_DEC059_OS_calibration.json").read_text(encoding="utf-8"))
    dense = np.array([c["pmax_margin"]["dense_min"] - c["pmax_margin"]["tds_min"] for c in cal["cells"]])
    grid = np.array([c["pmax_margin"]["dtgrid_min"] - c["pmax_margin"]["tds_min"] for c in cal["cells"]])
    ed, eg = -dense, -grid                                           # e = m_TDS - m_pred
    out["calibration"] = {"n": len(ed), "dense": {"e_min": float(ed.min()), "e_max": float(ed.max()), "n_optimistic": int((ed < 0).sum()), "n_one_sided_violations": int((ed < -FLOOR).sum())},
                          "dt_grid_M3": {"e_min": float(eg.min()), "e_max": float(eg.max()), "n_optimistic": int((eg < 0).sum()), "n_one_sided_violations": int((eg < -FLOOR).sum()),
                                         "n_two_sided_violations": int((np.abs(eg) > FLOOR).sum())},
                          "note": "the dt-grid predictor is the M3 predictor refuted in DEC-057 (optimistic); the one-sided criterion must reject it, and the dense model must pass"}
    out["false_safe_bound"] = {"statement": "Let a cell be predicted SAFE (m_pred >= U_D8). If e >= -floor then m_TDS >= U_D8 - floor > -U_D8, so the TDS class cannot be UNSAFE; the worst admissible outcome is "
                                            "NUMERICALLY_INDETERMINATE (a downgrade, never counted as safe). With floor = 1e-3 and U_D8 = 0.0109: m_TDS >= 0.0099. For the post-50-ms "
                                            "binary margins the criterion is silent (the dense model covers only the first 50 ms).",
                               "floor": FLOOR, "U_D8": U_D8, "min_guaranteed_margin_if_pred_SAFE": U_D8 - FLOOR,
                               "data_check": {"pred_SAFE_and_TDS_UNSAFE": int(sum(r["pred_class"] == "SAFE" and r["tds_class"] == "UNSAFE" for oc in out["tune"] for r in out["tune"][oc]))}}
    out["limits"] = ["The one-sided floor is not independent of the TUNE data (it was chosen after seeing them): post-TUNE amendment, usable only for a new revision with its own TEST gate.",
                     "One-sidedness does not bound over-conservatism (e large positive): that costs dispatch cost J, not safety.",
                     "It covers the 50-ms Pmax peak only; Q, S, V and post-50-ms margins are classified on samples."]
    print(json.dumps({k: out[k] for k in ("tune_summary", "calibration", "false_safe_bound")}, indent=1, default=float)[:2500])
    if write:
        with open(C55.ART / "IEEE39_DEC060_sign_audit.json", "x", encoding="utf-8") as f:
            json.dump(out, f, indent=1, default=float)
    return out


if __name__ == "__main__":
    main("write" in sys.argv)
