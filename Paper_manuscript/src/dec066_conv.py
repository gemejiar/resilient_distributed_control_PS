"""DEC-066 T4e: convergence / start-point sensitivity of the OPF designs (0 TDS).  Groups: same problem, different start (algorithm1 starts from plant.z_ref unless DEC066_START=1 replaces it).
Writes artifacts/IEEE39_DEC066_T4e_convergence.csv (exclusive).  Run: <venv python> dec066_conv.py write"""
from __future__ import annotations

import csv
import json
import sys

import numpy as np

import dec054_common as C54
import dec055_common as C55

ST = C54.RUNS_DIR.parent
P = {"A": "DEC055_state/m3_OC1.json", "B": "DEC066_state/abl_B_OC1.json", "C": "DEC066_state/abl_C_OC1.json", "D": "DEC059_state/m3os_OC1.json", "E": "DEC066_state/abl_E_OC1.json"}
for k in ("A2", "A3", "B2", "B3", "B4", "EQ1", "EQ2", "DQ1", "DQ2"):
    P[k] = f"DEC066_state/bud_{k}_OC1.json"
GROUP = {"A": "A", "A2": "A", "A3": "A", "B": "B", "B2": "B", "B3": "B", "B4": "B", "C": "C", "D": "D", "E": "E", "EQ1": "EQ", "EQ2": "EQ", "DQ1": "DQ", "DQ2": "DQ"}
START = {"A": "case dispatch (z_ref) [+ M0/M3 fallback seeds]", "A2": "z_ref (seed A only on failure)", "A3": "replaced by D", "B": "z_ref (M3 seed on failure)", "B2": "z_ref (seed B on failure)", "B3": "replaced by C", "B4": "replaced by D",
         "C": "z_ref (M3 seed on failure)", "D": "z_ref (M3 seed on failure)", "E": "z_ref (M3 seed on failure)", "EQ1": "z_ref", "EQ2": "replaced by D", "DQ1": "z_ref", "DQ2": "replaced by E"}


def main(write=False):
    S = {k: json.loads((ST / p).read_text(encoding="utf-8")) for k, p in P.items()}
    m0 = json.loads((ST / "DEC055_state/m0_OC1.json").read_text(encoding="utf-8"))
    zref = np.array(m0["z_ref"])
    rows = []
    for k, s in S.items():
        z = np.array(s["z"])
        ref = next(g for g in S if GROUP[g] == GROUP[k])                     # first member of the group
        zr = np.array(S[ref]["z"])
        rows.append({"design": k, "group": GROUP[k], "start": START[k], "status": s["status"], "J": "" if s["J"] is None else round(s["J"], 7), "kkt_residual": "" if s["kkt"] is None else round(float(s["kkt"]), 4), "sum_abs_dP_vs_case_MW": round(float(np.abs(z[:9] - zref[:9]).sum() * 100), 3),
                     "max_abs_dz_vs_group_first": float(f"{np.abs(z - zr).max():.2e}"), "dJ_vs_group_first": "" if s["J"] is None else float(f"{s['J'] - S[ref]['J']:.2e}"), "min_internal_margin_final_iter": "" if not s["log"] else float(f"{s['log'][-1]['min_margin']:.2e}"), "plant_evals": s.get("plant_evaluations")})
    print("kkt_tol", C54.PROPOSED.get("kkt_tol"))
    for r in rows:
        print(r)
    if write:
        with open(C55.ART / "IEEE39_DEC066_T4e_convergence.csv", "x", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    main("write" in sys.argv)
