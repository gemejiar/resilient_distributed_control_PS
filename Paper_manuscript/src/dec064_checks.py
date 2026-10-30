"""DEC-064 consistency checks between theory, implementation and stored results (read-only; no TDS).
 (1) Proposition OS class membership: maximum reference displacement of each controller over [t_e, t_e + 50 ms] against T * vbar_k (vbar_k = 0.01 * smax_k pu/s).
 (2) Mechanism of the K7 nadir difference: total active-power reference displacement sum_i (P*_i(t) - P*_i(t_e)) of B2, B1s, B4', B5' at fixed times after the event and the time of the f_COI nadir.
 (3) T2 consistency: after the last solver call of B5' the loop is on the fast path (v = v_nom, CLF row satisfied) for the rest of the run.
Writes IEEE39_DEC064_checks.json exclusively with 'write'."""
from __future__ import annotations

import json
import sys

import numpy as np

import dec055_common as C55
import dec059_eq as EQ
import dec059_tds as T

TE = 5.0
CELLS = [("OC1", "M3REV3", "b21P_S2"), ("OC1", "M3REV3", "b31P_S2"), ("OC1", "M3REV3", "b39P_S2"), ("OC2", "M3OS", "b21P_S2"), ("OC2", "M3OS", "b31P_S2"), ("OC2", "M3OS", "b39P_S2")]
CTL = {"B5P": "D62TEST_B5P_", "B4P": "D62CMP_B4P_", "B2": "D62CMP_B2_", "B1S": "D62CMP_B1S_"}


def main(write=False):
    out = {"label": "DEC064_CONSISTENCY_CHECKS_NO_TDS", "OS": {}, "mechanism": {}, "T2_fast_path_after_window": {}}
    for oc, d, cell in CELLS:
        e = EQ.Eq(oc, T.dispatch_z(oc, d))
        rs = EQ.refset(e.ctx, e.st)
        vbar = rs["vbar"]
        key = f"{oc}_{d}_{cell}"
        out["OS"][key], out["mechanism"][key] = {}, {}
        for c, pre in CTL.items():
            z = np.load(T.RUNS / f"{pre}{oc}_{d}_{cell}" / "series.npz", allow_pickle=True)
            t = z["cmd_t"]
            u = np.hstack([z["cmd_pset"], z["cmd_qset"]])
            i0 = int(np.searchsorted(t, TE - 1e-9))
            k = (t >= TE) & (t <= TE + 0.05)
            disp = np.abs(u[k] - u[i0][None, :]).max(axis=0)
            ratio = disp / (0.05 * vbar)
            out["OS"][key][c] = {"max_ratio_displacement_over_T_vbar": float(ratio.max()), "argmax_component": int(ratio.argmax())}
            P = z["cmd_pset"]
            tot = {f"{dt}s": float((P[int(np.searchsorted(t, TE + dt))] - P[i0]).sum()) for dt in (1, 2, 4, 8, 15)}
            f = z["f_coi_hz"]
            tt = z["t"]
            n = min(len(f), len(tt))
            msk = tt[:n] >= TE
            tm, fm = tt[:n][msk], f[:n][msk]
            out["mechanism"][key][c] = {"sum_dP_ref": tot, "nadir_hz": float(fm.min()), "t_nadir_s_after_event": float(tm[int(fm.argmin())] - TE)}
    for r in sorted(p.name for p in T.RUNS.iterdir() if p.name.startswith("D62TEST_B5P_")):
        z = np.load(T.RUNS / r / "series.npz", allow_pickle=True)
        pa, tp = z["b5_path"], z["b5_t"]
        last = tp[pa == 1].max()
        after = pa[tp > last]
        out["T2_fast_path_after_window"][r] = {"t_last_solver": float(last), "n_after": int(len(after)), "all_fast": bool((after == 0).all())}
    out["T2_all_fast_after_window"] = all(v["all_fast"] for v in out["T2_fast_path_after_window"].values())
    out["OS_max_ratio_by_controller"] = {c: max(out["OS"][k][c]["max_ratio_displacement_over_T_vbar"] for k in out["OS"]) for c in CTL}
    print(json.dumps({k: out[k] for k in ("OS_max_ratio_by_controller", "T2_all_fast_after_window")}, indent=1))
    for key, v in out["mechanism"].items():
        print(key, {c: (round(x["sum_dP_ref"]["2s"], 4), round(x["sum_dP_ref"]["8s"], 4), round(x["sum_dP_ref"]["15s"], 4), round(x["nadir_hz"], 4), round(x["t_nadir_s_after_event"], 2)) for c, x in v.items()})
    if write:
        with open(C55.ART / "IEEE39_DEC064_checks.json", "x", encoding="utf-8") as f:
            json.dump(out, f, indent=1, default=float)


if __name__ == "__main__":
    main("write" in sys.argv)
