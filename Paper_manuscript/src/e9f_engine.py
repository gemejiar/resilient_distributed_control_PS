"""E9-F: Lie derivatives of the NONLINEAR reduced DAE (exact algebraics, exact curvature) and HOCBF conditions with a restricted input set.

The reduced system is  x_d' = F(x_d, u, d(tau)),  u_SG' = v_SG(x)  (original RDC, known action),  u_GFM' = v_GFM (the QP inputs),  tau' = 1,
with the algebraic variables y and the quasi-algebraic states x_z eliminated by solving g(x, y, u, d) = 0 (Newton, tight tolerance, chord Jacobian) at every point,
and the GFM actuator feedback (Paux0 = KC (y0 + dPset - PIplim_y), Qaux0 likewise) closed inside the algebraic solve.  The time derivatives of the outputs
(P, Q of the ten units and the 39 bus voltages) along the flow with v_GFM = 0 are obtained by nested central directional differences along the flow field,

    G_0 = Y,   G_k(x) = [G_{k-1}(x + eps F(x)) - G_{k-1}(x - eps F(x))] / (2 eps),

which are exact up to the truncation / round-off of the differences (checked with two eps) and contain the curvature of the DAE, the algebraic effects and the time
derivatives of the disturbance (the clock tau is part of the state; the disturbance is d = amplitude * sigma(tau)).  The decoupling coefficients of the GFM rates come from the
Markov parameters of the exact first-order Jacobians at the current state (lowest-order coefficient); the neglected curvature part is proportional to |F| and is measured by a
finite-difference check at representative states.  The engine writes into the live ANDES system while evaluating and restores it in ``close()``.
Nothing here is a certificate: it is a consistent evaluation of the conditions on the modelled DAE.
"""

from __future__ import annotations

import time
from math import comb
from typing import Any

import numpy as np
from scipy.linalg import lu_factor, lu_solve

import e9a_hocbf as H
import e9a_linear as L
import run_e8_ieee39 as e8
import select_equilibrium_b3 as b3

NEWTON_TOL = 1.0e-13
NEWTON_MAX = 8


def quintic(s: float) -> tuple[float, float, float, float]:
    """C2 smoothstep sigma(s) = 10 s^3 - 15 s^4 + 6 s^5 on [0, 1] and its first three derivatives with respect to s."""
    if s <= 0.0:
        return 0.0, 0.0, 0.0, 0.0
    if s >= 1.0:
        return 1.0, 0.0, 0.0, 0.0
    return (10 * s ** 3 - 15 * s ** 4 + 6 * s ** 5, 30 * s ** 2 - 60 * s ** 3 + 30 * s ** 4, 60 * s - 180 * s ** 2 + 120 * s ** 3, 60 - 360 * s + 360 * s ** 2)


class Disturbance:
    """Load disturbance d(t): a quintic (C2) ramp of given duration, or none.  kind 'P' acts on PQ.Ppf at bus 4, 'Q' on PQ.Qpf at bus 21."""

    def __init__(self, kind: str | None, amplitude_pu: float = 0.0, t_start: float = 5.0, duration: float = 5.0):
        self.kind, self.amp, self.t0, self.T = kind, amplitude_pu, t_start, duration

    def value(self, t: float) -> float:
        return self.amp * quintic((t - self.t0) / self.T)[0] if self.kind else 0.0


class Engine:
    def __init__(self, sys_, ctx, st, lin, dist: Disturbance | None = None, t_now: float = 0.0):
        self.s, self.ctx, self.st, self.lin = sys_, ctx, st, lin
        self.dist = dist or Disturbance(None)
        raw = lin["raw"]
        self.d_idx, self.z_idx = lin["d_idx"], lin["z_idx"]
        self.tf_d = np.asarray(raw["tf"], float)[self.d_idx]
        self.nz = len(self.z_idx)
        fx, fy, gx, gy = raw["fx"], raw["fy"], raw["gx"], raw["gy"]
        self.lu = lu_factor(np.block([[fx[np.ix_(self.z_idx, self.z_idx)], fy[self.z_idx]], [gx[:, self.z_idx], gy]]))
        self.x_base = np.array(sys_.dae.x, float).copy()
        self.y_base = np.array(sys_.dae.y, float).copy()
        self.x_orig, self.y_orig = self.x_base.copy(), self.y_base.copy()     # what close() restores (the projection only changes x_base / y_base)
        self.rs = H.rows_of(sys_, ctx)
        self.n_sg = ctx["n_sg"]
        for k in ("a_p", "a_q", "a_y", "a_yq", "a_f", "a_v"):
            setattr(self, k, np.asarray(st[k]))
        self.u_base = np.concatenate([np.asarray(st["pset"], float), np.asarray(st["qset"], float)])
        self.t_now = t_now
        pq_bus = [int(b) for b in sys_.PQ.bus.v]
        self.ipq = {"P": pq_bus.index(4), "Q": pq_bus.index(21)}
        self.saved = {k: np.array(getattr(m, a).v, float).copy() for k, (m, a) in self._param_slots().items()}
        self.load_base = {"P": float(sys_.PQ.Ppf.v[self.ipq["P"]]) - (self.dist.value(t_now) if self.dist.kind == "P" else 0.0),
                          "Q": float(sys_.PQ.Qpf.v[self.ipq["Q"]]) - (self.dist.value(t_now) if self.dist.kind == "Q" else 0.0)}
        self.n_solves, self.t_solve, self.nx = 0, 0.0, len(self.d_idx)
        self.sg_rates = True      # False: references held constant (validation against a frozen-reference free flow)

    def _param_slots(self):
        s = self.s
        return {"paux0": (s.TGOV1N, "paux0"), "vref0": (s.IEEEX1, "vref0"), "Paux0": (s.REGF1, "Paux0"), "Qaux0": (s.REGF1, "Qaux0"), "Ppf": (s.PQ, "Ppf"), "Qpf": (s.PQ, "Qpf")}

    def project_fast(self, lam_c: float = 100.0) -> dict[str, Any]:
        """Slow-manifold projection of the probe state: the components of x_d along the fast modes (|Re lambda| > lam_c) are moved so that the fast part of the velocity vanishes,
        W_f^T [F + A V_f dxi] = 0  ->  dxi = -Lambda_f^-1 W_f^T F  (one Newton step on the quasi-steady manifold), and the algebraics are re-solved.  The fast content of the
        simulated state at solver-tolerance level (about 1e-7) is amplified by lambda^3 in third derivatives; physical fast transients are also removed, so this is the
        derivative of the slow (reduced) dynamics.  Returns diagnostics."""
        a = self.lin["A"]
        lam, vr = np.linalg.eig(a)
        wl = np.linalg.inv(vr)
        fast = np.abs(lam.real) > lam_c
        x0 = self.xt0()
        y, fd = self.solve(x0)
        dxi = -(wl[fast] @ fd) / lam[fast]
        dx = (vr[:, fast] @ dxi).real
        self.x_base[self.d_idx] += dx
        y2, fd2 = self.solve(self.xt0())
        self.y_base = y2.copy()
        return {"n_fast_modes": int(fast.sum()), "lambda_c": lam_c, "max_abs_state_shift": float(np.abs(dx).max()), "velocity_norm_before": float(np.linalg.norm(fd)), "velocity_norm_after": float(np.linalg.norm(fd2)),
                "fast_velocity_component_before": float(np.abs(wl[fast] @ fd).max()), "fast_velocity_component_after": float(np.abs(wl[fast] @ fd2).max())}

    def close(self) -> None:
        """Restore the live system (states, algebraics, actuator and load parameters) exactly as it was at construction."""
        self.s.dae.x[:] = self.x_orig
        self.s.dae.y[:] = self.y_orig
        self.s.vars_to_models()
        for k, (m, a) in self._param_slots().items():
            getattr(m, a).v[:] = self.saved[k]
        L._refresh(self.s)

    # ---------------------------------------------------------------- state vector xt = (x_d, u(20), t)
    def xt0(self) -> np.ndarray:
        return np.concatenate([self.x_base[self.d_idx], self.u_base, [self.t_now]])

    def _apply_params(self, u: np.ndarray, y: np.ndarray, t: float) -> None:
        s, ctx, st, n_sg = self.s, self.ctx, self.st, self.n_sg
        s.TGOV1N.paux0.v[ctx["tg_pos"]] = (u[:10] - st["pn"])[:n_sg]
        z = np.clip(e8.KAPPA_SG * (u[10:] - st["qn"])[:n_sg], -e8.Z_CLAMP, e8.Z_CLAMP)
        s.IEEEX1.vref0.v[ctx["ex_pos"]] = st["vref0_sg"][ctx["ex_pos"]] + z
        s.REGF1.Paux0.v[:] = e8.KC_GFM * (st["y0"] + (u[:10] - st["pn"])[n_sg:] - y[self.a_y])
        s.REGF1.Qaux0.v[:] = e8.KCQ_GFM * (st["y0q"] + (u[10:] - st["qn"])[n_sg:] - y[self.a_yq])
        if self.dist.kind == "P":
            s.PQ.Ppf.v[self.ipq["P"]] = self.load_base["P"] + self.dist.value(t)
        if self.dist.kind == "Q":
            s.PQ.Qpf.v[self.ipq["Q"]] = self.load_base["Q"] + self.dist.value(t)

    def solve(self, xt: np.ndarray):
        """Algebraic solution at xt: returns (y, f_d / tf_d); quasi-algebraic states and y solved to NEWTON_TOL (chord Newton)."""
        t0 = time.perf_counter()
        dae = self.s.dae
        xd, u, t = xt[:self.nx], xt[self.nx:self.nx + 20], xt[-1]
        x = self.x_base.copy()
        x[self.d_idx] = xd
        y = self.y_base.copy()
        res = np.inf
        for _ in range(NEWTON_MAX):
            dae.x[:] = x
            dae.y[:] = y
            self.s.vars_to_models()          # models read their own copies of x, y
            self._apply_params(u, y, t)
            L._refresh(self.s)
            f, g = np.array(dae.f, float).ravel(), np.array(dae.g, float).ravel()
            r = np.concatenate([f[self.z_idx], g])
            res = np.abs(r).max()
            if res < NEWTON_TOL:
                break
            dlt = lu_solve(self.lu, -r)
            x[self.z_idx] += dlt[:self.nz]
            y += dlt[self.nz:]
        self.last_residual = float(res)
        self.n_solves += 1
        self.t_solve += time.perf_counter() - t0
        return y, f[self.d_idx] / self.tf_d

    def outputs(self, y: np.ndarray) -> np.ndarray:
        return np.concatenate([y[self.rs["P"]], y[self.rs["Q"]], y[self.rs["Vbus"]]])

    def rdc_sg_rates(self, u: np.ndarray, y: np.ndarray):
        st, ctx = self.st, self.ctx
        parts, _, _ = b3.rdc_field(u[:10], u[10:], y[self.a_p], y[self.a_q], y[self.a_v], y[self.a_f], st["pn"], st["qn"], ctx["lim"], ctx["adjacency"], st["gref_p"], st["gref_q"], st["k_ip"])
        return parts["vP"], parts["vQ"]

    def field(self, xt: np.ndarray):
        """F~(xt) (v_GFM = 0) and the outputs at xt."""
        y, fd = self.solve(xt)
        u = xt[self.nx:self.nx + 20]
        udot = np.zeros(20)
        if self.sg_rates:
            vp, vq = self.rdc_sg_rates(u, y)
            udot[:self.n_sg] = vp[:self.n_sg]
            udot[10:10 + self.n_sg] = vq[:self.n_sg]
        return np.concatenate([fd, udot, [1.0]]), self.outputs(y)

    def jets(self, kmax: int = 3, eps: float = 3.0e-4) -> np.ndarray:
        """D[k] = d^k Y / dt^k along the flow at the probe state (k = 0..kmax), v_GFM = 0, by nested central differences along F~."""
        def G(k: int, xt: np.ndarray) -> np.ndarray:
            if k == 0:
                return self.outputs(self.solve(xt)[0])
            f, _ = self.field(xt)
            return (G(k - 1, xt + eps * f) - G(k - 1, xt - eps * f)) / (2 * eps)

        x0 = self.xt0()
        f0, y0 = self.field(x0)
        out = [y0]
        for k in range(1, kmax + 1):
            out.append((G(k - 1, x0 + eps * f0) - G(k - 1, x0 - eps * f0)) / (2 * eps))
        return np.array(out)

    def gfm_coefficients(self) -> dict[str, Any]:
        """Markov parameters C A^k B_v of the eight GFM channels at the current state: relative-degree check and the order-3 coefficient."""
        n_sg = self.n_sg
        cols = [n_sg + i for i in range(4)] + [10 + n_sg + i for i in range(4)]
        allrows = np.concatenate([self.rs["P"], self.rs["Q"], self.rs["Vbus"]])
        a_z, b_v, c_z = L.augmented(self.lin, allrows)
        mk = L.markov(a_z, b_v, c_z, 4)[:, :, cols]
        return {"M0_max": float(np.abs(mk[0]).max()), "M1_max": float(np.abs(mk[1]).max()), "M2_min_row_max": float(np.abs(mk[2]).max(axis=1).min()), "lead": mk[2], "cols": cols,
                "relative_degree_3_all_outputs": bool(np.abs(mk[0]).max() < 1e-8 and np.abs(mk[1]).max() < 1e-8 and np.abs(mk[2]).max(axis=1).min() > 1e-8)}


# ---------------------------------------------------------------------------- barrier conditions
def barrier_table(n_bus: int = 39) -> list[dict[str, Any]]:
    out = []
    for i in range(10):
        out += [{"name": f"P+{i}", "kind": "P+", "unit": i}, {"name": f"P-{i}", "kind": "P-", "unit": i}, {"name": f"Q+{i}", "kind": "Q+", "unit": i},
                {"name": f"Q-{i}", "kind": "Q-", "unit": i}, {"name": f"S{i}", "kind": "S", "unit": i}]
    for b in range(n_bus):
        out += [{"name": f"V+{b}", "kind": "V+", "bus": b}, {"name": f"V-{b}", "kind": "V-", "bus": b}]
    return out


def barrier_jets(bar: dict[str, Any], D: np.ndarray, lim: dict[str, np.ndarray], kmax: int = 3) -> np.ndarray:
    """h and h^(1..kmax) along the flow from the exact output jets; the quadratic S barrier uses the exact Leibniz rule (barrier curvature)."""
    k = bar["kind"]
    if k == "S":
        i = bar["unit"]
        P, Q = D[:, i], D[:, 10 + i]
        out = np.zeros(kmax + 1)
        out[0] = lim["smax"][i] ** 2 - P[0] ** 2 - Q[0] ** 2
        for n in range(1, kmax + 1):
            out[n] = -sum(comb(n, j) * (P[j] * P[n - j] + Q[j] * Q[n - j]) for j in range(n + 1))
        return out
    if k in ("P+", "P-", "Q+", "Q-"):
        i = bar["unit"]
        col = i if k[0] == "P" else 10 + i
        sg = -1.0 if k[1] == "+" else 1.0
        out = sg * D[:kmax + 1, col].copy()
        out[0] += {"P+": lim["pmax"][i], "P-": -lim["pmin"][i], "Q+": lim["qmax"][i], "Q-": -lim["qmin"][i]}[k]
        return out
    b = bar["bus"]
    sg = -1.0 if k == "V+" else 1.0
    out = sg * D[:kmax + 1, 20 + b].copy()
    out[0] += 1.05 if k == "V+" else -0.95
    return out


def hocbf_rows(D: np.ndarray, coeff: dict[str, Any], lim: dict[str, np.ndarray], lam: float, pset: np.ndarray, qset: np.ndarray):
    """Constraints A v_GFM >= b (eight inputs) for the r = 3 physical barriers and the degree-one GFM reference barriers.

    psi_k = sum_i C(k,i) lam^(k-i) h^(i); membership of C_H needs psi_k >= 0 for k < 3; the constraint is
    sum_{k<3} C(3,k) lam^(3-k) h^(k) + h^(3)_free + A v >= 0 (h^(3)_free: all rates of the non-selected channels at their RDC values, the GFM rates at zero).
    """
    lead = coeff["lead"]
    rows, rhs, meta = [], [], []
    for bar in barrier_table():
        hj = barrier_jets(bar, D, lim)
        kd = bar["kind"]
        if kd == "S":
            i = bar["unit"]
            a_vec = -2.0 * D[0, i] * lead[i] - 2.0 * D[0, 10 + i] * lead[10 + i]
        elif kd in ("P+", "P-"):
            a_vec = (-1.0 if kd == "P+" else 1.0) * lead[bar["unit"]]
        elif kd in ("Q+", "Q-"):
            a_vec = (-1.0 if kd == "Q+" else 1.0) * lead[10 + bar["unit"]]
        else:
            a_vec = (-1.0 if kd == "V+" else 1.0) * lead[20 + bar["bus"]]
        psi = [sum(comb(k, i) * lam ** (k - i) * hj[i] for i in range(k + 1)) for k in range(3)]
        rows.append(a_vec)
        rhs.append(-(sum(comb(3, k) * lam ** (3 - k) * hj[k] for k in range(3)) + hj[3]))
        meta.append({"name": bar["name"], "kind": kd, "h0": float(hj[0]), "psi": [float(x) for x in psi], "psi_min": float(min(psi)), "inside": bool(min(psi) >= 0.0 and hj[0] >= 0.0),
                     "h": [float(x) for x in hj]})
    ref_rows, ref_rhs, ref_meta = [], [], []
    for g in range(4):
        i = 6 + g
        for ch, sg, val, nm in ((i, -1.0, lim["pmax"][i] - pset[i], "Pset+"), (i, 1.0, pset[i] - lim["pmin"][i], "Pset-"), (10 + i, -1.0, lim["qmax"][i] - qset[i], "Qset+"), (10 + i, 1.0, qset[i] - lim["qmin"][i], "Qset-")):
            r_ = np.zeros(8)
            r_[g if ch < 10 else 4 + g] = sg
            ref_rows.append(r_); ref_rhs.append(-lam * val); ref_meta.append({"name": f"{nm}{i}", "h0": float(val), "inside": bool(val >= 0)})
        r_ = np.zeros(8)
        r_[g], r_[4 + g] = -2.0 * pset[i], -2.0 * qset[i]
        hs = lim["smax"][i] ** 2 - pset[i] ** 2 - qset[i] ** 2
        ref_rows.append(r_); ref_rhs.append(-lam * hs); ref_meta.append({"name": f"Sset{i}", "h0": float(hs), "inside": bool(hs >= 0)})
    return np.array(rows), np.array(rhs), meta, np.array(ref_rows), np.array(ref_rhs), ref_meta
