"""DEC-053 central module: source registry, series loading and the single metric code (post-processing only, no TDS)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "Paper_manuscript" / "artifacts"
FIG = ROOT / "Paper_manuscript" / "figures_main"
UNIT_BUS = [30, 31, 33, 35, 38, 39, 32, 37, 34, 36]
UNIT = ["SG30", "SG31", "SG33", "SG35", "SG38", "SG39", "GFM32", "GFM37", "GFM34", "GFM36"]
VLO, VHI, F0, T_EVENT = 0.95, 1.05, 60.0, 5.0
# events: P+ = +58.564 MW at bus 4, Q+ = +17.345 MVAr at bus 21 (t = 5 s)
EV = {"S0": (None, 0.0, 0.0), "P+": (4, 58.564, 0.0), "Q+": (21, 0.0, 17.345)}

# (key, file, prefix, stage, controller, variant, dispatch, scenario, t_end, committed_in_git)
def _s(key, file, pre, stage, ctl, var, disp, scen, tend):
    return dict(key=key, file=file, pre=pre, stage=stage, controller=ctl, variant=var, dispatch=disp, scenario=scen, t_end=tend)


SOURCES: list[dict] = []
for sc in ("P+", "Q+"):
    SOURCES.append(_s(f"E5t_{sc}", "IEEE39_E5_C2t_timeseries.npz", f"{sc}_", "E5", "B0", "C2t", "C2t", sc, 40.0))
SOURCES.append(_s("E6t_P+", "IEEE39_E6_C2t_timeseries.npz", "", "E6", "B1_P", "C2t", "C2t", "P+", 80.0))
for sc in ("S0", "P+", "Q+"):
    SOURCES.append(_s(f"E7t_{sc}", "IEEE39_E7_C2t_timeseries.npz", f"{sc}_", "E7", "B1_PQ", "C2t", "C2t", sc, 120.0))
    SOURCES.append(_s(f"E8_{sc}", "IEEE39_E8_C2t_timeseries.npz", f"{sc}_", "E8", "B2", "C2t", "C2t", sc, 200.0))
for v in ("Vsafe", "Vsafe_R35", "Vsafe_R35_040"):
    for sc in ("S0", "P+", "Q+"):
        SOURCES.append(_s(f"E9B0_{v}_{sc}", f"IEEE39_E9B0_{v}_series.npz", f"{sc}__", "E9-B0", "B2", f"C2t_{v}", f"C2t_{v}", sc, 200.0))
for sc in ("S0", "P+", "Q+"):
    SOURCES.append(_s(f"B2QV1_{sc}", "IEEE39_DEC050_B_B2QV1_series.npz", f"{sc}__", "DEC050-B", "B2_QV1", "C2t_Vsafe_R35_040", "C2t_Vsafe_R35_040", sc, 200.0))
    SOURCES.append(_s(f"B3_{sc}", f"IEEE39_B3_C2t_{'Pplus' if sc == 'P+' else 'Qplus' if sc == 'Q+' else 'S0'}_timeseries.npz", "B3_", "B3", "B3", "C2t", "C2t", sc, 200.0))
SOURCES.append(_s("DEC050A_Q+", "IEEE39_DEC050_A_longrun_Qplus_series.npz", "", "DEC050-A", "B2", "C2t_Vsafe_R35_040", "C2t_Vsafe_R35_040", "Q+", 2000.0))
KEY = {s["key"]: s for s in SOURCES}


def sha(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load(key: str) -> dict:
    s = KEY[key]
    z = np.load(ART / s["file"], allow_pickle=True)
    pre = s["pre"]
    g = lambda n: z[pre + n] if pre + n in z.files else None
    d = {"t": g("time_s"), "V": g("bus_voltage_pu"), "f": g("bus_frequency_hz"), "fsg": g("sg_frequency_hz")}
    d["P"] = np.hstack([g("sg_p_pu"), g("gfm_p_pu")])
    d["Q"] = np.hstack([g("sg_q_pu"), g("gfm_q_pu")])
    d["bus_ids"] = g("bus_ids") if g("bus_ids") is not None else np.arange(1, 40)
    for n in ("cmd_t", "cmd_pset", "cmd_qset"):
        d[n] = g(n)
    for n in ("pn", "qn", "pmax", "pmin", "qmax", "qmin", "smax"):
        d["u_" + n] = g("unit_" + n)
    if d["u_pmax"] is None:
        d["u_pmax"] = z["P+_unit_pmax"] if "P+_unit_pmax" in z.files else (z["S0_unit_pmax"] if "S0_unit_pmax" in z.files else None)
    d["meta"] = s
    return d


def _fill_limits(d: dict, ref: dict) -> None:
    for n in ("pn", "qn", "pmax", "pmin", "qmax", "qmin", "smax"):
        if d.get("u_" + n) is None:
            d["u_" + n] = ref["u_" + n]


def limits() -> dict:
    """Unit limits from the E8 original-RDC series (system-base pu)."""
    z = np.load(ART / "IEEE39_E8_C2t_timeseries.npz")
    return {n: z["P+_unit_" + n] for n in ("pn", "qn", "pmax", "pmin", "qmax", "qmin", "smax")}


def _runs(mask: np.ndarray):
    """Return total duration-count of True samples (callers multiply by dt)."""
    return int(mask.sum())


def indicators(d: dict, lim: dict, t_end: float | None = None, scen: str = "P+") -> dict:
    """Single code path for the H2/H3/physical indicators over [0, t_end]."""
    t = d["t"]
    t_end = t[-1] if t_end is None else t_end
    m = t <= t_end + 1e-9
    t = t[m]
    dt = float(np.median(np.diff(t)))
    post = t >= T_EVENT
    fm = d["f"][m].mean(axis=1)  # unweighted mean of the 39 ANDES BusFreq signals (Hz)
    fsg = d["fsg"][m].mean(axis=1) if d["fsg"] is not None else None
    out = {"window_s": float(t_end), "dt_s": dt, "n_samples": int(m.sum())}
    out["f_mean_pre_Hz"] = float(fm[t < T_EVENT].mean())
    out["f_nadir_Hz"] = float(fm[post].min())
    out["f_zenith_Hz"] = float(fm[post].max())
    k = max(int(round(0.1 / dt)), 1)  # 0.1 s moving average before differencing (documented)
    fs = np.convolve(fm, np.ones(k) / k, mode="same")
    ro = np.gradient(fs, t)
    out["rocof_max_Hz_s"] = float(np.abs(ro[post][k:-k]).max())
    out["rocof_raw_max_Hz_s"] = float(np.abs(np.gradient(fm, t)[post]).max())
    wf = t >= t_end - 5.0
    out["f_final_error_Hz"] = float(fm[wf].mean() - F0)  # not rounded to zero
    out["f_final_error_window_s"] = 5.0
    out["f_sg_final_error_Hz"] = float(fsg[wf].mean() - F0) if fsg is not None else None
    dev = np.abs(fm - F0)
    ok = dev < 2e-3
    last_bad = np.where(~ok & post)[0]
    if last_bad.size == 0:
        out["f_settling_2mHz_s"] = 0.0
    elif last_bad[-1] >= len(t) - 1:
        out["f_settling_2mHz_s"] = "NOT_OBSERVED_WITHIN_HORIZON"
    else:
        out["f_settling_2mHz_s"] = float(t[last_bad[-1] + 1] - T_EVENT)
    V = d["V"][m]
    out["V_min_pu"], out["V_max_pu"] = float(V.min()), float(V.max())
    outside = (V < VLO) | (V > VHI)
    out["t_outside_band_s_any_bus"] = float(outside.any(axis=1).sum() * dt)
    out["n_buses_outside_band"] = int(outside.any(axis=0).sum())
    ub = [list(d["bus_ids"]).index(b) for b in UNIT_BUS]
    vf = V[wf]
    out["V_err_vs_1pu_mean_abs_unitbus_final"] = float(np.abs(vf[:, ub].mean(axis=0) - 1.0).mean())
    out["V_err_vs_1pu_max_abs_unitbus_final"] = float(np.abs(vf[:, ub].mean(axis=0) - 1.0).max())
    out["V_err_vs_1pu_mean_abs_39bus_final"] = float(np.abs(vf.mean(axis=0) - 1.0).mean())
    out["V_err_vs_1pu_max_abs_39bus_final"] = float(np.abs(vf.mean(axis=0) - 1.0).max())
    P, Q = d["P"][m], d["Q"][m]
    S = np.hypot(P, Q)
    mg = {"Pmax": lim["pmax"] - P, "Pmin": P - lim["pmin"], "Qmax": lim["qmax"] - Q, "Qmin": Q - lim["qmin"], "Smax": lim["smax"] - S}
    for nm, a in mg.items():
        a = a[post]
        out[f"min_margin_{nm}_pu"] = float(a.min())
        j = np.unravel_index(a.argmin(), a.shape)
        out[f"min_margin_{nm}_unit"] = UNIT[j[1]]
        out[f"min_margin_{nm}_t_s"] = float(t[post][j[0]])
        out[f"t_violation_{nm}_s"] = float((a < 0).any(axis=1).sum() * dt)
    pn, qr = lim["pn"], lim["qmax"] - lim["qmin"]
    out["P_share_spread_final"] = float(np.ptp(P[wf].mean(axis=0) / pn))  # physical P / Pn (weights d_P = 1/Pn)
    out["Q_share_spread_final"] = float(np.ptp(Q[wf].mean(axis=0) / qr))  # physical Q / (Qmax-Qmin)
    if d["cmd_pset"] is not None:
        ct = d["cmd_t"]
        cm = ct <= t_end + 1e-9
        wc = ct[cm] >= t_end - 5.0
        ps = d["cmd_pset"][cm][wc].mean(axis=0)
        qs = d["cmd_qset"][cm][wc].mean(axis=0)
        out["Pset_share_spread_final"] = float(np.ptp(ps / pn))
        out["Qset_share_spread_final"] = float(np.ptp(qs / qr))
        qd = np.gradient(d["cmd_qset"][cm], ct[cm], axis=0)
        wl = ct[cm] >= t_end - 20.0
        out["Qset_max_rate_last20s_pu_s"] = float(np.abs(qd[wl]).max())
    return out
