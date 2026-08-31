#!/usr/bin/env python
"""Independent post-hoc verification of seed66's best checkpoint
(seed66_ep1200, DEC-P2-043) against the SAME full stability-screen
methodology already used for seeds 11-55 (DEC-P2-040,
stage_p2e11d_full_stability_screen.py) -- reuses run_full/j_val from that
module UNMODIFIED, fresh checkpoint reload, fresh env, fresh classify_v2
calls (not a re-read of the training-time diag_log). Writes to a
SEPARATELY-named output file; does NOT touch the frozen DEC-P2-040 evidence
(p2e11d_stability_classification.csv etc, 5-seed data).
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p2_env_train import VALIDATION_SCENARIOS
from stage_p2e11d_full_stability_screen import KD_STAR, run_full, j_val
from stage_p2e5b_fr_grid_corrected import analyze_trace_v2
from stable_baselines3 import TD3

CKPT_DIR = os.path.join('Paper_2', 'artifacts', 'models', 'p2e9_seeds')
OUT_DIAG = os.path.join('Paper_2', 'artifacts', 'diagnostics')
BEST_CKPT = 'seed66_ep1200'

model = TD3.load(os.path.join(CKPT_DIR, BEST_CKPT))
rows = []
for scen_idx, scen in enumerate(VALIDATION_SCENARIOS):
    r = run_full(scen, KD_STAR, model)
    res = analyze_trace_v2(r['t'], r['f_worst_hz'], r['p_command1_mw'], r['p_command2_mw'],
                            r['tds_success'], r['saturation_fraction'])
    jv = j_val(r['df_peak'], r['rocof_peak'])
    rows.append(dict(controller='seed66', scenario=str(scen), scenario_idx=scen_idx,
                      J_val=jv, df_peak_hz=r['df_peak'], rocof_peak_hz_s=r['rocof_peak'],
                      classification_v2=res['classification_v2'],
                      detrended_frequency_p2p=res['detrended_frequency_p2p'],
                      persistence_ratio=res['persistence_ratio'],
                      sign_reversals_final_window=res['sign_reversals_final_window'],
                      saturation_fraction=r['saturation_fraction']))
    print(f"  scen{scen_idx} seed66       J_val={jv:.4f} class={res['classification_v2']:14s} "
          f"detrended_p2p={res['detrended_frequency_p2p']*1000:.2f}mHz sat={r['saturation_fraction']:.3f}")

df = pd.DataFrame(rows)
out_path = os.path.join(OUT_DIAG, 'p2e11d_stability_classification_seed66.csv')
df.to_csv(out_path, index=False)
n_stable = int((df['classification_v2'] == 'STABLE').sum())
print(f"\nSaved: {out_path}")
print(f"seed66 ({BEST_CKPT}): {n_stable}/6 STABLE, mean J_val={df['J_val'].mean():.4f}")
