"""DEC-057 / D7 analysis: centered RDC B3 (post-processing of lot D7 and of the static R1-R7 checks).  Decision rule D7 of ops/sted/DEC057_protocol.md.
G1 flat and AC-04 metrics are computed exactly as dec055_l1.analyze (frozen criteria); B2 (DEC-055 L1 runs) is the comparative reference.
Writes IEEE39_DEC057_D7_results.json and IEEE39_DEC057_D7_{flat,growth,event}.png exclusively."""
from __future__ import annotations

import json

import numpy as np

import dec054_common as C54
import dec055_common as C
import dec057_tds as T

R55 = C54.RUNS_DIR.parent / "DEC055_runs"
ST57 = C54.RUNS_DIR.parent / "DEC057_state"
SG31 = 1
PMAX = np.array([10.4, 6.5, 6.82, 6.97, 8.65, 11.0, 7.5, 5.64, 5.5, 5.95])


def load(p):
    return dict(np.load(p / "series.npz"))


def g1_flat(z, status, final_residual):
    t = z["t"]
    w = (t >= 0.0) & (t <= 20.0)
    fc, fm, V = z["f_coi_hz"], C.mean_busfreq_hz(z["f_bus_hz"]), z["V"]
    met = {"f_coi_drift_20s_hz": float(np.abs(fc[w] - fc[0]).max()), "mean_busfreq_drift_20s_hz": float(np.abs(fm[w] - fm[0]).max()), "v_drift_20s_pu": float(np.abs(V[w] - V[0]).max()),
           "f_coi_drift_200s_hz": float(np.abs(fc - fc[0]).max()), "v_drift_200s_pu": float(np.abs(V - V[0]).max()), "V_min": float(V.min()), "V_max": float(V.max())}
    step = max(1, int(round(1.0 / (t[1] - t[0]))))
    Vs = V[::step]
    met["rolling_drift20_max_pu"] = float(max(np.abs(Vs[k:k + 21] - Vs[k]).max() for k in range(len(Vs) - 20)))
    ok = (met["f_coi_drift_20s_hz"] <= C.THR["flat_drift_hz"] and met["mean_busfreq_drift_20s_hz"] <= C.THR["flat_drift_hz"] and met["v_drift_20s_pu"] <= C.THR["flat_drift_pu"]
          and met["V_min"] >= C54.VLO and met["V_max"] <= C54.VHI and status == "TDS_SAFE_OBSERVED" and (final_residual or 0) <= 1e-6)
    return met, ("PASS" if ok else "FAIL")


def ac04(z, ref):
    t, tr = z["t"], ref["t"]
    wr = tr <= 20.0
    idx = np.searchsorted(t, tr[wr] - 1e-12)
    ok_grid = bool(np.allclose(t[idx], tr[wr], atol=1e-9))
    dP = np.abs(z["P"][idx] - ref["P"][wr])
    dV = float(np.abs(z["V"][idx] - ref["V"][wr]).max())
    fh, fr = C.mean_busfreq_hz(z["f_bus_hz"][idx]), C.mean_busfreq_hz(ref["f_bus_hz"][wr])
    nad = float(abs((60 - fh.min()) - (60 - fr.min())) / max(60 - fr.min(), 1e-12))
    late = tr[wr] > C.EVENT_T + 0.05
    met = {"grid_aligned": ok_grid, "P_max_abs_diff_20s": float(dP.max()), "P_max_abs_diff_excluding_first_50ms": float(dP[late].max()), "V_max_abs_diff_20s": dV, "mean_busfreq_nadir_rel_diff": nad}
    return met, ("PASS" if ok_grid and met["P_max_abs_diff_20s"] <= 0.005 and dV <= 0.005 and nad <= 0.01 else "FAIL")


def event_metrics(z):
    t, P, V = z["t"], z["P"], z["V"]
    post = t >= C.EVENT_T - 1e-9
    mg = PMAX[None, :] - P[post]
    a, j = np.unravel_index(np.argmin(mg), mg.shape)
    fc = z["f_coi_hz"]
    late = t >= 120.0
    return {"min_Pmax_margin": float(mg[a, j]), "unit": C.UNITS[j], "t_after_event_s": float(t[post][a] - C.EVENT_T), "f_coi_nadir_hz": float(fc[post].min()),
            "V_min_post": float(V[post].min()), "V_max_post": float(V[post].max()), "f_coi_final_err_hz_120_200": float(np.abs(fc[late] - 60.0).max()) if late.any() else None,
            "unit_V_final": None, "Q_final": z["Q"][-1].tolist(), "V_bus_final_minus_pre": float(np.abs(V[-1] - V[np.searchsorted(t, C.EVENT_T - 1e-9) - 1]).max())}


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    out = {"stage": "DEC-057 D7 (centered RDC B3) results", "protocol_sha256": C54.sha_file(C.ROOT / "ops/sted/DEC057_protocol.md")}
    # static R1-R7
    out["static_R1_R7"] = {}
    for f in sorted(ST57.glob("b3eq_*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        R = d["rules"]
        out["static_R1_R7"][f"{d['oc']}_{d['dispatch']}"] = {"R1_R6": R["equilibrium_R1_R6"], "R7": R["R7_linear_stability"]["pass"], "rightmost": R["R7_linear_stability"]["rightmost_excluding_null"][:2],
                                                            "dominant": R["rightmost_mode_participation"]["top"][:3], "gQ_raw_min": R["R4_capability_interior"]["gQ_raw_min"],
                                                            "gP_raw_min": R["R4_capability_interior"]["gP_raw_min"], "B2_rate_at_xi": R["R2_B3_rates"]["B2_rates_max_abs_for_comparison"]}
    # flat runs: B3 (DEC-057) and B2 (DEC-055 L1)
    flat, ser = {}, {}
    for oc in ("OC1", "OC2", "OC3"):
        for ctrl, p in (("B3", T.RUNS / f"D57D7_B3_flat_{oc}_M0"), ("B2", R55 / f"D55L1_flat_{oc}_M0")):
            st = json.loads((p / "status.json").read_text(encoding="utf-8"))
            dg = json.loads((p / "diag.json").read_text(encoding="utf-8"))
            z = load(p)
            ser[(oc, ctrl)] = z
            met, v = g1_flat(z, st["status"], dg.get("final_residual"))
            flat[f"{oc}_{ctrl}"] = dict(met, G1_flat_verdict=v, status=st["status"])
    out["flat_G1"] = flat
    # 2000-s B3 OC3 run: growth of the deviation from xi(z)
    p = T.RUNS / "D57D7_B3_flat_OC3_M0_2000s"
    st = json.loads((p / "status.json").read_text(encoding="utf-8"))
    g = {"status": st["status"], "error_tail": (st.get("error") or "")[-300:]}
    if (p / "series.npz").exists():
        z = load(p)
        t, V, Q = z["t"], z["V"], z["Q"]
        dev = np.abs(V - V[0]).max(axis=1)
        dq = np.abs(Q - Q[0]).max(axis=1)
        g.update({"t_end": float(t[-1]), "max_dV_bus": float(dev.max()), "max_dQ_unit": float(dq.max())})
        for th in (1e-9, 1e-6, 1e-3, 1e-2):
            k = np.where(dev > th)[0]
            g[f"t_first_dV_gt_{th:g}"] = float(t[k[0]]) if k.size else None
        k = (dev > 1e-10) & (dev < 1e-4)
        if k.sum() > 10:
            c = np.polyfit(t[k], np.log(dev[k]), 1)
            g["fitted_growth_rate_1_per_s"] = float(c[0])
            g["fit_window_s"] = [float(t[k][0]), float(t[k][-1])]
        g["prediction_R7_rate"] = out["static_R1_R7"]["OC3_M0"]["rightmost"][0][0]
        g["prediction_confirmed_dV_gt_1e-3_before_2000s"] = g.get("t_first_dV_gt_0.001") is not None
        cq = z.get("cmd_qset")
        if cq is not None and len(cq):
            g["Qset_SG30_minus_Qn_final"] = float(cq[-1][0] - z["unit_qn"][0])
        ser["growth"] = z
    out["B3_OC3_2000s"] = g
    # reference event: B3 vs B2 (stored DEC-054 run) and AC-04 (B3 dt vs dt/2)
    zb3, zb3h = load(T.RUNS / "D57D7_B3_P3B2_b7P_M3_dt"), load(T.RUNS / "D57D7_B3_P3B2_b7P_M3_dthalf")
    zb2, zb2h = load(R55 / "D55L1_regress_P3B2_b7P_M3"), load(R55 / "D55L1_dthalf_P3B2_b7P_M3")
    out["event"] = {"B3_dt": event_metrics(zb3), "B2_dt": event_metrics(zb2), "B3_dthalf": event_metrics(zb3h), "B2_dthalf": event_metrics(zb2h)}
    out["AC04"] = {"B3": dict(zip(("metrics", "verdict"), ac04(zb3h, zb3))), "B2_DEC055": dict(zip(("metrics", "verdict"), ac04(zb2h, zb2)))}
    # decision rule D7 per OC (M0 dispatch, the G1 definition)
    dec = {}
    for oc in ("OC1", "OC2", "OC3"):
        s = out["static_R1_R7"][f"{oc}_M0"]
        dec[oc] = {"R1_R6": s["R1_R6"], "R7": s["R7"], "flat_G1_B3": flat[f"{oc}_B3"]["G1_flat_verdict"],
                   "D7": "RESOLVED" if (s["R1_R6"] and s["R7"] and flat[f"{oc}_B3"]["G1_flat_verdict"] == "PASS") else "NOT_RESOLVED"}
    out["D7_decision_by_OC"] = dec
    with open(C.ART / "IEEE39_DEC057_D7_results.json", "x", encoding="utf-8") as f:
        json.dump(out, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else float(o))
    # figures
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.2), sharey=True)
    for a, oc in zip(ax, ("OC1", "OC2", "OC3")):
        for ctrl, c in (("B2", "tab:gray"), ("B3", "tab:blue")):
            z = ser[(oc, ctrl)]
            a.semilogy(z["t"], np.maximum(np.abs(z["V"] - z["V"][0]).max(axis=1), 1e-16), c=c, lw=1, label=f"{ctrl}: max_b |V_b(t) - V_b(0)|")
        a.axhline(C.THR["flat_drift_pu"], c="k", ls=":", lw=0.9, label="G1 1e-3 pu (frozen)")
        a.set(title=f"{oc} M0 flat run (RDC on at 5 s)", xlabel="t (s)")
        a.legend(fontsize=7)
    ax[0].set_ylabel("bus-voltage deviation from t = 0 (pu)")
    fig.tight_layout()
    with open(C.FIG / "IEEE39_DEC057_D7_flat.png", "xb") as f:
        fig.savefig(f, dpi=140, format="png")
    plt.close(fig)
    if "growth" in ser:
        z = ser["growth"]
        fig, ax = plt.subplots(figsize=(8, 4.2))
        dev = np.maximum(np.abs(z["V"] - z["V"][0]).max(axis=1), 1e-17)
        ax.semilogy(z["t"], dev, lw=1, label="B3, OC3 M0: max_b |V_b(t) - V_b(0)| (TDS)")
        if g.get("fitted_growth_rate_1_per_s") is not None:
            t0 = g["fit_window_s"][0]
            k = np.searchsorted(z["t"], t0)
            tt = np.linspace(t0, z["t"][-1], 50)
            ax.semilogy(tt, dev[k] * np.exp(g["prediction_R7_rate"] * (tt - t0)), "k--", lw=0.9, label=f"exp({g['prediction_R7_rate']:.4f} t) (static R7 eigenvalue)")
        ax.axhline(1e-3, c="tab:red", ls=":", lw=0.9, label="1e-3 pu")
        ax.set(xlabel="t (s)", ylabel="pu", title="OC3: departure of B3 from its (linearly unstable) equilibrium")
        ax.legend(fontsize=7)
        fig.tight_layout()
        with open(C.FIG / "IEEE39_DEC057_D7_growth.png", "xb") as f:
            fig.savefig(f, dpi=140, format="png")
        plt.close(fig)
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
    for z, lab, ls in ((zb2, "B2", "-"), (zb3, "B3", "--")):
        ax[0].plot(z["t"] - C.EVENT_T, z["f_coi_hz"], ls=ls, lw=1, label=lab)
        ax[1].plot(z["t"] - C.EVENT_T, z["V"][:, 6], ls=ls, lw=1, label=lab)
        ax[2].plot(z["t"] - C.EVENT_T, z["Q"][:, SG31], ls=ls, lw=1, label=lab)
    for a, ttl in zip(ax, ("f_COI (Hz)", "|V| bus 7 (pu)", "Q SG31 (pu)")):
        a.set(xlabel="time after event (s)", title=f"{ttl}, P3B2_b7P_M3 (OC1)")
        a.legend(fontsize=7)
    fig.tight_layout()
    with open(C.FIG / "IEEE39_DEC057_D7_event.png", "xb") as f:
        fig.savefig(f, dpi=140, format="png")
    plt.close(fig)
    print(json.dumps({"D7": dec, "flat": {k: {a: v[a] for a in ("v_drift_20s_pu", "rolling_drift20_max_pu", "f_coi_drift_200s_hz", "G1_flat_verdict")} for k, v in flat.items()},
                      "growth": g, "event": out["event"], "AC04": out["AC04"]}, indent=1, default=float))


if __name__ == "__main__":
    main()
