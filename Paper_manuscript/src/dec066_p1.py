"""DEC-066 P1: window-resolved prediction (jump / 50 ms dense / 195 s grid) for the DEC-062 blind cells, from the EXISTING predictor (dec054_predictor, dec059_pred, dec059_os); 0 TDS.
For each (OC, dispatch, bus, severity): algebraic jump P+, dense 0-50 ms excursion (OS.DENSE), full-horizon excursion on the M3 grid ([0,1] 2^-8 trap, [1,10] 0.05, [10,195] 0.5 exact, parabolic refinement),
predicted trajectories P_i(t) = P+ + D_i(t), and the maxima observed in the stored TDS series per window.  Writes IEEE39_DEC066_P1_windows.csv and IEEE39_DEC066_P1_traj_<oc>_<m>_<cell>.npz exclusively.
Run: <venv python> dec066_p1.py <OC> <dispatch> [cell ...] [write]   (cells like b39P_S2; default all 9 TEST cells)"""
from __future__ import annotations

import csv
import json
import sys

import numpy as np

import dec054_opf as OPF
import dec054_predictor as PRD
import dec055_common as C55
import dec055_oc as OCM
import dec059_eq as EQ
import dec059_os as OS
import dec059_tds as T
import dec062_r5 as R5

U_D8 = 0.0109
TE = 5.0
UNITS = C55.UNITS


def klass(m):
    return "SAFE" if m >= U_D8 else "UNSAFE" if m <= -U_D8 else "INDET"


def tds_windows(oc, m, cell, pmax, pmin):
    z = np.load(T.RUNS / f"D62TEST_B5P_{oc}_{m}_{cell}" / "series.npz", allow_pickle=True)
    t, P = z["t"], z["P"]
    out = {}
    k = int(np.searchsorted(t, TE - 1e-9))
    wins = {"jump": (TE, TE + 1e-9), "fast": (TE, TE + 0.05), "slow": (TE + 0.05, 200.0), "all": (TE, 200.0)}
    for name, (a, b) in wins.items():
        w = (t >= a - 1e-9) & (t <= b + 1e-9)
        up = pmax[None, :] - P[w]
        i = np.unravel_index(up.argmin(), up.shape)
        out[name] = {"pmax_margin": float(up.min()), "unit": UNITS[i[1]], "t_after_event": float(t[w][i[0]] - TE)}
    return out, t, P


def main(oc, m, cells=None, write=False):
    plant = OCM.make_plant(oc)
    lim = plant.limits
    pmax, pmin = np.asarray(lim["pmax"], float), np.asarray(lim["pmin"], float)
    z = np.asarray(EQ.dispatch(oc, m)[0], float)
    rows = []
    for b in R5.TEST:
        for s in R5.SEV:
            cell = f"b{b}P_{s}"
            if cells and cell not in cells:
                continue
            amp = round(C55.oc_amp(s), 5)
            sc = OPF.Scenario(cell, b, "P", amp)
            jp = plant.jump(z, sc)
            A, f, Cm = plant.affine(z, sc)
            t50, D50, _ = PRD.propagate(A, f, Cm, OS.DENSE)
            ex = PRD.excursion(A, f, Cm)                              # M3 grid, 0-195 s, parabolic refinement
            tg, Dg, _ = PRD.propagate(A, f, Cm)
            Pp = jp["P_plus"]
            up50 = Pp + np.maximum(D50.max(axis=1), 0.0)
            upF = Pp + ex["E_up"]
            m_jump, m50, mF = pmax - Pp, pmax - up50, pmax - upF
            iF = int(mF.argmin())
            obs, t, P = tds_windows(oc, m, cell, pmax, pmin)
            pred_traj = Pp[:, None] + Dg                              # predicted P_i(t) on the M3 grid
            if write:
                with open(C55.ART / f"IEEE39_DEC066_P1_traj_{oc}_{m}_{cell}.npz", "xb") as fh:
                    np.savez_compressed(fh, t=tg, P_pred=pred_traj, t50=t50, P_pred50=Pp[:, None] + D50, P_jump=Pp, pmax=pmax, t_tds=t, P_tds=P)
            rows.append({"oc": oc, "dispatch": m, "cell": cell, "jump_margin": float(m_jump.min()), "jump_unit": UNITS[int(m_jump.argmin())],
                         "pred50_margin": float(m50.min()), "pred50_unit": UNITS[int(m50.argmin())],
                         "predF_margin": float(mF.min()), "predF_unit": UNITS[iF], "predF_t_after_event": float(ex["t_up"][iF]), "predF_sampling_error": float(ex["sampling_error_up"][iF]),
                         "tds_jump_margin": obs["jump"]["pmax_margin"], "tds_fast_margin": obs["fast"]["pmax_margin"], "tds_slow_margin": obs["slow"]["pmax_margin"], "tds_slow_unit": obs["slow"]["unit"],
                         "tds_slow_t": obs["slow"]["t_after_event"], "tds_all_margin": obs["all"]["pmax_margin"], "tds_all_unit": obs["all"]["unit"], "tds_all_t": obs["all"]["t_after_event"],
                         "class_pred50": klass(float(m50.min())), "class_predF": klass(float(mF.min())), "class_tds_all": klass(obs["all"]["pmax_margin"]), "class_tds_fast": klass(obs["fast"]["pmax_margin"]),
                         "ok": bool(ex["ok"])})
            print(oc, m, cell, {k: (round(v, 5) if isinstance(v, float) else v) for k, v in rows[-1].items() if k in ("jump_margin", "pred50_margin", "predF_margin", "predF_unit", "predF_t_after_event", "tds_all_margin", "tds_all_unit", "tds_all_t", "class_pred50", "class_predF", "class_tds_all")}, flush=True)
    if write and rows:
        with open(C55.ART / f"IEEE39_DEC066_P1_windows_{oc}_{m}.csv", "x", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    return rows


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if x != "write"]
    main(a[0], a[1], a[2:] or None, "write" in sys.argv)
