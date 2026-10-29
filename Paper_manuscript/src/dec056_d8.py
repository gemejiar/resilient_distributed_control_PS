"""DEC-056 / D8 analysis (post-processing of the D8 lot and of the two reused DEC-055 L1 runs; the algebraic jump is a static solve, no TDS).
Writes IEEE39_DEC056_D8_convergence.json and the figures IEEE39_DEC056_D8_{transient,convergence,trajectories}.png exclusively.
Decision rules: ops/sted/DEC056_protocol.md (pre-registered)."""
from __future__ import annotations

import json

import numpy as np

import dec054_common as C54
import dec055_common as C55
import dec056_tds as T

R55 = C54.RUNS_DIR.parent / "DEC055_runs"
TE = C55.EVENT_T
PMAX = np.array([10.4, 6.5, 6.82, 6.97, 8.65, 11.0, 7.5, 5.64, 5.5, 5.95])       # case Pmax in UNITS order (IEEE39_DEC053_constraints_dictionary.csv)
SG31 = 1
FS = 1.25


def runs():
    out = {"trapezoid": {1: R55 / "D55L1_regress_P3B2_b7P_M3", 2: R55 / "D55L1_dthalf_P3B2_b7P_M3"}, "backeuler": {}}
    for d in (4, 8, 16):
        out["trapezoid"][d] = T.RUNS / f"D56D8_trapezoid_dt{d}"
    for d in (1, 2, 4, 8, 16):
        out["backeuler"][d] = T.RUNS / f"D56D8_backeuler_dt{d}"
    return out


def load(p, tf=20.0):
    z = dict(np.load(p / "series.npz"))
    k = z["t"] <= tf + 1e-9
    return {key: (v[k] if (hasattr(v, "shape") and v.shape[:1] == z["t"].shape) else v) for key, v in z.items()}


def at(z, t):
    i = int(np.searchsorted(z["t"], t - 1e-9))
    return i


def quantities(z, P_plus):
    t, P, V = z["t"], z["P"], z["V"]
    ke = at(z, TE)
    post = (t >= TE - 1e-9)
    w = post & (t <= TE + 0.5)
    i31 = int(np.argmax(np.where(w, P[:, SG31], -np.inf)))
    mg = PMAX[None, :] - P[post]
    a, j = np.unravel_index(np.argmin(mg), mg.shape)
    fc = z.get("f_coi_hz")
    fm = C55.mean_busfreq_hz(z["f_bus_hz"])
    q = {"P_SG31_first_sample": float(P[ke, SG31]), "first_sample_minus_jump_SG31": float(P[ke, SG31] - P_plus[SG31]),
         "first_sample_minus_jump_maxabs": float(np.abs(P[ke] - P_plus).max()),
         "P_SG31_max_0_500ms": float(P[i31, SG31]), "t_P_SG31_max_after_event_s": float(t[i31] - TE),
         "margin_min_post": float(mg[a, j]), "margin_min_unit": C55.UNITS[j], "t_margin_min_after_event_s": float(t[post][a] - TE),
         "V_min_post": float(V[post].min()), "V_max_post": float(V[post].max()),
         "f_meanbus_nadir_hz": float(fm[post].min()), "t_meanbus_nadir_s": float(t[post][np.argmin(fm[post])] - TE)}
    if fc is not None:
        q.update({"f_coi_nadir_hz": float(fc[post].min()), "t_f_coi_nadir_s": float(t[post][np.argmin(fc[post])] - TE),
                  "rocof_coi_100ms_hz_s": float((fc[at(z, TE + 0.1)] - fc[ke - 1]) / (t[at(z, TE + 0.1)] - t[ke - 1]))})
    for tt in (0.05, 0.1, 0.5, 1.0, 5.0, 15.0):
        i = at(z, TE + tt)
        q[f"P_SG31_at_{tt}s"] = float(P[i, SG31])
        q[f"Q_SG31_at_{tt}s"] = float(z["Q"][i, SG31])
        q[f"V_bus7_at_{tt}s"] = float(V[i, 6])
        if fc is not None:
            q[f"f_coi_at_{tt}s"] = float(fc[i])
    # ringing index: period-2h component in the first 50 ms
    k50 = at(z, TE + 0.05)
    seg = P[ke:k50 + 2]
    if len(seg) >= 3:
        r2 = np.abs(seg[1:-1] - 0.5 * (seg[:-2] + seg[2:]))
        d = np.diff(seg, axis=0)
        alt = (np.sign(d[1:] * d[:-1]) < 0).mean(axis=0)
        q.update({"ringing_amp_2h_50ms_max_pu": float(r2.max()), "ringing_amp_2h_50ms_GFM_max_pu": float(r2[:, 6:].max()), "sign_alternation_fraction_50ms_GFM": float(alt[6:].mean()),
                  "sign_alternation_fraction_50ms_SG": float(alt[:6].mean())})
    return q


def order_and_limit(vals):
    """vals: {div: q} for div = 1, 2, 4, ...  Pre-registered rule on the last three levels."""
    ds = sorted(vals)
    if len(ds) < 3:
        return {"verdict": "INSUFFICIENT_LEVELS"}
    a, b, c = (vals[d] for d in ds[-3:])
    e1, e2 = b - a, c - b
    out = {"levels": ds, "diff_last": float(e2), "diff_prev": float(e1)}
    if e2 == 0.0 and e1 == 0.0:
        return dict(out, verdict="CONVERGED", p=None, limit=float(c), U_finest=0.0)
    if e2 == 0.0 or np.sign(e1) != np.sign(e2) or abs(e2) >= abs(e1):
        return dict(out, verdict="NOT_CONVERGED", p=None)
    p = float(np.log2(abs(e1) / abs(e2)))
    out["p"] = p
    if not (0.7 <= p <= 2.5):
        return dict(out, verdict="NOT_CONVERGED")
    lim = float(c + e2 / (2 ** p - 1))
    U_f = float(FS * abs(e2) / (2 ** p - 1))
    out.update({"verdict": "CONVERGED", "limit": lim, "U_finest": U_f, "U_by_level": {str(d): float(abs(vals[d] - lim) + U_f) for d in ds},
                "U_protocol_formula_finest_pair": float(FS * abs(e2) / (2 ** p - 1) + abs(e2))})      # literal formula of the protocol text (more conservative)
    return out


def jump_plus():
    import dec054_opf as OPF
    import dec055_oc as OCM
    ref = json.loads((C54.RUNS_DIR / T.REF / "config.json").read_text(encoding="utf-8"))["test"]
    OCM.PFLOW_TOL = 1e-6                                   # same PFlow tolerance as the runs of the reference configuration
    plant = OCM.make_plant("OC1")
    j = plant.jump(np.asarray(ref["z"], float), OPF.Scenario("b7P", ref["bus"], ref["kind"], ref["amp"]))
    assert j["ok"], j
    return np.asarray(j["P_plus"], float), float(j["residual"])


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    P_plus, jres = jump_plus()
    R = runs()
    Z, Q, status = {}, {}, {}
    for meth, dd in R.items():
        for d, p in dd.items():
            st = json.loads((p / "status.json").read_text(encoding="utf-8"))
            status[f"{meth}_dt{d}"] = st["status"]
            if (p / "series.npz").exists():
                Z[(meth, d)] = load(p)
                Q[(meth, d)] = quantities(Z[(meth, d)], P_plus)
    # wrapper regression and Newton tolerance
    ref = load(R55 / "D55L1_regress_P3B2_b7P_M3")
    rg = load(T.RUNS / "D56D8_trapezoid_dt1_regress")
    regress = {k: bool(rg[k].shape == ref[k].shape and np.array_equal(rg[k], ref[k])) for k in ("t", "P", "Q", "V")}
    tl = load(T.RUNS / "D56D8_trapezoid_dt1_tol1e-8")
    qt = quantities(tl, P_plus)
    tol_sens = {k: float(qt[k] - Q[("trapezoid", 1)][k]) for k in qt if isinstance(qt[k], float)}
    # the tol = 1e-8 run reduced its step at the event step (ANDES halves h when Newton needs >= 15 iterations, also with fixt = 1): non-uniform grid,
    # differences therefore on the reference grid by linear interpolation, excluding the first 50 ms after the event where interpolation is not meaningful
    dtl = np.diff(tl["t"])
    tol_sens["nonuniform_steps"] = int((np.abs(dtl - T.DT) > 1e-12).sum())
    tol_sens["t_first_nonuniform"] = float(tl["t"][np.argmax(np.abs(dtl - T.DT) > 1e-12)])
    keep = (ref["t"] < TE - 1e-9) | (ref["t"] > TE + 0.05)
    for k in ("P", "V"):
        ii = np.column_stack([np.interp(ref["t"], tl["t"], tl[k][:, c]) for c in range(tl[k].shape[1])])
        tol_sens[f"max_abs_{k}_diff_20s_interp_excl_50ms"] = float(np.abs(ii - ref[k])[keep].max())
    tol_sens["max_abs_P_diff_20s"] = tol_sens["max_abs_P_diff_20s_interp_excl_50ms"]
    # convergence per quantity and sequence
    keys = [k for k in Q[("backeuler", 1)] if isinstance(Q[("backeuler", 1)][k], float)]
    conv = {}
    for k in keys:
        conv[k] = {}
        for meth in ("trapezoid", "backeuler"):
            vals = {d: Q[(meth, d)][k] for d in sorted(R[meth]) if (meth, d) in Q}
            conv[k][meth] = dict(order_and_limit(vals), values={str(d): v for d, v in vals.items()})
        a, b = conv[k]["trapezoid"], conv[k]["backeuler"]
        if a.get("verdict") == "CONVERGED" and b.get("verdict") == "CONVERGED":
            conv[k]["limits_agree"] = bool(abs(a["limit"] - b["limit"]) <= a["U_finest"] + b["U_finest"])
            conv[k]["accepted_limit"] = 0.5 * (a["limit"] + b["limit"]) if conv[k]["limits_agree"] else None
        else:
            conv[k]["limits_agree"] = None
            conv[k]["accepted_limit"] = None
    # classification of the protocol-step stored-sample margin (pre-registered rule 2)
    m_dt = Q[("trapezoid", 1)]["margin_min_post"]
    cm = conv["margin_min_post"]
    if cm["accepted_limit"] is not None:
        U = abs(m_dt - cm["accepted_limit"]) + max(cm["trapezoid"]["U_finest"], cm["backeuler"]["U_finest"])
        cls = "SAFE" if m_dt - U >= 0 else ("UNSAFE" if m_dt + U < 0 else "NUMERICALLY_INDETERMINATE")
    else:
        U, cls = None, "NUMERICALLY_INDETERMINATE (no accepted limit)"
    out = {"stage": "DEC-056 D8 convergence analysis", "reference_case": T.REF, "status": status, "wrapper_regression_bit_identical": regress,
           "algebraic_jump_P_plus": P_plus, "jump_residual": jres, "newton_tol_1e-8_minus_1e-4_at_dt": tol_sens, "quantities": {f"{m}_dt{d}": q for (m, d), q in Q.items()},
           "convergence": conv, "protocol_step_margin": {"m_dt_trapezoid": m_dt, "U": U, "class": cls}}
    with open(C55.ART / "IEEE39_DEC056_D8_convergence.json", "x", encoding="utf-8") as f:
        json.dump(out, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else float(o))
    # figures
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.2), sharey=True)
    for a, meth in zip(ax, ("trapezoid", "backeuler")):
        for d in sorted(R[meth]):
            if (meth, d) in Z:
                z = Z[(meth, d)]
                w = (z["t"] >= TE - 0.01) & (z["t"] <= TE + 0.06)
                a.plot((z["t"][w] - TE) * 1e3, z["P"][w, SG31], marker=".", ms=3, lw=0.8, label=f"h = dt/{d}")
        a.axhline(PMAX[SG31], c="k", ls="--", lw=0.8, label="Pmax SG31")
        a.axhline(P_plus[SG31], c="tab:red", ls=":", lw=0.8, label="algebraic jump P+")
        a.set(xlabel="time after event (ms)", title=f"SG31 P, {meth}")
        a.legend(fontsize=7)
    ax[0].set_ylabel("P (pu, system base)")
    fig.tight_layout()
    with open(C55.FIG / "IEEE39_DEC056_D8_transient.png", "xb") as f:
        fig.savefig(f, dpi=140, format="png")
    plt.close(fig)
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
    for a, k in zip(ax, ("P_SG31_max_0_500ms", "first_sample_minus_jump_SG31", "f_coi_nadir_hz")):
        for meth, mk in (("trapezoid", "o-"), ("backeuler", "s-")):
            c = conv[k][meth]
            hs = [T.DT / int(d) for d in c["values"]]
            vs = list(c["values"].values())
            a.plot(hs, vs, mk, label=f"{meth} ({c.get('verdict')}, p={c.get('p') if c.get('p') is None else round(c['p'], 2)})")
            if c.get("limit") is not None:
                a.axhline(c["limit"], ls=":", lw=0.8, c="tab:blue" if meth == "trapezoid" else "tab:orange")
        a.set_xscale("log", base=2)
        a.set(xlabel="h (s)", title=k)
        a.legend(fontsize=7)
    fig.tight_layout()
    with open(C55.FIG / "IEEE39_DEC056_D8_convergence.png", "xb") as f:
        fig.savefig(f, dpi=140, format="png")
    plt.close(fig)
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
    zf = Z[("backeuler", 16)]
    for meth, d, ls in (("trapezoid", 1, "-"), ("trapezoid", 16, "--"), ("backeuler", 1, "-."), ("backeuler", 16, ":")):
        if (meth, d) not in Z:
            continue
        z = Z[(meth, d)]
        lab = f"{meth} dt/{d}"
        ax[0].plot(z["t"] - TE, z["f_coi_hz"], ls=ls, lw=1, label=lab)
        ax[1].plot(z["t"] - TE, z["V"][:, 6], ls=ls, lw=1, label=lab)
        ax[2].plot(z["t"] - TE, z["Q"][:, SG31], ls=ls, lw=1, label=lab)
    for a, ttl in zip(ax, ("f_COI (Hz)", "|V| bus 7 (pu)", "Q SG31 (pu)")):
        a.set(xlim=(-0.5, 15), xlabel="time after event (s)", title=ttl)
        a.legend(fontsize=7)
    fig.tight_layout()
    with open(C55.FIG / "IEEE39_DEC056_D8_trajectories.png", "xb") as f:
        fig.savefig(f, dpi=140, format="png")
    plt.close(fig)
    print(json.dumps({"regress": regress, "tol": {k: tol_sens[k] for k in ("P_SG31_max_0_500ms", "margin_min_post", "max_abs_P_diff_20s")},
                      "class": out["protocol_step_margin"],
                      "summary": {k: {m: (conv[k][m].get("verdict"), conv[k][m].get("p"), conv[k][m].get("limit")) for m in ("trapezoid", "backeuler")} | {"agree": conv[k]["limits_agree"]}
                                  for k in ("P_SG31_max_0_500ms", "margin_min_post", "first_sample_minus_jump_SG31", "first_sample_minus_jump_maxabs", "f_coi_nadir_hz", "V_min_post",
                                            "P_SG31_at_0.05s", "P_SG31_at_1.0s", "f_coi_at_5.0s", "V_bus7_at_5.0s", "ringing_amp_2h_50ms_GFM_max_pu")}}, indent=1, default=float))


if __name__ == "__main__":
    main()
