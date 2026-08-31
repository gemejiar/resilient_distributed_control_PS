#!/usr/bin/env python
"""
P2-E5 -- physical-controller structure diagnostic: independent Kf/Kr sweeps.

Answers: which feedback channel (frequency-deviation Kf, RoCoF Kr, or their
interaction) causes the limit-cycle instability found in P2-E4 (DEC-P2-009/
DEC-P2-010), and which channel actually contributes real nadir/RoCoF
improvement? Kf and Kr are swept ONE AT A TIME (the other held at exactly
zero) -- no single gain_mult scalar applied to both.

Tc=100ms is used as a DIAGNOSTIC REFERENCE ONLY (the only value that was
numerically stable in BOTH P2-E4 DESIGN probes with the conservative gain --
see DEC-P2-009/010). This does NOT freeze Tc.

Pmax, tip, BusROCOF (Tf/Tw/Tr), BESS location, and Tc itself are all held
fixed -- reuses p2_common.run_physical_scenario_tc() unchanged. Reuses the
STABLE/MARGINAL/LIMIT_CYCLE/NUMERICAL_FAILURE classification and thresholds
from stage_p2e4b_tc_local_sweep.py unchanged (same criteria as P2-E4).

Same two DESIGN probes as P2-E3/E4 (gen_severe, load_severe). No validation,
no P2-T*, no new scenarios chosen after seeing results.
"""
import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from p2_common import run_physical_scenario_tc, TD, TF_INITIAL, F0_HZ
from stage_p2e4b_tc_local_sweep import (
    classify, sign_reversals, periodicity_estimate, controller_rate_rocof_max,
    FINAL_WINDOW_START_S, STABLE_FREQ_P2P_MAX_HZ, STABLE_SIGN_REV_MAX, STABLE_SAT_FRAC_MAX,
    LIMIT_CYCLE_FREQ_P2P_MIN_HZ, LIMIT_CYCLE_SIGN_REV_MIN,
)

PMAX_MW = 293.4  # UNCHANGED from P2-E3/E4 -- no Pmax sweep in this stage
KF0 = PMAX_MW / 0.5
KR0 = PMAX_MW / 1.0
TC_REF_S = 0.100  # diagnostic reference ONLY (DEC-P2-009/010: only value stable in BOTH probes) -- NOT frozen
TC_P2E5_DIAGNOSTIC_REFERENCE_ONLY = True
TSTEP = 0.005  # unchanged from P2-E4

KF_MULTS = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.75, 1.00]
KR_MULTS = [0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.75, 1.00]
WIN_THRESHOLD = 0.10  # P2 plan Section 21 WIN criterion, reused here as "material improvement"
MAX_FR_GRID = 16

SCENARIOS = [
    dict(label='gen_severe', kind='gen', gen='GENROU_4', rho=0.90, lambda_L=1.00),
    dict(label='load_severe', kind='load', bus=20, alpha_L=0.50, lambda_L=1.00),
]

OUT_DIAG = os.path.join('Paper_2', 'artifacts', 'diagnostics')
OUT_TRAJ = os.path.join('Paper_2', 'artifacts', 'trajectories')
OUT_FIG = os.path.join('Paper_2', 'artifacts', 'figures')
for d in (OUT_DIAG, OUT_TRAJ, OUT_FIG):
    os.makedirs(d, exist_ok=True)


def run_condition(scenario, k_f, k_r, controller='physical'):
    kwargs = dict(kind=scenario['kind'], lambda_L=scenario['lambda_L'],
                  p_max_bess_mw=PMAX_MW, k_f=k_f, k_r=k_r, tc=TC_REF_S, tstep=TSTEP,
                  controller=controller, tf=TF_INITIAL)
    if scenario['kind'] == 'gen':
        kwargs['gen'] = scenario['gen']
        kwargs['rho'] = scenario['rho']
    else:
        kwargs['bus'] = scenario['bus']
        kwargs['alpha_L'] = scenario['alpha_L']
    return run_physical_scenario_tc(**kwargs)


def analyze_run(scenario, condition_label, k_f, k_r, r):
    t = r['t']; f = r['f_worst_hz']; rocof = r['rocof_worst_hz_s']
    pcmd1 = r['p_command1_mw']; pcmd2 = r['p_command2_mw']
    pdel1 = r['p_delivered1_mw']; pdel2 = r['p_delivered2_mw']

    window_final = t >= FINAL_WINDOW_START_S

    freq_p2p_final = float(np.ptp(f[window_final])) if np.any(window_final) else float('nan')
    rocof_p2p_final = float(np.ptp(rocof[window_final])) if np.any(window_final) else float('nan')

    sign_rev_final = max(sign_reversals(pcmd1[window_final]), sign_reversals(pcmd2[window_final]))

    idx = r['action_step_indices']
    idx = idx[idx < len(pcmd1)]
    dp1_at_ctrl = pcmd1[idx]; dp2_at_ctrl = pcmd2[idx]
    n_visits_pos = int(np.sum(dp1_at_ctrl >= PMAX_MW - 1e-6) + np.sum(dp2_at_ctrl >= PMAX_MW - 1e-6))
    n_visits_neg = int(np.sum(dp1_at_ctrl <= -PMAX_MW + 1e-6) + np.sum(dp2_at_ctrl <= -PMAX_MW + 1e-6))

    period_est = periodicity_estimate(t[window_final], pcmd1[window_final])
    rocof_ctrl_rate = controller_rate_rocof_max(r)
    rocof_full = r['rocof_max_hz_s']
    undersample_gap_pct = (100.0 * (rocof_full - rocof_ctrl_rate) / rocof_full
                            if (rocof_full and not np.isnan(rocof_ctrl_rate)) else float('nan'))

    label = classify(r['tds_success'], freq_p2p_final, sign_rev_final, r['saturation_fraction'])

    row = dict(
        scenario=scenario['label'], condition=condition_label, k_f=k_f, k_r=k_r,
        Tc_ms=TC_REF_S * 1000, Pmax_MW=PMAX_MW, classification=label,
        df_nadir_hz=r['df_nadir_hz'], RoCoF_max_hz_s=rocof_full,
        RoCoF_max_controller_rate_hz_s=rocof_ctrl_rate, RoCoF_undersampling_gap_pct=undersample_gap_pct,
        time_to_nadir_s=r['t_nadir_s'], settling_time_s=r['settling_time_s'],
        Ppeak_MW=r['p_peak_mw'], saturation_fraction=r['saturation_fraction'],
        command_delivered_max_error_MW=r['command_delivered_max_error_mw'],
        command_delivered_rms_error_MW=r['command_delivered_rms_error_mw'],
        sign_reversals_final_window=sign_rev_final,
        n_visits_positive_saturation=n_visits_pos, n_visits_negative_saturation=n_visits_neg,
        freq_p2p_final_hz=freq_p2p_final, rocof_p2p_final_hz_s=rocof_p2p_final,
        oscillation_period_estimate_s=period_est,
        TDS_success=bool(r['tds_success']),
    )
    traces = dict(t=t, f_worst_hz=f, rocof_worst_hz_s=rocof,
                  p_command1_mw=pcmd1, p_command2_mw=pcmd2,
                  p_delivered1_mw=pdel1, p_delivered2_mw=pdel2)
    return row, traces


def add_improvement_cols(df, noffc_ref):
    for scenario in SCENARIOS:
        label = scenario['label']
        base_f = noffc_ref[label]['df_nadir_hz']
        base_r = noffc_ref[label]['RoCoF_max_hz_s']
        mask = df['scenario'] == label
        df.loc[mask, 'I_f_vs_NoFFC'] = (np.abs(base_f) - np.abs(df.loc[mask, 'df_nadir_hz'])) / np.abs(base_f)
        df.loc[mask, 'I_r_vs_NoFFC'] = (base_r - df.loc[mask, 'RoCoF_max_hz_s']) / base_r
    return df


def print_row(row):
    print(f"  [{row['scenario']:12s} {row['condition']:8s} Kf={row['k_f']:6.1f} Kr={row['k_r']:6.1f}] "
          f"class={row['classification']:16s} df_nadir={row['df_nadir_hz']:+.4f}Hz "
          f"RoCoF_max={row['RoCoF_max_hz_s']:.3f}Hz/s I_f={row['I_f_vs_NoFFC']*100:+.1f}% "
          f"I_r={row['I_r_vs_NoFFC']*100:+.1f}% sat={row['saturation_fraction']:.3f} "
          f"sign_rev={row['sign_reversals_final_window']} tds_ok={row['TDS_success']}")


def main():
    rows = []
    traces = {}

    print(f"=== P2-E5: Kf/Kr structure diagnostic (Tc={TC_REF_S*1000:.0f}ms DIAGNOSTIC REFERENCE ONLY, "
          f"Pmax={PMAX_MW}MW unchanged) ===")
    print(f"TC_P2E5_DIAGNOSTIC_REFERENCE_ONLY = {TC_P2E5_DIAGNOSTIC_REFERENCE_ONLY}")
    print(f"Kf0={KF0:.1f} MW/Hz, Kr0={KR0:.1f} MW/(Hz/s)")

    noffc_ref = {}
    print("\n--- NoFFC baselines ---")
    for scenario in SCENARIOS:
        r = run_condition(scenario, 0.0, 0.0, controller='no_ffc')
        row, tr = analyze_run(scenario, 'NoFFC', 0.0, 0.0, r)
        row['I_f_vs_NoFFC'] = 0.0
        row['I_r_vs_NoFFC'] = 0.0
        rows.append(row)
        noffc_ref[scenario['label']] = row
        traces[f"{scenario['label']}_NoFFC"] = tr
        print(f"  {scenario['label']}: df_nadir={row['df_nadir_hz']:+.4f}Hz RoCoF_max={row['RoCoF_max_hz_s']:.3f}Hz/s")

    print(f"\n=== F-only sweep (Kr=0), Kf multipliers {KF_MULTS} ===")
    f_only_rows = []
    for scenario in SCENARIOS:
        for mult in KF_MULTS:
            r = run_condition(scenario, mult * KF0, 0.0)
            row, tr = analyze_run(scenario, 'F-only', mult * KF0, 0.0, r)
            rows.append(row)
            f_only_rows.append(row)
            traces[f"{scenario['label']}_Fonly_mult{mult}"] = tr

    print(f"\n=== R-only sweep (Kf=0), Kr multipliers {KR_MULTS} ===")
    r_only_rows = []
    for scenario in SCENARIOS:
        for mult in KR_MULTS:
            r = run_condition(scenario, 0.0, mult * KR0)
            row, tr = analyze_run(scenario, 'R-only', 0.0, mult * KR0, r)
            rows.append(row)
            r_only_rows.append(row)
            traces[f"{scenario['label']}_Ronly_mult{mult}"] = tr

    df = pd.DataFrame(rows)
    df = add_improvement_cols(df, noffc_ref)
    # refresh f_only_rows/r_only_rows with I_f/I_r now that they're in df
    df_f = df[df['condition'] == 'F-only'].copy()
    df_r = df[df['condition'] == 'R-only'].copy()

    print("\n--- F-only results ---")
    for _, row in df_f.iterrows():
        print_row(row)
    print("\n--- R-only results ---")
    for _, row in df_r.iterrows():
        print_row(row)

    out_csv_f = os.path.join(OUT_DIAG, 'p2e5_kf_sweep.csv')
    out_csv_r = os.path.join(OUT_DIAG, 'p2e5_kr_sweep.csv')
    df_f.to_csv(out_csv_f, index=False)
    df_r.to_csv(out_csv_r, index=False)
    print(f"\nSaved: {out_csv_f} ({len(df_f)} rows)")
    print(f"Saved: {out_csv_r} ({len(df_r)} rows)")

    # --- Summary statistics per channel/probe (for CASE classification) ---
    print("\n=== Channel summary (per scenario) ===")
    channel_summary = {}
    for scenario in SCENARIOS:
        label = scenario['label']
        sub_f = df_f[df_f['scenario'] == label]
        sub_r = df_r[df_r['scenario'] == label]
        f_stable = sub_f[sub_f['classification'] == 'STABLE']
        r_stable = sub_r[sub_r['classification'] == 'STABLE']
        f_stable_useful = f_stable[f_stable['I_f_vs_NoFFC'] >= WIN_THRESHOLD]
        r_stable_useful = r_stable[r_stable['I_r_vs_NoFFC'] >= WIN_THRESHOLD]
        channel_summary[label] = dict(
            f_stable_frac=len(f_stable) / len(sub_f), r_stable_frac=len(r_stable) / len(sub_r),
            f_stable_mults=sorted(f_stable['k_f'].values / KF0),
            r_stable_mults=sorted(r_stable['k_r'].values / KR0),
            f_best_I_f=f_stable['I_f_vs_NoFFC'].max() if len(f_stable) else float('nan'),
            r_best_I_r=r_stable['I_r_vs_NoFFC'].max() if len(r_stable) else float('nan'),
            f_useful=len(f_stable_useful) > 0, r_useful=len(r_stable_useful) > 0,
        )
        print(f"  {label}: F-only stable_frac={channel_summary[label]['f_stable_frac']:.2f} "
              f"(mults={channel_summary[label]['f_stable_mults']}), "
              f"best I_f in stable region={channel_summary[label]['f_best_I_f']*100:.1f}%, useful={channel_summary[label]['f_useful']}")
        print(f"  {label}: R-only stable_frac={channel_summary[label]['r_stable_frac']:.2f} "
              f"(mults={channel_summary[label]['r_stable_mults']}), "
              f"best I_r in stable region={channel_summary[label]['r_best_I_r']*100:.1f}%, useful={channel_summary[label]['r_useful']}")

    all_f_stable_frac = np.mean([v['f_stable_frac'] for v in channel_summary.values()])
    all_r_stable_frac = np.mean([v['r_stable_frac'] for v in channel_summary.values()])
    any_f_useful = any(v['f_useful'] for v in channel_summary.values())
    any_r_useful = any(v['r_useful'] for v in channel_summary.values())
    print(f"\nOverall: mean F-only stable fraction={all_f_stable_frac:.2f}, "
          f"mean R-only stable fraction={all_r_stable_frac:.2f}, "
          f"F-only useful anywhere={any_f_useful}, R-only useful anywhere={any_r_useful}")

    # --- Conditional F+R grid: only build from points STABLE in BOTH probes ---
    common_f_mults = sorted(set(channel_summary[SCENARIOS[0]['label']]['f_stable_mults']) &
                             set(channel_summary[SCENARIOS[1]['label']]['f_stable_mults']))
    common_r_mults = sorted(set(channel_summary[SCENARIOS[0]['label']]['r_stable_mults']) &
                             set(channel_summary[SCENARIOS[1]['label']]['r_stable_mults']))
    print(f"\nKf multipliers stable in BOTH probes: {common_f_mults}")
    print(f"Kr multipliers stable in BOTH probes: {common_r_mults}")

    df_fr = pd.DataFrame()
    if len(common_f_mults) > 0 and len(common_r_mults) > 0:
        grid = [(fm, rm) for fm in common_f_mults for rm in common_r_mults]
        if len(grid) > MAX_FR_GRID:
            fm_sub = common_f_mults[::max(1, len(common_f_mults) // 4)][:4]
            rm_sub = common_r_mults[::max(1, len(common_r_mults) // 4)][:4]
            grid = [(fm, rm) for fm in fm_sub for rm in rm_sub][:MAX_FR_GRID]
        print(f"\n=== F+R grid ({len(grid)} combinations, drawn only from mutually-stable "
              f"F-only/R-only regions) ===")
        fr_rows = []
        for scenario in SCENARIOS:
            for fm, rm in grid:
                r = run_condition(scenario, fm * KF0, rm * KR0)
                row, tr = analyze_run(scenario, 'F+R', fm * KF0, rm * KR0, r)
                fr_rows.append(row)
                traces[f"{scenario['label']}_FR_f{fm}_r{rm}"] = tr
        df_fr = pd.DataFrame(fr_rows)
        df_fr = add_improvement_cols(df_fr, noffc_ref)
        for _, row in df_fr.iterrows():
            print_row(row)
        out_csv_fr = os.path.join(OUT_DIAG, 'p2e5_kf_kr_grid.csv')
        df_fr.to_csv(out_csv_fr, index=False)
        print(f"\nSaved: {out_csv_fr} ({len(df_fr)} rows)")
    else:
        print("\nF+R grid SKIPPED: no Kf and/or Kr multiplier is STABLE in both DESIGN probes "
              "simultaneously (Section 8 of the instruction: only build the grid from mutually-stable "
              "unidimensional regions).")

    out_npz = os.path.join(OUT_TRAJ, 'p2e5_physical_structure_traces.npz')
    flat_traces = {}
    for key, d in traces.items():
        for name, arr in d.items():
            flat_traces[f"{key}__{name}"] = arr
    np.savez(out_npz, **flat_traces)
    print(f"Saved: {out_npz}")

    make_figures(df_f, df_r, df_fr, traces, channel_summary)

    return df_f, df_r, df_fr, channel_summary


def make_figures(df_f, df_r, df_fr, traces, channel_summary):
    class_colors = {'STABLE': 'C2', 'MARGINAL': 'C1', 'LIMIT_CYCLE': 'C3', 'NUMERICAL_FAILURE': 'k'}

    # Fig 1: F-only stability/performance vs Kf
    fig1, (ax1a, ax1b) = plt.subplots(1, 2, figsize=(10, 3.5))
    for scenario in SCENARIOS:
        sub = df_f[df_f['scenario'] == scenario['label']].sort_values('k_f')
        ax1a.plot(sub['k_f'] / KF0, sub['I_f_vs_NoFFC'] * 100, marker='o', label=scenario['label'])
        for _, row in sub.iterrows():
            ax1b.scatter(row['k_f'] / KF0, 0 if scenario['label'] == SCENARIOS[0]['label'] else 1,
                         color=class_colors[row['classification']], s=70, zorder=3)
    ax1a.set_xlabel('Kf / Kf0'); ax1a.set_ylabel('I_f vs NoFFC (%)'); ax1a.set_title('F-only: nadir improvement')
    ax1a.axhline(WIN_THRESHOLD * 100, color='gray', linestyle=':', linewidth=1)
    ax1a.legend(fontsize=7); ax1a.grid(True, linestyle=':', alpha=0.6)
    ax1b.set_yticks([0, 1]); ax1b.set_yticklabels([s['label'] for s in SCENARIOS])
    ax1b.set_xlabel('Kf / Kf0'); ax1b.set_title('F-only: stability classification')
    fig1.tight_layout()
    fig1.savefig(os.path.join(OUT_FIG, 'p2e5_fig1_fonly_vs_kf.png'), dpi=200)
    plt.close(fig1)

    # Fig 2: R-only stability/performance vs Kr
    fig2, (ax2a, ax2b) = plt.subplots(1, 2, figsize=(10, 3.5))
    for scenario in SCENARIOS:
        sub = df_r[df_r['scenario'] == scenario['label']].sort_values('k_r')
        ax2a.plot(sub['k_r'] / KR0, sub['I_r_vs_NoFFC'] * 100, marker='o', label=scenario['label'])
        for _, row in sub.iterrows():
            ax2b.scatter(row['k_r'] / KR0, 0 if scenario['label'] == SCENARIOS[0]['label'] else 1,
                         color=class_colors[row['classification']], s=70, zorder=3)
    ax2a.set_xlabel('Kr / Kr0'); ax2a.set_ylabel('I_r vs NoFFC (%)'); ax2a.set_title('R-only: RoCoF improvement')
    ax2a.axhline(WIN_THRESHOLD * 100, color='gray', linestyle=':', linewidth=1)
    ax2a.legend(fontsize=7); ax2a.grid(True, linestyle=':', alpha=0.6)
    ax2b.set_yticks([0, 1]); ax2b.set_yticklabels([s['label'] for s in SCENARIOS])
    ax2b.set_xlabel('Kr / Kr0'); ax2b.set_title('R-only: stability classification')
    fig2.tight_layout()
    fig2.savefig(os.path.join(OUT_FIG, 'p2e5_fig2_ronly_vs_kr.png'), dpi=200)
    plt.close(fig2)

    # Fig 3: nadir & RoCoF improvement, F-only vs R-only side by side
    fig3, (ax3a, ax3b) = plt.subplots(1, 2, figsize=(10, 3.5))
    for scenario in SCENARIOS:
        subf = df_f[df_f['scenario'] == scenario['label']].sort_values('k_f')
        subr = df_r[df_r['scenario'] == scenario['label']].sort_values('k_r')
        ax3a.plot(subf['k_f'] / KF0, subf['I_r_vs_NoFFC'] * 100, marker='o', label=f"{scenario['label']} (cross-effect on RoCoF)")
        ax3b.plot(subr['k_r'] / KR0, subr['I_f_vs_NoFFC'] * 100, marker='o', label=f"{scenario['label']} (cross-effect on nadir)")
    ax3a.set_xlabel('Kf / Kf0'); ax3a.set_ylabel('I_r vs NoFFC (%)'); ax3a.set_title('F-only: cross-effect on RoCoF')
    ax3b.set_xlabel('Kr / Kr0'); ax3b.set_ylabel('I_f vs NoFFC (%)'); ax3b.set_title('R-only: cross-effect on nadir')
    for ax in (ax3a, ax3b):
        ax.axhline(0, color='gray', linewidth=0.8); ax.legend(fontsize=6); ax.grid(True, linestyle=':', alpha=0.6)
    fig3.tight_layout()
    fig3.savefig(os.path.join(OUT_FIG, 'p2e5_fig3_cross_effects.png'), dpi=200)
    plt.close(fig3)

    # Fig 4: representative trajectories F-only vs R-only (largest stable gain, gen_severe)
    f_stable = df_f[(df_f['scenario'] == 'gen_severe') & (df_f['classification'] == 'STABLE')]
    r_stable = df_r[(df_r['scenario'] == 'gen_severe') & (df_r['classification'] == 'STABLE')]
    fig4, ax4 = plt.subplots(figsize=(7, 3.5))
    tr0 = traces['gen_severe_NoFFC']
    ax4.plot(tr0['t'], tr0['f_worst_hz'], 'k:', label='NoFFC', linewidth=1.0)
    if len(f_stable):
        best_f_mult = f_stable.loc[f_stable['I_f_vs_NoFFC'].idxmax(), 'k_f'] / KF0
        tr = traces[f'gen_severe_Fonly_mult{best_f_mult}']
        ax4.plot(tr['t'], tr['f_worst_hz'], 'C0-', label=f'F-only (Kf={best_f_mult:.2f}x)', linewidth=1.1)
    if len(r_stable):
        best_r_mult = r_stable.loc[r_stable['I_r_vs_NoFFC'].idxmax(), 'k_r'] / KR0
        tr = traces[f'gen_severe_Ronly_mult{best_r_mult}']
        ax4.plot(tr['t'], tr['f_worst_hz'], 'C1-', label=f'R-only (Kr={best_r_mult:.2f}x)', linewidth=1.1)
    ax4.set_xlabel('Time (s)'); ax4.set_ylabel('Worst-bus frequency (Hz)')
    ax4.set_title('P2-E5 Fig 4: representative trajectories, gen_severe')
    ax4.legend(fontsize=7); ax4.grid(True, linestyle=':', alpha=0.6)
    fig4.tight_layout()
    fig4.savefig(os.path.join(OUT_FIG, 'p2e5_fig4_representative_trajectories.png'), dpi=200)
    plt.close(fig4)

    # Fig 5: Pareto map I_f vs I_r, if F+R was executed
    if df_fr is not None and len(df_fr):
        fig5, ax5 = plt.subplots(figsize=(6, 5))
        for scenario in SCENARIOS:
            sub = df_fr[df_fr['scenario'] == scenario['label']]
            ax5.scatter(sub['I_f_vs_NoFFC'] * 100, sub['I_r_vs_NoFFC'] * 100, label=scenario['label'], s=60)
        ax5.axhline(WIN_THRESHOLD * 100, color='gray', linestyle=':', linewidth=1)
        ax5.axvline(WIN_THRESHOLD * 100, color='gray', linestyle=':', linewidth=1)
        ax5.set_xlabel('I_f vs NoFFC (%)'); ax5.set_ylabel('I_r vs NoFFC (%)')
        ax5.set_title('P2-E5 Fig 5: F+R Pareto map (top-right = simultaneous improvement)')
        ax5.legend(fontsize=7); ax5.grid(True, linestyle=':', alpha=0.6)
        fig5.tight_layout()
        fig5.savefig(os.path.join(OUT_FIG, 'p2e5_fig5_pareto_map.png'), dpi=200)
        plt.close(fig5)

    # Fig 6: onset of oscillation for the first unstable R-only point (synchronized traces)
    r_unstable = df_r[(df_r['scenario'] == 'gen_severe') & (df_r['classification'] == 'LIMIT_CYCLE')].sort_values('k_r')
    if len(r_unstable):
        mult = r_unstable.iloc[0]['k_r'] / KR0
        tr = traces[f'gen_severe_Ronly_mult{mult}']
        fig6, (ax6a, ax6b) = plt.subplots(2, 1, figsize=(7, 5), sharex=True)
        window = (tr['t'] >= TD - 0.05) & (tr['t'] <= TD + 1.0)
        ax6a.plot(tr['t'][window], tr['rocof_worst_hz_s'][window], 'C3-', label='RoCoF')
        ax6a.set_ylabel('|RoCoF| (Hz/s)')
        ax6b.plot(tr['t'][window], tr['p_command1_mw'][window], 'k--', label='P_command1', linewidth=1.0)
        ax6b.plot(tr['t'][window], tr['p_delivered1_mw'][window], 'C0-', label='P_delivered1', linewidth=1.0)
        ax6b.set_ylabel('BESS1 power (MW)'); ax6b.set_xlabel('Time (s)')
        ax6a.set_title(f'P2-E5 Fig 6: onset of oscillation, R-only Kr={mult:.2f}x, gen_severe')
        ax6a.legend(fontsize=7); ax6b.legend(fontsize=7)
        ax6a.grid(True, linestyle=':', alpha=0.6); ax6b.grid(True, linestyle=':', alpha=0.6)
        fig6.tight_layout()
        fig6.savefig(os.path.join(OUT_FIG, 'p2e5_fig6_oscillation_onset.png'), dpi=200)
        plt.close(fig6)

    print(f"Saved figures to {OUT_FIG}")


if __name__ == '__main__':
    main()
