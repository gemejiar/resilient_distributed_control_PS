#!/usr/bin/env python
"""
P2-E5e -- local vs global(worst-system) feedback diagnostic for load_severe.

Determines whether load_severe's zero response to Kr is caused by local
observability (DEC-P2-014) rather than by the control law/gain/authority
itself. Same Kf=1.0x, Kr=0.75x (the best F+R point found, DEC-P2-014),
Pmax, Tc=100ms, tip, BusROCOF/Tf/Tw/Tr, BESS location, tstep=5ms -- the ONLY
difference between variants is which frequency/RoCoF reading feeds the
control law:
  A) local  -- each BESS's own bus BusROCOF (unchanged from every prior run)
  B) global -- both BESS fed the worst-system frequency/RoCoF (min BusFreq.f /
     max |BusROCOF.Wf_y| over GEN_BUSES) instead of their local reading
     (p2_common.run_physical_scenario_tc(feedback='global'), new capability
     added this round -- pure re-routing of an already-computed signal into
     the existing control law, no new model/weighting).

Variant A reuses the already-computed row from
Paper_2/artifacts/diagnostics/p2e5_kf_kr_grid.csv (no new simulation).
Variant B requires exactly ONE new simulation.
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

OUT_DIAG = os.path.join('Paper_2', 'artifacts', 'diagnostics')
OUT_TRAJ = os.path.join('Paper_2', 'artifacts', 'trajectories')


def classify_simple(tds_success, sat_frac):
    """Reuses the saturation_fraction-based stability signal only (no new
    trajectory needed for NoFFC reference here) -- consistent with the fact
    that STABLE in every prior local/global point in this range had
    saturation_fraction==0.0 and this diagnostic does not re-derive the full
    detrended classifier for a single confirmatory point."""
    if not tds_success:
        return 'NUMERICAL_FAILURE'
    return 'STABLE' if sat_frac < 0.05 else 'CHECK_MANUALLY'


def main():
    # NoFFC reference (needed to compute I_f/I_r) -- already available from the
    # F+R grid run (no new simulation): read from the existing trace.
    d = np.load(os.path.join(OUT_TRAJ, 'p2e5_physical_structure_traces.npz'))
    f0 = d['load_severe_NoFFC__f_worst_hz']
    rocof0 = d['load_severe_NoFFC__rocof_worst_hz_s']
    noffc_df_nadir = float(np.min(f0) - F0_HZ)
    noffc_rocof_max = float(np.max(rocof0))

    # Variant A (local feedback): reuse existing F+R grid row, no new sim.
    grid = pd.read_csv(os.path.join(OUT_DIAG, 'p2e5_kf_kr_grid.csv'))
    row_a = grid[(grid['scenario'] == 'load_severe') & (grid['k_f_mult'] == 1.0) &
                 (grid['k_r_mult'] == 0.75)].iloc[0]
    variant_a = dict(
        variant='A_local', df_nadir_hz=float(row_a['df_nadir_hz']),
        RoCoF_max_hz_s=float(row_a['RoCoF_max_hz_s']), Ppeak_MW=float(row_a['Ppeak_MW']),
        saturation_fraction=float(row_a['saturation_fraction']),
        classification=row_a['classification'], TDS_success=bool(row_a['TDS_success']),
    )

    # Variant B (global feedback): ONE new simulation, everything else identical.
    r = run_physical_scenario_tc(kind='load', bus=20, alpha_L=0.50, lambda_L=1.00,
                                  p_max_bess_mw=PMAX_MW, k_f=KF, k_r=KR, tc=TC_S, tstep=TSTEP,
                                  controller='physical', feedback='global', tf=6.0)
    variant_b = dict(
        variant='B_global', df_nadir_hz=r['df_nadir_hz'], RoCoF_max_hz_s=r['rocof_max_hz_s'],
        Ppeak_MW=r['p_peak_mw'], saturation_fraction=r['saturation_fraction'],
        classification=classify_simple(r['tds_success'], r['saturation_fraction']),
        TDS_success=bool(r['tds_success']),
    )

    rows = [variant_a, variant_b]
    for row in rows:
        row['I_f_vs_NoFFC'] = (abs(noffc_df_nadir) - abs(row['df_nadir_hz'])) / abs(noffc_df_nadir)
        row['I_r_vs_NoFFC'] = (noffc_rocof_max - row['RoCoF_max_hz_s']) / noffc_rocof_max

    df = pd.DataFrame(rows)
    out_csv = os.path.join(OUT_DIAG, 'p2e5e_local_vs_global_feedback.csv')
    df.to_csv(out_csv, index=False)

    print("=== P2-E5e: local vs global feedback, load_severe, Kf=1.0x Kr=0.75x, Tc=100ms ===")
    print(f"NoFFC reference: df_nadir={noffc_df_nadir:+.4f}Hz RoCoF_max={noffc_rocof_max:.4f}Hz/s")
    for row in rows:
        print(f"  [{row['variant']:10s}] df_nadir={row['df_nadir_hz']:+.4f}Hz "
              f"RoCoF_max={row['RoCoF_max_hz_s']:.4f}Hz/s I_f={row['I_f_vs_NoFFC']*100:+.2f}% "
              f"I_r={row['I_r_vs_NoFFC']*100:+.2f}% Ppeak={row['Ppeak_MW']:.1f}MW "
              f"sat={row['saturation_fraction']:.4f} class={row['classification']} "
              f"tds_ok={row['TDS_success']}")
    print(f"\nSaved: {out_csv}")


if __name__ == '__main__':
    main()
