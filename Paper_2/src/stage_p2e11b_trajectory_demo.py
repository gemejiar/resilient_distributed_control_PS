#!/usr/bin/env python
"""
P2-E11b -- full trajectory demo: does the trained TD3 residual visibly act
to improve nadir/RoCoF under a real disturbance? NoFFC vs droop* vs TD3
(seed44, best J_val_P2 in the DEC-P2-037 preview) on the two validation
event TYPES (one gen, one load, middle operating point lambda_L=1.00).
Full-resolution trajectory (t, f_worst, RoCoF_worst over the 10 GEN_BUSES,
P_command/P_delivered per BESS), same f_worst/RoCoF_worst definition used
throughout the campaign (p2_common.py, DEC-P2-030/033 corrected scope).

Validation-split only, NOT P2-T*.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p2_env_train import P2ResidualTrainEnv, F0_HZ
from stable_baselines3 import TD3

PMAX_MW = 293.4
KD_STAR = 4694.4
P_RL_MAX_MW = 73.35
TC = TSTEP = 0.005
BESS_BUS1, BESS_BUS2 = 16, 20
BEST_SEED, BEST_CKPT = 44, 'seed44_ep600'
CKPT_DIR = os.path.join('Paper_2', 'artifacts', 'models', 'p2e9_seeds')
OUT_TRAJ = os.path.join('Paper_2', 'artifacts', 'trajectories')
os.makedirs(OUT_TRAJ, exist_ok=True)

SCENARIOS = {
    'gen_val': dict(kind='gen', gen='GENROU_6', rho=0.6, lambda_L=1.00),
    'load_val': dict(kind='load', pq_idx='PQ_10', alpha_L=0.3, lambda_L=1.00),
}


def make_env(scen, kd_star):
    return P2ResidualTrainEnv(obs_mode='OBS-A', p_max_bess_mw=PMAX_MW, kd_star_mw_per_hz=kd_star,
                               p_rl_max_mw=P_RL_MAX_MW, tc=TC, tstep=TSTEP,
                               bess_bus1=BESS_BUS1, bess_bus2=BESS_BUS2, fixed_scenario=scen)


def run_trajectory(scen, kd_star, model=None):
    env = make_env(scen, kd_star)
    obs, info = env.reset()
    t_hist, f_worst_hist, rocof_worst_hist = [], [], []
    pc1_hist, pc2_hist, pd1_hist, pd2_hist = [], [], [], []
    terminated = truncated = False
    while not (terminated or truncated):
        action = model.predict(obs, deterministic=True)[0] if model is not None else np.zeros(2)
        obs, reward, terminated, truncated, info = env.step(action)
        f_gen, rocof_gen = env._gen_bus_arrays()
        raw = env.get_raw_signals()
        t_hist.append(info['t'])
        f_worst_hist.append(float(np.min(f_gen)))
        rocof_worst_hist.append(float(np.max(np.abs(rocof_gen))))
        pc1_hist.append(info['p_total_mw'][0])
        pc2_hist.append(info['p_total_mw'][1])
        pd1_hist.append(raw['p1_mw'])
        pd2_hist.append(raw['p2_mw'])
    return dict(t=np.array(t_hist), f_worst_hz=np.array(f_worst_hist),
                rocof_worst_hz_s=np.array(rocof_worst_hist),
                p_command1_mw=np.array(pc1_hist), p_command2_mw=np.array(pc2_hist),
                p_delivered1_mw=np.array(pd1_hist), p_delivered2_mw=np.array(pd2_hist))


def main():
    model = TD3.load(os.path.join(CKPT_DIR, BEST_CKPT))
    flat = {}
    for scen_label, scen in SCENARIOS.items():
        print(f"=== {scen_label}: {scen} ===")
        for ctrl_label, kd, mdl in [('NoFFC', 0.0, None), ('droop_star', KD_STAR, None),
                                     (f'TD3_seed{BEST_SEED}', KD_STAR, model)]:
            tr = run_trajectory(scen, kd, mdl)
            key = f'{scen_label}__{ctrl_label}'
            for name, arr in tr.items():
                flat[f'{key}__{name}'] = arr
            i_nadir = int(np.argmin(tr['f_worst_hz']))
            i_rocof = int(np.argmax(tr['rocof_worst_hz_s']))
            print(f"  {ctrl_label:14s} nadir={tr['f_worst_hz'][i_nadir]:.4f}Hz@t={tr['t'][i_nadir]:.3f}s "
                  f"RoCoF_max={tr['rocof_worst_hz_s'][i_rocof]:.3f}Hz/s@t={tr['t'][i_rocof]:.3f}s "
                  f"Ppeak1={np.max(np.abs(tr['p_delivered1_mw'])):.1f}MW "
                  f"Ppeak2={np.max(np.abs(tr['p_delivered2_mw'])):.1f}MW")

    out_npz = os.path.join(OUT_TRAJ, 'p2e11b_trajectory_demo.npz')
    np.savez_compressed(out_npz, **flat)
    print(f"\nSaved: {out_npz}")


if __name__ == '__main__':
    main()
