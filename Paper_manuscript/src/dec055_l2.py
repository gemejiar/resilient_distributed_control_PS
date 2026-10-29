"""DEC-055 Lot L2 (TUNE verification, eps recalibration, one dynamic-cut round) and gate G4 (freeze before TEST).
Stages:  planA | runA | analyzeA | redesign <OC> | planB | runB | analyzeB | freeze
Rules (declared in the sealed plan before any L2 TDS):
  R1 round A: the provisional M3 dispatch of every OC with a feasible design is run at the 8 TUNE events {7,20,16,24} x {S2,S3} (B2, 200 s).
  R2 eps_OC = max(eps_TUNE-OC1 prior, eps_floor, kappa * max positive signed error of round A of that OC), per unit and side (peak / trough).
  R3 G3 PASS for an OC if round A shows no physical violation (P, Q, S, V at stored samples) AND every DESIGN margin of the provisional dispatch,
     recomputed with eps_OC, is >= -tau_cut.  The dispatch is then kept.
  R4 otherwise one redesign round: Algorithm 1 with eps_OC plus a local dynamic cut (delta = observed excess + tau_cut, trust region r_tr) for every
     violating (unit, TUNE event); round B re-verifies the violating TUNE events and the TUNE event with the smallest observed margin (<= 8 TDS shared by
     all OCs, allocated in OC order).  A violation in round B is a STOP for M3 in that OC (no M3 TEST cells there; registered as excluded).
  R5 G4 freezes one M0 and one M3 dispatch per OC, eps_OC, code hashes; T-A labels and the S3 status of every TEST cell are recomputed with the frozen
     dispatches and frozen in a new cell registry before any TEST TDS."""
from __future__ import annotations

import csv
import json
import os
import subprocess
import sys

import numpy as np

import dec054_common as C54
import dec055_common as C
import dec055_exec as X

PLAN_A, PLAN_B = C.ART / "IEEE39_DEC055_L2_planA.json", C.ART / "IEEE39_DEC055_L2_planB.json"
RULES = __doc__.split("Rules (declared in the sealed plan before any L2 TDS):")[1].strip()


def st(name):
    p = C.STATE / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def m3_ok(oc):
    s = st(f"m3_{oc}")
    return bool(s and s.get("z") and s["status"] in ("FEASIBLE_PREDICTED", "LOCAL_OPTIMUM_FOUND"))


def planA():
    runs = []
    for oc in C.OC:
        if not m3_ok(oc):
            continue
        z = st(f"m3_{oc}")["z"]
        for b in C.TUNE:
            for s in C.TUNE_SEVERITIES:
                runs.append({"run_id": f"D55L2A_{oc}_b{b}_{s}_M3", "oc": oc, "method": "M3", "bus": b, "severity": s, "z": z, "scenario": {"bus": b, "kind": "P", "amp": C.oc_amp(s)},
                             "time_step_s": None, "purpose": f"L2 round A: TUNE verification of the provisional M3 dispatch of {oc}, bus {b}, {s}"})
    with open(PLAN_A, "x", encoding="utf-8") as f:
        json.dump({"stage": "DEC-055 L2 round A plan (sealed before any L2 TDS)", "rules": RULES, "runs": runs, "excluded_OC": [oc for oc in C.OC if not m3_ok(oc)],
                   "m3_state_sha256": {oc: C54.sha_file(C.STATE / f"m3_{oc}.json") for oc in C.OC if (C.STATE / f"m3_{oc}.json").exists()}}, f, indent=1)
    print("planA", len(runs))


def runA():
    X.execute(json.loads(PLAN_A.read_text(encoding="utf-8"))["runs"], "L2")


def run_metrics(run_id):
    import dec054_p3a_audit as P3A
    s, cfg, met, ser = X.load_run(run_id)
    out = {"status": s["status"]}
    if ser is None or met is None:
        return out
    un = met["unit"]
    out.update({"n_violating_pairs_P": met["n_violating_pairs_P"], "V_outside_buses_post": met.get("V_outside_buses_post"), "V_min_post": met.get("V_min_post"), "V_max_post": met.get("V_max_post"),
                "min_margin_Pmax": un["Pmax"]["min_margin"], "min_margin_Pmin": un["Pmin"]["min_margin"], "max_excess_Pmax": un["Pmax"]["max_excess"], "max_excess_Pmin": un["Pmin"]["max_excess"],
                "violates_Q": bool(any(un["Qmax"]["violates"]) or any(un["Qmin"]["violates"])), "violates_S": bool(any(un["Smax"]["violates"]))})
    out["physical_violation"] = bool(out["n_violating_pairs_P"] > 0 or (out["V_outside_buses_post"] or 0) > 0 or out["violates_Q"] or out["violates_S"])
    pr = cfg.get("prediction") or {}
    if pr.get("dP_jump") and "pred_t" in ser:
        cr = P3A.compare_run(ser["t"], ser["P"], pr["dP_jump"], ser["pred_t"], ser["pred_D"])
        out.update({"e_peak": cr["e_peak"].tolist(), "e_trough": cr["e_trough"].tolist(), "first_sample_error": cr["first_sample_error"].tolist()})
        js = C.jump_vs_first_sample(ser["t"], ser["P"], pr["P_plus"])
        out["jump_vs_first_sample"] = js
    return out


def eps_prior():
    import dec054_g4_design as G4
    eJ, eEu, eEd = G4.eps_vectors()
    return eJ, eEu, eEd


def analyzeA():
    p = json.loads(PLAN_A.read_text(encoding="utf-8"))
    kap, fl = C54.PROPOSED["kappa"], C54.PROPOSED["eps_floor_pu"]
    eJ, eEu, eEd = eps_prior()
    res = {"stage": "DEC-055 L2 round A analysis", "runs": {}, "oc": {}}
    rows = []
    for r in p["runs"]:
        m = run_metrics(r["run_id"])
        res["runs"][r["run_id"]] = m
        for i, u in enumerate(C.UNITS):
            rows.append({"run_id": r["run_id"], "oc": r["oc"], "bus": r["bus"], "severity": r["severity"], "unit": u, "status": m["status"],
                         "min_margin_Pmax_pu": (m.get("min_margin_Pmax") or [None] * 10)[i], "min_margin_Pmin_pu": (m.get("min_margin_Pmin") or [None] * 10)[i],
                         "peak_error_signed_pu": (m.get("e_peak") or [None] * 10)[i], "trough_error_signed_pu": (m.get("e_trough") or [None] * 10)[i],
                         "first_sample_error_pu": (m.get("first_sample_error") or [None] * 10)[i]})
    for oc in sorted({r["oc"] for r in p["runs"]}):
        rr = [res["runs"][r["run_id"]] for r in p["runs"] if r["oc"] == oc]
        ep = np.array([x["e_peak"] for x in rr if "e_peak" in x])
        et = np.array([x["e_trough"] for x in rr if "e_trough" in x])
        up = np.maximum.reduce([eEu, np.full(10, fl), kap * np.maximum(ep.max(axis=0), 0.0)]) if ep.size else eEu
        dn = np.maximum.reduce([eEd, np.full(10, fl), kap * np.maximum(et.max(axis=0), 0.0)]) if et.size else eEd
        viol = [r["run_id"] for r in p["runs"] if r["oc"] == oc and res["runs"][r["run_id"]].get("physical_violation", True)]
        fails = [r["run_id"] for r in p["runs"] if r["oc"] == oc and res["runs"][r["run_id"]]["status"] == "TDS_NUMERICAL_FAILURE"]
        res["oc"][oc] = {"eps_E_up": up.tolist(), "eps_E_dn": dn.tolist(), "eps_J": eJ.tolist(), "violating_runs": viol, "numerical_failures": fails,
                         "max_jump_vs_first_sample": max([x["jump_vs_first_sample"]["max_abs_err"] for x in rr if "jump_vs_first_sample" in x] or [None])}
    # R3 static recheck of the DESIGN margins with eps_OC (separate process per OC)
    for oc, v in res["oc"].items():
        code = ("import json,numpy as np,dec055_oc as O,dec054_opf as OPF,dec055_l0 as L0,dec054_common as C54;p=O.make_plant('%s');"
                "z=np.array(json.load(open(r'%s'))['z']);pb=OPF.Problem(p,'M3',L0.design_scenarios(),np.array(%s),np.array(%s),cfg=dict(C54.PROPOSED),eps_E_dn=np.array(%s));"
                "mg=pb.all_margins(z);print(json.dumps(float(min(min(a[0].min(),a[1].min()) for a in mg.values()))))") % (oc, str(C.STATE / f"m3_{oc}.json"), v["eps_J"], v["eps_E_up"], v["eps_E_dn"])
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(C.SRC), env=dict(os.environ, OMP_NUM_THREADS="1"))
        try:
            v["design_min_margin_with_eps_OC"] = json.loads(out.stdout.strip().splitlines()[-1])
        except Exception:
            v["design_min_margin_with_eps_OC"] = None
            v["recheck_error"] = out.stderr[-500:]
        mm = v["design_min_margin_with_eps_OC"]
        v["G3"] = "PASS" if (not v["violating_runs"] and not v["numerical_failures"] and mm is not None and mm >= -C54.PROPOSED["tau_cut_pu"]) else "REDESIGN_REQUIRED"
        print(oc, v["G3"], "violations", v["violating_runs"], "design min margin", mm, flush=True)
    with open(C.ART / "IEEE39_DEC055_L2_resultsA.json", "x", encoding="utf-8") as f:
        json.dump(res, f, indent=1, default=float)
    with open(C.ART / "IEEE39_DEC055_L2_validationA.csv", "x", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def redesign(oc):
    """R4: Algorithm 1 with eps_OC and local dynamic cuts for the violating (unit, TUNE event) of round A."""
    import time

    import dec054_opf as OPF
    import dec055_l0 as L0
    import dec055_oc as OCM
    t0 = time.time()
    A = json.loads((C.ART / "IEEE39_DEC055_L2_resultsA.json").read_text(encoding="utf-8"))
    v = A["oc"][oc]
    plant = OCM.OCPooledPlant(oc, int(os.environ.get("DEC055_WORKERS", "3")))
    scen = L0.design_scenarios()
    p = json.loads(PLAN_A.read_text(encoding="utf-8"))
    cuts = []
    for r in p["runs"]:
        if r["oc"] != oc or r["run_id"] not in v["violating_runs"]:
            continue
        m = A["runs"][r["run_id"]]
        scen.append(OPF.Scenario(f"TUNE_b{r['bus']}_{r['severity']}", r["bus"], "P", C.oc_amp(r["severity"])))
        for i in range(10):
            for cls, ex in (("P+", m["max_excess_Pmax"][i]), ("P-", m["max_excess_Pmin"][i])):
                if ex > 0:
                    cuts.append((len(scen) - 1, i, cls, ex + C54.PROPOSED["tau_cut_pu"]))
    cfg = dict(C54.PROPOSED, K_max=8, N_it=25, ftol=1e-6, verbose=False)
    z0 = np.array(st(f"m3_{oc}")["z"])
    rr = np.concatenate([np.full(9, C54.PROPOSED["r_tr_p0_pu"]), np.full(10, C54.PROPOSED["r_tr_v0_pu"])])
    pb_hook = {"cuts": [{"d": d, "i": i, "cls": c, "delta": dl} for d, i, c, dl in cuts]}
    orig = OPF.Problem.__init__

    def init(self, *a, **k):
        orig(self, *a, **k)
        for c in pb_hook["cuts"]:
            self.add_dynamic_cut(c["d"], c["i"], c["cls"], c["delta"], z0, rr)
    OPF.Problem.__init__ = init
    try:
        r = OPF.algorithm1(plant, "M3", scen, np.array(v["eps_J"]), np.array(v["eps_E_up"]), cfg=cfg, z_seeds=[z0], k0=4, eps_E_dn=np.array(v["eps_E_dn"]))
    finally:
        OPF.Problem.__init__ = orig
        plant.close()
    out = {"oc": oc, "status": r.status, "J": r.J, "kkt": r.kkt_residual, "z": None if r.z is None else r.z.tolist(), "cuts": pb_hook["cuts"], "added_TUNE_events": [s.name for s in scen[12:]],
           "eps": {"J": v["eps_J"], "E_up": v["eps_E_up"], "E_dn": v["eps_E_dn"]}, "seconds": round(time.time() - t0, 1)}
    with open(C.STATE / f"m3r_{oc}.json", "x", encoding="utf-8") as f:
        json.dump(out, f, indent=1, default=float)
    print(oc, "redesign", r.status, r.J)


def final_m3(oc):
    """Dispatch frozen for M3 in the OC per R3/R4/round B (None => M3 excluded in that OC)."""
    A = json.loads((C.ART / "IEEE39_DEC055_L2_resultsA.json").read_text(encoding="utf-8"))
    if oc not in A["oc"]:
        return None, "M3 design not feasible (G2)"
    v = A["oc"][oc]
    if v["G3"] == "PASS":
        return st(f"m3_{oc}"), "round A PASS"
    rd = st(f"m3r_{oc}")
    if not rd or rd["status"] not in ("FEASIBLE_PREDICTED", "LOCAL_OPTIMUM_FOUND") or rd["z"] is None:
        return None, "redesign failed"
    B = C.ART / "IEEE39_DEC055_L2_resultsB.json"
    if not B.exists():
        return None, "round B not executed"
    b = json.loads(B.read_text(encoding="utf-8"))["oc"].get(oc)
    if not b or b["violating_runs"] or b["numerical_failures"]:
        return None, "round B violation or failure (STOP for M3 in this OC)"
    return rd, "redesigned and verified in round B"


def planB():
    A = json.loads((C.ART / "IEEE39_DEC055_L2_resultsA.json").read_text(encoding="utf-8"))
    p = json.loads(PLAN_A.read_text(encoding="utf-8"))
    runs, budget = [], 8
    for oc, v in A["oc"].items():
        if v["G3"] == "PASS":
            continue
        rd = st(f"m3r_{oc}")
        if not rd or rd["z"] is None or rd["status"] not in ("FEASIBLE_PREDICTED", "LOCAL_OPTIMUM_FOUND"):
            continue
        cand = [r for r in p["runs"] if r["oc"] == oc]
        pick = [r for r in cand if r["run_id"] in v["violating_runs"]]
        smallest = min(cand, key=lambda r: min(A["runs"][r["run_id"]].get("min_margin_Pmax") or [9]))
        if smallest not in pick:
            pick.append(smallest)
        for r in pick[:max(0, min(3, budget))]:
            runs.append(dict(r, run_id=r["run_id"].replace("D55L2A", "D55L2B"), z=rd["z"], purpose=f"L2 round B: re-verification of the redesigned M3 of {oc}"))
            budget -= 1
    with open(PLAN_B, "x", encoding="utf-8") as f:
        json.dump({"stage": "DEC-055 L2 round B plan (sealed before the round-B TDS)", "rules": RULES, "runs": runs}, f, indent=1)
    print("planB", len(runs))


def runB():
    X.execute(json.loads(PLAN_B.read_text(encoding="utf-8"))["runs"], "L2")


def analyzeB():
    p = json.loads(PLAN_B.read_text(encoding="utf-8"))
    res = {"stage": "DEC-055 L2 round B analysis", "runs": {r["run_id"]: run_metrics(r["run_id"]) for r in p["runs"]}, "oc": {}}
    for oc in sorted({r["oc"] for r in p["runs"]}):
        ids = [r["run_id"] for r in p["runs"] if r["oc"] == oc]
        res["oc"][oc] = {"violating_runs": [i for i in ids if res["runs"][i].get("physical_violation", True)], "numerical_failures": [i for i in ids if res["runs"][i]["status"] == "TDS_NUMERICAL_FAILURE"]}
    with open(C.ART / "IEEE39_DEC055_L2_resultsB.json", "x", encoding="utf-8") as f:
        json.dump(res, f, indent=1, default=float)
    print(json.dumps(res["oc"]))


def freeze():
    """G4.  One M0 and one M3 dispatch per OC; T-A of TEST cells recomputed with the frozen dispatches (separate process per OC); new cell registry."""
    import dec054_runner as RUN
    A = json.loads((C.ART / "IEEE39_DEC055_L2_resultsA.json").read_text(encoding="utf-8"))
    disp, notes = {}, {}
    for oc in C.OC:
        m0 = st(f"m0_{oc}")
        m3, why = final_m3(oc)
        disp[oc] = {"M0": {"z": m0["z"], "status": m0["status"], "J": m0["J"], "z_sha256": RUN.z_digest(np.array(m0["z"]))},
                    "M3": None if m3 is None else {"z": m3["z"], "status": m3["status"], "J": m3["J"], "z_sha256": RUN.z_digest(np.array(m3["z"]))}}
        notes[oc] = why
    ta = {}
    for oc in C.OC:
        code = ("import json,numpy as np,dec055_oc as O,dec054_opf as OPF,dec055_common as C;p=O.make_plant('%s');lim={k:np.asarray(v) for k,v in p.limits.items()};d=json.loads(%r);out={}\n"
                "for m,e in d.items():\n"
                " if e is None: continue\n"
                " z=np.array(e['z'])\n"
                " for b in C.TEST:\n"
                "  for s in C.SEVERITY:\n"
                "   j=p.jump(z,OPF.Scenario('t',b,'P',C.oc_amp(s)))\n"
                "   if j.get('ok'):\n"
                "    p.affine(z,OPF.Scenario('t',b,'P',C.oc_amp(s)),diag=True);j['gy_min_sv']=p.last_affine_diag['gy_min_sv_post_jump']\n"
                "   r=C.classify_ta(j,lim);out[f'{m}_b{b}_{s}']={'label':r['label'],'worst':r.get('worst'),'violated':r.get('violated'),'P_plus':np.asarray(j.get('P_plus',[])).tolist()}\n"
                "print(json.dumps(out))") % (oc, json.dumps(disp[oc]))
        o = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(C.SRC), env=dict(os.environ, OMP_NUM_THREADS="1"))
        ta[oc] = json.loads(o.stdout.strip().splitlines()[-1])
    tc = {oc: st(f"tc_{oc}") for oc in C.OC}
    rows = []
    for r in C.enumerate_cells():
        if r["partition"] != "TEST":
            continue
        key = f"TEST_b{r['bus']}_{r['severity']}"
        r["tc_class"] = tc[r["oc"]]["cells"][key]["tc_class"]
        r["ta_M0"] = ta[r["oc"]].get(f"M0_b{r['bus']}_{r['severity']}", {}).get("label", "NOT_COMPUTED")
        r["ta_M3"] = ta[r["oc"]].get(f"M3_b{r['bus']}_{r['severity']}", {}).get("label", "M3_EXCLUDED")
        m3s = (disp[r["oc"]]["M3"] or {}).get("status", "EXCLUDED")
        if r["severity"] == "S3":
            r["s3_status"] = C.classify_s3(r["tc_class"], m3s, r["ta_M3"])
        reasons = []
        if r["strategy"].startswith("M3") and disp[r["oc"]]["M3"] is None:
            reasons.append(f"M3 excluded in {r['oc']}: {notes[r['oc']]}")
        if r["tc_class"] == "PROVEN_INFEASIBLE":
            reasons.append("PROVEN_INFEASIBLE")
        r["exclusion_reason"] = "; ".join(reasons)
        r["confirmatory"] = C.confirmatory(r)
        r["notes"] = "frozen at G4" + ("; B1 arm deferred" if r["schedule"] == "DEFERRED" else "")
        rows.append(r)
    C.write_cells(C.ART / "IEEE39_DEC055_cells_G4_TEST.csv", rows)
    code_files = sorted(p.name for p in C.SRC.glob("dec055_*.py")) + ["dec054_runner.py", "dec054_plant.py", "dec054_metrics.py", "dec054_opf.py", "dec054_predictor.py", "run_b3_ieee39.py", "run_e8_ieee39.py"]
    frozen = {"stage": "DEC-055 G4 design freeze (before any TEST TDS)", "dispatches": disp, "dispatch_notes": notes,
              "eps": {oc: {k: A["oc"][oc][k] for k in ("eps_J", "eps_E_up", "eps_E_dn")} for oc in A["oc"]}, "ta_TEST_frozen": ta,
              "test_scenarios": [{"oc": r["oc"], "bus": r["bus"], "severity": r["severity"], "amp_pu": r["amp_pu"]} for r in rows if r["strategy"] == "M0B2"],
              "code_sha256": {n: C54.sha_file(C.SRC / n) for n in code_files}, "protocol_sha256": C54.sha_file(C.ROOT / "ops/sted/DEC055_protocol.md"),
              "cells_sha256": C54.sha_file(C.ART / "IEEE39_DEC055_cells_G4_TEST.csv"), "case_sha256": {oc: C54.sha_file(d["case"]) for oc, d in C.OC.items()}}
    with open(C.ART / "IEEE39_DEC055_design_frozen.json", "x", encoding="utf-8") as f:
        json.dump(frozen, f, indent=1, default=float)
    print(json.dumps({oc: {m: (v["status"] if v else None) for m, v in d.items()} for oc, d in disp.items()}), json.dumps(notes))


if __name__ == "__main__":
    a = sys.argv[1:]
    fn = {"planA": planA, "runA": runA, "analyzeA": analyzeA, "planB": planB, "runB": runB, "analyzeB": analyzeB, "freeze": freeze}
    redesign(a[1]) if a[0] == "redesign" else fn[a[0]]()
