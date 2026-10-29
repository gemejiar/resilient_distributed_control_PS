"""DEC-055 G0: cell registry, static summaries and the G0 freeze manifest (no TDS).
Writes exclusively: IEEE39_DEC055_cells.csv, IEEE39_DEC055_static_summary.json, IEEE39_DEC055_g0_freeze.json."""
from __future__ import annotations

import json
import subprocess

import numpy as np
import pandas as pd

import dec054_common as C54
import dec055_common as C

ART, STATE = C.ART, C.STATE


def ld(name):
    p = STATE / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def main():
    rows = C.enumerate_cells()
    tc = {oc: ld(f"tc_{oc}") for oc in C.OC}
    import dec055_l0 as L0
    ta = {oc: L0.load_ta(oc) for oc in C.OC}
    des = {oc: {m: ld(f"{m}_{oc}") for m in ("m0", "m3")} for oc in C.OC}
    for r in rows:
        key = f"{r['partition']}_b{r['bus']}_{r['severity']}"
        t = (tc[r["oc"]] or {}).get("cells", {}).get(key, {})
        r["tc_class"] = t.get("tc_class", "NOT_COMPUTED")
        a = (ta[r["oc"]] or {}).get("cells", {}).get(key, {})
        r["ta_M0"], r["ta_M3"] = a.get("M0", {}).get("label", "NOT_COMPUTED"), a.get("M3", {}).get("label", "NOT_COMPUTED")
        m3s = (des[r["oc"]]["m3"] or {}).get("status", "MISSING")
        if r["severity"] == "S3":
            r["s3_status"] = C.classify_s3(r["tc_class"], m3s, r["ta_M3"])
        reasons = []
        if r["tc_class"] == "PROVEN_INFEASIBLE":
            reasons.append("PROVEN_INFEASIBLE (not simulated)")
        if r["partition"] == "TEST" and r["strategy"].startswith("M3") and m3s not in ("FEASIBLE_PREDICTED", "LOCAL_OPTIMUM_FOUND"):
            reasons.append(f"M3 design of {r['oc']} is {m3s}")
        r["exclusion_reason"] = "; ".join(reasons)
        r["confirmatory"] = C.confirmatory(r)
        notes = ["T-A labels from the PROVISIONAL L0 dispatches; recomputed with the frozen G4 dispatches before any TEST TDS"]
        if r["tc_class"] == "AC_UNDETERMINED":
            notes.append("exploratory only")
        if r["partition"] == "TEST" and r["schedule"] == "DEFERRED":
            notes.append("B1 arm deferred (full factorial kept)")
        r["notes"] = "; ".join(notes)
    C.write_cells(ART / "IEEE39_DEC055_cells.csv", rows)
    # ---- static summary
    g = pd.read_excel(C.BASE_CASE, sheet_name="GENROU")
    w = g.M * g.Sn
    summ = {"cells_total": len(rows), "by_partition": {p: sum(r["partition"] == p for r in rows) for p in ("DESIGN", "TUNE", "TEST")},
            "tc_classes_per_disturbance": {k: sum(c["tc_class"] == k for oc in C.OC for c in ((tc[oc] or {}).get("cells", {})).values()) for k in ("AC_FEASIBLE", "AC_UNDETERMINED", "PROVEN_INFEASIBLE")},
            "designs": {oc: {m: ({k: v for k, v in (d or {}).items() if k in ("status", "J", "kkt", "iterations", "seconds", "V_min", "V_max", "redispatch_MW_abs_sum", "init_ok")} if d else "MISSING") for m, d in des[oc].items()} for oc in C.OC},
            "ta_TEST": {}, "coi_weight_share": dict(zip(g.bus.astype(int).astype(str), (w / w.sum()).round(4).tolist())),
            "tc_capacity": {oc: {k: (tc[oc] or {}).get(k) for k in ("pmax_total", "load_total_pre")} for oc in C.OC}}
    for oc in C.OC:
        for key, rec in ((ta[oc] or {}).get("cells", {})).items():
            if key.startswith("TEST"):
                summ["ta_TEST"][f"{oc}_{key}"] = {m: {"label": v.get("label"), "worst": v.get("worst"), "violated": v.get("violated"), "residual": v.get("residual"), "gy_min_sv": v.get("gy_min_sv")} for m, v in rec.items()}
    scheduled = [r for r in rows if r["partition"] == "TEST" and r["schedule"] == "SCHEDULED"]
    summ["TEST_scheduled"] = {"n": len(scheduled), "confirmatory": sum(bool(r["confirmatory"]) for r in scheduled), "excluded": sum(bool(r["exclusion_reason"]) for r in scheduled)}
    with open(ART / "IEEE39_DEC055_static_summary.json", "x", encoding="utf-8") as f:
        json.dump(summ, f, indent=1, default=float)
    # ---- freeze manifest
    code = sorted(p.name for p in C.SRC.glob("dec055_*.py")) + ["test_dec055.py"] + [f"dec054_{n}.py" for n in ("common", "opf", "plant", "pool", "predictor", "rdcinit", "runner", "metrics", "store", "g4_design")] + \
        ["run_e8_ieee39.py", "run_b3_ieee39.py", "run_dec051_h3_jump.py", "dec051_core.py", "e9h_predictor.py", "e9a_linear.py", "run_dec051_equilibrium.py", "select_equilibrium_b3.py", "run_e7_ieee39.py", "run_e5_ieee39.py", "variant.py"]
    art = sorted(p.name for p in ART.glob("IEEE39_DEC055_*") if p.name != "IEEE39_DEC055_g0_freeze.json")
    st = sorted(p.name for p in STATE.glob("*.json"))
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=str(C.ROOT)).stdout.strip()
    man = {"stage": "DEC-055 G0 freeze (L0, 0 TDS)", "git_parent_commit": head, "protocol": {"path": "ops/sted/DEC055_protocol.md", "sha256": C54.sha_file(C.ROOT / "ops/sted/DEC055_protocol.md")},
           "thresholds": C.THR, "partitions": {"DESIGN": C.DESIGN, "TUNE": C.TUNE, "TUNE_SEVERITIES": C.TUNE_SEVERITIES, "TEST": C.TEST, "SEEN_NOT_TEST": C.SEEN_NOT_TEST},
           "severities": C.SEVERITY, "dp_ref_pu": C.DP_REF_PU, "strategies": C.STRATEGIES, "oc_rule": {"pv_cap_backoff_pu": C.PV_CAP_BACKOFF_PU, "pflow_tol": 1e-10},
           "cases": {oc: {"path": str(d["case"].relative_to(C.ROOT)), "sha256": C54.sha_file(d["case"]), "load_scale": d["load_scale"]} for oc, d in C.OC.items()},
           "code": {n: C54.sha_file(C.SRC / n) for n in code}, "artifacts": {n: C54.sha_file(ART / n) for n in art},
           "local_state": {n: C54.sha_file(STATE / n) for n in st}, "tds_used": 0,
           "provisional": "M0/M3 dispatches and T-A labels of L0 are provisional; the dispatch freeze is G4 (after L2)"}
    with open(ART / "IEEE39_DEC055_g0_freeze.json", "x", encoding="utf-8") as f:
        json.dump(man, f, indent=1)
    print(json.dumps({k: summ[k] for k in ("cells_total", "by_partition", "tc_classes_per_disturbance", "TEST_scheduled")}))


if __name__ == "__main__":
    main()
