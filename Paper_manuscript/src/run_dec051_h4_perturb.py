"""DEC-051 block B5: time-domain validation of the local prediction (dynamic simulations H4-1 and H4-2 of the budget).

The original B2 controller runs on C2t_Vsafe_R35_040 from the verified equilibrium (A) plus a small perturbation along the dominant slow right eigenvector of the quotient Jacobian (sign +1 and -1),
with the load parameters of the post-event Q+ equilibrium and NO event.  Amplitude (declared before running): the perturbation is scaled so that max |du| over the 20 references is 0.02 pu.
The differential states and the references are set to  x* + s eps v_x,  u* + s eps v_u; the quasi-algebraic states and algebraic variables are recomputed from g = 0 with the actuator maps theta(u, y)
(consistent initial condition).  The RDC runs from t = 0 with the same law and the same fixed step as b.run.  The state is logged every 0.1 s.
Environment: H4_SIGN (+1/-1), H4_HORIZON (default 1000 s)."""

from __future__ import annotations

import os

os.environ["C2_VARIANT"] = "C2t"

import numpy as np

import dec051_core as C
import e9h_predictor as PR
import run_e8_ieee39 as e8
from run_e0_ieee39 import ARTIFACTS_DIR as A, git_commit, sha256

SIGN = float(os.environ.get("H4_SIGN", "1"))
HORIZON = float(os.environ.get("H4_HORIZON", "1000"))
AMP_U = 0.02
LOG_EVERY = 26   # ~0.1 s at h = 0.00390625 s


def main() -> int:
    eq = dict(np.load(A / "IEEE39_DEC051_equilibrium_state.npz"))
    mode = dict(np.load(A / "IEEE39_DEC051_H4_mode.npz"))      # v_x (n_dyn), v_u (20): unit-norm slow right eigenvector of the quotient Jacobian, lifted to the original coordinates
    system, ctx = C.build_system("S0")
    st = C.rdc_state(system, ctx)
    for k in C.PQ_PARAMS:
        getattr(system.PQ, k).v[:] = eq["PQ_" + k]
    ix = C.index_sets(system)
    d_idx = ix["d_idx"]
    scale = AMP_U / np.abs(mode["v_u"]).max()
    x = np.array(eq["x"], float)
    x[d_idx] += SIGN * scale * mode["v_x"]
    u = eq["u"] + SIGN * scale * mode["v_u"]
    C.set_state(system, x, np.array(eq["y"], float))
    pred = PR.LinearPredictor(ctx)
    C.apply_params(system, ctx, st, u)
    C.L.linearize(system, ctx, cache=pred.cache)
    info = C.inner_solve(system, ctx, st, u, ix, pred.cache, tol=1e-12)
    if not info["converged"]:
        raise RuntimeError(f"consistent initial condition not found: {info['residual_history'][-3:]}")
    system.TDS.config.tf = HORIZON
    system.TDS.config.save_every = 1000000
    system.TDS.config.no_tqdm = 1
    system.TDS.fg_update(system.exist.tds)
    if os.environ.get("H4_DRY"):
        F0 = np.abs(__import__("run_dec051_equilibrium").residual_vec(system, ctx, st, ix, u)[0]).max()
        print({"dry_run": True, "initial_inner_residual": info["residual_history"][-1], "max_abs_F_at_start": float(F0), "scale": float(scale), "dae_t": float(system.dae.t), "tf": system.TDS.config.tf}, flush=True)
        return 0
    sys_state: dict = {"u": u.copy(), "last_t": -1.0, "n": -1}
    log = {k: [] for k in ("t", "u", "x_d", "P", "Q", "Vunit", "Vbus", "f_hz", "g_inf", "rates")}
    dt = ctx["h"]
    n_sg = ctx["n_sg"]

    def cb(t, s):
        t = float(t)
        if t <= sys_state["last_t"]:
            return
        sys_state["last_t"] = t
        y = s.dae.y
        p = np.asarray(y[st["a_p"]], float); q = np.asarray(y[st["a_q"]], float); v = np.asarray(y[st["a_v"]], float); om = np.asarray(y[st["a_f"]], float)
        uu = sys_state["u"]
        r = C.rdc_rates(st, ctx, uu[:10], uu[10:], p, q, v, om)
        sys_state["n"] += 1
        if sys_state["n"] % LOG_EVERY == 0:
            log["t"].append(t); log["u"].append(uu.copy()); log["x_d"].append(np.array(s.dae.x[d_idx], float)); log["P"].append(p); log["Q"].append(q); log["Vunit"].append(v)
            log["Vbus"].append(np.asarray(y[np.asarray(s.Bus.v.a)], float)); log["f_hz"].append(float(om.mean() - 1.0) * 60.0); log["g_inf"].append(float(np.abs(s.dae.g).max())); log["rates"].append(r)
        sys_state["u"] = uu + dt * r
        C.apply_params(s, ctx, st, sys_state["u"])

    system.TDS.callpert = cb
    ok = bool(system.TDS.run(no_summary=True))
    out = {k: np.asarray(v) for k, v in log.items()}
    out["tds_ok"], out["t_end_s"], out["amp_scale"], out["sign"] = np.asarray(ok), np.asarray(float(system.dae.t)), np.asarray(scale), np.asarray(SIGN)
    out["x_eq_d"], out["u_eq"] = np.array(eq["x"], float)[d_idx], np.array(eq["u"], float)
    tag = "plus" if SIGN > 0 else "minus"
    p = A / f"IEEE39_DEC051_H4_perturb_{tag}.npz"
    np.savez_compressed(p, **out)
    print({"tds_ok": ok, "t_end": float(system.dae.t), "file": str(p), "sha256": sha256(p), "git": git_commit(), "n_logged": len(log["t"])}, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
