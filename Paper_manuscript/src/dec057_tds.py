"""DEC-057 TDS lots (D8 local refinement, D7 centered RDC B3, INS OC3 instability, M3V OC3 M3 in-sample validation).  Stages:  plan <LOT> | run <LOT>
  plan  writes IEEE39_DEC057_<LOT>_plan.json exclusively (sealed before any TDS of the lot)
  run   requests every id in the append-only DEC-057 ledger, runs the TDS in parallel worker processes, stores every run (also failures) before completing the ledger
Wraps dec055_runner.execute_tds_oc without editing it (protocol ops/sted/DEC057_protocol.md, implementation notes):
  * method / Newton tol / horizon / RDC activation time as in dec056_tds;
  * controller: run_b3_ieee39.run is called with mode "B3" (ref None: offset = v_RDC at the pre-event equilibrium, DEC-039) instead of "B2";
  * local refinement: a wrapper of TDS.callpert shortens the pending step to dt/k on [t_on - dt, t_off] and keeps ctx["h"] (step of the RDC update) equal to it;
  * read-only diagnostics: state snapshots, discrete-limiter flag-change log, end state, storage thinning (save_every / log_every)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

import dec054_common as C54
import dec055_common as C55

RUNS = C54.RUNS_DIR.parent / "DEC057_runs"
LEDGER = C55.ART / "IEEE39_DEC057_tds_ledger.csv"
BUDGET = {"D8": 22, "D7": 6, "INS": 2, "M3V": 26, "RES": 4}
BUDGET_TOTAL = 60
DT = C54.DT
TE = C55.EVENT_T
ST57 = C54.RUNS_DIR.parent / "DEC057_state"


class Ledger(C55.Ledger):
    def request(self, block, scenario, method, run_id, purpose, solver="trapezoid dt=2^-8"):
        if block not in BUDGET:
            raise C54.GateError(f"unknown lot {block}")
        if not purpose.strip() or not run_id.strip():
            raise C54.GateError("a TDS needs a run_id and a justification before launch")
        if any(r["run_id"] == run_id and r["status"] == "REQUESTED" for r in self.rows):
            raise C54.GateError(f"run_id {run_id} already requested (no silent retries)")
        if self.used() >= BUDGET_TOTAL or self.used(block) >= BUDGET[block]:
            raise C54.GateError(f"budget exhausted ({block})")
        tid = f"D57T{self.used() + 1:03d}"
        self._append({"tds_id": tid, "block": block, "scenario": scenario, "method": method, "run_id": run_id, "purpose": purpose, "status": "REQUESTED", "dt": "", "solver": solver})
        return tid


def plan_path(lot):
    return C55.ART / f"IEEE39_DEC057_{lot}_plan.json"


def _ref(run):
    c = json.loads((C54.RUNS_DIR / run / "config.json").read_text(encoding="utf-8"))
    t = c.get("test") or {"z": c["z"], **c["scenario"]}
    return {"z": t["z"], "scenario": {"bus": int(t["bus"]), "kind": t["kind"], "amp": float(t["amp"])}}


def plan_d8():
    base = {"oc": "OC1", "pflow_tol": 1e-6, "tf": 20.0, "activation_s": None, "tol": 1e-4, "time_step_s": DT, "controller": "B2"}
    runs = []
    r = _ref("P3B2_b7P_M3")
    for meth in ("trapezoid", "backeuler"):
        runs.append(dict(base, **r, run_id=f"D57D8_b7_{meth}_loc16", method=meth, refine={"k": 16, "t_on": TE, "t_off": TE + 0.5},
                         purpose=f"D8 rule D8-1: local {meth} dt/16 on [t_e-dt, t_e+0.5] vs the uniform DEC-056 dt/16 run (reference case P3B2_b7P_M3)"))
    for case, tag in (("P3B2_b8P_M3", "b8"), ("P3-C_bus12P_M3", "bus12")):
        r = _ref(case)
        for meth in ("trapezoid", "backeuler"):
            for k in (1, 2, 4, 8, 16):
                runs.append(dict(base, **r, run_id=f"D57D8_{tag}_{meth}_loc{k}", method=meth, refine=None if k == 1 else {"k": k, "t_on": TE, "t_off": TE + 0.5},
                                 purpose=f"D8 convergence {case}: {meth}, " + ("uniform dt" + (" (regression vs the stored run)" if meth == "trapezoid" else "") if k == 1 else f"local dt/{k} on [t_e-dt, t_e+0.5]")))
    return {"stage": "DEC-057 lot D8 plan (sealed before any TDS of the lot)", "block": "D8", "runs": runs, "protocol_sha256": C54.sha_file(C55.ROOT / "ops/sted/DEC057_protocol.md")}


def plan_d7():
    m0 = {oc: json.loads((C55.STATE / f"m0_{oc}.json").read_text(encoding="utf-8"))["z"] for oc in ("OC1", "OC2", "OC3")}
    flat = {"bus": 8, "kind": "P", "amp": 0.0}
    base = {"scenario": flat, "pflow_tol": None, "method": "trapezoid", "tol": 1e-4, "time_step_s": None, "controller": "B3", "activation_s": None, "tf": 200.0}
    runs = [dict(base, run_id=f"D57D7_B3_flat_{oc}_M0", oc=oc, z=m0[oc], purpose=f"D7 B3 flat run at {oc} M0 with the G1 settings (frozen 20-s drift criterion)") for oc in ("OC1", "OC2", "OC3")]
    runs.append(dict(base, run_id="D57D7_B3_flat_OC3_M0_2000s", oc="OC3", z=m0["OC3"], tf=2000.0, save_every=16, log_every=16,
                     purpose="D7 R7 test: stability of the B3 equilibrium in OC3 (linearised +0.0198 1/s); predicted deviation > 1e-3 pu before 2000 s if the eigenvalue is real"))
    r = _ref("P3B2_b7P_M3")
    for h, tag in ((DT, "dt"), (DT / 2, "dthalf")):
        runs.append(dict(base, **r, oc="OC1", pflow_tol=1e-6, time_step_s=h, run_id=f"D57D7_B3_P3B2_b7P_M3_{tag}",
                         purpose=f"D7 B3 on the reference event (comparison with the stored B2 run) at {tag}: AC-04 step check of G1"))
    return {"stage": "DEC-057 lot D7 plan (sealed before any TDS of the lot)", "block": "D7", "runs": runs, "protocol_sha256": C54.sha_file(C55.ROOT / "ops/sted/DEC057_protocol.md")}


def plan_ins():
    p = json.loads((C55.ART / "IEEE39_DEC056_D7a_plan.json").read_text(encoding="utf-8"))
    r = {k: v for k, v in next(x for x in p["runs"] if x["run_id"] == "D56D7_presettle_OC3_M0").items() if k not in ("tds_id", "purpose", "run_id")}
    snaps = [200.0, 250.0, 280.0, 290.0] + [float(s) for s in range(295, 326)] + [330.0]
    runs = [dict(r, controller="B2", tf=330.0, snapshots=snaps, flags_log=True, run_id="D57INS_OC3_M0_B2_presettle_snap",
                 purpose="INS (i): D56T012 configuration to 330 s with full-state snapshots and the discrete-limiter flag-change log (regression: bit-identical to D56T014)"),
            dict(r, controller="B2", tf=345.0, time_step_s=DT / 2, flags_log=True, keep_partial=True, run_id="D57INS_OC3_M0_B2_presettle_dthalf",
                 purpose="INS (ii): same at dt/2 (H9c numerical-origin test: onset within +-5 s and growth rate within +-15 %)")]
    return {"stage": "DEC-057 lot INS plan (sealed before any TDS of the lot)", "block": "INS", "runs": runs, "protocol_sha256": C54.sha_file(C55.ROOT / "ops/sted/DEC057_protocol.md")}


def plan_m3v():
    import dec055_l0 as L0
    s = json.loads((ST57.parent / "DEC056_state" / "oc3_seeded_full.json").read_text(encoding="utf-8"))
    z = s["z"]
    base = {"oc": "OC3", "z": z, "pflow_tol": None, "method": "trapezoid", "tol": 1e-4, "time_step_s": None, "activation_s": None, "tf": 200.0, "dump_end": True}
    runs = []
    for ctrl in ("B2", "B3"):
        for sc in L0.design_scenarios():
            runs.append(dict(base, controller=ctrl, scenario={"bus": sc.bus, "kind": sc.kind, "amp": sc.amp}, refine={"k": 16, "t_on": TE, "t_off": TE + 0.5},
                             run_id=f"D57M3V_{ctrl}_{sc.name}", purpose=f"M3V in-sample DESIGN cell {sc.name}, OC3 M3 (DEC-056 seeded), {ctrl}, local trapezoid dt/16"))
        runs.append(dict(base, controller=ctrl, scenario={"bus": 8, "kind": "P", "amp": 0.0}, run_id=f"D57M3V_{ctrl}_flat", purpose=f"M3V flat run at the OC3 M3 dispatch, {ctrl}"))
    return {"stage": "DEC-057 lot M3V plan (sealed before any TDS of the lot)", "block": "M3V", "runs": runs, "z_source": "DEC056_state/oc3_seeded_full.json",
            "z_source_sha256": C54.sha_file(ST57.parent / "DEC056_state" / "oc3_seeded_full.json"), "protocol_sha256": C54.sha_file(C55.ROOT / "ops/sted/DEC057_protocol.md")}


def plan_res1():
    """Smoke test of every wrapper feature on a 0.6-s horizon (reference case, local refinement, B3, snapshots, flag log, end state, thinning)."""
    r = _ref("P3B2_b7P_M3")
    run = dict(r, oc="OC1", pflow_tol=1e-6, tf=5.6, activation_s=None, tol=1e-4, time_step_s=DT, method="trapezoid", controller="B3", refine={"k": 16, "t_on": TE, "t_off": TE + 0.5},
               snapshots=[4.0, 5.0, 5.25, 5.55], flags_log=True, dump_end=True, log_every=1, save_every=1, run_id="D57RES_smoke_features",
               purpose="RESERVE (logged justification): smoke test of the DEC-057 wrapper (local refinement, B3, snapshots, flag log, end state) before the lots, so that a code defect does not consume lot runs")
    return {"stage": "DEC-057 reserve plan 1 (sealed before its TDS)", "block": "RES", "runs": [run], "justification": run["purpose"]}


def plan_res2():
    r = dict(plan_res1()["runs"][0], run_id="D57RES_smoke_features_2")
    r["purpose"] = ("RESERVE (logged justification): D57T001 failed in the wrapper (dae.t assigned a Python float; ANDES needs the ndarray, dae.store calls t.tolist()); "
                    "code fixed (in-place update of dae.t), identical smoke test repeated")
    return {"stage": "DEC-057 reserve plan 2 (sealed before its TDS)", "block": "RES", "runs": [r], "justification": r["purpose"]}


def plan_res3():
    r = {k: v for k, v in json.loads(plan_path("INS").read_text(encoding="utf-8"))["runs"][0].items() if k not in ("tds_id",)}
    r.update(run_id="D57RES_INS_OC3_honest_tol1e-8", honest=True, tol=1e-8, tf=330.0, keep_partial=True,
             snapshots=[float(s) for s in range(10, 200, 10)] + [200.0, 250.0, 300.0],
             purpose=("RESERVE (logged justification, H9c discrimination): the frozen-time linearisation of plant + B2 along the INS run is validated by an "
                      "independent FD Jacobian (1e-7) and has a 1.30 Hz pair at +0.58 1/s from t = 200 s, but the default TDS (lazy chord-Newton Jacobian, "
                      "convergence on |increment| <= 1e-4) shows no growth until ~312 s (dt) / ~334 s (dt/2). Same configuration with the Jacobian refreshed at "
                      "every iteration and tol 1e-8. PREDICTION if the late onset is a solver artifact: growth of the 1.25-1.3 Hz component starts at the time "
                      "the frozen-time pair crosses Re = 0 (from this run's own snapshots), well before 300 s; otherwise onset within +-5 s of the default run"))
    return {"stage": "DEC-057 reserve plan 3 (sealed before its TDS)", "block": "RES", "runs": [r], "justification": r["purpose"]}


def plan_res4():
    r = {k: v for k, v in json.loads(plan_path("INS").read_text(encoding="utf-8"))["runs"][0].items() if k not in ("tds_id",)}
    r.update(run_id="D57RES_INS_OC3_reset_tiny0", reset_tiny=0, tf=330.0, keep_partial=True, snapshots=[float(s) for s in range(10, 330, 10)],
             purpose=("RESERVE (logged justification, H9e discrimination, last reserve run): RES3 (honest Jacobian, tol 1e-8) left the onset at ~315-320 s, so the "
                      "lazy Jacobian and the Newton tolerance are not the cause. ANDES zeroes Newton increments below tol_zero = 1e-10 (reset_tiny = 1, default); "
                      "a 1.3 Hz mode of amplitude ~1e-8 has per-step increments ~0.03 x amplitude, below that threshold. Same configuration as INS (i) with "
                      "reset_tiny = 0 as the only change. PREDICTION if the dead zone masks the instability: growth of the 1.25-1.3 Hz component starts close to "
                      "the frozen-time crossing (about 60-80 s, RES3 snapshots) at a rate consistent with the frozen-time real part, i.e. far earlier than 300 s; "
                      "if the onset stays at ~315 s (+-10 s) the hypothesis is refuted"))
    return {"stage": "DEC-057 reserve plan 4 (sealed before its TDS)", "block": "RES", "runs": [r], "justification": r["purpose"]}


def plan(lot, extra=None):
    p = {"D8": plan_d8, "D7": plan_d7, "INS": plan_ins, "M3V": plan_m3v, "RES1": plan_res1, "RES2": plan_res2, "RES3": plan_res3, "RES4": plan_res4}[lot]() if extra is None else extra
    with open(plan_path(lot), "x", encoding="utf-8") as f:
        json.dump(p, f, indent=1)
    print("plan", lot, len(p["runs"]))


def flag_vector(system):
    """Concatenated zu / zl / zi of every discrete block (read only) and the matching names."""
    vals, names = [], []
    for mn, m in system.models.items():
        if m.n == 0:
            continue
        for dn, d in m.discrete.items():
            for a in ("zu", "zl", "zi"):
                v = getattr(d, a, None)
                if v is None:
                    continue
                v = np.asarray(v, float).ravel()
                vals.append(v)
                names += [f"{mn}.{dn}.{a}[{i}]" for i in range(v.size)]
    return (np.concatenate(vals) if vals else np.zeros(0)), names


def execute(r):
    """One TDS with the per-run settings (child process)."""
    import dec055_oc as OCM
    import dec055_runner as R
    import run_b3_ieee39 as b
    import run_e8_ieee39 as e8
    OCM.select(r["oc"])
    saved = (e8.FINAL_TIME_S, b.EVENT_TIME_S, e8.configure, b.run)
    extra = {}
    keep = {}
    orig_run = b.run
    dt0 = float(r["time_step_s"] if r["time_step_s"] is not None else DT)

    def run_wrapped(mode, *a, **k):
        if r.get("log_every"):
            k["log_every"] = int(r["log_every"])
        system, d, diag = orig_run(r.get("controller", "B2"), *a, **k)
        if r.get("keep_partial") and not diag.get("tds_ok"):
            keep.update({"t": d["time_s"], "P": np.hstack([d["sg_p_pu"], d["gfm_p_pu"]]), "Q": np.hstack([d["sg_q_pu"], d["gfm_q_pu"]]), "V": d["bus_voltage_pu"],
                         "f_bus_hz": d["bus_frequency_hz"], "cmd_t": d.get("cmd_t"), "cmd_qset": d.get("cmd_qset"), "cmd_pset": d.get("cmd_pset"), "cmd_gq": d.get("cmd_gq"), "cmd_z": d.get("cmd_z")})
        if r.get("dump_end"):
            fv, fn = flag_vector(system)
            extra.update({"end_t": float(system.dae.t), "end_x": np.array(system.dae.x), "end_y": np.array(system.dae.y), "end_flags": fv, "flag_names": np.array(fn),
                          "end_pset": d["cmd_pset"][-1], "end_qset": d["cmd_qset"][-1], "end_cmd_t": d["cmd_t"][-1],
                          **{f"end_PQ_{n}": np.array(getattr(system.PQ, n).v) for n in ("p0", "q0", "Ppf", "Qpf")}})
        return system, d, diag
    b.run = run_wrapped
    inner = e8.configure

    def configure(scenario, time_step_s, _inner=inner):
        system, ctx = _inner(scenario, time_step_s)
        system.TDS.config.method = r["method"]
        system.TDS.config.tol = float(r["tol"])
        if r.get("save_every"):
            system.TDS.config.save_every = int(r["save_every"])
        if r.get("honest"):
            system.TDS.config.honest = 1                # Newton Jacobian refreshed at every iteration (ANDES default: lazy, chord iterations)
        if r.get("reset_tiny") is not None:
            system.TDS.config.reset_tiny = int(r["reset_tiny"])     # ANDES default 1: Newton increments below tol/1e6 (= 1e-10) are set to zero
        tds = system.TDS
        run0 = tds.run
        ref = r.get("refine")
        snaps = sorted(r.get("snapshots") or [])
        state = {"phase": "coarse", "snap_i": 0, "flags_prev": None}
        snap = {"t": [], "x": [], "y": [], "flags": []}
        flog = {"t": [], "i": [], "v": []}

        def run_patched(*a, **k):
            cb = tds.callpert

            def cb2(t, sys_):
                dae = sys_.dae
                t_prev = float(dae.t - tds.h)
                if ref is not None:
                    hf = dt0 / int(ref["k"])
                    if state["phase"] == "coarse" and dae.t >= ref["t_on"] - 1e-12:
                        new = hf
                        state["phase"] = "fine"
                    elif state["phase"] == "fine" and t_prev >= ref["t_off"] - 1e-12:
                        new = dt0
                        state["phase"] = "done"
                    else:
                        new = None
                    if new is not None:
                        dae.t -= tds.h                  # in place: dae.t stays an ndarray (ANDES calls dae.t.tolist()); exact for dyadic steps
                        dae.t += new
                        tds.h = new
                        tds.deltat = new
                        tds.config.tstep = new
                        ctx["h"] = new
                if snaps or r.get("flags_log"):
                    fv, fn = flag_vector(sys_)
                    if r.get("flags_log"):
                        if state["flags_prev"] is None:
                            extra["flag_names"] = np.array(fn)
                            extra["flags_initial"] = fv.copy()
                        else:
                            ch = np.where(fv != state["flags_prev"])[0]
                            for i in ch:
                                flog["t"].append(t_prev)
                                flog["i"].append(int(i))
                                flog["v"].append(float(fv[i]))
                        state["flags_prev"] = fv
                    while state["snap_i"] < len(snaps) and t_prev >= snaps[state["snap_i"]] - 1e-12:
                        snap["t"].append(t_prev)
                        snap["x"].append(np.array(dae.x))
                        snap["y"].append(np.array(dae.y))
                        snap["flags"].append(fv.copy())
                        extra["flag_names"] = np.array(fn)
                        state["snap_i"] += 1
                return cb(dae.t, sys_)
            tds.callpert = cb2
            try:
                return run0(*a, **k)
            finally:
                if snap["t"]:
                    extra.update({f"snap_{k_}": np.array(v) for k_, v in snap.items()})
                if r.get("flags_log"):
                    extra.update({"flaglog_t": np.array(flog["t"]), "flaglog_i": np.array(flog["i"], int), "flaglog_v": np.array(flog["v"])})
        tds.run = run_patched
        return system, ctx
    try:
        e8.FINAL_TIME_S = float(r["tf"])
        if r.get("activation_s") is not None:
            b.EVENT_TIME_S = float(r["activation_s"])
        e8.configure = configure
        OCM.select = lambda oc: None            # keep the wrapped configure (execute_tds_oc calls select again)
        res = R.execute_tds_oc(r["oc"], np.asarray(r["z"], float), r["scenario"], r["time_step_s"], pflow_tol=r["pflow_tol"])
    finally:
        e8.FINAL_TIME_S, b.EVENT_TIME_S, e8.configure, b.run = saved
    if keep and res.get("series") is None:
        res["series"] = {k: v for k, v in keep.items() if v is not None}
        res["notes"] = "PARTIAL series up to the numerical failure; " + str(res.get("notes", ""))
    if res.get("series") is not None:
        res["series"].update({k: v for k, v in extra.items() if v is not None})
    elif extra:
        res["series"] = {k: v for k, v in extra.items() if v is not None}
    res.setdefault("diag", {}).update({"method": r["method"], "tds_tol": r["tol"], "tf": r["tf"], "activation_s": r.get("activation_s"), "controller": r.get("controller", "B2"),
                                       "refine": r.get("refine"), "save_every": r.get("save_every"), "log_every": r.get("log_every")})
    return res


def _child(run_json):
    import dec054_store as ST
    r = json.loads(run_json)
    res, err = None, None
    try:
        res = execute(r)
        status = res["status"]
    except Exception as ex:
        status, err = "TDS_NUMERICAL_FAILURE", ex
    res = res or {}
    ST.save_run(RUNS, r["run_id"], status=status, tds_id=r["tds_id"], series=res.get("series"), metrics=res.get("metrics"), config=r, diag=res.get("diag"),
                notes=str(res.get("notes", "")), error=err, ledger_row={"tds_id": r["tds_id"]})
    print(json.dumps({"run_id": r["run_id"], "status": status}))


def run(lot, workers=6, only=None):
    run_many([lot], workers, only)


def run_many(lots, workers=6, only=None):
    """All ledger ids of the given lots are requested by ONE process before any TDS (the ledger counts ids from its own rows), then one worker pool;
    the longest runs (by tf / h) are started first."""
    L = Ledger(LEDGER)
    todo = []
    for lot in lots:
        p = json.loads(plan_path(lot).read_text(encoding="utf-8"))
        for r in p["runs"]:
            if only is None or r["run_id"] in only:
                h = r["time_step_s"] if r["time_step_s"] is not None else DT
                r["tds_id"] = L.request(p.get("block", lot), json.dumps(r["scenario"]), r["method"], r["run_id"], r["purpose"],
                                        solver=f"{r['method']} h={h:.6g} tol={r['tol']:g} ctrl={r.get('controller', 'B2')} refine={r.get('refine')}")
                todo.append(r)
    todo.sort(key=lambda r: -r["tf"] / (r["time_step_s"] or DT))
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONWARNINGS="ignore")

    def go(r):
        out = subprocess.run([sys.executable, "-c", f"import dec057_tds as M; M._child({json.dumps(json.dumps(r))})"], capture_output=True, text=True, cwd=str(C55.SRC), env=env)
        line = [x for x in out.stdout.splitlines() if x.startswith("{")]
        return r, (json.loads(line[-1])["status"] if line else "TDS_NUMERICAL_FAILURE"), out.stderr[-1500:]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for r, status, errtxt in ex.map(go, todo):
            L.complete(r["tds_id"], status if status in C54.TDS_STATUS else "TDS_NUMERICAL_FAILURE", "" if status in C54.TDS_STATUS else errtxt[-300:])
            print(r["run_id"], status, flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "plan":
        plan(sys.argv[2])
    else:
        run_many(sys.argv[2:], int(os.environ.get("DEC057_WORKERS", "6")))
