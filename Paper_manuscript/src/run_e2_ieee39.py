"""Run E2: a 1% reactive-load step on the ten-SG IEEE 39-bus case."""

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

from run_e0_ieee39 import (  # noqa: E402
    ARTIFACTS_DIR,
    CRITICAL_BUSES,
    E0_CASE,
    FIGURES_DIR,
    MATRIX_FILE,
    NOMINAL_FREQUENCY_HZ,
    PROJECT_ROOT,
    extract_time_series,
    git_commit,
    prepare_case,
    sha256,
)


EVENT_TIME_S = 5.0
FINAL_TIME_S = 30.0
TARGET_BUS = 21
LOAD_INCREMENT_FRACTION = 0.01
TIME_STEP_S = 0.00390625
REFINED_TIME_STEP_S = TIME_STEP_S / 2
SETTLING_WINDOW_S = 1.0

RAW_FILE = ARTIFACTS_DIR / "IEEE39_E2_C0_timeseries.npz"
SUMMARY_FILE = ARTIFACTS_DIR / "IEEE39_E2_C0_summary.json"
FREQUENCY_FIGURE = FIGURES_DIR / "IEEE39_E2_C0_frequency.png"
VOLTAGE_FIGURE = FIGURES_DIR / "IEEE39_E2_C0_voltage.png"
REACTIVE_FIGURE = FIGURES_DIR / "IEEE39_E2_C0_reactive_excitation.png"


def configure_system(time_step_s: float) -> tuple[Any, float, float, str]:
    """Load C0, select constant-power PQ behavior, and add the E2 event."""
    system = andes.load(
        str(E0_CASE), setup=False, default_config=True, no_output=True
    )
    system.PQ.config.p2p = 1.0
    system.PQ.config.p2i = 0.0
    system.PQ.config.p2z = 0.0
    system.PQ.config.q2q = 1.0
    system.PQ.config.q2i = 0.0
    system.PQ.config.q2z = 0.0

    total_load_q_pu = float(np.sum(system.PQ.q0.v))
    increment_q_pu = LOAD_INCREMENT_FRACTION * total_load_q_pu
    targets = [
        idx for idx, bus in zip(system.PQ.idx.v, system.PQ.bus.v)
        if int(bus) == TARGET_BUS
    ]
    if len(targets) != 1:
        raise RuntimeError(f"Expected one PQ load at bus {TARGET_BUS}; found {targets}.")
    target_idx = str(targets[0])
    system.add(
        "Alter",
        idx="E2_REACTIVE_LOAD_STEP",
        t=EVENT_TIME_S,
        model="PQ",
        dev=target_idx,
        src="Qpf",
        attr="v",
        method="+",
        amount=increment_q_pu,
    )
    system.setup()
    system.TDS.config.tf = FINAL_TIME_S
    system.TDS.config.tstep = time_step_s
    system.TDS.config.fixt = 1
    system.TDS.config.no_tqdm = 1
    return system, total_load_q_pu, increment_q_pu, target_idx


def run_simulation(time_step_s: float) -> tuple[Any, dict[str, np.ndarray], dict[str, Any]]:
    """Execute PFlow/TDS and extract the physical channels used by E2."""
    system, total_q_pu, increment_q_pu, target_idx = configure_system(time_step_s)
    pflow_ok = bool(system.PFlow.run())
    pflow_residual = float(np.max(np.abs(system.dae.g)))
    tds_ok = bool(system.TDS.run(no_summary=True)) if pflow_ok else False
    data = extract_time_series(system)
    data["sg_reactive_power_pu"] = np.asarray(
        system.dae.ts.y[:, np.asarray(system.GENROU.Qe.a, dtype=int)], dtype=float
    )
    data["sg_field_voltage_pu"] = np.asarray(
        system.dae.ts.y[:, np.asarray(system.GENROU.vf.a, dtype=int)], dtype=float
    )
    data["event_time_s"] = np.asarray([EVENT_TIME_S], dtype=float)
    diagnostics: dict[str, Any] = {
        "pflow_ok": pflow_ok,
        "tds_ok": tds_ok,
        "pflow_residual": pflow_residual,
        "final_residual": float(np.max(np.abs(system.dae.g))),
        "total_load_q_pu": total_q_pu,
        "increment_q_pu": increment_q_pu,
        "system_mva": float(system.config.mva),
        "target_idx": target_idx,
    }
    return system, data, diagnostics


def compute_metrics(data: dict[str, np.ndarray]) -> dict[str, float]:
    """Compute E2 voltage, frequency, reactive-power, and excitation metrics."""
    time_s = data["time_s"]
    voltage_pu = data["bus_voltage_pu"]
    frequency_hz = data["bus_frequency_hz"]
    reactive_pu = data["sg_reactive_power_pu"]
    field_voltage_pu = data["sg_field_voltage_pu"]
    target_col = int(np.flatnonzero(data["bus_ids"] == TARGET_BUS)[0])
    pre = time_s < EVENT_TIME_S
    final = time_s >= FINAL_TIME_S - SETTLING_WINDOW_S
    prior = (time_s >= FINAL_TIME_S - 2 * SETTLING_WINDOW_S) & (
        time_s < FINAL_TIME_S - SETTLING_WINDOW_S
    )
    return {
        "minimum_bus_voltage_pu": float(np.min(voltage_pu)),
        "maximum_bus_voltage_pu": float(np.max(voltage_pu)),
        "minimum_bus21_voltage_pu": float(np.min(voltage_pu[:, target_col])),
        "pre_event_bus21_voltage_pu": float(np.mean(voltage_pu[pre, target_col])),
        "final_bus21_voltage_pu": float(np.mean(voltage_pu[final, target_col])),
        "maximum_abs_frequency_deviation_hz": float(
            np.max(np.abs(frequency_hz - NOMINAL_FREQUENCY_HZ))
        ),
        "final_mean_bus_frequency_hz": float(np.mean(frequency_hz[final])),
        "final_frequency_window_change_hz": float(
            abs(np.mean(frequency_hz[final]) - np.mean(frequency_hz[prior]))
        ),
        "pre_event_total_sg_reactive_power_pu": float(
            np.mean(np.sum(reactive_pu[pre], axis=1))
        ),
        "final_total_sg_reactive_power_pu": float(
            np.mean(np.sum(reactive_pu[final], axis=1))
        ),
        "pre_event_mean_field_voltage_pu": float(np.mean(field_voltage_pu[pre])),
        "final_mean_field_voltage_pu": float(np.mean(field_voltage_pu[final])),
    }


def relative_difference(value: float, reference: float) -> float:
    return abs(value - reference) / max(abs(reference), 1e-12)


def plot_frequency(data: dict[str, np.ndarray]) -> None:
    time_s = data["time_s"]
    bus_ids = data["frequency_bus_ids"]
    frequency_hz = data["bus_frequency_hz"]
    sg_frequency_hz = data["sg_frequency_hz"]
    critical = np.isin(bus_ids, CRITICAL_BUSES)
    fig, axes = plt.subplots(3, 1, figsize=(9, 9), sharex=True)
    for col in np.flatnonzero(critical):
        axes[0].plot(time_s, frequency_hz[:, col], label=f"Bus {bus_ids[col]}")
    axes[0].set_title("E2--C0: critical-bus filtered frequency")
    axes[0].legend(ncol=4, fontsize=8)
    axes[1].plot(time_s, frequency_hz[:, ~critical], color="0.72", lw=0.7, alpha=0.65)
    axes[1].plot(time_s, frequency_hz.min(axis=1), label="Minimum")
    axes[1].plot(time_s, frequency_hz.max(axis=1), label="Maximum")
    axes[1].set_title("Remaining filtered bus frequencies and envelope")
    axes[1].legend(fontsize=8)
    for col, bus in enumerate(data["sg_bus_ids"]):
        axes[2].plot(time_s, sg_frequency_hz[:, col], label=f"SG bus {bus}")
    axes[2].set_title("Unfiltered synchronous-generator rotor frequency")
    axes[2].set_xlabel("Time [s]")
    axes[2].legend(ncol=5, fontsize=7)
    for axis in axes:
        axis.axhline(NOMINAL_FREQUENCY_HZ, color="black", ls="--", lw=1)
        axis.axvline(EVENT_TIME_S, color="tab:red", ls=":", lw=1)
        axis.set_ylabel("Frequency [Hz]")
        axis.ticklabel_format(axis="y", style="plain", useOffset=False)
        axis.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(FREQUENCY_FIGURE, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_voltage(data: dict[str, np.ndarray]) -> None:
    time_s = data["time_s"]
    bus_ids = data["bus_ids"]
    voltage_pu = data["bus_voltage_pu"]
    critical = np.isin(bus_ids, CRITICAL_BUSES)
    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    for col in np.flatnonzero(critical):
        axes[0].plot(time_s, voltage_pu[:, col], label=f"Bus {bus_ids[col]}")
    axes[0].set_title("E2--C0: critical-bus voltage magnitude")
    axes[0].legend(ncol=4, fontsize=8)
    axes[1].plot(time_s, voltage_pu[:, ~critical], color="0.72", lw=0.7, alpha=0.65)
    axes[1].plot(time_s, voltage_pu.min(axis=1), label="Minimum")
    axes[1].plot(time_s, voltage_pu.max(axis=1), label="Maximum")
    axes[1].axhline(float(np.min(data["bus_voltage_min_pu"])), color="black", ls="--")
    axes[1].axhline(float(np.max(data["bus_voltage_max_pu"])), color="black", ls="--")
    axes[1].set_title("All buses, system envelope, and case limits")
    axes[1].set_xlabel("Time [s]")
    axes[1].legend(fontsize=8)
    for axis in axes:
        axis.axvline(EVENT_TIME_S, color="tab:red", ls=":", lw=1)
        axis.set_ylabel("Voltage |V| [pu]")
        axis.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(VOLTAGE_FIGURE, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_reactive_excitation(data: dict[str, np.ndarray]) -> None:
    time_s = data["time_s"]
    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    for col, bus in enumerate(data["sg_bus_ids"]):
        axes[0].plot(time_s, data["sg_reactive_power_pu"][:, col], label=f"SG bus {bus}")
        axes[1].plot(time_s, data["sg_field_voltage_pu"][:, col], label=f"SG bus {bus}")
    axes[0].set_title("Generator reactive-power response")
    axes[0].set_ylabel("Reactive power [pu]")
    axes[1].set_title("Generator field-voltage response")
    axes[1].set_ylabel("Field voltage [pu]")
    axes[1].set_xlabel("Time [s]")
    for axis in axes:
        axis.axvline(EVENT_TIME_S, color="tab:red", ls=":", lw=1)
        axis.legend(ncol=5, fontsize=7)
        axis.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(REACTIVE_FIGURE, dpi=300, bbox_inches="tight")
    plt.close(fig)


def update_matrix(summary: dict[str, Any]) -> None:
    with MATRIX_FILE.open("r", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames or [])
        rows = [row for row in reader if row.get("stage") != "E2"]
    row = {key: "" for key in fields}
    row.update(
        {
            "run_id": summary["run_id"], "stage": "E2", "case": "C0_10SG",
            "scenario": "reactive_load_step_1pct_bus21", "baseline": "E0_C0",
            "source_sha256": summary["source_sha256"],
            "variant_sha256": summary["variant_sha256"],
            "andes_version": summary["andes_version"], "git_commit": summary["git_commit"],
            "seed": "not_applicable_deterministic", "simulation_t0": 0.0,
            "simulation_tf": FINAL_TIME_S,
            "solver_settings": json.dumps(summary["solver"], sort_keys=True),
            "event_time": EVENT_TIME_S, "event_bus": TARGET_BUS,
            "event_P_MW": 0.0, "event_Q_MVAr": summary["event"]["increment_mvar"],
            "fn_Hz": NOMINAL_FREQUENCY_HZ, "bus_freq_set": "1-39",
            "bus_volt_set": "1-39",
            "f_nadir_Hz": NOMINAL_FREQUENCY_HZ - summary["metrics"]["maximum_abs_frequency_deviation_hz"],
            "min_V_pu": summary["metrics"]["minimum_bus_voltage_pu"],
            "max_V_pu": summary["metrics"]["maximum_bus_voltage_pu"],
            "dae_residual": summary["diagnostics"]["final_residual"],
            "status_auto": summary["status_auto"], "status_human": "PENDING",
            "frequency_figure": FREQUENCY_FIGURE.relative_to(PROJECT_ROOT).as_posix(),
            "voltage_figure": VOLTAGE_FIGURE.relative_to(PROJECT_ROOT).as_posix(),
            "raw_file": RAW_FILE.relative_to(PROJECT_ROOT).as_posix(),
            "decision_note": "E3 is not authorized until human review of E2 figures.",
        }
    )
    with MATRIX_FILE.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows + [row])


def main() -> int:
    prepare_case()
    system, data, diagnostics = run_simulation(TIME_STEP_S)
    _, refined_data, refined_diagnostics = run_simulation(REFINED_TIME_STEP_S)
    metrics = compute_metrics(data)
    refined_metrics = compute_metrics(refined_data)
    numerical = {
        "bus21_voltage_nadir_relative_difference": relative_difference(
            metrics["minimum_bus21_voltage_pu"], refined_metrics["minimum_bus21_voltage_pu"]
        ),
        "minimum_voltage_absolute_difference_pu": abs(
            metrics["minimum_bus_voltage_pu"] - refined_metrics["minimum_bus_voltage_pu"]
        ),
        "maximum_voltage_absolute_difference_pu": abs(
            metrics["maximum_bus_voltage_pu"] - refined_metrics["maximum_bus_voltage_pu"]
        ),
        "frequency_excursion_relative_difference": relative_difference(
            metrics["maximum_abs_frequency_deviation_hz"],
            refined_metrics["maximum_abs_frequency_deviation_hz"],
        ),
    }
    signs_ok = (
        metrics["minimum_bus21_voltage_pu"] < metrics["pre_event_bus21_voltage_pu"]
        and metrics["final_total_sg_reactive_power_pu"]
        > metrics["pre_event_total_sg_reactive_power_pu"]
        and metrics["final_mean_field_voltage_pu"]
        > metrics["pre_event_mean_field_voltage_pu"]
    )
    numerical_ok = (
        numerical["bus21_voltage_nadir_relative_difference"] <= 0.01
        and numerical["minimum_voltage_absolute_difference_pu"] <= 0.005
        and numerical["maximum_voltage_absolute_difference_pu"] <= 0.005
        and numerical["frequency_excursion_relative_difference"] <= 0.01
    )
    bounds_ok = (
        metrics["minimum_bus_voltage_pu"] >= float(np.min(data["bus_voltage_min_pu"]))
        and metrics["maximum_bus_voltage_pu"] <= float(np.max(data["bus_voltage_max_pu"]))
    )
    settled = metrics["final_frequency_window_change_hz"] <= 0.001
    automatic_pass = all(
        (
            diagnostics["pflow_ok"], diagnostics["tds_ok"],
            refined_diagnostics["pflow_ok"], refined_diagnostics["tds_ok"],
            signs_ok, numerical_ok, bounds_ok, settled,
            np.all(np.isfinite(data["bus_voltage_pu"])),
            np.all(np.isfinite(data["bus_frequency_hz"])),
        )
    )
    status_auto = "PASS_AUTO_WAIT_HUMAN" if automatic_pass else "FAIL"
    run_id = f"IEEE39_E2_C0_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    np.savez_compressed(RAW_FILE, **data)
    plot_frequency(data)
    plot_voltage(data)
    plot_reactive_excitation(data)
    summary: dict[str, Any] = {
        "run_id": run_id, "created_utc": datetime.now(timezone.utc).isoformat(),
        "status_auto": status_auto, "status_human": "PENDING",
        "source_case": str(E0_CASE.relative_to(PROJECT_ROOT)),
        "source_sha256": sha256(E0_CASE), "variant_sha256": sha256(E0_CASE),
        "runner_sha256": sha256(Path(__file__).resolve()), "git_commit": git_commit(),
        "python_version": platform.python_version(), "andes_version": andes.__version__,
        "event": {
            "time_s": EVENT_TIME_S, "bus": TARGET_BUS,
            "target_device": diagnostics["target_idx"],
            "total_initial_reactive_load_mvar": diagnostics["total_load_q_pu"] * diagnostics["system_mva"],
            "increment_fraction": LOAD_INCREMENT_FRACTION,
            "increment_mvar": diagnostics["increment_q_pu"] * diagnostics["system_mva"],
            "active_increment_mw": 0.0,
        },
        "solver": {
            "method": system.TDS.config.method, "t0_s": 0.0,
            "tf_s": FINAL_TIME_S, "time_step_s": TIME_STEP_S,
            "refined_time_step_s": REFINED_TIME_STEP_S,
            "tolerance": system.TDS.config.tol,
            "maximum_iterations": system.TDS.config.max_iter,
        },
        "diagnostics": diagnostics, "refined_diagnostics": refined_diagnostics,
        "metrics": metrics, "refined_metrics": refined_metrics,
        "numerical_step_comparison": numerical,
        "checks": {
            "physical_signs": signs_ok, "numerical_convergence": numerical_ok,
            "voltage_within_case_bounds": bounds_ok, "final_frequency_settled": settled,
        },
        "limitations": [
            "The run is a numerical reactive-load response test, not a nonlinear stability certificate.",
            "ANDES reports original-case GENROU warnings for xl <= xd2.",
            "Bus frequency uses the BusFreq filter; SG rotor frequency is stored separately.",
        ],
    }
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    update_matrix(summary)
    print(json.dumps(summary, indent=2))
    return 0 if automatic_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
