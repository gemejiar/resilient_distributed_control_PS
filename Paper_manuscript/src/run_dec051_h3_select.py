"""DEC-051 block C5 (no dynamic simulation): a-priori predictions and the analytic choice of the second validation disturbance, fixed BEFORE the two H3 simulations.

Sim H3-1: P+ of 110 % of the nominal event (64.4204 MW at bus 4), B2, C2t_Vsafe_R35_040, 200 s (the Alter-event mechanism of the historical runs).
Sim H3-2 (selection rule, declared; revised once BEFORE any H3 simulation, see below): among the PQ buses other than bus 4 and with an admissible post-event power flow, the load whose P step of 58.564 MW
(nominal size) has the SMALLEST POSITIVE predicted margin (min over the ten units of Pmax - predicted peak, with the prediction rule below) in C2t_Vsafe_R35_040, i.e. the most demanding disturbance that the
preventive inequality still certifies (the boundary of the certified class).  First version of the rule (smallest margin overall) selected bus 31, a 58.6 MW load at the terminal of SG31, whose reserve is 13.9 MW:
a trivially violating event; it is kept in the scan as an analytic prediction of violation (not simulated).  Algebraic solve, differential states continuous.  The disturbance is admissible if the power flow of the post-event loads converges and the
static post-event minimum voltage stays >= 0.95 pu (the upper band is not used: the pre-event case has buses up to 1.07 pu).  Applied with the dist_fn step mechanism (the Alter event of run_e8 is wired to bus 4 only) at t = 5 s.
Prediction rule (declared): predicted peak P_i = dP_i^jump(analytic, amplitude of the run) + k * max(fast increment_i, slow increment_i, 0), with the fast (<= 50 ms) and slow increments OBSERVED in the 58.564 MW P+ run at bus 4
of the same configuration and k = amplitude / 58.564 MW (linear scaling hypothesis, tested by the runs).  Predicted margin_i = Pmax_i - predicted peak_i."""

from __future__ import annotations

import json

import numpy as np

import dec051_core as C
import run_dec051_h3_jump as J
from run_e0_ieee39 import ARTIFACTS_DIR as A, git_commit, sha256

NAMES = J.NAMES
CFG = "C2t_Vsafe_R35_040"


def main() -> int:
    jr = json.loads((A / "IEEE39_DEC051_H3_jump.json").read_text(encoding="utf-8"))["configs"][CFG]
    lim_pmax = None
    system, ctx = J.make(J.CONFIGS[CFG])
    st = C.rdc_state(system, ctx)
    ix = C.index_sets(system)
    cache: dict = {}
    C.apply_params(system, ctx, st, np.concatenate([st["pn"], st["qn"]]))
    C.L.linearize(system, ctx, cache=cache)
    lim = ctx["lim"]
    pre = st["pn"].copy()
    R = lim["pmax"] - pre
    sg31, sg35 = NAMES.index("SG31"), NAMES.index("SG35")
    fast = np.maximum(np.array(jr["observed_fast_increment_over_jump"]), 0.0)
    slow = np.maximum(np.array(jr["observed_slow_increment_over_jump"]), 0.0)
    inc = np.maximum(fast, slow)

    def predict(dP_jump, k):
        peak = pre + dP_jump + k * inc
        return peak, lim["pmax"] - peak

    # H3-1
    j110 = np.array(jr["events"]["P+"]["1.1"]["dP_jump"])
    pk1, mg1 = predict(j110, 1.1)
    pred1 = {"event": "P+ 110 % at bus 4", "amplitude_MW": 64.4204, "predicted_peak_P_pu": pk1.tolist(), "predicted_margin_to_pmax_pu": mg1.tolist(), "predicted_violating_units": [NAMES[i] for i in np.where(mg1 < 0)[0]],
             "analytic_jump_pu": j110.tolist(), "reserve_pre_pu": R.tolist()}
    # H3-2: scan all PQ buses except 4
    buses = [int(b) for b in system.PQ.bus.v]
    scan = []
    for bus in buses:
        if bus == 4:
            continue
        j = J.jump(system, ctx, st, ix, cache, bus, 0.58564, 0.0)
        dP = j["P"] - pre
        peak_b, marg_b = predict(dP, 1.0)
        scan.append({"bus": bus, "predicted_min_margin_all_units": float(marg_b.min()), "predicted_binding_unit": NAMES[int(np.argmin(marg_b))], "predicted_violating_units": [NAMES[i] for i in np.where(marg_b < 0)[0]], "dP_jump_SG31": float(dP[sg31]), "dP_jump_SG35": float(dP[sg35]), "post_jump_margin_SG31": float(R[sg31] - dP[sg31]), "post_jump_margin_SG35": float(R[sg35] - dP[sg35]),
                     "min_post_jump_margin": float(min(R[sg31] - dP[sg31], R[sg35] - dP[sg35])), "solve_converged": bool(j["converged"]), "bus_voltage_min_max_static_post_jump": [float(j["Vbus"].min()), float(j["Vbus"].max())]})
    scan.sort(key=lambda r: r["predicted_min_margin_all_units"])
    # admissibility: power flow with the post-event loads converges and voltages in band
    import select_equilibrium_b3 as b3
    chosen = None
    for r in scan:
        s = b3.load_plant({r["bus"]: (0.58564, 0.0)})
        ok = bool(s.PFlow.run())
        vb = np.asarray(s.Bus.v.v, float)
        r["post_event_power_flow_converged"], r["post_event_static_voltage_min_max"] = ok, [float(vb.min()), float(vb.max())]
        if ok and vb.min() >= 0.95 and r["predicted_min_margin_all_units"] > 0 and chosen is None and r["predicted_min_margin_all_units"] == min(q["predicted_min_margin_all_units"] for q in scan if q["predicted_min_margin_all_units"] > 0):   # upper bound not used: the pre-event case already has buses above 1.05 pu (known since DEC-039)
            chosen = r
    j2 = J.jump(system, ctx, st, ix, cache, chosen["bus"], 0.58564, 0.0)
    pk2, mg2 = predict(j2["P"] - pre, 1.0)
    pred2 = {"event": f"P+ 58.564 MW at bus {chosen['bus']} (dist_fn step at 5 s)", "bus": chosen["bus"], "amplitude_MW": 58.564, "predicted_peak_P_pu": pk2.tolist(), "predicted_margin_to_pmax_pu": mg2.tolist(),
             "predicted_violating_units": [NAMES[i] for i in np.where(mg2 < 0)[0]], "analytic_jump_pu": (j2["P"] - pre).tolist(), "selection_scan_sorted_worst_first": scan, "n_buses_scanned": len(scan)}
    out = {"stage": "DEC-051 C5 predictions (written before the simulations)", "git_commit": git_commit(), "doc": __doc__, "configuration": CFG, "increments_used": {"fast": fast.tolist(), "slow": slow.tolist()}, "H3_1": pred1, "H3_2": pred2,
           "inputs_sha256": {"IEEE39_DEC051_H3_jump.json": sha256(A / "IEEE39_DEC051_H3_jump.json")}}
    (A / "IEEE39_DEC051_H3_predictions.json").write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
    print("H3-1 predicted margins SG31/SG35:", round(mg1[sg31], 4), round(mg1[sg35], 4), pred1["predicted_violating_units"])
    print("H3-2 bus", chosen["bus"], "predicted margins SG31/SG35:", round(mg2[sg31], 4), round(mg2[sg35], 4), pred2["predicted_violating_units"], "min all", round(float(mg2.min()), 4), "| scan:", [(r["bus"], round(r["predicted_min_margin_all_units"], 4), r["predicted_binding_unit"]) for r in scan[:8]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
