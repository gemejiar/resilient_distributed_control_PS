"""DEC-051 block A (contingency simulation 1 of 2, reproducibility/integrity): re-run of the DEC-050 2000 s B2 Q+ trajectory on C2t_Vsafe_R35_040 with the sole purpose of storing the FULL
ANDES state (all x, all y, load and actuator parameters, RDC state) at t = 1999 s, which DEC-050 did not store.  The controller, plant, event and horizon are those of run_dec050_a_longrun.py;
the series and command logs are thinned exactly as there.  The stored reference vector is compared with the DEC-050 probe u0 (reproducibility check)."""

from __future__ import annotations

import os

os.environ["C2_VARIANT"] = "C2t"
os.environ.setdefault("E9B0_VARIANT", "C2t_Vsafe_R35_040")
os.environ.setdefault("E9B0_DELTA", "0.040")

import numpy as np

import run_b3_ieee39 as b
from e9b_variant import HOOK, VARIANT
from run_e0_ieee39 import ARTIFACTS_DIR as A, git_commit, sha256

assert VARIANT == "C2t_Vsafe_R35_040", VARIANT
HORIZON, T_DUMP = 2000.0, 1999.0
PQ_PARAMS = ("p0", "q0", "Ppf", "Qpf")


class Dump:
    def __init__(self):
        self.out = {}
        self.done = False

    def __call__(self, t, sys_, ctx, st, vp, vq):
        if self.done or t < T_DUMP:
            return
        self.done = True
        o = self.out
        o["t"] = np.asarray(float(t))
        o["x"], o["y"] = np.array(sys_.dae.x, float), np.array(sys_.dae.y, float)
        for name in PQ_PARAMS:
            o["PQ_" + name] = np.array(getattr(sys_.PQ, name).v, float)
        o["TGOV1N_paux0"], o["IEEEX1_vref0"] = np.array(sys_.TGOV1N.paux0.v, float), np.array(sys_.IEEEX1.vref0.v, float)
        o["REGF1_Paux0"], o["REGF1_Qaux0"] = np.array(sys_.REGF1.Paux0.v, float), np.array(sys_.REGF1.Qaux0.v, float)
        for k in ("pset", "qset", "pn", "qn", "y0", "y0q", "vref0_sg", "d_p", "d_q"):
            o["st_" + k] = np.array(st[k], float)
        for k in ("gref_p", "gref_q", "k_ip"):
            o["st_" + k] = np.asarray(float(st[k]))
        o["vnom_p"], o["vnom_q"] = np.array(vp, float), np.array(vq, float)
        np.savez_compressed(A / "IEEE39_DEC051_state_t1999.npz", **o)   # saved immediately: nothing after this point can lose it
        print(f"state dumped at t = {t:.3f} s, max|v_nom| = {max(np.abs(vp).max(), np.abs(vq).max()):.3e}", flush=True)


def hook(system, ctx):
    HOOK(system, ctx)
    system.TDS.config.tf = HORIZON
    system.TDS.config.save_every = 1000


def main() -> int:
    dump = Dump()
    _, d, diag = b.run("B2", "Q+", probe=dump, init_hook=hook, log_every=1000)
    print("diag", diag, flush=True)
    pr = np.load(A / "IEEE39_DEC050_A_longrun_Qplus_probes.npz")
    u_ref = pr["t1999_u0"]
    u_new = np.concatenate([dump.out["st_pset"], dump.out["st_qset"]])
    dump.out["reproducibility_max_abs_u_diff_vs_DEC050"] = np.asarray(float(np.abs(u_new - u_ref).max()))
    p = A / "IEEE39_DEC051_state_t1999.npz"
    np.savez_compressed(p, **dump.out)
    print({"file": str(p), "sha256": sha256(p), "u_diff": float(dump.out["reproducibility_max_abs_u_diff_vs_DEC050"]), "git": git_commit()}, flush=True)
    return 0 if diag["tds_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
