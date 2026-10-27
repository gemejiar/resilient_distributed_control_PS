"""E9-A test C: the frozen linear model against the nonlinear ANDES step responses of run_e9a_sg31 (P31 to each unit step in Pset).

Linear model at the pre-event equilibrium (z = (xd, Pset, Qset), unit step on one reference at t = 0) versus the nonlinear difference run
(event + step minus event alone, same simulation as in the SG31 authority audit).  Differences are expected to be small but not zero: the
nonlinear runs are linearized around the post-event trajectory, the linear model around the pre-event equilibrium.
"""

from __future__ import annotations

import json
import os

os.environ["C2_VARIANT"] = "C2t"

import numpy as np
from scipy.linalg import expm

import e9a_hocbf as H
import e9a_linear as L
import run_e8_ieee39 as e8
from run_e0_ieee39 import ARTIFACTS_DIR, git_commit

OUT = ARTIFACTS_DIR / "IEEE39_E9A_linear_validation.json"
TAUS = (0.15, 0.5, 1.0, 2.0, 2.7, 5.0)


def main() -> int:
    system, ctx = e8.configure("S0", e8.TIME_STEP_S)
    system.PFlow.run()
    system.TDS.init()
    lin = L.linearize(system, ctx)
    rs = H.rows_of(system, ctx)
    names = [("SG" if i < ctx["n_sg"] else "GFM") + str(b) for i, b in enumerate(ctx["unit_bus"])]
    i31 = names.index("SG31")
    a_z, b_v, c_z = L.augmented(lin, rs["P"][[i31]])
    nl = json.loads((ARTIFACTS_DIR / "IEEE39_E9A_sg31_authority.json").read_text(encoding="utf-8"))["channel_step_response"]
    out = {"git_commit": git_commit(), "taus_s": list(TAUS), "channels": {}}
    # unit step on the reference state z_ref(j) = 1 at t = 0: z(0) = e_j, v = 0
    n_z = a_z.shape[0]
    for ch, lab in ((1, "Pset_SG31"), (3, "Pset_SG35"), (6, "Pset_GFM32"), (0, "Pset_SG30"), (11, "Qset_SG31")):
        z0 = np.zeros(n_z); z0[n_z - 20 + ch] = 1.0
        row = {}
        for tau in TAUS:
            lin_val = float((c_z @ expm(a_z * tau) @ z0)[0])
            nl_val = nl[lab]["dP31_per_unit_step"][str(tau)]
            row[str(tau)] = {"linear": lin_val, "nonlinear": nl_val, "abs_diff": abs(lin_val - nl_val)}
        out["channels"][lab] = row
        print(lab, {k: (round(v["linear"], 3), round(v["nonlinear"], 3)) for k, v in row.items()})
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
