"""DEC-054 G3 / P3-A: audit of the post-event affine predictor against ANDES (<= 8 TDS, DESIGN buses only, predeclared plan).

Phases:  `plan`    write IEEE39_DEC054_p3a_plan.json exclusively (to be committed BEFORE any TDS)
         `run`     execute the eight planned TDS in order through the ledger (no retries, failures recorded and counted)
         `analyze` signed errors, criteria of the plan, eps calibration (DESIGN data only), CSV/JSON/MD outputs
Prediction for each run is computed BEFORE its TDS and stored in the run configuration."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

import dec054_common as COM
import dec054_opf as OPF
import dec054_store as ST

PLAN = COM.ART / "IEEE39_DEC054_p3a_plan.json"
AMP_P, AMP_Q = 0.58564, 0.17345
UN = COM.UNITS

CRITERIA = {
    "peak_positive_error_max_pu": 0.03,          # observed peak above the predicted peak P_pre + dP + E_up (optimistic prediction), per unit
    "trough_positive_error_max_pu": 0.03,        # observed trough below the predicted trough P_pre + dP - E_dn (optimistic prediction), per unit
    "first_sample_error_reported_only_pu": 0.05,  # error of the first stored sample vs the model at tau = DT: reported, not a criterion
    "binding_units": ["SG31", "SG35"],
    "max_failing_units": 3,
    "fidelity_peak_diff_max_pu": 0.01,
    "verdict_rule": "PREDICTOR_AUDIT_PASS if every unit meets both tolerances over the DESIGN P events (T1-T4, T7); PARTIAL if SG31 and SG35 pass and at most 3 units fail; "
                    "PREDICTOR_AUDIT_FAILED if SG31 or SG35 fails, more than 3 units fail, or a P event produced no observation.  Q/S/V outputs have no predictor (only P rows are modelled): verification metrics only.",
    "stop_rule": "PREDICTOR_AUDIT_FAILED stops the campaign (no P3-B/P3-C).",
}
METRICS = {
    "alignment": "events enter through the dist_fn callback at t=5.0 BEFORE the integrator step 4.99609375->5.0, so the stored sample at 5.0 is one trapezoid step after the event: observed sample t_k corresponds to model time tau_k = (t_k - 5.0) + 2^-8 s; P_pre = P(4.99609375 s)",
    "peak_pred": "P_pre + dP_jump + E_up_pred  (E_up = max(0, max_tau D(tau)), D(0)=0)",
    "trough_pred": "P_pre + dP_jump - E_dn_pred",
    "peak_obs/trough_obs": "max/min of the stored P over tau in [0, 195 s]",
    "errors": "e_peak = peak_obs - peak_pred (positive = optimistic); e_trough = trough_pred - trough_obs (positive = optimistic)",
    "first_sample": "P(5.0)-P_pre versus dP_jump + D(2^-8 s)",
    "limiters": "RDC exciter clamp (|z| >= 0.0999) from the stored command series; ANDES internal limiter states are not stored by the executor (UNOBSERVED)",
}


def scenarios(z_ref, zC):
    sc = [("P3A_01_b8P_zref", 8, "P", AMP_P, "z_ref", z_ref, None, "P step, DESIGN bus 8"),
          ("P3A_02_b23P_zref", 23, "P", AMP_P, "z_ref", z_ref, None, "P step, DESIGN bus 23"),
          ("P3A_03_b28P_zref", 28, "P", AMP_P, "z_ref", z_ref, None, "P step, DESIGN bus 28"),
          ("P3A_04_b25P_zref", 25, "P", AMP_P, "z_ref", z_ref, None, "P step, DESIGN bus 25"),
          ("P3A_05_b8Q_zref", 8, "Q", AMP_Q, "z_ref", z_ref, None, "Q step, DESIGN bus 8"),
          ("P3A_06_b23Q_zref", 23, "Q", AMP_Q, "z_ref", z_ref, None, "Q step, DESIGN bus 23"),
          ("P3A_07_b28P_zC", 28, "P", AMP_P, "z_SG31-0.10_SG38+0.10", zC, None, "P step on a redispatched point: audit of the I(z)-dependent predictor"),
          ("P3A_08_b8P_zref_dt_half", 8, "P", AMP_P, "z_ref", z_ref, 2.0 ** -9, "numerical fidelity: same as T1 with step 2^-9 s")]
    return sc


def build_plan():
    import dec054_plant as PL
    P = PL.AndesPlant()
    z0 = P.z_ref.copy()
    zC = z0.copy(); zC[1] -= 0.10; zC[4] += 0.10
    tests = []
    for rid, bus, kind, amp, dname, z, dt, purpose in scenarios(z0, zC):
        tests.append({"run_id": rid, "bus": bus, "kind": kind, "amp": amp, "dispatch": dname, "z": z.tolist(), "z_sha256": __import__("dec054_runner").z_digest(z), "time_step_s": dt, "purpose": purpose})
    assert all(t["bus"] in COM.DESIGN for t in tests)
    code = ["dec054_common.py", "dec054_plant.py", "dec054_predictor.py", "dec054_runner.py", "dec054_store.py", "dec054_metrics.py", "dec054_opf.py", "dec054_p3a_audit.py", "dec054_rdcinit.py"]
    plan = {"stage": "DEC-054 G3 P3-A predictor audit", "sealed": True, "budget_tds": 8, "block": "P3-A", "horizon": {"event_s": 5.0, "end_s": 200.0, "post_event_s": 195.0}, "partition_used": "DESIGN only " + str(COM.DESIGN),
            "tests": tests, "criteria": CRITERIA, "metrics": METRICS, "code_sha256": {f: COM.sha_file(Path(__file__).parent / f) for f in code}, "andes_version": "2.0.0",
            "gate0": COM.backup_gate()["status"], "note": "plan sealed before the first TDS; no retry of failed runs; DESIGN buses only (TUNE/TEST untouched)"}
    with open(PLAN, "x", encoding="utf-8") as f:
        json.dump(plan, f, indent=1)
    print("plan written", len(tests), "tests")


def run():
    import dec054_plant as PL
    import dec054_predictor as PRD
    import dec054_runner as RUN
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    assert plan["sealed"] and plan["budget_tds"] == 8 and len(plan["tests"]) == 8
    ledger = COM.TdsLedger(COM.ART / "IEEE39_DEC054_tds_ledger.csv")
    P = PL.AndesPlant()
    for t in plan["tests"]:
        rid = t["run_id"]
        z = np.asarray(t["z"], float)
        assert RUN.z_digest(z) == t["z_sha256"]
        sc = OPF.Scenario(rid, t["bus"], t["kind"], t["amp"])
        pred = {}
        err = None
        try:
            e = P.evaluate(z)
            j = P.jump(z, sc)
            A, f, C = P.affine(z, sc, diag=True)
            x = PRD.excursion(A, f, C)
            pred = {"P_pre": e["P"], "Q_pre": e["Q"], "V_pre": e["V"], "I": {k: v for k, v in e["I"].items() if k in ("k_ip", "gref_p", "gref_q")}, "dP_jump": j["dP"], "dQ_jump": j["dQ"],
                    "E_up": x["E_up"], "E_dn": x["E_dn"], "t_up": x["t_up"], "t_dn": x["t_dn"], "sampling_error_up": x["sampling_error_up"], "gy_min_sv": P.last_affine_diag["gy_min_sv_post_jump"]}
            traj = {"pred_t": x["t"], "pred_D": x["D"]}
        except Exception as ex:      # a prediction failure is recorded; the TDS is still run (the audit needs the observation)
            err, traj = ex, {}
        tid = ledger.request("P3-A", rid, "predictor_audit", rid, t["purpose"])
        cfg = {"run_id": rid, "tds_id": tid, "test": t, "prediction": pred, "plan_sha256": COM.sha_file(PLAN), "criteria": plan["criteria"]}
        res, tds_err = None, None
        try:
            res = RUN.execute_tds(z, {"bus": t["bus"], "kind": t["kind"], "amp": t["amp"]}, time_step_s=t["time_step_s"])
            status = res["status"]
        except Exception as ex:
            status, tds_err = "TDS_NUMERICAL_FAILURE", ex
        res = res or {}
        series = dict(res.get("series") or {}, **traj) if res.get("series") is not None else (traj or None)
        ST.save_run(COM.RUNS_DIR, rid, status=status, tds_id=tid, series=series, metrics=res.get("metrics"), config=cfg, diag=res.get("diag"), notes=str(res.get("notes", "")),
                    error=tds_err or err, ledger_row=next((r for r in ledger.rows if r["tds_id"] == tid and r["status"] == "REQUESTED"), {}))
        ledger.complete(tid, status, str(tds_err or err or res.get("notes", ""))[:400])
        print(rid, status, flush=True)


# ------------------------------------------------------------------ analysis
def compare_run(t, P, pred_dP, pred_t, pred_D, horizon: float = 195.0, dt: float = COM.DT, t_event: float = 5.0) -> dict:
    """Observed-vs-predicted comparison with the model-time alignment tau_k = (t_k - t_e) + dt."""
    t, P = np.asarray(t, float), np.asarray(P, float)
    i0 = int(np.argmin(np.abs(t - t_event)))
    assert abs(t[i0] - t_event) < 1e-6 and t[i0 - 1] < t_event
    Ppre = P[i0 - 1]
    tau = t[i0:] - t_event + dt
    m = tau <= horizon + 1e-9
    obs = P[i0:][m] - Ppre
    tau = tau[m]
    dP = np.asarray(pred_dP, float)
    predD = np.asarray(pred_D, float)
    peak_pred = dP + np.maximum(predD.max(axis=1), 0.0)
    trough_pred = dP - np.maximum((-predD).max(axis=1), 0.0)
    peak_obs, trough_obs = obs.max(axis=0), obs.min(axis=0)
    pr_at = np.array([dP[i] + np.interp(tau, pred_t, predD[i]) for i in range(P.shape[1])]).T
    return {"dP_pred": dP, "peak_pred": peak_pred, "trough_pred": trough_pred, "peak_obs": peak_obs, "trough_obs": trough_obs, "e_peak": peak_obs - peak_pred, "e_trough": trough_pred - trough_obs,
            "t_peak_obs": tau[np.argmax(obs, axis=0)], "t_trough_obs": tau[np.argmin(obs, axis=0)], "first_sample_obs": obs[0], "first_sample_pred": pr_at[0], "first_sample_error": obs[0] - pr_at[0],
            "traj_rmse": np.sqrt(np.mean((obs - pr_at) ** 2, axis=0)), "traj_max_abs": np.abs(obs - pr_at).max(axis=0), "Ppre": Ppre}


def analyze():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    crit = plan["criteria"]
    rows, per_run = [], {}
    for t in plan["tests"]:
        rid = t["run_id"]
        d = COM.RUNS_DIR / rid
        st = json.loads((d / "status.json").read_text(encoding="utf-8"))
        cfg = json.loads((d / "config.json").read_text(encoding="utf-8"))
        if st["status"] == "TDS_NUMERICAL_FAILURE" or not (d / "series.npz").exists():
            per_run[rid] = {"status": st["status"], "error": st.get("error")}
            continue
        z = np.load(d / "series.npz")
        pr = cfg["prediction"]
        if not pr or "pred_t" not in z.files:
            per_run[rid] = {"status": st["status"], "error": "no prediction"}
            continue
        cr = compare_run(z["t"], z["P"], pr["dP_jump"], z["pred_t"], z["pred_D"])
        per_run[rid] = {"status": st["status"], "cmp": cr, "diag": cfg.get("diag"), "V_min": float(z["V"].min()), "V_max": float(z["V"].max())}
        for i, u in enumerate(UN):
            rows.append({"run_id": rid, "bus": t["bus"], "kind": t["kind"], "dispatch": t["dispatch"], "time_step_s": t["time_step_s"] or 2.0 ** -8, "unit": u, "P_pre_pu": float(cr["Ppre"][i]),
                         "dP_jump_pred_pu": float(cr["dP_pred"][i]), "peak_pred_pu": float(cr["peak_pred"][i]), "peak_obs_pu": float(cr["peak_obs"][i]), "peak_error_signed_pu": float(cr["e_peak"][i]),
                         "trough_pred_pu": float(cr["trough_pred"][i]), "trough_obs_pu": float(cr["trough_obs"][i]), "trough_error_signed_pu": float(cr["e_trough"][i]),
                         "E_up_pred_pu": float(pr["E_up"][i]), "E_dn_pred_pu": float(pr["E_dn"][i]), "t_peak_obs_s": float(cr["t_peak_obs"][i]), "t_up_pred_s": float(pr["t_up"][i]),
                         "first_sample_obs_pu": float(cr["first_sample_obs"][i]), "first_sample_pred_pu": float(cr["first_sample_pred"][i]), "first_sample_error_pu": float(cr["first_sample_error"][i]),
                         "trajectory_rmse_pu": float(cr["traj_rmse"][i]), "trajectory_max_abs_pu": float(cr["traj_max_abs"][i]), "sampling_error_up_pred": float(pr["sampling_error_up"][i])})
    p_runs = [t["run_id"] for t in plan["tests"] if t["kind"] == "P" and t["time_step_s"] is None]
    unit_res = {}
    for u in UN:
        ep = [r["peak_error_signed_pu"] for r in rows if r["unit"] == u and r["run_id"] in p_runs]
        et = [r["trough_error_signed_pu"] for r in rows if r["unit"] == u and r["run_id"] in p_runs]
        unit_res[u] = {"n_events": len(ep), "max_peak_error": max(ep) if ep else None, "max_trough_error": max(et) if et else None,
                       "pass": bool(ep and max(ep) <= crit["peak_positive_error_max_pu"] and max(et) <= crit["trough_positive_error_max_pu"])}
    failing = [u for u, r in unit_res.items() if not r["pass"]]
    n_ok = sum(1 for rid in p_runs if "cmp" in per_run.get(rid, {}))
    if n_ok < len(p_runs):
        verdict, reason = "PREDICTOR_AUDIT_FAILED", f"only {n_ok}/{len(p_runs)} P events produced observations"
    elif any(u in failing for u in crit["binding_units"]) or len(failing) > crit["max_failing_units"]:
        verdict, reason = "PREDICTOR_AUDIT_FAILED", f"failing units {failing}"
    elif failing:
        verdict, reason = "PREDICTOR_AUDIT_PARTIAL", f"failing units {failing} (binding units pass)"
    else:
        verdict, reason = "PREDICTOR_AUDIT_PASS", "all units within the predeclared tolerances"
    fid = None
    a_, b_ = per_run.get("P3A_01_b8P_zref", {}), per_run.get("P3A_08_b8P_zref_dt_half", {})
    if "cmp" in a_ and "cmp" in b_:
        fid = {"max_abs_peak_obs_diff": float(np.abs(a_["cmp"]["peak_obs"] - b_["cmp"]["peak_obs"]).max()), "max_abs_trough_obs_diff": float(np.abs(a_["cmp"]["trough_obs"] - b_["cmp"]["trough_obs"]).max()),
               "tolerance": crit["fidelity_peak_diff_max_pu"]}
        fid["ok"] = bool(max(fid["max_abs_peak_obs_diff"], fid["max_abs_trough_obs_diff"]) <= crit["fidelity_peak_diff_max_pu"])

    def eps_for(runs):
        out = {}
        for u in UN:
            ep = [r["peak_error_signed_pu"] for r in rows if r["unit"] == u and r["run_id"] in runs]
            et = [r["trough_error_signed_pu"] for r in rows if r["unit"] == u and r["run_id"] in runs]
            fl, kp = COM.PROPOSED["eps_floor_pu"], COM.PROPOSED["kappa"]
            out[u] = {"eps_J": fl, "eps_E_up": max(fl, kp * max([0.0] + ep)), "eps_E_dn": max(fl, kp * max([0.0] + et)), "max_signed_peak_error": max(ep) if ep else None,
                      "max_signed_trough_error": max(et) if et else None, "n": len(ep)}
        return out
    q_runs = [t["run_id"] for t in plan["tests"] if t["kind"] == "Q"]
    eps = {"source": "P3-A DESIGN events only (buses 8,23,28,25). eps_E calibrated on the TOTAL peak/trough error (jump proxy included: the true algebraic jump is not observable), eps_J = floor. "
                     "Rule eps = max(floor, kappa*max positive error), kappa=1.5, floor=1e-3 (PROPOSED, EMPIRICAL_LOCATION_AWARE_MARGIN; no coverage claim)",
           "P_events": eps_for(p_runs), "Q_events": eps_for(q_runs), "n_P_events": len(p_runs), "n_Q_events": len(q_runs)}
    evid = {rid: {"status": v["status"], "V_min": v.get("V_min"), "V_max": v.get("V_max"), "final_residual": (v.get("diag") or {}).get("final_residual"), "error": v.get("error")} for rid, v in per_run.items()}
    out = {"stage": "DEC-054 P3-A analysis", "verdict": verdict, "reason": reason, "unit_results": unit_res, "fidelity": fid, "eps_calibration": eps, "runs": evid, "criteria": crit,
           "tds_used": sum(1 for r in COM.TdsLedger(COM.ART / "IEEE39_DEC054_tds_ledger.csv").rows if r["status"] == "REQUESTED" and r["block"] == "P3-A")}
    with open(COM.ART / "IEEE39_DEC054_p3a_analysis.json", "x", encoding="utf-8") as f:
        json.dump(out, f, indent=1, default=float)
    with open(COM.ART / "IEEE39_DEC054_dynamic_predictor_validation.csv", "x", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with open(COM.ART / "IEEE39_DEC054_algebraic_jump_validation.csv", "x", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["run_id", "bus", "kind", "dispatch", "unit", "dP_jump_pred_pu", "first_sample_obs_pu", "first_sample_pred_pu", "first_sample_error_pu"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in w.fieldnames})
    print("VERDICT", verdict, reason)
    return out


if __name__ == "__main__":
    {"plan": build_plan, "run": run, "analyze": analyze}[sys.argv[1]]()
