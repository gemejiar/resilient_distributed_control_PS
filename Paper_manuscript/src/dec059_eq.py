"""DEC-059 static stage (0 TDS): equilibrium-selection rule E* and the T2 hypothesis checks for the proposed controller B5' (theory: artifacts/IEEE39_DEC059_theory.md).
  target <OC> <M0|M3|path.json> [bus kind amp]   -> DEC059_state/target_<tag>.npz + .json (exclusive)
E1  plant equilibrium of the RUNNING system (same initialisation as the TDS: plant._make(z) + rdc_state), post-event constant-power load Ppf += amp at the
    event bus (the dist_fn of dec054_runner), one SG rotor angle anchored at its pre-event value; unknowns x_d (PSS-complete dynamic states) and u = (Pset, Qset);
E2  P_i / Pn_i equal for i not in A (zero set of the RDC consensus term with D_P = 1/Pn); i in A pinned at the eps_sel-interior physical limit;
E3  unit-bus |V_i| = V_i(0) for i not in A_Q; i in A_Q: Q_i pinned at the eps_sel-interior limit;
E4  admissibility checked after solving (u* in int W incl. the SG exciter clamp rows, P/Q/S case limits, 39 bus voltages in [0.95, 1.05], no active limiter flag).
Newton with a central-difference Jacobian of the full residual (inner algebraic / quasi-algebraic solve by dec051_core.inner_solve), accepted at |R|_inf <= 1e-10.
T2 checks at the target: closed-loop Jacobian M of plant + RDC (offset constant, so the centered and original Jacobians coincide), its continuous spectrum mod the
common-angle null mode (H5), the sampled-map spectrum with exact ZOH and the explicit reference update (H4), H_r of A_r' H + H A_r = -I on ker l', lambda = 1/(2 lmax(H_r)),
the first-order QP-inactivity radius, and the agreement of the M plant rows with the FD Jacobian of E1 (consistency, level L-a)."""
from __future__ import annotations

import json
import sys
import time

import numpy as np
import scipy.linalg as sla

import dec054_common as C54
import dec055_common as C55
import dec055_oc as OCM
import dec057_static as S
import dec059_b5 as B5

STATE = C54.RUNS_DIR.parent / "DEC059_state"
UNITS = C55.UNITS
EPS_SEL = 0.01
TOL_ROOT = 1e-10
V_BAND = (0.95, 1.05)
H_STEP = C54.DT
ALPHA = B5.ALPHA


def refset(ctx, st):
    """Reference rows of W and the rate box: the pure definition of dec059_b5.refset (shared with the controller)."""
    return B5.refset(ctx["lim"], ctx["n_sg"], st["qn"], UNITS)


margins = B5.margins


class Eq:
    def __init__(self, oc, z):
        self.oc, self.z = oc, np.asarray(z, float)
        self.plant = OCM.make_plant(oc)
        self.system, self.ctx, self.rep = self.plant._make(self.z)
        self.K = self.plant.K
        self.st = self.K.rdc_state(self.system, self.ctx)
        self.u0 = np.concatenate([self.st["pn"], self.st["qn"]])
        self.cache = S._cache_for(self.plant, self.system, self.ctx, self.st, self.u0)
        self.ix = self.K.index_sets(self.system)
        self.d, self.tf = self.ix["d_idx"], self.ix["tf"]
        self.x_full0, self.y_full0 = np.array(self.system.dae.x), np.array(self.system.dae.y)
        self.anchor = int(np.where(self.d == int(np.asarray(self.system.GENROU.delta.a)[0]))[0][0])
        self.V0 = np.asarray(self.system.dae.y[self.st["a_v"]], float).copy()
        self.lim = self.ctx["lim"]

    def apply_load(self, bus, kind, amp):
        k = [int(b) for b in self.system.PQ.bus.v].index(int(bus))
        (self.system.PQ.Ppf if kind == "P" else self.system.PQ.Qpf).v[k] += float(amp)

    def evaluate(self, w):
        sys_ = self.system
        n = len(self.d)
        sys_.dae.x[:] = self.x_work
        sys_.dae.y[:] = self.y_work
        sys_.dae.x[self.d] = w[:n]
        sys_.vars_to_models()
        info = self.K.inner_solve(sys_, self.ctx, self.st, w[n:], self.ix, self.cache, tol=1e-13, itmax=40)
        f, g = self.K.fg_all(sys_)
        y = sys_.dae.y
        out = {"F": f[self.d] / self.tf[self.d], "P": np.asarray(y[self.st["a_p"]], float), "Q": np.asarray(y[self.st["a_q"]], float),
               "V": np.asarray(y[self.st["a_v"]], float), "om": np.asarray(y[self.st["a_f"]], float), "conv": bool(info["converged"]),
               "res_alg": float(info["residual_history"][-1]), "x": np.array(sys_.dae.x), "y": np.array(y)}
        return out

    def residual(self, w, pinP, pinQ):
        e = self.evaluate(w)
        n = len(self.d)
        pn = self.st["pn"]
        free = [i for i in range(10) if i not in pinP]
        r_p = [e["P"][i] / pn[i] - e["P"][free[0]] / pn[free[0]] for i in free[1:]] + [e["P"][i] - pinP[i] for i in pinP]
        r_v = [e["V"][i] - self.V0[i] if i not in pinQ else e["Q"][i] - pinQ[i] for i in range(10)]
        R = np.concatenate([e["F"], r_p, r_v, [w[self.anchor] - self.x_full0[self.d][self.anchor]]])
        return R, e

    def jac(self, w, pinP, pinQ):
        m = len(w)
        J = np.zeros((m, m))
        for k in range(m):
            hk = 1e-7 * max(1.0, abs(w[k]))
            wp, wm = w.copy(), w.copy()
            wp[k] += hk
            wm[k] -= hk
            J[:, k] = (self.residual(wp, pinP, pinQ)[0] - self.residual(wm, pinP, pinQ)[0]) / (2 * hk)
        return J

    def solve(self, pinP, pinQ, w0, itmax=25):
        w = w0.copy()
        hist = []
        J = None
        for it in range(itmax):
            R, e = self.residual(w, pinP, pinQ)
            nr = float(np.abs(R).max())
            hist.append(nr)
            if nr <= TOL_ROOT and e["conv"]:
                return w, e, hist, J
            J = self.jac(w, pinP, pinQ)
            dw = np.linalg.solve(J, -R)
            t = 1.0
            for _ in range(8):                                  # backtracking on |R|_inf
                R2, e2 = self.residual(w + t * dw, pinP, pinQ)
                if e2["conv"] and np.abs(R2).max() < nr:
                    break
                t *= 0.5
            w = w + t * dw
        R, e = self.residual(w, pinP, pinQ)
        hist.append(float(np.abs(R).max()))
        return w, e, hist, J

    def target(self, scenario=None):
        t0 = time.time()
        if scenario is not None and scenario["amp"] != 0.0:
            self.apply_load(scenario["bus"], scenario["kind"], scenario["amp"])
        self.x_work, self.y_work = self.x_full0.copy(), self.y_full0.copy()
        lim = self.lim
        rng = lim["pmax"] - lim["pmin"]
        # eps_sel-interior bands widened to contain the pre-event value (a unit already inside the margin takes no further share toward its limit; d = 0 -> xi(0))
        pn, qn = self.st["pn"], self.st["qn"]
        p_lo, p_hi = np.minimum(lim["pmin"] + EPS_SEL * rng, pn), np.maximum(lim["pmax"] - EPS_SEL * rng, pn)
        qr = lim["qmax"] - lim["qmin"]
        q_lo, q_hi = np.minimum(lim["qmin"] + EPS_SEL * qr, qn), np.maximum(lim["qmax"] - EPS_SEL * qr, qn)
        pinP, pinQ = {}, {}
        w = np.concatenate([self.x_full0[self.d], self.u0])
        log = []
        for rnd in range(12):
            w, e, hist, J = self.solve(pinP, pinQ, w)
            ok = hist[-1] <= TOL_ROOT and e["conv"]
            new = False
            if ok:
                for i in range(10):
                    if i not in pinP and not (p_lo[i] <= e["P"][i] <= p_hi[i]):
                        pinP[i] = float(np.clip(e["P"][i], p_lo[i], p_hi[i]))
                        new = True
                    if i not in pinQ and not (q_lo[i] <= e["Q"][i] <= q_hi[i]):
                        pinQ[i] = float(np.clip(e["Q"][i], q_lo[i], q_hi[i]))
                        new = True
            log.append({"round": rnd, "residual_history": hist, "converged": ok, "pinP": {UNITS[i]: v for i, v in pinP.items()}, "pinQ": {UNITS[i]: v for i, v in pinQ.items()}})
            if not ok or not new:
                break
        self.x_work, self.y_work = e["x"], e["y"]
        n = len(self.d)
        u = w[n:]
        out = {"oc": self.oc, "z": self.z, "scenario": scenario, "rounds": log, "root_residual": hist[-1], "root_ok": bool(ok), "x_d": w[:n], "u": u, "x_full": e["x"], "y_full": e["y"],
               "P": e["P"], "Q": e["Q"], "V": e["V"], "omega": e["om"], "A_set": [UNITS[i] for i in pinP], "AQ_set": [UNITS[i] for i in pinQ], "J_E1": J}
        out.update(self.checks(out))
        out["seconds"] = round(time.time() - t0, 1)
        return out

    def checks(self, T):
        """E4 admissibility and the T2 hypotheses (H1-H5) at the target; system left at the target state."""
        sys_, ctx, st, K = self.system, self.ctx, self.st, self.K
        u, P, Q, V = T["u"], T["P"], T["Q"], T["V"]
        lim = self.lim
        self.evaluate(np.concatenate([T["x_d"], u]))
        K.apply_params(sys_, ctx, st, u)
        vb = np.asarray(sys_.dae.y[np.asarray(sys_.Bus.v.a)], float)
        rs = refset(ctx, st)
        c_aff, c_disc = margins(rs, u)
        flags = S.active_flags(sys_)
        rates = K.rdc_rates(st, ctx, u[:10], u[10:], P, Q, V, T["omega"])          # = offset o of the target (v_nom(xi*) = 0 by construction)
        e4 = {"ref_affine_min": float(c_aff.min()), "ref_affine_argmin": rs["names"][int(c_aff.argmin())], "ref_disc_min": float(c_disc.min()),
              "P_to_pmax_min": float((lim["pmax"] - P).min()), "P_to_pmin_min": float((P - lim["pmin"]).min()), "Q_to_qmax_min": float((lim["qmax"] - Q).min()),
              "Q_to_qmin_min": float((Q - lim["qmin"]).min()), "S_margin_min": float((lim["smax"] - np.hypot(P, Q)).min()), "V_bus_min": float(vb.min()), "V_bus_max": float(vb.max()),
              "active_flags": [f for f in flags if not f.startswith("PV.")], "omega_minus_1_max": float(np.abs(T["omega"] - 1).max()),
              "unit_V_minus_V0_max": float(np.abs(V - self.V0).max()), "P_minus_Pset_max": float(np.abs(P - u[:10]).max())}
        e4["pass"] = bool(c_aff.min() > 0 and c_disc.min() > 0 and e4["P_to_pmax_min"] >= 0 and e4["P_to_pmin_min"] >= 0 and e4["Q_to_qmax_min"] >= 0 and e4["Q_to_qmin_min"] >= 0
                          and e4["S_margin_min"] >= 0 and vb.min() >= V_BAND[0] and vb.max() <= V_BAND[1] and not e4["active_flags"])
        b, vn, _ = S.closed_loop(self.plant, sys_, ctx, st, u)
        M, n = b["M"], b["n_dyn"]
        assert n == len(self.d)
        ev, Wr = np.linalg.eig(M)
        j0 = int(np.argmin(np.abs(ev)))
        evl, Wl = np.linalg.eig(M.T)
        k0 = int(np.argmin(np.abs(evl)))
        r = np.real(Wr[:, j0])
        l = np.real(Wl[:, k0])
        l = l / (l @ r)
        rest = np.delete(ev, j0)
        U = sla.null_space(l[None, :])
        Ar = U.T @ M @ U
        inv_err = float(np.abs(M @ U - U @ Ar).max() / np.abs(M).max())
        Hr = sla.solve_continuous_lyapunov(Ar.T, -np.eye(Ar.shape[0]))
        Hr = 0.5 * (Hr + Hr.T)
        lyap_res = float(np.abs(Ar.T @ Hr + Hr @ Ar + np.eye(Ar.shape[0])).max())
        eh = np.linalg.eigvalsh(Hr)
        lam = 1.0 / (2.0 * eh.max())
        ed = S.discrete_spectrum(M, n, H_STEP)
        jd = int(np.argmin(np.abs(ed)))
        drest = np.delete(ed, jd)
        # first-order QP-inactivity radius (estimate, not a certificate): v_nom ~ Kv e with Kv = M[n:, :]
        Kv = M[n:, :]
        Ea = np.hstack([np.zeros((rs["A"].shape[0], n)), rs["A"]])
        r_aff = ALPHA * c_aff / (np.linalg.norm(rs["A"] @ Kv, axis=1) + ALPHA * np.linalg.norm(Ea, axis=1))
        r_box = rs["vbar"] / np.linalg.norm(Kv, axis=1)
        fd = None
        if T.get("J_E1") is not None:
            Jx = T["J_E1"][:n, :]
            fd = {"max_abs_diff_plant_rows": float(np.abs(Jx - M[:n, :]).max()), "max_abs_M_plant_rows": float(np.abs(M[:n, :]).max())}
        h = {"H1_root": {"residual": T["root_residual"], "pass": bool(T["root_ok"])},
             "H2_smooth": {"active_flags": e4["active_flags"], "pass": not e4["active_flags"]},
             "H3_interior": {"ref_affine_min": e4["ref_affine_min"], "ref_disc_min": e4["ref_disc_min"], "pass": bool(c_aff.min() > 0 and c_disc.min() > 0)},
             "H4_sampled": {"max_re_equiv_rate_excl_null": float(drest.real.max()), "rho_q": float(np.exp(H_STEP * drest.real.max())), "null_rate": [float(ed[jd].real), float(ed[jd].imag)],
                            "pass": bool(drest.real.max() < 0)},
             "H5_continuous": {"null_eig": [float(ev[j0].real), float(ev[j0].imag)], "rightmost_excl_null": sorted([[float(a.real), float(a.imag)] for a in rest], key=lambda q: -q[0])[:6],
                               "pass": bool(rest.real.max() < 0)}}
        clf = {"lambda": float(lam), "Hr_eig_min": float(eh.min()), "Hr_eig_max": float(eh.max()), "lyap_residual": lyap_res, "invariance_error_rel": inv_err, "dim": int(Ar.shape[0])}
        radii = {"r_QP_affine_min": float(r_aff.min()), "r_QP_affine_argmin": rs["names"][int(r_aff.argmin())], "r_QP_box_min": float(r_box.min()), "r_QP": float(min(r_aff.min(), r_box.min())),
                 "note": "first-order estimates in the full (x_d, u) Euclidean norm; not certificates"}
        return {"E4": e4, "T2": h, "clf": clf, "radii": radii, "fd_check": fd, "offset": rates, "rates_check_vnom_at_target": 0.0,
                "M": M, "n_dyn": n, "r_null": r, "l_null": l, "U": U, "Hr": Hr, "refset_names": rs["names"]}


def save_target(tag, T):
    STATE.mkdir(parents=True, exist_ok=True)
    arrays = {k: np.asarray(T[k]) for k in ("x_d", "u", "x_full", "y_full", "P", "Q", "V", "omega", "offset", "M", "r_null", "l_null", "U", "Hr", "z")}
    with open(STATE / f"target_{tag}.npz", "xb") as f:
        np.savez_compressed(f, **arrays, lam=T["clf"]["lambda"], n_dyn=T["n_dyn"])
    js = {k: v for k, v in T.items() if k not in arrays and k not in ("J_E1",)}
    with open(STATE / f"target_{tag}.json", "x", encoding="utf-8") as f:
        json.dump(js, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else (float(o) if np.isscalar(o) else str(o)))
    return STATE / f"target_{tag}.npz"


def dispatch(oc, m):
    if m == "M3CUT":                                                 # DEC-059 R4 single dynamic cut cycle (static design; TDS recheck pending)
        s = json.loads((STATE / f"m3os_cut_{oc}.json").read_text(encoding="utf-8"))
        return np.array(s["z"]), m
    if m == "M3OS":                                                  # DEC-059 R4 M3 with the overshoot term
        s = json.loads((STATE / f"m3os_{oc}.json").read_text(encoding="utf-8"))
        return np.array(s["z"]), m
    if m.endswith(".json"):
        s = json.loads(open(m, encoding="utf-8").read())
        return np.array(s["z"]), m
    return S.dispatch(oc, m)[0], m


def main(oc, m, bus=None, kind=None, amp=None):
    z, src = dispatch(oc, m)
    sc = None if bus is None else {"bus": int(bus), "kind": kind, "amp": float(amp)}
    E = Eq(oc, z)
    T = E.target(sc)
    # rule revision r2 (E2/E3 bands contain the pre-event value); target_OC1_M0_d0.* of revision 1 is kept as superseded
    tag = f"r2_{oc}_{m if not m.endswith('.json') else 'custom'}_" + ("d0" if sc is None or sc["amp"] == 0 else f"b{sc['bus']}{sc['kind']}_{sc['amp']:.5f}")
    p = save_target(tag, T)
    print(tag, {"root": T["root_residual"], "rounds": len(T["rounds"]), "A": T["A_set"], "AQ": T["AQ_set"], "E4": T["E4"]["pass"],
                "T2": {k: v["pass"] for k, v in T["T2"].items()}, "H4": T["T2"]["H4_sampled"]["max_re_equiv_rate_excl_null"], "H5": T["T2"]["H5_continuous"]["rightmost_excl_null"][:2],
                "lam": T["clf"]["lambda"], "r_QP": T["radii"]["r_QP"], "fd": T["fd_check"], "s": T["seconds"]}, flush=True)
    return p


if __name__ == "__main__":
    if sys.argv[1] == "target":
        main(*sys.argv[2:])
