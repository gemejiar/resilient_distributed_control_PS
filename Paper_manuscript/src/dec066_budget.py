"""DEC-066 controls (0 TDS; PF/linearisation only): convergence/restart of A and B, and designs at EQUAL redispatch budget for the D-versus-E contrast.
Same Algorithm 1 (dec054_opf, unchanged), K_max=8, N_it=25, ftol=1e-6, k0=4, 12 DESIGN events, as dec066_ablation.py.
  design <label> <dense 0|1> <eps_OS 0|1> <band_pu> <seed: A|B|M3> [workers]
     dense   : E = max(E_grid, E_dense 0-50 ms)         eps_OS : adds eps_OS up/dn          band : added to E_up and E_dn (pu)
     seed    : z of the starting point (NOTE: algorithm1 starts from plant.z_ref and uses the seed only on failure, unless DEC066_START=1) (A = DEC-055 M3, B = DEC066 abl_B, M3 = DEC-055 M3)    state: backups/DEC066_state/bud_<label>_OC1.json (exclusive)
  Labels used: A2 (restart of A from its own z), B2 (restart of B from its own z), EQ* (U-only band tuned to the effort of D), DQ* (dense+eps_OS band tuned to the effort of E)."""
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
OC = "OC1"
SEED = {"A": C54.RUNS_DIR.parent / "DEC055_state" / "m3_OC1.json", "M3": C54.RUNS_DIR.parent / "DEC055_state" / "m3_OC1.json", "B": STATE / "abl_B_OC1.json", "C": STATE / "abl_C_OC1.json", "E": STATE / "abl_E_OC1.json", "D": C54.RUNS_DIR.parent / "DEC059_state" / "m3os_OC1.json"}


def design(label, dense, eos, band, seed, workers=2):
    import dec054_g4_design as G4
    import dec054_opf as OPF
    import dec055_l0 as L0
    import dec059_os as OS
    t0 = time.time()
    cal = json.loads((C55.ART / "IEEE39_DEC059_OS_calibration.json").read_text(encoding="utf-8"))["summary"]
    z0 = np.array(json.loads(SEED[seed].read_text(encoding="utf-8"))["z"])
    m3 = np.array(json.loads(SEED["M3"].read_text(encoding="utf-8"))["z"])
    eJ, eEu, eEd = G4.eps_vectors()
    add_u = band + (cal["eps_OS_up"] if eos else 0.0)
    add_d = band + (cal["eps_OS_dn"] if eos else 0.0)
    if os.environ.get("DEC066_START") == "1":      # start-point sensitivity: algorithm1 always tries plant.z_ref first and uses z_seeds only if that start fails, so the first start is replaced by z0
        _orig = OPF.solve_nlp
        zr = np.array(OCM.make_plant(OC).z_ref, float)
        OPF.solve_nlp = lambda pb, W, s0: _orig(pb, W, z0 if np.allclose(s0, zr) else s0)
    if dense:
        OCM._init_worker = OS._init_worker_os
    plant = OCM.OCPooledPlant(OC, int(workers))
    cfg = dict(C54.PROPOSED, K_max=8, N_it=int(os.environ.get("DEC059_NIT", "25")), ftol=1e-6, verbose=False)
    try:
        r = OPF.algorithm1(plant, "M3", L0.design_scenarios(), eJ, eEu + add_u, cfg=cfg, z_seeds=[z0], k0=4, eps_E_dn=eEd + add_d,
                           log=lambda x: print(label, "  iter", {k: x[k] for k in ("k", "W", "min_margin", "J")}, flush=True))
        out = {"label": label, "oc": OC, "dense": bool(dense), "eps_OS": bool(eos), "band": band, "eps_add_up": add_u, "eps_add_dn": add_d, "seed": seed, "start_replaced": os.environ.get("DEC066_START") == "1", "status": r.status, "J": r.J, "kkt": r.kkt_residual,
               "log": r.log, "z": None if r.z is None else r.z.tolist(), "plant_evaluations": plant.n_eval, "seconds": round(time.time() - t0, 1)}
        if r.z is not None:
            out.update({"redispatch_MW_abs_sum_vs_case": float(np.abs(r.z[:9] - plant.z_ref[:9]).sum() * 100), "redispatch_MW_abs_sum_vs_M3": float(np.abs(r.z[:9] - m3[:9]).sum() * 100),
                        "dz_vs_seed_max": float(np.abs(r.z - z0).max())})
        STATE.mkdir(parents=True, exist_ok=True)
        with open(STATE / f"bud_{label}_{OC}.json", "x", encoding="utf-8") as f:
            json.dump(out, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else float(o))
        print(label, r.status, r.J, out.get("redispatch_MW_abs_sum_vs_case"), out["seconds"], "s", flush=True)
    finally:
        plant.close()


if __name__ == "__main__":
    if sys.argv[1] == "design":
        design(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5]), sys.argv[6], *(int(x) for x in sys.argv[7:8]))
