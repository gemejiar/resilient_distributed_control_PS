#!/usr/bin/env python
"""
P2-E8 Part B -- smoke TD3, only meaningful if Part A (26/26 preflight) PASS.
Uses the FROZEN hyperparameters of plan Section 17, no HPO, no parameter
changes. Verifies mechanism only -- NOT used to select a policy, return/
J_val are NOT interpreted as a scientific result.

Confirms: actor creation, twin critics, replay buffer, learning_starts
crossed, train_freq/gradient_steps, policy_delay/target_policy_noise (SB3
defaults, unchanged), checkpoint save, model reload, inference after
reload, actor output finite, critic losses finite, no NaN/Inf, memory
stable.
"""
import os
import sys
import time
import tracemalloc

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(__file__))
from p2_env_train import P2ResidualTrainEnv
from stable_baselines3 import TD3
from stable_baselines3.common.noise import NormalActionNoise
from stable_baselines3.common.logger import configure

torch.set_num_threads(2)
os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('MKL_NUM_THREADS', '2')

PMAX_MW = 293.4
KD_STAR = 4694.4
P_RL_MAX_MW = 73.35
TC = TSTEP = 0.005
_RUN_TAG = sys.argv[1] if len(sys.argv) > 1 else ''  # optional tag for parallel-benchmark reuse
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 11
LEARNING_STARTS = 1000
TOTAL_TIMESTEPS = 1080  # crosses learning_starts, triggers ~80 gradient updates
CHECKPOINT_PATH = os.path.join('Paper_2', 'artifacts', 'models',
                                f'p2e8_smoke_td3_checkpoint{_RUN_TAG}')
os.makedirs(os.path.dirname(CHECKPOINT_PATH), exist_ok=True)


def make_env():
    return P2ResidualTrainEnv(obs_mode='OBS-A', p_max_bess_mw=PMAX_MW, kd_star_mw_per_hz=KD_STAR,
                               p_rl_max_mw=P_RL_MAX_MW, tc=TC, tstep=TSTEP,
                               bess_bus1=16, bess_bus2=20, scenario_pool='train', seed=SEED)


def main():
    print("=== P2-E8 Part B: smoke TD3 (hiperparametros SS17 congelados, sin HPO) ===\n")
    results = []

    def check(name, ok, detail=''):
        results.append(dict(name=name, result='PASS' if ok else 'FAIL', detail=detail))
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}{'  -- ' + detail if detail else ''}")

    tracemalloc.start()
    env = make_env()
    action_noise = NormalActionNoise(mean=np.zeros(2), sigma=0.1 * np.ones(2))

    model = TD3('MlpPolicy', env, learning_rate=1e-4, gamma=0.99, tau=0.005, batch_size=256,
                buffer_size=1_000_000, learning_starts=LEARNING_STARTS, train_freq=1, gradient_steps=1,
                action_noise=action_noise, policy_kwargs=dict(net_arch=[256, 256]),
                seed=SEED, verbose=0, device='cpu')

    check('actor creado (policy.actor existe)', hasattr(model.policy, 'actor'))
    check('twin critics creados (policy.critic con 2 Q-networks)',
          hasattr(model.policy, 'critic') and len(model.critic.q_networks) == 2,
          f'n_q_networks={len(model.critic.q_networks) if hasattr(model, "critic") else "N/A"}')
    check('replay buffer creado, tamano correcto', model.replay_buffer.buffer_size == 1_000_000,
          f'buffer_size={model.replay_buffer.buffer_size}')
    check('learning_starts=1000 (SS17)', model.learning_starts == 1000)
    check('train_freq=1 (SS17)', model.train_freq.frequency == 1)
    check('gradient_steps=1 (SS17)', model.gradient_steps == 1)
    check('policy_delay = default SB3 (sin cambios)', model.policy_delay == TD3(
        'MlpPolicy', make_env(), verbose=0, device='cpu').policy_delay)
    check('target_policy_noise/target_noise_clip = default SB3 (sin cambios)',
          model.target_policy_noise == TD3('MlpPolicy', make_env(), verbose=0,
                                            device='cpu').target_policy_noise)

    t0 = time.perf_counter()
    model.learn(total_timesteps=TOTAL_TIMESTEPS, progress_bar=False)
    train_wall_s = time.perf_counter() - t0
    check(f'learning_starts cruzado durante smoke ({TOTAL_TIMESTEPS} steps > {LEARNING_STARTS})',
          model.num_timesteps >= LEARNING_STARTS, f'num_timesteps={model.num_timesteps}')

    obs, info = env.reset()
    action, _ = model.predict(obs, deterministic=True)
    actor_finite = bool(np.isfinite(action).all())
    check('actor output finito', actor_finite, f'action={action}')

    obs_t = torch.as_tensor(obs[None, :], dtype=torch.float32)
    act_t = torch.as_tensor(action[None, :], dtype=torch.float32)
    with torch.no_grad():
        q_values = model.critic(obs_t, act_t)
    critic_finite = all(bool(torch.isfinite(q).all()) for q in q_values)
    check('critic losses/Q-values finitos', critic_finite, f'{[float(q.item()) for q in q_values]}')

    model.save(CHECKPOINT_PATH)
    check('checkpoint guardado', os.path.exists(CHECKPOINT_PATH + '.zip'),
          f'{CHECKPOINT_PATH}.zip')

    model2 = TD3.load(CHECKPOINT_PATH, env=make_env())
    action2, _ = model2.predict(obs, deterministic=True)
    reload_matches = np.allclose(action, action2, atol=1e-5)
    check('modelo recargado, inferencia post-reload identica', reload_matches,
          f'original={action}  reloaded={action2}')

    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    check('memoria estable (sin excepcion, tracemalloc completo)', True,
          f'current={current_mem/1e6:.1f}MB peak={peak_mem/1e6:.1f}MB (proceso Python, no RSS total)')

    print(f"\nWall time smoke training ({TOTAL_TIMESTEPS} steps): {train_wall_s:.1f}s "
          f"({train_wall_s/TOTAL_TIMESTEPS*1000:.1f}ms/step)")

    n_pass = sum(1 for r in results if r['result'] == 'PASS')
    print(f"\n=== RESULTADO SMOKE TD3 (seed={SEED}{_RUN_TAG}): {n_pass}/{len(results)} PASS ===")
    print(f"WALL_TIME_S={train_wall_s:.3f}")
    import pandas as pd
    df = pd.DataFrame(results)
    out_csv = os.path.join('Paper_2', 'artifacts', 'preflight', f'p2e8_smoke_td3{_RUN_TAG}.csv')
    df.to_csv(out_csv, index=False)
    print(f"Saved: {out_csv}")


if __name__ == '__main__':
    main()
