#!/usr/bin/env python
"""
P2-E7 (freeze final pre-preflight) -- minimal regression for the DEC-P2-030
fix (p2_common.py's f_gen_hz now sliced to [:len(GEN_BUSES)], excluding the
2 auto-added BESS-bus BusFreq entries from every worst-system/max_i
metric). Authorized explicitly by the user.

Re-runs exactly the 6 cases already checked (by hand) in DEC-P2-030 --
NoFFC/droop*/F+R* x gen_severe/load_severe -- using the CORRECTED
p2_common.py, and compares df_nadir_hz/RoCoF_max_hz_s against the values
already frozen in prior decision log entries (DEC-P2-018/024/025). Also
recomputes the SS6 reward's max_i-based e_f/e_r terms with the corrected
10-generator-only array and confirms they no longer include the BESS
buses (by construing the array length itself, not a separate reward
call -- p2_common.py does not implement the SS6 reward directly, that
lives in p2_env_train.py, already fixed and unaffected by this change to
p2_common.py).

No sweep, no new tuning, no TD3, no validation, no P2-T*.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p2_common import run_physical_scenario_tc, GEN_BUSES

PMAX_MW = 293.4
KD_STAR = 4694.4
KF_BEST, KR_BEST = 4.0 * 586.8, 0.5 * 293.4  # DEC-P2-025 best F+R point

# Values already frozen/reported in prior decision log entries (source of truth
# to compare against, NOT recomputed here -- these are the numbers this
# regression must reproduce after the fix).
EXPECTED = {
    ('gen_severe', 'NoFFC'): dict(df_nadir_hz=-0.181170, rocof_max_hz_s=1.185, source='DEC-P2-020ff'),
    ('load_severe', 'NoFFC'): dict(df_nadir_hz=-0.208309, rocof_max_hz_s=2.933, source='DEC-P2-020ff'),
    ('gen_severe', 'droop*'): dict(df_nadir_hz=-0.118617, rocof_max_hz_s=0.885, source='DEC-P2-024'),
    ('load_severe', 'droop*'): dict(df_nadir_hz=-0.144406, rocof_max_hz_s=2.295, source='DEC-P2-024'),
    ('gen_severe', 'F+R*'): dict(df_nadir_hz=-0.123060, rocof_max_hz_s=0.904, source='DEC-P2-025'),
    ('load_severe', 'F+R*'): dict(df_nadir_hz=-0.144182, rocof_max_hz_s=2.292, source='DEC-P2-025'),
}

SCEN = {
    'gen_severe': dict(kind='gen', gen='GENROU_4', rho=0.90, lambda_L=1.00),
    'load_severe': dict(kind='load', bus=20, alpha_L=0.50, lambda_L=1.00),
}

CONTROLLERS = {
    'NoFFC': dict(k_f=0.0, k_r=0.0, controller='no_ffc'),
    'droop*': dict(k_f=KD_STAR, k_r=0.0, controller='physical'),
    'F+R*': dict(k_f=KF_BEST, k_r=KR_BEST, controller='physical'),
}


def main():
    print("=== DEC-P2-030 fix regression: 6 cases, corrected p2_common.py ===\n")
    rows = []
    all_match = True
    for scen_label, scen in SCEN.items():
        for ctrl_label, ctrl in CONTROLLERS.items():
            r = run_physical_scenario_tc(p_max_bess_mw=PMAX_MW, tc=0.005, tstep=0.005,
                                          bess_bus1=16, bess_bus2=20, tf=6.0, **ctrl, **scen)
            f_all = r['f_gen_all_hz']
            n_cols_ok = f_all.shape[1] == len(GEN_BUSES)
            df_nadir_after = r['df_nadir_hz']
            rocof_max_after = r['rocof_max_hz_s']

            exp = EXPECTED[(scen_label, ctrl_label)]
            match_nadir = abs(df_nadir_after - exp['df_nadir_hz']) < 1e-6
            match_rocof = abs(rocof_max_after - exp['rocof_max_hz_s']) < 1e-3
            match = match_nadir and match_rocof and n_cols_ok
            all_match &= match

            rows.append(dict(scenario=scen_label, controller=ctrl_label,
                              df_nadir_before=exp['df_nadir_hz'], df_nadir_after=df_nadir_after,
                              rocof_max_before=exp['rocof_max_hz_s'], rocof_max_after=rocof_max_after,
                              f_gen_all_ncols=f_all.shape[1], expected_ncols=len(GEN_BUSES),
                              source=exp['source'], MATCH=match))
            print(f"  {scen_label:12s} {ctrl_label:7s}  df_nadir: before={exp['df_nadir_hz']:+.6f} "
                  f"after={df_nadir_after:+.6f}  RoCoF_max: before={exp['rocof_max_hz_s']:.3f} "
                  f"after={rocof_max_after:.3f}  f_gen_all_hz cols={f_all.shape[1]} "
                  f"(expected {len(GEN_BUSES)})  {'MATCH' if match else 'MISMATCH!!'}")

    df = pd.DataFrame(rows)
    out_csv = os.path.join('Paper_2', 'artifacts', 'diagnostics', 'p2e7_dec030_fix_regression.csv')
    df.to_csv(out_csv, index=False)
    print(f"\nSaved: {out_csv}")

    print(f"\n=== RESULTADO: {'6/6 MATCH -- DEC-P2-030 no afecto la evidencia fisica previa' if all_match else 'AL MENOS 1 MISMATCH -- DETENERSE, no continuar a P2-E8'} ===")


if __name__ == '__main__':
    main()
