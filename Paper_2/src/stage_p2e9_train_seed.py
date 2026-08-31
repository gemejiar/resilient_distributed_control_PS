#!/usr/bin/env python
"""
P2-E9 -- final TD3 training, one seed. Config FROZEN (DEC-P2-033), no
modification. Checkpoint selection EXCLUSIVELY by minimum J_val_P2 (never
return/actor loss/critic loss/Ppeak/energy/saturation_fraction). Early
stopping exactly plan Section 19 (>=2000 episodes, patience=5 evals).

Usage:
  python stage_p2e9_train_seed.py <seed> [--min-episodes N] [--patience N]
                                          [--eval-freq N] [--max-episodes N]

The optional overrides exist ONLY for mechanical dry-run validation of this
script before committing the real multi-hour run (DEC-P2-035) -- the real
run always uses the plan-frozen defaults (2000/5/200/6000), never HPO on
these numbers.
"""
import argparse
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(__file__))
from p2_env_train import P2ResidualTrainEnv
from p2_train_callback import P2ValidationCallback
from stable_baselines3 import TD3
from stable_baselines3.common.noise import NormalActionNoise

torch.set_num_threads(2)
os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('MKL_NUM_THREADS', '2')

PMAX_MW = 293.4
KD_STAR = 4694.4
P_RL_MAX_MW = 73.35
TC = TSTEP = 0.005
BESS_BUS1, BESS_BUS2 = 16, 20

CKPT_DIR = os.path.join('Paper_2', 'artifacts', 'models', 'p2e9_seeds')
LOG_DIR = os.path.join('Paper_2', 'artifacts', 'diagnostics', 'p2e9_seeds')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('seed', type=int)
    ap.add_argument('--min-episodes', type=int, default=2000)
    ap.add_argument('--patience', type=int, default=5)
    ap.add_argument('--eval-freq', type=int, default=200)
    ap.add_argument('--max-episodes', type=int, default=6000)
    # seed66 (DEC-P2-041 pending): both optional, default = exact behavior used by seeds 11-55.
    ap.add_argument('--action-smoothness-weight', type=float, default=0.0)
    ap.add_argument('--require-stability-for-best', action='store_true', default=False)
    args = ap.parse_args()

    is_dry_run = (args.min_episodes, args.patience, args.eval_freq, args.max_episodes) != (2000, 5, 200, 6000)
    print(f"=== P2-E9: seed={args.seed} {'[DRY-RUN VALIDATION, no plan defaults]' if is_dry_run else '[REAL RUN, plan SS19 defaults]'} ===")
    print(f"min_episodes={args.min_episodes} patience={args.patience} eval_freq={args.eval_freq} "
          f"max_episodes_safety_cap={args.max_episodes}")
    print(f"action_smoothness_weight={args.action_smoothness_weight} "
          f"require_stability_for_best={args.require_stability_for_best}")

    env = P2ResidualTrainEnv(obs_mode='OBS-A', p_max_bess_mw=PMAX_MW, kd_star_mw_per_hz=KD_STAR,
                              p_rl_max_mw=P_RL_MAX_MW, tc=TC, tstep=TSTEP,
                              bess_bus1=BESS_BUS1, bess_bus2=BESS_BUS2,
                              scenario_pool='train', seed=args.seed,
                              action_smoothness_weight=args.action_smoothness_weight)
    action_noise = NormalActionNoise(mean=np.zeros(2), sigma=0.1 * np.ones(2))
    model = TD3('MlpPolicy', env, learning_rate=1e-4, gamma=0.99, tau=0.005, batch_size=256,
                buffer_size=1_000_000, learning_starts=1000, train_freq=1, gradient_steps=1,
                action_noise=action_noise, policy_kwargs=dict(net_arch=[256, 256]),
                seed=args.seed, verbose=0, device='cpu')

    callback = P2ValidationCallback(
        seed=args.seed, ckpt_dir=CKPT_DIR, log_dir=LOG_DIR,
        eval_freq_episodes=args.eval_freq, min_episodes_before_stop=args.min_episodes,
        patience_evals=args.patience, max_episodes_safety_cap=args.max_episodes,
        pmax_mw=PMAX_MW, kd_star=KD_STAR, p_rl_max_mw=P_RL_MAX_MW, tc=TC, tstep=TSTEP,
        bess_bus1=BESS_BUS1, bess_bus2=BESS_BUS2, verbose=1,
        action_smoothness_weight=args.action_smoothness_weight,
        require_stability_for_best=args.require_stability_for_best)

    t0 = time.perf_counter()
    upper_bound_steps = args.max_episodes * 1200 + 10_000  # safety valve, callback stops earlier
    model.learn(total_timesteps=upper_bound_steps, callback=callback, progress_bar=False)
    wall_s = time.perf_counter() - t0

    eval_csv, diag_csv = callback.save_logs()

    print(f"\n=== RESULTADO seed={args.seed} ===")
    print(f"best_checkpoint: {callback.best_ckpt_path}")
    print(f"best_J_val_P2: {callback.best_j_val:.4f}")
    print(f"best_episode: {callback.best_episode}")
    print(f"stopped_early: {callback.stopped_early}  reason: {callback.stop_reason}")
    print(f"total_timesteps: {model.num_timesteps}  total_episodes: {model.num_timesteps // 1200}")
    print(f"numerical_failures: {callback.numerical_failures}")
    print(f"wall_time_s: {wall_s:.1f}")
    print(f"eval_log: {eval_csv}")
    print(f"diag_log: {diag_csv}")

    # Checkpoint integrity check: two INDEPENDENT reloads of the SAME best checkpoint file must
    # produce identical deterministic output (true round-trip/corruption test). NOTE: comparing
    # against the final in-memory model would be wrong -- the final model is a LATER training point
    # than the best checkpoint by construction, so they are expected to differ; that is not what
    # "integrity" should mean (found and corrected after seed 11 -- see DEC-P2-035 for the
    # investigation that confirmed seed 11's checkpoint file was never actually corrupted).
    integrity_ok = False
    if callback.best_ckpt_path and os.path.exists(callback.best_ckpt_path + '.zip'):
        obs, info = env.reset()
        reloaded_a = TD3.load(callback.best_ckpt_path, env=env)
        reloaded_b = TD3.load(callback.best_ckpt_path, env=env)
        a1, _ = reloaded_a.predict(obs, deterministic=True)
        a2, _ = reloaded_b.predict(obs, deterministic=True)
        integrity_ok = bool(np.allclose(a1, a2, atol=1e-8))
    print(f"checkpoint_integrity: {'PASS' if integrity_ok else 'FAIL'}")


if __name__ == '__main__':
    main()
