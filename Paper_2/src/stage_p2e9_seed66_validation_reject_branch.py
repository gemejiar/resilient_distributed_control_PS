#!/usr/bin/env python
"""seed66 pre-training validation, gap-fill for step 3 (DEC-P2-041): the
seed=999/3-episode dry-run (stage_p2e9_seed66_validation_stability_dryrun.py)
never produced an unstable scenario (the untrained policy stayed close to
droop*-only behavior, which is STABLE in all 6 scenarios per DEC-P2-040), so
the REJECTION branch of the stability gate (J_val_P2 improves but not all 6
scenarios are STABLE -> must NOT count as "improved") was never exercised.

This forces that branch via a monkeypatch of analyze_trace_v2 (the first
evaluated scenario forced to LIMIT_CYCLE) on a real, fast evaluation
(seed11 ep200, no training needed) and confirms the callback correctly
refuses to accept the checkpoint as "best" even when best_j_val is set to
an artificially high sentinel that GUARANTEES a J_val-only "improvement".

Result on the real seed11 ep200 checkpoint: besides the one forced
scenario, 2 further GEN scenarios independently classified non-STABLE at
this very early checkpoint (n_stable_of_6=3, not the 5 naively expected
from forcing only 1) -- a real property of this early/undertrained
checkpoint, not a code defect (analyze_trace_v2 was called exactly 6
times, matching the 6 validation scenarios). The correctness check below
uses the invariants that actually matter (not all_stable -> not improved,
best_j_val/best_ckpt_path left untouched), not the originally over-specific
"exactly 5 stable" assumption.
"""
import os
import sys
import time

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'Paper_2', 'src'))
os.chdir(REPO)

import p2_train_callback
from p2_env_train import P2ResidualTrainEnv
from p2_train_callback import P2ValidationCallback
from stable_baselines3 import TD3
from stable_baselines3.common.logger import configure as _configure_logger

PMAX_MW, KD_STAR, P_RL_MAX_MW, TC, TSTEP = 293.4, 4694.4, 73.35, 0.005, 0.005
BESS_BUS1, BESS_BUS2 = 16, 20

ckpt_path = os.path.join('Paper_2', 'artifacts', 'models', 'p2e9_seeds', 'seed11_ep200')
env0 = P2ResidualTrainEnv(obs_mode='OBS-A', p_max_bess_mw=PMAX_MW, kd_star_mw_per_hz=KD_STAR,
                           p_rl_max_mw=P_RL_MAX_MW, tc=TC, tstep=TSTEP,
                           bess_bus1=BESS_BUS1, bess_bus2=BESS_BUS2,
                           scenario_pool='train', seed=11)
model = TD3.load(ckpt_path, env=env0)
model._logger = _configure_logger(folder=None, format_strings=[])

_real_analyze = p2_train_callback.analyze_trace_v2
_call_count = {'n': 0}


def _forced_analyze(t, f, pcmd1, pcmd2, tds_success, saturation_fraction):
    _call_count['n'] += 1
    res = _real_analyze(t, f, pcmd1, pcmd2, tds_success, saturation_fraction)
    if _call_count['n'] == 1:
        res = dict(res)
        res['classification_v2'] = 'LIMIT_CYCLE'
    return res


p2_train_callback.analyze_trace_v2 = _forced_analyze

cb = P2ValidationCallback(seed=11, ckpt_dir=os.path.join('c:\\tmp\\seed66_dryrun', 'reject_ckpt'),
                           log_dir=os.path.join('c:\\tmp\\seed66_dryrun', 'reject_log'),
                           pmax_mw=PMAX_MW, kd_star=KD_STAR, p_rl_max_mw=P_RL_MAX_MW,
                           tc=TC, tstep=TSTEP, bess_bus1=BESS_BUS1, bess_bus2=BESS_BUS2,
                           verbose=1, action_smoothness_weight=0.0,
                           require_stability_for_best=True)
cb.model = model
cb.num_timesteps = 200 * 1200
cb.best_j_val = 999.0  # force "would improve" so only the stability gate can block eligibility
cb._t_start = time.perf_counter()
cb._evaluate_and_checkpoint()

row = cb.eval_log[-1]
diag_row = cb.diag_log[-1]
print(f"scenarios evaluated (analyze_trace_v2 calls): {_call_count['n']} (expect 6)")
print(f"J_val_P2={row['J_val_P2']:.4f}  best_j_val_before=999.0 (guaranteed 'improvement' by J_val alone)")
print(f"n_stable_of_6={diag_row['n_stable_of_6']}  all_stable={diag_row['all_stable']}  "
      f"unstable_scenarios='{diag_row['unstable_scenarios']}'")
print(f"improved (eval_log)={row['improved']}")
print(f"cb.best_j_val after call={cb.best_j_val} (should STILL be 999.0 -- unchanged, checkpoint rejected)")
print(f"cb.best_ckpt_path={cb.best_ckpt_path} (should be None -- never accepted)")

ok = (diag_row['n_stable_of_6'] < 6 and diag_row['all_stable'] is False and
      row['improved'] is False and cb.best_j_val == 999.0 and cb.best_ckpt_path is None)
print(f"\nREJECTION-BRANCH CHECK: {'PASS' if ok else 'FAIL'}")

p2_train_callback.analyze_trace_v2 = _real_analyze
