"""DEC-062 TEST cohorts (protocol ops/sted/DEC062_protocol.md sections 6-7).  Builders only compose run dictionaries with the frozen executor (dec059_tds.execute); no tuning.
Must not run before the access acta IEEE39_DEC062_gate_TEST_access.json exists and the tag dec062-freeze is set.
  targets            prints the (oc, dispatch, bus, amp) list of E* targets needed (computed with the frozen rule by dec059_eq.py after the freeze)
  plan A | B         A: OC1/OC2 x TEST buses x {S1,S2,S3} x {M0, M3+OS} with B5P (36).  B: S2 TEST cells at the M3+OS dispatch with B2, B1S, B4P (18)
Dispatch labels: M0 and the frozen preventive design of each OC (OC1: M3REV3, OC2: M3OS)."""
from __future__ import annotations

import json
import sys

import dec054_common as C54
import dec055_common as C55
import dec059_tds as T

TEST = C55.TEST
SEV = ("S1", "S2", "S3")
DES = {"OC1": "M3REV3", "OC2": "M3OS"}


def amp(sev):
    return round(C55.oc_amp(sev), 5)


def tag(oc, m, bus=None, sev=None):
    return f"r2_{oc}_{m}_d0" if bus is None else f"r2_{oc}_{m}_b{bus}P_{amp(sev):.5f}"


def run(oc, m, bus, sev, controller, rid, purpose):
    r = T.b5_run(oc, {"bus": bus, "kind": "P", "amp": amp(sev)}, rid, purpose, tag(oc, m), tag(oc, m, bus, sev), m=m)
    r["controller"] = controller
    if controller in ("B2", "B1S"):
        r["b5"] = {}
    return r


def target_list():
    return [(oc, m, b, amp(s)) for oc in ("OC1", "OC2") for m in ("M0", DES[oc]) for b in TEST for s in SEV]


def meta():
    return {"protocol_sha256": C54.sha_file(C55.ROOT / "ops/sted/DEC062_protocol.md"), "access_acta_sha256": C54.sha_file(C55.ART / "IEEE39_DEC062_gate_TEST_access.json"),
            "design_sha256": {"OC1": C54.sha_file(T.ST59 / "m3os_rev3_OC1.json"), "OC2": C54.sha_file(T.ST59 / "m3os_OC2.json")},
            "code_sha256": {f: C54.sha_file(C55.SRC / f) for f in ("dec059_b5.py", "dec059_eq.py", "dec059_tds.py", "dec059_os.py", "dec059_pred.py", "dec059_metrics.py", "dec062_r5.py", "dec062_test.py")}}


def plan_a():
    runs = [run(oc, m, b, s, "B5P", f"D62TEST_B5P_{oc}_{m}_b{b}P_{s}", f"DEC-062 cohort A (blind TEST): {oc} {m} cell b{b}P_{s} with B5P (frozen), local dt/16; no redesign after the first TEST TDS")
            for oc in ("OC1", "OC2") for m in ("M0", DES[oc]) for b in TEST for s in SEV]
    return {"stage": "DEC-062 cohort A plan: blind TEST (sealed after the freeze and the predictions, before any TEST TDS)", "block": "R5", "runs": runs, **meta()}


def plan_b():
    runs = [run(oc, DES[oc], b, "S2", c, f"D62CMP_{c}_{oc}_{DES[oc]}_b{b}P_S2", f"DEC-062 cohort B (comparison): {c} on the TEST cell b{b}P_S2 at the {oc} {DES[oc]} dispatch (same event, dispatch, solver, local dt/16)")
            for oc in ("OC1", "OC2") for b in TEST for c in ("B2", "B1S", "B4P")]
    return {"stage": "DEC-062 cohort B plan: fair comparison on the S2 TEST cells (sealed before its TDS)", "block": "R5", "runs": runs, **meta()}


def plan(lot):
    p = {"A": plan_a, "B": plan_b}[lot]()
    with open(T.plan_path("R5" + lot), "x", encoding="utf-8") as f:
        json.dump(p, f, indent=1)
    print("plan", "R5" + lot, len(p["runs"]))


if __name__ == "__main__":
    if sys.argv[1] == "targets":
        for t in target_list():
            print(*t)
    else:
        plan(sys.argv[2])
