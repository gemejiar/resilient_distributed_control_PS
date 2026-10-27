"""DEC-051 block A: exact equilibrium of the full DAE + original RDC (no time stepping).

Unknowns: dynamic states x_d, quasi-algebraic states x_z, algebraic variables y and the 20 references u = [Pset, Qset].  Equations: f_d = 0 (x' = 0), f_z = 0, g = 0, and the 20 RDC rates v_RDC(u, P, Q, V, omega) = 0,
with the E8 actuator maps theta(u, y) evaluated exactly (no frozen references).  Common rotor-angle symmetry: the DAE is invariant to a common shift of all rotor angles, so the right object is a RELATIVE equilibrium: all angle rates equal one common value c = Omega_b (omega_s - 1) (the
synchronous speed offset, a result of the solve) and every other rate is zero.  The residual is therefore the quotient residual F_q = F - v_null F_c (c = SG31 angle), and the explicit condition
 delta_SG31 = its 1999 s value removes the shift of the solution.
Method: outer damped Newton on (x_d, u) with the reduced Jacobian M of the closed loop (ANDES analytic Jacobians; parameter derivatives by finite differences, as in E9/DEC-050), the inner Newton re-solves
(x_z, y) from g = 0 at every outer iterate (so the algebraic constraints and the maps theta(u, y) hold at every iterate); backtracking line search on the infinity norm of [x_d'; v_RDC].
Start: the full ANDES state stored at t = 1999 s by run_dec051_state_dump.py.  Starts perturbed by 1e-3 relative are re-solved to test local uniqueness and tolerance sensitivity.
Independent validation (A2) re-evaluates every equation with fresh calls and checks balances, limits, discrete-limiter flags, clamp and regularity."""

from __future__ import annotations

import csv
import json

import numpy as np

import dec051_core as C
import e9h_predictor as PR
import run_e8_ieee39 as e8
from run_e0_ieee39 import ARTIFACTS_DIR as A, git_commit, sha256

NAMES = ["SG30", "SG31", "SG33", "SG35", "SG38", "SG39", "GFM32", "GFM37", "GFM34", "GFM36"]


def outputs(system, st):
    y = system.dae.y
    return (np.asarray(y[st["a_p"]], float), np.asarray(y[st["a_q"]], float), np.asarray(y[st["a_v"]], float), np.asarray(y[st["a_f"]], float))


def rates(system, ctx, st, u):
    p, q, v, om = outputs(system, st)
    return C.rdc_rates(st, ctx, u[:10], u[10:], p, q, v, om)


def prepare(dump):
    system, ctx = C.build_system("S0")
    st = C.rdc_state(system, ctx, dump)
    C.load_dump_into(system, dump)
    C.set_state(system, dump["x"], dump["y"])
    ix = C.index_sets(system)
    names = list(system.dae.x_name)
    gen_idx = list(system.GENROU.idx.v)
    sg31 = gen_idx[[int(b) for b in system.GENROU.bus.v].index(31)]
    pin = names.index("delta " + str(sg31).replace("_", " "))
    return system, ctx, st, ix, pin


def residual_vec(system, ctx, st, ix, u):
    f0, g0 = C.fg_all(system)
    d_idx = ix["d_idx"]
    return np.concatenate([f0[d_idx] / ix["tf"][d_idx], rates(system, ctx, st, u)]), f0, g0


def newton(system, ctx, st, ix, pin, x_start, y_start, u_start, tol=1e-11, itmax=25, verbose=True, vnull=None):
    d_idx = ix["d_idx"]
    pin_pos = int(np.where(d_idx == pin)[0][0])
    pred = PR.LinearPredictor(ctx)
    pred.lim = ctx["lim"]
    C.set_state(system, x_start, y_start)
    u = u_start.copy()
    if vnull is None:
        vnull = angle_null(system, ctx, st, ix, pred, u, pin_pos)
    x_ref = float(x_start[pin])
    hist = []
    cache = pred.cache
    C.apply_params(system, ctx, st, u)
    for it in range(itmax):
        info = C.inner_solve(system, ctx, st, u, ix, cache if "fp" in cache else _init_cache(system, ctx, st, pred, u), tol=1e-13)
        F0, f0, g0 = residual_vec(system, ctx, st, ix, u)
        F = quotient(F0, vnull, pin_pos)
        nrm = float(np.abs(F).max())
        hist.append({"iter": it, "norm_inf_F": nrm, "common_angle_rate_c": float(F0[pin_pos]), "norm_xdot_quotient": float(np.abs(F[:len(d_idx) - 1]).max()), "norm_vrdc": float(np.abs(F[len(d_idx) - 1:]).max()), "inner_iterations": info["iterations"],
                     "inner_residual": info["residual_history"][-1], "g_inf": float(np.abs(g0).max())})
        if verbose:
            print(hist[-1], flush=True)
        if nrm < tol:
            break
        p, q, v, om = outputs(system, st)
        vn = rates(system, ctx, st, u)
        pb = pred.build(system, st, vn[:10], vn[10:], 1999.0, refresh_params=True)
        M = pb["M"]
        n = len(d_idx)
        Qm = quotient_matrix(vnull, pin_pos)
        aug = np.vstack([Qm @ M, np.eye(M.shape[0])[pin_pos][None, :]])
        rhs = np.concatenate([-F, [0.0]])
        step = np.linalg.lstsq(aug, rhs, rcond=1e-13)[0]
        # backtracking on ||F||_inf
        x_old, y_old, u_old = np.array(system.dae.x), np.array(system.dae.y), u.copy()
        lam = 1.0
        while True:
            system.dae.x[:] = x_old
            system.dae.y[:] = y_old
            system.dae.x[d_idx] += lam * step[:n]
            u = u_old + lam * step[n:]
            system.vars_to_models()
            C.inner_solve(system, ctx, st, u, ix, pred.cache, tol=1e-13)
            Fn, _, _ = residual_vec(system, ctx, st, ix, u)
            Fn = quotient(Fn, vnull, pin_pos)
            if np.abs(Fn).max() < nrm or lam < 1e-4:
                break
            lam *= 0.5
        hist[-1]["step_length"] = lam
        hist[-1]["rank_deficit_of_[QM; pin]"] = int(M.shape[0] - np.linalg.matrix_rank(aug, tol=1e-9))
    return np.array(system.dae.x), np.array(system.dae.y), u, hist, pred, vnull


def angle_null(system, ctx, st, ix, pred, u, pin_pos):
    """Right null vector of the closed-loop Jacobian (common rotor-angle shift), normalised to 1 at the SG31 angle; entries below 1e-6 are set to 0 (structural zeros)."""
    vn = rates(system, ctx, st, u)
    M = pred.build(system, st, vn[:10], vn[10:], 1999.0, refresh_params=True)["M"]
    _, sv, vt = np.linalg.svd(M)
    v = vt[-1] / vt[-1][pin_pos]
    v[np.abs(v) < 1e-6] = 0.0
    return v


def quotient_matrix(vnull, c):
    n = len(vnull)
    Q = np.eye(n) - np.outer(vnull, np.eye(n)[c])
    return np.delete(Q, c, axis=0)


def quotient(F, vnull, c):
    return np.delete(F - vnull * F[c], c)


def _init_cache(system, ctx, st, pred, u):
    C.apply_params(system, ctx, st, u)
    import e9a_linear as L
    L.linearize(system, ctx, cache=pred.cache)
    return pred.cache


def main() -> int:
    dump = dict(np.load(A / "IEEE39_DEC051_state_t1999.npz"))
    system, ctx, st, ix, pin = prepare(dump)
    u0 = np.concatenate([dump["st_pset"], dump["st_qset"]])
    # consistency of the RDC replica with the stored run at the dumped state
    C.apply_params(system, ctx, st, u0)
    vrep = rates(system, ctx, st, u0)
    vdump = np.concatenate([dump["vnom_p"], dump["vnom_q"]])
    rep = float(np.abs(vrep - vdump).max())
    x, y, u, hist, pred, vnull = newton(system, ctx, st, ix, pin, dump["x"], dump["y"], u0)
    converged = hist[-1]["norm_inf_F"] < 1e-8      # declared target (DEC-051): normalised residual of order 1e-8; the reached value is reported
    # local uniqueness / tolerance sensitivity: re-solve from perturbed starts
    rng = np.random.default_rng(11)
    sens = []
    for k in range(2):
        xs = x * (1 + 1e-3 * rng.standard_normal(x.shape)) if False else x + 1e-3 * rng.standard_normal(x.shape) * np.maximum(np.abs(x), 1e-3)
        xs[pin] = x[pin]
        us = u * (1 + 1e-3 * rng.standard_normal(u.shape))
        x2, y2, u2, h2, _, _ = newton(system, ctx, st, ix, pin, xs, y, us, verbose=False, vnull=vnull)
        sens.append({"start_perturbation": "1e-3 relative on x and u", "final_norm_inf_F": h2[-1]["norm_inf_F"], "iterations": len(h2), "max_abs_dx_vs_root": float(np.abs(x2[ix["d_idx"]] - x[ix["d_idx"]]).max()), "max_abs_du_vs_root": float(np.abs(u2 - u).max())})
    # restore the root in the system for validation
    C.set_state(system, x, y)
    C.inner_solve(system, ctx, st, u, ix, pred.cache, tol=1e-13)
    np.savez_compressed(A / "IEEE39_DEC051_equilibrium_state.npz", x=np.array(system.dae.x), y=np.array(system.dae.y), u=u, pin=pin, **{"PQ_" + k: np.array(getattr(system.PQ, k).v) for k in C.PQ_PARAMS})
    out = {"stage": "DEC-051 A", "git_commit": git_commit(), "doc": __doc__, "rdc_replica_vs_stored_rates_max_abs": rep, "newton_history": hist, "converged_declared_1e-8": converged, "reached_below_1e-11": bool(hist[-1]["norm_inf_F"] < 1e-11), "sensitivity_starts": sens,
           "distance_to_1999s_point": {"max_abs_dx_dynamic": float(np.abs(system.dae.x[ix["d_idx"]] - dump["x"][ix["d_idx"]]).max()), "max_abs_du": float(np.abs(u - u0).max()), "max_abs_dy": float(np.abs(system.dae.y - dump["y"]).max())},
           "reproducibility_u_diff_vs_DEC050": float(dump["reproducibility_max_abs_u_diff_vs_DEC050"])}
    # ---------------- A2 independent validation
    d_idx, z_idx = ix["d_idx"], ix["z_idx"]
    f0, g0 = C.fg_all(system)
    tf = ix["tf"]
    p, q, v, om = outputs(system, st)
    vb = np.asarray(system.dae.y[np.asarray(system.Bus.v.a)], float)
    lim = ctx["lim"]
    s = np.hypot(p, q)
    z_raw = e8.KAPPA_SG * (u[10:] - st["qn"])[:ctx["n_sg"]]
    gp, gq = e8.capability_factors(u[:10], u[10:], lim)
    pl = float(np.sum(system.PQ.Ppf.v)); ql = float(np.sum(system.PQ.Qpf.v))
    import select_equilibrium_b3 as b3
    ybus = system.build_ybus()
    import scipy.sparse as sp
    Y = sp.coo_matrix((list(ybus.V), (list(ybus.I), list(ybus.J))), shape=ybus.size).toarray()
    bus_ids = [int(b) for b in system.Bus.idx.v]
    ang = np.asarray(system.dae.y[np.asarray(system.Bus.a.a)], float)
    vc = vb * np.exp(1j * ang)
    sinj = vc * np.conj(Y @ vc)
    loss_p = float(sinj.real.sum())
    a2 = {"residual_f_dynamic_raw_inf": float(np.abs(f0[d_idx]).max()), "residual_xdot_inf": float(np.abs(f0[d_idx] / tf[d_idx]).max()), "residual_f_quasi_algebraic_inf": float(np.abs(f0[z_idx]).max()) if len(z_idx) else 0.0,
          "residual_g_inf": float(np.abs(g0).max()), "rdc_rates_inf": float(np.abs(rates(system, ctx, st, u)).max()),
          "rdc_rates_by_unit_P": rates(system, ctx, st, u)[:10].tolist(), "rdc_rates_by_unit_Q": rates(system, ctx, st, u)[10:].tolist(),
          "balance": {"sum_P_units_pu": float(p.sum()), "sum_P_constant_power_loads_pu": pl, "network_loss_pu_from_Ybus": loss_p, "residual_P_pu": float(p.sum() - pl - loss_p), "sum_Q_units_pu": float(q.sum()), "sum_Q_loads_pu": ql},
          "units": {n: {"P_pu": float(p[i]), "Q_pu": float(q[i]), "S_pu": float(s[i]), "V_pu": float(v[i]), "P_margin_to_pmax": float(lim["pmax"][i] - p[i]), "Q_margin_to_qmax": float(lim["qmax"][i] - q[i]), "Q_margin_to_qmin": float(q[i] - lim["qmin"][i]),
                        "S_margin_pu": float(lim["smax"][i] - s[i]), "Pset_minus_Pn": float(u[i] - st["pn"][i]), "Qset_minus_Qn": float(u[10 + i] - st["qn"][i]), "g_P_raw": float(gp[i]), "g_Q_raw": float(gq[i])} for i, n in enumerate(NAMES)},
          "bus_voltage_min_max_pu": [float(vb.min()), float(vb.max())], "bus_voltages_pu": vb.tolist(), "n_buses_outside_0.95_1.05": int(((vb < 0.95) | (vb > 1.05)).sum()),
          "frequency_deviation_hz": float((om.mean() - 1.0) * 60.0), "omega_unit_spread": float(om.max() - om.min()),
          "sg_z_clamp_margin": float(e8.Z_CLAMP - np.abs(z_raw).max()), "z_raw": z_raw.tolist(), "min_capability_factors_raw": [float(gp.min()), float(gq.min())]}
    # discrete limiter flags
    flags = {}
    try:
        system.l_update_var(system.exist.pflow_tds, niter=0, err=0.0) if False else None
    except Exception:
        pass
    for mn, m in system.models.items():
        if m.n == 0:
            continue
        for dn, dobj in m.discrete.items():
            if hasattr(dobj, "zu") and hasattr(dobj, "zl"):
                flags[f"{mn}.{dn}"] = {"active_upper": int((np.asarray(dobj.zu) == 1).sum()), "active_lower": int((np.asarray(dobj.zl) == 1).sum())}
    a2["limiter_flags_stored"] = flags
    # regularity of the algebraic block
    lin = C.L.linearize(system, ctx, cache=pred.cache)
    a2["regularity"] = {"extended_algebraic_block_min_singular_value": lin["gy_min_sv"], "extended_algebraic_block_cond": lin["gy_cond"], "gy_only_cond": lin["gy_only_cond"], "n_dynamic": lin["n_dynamic"], "n_quasi_algebraic": lin["n_quasi_algebraic"],
                        "n_forced_PSS_states_eliminated": lin["n_dropped_IEEEST_states"]}
    # IEEEST states: are they frozen in the stored trajectory?  compare with the pre-event initial values
    pin_pos = int(np.where(ix["d_idx"] == pin)[0][0])
    F0, _, _ = residual_vec(system, ctx, st, ix, u)
    Fq = quotient(F0, vnull, pin_pos)
    a2["quotient"] = {"norm_inf_quotient_residual": float(np.abs(Fq).max()), "common_angle_rate_rad_per_s": float(F0[pin_pos]), "implied_synchronous_frequency_offset_hz": float(F0[pin_pos] / (2 * np.pi)),
                      "n_angle_states_in_null_vector": int((vnull[:len(ix["d_idx"])] != 0).sum()), "n_nonzero_entries_in_null_vector_total": int((vnull != 0).sum()),
                      "angle_rates_spread_after_removing_common_rate": float(np.abs(Fq).max())}
    # PSS: genuine states kept (LL2_x, WO_x); the forced ones eliminated and checked consistent
    ynames = list(system.dae.y_name)
    pss = ix["pss"]
    a2["PSS"] = {"forced_state_rows_f_inf": float(np.abs(f0[ix["junk_x"]]).max()), "forced_algebraic_rows_g_inf": float(np.abs(g0[ix["junk_y"]]).max()),
                 "vsout_by_SG": [float(system.dae.y[d["y_vsout"]]) for d in pss.values()], "WO_x_plus_2_LL2_x_max_abs": float(max(abs(system.dae.x[d["WO_x"]] + 2 * system.dae.x[d["LL2_x"]]) for d in pss.values())),
                 "LL2_x_minus_sig_max_abs": float(max(abs(system.dae.x[d["LL2_x"]] - system.dae.y[d["y_sig"]]) for d in pss.values())), "n_genuine_PSS_states_kept": 2 * len(pss),
                 "note": "PSS active: washout of the lagged electrical power, DC gain zero -> vsout = 0 at a relative equilibrium"}
    out["A2"] = a2
    out["tolerance"] = {"declared_target_normalized_residual": 1e-8, "reached_norm_inf_F_quotient": hist[-1]["norm_inf_F"], "reached_g_inf": a2["residual_g_inf"], "reached_rdc_rates_inf": a2["rdc_rates_inf"]}
    out["GATE_A"] = "EQUILIBRIUM_EXACT" if (converged and a2["residual_g_inf"] < 1e-8 and a2["rdc_rates_inf"] < 1e-8 and a2["quotient"]["norm_inf_quotient_residual"] < 1e-8 and a2["regularity"]["extended_algebraic_block_min_singular_value"] > 1e-8) else "EQUILIBRIUM_APPROXIMATE"
    (A / "IEEE39_DEC051_equilibrium.json").write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
    with (A / "IEEE39_DEC051_equilibrium.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["unit", "P_pu", "Q_pu", "S_pu", "V_pu", "Pset_minus_Pn_pu", "Qset_minus_Qn_pu", "P_margin_to_pmax_pu", "Q_margin_to_qmax_pu", "S_margin_pu", "g_P_raw", "g_Q_raw", "vrdc_P", "vrdc_Q"])
        for i, n in enumerate(NAMES):
            r = a2["units"][n]
            w.writerow([n, r["P_pu"], r["Q_pu"], r["S_pu"], r["V_pu"], r["Pset_minus_Pn"], r["Qset_minus_Qn"], r["P_margin_to_pmax"], r["Q_margin_to_qmax"], r["S_margin_pu"], r["g_P_raw"], r["g_Q_raw"], a2["rdc_rates_by_unit_P"][i], a2["rdc_rates_by_unit_Q"][i]])
    print(json.dumps({"GATE_A": out["GATE_A"], "tolerance": out["tolerance"], "distance": out["distance_to_1999s_point"], "rep": rep, "sens": sens, "balance": a2["balance"], "regularity": a2["regularity"],
                      "PSS": a2["PSS"]}, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
