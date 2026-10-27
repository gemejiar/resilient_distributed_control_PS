"""E9-A audit of the stored C2t runs: physical constraint matrix, transient margins of the ten units, IBR audit and SG31 timeline.

Reads the stored raw series only (no new simulation, nothing is modified): E5t (primary control only), E8 (original RDC, "B2") and
B3 (centered RDC) for S0, P+ and Q+.  Limits are the case limits used since E7 (PV/Slack pmax, qmin, qmax; Sn/100 for S); pmin = 0.
The bus-voltage band 0.95--1.05 pu is the one of the B3-A AC selection.  Nothing here is a safety claim: all barriers are evaluated on
modelled outputs only.
"""

from __future__ import annotations

import json
import os

os.environ["C2_VARIANT"] = "C2t"

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from run_e0_ieee39 import ARTIFACTS_DIR, FIGURES_DIR, git_commit, sha256  # noqa: E402

OUT_JSON = ARTIFACTS_DIR / "IEEE39_E9A_physical_audit.json"
FIG_MARGINS = FIGURES_DIR / "IEEE39_E9A_margins.png"
FIG_SG31 = FIGURES_DIR / "IEEE39_E9A_sg31_timeline.png"
EVENT = 5.0
V_BAND = (0.95, 1.05)
LOAD_STEP_P_PU = 0.58564


def load_sets() -> dict[str, dict[str, np.ndarray]]:
    e8 = np.load(ARTIFACTS_DIR / "IEEE39_E8_C2t_timeseries.npz")
    e5 = np.load(ARTIFACTS_DIR / "IEEE39_E5_C2t_timeseries.npz")
    sets: dict[str, dict[str, np.ndarray]] = {}
    for sc in ("S0", "P+", "Q+"):
        if sc == "S0":
            continue
        sets[f"E5t primary only {sc}"] = {k[len(sc) + 1:]: e5[k] for k in e5.files if k.startswith(sc + "_")}
    for sc in ("S0", "P+", "Q+"):
        sets[f"B2 (E8) {sc}"] = {k[len(sc) + 1:]: e8[k] for k in e8.files if k.startswith(sc + "_")}
    for sc, tag in (("S0", "S0"), ("P+", "Pplus"), ("Q+", "Qplus")):
        z = np.load(ARTIFACTS_DIR / f"IEEE39_B3_C2t_{tag}_timeseries.npz")
        sets[f"B3 {sc}"] = {k[3:]: z[k] for k in z.files if k.startswith("B3_")}
    return sets


def unit_arrays(d: dict[str, np.ndarray], ref: dict[str, np.ndarray]):
    p = np.hstack([d["sg_p_pu"], d["gfm_p_pu"]])
    q = np.hstack([d["sg_q_pu"], d["gfm_q_pu"]])
    ids = list(ref["bus_ids"])
    cols = [ids.index(b) for b in ref["unit_bus_ids"]]
    return p, q, d["bus_voltage_pu"][:, cols]


def spans(t: np.ndarray, flag: np.ndarray) -> list[tuple[float, float]]:
    out, start = [], None
    for i, f in enumerate(flag):
        if f and start is None:
            start = t[i]
        if not f and start is not None:
            out.append((float(start), float(t[i - 1])))
            start = None
    if start is not None:
        out.append((float(start), float(t[-1])))
    return out


def main() -> int:
    sets = load_sets()
    ref = sets["B2 (E8) P+"]
    names = [("SG" if i < ref["sg_p_pu"].shape[1] else "GFM") + str(b) for i, b in enumerate(ref["unit_bus_ids"])]
    lim = {k: ref[f"unit_{k}"] for k in ("pmax", "pmin", "qmax", "qmin", "smax")}
    rp, rq = lim["pmax"] - lim["pmin"], lim["qmax"] - lim["qmin"]
    result: dict = {"source": "stored raw series (read only)", "units": names, "limits_pu": {k: v.tolist() for k, v in lim.items()},
                    "voltage_band_pu": list(V_BAND), "git_commit": git_commit(),
                    "raw_sha256": {n: sha256(ARTIFACTS_DIR / f) for n, f in (("E8", "IEEE39_E8_C2t_timeseries.npz"), ("E5t", "IEEE39_E5_C2t_timeseries.npz"),
                                                                              ("B3_S0", "IEEE39_B3_C2t_S0_timeseries.npz"), ("B3_P+", "IEEE39_B3_C2t_Pplus_timeseries.npz"),
                                                                              ("B3_Q+", "IEEE39_B3_C2t_Qplus_timeseries.npz"))},
                    "runs": {}}
    margin_mat = {}
    for name, d in sets.items():
        t = d["time_s"]
        p, q, v = unit_arrays(d, ref)
        post = t >= EVENT
        s_rel = 1.0 - np.hypot(p, q) / lim["smax"]
        m = {"P_to_pmax_pu": lim["pmax"] - p, "P_to_pmin_pu": p - lim["pmin"], "Q_to_qmax_pu": lim["qmax"] - q, "Q_to_qmin_pu": q - lim["qmin"], "S_rel": s_rel}
        rec = {k: {"min": v_.min(axis=0).tolist(), "t_min": [float(t[i]) for i in v_.argmin(axis=0)]} for k, v_ in m.items()}
        rec["min_P_to_pmax_fraction_of_range"] = ((lim["pmax"] - p).min(axis=0) / rp).tolist()
        rec["min_Q_to_limit_fraction_of_range"] = (np.minimum(lim["qmax"] - q, q - lim["qmin"]).min(axis=0) / rq).tolist()
        rec["violations"] = {}
        for k, v_ in m.items():
            for i, n in enumerate(names):
                if (v_[:, i] < 0).any():
                    sp = spans(t, v_[:, i] < 0)
                    rec["violations"][f"{n}:{k}"] = {"spans_s": sp, "duration_s": float(sum(b - a for a, b in sp)), "worst_margin": float(v_[:, i].min()),
                                                     "t_worst_s": float(t[v_[:, i].argmin()])}
        vb = d["bus_voltage_pu"]
        bus_ids = ref["bus_ids"].tolist()
        out_band = (vb < V_BAND[0]) | (vb > V_BAND[1])
        rec["bus_voltage"] = {"min_pu": float(vb.min()), "max_pu": float(vb.max()), "max_bus": int(bus_ids[int(vb.max(axis=0).argmax())]),
                              "pre_event_max_pu": float(vb[(t >= EVENT - 2) & (t < EVENT)].mean(axis=0).max()),
                              "pre_event_buses_above_1p05": [int(b) for b, x in zip(bus_ids, vb[(t >= EVENT - 2) & (t < EVENT)].mean(axis=0)) if x > V_BAND[1]],
                              "n_buses_ever_outside_band": int(out_band.any(axis=0).sum()),
                              "final_buses_outside_band": [int(b) for b, x in zip(bus_ids, vb[t >= t[-1] - 2].mean(axis=0)) if not V_BAND[0] <= x <= V_BAND[1]]}
        rec["frequency"] = {"max_abs_dev_hz": float(np.abs(d["bus_frequency_hz"].mean(axis=1) - 60.0).max()),
                            "nadir_hz": float(d["bus_frequency_hz"].mean(axis=1)[post].min())}
        if "cmd_y" in d:
            rec["gfm_internal_limiter"] = {"PIplim_y_max": np.abs(d["cmd_y"]).max(axis=0).tolist(), "PIqlim_y_max": np.abs(d["cmd_yq"]).max(axis=0).tolist()}
        result["runs"][name] = rec
        margin_mat[name] = np.array([rec["P_to_pmax_pu"]["min"], rec["Q_to_qmax_pu"]["min"], rec["Q_to_qmin_pu"]["min"]])
    # constraint matrix (what is modelled, what is not)
    result["constraint_matrix"] = {
        "physical_outputs_modelled": ["P_i <= pmax_i (case limit)", "P_i >= pmin_i = 0", "Q_i in [qmin_i, qmax_i] (case limits)",
                                      "S_i^2 = P_i^2 + Q_i^2 <= (Sn_i/100)^2 (circle; not an SG capability curve)", "V_bus in [0.95, 1.05] pu at the 39 buses (B3-A band)"],
        "reference_set_modelled": ["Pset_i in [pmin_i, pmax_i]", "Qset_i in [qmin_i, qmax_i]", "Pset^2 + Qset^2 <= smax^2 (control coordinates, not physical power; DEC-038)"],
        "UNMODELED": ["SG capability curve (stator current, field, underexcitation)", "REGF1 converter current limit (the model has none; no I_max barrier is declared)",
                      "SG field thermal state", "REGF1 energy / state of charge"],
        "internal_limiters_present": {"REGF1.PIplim": "+-Pmax = +-Sn/100 (not the case pmax)", "REGF1.PIqlim": "+-Qmax = +-Sn/100", "TGOV1N valve VMAX/VMIN": "above the case pmax"}}
    # SG31 timeline from the stored runs
    i31, i35 = names.index("SG31"), names.index("SG35")
    sg31 = {}
    fig, ax = plt.subplots(2, 2, figsize=(13, 8))
    for name in ("E5t primary only P+", "B2 (E8) P+", "B3 P+"):
        d = sets[name]; t = d["time_s"]; p, q, _ = unit_arrays(d, ref)
        ex = p[:, i31] - lim["pmax"][i31]
        sp = spans(t, ex > 0)
        pk = int(p[:, i31].argmax())
        pre = float(p[(t >= EVENT - 1) & (t < EVENT), i31].mean())
        win = (t >= EVENT) & (t <= t[pk])
        slope = np.gradient(p[:, i31], t)
        om = d["bus_frequency_hz"].mean(axis=1)
        sg31[name] = {"pmax_pu": float(lim["pmax"][i31]), "pre_event_P_pu": pre, "pre_event_margin_pu": float(lim["pmax"][i31] - pre), "violation_spans_s": sp, "per_span_peak_excess_pu": [float(ex[(t >= a) & (t <= b)].max()) for a, b in sp],
                      "per_span_t_peak_after_event_s": [float(t[(t >= a) & (t <= b)][ex[(t >= a) & (t <= b)].argmax()] - EVENT) for a, b in sp],
                      "first_violation_after_event_s": (sp[0][0] - EVENT) if sp else None, "duration_above_pmax_s": float(sum(b - a for a, b in sp)),
                      "peak_P_pu": float(p[pk, i31]), "excess_pu": float(max(0.0, p[pk, i31] - lim["pmax"][i31])), "t_peak_after_event_s": float(t[pk] - EVENT),
                      "rise_peak_minus_pre_pu": float(p[pk, i31] - pre), "rise_over_load_step": float((p[pk, i31] - pre) / LOAD_STEP_P_PU),
                      "max_dP_dt_pu_per_s_before_peak": float(slope[win].max()), "mean_frequency_at_peak_hz": float(om[pk]),
                      "other_units_P_rise_at_t_peak_pu": (p[pk] - p[(t >= EVENT - 1) & (t < EVENT)].mean(axis=0)).tolist(),
                      "final_P_pu": float(p[t >= t[-1] - 2, i31].mean()), "final_margin_pu": float(lim["pmax"][i31] - p[t >= t[-1] - 2, i31].mean())}
        sg = slice(None)
        ax[0, 0].plot(t - EVENT, p[:, i31], label=name); ax[0, 1].plot(t - EVENT, p[:, i31], label=name)
        ax[1, 0].plot(t - EVENT, p[:, i35], label=name); ax[1, 1].plot(t - EVENT, om - 60.0, label=name)
    for a, ttl, hl in ((ax[0, 0], "SG31 physical P (0--60 s after event)", lim["pmax"][i31]), (ax[0, 1], "SG31 physical P (zoom)", lim["pmax"][i31]),
                       (ax[1, 0], "SG35 physical P", lim["pmax"][i35])):
        a.axhline(hl, color="k", ls="--", lw=.8, label="case pmax"); a.set_title(ttl); a.grid(alpha=.25); a.set_xlabel("Time since event [s]"); a.set_ylabel("P [pu]")
    ax[0, 0].set_xlim(-1, 60); ax[0, 1].set_xlim(-0.5, 8); ax[1, 0].set_xlim(-1, 60)
    ax[1, 1].set_title("mean bus frequency - 60 Hz"); ax[1, 1].set_xlim(-1, 20); ax[1, 1].set_ylabel("Hz"); ax[1, 1].grid(alpha=.25); ax[1, 1].set_xlabel("Time since event [s]")
    ax[0, 0].legend(fontsize=7); fig.suptitle("E9-A: SG31 and SG35 physical power in P+ (stored runs, read only)"); fig.tight_layout()
    fig.savefig(FIG_SG31, dpi=300, bbox_inches="tight"); plt.close(fig)
    result["SG31_timeline"] = sg31
    # margin figure: min margins per unit and run
    labels = list(margin_mat)
    fig, ax = plt.subplots(1, 3, figsize=(17, 6))
    for k, ttl in enumerate(("min (pmax - P) [pu]", "min (qmax - Q) [pu]", "min (Q - qmin) [pu]")):
        mat = np.array([margin_mat[l][k] for l in labels])
        im = ax[k].imshow(mat, aspect="auto", cmap="RdYlGn", vmin=-0.1, vmax=0.5)
        ax[k].set_xticks(range(10)); ax[k].set_xticklabels(names, rotation=60, fontsize=8); ax[k].set_yticks(range(len(labels))); ax[k].set_yticklabels(labels if k == 0 else [], fontsize=8)
        ax[k].set_title(ttl)
        for r in range(mat.shape[0]):
            for c in range(10):
                ax[k].text(c, r, f"{mat[r, c]:.2f}", ha="center", va="center", fontsize=6)
    fig.colorbar(im, ax=ax, shrink=.7); fig.suptitle("E9-A: minimum transient physical margins of the ten units over all stored runs (negative = violation of the case limit)")
    fig.savefig(FIG_MARGINS, dpi=300, bbox_inches="tight"); plt.close(fig)
    OUT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("units", names)
    for n, r in result["runs"].items():
        print(n, "viol:", {k: round(v["worst_margin"], 4) for k, v in r["violations"].items()}, "| Vmax", round(r["bus_voltage"]["max_pu"], 4), "bus", r["bus_voltage"]["max_bus"])
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "other_units_P_rise_at_t_peak_pu"} for k, v in sg31.items()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
