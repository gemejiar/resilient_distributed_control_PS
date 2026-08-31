#!/usr/bin/env python
"""
P2-E5c -- tstep (integration step) convergence check on the exact F+R
aggressive case that showed numerical sensitivity (DEC-P2-012).

Same Tc=100ms, Kf=Kr=1.0x, Pmax=293.4MW, tip, BusROCOF/Tf/Tw/Tr, disturbance
(load_severe: PQ_9/bus20, alpha_L=0.50, lambda_L=1.00) -- ONLY tstep varies:
{10, 5, 2.5, 1} ms. Convergence criterion: <~1% relative change in the main
metrics (df_nadir, RoCoF_max, Ppeak, saturation_fraction) between two
successive refinements.

Does NOT touch Tc/Kf/Kr/Pmax/tip/filters, does NOT train TD3, does NOT use
validation or P2-T*, does NOT build the F+R grid.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p2_common import run_physical_scenario_tc

PMAX_MW = 293.4
KF0 = PMAX_MW / 0.5
KR0 = PMAX_MW / 1.0
TC_S = 0.100
TSTEPS_MS = [10.0, 5.0, 2.5, 1.0]

OUT_DIAG = os.path.join('Paper_2', 'artifacts', 'diagnostics')
os.makedirs(OUT_DIAG, exist_ok=True)


def main():
    rows = []
    print("=== P2-E5c: tstep convergence, F+R aggressive case (Kf=Kr=1.0x, Tc=100ms, load_severe) ===")
    for tstep_ms in TSTEPS_MS:
        r = run_physical_scenario_tc(kind='load', bus=20, alpha_L=0.50, lambda_L=1.00,
                                      p_max_bess_mw=PMAX_MW, k_f=1.0 * KF0, k_r=1.0 * KR0,
                                      tc=TC_S, tstep=tstep_ms / 1000.0, controller='physical', tf=6.0)
        row = dict(tstep_ms=tstep_ms, df_nadir_hz=r['df_nadir_hz'], RoCoF_max_hz_s=r['rocof_max_hz_s'],
                   Ppeak_MW=r['p_peak_mw'], saturation_fraction=r['saturation_fraction'],
                   TDS_success=bool(r['tds_success']), runtime_s=r['runtime_seconds'])
        rows.append(row)
        print(f"  tstep={tstep_ms:5.2f}ms: df_nadir={row['df_nadir_hz']:+.4f}Hz "
              f"RoCoF_max={row['RoCoF_max_hz_s']:.4f}Hz/s Ppeak={row['Ppeak_MW']:.1f}MW "
              f"sat={row['saturation_fraction']:.4f} tds_ok={row['TDS_success']} "
              f"runtime={row['runtime_s']:.1f}s")

    df = pd.DataFrame(rows).sort_values('tstep_ms', ascending=False).reset_index(drop=True)

    # Relative error between successive refinements (coarser -> finer), i.e.
    # row i vs row i+1 (finer). Denominator = finer value (the better estimate).
    metrics = ['df_nadir_hz', 'RoCoF_max_hz_s', 'Ppeak_MW', 'saturation_fraction']
    print("\n=== Relative change between successive refinements ===")
    rel_rows = []
    for i in range(len(df) - 1):
        coarse = df.iloc[i]
        fine = df.iloc[i + 1]
        rel = {}
        for m in metrics:
            denom = abs(fine[m]) if abs(fine[m]) > 1e-6 else 1e-6
            rel[m] = abs(coarse[m] - fine[m]) / denom * 100.0
        rel_rows.append(dict(from_tstep_ms=coarse['tstep_ms'], to_tstep_ms=fine['tstep_ms'], **rel))
        print(f"  {coarse['tstep_ms']:.2f}ms -> {fine['tstep_ms']:.2f}ms: "
              + ", ".join(f"{m}={rel[m]:.2f}%" for m in metrics))

    df_rel = pd.DataFrame(rel_rows)

    out_csv = os.path.join(OUT_DIAG, 'p2e5c_tstep_convergence.csv')
    df.to_csv(out_csv, index=False)
    out_csv_rel = os.path.join(OUT_DIAG, 'p2e5c_tstep_convergence_relative_error.csv')
    df_rel.to_csv(out_csv_rel, index=False)
    print(f"\nSaved: {out_csv}")
    print(f"Saved: {out_csv_rel}")

    # Convergence determination: first refinement step (going finer) where ALL
    # four metrics change by <1% relative to the next-finer step.
    converged_tstep = None
    for _, rel_row in df_rel.iterrows():
        if all(rel_row[m] < 1.0 for m in metrics):
            converged_tstep = rel_row['to_tstep_ms']
            break
    print(f"\nFirst tstep (from finer side) where ALL metrics change <1% vs next refinement: "
          f"{converged_tstep} ms" if converged_tstep is not None else
          "\nNo pair of successive refinements achieved <1% change on ALL metrics within the tested range.")


if __name__ == '__main__':
    main()
