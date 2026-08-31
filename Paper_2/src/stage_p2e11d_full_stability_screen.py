#!/usr/bin/env python
"""
P2-E11d -- Options 1+2 (user-authorized): (1) extend the oscillation check
from 2 to all 6 validation scenarios; (2) apply the ALREADY-VALIDATED
stability classifier (classify_v2/analyze_trace_v2, DEC-P2-017, used
throughout P2-E5 to certify STOP-P2-A Criterion 2 "sin oscilacion
sostenida" for the physical controller) to the TD3 policies -- reusing the
existing methodology, not inventing a new ad-hoc criterion. No retraining,
no checkpoint reselection -- purely a post-hoc screen of the 5 ALREADY
FROZEN checkpoints (DEC-P2-036).

For NoFFC, droop*, and the 5 frozen TD3 checkpoints, on all 6 validation
scenarios: full f_worst_hz/p_command trajectory, J_val_P2 (SS7),
classify_v2 (STABLE/MARGINAL/LIMIT_CYCLE), and per-window command
oscillation amplitude (persistence check).
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p2_env_train import P2ResidualTrainEnv, VALIDATION_SCENARIOS, F_REF_HZ, R_REF_HZ_S
from stage_p2e5b_fr_grid_corrected import analyze_trace_v2
from stable_baselines3 import TD3

PMAX_MW = 293.4
KD_STAR = 4694.4
P_RL_MAX_MW = 73.35
TC = TSTEP = 0.005
BESS_BUS1, BESS_BUS2 = 16, 20
SEED_CKPT = {11: 'seed11_ep400', 22: 'seed22_ep1600', 33: 'seed33_ep400',
             44: 'seed44_ep600', 55: 'seed55_ep1400'}
CKPT_DIR = os.path.join('Paper_2', 'artifacts', 'models', 'p2e9_seeds')
OUT_DIAG = os.path.join('Paper_2', 'artifacts', 'diagnostics')
WINDOWS = [(0.0, 1.0), (1.0, 2.0), (2.0, 3.0), (3.0, 4.0), (4.0, 5.0)]


def make_env(scen, kd_star):
    return P2ResidualTrainEnv(obs_mode='OBS-A', p_max_bess_mw=PMAX_MW, kd_star_mw_per_hz=kd_star,
                               p_rl_max_mw=P_RL_MAX_MW, tc=TC, tstep=TSTEP,
                               bess_bus1=BESS_BUS1, bess_bus2=BESS_BUS2, fixed_scenario=scen)


def run_full(scen, kd_star, model):
    env = make_env(scen, kd_star)
    obs, info = env.reset()
    t_hist, f_worst_hist, pc1_hist, pc2_hist = [], [], [], []
    sat_count = action_count = 0
    terminated = truncated = False
    while not (terminated or truncated):
        action = model.predict(obs, deterministic=True)[0] if model is not None else np.zeros(2)
        obs, reward, terminated, truncated, info = env.step(action)
        f_gen, rocof_gen = env._gen_bus_arrays()
        t_hist.append(info['t'])
        f_worst_hist.append(float(np.min(f_gen)))
        pc1_hist.append(info['p_total_mw'][0])
        pc2_hist.append(info['p_total_mw'][1])
        action_count += 1
        if (abs(info['p_total_mw'][0]) >= PMAX_MW - 1e-3 or abs(info['p_total_mw'][1]) >= PMAX_MW - 1e-3):
            sat_count += 1
    return dict(t=np.array(t_hist), f_worst_hz=np.array(f_worst_hist),
                p_command1_mw=np.array(pc1_hist), p_command2_mw=np.array(pc2_hist),
                tds_success=info['tds_success'], saturation_fraction=sat_count / max(action_count, 1),
                df_peak=info['df_peak'], rocof_peak=info['rocof_peak'])


def j_val(df_peak, rocof_peak):
    return (max(df_peak / F_REF_HZ, rocof_peak / R_REF_HZ_S) +
            0.25 * (df_peak / F_REF_HZ + rocof_peak / R_REF_HZ_S))


def main():
    controllers = [('NoFFC', 0.0, None), ('droop_star', KD_STAR, None)]
    models = {}
    for seed, ckpt in SEED_CKPT.items():
        models[seed] = TD3.load(os.path.join(CKPT_DIR, ckpt))
        controllers.append((f'seed{seed}', KD_STAR, models[seed]))

    class_rows, osc_rows = [], []
    for scen_idx, scen in enumerate(VALIDATION_SCENARIOS):
        for ctrl_label, kd, model in controllers:
            r = run_full(scen, kd, model)
            res = analyze_trace_v2(r['t'], r['f_worst_hz'], r['p_command1_mw'], r['p_command2_mw'],
                                    r['tds_success'], r['saturation_fraction'])
            jv = j_val(r['df_peak'], r['rocof_peak'])
            class_rows.append(dict(controller=ctrl_label, scenario=str(scen), scenario_idx=scen_idx,
                                    J_val=jv, df_peak_hz=r['df_peak'], rocof_peak_hz_s=r['rocof_peak'],
                                    classification_v2=res['classification_v2'],
                                    detrended_frequency_p2p=res['detrended_frequency_p2p'],
                                    persistence_ratio=res['persistence_ratio'],
                                    sign_reversals_final_window=res['sign_reversals_final_window'],
                                    saturation_fraction=r['saturation_fraction']))
            print(f"  scen{scen_idx} {ctrl_label:12s} J_val={jv:.4f} class={res['classification_v2']:14s} "
                  f"detrended_p2p={res['detrended_frequency_p2p']*1000:.2f}mHz sat={r['saturation_fraction']:.3f}")

            ptot = r['p_command1_mw'] + r['p_command2_mw']
            tau = r['t'] - 1.0
            for w0, w1 in WINDOWS:
                m = (tau >= w0) & (tau < w1)
                if m.sum() > 1:
                    osc_rows.append(dict(controller=ctrl_label, scenario=str(scen), scenario_idx=scen_idx,
                                          window_start_s=w0, window_end_s=w1,
                                          p_total_ptp_mw=float(np.ptp(ptot[m]))))

    df_class = pd.DataFrame(class_rows)
    df_osc = pd.DataFrame(osc_rows)
    df_class.to_csv(os.path.join(OUT_DIAG, 'p2e11d_stability_classification.csv'), index=False)
    df_osc.to_csv(os.path.join(OUT_DIAG, 'p2e11d_oscillation_full.csv'), index=False)
    print(f"\nSaved: p2e11d_stability_classification.csv, p2e11d_oscillation_full.csv")

    print("\n=== Resumen: cuantos escenarios (de 6) clasifican STABLE, por controlador ===")
    summary = df_class.groupby('controller')['classification_v2'].apply(
        lambda s: (s == 'STABLE').sum()).reindex(['NoFFC', 'droop_star'] + [f'seed{s}' for s in SEED_CKPT])
    print(summary.to_string())
    summary.to_csv(os.path.join(OUT_DIAG, 'p2e11d_stability_summary.csv'))


if __name__ == '__main__':
    main()
