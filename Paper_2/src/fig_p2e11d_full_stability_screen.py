#!/usr/bin/env python
"""P2-E11d figures: stability classification (classify_v2, DEC-P2-017
methodology reused) across all 6 validation scenarios, extended oscillation
persistence, and a joint J_val_P2 + stability summary."""
import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

sys.path.insert(0, os.path.dirname(__file__))
from p2_figures_common import style_axes, finalize_and_save, DOUBLE_COL_W, SINGLE_COL_W

DIAG_DIR = os.path.join('Paper_2', 'artifacts', 'diagnostics')
SEEDS = [11, 22, 33, 44, 55]
SEED_COLOR = {11: 'C0', 22: 'C1', 33: 'C3', 44: 'C2', 55: 'C4'}
ORDER = ['NoFFC', 'droop_star'] + [f'seed{s}' for s in SEEDS]
LABELS = ['NoFFC', 'droop*'] + [f'seed {s}' for s in SEEDS]
CLASS_COLOR = {'STABLE': '#2a9d3f', 'MARGINAL': '#e8a33d', 'LIMIT_CYCLE': '#d1495b',
               'NUMERICAL_FAILURE': '#333333'}
CLASS_CODE = {'STABLE': 0, 'MARGINAL': 1, 'LIMIT_CYCLE': 2, 'NUMERICAL_FAILURE': 3}


def fig_a_classification_grid():
    df = pd.read_csv(os.path.join(DIAG_DIR, 'p2e11d_stability_classification.csv'))
    scenarios = sorted(df['scenario_idx'].unique())
    mat = np.zeros((len(ORDER), len(scenarios)))
    for i, c in enumerate(ORDER):
        for j, s in enumerate(scenarios):
            row = df[(df['controller'] == c) & (df['scenario_idx'] == s)].iloc[0]
            mat[i, j] = CLASS_CODE[row['classification_v2']]

    fig, ax = plt.subplots(figsize=(DOUBLE_COL_W, 3.4))
    cmap = plt.matplotlib.colors.ListedColormap(
        [CLASS_COLOR['STABLE'], CLASS_COLOR['MARGINAL'], CLASS_COLOR['LIMIT_CYCLE'],
         CLASS_COLOR['NUMERICAL_FAILURE']])
    ax.imshow(mat, cmap=cmap, vmin=-0.5, vmax=3.5, aspect='auto')
    ax.set_xticks(range(len(scenarios)))
    ax.set_xticklabels([f'gen op{j+1}' if j < 3 else f'load op{j-2}' for j in scenarios], fontsize=7)
    ax.set_yticks(range(len(ORDER)))
    ax.set_yticklabels(LABELS, fontsize=7.5)
    for i in range(len(ORDER)):
        for j in range(len(scenarios)):
            row = df[(df['controller'] == ORDER[i]) & (df['scenario_idx'] == scenarios[j])].iloc[0]
            ax.text(j, i, row['classification_v2'][:4], ha='center', va='center', fontsize=5.5,
                    color='white')
    handles = [Patch(facecolor=v, label=k) for k, v in CLASS_COLOR.items() if k != 'NUMERICAL_FAILURE']
    ax.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=7)
    ax.set_title('P2-E11d-A -- clasificacion classify_v2 (DEC-P2-017), 6 escenarios de validation',
                 fontsize=8.5)
    fig.tight_layout()
    finalize_and_save(fig, 'P2E11d_A_classification_grid')
    plt.close(fig)


def fig_b_oscillation_all_scenarios():
    df = pd.read_csv(os.path.join(DIAG_DIR, 'p2e11d_oscillation_full.csv'))
    scenarios = sorted(df['scenario_idx'].unique())
    fig, axes = plt.subplots(2, 3, figsize=(DOUBLE_COL_W, 4.6), sharex=True, sharey=True)
    for j, scen_idx in enumerate(scenarios):
        ax = axes.flat[j]
        sub_all = df[df['scenario_idx'] == scen_idx]
        for seed in SEEDS:
            sub = sub_all[sub_all['controller'] == f'seed{seed}'].sort_values('window_start_s')
            ax.plot(sub['window_start_s'], sub['p_total_ptp_mw'], marker='o', markersize=2.5,
                    color=SEED_COLOR[seed], linewidth=1.0, label=f'seed {seed}')
        label = f'gen op{j+1}' if j < 3 else f'load op{j-2}'
        ax.set_title(label, fontsize=7.5)
        style_axes(ax)
    axes[0, 0].legend(fontsize=6, ncol=1, loc='upper right')
    fig.text(0.0, 0.5, r'$P_{BESS1}+P_{BESS2}$ pico-a-pico por ventana de 1s (MW)', rotation=90,
              va='center', fontsize=8)
    fig.text(0.5, 0.0, r'Ventana $\tau$ (s)', ha='center', fontsize=8)
    fig.suptitle('P2-E11d-B -- persistencia de oscilacion, los 6 escenarios de validation', fontsize=8.5)
    fig.tight_layout(rect=[0.03, 0.03, 1, 0.95])
    finalize_and_save(fig, 'P2E11d_B_oscillation_all')
    plt.close(fig)


def fig_c_joint_summary():
    df_class = pd.read_csv(os.path.join(DIAG_DIR, 'p2e11d_stability_classification.csv'))
    n_stable = df_class.groupby('controller')['classification_v2'].apply(lambda s: (s == 'STABLE').sum())
    mean_jval = df_class.groupby('controller')['J_val'].mean()

    fig, ax1 = plt.subplots(figsize=(SINGLE_COL_W, 3.2))
    x = np.arange(len(ORDER))
    colors = ['0.6', '0.2'] + [SEED_COLOR[s] for s in SEEDS]
    bars = ax1.bar(x, [mean_jval[c] for c in ORDER], color=colors, edgecolor='black', linewidth=0.5)
    ax1.axhline(mean_jval['droop_star'], color='black', linestyle='--', linewidth=0.8)
    ax1.set_ylabel(r'mean $J_{val,P2}$ (6 escenarios)')
    ax1.set_xticks(x)
    ax1.set_xticklabels(LABELS, rotation=40, ha='right', fontsize=6.5)
    style_axes(ax1)

    ax2 = ax1.twinx()
    ax2.plot(x, [n_stable[c] for c in ORDER], marker='D', color='black', markersize=5,
             linestyle='none', zorder=5)
    ax2.set_ylabel('# escenarios STABLE (de 6)')
    ax2.set_ylim(-0.3, 6.3)

    ax1.set_title('P2-E11d-C -- J_val_P2 (barras) y # escenarios STABLE\n(rombos, classify_v2 sobre las 6 de validation)',
                  fontsize=7.8)
    fig.tight_layout()
    finalize_and_save(fig, 'P2E11d_C_joint_summary')
    plt.close(fig)


def main():
    fig_a_classification_grid()
    fig_b_oscillation_all_scenarios()
    fig_c_joint_summary()


if __name__ == '__main__':
    main()
