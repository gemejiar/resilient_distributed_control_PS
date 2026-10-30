"""DEC-066: observed metrics of the ablation TDS (T5) from backups/DEC066_runs and comparison with the registered predictions.  Pure post-processing.
Per run: M3V-1 class (dec059_metrics), Pmax/Pmin margins by window (0-50 ms, 50 ms-10 s, 10-195 s), limiting unit and instant, maximum excess and approximate duration below the limit
(sample integration), Q/S/V margins, COI frequency nadir/error, unit-voltage errors, redispatch effort of the controller.
Run: <venv python> dec066_abl_obs.py [write] -> artifacts/IEEE39_DEC066_T5_observed.csv (exclusive) and prints the table."""
from __future__ import annotations

import csv
import json
import sys

import numpy as np

import dec054_common as C54
import dec055_common as C55
import dec055_oc as OCM
import dec059_metrics as M
import dec059_tds as T59
import dec062_test as TS
import dec066_tds as D66

T59.RUNS = D66.RUNS
TE = C54.EVENT_T
UNITS = C55.UNITS


def row(run_id, lim):
    z = np.load(D66.RUNS / run_id / "series.npz", allow_pickle=True)
    t, P = z["t"], z["P"]
    pmax = np.asarray(lim["pmax"], float)
    m = TS.record(run_id, lim, None, "B5P")
    cfg = json.loads((D66.RUNS / run_id / "config.json").read_text(encoding="utf-8"))
    out = {"run_id": run_id, "design": cfg.get("dispatch_label"), "bus": cfg["scenario"]["bus"], "amp": cfg["scenario"]["amp"], "class": m["class"], "reasons": ";".join(map(str, m["reasons"])) if m["reasons"] else ""}
    wins = {"0_50ms": (TE, TE + 0.05), "50ms_10s": (TE + 0.05, TE + 10), "10_195s": (TE + 10, TE + 195), "all": (TE, 200.0)}
    for name, (a, b) in wins.items():
        w = (t >= a - 1e-9) & (t <= b + 1e-9)
        mg = pmax[None, :] - P[w]
        i, j = np.unravel_index(mg.argmin(), mg.shape)
        out[f"mPmax_{name}"] = float(mg.min()); out[f"unit_{name}"] = UNITS[j]; out[f"t_{name}_s"] = float(t[w][i] - TE)
    w = t >= TE - 1e-9
    mg = (pmax[None, :] - P[w])[:, UNITS.index(out["unit_all"])]
    tt = t[w]
    viol = mg < 0
    out["max_excess_pu"] = float(max(-mg.min(), 0.0))
    out["duration_below_limit_s_approx"] = float(np.trapezoid(viol.astype(float), tt)) if viol.any() else 0.0
    out["n_samples_below_limit"] = int(viol.sum())
    out["jump_margin_first_sample"] = float((pmax - P[np.searchsorted(t, TE - 1e-9)]).min())
    out["pmin_margin_min"] = m["margins"]["pmin_margin_min"]; out["qmax_margin_min"] = m["margins"]["qmax_margin_min"]; out["qmin_margin_min"] = m["margins"]["qmin_margin_min"]
    out["s_margin_min"] = m["margins"]["s_margin_min"]; out["V_bus_min"] = m["margins"]["V_bus_min"]; out["V_bus_max"] = m["margins"]["V_bus_max"]
    out["f_nadir_hz"] = m["frequency"]["f_coi_nadir_hz"]; out["f_err_200s_hz"] = m["frequency"]["f_err_200s_hz"]; out["rocof_100ms"] = m["frequency"]["rocof_100ms_hz_s"]
    out["unitV_err_vs_setpoint_max"] = m["voltage"]["unit_V_err_vs_setpoint"]["max"]; out["V_settle_s"] = m["voltage"]["settle_1e-3_s"]
    out["P_total_variation"] = m["effort"]["p_total_variation"]; out["T1_min_c"] = m.get("T1_min_c"); out["QP_fallback"] = m.get("QP_fallback")
    return out


def main(write=False):
    lim = OCM.make_plant("OC1").limits
    runs = sorted(p.name for p in D66.RUNS.iterdir() if (p / "series.npz").exists())
    rows = [row(r, lim) for r in runs]
    for r in rows:
        print({k: (round(v, 5) if isinstance(v, float) else v) for k, v in r.items() if k in ("run_id", "class", "mPmax_0_50ms", "unit_0_50ms", "t_0_50ms_s", "mPmax_50ms_10s", "mPmax_10_195s", "mPmax_all", "unit_all", "t_all_s", "max_excess_pu", "duration_below_limit_s_approx", "f_nadir_hz", "V_bus_min", "V_bus_max")})
    if write and rows:
        with open(C55.ART / "IEEE39_DEC066_T5_observed.csv", "x", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    main("write" in sys.argv)
