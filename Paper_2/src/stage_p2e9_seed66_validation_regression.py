#!/usr/bin/env python
"""seed66 pre-training validation, step 1 of the approved plan
(DEC-P2-041): action_smoothness_weight=0.0 and require_stability_for_best=
False must reproduce EXACTLY the historical seed11 ep=200 evaluation
(J_val_P2, df_peak_mean_hz, rocof_peak_mean_hz_s) already logged in
seed11_eval_log.csv from the real P2-E9 run -- same deterministic policy,
same fixed scenarios, same seed. Same regression pattern as DEC-P2-030/033.
"""
import os
import sys
import time

import numpy as np
import pandas as pd

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'Paper_2', 'src'))
os.chdir(REPO)

from p2_env_train import P2ResidualTrainEnv
from p2_train_callback import P2ValidationCallback
from stable_baselines3 import TD3
from stable_baselines3.common.logger import configure as _configure_logger

PMAX_MW, KD_STAR, P_RL_MAX_MW, TC, TSTEP = 293.4, 4694.4, 73.35, 0.005, 0.005
BESS_BUS1, BESS_BUS2 = 16, 20

print("=" * 70)
print("STEP 1: REGRESSION COMPATIBILITY (seed11, ep200, real historical data)")
print("=" * 70)

hist_csv = os.path.join('Paper_2', 'artifacts', 'diagnostics', 'p2e9_seeds', 'seed11_eval_log.csv')
hist = pd.read_csv(hist_csv)
hist_row = hist[hist['episode'] == 200].iloc[0]
print(f"Historical (real P2-E9 run) seed11 ep200: J_val_P2={hist_row['J_val_P2']:.6f} "
      f"df_peak_mean_hz={hist_row['df_peak_mean_hz']:.6f} rocof_peak_mean_hz_s={hist_row['rocof_peak_mean_hz_s']:.6f}")

ckpt_path = os.path.join('Paper_2', 'artifacts', 'models', 'p2e9_seeds', 'seed11_ep200')
env0 = P2ResidualTrainEnv(obs_mode='OBS-A', p_max_bess_mw=PMAX_MW, kd_star_mw_per_hz=KD_STAR,
                           p_rl_max_mw=P_RL_MAX_MW, tc=TC, tstep=TSTEP,
                           bess_bus1=BESS_BUS1, bess_bus2=BESS_BUS2,
                           scenario_pool='train', seed=11)
model = TD3.load(ckpt_path, env=env0)
model._logger = _configure_logger(folder=None, format_strings=[])

cb = P2ValidationCallback(seed=11, ckpt_dir=os.path.join('c:\\tmp\\seed66_dryrun', 'ckpt_regr'),
                           log_dir=os.path.join('c:\\tmp\\seed66_dryrun', 'log_regr'),
                           pmax_mw=PMAX_MW, kd_star=KD_STAR, p_rl_max_mw=P_RL_MAX_MW,
                           tc=TC, tstep=TSTEP, bess_bus1=BESS_BUS1, bess_bus2=BESS_BUS2,
                           verbose=0, action_smoothness_weight=0.0,
                           require_stability_for_best=False)
cb.model = model
cb.num_timesteps = 200 * 1200
cb._t_start = time.perf_counter()
cb._evaluate_and_checkpoint()
new_row = cb.eval_log[-1]
print(f"NEW code (weight=0.0, require_stability=False): J_val_P2={new_row['J_val_P2']:.6f} "
      f"df_peak_mean_hz={new_row['df_peak_mean_hz']:.6f} rocof_peak_mean_hz_s={new_row['rocof_peak_mean_hz_s']:.6f}")

ok_j = np.isclose(new_row['J_val_P2'], hist_row['J_val_P2'], atol=1e-9)
ok_df = np.isclose(new_row['df_peak_mean_hz'], hist_row['df_peak_mean_hz'], atol=1e-9)
ok_r = np.isclose(new_row['rocof_peak_mean_hz_s'], hist_row['rocof_peak_mean_hz_s'], atol=1e-9)
print(f"MATCH J_val_P2: {ok_j}  MATCH df_peak: {ok_df}  MATCH rocof_peak: {ok_r}")
print(f"'classification_v2' key present in row (should be ABSENT when require_stability_for_best=False): "
      f"{'classification_v2' in new_row}")
print(f"STEP 1 RESULT: {'PASS' if (ok_j and ok_df and ok_r) else 'FAIL'}")
