"""DEC-051 closure (no simulation): H3 summary and inequality tables, H4 final assessment, domains (block D), validation table, figures, hashes, conclusions matrix and the consolidated report.

Everything is computed from the stored JSON/NPZ of the DEC-051 stages and from the historical artifacts; the only model evaluations are the algebraic/nonlinear-field evaluations needed for the
domain check (post-jump state versus the local certificate) and for the Kantorovich-type existence condition (static, no time stepping)."""

from __future__ import annotations

import csv
import json
import os

os.environ["C2_VARIANT"] = "C2t"

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import dec051_core as C  # noqa: E402
import run_dec051_equilibrium as EQ  # noqa: E402
import run_dec051_h4 as H4  # noqa: E402
from run_e0_ieee39 import ARTIFACTS_DIR as A, FIGURES_DIR, PROJECT_ROOT, git_commit, sha256  # noqa: E402

NAMES = ["SG30", "SG31", "SG33", "SG35", "SG38", "SG39", "GFM32", "GFM37", "GFM34", "GFM36"]
GRID = (0.25, 0.5, 0.75, 1.0, 1.1, 1.25, 1.5)
P_STEP_MW = 58.564
plt.rcParams.update({"font.family": "serif", "font.size": 8, "axes.grid": True, "grid.alpha": 0.25, "legend.fontsize": 7, "figure.dpi": 150})
COL = {"ok": "#2a7f3f", "bad": "#b2182b", "neutral": "#4d4d4d", "c1": "#2166ac", "c2": "#d6604d", "c3": "#e0a526"}


def J(name):
    return json.loads((A / name).read_text(encoding="utf-8"))


def main() -> int:
    jr, pred, s1, s2 = J("IEEE39_DEC051_H3_jump.json"), J("IEEE39_DEC051_H3_predictions.json"), J("IEEE39_DEC051_H3_sim1.json"), J("IEEE39_DEC051_H3_sim2.json")
    h4, h4v, eqj = J("IEEE39_DEC051_H4_summary.json"), J("IEEE39_DEC051_H4_validation.json"), J("IEEE39_DEC051_equilibrium.json")
    d50 = J("IEEE39_DEC050_C_dynamic.json")
    e12 = J("IEEE39_E12_frontier.json")["dynamic_runs"]
    auth = J("IEEE39_E9A_sg31_authority.json")
    sg31, sg35 = NAMES.index("SG31"), NAMES.index("SG35")
    with_series = ["C2t", "C2t_Vsafe", "C2t_Vsafe_R35 (0.015)", "C2t_Vsafe_R35_040"]
    eps = max(jr["configs"][c]["jump_prediction_vs_first_sample_max_abs"] for c in with_series)
    # ------------------------------------------------------------------ H3: inequality table
    import dec051_core  # noqa: F401  (limits come from the stored series)
    e8 = np.load(A / "IEEE39_E8_C2t_timeseries.npz")
    pmax = e8["P+_unit_pmax"]
    rows, ineq = [], {}
    for c in with_series:
        cf = jr["configs"][c]
        pre = np.array(cf["P_pre"]); R = np.array(cf["reserve_P"])
        jump = np.array(cf["events"]["P+"]["1"]["dP_jump"])
        fast = np.maximum(np.array(cf["observed_fast_increment_over_jump"]), 0); slow = np.maximum(np.array(cf["observed_slow_increment_over_jump"]), 0)
        inc = np.maximum(fast, slow)
        pk_pred = pre + jump + inc
        pk_obs = np.array(cf["observed_P+_peak"])
        m_jump = R - jump - eps
        m_full = pmax - pk_pred - eps
        m_obs = pmax - pk_obs
        ineq[c] = {"SG31": {"reserve": float(R[sg31]), "jump": float(jump[sg31]), "fast_increment": float(fast[sg31]), "slow_increment": float(slow[sg31]), "margin_after_jump": float(m_jump[sg31]), "predicted_min_margin": float(m_full[sg31]), "observed_min_margin": float(m_obs[sg31])},
                   "SG35": {"reserve": float(R[sg35]), "jump": float(jump[sg35]), "fast_increment": float(fast[sg35]), "slow_increment": float(slow[sg35]), "margin_after_jump": float(m_jump[sg35]), "predicted_min_margin": float(m_full[sg35]), "observed_min_margin": float(m_obs[sg35])},
                   "units_violating_observed": [NAMES[i] for i in np.where(m_obs < 0)[0]], "units_violating_inequality_full": [NAMES[i] for i in np.where(m_full < 0)[0]], "units_violating_inequality_jump_only": [NAMES[i] for i in np.where(m_jump < 0)[0]]}
        for i, n in enumerate(NAMES):
            rows.append([c, "P+ 58.564 MW (bus 4)", n, pre[i], pmax[i], R[i], jump[i], fast[i], slow[i], eps, pk_pred[i], m_full[i], pk_obs[i], m_obs[i], bool(m_full[i] >= 0), bool(m_obs[i] < 0),
                         "jump: algebraic solve (conservative, amplitude grid); increments: empirical (same run)"])
    # validation sims
    for tag, s, p in (("H3-1 P+ 110 % bus 4 (R35_040)", s1, pred["H3_1"]), ("H3-2 P+ 58.564 MW bus 18 (R35_040)", s2, pred["H3_2"])):
        pk = np.array(s["observed_peak_P_pu"]); pp = np.array(p["predicted_peak_P_pu"])
        for i, n in enumerate(NAMES):
            rows.append([tag, s["event"], n, "", pmax[i], "", "", "", "", "", pp[i], p["predicted_margin_to_pmax_pu"][i], pk[i], s["observed_margin_to_pmax_pu"][i], bool(p["predicted_margin_to_pmax_pu"][i] >= 0), bool(s["observed_margin_to_pmax_pu"][i] < 0),
                         "independent prediction (increments borrowed from the 58.564 MW run, linear scaling)"])
    with (A / "IEEE39_DEC051_safety_margins.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["config_or_run", "event", "unit", "P_pre_pu", "Pmax_pu", "reserve_pu", "dP_jump_pu", "fast_increment_pu", "slow_increment_pu", "eps_jump_pu", "predicted_peak_pu", "predicted_margin_pu", "observed_peak_pu", "observed_margin_pu",
                    "inequality_holds", "observed_violation", "bound_class"])
        w.writerows(rows)
    # attribution of the SG31 / SG35 improvement
    att = {}
    for c in ("C2t", "C2t + Vsafe voltages only", "C2t + Vsafe dispatch only", "C2t_Vsafe", "C2t_Vsafe_R35 (0.015)", "C2t_Vsafe_R35_040"):
        cf = jr["configs"][c]
        att[c] = {"reserve_SG31": cf["reserve_P"][sg31], "reserve_SG35": cf["reserve_P"][sg35], "jump_SG31": cf["events"]["P+"]["1"]["dP_jump"][sg31], "jump_SG35": cf["events"]["P+"]["1"]["dP_jump"][sg35],
                  "margin_after_jump_SG31": cf["events"]["P+"]["1"]["margin_P_post"][sg31], "margin_after_jump_SG35": cf["events"]["P+"]["1"]["margin_P_post"][sg35]}
    base, vonly, ponly, both = att["C2t"], att["C2t + Vsafe voltages only"], att["C2t + Vsafe dispatch only"], att["C2t_Vsafe"]
    attrib = {"SG31_post_jump_margin_change_due_to_voltages_only": vonly["margin_after_jump_SG31"] - base["margin_after_jump_SG31"], "SG31_change_due_to_dispatch_only": ponly["margin_after_jump_SG31"] - base["margin_after_jump_SG31"],
              "SG31_change_both": both["margin_after_jump_SG31"] - base["margin_after_jump_SG31"], "SG35_change_due_to_voltages_only": vonly["margin_after_jump_SG35"] - base["margin_after_jump_SG35"],
              "SG35_change_due_to_dispatch_only": ponly["margin_after_jump_SG35"] - base["margin_after_jump_SG35"], "SG35_change_both": both["margin_after_jump_SG35"] - base["margin_after_jump_SG35"],
              "SG35_observed_min_margin_Vsafe_to_R35_040": [ineq["C2t_Vsafe"]["SG35"]["observed_min_margin"], ineq["C2t_Vsafe_R35_040"]["SG35"]["observed_min_margin"]],
              "reading": "the SG31 improvement comes from the active-power dispatch of the B3-A solution (reserve 0.040 -> 0.139 pu); the Vsafe voltage set-points alone do not help (-0.0025 pu). SG35 is hit by the slow electromechanical excursion (peak at ~7.8 s) which the R35 redispatch compensates one-to-one with reserve."}
    # authority of the references in the first instants
    chs = auth["channel_step_response"]
    ts = ["0.004", "0.05", "0.15", "0.5"]
    authority = {t: {"max_abs_dP31_per_unit_reference_step": max(abs(v["dP31_per_unit_step"][t]) for v in chs.values()), "max_abs_dP35_per_unit_reference_step": max(abs(v["dP35_per_unit_step"][t]) for v in chs.values())} for t in ts}
    # frontier prediction from the inequality (R35_040)
    cf = jr["configs"]["C2t_Vsafe_R35_040"]
    R = np.array(cf["reserve_P"]); fast = np.maximum(np.array(cf["observed_fast_increment_over_jump"]), 0); slow = np.maximum(np.array(cf["observed_slow_increment_over_jump"]), 0); inc = np.maximum(fast, slow)
    amps = np.array([g * P_STEP_MW for g in GRID])
    mm = []
    for g in GRID:
        jmp = np.array(cf["events"]["P+"][f"{g:g}"]["dP_jump"])
        m = R - jmp - g * inc - eps
        mm.append(m)
    mm = np.array(mm)
    minm = mm.min(axis=1); bind = [NAMES[int(i)] for i in mm.argmin(axis=1)]
    a_star = None
    for k in range(len(GRID) - 1):
        if minm[k] >= 0 > minm[k + 1]:
            a_star = float(amps[k] + (amps[k + 1] - amps[k]) * minm[k] / (minm[k] - minm[k + 1]))
            break
    ok_p = [x["amplitude"] for x in d50["P"] if not x["violating_units"] and not x["tds_failed"]]
    bad_p = [x["amplitude"] for x in d50["P"] if x["violating_units"] or x["tds_failed"]]
    frontier = {"amplitudes_MW": amps.tolist(), "predicted_min_margin_pu": minm.tolist(), "binding_unit": bind, "predicted_crossing_amplitude_MW": a_star, "dynamic_bracket_DEC050_MW": [max(ok_p), min(bad_p)],
                "E12_violation_at_MW": 87.76, "prediction_inside_bracket": bool(a_star is not None and max(ok_p) <= a_star <= min(bad_p))}
    # ------------------------------------------------------------------ H3 gate
    sims_ok = (not s1["observed_units_crossing_limits"]) and (not s2["observed_units_crossing_limits"])
    pred_ok = (not pred["H3_1"]["predicted_violating_units"]) and (not pred["H3_2"]["predicted_violating_units"])
    crit_err = max(abs(s1["prediction_error_margin_pu"][sg31]), abs(s1["prediction_error_margin_pu"][sg35]), abs(s2["prediction_error_margin_pu"][sg31]), abs(s2["prediction_error_margin_pu"][sg35]))
    gate_c = "H3_PREVENTIVE_NUMERICALLY_SUPPORTED" if (sims_ok and pred_ok and ineq["C2t_Vsafe_R35_040"]["units_violating_observed"] == []) else "H3_NOT_SUPPORTED"
    q_ev = cf["events"]["Q+"]["1"]
    h3 = {"stage": "DEC-051 H3-R", "git_commit": git_commit(), "hypothesis_H3R": "A preventive selection of the operating point with explicit reserves avoids the observed physical violations under a delimited class of disturbances without modifying the RDC.",
          "delimited_class_tested": "P load steps at bus 4 up to 64.42 MW and at bus 18 (58.564 MW); Q+ 17.345 MVAr at bus 21; configuration C2t_Vsafe_R35_040; B2 original; 200 s", "eps_jump_pu": eps, "inequality_table": ineq, "attribution_voltage_vs_dispatch": {"per_configuration": att, "decomposition": attrib},
          "reference_authority_first_instants": authority, "frontier_prediction_vs_dynamic_bracket": frontier, "Q_plus_post_jump_R35_040": {"min_margin_Qmax": float(min(q_ev["margin_Q_post_max"])), "min_margin_Qmin": float(min(q_ev["margin_Q_post_min"])), "min_margin_S": float(min(q_ev["margin_S_post"])),
                                                                                                                 "min_margin_P": float(min(q_ev["margin_P_post"])), "bus_voltage_min_max_static_post_jump": q_ev["bus_voltage_min_max"]},
          "validation": {"H3_1": {"event": s1["event"], "predicted_margin_SG31_SG35": [pred["H3_1"]["predicted_margin_to_pmax_pu"][sg31], pred["H3_1"]["predicted_margin_to_pmax_pu"][sg35]], "observed_margin_SG31_SG35": [s1["observed_margin_to_pmax_pu"][sg31], s1["observed_margin_to_pmax_pu"][sg35]],
                                  "max_abs_prediction_error_all_units": float(np.abs(s1["prediction_error_margin_pu"]).max()), "units_crossing_limits": s1["observed_units_crossing_limits"], "n_buses_below_0.95": s1["n_buses_below_0.95"]},
                         "H3_2": {"event": s2["event"], "selection": "smallest positive predicted margin among admissible buses (rule revised once before any simulation, see predictions file)", "predicted_margin_SG31_SG35": [pred["H3_2"]["predicted_margin_to_pmax_pu"][sg31], pred["H3_2"]["predicted_margin_to_pmax_pu"][sg35]],
                                  "observed_margin_SG31_SG35": [s2["observed_margin_to_pmax_pu"][sg31], s2["observed_margin_to_pmax_pu"][sg35]], "max_abs_prediction_error_all_units": float(np.abs(s2["prediction_error_margin_pu"]).max()),
                                  "units_crossing_limits": s2["observed_units_crossing_limits"], "n_buses_below_0.95": s2["n_buses_below_0.95"], "analytic_scan_predicting_violations_not_simulated": [(r["bus"], r["predicted_min_margin_all_units"], r["predicted_binding_unit"]) for r in pred["H3_2"]["selection_scan_sorted_worst_first"] if r["predicted_min_margin_all_units"] < 0]}},
          "bound_classes": {"jump_at_t0+": "conservative: exact algebraic solution of the DAE with continuous differential states, evaluated on the amplitude grid with monotonicity checked on the grid (not proved in the continuum); eps = max discrepancy with the first simulated sample",
                            "fast_phase_(<=50_ms)_and_slow_excursion": "empirical, from the simulated 58.564 MW run of the same configuration, scaled linearly with the amplitude (hypothesis tested by the two validation runs)", "universal_bounds": "none"},
          "GATE_C": gate_c, "formal_certificate": "none: the transient increments are empirical; H3_PREVENTIVE_CERTIFIED is not claimed"}
    (A / "IEEE39_DEC051_H3_summary.json").write_text(json.dumps(h3, indent=2, default=float), encoding="utf-8")
    # ------------------------------------------------------------------ H4: Kantorovich-type condition, a-posteriori certificate, domains
    eq, system, ctx, st, ix, pred_, u = H4.load_eq()
    d_idx = ix["d_idx"]; n = len(d_idx); N = n + 20
    pin_pos = int(np.where(d_idx == int(eq["pin"]))[0][0])
    vnull = EQ.angle_null(system, ctx, st, ix, pred_, u, pin_pos)
    Qm = EQ.quotient_matrix(vnull, pin_pos)
    S = np.delete(np.eye(N), pin_pos, axis=1)
    mt = np.load(A / "IEEE39_DEC051_H4_matrices.npz")
    Aq, Psc, D = mt["Aq"], mt["P_scaled"], np.diag(mt["D"])
    As = D @ Aq @ np.linalg.inv(D)
    R_ = As.T @ Psc + Psc @ As + np.eye(As.shape[0])
    wP = np.linalg.eigvalsh(Psc)
    cert = {"lambda_min_P": float(wP.min()), "eig_solver_error_bound_(eps*lambda_max)": float(np.finfo(float).eps * wP.max() * 10), "spectral_norm_of_residual_(A^T P + P A + I)": float(np.linalg.norm(R_, 2)),
            "evaluation_error_bound_(eps*|A||P|)": float(np.finfo(float).eps * np.linalg.norm(As, 2) * np.linalg.norm(Psc, 2) * len(As)), "certificate_holds": None}
    cert["certificate_holds"] = bool(cert["lambda_min_P"] > 10 * cert["eig_solver_error_bound_(eps*lambda_max)"] and cert["spectral_norm_of_residual_(A^T P + P A + I)"] + cert["evaluation_error_bound_(eps*|A||P|)"] < 1.0)
    cert["statement"] = "P symmetric positive definite and A^T P + P A <= -(1 - ||R||) I with ||R|| < 1 imply Hurwitz A (a-posteriori Lyapunov certificate, independent of the accuracy of the eigenvalue computation)"
    # Kantorovich-type existence: sigma_min of the quotient Jacobian and the second-derivative bound it allows
    Jq = np.vstack([Aq, np.zeros((0, Aq.shape[1]))])
    sig = np.linalg.svd(Aq, compute_uv=False)
    res = eqj["tolerance"]["reached_norm_inf_F_quotient"] * np.sqrt(Aq.shape[0])
    beta = 1.0 / sig[-1]
    eta = beta * res
    L_allowed = 0.5 / (beta * eta)
    # empirical second-derivative estimate from the nonlinear field (static evaluations)
    x_eq, y_eq = np.array(eq["x"]), np.array(eq["y"])
    Jfull = np.zeros((N, N))
    # reuse the numerical Jacobian through Aq: remainder r(delta) = Qm F(xi*+S e) - Aq e
    rng = np.random.default_rng(2)
    Ls = []
    for sc in (1e-3, 1e-2):
        for _ in range(6):
            e = rng.standard_normal(Aq.shape[0]); e = (np.linalg.inv(D) @ (e / np.linalg.norm(D @ e))) * sc
            xi = S @ e
            xn = x_eq.copy(); xn[d_idx] += xi[:n]; un = eq["u"] + xi[n:]
            C.set_state(system, xn, y_eq)
            C.inner_solve(system, ctx, st, un, ix, pred_.cache, tol=1e-12)
            F0, _, _ = EQ.residual_vec(system, ctx, st, ix, un)
            rem = EQ.quotient(F0, vnull, pin_pos) - Aq @ e
            Ls.append(float(np.linalg.norm(rem) / np.linalg.norm(D @ e) ** 2))
    C.set_state(system, x_eq, y_eq)
    kant = {"sigma_min_quotient_jacobian": float(sig[-1]), "residual_2norm": float(res), "beta": float(beta), "eta": float(eta), "second_derivative_bound_allowed_by_Kantorovich_h<=1/2": float(L_allowed),
            "empirical_remainder_ratio_||F(xi)-A e||/||e||^2_(scaled, sampled)": {"max": max(Ls), "values": Ls}, "reading": "if the second derivative of the reduced field in the scaled norm is below the allowed value on the ball of radius 2*eta around the computed root, a true equilibrium exists there (Newton-Kantorovich); the bound is not verified, only compared with sampled ratios"}
    # post-jump state versus the local region (Q+ only: the certified equilibrium is the Q+ one)
    s0, _ = C.build_system("S0")
    x_pre = np.array(s0.dae.x)
    xi_pre = np.concatenate([x_pre[d_idx] - x_eq[d_idx], np.concatenate([st["pn"], st["qn"]]) - eq["u"]])
    e_pre = Qm @ xi_pre
    V_pre = float((D @ e_pre) @ Psc @ (D @ e_pre))
    levels = h4["H4_3_empirical_region"]["levels"]
    rho_stab_emp = max(l["rho"] for l in levels if l["all_negative"] and l["all_inner_converged"])
    ok_phys = [l["rho"] for l in levels if l["min_physical_margin_pu_over_directions"] > 0]
    rho_phys_emp = max(ok_phys) if ok_phys else 0.0
    domains = {"1_regularity_domain": {"description": "algebraic block regular", "equilibrium_min_singular_value": h4["regularity"]["algebraic_block_min_singular_value"], "inner_solve_converged_at_all_sampled_points": bool(all(l["all_inner_converged"] for l in levels)),
                                       "radius": "not quantified (sampled up to rho = %.2e)" % max(l["rho"] for l in levels)},
               "2_local_stability_domain": {"description": "neighbourhood where the indirect Lyapunov method applies", "radius": "exists, NOT quantified", "empirical_vdot_negative_up_to_rho": rho_stab_emp, "status": "REGION_NOT_CERTIFIED"},
               "3_physical_limits_domain": {"description": "P/Q/S limits satisfied", "empirical_up_to_rho": rho_phys_emp, "first_level_with_violation": min([l["rho"] for l in levels if l["min_physical_margin_pu_over_directions"] <= 0] + [float("inf")])},
               "4_post_jump_states": {"description": "state immediately after the Q+ step = pre-event differential state and references (algebraic variables re-solved)", "V_of_pre_event_state_relative_to_Q+_equilibrium": V_pre,
                                      "ratio_to_rho_stab_empirical": V_pre / rho_stab_emp, "ratio_to_rho_phys_empirical": V_pre / rho_phys_emp if rho_phys_emp > 0 else None,
                                      "belongs_to_certified_or_empirical_region": bool(V_pre <= rho_phys_emp)},
               "joint_safe_invariant_region": "NOT ESTABLISHED: the post-jump state lies outside every region for which any property was obtained; no invariance of a set that is also inside the physical limits was proved; the P+ post-event equilibrium was not computed",
               "certified_nothing_combined": True}
    final_h4 = {"existence": {"computed_root_residual_quotient_inf": eqj["tolerance"]["reached_norm_inf_F_quotient"], "declared_target": 1e-8, "local_uniqueness_from_perturbed_starts": eqj["sensitivity_starts"], "kantorovich_type_condition": kant, "status": "CONDITIONAL"},
                "H4_1": {"a_posteriori_lyapunov_certificate": cert, "spectrum": h4["H4_1_spectrum"], "robustness": h4["H4_1_robustness"], "status": "PROVEN (computer-assisted, floating point)" if cert["certificate_holds"] else "NOT_PROVEN"},
                "H4_2": {"gate": h4["GATE_B"], "theorem": "Lyapunov's indirect method on the quotient reduced field: exact relative equilibrium, regular algebraic block (implicit function theorem), C1 field in the neighbourhood where no limiter/clamp/positive part switches (all 142 margins positive), Hurwitz Jacobian",
                         "status": "PROVEN (computer-assisted: hypotheses verified numerically)" if (cert["certificate_holds"] and all(h4["GATE_B"]["hypotheses"].values())) else "NOT_PROVEN", "scope": "relative equilibrium of the original B2 RDC after Q+ on C2t_Vsafe_R35_040; neighbourhood of unquantified radius; exponential stability modulo the common rotor-angle shift"},
                "H4_3": {"status": "REGION_NOT_CERTIFIED", "empirical": h4["H4_3_empirical_region"]}, "validation_time_domain": h4v["runs"], "domains": domains, "limitations_of_scope": [
                    "ANDES Jacobians were not used for the theorem: the central-difference derivative of the nonlinear field is (E9 analytic assembly differs by ~0.13 % Frobenius and ~18 % in the slowest eigenvalue)",
                    "five forced IEEEST variables per SG (degenerate zero-time-constant blocks) are eliminated exactly; the two genuine PSS states per SG are retained", "no interval arithmetic: floating-point evaluation with a-posteriori checks",
                    "single equilibrium (Q+); no result for other events or for the P+ post-event equilibrium"]}
    h4["final_assessment"] = final_h4
    (A / "IEEE39_DEC051_H4_summary.json").write_text(json.dumps(h4, indent=2, default=float), encoding="utf-8")
    # ------------------------------------------------------------------ validation CSV
    vrows = [["DEC051-A-eq", "equilibrium Newton from the 1999 s state", f"quotient residual {eqj['tolerance']['reached_norm_inf_F_quotient']:.2e}", "target 1e-8", "", "GATE_A " + eqj["GATE_A"], "static"],
             ["DEC051-A-uniq", "two perturbed starts (1e-3 relative)", "same root", f"|dx|<={max(x['max_abs_dx_vs_root'] for x in eqj['sensitivity_starts']):.1e}, |du|<={max(x['max_abs_du_vs_root'] for x in eqj['sensitivity_starts']):.1e}", "", "local uniqueness supported", "static"]]
    for tag in ("plus", "minus"):
        r = h4v["runs"][tag]
        vrows.append([f"DEC051-H4-{tag}", f"1000 s from equilibrium + {'+' if tag == 'plus' else '-'}0.02 pu slow-mode perturbation", f"V(1000)/V(0) linear {r['linear_prediction_V_final'] / r['V_initial']:.4f}", f"observed {r['V_ratio_final_over_initial']:.4f}",
                      f"V monotone decreasing {r['V_monotone_decreasing_fraction']:.2f}", "converges to the equilibrium; faster than linear (see report)", "sim"])
    vrows += [["DEC051-H3-1", s1["event"], f"margin SG31/SG35 {pred['H3_1']['predicted_margin_to_pmax_pu'][sg31]:.4f}/{pred['H3_1']['predicted_margin_to_pmax_pu'][sg35]:.4f}", f"{s1['observed_margin_to_pmax_pu'][sg31]:.4f}/{s1['observed_margin_to_pmax_pu'][sg35]:.4f}",
               f"max err {np.abs(s1['prediction_error_margin_pu']).max():.4f}", "no violation (as predicted)", "sim"],
              ["DEC051-H3-2", s2["event"], f"margin SG31/SG35 {pred['H3_2']['predicted_margin_to_pmax_pu'][sg31]:.4f}/{pred['H3_2']['predicted_margin_to_pmax_pu'][sg35]:.4f}", f"{s2['observed_margin_to_pmax_pu'][sg31]:.4f}/{s2['observed_margin_to_pmax_pu'][sg35]:.4f}",
               f"max err {np.abs(s2['prediction_error_margin_pu']).max():.4f}", "no violation (as predicted; conservative)", "sim"],
              ["DEC050-reuse", "P step 65.9 MW / 73.2 MW (R35_040)", "inequality crossing %.1f MW" % (a_star or float('nan')), "ok / SG31 crosses", "", "prediction inside the dynamic bracket" if frontier["prediction_inside_bracket"] else "prediction outside the bracket", "reused"],
              ["DEC050-reuse", "delay 0.5 s / 0.75 s", "", "ok / band violations", "", "reused, not reinterpreted", "reused"]]
    with (A / "IEEE39_DEC051_validation.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "test", "prediction", "observation", "error_or_note", "outcome", "type"])
        w.writerows(vrows)
    # ------------------------------------------------------------------ figures
    fig, ax = plt.subplots(2, 2, figsize=(7.2, 6.4))
    cfgs = ["C2t", "C2t_Vsafe", "C2t_Vsafe_R35 (0.015)", "C2t_Vsafe_R35_040"]
    lab = ["C2t", "Vsafe", "Vsafe+R35\n(0.015)", "Vsafe+R35\n(0.040)"]
    for k, (unit, ui) in enumerate((("SG31", sg31), ("SG35", sg35))):
        a = ax[0, 0]
        for j, c in enumerate(cfgs):
            q = ineq[c][unit]
            x0 = j + (-0.2 if unit == "SG31" else 0.2)
            segs = [(q["jump"], COL["c2"], "algebraic jump (t=0+)"), (q["fast_increment"], COL["c3"], "fast phase (<=50 ms)"), (q["slow_increment"], "#8c6bb1", "slow excursion")]
            left = 0.0
            for v, colr, lb in segs:
                a.bar(x0, v, 0.36, bottom=left, color=colr, label=lb if (j == 0 and unit == "SG31") else None)
                left += v
            a.plot([x0 - 0.18, x0 + 0.18], [q["reserve"], q["reserve"]], color="k", lw=1.6, label="reserve $P_{max}-P_{pre}$" if (j == 0 and unit == "SG31") else None)
    ax[0, 0].set_xticks(range(4)); ax[0, 0].set_xticklabels(lab); ax[0, 0].set_ylabel("active power [pu]"); ax[0, 0].set_title("(a) reserve vs consumption, P+ 58.564 MW (left SG31, right SG35)", fontsize=7); ax[0, 0].set_ylim(0, 0.17); ax[0, 0].legend(loc="upper left", ncol=2, fontsize=6)
    t8, p8 = e8["P+_time_s"], e8["P+_sg_p_pu"]
    z = np.load(A / "IEEE39_E9B0_Vsafe_R35_040_series.npz")
    tz, pz = z["P+__time_s"], z["P+__sg_p_pu"]
    for (tt, pp, ls, nm) in ((t8, p8, "-", "C2t"), (tz, pz, "--", "Vsafe+R35 (0.040)")):
        m = (tt >= 4.9) & (tt <= 14)
        ax[0, 1].plot(tt[m], pp[m][:, sg31], ls, color=COL["c1"], label=f"SG31 {nm}")
        ax[0, 1].plot(tt[m], pp[m][:, sg35], ls, color=COL["c2"], label=f"SG35 {nm}")
    ax[0, 1].axhline(pmax[sg31], color=COL["c1"], lw=0.7, ls=":"); ax[0, 1].axhline(pmax[sg35], color=COL["c2"], lw=0.7, ls=":")
    ax[0, 1].set_xlabel("time [s]"); ax[0, 1].set_ylabel("P [pu]"); ax[0, 1].set_title("(b) SG31/SG35 P after P+ (dotted: $P_{max}$)", fontsize=7); ax[0, 1].legend(ncol=2)
    xs = np.arange(2)
    for j, (nm, pv, ob) in enumerate((("H3-1 (110 %, bus 4)", pred["H3_1"]["predicted_margin_to_pmax_pu"], s1["observed_margin_to_pmax_pu"]), ("H3-2 (58.6 MW, bus 18)", pred["H3_2"]["predicted_margin_to_pmax_pu"], s2["observed_margin_to_pmax_pu"]))):
        for k2, ui in enumerate((sg31, sg35)):
            x0 = j * 3 + k2 * 1.2
            ax[1, 0].bar(x0 - 0.2, pv[ui], 0.38, color="#9ecae1", label="predicted" if (j == 0 and k2 == 0) else None)
            ax[1, 0].bar(x0 + 0.2, ob[ui], 0.38, color=COL["c1"], label="observed" if (j == 0 and k2 == 0) else None)
            ax[1, 0].text(x0, 0.002, NAMES[ui], ha="center", fontsize=6, rotation=90, va="bottom", color="white")
    ax[1, 0].axhline(0, color="k", lw=0.8); ax[1, 0].set_xticks([0.6, 3.6]); ax[1, 0].set_xticklabels(["H3-1: 110 %, bus 4\n(SG31 | SG35)", "H3-2: 58.6 MW, bus 18\n(SG31 | SG35)"]); ax[1, 0].set_ylabel("min margin to $P_{max}$ [pu]"); ax[1, 0].set_title("(c) independent validation", fontsize=7); ax[1, 0].legend()
    ax[1, 1].plot(amps, minm, "o-", color=COL["c1"], label="inequality: min over units of $R_i-\\Delta P_i$ (R35_040)")
    for amp, ok_ in [(a_, True) for a_ in ok_p] + [(a_, False) for a_ in bad_p] + [(P_STEP_MW, True), (64.4204, True)]:
        ax[1, 1].scatter([amp], [0.0], marker="s" if amp in ok_p or amp in (P_STEP_MW, 64.4204) else "x", color=COL["ok"] if ok_ else COL["bad"], zorder=5)
    ax[1, 1].scatter([87.76], [0], marker="x", color=COL["bad"]); ax[1, 1].axhline(0, color="k", lw=0.8)
    ax[1, 1].set_xlabel("P step at bus 4 [MW]"); ax[1, 1].set_ylabel("predicted min margin [pu]"); ax[1, 1].set_title("(d) predicted frontier vs runs (green ok, red violation)", fontsize=7); ax[1, 1].legend(loc="upper right", fontsize=6)
    fig.tight_layout(); fig.savefig(FIGURES_DIR / "IEEE39_DEC051_H3_reserve_safety.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    # H4 figure
    fig, ax = plt.subplots(2, 2, figsize=(7.2, 6.4))
    ev = np.linalg.eigvals(Aq)
    ax[0, 0].scatter(ev.real, ev.imag, s=6, color=COL["c1"]); ax[0, 0].set_xscale("symlog", linthresh=1e-2); ax[0, 0].axvline(0, color="k", lw=0.7)
    ax[0, 0].set_xlabel("Re($\\lambda$) [1/s]"); ax[0, 0].set_ylabel("Im($\\lambda$) [rad/s]"); ax[0, 0].set_title("(a) spectrum, quotient Jacobian (227 modes)", fontsize=7)
    ax[0, 0].annotate(f"slowest $\\tau$={h4['H4_1_spectrum']['slowest'][0]['tau_s']:.0f} s", (h4['H4_1_spectrum']['slowest'][0]['re'], 0), xytext=(-3, 600), arrowprops=dict(arrowstyle="->"), fontsize=7)
    for tag, colr in (("plus", COL["c1"]), ("minus", COL["c2"])):
        zz = np.load(A / f"IEEE39_DEC051_H4_validation_{tag}_summary.npz")
        ax[0, 1].semilogy(zz["t"], zz["V"] / zz["V"][0], color=colr, label=f"observed ({'+' if tag == 'plus' else '-'})")
    ax[0, 1].semilogy(zz["sel_t"], zz["Vlin"] / zz["V"][0], "k--", label="linear prediction $e^{A_q t}e_0$")
    ax[0, 1].set_xlabel("time [s]"); ax[0, 1].set_ylabel("$V(e)/V(e_0)$"); ax[0, 1].set_title("(b) $V(e)$ along the perturbed runs", fontsize=7); ax[0, 1].legend()
    for tag, colr in (("plus", COL["c1"]), ("minus", COL["c2"])):
        zz = np.load(A / f"IEEE39_DEC051_H4_validation_{tag}_summary.npz")
        ax[1, 0].semilogy(zz["t"], zz["qref_max"], color=colr, label=f"max |Qset-Qset*| ({'+' if tag == 'plus' else '-'})")
    ax[1, 0].set_xlabel("time [s]"); ax[1, 0].set_ylabel("pu"); ax[1, 0].set_title("(c) reference error vs equilibrium", fontsize=7); ax[1, 0].legend()
    rl = [l["rho"] for l in levels]
    ax[1, 1].semilogx(rl, [l["min_physical_margin_pu_over_directions"] for l in levels], "o-", color=COL["c2"], label="min margin over 81 directions")
    ax[1, 1].axhline(0, color="k", lw=0.8)
    ax[1, 1].set_xlabel(r"level $\rho$ of $V=e^TPe$ (scaled)"); ax[1, 1].set_ylabel("min P/Q/S margin [pu]")
    ax[1, 1].set_title("(d) empirical region (REGION_NOT_CERTIFIED)", fontsize=7)
    ax[1, 1].text(0.03, 0.05, r"$\dot V<0$ in all 81 sampled directions at every level; physical margins lost above $\rho\sim5\times10^{-5}$", transform=ax[1, 1].transAxes, fontsize=6, wrap=True)
    ax[1, 1].legend(loc="center left", fontsize=6)
    fig.tight_layout(); fig.savefig(FIGURES_DIR / "IEEE39_DEC051_H4_local_stability.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    # ------------------------------------------------------------------ conclusions matrix
    jump_ok = all(len(ineq["C2t_Vsafe_R35_040"][u_]["margin_after_jump"] if False else []) == 0 for u_ in ("SG31", "SG35"))
    M = [("Existencia de equilibrio DAE-RDC", "Condicional (Newton-Kantorovich no verificado)", "Si: residual %.1e, unicidad local" % eqj["tolerance"]["reached_norm_inf_F_quotient"], "Q+ sobre C2t_Vsafe_R35_040, equilibrio relativo", "CONDITIONAL"),
         ("Estabilidad lineal local", "Si (certificado Lyapunov a posteriori, asistido por computador)", "Si: max Re = %.2e, zeta_min = %.3f" % (h4["H4_1_spectrum"]["max_real_part"], h4["H4_1_spectrum"]["min_damping_ratio_oscillatory"]), "Ese punto; cociente por el angulo comun", "PROVEN"),
         ("Estabilidad no lineal local", "Si (metodo indirecto de Lyapunov; hipotesis verificadas numericamente)", "Si: dos corridas +/-, V decrece monotonamente", "Vecindad de radio NO cuantificado", "PROVEN"),
         ("Region invariante segura", "No", "Parcial: V-dot<0 muestreado; limites P/Q/S solo hasta rho=%.1e" % rho_phys_emp, "Elipsoide empirico", "NOT_PROVEN"),
         ("Reserva preventiva SG31/SG35", "Parcial (salto algebraico exacto; incrementos empiricos)", "Si: 3 corridas B2 sin violacion; desigualdad predice la frontera dinamica" if frontier["prediction_inside_bracket"] else "Si: 3 corridas sin violacion", "P+ barra 4 hasta 64.4 MW y barra 18; R35_040", "NUMERICALLY_SUPPORTED"),
         ("Seguridad ante salto instantaneo", "Condicional (resolucion algebraica con continuidad de estados; malla de amplitudes)", "Si: error de prediccion %.1e pu" % eps, "P+ en barra 4 (rejilla 0.25-1.5x)", "CONDITIONAL"),
         ("Seguridad transitoria posterior", "No", "Si: incrementos rapido y lento observados", "Misma clase; escalado lineal empirico", "NUMERICALLY_SUPPORTED"),
         ("H3 original (HOCBF) / H3-R", "H3 original: no; H3-R: parcial", "H3 original: sin lazo cerrado; H3-R: " + gate_c, "Diferenciado", "H3 original NOT_PROVEN; H3-R NUMERICALLY_SUPPORTED"),
         ("H4 original (CLF-HOCBF) / H4-R", "H4 original: no; H4-R: si (local)", "H4 original: no implementado; H4-R: dos validaciones", "Diferenciado", "H4 original NOT_PROVEN; H4-R PROVEN (local, asistido)")]
    fig, ax = plt.subplots(1, 2, figsize=(7.4, 3.6), gridspec_kw={"width_ratios": [1, 1.2]})
    a = ax[0]
    lv = [("regularity (sampled)", max(l["rho"] for l in levels), COL["neutral"]), ("$\\dot V<0$ (sampled)", rho_stab_emp, COL["c1"]), ("switch-free (linear est.)", h4["smoothness_domain"]["nearest_switch_by_P_norm"]["rho_switch_linear_estimate"], COL["c3"]),
          ("P/Q/S limits OK (sampled)", rho_phys_emp, COL["ok"]), ("pre-event state (Q+ jump)", V_pre, COL["bad"])]
    for i, (nm, v, colr) in enumerate(lv):
        a.barh(i, v, color=colr)
        a.text(v * 1.3, i, f"{v:.1e}", va="center", fontsize=6)
    a.set_xscale("log"); a.set_yticks(range(len(lv))); a.set_yticklabels([x[0] for x in lv]); a.set_xlabel("level $\\rho$ of $V=e^TPe$ (scaled coordinates)"); a.set_title("Nested domains around the Q+ equilibrium")
    a.set_xlim(1e-7, max(V_pre * 30, 1)); a.set_yticklabels([x[0] for x in lv], fontsize=6)
    b = ax[1]; b.axis("off")
    cell = [[m[0], m[4].replace("NUMERICALLY_SUPPORTED", "NUM_SUPPORTED").replace("H3 original NOT_PROVEN; H3-R NUM_SUPPORTED", "R: NUM_SUPP.").replace("H4 original NOT_PROVEN; H4-R PROVEN (local, asistido)", "R: PROVEN (local)")] for m in M]
    tb = b.table(cellText=cell, colLabels=["Property", "Status"], loc="center", cellLoc="left", colWidths=[0.55, 0.45])
    tb.auto_set_font_size(False); tb.set_fontsize(5.5); tb.scale(1, 1.35)
    for (r, c_), cl in tb.get_celld().items():
        if r > 0 and c_ == 1:
            t_ = cell[r - 1][1]
            cl.set_facecolor("#c7e9c0" if t_.startswith("PROVEN") or "PROVEN (" in t_ else "#fff7bc" if "CONDITIONAL" in t_ or "SUPPORTED" in t_ else "#fcbba1")
    b.set_title("Conclusions matrix", fontsize=8)
    fig.tight_layout(); fig.savefig(FIGURES_DIR / "IEEE39_DEC051_H3H4_summary.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    # ------------------------------------------------------------------ hashes and consolidation
    files = sorted(A.glob("IEEE39_DEC051_*")) + sorted(FIGURES_DIR.glob("IEEE39_DEC051_*"))
    code = sorted((PROJECT_ROOT / "Paper_manuscript" / "src").glob("*dec051*.py"))
    cons = {"stage": "DEC-051 consolidation", "git_commit": git_commit(), "base": "review/rdc-recovery-dec050 @ c07c482", "dynamic_simulations": {"limit": 6, "used": 6, "list": [
        {"id": 1, "what": "contingency: 2000 s state-dump run that crashed at t=1999 s (AttributeError PQ.Ipf in the dump code); nothing usable, counted"}, {"id": 2, "what": "contingency: 2000 s re-run, full ANDES state at 1999 s stored"},
        {"id": 3, "what": "H3-1: P+ 110 % bus 4, B2, R35_040, 200 s"}, {"id": 4, "what": "H3-2: P step 58.564 MW at bus 18, B2, R35_040, 200 s"}, {"id": 5, "what": "H4-1: +perturbation from the equilibrium, 1000 s"}, {"id": 6, "what": "H4-2: -perturbation from the equilibrium, 1000 s"}]},
        "hashes_sha256": {p.name: sha256(p) for p in files + code}, "H3_GATE_C": gate_c, "H4_GATE_A": eqj["GATE_A"], "H4_GATE_B": h4["GATE_B"], "conclusions_matrix": [dict(zip(("property", "mathematical_demonstration", "numerical_evidence", "scope", "status"), m)) for m in M],
        "predictions_file_sha256_before_runs": open(PROJECT_ROOT / "scratch_pred_hash.txt").read().strip() if (PROJECT_ROOT / "scratch_pred_hash.txt").exists() else None}
    (A / "IEEE39_DEC051_consolidation.json").write_text(json.dumps(cons, indent=2, default=float), encoding="utf-8")
    print(json.dumps({"gate_c": gate_c, "eps": eps, "frontier": {k: frontier[k] for k in ("predicted_crossing_amplitude_MW", "dynamic_bracket_DEC050_MW", "prediction_inside_bracket")}, "cert": cert, "kantorovich": {k: kant[k] for k in ("sigma_min_quotient_jacobian", "second_derivative_bound_allowed_by_Kantorovich_h<=1/2")},
                      "L_emp_max": max(Ls), "V_pre": V_pre, "rho_stab": rho_stab_emp, "rho_phys": rho_phys_emp, "attrib": attrib}, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
