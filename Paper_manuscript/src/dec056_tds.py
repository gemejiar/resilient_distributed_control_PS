"""DEC-056 diagnostic TDS lots (D8 numerical convergence, D7 closed-loop settling).  Stages:  plan <LOT> | run <LOT>
  plan  writes IEEE39_DEC056_<LOT>_plan.json exclusively (sealed before any TDS of the lot)
  run   requests every id in the append-only DEC-056 ledger, runs the TDS in parallel worker processes, stores every run (also failures) before completing the ledger
Wraps dec055_runner.execute_tds_oc without editing it: the integrator (TDS.config.method), the TDS Newton tolerance (TDS.config.tol), the horizon
(run_e8_ieee39.FINAL_TIME_S) and the RDC activation time (run_b3_ieee39.EVENT_TIME_S) are set per run and restored afterwards; the load event of
dec054_runner.execute_tds stays at t = 5 s."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

import dec054_common as C54
import dec055_common as C55

RUNS = C54.RUNS_DIR.parent / "DEC056_runs"
LEDGER = C55.ART / "IEEE39_DEC056_tds_ledger.csv"
BUDGET = {"D8": 10, "D7": 6, "RES": 2}
BUDGET_TOTAL = 18
DT = C54.DT
REF = "P3B2_b7P_M3"


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
        tid = f"D56T{self.used() + 1:03d}"
        self._append({"tds_id": tid, "block": block, "scenario": scenario, "method": method, "run_id": run_id, "purpose": purpose, "status": "REQUESTED", "dt": "", "solver": solver})
        return tid


def plan_path(lot):
    return C55.ART / f"IEEE39_DEC056_{lot}_plan.json"


def plan_d8():
    ref = json.loads((C54.RUNS_DIR / REF / "config.json").read_text(encoding="utf-8"))["test"]
    sc = {"bus": ref["bus"], "kind": ref["kind"], "amp": ref["amp"]}
    base = {"oc": "OC1", "z": ref["z"], "scenario": sc, "pflow_tol": 1e-6, "tf": 20.0, "activation_s": None}
    runs = [dict(base, run_id="D56D8_trapezoid_dt1_regress", method="trapezoid", tol=1e-4, time_step_s=DT,
                 purpose="wrapper regression: must reproduce the first 20 s of the stored run bit for bit")]
    for meth, divs in (("trapezoid", (4, 8, 16)), ("backeuler", (1, 2, 4, 8, 16))):
        for d in divs:
            runs.append(dict(base, run_id=f"D56D8_{meth}_dt{d}", method=meth, tol=1e-4, time_step_s=DT / d, purpose=f"D8 convergence: {meth}, h = dt/{d}"))
    runs.append(dict(base, run_id="D56D8_trapezoid_dt1_tol1e-8", method="trapezoid", tol=1e-8, time_step_s=DT, purpose="D8 Newton-tolerance sensitivity at the protocol step"))
    return {"stage": "DEC-056 lot D8 plan (sealed before any TDS of the lot)", "reference_run": REF, "reuse": ["D55L1_regress_P3B2_b7P_M3 (trapezoid dt)", "D55L1_dthalf_P3B2_b7P_M3 (trapezoid dt/2)"],
            "runs": runs, "protocol_sha256": C54.sha_file(C55.ROOT / "ops/sted/DEC056_protocol.md")}


def plan_d7a():
    """Closed-loop settling and self-consistent dispatch checks (no event: amplitude 0 at bus 8, as the L1 flat runs; protocol solver settings)."""
    m0 = {oc: json.loads((C55.STATE / f"m0_{oc}.json").read_text(encoding="utf-8"))["z"] for oc in ("OC1", "OC3")}
    sc2 = json.loads((RUNS.parent / "DEC056_state" / "d7_selfc2_OC2_M0_v0.json").read_text(encoding="utf-8"))
    flat = {"bus": 8, "kind": "P", "amp": 0.0}
    base = {"scenario": flat, "pflow_tol": None, "method": "trapezoid", "tol": 1e-4, "time_step_s": None}
    runs = [dict(base, run_id=f"D56D7_presettle_{oc}_M0", oc=oc, z=m0[oc], tf=600.0, activation_s=0.0,
                 purpose=f"D7 settling of B2 activated at t = 0 at the {oc} M0 dispatch (no event): time to 20-s drift <= 1e-3 / 1e-4 pu; start point for xi*(z)")
            for oc in ("OC1", "OC3")]
    runs.append(dict(base, run_id="D56D7_flat_OC2_SCv0", oc="OC2", z=sc2["z"], tf=200.0, activation_s=None,
                     purpose="D7 flat run (G1 settings) at the OC2 self-consistent dispatch (v0 free, max|v_Q| 7.2e-4 at activation): frozen G1 drift criterion test"))
    return {"stage": "DEC-056 lot D7 plan A (sealed before any TDS of the plan)", "block": "D7", "runs": runs,
            "selfc2_OC2_sha256": C54.sha_file(RUNS.parent / "DEC056_state" / "d7_selfc2_OC2_M0_v0.json"), "protocol_sha256": C54.sha_file(C55.ROOT / "ops/sted/DEC056_protocol.md")}


def plan(lot, extra=None):
    p = {"D8": plan_d8, "D7a": plan_d7a}[lot]() if extra is None else extra
    with open(plan_path(lot), "x", encoding="utf-8") as f:
        json.dump(p, f, indent=1)
    print("plan", lot, len(p["runs"]))


def execute(r):
    """One TDS with the per-run solver settings (child process)."""
    import dec055_oc as OCM
    import dec055_runner as R
    import run_b3_ieee39 as b
    import run_e8_ieee39 as e8
    OCM.select(r["oc"])
    saved = (e8.FINAL_TIME_S, b.EVENT_TIME_S, e8.configure)
    inner = e8.configure

    def configure(scenario, time_step_s, _inner=inner):
        system, ctx = _inner(scenario, time_step_s)
        system.TDS.config.method = r["method"]
        system.TDS.config.tol = float(r["tol"])
        return system, ctx
    try:
        e8.FINAL_TIME_S = float(r["tf"])
        if r.get("activation_s") is not None:
            b.EVENT_TIME_S = float(r["activation_s"])
        e8.configure = configure
        OCM.select = lambda oc: None            # keep the wrapped configure (execute_tds_oc calls select again)
        res = R.execute_tds_oc(r["oc"], np.asarray(r["z"], float), r["scenario"], r["time_step_s"], pflow_tol=r["pflow_tol"])
    finally:
        e8.FINAL_TIME_S, b.EVENT_TIME_S, e8.configure = saved
    res.setdefault("diag", {}).update({"method": r["method"], "tds_tol": r["tol"], "tf": r["tf"], "activation_s": r.get("activation_s")})
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


def run(lot, workers=6):
    p = json.loads(plan_path(lot).read_text(encoding="utf-8"))
    L = Ledger(LEDGER)
    for r in p["runs"]:
        h = r["time_step_s"] if r["time_step_s"] is not None else DT
        r["tds_id"] = L.request(p.get("block", lot), json.dumps(r["scenario"]), r["method"], r["run_id"], r["purpose"], solver=f"{r['method']} h={h:.6g} tol={r['tol']:g}")
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONWARNINGS="ignore")

    def go(r):
        out = subprocess.run([sys.executable, "-c", f"import dec056_tds as M; M._child({json.dumps(json.dumps(r))})"], capture_output=True, text=True, cwd=str(C55.SRC), env=env)
        line = [x for x in out.stdout.splitlines() if x.startswith("{")]
        return r, (json.loads(line[-1])["status"] if line else "TDS_NUMERICAL_FAILURE"), out.stderr[-1500:]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for r, status, errtxt in ex.map(go, p["runs"]):
            L.complete(r["tds_id"], status if status in C54.TDS_STATUS else "TDS_NUMERICAL_FAILURE", "" if status in C54.TDS_STATUS else errtxt[-300:])
            print(r["run_id"], status, flush=True)


if __name__ == "__main__":
    {"plan": plan, "run": run}[sys.argv[1]](sys.argv[2])
