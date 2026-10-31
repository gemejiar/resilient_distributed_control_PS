"""DEC-066 closure: observed metrics of the runs of one lot (F2/F3/F4) with the same post-processing as dec066_abl_obs.row, plus the pre-event headroom of the limiting unit and the observed excursion
(headroom - margin).  Run: <venv python> dec066_obs2.py <LOT> [write]  -> artifacts/IEEE39_DEC066_T5_<LOT>_observed.csv (exclusive)"""
from __future__ import annotations

import csv
import sys

import numpy as np

import dec054_common as C54
import dec055_common as C55
import dec055_oc as OCM
import dec066_abl_obs as O
import dec066_tds as D66

TE = C54.EVENT_T


def main(lot, write=False):
    lim = OCM.make_plant("OC1").limits
    pmax = np.asarray(lim["pmax"], float)
    rows = []
    for p in sorted(D66.RUNS.iterdir()):
        if not p.name.startswith(f"D66{lot}_") or not (p / "series.npz").exists():
            continue
        r = O.row(p.name, lim)
        z = np.load(p / "series.npz", allow_pickle=True)
        t, P = z["t"], z["P"]
        pre = P[np.searchsorted(t, TE - 1e-9) - 1]            # last sample before the event
        j = C55.UNITS.index(r["unit_0_50ms"])
        r["pre_headroom_limiting_unit"] = float(pmax[j] - pre[j])
        r["excursion_observed_0_50ms"] = r["pre_headroom_limiting_unit"] - r["mPmax_0_50ms"]
        r["pre_headroom_min_all_units"] = float((pmax - pre).min())
        rows.append(r)
    for r in rows:
        print(r["run_id"], r["class"], round(r["mPmax_0_50ms"], 5), r["unit_0_50ms"], round(1e3 * r["t_0_50ms_s"], 2), "ms  pre-headroom", round(r["pre_headroom_limiting_unit"], 5), "excursion", round(r["excursion_observed_0_50ms"], 5),
              "w50ms-10s", round(r["mPmax_50ms_10s"], 4), "fnadir", round(r["f_nadir_hz"], 4), "Vmin", round(r["V_bus_min"], 4), "dur_ms", round(1e3 * r["duration_below_limit_s_approx"], 2))
    if write and rows:
        with open(C55.ART / f"IEEE39_DEC066_T5_{lot}_observed.csv", "x", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    main(sys.argv[1], "write" in sys.argv)
