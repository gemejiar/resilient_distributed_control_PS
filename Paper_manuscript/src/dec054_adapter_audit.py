"""DEC-054 G2: real-plant audit of the ANDES adapter.  Static only: PFlow + TDS.init (no time stepping, 0 TDS), algebraic jumps and Jacobians on DESIGN buses only.
Writes IEEE39_DEC054_adapter_audit.json and .md exclusively.  Run: <venv python> dec054_adapter_audit.py"""
from __future__ import annotations

import inspect
import json
import time
from pathlib import Path

import numpy as np

import dec054_common as COM
import dec054_opf as OPF
import dec054_plant as PL
import dec054_predictor as PRD

ORIG_ART = Path(r"c:/onedrive/OneDrive - Universidad del Valle/05_Univalle_Investigacion/02_Publicaciones/En_Preparacion/Proyectos_Latex/Resilient_distributed_control_PS/Paper_manuscript/artifacts")
CHECKS: dict = {}


def check(name, ok, **ev):
    CHECKS[name] = {"status": "PASS" if ok else "FAIL", **ev}
    print(f"[{'PASS' if ok else 'FAIL'}] {name}", flush=True)
    return ok


def main():
    gate = COM.backup_gate()
    assert gate["verified"], f"gate: {gate}"
    t_all = time.time()
    P = PL.AndesPlant()
    z0 = P.z_ref.copy()
    system, ctx, rep0 = P._make(z0)
    K = P.K
    spec = PL.variable_spec()
    # ---------------- C01 mapping
    pv_buses = [int(b) for b in system.PV.bus.v]
    ev0 = P.evaluate(z0)
    check("C01_variable_and_unit_mapping",
          spec["n"] == 19 and P.z_ref.shape == (19,) and ctx["unit_bus"] == COM.UNIT_BUS and sorted(pv_buses) == sorted(PL.PV_BUS) and [int(b) for b in system.Slack.bus.v] == [39]
          and sorted(int(b) for b in system.Bus.idx.v) == list(range(1, 40)) and len(system.GENROU.bus.v) == 6 and len(system.REGF1.bus.v) == 4
          and np.allclose(ev0["P"][COM.PV_IDX], z0[:9], atol=1e-9),
          n_vars=spec["n"], names=spec["names"], unit_bus_ctx=ctx["unit_bus"], pv_buses=pv_buses, slack_bus=[int(b) for b in system.Slack.bus.v], n_buses=len(system.Bus.idx.v),
          n_SG=len(system.GENROU.bus.v), n_GFM=len(system.REGF1.bus.v), z_ref=z0.tolist(), P_pre_PV_equals_p0_max_diff=float(np.abs(ev0["P"][COM.PV_IDX] - z0[:9]).max()))
    # ---------------- C02 limits / bases / Slack
    e8 = np.load(ORIG_ART / "IEEE39_E8_C2t_timeseries.npz")
    lim = ctx["lim"]
    diffs = {k: float(np.abs(np.asarray(lim[k]) - e8["P+_unit_" + k]).max()) for k in ("pmax", "pmin", "qmax", "qmin", "smax")}
    sn = np.concatenate([np.asarray(system.GENROU.Sn.v, float), np.asarray(system.REGF1.Sn.v, float)]) / 100.0
    sl = {"pmax": float(system.Slack.pmax.v[0]), "pmin": float(system.Slack.pmin.v[0]), "qmax": float(system.Slack.qmax.v[0]), "qmin": float(system.Slack.qmin.v[0])}
    check("C02_limits_bases_slack", max(diffs.values()) == 0.0 and np.allclose(sn, lim["smax"]) and abs(sl["pmax"] - lim["pmax"][5]) < 1e-12 and abs(sl["qmax"] - lim["qmax"][5]) < 1e-12 and abs(sl["qmin"] - lim["qmin"][5]) < 1e-12,
          max_abs_diff_vs_E8_stored_limits=diffs, base_MVA=100.0, Sn_pu_equals_smax=bool(np.allclose(sn, lim["smax"])), slack_limits=sl, lim_SG39={k: float(lim[k][5]) for k in ("pmax", "pmin", "qmax", "qmin", "smax")})
    # ---------------- C03 initialisation validity (valid and invalid candidates)
    cands = {"z_ref": z0.copy()}
    zA = z0.copy(); zA[3] -= 0.30; zA[7] += 0.30; cands["SG35-0.30_GFM34+0.30"] = zA      # z[3]=p0_SG35, z[7]=p0_GFM34
    zB = z0.copy(); zB[9:] -= 0.01; cands["v0-0.01"] = zB
    zC = z0.copy(); zC[1] -= 0.10; zC[4] += 0.10; cands["SG31-0.10_SG38+0.10"] = zC
    rows, timing = {}, []
    for nm, z in cands.items():
        t = time.time(); e = P.evaluate(z); timing.append(time.time() - t)
        rows[nm] = {"ok": e["ok"], "reason": e.get("reason"), "init_report": e.get("init_report"), "I_vs_executor": e.get("I_vs_executor_max_diff"),
                    "k_ip": float(e["I"]["k_ip"]) if e["ok"] else None, "Vmin": float(e["V"].min()) if e["ok"] else None, "Vmax": float(e["V"].max()) if e["ok"] else None,
                    "P_slack": float(e["P"][5]) if e["ok"] else None, "Q_slack": float(e["Q"][5]) if e["ok"] else None}
    inv = {}
    zi1 = z0.copy(); zi1[1] = lim["pmax"][1] + 0.2; inv["SG31_p0_above_pmax"] = P.evaluate(zi1)
    zi2 = z0.copy(); zi2[9:] = 0.3; inv["v0_all_0.3"] = P.evaluate(zi2)
    check("C03_initialisation_validity", all(r["ok"] for r in rows.values()) and all(not v["ok"] for v in inv.values()) and max(r["init_report"]["residual_g_inf"] for r in rows.values()) <= 1e-8,
          valid_candidates=rows, invalid_candidates={k: {"ok": v["ok"], "reason": v.get("reason"), "detail": str(v.get("init_report") or v.get("error"))[:300]} for k, v in inv.items()},
          seconds_per_evaluate_mean=float(np.mean(timing)))
    # ---------------- C04 I(z) vs executor and vs E8
    k8 = json.load(open(ORIG_ART / "IEEE39_E8_C2t_summary.json"))["controller"]["k_ip_computed"]
    I0 = ev0["I"]
    check("C04_RDC_initialisation_matches_executor",
          all((r["I_vs_executor"] is not None and r["I_vs_executor"] <= 1e-9) for r in rows.values()) and abs(I0["k_ip"] - k8) < 1e-9 and np.allclose(I0["pn"], e8["P+_unit_pn"], atol=1e-9) and np.allclose(I0["qn"], e8["P+_unit_qn"], atol=1e-9)
          and np.array_equal(I0["pset0"], I0["pn"]) and np.array_equal(I0["qset0"], I0["qn"]) and k_ip_varies(rows),
          I_vs_executor_max_diff={k: v["I_vs_executor"] for k, v in rows.items()}, k_ip_zref=float(I0["k_ip"]), k_ip_E8_stored=k8, pn_vs_E8_max_diff=float(np.abs(I0["pn"] - e8["P+_unit_pn"]).max()),
          qn_vs_E8_max_diff=float(np.abs(I0["qn"] - e8["P+_unit_qn"]).max()), gref_p=float(I0["gref_p"]), gref_q=float(I0["gref_q"]), d_p=I0["d_p"].tolist(), d_q=I0["d_q"].tolist(),
          d_q_independent_of_dispatch=bool(np.allclose(P.evaluate(zA)["I"]["d_q"], I0["d_q"])), k_ip_by_candidate={k: v["k_ip"] for k, v in rows.items()})
    # ---------------- C05 balance and Slack
    Pq = {nm: (P.evaluate(z)) for nm, z in cands.items()}
    slack_ok = all(0.0 <= e["P"][5] <= lim["pmax"][5] and lim["qmin"][5] <= e["Q"][5] <= lim["qmax"][5] for e in Pq.values())
    check("C05_AC_balance_and_slack", slack_ok and all(r["init_report"]["residual_g_inf"] <= 1e-8 for r in rows.values()),
          residual_g_inf={k: v["init_report"]["residual_g_inf"] for k, v in rows.items()}, residual_f_inf={k: v["init_report"]["residual_f_inf"] for k, v in rows.items()},
          slack_P_Q={k: (float(e["P"][5]), float(e["Q"][5])) for k, e in Pq.items()}, note="nodal P/Q balance is the algebraic residual g (incl. losses); the Slack closes the active balance")
    # ---------------- C06 + C07 DESIGN-bus jumps, Jacobian regularity, post-jump anchoring
    jrows = []
    ok_j = True
    ok_anchor = True
    ok_d0 = True
    ok_pss = True
    for bus in COM.DESIGN:
        for kind, amp in (("P", 0.58564), ("Q", 0.17345)):
            for frac in (0.5, 1.0):
                sc = OPF.Scenario(f"b{bus}{kind}{frac}", bus, kind, amp * frac)
                j = P.jump(z0, sc)
                A, f, C = P.affine(z0, sc, diag=True)
                d = P.last_affine_diag
                x = PRD.excursion(A, f, C)
                anchor = float(np.abs(d["P_post_jump"] - (ev0["P"] + j["dP"])).max()) if j["ok"] else None
                ok_j &= bool(j["ok"] and j["residual"] <= 1e-9 and d["gy_min_sv_post_jump"] > 1e-6)
                ok_anchor &= bool(anchor is not None and anchor <= 1e-8 and d["inner_converged"])
                ok_d0 &= bool(np.abs(x["D0"]).max() == 0.0 and np.all(x["E_up"] >= 0) and np.all(x["E_dn"] >= 0))
                names = list(system.dae.x_name)
                pss_idx = {v[k] for v in d["ix_pss"].values() for k in ("LL2_x", "WO_x")}
                pss_names = [names[i] for i in d["d_idx_original"] if i in pss_idx]
                ok_pss &= bool(len(pss_names) == 12)
                jrows.append({"scenario": sc.name, "bus": bus, "kind": kind, "amp_pu": sc.amp, "jump_ok": j["ok"], "jump_residual": j.get("residual"), "dP_jump": j["dP"].tolist(), "dQ_jump": j["dQ"].tolist(),
                              "post_jump_anchor_vs_jump_max_diff": anchor, "inner_residual": d["inner_residual"], "gy_min_sv_post_jump": d["gy_min_sv_post_jump"], "gy_cond_post_jump": d["gy_cond_post_jump"],
                              "M_shape": d["M_shape"], "D0_max_abs": float(np.abs(x["D0"]).max()), "E_up": x["E_up"].tolist(), "E_dn": x["E_dn"].tolist(), "t_up_s": x["t_up"].tolist(), "t_dn_s": x["t_dn"].tolist(),
                              "sampling_error_up_max": float(x["sampling_error_up"].max()), "forcing_norm": d["f_norm"], "n_PSS_dynamic_states_in_model": len(pss_names)})
                print("   ", sc.name, "jump", j["ok"], "gy_min_sv", round(d["gy_min_sv_post_jump"], 5), "anchor", anchor, flush=True)
    lin_amp = []
    for bus in COM.DESIGN:
        for kind in ("P", "Q"):
            a = next(r for r in jrows if r["bus"] == bus and r["kind"] == kind and r["amp_pu"] < 0.5 * (0.58564 if kind == "P" else 0.17345) * 1.01)
            b = next(r for r in jrows if r["bus"] == bus and r["kind"] == kind and r["amp_pu"] > 0.9 * (0.58564 if kind == "P" else 0.17345))
            lin_amp.append(float(np.abs(np.array(b["dP_jump"]) - 2 * np.array(a["dP_jump"])).max()))
    check("C06_DESIGN_jumps_and_algebraic_Jacobian", ok_j, buses=COM.DESIGN, scenarios=len(jrows), min_gy_sv=min(r["gy_min_sv_post_jump"] for r in jrows), max_cond=max(r["gy_cond_post_jump"] for r in jrows),
          max_jump_residual=max(r["jump_residual"] for r in jrows), nonlinearity_max_abs_dP_1x_minus_2x_half=float(max(lin_amp)),
          note="only DESIGN buses were used; TUNE/TEST buses were not touched")
    check("C07_post_jump_anchoring_no_double_count", ok_anchor and ok_d0, max_anchor_diff=max(r["post_jump_anchor_vs_jump_max_diff"] for r in jrows), max_D0=max(r["D0_max_abs"] for r in jrows),
          reading="the affine model is built at the post-jump point (x and references continuous, algebraic re-solved); P(xi_0)=pn+jump to <=1e-8 and D(0+)=0 exactly")
    # ---------------- C08 PSS / reduced model structure
    d = P.last_affine_diag
    check("C08_PSS_12_genuine_states_and_reduced_structure", ok_pss and d["n_dyn"] == 208 and d["n_dropped_IEEEST_states"] == 30 and d["n_quasi_algebraic"] == 12 and d["M_shape"] == [228, 228],
          n_dynamic=d["n_dynamic"], n_quasi_algebraic=d["n_quasi_algebraic"], n_dropped_IEEEST_states=d["n_dropped_IEEEST_states"], M_shape=d["M_shape"], n_reference_states=20,
          pss_states_per_SG=2, n_SG=6, genuine_PSS_states=int(len(pss_names)), pss_state_names=pss_names, n_x=d["n_x"], n_y=d["n_y"])
    # ---------------- C09 event / callback order at t = 5 s
    import andes
    from andes.routines.tds import TDS
    src = inspect.getsource(TDS.run)
    i_cp, i_step, i_store, i_sw = src.index("self.callpert(dae.t, system)"), src.index("self.itm_step()"), src.index("dae.store()"), src.index("self.do_switch()")
    code_order = i_cp < i_step < i_store < i_sw
    t = e8["P+_time_s"]
    pre = t < 5.0 - 1e-9
    P_pre = e8["P+_sg_p_pu"][pre][-1]
    dev = np.abs(e8["P+_sg_p_pu"] - P_pre).max(axis=1)
    first_elec = float(t[(t >= 5.0 - 1e-9) & (dev > 1e-6)][0])
    ct = e8["P+_cmd_t"]
    cp = e8["P+_cmd_pset"]
    pre_c = ct < 5.0 - 1e-9
    devc = np.abs(cp - cp[pre_c][-1]).max(axis=1)
    first_cmd = float(ct[(ct >= 5.0 - 1e-9) & (devc > 1e-9)][0])
    around = [float(x) for x in t[(t > 4.995) & (t < 5.012)]]
    h = COM.DT
    first_sample_after = float(t[t > 5.0 + 1e-9][0])
    check("C09_event_callback_algebraic_order_at_t5", code_order and abs(first_sample_after - 5.0001) < 1e-9 and abs(first_elec - 5.0001) < 1e-9 and abs(first_cmd - (5.0001 + h)) < 1e-9,
          andes_version=andes.__version__, code_order_in_TDS_run="callpert(t) -> itm_step() -> store -> do_switch() (events are applied AFTER the step of the event time is solved and stored)",
          stored_times_around_event_s=around, first_post_event_stored_sample_s=first_sample_after, first_sample_with_electrical_change_s=first_elec, first_RDC_reference_change_s=first_cmd,
          reading="ANDES shortens the step around the event (stored times ..., 4.9999, 5.0, 5.0001, then 5.0001+k*2^-8): the algebraic jump is visible at the first stored sample t_e+1e-4 s (proxy of 0+), the RDC references first change at t_e+1e-4+2^-8 s. The RDC callback uses a constant dt=2^-8 s in its Euler update even for the 1e-4 s steps (run_e8_ieee39.py:171-173) and sees the event in its measurements one callback after the jump. These effects are neglected by the continuous-time predictor and are bounded in the G3 audit.")
    # ---------------- C10 horizon
    tg = PRD.time_grid()
    check("C10_horizon_5_to_200s", COM.EVENT_T == 5.0 and COM.T_END == 200.0 and COM.T_POST == 195.0 and abs(tg[-1] - 195.0) < 1e-9 and abs(tg[1] - COM.DT) < 1e-12,
          event_s=COM.EVENT_T, end_s=COM.T_END, post_event_horizon_s=COM.T_POST, grid_last_s=float(tg[-1]), first_step_s=float(tg[1]), grid_points=int(len(tg)))
    tds_used = 0
    out = {"stage": "DEC-054 G2 adapter audit", "gate0": gate["status"], "tds_used": tds_used, "andes_version": andes.__version__, "seconds_total": round(time.time() - t_all, 1), "checks": CHECKS,
           "design_jump_rows": jrows, "overall": "PASS" if all(c["status"] == "PASS" for c in CHECKS.values()) else "FAIL"}
    with open(COM.ART / "IEEE39_DEC054_adapter_audit.json", "x", encoding="utf-8") as f:
        json.dump(out, f, indent=1, default=float)
    md = ["# DEC-054 G2 — Real-plant adapter audit", "", f"Gate 0: `{gate['status']}` (investigator waiver; copy NOT independent). **TDS used: 0.** Static only: PFlow, TDS.init without stepping, algebraic jumps and Jacobians on DESIGN buses `{COM.DESIGN}`.",
          f"**Overall: {out['overall']}** (ANDES {andes.__version__}, {out['seconds_total']} s).", "", "| Check | Status |", "|---|---|"]
    md += [f"| {k} | {v['status']} |" for k, v in CHECKS.items()]
    md += ["", "## Evidence (see the JSON for all numbers)"]
    for k, v in CHECKS.items():
        md += [f"### {k} — {v['status']}", "```", json.dumps({a: b for a, b in v.items() if a != 'status'}, indent=1, default=float)[:3500], "```"]
    with open(COM.ART / "IEEE39_DEC054_adapter_audit.md", "x", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("OVERALL", out["overall"])


def k_ip_varies(rows):
    v = [r["k_ip"] for r in rows.values()]
    return max(v) - min(v) > 1e-6


if __name__ == "__main__":
    main()
