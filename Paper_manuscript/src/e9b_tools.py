"""E9-B1 tools: prediction error of the frozen model, derivative check, independent feasibility, conflict analysis and failure classification.

Declared before reading any verdict (DEC-044):
  * failure classification of a barrier in the conflict set of an infeasible QP:
      - "authority": the barrier alone cannot be met within the rate envelope (single-row authority scale s_j > 1, or no authority) while the frozen model predicts
        its value at tau = 0.25 s with a relative error <= 0.5 (relative to max(|h0|, 1e-3));
      - "approximation": the relative prediction error at tau = 0.25 s exceeds 0.5 (the frozen model cannot be trusted for this barrier);
      - "mixed": the single-row authority is within the envelope (s_j <= 1) and the prediction error is moderate, i.e. the conflict comes from the combination.
  * the rate envelope (observed maxima of the original RDC in E8) is an experimental candidate bound, never a hardware limit.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
from scipy.linalg import expm
from scipy.optimize import linprog, minimize

import e9a_linear as L

TAUS = (0.05, 0.1, 0.25, 0.5, 1.0)
SUBSTEP = 1.0 / 256.0
REL_ERR_APPROX = 0.5


def _interp_u(cmd_t: np.ndarray, cmd_p: np.ndarray, cmd_q: np.ndarray, t: float) -> np.ndarray:
    return np.concatenate([[np.interp(t, cmd_t, cmd_p[:, i]) for i in range(cmd_p.shape[1])], [np.interp(t, cmd_t, cmd_q[:, i]) for i in range(cmd_q.shape[1])]])


def predict_outputs(lin: dict[str, Any], rows: dict[str, np.ndarray], y_now: np.ndarray, t0: float, series: dict[str, np.ndarray], taus=TAUS) -> dict[str, Any]:
    """Affine prediction with the frozen Jacobian and the ACTUAL reference history; compare with the stored nonlinear trajectory.

    delta' = A delta + xdot0 + B_u du(t),   y = y0 + Cx delta + Cu du.   Isolates the linearization/algebraic error from the control effect.
    """
    a, bu, cx, cu, xdot = lin["A"], lin["B_u"], lin["Cy_x"], lin["Cy_u"], lin["xdot"]
    n = a.shape[0]
    m = np.zeros((2 * n, 2 * n))
    m[:n, :n], m[:n, n:] = a, np.eye(n)
    e = expm(m * SUBSTEP)
    phi, gam = e[:n, :n], e[:n, n:]
    idx = np.concatenate([rows["P"], rows["Q"], rows["Vbus"]])
    u0 = _interp_u(series["cmd_t"], series["cmd_pset"], series["cmd_qset"], t0)
    delta = np.zeros(n)
    t = series["time_s"]
    p_act = np.hstack([series["sg_p_pu"], series["gfm_p_pu"]])
    q_act = np.hstack([series["sg_q_pu"], series["gfm_q_pu"]])
    v_act = series["bus_voltage_pu"]
    out: dict[str, Any] = {}
    steps = {int(round(tau / SUBSTEP)): tau for tau in taus}
    for k in range(1, max(steps) + 1):
        du = _interp_u(series["cmd_t"], series["cmd_pset"], series["cmd_qset"], t0 + (k - 1) * SUBSTEP) - u0
        delta = phi @ delta + gam @ (xdot + bu @ du)
        if k in steps:
            du_k = _interp_u(series["cmd_t"], series["cmd_pset"], series["cmd_qset"], t0 + k * SUBSTEP) - u0
            y_pred = y_now[idx] + cx[idx] @ delta + cu[idx] @ du_k
            tt = t0 + steps[k]
            pa = np.array([np.interp(tt, t, p_act[:, i]) for i in range(10)])
            qa = np.array([np.interp(tt, t, q_act[:, i]) for i in range(10)])
            va = np.array([np.interp(tt, t, v_act[:, i]) for i in range(v_act.shape[1])])
            out[f"{steps[k]}"] = {"P_pred": y_pred[:10], "Q_pred": y_pred[10:20], "V_pred": y_pred[20:], "P_act": pa, "Q_act": qa, "V_act": va,
                                  "max_abs_err_P": float(np.abs(y_pred[:10] - pa).max()), "max_abs_err_Q": float(np.abs(y_pred[10:20] - qa).max()),
                                  "max_abs_err_V": float(np.abs(y_pred[20:] - va).max())}
    return out


def h_from_outputs(kind: str, unit: int | None, bus: int | None, p, q, v, lim) -> float:
    if kind == "P+":
        return lim["pmax"][unit] - p[unit]
    if kind == "P-":
        return p[unit] - lim["pmin"][unit]
    if kind == "Q+":
        return lim["qmax"][unit] - q[unit]
    if kind == "Q-":
        return q[unit] - lim["qmin"][unit]
    if kind == "S":
        return lim["smax"][unit] ** 2 - p[unit] ** 2 - q[unit] ** 2
    return (1.05 - v[bus]) if kind == "V+" else (v[bus] - 0.95)


def derivative_check(lin: dict[str, Any], rows: dict[str, np.ndarray], t0: float, series: dict[str, np.ndarray], u_dot: np.ndarray, kmax: int = 3, half: int = 5, deg: int = 4) -> dict[str, Any]:
    """Frozen-model output derivatives c A^{k-1} z_dot0 (k = 1..kmax) against local polynomial-fit derivatives of the stored nonlinear series."""
    idx = np.concatenate([rows["P"], rows["Q"], rows["Vbus"]])
    a_z, _, c_z = L.augmented(lin, idx)
    zdot = np.concatenate([lin["xdot"], u_dot])
    t = series["time_s"]
    i0 = int(np.searchsorted(t, t0))
    sl = slice(max(i0 - half, 0), i0 + half + 1)
    tt = t[sl] - t[i0]
    data = np.hstack([series["sg_p_pu"], series["gfm_p_pu"], series["sg_q_pu"], series["gfm_q_pu"], series["bus_voltage_pu"]])[sl]
    vander = np.vander(tt, deg + 1, increasing=True)
    coef, *_ = np.linalg.lstsq(vander, data, rcond=None)
    fact = [1.0, 1.0, 2.0, 6.0, 24.0, 120.0, 720.0]
    res: dict[str, Any] = {}
    cur = c_z.copy()
    for k in range(1, kmax + 1):
        pred = cur @ zdot if k == 1 else (c_z @ np.linalg.matrix_power(a_z, k - 1)) @ zdot
        act = coef[k] * fact[k]
        floor = max(1e-6, 1e-3 * np.abs(act).max())
        rel = np.abs(pred - act) / np.maximum(np.abs(act), floor)
        res[f"order_{k}"] = {"max_abs_diff": float(np.abs(pred - act).max()), "max_rel_err": float(rel.max()), "median_rel_err": float(np.median(rel)),
                             "worst_output": int(np.argmax(rel)), "max_abs_act": float(np.abs(act).max())}
    return res


def feasibility_audit(ev: dict[str, Any], vnom: np.ndarray, vref: np.ndarray, bar_meta: list[dict[str, Any]], lim, errs: dict[str, Any] | None) -> dict[str, Any]:
    """Independent feasibility checks, conflict set (elastic-LP duals), QP by two solvers, raw-constraint residuals and failure classification."""
    a_all = np.vstack([ev["A"], ev["A_ref"]]) * vref[None, :]
    b_all = np.concatenate([ev["b"], ev["b_ref"]])
    meta_all = list(ev["meta"]) + list(ev["meta_ref"])
    names = [m["name"] for m in meta_all]
    norms = np.linalg.norm(a_all, axis=1)
    live = norms > 1e-9
    dead_bad = [names[i] for i in np.where(~live & (b_all > 0))[0]]
    a_n, b_n = a_all[live] / norms[live, None], b_all[live] / norms[live]
    ln = [n for n, l in zip(names, live) if l]
    nvar = a_n.shape[1]
    out: dict[str, Any] = {"n_constraints": int(len(b_all)), "n_live": int(live.sum()), "dead_rows_requiring_action": dead_bad, "row_norm_min": float(norms[live].min()) if live.any() else None,
                           "row_norm_max": float(norms.max()), "row_norm_ratio": float(norms.max() / norms[live].min()) if live.any() else None}

    def scale_lp(an, bn, method):
        c = np.zeros(nvar + 1); c[-1] = 1.0
        aub = np.vstack([np.hstack([-an, np.zeros((an.shape[0], 1))]), np.hstack([np.eye(nvar), -np.ones((nvar, 1))]), np.hstack([-np.eye(nvar), -np.ones((nvar, 1))])])
        bub = np.concatenate([-bn, np.zeros(2 * nvar)])
        r = linprog(c, A_ub=aub, b_ub=bub, bounds=[(None, None)] * nvar + [(0, None)], method=method)
        return r

    t0 = time.perf_counter()
    r_ds, r_ipm = scale_lp(a_n, b_n, "highs-ds"), scale_lp(a_n, b_n, "highs-ipm")
    out["time_lp_s"] = time.perf_counter() - t0
    s_ds = float(r_ds.x[-1]) if r_ds.status == 0 else None
    s_ipm = float(r_ipm.x[-1]) if r_ipm.status == 0 else None
    out["authority_scale_min"] = s_ds
    out["independent_check"] = {"highs_ds_status": int(r_ds.status), "highs_ipm_status": int(r_ipm.status), "scale_ds": s_ds, "scale_ipm": s_ipm,
                                "agree": bool((s_ds is None and s_ipm is None) or (s_ds is not None and s_ipm is not None and abs(s_ds - s_ipm) <= 1e-6 * max(1.0, abs(s_ds))))}
    if s_ds is not None:
        w = r_ds.x[:nvar]
        raw_res = a_all @ (w * 1.0) - b_all
        out["independent_check"]["raw_constraint_min_slack_at_lp_solution"] = float(raw_res.min())
    # elastic LP at s = 1: conflicting rows through the duals
    c2 = np.zeros(nvar + 1); c2[-1] = 1.0
    a2 = np.hstack([-a_n, -np.ones((a_n.shape[0], 1))])
    r2 = linprog(c2, A_ub=a2, b_ub=-b_n, bounds=[(-1, 1)] * nvar + [(0, None)], method="highs")
    out["elastic_violation_at_s1"] = float(r2.x[-1]) if r2.status == 0 else None
    conflicts = []
    if r2.status == 0 and r2.x[-1] > 1e-9:
        marg = np.abs(np.asarray(r2.ineqlin.marginals))
        order = np.argsort(-marg)
        conflicts = [{"name": ln[i], "dual": float(marg[i]), "r": next((m["r"] for m in meta_all if m["name"] == ln[i]), None)} for i in order[:12] if marg[i] > 1e-9]
    out["conflict_set_top"] = conflicts
    out["n_conflict_rows"] = int(len(conflicts))
    # QP at s = 1 with two solvers
    w_nom = vnom / vref
    cons = [{"type": "ineq", "fun": lambda w: a_n @ w - b_n, "jac": lambda w: a_n}]
    qp = {}
    for method in ("SLSQP", "trust-constr"):
        t1 = time.perf_counter()
        kw = {"options": {"maxiter": 300}} if method == "SLSQP" else {"options": {"maxiter": 300, "gtol": 1e-10}}
        if method == "trust-constr":
            from scipy.optimize import LinearConstraint
            res = minimize(lambda w: 0.5 * np.sum((w - w_nom) ** 2), np.clip(w_nom, -1, 1), jac=lambda w: w - w_nom, hess=lambda w: np.eye(nvar), bounds=[(-1, 1)] * nvar,
                           constraints=[LinearConstraint(a_n, b_n, np.inf)], method=method, options={"maxiter": 300, "gtol": 1e-10})
        else:
            res = minimize(lambda w: 0.5 * np.sum((w - w_nom) ** 2), np.clip(w_nom, -1, 1), jac=lambda w: w - w_nom, bounds=[(-1, 1)] * nvar, constraints=cons, method=method,
                           options={"maxiter": 300, "ftol": 1e-12})
        viol = float(max(0.0, (b_n - a_n @ res.x).max()))
        qp[method] = {"converged": bool(viol < 1e-7), "max_violation": viol, "objective": float(0.5 * np.sum((res.x - w_nom) ** 2)), "time_s": time.perf_counter() - t1,
                      "active_rows": [ln[i] for i in np.where(np.abs(a_n @ res.x - b_n) < 1e-6)[0]][:10]}
    out["qp"] = qp
    out["qp_solvers_agree"] = bool(qp["SLSQP"]["converged"] == qp["trust-constr"]["converged"] and (not qp["SLSQP"]["converged"] or abs(qp["SLSQP"]["objective"] - qp["trust-constr"]["objective"]) < 1e-5))
    out["nominal_satisfies_all"] = bool(np.all(a_n @ np.clip(w_nom, -1, 1) - b_n >= -1e-9))
    # failure classification of the conflicting barriers
    cls = []
    if conflicts and errs is not None:
        for cdic in conflicts[:8]:
            nm = cdic["name"]
            row = ln.index(nm)
            single = np.vstack([a_n[row:row + 1], a_n[[i for i, n in enumerate(ln) if "set" in n]]])
            sb = np.concatenate([b_n[row:row + 1], b_n[[i for i, n in enumerate(ln) if "set" in n]]])
            rs = scale_lp(single, sb, "highs")
            s_j = float(rs.x[-1]) if rs.status == 0 else None
            mm = next((m for m in ev["meta"] if m["name"] == nm), None)
            rel = None
            if mm is not None and "kind" in mm and errs.get("0.25"):
                e = errs["0.25"]
                hp = h_from_outputs(mm["kind"], mm.get("unit"), mm.get("bus"), e["P_pred"], e["Q_pred"], e["V_pred"], lim)
                ha = h_from_outputs(mm["kind"], mm.get("unit"), mm.get("bus"), e["P_act"], e["Q_act"], e["V_act"], lim)
                rel = float(abs(hp - ha) / max(abs(mm["h0"]), 1e-3))
            if rel is not None and rel > REL_ERR_APPROX:
                label = "approximation"
            elif s_j is None or s_j > 1.0:
                label = "authority"
            else:
                label = "mixed"
            cls.append({"name": nm, "single_row_authority_scale": s_j, "relative_h_prediction_error_tau_0.25s": rel, "classification": label})
    out["conflict_classification"] = cls
    return out
