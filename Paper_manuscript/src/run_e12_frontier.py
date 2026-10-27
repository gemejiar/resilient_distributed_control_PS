"""E12 (Option B): operational frontier and feasibility of a growing load deficit.

Static part: with the frozen AC problem of B3-A (all 39 buses, P/Q/S limits tightened by 1 % of their range, bus voltages in 0.95-1.05 pu, free redispatch of the ten units) the largest
multiple m of the original P+ (58.564 MW at bus 4) and of the original Q+ (17.345 MVAr at bus 21) for which an AC equilibrium exists is located by doubling and bisection (feasibility only:
the objective is irrelevant).  Dynamic part: B2 (original RDC, no filter) on the frozen variant C2t_Vsafe_R35_040 is run for 40 s at the declared fractions 0.10, 0.25, 0.50, 0.75, 0.90 of each
static frontier.  Each amplitude is classified as
  (i)   no AC equilibrium exists (amplitude above the static frontier) - not simulated, reported;
  (ii)  an equilibrium exists but the simulation fails (TDS not converged), crosses a P/Q/S limit or leaves the 0.95-1.05 pu band;
  (iii) equilibrium exists and the simulation respects the limits.
No optimisation of the controller, no change of capacities or gains; "recovery" is only claimed where the run shows it.
"""

from __future__ import annotations

import csv
import json
import os
import time
from typing import Any

os.environ["C2_VARIANT"] = "C2t"

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import run_b3_ieee39 as b  # noqa: E402
import run_e8_ieee39 as e8  # noqa: E402
import select_equilibrium_b3 as b3  # noqa: E402
from e9b_variant import HOOK, VARIANT  # noqa: E402
from run_e0_ieee39 import ARTIFACTS_DIR as A, FIGURES_DIR, git_commit  # noqa: E402

BASE_MVA = 100.0
P_STEP_PU, Q_STEP_PU = 58.564 / BASE_MVA, 17.345 / BASE_MVA
FRACTIONS = (0.10, 0.25, 0.50, 0.75, 0.90)
HORIZON = 40.0
V_BAND = (0.95, 1.05)


def static_setup():
    base = b3.load_plant()
    lim = b3.unit_limits(base)
    y, bus, pl0, ql0 = b3.network(base)
    slack_pos, slack_angle = bus.index(int(base.Slack.bus.v[0])), float(base.Slack.a0.v[0])
    ref = b3.load_plant()
    ref.PFlow.run()
    ref.TDS.config.no_tqdm = 1
    ref.TDS.config.tf = 1
    ref.TDS.init()
    pre = b3.andes_state(ref, lim)
    return lim, slack_pos, slack_angle, pre["p"], pre["q"]


def feasible(kind: str, mult: float, ctx) -> dict[str, Any]:
    lim, slack_pos, slack_angle, p_pre, q_pre = ctx
    loads = {4: (P_STEP_PU * mult, 0.0)} if kind == "P" else {21: (0.0, Q_STEP_PU * mult)}
    s = b3.load_plant(loads)
    ok = bool(s.PFlow.run())
    y, bus, pl, ql = b3.network(s)
    t0 = time.perf_counter()
    sol = b3.solve(y, bus, pl, ql, lim, p_pre, q_pre, np.asarray(s.Bus.v.v, float), np.asarray(s.Bus.a.v, float), slack_pos, slack_angle)
    feas = bool(sol["success"] and sol["ineq_min"] >= -1e-6 and sol["eq_residual_max"] <= 1e-6)
    return {"kind": kind, "multiple": mult, "amplitude": mult * (P_STEP_PU if kind == "P" else Q_STEP_PU) * BASE_MVA, "pflow_ok": ok, "feasible": feas, "ineq_min": sol["ineq_min"], "eq_residual": sol["eq_residual_max"],
            "message": sol["message"], "active_constraints": sol["active_constraints"][:6], "time_s": time.perf_counter() - t0,
            "P_star": [float(x) for x in sol["p"]], "V_bus_min_max": [float(sol["v_bus"].min()), float(sol["v_bus"].max())]}


def frontier(kind: str, ctx, log: list) -> float:
    lo, hi = 1.0, 2.0
    r = feasible(kind, lo, ctx)
    log.append(r)
    if not r["feasible"]:
        return 0.0
    while hi < 64:
        r = feasible(kind, hi, ctx)
        log.append(r)
        if not r["feasible"]:
            break
        lo, hi = hi, hi * 2
    for _ in range(9):
        mid = 0.5 * (lo + hi)
        r = feasible(kind, mid, ctx)
        log.append(r)
        if r["feasible"]:
            lo = mid
        else:
            hi = mid
    return lo


def dynamic(kind: str, mult: float, lim) -> dict[str, Any]:
    name = f"{kind}x{mult:.3f}"
    e8.SCENARIOS[name] = {"p_mw": P_STEP_PU * BASE_MVA * mult} if kind == "P" else {"q_mvar": Q_STEP_PU * BASE_MVA * mult}

    def hook(system, ctx):
        HOOK(system, ctx)
        system.TDS.config.tf = HORIZON

    try:
        _, d, diag = b.run("B2", name, init_hook=hook)
    except Exception as exc:  # numerical failure of the TDS is a result
        return {"kind": kind, "multiple": mult, "tds_failed": True, "error": repr(exc)[:200], "class": "(ii) equilibrium exists, simulation fails"}
    t = d["time_s"]
    p = np.hstack([d["sg_p_pu"], d["gfm_p_pu"]]); q = np.hstack([d["sg_q_pu"], d["gfm_q_pu"]])
    vb = d["bus_voltage_pu"]
    s_rel = 1 - np.hypot(p, q) / lim["smax"]
    viol = [i for i in range(10) if (p[:, i].max() > lim["pmax"][i] or p[:, i].min() < lim["pmin"][i] or q[:, i].max() > lim["qmax"][i] or q[:, i].min() < lim["qmin"][i] or s_rel[:, i].min() < 0)]
    f = d["bus_frequency_hz"].mean(axis=1)
    out = {"kind": kind, "multiple": mult, "amplitude": mult * (P_STEP_PU if kind == "P" else Q_STEP_PU) * BASE_MVA, "tds_failed": not (diag["tds_ok"] and diag["t_end_s"] >= HORIZON - 1e-6),
           "t_end_s": diag["t_end_s"], "violating_units": viol, "n_buses_outside_band": int(((vb < V_BAND[0]) | (vb > V_BAND[1])).any(axis=0).sum()), "frequency_nadir_hz": float(f[t >= 5].min()),
           "frequency_final_error_hz": float(f[t >= t[-1] - 5].mean() - 60.0), "bus_voltage_min_pu": float(vb.min()), "bus_voltage_max_pu": float(vb.max()),
           "min_P_margin_pu": (lim["pmax"] - p).min(axis=0).tolist(), "final_residual": diag["final_residual"]}
    out["class"] = "(iii) equilibrium exists and the run respects the limits" if not (out["tds_failed"] or viol or out["n_buses_outside_band"]) else "(ii) equilibrium exists, run violates a limit/band or fails"
    return out


def main() -> int:
    ctx = static_setup()
    lim = ctx[0]
    logs: dict[str, list] = {"P": [], "Q": []}
    fr = {k: frontier(k, ctx, logs[k]) for k in ("P", "Q")}
    print("static frontier (multiples of the original step):", fr, flush=True)
    dyn = []
    for kind in ("P", "Q"):
        for fz in FRACTIONS:
            m = fr[kind] * fz
            r = dynamic(kind, m, lim)
            r["fraction_of_static_frontier"] = fz
            dyn.append(r)
            print(kind, round(m, 2), r["class"], r.get("violating_units"), flush=True)
    above = [{"kind": k, "multiple": fr[k] * 1.05, "class": "(i) no AC equilibrium exists (above the static frontier; first infeasible bracket in the log)"} for k in ("P", "Q")]
    summary = {"stage": "E12", "git_commit": git_commit(), "variant_dynamic": VARIANT, "static_plant": "C2t (historical case dispatch as pre-event reference, B3-A AC problem)", "static_frontier_multiples": fr,
               "static_frontier_amplitudes": {"P_MW": fr["P"] * P_STEP_PU * BASE_MVA, "Q_MVAr": fr["Q"] * Q_STEP_PU * BASE_MVA}, "dynamic_runs": dyn, "class_i_examples": above,
               "static_logs": {k: [{kk: vv for kk, vv in r.items() if kk not in ("P_star",)} for r in v] for k, v in logs.items()}, "fractions": list(FRACTIONS), "horizon_s": HORIZON}
    (A / "IEEE39_E12_frontier.json").write_text(json.dumps(summary, indent=2, default=float), encoding="utf-8")
    with (A / "IEEE39_E12_frontier.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["kind", "multiple", "amplitude", "fraction_of_static_frontier", "class", "tds_failed", "violating_units", "n_buses_outside_band", "frequency_nadir_hz", "bus_voltage_min_pu", "bus_voltage_max_pu"])
        w.writeheader()
        for r in dyn:
            w.writerow({k: (";".join(map(str, r.get(k))) if isinstance(r.get(k), list) else r.get(k)) for k in w.fieldnames})
    fig, ax = plt.subplots(1, 3, figsize=(18, 5))
    for k, col in (("P", "tab:blue"), ("Q", "tab:orange")):
        xs = [r["multiple"] for r in logs[k]]; ys = [r["ineq_min"] for r in logs[k]]
        ax[0].scatter(xs, ys, s=14, color=col, label=f"{k}: AC problem (min inequality slack)")
    ax[0].axhline(0, color="k", lw=.8); ax[0].set_xscale("log"); ax[0].set_xlabel("multiple of the original step"); ax[0].set_title("static AC feasibility: smallest constraint slack vs amplitude"); ax[0].legend(fontsize=7)
    for k, col in (("P", "tab:blue"), ("Q", "tab:orange")):
        rr = [r for r in dyn if r["kind"] == k]
        ax[1].plot([r["multiple"] for r in rr], [r.get("frequency_nadir_hz", np.nan) for r in rr], "o-", color=col, label=f"{k} nadir")
        ax[2].plot([r["multiple"] for r in rr], [r.get("bus_voltage_min_pu", np.nan) for r in rr], "o-", color=col, label=f"{k} min V")
    ax[1].set_title("B2 dynamic runs (fractions of the static frontier): frequency nadir"); ax[2].set_title("minimum bus voltage")
    for a in ax[1:]:
        a.set_xscale("log"); a.legend(fontsize=7); a.set_xlabel("multiple of the original step")
    for a in ax:
        a.grid(alpha=.25)
    fig.suptitle(f"E12: operational frontier (static frontier P x{fr['P']:.1f}, Q x{fr['Q']:.1f} of the original steps; dynamic runs on {VARIANT})"); fig.tight_layout()
    fig.savefig(FIGURES_DIR / "IEEE39_E12_frontier.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
