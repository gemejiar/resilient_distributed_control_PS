"""DEC-052 block D (H3-R audit).  Static algebraic solves and post-processing of stored DEC-051 data only; no time-domain simulation.
Outputs: IEEE39_DEC052_H3_voltage_audit.csv, IEEE39_DEC052_H3_reserve_audit.csv, IEEE39_DEC052_H3_location_scan.csv, IEEE39_DEC052_H3_audit.json."""
from __future__ import annotations

import csv
import json

import numpy as np

import dec052_common as K
import dec051_core as C
import run_dec051_h3_jump as J
import run_e8_ieee39 as e8
import select_equilibrium_b3 as b3
from run_e0_ieee39 import ARTIFACTS_DIR as A

NAMES = J.NAMES
CFG = "C2t_Vsafe_R35_040"
LO, HI = 0.95, 1.05
AMP = 0.58564


def pf_c2t(bus, dp):
    """The plant used by the DEC-051 screening (select_equilibrium_b3.load_plant = historical C2t, no Vsafe/R35 hook)."""
    s = b3.load_plant({bus: (dp, 0.0)} if bus is not None else {})
    ok = bool(s.PFlow.run())
    return ok, np.asarray(s.Bus.v.v, float).copy()


def pf_variant(bus, dp):
    """The plant used by the H3 simulations: C2t_Vsafe_R35_040 (hook applied before the power flow), post-event load added to PQ.p0."""
    system, ctx = e8.configure("S0", e8.TIME_STEP_S)
    J.CONFIGS[CFG](system, ctx)
    if bus is not None:
        k = [int(b) for b in system.PQ.bus.v].index(bus)
        system.PQ.p0.v[k] += dp
    ok = bool(system.PFlow.run())
    return ok, np.asarray(system.Bus.v.v, float).copy()


def band(v):
    return {"vmin": float(v.min()), "vmax": float(v.max()), "n_above_1.05": int((v > HI).sum()), "n_below_0.95": int((v < LO).sum()), "within_original_band": bool(v.min() >= LO and v.max() <= HI)}


def main() -> int:
    pred = json.loads((A / "IEEE39_DEC051_H3_predictions.json").read_text(encoding="utf-8"))
    jr = json.loads((A / "IEEE39_DEC051_H3_jump.json").read_text(encoding="utf-8"))["configs"]
    s1 = json.loads((A / "IEEE39_DEC051_H3_sim1.json").read_text(encoding="utf-8"))
    s2 = json.loads((A / "IEEE39_DEC051_H3_sim2.json").read_text(encoding="utf-8"))
    out: dict = {"stage": "DEC-052 block D (H3-R audit)", "git_commit": K.git_commit(), "software": K.env(), "band": [LO, HI],
                 "inputs_sha256": {f: K.sha(A / f) for f in ("IEEE39_DEC051_H3_predictions.json", "IEEE39_DEC051_H3_jump.json", "IEEE39_DEC051_H3_sim1.json", "IEEE39_DEC051_H3_sim2.json")}}
    # ------------------------------------------------------------------ D1/D2: voltage audit
    rows = []
    ok0, v0 = pf_c2t(None, 0.0)
    ok1, v1 = pf_variant(None, 0.0)
    rows.append(["pre-event", "-", "-", "static power flow, historical C2t (plant used by the DEC-051 screening)", ok0] + list(band(v0).values()))
    rows.append(["pre-event", "-", "-", "static power flow, C2t_Vsafe_R35_040 (plant used by the H3 simulations)", ok1] + list(band(v1).values()))
    sysd, ctxd = J.make(J.CONFIGS[CFG])
    vdyn = np.asarray(sysd.dae.y[np.asarray(sysd.Bus.v.a)], float)
    sysc, ctxc = J.make(lambda s, c: None)
    vdync = np.asarray(sysc.dae.y[np.asarray(sysc.Bus.v.a)], float)
    rows.append(["pre-event", "-", "-", "ANDES TDS initialisation t=0, historical C2t", True] + list(band(vdync).values()))
    rows.append(["pre-event", "-", "-", "ANDES TDS initialisation t=0, C2t_Vsafe_R35_040", True] + list(band(vdyn).values()))
    out["pre_event"] = {"static_C2t": band(v0), "static_R35_040": band(v1), "tds_init_C2t": band(vdync), "tds_init_R35_040": band(vdyn), "static_vs_tds_init_max_abs_diff_R35_040": float(np.abs(v1 - vdyn).max()),
                        "static_vs_tds_init_max_abs_diff_C2t": float(np.abs(v0 - vdync).max()), "bus_of_max_C2t": int(np.argmax(v0)) + 1, "bus_of_max_R35_040": int(np.argmax(v1)) + 1}
    system, ctx = J.make(J.CONFIGS[CFG])
    st = C.rdc_state(system, ctx)
    ix = C.index_sets(system)
    cache: dict = {}
    C.apply_params(system, ctx, st, np.concatenate([st["pn"], st["qn"]]))
    C.L.linearize(system, ctx, cache=cache)
    buses = [int(b) for b in system.PQ.bus.v]
    pre_p = st["pn"].copy()
    scan = {r["bus"]: r for r in pred["H3_2"]["selection_scan_sorted_worst_first"]}
    cand = [(4, 0.58564, "P+ 58.564 MW bus 4 (historical nominal)"), (4, 0.644204, "P+ 64.4204 MW bus 4 (H3-1)")] + [(b, AMP, f"P+ 58.564 MW bus {b}") for b in buses if b != 4]
    loc = []
    for bus, dp, label in cand:
        ok_a, va = pf_c2t(bus, dp)
        ok_b, vb = pf_variant(bus, dp)
        j = J.jump(system, ctx, st, ix, cache, bus, dp, 0.0)
        ba, bb, bj = band(va), band(vb), band(j["Vbus"])
        for src, ok, bd in (("static power flow, historical C2t (DEC-051 screening plant)", ok_a, ba), ("static power flow, C2t_Vsafe_R35_040", ok_b, bb), ("algebraic post-jump (differential states continuous), C2t_Vsafe_R35_040", j["converged"], bj)):
            rows.append(["post-event", bus, dp * 100.0, src, ok] + list(bd.values()))
        sc = scan.get(bus)
        dP = j["P"] - pre_p
        loc.append({"bus": bus, "amplitude_MW": dp * 100.0, "label": label, "screen_static_C2t": ba, "static_R35_040": bb, "post_jump_R35_040": bj, "DEC051_predicted_min_margin": sc["predicted_min_margin_all_units"] if sc else None,
                    "DEC051_binding_unit": sc["predicted_binding_unit"] if sc else None, "dP_jump_SG31": float(dP[1]), "dP_jump_SG35": float(dP[3])})
    out["screening_plant_defect"] = {"finding": "the DEC-051 admissibility screen (select_equilibrium_b3.load_plant) evaluated the HISTORICAL C2t plant, whose pre-event voltages reach %.3f pu at bus %d (%d buses above 1.05 pu), not C2t_Vsafe_R35_040 (the plant of the H3 simulations; static voltages %.3f-%.3f pu). The upper-bound relaxation of DEC-051 was unnecessary: it followed from screening the wrong plant." % (v0.max(), int(np.argmax(v0)) + 1, int((v0 > HI).sum()), v1.min(), v1.max()),
                                     "dynamic_simulation_bus_voltage_min_max": {"H3-1": s1["bus_voltage_min_max_pu"], "H3-2": s2["bus_voltage_min_max_pu"]}, "buses_outside_band_in_simulations": {"H3-1": s1["n_buses_outside_0.95_1.05"], "H3-2": s2["n_buses_outside_0.95_1.05"]}}
    adm_static = {r["bus"]: r["static_R35_040"]["within_original_band"] for r in loc}
    adm_jump = {r["bus"]: r["post_jump_R35_040"]["within_original_band"] for r in loc}
    cands = [r for r in loc if r["bus"] != 4 and r["DEC051_predicted_min_margin"] is not None and r["DEC051_predicted_min_margin"] > 0 and adm_static[r["bus"]] and adm_jump[r["bus"]]]
    best = min(cands, key=lambda r: r["DEC051_predicted_min_margin"]) if cands else None
    out["reselection_original_band_on_R35_040_plant"] = {"rule": "DEC-051 rule unchanged (smallest positive predicted margin); admissibility = static post-event power flow converged with all 39 buses in [0.95, 1.05] on C2t_Vsafe_R35_040 and algebraic post-jump voltages in the band",
                                                         "admissible_buses_by_static_flow": sorted(b for b, a in adm_static.items() if a), "inadmissible_buses_by_static_flow": sorted(b for b, a in adm_static.items() if not a),
                                                         "inadmissible_buses_by_post_jump": sorted(b for b, a in adm_jump.items() if not a), "selected_bus": best["bus"] if best else None, "DEC051_selected_bus": int(pred["H3_2"]["bus"]),
                                                         "selection_changes": bool(best is None or best["bus"] != int(pred["H3_2"]["bus"])), "selected_predicted_margin": best["DEC051_predicted_min_margin"] if best else None}
    with (A / "IEEE39_DEC052_H3_voltage_audit.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["state", "bus_of_disturbance", "amplitude_MW", "source", "converged", "vmin_pu", "vmax_pu", "n_buses_above_1.05", "n_buses_below_0.95", "within_original_band_0.95_1.05"])
        w.writerows(rows)
    with (A / "IEEE39_DEC052_H3_location_scan.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["bus", "amplitude_MW", "dP_jump_SG31_pu", "dP_jump_SG35_pu", "DEC051_predicted_min_margin_pu", "DEC051_binding_unit", "static_C2t_vmax", "static_R35_040_vmin", "static_R35_040_vmax", "post_jump_R35_040_vmin", "post_jump_R35_040_vmax", "R35_040_within_band_static", "R35_040_within_band_post_jump"])
        for r in loc:
            w.writerow([r["bus"], r["amplitude_MW"], r["dP_jump_SG31"], r["dP_jump_SG35"], r["DEC051_predicted_min_margin"], r["DEC051_binding_unit"], r["screen_static_C2t"]["vmax"], r["static_R35_040"]["vmin"], r["static_R35_040"]["vmax"],
                        r["post_jump_R35_040"]["vmin"], r["post_jump_R35_040"]["vmax"], r["static_R35_040"]["within_original_band"], r["post_jump_R35_040"]["within_original_band"]])
    # ------------------------------------------------------------------ D3/D4: reserve audit and trajectory re-check
    e8s = np.load(A / "IEEE39_E8_C2t_timeseries.npz")
    lim = {k: e8s[f"P+_unit_{k}"] for k in ("pmax", "pmin", "qmax", "qmin", "smax")}
    cf = jr[CFG]
    pre = np.array(cf["P_pre"]); R = np.array(cf["reserve_P"])
    inc_ref = np.maximum(np.maximum(np.array(cf["observed_fast_increment_over_jump"]), 0), np.maximum(np.array(cf["observed_slow_increment_over_jump"]), 0))
    eps = max(jr[c]["jump_prediction_vs_first_sample_max_abs"] for c in ("C2t", "C2t_Vsafe", "C2t_Vsafe_R35 (0.015)", CFG))
    out["epsilon_DEC051"] = {"value_pu": eps, "definition": "max over the four configurations with a stored series of |algebraic jump - first stored sample| in the 58.564 MW P+ event at bus 4 (jump term only)"}
    rrows, summ = [], {}
    series = {"H3-1": np.load(A / "IEEE39_DEC051_H3_sim1_series.npz"), "H3-2": np.load(A / "IEEE39_DEC051_H3_sim2_series.npz")}
    for tag, s, pr, k in (("H3-1", s1, pred["H3_1"], 1.1), ("H3-2", s2, pred["H3_2"], 1.0)):
        jump = np.array(pr["analytic_jump_pu"])
        used = k * inc_ref
        peak_pred = pre + jump + used
        peak_obs = np.array(s["observed_peak_P_pu"])
        m_pred, m_obs = lim["pmax"] - peak_pred, lim["pmax"] - peak_obs
        first = np.array(s["first_sample_after_event_P_pu"])
        inc_obs = peak_obs - (pre + jump)
        z = series[tag]
        t, P, Q, V = z["time_s"], z["P"], z["Q"], z["bus_voltage_pu"]
        post = t > 5.0 + 1e-9
        sm = lim["smax"] - np.hypot(P, Q)
        for i, n in enumerate(NAMES):
            rrows.append([tag, s["event"], n, lim["pmax"][i], pre[i], R[i], jump[i], first[i], (pre[i] + jump[i]) - first[i], used[i], peak_pred[i], m_pred[i], peak_obs[i], m_obs[i], m_obs[i] - m_pred[i],
                          "conservative" if m_obs[i] >= m_pred[i] else "NON-CONSERVATIVE", inc_obs[i], bool(inc_obs[i] > used[i] + 1e-12), float(Q[post, i].max()), float(lim["qmax"][i] - Q[post, i].max()),
                          float(Q[post, i].min() - lim["qmin"][i]), float(sm[post, i].min())])
        err = m_obs - m_pred
        nc = err < 0
        summ[tag] = {"max_abs_error_all_units_pu": float(np.abs(err).max()), "unit_of_max_abs_error": NAMES[int(np.abs(err).argmax())], "n_units_nonconservative": int(nc.sum()), "nonconservative_units": [NAMES[i] for i in np.where(nc)[0]],
                     "max_nonconservative_error_pu": float(-err.min()) if nc.any() else 0.0, "observed_margin_of_nonconservative_units_pu": {NAMES[i]: float(m_obs[i]) for i in np.where(nc)[0]},
                     "predicted_margin_of_nonconservative_units_pu": {NAMES[i]: float(m_pred[i]) for i in np.where(nc)[0]}, "SG31_SG35_error_pu": [float(err[1]), float(err[3])], "SG31_SG35_observed_margin_pu": [float(m_obs[1]), float(m_obs[3])],
                     "SG31_SG35_predicted_margin_pu": [float(m_pred[1]), float(m_pred[3])], "SG31_SG35_observed_excursion_over_jump_pu": [float(inc_obs[1]), float(inc_obs[3])], "SG31_SG35_empirical_term_used_pu": [float(used[1]), float(used[3])],
                     "units_where_observed_excursion_exceeded_the_empirical_term": [NAMES[i] for i in range(10) if inc_obs[i] > used[i] + 1e-12], "ratio_max_nonconservative_error_over_epsilon": float((-err.min()) / eps) if nc.any() else 0.0,
                     "trajectory_min_margins_pu": {"P_to_pmax": float(m_obs.min()), "P_to_pmin": float((P[post] - lim["pmin"]).min()), "Q_to_qmax": float((lim["qmax"] - Q[post]).min()), "Q_to_qmin": float((Q[post] - lim["qmin"]).min()), "S": float(sm[post].min())},
                     "bus_voltage_pre_event_min_max": [float(V[~post].min()), float(V[~post].max())], "bus_voltage_post_event_min_max": [float(V[post].min()), float(V[post].max())],
                     "bus_of_max_post_event": int(np.unravel_index(np.argmax(V[post]), V[post].shape)[1]) + 1, "n_buses_outside_original_band_whole_run": int(((V < LO) | (V > HI)).any(axis=0).sum()),
                     "series_sha256_local": K.sha(A / f"IEEE39_DEC051_H3_sim{tag[-1]}_series.npz")}
    out["reserve_audit"] = summ
    out["inequality_term_classes"] = {"R_i": "initial reserve, exact (limit minus pre-event physical power)",
                                      "dP_jump": "algebraic: ANDES algebraic solve with continuous differential states; floating point, no validated enclosure; computed on an amplitude grid, monotone on the grid, not proved in the continuum; location dependent",
                                      "dP_exc_fast": "empirical: maximum over (5 s, 5.05 s] in the 58.564 MW event at bus 4, scaled linearly with amplitude; hypothesis untested for other locations", "dP_exc_slow": "empirical: maximum over t > 5.05 s of the same bus-4 run (200 s horizon only)",
                                      "epsilon": "observed discrepancy of the JUMP term only (%.2e pu); it is neither a bound of the excursion terms nor a mathematical bound" % eps, "universal_guarantee": False,
                                      "reason": "two terms depend on empirical maxima from one disturbance location and a 200 s horizon; the bus-18 run exceeds the empirical term at some units when the location changes"}
    with (A / "IEEE39_DEC052_H3_reserve_audit.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["run", "event", "unit", "pmax_pu", "P_pre_pu", "reserve_R_pu", "dP_jump_algebraic_pu", "first_sample_after_event_pu", "jump_minus_first_sample_pu", "empirical_excursion_used_pu", "predicted_peak_pu", "predicted_margin_pu",
                    "observed_peak_pu", "observed_margin_pu", "observed_minus_predicted_margin_pu", "direction", "observed_excursion_over_jump_pu", "empirical_term_exceeded", "Q_peak_post_pu", "margin_to_qmax_pu", "margin_to_qmin_pu", "min_S_margin_pu"])
        w.writerows(rrows)
    K.dump("IEEE39_DEC052_H3_audit.json", out)
    print(json.dumps({"screening": out["screening_plant_defect"], "pre": out["pre_event"], "reselection": out["reselection_original_band_on_R35_040_plant"],
                      "summ": {k: {kk: v[kk] for kk in ("max_abs_error_all_units_pu", "unit_of_max_abs_error", "nonconservative_units", "max_nonconservative_error_pu", "SG31_SG35_error_pu", "units_where_observed_excursion_exceeded_the_empirical_term",
                                                       "bus_voltage_pre_event_min_max", "bus_voltage_post_event_min_max", "n_buses_outside_original_band_whole_run", "trajectory_min_margins_pu")} for k, v in summ.items()}}, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
