"""E9-H: predictive safety filter (B4) versus B2 on C2t_Vsafe_R35_040.

Stages (declared before running, DEC-047):
  1. S0 (60 s): B4 active from t = 5.5 s; passes only if the safety LP is feasible at every update with zero action (nominal command kept) and the mean update cost is <= 0.5 s.
  2. Shadow runs on P+ and Q+ (filter evaluated, output discarded): the scenario is selected by this rule, before any B4 result exists: P+ if in the shadow run the nominal B2 command violates a tightened
     ENFORCEABLE barrier at >= 3 updates and the LP is feasible at every update; else Q+ under the same rule; else no scenario (the development stops, option B).
  3. B2 versus B4 on the selected scenario (60 s) with identical variant, dispatch, perturbation and actuators.
If the LP is infeasible at an update at which the nominal command violates an enforceable constraint, the test STOPS (no relaxation).  The result is reported as: constraints enforced up to the
verified horizon, conditional on the empirical error bound; no claim against unknown steps; no claim of improved safety if B2 respects all physical constraints.
Monitored barriers (not influenced by the GFM within the horizon, e.g. SG limits) are only reported: their reserve is checked, not enforced.
"""

from __future__ import annotations

import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

os.environ["C2_VARIANT"] = "C2t"

import andes
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import e9h_predictor as PR  # noqa: E402
import run_b3_ieee39 as b  # noqa: E402
import run_e8_ieee39 as e8  # noqa: E402
from e9b_variant import HOOK, TAG, VARIANT  # noqa: E402
from run_e0_ieee39 import ARTIFACTS_DIR, FIGURES_DIR, extract_time_series, git_commit, sha256  # noqa: E402

OUT = ARTIFACTS_DIR / f"IEEE39_E9H_b4{TAG}.json"
BOUNDS = ARTIFACTS_DIR / f"IEEE39_E9H_error_bounds{TAG}.npz"
UPDATE = 0.1
HORIZON_RUN = 60.0
T_ACT = 5.5
REFRESH_EVERY = 10
ENVELOPE = {"S0": (0.616, 0.0154), "P+": (0.616, 0.0154), "Q+": (0.195, 0.0154)}
V_BAND = (0.95, 1.05)


class StopSafety(Exception):
    pass


class PredictiveFilter:
    def __init__(self, scenario: str, shadow: bool, eps: np.ndarray):
        self.sc, self.shadow, self.eps = scenario, shadow, eps
        self.vref = np.concatenate([np.full(4, ENVELOPE[scenario][0]), np.full(4, ENVELOPE[scenario][1])])
        self.pred = PR.LinearPredictor(None)
        self.next, self.i, self.dv, self.log, self.stopped = T_ACT, 0, np.zeros(8), [], None
        self.ready = False
        self.store: list[dict[str, Any]] = []

    def fn(self, t, sys_, ctx, st, vnom_p, vnom_q):
        vp, vq = np.array(vnom_p, float), np.array(vnom_q, float)
        if t < T_ACT - 1e-9:
            return vp, vq
        v_nom = np.concatenate([vp[6:10], vq[6:10]])
        if t >= self.next - 1e-9:
            self.update(t, sys_, ctx, st, vnom_p, vnom_q, v_nom)
            self.next += UPDATE
            self.i += 1
        if self.shadow:
            return vp, vq
        v = np.clip(v_nom + self.dv, -self.vref, self.vref)
        vp[6:10], vq[6:10] = v[:4], v[4:]
        return vp, vq

    def update(self, t, sys_, ctx, st, vnom_p, vnom_q, v_nom) -> None:
        if not self.ready:
            self.pred.ctx, self.pred.lim, self.ready = ctx, ctx["lim"], True
        t0 = time.perf_counter()
        p = self.pred.build(sys_, st, vnom_p, vnom_q, float(t), refresh_params=(self.i % REFRESH_EVERY == 0))
        t_pred = time.perf_counter() - t0
        t1 = time.perf_counter()
        rows = PR.assemble_vec(p, self.eps, self.vref, ctx["lim"])          # vectorised after the first S0 run exceeded the declared cost (same rows; identical to the loop version)
        enforce = PR.classify_vec(rows)
        is_enf = np.isin(rows["name"], list(enforce))
        slack = rows["m"] - rows["eps"]
        nominal_viol = sorted({str(x) for x in rows["name"][is_enf & (slack < 0)]})
        monitored_viol = sorted({str(x) for x in rows["name"][~is_enf & (slack < 0)]})
        worst_enf = float(slack[is_enf].min()) if is_enf.any() else float("inf")
        sol = PR.solve_lp_vec(rows, enforce, p, self.vref, ctx["lim"])
        t_lp = time.perf_counter() - t1
        rec = {"t_s": float(t), "n_enforced_barriers": len(enforce), "enforced_names_sample": sorted(enforce)[:6], "nominal_violates_enforceable": nominal_viol, "monitored_reserve_violated": monitored_viol,
               "worst_enforceable_margin_minus_eps": float(worst_enf), "lp_feasible": sol["feasible"], "lp_rows": sol["n_rows"], "t_predict_s": t_pred, "t_assemble_lp_s": t_lp,
               "timing_predict": p["timing"]}
        if sol["feasible"]:
            self.dv = sol["dv"]
            rec["dv_norm_normalized"] = float(np.linalg.norm(self.dv / self.vref))
            rec["dv_max_abs"] = float(np.abs(self.dv).max())
            rec["active"] = bool(nominal_viol)
        else:
            rec["elastic_violation"] = sol.get("elastic_violation")
            self.log.append(rec)
            self.stopped = {"t_s": float(t), "cause": "safety LP infeasible (no relaxation applied)", "nominal_violates_enforceable": nominal_viol, "elastic_violation": sol.get("elastic_violation")}
            if not self.shadow:
                raise StopSafety(f"infeasible at t = {t:.3f}")
            self.dv = np.zeros(8)
            rec["active"] = True
            return
        if self.i % 10 == 0 and t + PR.HORIZON <= HORIZON_RUN:
            self.store.append({"t0": float(t), "Y": p["Y"].copy(), "R": p["R"].copy(), "dv": self.dv.copy()})
        self.log.append(rec)


def unit_arrays(d):
    ids = list(d["bus_ids"])
    cols = [ids.index(bb) for bb in d["unit_bus_ids"]]
    return np.hstack([d["sg_p_pu"], d["gfm_p_pu"]]), np.hstack([d["sg_q_pu"], d["gfm_q_pu"]]), d["bus_voltage_pu"][:, cols]


def metrics(d, lim) -> dict[str, Any]:
    t = d["time_s"]
    p, q, v = unit_arrays(d)
    vb = d["bus_voltage_pu"]
    s_rel = 1 - np.hypot(p, q) / lim["smax"]
    return {"t_end_s": float(t[-1]), "min_P_margin_pu": (lim["pmax"] - p).min(axis=0).tolist(), "min_Q_margin_pu": np.minimum(lim["qmax"] - q, q - lim["qmin"]).min(axis=0).tolist(),
            "min_S_rel_margin": s_rel.min(axis=0).tolist(), "bus_voltage_min_pu": float(vb.min()), "bus_voltage_max_pu": float(vb.max()),
            "min_voltage_margin_to_band_pu": float(np.minimum(vb - V_BAND[0], V_BAND[1] - vb).min()), "n_buses_ever_outside_band": int(((vb < V_BAND[0]) | (vb > V_BAND[1])).any(axis=0).sum()),
            "violating_units": [i for i in range(10) if (p[:, i].max() > lim["pmax"][i] or p[:, i].min() < lim["pmin"][i] or q[:, i].max() > lim["qmax"][i] or q[:, i].min() < lim["qmin"][i] or s_rel[:, i].min() < 0)],
            "frequency_nadir_hz": float(d["bus_frequency_hz"].mean(axis=1).min()), "frequency_max_dev_hz": float(np.abs(d["bus_frequency_hz"].mean(axis=1) - 60.0).max()),
            "max_cmd_z": float(np.abs(d["cmd_z"]).max()) if "cmd_z" in d else None}


def run_scenario(sc: str, shadow: bool, eps: np.ndarray, label: str, plot: bool = True) -> dict[str, Any]:
    cap: dict[str, Any] = {}

    def hook(system, ctx):
        HOOK(system, ctx)
        system.TDS.config.tf = HORIZON_RUN
        cap["sys"], cap["ctx"] = system, ctx

    flt = PredictiveFilter(sc, shadow, eps)
    t0 = time.perf_counter()
    _, d2, diag2 = b.run("B2", sc, init_hook=hook)
    t_b2 = time.perf_counter() - t0
    lim = cap["ctx"]["lim"]
    stopped_exc = None
    t0 = time.perf_counter()
    try:
        _, d4, diag4 = b.run("B2", sc, init_hook=hook, qp_filter={"fn": flt.fn})
    except StopSafety as exc:
        stopped_exc = str(exc)
        s = cap["sys"]
        d4 = extract_time_series(s)
        yy = s.dae.ts.y
        d4["sg_p_pu"], d4["sg_q_pu"] = np.asarray(yy[:, s.GENROU.Pe.a], float), np.asarray(yy[:, s.GENROU.Qe.a], float)
        d4["gfm_p_pu"], d4["gfm_q_pu"] = np.asarray(yy[:, s.REGF1.Pe.a], float), np.asarray(yy[:, s.REGF1.Qe.a], float)
        d4["bus_ids"], d4["unit_bus_ids"] = np.asarray(d2["bus_ids"]), np.asarray(d2["unit_bus_ids"])
        diag4 = {"tds_ok": False, "stopped": True}
    t_b4 = time.perf_counter() - t0
    m2, m4 = metrics(d2, lim), metrics(d4, lim)
    n = min(len(d2["time_s"]), len(d4["time_s"]))
    p2, q2, _ = unit_arrays(d2)
    p4, q4, _ = unit_arrays(d4)
    diff = {"max_abs_frequency_diff_hz": float(np.abs(d2["bus_frequency_hz"][:n] - d4["bus_frequency_hz"][:n]).max()), "max_abs_voltage_diff_pu": float(np.abs(d2["bus_voltage_pu"][:n] - d4["bus_voltage_pu"][:n]).max()),
            "max_abs_P_diff_pu": float(np.abs(p2[:n] - p4[:n]).max()), "max_abs_Q_diff_pu": float(np.abs(q2[:n] - q4[:n]).max())}
    log = flt.log
    walls = [r["t_predict_s"] + r["t_assemble_lp_s"] for r in log]
    t = d4["time_s"]
    Y = np.hstack([np.hstack([d4["sg_p_pu"], d4["gfm_p_pu"]]), np.hstack([d4["sg_q_pu"], d4["gfm_q_pu"]]), d4["bus_voltage_pu"]])
    viol_cnt, tot_cnt, worst_ratio = 0, 0, 0.0
    for w in flt.store:
        sel = (t > w["t0"] + 1e-9) & (t <= w["t0"] + 0.3 + 1e-9)
        if not sel.any():
            continue
        tau = t[sel] - w["t0"]
        grid = np.arange(PR.K + 1) * PR.DT
        yp = w["Y"] + np.einsum("kjm,m->kj", w["R"], w["dv"])
        pred = np.stack([np.interp(tau, grid, yp[:, j]) for j in range(59)], axis=1)
        err = np.abs(Y[sel] - pred)
        kb = np.clip(np.ceil(tau / PR.DT - 1e-9).astype(int), 1, PR.K)
        bound = eps[kb]
        viol_cnt += int((err > bound).sum())
        tot_cnt += int(err.size)
        worst_ratio = max(worst_ratio, float(np.max(err / np.maximum(bound, 1e-12))))
    out = {"label": label, "scenario": sc, "shadow": shadow, "B2": m2, "B4": m4, "difference_B4_minus_B2": diff, "stopped": flt.stopped, "stop_exception": stopped_exc,
           "filter": {"n_updates": len(log), "n_active_updates": int(sum(1 for r in log if r.get("active"))), "n_lp_infeasible": int(sum(1 for r in log if not r["lp_feasible"])),
                      "max_dv_abs_pu_per_s": float(max([r.get("dv_max_abs", 0.0) for r in log], default=0.0)), "n_updates_nominal_violates_enforceable": int(sum(1 for r in log if r["nominal_violates_enforceable"])),
                      "enforceable_barriers_activated": sorted({nm for r in log for nm in r["nominal_violates_enforceable"]}), "monitored_reserve_violations": sorted({nm for r in log for nm in r["monitored_reserve_violated"]}),
                      "n_updates_monitored_reserve_violated": int(sum(1 for r in log if r["monitored_reserve_violated"])), "active_times_s": [r["t_s"] for r in log if r.get("active")][:80],
                      "worst_enforceable_margin_minus_eps_min": float(min([r["worst_enforceable_margin_minus_eps"] for r in log], default=np.inf))},
           "cost": {"mean_update_s": float(np.mean(walls)) if walls else None, "p95_update_s": float(np.percentile(walls, 95)) if walls else None, "max_update_s": float(max(walls)) if walls else None,
                    "requirement_mean_le_0.5s": bool(np.mean(walls) <= 0.5) if walls else None, "update_period_s": UPDATE, "wall_B2_s": t_b2, "wall_B4_s": t_b4},
           "coverage_first_0.3s_of_each_window": {"samples": tot_cnt, "outside_bound": viol_cnt, "fraction_inside": (1 - viol_cnt / tot_cnt) if tot_cnt else None, "worst_error_over_bound": worst_ratio},
           "diag_B2": diag2, "diag_B4": diag4, "log_head": log[:2], "log_tail": log[-2:]}
    if plot and not shadow:
        plot_case(label, d2, d4, flt, lim)
    print(f"{label}: shadow={shadow} updates={len(log)} active={out['filter']['n_active_updates']} infeasible={out['filter']['n_lp_infeasible']} stopped={flt.stopped is not None} "
          f"mean_update={out['cost']['mean_update_s']} max|dV|={diff['max_abs_voltage_diff_pu']:.2e} B2viol={m2['violating_units']} B4viol={m4['violating_units']}", flush=True)
    return out


def plot_case(label, d2, d4, flt, lim) -> None:
    fig, ax = plt.subplots(2, 3, figsize=(19, 9))
    for d, ls, lb in ((d2, "-", "B2"), (d4, "--", "B4")):
        t = d["time_s"]
        ax[0, 0].plot(t, d["bus_frequency_hz"].mean(axis=1) - 60.0, ls, label=lb)
        ax[0, 1].plot(t, d["bus_voltage_pu"].max(axis=1), ls, label=f"{lb} max")
        ax[0, 1].plot(t, d["bus_voltage_pu"].min(axis=1), ls, lw=.8, label=f"{lb} min")
        p, q, v = unit_arrays(d)
        for i, nm in ((1, "SG31"), (3, "SG35"), (9, "GFM36"), (6, "GFM32")):
            ax[0, 2].plot(t, p[:, i], ls, lw=.9, label=f"{lb} P {nm}")
        ax[1, 0].plot(t, (lim["pmax"] - p).min(axis=1), ls, label=f"{lb} min(pmax-P)")
        ax[1, 0].plot(t, (1 - np.hypot(p, q) / lim["smax"]).min(axis=1), ls, label=f"{lb} min S rel")
        if "cmd_pset" in d:
            ax[1, 1].plot(d["cmd_t"], d["cmd_pset"][:, 6:] - d["unit_pn"][6:], ls, lw=.9)
    ax[0, 1].axhline(1.05, color="k", ls=":", lw=.8)
    ax[0, 1].axhline(0.95, color="k", ls=":", lw=.8)
    tt = [r["t_s"] for r in flt.log]
    ax[1, 2].plot(tt, [r.get("dv_norm_normalized", np.nan) for r in flt.log], "o-", ms=2, label="||dv||/v_ref")
    ax[1, 2].plot(tt, [len(r["nominal_violates_enforceable"]) for r in flt.log], "s-", ms=2, label="enforceable barriers violated by the nominal plan")
    ax[1, 2].plot(tt, [len(r["monitored_reserve_violated"]) for r in flt.log], "^-", ms=2, label="monitored barriers without reserve")
    ax[1, 2].plot(tt, [r["worst_enforceable_margin_minus_eps"] for r in flt.log], "-", lw=.8, label="worst enforceable (margin - bound)")
    for a in ax.ravel():
        a.axvline(5.0, color="tab:red", ls=":", lw=.8)
        a.axvline(T_ACT, color="g", ls=":", lw=.9)
        a.grid(alpha=.25)
        a.set_xlabel("Time [s]")
    ax[0, 0].set_title("mean bus frequency - 60 Hz"); ax[0, 1].set_title("39-bus voltage extremes"); ax[0, 2].set_title("physical P"); ax[1, 0].set_title("physical margins")
    ax[1, 1].set_title("GFM Pset - Pn (B2 solid, B4 dashed)"); ax[1, 2].set_title("filter indicators")
    for a in (ax[0, 0], ax[0, 1], ax[0, 2], ax[1, 0], ax[1, 2]):
        a.legend(fontsize=6)
    fig.suptitle(f"E9-H {label}: B2 vs B4 (predictive safety filter on the GFM rates, H = 3 s, Ts = 0.1 s) on {VARIANT}; green dotted: filter start")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"IEEE39_E9H_{label.replace(' ', '_').replace('+', 'p')}{TAG}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    z = np.load(BOUNDS)
    eps = z["eps"]
    result: dict[str, Any] = {"variant": VARIANT, "git_commit": git_commit(), "andes": andes.__version__, "python": platform.python_version(), "update_s": UPDATE, "horizon_s": PR.HORIZON,
                              "bounds_sha256": sha256(BOUNDS), "doc": __doc__, "stages": {}}
    stages = sys.argv[1:] or ["S0", "shadow", "selected"]
    if "S0" in stages:
        result["stages"]["S0"] = run_scenario("S0", False, eps, "S0")
        s0 = result["stages"]["S0"]
        s0["gate"] = {"lp_feasible_every_update": s0["filter"]["n_lp_infeasible"] == 0, "zero_action_every_update": s0["filter"]["n_active_updates"] == 0 and s0["stopped"] is None,
                      "cost_requirement": s0["cost"]["requirement_mean_le_0.5s"]}
        s0["gate"]["passed"] = bool(all(s0["gate"].values()))
        OUT.write_text(json.dumps(result, indent=2, default=float), encoding="utf-8")
        if not s0["gate"]["passed"]:
            print("S0 gate NOT passed: stop", flush=True)
            return 0
    if "shadow" in stages:
        sh = {sc: run_scenario(sc, True, eps, f"shadow {sc}", plot=False) for sc in ("P+", "Q+")}
        result["stages"]["shadow"] = sh
        sel = None
        for sc in ("P+", "Q+"):
            r = sh[sc]["filter"]
            if r["n_updates_nominal_violates_enforceable"] >= 3 and r["n_lp_infeasible"] == 0:
                sel = sc
                break
        result["selected_scenario"] = sel
        result["selection_rule"] = "P+ if the nominal B2 plan violates a tightened enforceable barrier at >= 3 updates and the LP is feasible at every update; else Q+ under the same rule; else none"
        OUT.write_text(json.dumps(result, indent=2, default=float), encoding="utf-8")
        if sel is None:
            print("no scenario activates an enforceable constraint with a feasible LP: stop (option B)", flush=True)
            return 0
    if "selected" in stages:
        sel = result.get("selected_scenario") or json.loads(OUT.read_text(encoding="utf-8")).get("selected_scenario")
        result["selected_scenario"] = sel
        if sel:
            result["stages"]["selected_B2_vs_B4"] = run_scenario(sel, False, eps, f"{sel} selected")
    result["code_sha256"] = {f: sha256(Path(__file__).parent / f) for f in ("run_e9h_b4.py", "e9h_predictor.py", "validate_e9h_predictor.py", "e9a_linear.py", "run_b3_ieee39.py")}
    OUT.write_text(json.dumps(result, indent=2, default=float), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
