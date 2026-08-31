#!/usr/bin/env python
"""seed66 pre-training validation, step 3 of the approved plan (DEC-P2-041):
mechanical dry-run of the stability-gated checkpoint eligibility logic.
Mirrors stage_p2e9_train_seed.py's construction exactly (same env/model/
callback classes and hyperparameters) but at reduced scale (seed=999,
min_episodes=2, patience=1, eval_freq=1, max_episodes=3), same synthetic-
seed pattern already used to validate P2ValidationCallback before the real
P2-E9 run (DEC-P2-035).

Runs the SAME dry-run TWICE (require_stability_for_best=False, then True)
to directly confirm the gate changes which checkpoints get accepted as
"best" without altering anything else (early stopping floor/patience/
eval-freq bookkeeping, checkpoint saving, numerical-failure counting).

NOTE: this run alone only exercises the ACCEPT path (the untrained/near-
random seed=999 policy over 3 episodes stayed STABLE in all 6 scenarios
every time, since it is close to droop*-only behavior, which is known
STABLE per DEC-P2-040). The REJECT path is exercised separately in
stage_p2e9_seed66_validation_reject_branch.py.
"""
import os
import sys
import time

import numpy as np
import pandas as pd
import torch

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'Paper_2', 'src'))
os.chdir(REPO)

from p2_env_train import P2ResidualTrainEnv
from p2_train_callback import P2ValidationCallback
from stable_baselines3 import TD3
from stable_baselines3.common.noise import NormalActionNoise

torch.set_num_threads(2)

SCRATCH = r"c:\tmp\seed66_dryrun"

PMAX_MW, KD_STAR, P_RL_MAX_MW, TC, TSTEP = 293.4, 4694.4, 73.35, 0.005, 0.005
BESS_BUS1, BESS_BUS2 = 16, 20
SEED = 999


def run_dry(require_stability, label):
    print("=" * 70)
    print(f"DRY-RUN: require_stability_for_best={require_stability}  ({label})")
    print("=" * 70)
    env = P2ResidualTrainEnv(obs_mode='OBS-A', p_max_bess_mw=PMAX_MW, kd_star_mw_per_hz=KD_STAR,
                              p_rl_max_mw=P_RL_MAX_MW, tc=TC, tstep=TSTEP,
                              bess_bus1=BESS_BUS1, bess_bus2=BESS_BUS2,
                              scenario_pool='train', seed=SEED,
                              action_smoothness_weight=0.02)
    action_noise = NormalActionNoise(mean=np.zeros(2), sigma=0.1 * np.ones(2))
    model = TD3('MlpPolicy', env, learning_rate=1e-4, gamma=0.99, tau=0.005, batch_size=256,
                buffer_size=1_000_000, learning_starts=1000, train_freq=1, gradient_steps=1,
                action_noise=action_noise, policy_kwargs=dict(net_arch=[256, 256]),
                seed=SEED, verbose=0, device='cpu')

    ckpt_dir = os.path.join(SCRATCH, f'dryrun_seed66_{"stab" if require_stability else "nostab"}_ckpt')
    log_dir = os.path.join(SCRATCH, f'dryrun_seed66_{"stab" if require_stability else "nostab"}_log')
    callback = P2ValidationCallback(
        seed=SEED, ckpt_dir=ckpt_dir, log_dir=log_dir,
        eval_freq_episodes=1, min_episodes_before_stop=2, patience_evals=1, max_episodes_safety_cap=3,
        pmax_mw=PMAX_MW, kd_star=KD_STAR, p_rl_max_mw=P_RL_MAX_MW, tc=TC, tstep=TSTEP,
        bess_bus1=BESS_BUS1, bess_bus2=BESS_BUS2, verbose=1,
        action_smoothness_weight=0.02, require_stability_for_best=require_stability)

    t0 = time.perf_counter()
    upper_bound_steps = 3 * 1200 + 10_000
    model.learn(total_timesteps=upper_bound_steps, callback=callback, progress_bar=False)
    wall_s = time.perf_counter() - t0

    eval_csv, diag_csv = callback.save_logs()
    print(f"best_checkpoint={callback.best_ckpt_path}  best_J_val_P2={callback.best_j_val}  "
          f"best_episode={callback.best_episode}")
    print(f"stopped_early={callback.stopped_early}  reason={callback.stop_reason}")
    print(f"wall_time_s={wall_s:.1f}")

    eval_df = pd.read_csv(eval_csv)
    diag_df = pd.read_csv(diag_csv)
    print("\neval_log:")
    print(eval_df[['episode', 'J_val_P2', 'improved', 'evals_since_improvement']].to_string(index=False))
    if require_stability:
        print("\ndiag_log (stability columns):")
        cols = [c for c in ['episode', 'n_stable_of_6', 'all_stable', 'unstable_scenarios'] if c in diag_df.columns]
        print(diag_df[cols].to_string(index=False))
        merged = eval_df.merge(diag_df[['episode', 'all_stable']], on='episode')
        bad = merged[(merged['improved']) & (~merged['all_stable'])]
        print(f"\nSANITY CHECK (no row should be improved=True with all_stable=False): "
              f"{'PASS' if len(bad) == 0 else 'FAIL -- ' + str(bad)}")
    else:
        print(f"\n'n_stable_of_6' column present in diag_log (should be ABSENT): "
              f"{'n_stable_of_6' in diag_df.columns}")
    return callback, eval_df


cb_false, ev_false = run_dry(False, "reproduces old min-J_val-only selection")
print()
cb_true, ev_true = run_dry(True, "new AND-stability gate")

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"require_stability=False: best_J_val_P2={cb_false.best_j_val:.4f} at ep={cb_false.best_episode}, "
      f"n_improved={int(ev_false['improved'].sum())}/{len(ev_false)}")
print(f"require_stability=True : best_J_val_P2={cb_true.best_j_val:.4f} at ep={cb_true.best_episode}, "
      f"n_improved={int(ev_true['improved'].sum())}/{len(ev_true)}")
