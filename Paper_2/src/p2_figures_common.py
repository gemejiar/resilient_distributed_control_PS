#!/usr/bin/env python
"""
Paper_2 figure package -- shared style/loading utilities.

All time axes use tau = t - TD (seconds, event at tau=0). Matplotlib only
(no seaborn). Consistent controller styling across every figure:
  NoFFC     -> black, dotted
  F+R       -> solid (color encodes BESS-pair variant when >1 is shown)
  Open-loop -> dashed
"""
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

TRAJ_NPZ = os.path.join('Paper_2', 'artifacts', 'trajectories', 'figures', 'p2_figures_trajectories.npz')
OUT_DIR = os.path.join('Paper_2', 'figures_main')
os.makedirs(OUT_DIR, exist_ok=True)

TD = 1.0  # disturbance instant (p2_common.TD)

CONTROLLER_STYLE = {
    'NoFFC':    dict(color='black', linestyle=':', linewidth=1.3),
    'F+R':      dict(color='C0', linestyle='-', linewidth=1.3),
    'OpenLoop': dict(color='C1', linestyle='--', linewidth=1.3),
}
PAIR_COLOR = {'16_20': 'C0', '12_13': 'C3', '16_24': 'C2'}
PAIR_LABEL = {'16_20': 'F+R (16,20)', '12_13': 'F+R (12,13)', '16_24': 'F+R (16,24)'}

SINGLE_COL_W = 3.5   # inches, ~89mm
DOUBLE_COL_W = 7.16  # inches, ~182mm

plt.rcParams.update({
    'font.size': 8,
    'font.family': 'serif',
    'axes.linewidth': 0.7,
    'xtick.direction': 'in',
    'ytick.direction': 'in',
    'legend.frameon': False,
    'legend.fontsize': 7,
    'axes.grid': True,
    'grid.linewidth': 0.4,
    'grid.alpha': 0.35,
    'axes.axisbelow': True,
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'savefig.facecolor': 'white',
})


class Runs:
    """Lazy accessor for a single run's arrays, with tau precomputed."""

    def __init__(self, npz, key):
        self._npz = npz
        self._key = key

    def __getitem__(self, name):
        return self._npz[f'{self._key}__{name}']

    @property
    def tau(self):
        return self['t'] - TD


def load_npz():
    return np.load(TRAJ_NPZ)


def run(npz, scenario, tag):
    return Runs(npz, f'{scenario}__{tag}')


def style_axes(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, linestyle=':', linewidth=0.4, alpha=0.35)


def mark_event(ax, label='Event', y_frac=0.94):
    ax.axvline(0.0, color='0.5', linewidth=0.8, zorder=1)
    ylim = ax.get_ylim()
    ax.text(0.0, ylim[0] + y_frac * (ylim[1] - ylim[0]), f' {label}', fontsize=6.5,
            color='0.35', va='top', ha='left')


def finalize_and_save(fig, name):
    """Saves single-column and double-column PNG+PDF, preserving the
    figure's original aspect ratio (captured once, before any resizing)."""
    w0, h0 = fig.get_size_inches()
    aspect = h0 / w0
    for suffix, w in [('_1col', SINGLE_COL_W), ('_2col', DOUBLE_COL_W)]:
        fig.set_size_inches(w, w * aspect)
        fig.savefig(os.path.join(OUT_DIR, f'{name}{suffix}.png'), dpi=300, bbox_inches='tight')
        fig.savefig(os.path.join(OUT_DIR, f'{name}{suffix}.pdf'), bbox_inches='tight')
    print(f"Saved: {name}_1col/_2col (.png/.pdf)")
