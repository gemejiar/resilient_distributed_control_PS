"""E9-F: validation of the nonlinear Lie-derivative engine at free-flow states (references frozen): engine vs frozen Jacobian vs ANDES free-flow truth."""
from __future__ import annotations

import json
import os
import sys
import time

os.environ["C2_VARIANT"] = "C2t"

import numpy as np

import e9a_hocbf as H
import e9a_linear as L
import e9f_engine as E
import run_b3_ieee39 as b
import run_e9c_lie_validation as V
from e9b_variant import HOOK
from run_e0_ieee39 import ARTIFACTS_DIR


class Probe:
    def __init__(self, t0):
        self.t0, self.done, self.rec = t0, False, {}

    def __call__(self, t, sys_, ctx, st, vp, vq):
        if self.done or t < self.t0:
            return
        self.done = True
        lin = L.linearize(sys_, ctx)
        eng = E.Engine(sys_, ctx, st, lin, t_now=float(t))
        eng.sg_rates = False
        if float(os.environ.get("E9F_PROJECT_FAST", "0")):
            self.rec["projection"] = eng.project_fast(float(os.environ["E9F_PROJECT_FAST"]))
            lin = lin
        x0 = eng.xt0()
        y, fd = eng.solve(x0)
        self.rec["base_solve_max_y_diff"] = float(np.abs(y - eng.y_base).max())
        self.rec["base_solve_xdot_diff_vs_linearize"] = float(np.abs(fd - lin["xdot"]).max())
        self.rec["newton_residual"] = eng.last_residual
        t1 = time.perf_counter()
        d1 = eng.jets(3, 3.0e-4)
        self.rec["jets_time_s"] = time.perf_counter() - t1
        self.rec["n_solves"] = eng.n_solves
        d2 = eng.jets(3, 6.0e-4)
        self.rec["D"], self.rec["D_eps2"] = d1, d2
        rs = eng.rs
        idx = np.concatenate([rs["P"], rs["Q"], rs["Vbus"]])
        a_z, b_v, c_z = L.augmented(lin, idx)
        zdot = np.concatenate([fd2 if False else lin["xdot"], np.zeros(20)])
        pred = np.zeros((4, len(idx))); cur = zdot.copy()
        for k in range(1, 4):
            pred[k] = c_z @ cur; cur = a_z @ cur
        self.rec["frozen"] = pred
        self.rec["t0_actual"] = float(t)
        eng.close()


def main():
    plan = [(a.split(":")[0], float(a.split(":")[1])) for a in sys.argv[1:]] or [("S0", 30.0), ("P+", 7.72)]
    out = {}
    for sc, t0 in plan:
        pr = Probe(t0)
        data, diag = V.run_free(sc, t0, probe=pr)
        r = pr.rec
        t = data["time_s"]
        p, q, vb = V.series_pqv(data)
        Y = np.hstack([p, q, vb])
        truth = {deg: V.poly_derivs(t, Y, r["t0_actual"], deg) for deg in (5, 6, 7)}
        tr = truth[6]
        unc = np.abs(truth[5] - truth[7])
        D, D2, F = r["D"], r["D_eps2"], r["frozen"]
        rec = {"base_solve_max_y_diff": r["base_solve_max_y_diff"], "base_xdot_diff": r["base_solve_xdot_diff_vs_linearize"], "newton_residual": r["newton_residual"],
               "jets_time_s": r["jets_time_s"], "n_solves": r["n_solves"]}
        for k in (1, 2, 3):
            scale = np.maximum(np.abs(tr[k]), 1e-3 * np.abs(tr[k]).max() + 1e-12)
            rec[f"order_{k}"] = {"engine_vs_truth_median_rel": float(np.median(np.abs(D[k] - tr[k]) / scale)), "frozen_vs_truth_median_rel": float(np.median(np.abs(F[k] - tr[k]) / scale)),
                                 "engine_vs_frozen_median_rel": float(np.median(np.abs(D[k] - F[k]) / scale)), "engine_eps_consistency_median_rel": float(np.median(np.abs(D[k] - D2[k]) / scale)),
                                 "engine_vs_truth_max_abs": float(np.abs(D[k] - tr[k]).max()), "frozen_vs_truth_max_abs": float(np.abs(F[k] - tr[k]).max()), "truth_abs_max": float(np.abs(tr[k]).max()),
                                 "truth_fit_uncertainty_median": float(np.median(unc[k])), "engine_eps_consistency_max_abs": float(np.abs(D[k] - D2[k]).max())}
        out[f"{sc}@{t0}"] = rec
        print(sc, t0, json.dumps(rec, indent=1))
    (ARTIFACTS_DIR / os.environ.get("E9F_TEST_OUT", "tmp_engine_test.json")).write_text(json.dumps(out, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
