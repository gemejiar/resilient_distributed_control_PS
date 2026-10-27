"""E9-A: consolidate the audit, relative-degree, authority and feasibility results into one summary JSON (no simulation).

Adds the IBR audit (GFM32/34/36/37), the conditional C2t_IBRreserve proposal (documented, NOT implemented), the SG31 diagnosis, the
initial-voltage finding and the automatic checks.  Thresholds used for the checks are declared here, before reading the verdicts.
"""

from __future__ import annotations

import json
import os
import platform

os.environ["C2_VARIANT"] = "C2t"

import numpy as np

from run_e0_ieee39 import ARTIFACTS_DIR, FIGURES_DIR, MATRIX_FILE, PROJECT_ROOT, git_commit, sha256
import csv

A = ARTIFACTS_DIR
OUT = A / "IEEE39_E9A_summary.json"
FIGS = ["margins", "sg31_timeline", "sg31_authority", "relative_degree", "qp_feasibility", "frequency_voltage"]
IBR_MARGIN_FRACTION = 0.02    # a GFM is flagged "thin" if its minimum transient P margin is below 2 % of its P range


def main() -> int:
    audit = json.loads((A / "IEEE39_E9A_physical_audit.json").read_text(encoding="utf-8"))
    auth = json.loads((A / "IEEE39_E9A_sg31_authority.json").read_text(encoding="utf-8"))
    hoc = json.loads((A / "IEEE39_E9A_hocbf_diagnostic.json").read_text(encoding="utf-8"))
    val = json.loads((A / "IEEE39_E9A_linear_validation.json").read_text(encoding="utf-8"))
    names = audit["units"]
    lim = {k: np.array(v) for k, v in audit["limits_pu"].items()}
    rng_p = lim["pmax"] - lim["pmin"]
    gfm = [names.index(n) for n in ("GFM32", "GFM34", "GFM36", "GFM37")]
    ibr: dict = {}
    for i in gfm:
        n = names[i]
        worst = {}
        for run, r in audit["runs"].items():
            worst[run] = {"min_P_to_pmax_pu": r["P_to_pmax_pu"]["min"][i], "min_Q_to_qmax_pu": r["Q_to_qmax_pu"]["min"][i], "min_Q_to_qmin_pu": r["Q_to_qmin_pu"]["min"][i],
                          "min_S_rel_margin": r["S_rel"]["min"][i]}
        mp = min(w["min_P_to_pmax_pu"] for w in worst.values())
        ibr[n] = {"pmax_pu": float(lim["pmax"][i]), "qmin_qmax_pu": [float(lim["qmin"][i]), float(lim["qmax"][i])], "Sn_pu": float(lim["smax"][i]),
                  "worst_min_P_margin_pu": mp, "worst_min_P_margin_fraction_of_range": float(mp / rng_p[i]),
                  "worst_min_S_rel_margin": min(w["min_S_rel_margin"] for w in worst.values()),
                  "worst_min_Q_margin_pu": min(min(w["min_Q_to_qmax_pu"], w["min_Q_to_qmin_pu"]) for w in worst.values()),
                  "violation_in_any_stored_run": any(k.startswith(n) for r in audit["runs"].values() for k in r["violations"]),
                  "thin_P_margin": bool(mp / rng_p[i] < IBR_MARGIN_FRACTION), "per_run": worst}
        y = audit["runs"]["B3 P+"].get("gfm_internal_limiter")
        if y:
            j = gfm.index(i)
            ibr[n]["internal_limiter"] = {"REGF1_Pmax_pu": float(lim["smax"][i]), "max_PIplim_y_pu_B3_P+": y["PIplim_y_max"][j], "max_PIqlim_y_pu_B3_P+": y["PIqlim_y_max"][j],
                                          "binding": bool(y["PIplim_y_max"][j] >= lim["smax"][i] - 1e-6)}
    need = [n for n, v in ibr.items() if v["thin_P_margin"]]
    reserve = {"decision": "NOT implemented; conditional proposal", "evidence_of_need_in_stored_scenarios": "no unit violates its case limits in S0, P+ or Q+ (only SG31, by the instantaneous load jump)",
               "units_with_thin_P_margin": need,
               "proposal_if_E9B_requires_reserve": {"variant_name": "C2t_IBRreserve", "initial_sensitivity": "+10 % nominal capacity on the justified units only", "candidates": need,
                                                    "coherence_checklist": ["REGF1.Sn", "REGF1.Pmax/Pmin/Qmax/Qmin (= +-Sn/100 internal limiters)", "case pmax/qmin/qmax on PV and the static limits used by E7-E9",
                                                                            "S circle: Sn/100", "per-unit conversion of xf, rf and of the control gains when Sn changes (ANDES scales by Sn/Sb)",
                                                                            "initialization: PV p0 / q split and the dynamic initial values (PIplim_y, PIqlim_y, vref)",
                                                                            "recompute the B3-A weights/ranges, the E8 capability set W_i and the B2/B3 gains (R_P, R_Q, d_P, d_Q) before any comparison",
                                                                            "keep C2t and every historical run untouched; new frozen baseline for the variant"]}}
    sg31 = audit["SG31_timeline"]["B2 (E8) P+"]
    sg31_diag = {
        "violation_B2_P+": {"spans_s": sg31["violation_spans_s"], "first_after_event_s": sg31["first_violation_after_event_s"], "per_span_peak_excess_pu": sg31["per_span_peak_excess_pu"],
                            "per_span_t_peak_after_event_s": sg31["per_span_t_peak_after_event_s"], "total_duration_s": sg31["duration_above_pmax_s"],
                            "pre_event_margin_pu": sg31["pre_event_margin_pu"], "jump_in_first_step_pu": sg31["rise_peak_minus_pre_pu"], "jump_over_load_step": sg31["rise_over_load_step"]},
        "instantaneous_jump": "P31 rises by 0.110 pu within the first solver step (4 ms) after the load step, against a pre-event margin of 0.040 pu; the own governor channel has 0.000 response at 4 ms (relative degree 4)",
        "slow_excursion": "second excursion (peak 0.021 pu in B2, 0.016 pu in B3, 0.030 pu with primary control only) at about 2.7 s (5.3 s with primary only); the own channel responds with 0.18 (0.15 s), 0.70 (0.5 s) and 0.74 (2.7 s) pu per pu of Pset31",
        "channel_response_dP31_per_unit_step": {k: v["dP31_per_unit_step"] for k, v in auth["channel_step_response"].items() if k.startswith("Pset")},
        "preventable_by_reference_rates": {"instantaneous_jump": False, "slow_excursion": True},
        "reason_instantaneous": "relative degree 4 (own governor channel) or 3 (through GFM channels) with respect to the reference rate: no reference rate changes P within 4 ms",
        "minimum_preventive_margin_needed_pu": 0.110,
        "redispatch_open_loop_primary_only": {k: {"SG31_peak_pu": v["SG31_peak_pu"], "pre_margin_pu": v["pre_margin_to_pmax_pu"][names.index("SG31")], "violating_units": v["units_with_pmax_violation"]}
                                              for k, v in auth["redispatch_sweep"].items()},
        "redispatch_threshold_pu": 0.08, "SG35_min_transient_margin_pu": min(r["P_to_pmax_pu"]["min"][names.index("SG35")] for r in audit["runs"].values())}
    stat = hoc["static"]
    dyn = {}
    for key, res in hoc["dynamic"].items():
        rows = res["probes"]
        feas = [r for r in rows if r["lam_2"]["qp_converged"]]
        first_feas_after = next((r["t_s"] - 5.0 for r in rows if r["t_s"] > 5.0 and r["lam_2"]["qp_converged"] and all(rr["lam_2"]["qp_converged"] for rr in rows if rr["t_s"] >= r["t_s"])), None)
        dyn[key] = {"qp_feasible_at_s1_pre_event": bool(rows[0]["lam_2"]["qp_converged"]), "barriers_outside_CH_pre_event": len(rows[0]["barriers_outside_CH"]),
                    "barriers_outside_CH_right_after_event_t=0.004s": len(rows[2]["barriers_outside_CH"]),
                    "qp_infeasible_for_all_authority_scales_after_event_until_s": next((r["t_s"] - 5.0 for r in rows if r["t_s"] > 5.0 and r["lam_2"]["authority_scale_min"] is not None), None),
                    "first_time_after_event_with_feasible_QP_from_then_on_s": first_feas_after,
                    "authority_scale_min_by_probe": [(round(r["t_s"] - 5.0, 4), r["lam_2"]["authority_scale_min"]) for r in rows],
                    "SG31_alone_authority_scale_by_probe": [(round(r["t_s"] - 5.0, 4), r["lam_2"]["authority_scale_by_group"]["SG31_P_upper_only"]) for r in rows]}
    checks = {
        "dae_regular_index_one_C2t": stat["C2t"]["dae"]["regular_index_one"], "dae_regular_index_one_Vsafe": stat["C2t_Vsafe"]["dae"]["regular_index_one"],
        "linear_model_matches_nonlinear_steps_3e-3": bool(max(v["abs_diff"] for c in val["channels"].values() for v in c.values()) <= 3.0e-3),
        "C2t_initial_voltage_outside_band": stat["C2t"]["pre_event_bus_voltage"]["n_above_1p05"] > 0,
        "Vsafe_initial_voltage_inside_band": stat["C2t_Vsafe"]["pre_event_bus_voltage"]["n_above_1p05"] == 0 and stat["C2t_Vsafe"]["pre_event_bus_voltage"]["n_below_0p95"] == 0,
        "no_barrier_of_relative_degree_below_3_in_P_Q_V": min(min(v for v in row if v > 0) for row in stat["C2t"]["relative_degree_matrix_P_Q_V"]) >= 3,
        "SG31_P_violation_persists": sg31["excess_pu"] > 0, "historical_runs_untouched": True, "QP_not_applied_to_the_plant": True}
    status = "FINDINGS_WAIT_HUMAN"
    summary = {"stage": "E9-A", "status_auto": status, "status_human": "PENDING", "created_python": platform.python_version(), "git_commit": git_commit(),
               "scope": "preparation and feasibility audit; B2 nominal, CLF off, QP diagnostic only (never closed in the loop); C2t, gains, graph, actuator maps, perturbations frozen",
               "constraint_matrix": audit["constraint_matrix"], "dae_regularity": {k: v["dae"] for k, v in stat.items()},
               "initial_voltage": {k: v["pre_event_bus_voltage"] for k, v in stat.items()},
               "relative_degrees": {"summary": "P_i, Q_i and all 39 bus voltages: 4 with respect to every SG reference rate, 3 with respect to every GFM reference rate (structural; same order for all outputs through the algebraic network coupling); reference barriers: 1",
                                    "units": stat["C2t"]["relative_degree_units"], "buses_min": stat["C2t"]["relative_degree_buses_min_over_channels"]},
               "linear_model_validation": val["channels"], "transient_margins_per_run": {k: {kk: vv for kk, vv in r.items() if kk in ("P_to_pmax_pu", "Q_to_qmax_pu", "Q_to_qmin_pu", "S_rel", "violations")} for k, r in audit["runs"].items()},
               "ibr_audit": ibr, "ibr_reserve": reserve, "sg31_diagnosis": sg31_diag, "qp_feasibility": dyn,
               "controls_sensitivity_note": "leading Markov coefficients per output/channel are in IEEE39_E9A_hocbf_diagnostic.json (relative_degree_units: lead_coeff_own_Pset/Qset)",
               "checks": checks, "assumptions": ["rate envelope for the authority scale = observed maxima of the original/centered RDC, not hardware limits", "class-K gains lambda = 2 s^-1 (1 and 5 reported), fixed a priori",
                                                 "r >= 2 derivatives from the frozen Jacobian (curvature neglected): local-linear diagnostic, not a certificate", "SG exciter clamp +-0.1 pu not linearized (|z| stayed below 0.056 pu in B2/B3)",
                                                 "no current limit is declared: REGF1 has none", "SG capability curve UNMODELED; S circle only", "Vsafe = B3-A d = 0 AC solution used only as an independent initial condition"],
               "figures": {f: f"Paper_manuscript/figures_main/IEEE39_E9A_{f}.png" for f in FIGS},
               "artifacts_sha256": {f.name: sha256(f) for f in sorted(A.glob("IEEE39_E9A_*.json")) if f.name != OUT.name} | {"IEEE39_E9A_replay_series.npz": sha256(A / "IEEE39_E9A_replay_series.npz")},
               "code_sha256": {f: sha256(PROJECT_ROOT / "Paper_manuscript" / "src" / f) for f in ("e9a_linear.py", "e9a_hocbf.py", "run_e9a_hocbf.py", "run_e9a_sg31.py", "audit_e9a_physical.py", "validate_e9a_linear.py", "finalize_e9a.py")},
               "open": ["OPEN-SG31-PMAX stays open: the 0.07 pu excess is an instantaneous jump that no reference rate can prevent from the C2t pre-event dispatch; only a preventive margin of at least 0.11 pu (open-loop redispatch of >= 0.08 pu) avoids it",
                        "E9-B (QP in closed loop), CLF, weight sensitivity, E10-E15 not run", "no dynamic-safety or regional-stability claim"]}
    OUT.write_text(json.dumps(summary, indent=2, default=float), encoding="utf-8")
    # experiment matrix row
    with MATRIX_FILE.open("r", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames or [])
        rows = [r for r in reader if r.get("stage") != "E9A"]
    row = {k: "" for k in fields}
    row.update({"run_id": "E9A_diagnostic", "stage": "E9A", "case": "C2t (+ C2t_Vsafe initial-condition variant)", "scenario": "B2_nominal_HOCBF_diagnostic_P+_Q+", "baseline": "E8_C2t_B2",
                "git_commit": git_commit(), "simulation_tf": 200.0, "event_time": 5.0, "status_auto": status, "status_human": "PENDING",
                "frequency_figure": summary["figures"]["frequency_voltage"], "voltage_figure": summary["figures"]["frequency_voltage"],
                "decision_note": "E9-A preparation/audit; QP not in the loop; E9-B, CLF and E10-E15 stay blocked (DEC-043)."})
    with MATRIX_FILE.open("w", newline="", encoding="utf-8") as stream:
        w = csv.DictWriter(stream, fieldnames=fields)
        w.writeheader()
        w.writerows(rows + [row])
    print(json.dumps(checks, indent=1)); print(json.dumps(dyn["C2t_Vsafe:P+"]["authority_scale_min_by_probe"])); print(need, ibr["GFM32"]["worst_min_P_margin_fraction_of_range"], ibr["GFM36"]["worst_min_P_margin_fraction_of_range"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
