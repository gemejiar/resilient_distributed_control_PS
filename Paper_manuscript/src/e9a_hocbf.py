"""E9-A diagnostic HOCBF construction and QP feasibility (frozen-Jacobian model of e9a_linear; never in the simulation loop).

Barriers (all on modelled quantities only):
  physical   h = pmax - P,  P - pmin,  qmax - Q,  Q - qmin,  smax^2 - P^2 - Q^2   (10 units),  V - 0.95,  1.05 - V (39 buses)
  reference  h^u = pmax - Pset,  Pset - pmin,  qmax - Qset,  Qset - qmin,  smax^2 - Pset^2 - Qset^2   (relative degree one in v)
Relative degree r_j is read from the Markov parameters C A^k B_v of the augmented model (z = (xd, Pset, Qset), v = dz_ref/dt): r = k + 1 for
the first k with a non-zero coefficient.  With equal linear class-K gains lambda the HOCBF condition is
    sum_{k=0..r} C(r,k) lambda^{r-k} h^{(k)} >= 0,      h^{(k)} = c A^{k-1} z_dot0  (k < r),   h^{(r)} = c A^{r-1} (z_dot0 + B_v v),
affine in v.  Higher-order derivatives use the frozen Jacobian at the probed state (curvature terms are neglected), so for r >= 2 the
numbers are a local-linear diagnostic, not a certificate.  The QP is solved here only to test feasibility.
"""

from __future__ import annotations

from math import comb
from typing import Any

import numpy as np
from scipy.optimize import linprog, minimize

import e9a_linear as L

V_BAND = (0.95, 1.05)
THR = 1.0e-8            # absolute threshold on a Markov coefficient (structural zeros are ~1e-17, non-zeros >= 1e-3 in C2t)
K_MAX = 8
ROW_TOL = 1.0e-9


def rows_of(system: Any, ctx: dict[str, Any]) -> dict[str, np.ndarray]:
    oi = L.output_indices(system, ctx)
    return {"P": oi["P"], "Q": oi["Q"], "Vbus": oi["Vbus"], "bus_ids": oi["bus_ids"]}


def relative_degrees(lin: dict[str, Any], rows: np.ndarray, kmax: int = K_MAX) -> dict[str, Any]:
    """Relative degree of each output row with respect to each of the 20 reference rates, and the leading coefficient."""
    a_z, b_v, c_z = L.augmented(lin, rows)
    m = L.markov(a_z, b_v, c_z, kmax)
    n_o, n_in = c_z.shape[0], b_v.shape[1]
    rd = np.full((n_o, n_in), 0, dtype=int)
    lead = np.zeros((n_o, n_in))
    for o in range(n_o):
        for j in range(n_in):
            for k in range(kmax):
                if abs(m[k, o, j]) > THR:
                    rd[o, j], lead[o, j] = k + 1, m[k, o, j]
                    break
    return {"rd": rd, "lead": lead, "markov_abs_max": np.abs(m).max(axis=(1, 2)).tolist()}


def _barrier_list(lim: dict[str, np.ndarray], n_bus: int) -> list[dict[str, Any]]:
    out = []
    for i in range(10):
        out += [{"name": f"P{i}+", "kind": "P+", "unit": i}, {"name": f"P{i}-", "kind": "P-", "unit": i}, {"name": f"Q{i}+", "kind": "Q+", "unit": i},
                {"name": f"Q{i}-", "kind": "Q-", "unit": i}, {"name": f"S{i}", "kind": "S", "unit": i}]
    for b in range(n_bus):
        out += [{"name": f"V{b}+", "kind": "V+", "bus": b}, {"name": f"V{b}-", "kind": "V-", "bus": b}]
    return out


def evaluate(lin: dict[str, Any], rowset: dict[str, np.ndarray], p: np.ndarray, q: np.ndarray, vbus: np.ndarray, pset: np.ndarray, qset: np.ndarray,
             lim: dict[str, np.ndarray], lam: float, unit_names: list[str], bus_ids: np.ndarray) -> dict[str, Any]:
    """HOCBF constraints A v >= b for the physical barriers and the (relative-degree-one) reference barriers at one frozen state."""
    n_d = lin["A"].shape[0]
    allrows = np.concatenate([rowset["P"], rowset["Q"], rowset["Vbus"]])
    a_z, b_v, c_all = L.augmented(lin, allrows)
    iP, iQ = np.arange(10), 10 + np.arange(10)
    iV = 20 + np.arange(len(rowset["Vbus"]))
    zdot = np.concatenate([lin["xdot"], np.zeros(20)])
    # row-wise Markov and derivative stacks
    mk = L.markov(a_z, b_v, c_all, K_MAX)
    chains = [c_all]
    for _ in range(K_MAX):
        chains.append(chains[-1] @ a_z)             # chains[k] = C A^k
    barriers = _barrier_list(lim, len(rowset["Vbus"]))
    A_rows, b_vec, meta = [], [], []
    for bar in barriers:
        kind = bar["kind"]
        if kind in ("P+", "P-", "Q+", "Q-", "S"):
            i = bar["unit"]
            if kind == "S":
                c_idx = np.array([iP[i], iQ[i]])
                w = np.array([-2.0 * p[i], -2.0 * q[i]])
                h0 = lim["smax"][i] ** 2 - p[i] ** 2 - q[i] ** 2
            else:
                sgn = {"P+": -1.0, "P-": 1.0, "Q+": -1.0, "Q-": 1.0}[kind]
                c_idx, w = np.array([iP[i] if kind[0] == "P" else iQ[i]]), np.array([sgn])
                h0 = {"P+": lim["pmax"][i] - p[i], "P-": p[i] - lim["pmin"][i], "Q+": lim["qmax"][i] - q[i], "Q-": q[i] - lim["qmin"][i]}[kind]
        else:
            bidx = bar["bus"]
            c_idx, w = np.array([iV[bidx]]), np.array([-1.0 if kind == "V+" else 1.0])
            h0 = (V_BAND[1] - vbus[bidx]) if kind == "V+" else (vbus[bidx] - V_BAND[0])
        # relative degree for this barrier: first k with a non-zero combination of Markov rows over any channel
        r, lead_vec = None, None
        for k in range(K_MAX):
            vec = (w[:, None] * mk[k][c_idx]).sum(axis=0)
            if np.abs(vec).max() > THR:
                r, lead_vec = k + 1, vec
                break
        if r is None:
            meta.append({"name": bar["name"], "r": None, "h0": float(h0), "no_authority": True})
            continue
        c_comb = (w[:, None] * np.stack([chains[0][ci] for ci in c_idx])).sum(axis=0)
        # h^{(k)} for 1 <= k < r: c A^{k-1} zdot ; v-free part of h^{(r)}
        d = [float(h0)] + [float((w[:, None] * np.stack([chains[k - 1][ci] for ci in c_idx])).sum(axis=0) @ zdot) for k in range(1, r + 1)]
        psi = [sum(comb(k, i) * lam ** (k - i) * d[i] for i in range(k + 1)) for k in range(r)]
        rhs = -(sum(comb(r, k) * lam ** (r - k) * d[k] for k in range(r)) + d[r])
        A_rows.append(lead_vec.copy())
        b_vec.append(rhs)
        meta.append({"name": bar["name"], "kind": kind, "r": r, "h0": float(h0), "psi_min": float(min(psi)), "psi": [float(x) for x in psi], "d": [float(x) for x in d], "lead_norm": float(np.linalg.norm(lead_vec)), "psi_outside": bool(min(psi) < 0.0), "unit": bar.get("unit"),
                     "bus": bar.get("bus")})
    # reference barriers (relative degree one, direct in v)
    ref_rows, ref_b, ref_meta = [], [], []
    for i in range(10):
        h = {"Pset+": lim["pmax"][i] - pset[i], "Pset-": pset[i] - lim["pmin"][i], "Qset+": lim["qmax"][i] - qset[i], "Qset-": qset[i] - lim["qmin"][i]}
        for nm, val in h.items():
            row = np.zeros(20)
            row[i if nm.startswith("P") else 10 + i] = -1.0 if nm.endswith("+") else 1.0
            ref_rows.append(row); ref_b.append(-lam * val); ref_meta.append({"name": f"{nm}_{unit_names[i]}", "r": 1, "h0": float(val), "psi_outside": bool(val < 0)})
        hs = lim["smax"][i] ** 2 - pset[i] ** 2 - qset[i] ** 2
        row = np.zeros(20); row[i], row[10 + i] = -2.0 * pset[i], -2.0 * qset[i]
        ref_rows.append(row); ref_b.append(-lam * hs); ref_meta.append({"name": f"Sset_{unit_names[i]}", "r": 1, "h0": float(hs), "psi_outside": bool(hs < 0)})
    return {"A": np.array(A_rows), "b": np.array(b_vec), "meta": [m for m in meta if m.get("r") is not None], "no_authority": [m for m in meta if m.get("r") is None],
            "A_ref": np.array(ref_rows), "b_ref": np.array(ref_b), "meta_ref": ref_meta}


def scale_channels(v_ref_p: float, v_ref_q: float) -> np.ndarray:
    return np.concatenate([np.full(10, v_ref_p), np.full(10, v_ref_q)])


def feasibility(ev: dict[str, Any], vnom: np.ndarray, vref: np.ndarray) -> dict[str, Any]:
    """Minimal authority scale s*, and QP at s = 1.

    w = v / vref (dimensionless); constraints A diag(vref) w >= b normalised by the row norm; |w| <= s.  s* is the smallest s for
    which the full HOCBF + reference constraint set is feasible; the QP minimises ||w - w_nom||^2 at s = 1.
    """
    a_all = np.vstack([ev["A"], ev["A_ref"]]) * vref[None, :]
    b_all = np.concatenate([ev["b"], ev["b_ref"]])
    norms = np.linalg.norm(a_all, axis=1)
    dead = norms < ROW_TOL
    names = [m["name"] for m in ev["meta"]] + [m["name"] for m in ev["meta_ref"]]
    dead_bad = [names[i] for i in np.where(dead & (b_all > 0))[0]]
    live = ~dead
    a_n = a_all[live] / norms[live, None]
    b_n = b_all[live] / norms[live]
    live_names = [n for n, l in zip(names, live) if l]
    out: dict[str, Any] = {"n_constraints": int(len(b_all)), "n_dead_rows": int(dead.sum()), "dead_rows_requiring_action": dead_bad}
    # LP: min s subject to a_n w >= b_n, -s <= w <= s
    n = a_n.shape[1]
    c = np.zeros(n + 1); c[-1] = 1.0
    a_ub = np.vstack([np.hstack([-a_n, np.zeros((a_n.shape[0], 1))]), np.hstack([np.eye(n), -np.ones((n, 1))]), np.hstack([-np.eye(n), -np.ones((n, 1))])])
    b_ub = np.concatenate([-b_n, np.zeros(2 * n)])
    res = linprog(c, A_ub=a_ub, b_ub=b_ub, bounds=[(None, None)] * n + [(0, None)], method="highs")
    def scale_for(mask: np.ndarray) -> float | None:
        if not mask.any():
            return 0.0
        am, bm = a_n[mask], b_n[mask]
        aub = np.vstack([np.hstack([-am, np.zeros((am.shape[0], 1))]), np.hstack([np.eye(n), -np.ones((n, 1))]), np.hstack([-np.eye(n), -np.ones((n, 1))])])
        bub = np.concatenate([-bm, np.zeros(2 * n)])
        r_ = linprog(c, A_ub=aub, b_ub=bub, bounds=[(None, None)] * n + [(0, None)], method="highs")
        return float(r_.x[-1]) if r_.status == 0 else None

    ln = np.array(live_names)
    is_v = np.array([nm.startswith("V") for nm in ln])
    is_ref = np.array([("set" in nm) for nm in ln])
    out["authority_scale_by_group"] = {"all": scale_for(np.ones(len(ln), bool)), "physical_PQS_and_reference_no_V": scale_for(~is_v), "V_only": scale_for(is_v),
                                       "SG31_P_upper_only": scale_for(np.isin(ln, ["P1+"])), "SG31_P_upper_with_reference_limits": scale_for(np.isin(ln, ["P1+"]) | is_ref)}
    out["lp_status"] = int(res.status)
    out["authority_scale_min"] = float(res.x[-1]) if res.status == 0 else None
    # elastic LP for the diagnostic of the most demanding rows: min t s.t. a_n w + t >= b_n with |w| <= 1  -> t* = worst unmet normalised violation
    c2 = np.zeros(n + 1); c2[-1] = 1.0
    a2 = np.hstack([-a_n, -np.ones((a_n.shape[0], 1))])
    res2 = linprog(c2, A_ub=a2, b_ub=-b_n, bounds=[(-1, 1)] * n + [(0, None)], method="highs")
    out["elastic_violation_at_s1"] = float(res2.x[-1]) if res2.status == 0 else None
    if res2.status == 0:
        w2 = res2.x[:n]
        slack = a_n @ w2 - b_n
        worst = np.argsort(slack)[:5]
        out["most_demanding_rows_at_s1"] = [{"name": live_names[i], "slack": float(slack[i])} for i in worst]
    # QP at s = 1
    w_nom = vnom / vref
    cons = [{"type": "ineq", "fun": lambda w: a_n @ w - b_n, "jac": lambda w: a_n}]
    qp = minimize(lambda w: 0.5 * np.sum((w - w_nom) ** 2), np.clip(w_nom, -1, 1), jac=lambda w: w - w_nom, bounds=[(-1, 1)] * n, constraints=cons, method="SLSQP",
                  options={"maxiter": 200, "ftol": 1e-10})
    viol = float(max(0.0, (b_n - a_n @ qp.x).max())) if qp.x is not None else None
    out["qp_converged"] = bool(qp.success and viol is not None and viol < 1e-7)
    out["qp_max_constraint_violation"] = viol
    out["qp_deviation_from_nominal_norm"] = float(np.linalg.norm(qp.x - w_nom)) if qp.x is not None else None
    out["nominal_satisfies_all"] = bool(np.all(a_n @ np.clip(w_nom, -1, 1) - b_n >= -1e-9))
    return out
