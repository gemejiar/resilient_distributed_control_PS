"""DEC-056 / OC3: diagnosis of the M3 design failure of DEC-055 (SOLVER_FAILED, 'Iteration limit reached' in the FIRST NLP of Algorithm 1).  NO TDS.
Same problem as dec055_l0.stage_m3 (DESIGN = {8,23,28,25} x {S1,S2,S3}, eps of DEC-054, cfg of DEC-055); nothing of the M3 formulation is changed.

  point       margins and base constraints at the failed point and at the M0 seed; initial working set; finite-difference gradient noise of the most violated
              margins for h = 1e-2 .. 1e-6; Jacobian conditioning and column scaling; linearised feasibility LP  max t  s.t.  m + G dz >= t  (all 12 scenarios,
              both sides, and the base constraints) for three trust radii
  trace       reduced replication of the failing NLP (SLSQP from the M0 seed, working set W0, 6 iterations) with every constraint evaluation logged
  phase1      feasibility-first sequential LP: maximise the minimum design margin with exact re-evaluation and a trust region; stops at the first point whose
              exact minimum margin (all 12 scenarios x 10 units x 2 sides, base constraints) is >= 0
  seeded      Algorithm 1 unchanged (same cfg, N_it 25), seeds = [phase-1 point] only after phase1 succeeded (least invasive strategy: a new start point)
State: Paper_manuscript/backups/DEC056_state (exclusive)."""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

import dec054_common as C54
import dec055_common as C55
import dec055_oc as OCM

STATE = C54.RUNS_DIR.parent / "DEC056_state"
OC = "OC3"


def save(name, obj):
    STATE.mkdir(parents=True, exist_ok=True)
    with open(STATE / f"{name}.json", "x", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else (float(o) if np.isscalar(o) else str(o)))


def setup(workers, mode="M3"):
    """mode M3: the DEC-055 design problem; mode M2: the same problem with the jump margins only (eps_J kept, no excursion predictor)."""
    import dec054_g4_design as G4
    import dec054_opf as OPF
    import dec055_l0 as L0
    plant = OCM.OCPooledPlant(OC, workers)
    eJ, eEu, eEd = G4.eps_vectors()
    cfg = dict(C54.PROPOSED, K_max=8, N_it=25, ftol=1e-6, verbose=False)
    pb = OPF.Problem(plant, mode, L0.design_scenarios(), eJ, eEu, cfg=cfg, eps_E_dn=eEd)
    s3 = json.loads((C55.STATE / "m3_OC3.json").read_text(encoding="utf-8"))
    m0 = json.loads((C55.STATE / "m0_OC3.json").read_text(encoding="utf-8"))
    return plant, pb, OPF, np.array(s3["z"]), np.array(m0["z"])


def all_m(pb, z):
    """(240,) design margins in (scenario, side, unit) order and the base constraints."""
    pb._pf([z], set(range(len(pb.sc))))
    v = []
    for d in range(len(pb.sc)):
        up, dn, _ = pb.margins_d(z, d)
        v.append(np.concatenate([up, dn]))
    return np.concatenate(v), pb.base(z)


def label(k, pb):
    d, r = divmod(k, 20)
    side, i = divmod(r, 10)
    return f"{pb.sc[d].name}:{'P+' if side == 0 else 'P-'}:{C55.UNITS[i]}"


def jac(pb, z, h, lo, hi):
    zs = []
    for k in range(len(z)):
        zz = z.copy()
        zz[k] += h if z[k] + h <= hi[k] else -h
        zs.append(zz)
    pb._pf([z] + zs, set(range(len(pb.sc))))
    m0, b0 = all_m(pb, z)
    Gm, Gb = np.zeros((m0.size, len(z))), np.zeros((b0.size, len(z)))
    for k, zz in enumerate(zs):
        m1, b1 = all_m(pb, zz)
        s = (zz[k] - z[k])
        Gm[:, k], Gb[:, k] = (m1 - m0) / s, (b1 - b0) / s
    return m0, b0, Gm, Gb


def lp_step(m, b, Gm, Gb, z, lo, hi, rp, rv):
    """max t  s.t.  m + Gm dz >= t,  b + Gb dz >= 0 (base, kept feasible),  bounds and |dz| <= r  (scipy HiGHS)."""
    from scipy.optimize import linprog
    n = len(z)
    r = np.concatenate([np.full(9, rp), np.full(n - 9, rv)])
    lb, ub = np.maximum(lo - z, -r), np.minimum(hi - z, r)
    c = np.zeros(n + 1)
    c[-1] = -1.0
    A = np.vstack([np.hstack([-Gm, np.ones((Gm.shape[0], 1))]), np.hstack([-Gb, np.zeros((Gb.shape[0], 1))])])
    rhs = np.concatenate([m, np.maximum(b, 0.0)])                 # base rows: keep b + Gb dz >= min(b, 0)
    res = linprog(c, A_ub=A, b_ub=rhs, bounds=list(zip(lb, ub)) + [(None, None)], method="highs")
    return (res.x[:n], float(res.x[-1]), res.status) if res.status == 0 else (np.zeros(n), float("nan"), res.status)


def stage_point(workers=7):
    t0 = time.time()
    plant, pb, OPF, zf, z0 = setup(workers)
    lo, hi = np.array(plant.z_lo), np.array(plant.z_hi)
    out = {"oc": OC, "z_fail": zf, "z_M0": z0, "dz_fail_vs_M0": zf - z0, "redispatch_MW_fail_vs_M0": float(np.abs(zf[:9] - z0[:9]).sum() * 100)}
    try:
        W0 = OPF.initial_working_set(pb, 4)
        out["W0_scenarios"] = sorted({pb.sc[d].name for (d, _, _) in W0})
        for nm, z in (("fail", zf), ("M0", z0)):
            m, b = all_m(pb, z)
            neg = np.where(m < 0)[0]
            out[nm] = {"min_margin": float(m.min()), "argmin": label(int(m.argmin()), pb), "n_negative_margins": int(neg.size), "n_margins": int(m.size),
                       "negative": {label(int(k), pb): float(m[k]) for k in neg[np.argsort(m[neg])][:30]}, "min_base": float(b.min()), "n_negative_base": int((b < 0).sum()),
                       "n_failed_evaluations": int((m <= -999).sum()), "J": float(pb.J(z)),
                       "W0_constraint_min": float(pb.constraints(z, W0).min()), "W0_n_negative": int((pb.constraints(z, W0) < 0).sum())}
            print(nm, {k: out[nm][k] for k in ("min_margin", "argmin", "n_negative_margins", "min_base", "n_failed_evaluations", "W0_constraint_min", "W0_n_negative")}, flush=True)
        # finite-difference noise of the 6 most violated margins and of J
        m, b = all_m(pb, zf)
        worst = list(np.argsort(m)[:6])
        hs = [1e-2, 1e-3, 1e-4, 1e-5, 1e-6]
        D = {}
        for h in hs:
            mm, bb, Gm, Gb = jac(pb, zf, h, lo, hi)
            D[h] = Gm[worst]
            out.setdefault("jac_by_h", {})[str(h)] = {"Gm_worst": Gm[worst], "col_norm_Gm": np.linalg.norm(Gm, axis=0), "sv_Gm_negative_rows": np.linalg.svd(Gm[m < 0], compute_uv=False) if (m < 0).any() else []}
            print("h", h, "done", round(time.time() - t0), "s", flush=True)
        ref = D[1e-4]
        out["fd_noise"] = {str(h): {"max_rel_diff_vs_h1e-4": float(np.abs(D[h] - ref).max() / max(np.abs(ref).max(), 1e-12)), "max_abs_diff_vs_h1e-4": float(np.abs(D[h] - ref).max())} for h in hs}
        out["worst_rows"] = [label(int(k), pb) for k in worst]
        # linearised feasibility at the failed point (h = 1e-4 Jacobian)
        mm, bb, Gm, Gb = jac(pb, zf, 1e-4, lo, hi)
        out["linear_feasibility"] = {}
        for rp, rv in ((0.05, 0.01), (0.2, 0.02), (1.0, 0.05), (3.0, 0.1)):
            dz, tt, stt = lp_step(mm, bb, Gm, Gb, zf, lo, hi, rp, rv)
            out["linear_feasibility"][f"r_p={rp},r_v={rv}"] = {"t_star": tt, "lp_status": int(stt), "dz": dz, "redispatch_MW": float(np.abs(dz[:9]).sum() * 100)}
            print("LP", rp, rv, tt, stt, flush=True)
    finally:
        plant.close()
    out["seconds"] = round(time.time() - t0, 1)
    save("oc3_point", out)


def stage_trace(workers=7, nit=6):
    """SLSQP from the M0 seed on the initial working set, exactly as solve_nlp does, with a log of every constraint evaluation."""
    from scipy.optimize import minimize
    t0 = time.time()
    plant, pb, OPF, zf, z0 = setup(workers)
    lo, hi = np.array(plant.z_lo), np.array(plant.z_hi)
    log = []
    try:
        W = OPF.initial_working_set(pb, 4)
        bnds = OPF._bounds(plant)
        orig = pb.constraints

        def cons_logged(z, W=W):
            c = orig(z, W)
            log.append({"kind": "c", "z_dist_from_seed": float(np.abs(z - z0).max()), "min": float(c.min()), "n_neg": int((c < 0).sum()), "n_fail": int((c <= -999).sum()), "J": float(pb.J(z))})
            return c

        def jac_c(z):
            zs = [z]
            for k in range(len(z)):
                zz = z.copy()
                zz[k] += 1e-4 if z[k] + 1e-4 <= hi[k] else -1e-4
                zs.append(zz)
            pb._pf(zs, {d for (d, _, _) in W})
            return OPF._fd_jac(lambda x: orig(x, W), z, lo, hi)
        its = []

        def cb(xk):
            c = orig(xk, W)
            its.append({"it": len(its) + 1, "J": float(pb.J(xk)), "min_con": float(c.min()), "n_neg": int((c < 0).sum()), "step_from_seed_inf": float(np.abs(xk - z0).max())})
            print(its[-1], flush=True)
        res = minimize(pb.J, z0.copy(), method="SLSQP", bounds=bnds, constraints=[{"type": "ineq", "fun": cons_logged, "jac": jac_c}], callback=cb,
                       jac=lambda z: OPF._fd_jac(lambda x: pb.J(x), z, lo, hi)[0], options={"maxiter": nit, "ftol": 1e-6})
        out = {"W0_size": len(W), "W0_scenarios": sorted({pb.sc[d].name for (d, _, _) in W}), "slsqp": {"status": int(res.status), "message": str(res.message), "nit": int(res.nit)},
               "iterations": its, "evaluations": log, "z_end": res.x, "dist_end_vs_fail_point": float(np.abs(res.x - zf).max())}
    finally:
        plant.close()
    out["seconds"] = round(time.time() - t0, 1)
    save("oc3_trace", out)
    print("trace", out["slsqp"], out["dist_end_vs_fail_point"], flush=True)


def stage_phase1(workers=7, itmax=12, mode=None):
    """mode M2 (default, env DEC056_PHASE1_MODE): restore jump admissibility first, because the M3 excursion predictor is undefined (unstable post-jump
    linearisation, ok=False sentinel -1e3) wherever the jump is inadmissible; the M3 margins are then evaluated exactly at the result."""
    t0 = time.time()
    mode = mode or os.environ.get("DEC056_PHASE1_MODE", "M2")
    plant, pb, OPF, zf, z0 = setup(workers, mode)
    lo, hi = np.array(plant.z_lo), np.array(plant.z_hi)
    z = z0.copy()
    rp, rv = 0.2, 0.02
    hist = []
    try:
        m, b = all_m(pb, z)
        for it in range(itmax):
            cur = min(float(m.min()), float(b.min()) if b.min() < 0 else np.inf)
            mm, bb, Gm, Gb = jac(pb, z, 1e-4, lo, hi)
            dz, tt, stt = lp_step(mm, bb, Gm, Gb, z, lo, hi, rp, rv)
            zt = z + dz
            mt, bt = all_m(pb, zt)
            new = float(mt.min())
            acc = bool(new > float(m.min()) and bt.min() >= min(0.0, b.min()) - 1e-9)
            hist.append({"it": it, "min_margin": float(m.min()), "argmin": label(int(m.argmin()), pb), "lp_t": tt, "lp_status": int(stt), "trial_min_margin": new, "trial_argmin": label(int(mt.argmin()), pb),
                         "trial_min_base": float(bt.min()), "accepted": acc, "r_p": rp, "r_v": rv, "step_inf": float(np.abs(dz).max()), "redispatch_MW_vs_M0": float(np.abs(zt[:9] - z0[:9]).sum() * 100)})
            print(hist[-1], flush=True)
            if acc:
                z, m, b = zt, mt, bt
                rp, rv = min(rp * 1.5, 2.0), min(rv * 1.5, 0.05)
            else:
                rp, rv = rp * 0.5, rv * 0.5
            if m.min() >= 0 and b.min() >= 0:
                break
            if rp < 1e-3:
                break
        out = {"mode": mode, "z": z, "min_margin": float(m.min()), "argmin": label(int(m.argmin()), pb), "min_base": float(b.min()), "feasible_design_constraints": bool(m.min() >= 0 and b.min() >= 0),
               "J": float(pb.J(z)), "redispatch_MW_vs_M0": float(np.abs(z[:9] - z0[:9]).sum() * 100), "dz_vs_M0": z - z0, "history": hist, "n_negative": int((m < 0).sum())}
        if mode == "M2":                   # exact M3 margins at the jump-admissible point
            pb3 = OPF.Problem(plant, "M3", pb.sc, pb.eps_J, pb.eps_E, cfg=pb.cfg, eps_E_dn=pb.eps_E_dn)
            m3, b3 = all_m(pb3, z)
            out["M3_at_result"] = {"min_margin": float(m3.min()), "argmin": label(int(m3.argmin()), pb3), "n_negative": int((m3 < 0).sum()), "n_predictor_failed": int((m3 <= -999).sum()) // 1,
                                   "feasible": bool(m3.min() >= 0 and b3.min() >= 0)}
            out["feasible_design_constraints_M3"] = out["M3_at_result"]["feasible"]
    finally:
        plant.close()
    out["seconds"] = round(time.time() - t0, 1)
    save("oc3_phase1", out)
    print("phase1", {k: out[k] for k in ("min_margin", "argmin", "min_base", "feasible_design_constraints", "J", "redispatch_MW_vs_M0", "seconds")}, flush=True)


def lp_minnorm(m, b, Gm, Gb, z, lo, hi, tau, scale):
    """min sum |dz_k| / scale_k  s.t.  m + Gm dz >= tau,  b + Gb dz >= min(b, 0),  bounds (HiGHS; dz = dp - dn)."""
    from scipy.optimize import linprog
    n = len(z)
    c = np.concatenate([1.0 / scale, 1.0 / scale])
    A = np.vstack([np.hstack([-Gm, Gm]), np.hstack([-Gb, Gb])])
    rhs = np.concatenate([m - tau, np.maximum(b, 0.0)])
    bnds = [(0, max(hi[k] - z[k], 0.0)) for k in range(n)] + [(0, max(z[k] - lo[k], 0.0)) for k in range(n)]
    res = linprog(c, A_ub=A, b_ub=rhs, bounds=bnds, method="highs")
    return (res.x[:n] - res.x[n:], res.status) if res.status == 0 else (None, res.status)


def stage_phase1b(workers=7, itmax=10, tau=0.002):
    """Feasibility restoration of the JUMP margins (M2 rows) by minimum-norm sequential LP with exact re-evaluation and a backtracking line search on
    initialisation validity (the ANDES initialisation is not valid everywhere inside the OPF variable bounds, e.g. TGOV1N VMIN).  M3 margins evaluated
    exactly at the end.  A failure is not a proof of infeasibility."""
    t0 = time.time()
    plant, pb, OPF, zf, z0 = setup(workers, "M2")
    lo, hi = np.array(plant.z_lo), np.array(plant.z_hi)
    scale = np.concatenate([np.full(9, 0.5), np.full(10, 0.05)])           # the C_disp scales of the M0-M3 objective (p_scale, v_scale)
    z = z0.copy()
    hist = []
    try:
        m, b = all_m(pb, z)
        for it in range(itmax):
            mm, bb, Gm, Gb = jac(pb, z, 1e-4, lo, hi)
            dz, stt = lp_minnorm(mm, bb, Gm, Gb, z, lo, hi, tau, scale)
            if dz is None:
                hist.append({"it": it, "lp_status": int(stt), "note": "linearised min-norm LP infeasible"})
                print(hist[-1], flush=True)
                break
            lam, acc = 1.0, False
            while lam >= 1 / 16:
                zt = z + lam * dz
                mt, bt = all_m(pb, zt)
                if mt.min() > -999 and bt.min() > -999 and mt.min() > m.min():
                    acc = True
                    break
                lam *= 0.5
            hist.append({"it": it, "min_margin": float(m.min()), "argmin": label(int(m.argmin()), pb), "lp_status": int(stt), "step_l1_scaled": float(np.sum(np.abs(dz) / scale)),
                         "lam": lam, "accepted": acc, "trial_min_margin": float(mt.min()), "trial_argmin": label(int(mt.argmin()), pb) if mt.min() > -999 else "INIT_OR_EVENT_FAILED",
                         "trial_min_base": float(bt.min()), "redispatch_MW_vs_M0": float(np.abs(zt[:9] - z0[:9]).sum() * 100)})
            print(hist[-1], flush=True)
            if not acc:
                break
            z, m, b = zt, mt, bt
            if m.min() >= 0 and b.min() >= -1e-9:
                break
        out = {"z": z, "min_jump_margin": float(m.min()), "argmin": label(int(m.argmin()), pb), "min_base": float(b.min()), "jump_admissible_all_design": bool(m.min() >= 0 and b.min() >= -1e-9),
               "redispatch_MW_vs_M0": float(np.abs(z[:9] - z0[:9]).sum() * 100), "dz_vs_M0": z - z0, "P": plant.evaluate(z)["P"], "history": hist, "tau": tau}
        pb3 = OPF.Problem(plant, "M3", pb.sc, pb.eps_J, pb.eps_E, cfg=pb.cfg, eps_E_dn=pb.eps_E_dn)
        m3, b3 = all_m(pb3, z)
        A_re = []
        for sc in pb.sc:
            try:
                A, f, C = plant.local.affine(z, sc)
                A_re.append(float(np.max(np.linalg.eigvals(A).real)))
            except Exception as ex:
                A_re.append(repr(ex)[:80])
        out["M3_at_result"] = {"min_margin": float(m3.min()), "argmin": label(int(m3.argmin()), pb3), "n_negative": int((m3 < 0).sum()), "n_predictor_failed_rows": int((m3 <= -999).sum()),
                               "feasible": bool(m3.min() >= 0 and b3.min() >= -1e-9), "post_jump_max_Re_eig_by_scenario": dict(zip([s.name for s in pb.sc], A_re))}
    finally:
        plant.close()
    out["seconds"] = round(time.time() - t0, 1)
    save("oc3_phase1b", out)
    print("phase1b", {k: out[k] for k in ("min_jump_margin", "argmin", "min_base", "jump_admissible_all_design", "redispatch_MW_vs_M0", "seconds")}, out["M3_at_result"], flush=True)


def stage_seeded(workers=7):
    import dec054_g4_design as G4
    """Seed = jump-admissible point of phase1b with the SG30 voltage set-point lowered by DEC056_DV30 (default -0.01 pu; the post-jump linearisations are
    Hurwitz modulo the angle null mode there, so the M3 rows are defined).  Algorithm 1 and its cfg unchanged unless DEC056_NIT / DEC056_KMAX are set for a
    REDUCED test (tag in the state-file name)."""
    t0 = time.time()
    p1 = json.loads((STATE / "oc3_phase1b.json").read_text(encoding="utf-8"))
    assert p1["jump_admissible_all_design"], "phase1b did not restore jump admissibility: seeded run not justified"
    dv30 = float(os.environ.get("DEC056_DV30", "-0.01"))
    seed = np.array(p1["z"])
    seed[9] += dv30
    plant, pb, OPF, zf, z0 = setup(workers)
    nit, kmax = os.environ.get("DEC056_NIT"), os.environ.get("DEC056_KMAX")
    cfg = dict(pb.cfg, **({"N_it": int(nit)} if nit else {}), **({"K_max": int(kmax)} if kmax else {}))
    tag = "reduced" if (nit or kmax) else "full"
    eJ, eEu, eEd = G4.eps_vectors()
    try:
        r = OPF.algorithm1(plant, "M3", pb.sc, eJ, eEu, cfg=cfg, z_seeds=[seed], k0=4, eps_E_dn=eEd,
                           log=lambda x: print("  iter", {k: x[k] for k in ("k", "W", "min_margin", "J")}, flush=True))
        out = {"status": r.status, "J": r.J, "kkt": r.kkt_residual, "iterations": r.iterations, "detail": r.detail, "cuts": r.cuts, "log": r.log, "z": r.z, "seed_z": seed,
               "seed": f"phase1b point with SG30 v0 {dv30:+.3f} pu; z_ref is always tried first by Algorithm 1", "cfg_N_it": cfg["N_it"], "cfg_K_max": cfg["K_max"], "tag": tag}
        if r.z is not None:
            m, b = all_m(pb, np.asarray(r.z))
            out.update({"exact_min_margin_all_design": float(m.min()), "exact_min_base": float(b.min()), "redispatch_MW_vs_M0": float(np.abs(np.asarray(r.z)[:9] - z0[:9]).sum() * 100)})
    finally:
        plant.close()
    out["seconds"] = round(time.time() - t0, 1)
    save(f"oc3_seeded_{tag}", out)
    print("seeded", {k: out.get(k) for k in ("status", "J", "iterations", "exact_min_margin_all_design", "redispatch_MW_vs_M0", "seconds")}, flush=True)


if __name__ == "__main__":
    w = int(os.environ.get("DEC056_WORKERS", "7"))
    {"point": stage_point, "trace": stage_trace, "phase1": stage_phase1, "phase1b": stage_phase1b, "seeded": stage_seeded}[sys.argv[1]](w)
