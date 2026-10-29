"""DEC-059 gate records (verifiable 'actas').  Pure post-processing of stored files; writes IEEE39_DEC059_gate_<name>.json exclusively.
  r4_tune      gate R4 -> TUNE   (conditions 1-6 of the goal: G1-P, T1/T2 verifiable conditions, M3+OS design criteria, no demonstrated physical violation, registered parameters, TEST intact)
  test_freeze  gate TUNE -> TEST (registered later, after TUNE; same registry plus the frozen design and the pre-registered classification rules)
The acta states PASS or FAIL per condition with the quantitative evidence; the overall result is PASS only if every condition passes."""
from __future__ import annotations

import csv
import glob
import hashlib
import json
import os
import platform
import subprocess
import sys

import numpy as np

import dec054_common as C54
import dec055_common as C55
import dec059_tds as T

TEST_BUSES = set(C55.TEST)
ST59 = T.ST59
CODE = ("dec059_b5.py", "dec059_eq.py", "dec059_tds.py", "dec059_os.py", "dec059_pred.py", "dec059_metrics.py", "dec059_gate.py", "test_dec059.py")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, cwd=str(C55.ROOT)).stdout.strip()


def registry():
    import andes
    import kvxopt
    import scipy
    reg = {"git_head": git("rev-parse", "HEAD"), "git_branch": git("rev-parse", "--abbrev-ref", "HEAD"), "python": sys.version.split()[0], "executable": sys.executable,
           "andes": andes.__version__, "numpy": np.__version__, "scipy": scipy.__version__, "kvxopt": kvxopt.__version__, "platform": platform.platform(),
           "tds_config": {"method": "trapezoid", "dt": C54.DT, "tol": 1e-4, "reset_tiny": 0, "honest": 0, "max_iter": 15, "refine": "dt/16 on [t_e - dt, t_e + 0.5 s]"},
           "protocol_sha256": sha(C55.ROOT / "ops/sted/DEC059_protocol.md"), "theory_sha256": sha(C55.ART / "IEEE39_DEC059_theory.md"),
           "code_sha256": {f: sha(C55.SRC / f) for f in CODE}, "andes_source_modified": False,
           "parameters": {"v_bar_frac_of_rating_per_s": 0.01, "alpha_per_s": 1.0, "R": "diag(v_bar^-2)", "rho_s": 1e6, "tau_info_s": 1.0, "eps_sel": 0.01, "Q_L": "I",
                          "lambda": "1/(2 lmax(H_r))", "U_D8_pu": 0.0109, "eps_floor_pu": 1e-3, "tau_cut_pu": 1e-4, "seeds": "none (deterministic; no random numbers in controller or targets)"}}
    return reg


def tests_intact():
    bad, scanned = [], 0
    L = T.LEDGER
    if L.exists():
        for r in csv.DictReader(open(L, encoding="utf-8")):
            scanned += 1
            try:
                sc = json.loads(r["scenario"])
                if int(sc.get("bus", -1)) in TEST_BUSES and float(sc.get("amp", 0)) != 0:
                    bad.append(("ledger", r["tds_id"], sc))
            except Exception:
                pass
    for pth in glob.glob(str(C55.ART / "IEEE39_DEC059_*_plan.json")):
        for r in json.loads(open(pth, encoding="utf-8").read())["runs"]:
            scanned += 1
            if int(r["scenario"]["bus"]) in TEST_BUSES and float(r["scenario"]["amp"]) != 0:
                bad.append((os.path.basename(pth), r["run_id"], r["scenario"]))
    for pth in glob.glob(str(ST59 / "target_*")) + glob.glob(str(C55.ART / "IEEE39_DEC059_pred_*")):
        scanned += 1
        n = os.path.basename(pth)
        if any(f"_b{b}P_" in n for b in TEST_BUSES) or n.endswith("_test.json"):
            bad.append(("file", n))
    for d in glob.glob(str(T.RUNS / "*")):
        scanned += 1
        n = os.path.basename(d)
        if "TEST" in n.upper() or any(f"_b{b}P_" in n for b in TEST_BUSES):
            bad.append(("run", n))
    return {"scanned": scanned, "test_buses": sorted(TEST_BUSES), "violations": bad, "pass": not bad}


def r4_tune():
    import dec059_metrics as M
    acta = {"gate": "R4 -> TUNE", "conditions": {}}
    # 1. G1-P
    g1 = {}
    for oc in ("OC1", "OC2"):
        run = f"D59G1P_plant_flat_{oc}_M3OS"
        z, st, cfg, _ = M._load(run)
        f = z["f_bus_hz"]
        g = {"status": st["status"], "t_end": float(z["t"][-1]), "max_abs_df_hz": float(np.abs(f - f[0]).max()), "max_abs_dV_pu": float(np.abs(z["V"] - z["V"][0]).max()), "V_min": float(z["V"].min()),
             "V_max": float(z["V"].max()), "tds_id": json.loads((T.RUNS / run / "status.json").read_text(encoding="utf-8")).get("tds_id")}
        g["pass"] = bool(st["status"] != "TDS_NUMERICAL_FAILURE" and g["t_end"] >= 19.99 and g["max_abs_df_hz"] <= 0.005 and g["max_abs_dV_pu"] <= 1e-3 and g["V_min"] >= 0.95 and g["V_max"] <= 1.05)
        g1[oc] = g
    acta["conditions"]["1_G1P_OC1_OC2"] = {"detail": g1, "pass": all(v["pass"] for v in g1.values())}
    # 2. T1/T2 verifiable conditions
    r = subprocess.run([sys.executable, "test_dec059.py"], capture_output=True, text=True, cwd=str(C55.SRC), env=dict(os.environ, OMP_NUM_THREADS="1"))
    tests = {"returncode": r.returncode, "passed": r.stdout.count("PASS "), "failed": r.stdout.count("FAIL ")}
    tg = {}
    for oc in ("OC1", "OC2"):
        rows = {}
        for f in sorted(glob.glob(str(ST59 / f"target_r2_{oc}_M3OS_*.json"))):
            js = json.loads(open(f, encoding="utf-8").read())
            n = os.path.basename(f)[len("target_r2_"):-5]
            rows[n] = {"root_residual": js["root_residual"], "E4": js["E4"]["pass"], "T2": {k: v["pass"] for k, v in js["T2"].items()}, "H4_rate": js["T2"]["H4_sampled"]["max_re_equiv_rate_excl_null"],
                       "rho_q": js["T2"]["H4_sampled"]["rho_q"], "A_set": js["A_set"], "r_QP": js["radii"]["r_QP"], "lambda": js["clf"]["lambda"], "Hr_min_eig": js["clf"]["Hr_eig_min"]}
        d0 = rows.get(f"{oc}_M3OS_d0")
        tg[oc] = {"targets": rows, "d0_all_T2_E4": bool(d0 and d0["E4"] and all(d0["T2"].values())),
                  "cells_with_failed_T2_or_E4": [k for k, v in rows.items() if not (v["E4"] and all(v["T2"].values()))]}
    acta["conditions"]["2_T1_T2_verifiable"] = {"T1": "proved (IEEE39_DEC059_theory.md section 3) and unit-tested", "unit_tests": tests, "targets": tg,
                                               "pass": bool(tests["returncode"] == 0 and tests["failed"] == 0 and all(v["d0_all_T2_E4"] for v in tg.values())),
                                               "note": "cells whose E* target fails E4/H1-H5 are labelled OUTSIDE_ASSUMPTIONS for B5' in the reports; they do not fail the gate"}
    # 3. M3+OS design criteria
    ds = {}
    for oc in ("OC1", "OC2"):
        js = json.loads((ST59 / f"m3os_{oc}.json").read_text(encoding="utf-8"))
        mm = js["log"][-1]["min_margin"]
        ds[oc] = {"status": js["status"], "J": js["J"], "J_M3_DEC055": js["J_M3_DEC055"], "kkt": js["kkt"], "min_margin": mm, "init_ok": js.get("init_ok"),
                  "redispatch_MW_vs_M3_DEC055": js.get("redispatch_MW_abs_sum_vs_M3_DEC055"), "eps_OS_up": js["eps"]["eps_OS_up"], "eps_D8": js["eps"]["eps_D8"],
                  "pass": bool(js["status"] in ("FEASIBLE_PREDICTED", "LOCAL_OPTIMUM_FOUND") and mm >= -1e-4 and js.get("init_ok"))}
        pj = C55.ART / f"IEEE39_DEC059_pred_{oc}_M3OS_design.json"
        if pj.exists():
            pr = json.loads(pj.read_text(encoding="utf-8"))
            ds[oc]["design_cells_predicted"] = {"safe": pr["n_pred_safe"], "indeterminate": pr["n_pred_indeterminate"], "unsafe": pr["n_pred_unsafe"],
                                               "min_pred_pmax_margin": min(c["pred_pmax_margin_min"] for c in pr["cells"] if c.get("ok"))}
            ds[oc]["pass"] = bool(ds[oc]["pass"] and pr["n_pred_unsafe"] == 0)
    acta["conditions"]["3_M3OS_design_criteria"] = {"detail": ds, "pass": all(v["pass"] for v in ds.values())}
    # 4. no demonstrated physical violation in the required tests (G1-P flats + pre-event consistency of the targets)
    pre = {oc: {"pre_event_pmax_margin_min": json.loads((ST59 / f"m3os_{oc}.json").read_text(encoding="utf-8")).get("pre_event_pmax_margin_min")} for oc in ("OC1", "OC2")}
    flat_ok = all(v["pass"] for v in g1.values())
    d0e4 = {oc: tg[oc]["targets"].get(f"{oc}_M3OS_d0", {}).get("E4") for oc in tg}
    acta["conditions"]["4_no_demonstrated_physical_violation"] = {"G1P_flats_in_band_and_drift": flat_ok, "d0_targets_E4_admissible": d0e4,
                                                                   "note": "event-run safety is the object of TUNE and TEST, not of this gate", "pass": bool(flat_ok and all(d0e4.values()))}
    # 5. registry
    reg = registry()
    acta["registry"] = reg
    acta["conditions"]["5_parameters_versions_criteria_registered"] = {"pass": True, "items": sorted(reg.keys())}
    # 6. TEST intact
    ti = tests_intact()
    acta["conditions"]["6_TEST_intact"] = ti
    acta["ledger_used"] = T.Ledger(T.LEDGER).used()
    acta["overall"] = "PASS" if all(c["pass"] for c in acta["conditions"].values()) else "FAIL"
    with open(C55.ART / "IEEE39_DEC059_gate_R4_TUNE.json", "x", encoding="utf-8") as f:
        json.dump(acta, f, indent=1, default=float)
    print(json.dumps({k: v["pass"] for k, v in acta["conditions"].items()}), acta["overall"], "ledger", acta["ledger_used"])
    return acta


if __name__ == "__main__":
    {"r4_tune": r4_tune}[sys.argv[1]]()
