#!/usr/bin/env python
"""P2_F03: IBR/BESS response to gen_severe -- same structure as F04."""
import os
import sys

import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from p2_figures_common import load_npz, run, style_axes, finalize_and_save, OUT_DIR, TD

META = pd.read_csv(os.path.join(OUT_DIR, 'figure_metadata.csv'))
PMAX_MW = 293.4


def mark_markers(ax, t_event, t_nadir, t_first_cmd):
    ylim = ax.get_ylim()
    span = ylim[1] - ylim[0]
    for x, label, color, y_frac in [(t_event, 'Event', '0.5', 0.95),
                                     (t_nadir, 'Nadir', 'firebrick', 0.85),
                                     (t_first_cmd, 'First cmd', 'C0', 0.75)]:
        if x is None:
            continue
        ax.axvline(x, color=color, linewidth=0.8, linestyle=(0, (4, 2)) if label != 'Event' else '-',
                   zorder=1, alpha=0.8)
        ax.text(x, ylim[0] + y_frac * span, f' {label}', fontsize=6, color=color, va='top', ha='left')


def main():
    npz = load_npz()
    r = run(npz, 'gen_severe', 'FR_16_20')
    m = META[(META['scenario'] == 'gen_severe') & (META['controller'] == 'F+R') &
              (META['bess_buses'] == '16_20')].iloc[0]

    t_event, t_nadir, t_first_cmd = 0.0, m['nadir_time_s'] - TD, m['first_command_time_s'] - TD

    window = (r.tau >= -0.2) & (r.tau <= 2.0)
    tau = r.tau[window]
    pc1, pc2 = r['p_command1_mw'][window], r['p_command2_mw'][window]
    pd1, pd2 = r['p_delivered1_mw'][window], r['p_delivered2_mw'][window]

    fig, axes = plt.subplots(4, 1, figsize=(3.5, 6.0), sharex=True)
    axA, axB, axC, axD = axes

    axA.step(tau, pc1, where='post', color='C0', linewidth=1.2, label='BESS1 (bus 16)')
    axA.step(tau, pc2, where='post', color='C3', linewidth=1.2, label='BESS2 (bus 20)')
    axB.plot(tau, pd1, color='C0', linewidth=1.2, label='BESS1 (bus 16)')
    axB.plot(tau, pd2, color='C3', linewidth=1.2, label='BESS2 (bus 20)')

    axC.step(tau, pc1, where='post', color='0.3', linewidth=1.0, linestyle='--', label='Command')
    axC.plot(tau, pd1, color='C0', linewidth=1.3, label='Delivered')
    axD.step(tau, pc2, where='post', color='0.3', linewidth=1.0, linestyle='--', label='Command')
    axD.plot(tau, pd2, color='C3', linewidth=1.3, label='Delivered')

    axA.set_ylabel(r'$P_{command}$ (MW)')
    axB.set_ylabel(r'$P_{delivered}$ (MW)')
    axC.set_ylabel('BESS1 (MW)')
    axD.set_ylabel('BESS2 (MW)')
    axD.set_xlabel(r'$\tau = t - t_{event}$ (s)')

    for ax in axes:
        style_axes(ax)
        mark_markers(ax, t_event, t_nadir, t_first_cmd)
    axA.legend(ncol=2, loc='lower right', fontsize=6)
    axC.legend(ncol=2, loc='lower right', fontsize=6)
    axD.legend(ncol=2, loc='lower right', fontsize=6)

    fig.align_ylabels(axes)
    fig.tight_layout()
    finalize_and_save(fig, 'P2_F03_gen_event_IBR_response')
    plt.close(fig)


if __name__ == '__main__':
    main()
