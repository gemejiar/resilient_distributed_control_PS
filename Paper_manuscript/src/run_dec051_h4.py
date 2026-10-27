"""DEC-051 block B (H4-R): local stability of the exact DAE-RDC relative equilibrium (no time stepping).

Reduction.  At the equilibrium of IEEE39_DEC051_equilibrium.json the algebraic block (quasi-algebraic states + algebraic variables) is regular (min singular value reported), so y = phi(x, u) locally
(implicit function theorem) and the closed loop is the ODE  xi' = F(xi),  xi = (x_d, u) in R^N (N = 208 dynamic states, including the two genuine PSS states per SG, + 20 references), whose Jacobian is the
matrix M of e9h_predictor.build with the PSS-complete linearisation of dec051_core (ANDES analytic Jacobians, Schur complement of the algebraic block, actuator maps, finite-difference linearisation of
the original RDC law).  The only marginal direction is the common rotor-angle shift v_null; quotient coordinates e = Qm xi (Qm removes the component along v_null at the SG31 angle) give
A_q = Qm M S of dimension N - 1, with S the embedding (SG31 angle coordinate = 0).
H4-1: spectrum of A_q (Hurwitz, margin, damping, conditioning, robustness to Jacobian errors).   H4-2: Lyapunov's indirect method (hypotheses checked: exact equilibrium, regular algebraic block,
smoothness domain = no limiter / clamp / positive-part switch active, Jacobian accuracy).   H4-3 (certified invariant sublevel set) is attempted only through an empirical estimate; it is labelled
REGION_NOT_CERTIFIED because no validated bound of the second derivatives of the ANDES vector field is available."""

from __future__ import annotations

import json

import numpy as np
import scipy.linalg as sl

import dec051_core as C
import e9a_linear as L
import e9h_predictor as PR
import run_dec051_equilibrium as EQ
import run_e8_ieee39 as e8
from run_e0_ieee39 import ARTIFACTS_DIR as A, git_commit, sha256

NAMES = EQ.NAMES


def load_eq():
    eq = dict(np.load(A / "IEEE39_DEC051_equilibrium_state.npz"))
    system, ctx = C.build_system("S0")
    st = C.rdc_state(system, ctx)
    for k in C.PQ_PARAMS:
        getattr(system.PQ, k).v[:] = eq["PQ_" + k]
    ix = C.index_sets(system)
    C.set_state(system, eq["x"], eq["y"])
    pred = PR.LinearPredictor(ctx)
    pred.lim = ctx["lim"]
    u = eq["u"].copy()
    C.apply_params(system, ctx, st, u)
    L.linearize(system, ctx, cache=pred.cache)
    C.inner_solve(system, ctx, st, u, ix, pred.cache, tol=1e-13)
    return eq, system, ctx, st, ix, pred, u


def build_M(system, ctx, st, pred, u):
    vn = EQ.rates(system, ctx, st, u)
    return pred.build(system, st, vn[:10], vn[10:], 1999.0, refresh_params=True)


def numerical_jacobian(system, ctx, st, ix, pred, eq, u, hs, hu):
    """Central-difference Jacobian of the nonlinear reduced vector field F(x_d, u) = [x_d'; v_RDC] at the equilibrium: every evaluation re-solves the quasi-algebraic states and the algebraic variables
    (inner Newton, forced PSS variables kept consistent), i.e. it is the derivative of the exact map whose zero was computed, with no analytic-Jacobian assembly involved."""
    d_idx = ix["d_idx"]
    n = len(d_idx)
    N = n + 20
    x0, y0 = np.array(eq["x"]), np.array(eq["y"])

    def F(vec):
        xn = x0.copy(); xn[d_idx] += vec[:n]
        un = u + vec[n:]
        C.set_state(system, xn, y0)
        C.inner_solve(system, ctx, st, un, ix, pred.cache, tol=1e-13)
        f, _, _ = EQ.residual_vec(system, ctx, st, ix, un)
        return f

    J = np.zeros((N, N))
    for j in range(N):
        h = hs if j < n else hu
        e = np.zeros(N); e[j] = h
        J[:, j] = (F(e) - F(-e)) / (2 * h)
    C.set_state(system, x0, y0)
    return J


def spectrum(Aq):
    ev, V = np.linalg.eig(Aq)
    re, im = ev.real, ev.imag
    osc = ev[np.abs(im) > 1e-9]
    zeta = -osc.real / np.abs(osc)
    order = np.argsort(-re)
    return ev, V, {"max_real_part": float(re.max()), "n_eigenvalues": int(len(ev)), "n_nonnegative_real_part": int((re >= -1e-12).sum()), "n_with_abs_real_part_below_1e-9": int((np.abs(re) < 1e-9).sum()),
                   "min_damping_ratio_oscillatory": float(zeta.min()), "least_damped": [{"re": float(osc[i].real), "im": float(osc[i].imag), "freq_hz": float(abs(osc[i].imag) / (2 * np.pi)), "zeta": float(zeta[i])} for i in np.argsort(zeta)[:8]],
                   "slowest": [{"re": float(ev[i].real), "im": float(ev[i].imag), "tau_s": float(-1 / ev[i].real)} for i in order[:8]], "condition_number_eigenvectors": float(np.linalg.cond(V))}


def lyap(Aq, D=None):
    """A^T P + P A = -I (optionally in diagonally scaled coordinates e_s = D e)."""
    if D is not None:
        Aq = D @ Aq @ np.linalg.inv(D)
    Pm = sl.solve_continuous_lyapunov(Aq.T, -np.eye(Aq.shape[0]))
    Pm = 0.5 * (Pm + Pm.T)
    w = np.linalg.eigvalsh(Pm)
    res = Aq.T @ Pm + Pm @ Aq + np.eye(Aq.shape[0])
    return Pm, {"lambda_min_P": float(w.min()), "lambda_max_P": float(w.max()), "cond_P": float(w.max() / w.min()) if w.min() > 0 else None, "positive_definite": bool(w.min() > 0),
                "residual_inf_norm": float(np.abs(res).max()), "decay_rate_of_V_per_s_lower_bound": float(1.0 / w.max()), "exponential_rate_of_norm_per_s": float(1.0 / (2 * w.max()))}


def switch_margins(system, ctx, st, ix, u, lin):
    """Distance of every nonsmooth element (ANDES limiters / anti-windups of the TDS-active models, RDC clamp and positive parts) to its switching point at the equilibrium, with the linear sensitivity of
    the switching variable to the state (so that a P-norm radius can be attached).  Elements that cannot be evaluated are listed as 'unchecked'."""
    from andes.core.var import State
    rows, unchecked = [], []
    n_d = len(ix["d_idx"])
    n = n_d + 20
    d_pos = {int(a): k for k, a in enumerate(lin["d_idx_original"])}
    z_pos = {int(a): k for k, a in enumerate(lin["z_idx_original"])}
    cy_x, cy_u = lin["Cy_x"], lin["Cy_u"]
    for mn, m in system.models.items():
        if m.n == 0 or mn in ("PV", "Slack"):
            continue
        for dn, d in m.discrete.items():
            if not (hasattr(d, "lower") and hasattr(d, "upper") and hasattr(d, "u")):
                continue
            try:
                var = d.u
                val = np.asarray(var.v, float)
                lo, up = np.asarray(d.lower.v, float) * np.ones_like(val), np.asarray(d.upper.v, float) * np.ones_like(val)
                addr = np.asarray(var.a, int)
                for k in range(len(val)):
                    sens = np.zeros(n)
                    if isinstance(var, State):
                        a = int(addr[k])
                        if a in d_pos:
                            sens[d_pos[a]] = 1.0
                        elif a in z_pos:
                            sens = np.concatenate([lin["wx_z"][z_pos[a]], lin["wu_z"][z_pos[a]]])
                        else:
                            continue     # forced PSS state (eliminated): not an independent variable
                    else:
                        sens = np.concatenate([cy_x[int(addr[k])], cy_u[int(addr[k])]])
                    for side, lim_v, sign in (("upper", up[k], 1.0), ("lower", lo[k], -1.0)):
                        if np.isfinite(lim_v) and abs(lim_v) < 1e8:
                            rows.append({"element": f"{mn}.{dn}[{k}]", "side": side, "value": float(val[k]), "limit": float(lim_v), "margin": float(sign * (lim_v - val[k])), "sens": sens * sign})
            except Exception as exc:
                unchecked.append({"element": f"{mn}.{dn}", "reason": repr(exc)[:120]})
    for i in range(ctx["n_sg"]):
        for sign in (1.0, -1.0):
            sens = np.zeros(n); sens[n_d + 10 + i] = e8.KAPPA_SG * sign
            z = e8.KAPPA_SG * (u[10 + i] - st["qn"][i])
            rows.append({"element": f"RDC.z_clamp[SG{i}]", "side": "upper" if sign > 0 else "lower", "value": float(z), "limit": e8.Z_CLAMP * sign, "margin": float(e8.Z_CLAMP - sign * z), "sens": sens})
    gp, gq = e8.capability_factors(u[:10], u[10:], ctx["lim"])
    h = 1e-6
    for i in range(10):
        for lab, g0, idx in (("gP", gp[i], 0), ("gQ", gq[i], 1)):
            sens = np.zeros(n)
            for j in range(20):
                uu = u.copy(); uu[j] += h
                gpp, gqq = e8.capability_factors(uu[:10], uu[10:], ctx["lim"])
                sens[n_d + j] = ((gpp, gqq)[idx][i] - g0) / h
            rows.append({"element": f"RDC.{lab}_positive_part[{NAMES[i]}]", "side": "lower", "value": float(g0), "limit": 0.0, "margin": float(g0), "sens": -sens})
    return rows, unchecked


def main() -> int:
    eq, system, ctx, st, ix, pred, u = load_eq()
    d_idx = ix["d_idx"]
    n = len(d_idx)
    N = n + 20
    pin_pos = int(np.where(d_idx == int(eq["pin"]))[0][0])
    pb = build_M(system, ctx, st, pred, u)
    M_E9 = pb["M"]
    Jn_a = numerical_jacobian(system, ctx, st, ix, pred, eq, u, 1e-6, 1e-5)
    Jn_b = numerical_jacobian(system, ctx, st, ix, pred, eq, u, 1e-5, 1e-4)
    M = Jn_a            # the Jacobian used for every statement below is the central-difference one of the nonlinear field
    vnull = EQ.angle_null(system, ctx, st, ix, pred, u, pin_pos)
    Qm = EQ.quotient_matrix(vnull, pin_pos)
    S = np.delete(np.eye(N), pin_pos, axis=1)
    Aq = Qm @ M @ S
    sv = np.linalg.svd(M, compute_uv=False)
    ev_full = np.linalg.eigvals(M)
    out: dict = {"stage": "DEC-051 H4", "git_commit": git_commit(), "doc": __doc__, "equilibrium_json_sha256": sha256(A / "IEEE39_DEC051_equilibrium.json"), "dimensions": {"N_total": N, "n_dynamic": n, "n_refs": 20, "N_quotient": N - 1}}
    wl = np.linalg.svd(M.T)[2][-1]
    out["symmetry"] = {"smallest_singular_values_of_M": sv[-3:].tolist(), "norm_M_vnull": float(np.linalg.norm(M @ vnull)), "norm_Mt_wnull": float(np.linalg.norm(M.T @ wl)), "n_nonzero_entries_vnull": int((vnull != 0).sum()),
                       "vnull_nonzero_values_unique": sorted(set(np.round(vnull[vnull != 0], 8).tolist())), "vnull_support_names": [str(system.dae.x_name[d_idx[k]]) for k in np.where(vnull[:n] != 0)[0]],
                       "single_zero_direction_original_sv_ratio_criterion": bool(sv[-1] < 1e-8 * sv[0] and sv[-2] > 1e-6 * sv[0]), "sv_max": float(sv[0]), "sv_gap_second_over_smallest": float(sv[-2] / max(sv[-1], 1e-300)),
                       "single_zero_direction": bool(int((np.abs(ev_full.real) < 1e-9).sum()) == 1 and sv[-1] < 1e-8 * sv[-2]), "max_real_eig_full_M": float(ev_full.real.max()), "n_eig_abs_real_below_1e-9_full_M": int((np.abs(ev_full.real) < 1e-9).sum())}
    ev, V, spec = spectrum(Aq)
    out["H4_1_spectrum"] = spec
    Aq_E9 = Qm @ M_E9 @ S
    evE9 = np.linalg.eigvals(Aq_E9)
    evB = np.linalg.eigvals(Qm @ Jn_b @ S)
    zE9 = [-e.real / abs(e) for e in evE9 if abs(e.imag) > 1e-9]
    out["jacobian_comparison"] = {"used": "central differences of the nonlinear reduced field (h_states = 1e-6, h_refs = 1e-5), inner solve at every evaluation",
                                  "numerical_step_study_frobenius_rel_(h)_vs_(10h)": float(np.linalg.norm(Jn_a - Jn_b) / np.linalg.norm(Jn_a)), "max_real_part_with_10h": float(evB.real.max()),
                                  "max_abs_difference_sorted_eigenvalues_h_vs_10h": float(np.abs(np.sort_complex(evB) - np.sort_complex(ev)).max()),
                                  "E9_machinery_vs_numerical_frobenius_rel": float(np.linalg.norm(M_E9 - Jn_a) / np.linalg.norm(Jn_a)),
                                  "E9_machinery_spectrum": {"max_real_part": float(evE9.real.max()), "slowest_tau_s": float(-1 / evE9.real.max()), "min_damping_ratio": float(min(zE9))},
                                  "numerical_spectrum": {"max_real_part": spec["max_real_part"], "slowest_tau_s": spec["slowest"][0]["tau_s"], "min_damping_ratio": spec["min_damping_ratio_oscillatory"]},
                                  "note": "the E9-A/E9-H analytic assembly (used in E13 and DEC-050) differs from the numerical derivative by up to 1.7 % in some columns (rate rows of Pset versus the BusFreq states); the slowest eigenvalue, which depends on the capability factor of SG31 (g_Q = 0.12), moves by about 18 %"}
    # effect of the PSS on the spectrum (the E9-A / DEC-050 linearisation dropped it)
    L.linearize = C._orig_linearize
    pbn = build_M(system, ctx, st, pred, u)
    L.linearize = C.linearize_pss
    en = np.linalg.eigvals(pbn["M"])
    out["effect_of_PSS_on_spectrum"] = {"E9_machinery_without_PSS_max_real_nonzero": float(np.sort(en.real)[-2]), "with_PSS_max_real": spec["max_real_part"],
                                        "without_PSS_min_damping": float(min(-e.real / abs(e) for e in en if abs(e.imag) > 1e-9)), "with_PSS_min_damping": spec["min_damping_ratio_oscillatory"],
                                        "dimension_without": int(pbn["M"].shape[0]), "dimension_with": int(M.shape[0]), "note": "DEC-050 C3 numbers were computed without the PSS; they are superseded by the ones in this file"}
    rng = np.random.default_rng(5)
    rob = {}
    for rel in (1e-6, 1e-4):
        mx = [float(np.linalg.eigvals(Aq * (1 + rel * rng.standard_normal(Aq.shape))).real.max()) for _ in range(20)]
        rob[f"relative_entrywise_perturbation_{rel:g}"] = {"max_real_part_over_20_trials": max(mx), "min": min(mx)}
    fdres = {"numerical_jacobian_step_10x": {"max_real_part": float(evB.real.max()), "max_abs_difference_of_sorted_eigenvalues": float(np.abs(np.sort_complex(evB) - np.sort_complex(ev)).max())}}
    rob["finite_difference_step_of_parameter_derivatives"] = fdres
    out["H4_1_robustness"] = rob
    lin = L.linearize(system, ctx, cache=pred.cache)
    raw = lin["raw"]
    nz = lin["n_quasi_algebraic"]
    zi, di = raw["z_idx"], raw["d_idx"]
    kmat = np.block([[raw["fx"][np.ix_(zi, zi)], raw["fy"][zi]], [raw["gx"][:, zi], raw["gy"]]])
    lin["wx_z"] = np.linalg.solve(kmat, -np.vstack([raw["fx"][np.ix_(zi, di)], raw["gx"][:, di]]))[:nz]
    lin["wu_z"] = np.linalg.solve(kmat, -np.vstack([raw["fu"][zi], raw["gu"]]))[:nz]
    out["regularity"] = {"algebraic_block_min_singular_value": lin["gy_min_sv"], "algebraic_block_cond": lin["gy_cond"], "equilibrium_gate": json.loads((A / "IEEE39_DEC051_equilibrium.json").read_text(encoding="utf-8"))["GATE_A"]}
    xs = np.concatenate([np.array(eq["x"])[d_idx], eq["u"]])
    xs_q = np.delete(xs, pin_pos)
    D = np.diag(1.0 / np.maximum(np.abs(xs_q), 0.1))
    P_nat, ly_nat = lyap(Aq)
    P_sc, ly_sc = lyap(Aq, D)
    out["H4_2_lyapunov"] = {"natural_coordinates": ly_nat, "scaled_coordinates": ly_sc, "scaling": "e_s = D e with D = diag(1 / max(|xi*_k|, 0.1))"}
    rows, unchecked = switch_margins(system, ctx, st, ix, u, lin)
    Pinv = np.linalg.inv(P_sc)
    Dinv = np.linalg.inv(D)
    rad = []
    for r in rows:
        sq = np.delete(r["sens"], pin_pos)
        sc = sq @ Dinv
        den = float(np.sqrt(max(sc @ Pinv @ sc, 1e-300)))
        rad.append(r["margin"] / den if r["margin"] > 0 else -1.0)
    kmin = int(np.argmin(rad))
    out["smoothness_domain"] = {"n_elements_checked": len(rows), "all_inactive_at_equilibrium": bool(all(r["margin"] > 0 for r in rows)), "min_margin": float(min(r["margin"] for r in rows)),
                                "nearest_switch_by_P_norm": {"element": rows[kmin]["element"], "side": rows[kmin]["side"], "margin": rows[kmin]["margin"], "rho_switch_linear_estimate": float(rad[kmin] ** 2)},
                                "unchecked_elements": unchecked, "elements_with_smallest_margins": [{"element": r["element"], "side": r["side"], "margin": r["margin"]} for r in sorted(rows, key=lambda r: r["margin"])[:10]]}
    rho_sw = out["smoothness_domain"]["nearest_switch_by_P_norm"]["rho_switch_linear_estimate"]
    k0 = int(np.argmax(ev.real))
    vq = V[:, k0].real
    vq = vq / np.abs(vq).max()
    xi = S @ vq
    np.savez_compressed(A / "IEEE39_DEC051_H4_mode.npz", v_x=xi[:n], v_u=xi[n:], eigenvalue=ev[k0].real, tau_s=-1 / ev[k0].real)
    out["dominant_slow_mode"] = {"eigenvalue": float(ev[k0].real), "tau_s": float(-1 / ev[k0].real), "imag": float(ev[k0].imag), "max_abs_component_on_Pset": float(np.abs(xi[n:n + 10]).max()), "max_abs_component_on_Qset": float(np.abs(xi[n + 10:]).max()),
                                 "dominant_units_Qset": [NAMES[i] for i in np.argsort(-np.abs(xi[n + 10:]))[:3]]}
    x_eq, y_eq = np.array(eq["x"]), np.array(eq["y"])
    u_eq = eq["u"]
    dirs = []
    for i in np.argsort(-ev.real)[:12]:
        dirs += [V[:, i].real, V[:, i].imag]
    ord_z = [i for i in np.argsort(-ev.real / np.abs(ev)) if abs(ev[i].imag) > 1e-9][:12]
    for i in ord_z:
        dirs += [V[:, i].real, V[:, i].imag]
    dirs = [d for d in dirs if np.linalg.norm(d) > 1e-12]
    wP, vP = np.linalg.eigh(P_sc)
    for k in range(1, 6):          # directions of the largest eigenvalues of P: the worst case of the LINEAR part (minimum of e'e / e'Pe)
        dirs.append(vP[:, -k])
    for _ in range(40):
        dirs.append(rng.standard_normal(N - 1))
    sqP = sl.sqrtm(P_sc).real
    levels = [rho_sw * f for f in (1e-4, 1e-3, 1e-2, 1e-1, 1.0)]

    def vdot_at(es):
        e = Dinv @ es
        xi_full = S @ e
        xnew = x_eq.copy(); xnew[d_idx] += xi_full[:n]
        unew = u_eq + xi_full[n:]
        C.set_state(system, xnew, y_eq)
        info = C.inner_solve(system, ctx, st, unew, ix, pred.cache, tol=1e-11)
        F0, _, _ = EQ.residual_vec(system, ctx, st, ix, unew)
        Fq = EQ.quotient(F0, vnull, pin_pos)
        vd = 2 * es @ P_sc @ (D @ Fq)
        p, q, v, om = EQ.outputs(system, st)
        lim = ctx["lim"]
        marg = float(min((lim["pmax"] - p).min(), (p - lim["pmin"]).min(), (lim["qmax"] - q).min(), (q - lim["qmin"]).min(), (lim["smax"] - np.hypot(p, q)).min()))
        vb = np.asarray(system.dae.y[np.asarray(system.Bus.v.a)], float)
        return vd, -es @ es, info["converged"], marg, float(vb.min()), float(vb.max())

    results = []
    for rho in levels:
        vds, rel, conv, margs, vmin, vmax = [], [], [], [], [], []
        for d in dirs:
            z = np.linalg.solve(sqP, d / np.linalg.norm(d))
            z = z / np.sqrt(z @ P_sc @ z)
            vd, vl, ok, mg, vm, vM = vdot_at(np.sqrt(rho) * z)
            vds.append(vd / rho); rel.append((vd - vl) / abs(vl)); conv.append(ok); margs.append(mg); vmin.append(vm); vmax.append(vM)
        results.append({"rho": rho, "rho_over_rho_switch": rho / rho_sw, "n_directions": len(dirs), "max_Vdot_over_V": float(max(vds)), "all_negative": bool(max(vds) < 0), "max_relative_nonlinear_remainder": float(max(np.abs(rel))),
                        "all_inner_converged": bool(all(conv)), "min_physical_margin_pu_over_directions": float(min(margs)), "bus_voltage_min": float(min(vmin)), "bus_voltage_max": float(max(vmax))})
        print(results[-1], flush=True)
    C.set_state(system, x_eq, y_eq)
    out["H4_3_empirical_region"] = {"status": "REGION_NOT_CERTIFIED", "rho_switch_linear_estimate": rho_sw, "levels": results,
                                    "note": "sampling of V-dot along the nonlinear vector field on V = rho for eigen-directions and random directions: numerical validation only; no bound of the remainder is claimed"}
    h41 = spec["max_real_part"] < -1e-6 and spec["n_with_abs_real_part_below_1e-9"] == 0 and out["symmetry"]["single_zero_direction"]
    hyp = {"exact_equilibrium": out["regularity"]["equilibrium_gate"] == "EQUILIBRIUM_EXACT", "regular_algebraic_block": lin["gy_min_sv"] > 1e-8, "hurwitz_quotient": bool(h41),
           "all_switches_inactive_with_positive_margin": out["smoothness_domain"]["all_inactive_at_equilibrium"] and not unchecked,
           "jacobian_accuracy_ok": rob["finite_difference_step_of_parameter_derivatives"]["numerical_jacobian_step_10x"]["max_real_part"] < -1e-6 and rob["relative_entrywise_perturbation_1e-06"]["max_real_part_over_20_trials"] < -1e-6,
           "lyapunov_P_positive_definite": ly_sc["positive_definite"] and ly_nat["positive_definite"]}
    out["GATE_B"] = {"hypotheses": hyp, "H4_1": "PROVEN_COMPUTER_ASSISTED" if (h41 and hyp["jacobian_accuracy_ok"]) else "NOT_PROVEN", "H4_2": "ACCEPTED" if all(hyp.values()) else "NOT_ACCEPTED", "H4_3": "REGION_NOT_CERTIFIED"}
    (A / "IEEE39_DEC051_H4_summary.json").write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
    np.savez_compressed(A / "IEEE39_DEC051_H4_matrices.npz", Aq=Aq, P_scaled=P_sc, D=np.diag(D), eig=ev)
    print(json.dumps({"GATE_B": out["GATE_B"], "spec": {k: spec[k] for k in ("max_real_part", "min_damping_ratio_oscillatory", "n_with_abs_real_part_below_1e-9")}, "symmetry": out["symmetry"], "lyap_sc": ly_sc, "lyap_nat": ly_nat,
                      "smooth": out["smoothness_domain"]["nearest_switch_by_P_norm"], "robust": rob, "pss_effect": out["effect_of_PSS_on_spectrum"]}, indent=1, default=float)[:6000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
