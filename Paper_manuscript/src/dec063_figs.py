"""DEC-063 figure F12 (QP activity) from existing runs and IEEE39_DEC063_qp_*.json.  Exclusive PNG write in figures_main/.
  (a) reference cell OC1 rev3 b21 S2: |v - v_nom| of B5' and B4' and the CLF slack of B5' in the 8 s after the event
  (b) B5' - B4' commanded-reference difference (max over units) and f_COI difference in time, same cell
  (c) per run: smallest distance of any box barrier row to its binding threshold vbar/alpha (negative = the row could bind), M3 dispatches vs M0
  <venv python> dec063_figs.py"""
from __future__ import annotations

import json

import numpy as np

import dec055_common as C55
import dec059_figs as F59
import dec059_tds as T

BLUE, ORANGE, AQUA, YELLOW, INK, INK2, GRID = F59.BLUE, F59.ORANGE, F59.AQUA, F59.YELLOW, F59.INK, F59.INK2, F59.GRID


def main():
    plt = F59._plt()
    r5, r4 = "D62TEST_B5P_OC1_M3REV3_b21P_S2", "D62CMP_B4P_OC1_M3REV3_b21P_S2"
    z5, z4 = np.load(T.RUNS / r5 / "series.npz", allow_pickle=True), np.load(T.RUNS / r4 / "series.npz", allow_pickle=True)
    fig, ax = plt.subplots(1, 3, figsize=(7.4, 2.8))
    for z, col, lab in ((z5, BLUE, "B5'"), (z4, ORANGE, "B4'")):
        m = (z["b5_t"] >= 5) & (z["b5_t"] <= 9)
        ax[0].plot(z["b5_t"][m], z["b5_dv"][m], color=col, lw=1.0, label=lab)
    m = (z5["b5_t"] >= 5) & (z5["b5_t"] <= 9)
    a2 = ax[0].twinx()
    a2.plot(z5["b5_t"][m], z5["b5_slack"][m], color=AQUA, lw=0.8)
    a2.set_ylabel("B5' CLF slack (normalised)", fontsize=6)
    a2.tick_params(labelsize=6)
    ax[0].set(xlabel="time (s)", ylabel="max |v - v_nom| (pu/s)", title="(a) QP modification of the command")
    ax[0].legend(fontsize=6)
    n = min(len(z5["cmd_t"]), len(z4["cmd_t"]))
    d = np.abs(z5["cmd_pset"][:n] - z4["cmd_pset"][:n]).max(axis=1)
    t = z5["cmd_t"][:n]
    k = (t >= 5) & (t <= 30)
    ax[1].plot(t[k], d[k] * 1e3, color=BLUE, lw=1.0)
    ax[1].set(xlabel="time (s)", ylabel="max_i |P*_B5' - P*_B4'| (mpu)", title="(b) effect of the CLF row")
    b = json.loads((C55.ART / "IEEE39_DEC063_qp_binding.json").read_text(encoding="utf-8"))["runs"]
    xs, ys, cs = [], [], []
    for i, (r, v) in enumerate(sorted(b.items())):
        xs.append(i)
        ys.append(v["min_gap_box_rows"])
        cs.append(ORANGE if "_M0_" in r and "OC1" in r else BLUE)
    ax[2].scatter(xs, ys, s=10, c=cs)
    ax[2].axhline(0, color=INK2, lw=0.8)
    ax[2].set(xlabel="B5'/B4' run", ylabel="min (c_j - vbar_k/alpha) (pu)", title="(c) can a box barrier row bind? orange: OC1 M0")
    for a in ax:
        a.title.set_fontsize(7)
    fig.tight_layout()
    import os
    if os.environ.get("DEC059_FIG_PREVIEW"):
        fig.savefig(os.path.join(os.environ["DEC059_FIG_PREVIEW"], "F12.png"), dpi=200, bbox_inches="tight")
        return
    with open(C55.FIG / "IEEE39_DEC063_F12_QP_activity.png", "xb") as f:
        fig.savefig(f, dpi=200, format="png", bbox_inches="tight")


if __name__ == "__main__":
    main()
