#!/usr/bin/env python
"""P2_F09: worst-system RoCoF (full-resolution) comparison across BESS-pair
locations -- same structure as F08."""
import os
import sys

import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from p2_figures_common import (load_npz, run, CONTROLLER_STYLE, PAIR_COLOR, PAIR_LABEL,
                                style_axes, mark_event, finalize_and_save, OUT_DIR, TD)

META = pd.read_csv(os.path.join(OUT_DIR, 'figure_metadata.csv'))
PAIRS = ['12_13', '16_24', '16_20']


def panel(ax, npz, scenario, window):
    r0 = run(npz, scenario, 'NoFFC')
    w0 = (r0.tau >= window[0]) & (r0.tau <= window[1])
    ax.plot(r0.tau[w0], r0['rocof_worst_hz_s'][w0], label='NoFFC', **CONTROLLER_STYLE['NoFFC'])
    m0 = META[(META['scenario'] == scenario) & (META['controller'] == 'NoFFC')].iloc[0]
    ax.plot(m0['rocof_max_time_s'] - TD, m0['rocof_max_hz_s'], marker='o', ms=3.5, color='black', zorder=5)

    for pair in PAIRS:
        r = run(npz, scenario, f'FR_{pair}')
        w = (r.tau >= window[0]) & (r.tau <= window[1])
        ax.plot(r.tau[w], r['rocof_worst_hz_s'][w], color=PAIR_COLOR[pair], linestyle='-',
                linewidth=1.2, label=PAIR_LABEL[pair])
        m = META[(META['scenario'] == scenario) & (META['controller'] == 'F+R') &
                 (META['bess_buses'] == pair)].iloc[0]
        ax.plot(m['rocof_max_time_s'] - TD, m['rocof_max_hz_s'], marker='o', ms=3.5,
                color=PAIR_COLOR[pair], zorder=5)

    style_axes(ax)
    mark_event(ax)
    ax.set_ylabel('|RoCoF| (Hz/s)')


def main():
    npz = load_npz()
    fig, (axA, axB) = plt.subplots(2, 1, figsize=(3.5, 4.6), sharex=False)

    panel(axA, npz, 'gen_severe', window=(-0.1, 1.5))
    panel(axB, npz, 'load_severe', window=(-0.1, 0.5))

    axA.set_title('gen_severe', fontsize=8, loc='left')
    axB.set_title('load_severe', fontsize=8, loc='left')
    axB.set_xlabel(r'$\tau = t - t_{event}$ (s)')
    axA.legend(loc='upper right', fontsize=6, ncol=1)

    fig.tight_layout()
    finalize_and_save(fig, 'P2_F09_bess_location_rocof')
    plt.close(fig)


if __name__ == '__main__':
    main()
