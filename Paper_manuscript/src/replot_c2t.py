"""Regenerate the C2t figures from the saved time series (titles only; no simulation)."""
import os
os.environ["C2_VARIANT"] = "C2t"
import numpy as np
import run_e5_ieee39 as e5, run_e6_ieee39 as e6, run_e7_ieee39 as e7

def split(raw, prefixes):
    return {p: {k[len(p) + 1:]: raw[k] for k in raw.files if k.startswith(p + "_")} for p in prefixes}

raw5 = np.load(e5.RAW_FILE); d5 = split(raw5, ["P+", "Q+"])
e5.plot_frequency(d5); e5.plot_voltage(d5); e5.plot_primary(d5)
raw6 = np.load(e6.RAW_FILE); d6 = {k: raw6[k] for k in raw6.files}
e6.plot_frequency({"data": d6}, raw5); e6.plot_voltage({"data": d6}, raw5); e6.plot_secondary({"data": d6})
raw7 = np.load(e7.RAW_FILE); d7 = split(raw7, ["S0", "P+", "Q+"])
runs = {k: {"data": v, "system": None} for k, v in d7.items()}
e7.plot_frequency(runs); e7.plot_voltage(runs); e7.plot_secondary(runs["P+"])
print("replotted")
