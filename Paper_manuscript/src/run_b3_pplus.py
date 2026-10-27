"""B3-P+ / B3-Q+ (centered RDC, +58.564 MW at bus 4 or +17.345 MVAr at bus 21, t = 5 s) on C2t versus the B2 replica of E8 (DEC-040, DEC-041).

Reuses the B3 runner (``run_b3_ieee39``): same plant, graph, gains, E8 actuator maps and 200 s horizon.  The only
difference with S0 is the reference equilibrium of the centering offset: xi*(d) of B3-A (v2 file, selected in
advance and never re-optimized), v_nom = v_RDC(xi, d) - v_RDC(xi*(d), d) with Pset_eff/Qset_eff as the reference
setpoints.  xi*(d) uses the exact disturbance (privileged information, available from the event at t = 5 s, which is
also the activation time).  One scenario per run (B3_SCEN); weight sensitivity and E9 are not authorized.
"""

from __future__ import annotations

import csv
import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import andes
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import run_b3_ieee39 as b  # noqa: E402  (sets C2_VARIANT = C2t)
import run_e7_ieee39 as e7  # noqa: E402
import run_e8_ieee39 as e8  # noqa: E402
from run_e0_ieee39 import (  # noqa: E402
    ARTIFACTS_DIR, FIGURES_DIR, MATRIX_FILE, NOMINAL_FREQUENCY_HZ, PROJECT_ROOT, git_commit, sha256,
)
from variant import CASE_LABEL  # noqa: E402

SCEN = os.environ.get("B3_SCEN", "P+")  # P+ (DEC-040) or Q+ (DEC-041)
TAG = {"P+": "Pplus", "Q+": "Qplus"}[SCEN]
LABEL = f"B3-{SCEN}"
EVDESC = {"P+": "+58.564 MW at bus 4", "Q+": "+17.345 MVAr at bus 21"}[SCEN]
PREFIX = f"IEEE39_B3_C2t_{TAG}"
RAW_FILE = ARTIFACTS_DIR / f"{PREFIX}_timeseries.npz"
SUMMARY_FILE = ARTIFACTS_DIR / f"{PREFIX}_summary.json"
FIG = {k: FIGURES_DIR / f"{PREFIX}_{k}.png" for k in ("frequency", "voltage", "power", "rdc_action", "references", "errors")}
V2_FILE = ARTIFACTS_DIR / "IEEE39_B3A_C2t_equilibrium_v2.json"
EVENT, TF = e8.EVENT_TIME_S, e8.FINAL_TIME_S
# Predeclared reporting thresholds for the convergence-to-target flags (not tuned; failures are reported, not corrected)
TOL = {"f_hz": 2.0e-3, "p_pu": 5.0e-3, "q_pu": 5.0e-2, "v_pu": 5.0e-3, "pset_pu": 5.0e-3, "qset_pu": 5.0e-2}
TOL_REPLICATION = b.TOL_REPLICATION


def load_ref() -> dict[str, np.ndarray]:
    e = json.loads(V2_FILE.read_text(encoding="utf-8"))["scenarios"][SCEN]
    return {"pset_eff": np.array(e["Pset_eff"]), "qset_eff": np.array(e["Qset_eff"]), "p_star": np.array(e["P_star"]),
            "q_star": np.array(e["Q_star"]), "v_star": np.array(e["V_star"])}


def post_metrics(d: dict[str, np.ndarray], ref: dict[str, np.ndarray]) -> dict[str, Any]:
    t = d["time_s"]
    p, q, v = e7.unit_series(None, d)
    f = d["bus_frequency_hz"].mean(axis=1)
    fin = t >= t[-1] - 2.0
    post = t >= EVENT
    ct = d["cmd_t"]
    act = ct >= EVENT
    pset, qset, pn, qn = d["cmd_pset"], d["cmd_qset"], d["unit_pn"], d["unit_qn"]
    n_sg = d["sg_p_pu"].shape[1]
    names = [("SG" if i < n_sg else "GFM") + str(bus) for i, bus in enumerate(d["unit_bus_ids"])]
    dt = float(np.median(np.diff(ct)))
    err_p, err_q, err_v = p - ref["p_star"], q - ref["q_star"], v - ref["v_star"]
    pset_err, qset_err = pset - ref["pset_eff"], qset - ref["qset_eff"]

    def settle(series_abs, tol, time=t):  # time after the event of the last exceedance of tol; None if never exceeded
        sel = time >= EVENT
        idx = np.where(series_abs[sel] > tol)[0]
        return None if idx.size == 0 else float(time[sel][idx[-1]] - EVENT)

    # actuator tracking: GFM PIplim_y / PIqlim_y vs their commanded targets (y0 + Pset - Pn, y0q + Qset - Qn)
    y_err = d["cmd_y"] - (d["unit_y0"][None, :] + (pset - pn)[:, n_sg:])
    yq_err = d["cmd_yq"] - (d["unit_y0q"][None, :] + (qset - qn)[:, n_sg:])
    pmax, qmax, qmin = d["unit_pmax"], d["unit_qmax"], d["unit_qmin"]
    i31, i35 = names.index("SG31"), names.index("SG35")
    step = lambda x: np.abs(np.diff(x, axis=0))  # noqa: E731
    vb_fin = d["bus_voltage_pu"][fin].mean(axis=0)
    out = {
        "unit_names": names,
        "final_frequency_error_hz": float(f[fin].mean() - NOMINAL_FREQUENCY_HZ), "max_abs_frequency_deviation_hz": float(np.abs(f - NOMINAL_FREQUENCY_HZ).max()),
        "frequency_nadir_hz": float(f[post].min()), "frequency_2mHz_settling_s_after_event": settle(np.abs(f - NOMINAL_FREQUENCY_HZ), 2e-3),
        "final_abs_P_error_vs_Pstar_pu_per_unit": np.abs(err_p[fin].mean(axis=0)).tolist(), "final_abs_Q_error_vs_Qstar_pu_per_unit": np.abs(err_q[fin].mean(axis=0)).tolist(),
        "final_abs_V_error_vs_Vstar_pu_per_unit": np.abs(err_v[fin].mean(axis=0)).tolist(),
        "final_max_abs_P_error_pu": float(np.abs(err_p[fin].mean(axis=0)).max()), "final_max_abs_Q_error_pu": float(np.abs(err_q[fin].mean(axis=0)).max()),
        "final_max_abs_V_error_pu": float(np.abs(err_v[fin].mean(axis=0)).max()),
        "final_unit_P_pu": p[fin].mean(axis=0).tolist(), "final_unit_Q_pu": q[fin].mean(axis=0).tolist(), "final_unit_V_pu": v[fin].mean(axis=0).tolist(),
        "P_star_pu": ref["p_star"].tolist(), "Q_star_pu": ref["q_star"].tolist(), "V_star_pu": ref["v_star"].tolist(),
        "max_abs_P_error_after_event_pu": float(np.abs(err_p[post]).max()), "max_abs_Q_error_after_event_pu": float(np.abs(err_q[post]).max()),
        "max_abs_V_error_after_event_pu": float(np.abs(err_v[post]).max()),
        "final_pset_error_vs_Pset_eff_pu_per_unit": pset_err[-1].tolist(), "final_qset_error_vs_Qset_eff_pu_per_unit": qset_err[-1].tolist(),
        "final_max_abs_pset_error_pu": float(np.abs(pset_err[-1]).max()), "final_max_abs_qset_error_pu": float(np.abs(qset_err[-1]).max()),
        "qset_final_minus_qn_pu_per_unit": (qset[-1] - qn).tolist(), "qset_eff_minus_qn_pu_per_unit": (ref["qset_eff"] - qn).tolist(),
        "qset_drift_last20s_pu_per_unit": (qset[ct >= ct[-1] - 20.0][-1] - qset[ct >= ct[-1] - 20.0][0]).tolist(),
        "pset_drift_last20s_pu_per_unit": (pset[ct >= ct[-1] - 20.0][-1] - pset[ct >= ct[-1] - 20.0][0]).tolist(),
        "vnom_p_first_step_pu_per_s_per_unit": d["cmd_vnom_p"][act][0].tolist(), "vnom_q_first_step_pu_per_s_per_unit": d["cmd_vnom_q"][act][0].tolist(),
        "vnom_first_step_max_abs_p_pu_per_s": float(np.abs(d["cmd_vnom_p"][act][0]).max()), "vnom_first_step_max_abs_q_pu_per_s": float(np.abs(d["cmd_vnom_q"][act][0]).max()),
        "offset_jump_xi_pre_to_xi_star_p_pu_per_s": (d["offset_p"] - d["offset_pre_p"]).tolist(), "offset_jump_xi_pre_to_xi_star_q_pu_per_s": (d["offset_q"] - d["offset_pre_q"]).tolist(),
        "offset_jump_max_abs_p_pu_per_s": float(np.abs(d["offset_p"] - d["offset_pre_p"]).max()), "offset_jump_max_abs_q_pu_per_s": float(np.abs(d["offset_q"] - d["offset_pre_q"]).max()),
        "max_abs_dPset_dt_pu_per_s": float(np.abs(d["cmd_vnom_p"][act]).max()), "max_abs_dQset_dt_pu_per_s": float(np.abs(d["cmd_vnom_q"][act]).max()),
        "max_abs_dPset_dt_per_unit_pu_per_s": np.abs(d["cmd_vnom_p"][act]).max(axis=0).tolist(), "max_abs_dQset_dt_per_unit_pu_per_s": np.abs(d["cmd_vnom_q"][act]).max(axis=0).tolist(),
        "max_abs_dPset_dt_MW_per_s": float(100 * np.abs(d["cmd_vnom_p"][act]).max()),
        "rate_limits_specified": "none: the E8 realization has no explicit rate limit on Pset, Qset or actuator signals; maxima are reported only",
        "max_physical_dP_dt_pu_per_s": float((step(p[post]) / np.median(np.diff(t))).max()),
        "max_single_step_change_pset_pu": float(step(pset).max()), "max_single_step_change_qset_pu": float(step(qset).max()),
        "max_single_step_change_paux": float(step(d["cmd_paux"]).max()), "max_single_step_change_qaux": float(step(d["cmd_qaux"]).max()),
        "max_single_step_change_z": float(step(d["cmd_z"]).max()),
        "max_single_step_change_physical_P_pu": float(step(p[post]).max()), "max_single_step_change_physical_Q_pu": float(step(q[post]).max()),
        "pset_continuity_bound_dt_times_vmax": float(dt * np.abs(d["cmd_vnom_p"][act]).max()),
        "pset_continuous_at_event": bool(np.abs(pset[ct >= EVENT][0] - pset[ct < EVENT][-1]).max() <= 2 * dt * np.abs(d["cmd_vnom_p"][act]).max() + 1e-12),
        "qset_continuous_at_event": bool(np.abs(qset[ct >= EVENT][0] - qset[ct < EVENT][-1]).max() <= 2 * dt * np.abs(d["cmd_vnom_q"][act]).max() + 1e-12),
        "actuator_gfm_PIplim_y_tracking_max_abs_pu": float(np.abs(y_err).max()), "actuator_gfm_PIqlim_y_tracking_max_abs_pu": float(np.abs(yq_err).max()),
        "actuator_gfm_PIplim_y_tracking_final_max_abs_pu": float(np.abs(y_err[-1]).max()), "actuator_gfm_PIqlim_y_tracking_final_max_abs_pu": float(np.abs(yq_err[-1]).max()),
        "actuator_max_abs_paux": float(np.abs(d["cmd_paux"]).max()), "actuator_max_abs_qaux": float(np.abs(d["cmd_qaux"]).max()),
        "actuator_max_abs_z_pu": float(np.abs(d["cmd_z"]).max()), "z_clamp_pu": e8.Z_CLAMP, "z_clamp_hit": bool(np.any(np.abs(d["cmd_z"]) >= e8.Z_CLAMP - 1e-12)),
        "z_final_pu": d["cmd_z"][-1].tolist(),
        "min_gp_normalized": float(d["cmd_gp"].min()), "min_gq_normalized": float(d["cmd_gq"].min()),
        "physical_margin_to_pmax_min_per_unit_pu": (pmax - p).min(axis=0).tolist(), "transient_p_excess_over_pmax_pu": np.maximum(0.0, p.max(axis=0) - pmax).tolist(),
        "reference_margin_to_pmax_min_per_unit_pu": (pmax - pset).min(axis=0).tolist(),
        "reference_margin_to_qmax_min_per_unit_pu": (qmax - qset).min(axis=0).tolist(), "reference_margin_to_qmin_min_per_unit_pu": (qset - qmin).min(axis=0).tolist(),
        "physical_margin_to_qmax_min_per_unit_pu": (qmax - q).min(axis=0).tolist(), "physical_margin_to_qmin_min_per_unit_pu": (q - qmin).min(axis=0).tolist(),
        "physical_s_rel_margin_min_per_unit": (1 - np.hypot(p, q) / d["unit_smax"]).min(axis=0).tolist(),
        "SG31": {"physical_margin_to_pmax_min_pu": float((pmax - p)[:, i31].min()), "transient_p_excess_pu": float(max(0.0, p[:, i31].max() - pmax[i31])),
                 "reference_margin_to_pmax_min_pu": float((pmax - pset)[:, i31].min()), "pmax_pu": float(pmax[i31]), "P_max_pu": float(p[:, i31].max())},
        "SG35": {"physical_margin_to_pmax_min_pu": float((pmax - p)[:, i35].min()), "transient_p_excess_pu": float(max(0.0, p[:, i35].max() - pmax[i35])),
                 "reference_margin_to_pmax_min_pu": float((pmax - pset)[:, i35].min()), "pmax_pu": float(pmax[i35]), "P_max_pu": float(p[:, i35].max()),
                 "Pset_eff_margin_pu": float(pmax[i35] - ref["pset_eff"][i35])},
        "bus_voltage_min_pu": float(d["bus_voltage_pu"].min()), "bus_voltage_max_pu": float(d["bus_voltage_pu"].max()),
        "bus_voltage_final_min_pu": float(vb_fin.min()), "bus_voltage_final_max_pu": float(vb_fin.max()),
        "bus_voltage_final_outside_0p95_1p05": int(np.sum((vb_fin < 0.95) | (vb_fin > 1.05))),
        "bus_voltage_pre_event_max_pu": float(d["bus_voltage_pu"][(t >= EVENT - 2) & (t <= EVENT)].mean(axis=0).max()),
        "settling_s_after_event": {"P_err": settle(np.abs(err_p).max(axis=1), TOL["p_pu"]), "Q_err": settle(np.abs(err_q).max(axis=1), TOL["q_pu"]),
                                   "V_err": settle(np.abs(err_v).max(axis=1), TOL["v_pu"]), "Pset_err": settle(np.abs(pset_err).max(axis=1), TOL["pset_pu"], ct),
                                   "Qset_err": settle(np.abs(qset_err).max(axis=1), TOL["qset_pu"], ct)},
        "unit_bus_ids": d["unit_bus_ids"].tolist()}
    return out


def plots(b2: dict[str, np.ndarray], b3: dict[str, np.ndarray], ref: dict[str, np.ndarray]) -> None:
    names = ("B2 (original RDC; replica of E8)", f"{LABEL} (centered RDC, reference xi*(d))")
    runs = (b2, b3)
    n_sg = b3["sg_p_pu"].shape[1]
    label = lambda i, bus: f"{'SG' if i < n_sg else 'GFM'}{bus}"  # noqa: E731
    ev = dict(color="tab:red", ls=":", lw=.8)
    # 1 frequency
    fig, ax = plt.subplots(2, 2, figsize=(13, 8))
    for c, (nm, d) in enumerate(zip(names, runs)):
        t, f = d["time_s"], d["bus_frequency_hz"]
        ax[0, c].fill_between(t, f.min(1), f.max(1), color="0.85", label="39-bus envelope"); ax[0, c].plot(t, f.mean(1), "tab:blue", lw=1.0, label="mean bus frequency")
        ax[0, c].axhline(60, color="k", ls=":", lw=.8); ax[0, c].set_title(nm); ax[0, c].set_ylim(59.96, 60.01)
        dev = (f - 60.0) * 1e3
        ax[1, c].fill_between(t, dev.min(1), dev.max(1), color="0.85"); ax[1, c].plot(t, dev.mean(1), "tab:blue", lw=1.0)
        ax[1, c].axhline(0, color="k", ls=":", lw=.8); ax[1, c].set_title("zoom: f - 60 Hz [mHz] (own axis)"); ax[1, c].set_xlim(0, 100)
        for r in range(2):
            ax[r, c].axvline(EVENT, **ev); ax[r, c].grid(alpha=.25); ax[r, c].set_xlabel("Time [s]")
    ax[0, 0].set_ylabel("Frequency [Hz]"); ax[1, 0].set_ylabel("f - 60 Hz [mHz]"); ax[0, 0].legend(fontsize=7)
    fig.suptitle(f"{LABEL} on C2t ({EVDESC}, t = 5 s = activation): bus frequency"); fig.tight_layout()
    fig.savefig(FIG["frequency"], dpi=300, bbox_inches="tight"); plt.close(fig)
    # 2 voltage of the 39 buses + unit-bus error to V*
    fig, ax = plt.subplots(2, 2, figsize=(13, 8))
    for c, (nm, d) in enumerate(zip(names, runs)):
        t, vb = d["time_s"], d["bus_voltage_pu"]
        ax[0, c].plot(t, vb, lw=.6, color="tab:blue", alpha=.7); ax[0, c].axhline(1.05, color="k", ls="--", lw=.7); ax[0, c].axhline(0.95, color="k", ls="--", lw=.7)
        ax[0, c].set_title(nm + ": |V| of the 39 buses (dashed: 0.95 / 1.05 band)")
        _, _, v = e7.unit_series(None, d)
        for i, bus in enumerate(d["unit_bus_ids"]):
            ax[1, c].plot(t, v[:, i] - ref["v_star"][i], lw=.9, ls="-" if i < n_sg else "--", label=label(i, bus))
        ax[1, c].axhline(0, color="k", ls=":", lw=.8); ax[1, c].set_title("unit-bus V - V* [pu] (own axis)")
        for r in range(2):
            ax[r, c].axvline(EVENT, **ev); ax[r, c].grid(alpha=.25); ax[r, c].set_xlabel("Time [s]")
    ax[0, 0].set_ylabel("|V| [pu]"); ax[1, 0].set_ylabel("V - V* [pu]"); ax[1, 0].legend(ncol=3, fontsize=6)
    fig.suptitle(f"{LABEL} on C2t: bus voltages and unit-bus error to V*"); fig.tight_layout()
    fig.savefig(FIG["voltage"], dpi=300, bbox_inches="tight"); plt.close(fig)
    # 3 physical power with targets
    fig, ax = plt.subplots(2, 2, figsize=(13, 8))
    for c, (nm, d) in enumerate(zip(names, runs)):
        t = d["time_s"]; p, q, _ = e7.unit_series(None, d)
        for i, bus in enumerate(d["unit_bus_ids"]):
            kw = dict(lw=.9, ls="-" if i < n_sg else "--", label=label(i, bus))
            ax[0, c].plot(t, (p[:, i] - d["unit_pn"][i]) * 100, **kw); ax[1, c].plot(t, (q[:, i] - d["unit_qn"][i]) * 100, **kw)
            ax[0, c].plot(t[-1] + 2, (ref["p_star"][i] - d["unit_pn"][i]) * 100, "k>", ms=3); ax[1, c].plot(t[-1] + 2, (ref["q_star"][i] - d["unit_qn"][i]) * 100, "k>", ms=3)
        ax[0, c].set_title(nm + ": physical P - Pn [MW]"); ax[1, c].set_title("physical Q - Qn [MVAr]")
        for r in range(2):
            ax[r, c].axvline(EVENT, **ev); ax[r, c].grid(alpha=.25); ax[r, c].set_xlabel("Time [s]")
    ax[0, 0].legend(ncol=3, fontsize=6)
    fig.suptitle(f"{LABEL} on C2t: physical power of the ten units (triangles at the right: targets P*, Q*; own axes)"); fig.tight_layout()
    fig.savefig(FIG["power"], dpi=300, bbox_inches="tight"); plt.close(fig)
    # 4 RDC actions
    fig, ax = plt.subplots(2, 3, figsize=(16, 8))
    for r, key in enumerate(("p", "q")):
        for i, bus in enumerate(b3["unit_bus_ids"]):
            kw = dict(lw=.9, ls="-" if i < n_sg else "--", label=label(i, bus))
            ax[r, 0].plot(b2["cmd_t"], b2[f"cmd_vrdc_{key}"][:, i], **kw); ax[r, 1].plot(b3["cmd_t"], b3[f"cmd_vrdc_{key}"][:, i], **kw)
            ax[r, 2].plot(b3["cmd_t"], b3[f"cmd_vnom_{key}"][:, i], **kw)
        ax[r, 0].set_title(f"B2: applied original RDC field v_RDC,{key.upper()} [pu/s]"); ax[r, 1].set_title(f"B3: original field v_RDC,{key.upper()} along the B3 trajectory")
        ax[r, 2].set_title(f"B3: applied centered action v_nom,{key.upper()} = v_RDC - v_RDC(xi*)")
        for c in range(3):
            ax[r, c].axvline(EVENT, **ev); ax[r, c].grid(alpha=.25); ax[r, c].set_xlabel("Time [s]")
    ax[0, 0].legend(ncol=3, fontsize=6)
    fig.suptitle(f"{LABEL} on C2t: original and centered RDC actions (own axes; v_nom = dPset/dt, dQset/dt)"); fig.tight_layout()
    fig.savefig(FIG["rdc_action"], dpi=300, bbox_inches="tight"); plt.close(fig)
    # 5 references and actuator signals
    fig, ax = plt.subplots(2, 4, figsize=(20, 8))
    for r, (nm, d) in enumerate(zip(names, runs)):
        ct = d["cmd_t"]
        for i, bus in enumerate(d["unit_bus_ids"]):
            kw = dict(lw=.9, ls="-" if i < n_sg else "--", label=label(i, bus))
            ax[r, 0].plot(ct, d["cmd_pset"][:, i] - d["unit_pn"][i], **kw); ax[r, 1].plot(ct, d["cmd_qset"][:, i] - d["unit_qn"][i], **kw)
            ax[r, 0].plot(ct[-1] + 2, ref["pset_eff"][i] - d["unit_pn"][i], "k>", ms=3); ax[r, 1].plot(ct[-1] + 2, ref["qset_eff"][i] - d["unit_qn"][i], "k>", ms=3)
        for i in range(n_sg):
            ax[r, 2].plot(ct, d["cmd_z"][:, i], lw=.9, label=f"SG{d['unit_bus_ids'][i]} z")
        ax[r, 2].axhline(e8.Z_CLAMP, color="k", ls="--", lw=.7); ax[r, 2].axhline(-e8.Z_CLAMP, color="k", ls="--", lw=.7)
        for i in range(n_sg, 10):
            ax[r, 3].plot(ct, d["cmd_y"][:, i - n_sg] - (d["unit_y0"][i - n_sg] + (d["cmd_pset"][:, i] - d["unit_pn"][i])), lw=.9, label=f"GFM{d['unit_bus_ids'][i]} P")
            ax[r, 3].plot(ct, d["cmd_yq"][:, i - n_sg] - (d["unit_y0q"][i - n_sg] + (d["cmd_qset"][:, i] - d["unit_qn"][i])), lw=.9, ls=":", label=f"GFM{d['unit_bus_ids'][i]} Q")
        ax[r, 0].set_title(nm + ": Pset - Pn [pu] (triangles: Pset_eff)"); ax[r, 1].set_title("Qset - Qn [pu] (triangles: Qset_eff)")
        ax[r, 2].set_title("SG exciter offset z [pu] (dashed: clamp)"); ax[r, 3].set_title("GFM PIp/PIq tracking error vs command [pu]")
        for c in range(4):
            ax[r, c].axvline(EVENT, **ev); ax[r, c].grid(alpha=.25); ax[r, c].set_xlabel("Time [s]")
    ax[0, 0].legend(ncol=3, fontsize=6); ax[0, 3].legend(ncol=2, fontsize=6)
    fig.suptitle(f"{LABEL} on C2t: control references and actuator signals (own axes)"); fig.tight_layout()
    fig.savefig(FIG["references"], dpi=300, bbox_inches="tight"); plt.close(fig)
    # 6 errors to the target equilibrium (both runs against the same xi*)
    fig, ax = plt.subplots(2, 3, figsize=(16, 8))
    for r, (nm, d) in enumerate(zip(names, runs)):
        t = d["time_s"]; p, q, v = e7.unit_series(None, d)
        for i, bus in enumerate(d["unit_bus_ids"]):
            kw = dict(lw=.9, ls="-" if i < n_sg else "--", label=label(i, bus))
            ax[r, 0].plot(t, (p[:, i] - ref["p_star"][i]) * 100, **kw); ax[r, 1].plot(t, q[:, i] - ref["q_star"][i], **kw); ax[r, 2].plot(t, v[:, i] - ref["v_star"][i], **kw)
        ax[r, 0].set_title(nm + ": P - P* [MW]"); ax[r, 1].set_title("Q - Q* [pu]"); ax[r, 2].set_title("V - V* [pu]")
        for c in range(3):
            ax[r, c].axvline(EVENT, **ev); ax[r, c].grid(alpha=.25); ax[r, c].set_xlabel("Time [s]"); ax[r, c].axhline(0, color="k", ls=":", lw=.8)
    ax[0, 0].legend(ncol=3, fontsize=6)
    fig.suptitle(f"{LABEL} on C2t: error with respect to the selected target equilibrium xi*(d) (both runs against the same xi*; own axes)"); fig.tight_layout()
    fig.savefig(FIG["errors"], dpi=300, bbox_inches="tight"); plt.close(fig)


def update_matrix(summary: dict[str, Any]) -> None:
    stage = f"B3_{TAG}"
    with MATRIX_FILE.open("r", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream); fields = list(reader.fieldnames or [])
        rows = [row for row in reader if row.get("stage") != stage]
    m = summary["metrics"]
    row = {k: "" for k in fields}
    row.update({
        "run_id": summary["run_id"], "stage": stage, "case": CASE_LABEL, "scenario": f"{SCEN}_centered_RDC_xi_star_B3A", "baseline": f"E8_C2t_{SCEN}",
        "source_sha256": summary["case_sha256"], "variant_sha256": summary["case_sha256"], "andes_version": summary["andes_version"],
        "git_commit": summary["git_commit"], "seed": "not_applicable_deterministic", "simulation_t0": 0.0, "simulation_tf": TF,
        "solver_settings": json.dumps(summary["solver"], sort_keys=True), "event_time": EVENT, "event_bus": {"P+": "4(P)", "Q+": "21(Q)"}[SCEN], "event_P_MW": e8.SCENARIOS[SCEN].get("p_mw", ""), "event_Q_MVAr": e8.SCENARIOS[SCEN].get("q_mvar", ""),
        "fn_Hz": NOMINAL_FREQUENCY_HZ, "bus_freq_set": "1-39", "bus_volt_set": "1-39", "f_nadir_Hz": m["frequency_nadir_hz"],
        "dae_residual": summary["diagnostics"]["B3"]["final_residual"], "status_auto": summary["status_auto"], "status_human": "PENDING",
        "frequency_figure": FIG["frequency"].relative_to(PROJECT_ROOT).as_posix(), "voltage_figure": FIG["voltage"].relative_to(PROJECT_ROOT).as_posix(),
        "raw_file": RAW_FILE.relative_to(PROJECT_ROOT).as_posix(),
        "decision_note": f"{LABEL} awaits human review; weight sensitivity and E9 stay blocked ({'DEC-040' if SCEN == 'P+' else 'DEC-041'})."})
    with MATRIX_FILE.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(rows + [row])


def main() -> int:
    ref = load_ref()
    _, b2, d2 = b.run("B2", SCEN)
    print("B2 replica done", d2, flush=True)
    _, b3, d3 = b.run("B3", SCEN, ref=ref)
    print("B3 done", d3, flush=True)
    raw8 = np.load(e8.RAW_FILE)
    e8_p = {k[len(SCEN) + 1:]: raw8[k] for k in raw8.files if k.startswith(SCEN + "_")}
    rep = b.replication(b2, e8_p)
    m2, m3 = post_metrics(b2, ref), post_metrics(b3, ref)
    s0 = np.load(ARTIFACTS_DIR / "IEEE39_B3_C2t_S0_timeseries.npz")
    s0_t, s0_v = s0["B3_time_s"], s0["B3_bus_voltage_pu"]
    s0_vmax = float(s0_v[(s0_t >= EVENT - 2) & (s0_t <= EVENT)].mean(axis=0).max())
    s0_vmax_final = float(s0_v[s0_t >= s0_t[-1] - 2.0].mean(axis=0).max())
    checks = {
        "runs_converged": bool(d2["pflow_ok"] and d2["tds_ok"] and d3["pflow_ok"] and d3["tds_ok"] and d3["t_end_s"] >= TF - 1e-6
                               and d2["final_residual"] <= 1e-5 and d3["final_residual"] <= 1e-5),
        "B2_replica_matches_E8": bool(rep["same_time_axis"] and rep["max_abs_frequency_diff_hz"] <= TOL_REPLICATION["f_hz"]
                                      and rep["max_abs_unit_voltage_diff_pu"] <= TOL_REPLICATION["v_pu"]
                                      and max(rep["max_abs_unit_p_diff_pu"], rep["max_abs_unit_q_diff_pu"]) <= TOL_REPLICATION["pq_pu"]
                                      and max(rep["max_abs_pset_diff_pu"], rep["max_abs_qset_diff_pu"]) <= TOL_REPLICATION["ref_pu"]),
        "no_actuator_saturation": not m3["z_clamp_hit"],
        "references_inside_W": m3["min_gp_normalized"] > 0 and m3["min_gq_normalized"] > 0,
        "references_continuous_at_event": bool(m3["pset_continuous_at_event"] and m3["qset_continuous_at_event"]),
        "frequency_converged": abs(m3["final_frequency_error_hz"]) <= TOL["f_hz"],
        "P_converged_to_Pstar": m3["final_max_abs_P_error_pu"] <= TOL["p_pu"],
        "Q_converged_to_Qstar": m3["final_max_abs_Q_error_pu"] <= TOL["q_pu"],
        "V_converged_to_Vstar": m3["final_max_abs_V_error_pu"] <= TOL["v_pu"],
        "Pset_converged_to_Pset_eff": m3["final_max_abs_pset_error_pu"] <= TOL["pset_pu"],
        "Qset_converged_to_Qset_eff": m3["final_max_abs_qset_error_pu"] <= TOL["qset_pu"],
        "no_transient_p_excess_over_pmax": max(m3["transient_p_excess_over_pmax_pu"]) <= 0.0,
    }
    structural = ("runs_converged", "B2_replica_matches_E8", "no_actuator_saturation", "references_inside_W", "references_continuous_at_event")
    status = "FAIL" if not all(checks[k] for k in structural) else ("PASS_AUTO_WAIT_HUMAN" if all(checks.values()) else "FINDINGS_WAIT_HUMAN")
    np.savez_compressed(RAW_FILE, **{f"B3_{k}": v for k, v in b3.items()}, **{f"B2replica_{k}": v for k, v in b2.items()})
    plots(b2, b3, ref)
    case = e8.CASE
    summary = {
        "run_id": f"{PREFIX}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}", "created_utc": datetime.now(timezone.utc).isoformat(),
        "status_auto": status, "status_human": "PENDING", "scenario": SCEN, "failed_checks": [k for k, v in checks.items() if not v],
        "case": str(case.relative_to(PROJECT_ROOT)), "case_sha256": sha256(case), "runner_sha256": sha256(Path(__file__).resolve()),
        "b3_runner_sha256": sha256(Path(b.__file__).resolve()), "e8_runner_sha256": sha256(Path(e8.__file__).resolve()), "graph_sha256": sha256(e8.GRAPH_FILE),
        "b3a_equilibrium_v2_sha256": sha256(V2_FILE), "raw_timeseries_sha256": sha256(RAW_FILE),
        "e8_raw_sha256": sha256(e8.RAW_FILE), "b3_s0_summary_sha256": sha256(b.SUMMARY_FILE),
        "b3_s0_raw_sha256": sha256(ARTIFACTS_DIR / "IEEE39_B3_C2t_S0_timeseries.npz"),
        "git_commit": git_commit(), "python_version": platform.python_version(), "andes_version": andes.__version__,
        "controller": {"kind": "centered RDC v_nom = v_RDC(xi) - v_RDC(xi*(d), d), reference setpoints Pset_eff/Qset_eff of B3-A v2 (not re-optimized); "
                               "E8 law, gains, graph, actuator maps unchanged; xi*(d) uses exact disturbance knowledge (privileged information) available from t = 5 s",
                       "activation_time_s": EVENT, "horizon_s": TF, "time_step_s": e8.TIME_STEP_S, "weights_B3A": "frozen (selection from v2 file)"},
        "solver": {"method": "trapezoid", "time_step_s": e8.TIME_STEP_S, "tf_s": TF, "tolerance": 1e-4, "maximum_iterations": 15},
        "diagnostics": {"B2_replica": d2, "B3": d3}, "metrics": m3, "metrics_B2_replica": m2, "replication_B2_replica_vs_E8": rep,
        "reporting_thresholds_not_tuned": TOL, "checks": checks,
        "S0_note": {"b3_s0_pre_event_max_bus_voltage_pu": s0_vmax, "b3_s0_final_max_bus_voltage_pu": s0_vmax_final, "ac_selection_band_pu": [0.95, 1.05],
                    "text": "B3-S0 preserves the validated pre-event equilibrium, whose bus voltages exceed the 1.05 pu band used by the AC selection; S0 is not a safety certification."},
        "limitations": [f"{SCEN} only; the centered action and xi*(d) use exact disturbance knowledge (privileged information).",
                        "No explicit rate limit exists in the E8 realization, so rates are reported, not checked against a limit.",
                        "No stability, regional-stability or dynamic-safety claim; OPEN-SG31-PMAX stays open; weight sensitivity, E9 and extended horizons not run."]}
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    update_matrix(summary)
    print(status, json.dumps(checks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
