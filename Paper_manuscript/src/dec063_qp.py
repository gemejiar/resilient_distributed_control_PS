"""DEC-063: differential analysis of the QP (B5' vs B4' vs B2/B1s) from EXISTING DEC-062 TEST runs.  No TDS, no controller/dispatch/criterion change.
Builds the reference set W of each (OC, dispatch) with a power flow only (dec059_eq.Eq, no time-domain simulation) and evaluates, for the commanded references u(t) = (cmd_pset, cmd_qset) of every run,
  - the reference margins c_j(u(t)) (T1 quantity) also for B2 and B1s, which have no barrier filter  -> does the barrier filter prevent reference-set violations?
  - the QP activity logged by B5'/B4' (fast path vs solver, soft-CLF slack, |v - v_nom|) and the window in which it occurs;
  - the B5' - B4' trajectory differences (commands, f_COI, unit voltages).
Writes IEEE39_DEC063_qp_analysis.json exclusively (argument 'write').  Multipliers are NOT logged by the controller: the analysis states what it can and cannot resolve."""
from __future__ import annotations

import json
import sys

import numpy as np

import dec055_common as C55
import dec059_b5 as B5
import dec059_eq as EQ
import dec059_tds as T

TE = 5.0


def parse(run):
    p = run.split("_")
    return {"kind": p[0], "ctl": p[1], "oc": p[2], "disp": p[3], "cell": "_".join(p[4:])}


def stats_ref(rs, P, Q, t):
    u = np.hstack([P, Q])
    ca = u @ rs["A"].T + rs["b"][None, :]
    cd = rs["s"][None, :] ** 2 - P ** 2 - Q ** 2
    m = np.minimum(ca.min(axis=1), cd.min(axis=1))
    k = int(m.argmin())
    names = list(rs["names"])
    rows = ca[k].argmin() if ca[k].min() <= cd[k].min() else None
    return {"min_c": float(m.min()), "t_min": float(t[k]), "n_neg": int((m < -1e-12).sum()), "row_at_min": (names[rows] if rows is not None else f"disc {int(cd[k].argmin())}"),
            "min_c_after_event": float(m[t >= TE].min())}


def main(write=False):
    runs = sorted(p.name for p in T.RUNS.iterdir() if p.name.startswith(("D62TEST_", "D62CMP_")))
    cache, out = {}, {"label": "DEC063_ANALYSIS_OF_EXISTING_RUNS_NO_TDS", "runs": {}}
    series = {}
    for r in runs:
        pr = parse(r)
        key = (pr["oc"], pr["disp"])
        if key not in cache:
            e = EQ.Eq(pr["oc"], T.dispatch_z(pr["oc"], pr["disp"]))
            cache[key] = EQ.refset(e.ctx, e.st)
        rs = cache[key]
        z = np.load(T.RUNS / r / "series.npz", allow_pickle=True)
        t = z["cmd_t"]
        d = {"ctl": pr["ctl"], "oc": pr["oc"], "disp": pr["disp"], "cell": pr["cell"], "ref_margin": stats_ref(rs, z["cmd_pset"], z["cmd_qset"], t)}
        if "b5_path" in z.files:
            tp, pa, sl, dv, V = z["b5_t"], z["b5_path"], z["b5_slack"], z["b5_dv"], z["b5_V"]
            sol = pa == 1
            d["qp"] = {"calls": int(len(tp)), "solver": int(sol.sum()), "fallback": int((pa == 2).sum()), "slack_pos": int((sl > 1e-12).sum()), "slack_max": float(sl.max()), "dv_max": float(dv.max()),
                       "t_first_solver": float(tp[sol].min()) if sol.any() else None, "t_last_solver": float(tp[sol].max()) if sol.any() else None,
                       "last_solver_after_event_s": float(tp[sol].max() - TE) if sol.any() else None, "dv_int": float(np.sum(dv) * (tp[1] - tp[0]) if len(tp) > 1 else 0.0),
                       "slack_pos_t": ([float(tp[sl > 1e-12].min()), float(tp[sl > 1e-12].max())] if (sl > 1e-12).any() else None)}
            if np.isfinite(V).any():
                d["qp"]["V_first_valid"] = float(V[np.isfinite(V)][0])
        if "b1s_clipped" in z.files:
            d["b1s"] = {"clipped_calls": int((z["b1s_clipped"] > 0).sum()), "calls": int(len(z["b1s_t"]))}
        out["runs"][r] = d
        series[r] = {"t": t, "P": z["cmd_pset"], "Q": z["cmd_qset"], "fc": z["f_coi_hz"], "tt": z["t"], "V": z["V"]}
    # B5' vs B4' pairs (identical event, dispatch, solver, information; only the CLF row differs)
    pairs = {}
    for r in runs:
        if "_B4P_" in r:
            r5 = "D62TEST_B5P_" + r.split("_B4P_")[1]
            a, b = series[r5], series[r]
            n = min(len(a["t"]), len(b["t"]))
            dP, dQ = np.abs(a["P"][:n] - b["P"][:n]), np.abs(a["Q"][:n] - b["Q"][:n])
            m = min(len(a["fc"]), len(b["fc"]))
            pairs[r.split("_B4P_")[1]] = {"max_dP_cmd": float(dP.max()), "max_dQ_cmd": float(dQ.max()), "max_dfcoi_hz": float(np.abs(a["fc"][:m] - b["fc"][:m]).max()),
                                          "max_dV_pu": float(np.abs(a["V"][:m] - b["V"][:m]).max()), "t_of_max_dP": float(a["t"][int(dP.max(axis=1).argmax())]),
                                          "B5P_solver": out["runs"][r5]["qp"]["solver"], "B4P_solver": out["runs"][r]["qp"]["solver"], "B5P_slack_pos": out["runs"][r5]["qp"]["slack_pos"],
                                          "B4P_slack_pos": out["runs"][r]["qp"]["slack_pos"], "B5P_dv_max": out["runs"][r5]["qp"]["dv_max"], "B4P_dv_max": out["runs"][r]["qp"]["dv_max"]}
    out["B5P_vs_B4P_pairs"] = pairs
    b5 = [v for k, v in out["runs"].items() if v["ctl"] == "B5P"]
    out["summary_B5P_36_runs"] = {"n": len(b5), "runs_with_solver": sum(v["qp"]["solver"] > 0 for v in b5), "max_last_solver_after_event_s": max((v["qp"]["last_solver_after_event_s"] or 0) for v in b5),
                                  "runs_with_positive_slack": sum(v["qp"]["slack_pos"] > 0 for v in b5), "min_ref_margin": min(v["ref_margin"]["min_c"] for v in b5)}
    noq = {c: [(k.split("_")[-3] if False else k, v["ref_margin"]["min_c"], v["ref_margin"]["n_neg"], v["ref_margin"]["row_at_min"]) for k, v in out["runs"].items() if v["ctl"] == c] for c in ("B2", "B1S")}
    out["no_filter_reference_margins"] = noq
    print(json.dumps(out["summary_B5P_36_runs"], indent=1))
    print(json.dumps(pairs, indent=1)[:3500])
    for c, v in noq.items():
        print(c, [(x[0].split("_", 2)[-1], round(x[1], 4), x[2]) for x in v])
    print({k: (v["ctl"], v["disp"], v["cell"], v["qp"]["solver"], v["qp"]["slack_pos"], round(v["qp"]["dv_max"], 3), v["qp"]["last_solver_after_event_s"]) for k, v in out["runs"].items() if "qp" in v})
    if write:
        with open(C55.ART / "IEEE39_DEC063_qp_analysis.json", "x", encoding="utf-8") as f:
            json.dump(out, f, indent=1, default=float)




def binding(write=False):
    """Which QP rows can bind?  Box rows c_j(u) = A_j u + b_j bind only if c_j < vbar_k / alpha (largest allowed rate of decrease is vbar_k).  Also: fraction of solver calls with the rate box saturated."""
    runs = sorted(p.name for p in T.RUNS.iterdir() if p.name.startswith("D62TEST_B5P_") or p.name.startswith("D62CMP_B4P_"))
    cache, res = {}, {}
    for r in runs:
        pr = parse(r)
        key = (pr["oc"], pr["disp"])
        if key not in cache:
            e = EQ.Eq(pr["oc"], T.dispatch_z(pr["oc"], pr["disp"]))
            cache[key] = EQ.refset(e.ctx, e.st)
        rs = cache[key]
        z = np.load(T.RUNS / r / "series.npz", allow_pickle=True)
        t, P, Q = z["cmd_t"], z["cmd_pset"], z["cmd_qset"]
        w = (t >= TE) & (t <= TE + 5.0)
        u = np.hstack([P, Q])[w]
        ca = u @ rs["A"].T + rs["b"][None, :]
        col = np.abs(rs["A"]).argmax(axis=1)
        gap = ca - rs["vbar"][col][None, :] / B5.ALPHA                  # > 0: the barrier row cannot bind for any |v| <= vbar
        k = int(np.unravel_index(gap.argmin(), gap.shape)[1])
        pa, vv = z["b5_path"], z["b5_v"]
        sol = pa == 1
        sat = (np.abs(vv) >= rs["vbar"][None, :] * (1 - 1e-6)).any(axis=1)
        res[r] = {"min_gap_box_rows": float(gap.min()), "row_of_min_gap": rs["names"][k], "box_rows_can_bind": bool(gap.min() < 0), "n_solver": int(sol.sum()),
                  "solver_with_rate_box_saturated": int((sat & sol).sum()), "fast_with_rate_box_saturated": int((sat & ~sol).sum()), "disc_min_c": float((rs["s"][None, :] ** 2 - P[w] ** 2 - Q[w] ** 2).min())}
    sm = {"n_runs": len(res), "box_rows_can_bind_runs": [r for r, v in res.items() if v["box_rows_can_bind"]], "min_gap_overall": min(v["min_gap_box_rows"] for v in res.values()),
          "frac_solver_calls_with_rate_box_saturated": sum(v["solver_with_rate_box_saturated"] for v in res.values()) / sum(v["n_solver"] for v in res.values())}
    print(json.dumps(sm, indent=1))
    print({r.split("_", 2)[2]: (round(v["min_gap_box_rows"], 4), v["row_of_min_gap"], v["solver_with_rate_box_saturated"], v["n_solver"], round(v["disc_min_c"], 3)) for r, v in res.items()})
    if write:
        with open(C55.ART / "IEEE39_DEC063_qp_binding.json", "x", encoding="utf-8") as f:
            json.dump({"summary": sm, "runs": res}, f, indent=1, default=float)


if __name__ == "__main__":
    (binding if "binding" in sys.argv else main)("write" in sys.argv)
