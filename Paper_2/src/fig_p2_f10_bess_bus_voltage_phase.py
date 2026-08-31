#!/usr/bin/env python
"""P2_F10: voltage and phase at the BESS POI buses (16, 20) for the current
pair, NoFFC vs F+R -- checks the FFR action doesn't introduce a pathological
electrical response at the actuator buses. Main figure: gen_severe.
Supplementary: load_severe (same structure)."""
import os
import sys

import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from p2_figures_common import load_npz, run, CONTROLLER_STYLE, style_axes, mark_event, finalize_and_save


def plot_voltage_phase(scenario, name, window):
    npz = load_npz()
    r_noffc = run(npz, scenario, 'NoFFC')
    r_fr = run(npz, scenario, 'FR_16_20')

    fig, axes = plt.subplots(4, 1, figsize=(3.5, 6.0), sharex=True)
    axA, axB, axC, axD = axes

    for r, label in [(r_noffc, 'NoFFC'), (r_fr, 'F+R')]:
        style = CONTROLLER_STYLE[label]
        w = (r.tau >= window[0]) & (r.tau <= window[1])
        tau = r.tau[w]

        v16 = (r['v_bess1_pu'][w] - r['v_bess1_pu'][w][0]) * 1000
        v20 = (r['v_bess2_pu'][w] - r['v_bess2_pu'][w][0]) * 1000
        axA.plot(tau, v16, label=label, **style)
        axB.plot(tau, v20, label=label, **style)

        th16 = np.degrees(r['theta_bess1_rad'][w] - r['theta_bess1_rad'][w][0])
        th20 = np.degrees(r['theta_bess2_rad'][w] - r['theta_bess2_rad'][w][0])
        axC.plot(tau, th16, color=style['color'], linestyle=style['linestyle'],
                 linewidth=style['linewidth'], label=f'{label} bus16')
        axC.plot(tau, th20, color=style['color'], linestyle=style['linestyle'],
                 linewidth=style['linewidth'] * 0.6, alpha=0.6, label=f'{label} bus20')
        axD.plot(tau, th16 - th20, label=label, **style)

    axA.set_ylabel(r'$\Delta V_{16}$ (mpu)')
    axB.set_ylabel(r'$\Delta V_{20}$ (mpu)')
    axC.set_ylabel(r'$\Delta\theta$ (deg)')
    axD.set_ylabel(r'$\Delta\theta_{16}-\Delta\theta_{20}$ (deg)')
    axD.set_xlabel(r'$\tau = t - t_{event}$ (s)')

    for ax in axes:
        style_axes(ax)
        mark_event(ax)
    axA.legend(loc='lower right', fontsize=6.5)
    axC.legend(loc='lower right', fontsize=6, ncol=2)

    fig.align_ylabels(axes)
    fig.tight_layout()
    finalize_and_save(fig, name)
    plt.close(fig)


if __name__ == '__main__':
    plot_voltage_phase('gen_severe', 'P2_F10_bess_bus_voltage_phase', window=(-0.3, 3.0))
    plot_voltage_phase('load_severe', 'P2_F10s_bess_bus_voltage_phase_load_severe', window=(-0.2, 2.0))
