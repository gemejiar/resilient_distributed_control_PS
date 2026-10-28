"""DEC-054 G6 / P3-C: prospective cohort, 6 frozen scenarios x M0-M3 = 24 TDS (parallel execution, serial ledger/evidence).
Verifies the gate and the frozen file first (code hashes, one dispatch per method).  Every run (also failed ones) is requested in the ledger, executed with the FROZEN dispatch of its method,
stored exclusively and completed in the ledger.  No retries.  Run: <venv python> dec054_p3c.py"""
from __future__ import annotations

import os
import traceback
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

import dec054_common as COM
import dec054_runner as RUN
import dec054_store as ST

FROZEN = COM.ART / "IEEE39_DEC054_design_frozen.json"


def _exec(args):
    z, scenario = args
    try:
        import dec054_runner as R
        return R.execute_tds(np.asarray(z, float), scenario)
    except Exception:
        return {"status": "TDS_NUMERICAL_FAILURE", "error": traceback.format_exc(), "series": None, "metrics": None, "diag": None}


def main(workers: int = 6):
    for v in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"):
        os.environ[v] = "1"
    gate = COM.backup_gate()
    assert gate["verified"], gate
    frozen = RUN.verify_frozen(FROZEN, Path(__file__).parent)
    zs = RUN.validate_dispatches(frozen["dispatches"])
    scen = frozen["scenarios_test"]["scenarios"]
    assert [s["bus"] for s in scen] == COM.TEST
    ledger = COM.TdsLedger(COM.ART / "IEEE39_DEC054_tds_ledger.csv")
    jobs = []
    for s in scen:
        plan = [{"method": m, "scenario": s["name"], "z": zs[m]} for m in RUN.METHODS]
        RUN.assert_single_dispatch(plan, frozen["dispatches"])
        for m in RUN.METHODS:
            run_id = f"P3-C_{s['name']}_{m}"
            tid = ledger.request("P3-C", s["name"], m, run_id, "prospective comparison M0-M3 (frozen dispatch)")
            cfg = {"run_id": run_id, "tds_id": tid, "method": m, "scenario": s, "z": zs[m].tolist(), "z_sha256": RUN.z_digest(zs[m]), "frozen_file_sha256": COM.sha_file(FROZEN),
                   "code_sha256": frozen["code_sha256"], "andes_version": frozen["andes_version"], "params": frozen["params"]}
            jobs.append((run_id, tid, m, s, zs[m], cfg))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(_exec, (j[4].tolist(), j[3])) for j in jobs]
        for (run_id, tid, m, s, z, cfg), fu in zip(jobs, futs):
            try:
                res = fu.result()
                err = res.get("error")
            except Exception as ex:
                res, err = {}, repr(ex)
            status = res.get("status")
            if status not in COM.TDS_STATUS:
                status, err = "TDS_NUMERICAL_FAILURE", err or f"invalid status {status!r}"
            row = next((r for r in ledger.rows if r["tds_id"] == tid and r["status"] == "REQUESTED"), {})
            try:
                ST.save_run(COM.RUNS_DIR, run_id, status=status, tds_id=tid, series=res.get("series"), metrics=res.get("metrics"), config=cfg, diag=res.get("diag"), notes=str(res.get("notes", "")), error=err, ledger_row=row)
            except Exception as ex2:
                ledger.complete(tid, status, f"EVIDENCE_NOT_SAVED: {ex2!r}")
                raise
            ledger.complete(tid, status, (str(err) if err else str(res.get("notes", "")))[:400])
            print(run_id, status, flush=True)


if __name__ == "__main__":
    main()
