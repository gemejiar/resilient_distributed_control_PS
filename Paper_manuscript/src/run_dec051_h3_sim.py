"""DEC-051 block C5: the two independent H3 validation simulations (dynamic simulations H3-1 and H3-2 of the budget), original B2 controller, C2t_Vsafe_R35_040, 200 s, no filter.

H3-1: P+ of 64.4204 MW (110 % of the nominal event) at bus 4, historical Alter mechanism (scenario spec p_mw).
H3-2: P step of 58.564 MW at the bus selected analytically in IEEE39_DEC051_H3_predictions.json (written before this script), applied at t = 5 s through the dist_fn hook (the Alter event of run_e8 is wired to bus 4 only).
Predictions are read from the predictions file and compared after the run; nothing is tuned.  Environment variable H3_RUN = 1 or 2."""

from __future__ import annotations

import json
import os

os.environ["C2_VARIANT"] = "C2t"
os.environ.setdefault("E9B0_VARIANT", "C2t_Vsafe_R35_040")
os.environ.setdefault("E9B0_DELTA", "0.040")

import numpy as np

import run_b3_ieee39 as b
import run_e8_ieee39 as e8
from e9b_variant import HOOK, VARIANT
from run_e0_ieee39 import ARTIFACTS_DIR as A, git_commit, sha256

assert VARIANT == "C2t_Vsafe_R35_040", VARIANT
RUN = int(os.environ.get("H3_RUN", "1"))
NAMES = ["SG30", "SG31", "SG33", "SG35", "SG38", "SG39", "GFM32", "GFM37", "GFM34", "GFM36"]


def main() -> int:
    pred = json.loads((A / "IEEE39_DEC051_H3_predictions.json").read_text(encoding="utf-8"))
    kw = {}
    if RUN == 1:
        e8.SCENARIOS["P+x1.1"] = {"p_mw": 64.4204}
        scen, p = "P+x1.1", pred["H3_1"]
    else:
        p = pred["H3_2"]
        bus, amp = int(p["bus"]), p["amplitude_MW"] / 100.0
        state = {"done": False}

        def step(t, s):
            if not state["done"] and t >= 5.0:
                k = [int(x) for x in s.PQ.bus.v].index(bus)
                s.PQ.Ppf.v[k] += amp
                state["done"] = True
        kw["dist_fn"] = step
        scen = "S0"
    system, d, diag = b.run("B2", scen, init_hook=HOOK, **kw)
    lim = {k: d[f"unit_{k}"] for k in ("pmax", "pmin", "qmax", "qmin", "smax")}
    t = d["time_s"]
    P = np.hstack([d["sg_p_pu"], d["gfm_p_pu"]]); Q = np.hstack([d["sg_q_pu"], d["gfm_q_pu"]]); vb = d["bus_voltage_pu"]
    post = t > 5.0 + 1e-9
    pk = P[post].max(axis=0)
    s_rel = lim["smax"] - np.hypot(P, Q)
    viol = {NAMES[i]: [k for k, v in (("P+", P[:, i].max() > lim["pmax"][i]), ("P-", P[:, i].min() < lim["pmin"][i]), ("Q+", Q[:, i].max() > lim["qmax"][i]), ("Q-", Q[:, i].min() < lim["qmin"][i]), ("S", s_rel[:, i].min() < 0)) if v] for i in range(10)}
    viol = {k: v for k, v in viol.items() if v}
    f = d["bus_frequency_hz"].mean(axis=1)
    res = {"stage": f"DEC-051 H3-{RUN}", "git_commit": git_commit(), "diag": diag, "event": p["event"], "predicted_margin_to_pmax_pu": p["predicted_margin_to_pmax_pu"], "predicted_violating_units": p["predicted_violating_units"],
           "observed_peak_P_pu": pk.tolist(), "observed_margin_to_pmax_pu": (lim["pmax"] - pk).tolist(), "observed_t_of_peak_s": [float(t[post][np.argmax(P[post][:, i])]) for i in range(10)],
           "prediction_error_margin_pu": ((lim["pmax"] - pk) - np.array(p["predicted_margin_to_pmax_pu"])).tolist(), "observed_units_crossing_limits": viol,
           "min_margin_Qmax_pu": float((lim["qmax"] - Q).min()), "min_margin_Qmin_pu": float((Q - lim["qmin"]).min()), "min_margin_S_pu": float(s_rel.min()),
           "bus_voltage_min_max_pu": [float(vb.min()), float(vb.max())], "n_buses_outside_0.95_1.05": int(((vb < 0.95) | (vb > 1.05)).any(axis=0).sum()), "n_buses_below_0.95": int((vb < 0.95).any(axis=0).sum()),
           "frequency_nadir_hz": float(f[post].min()), "frequency_final_error_hz": float(f[t >= t[-1] - 10].mean() - 60.0), "first_sample_after_event_P_pu": P[post][0].tolist(), "t_first_sample_s": float(t[post][0])}
    raw = A / f"IEEE39_DEC051_H3_sim{RUN}_series.npz"
    np.savez_compressed(raw, time_s=t, P=P, Q=Q, bus_voltage_pu=vb, f_hz=f)
    res["series_sha256"] = sha256(raw)
    (A / f"IEEE39_DEC051_H3_sim{RUN}.json").write_text(json.dumps(res, indent=2, default=float), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("event", "predicted_violating_units", "observed_units_crossing_limits", "bus_voltage_min_max_pu", "n_buses_below_0.95")}, default=float))
    print("observed margin SG31/SG35", [round(res["observed_margin_to_pmax_pu"][i], 4) for i in (1, 3)], "predicted", [round(res["predicted_margin_to_pmax_pu"][i], 4) for i in (1, 3)], "max |pred err|", round(float(np.abs(res["prediction_error_margin_pu"]).max()), 4))
    return 0 if diag["tds_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
