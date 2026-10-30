"""DEC-066 ablation TDS (new ledger IEEE39_DEC066_tds_ledger.csv, new run directory backups/DEC066_runs, new state files backups/DEC066_state/target_*).  Frozen executor reused unchanged:
dec059_tds.execute (controller B5', local dt/16, tol 1e-4, trapezoid, reset_tiny 0) and dec059_tds.b5_run (run dictionary); only the dispatch z (designs A..E of
dec066_abl_analysis.SRC), the equilibrium-target tags, the ledger, the run directory and the plan path are DEC-066.
  target <V> <bus> <SEV|d0>          compute and save the supervisory targets (pre-event d0, or post-event for bus/severity) for design V (exclusive writes)
  plan <LOT> <spec>                  spec = "8:S3:A,B,C,D,E;21:S3:A,B,D,E;..." ; writes artifacts/IEEE39_DEC066_<LOT>_plan.json exclusively (sealed with the predictions before the run)
  run <LOT>                          requests every id in the DEC-066 ledger and runs the TDS (workers = DEC066_WORKERS, default 5)
Budget: 40 TDS in total (E1 <= 20, E2 <= 4, E3 <= 12, E4 <= 4)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

import dec054_common as C54
import dec055_common as C55
import dec059_eq as EQ
import dec059_tds as T
import dec066_abl_analysis as AA

STATE = C54.RUNS_DIR.parent / "DEC066_state"
RUNS = C54.RUNS_DIR.parent / "DEC066_runs"
LEDGER = C55.ART / "IEEE39_DEC066_tds_ledger.csv"
BUDGET = {"E1": 20, "E2": 4, "E3": 12, "E4": 4}
BUDGET_TOTAL = 40
OC = "OC1"
NAME = {"A": "M3", "B": "M3+dense", "C": "M3+dense+eps_OS", "D": "M3+OS", "E": "M3+U_D8 only"}


def amp(sev):
    return round(C55.oc_amp(sev), 5)


def z_of(v):
    return np.array(json.loads(AA.SRC[v].read_text(encoding="utf-8"))["z"])


def tag(v, bus=None, sev=None):
    return f"abl{v}_{OC}_d0" if bus is None else f"abl{v}_{OC}_b{bus}P_{amp(sev):.5f}"


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
        tid = f"D66T{self.used() + 1:03d}"
        self._append({"tds_id": tid, "block": block, "scenario": scenario, "method": method, "run_id": run_id, "purpose": purpose, "status": "REQUESTED", "dt": "", "solver": solver})
        return tid


def target(v, bus, sev):
    EQ.STATE = STATE
    z = z_of(v)
    sc = None if sev == "d0" else {"bus": int(bus), "kind": "P", "amp": amp(sev)}
    E = EQ.Eq(OC, z)
    Tg = E.target(sc)
    p = EQ.save_target(tag(v) if sev == "d0" else tag(v, bus, sev), Tg)
    print(p.name, {"E4": Tg["E4"]["pass"], "T2": {k: x["pass"] for k, x in Tg["T2"].items()}, "root": Tg["root_residual"]}, flush=True)


def build(v, bus, sev, lot, div=1):
    T.ST59 = STATE
    sc = {"bus": int(bus), "kind": "P", "amp": amp(sev)}
    rid = f"D66{lot}_B5P_{OC}_{v}_b{bus}P_{sev}"
    r = T.b5_run(OC, sc, rid, f"DEC-066 {lot}: B5' on b{bus}P_{sev} at design {v} ({NAME[v]}), OC1, local dt/16, frozen controller parameters", tag(v), tag(v, bus, sev), m="M0")
    r["z"] = z_of(v).tolist()
    r["dispatch_label"] = v
    if div != 1:                                  # E2: step sensitivity (dt/div; the local refinement k = 16 is kept, so the finest step is dt/(16 div))
        r["time_step_s"] = C54.DT / div
        r["run_id"] += f"_dt{div}"
        r["purpose"] += f"; time step dt/{div}"
    return r


def plan(lot, spec, preds=None):
    runs = []
    for item in spec.split(";"):
        b, s, vs = item.split(":")
        for v in vs.split(","):
            div = 1
            if "/" in v:
                v, div = v.split("/")
            runs.append(build(v, b, s, lot, int(div)))
    p = {"stage": f"DEC-066 ablation lot {lot} (sealed with the predictions before any TDS of the lot)", "block": lot, "runs": runs, "predictions": preds,
         "designs_sha256": {v: C54.sha_file(AA.SRC[v]) for v in "ABCDE"},
         "code_sha256": {f: C54.sha_file(C55.SRC / f) for f in ("dec059_b5.py", "dec059_tds.py", "dec059_eq.py", "dec066_tds.py", "dec066_abl_analysis.py")},
         "backup": "DEC-066 procedural exception: investigator waived the independent backup (same-disk copy only); see ops/sted/DEC066_protocol.md Addendum C"}
    with open(C55.ART / f"IEEE39_DEC066_{lot}_plan.json", "x", encoding="utf-8") as f:
        json.dump(p, f, indent=1)
    print("plan", lot, len(runs))


def _child(run_json):
    import dec054_store as ST
    r = json.loads(run_json)
    res, err = None, None
    try:
        res = T.execute(r)
        status = res["status"]
    except Exception as ex:
        status, err = "TDS_NUMERICAL_FAILURE", ex
    res = res or {}
    ST.save_run(RUNS, r["run_id"], status=status, tds_id=r["tds_id"], series=res.get("series"), metrics=res.get("metrics"), config=r, diag=res.get("diag"),
                notes=str(res.get("notes", "")), error=err, ledger_row={"tds_id": r["tds_id"]})
    print(json.dumps({"run_id": r["run_id"], "status": status}))


def run_many(lot, workers=5):
    L = Ledger(LEDGER)
    p = json.loads((C55.ART / f"IEEE39_DEC066_{lot}_plan.json").read_text(encoding="utf-8"))
    todo = []
    for r in p["runs"]:
        if r.get("reset_tiny") != 0:
            raise C54.GateError(f"{r['run_id']}: reset_tiny must be 0")
        r["tds_id"] = L.request(lot[:2], json.dumps(r["scenario"]), r["method"], r["run_id"], r["purpose"], solver=f"{r['method']} tol={r['tol']:g} reset_tiny=0 ctrl=B5P refine={r.get('refine')}")
        todo.append(r)
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONWARNINGS="ignore")

    def go(r):
        out = subprocess.run([sys.executable, "-c", f"import dec066_tds as M; M._child({json.dumps(json.dumps(r))})"], capture_output=True, text=True, cwd=str(C55.SRC), env=env)
        line = [x for x in out.stdout.splitlines() if x.startswith("{")]
        return r, (json.loads(line[-1])["status"] if line else "TDS_NUMERICAL_FAILURE"), out.stderr[-1500:]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for r, status, errtxt in ex.map(go, todo):
            L.complete(r["tds_id"], status if status in C54.TDS_STATUS else "TDS_NUMERICAL_FAILURE", "" if status in C54.TDS_STATUS else errtxt[-300:])
            print(r["run_id"], status, flush=True)


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "target":
        target(*sys.argv[2:5])
    elif c == "plan":
        plan(sys.argv[2], sys.argv[3])
    elif c == "run":
        run_many(sys.argv[2], int(os.environ.get("DEC066_WORKERS", "5")))
