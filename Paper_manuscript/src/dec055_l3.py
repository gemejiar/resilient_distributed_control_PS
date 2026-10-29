"""DEC-055 Lot L3: blind TEST cohort {M0, M3} x B2 per OC (gate G5) and the final analysis (gate G7).
Stages:  plan <OC> | run <OC> | analyze
The plan of an OC is written exclusively from IEEE39_DEC055_design_frozen.json (whose hashes are verified) and committed before its TDS.
Stop rules (protocol section 9): numerical failure -> stop the lot; M3 violation in a confirmatory cell -> SAFETY_CLAIM_REFUTED (lot finishes unchanged);
jump/first-sample error > 5e-3 pu -> JUMP_VALIDATION_FAILED (cell); protected hash changed or budget exceeded -> stop."""
from __future__ import annotations

import csv
import json
import sys

import numpy as np

import dec054_common as C54
import dec055_common as C
import dec055_exec as X

FROZEN = C.ART / "IEEE39_DEC055_design_frozen.json"
CELLS = C.ART / "IEEE39_DEC055_cells_G4_TEST.csv"


def verify_frozen():
    f = json.loads(FROZEN.read_text(encoding="utf-8"))
    bad = [n for n, h in f["code_sha256"].items() if C54.sha_file(C.SRC / n) != h]
    bad += [oc for oc, h in f["case_sha256"].items() if C54.sha_file(C.OC[oc]["case"]) != h]
    if C54.sha_file(CELLS) != f["cells_sha256"]:
        bad.append("cells")
    if bad:
        raise C54.GateError(f"frozen hashes changed: {bad}")
    return f


def plan(oc):
    f = verify_frozen()
    cells = [r for r in csv.DictReader(open(CELLS, encoding="utf-8")) if r["oc"] == oc and r["schedule"] == "SCHEDULED"]
    runs, skipped = [], []
    for r in cells:
        m = r["strategy"][:2]
        d = f["dispatches"][oc][m]
        if r["exclusion_reason"] or d is None:
            skipped.append({"cell_id": r["cell_id"], "reason": r["exclusion_reason"] or "dispatch excluded"})
            continue
        runs.append({"run_id": f"D55L3_{r['cell_id']}", "cell_id": r["cell_id"], "oc": oc, "method": m, "bus": int(r["bus"]), "severity": r["severity"], "z": d["z"], "z_sha256": d["z_sha256"],
                     "scenario": {"bus": int(r["bus"]), "kind": "P", "amp": float(r["amp_pu"])}, "time_step_s": None, "confirmatory": r["confirmatory"] == "True",
                     "purpose": f"L3 TEST {oc} bus {r['bus']} {r['severity']} {r['strategy']} (frozen dispatch)"})
    out = C.ART / f"IEEE39_DEC055_L3_plan_{oc}.json"
    with open(out, "x", encoding="utf-8") as fh:
        json.dump({"stage": f"DEC-055 L3 TEST plan {oc} (sealed before its TDS)", "frozen_sha256": C54.sha_file(FROZEN), "runs": runs, "skipped_cells": skipped}, fh, indent=1)
    print(oc, "runs", len(runs), "skipped", len(skipped))


def run(oc):
    import dec054_runner as RUN
    verify_frozen()
    p = json.loads((C.ART / f"IEEE39_DEC055_L3_plan_{oc}.json").read_text(encoding="utf-8"))
    for r in p["runs"]:
        assert RUN.z_digest(np.array(r["z"])) == r["z_sha256"], "dispatch differs from the frozen one"
    X.execute(p["runs"], "L3")


def freq_metrics(ser):
    t = ser["t"]
    post = t >= C.EVENT_T - 1e-9
    out = {}
    fm = C.mean_busfreq_hz(ser["f_bus_hz"])
    out["mean_busfreq_nadir_hz"] = float(fm[post].min())
    out["nodal_worst_nadir_hz"] = float(ser["f_bus_hz"][post].min())
    out["nodal_nadir_spread_hz"] = float(ser["f_bus_hz"][post].min(axis=0).max() - ser["f_bus_hz"][post].min(axis=0).min())
    if "f_coi_hz" in ser:
        fc = ser["f_coi_hz"]
        out.update({"f_coi_nadir_hz": float(fc[post].min()), "rocof_coi_100ms_hz_s": C.rocof_window(t, fc),
                    "f_coi_err_120s_hz": float(abs(np.interp(120.0, t, fc) - 60.0)), "f_coi_err_200s_hz": float(abs(fc[-1] - 60.0))})
        out["restored"] = bool(out["f_coi_err_120s_hz"] <= C.THR["f_restore_hz"] and out["f_coi_err_200s_hz"] <= C.THR["f_restore_hz"])
    out["rocof_mean_busfreq_100ms_hz_s"] = C.rocof_window(t, fm)
    return out


def analyze():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    import dec055_l2 as L2
    cells = list(csv.DictReader(open(CELLS, encoding="utf-8")))
    rows, cell_out = [], []
    for oc in C.OC:
        pp = C.ART / f"IEEE39_DEC055_L3_plan_{oc}.json"
        if not pp.exists():
            continue
        p = json.loads(pp.read_text(encoding="utf-8"))
        for r in p["runs"]:
            m = L2.run_metrics(r["run_id"])
            s, cfg, met, ser = X.load_run(r["run_id"])
            fmx = freq_metrics(ser) if ser is not None else {}
            js = m.get("jump_vs_first_sample", {})
            cell = {"cell_id": r["cell_id"], "oc": oc, "bus": r["bus"], "severity": r["severity"], "strategy": r["method"] + "B2", "confirmatory": r["confirmatory"], "tds_status": s["status"],
                    "physical_violation": m.get("physical_violation"), "n_violating_pairs_P": m.get("n_violating_pairs_P"), "min_margin_Pmax_min": min(m.get("min_margin_Pmax") or [np.nan]),
                    "max_excess_Pmax": max(m.get("max_excess_Pmax") or [np.nan]), "V_min_post": m.get("V_min_post"), "V_max_post": m.get("V_max_post"), "violates_Q": m.get("violates_Q"), "violates_S": m.get("violates_S"),
                    "jump_first_sample_max_err": js.get("max_abs_err"), "jump_accepted": js.get("accepted"), **fmx}
            if cell["tds_status"] == "TDS_PHYSICAL_VIOLATION" and cell["physical_violation"] is False:
                cell["tds_status"] = "TDS_SAFE_OBSERVED"            # runner counts the event sample; the metric layer is authoritative
            cell_out.append(cell)
            if ser is not None:
                for i, u in enumerate(C.UNITS):
                    rows.append({"cell_id": r["cell_id"], "oc": oc, "bus": r["bus"], "severity": r["severity"], "method": r["method"], "unit": u,
                                 "min_margin_Pmax_pu": m["min_margin_Pmax"][i], "max_excess_Pmax_pu": m["max_excess_Pmax"][i], "min_margin_Pmin_pu": m["min_margin_Pmin"][i]})
    test_rows = [dict(c, tds_status=("TDS_PHYSICAL_VIOLATION" if c["physical_violation"] else c["tds_status"])) for c in cell_out]
    verdict = C.safety_verdict(test_rows)
    # cluster sign test (OC, bus) over confirmatory severities
    scores = {}
    for oc in C.OC:
        for b in C.TEST:
            sc = 0
            for s in C.SEVERITY:
                m0 = [c for c in cell_out if c["oc"] == oc and c["bus"] == b and c["severity"] == s and c["strategy"] == "M0B2"]
                m3 = [c for c in cell_out if c["oc"] == oc and c["bus"] == b and c["severity"] == s and c["strategy"] == "M3B2"]
                if not (m0 and m3 and m3[0]["confirmatory"]):
                    continue
                sc += int(bool(m0[0]["physical_violation"]) and not m3[0]["physical_violation"]) - int(bool(m3[0]["physical_violation"]) and not m0[0]["physical_violation"])
            scores[f"{oc}_b{b}"] = sc
    st = C.cluster_sign_test(scores)
    jfail = [c["cell_id"] for c in cell_out if c.get("jump_accepted") is False]
    out = {"stage": "DEC-055 L3 analysis (G5/G7)", "safety_verdict_C2": verdict, "cluster_scores": scores, "sign_test": st, "jump_validation_failed": jfail, "cells": cell_out,
           "skipped": {oc: json.loads((C.ART / f"IEEE39_DEC055_L3_plan_{oc}.json").read_text(encoding="utf-8"))["skipped_cells"] for oc in C.OC if (C.ART / f"IEEE39_DEC055_L3_plan_{oc}.json").exists()},
           "ta_predictions_frozen": json.loads(FROZEN.read_text(encoding="utf-8"))["ta_TEST_frozen"]}
    with open(C.ART / "IEEE39_DEC055_L3_results.json", "x", encoding="utf-8") as f:
        json.dump(out, f, indent=1, default=float)
    with open(C.ART / "IEEE39_DEC055_L3_unit_margins.csv", "x", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    # figure: min Pmax margin per cell, M0 vs M3
    fig, ax = plt.subplots(1, 3, figsize=(15, 4), sharey=True)
    for a, oc in zip(ax, C.OC):
        lab, v0, v3 = [], [], []
        for b in C.TEST:
            for s in C.SEVERITY:
                g = {c["strategy"]: c for c in cell_out if c["oc"] == oc and c["bus"] == b and c["severity"] == s}
                lab.append(f"{b}/{s}")
                v0.append(g.get("M0B2", {}).get("min_margin_Pmax_min", np.nan))
                v3.append(g.get("M3B2", {}).get("min_margin_Pmax_min", np.nan))
        x = np.arange(len(lab))
        a.bar(x - 0.2, v0, 0.4, color="tab:red", label="M0+B2")
        a.bar(x + 0.2, v3, 0.4, color="tab:green", label="M3+B2")
        a.axhline(0, c="k", lw=0.8)
        a.set_xticks(x, lab, rotation=60, fontsize=7)
        a.set(title=f"{oc}: min (Pmax - P) over the 10 units", ylabel="pu")
        a.legend(fontsize=7)
    fig.tight_layout()
    with open(C.FIG / "IEEE39_DEC055_L3_margins.png", "xb") as f:
        fig.savefig(f, dpi=140, format="png")
    plt.close(fig)
    print(json.dumps({"verdict": verdict["verdict"], "refuting": verdict["refuting_cells"], "sign_test": st, "jump_failed": jfail}, indent=1))


if __name__ == "__main__":
    a = sys.argv[1:]
    {"plan": lambda: plan(a[1]), "run": lambda: run(a[1]), "analyze": analyze}[a[0]]()
