#!/usr/bin/env python
"""
P2-E11 -- validation-split comparison: NoFFC, droop* (Kd*=4694.4MW/Hz,
DEC-P2-024), and each of the 5 frozen TD3 checkpoints (DEC-P2-035/036),
evaluated on the SAME 6 validation scenarios used throughout P2-E9. This is
a PREVIEW of success on validation -- explicitly NOT the plan's final gate
(SS21), which requires P2-T1..T12 (not opened here).

Per (controller, scenario): df_peak, RoCoF_peak, J_val_P2 (SS7), plus
I_f/I_r relative to droop* (SS21 formula, computed here only as a
validation-split preview, not a gate verdict).
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p2_env_train import P2ResidualTrainEnv, VALIDATION_SCENARIOS, F_REF_HZ, R_REF_HZ_S
from stable_baselines3 import TD3

PMAX_MW = 293.4
KD_STAR = 4694.4
P_RL_MAX_MW = 73.35
TC = TSTEP = 0.005
BESS_BUS1, BESS_BUS2 = 16, 20

SEED_CHECKPOINTS = {
    11: 'seed11_ep400',
    22: 'seed22_ep1600',
    33: 'seed33_ep400',
    44: 'seed44_ep600',
    55: 'seed55_ep1400',
}
CKPT_DIR = os.path.join('Paper_2', 'artifacts', 'models', 'p2e9_seeds')
OUT_DIAG = os.path.join('Paper_2', 'artifacts', 'diagnostics')


def make_env(scen, kd_star, p_rl_max):
    return P2ResidualTrainEnv(obs_mode='OBS-A', p_max_bess_mw=PMAX_MW, kd_star_mw_per_hz=kd_star,
                               p_rl_max_mw=p_rl_max, tc=TC, tstep=TSTEP,
                               bess_bus1=BESS_BUS1, bess_bus2=BESS_BUS2, fixed_scenario=scen)


def run_fixed_action(scen, kd_star, action):
    env = make_env(scen, kd_star, P_RL_MAX_MW)
    obs, info = env.reset()
    terminated = truncated = False
    while not (terminated or truncated):
        obs, reward, terminated, truncated, info = env.step(action)
    return info['df_peak'], info['rocof_peak'], info['tds_success']


def run_policy(scen, model):
    env = make_env(scen, KD_STAR, P_RL_MAX_MW)
    obs, info = env.reset()
    terminated = truncated = False
    sat_count = action_count = 0
    while not (terminated or truncated):
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        action_count += 1
        if (abs(info['p_total_mw'][0]) >= PMAX_MW - 1e-3 or abs(info['p_total_mw'][1]) >= PMAX_MW - 1e-3):
            sat_count += 1
    return info['df_peak'], info['rocof_peak'], info['tds_success'], sat_count / max(action_count, 1)


def j_val(df_peak, rocof_peak):
    return (max(df_peak / F_REF_HZ, rocof_peak / R_REF_HZ_S) +
            0.25 * (df_peak / F_REF_HZ + rocof_peak / R_REF_HZ_S))


def main():
    rows = []

    print("=== NoFFC ===")
    for scen in VALIDATION_SCENARIOS:
        df_peak, rocof_peak, tds_ok = run_fixed_action(scen, kd_star=0.0, action=[0.0, 0.0])
        rows.append(dict(controller='NoFFC', scenario=str(scen), df_peak_hz=df_peak,
                          rocof_peak_hz_s=rocof_peak, J_val=j_val(df_peak, rocof_peak),
                          TDS_success=tds_ok, saturation_fraction=0.0))
        print(f"  {str(scen):70s} df_peak={df_peak:.4f}Hz RoCoF_peak={rocof_peak:.3f}Hz/s")

    print("\n=== droop* (Kd*=4694.4MW/Hz) ===")
    for scen in VALIDATION_SCENARIOS:
        df_peak, rocof_peak, tds_ok = run_fixed_action(scen, kd_star=KD_STAR, action=[0.0, 0.0])
        rows.append(dict(controller='droop_star', scenario=str(scen), df_peak_hz=df_peak,
                          rocof_peak_hz_s=rocof_peak, J_val=j_val(df_peak, rocof_peak),
                          TDS_success=tds_ok, saturation_fraction=0.0))
        print(f"  {str(scen):70s} df_peak={df_peak:.4f}Hz RoCoF_peak={rocof_peak:.3f}Hz/s")

    for seed, ckpt_name in SEED_CHECKPOINTS.items():
        print(f"\n=== seed {seed} ({ckpt_name}) ===")
        model = TD3.load(os.path.join(CKPT_DIR, ckpt_name))
        for scen in VALIDATION_SCENARIOS:
            df_peak, rocof_peak, tds_ok, sat = run_policy(scen, model)
            rows.append(dict(controller=f'seed{seed}', scenario=str(scen), df_peak_hz=df_peak,
                              rocof_peak_hz_s=rocof_peak, J_val=j_val(df_peak, rocof_peak),
                              TDS_success=tds_ok, saturation_fraction=sat))
            print(f"  {str(scen):70s} df_peak={df_peak:.4f}Hz RoCoF_peak={rocof_peak:.3f}Hz/s "
                  f"sat={sat:.3f}")

    df = pd.DataFrame(rows)

    # I_f/I_r relative to droop* (SS21 formula), per (controller, scenario) -- preview only
    droop_ref = df[df['controller'] == 'droop_star'].set_index('scenario')
    i_f_list, i_r_list = [], []
    for _, row in df.iterrows():
        d = droop_ref.loc[row['scenario']]
        i_f_list.append((abs(d['df_peak_hz']) - abs(row['df_peak_hz'])) / abs(d['df_peak_hz']))
        i_r_list.append((d['rocof_peak_hz_s'] - row['rocof_peak_hz_s']) / d['rocof_peak_hz_s'])
    df['I_f_vs_droop'] = i_f_list
    df['I_r_vs_droop'] = i_r_list

    out_csv = os.path.join(OUT_DIAG, 'p2e11_validation_comparison.csv')
    df.to_csv(out_csv, index=False)
    print(f"\nSaved: {out_csv}")

    print("\n=== RESUMEN (mean sobre 6 escenarios validation) ===")
    summary = df.groupby('controller').agg(
        J_val_mean=('J_val', 'mean'), df_peak_mean_hz=('df_peak_hz', 'mean'),
        rocof_peak_mean_hz_s=('rocof_peak_hz_s', 'mean'),
        I_f_vs_droop_mean=('I_f_vs_droop', 'mean'), I_r_vs_droop_mean=('I_r_vs_droop', 'mean'),
        saturation_fraction_mean=('saturation_fraction', 'mean'),
    )
    order = ['NoFFC', 'droop_star'] + [f'seed{s}' for s in SEED_CHECKPOINTS]
    print(summary.reindex(order).to_string())
    summary.reindex(order).to_csv(os.path.join(OUT_DIAG, 'p2e11_validation_comparison_summary.csv'))


if __name__ == '__main__':
    main()
