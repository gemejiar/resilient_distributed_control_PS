"""E9-B0 variant hooks: C2t_Vsafe (B3-A d = 0 AC solution as initial condition) and the incremental preventive redispatch derived from it.

The redispatch moves delta pu of active power from the violating unit (SG35) to the GFM, split in proportion to each GFM's minimum transient P margin
under B2 in P+ from C2t_Vsafe (IEEE39_E9B0_variant.json, i.e. the reserve actually available), by modifying PV p0 before the power flow exactly as the
Vsafe hook does.  The case file, the ratings, the gains, the graph, the actuator maps and the perturbations are untouched.
"""

from __future__ import annotations

import json
import os

import numpy as np

from run_e0_ieee39 import ARTIFACTS_DIR
from run_e9a_hocbf import vsafe_hook

VARIANT = os.environ.get("E9B0_VARIANT", "C2t_Vsafe")
DELTA = float(os.environ.get("E9B0_DELTA", "0"))
SOURCE_BUS = int(os.environ.get("E9B0_SOURCE_BUS", "35"))
RECEIVERS = (32, 37, 34, 36)
TAG = "" if VARIANT == "C2t_Vsafe" else "_" + VARIANT.replace("C2t_Vsafe_", "")


def receiver_weights() -> dict[int, float]:
    d = json.loads((ARTIFACTS_DIR / "IEEE39_E9B0_variant.json").read_text(encoding="utf-8"))["scenarios"]["P+"]["per_unit"]
    h = {b: max(d[f"GFM{b}"]["min_P_margin_to_pmax_pu"], 0.0) for b in RECEIVERS}
    tot = sum(h.values())
    return {b: v / tot for b, v in h.items()}


def hook_for(delta: float):
    def hook(system, ctx):
        vsafe_hook(system, ctx)
        if delta > 0:
            w = receiver_weights()
            pv = {int(b): k for k, b in enumerate(system.PV.bus.v)}
            system.PV.p0.v[pv[SOURCE_BUS]] -= delta
            for bus, wt in w.items():
                system.PV.p0.v[pv[bus]] += delta * wt
    return hook


HOOK = hook_for(DELTA)
