"""Run E1: a 1% active-load step on the ten-SG IEEE 39-bus case."""

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
    CASES_DIR,
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
TARGET_BUS = 4
LOAD_INCREMENT_FRACTION = 0.01
TIME_STEP_S = 0.00390625
REFINED_TIME_STEP_S = TIME_STEP_S / 2
SETTLING_WINDOW_S = 1.0
ROCOF_EXCLUSION_AFTER_EVENT_S = 0.1

RAW_FILE = ARTIFACTS_DIR / "IEEE39_E1_C0_timeseries.npz"
SUMMARY_FILE = ARTIFACTS_DIR / "IEEE39_E1_C0_summary.json"
LOGICAL_CASE = CASES_DIR / "ieee39_E0_C0_instrumented.xlsx"
FREQUENCY_FIGURE = FIGURES_DIR / "IEEE39_E1_C0_frequency.png"
VOLTAGE_FIGURE = FIGURES_DIR / "IEEE39_E1_C0_voltage.png"
POWER_FIGURE = FIGURES_DIR / "IEEE39_E1_C0_power.png"


def configure_system(time_step_s: float) -> tuple[Any, float, float, str]:
    """Load C0, configure constant-power load, and add the E1 event."""
    system = andes.load(
        str(LOGICAL_CASE), setup=False, default_config=True, no_output=True
    )
    system.PQ.config.p2p = 1.0
    system.PQ.config.p2i = 0.0
    system.PQ.config.p2z = 0.0
    system.PQ.config.q2q = 1.0
    system.PQ.config.q2i = 0.0
    system.PQ.config.q2z = 0.0

    total_load_pu = float(np.sum(system.PQ.p0.v))
    increment_pu = LOAD_INCREMENT_FRACTION * total_load_pu
    targets = [
        idx for idx, bus in zip(system.PQ.idx.v, system.PQ.bus.v)
        if int(bus) == TARGET_BUS
    ]
    if len(targets) != 1:
        raise RuntimeError(f"Expected one PQ load at bus {TARGET_BUS}; found {targets}.")
    target_idx = str(targets[0])
    system.add(
        "Alter",
        idx="E1_ACTIVE_LOAD_STEP",
        t=EVENT_TIME_S,
        model="PQ",
        dev=target_idx,
        src="Ppf",
        attr="v",
        method="+",
        amount=increment_pu,
    )
    system.setup()
    system.TDS.config.tf = FINAL_TIME_S
    system.TDS.config.tstep = time_step_s
    system.TDS.config.fixt = 1
    system.TDS.config.no_tqdm = 1
    return system, total_load_pu, increment_pu, target_idx


def run_simulation(time_step_s: float) -> tuple[Any, dict[str, np.ndarray], dict[str, float]]:
    """Execute PFlow and TDS and return raw arrays plus diagnostics."""
    system, total_load_pu, increment_pu, target_idx = configure_system(time_step_s)
    pflow_ok = bool(system.PFlow.run())
    pflow_residual = float(np.max(np.abs(system.dae.g)))
    tds_ok = bool(system.TDS.run(no_summary=True)) if pflow_ok else False
    data = extract_time_series(system)
    data["sg_mechanical_torque_pu"] = np.asarray(
        system.dae.ts.y[:, np.asarray(system.GENROU.tm.a, dtype=int)], dtype=float
    )
    data["sg_electrical_power_pu"] = np.asarray(
        system.dae.ts.y[:, np.asarray(system.GENROU.Pe.a, dtype=int)], dtype=float
    )
    data["event_time_s"] = np.asarray([EVENT_TIME_S], dtype=float)
    diagnostics = {
        "pflow_ok": float(pflow_ok),
        "tds_ok": float(tds_ok),
        "pflow_residual": pflow_residual,
        "final_residual": float(np.max(np.abs(system.dae.g))),
        "total_load_pu": total_load_pu,
        "increment_pu": increment_pu,
        "system_mva": float(system.config.mva),
        "target_idx": target_idx,
    }
    return system, data, diagnostics


def compute_metrics(data: dict[str, np.ndarray]) -> dict[str, float]:
    """Compute E1 metrics using explicit windows and units."""
    time_s = data["time_s"]
    frequency_hz = data["bus_frequency_hz"]
    voltage_pu = data["bus_voltage_pu"]
    mechanical = data["sg_mechanical_torque_pu"]
    electrical = data["sg_electrical_power_pu"]
    pre = time_s < EVENT_TIME_S
    final = time_s >= FINAL_TIME_S - SETTLING_WINDOW_S
    prior = (time_s >= FINAL_TIME_S - 2 * SETTLING_WINDOW_S) & (
        time_s < FINAL_TIME_S - SETTLING_WINDOW_S
    )
    rocof_hz_s = np.gradient(frequency_hz, time_s, axis=0)
    rocof_window = time_s >= EVENT_TIME_S + ROCOF_EXCLUSION_AFTER_EVENT_S

    return {
        "minimum_bus_frequency_hz": float(np.min(frequency_hz)),
        "maximum_abs_bus_rocof_hz_s": float(
            np.max(np.abs(rocof_hz_s[rocof_window]))
        ),
        "minimum_bus_voltage_pu": float(np.min(voltage_pu)),
        "maximum_bus_voltage_pu": float(np.max(voltage_pu)),
        "final_mean_bus_frequency_hz": float(np.mean(frequency_hz[final])),
        "final_frequency_window_change_hz": float(
            abs(np.mean(frequency_hz[final]) - np.mean(frequency_hz[prior]))
        ),
        "pre_event_mean_mechanical_torque_pu": float(np.mean(np.sum(mechanical[pre], axis=1))),
        "final_mean_mechanical_torque_pu": float(np.mean(np.sum(mechanical[final], axis=1))),
        "pre_event_mean_electrical_power_pu": float(np.mean(np.sum(electrical[pre], axis=1))),
        "final_mean_electrical_power_pu": float(np.mean(np.sum(electrical[final], axis=1))),
    }


def relative_difference(value: float, reference: float) -> float:
    """Return a safe relative difference with a physically meaningful scale."""
    scale = max(abs(reference), 1e-12)
    return abs(value - reference) / scale


def plot_frequency(data: dict[str, np.ndarray]) -> None:
    time_s = data["time_s"]
    bus_ids = data["frequency_bus_ids"]
    frequency_hz = data["bus_frequency_hz"]
    sg_frequency_hz = data["sg_frequency_hz"]
    sg_bus_ids = data["sg_bus_ids"]
    critical_mask = np.isin(bus_ids, CRITICAL_BUSES)

    fig, axes = plt.subplots(3, 1, figsize=(9.0, 9.0), sharex=True)
    for column in np.flatnonzero(critical_mask):
        axes[0].plot(time_s, frequency_hz[:, column], label=f"Bus {bus_ids[column]}")
    axes[0].set_title("E1--C0: critical-bus frequency")
    axes[0].legend(ncol=4, fontsize=8)

    remaining = frequency_hz[:, ~critical_mask]
    axes[1].plot(time_s, remaining, color="0.72", lw=0.7, alpha=0.65)
    axes[1].plot(time_s, frequency_hz.min(axis=1), color="tab:blue", label="Minimum")
    axes[1].plot(time_s, frequency_hz.max(axis=1), color="tab:red", label="Maximum")
    axes[1].set_title("Remaining buses and system envelope")
    axes[1].legend(fontsize=8)

    for column, bus in enumerate(sg_bus_ids):
        axes[2].plot(time_s, sg_frequency_hz[:, column], label=f"SG bus {bus}")
    axes[2].set_title("Synchronous-generator rotor frequency")
    axes[2].legend(ncol=5, fontsize=7)
    axes[2].set_xlabel("Time [s]")

    for axis in axes:
        axis.axhline(NOMINAL_FREQUENCY_HZ, color="black", lw=1, ls="--")
        axis.axvline(EVENT_TIME_S, color="tab:red", lw=1, ls=":")
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
    critical_mask = np.isin(bus_ids, CRITICAL_BUSES)

    fig, axes = plt.subplots(2, 1, figsize=(9.0, 7.0), sharex=True)
    for column in np.flatnonzero(critical_mask):
        axes[0].plot(time_s, voltage_pu[:, column], label=f"Bus {bus_ids[column]}")
    axes[0].set_title("E1--C0: critical-bus voltage magnitude")
    axes[0].legend(ncol=4, fontsize=8)

    axes[1].plot(time_s, voltage_pu[:, ~critical_mask], color="0.72", lw=0.7, alpha=0.65)
    axes[1].plot(time_s, voltage_pu.min(axis=1), color="tab:blue", label="Minimum")
    axes[1].plot(time_s, voltage_pu.max(axis=1), color="tab:red", label="Maximum")
    axes[1].axhline(float(np.min(data["bus_voltage_min_pu"])), color="black", ls="--")
    axes[1].axhline(float(np.max(data["bus_voltage_max_pu"])), color="black", ls="--")
    axes[1].set_title("All buses, system envelope, and case limits")
    axes[1].legend(fontsize=8)
    axes[1].set_xlabel("Time [s]")

    for axis in axes:
        axis.axvline(EVENT_TIME_S, color="tab:red", lw=1, ls=":")
        axis.set_ylabel("Voltage |V| [pu]")
        axis.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(VOLTAGE_FIGURE, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_power(data: dict[str, np.ndarray]) -> None:
    time_s = data["time_s"]
    sg_bus_ids = data["sg_bus_ids"]
    mechanical = data["sg_mechanical_torque_pu"]
    electrical = data["sg_electrical_power_pu"]
    fig, axes = plt.subplots(2, 1, figsize=(9.0, 7.0), sharex=True)
    for column, bus in enumerate(sg_bus_ids):
        axes[0].plot(time_s, mechanical[:, column], label=f"SG bus {bus}")
        axes[1].plot(time_s, electrical[:, column], label=f"SG bus {bus}")
    axes[0].set_ylabel("Mechanical torque [pu]")
    axes[0].set_title("Governor/mechanical response")
    axes[0].legend(ncol=5, fontsize=7)
    axes[1].set_ylabel("Electrical power [pu]")
    axes[1].set_xlabel("Time [s]")
    axes[1].set_title("Generator electrical-power response")
    axes[1].legend(ncol=5, fontsize=7)
    for axis in axes:
        axis.axvline(EVENT_TIME_S, color="tab:red", lw=1, ls=":")
        axis.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(POWER_FIGURE, dpi=300, bbox_inches="tight")
    plt.close(fig)


def update_matrix(summary: dict[str, Any]) -> None:
    with MATRIX_FILE.open("r", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames or [])
        rows = [row for row in reader if row.get("stage") != "E1"]
    row = {key: "" for key in fields}
    row.update(
        {
            "run_id": summary["run_id"], "stage": "E1", "case": "C0_10SG",
            "scenario": "active_load_step_1pct_bus4", "baseline": "E0_C0",
            "source_sha256": summary["source_sha256"],
            "variant_sha256": summary["variant_sha256"],
            "andes_version": summary["andes_version"], "git_commit": summary["git_commit"],
            "seed": "not_applicable_deterministic", "simulation_t0": 0.0,
            "simulation_tf": FINAL_TIME_S,
            "solver_settings": json.dumps(summary["solver"], sort_keys=True),
            "event_time": EVENT_TIME_S, "event_bus": TARGET_BUS,
            "event_P_MW": summary["event"]["increment_mw"], "event_Q_MVAr": 0.0,
            "fn_Hz": NOMINAL_FREQUENCY_HZ, "bus_freq_set": "1-39",
            "bus_volt_set": "1-39",
            "f_nadir_Hz": summary["metrics"]["minimum_bus_frequency_hz"],
            "max_RoCoF_Hz_s": summary["metrics"]["maximum_abs_bus_rocof_hz_s"],
            "min_V_pu": summary["metrics"]["minimum_bus_voltage_pu"],
            "max_V_pu": summary["metrics"]["maximum_bus_voltage_pu"],
            "dae_residual": summary["diagnostics"]["final_residual"],
            "status_auto": summary["status_auto"], "status_human": "PENDING",
            "frequency_figure": FREQUENCY_FIGURE.relative_to(PROJECT_ROOT).as_posix(),
            "voltage_figure": VOLTAGE_FIGURE.relative_to(PROJECT_ROOT).as_posix(),
            "raw_file": RAW_FILE.relative_to(PROJECT_ROOT).as_posix(),
            "decision_note": "E2 is not authorized until human review of E1 figures.",
        }
    )
    with MATRIX_FILE.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows + [row])


def main() -> int:
    prepare_case()
    main_system, data, diagnostics = run_simulation(TIME_STEP_S)
    _, refined_data, refined_diagnostics = run_simulation(REFINED_TIME_STEP_S)
    metrics = compute_metrics(data)
    refined_metrics = compute_metrics(refined_data)

    nadir_deviation = NOMINAL_FREQUENCY_HZ - metrics["minimum_bus_frequency_hz"]
    refined_nadir_deviation = NOMINAL_FREQUENCY_HZ - refined_metrics["minimum_bus_frequency_hz"]
    numerical = {
        "nadir_deviation_relative_difference": relative_difference(
            nadir_deviation, refined_nadir_deviation
        ),
        "minimum_voltage_absolute_difference_pu": abs(
            metrics["minimum_bus_voltage_pu"] - refined_metrics["minimum_bus_voltage_pu"]
        ),
        "maximum_voltage_absolute_difference_pu": abs(
            metrics["maximum_bus_voltage_pu"] - refined_metrics["maximum_bus_voltage_pu"]
        ),
        "rocof_relative_difference": relative_difference(
            metrics["maximum_abs_bus_rocof_hz_s"],
            refined_metrics["maximum_abs_bus_rocof_hz_s"],
        ),
    }
    signs_ok = (
        metrics["minimum_bus_frequency_hz"] < NOMINAL_FREQUENCY_HZ - 1e-4
        and metrics["final_mean_mechanical_torque_pu"]
        > metrics["pre_event_mean_mechanical_torque_pu"]
        and metrics["final_mean_electrical_power_pu"]
        > metrics["pre_event_mean_electrical_power_pu"]
    )
    numerical_ok = (
        numerical["nadir_deviation_relative_difference"] <= 0.01
        and numerical["minimum_voltage_absolute_difference_pu"] <= 0.005
        and numerical["maximum_voltage_absolute_difference_pu"] <= 0.005
        and numerical["rocof_relative_difference"] <= 0.05
    )
    bounds_ok = (
        metrics["minimum_bus_voltage_pu"] >= float(np.min(data["bus_voltage_min_pu"]))
        and metrics["maximum_bus_voltage_pu"] <= float(np.max(data["bus_voltage_max_pu"]))
    )
    settled = metrics["final_frequency_window_change_hz"] <= 0.001
    automatic_pass = all(
        (
            bool(diagnostics["pflow_ok"]), bool(diagnostics["tds_ok"]),
            bool(refined_diagnostics["pflow_ok"]), bool(refined_diagnostics["tds_ok"]),
            signs_ok, numerical_ok, bounds_ok, settled,
            np.all(np.isfinite(data["bus_frequency_hz"])),
            np.all(np.isfinite(data["bus_voltage_pu"])),
        )
    )
    status_auto = "PASS_AUTO_WAIT_HUMAN" if automatic_pass else "FAIL"
    run_id = f"IEEE39_E1_C0_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

    np.savez_compressed(RAW_FILE, **data)
    plot_frequency(data)
    plot_voltage(data)
    plot_power(data)
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
            "total_initial_active_load_mw": diagnostics["total_load_pu"] * diagnostics["system_mva"],
            "increment_fraction": LOAD_INCREMENT_FRACTION,
            "increment_mw": diagnostics["increment_pu"] * diagnostics["system_mva"],
            "reactive_increment_mvar": 0.0,
        },
        "solver": {
            "method": main_system.TDS.config.method, "t0_s": 0.0,
            "tf_s": FINAL_TIME_S, "time_step_s": TIME_STEP_S,
            "refined_time_step_s": REFINED_TIME_STEP_S,
            "tolerance": main_system.TDS.config.tol,
            "maximum_iterations": main_system.TDS.config.max_iter,
        },
        "diagnostics": diagnostics, "refined_diagnostics": refined_diagnostics,
        "metrics": metrics, "refined_metrics": refined_metrics,
        "numerical_step_comparison": numerical,
        "checks": {
            "physical_signs": signs_ok, "numerical_convergence": numerical_ok,
            "voltage_within_case_bounds": bounds_ok, "final_frequency_settled": settled,
        },
        "limitations": [
            "The run is a numerical response test, not a nonlinear stability certificate.",
            "ANDES reports original-case GENROU warnings for xl <= xd2.",
            "RoCoF is computed from the BusFreq output with Tf=Tw=0.02 s.",
            "RoCoF excludes the first 0.1 s after the ideal load step because the algebraic angle jump produces a step-size-dependent numerical impulse.",
        ],
    }
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    update_matrix(summary)
    print(json.dumps(summary, indent=2))
    return 0 if automatic_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
