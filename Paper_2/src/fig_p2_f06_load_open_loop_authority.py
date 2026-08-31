#!/usr/bin/env python
"""P2_F06: NoFFC vs F+R vs Open-loop for load_severe -- demonstrates BESS
physical authority. 3 panels: frequency deviation, RoCoF, total delivered
BESS power."""
import os
import sys

import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from p2_figures_common import load_npz, run, CONTROLLER_STYLE, style_axes, mark_event, finalize_and_save, OUT_DIR, TD

META = pd.read_csv(os.path.join(OUT_DIR, 'figure_metadata.csv'))


def main():
    npz = load_npz()
    cases = [('NoFFC', run(npz, 'load_severe', 'NoFFC'), 'NoFFC'),
             ('F+R', run(npz, 'load_severe', 'FR_16_20'), 'F+R'),
             ('OpenLoop', run(npz, 'load_severe', 'OpenLoop_16_20'), 'OpenLoop')]

    window = (-0.2, 2.0)
    fig, (axA, axB, axC) = plt.subplots(3, 1, figsize=(3.5, 4.6), sharex=True)

    for key, r, style_key in cases:
        style = CONTROLLER_STYLE[style_key]
        w = (r.tau >= window[0]) & (r.tau <= window[1])
        tau = r.tau[w]
        axA.plot(tau, (r['f_worst_hz'][w] - 60.0) * 1000, label=style_key, **style)
        axB.plot(tau, r['rocof_worst_hz_s'][w], label=style_key, **style)
        p_total = r['p_delivered1_mw'][w] + r['p_delivered2_mw'][w]
        axC.plot(tau, p_total, label=style_key, **style)

        m_rows = META[(META['scenario'] == 'load_severe') & (META['bess_buses'] == '16_20')]
        controller_name = 'NoFFC' if key == 'NoFFC' else ('F+R' if key == 'F+R' else 'OpenLoop')
        m = m_rows[m_rows['controller'] == controller_name].iloc[0]
        axA.plot(m['nadir_time_s'] - TD, (m['nadir_value_hz'] - 60.0) * 1000, marker='o', ms=4,
                 color=style['color'], zorder=5)
        axB.plot(m['rocof_max_time_s'] - TD, m['rocof_max_hz_s'], marker='o', ms=4,
                 color=style['color'], zorder=5)

    axA.set_ylabel(r'$\Delta f$ (mHz)')
    axB.set_ylabel('|RoCoF| (Hz/s)')
    axC.set_ylabel(r'$P_{BESS,total}$ (MW)')
    axC.set_xlabel(r'$\tau = t - t_{event}$ (s)')

    for ax in (axA, axB, axC):
        style_axes(ax)
        mark_event(ax)
    axA.legend(loc='lower right', fontsize=6.5)

    fig.align_ylabels((axA, axB, axC))
    fig.tight_layout()
    finalize_and_save(fig, 'P2_F06_load_event_open_loop_authority')
    plt.close(fig)


if __name__ == '__main__':
    main()
