#!/usr/bin/env python
"""
P2-E11c -- follow-up diagnostic (not requested, found during P2-E11b's
trajectory demo): check whether the growing command oscillation seen in
seed44's gen_val trajectory is present in the other 4 seeds too, and
whether it appears in load_val as well. Validation-split only.

Not a checkpoint reselection, not a retraining -- purely a diagnostic
measurement to report honestly to the user before any decision is made.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p2_env_train import P2ResidualTrainEnv
from stable_baselines3 import TD3

PMAX_MW = 293.4
KD_STAR = 4694.4
P_RL_MAX_MW = 73.35
TC = TSTEP = 0.005
BESS_BUS1, BESS_BUS2 = 16, 20
CKPT_DIR = os.path.join('Paper_2', 'artifacts', 'models', 'p2e9_seeds')
OUT_DIAG = os.path.join('Paper_2', 'artifacts', 'diagnostics')

SEED_CKPT = {11: 'seed11_ep400', 22: 'seed22_ep1600', 33: 'seed33_ep400',
             44: 'seed44_ep600', 55: 'seed55_ep1400'}
SCENARIOS = {
    'gen_val': dict(kind='gen', gen='GENROU_6', rho=0.6, lambda_L=1.00),
    'load_val': dict(kind='load', pq_idx='PQ_10', alpha_L=0.3, lambda_L=1.00),
}
WINDOWS = [(0.0, 1.0), (1.0, 2.0), (2.0, 3.0), (3.0, 4.0), (4.0, 5.0)]


def main():
    rows = []
    for scen_label, scen in SCENARIOS.items():
        for seed, ckpt in SEED_CKPT.items():
            model = TD3.load(os.path.join(CKPT_DIR, ckpt))
            env = P2ResidualTrainEnv(obs_mode='OBS-A', fixed_scenario=scen, p_max_bess_mw=PMAX_MW,
                                      kd_star_mw_per_hz=KD_STAR, p_rl_max_mw=P_RL_MAX_MW, tc=TC,
                                      tstep=TSTEP, bess_bus1=BESS_BUS1, bess_bus2=BESS_BUS2)
            obs, info = env.reset()
            ptot_hist, t_hist = [], []
            terminated = truncated = False
            while not (terminated or truncated):
                action, _ = model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = env.step(action)
                ptot_hist.append(info['p_total_mw'][0] + info['p_total_mw'][1])
                t_hist.append(info['t'])
            ptot = np.array(ptot_hist)
            tau = np.array(t_hist) - 1.0
            for w0, w1 in WINDOWS:
                m = (tau >= w0) & (tau < w1)
                if m.sum() > 1:
                    rows.append(dict(scenario=scen_label, seed=seed, window_start_s=w0,
                                      window_end_s=w1, p_total_ptp_mw=float(np.ptp(ptot[m]))))
            print(f"  {scen_label:10s} seed{seed}: " +
                  " ".join(f"[{w0:.0f}-{w1:.0f})={r['p_total_ptp_mw']:.0f}MW"
                            for r, (w0, w1) in zip(rows[-5:], WINDOWS)))

    df = pd.DataFrame(rows)
    out_csv = os.path.join(OUT_DIAG, 'p2e11c_oscillation_check.csv')
    df.to_csv(out_csv, index=False)
    print(f"\nSaved: {out_csv}")

    print("\n=== Tendencia (ultima ventana / primera ventana con oscilacion, gen_val) ===")
    for seed in SEED_CKPT:
        sub = df[(df['scenario'] == 'gen_val') & (df['seed'] == seed)].sort_values('window_start_s')
        first, last = sub['p_total_ptp_mw'].iloc[1], sub['p_total_ptp_mw'].iloc[-1]  # skip window [0,1) (the transient itself)
        trend = 'CRECIENTE' if last > first * 1.3 else ('DECAYENTE' if last < first * 0.7 else 'ESTABLE')
        print(f"  seed{seed}: [1-2)s={first:.0f}MW -> [4-5)s={last:.0f}MW  -> {trend}")


if __name__ == '__main__':
    main()
