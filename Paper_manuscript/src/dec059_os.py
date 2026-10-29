"""DEC-059 R4 (decision DD): sub-cycle overshoot term of the preventive design M3 (theory: IEEE39_DEC059_theory.md section 6; protocol R4).
Physical model: the same affine post-jump predictor of M3 (dec054_predictor: d xi' = A d xi + f, d xi(t_e+) = 0, P = P+ + C d xi) evaluated in DENSE time on
[0, T_OS] with the exact matrix exponential at step DT/64.  The original M3 grid integrates the first second with the implicit trapezoid at DT = 3.9 ms, so a
peak of the fast (subtransient/network) response inside one step is not represented (DEC-057 refutation: SG31 peak at 2.2 ms).
  calib            per DESIGN/TUNE cell with a locally refined (dt/16) TDS: TDS peak vs dense prediction per unit (upper and lower), overshoot beyond the jump,
                   its scenario dependence (ratio to the jump), the model error and the declared bound eps_OS = max(underprediction) over the calibration set;
                   writes IEEE39_DEC059_OS_calibration.json (exclusive).  Calibration set: DESIGN cells and DEC-054 cohort (TUNE-labelled) only; no TEST data.
  design <OC>      M3 Algorithm 1 (dec054_opf, unchanged) with the excursion E = max(E_grid, E_dense[0, T_OS]) and eps_E + eps_OS + eps_D8 (eps_D8 = U_D8, so that a
                   predicted feasible design aims at the SAFE class of rule M3V-1), seeded at the DEC-055 M3 dispatch; state DEC059_state/m3os_<OC>.json (exclusive)."""
from __future__ import annotations

import json
import os
import sys
import time
import types

import numpy as np

import dec054_common as C54
import dec055_common as C55
import dec055_oc as OCM
import dec054_predictor as PRD

T_OS = 0.05
H_OS = C54.DT / 64
U_D8 = 0.0109
STATE = C54.RUNS_DIR.parent / "DEC059_state"
DENSE = [[0.0, T_OS, H_OS, "exact"]]


def os_excursion(self, z, sc, stale=None):
    try:
        A, f, Cm = self.affine(z, sc, stale=stale)
    except Exception as ex:                                  # same contract as AndesPlant.excursion
        return {"ok": False, "reason": repr(ex)}
    x = PRD.excursion(A, f, Cm)
    _, D, _ = PRD.propagate(A, f, Cm, DENSE)
    ok = bool(x["ok"] and np.all(np.isfinite(D)) and np.abs(D).max() <= 50.0)
    eu, ed = np.maximum(D.max(axis=1), 0.0), np.maximum((-D).max(axis=1), 0.0)
    E_up, E_dn = (np.maximum(x["E_up"], eu), np.maximum(x["E_dn"], ed)) if ok else (np.zeros(10), np.zeros(10))
    return {"ok": ok, "E_up": E_up, "E_dn": E_dn, "t_up": x["t_up"], "sampling_error": x["sampling_error_up"], "horizon_s": C54.T_POST,
            "E_dense_up": eu, "E_dense_dn": ed, "E_grid_up": x["E_up"], "E_grid_dn": x["E_dn"]}


def make_os_plant(oc):
    p = OCM.make_plant(oc)
    p.excursion = types.MethodType(os_excursion, p)
    return p


def _init_worker_os(oc):
    import dec054_pool as POOL
    os.environ.update({v: "1" for v in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS")})
    POOL._W = make_os_plant(oc)


# ------------------------------------------------------------------------------------------------------------------------------------- calibration
def calib_cells():
    import dec057_tds as T7
    import dec059_tds as T9
    z3 = json.loads((C54.RUNS_DIR.parent / "DEC056_state" / "oc3_seeded_full.json").read_text(encoding="utf-8"))["z"]
    import dec055_l0 as L0
    cells = [("OC3", z3, {"bus": s.bus, "kind": s.kind, "amp": s.amp}, T7.RUNS / f"D57M3V_B2_{s.name}", "DESIGN (OC3 M3, DEC-057 M3V)", None) for s in L0.design_scenarios()]
    for tag in ("b7", "b8", "bus12"):
        d = T7.RUNS / f"D57D8_{tag}_trapezoid_loc16"
        c = json.loads((d / "config.json").read_text(encoding="utf-8"))
        cells.append(("OC1", c["z"], c["scenario"], d, "TUNE-labelled DEC-054 cohort (OC1, DEC-054 M3)", 1e-6))
    for run in ("D59S2_B5P_OC1_M0_b8P_S2", "D59S3_B5P_OC2_M0_b8P_S2", "D59S4_B5P_OC3_M0_b8P_S2"):
        d = T9.RUNS / run
        c = json.loads((d / "config.json").read_text(encoding="utf-8"))
        cells.append((c["oc"], c["z"], c["scenario"], d, "DESIGN (b8P_S2, M0, B5' smoke)", None))
    return cells


def calib_part(oc_only, dest):
    """Rows of the calibration cells of one OC (one process per OC: dec055_oc.select patches module globals and an OC switch inside a process is not clean)."""
    import dec054_opf as OPF
    t0 = time.time()
    rows = []
    plants = {}
    pf0 = OCM.PFLOW_TOL
    for oc, z, sc, d, label, pftol in [c for c in calib_cells() if c[0] == oc_only]:
        OCM.PFLOW_TOL = pf0 if pftol is None else pftol          # DEC-054 cohort runs were initialised with the PFlow tolerance 1e-6
        if oc not in plants:
            plants[oc] = OCM.make_plant(oc)
        plant = plants[oc]
        z = np.asarray(z, float)
        S = OPF.Scenario("c", int(sc["bus"]), sc["kind"], float(sc["amp"]))
        jp = plant.jump(z, S)
        A, f, Cm = plant.affine(z, S)
        _, D, _ = PRD.propagate(A, f, Cm, DENSE)
        tg, Dg, _ = PRD.propagate(A, f, Cm, [[0.0, T_OS, C54.DT, "trap"]])
        s = np.load(d / "series.npz", allow_pickle=True)
        t = s["t"]
        k = (t >= C54.EVENT_T - 1e-12) & (t <= C54.EVENT_T + T_OS + 1e-12)
        Pt = s["P"][k]
        Pp = jp["P_plus"]
        lim = plant.limits
        rec = {"oc": oc, "scenario": sc, "source": d.name, "label": label, "dispatch_pflow_tol": pftol}
        for side, sgn in (("up", 1.0), ("dn", -1.0)):
            tds_peak = (sgn * Pt).max(axis=0)
            pred_peak = sgn * Pp + np.maximum((sgn * D).max(axis=1), 0.0)
            grid_peak = sgn * Pp + np.maximum((sgn * Dg).max(axis=1), 0.0)
            rec[side] = {"tds_peak": (sgn * tds_peak).tolist(), "pred_dense_peak": (sgn * pred_peak).tolist(), "pred_dtgrid_peak": (sgn * grid_peak).tolist(),
                         "underprediction": (tds_peak - pred_peak).tolist(), "overshoot_beyond_jump_dense": np.maximum((sgn * D).max(axis=1), 0.0).tolist(),
                         "jump": (Pp - s["P"][t < C54.EVENT_T - 1e-12][-1]).tolist()}
        mp_t = lim["pmax"] - Pt.max(axis=0)
        mp_d = lim["pmax"] - (Pp + np.maximum(D.max(axis=1), 0.0))
        mp_g = lim["pmax"] - (Pp + np.maximum(Dg.max(axis=1), 0.0))
        rec["pmax_margin"] = {"tds_min": float(mp_t.min()), "tds_unit": C55.UNITS[int(mp_t.argmin())], "dense_min": float(mp_d.min()), "dense_unit": C55.UNITS[int(mp_d.argmin())],
                              "dtgrid_min": float(mp_g.min()), "jump_only_min": float((lim["pmax"] - Pp).min())}
        rows.append(rec)
        print(d.name, rec["pmax_margin"], "max underpred up", round(max(rec["up"]["underprediction"]), 6), flush=True)
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(rows, f, default=float)


def stage_calib(write=False):
    import subprocess
    t0 = time.time()
    scratch = os.environ.get("DEC059_SCRATCH", r"C:/Users/gemej/dec059_scratch")
    rows = []
    for oc in ("OC3", "OC1", "OC2"):
        dest = os.path.join(scratch, f"os_calib_part_{oc}.json")
        subprocess.run([sys.executable, "-W", "ignore", __file__, "calib_part", oc, dest], check=True, cwd=str(C55.SRC))
        rows += json.loads(open(dest, encoding="utf-8").read())
    U = np.array([r["up"]["underprediction"] for r in rows])
    Dn = np.array([r["dn"]["underprediction"] for r in rows])
    os_up = np.array([r["up"]["overshoot_beyond_jump_dense"] for r in rows])
    jumps = np.abs(np.array([r["up"]["jump"] for r in rows]))
    ratio = np.where(jumps > 1e-3, os_up / np.maximum(jumps, 1e-12), np.nan)
    summ = {"n_cells": len(rows), "eps_OS_up": float(max(U.max(), 0.0)), "eps_OS_dn": float(max(Dn.max(), 0.0)),
            "underprediction_up_quantiles": np.quantile(U, [0.5, 0.9, 0.99, 1.0]).tolist(), "overprediction_up_max": float(-U.min()),
            "pmax_margin_error_dense_minus_tds": [r["pmax_margin"]["dense_min"] - r["pmax_margin"]["tds_min"] for r in rows],
            "pmax_margin_error_dtgrid_minus_tds": [r["pmax_margin"]["dtgrid_min"] - r["pmax_margin"]["tds_min"] for r in rows],
            "overshoot_to_jump_ratio_by_unit": {"median": np.nanmedian(ratio, axis=0).tolist(), "min": np.nanmin(ratio, axis=0).tolist(), "max": np.nanmax(ratio, axis=0).tolist()},
            "overshoot_up_max_by_unit": os_up.max(axis=0).tolist(), "units": C55.UNITS, "seconds": round(time.time() - t0, 1),
            "note": "the TDS peaks carry the D8 numerical uncertainty (U_D8 = 0.0109 pu); eps_OS is an empirical bound on 18 DESIGN/TUNE cells, not a guarantee"}
    out = {"stage": "DEC-059 R4 overshoot-term calibration (DESIGN/TUNE only)", "T_OS": T_OS, "H_OS": H_OS, "cells": rows, "summary": summ}
    if write:
        with open(C55.ART / "IEEE39_DEC059_OS_calibration.json", "x", encoding="utf-8") as f:
            json.dump(out, f, indent=1, default=float)
    print(json.dumps(summ, indent=1, default=float))
    return out


# ------------------------------------------------------------------------------------------------------------------------------------- design
def stage_design(oc, workers="3", cut=None):
    import dec054_g4_design as G4
    import dec054_opf as OPF
    import dec055_l0 as L0
    t0 = time.time()
    cal = json.loads((C55.ART / "IEEE39_DEC059_OS_calibration.json").read_text(encoding="utf-8"))["summary"]
    m3 = json.loads((C55.STATE / f"m3_{oc}.json").read_text(encoding="utf-8"))
    scen = L0.design_scenarios()
    seed_z = m3["z"]
    if cut == "cut":      # the single dynamic cut cycle of the protocol (Addendum B item 4): eligible UNSAFE TUNE cells of this OC are added, same formulation / cfg / eps, seed = current M3+OS
        tr = json.loads((C55.ART / "IEEE39_DEC059_TUNE_results.json").read_text(encoding="utf-8"))[oc]
        for c in tr["cells"]:
            if c["eligible_for_G3"] and c["tds"]["class"] == "UNSAFE":
                scen.append(OPF.Scenario(c["cell"], int(c["cell"].split("P_")[0][1:]), "P", float(c["pred"].get("amp", 0) or C55.oc_amp(c["cell"].split("_")[1]))))
        seed_z = json.loads((STATE / f"m3os_{oc}.json").read_text(encoding="utf-8"))["z"]
    OCM._init_worker = _init_worker_os                      # pool workers (also after a rebuild) use the OS-augmented excursion
    plant = OCM.OCPooledPlant(oc, int(workers))
    eJ, eEu, eEd = G4.eps_vectors()
    eEu2 = eEu + cal["eps_OS_up"] + U_D8
    eEd2 = eEd + cal["eps_OS_dn"] + U_D8
    cfg = dict(C54.PROPOSED, K_max=8, N_it=int(os.environ.get("DEC059_NIT", "25")), ftol=1e-6, verbose=False)
    try:
        r = OPF.algorithm1(plant, "M3", scen, eJ, eEu2, cfg=cfg, z_seeds=[np.array(seed_z)], k0=4, eps_E_dn=eEd2,
                           log=lambda x: print(oc, "  iter", {k: x[k] for k in ("k", "W", "min_margin", "J")}, flush=True))
        out = {"oc": oc, "method": "M3+OS" + ("+cut" if cut else ""), "cut_scenarios": [x.name for x in scen[12:]], "status": r.status, "J": r.J, "kkt": r.kkt_residual, "iterations": r.iterations, "detail": r.detail, "cuts": r.cuts, "log": r.log,
               "z": None if r.z is None else r.z.tolist(), "seed": "DEC-055 M3 of the OC", "J_M3_DEC055": m3["J"],
               "eps": {"J": eJ.tolist(), "E_up": eEu2.tolist(), "E_dn": eEd2.tolist(), "eps_OS_up": cal["eps_OS_up"], "eps_OS_dn": cal["eps_OS_dn"], "eps_D8": U_D8},
               "T_OS": T_OS, "H_OS": H_OS, "event_tasks": plant.n_event_tasks, "plant_evaluations": plant.n_eval, "seconds": round(time.time() - t0, 1)}
        if r.z is not None:
            e = plant.evaluate(r.z)
            out.update({"init_ok": bool(e["ok"]), "redispatch_MW_abs_sum_vs_case": float(np.abs(r.z[:9] - plant.z_ref[:9]).sum() * 100),
                        "redispatch_MW_abs_sum_vs_M3_DEC055": float(np.abs(r.z[:9] - np.array(m3["z"])[:9]).sum() * 100)})
        STATE.mkdir(parents=True, exist_ok=True)
        with open(STATE / (f"m3os_cut_{oc}.json" if cut else f"m3os_{oc}.json"), "x", encoding="utf-8") as f:
            json.dump(out, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else float(o))
        print(oc, "M3+OS", r.status, r.J, round(time.time() - t0, 1), "s", flush=True)
    finally:
        plant.close()


if __name__ == "__main__":
    if sys.argv[1] == "calib_part":
        calib_part(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "calib":
        stage_calib("write" in sys.argv)
    elif sys.argv[1] == "design":
        stage_design(*sys.argv[2:])
