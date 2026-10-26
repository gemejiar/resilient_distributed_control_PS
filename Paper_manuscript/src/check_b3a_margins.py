"""Static margin check of the B3-A equilibria on physical powers and on effective references (DEC-039, condition 2).

Reads the v2 equilibrium file; no simulation.  Margins are reported in pu (100 MVA) and as a fraction of each range
(P: pmax - pmin, Q: qmax - qmin) so that units with different capability are comparable.  The B3-A selection imposed a
1 % interior margin on the physical P*, Q* (not on the effective references); this check reports where the effective
references fall relative to that same margin.
"""

from __future__ import annotations

import json
import os

os.environ["C2_VARIANT"] = "C2t"

import numpy as np

import run_e8_ieee39 as e8
import select_equilibrium_b3 as b3
from run_e0_ieee39 import ARTIFACTS_DIR

V2 = ARTIFACTS_DIR / "IEEE39_B3A_C2t_equilibrium_v2.json"
OUT = ARTIFACTS_DIR / "IEEE39_B3A_C2t_margin_check.json"


def main() -> int:
    d = json.loads(V2.read_text(encoding="utf-8"))
    lim = b3.unit_limits(b3.load_plant())
    names = [("SG" if i < d["n_sg"] else "GFM") + str(b) for i, b in enumerate(d["unit_bus_order"])]
    rp, rq = lim["pmax"] - lim["pmin"], lim["qmax"] - lim["qmin"]
    out: dict = {"definition": "margin fractions use the case ranges; B3-A selection margin EPS = 0.01 on physical P*, Q*", "scenarios": {}}
    for sc in ("S0", "P+", "Q+"):
        e = d["scenarios"][sc]
        layers = {"physical": (np.array(e["P_star"]), np.array(e["Q_star"])), "effective_reference": (np.array(e["Pset_eff"]), np.array(e["Qset_eff"]))}
        res = {}
        for layer, (p, q) in layers.items():
            res[layer] = {
                "P_to_pmax_pu": (lim["pmax"] - p).tolist(), "P_to_pmax_fraction_of_range": ((lim["pmax"] - p) / rp).tolist(),
                "Q_to_qmax_fraction_of_range": ((lim["qmax"] - q) / rq).tolist(), "Q_to_qmin_fraction_of_range": ((q - lim["qmin"]) / rq).tolist(),
                "S_rel_margin": (1 - np.hypot(p, q) / lim["smax"]).tolist()}
            frac = np.minimum.reduce([(lim["pmax"] - p) / rp, (p - lim["pmin"]) / rp, (lim["qmax"] - q) / rq, (q - lim["qmin"]) / rq])
            res[layer]["tightest_fraction_per_unit"] = frac.tolist()
            res[layer]["tightest_unit"] = names[int(np.argmin(frac))]
            res[layer]["tightest_fraction"] = float(frac.min())
            res[layer]["units_below_EPS_1pct"] = [n for n, f in zip(names, frac) if f < b3.EPS]
        out["scenarios"][sc] = res
        print(sc, {k: (v["tightest_unit"], round(v["tightest_fraction"], 4), v["units_below_EPS_1pct"]) for k, v in res.items()})
    sg35 = names.index("SG35")
    out["SG35_note"] = {sc: {"P*_margin_pu": out["scenarios"][sc]["physical"]["P_to_pmax_pu"][sg35],
                             "Pset_eff_margin_pu": out["scenarios"][sc]["effective_reference"]["P_to_pmax_pu"][sg35],
                             "Pset_eff_margin_fraction": out["scenarios"][sc]["effective_reference"]["P_to_pmax_fraction_of_range"][sg35]}
                        for sc in ("S0", "P+", "Q+")}
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out["SG35_note"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
