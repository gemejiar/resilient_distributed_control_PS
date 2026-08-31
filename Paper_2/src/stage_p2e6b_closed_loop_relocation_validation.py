#!/usr/bin/env python
"""
P2-E6b -- closed-loop validation of BESS relocation candidates.

Real Kf/Kr feedback controller (NOT the open-loop probe used for screening,
P2-E6/DEC-P2-017) at the two candidates authorized for testing: (16,24) and
(16,20), against BOTH DESIGN scenarios (gen_severe, load_severe). Same Kf,
Kr, Pmax, Tc=100ms, tstep=5ms as the best-known F+R point (DEC-P2-014:
Kf=1.0x, Kr=0.75x) -- no retuning. Current pair (12,13) reused from the
already-computed p2e5_kf_kr_grid.csv row at the identical Kf/Kr point -- no
new simulation needed for the baseline.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p2_common import run_physical_scenario_tc, F0_HZ

PMAX_MW = 293.4
KF0 = PMAX_MW / 0.5
KR0 = PMAX_MW / 1.0
KF = 1.0 * KF0
KR = 0.75 * KR0
TC_S = 0.100
TSTEP = 0.005
TF = 6.0

SCENARIOS = [
    dict(label='gen_severe', kind='gen', gen='GENROU_4', rho=0.90, lambda_L=1.00),
    dict(label='load_severe', kind='load', bus=20, alpha_L=0.50, lambda_L=1.00),
]

PAIRS_TO_TEST = [(16, 24), (16, 20)]

OUT_DIAG = os.path.join('Paper_2', 'artifacts', 'diagnostics')
os.makedirs(OUT_DIAG, exist_ok=True)

NOFFC_REF = {
    'gen_severe': dict(df_nadir=-0.18117025597484826, rocof_max=1.1852609765445359),
    'load_severe': dict(df_nadir=-0.2083094810780466, rocof_max=2.933356509159679),
}


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
    rows = []

    # Baseline (12,13): reused from p2e5_kf_kr_grid.csv, identical Kf=1.0x/Kr=0.75x point.
    grid = pd.read_csv(os.path.join(OUT_DIAG, 'p2e5_kf_kr_grid.csv'))
    for scenario in SCENARIOS:
        row_ref = grid[(grid['scenario'] == scenario['label']) & (grid['k_f_mult'] == 1.0) &
                        (grid['k_r_mult'] == 0.75)].iloc[0]
        rows.append(dict(
            bus1=13, bus2=12, pair_label='(12,13) current', scenario=scenario['label'],
            df_nadir_hz=float(row_ref['df_nadir_hz']), RoCoF_max_hz_s=float(row_ref['RoCoF_max_hz_s']),
            saturation_fraction=float(row_ref['saturation_fraction']),
            classification=row_ref['classification'], TDS_success=bool(row_ref['TDS_success']),
        ))

    print(f"=== P2-E6b: closed-loop F+R validation, Kf={KF:.1f} Kr={KR:.1f} Tc=100ms tstep=5ms ===")
    for pair in PAIRS_TO_TEST:
        for scenario in SCENARIOS:
            r = run_physical_scenario_tc(p_max_bess_mw=PMAX_MW, k_f=KF, k_r=KR, tc=TC_S, tstep=TSTEP,
                                          controller='physical', bess_bus1=pair[0], bess_bus2=pair[1],
                                          tf=TF, **probe_kwargs(scenario))
            rows.append(dict(
                bus1=pair[0], bus2=pair[1], pair_label=f'{pair}', scenario=scenario['label'],
                df_nadir_hz=r['df_nadir_hz'], RoCoF_max_hz_s=r['rocof_max_hz_s'],
                saturation_fraction=r['saturation_fraction'],
                classification='STABLE' if r['saturation_fraction'] < 0.05 and r['tds_success'] else 'CHECK',
                TDS_success=bool(r['tds_success']),
            ))

    df = pd.DataFrame(rows)
    for scenario in SCENARIOS:
        label = scenario['label']
        base_f = NOFFC_REF[label]['df_nadir']
        base_r = NOFFC_REF[label]['rocof_max']
        mask = df['scenario'] == label
        df.loc[mask, 'I_f_vs_NoFFC'] = (np.abs(base_f) - np.abs(df.loc[mask, 'df_nadir_hz'])) / np.abs(base_f)
        df.loc[mask, 'I_r_vs_NoFFC'] = (base_r - df.loc[mask, 'RoCoF_max_hz_s']) / base_r

    out_csv = os.path.join(OUT_DIAG, 'p2e6b_closed_loop_relocation_validation.csv')
    df.to_csv(out_csv, index=False)

    print(df[['pair_label', 'scenario', 'I_f_vs_NoFFC', 'I_r_vs_NoFFC', 'saturation_fraction',
              'classification', 'TDS_success']].to_string(index=False))
    print(f"\nSaved: {out_csv}")

    print("\n=== Per-pair summary (min I_f, min I_r across both scenarios -- worst-case robustness) ===")
    for pair_label in df['pair_label'].unique():
        sub = df[df['pair_label'] == pair_label]
        print(f"  {pair_label}: min(I_f)={sub['I_f_vs_NoFFC'].min()*100:+.2f}% "
              f"min(I_r)={sub['I_r_vs_NoFFC'].min()*100:+.2f}% "
              f"max(sat)={sub['saturation_fraction'].max():.4f} "
              f"all_stable={bool((sub['classification'] == 'STABLE').all())}")


if __name__ == '__main__':
    main()
