"""DEC-054 G7 ablations (post-hoc, NO TDS): (A1) M0->M2 value of the jump, (A2) M2->M3 value of the excursion + multi-contingency, (A3) M1->M3, and
(A5) predictor with the correct I(z) versus the stale initialisation of the historical dispatch z_ref (DEC-051 hazard), on the frozen test events and the frozen dispatches.
Writes IEEE39_DEC054_ablation.csv and IEEE39_DEC054_ablation_I_of_z.json exclusively."""
from __future__ import annotations

import csv
import json

import numpy as np

import dec054_common as COM
import dec054_opf as OPF
import dec054_p3a_audit as P3A
import dec054_plant as PL
import dec054_predictor as PRD


def main():
    frozen = json.loads((COM.ART / "IEEE39_DEC054_design_frozen.json").read_text(encoding="utf-8"))
    summ = json.loads((COM.ART / "IEEE39_DEC054_prospective_summary.json").read_text(encoding="utf-8"))["summary"]
    rows = []
    for a, b, label in (("M0", "M2", "A1 value of modelling the algebraic jump (M0 -> M2)"), ("M2", "M3", "A2 value of the excursion + multi-contingency (M2 -> M3)"), ("M1", "M3", "A3 static reserve vs M3 (M1 -> M3)")):
        sa, sb = summ[a], summ[b]
        rows.append({"ablation": label, "from": a, "to": b, "violating_pairs_P_from": sa["violating_pairs_P"], "violating_pairs_P_to": sb["violating_pairs_P"], "scenarios_with_P_violation_from": sa["scenarios_with_P_violation"],
                     "scenarios_with_P_violation_to": sb["scenarios_with_P_violation"], "total_P_excess_from_pu": sa["total_P_excess_pu"], "total_P_excess_to_pu": sb["total_P_excess_pu"], "design_J_from": sa["design_J"], "design_J_to": sb["design_J"]})
    with open(COM.ART / "IEEE39_DEC054_ablation.csv", "x", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    # A5: predictor with correct vs stale I(z)
    P = PL.AndesPlant()
    z_ref = P.z_ref
    stale = P.stale_state(z_ref)
    res = {}
    for m in ("M3", "M2", "M1", "M0"):
        z = np.array(frozen["dispatches"][m]["z"])
        for s in frozen["scenarios_test"]["scenarios"]:
            rid = f"P3-C_{s['name']}_{m}"
            d = COM.RUNS_DIR / rid
            if not (d / "series.npz").exists():
                continue
            ser = np.load(d / "series.npz")
            sc = OPF.Scenario(s["name"], s["bus"], s["kind"], s["amp"])
            j = P.jump(z, sc)
            out = {}
            for tag, stl in (("correct_I", None), ("stale_I", stale)):
                A, f, C = P.affine(z, sc, stale=stl)
                x = PRD.excursion(A, f, C)
                cr = P3A.compare_run(ser["t"], ser["P"], j["dP"], x["t"], x["D"])
                out[tag] = {"peak_error": cr["e_peak"].tolist(), "trough_error": cr["e_trough"].tolist(), "max_abs_peak_error": float(np.abs(cr["e_peak"]).max()), "max_abs_trough_error": float(np.abs(cr["e_trough"]).max()),
                            "E_up": x["E_up"].tolist(), "E_dn": x["E_dn"].tolist()}
            out["E_up_difference_max"] = float(np.abs(np.array(out["correct_I"]["E_up"]) - np.array(out["stale_I"]["E_up"])).max())
            res[rid] = out
            print(rid, round(out["correct_I"]["max_abs_peak_error"], 4), round(out["stale_I"]["max_abs_peak_error"], 4), flush=True)
    with open(COM.ART / "IEEE39_DEC054_ablation_I_of_z.json", "x", encoding="utf-8") as f:
        json.dump({"runs": res, "reading": "peak/trough errors (observed - predicted) with the correct initialisation I(z) of the executed dispatch vs the stale I(z_ref); A5 of the design"}, f, indent=1)


if __name__ == "__main__":
    main()
