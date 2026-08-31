#!/usr/bin/env python
"""P2_F05: timing zoom -- shows, without stating it in words, that the
load_severe nadir occurs before the F+R controller's first reactive command.
Three aligned panels: frequency deviation, RoCoF, total BESS power
(command + delivered)."""
import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from p2_figures_common import load_npz, run, CONTROLLER_STYLE, style_axes, finalize_and_save, OUT_DIR, TD

META = pd.read_csv(os.path.join(OUT_DIR, 'figure_metadata.csv'))


def main():
    npz = load_npz()
    r_noffc = run(npz, 'load_severe', 'NoFFC')
    r_fr = run(npz, 'load_severe', 'FR_16_20')
    m_noffc = META[(META['scenario'] == 'load_severe') & (META['controller'] == 'NoFFC')].iloc[0]
    m_fr = META[(META['scenario'] == 'load_severe') & (META['controller'] == 'F+R') &
                (META['bess_buses'] == '16_20')].iloc[0]

    window = (r_fr.tau >= -0.05) & (r_fr.tau <= 0.35)

    fig, (axA, axB, axC) = plt.subplots(3, 1, figsize=(3.5, 4.6), sharex=True)

    for r, label in [(r_noffc, 'NoFFC'), (r_fr, 'F+R')]:
        style = CONTROLLER_STYLE[label]
        w = (r.tau >= -0.05) & (r.tau <= 0.35)
        tau = r.tau[w]
        axA.plot(tau, r['f_worst_hz'][w] - 60.0, label=label, **style)
        axB.plot(tau, r['rocof_worst_hz_s'][w], label=label, **style)

    axA.plot(m_noffc['nadir_time_s'] - TD, m_noffc['nadir_value_hz'] - 60.0, marker='o', ms=4,
             color=CONTROLLER_STYLE['NoFFC']['color'], zorder=5)
    axA.plot(m_fr['nadir_time_s'] - TD, m_fr['nadir_value_hz'] - 60.0, marker='o', ms=4,
             color=CONTROLLER_STYLE['F+R']['color'], zorder=5)
    axB.plot(m_noffc['rocof_max_time_s'] - TD, m_noffc['rocof_max_hz_s'], marker='o', ms=4,
             color=CONTROLLER_STYLE['NoFFC']['color'], zorder=5)
    axB.plot(m_fr['rocof_max_time_s'] - TD, m_fr['rocof_max_hz_s'], marker='o', ms=4,
             color=CONTROLLER_STYLE['F+R']['color'], zorder=5)

    tau_c = r_fr.tau[window]
    pcmd_total = r_fr['p_command1_mw'][window] + r_fr['p_command2_mw'][window]
    pdel_total = r_fr['p_delivered1_mw'][window] + r_fr['p_delivered2_mw'][window]
    axC.step(tau_c, pcmd_total, where='post', color='0.3', linewidth=1.1, linestyle='--',
             label=r'$P_{command,total}$')
    axC.plot(tau_c, pdel_total, color='C0', linewidth=1.3, label=r'$P_{delivered,total}$')

    t_first_cmd = m_fr['first_command_time_s'] - TD

    for ax in (axA, axB, axC):
        ax.axvline(0.0, color='0.5', linewidth=0.8, zorder=1)
        ax.axvline(t_first_cmd, color='C0', linewidth=0.8, linestyle=(0, (4, 2)), zorder=1, alpha=0.8)
        style_axes(ax)
    ylimA = axA.get_ylim()
    axA.text(0.0, ylimA[0] + 0.94 * (ylimA[1] - ylimA[0]), ' Event', fontsize=6, color='0.35', va='top')
    axA.text(m_fr['nadir_time_s'] - TD, ylimA[0] + 0.08 * (ylimA[1] - ylimA[0]), 'Nadir', fontsize=6,
             color='firebrick', va='bottom', ha='center')
    ylimC = axC.get_ylim()
    axC.text(t_first_cmd, ylimC[0] + 0.9 * (ylimC[1] - ylimC[0]), ' First cmd', fontsize=6, color='C0', va='top')

    axA.set_ylabel(r'$\Delta f$ (Hz)')
    axB.set_ylabel('|RoCoF| (Hz/s)')
    axC.set_ylabel(r'$P_{BESS,total}$ (MW)')
    axC.set_xlabel(r'$\tau = t - t_{event}$ (s)')
    axA.legend(loc='lower right', fontsize=6.5)
    axC.legend(loc='lower right', fontsize=6.5)

    fig.align_ylabels((axA, axB, axC))
    fig.tight_layout()
    finalize_and_save(fig, 'P2_F05_load_event_timing_zoom')
    plt.close(fig)


if __name__ == '__main__':
    main()
