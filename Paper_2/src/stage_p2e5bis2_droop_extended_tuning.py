#!/usr/bin/env python
"""
P2-E5bis, controlled extension -- authorized explicitly by the user after
DEC-P2-023 showed the 0.25-4.0x*K0 droop grid did not bound an interior
optimum (monotonic improvement all the way to the tested edge).

Architecture UNCHANGED: P = -Kd * df_local, saturated to +-Pmax, ZOH at
Tc=tstep=5ms (same as the F+R candidate). No new controller code -- still the
existing 'physical' controller with k_r=0.0.

Grid: Kd/K0 in {4, 6, 8, 12, 16} (K0=Pmax/0.5Hz=586.8MW/Hz), both DESIGN
scenarios (gen_severe, load_severe), buses 16/20, Pmax=293.4MW, Tc=tstep=5ms.
Kd=4.0x is re-run here (not reused from p2e5bis) so every point in this
extended analysis comes from the identical code path/instrumentation.

Per point: df_nadir, RoCoF_max, J_phys=|df_nadir|/0.5+RoCoF_max/1.0 (mean over
both DESIGN scenarios), Ppeak, saturation_fraction, classify_v2 stability,
post-event oscillation (detrended p2p / persistence / sign reversals),
settling_time_s (already computed by run_physical_scenario_tc, +-20mHz band
around the final value), and Delta_f_sat=Pmax/Kd (documentation only, not a
simulated quantity).

Stopping-rule evaluation (per user's Section 7-10) is applied POST-HOC to the
full {4,6,8,12,16} grid (all 5 points are run -- computationally cheap, and
rule 10 explicitly anticipates evaluating up to 16x before deciding, so there
is no adaptive early-stop mid-grid; the decision of what to do BEYOND 16x is
what gets escalated, not whether to run each point).

Finally: tuned droop (whatever Kd* the stopping rules select, or the best
available point if no freeze condition is met) is compared against Physical
F+R (Kf=586.8, Kr=220.05) on the SAME two DESIGN probes, both re-run here
under identical code path for a clean apples-to-apples comparison.

No TD3, no validation, no P2-T*.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p2_common import run_physical_scenario_tc, F0_HZ
from stage_p2e5b_fr_grid_corrected import analyze_trace_v2

PMAX_MW = 293.4
K0 = PMAX_MW / 0.5  # 586.8 MW/Hz
KF0, KR0 = PMAX_MW / 0.5, PMAX_MW / 1.0
KD_MULT_GRID = [4.0, 6.0, 8.0, 12.0, 16.0]
KF_FR, KR_FR = 1.0 * KF0, 0.75 * KR0  # frozen F+R candidate (DEC-P2-018/020)
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


def run_one(scenario, k_f, k_r, controller_tag):
    r = run_physical_scenario_tc(kind=scenario['kind'], gen=scenario.get('gen'),
                                  rho=scenario.get('rho'), bus=scenario.get('bus'),
                                  alpha_L=scenario.get('alpha_L'), lambda_L=scenario['lambda_L'],
                                  p_max_bess_mw=PMAX_MW, k_f=k_f, k_r=k_r, tc=TC_S, tstep=TSTEP,
                                  controller='physical' if (k_f or k_r) else 'no_ffc',
                                  bess_bus1=BESS_BUS1, bess_bus2=BESS_BUS2, tf=TF)
    res = analyze_trace_v2(r['t'], r['f_worst_hz'], r['p_command1_mw'], r['p_command2_mw'],
                            r['tds_success'], r['saturation_fraction'])
    row = dict(controller=controller_tag, scenario=scenario['label'],
               df_nadir_hz=r['df_nadir_hz'], rocof_max_hz_s=r['rocof_max_hz_s'],
               settling_time_s=r['settling_time_s'], Ppeak_MW=r['p_peak_mw'],
               saturation_fraction=r['saturation_fraction'], TDS_success=bool(r['tds_success']),
               classification_v2=res['classification_v2'],
               detrended_frequency_p2p=res['detrended_frequency_p2p'],
               persistence_ratio=res['persistence_ratio'],
               sign_reversals_final_window=res['sign_reversals_final_window'])
    trace = dict(t=r['t'], f_worst_hz=r['f_worst_hz'], rocof_worst_hz_s=r['rocof_worst_hz_s'],
                 p_command1_mw=r['p_command1_mw'], p_command2_mw=r['p_command2_mw'],
                 p_delivered1_mw=r['p_delivered1_mw'], p_delivered2_mw=r['p_delivered2_mw'])
    return row, trace


def main():
    print(f"=== P2-E5bis extended: droop grid Kd/K0 = {KD_MULT_GRID}, buses {BESS_BUS1}/{BESS_BUS2}, "
          f"Tc=tstep={TC_S*1000:.1f}ms ===\n")

    rows, traces = [], {}

    # NoFFC reference (for reporting only, not the STOP-P2-A comparator)
    noffc_ref = {}
    for scenario in SCENARIOS:
        row, tr = run_one(scenario, 0.0, 0.0, 'NoFFC')
        rows.append(row)
        traces[f"{scenario['label']}_NoFFC"] = tr
        noffc_ref[scenario['label']] = dict(nadir=row['df_nadir_hz'], rocof=row['rocof_max_hz_s'])
        print(f"  [{scenario['label']:12s} NoFFC] df_nadir={row['df_nadir_hz']:+.4f}Hz "
              f"RoCoF_max={row['rocof_max_hz_s']:.3f}Hz/s")

    # Droop grid
    for mult in KD_MULT_GRID:
        k_d = mult * K0
        delta_f_sat = PMAX_MW / k_d
        for scenario in SCENARIOS:
            row, tr = run_one(scenario, k_d, 0.0, f'droop_{mult:g}x')
            row['k_d_mult'] = mult
            row['k_d_mw_per_hz'] = k_d
            row['delta_f_sat_hz'] = delta_f_sat
            row['J_phys'] = abs(row['df_nadir_hz']) / 0.5 + row['rocof_max_hz_s'] / 1.0
            rows.append(row)
            traces[f"{scenario['label']}_droop_{mult:g}x"] = tr
            print(f"  [{scenario['label']:12s} Kd={mult:5.1f}x={k_d:8.1f}MW/Hz  "
                  f"df_sat={delta_f_sat*1000:5.1f}mHz] df_nadir={row['df_nadir_hz']:+.4f}Hz "
                  f"RoCoF_max={row['rocof_max_hz_s']:.3f}Hz/s J={row['J_phys']:.4f} "
                  f"sat={row['saturation_fraction']:.3f} class={row['classification_v2']} "
                  f"settle={row['settling_time_s']*1000:.0f}ms")

    # F+R candidate, re-run here for apples-to-apples comparison
    for scenario in SCENARIOS:
        row, tr = run_one(scenario, KF_FR, KR_FR, 'F+R')
        row['J_phys'] = abs(row['df_nadir_hz']) / 0.5 + row['rocof_max_hz_s'] / 1.0
        rows.append(row)
        traces[f"{scenario['label']}_FR"] = tr
        print(f"  [{scenario['label']:12s} F+R  Kf={KF_FR:.1f} Kr={KR_FR:.1f}] "
              f"df_nadir={row['df_nadir_hz']:+.4f}Hz RoCoF_max={row['rocof_max_hz_s']:.3f}Hz/s "
              f"J={row['J_phys']:.4f} sat={row['saturation_fraction']:.3f} class={row['classification_v2']}")

    df = pd.DataFrame(rows)
    out_csv = os.path.join(OUT_DIAG, 'p2e5bis2_droop_extended_tuning.csv')
    df.to_csv(out_csv, index=False)
    print(f"\nSaved: {out_csv}")

    out_npz = os.path.join(OUT_TRAJ, 'p2e5bis2_droop_extended_tuning_traces.npz')
    flat = {}
    for key, d in traces.items():
        for name, arr in d.items():
            flat[f"{key}__{name}"] = arr
    np.savez_compressed(out_npz, **flat)
    print(f"Saved: {out_npz}")

    # ---- Stopping-rule evaluation (Section 7-10), applied to the droop grid only ----
    droop = df[df['controller'].str.startswith('droop_')].copy()
    j_mean = droop.groupby('k_d_mult')['J_phys'].mean().sort_index()
    print("\n=== J_phys (mean over both DESIGN scenarios) vs Kd ===")
    for mult, j in j_mean.items():
        print(f"  Kd={mult:5.1f}x  J_phys={j:.4f}")

    mults = list(j_mean.index)
    freeze_mult, freeze_reason = None, None

    # Rule C: reversal (RoCoF or nadir gets worse at higher Kd, per scenario)
    reversal_at = None
    for scenario in SCENARIOS:
        sub = droop[droop['scenario'] == scenario['label']].sort_values('k_d_mult')
        nadir_abs = sub['df_nadir_hz'].abs().values
        rocof = sub['rocof_max_hz_s'].values
        for i in range(1, len(sub)):
            if nadir_abs[i] > nadir_abs[i - 1] + 1e-6 or rocof[i] > rocof[i - 1] + 1e-6:
                reversal_at = float(sub['k_d_mult'].values[i])
                print(f"\n[Rule C] Reversal detected in {scenario['label']} at Kd={reversal_at:.1f}x "
                      f"(nadir or RoCoF got WORSE than the previous point)")
                break
        if reversal_at:
            break

    # Rule D: persistent oscillation / LIMIT_CYCLE anywhere in the grid
    osc_at = None
    bad = droop[(droop['classification_v2'] == 'LIMIT_CYCLE') |
                (droop['classification_v2'] == 'NUMERICAL_FAILURE')]
    if len(bad):
        osc_at = float(bad['k_d_mult'].min())
        print(f"\n[Rule D] Non-STABLE classification first appears at Kd={osc_at:.1f}x "
              f"({bad.sort_values('k_d_mult').iloc[0]['classification_v2']})")

    # Rule E: saturation growing to relay-like behavior (threshold declared explicitly: >=0.5)
    RELAY_THRESHOLD = 0.5
    relay = droop[droop['saturation_fraction'] >= RELAY_THRESHOLD]
    relay_at = float(relay['k_d_mult'].min()) if len(relay) else None
    if relay_at:
        print(f"\n[Rule E] saturation_fraction >= {RELAY_THRESHOLD} first at Kd={relay_at:.1f}x "
              f"(relay-like behavior)")

    # Rule A: interior minimum of J_phys
    interior_min_mult = None
    for i in range(1, len(mults) - 1):
        if j_mean.iloc[i] < j_mean.iloc[i - 1] and j_mean.iloc[i] < j_mean.iloc[i + 1]:
            interior_min_mult = mults[i]
            break
    if interior_min_mult:
        print(f"\n[Rule A] Interior minimum of J_phys at Kd={interior_min_mult:.1f}x")

    # Rule B: plateau -- consecutive improvement <1% in BOTH df_nadir and RoCoF_max, both scenarios
    plateau_at = None
    for i in range(1, len(mults)):
        m_prev, m_cur = mults[i - 1], mults[i]
        both_below_1pct = True
        for scenario in SCENARIOS:
            sub = droop[droop['scenario'] == scenario['label']].set_index('k_d_mult')
            d_nadir = abs(sub.loc[m_prev, 'df_nadir_hz']) - abs(sub.loc[m_cur, 'df_nadir_hz'])
            d_rocof = sub.loc[m_prev, 'rocof_max_hz_s'] - sub.loc[m_cur, 'rocof_max_hz_s']
            rel_nadir = d_nadir / abs(sub.loc[m_prev, 'df_nadir_hz'])
            rel_rocof = d_rocof / sub.loc[m_prev, 'rocof_max_hz_s']
            if rel_nadir >= 0.01 or rel_rocof >= 0.01:
                both_below_1pct = False
        if both_below_1pct:
            plateau_at = m_cur
            break
    if plateau_at:
        print(f"\n[Rule B] Plateau (<1% improvement in both metrics, both scenarios) reached at "
              f"Kd={plateau_at:.1f}x (vs previous grid point)")

    print("\n=== Freeze decision ===")
    # Rules C/D/E all mean "stop extending Kd" -- the correct trigger is whichever
    # of them fires FIRST (smallest Kd), not whichever is checked first in code.
    # (Bug caught in initial run: checking Rule C before Rule D regardless of which
    # one actually triggers earlier picked Kd=12x, a point where load_severe was
    # already LIMIT_CYCLE -- corrected here to take the minimum trigger point.)
    stop_triggers = [x for x in (reversal_at, osc_at, relay_at) if x is not None]
    first_stop = min(stop_triggers) if stop_triggers else None
    if first_stop is not None:
        idx = mults.index(first_stop)
        freeze_mult = mults[idx - 1] if idx > 0 else None
        which = []
        if reversal_at == first_stop:
            which.append('C (reversal)')
        if osc_at == first_stop:
            which.append('D (non-STABLE)')
        if relay_at == first_stop:
            which.append('E (relay-like saturation)')
        freeze_reason = (f"Rule {'/'.join(which)} triggers at Kd={first_stop:.1f}x (earliest of all "
                          f"C/D/E triggers) -> freeze at last point STABLE in BOTH scenarios")
    elif interior_min_mult:
        freeze_mult = interior_min_mult
        freeze_reason = "Rule A (interior J_phys minimum) -> freeze at the minimum"
    elif plateau_at:
        # Rule 9: within the plateau, select the SMALLEST Kd within 1% of the best J_phys
        best_j = j_mean.min()
        within_1pct = j_mean[j_mean <= best_j * 1.01]
        freeze_mult = float(within_1pct.index.min())
        freeze_reason = "Rule B/9 (plateau) -> smallest Kd within 1% of best J_phys"
    else:
        freeze_reason = ("Rule 10: J_phys keeps improving materially through Kd=16.0x with no "
                          "pathology (no reversal, no instability, no relay-like saturation, no "
                          "plateau) -- STOPPING per explicit instruction, NOT selecting Kd* "
                          "automatically. Escalate to user.")

    print(freeze_reason)
    if freeze_mult is not None:
        print(f"\nFrozen Kd* = {freeze_mult:.1f}x = {freeze_mult*K0:.1f} MW/Hz "
              f"(Delta_f_sat = {PMAX_MW/(freeze_mult*K0)*1000:.1f} mHz)")

    # ---- Section 11: compare tuned droop (if any) vs F+R on both DESIGN probes ----
    print("\n=== F+R (Kf=586.8, Kr=220.05) vs droop grid, both DESIGN probes ===")
    fr = df[df['controller'] == 'F+R'].set_index('scenario')
    for scenario in SCENARIOS:
        label = scenario['label']
        base_nadir = abs(noffc_ref[label]['nadir'])
        base_rocof = noffc_ref[label]['rocof']
        fr_row = fr.loc[label]
        fr_if = (base_nadir - abs(fr_row['df_nadir_hz'])) / base_nadir
        fr_ir = (base_rocof - fr_row['rocof_max_hz_s']) / base_rocof
        print(f"  {label:12s} F+R:   I_f={fr_if*100:+.1f}% I_r={fr_ir*100:+.1f}% "
              f"J={fr_row['J_phys']:.4f} sat={fr_row['saturation_fraction']:.3f}")
        if freeze_mult is not None:
            d_row = droop[(droop['scenario'] == label) & (droop['k_d_mult'] == freeze_mult)].iloc[0]
            d_if = (base_nadir - abs(d_row['df_nadir_hz'])) / base_nadir
            d_ir = (base_rocof - d_row['rocof_max_hz_s']) / base_rocof
            print(f"  {label:12s} droop*: I_f={d_if*100:+.1f}% I_r={d_ir*100:+.1f}% "
                  f"J={d_row['J_phys']:.4f} sat={d_row['saturation_fraction']:.3f} "
                  f"(Kd={freeze_mult:.1f}x)")
        else:
            best_row = droop[(droop['scenario'] == label) & (droop['k_d_mult'] == 16.0)].iloc[0]
            b_if = (base_nadir - abs(best_row['df_nadir_hz'])) / base_nadir
            b_ir = (base_rocof - best_row['rocof_max_hz_s']) / base_rocof
            print(f"  {label:12s} droop@16x (NOT frozen): I_f={b_if*100:+.1f}% I_r={b_ir*100:+.1f}% "
                  f"J={best_row['J_phys']:.4f} sat={best_row['saturation_fraction']:.3f}")


if __name__ == '__main__':
    main()
