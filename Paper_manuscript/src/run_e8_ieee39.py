"""E8--C2t: original RDC (bounded-integral capability-aware consensus) on the retuned plant C2t.

Plant: C2t only (DEC-030, conditions 1-2); the runner refuses any other ``C2_VARIANT``.
Controller: Eqs. (26)--(35) of the reference paper (Kavvathas et al., IEEE TPWRS 2025) as
reproduced in Eq. (rdc)--(laplacians) of main.tex, **without** centering, barrier or CLF layers:

  dPset/dt = kIP ( [gP](1 - omega) - kP LP dP P ) - k (Pset - Pn)
  dQset/dt = kIQ ( kV [gQ](Vref - V) - kQ LQ dQ Q ) - k (Qset - Qn)
  LP = [gP][A gP] - [gP] A [gP],  LQ likewise;  Vref = 1.0 pu, omega_S = 1 pu.

Capability set W_i (DEC-023): GFM exactly as Eqs. (30)--(31) with Smax = Sn/100, Pmax = case pmax,
Pmin = 0; SG as Eq. (28)--(29) with the excitation-limit and iron-core terms (24)--(25) replaced by
the case plant limits qmin/qmax (the ANDES SG has no capability-curve parameters).  Declared
adaptations: dP_i = 1/Pn_i, dQ_i = 1/(qmax_i - qmin_i); g scaled by one scalar per channel
(absorbed in the gains); graph = E6 graph; leakage k small.

Actuation (DEC-032): Pset -> SG paux0 = Pset - Pn, GFM Paux0 = KC (y0 + Pset - Pn - y);
Qset -> inner tracking of the measured Q: GFM Qaux0 = KCQ (Qset - Q), SG dvref0/dt = KZ (Qset - Q).
Scenarios and plant identical to E7t: S0, P+ (+58.564 MW, bus 4), Q+ (+17.345 MVAr, bus 21) at t = 5 s.
"""

from __future__ import annotations

import csv
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import andes
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import run_e5_ieee39 as e5  # noqa: E402
import run_e7_ieee39 as e7  # noqa: E402
from run_e0_ieee39 import (  # noqa: E402
    ARTIFACTS_DIR, FIGURES_DIR, MATRIX_FILE, NOMINAL_FREQUENCY_HZ, PROJECT_ROOT,
    extract_time_series, git_commit, sha256,
)
from variant import CASE_LABEL, VARIANT  # noqa: E402

if VARIANT != "C2t":
    raise SystemExit("E8 runs on C2t only (DEC-030, condition 2); set C2_VARIANT=C2t.")

CASE = e5.CASE
PREFIX = "IEEE39_E8_C2t"
RAW_FILE = ARTIFACTS_DIR / f"{PREFIX}_timeseries.npz"
SUMMARY_FILE = ARTIFACTS_DIR / f"{PREFIX}_summary.json"
GRAPH_FILE = e7.GRAPH_FILE
FREQUENCY_FIGURE = FIGURES_DIR / f"{PREFIX}_frequency.png"
VOLTAGE_FIGURE = FIGURES_DIR / f"{PREFIX}_voltage.png"
SECONDARY_FIGURE = FIGURES_DIR / f"{PREFIX}_secondary.png"

EVENT_TIME_S = e5.EVENT_TIME_S
FINAL_TIME_S = 200.0
TIME_STEP_S = e5.TIME_STEP_S
REFINED_TIME_STEP_S = e5.REFINED_TIME_STEP_S
BASE_MVA = 100.0
SCENARIOS = e7.SCENARIOS
V_REF = 1.0
# A-priori gains (DEC-033); not tuned.
SPEED_TARGET = 160.0           # kIP * sum(g_P normalized) at nominal, same integral speed as E7 (60 x 2.69)
K_P, K_LEAK = 0.1, 1.0e-3
# Attempt 1 (K_IQ 1.2) failed: sustained 45 s unit-voltage oscillation, +/-0.05 pu (DEC-034).
K_IQ, K_V, K_Q = 0.3, 1.0, 0.01
# Attempt 2 (K_IQ 0.3, inner KCQ/KZ 0.02) failed: double-integrator cascade with a slow inner Q loop, ~100 s
# oscillation saturating z (DEC-034).  Attempt 3 speeds the inner Q loops 5x.
# Attempt 3 (inner KCQ/KZ 0.1) diverged.  Attempt 4 removes the inner Q integrator: proportional Qset -> vref map
# (SG, kappa from the E7.0 sensitivities dQ/dvref ~ 17 pu/pu) and reference tracking of PIqlim_y (GFM, as for P).
KC_GFM, KCQ_GFM, KAPPA_SG, Z_CLAMP = 0.05, 0.05, 0.06, 0.10


def capability_factors(pset: np.ndarray, qset: np.ndarray, lim: dict[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    """Raw gP, gQ of Eqs. (28)--(31) with the declared SG substitution; clipped at 0 outside W_i."""
    circle = 1.0 - (pset ** 2 + qset ** 2) / lim["smax"] ** 2
    box_q = (lim["qmax"] - qset) * (qset - lim["qmin"]) / ((lim["qmax"] - lim["qmin"]) / 2.0) ** 2
    box_p = (lim["pmax"] - pset) * (pset - lim["pmin"])
    sg = lim["is_sg"]
    g_p = box_p * circle * np.where(sg, box_q, 1.0)
    g_q = circle * np.where(sg, box_q, 1.0)
    return np.maximum(g_p, 0.0), np.maximum(g_q, 0.0)


def configure(scenario: str, time_step_s: float) -> tuple[Any, dict[str, Any]]:
    spec = SCENARIOS[scenario]
    system = andes.load(str(CASE), setup=False, default_config=True, no_output=True)
    system.PQ.config.p2p, system.PQ.config.p2i, system.PQ.config.p2z = 1.0, 0.0, 0.0
    system.PQ.config.q2q, system.PQ.config.q2i, system.PQ.config.q2z = 1.0, 0.0, 0.0
    for channel, bus, key, src in (("P", 4, "p_mw", "Ppf"), ("Q", 21, "q_mvar", "Qpf")):
        if key in spec:
            dev = [str(i) for i, b in zip(system.PQ.idx.v, system.PQ.bus.v) if int(b) == bus]
            if len(dev) != 1:
                raise RuntimeError(f"Expected one PQ at bus {bus}; found {dev}.")
            system.add("Alter", idx=f"E8_{channel}", t=EVENT_TIME_S, model="PQ", dev=dev[0], src=src,
                       attr="v", method="+", amount=spec[key] / BASE_MVA)
    if "toggle_line" in spec:   # E15 (N-1): optional line outage at the event time; historical scenarios never carry this key
        system.add("Toggle", idx="E15_N1", model="Line", dev=spec["toggle_line"], t=EVENT_TIME_S)
    system.setup()
    system.TDS.config.tf = FINAL_TIME_S
    system.TDS.config.tstep = time_step_s
    system.TDS.config.fixt = 1
    system.TDS.config.no_tqdm = 1

    graph = json.loads(GRAPH_FILE.read_text(encoding="utf-8"))
    sg_bus = [int(b) for b in system.GENROU.bus.v]
    gfm_bus = [int(b) for b in system.REGF1.bus.v]
    unit_bus = sg_bus + gfm_bus
    n_sg, n = len(sg_bus), len(unit_bus)
    pos = {b: i for i, b in enumerate(unit_bus)}
    adjacency = np.zeros((n, n))
    for u, v in graph["edges"]:
        adjacency[pos[u], pos[v]] = adjacency[pos[v], pos[u]] = graph["weights"]
    case_lim = e7.static_limits(system)
    sn_pu = np.concatenate([np.asarray(system.GENROU.Sn.v, float), np.asarray(system.REGF1.Sn.v, float)]) / BASE_MVA
    lim = {"pmax": np.array([case_lim[b]["pmax"] for b in unit_bus]), "pmin": np.zeros(n),
           "qmax": np.array([case_lim[b]["qmax"] for b in unit_bus]),
           "qmin": np.array([case_lim[b]["qmin"] for b in unit_bus]), "smax": sn_pu,
           "is_sg": np.arange(n) < n_sg}
    ctx = {
        "unit_bus": unit_bus, "n_sg": n_sg, "adjacency": adjacency, "lim": lim, "sn_pu": sn_pu,
        "tg_pos": [list(system.TGOV1N.syn.v).index(g) for g in system.GENROU.idx.v],
        "ex_pos": [list(system.IEEEX1.syn.v).index(g) for g in system.GENROU.idx.v],
        "bus_list": list(system.BusFreq.bus.v), "bus_idx": list(system.Bus.idx.v), "h": time_step_s,
        "last_t": -1.0, "init": None, "z": np.zeros(n_sg),
        "log": {k: [] for k in ("t", "pset", "qset", "gp", "gq", "paux", "qaux", "z")},
    }

    def rdc(t: Any, sys_: Any) -> None:
        t = float(t)  # ``dae.t`` is mutated in place
        y = sys_.dae.y
        if ctx["init"] is None:  # variable addresses exist only after TDS initialization
            ctx["a_f"] = np.asarray(sys_.BusFreq.f.a)[[ctx["bus_list"].index(b) for b in unit_bus]]
            ctx["a_v"] = np.asarray(sys_.Bus.v.a)[[ctx["bus_idx"].index(b) for b in unit_bus]]
            ctx["a_p"] = np.concatenate([np.asarray(sys_.GENROU.Pe.a), np.asarray(sys_.REGF1.Pe.a)])
            ctx["a_q"] = np.concatenate([np.asarray(sys_.GENROU.Qe.a), np.asarray(sys_.REGF1.Qe.a)])
            ctx["a_y"] = np.asarray(sys_.REGF1.PIplim_y.a)
            ctx["pn"] = np.asarray(y[ctx["a_p"]], float).copy()
            ctx["qn"] = np.asarray(y[ctx["a_q"]], float).copy()
            ctx["pset"], ctx["qset"] = ctx["pn"].copy(), ctx["qn"].copy()
            ctx["y0"] = np.asarray(y[ctx["a_y"]], float).copy()
            ctx["a_yq"] = np.asarray(sys_.REGF1.PIqlim_y.a)
            ctx["y0q"] = np.asarray(y[ctx["a_yq"]], float).copy()
            ctx["vref0_sg"] = np.asarray(sys_.IEEEX1.vref0.v, float).copy()
            gp0, gq0 = capability_factors(ctx["pset"], ctx["qset"], lim)
            if np.any(gp0 <= 0) or np.any(gq0 <= 0):
                raise RuntimeError("Nominal setpoint is not in the interior of W_i.")
            ctx["gref_p"], ctx["gref_q"] = gp0.max(), gq0.max()
            ctx["k_ip"] = SPEED_TARGET / float((gp0 / ctx["gref_p"]).sum())
            ctx["d_p"] = 1.0 / ctx["pn"]
            ctx["d_q"] = 1.0 / (lim["qmax"] - lim["qmin"])
            ctx["init"] = True
        if t <= ctx["last_t"]:
            return
        ctx["last_t"] = t
        dt, a = ctx["h"], ctx["adjacency"]
        omega = np.asarray(y[ctx["a_f"]], float)
        volt = np.asarray(y[ctx["a_v"]], float)
        p_now = np.asarray(y[ctx["a_p"]], float)
        q_now = np.asarray(y[ctx["a_q"]], float)
        gp_raw, gq_raw = capability_factors(ctx["pset"], ctx["qset"], lim)
        gp, gq = gp_raw / ctx["gref_p"], gq_raw / ctx["gref_q"]
        if t >= EVENT_TIME_S:
            xp, xq = ctx["d_p"] * p_now, ctx["d_q"] * q_now
            lp_x = gp * (a * gp[None, :] * (xp[:, None] - xp[None, :])).sum(axis=1)
            lq_x = gq * (a * gq[None, :] * (xq[:, None] - xq[None, :])).sum(axis=1)
            dpset = ctx["k_ip"] * (gp * (1.0 - omega) - K_P * lp_x) - K_LEAK * (ctx["pset"] - ctx["pn"])
            dqset = K_IQ * (K_V * gq * (V_REF - volt) - K_Q * lq_x) - K_LEAK * (ctx["qset"] - ctx["qn"])
            ctx["pset"] = ctx["pset"] + dt * dpset
            ctx["qset"] = ctx["qset"] + dt * dqset
        n_sg_ = ctx["n_sg"]
        sys_.TGOV1N.paux0.v[ctx["tg_pos"]] = (ctx["pset"] - ctx["pn"])[:n_sg_]
        paux = KC_GFM * (ctx["y0"] + (ctx["pset"] - ctx["pn"])[n_sg_:] - np.asarray(y[ctx["a_y"]], float))
        sys_.REGF1.Paux0.v[:] = paux
        q_err = ctx["qset"] - q_now
        ctx["z"] = np.clip(KAPPA_SG * (ctx["qset"] - ctx["qn"])[:n_sg_], -Z_CLAMP, Z_CLAMP)
        sys_.IEEEX1.vref0.v[ctx["ex_pos"]] = ctx["vref0_sg"][ctx["ex_pos"]] + ctx["z"]
        qaux = KCQ_GFM * (ctx["y0q"] + (ctx["qset"] - ctx["qn"])[n_sg_:] - np.asarray(y[ctx["a_yq"]], float))
        sys_.REGF1.Qaux0.v[:] = qaux
        for key, val in (("t", t), ("pset", ctx["pset"].copy()), ("qset", ctx["qset"].copy()), ("gp", gp.copy()),
                         ("gq", gq.copy()), ("paux", paux.copy()), ("qaux", qaux.copy()), ("z", ctx["z"].copy())):
            ctx["log"][key].append(val)

    system.TDS.callpert = rdc
    return system, ctx


def simulate(scenario: str, time_step_s: float) -> tuple[Any, dict[str, np.ndarray], dict[str, Any], dict[str, Any]]:
    system, ctx = configure(scenario, time_step_s)
    pflow_ok = bool(system.PFlow.run())
    pflow_residual = float(np.max(np.abs(system.dae.g)))
    tds_ok = bool(system.TDS.run(no_summary=True)) if pflow_ok else False
    data = extract_time_series(system)
    y = system.dae.ts.y
    data["sg_p_pu"] = np.asarray(y[:, system.GENROU.Pe.a], dtype=float)
    data["sg_q_pu"] = np.asarray(y[:, system.GENROU.Qe.a], dtype=float)
    data["gfm_bus_ids"] = np.asarray(system.REGF1.bus.v, dtype=int)
    data["gfm_p_pu"] = np.asarray(y[:, system.REGF1.Pe.a], dtype=float)
    data["gfm_q_pu"] = np.asarray(y[:, system.REGF1.Qe.a], dtype=float)
    data["unit_bus_ids"] = np.asarray(ctx["unit_bus"], dtype=int)
    for key in ("t", "pset", "qset", "gp", "gq", "paux", "qaux", "z"):
        data[f"cmd_{key}"] = np.asarray(ctx["log"][key])
    for key in ("pn", "qn"):
        data[f"unit_{key}"] = ctx[key]
    for key in ("pmax", "pmin", "qmax", "qmin", "smax"):
        data[f"unit_{key}"] = ctx["lim"][key]
    diag = {"pflow_ok": pflow_ok, "tds_ok": tds_ok, "pflow_residual": pflow_residual,
            "final_residual": float(np.max(np.abs(system.dae.g))), "t_end_s": float(system.dae.ts.t[-1]),
            "k_ip": float(ctx["k_ip"]), "g_ref_p": float(ctx["gref_p"]), "g_ref_q": float(ctx["gref_q"])}
    return system, data, diag, ctx


def metrics(data: dict[str, np.ndarray]) -> dict[str, Any]:
    t = data["time_s"]
    pre = (EVENT_TIME_S - e5.SETTLING_WINDOW_S, EVENT_TIME_S)
    post = (t[-1] - e5.SETTLING_WINDOW_S, t[-1] + 1e-9)
    p, q, v = e7.unit_series(None, data)
    f_mean = data["bus_frequency_hz"].mean(axis=1)
    pn, qn = data["unit_pn"], data["unit_qn"]
    p_end, q_end, v_end = e7.window(t, p, *post), e7.window(t, q, *post), e7.window(t, v, *post)
    ratio = p_end / pn
    cmd_t = data["cmd_t"]
    pset, qset = data["cmd_pset"], data["cmd_qset"]
    margin_p = np.minimum(data["unit_pmax"] - pset, pset - data["unit_pmin"]).min(axis=0)
    margin_q = np.minimum(data["unit_qmax"] - qset, qset - data["unit_qmin"]).min(axis=0)
    margin_s = (1.0 - np.hypot(pset, qset).max(axis=0) / data["unit_smax"])
    excess = np.maximum(0.0, p.max(axis=0) - data["unit_pmax"])
    after = t >= EVENT_TIME_S
    out_band = np.flatnonzero(np.abs(f_mean[after] - NOMINAL_FREQUENCY_HZ) > 0.002)
    q_excess_hi = np.maximum(0.0, q_end - data["unit_qmax"])
    q_excess_lo = np.maximum(0.0, data["unit_qmin"] - q_end)
    return {
        "final_frequency_error_hz": float(e7.window(t, f_mean, *post) - NOMINAL_FREQUENCY_HZ),
        "frequency_nadir_hz": float(f_mean.min()),
        "settling_time_2mHz_s": float(t[after][out_band[-1]] - EVENT_TIME_S) if out_band.size else 0.0,
        "unit_bus_ids": data["unit_bus_ids"].tolist(), "final_unit_voltage_pu": v_end.tolist(),
        "max_abs_voltage_error_final_pu": float(np.abs(v_end - V_REF).max()),
        "mean_abs_voltage_error_final_pu": float(np.abs(v_end - V_REF).mean()),
        "voltage_min_pu": float(data["bus_voltage_pu"].min()), "voltage_max_pu": float(data["bus_voltage_pu"].max()),
        "final_p_pu": p_end.tolist(), "final_p_over_pn": ratio.tolist(),
        "p_over_pn_spread_final": float(ratio.max() - ratio.min()),
        "final_q_pu": q_end.tolist(), "final_qset_pu": qset[-1].tolist(),
        "max_abs_q_tracking_error_final_pu": float(np.abs(q_end - qset[-1]).max()),
        "final_pset_minus_pn_pu": (pset[-1] - pn).tolist(), "total_delivered_dp_pu": float((p_end - e7.window(t, p, *pre)).sum()),
        "setpoint_min_margin_p_pu": margin_p.tolist(), "setpoint_min_margin_q_pu": margin_q.tolist(),
        "setpoint_min_margin_s_rel": margin_s.tolist(),
        "setpoint_invariance_margin_min": float(min(margin_p.min(), margin_q.min(), margin_s.min() * 1e-3)),
        "final_p_margin_to_pmax_pu": (data["unit_pmax"] - p_end).tolist(),
        "transient_p_excess_over_pmax_pu": excess.tolist(),
        "final_q_excess_over_case_limits_pu": (q_excess_hi + q_excess_lo).tolist(),
        "min_gp_normalized": float(data["cmd_gp"].min()), "min_gq_normalized": float(data["cmd_gq"].min()),
        "max_abs_z_pu": float(np.abs(data["cmd_z"]).max()),
    }


def plot_frequency(runs: dict[str, dict[str, Any]]) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    for col, (name, run) in enumerate(runs.items()):
        d = run["data"]; t, f = d["time_s"], d["bus_frequency_hz"]
        for row, (xlim, scale, unit) in enumerate(((None, 1.0, "Hz"), ((EVENT_TIME_S - 2, EVENT_TIME_S + 40), 1e3, "mHz"))):
            axis = axes[row, col]
            dev = (f - 60.0) * scale if row else f
            axis.fill_between(t, dev.min(1), dev.max(1), color="0.85", label="39-bus envelope")
            axis.plot(t, dev.mean(1), "tab:blue", lw=1.0, label="mean bus frequency")
            axis.axhline(0 if row else 60, color="black", ls=":", lw=.8); axis.axvline(EVENT_TIME_S, color="tab:red", ls=":", lw=.8)
            axis.set_xlabel("Time [s]"); axis.grid(alpha=.25)
            if row:
                axis.set_xlim(*xlim); axis.set_title(f"{name}: zoom, deviation [mHz]")
            else:
                axis.set_title(name); axis.set_ylim(59.97, 60.01); axis.ticklabel_format(axis="y", style="plain", useOffset=False)
    axes[0, 0].set_ylabel("Frequency [Hz]"); axes[1, 0].set_ylabel("f - 60 Hz [mHz]"); axes[0, 0].legend(fontsize=7)
    fig.suptitle("E8--C2t: bus frequency, original RDC (top: full run; bottom: zoom with independent axes)")
    fig.tight_layout(); fig.savefig(FREQUENCY_FIGURE, dpi=300, bbox_inches="tight"); plt.close(fig)


def plot_voltage(runs: dict[str, dict[str, Any]]) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharey=True)
    for axis, (name, run) in zip(axes, runs.items()):
        d = run["data"]; t = d["time_s"]
        _, _, v = e7.unit_series(None, d)
        n_sg = d["sg_p_pu"].shape[1]
        for i, b in enumerate(d["unit_bus_ids"]):
            axis.plot(t, v[:, i], lw=.9, ls="-" if i < n_sg else "--", label=f"{'SG' if i < n_sg else 'GFM'}{b}")
        axis.axhspan(V_REF - 0.02, V_REF + 0.02, color="tab:green", alpha=.12, label="1.0 +/- 0.02")
        axis.axhline(V_REF, color="black", ls=":", lw=.8); axis.axvline(EVENT_TIME_S, color="tab:red", ls=":", lw=.8)
        axis.set_xlabel("Time [s]"); axis.set_title(name); axis.grid(alpha=.25)
    axes[0].set_ylabel("Unit-bus voltage |V| [pu]"); axes[0].legend(ncol=3, fontsize=6)
    fig.suptitle("E8--C2t: voltage at the ten unit buses (Vref 1.0 pu), original RDC")
    fig.tight_layout(); fig.savefig(VOLTAGE_FIGURE, dpi=300, bbox_inches="tight"); plt.close(fig)


def plot_secondary(run: dict[str, Any]) -> None:
    d = run["data"]; t = d["cmd_t"]; n_sg = d["sg_p_pu"].shape[1]
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), sharex=True)
    for i, b in enumerate(d["unit_bus_ids"]):
        style = dict(lw=.9, ls="-" if i < n_sg else "--", label=f"{'SG' if i < n_sg else 'GFM'}{b}")
        axes[0, 0].plot(t, d["cmd_pset"][:, i] - d["unit_pn"][i], **style)
        axes[0, 1].plot(t, d["cmd_qset"][:, i] - d["unit_qn"][i], **style)
        axes[1, 0].plot(t, d["cmd_gp"][:, i], **style)
        axes[1, 1].plot(t, d["cmd_gq"][:, i], **style)
    for axis, label in zip(axes.flat, ("Pset - Pn [pu, 100 MVA]", "Qset - Qn [pu]", "g_P (normalized)", "g_Q (normalized)")):
        axis.set_ylabel(label); axis.grid(alpha=.25); axis.axvline(EVENT_TIME_S, color="tab:red", ls=":", lw=.8)
    axes[0, 0].legend(ncol=2, fontsize=6)
    for axis in axes[-1]: axis.set_xlabel("Time [s]")
    fig.suptitle("E8--C2t (P+): RDC setpoint states and capability factors")
    fig.tight_layout(); fig.savefig(SECONDARY_FIGURE, dpi=300, bbox_inches="tight"); plt.close(fig)


def final_unit_voltage(raw: Any, prefix: str, unit_bus: list[int]) -> np.ndarray:
    t = raw[f"{prefix}time_s"]; ids = list(raw[f"{prefix}bus_ids"])
    v = raw[f"{prefix}bus_voltage_pu"][:, [ids.index(b) for b in unit_bus]]
    return e7.window(t, v, t[-1] - 2.0, t[-1] + 1e-9)


def comparison(unit_bus: list[int]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    s5 = json.loads((ARTIFACTS_DIR / "IEEE39_E5_C2t_summary.json").read_text(encoding="utf-8"))["metrics"]["P+"]
    s6 = json.loads((ARTIFACTS_DIR / "IEEE39_E6_C2t_summary.json").read_text(encoding="utf-8"))
    s7 = json.loads((ARTIFACTS_DIR / "IEEE39_E7_C2t_summary.json").read_text(encoding="utf-8"))["metrics"]["P+"]
    r5, r6 = np.load(ARTIFACTS_DIR / "IEEE39_E5_C2t_timeseries.npz"), np.load(e7.E6_RAW)
    v5, v6 = final_unit_voltage(r5, "P+_", unit_bus), final_unit_voltage(r6, "", unit_bus)
    audit = json.loads((ARTIFACTS_DIR / "IEEE39_C2t_capacity_audit.json").read_text(encoding="utf-8"))["dynamic_envelopes"]
    sg31 = lambda env: float(env["31"]["P_excess_over_pmax_pu"])  # noqa: E731
    out["E5t_primary"] = {"final_frequency_error_hz": s5["steady_state_delta_f_hz"], "frequency_nadir_hz": s5["frequency_nadir_hz"],
                          "mean_abs_voltage_error_pu": float(np.abs(v5 - V_REF).mean()), "max_abs_voltage_error_pu": float(np.abs(v5 - V_REF).max()),
                          "sg31_transient_p_excess_pu": sg31(audit["E5_P+"])}
    out["E6t_consensus_P"] = {"final_frequency_error_hz": s6["metrics"]["secondary"]["final_frequency_error_hz"],
                              "frequency_nadir_hz": s6["metrics"]["secondary"]["frequency_nadir_hz"],
                              "mean_abs_voltage_error_pu": float(np.abs(v6 - V_REF).mean()), "max_abs_voltage_error_pu": float(np.abs(v6 - V_REF).max()),
                              "sg31_transient_p_excess_pu": sg31(audit["E6_P+"])}
    out["E7t_coordinated_PQ"] = {"final_frequency_error_hz": s7["final_frequency_error_hz"], "frequency_nadir_hz": s7["frequency_nadir_hz"],
                                 "mean_abs_voltage_error_pu": s7["mean_abs_voltage_error_final_pu"], "max_abs_voltage_error_pu": s7["max_abs_voltage_error_final_pu"],
                                 "sg31_transient_p_excess_pu": s7["transient_p_excess_over_pmax_pu"][1]}
    return out


def update_matrix(summary: dict[str, Any]) -> None:
    with MATRIX_FILE.open("r", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream); fields = list(reader.fieldnames or [])
        rows = [row for row in reader if row.get("stage") != "E8"]
    m = summary["metrics"]["P+"]
    row = {key: "" for key in fields}
    row.update({
        "run_id": summary["run_id"], "stage": "E8", "case": CASE_LABEL,
        "scenario": "S0_P+_Q+_1pct_separate_original_RDC", "baseline": "E7t_C2t",
        "source_sha256": summary["case_sha256"], "variant_sha256": summary["case_sha256"],
        "andes_version": summary["andes_version"], "git_commit": summary["git_commit"],
        "seed": "not_applicable_deterministic", "simulation_t0": 0.0, "simulation_tf": FINAL_TIME_S,
        "solver_settings": json.dumps(summary["solver"], sort_keys=True), "event_time": EVENT_TIME_S,
        "event_bus": "4(P);21(Q)", "event_P_MW": SCENARIOS["P+"]["p_mw"], "event_Q_MVAr": SCENARIOS["Q+"]["q_mvar"],
        "fn_Hz": NOMINAL_FREQUENCY_HZ, "bus_freq_set": "1-39", "bus_volt_set": "1-39",
        "f_nadir_Hz": m["frequency_nadir_hz"], "min_V_pu": m["voltage_min_pu"], "max_V_pu": m["voltage_max_pu"],
        "dae_residual": max(d["final_residual"] for d in summary["diagnostics"].values()),
        "status_auto": summary["status_auto"], "status_human": "PENDING",
        "frequency_figure": FREQUENCY_FIGURE.relative_to(PROJECT_ROOT).as_posix(),
        "voltage_figure": VOLTAGE_FIGURE.relative_to(PROJECT_ROOT).as_posix(),
        "raw_file": RAW_FILE.relative_to(PROJECT_ROOT).as_posix(),
        "decision_note": "E9 (modified RDC) and later stages remain blocked pending human approval of E8 figures.",
    })
    with MATRIX_FILE.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(rows + [row])


def main() -> int:
    graph = json.loads(GRAPH_FILE.read_text(encoding="utf-8"))
    runs: dict[str, dict[str, Any]] = {}
    for name in SCENARIOS:
        system, data, diag, _ = simulate(name, TIME_STEP_S)
        runs[name] = {"system": system, "data": data, "diag": diag, "metrics": metrics(data)}
    r_system, r_data, r_diag, _ = simulate("P+", REFINED_TIME_STEP_S)
    refined = {"diagnostics": r_diag, "metrics": metrics(r_data)}
    m = {n: r["metrics"] for n, r in runs.items()}
    m_p = m["P+"]
    numerical = {
        "final_frequency_error_difference_hz": abs(m_p["final_frequency_error_hz"] - refined["metrics"]["final_frequency_error_hz"]),
        "voltage_min_abs_difference_pu": abs(m_p["voltage_min_pu"] - refined["metrics"]["voltage_min_pu"]),
        "max_voltage_error_difference_pu": abs(m_p["max_abs_voltage_error_final_pu"] - refined["metrics"]["max_abs_voltage_error_final_pu"]),
    }
    unit_bus = runs["P+"]["data"]["unit_bus_ids"].tolist()
    compare = comparison(unit_bus)
    every = lambda fn: all(fn(x) for x in m.values())  # noqa: E731
    checks = {
        "plant_is_C2t": VARIANT == "C2t",
        "graph_connected_and_loss_tolerant": bool(graph["connected"] and graph["all_single_link_losses_ok"] and graph["all_single_unit_losses_ok"]),
        "all_runs_converged": all(r["diag"]["pflow_ok"] and r["diag"]["tds_ok"] and r["diag"]["final_residual"] <= 1e-5
                                  and r["diag"]["t_end_s"] >= FINAL_TIME_S - 1e-6 for r in list(runs.values()) + [{"diag": r_diag}]),
        "structure_6sg_4gfm": len(runs["P+"]["system"].GENROU.idx.v) == 6 and len(runs["P+"]["system"].REGF1.idx.v) == 4,
        "frequency_within_1mHz_all": every(lambda x: abs(x["final_frequency_error_hz"]) <= 0.001),
        "setpoints_inside_W_throughout_all": every(lambda x: x["setpoint_invariance_margin_min"] >= -1e-9),
        "p_over_pn_spread_within_0.02_P+": m_p["p_over_pn_spread_final"] <= 0.02,
                "final_p_below_pmax_all": every(lambda x: all(v >= -1e-6 for v in x["final_p_margin_to_pmax_pu"])),
        "mean_voltage_error_below_E6t_P+": m_p["mean_abs_voltage_error_final_pu"] < compare["E6t_consensus_P"]["mean_abs_voltage_error_pu"],
        "numerical_convergence": numerical["final_frequency_error_difference_hz"] <= 0.001
                                 and numerical["voltage_min_abs_difference_pu"] <= .005
                                 and numerical["max_voltage_error_difference_pu"] <= 0.005,
    }
    info = {
        "max_abs_q_tracking_error_final_pu": {n: x["max_abs_q_tracking_error_final_pu"] for n, x in m.items()},
        "voltage_target_0.02pu_met_all": every(lambda x: x["max_abs_voltage_error_final_pu"] <= 0.02),
        "sg31_transient_p_excess_pu": {n: x["transient_p_excess_over_pmax_pu"][1] for n, x in m.items()},
        "final_q_exceeds_case_limits_any_unit": {n: bool(any(v > 1e-6 for v in x["final_q_excess_over_case_limits_pu"])) for n, x in m.items()},
    }
    status = "PASS_AUTO_WAIT_HUMAN" if all(checks.values()) else "FAIL"
    np.savez_compressed(RAW_FILE, **{f"{n}_{k}": v for n, r in runs.items() for k, v in r["data"].items()})
    plot_frequency(runs); plot_voltage(runs); plot_secondary(runs["P+"])
    system = runs["P+"]["system"]
    summary = {
        "run_id": f"{PREFIX}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "created_utc": datetime.now(timezone.utc).isoformat(), "status_auto": status, "status_human": "PENDING",
        "case": str(CASE.relative_to(PROJECT_ROOT)), "case_sha256": sha256(CASE),
        "runner_sha256": sha256(Path(__file__).resolve()), "graph_sha256": sha256(GRAPH_FILE),
        "git_commit": git_commit(), "python_version": platform.python_version(), "andes_version": andes.__version__,
        "controller": {"kind": "original RDC, Eqs. (26)-(35) of the reference paper; no centering, barrier or CLF",
                       "speed_target": SPEED_TARGET, "k_ip_computed": runs["P+"]["diag"]["k_ip"], "k_P": K_P, "k_leak": K_LEAK,
                       "k_IQ": K_IQ, "k_V": K_V, "k_Q": K_Q, "v_ref_pu": V_REF, "d_P": "1/Pn_i", "d_Q": "1/(qmax_i-qmin_i)",
                       "g_normalization": {"g_ref_p": runs["P+"]["diag"]["g_ref_p"], "g_ref_q": runs["P+"]["diag"]["g_ref_q"]},
                       "capability": "GFM Eqs. (30)-(31) with Smax = Sn/100, Pmax = case pmax, Pmin = 0; SG Eqs. (28)-(29) with case qmin/qmax for the (24)-(25) terms",
                       "actuation": {"sg_P": "TGOV1N.paux0 = Pset - Pn", "gfm_P": f"REGF1.Paux0 = KC (y0 + Pset - Pn - y), KC {KC_GFM}",
                                     "sg_Q": f"IEEEX1.vref0 = vref0(0) + KAPPA (Qset - Qn), KAPPA {KAPPA_SG}", "gfm_Q": f"REGF1.Qaux0 = KCQ (y0q + Qset - Qn - PIqlim_y), KCQ {KCQ_GFM}"},
                       "secondary_start_s": EVENT_TIME_S},
        "scenarios": SCENARIOS,
        "solver": {"method": system.TDS.config.method, "tf_s": FINAL_TIME_S, "time_step_s": TIME_STEP_S,
                   "refined_time_step_s": REFINED_TIME_STEP_S, "tolerance": system.TDS.config.tol,
                   "maximum_iterations": system.TDS.config.max_iter},
        "diagnostics": {n: r["diag"] for n, r in runs.items()}, "metrics": m, "refined_P+": refined,
        "numerical_step_comparison": numerical, "comparison_on_C2t_P+": compare, "info": info, "checks": checks,
        "limitations": [
            "Original RDC only; the capability set of the SG replaces the excitation-limit and iron-core terms by the case plant limits (no ANDES capability-curve data).",
            "Gains and the d_P/d_Q choices were fixed a priori (DEC-033), not tuned; the 0.02 pu voltage target is reported, not a gate.",
            "The original RDC limits the setpoints Pset, Qset; instantaneous P and Q can exceed the case limits through the primary droop (SG31, OPEN-SG31-PMAX).",
            "GFM reactive capability uses Eq. (31) (apparent-power disc only), so the case qmin/qmax can be exceeded by GFM; reported in info.",
            "Q/V actuation by inner tracking loops (DEC-032) differs from the E7 voltage-setpoint-offset structure; the E7 versus E8 comparison mixes law and actuation.",
            "Ideal measurements, zero delay, forward-Euler integration of the controller at the TDS step; no stability, regional-stability or physical-invariance claim.",
            "Graph hub at bus 30 (degree 9) inherited from E6."],
    }
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    update_matrix(summary)
    print(json.dumps({"status_auto": status, "checks": checks, "numerical": numerical, "info": info}, indent=2))
    for name, mm in m.items():
        print(name, json.dumps({k: mm[k] for k in (
            "final_frequency_error_hz", "frequency_nadir_hz", "settling_time_2mHz_s", "max_abs_voltage_error_final_pu",
            "mean_abs_voltage_error_final_pu", "final_unit_voltage_pu", "final_p_over_pn", "p_over_pn_spread_final",
            "max_abs_q_tracking_error_final_pu", "setpoint_invariance_margin_min", "transient_p_excess_over_pmax_pu",
            "final_q_excess_over_case_limits_pu", "final_pset_minus_pn_pu")}))
    print("compare", json.dumps(compare))
    return 0 if status != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
