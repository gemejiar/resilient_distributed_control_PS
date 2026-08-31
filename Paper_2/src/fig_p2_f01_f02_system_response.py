#!/usr/bin/env python
"""P2_F01 (gen_severe) and P2_F02 (load_severe): full system response,
NoFFC vs F+R(16,20), 4 panels (voltage, frequency, phase angle, RoCoF)."""
import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from p2_figures_common import (load_npz, run, CONTROLLER_STYLE, style_axes, mark_event,
                                finalize_and_save, OUT_DIR, TD)

META = pd.read_csv(os.path.join(OUT_DIR, 'figure_metadata.csv'))


def meta_row(scenario, controller, buses):
    m = META[(META['scenario'] == scenario) & (META['controller'] == controller) &
              (META['bess_buses'] == buses)]
    return m.iloc[0] if len(m) else None


def plot_system_response(scenario, name, window):
    npz = load_npz()
    r_noffc = run(npz, scenario, 'NoFFC')
    r_fr = run(npz, scenario, 'FR_16_20')

    fig, axes = plt.subplots(4, 1, figsize=(SINGLE_W, 6.2), sharex=True)
    ax_v, ax_f, ax_th, ax_r = axes

    for r, label in [(r_noffc, 'NoFFC'), (r_fr, 'F+R')]:
        style = CONTROLLER_STYLE[label]
        w = (r.tau >= window[0]) & (r.tau <= window[1])
        tau = r.tau[w]

        v16 = r['v_bess1_pu'][w] - r['v_bess1_pu'][w][0]
        v20 = r['v_bess2_pu'][w] - r['v_bess2_pu'][w][0]
        ax_v.plot(tau, v16 * 1000, label=f'{label} bus16', **style)
        ax_v.plot(tau, v20 * 1000, label=f'{label} bus20', linewidth=style['linewidth'] * 0.6,
                  color=style['color'], linestyle=style['linestyle'], alpha=0.6)

        f_worst = r['f_worst_hz'][w]
        ax_f.plot(tau, f_worst, label=f'{label} worst-bus', **style)

        th16 = np.degrees(r['theta_bess1_rad'][w] - r['theta_bess1_rad'][w][0])
        th20 = np.degrees(r['theta_bess2_rad'][w] - r['theta_bess2_rad'][w][0])
        ax_th.plot(tau, th16, label=f'{label} bus16', **style)
        ax_th.plot(tau, th20, linewidth=style['linewidth'] * 0.6, color=style['color'],
                   linestyle=style['linestyle'], alpha=0.6, label=f'{label} bus20')

        rocof = r['rocof_worst_hz_s'][w]
        ax_r.plot(tau, rocof, label=f'{label} worst-system', **style)

    m_noffc = meta_row(scenario, 'NoFFC', '16_20')
    m_fr = meta_row(scenario, 'F+R', '16_20')
    for m, label in [(m_noffc, 'NoFFC'), (m_fr, 'F+R')]:
        style = CONTROLLER_STYLE[label]
        ax_f.plot(m['nadir_time_s'] - TD, m['nadir_value_hz'], marker='o', ms=4,
                  color=style['color'], zorder=5)
        ax_r.plot(m['rocof_max_time_s'] - TD, m['rocof_max_hz_s'], marker='o', ms=4,
                  color=style['color'], zorder=5)

    i_f = (abs(m_noffc['nadir_value_hz'] - 60) - abs(m_fr['nadir_value_hz'] - 60)) / abs(m_noffc['nadir_value_hz'] - 60)
    i_r = (m_noffc['rocof_max_hz_s'] - m_fr['rocof_max_hz_s']) / m_noffc['rocof_max_hz_s']
    ax_f.annotate(f'$I_f$={i_f*100:+.1f}%', xy=(0.02, 0.06), xycoords='axes fraction',
                  ha='left', fontsize=6.5)
    ax_r.annotate(f'$I_r$={i_r*100:+.1f}%', xy=(0.97, 0.90), xycoords='axes fraction',
                  ha='right', fontsize=6.5)

    ax_v.set_ylabel(r'$\Delta V$ (mpu)')
    ax_f.set_ylabel('Frequency (Hz)')
    ax_th.set_ylabel(r'$\Delta\theta$ (deg)')
    ax_r.set_ylabel('|RoCoF| (Hz/s)')
    ax_r.set_xlabel(r'$\tau = t - t_{event}$ (s)')

    for ax in axes:
        style_axes(ax)
        mark_event(ax)
    ax_v.legend(ncol=2, loc='lower right', fontsize=6)
    ax_f.legend(ncol=1, loc='upper right', fontsize=6)

    fig.align_ylabels(axes)
    fig.tight_layout()
    finalize_and_save(fig, name)
    plt.close(fig)


SINGLE_W = 3.5

if __name__ == '__main__':
    # Full simulated horizon (tf=6.0s, TD=1.0s) -- gen_severe's true nadir occurs
    # late (~t=4.8s, a slow secondary decline, not the fast initial swing); a
    # shorter window would misleadingly cut the trajectory off mid-decline.
    plot_system_response('gen_severe', 'P2_F01_gen_event_system_response', window=(-0.3, 5.0))
    plot_system_response('load_severe', 'P2_F02_load_event_system_response', window=(-0.3, 5.0))
