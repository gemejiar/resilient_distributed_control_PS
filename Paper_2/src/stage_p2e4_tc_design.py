#!/usr/bin/env python
"""
P2-E4 -- Control-update-time (Tc) design.

Compares Tc in {100, 50, 20} ms with EVERYTHING ELSE held fixed (case,
BESS buses, Pmax, ESD1 model, tip, BusROCOF Tf/Tw/Tr, disturbance, operating
point, horizon, Kf, Kr) -- the only independent variable is Tc. Integration/
logging resolution (tstep=5ms) is fixed and IDENTICAL across every Tc, so
nadir/RoCoF are always read from the same integration-level trajectory
regardless of the control-update period (p2_common.run_physical_scenario_tc).

Experiment 1 (mandatory): conservative Kf/Kr (gain_mult=0.5, already shown
stable for BOTH design probes at Tc=100ms in DEC-P2-005) across NoFFC and
Tc=100/50/20ms, both DESIGN probes (severe generation deficit, severe load
increase).

Experiment 2 (diagnostic, only if experiment 1 is numerically robust at
50/20ms): a gain that was previously too aggressive/near the stability edge
at Tc=100ms (gain_mult=1.0, DEC-P2-005 showed this destabilizing for the load
probe: RoCoF 5.8x worse than NoFFC) across the same three Tc, to see whether
part of that instability is a control-update-rate artifact.

Does NOT retune Kf/Kr for best performance, does NOT touch Pmax, does NOT
train TD3, does NOT open P2-T1..T12. DESIGN-only probes (G_train_P2/
L_train_P2), same probes as the P2-E3 gain tanteo/refine diagnostics
(DEC-P2-005) for experimental continuity.
"""
import os
import sys
import time

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from p2_common import run_physical_scenario_tc, TD, TF_INITIAL, F0_HZ

PMAX_MW = 293.4  # alpha_P=1.0, same provisional value as P2-E3/P2-E3A/P2-E3B (Pmax NOT frozen here)
KF0 = PMAX_MW / 0.5   # 586.8 MW/Hz
KR0 = PMAX_MW / 1.0   # 293.4 MW/(Hz/s)
GAIN_CONSERVATIVE = 0.5  # DEC-P2-005: stable (no saturation, no oscillation) for BOTH probes at Tc=100ms
GAIN_AGGRESSIVE = 1.0    # DEC-P2-005: destabilizing for the load probe at Tc=100ms (RoCoF 5.8x worse)

TC_LIST_MS = [100, 50, 20]
TSTEP = 0.005  # 5 ms, fixed integration/logging resolution, IDENTICAL across every Tc and every run

SCENARIOS = [
    dict(label='gen_severe', kind='gen', gen='GENROU_4', rho=0.90, lambda_L=1.00),
    dict(label='load_severe', kind='load', bus=20, alpha_L=0.50, lambda_L=1.00),  # PQ_9, bus 20
]

OUT_DIAG = os.path.join('Paper_2', 'artifacts', 'diagnostics')
OUT_TRAJ = os.path.join('Paper_2', 'artifacts', 'trajectories')
OUT_FIG = os.path.join('Paper_2', 'artifacts', 'figures')
for d in (OUT_DIAG, OUT_TRAJ, OUT_FIG):
    os.makedirs(d, exist_ok=True)


def run_condition(scenario, tc_s, k_f, k_r, controller='physical'):
    kwargs = dict(kind=scenario['kind'], lambda_L=scenario['lambda_L'],
                  p_max_bess_mw=PMAX_MW, k_f=k_f, k_r=k_r, tc=tc_s, tstep=TSTEP,
                  controller=controller, tf=TF_INITIAL)
    if scenario['kind'] == 'gen':
        kwargs['gen'] = scenario['gen']
        kwargs['rho'] = scenario['rho']
    else:
        kwargs['bus'] = scenario['bus']
        kwargs['alpha_L'] = scenario['alpha_L']
    return run_physical_scenario_tc(**kwargs)


def controller_rate_rocof_max(r):
    """Diagnostic required by the plan (Section 7): what RoCoF_max WOULD have
    been read if sampled only at control-update instants, vs. the true
    integration-level max. A large gap flags an undersampling artifact."""
    idx = r['action_step_indices']
    if len(idx) == 0 or len(r['rocof_worst_hz_s']) == 0:
        return float('nan')
    idx = idx[idx < len(r['rocof_worst_hz_s'])]
    if len(idx) == 0:
        return float('nan')
    return float(np.max(r['rocof_worst_hz_s'][idx]))


def make_row(scenario, controller_label, gain_label, tc_ms, k_f, k_r, r):
    rocof_ctrl_rate = controller_rate_rocof_max(r)
    rocof_full = r['rocof_max_hz_s']
    undersample_gap_pct = (100.0 * (rocof_full - rocof_ctrl_rate) / rocof_full
                            if (rocof_full and not np.isnan(rocof_ctrl_rate)) else float('nan'))
    return dict(
        scenario=scenario['label'], controller=controller_label, gain_label=gain_label,
        Tc_ms=tc_ms, Kf=k_f, Kr=k_r, Pmax_MW=PMAX_MW,
        df_nadir_hz=r['df_nadir_hz'], f_nadir_hz=r['f_nadir_hz'],
        RoCoF_max_hz_s=rocof_full, RoCoF_max_controller_rate_hz_s=rocof_ctrl_rate,
        RoCoF_undersampling_gap_pct=undersample_gap_pct,
        time_to_nadir_s=r['t_nadir_s'], settling_time_s=r['settling_time_s'],
        Ppeak_MW=r['p_peak_mw'], saturation_fraction=r['saturation_fraction'],
        command_delivered_max_error_MW=r['command_delivered_max_error_mw'],
        command_delivered_rms_error_MW=r['command_delivered_rms_error_mw'],
        runtime_s=r['runtime_seconds'],
        expected_actions=r['expected_actions'], actual_actions=r['actual_actions'],
        first_action_time_s=r['first_action_time_s'], last_action_time_s=r['last_action_time_s'],
        dae_t_final=r['dae_t_final'], max_step_gap_s=r['max_step_gap_s'],
        TDS_success=bool(r['tds_success']),
    )


def print_row(row):
    tc = row['Tc_ms'] if row['Tc_ms'] is not None else '--'
    print(f"  [{row['scenario']:12s} {row['controller']:8s} {row['gain_label']:12s} Tc={tc}ms] "
          f"df_nadir={row['df_nadir_hz']:+.4f}Hz "
          f"RoCoF_max={row['RoCoF_max_hz_s']:.4f}Hz/s "
          f"(ctrl-rate={row['RoCoF_max_controller_rate_hz_s']:.4f}, gap={row['RoCoF_undersampling_gap_pct']:.1f}%) "
          f"sat={row['saturation_fraction']:.3f} Ppeak={row['Ppeak_MW']:.1f}MW "
          f"cmd_err(max/rms)={row['command_delivered_max_error_MW']:.2f}/{row['command_delivered_rms_error_MW']:.3f}MW "
          f"actions={row['actual_actions']}/{row['expected_actions']} "
          f"dae_t_final={row['dae_t_final']:.4f} runtime={row['runtime_s']:.2f}s "
          f"tds_ok={row['TDS_success']}")


def main():
    rows = []
    traces = {}

    print("=== P2-E4: NoFFC baselines (Tc-independent, DESIGN probes) ===")
    noffc_ref = {}
    for scenario in SCENARIOS:
        r = run_condition(scenario, tc_s=0.1, k_f=0.0, k_r=0.0, controller='no_ffc')
        row = make_row(scenario, 'NoFFC', 'n/a', None, 0.0, 0.0, r)
        rows.append(row)
        print_row(row)
        noffc_ref[scenario['label']] = row
        traces[f"{scenario['label']}_NoFFC"] = dict(
            t=r['t'], f_worst_hz=r['f_worst_hz'], rocof_worst_hz_s=r['rocof_worst_hz_s'],
            p_command1_mw=r['p_command1_mw'], p_command2_mw=r['p_command2_mw'],
            p_delivered1_mw=r['p_delivered1_mw'], p_delivered2_mw=r['p_delivered2_mw'])

    print("\n=== P2-E4 Experiment 1: conservative Kf/Kr (gain_mult="
          f"{GAIN_CONSERVATIVE}) across Tc={TC_LIST_MS} ===")
    print(f"Kf={GAIN_CONSERVATIVE*KF0:.1f} MW/Hz, Kr={GAIN_CONSERVATIVE*KR0:.1f} MW/(Hz/s) "
          f"-- chosen for STABILITY (DEC-P2-005: stable, no saturation, bit-identical response across "
          f"gain_mult 0.5-0.9 for the load probe), NOT for maximum known performance.")
    exp1_rows = []
    for scenario in SCENARIOS:
        for tc_ms in TC_LIST_MS:
            r = run_condition(scenario, tc_s=tc_ms / 1000.0,
                               k_f=GAIN_CONSERVATIVE * KF0, k_r=GAIN_CONSERVATIVE * KR0)
            row = make_row(scenario, 'Physical', 'conservative', tc_ms,
                            GAIN_CONSERVATIVE * KF0, GAIN_CONSERVATIVE * KR0, r)
            rows.append(row)
            exp1_rows.append(row)
            print_row(row)
            traces[f"{scenario['label']}_conservative_Tc{tc_ms}"] = dict(
                t=r['t'], f_worst_hz=r['f_worst_hz'], rocof_worst_hz_s=r['rocof_worst_hz_s'],
                p_command1_mw=r['p_command1_mw'], p_command2_mw=r['p_command2_mw'],
                p_delivered1_mw=r['p_delivered1_mw'], p_delivered2_mw=r['p_delivered2_mw'])

    exp1_robust_50_20 = all(
        r['TDS_success'] and r['saturation_fraction'] < 0.5 and
        r['RoCoF_max_hz_s'] < 3.0 * noffc_ref[r['scenario']]['RoCoF_max_hz_s']
        for r in exp1_rows if r['Tc_ms'] in (50, 20)
    )
    print(f"\nExperiment-1 robustness check (Tc=50/20ms): TDS_success + saturation<0.5 + "
          f"RoCoF_max < 3x NoFFC on all rows -> {exp1_robust_50_20}")

    if exp1_robust_50_20:
        print(f"\n=== P2-E4 Experiment 2 (diagnostic): aggressive Kf/Kr (gain_mult="
              f"{GAIN_AGGRESSIVE}) across Tc={TC_LIST_MS} ===")
        print(f"Kf={GAIN_AGGRESSIVE*KF0:.1f} MW/Hz, Kr={GAIN_AGGRESSIVE*KR0:.1f} MW/(Hz/s) "
              f"-- DEC-P2-005: destabilizing for the load probe at Tc=100ms (RoCoF 5.8x worse, "
              f"11.7% saturation). Diagnostic only: does NOT search for the best gain.")
        for scenario in SCENARIOS:
            for tc_ms in TC_LIST_MS:
                r = run_condition(scenario, tc_s=tc_ms / 1000.0,
                                   k_f=GAIN_AGGRESSIVE * KF0, k_r=GAIN_AGGRESSIVE * KR0)
                row = make_row(scenario, 'Physical', 'aggressive', tc_ms,
                                GAIN_AGGRESSIVE * KF0, GAIN_AGGRESSIVE * KR0, r)
                rows.append(row)
                print_row(row)
                traces[f"{scenario['label']}_aggressive_Tc{tc_ms}"] = dict(
                    t=r['t'], f_worst_hz=r['f_worst_hz'], rocof_worst_hz_s=r['rocof_worst_hz_s'],
                    p_command1_mw=r['p_command1_mw'], p_command2_mw=r['p_command2_mw'],
                    p_delivered1_mw=r['p_delivered1_mw'], p_delivered2_mw=r['p_delivered2_mw'])
    else:
        print("\nExperiment 2 SKIPPED: experiment 1 was not numerically robust at Tc=50/20ms.")

    df = pd.DataFrame(rows)
    for scenario in SCENARIOS:
        base_f = noffc_ref[scenario['label']]['df_nadir_hz']
        base_r = noffc_ref[scenario['label']]['RoCoF_max_hz_s']
        mask = df['scenario'] == scenario['label']
        df.loc[mask, 'I_f_vs_NoFFC'] = (np.abs(base_f) - np.abs(df.loc[mask, 'df_nadir_hz'])) / np.abs(base_f)
        df.loc[mask, 'I_r_vs_NoFFC'] = (base_r - df.loc[mask, 'RoCoF_max_hz_s']) / base_r

    out_csv = os.path.join(OUT_DIAG, 'p2e4_tc_design.csv')
    df.to_csv(out_csv, index=False)
    print(f"\nSaved: {out_csv} ({len(df)} rows)")

    flat_traces = {}
    for key, d in traces.items():
        for name, arr in d.items():
            flat_traces[f"{key}__{name}"] = arr
    out_npz = os.path.join(OUT_TRAJ, 'p2e4_tc_traces.npz')
    np.savez(out_npz, **flat_traces)
    print(f"Saved: {out_npz}")

    make_figures(df, traces, noffc_ref)


def make_figures(df, traces, noffc_ref):
    colors = {100: 'C0', 50: 'C1', 20: 'C2'}

    # Figure A: frequency trajectories, Figure B: RoCoF trajectories (conservative gain only)
    for scenario in SCENARIOS:
        label = scenario['label']
        figA, axA = plt.subplots(figsize=(6, 3.5))
        figB, axB = plt.subplots(figsize=(6, 3.5))
        tr0 = traces[f"{label}_NoFFC"]
        axA.plot(tr0['t'], tr0['f_worst_hz'], 'k:', label='NoFFC', linewidth=1.0)
        axB.plot(tr0['t'], tr0['rocof_worst_hz_s'], 'k:', label='NoFFC', linewidth=1.0)
        for tc_ms in TC_LIST_MS:
            key = f"{label}_conservative_Tc{tc_ms}"
            if key not in traces:
                continue
            tr = traces[key]
            axA.plot(tr['t'], tr['f_worst_hz'], color=colors[tc_ms], label=f'Tc={tc_ms}ms', linewidth=1.1)
            axB.plot(tr['t'], tr['rocof_worst_hz_s'], color=colors[tc_ms], label=f'Tc={tc_ms}ms', linewidth=1.1)
        for ax, ylab, title in [(axA, 'Worst-bus frequency (Hz)', f'P2-E4 Fig A: frequency, {label}'),
                                 (axB, 'Worst-bus |RoCoF| (Hz/s)', f'P2-E4 Fig B: RoCoF, {label}')]:
            ax.set_xlabel('Time (s)')
            ax.set_ylabel(ylab)
            ax.set_title(title)
            ax.legend(fontsize=7)
            ax.grid(True, linestyle=':', alpha=0.6)
        figA.tight_layout()
        figB.tight_layout()
        figA.savefig(os.path.join(OUT_FIG, f'p2e4_figA_freq_{label}.png'), dpi=200)
        figB.savefig(os.path.join(OUT_FIG, f'p2e4_figB_rocof_{label}.png'), dpi=200)
        plt.close(figA)
        plt.close(figB)

    # Figure C: Pcommand vs Pdelivered (BESS1) for the gen_severe scenario, all Tc
    figC, axes = plt.subplots(1, len(TC_LIST_MS), figsize=(4 * len(TC_LIST_MS), 3.2), sharey=True)
    for ax, tc_ms in zip(axes, TC_LIST_MS):
        key = f"gen_severe_conservative_Tc{tc_ms}"
        if key not in traces:
            continue
        tr = traces[key]
        window = (tr['t'] >= TD - 0.05) & (tr['t'] <= TD + 0.5)
        ax.plot(tr['t'][window], tr['p_command1_mw'][window], 'k--', label='P_command', linewidth=1.0)
        ax.plot(tr['t'][window], tr['p_delivered1_mw'][window], 'C0-', label='P_delivered', linewidth=1.0)
        ax.set_title(f'Tc={tc_ms}ms')
        ax.set_xlabel('Time (s)')
        ax.grid(True, linestyle=':', alpha=0.6)
    axes[0].set_ylabel('BESS1 power (MW)')
    axes[0].legend(fontsize=7)
    figC.suptitle('P2-E4 Fig C: P_command vs P_delivered (BESS1, gen_severe, conservative gains)')
    figC.tight_layout()
    figC.savefig(os.path.join(OUT_FIG, 'p2e4_figC_command_delivered.png'), dpi=200)
    plt.close(figC)

    # Figure D: summary nadir/RoCoF improvement vs Tc
    figD, (axD1, axD2) = plt.subplots(1, 2, figsize=(9, 3.5))
    for scenario in SCENARIOS:
        label = scenario['label']
        sub = df[(df['scenario'] == label) & (df['gain_label'] == 'conservative')].sort_values('Tc_ms')
        axD1.plot(sub['Tc_ms'], 100 * sub['I_f_vs_NoFFC'], marker='o', label=label)
        axD2.plot(sub['Tc_ms'], 100 * sub['I_r_vs_NoFFC'], marker='o', label=label)
    for ax, ylab, title in [(axD1, 'I_f vs NoFFC (%)', 'Nadir improvement vs Tc'),
                             (axD2, 'I_r vs NoFFC (%)', 'RoCoF improvement vs Tc')]:
        ax.set_xlabel('Tc (ms)')
        ax.set_ylabel(ylab)
        ax.set_title(title)
        ax.axhline(0, color='gray', linewidth=0.8)
        ax.invert_xaxis()
        ax.legend(fontsize=7)
        ax.grid(True, linestyle=':', alpha=0.6)
    figD.tight_layout()
    figD.savefig(os.path.join(OUT_FIG, 'p2e4_figD_summary_vs_tc.png'), dpi=200)
    plt.close(figD)

    # Figure E: runtime vs Tc
    figE, axE = plt.subplots(figsize=(5, 3.5))
    for scenario in SCENARIOS:
        label = scenario['label']
        sub = df[(df['scenario'] == label) & (df['gain_label'] == 'conservative')].sort_values('Tc_ms')
        axE.plot(sub['Tc_ms'], sub['runtime_s'], marker='o', label=label)
    axE.set_xlabel('Tc (ms)')
    axE.set_ylabel('Wall-clock runtime (s)')
    axE.set_title('P2-E4 Fig E: computational cost vs Tc')
    axE.invert_xaxis()
    axE.legend(fontsize=7)
    axE.grid(True, linestyle=':', alpha=0.6)
    figE.tight_layout()
    figE.savefig(os.path.join(OUT_FIG, 'p2e4_figE_runtime_vs_tc.png'), dpi=200)
    plt.close(figE)

    print(f"Saved figures A-E to {OUT_FIG}")


if __name__ == '__main__':
    t0 = time.perf_counter()
    main()
    print(f"\nTotal wall-clock time: {time.perf_counter() - t0:.1f}s")
