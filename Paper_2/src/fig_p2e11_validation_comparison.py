#!/usr/bin/env python
"""
P2-E11 -- figure package: validation-split comparison (NoFFC / droop* / 5
frozen TD3 checkpoints), used to preview success of the training process
before the single-shot P2-T1..T12 test (NOT opened here, NOT the plan's
final gate SS21).

F1: J_val_P2 learning curves per seed (validation, evaluated every 200
    episodes during P2-E9), droop* baseline as reference line, best point
    marked per seed.
F2: mean J_val_P2 over the 6 validation scenarios -- NoFFC / droop* / 5
    seeds, bar chart.
F3: I_f/I_r vs droop* (SS21 formula, validation preview only) per seed,
    scatter, with the plan's 10%/15% design-target lines shown as
    orientation only (explicitly not a gate verdict).
F4: per-scenario J_val_P2 heatmap (controller x validation scenario) --
    shows whether seed33's weakness is scenario-specific or general.
"""
import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from p2_figures_common import style_axes, finalize_and_save, SINGLE_COL_W, DOUBLE_COL_W

DIAG_DIR = os.path.join('Paper_2', 'artifacts', 'diagnostics')
SEEDS = [11, 22, 33, 44, 55]
SEED_COLOR = {11: 'C0', 22: 'C1', 33: 'C3', 44: 'C2', 55: 'C4'}
BEST_J = {11: 0.5299, 22: 0.5263, 33: 0.5769, 44: 0.5217, 55: 0.5444}
BEST_EP = {11: 400, 22: 1600, 33: 400, 44: 600, 55: 1400}


def fig1_learning_curves():
    fig, ax = plt.subplots(figsize=(DOUBLE_COL_W, 3.2))
    for seed in SEEDS:
        df = pd.read_csv(os.path.join(DIAG_DIR, 'p2e9_seeds', f'seed{seed}_eval_log.csv'))
        ax.plot(df['episode'], df['J_val_P2'], color=SEED_COLOR[seed], linewidth=1.1,
                label=f'seed {seed}', marker='o', markersize=2.2)
        ax.plot(BEST_EP[seed], BEST_J[seed], marker='*', markersize=11, color=SEED_COLOR[seed],
                markeredgecolor='black', markeredgewidth=0.5, zorder=5)

    comp = pd.read_csv(os.path.join(DIAG_DIR, 'p2e11_validation_comparison_summary.csv'), index_col=0)
    droop_j = comp.loc['droop_star', 'J_val_mean']
    noffc_j = comp.loc['NoFFC', 'J_val_mean']
    ax.axhline(droop_j, color='0.2', linestyle='--', linewidth=1.0, label='droop* (baseline)')
    ax.axhline(noffc_j, color='0.6', linestyle=':', linewidth=1.0, label='NoFFC')

    ax.set_xlabel('Episodio de entrenamiento')
    ax.set_ylabel(r'$J_{val,P2}$ (validation, 6 escenarios)')
    ax.set_title('F1 -- Curvas de aprendizaje por seed (estrella = mejor checkpoint)', fontsize=8.5)
    style_axes(ax)
    ax.legend(fontsize=6.2, ncol=4, loc='upper right')
    fig.tight_layout()
    finalize_and_save(fig, 'P2E11_F1_learning_curves')
    plt.close(fig)


def fig2_bar_comparison():
    comp = pd.read_csv(os.path.join(DIAG_DIR, 'p2e11_validation_comparison_summary.csv'), index_col=0)
    order = ['NoFFC', 'droop_star'] + [f'seed{s}' for s in SEEDS]
    labels = ['NoFFC', 'droop*'] + [f'seed {s}' for s in SEEDS]
    colors = ['0.6', '0.2'] + [SEED_COLOR[s] for s in SEEDS]
    values = [comp.loc[c, 'J_val_mean'] for c in order]

    fig, ax = plt.subplots(figsize=(SINGLE_COL_W, 3.0))
    bars = ax.bar(labels, values, color=colors, edgecolor='black', linewidth=0.5)
    ax.axhline(comp.loc['droop_star', 'J_val_mean'], color='black', linestyle='--', linewidth=0.8)
    ax.set_ylabel(r'mean $J_{val,P2}$ (validation)')
    ax.set_title('F2 -- Comparacion global (menor = mejor)', fontsize=8.5)
    plt.setp(ax.get_xticklabels(), rotation=40, ha='right', fontsize=6.5)
    style_axes(ax)
    fig.tight_layout()
    finalize_and_save(fig, 'P2E11_F2_bar_comparison')
    plt.close(fig)


def fig3_if_ir_scatter():
    df = pd.read_csv(os.path.join(DIAG_DIR, 'p2e11_validation_comparison.csv'))
    fig, ax = plt.subplots(figsize=(SINGLE_COL_W, 3.2))
    for seed in SEEDS:
        sub = df[df['controller'] == f'seed{seed}']
        ax.scatter(sub['I_f_vs_droop'] * 100, sub['I_r_vs_droop'] * 100, color=SEED_COLOR[seed],
                   s=22, alpha=0.55, label=f'seed {seed}')
        ax.scatter(sub['I_f_vs_droop'].mean() * 100, sub['I_r_vs_droop'].mean() * 100,
                   color=SEED_COLOR[seed], s=90, marker='D', edgecolor='black', linewidth=0.6, zorder=5)
    ax.axvline(10, color='0.5', linestyle=':', linewidth=0.8)
    ax.axhline(10, color='0.5', linestyle=':', linewidth=0.8)
    ax.axvline(15, color='0.75', linestyle=':', linewidth=0.6)
    ax.axhline(15, color='0.75', linestyle=':', linewidth=0.6)
    ax.axvline(0, color='black', linewidth=0.6)
    ax.axhline(0, color='black', linewidth=0.6)
    ax.text(10, ax.get_ylim()[1] * 0.95, '10%', fontsize=6, color='0.5')
    ax.text(15, ax.get_ylim()[1] * 0.85, '15%', fontsize=6, color='0.6')
    ax.set_xlabel(r'$I_f$ vs. droop* (%)')
    ax.set_ylabel(r'$I_r$ vs. droop* (%)')
    ax.set_title('F3 -- Preview en validation (rombos=media por seed)\n'
                  'lineas punteadas: SS21 design targets, NO el gate final', fontsize=7.5)
    style_axes(ax)
    ax.legend(fontsize=6, ncol=2, loc='lower left')
    fig.tight_layout()
    finalize_and_save(fig, 'P2E11_F3_if_ir_preview')
    plt.close(fig)


def fig4_heatmap():
    df = pd.read_csv(os.path.join(DIAG_DIR, 'p2e11_validation_comparison.csv'))
    order = ['NoFFC', 'droop_star'] + [f'seed{s}' for s in SEEDS]
    labels = ['NoFFC', 'droop*'] + [f'seed {s}' for s in SEEDS]
    scenarios = sorted(df['scenario'].unique())
    mat = np.zeros((len(order), len(scenarios)))
    for i, c in enumerate(order):
        for j, s in enumerate(scenarios):
            row = df[(df['controller'] == c) & (df['scenario'] == s)]
            mat[i, j] = row['J_val'].values[0]

    fig, ax = plt.subplots(figsize=(DOUBLE_COL_W, 3.4))
    im = ax.imshow(mat, cmap='RdYlGn_r', aspect='auto')
    ax.set_xticks(range(len(scenarios)))
    ax.set_xticklabels([s.replace("'", "").replace('kind: ', '')[:38] for s in
                         [str(sc) for sc in scenarios]], rotation=30, ha='right', fontsize=5.5)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(labels, fontsize=7)
    for i in range(len(order)):
        for j in range(len(scenarios)):
            ax.text(j, i, f'{mat[i,j]:.2f}', ha='center', va='center', fontsize=5.5)
    fig.colorbar(im, ax=ax, label=r'$J_{val,P2}$', shrink=0.85)
    ax.set_title('F4 -- $J_{val,P2}$ por escenario de validation (verde=mejor)', fontsize=8.5)
    fig.tight_layout()
    finalize_and_save(fig, 'P2E11_F4_scenario_heatmap')
    plt.close(fig)


def main():
    fig1_learning_curves()
    fig2_bar_comparison()
    fig3_if_ir_scatter()
    fig4_heatmap()


if __name__ == '__main__':
    main()
