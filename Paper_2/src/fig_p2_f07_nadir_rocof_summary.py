#!/usr/bin/env python
"""P2_F07: quantitative summary of I_f, I_r improvement across configurations
for both DESIGN scenarios. Does not hide null/negative results."""
import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from p2_figures_common import OUT_DIR, PAIR_COLOR

META = pd.read_csv(os.path.join(OUT_DIR, 'figure_metadata.csv'))
CONFIGS = [('NoFFC', '16_20', 'NoFFC'), ('F+R', '12_13', 'F+R (12,13)'),
           ('F+R', '16_24', 'F+R (16,24)'), ('F+R', '16_20', 'F+R (16,20)')]
SCENARIOS = ['gen_severe', 'load_severe']


def get_metrics(scenario):
    noffc = META[(META['scenario'] == scenario) & (META['controller'] == 'NoFFC')].iloc[0]
    base_f, base_r = abs(noffc['nadir_value_hz'] - 60.0), noffc['rocof_max_hz_s']
    rows = []
    for controller, buses, label in CONFIGS:
        m = META[(META['scenario'] == scenario) & (META['controller'] == controller) &
                  (META['bess_buses'] == buses)].iloc[0]
        i_f = (base_f - abs(m['nadir_value_hz'] - 60.0)) / base_f
        i_r = (base_r - m['rocof_max_hz_s']) / base_r
        rows.append(dict(label=label, I_f=i_f * 100, I_r=i_r * 100))
    return pd.DataFrame(rows)


def main():
    fig, (axF, axR) = plt.subplots(1, 2, figsize=(7.0, 3.2))
    x = np.arange(len(CONFIGS))
    width = 0.35
    colors = {'NoFFC': 'black', 'F+R (12,13)': PAIR_COLOR['12_13'],
              'F+R (16,24)': PAIR_COLOR['16_24'], 'F+R (16,20)': PAIR_COLOR['16_20']}

    for i, scenario in enumerate(SCENARIOS):
        df = get_metrics(scenario)
        offset = (i - 0.5) * width
        bar_colors = [colors[l] for l in df['label']]
        axF.bar(x + offset, df['I_f'], width, label=scenario, edgecolor=bar_colors, fill=(i == 0),
                facecolor=bar_colors if i == 0 else 'none', linewidth=1.3,
                hatch=None if i == 0 else '///')
        axR.bar(x + offset, df['I_r'], width, label=scenario, edgecolor=bar_colors, fill=(i == 0),
                facecolor=bar_colors if i == 0 else 'none', linewidth=1.3,
                hatch=None if i == 0 else '///')

    for ax, ylabel, title in [(axF, r'$I_f$ (%)', 'Frequency nadir improvement'),
                               (axR, r'$I_r$ (%)', 'RoCoF improvement')]:
        ax.axhline(0, color='0.3', linewidth=0.8)
        ax.axhline(10, color='0.5', linewidth=0.8, linestyle=':')
        ax.text(len(CONFIGS) - 0.5, 10, ' 10% threshold', fontsize=6, color='0.4', va='bottom', ha='right')
        ax.set_xticks(x)
        ax.set_xticklabels([c[2] for c in CONFIGS], rotation=25, ha='right', fontsize=6.5)
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=8)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, axis='y', linestyle=':', linewidth=0.4, alpha=0.35)

    handles = [plt.Rectangle((0, 0), 1, 1, facecolor='0.5', edgecolor='0.5', label='gen_severe'),
               plt.Rectangle((0, 0), 1, 1, facecolor='none', edgecolor='0.5', hatch='///', label='load_severe')]
    fig.legend(handles=handles, loc='upper center', ncol=2, fontsize=7, bbox_to_anchor=(0.5, 1.06))

    fig.tight_layout()
    from p2_figures_common import finalize_and_save
    finalize_and_save(fig, 'P2_F07_nadir_rocof_summary')
    plt.close(fig)


if __name__ == '__main__':
    main()
