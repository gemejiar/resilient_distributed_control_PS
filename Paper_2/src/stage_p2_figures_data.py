#!/usr/bin/env python
"""
Paper_2 figure package -- data generation.

Runs the DESIGN simulations needed for the P2_F01-F10 figure package: NoFFC,
F+R (frozen Kf/Kr, Tc=100ms) at the current BESS pair (16,20) and at the two
historical pairs (12,13 and 16,24) for comparison figures, and one open-loop
positive-injection case for load_severe. All at tstep=5ms, tf=6.0s, using
p2_common.run_physical_scenario_tc() with the newly added full instrumentation
(bus voltage/angle at BESS POI and system-wide, per-generator-bus frequency/
RoCoF arrays, COI-proxy frequency).

No sweep, no tuning, no TD3, no validation, no P2-T*. Only DESIGN scenarios
(gen_severe, load_severe).
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p2_common import run_physical_scenario_tc, TD, F0_HZ, GEN_BUSES

PMAX_MW = 293.4
KF0 = PMAX_MW / 0.5
KR0 = PMAX_MW / 1.0
KF = 1.0 * KF0
KR = 0.75 * KR0
TSTEP = 0.005
TC_S = TSTEP  # DEC-P2-020: continuous re-evaluation each computation cycle (was 0.100s / Tc=100ms)
TF = 6.0

SCENARIOS = {
    'gen_severe': dict(kind='gen', gen='GENROU_4', rho=0.90, lambda_L=1.00),
    'load_severe': dict(kind='load', bus=20, alpha_L=0.50, lambda_L=1.00),
}

BESS_PAIRS = {
    '16_20': (16, 20),   # current, frozen (DEC-P2-018)
    '12_13': (12, 13),   # original P1/P2-E1 placement
    '16_24': (16, 24),   # robust open-loop candidate (superseded)
}

OUT_TRAJ = os.path.join('Paper_2', 'artifacts', 'trajectories', 'figures')
OUT_DIAG = os.path.join('Paper_2', 'figures_main')
os.makedirs(OUT_TRAJ, exist_ok=True)
os.makedirs(OUT_DIAG, exist_ok=True)


def run_all():
    runs = {}

    for scen_label, scen in SCENARIOS.items():
        # NoFFC (BESS pair doesn't matter -- zero command everywhere; use current pair)
        key = f'{scen_label}__NoFFC'
        print(f"Running {key} ...")
        runs[key] = run_physical_scenario_tc(p_max_bess_mw=PMAX_MW, k_f=0.0, k_r=0.0, tc=TC_S,
                                              tstep=TSTEP, controller='no_ffc',
                                              bess_bus1=16, bess_bus2=20, tf=TF, **scen)

        for pair_label, (b1, b2) in BESS_PAIRS.items():
            key = f'{scen_label}__FR_{pair_label}'
            print(f"Running {key} ...")
            runs[key] = run_physical_scenario_tc(p_max_bess_mw=PMAX_MW, k_f=KF, k_r=KR, tc=TC_S,
                                                  tstep=TSTEP, controller='physical',
                                                  bess_bus1=b1, bess_bus2=b2, tf=TF, **scen)

    # Open-loop positive injection, load_severe only, current pair (16,20) -- matches P2-E7 Case C
    key = 'load_severe__OpenLoop_16_20'
    print(f"Running {key} ...")
    runs[key] = run_physical_scenario_tc(p_max_bess_mw=PMAX_MW, k_f=0.0, k_r=0.0, tc=TC_S,
                                          tstep=TSTEP, controller='open_loop_fixed',
                                          open_loop_command_mw=PMAX_MW,
                                          bess_bus1=16, bess_bus2=20, tf=TF, **SCENARIOS['load_severe'])

    return runs


def first_nonzero_command_time(t, pc1, pc2, eps=1e-6):
    combined = np.abs(pc1) + np.abs(pc2)
    idx = np.where((t >= TD) & (combined > eps))[0]
    return float(t[idx[0]]) if len(idx) else float('nan')


def build_metadata(runs):
    rows = []
    for key, r in runs.items():
        scenario, tag = key.split('__', 1)
        if tag == 'NoFFC':
            controller, buses = 'NoFFC', '16_20'
        elif tag.startswith('FR_'):
            controller, buses = 'F+R', tag[3:]
        else:
            controller, buses = 'OpenLoop', tag.split('_', 1)[1]

        t = r['t']
        f_worst = r['f_worst_hz']
        rocof_worst = r['rocof_worst_hz_s']
        i_nadir = int(np.argmin(f_worst))
        i_rocof_peak = int(np.argmax(rocof_worst))

        # which GEN_BUS is "responsible" for the nadir / RoCoF peak
        f_gen_all = r['f_gen_all_hz']
        rocof_gen_all = r['rocof_gen_all_hz_s']
        worst_f_bus = int(GEN_BUSES[int(np.argmin(f_gen_all[i_nadir]))])
        worst_rocof_bus = int(GEN_BUSES[int(np.argmax(np.abs(rocof_gen_all[i_rocof_peak])))])

        first_cmd_t = first_nonzero_command_time(t, r['p_command1_mw'], r['p_command2_mw'])

        rows.append(dict(
            scenario=scenario, controller=controller, bess_buses=buses,
            event_time_s=TD, nadir_value_hz=float(f_worst[i_nadir]), nadir_time_s=float(t[i_nadir]),
            rocof_max_hz_s=float(rocof_worst[i_rocof_peak]), rocof_max_time_s=float(t[i_rocof_peak]),
            first_command_time_s=first_cmd_t,
            ppeak_bess1_mw=float(np.max(np.abs(r['p_delivered1_mw']))),
            ppeak_bess2_mw=float(np.max(np.abs(r['p_delivered2_mw']))),
            worst_frequency_bus_at_nadir=worst_f_bus, worst_rocof_bus_at_peak=worst_rocof_bus,
            TDS_success=bool(r['tds_success']),
        ))
    return pd.DataFrame(rows)


def main():
    runs = run_all()

    out_npz = os.path.join(OUT_TRAJ, 'p2_figures_trajectories.npz')
    flat = {}
    for key, r in runs.items():
        for name in ['t', 'f_worst_hz', 'rocof_worst_hz_s', 'f_coi_hz',
                     'p_command1_mw', 'p_command2_mw', 'p_delivered1_mw', 'p_delivered2_mw',
                     'action_step_indices', 'v_bess1_pu', 'theta_bess1_rad',
                     'v_bess2_pu', 'theta_bess2_rad', 'v_all_pu', 'theta_all_rad', 'all_bus_idx',
                     'f_gen_all_hz', 'rocof_gen_all_hz_s', 'gen_buses',
                     'f_bess1_hz', 'rocof_bess1_hz_s', 'f_bess2_hz', 'rocof_bess2_hz_s']:
            flat[f'{key}__{name}'] = r[name]
    np.savez_compressed(out_npz, **flat)
    print(f"\nSaved: {out_npz} ({len(runs)} runs)")

    df_meta = build_metadata(runs)
    out_csv = os.path.join(OUT_DIAG, 'figure_metadata.csv')
    df_meta.to_csv(out_csv, index=False)
    print(f"Saved: {out_csv}")
    print(df_meta.to_string(index=False))


if __name__ == '__main__':
    main()
