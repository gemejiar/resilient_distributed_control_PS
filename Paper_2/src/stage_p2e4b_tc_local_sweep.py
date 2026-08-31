#!/usr/bin/env python
"""
P2-E4 diagnostic extension -- local Tc sweep around the Tc=50ms instability
found in DEC-P2-009.

Goal: determine whether the Tc=50ms limit cycle is (1) a narrow band around
50ms, (2) a wide sampled-data instability region, (3) a Tc/ESD1/BusROCOF
interaction, or (4) an implementation/timing artifact -- WITHOUT calling it
"resonance" and WITHOUT touching Tr/Tf/Tw, Kf, Kr, Pmax, tip, BESS location,
or the aggressive gain. Everything is held fixed except Tc; reuses
p2_common.run_physical_scenario_tc() UNCHANGED (same driver as DEC-P2-009).

Tc points: the 3 already measured (20/50/100ms, DEC-P2-009) plus 7 new
diagnostic points (30/40/45/55/60/70/80ms) bracketing the unstable point.
Same two DESIGN probes as P2-E4 (gen_severe: GENROU_4 @ rho=0.90; load_severe:
PQ_9/bus 20 @ alpha_L=0.50), same conservative gain (gain_mult=0.5).

Classifies each (scenario, Tc) run as STABLE / MARGINAL / LIMIT_CYCLE /
NUMERICAL_FAILURE using an explicit, documented, uniformly-applied
quantitative rule (Section 4/5 below) -- not visual inspection and not
TDS_success alone.
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

PMAX_MW = 293.4
KF0 = PMAX_MW / 0.5
KR0 = PMAX_MW / 1.0
GAIN_CONSERVATIVE = 0.5  # UNCHANGED from DEC-P2-009 -- the only independent variable here is Tc
KF = GAIN_CONSERVATIVE * KF0
KR = GAIN_CONSERVATIVE * KR0

# Already-measured points (DEC-P2-009) + new diagnostic points bracketing 50ms.
# Not a denser grid yet -- localizing the approximate stability boundary only.
TC_LIST_MS = [20, 30, 40, 45, 50, 55, 60, 70, 80, 100]
TSTEP = 0.005  # identical to DEC-P2-009, fixed across every Tc

SCENARIOS = [
    dict(label='gen_severe', kind='gen', gen='GENROU_4', rho=0.90, lambda_L=1.00),
    dict(label='load_severe', kind='load', bus=20, alpha_L=0.50, lambda_L=1.00),
]

OUT_DIAG = os.path.join('Paper_2', 'artifacts', 'diagnostics')
OUT_TRAJ = os.path.join('Paper_2', 'artifacts', 'trajectories')
OUT_FIG = os.path.join('Paper_2', 'artifacts', 'figures')
for d in (OUT_DIAG, OUT_TRAJ, OUT_FIG):
    os.makedirs(d, exist_ok=True)

# --- Explicit, documented classification thresholds (Section 4/5 of the user's
# instruction: no visual-only classification, must require PERSISTENT
# evidence in the final part of the episode, applied identically to every
# Tc/scenario -- never tuned per point). ---
FINAL_WINDOW_START_S = TF_INITIAL - 1.0  # last 1 s of the 6 s horizon
STABLE_FREQ_P2P_MAX_HZ = 0.010     # <=10 mHz peak-to-peak in the final window
STABLE_SIGN_REV_MAX = 1            # <=1 sign reversal of Pcommand in the final window
STABLE_SAT_FRAC_MAX = 0.05         # <5% of control updates (whole episode) saturated
LIMIT_CYCLE_FREQ_P2P_MIN_HZ = 0.030  # >=30 mHz peak-to-peak in the final window
LIMIT_CYCLE_SIGN_REV_MIN = 3         # >=3 sign reversals in the final window (persistent, not one swing)


def run_condition(scenario, tc_ms):
    kwargs = dict(kind=scenario['kind'], lambda_L=scenario['lambda_L'],
                  p_max_bess_mw=PMAX_MW, k_f=KF, k_r=KR, tc=tc_ms / 1000.0, tstep=TSTEP,
                  controller='physical', tf=TF_INITIAL)
    if scenario['kind'] == 'gen':
        kwargs['gen'] = scenario['gen']
        kwargs['rho'] = scenario['rho']
    else:
        kwargs['bus'] = scenario['bus']
        kwargs['alpha_L'] = scenario['alpha_L']
    return run_physical_scenario_tc(**kwargs)


def sign_reversals(x, eps=1e-6):
    s = np.sign(np.where(np.abs(x) < eps, 0.0, x))
    nz = s[s != 0]
    if len(nz) < 2:
        return 0
    return int(np.sum(np.diff(nz) != 0))


def controller_rate_rocof_max(r):
    idx = r['action_step_indices']
    if len(idx) == 0 or len(r['rocof_worst_hz_s']) == 0:
        return float('nan')
    idx = idx[idx < len(r['rocof_worst_hz_s'])]
    if len(idx) == 0:
        return float('nan')
    return float(np.max(r['rocof_worst_hz_s'][idx]))


def periodicity_estimate(t, x, eps=1e-6):
    """Simple periodicity proxy: mean time between consecutive sign
    reversals of x, doubled (a full cycle = two reversals). NaN if fewer
    than 3 reversals (not enough to estimate a period)."""
    s = np.sign(np.where(np.abs(x) < eps, 0.0, x))
    nz_idx = np.where(s != 0)[0]
    if len(nz_idx) < 2:
        return float('nan')
    s_nz = s[nz_idx]
    t_nz = t[nz_idx]
    rev_idx = np.where(np.diff(s_nz) != 0)[0] + 1
    rev_times = t_nz[rev_idx]
    if len(rev_times) < 3:
        return float('nan')
    return float(2 * np.mean(np.diff(rev_times)))


def classify(tds_success, freq_p2p_final, sign_rev_final, sat_frac_full):
    if not tds_success:
        return 'NUMERICAL_FAILURE'
    is_stable = (freq_p2p_final <= STABLE_FREQ_P2P_MAX_HZ and
                 sign_rev_final <= STABLE_SIGN_REV_MAX and
                 sat_frac_full < STABLE_SAT_FRAC_MAX)
    is_limit_cycle = (freq_p2p_final >= LIMIT_CYCLE_FREQ_P2P_MIN_HZ and
                      sign_rev_final >= LIMIT_CYCLE_SIGN_REV_MIN)
    if is_limit_cycle:
        return 'LIMIT_CYCLE'
    if is_stable:
        return 'STABLE'
    return 'MARGINAL'


def analyze_run(scenario, tc_ms, r):
    t = r['t']
    f = r['f_worst_hz']
    rocof = r['rocof_worst_hz_s']
    pcmd1 = r['p_command1_mw']
    pcmd2 = r['p_command2_mw']
    pdel1 = r['p_delivered1_mw']
    pdel2 = r['p_delivered2_mw']

    window_final = t >= FINAL_WINDOW_START_S
    window_post_td = t >= TD

    freq_p2p_final = float(np.ptp(f[window_final])) if np.any(window_final) else float('nan')
    rocof_p2p_final = float(np.ptp(rocof[window_final])) if np.any(window_final) else float('nan')
    pcmd1_p2p_final = float(np.ptp(pcmd1[window_final])) if np.any(window_final) else float('nan')
    pdel1_p2p_final = float(np.ptp(pdel1[window_final])) if np.any(window_final) else float('nan')

    sign_rev_final_1 = sign_reversals(pcmd1[window_final])
    sign_rev_final_2 = sign_reversals(pcmd2[window_final])
    sign_rev_final = max(sign_rev_final_1, sign_rev_final_2)
    sign_rev_full = max(sign_reversals(pcmd1[window_post_td]), sign_reversals(pcmd2[window_post_td]))

    idx = r['action_step_indices']
    idx = idx[idx < len(pcmd1)]
    dp1_at_ctrl = pcmd1[idx]
    dp2_at_ctrl = pcmd2[idx]
    n_visits_pos = int(np.sum(dp1_at_ctrl >= PMAX_MW - 1e-6) + np.sum(dp2_at_ctrl >= PMAX_MW - 1e-6))
    n_visits_neg = int(np.sum(dp1_at_ctrl <= -PMAX_MW + 1e-6) + np.sum(dp2_at_ctrl <= -PMAX_MW + 1e-6))

    period_est = periodicity_estimate(t[window_final], pcmd1[window_final])

    rocof_ctrl_rate = controller_rate_rocof_max(r)
    rocof_full = r['rocof_max_hz_s']
    undersample_gap_pct = (100.0 * (rocof_full - rocof_ctrl_rate) / rocof_full
                            if (rocof_full and not np.isnan(rocof_ctrl_rate)) else float('nan'))

    label = classify(r['tds_success'], freq_p2p_final, sign_rev_final, r['saturation_fraction'])

    row = dict(
        scenario=scenario['label'], Tc_ms=tc_ms, Kf=KF, Kr=KR, Pmax_MW=PMAX_MW,
        classification=label,
        df_nadir_hz=r['df_nadir_hz'], RoCoF_max_hz_s=rocof_full,
        RoCoF_max_controller_rate_hz_s=rocof_ctrl_rate, RoCoF_undersampling_gap_pct=undersample_gap_pct,
        time_to_nadir_s=r['t_nadir_s'], settling_time_s=r['settling_time_s'],
        Ppeak_MW=r['p_peak_mw'], saturation_fraction=r['saturation_fraction'],
        command_delivered_max_error_MW=r['command_delivered_max_error_mw'],
        command_delivered_rms_error_MW=r['command_delivered_rms_error_mw'],
        sign_reversals_final_window=sign_rev_final, sign_reversals_full_post_td=sign_rev_full,
        n_visits_positive_saturation=n_visits_pos, n_visits_negative_saturation=n_visits_neg,
        freq_p2p_final_hz=freq_p2p_final, rocof_p2p_final_hz_s=rocof_p2p_final,
        pcommand1_p2p_final_mw=pcmd1_p2p_final, pdelivered1_p2p_final_mw=pdel1_p2p_final,
        oscillation_period_estimate_s=period_est,
        expected_actions=r['expected_actions'], actual_actions=r['actual_actions'],
        first_action_time_s=r['first_action_time_s'], last_action_time_s=r['last_action_time_s'],
        dae_t_final=r['dae_t_final'], max_step_gap_s=r['max_step_gap_s'],
        timing_exact=(r['expected_actions'] == r['actual_actions'] and
                      abs(r['dae_t_final'] - TF_INITIAL) < 2 * TSTEP),
        runtime_s=r['runtime_seconds'], TDS_success=bool(r['tds_success']),
    )
    traces = dict(t=t, f_worst_hz=f, rocof_worst_hz_s=rocof,
                  p_command1_mw=pcmd1, p_command2_mw=pcmd2,
                  p_delivered1_mw=pdel1, p_delivered2_mw=pdel2)
    return row, traces


def main():
    rows = []
    traces = {}
    print(f"=== P2-E4 diagnostic extension: local Tc sweep, Kf={KF:.1f} MW/Hz, Kr={KR:.1f} MW/(Hz/s) "
          f"(UNCHANGED conservative gain from DEC-P2-009) ===")
    print(f"Tc points: {TC_LIST_MS} ms")
    for scenario in SCENARIOS:
        for tc_ms in TC_LIST_MS:
            r = run_condition(scenario, tc_ms)
            row, tr = analyze_run(scenario, tc_ms, r)
            rows.append(row)
            traces[f"{scenario['label']}_Tc{tc_ms}"] = tr
            print(f"  [{scenario['label']:12s} Tc={tc_ms:3d}ms] class={row['classification']:16s} "
                  f"df_nadir={row['df_nadir_hz']:+.4f}Hz RoCoF_max={row['RoCoF_max_hz_s']:.3f}Hz/s "
                  f"freq_p2p_final={row['freq_p2p_final_hz']*1000:.1f}mHz "
                  f"sign_rev_final={row['sign_reversals_final_window']} "
                  f"sat_frac={row['saturation_fraction']:.3f} "
                  f"sat_visits(+/-)={row['n_visits_positive_saturation']}/{row['n_visits_negative_saturation']} "
                  f"period_est={row['oscillation_period_estimate_s']} "
                  f"timing_exact={row['timing_exact']} tds_ok={row['TDS_success']}")

    df = pd.DataFrame(rows)
    out_csv = os.path.join(OUT_DIAG, 'p2e4_tc_local_sweep.csv')
    df.to_csv(out_csv, index=False)
    print(f"\nSaved: {out_csv} ({len(df)} rows)")

    flat_traces = {}
    for key, d in traces.items():
        for name, arr in d.items():
            flat_traces[f"{key}__{name}"] = arr
    out_npz = os.path.join(OUT_TRAJ, 'p2e4_tc_local_sweep_traces.npz')
    np.savez(out_npz, **flat_traces)
    print(f"Saved: {out_npz}")

    print("\n--- Timing verification summary ---")
    print(f"all timing_exact: {bool(df['timing_exact'].all())}")
    if not df['timing_exact'].all():
        print(df[~df['timing_exact']][['scenario', 'Tc_ms', 'expected_actions', 'actual_actions', 'dae_t_final']])

    print("\n--- Classification summary ---")
    print(df.pivot_table(index='Tc_ms', columns='scenario', values='classification', aggfunc='first'))

    make_figures(df, traces)


def make_figures(df, traces):
    class_colors = {'STABLE': 'C2', 'MARGINAL': 'C1', 'LIMIT_CYCLE': 'C3', 'NUMERICAL_FAILURE': 'k'}
    class_markers = {'STABLE': 'o', 'MARGINAL': 's', 'LIMIT_CYCLE': 'X', 'NUMERICAL_FAILURE': 'v'}

    # Fig 1: stability map (Tc vs classification, one row per scenario)
    fig1, ax1 = plt.subplots(figsize=(7, 3))
    for i, scenario in enumerate(SCENARIOS):
        sub = df[df['scenario'] == scenario['label']].sort_values('Tc_ms')
        for _, row in sub.iterrows():
            ax1.scatter(row['Tc_ms'], i, color=class_colors[row['classification']],
                        marker=class_markers[row['classification']], s=90, zorder=3)
    ax1.set_yticks(range(len(SCENARIOS)))
    ax1.set_yticklabels([s['label'] for s in SCENARIOS])
    ax1.set_xlabel('Tc (ms)')
    ax1.set_title('P2-E4 diagnostic: stability classification vs Tc')
    handles = [plt.Line2D([0], [0], marker=class_markers[k], color='w', markerfacecolor=class_colors[k],
                           markersize=9, label=k) for k in class_colors]
    ax1.legend(handles=handles, fontsize=7, loc='upper right', ncol=2)
    ax1.grid(True, axis='x', linestyle=':', alpha=0.6)
    fig1.tight_layout()
    fig1.savefig(os.path.join(OUT_FIG, 'p2e4_tc_stability_map.png'), dpi=200)
    plt.close(fig1)

    # Fig 2: nadir / RoCoF vs Tc
    fig2, (ax2a, ax2b) = plt.subplots(1, 2, figsize=(9, 3.5))
    for scenario in SCENARIOS:
        sub = df[df['scenario'] == scenario['label']].sort_values('Tc_ms')
        ax2a.plot(sub['Tc_ms'], sub['df_nadir_hz'], marker='o', label=scenario['label'])
        ax2b.plot(sub['Tc_ms'], sub['RoCoF_max_hz_s'], marker='o', label=scenario['label'])
    ax2a.set_xlabel('Tc (ms)'); ax2a.set_ylabel('df_nadir (Hz)'); ax2a.set_title('Nadir vs Tc')
    ax2b.set_xlabel('Tc (ms)'); ax2b.set_ylabel('RoCoF_max (Hz/s)'); ax2b.set_title('RoCoF max vs Tc')
    for ax in (ax2a, ax2b):
        ax.legend(fontsize=7); ax.grid(True, linestyle=':', alpha=0.6)
    fig2.tight_layout()
    fig2.savefig(os.path.join(OUT_FIG, 'p2e4_tc_nadir_rocof_map.png'), dpi=200)
    plt.close(fig2)

    # Fig 3: saturation fraction vs Tc
    fig3, ax3 = plt.subplots(figsize=(6, 3.5))
    for scenario in SCENARIOS:
        sub = df[df['scenario'] == scenario['label']].sort_values('Tc_ms')
        ax3.plot(sub['Tc_ms'], sub['saturation_fraction'], marker='o', label=scenario['label'])
    ax3.set_xlabel('Tc (ms)'); ax3.set_ylabel('Saturation fraction')
    ax3.set_title('P2-E4 diagnostic: saturation fraction vs Tc')
    ax3.legend(fontsize=7); ax3.grid(True, linestyle=':', alpha=0.6)
    fig3.tight_layout()
    fig3.savefig(os.path.join(OUT_FIG, 'p2e4_tc_saturation_map.png'), dpi=200)
    plt.close(fig3)

    # Fig 4: command behavior (Pcommand1 in final window) across Tc, gen_severe
    tcs_to_plot = TC_LIST_MS
    fig4, axes4 = plt.subplots(2, 5, figsize=(18, 6), sharey=True)
    for ax, tc_ms in zip(axes4.flat, tcs_to_plot):
        key = f"gen_severe_Tc{tc_ms}"
        tr = traces[key]
        window = tr['t'] >= FINAL_WINDOW_START_S
        ax.plot(tr['t'][window], tr['p_command1_mw'][window], 'k--', linewidth=0.9, label='cmd')
        ax.plot(tr['t'][window], tr['p_delivered1_mw'][window], 'C0-', linewidth=0.9, label='del')
        ax.set_title(f'Tc={tc_ms}ms', fontsize=9)
        ax.grid(True, linestyle=':', alpha=0.5)
    axes4[0, 0].legend(fontsize=7)
    fig4.suptitle('P2-E4 diagnostic Fig: BESS1 command/delivered, final 1s window, gen_severe')
    fig4.tight_layout()
    fig4.savefig(os.path.join(OUT_FIG, 'p2e4_tc_command_behavior.png'), dpi=200)
    plt.close(fig4)

    print(f"Saved figures to {OUT_FIG}")


if __name__ == '__main__':
    main()
