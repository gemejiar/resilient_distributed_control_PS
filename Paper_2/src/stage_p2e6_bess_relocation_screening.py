#!/usr/bin/env python
"""
P2-E6 -- BESS relocation screening (open-loop, joint across BOTH DESIGN
scenarios, not distance-only, not single-disturbance).

Step A: single-bus open-loop sensitivity (same +293.4MW step at t=TD as
P2-E5f) for EVERY technically-admissible bus (1-29), against BOTH DESIGN
scenarios (gen_severe: GENROU_4 rho=0.90; load_severe: PQ_9/bus20
alpha_L=0.50). Joint score = mean of the 4 metrics (delta_df, delta_RoCoF for
each scenario), each normalized by its own max across all 29 buses -- no
single scenario or metric dominates, and proximity to one disturbance alone
cannot win by itself.

Step B: the top-4 candidates by joint score are tested as PAIRS (all 6
combinations) using a genuine joint two-bus open-loop injection
(run_spatial_controllability_probe_multi), against both scenarios -- mirrors
the P1 Section 7.2 "4 candidates -> pair screening" methodology already
established in this project. The CURRENT pair (BESS_BUS_1=13, BESS_BUS_2=12)
is also tested with the identical dual-bus methodology for a direct,
apples-to-apples comparison.

Same Pmax per unit (293.4MW), same injection methodology, same low-inertia
case, same tstep=5ms, same metrics as P2-E5f. DESIGN scenarios only -- no
validation, no P2-T1..T12. Does NOT freeze anything by itself, does NOT
re-run P2-E5 F+R, does NOT re-evaluate STOP-P2-A -- those are explicitly
deferred to a separate authorization.
"""
import os
import sys
from itertools import combinations

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p2_common import (run_spatial_controllability_probe, run_spatial_controllability_probe_multi,
                        BESS_BUS_1, BESS_BUS_2, BESS_ADMISSIBLE_BUSES, TF_INITIAL)

PMAX_BESS_MW = 293.4
COMMAND_MW = PMAX_BESS_MW
TSTEP = 0.005
TOP_K = 4

SCENARIOS = [
    dict(label='gen_severe', kind='gen', gen='GENROU_4', rho=0.90, lambda_L=1.00),
    dict(label='load_severe', kind='load', bus=20, alpha_L=0.50, lambda_L=1.00),
]

OUT_DIAG = os.path.join('Paper_2', 'artifacts', 'diagnostics')
os.makedirs(OUT_DIAG, exist_ok=True)


def probe_kwargs(scenario):
    kwargs = dict(kind=scenario['kind'], lambda_L=scenario['lambda_L'])
    if scenario['kind'] == 'gen':
        kwargs['gen'] = scenario['gen']
        kwargs['rho'] = scenario['rho']
    else:
        kwargs['bus'] = scenario['bus']
        kwargs['alpha_L'] = scenario['alpha_L']
    return kwargs


def main():
    print("=== P2-E6 Step A: single-bus screening, all admissible buses x 2 DESIGN scenarios ===")
    noffc = {}
    for scenario in SCENARIOS:
        r0 = run_spatial_controllability_probe(test_bus=BESS_BUS_1, command_mw=0.0,
                                                p_max_bess_mw=PMAX_BESS_MW, tstep=TSTEP,
                                                tf=TF_INITIAL, **probe_kwargs(scenario))
        noffc[scenario['label']] = dict(df_nadir=r0['df_nadir_hz'], rocof_max=r0['rocof_max_hz_s'])
        print(f"  NoFFC {scenario['label']}: df_nadir={r0['df_nadir_hz']:+.4f}Hz "
              f"RoCoF_max={r0['rocof_max_hz_s']:.4f}Hz/s")

    rows = []
    for b in BESS_ADMISSIBLE_BUSES:
        row = dict(bus=b)
        for scenario in SCENARIOS:
            r = run_spatial_controllability_probe(test_bus=b, command_mw=COMMAND_MW,
                                                    p_max_bess_mw=PMAX_BESS_MW, tstep=TSTEP,
                                                    tf=TF_INITIAL, **probe_kwargs(scenario))
            label = scenario['label']
            row[f'delta_df_{label}'] = r['df_nadir_hz'] - noffc[label]['df_nadir']
            row[f'delta_rocof_{label}'] = noffc[label]['rocof_max'] - r['rocof_max_hz_s']
            row[f'tds_ok_{label}'] = bool(r['tds_success'])
        rows.append(row)
        print(f"  bus {b:3d}: "
              f"df_gen={row['delta_df_gen_severe']*1000:+6.2f}mHz rocof_gen={row['delta_rocof_gen_severe']:+.4f}Hz/s "
              f"df_load={row['delta_df_load_severe']*1000:+6.2f}mHz rocof_load={row['delta_rocof_load_severe']:+.4f}Hz/s")

    df = pd.DataFrame(rows)
    metric_cols = ['delta_df_gen_severe', 'delta_rocof_gen_severe', 'delta_df_load_severe', 'delta_rocof_load_severe']
    for c in metric_cols:
        maxval = df[c].abs().max()
        df[f'{c}_norm'] = df[c] / maxval if maxval > 1e-9 else 0.0
    df['joint_score'] = df[[f'{c}_norm' for c in metric_cols]].mean(axis=1)
    df = df.sort_values('joint_score', ascending=False).reset_index(drop=True)

    out_csv_a = os.path.join(OUT_DIAG, 'p2e6_single_bus_screening.csv')
    df.to_csv(out_csv_a, index=False)
    print(f"\nSaved: {out_csv_a}")
    print("\n=== Top candidates by joint score (mean of 4 normalized metrics) ===")
    print(df[['bus', 'joint_score'] + metric_cols].head(8).to_string(index=False))

    top4 = df['bus'].head(TOP_K).tolist()
    print(f"\nTop-{TOP_K} candidates for pair screening: {top4}")
    print(f"(for reference, current BESS_BUS_1={BESS_BUS_1} rank="
          f"{int(df.index[df['bus'] == BESS_BUS_1][0]) + 1}, "
          f"BESS_BUS_2={BESS_BUS_2} rank={int(df.index[df['bus'] == BESS_BUS_2][0]) + 1} of {len(df)})")

    print(f"\n=== P2-E6 Step B: pair screening (top-{TOP_K} candidates, all "
          f"{len(list(combinations(top4, 2)))} pairs, + current pair as baseline) ===")
    pair_rows = []
    all_pairs = list(combinations(sorted(top4), 2)) + [(min(BESS_BUS_1, BESS_BUS_2), max(BESS_BUS_1, BESS_BUS_2))]
    seen = set()
    for pair in all_pairs:
        if pair in seen:
            continue
        seen.add(pair)
        is_current = set(pair) == {BESS_BUS_1, BESS_BUS_2}
        row = dict(bus1=pair[0], bus2=pair[1], is_current_pair=is_current)
        for scenario in SCENARIOS:
            r = run_spatial_controllability_probe_multi(test_buses=list(pair), command_mw=COMMAND_MW,
                                                          p_max_bess_mw=PMAX_BESS_MW, tstep=TSTEP,
                                                          tf=TF_INITIAL, **probe_kwargs(scenario))
            label = scenario['label']
            row[f'delta_df_{label}'] = r['df_nadir_hz'] - noffc[label]['df_nadir']
            row[f'delta_rocof_{label}'] = noffc[label]['rocof_max'] - r['rocof_max_hz_s']
            row[f'tds_ok_{label}'] = bool(r['tds_success'])
        pair_rows.append(row)
        tag = ' [CURRENT PAIR]' if is_current else ''
        print(f"  ({pair[0]:3d},{pair[1]:3d}){tag}: "
              f"df_gen={row['delta_df_gen_severe']*1000:+6.2f}mHz rocof_gen={row['delta_rocof_gen_severe']:+.4f}Hz/s "
              f"df_load={row['delta_df_load_severe']*1000:+6.2f}mHz rocof_load={row['delta_rocof_load_severe']:+.4f}Hz/s")

    df_pairs = pd.DataFrame(pair_rows)
    for c in metric_cols:
        maxval = df_pairs[c].abs().max()
        df_pairs[f'{c}_norm'] = df_pairs[c] / maxval if maxval > 1e-9 else 0.0
    df_pairs['joint_score'] = df_pairs[[f'{c}_norm' for c in metric_cols]].mean(axis=1)
    df_pairs = df_pairs.sort_values('joint_score', ascending=False).reset_index(drop=True)

    out_csv_b = os.path.join(OUT_DIAG, 'p2e6_pair_screening.csv')
    df_pairs.to_csv(out_csv_b, index=False)
    print(f"\nSaved: {out_csv_b}")
    print("\n=== Pair ranking by joint score ===")
    print(df_pairs[['bus1', 'bus2', 'is_current_pair', 'joint_score'] + metric_cols].to_string(index=False))

    best = df_pairs.iloc[0]
    current = df_pairs[df_pairs['is_current_pair']].iloc[0]
    print(f"\nBest pair: ({int(best['bus1'])}, {int(best['bus2'])}) joint_score={best['joint_score']:.3f}")
    print(f"Current pair: ({int(current['bus1'])}, {int(current['bus2'])}) joint_score={current['joint_score']:.3f}")


if __name__ == '__main__':
    main()
