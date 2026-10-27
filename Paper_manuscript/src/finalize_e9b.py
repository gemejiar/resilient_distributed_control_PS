"""E9-B0/B1: consolidate the frozen-variant validation and the feasibility audit into tables and one summary JSON (no simulation)."""

from __future__ import annotations

import csv
import json
import os
import platform

os.environ["C2_VARIANT"] = "C2t"

from run_e0_ieee39 import ARTIFACTS_DIR as A, MATRIX_FILE, PROJECT_ROOT, git_commit, sha256

SRC = PROJECT_ROOT / "Paper_manuscript" / "src"
TAG = "_R35"
EVENT = 5.0


def main() -> int:
    b0p = json.loads((A / "IEEE39_E9B0_variant.json").read_text(encoding="utf-8"))
    b0 = json.loads((A / f"IEEE39_E9B0_variant{TAG}.json").read_text(encoding="utf-8"))
    red = json.loads((A / "IEEE39_E9B0_redispatch_search.json").read_text(encoding="utf-8"))
    b1 = json.loads((A / f"IEEE39_E9B1_feasibility{TAG}.json").read_text(encoding="utf-8"))
    ic = b0["initial_condition"]
    units = ic["units"]
    cols = sorted({k for u in units for k in u}, key=lambda k: (k != "unit", k != "bus", k))
    with (A / f"IEEE39_E9B0_initial_condition{TAG}_units.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(units)
    with (A / f"IEEE39_E9B0_initial_condition{TAG}_buses.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["bus", "V_pu", "angle_rad", "in_band"])
        w.writeheader()
        w.writerows(ic["bus_voltages_39"])
    names = [u["unit"] for u in units]
    hist_p = json.loads((A / "IEEE39_B3A_C2t_equilibrium_v2.json").read_text(encoding="utf-8"))["pre_event_reference"]["P"]
    dispatch = {n: {"C2t_historical_P_pu": hist_p[i], "C2t_Vsafe_P_pu": b0p["initial_condition"]["units"][i]["P_pu"], "C2t_Vsafe_R35_P_pu": units[i]["P_pu"]} for i, n in enumerate(names)}
    keys = ("max_P_pu", "min_P_pu", "max_Q_pu", "min_Q_pu", "max_S_pu", "min_P_margin_to_pmax_pu", "min_Q_margin_to_qmax_pu", "min_Q_margin_to_qmin_pu", "min_S_rel_margin")
    scen = {}
    for sc, m in b0["scenarios"].items():
        scen[sc] = {"violating_units": m["violating_units"], "frequency": m["frequency"], "bus_voltage": m["bus_voltage"], "final_residual": m["diagnostics"]["final_residual"],
                    "continuity_physical_states": m["continuity"]["excluding_degenerate_IEEEST_states"],
                    "per_unit": {n: {k: r[k] for k in keys} for n, r in m["per_unit"].items()}}
    scen_plain = {sc: {"violating_units": m["violating_units"], "SG35_P_violation_pu": m["per_unit"]["SG35"]["P_violation_pu"],
                       "SG31_min_P_margin_pu": m["per_unit"]["SG31"]["min_P_margin_to_pmax_pu"]} for sc, m in b0p["scenarios"].items()}
    ch = {}
    for sc, res in b1["scenarios"].items():
        rows = res["probes"]
        pre = [r for r in rows if r["t_s"] < EVENT + 0.00005][-1]
        post = [r for r in rows if r["t_s"] > EVENT + 0.002]
        first = post[0]
        win = [r for r in post if 0.4 <= r["t_s"] - EVENT <= 5.0 and "derivative_check" in r]
        cross = [r["prediction_error"]["0.25"]["max_abs_err_P"] for r in rows if r["prediction_error"]["0.25"]["window_crosses_load_step"]]
        ch[sc] = {"verdict": res["verdict"],
                  "pre_event": {"t_s": pre["t_s"] - EVENT, "barriers_outside_CH": pre["C_H"]["n_outside"], "h_negative": pre["C_H"]["h_negative"], "qp_feasible": pre["audit"]["qp"]["SLSQP"]["converged"],
                                "min_h_by_kind": pre["C_H"]["min_h_by_kind"], "relative_degree_by_kind": pre["C_H"]["relative_degree_by_kind"]},
                  "first_post_jump": {"t_s": first["t_s"] - EVENT, "barriers_outside_CH": first["C_H"]["n_outside"], "outside_by_kind": first["C_H"]["outside_by_kind"],
                                      "h_negative": first["C_H"]["h_negative"], "worst_psi": first["C_H"]["worst_psi_min"], "qp_feasible": first["audit"]["qp"]["SLSQP"]["converged"],
                                      "elastic_violation": first["audit"]["elastic_violation_at_s1"], "conflict_set": first["audit"]["conflict_set_top"],
                                      "classification": first["audit"]["conflict_classification"]},
                  "time_series": [{"t_after_event_s": r["t_s"] - EVENT, "n_outside_CH": r["C_H"]["n_outside"], "outside_by_kind": r["C_H"]["outside_by_kind"],
                                   "authority_scale_min": r["audit"]["authority_scale_min"], "qp_feasible_slsqp": r["audit"]["qp"]["SLSQP"]["converged"],
                                   "qp_feasible_trust_constr": r["audit"]["qp"]["trust-constr"]["converged"], "elastic_violation": r["audit"]["elastic_violation_at_s1"],
                                   "conflict_set_top": r["audit"]["conflict_set_top"][:3], "classification": [(c["name"], c["classification"]) for c in r["audit"]["conflict_classification"]],
                                   "lambda_1_authority": r.get("lam_1_authority_scale"), "lambda_5_authority": r.get("lam_5_authority_scale"), "SG35_P+": r["SG35_P+"], "SG31_P+": r["SG31_P+"],
                                   "solvers_agree": r["audit"]["qp_solvers_agree"] and r["audit"]["independent_check"]["agree"], "qp_time_s": r["audit"]["qp"]["SLSQP"]["time_s"]} for r in rows],
                  "model_error": {"relative_degree_unchanged_all_probes": all(r["relative_degree_same_as_first_probe"] for r in rows),
                                  "leading_coeff_ratio_range": [min(r["leading_coeff_ratio_vs_first_probe"]["min"] for r in rows), max(r["leading_coeff_ratio_vs_first_probe"]["max"] for r in rows)],
                                  "max_pred_error_tau0.25_after_jump_0.004_to_5s": {k: max(r["prediction_error"]["0.25"][f"max_abs_err_{k}"] for r in post if 0.004 <= r["t_s"] - EVENT <= 5.0) for k in ("P", "Q", "V")},
                                  "pred_error_P_pu_when_window_crosses_the_load_step": max(cross) if cross else None,
                                  "derivative_check_transient_window_0.4_5s_median_rel_err": {f"order_{k}": [float(r["derivative_check"][f"order_{k}"]["median_rel_err"]) for r in win] for k in (1, 2, 3)},
                                  "power_balance_note": "independent nodal balance: valid pre-event and in Q+ (5.6e-6 pu); in P+ after the event it equals the load step (0.5856 pu) because the PQ parameter used for the sum does not carry the Alter step (bookkeeping artefact, not a DAE residual)",
                                  "max_algebraic_residual_all_probes": max(r["residual_g"] for r in rows)},
                  "continuity": res["continuity"]["excluding_degenerate_IEEEST_states"]}
    status = "FINDINGS_WAIT_HUMAN"
    figs = {k: f"Paper_manuscript/figures_main/IEEE39_{k}.png" for k in ("E9B0_margins_R35", "E9B1_CH_membership_R35", "E9B1_qp_feasibility_R35", "E9B1_model_error_R35")}
    summary = {
        "stage": "E9-B0/E9-B1", "status_auto": status, "status_human": "PENDING", "git_commit": git_commit(), "python": platform.python_version(),
        "variant": {"name": b0["variant"], "definition": "C2t_Vsafe (B3-A d = 0 AC solution as initial condition) plus an incremental preventive redispatch of SG35 to the GFM",
                    "plain_Vsafe_result": scen_plain,
                    "redispatch": {"source": "SG35", "delta_min_pu": red["delta_min_pu"], "delta_frozen_pu": red["delta_frozen_pu"], "rule": red["rule"], "receiver_shares_of_delta": red["receivers_GFM"],
                                   "SG35_transient_margin_in_P+_at_frozen_delta_pu": red["check_at_frozen"]["min_P_margin_pu"]["SG35"]},
                    "dispatch_P_pu": dispatch, "initial_condition_tables": ["IEEE39_E9B0_initial_condition_R35_units.csv", "IEEE39_E9B0_initial_condition_R35_buses.csv"],
                    "AC_DAE_initialization": {k: ic[k] for k in ("pflow_residual", "init_max_abs_f", "init_max_abs_g", "power_balance", "bus_voltage_min_pu", "bus_voltage_max_pu", "n_buses_outside_band")},
                    "flat_run_20s": b0["flat_run"], "scenarios_B2_no_QP": scen, "frozen": True},
        "C_H_and_QP": ch,
        "assumptions": ["rate envelope (P+: 0.616 pu/s on P, 0.0154 on Q; Q+: 0.195, 0.0154) is an experimental candidate bound from E8/B3, not hardware",
                        "lambda = 2 s^-1 a priori; 1 and 5 for sensitivity only",
                        "derivatives of order >= 2 from the frozen Jacobian; reference derivatives from polynomial fits of the nonlinear series",
                        "failure classification rule declared in e9b_tools.py before reading the verdicts",
                        "the 0.005 pu rounding of the redispatch is my rule, declared before running; the investigator may replace it"],
        "figures": figs, "raw_sha256": {f: sha256(A / f) for f in ("IEEE39_E9B0_Vsafe_series.npz", "IEEE39_E9B0_Vsafe_R35_series.npz")},
        "artifacts_sha256": {f.name: sha256(f) for f in sorted(A.glob("IEEE39_E9B*")) if f.suffix in (".json", ".csv") and f.name != "IEEE39_E9B_summary.json"},
        "code_sha256": {f: sha256(SRC / f) for f in ("e9b_variant.py", "e9b_tools.py", "run_e9b0_variant.py", "run_e9b0_redispatch.py", "run_e9b1_feasibility.py", "finalize_e9b.py", "e9a_linear.py", "e9a_hocbf.py")},
        "open": ["OPEN-SG31-PMAX stays open for the original C2t; the reserve variant is a separate configuration",
                 "E9-B2 (closed loop) not run; weight sensitivity, E10-E15 not run; no change of Sn or SG31 Pmax",
                 "post-jump states of P+ and Q+ are outside C_H and the QP is infeasible until about 2 s (P+) and 1 s (Q+): closed-loop protection NOT authorized for those scenarios",
                 "no certificate: frozen-Jacobian derivatives, assumed rate envelope, sampled controller not validated"]}
    (A / "IEEE39_E9B_summary.json").write_text(json.dumps(summary, indent=2, default=float), encoding="utf-8")
    with MATRIX_FILE.open("r", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames or [])
        rows = [r for r in reader if r.get("stage") not in ("E9B0", "E9B1")]
    new = []
    for stage, note, scen_txt in (("E9B0", "E9-B0 variant C2t_Vsafe_R35 validated and frozen; B2 without QP; no limit violated (DEC-044).", "Vsafe_R35_B2_S0_P+_Q+"),
                                  ("E9B1", "E9-B1 C_H and QP feasibility outside the loop; P+/Q+ post-jump outside C_H, closed loop not authorized; E9-B2 blocked (DEC-044).", "Vsafe_R35_HOCBF_diagnostic_S0_P+_Q+")):
        row = {k: "" for k in fields}
        row.update({"run_id": f"{stage}_Vsafe_R35", "stage": stage, "case": "C2t_Vsafe_R35 (initial-condition variant of C2t)", "scenario": scen_txt, "baseline": "E8_C2t_B2", "git_commit": git_commit(),
                    "simulation_tf": 200.0, "event_time": 5.0, "status_auto": status, "status_human": "PENDING", "frequency_figure": figs["E9B0_margins_R35"],
                    "voltage_figure": figs["E9B1_CH_membership_R35"], "raw_file": "Paper_manuscript/artifacts/IEEE39_E9B0_Vsafe_R35_series.npz", "decision_note": note})
        new.append(row)
    with MATRIX_FILE.open("w", newline="", encoding="utf-8") as stream:
        w = csv.DictWriter(stream, fieldnames=fields)
        w.writeheader()
        w.writerows(rows + new)
    print({sc: c["verdict"]["closed_loop_protection_authorized_for_scenario"] for sc, c in ch.items()}, red["delta_min_pu"], red["delta_frozen_pu"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
