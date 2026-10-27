"""E9-H: predictive safety filter on the eight GFM reference rates (no HOCBF derivatives).

Predictor.  At every supervisory update the ANDES state is linearized (frozen Jacobians, parameter derivatives cached) and the closed loop "plant + original RDC" is written as an
affine system in (dx_d, du):
    dx' = A dx + B_u du + xdot0,                du' = v0 + G_u du + G_y (C dx + C_u du) + E dv ,
where v0 is the nominal (B2) rate command at the update, G is the finite-difference linearization of the RDC law with respect to (u, P, Q, V_unit, omega_unit), and dv is a constant
offset of the eight GFM rates over the horizon H (candidate action).  The exact discretisation expm(M dt) gives the nominal prediction Y_k (k dt, k = 1..K) of the 59 outputs
(P, Q of the ten units, 39 bus voltages) and their sensitivity R_k to dv.  The SG references follow the original RDC inside the prediction.
Safety condition.  For every enforceable barrier j and grid time k:  m_j,k(nominal) + r_jk . dv - s |r_jk| |dv| >= eps_jk, with eps the prediction-error bound (e9h validation) and s the
relative error of the sensitivities (E9-C ramp tests).  Barriers whose achievable margin change over the horizon is below 10 % of their bound are MONITORED only (no guarantee).
Nothing here is a mathematical proof: eps and s are empirical maxima times a declared factor.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
from scipy.linalg import expm
from scipy.optimize import linprog

import e9a_hocbf as H
import e9a_linear as L
import e9f_engine as E
import select_equilibrium_b3 as b3

DT = 0.1
HORIZON = 3.0
K = int(round(HORIZON / DT))
GFM_CH = [6, 7, 8, 9, 16, 17, 18, 19]          # reference channels of GFM32, GFM37, GFM34, GFM36 (Pset then Qset)
SENS_ERR = 0.15                                 # relative error of the sensitivities (E9-C ramp tests: 31 / 14 / 10 % at 0.05 / 0.1 / 0.2 s); declared
ENFORCEABLE_FRACTION = 0.10                     # declared


class LinearPredictor:
    def __init__(self, ctx: dict[str, Any], cache: dict[str, Any] | None = None):
        self.ctx, self.cache = ctx, cache if cache is not None else {}
        self.lim = ctx["lim"] if ctx else None

    def _rdc(self, st, u, p, q, v, om):
        parts, _, _ = b3.rdc_field(u[:10], u[10:], p, q, v, om, st["pn"], st["qn"], self.ctx["lim"], self.ctx["adjacency"], st["gref_p"], st["gref_q"], st["k_ip"])
        return np.concatenate([parts["vP"], parts["vQ"]])

    def build(self, sys_, st, vnom_p, vnom_q, t: float, refresh_params: bool) -> dict[str, Any]:
        ctx = self.ctx
        tt: dict[str, float] = {}
        t0 = time.perf_counter()
        if refresh_params:
            self.cache.clear()
        lin = L.linearize(sys_, ctx, cache=self.cache)
        tt["linearize"] = time.perf_counter() - t0
        t0 = time.perf_counter()
        rs = H.rows_of(sys_, ctx)
        y = np.asarray(sys_.dae.y, float)
        a_p, a_q, a_v, a_f = (np.asarray(st[k]) for k in ("a_p", "a_q", "a_v", "a_f"))
        u0 = np.concatenate([np.asarray(st["pset"], float), np.asarray(st["qset"], float)])
        p0, q0, v0u, om0 = y[a_p], y[a_q], y[a_v], y[a_f]
        v0 = np.concatenate([vnom_p, vnom_q]) if t >= 5.0 else np.zeros(20)
        base = self._rdc(st, u0, p0, q0, v0u, om0)
        h = 1e-6
        G_u = np.zeros((20, 20)); G_y = np.zeros((20, 40))
        for i in range(20):
            du = u0.copy(); du[i] += h
            G_u[:, i] = (self._rdc(st, du, p0, q0, v0u, om0) - base) / h
        args = [p0, q0, v0u, om0]
        for blk in range(4):
            for i in range(10):
                a = [x.copy() for x in args]
                a[blk][i] += h
                G_y[:, 10 * blk + i] = (self._rdc(st, u0, *a) - base) / h
        tt["rdc_fd"] = time.perf_counter() - t0
        t0 = time.perf_counter()
        idx40 = np.concatenate([a_p, a_q, a_v, a_f])
        idx59 = np.concatenate([rs["P"], rs["Q"], rs["Vbus"]])
        n = lin["A"].shape[0]
        Cx40, Cu40 = lin["Cy_x"][idx40], lin["Cy_u"][idx40]
        Cz = np.hstack([lin["Cy_x"][idx59], lin["Cy_u"][idx59]])
        M = np.zeros((n + 20, n + 20))
        M[:n, :n], M[:n, n:] = lin["A"], lin["B_u"]
        M[n:, :n] = G_y @ Cx40
        M[n:, n:] = G_u + G_y @ Cu40
        nz = n + 20
        Mt = np.zeros((nz + 1 + 8, nz + 1 + 8))
        Mt[:nz, :nz] = M
        Mt[:n, nz] = lin["xdot"]
        Mt[n:nz, nz] = v0
        for j, ch in enumerate(GFM_CH):
            Mt[n + ch, nz + 1 + j] = 1.0
        Phi = expm(Mt * DT)
        tt["assemble_expm"] = time.perf_counter() - t0
        t0 = time.perf_counter()
        V = np.zeros((nz + 1 + 8, 9))
        V[nz, 0] = 1.0
        for j in range(8):
            V[nz + 1 + j, 1 + j] = 1.0
        Y = np.zeros((K + 1, 59)); R = np.zeros((K + 1, 59, 8)); U = np.zeros((K + 1, 20)); RU = np.zeros((K + 1, 20, 8))
        y0_59 = y[idx59]
        Y[0] = y0_59; U[0] = u0
        for k in range(1, K + 1):
            V = Phi @ V
            Z = V[:nz]
            Y[k] = y0_59 + Cz @ Z[:, 0]
            R[k] = Cz @ Z[:, 1:]
            U[k] = u0 + Z[n:, 0]
            RU[k] = Z[n:, 1:]
        tt["propagate"] = time.perf_counter() - t0
        return {"Y": Y, "R": R, "U": U, "RU": RU, "y0": y0_59, "u0": u0, "t": t, "timing": tt, "M": M, "A_plant": lin["A"], "n_dyn": n, "xdot": lin["xdot"], "v0": v0, "Cz": Cz}


def tighten_and_assemble(pred: dict[str, Any], eps: np.ndarray, vref: np.ndarray, lim: dict[str, np.ndarray], sens_err: float = SENS_ERR):
    """Rows of the safety LP.  eps: (K+1, 59) error bounds of the outputs (row 0 unused).  Returns rows (list of dict) and the arrays for the LP."""
    Y, R, U, RU = pred["Y"], pred["R"], pred["U"], pred["RU"]
    rows = []                                   # each: name, kind, k, m (nominal margin), r (8,), eps, enforceable-flag computed later
    P, Q, V = slice(0, 10), slice(10, 20), slice(20, 59)
    for k in range(1, K + 1):
        for i in range(10):
            e_p, e_q = eps[k, i], eps[k, 10 + i]
            rows.append({"name": f"P+{i}", "k": k, "m": lim["pmax"][i] - Y[k, i], "r": -R[k, i], "eps": e_p})
            rows.append({"name": f"P-{i}", "k": k, "m": Y[k, i] - lim["pmin"][i], "r": R[k, i], "eps": e_p})
            rows.append({"name": f"Q+{i}", "k": k, "m": lim["qmax"][i] - Y[k, 10 + i], "r": -R[k, 10 + i], "eps": e_q})
            rows.append({"name": f"Q-{i}", "k": k, "m": Y[k, 10 + i] - lim["qmin"][i], "r": R[k, 10 + i], "eps": e_q})
            s_nom = float(np.hypot(Y[k, i], Y[k, 10 + i]))
            if s_nom > 1e-9:
                gp, gq = Y[k, i] / s_nom, Y[k, 10 + i] / s_nom
                r_s = gp * R[k, i] + gq * R[k, 10 + i]
                dmax = float(np.linalg.norm(np.stack([R[k, i], R[k, 10 + i]]), axis=0) @ vref)
                eps_s = abs(gp) * e_p + abs(gq) * e_q + dmax ** 2 / (2 * s_nom)
                rows.append({"name": f"S{i}", "k": k, "m": lim["smax"][i] - s_nom, "r": -r_s, "eps": eps_s})
        for b_ in range(39):
            e_v = eps[k, 20 + b_]
            rows.append({"name": f"V+{b_}", "k": k, "m": 1.05 - Y[k, 20 + b_], "r": -R[k, 20 + b_], "eps": e_v})
            rows.append({"name": f"V-{b_}", "k": k, "m": Y[k, 20 + b_] - 0.95, "r": R[k, 20 + b_], "eps": e_v})
    for r in rows:
        r["gain"] = float(np.sum(np.maximum.reduce([r["r"] - sens_err * np.abs(r["r"]), -r["r"] - sens_err * np.abs(r["r"]), np.zeros(8)]) * vref))
        r["worst_loss"] = float(np.sum(np.abs(r["r"]) * (1 + sens_err) * vref))
    return rows


def classify(rows: list[dict[str, Any]], fraction: float = ENFORCEABLE_FRACTION) -> set[str]:
    """Barriers (by name) that the GFM actions can influence: achievable margin change over the horizon >= fraction * largest bound."""
    best_gain: dict[str, float] = {}
    max_eps: dict[str, float] = {}
    for r in rows:
        best_gain[r["name"]] = max(best_gain.get(r["name"], 0.0), r["gain"])
        max_eps[r["name"]] = max(max_eps.get(r["name"], 0.0), r["eps"])
    return {n for n in best_gain if best_gain[n] >= fraction * max_eps[n] and best_gain[n] > 1e-9}


def solve_lp(rows: list[dict[str, Any]], enforce: set[str], pred: dict[str, Any], vref: np.ndarray, lim: dict[str, np.ndarray], sens_err: float = SENS_ERR) -> dict[str, Any]:
    """Minimal-intervention LP:  min sum |dv_i| / vref_i  subject to the tightened margins of the enforceable barriers and the GFM reference boxes.  dv = d+ - d-."""
    A, b = [], []
    for r in rows:
        if r["name"] not in enforce:
            continue
        if r["m"] - r["eps"] - r["worst_loss"] >= 0:           # cannot be violated by any admissible dv: pruned
            continue
        rr = r["r"]
        A.append(np.concatenate([-(rr - sens_err * np.abs(rr)), (rr + sens_err * np.abs(rr))]))
        b.append(r["m"] - r["eps"])
    U, RU = pred["U"], pred["RU"]
    for k in range(1, K + 1):
        for g in range(4):
            i = 6 + g
            for ch, lo, hi in ((i, lim["pmin"][i], lim["pmax"][i]), (10 + i, lim["qmin"][i], lim["qmax"][i])):
                rr = RU[k, ch]
                A.append(np.concatenate([rr, -rr])); b.append(hi - U[k, ch])           # u_nom + RU dv <= hi
                A.append(np.concatenate([-rr, rr])); b.append(U[k, ch] - lo)           # u_nom + RU dv >= lo
    A, b = np.array(A), np.array(b)
    c = np.concatenate([1.0 / vref, 1.0 / vref])
    res = linprog(c, A_ub=A, b_ub=b, bounds=[(0, v) for v in vref] * 2, method="highs")
    out = {"status": int(res.status), "n_rows": int(len(b)), "feasible": bool(res.status == 0)}
    if res.status == 0:
        d = res.x[:8] - res.x[8:]
        out["dv"] = d
        out["cost"] = float(res.fun)
        out["min_slack_rows"] = float((b - A @ res.x).min()) if len(b) else None
    else:
        # diagnostic: elastic LP to name the conflicting rows (not applied)
        c2 = np.zeros(17); c2[-1] = 1.0
        lp2 = linprog(c2, A_ub=np.hstack([A, -np.ones((A.shape[0], 1))]), b_ub=b, bounds=[(0, v) for v in vref] * 2 + [(0, None)], method="highs")
        if lp2.status == 0:
            slack = b - A @ lp2.x[:16]
            out["elastic_violation"] = float(lp2.x[-1])
            out["worst_rows_idx"] = [int(i) for i in np.argsort(slack)[:5]]
    return out


# ------------------------------------------------------------------------------------------------ vectorised implementation (same rows, same LP; measured faster)
_NAMES_CACHE: dict[str, np.ndarray] = {}


def _names() -> dict[str, np.ndarray]:
    if not _NAMES_CACHE:
        _NAMES_CACHE["P+"] = np.array([f"P+{i}" for i in range(10)]); _NAMES_CACHE["P-"] = np.array([f"P-{i}" for i in range(10)])
        _NAMES_CACHE["Q+"] = np.array([f"Q+{i}" for i in range(10)]); _NAMES_CACHE["Q-"] = np.array([f"Q-{i}" for i in range(10)])
        _NAMES_CACHE["S"] = np.array([f"S{i}" for i in range(10)])
        _NAMES_CACHE["V+"] = np.array([f"V+{b}" for b in range(39)]); _NAMES_CACHE["V-"] = np.array([f"V-{b}" for b in range(39)])
    return _NAMES_CACHE


def assemble_vec(pred: dict[str, Any], eps: np.ndarray, vref: np.ndarray, lim: dict[str, np.ndarray], sens_err: float = SENS_ERR) -> dict[str, Any]:
    """Vectorised version of tighten_and_assemble (identical rows); returns arrays name, k, m, r, eps, gain, worst_loss."""
    Y, R = pred["Y"][1:], pred["R"][1:]
    E = eps[1:]
    nm = _names()
    blocks = []

    def add(name, m, r, e):                      # m, e: (K, n); r: (K, n, 8); name: (n,)
        kk = np.repeat(np.arange(1, K + 1), m.shape[1])
        blocks.append((np.tile(name, K), kk, m.reshape(-1), r.reshape(-1, 8), e.reshape(-1)))

    add(nm["P+"], lim["pmax"][None, :] - Y[:, :10], -R[:, :10], E[:, :10])
    add(nm["P-"], Y[:, :10] - lim["pmin"][None, :], R[:, :10], E[:, :10])
    add(nm["Q+"], lim["qmax"][None, :] - Y[:, 10:20], -R[:, 10:20], E[:, 10:20])
    add(nm["Q-"], Y[:, 10:20] - lim["qmin"][None, :], R[:, 10:20], E[:, 10:20])
    s_nom = np.hypot(Y[:, :10], Y[:, 10:20])
    ok = s_nom > 1e-9
    sn = np.where(ok, s_nom, 1.0)
    gp, gq = Y[:, :10] / sn, Y[:, 10:20] / sn
    r_s = gp[:, :, None] * R[:, :10] + gq[:, :, None] * R[:, 10:20]
    dmax = np.sqrt(R[:, :10] ** 2 + R[:, 10:20] ** 2) @ vref
    eps_s = np.abs(gp) * E[:, :10] + np.abs(gq) * E[:, 10:20] + dmax ** 2 / (2 * sn)
    kk = np.repeat(np.arange(1, K + 1), 10)
    mask = ok.reshape(-1)
    blocks.append((np.tile(nm["S"], K)[mask], kk[mask], (lim["smax"][None, :] - s_nom).reshape(-1)[mask], (-r_s).reshape(-1, 8)[mask], eps_s.reshape(-1)[mask]))
    add(nm["V+"], 1.05 - Y[:, 20:], -R[:, 20:], E[:, 20:])
    add(nm["V-"], Y[:, 20:] - 0.95, R[:, 20:], E[:, 20:])
    name = np.concatenate([b_[0] for b_ in blocks]); k = np.concatenate([b_[1] for b_ in blocks]); m = np.concatenate([b_[2] for b_ in blocks])
    r = np.concatenate([b_[3] for b_ in blocks]); e = np.concatenate([b_[4] for b_ in blocks])
    ar = np.abs(r)
    gain = (np.maximum(np.maximum(r - sens_err * ar, -r - sens_err * ar), 0.0) * vref).sum(axis=1)
    worst = (ar * (1 + sens_err) * vref).sum(axis=1)
    return {"name": name, "k": k, "m": m, "r": r, "eps": e, "gain": gain, "worst_loss": worst}


def classify_vec(rows: dict[str, Any], fraction: float = ENFORCEABLE_FRACTION) -> set[str]:
    names, inv = np.unique(rows["name"], return_inverse=True)
    g = np.zeros(len(names)); e = np.zeros(len(names))
    np.maximum.at(g, inv, rows["gain"]); np.maximum.at(e, inv, rows["eps"])
    return {str(n) for n, gg, ee in zip(names, g, e) if gg >= fraction * ee and gg > 1e-9}


def solve_lp_vec(rows: dict[str, Any], enforce: set[str], pred: dict[str, Any], vref: np.ndarray, lim: dict[str, np.ndarray], sens_err: float = SENS_ERR) -> dict[str, Any]:
    sel = np.isin(rows["name"], list(enforce)) & ((rows["m"] - rows["eps"] - rows["worst_loss"]) < 0)
    rr = rows["r"][sel]
    A = np.hstack([-(rr - sens_err * np.abs(rr)), (rr + sens_err * np.abs(rr))])
    b = (rows["m"] - rows["eps"])[sel]
    U, RU = pred["U"][1:], pred["RU"][1:]
    A_ref, b_ref = [], []
    for g in range(4):
        i = 6 + g
        for ch, lo, hi in ((i, lim["pmin"][i], lim["pmax"][i]), (10 + i, lim["qmin"][i], lim["qmax"][i])):
            rch = RU[:, ch]                                    # (K, 8)
            A_ref.append(np.hstack([rch, -rch])); b_ref.append(hi - U[:, ch])
            A_ref.append(np.hstack([-rch, rch])); b_ref.append(U[:, ch] - lo)
    A = np.vstack([A] + A_ref)
    b = np.concatenate([b] + b_ref)
    c = np.concatenate([1.0 / vref, 1.0 / vref])
    res = linprog(c, A_ub=A, b_ub=b, bounds=[(0, v) for v in vref] * 2, method="highs")
    out = {"status": int(res.status), "n_rows": int(len(b)), "feasible": bool(res.status == 0)}
    if res.status == 0:
        out["dv"] = res.x[:8] - res.x[8:]
        out["cost"] = float(res.fun)
    else:
        c2 = np.zeros(17); c2[-1] = 1.0
        lp2 = linprog(c2, A_ub=np.hstack([A, -np.ones((A.shape[0], 1))]), b_ub=b, bounds=[(0, v) for v in vref] * 2 + [(0, None)], method="highs")
        if lp2.status == 0:
            out["elastic_violation"] = float(lp2.x[-1])
    return out
