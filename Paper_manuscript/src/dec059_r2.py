"""DEC-059 lot R2 analysis (numerical closure): each run against the prediction registered in ops/sted/DEC059_protocol.md and IEEE39_DEC059_R2_plan.json.
Writes IEEE39_DEC059_R2_results.json exclusively."""
from __future__ import annotations

import json

import numpy as np

import dec055_common as C55
import dec057_ins as INS
import dec057_tds as T7
import dec059_tds as T

TE = T.TE


def load(root, run):
    d = root / run
    return dict(np.load(d / "series.npz", allow_pickle=True)), json.loads((d / "status.json").read_text(encoding="utf-8"))


def unit_lim(oc):
    import dec055_oc as OCM
    return OCM.make_plant(oc).limits


def main(write=False):
    out = {"stage": "DEC-059 R2 numerical closure (reset_tiny = 0)"}
    lim1 = unit_lim("OC1")
    # N1 / N2: effect of reset_tiny on the D8 transient; reproducibility
    a, sa = load(T.RUNS, "D59N1_b8_trap_loc16_rt0")
    b, sb = load(T.RUNS, "D59N2_b8_trap_loc16_rt0_repeat")
    c, sc = load(T7.RUNS, "D57D8_b8_trapezoid_loc16")
    n = min(len(a["t"]), len(c["t"]))
    same_t = bool(np.array_equal(a["t"][:n], c["t"][:n]))
    w = (a["t"][:n] >= TE - 1e-12) & (a["t"][:n] <= TE + 0.5)
    k50 = (a["t"] >= TE - 1e-12) & (a["t"] <= TE + 0.05)
    m_rt0 = float((lim1["pmax"][None, :] - a["P"][k50]).min())
    k50c = (c["t"] >= TE - 1e-12) & (c["t"] <= TE + 0.05)
    m_rt1 = float((lim1["pmax"][None, :] - c["P"][k50c]).min())
    dP = np.abs(a["P"][:n] - c["P"][:n])
    out["N1_reset_tiny_effect_D8"] = {"same_time_grid": same_t, "max_abs_dP_window_te_te+0.5": float(dP[w].max()), "max_abs_dP_whole_20s": float(dP.max()),
                                      "max_abs_dV_whole": float(np.abs(a["V"][:n] - c["V"][:n]).max()), "pmax_margin_50ms_rt0": m_rt0, "pmax_margin_50ms_rt1": m_rt1,
                                      "prediction": "|dP| <= 1e-6 pu on [t_e, t_e+0.5]", "verdict": "CONFIRMED" if dP[w].max() <= 1e-6 else "REFUTED"}
    out["N2_reproducibility"] = {k: bool(np.array_equal(a[k], b[k])) for k in ("t", "P", "Q", "V")}
    out["N2_reproducibility"]["verdict"] = "CONFIRMED (bit-identical)" if all(out["N2_reproducibility"].values()) else "REFUTED"
    # N3: OC3 M3 refutation under reset_tiny 0
    lim3 = unit_lim("OC3")
    z3, s3 = load(T.RUNS, "D59N3_M3V_B2_b8P_S3_rt0")
    z7, _ = load(T7.RUNS, "D57M3V_B2_b8P_S3")
    k = (z3["t"] >= TE - 1e-12) & (z3["t"] <= TE + 0.05)
    mm = lim3["pmax"][None, :] - z3["P"][k]
    i, j = np.unravel_index(int(np.argmin(mm)), mm.shape)
    k7 = (z7["t"] >= TE - 1e-12) & (z7["t"] <= TE + 0.05)
    m7 = float((lim3["pmax"][None, :] - z7["P"][k7]).min())
    out["N3_OC3_M3_refutation"] = {"status": s3["status"], "min_pmax_margin_50ms": float(mm.min()), "unit": C55.UNITS[j], "t_after_event_ms": float((z3["t"][k][i] - TE) * 1e3),
                                   "DEC057_value_reset_tiny1": m7, "difference": float(mm.min() - m7),
                                   "verdict": "CONFIRMED (UNSAFE beyond U_D8)" if mm.min() <= -0.0109 and abs(mm.min() - m7) <= 1e-4 else "SEE VALUES"}
    # plant-only flats (G1-P)
    g1 = {}
    for oc in ("OC1", "OC2", "OC3"):
        z, s = load(T.RUNS, f"D59N_plant_flat_{oc}_M0")
        f = z["f_bus_hz"]
        g1[oc] = {"status": s["status"], "max_abs_df_hz": float(np.abs(f - f[0]).max()), "max_abs_dV_pu": float(np.abs(z["V"] - z["V"][0]).max()),
                  "V_min": float(z["V"].min()), "V_max": float(z["V"].max()), "cmd_ref_change": float(np.abs(z["cmd_pset"] - z["cmd_pset"][0]).max()) if len(z["cmd_pset"]) else 0.0}
        g1[oc]["G1_P"] = "PASS" if g1[oc]["max_abs_df_hz"] <= 0.005 and g1[oc]["max_abs_dV_pu"] <= 1e-3 and z["V"].min() >= 0.95 and z["V"].max() <= 1.05 else "FAIL"
    out["G1P_plant_flat_M0"] = g1
    # B3 flats OC1/OC2: dead-zone audit
    b3 = {}
    for oc in ("OC1", "OC2"):
        z, s = load(T.RUNS, f"D59N_B3_flat_{oc}_M0")
        b3[oc] = {"status": s["status"], "max_abs_dV_pu": float(np.abs(z["V"] - z["V"][0]).max()), "max_abs_dP_pu": float(np.abs(z["P"] - z["P"][0]).max()),
                  "max_abs_df_hz": float(np.abs(z["f_bus_hz"] - z["f_bus_hz"][0]).max()), "max_abs_dPset": float(np.abs(z["cmd_pset"] - z["cmd_pset"][0]).max()),
                  "max_abs_dQset": float(np.abs(z["cmd_qset"] - z["cmd_qset"][0]).max())}
        b3[oc]["verdict"] = "CONFIRMED (<= 1e-6)" if max(b3[oc]["max_abs_dV_pu"], b3[oc]["max_abs_dP_pu"]) <= 1e-6 else "REFUTED"
        b3[oc]["G1_drift_20s_criteria"] = "PASS" if b3[oc]["max_abs_dV_pu"] <= 1e-3 and b3[oc]["max_abs_df_hz"] <= 0.005 else "FAIL"
    out["B3_flat_audit"] = b3
    # OC3 B3 2000 s
    z, s = load(T.RUNS, "D59N_B3_flat_OC3_M0_2000s")
    t = z["t"]
    dev = np.maximum(np.abs(z["V"] - z["V"][0]).max(axis=1), np.abs(z["P"] - z["P"][0]).max(axis=1))
    g = (dev > 1e-11) & (dev < 1e-4) & (t > 50)
    rate = float(np.polyfit(t[g], np.log(dev[g]), 1)[0]) if g.sum() > 10 else None
    cross = t[np.where(dev > 1e-3)[0][0]] if (dev > 1e-3).any() else None
    out["OC3_B3_2000s"] = {"status": s["status"], "t_end": float(t[-1]), "dev_max": float(dev.max()), "dev_at_200s": float(np.interp(200, t, dev)), "dev_at_1000s": float(np.interp(1000, t, dev)),
                           "growth_rate_fit_1e-11_to_1e-4": rate, "t_dev_gt_1e-3": None if cross is None else float(cross), "predicted_rate": 0.0198,
                           "verdict": ("CONFIRMED" if rate is not None and abs(rate - 0.0198) <= 0.15 * 0.0198 and cross is not None else "REFUTED / SEE VALUES")}
    # N10 dt/2 vs RES4
    zn, sn = load(T.RUNS, "D59N10_OC3_M0_B2_rt0_dthalf")
    zr, _ = load(T7.RUNS, "D57RES_INS_OC3_reset_tiny0")
    rec = {"status": sn["status"], "t_end_dthalf": float(zn["t"][-1]), "t_end_RES4_dt": float(zr["t"][-1])}
    for lab, zz in (("dthalf", zn), ("RES4_dt", zr)):
        tc, amp = INS.amp_series(zz)
        gg = (amp > 1e-8) & (amp < 1e-3) & (tc > 60)
        rec[f"growth_rate_{lab}"] = float(np.polyfit(tc[gg], np.log(amp[gg]), 1)[0]) if gg.sum() > 4 else None
    rec["rate_rel_diff"] = abs(rec["growth_rate_dthalf"] - rec["growth_rate_RES4_dt"]) / abs(rec["growth_rate_RES4_dt"]) if rec["growth_rate_dthalf"] and rec["growth_rate_RES4_dt"] else None
    rec["verdict"] = "CONFIRMED" if rec["rate_rel_diff"] is not None and rec["rate_rel_diff"] <= 0.15 and abs(rec["t_end_dthalf"] - rec["t_end_RES4_dt"]) <= 10 else "SEE VALUES"
    out["N10_OC3_instability_dthalf"] = rec
    if write:
        with open(C55.ART / "IEEE39_DEC059_R2_results.json", "x", encoding="utf-8") as f:
            json.dump(out, f, indent=1, default=float)
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    import sys
    main("write" in sys.argv)
