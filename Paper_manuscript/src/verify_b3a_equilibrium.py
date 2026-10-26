"""B3-A equilibrium verification (revision of DEC-037; reads the preserved v1 selection, changes nothing in it).

1. Reference equilibria: pre-event xi_pre (used for S0, d = 0) and post-event xi*(d) (P+, Q+) from the v1 solution.
2. Effective ANDES references: what the real E8 actuator channels need to hold xi* (SG governor reference, SG exciter
   reference, GFM PIplim_y/PIqlim_y), expressed as the RDC setpoints Pset_eff, Qset_eff through the E8 maps; the
   manuscript convention Pset = P*, Qset = Q* is reported alongside, not imposed.
3. Centering: v_RDC at xi_pre and xi*, v_nom = v_RDC - v_RDC(xi*) evaluated at xi* (must vanish), at xi_pre (command at the
   instant xi* is updated) and the offset jump when the reference switches from xi_pre to xi*(d).
4. Frozen-reference dynamic check on C2t with the real E8 actuators: the event load step and the effective references
   applied together at t = 5 s, no RDC; the plant must settle at xi*.  It checks the DAE equilibrium and its reachability
   with the actuators; it is not the B2-B3 comparison.
"""

from __future__ import annotations

import csv
import json
import os

os.environ["C2_VARIANT"] = "C2t"

import numpy as np

import run_e8_ieee39 as e8
import select_equilibrium_b3 as b3
from run_e0_ieee39 import ARTIFACTS_DIR, sha256

V1_JSON = ARTIFACTS_DIR / "IEEE39_B3_C2t_equilibrium_selection.json"
OUT_JSON = ARTIFACTS_DIR / "IEEE39_B3A_C2t_equilibrium_v2.json"
OUT_CSV = ARTIFACTS_DIR / "IEEE39_B3A_C2t_equilibrium_v2.csv"
OUT_CONV = ARTIFACTS_DIR / "IEEE39_B3A_C2t_frozen_reference_convergence.json"
FROZEN_TF_S = 150.0
CONV_TIMES_S = (6, 8, 10, 15, 20, 30, 45, 60, 90, 120, 150)


def frozen_run(name: str, pset_eff: np.ndarray, qset_eff: np.ndarray, lim, vref_gfm: np.ndarray | None = None) -> dict:
    system, ctx = e8.configure(name, e8.TIME_STEP_S)
    system.TDS.config.tf = FROZEN_TF_S
    cap: dict = {}
    n_sg = ctx["n_sg"]

    def cb(t, sys_):
        t = float(t)
        y = sys_.dae.y
        if not cap:
            cap["a_p"] = np.concatenate([np.asarray(sys_.GENROU.Pe.a), np.asarray(sys_.REGF1.Pe.a)])
            cap["a_q"] = np.concatenate([np.asarray(sys_.GENROU.Qe.a), np.asarray(sys_.REGF1.Qe.a)])
            cap["a_y"], cap["a_yq"] = np.asarray(sys_.REGF1.PIplim_y.a), np.asarray(sys_.REGF1.PIqlim_y.a)
            cap["pn"], cap["qn"] = np.asarray(y[cap["a_p"]], float).copy(), np.asarray(y[cap["a_q"]], float).copy()
            cap["y0"], cap["y0q"] = np.asarray(y[cap["a_y"]], float).copy(), np.asarray(y[cap["a_yq"]], float).copy()
            cap["vref0"] = np.asarray(sys_.IEEEX1.vref0.v, float).copy()
            cap["last"] = -1.0
            cap["vref_gfm0"] = np.asarray(sys_.REGF1.vref.v, float).copy()
        if t <= cap["last"]:
            return
        cap["last"] = t
        ps, qs = (pset_eff, qset_eff) if t >= e8.EVENT_TIME_S else (cap["pn"], cap["qn"])
        sys_.TGOV1N.paux0.v[ctx["tg_pos"]] = (ps - cap["pn"])[:n_sg]
        sys_.REGF1.Paux0.v[:] = e8.KC_GFM * (cap["y0"] + (ps - cap["pn"])[n_sg:] - np.asarray(y[cap["a_y"]], float))
        z = np.clip(e8.KAPPA_SG * (qs - cap["qn"])[:n_sg], -e8.Z_CLAMP, e8.Z_CLAMP)
        sys_.IEEEX1.vref0.v[ctx["ex_pos"]] = cap["vref0"][ctx["ex_pos"]] + z
        if vref_gfm is not None:  # extra channel, not used in E8
            sys_.REGF1.vref.v[:] = vref_gfm if t >= e8.EVENT_TIME_S else cap["vref_gfm0"]
        sys_.REGF1.Qaux0.v[:] = e8.KCQ_GFM * (cap["y0q"] + (qs - cap["qn"])[n_sg:] - np.asarray(y[cap["a_yq"]], float))

    system.TDS.callpert = cb
    system.PFlow.run()
    ok = bool(system.TDS.run(no_summary=True))
    t = np.asarray(system.dae.ts.t, float)
    y = np.asarray(system.dae.ts.y)
    p = np.hstack([y[:, system.GENROU.Pe.a], y[:, system.REGF1.Pe.a]])
    q = np.hstack([y[:, system.GENROU.Qe.a], y[:, system.REGF1.Qe.a]])
    bus_idx = list(system.Bus.idx.v)
    v = np.stack([y[:, system.Bus.v.a[bus_idx.index(b)]] for b in lim["unit_bus"]], axis=1)
    f = np.asarray(y[:, system.BusFreq.f.a]).mean(axis=1) * 60.0
    return {"ok": ok, "t_end_s": float(t[-1]), "t": t, "p": p, "q": q, "v": v, "f": f}


def main() -> int:
    v1 = json.loads(V1_JSON.read_text(encoding="utf-8"))
    base = b3.load_plant()
    lim = b3.unit_limits(base)
    unit_bus, n_sg = lim["unit_bus"], len(base.GENROU.bus.v)
    sg, gf = slice(0, n_sg), slice(n_sg, 10)

    ref = b3.load_plant(); ref.PFlow.run(); ref.TDS.config.no_tqdm = 1; ref.TDS.config.tf = 1; ref.TDS.init()
    init_pre = {"init_max_abs_f": float(np.abs(ref.dae.f).max()), "init_max_abs_g": float(np.abs(ref.dae.g).max())}
    pre = b3.andes_state(ref, lim)
    p_pre, q_pre, v_pre = pre["p"], pre["q"], pre["v"]
    flat_pre = b3.validate_dynamic({}, p_pre, v_pre, lim, pre)
    flat_pre.pop("state")

    vref_pre = np.asarray(ref.REGF1.vref.v, float).copy()
    qdrp = np.asarray(ref.REGF1.Qdrp.v, float).copy()
    gp0, gq0 = e8.capability_factors(p_pre, q_pre, lim)
    gref_p, gref_q = gp0.max(), gq0.max()
    k_ip = e8.SPEED_TARGET / float((gp0 / gref_p).sum())
    graph = json.loads(e8.GRAPH_FILE.read_text(encoding="utf-8"))
    pos = {b: i for i, b in enumerate(unit_bus)}
    adjacency = np.zeros((10, 10))
    for u, w in graph["edges"]:
        adjacency[pos[u], pos[w]] = adjacency[pos[w], pos[u]] = graph["weights"]

    def field(pset, qset, p, q, v):
        parts, gp, gq = b3.rdc_field(pset, qset, p, q, v, 1.0, p_pre, q_pre, lim, adjacency, gref_p, gref_q, k_ip)
        return np.concatenate([parts["vP"], parts["vQ"]]), parts, gp, gq

    result: dict = {
        "base": "B3-A: v1 AC selection (DEC-037) with frozen weights; v1 files are preserved unchanged",
        "v1_selection_sha256": sha256(V1_JSON), "frozen_selection_parameters": v1["frozen_selection_parameters"],
        "unit_bus_order": unit_bus, "n_sg": n_sg,
        "pre_event_reference": {"P": p_pre.tolist(), "Q": q_pre.tolist(), "V": v_pre.tolist(), "dynamic_init": init_pre,
                                "flat_run": flat_pre,
                                "SG_pref": pre["sg_pref"].tolist(), "SG_vref": pre["sg_vref"].tolist(),
                                "GFM_PIplim_y": pre["gfm_piplim_y"].tolist(), "GFM_PIqlim_y": pre["gfm_piqlim_y"].tolist()},
        "S0_reference_rule": ("d = 0: the reference is the validated pre-event equilibrium xi_pre (the nominal operating point is "
                              "an admissible equilibrium; the S0 scenario checks that the centered controller leaves it invariant). "
                              "The AC selection is applied only for d != 0, so xi*(d) is discontinuous at d = 0; the AC solution at "
                              "d = 0 (v1 'S0') is kept as evidence only."),
        "information_status": "xi*(d), d != 0 uses the exact disturbance (privileged information), available from the event; xi_pre is known beforehand.",
        "scenarios": {}}
    rows, conv = [], {}
    for name in ("S0", "P+", "Q+"):
        d = v1["scenarios"][name]
        if name == "S0":
            p_s, q_s, v_s = p_pre, q_pre, v_pre
            act = {"sg_pref": pre["sg_pref"], "sg_vref": pre["sg_vref"], "gfm_p": pre["gfm_piplim_y"], "gfm_q": pre["gfm_piqlim_y"]}
            dyn = {"init_max_abs_f": init_pre["init_max_abs_f"], "init_max_abs_g": init_pre["init_max_abs_g"], **{k: v for k, v in flat_pre.items() if k.startswith("flat")}}
        else:
            p_s, q_s, v_s = (np.array(d[k]) for k in ("P_star", "Q_star", "V_star"))
            loads = b3.scenario_loads(e8.SCENARIOS[name])
            dyn = b3.validate_dynamic(loads, p_s, v_s, lim, pre)
            st = dyn.pop("state")
            act = {"sg_pref": st["sg_pref"], "sg_vref": st["sg_vref"], "gfm_p": st["gfm_piplim_y"], "gfm_q": st["gfm_piqlim_y"]}
        # effective references through the E8 actuator maps (do not assume Pset = P, Qset = Q)
        pset_eff, qset_init = p_pre.copy(), q_pre.copy()
        pset_eff[sg] = p_pre[sg] + (act["sg_pref"] - pre["sg_pref"])
        pset_eff[gf] = p_pre[gf] + (act["gfm_p"] - pre["gfm_piplim_y"])
        z_req = act["sg_vref"] - pre["sg_vref"]
        qset_init[sg] = q_pre[sg] + z_req / e8.KAPPA_SG
        qset_init[gf] = q_pre[gf] + (act["gfm_q"] - pre["gfm_piqlim_y"])      # y at the initialization value (needs vref* = V*)
        # E8 realizes the GFM Q only through PIqlim_y and leaves vref at its pre-event value: vref2 = (y - Q) Qdrp + vref
        # and vd = vref2 at steady state, hence y_eff = Q* + (V* - vref_pre)/Qdrp.
        qset_eff = qset_init.copy()
        y_eff = q_s[gf] + (v_s[gf] - vref_pre) / qdrp
        qset_eff[gf] = q_pre[gf] + y_eff - pre["gfm_piqlim_y"]
        gp_eff, gq_eff = e8.capability_factors(pset_eff, qset_eff, lim)
        v_star_field, parts, gp, gq = field(pset_eff, qset_eff, p_s, q_s, v_s)
        v_man_field, parts_man, _, _ = field(p_s.copy(), q_s.copy(), p_s, q_s, v_s)
        v_pre_field, _, _, _ = field(p_pre, q_pre, p_pre, q_pre, v_pre)
        v_nom_at_star = v_star_field - field(pset_eff, qset_eff, p_s, q_s, v_s)[0]
        v_nom_at_pre = v_pre_field - v_star_field
        jump = v_star_field - v_pre_field
        # sanity: v_nom is nonzero away from xi* (half-way point)
        mid = 0.5 * (p_s + p_pre), 0.5 * (q_s + q_pre), 0.5 * (v_s + v_pre)
        v_nom_mid = field(0.5 * (pset_eff + p_pre), 0.5 * (qset_eff + q_pre), *mid)[0] - v_star_field
        entry = {
            "reference_rule": "xi_pre (d = 0)" if name == "S0" else "AC selection xi*(d) (B3-A)",
            "P_star": p_s.tolist(), "Q_star": q_s.tolist(), "V_star": v_s.tolist(),
            "Pset_eff": pset_eff.tolist(), "Qset_eff": qset_eff.tolist(), "Qset_init_required_y": qset_init.tolist(),
            "GFM_vref_pre": vref_pre.tolist(), "GFM_Qdrp": qdrp.tolist(), "GFM_y_eff_E8_channel": y_eff.tolist(), "GFM_vref_star_init": v_s[gf].tolist(), "Pset_manuscript": p_s.tolist(), "Qset_manuscript": q_s.tolist(),
            "actuator_required": {
                "sg_dpref": (act["sg_pref"] - pre["sg_pref"]).tolist(), "sg_dvref": z_req.tolist(),
                "gfm_dPIplim_y": (act["gfm_p"] - pre["gfm_piplim_y"]).tolist(), "gfm_dPIqlim_y": (act["gfm_q"] - pre["gfm_piqlim_y"]).tolist(),
                "sg_dpref_minus_dP": ((act["sg_pref"] - pre["sg_pref"]) - (p_s - p_pre)[sg]).tolist(),
                "sg_vref_clamp_margin": (e8.Z_CLAMP - np.abs(z_req)).tolist()},
            "capacity_margins_at_Pstar_Qstar": {
                "P_to_pmax": (lim["pmax"] - p_s).tolist(), "P_to_pmin": (p_s - lim["pmin"]).tolist(), "Q_to_qmax": (lim["qmax"] - q_s).tolist(),
                "Q_to_qmin": (q_s - lim["qmin"]).tolist(), "S_rel_margin": (1 - np.hypot(p_s, q_s) / lim["smax"]).tolist()},
            "effective_setpoint_in_W": {"gP_raw": gp_eff.tolist(), "gQ_raw": gq_eff.tolist(), "all_positive": bool(np.all(gp_eff > 0) and np.all(gq_eff > 0)),
                                        "P_to_pmax": (lim["pmax"] - pset_eff).tolist(), "Q_to_qmax": (lim["qmax"] - qset_eff).tolist(),
                                        "Q_to_qmin": (qset_eff - lim["qmin"]).tolist()},
            "dynamic_validation": dyn,
            "centering": {
                "v_RDC_at_xi_star_effective_refs_pu_per_s": {"vP": parts["vP"].tolist(), "vQ": parts["vQ"].tolist()},
                "v_RDC_at_xi_star_manuscript_refs_pu_per_s": {"vP": parts_man["vP"].tolist(), "vQ": parts_man["vQ"].tolist()},
                "v_RDC_at_xi_pre_pu_per_s": {"vP": v_pre_field[:10].tolist(), "vQ": v_pre_field[10:].tolist()},
                "max_abs_vP_RDC_at_xi_star_MW_per_s": float(100 * np.abs(v_star_field[:10]).max()),
                "max_abs_vQ_RDC_at_xi_star_MVAr_per_s": float(100 * np.abs(v_star_field[10:]).max()),
                "max_abs_v_nom_at_xi_star": float(np.abs(v_nom_at_star).max()),
                "max_abs_v_nom_at_xi_pre_pu_per_s": {"vP": float(np.abs(v_nom_at_pre[:10]).max()), "vQ": float(np.abs(v_nom_at_pre[10:]).max())},
                "max_abs_v_nom_halfway_pu_per_s": float(np.abs(v_nom_mid).max()),
                "offset_jump_at_update_pu_per_s": {"vP": jump[:10].tolist(), "vQ": jump[10:].tolist()},
                "max_abs_offset_jump_vP_vQ_pu_per_s": [float(np.abs(jump[:10]).max()), float(np.abs(jump[10:]).max())],
                "units": "pu/s on the 100 MVA system base (1 pu/s = 100 MW/s or MVAr/s)"}}
        if name != "S0":
            entry["frozen_reference_check"] = {}
            for tag, kw in (("E8_channels_only", dict(qset=qset_eff, vref=None)),
                            ("E8_channels_plus_GFM_vref", dict(qset=qset_init, vref=v_s[gf]))):
                fr = frozen_run(name, pset_eff, kw["qset"], lim, kw["vref"])
                t = fr["t"]
                idx = [int(np.argmin(np.abs(t - tt))) for tt in CONV_TIMES_S]
                end = slice(int(np.argmin(np.abs(t - (FROZEN_TF_S - 5.0)))), None)
                conv[f"{name}_{tag}"] = {"times_s": list(CONV_TIMES_S),
                          "max_abs_P_error_pu": [float(np.abs(fr["p"][i] - p_s).max()) for i in idx],
                          "max_abs_Q_error_pu": [float(np.abs(fr["q"][i] - q_s).max()) for i in idx],
                          "max_abs_V_error_pu": [float(np.abs(fr["v"][i] - v_s).max()) for i in idx],
                          "frequency_error_hz": [float(fr["f"][i] - 60.0) for i in idx]}
                fc = {
                    "converged": fr["ok"], "t_end_s": fr["t_end_s"],
                    "final_P_error_pu": (fr["p"][end].mean(axis=0) - p_s).tolist(),
                    "final_Q_error_pu": (fr["q"][end].mean(axis=0) - q_s).tolist(),
                    "final_V_error_pu": (fr["v"][end].mean(axis=0) - v_s).tolist(),
                    "final_max_abs_P_error_pu": float(np.abs(fr["p"][end].mean(axis=0) - p_s).max()),
                    "final_max_abs_Q_error_pu": float(np.abs(fr["q"][end].mean(axis=0) - q_s).max()),
                    "final_max_abs_V_error_pu": float(np.abs(fr["v"][end].mean(axis=0) - v_s).max()),
                    "final_frequency_error_hz": float(fr["f"][end].mean() - 60.0),
                    "last_5s_max_abs_drift_P_pu": float(np.abs(fr["p"][end] - fr["p"][end][0]).max()),
                    "transient_p_excess_over_pmax_pu": np.maximum(0.0, fr["p"].max(axis=0) - lim["pmax"]).tolist()}
                entry["frozen_reference_check"][tag] = fc
                print(f"{name} frozen[{tag}]: ok={fc['converged']} dP={fc['final_max_abs_P_error_pu']:.2e} dQ={fc['final_max_abs_Q_error_pu']:.2e} "
                      f"dV={fc['final_max_abs_V_error_pu']:.2e} df={fc['final_frequency_error_hz']:.2e} drift5s={fc['last_5s_max_abs_drift_P_pu']:.1e}", flush=True)
        result["scenarios"][name] = entry
        c = entry["centering"]
        print(f"{name}: v_nom(xi*)={c['max_abs_v_nom_at_xi_star']:.1e} halfway={c['max_abs_v_nom_halfway_pu_per_s']:.3f} "
              f"vRDC* P/Q={np.abs(v_star_field[:10]).max():.4f}/{np.abs(v_star_field[10:]).max():.4f} jump={c['max_abs_offset_jump_vP_vQ_pu_per_s']} "
              f"W_ok={entry['effective_setpoint_in_W']['all_positive']} init_g={dyn['init_max_abs_g']:.1e}", flush=True)
        for i, b in enumerate(unit_bus):
            rows.append({"scenario": name, "unit": ("SG" if i < n_sg else "GFM") + str(b), "P_pre": p_pre[i], "Q_pre": q_pre[i], "V_pre": v_pre[i],
                         "P_star": p_s[i], "Q_star": q_s[i], "V_star": v_s[i], "Pset_eff": pset_eff[i], "Qset_eff": qset_eff[i],
                         "P_to_pmax": lim["pmax"][i] - p_s[i], "Q_to_qmax": lim["qmax"][i] - q_s[i], "Q_to_qmin": q_s[i] - lim["qmin"][i],
                         "S_rel_margin": 1 - np.hypot(p_s[i], q_s[i]) / lim["smax"][i], "vP_RDC_star": v_star_field[i], "vQ_RDC_star": v_star_field[10 + i],
                         "vP_nom_at_pre": v_nom_at_pre[i], "vQ_nom_at_pre": v_nom_at_pre[10 + i]})
    OUT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")
    OUT_CONV.write_text(json.dumps(conv, indent=2), encoding="utf-8")
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
