#!/usr/bin/env python
"""
P2-E8 Part C -- computational benchmark, exactly the FROZEN final environment
(droop*+TD3 residual, OBS-A, Tc=tstep=5ms, DEC-P2-033). Real measurements,
not extrapolation from Paper_1. No hours of training -- single-seed +
short 5-process parallel test only.
"""
import os
import sys
import time
import subprocess

import numpy as np
import pandas as pd
import psutil
import torch

sys.path.insert(0, os.path.dirname(__file__))
from p2_env_train import P2ResidualTrainEnv, VALIDATION_SCENARIOS
from stable_baselines3 import TD3
from stable_baselines3.common.noise import NormalActionNoise

torch.set_num_threads(2)
os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('MKL_NUM_THREADS', '2')

PMAX_MW = 293.4
KD_STAR = 4694.4
P_RL_MAX_MW = 73.35
TC = TSTEP = 0.005
SEED = 11
LEARNING_STARTS = 1000
OUT_DIAG = os.path.join('Paper_2', 'artifacts', 'preflight')
os.makedirs(OUT_DIAG, exist_ok=True)


def make_env():
    return P2ResidualTrainEnv(obs_mode='OBS-A', p_max_bess_mw=PMAX_MW, kd_star_mw_per_hz=KD_STAR,
                               p_rl_max_mw=P_RL_MAX_MW, tc=TC, tstep=TSTEP,
                               bess_bus1=16, bess_bus2=20, scenario_pool='train', seed=SEED)


def measure_pure_simulation():
    print("\n--- 1. Costo de simulacion SIN aprendizaje (env puro, sin TD3) ---")
    env = make_env()
    env.reset()
    t0 = time.perf_counter()
    n = env.n_int_steps
    for _ in range(n):
        env.step([0.0, 0.0])
    dt = time.perf_counter() - t0
    print(f"  {n} pasos (1 episodio) en {dt:.2f}s -> {dt/n*1000:.2f}ms/paso, "
          f"{dt/n*1000*1000:.1f}ms/1000 transiciones")
    return dict(n_steps=n, wall_s=dt, ms_per_step=dt / n * 1000)


def measure_td3_episode(with_gradient_updates):
    label = 'CON gradient updates (post-warmup)' if with_gradient_updates else 'SIN gradient updates (warmup)'
    print(f"\n--- 2. Costo de un episodio TD3, {label} ---")
    env = make_env()
    noise = NormalActionNoise(mean=np.zeros(2), sigma=0.1 * np.ones(2))
    ls = 0 if with_gradient_updates else 100_000  # force/prevent gradient updates during this episode
    model = TD3('MlpPolicy', env, learning_rate=1e-4, gamma=0.99, tau=0.005, batch_size=256,
                buffer_size=1_000_000, learning_starts=ls, train_freq=1, gradient_steps=1,
                action_noise=noise, policy_kwargs=dict(net_arch=[256, 256]), seed=SEED,
                verbose=0, device='cpu')
    n = env.n_int_steps
    t0 = time.perf_counter()
    model.learn(total_timesteps=n, progress_bar=False)
    dt = time.perf_counter() - t0
    print(f"  {n} transiciones en {dt:.2f}s -> {dt/n*1000:.2f}ms/paso, "
          f"{dt/n*1000*1000:.1f}ms/1000 transiciones")
    return dict(n_steps=n, wall_s=dt, ms_per_step=dt / n * 1000)


def measure_ram_and_buffer():
    print("\n--- 5/6. RAM y tamano real del replay buffer (buffer_size=1_000_000) ---")
    proc = psutil.Process()
    rss_before = proc.memory_info().rss
    env = make_env()
    noise = NormalActionNoise(mean=np.zeros(2), sigma=0.1 * np.ones(2))
    model = TD3('MlpPolicy', env, learning_rate=1e-4, gamma=0.99, tau=0.005, batch_size=256,
                buffer_size=1_000_000, learning_starts=LEARNING_STARTS, train_freq=1, gradient_steps=1,
                action_noise=noise, policy_kwargs=dict(net_arch=[256, 256]), seed=SEED,
                verbose=0, device='cpu')
    rss_after_buffer = proc.memory_info().rss
    buf = model.replay_buffer
    buf_bytes = buf.observations.nbytes + buf.actions.nbytes + buf.rewards.nbytes + buf.dones.nbytes
    if hasattr(buf, 'next_observations') and buf.next_observations is not None:
        buf_bytes += buf.next_observations.nbytes
    print(f"  RSS antes de crear el modelo: {rss_before/1e6:.1f}MB")
    print(f"  RSS despues de crear TD3 (con replay buffer 1M): {rss_after_buffer/1e6:.1f}MB "
          f"(delta={((rss_after_buffer-rss_before)/1e6):.1f}MB)")
    print(f"  Tamano real del replay buffer (numpy arrays): {buf_bytes/1e6:.1f}MB")
    return dict(rss_before_mb=rss_before / 1e6, rss_after_buffer_mb=rss_after_buffer / 1e6,
                buffer_bytes_mb=buf_bytes / 1e6)


def measure_cpu_during_training():
    print("\n--- 7. Uso de CPU observado (single-seed) ---")
    env = make_env()
    noise = NormalActionNoise(mean=np.zeros(2), sigma=0.1 * np.ones(2))
    model = TD3('MlpPolicy', env, learning_rate=1e-4, gamma=0.99, tau=0.005, batch_size=256,
                buffer_size=1_000_000, learning_starts=LEARNING_STARTS, train_freq=1, gradient_steps=1,
                action_noise=noise, policy_kwargs=dict(net_arch=[256, 256]), seed=SEED,
                verbose=0, device='cpu')
    proc = psutil.Process()
    proc.cpu_percent(interval=None)  # prime the counter
    t0 = time.perf_counter()
    model.learn(total_timesteps=1200, progress_bar=False)
    dt = time.perf_counter() - t0
    cpu_pct = proc.cpu_percent(interval=None)
    print(f"  CPU% del proceso (psutil, promedio sobre {dt:.1f}s de entrenamiento single-seed): "
          f"{cpu_pct:.1f}% (>100% posible si usa >1 nucleo logico; {psutil.cpu_count(logical=True)} "
          f"nucleos logicos disponibles)")
    return dict(cpu_percent=cpu_pct, n_logical_cores=psutil.cpu_count(logical=True))


def measure_validation_eval_cost():
    print("\n--- 8. Costo de evaluacion validation (6 escenarios, politica deterministica) ---")
    env_train = make_env()
    noise = NormalActionNoise(mean=np.zeros(2), sigma=0.1 * np.ones(2))
    model = TD3('MlpPolicy', env_train, learning_rate=1e-4, gamma=0.99, tau=0.005, batch_size=256,
                buffer_size=10_000, learning_starts=1000, train_freq=1, gradient_steps=1,
                action_noise=noise, policy_kwargs=dict(net_arch=[256, 256]), seed=SEED,
                verbose=0, device='cpu')
    model.learn(total_timesteps=1050, progress_bar=False)  # minimal warmup so predict() is well-formed
    t0 = time.perf_counter()
    for scen in VALIDATION_SCENARIOS:
        env = P2ResidualTrainEnv(obs_mode='OBS-A', p_max_bess_mw=PMAX_MW, kd_star_mw_per_hz=KD_STAR,
                                  p_rl_max_mw=P_RL_MAX_MW, tc=TC, tstep=TSTEP, bess_bus1=16, bess_bus2=20,
                                  fixed_scenario=scen, seed=SEED)
        obs, info = env.reset()
        terminated = truncated = False
        while not (terminated or truncated):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
    dt = time.perf_counter() - t0
    print(f"  6 escenarios de validation evaluados en {dt:.2f}s ({dt/6:.2f}s/escenario)")
    return dict(wall_s=dt, n_scenarios=len(VALIDATION_SCENARIOS))


def measure_checkpoint_io():
    print("\n--- 9. Tiempo de guardado/carga de checkpoint ---")
    env = make_env()
    model = TD3('MlpPolicy', env, buffer_size=10_000, learning_starts=1000,
                policy_kwargs=dict(net_arch=[256, 256]), seed=SEED, verbose=0, device='cpu')
    path = os.path.join('Paper_2', 'artifacts', 'models', 'p2e8_benchmark_ckpt')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    t0 = time.perf_counter()
    model.save(path)
    t_save = time.perf_counter() - t0
    t0 = time.perf_counter()
    TD3.load(path, env=make_env())
    t_load = time.perf_counter() - t0
    print(f"  save(): {t_save*1000:.1f}ms   load(): {t_load*1000:.1f}ms")
    return dict(save_s=t_save, load_s=t_load)


def run_parallel_test(n_procs=5):
    print(f"\n--- Prueba de concurrencia: {n_procs} procesos/seeds simultaneos ---")
    seeds = [11, 22, 33, 44, 55][:n_procs]
    script = os.path.join('Paper_2', 'src', 'stage_p2e8b_smoke_td3.py')
    proc = psutil.Process()
    procs = []
    t0 = time.perf_counter()
    cpu_samples = []
    for seed in seeds:
        p = subprocess.Popen([sys.executable, script, f'_par{seed}', str(seed)],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        procs.append(p)
    # sample system-wide CPU while the batch runs
    psutil.cpu_percent(interval=None)
    while any(p.poll() is None for p in procs):
        cpu_samples.append(psutil.cpu_percent(interval=1.0))
    dt_parallel = time.perf_counter() - t0
    outputs = [p.communicate()[0] if p.stdout is None else (p.stdout.read() if p.stdout else '') for p in procs]
    # (communicate already drains stdout above for procs that finished after poll loop; ensure clean join)
    for p in procs:
        p.wait()
    all_ok = all(p.returncode == 0 for p in procs)
    print(f"  {n_procs} procesos completados en {dt_parallel:.1f}s pared (paralelo)")
    print(f"  returncodes: {[p.returncode for p in procs]}  todos_ok={all_ok}")
    if cpu_samples:
        print(f"  CPU sistema durante el batch: min={min(cpu_samples):.0f}% max={max(cpu_samples):.0f}% "
              f"mean={np.mean(cpu_samples):.0f}% (100%=1 nucleo logico saturado, "
              f"{psutil.cpu_count(logical=True)*100}%=todos saturados)")
    return dict(n_procs=n_procs, wall_s_parallel=dt_parallel, all_ok=all_ok,
                cpu_min=min(cpu_samples) if cpu_samples else None,
                cpu_max=max(cpu_samples) if cpu_samples else None,
                cpu_mean=float(np.mean(cpu_samples)) if cpu_samples else None)


def main():
    print("=== P2-E8 Part C: benchmark computacional (config FROZEN DEC-P2-033) ===")

    r1 = measure_pure_simulation()
    r2a = measure_td3_episode(with_gradient_updates=False)
    r2b = measure_td3_episode(with_gradient_updates=True)
    r5 = measure_ram_and_buffer()
    r7 = measure_cpu_during_training()
    r8 = measure_validation_eval_cost()
    r9 = measure_checkpoint_io()

    single_seed_1080_wall_s = None
    print("\n--- Referencia: 1 episodio de warmup + episodios con gradiente (single-seed, 1080 steps) ---")
    t0 = time.perf_counter()
    env = make_env()
    noise = NormalActionNoise(mean=np.zeros(2), sigma=0.1 * np.ones(2))
    model = TD3('MlpPolicy', env, learning_rate=1e-4, gamma=0.99, tau=0.005, batch_size=256,
                buffer_size=1_000_000, learning_starts=1000, train_freq=1, gradient_steps=1,
                action_noise=noise, policy_kwargs=dict(net_arch=[256, 256]), seed=SEED,
                verbose=0, device='cpu')
    model.learn(total_timesteps=1080, progress_bar=False)
    single_seed_1080_wall_s = time.perf_counter() - t0
    print(f"  1080 transiciones (single-seed, referencia para el test de concurrencia): "
          f"{single_seed_1080_wall_s:.1f}s")

    rP = run_parallel_test(n_procs=5)

    summary = dict(
        pure_sim_ms_per_step=r1['ms_per_step'],
        td3_episode_warmup_ms_per_step=r2a['ms_per_step'],
        td3_episode_gradient_ms_per_step=r2b['ms_per_step'],
        transitions_per_episode=r1['n_steps'],
        ms_per_1000_transitions_warmup=r2a['ms_per_step'] * 1000,
        ms_per_1000_transitions_gradient=r2b['ms_per_step'] * 1000,
        rss_after_buffer_mb=r5['rss_after_buffer_mb'],
        replay_buffer_actual_mb=r5['buffer_bytes_mb'],
        cpu_percent_single_seed=r7['cpu_percent'],
        n_logical_cores=r7['n_logical_cores'],
        validation_eval_wall_s=r8['wall_s'],
        checkpoint_save_s=r9['save_s'],
        checkpoint_load_s=r9['load_s'],
        single_seed_1080steps_wall_s=single_seed_1080_wall_s,
        parallel_5procs_wall_s=rP['wall_s_parallel'],
        parallel_5procs_all_ok=rP['all_ok'],
        parallel_cpu_min=rP['cpu_min'], parallel_cpu_max=rP['cpu_max'], parallel_cpu_mean=rP['cpu_mean'],
        speedup_vs_sequential=(5 * single_seed_1080_wall_s / rP['wall_s_parallel']
                                if rP['wall_s_parallel'] else None),
    )
    df = pd.DataFrame([summary])
    out_csv = os.path.join(OUT_DIAG, 'p2e8_benchmark_summary.csv')
    df.to_csv(out_csv, index=False)
    print(f"\nSaved: {out_csv}")
    print("\n=== RESUMEN BENCHMARK ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")


if __name__ == '__main__':
    main()
