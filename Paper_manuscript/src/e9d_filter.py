"""E9-D: per-step HOCBF-QP filter (frozen-Jacobian model, refreshed periodically) with the same constraints as e9a_hocbf.evaluate.

Prepared for the supervised S0 test (E9-B2).  NOT used by any historical run.  The model (A, B, C of the augmented system and the chains c A^k) is refreshed every
``refresh_s`` seconds; at every control step only matrix-vector products with the current z_dot0 = (x_dot, 0) and the current outputs are evaluated, so the per-step cost is
independent of the linearization cost (both are measured and reported).  The QP is  min 1/2 ||(v - v_nom)/v_ref||^2  s.t. A v >= b (rows normalised), |v/v_ref| <= 1;
when the nominal command already satisfies every constraint it IS the QP optimum and is returned unchanged (no numerical noise is injected).  If the QP is infeasible the
least-violation (elastic) solution is applied and the event is counted: no constraint is relaxed silently.
"""

from __future__ import annotations

import time
from math import comb
from typing import Any

import numpy as np
from scipy.optimize import linprog, minimize

import e9a_hocbf as H
import e9a_linear as L


class FastHOCBF:
    def __init__(self, lam: float, vref: tuple[float, float], refresh_s: float = 5.0, curvature_S: bool = False):
        self.lam, self.vref_pair, self.refresh_s, self.curv = lam, vref, refresh_s, curvature_S
        self.vref = H.scale_channels(*vref)
        self.t_refresh = -1e9
        self.stats = {"n_steps": 0, "n_nominal_feasible": 0, "n_qp": 0, "n_qp_infeasible": 0, "t_refresh_s": [], "t_step_s": [], "t_qp_s": [], "max_deviation_norm": 0.0, "n_refresh": 0}
        self.lin: dict[str, Any] | None = None

    # ------------------------------------------------------------------ model refresh
    def refresh(self, sys_, ctx, st, t: float) -> None:
        t0 = time.perf_counter()
        lin = L.linearize(sys_, ctx)
        self.rs = H.rows_of(sys_, ctx)
        rows = np.concatenate([self.rs["P"], self.rs["Q"], self.rs["Vbus"]])
        a_z, b_v, c_all = L.augmented(lin, rows)
        self.n_z = a_z.shape[0]
        chains = [c_all]
        for _ in range(3):
            chains.append(chains[-1] @ a_z)                 # chains[k] = C A^k, k = 0..3
        self.chains = chains
        self.lead = chains[2] @ b_v                         # C A^2 B_v: relative degree 3 for every output (checked below)
        mk = L.markov(a_z, b_v, c_all, 4)
        self.r_ok = bool(np.abs(mk[0]).max() < 1e-8 and np.abs(mk[1]).max() < 1e-8 and np.abs(mk[2]).min(axis=1).max() > 0)
        lin["tf_d"] = np.asarray(lin["raw"]["tf"], float)[lin["d_idx"]]
        self.lin = lin
        self.n_d = a_z.shape[0] - 20
        self.t_refresh = t
        self.stats["n_refresh"] += 1
        self.stats["t_refresh_s"].append(time.perf_counter() - t0)

    # ------------------------------------------------------------------ constraints
    def constraints(self, p, q, vb, pset, qset, zdot, lim) -> tuple[np.ndarray, np.ndarray, list[str]]:
        lam = self.lam
        d1, d2, d3 = (ch @ zdot for ch in (self.chains[0], self.chains[1], self.chains[2]))       # h^(1..3) of the outputs (c A^{k-1} z_dot, k = 1..3)
        # chains index: output derivative k uses c A^{k-1} z_dot -> k=1: chains[0], k=2: chains[1], k=3: chains[2]
        iP, iQ, iV = slice(0, 10), slice(10, 20), slice(20, None)
        rows, rhs, names = [], [], []

        def add(lead, h0, e1, e2, e3, name):
            rows.append(lead)
            rhs.append(-(lam ** 3 * h0 + 3 * lam ** 2 * e1 + 3 * lam * e2 + e3))
            names.append(name)

        for i in range(10):
            for kind, sg, h0 in (("P+", -1.0, lim["pmax"][i] - p[i]), ("P-", 1.0, p[i] - lim["pmin"][i])):
                add(sg * self.lead[i], h0, sg * d1[i], sg * d2[i], sg * d3[i], f"{kind}{i}")
            for kind, sg, h0 in (("Q+", -1.0, lim["qmax"][i] - q[i]), ("Q-", 1.0, q[i] - lim["qmin"][i])):
                add(sg * self.lead[10 + i], h0, sg * d1[10 + i], sg * d2[10 + i], sg * d3[10 + i], f"{kind}{i}")
            wP, wQ = -2.0 * p[i], -2.0 * q[i]
            ds = [wP * dd[i] + wQ * dd[10 + i] for dd in (d1, d2, d3)]
            if self.curv:
                # exact Leibniz terms of S = smax^2 - P^2 - Q^2 from the predicted output derivatives (E9-C curvature)
                P = [p[i], d1[i], d2[i], d3[i]]
                Q = [q[i], d1[10 + i], d2[10 + i], d3[10 + i]]
                ds = [-sum(comb(k, j) * (P[j] * P[k - j] + Q[j] * Q[k - j]) for j in range(k + 1)) for k in (1, 2, 3)]
            add(wP * self.lead[i] + wQ * self.lead[10 + i], lim["smax"][i] ** 2 - p[i] ** 2 - q[i] ** 2, ds[0], ds[1], ds[2], f"S{i}")
        for b_i in range(len(vb)):
            add(-self.lead[20 + b_i], 1.05 - vb[b_i], -d1[20 + b_i], -d2[20 + b_i], -d3[20 + b_i], f"V+{b_i}")
            add(self.lead[20 + b_i], vb[b_i] - 0.95, d1[20 + b_i], d2[20 + b_i], d3[20 + b_i], f"V-{b_i}")
        a_ref, b_ref = [], []
        for i in range(10):
            for ch, sgn, val in ((i, -1.0, lim["pmax"][i] - pset[i]), (i, 1.0, pset[i] - lim["pmin"][i]), (10 + i, -1.0, lim["qmax"][i] - qset[i]), (10 + i, 1.0, qset[i] - lim["qmin"][i])):
                r_ = np.zeros(20); r_[ch] = sgn
                a_ref.append(r_); b_ref.append(-lam * val); names.append(f"ref{ch}{'+' if sgn < 0 else '-'}")
            r_ = np.zeros(20); r_[i], r_[10 + i] = -2.0 * pset[i], -2.0 * qset[i]
            a_ref.append(r_); b_ref.append(-lam * (lim["smax"][i] ** 2 - pset[i] ** 2 - qset[i] ** 2)); names.append(f"refS{i}")
        return np.vstack([np.array(rows), np.array(a_ref)]), np.concatenate([np.array(rhs), np.array(b_ref)]), names

    # ------------------------------------------------------------------ one control step
    def filter(self, t, sys_, ctx, st, vnom_p, vnom_q):
        t0 = time.perf_counter()
        if self.lin is None or t - self.t_refresh >= self.refresh_s:
            self.refresh(sys_, ctx, st, t)
        y = sys_.dae.y
        p, q, vb = (np.asarray(y[self.rs[k]], float) for k in ("P", "Q", "Vbus"))
        xdot = np.asarray(sys_.dae.f, float).ravel()[self.lin["d_idx"]] / self.lin["tf_d"]
        zdot = np.concatenate([xdot, np.zeros(20)])
        a_all, b_all, names = self.constraints(p, q, vb, np.asarray(st["pset"], float), np.asarray(st["qset"], float), zdot, ctx["lim"])
        vnom = np.concatenate([vnom_p, vnom_q])
        w_nom = vnom / self.vref
        a_s = a_all * self.vref[None, :]
        nrm = np.linalg.norm(a_s, axis=1)
        live = nrm > 1e-9
        a_n, b_n = a_s[live] / nrm[live, None], b_all[live] / nrm[live]
        self.stats["n_steps"] += 1
        sat = a_n @ np.clip(w_nom, -1, 1) - b_n
        info = {"active": False, "infeasible": False, "violated": []}
        if np.any(sat < -1e-12):
            ln = [n for n, l in zip(names, live) if l]
            bad = np.argsort(sat)[:3]
            info["violated"] = [(ln[i], float(sat[i])) for i in bad if sat[i] < -1e-12]
            for i in np.where(sat < -1e-12)[0]:
                self.stats.setdefault("violated_counts", {})
                self.stats["violated_counts"][ln[i]] = self.stats["violated_counts"].get(ln[i], 0) + 1
        if np.all(sat >= -1e-12) and np.all(np.abs(w_nom) <= 1.0 + 1e-12):
            self.stats["n_nominal_feasible"] += 1
            w = w_nom
        else:
            tq = time.perf_counter()
            self.stats["n_qp"] += 1
            res = minimize(lambda w_: 0.5 * np.sum((w_ - w_nom) ** 2), np.clip(w_nom, -1, 1), jac=lambda w_: w_ - w_nom, bounds=[(-1, 1)] * 20,
                           constraints=[{"type": "ineq", "fun": lambda w_: a_n @ w_ - b_n, "jac": lambda w_: a_n}], method="SLSQP", options={"maxiter": 100, "ftol": 1e-12})
            viol = float(max(0.0, (b_n - a_n @ res.x).max()))
            if viol > 1e-7:                                   # infeasible: least-violation solution, counted and reported
                c = np.zeros(21); c[-1] = 1.0
                lp = linprog(c, A_ub=np.hstack([-a_n, -np.ones((a_n.shape[0], 1))]), b_ub=-b_n, bounds=[(-1, 1)] * 20 + [(0, None)], method="highs")
                w = lp.x[:20] if lp.status == 0 else np.clip(res.x, -1, 1)
                self.stats["n_qp_infeasible"] += 1
                info["infeasible"] = True
            else:
                w = res.x
            info["active"] = True
            self.stats["t_qp_s"].append(time.perf_counter() - tq)
            self.stats["max_deviation_norm"] = max(self.stats["max_deviation_norm"], float(np.linalg.norm(w - w_nom)))
        v = w * self.vref
        self.stats["t_step_s"].append(time.perf_counter() - t0)
        self.last = info
        return v[:10], v[10:]
