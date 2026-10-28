"""DEC-054 G4: offline design of M0-M3 on the real IEEE-39 plant (PF + TDS.init + algebraic jump + affine predictor only; NO TDS).
Design events: P +0.58564 pu at the DESIGN and TUNE buses {8,23,28,25,7,20,16,24}; margins eps from the P3-A DESIGN calibration.
Stages (each writes an exclusive state file and can be resumed): m0, m3, m2, m1.  Run: <venv python> dec054_g4_design.py <stage>"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np

import dec054_common as COM
import dec054_opf as OPF
import dec054_pool as POOL

STATE = COM.RUNS_DIR.parent / "DEC054_g4_state"
AMP = 0.58564
RHO_GRID = [0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.15, 0.20]
RHO_REFINE = [0.065, 0.07, 0.075]       # predeclared refinement between the last non-compliant and the first compliant grid value (statics only)      # predeclared M1 grid (static/predicted DESIGN+TUNE evaluation only)


def eps_vectors():
    a = json.loads((COM.ART / "IEEE39_DEC054_p3a_analysis.json").read_text(encoding="utf-8"))["eps_calibration"]["P_events"]
    fl = COM.PROPOSED["eps_floor_pu"]
    return (np.full(10, fl), np.array([a[u]["eps_E_up"] for u in COM.UNITS]), np.array([a[u]["eps_E_dn"] for u in COM.UNITS]))


def scenarios():
    return [OPF.Scenario(f"b{b}P", b, "P", AMP) for b in COM.DESIGN + COM.TUNE]


def describe(plant, z, scen, eJ, eEu, eEd, label=""):
    """Predicted full (jump + excursion + eps) margins at z for all design events + base constraints + cost terms (identical definition for every method)."""
    pb = OPF.Problem(plant, "M3", scen, eJ, eEu, cfg=dict(COM.PROPOSED), eps_E_dn=eEd)
    e = plant.evaluate(z)
    mg = pb.all_margins(z)
    up = np.array([mg[d][0] for d in range(len(scen))])
    dn = np.array([mg[d][1] for d in range(len(scen))])
    base = pb.base(z)
    lim = plant.limits
    return {"label": label, "z": np.asarray(z).tolist(), "init_ok": bool(e["ok"]), "P_pre": e["P"].tolist(), "Q_pre": e["Q"].tolist(), "V_min": float(e["V"].min()), "V_max": float(e["V"].max()),
            "reserve_P": (lim["pmax"] - e["P"]).tolist(), "base_min_margin": float(base.min()), "C_disp": pb.C_disp(z), "C_pat": pb.C_pat(z), "J": pb.J(z),
            "redispatch_MW_abs_sum": float(np.abs((np.asarray(z)[:9] - plant.z_ref[:9])).sum() * 100.0),
            "pred_margin_upper_min_by_unit": up.min(axis=0).tolist(), "pred_margin_lower_min_by_unit": dn.min(axis=0).tolist(),
            "pred_margin_min": float(min(up.min(), dn.min())), "n_violated_margins": int((up < -1e-4).sum() + (dn < -1e-4).sum()), "n_violating_events": int(((up < -1e-4).any(axis=1) | (dn < -1e-4).any(axis=1)).sum()),
            "k_ip": float(e["I"]["k_ip"]), "violating_units": sorted({COM.UNITS[i] for r in np.argwhere(up < -1e-4) for i in [r[1]]} | {COM.UNITS[i] for r in np.argwhere(dn < -1e-4) for i in [r[1]]})}


def save_state(name, obj):
    STATE.mkdir(parents=True, exist_ok=True)
    with open(STATE / f"{name}.json", "x", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, default=float)


def load_state(name):
    p = STATE / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def main(stage):
    t0 = time.time()
    plant = POOL.PooledPlant(int(os.environ.get("DEC054_WORKERS", "7")))
    scen = scenarios()
    eJ, eEu, eEd = eps_vectors()
    cfg = dict(COM.PROPOSED, K_max=8, N_it=int(os.environ.get("DEC054_NIT", "25")), ftol=1e-6, verbose=True)
    print("setup", round(time.time() - t0, 1), "s; z_ref valid:", plant.evaluate(plant.z_ref)["ok"], flush=True)
    try:
        if stage == "m0":
            r = OPF.solve_static(plant, "M0", scen, cfg=cfg)
            out = {"method": "M0", "status": r.status, "J": r.J, "iterations": r.iterations, "kkt": r.kkt_residual, "detail": r.detail, "seconds": round(time.time() - t0, 1)}
            if r.z is not None:
                out["describe"] = describe(plant, r.z, scen, eJ, eEu, eEd, "M0")
            save_state("m0", out)
        elif stage in ("m2", "m3"):
            m0 = load_state("m0")
            seeds = [np.array(m0["describe"]["z"])] if m0 and "describe" in m0 else []
            r = OPF.algorithm1(plant, stage.upper(), scen, eJ, eEu, cfg=cfg, z_seeds=seeds, k0=int(os.environ.get("DEC054_K0", "4")), eps_E_dn=eEd, log=lambda x: print("  iter", x, flush=True))
            out = {"method": stage.upper(), "status": r.status, "J": r.J, "iterations": r.iterations, "kkt": r.kkt_residual, "detail": r.detail, "cuts": r.cuts, "log": r.log, "seconds": round(time.time() - t0, 1),
                   "event_tasks": plant.n_event_tasks, "plant_evaluations": plant.n_eval}
            if r.z is not None:
                out["describe"] = describe(plant, r.z, scen, eJ, eEu, eEd, stage.upper())
            save_state(stage, out)
        elif stage in ("m1", "m1b"):
            res = []
            for rho in (RHO_GRID if stage == "m1" else RHO_REFINE):
                r = OPF.solve_static(plant, "M1", scen, rho=rho, cfg=cfg)
                item = {"rho": rho, "status": r.status, "J": r.J}
                if r.z is not None:
                    item["describe"] = describe(plant, r.z, scen, eJ, eEu, eEd, f"M1_rho{rho}")
                res.append(item)
                print("  rho", rho, r.status, r.J, item.get("describe", {}).get("n_violated_margins"), flush=True)
            save_state(stage, {"method": "M1", "grid": res, "seconds": round(time.time() - t0, 1)})
    finally:
        plant.close()
    print("stage", stage, "done", round(time.time() - t0, 1), "s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
