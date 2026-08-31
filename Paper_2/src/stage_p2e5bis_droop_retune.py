#!/usr/bin/env python
"""
P2-E5bis -- retune the mandatory droop baseline under EXACTLY the current
candidate physical configuration (DEC-P2-022), so it can serve as the
`STOP-P2-A` Criterion-1 comparator (plan SS20: improvement must be measured
against the tuned droop, not against NoFFC).

Droop control law (pure proportional, local bus frequency, no RoCoF term) is
already available in p2_common.run_physical_scenario_tc() as the existing
'physical' controller with k_r=0.0 -- this is exactly Paper_1's
`P = -K_d * (f_local - F0)` law (Paper_1/src/run_ffc_study.py,
run_droop_validation(), lines 675-686), saturated to +-Pmax, ZOH at Tc. No new
controller code is written; only a gain grid + selection procedure.

Retuning methodology (adapted from Paper_1's tune_droop(), lines 713-748):
Paper_1 selected K_d by grid search over {0.25,0.5,1,2,4}xK0 minimizing a
J_val computed on 4 VALIDATION scenarios (V1-V4). Paper_2 governance forbids
touching validation at this stage -- the user's instruction explicitly says
"mismos DESIGN scenarios". This script therefore reproduces the SAME grid
(same K0=Pmax/0.5Hz=586.8MW/Hz basis, same 5-point multiplier set for direct
comparability with Paper_1) but selects K_d* using ONLY the two DESIGN
scenarios (gen_severe, load_severe), with the classify_v2 stability
classifier already validated in this session (DEC-P2-017) instead of Paper_1's
simpler pass/fail. J is a simplified two-term version of Paper_1's J_val
(|df_nadir|/0.5 + RoCoF_max/1.0, mean over both DESIGN scenarios) -- the
energy term of Paper_1's J_val is DROPPED because Paper_2's driver does not
log delivered BESS energy; this simplification is declared explicitly, not
hidden.

Config (frozen candidates, DEC-P2-018/020/022): BESS buses 16/20, Tc=tstep=
5ms (the CURRENT F+R candidate Tc, not Paper_1's/older P2 diagnostic
Tc=100ms reference -- comparison against droop must use the same Tc as the
F+R candidate it will be compared to), Pmax=293.4MW, tstep=5ms, same
low-inertia case, same two DESIGN scenarios.

No sweep beyond this grid, no tuning of Tc/Pmax/location, no TD3, no
validation, no P2-T*. Does not overwrite any existing CSV.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p2_common import run_physical_scenario_tc, TD, F0_HZ
from stage_p2e5b_fr_grid_corrected import analyze_trace_v2

PMAX_MW = 293.4
K0 = PMAX_MW / 0.5  # 586.8 MW/Hz -- same basis as Paper_1's K_0 and Paper_2's KF0
K_D_GRID_MULT = [0.25, 0.5, 1.0, 2.0, 4.0]  # same multiplier set as Paper_1 tune_droop()
TSTEP = 0.005
TC_S = TSTEP  # DEC-P2-020/022: current F+R candidate Tc, NOT the 100ms diagnostic reference
TF = 6.0
BESS_BUS1, BESS_BUS2 = 16, 20  # frozen, DEC-P2-018

SCENARIOS = [
    dict(label='gen_severe', kind='gen', gen='GENROU_4', rho=0.90, lambda_L=1.00),
    dict(label='load_severe', kind='load', bus=20, alpha_L=0.50, lambda_L=1.00),
]

OUT_DIAG = os.path.join('Paper_2', 'artifacts', 'diagnostics')
OUT_TRAJ = os.path.join('Paper_2', 'artifacts', 'trajectories')
os.makedirs(OUT_DIAG, exist_ok=True)
os.makedirs(OUT_TRAJ, exist_ok=True)


def run_grid():
    rows = []
    traces = {}
    for scenario in SCENARIOS:
        # NoFFC reference at this exact config, for I_f/I_r bookkeeping only
        # (STOP-P2-A itself is decided vs droop, not vs NoFFC -- this is a
        # secondary reference column, not the comparator).
        r0 = run_physical_scenario_tc(kind=scenario['kind'], gen=scenario.get('gen'),
                                       rho=scenario.get('rho'), bus=scenario.get('bus'),
                                       alpha_L=scenario.get('alpha_L'), lambda_L=scenario['lambda_L'],
                                       p_max_bess_mw=PMAX_MW, k_f=0.0, k_r=0.0, tc=TC_S, tstep=TSTEP,
                                       controller='no_ffc', bess_bus1=BESS_BUS1, bess_bus2=BESS_BUS2, tf=TF)
        noffc_nadir = float(np.min(r0['f_worst_hz']) - F0_HZ)
        noffc_rocof = float(np.max(r0['rocof_worst_hz_s']))

        for mult in K_D_GRID_MULT:
            k_d = mult * K0
            r = run_physical_scenario_tc(kind=scenario['kind'], gen=scenario.get('gen'),
                                          rho=scenario.get('rho'), bus=scenario.get('bus'),
                                          alpha_L=scenario.get('alpha_L'), lambda_L=scenario['lambda_L'],
                                          p_max_bess_mw=PMAX_MW, k_f=k_d, k_r=0.0, tc=TC_S, tstep=TSTEP,
                                          controller='physical', bess_bus1=BESS_BUS1, bess_bus2=BESS_BUS2, tf=TF)
            res = analyze_trace_v2(r['t'], r['f_worst_hz'], r['p_command1_mw'], r['p_command2_mw'],
                                    r['tds_success'], r['saturation_fraction'])
            i_f = (abs(noffc_nadir) - abs(r['df_nadir_hz'])) / abs(noffc_nadir)
            i_r = (noffc_rocof - r['rocof_max_hz_s']) / noffc_rocof
            row = dict(scenario=scenario['label'], k_d_mult=mult, k_d_mw_per_hz=k_d,
                       Tc_ms=TC_S * 1000, Pmax_MW=PMAX_MW,
                       df_nadir_hz=r['df_nadir_hz'], rocof_max_hz_s=r['rocof_max_hz_s'],
                       I_f_vs_NoFFC=i_f, I_r_vs_NoFFC=i_r,
                       Ppeak_MW=r['p_peak_mw'], saturation_fraction=r['saturation_fraction'],
                       TDS_success=bool(r['tds_success']),
                       classification_v2=res['classification_v2'],
                       detrended_frequency_p2p=res['detrended_frequency_p2p'],
                       sign_reversals_final_window=res['sign_reversals_final_window'])
            rows.append(row)
            key = f"{scenario['label']}_droop_mult{mult:g}"
            traces[key] = dict(t=r['t'], f_worst_hz=r['f_worst_hz'], rocof_worst_hz_s=r['rocof_worst_hz_s'],
                                p_command1_mw=r['p_command1_mw'], p_command2_mw=r['p_command2_mw'],
                                p_delivered1_mw=r['p_delivered1_mw'], p_delivered2_mw=r['p_delivered2_mw'])
            print(f"  [{scenario['label']:12s} Kd={mult:.2f}x={k_d:7.1f}MW/Hz] "
                  f"class={row['classification_v2']:14s} df_nadir={row['df_nadir_hz']:+.4f}Hz "
                  f"RoCoF_max={row['rocof_max_hz_s']:.3f}Hz/s I_f={i_f*100:+.1f}% I_r={i_r*100:+.1f}% "
                  f"sat={row['saturation_fraction']:.3f}")
        traces[f"{scenario['label']}_NoFFC"] = dict(
            t=r0['t'], f_worst_hz=r0['f_worst_hz'], rocof_worst_hz_s=r0['rocof_worst_hz_s'],
            p_command1_mw=r0['p_command1_mw'], p_command2_mw=r0['p_command2_mw'],
            p_delivered1_mw=r0['p_delivered1_mw'], p_delivered2_mw=r0['p_delivered2_mw'])
    return pd.DataFrame(rows), traces


def select_kd_star(df):
    """Among K_d multipliers STABLE (classify_v2) in BOTH DESIGN scenarios,
    pick the one minimizing the simplified two-term J (mean over scenarios of
    |df_nadir|/0.5 + RoCoF_max/1.0). No energy term (not logged, see module
    docstring)."""
    stable_mults = {}
    for scenario in SCENARIOS:
        label = scenario['label']
        sub = df[(df['scenario'] == label) & (df['classification_v2'] == 'STABLE')]
        stable_mults[label] = set(sub['k_d_mult'].values)
    common = sorted(stable_mults[SCENARIOS[0]['label']] & stable_mults[SCENARIOS[1]['label']])
    print(f"\nK_d multipliers STABLE (v2) in BOTH DESIGN scenarios: {common}")
    if not common:
        return None, None

    j_by_mult = {}
    for mult in common:
        j_terms = []
        for scenario in SCENARIOS:
            row = df[(df['scenario'] == scenario['label']) & (df['k_d_mult'] == mult)].iloc[0]
            j_terms.append(abs(row['df_nadir_hz']) / 0.5 + row['rocof_max_hz_s'] / 1.0)
        j_by_mult[mult] = float(np.mean(j_terms))
    best_mult = min(j_by_mult, key=j_by_mult.get)
    print("J (mean over DESIGN scenarios, lower is better):")
    for mult in common:
        marker = '  <-- selected' if mult == best_mult else ''
        print(f"  K_d={mult:.2f}x  J={j_by_mult[mult]:.4f}{marker}")
    return best_mult, j_by_mult[best_mult]


def main():
    print("=== P2-E5bis: droop retune under current candidate config "
          f"(buses {BESS_BUS1}/{BESS_BUS2}, Tc=tstep={TC_S*1000:.1f}ms, Pmax={PMAX_MW}MW) ===\n")
    df, traces = run_grid()

    out_csv = os.path.join(OUT_DIAG, 'p2e5bis_droop_retune.csv')
    df.to_csv(out_csv, index=False)
    print(f"\nSaved: {out_csv}")

    out_npz = os.path.join(OUT_TRAJ, 'p2e5bis_droop_retune_traces.npz')
    flat = {}
    for key, d in traces.items():
        for name, arr in d.items():
            flat[f"{key}__{name}"] = arr
    np.savez_compressed(out_npz, **flat)
    print(f"Saved: {out_npz}")

    best_mult, best_j = select_kd_star(df)
    if best_mult is None:
        print("\nNo K_d multiplier is STABLE in both DESIGN scenarios -- droop retune INCONCLUSIVE, "
              "cannot select K_d* from this grid. Escalate to user.")
        return

    print(f"\n=== Selected droop baseline: K_d* = {best_mult:.2f}x = {best_mult*K0:.1f} MW/Hz "
          f"(Paper_1 frozen value was 580.0 MW/Hz ~= {580.0/K0:.2f}x on this K0 basis) ===")
    for scenario in SCENARIOS:
        row = df[(df['scenario'] == scenario['label']) & (df['k_d_mult'] == best_mult)].iloc[0]
        print(f"  {scenario['label']:12s} df_nadir={row['df_nadir_hz']:+.4f}Hz "
              f"RoCoF_max={row['rocof_max_hz_s']:.3f}Hz/s I_f_vs_NoFFC={row['I_f_vs_NoFFC']*100:+.1f}% "
              f"I_r_vs_NoFFC={row['I_r_vs_NoFFC']*100:+.1f}% sat={row['saturation_fraction']:.3f} "
              f"class={row['classification_v2']}")


if __name__ == '__main__':
    main()
