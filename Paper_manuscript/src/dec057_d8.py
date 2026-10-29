"""DEC-057 / D8 analysis: local refinement up to dt/16 on [t_e - dt, t_e + 0.5 s] (lot D8) for the three critical DEC-054 M3 cases (post-processing; the algebraic
jumps are static solves).  Rules D8-1 .. D8-4 of ops/sted/DEC057_protocol.md; convergence rule = dec056_d8.order_and_limit (unchanged).
The instantaneous Pmax margin is the classified quantity; the one-cycle mean is complementary (defined here explicitly: trailing mean of P over
[t - 4 dt, t] by trapezoidal quadrature on the stored grid, evaluated at stored samples t >= t_e + 4 dt).
Writes IEEE39_DEC057_D8_convergence.json and IEEE39_DEC057_D8_{peaks,convergence}.png exclusively."""
from __future__ import annotations

import json

import numpy as np

import dec054_common as C54
import dec055_common as C55
import dec056_d8 as D6
import dec056_tds as T6
import dec057_tds as T

TE = C55.EVENT_T
PMAX = D6.PMAX
CASES = {"b7": "P3B2_b7P_M3", "b8": "P3B2_b8P_M3", "bus12": "P3-C_bus12P_M3"}
R55 = D6.R55


def seq(tag):
    """{method: {k: run dir}}; the reference case uses the uniform DEC-056/DEC-055 runs (the local k = 16 runs are the rule D8-1 check)."""
    if tag == "b7":
        return D6.runs()
    return {m: {k: T.RUNS / f"D57D8_{tag}_{m}_loc{k}" for k in (1, 2, 4, 8, 16)} for m in ("trapezoid", "backeuler")}


def jump(case):
    import dec054_opf as OPF
    import dec055_oc as OCM
    r = T._ref(case)
    OCM.PFLOW_TOL = 1e-6
    plant = OCM.make_plant("OC1")
    sc = r["scenario"]
    j = plant.jump(np.asarray(r["z"], float), OPF.Scenario(case, sc["bus"], sc["kind"], sc["amp"]))
    assert j["ok"], j
    return np.asarray(j["P_plus"], float), float(j["residual"])


def cycle_mean_margin(z):
    t, P = z["t"], z["P"]
    w = 4 * C54.DT
    k0 = int(np.searchsorted(t, TE - 1e-9))
    best = (np.inf, None, None)
    cum = np.concatenate([np.zeros((1, P.shape[1])), np.cumsum(0.5 * (P[1:] + P[:-1]) * np.diff(t)[:, None], axis=0)])
    for i in range(k0, len(t)):
        if t[i] < TE + w - 1e-12:
            continue
        ta = t[i] - w
        j = int(np.searchsorted(t, ta - 1e-12))
        # integral over [ta, t_i]: cumulative from t_j to t_i plus the partial interval [ta, t_j] (linear interpolation)
        Pa = P[j - 1] + (P[j] - P[j - 1]) * (ta - t[j - 1]) / (t[j] - t[j - 1]) if t[j] > ta else P[j]
        I = cum[i] - cum[j] + 0.5 * (Pa + P[j]) * (t[j] - ta)
        m = PMAX - I / w
        a = int(np.argmin(m))
        if m[a] < best[0]:
            best = (float(m[a]), C55.UNITS[a], float(t[i] - TE))
    return {"min_margin": best[0], "unit": best[1], "t_after_event_s": best[2]}


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    out = {"stage": "DEC-057 D8 local-refinement analysis", "protocol_sha256": C54.sha_file(C55.ROOT / "ops/sted/DEC057_protocol.md"), "cases": {}}
    Z = {}
    for tag, case in CASES.items():
        Pp, jres = jump(case)
        R = seq(tag)
        Q, st = {}, {}
        for meth, dd in R.items():
            for k, p in dd.items():
                st[f"{meth}_k{k}"] = json.loads((p / "status.json").read_text(encoding="utf-8"))["status"]
                if (p / "series.npz").exists():
                    Z[(tag, meth, k)] = D6.load(p)
                    q = D6.quantities(Z[(tag, meth, k)], Pp)
                    q.update({f"cycle_mean_{a}": b for a, b in cycle_mean_margin(Z[(tag, meth, k)]).items()})
                    Q[(meth, k)] = q
        keys = [k for k in Q[("backeuler", 1)] if isinstance(Q[("backeuler", 1)][k], float)]
        conv = {}
        for key in keys:
            conv[key] = {}
            for meth in ("trapezoid", "backeuler"):
                vals = {k: Q[(meth, k)][key] for k in sorted(R[meth]) if (meth, k) in Q}
                conv[key][meth] = dict(D6.order_and_limit(vals), values={str(k): v for k, v in vals.items()})
            a, b = conv[key]["trapezoid"], conv[key]["backeuler"]
            agree = a.get("verdict") == "CONVERGED" and b.get("verdict") == "CONVERGED" and abs(a["limit"] - b["limit"]) <= a["U_finest"] + b["U_finest"]
            conv[key]["limits_agree"] = bool(agree) if (a.get("verdict") == "CONVERGED" and b.get("verdict") == "CONVERGED") else None
            conv[key]["accepted_limit"] = 0.5 * (a["limit"] + b["limit"]) if agree else None
        c = conv["margin_min_post"]
        m16, m16be, m8 = Q[("trapezoid", 16)]["margin_min_post"], Q[("backeuler", 16)]["margin_min_post"], Q[("trapezoid", 8)]["margin_min_post"]
        if c["accepted_limit"] is not None:
            U = abs(m16 - c["accepted_limit"]) + max(c["trapezoid"]["U_finest"], c["backeuler"]["U_finest"])
            cls = "SAFE" if m16 - U >= 0 else ("UNSAFE" if m16 + U < 0 else "NUMERICALLY_INDETERMINATE")
            u_rule = "accepted limit"
        else:
            U, cls, u_rule = None, "NUMERICALLY_INDETERMINATE", "no accepted limit (rule D8-3)"
        spread = abs(m16 - m16be) + abs(m16 - m8)
        out["cases"][tag] = {"case": case, "algebraic_jump_P_plus": Pp, "jump_residual": jres, "status": st, "quantities": {f"{m}_k{k}": q for (m, k), q in Q.items()},
                             "convergence": conv, "classification_instantaneous_Pmax": {"m16_trapezoid": m16, "m16_backeuler": m16be, "m8_trapezoid": m8, "U": U, "U_rule": u_rule, "class": cls,
                                                                                         "empirical_spread_TR16_BE16_plus_TR16_TR8": spread},
                             "complementary_one_cycle_mean": {f"{m}_k{k}": Q[(m, k)]["cycle_mean_min_margin"] for (m, k) in Q}}
    # rule D8-1: local k = 16 vs uniform dt/16 (reference case)
    d81 = {}
    for meth in ("trapezoid", "backeuler"):
        a = D6.load(T.RUNS / f"D57D8_b7_{meth}_loc16")
        b = D6.load(T6.RUNS / f"D56D8_{meth}_dt16")
        w = lambda z: (z["t"] >= TE - 1e-9) & (z["t"] <= TE + 0.5 + 1e-9)
        ta, tb = a["t"][w(a)], b["t"][w(b)]
        same_grid = bool(ta.shape == tb.shape and np.array_equal(ta, tb))
        dP = float(np.abs(a["P"][w(a)] - b["P"][w(b)]).max()) if same_grid else None
        post = {}
        for tt in (0.6, 1.0, 5.0, 15.0):
            ia, ib = D6.at(a, TE + tt), D6.at(b, TE + tt)
            post[str(tt)] = {"t_a": float(a["t"][ia]), "t_b": float(b["t"][ib]), "max_abs_dP": float(np.abs(a["P"][ia] - b["P"][ib]).max()), "max_abs_dV": float(np.abs(a["V"][ia] - b["V"][ib]).max())}
        qa, qb = D6.quantities(a, out["cases"]["b7"]["algebraic_jump_P_plus"]), D6.quantities(b, out["cases"]["b7"]["algebraic_jump_P_plus"])
        d81[meth] = {"same_grid_on_window": same_grid, "max_abs_dP_window": dP, "pass_1e-9": bool(dP is not None and dP <= 1e-9), "after_window": post,
                     "delta_quantities_local_minus_uniform": {k: float(qa[k] - qb[k]) for k in ("P_SG31_max_0_500ms", "margin_min_post", "f_coi_nadir_hz", "V_min_post", "rocof_coi_100ms_hz_s")}}
        out["cases"]["b7"]["quantities"][f"{meth}_loc16"] = qa
    out["rule_D8_1"] = d81
    # rule D8-4: U_D8 for lot M3V
    acc = [v["classification_instantaneous_Pmax"]["U"] for v in out["cases"].values() if v["classification_instantaneous_Pmax"]["U"] is not None]
    if len(acc) == len(CASES):
        U_D8, rule = max(acc), "max over cases of |m16 - L| + U_finest (all cases have an accepted limit)"
    else:
        U_D8, rule = max(v["classification_instantaneous_Pmax"]["empirical_spread_TR16_BE16_plus_TR16_TR8"] for v in out["cases"].values()), \
            "empirical method-and-step spread max |m16,TR - m16,BE| + |m16,TR - m8,TR| (not every case has an accepted limit)"
    out["rule_D8_4"] = {"U_D8_pu": U_D8, "rule": rule}
    with open(C55.ART / "IEEE39_DEC057_D8_convergence.json", "x", encoding="utf-8") as f:
        json.dump(out, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else float(o))
    # figures
    fig, ax = plt.subplots(2, 3, figsize=(16, 7.5), sharex=True)
    for col, tag in enumerate(CASES):
        for row, meth in enumerate(("trapezoid", "backeuler")):
            a = ax[row, col]
            for k in (1, 2, 4, 8, 16):
                if (tag, meth, k) in Z:
                    z = Z[(tag, meth, k)]
                    w = (z["t"] >= TE - 0.005) & (z["t"] <= TE + 0.04)
                    i = int(np.argmin((PMAX[None, :] - z["P"][w]).min(0)))
                    a.plot((z["t"][w] - TE) * 1e3, z["P"][w, i], marker=".", ms=2.5, lw=0.8, label=f"k = {k} ({C55.UNITS[i]})")
            unit = out["cases"][tag]["quantities"][f"{meth}_k16"]["margin_min_unit"]
            a.axhline(PMAX[C55.UNITS.index(unit)], c="k", ls="--", lw=0.8, label=f"Pmax {unit}")
            a.set(title=f"{CASES[tag]}: {meth}", xlabel="time after event (ms)" if row else None, ylabel="P of the critical unit (pu)" if col == 0 else None)
            a.legend(fontsize=6)
    fig.tight_layout()
    with open(C55.FIG / "IEEE39_DEC057_D8_peaks.png", "xb") as f:
        fig.savefig(f, dpi=140, format="png")
    plt.close(fig)
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.3))
    for a, tag in zip(ax, CASES):
        for meth, mk in (("trapezoid", "o-"), ("backeuler", "s-")):
            c = out["cases"][tag]["convergence"]["margin_min_post"][meth]
            ks = [int(k) for k in c["values"]]
            a.plot([C54.DT / k for k in ks], list(c["values"].values()), mk, label=f"instantaneous, {meth} ({c.get('verdict')})")
            cm = out["cases"][tag]["convergence"]["cycle_mean_min_margin"][meth]
            a.plot([C54.DT / int(k) for k in cm["values"]], list(cm["values"].values()), mk, alpha=0.45, label=f"one-cycle mean (complementary), {meth}")
        a.axhline(0, c="k", lw=0.8)
        a.set_xscale("log", base=2)
        a.set(title=f"{CASES[tag]}: {out['cases'][tag]['classification_instantaneous_Pmax']['class']}", xlabel="h in [t_e - dt, t_e + 0.5 s] (s)", ylabel="min Pmax margin (pu)")
        a.legend(fontsize=6)
    fig.tight_layout()
    with open(C55.FIG / "IEEE39_DEC057_D8_convergence.png", "xb") as f:
        fig.savefig(f, dpi=140, format="png")
    plt.close(fig)
    print(json.dumps({"D8_1": {m: {k: v[k] for k in ("same_grid_on_window", "max_abs_dP_window", "pass_1e-9", "delta_quantities_local_minus_uniform")} for m, v in d81.items()},
                      "D8_4": out["rule_D8_4"],
                      "cases": {t: {"class": v["classification_instantaneous_Pmax"], "peak": {m: (v["convergence"]["P_SG31_max_0_500ms"][m].get("verdict"), v["convergence"]["margin_min_post"][m]["values"])
                                                                                               for m in ("trapezoid", "backeuler")},
                                    "margin_verdicts": {m: (v["convergence"]["margin_min_post"][m].get("verdict"), v["convergence"]["margin_min_post"][m].get("p"), v["convergence"]["margin_min_post"][m].get("limit")) for m in ("trapezoid", "backeuler")},
                                    "cycle": v["complementary_one_cycle_mean"], "slow": {k: v["convergence"][k]["limits_agree"] for k in ("f_coi_nadir_hz", "V_min_post", "P_SG31_at_1.0s", "f_coi_at_5.0s")}}
                                for t, v in out["cases"].items()}}, indent=1, default=float))


if __name__ == "__main__":
    main()
