"""DEC-055 parallel TDS execution for L2/L3: the parent requests every TDS id in the append-only ledger, each run executes in its own process
(one OC case per process), computes the static predictions (algebraic jump at t_e+, affine post-event predictor) BEFORE the TDS, stores the run
(also on failure) and the parent completes the ledger.  No retries."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

import dec054_common as C54
import dec055_common as C

RUNS = C54.RUNS_DIR.parent / "DEC055_runs"


def _child(run_json):
    import dec054_opf as OPF
    import dec054_predictor as PRD
    import dec054_store as ST
    import dec055_oc as OCM
    import dec055_runner as R
    r = json.loads(run_json)
    z = np.asarray(r["z"], float)
    pred, traj, perr = {}, {}, None
    if r.get("predict", True) and r["scenario"]["amp"] != 0.0:
        try:
            plant = OCM.make_plant(r["oc"])
            sc = OPF.Scenario(r["run_id"], r["scenario"]["bus"], r["scenario"]["kind"], r["scenario"]["amp"])
            j = plant.jump(z, sc)
            A, f, Cm = plant.affine(z, sc, diag=True)
            x = PRD.excursion(A, f, Cm)
            pred = {"jump_ok": bool(j.get("ok")), "jump_residual": j.get("residual"), "dP_jump": j["dP"].tolist(), "P_plus": j["P_plus"].tolist(), "Q_plus": j["Q_plus"].tolist(),
                    "V_plus": j["V_plus"].tolist(), "gy_min_sv": plant.last_affine_diag["gy_min_sv_post_jump"], "E_up": x["E_up"].tolist(), "E_dn": x["E_dn"].tolist(), "excursion_ok": bool(x["ok"])}
            traj = {"pred_t": x["t"], "pred_D": x["D"]}
        except Exception as ex:
            perr = repr(ex)
    res, err = None, None
    try:
        res = R.execute_tds_oc(r["oc"], z, r["scenario"], r.get("time_step_s"))
        status = res["status"]
    except Exception as ex:
        status, err = "TDS_NUMERICAL_FAILURE", ex
    res = res or {}
    series = res.get("series")
    if series is not None and traj:
        series = dict(series, **traj)
    cfg = dict(r, prediction=pred, prediction_error=perr)
    ST.save_run(RUNS, r["run_id"], status=status, tds_id=r["tds_id"], series=series, metrics=res.get("metrics"), config=cfg, diag=res.get("diag"),
                notes=str(res.get("notes", "")), error=err, ledger_row={"tds_id": r["tds_id"]})
    print(json.dumps({"run_id": r["run_id"], "status": status}))


def execute(runs: list, lot: str, workers: int = 6) -> list:
    L = C.Ledger(C.LEDGER)
    for r in runs:
        r["tds_id"] = L.request(lot, f"b{r['scenario']['bus']}{r['scenario']['kind']}_{r.get('severity', '')}", r["method"], r["run_id"], r["purpose"])
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")

    def go(r):
        out = subprocess.run([sys.executable, "-c", f"import dec055_exec as X; X._child({json.dumps(json.dumps(r))})"], capture_output=True, text=True, cwd=str(C.SRC), env=env)
        line = [x for x in out.stdout.splitlines() if x.startswith("{")]
        return r, (json.loads(line[-1])["status"] if line else "TDS_NUMERICAL_FAILURE"), out.stderr[-600:]
    done = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for r, status, errtxt in ex.map(go, runs):
            ok = status in C54.TDS_STATUS
            L.complete(r["tds_id"], status if ok else "TDS_NUMERICAL_FAILURE", "" if ok else errtxt[-300:])
            done.append((r["run_id"], status))
            print(r["run_id"], status, flush=True)
    return done


def load_run(run_id):
    d = RUNS / run_id
    st = json.loads((d / "status.json").read_text(encoding="utf-8"))
    cfg = json.loads((d / "config.json").read_text(encoding="utf-8"))
    met = json.loads((d / "metrics.json").read_text(encoding="utf-8")) if (d / "metrics.json").exists() else None
    ser = dict(np.load(d / "series.npz")) if (d / "series.npz").exists() else None
    return st, cfg, met, ser
