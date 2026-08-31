#!/usr/bin/env python
"""P2-E11c figure: sustained/growing command oscillation check, all 5 seeds
x 2 validation scenario types x 5 one-second windows. Shows whether each
seed's command settles (decaying ptp) or keeps chattering (sustained/
growing ptp) well after the initial transient."""
import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from p2_figures_common import style_axes, finalize_and_save, DOUBLE_COL_W

DIAG_DIR = os.path.join('Paper_2', 'artifacts', 'diagnostics')
SEEDS = [11, 22, 33, 44, 55]
SEED_COLOR = {11: 'C0', 22: 'C1', 33: 'C3', 44: 'C2', 55: 'C4'}


def main():
    df = pd.read_csv(os.path.join(DIAG_DIR, 'p2e11c_oscillation_check.csv'))
    fig, axes = plt.subplots(1, 2, figsize=(DOUBLE_COL_W, 3.2), sharey=True)
    for ax, scen in zip(axes, ['gen_val', 'load_val']):
        sub_all = df[df['scenario'] == scen]
        for seed in SEEDS:
            sub = sub_all[sub_all['seed'] == seed].sort_values('window_start_s')
            ax.plot(sub['window_start_s'], sub['p_total_ptp_mw'], marker='o', markersize=3,
                    color=SEED_COLOR[seed], linewidth=1.2, label=f'seed {seed}')
        ax.set_xlabel(r'Ventana $\tau$ (s)')
        ax.set_title(scen, fontsize=8.5)
        style_axes(ax)
    axes[0].set_ylabel(r'$P_{BESS1}+P_{BESS2}$ pico-a-pico\npor ventana de 1s (MW)')
    axes[1].legend(fontsize=6.5, loc='upper right')
    fig.suptitle('P2-E11c -- persistencia de oscilacion del comando TD3 (no capturada por $J_{val,P2}$)',
                 fontsize=8.5)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    finalize_and_save(fig, 'P2E11c_oscillation_persistence')
    plt.close(fig)


if __name__ == '__main__':
    main()
