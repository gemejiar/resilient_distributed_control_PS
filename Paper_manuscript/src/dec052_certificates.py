"""DEC-052 blocks B and C (H4-R): Jacobian audit, floating-point-validated Lyapunov certificate for the computed matrix, root (Newton-Kantorovich) certificate attempt.  Static evaluation only; no TDS run.
Outputs: IEEE39_DEC052_jacobian_certificate.json, IEEE39_DEC052_lyapunov_certificate.json, IEEE39_DEC052_root_certificate.json.

Validation level.  The matrix arithmetic below is validated with the standard first-order floating-point error bounds of Higham (gamma_k = k u / (1 - k u)), NOT with directed rounding.  Those bounds make the
statements rigorous for the computed floating-point matrices.  They say nothing about the distance between the computed Jacobian and the exact derivative of the ANDES equations: no validated bound
(interval arithmetic / automatic differentiation of the ANDES equations) is available, see the 'blocked_operation' entries."""
from __future__ import annotations

import json as _j

import numpy as np
import scipy.linalg as sl
from scipy.linalg import matrix_balance
from scipy.optimize import minimize_scalar

import dec052_common as K
import dec051_core as C
import e9a_linear as L
import run_dec051_equilibrium as EQ
import run_dec051_h4 as H4
from run_e0_ieee39 import ARTIFACTS_DIR as A

U = K.EPS


def gam(k):
    return K.gamma(int(k))


def chol_ok(B):
    try:
        np.linalg.cholesky(B)
        return True
    except np.linalg.LinAlgError:
        return False


def pd_lower_bound(B):
    """Lower bound of lambda_min(B) for symmetric float B (first-order Higham backward-error argument): largest s with chol(B - s I) successful, minus mu = gamma_(n+1) tr(B) 1.001."""
    n = B.shape[0]
    mu = gam(n + 1) * float(np.trace(B)) * 1.001
    hi = float(np.linalg.eigvalsh(B)[0]) * 1.5 + 1e-300
    if hi <= 2 * mu or not chol_ok(B - 2 * mu * np.eye(n)):
        return None, mu
    lo = 2 * mu
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if chol_ok(B - mid * np.eye(n)):
            lo = mid
        else:
            hi = mid
    return lo - mu, mu


def pd_upper_bound_norm(B):
    """Upper bound of lambda_max(B) = ||B||_2 (B symmetric positive definite): smallest s with chol(s I - B) successful, plus mu; never above the ||B||_inf bound."""
    n = B.shape[0]
    p_inf = float(np.abs(B).sum(axis=1).max()) * (1 + gam(n))
    mu = gam(n + 1) * n * p_inf * 1.001
    hi, lo = p_inf, float(np.linalg.eigvalsh(B)[-1]) * 0.5
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if chol_ok(mid * np.eye(n) - B):
            hi = mid
        else:
            lo = mid
    return min(hi + mu, p_inf), p_inf


def lyap_certificate(As, P):
    n = As.shape[0]
    Ps = 0.5 * (P + P.T)                                     # exactly symmetric by construction
    R0 = As.T @ Ps + Ps @ As + np.eye(n)
    err = gam(n + 3) * (np.abs(As.T) @ np.abs(Ps) + np.abs(Ps) @ np.abs(As) + np.abs(R0) + np.eye(n))
    r0_ub = float(np.linalg.norm(R0, "fro") * (1 + gam(n * n)) + np.linalg.norm(err, "fro"))
    lam_min_lb, mu = pd_lower_bound(Ps)
    lam_max_ub, p_inf = pd_upper_bound_norm(Ps)
    ok = bool(lam_min_lb is not None and lam_min_lb > 0 and r0_ub < 1)
    return {"n": n, "P_symmetrisation": "P_used = fl(0.5 (P + P^T)), exactly symmetric", "R0_frobenius_computed": float(np.linalg.norm(R0, "fro")), "R0_spectral_computed": float(np.linalg.norm(R0, 2)),
            "R0_norm_upper_bound_for_computed_matrices": r0_ub, "P_positive_definite_certified": bool(lam_min_lb is not None and lam_min_lb > 0), "lambda_min_P_lower_bound": lam_min_lb,
            "lambda_min_P_computed_eigvalsh": float(np.linalg.eigvalsh(Ps)[0]), "lambda_max_P_upper_bound": lam_max_ub, "lambda_max_P_computed": float(np.linalg.eigvalsh(Ps)[-1]), "norm_inf_P": p_inf,
            "cholesky_shift_mu": mu, "certificate_for_the_computed_matrix": ok, "margin_1_minus_R0": float(1 - r0_ub),
            "delta_A_tolerable_(1-||R0||)/(2||P||)": float((1 - r0_ub) / (2 * lam_max_ub)) if ok else None}, Ps


def complex_stability_radius(As):
    f = lambda lw: float(np.linalg.svd(As - 1j * np.exp(lw) * np.eye(As.shape[0]), compute_uv=False)[-1])
    grid = np.linspace(np.log(1e-6), np.log(1e4), 160)
    vals = [f(g) for g in grid]
    k = int(np.argmin(vals))
    res = minimize_scalar(f, bounds=(grid[max(k - 1, 0)], grid[min(k + 1, len(grid) - 1)]), method="bounded", options={"xatol": 1e-9})
    s0 = float(np.linalg.svd(As, compute_uv=False)[-1])
    return float(min(res.fun, s0, min(vals))), float(np.exp(res.x)), s0


def main() -> int:
    eq, system, ctx, st, ix, pred, u = H4.load_eq()
    d_idx = ix["d_idx"]
    n = len(d_idx)
    N = n + 20
    pin_pos = int(np.where(d_idx == int(eq["pin"]))[0][0])
    vnull = EQ.angle_null(system, ctx, st, ix, pred, u, pin_pos)
    Qm = EQ.quotient_matrix(vnull, pin_pos)
    S = np.delete(np.eye(N), pin_pos, axis=1)
    mt = np.load(A / "IEEE39_DEC051_H4_matrices.npz")
    Aq51, P51, Dd = mt["Aq"], mt["P_scaled"], mt["D"]
    D, Dinv = np.diag(Dd), np.diag(1.0 / Dd)
    sw = K.env()
    # ---------------------------------------------------------------- C1: Jacobians
    stale = {"max_abs_pset_minus_u": float(np.abs(st["pset"] - u[:10]).max()), "max_abs_qset_minus_u": float(np.abs(st["qset"] - u[10:]).max())}
    M_stale = H4.build_M(system, ctx, st, pred, u)["M"]
    st["pset"], st["qset"] = u[:10].copy(), u[10:].copy()
    M_fix = H4.build_M(system, ctx, st, pred, u)["M"]
    L.linearize = C._orig_linearize
    M_nopss = H4.build_M(system, ctx, st, pred, u)["M"]
    L.linearize = C.linearize_pss
    Jn_a = H4.numerical_jacobian(system, ctx, st, ix, pred, eq, u, 1e-6, 1e-5)
    Jn_b = H4.numerical_jacobian(system, ctx, st, ix, pred, eq, u, 1e-5, 1e-4)
    Jn_c = H4.numerical_jacobian(system, ctx, st, ix, pred, eq, u, 1e-7, 1e-6)
    q = lambda M: Qm @ M @ S
    As_ = lambda Aq: D @ Aq @ Dinv
    two = lambda X: float(np.linalg.norm(X, 2))
    rel = lambda X, Y: float(np.linalg.norm(X - Y) / np.linalg.norm(Y))
    colrel = lambda X, Y: np.linalg.norm(X - Y, axis=0) / np.maximum(np.linalg.norm(Y, axis=0), 1e-300)
    cs, cf = colrel(M_stale, Jn_a), colrel(M_fix, Jn_a)

    def spec(Mf, quotient=True):
        ev = np.linalg.eigvals(q(Mf) if quotient else Mf)
        if not quotient:
            ev = np.delete(ev, int(np.argmin(np.abs(ev))))
        osc = ev[np.abs(ev.imag) > 1e-9]
        return {"max_real_part": float(ev.real.max()), "slowest_tau_s": float(-1 / ev.real.max()), "min_damping": float((-osc.real / np.abs(osc)).min())}
    sp = {"numerical_central_difference_h": spec(Jn_a), "analytic_ANDES_assembly_with_correct_references": spec(M_fix), "analytic_ANDES_assembly_with_stale_references(DEC-051 harness)": spec(M_stale),
          "analytic_without_PSS_(E9-A_linearisation)_correct_references": spec(M_nopss, quotient=False)}
    Aq_n, Aq_f = q(Jn_a), q(M_fix)
    jac = {"stage": "DEC-052 C1/C2 Jacobian audit", "git_commit": K.git_commit(), "software": sw,
           "reference_matrix": "central-difference Jacobian of the nonlinear reduced field F(x_d, u) = [x_d'; v_RDC] with inner re-solve of the algebraic block at every evaluation (DEC-051 model with PSS); h_states=1e-6, h_refs=1e-5",
           "comparison": {"analytic_with_correct_references_vs_numerical": {"frobenius_rel": rel(M_fix, Jn_a), "max_column_rel": float(cf.max()), "max_abs_entry": float(np.abs(M_fix - Jn_a).max())},
                          "analytic_with_stale_references_vs_numerical": {"frobenius_rel": rel(M_stale, Jn_a), "max_column_rel": float(cs.max()), "max_abs_entry": float(np.abs(M_stale - Jn_a).max())},
                          "numerical_h_vs_10h": {"frobenius_rel": rel(Jn_a, Jn_b)}, "numerical_h_vs_h/10": {"frobenius_rel": rel(Jn_a, Jn_c)}},
           "CAUSE_OF_THE_1.7_PERCENT_DISCREPANCY": {
               "finding": "produced by the DEC-051 harness, not by the E9 analytic assembly: e9h_predictor.build() evaluates the original RDC law at u0 = [st['pset'], st['qset']], and run_dec051_h4.load_eq() rebuilt st from the pre-event state (pset = pn, qset = qn) without writing the equilibrium references into it. The capability factors g_P, g_Q (and the RDC derivatives) were evaluated at the wrong references (largest error in Qset 0.249 pu); the slowest mode depends on g_Q of SG31, which explains 504 s vs 427 s.",
               "stale_reference_error": stale, "fix": "assign st['pset'], st['qset'] = u* before build(); analytic and numerical Jacobians then agree at the finite-difference accuracy",
               "consequence_for_history": "E13 and DEC-050 call build() inside a live B2 replay where st['pset'], st['qset'] are the live references (run_b3_ieee39 updates them every step): no evidence of an analytic-assembly error there. What remains true for E9-A/E13/DEC-050 is the omission of the PSS states. The DEC-051 statement 'the analytic assembly of E9-A/E9-H/DEC-050 has entry errors up to 1.7 %' is WITHDRAWN (INVALIDATED); the numerical Jacobian used by DEC-051 was correct."},
           "spectra_quotient": sp, "dimensions": {"N": N, "N_quotient": N - 1, "n_dynamic": n, "references": 20}, "coordinates": "quotient coordinates e = Qm xi; scaled e_s = D e, D = diag(1/max(|xi*|, 0.1)) (DEC-051)"}
    dA = {"scaled_2norm_Anum_h_minus_Anum_10h": two(As_(Aq_n) - As_(q(Jn_b))), "scaled_2norm_Anum_h_minus_Anum_h/10": two(As_(Aq_n) - As_(q(Jn_c))), "scaled_2norm_Anum_minus_Aanalytic_correct": two(As_(Aq_n) - As_(Aq_f)),
          "scaled_2norm_Anum_minus_DEC051_Aq": two(As_(Aq_n) - As_(Aq51)), "scaled_2norm_of_A": two(As_(Aq_n))}
    jac["empirical_consistency_indicators_(not_bounds)"] = dA
    # ---------------------------------------------------------------- Lyapunov certificate
    As = As_(Aq51)
    scal_err = float(np.linalg.norm(3 * U * (np.abs(D) @ np.abs(Aq51) @ np.abs(Dinv)), "fro") * (1 + gam(N)))
    cert, _ = lyap_certificate(As, P51)
    Ab, Tb = matrix_balance(Aq51, permute=False, scale=True)       # strategy 2: diagonal similarity that balances row/column norms
    Pb = sl.solve_continuous_lyapunov(Ab.T, -np.eye(N - 1)); Pb = 0.5 * (Pb + Pb.T)
    cert_b, _ = lyap_certificate(Ab, Pb)
    scal_err_b = float(np.linalg.norm(3 * U * (np.abs(np.linalg.inv(Tb)) @ np.abs(Aq51) @ np.abs(Tb)), "fro"))
    Pn = sl.solve_continuous_lyapunov(Aq51.T, -np.eye(N - 1)); Pn = 0.5 * (Pn + Pn.T)
    cert_n, _ = lyap_certificate(Aq51, Pn)
    rC, w_at, s0 = complex_stability_radius(As)
    Tbi = np.linalg.inv(Tb)
    dA_b = {"scaled_2norm_Anum_h_minus_Anum_10h": two(Tbi @ (Aq_n - q(Jn_b)) @ Tb), "scaled_2norm_Anum_h_minus_Anum_h/10": two(Tbi @ (Aq_n - q(Jn_c)) @ Tb), "scaled_2norm_Anum_minus_Aanalytic_correct": two(Tbi @ (Aq_n - Aq_f) @ Tb), "scaled_2norm_of_A": two(Ab)}
    rC_b, w_b, s0_b = complex_stability_radius(Ab)
    dtol = cert["delta_A_tolerable_(1-||R0||)/(2||P||)"]
    ly = {"stage": "DEC-052 C3/C4 Lyapunov certificate", "git_commit": K.git_commit(), "software": sw, "arithmetic": "binary64; first-order Higham bounds gamma_k; no directed rounding (valid for the computed floating matrices, not interval arithmetic)",
          "inputs_sha256": {"IEEE39_DEC051_H4_matrices.npz": K.sha(A / "IEEE39_DEC051_H4_matrices.npz")}, "matrix": "Ahat_s = D Aq D^-1 with Aq the DEC-051 quotient Jacobian (central differences), D = diag(1/max(|xi*|,0.1))",
          "P": "DEC-051 solution of Ahat_s^T P + P Ahat_s = -I (scaled coordinates)",
          "strategy_1_DEC051_scaling": {**cert, "rounding_of_scaling_product_D_Aq_Dinv_frobenius_bound": scal_err},
          "strategy_2_diagonal_balancing_similarity_(scipy_matrix_balance), P_recomputed": {**cert_b, "rounding_of_balancing_product_frobenius_bound": scal_err_b},
          "reference_natural_coordinates": cert_n,
          "inequality": "||R0||_2 + 2 ||P||_2 delta_A < 1  with  A^T P + P A = -I + R0 + E^T P + P E,  E = A - Ahat",
          "delta_A_available": None, "delta_A_status": "NOT_AVAILABLE: no validated bound of ||E||_2 (see jacobian certificate)",
          "delta_A_tolerable_strategy_1": dtol, "delta_A_tolerable_strategy_2": cert_b["delta_A_tolerable_(1-||R0||)/(2||P||)"], "delta_A_tolerable_natural": cert_n["delta_A_tolerable_(1-||R0||)/(2||P||)"],
          "empirical_consistency_scaled_2norm_(not_a_bound)": dA, "empirical_consistency_in_balanced_coordinates_(not_a_bound)": dA_b,
          "complex_stability_radius_balanced_coordinates_numerical_(not_validated)": {"r_C": rC_b, "omega_at_min": w_b, "sigma_min_at_omega_0": s0_b},
          "complex_stability_radius_of_Ahat_s_numerical_(not_validated)": {"r_C": rC, "omega_at_min": w_at, "sigma_min_at_omega_0": s0, "meaning": "Ahat + E is Hurwitz for every ||E||_2 < r_C (exact statement about the matrix; the number is an unvalidated floating evaluation)",
                                                                              "lyapunov_lower_bound_1_over_(2 lambda_max(P))": float(1 / (2 * cert["lambda_max_P_upper_bound"]))},
          "classification": {"linear_stability_numerical": "SUPPORTED (eigenvalues, a-posteriori Lyapunov residual, two independent Jacobian assemblies, two full-ANDES time-domain runs)",
                             "linear_stability_rigorous_for_computed_matrix": "CERTIFIED" if cert["certificate_for_the_computed_matrix"] else "NOT_CERTIFIED", "linear_stability_rigorous_for_exact_Jacobian": "NOT_CERTIFIED (delta_A unavailable)"}}
    dtol_b = cert_b["delta_A_tolerable_(1-||R0||)/(2||P||)"]
    ly["comparison_empirical_vs_tolerable"] = {"balanced_empirical_Anum_vs_Aanalytic_over_tolerable_strategy_2": float(dA_b["scaled_2norm_Anum_minus_Aanalytic_correct"] / dtol_b) if dtol_b else None, "balanced_empirical_h_vs_10h_over_tolerable_strategy_2": float(dA_b["scaled_2norm_Anum_h_minus_Anum_10h"] / dtol_b) if dtol_b else None, "empirical_Anum_vs_Aanalytic_over_tolerable_strategy_1": float(dA["scaled_2norm_Anum_minus_Aanalytic_correct"] / dtol) if dtol else None,
                                              "empirical_h_vs_10h_over_tolerable_strategy_1": float(dA["scaled_2norm_Anum_h_minus_Anum_10h"] / dtol) if dtol else None,
                                              "reading": "ratios > 1: finite-difference-level uncertainty of the Jacobian exceeds what the Lyapunov inequality with Q = I can absorb, so even a validated delta_A of the empirical size would not close the certificate"}
    K.dump("IEEE39_DEC052_lyapunov_certificate.json", ly)
    jac["lyapunov_tolerance_link"] = {"delta_A_tolerable_strategy_1": dtol, "delta_A_tolerable_strategy_2": ly["delta_A_tolerable_strategy_2"]}
    blocked = ("A validated ||E||_2 needs (i) interval enclosures of the first and second derivatives of the 706 ANDES equations (250 states + 456 algebraic variables; compiled numpy callables without interval or AD backend; "
               "pyinterval, jax and autograd are not installed), (ii) an enclosure of the implicit elimination of the 486 x 486 algebraic block and of its derivative, (iii) interval evaluation of the RDC law (capability factors with positive parts, graph Laplacian) "
               "and of the discrete limiter logic, (iv) a validated bound of the finite-difference truncation error (third derivatives) and of the location error of the exact equilibrium. None is available; step studies are consistency checks only.")
    jac["delta_A_bound"] = {"status": "NOT_CERTIFIED", "blocked_operation": blocked, "components_budget": {"rounding_of_scaling_product": scal_err, "finite_difference_truncation": "NOT BOUNDED", "algebraic_elimination": "NOT BOUNDED",
                                                                                                               "equilibrium_location": "NOT BOUNDED (needs the root certificate)", "RDC_derivative_finite_difference": "NOT BOUNDED"}}
    K.dump("IEEE39_DEC052_jacobian_certificate.json", jac)
    # ---------------------------------------------------------------- B: root certificate attempt
    C.set_state(system, np.array(eq["x"]), np.array(eq["y"]))
    C.inner_solve(system, ctx, st, u, ix, pred.cache, tol=1e-13)
    F0, f0, g0 = EQ.residual_vec(system, ctx, st, ix, u)
    Fq = EQ.quotient(F0, vnull, pin_pos)
    As2 = As_(Aq_n)
    Cinv = np.linalg.inv(As2)
    beta = two(Cinv)
    eta = float(np.linalg.norm(Cinv @ (D @ Fq)))
    lreq = 1.0 / (2 * beta * eta)
    j51 = _j.loads((A / "IEEE39_DEC051_equilibrium.json").read_text(encoding="utf-8"))
    h51 = _j.loads((A / "IEEE39_DEC051_H4_summary.json").read_text(encoding="utf-8"))
    rem = [lv["max_relative_nonlinear_remainder"] for lv in h51["H4_3_empirical_region"]["levels"]]
    alg = float(max(np.abs(g0).max(), np.abs(f0[ix["z_idx"]]).max()))
    root = {"stage": "DEC-052 B root certificate attempt", "git_commit": K.git_commit(), "software": sw,
            "problem": "F_q(z) = Qm [f_d(x_d, y, u)/Tf ; v_RDC(u, P, Q, V, omega)] with y = phi(x_d, u) from the inner Newton solve of [f_z; g] = 0; unknown z = Qm xi in R^227 (SG31 angle fixed); relative equilibrium F = c v_null removed by the quotient; original RDC, E8 actuator maps, PSS kept",
            "approximate_root_z0": "IEEE39_DEC051_equilibrium_state.npz", "inputs_sha256": {f: K.sha(A / f) for f in ("IEEE39_DEC051_equilibrium_state.npz", "IEEE39_DEC051_equilibrium.json")},
            "residuals_recomputed_now": {"quotient_residual_inf": float(np.abs(Fq).max()), "algebraic_residual_inf": alg, "common_angle_rate_c": float(F0[pin_pos])},
            "residuals_DEC051": {"quotient": j51["tolerance"]["reached_norm_inf_F_quotient"], "g": j51["tolerance"]["reached_g_inf"]},
            "newton_history_last_iterations": j51["newton_history"][-4:], "local_uniqueness_starts": j51["sensitivity_starts"],
            "kantorovich_quantities_scaled_2norm": {"norm": "||D e||_2 on the domain, ||D F||_2 on the range (D of DEC-051)", "C": "inverse of the scaled central-difference Jacobian", "beta=||C||_2": beta, "eta=||C F_q(z0)||_2": eta,
                                                    "cond_2(A_s)": float(np.linalg.cond(As2)), "required_Lipschitz_constant_of_J_on_the_ball_L_req=1/(2 beta eta)": lreq, "ball_radius_if_satisfied": eta,
                                                    "contraction_condition_needs": "sup_{z in X} ||I - C J(z)|| < 1 and ||C F(z0)|| + sup||I - C J(z)|| r < r, i.e. a validated inclusion of J(X), or equivalently L <= L_req"},
            "L_not_validated_diagnostics": {"DEC051_sampled_relative_nonlinear_remainder_of_Vdot_at_levels": rem, "DEC051_sampled_second_derivative_ratio_max": 160,
                                            "reading": "sampled values, NOT a bound; the DEC-051 'bound 1521' was computed in a different norm and must not be compared with L_req above"},
            "interval_inclusion_attempted": False,
            "reason": "no validated enclosure of J(X) or of the second derivatives is obtainable with the available infrastructure (blocked operation below); mpmath high precision, step comparisons and random sampling are excluded by the protocol as substitutes for an inclusion",
            "blocked_operation": blocked,
            "algebraic_elimination_error": "the inner solve reaches [f_z; g] residual %.1e; the elimination error is not enclosed in the interval sense" % alg,
            "GATE_B": "ROOT_NUMERICALLY_VERIFIED", "justification": "quotient residual %.1e with quadratic final Newton steps, local uniqueness from perturbed starts, algebraic block nonsingular (validated for the computed matrix), but no inclusion of J(X)" % float(np.abs(Fq).max()),
            "what_would_certify_it": "L <= %.3e on the ball of radius %.2e (scaled) would give a unique root in that ball (Newton-Kantorovich); it would locate the root only: the stability statement would still need the validated delta_A" % (lreq, eta)}
    K.dump("IEEE39_DEC052_root_certificate.json", root)
    print({"stale": stale, "fix_frob": rel(M_fix, Jn_a), "stale_frob": rel(M_stale, Jn_a), "spectra": sp, "empirical": dA})
    print({"cert_ok": cert["certificate_for_the_computed_matrix"], "R0_ub": cert["R0_norm_upper_bound_for_computed_matrices"], "lam_min_lb": cert["lambda_min_P_lower_bound"], "lam_max_ub": cert["lambda_max_P_upper_bound"], "dtol": dtol,
           "dtol_b": ly["delta_A_tolerable_strategy_2"], "dtol_n": ly["delta_A_tolerable_natural"], "cert_b_ok": cert_b["certificate_for_the_computed_matrix"], "r_C": rC, "beta": beta, "eta": eta, "L_req": lreq})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
