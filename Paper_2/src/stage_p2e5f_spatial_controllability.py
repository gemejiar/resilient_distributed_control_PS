#!/usr/bin/env python
"""
P2-E5f -- spatial controllability probe for load_severe.

Open-loop (no Kf/Kr, no feedback): a single BESS-sized device, at ONE
candidate bus at a time, receives a FIXED +Pmax,BESS step exactly at the
disturbance instant (t=TD), held constant -- a best-case upper bound on what
any feedback controller at that location could ever achieve. Compares BESS
bus 13, BESS bus 12 (frozen locations), the closest electrical-distance
candidates to the disturbed bus (PQ_9/bus 20), and bus 20 itself (oracle
upper bound, not a real candidate -- co-located with the disturbance).

Same load_severe scenario, same low-inertia case, same total Pmax per probe
(one BESS unit's worth, 293.4MW, identical magnitude at every location), same
Tc-irrelevant open-loop test (no Tc since there is no feedback loop here),
same tstep=5ms. No Kf/Kr tuning. No TD3.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p2_common import (build_case, electrical_distance, run_spatial_controllability_probe,
                        BESS_BUS_1, BESS_BUS_2, BESS_ADMISSIBLE_BUSES, TF_INITIAL, F0_HZ)

PMAX_BESS_MW = 293.4  # one BESS unit's authority -- identical magnitude at every test location
COMMAND_MW = PMAX_BESS_MW  # positive (discharge) -- correct direction to counter a load increase
TSTEP = 0.005

OUT_DIAG = os.path.join('Paper_2', 'artifacts', 'diagnostics')
os.makedirs(OUT_DIAG, exist_ok=True)


def main():
    print("=== P2-E5f: electrical distance from bus 20 (load_severe disturbance) ===")
    ss = build_case(k=None, quiet=True)  # topology only, no contingency/inertia scaling needed (build_case() already calls ss.setup())
    dist = electrical_distance(ss, [20])[20]
    dist_admissible = {b: dist[b] for b in BESS_ADMISSIBLE_BUSES if b in dist}
    ranked = sorted(dist_admissible.items(), key=lambda kv: kv[1])
    print("Closest BESS-admissible buses to bus 20 (excluding 20 itself):")
    closest = [b for b, d in ranked if b != 20][:3]
    for b, d in ranked[:6]:
        marker = ' <-- BESS_BUS_1' if b == BESS_BUS_1 else (' <-- BESS_BUS_2' if b == BESS_BUS_2 else '')
        print(f"  bus {b:3d}: dist={d:.4f}{marker}")
    print(f"dist(bus 20 -> BESS_BUS_1={BESS_BUS_1}) = {dist[BESS_BUS_1]:.4f}")
    print(f"dist(bus 20 -> BESS_BUS_2={BESS_BUS_2}) = {dist[BESS_BUS_2]:.4f}")

    test_buses = sorted(set([BESS_BUS_1, BESS_BUS_2] + closest + [20]))
    print(f"\nTest buses: {test_buses} (20 = oracle upper bound, co-located with disturbance, not a real candidate)")

    # NoFFC reference (reused, no new sim needed for this -- already computed in P2-E5,
    # but recomputed here fresh via the same disturbance mechanism for self-containment
    # and exact consistency with this driver's TDS settings).
    r0 = run_spatial_controllability_probe(kind='load', bus=20, alpha_L=0.50, lambda_L=1.00,
                                            test_bus=BESS_BUS_1, command_mw=0.0,
                                            p_max_bess_mw=PMAX_BESS_MW, tstep=TSTEP, tf=TF_INITIAL)
    noffc_df_nadir = r0['df_nadir_hz']
    noffc_rocof_max = r0['rocof_max_hz_s']
    print(f"\nNoFFC reference (command=0): df_nadir={noffc_df_nadir:+.4f}Hz RoCoF_max={noffc_rocof_max:.4f}Hz/s")

    rows = []
    print(f"\n=== Open-loop +{COMMAND_MW:.1f}MW step at t=TD, per test bus ===")
    for tb in test_buses:
        r = run_spatial_controllability_probe(kind='load', bus=20, alpha_L=0.50, lambda_L=1.00,
                                               test_bus=tb, command_mw=COMMAND_MW,
                                               p_max_bess_mw=PMAX_BESS_MW, tstep=TSTEP, tf=TF_INITIAL)
        delta_df = r['df_nadir_hz'] - noffc_df_nadir
        delta_rocof = noffc_rocof_max - r['rocof_max_hz_s']  # positive = improvement
        sens_df = delta_df / COMMAND_MW
        sens_rocof = delta_rocof / COMMAND_MW
        row = dict(test_bus=tb, dist_to_bus20=dist.get(tb, float('nan')),
                   df_nadir_hz=r['df_nadir_hz'], RoCoF_max_hz_s=r['rocof_max_hz_s'],
                   delta_df_nadir_hz=delta_df, delta_RoCoF_max_hz_s=delta_rocof,
                   sensitivity_df_hz_per_MW=sens_df, sensitivity_RoCoF_hz_s_per_MW=sens_rocof,
                   p_peak_MW=r['p_peak_mw'], TDS_success=bool(r['tds_success']))
        rows.append(row)
        label = 'BESS_BUS_1' if tb == BESS_BUS_1 else ('BESS_BUS_2' if tb == BESS_BUS_2 else
                                                          ('ORACLE(bus20)' if tb == 20 else 'candidate'))
        print(f"  bus {tb:3d} ({label:14s}) dist={row['dist_to_bus20']:.4f}: "
              f"delta_df_nadir={delta_df*1000:+.2f}mHz delta_RoCoF={delta_rocof:+.4f}Hz/s "
              f"sens_df={sens_df*1000:+.4f}mHz/MW sens_RoCoF={sens_rocof*1000:+.4f}mHz/s/MW "
              f"Ppeak={row['p_peak_MW']:.1f}MW tds_ok={row['TDS_success']}")

    df = pd.DataFrame(rows).sort_values('dist_to_bus20')
    out_csv = os.path.join(OUT_DIAG, 'p2e5f_spatial_controllability.csv')
    df.to_csv(out_csv, index=False)
    print(f"\nSaved: {out_csv}")

    best_row = df.loc[df['delta_RoCoF_max_hz_s'].abs().add(df['delta_df_nadir_hz'].abs()).idxmax()] \
        if df['delta_RoCoF_max_hz_s'].abs().max() > 1e-6 or df['delta_df_nadir_hz'].abs().max() > 1e-6 \
        else None
    print("\n=== Summary ===")
    print(df[['test_bus', 'dist_to_bus20', 'delta_df_nadir_hz', 'delta_RoCoF_max_hz_s']].to_string(index=False))
    if best_row is not None:
        print(f"\nLargest-magnitude effect found at bus {int(best_row['test_bus'])}: "
              f"delta_df_nadir={best_row['delta_df_nadir_hz']*1000:+.2f}mHz, "
              f"delta_RoCoF={best_row['delta_RoCoF_max_hz_s']:+.4f}Hz/s")
    else:
        print("\nNo location tested produced a non-negligible effect on either metric.")


if __name__ == '__main__':
    main()
