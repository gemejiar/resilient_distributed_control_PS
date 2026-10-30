"""DEC-065 corrected Proposition OS: numerical evaluation of the linearised DAE gain bound (no TDS; power flow + Jacobians only).
Statement (proved in IEEE39_DEC065_proofs.md, Theorem OS-L): for reference trajectories u^a, u^b with |u^a_k(s) - u^b_k(s)| <= s w_k on [t_e, t_e + T] (zero initial difference, same x(t_e), same d), the first-order output difference is
    Delta y_j(T) = sum_k int_0^T [ C_x e^{A(T-s)} B_k ]_j  Delta u_k(s) ds + [C_u]_jk Delta u_k(T),
bounded by  sum_k w_k ( int_0^T |G_jk(T-s)| s ds + |C_u,jk| T ),  G_jk(tau) = [C_x e^{A tau} B_k]_j.
A, B, C_x, C_u are the reduced Jacobians of the DAE (algebraic variables eliminated, index-1) at the pre-event equilibrium; they are ESTIMATES (frozen linearisation, no Lipschitz certificate).
Controller rate bounds: B5'/B4' w = vbar (box row Q1, by construction); B1s w_P = k_i |1 - omega| (omega continuous), w_Q = K_IQ K_V |V0 - V| with the jump |V0 - V(t_e+)| from the stored series; B2: v_B2(t_e+) measured at the first sample (exact value of the sampled law at the jump) and the 50 ms maximum of the stored commands (empirical; no derived bound).
Compares the bound with the observed output differences between runs and checks the linear model against the observed pairwise differences.  Writes IEEE39_DEC065_os_check.json exclusively with 'write'."""
from __future__ import annotations

import json
import sys

import numpy as np
from scipy.linalg import expm

import dec054_common as C54
import dec055_common as C55
import dec059_eq as EQ
import dec059_tds as T

TE, TT = 5.0, 0.05
CELLS = [("OC1", "M3REV3", "b21P_S2"), ("OC1", "M3REV3", "b31P_S2"), ("OC1", "M3REV3", "b39P_S2"), ("OC2", "M3OS", "b21P_S2"), ("OC2", "M3OS", "b31P_S2"), ("OC2", "M3OS", "b39P_S2")]
PRE = {"B5P": "D62TEST_B5P_", "B4P": "D62CMP_B4P_", "B2": "D62CMP_B2_", "B1S": "D62CMP_B1S_"}


def load(run):
    z = np.load(T.RUNS / run / "series.npz", allow_pickle=True)
    return z


def main(write=False):
    out = {"label": "DEC065_OS_LINEARISED_GAIN_ESTIMATE_NO_TDS", "cells": {}}
    cache = {}
    for oc, d, cell in CELLS:
        e = cache.get((oc, d))
        if e is None:
            e = EQ.Eq(oc, T.dispatch_z(oc, d))
            lin = e.plant.L.linearize(e.system, e.ctx, cache=e.cache)
            rows = np.concatenate([e.st["a_p"], e.st["a_q"], e.st["a_v"]]).astype(int)
            A, B, Cx, Cu = lin["A"], lin["B_u"], lin["Cy_x"][rows], lin["Cy_u"][rows]
            n = 10
            h = 0.001
            M = expm(A * h)
            taus = np.arange(0, int(TT / h) + 1) * h
            Gs = []
            X = B.copy()
            for _ in taus:
                Gs.append(Cx @ X)
                X = M @ X
            Gs = np.array(Gs)                                      # (nt, rows, 20): G(tau)
            e = (e, A, B, Cx, Cu, Gs, taus, h, rows)
            cache[(oc, d)] = e
        ee, A, B, Cx, Cu, Gs, taus, h, rows = e
        rs = EQ.refset(ee.ctx, ee.st)
        vbar = rs["vbar"]
        s_grid = taus
        # int_0^T |G(T-s)| s ds  (trapezoid on the 1 ms grid) per (row, input)
        wint = np.trapezoid(np.abs(Gs[::-1]) * s_grid[:, None, None], dx=h, axis=0) + np.abs(Cu) * TT

        def bound(w):
            return (wint * w[None, :]).sum(axis=1)

        runs = {c: load(f"{p}{oc}_{d}_{cell}") for c, p in PRE.items()}
        t = runs["B2"]["cmd_t"]
        i0 = int(np.searchsorted(t, TE - 1e-9))
        k50 = (t >= TE) & (t <= TE + TT)
        ub = {c: np.hstack([z["cmd_pset"], z["cmd_qset"]]) for c, z in runs.items()}
        rate = {c: np.abs(ub[c][k50] - ub[c][i0][None, :]).max(axis=0) / TT for c in ub}       # max displacement / T per component (empirical)
        v_te = {c: np.abs(ub[c][i0 + 1] - ub[c][i0]) / (t[i0 + 1] - t[i0]) for c in ub}        # sampled rate at the first step after t_e
        w = {"B5P": vbar, "B4P": vbar}
        w["B2"] = rate["B2"]
        w["B1S"] = rate["B1S"]
        # observed output differences at t_e + T
        tt = runs["B2"]["t"]
        ia = int(np.searchsorted(tt, TE + TT))
        ib = int(np.searchsorted(tt, TE - 1e-9))

        def outs(z):
            P, Q, V = z["P"], z["Q"], z["V"]
            return np.concatenate([P[ia], Q[ia], V[ia][[b - 1 for b in C54.UNIT_BUS]]])

        obs = {c: np.abs(outs(runs["B5P"]) - outs(runs[c])) for c in ("B4P", "B2", "B1S")}
        key = f"{oc}_{d}_{cell}"
        out["cells"][key] = {}
        for c in ("B4P", "B2", "B1S"):
            wsum = w["B5P"] + w[c]
            bnd = bound(wsum)
            # linear model driven by the ACTUAL command difference (consistency of the gain estimate)
            du = ub["B5P"][k50] - ub[c][k50]
            tk = t[k50] - TE
            lin_pred = np.zeros(len(rows))
            dts = np.gradient(t[k50])                              # actual step (the local refinement uses dt/16 around t_e)
            for s_i, ds, dt_i in zip(tk, du, dts):
                tau = TT - s_i
                gi = min(int(round(tau / h)), len(taus) - 1)
                lin_pred += Gs[gi] @ ds * dt_i
            lin_pred += Cu @ du[-1]
            out["cells"][key][c] = {"bound_max": float(bnd.max()), "observed_max": float(obs[c].max()), "ratio_bound_over_observed": float(bnd.max() / max(obs[c].max(), 1e-16)),
                                    "linear_prediction_max": float(np.abs(lin_pred).max()), "rate_ratio_to_vbar_max": float((w[c] / vbar).max()), "v_te_ratio_to_vbar_max": float((v_te[c] / vbar).max()),
                                    "bound_holds": bool((obs[c] <= bnd + 1e-12).all())}
        print(key, {c: (round(v["bound_max"], 6), round(v["observed_max"], 6), round(v["linear_prediction_max"], 6), round(v["rate_ratio_to_vbar_max"], 2), v["bound_holds"]) for c, v in out["cells"][key].items()}, flush=True)
    out["all_bounds_hold"] = all(v["bound_holds"] for c in out["cells"].values() for v in c.values())
    if write:
        with open(C55.ART / "IEEE39_DEC065_os_check.json", "x", encoding="utf-8") as f:
            json.dump(out, f, indent=1, default=float)


if __name__ == "__main__":
    main("write" in sys.argv)
