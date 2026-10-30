"""DEC-066 P2: ablation of the overshoot (OS) components of M3+OS at the SAME design set, objective, base constraints, solver, cfg, seed and starting point (0 TDS; PF/linearisation only).
M3+OS (dec059_os.stage_design) differs from the historical M3 (DEC-055) in THREE simultaneous ways:
   (i) dense 0-50 ms excursion:  E = max(E_grid(0-195 s), E_dense)         [dec059_os.os_excursion]
  (ii) empirical overshoot term: eps_OS_up = 3.88e-4, eps_OS_dn = 6.1e-5 pu [IEEE39_DEC059_OS_calibration.json]
 (iii) numerical band U_D8 = 0.0109 pu added to E_up and E_dn               (by far the largest)
Variants (OC1 only; all use dec054_opf.algorithm1 unchanged, K_max=8, N_it=25, ftol=1e-6, k0=4, seed = DEC-055 M3 z, scenarios dec055_l0.design_scenarios()):
  A  historical M3                       (existing DEC-055 state, not rerun)
  B  M3 + dense                          eps = eps_M3                         (dense yes, eps_OS no, U_D8 no)
  C  M3 + dense + eps_OS                 eps = eps_M3 + eps_OS                (U_D8 no)
  E  M3 + U_D8 only (control)            eps = eps_M3 + U_D8, standard excursion (no dense, no eps_OS)
  D  M3+OS as implemented                (existing DEC-059 state, not rerun)
States are written exclusively to backups/DEC066_state/abl_<V>_<OC>.json.  Run: <venv python> dec066_ablation.py design <V> <OC> [workers]"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

import dec054_common as C54
import dec055_common as C55
import dec055_oc as OCM

STATE = C54.RUNS_DIR.parent / "DEC066_state"
U_D8 = 0.0109


def design(variant, oc, workers=3):
    import dec054_g4_design as G4
    import dec054_opf as OPF
    import dec055_l0 as L0
    import dec059_os as OS
    t0 = time.time()
    cal = json.loads((C55.ART / "IEEE39_DEC059_OS_calibration.json").read_text(encoding="utf-8"))["summary"]
    m3 = json.loads((C55.STATE / f"m3_{oc}.json").read_text(encoding="utf-8"))
    scen = L0.design_scenarios()
    eJ, eEu, eEd = G4.eps_vectors()
    dense, add_u, add_d = {"B": (True, 0.0, 0.0), "C": (True, cal["eps_OS_up"], cal["eps_OS_dn"]), "E": (False, U_D8, U_D8)}[variant]
    if dense:
        OCM._init_worker = OS._init_worker_os
    plant = OCM.OCPooledPlant(oc, int(workers))
    cfg = dict(C54.PROPOSED, K_max=8, N_it=int(os.environ.get("DEC059_NIT", "25")), ftol=1e-6, verbose=False)
    try:
        r = OPF.algorithm1(plant, "M3", scen, eJ, eEu + add_u, cfg=cfg, z_seeds=[np.array(m3["z"])], k0=4, eps_E_dn=eEd + add_d,
                           log=lambda x: print(variant, oc, "  iter", {k: x[k] for k in ("k", "W", "min_margin", "J")}, flush=True))
        out = {"variant": variant, "oc": oc, "dense": dense, "eps_add_up": add_u, "eps_add_dn": add_d, "status": r.status, "J": r.J, "kkt": r.kkt_residual, "iterations": r.iterations, "detail": r.detail, "cuts": r.cuts, "log": r.log,
               "z": None if r.z is None else r.z.tolist(), "seed": "DEC-055 M3 of the OC", "n_scenarios": len(scen), "event_tasks": plant.n_event_tasks, "plant_evaluations": plant.n_eval, "seconds": round(time.time() - t0, 1)}
        if r.z is not None:
            e = plant.evaluate(r.z)
            out.update({"init_ok": bool(e["ok"]), "redispatch_MW_abs_sum_vs_case": float(np.abs(r.z[:9] - plant.z_ref[:9]).sum() * 100), "redispatch_MW_abs_sum_vs_M3": float(np.abs(r.z[:9] - np.array(m3["z"])[:9]).sum() * 100)})
        STATE.mkdir(parents=True, exist_ok=True)
        with open(STATE / f"abl_{variant}_{oc}.json", "x", encoding="utf-8") as f:
            json.dump(out, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else float(o))
        print(variant, oc, r.status, r.J, out["seconds"], "s", flush=True)
    finally:
        plant.close()


if __name__ == "__main__":
    if sys.argv[1] == "design":
        design(sys.argv[2], sys.argv[3], *(sys.argv[4:5] or [3]))
