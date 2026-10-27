"""E9-G: B4 = B2 (original RDC, nominal) + HOCBF-QP filter on the eight GFM reference rates, closed loop, compared with B2 on the same variant, dispatch, perturbation and actuators.

Formulation (E9-F): exact nonlinear derivatives of the reduced DAE (algebraics, curvature, disturbance derivatives), evaluated on the slow manifold (fast modes with |Re lambda| > 100 s^-1
projected out), relative degree 3 verified with respect to the eight GFM channels, SG references under the original RDC, lambda = 2 s^-1, rate envelope = observed RDC maxima
(experimental candidate bound), physical P/Q/S/V barriers and GFM reference barriers.  The QP is updated every UPDATE_S seconds with the model refreshed at each update; between updates the
correction dv = v_QP - v_nom(t_update) is held and added to the current nominal rate (clipped to the envelope).  Protection starts at the instant fixed by the E9-F feasibility verdict of the
same case (first probe after which the state is in C_H and the QP feasible at every later probe); before it the nominal command is applied and nothing is claimed.
If at any update the nominal command violates a constraint and the QP is infeasible, the safety test STOPS at that instant: no elastic or relaxed solution is applied.
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
from scipy.optimize import linprog, minimize

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import e9a_hocbf as H  # noqa: E402
import e9a_linear as L  # noqa: E402
import e9f_engine as E  # noqa: E402
import run_b3_ieee39 as b  # noqa: E402
import run_e7_ieee39 as e7  # noqa: E402
import run_e8_ieee39 as e8  # noqa: E402
import run_e9f_feasibility as F  # noqa: E402
from e9b_variant import HOOK, TAG, VARIANT  # noqa: E402
from run_e0_ieee39 import ARTIFACTS_DIR, FIGURES_DIR, extract_time_series, git_commit, sha256  # noqa: E402

OUT = ARTIFACTS_DIR / f"IEEE39_E9G_b4{TAG}.json"
UPDATE_S = 0.1
HORIZON = 60.0
EVENT = 5.0
LAM = 2.0
PROJECT = 100.0
V_BAND = (0.95, 1.05)


class StopSafety(Exception):
    pass


class QPFilter:
    def __init__(self, name: str, dist: E.Disturbance | None, t_protect: float):
        self.name, self.dist, self.t_protect = name, dist, t_protect
        self.vref = np.concatenate([np.full(4, F.ENVELOPE[name][0]), np.full(4, F.ENVELOPE[name][1])])
        self.next_update = t_protect
        self.dv = np.zeros(8)
        self.log: list[dict[str, Any]] = []
        self.stopped: dict[str, Any] | None = None

    def fn(self, t, sys_, ctx, st, vnom_p, vnom_q):
        vp, vq = np.array(vnom_p, float), np.array(vnom_q, float)
        if t < self.t_protect:
            return vp, vq
        v_nom = np.concatenate([vp[6:10], vq[6:10]])
        if t >= self.next_update - 1e-9:
            self.update(t, sys_, ctx, st, v_nom)
            self.next_update += UPDATE_S
        v = np.clip(v_nom + self.dv, -self.vref, self.vref)
        vp[6:10], vq[6:10] = v[:4], v[4:]
        return vp, vq

    def update(self, t, sys_, ctx, st, v_nom) -> None:
        t0 = time.perf_counter()
        lin = L.linearize(sys_, ctx)
        t_lin = time.perf_counter() - t0
        eng = E.Engine(sys_, ctx, st, lin, self.dist, t_now=float(t))
        proj = eng.project_fast(PROJECT)
        D = eng.jets(3, F.EPS1)
        coeff = eng.gfm_coefficients()
        pset, qset = np.asarray(st["pset"], float), np.asarray(st["qset"], float)
        A, b_, meta, A_ref, b_ref, meta_ref = E.hocbf_rows(D, coeff, ctx["lim"], LAM, pset, qset)
        eng.close()
        t_eng = time.perf_counter() - t0 - t_lin
        a_all, b_all = np.vstack([A, A_ref]), np.concatenate([b_, b_ref])
        names = [m["name"] for m in meta] + [m["name"] for m in meta_ref]
        a_s = a_all * self.vref[None, :]
        nrm = np.linalg.norm(a_s, axis=1)
        live = nrm > 1e-9
        dead_bad = [names[i] for i in np.where(~live & (b_all > 0))[0]]
        a_n, b_n = a_s[live] / nrm[live, None], b_all[live] / nrm[live]
        ln = [n for n, l in zip(names, live) if l]
        w_nom = np.clip(v_nom / self.vref, -1, 1)
        slack = a_n @ w_nom - b_n
        rec: dict[str, Any] = {"t_s": float(t), "n_outside_CH": int(sum(1 for m in meta if not m["inside"])), "h_negative": [m["name"] for m in meta if m["h0"] < 0], "dead_rows_requiring_action": dead_bad,
                               "nominal_violated_rows": int((slack < -1e-12).sum()), "min_nominal_slack": float(slack.min()), "relative_degree_3": coeff["relative_degree_3_all_outputs"],
                               "projection_fast_modes": proj["n_fast_modes"], "t_linearize_s": t_lin, "t_engine_s": t_eng}
        t1 = time.perf_counter()
        feasible = True
        if np.any(slack < -1e-12) or dead_bad:
            res = minimize(lambda w: 0.5 * np.sum((w - w_nom) ** 2), w_nom, jac=lambda w: w - w_nom, bounds=[(-1, 1)] * 8,
                           constraints=[{"type": "ineq", "fun": lambda w: a_n @ w - b_n, "jac": lambda w: a_n}], method="SLSQP", options={"maxiter": 100, "ftol": 1e-12})
            viol = float(max(0.0, (b_n - a_n @ res.x).max()))
            if viol > 1e-7 or dead_bad:
                # independent confirmation of infeasibility by LP before stopping
                c = np.zeros(9); c[-1] = 1.0
                lp = linprog(c, A_ub=np.hstack([-a_n, -np.ones((a_n.shape[0], 1))]), b_ub=-b_n, bounds=[(-1, 1)] * 8 + [(0, None)], method="highs")
                feasible = bool(lp.status == 0 and lp.x[-1] <= 1e-9 and not dead_bad)
                if feasible:
                    res_w = lp.x[:8]
                    dv = res_w * self.vref - v_nom
                else:
                    srt = np.argsort(lp.x[:8] @ a_n.T - b_n) if lp.status == 0 else np.arange(3)
                    rec["conflict_rows"] = [ln[i] for i in srt[:4]]
                    rec["elastic_violation"] = float(lp.x[-1]) if lp.status == 0 else None
                    rec["feasible"] = False
                    rec["t_qp_s"] = time.perf_counter() - t1
                    self.log.append(rec)
                    self.stopped = {"t_s": float(t), "cause": "QP infeasible with the nominal command violating a hard constraint (no relaxation applied)", "conflict_rows": rec["conflict_rows"],
                                    "elastic_violation": rec["elastic_violation"], "n_outside_CH": rec["n_outside_CH"], "dead_rows": dead_bad}
                    raise StopSafety(f"QP infeasible at t = {t:.3f} s")
            else:
                dv = res.x * self.vref - v_nom
            self.dv = dv
            rec["active"] = True
            rec["dv_norm_normalized"] = float(np.linalg.norm(dv / self.vref))
            rec["dv_max_abs"] = float(np.abs(dv).max())
        else:
            self.dv = np.zeros(8)
            rec["active"] = False
            rec["dv_norm_normalized"] = 0.0
            rec["dv_max_abs"] = 0.0
        rec["feasible"] = True
        rec["t_qp_s"] = time.perf_counter() - t1
        self.log.append(rec)


def unit_arrays(d):
    ids = list(d["bus_ids"])
    cols = [ids.index(bb) for bb in d["unit_bus_ids"]]
    return np.hstack([d["sg_p_pu"], d["gfm_p_pu"]]), np.hstack([d["sg_q_pu"], d["gfm_q_pu"]]), d["bus_voltage_pu"][:, cols]


def run_one(name: str, t_protect: float) -> dict[str, Any]:
    sc, dist = F.CASES[name]
    cap: dict[str, Any] = {}

    def hook(system, ctx):
        HOOK(system, ctx)
        system.TDS.config.tf = HORIZON
        cap["sys"], cap["ctx"] = system, ctx

    t0 = time.perf_counter()
    _, d2, diag2 = b.run("B2", sc, init_hook=hook, dist_fn=F.make_dist_fn(dist))
    t_b2 = time.perf_counter() - t0
    lim = cap["ctx"]["lim"]
    flt = QPFilter(name, dist, t_protect)
    stopped_exc = None
    t0 = time.perf_counter()
    try:
        _, d4, diag4 = b.run("B2", sc, init_hook=hook, dist_fn=F.make_dist_fn(dist), qp_filter={"fn": flt.fn})
    except StopSafety as exc:
        stopped_exc = str(exc)
        d4 = extract_time_series(cap["sys"])
        s = cap["sys"]
        yy = s.dae.ts.y
        d4["sg_p_pu"], d4["sg_q_pu"] = np.asarray(yy[:, s.GENROU.Pe.a], float), np.asarray(yy[:, s.GENROU.Qe.a], float)
        d4["gfm_p_pu"], d4["gfm_q_pu"] = np.asarray(yy[:, s.REGF1.Pe.a], float), np.asarray(yy[:, s.REGF1.Qe.a], float)
        d4["bus_ids"] = np.asarray(d2["bus_ids"]); d4["unit_bus_ids"] = np.asarray(d2["unit_bus_ids"])
        diag4 = {"tds_ok": False, "stopped": True}
    t_b4 = time.perf_counter() - t0

    def metrics(d) -> dict[str, Any]:
        t = d["time_s"]
        p, q, v = unit_arrays(d)
        vb = d["bus_voltage_pu"]
        s_rel = 1 - np.hypot(p, q) / lim["smax"]
        return {"t_end_s": float(t[-1]), "min_P_margin_pu": (lim["pmax"] - p).min(axis=0).tolist(), "min_Q_margin_pu": np.minimum(lim["qmax"] - q, q - lim["qmin"]).min(axis=0).tolist(), "min_S_rel_margin": s_rel.min(axis=0).tolist(),
                "bus_voltage_min_pu": float(vb.min()), "bus_voltage_max_pu": float(vb.max()), "min_voltage_margin_to_band_pu": float(np.minimum(vb - V_BAND[0], V_BAND[1] - vb).min()),
                "n_buses_ever_outside_band": int(((vb < V_BAND[0]) | (vb > V_BAND[1])).any(axis=0).sum()),
                "violating_units": [i for i in range(10) if (p[:, i].max() > lim["pmax"][i] or p[:, i].min() < lim["pmin"][i] or q[:, i].max() > lim["qmax"][i] or q[:, i].min() < lim["qmin"][i] or s_rel[:, i].min() < 0)],
                "frequency_nadir_hz": float(d["bus_frequency_hz"].mean(axis=1).min()), "frequency_max_dev_hz": float(np.abs(d["bus_frequency_hz"].mean(axis=1) - 60.0).max()),
                "max_cmd_z": float(np.abs(d["cmd_z"]).max()) if "cmd_z" in d else None}
    m2, m4 = metrics(d2), metrics(d4)
    n = min(len(d2["time_s"]), len(d4["time_s"]))
    p2, q2, v2 = unit_arrays(d2)
    p4, q4, v4 = unit_arrays(d4)
    pre = d2["time_s"][:n] < t_protect
    diff = {"max_abs_frequency_diff_hz": float(np.abs(d2["bus_frequency_hz"][:n] - d4["bus_frequency_hz"][:n]).max()), "max_abs_voltage_diff_pu": float(np.abs(d2["bus_voltage_pu"][:n] - d4["bus_voltage_pu"][:n]).max()),
            "max_abs_P_diff_pu": float(np.abs(p2[:n] - p4[:n]).max()), "max_abs_Q_diff_pu": float(np.abs(q2[:n] - q4[:n]).max()),
            "max_abs_diff_before_protection_start": float(max(np.abs(p2[:n][pre] - p4[:n][pre]).max() if pre.any() else 0.0, np.abs(d2["bus_voltage_pu"][:n][pre] - d4["bus_voltage_pu"][:n][pre]).max() if pre.any() else 0.0))}
    log = flt.log
    cost = {"updates": len(log), "t_linearize_mean_s": float(np.mean([r["t_linearize_s"] for r in log])) if log else None, "t_engine_mean_s": float(np.mean([r["t_engine_s"] for r in log])) if log else None,
            "t_qp_mean_s": float(np.mean([r["t_qp_s"] for r in log])) if log else None, "t_qp_max_s": float(np.max([r["t_qp_s"] for r in log])) if log else None,
            "t_update_total_mean_s": float(np.mean([r["t_linearize_s"] + r["t_engine_s"] + r["t_qp_s"] for r in log])) if log else None, "control_period_s": e8.TIME_STEP_S, "filter_update_period_s": UPDATE_S,
            "wall_B2_s": t_b2, "wall_B4_s": t_b4}
    out = {"case": name, "scenario": sc, "disturbance": None if dist is None else {"kind": dist.kind, "amplitude_pu": dist.amp, "profile": "quintic C2 ramp 5 s"}, "t_protect_s": t_protect,
           "B2": m2, "B4": m4, "difference_B4_minus_B2": diff, "stopped": flt.stopped, "stop_exception": stopped_exc,
           "qp": {"n_updates": len(log), "n_active": int(sum(1 for r in log if r.get("active"))), "n_infeasible": int(sum(1 for r in log if not r.get("feasible", True))),
                  "max_dv_abs_pu_per_s": float(max([r["dv_max_abs"] for r in log if "dv_max_abs" in r], default=0.0)), "active_times_s": [r["t_s"] for r in log if r.get("active")][:60],
                  "n_outside_CH_max": int(max([r["n_outside_CH"] for r in log], default=0)), "relative_degree_3_all_updates": bool(all(r["relative_degree_3"] for r in log)) if log else None},
           "cost": cost, "diag_B2": diag2, "diag_B4": diag4, "log_head": log[:3], "log_tail": log[-3:]}
    plot_case(name, d2, d4, flt, lim, t_protect)
    print(f"{name}: stopped={flt.stopped is not None} updates={len(log)} active={out['qp']['n_active']} infeasible={out['qp']['n_infeasible']} max|dV|={diff['max_abs_voltage_diff_pu']:.2e} max|df|={diff['max_abs_frequency_diff_hz']:.2e} "
          f"B2viol={m2['violating_units']} B4viol={m4['violating_units']} update={cost['t_update_total_mean_s']}", flush=True)
    return out


def plot_case(name, d2, d4, flt, lim, t_protect) -> None:
    fig, ax = plt.subplots(2, 3, figsize=(19, 9))
    for d, ls, lb in ((d2, "-", "B2"), (d4, "--", "B4")):
        t = d["time_s"]
        ax[0, 0].plot(t, d["bus_frequency_hz"].mean(axis=1) - 60.0, ls, label=lb)
        ax[0, 1].plot(t, d["bus_voltage_pu"].max(axis=1), ls, label=f"{lb} max"); ax[0, 1].plot(t, d["bus_voltage_pu"].min(axis=1), ls, lw=.8, label=f"{lb} min")
        p, q, v = unit_arrays(d)
        ax[0, 2].plot(t, p[:, 1], ls, label=f"{lb} P SG31"); ax[0, 2].plot(t, p[:, 3], ls, label=f"{lb} P SG35"); ax[0, 2].plot(t, p[:, 9], ls, label=f"{lb} P GFM36")
        ax[1, 0].plot(t, (lim["pmax"] - p).min(axis=1), ls, label=f"{lb} min(pmax-P)"); ax[1, 0].plot(t, (1 - np.hypot(p, q) / lim["smax"]).min(axis=1), ls, label=f"{lb} min S rel")
        if "cmd_pset" in d:
            ax[1, 1].plot(d["cmd_t"], d["cmd_pset"][:, 6:] - d["unit_pn"][6:], ls, lw=.9)
    ax[0, 1].axhline(1.05, color="k", ls=":", lw=.8); ax[0, 1].axhline(0.95, color="k", ls=":", lw=.8)
    ax[0, 2].axhline(lim["pmax"][1], color="r", ls=":", lw=.6); ax[0, 2].axhline(lim["pmax"][3], color="r", ls=":", lw=.6)
    tt = [r["t_s"] for r in flt.log]
    ax[1, 2].plot(tt, [r["dv_norm_normalized"] for r in flt.log], "o-", ms=2, label="||dv||/v_ref (QP correction)")
    ax[1, 2].plot(tt, [r["nominal_violated_rows"] for r in flt.log], "s-", ms=2, label="rows violated by the nominal command"); ax[1, 2].plot(tt, [r["n_outside_CH"] for r in flt.log], "^-", ms=2, label="barriers outside C_H")
    for a in ax.ravel():
        a.axvline(t_protect, color="g", ls=":", lw=.9); a.axvline(EVENT, color="tab:red", ls=":", lw=.8); a.grid(alpha=.25); a.set_xlabel("Time [s]")
    ax[0, 0].set_title("mean bus frequency - 60 Hz"); ax[0, 1].set_title("39-bus voltage extremes"); ax[0, 2].set_title("physical P (dotted red: pmax SG31, SG35)")
    ax[1, 0].set_title("physical margins"); ax[1, 1].set_title("GFM Pset - Pn (B2 solid, B4 dashed)"); ax[1, 2].set_title("QP intervention and feasibility indicators")
    for a in (ax[0, 0], ax[0, 1], ax[0, 2], ax[1, 0], ax[1, 2]):
        a.legend(fontsize=6)
    fig.suptitle(f"E9-G {name}: B2 vs B4 (HOCBF-QP on the GFM rates) on {VARIANT}; green dotted: protection start; stopped: {flt.stopped is not None}"); fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"IEEE39_E9G_{name.replace(' ', '_').replace('+', 'p')}{TAG}.png", dpi=300, bbox_inches="tight"); plt.close(fig)


def main() -> int:
    feas = json.loads((ARTIFACTS_DIR / f"IEEE39_E9F_feasibility{TAG}_slow.json").read_text(encoding="utf-8"))
    names = sys.argv[1:] or list(F.CASES)
    result: dict[str, Any] = {"variant": VARIANT, "git_commit": git_commit(), "andes": andes.__version__, "python": platform.python_version(), "lambda": LAM, "update_period_s": UPDATE_S, "horizon_s": HORIZON,
                              "projection_lambda_c": PROJECT, "doc": __doc__, "cases": {}}
    for n in names:
        start = feas["cases"][n]["verdict"]["protection_may_start_at_s_after_event"]
        t_prot = EVENT if n == "S0" else EVENT + float(start)
        result["cases"][n] = run_one(n, t_prot)
        OUT.write_text(json.dumps(result, indent=2, default=float), encoding="utf-8")
    result["code_sha256"] = {f: sha256(Path(__file__).parent / f) for f in ("run_e9g_b4.py", "e9f_engine.py", "run_e9f_feasibility.py", "e9a_linear.py", "e9a_hocbf.py", "run_b3_ieee39.py")}
    OUT.write_text(json.dumps(result, indent=2, default=float), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
