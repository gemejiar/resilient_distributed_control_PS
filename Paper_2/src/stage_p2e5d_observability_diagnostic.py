#!/usr/bin/env python
"""
P2-E5d -- load_severe observability diagnostic (local BESS RoCoF vs
worst-system RoCoF). No new simulations: reuses the lowest-gain F+R grid
trace already computed in Paper_2/artifacts/trajectories/p2e5_fr_grid_traces.npz
(Kf=0.1x, Kr=0.05x -- closest to an unforced reference; load_severe showed
0% I_f/I_r across the ENTIRE F+R grid, so any grid point is representative of
the underlying local/global RoCoF relationship for this disturbance).

No controller/gain/Pmax/Tc/filter/BESS-location changes. No new Kf/Kr or Pmax
sweep. RoCoF_COI is NOT computed here -- it is not implemented anywhere in
the current P2 codebase (grep-verified) and would require a new model
addition (H-weighted combination across GEN_BUSES), which this diagnostic is
explicitly not authorized to add.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from p2_common import TD

OUT_DIAG = os.path.join('Paper_2', 'artifacts', 'diagnostics')
TRAJ = os.path.join('Paper_2', 'artifacts', 'trajectories', 'p2e5_fr_grid_traces.npz')


def main():
    d = np.load(TRAJ)
    key = 'load_severe_FR_f0.1_r0.05'
    t = d[f'{key}__t']
    rocof_sys = d[f'{key}__rocof_worst_hz_s']
    rocof_b13 = np.abs(d[f'{key}__rocof_bess1_hz_s'])  # BESS_BUS_1 = 13
    rocof_b12 = np.abs(d[f'{key}__rocof_bess2_hz_s'])  # BESS_BUS_2 = 12

    window = (t >= TD - 0.1) & (t <= TD + 2.0)
    tw = t[window]
    sys_w = rocof_sys[window]
    b13_w = rocof_b13[window]
    b12_w = rocof_b12[window]

    def peak_info(x):
        i = int(np.argmax(x))
        return float(x[i]), float(tw[i])

    peak_sys, t_peak_sys = peak_info(sys_w)
    peak_b13, t_peak_b13 = peak_info(b13_w)
    peak_b12, t_peak_b12 = peak_info(b12_w)

    def correlation(a, b):
        return float(np.corrcoef(a, b)[0, 1])

    corr_b13 = correlation(b13_w, sys_w)
    corr_b12 = correlation(b12_w, sys_w)

    def lag_via_xcorr(a, b, dt):
        """Lag (s) that maximizes cross-correlation of a relative to b.
        Positive = a lags behind b (a peaks later)."""
        a0 = a - np.mean(a)
        b0 = b - np.mean(b)
        xcorr = np.correlate(a0, b0, mode='full')
        lags = np.arange(-len(a0) + 1, len(a0)) * dt
        return float(lags[int(np.argmax(xcorr))])

    dt = float(np.median(np.diff(tw)))
    lag_b13 = lag_via_xcorr(b13_w, sys_w, dt)
    lag_b12 = lag_via_xcorr(b12_w, sys_w, dt)

    print(f"=== P2-E5d: load_severe observability diagnostic (reference trace: {key}) ===")
    print(f"Peak worst-system RoCoF : {peak_sys:.4f} Hz/s at t={t_peak_sys:.3f}s (t-TD={t_peak_sys - TD:.3f}s)")
    print(f"Peak local RoCoF bus 13 : {peak_b13:.4f} Hz/s at t={t_peak_b13:.3f}s (t-TD={t_peak_b13 - TD:.3f}s) "
          f"-- ratio local/global = {peak_b13 / peak_sys:.3f}")
    print(f"Peak local RoCoF bus 12 : {peak_b12:.4f} Hz/s at t={t_peak_b12:.3f}s (t-TD={t_peak_b12 - TD:.3f}s) "
          f"-- ratio local/global = {peak_b12 / peak_sys:.3f}")
    print(f"\nCorrelation (Pearson, full window) bus13 vs system: {corr_b13:.3f}")
    print(f"Correlation (Pearson, full window) bus12 vs system: {corr_b12:.3f}")
    print(f"\nCross-correlation lag bus13 vs system: {lag_b13*1000:+.1f} ms "
          f"({'local lags global' if lag_b13 > 0 else 'local leads global' if lag_b13 < 0 else 'no lag'})")
    print(f"Cross-correlation lag bus12 vs system: {lag_b12*1000:+.1f} ms "
          f"({'local lags global' if lag_b12 > 0 else 'local leads global' if lag_b12 < 0 else 'no lag'})")
    print("\nRoCoF_COI: NOT AVAILABLE -- not implemented anywhere in the P2 codebase; would require a new "
          "H-weighted model addition, not authorized in this diagnostic.")

    import csv
    out_csv = os.path.join(OUT_DIAG, 'p2e5d_observability_diagnostic.csv')
    with open(out_csv, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['signal', 'peak_rocof_hz_s', 't_peak_s', 't_peak_minus_TD_s', 'ratio_to_system',
                     'correlation_to_system', 'lag_vs_system_ms'])
        w.writerow(['worst_system', peak_sys, t_peak_sys, t_peak_sys - TD, 1.0, 1.0, 0.0])
        w.writerow(['local_bess_bus13', peak_b13, t_peak_b13, t_peak_b13 - TD, peak_b13 / peak_sys,
                     corr_b13, lag_b13 * 1000])
        w.writerow(['local_bess_bus12', peak_b12, t_peak_b12, t_peak_b12 - TD, peak_b12 / peak_sys,
                     corr_b12, lag_b12 * 1000])
    print(f"\nSaved: {out_csv}")


if __name__ == '__main__':
    main()
