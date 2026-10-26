"""E5--C2: contrast native primary P-f and Q-V responses on the frozen C2 case.

The C2 case file is read only.  Primary control only: the SG governors/AVR/PSS
and the REGF1 droop loops are left at their case/ANDES-default values; no
secondary, tertiary, RDC, or CLF-HOCBF layer exists in the case.  The P-f
channel (+58.564 MW at bus 4) and the Q-V channel (+17.345 MVAr at bus 21)
are simulated in separate runs (1 % steps; the S1 amplitudes failed).
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

from run_e0_ieee39 import (  # noqa: E402
    ARTIFACTS_DIR, CRITICAL_BUSES, FIGURES_DIR, MATRIX_FILE,
    NOMINAL_FREQUENCY_HZ, PROJECT_ROOT, extract_time_series, git_commit, sha256,
)

from variant import CASE_FILE, CASE_LABEL, SUFFIX, VARIANT  # noqa: E402

CASE = PROJECT_ROOT / "Paper_manuscript" / "cases" / CASE_FILE
PREFIX = f"IEEE39_E5_{VARIANT}"
RAW_FILE = ARTIFACTS_DIR / f"{PREFIX}_timeseries.npz"
SUMMARY_FILE = ARTIFACTS_DIR / f"{PREFIX}_summary.json"
FREQUENCY_FIGURE = FIGURES_DIR / f"{PREFIX}_frequency.png"
VOLTAGE_FIGURE = FIGURES_DIR / f"{PREFIX}_voltage.png"
POWER_FIGURE = FIGURES_DIR / f"{PREFIX}_primary_response.png"

EVENT_TIME_S = 5.0
FINAL_TIME_S = 40.0
TIME_STEP_S = 0.00390625
REFINED_TIME_STEP_S = TIME_STEP_S / 2
SETTLING_WINDOW_S = 2.0
ROCOF_WINDOW_S = 0.5
BASE_MVA = 100.0
SCENARIOS = {
    # 1 % of total P / Q load (as in E3--E4.2).  The S1 amplitudes of +100 MW
    # and +50 MVAr did not converge on C2 (see DEC-017), so they are not used.
    "P+": {"channel": "P", "bus": 4, "amount_mw": 58.564},
    "Q+": {"channel": "Q", "bus": 21, "amount_mvar": 17.345},
}
AGC_MODELS = ("ACE", "ACEc", "AGC", "AGVC")


def configure(name: str, time_step_s: float) -> Any:
    spec = SCENARIOS[name]
    system = andes.load(str(CASE), setup=False, default_config=True, no_output=True)
    system.PQ.config.p2p, system.PQ.config.p2i, system.PQ.config.p2z = 1.0, 0.0, 0.0
    system.PQ.config.q2q, system.PQ.config.q2i, system.PQ.config.q2z = 1.0, 0.0, 0.0
    channel = spec["channel"]
    amount_pu = spec["amount_mw" if channel == "P" else "amount_mvar"] / BASE_MVA
    targets = [str(idx) for idx, bus in zip(system.PQ.idx.v, system.PQ.bus.v)
               if int(bus) == spec["bus"]]
    if len(targets) != 1:
        raise RuntimeError(f"Expected one PQ at bus {spec['bus']}; found {targets}.")
    system.add("Alter", idx=f"E5_{channel}", t=EVENT_TIME_S, model="PQ",
               dev=targets[0], src="Ppf" if channel == "P" else "Qpf",
               attr="v", method="+", amount=amount_pu)
    system.setup()
    system.TDS.config.tf = FINAL_TIME_S
    system.TDS.config.tstep = time_step_s
    system.TDS.config.fixt = 1
    system.TDS.config.no_tqdm = 1
    return system


def simulate(name: str, time_step_s: float) -> tuple[Any, dict[str, np.ndarray], dict[str, Any]]:
    system = configure(name, time_step_s)
    pflow_ok = bool(system.PFlow.run())
    pflow_residual = float(np.max(np.abs(system.dae.g)))
    tds_ok = bool(system.TDS.run(no_summary=True)) if pflow_ok else False
    data = extract_time_series(system)
    x, y = system.dae.ts.x, system.dae.ts.y
    data["sg_p_pu"] = np.asarray(y[:, system.GENROU.Pe.a], dtype=float)
    data["sg_q_pu"] = np.asarray(y[:, system.GENROU.Qe.a], dtype=float)
    data["sg_tm_pu"] = np.asarray(y[:, system.GENROU.tm.a], dtype=float)
    data["sg_governor_pout_pu"] = np.asarray(y[:, system.TGOV1N.pout.a], dtype=float)
    data["gfm_bus_ids"] = np.asarray(system.REGF1.bus.v, dtype=int)
    data["gfm_p_pu"] = np.asarray(y[:, system.REGF1.Pe.a], dtype=float)
    data["gfm_q_pu"] = np.asarray(y[:, system.REGF1.Qe.a], dtype=float)
    data["gfm_v_pu"] = np.asarray(y[:, system.REGF1.v.a], dtype=float)
    return system, data, {
        "pflow_ok": pflow_ok, "tds_ok": tds_ok, "pflow_residual": pflow_residual,
        "final_residual": float(np.max(np.abs(system.dae.g))),
    }


def window_mean(t: np.ndarray, values: np.ndarray, start: float, stop: float) -> np.ndarray:
    mask = (t >= start) & (t < stop)
    return np.mean(values[mask], axis=0)


def metrics(system: Any, data: dict[str, np.ndarray], name: str) -> dict[str, Any]:
    t = data["time_s"]
    pre = (EVENT_TIME_S - SETTLING_WINDOW_S, EVENT_TIME_S)
    post = (t[-1] - SETTLING_WINDOW_S, t[-1] + 1e-9)
    f, v = data["bus_frequency_hz"], data["bus_voltage_pu"]
    f_mean = f.mean(axis=1)
    h_weight = np.asarray(system.GENROU.M.v * system.GENROU.Sn.v, dtype=float)
    f_coi = (data["sg_frequency_hz"] * h_weight).sum(axis=1) / h_weight.sum()
    after = t >= EVENT_TIME_S
    # RoCoF: least-squares slope of the SG-COI frequency over a sliding window.
    step = t[1] - t[0]
    n_win = int(round(ROCOF_WINDOW_S / step))
    idx = np.flatnonzero(after)
    slopes = [np.polyfit(t[i:i + n_win], f_coi[i:i + n_win], 1)[0]
              for i in idx[: len(idx) - n_win : max(1, n_win // 10)]]
    d_f_hz = float(window_mean(t, f_mean, *post) - window_mean(t, f_mean, *pre))
    d_f_pu = d_f_hz / NOMINAL_FREQUENCY_HZ

    sg_sn = np.asarray(system.GENROU.Sn.v, dtype=float)
    sg_r = np.asarray(system.TGOV1N.R.v, dtype=float)  # system-base droop
    gfm_sn = np.asarray(system.REGF1.Sn.v, dtype=float)
    d_sg_p = window_mean(t, data["sg_p_pu"], *post) - window_mean(t, data["sg_p_pu"], *pre)
    d_gfm_p = window_mean(t, data["gfm_p_pu"], *post) - window_mean(t, data["gfm_p_pu"], *pre)
    d_sg_q = window_mean(t, data["sg_q_pu"], *post) - window_mean(t, data["sg_q_pu"], *pre)
    d_gfm_q = window_mean(t, data["gfm_q_pu"], *post) - window_mean(t, data["gfm_q_pu"], *pre)
    d_gfm_v = window_mean(t, data["gfm_v_pu"], *post) - window_mean(t, data["gfm_v_pu"], *pre)
    gfm_bus_col = [list(data["bus_ids"]).index(b) for b in data["gfm_bus_ids"]]
    d_bus_v = window_mean(t, v, *post) - window_mean(t, v, *pre)

    # Effective P-f droop per unit, delivered power in system pu.  Nominal SG
    # droop is TGOV1N.R (already on system base); nominal GFM droop wdrp is
    # reported on Sn base and converted for comparison.
    gfm_wdrp_sys = np.asarray(system.REGF1.wdrp.v, dtype=float) * BASE_MVA / gfm_sn
    with np.errstate(divide="ignore", invalid="ignore"):
        sg_r_eff = -d_f_pu / d_sg_p
        gfm_r_eff = -d_f_pu / d_gfm_p
    settled = np.flatnonzero(np.abs(f_mean[after] - window_mean(t, f_mean, *post)) > 0.002)
    settling = float(t[after][settled[-1]] - EVENT_TIME_S) if settled.size else 0.0

    gfm_p_max = np.asarray(system.REGF1.Pmax.v, dtype=float)
    gfm_q_max = np.asarray(system.REGF1.Qmax.v, dtype=float)
    sg_governor_max = np.asarray(system.TGOV1N.VMAX.v, dtype=float)
    return {
        "frequency_nadir_hz": float(f_mean.min()),
        "frequency_zenith_hz": float(f_mean.max()),
        "bus_frequency_min_hz": float(f.min()), "bus_frequency_max_hz": float(f.max()),
        "max_abs_rocof_coi_hz_per_s": float(np.max(np.abs(slopes))) if slopes else 0.0,
        "steady_state_delta_f_hz": d_f_hz,
        "settling_time_2mHz_s": settling,
        "voltage_min_pu": float(v.min()), "voltage_max_pu": float(v.max()),
        "delta_voltage_gfm_buses_pu": d_bus_v[gfm_bus_col].tolist(),
        "delta_voltage_event_bus_pu": float(d_bus_v[list(data["bus_ids"]).index(SCENARIOS[name]["bus"])]),
        "sg_bus_ids": data["sg_bus_ids"].tolist(),
        "delta_sg_p_pu": d_sg_p.tolist(), "delta_gfm_p_pu": d_gfm_p.tolist(),
        "delta_sg_q_pu": d_sg_q.tolist(), "delta_gfm_q_pu": d_gfm_q.tolist(),
        "delta_gfm_terminal_v_pu": d_gfm_v.tolist(),
        "total_delta_generation_p_pu": float(d_sg_p.sum() + d_gfm_p.sum()),
        "total_delta_generation_q_pu": float(d_sg_q.sum() + d_gfm_q.sum()),
        "gfm_share_of_delta_p": float(d_gfm_p.sum() / (d_sg_p.sum() + d_gfm_p.sum())),
        "effective_droop_sg_sysbase": sg_r_eff.tolist(),
        "nominal_droop_sg_sysbase": sg_r.tolist(),
        "effective_droop_gfm_sysbase": gfm_r_eff.tolist(),
        "nominal_droop_gfm_sysbase_from_wdrp": gfm_wdrp_sys.tolist(),
        "nominal_wdrp_gfm_raw": np.asarray(system.REGF1.wdrp.v).tolist(),
        "nominal_qdrp_gfm_raw": np.asarray(system.REGF1.Qdrp.v).tolist(),
        "gfm_sn_mva": gfm_sn.tolist(), "sg_sn_mva": sg_sn.tolist(),
        "gfm_max_p_pu": data["gfm_p_pu"].max(axis=0).tolist(),
        "gfm_max_abs_q_pu": np.abs(data["gfm_q_pu"]).max(axis=0).tolist(),
        "gfm_p_limit_pu": gfm_p_max.tolist(), "gfm_q_limit_pu": gfm_q_max.tolist(),
        "sg_governor_pout_max_pu": data["sg_governor_pout_pu"].max(axis=0).tolist(),
        "sg_governor_vmax_pu": sg_governor_max.tolist(),
        "gfm_limit_reached": bool(np.any(data["gfm_p_pu"].max(axis=0) >= gfm_p_max - 1e-6)
                                   or np.any(np.abs(data["gfm_q_pu"]).max(axis=0) >= gfm_q_max - 1e-6)),
        "governor_limit_reached": bool(np.any(
            data["sg_governor_pout_pu"].max(axis=0) >= sg_governor_max - 1e-6)),
    }


def plot_frequency(all_data: dict[str, dict[str, np.ndarray]]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharex=True)
    for axis, (name, data) in zip(axes, all_data.items()):
        ids, f = data["frequency_bus_ids"], data["bus_frequency_hz"]
        axis.fill_between(data["time_s"], f.min(1), f.max(1), color="0.85", label="39-bus envelope")
        for col in np.flatnonzero(np.isin(ids, CRITICAL_BUSES)):
            axis.plot(data["time_s"], f[:, col], lw=.8, label=f"Bus {ids[col]}")
        axis.axhline(60, color="black", ls=":", lw=.8)
        axis.axvline(EVENT_TIME_S, color="tab:red", ls=":", lw=.8)
        axis.set_title(f"{name}: " + ("+58.564 MW, bus 4" if name == "P+" else "+17.345 MVAr, bus 21"))
        axis.set_xlabel("Time [s]"); axis.grid(alpha=.25)
        axis.ticklabel_format(axis="y", style="plain", useOffset=False)
    axes[0].set_ylabel("Frequency [Hz]"); axes[0].legend(ncol=3, fontsize=6)
    fig.suptitle(f"E5--{VARIANT}: filtered bus frequency, primary control only")
    fig.tight_layout(); fig.savefig(FREQUENCY_FIGURE, dpi=300, bbox_inches="tight"); plt.close(fig)


def plot_voltage(all_data: dict[str, dict[str, np.ndarray]]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharex=True)
    for axis, (name, data) in zip(axes, all_data.items()):
        ids, v = data["bus_ids"], data["bus_voltage_pu"]
        axis.fill_between(data["time_s"], v.min(1), v.max(1), color="0.85", label="39-bus envelope")
        for col in np.flatnonzero(np.isin(ids, CRITICAL_BUSES)):
            axis.plot(data["time_s"], v[:, col], lw=.8, label=f"Bus {ids[col]}")
        axis.axvline(EVENT_TIME_S, color="tab:red", ls=":", lw=.8)
        axis.set_title(name); axis.set_xlabel("Time [s]"); axis.grid(alpha=.25)
    axes[0].set_ylabel("Voltage |V| [pu]"); axes[0].legend(ncol=4, fontsize=6)
    fig.suptitle(f"E5--{VARIANT}: bus-voltage response, primary control only")
    fig.tight_layout(); fig.savefig(VOLTAGE_FIGURE, dpi=300, bbox_inches="tight"); plt.close(fig)


def plot_primary(all_data: dict[str, dict[str, np.ndarray]]) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), sharex=True)
    for col, (name, data) in enumerate(all_data.items()):
        t = data["time_s"]; pre = t < EVENT_TIME_S
        for row, (sg_key, gfm_key, label) in enumerate(
                (("sg_p_pu", "gfm_p_p_pu", "P"), ("sg_q_pu", "gfm_q_pu", "Q"))):
            axis = axes[row, col]
            sg = data[sg_key]; gfm = data["gfm_p_pu" if label == "P" else "gfm_q_pu"]
            for i, bus in enumerate(data["sg_bus_ids"]):
                axis.plot(t, sg[:, i] - sg[pre, i].mean(), lw=.9, label=f"SG{bus}")
            for i, bus in enumerate(data["gfm_bus_ids"]):
                axis.plot(t, gfm[:, i] - gfm[pre, i].mean(), "--", lw=1.2, label=f"GFM{bus}")
            axis.axvline(EVENT_TIME_S, color="tab:red", ls=":", lw=.8); axis.grid(alpha=.25)
            axis.set_ylabel(f"Delta {label} delivered [pu, 100 MVA]")
            axis.set_title(f"{name}: delivered {label} change")
    axes[0, 0].legend(ncol=2, fontsize=6)
    for axis in axes[-1]: axis.set_xlabel("Time [s]")
    fig.suptitle(f"E5--{VARIANT}: SG and GFM delivered power change")
    fig.tight_layout(); fig.savefig(POWER_FIGURE, dpi=300, bbox_inches="tight"); plt.close(fig)


def update_matrix(summary: dict[str, Any]) -> None:
    with MATRIX_FILE.open("r", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream); fields = list(reader.fieldnames or [])
        rows = [row for row in reader if row.get("stage") != f"E5{SUFFIX}"]
    row = {key: "" for key in fields}
    p, q = summary["metrics"]["P+"], summary["metrics"]["Q+"]
    row.update({
        "run_id": summary["run_id"], "stage": f"E5{SUFFIX}", "case": CASE_LABEL,
        "scenario": "S1alt_1pct_primary_P-f_and_Q-V_separate", "baseline": "B0_primary_only",
        "source_sha256": summary["case_sha256"], "variant_sha256": summary["case_sha256"],
        "andes_version": summary["andes_version"], "git_commit": summary["git_commit"],
        "seed": "not_applicable_deterministic", "simulation_t0": 0.0,
        "simulation_tf": FINAL_TIME_S, "solver_settings": json.dumps(summary["solver"], sort_keys=True),
        "event_time": EVENT_TIME_S, "event_bus": "4(P);21(Q)", "event_P_MW": SCENARIOS["P+"]["amount_mw"],
        "event_Q_MVAr": SCENARIOS["Q+"]["amount_mvar"], "fn_Hz": NOMINAL_FREQUENCY_HZ,
        "bus_freq_set": "1-39", "bus_volt_set": "1-39",
        "f_nadir_Hz": p["frequency_nadir_hz"], "max_RoCoF_Hz_s": p["max_abs_rocof_coi_hz_per_s"],
        "min_V_pu": min(p["voltage_min_pu"], q["voltage_min_pu"]),
        "max_V_pu": max(p["voltage_max_pu"], q["voltage_max_pu"]),
        "dae_residual": max(d["final_residual"] for d in summary["diagnostics"].values()),
        "status_auto": summary["status_auto"], "status_human": "PENDING",
        "frequency_figure": FREQUENCY_FIGURE.relative_to(PROJECT_ROOT).as_posix(),
        "voltage_figure": VOLTAGE_FIGURE.relative_to(PROJECT_ROOT).as_posix(),
        "raw_file": RAW_FILE.relative_to(PROJECT_ROOT).as_posix(),
        "decision_note": "E6 remains blocked pending human approval of E5 figures.",
    })
    with MATRIX_FILE.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(rows + [row])


def main() -> int:
    data_by_name: dict[str, dict[str, np.ndarray]] = {}
    diagnostics: dict[str, Any] = {}
    metric_values: dict[str, Any] = {}
    structure: dict[str, Any] = {}
    for name in SCENARIOS:
        system, data, diag = simulate(name, TIME_STEP_S)
        data_by_name[name], diagnostics[name] = data, diag
        metric_values[name] = metrics(system, data, name)
        structure[name] = {
            "sg_count": len(system.GENROU.idx.v), "gfm_count": len(system.REGF1.idx.v),
            "agc_models_in_case": {m: int(getattr(system, m).n) for m in AGC_MODELS if hasattr(system, m)},
        }
    refined: dict[str, Any] = {}
    for name in SCENARIOS:
        system, data, diag = simulate(name, REFINED_TIME_STEP_S)
        refined[name] = {"diagnostics": diag, "metrics": metrics(system, data, name)}
    numerical = {
        name: {
            "frequency_nadir_abs_difference_hz": abs(metric_values[name]["frequency_nadir_hz"] - refined[name]["metrics"]["frequency_nadir_hz"]),
            "voltage_min_abs_difference_pu": abs(metric_values[name]["voltage_min_pu"] - refined[name]["metrics"]["voltage_min_pu"]),
        } for name in SCENARIOS
    }
    p, q = metric_values["P+"], metric_values["Q+"]
    event_p_pu = SCENARIOS["P+"]["amount_mw"] / BASE_MVA
    checks = {
        "all_runs_converged": all(d["pflow_ok"] and d["tds_ok"] and d["final_residual"] <= 1e-5
                                  for d in diagnostics.values()),
        "structure_6sg_4gfm_no_agc": all(s["sg_count"] == 6 and s["gfm_count"] == 4
                                         and not any(s["agc_models_in_case"].values())
                                         for s in structure.values()),
        "P_event_frequency_drops": p["steady_state_delta_f_hz"] < 0 and p["frequency_nadir_hz"] < NOMINAL_FREQUENCY_HZ,
        "P_event_all_units_increase_P": all(x > 0 for x in p["delta_sg_p_pu"] + p["delta_gfm_p_pu"]),
        "P_balance_within_10pct_of_event": abs(p["total_delta_generation_p_pu"] - event_p_pu) <= 0.10 * event_p_pu,
        "Q_event_local_voltage_drops": q["delta_voltage_event_bus_pu"] < 0,
        "Q_event_gfm_Q_responds": all(x > 0 for x in q["delta_gfm_q_pu"]),
        "no_unreported_saturation": not any(m["gfm_limit_reached"] or m["governor_limit_reached"]
                                            for m in metric_values.values()),
        "numerical_convergence": all(v["frequency_nadir_abs_difference_hz"] <= .002
                                     and v["voltage_min_abs_difference_pu"] <= .005
                                     for v in numerical.values()),
    }
    status = "PASS_AUTO_WAIT_HUMAN" if all(checks.values()) else "FAIL"
    raw = {f"{n}_{k}": v for n, d in data_by_name.items() for k, v in d.items()}
    np.savez_compressed(RAW_FILE, **raw)
    plot_frequency(data_by_name); plot_voltage(data_by_name); plot_primary(data_by_name)
    summary = {
        "run_id": f"{PREFIX}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "created_utc": datetime.now(timezone.utc).isoformat(), "status_auto": status,
        "status_human": "PENDING", "case": str(CASE.relative_to(PROJECT_ROOT)),
        "case_sha256": sha256(CASE), "runner_sha256": sha256(Path(__file__).resolve()),
        "git_commit": git_commit(), "python_version": platform.python_version(),
        "andes_version": andes.__version__,
        "events": {"P+": "+58.564 MW at bus 4 (450 MW base load)", "Q+": "+17.345 MVAr at bus 21 (115 MVAr base load)"},
        "solver": {"method": system.TDS.config.method, "tf_s": FINAL_TIME_S,
                   "time_step_s": TIME_STEP_S, "refined_time_step_s": REFINED_TIME_STEP_S,
                   "tolerance": system.TDS.config.tol, "maximum_iterations": system.TDS.config.max_iter},
        "structure": structure, "diagnostics": diagnostics, "metrics": metric_values,
        "refined": refined, "numerical_step_comparison": numerical, "checks": checks,
        "limitations": [
            "Diagnostic contrast of native primary control with ANDES default REGF1 parameters; no tuning was performed.",
            "Steady state is taken as the mean of the last 2 s of a 40 s run; slow governor/AVR tails may remain.",
            "RoCoF is the least-squares slope of the H*Sn-weighted SG-COI frequency over 0.5 s windows; it is not the control filter output.",
            "Effective droop is delivered power versus mean bus frequency change and includes network losses and load-voltage dependence (PQ configured as constant power).",
            "REGF1 has no energy/SoC model; the P limits are model limits, not an energy adequacy proof.",
            "EIG for C2 was recorded in E4.2; this stage does not change the model."],
    }
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    update_matrix(summary)
    print(json.dumps({"status_auto": status, "checks": checks, "numerical": numerical}, indent=2))
    for name, m in metric_values.items():
        print(name, json.dumps({k: m[k] for k in (
            "frequency_nadir_hz", "steady_state_delta_f_hz", "max_abs_rocof_coi_hz_per_s",
            "settling_time_2mHz_s", "voltage_min_pu", "delta_voltage_event_bus_pu",
            "total_delta_generation_p_pu", "total_delta_generation_q_pu", "gfm_share_of_delta_p",
            "delta_gfm_p_pu", "delta_gfm_q_pu", "effective_droop_gfm_sysbase",
            "nominal_droop_gfm_sysbase_from_wdrp", "effective_droop_sg_sysbase",
            "nominal_droop_sg_sysbase", "delta_gfm_terminal_v_pu",
            "gfm_limit_reached", "governor_limit_reached")}, indent=1))
    return 0 if status != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
