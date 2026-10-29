"""DEC-057 static analyses (no time integration).  Protocol ops/sted/DEC057_protocol.md.
  b3eq   <OC> <M>   D7 rules R1-R7: is xi(z) a realizable equilibrium of plant + centered RDC B3 (DEC-039), and is it linearly stable?
                    The B3 offset is v_RDC at the pre-event point, computed exactly as run_b3_ieee39.run does (p = Pn, q = Qn, omega = 1, unit V at t = 0).
State: Paper_manuscript/backups/DEC057_state (exclusive)."""
from __future__ import annotations

import json
import sys
import time

import numpy as np

import dec054_common as C54
import dec055_common as C55
import dec055_oc as OCM

STATE = C54.RUNS_DIR.parent / "DEC057_state"
ST56 = C54.RUNS_DIR.parent / "DEC056_state"
UNITS = C55.UNITS


def save(name, obj):
    STATE.mkdir(parents=True, exist_ok=True)
    with open(STATE / f"{name}.json", "x", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else (float(o) if np.isscalar(o) else str(o)))


def dispatch(oc, m):
    if m == "M3S":                                                  # OC3 M3 of the DEC-056 seeded Algorithm 1
        return np.array(json.loads((ST56 / "oc3_seeded_full.json").read_text(encoding="utf-8"))["z"]), "DEC-056 seeded FEASIBLE_PREDICTED"
    s = json.loads((C55.STATE / f"{m.lower()}_{oc}.json").read_text(encoding="utf-8"))
    return np.array(s["z"]), s["status"]


def active_flags(system):
    import dec057_tds as T
    fv, fn = T.flag_vector(system)
    return [n for n, v in zip(fn, fv) if v and (".zu[" in n or ".zl[" in n)]


def spectrum(M, k=6):
    ev = np.linalg.eigvals(M)
    ev = ev[np.argsort(-ev.real)]
    null = int(np.argmin(np.abs(ev)))                              # the common-angle null mode (structural)
    rest = np.delete(ev, null)
    return {"null_mode": [float(ev[null].real), float(ev[null].imag)], "rightmost_excluding_null": [[float(x.real), float(x.imag)] for x in rest[:k]],
            "n_re_gt_1e-9_excluding_null": int((rest.real > 1e-9).sum()), "hurwitz_mod_null": bool((rest.real < -1e-9).all())}


def stage_b3eq(oc, m):
    t0 = time.time()
    z, status = dispatch(oc, m)
    plant = OCM.make_plant(oc)
    system, ctx, rep = plant._make(z)
    K, e8, L = plant.K, plant.e8, plant.L
    st = K.rdc_state(system, ctx)
    u = np.concatenate([st["pn"], st["qn"]])
    zraw = K.apply_params(system, ctx, st, u)
    f, g = L._fg(system)
    y = system.dae.y
    p, q, v, om = (np.asarray(y[st[k]], float) for k in ("a_p", "a_q", "a_v", "a_f"))
    v_b2 = K.rdc_rates(st, ctx, u[:10], u[10:], p, q, v, om)
    off = K.rdc_rates(st, ctx, st["pn"], st["qn"], st["pn"], st["qn"], v, 1.0)        # B3 offset (run_b3_ieee39: field(pn, qn, pn, qn, volt0, 1.0))
    v_b3 = v_b2 - off
    lim = ctx["lim"]
    gp, gq = e8.capability_factors(u[:10], u[10:], lim)
    paux = (u[:10] - st["pn"])[:ctx["n_sg"]]
    gfm_paux = e8.KC_GFM * (st["y0"] - np.asarray(y[st["a_y"]], float))
    gfm_qaux = e8.KCQ_GFM * (st["y0q"] - np.asarray(y[st["a_yq"]], float))
    vb = np.asarray(y[np.asarray(system.Bus.v.a)], float)
    s = np.hypot(p, q)
    flags = active_flags(system)
    pred = plant.PR.LinearPredictor(ctx)
    pred.lim = lim
    b = pred.build(system, st, v_b3[:10], v_b3[10:], 5.0, refresh_params=True)
    sp = spectrum(b["M"])
    R = {"R1_plant_residual": {"f_inf": float(np.abs(f).max()), "g_inf": float(np.abs(g).max()), "pass": bool(np.abs(f).max() <= 1e-10 and np.abs(g).max() <= 1e-10)},
         "R2_B3_rates": {"max_abs": float(np.abs(v_b3).max()), "B2_rates_max_abs_for_comparison": float(np.abs(v_b2).max()), "omega_minus_1_max": float(np.abs(om - 1).max()), "pass": bool(np.abs(v_b3).max() <= 1e-10)},
         "R3_actuators": {"sg_paux_max_abs": float(np.abs(paux).max()), "sg_z_max_abs": float(np.abs(zraw).max()), "z_clamp_margin": float(e8.Z_CLAMP - np.abs(zraw).max()),
                          "gfm_Paux0_max_abs": float(np.abs(gfm_paux).max()), "gfm_Qaux0_max_abs": float(np.abs(gfm_qaux).max()),
                          "pass": bool(max(np.abs(paux).max(), np.abs(zraw).max(), np.abs(gfm_paux).max(), np.abs(gfm_qaux).max()) <= 1e-10)},
         "R4_capability_interior": {"gP_raw_min": float(gp.min()), "gQ_raw_min": float(gq.min()), "gQ_argmin": UNITS[int(gq.argmin())], "pass": bool(gp.min() > 0 and gq.min() > 0)},
         "R5_limiters": {"active_zu_zl": flags, "pass": not [n for n in flags if not n.startswith("PV.")]},
         "R6_case_limits": {"P_to_pmax_min": float((lim["pmax"] - p).min()), "P_to_pmin_min": float((p - lim["pmin"]).min()), "Q_to_qmax_min": float((lim["qmax"] - q).min()),
                            "Q_to_qmin_min": float((q - lim["qmin"]).min()), "S_margin_min": float((lim["smax"] - s).min()), "V_bus_min": float(vb.min()), "V_bus_max": float(vb.max()),
                            "pass": bool((lim["pmax"] - p).min() >= 0 and (p - lim["pmin"]).min() >= 0 and (lim["qmax"] - q).min() >= 0 and (q - lim["qmin"]).min() >= 0
                                         and (lim["smax"] - s).min() >= 0 and vb.min() >= 0.95 and vb.max() <= 1.05)},
         "R7_linear_stability": dict(sp, **{"pass": sp["hurwitz_mod_null"]})}
    R["equilibrium_R1_R6"] = all(R[k]["pass"] for k in ("R1_plant_residual", "R2_B3_rates", "R3_actuators", "R4_capability_interior", "R5_limiters", "R6_case_limits"))
    R["equilibrium_reached_and_stable_R1_R7"] = R["equilibrium_R1_R6"] and R["R7_linear_stability"]["pass"]
    # the rightmost non-null mode: dominant states (participation)
    ev, W = np.linalg.eig(b["M"])
    order = np.argsort(-ev.real)
    j = next(i for i in order if abs(ev[i]) > 1e-8)
    wl = np.linalg.inv(W)[j]
    pf = np.abs(W[:, j] * wl)
    pf /= pf.sum()
    names = [str(system.dae.x_name[i]) for i in plant.K.index_sets(system)["d_idx"]] + [f"Pset {u_}" for u_ in UNITS] + [f"Qset {u_}" for u_ in UNITS]
    top = np.argsort(-pf)[:8]
    R["rightmost_mode_participation"] = {"eig": [float(ev[j].real), float(ev[j].imag)], "top": [[names[i] if i < len(names) else str(i), float(pf[i])] for i in top]}
    out = {"oc": oc, "dispatch": m, "dispatch_status": status, "z": z, "rules": R, "seconds": round(time.time() - t0, 1)}
    save(f"b3eq_{oc}_{m}", out)
    print(oc, m, {k: (R[k]["pass"] if isinstance(R[k], dict) and "pass" in R[k] else R[k]) for k in R if k != "rightmost_mode_participation"}, sp["rightmost_excluding_null"][:2],
          R["rightmost_mode_participation"]["top"][:3], flush=True)


def stage_seedrule(workers="1"):
    """OC3 seed rule (i) of the protocol, re-executed from the M0 point with DESIGN data only:
    step 1 = the DEC-056 phase-1b minimum-norm SLP on the jump rows (re-run in this process, must reproduce the stored point);
    step 2 = while a DESIGN post-jump closed-loop linearisation has Re > 1e-9: lower v0 of the unit owning the reference state with the largest
             participation in the rightmost mode by r_tr_v0_pu (at most 5 steps, inside the bounds, base and jump constraints kept);
    step 3 = compare with the DEC-056 seed."""
    import dec055_l0 as L0
    import dec056_oc3 as D
    t0 = time.time()
    held = {}
    D.save = lambda name, obj: held.update({name: obj})              # keep the re-run in memory (the DEC-056 state is not touched)
    D.stage_phase1b(int(workers))
    p1 = held["oc3_phase1b"]
    ref1 = json.loads((ST56 / "oc3_phase1b.json").read_text(encoding="utf-8"))
    seed56 = np.array(json.loads((ST56 / "oc3_seeded_full.json").read_text(encoding="utf-8"))["seed_z"])
    z = np.array(p1["z"], float)
    out = {"step1": {"reproduces_DEC056_phase1b_max_abs_dz": float(np.abs(z - np.array(ref1["z"])).max()), "min_jump_margin": p1["min_jump_margin"], "min_base": p1["min_base"],
                     "jump_admissible_all_design": p1["jump_admissible_all_design"], "redispatch_MW_vs_M0": p1["redispatch_MW_vs_M0"], "seconds": p1["seconds"]}}
    plant = OCM.make_plant("OC3")
    plantp, pb, OPF, _, _ = D.setup(int(workers), "M2")
    lo, hi = np.array(plant.z_lo), np.array(plant.z_hi)
    names = list(plant.var_names)
    step = float(C54.PROPOSED["r_tr_v0_pu"])
    hist = []
    try:
        for it in range(6):
            re, part = {}, np.zeros(20)
            for sc in L0.design_scenarios():
                A = plant.affine(z, sc)[0]
                ev, W = np.linalg.eig(A)
                j = int(np.argmax(ev.real))
                re[sc.name] = float(ev[j].real)
                if ev[j].real > 1e-9:
                    wl = np.linalg.inv(W)[j]
                    pf = np.abs(W[:, j] * wl)
                    part += pf[-20:] / pf.sum()
            m, b = D.all_m(pb, z)
            rec = {"it": it, "max_re_by_scenario": re, "min_jump_margin": float(m.min()), "min_base": float(b.min()), "z_v0": z[9:].tolist()}
            if max(re.values()) <= 1e-9:
                rec["action"] = "all DESIGN post-jump linearisations Hurwitz modulo the null mode: stop"
                hist.append(rec)
                break
            k = int(np.argmax(part))
            unit = UNITS[k % 10]
            vi = names.index(f"v0_{unit}")
            rec.update({"dominant_reference_state": ("Pset " if k < 10 else "Qset ") + unit, "participation_sum": part.tolist(), "variable": names[vi]})
            if it == 5 or z[vi] - step < lo[vi]:
                rec["action"] = "stop: step budget or bound reached"
                hist.append(rec)
                break
            z = z.copy()
            z[vi] -= step
            rec["action"] = f"{names[vi]} -= {step}"
            hist.append(rec)
        m, b = D.all_m(pb, z)
    finally:
        plantp.close()
    out.update({"step2": hist, "seed": z, "bounds_ok": bool(np.all(z >= lo - 1e-12) and np.all(z <= hi + 1e-12)), "final_min_jump_margin": float(m.min()), "final_min_base": float(b.min()),
                "equals_DEC056_seed_max_abs": float(np.abs(z - seed56).max()), "changed_variables_vs_phase1b": [names[i] for i in np.where(np.abs(z - np.array(p1["z"])) > 0)[0]],
                "r_tr_v0_pu": step, "seconds": round(time.time() - t0, 1)})
    save("oc3_seedrule", out)
    print({k: out[k] for k in ("bounds_ok", "final_min_jump_margin", "final_min_base", "equals_DEC056_seed_max_abs", "changed_variables_vs_phase1b")}, out["step1"], flush=True)


def load_state(plant, z, x, y, flags, u, pq=None):
    """Fresh validated system at z, then the stored state (x, y), the stored discrete flags and the references u = [Pset, Qset]."""
    import dec057_tds as T
    system, ctx, _ = plant._make(z)
    st = plant.K.rdc_state(system, ctx)
    if pq is not None:
        for n, v in pq.items():
            getattr(system.PQ, n).v[:] = v
    plant.K.set_state(system, np.asarray(x, float), np.asarray(y, float))
    k = 0
    for mn, m in system.models.items():
        if m.n == 0:
            continue
        for dn, d in m.discrete.items():
            for a in ("zu", "zl", "zi"):
                v = getattr(d, a, None)
                if v is None:
                    continue
                nv = np.asarray(v).size
                v[:] = np.asarray(flags[k:k + nv]).reshape(np.shape(v))
                k += nv
    assert k == len(flags)
    plant.K.apply_params(system, ctx, st, np.asarray(u, float))
    _, names = T.flag_vector(system)
    return system, ctx, st


def closed_loop(plant, system, ctx, st, u):
    y = system.dae.y
    p, q, v, om = (np.asarray(y[st[k]], float) for k in ("a_p", "a_q", "a_v", "a_f"))
    vn = plant.K.rdc_rates(st, ctx, u[:10], u[10:], p, q, v, om)
    st = dict(st, pset=np.asarray(u[:10], float), qset=np.asarray(u[10:], float))
    pred = plant.PR.LinearPredictor(ctx)
    pred.lim = ctx["lim"]
    b = pred.build(system, st, vn[:10], vn[10:], 1999.0, refresh_params=True)
    return b, vn, st


def discrete_spectrum(M, n, h):
    """Closed loop as executed by the TDS: plant over one step with the references held (exact ZOH of the linearised plant) and the explicit RDC update
    u_k = u_{k-1} + h v(y_{k-1}, u_{k-1}) applied before the step.  Returns eigenvalues as equivalent continuous rates ln(lambda)/h."""
    from scipy.linalg import expm
    A, B, Ky, K = M[:n, :n], M[:n, n:], M[n:, :n], M[n:, n:]
    m = B.shape[1]
    E = expm(np.block([[A, B], [np.zeros((m, n)), np.zeros((m, m))]]) * h)
    Phi, Gam = E[:n, :n], E[:n, n:]
    I = np.eye(m)
    D = np.block([[Phi + Gam @ (h * Ky), Gam @ (I + h * K)], [h * Ky, I + h * K]])
    lam = np.linalg.eigvals(D)
    return np.log(lam.astype(complex)) / h


def mode_near(ev, f0=1.25, band=(0.8, 1.8)):
    w = np.abs(ev.imag) / (2 * np.pi)
    k = np.where((w >= band[0]) & (w <= band[1]) & (ev.imag > 0))[0]
    if k.size == 0:
        return None
    j = k[np.argmax(ev.real[k])]
    return j


def stage_ins():
    """Frozen-time linearisations of plant + B2 at the snapshots of D57INS_OC3_M0_B2_presettle_snap (state, flags and references as in the TDS):
    rightmost mode, the 0.8-1.8 Hz pair with the largest real part, its participation factors, the discrete-time spectrum of the executed loop at
    h = dt, dt/2, dt/4, and first-order sensitivities of that pair to the B2 gains (linearisation only)."""
    import dec057_tds as T
    t0 = time.time()
    s = np.load(T.RUNS / "D57INS_OC3_M0_B2_presettle_snap" / "series.npz", allow_pickle=False)
    z = np.array(json.loads((C55.STATE / "m0_OC3.json").read_text(encoding="utf-8"))["z"])
    plant = OCM.make_plant("OC3")
    e8 = plant.e8
    out = {"source": "D57INS_OC3_M0_B2_presettle_snap", "snapshots": []}
    for i, ts in enumerate(s["snap_t"]):
        j = int(np.where(np.abs(s["cmd_t"] - ts) < 1e-9)[0][0])
        u = np.concatenate([s["cmd_pset"][j], s["cmd_qset"][j]])
        system, ctx, st = load_state(plant, z, s["snap_x"][i], s["snap_y"][i], s["snap_flags"][i], u)
        b, vn, st2 = closed_loop(plant, system, ctx, st, u)
        M, n = b["M"], b["n_dyn"]
        ev, W = np.linalg.eig(M)
        jr = int(np.argmax(np.where(np.abs(ev) > 1e-8, ev.real, -np.inf)))
        jm = mode_near(ev)
        rec = {"t": float(ts), "rates_inf": float(np.abs(vn).max()), "rightmost": [float(ev[jr].real), float(ev[jr].imag)],
               "n_re_gt_1e-9_excl_null": int(((ev.real > 1e-9) & (np.abs(ev) > 1e-8)).sum())}
        if jm is not None:
            wl = np.linalg.inv(W)[jm]
            pf = np.abs(W[:, jm] * wl)
            pf /= pf.sum()
            names = [str(system.dae.x_name[k]) for k in plant.K.index_sets(system)["d_idx"]] + [f"Pset {u_}" for u_ in UNITS] + [f"Qset {u_}" for u_ in UNITS]
            top = np.argsort(-pf)[:10]
            rec["mode_1p25Hz"] = {"eig": [float(ev[jm].real), float(ev[jm].imag)], "f_hz": float(ev[jm].imag / (2 * np.pi)), "damping_ratio": float(-ev[jm].real / abs(ev[jm])),
                                  "participation_top": [[names[k] if k < len(names) else str(k), float(pf[k])] for k in top],
                                  "participation_rdc_states_sum": float(pf[n:].sum())}
            for hdiv in (1, 2, 4):
                ed = discrete_spectrum(M, n, C54.DT / hdiv)
                jd = mode_near(ed)
                rec["mode_1p25Hz"][f"discrete_h_dt/{hdiv}"] = [float(ed[jd].real), float(ed[jd].imag)] if jd is not None else None
            if i % 6 == 0 or ts >= 310:
                sens = {}
                for name in ("K_IQ", "K_V", "K_Q", "K_P", "K_LEAK", "k_ip"):
                    if name == "k_ip":
                        stp = dict(st, k_ip=st["k_ip"] * 1.01)
                        bb, _, _ = closed_loop(plant, system, ctx, stp, u)
                    else:
                        old = getattr(e8, name)
                        setattr(e8, name, old * 1.01)
                        try:
                            bb, _, _ = closed_loop(plant, system, ctx, st, u)
                        finally:
                            setattr(e8, name, old)
                    e2 = np.linalg.eigvals(bb["M"])
                    k2 = mode_near(e2)
                    sens[name] = {"dRe_per_1pct": float(e2[k2].real - ev[jm].real), "dIm_per_1pct": float(e2[k2].imag - ev[jm].imag)} if k2 is not None else None
                rec["mode_1p25Hz"]["sensitivity_+1pct"] = sens
        out["snapshots"].append(rec)
        print(round(float(ts), 3), rec["rightmost"], rec.get("mode_1p25Hz", {}).get("eig"), {k: v for k, v in rec.get("mode_1p25Hz", {}).items() if k.startswith("discrete")}, flush=True)
    out["seconds"] = round(time.time() - t0, 1)
    save("ins_snapshots", out)


def fd_jacobian(plant, system, ctx, st, u, cache, h=1e-7):
    """Independent check of the closed-loop Jacobian M: central finite differences of F(x_d, u) = [x_d' ; v_B2], with the quasi-algebraic states and the
    algebraic variables re-solved (dec051_core.inner_solve, actuator maps exact) at every evaluation."""
    K = plant.K
    ix = K.index_sets(system)
    d = ix["d_idx"]
    tf = ix["tf"]
    x0, y0 = np.array(system.dae.x), np.array(system.dae.y)

    def F(xd, uu):
        system.dae.x[:] = x0
        system.dae.y[:] = y0
        system.dae.x[d] = xd
        system.vars_to_models()
        info = K.inner_solve(system, ctx, st, uu, ix, cache, tol=1e-12)
        f, g = K.fg_all(system)
        y = system.dae.y
        p, q, v, om = (np.asarray(y[st[k]], float) for k in ("a_p", "a_q", "a_v", "a_f"))
        return np.concatenate([f[d] / tf[d], K.rdc_rates(st, ctx, uu[:10], uu[10:], p, q, v, om)]), info["converged"]
    xd0 = x0[d].copy()
    n, m = len(d), len(u)
    J = np.zeros((n + m, n + m))
    bad = 0
    for k in range(n + m):
        hk = h * max(1.0, abs(xd0[k]) if k < n else abs(u[k - n]))
        xp, xm, up, um = xd0.copy(), xd0.copy(), np.array(u, float), np.array(u, float)
        if k < n:
            xp[k] += hk
            xm[k] -= hk
        else:
            up[k - n] += hk
            um[k - n] -= hk
        Fp, c1 = F(xp, up)
        Fm, c2 = F(xm, um)
        bad += (not c1) + (not c2)
        J[:, k] = (Fp - Fm) / (2 * hk)
    F(xd0, np.array(u, float))
    return J, bad


def stage_fdcheck():
    """FD Jacobian vs the predictor M at t = 0 (initialised OC3 M0 point) and at the 200-s and 300-s snapshots of the INS run."""
    import dec057_tds as T
    t0 = time.time()
    z = np.array(json.loads((C55.STATE / "m0_OC3.json").read_text(encoding="utf-8"))["z"])
    plant = OCM.make_plant("OC3")
    s = np.load(T.RUNS / "D57INS_OC3_M0_B2_presettle_snap" / "series.npz", allow_pickle=False)
    out = {}
    cases = [("t0", None)] + [(f"t{int(v)}", list(np.round(s["snap_t"], 6)).index(v)) for v in (200.0, 300.0)]
    for tag, i in cases:
        if i is None:
            system, ctx, _ = plant._make(z)
            st = plant.K.rdc_state(system, ctx)
            u = np.concatenate([st["pn"], st["qn"]])
            plant.K.apply_params(system, ctx, st, u)
        else:
            ts = s["snap_t"][i]
            j = int(np.where(np.abs(s["cmd_t"] - ts) < 1e-9)[0][0])
            u = np.concatenate([s["cmd_pset"][j], s["cmd_qset"][j]])
            system, ctx, st = load_state(plant, z, s["snap_x"][i], s["snap_y"][i], s["snap_flags"][i], u)
        b, vn, st2 = closed_loop(plant, system, ctx, st, u)
        M, n = b["M"], b["n_dyn"]
        J, bad = fd_jacobian(plant, system, ctx, st2, u, _cache_for(plant, system, ctx, st2, u))
        eM, eJ = np.linalg.eigvals(M), np.linalg.eigvals(J)
        jm, jj = mode_near(eM), mode_near(eJ)
        rel = float(np.abs(J - M).max() / np.abs(M).max()) if J.shape == M.shape else None
        blocks = {}
        if J.shape == M.shape:
            for nm, sl in (("A", (slice(0, n), slice(0, n))), ("B", (slice(0, n), slice(n, None))), ("Ky", (slice(n, None), slice(0, n))), ("K", (slice(n, None), slice(n, None)))):
                blocks[nm] = {"max_abs_diff": float(np.abs(J[sl] - M[sl]).max()), "max_abs_M": float(np.abs(M[sl]).max())}
        out[tag] = {"n_dyn_M": int(n), "shape_M": list(M.shape), "shape_J": list(J.shape), "inner_not_converged": int(bad), "max_rel_diff": rel, "blocks": blocks,
                    "pair_M": [float(eM[jm].real), float(eM[jm].imag)] if jm is not None else None, "pair_FD": [float(eJ[jj].real), float(eJ[jj].imag)] if jj is not None else None,
                    "rightmost_M": sorted([[float(a.real), float(a.imag)] for a in eM], key=lambda r: -r[0])[:4],
                    "rightmost_FD": sorted([[float(a.real), float(a.imag)] for a in eJ], key=lambda r: -r[0])[:4]}
        print(tag, {k: v for k, v in out[tag].items() if k not in ("blocks",)}, out[tag]["blocks"], flush=True)
    out["seconds"] = round(time.time() - t0, 1)
    save("ins_fdcheck", out)


def _cache_for(plant, system, ctx, st, u):
    pred = plant.PR.LinearPredictor(ctx)
    pred.lim = ctx["lim"]
    plant.K.apply_params(system, ctx, st, u)
    plant.L.linearize(system, ctx, cache=pred.cache)
    return pred.cache


if __name__ == "__main__":
    {"b3eq": stage_b3eq, "seedrule": stage_seedrule, "ins": stage_ins, "fdcheck": stage_fdcheck}[sys.argv[1]](*sys.argv[2:])
