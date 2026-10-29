"""DEC-059 R5 plan builders (TEST blind evaluation, fair comparison, OC3 demanding case, tau_info check).  NOT executed before the TEST gate (acta IEEE39_DEC059_gate_TEST.json
must be PASS).  Builders only compose run dictionaries with the frozen executor (dec059_tds.execute); they contain no tuning.
  plan_r5a  TEST: OC1/OC2 x buses {21, 31, 39} x {S1, S2, S3} x dispatch {M0, M3OS} x B5'                           (36 TDS)
  plan_r5b  comparison on the S2 TEST cells at the M3OS dispatch: B2, B1s, B4'                                        (18 TDS)
  plan_r5c  OC3 demanding case: M0 x S2 x TEST buses x {B2, B5'}                                                      (6 TDS)
  plan_r5d  tau_info check on one S2 TEST cell (OC1 M3OS): tau_info 0.25 s and 4 s (the declared value, 1 s, is in r5a)  (2 TDS)
Targets of B5' / B4' for every (OC, dispatch, cell): rule E* (dec059_eq target), computed only AFTER the TEST gate, with the frozen rule."""
from __future__ import annotations

import json
import sys

import dec054_common as C54
import dec055_common as C55
import dec059_tds as T

TEST = C55.TEST
SEV = ("S1", "S2", "S3")


def amp(sev):
    return round(C55.oc_amp(sev), 5)


def tag(oc, m, bus=None, sev=None):
    return f"r2_{oc}_{m}_d0" if bus is None else f"r2_{oc}_{m}_b{bus}P_{amp(sev):.5f}"


def run(oc, m, bus, sev, controller, rid, purpose, tau=1.0):
    sc = {"bus": bus, "kind": "P", "amp": amp(sev)}
    r = T.b5_run(oc, sc, rid, purpose, tag(oc, m), tag(oc, m, bus, sev), m=m)
    r["controller"] = controller
    r["b5"]["tau_info"] = tau
    if controller in ("B2", "B1S"):
        r["b5"] = {}
    return r


def meta():
    return {"protocol_sha256": C54.sha_file(C55.ROOT / "ops/sted/DEC059_protocol.md"),
            "gate_TEST_sha256": C54.sha_file(C55.ART / "IEEE39_DEC059_gate_TEST.json"),
            "code_sha256": {f: C54.sha_file(C55.SRC / f) for f in ("dec059_b5.py", "dec059_eq.py", "dec059_tds.py", "dec059_os.py", "dec059_pred.py", "dec059_metrics.py", "dec059_gate.py")}}


def plan_r5a():
    runs = [run(oc, m, b, s, "B5P", f"D59TEST_B5P_{oc}_{m}_b{b}P_{s}", f"R5 TEST: {oc} {m} cell b{b}P_{s} with B5' (frozen), local dt/16; blind (no redesign after the first TEST TDS)")
            for oc in ("OC1", "OC2") for m in ("M0", "M3OS") for b in TEST for s in SEV]
    return {"stage": "DEC-059 lot R5a plan: TEST (sealed after the TEST gate and before any TEST TDS)", "block": "R5", "runs": runs, **meta()}


def plan_r5b():
    runs = [run(oc, "M3OS", b, "S2", c, f"D59CMP_{c}_{oc}_M3OS_b{b}P_S2", f"R5 comparison: {c} on the TEST cell b{b}P_S2 at the {oc} M3+OS dispatch (same event, dispatch, solver, local dt/16)")
            for oc in ("OC1", "OC2") for b in TEST for c in ("B2", "B1S", "B4P")]
    return {"stage": "DEC-059 lot R5b plan: fair comparison on the S2 TEST cells (sealed before its TDS)", "block": "R5", "runs": runs, **meta()}


def plan_r5c():
    runs = [run("OC3", "M0", b, "S2", c, f"D59OC3_{c}_M0_b{b}P_S2", f"R5 OC3 demanding case: {c}, M0, TEST cell b{b}P_S2 (reported with the target labels; not a counter-example when the target is unstable)")
            for b in TEST for c in ("B2", "B5P")]
    return {"stage": "DEC-059 lot R5c plan: OC3 demanding case (sealed before its TDS)", "block": "R5", "runs": runs, **meta()}


def plan_r5d():
    runs = [run("OC1", "M3OS", TEST[0], "S2", "B5P", f"D59TAU_B5P_OC1_M3OS_b{TEST[0]}P_S2_tau{str(t).replace('.', 'p')}", f"R5 tau_info check: tau_info = {t} s on the TEST cell b{TEST[0]}P_S2, OC1 M3+OS", tau=t)
            for t in (0.25, 4.0)]
    return {"stage": "DEC-059 lot R5d plan: tau_info check (sealed before its TDS)", "block": "R5", "runs": runs, **meta()}


PLANS = {"R5A": plan_r5a, "R5B": plan_r5b, "R5C": plan_r5c, "R5D": plan_r5d}


def plan(lot):
    p = PLANS[lot]()
    with open(T.plan_path(lot), "x", encoding="utf-8") as f:
        json.dump(p, f, indent=1)
    print("plan", lot, len(p["runs"]))


if __name__ == "__main__":
    plan(sys.argv[1])
