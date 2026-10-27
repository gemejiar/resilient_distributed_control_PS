"""DEC-052 block A: structural audit of the DEC-051 reduced model (PSS elimination, angular symmetry, algebraic regularity, fidelity to the simulated DAE-RDC).  Static evaluation only; no TDS run.
Output: IEEE39_DEC052_model_audit.json."""
from __future__ import annotations

import json

import numpy as np
import scipy.linalg as sl
import sympy as sp

import dec052_common as K
import dec051_core as C
import e9a_linear as L
import run_dec051_equilibrium as EQ
import run_dec051_h4 as H4
from run_e0_ieee39 import ARTIFACTS_DIR as A


def pss_symbolic(system) -> dict:
    """Substitute the ANDES parameters (A1..A6 = T1 = T2 = T3 = 0, F2/LL1 zero-time-constant flags = 1) into the ANDES equations of the degenerate IEEEST variables and solve the constraint chain."""
    m = system.IEEEST
    par = {p: sorted(set(np.asarray(getattr(m, p).v).tolist())) for p in ("A1", "A2", "A3", "A4", "A5", "A6", "T1", "T2", "T3", "T4", "T5", "T6", "KS")}
    flags = {f"{b}_LT_z{k}": sorted(set(np.asarray(getattr(getattr(m, b).LT, f"z{k}")).tolist())) for b in ("F2", "LL1", "LL2", "WO") for k in (0, 1)}
    names = ["sig", "F1_x", "F1_y", "F2_x1", "F2_x2", "F2_y", "LL1_x", "LL1_y", "LL2_x", "LL2_y", "A1", "A2", "A3", "A4", "A5", "A6", "T1", "T2", "T3", "T4", "F2_LT_z1", "LL1_LT_z1", "LL2_LT_z1", "LL2_LT_z0"]
    S = {n: sp.Symbol(n) for n in names}
    zero = {S[k]: 0 for k in ("A1", "A2", "A3", "A4", "A5", "A6", "T1", "T2", "T3")}
    zero.update({S["F2_LT_z1"]: 1, S["LL1_LT_z1"]: 1, S["LL2_LT_z1"]: 0, S["LL2_LT_z0"]: 1, S["T4"]: sp.Rational(3, 4)})
    es = {}
    for d in (m.states, m.algebs):
        for k, v in d.items():
            if k in ("F1_x", "F2_x1", "LL1_x", "F2_y", "LL1_y", "LL2_x", "LL2_y"):
                es[k] = sp.sympify(str(v.e_str), locals=S)
    cons = {k: sp.simplify(es[k].subs(zero)) for k in ("F1_x", "F2_x1", "LL1_x", "F2_y", "LL1_y")}
    sol = sp.solve(list(cons.values()), [S["F1_y"], S["F2_x2"], S["F2_y"], S["LL1_x"], S["LL1_y"]], dict=True)[0]
    ll2x = sp.simplify(es["LL2_x"].subs(zero).subs(sol))
    ll2y = sp.simplify(es["LL2_y"].subs(zero))
    return {"andes_parameters": par, "lead_lag_flags": flags, "equations_after_substitution": {k: str(v) for k, v in cons.items()}, "solution_of_constraint_chain": {str(k): str(v) for k, v in sol.items()},
            "LL2_x_equation_after_elimination": str(ll2x), "LL2_y_equation_after_substitution": str(ll2y),
            "differential_consequences": "F1_y' = F1_x and F2_x2' = F2_x1 are differentiated copies of F1_y = sig and F2_x2 = F1_y (index-2 structure of the ANDES formulation); F1_x, F2_x1 feed no retained equation",
            "all_constraints_resolve_to_sig": bool(all(sp.simplify(v - S["sig"]) == 0 for v in sol.values())),
            "LL2_x_is_lag_of_sig_with_T4": bool(sp.simplify(ll2x - (S["sig"] - S["LL2_x"])) == 0), "LL2_x_note": "ANDES e_str is the numerator: T4 * LL2_x' = sig - LL2_x with T4 = 0.75 s"}


def main() -> int:
    eq, system, ctx, st, ix, pred, u = H4.load_eq()
    d_idx = ix["d_idx"]
    n = len(d_idx)
    N = n + 20
    pin_pos = int(np.where(d_idx == int(eq["pin"]))[0][0])
    out: dict = {"stage": "DEC-052 block A (model audit)", "git_commit": K.git_commit(), "software": K.env(),
                 "inputs_sha256": {f: K.sha(A / f) for f in ("IEEE39_DEC051_equilibrium_state.npz", "IEEE39_DEC051_H4_matrices.npz", "IEEE39_DEC051_equilibrium.json")}}
    xn, yn = list(system.dae.x_name), list(system.dae.y_name)
    # ------------------------------------------------------------------ A1
    pss = ix["pss"]
    pos_in_reduced = {int(a): int(k) for k, a in enumerate(d_idx)}
    rows = []
    for unit, d in pss.items():
        for k in C.JUNK_X:
            rows.append({"unit": unit, "andes_name": xn[d[k]], "andes_address": int(d[k]), "role": "eliminated (forced identity)", "reduced_index": None})
        for k in ("LL2_x", "WO_x"):
            rows.append({"unit": unit, "andes_name": xn[d[k]], "andes_address": int(d[k]), "role": "kept (genuine PSS state)", "reduced_index": pos_in_reduced[int(d[k])]})
        for k in C.JUNK_Y:
            rows.append({"unit": unit, "andes_name": yn[d["y_" + k]], "andes_address": int(d["y_" + k]), "role": "eliminated algebraic (forced identity)", "reduced_index": None})
    sym = pss_symbolic(system)
    lin0 = C._orig_linearize(system, ctx, cache=pred.cache)
    raw = lin0["raw"]
    jx, jy, kx, ky = ix["junk_x"], ix["junk_y"], ix["keep_x"], ix["keep_y"]
    nzdep = []
    for nm, M, rr, cc, rn, cn in (("fx[keep_x, junk_x]", raw["fx"][np.ix_(kx, jx)], kx, jx, xn, xn), ("fy[keep_x, junk_y]", raw["fy"][np.ix_(kx, jy)], kx, jy, xn, yn),
                                  ("gx[keep_y, junk_x]", raw["gx"][np.ix_(ky, jx)], ky, jx, yn, xn), ("gy[keep_y, junk_y]", raw["gy"][np.ix_(ky, jy)], ky, jy, yn, yn)):
        for i, j in zip(*np.nonzero(np.abs(M) > 0)):
            nzdep.append({"block": nm, "row": rn[rr[i]], "col": cn[cc[j]], "value": float(M[i, j])})
    x_eq, y_eq = np.array(eq["x"]), np.array(eq["y"])
    C.set_state(system, x_eq, y_eq)
    C.inner_solve(system, ctx, st, u, ix, pred.cache, tol=1e-13)
    f0, g0 = C.fg_all(system)
    forced = []
    for d in pss.values():
        forced += [f0[d["F1_x"]], f0[d["F2_x1"]], f0[d["LL1_x"]], g0[d["y_F2_y"]], g0[d["y_LL1_y"]], f0[d["F1_y"]], f0[d["F2_x2"]]]
    rng = np.random.default_rng(52)
    off = []
    for _ in range(3):
        xx = x_eq.copy(); xx[d_idx] += 1e-2 * rng.standard_normal(n) * np.maximum(np.abs(xx[d_idx]), 0.1)
        C.set_state(system, xx, y_eq)
        C.inner_solve(system, ctx, st, u, ix, pred.cache, tol=1e-12)
        f1, g1 = C.fg_all(system)
        off.append(float(max(max(abs(f1[d[k]]) for d in pss.values() for k in ("F1_x", "F2_x1", "LL1_x")), max(abs(g1[d["y_" + k]]) for d in pss.values() for k in C.JUNK_Y))))
    C.set_state(system, x_eq, y_eq)
    C.inner_solve(system, ctx, st, u, ix, pred.cache, tol=1e-13)
    conn = {}
    try:
        vso = system.IEEEST.vsout
        conn.update({"vsout_class": type(vso).__name__, "vsout_e_str": str(vso.e_str), "vsout_target": f"{getattr(vso, 'src', '?')} of {getattr(vso, 'model', '?')}"})
    except Exception as exc:                         # pragma: no cover
        conn["vsout_error"] = repr(exc)
    jac_rows = {}
    for unit, d in pss.items():
        c = d["y_vsout"]
        rr = [(yn[i], float(raw["gy"][i, c])) for i in range(raw["gy"].shape[0]) if raw["gy"][i, c] != 0 and i != c]
        rx = [(xn[i], float(raw["fy"][i, c])) for i in range(raw["fy"].shape[0]) if raw["fy"][i, c] != 0]
        cs = d["y_sig"]
        srcs = [(yn[j], float(raw["gy"][cs, j])) for j in range(raw["gy"].shape[1]) if raw["gy"][cs, j] != 0 and j != cs] + [(xn[j], float(raw["gx"][cs, j])) for j in range(raw["gx"].shape[1]) if raw["gx"][cs, j] != 0]
        jac_rows[unit] = {"vsout_enters_algebraic_equations": rr, "vsout_enters_state_equations": rx, "sig_depends_on": srcs}
    conn["jacobian_connectivity_per_PSS_unit"] = jac_rows
    conn.update({"sig_equation": str(system.IEEEST.algebs["sig"].e_str), "MODE": sorted(set(np.asarray(system.IEEEST.MODE.v).tolist())), "host_generators": [str(g) for g in system.IEEEST.syn.v],
                 "host_exciters": [str(g) for g in system.IEEEST.avr.v], "input": "MODE 3: electrical power te/(Sn/Sb) of the host generator"})
    out["A1"] = {"table_andes_to_reduced": rows, "symbolic_elimination": sym, "nonzero_dependence_of_retained_equations_on_eliminated_variables": nzdep,
                 "residual_of_forced_rows_at_equilibrium_max_abs": float(np.max(np.abs(forced))), "constraint_residual_off_equilibrium_3_random_perturbations_1e-2": off, "connections": conn,
                 "kept_dynamic_pss_states_in_reduced_model": int(sum(r["reduced_index"] is not None for r in rows)), "eliminated_states": int(len(jx)), "eliminated_algebraics": int(len(jy)),
                 "dimensions": {"ANDES_states": int(len(xn)), "ANDES_algebraics": int(system.dae.m), "reduced_dynamic": n, "references": 20, "total_N": N, "quasi_algebraic_states_kept": int(len(ix["z_idx"])), "algebraic_variables_kept": int(len(ky))},
                 "criterion_A1": "equivalence of retained and eliminated equations on the constraint manifold: the symbolic chain resolves to sig, retained equations see the eliminated variables only through LL2_x <- LL1_y (= sig), forced rows have zero numerical residual",
                 "limit": "valid on the constraint manifold for smooth trajectories; at an algebraic jump of sig the ANDES integrator produces a non-physical impulse in F1_x/F2_x1 that feeds no retained equation"}
    # ------------------------------------------------------------------ A2
    vnull = EQ.angle_null(system, ctx, st, ix, pred, u, pin_pos)
    Qm = EQ.quotient_matrix(vnull, pin_pos)
    S = np.delete(np.eye(N), pin_pos, axis=1)
    mt = np.load(A / "IEEE39_DEC051_H4_matrices.npz")
    Aq = mt["Aq"]
    ang_y = np.asarray(system.Bus.a.a, int)
    inv = []
    for trial in range(3):
        xx, yy = x_eq.copy(), y_eq.copy()
        if trial:
            xx[d_idx] += 1e-2 * rng.standard_normal(n) * np.maximum(np.abs(xx[d_idx]), 0.1)
            C.set_state(system, xx, yy); C.inner_solve(system, ctx, st, u, ix, pred.cache, tol=1e-12); xx, yy = np.array(system.dae.x), np.array(system.dae.y)
        C.set_state(system, xx, yy); fa, ga = C.fg_all(system)
        s = 0.5
        x2, y2 = xx.copy(), yy.copy(); x2[d_idx] += s * vnull[:n]; y2[ang_y] += s
        C.set_state(system, x2, y2); fb, gb = C.fg_all(system)
        gd = np.abs(gb - ga)
        inv.append({"trial": trial, "shift_rad": s, "max_abs_diff_f": float(np.abs(fb - fa).max()), "max_abs_diff_g": float(gd.max()), "worst_g_row": str(yn[int(gd.argmax())])})
    C.set_state(system, x_eq, y_eq)
    angle_names = [xn[d_idx[k]] for k in np.where(vnull[:n] != 0)[0]]
    kinds = sorted({" ".join(a.split()[:2]) for a in angle_names})
    T = np.column_stack([S, vnull])
    Jn = H4.numerical_jacobian(system, ctx, st, ix, pred, eq, u, 1e-6, 1e-5)
    Tinv = np.vstack([Qm, np.eye(N)[pin_pos][None, :]])
    B = Tinv @ Jn @ T
    blocks = {"norm_M_v": float(np.linalg.norm(Jn @ vnull)), "relative_norm_M_v_over_norm_M": float(np.linalg.norm(Jn @ vnull) / np.linalg.norm(Jn)), "abs_lower_right_cell": float(abs(B[-1, -1])),
              "norm_upper_right_cell_Qm_M_v": float(np.linalg.norm(B[:-1, -1])), "norm_(upper_left - Aq_DEC051)_relative": float(np.linalg.norm(B[:-1, :-1] - Aq) / np.linalg.norm(Aq))}
    evM, evA = np.linalg.eigvals(Jn), np.linalg.eigvals(Aq)
    rest = np.delete(evM, int(np.argmin(np.abs(evM))))
    pres = float(max(np.abs(evA[:, None] - rest[None, :]).min(axis=1).max(), np.abs(rest[:, None] - evA[None, :]).min(axis=1).max()))
    out["A2"] = {"angle_like_states_in_null_vector": int((vnull != 0).sum()), "kinds": kinds, "bus_angle_variables_shifted": int(len(ang_y)), "nonlinear_invariance_under_common_shift": inv,
                 "projection": "S = I with column pin removed (embedding, SG31 angle = 0); Qm = I - v e_pin^T with row pin removed; reconstruction xi = S e + xi_pin v; Qm S = I", "Qm_S_identity_error": float(np.abs(Qm @ S - np.eye(N - 1)).max()),
                 "cond_of_change_of_basis_[S v]": float(np.linalg.cond(T)), "vnull_unique_nonzero_values": sorted(set(np.round(vnull[vnull != 0], 10).tolist())), "block_triangular_structure_of_M_in_basis_[S v]": blocks,
                 "eig(M) minus the zero eigenvalue vs eig(Aq): max matching distance": pres,
                 "relative_equilibrium": {"common_angle_rate_rad_per_s": json.loads((A / "IEEE39_DEC051_equilibrium.json").read_text(encoding="utf-8"))["A2"]["quotient"]["common_angle_rate_rad_per_s"],
                                          "quotient_residual": json.loads((A / "IEEE39_DEC051_equilibrium.json").read_text(encoding="utf-8"))["A2"]["quotient"]["norm_inf_quotient_residual"]},
                 "structural_argument": "the DAE depends on rotor/PLL angles and bus angles only through angle differences, so F(x + a v, y + a w, u) = F(x, y, u) for the exact vector field (verified above to roundoff at the equilibrium and at two perturbed points), hence M v = 0 and, in the basis [S v], M = [[Aq, 0],[*, 0]] with eig(M) = eig(Aq) U {0}. The quotient field e' = Qm F(S e + a v) is independent of a: the reduction removes exactly one direction and no physical mode; a relative equilibrium has F = c v with c != 0 allowed."}
    # ------------------------------------------------------------------ A3
    lin = L.linearize(system, ctx, cache=pred.cache)
    rw = lin["raw"]
    zi = rw["z_idx"]
    Kmat = np.block([[rw["fx"][np.ix_(zi, zi)], rw["fy"][zi]], [rw["gx"][:, zi], rw["gy"]]])
    sv = np.linalg.svd(Kmat, compute_uv=False)
    Dr, Dc = np.ones(Kmat.shape[0]), np.ones(Kmat.shape[1]); Ks = Kmat.copy()
    for _ in range(30):
        r = np.sqrt(np.abs(Ks).max(axis=1)); c = np.sqrt(np.abs(Ks).max(axis=0)); r[r == 0] = 1; c[c == 0] = 1
        Ks = Ks / r[:, None] / c[None, :]; Dr *= r; Dc *= c
    svs = np.linalg.svd(Ks, compute_uv=False)
    R = np.linalg.inv(Kmat)
    nK = Kmat.shape[0]
    rump = float(np.abs(np.eye(nK) - R @ Kmat).sum(axis=1).max() + (K.gamma(nK + 2) * (np.abs(R) @ np.abs(Kmat))).sum(axis=1).max())
    Zf = np.where(raw["tf"] == 0)[0]
    Kfull = np.block([[raw["fx"][np.ix_(Zf, Zf)], raw["fy"][Zf]], [raw["gx"][:, Zf], raw["gy"]]])
    svf = np.linalg.svd(Kfull, compute_uv=False)
    out["A3"] = {"structure": "DAE x' = f(x,y,u), 0 = g(x,y,u); quasi-algebraic states (Tf = 0) are appended to the algebraic block", "block_dimension": int(nK), "n_quasi_algebraic_states": int(len(zi)), "n_algebraic_variables": int(rw["gy"].shape[0]),
                 "norm_2": float(sv[0]), "norm_inf": float(np.abs(Kmat).sum(axis=1).max()), "min_singular_value": float(sv[-1]), "condition_number_2": float(sv[0] / sv[-1]),
                 "after_Ruiz_equilibration": {"min_singular_value": float(svs[-1]), "condition_number_2": float(svs[0] / svs[-1]), "row_scale_range": [float(Dr.min()), float(Dr.max())], "col_scale_range": [float(Dc.min()), float(Dc.max())]},
                 "validated_nonsingularity_of_the_floating_matrix": {"method": "Rump-type: ||I - R K||_inf + gamma_(n+2) || |R||K| ||_inf < 1 with R = fl(inv(K)); first-order floating-point error bound (Higham), no directed rounding", "bound": rump, "nonsingular": bool(rump < 1)},
                 "algebraic_residual_inf_at_equilibrium": float(max(np.abs(g0).max(), np.abs(f0[ix["z_idx"]]).max())),
                 "unreduced_block_with_eliminated_IEEEST_variables": {"dimension": int(Kfull.shape[0]), "min_singular_value": float(svf[-1]), "n_singular_values_below_1e-12_rel": int((svf < 1e-12 * svf[0]).sum()),
                                                                       "comment": "singular: the ANDES formulation is index-2 on the degenerate IEEEST chain (F1_x does not appear in its own constraint); the elimination yields a regular index-1 block"},
                 "caveat": "a favourable condition number is a diagnostic; the nonsingularity bound is validated for the computed floating matrix, not for the exact Jacobian of the nonlinear equations"}
    # ------------------------------------------------------------------ PSS influence and trajectory-level fidelity
    ev, Vr = np.linalg.eig(Aq)
    Wl = np.linalg.inv(Vr)
    part = np.abs(Vr * Wl.T); part = part / part.sum(axis=0, keepdims=True)
    keep_pos = np.array([k for k in range(N) if k != pin_pos])
    pss_xi = np.array([pos_in_reduced[int(d[k])] for d in pss.values() for k in ("LL2_x", "WO_x")])
    pss_q = np.array([int(np.where(keep_pos == p)[0][0]) for p in pss_xi])
    ppss = part[pss_q].sum(axis=0)
    order = np.argsort(-ev.real)
    near = lambda lam: ev[np.argmin(np.abs(ev - lam))]
    out["PSS_influence"] = {"modes_with_PSS_participation_above_0.2": int((ppss > 0.2).sum()), "max_PSS_participation": float(ppss.max()),
                            "slowest_8_modes": [{"tau_s": float(-1 / ev[i].real), "PSS_participation": float(ppss[i])} for i in order[:8]],
                            "nearest_eigenvalue_to_-1/T4": {"nominal": -1 / 0.75, "re": float(near(-1 / 0.75).real), "im": float(near(-1 / 0.75).imag)}, "nearest_eigenvalue_to_-1/T6": {"nominal": -1 / 4.2, "re": float(near(-1 / 4.2).real), "im": float(near(-1 / 4.2).imag)},
                            "reference": "IEEE39_DEC051_H4_summary.json effect_of_PSS_on_spectrum compares with the E9-A linearisation that drops the PSS"}
    Dsc = np.diag(mt["D"])
    fid = {}
    for tag in ("plus", "minus"):
        f = A / f"IEEE39_DEC051_H4_perturb_{tag}.npz"
        if not f.exists():
            fid[tag] = "series file not present locally"
            continue
        z = dict(np.load(f)); t = z["t"]
        xi = np.hstack([z["x_d"] - z["x_eq_d"][None, :], z["u"] - z["u_eq"][None, :]])
        Eq = (Qm @ xi.T).T
        e0 = Eq[0]; res = []
        for tt in (1.0, 10.0, 50.0, 100.0, 200.0, 400.0, 700.0, 1000.0):
            i = int(np.argmin(np.abs(t - tt)))
            elin = sl.expm(Aq * t[i]) @ e0
            nm = lambda v: float(np.linalg.norm(Dsc @ v))
            res.append({"t_s": float(t[i]), "rel_state_error_scaled_2norm": nm(Eq[i] - elin) / nm(Eq[i]), "rel_error_PSS_states_unscaled": float(np.linalg.norm((Eq[i] - elin)[pss_q]) / max(np.linalg.norm(Eq[i][pss_q]), 1e-300)), "norm_sim_scaled": nm(Eq[i])})
        fid[tag] = res
    out["fidelity_vs_full_TDS_linear_prediction"] = {"note": "full-state comparison of the ANDES time-domain runs (DEC-051 H4, +-0.02 pu along the slowest mode) with expm(Aq t) e(0); nonlinearity and slow-mode dominance included", **fid}
    out["GATE_A"] = decide(out)
    K.dump("IEEE39_DEC052_model_audit.json", out)
    print(json.dumps(out["GATE_A"], indent=1))
    return 0


def decide(o) -> dict:
    a1, a2, a3 = o["A1"], o["A2"], o["A3"]
    c1 = a1["symbolic_elimination"]["all_constraints_resolve_to_sig"] and a1["symbolic_elimination"]["LL2_x_is_lag_of_sig_with_T4"]
    c1b = a1["residual_of_forced_rows_at_equilibrium_max_abs"] < 1e-9 and max(a1["constraint_residual_off_equilibrium_3_random_perturbations_1e-2"]) < 1e-9
    c1c = all(r["col"].startswith("LL1_y") and r["row"].startswith("LL2_x") for r in a1["nonzero_dependence_of_retained_equations_on_eliminated_variables"])
    c2 = max(max(r["max_abs_diff_f"], r["max_abs_diff_g"]) for r in a2["nonlinear_invariance_under_common_shift"]) < 1e-8
    c3 = a3["validated_nonsingularity_of_the_floating_matrix"]["nonsingular"]
    f = o["fidelity_vs_full_TDS_linear_prediction"]
    fe = [r["rel_state_error_scaled_2norm"] for k, v in f.items() if isinstance(v, list) for r in v]
    ok = bool(c1 and c1b and c1c and c2 and c3)
    return {"A1_equivalence_symbolic": bool(c1), "A1_forced_rows_zero_residual": bool(c1b), "A1_only_dependence_is_LL2_x_on_LL1_y": bool(c1c), "A2_symmetry_invariance_to_roundoff": bool(c2), "A3_algebraic_block_nonsingular_validated_for_floating_matrix": bool(c3),
            "fidelity_max_relative_state_error_over_runs_and_times": float(max(fe)) if fe else None, "GATE_A": "PASSED" if ok else "FAILED"}


if __name__ == "__main__":
    raise SystemExit(main())
