"""DEC-054 preventive OPF core: M0-M3 and Algorithm 1 (multi-contingency adaptive constraint separation, v2 sec 2.6-2.8, 4).

Plant-agnostic: the plant adapter supplies evaluate(z), jump(z,d), excursion(z,d) (see dec054_plant.py for ANDES, dec054_synth.py for the synthetic test plant).
Solver: scipy SLSQP (local; every outcome is at most LOCAL_OPTIMUM_FOUND / FEASIBLE_PREDICTED, never a global-optimum claim).
Margins (upper):  M+ = Pmax_i - P-_i(z) - dP_jump_{i,d}(z) - E+_{i,d}(z) - eps_J_i - eps_E_i
         (lower):  M- = P-_i(z) + dP_jump_{i,d}(z) - Pmin_i - E-_{i,d}(z) - eps_J_i - eps_E_i       (signed jump on both sides; v2's min(0, dP) is replaced)
M2 uses E=0 and eps_J only; M3 uses everything; M0 none; M1 static R_i >= rho (Pmax_i - Pmin_i)."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import minimize, nnls

from dec054_common import N_PV, N_V, N_Z, PROPOSED, PV_IDX, VHI, VLO

NU = 10


@dataclass(frozen=True)
class Scenario:
    name: str
    bus: int
    kind: str            # "P" or "Q"
    amp: float           # pu on system base


@dataclass
class OPFResult:
    method: str
    status: str
    z: np.ndarray | None
    J: float | None
    iterations: int
    cuts: list = field(default_factory=list)
    log: list = field(default_factory=list)
    margins: dict | None = None
    detail: str = ""
    kkt_residual: float | None = None
    solver_calls: int = 0


class Problem:
    def __init__(self, plant, mode: str, scenarios: list, eps_J=None, eps_E=None, rho: float = 0.0, cfg: dict | None = None, kappa_pat: float | None = None):
        assert mode in ("M0", "M1", "M2", "M3")
        self.plant, self.mode, self.sc, self.cfg = plant, mode, list(scenarios), dict(PROPOSED if cfg is None else cfg)
        self.eps_J = np.zeros(NU) if eps_J is None else np.asarray(eps_J, float)
        self.eps_E = np.zeros(NU) if eps_E is None else np.asarray(eps_E, float)
        self.rho = rho
        self.lim = plant.limits
        ref = plant.evaluate(plant.z_ref)
        assert ref["ok"], "reference dispatch must initialise"
        self.P_ref, self.Q_ref = ref["P"], ref["Q"]
        self.pi_p = self.P_ref / self.P_ref.sum()                       # frozen design shares (a priori, from z_ref)
        self.q_rng = self.lim["qmax"] - self.lim["qmin"]
        self.pi_q = self.Q_ref / self.q_rng
        self.p_scale = (self.lim["pmax"] - self.lim["pmin"])[PV_IDX]
        self._cache: dict = {}
        self.dyn_cuts: list = []
        self.calls = 0

    # ---------------------------------------------------------------- objective (identical for M0-M3; non-degenerate)
    def C_disp(self, z):
        p0, v0 = z[:N_PV], z[N_PV:]
        pr, vr = self.plant.z_ref[:N_PV], self.plant.z_ref[N_PV:]
        return float(np.sum(((p0 - pr) / self.p_scale) ** 2) + np.sum(((v0 - vr) / self.cfg["v_scale_pu"]) ** 2))

    def C_pat(self, z):
        e = self.plant.evaluate(z)
        if not e["ok"]:
            return 1e3
        return float(np.sum((e["P"] / e["P"].sum() - self.pi_p) ** 2) + np.sum((e["Q"] / self.q_rng - self.pi_q) ** 2))

    def J(self, z):
        return self.C_disp(z) + self.cfg["lambda_pat"] * self.C_pat(z)

    # ---------------------------------------------------------------- constraints
    def base(self, z):
        e = self.plant.evaluate(z)
        if not e["ok"]:
            return -1e3 * np.ones(2 * 39 + 5 * NU)
        P, Q, V, lim = e["P"], e["Q"], e["V"], self.lim
        S = np.hypot(P, Q)
        floor = np.maximum(lim["pmin"], self.cfg["P_floor_pu"])
        return np.concatenate([V - VLO, VHI - V, P - floor, lim["pmax"] - P, Q - lim["qmin"], lim["qmax"] - Q, lim["smax"] - S])

    def margins_d(self, z, d_idx):
        """(10 upper, 10 lower) design margins for scenario d at z; M2: jump only; M3: jump + excursion."""
        key = (tuple(np.round(z, 12)), d_idx, self.mode in ("M2", "M3"), self.mode)
        if key in self._cache:
            return self._cache[key]
        self.calls += 1
        sc = self.sc[d_idx]
        e = self.plant.evaluate(z)
        j = self.plant.jump(z, sc)
        if not (e["ok"] and j["ok"]):
            out = (-1e3 * np.ones(NU), -1e3 * np.ones(NU), {"ok": False})
            self._cache[key] = out
            return out
        dP = j["dP"]
        if self.mode == "M3":
            x = self.plant.excursion(z, sc)
            Eup, Edn = x["E_up"], x["E_dn"]
            epsE = self.eps_E
        else:
            Eup = Edn = np.zeros(NU)
            epsE = np.zeros(NU)
        lim = self.lim
        up = lim["pmax"] - e["P"] - dP - Eup - self.eps_J - epsE
        dn = e["P"] + dP - lim["pmin"] - Edn - self.eps_J - epsE
        for c in self.dyn_cuts:      # local empirical corrections (P3-B): only inside their trust region
            if c["d"] == d_idx and np.max(np.abs(z - c["z_c"]) / c["r"]) <= 1.0:
                (up if c["cls"] == "P+" else dn)[c["i"]] -= c["delta"]
        out = (up, dn, {"ok": True})
        self._cache[key] = out
        return out

    def constraints(self, z, W=()):
        parts = [self.base(z)]
        if self.mode == "M1":
            e = self.plant.evaluate(z)
            lim = self.lim
            parts.append((lim["pmax"] - e["P"]) - self.rho * (lim["pmax"] - lim["pmin"]) if e["ok"] else -1e3 * np.ones(NU))
        if self.mode in ("M2", "M3"):
            vals = []
            for (d, i, cls) in sorted(W):
                up, dn, _ = self.margins_d(z, d)
                vals.append((up if cls == "P+" else dn)[i])
            if vals:
                parts.append(np.array(vals))
        return np.concatenate(parts)

    def all_margins(self, z):
        return {d: self.margins_d(z, d) for d in range(len(self.sc))}

    def most_violated(self, z):
        worst = (np.inf, None)
        for d in range(len(self.sc)):
            up, dn, info = self.margins_d(z, d)
            for cls, arr in (("P+", up), ("P-", dn)):
                i = int(np.argmin(arr))
                if arr[i] < worst[0]:
                    worst = (float(arr[i]), (d, i, cls))
        return worst


# --------------------------------------------------------------------------- NLP
def _bounds(plant, z_c=None, r=None):
    lo, hi = np.array(plant.z_lo, float), np.array(plant.z_hi, float)
    if z_c is not None:
        lo, hi = np.maximum(lo, z_c - r), np.minimum(hi, z_c + r)
    return list(zip(lo, hi))


def kkt_residual(problem: Problem, z, W, tol_active: float = 1e-6, h: float = 1e-6):
    """Approximate KKT residual of the working-set NLP: min ||grad J - sum lam_k grad g_k||, lam >= 0, over active inequalities and active bounds (finite differences)."""
    n = len(z)

    def grad(fun):
        g0 = np.atleast_1d(fun(z))
        G = np.zeros((g0.size, n))
        for k in range(n):
            zz = z.copy()
            zz[k] += h
            G[:, k] = (np.atleast_1d(fun(zz)) - g0) / h
        return g0, G

    gJ = grad(lambda x: np.array([problem.J(x)]))[1][0]
    c0, Gc = grad(lambda x: problem.constraints(x, W))
    act = np.where(c0 <= tol_active)[0]
    rows = [Gc[k] for k in act]
    lo = np.array(problem.plant.z_lo)
    hi = np.array(problem.plant.z_hi)
    for k in range(n):
        if z[k] - lo[k] <= 1e-8:
            e = np.zeros(n); e[k] = 1.0; rows.append(e)
        if hi[k] - z[k] <= 1e-8:
            e = np.zeros(n); e[k] = -1.0; rows.append(e)
    if not rows:
        return float(np.linalg.norm(gJ)), 0
    Amat = np.array(rows).T
    lam, rn = nnls(Amat, gJ)
    return float(rn), len(rows)


def solve_nlp(problem: Problem, W, z0, z_c=None, r=None):
    cons = [{"type": "ineq", "fun": lambda z: problem.constraints(z, W)}]
    try:
        res = minimize(problem.J, np.asarray(z0, float), method="SLSQP", bounds=_bounds(problem.plant, z_c, r), constraints=cons,
                       options={"maxiter": problem.cfg["N_it"], "ftol": 1e-10})
    except Exception as ex:        # solver exception: never read as infeasibility
        return {"ok": False, "kind": "SOLVER_FAILED", "z": np.asarray(z0, float), "msg": repr(ex)}
    z = np.asarray(res.x, float)
    c = problem.constraints(z, W)
    viol = float(-min(0.0, c.min()))
    if res.status == 4:
        return {"ok": False, "kind": "INFEASIBLE_NOT_DEMONSTRATED", "z": z, "msg": res.message, "viol": viol}
    if not res.success and viol > problem.cfg["tau_cut_pu"]:
        return {"ok": False, "kind": "SOLVER_FAILED", "z": z, "msg": res.message, "viol": viol}
    return {"ok": True, "z": z, "msg": res.message, "viol": viol, "nit": int(res.nit)}


def initial_working_set(problem: Problem, k0: int = 2):
    """D_0: the k0 scenarios with the largest STATIC jump-only exceedance at z_ref (rule, no TDS data); all units, both sides."""
    z = problem.plant.z_ref
    sev = []
    for d, sc in enumerate(problem.sc):
        e, j = problem.plant.evaluate(z), problem.plant.jump(z, sc)
        sev.append(float(np.max(j["dP"] - (problem.lim["pmax"] - e["P"]))))
    order = list(np.argsort(sev)[::-1][:k0])
    W = set()
    for d in order:
        for i in range(NU):
            W.add((int(d), i, "P+"))
            W.add((int(d), i, "P-"))
    return W


def algorithm1(plant, mode: str, scenarios: list, eps_J, eps_E, cfg: dict | None = None, z_seeds=None, k0: int = 2) -> OPFResult:
    """Algorithm 1 for M2/M3; exit states per OPF_STATUS (no success guarantee).  Any exception raised by the plant/predictor is SOLVER_FAILED
    (never read as infeasibility)."""
    assert mode in ("M2", "M3")
    try:
        return _algorithm1(plant, mode, scenarios, eps_J, eps_E, cfg, z_seeds, k0)
    except Exception as ex:
        return OPFResult(mode, "SOLVER_FAILED", None, None, 0, detail=repr(ex))


def _algorithm1(plant, mode, scenarios, eps_J, eps_E, cfg, z_seeds, k0) -> OPFResult:
    pb = Problem(plant, mode, scenarios, eps_J, eps_E, cfg=cfg)
    cfg = pb.cfg
    W = initial_working_set(pb, k0)
    res = OPFResult(mode, "ITERATION_BUDGET_EXHAUSTED", None, None, 0)
    seeds = [np.array(plant.z_ref, float)] + [np.asarray(s, float) for s in (z_seeds or [])]
    z_prev = None
    best = None
    for k in range(cfg["K_max"] + 1):
        starts = seeds + ([z_prev] if z_prev is not None else [])
        sol, s_used = None, None
        for s0 in starts:
            cand = solve_nlp(pb, W, s0)
            if cand["ok"]:
                sol, s_used = cand, s0
                break
            sol = cand
        res.iterations = k
        if not sol["ok"]:
            res.status = sol["kind"]
            res.detail = sol.get("msg", "")
            res.z = sol["z"]
            break
        z = sol["z"]
        z_prev = z
        m, key = pb.most_violated(z)
        res.log.append({"k": k, "W": len(W), "min_margin": m, "most_violated": key, "J": pb.J(z), "solver_viol": sol["viol"]})
        best = (z, m)
        if m >= -cfg["tau_cut_pu"]:
            kk, nact = kkt_residual(pb, z, W)
            res.z, res.J, res.kkt_residual = z, pb.J(z), kk
            res.status = "LOCAL_OPTIMUM_FOUND" if kk <= cfg["kkt_tol"] * (1.0 + abs(res.J)) else "FEASIBLE_PREDICTED"
            break
        if key in W:
            res.status = "STAGNATED_EXISTING_CUT"
            res.z, res.J = z, pb.J(z)
            res.detail = f"most violated {key} already in W with margin {m:.3e}: solver/gradient/predictor non-smoothness or contradictory constraints"
            break
        W.add(key)
        res.cuts.append({"k": k, "cut": key, "margin": m, "unit": plant.units[key[1]] if hasattr(plant, "units") else key[1], "scenario": scenarios[key[0]].name})
    else:
        res.status = "ITERATION_BUDGET_EXHAUSTED"
        res.z = best[0] if best else None
        res.J = pb.J(best[0]) if best else None
    res.margins = None
    if res.z is not None:
        res.margins = {}
        for d in range(len(scenarios)):
            u, l, _ = pb.margins_d(res.z, d)
            res.margins[d] = (u.copy(), l.copy())
    res.solver_calls = pb.calls
    return res


def solve_static(plant, mode: str, scenarios: list, rho: float = 0.0, cfg: dict | None = None, eps_J=None, eps_E=None) -> OPFResult:
    """M0 (base AC-OPF) and M1 (static reserve) in one solve."""
    assert mode in ("M0", "M1")
    pb = Problem(plant, mode, scenarios, eps_J, eps_E, rho=rho, cfg=cfg)
    sol = solve_nlp(pb, set(), np.array(plant.z_ref, float))
    if not sol["ok"]:
        return OPFResult(mode, sol["kind"], sol["z"], None, 0, detail=sol.get("msg", ""))
    z = sol["z"]
    kk, _ = kkt_residual(pb, z, set())
    st = "LOCAL_OPTIMUM_FOUND" if kk <= pb.cfg["kkt_tol"] * (1.0 + pb.J(z)) else "FEASIBLE_PREDICTED"
    return OPFResult(mode, st, z, pb.J(z), sol.get("nit", 0), kkt_residual=kk, solver_calls=pb.calls)
