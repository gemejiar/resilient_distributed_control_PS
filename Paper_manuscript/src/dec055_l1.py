"""DEC-055 Lot L1 (5 TDS, gate G1).  Stages:  plan | run | analyze
  plan     writes IEEE39_DEC055_L1_plan.json exclusively (before any TDS): the 5 runs, their purpose and the G1 criteria
  run      requests every TDS id in the append-only ledger (parent process), executes the runs in parallel worker processes (one OC per process),
           stores every run (also failures) before completing the ledger
  analyze  G1 verdicts, figures FIG-F / FIG-V and the numerics figure; writes IEEE39_DEC055_L1_results.json exclusively"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

import dec054_common as C54
import dec055_common as C

PLAN = C.ART / "IEEE39_DEC055_L1_plan.json"
RUNS = C54.RUNS_DIR.parent / "DEC055_runs"
REF_RUN = "P3B2_b7P_M3"                       # stored DEC-054 run (OC1, TUNE bus 7, +0.58564 pu, M3 frozen dispatch of DEC-054)
CRIT = {"flat": {"init_residual_max": C.THR["init_residual"], "drift_window_s": [0.0, 20.0], "f_coi_drift_max_hz": C.THR["flat_drift_hz"], "mean_busfreq_drift_max_hz": C.THR["flat_drift_hz"],
                 "v_drift_max_pu": C.THR["flat_drift_pu"], "v_band": [C54.VLO, C54.VHI], "no_unit_limit_violation": True},
        "regression": {"P_Q_V_bit_identical_to_stored": True},
        "dt_half": {"window_s": [0.0, 20.0], "nadir_rel_diff_max": 0.01, "v_max_abs_diff_pu": 0.005, "p_max_abs_diff_pu": 0.005}}


def plan():
    st = {oc: json.loads((C.STATE / f"m0_{oc}.json").read_text(encoding="utf-8")) for oc in C.OC}
    ref = json.loads((C54.RUNS_DIR / REF_RUN / "config.json").read_text(encoding="utf-8"))
    zr = ref["test"]["z"]
    runs = [{"run_id": f"D55L1_flat_{oc}_M0", "oc": oc, "kind": "flat", "z": st[oc]["z"], "scenario": {"bus": 8, "kind": "P", "amp": 0.0}, "time_step_s": None, "pflow_tol": None,
             "purpose": f"G1 flat run of {oc} at its M0 dispatch (no event), COI recorded"} for oc in C.OC]
    runs.append({"run_id": "D55L1_regress_P3B2_b7P_M3", "oc": "OC1", "kind": "regression", "z": zr, "scenario": {"bus": ref["test"]["bus"], "kind": ref["test"]["kind"], "amp": ref["test"]["amp"]},
                 "time_step_s": None, "pflow_tol": 1e-6, "purpose": "COI-recording regression: re-run of the stored DEC-054 run with the DEC-055 runner (PFlow tol 1e-6 as stored)"})
    runs.append({"run_id": "D55L1_dthalf_P3B2_b7P_M3", "oc": "OC1", "kind": "dt_half", "z": zr, "scenario": dict(runs[-1]["scenario"]), "time_step_s": C54.DT / 2, "pflow_tol": 1e-6,
                 "purpose": "AC-04 step refinement of the same configuration (dt/2)"})
    with open(PLAN, "x", encoding="utf-8") as f:
        json.dump({"stage": "DEC-055 L1 plan (sealed before any TDS)", "runs": runs, "criteria": CRIT, "reference_run": REF_RUN,
                   "reference_series_sha256": C54.sha_file(C54.RUNS_DIR / REF_RUN / "series.npz"), "protocol_sha256": C54.sha_file(C.ROOT / "ops/sted/DEC055_protocol.md")}, f, indent=1)
    print("plan written", len(runs))


def _child(run_json):
    """Executed in a separate process: one TDS, stored with dec054_store.save_run (evidence kept also on failure)."""
    import dec054_store as ST
    import dec055_runner as R
    r = json.loads(run_json)
    res, err = None, None
    try:
        res = R.execute_tds_oc(r["oc"], np.asarray(r["z"], float), r["scenario"], r["time_step_s"], pflow_tol=r["pflow_tol"])
        status = res["status"]
    except Exception as ex:
        status, err = "TDS_NUMERICAL_FAILURE", ex
    res = res or {}
    ST.save_run(RUNS, r["run_id"], status=status, tds_id=r["tds_id"], series=res.get("series"), metrics=res.get("metrics"), config=r, diag=res.get("diag"),
                notes=str(res.get("notes", "")), error=err, ledger_row={"tds_id": r["tds_id"]})
    print(json.dumps({"run_id": r["run_id"], "status": status}))


def run():
    p = json.loads(PLAN.read_text(encoding="utf-8"))
    L = C.Ledger(C.LEDGER)
    for r in p["runs"]:
        r["tds_id"] = L.request("L1", r["kind"], r["oc"], r["run_id"], r["purpose"], solver=f"trapezoid dt={'2^-9' if r['time_step_s'] else '2^-8'}")
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")

    def go(r):
        out = subprocess.run([sys.executable, "-c", f"import dec055_l1 as M; M._child({json.dumps(json.dumps(r))})"], capture_output=True, text=True, cwd=str(C.SRC), env=env)
        line = [x for x in out.stdout.splitlines() if x.startswith("{")]
        return r, (json.loads(line[-1])["status"] if line else "TDS_NUMERICAL_FAILURE"), out.stderr[-1500:]
    with ThreadPoolExecutor(max_workers=len(p["runs"])) as ex:
        for r, status, errtxt in ex.map(go, p["runs"]):
            L.complete(r["tds_id"], status if status in C54.TDS_STATUS else "TDS_NUMERICAL_FAILURE", "" if status in C54.TDS_STATUS else errtxt[-300:])
            print(r["run_id"], status, flush=True)


def analyze():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    p = json.loads(PLAN.read_text(encoding="utf-8"))
    out = {"stage": "DEC-055 L1 results (G1)", "runs": {}, "criteria": p["criteria"]}
    ser = {}
    for r in p["runs"]:
        d = RUNS / r["run_id"]
        st = json.loads((d / "status.json").read_text(encoding="utf-8"))
        rec = {"status": st["status"], "tds_id": r["tds_id"] if "tds_id" in r else st.get("tds_id")}
        if (d / "series.npz").exists():
            z = dict(np.load(d / "series.npz"))
            ser[r["run_id"]] = z
            diag = json.loads((d / "diag.json").read_text(encoding="utf-8")) if (d / "diag.json").exists() else {}
            rec["final_residual"] = diag.get("final_residual")
        out["runs"][r["run_id"]] = rec
    verdict = {}
    for r in p["runs"]:
        z = ser.get(r["run_id"])
        rec = out["runs"][r["run_id"]]
        if z is None:
            verdict[r["run_id"]] = "FAIL (no series)"
            continue
        t = z["t"]
        w = (t >= 0.0) & (t <= 20.0)
        if r["kind"] == "flat":
            fc = z["f_coi_hz"]
            fm = C.mean_busfreq_hz(z["f_bus_hz"])
            V = z["V"]
            met = {"f_coi_drift_20s_hz": float(np.abs(fc[w] - fc[0]).max()), "mean_busfreq_drift_20s_hz": float(np.abs(fm[w] - fm[0]).max()),
                   "v_drift_20s_pu": float(np.abs(V[w] - V[0]).max()), "f_coi_drift_200s_hz": float(np.abs(fc - fc[0]).max()), "v_drift_200s_pu": float(np.abs(V - V[0]).max()),
                   "V_min": float(V.min()), "V_max": float(V.max()), "f_coi_0_hz": float(fc[0]), "status": rec["status"]}
            ok = (met["f_coi_drift_20s_hz"] <= C.THR["flat_drift_hz"] and met["mean_busfreq_drift_20s_hz"] <= C.THR["flat_drift_hz"] and met["v_drift_20s_pu"] <= C.THR["flat_drift_pu"]
                  and met["V_min"] >= C54.VLO and met["V_max"] <= C54.VHI and rec["status"] == "TDS_SAFE_OBSERVED" and (rec.get("final_residual") or 0) <= 1e-6)
            rec["metrics"] = met
            verdict[r["run_id"]] = "PASS" if ok else "FAIL"
        elif r["kind"] == "regression":
            ref = np.load(C54.RUNS_DIR / REF_RUN / "series.npz")
            same = {k: bool(z[k].shape == ref[k].shape and np.array_equal(z[k], ref[k])) for k in ("t", "P", "Q", "V")}
            diffs = {k: (float(np.abs(z[k] - ref[k]).max()) if z[k].shape == ref[k].shape else None) for k in ("P", "Q", "V")}
            rec["metrics"] = {"bit_identical": same, "max_abs_diff": diffs, "coi_present": "f_coi_hz" in z}
            verdict[r["run_id"]] = "PASS" if all(same.values()) and "f_coi_hz" in z else "FAIL"
        else:
            ref = np.load(C54.RUNS_DIR / REF_RUN / "series.npz")
            tr = ref["t"]
            wr = tr <= 20.0
            idx = np.searchsorted(t, tr[wr] - 1e-12)
            ok_grid = bool(np.allclose(t[idx], tr[wr], atol=1e-9))
            dP = float(np.abs(z["P"][idx] - ref["P"][wr]).max())
            dV = float(np.abs(z["V"][idx] - ref["V"][wr]).max())
            fh, fr = C.mean_busfreq_hz(z["f_bus_hz"][idx]), C.mean_busfreq_hz(ref["f_bus_hz"][wr])
            nad = float(abs((60 - fh.min()) - (60 - fr.min())) / max(60 - fr.min(), 1e-12))
            rec["metrics"] = {"grid_aligned": ok_grid, "P_max_abs_diff_20s": dP, "V_max_abs_diff_20s": dV, "mean_busfreq_nadir_rel_diff": nad}
            verdict[r["run_id"]] = "PASS" if ok_grid and dP <= 0.005 and dV <= 0.005 and nad <= 0.01 else "FAIL"
    out["verdict"] = verdict
    out["G1"] = "PASS" if all(v == "PASS" for v in verdict.values()) else "FAIL"
    # figures (FIG-F, FIG-V of the gate; numerics)
    fl = [r for r in p["runs"] if r["kind"] == "flat" and r["run_id"] in ser]
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    for r in fl:
        z = ser[r["run_id"]]
        ax[0].plot(z["t"], z["f_coi_hz"] - 60.0, lw=1, label=f"{r['oc']} f_COI")
        ax[1].plot(z["t"], C.mean_busfreq_hz(z["f_bus_hz"]) - 60.0, lw=1, label=f"{r['oc']} mean BusFreq")
    for a, ttl in zip(ax, ("f_COI - 60 Hz (6 GENROU, M*Sn weights)", "mean BusFreq - 60 Hz (39 buses, unweighted)")):
        a.axhspan(-C.THR["flat_drift_hz"], C.THR["flat_drift_hz"], color="0.9", label="G1 drift band")
        a.set(xlabel="t (s)", ylabel="Hz", title=ttl)
        a.legend(fontsize=7)
    fig.suptitle("DEC-055 L1 flat runs (no event), M0 dispatch of each OC")
    fig.tight_layout()
    with open(C.FIG / "IEEE39_DEC055_L1_frequency.png", "xb") as f:
        fig.savefig(f, dpi=140, format="png")
    plt.close(fig)
    fig, ax = plt.subplots(1, 3, figsize=(14, 4), sharey=True)
    for a, r in zip(ax, fl):
        z = ser[r["run_id"]]
        a.plot(z["t"], z["V"], lw=0.5, c="0.6")
        a.plot(z["t"], z["V"].min(axis=1), c="tab:blue", lw=1.2, label="V_min(t)")
        a.plot(z["t"], z["V"].max(axis=1), c="tab:red", lw=1.2, label="V_max(t)")
        a.axhline(C54.VLO, c="k", ls="--", lw=0.8)
        a.axhline(C54.VHI, c="k", ls="--", lw=0.8)
        a.set(xlabel="t (s)", title=f"{r['oc']}: |V| of the 39 buses")
        a.legend(fontsize=7)
    ax[0].set_ylabel("pu")
    fig.tight_layout()
    with open(C.FIG / "IEEE39_DEC055_L1_voltage.png", "xb") as f:
        fig.savefig(f, dpi=140, format="png")
    plt.close(fig)
    if "D55L1_dthalf_P3B2_b7P_M3" in ser:
        ref = np.load(C54.RUNS_DIR / REF_RUN / "series.npz")
        z = ser["D55L1_dthalf_P3B2_b7P_M3"]
        fig, ax = plt.subplots(1, 2, figsize=(12, 4))
        for i, u in ((1, "SG31"), (3, "SG35")):
            ax[0].plot(ref["t"], ref["P"][:, i], lw=1, label=f"{u} dt (stored)")
            ax[0].plot(z["t"], z["P"][:, i], lw=1, ls="--", label=f"{u} dt/2")
        ax[0].set(xlim=(4.9, 20), xlabel="t (s)", ylabel="P (pu)", title="AC-04 step refinement, P step bus 7")
        ax[1].plot(ref["t"], C.mean_busfreq_hz(ref["f_bus_hz"]), lw=1, label="dt (stored)")
        ax[1].plot(z["t"], C.mean_busfreq_hz(z["f_bus_hz"]), lw=1, ls="--", label="dt/2")
        if "f_coi_hz" in z:
            ax[1].plot(z["t"], z["f_coi_hz"], lw=1, label="f_COI dt/2")
        ax[1].set(xlim=(4.9, 20), xlabel="t (s)", ylabel="Hz", title="frequency")
        for a in ax:
            a.legend(fontsize=7)
        fig.tight_layout()
        with open(C.FIG / "IEEE39_DEC055_L1_numerics.png", "xb") as f:
            fig.savefig(f, dpi=140, format="png")
        plt.close(fig)
    with open(C.ART / "IEEE39_DEC055_L1_results.json", "x", encoding="utf-8") as f:
        json.dump(out, f, indent=1, default=float)
    print(json.dumps({"verdict": verdict, "G1": out["G1"]}, indent=1))


if __name__ == "__main__":
    {"plan": plan, "run": run, "analyze": analyze}[sys.argv[1]]()
