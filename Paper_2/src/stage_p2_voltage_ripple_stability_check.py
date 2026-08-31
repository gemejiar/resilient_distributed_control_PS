#!/usr/bin/env python
"""
Single diagnostic authorized after DEC-P2-022: verify whether the low-amplitude
voltage ripple visible in F02/F10s (load_severe, F+R(16,20), Tc=tstep=5ms) --
growing slightly toward the end of the original tf=6.0s window and absent in
NoFFC -- is bounded/decaying or genuinely growing, by extending the simulation
horizon well past the original window. Touches STOP-P2-A Criterion 2
("estabilidad numerica, sin oscilacion sostenida").

Runs ONLY load_severe (the scenario where the ripple was observed), NoFFC and
F+R(16,20), same frozen config as DEC-P2-020/021 (Kf=586.8, Kr=220.05,
Pmax=293.4MW, buses 16/20, Tc=tstep=5ms), with tf extended from 6.0s to 20.0s.
Writes a NEW CSV/npz (does not overwrite the original figure trajectories).

No sweep, no tuning, no TD3, no validation, no P2-T*.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p2_common import run_physical_scenario_tc, TD

PMAX_MW = 293.4
KF0 = PMAX_MW / 0.5
KR0 = PMAX_MW / 1.0
KF = 1.0 * KF0
KR = 0.75 * KR0
TSTEP = 0.005
TC_S = TSTEP
TF_EXTENDED = 20.0

OUT_DIAG = os.path.join('Paper_2', 'artifacts', 'diagnostics')
OUT_TRAJ = os.path.join('Paper_2', 'artifacts', 'trajectories')
os.makedirs(OUT_DIAG, exist_ok=True)
os.makedirs(OUT_TRAJ, exist_ok=True)

SCEN = dict(kind='load', bus=20, alpha_L=0.50, lambda_L=1.00)


def peak_to_peak_windows(t, v_mpu, window_s=1.0):
    """Peak-to-peak amplitude of the (already event-referenced) voltage
    signal in successive non-overlapping windows, to see if amplitude grows,
    shrinks, or stays flat over the extended horizon."""
    rows = []
    t0 = TD
    n_windows = int(np.floor((t[-1] - t0) / window_s))
    for i in range(n_windows):
        w0, w1 = t0 + i * window_s, t0 + (i + 1) * window_s
        mask = (t >= w0) & (t < w1)
        if mask.sum() < 2:
            continue
        seg = v_mpu[mask]
        rows.append(dict(window_start_s=w0 - TD, window_end_s=w1 - TD,
                          v_ptp_mpu=float(seg.max() - seg.min())))
    return pd.DataFrame(rows)


def main():
    print("Running load_severe NoFFC (tf=20s) ...")
    r_noffc = run_physical_scenario_tc(p_max_bess_mw=PMAX_MW, k_f=0.0, k_r=0.0, tc=TC_S,
                                        tstep=TSTEP, controller='no_ffc',
                                        bess_bus1=16, bess_bus2=20, tf=TF_EXTENDED, **SCEN)
    print("Running load_severe F+R(16,20) (tf=20s) ...")
    r_fr = run_physical_scenario_tc(p_max_bess_mw=PMAX_MW, k_f=KF, k_r=KR, tc=TC_S,
                                     tstep=TSTEP, controller='physical',
                                     bess_bus1=16, bess_bus2=20, tf=TF_EXTENDED, **SCEN)

    print(f"NoFFC TDS_success={r_noffc['tds_success']}  F+R TDS_success={r_fr['tds_success']}")

    out_npz = os.path.join(OUT_TRAJ, 'p2_voltage_ripple_stability_check_traces.npz')
    flat = {}
    for tag, r in [('noffc', r_noffc), ('fr', r_fr)]:
        for name in ['t', 'v_bess1_pu', 'v_bess2_pu', 'theta_bess1_rad', 'theta_bess2_rad',
                     'f_worst_hz', 'rocof_worst_hz_s', 'p_command1_mw', 'p_command2_mw',
                     'p_delivered1_mw', 'p_delivered2_mw']:
            flat[f'{tag}__{name}'] = r[name]
    np.savez_compressed(out_npz, **flat)
    print(f"Saved: {out_npz}")

    dfs = []
    for tag, r in [('NoFFC', r_noffc), ('F+R', r_fr)]:
        t = r['t']
        for bus_tag, v_key in [('bus16', 'v_bess1_pu'), ('bus20', 'v_bess2_pu')]:
            v0 = r[v_key][0]
            v_mpu = (r[v_key] - v0) * 1000.0
            df = peak_to_peak_windows(t, v_mpu, window_s=1.0)
            df['controller'] = tag
            df['bus'] = bus_tag
            dfs.append(df)
    df_all = pd.concat(dfs, ignore_index=True)
    out_csv = os.path.join(OUT_DIAG, 'p2_voltage_ripple_stability_check.csv')
    df_all.to_csv(out_csv, index=False)
    print(f"Saved: {out_csv}")
    print(df_all.to_string(index=False))

    print("\n--- Trend check: last window vs peak window amplitude, per controller/bus ---")
    for (ctrl, bus), g in df_all.groupby(['controller', 'bus']):
        g = g.sort_values('window_start_s')
        peak_amp = g['v_ptp_mpu'].max()
        peak_win = g.loc[g['v_ptp_mpu'].idxmax(), 'window_start_s']
        last_amp = g['v_ptp_mpu'].iloc[-1]
        last_win = g['window_start_s'].iloc[-1]
        trend = 'GROWING' if last_amp > peak_amp * 0.8 and last_win > peak_win + 2 else 'DECAYING/BOUNDED'
        print(f"{ctrl:6s} {bus:6s}  peak={peak_amp:7.3f} mpu @ t={peak_win:5.1f}s   "
              f"last={last_amp:7.3f} mpu @ t={last_win:5.1f}s   -> {trend}")


if __name__ == '__main__':
    main()
