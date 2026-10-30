"""DEC-066 A1/D: tables T4, T4b, T4c, T4d from IEEE39_DEC066_ablation_raw.json and the design states (0 TDS).
T4  A..E design summary + common external diagnostic over the 12 design events (no eps margin, dense+grid excursion) + internal margin with each variant's own eps.
T4b active / near-active constraints (internal margin < NEAR) and the effect of the dense term on them.
T4c predicted margins by window for the evaluation events (prediction register, written BEFORE any TDS).
T4d pairwise attribution B-A, C-B, D-C, E-A, D-E on design quantities (dispatch distance, J, margins).
Run: <venv python> dec066_abl_tables.py write"""
from __future__ import annotations

import csv
import json
import sys

import numpy as np

import dec054_common as C54
import dec054_g4_design as G4
import dec055_common as C55

ART = C55.ART
U_D8, NEAR = 0.0109, 1e-3
STATE = C54.RUNS_DIR.parent
SRC = {"A": STATE / "DEC055_state" / "m3_OC1.json", "B": STATE / "DEC066_state" / "abl_B_OC1.json", "C": STATE / "DEC066_state" / "abl_C_OC1.json",
       "D": STATE / "DEC059_state" / "m3os_OC1.json", "E": STATE / "DEC066_state" / "abl_E_OC1.json"}
DENSE = {"A": False, "B": True, "C": True, "D": True, "E": False}
NAME = {"A": "M3", "B": "M3+dense", "C": "M3+dense+epsOS", "D": "M3+OS (full)", "E": "M3+U_D8 only"}


def wr(name, rows):
    with open(ART / name, "x", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main(write=False):
    raw = json.loads((ART / "IEEE39_DEC066_ablation_raw.json").read_text(encoding="utf-8"))
    cal = json.loads((ART / "IEEE39_DEC059_OS_calibration.json").read_text(encoding="utf-8"))["summary"]
    eJ, eEu, eEd = G4.eps_vectors()
    add = {"A": (0, 0), "B": (0, 0), "C": (cal["eps_OS_up"], cal["eps_OS_dn"]), "D": (cal["eps_OS_up"] + U_D8, cal["eps_OS_dn"] + U_D8), "E": (U_D8, U_D8)}
    units, pmax, pmin = raw["units"], np.array(raw["pmax"]), np.array(raw["pmin"])
    st = {k: json.loads(p.read_text(encoding="utf-8")) for k, p in SRC.items()}
    m0 = json.loads((STATE / "DEC055_state" / "m0_OC1.json").read_text(encoding="utf-8"))
    Z = {k: np.array(st[k]["z"]) for k in st}
    zref = np.array(m0["z_ref"])
    nev = len(raw["events"])
    des = [i for i, e in enumerate(raw["events"]) if e["role"] == "design"]
    M = {}                      # per variant: arrays [event][unit]
    for k in "ABCDE":
        ev = raw["rows"][k]["events"]
        g = lambda key: np.array([e[key] for e in ev])
        Pp, Eg, Eg_d, Ed, Ed_d = g("P_plus"), g("E_grid_up"), g("E_grid_dn"), g("E_dense_up"), g("E_dense_dn")
        M[k] = {"Pp": Pp, "Eg_up": Eg, "Eg_dn": Eg_d, "Ed_up": Ed, "Ed_dn": Ed_d, "ok": np.array([e["pred_ok"] for e in ev]),
                "mid_up": g("win_mid_up"), "slow_up": g("win_slow_up"), "mid_dn": g("win_mid_dn"), "slow_dn": g("win_slow_dn")}
    # ---- T4: design summary
    t4, t4b = [], []
    for k in "ABCDE":
        m, s = M[k], st[k]
        E_up = np.maximum(m["Eg_up"], m["Ed_up"]) if DENSE[k] else m["Eg_up"]
        E_dn = np.maximum(m["Eg_dn"], m["Ed_dn"]) if DENSE[k] else m["Eg_dn"]
        ext_up = pmax - m["Pp"] - np.maximum(m["Eg_up"], m["Ed_up"])           # common external diagnostic: dense + grid, no eps
        ext_dn = m["Pp"] - pmin - np.maximum(m["Eg_dn"], m["Ed_dn"])
        ext_grid_up = pmax - m["Pp"] - m["Eg_up"]                              # grid only (historical M3 view)
        int_up = pmax - m["Pp"] - E_up - eJ - eEu - add[k][0]
        int_dn = m["Pp"] - pmin - E_dn - eJ - eEd - add[k][1]
        d = np.array(des)
        eu = ext_up[d]
        i, j = np.unravel_index(eu.argmin(), eu.shape)
        ei = int_up[d]
        i2, j2 = np.unravel_index(ei.argmin(), ei.shape)
        dE = np.maximum(m["Ed_up"][d] - m["Eg_up"][d], 0.0)
        near = [(raw["events"][d[a]]["name"], units[b], "P+", float(ei[a, b])) for a, b in zip(*np.where(ei < NEAR))] + \
               [(raw["events"][d[a]]["name"], units[b], "P-", float(int_dn[d][a, b])) for a, b in zip(*np.where(int_dn[d] < NEAR))]
        z = Z[k]
        dz = lambda r: float(np.abs(z[:9] - r[:9]).sum() * 100)
        t4.append({"variant": k, "name": NAME[k], "status": s["status"], "J": round(s["J"], 5), "kkt": round(float(s["kkt"]), 4), "iterations": s["iterations"], "plant_evals": s["plant_evaluations"],
                   "seconds": s["seconds"], "sumdP_vs_case_MW": round(dz(zref), 3), "sumdP_vs_A_MW": round(dz(Z["A"]), 3), "sumdP_vs_M0_MW": round(dz(np.array(m0["z"])), 3),
                   "dV_max_vs_A": float(np.abs(z[9:] - Z["A"][9:]).max()), "P_SG39_pre_pu": float(raw["rows"][k]["P_pre"][-1]) if False else float(raw["rows"][k]["P_pre"][units.index("SG39")]) if "SG39" in units else None,
                   "ext_min_margin_dense_noeps": round(float(eu.min()), 5), "ext_unit": units[j], "ext_event": raw["events"][d[i]]["name"], "ext_min_margin_gridonly": round(float(ext_grid_up[d].min()), 5),
                   "int_min_margin_own_eps": round(float(ei.min()), 5), "int_unit": units[j2], "int_event": raw["events"][d[i2]]["name"], "n_near_active": len(near),
                   "max_dE_dense": round(float(dE.max()), 6), "n_dE_dense_gt_1e-6": int((dE > 1e-6).sum()), "predictor_invalid_events": int((~m["ok"][d]).sum())})
        for (e, u, sd, v) in near:
            t4b.append({"variant": k, "event": e, "unit": u, "side": sd, "internal_margin": round(v, 6)})
    # ---- T4b: dense effect per event/unit for the near-active of each variant (+ A for reference)
    dense_rows = []
    for k in "ABCDE":
        m = M[k]
        for a in des:
            dE = np.maximum(m["Ed_up"][a] - m["Eg_up"][a], 0.0)
            for b in np.where(dE > 1e-6)[0]:
                dense_rows.append({"variant": k, "event": raw["events"][a]["name"], "unit": units[b], "jump_slack": round(float(pmax[b] - m["Pp"][a][b]), 5), "E_grid": round(float(m["Eg_up"][a][b]), 6),
                                   "E_dense": round(float(m["Ed_up"][a][b]), 6), "dE_dense": round(float(dE[b]), 6)})
    # ---- T4c: prediction register for evaluation events
    t4c = []
    ev_idx = [i for i, e in enumerate(raw["events"]) if e["role"] == "eval"]
    for a in ev_idx:
        row = {"event": raw["events"][a]["name"]}
        classes = []
        for k in "ABCDE":
            m = M[k]
            if not m["ok"][a]:
                cl, mj, m50, mm, ms = "PREDICTOR_INVALID", None, None, None, None
                lim_u = ""
            else:
                mj_v = pmax - m["Pp"][a]
                mj = float(mj_v.min())
                m50 = float((pmax - m["Pp"][a] - np.maximum(m["Ed_up"][a], 0)).min())
                mm = float((pmax - m["Pp"][a] - m["mid_up"][a]).min())
                ms = float((pmax - m["Pp"][a] - m["slow_up"][a]).min())
                lim_u = units[int(mj_v.argmin())]
                if mj <= -U_D8:
                    cl = "UNSAFE_BY_JUMP"
                elif min(m50, mm) <= -U_D8:
                    cl = "UNSAFE_BY_VALID_PREDICTOR"
                elif min(m50, mm) >= U_D8:
                    cl = "PREDICTED_SAFE_0_10s" + ("_SLOWWINDOW_UNVERIFIED" if ms < 0 else "")
                else:
                    cl = "INDETERMINATE"
            classes.append(cl)
            row[f"{k}_class"] = cl
            row[f"{k}_jump"] = None if mj is None else round(mj, 5)
            row[f"{k}_m50ms"] = None if m50 is None else round(m50, 5)
            row[f"{k}_m50ms_10s"] = None if mm is None else round(mm, 5)
            row[f"{k}_m10_195s"] = None if ms is None else round(ms, 5)
        mins = [row[f"{k}_m50ms_10s"] for k in "ABCDE" if row[f"{k}_m50ms_10s"] is not None]
        row["class_differs"] = len(set(classes)) > 1
        row["spread_m50ms_10s"] = None if not mins else round(max(mins) - min(mins), 5)
        t4c.append(row)
    # ---- T4d: pairwise attribution
    pair = []
    by = {r["variant"]: r for r in t4}
    for a, b, what in [("A", "B", "dense"), ("B", "C", "eps_OS"), ("C", "D", "U_D8 (given dense+eps_OS)"), ("A", "E", "U_D8 alone"), ("E", "D", "dense+eps_OS given U_D8"), ("A", "D", "full OS")]:
        pair.append({"contrast": f"{b}-{a}", "component": what, "sumdP_between_MW": round(float(np.abs(Z[a][:9] - Z[b][:9]).sum() * 100), 3), "dJ": round(by[b]["J"] - by[a]["J"], 5),
                     "d_ext_min_margin": round(by[b]["ext_min_margin_dense_noeps"] - by[a]["ext_min_margin_dense_noeps"], 5), "d_sumdP_vs_case_MW": round(by[b]["sumdP_vs_case_MW"] - by[a]["sumdP_vs_case_MW"], 3),
                     "d_kkt": round(by[b]["kkt"] - by[a]["kkt"], 4)})
    for r in t4:
        print(r)
    for r in pair:
        print(r)
    for r in t4c:
        print({k: v for k, v in r.items() if k.endswith("class") or k in ("event", "spread_m50ms_10s")})
    if write:
        wr("IEEE39_DEC066_T4_OPF_ablation.csv", t4)
        wr("IEEE39_DEC066_T4b_active_constraints.csv", t4b or [{"variant": "-", "event": "-", "unit": "-", "side": "-", "internal_margin": ""}])
        wr("IEEE39_DEC066_T4b2_dense_effect.csv", dense_rows or [{"variant": "-", "event": "-", "unit": "-", "jump_slack": "", "E_grid": "", "E_dense": "", "dE_dense": ""}])
        wr("IEEE39_DEC066_T4c_prediction_register.csv", t4c)
        wr("IEEE39_DEC066_T4d_pairwise.csv", pair)


if __name__ == "__main__":
    main("write" in sys.argv)
