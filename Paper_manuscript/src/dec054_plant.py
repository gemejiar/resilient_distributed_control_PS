"""DEC-054 ANDES plant adapter (P2 glue).  STATUS: UNTESTED_ON_PLANT.  Written against existing, previously validated helpers (no historical file edited):
  hooks of the E9-B0 type (PV p0 / v0 before PFlow), dec051_core.rdc_state, run_dec051_h3_jump.jump, e9h_predictor.LinearPredictor.build (closed-loop M, plant forcing, RDC rates, output rows).
It must NOT be executed before BACKUP_VERIFIED and the P2 checks listed in the v2 design (callback ordering, GFM initial residuals, Euler-vs-continuous mismatch).
All ANDES imports are lazy so that the unit tests and the synthetic plant never load ANDES."""
from __future__ import annotations

import numpy as np

import dec054_rdcinit as RI
import dec054_predictor as PRD
from dec054_common import N_PV, N_V, PV_UNITS, UNIT_BUS, UNITS, T_POST, backup_gate

PV_BUS = [UNIT_BUS[UNITS.index(u)] for u in PV_UNITS]


def hook_for_z(z):
    """Impose z=(p0 of the 9 PV devices, v0 of the 10 unit buses) before PFlow (same mechanism as e9a_hocbf.vsafe_hook / e9b_variant.hook_for)."""
    z = np.asarray(z, float)

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


class AndesPlant:
    """Adapter with the same interface as dec054_synth.SyntheticPlant.  Every call re-initialises the candidate (PF + TDS.init, no stepping)."""
    units = UNITS
    validated = False

    def __init__(self, require_backup: bool = True):
        if require_backup and not backup_gate()["verified"]:
            raise RuntimeError("STOP_BACKUP_NOT_VERIFIED: the ANDES plant adapter is not to be instantiated before BACKUP_VERIFIED")
        import os
        os.environ.setdefault("C2_VARIANT", "C2t")
        import dec051_core as K            # noqa: F401  (patches the PSS-complete linearisation, read-only use)
        import run_dec051_h3_jump as J
        import run_dec051_equilibrium as EQ
        import e9a_linear as L
        import e9h_predictor as PR
        self.K, self.J, self.EQ, self.L, self.PR = K, J, EQ, L, PR
        sys0, ctx0 = J.make(None)
        self.limits = {k: np.asarray(v) for k, v in ctx0["lim"].items()}
        self.z_ref = None            # to be set by the caller from the historical C2t case values (read from the case, not from R35_040)
        self.z_lo = np.concatenate([np.maximum(self.limits["pmin"][[UNITS.index(u) for u in PV_UNITS]], 0.05), 0.95 * np.ones(N_V)])
        self.z_hi = np.concatenate([self.limits["pmax"][[UNITS.index(u) for u in PV_UNITS]], 1.05 * np.ones(N_V)])

    def _make(self, z):
        return self.J.make(hook_for_z(z))

    def evaluate(self, z):
        try:
            system, ctx = self._make(z)
        except Exception as ex:          # initialisation failure is reported, never read as infeasibility
            return {"ok": False, "error": repr(ex)}
        st = self.K.rdc_state(system, ctx)
        y = np.asarray(system.dae.y, float)
        P, Q, V = y[st["a_p"]].copy(), y[st["a_q"]].copy(), y[np.asarray(system.Bus.v.a)].copy()
        try:
            I = RI.init_map(P, Q, ctx["lim"])
        except RI.InitError as ex:
            return {"ok": False, "error": repr(ex)}
        # consistency of the pure-NumPy map with the executor's state (documentary check; recorded)
        diff = max(float(np.abs(I["k_ip"] - st["k_ip"])), float(np.abs(I["gref_p"] - st["gref_p"])), float(np.abs(I["d_p"] - st["d_p"]).max()))
        return {"ok": True, "P": P, "Q": Q, "V": V, "I": I, "I_vs_executor_max_diff": diff, "residual": float(np.max(np.abs(system.dae.g)))}

    def jump(self, z, sc):
        system, ctx = self._make(z)
        st = self.K.rdc_state(system, ctx)
        ix = self.K.index_sets(system)
        cache: dict = {}
        self.K.apply_params(system, ctx, st, np.concatenate([st["pn"], st["qn"]]))
        self.K.L.linearize(system, ctx, cache=cache)
        dp = sc.amp if sc.kind == "P" else 0.0
        dq = sc.amp if sc.kind == "Q" else 0.0
        out = self.J.jump(system, ctx, st, ix, cache, sc.bus, dp, dq)
        return {"ok": bool(out["converged"]), "dP": out["P"] - st["pn"], "dQ": out["Q"] - st["qn"], "P_plus": out["P"], "Q_plus": out["Q"], "V_plus": out["Vbus"], "residual": out["residual"]}

    def affine(self, z, sc):
        """(A+, f+, C) at the post-jump point with the RDC active (v2 sec 2.4): M of e9h_predictor.build, forcing = [plant xdot; RDC rates at the post-jump point]."""
        system, ctx = self._make(z)
        st = self.K.rdc_state(system, ctx)
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
        self.K.inner_solve(system, ctx, st, u, ix, pred.cache, tol=1e-11, itmax=40)      # algebraic jump: x and u continuous
        vn = self.EQ.rates(system, ctx, st, u)
        b = pred.build(system, st, vn[:10], vn[10:], 5.0, refresh_params=True)
        M, n = b["M"], b["n_dyn"]
        f = np.concatenate([b["xdot"], b["v0"]])
        C = b["Cz"][:10]                                                                  # physical P rows
        return M, f, C

    def excursion(self, z, sc):
        A, f, C = self.affine(z, sc)
        x = PRD.excursion(A, f, C)
        return {"E_up": x["E_up"], "E_dn": x["E_dn"], "t_up": x["t_up"], "sampling_error": x["sampling_error_up"], "horizon_s": T_POST}
