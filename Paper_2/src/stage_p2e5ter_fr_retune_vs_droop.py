#!/usr/bin/env python
"""
P2-E5ter -- final retune of Physical F+R (Kf, Kr) under the FROZEN config,
to give F+R a fair chance against the tuned droop baseline frozen in
DEC-P2-024 (Kd*=4694.4 MW/Hz). Authorized explicitly by the user
("AUTORIZO EL CIERRE DEFINITIVO DE STOP-P2-A MEDIANTE RETUNING FINAL DEL
CONTROLADOR PHYSICAL F+R").

Frozen (unchanged): BESS buses 16/20, Tc=tstep=5ms, Pmax=293.4MW/BESS, tip,
BusROCOF, low-inertia case, gen_severe/load_severe DESIGN scenarios,
droop*=4694.4 MW/Hz (NOT re-tuned here). Control law UNCHANGED:
P = -Kf*df - Kr*RoCoF, saturated +-Pmax (existing 'physical' controller,
no new code).

Small grid around the current point (not an open sweep), per explicit user
spec: Kf/Kf0 in {0.5,1,2,4} x Kr/Kr0 in {0.25,0.5,0.75,1,1.5,2} = 24 combos,
both DESIGN scenarios (48 sims) + droop* re-run here (2 sims) for a fully
self-contained, apples-to-apples artifact.

Selection: discard any combo LIMIT_CYCLE/NUMERICAL_FAILURE/not classify_v2
STABLE in BOTH scenarios (this already encodes "no pathological saturation",
classify_v2's STABLE requires sat_frac<0.05). Among STABLE survivors, select
by minimum J_phys = mean over both DESIGN scenarios of
|df_nadir|/0.5 + RoCoF_max/1.0 -- the same criterion already used for the
droop retune (DEC-P2-023/024).

Final comparison and STOP-P2-A Criterion-1 verdict computed vs. droop*
(DEC-P2-024), NOT vs. NoFFC (NoFFC numbers are also recorded for context
only, per the running convention in this campaign, never used as the
decision metric here).

No re-tuning of droop, no Tc/BESS-location/Pmax change, no TD3, no
validation, no P2-T*.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p2_common import run_physical_scenario_tc
from stage_p2e5b_fr_grid_corrected import analyze_trace_v2

PMAX_MW = 293.4
KF0 = PMAX_MW / 0.5   # 586.8 MW/Hz
KR0 = PMAX_MW / 1.0   # 293.4 MW/(Hz/s)
KD_STAR_MW_PER_HZ = 4694.4  # frozen, DEC-P2-024 -- NOT re-tuned here

KF_MULT_GRID = [0.5, 1.0, 2.0, 4.0]
KR_MULT_GRID = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0]

TSTEP = 0.005
TC_S = TSTEP
TF = 6.0
BESS_BUS1, BESS_BUS2 = 16, 20

SCENARIOS = [
    dict(label='gen_severe', kind='gen', gen='GENROU_4', rho=0.90, lambda_L=1.00),
    dict(label='load_severe', kind='load', bus=20, alpha_L=0.50, lambda_L=1.00),
]

OUT_DIAG = os.path.join('Paper_2', 'artifacts', 'diagnostics')
OUT_TRAJ = os.path.join('Paper_2', 'artifacts', 'trajectories')
os.makedirs(OUT_DIAG, exist_ok=True)
os.makedirs(OUT_TRAJ, exist_ok=True)


def run_one(scenario, k_f, k_r, controller):
    r = run_physical_scenario_tc(kind=scenario['kind'], gen=scenario.get('gen'),
                                  rho=scenario.get('rho'), bus=scenario.get('bus'),
                                  alpha_L=scenario.get('alpha_L'), lambda_L=scenario['lambda_L'],
                                  p_max_bess_mw=PMAX_MW, k_f=k_f, k_r=k_r, tc=TC_S, tstep=TSTEP,
                                  controller=controller, bess_bus1=BESS_BUS1, bess_bus2=BESS_BUS2, tf=TF)
    res = analyze_trace_v2(r['t'], r['f_worst_hz'], r['p_command1_mw'], r['p_command2_mw'],
                            r['tds_success'], r['saturation_fraction'])
    j_phys = abs(r['df_nadir_hz']) / 0.5 + r['rocof_max_hz_s'] / 1.0
    row = dict(scenario=scenario['label'],
               df_nadir_hz=r['df_nadir_hz'], rocof_max_hz_s=r['rocof_max_hz_s'], J_phys=j_phys,
               Ppeak_MW=r['p_peak_mw'], saturation_fraction=r['saturation_fraction'],
               settling_time_s=r['settling_time_s'], TDS_success=bool(r['tds_success']),
               classification_v2=res['classification_v2'],
               detrended_frequency_p2p=res['detrended_frequency_p2p'],
               persistence_ratio=res['persistence_ratio'],
               sign_reversals_final_window=res['sign_reversals_final_window'])
    return row


def main():
    print(f"=== P2-E5ter: F+R retune grid, Kf/Kf0 x {KF_MULT_GRID}, Kr/Kr0 x {KR_MULT_GRID} "
          f"({len(KF_MULT_GRID)*len(KR_MULT_GRID)} combos x 2 scenarios), "
          f"buses {BESS_BUS1}/{BESS_BUS2}, Tc=tstep={TC_S*1000:.1f}ms ===\n")

    rows = []

    # NoFFC reference (context only)
    noffc_ref = {}
    for scenario in SCENARIOS:
        row = run_one(scenario, 0.0, 0.0, 'no_ffc')
        row['controller'] = 'NoFFC'
        rows.append(row)
        noffc_ref[scenario['label']] = dict(nadir=row['df_nadir_hz'], rocof=row['rocof_max_hz_s'])
        print(f"  [{scenario['label']:12s} NoFFC ] df_nadir={row['df_nadir_hz']:+.4f}Hz "
              f"RoCoF_max={row['rocof_max_hz_s']:.3f}Hz/s")

    # droop*, re-run here for a self-contained comparison
    droop_ref = {}
    for scenario in SCENARIOS:
        row = run_one(scenario, KD_STAR_MW_PER_HZ, 0.0, 'physical')
        row['controller'] = 'droop_star'
        rows.append(row)
        droop_ref[scenario['label']] = dict(nadir=row['df_nadir_hz'], rocof=row['rocof_max_hz_s'],
                                             J=row['J_phys'], sat=row['saturation_fraction'])
        print(f"  [{scenario['label']:12s} droop*] df_nadir={row['df_nadir_hz']:+.4f}Hz "
              f"RoCoF_max={row['rocof_max_hz_s']:.3f}Hz/s J={row['J_phys']:.4f} "
              f"sat={row['saturation_fraction']:.3f} class={row['classification_v2']}")

    # F+R grid
    for kf_m in KF_MULT_GRID:
        for kr_m in KR_MULT_GRID:
            k_f, k_r = kf_m * KF0, kr_m * KR0
            for scenario in SCENARIOS:
                row = run_one(scenario, k_f, k_r, 'physical')
                row['controller'] = 'F+R'
                row['kf_mult'] = kf_m
                row['kr_mult'] = kr_m
                rows.append(row)
                print(f"  [{scenario['label']:12s} Kf={kf_m:.2f}x Kr={kr_m:.2f}x] "
                      f"df_nadir={row['df_nadir_hz']:+.4f}Hz RoCoF_max={row['rocof_max_hz_s']:.3f}Hz/s "
                      f"J={row['J_phys']:.4f} sat={row['saturation_fraction']:.3f} "
                      f"class={row['classification_v2']:14s} settle={row['settling_time_s']*1000:.0f}ms")

    df = pd.DataFrame(rows)
    out_csv = os.path.join(OUT_DIAG, 'p2e5ter_fr_retune_vs_droop.csv')
    df.to_csv(out_csv, index=False)
    print(f"\nSaved: {out_csv}")

    # ---- Selection: discard non-STABLE-in-both, pick min J_phys among survivors ----
    fr = df[df['controller'] == 'F+R'].copy()
    survivors = []
    for (kf_m, kr_m), sub in fr.groupby(['kf_mult', 'kr_mult']):
        if len(sub) == 2 and (sub['classification_v2'] == 'STABLE').all():
            survivors.append((kf_m, kr_m, sub['J_phys'].mean()))
    survivors_df = pd.DataFrame(survivors, columns=['kf_mult', 'kr_mult', 'J_phys_mean']).sort_values('J_phys_mean')
    print(f"\n=== {len(survivors_df)}/{len(KF_MULT_GRID)*len(KR_MULT_GRID)} combinations STABLE in BOTH "
          f"scenarios (discarded: LIMIT_CYCLE / NUMERICAL_FAILURE / pathological saturation) ===")
    print(survivors_df.to_string(index=False))

    if len(survivors_df) == 0:
        print("\nNo F+R combination is STABLE in both scenarios -- cannot select a retuned F+R. "
              "STOP-P2-A Criterion 1: FAIL (no valid F+R candidate). Escalate to user.")
        return

    best_kf, best_kr = survivors_df.iloc[0]['kf_mult'], survivors_df.iloc[0]['kr_mult']
    print(f"\nSelected (min J_phys among STABLE survivors): Kf={best_kf:.2f}x={best_kf*KF0:.1f}MW/Hz, "
          f"Kr={best_kr:.2f}x={best_kr*KR0:.1f}MW/(Hz/s)")

    # ---- Final comparison: best F+R vs droop*, vs droop* (NOT vs NoFFC) ----
    print("\n=== FINAL COMPARISON: best F+R vs. droop* (frozen, DEC-P2-024) ===")
    verdict_ok = True
    for scenario in SCENARIOS:
        label = scenario['label']
        fr_row = fr[(fr['scenario'] == label) & (fr['kf_mult'] == best_kf) & (fr['kr_mult'] == best_kr)].iloc[0]
        d = droop_ref[label]
        i_f_vs_droop = (abs(d['nadir']) - abs(fr_row['df_nadir_hz'])) / abs(d['nadir'])
        i_r_vs_droop = (d['rocof'] - fr_row['rocof_max_hz_s']) / d['rocof']
        material = (i_f_vs_droop >= 0.10) and (i_r_vs_droop >= 0.10)
        simultaneous_improvement = (i_f_vs_droop > 0) and (i_r_vs_droop > 0)
        if not simultaneous_improvement:
            verdict_ok = False
        print(f"  {label:12s} droop*: df_nadir={d['nadir']:+.4f}Hz RoCoF={d['rocof']:.3f}Hz/s "
              f"J={d['J']:.4f}")
        print(f"  {label:12s} F+R*:   df_nadir={fr_row['df_nadir_hz']:+.4f}Hz "
              f"RoCoF={fr_row['rocof_max_hz_s']:.3f}Hz/s J={fr_row['J_phys']:.4f} "
              f"sat={fr_row['saturation_fraction']:.3f}")
        print(f"  {label:12s} I_f_vs_droop={i_f_vs_droop*100:+.1f}%  I_r_vs_droop={i_r_vs_droop*100:+.1f}%  "
              f"simultaneous_improvement={simultaneous_improvement}  material(>=10%% both)={material}")

    print(f"\n=== STOP-P2-A Criterion 1 verdict (simultaneous, reproducible improvement over droop*, "
          f"both DESIGN scenarios) ===")
    if verdict_ok:
        print("Best F+R shows a simultaneous (nadir AND RoCoF) improvement over droop* in BOTH "
              "DESIGN scenarios -- Criterion 1 direction: PASS-leaning (see printed I_f/I_r for "
              "materiality against the SS20 10% orientative design target).")
    else:
        print("Best F+R does NOT show a simultaneous improvement over droop* in both scenarios -- "
              "Criterion 1: FAIL. Per user instruction (point 10): STOP-P2-A = FAIL definitivo; "
              "no TD3 training under the current plan.")


if __name__ == '__main__':
    main()
