"""E7--C2: capability-aware coordinated P/Q consensus secondary on the frozen C2 case.

Primary control identical to E5/E6; the C2 case file is read only.  An external loop
(TDS ``callpert`` hook, once per fixed step) integrates, per unit i (ten units, E6 graph):

  P: dP_i/dt = kIP g_i (1 - omega_i) - kIP kP sum_j a_ij (g_j dP_i - g_i dP_j)
     g_i = h_i / max_j h_j, h_i = pmax_i - P_i0 (upward headroom at the pre-event dispatch);
     equilibrium: omega = 1 and dP_i / h_i equal for all units.
  Q: dS_i/dt = kV (1 - V_i) g_up/dn(rho_i) - kQ sum_j a_ij (rho_i - rho_j)
     rho_i = (Q_i - qmin_i^eff) / (qmax_i^eff - qmin_i^eff) with
     q^eff limited by sqrt(Sn_i^2 - P_i^2) (P has priority over Q);
     g_up/dn go to zero as rho_i approaches 0.90 / 0.05 in the direction that would
     push it outside; S_i is a voltage-setpoint offset applied to REGF1.vref (GFM) or
     IEEEX1.vref0 (SG).  Targets: omega = 1 (60 Hz) and V_i = 1.0 pu at the ten unit buses.

Actuation of P: SG -> TGOV1N.paux0 (system pu); GFM -> REGF1.Paux0 = KC (y0 + dP - PIplim_y).
Scenarios: S0 (no disturbance, targets only), P+ (+58.564 MW at bus 4) and Q+ (+17.345 MVAr at
bus 21), each at t = 5 s and run separately.  Capability = case plant data (pmax, qmin, qmax) with S <= Sn (DEC-023).
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

import run_e5_ieee39 as e5  # noqa: E402
from variant import CASE_LABEL, SUFFIX, VARIANT  # noqa: E402
from run_e0_ieee39 import (  # noqa: E402
    ARTIFACTS_DIR, FIGURES_DIR, MATRIX_FILE, NOMINAL_FREQUENCY_HZ, PROJECT_ROOT,
    extract_time_series, git_commit, sha256,
)

CASE = e5.CASE
# E7_MODE=limited (options B/C of DEC-026/027): voltage-setpoint offsets limited to a stable fraction of the
# way to 1.0 pu on the unmodified C2; stage label E7L, plant variant C2.
MODE = os.environ.get("E7_MODE", "full")
LIMITED = MODE == "limited"
LTAG = "L" if LIMITED else ""
PREFIX = f"IEEE39_E7{LTAG}_{VARIANT}"
RAW_FILE = ARTIFACTS_DIR / f"{PREFIX}_timeseries.npz"
SUMMARY_FILE = ARTIFACTS_DIR / f"{PREFIX}_summary.json"
GRAPH_FILE = ARTIFACTS_DIR / "IEEE39_E6_C2_communication_graph.json"
E5_SUMMARY = ARTIFACTS_DIR / f"IEEE39_E5_{VARIANT}_summary.json"
E6_RAW = ARTIFACTS_DIR / f"IEEE39_E6_{VARIANT}_timeseries.npz"
AUDIT_FILE = ARTIFACTS_DIR / f"IEEE39_{VARIANT}_capacity_audit.json"
FREQUENCY_FIGURE = FIGURES_DIR / f"{PREFIX}_frequency.png"
VOLTAGE_FIGURE = FIGURES_DIR / f"{PREFIX}_voltage.png"
SECONDARY_FIGURE = FIGURES_DIR / f"{PREFIX}_secondary.png"

EVENT_TIME_S = e5.EVENT_TIME_S
FINAL_TIME_S = 120.0
TIME_STEP_S = e5.TIME_STEP_S
REFINED_TIME_STEP_S = e5.REFINED_TIME_STEP_S
BASE_MVA = 100.0
# Simultaneous +1 % P and +1 % Q steps do not converge on C2 even without secondary (t ~ 5.17 s,
# DEC-026), so the channels are tested separately as in E5.
SCENARIOS = {"S0": {}, "P+": {"p_mw": 58.564}, "Q+": {"q_mvar": 17.345}}
E5_AUDIT_KEY = {"S0": None, "P+": "E5_P+", "Q+": "E5_Q+"}
# A-priori gains from time-scale estimates (DEC-026); not tuned.
K_IP, K_P, KC_GFM = 60.0, 0.1, 0.05
# Attempt 1 (K_V 0.5, K_Q 0.005) failed: setpoint moves too fast, S0 frequency nadir 59.82 Hz (DEC-026).
K_V, K_Q = 0.1, 0.001
RHO_MAX, RHO_MIN, RHO_BAND = 0.90, 0.05, 0.05
S_CLAMP = 0.08
ALPHA_MAX = 0.25  # limited mode: fraction of the way to V_TARGET (zeta 0.041 at 25 % on C2, DEC-026)
V_TARGET = 1.0
V_TOLERANCE = 0.05 if LIMITED else 0.02


def static_limits(system: Any) -> dict[int, dict[str, float]]:
    out = {}
    for model in ("PV", "Slack"):
        d = getattr(system, model)
        for k, b in enumerate(d.bus.v):
            out[int(b)] = {"pmax": float(d.pmax.v[k]), "qmin": float(d.qmin.v[k]), "qmax": float(d.qmax.v[k])}
    return out


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
            system.add("Alter", idx=f"E7_{channel}", t=EVENT_TIME_S, model="PQ", dev=dev[0], src=src,
                       attr="v", method="+", amount=spec[key] / BASE_MVA)
    system.setup()
    system.TDS.config.tf = FINAL_TIME_S
    system.TDS.config.tstep = time_step_s
    system.TDS.config.fixt = 1
    system.TDS.config.no_tqdm = 1

    graph = json.loads(GRAPH_FILE.read_text(encoding="utf-8"))
    sg_bus = [int(b) for b in system.GENROU.bus.v]
    gfm_bus = [int(b) for b in system.REGF1.bus.v]
    unit_bus = sg_bus + gfm_bus
    n_sg = len(sg_bus)
    pos = {b: i for i, b in enumerate(unit_bus)}
    adjacency = np.zeros((len(unit_bus), len(unit_bus)))
    for u, v in graph["edges"]:
        adjacency[pos[u], pos[v]] = adjacency[pos[v], pos[u]] = graph["weights"]
    lim = static_limits(system)
    sn_pu = np.concatenate([np.asarray(system.GENROU.Sn.v, float), np.asarray(system.REGF1.Sn.v, float)]) / BASE_MVA
    ctx = {
        "unit_bus": unit_bus, "n_sg": n_sg, "adjacency": adjacency, "sn_pu": sn_pu,
        "pmax": np.array([lim[b]["pmax"] for b in unit_bus]), "qmin": np.array([lim[b]["qmin"] for b in unit_bus]),
        "qmax": np.array([lim[b]["qmax"] for b in unit_bus]),
        "tg_pos": [list(system.TGOV1N.syn.v).index(g) for g in system.GENROU.idx.v],
        "ex_pos": [list(system.IEEEX1.syn.v).index(g) for g in system.GENROU.idx.v],
        "bus_list": list(system.BusFreq.bus.v), "bus_idx": list(system.Bus.idx.v),
        "dp": np.zeros(len(unit_bus)), "s": np.zeros(len(unit_bus)), "rho_f": None, "h": time_step_s,
        "last_t": -1.0, "init": None, "log": {k: [] for k in ("t", "dp", "s", "rho", "paux", "g")},
    }

    def secondary(t: Any, sys_: Any) -> None:
        t = float(t)  # ``dae.t`` is mutated in place
        y = sys_.dae.y
        if ctx["init"] is None:  # variable addresses exist only after TDS initialization
            ctx["a_f"] = np.asarray(sys_.BusFreq.f.a)[[ctx["bus_list"].index(b) for b in unit_bus]]
            ctx["a_v"] = np.asarray(sys_.Bus.v.a)[[ctx["bus_idx"].index(b) for b in unit_bus]]
            ctx["a_p"] = np.concatenate([np.asarray(sys_.GENROU.Pe.a), np.asarray(sys_.REGF1.Pe.a)])
            ctx["a_q"] = np.concatenate([np.asarray(sys_.GENROU.Qe.a), np.asarray(sys_.REGF1.Qe.a)])
            ctx["a_y"] = np.asarray(sys_.REGF1.PIplim_y.a)
            p0 = np.asarray(y[ctx["a_p"]], float).copy()
            head = ctx["pmax"] - p0
            if np.any(head <= 0):
                raise RuntimeError("Non-positive upward P headroom at the pre-event dispatch.")
            ctx["head"], ctx["g"] = head, head / head.max()
            ctx["y0"] = np.asarray(y[ctx["a_y"]], float).copy()
            ctx["vref_gfm0"] = np.asarray(sys_.REGF1.vref.v, float).copy()
            ctx["vref_sg0"] = np.asarray(sys_.IEEEX1.vref0.v, float).copy()
            ctx["s_clamp"] = (ALPHA_MAX * np.abs(np.asarray(y[ctx["a_v"]], float) - V_TARGET)) if LIMITED \
                else np.full(len(unit_bus), S_CLAMP)
            ctx["init"] = True
        if t <= ctx["last_t"]:
            return
        ctx["last_t"] = t
        dt, a, g = ctx["h"], ctx["adjacency"], ctx["g"]
        omega = np.asarray(y[ctx["a_f"]], float)
        volt = np.asarray(y[ctx["a_v"]], float)
        p_now = np.asarray(y[ctx["a_p"]], float)
        q_now = np.asarray(y[ctx["a_q"]], float)
        room = np.sqrt(np.maximum(ctx["sn_pu"] ** 2 - p_now ** 2, 1e-9))  # P has priority over Q
        q_hi, q_lo = np.minimum(ctx["qmax"], room), np.maximum(ctx["qmin"], -room)
        rho_raw = np.clip((q_now - q_lo) / np.maximum(q_hi - q_lo, 1e-6), -0.5, 1.5)
        ctx["rho_f"] = rho_raw if ctx["rho_f"] is None else ctx["rho_f"] + dt / 1.0 * (rho_raw - ctx["rho_f"])
        rho = ctx["rho_f"]
        if t >= EVENT_TIME_S:
            consensus_p = (a * (np.outer(ctx["dp"], g) - np.outer(g, ctx["dp"]))).sum(axis=1)
            ctx["dp"] = ctx["dp"] + dt * K_IP * (g * (1.0 - omega) - K_P * consensus_p)
            err_v = V_TARGET - volt
            g_up = np.clip((RHO_MAX - rho) / RHO_BAND, 0.0, 1.0)
            g_dn = np.clip((rho - RHO_MIN) / RHO_BAND, 0.0, 1.0)
            v_term = K_V * err_v * np.where(err_v > 0, g_up, g_dn)
            q_term = K_Q * (a * (rho[:, None] - rho[None, :])).sum(axis=1)
            ctx["s"] = np.clip(ctx["s"] + dt * (v_term - q_term), -ctx["s_clamp"], ctx["s_clamp"])
            ctx["dp"] = np.minimum(ctx["dp"], 0.95 * ctx["head"])
        n_sg = ctx["n_sg"]
        sys_.TGOV1N.paux0.v[ctx["tg_pos"]] = ctx["dp"][:n_sg]
        paux = KC_GFM * (ctx["y0"] + ctx["dp"][n_sg:] - np.asarray(y[ctx["a_y"]], float))
        sys_.REGF1.Paux0.v[:] = paux
        sys_.IEEEX1.vref0.v[ctx["ex_pos"]] = ctx["vref_sg0"][ctx["ex_pos"]] + ctx["s"][:n_sg]
        sys_.REGF1.vref.v[:] = ctx["vref_gfm0"] + ctx["s"][n_sg:]
        for key, val in (("t", t), ("dp", ctx["dp"].copy()), ("s", ctx["s"].copy()), ("rho", rho.copy()),
                         ("paux", paux.copy()), ("g", g.copy())):
            ctx["log"][key].append(val)

    system.TDS.callpert = secondary
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
    data["sg_governor_pout_pu"] = np.asarray(y[:, system.TGOV1N.pout.a], dtype=float)
    data["gfm_bus_ids"] = np.asarray(system.REGF1.bus.v, dtype=int)
    data["gfm_p_pu"] = np.asarray(y[:, system.REGF1.Pe.a], dtype=float)
    data["gfm_q_pu"] = np.asarray(y[:, system.REGF1.Qe.a], dtype=float)
    data["gfm_v_pu"] = np.asarray(y[:, system.REGF1.v.a], dtype=float)
    data["unit_bus_ids"] = np.asarray(ctx["unit_bus"], dtype=int)
    data["unit_sn_pu"] = ctx["sn_pu"]
    data["unit_pmax"], data["unit_qmin"], data["unit_qmax"] = ctx["pmax"], ctx["qmin"], ctx["qmax"]
    data["unit_head"] = ctx["head"]
    for key in ("t", "dp", "s", "rho", "paux", "g"):
        data[f"cmd_{key}"] = np.asarray(ctx["log"][key])
    diag = {"pflow_ok": pflow_ok, "tds_ok": tds_ok, "pflow_residual": pflow_residual,
            "final_residual": float(np.max(np.abs(system.dae.g))), "t_end_s": float(system.dae.ts.t[-1])}
    return system, data, diag, ctx


def unit_series(system: Any, data: dict[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ids = list(data["bus_ids"])
    cols = [ids.index(b) for b in data["unit_bus_ids"]]
    return (np.hstack([data["sg_p_pu"], data["gfm_p_pu"]]), np.hstack([data["sg_q_pu"], data["gfm_q_pu"]]),
            data["bus_voltage_pu"][:, cols])


def window(t: np.ndarray, x: np.ndarray, start: float, stop: float) -> np.ndarray:
    return x[(t >= start) & (t < stop)].mean(axis=0)


def metrics(system: Any, data: dict[str, np.ndarray], e5_excess: dict[int, float]) -> dict[str, Any]:
    t = data["time_s"]
    pre = (EVENT_TIME_S - e5.SETTLING_WINDOW_S, EVENT_TIME_S)
    post = (t[-1] - e5.SETTLING_WINDOW_S, t[-1] + 1e-9)
    p, q, v = unit_series(system, data)
    f_mean = data["bus_frequency_hz"].mean(axis=1)
    bus = data["unit_bus_ids"].tolist()
    dp_delivered = window(t, p, *post) - window(t, p, *pre)
    head = data["unit_head"]
    util = dp_delivered / head
    q_hi = np.minimum(data["unit_qmax"], np.sqrt(np.maximum(data["unit_sn_pu"] ** 2 - window(t, p, *post) ** 2, 0)))
    q_lo = np.maximum(data["unit_qmin"], -np.sqrt(np.maximum(data["unit_sn_pu"] ** 2 - window(t, p, *post) ** 2, 0)))
    q_end = window(t, q, *post)
    rho_end = (q_end - q_lo) / (q_hi - q_lo)
    v_end, v_pre = window(t, v, *post), window(t, v, *pre)
    s_end = np.hypot(window(t, p, *post), q_end) / data["unit_sn_pu"]
    command = data["cmd_dp"][-1]
    p_end = window(t, p, *post)
    excess = np.maximum(0.0, p.max(axis=0) - data["unit_pmax"])
    after = t >= EVENT_TIME_S
    out_band = np.flatnonzero(np.abs(f_mean[after] - NOMINAL_FREQUENCY_HZ) > 0.002)
    return {
        "final_frequency_error_hz": float(window(t, f_mean, *post) - NOMINAL_FREQUENCY_HZ),
        "frequency_nadir_hz": float(f_mean.min()),
        "settling_time_2mHz_s": float(t[after][out_band[-1]] - EVENT_TIME_S) if out_band.size else 0.0,
        "unit_bus_ids": bus,
        "final_unit_voltage_pu": v_end.tolist(), "pre_event_unit_voltage_pu": v_pre.tolist(),
        "max_abs_voltage_error_final_pu": float(np.abs(v_end - V_TARGET).max()),
        "mean_abs_voltage_error_final_pu": float(np.abs(v_end - V_TARGET).mean()),
        "mean_abs_voltage_error_pre_event_pu": float(np.abs(v_pre - V_TARGET).mean()),
        "voltage_min_pu": float(data["bus_voltage_pu"].min()), "voltage_max_pu": float(data["bus_voltage_pu"].max()),
        "commanded_dp_pu": command.tolist(), "delivered_dp_pu": dp_delivered.tolist(),
        "dp_tracking_abs_error_pu": np.abs(dp_delivered - command).tolist(),
        "delivered_dp_over_headroom": util.tolist(),
        "p_sharing_spread_rel": float((util.max() - util.min()) / util.mean()) if util.mean() > 0 else float("nan"),
        "total_delivered_dp_pu": float(dp_delivered.sum()),
        "final_p_pu": p_end.tolist(), "final_p_margin_to_pmax_pu": (data["unit_pmax"] - p_end).tolist(),
        "final_q_pu": q_end.tolist(), "final_q_utilization": rho_end.tolist(),
        "max_final_q_utilization": float(rho_end.max()), "min_final_q_utilization": float(rho_end.min()),
        "final_s_over_sn": s_end.tolist(), "max_final_s_over_sn": float(s_end.max()),
        "transient_p_excess_over_pmax_pu": excess.tolist(),
        "e5_transient_p_excess_over_pmax_pu": [e5_excess.get(b, 0.0) for b in bus],
        "final_vref_offset_pu": data["cmd_s"][-1].tolist(),
        "max_abs_vref_offset_pu": float(np.abs(data["cmd_s"]).max()),
        "max_gfm_paux_abs_pu": float(np.abs(data["cmd_paux"]).max()),
        "p_headroom_pu": head.tolist(),
    }


def plot_frequency(runs: dict[str, dict[str, Any]]) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), sharey=True)
    for axis, (name, run) in zip(axes, runs.items()):
        d = run["data"]; t, f = d["time_s"], d["bus_frequency_hz"]
        axis.fill_between(t, f.min(1), f.max(1), color="0.85", label="39-bus envelope")
        axis.plot(t, f.mean(1), "tab:blue", lw=1.0, label="mean bus frequency")
        axis.axhline(60, color="black", ls=":", lw=.8); axis.axvline(EVENT_TIME_S, color="tab:red", ls=":", lw=.8)
        axis.set_xlabel("Time [s]"); axis.set_title(name); axis.grid(alpha=.25)
        axis.set_ylim(59.97, 60.01); axis.ticklabel_format(axis="y", style="plain", useOffset=False)
    axes[0].set_ylabel("Frequency [Hz]"); axes[0].legend(fontsize=7)
    fig.suptitle(f"E7--{VARIANT}: bus frequency, capability-aware coordinated P/Q secondary")
    fig.tight_layout(); fig.savefig(FREQUENCY_FIGURE, dpi=300, bbox_inches="tight"); plt.close(fig)


def plot_voltage(runs: dict[str, dict[str, Any]]) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharey=True)
    for axis, (name, run) in zip(axes, runs.items()):
        d = run["data"]; t = d["time_s"]
        _, _, v = unit_series(run["system"], d)
        n_sg = d["sg_p_pu"].shape[1]
        for i, b in enumerate(d["unit_bus_ids"]):
            axis.plot(t, v[:, i], lw=.9, ls="-" if i < n_sg else "--", label=f"{'SG' if i < n_sg else 'GFM'}{b}")
        axis.axhspan(V_TARGET - V_TOLERANCE, V_TARGET + V_TOLERANCE, color="tab:green", alpha=.12, label="1.0 +/- 0.02")
        axis.axhline(V_TARGET, color="black", ls=":", lw=.8); axis.axvline(EVENT_TIME_S, color="tab:red", ls=":", lw=.8)
        axis.set_xlabel("Time [s]"); axis.set_title(name); axis.grid(alpha=.25)
    axes[0].set_ylabel("Unit-bus voltage |V| [pu]"); axes[0].legend(ncol=3, fontsize=6)
    fig.suptitle(f"E7--{VARIANT}: voltage at the ten unit buses (target 1.0 pu)")
    fig.tight_layout(); fig.savefig(VOLTAGE_FIGURE, dpi=300, bbox_inches="tight"); plt.close(fig)


def plot_secondary(run: dict[str, Any]) -> None:
    d = run["data"]; t = d["cmd_t"]; n_sg = d["sg_p_pu"].shape[1]
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), sharex=True)
    for i, b in enumerate(d["unit_bus_ids"]):
        style = dict(lw=.9, ls="-" if i < n_sg else "--", label=f"{'SG' if i < n_sg else 'GFM'}{b}")
        axes[0, 0].plot(t, d["cmd_dp"][:, i] / d["unit_head"][i], **style)
        axes[0, 1].plot(t, d["cmd_dp"][:, i], **style)
        axes[1, 0].plot(t, d["cmd_rho"][:, i], **style)
        axes[1, 1].plot(t, d["cmd_s"][:, i], **style)
    axes[1, 0].axhline(RHO_MAX, color="k", ls=":", lw=.8)
    for axis, label in zip(axes.flat, ("dPset / headroom [-]", "dPset [pu, 100 MVA]", "Q utilization rho [-]", "voltage-setpoint offset [pu]")):
        axis.set_ylabel(label); axis.grid(alpha=.25); axis.axvline(EVENT_TIME_S, color="tab:red", ls=":", lw=.8)
    axes[0, 0].legend(ncol=2, fontsize=6)
    for axis in axes[-1]: axis.set_xlabel("Time [s]")
    fig.suptitle(f"E7--{VARIANT} (P+): secondary states, headroom-weighted P and utilization-based Q")
    fig.tight_layout(); fig.savefig(SECONDARY_FIGURE, dpi=300, bbox_inches="tight"); plt.close(fig)


def update_matrix(summary: dict[str, Any]) -> None:
    with MATRIX_FILE.open("r", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream); fields = list(reader.fieldnames or [])
        rows = [row for row in reader if row.get("stage") != f"E7{LTAG}{SUFFIX}"]
    m = summary["metrics"]["P+"]
    row = {key: "" for key in fields}
    row.update({
        "run_id": summary["run_id"], "stage": f"E7{LTAG}{SUFFIX}", "case": CASE_LABEL,
        "scenario": "S0_P+_Q+_1pct_separate_coordinated_PQ_secondary", "baseline": f"E6{SUFFIX}_{VARIANT}",
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
        "decision_note": f"E8 remains blocked pending human approval of E7{LTAG} figures (mode {MODE}).",
    })
    with MATRIX_FILE.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(rows + [row])


def main() -> int:
    audit = json.loads(AUDIT_FILE.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH_FILE.read_text(encoding="utf-8"))
    e6 = np.load(E6_RAW)

    def excess_for(name: str) -> dict[int, float]:
        key = E5_AUDIT_KEY[name]
        return {} if key is None else {int(b): v["P_excess_over_pmax_pu"] for b, v in audit["dynamic_envelopes"][key].items()}

    runs: dict[str, dict[str, Any]] = {}
    for name in SCENARIOS:
        system, data, diag, _ = simulate(name, TIME_STEP_S)
        runs[name] = {"system": system, "data": data, "diag": diag, "metrics": metrics(system, data, excess_for(name))}
    r_system, r_data, r_diag, _ = simulate("P+", REFINED_TIME_STEP_S)
    refined = {"diagnostics": r_diag, "metrics": metrics(r_system, r_data, excess_for("P+"))}
    m = {n: r["metrics"] for n, r in runs.items()}
    m_p = m["P+"]
    numerical = {
        "final_frequency_error_difference_hz": abs(m_p["final_frequency_error_hz"] - refined["metrics"]["final_frequency_error_hz"]),
        "voltage_min_abs_difference_pu": abs(m_p["voltage_min_pu"] - refined["metrics"]["voltage_min_pu"]),
        "max_voltage_error_difference_pu": abs(m_p["max_abs_voltage_error_final_pu"] - refined["metrics"]["max_abs_voltage_error_final_pu"]),
    }
    e6_t = e6["time_s"]
    e6_v = window(e6_t, unit_series(None, {"bus_ids": e6["bus_ids"], "bus_voltage_pu": e6["bus_voltage_pu"],
                                           "unit_bus_ids": e6["unit_bus_ids"], "sg_p_pu": e6["sg_p_pu"], "sg_q_pu": e6["sg_q_pu"],
                                           "gfm_p_pu": e6["gfm_p_pu"], "gfm_q_pu": e6["gfm_q_pu"]})[2], e6_t[-1] - 2.0, e6_t[-1] + 1e-9)
    e6_mean_err = float(np.abs(e6_v - V_TARGET).mean())
    # P-channel effect isolated from the voltage re-dispatch: P+ minus S0 (same targets, no event).
    # The undifferentiated values stay in the summary; the terminal Pe of low-headroom SG also
    # moves with the voltage setpoints (armature losses), which the P secondary does not command.
    cmd_diff = np.asarray(m_p["commanded_dp_pu"]) - np.asarray(m["S0"]["commanded_dp_pu"])
    del_diff = np.asarray(m_p["delivered_dp_pu"]) - np.asarray(m["S0"]["delivered_dp_pu"])
    head = np.asarray(m_p["p_headroom_pu"])
    util_cmd = cmd_diff / head
    differential = {"commanded_dp_diff_pu": cmd_diff.tolist(), "delivered_dp_diff_pu": del_diff.tolist(),
                    "commanded_dp_over_headroom_diff": util_cmd.tolist(),
                    "commanded_sharing_spread_rel": float((util_cmd.max() - util_cmd.min()) / util_cmd.mean()),
                    "tracking_abs_error_diff_pu": np.abs(del_diff - cmd_diff).tolist(),
                    "total_delivered_dp_diff_pu": float(del_diff.sum())}
    track_tol = np.maximum(0.10 * np.abs(cmd_diff), 0.005)
    event_pu = SCENARIOS["P+"]["p_mw"] / BASE_MVA
    every = lambda fn: all(fn(x) for x in m.values())  # noqa: E731
    checks = {
        "graph_connected_and_loss_tolerant": bool(graph["connected"] and graph["all_single_link_losses_ok"] and graph["all_single_unit_losses_ok"]),
        "all_runs_converged": all(r["diag"]["pflow_ok"] and r["diag"]["tds_ok"] and r["diag"]["final_residual"] <= 1e-5
                                  and r["diag"]["t_end_s"] >= FINAL_TIME_S - 1e-6 for r in list(runs.values()) + [{"diag": r_diag}]),
        "structure_6sg_4gfm": len(runs["P+"]["system"].GENROU.idx.v) == 6 and len(runs["P+"]["system"].REGF1.idx.v) == 4,
        "frequency_within_1mHz_all": every(lambda x: abs(x["final_frequency_error_hz"]) <= 0.001),
        "unit_voltage_within_tolerance_all": every(lambda x: x["max_abs_voltage_error_final_pu"] <= V_TOLERANCE),
        "mean_voltage_error_below_E6_P+": m_p["mean_abs_voltage_error_final_pu"] < e6_mean_err,
        "p_commanded_sharing_spread_within_10pct_P+_minus_S0": differential["commanded_sharing_spread_rel"] <= 0.10,
        "p_delivered_tracks_command_P+_minus_S0": bool(np.all(np.asarray(differential["tracking_abs_error_diff_pu"]) <= track_tol)),
        "total_delivered_dp_matches_event_within_10pct_P+_minus_S0": abs(differential["total_delivered_dp_diff_pu"] - event_pu) <= 0.10 * event_pu,
        "final_p_below_pmax_all": every(lambda x: all(v >= 0.0 for v in x["final_p_margin_to_pmax_pu"])),
        "final_q_utilization_within_5_to_90pct_all": every(lambda x: x["max_final_q_utilization"] <= 0.90 + 1e-3 and x["min_final_q_utilization"] >= 0.05 - 1e-3),
        "final_s_below_0.9_sn_all": every(lambda x: x["max_final_s_over_sn"] <= 0.90),
        "transient_p_excess_not_worse_than_E5_all": every(lambda x: all(a <= b + 0.01 for a, b in zip(x["transient_p_excess_over_pmax_pu"], x["e5_transient_p_excess_over_pmax_pu"]))),
        "numerical_convergence": numerical["final_frequency_error_difference_hz"] <= 0.001
                                 and numerical["voltage_min_abs_difference_pu"] <= .005
                                 and numerical["max_voltage_error_difference_pu"] <= 0.005,
    }
    status = "PASS_AUTO_WAIT_HUMAN" if all(checks.values()) else "FAIL"
    np.savez_compressed(RAW_FILE, **{f"{n}_{k}": v for n, r in runs.items() for k, v in r["data"].items()})
    plot_frequency(runs); plot_voltage(runs); plot_secondary(runs["P+"])
    system = runs["P+"]["system"]
    summary = {
        "run_id": f"{PREFIX}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "created_utc": datetime.now(timezone.utc).isoformat(), "mode": MODE, "voltage_tolerance_pu": V_TOLERANCE, "status_auto": status, "status_human": "PENDING",
        "case": str(CASE.relative_to(PROJECT_ROOT)), "case_sha256": sha256(CASE),
        "runner_sha256": sha256(Path(__file__).resolve()), "graph_sha256": sha256(GRAPH_FILE),
        "audit_sha256": sha256(AUDIT_FILE), "git_commit": git_commit(), "python_version": platform.python_version(),
        "andes_version": andes.__version__,
        "controller": {"k_IP": K_IP, "k_P": K_P, "kc_gfm_paux": KC_GFM, "k_V": K_V, "k_Q": K_Q,
                       "rho_max": RHO_MAX, "rho_min": RHO_MIN, "rho_band": RHO_BAND, "vref_offset_clamp_pu": S_CLAMP,
                       "voltage_target_pu": V_TARGET, "voltage_tolerance_pu": V_TOLERANCE,
                       "secondary_start_s": EVENT_TIME_S,
                       "p_actuators": "SG TGOV1N.paux0; GFM REGF1.Paux0 = KC (y0 + dP - PIplim_y)",
                       "q_actuators": "SG IEEEX1.vref0 += s_i; GFM REGF1.vref += s_i (voltage-setpoint offset)"},
        "scenarios": SCENARIOS,
        "solver": {"method": system.TDS.config.method, "tf_s": FINAL_TIME_S, "time_step_s": TIME_STEP_S,
                   "refined_time_step_s": REFINED_TIME_STEP_S, "tolerance": system.TDS.config.tol,
                   "maximum_iterations": system.TDS.config.max_iter},
        "diagnostics": {n: r["diag"] for n, r in runs.items()}, "metrics": {n: r["metrics"] for n, r in runs.items()},
        "refined_P+": refined, "differential_P+_minus_S0": differential, "numerical_step_comparison": numerical, "e6_mean_abs_voltage_error_final_pu": e6_mean_err,
        "checks": checks,
        "limitations": [
            "Gains were fixed a priori from time-scale estimates and not tuned; no sensitivity runs.",
            "Capability is the case plant data (pmax, qmin, qmax) with S <= Sn, not a manufacturer curve; no current limit or SoC model.",
            "Q/V secondary acts as a voltage-setpoint offset (REGF1.vref, IEEEX1.vref0), not as the manuscript's Q_set input.",
            "Unit-bus voltage and Q-utilization sharing cannot both be exact; the residual is bounded by the 0.02 pu acceptance tolerance.",
            "Transient P excess caused by the unchanged primary control is reported, not corrected.",
            "Ideal measurements, zero communication delay; effective-graph connectivity under small g_i is not analysed here.",
            "The cyber graph hub at bus 30 (degree 9) is inherited from E6.",
            "No stability or safety certification."],
    }
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    update_matrix(summary)
    print(json.dumps({"status_auto": status, "checks": checks, "numerical": numerical}, indent=2))
    for name, mm in m.items():
        print(name, json.dumps({k: mm[k] for k in (
            "final_frequency_error_hz", "frequency_nadir_hz", "settling_time_2mHz_s", "max_abs_voltage_error_final_pu",
            "mean_abs_voltage_error_final_pu", "mean_abs_voltage_error_pre_event_pu", "final_unit_voltage_pu",
            "delivered_dp_over_headroom", "p_sharing_spread_rel", "total_delivered_dp_pu", "final_q_utilization",
            "max_final_s_over_sn", "transient_p_excess_over_pmax_pu", "final_vref_offset_pu", "final_p_margin_to_pmax_pu")}))
    print("differential", json.dumps({k: (np.round(v, 4).tolist() if isinstance(v, list) else round(v, 4)) for k, v in differential.items()}))
    print("E6 mean |V-1| final", e6_mean_err)
    return 0 if status != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
