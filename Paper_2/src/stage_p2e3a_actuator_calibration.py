#!/usr/bin/env python
"""
P2-E3A -- BESS actuator calibration gate.

Open-loop test (no closed frequency loop, no Alter contingency): for each
BESS, independently, apply constant commands at 0/25/50/75/100% of a
provisional P_max,BESS (both signs), let the ESD1 command->power path settle,
and compare P_delivered_MW (measured at the bus, Sb=100 MVA system base)
against the commanded value. Repeat a reduced set at a DIFFERENT P_max,BESS
to demonstrate that delivered power actually scales with the configured
rating (mandatory power convention, see p2_common.add_bess_pair /
DEC-P2-004/005/006).

Output: Paper_2/artifacts/preflight/p2_actuator_calibration.csv and a
commanded-vs-delivered figure. Does NOT train or run TD3; does NOT touch the
P2 final test.
"""
import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from p2_common import BESS_BUS_1, BESS_BUS_2, run_command_step_response

PMAX_PROVISIONAL_MW = 293.4  # alpha_P=1.0 value already used in P2-E3 diagnostics (DEC-P2-005)
PMAX_ALT_MW = 400.0          # deliberately ABOVE the old (buggy) ~100 MW ceiling (DEC-P1-024)
FRACTIONS_FULL = [-1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0]
FRACTIONS_ALT = [-1.0, -0.5, 0.0, 0.5, 1.0]

TF = 1.0
T_STEP = 0.1
TSTEP = 0.005  # 5 ms integration/logging resolution


def calibration_point(p_max_bess_mw, target_bus, frac):
    command_mw = frac * p_max_bess_mw
    r = run_command_step_response(p_max_bess_mw, target_bus, command_mw,
                                   tf=TF, tstep=TSTEP, t_step=T_STEP)
    p_delivered = float(r['p_delivered_mw'][-1]) if len(r['p_delivered_mw']) else float('nan')
    bus_v = float(r['bus_voltage'][-1]) if len(r['bus_voltage']) else float('nan')
    ipout = float(r['ipout_y'][-1]) if len(r['ipout_y']) else float('nan')
    pext0_pu = command_mw / 100.0
    pmx_pu = p_max_bess_mw / 100.0
    abs_err = p_delivered - command_mw
    denom = max(abs(command_mw), 1.0)  # 1 MW floor avoids div-by-zero at command=0
    rel_err = abs_err / denom
    saturation_flag = abs(command_mw) >= p_max_bess_mw - 1e-6
    return dict(
        p_max_bess_mw=p_max_bess_mw, bess_bus=target_bus, frac_of_pmax=frac,
        command_MW=command_mw, Pext0_pu=pext0_pu, pmx_pu=pmx_pu,
        Ipout_y=ipout, bus_voltage=bus_v, P_delivered_MW=p_delivered,
        absolute_error_MW=abs_err, relative_error=rel_err,
        saturation_flag=saturation_flag, TDS_success=bool(r['tds_success']),
    )


def main():
    rows = []
    print(f"=== P2-E3A: actuator calibration (provisional Pmax={PMAX_PROVISIONAL_MW} MW) ===")
    for bus in (BESS_BUS_1, BESS_BUS_2):
        for frac in FRACTIONS_FULL:
            rec = calibration_point(PMAX_PROVISIONAL_MW, bus, frac)
            rows.append(rec)
            print(f"  bus={bus} frac={frac:+.2f} cmd={rec['command_MW']:+8.2f}MW "
                  f"-> delivered={rec['P_delivered_MW']:+8.2f}MW  abs_err={rec['absolute_error_MW']:+.3f}MW "
                  f"rel_err={rec['relative_error']:+.4f}  sat={rec['saturation_flag']}  "
                  f"tds_ok={rec['TDS_success']}")

    print(f"\n=== P2-E3A: scaling check at alt Pmax={PMAX_ALT_MW} MW (bus {BESS_BUS_1} only) ===")
    for frac in FRACTIONS_ALT:
        rec = calibration_point(PMAX_ALT_MW, BESS_BUS_1, frac)
        rows.append(rec)
        print(f"  bus={BESS_BUS_1} frac={frac:+.2f} cmd={rec['command_MW']:+8.2f}MW "
              f"-> delivered={rec['P_delivered_MW']:+8.2f}MW  abs_err={rec['absolute_error_MW']:+.3f}MW "
              f"rel_err={rec['relative_error']:+.4f}  sat={rec['saturation_flag']}  "
              f"tds_ok={rec['TDS_success']}")

    df = pd.DataFrame(rows)
    out_csv = os.path.join('Paper_2', 'artifacts', 'preflight', 'p2_actuator_calibration.csv')
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    df.to_csv(out_csv, index=False)
    print(f"\nSaved: {out_csv} ({len(df)} rows)")

    nonsat = df[~df['saturation_flag']]
    print("\n--- Summary (non-saturated points only) ---")
    print(f"max |absolute_error_MW| = {nonsat['absolute_error_MW'].abs().max():.4f}")
    print(f"max |relative_error|    = {nonsat['relative_error'].abs().max():.4f}")
    print(f"all TDS_success         = {bool(df['TDS_success'].all())}")

    # Scaling demonstration: does 100% command at PMAX_ALT actually deliver ~PMAX_ALT?
    alt_100 = df[(df['p_max_bess_mw'] == PMAX_ALT_MW) & (df['frac_of_pmax'] == 1.0)]
    prov_100 = df[(df['p_max_bess_mw'] == PMAX_PROVISIONAL_MW) & (df['bess_bus'] == BESS_BUS_1)
                  & (df['frac_of_pmax'] == 1.0)]
    print(f"\n100% command @ Pmax={PMAX_PROVISIONAL_MW}MW -> delivered="
          f"{prov_100['P_delivered_MW'].iloc[0]:.2f} MW")
    print(f"100% command @ Pmax={PMAX_ALT_MW}MW -> delivered="
          f"{alt_100['P_delivered_MW'].iloc[0]:.2f} MW")
    print("(old buggy convention would have capped BOTH near ~100 MW regardless of Pmax label)")

    fig, ax = plt.subplots(figsize=(5.0, 5.0))
    for bus, marker, label in [(BESS_BUS_1, 'o', f'bus {BESS_BUS_1} (Pmax={PMAX_PROVISIONAL_MW:.0f}MW)'),
                                (BESS_BUS_2, 's', f'bus {BESS_BUS_2} (Pmax={PMAX_PROVISIONAL_MW:.0f}MW)')]:
        sub = df[(df['bess_bus'] == bus) & (df['p_max_bess_mw'] == PMAX_PROVISIONAL_MW)]
        ax.scatter(sub['command_MW'], sub['P_delivered_MW'], marker=marker, label=label, zorder=3)
    sub_alt = df[df['p_max_bess_mw'] == PMAX_ALT_MW]
    ax.scatter(sub_alt['command_MW'], sub_alt['P_delivered_MW'], marker='^', color='C2',
               label=f'bus {BESS_BUS_1} (Pmax={PMAX_ALT_MW:.0f}MW)', zorder=3)
    lims = [min(df['command_MW'].min(), df['P_delivered_MW'].min()) - 20,
            max(df['command_MW'].max(), df['P_delivered_MW'].max()) + 20]
    ax.plot(lims, lims, 'k--', linewidth=1, label='ideal 1:1', zorder=2)
    ax.set_xlabel('Commanded power (MW)')
    ax.set_ylabel('Delivered power (MW)')
    ax.set_title('P2-E3A: BESS actuator calibration')
    ax.legend(fontsize=7, loc='upper left')
    ax.grid(True, linestyle=':', alpha=0.6)
    fig.tight_layout()
    out_fig = os.path.join('Paper_2', 'artifacts', 'figures', 'p2_actuator_calibration.png')
    os.makedirs(os.path.dirname(out_fig), exist_ok=True)
    fig.savefig(out_fig, dpi=200)
    print(f"Saved: {out_fig}")


if __name__ == '__main__':
    main()
