"""DEC-051 block B5 analysis (post-processing of the two perturbation simulations; no simulation).

For each run (perturbation +/- along the dominant slow mode) the quotient state e(t) = Qm [x_d(t) - x_d*, u(t) - u*] is formed (Qm removes the common rotor-angle drift), the Lyapunov value V = e_s^T P e_s
(scaled coordinates, P of IEEE39_DEC051_H4_matrices.npz) is evaluated and compared with the LINEAR prediction e(t) = expm(A_q t) e(0).  Also reported: unit voltages, frequency, P/Q/S margins,
reference rates and the DAE residual.  The comparison validates the local prediction; it does not replace the proof."""

from __future__ import annotations

import json

import numpy as np
import scipy.linalg as sl

import dec051_core as C
import run_dec051_equilibrium as EQ
import run_dec051_h4 as H4
from run_e0_ieee39 import ARTIFACTS_DIR as A, git_commit, sha256


def main() -> int:
    eq, system, ctx, st, ix, pred, u = H4.load_eq()
    d_idx = ix["d_idx"]
    n, N = len(d_idx), len(d_idx) + 20
    pin_pos = int(np.where(d_idx == int(eq["pin"]))[0][0])
    vnull = EQ.angle_null(system, ctx, st, ix, pred, u, pin_pos)
    Qm = EQ.quotient_matrix(vnull, pin_pos)
    mt = np.load(A / "IEEE39_DEC051_H4_matrices.npz")
    Aq, Psc, D = mt["Aq"], mt["P_scaled"], np.diag(mt["D"])
    lim = ctx["lim"]
    out = {"stage": "DEC-051 H4 validation", "git_commit": git_commit(), "runs": {}}
    slow = np.load(A / "IEEE39_DEC051_H4_mode.npz")
    for tag in ("plus", "minus"):
        f = A / f"IEEE39_DEC051_H4_perturb_{tag}.npz"
        z = dict(np.load(f))
        t = z["t"]
        xi = np.hstack([z["x_d"] - z["x_eq_d"][None, :], z["u"] - z["u_eq"][None, :]])
        E = (Qm @ xi.T).T                       # (T, N-1)
        Es = E @ D.T
        Vv = np.einsum("ti,ij,tj->t", Es, Psc, Es)
        nrm = np.linalg.norm(Es, axis=1)
        e0 = E[0]
        sel = np.unique(np.linspace(0, len(t) - 1, 60).astype(int))
        Vlin = []
        for i in sel:
            el = sl.expm(Aq * t[i]) @ e0 if i > 0 else e0
            els = D @ el
            Vlin.append(float(els @ Psc @ els))
        Vlin = np.array(Vlin)
        P, Q, Vu = z["P"], z["Q"], z["Vunit"]
        s_rel = lim["smax"] - np.hypot(P, Q)
        qref = z["u"][:, 10:] - z["u_eq"][None, 10:]
        late = t >= t[-1] - 100
        rate = np.abs(z["rates"]).max(axis=1)
        k = np.polyfit(t[(t > 100) & (t < t[-1])], np.log(np.maximum(np.abs(qref[(t > 100) & (t < t[-1])]).max(axis=1), 1e-30)), 1)
        out["runs"][tag] = {"tds_ok": bool(z["tds_ok"]), "t_end_s": float(z["t_end_s"]), "n_logged": int(len(t)), "sign": float(z["sign"]), "amp_scale": float(z["amp_scale"]),
                            "V_initial": float(Vv[0]), "V_final": float(Vv[-1]), "V_ratio_final_over_initial": float(Vv[-1] / Vv[0]), "V_monotone_decreasing_fraction": float(np.mean(np.diff(Vv) <= 1e-12 * Vv[:-1].max())),
                            "V_max_over_run_over_initial": float(Vv.max() / Vv[0]), "norm_scaled_e_initial": float(nrm[0]), "norm_scaled_e_final": float(nrm[-1]), "distance_ratio_final_over_initial": float(nrm[-1] / nrm[0]),
                            "linear_prediction_V_final": float(Vlin[-1]), "linear_vs_observed_V_relative_error_at_final": float(abs(Vlin[-1] - Vv[sel[-1]]) / Vv[sel[-1]]),
                            "linear_vs_observed_V_max_relative_error": float(np.max(np.abs(Vlin - Vv[sel]) / Vv[sel])), "observed_decay_tau_Qset_error_s": float(-1 / k[0]), "predicted_slow_mode_tau_s": float(slow["tau_s"]),
                            "max_abs_Qset_error_final_pu": float(np.abs(qref[-1]).max()), "frequency_dev_hz_min_max": [float(z["f_hz"].min()), float(z["f_hz"].max())], "unit_voltage_min_max_pu": [float(Vu.min()), float(Vu.max())],
                            "bus_voltage_min_max_pu": [float(z["Vbus"].min()), float(z["Vbus"].max())], "min_margin_P_pu": float(min((lim["pmax"] - P).min(), (P - lim["pmin"]).min())),
                            "min_margin_Q_pu": float(min((lim["qmax"] - Q).min(), (Q - lim["qmin"]).min())), "min_margin_S_pu": float(s_rel.min()), "max_reference_rate_pu_per_s": float(rate.max()), "final_reference_rate_pu_per_s": float(rate[-1]),
                            "dae_residual_g_inf_max": float(z["g_inf"].max())}
        np.savez_compressed(A / f"IEEE39_DEC051_H4_validation_{tag}_summary.npz", t=t, V=Vv, nrm=nrm, sel_t=t[sel], Vlin=Vlin, qref_max=np.abs(qref).max(axis=1))
    (A / "IEEE39_DEC051_H4_validation.json").write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
    print(json.dumps(out, indent=1, default=float)[:4500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
