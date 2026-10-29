"""DEC-057 / OC3 instability (lot INS + reserves RES3, RES4; post-processing and the stored static analyses ins_snapshots*, ins_fdcheck).
Hypotheses H9a (limiter switch), H9b (smooth crossing of the frozen-time spectrum), H9c (numerical); H9e (ANDES reset_tiny dead zone) added before RES4.
Onset = first time AFTER the global minimum of the 1.25 Hz lock-in amplitude of unit P (4-s windows, cubic trend removed) at which it exceeds 1e-6 pu.
Writes IEEE39_DEC057_INS_results_v2.json and IEEE39_DEC057_INS_{onset,mechanism}_v2.png exclusively.  (v1 of these files used an onset definition
that caught the B2 activation transient at t = 7 s; v1 is superseded and kept unmodified.)  First discrete-flag change time reported per run."""
from __future__ import annotations

import json

import numpy as np

import dec055_common as C
import dec055_oc as OCM
import dec056_tds as T6
import dec057_static as S
import dec057_tds as T

RUNS = {"default_dt (D56T014)": T6.RUNS / "D56RES_presettle_OC3_M0_partial", "default_dt_snap (INS i)": T.RUNS / "D57INS_OC3_M0_B2_presettle_snap",
        "default_dt/2 (INS ii)": T.RUNS / "D57INS_OC3_M0_B2_presettle_dthalf", "honest_tol1e-8 (RES3)": T.RUNS / "D57RES_INS_OC3_honest_tol1e-8",
        "reset_tiny0 (RES4)": T.RUNS / "D57RES_INS_OC3_reset_tiny0"}


def amp_series(z, w=4.0, f0=1.25, step=1.0):
    t, P = z["t"], z["P"]
    a = np.arange(t[0] + 5.0, t[-1] - w, step)
    out = []
    for a0 in a:
        k = (t >= a0) & (t < a0 + w)
        tt = t[k]
        X = np.column_stack([np.ones_like(tt), tt - a0, (tt - a0) ** 2, (tt - a0) ** 3, np.cos(2 * np.pi * f0 * tt), np.sin(2 * np.pi * f0 * tt)])
        c = np.linalg.lstsq(X, P[k], rcond=None)[0]
        out.append(np.hypot(c[4], c[5]).max())
    return a + w / 2, np.array(out)


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    out = {"stage": "DEC-057 OC3 instability study (INS)", "runs": {}}
    A = {}
    for lab, p in RUNS.items():
        st = json.loads((p / "status.json").read_text(encoding="utf-8"))
        z = dict(np.load(p / "series.npz", allow_pickle=True))
        tc, a = amp_series(z)
        A[lab] = (tc, a, z)
        imin = int(np.argmin(a))
        k = np.where((a > 1e-6) & (np.arange(len(a)) > imin))[0]
        on = float(tc[k[0]]) if k.size else None
        rec = {"status": st["status"], "t_end": float(z["t"][-1]), "onset_amp_gt_1e-6_s": on, "min_amp": float(a.min()), "t_min_amp": float(tc[imin])}
        if on is not None:
            g = (a > 1e-8) & (a < 1e-3) & (tc <= on + 15) & (np.arange(len(a)) > imin)
            if g.sum() > 4:
                rec["growth_rate_1e-8_to_1e-3"] = float(np.polyfit(tc[g], np.log(a[g]), 1)[0])
        if "flaglog_t" in z:
            rec["discrete_flag_changes"] = int(len(z["flaglog_t"]))
            rec["first_flag_change_s"] = float(z["flaglog_t"].min()) if len(z["flaglog_t"]) else None
        out["runs"][lab] = rec
    ref = dict(np.load(RUNS["default_dt (D56T014)"] / "series.npz", allow_pickle=True))
    zs = A["default_dt_snap (INS i)"][2]
    n = len(zs["t"])
    out["regression_INS_i_vs_D56T014"] = {"t_equal": bool(np.array_equal(zs["t"], ref["t"][:n])), "P_equal": bool(np.array_equal(zs["P"], ref["P"][:n])), "V_equal": bool(np.array_equal(zs["V"], ref["V"][:n]))}
    snaps = []
    for name in ("ins_snapshots_res3", "ins_snapshots"):
        d = json.loads((S.STATE / f"{name}.json").read_text(encoding="utf-8"))
        snaps += [(r["t"], r["mode_1p25Hz"]["eig"][0], r["mode_1p25Hz"]["f_hz"], name) for r in d["snapshots"] if "mode_1p25Hz" in r]
    snaps.sort()
    ts = np.array([s[0] for s in snaps])
    re = np.array([s[1] for s in snaps])
    kc = np.where(np.diff(np.sign(re)) > 0)[0]
    out["frozen_time_pair"] = {"t": ts.tolist(), "Re": re.tolist(), "f_hz": [s[2] for s in snaps],
                               "crossing_s": float(ts[kc[0]] - re[kc[0]] * (ts[kc[0] + 1] - ts[kc[0]]) / (re[kc[0] + 1] - re[kc[0]])) if kc.size else None}
    # RES4 growth rate vs frozen-time Re
    tc, a, _ = A["reset_tiny0 (RES4)"]
    cmp = []
    for t0 in (95.0, 105.0, 115.0, 125.0):
        k = (tc >= t0 - 5) & (tc <= t0 + 5) & (a > 1e-11) & (a < 1e-1)
        if k.sum() > 4:
            cmp.append({"t": t0, "TDS_growth_rate": float(np.polyfit(tc[k], np.log(a[k]), 1)[0]), "frozen_Re": float(np.interp(t0, ts, re))})
    out["RES4_growth_vs_frozen_Re"] = cmp
    fd = json.loads((S.STATE / "ins_fdcheck.json").read_text(encoding="utf-8"))
    out["FD_Jacobian_check"] = {k: {"max_rel_diff": v["max_rel_diff"], "pair_M": v["pair_M"], "pair_FD": v["pair_FD"]} for k, v in fd.items() if isinstance(v, dict)}
    d = json.loads((S.STATE / "ins_snapshots.json").read_text(encoding="utf-8"))
    r0 = d["snapshots"][0]["mode_1p25Hz"]
    out["mode_at_200s"] = {"eig": r0["eig"], "participation_top": r0["participation_top"][:8], "sensitivity_+1pct": r0.get("sensitivity_+1pct"),
                           "discrete_vs_continuous": {k: v for k, v in r0.items() if k.startswith("discrete")}}
    # mechanism: SG30 capability factor gP along the trajectory (RES3 cmd log)
    z3 = A["reset_tiny0 (RES4)"][2]
    plant = OCM.make_plant("OC3")
    lim = plant.limits
    ct, ps, qs = z3["cmd_t"], z3["cmd_pset"], z3["cmd_qset"]
    sel = np.arange(0, len(ct), max(1, len(ct) // 400))
    gp = np.array([plant.e8.capability_factors(ps[i], qs[i], lim)[0] for i in sel])
    qn = zs["unit_qn"]                     # same dispatch and initialisation (the partial RES4 series has no unit_qn)
    out["mechanism"] = {"t": ct[sel].tolist(), "gP_raw_SG30": gp[:, 0].tolist(), "Qset_minus_Qn_SG30": (qs[sel, 0] - qn[0]).tolist(),
                        "gP_raw_SG30_t0": float(gp[0, 0]), "gP_raw_SG30_at_crossing": float(np.interp(out["frozen_time_pair"]["crossing_s"] or 0, ct[sel], gp[:, 0]))}
    hyp = {"H9a_limiter_switch": "NOT_SUPPORTED: no discrete-limiter flag changed before the onset in any run with the flag log (default runs: 0 changes; "
                                 "RES4: all changes within the last 6 ms before the numerical failure, i.e. a consequence of the divergence)",
           "H9b_smooth_crossing": f"SUPPORTED (frozen-time sense): the 1.25-1.37 Hz pair crosses Re = 0 continuously at about {out['frozen_time_pair']['crossing_s']:.1f} s; "
                                  "FD Jacobian agrees to 1.3e-7",
           "H9c_numerical_growth": "REJECTED as the cause of the instability (RES4 growth rate matches the frozen-time Re); the onset TIME of the default runs is numerical",
           "H9e_reset_tiny_dead_zone": "SUPPORTED: with reset_tiny = 0 the growth starts near the crossing and the TDS fails at "
                                       f"{out['runs']['reset_tiny0 (RES4)']['t_end']:.1f} s instead of 343.4 s",
           "Hopf": "NOT CLAIMED: the crossing occurs along a slowly drifting non-equilibrium trajectory (frozen-time analysis); no equilibrium, transversality or first Lyapunov coefficient"}
    out["hypotheses"] = hyp
    with open(C.ART / "IEEE39_DEC057_INS_results_v2.json", "x", encoding="utf-8") as f:
        json.dump(out, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else float(o))
    fig, ax = plt.subplots(figsize=(10, 4.6))
    for lab, (tc, a, _) in A.items():
        if lab.startswith("default_dt_snap"):
            continue
        ax.semilogy(tc, np.maximum(a, 1e-14), lw=1, label=f"{lab}: onset {out['runs'][lab]['onset_amp_gt_1e-6_s']}")
    ax.set(xlabel="t (s), B2 active from t = 0, OC3 M0, no event", ylabel="1.25 Hz amplitude of unit P (pu)", title="OC3 oscillatory instability: TDS solver settings")
    ax2 = ax.twinx()
    ax2.plot(ts, re, "k.--", lw=0.8, label="frozen-time Re of the 1.3 Hz pair (right axis)")
    ax2.axhline(0, c="k", lw=0.5)
    ax2.set_ylabel("Re (1/s)")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=7, loc="upper left")
    fig.tight_layout()
    with open(C.FIG / "IEEE39_DEC057_INS_onset_v2.png", "xb") as f:
        fig.savefig(f, dpi=140, format="png")
    plt.close(fig)
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.2))
    ax[0].plot(out["mechanism"]["t"], out["mechanism"]["gP_raw_SG30"], label="g_P,raw SG30 (capability factor)")
    ax[0].plot(out["mechanism"]["t"], out["mechanism"]["Qset_minus_Qn_SG30"], label="Qset - Qn SG30 (pu)")
    ax[0].set(xlabel="t (s)", title="B2 frequency gain of SG30 is k_ip g_P/g_ref: g_P grows as Qset SG30 falls")
    ax[0].legend(fontsize=7)
    ax[1].plot(ts, re, "o-", ms=3)
    ax[1].axhline(0, c="k", lw=0.6)
    ax[1].set(xlabel="t (s)", ylabel="Re (1/s)", title="frozen-time 1.3 Hz pair (SG30 rotor + Pset SG30)")
    fig.tight_layout()
    with open(C.FIG / "IEEE39_DEC057_INS_mechanism_v2.png", "xb") as f:
        fig.savefig(f, dpi=140, format="png")
    plt.close(fig)
    print(json.dumps({k: out[k] for k in ("runs", "regression_INS_i_vs_D56T014", "RES4_growth_vs_frozen_Re", "hypotheses")}, indent=1, default=float),
          out["frozen_time_pair"]["crossing_s"], out["mechanism"]["gP_raw_SG30_t0"], out["mechanism"]["gP_raw_SG30_at_crossing"])


if __name__ == "__main__":
    main()
