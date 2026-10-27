"""DEC-051 shared machinery (no simulation): ANDES system at a given full state, the E8 actuator maps, the original RDC law, inner algebraic solve and the reduced Jacobian.

The closed loop of the original B2 controller is  x' = f(x, y, theta(u, y)),  0 = g(x, y, theta(u, y)),  u' = v_RDC(u, P, Q, V, omega)  with the actuator maps theta of run_b3_ieee39
(TGOV1N.paux0, IEEEX1.vref0 with the +-Z_CLAMP clamp, REGF1.Paux0/Qaux0 tracking forms).  Everything here only evaluates these equations; the historical runners are untouched.

IEEEST (DEC-051 finding).  The case carries an ACTIVE power-system stabiliser per SG: sig = (Sb/Sn) te -> F1 -> F2 -> LL1 -> LL2 (lag, T4 = 0.75 s) -> Vks (KS = -2) -> washout WO (K = T5 = 1, T = T6 = 4.2 s) -> limiter -> vsout
feeding IEEEX1.  The blocks F1 (Lag2ndOrd), F2 (LeadLag2ndOrd) and LL1 (LeadLag) have all time constants equal to zero: ANDES represents them with five states per unit (F1_x, F1_y, F2_x1, F2_x2, LL1_x) and
two algebraic variables (F2_y, LL1_y) that are forced to equal the signal (F1_y = F2_x2 = F2_y = LL1_x = LL1_y = sig, F1_x = F2_x1 = d sig/dt).  They are removed here exactly (substitution LL1_y -> sig in the
LL2 equation); the two genuine PSS states per unit (LL2_x, WO_x) are KEPT.  E9-A dropped all seven per unit, i.e. it removed the PSS feedback; that linearisation is superseded for DEC-051.
"""

from __future__ import annotations

import os

os.environ["C2_VARIANT"] = "C2t"
os.environ.setdefault("E9B0_VARIANT", "C2t_Vsafe_R35_040")
os.environ.setdefault("E9B0_DELTA", "0.040")

from typing import Any

import numpy as np

import e9a_linear as L
import e9h_predictor as PR
import run_e8_ieee39 as e8
from e9b_variant import HOOK, VARIANT
from run_e0_ieee39 import ARTIFACTS_DIR as A

assert VARIANT == "C2t_Vsafe_R35_040", VARIANT
PQ_PARAMS = ("p0", "q0", "Ppf", "Qpf")
JUNK_X = ("F1_x", "F1_y", "F2_x1", "F2_x2", "LL1_x")
JUNK_Y = ("F2_y", "LL1_y")


def _pss_names(system) -> dict[str, dict[str, int]]:
    xn, yn = list(system.dae.x_name), list(system.dae.y_name)
    units = sorted({n.split()[-1] for n in xn if "IEEEST" in n}, key=lambda s: int(s))
    out = {}
    for u in units:
        d = {k: xn.index(f"{k} IEEEST {u}") for k in JUNK_X}
        d.update({"LL2_x": xn.index(f"LL2_x IEEEST {u}"), "WO_x": xn.index(f"WO_x IEEEST {u}")})
        d.update({"y_" + k: yn.index(f"{k} IEEEST {u}") for k in JUNK_Y + ("sig", "vsout", "Vss", "WO_y", "LL2_y")})
        out[u] = d
    return out


def index_sets(system) -> dict[str, Any]:
    dae = system.dae
    tf = np.array(L.kv_matrix(dae.Tf), dtype=float).ravel()
    pss = _pss_names(system)
    jx = np.array(sorted(d[k] for d in pss.values() for k in JUNK_X), dtype=int)
    jy = np.array(sorted(d["y_" + k] for d in pss.values() for k in JUNK_Y), dtype=int)
    keep_x = np.setdiff1d(np.arange(len(tf)), jx)
    keep_y = np.setdiff1d(np.arange(dae.m), jy)
    return {"tf": tf, "d_idx": np.array([i for i in keep_x if tf[i] > 0], dtype=int), "z_idx": np.array([i for i in keep_x if tf[i] == 0], dtype=int), "junk_x": jx, "junk_y": jy, "keep_x": keep_x, "keep_y": keep_y,
            "pss": pss, "ieeest": jx}


def set_junk(system, ix) -> None:
    """Make the removed (forced) PSS variables consistent with the signal so that every ANDES residual is evaluated on a consistent state."""
    x, y = system.dae.x, system.dae.y
    for d in ix["pss"].values():
        sig = y[d["y_sig"]]
        for k in ("F1_y", "F2_x2", "LL1_x"):
            x[d[k]] = sig
        x[d["F1_x"]] = 0.0
        x[d["F2_x1"]] = 0.0
        y[d["y_F2_y"]] = sig
        y[d["y_LL1_y"]] = sig
    system.vars_to_models()


def build_system(scenario: str = "S0", hook=HOOK):
    """Fresh ANDES system of the frozen variant, power flow solved and TDS initialised (t = 0 pre-event state); no time stepping."""
    system, ctx = e8.configure(scenario, e8.TIME_STEP_S)
    hook(system, ctx)
    system.PFlow.run()
    system.TDS.init()
    return system, ctx


def rdc_state(system, ctx, dump: dict[str, np.ndarray] | None = None) -> dict[str, Any]:
    """The ``st`` dictionary of run_b3_ieee39 (indices from the system; pn, qn, y0, y0q, vref0, gref, k_ip from the pre-event initial state)."""
    y = system.dae.y
    unit_bus = ctx["unit_bus"]
    lim = ctx["lim"]
    st: dict[str, Any] = {}
    st["a_f"] = np.asarray(system.BusFreq.f.a)[[ctx["bus_list"].index(b) for b in unit_bus]]
    st["a_v"] = np.asarray(system.Bus.v.a)[[ctx["bus_idx"].index(b) for b in unit_bus]]
    st["a_p"] = np.concatenate([np.asarray(system.GENROU.Pe.a), np.asarray(system.REGF1.Pe.a)])
    st["a_q"] = np.concatenate([np.asarray(system.GENROU.Qe.a), np.asarray(system.REGF1.Qe.a)])
    st["a_y"], st["a_yq"] = np.asarray(system.REGF1.PIplim_y.a), np.asarray(system.REGF1.PIqlim_y.a)
    st["pn"], st["qn"] = np.asarray(y[st["a_p"]], float).copy(), np.asarray(y[st["a_q"]], float).copy()
    st["y0"], st["y0q"] = np.asarray(y[st["a_y"]], float).copy(), np.asarray(y[st["a_yq"]], float).copy()
    st["vref0_sg"] = np.asarray(system.IEEEX1.vref0.v, float).copy()
    gp0, gq0 = e8.capability_factors(st["pn"], st["qn"], lim)
    st["gref_p"], st["gref_q"] = gp0.max(), gq0.max()
    st["k_ip"] = e8.SPEED_TARGET / float((gp0 / st["gref_p"]).sum())
    st["d_p"] = 1.0 / st["pn"]
    st["d_q"] = 1.0 / (lim["qmax"] - lim["qmin"])
    st["pset"], st["qset"] = st["pn"].copy(), st["qn"].copy()
    if dump is not None:
        st["_pn_diff"] = float(np.abs(dump["st_pn"] - st["pn"]).max())
        st["_qn_diff"] = float(np.abs(dump["st_qn"] - st["qn"]).max())
    return st


def rdc_rates(st, ctx, pset, qset, p, q, volt, omega) -> np.ndarray:
    """Original (B2) RDC rates, identical to ``field`` of run_b3_ieee39.run (offset 0): returns [vP (10), vQ (10)]."""
    lim = ctx["lim"]
    gp_raw, gq_raw = e8.capability_factors(pset, qset, lim)
    gp, gq = gp_raw / st["gref_p"], gq_raw / st["gref_q"]
    xp, xq = st["d_p"] * p, st["d_q"] * q
    adj = ctx["adjacency"]
    lp = gp * (adj * gp[None, :] * (xp[:, None] - xp[None, :])).sum(axis=1)
    lq = gq * (adj * gq[None, :] * (xq[:, None] - xq[None, :])).sum(axis=1)
    vp = st["k_ip"] * (gp * (1.0 - omega) - e8.K_P * lp) - e8.K_LEAK * (pset - st["pn"])
    vq = e8.K_IQ * (e8.K_V * gq * (e8.V_REF - volt) - e8.K_Q * lq) - e8.K_LEAK * (qset - st["qn"])
    return np.concatenate([vp, vq])


def apply_params(system, ctx, st, u: np.ndarray) -> np.ndarray:
    """Actuator maps theta(u, y): writes TGOV1N.paux0, IEEEX1.vref0, REGF1.Paux0/Qaux0 from u = [Pset, Qset] and the current algebraic y.  Returns the unclamped SG z-vector."""
    y = system.dae.y
    n_sg = ctx["n_sg"]
    pset, qset = u[:10], u[10:]
    system.TGOV1N.paux0.v[ctx["tg_pos"]] = (pset - st["pn"])[:n_sg]
    system.REGF1.Paux0.v[:] = e8.KC_GFM * (st["y0"] + (pset - st["pn"])[n_sg:] - np.asarray(y[st["a_y"]], float))
    z_raw = e8.KAPPA_SG * (qset - st["qn"])[:n_sg]
    system.IEEEX1.vref0.v[ctx["ex_pos"]] = st["vref0_sg"][ctx["ex_pos"]] + np.clip(z_raw, -e8.Z_CLAMP, e8.Z_CLAMP)
    system.REGF1.Qaux0.v[:] = e8.KCQ_GFM * (st["y0q"] + (qset - st["qn"])[n_sg:] - np.asarray(y[st["a_yq"]], float))
    return z_raw


def set_state(system, x: np.ndarray, y: np.ndarray) -> None:
    system.dae.x[:] = x
    system.dae.y[:] = y
    system.vars_to_models()


def load_dump_into(system, dump) -> None:
    for name in PQ_PARAMS:
        getattr(system.PQ, name).v[:] = dump["PQ_" + name]


def fg_all(system) -> tuple[np.ndarray, np.ndarray]:
    return L._fg(system)


def inner_solve(system, ctx, st, u, ix, fp_cache, tol=1e-13, itmax=30) -> dict[str, Any]:
    """Given the dynamic states x_d (already in dae.x) and the references u, solve for the quasi-algebraic states and the algebraic variables: f_z = 0, g = 0, with the actuator maps re-evaluated
    from y at every iteration (the GFM tracking forms depend on y) and the forced PSS variables kept consistent with the signal.  Newton with the ANDES Jacobians; the parameter-feedback terms use ``fp_cache``."""
    dae = system.dae
    z_idx, ky = ix["z_idx"], ix["keep_y"]
    nz = len(z_idx)
    chans = L.input_channels(system, {**ctx})
    rn = []
    set_junk(system, ix)
    for it in range(itmax):
        apply_params(system, ctx, st, u)
        system.vars_to_models()
        f0, g0 = fg_all(system)
        r = np.concatenate([f0[z_idx], g0[ky]])
        rn.append(float(np.abs(r).max()))
        if rn[-1] < tol:
            break
        system.j_update(system.exist.pflow_tds)
        fx, fy, gx, gy = (np.array(L.kv_matrix(m), dtype=float) for m in (dae.fx, dae.fy, dae.gx, dae.gy))
        fy_c, gy_c = fy.copy(), gy.copy()
        for j, c in enumerate(chans):
            if c["fb"] is not None:
                col, kc = c["fb"]
                fy_c[:, col] += fp_cache["fp"][:, j] * (-kc)
                gy_c[:, col] += fp_cache["gp"][:, j] * (-kc)
        kx = ix["keep_x"]
        # LL2_x depends on LL1_y, which equals sig: substitute in the Jacobian (exact, the block is an identity)
        for d in ix["pss"].values():
            fy_c[d["LL2_x"], d["y_sig"]] += fy_c[d["LL2_x"], d["y_LL1_y"]]
            fy_c[d["LL2_x"], d["y_LL1_y"]] = 0.0
        kmat = np.block([[fx[np.ix_(z_idx, z_idx)], fy_c[np.ix_(z_idx, ky)]], [gx[np.ix_(ky, z_idx)], gy_c[np.ix_(ky, ky)]]])
        step = np.linalg.solve(kmat, -r)
        dae.x[z_idx] += step[:nz]
        dae.y[ky] += step[nz:]
        set_junk(system, ix)
    return {"iterations": len(rn), "residual_history": rn, "converged": rn[-1] < tol}


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
# linearisation with the genuine PSS dynamics (replaces e9a_linear.linearize inside this process)
_orig_linearize = L.linearize


def linearize_pss(system, ctx, eps: float = L.FD_EPS, cache=None):
    """Same as e9a_linear.linearize but (i) the five forced IEEEST states and two forced algebraic variables per unit are eliminated exactly and (ii) LL2_x, WO_x are kept as dynamic states."""
    lin0 = _orig_linearize(system, ctx, eps=eps, cache=cache)
    raw = lin0["raw"]
    ix = index_sets(system)
    fx, fy, gx, gy, fu, gu, tf = (raw[k].copy() for k in ("fx", "fy", "gx", "gy", "fu", "gu", "tf"))
    for d in ix["pss"].values():
        fy[d["LL2_x"], d["y_sig"]] += fy[d["LL2_x"], d["y_LL1_y"]]
        fy[d["LL2_x"], d["y_LL1_y"]] = 0.0
    kx, ky = ix["keep_x"], ix["keep_y"]
    fx, fy, gx, gy, fu, gu, tf2 = fx[np.ix_(kx, kx)], fy[np.ix_(kx, ky)], gx[np.ix_(ky, kx)], gy[np.ix_(ky, ky)], fu[kx], gu[ky], tf[kx]
    d_new = np.where(tf2 > 0)[0]
    z_new = np.where(tf2 == 0)[0]
    raw2 = {"fx": fx, "fy": fy, "gx": gx, "gy": gy, "fu": fu, "gu": gu, "tf": tf2, "d_idx": d_new, "z_idx": z_new}
    out = L.reduce(raw2)
    n_y = raw["gy"].shape[0]
    cx = np.zeros((n_y, out["Cy_x"].shape[1]))
    cu = np.zeros((n_y, out["Cy_u"].shape[1]))
    cx[ky] = out["Cy_x"]
    cu[ky] = out["Cy_u"]
    out["Cy_x"], out["Cy_u"] = cx, cu
    f0, g0 = _fg_cached(system)
    out.update({"raw": raw2, "xdot": f0[kx][d_new] / tf2[d_new], "g0_norm": float(max(np.abs(g0[ky]).max(), np.abs(f0[kx][z_new]).max() if len(z_new) else 0.0)), "n_x": len(kx), "n_y": len(ky),
                "n_dropped_IEEEST_states": int(len(ix["junk_x"])), "gy_only_cond": float(np.linalg.cond(gy)), "d_idx_original": kx[d_new], "z_idx_original": kx[z_new]})
    return out


def _fg_cached(system):
    return L._fg(system)


L.linearize = linearize_pss      # the predictor (PR.build) and every caller in this process now use the PSS-complete linearisation
