"""B3 step 1: reference equilibrium xi*(d) for the centered RDC (Eqs. eq:centered, eq:eqselection).

Static AC problem on plant C2t, no dynamic simulation of the controller:

    min  sum_i [ ((P_i-P_i^pre)/R_P,i)^2 + ((Q_i-Q_i^pre)/R_Q,i)^2 + ((V_i-V_REF)/DV)^2 ]   (units i = 10 SG/GFM)
    s.t. AC power balance at the 39 buses (constant-power loads of the scenario, omega = 1, losses included),
         P/Q box limits of the case plant data and S <= Sn/100, each tightened by EPS of its range,
         0.95 <= V_bus <= 1.05 at all 39 buses.

The weights are frozen below before any comparison.  The pre-event reference (P^pre, Q^pre) is the C2t power flow
without disturbance; the post-event equilibrium uses the exact disturbance d (privileged information, DEC-037).
The result is validated with ANDES: power flow, dynamic initialization, DAE residuals, a flat run, the actuator
references the initialization requires, and the original RDC field evaluated at xi*.
"""

from __future__ import annotations

import csv
import json
import os

os.environ["C2_VARIANT"] = "C2t"

import andes
import numpy as np
import scipy.sparse as sp
from scipy.optimize import minimize

import run_e7_ieee39 as e7
import run_e8_ieee39 as e8
from run_e0_ieee39 import ARTIFACTS_DIR, PROJECT_ROOT, sha256
from variant import CASE_FILE

CASE = PROJECT_ROOT / "Paper_manuscript" / "cases" / CASE_FILE
OUT_JSON = ARTIFACTS_DIR / "IEEE39_B3_C2t_equilibrium_selection.json"
OUT_CSV = ARTIFACTS_DIR / "IEEE39_B3_C2t_equilibrium_selection.csv"
BASE_MVA = 100.0
# Frozen selection parameters (DEC-037): unit weights 1 on dimensionless terms.
W_P, W_Q, W_V = 1.0, 1.0, 1.0
DV_SCALE = 0.05           # pu: half-width of the bus-voltage band; 0.02 acted as an equality in a first trial (DEC-037)
V_REF = 1.0               # reference, not an equality
V_MIN_BUS, V_MAX_BUS = 0.95, 1.05
EPS = 0.01                # fraction of each capability range kept as interior margin
EPS_S = 0.01              # relative margin on the apparent-power disc
FLAT_RUN_S = 20.0


def load_plant(loads: dict[int, tuple[float, float]] | None = None, p_star=None, v_star=None, unit_bus=None) -> andes.System:
    s = andes.load(str(CASE), setup=False, default_config=True, no_output=True)
    s.PQ.config.p2p, s.PQ.config.p2i, s.PQ.config.p2z = 1.0, 0.0, 0.0
    s.PQ.config.q2q, s.PQ.config.q2i, s.PQ.config.q2z = 1.0, 0.0, 0.0
    s.setup()
    for bus, (dp, dq) in (loads or {}).items():
        k = [int(b) for b in s.PQ.bus.v].index(bus)
        s.PQ.p0.v[k] += dp
        s.PQ.q0.v[k] += dq
    if p_star is not None:
        pos = {b: i for i, b in enumerate(unit_bus)}
        for model in ("PV", "Slack"):
            d = getattr(s, model)
            for k, b in enumerate(d.bus.v):
                d.v0.v[k] = v_star[pos[int(b)]]
                if model == "PV":
                    d.p0.v[k] = p_star[pos[int(b)]]
    return s


def scenario_loads(spec: dict[str, float]) -> dict[int, tuple[float, float]]:
    out: dict[int, tuple[float, float]] = {}
    if "p_mw" in spec:
        out[4] = (spec["p_mw"] / BASE_MVA, 0.0)
    if "q_mvar" in spec:
        out[21] = (0.0, spec["q_mvar"] / BASE_MVA)
    return out


def network(s: andes.System):
    ybus = s.build_ybus()
    y = sp.coo_matrix((list(ybus.V), (list(ybus.I), list(ybus.J))), shape=ybus.size).toarray()
    bus = [int(b) for b in s.Bus.idx.v]
    pl, ql = np.zeros(len(bus)), np.zeros(len(bus))
    for b, p, q in zip(s.PQ.bus.v, s.PQ.p0.v, s.PQ.q0.v):
        pl[bus.index(int(b))] += p
        ql[bus.index(int(b))] += q
    return y, bus, pl, ql


def unit_limits(s: andes.System) -> dict[str, np.ndarray]:
    case_lim = e7.static_limits(s)
    unit_bus = [int(b) for b in s.GENROU.bus.v] + [int(b) for b in s.REGF1.bus.v]
    sn = np.concatenate([np.asarray(s.GENROU.Sn.v, float), np.asarray(s.REGF1.Sn.v, float)]) / BASE_MVA
    return {"unit_bus": unit_bus, "pmax": np.array([case_lim[b]["pmax"] for b in unit_bus]), "pmin": np.zeros(len(unit_bus)),
            "qmax": np.array([case_lim[b]["qmax"] for b in unit_bus]), "qmin": np.array([case_lim[b]["qmin"] for b in unit_bus]),
            "smax": sn, "is_sg": np.arange(len(unit_bus)) < len(s.GENROU.bus.v)}


def solve(y, bus, pl, ql, lim, p_pre, q_pre, start_v, start_a, slack_pos, slack_angle):
    n = len(bus)
    u_pos = np.array([bus.index(b) for b in lim["unit_bus"]])
    other = np.array([i for i in range(n) if i not in set(u_pos)])
    free = np.array([i for i in range(n) if i != slack_pos])
    rp, rq = lim["pmax"] - lim["pmin"], lim["qmax"] - lim["qmin"]

    def unpack(x):
        v = x[:n]
        a = np.zeros(n)
        a[free] = x[n:]
        a[slack_pos] = slack_angle
        return v, a

    def injections(x):
        v, a = unpack(x)
        vc = v * np.exp(1j * a)
        i_bus = y @ vc
        return v, a, vc, i_bus, vc * np.conj(i_bus)

    def ds_dx(x):
        """Complex jacobian of the bus injections w.r.t. [V (n), theta (free)] (MATPOWER form)."""
        v, a, vc, i_bus, _ = injections(x)
        dv = np.diag(vc / v)
        dsa = 1j * np.diag(vc) @ np.conj(np.diag(i_bus) - y @ np.diag(vc))
        dsm = np.diag(vc) @ np.conj(y @ dv) + np.diag(np.conj(i_bus)) @ dv
        return np.hstack([dsm, dsa[:, free]])

    def unit_pq(x):
        v, a, vc, i_bus, s_inj = injections(x)
        return s_inj.real[u_pos] + pl[u_pos], s_inj.imag[u_pos] + ql[u_pos], v

    def terms(x):
        p, q, v = unit_pq(x)
        return (W_P * np.sum(((p - p_pre) / rp) ** 2), W_Q * np.sum(((q - q_pre) / rq) ** 2),
                W_V * np.sum(((v[u_pos] - V_REF) / DV_SCALE) ** 2))

    nx = n + len(free)

    def grad(x):
        p, q, v = unit_pq(x)
        d = ds_dx(x)
        g = 2 * W_P * ((p - p_pre) / rp ** 2) @ d.real[u_pos] + 2 * W_Q * ((q - q_pre) / rq ** 2) @ d.imag[u_pos]
        gv = np.zeros(nx)
        gv[u_pos] = 2 * W_V * (v[u_pos] - V_REF) / DV_SCALE ** 2
        return g + gv

    def eq(x):
        v, a, vc, i_bus, s_inj = injections(x)
        return np.concatenate([s_inj.real[other] + pl[other], s_inj.imag[other] + ql[other]])

    def eq_jac(x):
        d = ds_dx(x)
        return np.vstack([d.real[other], d.imag[other]])

    def ineq(x):
        p, q, v = unit_pq(x)
        return np.concatenate([
            lim["pmax"] - EPS * rp - p, p - lim["pmin"] - EPS * rp, lim["qmax"] - EPS * rq - q, q - lim["qmin"] - EPS * rq,
            ((1 - EPS_S) * lim["smax"]) ** 2 - p ** 2 - q ** 2, v - V_MIN_BUS, V_MAX_BUS - v])

    def ineq_jac(x):
        p, q, v = unit_pq(x)
        d = ds_dx(x)
        dp, dq = d.real[u_pos], d.imag[u_pos]
        eye_v = np.zeros((n, nx))
        eye_v[np.arange(n), np.arange(n)] = 1.0
        return np.vstack([-dp, dp, -dq, dq, -2 * p[:, None] * dp - 2 * q[:, None] * dq, eye_v, -eye_v])

    x0 = np.concatenate([start_v, start_a[free]])
    res = minimize(lambda x: sum(terms(x)), x0, jac=grad, method="SLSQP",
                   constraints=[{"type": "eq", "fun": eq, "jac": eq_jac}, {"type": "ineq", "fun": ineq, "jac": ineq_jac}],
                   options={"maxiter": 500, "ftol": 1e-12})
    p, q, v = unit_pq(res.x)
    vb, ab = unpack(res.x)
    ineq_names = ([f"P<=pmax-eps@{b}" for b in lim["unit_bus"]] + [f"P>=pmin+eps@{b}" for b in lim["unit_bus"]]
                  + [f"Q<=qmax-eps@{b}" for b in lim["unit_bus"]] + [f"Q>=qmin+eps@{b}" for b in lim["unit_bus"]]
                  + [f"S<=Sn@{b}" for b in lim["unit_bus"]] + [f"V>=Vmin@{b}" for b in bus] + [f"V<=Vmax@{b}" for b in bus])
    g = ineq(res.x)
    return {"success": bool(res.success), "message": str(res.message), "iterations": int(res.nit),
            "p": p, "q": q, "v_bus": vb, "a_bus": ab, "v_unit": v[u_pos], "eq_residual_max": float(np.abs(eq(res.x)).max()),
            "ineq_min": float(g.min()), "active_constraints": [n for n, gi in zip(ineq_names, g) if gi < 1e-6],
            "objective_terms": dict(zip(("P_redispatch", "Q_redispatch", "V_regulation"), map(float, terms(res.x))))}


def rdc_field(pset, qset, p, q, v, omega, pn, qn, lim, adjacency, gref_p, gref_q, k_ip):
    """Original RDC (E8 law, Eqs. 26--35) evaluated at a point; same constants and normalization as run_e8."""
    gp_raw, gq_raw = e8.capability_factors(pset, qset, lim)
    gp, gq = gp_raw / gref_p, gq_raw / gref_q
    xp, xq = p / pn, q / (lim["qmax"] - lim["qmin"])
    lp = gp * (adjacency * gp[None, :] * (xp[:, None] - xp[None, :])).sum(axis=1)
    lq = gq * (adjacency * gq[None, :] * (xq[:, None] - xq[None, :])).sum(axis=1)
    parts = {"vP_frequency": k_ip * gp * (1.0 - omega), "vP_consensus": -k_ip * e8.K_P * lp, "vP_leak": -e8.K_LEAK * (pset - pn),
             "vQ_voltage": e8.K_IQ * e8.K_V * gq * (e8.V_REF - v), "vQ_consensus": -e8.K_IQ * e8.K_Q * lq,
             "vQ_leak": -e8.K_LEAK * (qset - qn)}
    parts["vP"] = parts["vP_frequency"] + parts["vP_consensus"] + parts["vP_leak"]
    parts["vQ"] = parts["vQ_voltage"] + parts["vQ_consensus"] + parts["vQ_leak"]
    return parts, gp, gq


def andes_state(s: andes.System, lim) -> dict[str, np.ndarray]:
    y = s.dae.y
    p = np.concatenate([np.asarray(y[s.GENROU.Pe.a], float), np.asarray(y[s.REGF1.Pe.a], float)])
    q = np.concatenate([np.asarray(y[s.GENROU.Qe.a], float), np.asarray(y[s.REGF1.Qe.a], float)])
    bus_idx = list(s.Bus.idx.v)
    v = np.array([float(y[s.Bus.v.a][bus_idx.index(b)]) for b in lim["unit_bus"]])
    tg = [list(s.TGOV1N.syn.v).index(g) for g in s.GENROU.idx.v]
    ex = [list(s.IEEEX1.syn.v).index(g) for g in s.GENROU.idx.v]
    act = {"sg_pref": np.asarray(s.TGOV1N.pref.v, float)[tg], "sg_vref": np.asarray(s.IEEEX1.vref.v, float)[ex],
           "gfm_piplim_y": np.asarray(y[s.REGF1.PIplim_y.a], float), "gfm_piqlim_y": np.asarray(y[s.REGF1.PIqlim_y.a], float)}
    return {"p": p, "q": q, "v": v, **act}


def validate_dynamic(loads, p_star, v_star, lim, ref_state) -> dict:
    s = load_plant(loads, p_star, v_star, lim["unit_bus"])
    ok = bool(s.PFlow.run())
    out: dict = {"pflow_ok": ok, "pflow_residual": float(np.abs(s.dae.g).max())}
    bus_idx = list(s.Bus.idx.v)
    s.TDS.config.tf, s.TDS.config.tstep, s.TDS.config.fixt, s.TDS.config.no_tqdm = FLAT_RUN_S, 0.00390625, 1, 1
    s.TDS.init()
    out["init_max_abs_f"], out["init_max_abs_g"] = float(np.abs(s.dae.f).max()), float(np.abs(s.dae.g).max())
    state0 = andes_state(s, lim)
    s = load_plant(loads, p_star, v_star, lim["unit_bus"])  # fresh system: the flat run is a separate TDS run
    s.PFlow.run()
    s.TDS.config.tf, s.TDS.config.tstep, s.TDS.config.fixt, s.TDS.config.no_tqdm = FLAT_RUN_S, 0.00390625, 1, 1
    t_ok = bool(s.TDS.run(no_summary=True))
    y = s.dae.ts.y
    f = np.asarray(y[:, s.BusFreq.f.a]) * 60.0
    out.update({"flat_run_converged": t_ok, "flat_steps": int(y.shape[0]), "flat_t_end_s": float(s.dae.ts.t[-1]),
                "flat_max_abs_frequency_drift_hz": float(np.abs(f - 60.0).max()),
                "flat_max_abs_voltage_drift_pu": float(np.abs(y[:, s.Bus.v.a] - y[0, s.Bus.v.a]).max()),
                "flat_max_abs_dynamic_state_drift": float(np.abs(np.asarray(s.dae.ts.x) - np.asarray(s.dae.ts.x)[0]).max()),
                "flat_max_abs_unit_p_drift_pu": float(np.abs(y[:, s.GENROU.Pe.a] - y[0, s.GENROU.Pe.a]).max()),
                "pflow_max_abs_voltage_dev_vs_selection": None})
    out["state"] = state0
    return out


def main() -> int:
    base = load_plant()
    lim = unit_limits(base)
    unit_bus = lim["unit_bus"]
    n_sg = len(base.GENROU.bus.v)
    y, bus, pl0, ql0 = network(base)
    slack_bus = int(base.Slack.bus.v[0])
    slack_pos, slack_angle = bus.index(slack_bus), float(base.Slack.a0.v[0])

    ref_sys = load_plant()
    ref_sys.PFlow.run(); ref_sys.TDS.config.no_tqdm = 1; ref_sys.TDS.config.tf = 1; ref_sys.TDS.init()
    pre = andes_state(ref_sys, lim)
    p_pre, q_pre, v_pre = pre["p"], pre["q"], pre["v"]
    # RDC constants exactly as run_e8 (a-priori, nominal setpoint at the pre-event dispatch)
    gp0, gq0 = e8.capability_factors(p_pre, q_pre, lim)
    gref_p, gref_q = gp0.max(), gq0.max()
    k_ip = e8.SPEED_TARGET / float((gp0 / gref_p).sum())
    graph = json.loads(e8.GRAPH_FILE.read_text(encoding="utf-8"))
    pos = {b: i for i, b in enumerate(unit_bus)}
    adjacency = np.zeros((10, 10))
    for u, v in graph["edges"]:
        adjacency[pos[u], pos[v]] = adjacency[pos[v], pos[u]] = graph["weights"]
    raw8 = np.load(e8.RAW_FILE)

    result: dict = {
        "plant": "C2t", "case_sha256": sha256(CASE),
        "frozen_selection_parameters": {"W_P": W_P, "W_Q": W_Q, "W_V": W_V, "DV_SCALE_pu": DV_SCALE, "V_REF_pu": V_REF,
                                        "V_BUS_BOUNDS_pu": [V_MIN_BUS, V_MAX_BUS], "EPS_range_fraction": EPS, "EPS_S": EPS_S,
                                        "P_range": "pmax - pmin of the case static generator, pmin = 0",
                                        "Q_range": "qmax - qmin of the case static generator"},
        "unit_bus_order": unit_bus, "n_sg": n_sg,
        "pre_event_reference": {"definition": "C2t power flow and dynamic initialization without disturbance (xi_pre)",
                                "P": p_pre.tolist(), "Q": q_pre.tolist(), "V": v_pre.tolist()},
        "information_status": ("xi*(d) uses the exact disturbance d: privileged information. It is not available before the event "
                               "(t_event = 5 s); the pre-event reference above is the only equilibrium known beforehand."),
        "scenarios": {}}
    rows = []
    for name, spec in e8.SCENARIOS.items():
        loads = scenario_loads(spec)
        s_sc = load_plant(loads)
        s_sc.PFlow.run()
        y_sc, bus_sc, pl, ql = network(s_sc)
        sol = solve(y_sc, bus_sc, pl, ql, lim, p_pre, q_pre, np.asarray(s_sc.Bus.v.v, float), np.asarray(s_sc.Bus.a.v, float),
                    slack_pos, slack_angle)
        dyn = validate_dynamic(loads, sol["p"], sol["v_unit"], lim, pre)
        st = dyn.pop("state")
        bus_idx = list(s_sc.Bus.idx.v)
        v_andes_all = None
        chk = load_plant(loads, sol["p"], sol["v_unit"], unit_bus); chk.PFlow.run()
        dyn["pflow_max_abs_voltage_dev_vs_selection"] = float(np.abs(np.asarray(chk.Bus.v.v) - sol["v_bus"]).max())
        dyn["pflow_max_abs_angle_dev_vs_selection_rad"] = float(np.abs(np.asarray(chk.Bus.a.v) - sol["a_bus"]).max())
        dyn["init_unit_P_dev_vs_selection_pu"] = float(np.abs(st["p"] - sol["p"]).max())
        dyn["init_unit_Q_dev_vs_selection_pu"] = float(np.abs(st["q"] - sol["q"]).max())
        # Pset*, Qset*: omega = 1 convention, Pset = P, Qset = Q at the equilibrium (manuscript variables)
        pset, qset = sol["p"].copy(), sol["q"].copy()
        field, gp, gq = rdc_field(pset, qset, sol["p"], sol["q"], sol["v_unit"], 1.0, p_pre, q_pre, lim, adjacency, gref_p, gref_q, k_ip)
        field_pre, _, _ = rdc_field(p_pre, q_pre, p_pre, q_pre, v_pre, 1.0, p_pre, q_pre, lim, adjacency, gref_p, gref_q, k_ip)
        cmd_t, cmd_p, cmd_q = raw8[f"{name}_cmd_t"], raw8[f"{name}_cmd_pset"], raw8[f"{name}_cmd_qset"]
        dt = np.diff(cmd_t)
        rate_p = np.abs(np.diff(cmd_p, axis=0) / dt[:, None])[cmd_t[1:] >= 5.0].max(axis=0)
        rate_q = np.abs(np.diff(cmd_q, axis=0) / dt[:, None])[cmd_t[1:] >= 5.0].max(axis=0)
        sg, gf = slice(0, n_sg), slice(n_sg, 10)
        ref_act = pre
        actuator = {
            "dP_star": (sol["p"] - p_pre).tolist(), "dQ_star": (sol["q"] - q_pre).tolist(),
            "sg_dpref_required": (st["sg_pref"] - ref_act["sg_pref"]).tolist(),
            "sg_dvref_required": (st["sg_vref"] - ref_act["sg_vref"]).tolist(),
            "sg_dvref_E8_map_kappa_dQ": (e8.KAPPA_SG * (qset - q_pre)[sg]).tolist(),
            "gfm_dPIplim_y_required": (st["gfm_piplim_y"] - ref_act["gfm_piplim_y"]).tolist(),
            "gfm_dPIqlim_y_required": (st["gfm_piqlim_y"] - ref_act["gfm_piqlim_y"]).tolist()}
        actuator["max_abs_sg_dpref_minus_dP_pu"] = float(np.abs(np.array(actuator["sg_dpref_required"]) - np.array(actuator["dP_star"])[sg]).max())
        actuator["max_abs_gfm_dPIplim_minus_dP_pu"] = float(np.abs(np.array(actuator["gfm_dPIplim_y_required"]) - np.array(actuator["dP_star"])[gf]).max())
        actuator["max_abs_gfm_dPIqlim_minus_dQ_pu"] = float(np.abs(np.array(actuator["gfm_dPIqlim_y_required"]) - np.array(actuator["dQ_star"])[gf]).max())
        actuator["max_abs_sg_dvref_required_minus_E8_map"] = float(np.abs(np.array(actuator["sg_dvref_required"]) - np.array(actuator["sg_dvref_E8_map_kappa_dQ"])).max())
        info_e8 = {}
        data8 = {k[len(name) + 1:]: raw8[k] for k in raw8.files if k.startswith(name + "_")}
        p8, q8, v8 = e7.unit_series(None, data8)
        info_e8 = {"E8_final_P": p8[-1].tolist(), "E8_final_Q": q8[-1].tolist(), "E8_final_V": v8[-1].tolist(),
                   "E8_final_qset": cmd_q[-1].tolist(),
                   "max_abs_P_star_minus_E8_final_pu": float(np.abs(sol["p"] - p8[-1]).max()),
                   "max_abs_Q_star_minus_E8_final_pu": float(np.abs(sol["q"] - q8[-1]).max()),
                   "max_abs_V_star_minus_E8_final_pu": float(np.abs(sol["v_unit"] - v8[-1]).max())}
        margins = {"P_to_pmax": (lim["pmax"] - pset).tolist(), "P_to_pmin": (pset - lim["pmin"]).tolist(),
                   "Q_to_qmax": (lim["qmax"] - qset).tolist(), "Q_to_qmin": (qset - lim["qmin"]).tolist(),
                   "S_rel_margin": (1 - np.hypot(pset, qset) / lim["smax"]).tolist(), "gP_normalized": gp.tolist(),
                   "gQ_normalized": gq.tolist()}
        result["scenarios"][name] = {
            "disturbance": spec, "optimizer": {k: v for k, v in sol.items() if k not in ("p", "q", "v_bus", "a_bus", "v_unit")},
            "P_star": sol["p"].tolist(), "Q_star": sol["q"].tolist(), "V_star": sol["v_unit"].tolist(),
            "Pset_star": pset.tolist(), "Qset_star": qset.tolist(), "capacity_margins": margins,
            "all_bus_voltage_min_max": [float(sol["v_bus"].min()), float(sol["v_bus"].max())],
            "dynamic_validation": dyn, "actuator_consistency": actuator,
            "v_RDC_at_xi_star": {k: val.tolist() for k, val in field.items()},
            "v_RDC_at_pre_event_xi": {k: val.tolist() for k, val in field_pre.items()},
            "v_RDC_norms": {"max_abs_vP_star": float(np.abs(field["vP"]).max()), "max_abs_vQ_star": float(np.abs(field["vQ"]).max()),
                            "E8_max_abs_dPset_dt_after_event": rate_p.tolist(), "E8_max_abs_dQset_dt_after_event": rate_q.tolist(),
                            "ratio_vP_star_to_E8_peak_rate": float(np.abs(field["vP"]).max() / rate_p.max()),
                            "ratio_vQ_star_to_E8_peak_rate": float(np.abs(field["vQ"]).max() / rate_q.max())},
            "information_E8_trajectory_not_used_as_reference": info_e8}
        for i, b in enumerate(unit_bus):
            rows.append({"scenario": name, "unit": ("SG" if i < n_sg else "GFM") + str(b), "bus": b,
                         "P_pre": p_pre[i], "P_star": sol["p"][i], "Q_pre": q_pre[i], "Q_star": sol["q"][i], "V_star": sol["v_unit"][i],
                         "Pset_star": pset[i], "Qset_star": qset[i], "P_to_pmax": margins["P_to_pmax"][i],
                         "Q_to_qmax": margins["Q_to_qmax"][i], "Q_to_qmin": margins["Q_to_qmin"][i],
                         "S_rel_margin": margins["S_rel_margin"][i], "vP_RDC_star": field["vP"][i], "vQ_RDC_star": field["vQ"][i]})
        print(f"{name}: success={sol['success']} eq_res={sol['eq_residual_max']:.2e} ineq_min={sol['ineq_min']:.2e} "
              f"init_g={dyn['init_max_abs_g']:.1e} flat_df={dyn['flat_max_abs_frequency_drift_hz']:.2e}Hz "
              f"flat_dV={dyn['flat_max_abs_voltage_drift_pu']:.2e} Vbus=[{sol['v_bus'].min():.4f},{sol['v_bus'].max():.4f}]")
    OUT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
