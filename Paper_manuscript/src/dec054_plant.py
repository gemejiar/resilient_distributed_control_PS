"""DEC-054 ANDES plant adapter (P2 glue).  STATUS: UNTESTED_ON_PLANT (the pure-Python parts below are unit-tested with mock systems).
Reuses existing, previously validated helpers without editing them (hook of the E9-B0 type, dec051_core.rdc_state, run_dec051_h3_jump.jump,
e9h_predictor.LinearPredictor.build).  It must NOT be instantiated before BACKUP_VERIFIED; all ANDES imports are lazy.

Integration rules enforced here
  * z_ref is read from the HISTORICAL case (PV p0, PV/Slack v0 of the loaded C2t case, scenario S0 = no event); it never depends on any contingency.
  * the decision vector has exactly 19 variables: p0 of the 9 PV devices followed by v0 of the 10 unit buses (UNITS order).
  * an initialisation is valid only if PFlow converged, TDS.init ran (`initialized`, `test_ok`), the DAE residuals are below tolerance, all arrays are finite
    and the pure-NumPy I(z) map agrees with the executor's state.  `ok=True` is never returned otherwise."""
from __future__ import annotations

import numpy as np

import dec054_predictor as PRD
import dec054_rdcinit as RI
from dec054_common import N_PV, N_V, N_Z, PROPOSED, PV_UNITS, T_POST, UNIT_BUS, UNITS, backup_gate

PV_BUS = [UNIT_BUS[UNITS.index(u)] for u in PV_UNITS]
VAR_NAMES = [f"p0_{u}" for u in PV_UNITS] + [f"v0_{u}" for u in UNITS]


class InitInvalid(RuntimeError):
    pass


def variable_spec() -> dict:
    """The 19 decision variables (names, order).  The adapter delivers exactly these."""
    assert len(VAR_NAMES) == N_Z == 19 and len(set(VAR_NAMES)) == 19
    return {"names": list(VAR_NAMES), "n": N_Z, "p0_units": list(PV_UNITS), "v0_units": list(UNITS), "p0_buses": list(PV_BUS), "v0_buses": list(UNIT_BUS)}


def z_ref_from_system(system) -> np.ndarray:
    """Reference dispatch from the loaded HISTORICAL case: p0 of the 9 PV devices (PV_UNITS order) then v0 of the 10 unit buses (UNITS order).
    Takes the system only (no scenario, no event, no prospective information).  Raises on any structural mismatch."""
    pv_bus = [int(b) for b in system.PV.bus.v]
    p0 = np.asarray(system.PV.p0.v, float)
    if sorted(pv_bus) != sorted(PV_BUS) or len(pv_bus) != len(set(pv_bus)):
        raise ValueError(f"PV buses {sorted(pv_bus)} do not match the expected {sorted(PV_BUS)}")
    pvals = [float(p0[pv_bus.index(b)]) for b in PV_BUS]
    pv_v0 = np.asarray(system.PV.v0.v, float)
    sl_bus = [int(b) for b in system.Slack.bus.v]
    sl_v0 = np.asarray(system.Slack.v0.v, float)
    vvals = []
    for b in UNIT_BUS:
        if b in pv_bus:
            vvals.append(float(pv_v0[pv_bus.index(b)]))
        elif b in sl_bus:
            vvals.append(float(sl_v0[sl_bus.index(b)]))
        else:
            raise ValueError(f"unit bus {b} is neither PV nor Slack")
    z = np.array(pvals + vvals, float)
    if z.shape != (N_Z,) or not np.all(np.isfinite(z)):
        raise ValueError("z_ref must be 19 finite values")
    return z


def hook_for_z(z):
    """Impose z=(p0 of the 9 PV devices, v0 of the 10 unit buses) before PFlow (same mechanism as e9a_hocbf.vsafe_hook / e9b_variant.hook_for)."""
    z = np.asarray(z, float)
    if z.shape != (N_Z,) or not np.all(np.isfinite(z)):
        raise ValueError("z must be 19 finite values")

    def hook(system, ctx):
        pv_bus = [int(b) for b in system.PV.bus.v]
        for bus, val in zip(PV_BUS, z[:N_PV]):
            system.PV.p0.v[pv_bus.index(bus)] = val
        vmap = {UNIT_BUS[i]: z[N_PV + i] for i in range(N_V)}
        for model in ("PV", "Slack"):
            dev = getattr(system, model)
            for k, bb in enumerate(dev.bus.v):
                dev.v0.v[k] = vmap[int(bb)]
    return hook


def check_initialisation(system, pf_ok: bool, tol: float | None = None) -> dict:
    """Explicit validity verdict for one candidate initialisation (pure: works on any object with the ANDES attributes; mock-tested).
    Never reports ok=True unless every check passes; unverifiable flags are failures, not successes."""
    tol = PROPOSED["init_tol"] if tol is None else tol
    reasons = []
    pf_conv = getattr(getattr(system, "PFlow", None), "converged", None)
    if not pf_ok:
        reasons.append("PFlow.run() returned False")
    if pf_conv is not True:
        reasons.append(f"PFlow.converged is {pf_conv!r}")
    tds = getattr(system, "TDS", None)
    if getattr(tds, "initialized", None) is not True:
        reasons.append(f"TDS.initialized is {getattr(tds, 'initialized', None)!r}")
    test_ok = getattr(tds, "test_ok", None)
    if test_ok is not True:
        reasons.append(f"TDS.test_ok is {test_ok!r}")
    dae = system.dae
    arrays = {k: np.asarray(getattr(dae, k), float) for k in ("f", "g", "x", "y")}
    finite = all(np.all(np.isfinite(a)) for a in arrays.values())
    if not finite:
        reasons.append("non-finite entries in the DAE arrays")
    res_f = float(np.max(np.abs(arrays["f"]))) if arrays["f"].size and finite else float("nan")
    res_g = float(np.max(np.abs(arrays["g"]))) if arrays["g"].size and finite else float("nan")
    if not (res_f <= tol):
        reasons.append(f"|f|_inf = {res_f:.3e} exceeds {tol:.1e}")
    if not (res_g <= tol):
        reasons.append(f"|g|_inf = {res_g:.3e} exceeds {tol:.1e}")
    return {"ok": not reasons, "reasons": reasons, "pf_ok": bool(pf_ok), "pf_converged": pf_conv, "tds_initialized": getattr(tds, "initialized", None), "tds_test_ok": test_ok,
            "residual_f_inf": res_f, "residual_g_inf": res_g, "finite": bool(finite), "tol": tol}


class AndesPlant:
    """Adapter with the same interface as dec054_synth.SyntheticPlant.  Every call re-initialises the candidate (PF + TDS.init, no stepping) and validates it."""
    units = UNITS
    validated = False

    def __init__(self, require_backup: bool = True):
        if require_backup and not backup_gate()["verified"]:
            raise RuntimeError("STOP_BACKUP_NOT_VERIFIED: the ANDES plant adapter is not to be instantiated before BACKUP_VERIFIED")
        import os
        os.environ.setdefault("C2_VARIANT", "C2t")
        import dec051_core as K            # noqa: F401  (patches the PSS-complete linearisation, read-only use)
        import e9a_linear as L
        import e9h_predictor as PR
        import run_dec051_equilibrium as EQ
        import run_dec051_h3_jump as J
        import run_e8_ieee39 as e8
        self.K, self.J, self.EQ, self.L, self.PR, self.e8 = K, J, EQ, L, PR, e8
        system0, ctx0 = e8.configure("S0", e8.TIME_STEP_S)          # historical case, no event, no PF/TDS yet
        self.limits = {k: np.asarray(v) for k, v in ctx0["lim"].items()}
        self.z_ref = z_ref_from_system(system0)                      # the historical case values (never a contingency-dependent value)
        pv_idx = [UNITS.index(u) for u in PV_UNITS]
        self.z_lo = np.concatenate([np.maximum(self.limits["pmin"][pv_idx], 0.05), 0.95 * np.ones(N_V)])
        self.z_hi = np.concatenate([self.limits["pmax"][pv_idx], np.maximum(1.05, self.z_ref[N_PV:])])      # case v0 reaches 1.06 pu; the 0.95-1.05 band is enforced on bus voltages, not on set-points
        spec = variable_spec()
        assert self.z_ref.shape == (spec["n"],) and self.z_lo.shape == self.z_hi.shape == (spec["n"],)
        self.var_names = spec["names"]

    # ------------------------------------------------------------------ validated initialisation
    def _make(self, z):
        """configure -> hook(z) -> PFlow.run -> TDS.init, then check_initialisation.  Raises InitInvalid with the full report if anything is invalid."""
        system, ctx = self.e8.configure("S0", self.e8.TIME_STEP_S)
        hook_for_z(z)(system, ctx)
        pf_ok = bool(system.PFlow.run())
        report = check_initialisation(system, pf_ok)
        if report["pf_converged"] is True and pf_ok:
            system.TDS.init()
            report = check_initialisation(system, pf_ok)
        if not report["ok"]:
            raise InitInvalid(report)
        return system, ctx, report

    def evaluate(self, z):
        try:
            system, ctx, rep = self._make(z)
        except InitInvalid as ex:
            return {"ok": False, "reason": "INIT_INVALID", "init_report": ex.args[0]}
        except Exception as ex:          # any other failure is reported, never read as infeasibility
            return {"ok": False, "reason": repr(ex)}
        st = self.K.rdc_state(system, ctx)
        y = np.asarray(system.dae.y, float)
        P, Q, V = y[st["a_p"]].copy(), y[st["a_q"]].copy(), y[np.asarray(system.Bus.v.a)].copy()
        try:
            I = RI.init_map(P, Q, ctx["lim"])
        except RI.InitError as ex:
            return {"ok": False, "reason": "INIT_MAP_ERROR", "error": repr(ex)}
        diff = max(abs(I["k_ip"] - st["k_ip"]), abs(I["gref_p"] - st["gref_p"]), abs(I["gref_q"] - st["gref_q"]), float(np.abs(I["d_p"] - st["d_p"]).max()), float(np.abs(I["d_q"] - st["d_q"]).max()))
        if not np.all(np.isfinite([diff])) or diff > 1e-9:
            return {"ok": False, "reason": "INIT_MAP_MISMATCH", "I_vs_executor_max_diff": float(diff)}
        return {"ok": True, "P": P, "Q": Q, "V": V, "I": I, "I_vs_executor_max_diff": float(diff), "init_report": rep}

    def jump(self, z, sc):
        try:
            system, ctx, rep = self._make(z)
        except InitInvalid as ex:
            return {"ok": False, "reason": "INIT_INVALID", "init_report": ex.args[0]}
        st = self.K.rdc_state(system, ctx)
        ix = self.K.index_sets(system)
        cache: dict = {}
        self.K.apply_params(system, ctx, st, np.concatenate([st["pn"], st["qn"]]))
        self.K.L.linearize(system, ctx, cache=cache)
        dp = sc.amp if sc.kind == "P" else 0.0
        dq = sc.amp if sc.kind == "Q" else 0.0
        out = self.J.jump(system, ctx, st, ix, cache, sc.bus, dp, dq)
        ok = bool(out["converged"]) and bool(np.isfinite(out["residual"])) and out["residual"] <= 1e-9
        if not ok:
            return {"ok": False, "reason": "JUMP_NOT_CONVERGED", "residual": out["residual"]}
        return {"ok": True, "dP": out["P"] - st["pn"], "dQ": out["Q"] - st["qn"], "P_plus": out["P"], "Q_plus": out["Q"], "V_plus": out["Vbus"], "residual": out["residual"]}

    def stale_state(self, z_stale):
        """RDC initial state (pn, qn, pset, qset, k_ip, gref, d_p, y0, vref0) of ANOTHER dispatch: used only by the I(z) ablation (A5, the DEC-051 stale-reference hazard)."""
        system, ctx, _ = self._make(z_stale)
        return self.K.rdc_state(system, ctx)

    def affine(self, z, sc, diag: bool = False, stale=None):
        """(A+, f+, C) at the post-jump point with the RDC active (v2 sec 2.4): M of e9h_predictor.build, forcing = [plant xdot; RDC rates at the post-jump point]."""
        system, ctx, rep = self._make(z)
        st = self.K.rdc_state(system, ctx)
        if stale is not None:               # ablation A5 only: wrong (stale) RDC initialisation on the candidate's plant state
            for k in ("pn", "qn", "pset", "qset", "k_ip", "gref_p", "gref_q", "d_p", "d_q", "y0", "y0q", "vref0_sg"):
                st[k] = stale[k].copy() if hasattr(stale[k], "copy") else stale[k]
        ix = self.K.index_sets(system)
        pred = self.PR.LinearPredictor(ctx)
        pred.lim = ctx["lim"]
        u = np.concatenate([st["pn"], st["qn"]])
        self.K.apply_params(system, ctx, st, u)
        k = [int(b) for b in system.PQ.bus.v].index(sc.bus)
        if sc.kind == "P":
            system.PQ.Ppf.v[k] += sc.amp
        else:
            system.PQ.Qpf.v[k] += sc.amp
        self.L.linearize(system, ctx, cache=pred.cache)
        info = self.K.inner_solve(system, ctx, st, u, ix, pred.cache, tol=1e-11, itmax=40)      # algebraic jump: x and u continuous
        P_post = np.asarray(system.dae.y, float)[st["a_p"]].copy()
        vn = self.EQ.rates(system, ctx, st, u)
        b = pred.build(system, st, vn[:10], vn[10:], 5.0, refresh_params=True)
        M = b["M"]
        f = np.concatenate([b["xdot"], b["v0"]])
        C = b["Cz"][:10]                                                                  # physical P rows
        if not (np.all(np.isfinite(M)) and np.all(np.isfinite(f)) and np.all(np.isfinite(C))):
            raise InitInvalid({"ok": False, "reasons": ["non-finite predictor matrices"]})
        if not info.get("converged", False):
            raise InitInvalid({"ok": False, "reasons": [f"post-jump algebraic solve did not converge (residual {info.get('residual_history', ['?'])[-1]})"]})
        self.last_affine_diag = {"inner_converged": bool(info["converged"]), "inner_residual": float(info["residual_history"][-1]), "P_post_jump": P_post, "P_pre": st["pn"].copy(),
                                 "M_shape": list(M.shape), "n_dyn": int(b["n_dyn"]), "f_norm": float(np.linalg.norm(f)), "u_pre": u.copy()}
        if diag:
            lin2 = self.L.linearize(system, ctx, cache=pred.cache)
            self.last_affine_diag.update({"gy_min_sv_post_jump": float(lin2["gy_min_sv"]), "gy_cond_post_jump": float(lin2["gy_cond"]), "n_x": int(lin2["n_x"]), "n_y": int(lin2["n_y"]),
                                          "n_dynamic": int(lin2["n_dynamic"]), "n_quasi_algebraic": int(lin2["n_quasi_algebraic"]), "n_dropped_IEEEST_states": int(lin2["n_dropped_IEEEST_states"]),
                                          "d_idx_original": np.asarray(lin2["d_idx_original"]).tolist(), "z_idx_original": np.asarray(lin2["z_idx_original"]).tolist(), "ix_pss": {k: v for k, v in ix["pss"].items()}})
        return M, f, C

    def excursion(self, z, sc, stale=None):
        try:
            A, f, C = self.affine(z, sc, stale=stale)
        except InitInvalid as ex:
            return {"ok": False, "reason": "INIT_INVALID", "init_report": ex.args[0]}
        x = PRD.excursion(A, f, C)
        return {"ok": x["ok"], "E_up": x["E_up"], "E_dn": x["E_dn"], "t_up": x["t_up"], "sampling_error": x["sampling_error_up"], "horizon_s": T_POST}
