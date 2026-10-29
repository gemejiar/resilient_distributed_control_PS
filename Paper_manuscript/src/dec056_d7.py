"""DEC-056 / D7: why the OPF dispatch is not an equilibrium of the closed loop (plant + original B2 RDC), and which consistent equilibria exist.
NO time integration: PFlow, TDS.init without steps, algebraic solves, linearisations, matrix exponentials of the linearised closed loop.

  diag  <OC> <M>   residuals at the initialised dispatch xi(z): plant f and g by model, the 20 RDC rates split into the voltage term K_IQ K_V gQ (1 - V),
                   the Q-consensus term -K_IQ K_Q lQ and the leak (zero at activation, Qset = Qn); eigenvalues of the closed-loop Jacobian; linear response of the
                   closed loop from xi(z) (RDC on, no event): predicted bus-voltage drift and the time after which the 20-s drift of G1 is below 1e-3 pu
  selfc <OC> <M>   self-consistent dispatch: p0 kept, the 10 unit voltage set-points v0 solved so that the B2 rates vanish at activation (v_Q(xi(z)) = 0, v_P = 0
                   holds identically); limits of the OPF base constraints checked at the solution
  cleq  <OC> <M>   closed-loop relative equilibrium xi*(z) reached by B2 activated at xi(z) (nominals Pn, Qn of z): damped Newton of DEC-051 started at xi(z)
State files: Paper_manuscript/backups/DEC056_state (exclusive)."""
from __future__ import annotations

import json
import sys
import time

import numpy as np

import dec054_common as C54
import dec055_common as C55
import dec055_oc as OCM
from dec054_plant import InitInvalid

STATE = C54.RUNS_DIR.parent / "DEC056_state"
UNITS = C55.UNITS


def save(name, obj):
    STATE.mkdir(parents=True, exist_ok=True)
    with open(STATE / f"{name}.json", "x", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else float(o))


def dispatch(oc, m):
    """z of the M0 / M3 static design of DEC-055 (state files, read only); 'M3_D54' = the frozen DEC-054 M3 dispatch (OC1)."""
    if m == "M3_D54":
        return np.array(json.loads((C54.RUNS_DIR / "P3B2_b7P_M3" / "config.json").read_text(encoding="utf-8"))["test"]["z"]), "DEC-054 frozen"
    s = json.loads((C55.STATE / f"{m.lower()}_{oc}.json").read_text(encoding="utf-8"))
    return np.array(s["z"]), s["status"]


def split_rates(K, e8, st, ctx, u, system):
    """The B2 rates at the current state, term by term (identical algebra to dec051_core.rdc_rates)."""
    p, q, v, om = (np.asarray(system.dae.y[st[k]], float) for k in ("a_p", "a_q", "a_v", "a_f"))
    lim = ctx["lim"]
    gp_raw, gq_raw = e8.capability_factors(u[:10], u[10:], lim)
    gp, gq = gp_raw / st["gref_p"], gq_raw / st["gref_q"]
    adj = ctx["adjacency"]
    xq = st["d_q"] * q
    lq = gq * (adj * gq[None, :] * (xq[:, None] - xq[None, :])).sum(axis=1)
    volt = e8.K_IQ * e8.K_V * gq * (e8.V_REF - v)
    cons = -e8.K_IQ * e8.K_Q * lq
    leak = -e8.K_LEAK * (u[10:] - st["qn"])
    tot = K.rdc_rates(st, ctx, u[:10], u[10:], p, q, v, om)
    assert np.allclose(tot[10:], volt + cons + leak, atol=1e-14)
    # unit voltage that cancels the rate with the consensus term frozen at its current value (first-order self-consistency)
    v_star = e8.V_REF - (e8.K_Q / e8.K_V) * lq / gq
    return {"v_P": tot[:10], "v_Q": tot[10:], "v_Q_voltage_term": volt, "v_Q_consensus_term": cons, "v_Q_leak_term": leak, "unit_V": v, "unit_Q": q, "gq_norm": gq,
            "unit_V_cancelling_rate_first_order": v_star}


def residual_groups(system):
    f, g = np.asarray(system.dae.f, float), np.asarray(system.dae.g, float)
    out = {}
    for arr, names, tag in ((f, system.dae.x_name, "f"), (g, system.dae.y_name, "g")):
        for val, nm in zip(arr, names):
            parts = str(nm).split()
            model = parts[1] if len(parts) > 1 else parts[0]
            model = model.split("_")[0]
            k = f"{tag}:{model}"
            out[k] = max(out.get(k, 0.0), abs(float(val)))
    return out


def settle(M, f, Cz, n_buses=39, t_end=6000.0, dt=1.0, window=20.0, thr=(1e-3, 1e-4)):
    """Linear response delta' = M delta + f, delta(0) = 0; outputs Y = Cz delta.  Returns the bus-voltage trajectory summary and the earliest activation
    time T after which every 20-s window [T, T+20] has max |V(s) - V(T)| <= thr (all 39 buses), for each threshold."""
    from scipy.linalg import expm
    nz = M.shape[0]
    Mt = np.zeros((nz + 1, nz + 1))
    Mt[:nz, :nz] = M
    Mt[:nz, nz] = f
    Phi = expm(Mt * dt)
    n = int(round(t_end / dt))
    z = np.zeros(nz + 1)
    z[nz] = 1.0
    Y = np.zeros((n + 1, Cz.shape[0]))
    for k in range(1, n + 1):
        z = Phi @ z
        Y[k] = Cz @ z[:nz]
    t = np.arange(n + 1) * dt
    V = Y[:, 20:20 + n_buses]
    w = int(round(window / dt))
    drift = np.array([np.abs(V[k:k + w + 1] - V[k]).max() for k in range(n - w)])
    res = {"t_end_s": t_end, "dt_s": dt, "dV_bus_at": {str(int(s)): float(np.abs(V[int(s / dt)]).max()) for s in (20, 100, 500, 1000, 2000, t_end)},
           "drift20_first_window_pu": float(drift[0]), "dQ_unit_final_pu": Y[-1, 10:20].tolist(), "dP_unit_final_pu": Y[-1, :10].tolist(), "dV_bus_final_pu": V[-1].tolist()}
    for th in thr:
        ok = np.where(drift <= th)[0]
        # first index after which ALL later windows satisfy the threshold
        bad = np.where(drift > th)[0]
        T = 0.0 if bad.size == 0 else (float(t[bad[-1] + 1]) if bad[-1] + 1 < len(drift) else None)
        res[f"T_settle_drift20_le_{th:g}_s"] = T
    return res, t, V


def stage_diag(oc, m):
    t0 = time.time()
    z, status = dispatch(oc, m)
    plant = OCM.make_plant(oc)
    system, ctx, rep = plant._make(z)
    K, e8 = plant.K, plant.e8
    st = K.rdc_state(system, ctx)
    u = np.concatenate([st["pn"], st["qn"]])
    K.apply_params(system, ctx, st, u)
    r = split_rates(K, e8, st, ctx, u, system)
    groups = residual_groups(system)
    pred = plant.PR.LinearPredictor(ctx)
    pred.lim = ctx["lim"]
    b = pred.build(system, st, r["v_P"], r["v_Q"], 5.0, refresh_params=True)
    M, f = b["M"], np.concatenate([b["xdot"], b["v0"]])
    ev = np.linalg.eigvals(M)
    evs = ev[np.argsort(-ev.real)]
    s, tt, V = settle(M, f, b["Cz"])
    vb0 = np.asarray(system.dae.y[np.asarray(system.Bus.v.a)], float)
    out = {"oc": oc, "dispatch": m, "dispatch_status": status, "z": z, "init_report": rep, "residual_max_by_model": groups,
           "rdc": {k: np.asarray(v).tolist() for k, v in r.items()}, "max_abs_v_P": float(np.abs(r["v_P"]).max()), "max_abs_v_Q": float(np.abs(r["v_Q"]).max()),
           "max_abs_voltage_term": float(np.abs(r["v_Q_voltage_term"]).max()), "max_abs_consensus_term": float(np.abs(r["v_Q_consensus_term"]).max()),
           "max_abs_unit_V_minus_Vref": float(np.abs(r["unit_V"] - 1.0).max()),
           "closed_loop_eig_rightmost": [[float(x.real), float(x.imag)] for x in evs[:8]], "n_eig_re_pos_gt_1e-9": int((ev.real > 1e-9).sum()),
           "linear_settling": s, "bus_V_pre": vb0.tolist(), "seconds": round(time.time() - t0, 1)}
    STATE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(STATE / f"d7_linresp_{oc}_{m}.npz", t=tt, dV=V)
    save(f"d7_diag_{oc}_{m}", out)
    print(oc, m, {k: out[k] for k in ("max_abs_v_P", "max_abs_v_Q", "max_abs_voltage_term", "max_abs_consensus_term", "max_abs_unit_V_minus_Vref", "n_eig_re_pos_gt_1e-9")},
          {k: v for k, v in s.items() if k.startswith("T_") or k.startswith("drift")}, flush=True)


def stage_selfc(oc, m, tol=1e-10, itmax=12, h=1e-6):
    """Newton on v0 (10) with p0 fixed: F(v0) = v_Q at activation.  Finite-difference Jacobian; every evaluation is a validated PFlow + TDS.init."""
    t0 = time.time()
    z0, status = dispatch(oc, m)
    plant = OCM.make_plant(oc)
    K, e8 = plant.K, plant.e8

    def F(z):
        system, ctx, _ = plant._make(z)
        st = K.rdc_state(system, ctx)
        u = np.concatenate([st["pn"], st["qn"]])
        return K.rdc_rates(st, ctx, u[:10], u[10:], *(np.asarray(system.dae.y[st[k]], float) for k in ("a_p", "a_q", "a_v", "a_f"))), system
    z = z0.copy()
    hist = []
    for it in range(itmax):
        r, _ = F(z)
        nrm = float(np.abs(r).max())
        hist.append({"it": it, "max_abs_v": nrm, "max_abs_v_P": float(np.abs(r[:10]).max()), "v0": z[9:].tolist()})
        print(oc, m, "selfc it", it, f"{nrm:.3e}", flush=True)
        if nrm < tol:
            break
        Jm = np.zeros((10, 10))
        for k in range(10):
            zz = z.copy()
            zz[9 + k] += h
            Jm[:, k] = (F(zz)[0][10:] - r[10:]) / h
        step = np.linalg.solve(Jm, -r[10:])
        lam = 1.0
        while lam > 1e-3:
            zt = z.copy()
            zt[9:] += lam * step
            try:
                if np.abs(F(zt)[0]).max() < nrm:
                    break
            except InitInvalid:
                pass
            lam *= 0.5
        z = zt
        hist[-1].update({"step_inf": float(np.abs(step).max()), "lam": lam, "cond_J": float(np.linalg.cond(Jm))})
    e = plant.evaluate(z)
    lim = plant.limits
    vm, cm = C54.PROPOSED["v_margin_pu"], C54.PROPOSED["cap_margin_pu"]
    chk = {}
    if e["ok"]:
        P, Q, V = e["P"], e["Q"], e["V"]
        chk = {"V_min": float(V.min()), "V_max": float(V.max()), "V_band_with_margin_ok": bool(V.min() >= 0.95 + vm and V.max() <= 1.05 - vm), "V_band_ok": bool(V.min() >= 0.95 and V.max() <= 1.05),
               "P_margin_min": float((lim["pmax"] - P).min()), "Q_to_qmax_min": float((lim["qmax"] - Q).min()), "Q_to_qmin_min": float((Q - lim["qmin"]).min()),
               "S_margin_min": float((lim["smax"] - np.hypot(P, Q)).min()), "base_constraints_ok": bool(V.min() >= 0.95 + vm and V.max() <= 1.05 - vm and (lim["pmax"] - cm - P).min() >= 0
                                                                                                           and (lim["qmax"] - cm - Q).min() >= 0 and (Q - lim["qmin"] - cm).min() >= 0 and (lim["smax"] - cm - np.hypot(P, Q)).min() >= 0),
               "P": P.tolist(), "Q": Q.tolist(), "dP_vs_dispatch": (P - plant.evaluate(z0)["P"]).tolist(), "unit_V": [float(V[b - 1]) for b in C55.UNIT_BUS],
               "v0_bounds_ok": bool(np.all(z[9:] >= plant.z_lo[9:] - 1e-12) and np.all(z[9:] <= plant.z_hi[9:] + 1e-12))}
    out = {"oc": oc, "dispatch": m, "dispatch_status": status, "z_dispatch": z0, "z_selfconsistent": z, "converged": hist[-1]["max_abs_v"] < tol, "history": hist,
           "dv0_vs_dispatch": (z[9:] - z0[9:]).tolist(), "init_ok": bool(e["ok"]), "checks": chk, "seconds": round(time.time() - t0, 1)}
    save(f"d7_selfc_{oc}_{m}", out)
    print(oc, m, "selfc", out["converged"], json.dumps({k: v for k, v in chk.items() if not isinstance(v, list)}), flush=True)


def stage_selfc2(oc, m, free="v0"):
    """Constrained version of selfc (the unconstrained Newton of selfc can reach the boundary of the capability set, where gQ = 0 cancels v_Q trivially and
    B2 refuses to start).  min ||v_Q||^2 over v0 (free='v0', p0 fixed) or over all 19 variables (free='all'), subject to the OPF base constraints of DEC-054
    (bus V in [0.95+0.005, 1.05-0.005], unit P/Q/S with 0.01 pu margin; Q margin keeps gQ > 0) and the variable bounds.  A zero minimum is a self-consistent
    dispatch; a positive local minimum is NOT a proof that none exists."""
    import dec054_opf as OPF
    from scipy.optimize import minimize
    t0 = time.time()
    z0, status = dispatch(oc, m)
    plant = OCM.make_plant(oc)
    K = plant.K
    pb = OPF.Problem(plant, "M0", [], cfg=dict(C54.PROPOSED))
    cache = {}

    def ev(z):
        key = tuple(np.round(z, 13))
        if key not in cache:
            try:
                system, ctx, _ = plant._make(z)
                st = K.rdc_state(system, ctx)
                u = np.concatenate([st["pn"], st["qn"]])
                r = K.rdc_rates(st, ctx, u[:10], u[10:], *(np.asarray(system.dae.y[st[k]], float) for k in ("a_p", "a_q", "a_v", "a_f")))
                cache[key] = (r, pb.base(z))
            except Exception:
                cache[key] = (np.full(20, 1.0), -1e3 * np.ones(2 * 39 + 50))
        return cache[key]
    idx = np.arange(9, 19) if free == "v0" else np.arange(19)

    def full(x):
        z = z0.copy()
        z[idx] = x
        return z
    obj = lambda x: 1e4 * float(np.sum(ev(full(x))[0][10:] ** 2))
    con = lambda x: ev(full(x))[1]
    bnds = list(zip(np.asarray(plant.z_lo)[idx], np.asarray(plant.z_hi)[idx]))
    res = minimize(obj, z0[idx], method="SLSQP", bounds=bnds, constraints=[{"type": "ineq", "fun": con}], options={"maxiter": 100, "ftol": 1e-16, "eps": 1e-7})
    z = full(res.x)
    r, b = ev(z)
    e = plant.evaluate(z)
    system, ctx, _ = plant._make(z)
    st = K.rdc_state(system, ctx)
    gp0, gq0 = plant.e8.capability_factors(st["pn"], st["qn"], ctx["lim"])
    out = {"oc": oc, "dispatch": m, "free": free, "solver": {"success": bool(res.success), "message": str(res.message), "nit": int(res.nit)}, "z_dispatch": z0, "z": z,
           "max_abs_v_Q": float(np.abs(r[10:]).max()), "max_abs_v_P": float(np.abs(r[:10]).max()), "min_base_constraint": float(b.min()),
           "gq_raw_min": float(gq0.min()), "gp_raw_min": float(gp0.min()), "dz": (z - z0).tolist(),
           "V_min": float(e["V"].min()) if e["ok"] else None, "V_max": float(e["V"].max()) if e["ok"] else None, "P": e["P"].tolist() if e["ok"] else None, "Q": e["Q"].tolist() if e["ok"] else None,
           "redispatch_MW_abs_sum_vs_dispatch": float(np.abs(z[:9] - z0[:9]).sum() * 100), "evaluations": len(cache), "seconds": round(time.time() - t0, 1)}
    if out["max_abs_v_Q"] < 1e-6:
        pred = plant.PR.LinearPredictor(ctx)
        pred.lim = ctx["lim"]
        u = np.concatenate([st["pn"], st["qn"]])
        K.apply_params(system, ctx, st, u)
        Mm = pred.build(system, st, r[:10], r[10:], 5.0, refresh_params=True)["M"]
        evs = np.linalg.eigvals(Mm)
        evs = evs[np.argsort(-evs.real)]
        out["closed_loop_eig_rightmost"] = [[float(a.real), float(a.imag)] for a in evs[:6]]
    save(f"d7_selfc2_{oc}_{m}_{free}", out)
    print(oc, m, free, {k: out[k] for k in ("max_abs_v_Q", "min_base_constraint", "gq_raw_min", "V_min", "V_max", "redispatch_MW_abs_sum_vs_dispatch", "seconds")}, out["solver"],
          out.get("closed_loop_eig_rightmost", [])[:3], flush=True)


def stage_cleq(oc, m):
    import run_dec051_equilibrium as EQ
    t0 = time.time()
    z, status = dispatch(oc, m)
    plant = OCM.make_plant(oc)
    system, ctx, _ = plant._make(z)
    K, e8 = plant.K, plant.e8
    st = K.rdc_state(system, ctx)
    ix = K.index_sets(system)
    names = list(system.dae.x_name)
    sg31 = list(system.GENROU.idx.v)[[int(b) for b in system.GENROU.bus.v].index(31)]
    pin = names.index("delta " + str(sg31).replace("_", " "))
    x0, y0 = np.array(system.dae.x), np.array(system.dae.y)
    vb0 = np.asarray(system.dae.y[np.asarray(system.Bus.v.a)], float).copy()
    u0 = np.concatenate([st["pn"], st["qn"]])
    x, y, u, hist, pred, vnull = EQ.newton(system, ctx, st, ix, pin, x0, y0, u0, tol=1e-10, itmax=40, verbose=False)
    K.set_state(system, x, y)
    K.inner_solve(system, ctx, st, u, ix, pred.cache, tol=1e-13)
    p, q, v, om = EQ.outputs(system, st)
    vb = np.asarray(system.dae.y[np.asarray(system.Bus.v.a)], float)
    lim = ctx["lim"]
    z_raw = e8.KAPPA_SG * (u[10:] - st["qn"])[:ctx["n_sg"]]
    vn = EQ.rates(system, ctx, st, u)
    M = pred.build(system, st, vn[:10], vn[10:], 1999.0, refresh_params=True)["M"]
    ev = np.linalg.eigvals(M)
    ev = ev[np.argsort(-ev.real)]
    out = {"oc": oc, "dispatch": m, "dispatch_status": status, "newton_last": hist[-1], "n_iter": len(hist), "converged_1e-8": bool(hist[-1]["norm_inf_F"] < 1e-8),
           "g_inf": float(np.abs(system.dae.g).max()), "rdc_rates_inf": float(np.abs(vn).max()),
           "unit_P": p.tolist(), "unit_Q": q.tolist(), "unit_V": v.tolist(), "dP_vs_dispatch": (p - st["pn"]).tolist(), "dQ_vs_dispatch": (q - st["qn"]).tolist(),
           "Qset_minus_Qn": (u[10:] - st["qn"]).tolist(), "Pset_minus_Pn": (u[:10] - st["pn"]).tolist(), "z_clamp_margin": float(e8.Z_CLAMP - np.abs(z_raw).max()),
           "bus_V_min_max": [float(vb.min()), float(vb.max())], "max_abs_dV_bus_vs_dispatch": float(np.abs(vb - vb0).max()), "n_bus_outside_band": int(((vb < 0.95) | (vb > 1.05)).sum()),
           "P_margin_min": float((lim["pmax"] - p).min()), "Q_to_qmax_min": float((lim["qmax"] - q).min()), "Q_to_qmin_min": float((q - lim["qmin"]).min()),
           "S_margin_min": float((lim["smax"] - np.hypot(p, q)).min()), "freq_offset_hz": float((om.mean() - 1.0) * 60.0),
           "eig_rightmost": [[float(a.real), float(a.imag)] for a in ev[:6]], "seconds": round(time.time() - t0, 1)}
    save(f"d7_cleq_{oc}_{m}", out)
    np.savez_compressed(STATE / f"d7_cleq_{oc}_{m}.npz", x=x, y=y, u=u, x0=x0, y0=y0, u0=u0)
    print(oc, m, "cleq", {k: out[k] for k in ("converged_1e-8", "n_iter", "g_inf", "rdc_rates_inf", "bus_V_min_max", "max_abs_dV_bus_vs_dispatch", "z_clamp_margin", "P_margin_min")},
          out["eig_rightmost"][:3], flush=True)


if __name__ == "__main__":
    {"diag": stage_diag, "selfc": stage_selfc, "cleq": stage_cleq, "selfc2": stage_selfc2}[sys.argv[1]](*sys.argv[2:])
