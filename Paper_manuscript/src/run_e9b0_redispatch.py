"""E9-B0 step 3: minimal incremental redispatch that removes the SG35 limit violation of B2 / P+ from C2t_Vsafe (DEC-044).

delta (pu) moves from SG35 to the GFM (32, 37, 34, 36) in proportion to their available transient P margin (e9b_variant).  The violation excess of every unit
(P above pmax, P below pmin, Q outside [qmin, qmax], S above Sn) is evaluated with B2 (original RDC, no QP) in P+ over the first 30 s, where all transient excursions
occur; bisection gives the smallest delta with zero excess, and the frozen delta is that value rounded UP to the next multiple of 0.005 pu (declared before running).
The frozen variant is then validated over the full 200 s in S0, P+ and Q+ by run_e9b0_variant (E9B0_VARIANT=C2t_Vsafe_R35, E9B0_DELTA=frozen value).
"""

from __future__ import annotations

import json
import math
import os

os.environ["C2_VARIANT"] = "C2t"

import numpy as np

import run_b3_ieee39 as b
import run_e8_ieee39 as e8
from e9b_variant import hook_for, receiver_weights
from run_e0_ieee39 import ARTIFACTS_DIR, git_commit
from run_e9b0_variant import margins

OUT = ARTIFACTS_DIR / "IEEE39_E9B0_redispatch_search.json"
HORIZON = 30.0
ROUND = 0.005


def excess(delta: float, scenario: str = "P+") -> dict:
    base = hook_for(delta)

    def hook(system, ctx):
        base(system, ctx)
        system.TDS.config.tf = HORIZON

    _, data, diag = b.run("B2", scenario, init_hook=hook)
    lim = e8.configure("S0", e8.TIME_STEP_S)[1]["lim"]
    names = [("SG" if i < 6 else "GFM") + str(bb) for i, bb in enumerate(data["unit_bus_ids"])]
    m = margins(data, lim, names)
    worst = {n: max(r["P_violation_pu"], r["P_below_pmin_pu"], r["Q_violation_pu"], r["S_violation_pu"]) for n, r in m["per_unit"].items()}
    return {"delta": delta, "tds_ok": diag["tds_ok"], "max_excess_pu": max(worst.values()), "violating": {n: v for n, v in worst.items() if v > 0},
            "min_P_margin_pu": {n: r["min_P_margin_to_pmax_pu"] for n, r in m["per_unit"].items()}}


def main() -> int:
    log = []
    lo, hi = 0.0, 0.06
    e_lo, e_hi = excess(lo), excess(hi)
    log += [e_lo, e_hi]
    print("delta 0:", e_lo["violating"], "delta 0.06:", e_hi["violating"], flush=True)
    assert e_lo["max_excess_pu"] > 0 and e_hi["max_excess_pu"] == 0, "bracket does not enclose the threshold"
    for _ in range(11):
        mid = 0.5 * (lo + hi)
        r = excess(mid)
        log.append(r)
        print(f"delta {mid:.5f}: excess {r['max_excess_pu']:.5f} {r['violating']}", flush=True)
        if r["max_excess_pu"] > 0:
            lo = mid
        else:
            hi = mid
    frozen = math.ceil(hi / ROUND - 1e-9) * ROUND
    chk = excess(frozen)
    log.append(chk)
    out = {"git_commit": git_commit(), "source_unit": "SG35", "receivers_GFM": receiver_weights(), "scenario_for_search": "B2 / P+", "horizon_s": HORIZON, "bisection_bracket_pu": [lo, hi],
           "delta_min_pu": hi, "rounding_pu": ROUND, "delta_frozen_pu": frozen, "check_at_frozen": chk, "log": log,
           "rule": "frozen delta = delta_min rounded up to the next multiple of 0.005 pu (declared before running); the investigator can replace it"}
    OUT.write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
    print("delta_min", hi, "frozen", frozen, "check", chk["violating"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
