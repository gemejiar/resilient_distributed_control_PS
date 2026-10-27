"""E11 (Option B): simultaneous limits and physical redistribution of power.

Part A (no new simulation): on the stored runs (E5t primary control only, E8 original RDC, B3 centered RDC, B2 on C2t_Vsafe_R35_040; P+ and Q+) the normalised margins of the ten units
(P to pmax and pmin over the P range, Q to qmax / qmin over the Q range, relative S margin) are evaluated at every time; a unit is "near a limit" if any margin is below NEAR = 5 % of its range.
Reported: the largest number of units near a limit simultaneously, the duration of the overlaps, the pair of different units with the longest simultaneous proximity, the units that cross a limit,
the redistribution of the delivered active power (final minus pre-event) against the pre-event headroom, and the SG / GFM shares of the event.
Part B (one simulation, B2, frozen variant C2t_Vsafe_R35_040, 100 s): the simultaneous load event P+ and Q+ (58.564 MW at bus 4 and 17.345 MVAr at bus 21 at t = 5 s) forces the
proximity of several limits at once (SG31, SG35 and GFM36 in P+; voltage and Q margins); the run is evaluated with the same metrics.  No optimisation, no tuning.
Documented negative result reused: the simultaneous 100 MW + 50 MVAr screen on C2 (IEEE39_E5_S1screen_C2_...FAIL).
"""

from __future__ import annotations

import csv
import json
import os
from typing import Any

os.environ["C2_VARIANT"] = "C2t"

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import run_b3_ieee39 as b  # noqa: E402
import run_e8_ieee39 as e8  # noqa: E402
from e9b_variant import HOOK  # noqa: E402
from run_e0_ieee39 import ARTIFACTS_DIR as A, FIGURES_DIR, git_commit, sha256  # noqa: E402

EVENT = 5.0
NEAR = 0.05


def limits() -> dict[str, np.ndarray]:
    e = np.load(A / "IEEE39_E8_C2t_timeseries.npz")
    return {k: e[f"P+_unit_{k}"] for k in ("pmax", "pmin", "qmax", "qmin", "smax")}


def evaluate(name: str, d: dict[str, np.ndarray], lim: dict[str, np.ndarray], names: list[str], t0_pre: float = EVENT):
    t = d["time_s"]
    p = np.hstack([d["sg_p_pu"], d["gfm_p_pu"]])
    q = np.hstack([d["sg_q_pu"], d["gfm_q_pu"]])
    rp, rq = lim["pmax"] - lim["pmin"], lim["qmax"] - lim["qmin"]
    m = {"P+": (lim["pmax"] - p) / rp, "P-": (p - lim["pmin"]) / rp, "Q+": (lim["qmax"] - q) / rq, "Q-": (q - lim["qmin"]) / rq, "S": 1 - np.hypot(p, q) / lim["smax"]}
    worst = np.minimum.reduce(list(m.values()))
    near = worst < NEAR
    cross = {n: [k for k, v in m.items() if (v[:, i] < 0).any()] for i, n in enumerate(names) if any((v[:, i] < 0).any() for v in m.values())}
    dt = float(np.median(np.diff(t)))
    count = near.sum(axis=1)
    pair_best, pair_dur = None, 0.0
    for i in range(10):
        for j in range(i + 1, 10):
            dur = float((near[:, i] & near[:, j]).sum() * dt)
            if dur > pair_dur:
                pair_best, pair_dur = (names[i], names[j]), dur
    pre = (t >= t0_pre - 1) & (t < t0_pre)
    fin = t >= t[-1] - 10
    dP = p[fin].mean(axis=0) - p[pre].mean(axis=0)
    head = lim["pmax"] - p[pre].mean(axis=0)
    n_sg = d["sg_p_pu"].shape[1]
    ev = float(dP.sum())
    corr = float(np.corrcoef(dP, head)[0, 1]) if np.std(dP) > 0 else None
    out = {"run": name, "max_units_near_limit_simultaneously": int(count.max()), "time_with_>=2_units_near_s": float((count >= 2).sum() * dt), "time_with_>=3_units_near_s": float((count >= 3).sum() * dt),
           "longest_simultaneous_pair": list(pair_best) if pair_best else None, "longest_simultaneous_pair_duration_s": pair_dur,
           "units_near_limit_at_any_time": [names[i] for i in range(10) if near[:, i].any()], "units_crossing_a_limit": cross,
           "min_normalised_margin_by_unit": {n: float(worst[:, i].min()) for i, n in enumerate(names)}, "delivered_dP_by_unit_pu": {n: float(x) for n, x in zip(names, dP)},
           "delivered_dP_total_pu": ev, "SG_share_of_delivered_dP": float(dP[:n_sg].sum() / ev) if abs(ev) > 1e-9 else None, "GFM_share_of_delivered_dP": float(dP[n_sg:].sum() / ev) if abs(ev) > 1e-9 else None,
           "corr_delivered_dP_vs_pre_event_headroom": corr, "pre_event_headroom_pu": {n: float(x) for n, x in zip(names, head)}, "total_pre_event_headroom_pu": float(head.sum()),
           "bus_voltage_min_pu": float(d["bus_voltage_pu"].min()), "bus_voltage_max_pu": float(d["bus_voltage_pu"].max()), "frequency_nadir_hz": float(d["bus_frequency_hz"].mean(axis=1).min()),
           "frequency_final_error_hz": float(d["bus_frequency_hz"].mean(axis=1)[fin].mean() - 60.0)}
    return out, count, worst, t


def part_a(lim, names):
    out, series = {}, {}
    e5 = np.load(A / "IEEE39_E5_C2t_timeseries.npz")
    e8z = np.load(A / "IEEE39_E8_C2t_timeseries.npz")
    v = np.load(A / "IEEE39_E9B0_Vsafe_R35_040_series.npz")
    for sc in ("P+", "Q+"):
        runs = {f"E5t_primary_only {sc}": {k[len(sc) + 1:]: e5[k] for k in e5.files if k.startswith(sc + "_")},
                f"E8_B2 {sc}": {k[len(sc) + 1:]: e8z[k] for k in e8z.files if k.startswith(sc + "_")},
                f"R35_040_B2 {sc}": {k.split("__", 1)[1]: v[k] for k in v.files if k.startswith(sc + "__")}}
        tag = "Pplus" if sc == "P+" else "Qplus"
        z = np.load(A / f"IEEE39_B3_C2t_{tag}_timeseries.npz")
        runs[f"B3_centered {sc}"] = {k[3:]: z[k] for k in z.files if k.startswith("B3_")}
        for n, d in runs.items():
            r, c, w, t = evaluate(n, d, lim, names)
            out[n] = r
            series[n] = (t, c, w)
    return out, series


def part_b(lim, names):
    e8.SCENARIOS["P+Q+"] = {"p_mw": 58.564, "q_mvar": 17.345}

    def hook(system, ctx):
        HOOK(system, ctx)
        system.TDS.config.tf = 100.0

    _, data, diag = b.run("B2", "P+Q+", init_hook=hook)
    r, c, w, t = evaluate("R35_040_B2 P+Q+ (simultaneous)", data, lim, names)
    r["diag"] = diag
    return {"R35_040_B2 P+Q+ (simultaneous)": r}, (t, c, w)


def main() -> int:
    lim = limits()
    names = ["SG30", "SG31", "SG33", "SG35", "SG38", "SG39", "GFM32", "GFM37", "GFM34", "GFM36"]
    ra, sa = part_a(lim, names)
    rb, sb = part_b(lim, names)
    res = {**ra, **rb}
    ser = {**sa, "R35_040_B2 P+Q+ (simultaneous)": sb}
    s1 = json.loads((A / "IEEE39_E5_S1screen_C2_100MW_50MVAr_FAIL_summary.json").read_text(encoding="utf-8"))
    rows = [{"run": n, "max_units_near": r["max_units_near_limit_simultaneously"], "t_ge2_near_s": r["time_with_>=2_units_near_s"], "t_ge3_near_s": r["time_with_>=3_units_near_s"], "pair": "-".join(r["longest_simultaneous_pair"] or []),
             "pair_duration_s": r["longest_simultaneous_pair_duration_s"], "crossing": ";".join(f"{k}:{'/'.join(v)}" for k, v in r["units_crossing_a_limit"].items()), "dP_total_pu": r["delivered_dP_total_pu"],
             "GFM_share": r["GFM_share_of_delivered_dP"], "corr_dP_headroom": r["corr_delivered_dP_vs_pre_event_headroom"], "Vmin": r["bus_voltage_min_pu"], "Vmax": r["bus_voltage_max_pu"], "f_nadir_hz": r["frequency_nadir_hz"]}
            for n, r in res.items()]
    with (A / "IEEE39_E11_limits.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    summary = {"stage": "E11", "git_commit": git_commit(), "near_threshold_fraction_of_range": NEAR, "runs": res,
               "reused_negative_result": {"file": "IEEE39_E5_S1screen_C2_100MW_50MVAr_FAIL_summary.json", "status_auto": s1.get("status_auto"), "keys": list(s1)[:12]},
               "inputs_sha256": {f: sha256(A / f) for f in ("IEEE39_E5_C2t_timeseries.npz", "IEEE39_E8_C2t_timeseries.npz", "IEEE39_E9B0_Vsafe_R35_040_series.npz", "IEEE39_B3_C2t_Pplus_timeseries.npz")}}
    (A / "IEEE39_E11_summary.json").write_text(json.dumps(summary, indent=2, default=float), encoding="utf-8")
    fig, ax = plt.subplots(2, 3, figsize=(19, 9))
    for n, (t, c, w) in ser.items():
        if "P+" in n and "Q+" not in n:
            ax[0, 0].plot(t, c, lw=.9, label=n)
        if n.endswith("Q+"):
            ax[0, 1].plot(t, c, lw=.9, label=n)
        if "simultaneous" in n:
            ax[0, 2].plot(t, w, lw=.8)
    ax[0, 0].set_title("P+: number of units within 5 % of a limit")
    ax[0, 1].set_title("Q+: number of units within 5 % of a limit")
    ax[0, 2].set_title("P+Q+ simultaneous: tightest normalised margin per unit (10 curves)")
    sel = [n for n in res if n.endswith("P+")] + ["R35_040_B2 P+Q+ (simultaneous)"]
    x = np.arange(10)
    for k, n in enumerate(sel):
        ax[1, 0].bar(x + 0.15 * (k - len(sel) / 2), [res[n]["min_normalised_margin_by_unit"][u] for u in names], 0.15, label=n)
        ax[1, 1].bar(x + 0.15 * (k - len(sel) / 2), [res[n]["delivered_dP_by_unit_pu"][u] for u in names], 0.15, label=n)
    ax[1, 0].set_xticks(x); ax[1, 0].set_xticklabels(names, rotation=60, fontsize=7); ax[1, 0].set_title("minimum normalised margin by unit"); ax[1, 0].axhline(NEAR, color="r", ls="--", lw=.8)
    ax[1, 1].set_xticks(x); ax[1, 1].set_xticklabels(names, rotation=60, fontsize=7); ax[1, 1].set_title("delivered dP by unit (final - pre) [pu]")
    heads = [res[sel[0]]["pre_event_headroom_pu"][u] for u in names]
    ax[1, 2].bar(x, heads); ax[1, 2].set_xticks(x); ax[1, 2].set_xticklabels(names, rotation=60, fontsize=7); ax[1, 2].set_title("pre-event active-power headroom (pmax - P) [pu], E5t reference dispatch")
    for a in ax.ravel():
        a.grid(alpha=.25)
    for a in (ax[0, 0], ax[0, 1], ax[1, 0], ax[1, 1]):
        a.legend(fontsize=6)
    fig.suptitle("E11: simultaneous limits and physical redistribution (stored runs and the simultaneous P+Q+ event on C2t_Vsafe_R35_040)")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "IEEE39_E11_limits.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    for n, r in res.items():
        print(f"{n:38s} nearmax={r['max_units_near_limit_simultaneously']} t>=2={r['time_with_>=2_units_near_s']:.1f}s pair={r['longest_simultaneous_pair']} {r['longest_simultaneous_pair_duration_s']:.1f}s cross={r['units_crossing_a_limit']} GFMshare={r['GFM_share_of_delivered_dP']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
