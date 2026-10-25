"""Execute the next approved incremental SG-to-REGF1 replacement gate.

The configuration table is reusable for E4, E4.1, and E4.2.  Select the stage
with the first command-line argument (default E4).  Only stages whose
predecessor is human-approved may be run.
"""

from __future__ import annotations

import csv
import json
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import andes
import matplotlib
import numpy as np
from openpyxl import load_workbook

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from run_e0_ieee39 import (  # noqa: E402
    ARTIFACTS_DIR, CRITICAL_BUSES, FIGURES_DIR, MATRIX_FILE,
    NOMINAL_FREQUENCY_HZ, PROJECT_ROOT, extract_time_series, git_commit, sha256,
)

EVENT_TIME_S = 5.0
FINAL_TIME_S = 30.0
FLAT_FINAL_TIME_S = 10.0
TIME_STEP_S = 0.00390625
REFINED_TIME_STEP_S = TIME_STEP_S / 2
STEP_FRACTION = 0.01
P_EVENT_BUS = 4
Q_EVENT_BUS = 21

STAGES = {
    "E4": {
        "stage": "E4", "case_label": "C1_8SG_2GFM", "prefix": "IEEE39_E4_C1",
        "source_case": "ieee39_C0a_9SG_1GFM.xlsx",
        "variant_case": "ieee39_C1_8SG_2GFM.xlsx",
        "baseline": "E3_C0a", "baseline_summary": "IEEE39_E3_C0a_summary.json",
        "replacement_bus": 37, "static_gen": 8, "sn_mva": 970.2,
        "dynamic_rows": {
            "GENROU": "GENROU_8", "TGOV1N": "TGOV1_8",
            "IEEEX1": "IEEEX1_8", "IEEEST": "IEEEST_8",
        },
        "expected_sg": 8, "expected_gfm": 2, "gfm_buses": {32, 37},
        "next_stage": "E4.1",
    },
    "E4.1": {
        "stage": "E4.1", "case_label": "C1a_7SG_3GFM", "prefix": "IEEE39_E4_1_C1a",
        "source_case": "ieee39_C1_8SG_2GFM.xlsx",
        "variant_case": "ieee39_C1a_7SG_3GFM.xlsx",
        "baseline": "E4_C1", "baseline_summary": "IEEE39_E4_C1_summary.json",
        "replacement_bus": 34, "static_gen": 5, "sn_mva": 1080.2,
        "dynamic_rows": {
            "GENROU": "GENROU_5", "TGOV1N": "TGOV1_5",
            "IEEEX1": "IEEEX1_5", "IEEEST": "IEEEST_5",
        },
        "expected_sg": 7, "expected_gfm": 3, "gfm_buses": {32, 34, 37},
        "next_stage": "E4.2",
    },
    "E4.2": {
        "stage": "E4.2", "case_label": "C2_6SG_4GFM", "prefix": "IEEE39_E4_2_C2",
        "source_case": "ieee39_C1a_7SG_3GFM.xlsx",
        "variant_case": "ieee39_C2_6SG_4GFM.xlsx",
        "baseline": "E4_1_C1a", "baseline_summary": "IEEE39_E4_1_C1a_summary.json",
        "replacement_bus": 36, "static_gen": 7, "sn_mva": 1025.2,
        "dynamic_rows": {
            "GENROU": "GENROU_7", "TGOV1N": "TGOV1_7",
            "IEEEX1": "IEEEX1_7", "IEEEST": "IEEEST_7",
        },
        "expected_sg": 6, "expected_gfm": 4, "gfm_buses": {32, 34, 36, 37},
        "next_stage": "E5",
    },
}
CONFIG = STAGES[sys.argv[1] if len(sys.argv) > 1 else "E4"]
STAGE_TAG = CONFIG["stage"].replace(".", "_")
REPLACED = CONFIG["replacement_bus"]

SOURCE_CASE = PROJECT_ROOT / "Paper_manuscript" / "cases" / CONFIG["source_case"]
VARIANT_CASE = PROJECT_ROOT / "Paper_manuscript" / "cases" / CONFIG["variant_case"]
PREFIX = CONFIG["prefix"]
RAW_FILE = ARTIFACTS_DIR / f"{PREFIX}_timeseries.npz"
SUMMARY_FILE = ARTIFACTS_DIR / f"{PREFIX}_summary.json"
FREQUENCY_FIGURE = FIGURES_DIR / f"{PREFIX}_frequency.png"
VOLTAGE_FIGURE = FIGURES_DIR / f"{PREFIX}_voltage.png"
POWER_FIGURE = FIGURES_DIR / f"{PREFIX}_gfm_power.png"
BASELINE_SUMMARY = ARTIFACTS_DIR / CONFIG["baseline_summary"]


def build_variant() -> None:
    """Create the variant from the approved predecessor without modifying it."""
    if VARIANT_CASE.exists():
        return
    shutil.copy2(SOURCE_CASE, VARIANT_CASE)
    workbook = load_workbook(VARIANT_CASE)
    for sheet_name, idx in CONFIG["dynamic_rows"].items():
        sheet = workbook[sheet_name]
        idx_col = [cell.value for cell in sheet[1]].index("idx") + 1
        rows = [r for r in range(2, sheet.max_row + 1)
                if str(sheet.cell(r, idx_col).value) == idx]
        if len(rows) != 1:
            raise RuntimeError(f"Expected one {idx} in {sheet_name}; found {rows}.")
        sheet.delete_rows(rows[0], 1)
    sheet = workbook["REGF1"]
    existing = {str(sheet.cell(r, 2).value) for r in range(2, sheet.max_row + 1)}
    new_idx = f"REGF1_{REPLACED}"
    if new_idx in existing:
        raise RuntimeError(f"{new_idx} already exists in the source case.")
    sheet.append([1, new_idx, 1, f"GFM{REPLACED}", REPLACED,
                  CONFIG["static_gen"], CONFIG["sn_mva"], NOMINAL_FREQUENCY_HZ])
    workbook.save(VARIANT_CASE)


def configure_system(scenario: str | tuple[str, str], time_step_s: float) -> tuple[Any, dict[str, float]]:
    system = andes.load(str(VARIANT_CASE), setup=False, default_config=True, no_output=True)
    system.PQ.config.p2p, system.PQ.config.p2i, system.PQ.config.p2z = 1.0, 0.0, 0.0
    system.PQ.config.q2q, system.PQ.config.q2i, system.PQ.config.q2z = 1.0, 0.0, 0.0
    event = {"p_pu": 0.0, "q_pu": 0.0, "bus": 0.0}
    if scenario != "flat":
        channel, sign = scenario
        source = "Ppf" if channel == "P" else "Qpf"
        bus = P_EVENT_BUS if channel == "P" else Q_EVENT_BUS
        total = float(np.sum(system.PQ.p0.v if channel == "P" else system.PQ.q0.v))
        amount = STEP_FRACTION * total
        targets = [str(idx) for idx, device_bus in zip(system.PQ.idx.v, system.PQ.bus.v)
                   if int(device_bus) == bus]
        if len(targets) != 1:
            raise RuntimeError(f"Expected one PQ device at bus {bus}; found {targets}.")
        system.add("Alter", idx=f"{STAGE_TAG}_{channel}_{sign}", t=EVENT_TIME_S,
                   model="PQ", dev=targets[0], src=source, attr="v",
                   method=sign, amount=amount)
        event = {"p_pu": amount * (channel == "P"),
                 "q_pu": amount * (channel == "Q"), "bus": float(bus)}
    system.setup()
    system.TDS.config.tf = FLAT_FINAL_TIME_S if scenario == "flat" else FINAL_TIME_S
    system.TDS.config.tstep = time_step_s
    system.TDS.config.fixt = 1
    system.TDS.config.no_tqdm = 1
    return system, event


def extract_gfm_series(system: Any) -> dict[str, np.ndarray]:
    data = extract_time_series(system)
    x, y = system.dae.ts.x, system.dae.ts.y
    data["gfm_ids"] = np.asarray(system.REGF1.idx.v, dtype=str)
    data["gfm_bus_ids"] = np.asarray(system.REGF1.bus.v, dtype=int)
    data["gfm_active_power_pu"] = np.asarray(y[:, system.REGF1.Pe.a], dtype=float)
    data["gfm_reactive_power_pu"] = np.asarray(y[:, system.REGF1.Qe.a], dtype=float)
    data["gfm_voltage_pu"] = np.asarray(y[:, system.REGF1.v.a], dtype=float)
    p_sensed = np.asarray(x[:, system.REGF1.Psen_y.a], dtype=float)
    p_limited = np.asarray(y[:, system.REGF1.PIplim_y.a], dtype=float)
    scale = np.asarray(system.REGF1.w0.v * system.REGF1.wdrp.v, dtype=float)
    dw = np.clip((p_limited - p_sensed) * scale,
                 np.asarray(system.REGF1.dwmin.v), np.asarray(system.REGF1.dwmax.v))
    data["gfm_frequency_hz"] = NOMINAL_FREQUENCY_HZ + dw / (2 * np.pi)
    return data


def simulate(scenario: str | tuple[str, str], time_step_s: float) -> tuple[Any, dict[str, np.ndarray], dict[str, Any]]:
    system, event = configure_system(scenario, time_step_s)
    pflow_ok = bool(system.PFlow.run())
    pflow_residual = float(np.max(np.abs(system.dae.g)))
    tds_ok = bool(system.TDS.run(no_summary=True)) if pflow_ok else False
    data = extract_gfm_series(system)
    return system, data, {
        "pflow_ok": pflow_ok, "tds_ok": tds_ok,
        "pflow_residual": pflow_residual,
        "final_residual": float(np.max(np.abs(system.dae.g))), "event": event,
    }


def compute_metrics(data: dict[str, np.ndarray], scenario: str) -> dict[str, Any]:
    t, f, v = data["time_s"], data["bus_frequency_hz"], data["bus_voltage_pu"]
    pre = t < (EVENT_TIME_S if scenario != "flat" else min(2.0, t[-1]))
    final = t >= t[-1] - 1.0
    return {
        "frequency_min_hz": float(np.min(f)), "frequency_max_hz": float(np.max(f)),
        "voltage_min_pu": float(np.min(v)), "voltage_max_pu": float(np.max(v)),
        "final_mean_frequency_hz": float(np.mean(f[final])),
        "final_mean_voltage_pu": float(np.mean(v[final])),
        "pre_gfm_p_pu": np.mean(data["gfm_active_power_pu"][pre], axis=0).tolist(),
        "final_gfm_p_pu": np.mean(data["gfm_active_power_pu"][final], axis=0).tolist(),
        "pre_gfm_q_pu": np.mean(data["gfm_reactive_power_pu"][pre], axis=0).tolist(),
        "final_gfm_q_pu": np.mean(data["gfm_reactive_power_pu"][final], axis=0).tolist(),
        "flat_frequency_drift_hz": float(np.max(np.abs(f[-1] - f[0]))),
        "flat_voltage_drift_pu": float(np.max(np.abs(v[-1] - v[0]))),
    }


def run_eig() -> dict[str, Any]:
    system, _ = configure_system("flat", TIME_STEP_S)
    pflow_ok = bool(system.PFlow.run())
    eig_ok = bool(system.EIG.run()) if pflow_ok else False
    values = np.asarray(system.EIG.mu, dtype=complex)
    values = values[np.isfinite(values)]
    state_names = np.asarray(system.EIG.x_name, dtype=str)
    degenerate = np.asarray(
        [idx for idx, name in enumerate(state_names)
         if name.startswith("F1_y IEEEST")], dtype=int
    )
    # In this stock case every remaining IEEEST has A1=A2=0. Lag2ndOrd
    # therefore contains a zero-time-constant internal state and a constant
    # output state. ANDES 2.0.0 constraint reduction retains these outputs in
    # C1 as +1 diagonal rows, although they are zero/degenerate modes in the
    # defining equations. Preserve the raw result, then evaluate the remaining
    # physical subspace after removing exactly those documented states.
    # The constraint reduction may retain the degenerate output as F1_y for
    # only some units (others appear as F2_x2 with zero diagonal), so require
    # that every retained F1_y row is +1 and accounts for every raw unstable mode.
    state_matrix = np.asarray(system.EIG.As, dtype=float)
    ieeest_degeneracy_verified = bool(
        0 < degenerate.size <= len(system.IEEEST.idx.v)
        and np.allclose(np.diag(state_matrix)[degenerate], 1.0)
        and int(np.sum(values.real > 1e-6)) == degenerate.size
        and np.allclose(system.IEEEST.A1.v, 0.0)
        and np.allclose(system.IEEEST.A2.v, 0.0)
    )
    keep = np.asarray([idx for idx in range(state_matrix.shape[0])
                       if idx not in set(degenerate.tolist())], dtype=int)
    physical_values = np.linalg.eigvals(state_matrix[np.ix_(keep, keep)])
    raw_positive = int(np.sum(values.real > 1e-6))
    physical_positive = int(np.sum(physical_values.real > 1e-6))
    return {
        "pflow_ok": pflow_ok, "eig_ok": eig_ok, "eigenvalue_count": int(values.size),
        "raw_maximum_real_part": float(np.max(values.real)),
        "raw_unstable_mode_count": raw_positive,
        "near_zero_mode_count": int(np.sum(np.abs(values.real) <= 1e-8)),
        "ieeest_degeneracy_verified": ieeest_degeneracy_verified,
        "excluded_degenerate_state_names": state_names[degenerate].tolist(),
        "excluded_state_matrix_diagonal": np.diag(state_matrix)[degenerate].tolist(),
        "physical_subspace_maximum_real_part": float(np.max(physical_values.real)),
        "physical_subspace_unstable_mode_count": physical_positive,
        "eigenvalues_real": values.real.tolist(), "eigenvalues_imag": values.imag.tolist(),
        "physical_subspace_eigenvalues_real": physical_values.real.tolist(),
        "physical_subspace_eigenvalues_imag": physical_values.imag.tolist(),
    }


def plot_frequency(all_data: dict[str, dict[str, np.ndarray]]) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), sharex=True, sharey=True)
    for axis, (name, data) in zip(axes.flat, all_data.items()):
        ids, f = data["frequency_bus_ids"], data["bus_frequency_hz"]
        axis.fill_between(data["time_s"], f.min(1), f.max(1), color="0.85", label="39-bus envelope")
        for col in np.flatnonzero(np.isin(ids, CRITICAL_BUSES)):
            axis.plot(data["time_s"], f[:, col], lw=.8, label=f"Bus {ids[col]}")
        for col, bus in enumerate(data["gfm_bus_ids"]):
            axis.plot(data["time_s"], data["gfm_frequency_hz"][:, col], "--", lw=1.1,
                      label=f"GFM{bus}")
        axis.axhline(60, color="black", ls=":", lw=.8)
        axis.axvline(EVENT_TIME_S, color="tab:red", ls=":", lw=.8)
        axis.set_title(name); axis.grid(alpha=.25)
        axis.ticklabel_format(axis="y", style="plain", useOffset=False)
    axes[0, 0].legend(ncol=3, fontsize=6)
    for axis in axes[:, 0]: axis.set_ylabel("Frequency [Hz]")
    for axis in axes[-1, :]: axis.set_xlabel("Time [s]")
    fig.suptitle(f"{CONFIG['stage']}--{CONFIG['case_label'].split('_')[0]}: filtered bus and GFM frequencies")
    fig.tight_layout(); fig.savefig(FREQUENCY_FIGURE, dpi=300, bbox_inches="tight"); plt.close(fig)


def plot_voltage(all_data: dict[str, dict[str, np.ndarray]]) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), sharex=True)
    for axis, (name, data) in zip(axes.flat, all_data.items()):
        ids, v = data["bus_ids"], data["bus_voltage_pu"]
        axis.fill_between(data["time_s"], v.min(1), v.max(1), color="0.85", label="39-bus envelope")
        for col in np.flatnonzero(np.isin(ids, CRITICAL_BUSES)):
            axis.plot(data["time_s"], v[:, col], lw=.8, label=f"Bus {ids[col]}")
        axis.axvline(EVENT_TIME_S, color="tab:red", ls=":", lw=.8)
        axis.set_title(name); axis.grid(alpha=.25)
    axes[0, 0].legend(ncol=4, fontsize=6)
    for axis in axes[:, 0]: axis.set_ylabel("Voltage |V| [pu]")
    for axis in axes[-1, :]: axis.set_xlabel("Time [s]")
    fig.suptitle(f"{CONFIG['stage']}--{CONFIG['case_label'].split('_')[0]}: bus-voltage response")
    fig.tight_layout(); fig.savefig(VOLTAGE_FIGURE, dpi=300, bbox_inches="tight"); plt.close(fig)


def plot_power(all_data: dict[str, dict[str, np.ndarray]]) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), sharex=True)
    for axis, (name, data) in zip(axes.flat, all_data.items()):
        for col, bus in enumerate(data["gfm_bus_ids"]):
            axis.plot(data["time_s"], data["gfm_active_power_pu"][:, col],
                      label=f"P GFM{bus}")
            axis.plot(data["time_s"], data["gfm_reactive_power_pu"][:, col], "--",
                      label=f"Q GFM{bus}")
        axis.axvline(EVENT_TIME_S, color="tab:red", ls=":")
        axis.set_title(name); axis.set_ylabel("Delivered power [pu]"); axis.grid(alpha=.25)
    axes[0, 0].legend(ncol=2, fontsize=7)
    for axis in axes[-1, :]: axis.set_xlabel("Time [s]")
    fig.suptitle(f"{CONFIG['stage']}--{CONFIG['case_label'].split('_')[0]}: delivered GFM active and reactive power")
    fig.tight_layout(); fig.savefig(POWER_FIGURE, dpi=300, bbox_inches="tight"); plt.close(fig)


def update_matrix(summary: dict[str, Any]) -> None:
    with MATRIX_FILE.open("r", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream); fields = list(reader.fieldnames or [])
        rows = [row for row in reader if row.get("stage") != CONFIG["stage"]]
    row = {key: "" for key in fields}
    row.update({
        "run_id": summary["run_id"], "stage": CONFIG["stage"], "case": CONFIG["case_label"],
        "scenario": "flat_and_small_signed_P_Q_steps", "baseline": CONFIG["baseline"],
        "source_sha256": summary["source_sha256"], "variant_sha256": summary["variant_sha256"],
        "andes_version": summary["andes_version"], "git_commit": summary["git_commit"],
        "seed": "not_applicable_deterministic", "simulation_t0": 0.0, "simulation_tf": FINAL_TIME_S,
        "solver_settings": json.dumps(summary["solver"], sort_keys=True), "event_time": EVENT_TIME_S,
        "event_bus": "4(P);21(Q)", "event_P_MW": summary["events"]["P+_mw"],
        "event_Q_MVAr": summary["events"]["Q+_mvar"], "fn_Hz": NOMINAL_FREQUENCY_HZ,
        "bus_freq_set": "1-39", "bus_volt_set": "1-39",
        "f_nadir_Hz": summary["metrics"]["P+"]["frequency_min_hz"],
        "min_V_pu": min(item["voltage_min_pu"] for item in summary["metrics"].values()),
        "max_V_pu": max(item["voltage_max_pu"] for item in summary["metrics"].values()),
        "dae_residual": max(item["final_residual"] for item in summary["diagnostics"].values()),
        "status_auto": summary["status_auto"], "status_human": "PENDING",
        "frequency_figure": FREQUENCY_FIGURE.relative_to(PROJECT_ROOT).as_posix(),
        "voltage_figure": VOLTAGE_FIGURE.relative_to(PROJECT_ROOT).as_posix(),
        "raw_file": RAW_FILE.relative_to(PROJECT_ROOT).as_posix(),
        "decision_note": f"{CONFIG['next_stage']} remains blocked pending human approval of {CONFIG['stage']} figures.",
    })
    with MATRIX_FILE.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(rows + [row])


def main() -> int:
    build_variant()
    scenarios = {"P+": ("P", "+"), "P-": ("P", "-"),
                 "Q+": ("Q", "+"), "Q-": ("Q", "-")}
    flat_system, flat_data, flat_diag = simulate("flat", TIME_STEP_S)
    data_by_scenario: dict[str, dict[str, np.ndarray]] = {}
    diagnostics: dict[str, Any] = {"flat": flat_diag}
    metric_values: dict[str, Any] = {"flat": compute_metrics(flat_data, "flat")}
    for name, scenario in scenarios.items():
        _, data, diag = simulate(scenario, TIME_STEP_S)
        data_by_scenario[name] = data; diagnostics[name] = diag
        metric_values[name] = compute_metrics(data, name)
    refined: dict[str, Any] = {}
    for name in ("P+", "Q+"):
        _, data, diag = simulate(scenarios[name], REFINED_TIME_STEP_S)
        refined[name] = {"diagnostics": diag, "metrics": compute_metrics(data, name)}
    eig = run_eig()
    numerical = {
        name: {
            "frequency_min_abs_difference_hz": abs(metric_values[name]["frequency_min_hz"] - refined[name]["metrics"]["frequency_min_hz"]),
            "voltage_min_abs_difference_pu": abs(metric_values[name]["voltage_min_pu"] - refined[name]["metrics"]["voltage_min_pu"]),
        } for name in refined
    }
    structure_ok = (len(flat_system.GENROU.idx.v) == CONFIG["expected_sg"]
                    and len(flat_system.REGF1.idx.v) == CONFIG["expected_gfm"]
                    and CONFIG["dynamic_rows"]["GENROU"] not in flat_system.GENROU.idx.v
                    and set(flat_system.REGF1.bus.v) == CONFIG["gfm_buses"])
    flat_ok = (metric_values["flat"]["flat_frequency_drift_hz"] <= 1e-4
               and metric_values["flat"]["flat_voltage_drift_pu"] <= 1e-5)
    signs_ok = (metric_values["P+"]["frequency_min_hz"] < metric_values["P-"]["frequency_min_hz"]
                and metric_values["Q+"]["final_mean_voltage_pu"] < metric_values["Q-"]["final_mean_voltage_pu"])
    numerical_ok = all(v["frequency_min_abs_difference_hz"] <= .002
                       and v["voltage_min_abs_difference_pu"] <= .002 for v in numerical.values())
    runs_ok = all(v["pflow_ok"] and v["tds_ok"] and v["final_residual"] <= 1e-5
                  for v in diagnostics.values())
    both_inject = all(np.all(np.asarray(metric_values[s]["pre_gfm_p_pu"]) > 0) for s in metric_values)
    automatic_pass = all((structure_ok, flat_ok, signs_ok, numerical_ok, runs_ok,
                          both_inject, eig["eig_ok"], eig["ieeest_degeneracy_verified"],
                          eig["physical_subspace_unstable_mode_count"] == 0))
    status = "PASS_AUTO_WAIT_HUMAN" if automatic_pass else "FAIL"
    raw: dict[str, np.ndarray] = {}
    for name, data in {"flat": flat_data, **data_by_scenario}.items():
        for key, value in data.items(): raw[f"{name}_{key}"] = value
    np.savez_compressed(RAW_FILE, **raw)
    plot_frequency(data_by_scenario); plot_voltage(data_by_scenario); plot_power(data_by_scenario)
    e3 = json.loads(BASELINE_SUMMARY.read_text(encoding="utf-8"))
    comparison = {
        "P+_frequency_nadir_change_vs_baseline_hz": metric_values["P+"]["frequency_min_hz"] - e3["metrics"]["P+"]["frequency_min_hz"],
        "P+_minimum_voltage_change_vs_baseline_pu": metric_values["P+"]["voltage_min_pu"] - e3["metrics"]["P+"]["voltage_min_pu"],
        "Q+_minimum_voltage_change_vs_baseline_pu": metric_values["Q+"]["voltage_min_pu"] - e3["metrics"]["Q+"]["voltage_min_pu"],
    }
    summary = {
        "run_id": f"{PREFIX}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "created_utc": datetime.now(timezone.utc).isoformat(), "status_auto": status,
        "status_human": "PENDING", "source_case": str(SOURCE_CASE.relative_to(PROJECT_ROOT)),
        "variant_case": str(VARIANT_CASE.relative_to(PROJECT_ROOT)),
        "source_sha256": sha256(SOURCE_CASE), "variant_sha256": sha256(VARIANT_CASE),
        "runner_sha256": sha256(Path(__file__).resolve()), "git_commit": git_commit(),
        "python_version": platform.python_version(), "andes_version": andes.__version__,
        "configuration": {**CONFIG, "gfm_buses": list(map(int, flat_system.REGF1.bus.v)),
                          "gfm_static_generators": list(map(int, flat_system.REGF1.gen.v)),
                          "gfm_sn_mva": list(map(float, flat_system.REGF1.Sn.v)),
                          "parameter_policy": "ANDES 2.0.0 REGF1 defaults except bus, gen, Sn, fn"},
        "events": {"P+_mw": diagnostics["P+"]["event"]["p_pu"] * flat_system.config.mva,
                   "P-_mw": -diagnostics["P-"]["event"]["p_pu"] * flat_system.config.mva,
                   "Q+_mvar": diagnostics["Q+"]["event"]["q_pu"] * flat_system.config.mva,
                   "Q-_mvar": -diagnostics["Q-"]["event"]["q_pu"] * flat_system.config.mva},
        "solver": {"method": flat_system.TDS.config.method, "tf_flat_s": FLAT_FINAL_TIME_S,
                   "tf_step_s": FINAL_TIME_S, "time_step_s": TIME_STEP_S,
                   "refined_time_step_s": REFINED_TIME_STEP_S,
                   "tolerance": flat_system.TDS.config.tol,
                   "maximum_iterations": flat_system.TDS.config.max_iter},
        "diagnostics": diagnostics, "metrics": metric_values, "refined": refined,
        "numerical_step_comparison": numerical, "comparison_with_baseline": comparison,
        "eigenanalysis": eig,
        "checks": {"flat_no_drift": flat_ok, "response_signs": signs_ok,
                   "numerical_convergence": numerical_ok, "all_runs_converged": runs_ok,
                   "structure_no_duplicate": structure_ok,
                   "both_gfm_inject_active_power": both_inject,
                   "no_positive_eigenvalues_in_physical_subspace": eig["physical_subspace_unstable_mode_count"] == 0},
        "limitations": ["REGF1 is a positive-sequence RMS model and contains no BESS state-of-charge model.",
                        "Raw EIG contains eight spurious +1 modes from degenerate IEEEST F1 blocks (A1=A2=0); the documented reduced physical subspace has no positive modes.",
                        "EIG evidence is local; degenerate modes and conditioning warnings preclude a strict Hurwitz claim.",
                        "The signed 1% load steps are diagnostic and do not establish nonlinear safety."],
    }
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    update_matrix(summary)
    print(json.dumps({"status_auto": status, "checks": summary["checks"],
                      "events": summary["events"], "comparison_with_baseline": comparison,
                      "eigenanalysis": {k: v for k, v in eig.items()
                                        if "eigenvalues_" not in k and k != "excluded_degenerate_state_names"}}, indent=2))
    return 0 if automatic_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
