#!/usr/bin/env python
"""seed66 pre-training validation, step 2 of the approved plan (DEC-P2-041):
magnitude-balance smoke test for action_smoothness_weight=0.02. Inspects the
smoothness penalty against the tracking term (e_f^2+e_r^2+2*max(e_f,e_r)^2)
in two regimes: Case A (seed11 ep200, train-pool, typical/converged
behavior) and Case B (seed44 ep600 -- the frozen best checkpoint, DEC-P2-035
-- on the first GEN validation scenario, the known-oscillatory case per
DEC-P2-039/040) to check the weight is neither negligible nor dominant in
the regime it is meant to act on.
"""
import os
import sys

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'Paper_2', 'src'))
os.chdir(REPO)

from p2_env_train import P2ResidualTrainEnv, VALIDATION_SCENARIOS
from stable_baselines3 import TD3
from stable_baselines3.common.logger import configure as _configure_logger

PMAX_MW, KD_STAR, P_RL_MAX_MW, TC, TSTEP = 293.4, 4694.4, 73.35, 0.005, 0.005
BESS_BUS1, BESS_BUS2 = 16, 20

print("=" * 70)
print("STEP 2: MAGNITUDE-BALANCE SMOKE (action_smoothness_weight=0.02)")
print("=" * 70)


def run_case(label, ckpt, scenario_pool, seed, fixed_scenario, n_max):
    env = P2ResidualTrainEnv(obs_mode='OBS-A', p_max_bess_mw=PMAX_MW, kd_star_mw_per_hz=KD_STAR,
                              p_rl_max_mw=P_RL_MAX_MW, tc=TC, tstep=TSTEP,
                              bess_bus1=BESS_BUS1, bess_bus2=BESS_BUS2,
                              scenario_pool=scenario_pool, seed=seed, fixed_scenario=fixed_scenario,
                              action_smoothness_weight=0.02)
    m = TD3.load(ckpt, env=env)
    m._logger = _configure_logger(folder=None, format_strings=[])
    obs, info = env.reset()
    tracking_terms, smooth_penalties = [], []
    terminated = truncated = False
    n = 0
    while not (terminated or truncated) and n < n_max:
        action, _ = m.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        tracking_terms.append(info['e_f'] ** 2 + info['e_r'] ** 2 + 2.0 * max(info['e_f'], info['e_r']) ** 2)
        smooth_penalties.append(info['smooth_penalty'])
        n += 1
    tracking_terms = np.array(tracking_terms)
    smooth_penalties = np.array(smooth_penalties)
    ratio_mean = smooth_penalties.mean() / max(tracking_terms.mean(), 1e-9)
    print(f"-- {label} -- steps={n}")
    print(f"   tracking term: mean={tracking_terms.mean():.5f} median={np.median(tracking_terms):.5f} "
          f"p90={np.percentile(tracking_terms, 90):.5f} max={tracking_terms.max():.5f}")
    print(f"   smooth_penalty: mean={smooth_penalties.mean():.5f} median={np.median(smooth_penalties):.5f} "
          f"p90={np.percentile(smooth_penalties, 90):.5f} max={smooth_penalties.max():.5f}")
    print(f"   ratio of means (smooth_penalty / tracking_term): {ratio_mean:.4f}")
    return ratio_mean


ckpt_path = os.path.join('Paper_2', 'artifacts', 'models', 'p2e9_seeds', 'seed11_ep200')
ratio_a = run_case("Case A: seed11 ep200, train pool (typical/converged)", ckpt_path,
                    'train', 11, None, 1500)

seed44_ckpt = os.path.join('Paper_2', 'artifacts', 'models', 'p2e9_seeds', 'seed44_ep600')
gen_scenario = VALIDATION_SCENARIOS[0]  # dict(kind='gen', gen='GENROU_6', rho=0.60, lambda_L=0.95) -- DEC-P2-039/040 known-oscillatory case
print(f"gen_scenario (Case B, known-oscillatory per DEC-P2-039/040): {gen_scenario}")
ratio_b = run_case("Case B: seed44 ep600 (best), GEN validation scenario (known-oscillatory)",
                    seed44_ckpt, 'train', 44, gen_scenario, 1200)

print(f"\nSTEP 2 RESULT: informational -- Case A ratio={ratio_a:.4f}, Case B ratio={ratio_b:.4f}. "
      f"Expect same order of magnitude in the regime the penalty needs to act (Case B), not >>1 or <<0.01.")
