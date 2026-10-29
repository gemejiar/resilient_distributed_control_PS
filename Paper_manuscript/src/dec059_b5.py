"""DEC-059 proposed controller B5' (theory: artifacts/IEEE39_DEC059_theory.md, section 2; protocol ops/sted/DEC059_protocol.md).
Pure part (no ANDES import at module level, unit-tested by test_dec059.py):
  refset           reference rows of W: c1..c4 (P/Q boxes, all units), c6/c7 (SG exciter clamp), c5 discs, rate box vbar
  hard_ok, theta   exact check of (Q1)-(Q3) and the largest feasible scaling of a command (T1-F: theta = 1 at v = 0)
  solve_qp         min 1/2 (v - v_nom)' R (v - v_nom) + 1/2 rho_s s^2  s.t. (Q1)-(Q3) and the soft CLF row (Q4); cone QP (kvxopt.coneqp);
                   fast path: v_nom is returned when it satisfies every row with s = 0 (then it is the unique minimiser)
  schedule         A-INFO: target validity and offset choice versus time
ANDES part: make_filter(r) builds the qp_filter of run_b3_ieee39.run (mode B3, so the pre-event offset is v_RDC(xi(0)) = v_RDC(xi*(d-))).
Parameters (protocol, declared before the smoke): vbar = 0.01 Sn/100 pu/s, alpha = 1/s (gamma = alpha h), R = diag(vbar^-2), rho_s = 1e6 (CLF row normalised
by the norm of its v-gradient), tau_info = 1 s."""
from __future__ import annotations

import time

import numpy as np

ALPHA = 1.0
RHO_S = 1.0e6
VBAR_FRAC = 0.01
TAU_INFO = 1.0
KAPPA_SG, Z_CLAMP = 0.06, 0.10          # run_e8_ieee39.KAPPA_SG, Z_CLAMP (checked against the module in make_filter)


def refset(lim, n_sg, qn, units=None, kappa=KAPPA_SG, zclamp=Z_CLAMP):
    n = len(lim["pmax"])
    units = units or [str(i) for i in range(n)]
    A, b, names = [], [], []
    for i in range(n):
        for sgn, off, tag, k in ((-1, lim["pmax"][i], "pmax", i), (1, -lim["pmin"][i], "pmin", i), (-1, lim["qmax"][i], "qmax", n + i), (1, -lim["qmin"][i], "qmin", n + i)):
            row = np.zeros(2 * n)
            row[k] = sgn
            A.append(row), b.append(off), names.append(f"{tag} {units[i]}")
        if i < n_sg:                                    # c6 = zq - (Q - Qn) = -Q + (zq + Qn);  c7 = zq + (Q - Qn) = Q + (zq - Qn)
            zq = zclamp / kappa
            for sgn, off, tag in ((-1, zq + qn[i], "zclamp+"), (1, zq - qn[i], "zclamp-")):
                row = np.zeros(2 * n)
                row[n + i] = sgn
                A.append(row), b.append(off), names.append(f"{tag} {units[i]}")
    s = np.asarray(lim["smax"], float)
    return {"A": np.array(A), "b": np.array(b, float), "names": names, "s": s, "n": n, "vbar": VBAR_FRAC * np.concatenate([s, s])}


def margins(rs, u):
    n = rs["n"]
    return rs["A"] @ u + rs["b"], rs["s"] ** 2 - u[:n] ** 2 - u[n:] ** 2


def hard_ok(rs, u, v, h, alpha=ALPHA, tol=0.0):
    """(Q1)-(Q3) evaluated in the 'next value' form c(u + h v) >= (1 - gamma) c(u); tol is an absolute slack used only by the tests."""
    g = alpha * h
    n = rs["n"]
    if np.any(np.abs(v) > rs["vbar"] + tol):
        return False
    ca, cd = margins(rs, u)
    un = u + h * v
    ca2, cd2 = margins(rs, un)
    return bool(np.all(ca2 >= (1 - g) * ca - tol) and np.all(cd2 >= (1 - g) * cd - tol))


def theta(rs, u, v, h, alpha=ALPHA):
    """Largest t in [0, 1] with t v satisfying (Q1)-(Q3) (convex rows, all satisfied at t = 0 when u is in W: T1-F)."""
    n = rs["n"]
    t = 1.0
    av = np.abs(v)
    k = av > 0
    if k.any():
        t = min(t, float((rs["vbar"][k] / av[k]).min()))
    ca, cd = margins(rs, u)
    Av = rs["A"] @ v
    k = Av < 0
    if k.any():
        t = min(t, float((alpha * np.maximum(ca[k], 0.0) / (-Av[k])).min()))
    g = alpha * h
    for i in range(n):
        ui, vi = np.array([u[i], u[n + i]]), np.array([v[i], v[n + i]])
        R2 = rs["s"][i] ** 2 - (1 - g) * max(cd[i], 0.0)
        a, bq, c = h * h * (vi @ vi), 2 * h * (ui @ vi), ui @ ui - R2
        if a > 0:
            disc = bq * bq - 4 * a * c
            root = (-bq + np.sqrt(max(disc, 0.0))) / (2 * a)
            t = min(t, max(root, 0.0))
    return max(0.0, t)


def schedule(t, t_e, tau, event):
    """A-INFO.  Returns (target, valid): target 'pre' or 'post'; valid False on [t_e, t_e + tau) of an event run (the CLF row is dropped there)."""
    if not event or t < t_e:
        return "pre", True
    if t < t_e + tau:
        return "pre", False
    return "post", True


def solve_qp(rs, u, vnom, h, clf=None, alpha=ALPHA, rho_s=RHO_S, force_solver=False):
    """clf = (g, bc): row g'v <= bc + s (already in the normalised form).  Returns v, s, info."""
    n2 = 2 * rs["n"]
    vbar = rs["vbar"]
    R = 1.0 / vbar ** 2
    if not force_solver and hard_ok(rs, u, vnom, h, alpha) and (clf is None or float(clf[0] @ vnom) <= clf[1]):
        return vnom.copy(), 0.0, {"path": 0}
    from kvxopt import matrix, solvers
    solvers.options.update({"show_progress": False, "abstol": 1e-11, "reltol": 1e-11, "feastol": 1e-11, "maxiters": 100})
    nv = n2 + (1 if clf is not None else 0)
    P = np.zeros((nv, nv))
    P[:n2, :n2] = np.diag(R)
    q = np.zeros(nv)
    q[:n2] = -R * vnom
    if clf is not None:
        P[n2, n2] = rho_s
    Gl, hl = [], []
    I = np.eye(n2)
    for i in range(n2):
        Gl.append(np.r_[I[i], np.zeros(nv - n2)]), hl.append(vbar[i])
        Gl.append(np.r_[-I[i], np.zeros(nv - n2)]), hl.append(vbar[i])
    ca, cd = margins(rs, u)
    for j in range(rs["A"].shape[0]):
        Gl.append(np.r_[-rs["A"][j], np.zeros(nv - n2)]), hl.append(alpha * ca[j])
    if clf is not None:
        Gl.append(np.r_[clf[0], -1.0]), hl.append(clf[1])
        Gl.append(np.r_[np.zeros(n2), -1.0]), hl.append(0.0)
    Gq, hq = [], []
    g = alpha * h
    n = rs["n"]
    for i in range(n):
        r_i = np.sqrt(rs["s"][i] ** 2 - (1 - g) * cd[i])
        rows = np.zeros((3, nv))
        rows[1, i] = -h
        rows[2, n + i] = -h
        Gq.append(rows), hq.append([r_i, u[i], u[n + i]])
    G = np.vstack([np.array(Gl)] + Gq)
    hh = np.concatenate([np.array(hl)] + [np.array(x) for x in hq])
    dims = {"l": len(hl), "q": [3] * n, "s": []}
    t0 = time.perf_counter()
    try:
        sol = solvers.coneqp(matrix(P), matrix(q), matrix(G), matrix(hh), dims)
        ok = sol["status"] == "optimal"
        w = np.array(sol["x"]).ravel()
    except (ValueError, ArithmeticError):
        ok, w = False, None
    dt = time.perf_counter() - t0
    if not ok:
        th = theta(rs, u, vnom, h, alpha)
        return th * vnom, 0.0, {"path": 2, "theta": th, "solver_s": dt}
    v, s = w[:n2], (float(w[n2]) if clf is not None else 0.0)
    th = theta(rs, u, v, h, alpha)
    if th < 1.0:                                       # interior-point solution marginally outside a row: scale toward 0 (exact by convexity, T1-F)
        v = th * v * (1 - 1e-12)
    return v, max(s, 0.0), {"path": 1, "theta": th, "solver_s": dt}


# ------------------------------------------------------------------------------------------------------------------------------- ANDES-side filter
class InfoInconsistent(RuntimeError):
    pass


class Filter:
    def __init__(self, r):
        cfg = r["b5"]
        self.cfg = cfg
        self.pre = dict(np.load(cfg["pre_target"]))
        self.post = dict(np.load(cfg["post_target"])) if cfg.get("post_target") else None
        self.event = bool(cfg.get("event", self.post is not None))
        self.t_e, self.tau = float(cfg.get("t_e", 5.0)), float(cfg.get("tau_info", TAU_INFO))
        self.init = False
        self.switched = False
        self.log = {k: [] for k in ("t", "path", "slack", "V", "c_min", "dv", "cpu", "valid", "v")}
        self.n_solver_fail = 0
        self.spec = {"fn": self.fn, "also_before_event": False}

    def _clfdata(self, T):
        n = int(T["n_dyn"])
        pd = bool(np.linalg.eigvalsh(T["Hr"]).min() > 0)    # K = K_nom does not stabilise A_r -> H_r indefinite: CLF_NOT_CONSTRUCTIBLE, row dropped (main.tex: K must be stabilising)
        return {"x": T["x_d"], "u": T["u"], "r": T["r_null"], "l": T["l_null"], "U": T["U"], "H": T["Hr"], "lam": float(T["lam"]), "n": n, "off": T["offset"], "pd": pd}

    def _first(self, sys_, ctx, st):
        import dec051_core as K
        import run_e8_ieee39 as e8
        if (e8.KAPPA_SG, e8.Z_CLAMP) != (KAPPA_SG, Z_CLAMP):
            raise InfoInconsistent("actuator constants differ from the B5' declaration")
        ix = K.index_sets(sys_)
        self.d, self.tf = ix["d_idx"], ix["tf"]
        self.rs = refset(ctx["lim"], ctx["n_sg"], st["qn"])
        self.cp = self._clfdata(self.pre)
        self.cq = self._clfdata(self.post) if self.post is not None else None
        x = np.asarray(sys_.dae.x, float)[self.d]
        u = np.concatenate([st["pset"], st["qset"]])
        chk = {"x_vs_pre_target": float(np.abs(x - self.cp["x"]).max()), "u_vs_pre_target": float(np.abs(u - self.cp["u"]).max()),
               "offset_vs_B3_pre": float(np.abs(np.concatenate([st["off_p"], st["off_q"]]) - self.cp["off"]).max())}
        if self.cq is not None:
            chk["post_target_same_dispatch"] = float(np.abs(self.post["z"] - self.pre["z"]).max())
        self.consistency = chk
        if chk["x_vs_pre_target"] > 1e-6 or chk["u_vs_pre_target"] > 1e-9 or chk["offset_vs_B3_pre"] > 1e-9 or chk.get("post_target_same_dispatch", 0.0) > 0:
            raise InfoInconsistent(f"supervisory target inconsistent with the running system: {chk}")
        self.init = True

    def clf_row(self, c, sys_, u):
        x = np.asarray(sys_.dae.x, float)[self.d]
        xdot = np.asarray(sys_.dae.f, float)[self.d] / self.tf[self.d]
        e = np.concatenate([x - c["x"], u - c["u"]])
        pe = e - c["r"] * (c["l"] @ e)
        eh = c["U"].T @ pe
        He = c["H"] @ eh
        V = float(eh @ He)
        w = 2.0 * (c["U"] @ He)
        w = w - c["l"] * (c["r"] @ w)                   # gradient of V(e) = (U' P e)' H (U' P e) with P = I - r l'  ->  P' U 2 H eh
        n = c["n"]
        gv, gx = w[n:], w[:n]
        bc = -c["lam"] * V - float(gx @ xdot)
        nrm = float(np.linalg.norm(gv))
        if nrm == 0.0:
            return None, V
        return (gv / nrm, bc / nrm), V

    def fn(self, t, sys_, ctx, st, vnom_p, vnom_q):
        c0 = time.perf_counter()
        if not self.init:
            self._first(sys_, ctx, st)
        which, valid = schedule(t, self.t_e, self.tau, self.event)
        vnom = np.concatenate([vnom_p, vnom_q])
        if which == "post" and not self.switched:
            old = np.concatenate([st["off_p"], st["off_q"]])
            new = self.cq["off"]
            st["off_p"], st["off_q"] = new[:10].copy(), new[10:].copy()
            vnom = vnom + old - new
            self.switched = True
        c = self.cq if which == "post" else self.cp
        u = np.concatenate([st["pset"], st["qset"]])
        h = float(ctx["h"])
        clf, V = (self.clf_row(c, sys_, u) if valid and c["pd"] else (None, np.nan))
        v, s, info = solve_qp(self.rs, u, vnom, h, clf)
        if info["path"] == 2:
            self.n_solver_fail += 1
        ca, cd = margins(self.rs, u)
        for k, val in (("t", t), ("path", info["path"]), ("slack", s), ("V", V), ("c_min", min(ca.min(), cd.min())), ("dv", float(np.abs(v - vnom).max())),
                       ("cpu", time.perf_counter() - c0), ("valid", float(valid))):
            self.log[k].append(val)
        self.log["v"].append(v.astype(np.float32))
        return v[:10], v[10:]

    def log_arrays(self):
        return {f"b5_{k}": np.asarray(v) for k, v in self.log.items()}

    def summary(self):
        L = {k: np.asarray(v) for k, v in self.log.items() if k != "v"}
        if not len(L["t"]):
            return {"b5": "filter never called"}
        return {"b5": {"calls": int(len(L["t"])), "fast_path": int((L["path"] == 0).sum()), "solver": int((L["path"] == 1).sum()), "fallback": int((L["path"] == 2).sum()),
                       "slack_max": float(np.nanmax(L["slack"])), "slack_positive_calls": int((L["slack"] > 1e-12).sum()), "c_min_over_run": float(L["c_min"].min()),
                       "cpu_mean_s": float(L["cpu"].mean()), "cpu_max_s": float(L["cpu"].max()), "consistency": self.consistency, "switched_to_post": self.switched,
                       "V_last": float(L["V"][-1]) if np.isfinite(L["V"][-1]) else None,
                       "clf_constructible": {"pre": self.cp["pd"], "post": None if self.cq is None else self.cq["pd"]}}}


class FilterNoCLF(Filter):
    """B4' (comparator, main.tex 'nominal controller with a barrier-only filter'): B5' with the CLF row (Q4) removed; everything else identical."""

    def clf_row(self, c, sys_, u):
        return None, np.nan


class B1s:
    """B1s (comparator, main.tex 'conventional separately saturated integral controller'; declared before the R5 plan):
        v_P,i = k_i (1 - omega_i),  k_i = 160 Pn_i / sum Pn  (same total integral speed as B2, run_e8_ieee39.SPEED_TARGET; sharing proportional to Pn)
        v_Q,i = K_IQ K_V (V_i(0) - V_i)  (E8 gains 0.3 x 1.0; target = the dispatch unit-bus voltage, the same target as B5')
    no communication, no capability factors, no leakage; each reference clamped separately to its box (P in [pmin, pmax]; Q in [qmin, qmax] and, for SG,
    inside the exciter clamp range) by clipping u + h v (anti-windup).  The apparent-power disc is NOT enforced (conventional separate saturation)."""

    def __init__(self, r):
        self.init = False
        self.log = {k: [] for k in ("t", "clipped", "c_min", "cpu", "v")}
        self.spec = {"fn": self.fn, "also_before_event": False}

    def fn(self, t, sys_, ctx, st, vnom_p, vnom_q):
        c0 = time.perf_counter()
        y = sys_.dae.y
        if not self.init:
            import run_e8_ieee39 as e8
            self.V0 = np.asarray(y[st["a_v"]], float).copy()
            self.k = e8.SPEED_TARGET * st["pn"] / st["pn"].sum()
            self.kq = e8.K_IQ * e8.K_V
            lim, n_sg = ctx["lim"], ctx["n_sg"]
            zq = e8.Z_CLAMP / e8.KAPPA_SG
            qlo, qhi = lim["qmin"].copy(), lim["qmax"].copy()
            qlo[:n_sg] = np.maximum(qlo[:n_sg], st["qn"][:n_sg] - zq)
            qhi[:n_sg] = np.minimum(qhi[:n_sg], st["qn"][:n_sg] + zq)
            self.lo, self.hi = np.concatenate([lim["pmin"], qlo]), np.concatenate([lim["pmax"], qhi])
            self.rs = refset(lim, n_sg, st["qn"])
            self.init = True
        om, V = np.asarray(y[st["a_f"]], float), np.asarray(y[st["a_v"]], float)
        v = np.concatenate([self.k * (1.0 - om), self.kq * (self.V0 - V)])
        u = np.concatenate([st["pset"], st["qset"]])
        h = float(ctx["h"])
        un = np.clip(u + h * v, self.lo, self.hi)
        vc = (un - u) / h
        ca, cd = margins(self.rs, u)
        for k, val in (("t", t), ("clipped", int((np.abs(vc - v) > 0).sum())), ("c_min", min(ca.min(), cd.min())), ("cpu", time.perf_counter() - c0)):
            self.log[k].append(val)
        self.log["v"].append(vc.astype(np.float32))
        return vc[:10], vc[10:]

    def log_arrays(self):
        return {f"b1s_{k}": np.asarray(v) for k, v in self.log.items()}

    def summary(self):
        L = {k: np.asarray(v) for k, v in self.log.items() if k != "v"}
        return {"b1s": {"calls": int(len(L["t"])), "clipped_calls": int((L["clipped"] > 0).sum()), "c_min_over_run": float(L["c_min"].min()) if len(L["c_min"]) else None,
                        "cpu_mean_s": float(L["cpu"].mean()) if len(L["cpu"]) else None}}


def make_filter(r):
    kind = r.get("controller", "B5P")
    return {"B5P": Filter, "B4P": FilterNoCLF, "B1S": B1s}[kind](r)
