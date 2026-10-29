"""DEC-057 / OC3 M3 validation (lot M3V, in-sample DESIGN cells) and the separate reporting categories of ops/sted/DEC057_protocol.md:
(a) predictive feasibility, (b) dynamic safety (rule M3V-1 per cell, rule M3V-2 for approval), (c) stability (pre-event spectrum at xi(z_M3) and the
frozen-time spectrum at the stored end state of every TDS), (d) optimality, (e) redispatch cost.
Writes IEEE39_DEC057_M3V_results.json and IEEE39_DEC057_M3V_{margins,traces}.png exclusively."""
from __future__ import annotations

import json

import numpy as np

import dec054_common as C54
import dec055_common as C
import dec055_oc as OCM
import dec057_static as S
import dec057_tds as T

ST56 = C54.RUNS_DIR.parent / "DEC056_state"


def lockin(t, y, a0, w=20.0, f0=1.25):
    k = (t >= a0) & (t < a0 + w)
    tt, yy = t[k], y[k]
    X = np.column_stack([np.ones_like(tt), tt - a0, (tt - a0) ** 2, np.cos(2 * np.pi * f0 * tt), np.sin(2 * np.pi * f0 * tt)])
    c = np.linalg.lstsq(X, yy, rcond=None)[0]
    return float(np.hypot(c[3], c[4]))


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plan = json.loads(T.plan_path("M3V").read_text(encoding="utf-8"))
    U = json.loads((C.ART / "IEEE39_DEC057_D8_convergence.json").read_text(encoding="utf-8"))["rule_D8_4"]["U_D8_pu"]
    seeded = json.loads((ST56 / "oc3_seeded_full.json").read_text(encoding="utf-8"))
    m0 = json.loads((C.STATE / "m0_OC3.json").read_text(encoding="utf-8"))
    z = np.array(plan["runs"][0]["z"])
    plant = OCM.make_plant("OC3")
    out = {"stage": "DEC-057 M3V results (in-sample DESIGN cells; not TUNE/TEST evidence)", "U_D8_pu": U, "cells": {}}
    ser = {}
    for r in plan["runs"]:
        p = T.RUNS / r["run_id"]
        st = json.loads((p / "status.json").read_text(encoding="utf-8"))
        rec = {"controller": r["controller"], "scenario": r["scenario"], "status": st["status"]}
        if not (p / "series.npz").exists():
            rec["class"] = "TDS_NUMERICAL_FAILURE"
            out["cells"][r["run_id"]] = rec
            continue
        zz = dict(np.load(p / "series.npz"))
        ser[r["run_id"]] = zz
        m = json.loads((p / "metrics.json").read_text(encoding="utf-8"))
        u = m["unit"]
        mp = np.array(u["Pmax"]["min_margin"])
        j = int(np.argmin(mp))
        qsv = {k: [C.UNITS[i] for i, v in enumerate(u[k]["violates"]) if v] for k in ("Qmax", "Qmin", "Smax", "Pmin")}
        t = zz["t"]
        post = t >= C.EVENT_T - 1e-9
        tj = float(t[post][np.argmin((np.array([10.4, 6.5, 6.82, 6.97, 8.65, 11.0, 7.5, 5.64, 5.5, 5.95])[None, :] - zz["P"][post])[:, j])] - C.EVENT_T)
        rec.update({"min_Pmax_margin": float(mp[j]), "unit": C.UNITS[j], "t_after_event_s": tj, "Q_S_Pmin_violations": qsv, "V_outside_buses_post": int(m["V_outside_buses_post"]),
                    "V_min_post": m["V_min_post"], "V_max_post": m["V_max_post"]})
        if st["status"] == "TDS_NUMERICAL_FAILURE":
            cls = "TDS_NUMERICAL_FAILURE"
        elif any(qsv[k] for k in ("Qmax", "Qmin", "Smax", "Pmin")) or m["V_outside_buses_post"] > 0:
            cls = "UNSAFE"
        elif rec["min_Pmax_margin"] >= U:
            cls = "SAFE"
        elif rec["min_Pmax_margin"] <= -U:
            cls = "UNSAFE"
        else:
            cls = "NUMERICALLY_INDETERMINATE"
        rec["class"] = cls
        fc = zz["f_coi_hz"]
        late = t >= 120.0
        V = zz["V"]
        k180 = t >= t[-1] - 20.0
        rec["late"] = {"f_coi_final_err_hz_120_200": float(np.abs(fc[late] - 60.0).max()), "V_drift_last20s_pu": float(np.abs(V[k180] - V[k180][0]).max()),
                       "P_1p25Hz_amp_last20s": max(lockin(t, zz["P"][:, i], t[-1] - 20.0) for i in range(10)), "P_1p25Hz_amp_5_25s": max(lockin(t, zz["P"][:, i], C.EVENT_T) for i in range(10))}
        # frozen-time spectrum at the stored end state
        try:
            pq = {n: zz[f"end_PQ_{n}"] for n in ("p0", "q0", "Ppf", "Qpf")}
            uu = np.concatenate([zz["end_pset"], zz["end_qset"]])
            system, ctx, stt = S.load_state(plant, z, zz["end_x"], zz["end_y"], zz["end_flags"], uu, pq=pq)
            b, vn, _ = S.closed_loop(plant, system, ctx, stt, uu)
            sp = S.spectrum(b["M"])
            ev = np.linalg.eigvals(b["M"])
            jm = S.mode_near(ev)
            _, gq = plant.e8.capability_factors(uu[:10], uu[10:], ctx["lim"])
            gp, _ = plant.e8.capability_factors(uu[:10], uu[10:], ctx["lim"])
            rec["end_state_frozen_spectrum"] = dict(sp, pair_0p8_1p8Hz=[float(ev[jm].real), float(ev[jm].imag)] if jm is not None else None, rates_inf=float(np.abs(vn).max()),
                                                    gP_raw=gp.tolist(), gQ_raw=gq.tolist())
        except Exception as ex:
            rec["end_state_frozen_spectrum"] = {"error": repr(ex)[:300]}
        out["cells"][r["run_id"]] = rec
        print(r["run_id"], cls, round(rec["min_Pmax_margin"], 5), rec["unit"], rec["late"], rec["end_state_frozen_spectrum"].get("rightmost_excluding_null", [None])[:1],
              rec["end_state_frozen_spectrum"].get("pair_0p8_1p8Hz"), flush=True)
    b2 = [v for k, v in out["cells"].items() if v["controller"] == "B2" and "flat" not in k]
    cl = [v["class"] for v in b2]
    approval = "M3_DYNAMIC_FEASIBILITY_REFUTED (in sample)" if "UNSAFE" in cl else ("DYNAMICALLY_VERIFIED_IN_SAMPLE" if all(c == "SAFE" for c in cl) else "NOT_VERIFIED")
    out["rule_M3V_2_B2"] = {"classes": dict(zip([k for k in out["cells"] if out["cells"][k]["controller"] == "B2" and "flat" not in k], cl)), "verdict": approval}
    out["B3_classes"] = {k: v["class"] for k, v in out["cells"].items() if v["controller"] == "B3" and "flat" not in k}
    pre = json.loads((S.STATE / "b3eq_OC3_M3S.json").read_text(encoding="utf-8"))["rules"]
    out["categories"] = {
        "a_predictive_feasibility": {"status": seeded["status"], "exact_min_margin_all_design_pu": seeded["exact_min_margin_all_design"], "tau_cut_pu": C54.PROPOSED["tau_cut_pu"],
                                     "exact_min_base": seeded["exact_min_base"], "seed_rule": "IEEE39_DEC057 static oc3_seedrule (reproduces the DEC-056 seed exactly)"},
        "b_dynamic_safety_in_sample": {"B2": approval, "U_D8_pu": U, "counts_B2": {c: cl.count(c) for c in set(cl)},
                                       "counts_B3": {c: list(out["B3_classes"].values()).count(c) for c in set(out["B3_classes"].values())}},
        "c_stability": {"pre_event_closed_loop_at_xi_zM3": {"hurwitz_mod_null": pre["R7_linear_stability"]["pass"], "rightmost": pre["R7_linear_stability"]["rightmost_excluding_null"][:2]},
                        "end_state_frozen_time": {k: v.get("end_state_frozen_spectrum", {}).get("rightmost_excluding_null", [None])[0] for k, v in out["cells"].items()},
                        "note": "frozen-time spectra at a non-equilibrium state: indicative only; no T-B claim"},
        "d_optimality": {"kkt_residual": seeded["kkt"], "kkt_tol_scaled": C54.PROPOSED["kkt_tol"] * (1 + seeded["J"]), "local_optimum": bool(seeded["kkt"] <= C54.PROPOSED["kkt_tol"] * (1 + seeded["J"]))},
        "e_redispatch_cost": {"J_M3": seeded["J"], "J_M0": m0.get("J"), "redispatch_MW_vs_M0": seeded["redispatch_MW_vs_M0"]}}
    with open(C.ART / "IEEE39_DEC057_M3V_results.json", "x", encoding="utf-8") as f:
        json.dump(out, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else float(o))
    # figures
    names = [r["run_id"].split("_", 2)[2] for r in plan["runs"] if r["controller"] == "B2" and "flat" not in r["run_id"]]
    fig, ax = plt.subplots(figsize=(11, 4.2))
    x = np.arange(len(names))
    for d, ctrl, c in ((-0.2, "B2", "tab:blue"), (0.2, "B3", "tab:orange")):
        vals = [out["cells"][f"D57M3V_{ctrl}_{n}"].get("min_Pmax_margin", np.nan) for n in names]
        ax.bar(x + d, vals, width=0.4, color=c, label=f"{ctrl}: min instantaneous Pmax margin (local dt/16)")
    ax.axhspan(-U, U, color="0.85", label=f"NUMERICALLY_INDETERMINATE band (U_D8 = {U:.4f} pu)")
    ax.axhline(0, c="k", lw=0.8)
    ax.set_xticks(x, names, rotation=45, fontsize=8)
    ax.set(ylabel="pu", title="OC3 M3 (DEC-056 seeded): in-sample DESIGN cells, 200 s TDS")
    ax.legend(fontsize=7)
    fig.tight_layout()
    with open(C.FIG / "IEEE39_DEC057_M3V_margins.png", "xb") as f:
        fig.savefig(f, dpi=140, format="png")
    plt.close(fig)
    worst = min((k for k in out["cells"] if "flat" not in k and "B2" in k and "min_Pmax_margin" in out["cells"][k]), key=lambda k: out["cells"][k]["min_Pmax_margin"])
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
    for k, ls in ((worst, "-"), (worst.replace("B2", "B3"), "--"), ("D57M3V_B2_flat", ":")):
        if k not in ser:
            continue
        zz = ser[k]
        ax[0].plot(zz["t"], zz["f_coi_hz"], ls=ls, lw=1, label=k)
        ax[1].plot(zz["t"], zz["V"].min(axis=1), ls=ls, lw=1, label=k)
        ax[2].plot(zz["t"], zz["P"][:, C.UNITS.index(out["cells"][worst]["unit"])], ls=ls, lw=1, label=k)
    for a, ttl in zip(ax, ("f_COI (Hz)", "min bus V (pu)", f"P {out['cells'][worst]['unit']} (pu)")):
        a.set(xlabel="t (s)", title=ttl)
        a.legend(fontsize=6)
    fig.tight_layout()
    with open(C.FIG / "IEEE39_DEC057_M3V_traces.png", "xb") as f:
        fig.savefig(f, dpi=140, format="png")
    plt.close(fig)
    print(json.dumps({"rule_M3V_2": out["rule_M3V_2_B2"], "B3": out["B3_classes"], "categories": out["categories"]}, indent=1, default=float))


def margins_fig_v2():
    """IEEE39_DEC057_M3V_margins_v2.png from the stored results (v1 drew the indeterminate band over the bars that lie inside it; v1 kept unmodified)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    d = json.loads((C.ART / "IEEE39_DEC057_M3V_results.json").read_text(encoding="utf-8"))
    U = d["U_D8_pu"]
    names = [k.split("_", 2)[2] for k in d["cells"] if k.startswith("D57M3V_B2_") and "flat" not in k]
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.axhspan(-U, U, color="0.88", zorder=0, label=f"NUMERICALLY_INDETERMINATE band (U_D8 = {U:.4f} pu)")
    for dx, ctrl, c in ((-0.2, "B2", "tab:blue"), (0.2, "B3", "tab:orange")):
        vals = [d["cells"][f"D57M3V_{ctrl}_{n}"]["min_Pmax_margin"] for n in names]
        ax.bar(x + dx, vals, width=0.4, color=c, zorder=2, label=f"{ctrl}: min instantaneous Pmax margin (local dt/16)")
        for xi, v, n in zip(x, vals, names):
            ax.text(xi + dx, v + (0.0012 if v >= 0 else -0.0028), d["cells"][f"D57M3V_{ctrl}_{n}"]["class"][:6], ha="center", fontsize=5, rotation=90 if v >= 0 else 0, zorder=3)
    ax.axhline(0, c="k", lw=0.8, zorder=1)
    ax.set_xticks(x, names, rotation=45, fontsize=8)
    ax.set(ylabel="pu", title="OC3 M3 (DEC-056 seeded): in-sample DESIGN cells, 200 s TDS")
    ax.legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    with open(C.FIG / "IEEE39_DEC057_M3V_margins_v2.png", "xb") as f:
        fig.savefig(f, dpi=140, format="png")
    plt.close(fig)


if __name__ == "__main__":
    import sys
    margins_fig_v2() if sys.argv[1:] == ["fig_v2"] else main()
