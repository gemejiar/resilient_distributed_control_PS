"""DEC-066 closure TDS (lots F2 = equal-effort confirmation, F3 = out-of-design validation, F4 = fixed fine-step check).  Wrapper over the DEC-066 ablation executor (dec066_tds), which in turn reuses
dec059_tds.execute / b5_run unchanged; nothing of the electrical models, ANDES or controller B5' is modified.  Differences with dec066_tds:
  * designs EQ1 and DQ1 (backups/DEC066_state/bud_*_OC1.json) are added to the design table;
  * new lots F2/F3/F4 are charged to the same ledger IEEE39_DEC066_tds_ledger.csv; the DEC-066 total of 40 TDS is unchanged (budget reassignment: the unused quota of E1 (3), E3 (12) and E4 (4) is
    reassigned to F2 (4), F3 (5), F4 (4) and F5 (1); the ledger refuses any request beyond 40 in total);
  * spec items accept a suffix  "/fix<n>"  for a fixed step dt/n over the whole run (refine = None, tf = FIXTF), and the existing "/n" for dt/n with the local refinement kept.
Commands:  target <V> <bus> <SEV|d0>  |  plan <LOT> <spec>  (reads predictions from artifacts/IEEE39_DEC066_<LOT>_pred.json)  |  run <LOT>"""
from __future__ import annotations

import json
import os
import sys

import dec054_common as C54
import dec055_common as C55
import dec059_tds as T
import dec066_abl_analysis as AA
import dec066_tds as D66

D66.BUDGET.update({"F2": 4, "F3": 5, "F4": 4, "F5": 1})
AA.SRC.update({"EQ1": C54.RUNS_DIR.parent / "DEC066_state" / "bud_EQ1_OC1.json", "DQ1": C54.RUNS_DIR.parent / "DEC066_state" / "bud_DQ1_OC1.json"})
D66.NAME.update({"EQ1": "U only at the effort of D", "DQ1": "dense+eps_OS at the effort of E"})
FIXTF = 20.0


def build(v, bus, sev, lot, mode=None):
    if mode is None:
        return D66.build(v, bus, sev, lot)
    if mode.startswith("fix"):
        n = int(mode[3:])
        r = D66.build(v, bus, sev, lot)
        r["refine"] = None
        r["time_step_s"] = C54.DT / n
        r["tf"] = FIXTF
        r["run_id"] += f"_fix{n}"
        r["purpose"] += f"; fixed step dt/{n} over [0,{FIXTF:g}] s, no local refinement"
        return r
    return D66.build(v, bus, sev, lot, int(mode))


def plan(lot, spec):
    preds = json.loads((C55.ART / f"IEEE39_DEC066_{lot}_pred.json").read_text(encoding="utf-8"))
    runs = []
    for item in spec.split(";"):
        b, s, vs = item.split(":")
        for v in vs.split(","):
            mode = None
            if "/" in v:
                v, mode = v.split("/")
            runs.append(build(v, b, s, lot, mode))
    p = {"stage": f"DEC-066 closure lot {lot} (sealed with hypotheses and predictions before any TDS of the lot)", "block": lot, "runs": runs, "predictions": preds,
         "designs_sha256": {v: C54.sha_file(AA.SRC[v]) for v in AA.SRC},
         "code_sha256": {f: C54.sha_file(C55.SRC / f) for f in ("dec059_b5.py", "dec059_tds.py", "dec059_eq.py", "dec066_tds.py", "dec066_tds2.py", "dec066_abl_analysis.py")},
         "backup": "DEC-066 procedural exception: independent backup waived by the investigator (same-disk copy only); see ops/sted/DEC066_protocol.md Addendum C"}
    with open(C55.ART / f"IEEE39_DEC066_{lot}_plan.json", "x", encoding="utf-8") as f:
        json.dump(p, f, indent=1)
    print("plan", lot, len(runs))


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "target":
        D66.target(*sys.argv[2:5])
    elif c == "plan":
        plan(sys.argv[2], sys.argv[3])
    elif c == "run":
        D66.run_many(sys.argv[2], int(os.environ.get("DEC066_WORKERS", "4")))
