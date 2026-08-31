#!/usr/bin/env python
"""
P2-E9 -- training loop infrastructure: periodic validation, checkpoint
selection by minimum J_val_P2 ONLY, and early stopping exactly per plan
Section 19 (no earlier than 2000 episodes, patience=5 consecutive
evaluations without improvement). This is new infrastructure -- P2-E6b's
short ablation and P2-E8's smoke TD3 never exercised checkpointing/
early-stopping, only raw model.learn() for a fixed short budget.

Checkpoint selection is EXCLUSIVELY by min J_val_P2 (plan Section 7).
Training return, actor loss, critic loss, Ppeak, energy, and
saturation_fraction are logged for DIAGNOSTIC purposes only and NEVER used
to select a checkpoint or to stop a seed early (explicit user instruction,
DEC-P2-035 authorization).
"""
import os
import time

import numpy as np
import pandas as pd
from stable_baselines3.common.callbacks import BaseCallback

from p2_env_train import P2ResidualTrainEnv, VALIDATION_SCENARIOS, F_REF_HZ, R_REF_HZ_S
from stage_p2e5b_fr_grid_corrected import analyze_trace_v2

STEPS_PER_EPISODE = 1200  # tf=6.0s / tstep=5ms, plan Section 19


class P2ValidationCallback(BaseCallback):
    """Every `eval_freq_episodes` episodes: evaluate deterministic policy on
    the 6 frozen validation scenarios, compute J_val_P2(global), save a
    checkpoint, track the best (minimum) J_val_P2 seen, and apply early
    stopping (floor `min_episodes_before_stop`, patience
    `patience_evals`) -- exactly plan Section 19, no earlier trigger, no
    HPO-driven adjustment."""

    def __init__(self, seed, ckpt_dir, log_dir, eval_freq_episodes=200,
                 min_episodes_before_stop=2000, patience_evals=5,
                 max_episodes_safety_cap=6000, pmax_mw=293.4, kd_star=4694.4,
                 p_rl_max_mw=73.35, tc=0.005, tstep=0.005, bess_bus1=16, bess_bus2=20,
                 verbose=0, action_smoothness_weight=0.0, require_stability_for_best=False):
        super().__init__(verbose)
        self.seed = seed
        self.ckpt_dir = ckpt_dir
        self.log_dir = log_dir
        os.makedirs(ckpt_dir, exist_ok=True)
        os.makedirs(log_dir, exist_ok=True)
        self.eval_freq_steps = eval_freq_episodes * STEPS_PER_EPISODE
        self.min_steps_before_stop = min_episodes_before_stop * STEPS_PER_EPISODE
        self.patience_evals = patience_evals
        self.max_steps_safety_cap = max_episodes_safety_cap * STEPS_PER_EPISODE
        self.env_kwargs = dict(p_max_bess_mw=pmax_mw, kd_star_mw_per_hz=kd_star,
                                p_rl_max_mw=p_rl_max_mw, tc=tc, tstep=tstep,
                                bess_bus1=bess_bus1, bess_bus2=bess_bus2,
                                action_smoothness_weight=action_smoothness_weight)
        # seed66 (DEC-P2-041 pending): stability-gated checkpoint eligibility, OFF by default
        # (False reproduces exactly the min-J_val_P2-only selection used by seeds 11-55).
        # Reuses analyze_trace_v2/classify_v2 UNMODIFIED (DEC-P2-017, already validated for the
        # physical controller's STOP-P2-A Criterion 2) -- not a new ad-hoc criterion.
        self.require_stability_for_best = require_stability_for_best

        self.best_j_val = float('inf')
        self.best_ckpt_path = None
        self.best_episode = None
        self.evals_since_improvement = 0
        self.last_eval_step = 0
        self.eval_log = []
        self.diag_log = []
        self.numerical_failures = 0
        self.stopped_early = False
        self.stop_reason = None
        self._t_start = None

    def _init_callback(self):
        self._t_start = time.perf_counter()

    def _on_step(self):
        if self.locals.get('infos'):
            for info in self.locals['infos']:
                if info.get('tds_success') is False:
                    self.numerical_failures += 1

        if self.num_timesteps - self.last_eval_step < self.eval_freq_steps:
            return True
        self.last_eval_step = self.num_timesteps
        self._evaluate_and_checkpoint()

        if (self.num_timesteps >= self.min_steps_before_stop and
                self.evals_since_improvement >= self.patience_evals):
            self.stopped_early = True
            self.stop_reason = (f'early_stopping (plan SS19: >= 2000 episodios, patience=5 sin '
                                 f'mejora de J_val_P2, cumplido en step={self.num_timesteps})')
            if self.verbose:
                print(f"  [seed {self.seed}] EARLY STOP: {self.stop_reason}")
            return False
        if self.num_timesteps >= self.max_steps_safety_cap:
            self.stopped_early = True
            self.stop_reason = (f'max_episodes_safety_cap alcanzado (step={self.num_timesteps}) -- '
                                 f'tope de seguridad de ingenieria, NO parte de la regla de early '
                                 f'stopping del plan SS19, documentado explicitamente como distinto')
            if self.verbose:
                print(f"  [seed {self.seed}] STOP (safety cap): {self.stop_reason}")
            return False
        return True

    def _evaluate_and_checkpoint(self):
        episode_num = self.num_timesteps // STEPS_PER_EPISODE
        rows = []
        for scen in VALIDATION_SCENARIOS:
            env = P2ResidualTrainEnv(obs_mode='OBS-A', fixed_scenario=scen,
                                      seed=self.seed, **self.env_kwargs)
            obs, info = env.reset()
            terminated = truncated = False
            sat_count = action_count = 0
            t_hist, f_worst_hist, pc1_hist, pc2_hist = [], [], [], []
            while not (terminated or truncated):
                action, _ = self.model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = env.step(action)
                action_count += 1
                if (abs(info['p_total_mw'][0]) >= self.env_kwargs['p_max_bess_mw'] - 1e-3 or
                        abs(info['p_total_mw'][1]) >= self.env_kwargs['p_max_bess_mw'] - 1e-3):
                    sat_count += 1
                if self.require_stability_for_best:
                    f_gen, _ = env._gen_bus_arrays()
                    t_hist.append(info['t']); f_worst_hist.append(float(np.min(f_gen)))
                    pc1_hist.append(info['p_total_mw'][0]); pc2_hist.append(info['p_total_mw'][1])
            df_peak, rocof_peak = info['df_peak'], info['rocof_peak']
            j_val = (max(df_peak / F_REF_HZ, rocof_peak / R_REF_HZ_S) +
                     0.25 * (df_peak / F_REF_HZ + rocof_peak / R_REF_HZ_S))
            sat_frac = sat_count / max(action_count, 1)
            row = dict(scenario=str(scen), df_peak_hz=df_peak, rocof_peak_hz_s=rocof_peak,
                       J_val=j_val, TDS_success=info['tds_success'], saturation_fraction=sat_frac)
            if self.require_stability_for_best:
                res = analyze_trace_v2(np.array(t_hist), np.array(f_worst_hist),
                                        np.array(pc1_hist), np.array(pc2_hist),
                                        info['tds_success'], sat_frac)
                row['classification_v2'] = res['classification_v2']
            rows.append(row)
        df = pd.DataFrame(rows)
        j_val_global = float(df['J_val'].mean())
        all_stable = bool((df['classification_v2'] == 'STABLE').all()) if self.require_stability_for_best else None

        ckpt_path = os.path.join(self.ckpt_dir, f'seed{self.seed}_ep{episode_num}')
        self.model.save(ckpt_path)

        eligible = (j_val_global < self.best_j_val) and (not self.require_stability_for_best or all_stable)
        improved = eligible
        if improved:
            self.best_j_val = j_val_global
            self.best_ckpt_path = ckpt_path
            self.best_episode = episode_num
            self.evals_since_improvement = 0
        else:
            self.evals_since_improvement += 1

        # diagnostics (NOT used for selection) from SB3's own logger
        actor_loss = self.model.logger.name_to_value.get('train/actor_loss', float('nan'))
        critic_loss = self.model.logger.name_to_value.get('train/critic_loss', float('nan'))
        ep_return = self.model.logger.name_to_value.get('rollout/ep_rew_mean', float('nan'))

        self.eval_log.append(dict(
            seed=self.seed, episode=episode_num, step=self.num_timesteps, J_val_P2=j_val_global,
            df_peak_mean_hz=float(df['df_peak_hz'].mean()), rocof_peak_mean_hz_s=float(df['rocof_peak_hz_s'].mean()),
            checkpoint_path=ckpt_path, improved=improved,
            evals_since_improvement=self.evals_since_improvement,
            wall_time_s=time.perf_counter() - self._t_start,
        ))
        diag_row = dict(
            seed=self.seed, episode=episode_num, step=self.num_timesteps,
            actor_loss=actor_loss, critic_loss=critic_loss, episode_return_mean=ep_return,
            replay_buffer_pos=self.model.replay_buffer.pos, numerical_failures_cumulative=self.numerical_failures,
            saturation_fraction_mean=float(df['saturation_fraction'].mean()),
        )
        if self.require_stability_for_best:
            # seed66 (DEC-P2-041 pending): per-eval stability breakdown, diagnostic only (NOT used
            # for selection beyond the all_stable gate already applied above) -- without this, a
            # rejected-for-instability checkpoint leaves no record of WHICH of the 6 scenarios broke.
            diag_row['n_stable_of_6'] = int((df['classification_v2'] == 'STABLE').sum())
            diag_row['all_stable'] = all_stable
            diag_row['unstable_scenarios'] = ';'.join(
                df.loc[df['classification_v2'] != 'STABLE', 'scenario'].tolist())
        self.diag_log.append(diag_row)
        if self.verbose:
            print(f"  [seed {self.seed}] ep={episode_num} step={self.num_timesteps} "
                  f"J_val_P2={j_val_global:.4f} {'(mejor)' if improved else f'(sin mejora x{self.evals_since_improvement})'}")

    def save_logs(self):
        eval_csv = os.path.join(self.log_dir, f'seed{self.seed}_eval_log.csv')
        diag_csv = os.path.join(self.log_dir, f'seed{self.seed}_diag_log.csv')
        pd.DataFrame(self.eval_log).to_csv(eval_csv, index=False)
        pd.DataFrame(self.diag_log).to_csv(diag_csv, index=False)
        return eval_csv, diag_csv
