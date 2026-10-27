"""E10 (Option B): convergence, residual errors and behaviour of the RDC on the stored 200 s runs (no new simulation).

Runs analysed (all reproducible from the stored raw series): E8 (original RDC on C2t, "B2"), B3 (centered RDC with the B3-A reference) and the B2 replay on the frozen variant
C2t_Vsafe_R35_040 (S0, P+, Q+ each).  For every run and scenario:
  * frequency: final error (last 10 s), nadir, 2 mHz settling time, slope over the last 20 s and, when the tail is monotone, an exponential time-constant estimate;
  * voltage: final bus-voltage extremes, mean error of the unit buses with respect to 1.0 pu, slope of the extremes;
  * power / setpoints: final Pset - Pn and Qset - Qn per unit, drift of Pset and Qset over the last 20 s, spread of P/Pn among the ten units;
  * for E8 and B3: error with respect to the selected equilibrium xi*(d) of B3-A (P*, Q*, V*) and the setpoint reference (Pset_eff, Qset_eff);
  * a verdict per run: converged (all tail slopes below the declared tolerances) or not converged (with the offending channels).
Declared tolerances: frequency tail slope 1e-6 Hz/s, setpoint drift 1e-3 pu per 20 s, unit-voltage tail slope 1e-5 pu/s.  Nothing is tuned: negative results are reported.
"""

from __future__ import annotations

import csv
import json
import os

os.environ["C2_VARIANT"] = "C2t"

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from run_e0_ieee39 import ARTIFACTS_DIR as A, FIGURES_DIR, git_commit, sha256

EVENT = 5.0
TOL = {"f_slope_hz_per_s": 1e-6, "setpoint_drift_pu_per_20s": 1e-3, "v_slope_pu_per_s": 1e-5}
V2 = json.loads((A / "IEEE39_B3A_C2t_equilibrium_v2.json").read_text(encoding="utf-8"))


def load_runs() -> dict[str, dict[str, np.ndarray]]:
    runs: dict[str, dict[str, np.ndarray]] = {}
    e8 = np.load(A / "IEEE39_E8_C2t_timeseries.npz")
    for sc in ("S0", "P+", "Q+"):
        runs[f"E8_B2 {sc}"] = {k[len(sc) + 1:]: e8[k] for k in e8.files if k.startswith(sc + "_")}
    for sc, tag in (("S0", "S0"), ("P+", "Pplus"), ("Q+", "Qplus")):
        z = np.load(A / f"IEEE39_B3_C2t_{tag}_timeseries.npz")
        runs[f"B3_centered {sc}"] = {k[3:]: z[k] for k in z.files if k.startswith("B3_")}
    v = np.load(A / "IEEE39_E9B0_Vsafe_R35_040_series.npz")
    for sc in ("S0", "P+", "Q+"):
        runs[f"R35_040_B2 {sc}"] = {k.split("__", 1)[1]: v[k] for k in v.files if k.startswith(sc + "__")}
    return runs


def slope(t: np.ndarray, y: np.ndarray, span: float = 20.0) -> np.ndarray:
    sel = t >= t[-1] - span
    tt = t[sel] - t[sel].mean()
    return (tt[:, None] * (y[sel] - y[sel].mean(axis=0))).sum(axis=0) / (tt ** 2).sum()


def tau_estimate(t: np.ndarray, y: np.ndarray, t0: float) -> float | None:
    """Exponential time constant of |y - y_inf| over [t0, end - 20 s] with y_inf = mean of the last 10 s; None if the tail is not a decay."""
    yinf = y[t >= t[-1] - 10].mean()
    sel = (t >= t0) & (t <= t[-1] - 20)
    e = np.abs(y[sel] - yinf)
    ok = e > 1e-9
    if ok.sum() < 50:
        return None
    k = np.polyfit(t[sel][ok], np.log(e[ok]), 1)[0]
    return float(-1.0 / k) if k < 0 else None


def unit_arrays(d):
    ids = list(d["bus_ids"])
    cols = [ids.index(b) for b in d["unit_bus_ids"]]
    return np.hstack([d["sg_p_pu"], d["gfm_p_pu"]]), np.hstack([d["sg_q_pu"], d["gfm_q_pu"]]), d["bus_voltage_pu"][:, cols]


def analyse(name: str, d: dict[str, np.ndarray]) -> dict:
    t = d["time_s"]
    sc = name.split()[-1]
    p, q, v = unit_arrays(d)
    f = d["bus_frequency_hz"].mean(axis=1)
    fin = t >= t[-1] - 10
    pn = d["unit_pn"] if "unit_pn" in d else d["cmd_pset"][0]      # the initial setpoint equals the pre-event physical power
    qn = d["unit_qn"] if "unit_qn" in d else d["cmd_qset"][0]
    ct = d["cmd_t"]
    pset, qset = d["cmd_pset"], d["cmd_qset"]
    out: dict = {"run": name, "frequency_final_error_hz": float(f[fin].mean() - 60.0), "frequency_nadir_hz": float(f[t >= EVENT].min()), "frequency_max_dev_hz": float(np.abs(f - 60).max()),
                 "frequency_tail_slope_hz_per_s": float(slope(t, f[:, None])[0]), "frequency_tau_s": tau_estimate(t, f, EVENT + 5)}
    dev = np.abs(f - 60.0)
    post = t >= EVENT
    idx = np.where(post & (dev > 2e-3))[0]
    out["frequency_2mHz_settling_after_event_s"] = float(t[idx[-1]] - EVENT) if idx.size else 0.0
    vb = d["bus_voltage_pu"]
    out["bus_voltage_final_min_pu"], out["bus_voltage_final_max_pu"] = float(vb[fin].mean(axis=0).min()), float(vb[fin].mean(axis=0).max())
    out["bus_voltage_tail_slope_max_abs_pu_per_s"] = float(np.abs(slope(t, vb)).max())
    out["unit_voltage_mean_abs_error_to_1pu"] = float(np.abs(v[fin].mean(axis=0) - 1.0).mean())
    out["pset_minus_pn_final_pu"] = (pset[-1] - pn).tolist()
    out["qset_minus_qn_final_pu"] = (qset[-1] - qn).tolist()
    sp = slope(ct, np.hstack([pset, qset]), 20.0) * 20.0
    out["pset_drift_20s_max_abs_pu"], out["qset_drift_20s_max_abs_pu"] = float(np.abs(sp[:10]).max()), float(np.abs(sp[10:]).max())
    ratio = p[fin].mean(axis=0) / pn
    out["P_over_Pn_final_spread"] = float(ratio.max() - ratio.min())
    out["delivered_dP_sum_pu"] = float((p[fin].mean(axis=0) - p[(t >= EVENT - 2) & (t < EVENT)].mean(axis=0)).sum())
    if name.split()[0] in ("E8_B2", "B3_centered") and sc in V2["scenarios"]:
        e = V2["scenarios"][sc]
        ps, qs, vs = np.array(e["P_star"]), np.array(e["Q_star"]), np.array(e["V_star"])
        out["target_errors"] = {"max_abs_P_error_pu": float(np.abs(p[fin].mean(axis=0) - ps).max()), "max_abs_Q_error_pu": float(np.abs(q[fin].mean(axis=0) - qs).max()),
                                "max_abs_V_error_pu": float(np.abs(v[fin].mean(axis=0) - vs).max()), "max_abs_Pset_error_pu": float(np.abs(pset[-1] - np.array(e["Pset_eff"])).max()),
                                "max_abs_Qset_error_pu": float(np.abs(qset[-1] - np.array(e["Qset_eff"])).max())}
    out["tail_slopes_unit_P_pu_per_s_max"] = float(np.abs(slope(t, p)).max())
    bad = []
    if abs(out["frequency_tail_slope_hz_per_s"]) > TOL["f_slope_hz_per_s"]:
        bad.append("frequency")
    if out["pset_drift_20s_max_abs_pu"] > TOL["setpoint_drift_pu_per_20s"]:
        bad.append("Pset")
    if out["qset_drift_20s_max_abs_pu"] > TOL["setpoint_drift_pu_per_20s"]:
        bad.append("Qset")
    if out["bus_voltage_tail_slope_max_abs_pu_per_s"] > TOL["v_slope_pu_per_s"]:
        bad.append("voltage")
    out["converged"] = not bad
    out["not_converged_channels"] = bad
    return out


def main() -> int:
    runs = load_runs()
    res = {n: analyse(n, d) for n, d in runs.items()}
    rows = [{k: v for k, v in r.items() if not isinstance(v, (list, dict))} | ({f"target_{kk}": vv for kk, vv in r["target_errors"].items()} if "target_errors" in r else {}) for r in res.values()]
    keys = sorted({k for r in rows for k in r}, key=lambda k: (k != "run", k))
    with (A / "IEEE39_E10_convergence.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    summary = {"stage": "E10", "git_commit": git_commit(), "tolerances_declared": TOL, "runs": res,
               "counts": {"converged": sum(r["converged"] for r in res.values()), "total": len(res)},
               "finding": "none of the 200 s runs of the original or centered RDC satisfies all declared tail tolerances if Qset keeps drifting; see per-run channels",
               "inputs_sha256": {f: sha256(A / f) for f in ("IEEE39_E8_C2t_timeseries.npz", "IEEE39_B3_C2t_S0_timeseries.npz", "IEEE39_B3_C2t_Pplus_timeseries.npz", "IEEE39_B3_C2t_Qplus_timeseries.npz",
                                                          "IEEE39_E9B0_Vsafe_R35_040_series.npz", "IEEE39_B3A_C2t_equilibrium_v2.json")}}
    (A / "IEEE39_E10_summary.json").write_text(json.dumps(summary, indent=2, default=float), encoding="utf-8")
    fig, ax = plt.subplots(2, 3, figsize=(19, 9))
    names = list(runs)
    for n in names:
        d = runs[n]
        t = d["time_s"]
        f = d["bus_frequency_hz"].mean(axis=1)
        if "P+" in n:
            ax[0, 0].plot(t, (f - 60.0) * 1e3, lw=.9, label=n)
        if "Q+" in n:
            ax[0, 1].plot(t, (f - 60.0) * 1e3, lw=.9, label=n)
        if "P+" in n:
            ax[0, 2].plot(d["cmd_t"], np.abs(d["cmd_qset"] - d["cmd_qset"][0]).max(axis=1), lw=.9, label=n)
        if "S0" in n:
            ax[1, 0].plot(d["cmd_t"], np.abs(d["cmd_qset"] - d["cmd_qset"][0]).max(axis=1), lw=.9, label=n)
        ax[1, 1].plot(t, d["bus_voltage_pu"].max(axis=1) - d["bus_voltage_pu"].min(axis=1), lw=.6, alpha=.8)
    ax[0, 0].set_title("P+: mean frequency error [mHz]"); ax[0, 1].set_title("Q+: mean frequency error [mHz]"); ax[0, 2].set_title("P+: max |Qset - Qn| [pu]")
    ax[1, 0].set_title("S0: max |Qset - Qn| [pu]"); ax[1, 1].set_title("bus-voltage spread (max - min) in all runs")
    lab = list(res)
    ax[1, 2].barh(lab[::-1], [res[n]["qset_drift_20s_max_abs_pu"] for n in lab][::-1]); ax[1, 2].axvline(TOL["setpoint_drift_pu_per_20s"], color="r", ls="--", label="tolerance"); ax[1, 2].set_xscale("log")
    ax[1, 2].set_title("Qset drift over the last 20 s [pu]"); ax[1, 2].legend(fontsize=7)
    for a in ax.ravel():
        a.grid(alpha=.25)
    for a in (ax[0, 0], ax[0, 1], ax[0, 2], ax[1, 0]):
        a.legend(fontsize=6); a.set_xlabel("Time [s]")
    ax[0, 0].set_xlim(0, 60); ax[0, 1].set_xlim(0, 60)
    fig.suptitle("E10: convergence and residual behaviour of the original (E8, variant) and centered (B3) RDC over 200 s (stored runs)"); fig.tight_layout()
    fig.savefig(FIGURES_DIR / "IEEE39_E10_convergence.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    for n, r in res.items():
        te = r.get("target_errors", {})
        print(f"{n:22s} conv={r['converged']} bad={r['not_converged_channels']} f_err={r['frequency_final_error_hz']:.2e} tau_f={r['frequency_tau_s']} Qdrift={r['qset_drift_20s_max_abs_pu']:.3g} Pdrift={r['pset_drift_20s_max_abs_pu']:.3g} "
              f"Verr={te.get('max_abs_V_error_pu')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
