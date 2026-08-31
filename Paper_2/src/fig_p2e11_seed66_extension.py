#!/usr/bin/env python
"""
P2-E11/P2-E11d figures, extended to include seed66 (DEC-P2-043) alongside
the 5 original seeds. Mirrors fig_p2e11_validation_comparison.py,
fig_p2e11b_trajectory_demo.py, fig_p2e11c_oscillation_check.py, and
fig_p2e11d_full_stability_screen.py structurally (same plot logic), reading
the "_with_seed66" combined data files produced by
stage_p2e11_seed66_extension.py, and saving under NEW figure names (suffix
"_with_seed66") -- the original 12 frozen figures are NOT overwritten.
"""
import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

sys.path.insert(0, os.path.dirname(__file__))
from p2_figures_common import style_axes, finalize_and_save, SINGLE_COL_W, DOUBLE_COL_W

DIAG_DIR = os.path.join('Paper_2', 'artifacts', 'diagnostics')
TRAJ_DIR = os.path.join('Paper_2', 'artifacts', 'trajectories')
SEEDS = [11, 22, 33, 44, 55, 66]
SEED_COLOR = {11: 'C0', 22: 'C1', 33: 'C3', 44: 'C2', 55: 'C4', 66: 'C5'}
BEST_J = {11: 0.5299, 22: 0.5263, 33: 0.5769, 44: 0.5217, 55: 0.5444, 66: 0.5432}
BEST_EP = {11: 400, 22: 1600, 33: 400, 44: 600, 55: 1400, 66: 1200}


# ================= Stage 1: validation comparison (F1-F4) =================

def fig1_learning_curves():
    fig, ax = plt.subplots(figsize=(DOUBLE_COL_W, 3.2))
    for seed in SEEDS:
        df = pd.read_csv(os.path.join(DIAG_DIR, 'p2e9_seeds', f'seed{seed}_eval_log.csv'))
        ax.plot(df['episode'], df['J_val_P2'], color=SEED_COLOR[seed], linewidth=1.1,
                label=f'seed {seed}', marker='o', markersize=2.2)
        ax.plot(BEST_EP[seed], BEST_J[seed], marker='*', markersize=11, color=SEED_COLOR[seed],
                markeredgecolor='black', markeredgewidth=0.5, zorder=5)

    comp = pd.read_csv(os.path.join(DIAG_DIR, 'p2e11_validation_comparison_summary_with_seed66.csv'), index_col=0)
    droop_j = comp.loc['droop_star', 'J_val_mean']
    noffc_j = comp.loc['NoFFC', 'J_val_mean']
    ax.axhline(droop_j, color='0.2', linestyle='--', linewidth=1.0, label='droop* (baseline)')
    ax.axhline(noffc_j, color='0.6', linestyle=':', linewidth=1.0, label='NoFFC')

    ax.set_xlabel('Episodio de entrenamiento')
    ax.set_ylabel(r'$J_{val,P2}$ (validation, 6 escenarios)')
    ax.set_title('F1 -- Curvas de aprendizaje por seed, incl. seed66 (estrella = mejor checkpoint)', fontsize=8.5)
    style_axes(ax)
    ax.legend(fontsize=6.2, ncol=4, loc='upper right')
    fig.tight_layout()
    finalize_and_save(fig, 'P2E11_F1_learning_curves_with_seed66')
    plt.close(fig)


def fig2_bar_comparison():
    comp = pd.read_csv(os.path.join(DIAG_DIR, 'p2e11_validation_comparison_summary_with_seed66.csv'), index_col=0)
    order = ['NoFFC', 'droop_star'] + [f'seed{s}' for s in SEEDS]
    labels = ['NoFFC', 'droop*'] + [f'seed {s}' for s in SEEDS]
    colors = ['0.6', '0.2'] + [SEED_COLOR[s] for s in SEEDS]
    values = [comp.loc[c, 'J_val_mean'] for c in order]

    fig, ax = plt.subplots(figsize=(SINGLE_COL_W, 3.0))
    ax.bar(labels, values, color=colors, edgecolor='black', linewidth=0.5)
    ax.axhline(comp.loc['droop_star', 'J_val_mean'], color='black', linestyle='--', linewidth=0.8)
    ax.set_ylabel(r'mean $J_{val,P2}$ (validation)')
    ax.set_title('F2 -- Comparacion global, incl. seed66 (menor = mejor)', fontsize=8.5)
    plt.setp(ax.get_xticklabels(), rotation=40, ha='right', fontsize=6.5)
    style_axes(ax)
    fig.tight_layout()
    finalize_and_save(fig, 'P2E11_F2_bar_comparison_with_seed66')
    plt.close(fig)


def fig3_if_ir_scatter():
    df = pd.read_csv(os.path.join(DIAG_DIR, 'p2e11_validation_comparison_with_seed66.csv'))
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
    ax.set_title('F3 -- Preview en validation, incl. seed66 (rombos=media por seed)\n'
                  'lineas punteadas: SS21 design targets, NO el gate final', fontsize=7.5)
    style_axes(ax)
    ax.legend(fontsize=6, ncol=2, loc='lower left')
    fig.tight_layout()
    finalize_and_save(fig, 'P2E11_F3_if_ir_preview_with_seed66')
    plt.close(fig)


def fig4_heatmap():
    df = pd.read_csv(os.path.join(DIAG_DIR, 'p2e11_validation_comparison_with_seed66.csv'))
    order = ['NoFFC', 'droop_star'] + [f'seed{s}' for s in SEEDS]
    labels = ['NoFFC', 'droop*'] + [f'seed {s}' for s in SEEDS]
    scenarios = sorted(df['scenario'].unique())
    mat = np.zeros((len(order), len(scenarios)))
    for i, c in enumerate(order):
        for j, s in enumerate(scenarios):
            row = df[(df['controller'] == c) & (df['scenario'] == s)]
            mat[i, j] = row['J_val'].values[0]

    fig, ax = plt.subplots(figsize=(DOUBLE_COL_W, 3.7))
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
    ax.set_title('F4 -- $J_{val,P2}$ por escenario de validation, incl. seed66 (verde=mejor)', fontsize=8.5)
    fig.tight_layout()
    finalize_and_save(fig, 'P2E11_F4_scenario_heatmap_with_seed66')
    plt.close(fig)


# ================= Stage b: trajectory demo =================

STYLE_B = {
    'NoFFC':      dict(color='black', linestyle=':', linewidth=1.3),
    'droop_star': dict(color='0.35', linestyle='-', linewidth=1.3),
    'TD3_seed44': dict(color='C2', linestyle='-', linewidth=1.4),
    'TD3_seed66': dict(color='C5', linestyle='-', linewidth=1.4),
}
LABEL_B = {'NoFFC': 'NoFFC', 'droop_star': 'droop*', 'TD3_seed44': 'TD3 (seed 44)',
           'TD3_seed66': 'TD3 (seed 66)'}
TD_B = 1.0


def plot_scenario_b(npz, scen_label, title, window):
    fig, axes = plt.subplots(3, 1, figsize=(DOUBLE_COL_W, 6.0), sharex=True)
    axF, axR, axP = axes
    for ctrl in ['NoFFC', 'droop_star', 'TD3_seed44', 'TD3_seed66']:
        prefix = f'{scen_label}__{ctrl}__'
        t = npz[prefix + 't']
        tau = t - TD_B
        w = (tau >= window[0]) & (tau <= window[1])
        f_worst = npz[prefix + 'f_worst_hz']
        rocof = npz[prefix + 'rocof_worst_hz_s']
        pc1 = npz[prefix + 'p_command1_mw']
        pc2 = npz[prefix + 'p_command2_mw']
        pd1 = npz[prefix + 'p_delivered1_mw']
        pd2 = npz[prefix + 'p_delivered2_mw']

        style = STYLE_B[ctrl]
        axF.plot(tau[w], f_worst[w], label=LABEL_B[ctrl], **style)
        axR.plot(tau[w], rocof[w], **style)
        axP.plot(tau[w], pd1[w] + pd2[w], **style)
        if ctrl != 'NoFFC':
            axP.plot(tau[w], pc1[w] + pc2[w], color=style['color'], linestyle='--',
                      linewidth=0.7, alpha=0.6)

    axF.set_ylabel('Peor $f$ (Hz)\n(10 GEN_BUSES)')
    axR.set_ylabel('Peor |RoCoF|\n(Hz/s)')
    axP.set_ylabel('$P_{BESS1}+P_{BESS2}$\n(MW)')
    axP.set_xlabel(r'$\tau = t - t_{event}$ (s)')
    axF.set_title(f'{title} -- incl. seed66\nlinea solida=entregado, discontinua=comando (droop*/TD3)', fontsize=8.5)
    for ax in axes:
        style_axes(ax)
        ax.axvline(0.0, color='0.5', linewidth=0.8, zorder=1)
    axF.legend(fontsize=7, loc='lower right')
    fig.align_ylabels(axes)
    fig.tight_layout()
    finalize_and_save(fig, f'P2E11b_{scen_label}_trajectory_with_seed66')
    plt.close(fig)


def fig_b_trajectories():
    npz = np.load(os.path.join(TRAJ_DIR, 'p2e11b_trajectory_demo_with_seed66.npz'))
    plot_scenario_b(npz, 'gen_val', 'Evento GENROU_6, rho=0.6 (validation)', window=(-0.3, 5.0))
    plot_scenario_b(npz, 'load_val', 'Evento PQ_10, alpha_L=0.3 (validation)', window=(-0.2, 4.0))


# ================= Stage c: oscillation persistence =================

def fig_c_oscillation_persistence():
    df = pd.read_csv(os.path.join(DIAG_DIR, 'p2e11c_oscillation_check_with_seed66.csv'))
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
    fig.suptitle('P2-E11c -- persistencia de oscilacion del comando TD3, incl. seed66 (no capturada por $J_{val,P2}$)',
                 fontsize=8.5)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    finalize_and_save(fig, 'P2E11c_oscillation_persistence_with_seed66')
    plt.close(fig)


# ================= Stage d: full stability screen (A/B/C) =================

ORDER_D = ['NoFFC', 'droop_star'] + [f'seed{s}' for s in SEEDS]
LABELS_D = ['NoFFC', 'droop*'] + [f'seed {s}' for s in SEEDS]
CLASS_COLOR = {'STABLE': '#2a9d3f', 'MARGINAL': '#e8a33d', 'LIMIT_CYCLE': '#d1495b',
               'NUMERICAL_FAILURE': '#333333'}
CLASS_CODE = {'STABLE': 0, 'MARGINAL': 1, 'LIMIT_CYCLE': 2, 'NUMERICAL_FAILURE': 3}


def fig_a_classification_grid():
    df = pd.read_csv(os.path.join(DIAG_DIR, 'p2e11d_stability_classification_with_seed66.csv'))
    scenarios = sorted(df['scenario_idx'].unique())
    mat = np.zeros((len(ORDER_D), len(scenarios)))
    for i, c in enumerate(ORDER_D):
        for j, s in enumerate(scenarios):
            row = df[(df['controller'] == c) & (df['scenario_idx'] == s)].iloc[0]
            mat[i, j] = CLASS_CODE[row['classification_v2']]

    fig, ax = plt.subplots(figsize=(DOUBLE_COL_W, 3.7))
    cmap = plt.matplotlib.colors.ListedColormap(
        [CLASS_COLOR['STABLE'], CLASS_COLOR['MARGINAL'], CLASS_COLOR['LIMIT_CYCLE'],
         CLASS_COLOR['NUMERICAL_FAILURE']])
    ax.imshow(mat, cmap=cmap, vmin=-0.5, vmax=3.5, aspect='auto')
    ax.set_xticks(range(len(scenarios)))
    ax.set_xticklabels([f'gen op{j+1}' if j < 3 else f'load op{j-2}' for j in scenarios], fontsize=7)
    ax.set_yticks(range(len(ORDER_D)))
    ax.set_yticklabels(LABELS_D, fontsize=7.5)
    for i in range(len(ORDER_D)):
        for j in range(len(scenarios)):
            row = df[(df['controller'] == ORDER_D[i]) & (df['scenario_idx'] == scenarios[j])].iloc[0]
            ax.text(j, i, row['classification_v2'][:4], ha='center', va='center', fontsize=5.5,
                    color='white')
    handles = [Patch(facecolor=v, label=k) for k, v in CLASS_COLOR.items() if k != 'NUMERICAL_FAILURE']
    ax.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=7)
    ax.set_title('P2-E11d-A -- clasificacion classify_v2 (DEC-P2-017), incl. seed66, 6 escenarios de validation',
                 fontsize=8.5)
    fig.tight_layout()
    finalize_and_save(fig, 'P2E11d_A_classification_grid_with_seed66')
    plt.close(fig)


def fig_b_oscillation_all_scenarios():
    df = pd.read_csv(os.path.join(DIAG_DIR, 'p2e11d_oscillation_full_with_seed66.csv'))
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
    fig.suptitle('P2-E11d-B -- persistencia de oscilacion, incl. seed66, los 6 escenarios de validation', fontsize=8.5)
    fig.tight_layout(rect=[0.03, 0.03, 1, 0.95])
    finalize_and_save(fig, 'P2E11d_B_oscillation_all_with_seed66')
    plt.close(fig)


def fig_c_joint_summary():
    df_class = pd.read_csv(os.path.join(DIAG_DIR, 'p2e11d_stability_classification_with_seed66.csv'))
    n_stable = df_class.groupby('controller')['classification_v2'].apply(lambda s: (s == 'STABLE').sum())
    mean_jval = df_class.groupby('controller')['J_val'].mean()

    fig, ax1 = plt.subplots(figsize=(SINGLE_COL_W, 3.2))
    x = np.arange(len(ORDER_D))
    colors = ['0.6', '0.2'] + [SEED_COLOR[s] for s in SEEDS]
    ax1.bar(x, [mean_jval[c] for c in ORDER_D], color=colors, edgecolor='black', linewidth=0.5)
    ax1.axhline(mean_jval['droop_star'], color='black', linestyle='--', linewidth=0.8)
    ax1.set_ylabel(r'mean $J_{val,P2}$ (6 escenarios)')
    ax1.set_xticks(x)
    ax1.set_xticklabels(LABELS_D, rotation=40, ha='right', fontsize=6.5)
    style_axes(ax1)

    ax2 = ax1.twinx()
    ax2.plot(x, [n_stable[c] for c in ORDER_D], marker='D', color='black', markersize=5,
             linestyle='none', zorder=5)
    ax2.set_ylabel('# escenarios STABLE (de 6)')
    ax2.set_ylim(-0.3, 6.3)

    ax1.set_title('P2-E11d-C -- $J_{val,P2}$ (barras) y # escenarios STABLE, incl. seed66\n(rombos, classify_v2 sobre las 6 de validation)',
                  fontsize=7.8)
    fig.tight_layout()
    finalize_and_save(fig, 'P2E11d_C_joint_summary_with_seed66')
    plt.close(fig)


def main():
    fig1_learning_curves()
    fig2_bar_comparison()
    fig3_if_ir_scatter()
    fig4_heatmap()
    fig_b_trajectories()
    fig_c_oscillation_persistence()
    fig_a_classification_grid()
    fig_b_oscillation_all_scenarios()
    fig_c_joint_summary()


if __name__ == '__main__':
    main()
