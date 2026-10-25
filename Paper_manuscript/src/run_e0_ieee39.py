"""Run the E0 flat-start validation for the ANDES IEEE 39-bus case.

The script copies the ANDES-distributed dynamic case into the project, creates
an instrumented variant without active secondary/event devices, adds BusFreq
measurements at every bus, and generates the raw data and the two mandatory
supervision figures. It does not modify the ANDES-distributed source case.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import andes
import matplotlib
import numpy as np
from openpyxl import load_workbook

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CASES_DIR = PROJECT_ROOT / "Paper_manuscript" / "cases"
ARTIFACTS_DIR = PROJECT_ROOT / "Paper_manuscript" / "artifacts"
FIGURES_DIR = PROJECT_ROOT / "Paper_manuscript" / "figures_main"

SOURCE_CASE = Path(andes.get_case("ieee39/ieee39_full.xlsx")).resolve()
BASE_CASE = CASES_DIR / "ieee39_base_original.xlsx"
E0_CASE = CASES_DIR / "ieee39_E0_C0_instrumented.xlsx"
RAW_FILE = ARTIFACTS_DIR / "IEEE39_E0_C0_timeseries.npz"
SUMMARY_FILE = ARTIFACTS_DIR / "IEEE39_E0_C0_summary.json"
MATRIX_FILE = ARTIFACTS_DIR / "experiment_matrix.csv"
FREQUENCY_FIGURE = FIGURES_DIR / "IEEE39_E0_C0_frequency.png"
VOLTAGE_FIGURE = FIGURES_DIR / "IEEE39_E0_C0_voltage.png"

CRITICAL_BUSES = (4, 21, 32, 34, 36, 37, 39)
NOMINAL_FREQUENCY_HZ = 60.0
FINAL_TIME_S = 10.0
# A binary-exact step prevents an ANDES 2.0.0 end-time roundoff failure that
# occurs with 0.01 s after the solver has otherwise reached 10 s.
TIME_STEP_S = 0.03125
FREQUENCY_DRIFT_LIMIT_HZ = 0.005
VOLTAGE_DRIFT_LIMIT_PU = 1e-3


def sha256(path: Path) -> str:
    """Return the SHA-256 digest of *path*."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def git_commit() -> str:
    """Return the current commit without changing repository state."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def prepare_case() -> tuple[str, str]:
    """Preserve the package case and build the minimal E0 instrumentation."""
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    source_hash = sha256(SOURCE_CASE)

    if BASE_CASE.exists() and sha256(BASE_CASE) != source_hash:
        raise RuntimeError(
            f"Existing base case does not match the ANDES source: {BASE_CASE}"
        )
    if not BASE_CASE.exists():
        shutil.copy2(SOURCE_CASE, BASE_CASE)

    if E0_CASE.exists():
        workbook = load_workbook(E0_CASE, read_only=True, data_only=True)
        bus_freq = workbook["BusFreq"]
        headers = [cell.value for cell in bus_freq[1]]
        buses = sorted(
            int(row[headers.index("bus")])
            for row in bus_freq.iter_rows(min_row=2, values_only=True)
        )
        if buses != list(range(1, 40)):
            raise RuntimeError("Existing E0 case does not monitor buses 1--39 once.")
        if workbook["ACEc"].max_row != 1 or workbook["Toggler"].max_row != 1:
            raise RuntimeError("Existing E0 case contains ACEc or Toggler devices.")
        workbook.close()
        return source_hash, sha256(E0_CASE)

    shutil.copy2(BASE_CASE, E0_CASE)
    workbook = load_workbook(E0_CASE)

    for sheet_name in ("ACEc", "Toggler"):
        sheet = workbook[sheet_name]
        if sheet.max_row > 1:
            sheet.delete_rows(2, sheet.max_row - 1)

    bus_freq = workbook["BusFreq"]
    headers = [cell.value for cell in bus_freq[1]]
    rows = list(bus_freq.iter_rows(min_row=2, values_only=True))
    monitored_buses = {int(row[headers.index("bus")]) for row in rows}
    used_indices = {str(row[headers.index("idx")]) for row in rows}
    next_uid = max(int(row[headers.index("uid")]) for row in rows) + 1

    for bus in range(1, 40):
        if bus in monitored_buses:
            continue
        idx = f"BusFreq_E0_{bus}"
        if idx in used_indices:
            raise RuntimeError(f"Duplicate BusFreq index: {idx}")
        values = {
            "uid": next_uid,
            "idx": idx,
            "u": 1,
            "name": idx,
            "bus": bus,
            "Tf": 0.02,
            "Tw": 0.02,
            "fn": NOMINAL_FREQUENCY_HZ,
        }
        bus_freq.append([values[name] for name in headers])
        next_uid += 1

    workbook.save(E0_CASE)
    return source_hash, sha256(E0_CASE)


def extract_time_series(system: Any) -> dict[str, np.ndarray]:
    """Extract bus voltage/frequency and SG speed from ANDES arrays."""
    time_s = np.asarray(system.dae.ts.t, dtype=float)
    bus_voltage_pu = np.asarray(
        system.dae.ts.y[:, np.asarray(system.Bus.v.a, dtype=int)], dtype=float
    )
    bus_frequency_pu = np.asarray(
        system.dae.ts.y[:, np.asarray(system.BusFreq.f.a, dtype=int)], dtype=float
    )
    sg_frequency_pu = np.asarray(
        system.dae.ts.x[:, np.asarray(system.GENROU.omega.a, dtype=int)], dtype=float
    )

    bus_ids = np.asarray(system.Bus.idx.v, dtype=int)
    bus_voltage_min_pu = np.asarray(system.Bus.vmin.v, dtype=float)
    bus_voltage_max_pu = np.asarray(system.Bus.vmax.v, dtype=float)
    frequency_bus_ids = np.asarray(system.BusFreq.bus.v, dtype=int)
    sg_bus_ids = np.asarray(system.GENROU.bus.v, dtype=int)

    order = np.argsort(frequency_bus_ids)
    if not np.array_equal(frequency_bus_ids[order], np.arange(1, 40)):
        raise RuntimeError("BusFreq instrumentation does not cover buses 1--39 once.")

    return {
        "time_s": time_s,
        "bus_ids": bus_ids,
        "bus_voltage_min_pu": bus_voltage_min_pu,
        "bus_voltage_max_pu": bus_voltage_max_pu,
        "frequency_bus_ids": frequency_bus_ids[order],
        "sg_bus_ids": sg_bus_ids,
        "bus_voltage_pu": bus_voltage_pu,
        "bus_frequency_hz": bus_frequency_pu[:, order] * NOMINAL_FREQUENCY_HZ,
        "sg_frequency_hz": sg_frequency_pu * NOMINAL_FREQUENCY_HZ,
    }


def plot_frequency(data: dict[str, np.ndarray]) -> None:
    """Generate the mandatory E0 frequency figure."""
    time_s = data["time_s"]
    bus_ids = data["frequency_bus_ids"]
    frequency_hz = data["bus_frequency_hz"]
    sg_frequency_hz = data["sg_frequency_hz"]
    sg_bus_ids = data["sg_bus_ids"]

    fig, axes = plt.subplots(3, 1, figsize=(9.0, 9.0), sharex=True)
    critical_mask = np.isin(bus_ids, CRITICAL_BUSES)
    for column in np.flatnonzero(critical_mask):
        axes[0].plot(time_s, frequency_hz[:, column], label=f"Bus {bus_ids[column]}")
    axes[0].axhline(NOMINAL_FREQUENCY_HZ, color="black", lw=1, ls="--")
    axes[0].set_ylabel("Frequency [Hz]")
    axes[0].set_title("E0--C0: critical-bus frequency")
    axes[0].legend(ncol=4, fontsize=8)

    remaining = frequency_hz[:, ~critical_mask]
    axes[1].plot(time_s, remaining, color="0.72", lw=0.7, alpha=0.65)
    axes[1].plot(time_s, frequency_hz.min(axis=1), color="tab:blue", label="Minimum")
    axes[1].plot(time_s, frequency_hz.max(axis=1), color="tab:red", label="Maximum")
    axes[1].axhline(NOMINAL_FREQUENCY_HZ, color="black", lw=1, ls="--")
    axes[1].set_ylabel("Frequency [Hz]")
    axes[1].set_title("Remaining buses and system envelope")
    axes[1].legend(fontsize=8)

    for column, bus in enumerate(sg_bus_ids):
        axes[2].plot(time_s, sg_frequency_hz[:, column], label=f"SG bus {bus}")
    axes[2].axhline(NOMINAL_FREQUENCY_HZ, color="black", lw=1, ls="--")
    axes[2].set_xlabel("Time [s]")
    axes[2].set_ylabel("Frequency [Hz]")
    axes[2].set_title("Synchronous-generator rotor frequency")
    axes[2].legend(ncol=5, fontsize=7)

    for axis in axes:
        axis.set_ylim(NOMINAL_FREQUENCY_HZ - 0.01, NOMINAL_FREQUENCY_HZ + 0.01)
        axis.ticklabel_format(axis="y", style="plain", useOffset=False)
        axis.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(FREQUENCY_FIGURE, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_voltage(data: dict[str, np.ndarray]) -> None:
    """Generate the mandatory E0 voltage figure."""
    time_s = data["time_s"]
    bus_ids = data["bus_ids"]
    voltage_pu = data["bus_voltage_pu"]
    critical_mask = np.isin(bus_ids, CRITICAL_BUSES)

    voltage_min_pu = data["bus_voltage_min_pu"]
    voltage_max_pu = data["bus_voltage_max_pu"]

    fig, axes = plt.subplots(3, 1, figsize=(9.0, 9.0), sharex=True)
    for column in np.flatnonzero(critical_mask):
        axes[0].plot(time_s, voltage_pu[:, column], label=f"Bus {bus_ids[column]}")
    axes[0].set_ylabel("Voltage |V| [pu]")
    axes[0].set_title("E0--C0: critical-bus voltage magnitude")
    axes[0].legend(ncol=4, fontsize=8)

    remaining = voltage_pu[:, ~critical_mask]
    axes[1].plot(time_s, remaining, color="0.72", lw=0.7, alpha=0.65)
    axes[1].plot(time_s, voltage_pu.min(axis=1), color="tab:blue", label="Minimum")
    axes[1].plot(time_s, voltage_pu.max(axis=1), color="tab:red", label="Maximum")
    axes[1].set_xlabel("Time [s]")
    axes[1].set_ylabel("Voltage |V| [pu]")
    axes[1].set_title("All buses and system envelope")
    axes[1].legend(fontsize=8)

    axes[2].plot(time_s, voltage_pu.min(axis=1), color="tab:blue", label="Minimum")
    axes[2].plot(time_s, voltage_pu.max(axis=1), color="tab:red", label="Maximum")
    axes[2].axhline(
        float(np.min(voltage_min_pu)), color="black", lw=1, ls="--", label="Case limits"
    )
    axes[2].axhline(float(np.max(voltage_max_pu)), color="black", lw=1, ls="--")
    axes[2].fill_between(
        time_s,
        float(np.min(voltage_min_pu)),
        float(np.max(voltage_max_pu)),
        color="tab:green",
        alpha=0.06,
    )
    axes[2].set_xlabel("Time [s]")
    axes[2].set_ylabel("Voltage |V| [pu]")
    axes[2].set_title("System envelope and voltage limits from the case")
    axes[2].set_ylim(
        float(np.min(voltage_min_pu)) - 0.01,
        float(np.max(voltage_max_pu)) + 0.01,
    )
    axes[2].legend(fontsize=8)

    for axis in axes:
        axis.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(VOLTAGE_FIGURE, dpi=300, bbox_inches="tight")
    plt.close(fig)


def update_experiment_matrix(summary: dict[str, Any]) -> None:
    """Create or update the single experiment ledger row for E0."""
    fields = [
        "run_id", "stage", "case", "scenario", "baseline", "source_sha256",
        "variant_sha256", "andes_version", "git_commit", "seed",
        "simulation_t0", "simulation_tf", "solver_settings", "event_time",
        "event_bus", "event_P_MW", "event_Q_MVAr", "fn_Hz", "bus_freq_set",
        "bus_volt_set", "f_nadir_Hz", "max_RoCoF_Hz_s", "min_V_pu",
        "max_V_pu", "min_h", "qp_infeasible_count", "dae_residual",
        "status_auto", "status_human", "frequency_figure", "voltage_figure",
        "raw_file", "decision_note",
    ]
    row = {key: "" for key in fields}
    row.update(
        {
            "run_id": summary["run_id"],
            "stage": "E0",
            "case": "C0_10SG",
            "scenario": "flat_no_disturbance",
            "baseline": "ANDES_ieee39_full",
            "source_sha256": summary["source_sha256"],
            "variant_sha256": summary["variant_sha256"],
            "andes_version": summary["andes_version"],
            "git_commit": summary["git_commit"],
            "seed": "not_applicable_deterministic",
            "simulation_t0": 0.0,
            "simulation_tf": FINAL_TIME_S,
            "solver_settings": json.dumps(summary["solver"], sort_keys=True),
            "fn_Hz": NOMINAL_FREQUENCY_HZ,
            "bus_freq_set": "1-39",
            "bus_volt_set": "1-39",
            "f_nadir_Hz": summary["metrics"]["minimum_bus_frequency_hz"],
            "min_V_pu": summary["metrics"]["minimum_bus_voltage_pu"],
            "max_V_pu": summary["metrics"]["maximum_bus_voltage_pu"],
            "dae_residual": summary["metrics"]["final_max_abs_algebraic_residual"],
            "status_auto": summary["status_auto"],
            "status_human": "PENDING",
            "frequency_figure": FREQUENCY_FIGURE.relative_to(PROJECT_ROOT).as_posix(),
            "voltage_figure": VOLTAGE_FIGURE.relative_to(PROJECT_ROOT).as_posix(),
            "raw_file": RAW_FILE.relative_to(PROJECT_ROOT).as_posix(),
            "decision_note": "E1 is not authorized until human review of both figures.",
        }
    )
    existing_rows: list[dict[str, str]] = []
    if MATRIX_FILE.exists():
        with MATRIX_FILE.open("r", newline="", encoding="utf-8") as stream:
            existing_rows = [
                existing for existing in csv.DictReader(stream)
                if existing.get("stage") != "E0"
            ]
    with MATRIX_FILE.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerow(row)
        writer.writerows(existing_rows)


def main() -> int:
    """Execute E0 and return nonzero when the automatic gate fails."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    source_hash, variant_hash = prepare_case()

    system = andes.load(str(E0_CASE), default_config=True, no_output=True)
    counts = {
        "Bus": system.Bus.n,
        "GENROU": system.GENROU.n,
        "TGOV1N": system.TGOV1N.n,
        "IEEEX1": system.IEEEX1.n,
        "IEEEST": system.IEEEST.n,
        "BusFreq": system.BusFreq.n,
        "ACEc": system.ACEc.n,
        "Toggler": system.Toggler.n,
    }
    expected_counts = {
        "Bus": 39,
        "GENROU": 10,
        "TGOV1N": 10,
        "IEEEX1": 10,
        "IEEEST": 10,
        "BusFreq": 39,
        "ACEc": 0,
        "Toggler": 0,
    }

    pflow_ok = bool(system.PFlow.run())
    pflow_residual = float(np.max(np.abs(system.dae.g)))
    system.TDS.config.tf = FINAL_TIME_S
    system.TDS.config.tstep = TIME_STEP_S
    system.TDS.config.fixt = 1
    system.TDS.config.no_tqdm = 1
    tds_ok = bool(system.TDS.run(no_summary=True)) if pflow_ok else False

    data = extract_time_series(system)
    np.savez_compressed(RAW_FILE, **data)
    plot_frequency(data)
    plot_voltage(data)

    frequency_drift_hz = float(
        np.max(np.abs(data["bus_frequency_hz"] - data["bus_frequency_hz"][0, :]))
    )
    voltage_drift_pu = float(
        np.max(np.abs(data["bus_voltage_pu"] - data["bus_voltage_pu"][0, :]))
    )
    final_residual = float(np.max(np.abs(system.dae.g)))
    reached_final_time = bool(np.isclose(data["time_s"][-1], FINAL_TIME_S))
    automatic_pass = all(
        (
            counts == expected_counts,
            pflow_ok,
            tds_ok,
            reached_final_time,
            frequency_drift_hz <= FREQUENCY_DRIFT_LIMIT_HZ,
            voltage_drift_pu <= VOLTAGE_DRIFT_LIMIT_PU,
            np.all(np.isfinite(data["bus_frequency_hz"])),
            np.all(np.isfinite(data["bus_voltage_pu"])),
        )
    )
    status_auto = "PASS_AUTO_WAIT_HUMAN" if automatic_pass else "FAIL"
    run_id = f"IEEE39_E0_C0_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

    summary: dict[str, Any] = {
        "run_id": run_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status_auto": status_auto,
        "status_human": "PENDING",
        "source_case": str(SOURCE_CASE),
        "base_case": str(BASE_CASE.relative_to(PROJECT_ROOT)),
        "instrumented_case": str(E0_CASE.relative_to(PROJECT_ROOT)),
        "source_sha256": source_hash,
        "base_sha256": sha256(BASE_CASE),
        "variant_sha256": variant_hash,
        "git_commit": git_commit(),
        "runner_sha256": sha256(Path(__file__).resolve()),
        "python_version": platform.python_version(),
        "andes_version": andes.__version__,
        "counts": counts,
        "expected_counts": expected_counts,
        "pflow_ok": pflow_ok,
        "tds_ok": tds_ok,
        "reached_final_time": reached_final_time,
        "solver": {
            "method": system.TDS.config.method,
            "t0_s": 0.0,
            "tf_s": FINAL_TIME_S,
            "time_step_s": TIME_STEP_S,
            "fixed_step": True,
            "tolerance": system.TDS.config.tol,
            "maximum_iterations": system.TDS.config.max_iter,
        },
        "metrics": {
            "pflow_max_abs_algebraic_residual": pflow_residual,
            "final_max_abs_algebraic_residual": final_residual,
            "maximum_bus_frequency_drift_hz": frequency_drift_hz,
            "maximum_bus_voltage_drift_pu": voltage_drift_pu,
            "minimum_bus_frequency_hz": float(np.min(data["bus_frequency_hz"])),
            "maximum_bus_frequency_hz": float(np.max(data["bus_frequency_hz"])),
            "minimum_bus_voltage_pu": float(np.min(data["bus_voltage_pu"])),
            "maximum_bus_voltage_pu": float(np.max(data["bus_voltage_pu"])),
        },
        "thresholds": {
            "maximum_bus_frequency_drift_hz": FREQUENCY_DRIFT_LIMIT_HZ,
            "maximum_bus_voltage_drift_pu": VOLTAGE_DRIFT_LIMIT_PU,
        },
        "notes": [
            "No disturbance was applied.",
            "ACEc and Toggler rows were removed from the instrumented variant.",
            "BusFreq uses Tf=Tw=0.02 s and fn=60 Hz at buses 1--39.",
            "The 60 Hz base is verified from the effective case Line, Shunt, GENROU, and BusFreq data.",
            "No claim of nonlinear certification follows from this E0 run.",
        ],
    }
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    update_experiment_matrix(summary)
    print(json.dumps(summary, indent=2))
    return 0 if automatic_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
