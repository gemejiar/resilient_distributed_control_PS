"""E9-H predictor validation: error bound of the nominal prediction, cost and coverage (declared protocol, DEC-047).

Protocol (declared before running).  B2 (original RDC, no filter) is replayed on C2t_Vsafe_R35_040 for S0, P+ and Q+ over 60 s.  From t = 5.5 s (0.5 s after the event: the filter is never
active during the initial unsafe interval, nor claims anything about unknown future steps) a supervisory update is performed every Ts = 0.1 s with exactly the machinery of the filter
(linearization with parameter derivatives refreshed every 1 s and cached in between, closed-loop RDC prediction over H = 3 s on a 0.1 s grid).  Every 1 s the 3 s prediction (Delta v = 0) is stored and,
after the run, compared with the actual B2 trajectory on the solver grid (3.906 ms), the predicted curve being interpolated linearly between grid points (this includes the between-sample
behaviour).  Windows containing the event are excluded.  The bound is eps_j(tau_k) = FACTOR x the maximum observed absolute error of output j in the tau-bin k over all windows of the three
scenarios (cumulative maximum over k); it is an EMPIRICAL bound, not a mathematically derived one.
Requirements for continuing (declared): cost, mean update <= 0.5 s (offline, Python; no real-time claim); usefulness, in S0 the nominal predicted margins exceed eps for every enforceable barrier
(zero action feasible); coverage in the closed-loop test, at least 99 % of the (window, output, tau) samples within eps.
"""
from __future__ import annotations

import json
import os
import sys
import time

os.environ["C2_VARIANT"] = "C2t"

import numpy as np

import e9h_predictor as PR
import run_b3_ieee39 as b
from e9b_variant import HOOK, TAG, VARIANT
from run_e0_ieee39 import ARTIFACTS_DIR, git_commit, sha256

OUT = ARTIFACTS_DIR / f"IEEE39_E9H_error_bounds{TAG}.json"
NPZ = ARTIFACTS_DIR / f"IEEE39_E9H_error_bounds{TAG}.npz"
FACTOR = 1.5
UPDATE = 0.1
T_START = 5.5
HORIZON_RUN = 60.0
STORE_EVERY = 10          # every 1.0 s
REFRESH_EVERY = 10        # parameter derivatives refreshed every 1.0 s


class PredProbe:
    def __init__(self):
        self.pred = PR.LinearPredictor(None)
        self.next, self.i, self.windows, self.timing = T_START, 0, [], []
        self.ready = False

    def __call__(self, t, sys_, ctx, st, vp, vq):
        if t < self.next - 1e-9:
            return
        if not self.ready:
            self.pred.ctx, self.pred.lim = ctx, ctx["lim"]
            self.ready = True
        t0 = time.perf_counter()
        p = self.pred.build(sys_, st, vp, vq, float(t), refresh_params=(self.i % REFRESH_EVERY == 0))
        wall = time.perf_counter() - t0
        self.timing.append({"t": float(t), "wall": wall, **p["timing"]})
        if self.i % STORE_EVERY == 0 and t + PR.HORIZON <= HORIZON_RUN:
            self.windows.append({"t0": float(t), "Y": p["Y"].copy()})
        self.i += 1
        self.next += UPDATE


def actual_series(d):
    p = np.hstack([d["sg_p_pu"], d["gfm_p_pu"]])
    q = np.hstack([d["sg_q_pu"], d["gfm_q_pu"]])
    return d["time_s"], np.hstack([p, q, d["bus_voltage_pu"]])


def main():
    names = sys.argv[1:] or ["S0", "P+", "Q+"]
    Emax = np.zeros((PR.K + 1, 59))
    allerr = {k: [] for k in range(1, PR.K + 1)}
    per_sc, timing_all = {}, []
    for sc in names:
        pr = PredProbe()

        def hook(system, ctx):
            HOOK(system, ctx)
            system.TDS.config.tf = HORIZON_RUN

        _, data, diag = b.run("B2", sc, probe=pr, init_hook=hook)
        t, Y = actual_series(data)
        e_sc = np.zeros((PR.K + 1, 59))
        n_w = 0
        for w in pr.windows:
            t0 = w["t0"]
            sel = (t > t0 + 1e-9) & (t <= t0 + PR.HORIZON + 1e-9)
            tau = t[sel] - t0
            grid = np.arange(PR.K + 1) * PR.DT
            pred = np.stack([np.interp(tau, grid, w["Y"][:, j]) for j in range(59)], axis=1)
            err = np.abs(Y[sel] - pred)
            kbin = np.clip(np.ceil(tau / PR.DT - 1e-9).astype(int), 1, PR.K)
            for k in range(1, PR.K + 1):
                m = kbin == k
                if m.any():
                    e_sc[k] = np.maximum(e_sc[k], err[m].max(axis=0))
                    allerr[k].append(err[m].max(axis=0))
            n_w += 1
        Emax = np.maximum(Emax, e_sc)
        tm = {k: float(np.mean([x[k] for x in pr.timing])) for k in ("wall", "linearize", "rdc_fd", "assemble_expm", "propagate")}
        per_sc[sc] = {"n_windows": n_w, "n_updates": len(pr.timing), "timing_mean_s": tm, "wall_max_s": float(max(x["wall"] for x in pr.timing)), "max_error_P": float(e_sc[:, :10].max()),
                      "max_error_Q": float(e_sc[:, 10:20].max()), "max_error_V": float(e_sc[:, 20:].max()), "diag": diag}
        timing_all += pr.timing
        print(sc, per_sc[sc], flush=True)
    cum = np.maximum.accumulate(Emax, axis=0)
    eps = FACTOR * cum
    q99 = np.zeros((PR.K + 1, 59))
    for k in range(1, PR.K + 1):
        if allerr[k]:
            q99[k] = np.percentile(np.stack(allerr[k]), 99, axis=0)
    np.savez_compressed(NPZ, eps=eps, emax=Emax, q99=q99)
    wall = [x["wall"] for x in timing_all]
    res = {"variant": VARIANT, "git_commit": git_commit(), "factor": FACTOR, "update_s": UPDATE, "horizon_s": PR.HORIZON, "dt_s": PR.DT, "t_start_s": T_START, "doc": __doc__,
           "per_scenario": per_sc,
           "bound_summary": {"P_units_max_over_k_pu": float(eps[:, :10].max()), "Q_units_max_pu": float(eps[:, 10:20].max()), "V_buses_max_pu": float(eps[:, 20:].max()),
                             "P_at_tau_0.1": float(eps[1, :10].max()), "P_at_tau_1": float(eps[10, :10].max()), "P_at_tau_3": float(eps[30, :10].max()), "V_at_tau_3": float(eps[30, 20:].max())},
           "cost": {"mean_update_wall_s": float(np.mean(wall)), "p95_update_wall_s": float(np.percentile(wall, 95)), "max_update_wall_s": float(max(wall)),
                    "requirement_mean_le_0.5s": bool(np.mean(wall) <= 0.5), "control_update_Ts_s": UPDATE},
           "npz": NPZ.name, "npz_sha256": sha256(NPZ)}
    OUT.write_text(json.dumps(res, indent=2, default=float), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("bound_summary", "cost")}, indent=1))


if __name__ == "__main__":
    main()
