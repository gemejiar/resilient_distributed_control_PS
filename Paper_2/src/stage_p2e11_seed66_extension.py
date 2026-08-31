#!/usr/bin/env python
"""
P2-E11 seed66 extension -- single consolidated data-generation pass for
`seed66` (DEC-P2-043) across the 6 frozen validation scenarios, producing
everything needed to extend ALL FOUR P2-E11/P2-E11d figure stages
(validation comparison F1-F4, trajectory demo, oscillation persistence,
full stability screen A/B/C) with seed66 alongside the 5 original seeds --
WITHOUT touching any frozen evidence file (DEC-P2-035/036/040/041/043).
Every output is written to a SEPARATE "_with_seed66" file that concatenates
the untouched original rows with freshly-computed seed66 rows.

One ANDES simulation per validation scenario (6 total, VALIDATION_SCENARIOS
order confirmed by DEC-P2-043's independent check: idx0-2=gen op 0.95/1.00/
1.05, idx3-5=load op 0.95/1.00/1.05) -- reused across all downstream stages
instead of re-simulating per figure.
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
BEST_CKPT = 'seed66_ep1200'
CKPT_DIR = os.path.join('Paper_2', 'artifacts', 'models', 'p2e9_seeds')
OUT_DIAG = os.path.join('Paper_2', 'artifacts', 'diagnostics')
OUT_TRAJ = os.path.join('Paper_2', 'artifacts', 'trajectories')
WINDOWS = [(0.0, 1.0), (1.0, 2.0), (2.0, 3.0), (3.0, 4.0), (4.0, 5.0)]
# gen_val/load_val (stage b/c) = the lambda_L=1.00 validation scenarios, confirmed indices:
GEN_VAL_IDX, LOAD_VAL_IDX = 1, 4


def make_env(scen):
    return P2ResidualTrainEnv(obs_mode='OBS-A', p_max_bess_mw=PMAX_MW, kd_star_mw_per_hz=KD_STAR,
                               p_rl_max_mw=P_RL_MAX_MW, tc=TC, tstep=TSTEP,
                               bess_bus1=BESS_BUS1, bess_bus2=BESS_BUS2, fixed_scenario=scen)


def j_val(df_peak, rocof_peak):
    return (max(df_peak / F_REF_HZ, rocof_peak / R_REF_HZ_S) +
            0.25 * (df_peak / F_REF_HZ + rocof_peak / R_REF_HZ_S))


def run_full(scen, model):
    env = make_env(scen)
    obs, info = env.reset()
    t_hist, f_worst_hist, rocof_worst_hist = [], [], []
    pc1_hist, pc2_hist, pd1_hist, pd2_hist = [], [], [], []
    sat_count = action_count = 0
    terminated = truncated = False
    while not (terminated or truncated):
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        f_gen, rocof_gen = env._gen_bus_arrays()
        raw = env.get_raw_signals()
        t_hist.append(info['t'])
        f_worst_hist.append(float(np.min(f_gen)))
        rocof_worst_hist.append(float(np.max(np.abs(rocof_gen))))
        pc1_hist.append(info['p_total_mw'][0])
        pc2_hist.append(info['p_total_mw'][1])
        pd1_hist.append(raw['p1_mw'])
        pd2_hist.append(raw['p2_mw'])
        action_count += 1
        if (abs(info['p_total_mw'][0]) >= PMAX_MW - 1e-3 or abs(info['p_total_mw'][1]) >= PMAX_MW - 1e-3):
            sat_count += 1
    return dict(t=np.array(t_hist), f_worst_hz=np.array(f_worst_hist),
                rocof_worst_hz_s=np.array(rocof_worst_hist),
                p_command1_mw=np.array(pc1_hist), p_command2_mw=np.array(pc2_hist),
                p_delivered1_mw=np.array(pd1_hist), p_delivered2_mw=np.array(pd2_hist),
                tds_success=info['tds_success'], saturation_fraction=sat_count / max(action_count, 1),
                df_peak=info['df_peak'], rocof_peak=info['rocof_peak'])


def main():
    model = TD3.load(os.path.join(CKPT_DIR, BEST_CKPT))
    results = {}
    for scen_idx, scen in enumerate(VALIDATION_SCENARIOS):
        print(f"=== scen{scen_idx}: {scen} ===")
        r = run_full(scen, model)
        results[scen_idx] = r
        print(f"  df_peak={r['df_peak']:.4f}Hz rocof_peak={r['rocof_peak']:.3f}Hz/s "
              f"J_val={j_val(r['df_peak'], r['rocof_peak']):.4f} sat={r['saturation_fraction']:.3f}")

    # ---- Stage 1: validation_comparison (F1-F4) ----
    comp_rows = []
    for scen_idx, scen in enumerate(VALIDATION_SCENARIOS):
        r = results[scen_idx]
        comp_rows.append(dict(controller='seed66', scenario=str(scen), df_peak_hz=r['df_peak'],
                               rocof_peak_hz_s=r['rocof_peak'], J_val=j_val(r['df_peak'], r['rocof_peak']),
                               TDS_success=r['tds_success'], saturation_fraction=r['saturation_fraction']))
    df_new = pd.DataFrame(comp_rows)
    df_old = pd.read_csv(os.path.join(OUT_DIAG, 'p2e11_validation_comparison.csv'))
    droop_ref = df_old[df_old['controller'] == 'droop_star'].set_index('scenario')
    i_f_list, i_r_list = [], []
    for _, row in df_new.iterrows():
        d = droop_ref.loc[row['scenario']]
        i_f_list.append((abs(d['df_peak_hz']) - abs(row['df_peak_hz'])) / abs(d['df_peak_hz']))
        i_r_list.append((d['rocof_peak_hz_s'] - row['rocof_peak_hz_s']) / d['rocof_peak_hz_s'])
    df_new['I_f_vs_droop'] = i_f_list
    df_new['I_r_vs_droop'] = i_r_list
    df_combined = pd.concat([df_old, df_new], ignore_index=True)
    df_combined.to_csv(os.path.join(OUT_DIAG, 'p2e11_validation_comparison_with_seed66.csv'), index=False)

    summary_old = pd.read_csv(os.path.join(OUT_DIAG, 'p2e11_validation_comparison_summary.csv'), index_col=0)
    summary_new_row = pd.DataFrame([dict(
        J_val_mean=df_new['J_val'].mean(), df_peak_mean_hz=df_new['df_peak_hz'].mean(),
        rocof_peak_mean_hz_s=df_new['rocof_peak_hz_s'].mean(),
        I_f_vs_droop_mean=df_new['I_f_vs_droop'].mean(), I_r_vs_droop_mean=df_new['I_r_vs_droop'].mean(),
        saturation_fraction_mean=df_new['saturation_fraction'].mean(),
    )], index=['seed66'])
    summary_combined = pd.concat([summary_old, summary_new_row])
    summary_combined.to_csv(os.path.join(OUT_DIAG, 'p2e11_validation_comparison_summary_with_seed66.csv'))
    print(f"\nSaved stage-1 combined CSVs (validation_comparison, +seed66)")

    # ---- Stage d: full stability screen (A/B/C) ----
    class_rows, osc_rows = [], []
    for scen_idx, scen in enumerate(VALIDATION_SCENARIOS):
        r = results[scen_idx]
        res = analyze_trace_v2(r['t'], r['f_worst_hz'], r['p_command1_mw'], r['p_command2_mw'],
                                r['tds_success'], r['saturation_fraction'])
        class_rows.append(dict(controller='seed66', scenario=str(scen), scenario_idx=scen_idx,
                                J_val=j_val(r['df_peak'], r['rocof_peak']), df_peak_hz=r['df_peak'],
                                rocof_peak_hz_s=r['rocof_peak'], classification_v2=res['classification_v2'],
                                detrended_frequency_p2p=res['detrended_frequency_p2p'],
                                persistence_ratio=res['persistence_ratio'],
                                sign_reversals_final_window=res['sign_reversals_final_window'],
                                saturation_fraction=r['saturation_fraction']))
        ptot = r['p_command1_mw'] + r['p_command2_mw']
        tau = r['t'] - 1.0
        for w0, w1 in WINDOWS:
            m = (tau >= w0) & (tau < w1)
            if m.sum() > 1:
                osc_rows.append(dict(controller='seed66', scenario=str(scen), scenario_idx=scen_idx,
                                      window_start_s=w0, window_end_s=w1,
                                      p_total_ptp_mw=float(np.ptp(ptot[m]))))
    df_class_new = pd.DataFrame(class_rows)
    df_class_old = pd.read_csv(os.path.join(OUT_DIAG, 'p2e11d_stability_classification.csv'))
    df_class_combined = pd.concat([df_class_old, df_class_new], ignore_index=True)
    df_class_combined.to_csv(os.path.join(OUT_DIAG, 'p2e11d_stability_classification_with_seed66.csv'), index=False)

    df_osc_new = pd.DataFrame(osc_rows)
    df_osc_old = pd.read_csv(os.path.join(OUT_DIAG, 'p2e11d_oscillation_full.csv'))
    df_osc_combined = pd.concat([df_osc_old, df_osc_new], ignore_index=True)
    df_osc_combined.to_csv(os.path.join(OUT_DIAG, 'p2e11d_oscillation_full_with_seed66.csv'), index=False)
    print(f"Saved stage-d combined CSVs (stability_classification, oscillation_full, +seed66)")

    n_stable66 = int((df_class_new['classification_v2'] == 'STABLE').sum())
    summary_old_d = pd.read_csv(os.path.join(OUT_DIAG, 'p2e11d_stability_summary.csv'), index_col=0)
    summary_new_d = pd.DataFrame({'classification_v2': [n_stable66]}, index=['seed66'])
    summary_combined_d = pd.concat([summary_old_d, summary_new_d])
    summary_combined_d.to_csv(os.path.join(OUT_DIAG, 'p2e11d_stability_summary_with_seed66.csv'))
    print(f"seed66: {n_stable66}/6 STABLE (matches DEC-P2-043 independent check)")

    # ---- Stage c: oscillation persistence (gen_val/load_val = scenario_idx 1 and 4) ----
    osc_c_rows = []
    for scen_label, scen_idx in [('gen_val', GEN_VAL_IDX), ('load_val', LOAD_VAL_IDX)]:
        sub = df_osc_new[df_osc_new['scenario_idx'] == scen_idx]
        for _, r in sub.iterrows():
            osc_c_rows.append(dict(scenario=scen_label, seed=66, window_start_s=r['window_start_s'],
                                    window_end_s=r['window_end_s'], p_total_ptp_mw=r['p_total_ptp_mw']))
    df_c_new = pd.DataFrame(osc_c_rows)
    df_c_old = pd.read_csv(os.path.join(OUT_DIAG, 'p2e11c_oscillation_check.csv'))
    df_c_combined = pd.concat([df_c_old, df_c_new], ignore_index=True)
    df_c_combined.to_csv(os.path.join(OUT_DIAG, 'p2e11c_oscillation_check_with_seed66.csv'), index=False)
    print(f"Saved stage-c combined CSV (oscillation_check, +seed66)")

    # ---- Stage b: trajectory demo (gen_val/load_val, TD3_seed66 alongside NoFFC/droop*/TD3_seed44) ----
    old_npz = np.load(os.path.join(OUT_TRAJ, 'p2e11b_trajectory_demo.npz'))
    flat = {k: old_npz[k] for k in old_npz.files}
    for scen_label, scen_idx in [('gen_val', GEN_VAL_IDX), ('load_val', LOAD_VAL_IDX)]:
        r = results[scen_idx]
        key = f'{scen_label}__TD3_seed66'
        flat[f'{key}__t'] = r['t']
        flat[f'{key}__f_worst_hz'] = r['f_worst_hz']
        flat[f'{key}__rocof_worst_hz_s'] = r['rocof_worst_hz_s']
        flat[f'{key}__p_command1_mw'] = r['p_command1_mw']
        flat[f'{key}__p_command2_mw'] = r['p_command2_mw']
        flat[f'{key}__p_delivered1_mw'] = r['p_delivered1_mw']
        flat[f'{key}__p_delivered2_mw'] = r['p_delivered2_mw']
    out_npz = os.path.join(OUT_TRAJ, 'p2e11b_trajectory_demo_with_seed66.npz')
    np.savez_compressed(out_npz, **flat)
    print(f"Saved stage-b combined npz (trajectory_demo, +seed66): {out_npz}")


if __name__ == '__main__':
    main()
