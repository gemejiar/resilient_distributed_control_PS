"""DEC-059 per-run metrics (protocol: G-R3 criteria and the predefined K7 comparison metrics) for any DEC-059 run; pure post-processing of stored runs.
  <venv python> dec059_metrics.py <run_id> [<run_id> ...]          prints the metrics
  dec059_metrics.collect(run_ids, out_name)                          writes artifacts/<out_name>.json exclusively"""
from __future__ import annotations

import json
import sys

import numpy as np

import dec055_common as C55
import dec059_tds as T

TE = T.TE
U_D8 = 0.0109


def _load(run):
    d = T.RUNS / run
    return (dict(np.load(d / "series.npz", allow_pickle=True)), json.loads((d / "status.json").read_text(encoding="utf-8")),
            json.loads((d / "config.json").read_text(encoding="utf-8")), json.loads((d / "diag.json").read_text(encoding="utf-8")) if (d / "diag.json").exists() else {})


def window(t, y, a, b):
    k = (t >= a) & (t <= b)
    return y[k].mean(axis=0)


def metrics(run, lim=None):
    z, st, cfg, diag = _load(run)
    t = z["t"]
    out = {"run_id": run, "status": st["status"], "t_end": float(t[-1]), "controller": cfg.get("controller"), "oc": cfg["oc"], "scenario": cfg["scenario"]}
    if lim is None:
        import dec055_oc as OCM
        lim = OCM.make_plant(cfg["oc"]).limits
    P, Q, V = z["P"], z["Q"], z["V"]
    pn = z["unit_pn"]
    fc = z["f_coi_hz"] if "f_coi_hz" in z and len(z["f_coi_hz"]) == len(t) else z["f_bus_hz"].mean(axis=1)
    post = t >= TE - 1e-12
    out["f_coi_nadir_hz"] = float(fc[post].min())
    k100 = (t >= TE) & (t <= TE + 0.1)
    out["rocof_100ms_hz_s"] = float(np.polyfit(t[k100], fc[k100], 1)[0]) if k100.sum() > 3 else None
    for tt in (120.0, 200.0):
        if t[-1] >= tt - 1e-9:
            out[f"f_err_{int(tt)}s_hz"] = float(window(t, fc, tt - 2, tt + 1e-9) - 60.0)
    bad = np.where(np.abs(fc - 60.0) > 0.01)[0]
    out["settle_0p01Hz_s"] = float(t[bad[-1]] - TE) if bad.size and t[bad[-1]] > TE else 0.0
    # unit-bus voltages: bus columns (index = bus id - 1) in the UNITS order of dec054_common.UNIT_BUS (checked against the targets to 2e-15)
    import dec054_common as C54
    vu = V[:, [b - 1 for b in C54.UNIT_BUS]]
    v_set = vu[0]
    vend = window(t, vu, t[-1] - 2, t[-1] + 1e-9)
    out["unit_V_err_end_vs_setpoint"] = {"mean": float(np.abs(vend - v_set).mean()), "max": float(np.abs(vend - v_set).max())}
    out["unit_V_err_end_vs_1pu"] = {"mean": float(np.abs(vend - 1.0).mean()), "max": float(np.abs(vend - 1.0).max())}
    out["V_bus_min"], out["V_bus_max"] = float(V[post].min()), float(V[post].max())
    pend = window(t, P, t[-1] - 2, t[-1] + 1e-9)
    ratio = (pend - pn) / pn
    out["P_end"] = pend.tolist()
    # physical margins (stored samples; within 50 ms: U_D8 band)
    mp = lim["pmax"][None, :] - P
    k50 = (t >= TE - 1e-12) & (t <= TE + 0.05)
    out["pmax_margin_min"] = float(mp[post].min())
    out["pmax_margin_min_50ms"] = float(mp[k50].min()) if k50.any() else None
    out["pmax_margin_min_after_50ms"] = float(mp[t > TE + 0.05].min())
    out["pmin_margin_min"] = float((P - lim["pmin"][None, :])[post].min())
    out["qmax_margin_min"] = float((lim["qmax"][None, :] - Q)[post].min())
    out["qmin_margin_min"] = float((Q - lim["qmin"][None, :])[post].min())
    out["s_margin_min"] = float((lim["smax"][None, :] - np.hypot(P, Q))[post].min())
    m = out["pmax_margin_min_50ms"]
    out["pmax_50ms_class"] = None if m is None else ("SAFE" if m >= U_D8 else "UNSAFE" if m <= -U_D8 else "NUMERICALLY_INDETERMINATE")
    if "b5_t" in z:
        out["b5"] = {"calls": int(len(z["b5_t"])), "paths": np.bincount(z["b5_path"].astype(int), minlength=3).tolist(), "c_min": float(z["b5_c_min"].min()),
                     "slack_max": float(np.nanmax(z["b5_slack"])), "slack_positive": int((z["b5_slack"] > 1e-12).sum()), "cpu_mean_ms": float(1e3 * z["b5_cpu"].mean()),
                     "cpu_max_ms": float(1e3 * z["b5_cpu"].max()), "V_post_first": None, "V_end": float(z["b5_V"][-1]) if np.isfinite(z["b5_V"][-1]) else None}
        Vv = z["b5_V"]
        ok = np.isfinite(Vv)
        if ok.any():
            tv = z["b5_t"][ok]
            out["b5"]["V_post_first"] = float(Vv[ok][0])
            out["b5"]["V_ratio_end_over_first_valid"] = float(Vv[ok][-1] / Vv[ok][0]) if Vv[ok][0] > 0 else None
        b5c = cfg.get("b5", {})
        tgt = b5c.get("post_target") or b5c.get("pre_target")
        if tgt:
            Tg = dict(np.load(tgt))
            u_end = np.concatenate([z["end_pset"], z["end_qset"]])
            out["target"] = {"u_end_minus_ustar_max": float(np.abs(u_end - Tg["u"]).max()), "P_end_minus_Pstar_max": float(np.abs(pend - Tg["P"]).max()),
                             "unitV_end_minus_Vstar_max": float(np.abs(vend - Tg["V"]).max())}
            Ast = json.loads(open(tgt.replace(".npz", ".json"), encoding="utf-8").read())
            pinned = [C55.UNITS.index(u) for u in Ast["A_set"]]
            free = [i for i in range(10) if i not in pinned]
            out["sharing_std_free_units_end"] = float(np.std(ratio[free])) if len(free) > 1 else None
            out["target_labels"] = {"E4": Ast["E4"]["pass"], **{k: v["pass"] for k, v in Ast["T2"].items()}, "A_set": Ast["A_set"]}
    else:
        out["sharing_std_all_units_end"] = float(np.std(ratio))
    return out


def classify(m):
    """Addendum B item 1.  Returns (class, reasons).  TDS failure is reported apart."""
    if m["status"] == "TDS_NUMERICAL_FAILURE" or m["t_end"] < 199.99:
        return "TDS_NUMERICAL_FAILURE", ["run did not reach 200 s"]
    why = []
    m50 = m["pmax_margin_min_50ms"]
    cls = "SAFE"
    if m50 <= -U_D8:
        cls = "UNSAFE"
        why.append(f"P peak margin within 50 ms {m50:.4f} <= -U_D8")
    elif m50 < U_D8:
        cls = "NUMERICALLY_INDETERMINATE"
        why.append(f"|P peak margin within 50 ms| {m50:.4f} < U_D8")
    binary = {"Pmax after 50 ms": m["pmax_margin_min_after_50ms"], "Pmin": m["pmin_margin_min"], "Qmax": m["qmax_margin_min"], "Qmin": m["qmin_margin_min"], "S": m["s_margin_min"],
              "Vmin-0.95": m["V_bus_min"] - 0.95, "1.05-Vmax": 1.05 - m["V_bus_max"]}
    for k, v in binary.items():
        if v < 0:
            cls = "UNSAFE"
            why.append(f"{k} margin {v:.4f} < 0")
    return cls, why


def gr3(m):
    """G-R3 acceptance on one smoke run (protocol)."""
    c = {"no_tds_failure": m["status"] != "TDS_NUMERICAL_FAILURE" and m["t_end"] >= 199.99,
         "T1_reference_margins_nonneg": m.get("b5", {}).get("c_min", -1) >= 0,
         "QP_no_fallback": m.get("b5", {}).get("paths", [0, 0, 1])[2] == 0}
    if "target" in m:
        c["converged_f_AC05"] = abs(m.get("f_err_200s_hz", 1.0)) <= 0.01
        c["converged_unitV_vs_target_1e-3"] = m["target"]["unitV_end_minus_Vstar_max"] <= 1e-3
        c["sharing_std_1e-3"] = (m.get("sharing_std_free_units_end") or 0.0) <= 1e-3
    return c


def collect(runs, out_name):
    res = {}
    for r in runs:
        m = metrics(r)
        m["G_R3"] = gr3(m)
        m["class"], m["class_reasons"] = classify(m)
        res[r] = m
    with open(C55.ART / f"{out_name}.json", "x", encoding="utf-8") as f:
        json.dump(res, f, indent=1, default=float)
    return res


if __name__ == "__main__":
    for r in sys.argv[1:]:
        m = metrics(r)
        m["G_R3"] = gr3(m)
        print(json.dumps({k: v for k, v in m.items() if k != "P_end"}, indent=1, default=float))
