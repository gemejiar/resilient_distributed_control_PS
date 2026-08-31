#!/usr/bin/env python
"""
P2-E11b -- figure: NoFFC vs droop* vs TD3 (seed44) trajectories, full
resolution, on the two validation event types. Shows whether the trained
residual visibly acts to improve RoCoF/nadir, not just the aggregate
J_val_P2 numbers.
"""
import os
import sys

import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from p2_figures_common import style_axes, finalize_and_save, DOUBLE_COL_W

TRAJ_NPZ = os.path.join('Paper_2', 'artifacts', 'trajectories', 'p2e11b_trajectory_demo.npz')
TD = 1.0

STYLE = {
    'NoFFC':      dict(color='black', linestyle=':', linewidth=1.3),
    'droop_star': dict(color='0.35', linestyle='-', linewidth=1.3),
    'TD3_seed44': dict(color='C0', linestyle='-', linewidth=1.4),
}
LABEL = {'NoFFC': 'NoFFC', 'droop_star': 'droop*', 'TD3_seed44': 'TD3 (seed 44)'}


def plot_scenario(npz, scen_label, title, window):
    fig, axes = plt.subplots(3, 1, figsize=(DOUBLE_COL_W, 6.0), sharex=True)
    axF, axR, axP = axes
    for ctrl in ['NoFFC', 'droop_star', 'TD3_seed44']:
        prefix = f'{scen_label}__{ctrl}__'
        t = npz[prefix + 't']
        tau = t - TD
        w = (tau >= window[0]) & (tau <= window[1])
        f_worst = npz[prefix + 'f_worst_hz']
        rocof = npz[prefix + 'rocof_worst_hz_s']
        pc1 = npz[prefix + 'p_command1_mw']
        pc2 = npz[prefix + 'p_command2_mw']
        pd1 = npz[prefix + 'p_delivered1_mw']
        pd2 = npz[prefix + 'p_delivered2_mw']

        style = STYLE[ctrl]
        axF.plot(tau[w], f_worst[w], label=LABEL[ctrl], **style)
        axR.plot(tau[w], rocof[w], **style)
        axP.plot(tau[w], pd1[w] + pd2[w], **style)
        if ctrl != 'NoFFC':
            axP.plot(tau[w], pc1[w] + pc2[w], color=style['color'], linestyle='--',
                      linewidth=0.7, alpha=0.6)

    axF.set_ylabel('Peor $f$ (Hz)\n(10 GEN_BUSES)')
    axR.set_ylabel('Peor |RoCoF|\n(Hz/s)')
    axP.set_ylabel('$P_{BESS1}+P_{BESS2}$\n(MW)')
    axP.set_xlabel(r'$\tau = t - t_{event}$ (s)')
    axF.set_title(f'{title}\nlinea solida=entregado, discontinua=comando (droop*/TD3)', fontsize=8.5)
    for ax in axes:
        style_axes(ax)
        ax.axvline(0.0, color='0.5', linewidth=0.8, zorder=1)
    axF.legend(fontsize=7, loc='lower right')
    fig.align_ylabels(axes)
    fig.tight_layout()
    finalize_and_save(fig, f'P2E11b_{scen_label}_trajectory')
    plt.close(fig)


def main():
    npz = np.load(TRAJ_NPZ)
    plot_scenario(npz, 'gen_val', 'Evento GENROU_6, rho=0.6 (validation)', window=(-0.3, 5.0))
    plot_scenario(npz, 'load_val', 'Evento PQ_10, alpha_L=0.3 (validation)', window=(-0.2, 4.0))


if __name__ == '__main__':
    main()
