"""DEC-050 block C1 (static part, no dynamic simulation): dispatch-conditioned active-power frontier.

E12 compared a STATIC frontier (AC equilibrium with free redispatch of the ten units, 1 % interior margins, bus voltages 0.95-1.05 pu) with DYNAMIC runs of B2 on the variant
C2t_Vsafe_R35_040.  The static problem contains no dependence on the dispatch (the pre-event powers enter only the objective, not the constraints), so 117 MW is a ceiling for ANY redispatch
and is not comparable with a run that keeps a given dispatch and the RDC sharing.  Here the comparison is made on equal terms.  For each dispatch D in {C2t historical,
C2t_Vsafe_R35_040} and the load step at bus 4 of amplitude a:
    p_i = p0_i(D) + s_i (sum_j p_j - sum_j p0_j)        for all units  (the ACTIVE-POWER SHARES s_i observed in the B2 P+ run of that dispatch are frozen),
    AC power balance, Q free, V_bus in 0.95-1.05, P/Q/S limits with the same a margin of 0 (physical limits, as used to count violations in the dynamic runs) and, for reference, the 1 % margin used by E12 (which alone removes most of the SG reserve).
The largest a for which this problem is feasible is the first amplitude at which the observed sharing hits a limit or the network cannot supply it ("sharing frontier").
Shares are taken from the delivered dP at the end of the 200 s run at 58.564 MW (E11); they are an assumption of this extrapolation (the RDC shares change near limits).
"""

from __future__ import annotations

import json
import os
from typing import Any

os.environ["C2_VARIANT"] = "C2t"

import numpy as np
from scipy.optimize import minimize

import select_equilibrium_b3 as b3
from run_e0_ieee39 import ARTIFACTS_DIR as A, git_commit

P_STEP_PU = 58.564 / 100.0
DV = 0.05


def feasible_shared(mult: float, p0: np.ndarray, shares: np.ndarray, ctx, eps: float) -> dict[str, Any]:
    lim, slack_pos, slack_angle = ctx
    s = b3.load_plant({4: (P_STEP_PU * mult, 0.0)})
    s.PFlow.run()
    y, bus, pl, ql = b3.network(s)
    n = len(bus)
    u_pos = np.array([bus.index(b) for b in lim["unit_bus"]])
    other = np.array([i for i in range(n) if i not in set(u_pos)])
    free = np.array([i for i in range(n) if i != slack_pos])
    rp, rq = lim["pmax"] - lim["pmin"], lim["qmax"] - lim["qmin"]
    EPS, EPS_S = eps, eps

    def unpack(x):
        v = x[:n]; a = np.zeros(n); a[free] = x[n:]; a[slack_pos] = slack_angle
        return v, a

    def inj(x):
        v, a = unpack(x)
        vc = v * np.exp(1j * a)
        return v, vc * np.conj(y @ vc)

    def unit_pq(x):
        v, sj = inj(x)
        return sj.real[u_pos] + pl[u_pos], sj.imag[u_pos] + ql[u_pos], v

    def eq(x):
        v, sj = inj(x)
        p, _, _ = unit_pq(x)
        sh = p - p0 - shares * (p.sum() - p0.sum())
        return np.concatenate([sj.real[other] + pl[other], sj.imag[other] + ql[other], sh[:-1]])

    def ineq(x):
        p, q, v = unit_pq(x)
        return np.concatenate([lim["pmax"] - EPS * rp - p, p - lim["pmin"] - EPS * rp, lim["qmax"] - EPS * rq - q, q - lim["qmin"] - EPS * rq,
                               ((1 - EPS_S) * lim["smax"]) ** 2 - p ** 2 - q ** 2, v - 0.95, 1.05 - v])

    x0 = np.concatenate([np.asarray(s.Bus.v.v, float), np.asarray(s.Bus.a.v, float)[free]])
    res = minimize(lambda x: float(np.sum(((unit_pq(x)[2] - 1.0) / DV) ** 2)), x0, method="SLSQP", constraints=[{"type": "eq", "fun": eq}, {"type": "ineq", "fun": ineq}],
                   options={"maxiter": 300, "ftol": 1e-10})
    g = ineq(res.x)
    p, q, v = unit_pq(res.x)
    feas = bool(res.success and g.min() >= -1e-6 and np.abs(eq(res.x)).max() <= 1e-6)
    names = ([f"P<=pmax@{b}" for b in lim["unit_bus"]] + [f"P>=pmin@{b}" for b in lim["unit_bus"]] + [f"Q<=qmax@{b}" for b in lim["unit_bus"]] + [f"Q>=qmin@{b}" for b in lim["unit_bus"]]
             + [f"S@{b}" for b in lim["unit_bus"]] + [f"Vmin@{b}" for b in bus] + [f"Vmax@{b}" for b in bus])
    return {"multiple": mult, "amplitude_MW": mult * P_STEP_PU * 100.0, "feasible": feas, "ineq_min": float(g.min()), "eq_residual": float(np.abs(eq(res.x)).max()), "message": str(res.message),
            "binding_or_violated": [nm for nm, gi in zip(names, g) if gi < 1e-4][:6], "P": p.tolist()}


def frontier(p0, shares, ctx, log: list, eps: float) -> float:
    lo, hi = 0.25, 4.0
    r = feasible_shared(lo, p0, shares, ctx, eps); log.append(r)
    if not r["feasible"]:
        return 0.0
    r = feasible_shared(hi, p0, shares, ctx, eps); log.append(r)
    if r["feasible"]:
        return hi
    for _ in range(10):
        mid = 0.5 * (lo + hi)
        r = feasible_shared(mid, p0, shares, ctx, eps); log.append(r)
        lo, hi = (mid, hi) if r["feasible"] else (lo, mid)
    return lo


def main() -> int:
    base = b3.load_plant()
    lim = b3.unit_limits(base)
    y, bus, _, _ = b3.network(base)
    ctx = (lim, bus.index(int(base.Slack.bus.v[0])), float(base.Slack.a0.v[0]))
    e11 = json.loads((A / "IEEE39_E11_summary.json").read_text(encoding="utf-8"))["runs"]
    ref = b3.load_plant(); ref.PFlow.run(); ref.TDS.config.no_tqdm = 1; ref.TDS.config.tf = 1; ref.TDS.init()
    p_hist = b3.andes_state(ref, lim)["p"]
    vb = json.loads((A / "IEEE39_E9B0_variant_R35_040.json").read_text(encoding="utf-8"))["initial_condition"]["units"]
    cases = {"C2t historical (E8_B2 P+ shares)": (p_hist, e11["E8_B2 P+"]["delivered_dP_by_unit_pu"]),
             "C2t_Vsafe_R35_040 (R35_040_B2 P+ shares)": (np.array([u["P_pu"] for u in vb]), e11["R35_040_B2 P+"]["delivered_dP_by_unit_pu"])}
    out: dict[str, Any] = {"stage": "DEC-050 C1 static", "git_commit": git_commit(), "doc": __doc__, "cases": {}}
    for (name, (p0, dp)), eps in [(c, e) for e in (0.0, 0.01) for c in cases.items()]:
        name = f"{name} | interior margin {eps:g}"
        dp = np.array(list(dp.values()), float)
        sh = dp / dp.sum()
        log: list = []
        fr = frontier(np.asarray(p0, float), sh, ctx, log, eps)
        last_inf = next((r for r in reversed(log) if not r["feasible"]), None)
        out["cases"][name] = {"p0_pu": [float(x) for x in p0], "shares": sh.tolist(), "frontier_multiple": fr, "frontier_amplitude_MW": fr * P_STEP_PU * 100.0,
                              "first_infeasible_binding": last_inf["binding_or_violated"] if last_inf else None, "first_infeasible_amplitude_MW": last_inf["amplitude_MW"] if last_inf else None,
                              "log": [{k: v for k, v in r.items() if k != "P"} for r in log]}
        print(name, "frontier MW", round(fr * P_STEP_PU * 100, 2), last_inf["binding_or_violated"] if last_inf else None, flush=True)
    (A / "IEEE39_DEC050_C1_static.json").write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
