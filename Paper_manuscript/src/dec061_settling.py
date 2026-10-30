"""DEC-061 D4 (criterion iv, 1e-3 pu at 200 s kept): where does the residual unit-voltage error come from, and which B5' parameters can change it?  No TDS: stored DESIGN/TUNE runs only
(16 TUNE + 8 recheck, OC1/OC2, dispatches M3OS and M3CUT).  For every run: max|V_unit - V*| at 200 s, its late-window decay rate (150-200 s) against the target's slowest closed-loop mode
(H5 rightmost eigenvalue), the fraction of QP (non-fast-path) calls in the last 100 s, and the CLF rate lambda against 2*sigma_slow.
  <venv python> dec061_settling.py [write]"""
from __future__ import annotations

import glob
import json
import sys

import numpy as np

import dec054_common as C54
import dec055_common as C55
import dec059_tds as T


def one(run):
    d = T.RUNS / run
    z = np.load(d / "series.npz", allow_pickle=True)
    cfg = json.loads((d / "config.json").read_text(encoding="utf-8"))
    tg = dict(np.load(cfg["b5"]["post_target"]))
    tj = json.loads(open(str(cfg["b5"]["post_target"]).replace(".npz", ".json"), encoding="utf-8").read())
    t = z["t"]
    vu = z["V"][:, [b - 1 for b in C54.UNIT_BUS]]
    e = np.abs(vu - tg["V"][None, :]).max(axis=1)
    k = (t >= 150) & (t <= 200)
    sl = float(np.polyfit(t[k], np.log(np.maximum(e[k], 1e-12)), 1)[0])
    sig = -tj["T2"]["H5_continuous"]["rightmost_excl_null"][0][0]
    bt, bp = z["b5_t"], z["b5_path"]
    late = bt >= 100
    i5 = int(np.argmin(np.abs(t - (C54.EVENT_T + 1.0))))
    tail_valid = e[(t >= 200 - 2)]
    return {"run": run, "err_200s": float(tail_valid.mean()), "err_at_te_plus_1s": float(e[i5]), "err_at_50s": float(e[np.argmin(np.abs(t - 50))]), "late_decay_rate": -sl, "sigma_slow_H5": float(sig),
            "ratio_rate_over_sigma": float(-sl / sig), "qp_call_fraction_last_100s": float((bp[late] != 0).mean()) if late.any() else None, "clf_lambda": float(tg["lam"]),
            "two_sigma": float(2 * sig), "clf_lambda_over_two_sigma": float(tg["lam"] / (2 * sig)),
            "err_200_if_sigma_were_x1.5": float(e[np.argmin(np.abs(t - 150))] * np.exp(-1.5 * sig * 50))}


def main(write=False):
    runs = sorted(p.name for p in T.RUNS.iterdir() if p.name.startswith(("D59TUNE_B5P", "D60RCK_B5P")))
    rows = [one(r) for r in runs]
    out = {"stage": "DEC-061 D4 settling analysis (no TDS)", "rows": rows,
           "summary": {"n": len(rows), "late_rate_over_sigma_range": [min(r["ratio_rate_over_sigma"] for r in rows), max(r["ratio_rate_over_sigma"] for r in rows)],
                       "qp_fraction_last_100s_max": max(r["qp_call_fraction_last_100s"] or 0 for r in rows), "clf_lambda_over_two_sigma_max": max(r["clf_lambda_over_two_sigma"] for r in rows),
                       "n_err_200_above_1e-3": int(sum(r["err_200s"] > 1e-3 for r in rows))}}
    for r in rows:
        print(r["run"][-34:], "e200 %.2e" % r["err_200s"], "e(te+1) %.1e" % r["err_at_te_plus_1s"], "rate/sigma %.2f" % r["ratio_rate_over_sigma"], "qp_late %.3f" % (r["qp_call_fraction_last_100s"] or 0), "lam/2s %.1e" % r["clf_lambda_over_two_sigma"])
    print(out["summary"])
    if write:
        with open(C55.ART / "IEEE39_DEC061_settling_analysis.json", "x", encoding="utf-8") as f:
            json.dump(out, f, indent=1, default=float)


if __name__ == "__main__":
    main("write" in sys.argv)
