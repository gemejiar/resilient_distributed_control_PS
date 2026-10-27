"""DEC-050 block A analysis (post-processing of the single 2000 s run; no simulation).

1. Existence / location of the closed-loop equilibrium.  At each stored time t_k the closed loop (ANDES plant + original RDC) is linearised: z' = M dz + f0 with f0 = [xdot; v0] the actual
   drift (plant derivative and RDC rates).  The Newton step dz = -M^+ f0 (minimum-norm, the common rotor-angle mode is the only null direction) estimates the point where the nonlinear drift
   vanishes.  Its quality is judged against the SAME trajectory: predictions made at 199, 500 and 1000 s are compared with the state reached later and with each other.
2. Contrast with E10/E13: slowest modal time constants versus the observed decay of the distance to the final state; E10 tail tolerances evaluated at 2000 s.
3. Which term holds the equilibrium away from V = 1: per-unit decomposition of the Q-channel rate v_Q = K_IQ K_V g_Q (V_ref - V) - K_IQ K_Q l_Q - K_LEAK (Qset - Qn) at 199 s and 1999 s, and
   the SG clamp / capability-factor status.
4. Verified-equilibrium criterion (declared before looking): at t = 1999 s  max|v0| < 5e-5 pu/s (E10 setpoint tolerance 1e-3 pu / 20 s),  predicted remaining displacement of the
   references < 2e-3 pu and of the unit voltages < 2e-3 pu.  Only if it holds, the modal/Lyapunov analysis of M(1999 s) is reported as local analysis around a verified equilibrium.
"""

from __future__ import annotations

import json
import os

os.environ["C2_VARIANT"] = "C2t"

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import run_e8_ieee39 as e8  # noqa: E402
from run_e13_stability import modal  # noqa: E402
from run_e0_ieee39 import ARTIFACTS_DIR as A, FIGURES_DIR, git_commit, sha256  # noqa: E402

NAMES = ["SG30", "SG31", "SG33", "SG35", "SG38", "SG39", "GFM32", "GFM37", "GFM34", "GFM36"]
TIMES = (199, 500, 1000, 1999)
TOL_V0, TOL_U, TOL_V = 5e-5, 2e-3, 2e-3


def newton(pr, k):
    M, xdot, v0, Cz, y0, u0 = (pr[f"t{k}_{n}"] for n in ("M", "xdot", "v0", "Cz", "y0", "u0"))
    f0 = np.concatenate([xdot, v0])
    sv = np.linalg.svd(M, compute_uv=False)
    dz, *_ = np.linalg.lstsq(M, -f0, rcond=1e-10)
    ev = np.linalg.eigvals(M)
    stab = ev[ev.real < -1e-6]
    return {"dz": dz, "du": dz[-20:], "dY": Cz @ dz, "u0": u0, "y0": y0, "u_eq": u0 + dz[-20:], "Y_eq": y0 + Cz @ dz, "singular_values_min": sv[-3:].tolist(),
            "rank_deficit": int((sv < 1e-10 * sv[0]).sum()), "spectral_abscissa_stable": float(stab.real.max()), "n_unstable": int((ev.real > 1e-6).sum()), "n_marginal": int((np.abs(ev.real) <= 1e-6).sum()),
            "tau_slowest_s": float(-1 / stab.real.max()), "v0_inf": float(np.abs(v0).max()), "xdot_inf": float(np.abs(xdot).max()), "f0_consistency": float(np.linalg.norm(M @ dz + f0) / max(np.linalg.norm(f0), 1e-30))}


def main() -> int:
    d = np.load(A / "IEEE39_DEC050_A_longrun_Qplus_series.npz")
    pr = np.load(A / "IEEE39_DEC050_A_longrun_Qplus_probes.npz")
    t, tc = d["time_s"], d["cmd_t"]
    qs, ps = d["cmd_qset"], d["cmd_pset"]
    qn, pn = d["unit_qn"], d["unit_pn"]
    ub = list(d["bus_ids"])
    uv = d["bus_voltage_pu"][:, [ub.index(b) for b in d["unit_bus_ids"]]]
    f = d["bus_frequency_hz"].mean(axis=1)
    # replication of the first 200 s with the historical series of the same run (E9-B0 file)
    h = np.load(A / "IEEE39_E9B0_Vsafe_R35_040_series.npz")
    hq, ht = h["Q+__cmd_qset"], h["Q+__cmd_t"]
    i_h = np.searchsorted(ht, 199.0)
    i_n = np.searchsorted(tc, 199.0)
    rep = float(np.abs(hq[i_h] - qs[i_n]).max())
    nw = {k: newton(pr, k) for k in TIMES}
    u_last = nw[1999]["u_eq"]
    out: dict = {"stage": "DEC-050 A", "git_commit": git_commit(), "doc": __doc__, "series_sha256": sha256(A / "IEEE39_DEC050_A_longrun_Qplus_series.npz"), "probes_sha256": sha256(A / "IEEE39_DEC050_A_longrun_Qplus_probes.npz"),
                 "replication_first_200s_max_abs_qset_difference_pu": rep, "dynamic_simulations_used": "2 (8 s smoke test + this 2000 s run)", "newton": {}}
    for k in TIMES:
        n = nw[k]
        j = np.searchsorted(tc, float(k))
        later = {f"t{m}": float(np.abs(n["u_eq"] - qsp(qs, ps, tc, m)).max()) for m in TIMES if m > k}
        out["newton"][f"t{k}"] = {"v0_inf_pu_per_s": n["v0_inf"], "xdot_inf": n["xdot_inf"], "remaining_ref_displacement_inf_pu": float(np.abs(n["du"]).max()), "remaining_Qset_inf_pu": float(np.abs(n["du"][10:]).max()),
                                  "remaining_Pset_inf_pu": float(np.abs(n["du"][:10]).max()), "remaining_unit_V_inf_pu": float(np.abs(vunit(n["dY"], d)).max()),
                                  "predicted_vs_later_state_ref_inf_pu": later, "predicted_minus_last_prediction_ref_inf_pu": float(np.abs(n["u_eq"] - u_last).max()), "tau_slowest_s": n["tau_slowest_s"], "n_unstable": n["n_unstable"],
                                  "n_marginal": n["n_marginal"], "rank_deficit": n["rank_deficit"], "newton_consistency_residual": n["f0_consistency"]}
    # E10 tail metrics at the end
    w = tc >= tc[-1] - 100
    wt = t >= t[-1] - 100
    slope = lambda x, tt: float(np.polyfit(tt, x, 1)[0])
    out["tail_last_100s"] = {"qset_slope_max_abs_pu_per_s": float(max(abs(slope(qs[w][:, i], tc[w])) for i in range(10))), "pset_slope_max_abs_pu_per_s": float(max(abs(slope(ps[w][:, i], tc[w])) for i in range(10))),
                             "unit_voltage_slope_max_abs_pu_per_s": float(max(abs(slope(uv[wt][:, i], t[wt])) for i in range(10))), "frequency_error_hz": float(f[wt].mean() - 60.0),
                             "unit_voltage_mean_abs_error_to_1pu": float(np.abs(uv[-1] - 1.0).mean()), "unit_voltage_max_abs_error_to_1pu": float(np.abs(uv[-1] - 1.0).max()),
                             "qset_minus_qn_final_pu": (qs[-1] - qn).tolist(), "unit_voltage_final_pu": uv[-1].tolist(), "bus_voltage_final_min_max_pu": [float(d["bus_voltage_pu"][-1].min()), float(d["bus_voltage_pu"][-1].max())]}
    crit = {"max_abs_v0_lt_5e-5": nw[1999]["v0_inf"] < TOL_V0, "remaining_ref_lt_2e-3": bool(np.abs(nw[1999]["du"]).max() < TOL_U), "remaining_unit_V_lt_2e-3": bool(np.abs(vunit(nw[1999]["dY"], d)).max() < TOL_V)}
    out["verified_equilibrium_criterion"] = {**crit, "verified": all(crit.values())}
    # predicted equilibrium table (from the last probe) and evolution of the distance to it
    eqv = vunit(nw[1999]["Y_eq"], d)
    out["equilibrium_estimate"] = {"source_probe_s": 1999, "Qset_minus_Qn_pu": (u_last[10:] - qn).tolist(), "Pset_minus_Pn_pu": (u_last[:10] - pn).tolist(), "unit_voltage_pu": eqv.tolist(), "units": NAMES}
    dist = np.abs(qs - u_last[10:][None, :]).max(axis=1)
    sel = (tc > 205) & (tc < 1500) & (dist > 0)
    tau_fit = float(-1 / np.polyfit(tc[sel], np.log(dist[sel]), 1)[0])
    out["observed_decay_tau_s_of_distance_Qset_to_final"] = tau_fit
    out["distance_Qset_to_estimated_equilibrium_pu"] = {f"t={int(tt)}": float(dist[np.searchsorted(tc, tt)]) for tt in (10, 50, 100, 199, 500, 1000, 1500, 1990)}
    # decomposition of the Q channel
    gq = d["cmd_gq"]; vq = d["cmd_vrdc_q"]
    dec = {}
    for tag, tt in (("t199", 199.0), ("t1999", 1990.0)):
        i = np.searchsorted(tc, tt); j = np.searchsorted(t, tt)
        vt = e8.K_IQ * e8.K_V * gq[i] * (e8.V_REF - uv[j])
        leak = e8.K_LEAK * (qs[i] - qn)
        cons = vt - leak - vq[i]
        dec[tag] = {"voltage_term": vt.tolist(), "consensus_term": cons.tolist(), "leak_term": leak.tolist(), "v_rdc_q": vq[i].tolist(), "g_Q": gq[i].tolist(), "unit_voltage": uv[j].tolist(),
                    "z_clamp_active_SG": (np.abs(d["cmd_z"][i]) >= e8.Z_CLAMP - 1e-9).tolist()}
    out["Q_channel_decomposition"] = dec
    ev1999 = nw[1999]
    if out["verified_equilibrium_criterion"]["verified"]:
        out["modal_at_verified_equilibrium"] = {"closed_loop_with_RDC": modal(pr["t1999_M"]), "plant_frozen_references": modal(pr["t1999_A_plant"])}
    out["integrity"] = {"tds_ok": True, "note": "see diag in scratch log: tds_ok True, final_residual 1.3e-8, t_end 1999.99 s"}
    (A / "IEEE39_DEC050_A_summary.json").write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
    # figure
    fig, ax = plt.subplots(2, 3, figsize=(19, 10))
    for i in range(10):
        ax[0, 0].plot(tc, qs[:, i] - qn[i], lw=.9, label=NAMES[i]); ax[0, 0].plot(tc[-1] * 1.03, u_last[10 + i] - qn[i], "k.", ms=4)
        ax[0, 1].plot(t, uv[:, i], lw=.9)
    ax[0, 0].set_title("Qset - Qn [pu] (black dots: Newton estimate from t = 1999 s)"); ax[0, 0].legend(fontsize=6, ncol=2); ax[0, 1].axhline(1.0, color="k", ls=":"); ax[0, 1].set_title("unit-bus voltages [pu]")
    ax[0, 2].plot(t, (f - 60.0) * 1e3); ax[0, 2].set_title("mean frequency deviation [mHz]")
    ax[1, 0].semilogy(tc[dist > 0], dist[dist > 0]); ax[1, 0].set_title(f"max |Qset - Qset_eq| [pu]; fitted tau = {tau_fit:.0f} s (modal slowest {nw[1999]['tau_slowest_s']:.0f} s)")
    vv0 = [nw[k]["v0_inf"] for k in TIMES]
    ax[1, 1].semilogy(TIMES, vv0, "o-", label="max |v0| RDC rates"); ax[1, 1].semilogy(TIMES, [np.abs(nw[k]["du"]).max() for k in TIMES], "s-", label="Newton remaining ref displacement")
    ax[1, 1].axhline(TOL_V0, color="r", ls=":", lw=.8); ax[1, 1].axhline(TOL_U, color="r", ls="--", lw=.8); ax[1, 1].legend(fontsize=7); ax[1, 1].set_title("drift and remaining displacement vs probe time")
    x = np.arange(10)
    ax[1, 2].bar(x - 0.27, dec["t1999"]["voltage_term"], 0.27, label="voltage term"); ax[1, 2].bar(x, dec["t1999"]["consensus_term"], 0.27, label="consensus term"); ax[1, 2].bar(x + 0.27, dec["t1999"]["leak_term"], 0.27, label="leak term")
    ax[1, 2].set_xticks(x); ax[1, 2].set_xticklabels(NAMES, rotation=60, fontsize=7); ax[1, 2].legend(fontsize=7); ax[1, 2].set_title("Q-channel terms at 1990 s [pu/s] (sum with sign = v_Q)")
    for a in ax.ravel():
        a.grid(alpha=.25)
    fig.suptitle("DEC-050 A: 2000 s B2 run on C2t_Vsafe_R35_040 (Q+), closed-loop equilibrium estimate and residual drift"); fig.tight_layout()
    fig.savefig(FIGURES_DIR / "IEEE39_DEC050_A_longrun.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    print(json.dumps({k: out[k] for k in ("replication_first_200s_max_abs_qset_difference_pu", "verified_equilibrium_criterion", "observed_decay_tau_s_of_distance_Qset_to_final", "tail_last_100s", "distance_Qset_to_estimated_equilibrium_pu")}, indent=1, default=float)[:3500])
    print({k: {kk: v for kk, v in out["newton"][k].items() if kk != "predicted_vs_later_state_ref_inf_pu"} | {"later": out["newton"][k]["predicted_vs_later_state_ref_inf_pu"]} for k in out["newton"]})
    return 0


def qsp(qs, ps, tc, m):
    i = np.searchsorted(tc, float(m))
    return np.concatenate([ps[i], qs[i]])


def vunit(Y, d):
    """Voltages at the ten unit buses from a 59-vector of outputs (20 unit P/Q + 39 bus voltages)."""
    ub = list(d["bus_ids"])
    return np.asarray(Y)[20:][[ub.index(b) for b in d["unit_bus_ids"]]]


if __name__ == "__main__":
    raise SystemExit(main())
