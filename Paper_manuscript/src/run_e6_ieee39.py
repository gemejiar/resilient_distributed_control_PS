"""E6--C2: conventional consensus secondary frequency control on the frozen C2 case.

The C2 case file is read only and the primary control is left identical to E5.
An external loop (TDS ``callpert`` hook, evaluated once per fixed step) integrates
a power-increment command per unit i (system-base pu, ``Sn_i`` in system pu):

    dPset_i/dt = k_I [ (1 - omega_i) - k_P * sum_j a_ij (Pset_i/Sn_i - Pset_j/Sn_j) ]

i.e. the nominal law of Eq. (rdc) of the manuscript with g_P = 1 (no capability
factors), no leakage, D_P = diag(1/Sn_i), and the consensus acting on the secondary
increment so that the pre-event dispatch is not redistributed.  Actuation:
SG -> ``TGOV1N.paux0`` (system-base pu, verified empirically: delivered Pe follows it 1:1); GFM -> ``REGF1.Paux0 = KC (target - PIplim_y)``
because ``REGF1.Pref`` is initialization-only (a direct write has no effect; DEC-021).
No Q/V secondary.  Event: +58.564 MW at bus 4 at t = 5 s (as E5).
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
from run_e0_ieee39 import (  # noqa: E402
    ARTIFACTS_DIR, CRITICAL_BUSES, FIGURES_DIR, MATRIX_FILE,
    NOMINAL_FREQUENCY_HZ, PROJECT_ROOT, extract_time_series, git_commit, sha256,
)

CASE = e5.CASE
PREFIX = "IEEE39_E6_C2"
RAW_FILE = ARTIFACTS_DIR / f"{PREFIX}_timeseries.npz"
SUMMARY_FILE = ARTIFACTS_DIR / f"{PREFIX}_summary.json"
GRAPH_FILE = ARTIFACTS_DIR / "IEEE39_E6_C2_communication_graph.json"
E5_RAW = ARTIFACTS_DIR / "IEEE39_E5_C2_timeseries.npz"
E5_SUMMARY = ARTIFACTS_DIR / "IEEE39_E5_C2_summary.json"
FREQUENCY_FIGURE = FIGURES_DIR / f"{PREFIX}_frequency.png"
VOLTAGE_FIGURE = FIGURES_DIR / f"{PREFIX}_voltage.png"
SECONDARY_FIGURE = FIGURES_DIR / f"{PREFIX}_secondary.png"

EVENT_TIME_S = e5.EVENT_TIME_S
FINAL_TIME_S = 80.0
TIME_STEP_S = e5.TIME_STEP_S
REFINED_TIME_STEP_S = e5.REFINED_TIME_STEP_S
BASE_MVA = 100.0
EVENT_MW = 58.564
SECONDARY_START_S = EVENT_TIME_S
K_I, K_P = 20.0, 0.5          # declared a priori from time-scale estimates (see DEC-021)
KC_GFM = 0.05                 # Paux tracking gain, verified stable in the actuator test
SENSITIVITY_K_I = (10.0, 40.0)  # diagnostic only


def configure(k_i: float, time_step_s: float) -> tuple[Any, dict[str, Any]]:
    system = andes.load(str(CASE), setup=False, default_config=True, no_output=True)
    system.PQ.config.p2p, system.PQ.config.p2i, system.PQ.config.p2z = 1.0, 0.0, 0.0
    system.PQ.config.q2q, system.PQ.config.q2i, system.PQ.config.q2z = 1.0, 0.0, 0.0
    target = [str(i) for i, b in zip(system.PQ.idx.v, system.PQ.bus.v) if int(b) == 4]
    if len(target) != 1:
        raise RuntimeError(f"Expected one PQ at bus 4; found {target}.")
    system.add("Alter", idx="E6_P", t=EVENT_TIME_S, model="PQ", dev=target[0], src="Ppf",
               attr="v", method="+", amount=EVENT_MW / BASE_MVA)
    system.setup()
    system.TDS.config.tf = FINAL_TIME_S
    system.TDS.config.tstep = time_step_s
    system.TDS.config.fixt = 1
    system.TDS.config.no_tqdm = 1

    graph = json.loads(GRAPH_FILE.read_text(encoding="utf-8"))
    sg_bus = [int(b) for b in system.GENROU.bus.v]
    gfm_bus = [int(b) for b in system.REGF1.bus.v]
    unit_bus = sg_bus + gfm_bus
    pos = {b: i for i, b in enumerate(unit_bus)}
    adjacency = np.zeros((len(unit_bus), len(unit_bus)))
    for u, v in graph["edges"]:
        adjacency[pos[u], pos[v]] = adjacency[pos[v], pos[u]] = graph["weights"]
    laplacian = np.diag(adjacency.sum(1)) - adjacency
    tg_pos = [list(system.TGOV1N.syn.v).index(g) for g in system.GENROU.idx.v]
    bus_list = list(system.BusFreq.bus.v)
    freq_pos = [bus_list.index(b) for b in unit_bus]
    sn_mva = np.concatenate([np.asarray(system.GENROU.Sn.v, float), np.asarray(system.REGF1.Sn.v, float)])
    ctx = {
        "unit_bus": unit_bus, "n_sg": len(sg_bus), "laplacian": laplacian,
        "d_p": BASE_MVA / sn_mva, "sn_mva": sn_mva, "tg_pos": tg_pos, "freq_pos": freq_pos, "freq_addr": None,
        "y_addr": None, "k_i": k_i, "dp": np.zeros(len(unit_bus)),
        "last_t": -1.0, "y0": None, "log_t": [], "log_dp": [], "log_paux": [], "h": time_step_s,
    }

    def secondary(t: Any, sys_: Any) -> None:
        t = float(t)  # ``dae.t`` is mutated in place; keep a copy
        if ctx["y0"] is None:  # variable addresses exist only after TDS initialization
            ctx["freq_addr"] = np.asarray(sys_.BusFreq.f.a)[ctx["freq_pos"]]
            ctx["y_addr"] = np.asarray(sys_.REGF1.PIplim_y.a)
            ctx["y0"] = np.asarray(sys_.dae.y[ctx["y_addr"]], float).copy()
        if t <= ctx["last_t"]:
            return
        ctx["last_t"] = t
        if t >= SECONDARY_START_S:
            omega = np.asarray(sys_.dae.y[ctx["freq_addr"]], float)
            consensus = ctx["laplacian"] @ (ctx["dp"] * ctx["d_p"])
            ctx["dp"] = ctx["dp"] + ctx["h"] * ctx["k_i"] * ((1.0 - omega) - K_P * consensus)
        n_sg = ctx["n_sg"]
        sys_.TGOV1N.paux0.v[ctx["tg_pos"]] = ctx["dp"][:n_sg]
        y_now = np.asarray(sys_.dae.y[ctx["y_addr"]], float)
        paux = KC_GFM * (ctx["y0"] + ctx["dp"][n_sg:] - y_now)
        sys_.REGF1.Paux0.v[:] = paux
        ctx["log_t"].append(t)
        ctx["log_dp"].append(ctx["dp"].copy())
        ctx["log_paux"].append(paux.copy())

    system.TDS.callpert = secondary
    return system, ctx


def simulate(k_i: float, time_step_s: float) -> tuple[Any, dict[str, np.ndarray], dict[str, Any], dict[str, Any]]:
    system, ctx = configure(k_i, time_step_s)
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
    data["cmd_time_s"] = np.asarray(ctx["log_t"])
    data["cmd_dp_pu"] = np.asarray(ctx["log_dp"])
    data["cmd_gfm_paux_pu"] = np.asarray(ctx["log_paux"])
    data["unit_bus_ids"] = np.asarray(ctx["unit_bus"], dtype=int)
    data["unit_sn_mva"] = ctx["sn_mva"]
    diag = {"pflow_ok": pflow_ok, "tds_ok": tds_ok, "pflow_residual": pflow_residual,
            "final_residual": float(np.max(np.abs(system.dae.g))), "t_end_s": float(system.dae.ts.t[-1])}
    return system, data, diag, ctx


def secondary_metrics(system: Any, data: dict[str, np.ndarray]) -> dict[str, Any]:
    t = data["time_s"]
    pre = (EVENT_TIME_S - e5.SETTLING_WINDOW_S, EVENT_TIME_S)
    post = (t[-1] - e5.SETTLING_WINDOW_S, t[-1] + 1e-9)
    f_mean = data["bus_frequency_hz"].mean(axis=1)
    d_sg = e5.window_mean(t, data["sg_p_pu"], *post) - e5.window_mean(t, data["sg_p_pu"], *pre)
    d_gfm = e5.window_mean(t, data["gfm_p_pu"], *post) - e5.window_mean(t, data["gfm_p_pu"], *pre)
    delivered = np.concatenate([d_sg, d_gfm])
    command = data["cmd_dp_pu"][-1]
    sn_pu = data["unit_sn_mva"] / BASE_MVA
    share = delivered / sn_pu
    err = np.abs(delivered - command)
    after = t >= EVENT_TIME_S
    out_of_band = np.flatnonzero(np.abs(f_mean[after] - NOMINAL_FREQUENCY_HZ) > 0.002)
    return {
        "final_frequency_error_hz": float(e5.window_mean(t, f_mean, *post) - NOMINAL_FREQUENCY_HZ),
        "final_bus_frequency_spread_hz": float(np.ptp(e5.window_mean(t, data["bus_frequency_hz"], *post))),
        "frequency_nadir_hz": float(f_mean.min()),
        "settling_time_2mHz_s": float(t[after][out_of_band[-1]] - EVENT_TIME_S) if out_of_band.size else 0.0,
        "unit_bus_ids": data["unit_bus_ids"].tolist(),
        "commanded_dp_pu": command.tolist(), "delivered_dp_pu": delivered.tolist(),
        "command_tracking_abs_error_pu": err.tolist(),
        "delivered_dp_per_sn_pu": share.tolist(),
        "sharing_spread_rel": float((share.max() - share.min()) / share.mean()),
        "total_delivered_dp_pu": float(delivered.sum()),
        "event_pu": EVENT_MW / BASE_MVA,
        "max_gfm_paux_abs_pu": float(np.abs(data["cmd_gfm_paux_pu"]).max()),
    }


def run_case(k_i: float, time_step_s: float) -> dict[str, Any]:
    system, data, diag, _ = simulate(k_i, time_step_s)
    base = e5.metrics(system, data, "P+")
    return {"system": system, "data": data, "diag": diag, "base": base,
            "sec": secondary_metrics(system, data)}


def plot_frequency(run: dict[str, Any], e5_raw: Any) -> None:
    data = run["data"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    ids, f, t = data["frequency_bus_ids"], data["bus_frequency_hz"], data["time_s"]
    for axis, zoom in zip(axes, (False, True)):
        axis.fill_between(t, f.min(1), f.max(1), color="0.85", label="39-bus envelope")
        for col in np.flatnonzero(np.isin(ids, CRITICAL_BUSES)):
            axis.plot(t, f[:, col], lw=.8, label=f"Bus {ids[col]}")
        axis.plot(e5_raw["P+_time_s"], e5_raw["P+_bus_frequency_hz"].mean(1), "k--", lw=1.0, label="E5 mean (primary only)")
        axis.axhline(60, color="black", ls=":", lw=.8); axis.axvline(EVENT_TIME_S, color="tab:red", ls=":", lw=.8)
        axis.set_xlabel("Time [s]"); axis.grid(alpha=.25); axis.ticklabel_format(axis="y", style="plain", useOffset=False)
        if zoom:
            axis.set_ylim(59.985, 60.01); axis.set_title("zoom")
        else:
            axis.set_title("+58.564 MW at bus 4, consensus secondary")
    axes[0].set_ylabel("Frequency [Hz]"); axes[0].legend(ncol=3, fontsize=6)
    fig.suptitle("E6--C2: filtered bus frequency, primary + conventional consensus secondary")
    fig.tight_layout(); fig.savefig(FREQUENCY_FIGURE, dpi=300, bbox_inches="tight"); plt.close(fig)


def plot_voltage(run: dict[str, Any], e5_raw: Any) -> None:
    data = run["data"]
    ids, v, t = data["bus_ids"], data["bus_voltage_pu"], data["time_s"]
    fig, axis = plt.subplots(figsize=(8, 4.5))
    axis.fill_between(t, v.min(1), v.max(1), color="0.85", label="39-bus envelope")
    for col in np.flatnonzero(np.isin(ids, CRITICAL_BUSES)):
        axis.plot(t, v[:, col], lw=.8, label=f"Bus {ids[col]}")
    axis.axhline(e5_raw["P+_bus_voltage_pu"].min(), color="k", ls="--", lw=.9, label="E5 minimum")
    axis.axvline(EVENT_TIME_S, color="tab:red", ls=":", lw=.8)
    axis.set_xlabel("Time [s]"); axis.set_ylabel("Voltage |V| [pu]"); axis.grid(alpha=.25); axis.legend(ncol=4, fontsize=6)
    axis.set_title("E6--C2: bus-voltage response (no Q/V secondary)")
    fig.tight_layout(); fig.savefig(VOLTAGE_FIGURE, dpi=300, bbox_inches="tight"); plt.close(fig)


def plot_secondary(run: dict[str, Any]) -> None:
    data = run["data"]; t = data["cmd_time_s"]; bus = data["unit_bus_ids"]; n_sg = len(data["sg_bus_ids"])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for i, b in enumerate(bus):
        axes[0].plot(t, data["cmd_dp_pu"][:, i], lw=.9, ls="-" if i < n_sg else "--", label=f"{'SG' if i < n_sg else 'GFM'}{b}")
        axes[1].plot(t, data["cmd_dp_pu"][:, i] / (data["unit_sn_mva"][i] / BASE_MVA), lw=.9, ls="-" if i < n_sg else "--")
    axes[0].set_ylabel("Commanded increment dPset [pu, 100 MVA]"); axes[1].set_ylabel("dPset / Sn [pu on rating]")
    axes[0].legend(ncol=2, fontsize=6)
    for axis in axes:
        axis.set_xlabel("Time [s]"); axis.grid(alpha=.25); axis.axvline(EVENT_TIME_S, color="tab:red", ls=":", lw=.8)
    fig.suptitle("E6--C2: secondary commands and rating-proportional sharing")
    fig.tight_layout(); fig.savefig(SECONDARY_FIGURE, dpi=300, bbox_inches="tight"); plt.close(fig)


def update_matrix(summary: dict[str, Any]) -> None:
    with MATRIX_FILE.open("r", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream); fields = list(reader.fieldnames or [])
        rows = [row for row in reader if row.get("stage") != "E6"]
    m = summary["metrics"]["base"]
    row = {key: "" for key in fields}
    row.update({
        "run_id": summary["run_id"], "stage": "E6", "case": "C2_6SG_4GFM",
        "scenario": "P+1pct_primary_plus_consensus_secondary", "baseline": "E5_C2",
        "source_sha256": summary["case_sha256"], "variant_sha256": summary["case_sha256"],
        "andes_version": summary["andes_version"], "git_commit": summary["git_commit"],
        "seed": "not_applicable_deterministic", "simulation_t0": 0.0, "simulation_tf": FINAL_TIME_S,
        "solver_settings": json.dumps(summary["solver"], sort_keys=True), "event_time": EVENT_TIME_S,
        "event_bus": "4(P)", "event_P_MW": EVENT_MW, "fn_Hz": NOMINAL_FREQUENCY_HZ,
        "bus_freq_set": "1-39", "bus_volt_set": "1-39", "f_nadir_Hz": m["frequency_nadir_hz"],
        "max_RoCoF_Hz_s": m["max_abs_rocof_coi_hz_per_s"], "min_V_pu": m["voltage_min_pu"],
        "max_V_pu": m["voltage_max_pu"], "dae_residual": summary["diagnostics"]["final_residual"],
        "status_auto": summary["status_auto"], "status_human": "PENDING",
        "frequency_figure": FREQUENCY_FIGURE.relative_to(PROJECT_ROOT).as_posix(),
        "voltage_figure": VOLTAGE_FIGURE.relative_to(PROJECT_ROOT).as_posix(),
        "raw_file": RAW_FILE.relative_to(PROJECT_ROOT).as_posix(),
        "decision_note": "E7 remains blocked pending human approval of E6 figures.",
    })
    with MATRIX_FILE.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(rows + [row])


def main() -> int:
    e5_raw = np.load(E5_RAW)
    e5_vmin = json.loads(E5_SUMMARY.read_text(encoding="utf-8"))["metrics"]["P+"]["voltage_min_pu"]
    graph = json.loads(GRAPH_FILE.read_text(encoding="utf-8"))
    main_run = run_case(K_I, TIME_STEP_S)
    refined = run_case(K_I, REFINED_TIME_STEP_S)
    sensitivity: dict[str, Any] = {}
    for k_i in SENSITIVITY_K_I:
        r = run_case(k_i, TIME_STEP_S)
        sensitivity[str(k_i)] = {"diagnostics": r["diag"], "final_frequency_error_hz": r["sec"]["final_frequency_error_hz"],
                                 "frequency_nadir_hz": r["sec"]["frequency_nadir_hz"],
                                 "settling_time_2mHz_s": r["sec"]["settling_time_2mHz_s"],
                                 "sharing_spread_rel": r["sec"]["sharing_spread_rel"],
                                 "voltage_min_pu": r["base"]["voltage_min_pu"]}
    base, sec, diag = main_run["base"], main_run["sec"], main_run["diag"]
    numerical = {
        "frequency_nadir_abs_difference_hz": abs(base["frequency_nadir_hz"] - refined["base"]["frequency_nadir_hz"]),
        "voltage_min_abs_difference_pu": abs(base["voltage_min_pu"] - refined["base"]["voltage_min_pu"]),
        "final_frequency_error_difference_hz": abs(sec["final_frequency_error_hz"] - refined["sec"]["final_frequency_error_hz"]),
    }
    track_tol = np.maximum(0.10 * np.abs(sec["commanded_dp_pu"]), 0.005)
    checks = {
        "graph_connected_and_loss_tolerant": bool(graph["connected"] and graph["all_single_link_losses_ok"]
                                                  and graph["all_single_unit_losses_ok"]),
        "all_runs_converged": all(r["diag"]["pflow_ok"] and r["diag"]["tds_ok"] and r["diag"]["final_residual"] <= 1e-5
                                  and r["diag"]["t_end_s"] >= FINAL_TIME_S - 1e-6 for r in (main_run, refined)),
        "structure_6sg_4gfm": len(main_run["system"].GENROU.idx.v) == 6 and len(main_run["system"].REGF1.idx.v) == 4,
        "frequency_restored_within_1mHz": abs(sec["final_frequency_error_hz"]) <= 0.001,
        "all_units_increase_P": all(x > 0 for x in sec["delivered_dp_pu"]),
        "command_tracking_within_10pct_or_5e-3pu": bool(np.all(np.asarray(sec["command_tracking_abs_error_pu"]) <= track_tol)),
        "rating_proportional_sharing_within_10pct": sec["sharing_spread_rel"] <= 0.10,
        "total_generation_matches_event_within_10pct": abs(sec["total_delivered_dp_pu"] - sec["event_pu"]) <= 0.10 * sec["event_pu"],
        "no_unreported_saturation": not (base["gfm_limit_reached"] or base["governor_limit_reached"]),
        "voltage_min_not_worse_than_E5_by_5mpu": base["voltage_min_pu"] >= e5_vmin - 0.005,
        "numerical_convergence": numerical["frequency_nadir_abs_difference_hz"] <= .002
                                 and numerical["voltage_min_abs_difference_pu"] <= .005
                                 and numerical["final_frequency_error_difference_hz"] <= 0.001,
    }
    status = "PASS_AUTO_WAIT_HUMAN" if all(checks.values()) else "FAIL"
    np.savez_compressed(RAW_FILE, **main_run["data"])
    plot_frequency(main_run, e5_raw); plot_voltage(main_run, e5_raw); plot_secondary(main_run)
    system = main_run["system"]
    summary = {
        "run_id": f"{PREFIX}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "created_utc": datetime.now(timezone.utc).isoformat(), "status_auto": status, "status_human": "PENDING",
        "case": str(CASE.relative_to(PROJECT_ROOT)), "case_sha256": sha256(CASE),
        "runner_sha256": sha256(Path(__file__).resolve()), "graph_sha256": sha256(GRAPH_FILE),
        "git_commit": git_commit(), "python_version": platform.python_version(), "andes_version": andes.__version__,
        "controller": {"law": "dPset_i/dt = k_I[(1-omega_i) - k_P sum_j a_ij (dPset_i/Sn_i - dPset_j/Sn_j)]",
                       "k_I": K_I, "k_P": K_P, "kc_gfm_paux": KC_GFM, "secondary_start_s": SECONDARY_START_S,
                       "measurement": "local filtered BusFreq of each unit bus",
                       "sg_actuator": "TGOV1N.paux0 (system-base pu, verified empirically)",
                       "gfm_actuator": "REGF1.Paux0 = KC*(y0 + dPset - PIplim_y); REGF1.Pref is init-only"},
        "event": f"+{EVENT_MW} MW at bus 4, t = {EVENT_TIME_S} s",
        "solver": {"method": system.TDS.config.method, "tf_s": FINAL_TIME_S, "time_step_s": TIME_STEP_S,
                   "refined_time_step_s": REFINED_TIME_STEP_S, "tolerance": system.TDS.config.tol,
                   "maximum_iterations": system.TDS.config.max_iter},
        "diagnostics": diag, "metrics": {"base": base, "secondary": sec}, "e5_voltage_min_pu": e5_vmin,
        "refined": {"diagnostics": refined["diag"], "secondary": refined["sec"]},
        "numerical_step_comparison": numerical, "sensitivity_k_I_diagnostic": sensitivity, "checks": checks,
        "limitations": [
            "Conventional baseline: g_P = 1, no leakage, no capability factors; not the RDC.",
            "Gains k_I, k_P, KC were fixed a priori from time-scale estimates and not tuned; k_I sensitivity is diagnostic only.",
            "The consensus acts on the secondary increment, not on absolute power, so the pre-event dispatch is not redistributed.",
            "The loop is evaluated at the TDS fixed step by an external hook with zero communication delay and ideal measurement.",
            "No Q/V secondary; voltage is left to primary control.",
            "Sharing is by rating (Sn), not by headroom; headroom and capability weights enter in E7/E8.",
            "The cyber graph hub (bus 30, degree 9) is a structural single point of concentration even though connectivity survives its loss.",
            "No stability or safety certification; REGF1 has no energy/SoC model."],
    }
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    update_matrix(summary)
    print(json.dumps({"status_auto": status, "checks": checks, "numerical": numerical}, indent=2))
    print(json.dumps({k: sec[k] for k in ("final_frequency_error_hz", "final_bus_frequency_spread_hz", "frequency_nadir_hz",
                                          "settling_time_2mHz_s", "commanded_dp_pu", "delivered_dp_pu",
                                          "delivered_dp_per_sn_pu", "sharing_spread_rel", "total_delivered_dp_pu",
                                          "max_gfm_paux_abs_pu")}, indent=1))
    print("Vmin", base["voltage_min_pu"], "E5 Vmin", e5_vmin, "sens", json.dumps(sensitivity))
    return 0 if status != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
