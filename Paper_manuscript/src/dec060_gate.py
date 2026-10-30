"""DEC-060 gate TUNE -> TEST after the OC1 cut recheck (protocol Addendum C item 4).  The acta separates (1) compliance with the original protocol, (2) results under alternative
criteria, (3) post-TUNE changes.  Writes IEEE39_DEC060_gate_TEST.json exclusively; TEST is never opened by this script.
  <venv python> dec060_gate.py"""
from __future__ import annotations

import json

import numpy as np

import dec054_common as C54
import dec055_common as C55
import dec055_oc as OCM
import dec059_gate as G
import dec059_metrics as M
import dec059_tds as T

OC, M_ = "OC1", "M3CUT"


def main():
    rk = json.loads((C55.ART / "IEEE39_DEC060_RCK_results.json").read_text(encoding="utf-8"))
    tr = json.loads((C55.ART / "IEEE39_DEC059_TUNE_results.json").read_text(encoding="utf-8"))
    pmax = OCM.make_plant(OC).limits["pmax"]
    run = f"D60G1P_plant_flat_{OC}_{M_}"
    z, st, cfg, _ = M._load(run)
    f = z["f_bus_hz"]
    g1 = {"status": st["status"], "t_end": float(z["t"][-1]), "max_abs_df_hz": float(np.abs(f - f[0]).max()), "max_abs_dV_pu": float(np.abs(z["V"] - z["V"][0]).max()), "V_min": float(z["V"].min()), "V_max": float(z["V"].max())}
    g1["pass"] = bool(st["status"] != "TDS_NUMERICAL_FAILURE" and g1["t_end"] >= 19.99 and g1["max_abs_df_hz"] <= 0.005 and g1["max_abs_dV_pu"] <= 1e-3 and g1["V_min"] >= 0.95 and g1["V_max"] <= 1.05)
    za = np.array(json.loads((T.ST59 / "m3os_OC1.json").read_text(encoding="utf-8"))["z"])
    zb = np.array(json.loads((T.ST59 / "m3os_cut_OC1.json").read_text(encoding="utf-8"))["z"])
    d = zb - za
    mech = {"unit_order": C54.UNIT_BUS, "dP_setpoint_by_unit_pu": d[:10].tolist(), "largest_change_unit_bus": int(C54.UNIT_BUS[int(np.argmax(np.abs(d[:10])))]), "max_other_component_change": float(np.sort(np.abs(d))[-2]),
            "pmax_SG33_pu": float(pmax[2]), "SG33_P_before_after": [float(za[2]), float(zb[2])], "cells": []}
    for r in rk["cells"]:
        s = np.load(T.RUNS / r["run_id"] / "series.npz", allow_pickle=True)
        t, P = s["t"], s["P"]
        k = (t >= C54.EVENT_T - 1e-12) & (t <= C54.EVENT_T + 0.05 + 1e-12)
        m = pmax[None, :] - P[k]
        iu = int(np.unravel_index(m.argmin(), m.shape)[1])
        mech["cells"].append({"cell": r["cell"], "binding_unit_bus": int(C54.UNIT_BUS[iu]), "predicted_unit": r["pred"]["pred_pmax_unit"], "m50": float(m.min()), "m_after_50ms": r["tds"]["m_after_50ms"],
                              "subcycle_is_binding": bool(r["tds"]["m50"] < r["tds"]["m_after_50ms"])})
    A = rk["A_primary_protocol_literal"]
    blockers = [c for c in A["unsafe"]]
    acta = {"gate": "TUNE -> TEST after the OC1 cut recheck (DEC-060)", "ledger_used": T.Ledger(T.LEDGER).used(), "G1P_cut_dispatch": g1, "mechanism_H_B": mech,
            "1_original_protocol_compliance": {"OC1_reading_A_literal": {"G3_pass": A["pass"], "criteria": A["criteria"], "unsafe_eligible": A["unsafe"], "iv_failing_cells": A["iv_failing"], "indeterminate": A["indeterminate"]},
                                               "OC2": {"G3_pass": tr["OC2"]["G3"]["pass"], "criteria": tr["OC2"]["G3"]["criteria"], "cut_cycle": "none available (no UNSAFE cell); G3 fail on (iii) is final under the protocol"},
                                               "TEST_cohort_OCs": []},
            "2_alternative_results_not_used_for_the_verdict": {"B_eligibility_fixed_at_TUNE": {"pass": rk["B_eligibility_fixed_at_TUNE"]["pass"], "criteria": rk["B_eligibility_fixed_at_TUNE"]["criteria"]},
                                                              "cut_cells_only": {"pass": rk["cut_cells_only"]["pass"], "criteria": rk["cut_cells_only"]["criteria"]},
                                                              "A_with_one_sided_iii": {"pass": rk["A_with_one_sided_iii_POST_TUNE_AMENDMENT"]["pass"], "criteria": rk["A_with_one_sided_iii_POST_TUNE_AMENDMENT"]["criteria"]},
                                                              "sign_audit": "IEEE39_DEC060_sign_audit.json", "V_tail_diagnostic_per_cell": {r["cell"]: r["V_tail_diagnostic"] for r in rk["cells"]}},
            "3_post_TUNE_changes": ["dispatch_z accepts M3CUT", "recheck set wider than the protocol text (8 cells, b20 S3 newly eligible)", "one-sided criterion (iii) study (alternative only)", "long-horizon voltage extrapolation (diagnostic only)", "ledger block RES used"],
            "mandatory_safety_blocker": {"present": bool(blockers), "cells": blockers, "meaning": "an eligible cell is UNSAFE in TDS (pre-registered H-D)"},
            "registry": G.registry(), "recheck_code_sha256": {f: G.sha(C55.SRC / f) for f in ("dec060_audit.py", "dec060_recheck.py", "dec060_gate.py")}, "TEST_intact": G.tests_intact(), "test_opened": False}
    acta["verdict"] = "APPROVED" if (A["pass"] and not blockers and acta["TEST_intact"]["pass"]) else "REJECTED_TEST_SEALED"
    with open(C55.ART / "IEEE39_DEC060_gate_TEST.json", "x", encoding="utf-8") as fh:
        json.dump(acta, fh, indent=1, default=float)
    print(acta["verdict"], acta["ledger_used"], mech["largest_change_unit_bus"], [(c["cell"], c["binding_unit_bus"], c["subcycle_is_binding"]) for c in mech["cells"]], "G1P", g1["pass"], "intact", acta["TEST_intact"]["pass"])


if __name__ == "__main__":
    main()
