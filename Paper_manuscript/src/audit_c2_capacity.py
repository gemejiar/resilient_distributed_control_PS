"""C2 capacity and dispatch audit (pre-E7).

Read only on the frozen C2 case and on the recorded E5/E6 time series.  The unit
capability is taken from the case's own plant data (static generator ``pmax``,
``qmin``, ``qmax``) intersected with the apparent-power rating
``S_i <= Sn_i/100``; REGF1's internal ``Pmax = Qmax = Sn/100`` is reported for
contrast because it is looser than the case data.  Three parts:

1. static dispatch at the PFlow solution (P, Q, S, headroom per unit);
2. steady-state feasibility of holding all ten unit buses at 1.0 pu
   (PFlow with static-generator voltage setpoints set to 1.0, with and without
   the +1 % P / +1 % Q events);
3. dynamic envelope of P, Q, S per unit in the recorded E5 and E6 runs.
"""

from __future__ import annotations

import json

import andes
import numpy as np

from run_e0_ieee39 import ARTIFACTS_DIR, PROJECT_ROOT, sha256

from variant import CASE_FILE, VARIANT  # noqa: E402

CASE = PROJECT_ROOT / "Paper_manuscript" / "cases" / CASE_FILE
OUT = ARTIFACTS_DIR / f"IEEE39_{VARIANT}_capacity_audit.json"
BASE_MVA = 100.0
EVENT_P_PU, EVENT_Q_PU = 0.58564, 0.17345
TOL = 1e-6


def load(voltage_target: float | None, dq: float = 0.0, dp: float = 0.0) -> andes.System:
    s = andes.load(str(CASE), setup=False, default_config=True, no_output=True)
    s.PQ.config.p2p, s.PQ.config.p2i, s.PQ.config.p2z = 1.0, 0.0, 0.0
    s.PQ.config.q2q, s.PQ.config.q2i, s.PQ.config.q2z = 1.0, 0.0, 0.0
    s.setup()
    if voltage_target is not None:
        for model in ("PV", "Slack"):
            getattr(s, model).v0.v[:] = voltage_target
    pq_bus = [int(b) for b in s.PQ.bus.v]
    s.PQ.p0.v[pq_bus.index(4)] += dp
    s.PQ.q0.v[pq_bus.index(21)] += dq
    return s


def limits(s: andes.System, sn_mva: dict[int, float]) -> dict[int, dict[str, float]]:
    out: dict[int, dict[str, float]] = {}
    for model in ("PV", "Slack"):
        d = getattr(s, model)
        for k, b in enumerate(d.bus.v):
            out[int(b)] = {"pmax": float(d.pmax.v[k]), "qmin": float(d.qmin.v[k]),
                           "qmax": float(d.qmax.v[k]), "s_max": sn_mva[int(b)] / BASE_MVA}
    return out


def static_point(s: andes.System, lim: dict[int, dict[str, float]]) -> dict[str, dict[str, float]]:
    if not s.PFlow.run():
        raise RuntimeError("PFlow did not converge")
    out = {}
    for model in ("PV", "Slack"):
        d = getattr(s, model)
        for k, b in enumerate(d.bus.v):
            p, q, l = float(d.p.v[k]), float(d.q.v[k]), lim[int(b)]
            s_pu = float(np.hypot(p, q))
            violations = [name for name, bad in (
                ("P>pmax", p > l["pmax"] + TOL), ("Q>qmax", q > l["qmax"] + TOL),
                ("Q<qmin", q < l["qmin"] - TOL), ("S>Sn", s_pu > l["s_max"] + TOL)) if bad]
            out[str(int(b))] = {"P_pu": p, "Q_pu": q, "S_pu": s_pu, "S_over_Sn": s_pu / l["s_max"],
                                "P_headroom_pu": l["pmax"] - p, "Q_up_headroom_pu": l["qmax"] - q,
                                "Q_down_headroom_pu": q - l["qmin"], "violations": violations}
    return out


def dynamic_envelope(raw: np.lib.npyio.NpzFile, prefix: str, lim: dict[int, dict[str, float]],
                     sg_sn: list[float]) -> dict[str, dict[str, float]]:
    sg_bus = [int(b) for b in raw[f"{prefix}sg_bus_ids"]]
    gfm_bus = [int(b) for b in raw[f"{prefix}gfm_bus_ids"]]
    # GENROU.Pe/Qe are system-base pu (verified in E6); REGF1 Pe/Qe likewise.
    p = np.hstack([raw[f"{prefix}sg_p_pu"], raw[f"{prefix}gfm_p_pu"]])
    q = np.hstack([raw[f"{prefix}sg_q_pu"], raw[f"{prefix}gfm_q_pu"]])
    out = {}
    for col, b in enumerate(sg_bus + gfm_bus):
        l = lim[b]
        s_pu = np.hypot(p[:, col], q[:, col])
        violations = [name for name, bad in (
            ("P>pmax", p[:, col].max() > l["pmax"] + TOL), ("Q>qmax", q[:, col].max() > l["qmax"] + TOL),
            ("Q<qmin", q[:, col].min() < l["qmin"] - TOL), ("S>Sn", s_pu.max() > l["s_max"] + TOL)) if bad]
        out[str(b)] = {"P_max_pu": float(p[:, col].max()), "Q_max_pu": float(q[:, col].max()),
                       "Q_min_pu": float(q[:, col].min()), "S_over_Sn_max": float(s_pu.max() / l["s_max"]),
                       "P_excess_over_pmax_pu": float(max(0.0, p[:, col].max() - l["pmax"])),
                       "violations": violations}
    return out


def main() -> int:
    base = load(None)
    sn_mva = {int(b): float(sn) for b, sn in zip(base.GENROU.bus.v, base.GENROU.Sn.v)}
    sn_mva.update({int(b): float(sn) for b, sn in zip(base.REGF1.bus.v, base.REGF1.Sn.v)})
    lim = limits(base, sn_mva)
    regf1 = {int(b): {"Pmax": float(pm), "Qmax": float(qm), "Sn_pu": float(sn) / BASE_MVA}
             for b, pm, qm, sn in zip(base.REGF1.bus.v, base.REGF1.Pmax.v, base.REGF1.Qmax.v, base.REGF1.Sn.v)}
    contrast = {str(b): {"regf1_Pmax_over_case_pmax": regf1[b]["Pmax"] / lim[b]["pmax"],
                         "regf1_Qmax_over_case_qmax": regf1[b]["Qmax"] / lim[b]["qmax"],
                         "regf1_Qmax_over_case_abs_qmin": regf1[b]["Qmax"] / abs(lim[b]["qmin"])} for b in regf1}
    static = {"base": static_point(base, lim)}
    feas = {"v_target_1.0": static_point(load(1.0), lim),
            "v_target_1.0_plus_1pct_P_Q": static_point(load(1.0, EVENT_Q_PU, EVENT_P_PU), lim)}
    voltages = {}
    for tag, s in (("base", load(None)), ("v_target_1.0", load(1.0))):
        s.PFlow.run()
        voltages[tag] = {"all_bus_min_pu": float(np.min(s.Bus.v.v)), "all_bus_max_pu": float(np.max(s.Bus.v.v)),
                         "unit_bus_voltage_pu": {str(b): float(s.Bus.v.v[list(s.Bus.idx.v).index(b)]) for b in sorted(lim)}}
    e5, e6 = np.load(ARTIFACTS_DIR / f"IEEE39_E5_{VARIANT}_timeseries.npz"), np.load(ARTIFACTS_DIR / f"IEEE39_E6_{VARIANT}_timeseries.npz")
    sg_sn = [sn_mva[int(b)] for b in e6["sg_bus_ids"]]
    dynamic = {"E5_P+": dynamic_envelope(e5, "P+_", lim, sg_sn), "E5_Q+": dynamic_envelope(e5, "Q+_", lim, sg_sn),
               "E6_P+": dynamic_envelope(e6, "", lim, sg_sn)}
    flagged = {k: [f"bus{b}:{'/'.join(v['violations'])}" for b, v in d.items() if v["violations"]]
               for k, d in {**static, **feas, **dynamic}.items()}
    result = {"case_sha256": sha256(CASE), "capability_definition":
              "case static-generator pmax/qmin/qmax intersected with S <= Sn/100; PQ box and apparent-power disc",
              "regf1_internal_limits_contrast": contrast, "static_dispatch": static,
              "voltage_target_feasibility": feas, "voltage_summary": voltages,
              "dynamic_envelopes": dynamic, "violations_by_check": flagged,
              "limitations": [
                  "Case pmax/qmin/qmax are plant data of the IEEE-39 case, used as capability proxies; they are not a manufacturer capability curve.",
                  "PFlow assigns all active-power imbalance to the slack (bus 39); the 'plus 1 %' feasibility rows test Q feasibility, not P sharing.",
                  "REGF1 has no current limit and no SoC model; GFM P/Q capability here is the case box plus the Sn disc.",
                  "SG capability curves (rotor/stator/underexcitation limits) are not modeled; qmin/qmax stand in for them.",
                  "Dynamic envelopes use the recorded E5/E6 time series (1 % events); no larger disturbance was audited."]}
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(flagged, indent=1))
    for b in sorted(lim):
        s0, s1 = static["base"][str(b)], feas["v_target_1.0"][str(b)]
        print(f"bus{b}: P_head={s0['P_headroom_pu']:.3f} Qup_head base={s0['Q_up_headroom_pu']:.2f} V1.0={s1['Q_up_headroom_pu']:.2f} "
              f"Qdn_head base={s0['Q_down_headroom_pu']:.2f} V1.0={s1['Q_down_headroom_pu']:.2f}")
    print({k: (round(v["all_bus_min_pu"], 4), round(v["all_bus_max_pu"], 4)) for k, v in voltages.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
