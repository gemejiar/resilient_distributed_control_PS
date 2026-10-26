"""B3 dynamic (centered RDC) on C2t, scenario by scenario (DEC-039).  First delivery: S0 only.

Controller: the E8 original RDC law (run_e8_ieee39) with the centered direction of Eq. (centered),

    v_nom(xi, d) = v_RDC(xi, d) - v_RDC(xi*(d), d),

realized with the *same* E8 actuator maps, gains, graph, capability set, plant C2t, scenarios and horizon.  The
runner reuses ``run_e8_ieee39.configure`` (plant, alter events, graph, limits) and replaces only the controller step.

Three layers are kept apart (DEC-039):
  control reference  (Pset, Qset): the RDC states, in E8 actuator coordinates;
  actuator signal    : SG TGOV1N.paux0 = Pset - Pn;  SG IEEEX1.vref0 = vref0(0) + clip(kappa (Qset - Qn));
                       GFM REGF1.Paux0 / Qaux0 tracking forms that drive PIplim_y -> y0 + Pset - Pn and
                       PIqlim_y -> y0q + Qset - Qn;
  physical power     : P, Q measured at the unit; at omega = 1, SG P = Pset - armature-loss change, GFM P = Pset,
                       GFM Q = PIqlim_y - (V - vref_pre)/Qdrp, SG Q from the network.

Modes: ``B2`` (offset 0; replicates E8 with this code, so B2 and B3 share one realization) and ``B3``
(offset = v_RDC at the reference equilibrium: xi_pre for d = 0 as decided in DEC-038).
"""

from __future__ import annotations

import csv
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ["C2_VARIANT"] = "C2t"

import andes
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import run_e7_ieee39 as e7  # noqa: E402
import run_e8_ieee39 as e8  # noqa: E402
from run_e0_ieee39 import (  # noqa: E402
    ARTIFACTS_DIR, FIGURES_DIR, MATRIX_FILE, NOMINAL_FREQUENCY_HZ, PROJECT_ROOT, extract_time_series, git_commit, sha256,
)
from variant import CASE_LABEL  # noqa: E402

SCENARIO = os.environ.get("B3_SCENARIO", "S0")
PREFIX = f"IEEE39_B3_C2t_{SCENARIO}"
RAW_FILE = ARTIFACTS_DIR / f"{PREFIX}_timeseries.npz"
SUMMARY_FILE = ARTIFACTS_DIR / f"{PREFIX}_summary.json"
FIG = {k: FIGURES_DIR / f"{PREFIX}_{k}.png" for k in ("frequency", "voltage", "power", "rdc_action", "references")}
EVENT_TIME_S, FINAL_TIME_S, V_REF = e8.EVENT_TIME_S, e8.FINAL_TIME_S, e8.V_REF
# Predeclared S0 invariance tolerances (not an improvement criterion)
TOL_F_HZ, TOL_V_PU, TOL_PQ_PU, TOL_REF_PU, TOL_VNOM_ACTIVATION = 1.0e-4, 1.0e-3, 1.0e-3, 1.0e-3, 1.0e-9
TOL_REPLICATION = {"f_hz": 1.0e-6, "v_pu": 1.0e-6, "pq_pu": 1.0e-6, "ref_pu": 1.0e-6}


def run(mode: str, scenario: str, time_step_s: float = e8.TIME_STEP_S, ref: dict[str, np.ndarray] | None = None):
    system, ctx = e8.configure(scenario, time_step_s)
    lim = ctx["lim"]
    n_sg = ctx["n_sg"]
    unit_bus = ctx["unit_bus"]
    log = {k: [] for k in ("t", "pset", "qset", "gp", "gq", "paux", "qaux", "z", "vrdc_p", "vrdc_q", "vnom_p", "vnom_q", "active", "y", "yq")}
    st: dict[str, Any] = {"init": False, "last_t": -1.0}

    def field(pset, qset, p, q, volt, omega):
        gp_raw, gq_raw = e8.capability_factors(pset, qset, lim)
        gp, gq = gp_raw / st["gref_p"], gq_raw / st["gref_q"]
        xp, xq = st["d_p"] * p, st["d_q"] * q
        adj = ctx["adjacency"]
        lp = gp * (adj * gp[None, :] * (xp[:, None] - xp[None, :])).sum(axis=1)
        lq = gq * (adj * gq[None, :] * (xq[:, None] - xq[None, :])).sum(axis=1)
        vp = st["k_ip"] * (gp * (1.0 - omega) - e8.K_P * lp) - e8.K_LEAK * (pset - st["pn"])
        vq = e8.K_IQ * (e8.K_V * gq * (V_REF - volt) - e8.K_Q * lq) - e8.K_LEAK * (qset - st["qn"])
        return vp, vq, gp, gq

    def cb(t, sys_):
        t = float(t)
        y = sys_.dae.y
        if not st["init"]:
            st["a_f"] = np.asarray(sys_.BusFreq.f.a)[[ctx["bus_list"].index(b) for b in unit_bus]]
            st["a_v"] = np.asarray(sys_.Bus.v.a)[[ctx["bus_idx"].index(b) for b in unit_bus]]
            st["a_p"] = np.concatenate([np.asarray(sys_.GENROU.Pe.a), np.asarray(sys_.REGF1.Pe.a)])
            st["a_q"] = np.concatenate([np.asarray(sys_.GENROU.Qe.a), np.asarray(sys_.REGF1.Qe.a)])
            st["a_y"], st["a_yq"] = np.asarray(sys_.REGF1.PIplim_y.a), np.asarray(sys_.REGF1.PIqlim_y.a)
            st["pn"], st["qn"] = np.asarray(y[st["a_p"]], float).copy(), np.asarray(y[st["a_q"]], float).copy()
            st["pset"], st["qset"] = st["pn"].copy(), st["qn"].copy()
            st["y0"], st["y0q"] = np.asarray(y[st["a_y"]], float).copy(), np.asarray(y[st["a_yq"]], float).copy()
            st["vref0_sg"] = np.asarray(sys_.IEEEX1.vref0.v, float).copy()
            gp0, gq0 = e8.capability_factors(st["pset"], st["qset"], lim)
            if np.any(gp0 <= 0) or np.any(gq0 <= 0):
                raise RuntimeError("Nominal setpoint is not in the interior of W_i.")
            st["gref_p"], st["gref_q"] = gp0.max(), gq0.max()
            st["k_ip"] = e8.SPEED_TARGET / float((gp0 / st["gref_p"]).sum())
            st["d_p"] = 1.0 / st["pn"]
            st["d_q"] = 1.0 / (lim["qmax"] - lim["qmin"])
            volt0 = np.asarray(y[st["a_v"]], float)
            # reference equilibrium for d = 0: xi_pre (omega = 1, P = Pn, Q = Qn, setpoints at nominal)
            op, oq, _, _ = field(st["pn"], st["qn"], st["pn"], st["qn"], volt0, 1.0)
            st["off_p"], st["off_q"] = (op, oq) if mode == "B3" else (np.zeros_like(op), np.zeros_like(oq))
            st["off_pre_p"], st["off_pre_q"] = op, oq
            if mode == "B3" and ref is not None:  # post-event reference xi*(d), selected in advance (B3-A v2), not re-optimized
                st["off_p"], st["off_q"], _, _ = field(ref["pset_eff"], ref["qset_eff"], ref["p_star"], ref["q_star"], ref["v_star"], 1.0)
            st["init"] = True
        if t <= st["last_t"]:
            return
        st["last_t"] = t
        dt = ctx["h"]
        omega = np.asarray(y[st["a_f"]], float)
        volt = np.asarray(y[st["a_v"]], float)
        p_now, q_now = np.asarray(y[st["a_p"]], float), np.asarray(y[st["a_q"]], float)
        vp, vq, gp, gq = field(st["pset"], st["qset"], p_now, q_now, volt, omega)
        vnom_p, vnom_q = vp - st["off_p"], vq - st["off_q"]
        active = t >= EVENT_TIME_S
        if active:
            st["pset"] = st["pset"] + dt * vnom_p
            st["qset"] = st["qset"] + dt * vnom_q
        sys_.TGOV1N.paux0.v[ctx["tg_pos"]] = (st["pset"] - st["pn"])[:n_sg]
        paux = e8.KC_GFM * (st["y0"] + (st["pset"] - st["pn"])[n_sg:] - np.asarray(y[st["a_y"]], float))
        sys_.REGF1.Paux0.v[:] = paux
        z = np.clip(e8.KAPPA_SG * (st["qset"] - st["qn"])[:n_sg], -e8.Z_CLAMP, e8.Z_CLAMP)
        sys_.IEEEX1.vref0.v[ctx["ex_pos"]] = st["vref0_sg"][ctx["ex_pos"]] + z
        qaux = e8.KCQ_GFM * (st["y0q"] + (st["qset"] - st["qn"])[n_sg:] - np.asarray(y[st["a_yq"]], float))
        sys_.REGF1.Qaux0.v[:] = qaux
        for key, val in (("t", t), ("pset", st["pset"].copy()), ("qset", st["qset"].copy()), ("gp", gp.copy()), ("gq", gq.copy()),
                         ("paux", paux.copy()), ("qaux", qaux.copy()), ("z", z.copy()), ("vrdc_p", vp.copy()), ("vrdc_q", vq.copy()),
                         ("vnom_p", vnom_p.copy()), ("vnom_q", vnom_q.copy()), ("active", float(active)),
                         ("y", np.asarray(y[st["a_y"]], float).copy()), ("yq", np.asarray(y[st["a_yq"]], float).copy())):
            log[key].append(val)

    system.TDS.callpert = cb
    pflow_ok = bool(system.PFlow.run())
    tds_ok = bool(system.TDS.run(no_summary=True)) if pflow_ok else False
    data = extract_time_series(system)
    y = system.dae.ts.y
    data["sg_p_pu"] = np.asarray(y[:, system.GENROU.Pe.a], dtype=float)
    data["sg_q_pu"] = np.asarray(y[:, system.GENROU.Qe.a], dtype=float)
    data["gfm_bus_ids"] = np.asarray(system.REGF1.bus.v, dtype=int)
    data["gfm_p_pu"] = np.asarray(y[:, system.REGF1.Pe.a], dtype=float)
    data["gfm_q_pu"] = np.asarray(y[:, system.REGF1.Qe.a], dtype=float)
    data["unit_bus_ids"] = np.asarray(unit_bus, dtype=int)
    for key, vals in log.items():
        data[f"cmd_{key}"] = np.asarray(vals)
    data["unit_pn"], data["unit_qn"] = st["pn"], st["qn"]
    for key in ("pmax", "pmin", "qmax", "qmin", "smax"):
        data[f"unit_{key}"] = lim[key]
    data["offset_p"], data["offset_q"] = st["off_p"], st["off_q"]
    data["offset_pre_p"], data["offset_pre_q"] = st["off_pre_p"], st["off_pre_q"]
    data["unit_y0"], data["unit_y0q"] = st["y0"], st["y0q"]
    diag = {"pflow_ok": pflow_ok, "tds_ok": tds_ok, "final_residual": float(np.max(np.abs(system.dae.g))),
            "t_end_s": float(system.dae.ts.t[-1]), "k_ip": float(st["k_ip"])}
    return system, data, diag


def metrics(data: dict[str, np.ndarray], pre_window=(EVENT_TIME_S - 2.0, EVENT_TIME_S)) -> dict[str, Any]:
    t = data["time_s"]
    p, q, v = e7.unit_series(None, data)
    pre = (t >= pre_window[0]) & (t <= pre_window[1])
    p0, q0, v0 = p[pre].mean(axis=0), q[pre].mean(axis=0), v[pre].mean(axis=0)
    f = data["bus_frequency_hz"].mean(axis=1)
    ct = data["cmd_t"]
    pset, qset, gp, gq, z = data["cmd_pset"], data["cmd_qset"], data["cmd_gp"], data["cmd_gq"], data["cmd_z"]
    pn, qn = data["unit_pn"], data["unit_qn"]
    act = ct >= EVENT_TIME_S
    pmax, pmin, qmax, qmin, smax = (data[f"unit_{k}"] for k in ("pmax", "pmin", "qmax", "qmin", "smax"))
    post_event = t >= EVENT_TIME_S
    out = {
        "max_abs_frequency_deviation_hz": float(np.abs(f - NOMINAL_FREQUENCY_HZ).max()),
        "max_abs_frequency_deviation_after_activation_hz": float(np.abs(f[post_event] - NOMINAL_FREQUENCY_HZ).max()),
        "final_frequency_error_hz": float(e7.window(t, f, t[-1] - 2.0, t[-1] + 1e-9) - NOMINAL_FREQUENCY_HZ),
        "max_abs_voltage_change_from_pre_pu": float(np.abs(v[post_event] - v0).max()),
        "max_abs_voltage_change_per_unit_pu": np.abs(v[post_event] - v0).max(axis=0).tolist(),
        "final_unit_voltage_pu": e7.window(t, v, t[-1] - 2.0, t[-1] + 1e-9).tolist(),
        "pre_unit_voltage_pu": v0.tolist(),
        "max_abs_p_change_from_pre_pu": float(np.abs(p[post_event] - p0).max()),
        "max_abs_q_change_from_pre_pu": float(np.abs(q[post_event] - q0).max()),
        "max_abs_p_change_per_unit_pu": np.abs(p[post_event] - p0).max(axis=0).tolist(),
        "max_abs_q_change_per_unit_pu": np.abs(q[post_event] - q0).max(axis=0).tolist(),
        "max_abs_pset_minus_pn_pu": float(np.abs(pset - pn).max()), "max_abs_qset_minus_qn_pu": float(np.abs(qset - qn).max()),
        "max_abs_pset_minus_pn_per_unit_pu": np.abs(pset - pn).max(axis=0).tolist(),
        "max_abs_qset_minus_qn_per_unit_pu": np.abs(qset - qn).max(axis=0).tolist(),
        **({"max_abs_vnom_p_after_activation_pu_per_s": float(np.abs(data["cmd_vnom_p"][act]).max()),
            "max_abs_vnom_q_after_activation_pu_per_s": float(np.abs(data["cmd_vnom_q"][act]).max()),
            "vnom_at_activation_first_step_max_abs": float(max(np.abs(data["cmd_vnom_p"][act][0]).max(), np.abs(data["cmd_vnom_q"][act][0]).max())),
            "max_abs_vrdc_p_after_activation_pu_per_s": float(np.abs(data["cmd_vrdc_p"][act]).max()),
            "max_abs_vrdc_q_after_activation_pu_per_s": float(np.abs(data["cmd_vrdc_q"][act]).max()),
            "offset_p_pu_per_s": data["offset_p"].tolist(), "offset_q_pu_per_s": data["offset_q"].tolist()} if "cmd_vnom_p" in data else {}),
        "actuator_max_abs_paux": float(np.abs(data["cmd_paux"]).max()), "actuator_max_abs_qaux": float(np.abs(data["cmd_qaux"]).max()),
        "actuator_max_abs_z_pu": float(np.abs(z).max()), "actuator_z_clamp_margin_min_pu": float(e8.Z_CLAMP - np.abs(z).max()),
        "z_clamp_hit": bool(np.any(np.abs(z) >= e8.Z_CLAMP - 1e-12)),
        "min_gp_normalized": float(gp.min()), "min_gq_normalized": float(gq.min()),
        "reference_margin_to_pmax_min_per_unit_pu": (pmax - pset).min(axis=0).tolist(),
        "reference_margin_to_qmax_min_per_unit_pu": (qmax - qset).min(axis=0).tolist(),
        "reference_margin_to_qmin_min_per_unit_pu": (qset - qmin).min(axis=0).tolist(),
        "reference_s_rel_margin_min_per_unit": (1 - np.hypot(pset, qset) / smax).min(axis=0).tolist(),
        "physical_margin_to_pmax_min_per_unit_pu": (pmax - p).min(axis=0).tolist(),
        "physical_margin_to_qmax_min_per_unit_pu": (qmax - q).min(axis=0).tolist(),
        "physical_margin_to_qmin_min_per_unit_pu": (q - qmin).min(axis=0).tolist(),
        "physical_s_rel_margin_min_per_unit": (1 - np.hypot(p, q) / smax).min(axis=0).tolist(),
        "transient_p_excess_over_pmax_pu": np.maximum(0.0, p.max(axis=0) - pmax).tolist(),
        "unit_bus_ids": data["unit_bus_ids"].tolist()}
    sg35 = out["unit_bus_ids"].index(35)
    out["sg35"] = {"reference_margin_to_pmax_min_pu": out["reference_margin_to_pmax_min_per_unit_pu"][sg35],
                   "physical_margin_to_pmax_min_pu": out["physical_margin_to_pmax_min_per_unit_pu"][sg35]}
    return out


def replication(b2: dict[str, np.ndarray], ref: dict[str, np.ndarray]) -> dict[str, float]:
    """B2 replicated with this runner against the stored E8 series of the same scenario."""
    n = min(len(b2["time_s"]), len(ref["time_s"]))
    p, q, v = e7.unit_series(None, b2)
    pr, qr, vr = e7.unit_series(None, ref)
    return {"samples_compared": int(n), "same_time_axis": bool(np.allclose(b2["time_s"][:n], ref["time_s"][:n])),
            "max_abs_frequency_diff_hz": float(np.abs(b2["bus_frequency_hz"][:n] - ref["bus_frequency_hz"][:n]).max()),
            "max_abs_unit_voltage_diff_pu": float(np.abs(v[:n] - vr[:n]).max()),
            "max_abs_unit_p_diff_pu": float(np.abs(p[:n] - pr[:n]).max()), "max_abs_unit_q_diff_pu": float(np.abs(q[:n] - qr[:n]).max()),
            "max_abs_pset_diff_pu": float(np.abs(b2["cmd_pset"][:n] - ref["cmd_pset"][:n]).max()),
            "max_abs_qset_diff_pu": float(np.abs(b2["cmd_qset"][:n] - ref["cmd_qset"][:n]).max())}


def plots(b2: dict[str, np.ndarray], b3: dict[str, np.ndarray]) -> None:
    names = ("B2 (original RDC; replica of E8)", "B3-S0 (centered RDC, reference xi_pre)")
    runs = (b2, b3)
    n_sg = b3["sg_p_pu"].shape[1]
    label = lambda i, b: f"{'SG' if i < n_sg else 'GFM'}{b}"  # noqa: E731
    # frequency
    fig, ax = plt.subplots(2, 2, figsize=(13, 8))
    for c, (nm, d) in enumerate(zip(names, runs)):
        t, f = d["time_s"], d["bus_frequency_hz"]
        ax[0, c].fill_between(t, f.min(1), f.max(1), color="0.85", label="39-bus envelope")
        ax[0, c].plot(t, f.mean(1), "tab:blue", lw=1.0, label="mean bus frequency")
        ax[0, c].axhline(60, color="k", ls=":", lw=.8); ax[0, c].set_ylim(59.97, 60.01); ax[0, c].set_title(nm)
        dev = (f - 60.0) * 1e3
        ax[1, c].fill_between(t, dev.min(1), dev.max(1), color="0.85"); ax[1, c].plot(t, dev.mean(1), "tab:blue", lw=1.0)
        ax[1, c].axhline(0, color="k", ls=":", lw=.8); ax[1, c].set_title("zoom: f - 60 Hz [mHz] (own axis)"); ax[1, c].set_xlim(0, 60)
        for r in range(2):
            ax[r, c].axvline(EVENT_TIME_S, color="tab:red", ls=":", lw=.8, label="controller activation (t = 5 s)"); ax[r, c].grid(alpha=.25)
            ax[r, c].set_xlabel("Time [s]")
    ax[0, 0].set_ylabel("Frequency [Hz]"); ax[1, 0].set_ylabel("f - 60 Hz [mHz]"); ax[0, 0].legend(fontsize=7)
    fig.suptitle("B3-S0 on C2t (no load event): bus frequency"); fig.tight_layout(); fig.savefig(FIG["frequency"], dpi=300, bbox_inches="tight"); plt.close(fig)
    # voltage
    fig, ax = plt.subplots(2, 2, figsize=(13, 8))
    for c, (nm, d) in enumerate(zip(names, runs)):
        t = d["time_s"]; _, _, v = e7.unit_series(None, d)
        v0 = v[(t >= EVENT_TIME_S - 2) & (t <= EVENT_TIME_S)].mean(axis=0)
        for i, b in enumerate(d["unit_bus_ids"]):
            st = dict(lw=.9, ls="-" if i < n_sg else "--", label=label(i, b))
            ax[0, c].plot(t, v[:, i], **st); ax[1, c].plot(t, (v[:, i] - v0[i]) * 1e3, **st)
        ax[0, c].axhline(V_REF, color="k", ls=":", lw=.8); ax[0, c].set_title(nm)
        ax[1, c].set_title("unit-bus voltage change from its pre-activation value [10^-3 pu] (own axis)")
        for r in range(2):
            ax[r, c].axvline(EVENT_TIME_S, color="tab:red", ls=":", lw=.8); ax[r, c].grid(alpha=.25); ax[r, c].set_xlabel("Time [s]")
    ax[0, 0].set_ylabel("Unit-bus |V| [pu]"); ax[1, 0].set_ylabel("Delta |V| [10^-3 pu]"); ax[0, 0].legend(ncol=3, fontsize=6)
    fig.suptitle("B3-S0 on C2t: voltage at the ten unit buses"); fig.tight_layout(); fig.savefig(FIG["voltage"], dpi=300, bbox_inches="tight"); plt.close(fig)
    # physical power
    fig, ax = plt.subplots(2, 2, figsize=(13, 8))
    for c, (nm, d) in enumerate(zip(names, runs)):
        t = d["time_s"]; p, q, _ = e7.unit_series(None, d)
        for i, b in enumerate(d["unit_bus_ids"]):
            st = dict(lw=.9, ls="-" if i < n_sg else "--", label=label(i, b))
            ax[0, c].plot(t, (p[:, i] - d["unit_pn"][i]) * 100, **st); ax[1, c].plot(t, (q[:, i] - d["unit_qn"][i]) * 100, **st)
        ax[0, c].set_title(nm + ": physical P - Pn [MW]"); ax[1, c].set_title("physical Q - Qn [MVAr]")
        for r in range(2):
            ax[r, c].axvline(EVENT_TIME_S, color="tab:red", ls=":", lw=.8); ax[r, c].grid(alpha=.25); ax[r, c].set_xlabel("Time [s]")
    ax[0, 0].legend(ncol=3, fontsize=6)
    fig.suptitle("B3-S0 on C2t: physical active and reactive power of the ten units (own axes)")
    fig.tight_layout(); fig.savefig(FIG["power"], dpi=300, bbox_inches="tight"); plt.close(fig)
    # RDC actions
    fig, ax = plt.subplots(2, 3, figsize=(16, 8))
    for r, (key, unit) in enumerate((("p", "pu/s"), ("q", "pu/s"))):
        for i, b in enumerate(b3["unit_bus_ids"]):
            st = dict(lw=.9, ls="-" if i < n_sg else "--", label=label(i, b))
            ax[r, 0].plot(b2["cmd_t"], b2[f"cmd_vrdc_{key}"][:, i], **st)
            ax[r, 1].plot(b3["cmd_t"], b3[f"cmd_vrdc_{key}"][:, i], **st)
            ax[r, 2].plot(b3["cmd_t"], b3[f"cmd_vnom_{key}"][:, i], **st)
        ax[r, 0].set_title(f"B2: applied original RDC field v_RDC,{key.upper()} [{unit}]")
        ax[r, 1].set_title(f"B3: original field v_RDC,{key.upper()} along the B3 trajectory")
        ax[r, 2].set_title(f"B3: centered action v_nom,{key.upper()} = v_RDC - v_RDC(xi_pre)")
        for c in range(3):
            ax[r, c].axvline(EVENT_TIME_S, color="tab:red", ls=":", lw=.8); ax[r, c].grid(alpha=.25); ax[r, c].set_xlabel("Time [s]")
    ax[0, 0].legend(ncol=3, fontsize=6)
    fig.suptitle("B3-S0 on C2t: original and centered RDC actions (own axes)"); fig.tight_layout()
    fig.savefig(FIG["rdc_action"], dpi=300, bbox_inches="tight"); plt.close(fig)
    # references and actuator signals
    fig, ax = plt.subplots(2, 3, figsize=(16, 8))
    for r, (nm, d) in enumerate(zip(names, runs)):
        for i, b in enumerate(d["unit_bus_ids"]):
            st = dict(lw=.9, ls="-" if i < n_sg else "--", label=label(i, b))
            ax[r, 0].plot(d["cmd_t"], d["cmd_pset"][:, i] - d["unit_pn"][i], **st)
            ax[r, 1].plot(d["cmd_t"], d["cmd_qset"][:, i] - d["unit_qn"][i], **st)
        for i in range(n_sg):
            ax[r, 2].plot(d["cmd_t"], d["cmd_z"][:, i], lw=.9, label=f"SG{d['unit_bus_ids'][i]} exciter z")
        ax[r, 2].axhline(e8.Z_CLAMP, color="k", ls="--", lw=.7); ax[r, 2].axhline(-e8.Z_CLAMP, color="k", ls="--", lw=.7)
        ax[r, 0].set_title(nm + ": Pset - Pn [pu]"); ax[r, 1].set_title("Qset - Qn [pu]"); ax[r, 2].set_title("SG exciter reference offset z [pu] (dashed: clamp)")
        for c in range(3):
            ax[r, c].axvline(EVENT_TIME_S, color="tab:red", ls=":", lw=.8); ax[r, c].grid(alpha=.25); ax[r, c].set_xlabel("Time [s]")
    ax[0, 0].legend(ncol=3, fontsize=6)
    fig.suptitle("B3-S0 on C2t: control references and actuator signals (own axes)"); fig.tight_layout()
    fig.savefig(FIG["references"], dpi=300, bbox_inches="tight"); plt.close(fig)


def update_matrix(summary: dict[str, Any]) -> None:
    stage = f"B3_{SCENARIO}"
    with MATRIX_FILE.open("r", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream); fields = list(reader.fieldnames or [])
        rows = [row for row in reader if row.get("stage") != stage]
    m = summary["metrics"]
    row = {key: "" for key in fields}
    row.update({
        "run_id": summary["run_id"], "stage": stage, "case": CASE_LABEL, "scenario": f"{SCENARIO}_centered_RDC_xi_pre", "baseline": f"E8_C2t_{SCENARIO}",
        "source_sha256": summary["case_sha256"], "variant_sha256": summary["case_sha256"], "andes_version": summary["andes_version"],
        "git_commit": summary["git_commit"], "seed": "not_applicable_deterministic", "simulation_t0": 0.0, "simulation_tf": FINAL_TIME_S,
        "solver_settings": json.dumps(summary["solver"], sort_keys=True), "event_time": EVENT_TIME_S, "event_bus": "none (S0)",
        "fn_Hz": NOMINAL_FREQUENCY_HZ, "bus_freq_set": "1-39", "bus_volt_set": "1-39",
        "f_nadir_Hz": 60.0 - m["max_abs_frequency_deviation_hz"],
        "dae_residual": summary["diagnostics"]["B3"]["final_residual"], "status_auto": summary["status_auto"], "status_human": "PENDING",
        "frequency_figure": FIG["frequency"].relative_to(PROJECT_ROOT).as_posix(), "voltage_figure": FIG["voltage"].relative_to(PROJECT_ROOT).as_posix(),
        "raw_file": RAW_FILE.relative_to(PROJECT_ROOT).as_posix(),
        "decision_note": "B3-S0 awaits human review; P+ and Q+ and E9 stay blocked (DEC-039)."})
    with MATRIX_FILE.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(rows + [row])


def main() -> int:
    if SCENARIO != "S0":
        raise SystemExit("Only B3-S0 is authorized in this delivery (DEC-039).")
    _, b2, d2 = run("B2", SCENARIO)
    print("B2 replica done", d2, flush=True)
    _, b3, d3 = run("B3", SCENARIO)
    print("B3 done", d3, flush=True)
    raw8 = np.load(e8.RAW_FILE)
    e8_s0 = {k[len(SCENARIO) + 1:]: raw8[k] for k in raw8.files if k.startswith(SCENARIO + "_")}
    rep = replication(b2, e8_s0)
    m2, m3, m8 = metrics(b2), metrics(b3), metrics(e8_s0)
    checks = {
        "plant_is_C2t": True,
        "runs_converged": bool(d2["pflow_ok"] and d2["tds_ok"] and d3["pflow_ok"] and d3["tds_ok"] and d3["t_end_s"] >= FINAL_TIME_S - 1e-6
                               and d2["final_residual"] <= 1e-5 and d3["final_residual"] <= 1e-5),
        "B2_replica_matches_E8": bool(rep["same_time_axis"] and rep["max_abs_frequency_diff_hz"] <= TOL_REPLICATION["f_hz"]
                                      and rep["max_abs_unit_voltage_diff_pu"] <= TOL_REPLICATION["v_pu"]
                                      and max(rep["max_abs_unit_p_diff_pu"], rep["max_abs_unit_q_diff_pu"]) <= TOL_REPLICATION["pq_pu"]
                                      and max(rep["max_abs_pset_diff_pu"], rep["max_abs_qset_diff_pu"]) <= TOL_REPLICATION["ref_pu"]),
        "vnom_zero_at_activation": m3["vnom_at_activation_first_step_max_abs"] <= TOL_VNOM_ACTIVATION,
        "frequency_invariant": m3["max_abs_frequency_deviation_after_activation_hz"] <= TOL_F_HZ,
        "voltage_invariant": m3["max_abs_voltage_change_from_pre_pu"] <= TOL_V_PU,
        "power_invariant": max(m3["max_abs_p_change_from_pre_pu"], m3["max_abs_q_change_from_pre_pu"]) <= TOL_PQ_PU,
        "references_invariant": max(m3["max_abs_pset_minus_pn_pu"], m3["max_abs_qset_minus_qn_pu"]) <= TOL_REF_PU,
        "no_actuator_saturation": not m3["z_clamp_hit"],
        "references_inside_W": m3["min_gp_normalized"] > 0 and m3["min_gq_normalized"] > 0,
    }
    status = "PASS_AUTO_WAIT_HUMAN" if all(checks.values()) else "FAIL"
    np.savez_compressed(RAW_FILE, **{f"B3_{k}": v for k, v in b3.items()}, **{f"B2replica_{k}": v for k, v in b2.items()})
    plots(b2, b3)
    case = e8.CASE
    summary = {
        "run_id": f"{PREFIX}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}", "created_utc": datetime.now(timezone.utc).isoformat(),
        "status_auto": status, "status_human": "PENDING", "scenario": SCENARIO,
        "case": str(case.relative_to(PROJECT_ROOT)), "case_sha256": sha256(case), "runner_sha256": sha256(Path(__file__).resolve()),
        "e8_runner_sha256": sha256(Path(e8.__file__).resolve()), "graph_sha256": sha256(e8.GRAPH_FILE),
        "b3a_equilibrium_sha256": sha256(ARTIFACTS_DIR / "IEEE39_B3A_C2t_equilibrium_v2.json"),
        "git_commit": git_commit(), "python_version": platform.python_version(), "andes_version": andes.__version__,
        "controller": {"kind": "centered RDC v_nom = v_RDC(xi) - v_RDC(xi*), reference xi_pre for d = 0 (DEC-038); E8 law, gains, graph, actuator maps unchanged",
                       "frozen_from_E8": {"speed_target": e8.SPEED_TARGET, "k_P": e8.K_P, "k_leak": e8.K_LEAK, "k_IQ": e8.K_IQ, "k_V": e8.K_V, "k_Q": e8.K_Q,
                                          "kc_gfm": e8.KC_GFM, "kcq_gfm": e8.KCQ_GFM, "kappa_sg": e8.KAPPA_SG, "z_clamp": e8.Z_CLAMP},
                       "activation_time_s": EVENT_TIME_S, "horizon_s": FINAL_TIME_S, "time_step_s": e8.TIME_STEP_S,
                       "weights_B3A": "not used in S0 (xi_pre); frozen, no sensitivity run"},
        "solver": {"method": "trapezoid", "time_step_s": e8.TIME_STEP_S, "tf_s": FINAL_TIME_S, "tolerance": 1e-4, "maximum_iterations": 15},
        "diagnostics": {"B2_replica": d2, "B3": d3}, "metrics": m3, "metrics_B2_replica": m2, "metrics_E8_stored": m8,
        "replication_B2_replica_vs_E8": rep, "predeclared_tolerances": {"frequency_hz": TOL_F_HZ, "voltage_pu": TOL_V_PU, "power_pu": TOL_PQ_PU,
                                                                           "reference_pu": TOL_REF_PU, "vnom_at_activation": TOL_VNOM_ACTIVATION,
                                                                           "replication": TOL_REPLICATION},
        "checks": checks,
        "limitations": ["S0 only: no load event; the check is invariance of the nominal equilibrium, not performance.",
                        "B3 in S0 does not regulate voltage toward 1.0 pu by construction (reference xi_pre), unlike B2.",
                        "No stability, regional-stability, safety or physical P/Q invariance claim; OPEN-SG31-PMAX remains open."]}
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    update_matrix(summary)
    print(status, json.dumps(checks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
