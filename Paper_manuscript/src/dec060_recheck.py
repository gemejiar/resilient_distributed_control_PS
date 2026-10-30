"""DEC-060 D2: recheck of the OC1 single dynamic cut cycle (protocol Addendum C).  DESIGN/TUNE buses only (TEST never touched).
  plan      writes IEEE39_DEC060_RCK_plan.json exclusively (ledger block RES; sealed and committed before any TDS): G1-P at the cut dispatch + the 8 OC1 TUNE cells with B5' (frozen)
  analyse   [write]  per-cell classes, signed prediction errors, criteria (i)-(iv) literal, alternative readings kept apart, long-horizon diagnostic, mechanism; writes IEEE39_DEC060_RCK_results.json
  <venv python> dec060_recheck.py plan | analyse [write]  ;  run with:  dec059_tds.py run RCK"""
from __future__ import annotations

import json
import sys

import numpy as np

import dec054_common as C54
import dec055_common as C55
import dec059_metrics as M
import dec059_tds as T
import dec059_tune as TU

M_ = "M3CUT"
OC = "OC1"


def plan():
    runs = [{"oc": OC, "z": T.dispatch_z(OC, M_), "scenario": T.FLAT, "pflow_tol": None, "method": "trapezoid", "tol": 1e-4, "time_step_s": None, "activation_s": 1.0e9, "tf": 20.0,
             "controller": "B2", "reset_tiny": 0, "run_id": f"D60G1P_plant_flat_{OC}_{M_}",
             "purpose": "DEC-060 recheck G1-P: plant without secondary control at the OC1 cut dispatch, 20 s; frozen drift criteria 0.005 Hz / 1e-3 pu, buses in band"}]
    for bus in C55.TUNE:
        for sev in C55.TUNE_SEVERITIES:
            amp = round(C55.oc_amp(sev), 5)
            runs.append(T.b5_run(OC, {"bus": bus, "kind": "P", "amp": amp}, f"D60RCK_B5P_{OC}_{M_}_b{bus}P_{sev}",
                                 f"DEC-060 recheck cell b{bus}P_{sev}, OC1 cut dispatch, B5' (frozen parameters), local dt/16", f"r2_{OC}_{M_}_d0", f"r2_{OC}_{M_}_b{bus}P_{amp:.5f}", m=M_))
    p = {"stage": "DEC-060 lot RCK plan: OC1 cut-cycle recheck (sealed before any TDS of the lot)", "block": "RES", "runs": runs,
         "protocol_sha256": C54.sha_file(C55.ROOT / "ops/sted/DEC059_protocol.md"), "m3cut_sha256": C54.sha_file(T.ST59 / "m3os_cut_OC1.json"),
         "pred_sha256": {s: C54.sha_file(C55.ART / f"IEEE39_DEC059_pred_OC1_M3CUT_{s}.json") for s in ("design", "tune")},
         "code_sha256": {f: C54.sha_file(C55.SRC / f) for f in ("dec059_b5.py", "dec059_eq.py", "dec059_tds.py", "dec059_os.py", "dec059_pred.py", "dec059_metrics.py", "dec059_tune.py", "dec060_recheck.py")}}
    T.plan("RCK", p)


def vtail(run):
    """Diagnostic (D3), no TDS: decay of max|V_unit - V*| fitted on [100, 200] s, extrapolated to the time at which it reaches 1e-3."""
    z = np.load(T.RUNS / run / "series.npz", allow_pickle=True)
    cfg = json.loads((T.RUNS / run / "config.json").read_text(encoding="utf-8"))
    tg = dict(np.load(cfg["b5"]["post_target"]))
    t = z["t"]
    vu = z["V"][:, [b - 1 for b in C54.UNIT_BUS]]
    e = np.abs(vu - tg["V"][None, :]).max(axis=1)
    k = (t >= 100) & (t <= 200)
    sl, ic = np.polyfit(t[k], np.log(np.maximum(e[k], 1e-12)), 1)
    e200 = float(e[t >= t[-1] - 2].mean())
    t1e3 = float((np.log(1e-3) - ic) / sl) if sl < 0 else None
    return {"err_200s": e200, "decay_rate_1_per_s": float(sl), "t_reach_1e-3_s_extrapolated": t1e3, "fit_window_s": [100, 200]}


def analyse(write=False):
    import dec055_oc as OCM
    lim = OCM.make_plant(OC).limits
    pr = json.loads((C55.ART / f"IEEE39_DEC059_pred_{OC}_{M_}_tune.json").read_text(encoding="utf-8"))
    rows = []
    for c in pr["cells"]:
        run = f"D60RCK_B5P_{OC}_{M_}_b{c['bus']}P_{c['severity']}"
        m = M.metrics(run, lim)
        m["G_R3"] = M.gr3(m)
        cls, why = M.classify(m)
        adm = bool(c.get("admissible_at_jump", False))
        el = c["severity"] == "S2" or (c["severity"] == "S3" and adm)
        e = m["pmax_margin_min_50ms"] - c["pred_pmax_margin_min"]
        rows.append({"cell": c["name"], "run_id": run, "eligible_reading_A_rule_at_cut_dispatch": bool(el), "eligible_reading_B_fixed_at_TUNE": c["name"] in ("b7P_S2", "b20P_S2", "b16P_S2", "b24P_S2", "b7P_S3", "b16P_S3", "b24P_S3"),
                     "cut_cell": c["name"] in ("b20P_S2", "b16P_S3", "b24P_S3"), "admissible_at_jump_pred": adm,
                     "pred": {k: c.get(k) for k in ("jump_pmax_margin_min", "pred_pmax_margin_min", "pred_pmax_unit", "pred_class_all")},
                     "tds": {"m50": m["pmax_margin_min_50ms"], "m_after_50ms": m["pmax_margin_min_after_50ms"], "class": cls, "reasons": why, "qmax_margin": m["qmax_margin_min"], "s_margin": m["s_margin_min"],
                             "V_min": m["V_bus_min"], "V_max": m["V_bus_max"]},
                     "e_tds_minus_pred": e, "e_within_1e-3": abs(e) <= TU.EPS_FLOOR, "e_one_sided_ok": e >= -TU.EPS_FLOOR, "pred_class_matches": c.get("pred_class_all") == cls,
                     "G_R3": m["G_R3"], "target_labels": m.get("target_labels"), "regulation": {k: m.get(k) for k in ("f_coi_nadir_hz", "f_err_200s_hz", "settle_0p01Hz_s", "unit_V_err_end_vs_setpoint")},
                     "b5": m.get("b5"), "V_tail_diagnostic": vtail(run)})
    def g(sel, onesided=False):
        cells = [r for r in rows if sel(r)]
        gr = lambda r: all(v for k, v in r["G_R3"].items() if not (k.startswith("converged") or k.startswith("sharing")) or (r["target_labels"] or {}).get("H5_continuous", False))
        c = {"i_no_eligible_UNSAFE": not any(r["tds"]["class"] == "UNSAFE" for r in cells), "ii_no_TDS_failure": not any(r["tds"]["class"] == "TDS_NUMERICAL_FAILURE" for r in rows),
             "iii_OS_predictor": all((r["e_one_sided_ok"] if onesided else r["e_within_1e-3"]) for r in rows), "iv_GR3": all(gr(r) for r in cells if r["cell"] in [x["cell"] for x in cells])}
        return {"cells": [r["cell"] for r in cells], "criteria": c, "pass": all(c.values()), "unsafe": [r["cell"] for r in cells if r["tds"]["class"] == "UNSAFE"],
                "indeterminate": [r["cell"] for r in cells if r["tds"]["class"] == "NUMERICALLY_INDETERMINATE"], "iv_failing": [r["cell"] for r in cells if not gr(r)]}
    out = {"stage": "DEC-060 recheck results (OC1 cut dispatch, TUNE cells)", "cells": rows,
           "A_primary_protocol_literal": g(lambda r: r["eligible_reading_A_rule_at_cut_dispatch"]),
           "B_eligibility_fixed_at_TUNE": g(lambda r: r["eligible_reading_B_fixed_at_TUNE"]),
           "cut_cells_only": g(lambda r: r["cut_cell"]),
           "A_with_one_sided_iii_POST_TUNE_AMENDMENT": g(lambda r: r["eligible_reading_A_rule_at_cut_dispatch"], onesided=True)}
    for k in ("A_primary_protocol_literal", "B_eligibility_fixed_at_TUNE", "cut_cells_only", "A_with_one_sided_iii_POST_TUNE_AMENDMENT"):
        print(k, out[k]["pass"], out[k]["criteria"], "unsafe", out[k]["unsafe"], "iv fail", out[k]["iv_failing"])
    for r in rows:
        print(" ", r["cell"], "elig", r["eligible_reading_A_rule_at_cut_dispatch"], "pred", round(r["pred"]["pred_pmax_margin_min"], 4), "tds", round(r["tds"]["m50"], 4), r["tds"]["class"], "e", round(r["e_tds_minus_pred"], 5),
              "Verr200", round(r["V_tail_diagnostic"]["err_200s"], 5), "t1e-3", r["V_tail_diagnostic"]["t_reach_1e-3_s_extrapolated"])
    if write:
        with open(C55.ART / "IEEE39_DEC060_RCK_results.json", "x", encoding="utf-8") as f:
            json.dump(out, f, indent=1, default=float)
    return out


if __name__ == "__main__":
    {"plan": plan, "analyse": lambda: analyse("write" in sys.argv)}[sys.argv[1]]()
