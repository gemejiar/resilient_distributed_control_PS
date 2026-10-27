"""DEC-050 block A: single prolonged simulation (2000 s) of B2 on C2t_Vsafe_R35_040 under Q+ (dynamic simulation 1 of 12).

Why this run (declared before running).  E13 gives closed-loop slowest time constants of 540-650 s and E10 gives, for Q+, a residual Qset drift of 8.7e-3 pu / 20 s: drift x tau ~ 0.24 pu of
setpoint displacement is still to come at t = 200 s, which a 200 s horizon cannot show.  With tau = 560 s, 2000 s corresponds to e^{-3.5} ~ 3 % of the initial transient, so the E10 drift
tolerance (1e-3 pu / 20 s) is expected to be met.  The controller is NOT modified: this is the original B2 law on the frozen variant, same event, same plant.
At t = 199, 500, 1000, 1999 s the linearised closed loop (plant + RDC, M), the plant derivative xdot and the RDC rates v0 are stored, so the Newton extrapolation to the closed-loop
equilibrium can be validated against the later part of the same trajectory (post-processing in analyse_dec050_a.py).
Series are thinned (ANDES save_every = 100 steps, command log every 100 steps) to keep memory bounded; nothing else changes.
"""

from __future__ import annotations

import os
import time

os.environ["C2_VARIANT"] = "C2t"
os.environ.setdefault("E9B0_VARIANT", "C2t_Vsafe_R35_040")
os.environ.setdefault("E9B0_DELTA", "0.040")

import numpy as np

import e9h_predictor as PR
import run_b3_ieee39 as b
from e9b_variant import HOOK, VARIANT
from run_e0_ieee39 import ARTIFACTS_DIR as A, git_commit, sha256

assert VARIANT == "C2t_Vsafe_R35_040", VARIANT
HORIZON = float(os.environ.get("D50_HORIZON", "2000"))
SCEN = os.environ.get("D50_SCENARIO", "Q+")
PROBES = sorted(p for p in (199.0, 500.0, 1000.0, HORIZON - 1.0) if p <= HORIZON)
TAG = os.environ.get("D50_TAG", "A_longrun_Qplus")


class MultiProbe:
    def __init__(self):
        self.todo = list(PROBES)
        self.out: dict[str, np.ndarray] = {}
        self.pred = PR.LinearPredictor(None)
        self.next_print = 0.0
        self.wall = time.time()

    def __call__(self, t, sys_, ctx, st, vp, vq):
        if t >= self.next_print:
            print(f"t = {t:7.1f} s  wall {time.time() - self.wall:7.0f} s", flush=True)
            self.next_print += 100.0
        if self.todo and t >= self.todo[0]:
            tp = self.todo.pop(0)
            self.pred.ctx, self.pred.lim = ctx, ctx["lim"]
            p = self.pred.build(sys_, st, vp, vq, float(t), refresh_params=True)
            k = f"t{int(round(tp))}_"
            for key in ("M", "A_plant", "xdot", "v0", "Cz", "y0", "u0"):
                self.out[k + key] = np.asarray(p[key])
            self.out[k + "t_actual"] = np.asarray(float(t))
            print(f"probe at t = {t:.2f} s stored (|v0|_inf = {np.abs(p['v0']).max():.3e})", flush=True)


def hook(system, ctx):
    HOOK(system, ctx)
    system.TDS.config.tf = HORIZON
    system.TDS.config.save_every = 100


def main() -> int:
    pr = MultiProbe()
    _, d, diag = b.run("B2", SCEN, probe=pr, init_hook=hook, log_every=100)
    print("diag", diag, flush=True)
    raw = A / f"IEEE39_DEC050_{TAG}_series.npz"
    np.savez_compressed(raw, **{k: v for k, v in d.items() if isinstance(v, np.ndarray)})
    prb = A / f"IEEE39_DEC050_{TAG}_probes.npz"
    np.savez_compressed(prb, **pr.out)
    print({"series": str(raw), "sha256": sha256(raw), "probes": str(prb), "sha256_probes": sha256(prb), "git": git_commit()}, flush=True)
    return 0 if diag["tds_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
