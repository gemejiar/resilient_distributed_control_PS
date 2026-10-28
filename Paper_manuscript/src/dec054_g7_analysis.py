"""DEC-054 G7: scientific comparison of M0-M3 on the frozen prospective cohort (post-processing of stored runs; NO TDS).
Outputs (exclusive): IEEE39_DEC054_prospective_tests.csv, _prospective_summary.json, _physical_compliance.csv, _dispatches.csv, _cut_log.csv.
`analyze_run` can also be used on other stored runs (e.g. P3-B) as a dry test of the code path."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

import dec054_common as COM

UN = COM.UNITS
METHODS = ("M0", "M1", "M2", "M3")


def freq_metrics(t, f):
    t = np.asarray(t, float)
    fm = np.asarray(f, float).mean(axis=1)                        # unweighted mean of the 39 BusFreq signals (NOT a COI)
    post = t >= 5.0 - 1e-9
    dt = float(np.median(np.diff(t)))
    k = max(int(round(0.1 / dt)), 1)
    sm = np.convolve(fm, np.ones(k) / k, mode="same")
    ro = np.gradient(sm, t)
    return {"f_nadir_Hz": float(fm[post].min()), "f_zenith_Hz": float(fm[post].max()), "f_final_error_Hz": float(fm[t >= t[-1] - 5.0].mean() - 60.0),
            "rocof_filtered_max_Hz_s": float(np.abs(ro[post][k:-k]).max()), "rocof_raw_max_Hz_s": float(np.abs(np.gradient(fm, t)[post]).max())}


def analyze_run(run_id, root=None):
    d = Path(root or COM.RUNS_DIR) / run_id
    st = json.loads((d / "status.json").read_text(encoding="utf-8"))
    out = {"run_id": run_id, "status": st["status"], "error": st.get("error")}
    if not (d / "series.npz").exists():
        return out
    z = np.load(d / "series.npz")
    met = json.loads((d / "metrics.json").read_text(encoding="utf-8"))
    t, P, V = z["t"], z["P"], z["V"]
    un = met["unit"]
    post = t >= 5.0 - 1e-9
    out.update({"n_violating_pairs_P": met["n_violating_pairs_P"], "V_outside_buses_any": met["V_outside_buses"], "V_outside_buses_post": met.get("V_outside_buses_post"),
                "V_min_post": met.get("V_min_post"), "V_max_post": met.get("V_max_post"), "E_share_P_vs_pn": met["E_share_P_vs_pn"],
                "unit": {nm: {k: un[nm][k] for k in ("min_margin", "max_excess", "t_violation_s", "violates")} for nm in un},
                "jump_excess_Pmax": met["jump_excess_Pmax"], "later_excess_Pmax": met["later_excess_Pmax"], "bus_V_min": V[post].min(axis=0).tolist(), "bus_V_max": V[post].max(axis=0).tolist(),
                "bus_V_pre": V[t < 5.0 - 1e-9][-1].tolist(), "P_pre": P[t < 5.0 - 1e-9][-1].tolist()})
    out.update(freq_metrics(t, z["f_bus_hz"]))
    return out


def main():
    import dec054_g4_design as G4
    frozen = json.loads((COM.ART / "IEEE39_DEC054_design_frozen.json").read_text(encoding="utf-8"))
    scen = frozen["scenarios_test"]["scenarios"]
    rows, runs = [], {}
    for s in scen:
        for m in METHODS:
            rid = f"P3-C_{s['name']}_{m}"
            r = analyze_run(rid)
            r.update({"method": m, "scenario": s["name"], "bus": s["bus"]})
            runs[rid] = r
            if "unit" not in r:
                continue
            for i, u in enumerate(UN):
                rows.append({"run_id": rid, "method": m, "scenario": s["name"], "bus": s["bus"], "unit": u, "P_pre_pu": r["P_pre"][i], "min_margin_Pmax_pu": r["unit"]["Pmax"]["min_margin"][i],
                             "min_margin_Pmin_pu": r["unit"]["Pmin"]["min_margin"][i], "min_margin_Qmax_pu": r["unit"]["Qmax"]["min_margin"][i], "min_margin_Qmin_pu": r["unit"]["Qmin"]["min_margin"][i],
                             "min_margin_Smax_pu": r["unit"]["Smax"]["min_margin"][i], "max_excess_Pmax_pu": r["unit"]["Pmax"]["max_excess"][i], "t_violation_Pmax_s": r["unit"]["Pmax"]["t_violation_s"][i],
                             "jump_excess_Pmax_pu": r["jump_excess_Pmax"][i], "later_excess_Pmax_pu": r["later_excess_Pmax"][i],
                             "violates_P": bool(r["unit"]["Pmax"]["violates"][i] or r["unit"]["Pmin"]["violates"][i])})
    with open(COM.ART / "IEEE39_DEC054_prospective_tests.csv", "x", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    summ = {}
    for m in METHODS:
        rr = [r for r in runs.values() if r["method"] == m]
        ok = [r for r in rr if "unit" in r]
        tot = float(sum(sum(r["unit"]["Pmax"]["max_excess"]) + sum(r["unit"]["Pmin"]["max_excess"]) for r in ok))
        mx = float(max([max(r["unit"]["Pmax"]["max_excess"] + r["unit"]["Pmin"]["max_excess"]) for r in ok] + [0.0]))
        summ[m] = {"n_runs": len(rr), "n_failed": len(rr) - len(ok), "status_counts": {s: sum(1 for r in rr if r["status"] == s) for s in COM.TDS_STATUS},
                   "violating_pairs_P": int(sum(r["n_violating_pairs_P"] for r in ok)), "scenarios_with_P_violation": int(sum(1 for r in ok if r["n_violating_pairs_P"] > 0)),
                   "total_P_excess_pu": tot, "max_P_excess_pu": mx,
                   "scenarios_with_Q_violation": int(sum(1 for r in ok if any(r["unit"][k]["violates"][i] for k in ("Qmax", "Qmin") for i in range(10)))),
                   "scenarios_with_S_violation": int(sum(1 for r in ok if any(r["unit"]["Smax"]["violates"]))), "scenarios_with_V_outside_post": int(sum(1 for r in ok if (r["V_outside_buses_post"] or 0) > 0)),
                   "mean_f_nadir_Hz": float(np.mean([r["f_nadir_Hz"] for r in ok])), "mean_rocof_filtered_Hz_s": float(np.mean([r["rocof_filtered_max_Hz_s"] for r in ok])),
                   "mean_E_share_vs_pn": float(np.mean([r["E_share_P_vs_pn"] for r in ok])), "design_J": frozen["dispatches"][m]["J"], "design_status": frozen["dispatches"][m]["status"]}
    with open(COM.ART / "IEEE39_DEC054_prospective_summary.json", "x", encoding="utf-8") as f:
        json.dump({"summary": summ, "runs": {k: {a: b for a, b in v.items() if a not in ("unit", "bus_V_min", "bus_V_max", "bus_V_pre")} for k, v in runs.items()}}, f, indent=1, default=float)
    with open(COM.ART / "IEEE39_DEC054_physical_compliance.csv", "x", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["run_id", "method", "scenario", "item_type", "item", "quantity", "pre_event", "post_min", "post_max_or_margin", "violates", "model_status"])
        for rid, r in runs.items():
            if "unit" not in r:
                continue
            for i, u in enumerate(UN):
                for q in ("Pmax", "Pmin", "Qmax", "Qmin", "Smax"):
                    w.writerow([rid, r["method"], r["scenario"], "unit", u, q, "", "", r["unit"][q]["min_margin"][i], bool(r["unit"][q]["violates"][i]), "APPROXIMATED (RMS case limit; not a capability curve)"])
            for b in range(39):
                v0, vmn, vmx = r["bus_V_pre"][b], r["bus_V_min"][b], r["bus_V_max"][b]
                w.writerow([rid, r["method"], r["scenario"], "bus", f"bus{b + 1}", "V", v0, vmn, vmx, bool(vmn < COM.VLO or vmx > COM.VHI), "MODELLED (0.95-1.05 pu band)"])
    with open(COM.ART / "IEEE39_DEC054_dispatches.csv", "x", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["method", "variable", "value", "design_J", "design_status"])
        for m in METHODS:
            e = frozen["dispatches"][m]
            for nm, v in zip(["p0_" + u for u in COM.PV_UNITS] + ["v0_" + u for u in COM.UNITS], e["z"]):
                w.writerow([m, nm, v, e["J"], e["status"]])
    with open(COM.ART / "IEEE39_DEC054_cut_log.csv", "x", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["method", "k", "scenario", "unit", "class", "margin", "note"])
        for m in ("m2", "m3"):
            st = G4.load_state(m) or {}
            for c in st.get("cuts", []):
                w.writerow([m.upper(), c["k"], c["scenario"], c["unit"], c["cut"][2], c["margin"], "static adaptive cut"])
            for lg in st.get("log", []):
                w.writerow([m.upper(), lg["k"], "", "", "", lg["min_margin"], f"round: W={lg['W']} J={lg['J']:.4f} most_violated={lg['most_violated']}"])
    print(json.dumps({m: {k: v for k, v in s.items() if k in ("violating_pairs_P", "scenarios_with_P_violation", "total_P_excess_pu", "design_J", "n_failed")} for m, s in summ.items()}, indent=1))


if __name__ == "__main__":
    main()
