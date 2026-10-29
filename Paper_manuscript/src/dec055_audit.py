"""DEC-055 L0 static audits (no TDS).
    buses          audit of the TEST buses 21, 31, 39: loads per OC, load model, disturbance mechanism, interaction with SG31 and with the Slack, sensitivities
                   (from the T-A stage), and every previous exposure found in the repository (TDS events, algebraic screenings, selection rules, tuning)
    independence   DESIGN/TUNE/TEST independence: disjoint buses and events, provenance (hashes) of every input of the provisional designs
Writes IEEE39_DEC055_test_bus_audit.json and IEEE39_DEC055_independence_audit.json exclusively."""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import numpy as np

import dec054_common as C54
import dec055_common as C

ART = C.ART
TEST = set(C.TEST)


def _walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _walk(v, f"{path}/{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _walk(v, f"{path}[{i}]")
    else:
        yield path, o


def scan_json_exposures():
    """Every JSON value in the artefacts whose key mentions an event/disturbance bus and equals 21, 31 or 39."""
    hits = []
    key_re = re.compile(r"(event_bus|bus_of_disturbance|disturb|selected_bus|candidate|scenario_bus|/bus$)", re.I)
    for f in sorted(ART.glob("*.json")):
        if f.name.startswith("IEEE39_DEC055_"):
            continue
        try:
            o = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for p, v in _walk(o):
            if key_re.search(p) and isinstance(v, (int, float, str)) and str(v).strip() in {"21", "31", "39"}:
                hits.append({"file": f.name, "path": p, "bus": int(str(v).strip())})
    return hits


def scan_csv_exposures():
    hits = []
    for f in sorted(ART.glob("*.csv")):
        if f.name.startswith("IEEE39_DEC055_"):
            continue
        try:
            rows = list(csv.DictReader(open(f, encoding="utf-8")))
        except Exception:
            continue
        for i, r in enumerate(rows):
            for k, v in r.items():
                if k and re.search(r"(bus_of_disturbance|event_bus|^bus$|scenario)", k, re.I) and str(v).strip() in {"21", "31", "39"}:
                    hits.append({"file": f.name, "row": i, "column": k, "bus": int(str(v).strip()), "context": {kk: r[kk] for kk in list(r)[:5]}})
    return hits


def historical_tds_events():
    """Disturbances applied in TDS in earlier stages, from the scenario definitions in code and the DEC-054 ledger (authoritative sources)."""
    import os
    os.environ.setdefault("C2_VARIANT", "C2t")
    ev = []
    import run_e7_ieee39 as e7
    for name, spec in e7.SCENARIOS.items():
        if "p_mw" in spec:
            ev.append({"source": "run_e7_ieee39.SCENARIOS (E5-E16, B3, E9, DEC-050..053 runners)", "scenario": name, "bus": 4, "kind": "P"})
        if "q_mvar" in spec:
            ev.append({"source": "run_e7_ieee39.SCENARIOS (E5-E16, B3, E9, DEC-050..053 runners)", "scenario": name, "bus": 21, "kind": "Q"})
    for r in csv.DictReader(open(ART / "IEEE39_DEC054_tds_ledger.csv", encoding="utf-8")):
        if r["status"] == "REQUESTED":
            m = re.search(r"b(?:us)?(\d+)([PQ])", r["scenario"])
            if m:
                ev.append({"source": "IEEE39_DEC054_tds_ledger.csv", "scenario": r["scenario"], "bus": int(m.group(1)), "kind": m.group(2)})
    for f in ("IEEE39_DEC051_H3_sim1.json", "IEEE39_DEC051_H3_sim2.json"):
        p = ART / f
        if p.exists():
            o = json.loads(p.read_text(encoding="utf-8"))
            b = o.get("bus") or o.get("event_bus") or (o.get("scenario") or {}).get("bus")
            ev.append({"source": f, "scenario": str(o.get("scenario", ""))[:60], "bus": b, "kind": "P"})
    return ev


def stage_buses():
    import pandas as pd
    out = {"stage": "DEC-055 L0 TEST-bus audit (static)", "test_buses": C.TEST, "buses": {}}
    tds = historical_tds_events()
    jh, ch = scan_json_exposures(), scan_csv_exposures()
    for b in C.TEST:
        loads = {}
        for oc, d in C.OC.items():
            pq = pd.read_excel(d["case"], sheet_name="PQ")
            r = pq[pq.bus == b].iloc[0]
            loads[oc] = {"p0_pu": float(r.p0), "q0_pu": float(r.q0), "pf": float(r.p0 / np.hypot(r.p0, r.q0))}
        pv = pd.read_excel(C.BASE_CASE, sheet_name="PV")
        sl = pd.read_excel(C.BASE_CASE, sheet_name="Slack")
        gen_here = [f"PV idx {int(i)}" for i in pv[pv.bus == b].idx] + [f"Slack idx {int(i)}" for i in sl[sl.bus == b].idx]
        p_tds = [e for e in tds if e["bus"] == b and e["kind"] == "P"]
        q_tds = [e for e in tds if e["bus"] == b and e["kind"] == "Q"]
        screen = sorted({h["file"] for h in jh + ch if h["bus"] == b})
        if p_tds:
            status = "CONTAMINATED"
        elif q_tds or screen:
            status = "EXPOSED_NOT_P_TDS"
        else:
            status = "CLEAN"
        out["buses"][b] = {"loads": loads, "units_at_bus": gen_here, "load_model": "constant power in PFlow and TDS (PQ.config p2p=q2q=1, p2z=q2z=0, run_e8_ieee39.configure)",
                           "disturbance_mechanism": "P step added to PQ.Ppf of the existing load at t_e (dist_fn before the step 4.99609375 -> 5.0 s, dec054_runner.execute_tds); no new load device, no topology change",
                           "previous_P_TDS": p_tds, "previous_Q_TDS": q_tds, "algebraic_or_selection_exposure_files": screen, "status": status}
    out["buses"][31]["interaction"] = ("terminal bus of SG31 (the unit whose case Pmax binds in every earlier campaign): the load step is delivered mostly by SG31 through the algebraic jump; "
                                      "DEC-052 location scan dP_jump_SG31 = 0.316 pu for 0.586 pu (54 %); a very strong test of the SG31 limit")
    out["buses"][39]["interaction"] = ("terminal bus of SG39 = PFlow Slack and the large-inertia equivalent (M = 100 s on 1199 MVA); in TDS SG39 is an ordinary GENROU (the Slack exists only in PFlow); "
                                      "DEC-052 location scan dP_jump_SG31 = 0.0005 pu: the step is taken almost entirely by SG39 itself, a weak test of SG31/SG35 limits")
    out["buses"][21]["interaction"] = ("load bus between generator groups; used for all earlier Q steps (+17.345 MVAr) including the realisation and gain choice of the RDC Q channel (DEC-032/DEC-034 E8 attempts)")
    out["exposure_hits"] = {"json": [h for h in jh if h["bus"] in TEST], "csv": [h for h in ch if h["bus"] in TEST]}
    out["note"] = ("DEC-051 H3-2 screened all 19 PQ buses algebraically (static PF and post-jump) and applied a selection rule (bus 18 selected); DEC-052 repeated the scan "
                   "(IEEE39_DEC052_H3_location_scan.csv). The TEST buses were therefore exposed to algebraic screening and to a selection rule, never to a P-step TDS.")
    ta = Path(C.STATE / "ta_OC1_M0.json")
    if ta.exists():
        t = json.loads(ta.read_text(encoding="utf-8"))
        for b in C.TEST:
            r = t["cells"].get(f"TEST_b{b}_S2", {}).get("M0", {})
            if r.get("dP"):
                amp = C.oc_amp("S2")
                dP = np.array(r["dP"])
                out["buses"][b]["sensitivity_OC1_M0_S2"] = {"dPjump_per_pu": dict(zip(C.UNITS, (dP / amp).round(5).tolist())), "dPjump_SG31_share": float(dP[1] / amp),
                                                            "dPjump_SG35_share": float(dP[3] / amp), "V_plus_min": r.get("V_plus_min"), "V_plus_max": r.get("V_plus_max")}
    with open(ART / "IEEE39_DEC055_test_bus_audit.json", "x", encoding="utf-8") as f:
        json.dump(out, f, indent=1, default=float)
    print(json.dumps({b: out["buses"][b]["status"] for b in C.TEST}))


def stage_independence():
    D, T, X = set(C.DESIGN), set(C.TUNE), set(C.TEST)
    chk = {"design_tune_disjoint": not (D & T), "design_test_disjoint": not (D & X), "tune_test_disjoint": not (T & X),
           "test_not_in_seen_set": not (X & set(C.SEEN_NOT_TEST)), "test_not_in_dec054_partitions": not (X & (set(C54.DESIGN) | set(C54.TUNE) | set(C54.TEST)))}
    inputs = {}
    for name in ("IEEE39_DEC054_p3a_analysis.json", "IEEE39_DEC054_p3b_round1_analysis.json", "IEEE39_DEC054_p3a_plan.json", "IEEE39_DEC054_p3b_round1_plan.json"):
        p = ART / name
        o = json.loads(p.read_text(encoding="utf-8"))
        buses = sorted({int(t["bus"]) for t in o.get("tests", [])}) if "tests" in o else None
        txt = p.read_text(encoding="utf-8")
        inputs[name] = {"sha256": C54.sha_file(p), "event_buses_in_plan": buses, "mentions_test_bus_as_event": bool(re.search(r'"bus":\s*(21|31|39)\b', txt))}
    chk["eps_sources_free_of_test_buses"] = not any(v["mentions_test_bus_as_event"] for v in inputs.values())
    params = {k: C54.PROPOSED[k] for k in ("p_scale_pu", "cap_margin_pu", "v_margin_pu", "kappa", "eps_floor_pu")}
    out = {"stage": "DEC-055 L0 independence audit", "checks": chk, "eps_and_cut_inputs": inputs,
           "design_parameters": {"values": params, "provenance": "DEC-054 (set from DEC-054 DESIGN/TUNE pilots, frozen in IEEE39_DEC054_design_frozen.json); no TEST bus involved"},
           "selection_rules": {"TEST": "PQ buses with an existing load never stepped in P in a TDS (rule fixed before any DEC-055 computation); no dynamic result at 21/31/39 used",
                               "location_criteria": "jump sensitivity, post-jump voltage change: computed at OC1 with the M0 dispatch (static) and used only to document coverage"},
           "dec054_reuse": "DEC-054 P3-A/P3-B/P3-C data enter only as TUNE-OC1 calibration (eps); the DEC-054 cohort is not TEST evidence",
           "exposures_declared": "TEST buses were screened algebraically by DEC-051/052 (static PF, post-jump) and bus 21 was used for Q steps (incl. RDC Q-channel realisation, DEC-032/034): see IEEE39_DEC055_test_bus_audit.json",
           "pass": all(chk.values())}
    with open(ART / "IEEE39_DEC055_independence_audit.json", "x", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(chk))


if __name__ == "__main__":
    {"buses": stage_buses, "independence": stage_independence}[sys.argv[1]]()
