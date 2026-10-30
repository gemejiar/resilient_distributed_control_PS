"""DEC-062 pre-TEST validation (protocol ops/sted/DEC062_protocol.md section 4).  No TEST bus (21, 31, 39) appears here.
  plan A|B           A: G1-P of OC1 at the rev3 dispatch, plant without secondary control, 20 s (1 TDS).
                     B: OC2 at the frozen M3+OS dispatch with B5P: 6 fresh-bus cells (buses 3, 4, 12 x S2, S3) + 2 exact repeats of OC2 TUNE runs (b20 S3, b7 S3) for reproducibility (8 TDS).
  analyse [write]    checks V1-V6, writes IEEE39_DEC062_validation_results.json exclusively
  gate [write]       the access acta IEEE39_DEC062_gate_TEST_access.json (records the post-TUNE modification of the TEST access rule); never opens TEST
Run the TDS with:  dec059_tds.py run D62A D62B"""
from __future__ import annotations

import glob
import json
import sys

import numpy as np

import dec054_common as C54
import dec055_common as C55
import dec059_gate as G
import dec059_metrics as M
import dec059_tds as T
import dec059_tune as TU

FRESH = (3, 4, 12)
REPEATS = ("b20P_S3", "b7P_S3")
KEYS = ("t", "P", "Q", "V", "f_bus_hz")


def plan_a():
    r = {"oc": "OC1", "z": T.dispatch_z("OC1", "M3REV3"), "scenario": T.FLAT, "pflow_tol": None, "method": "trapezoid", "tol": 1e-4, "time_step_s": None, "activation_s": 1.0e9, "tf": 20.0,
         "controller": "B2", "reset_tiny": 0, "run_id": "D62G1P_plant_flat_OC1_M3REV3",
         "purpose": "DEC-062 V1: complete G1-P of OC1 at the rev3 dispatch: plant without secondary control, 20 s; frozen drift criteria 0.005 Hz / 1e-3 pu, buses in band"}
    return {"stage": "DEC-062 lot D62A plan (G1-P OC1 rev3; sealed before any TDS of the lot)", "block": "D62V", "runs": [r], "rev3_sha256": C54.sha_file(T.ST59 / "m3os_rev3_OC1.json"),
            "protocol_sha256": C54.sha_file(C55.ROOT / "ops/sted/DEC062_protocol.md")}


def plan_b():
    runs = []
    for bus in FRESH:
        for sev in ("S2", "S3"):
            amp = round(C55.oc_amp(sev), 5)
            runs.append(T.b5_run("OC2", {"bus": bus, "kind": "P", "amp": amp}, f"D62V_B5P_OC2_M3OS_b{bus}P_{sev}",
                                 f"DEC-062 V3: OC2 fresh-bus cell b{bus}P_{sev}, frozen M3+OS and B5P, local dt/16; (iii-U) prospective evaluation", "r2_OC2_M3OS_d0", f"r2_OC2_M3OS_b{bus}P_{amp:.5f}", m="M3OS"))
    for cell in REPEATS:
        bus, sev = int(cell.split("P_")[0][1:]), cell.split("_")[1]
        amp = round(C55.oc_amp(sev), 5)
        runs.append(T.b5_run("OC2", {"bus": bus, "kind": "P", "amp": amp}, f"D62REP_B5P_OC2_M3OS_b{bus}P_{sev}",
                             f"DEC-062 V2: exact repeat of D59TUNE_B5P_OC2_M3OS_b{bus}P_{sev} (reproducibility, expected bit-identical series)", "r2_OC2_M3OS_d0", f"r2_OC2_M3OS_b{bus}P_{amp:.5f}", m="M3OS"))
    return {"stage": "DEC-062 lot D62B plan (OC2 validation: fresh buses and repeats; sealed before any TDS of the lot)", "block": "D62V", "runs": runs,
            "protocol_sha256": C54.sha_file(C55.ROOT / "ops/sted/DEC062_protocol.md"), "m3os_sha256": C54.sha_file(T.ST59 / "m3os_OC2.json"),
            "pred_sha256": C54.sha_file(C55.ART / "IEEE39_DEC059_pred_OC2_M3OS_val.json"),
            "code_sha256": {f: C54.sha_file(C55.SRC / f) for f in ("dec059_b5.py", "dec059_eq.py", "dec059_tds.py", "dec059_os.py", "dec059_pred.py", "dec059_metrics.py", "dec059_tune.py", "dec062_val.py")}}


def plan(which):
    T.plan({"A": "D62A", "B": "D62B"}[which], {"A": plan_a, "B": plan_b}[which]())


def analyse(write=False):
    import dec055_oc as OCM
    out = {"stage": "DEC-062 pre-TEST validation results"}
    # V1: G1-P OC1 rev3 (20 s)
    z, st, cfg, _ = M._load("D62G1P_plant_flat_OC1_M3REV3")
    f = z["f_bus_hz"]
    g = {"status": st["status"], "t_end": float(z["t"][-1]), "max_abs_df_hz": float(np.abs(f - f[0]).max()), "max_abs_dV_pu": float(np.abs(z["V"] - z["V"][0]).max()), "V_min": float(z["V"].min()), "V_max": float(z["V"].max())}
    g["pass"] = bool(st["status"] != "TDS_NUMERICAL_FAILURE" and g["t_end"] >= 19.99 and g["max_abs_df_hz"] <= 0.005 and g["max_abs_dV_pu"] <= 1e-3 and g["V_min"] >= 0.95 and g["V_max"] <= 1.05)
    out["V1_G1P_OC1_rev3"] = g
    # V2: reproducibility
    rep = {}
    for cell in REPEATS:
        a = np.load(T.RUNS / f"D62REP_B5P_OC2_M3OS_{cell.replace('_', '_')}" / "series.npz", allow_pickle=True)
        b = np.load(T.RUNS / f"D59TUNE_B5P_OC2_M3OS_{cell}" / "series.npz", allow_pickle=True)
        d = {k: float(np.abs(a[k] - b[k]).max()) if a[k].shape == b[k].shape else None for k in KEYS}
        rep[cell] = {"max_abs_diff": d, "bit_identical": all(np.array_equal(a[k], b[k]) for k in KEYS)}
    out["V2_reproducibility"] = rep
    # V3-V5: fresh OC2 cells
    lim = OCM.make_plant("OC2").limits
    pr = json.loads((C55.ART / "IEEE39_DEC059_pred_OC2_M3OS_val.json").read_text(encoding="utf-8"))
    rows = []
    for c in pr["cells"]:
        run = f"D62V_B5P_OC2_M3OS_b{c['bus']}P_{c['severity']}"
        m = M.metrics(run, lim)
        m["G_R3"] = M.gr3(m)
        cls, why = M.classify(m)
        e = m["pmax_margin_min_50ms"] - c["pred_pmax_margin_min"]
        adm = bool(c.get("admissible_at_jump", False))
        rows.append({"cell": c["name"], "run_id": run, "eligible": bool(c["severity"] == "S2" or adm), "pred": {k: c.get(k) for k in ("jump_pmax_margin_min", "pred_pmax_margin_min", "pred_pmax_unit", "pred_class_all")},
                     "tds": {"m50": m["pmax_margin_min_50ms"], "m_after_50ms": m["pmax_margin_min_after_50ms"], "class": cls, "reasons": why, "V_min": m["V_bus_min"], "V_max": m["V_bus_max"]},
                     "e": e, "iii_H_two_sided": abs(e) <= TU.EPS_FLOOR, "iii_U_one_sided": e >= -TU.EPS_FLOOR, "class_matches_prediction": c.get("pred_class_all") == cls,
                     "false_SAFE": bool(c.get("pred_class_all") == "SAFE" and cls == "UNSAFE"), "G_R3": m["G_R3"], "target_labels": m.get("target_labels"),
                     "unit_V_err_200s": m["unit_V_err_end_vs_setpoint"], "regulation": {k: m.get(k) for k in ("f_coi_nadir_hz", "f_err_200s_hz", "settle_0p01Hz_s", "rocof_100ms_hz_s")}, "b5": m.get("b5")})
    tj = {}
    for fpath in sorted(glob.glob(str(T.ST59 / "target_r2_OC2_M3OS_b[0-9]*P_*.json"))):
        name = fpath.split("target_r2_OC2_M3OS_")[1][:-5]
        if int(name.split("P_")[0][1:]) in FRESH:
            js = json.loads(open(fpath, encoding="utf-8").read())
            tj[name] = {"E4": js["E4"]["pass"], "T2": {k: v["pass"] for k, v in js["T2"].items()}}
    el = [r for r in rows if r["eligible"]]
    out["cells"] = rows
    out["targets_fresh"] = tj
    out["checks"] = {"V1_G1P_OC1": g["pass"], "V2_repeats_bit_identical": all(v["bit_identical"] for v in rep.values()),
                     "V3_targets_E4_H1H5": bool(len(tj) == 6 and all(v["E4"] and all(v["T2"].values()) for v in tj.values())),
                     "V3_QP_no_fallback_T1_nonneg": all(r["G_R3"]["QP_no_fallback"] and r["G_R3"]["T1_reference_margins_nonneg"] for r in rows),
                     "V4_no_TDS_failure": not any(r["tds"]["class"] == "TDS_NUMERICAL_FAILURE" for r in rows),
                     "V5_no_false_SAFE": not any(r["false_SAFE"] for r in rows),
                     "V6_T2_local_V_decays": all((r["b5"] or {}).get("V_ratio_end_over_first_valid", 2) < 1 for r in rows)}
    out["reported_not_blocking"] = {"unsafe_eligible": [r["cell"] for r in el if r["tds"]["class"] == "UNSAFE"], "indeterminate": [r["cell"] for r in rows if r["tds"]["class"] == "NUMERICAL_INDETERMINATE" or r["tds"]["class"] == "NUMERICALLY_INDETERMINATE"],
                                    "iii_U_pass": all(r["iii_U_one_sided"] for r in rows), "iii_H_pass": all(r["iii_H_two_sided"] for r in rows), "iii_H_violating": [r["cell"] for r in rows if not r["iii_H_two_sided"]],
                                    "iv_failing": [r["cell"] for r in el if not all(v for k, v in r["G_R3"].items() if k.startswith("converged"))]}
    out["integrity_pass"] = all(out["checks"].values())
    print(json.dumps({"checks": out["checks"], "integrity_pass": out["integrity_pass"], "reported": out["reported_not_blocking"]}, indent=1))
    for r in rows:
        print(" ", r["cell"], "elig", r["eligible"], "pred", round(r["pred"]["pred_pmax_margin_min"], 4), "tds", round(r["tds"]["m50"], 4), r["tds"]["class"], "e", round(r["e"], 5), "Verr200", round(r["unit_V_err_200s"]["max"], 6))
    if write:
        with open(C55.ART / "IEEE39_DEC062_validation_results.json", "x", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1, default=float)
    return out


def gate():
    """Access acta: records the modification of the TEST access rule, the integrity checks V1-V6 and the freeze hashes.  Written before any TEST file exists."""
    import hashlib
    import subprocess
    v = json.loads((C55.ART / "IEEE39_DEC062_validation_results.json").read_text(encoding="utf-8"))
    intact = G.tests_intact()
    tg = {f.name: G.sha(f) for f in sorted(T.ST59.glob("target_*.json"))}
    code = ("dec054_common.py", "dec054_opf.py", "dec054_predictor.py", "dec054_plant.py", "dec055_common.py", "dec055_oc.py", "dec055_l0.py", "dec057_tds.py", "dec059_b5.py", "dec059_eq.py", "dec059_tds.py",
            "dec059_os.py", "dec059_pred.py", "dec059_metrics.py", "dec059_tune.py", "dec059_gate.py", "dec061_design.py", "dec061_rev3.py", "dec062_val.py", "dec062_r5.py", "dec062_test.py", "run_b3_ieee39.py")
    acta = {"gate": "DEC-062 access to TEST as an independent evaluation", "label": "EVALUATION_UNDER_MODIFIED_ACCESS_RULE",
            "preserved_verdicts": {"DEC-059 TUNE->TEST": "REJECTED", "DEC-060": "REJECTED_TEST_SEALED", "DEC-061 G-v2": "REJECTED_TEST_SEALED", "criterion_iv_failing_cells_DEC061": ["b7P_S3", "b16P_S3", "b24P_S3"],
                                   "criterion_iii_H_failing_DEC061": ["b20P_S2", "b20P_S3"]},
            "rule_modification": "Post-TUNE change of the TEST access rule (protocol DEC062 section 5): TEST opens as an independent evaluation if V1-V6 pass and the freeze is complete. It does not approve G3/G-v2 retroactively and does not "
                                 "mean full compliance with the original protocol.",
            "checks": v["checks"], "integrity_pass": v["integrity_pass"], "validation_reported_not_blocking": v["reported_not_blocking"], "TEST_intact_before_freeze": intact,
            "ledger_used": T.Ledger(T.LEDGER).used(), "committed_total": 112, "registry": G.registry(),
            "frozen_hashes": {"design_OC1_rev3": C54.sha_file(T.ST59 / "m3os_rev3_OC1.json"), "design_OC2_M3OS": C54.sha_file(T.ST59 / "m3os_OC2.json"), "protocols": {f: G.sha(C55.ROOT / "ops/sted" / f) for f in ("DEC059_protocol.md", "DEC061_protocol.md", "DEC062_protocol.md")},
                              "criterion_iii_doc": G.sha(C55.ART / "IEEE39_DEC061_criterion_iii.md"), "theory": G.sha(C55.ART / "IEEE39_DEC059_theory.md"), "code": {f: G.sha(C55.SRC / f) for f in code},
                              "n_targets": len(tg), "targets_sha256_of_hashes": hashlib.sha256(json.dumps(tg, sort_keys=True).encode()).hexdigest(), "git_head": G.git("rev-parse", "HEAD"), "git_dirty": G.git("status", "--porcelain")},
            "classification_rules": "rule M3V-1 (Addendum B item 1), U_D8 = 0.0109 pu; eligibility S1/S2 confirmatory, S3 promoted if admissible_at_jump at the dispatch under test; criteria G3 (i)-(iv) reported per OC and dispatch, (iii-H) and (iii-U) separately",
            "test_opened": False}
    acta["verdict"] = "ACCESS_AUTHORIZED_FREEZE_COMPLETE" if (v["integrity_pass"] and intact["pass"]) else "ACCESS_BLOCKED"
    with open(C55.ART / "IEEE39_DEC062_gate_TEST_access.json", "x", encoding="utf-8") as f:
        json.dump(acta, f, indent=1, default=float)
    print(acta["verdict"], acta["checks"], "intact", intact["pass"], "ledger", acta["ledger_used"], "dirty:", acta["frozen_hashes"]["git_dirty"][:200])


if __name__ == "__main__":
    if sys.argv[1] == "gate":
        gate()
    elif sys.argv[1] == "plan":
        plan(sys.argv[2])
    elif sys.argv[1] == "analyse":
        analyse("write" in sys.argv)
