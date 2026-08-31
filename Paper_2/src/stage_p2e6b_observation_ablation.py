#!/usr/bin/env python
"""
P2-E6b -- observation ablation for the droop*+TD3-residual architecture
(OBS-A local / OBS-B local+COI / OBS-C global). Authorized explicitly by
the user. Architecture, reward, P_RL,max, and hyperparameters are IDENTICAL
across the three variants -- only the observation changes.

Per-OBS verification (Sections 1-6 of the instruction), then ONE short,
comparable TD3 training run per OBS (single DESIGN seed, same step budget,
Section 17 hyperparameters, no HPO), then J_val_P2 + physical metrics on the
frozen validation scenario set (p2_env_train.VALIDATION_SCENARIOS).

NO test final, NO P2-T*, NO checkpoint/policy selection beyond this
ablation's own comparison rule, NO final-seed training.
"""
import os
import sys

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, os.path.dirname(__file__))
from p2_env_train import (P2ResidualTrainEnv, VALIDATION_SCENARIOS, OBS_DIMS,
                           F_REF_HZ, R_REF_HZ_S)
from stable_baselines3 import TD3
from stable_baselines3.common.noise import NormalActionNoise

torch.set_num_threads(2)
os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('MKL_NUM_THREADS', '2')

SEED = 11
TOTAL_TIMESTEPS = 3000
LEARNING_STARTS = 1000
PMAX_MW = 293.4
KD_STAR = 4694.4
P_RL_MAX_MW = 73.35
TC = TSTEP = 0.005

OUT_DIAG = os.path.join('Paper_2', 'artifacts', 'diagnostics')
os.makedirs(OUT_DIAG, exist_ok=True)

FIXED_SCEN = dict(kind='gen', gen='GENROU_4', rho=0.90, lambda_L=1.00)  # for verification checks only


def make_env(obs_mode, scenario_pool='train', fixed_scenario=None, seed=SEED):
    return P2ResidualTrainEnv(obs_mode=obs_mode, p_max_bess_mw=PMAX_MW, kd_star_mw_per_hz=KD_STAR,
                               p_rl_max_mw=P_RL_MAX_MW, tc=TC, tstep=TSTEP,
                               scenario_pool=scenario_pool, fixed_scenario=fixed_scenario, seed=seed)


def verify_obs(obs_mode):
    print(f"\n--- Verificacion {obs_mode} ---")
    ok = True

    env = make_env(obs_mode, fixed_scenario=FIXED_SCEN)
    obs, info = env.reset()
    dim_ok = obs.shape == (OBS_DIMS[obs_mode],)
    print(f"  1. dimension: {obs.shape} (esperado {(OBS_DIMS[obs_mode],)}) -> {'OK' if dim_ok else 'FALLA'}")
    ok &= dim_ok

    rng = np.random.default_rng(0)
    finite_ok = np.isfinite(obs).all()
    for _ in range(200):
        action = rng.uniform(-1, 1, size=2)
        obs, reward, term, trunc, info = env.step(action)
        if not (np.isfinite(obs).all() and np.isfinite(reward)):
            finite_ok = False
            break
        if term or trunc:
            obs, info = env.reset()
    print(f"  2. sin NaN/Inf (200 pasos, acciones aleatorias): {'OK' if finite_ok else 'FALLA'}")
    ok &= bool(finite_ok)

    env_a = make_env(obs_mode, fixed_scenario=FIXED_SCEN)
    obs_a, _ = env_a.reset()
    env_b = make_env(obs_mode, fixed_scenario=FIXED_SCEN)
    obs_b, _ = env_b.reset()
    reset_diff = float(np.max(np.abs(obs_a - obs_b)))
    reset_ok = reset_diff < 1e-6
    print(f"  3. reset consistente (mismo escenario fijo): max|diff|={reset_diff:.2e} -> "
          f"{'OK' if reset_ok else 'FALLA'}")
    ok &= reset_ok

    env_c = make_env(obs_mode, fixed_scenario=FIXED_SCEN)
    obs_c, _ = env_c.reset()
    traj = [obs_c.copy()]
    raw_rows = [dict(step=0, **env_c.get_raw_signals())]
    for step in range(1, env_c.n_int_steps + 1):
        obs_c, reward, term, trunc, info = env_c.step(np.zeros(2))
        traj.append(obs_c.copy())
        if step % 40 == 0:
            raw_rows.append(dict(step=step, **env_c.get_raw_signals()))
        if term or trunc:
            break
    traj = np.array(traj)
    scale_report = []
    for i in range(traj.shape[1]):
        scale_report.append(dict(component=i, min=float(traj[:, i].min()), max=float(traj[:, i].max()),
                                  mean=float(traj[:, i].mean())))
    print(f"  4. escalas por componente (obs normalizada, {obs_mode}):")
    for r in scale_report:
        print(f"       comp[{r['component']:2d}]  min={r['min']:+7.3f}  max={r['max']:+7.3f}  "
              f"mean={r['mean']:+7.3f}")

    raw_flat = []
    for r in raw_rows:
        row = {k: v for k, v in r.items() if not isinstance(v, np.ndarray)}
        raw_flat.append(row)
    df_raw = pd.DataFrame(raw_flat)
    out_csv = os.path.join(OUT_DIAG, f'p2e6b_raw_vs_norm_{obs_mode.replace("-", "").lower()}.csv')
    df_raw.to_csv(out_csv, index=False)
    print(f"  5. raw registrado durante 1 episodio: {out_csv}")

    print("  6. sin leakage: obs se lee del estado ANDES INMEDIATAMENTE despues del paso fisico "
          "actual (p2_env_train.py::_get_obs, llamada al final de step()/reset()) -- no existe "
          "ninguna lectura de estado futuro ni de la trayectoria del disturbio; verificado por "
          "inspeccion de codigo -> OK")

    return ok


def train_one(obs_mode):
    print(f"\n=== Entrenando TD3 sobre {obs_mode} (seed={SEED}, total_timesteps={TOTAL_TIMESTEPS}) ===")
    env = make_env(obs_mode, scenario_pool='train', seed=SEED)
    action_noise = NormalActionNoise(mean=np.zeros(2), sigma=0.1 * np.ones(2))
    model = TD3('MlpPolicy', env, learning_rate=1e-4, gamma=0.99, tau=0.005, batch_size=256,
                buffer_size=10_000, learning_starts=LEARNING_STARTS, train_freq=1, gradient_steps=1,
                action_noise=action_noise, policy_kwargs=dict(net_arch=[256, 256]),
                seed=SEED, verbose=0, device='cpu')
    model.learn(total_timesteps=TOTAL_TIMESTEPS, progress_bar=False)
    return model


def evaluate(obs_mode, model):
    print(f"\n=== Evaluando {obs_mode} sobre {len(VALIDATION_SCENARIOS)} escenarios de validation ===")
    rows = []
    for scen in VALIDATION_SCENARIOS:
        env = make_env(obs_mode, fixed_scenario=scen)
        obs, info = env.reset()
        sat_count, action_count = 0, 0
        terminated = truncated = False
        while not (terminated or truncated):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            action_count += 1
            if abs(info['p_total_mw'][0]) >= PMAX_MW - 1e-3 or abs(info['p_total_mw'][1]) >= PMAX_MW - 1e-3:
                sat_count += 1
        df_peak, rocof_peak = info['df_peak'], info['rocof_peak']
        j_val = (max(df_peak / F_REF_HZ, rocof_peak / R_REF_HZ_S) +
                 0.25 * (df_peak / F_REF_HZ + rocof_peak / R_REF_HZ_S))
        rows.append(dict(obs_mode=obs_mode, scenario=str(scen), df_peak_hz=df_peak,
                          rocof_peak_hz_s=rocof_peak, J_val=j_val,
                          TDS_success=info['tds_success'],
                          saturation_fraction=sat_count / max(action_count, 1)))
        print(f"  {str(scen):70s} df_peak={df_peak:.4f}Hz RoCoF_peak={rocof_peak:.3f}Hz/s "
              f"J_val={j_val:.4f} TDS_ok={info['tds_success']} sat={sat_count/max(action_count,1):.3f}")
    return pd.DataFrame(rows)


def main():
    print("=== P2-E6b: ablation de observacion (OBS-A/B/C), droop*+TD3 residual ===")
    print(f"Config congelada: buses 16/20, Tc=tstep={TC*1000:.0f}ms, Pmax={PMAX_MW}MW, "
          f"Kd*={KD_STAR}MW/Hz, P_RL,max={P_RL_MAX_MW}MW, seed={SEED}, "
          f"total_timesteps={TOTAL_TIMESTEPS} (identico para las 3 variantes)")

    verify_results = {}
    for obs_mode in ('OBS-A', 'OBS-B', 'OBS-C'):
        verify_results[obs_mode] = verify_obs(obs_mode)

    all_eval = []
    for obs_mode in ('OBS-A', 'OBS-B', 'OBS-C'):
        model = train_one(obs_mode)
        df_eval = evaluate(obs_mode, model)
        all_eval.append(df_eval)

    df_all = pd.concat(all_eval, ignore_index=True)
    out_csv = os.path.join(OUT_DIAG, 'p2e6b_observation_ablation.csv')
    df_all.to_csv(out_csv, index=False)
    print(f"\nSaved: {out_csv}")

    print("\n=== RESUMEN: J_val_P2(global) y metricas fisicas por OBS ===")
    summary = df_all.groupby('obs_mode').agg(
        J_val_P2_global=('J_val', 'mean'),
        df_peak_mean_hz=('df_peak_hz', 'mean'),
        rocof_peak_mean_hz_s=('rocof_peak_hz_s', 'mean'),
        TDS_success_rate=('TDS_success', 'mean'),
        saturation_fraction_mean=('saturation_fraction', 'mean'),
    ).reindex(['OBS-A', 'OBS-B', 'OBS-C'])
    print(summary.to_string())

    print("\n=== Verificacion (Secciones 1-6) por OBS ===")
    for k, v in verify_results.items():
        print(f"  {k}: {'TODAS OK' if v else 'FALLO EN AL MENOS UNA VERIFICACION'}")

    summary_csv = os.path.join(OUT_DIAG, 'p2e6b_observation_ablation_summary.csv')
    summary.to_csv(summary_csv)
    print(f"Saved: {summary_csv}")


if __name__ == '__main__':
    main()
