"""DEC-059 TDS lots (protocol ops/sted/DEC059_protocol.md).  Stages:  plan <LOT> | run <LOT> [<LOT> ...]
  plan  writes IEEE39_DEC059_<LOT>_plan.json exclusively (sealed and committed before any TDS of the lot)
  run   requests every id in the append-only DEC-059 ledger from ONE process, then runs the TDS in worker processes; every run (also failures) is stored
        before the ledger row is completed
Reuses dec057_tds.execute unchanged (method, tol, refinement, snapshots, flag log, end state, reset_tiny); every DEC-059 run sets reset_tiny = 0 explicitly (DE).
Controller "B5P" (proposed controller B5') is injected as a qp_filter of run_b3_ieee39.run in mode B3 (src/dec059_b5.py)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

import dec054_common as C54
import dec055_common as C55
import dec057_tds as T

RUNS = C54.RUNS_DIR.parent / "DEC059_runs"
LEDGER = C55.ART / "IEEE39_DEC059_tds_ledger.csv"
BUDGET = {"R2": 12, "R3": 6, "R4": 18, "R5": 62, "K4": 4, "R6": 8, "RES": 10}
BUDGET_TOTAL = 120
DT, TE = T.DT, T.TE
ST59 = C54.RUNS_DIR.parent / "DEC059_state"
FLAT = {"bus": 8, "kind": "P", "amp": 0.0}


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
        tid = f"D59T{self.used() + 1:03d}"
        self._append({"tds_id": tid, "block": block, "scenario": scenario, "method": method, "run_id": run_id, "purpose": purpose, "status": "REQUESTED", "dt": "", "solver": solver})
        return tid


def plan_path(lot):
    return C55.ART / f"IEEE39_DEC059_{lot}_plan.json"


def _from57(lot, run_id):
    r = next(x for x in json.loads(T.plan_path(lot).read_text(encoding="utf-8"))["runs"] if x["run_id"] == run_id)
    return {k: v for k, v in r.items() if k not in ("tds_id", "purpose", "run_id")}


def plan_r2():
    proto = C54.sha_file(C55.ROOT / "ops/sted/DEC059_protocol.md")
    rt = {"reset_tiny": 0}
    runs = []
    b8 = dict(_from57("D8", "D57D8_b8_trapezoid_loc16"), **rt)
    runs.append(dict(b8, run_id="D59N1_b8_trap_loc16_rt0", purpose="R2 N1: effect of reset_tiny on the D8 transient (vs D57D8_b8_trapezoid_loc16, reset_tiny 1); prediction |dP| <= 1e-6 pu on [t_e, t_e+0.5]"))
    runs.append(dict(b8, run_id="D59N2_b8_trap_loc16_rt0_repeat", purpose="R2 N2: identical repeat of N1 (reproducibility); prediction bit-identical"))
    runs.append(dict(_from57("M3V", "D57M3V_B2_b8P_S3"), **rt, run_id="D59N3_M3V_B2_b8P_S3_rt0",
                     purpose="R2 N3: robustness of the OC3 M3 refutation under reset_tiny 0; prediction SG31 margin -0.0140 +- 1e-4 pu (UNSAFE)"))
    d7 = {oc: _from57("D7", f"D57D7_B3_flat_{oc}_M0") for oc in ("OC1", "OC2", "OC3")}
    for oc in ("OC1", "OC2", "OC3"):
        runs.append(dict(d7[oc], **rt, controller="B2", activation_s=1.0e9, tf=20.0, run_id=f"D59N_plant_flat_{oc}_M0",
                         purpose=f"R2 G1-P: plant without secondary control (RDC never activated), {oc} M0, 20 s; frozen drift criteria 0.005 Hz / 1e-3 pu"))
    for oc in ("OC1", "OC2"):
        runs.append(dict(d7[oc], **rt, run_id=f"D59N_B3_flat_{oc}_M0", purpose=f"R2 audit of the DEC-057 B3 'drift 0.0' ({oc}, R7 stable): prediction deviation <= 1e-6 pu over 200 s"))
    runs.append(dict(_from57("D7", "D57D7_B3_flat_OC3_M0_2000s"), **rt, run_id="D59N_B3_flat_OC3_M0_2000s",
                     purpose="R2 audit of the DEC-057 R7 prediction (OC3 M0 B3, +0.0198 1/s): growth at 0.0198 +- 15 % from round-off, deviation > 1e-3 pu before 2000 s or TDS failure"))
    r4 = {k: v for k, v in json.loads(T.plan_path("RES4").read_text(encoding="utf-8"))["runs"][0].items() if k not in ("tds_id", "purpose", "run_id", "snapshots")}
    runs.append(dict(r4, reset_tiny=0, time_step_s=DT / 2, tf=160.0, keep_partial=True, run_id="D59N10_OC3_M0_B2_rt0_dthalf",
                     purpose="R2 N10: step sensitivity of the OC3 B2 instability (RES4 configuration at dt/2); prediction growth rate within +-15 % of RES4, failure time within +-10 s"))
    return {"stage": "DEC-059 lot R2 plan (sealed before any TDS of the lot)", "block": "R2", "runs": runs, "protocol_sha256": proto}


def _tgt(tag):
    p = ST59 / f"target_{tag}.npz"
    if not p.exists():
        raise C54.GateError(f"missing supervisory target {p.name} (run dec059_eq.py target first)")
    js = json.loads((ST59 / f"target_{tag}.json").read_text(encoding="utf-8"))
    return str(p), C54.sha_file(p), js


def b5_run(oc, scenario, run_id, purpose, pre_tag, post_tag=None, tf=200.0, refine=True):
    z = json.loads((C55.STATE / f"m0_{oc}.json").read_text(encoding="utf-8"))["z"]
    pre, pre_sha, pre_js = _tgt(pre_tag)
    b5 = {"pre_target": pre, "pre_sha256": pre_sha, "t_e": TE, "tau_info": 1.0, "event": post_tag is not None}
    if post_tag is not None:
        post, post_sha, post_js = _tgt(post_tag)
        b5.update(post_target=post, post_sha256=post_sha, post_labels={"E4": post_js["E4"]["pass"], "T2": {k: v["pass"] for k, v in post_js["T2"].items()}})
    return {"oc": oc, "z": z, "scenario": scenario, "pflow_tol": None, "method": "trapezoid", "tol": 1e-4, "time_step_s": None, "activation_s": None, "tf": tf,
            "controller": "B5P", "reset_tiny": 0, "refine": {"k": 16, "t_on": TE, "t_off": TE + 0.5} if refine and scenario["amp"] != 0 else None, "dump_end": True,
            "b5": b5, "run_id": run_id, "purpose": purpose}


def plan_r3():
    s2 = {"bus": 8, "kind": "P", "amp": 0.58564}
    runs = [b5_run("OC1", FLAT, "D59S1_B5P_flat_OC1_M0", "R3 smoke 1 / G1-C: B5' at d = 0 (target xi(0)), OC1 M0, 200 s; frozen drift criteria; QP inactive expected", "r2_OC1_M0_d0"),
            b5_run("OC1", s2, "D59S2_B5P_OC1_M0_b8P_S2", "R3 smoke 2: B5' on DESIGN b8P_S2, OC1 M0, tau_info 1 s, local dt/16; G-R3 criteria (convergence to xi*(d+))", "r2_OC1_M0_d0", "r2_OC1_M0_b8P_0.58564"),
            b5_run("OC2", s2, "D59S3_B5P_OC2_M0_b8P_S2", "R3 smoke 3: B5' on DESIGN b8P_S2, OC2 M0; G-R3 criteria", "r2_OC2_M0_d0", "r2_OC2_M0_b8P_0.58564"),
            b5_run("OC3", s2, "D59S4_B5P_OC3_M0_b8P_S2",
                   "R3 smoke 4 (pre-declared demanding case): B5' on DESIGN b8P_S2, OC3 M0. Replaces the protocol's OC3 flat run: at an unstable target (+0.0198 1/s) a 200-s flat run "
                   "starts from round-off and cannot show the instability; the event run does. Outcome reported with the target labels (TARGET_UNSTABLE if H4/H5 fail)", "r2_OC3_M0_d0", "r2_OC3_M0_b8P_0.58564")]
    return {"stage": "DEC-059 lot R3 smoke plan (sealed before any TDS of the lot; runs 5-6 reserved for one implementation repair and its repeat)", "block": "R3", "runs": runs,
            "protocol_sha256": C54.sha_file(C55.ROOT / "ops/sted/DEC059_protocol.md"), "code_sha256": {f: C54.sha_file(C55.SRC / f) for f in ("dec059_b5.py", "dec059_eq.py", "dec059_tds.py")}}


def plan(lot, extra=None):
    p = {"R2": plan_r2, "R3": plan_r3}[lot]() if extra is None else extra
    with open(plan_path(lot), "x", encoding="utf-8") as f:
        json.dump(p, f, indent=1)
    print("plan", lot, len(p["runs"]))


def execute(r):
    """dec057_tds.execute with the DEC-059 controller B5' (qp_filter) when requested; everything else unchanged."""
    if r.get("controller") != "B5P":
        return T.execute(r)
    import dec059_b5 as B5
    import run_b3_ieee39 as b
    orig = b.run
    filt = B5.make_filter(r)

    def run_b5(mode, *a, **k):
        k["qp_filter"] = filt.spec
        return orig("B3", *a, **k)
    b.run = run_b5
    try:
        res = T.execute(dict(r, controller="B3", keep_partial=True))
    finally:
        b.run = orig
    if filt.log["t"]:                                  # the runner keeps a fixed series subset: the filter log is added here
        res["series"] = dict(res.get("series") or {}, **filt.log_arrays())
    res.setdefault("diag", {}).update(filt.summary())
    res["diag"]["controller"] = "B5P"
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


def run_many(lots, workers=6, only=None):
    L = Ledger(LEDGER)
    todo = []
    for lot in lots:
        p = json.loads(plan_path(lot).read_text(encoding="utf-8"))
        for r in p["runs"]:
            if only is None or r["run_id"] in only:
                if r.get("reset_tiny") != 0:
                    raise C54.GateError(f"{r['run_id']}: DEC-059 runs must set reset_tiny = 0 explicitly (DE)")
                h = r["time_step_s"] if r["time_step_s"] is not None else DT
                r["tds_id"] = L.request(p.get("block", lot), json.dumps(r["scenario"]), r["method"], r["run_id"], r["purpose"],
                                        solver=f"{r['method']} h={h:.6g} tol={r['tol']:g} reset_tiny=0 ctrl={r.get('controller', 'B2')} refine={r.get('refine')}")
                todo.append(r)
    todo.sort(key=lambda r: -r["tf"] / (r["time_step_s"] or DT))
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONWARNINGS="ignore")

    def go(r):
        out = subprocess.run([sys.executable, "-c", f"import dec059_tds as M; M._child({json.dumps(json.dumps(r))})"], capture_output=True, text=True, cwd=str(C55.SRC), env=env)
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
        run_many(sys.argv[2:], int(os.environ.get("DEC059_WORKERS", "6")))
