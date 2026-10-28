"""DEC-054 G4 / P3-B: dynamic verification of the designed M3 dispatch on DESIGN/TUNE events only (<= 16 TDS in total for P3-B).
Round 1 = M3 dispatch at the eight DESIGN+TUNE events (8 TDS).  Stages: plan1 | run1 | analyze1.  The plan is written exclusively and committed BEFORE any TDS.
Round 2 (dynamic cuts, only if round 1 shows violations) is a separate script stage decided from the round-1 evidence."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

import dec054_common as COM
import dec054_opf as OPF
import dec054_p3a_audit as P3A
import dec054_store as ST

PLAN = COM.ART / "IEEE39_DEC054_p3b_round1_plan.json"
PLAN2 = COM.ART / "IEEE39_DEC054_p3b_round2_plan.json"
ROUND2_BUSES = [7, 8, 23, 20]      # round-1 events with the smallest observed P margin (7, 8) and the post-event voltage overshoot (23, 20)
STATE = COM.RUNS_DIR.parent / "DEC054_g4_state"
AMP = 0.58564
BUSES = COM.DESIGN + COM.TUNE
CRITERIA = {"verification_success": "no unit exceeds Pmax/Pmin (stored samples), no S/Q limit exceeded, all 39 voltages inside [0.95,1.05] in all 8 runs",
            "dynamic_cut_rule": "for every (unit, event) whose observed P exceeds a limit or whose observed margin is smaller than the predicted margin by more than eps: cut delta = observed excess + tau_cut (local, trust region), "
                                "eps updated with kappa*max positive error over P3-A + P3-B DESIGN/TUNE data",
            "budget": "round 1 uses 8 TDS; round 2 (re-verification of violating events only) uses the remaining P3-B budget (<= 8)"}


def build_plan():
    import dec054_runner as RUN
    m3 = json.loads((STATE / "m3.json").read_text(encoding="utf-8"))
    assert m3["status"] in ("FEASIBLE_PREDICTED", "LOCAL_OPTIMUM_FOUND") and "describe" in m3, m3["status"]
    z = np.array(m3["describe"]["z"])
    tests = [{"run_id": f"P3B1_b{b}P_M3", "bus": b, "kind": "P", "amp": AMP, "dispatch": "M3_round1", "z": z.tolist(), "z_sha256": RUN.z_digest(z), "time_step_s": None,
              "purpose": f"dynamic verification of the M3 dispatch, {'DESIGN' if b in COM.DESIGN else 'TUNE'} bus {b}"} for b in BUSES]
    plan = {"stage": "DEC-054 P3-B round 1", "sealed": True, "block": "P3-B", "budget_tds_round1": 8, "partition_used": {"DESIGN": COM.DESIGN, "TUNE": COM.TUNE}, "tests": tests, "criteria": CRITERIA,
            "m3_status": m3["status"], "m3_J": m3["J"], "gate0": COM.backup_gate()["status"]}
    with open(PLAN, "x", encoding="utf-8") as f:
        json.dump(plan, f, indent=1)
    print("plan written", len(tests))


def run(plan_path=None):
    import dec054_plant as PL
    import dec054_predictor as PRD
    import dec054_runner as RUN
    plan_path = plan_path or PLAN
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    ledger = COM.TdsLedger(COM.ART / "IEEE39_DEC054_tds_ledger.csv")
    P = PL.AndesPlant()
    for t in plan["tests"]:
        rid, z = t["run_id"], np.asarray(t["z"], float)
        assert RUN.z_digest(z) == t["z_sha256"]
        sc = OPF.Scenario(rid, t["bus"], t["kind"], t["amp"])
        pred, traj, err = {}, {}, None
        try:
            e = P.evaluate(z)
            j = P.jump(z, sc)
            A, f, C = P.affine(z, sc, diag=True)
            x = PRD.excursion(A, f, C)
            pred = {"P_pre": e["P"], "Q_pre": e["Q"], "V_pre": e["V"], "dP_jump": j["dP"], "dQ_jump": j["dQ"], "E_up": x["E_up"], "E_dn": x["E_dn"], "t_up": x["t_up"], "t_dn": x["t_dn"],
                    "sampling_error_up": x["sampling_error_up"], "gy_min_sv": P.last_affine_diag["gy_min_sv_post_jump"]}
            traj = {"pred_t": x["t"], "pred_D": x["D"]}
        except Exception as ex:
            err = ex
        tid = ledger.request("P3-B", rid, "M3_verification", rid, t["purpose"])
        cfg = {"run_id": rid, "tds_id": tid, "test": t, "prediction": pred, "plan_sha256": COM.sha_file(plan_path)}
        res, tds_err = None, None
        try:
            res = RUN.execute_tds(z, {"bus": t["bus"], "kind": t["kind"], "amp": t["amp"]})
            status = res["status"]
        except Exception as ex:
            status, tds_err = "TDS_NUMERICAL_FAILURE", ex
        res = res or {}
        series = dict(res.get("series") or {}, **traj) if res.get("series") is not None else (traj or None)
        ST.save_run(COM.RUNS_DIR, rid, status=status, tds_id=tid, series=series, metrics=res.get("metrics"), config=cfg, diag=res.get("diag"), notes=str(res.get("notes", "")), error=tds_err or err,
                    ledger_row=next((r for r in ledger.rows if r["tds_id"] == tid and r["status"] == "REQUESTED"), {}))
        ledger.complete(tid, status, str(tds_err or err or res.get("notes", ""))[:400])
        print(rid, status, flush=True)


def analyze1(plan_path=None, tag="round1"):
    plan = json.loads((plan_path or PLAN).read_text(encoding="utf-8"))
    lim = None
    rows, summ = [], {}
    p3a = json.loads((COM.ART / "IEEE39_DEC054_p3a_analysis.json").read_text(encoding="utf-8"))
    for t in plan["tests"]:
        rid = t["run_id"]
        d = COM.RUNS_DIR / rid
        st = json.loads((d / "status.json").read_text(encoding="utf-8"))
        cfg = json.loads((d / "config.json").read_text(encoding="utf-8"))
        if not (d / "series.npz").exists():
            summ[rid] = {"status": st["status"], "error": st.get("error")}
            continue
        z = np.load(d / "series.npz")
        pr = cfg["prediction"]
        cr = P3A.compare_run(z["t"], z["P"], pr["dP_jump"], z["pred_t"], z["pred_D"])
        Pabs = z["P"]
        post = z["t"] >= 5.0 - 1e-9
        met = json.loads((d / "metrics.json").read_text(encoding="utf-8"))
        # physical limits from the stored metrics structure
        un = met["unit"]
        summ[rid] = {"status": st["status"], "n_violating_pairs_P": met["n_violating_pairs_P"], "V_outside_buses_post": met.get("V_outside_buses_post"), "V_min_post": met.get("V_min_post"), "V_max_post": met.get("V_max_post"),
                     "min_margin_Pmax": [float(x) for x in un["Pmax"]["min_margin"]], "min_margin_Pmin": [float(x) for x in un["Pmin"]["min_margin"]],
                     "violating_Qmax": [bool(x) for x in un["Qmax"]["violates"]], "violating_Smax": [bool(x) for x in un["Smax"]["violates"]]}
        for i, u in enumerate(COM.UNITS):
            rows.append({"run_id": rid, "bus": t["bus"], "unit": u, "P_pre_pu": float(cr["Ppre"][i]), "peak_pred_pu": float(cr["peak_pred"][i]), "peak_obs_pu": float(cr["peak_obs"][i]), "peak_error_signed_pu": float(cr["e_peak"][i]),
                         "trough_pred_pu": float(cr["trough_pred"][i]), "trough_obs_pu": float(cr["trough_obs"][i]), "trough_error_signed_pu": float(cr["e_trough"][i]),
                         "min_margin_Pmax_obs_pu": summ[rid]["min_margin_Pmax"][i], "min_margin_Pmin_obs_pu": summ[rid]["min_margin_Pmin"][i]})
    viol = [r for r in rows if r["min_margin_Pmax_obs_pu"] < 0 or r["min_margin_Pmin_obs_pu"] < 0]
    kap, fl = COM.PROPOSED["kappa"], COM.PROPOSED["eps_floor_pu"]
    eps_new = {}
    for u in COM.UNITS:
        ep = [r["peak_error_signed_pu"] for r in rows if r["unit"] == u]
        et = [r["trough_error_signed_pu"] for r in rows if r["unit"] == u]
        a = p3a["eps_calibration"]["P_events"][u]
        eps_new[u] = {"eps_E_up": max(a["eps_E_up"], fl, kap * max([0.0] + ep)), "eps_E_dn": max(a["eps_E_dn"], fl, kap * max([0.0] + et)), "max_peak_err_P3B": max(ep) if ep else None, "max_trough_err_P3B": max(et) if et else None}
    ok = all(s.get("n_violating_pairs_P", 1) == 0 and s.get("V_outside_buses_post", 1) == 0 and not any(s.get("violating_Qmax", [True])) and not any(s.get("violating_Smax", [True])) for s in summ.values())
    out = {"stage": "DEC-054 P3-B round 1 analysis", "verification_success": bool(ok), "n_runs": len(summ), "runs": summ, "violating_unit_events": [{k: r[k] for k in ("run_id", "bus", "unit", "min_margin_Pmax_obs_pu", "min_margin_Pmin_obs_pu")} for r in viol],
           "eps_updated_candidates": eps_new, "tds_used_P3B": sum(1 for r in COM.TdsLedger(COM.ART / "IEEE39_DEC054_tds_ledger.csv").rows if r["status"] == "REQUESTED" and r["block"] == "P3-B")}
    with open(COM.ART / f"IEEE39_DEC054_p3b_{tag}_analysis.json", "x", encoding="utf-8") as f:
        json.dump(out, f, indent=1, default=float)
    with open(COM.ART / f"IEEE39_DEC054_p3b_{tag}_validation.csv", "x", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("verification_success", ok, "violating unit-events", len(viol))


def build_plan2():
    """Round 2: re-verification of the REDESIGNED M3 (voltage design margin) at four DESIGN/TUNE events chosen from the round-1 evidence (declared here, before any round-2 TDS)."""
    import dec054_runner as RUN
    m3 = json.loads((STATE / "m3.json").read_text(encoding="utf-8"))
    assert m3["status"] in ("FEASIBLE_PREDICTED", "LOCAL_OPTIMUM_FOUND") and "describe" in m3
    z = np.array(m3["describe"]["z"])
    tests = [{"run_id": f"P3B2_b{b}P_M3", "bus": b, "kind": "P", "amp": AMP, "dispatch": "M3_round2", "z": z.tolist(), "z_sha256": RUN.z_digest(z), "time_step_s": None,
              "purpose": f"re-verification of the redesigned M3 (v_margin 0.005 pu), bus {b}"} for b in ROUND2_BUSES]
    plan = {"stage": "DEC-054 P3-B round 2", "sealed": True, "block": "P3-B", "budget_tds_round2": len(tests), "partition_used": {"DESIGN": COM.DESIGN, "TUNE": COM.TUNE}, "tests": tests,
            "criteria": CRITERIA, "reason": "round 1 had no P/Q/S violations but post-event voltage overshoot above 1.05 pu (design voltages at the band edge); redesign with a 0.005 pu design margin on all 39 pre-event voltages (identical for M0-M3)",
            "m3_status": m3["status"], "m3_J": m3["J"], "gate0": COM.backup_gate()["status"]}
    with open(PLAN2, "x", encoding="utf-8") as f:
        json.dump(plan, f, indent=1)
    print("plan2 written", len(tests))


if __name__ == "__main__":
    st = sys.argv[1]
    {"plan1": build_plan, "run1": run, "analyze1": analyze1, "plan2": build_plan2, "run2": lambda: run(PLAN2), "analyze2": lambda: analyze1(PLAN2, "round2")}[st]()
