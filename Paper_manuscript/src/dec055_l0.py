"""DEC-055 Lot L0 (NO time integration: PFlow, TDS.init without steps, algebraic solves, static OPF, linearisations only).

Stages (state files in Paper_manuscript/backups/DEC055_state, exclusive; final artefacts in Paper_manuscript/artifacts, exclusive):
    init                 OC reference points: PFlow + TDS.init validity at z_ref of OC1..OC3
    m0  <OC>             static AC-OPF M0 of the OC (identical objective to DEC-054)
    m3  <OC>             provisional M3 design (Algorithm 1) on DESIGN = {8,23,28,25} x {S1,S2,S3}; eps = DEC-054 calibration (TUNE-OC1 data); NOT frozen
    tc  <OC>             T-C class of every cell of the OC (capacity condition + AC feasibility with limits + ANDES PFlow/TDS.init verification)
    ta  <OC>             T-A margins at t_e+ of every cell of the OC for the M0 and provisional M3 dispatches
Run: <venv python> dec055_l0.py <stage> [OC]"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

import dec054_common as C54
import dec055_common as C
import dec055_oc as OCM

STATE = C.STATE


def save(name, obj):
    STATE.mkdir(parents=True, exist_ok=True)
    with open(STATE / f"{name}.json", "x", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else float(o))


def load(name):
    p = STATE / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def oc_events(oc):
    """(partition, bus, severity) of every cell of the OC (strategy-independent)."""
    seen, out = set(), []
    for r in C.enumerate_cells():
        k = (r["partition"], r["bus"], r["severity"])
        if r["oc"] == oc and k not in seen:
            seen.add(k)
            out.append(k)
    return out


# ---------------------------------------------------------------- init
def stage_init():
    res = {}
    for oc in C.OC:
        import subprocess
        code = ("import json,dec055_oc as O;p=O.make_plant('%s');e=p.evaluate(p.z_ref);r=e.get('init_report',{});"
                "print(json.dumps({'ok':e['ok'],'reason':e.get('reason'),'res_f':r.get('residual_f_inf'),'res_g':r.get('residual_g_inf'),"
                "'V_min':float(e['V'].min()) if e['ok'] else None,'V_max':float(e['V'].max()) if e['ok'] else None,'n_V_above_1.05':int((e['V']>1.05).sum()) if e['ok'] else None,"
                "'P':e['P'].tolist() if e['ok'] else None,'z_ref':p.z_ref.tolist(),'pmax':p.limits['pmax'].tolist()}))") % oc
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(C.SRC))
        res[oc] = json.loads(out.stdout.strip().splitlines()[-1]) if out.returncode == 0 else {"ok": False, "stderr": out.stderr[-2000:]}
        print(oc, {k: res[oc].get(k) for k in ("ok", "res_f", "res_g", "V_min", "V_max", "n_V_above_1.05")}, flush=True)
    save("init", res)


# ---------------------------------------------------------------- static designs
def design_scenarios():
    import dec054_opf as OPF
    return [OPF.Scenario(f"b{b}P_{s}", b, "P", C.oc_amp(s)) for b in C.DESIGN for s in C.SEVERITY]


def stage_m0(oc):
    import dec054_opf as OPF
    t0 = time.time()
    plant = OCM.make_plant(oc)
    cfg = dict(C54.PROPOSED, K_max=8, N_it=int(os.environ.get("DEC055_NIT", "25")), ftol=1e-6, verbose=False)
    r = OPF.solve_static(plant, "M0", design_scenarios(), cfg=cfg)
    e = plant.evaluate(r.z) if r.z is not None else {"ok": False}
    save(f"m0_{oc}", {"oc": oc, "method": "M0", "status": r.status, "J": r.J, "kkt": r.kkt_residual, "iterations": r.iterations, "detail": r.detail,
                      "z": None if r.z is None else r.z.tolist(), "z_ref": plant.z_ref.tolist(), "init_ok": bool(e["ok"]),
                      "P_pre": e["P"].tolist() if e["ok"] else None, "V_min": float(e["V"].min()) if e["ok"] else None, "V_max": float(e["V"].max()) if e["ok"] else None,
                      "seconds": round(time.time() - t0, 1)})
    print(oc, "M0", r.status, r.J, round(time.time() - t0, 1), "s", flush=True)


def stage_m3(oc):
    import dec054_g4_design as G4
    import dec054_opf as OPF
    t0 = time.time()
    m0 = load(f"m0_{oc}")
    assert m0 and m0["z"] is not None and m0["init_ok"], "M0 of the OC is required as a seed"
    plant = OCM.OCPooledPlant(oc, int(os.environ.get("DEC055_WORKERS", "2")))
    eJ, eEu, eEd = G4.eps_vectors()                 # DEC-054 calibration (P3-A + P3-B round 1): TUNE-OC1 data, provisional for OC2/OC3 until L2
    cfg = dict(C54.PROPOSED, K_max=8, N_it=int(os.environ.get("DEC055_NIT", "25")), ftol=1e-6, verbose=False)
    try:
        r = OPF.algorithm1(plant, "M3", design_scenarios(), eJ, eEu, cfg=cfg, z_seeds=[np.array(m0["z"])], k0=4, eps_E_dn=eEd,
                           log=lambda x: print(oc, "  iter", {k: x[k] for k in ("k", "W", "min_margin", "J")}, flush=True))
        out = {"oc": oc, "method": "M3", "status": r.status, "J": r.J, "kkt": r.kkt_residual, "iterations": r.iterations, "detail": r.detail, "cuts": r.cuts, "log": r.log,
               "z": None if r.z is None else r.z.tolist(), "eps": {"J": eJ.tolist(), "E_up": eEu.tolist(), "E_dn": eEd.tolist(), "source": "DEC-054 P3-A + P3-B round 1 (TUNE-OC1)"},
               "event_tasks": plant.n_event_tasks, "plant_evaluations": plant.n_eval, "pool_rebuilds": plant.pool_rebuilds, "seconds": round(time.time() - t0, 1),
               "provisional": True}
        if r.z is not None:
            e = plant.evaluate(r.z)
            out.update({"init_ok": bool(e["ok"]), "P_pre": e["P"].tolist() if e["ok"] else None, "V_min": float(e["V"].min()) if e["ok"] else None,
                        "V_max": float(e["V"].max()) if e["ok"] else None, "redispatch_MW_abs_sum": float(np.abs(r.z[:9] - plant.z_ref[:9]).sum() * 100)})
        save(f"m3_{oc}", out)
        print(oc, "M3", r.status, r.J, round(time.time() - t0, 1), "s", flush=True)
    finally:
        plant.close()


# ---------------------------------------------------------------- T-C
def ac_feasible(bus, amp, margin=1e-6):
    """(C-i) static AC feasibility of the post-event load with the implemented limits (P, Q, S of the 10 units, 0.95-1.05 pu on 39 buses), unit P/Q free.
    SLSQP on the full AC network (select_equilibrium_b3.network), then verification by an ANDES PFlow at the solution set-points.  A failure is not a proof."""
    import select_equilibrium_b3 as b3
    from scipy.optimize import minimize
    s = b3.load_plant({bus: (amp, 0.0)})
    s.PFlow.config.tol = OCM.PFLOW_TOL
    s.PFlow.run()
    y, buses, pl, ql = b3.network(s)
    lim = b3.unit_limits(s)
    n = len(buses)
    u_pos = np.array([buses.index(b) for b in lim["unit_bus"]])
    slack_pos = buses.index(int(s.Slack.bus.v[0]))
    slack_angle = float(s.Slack.a0.v[0]) if hasattr(s.Slack, "a0") else 0.0
    other = np.array([i for i in range(n) if i not in set(u_pos)])
    free = np.array([i for i in range(n) if i != slack_pos])
    nx = n + len(free)

    def unpack(x):
        a = np.zeros(n)
        a[free] = x[n:]
        a[slack_pos] = slack_angle
        return x[:n], a

    def inj(x):
        v, a = unpack(x)
        vc = v * np.exp(1j * a)
        ib = y @ vc
        return v, vc, ib, vc * np.conj(ib)

    def ds_dx(x):
        v, vc, ib, _ = inj(x)
        dv = np.diag(vc / v)
        dsa = 1j * np.diag(vc) @ np.conj(np.diag(ib) - y @ np.diag(vc))
        dsm = np.diag(vc) @ np.conj(y @ dv) + np.diag(np.conj(ib)) @ dv
        return np.hstack([dsm, dsa[:, free]])

    def unit_pq(x):
        v, _, _, si = inj(x)
        return si.real[u_pos] + pl[u_pos], si.imag[u_pos] + ql[u_pos], v

    v0, a0 = np.asarray(s.Bus.v.v, float), np.asarray(s.Bus.a.v, float)
    x0 = np.concatenate([np.clip(v0, 0.951, 1.049), a0[free]])
    p0, q0, _ = unit_pq(np.concatenate([v0, a0[free]]))
    rp = lim["pmax"] - lim["pmin"]

    def obj(x):
        p, q, v = unit_pq(x)
        return float(np.sum(((p - p0) / rp) ** 2) + np.sum(((v[u_pos] - v0[u_pos]) / 0.05) ** 2))

    def eq(x):
        _, _, _, si = inj(x)
        return np.concatenate([si.real[other] + pl[other], si.imag[other] + ql[other]])

    def eq_jac(x):
        d = ds_dx(x)
        return np.vstack([d.real[other], d.imag[other]])

    def ineq(x, m=margin):
        p, q, v = unit_pq(x)
        return np.concatenate([lim["pmax"] - m - p, p - lim["pmin"] - m, lim["qmax"] - m - q, q - lim["qmin"] - m, (lim["smax"] - m) ** 2 - p ** 2 - q ** 2, v - 0.95 - m, 1.05 - m - v])

    def ineq_jac(x):
        p, q, v = unit_pq(x)
        d = ds_dx(x)
        dp, dq = d.real[u_pos], d.imag[u_pos]
        ev = np.zeros((n, nx))
        ev[np.arange(n), np.arange(n)] = 1.0
        return np.vstack([-dp, dp, -dq, dq, -2 * p[:, None] * dp - 2 * q[:, None] * dq, ev, -ev])

    res = minimize(obj, x0, method="SLSQP", constraints=[{"type": "eq", "fun": eq, "jac": eq_jac}, {"type": "ineq", "fun": ineq, "jac": ineq_jac}], options={"maxiter": 500, "ftol": 1e-12})
    p, q, v = unit_pq(res.x)
    out = {"success": bool(res.success), "message": str(res.message), "eq_residual_opt": float(np.abs(eq(res.x)).max()), "ineq_min_opt": float(ineq(res.x, 0.0).min()),
           "P": p.tolist(), "Q": q.tolist(), "V_unit": v[u_pos].tolist(), "andes_verified": False}
    if not res.success:
        return out
    # ANDES verification: PFlow at the solution set-points (PV p0, PV/Slack v0), then TDS.init (no steps): plant initialisable at that point
    s2 = b3.load_plant({bus: (amp, 0.0)}, p_star=p, v_star=v[u_pos], unit_bus=lim["unit_bus"])
    s2.PFlow.config.tol = OCM.PFLOW_TOL
    ok = bool(s2.PFlow.run()) and s2.PFlow.converged
    if ok:
        s2.TDS.init()
    y2 = np.asarray(s2.dae.y, float)
    vb = np.asarray(s2.Bus.v.v, float)
    gres = float(np.abs(s2.dae.g).max())
    st_p = np.concatenate([np.asarray(y2[s2.GENROU.Pe.a]), np.asarray(y2[s2.REGF1.Pe.a])]) if ok else np.full(10, np.nan)
    st_q = np.concatenate([np.asarray(y2[s2.GENROU.Qe.a]), np.asarray(y2[s2.REGF1.Qe.a])]) if ok else np.full(10, np.nan)
    g = np.concatenate([lim["pmax"] - st_p, st_p - lim["pmin"], lim["qmax"] - st_q, st_q - lim["qmin"], lim["smax"] - np.hypot(st_p, st_q), vb - 0.95, 1.05 - vb]) if ok else np.array([-np.inf])
    out.update({"andes_pflow_ok": ok, "andes_tds_init_ok": bool(getattr(s2.TDS, "initialized", False)), "eq_residual": gres, "ineq_min": float(g.min()),
                "andes_verified": bool(ok and getattr(s2.TDS, "initialized", False) and gres <= C.THR["ac_eq_residual"] and g.min() >= -C.THR["ac_ineq_tol"]),
                "P_andes": st_p.tolist(), "V_min_andes": float(vb.min()), "V_max_andes": float(vb.max())})
    return out


def stage_tc(oc):
    OCM.select(oc)
    import select_equilibrium_b3 as b3
    s = b3.load_plant()
    lim = b3.unit_limits(s)
    load0 = float(np.sum(s.PQ.p0.v))
    out = {"oc": oc, "pmax_total": float(lim["pmax"].sum()), "load_total_pre": load0, "cells": {}}
    for part, bus, sev in oc_events(oc):
        amp = C.oc_amp(sev)
        cap = C.capacity_necessary(float(lim["pmax"].sum()), load0 + amp)
        try:
            ac = ac_feasible(bus, amp)
        except Exception as ex:
            ac = {"success": False, "error": repr(ex)}
        cls = C.classify_tc(cap, ac)
        out["cells"][f"{part}_b{bus}_{sev}"] = {"capacity_ok": cap, "tc_class": cls, **ac}
        print(oc, part, bus, sev, cls, ac.get("message", ac.get("error", ""))[:60], flush=True)
    save(f"tc_{oc}", out)


# ---------------------------------------------------------------- T-A
def load_ta(oc):
    """Merged T-A record of the OC (one state file per method)."""
    out = {"oc": oc, "dispatch_status": {}, "cells": {}}
    for m in ("M0", "M3"):
        t = load(f"ta_{oc}_{m}")
        if not t:
            continue
        out["dispatch_status"].update(t["dispatch_status"])
        for k, v in t["cells"].items():
            out["cells"].setdefault(k, {}).update(v)
    return out


def stage_ta(oc, method):
    import dec054_opf as OPF
    plant = OCM.make_plant(oc)
    lim = {k: np.asarray(v) for k, v in plant.limits.items()}
    disp = {}
    for m in (method.lower(),):
        st = load(f"{m}_{oc}")
        disp[m.upper()] = None if not st or st.get("z") is None else (np.array(st["z"]), st["status"])
    out = {"oc": oc, "dispatch_status": {k: (v[1] if v else "MISSING") for k, v in disp.items()}, "cells": {}}
    for part, bus, sev in oc_events(oc):
        sc = OPF.Scenario(f"b{bus}P_{sev}", bus, "P", C.oc_amp(sev))
        rec = {}
        for m, d in disp.items():
            if d is None:
                rec[m] = {"label": "UNVERIFIED", "reason": "dispatch missing"}
                continue
            z = d[0]
            try:
                j = plant.jump(z, sc)
                if j.get("ok"):
                    plant.affine(z, sc, diag=True)
                    dg = plant.last_affine_diag
                    j.update({"gy_min_sv": dg["gy_min_sv_post_jump"], "gy_cond": dg["gy_cond_post_jump"], "inner_residual_affine": dg["inner_residual"]})
                cls = C.classify_ta(j, lim)
                cls.update({k: (np.asarray(j[k]).tolist() if k in j else None) for k in ("dP", "P_plus", "Q_plus")})
                cls.update({k: j.get(k) for k in ("residual", "gy_min_sv", "gy_cond")})
                cls["V_plus_min"] = float(np.min(j["V_plus"])) if j.get("ok") else None
                cls["V_plus_max"] = float(np.max(j["V_plus"])) if j.get("ok") else None
            except Exception as ex:
                cls = {"label": "UNVERIFIED", "reason": repr(ex)}
            rec[m] = cls
        out["cells"][f"{part}_b{bus}_{sev}"] = rec
        print(oc, part, bus, sev, {m: r["label"] for m, r in rec.items()}, flush=True)
    save(f"ta_{oc}_{method.upper()}", out)


if __name__ == "__main__":
    st = sys.argv[1]
    if st == "init":
        stage_init()
    elif st == "ta":
        stage_ta(sys.argv[2], sys.argv[3])
    else:
        {"m0": stage_m0, "m3": stage_m3, "tc": stage_tc}[st](sys.argv[2])
