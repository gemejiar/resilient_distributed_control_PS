"""DEC-053 phase B: H2 metrics (single code path), pairwise controller/dispatch contrasts, Q-V diagnosis, figure.  Post-processing only."""
import csv
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import dec053_core as C

A = C.ART
lim = C.limits()
LIMD = {"u_" + k: v for k, v in lim.items()}
ALL = {}
for k in C.KEY:
    d = C.load(k)
    C._fill_limits(d, LIMD)
    ALL[k] = d


def ind(k, win=None):
    return C.indicators(ALL[k], lim, win if win else C.KEY[k]["t_end"], C.KEY[k]["scenario"])


# ---------- B1/B4: metrics, one row per run at its own full horizon
metrics = []
for k, s in C.KEY.items():
    r = ind(k)
    metrics.append({"run_id": k, "controller": s["controller"], "variant": s["variant"], "scenario": s["scenario"], "horizon_s": s["t_end"], "window": "full", **r})
cols = []
for m in metrics:
    for c in m:
        if c not in cols:
            cols.append(c)
with open(A / "IEEE39_DEC053_H2_metrics.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, cols, restval="not_available(no Pset/Qset stored for this controller)")
    w.writeheader()
    w.writerows(metrics)

# ---------- pairwise
KEYS = ["f_nadir_Hz", "f_zenith_Hz", "rocof_max_Hz_s", "f_final_error_Hz", "V_min_pu", "V_max_pu", "t_outside_band_s_any_bus", "V_err_vs_1pu_mean_abs_unitbus_final",
        "V_err_vs_1pu_max_abs_unitbus_final", "min_margin_Pmax_pu", "min_margin_Qmax_pu", "min_margin_Qmin_pu", "min_margin_Smax_pu", "P_share_spread_final", "Q_share_spread_final"]
pairs = [
    ("CMP-01", "B1_PQ vs B2 (controller)", "E7t_P+", "E8_P+", 120.0, "CAUSALLY_COMPARABLE", "yes", "yes", "common 120 s", "yes"),
    ("CMP-01", "B1_PQ vs B2 (controller)", "E7t_Q+", "E8_Q+", 120.0, "CAUSALLY_COMPARABLE", "yes", "yes", "common 120 s", "yes"),
    ("CMP-01", "B1_PQ vs B2 (controller)", "E7t_S0", "E8_S0", 120.0, "CAUSALLY_COMPARABLE", "yes", "yes", "common 120 s", "yes"),
    ("CMP-02", "B1_P vs B2 (controller, P only)", "E6t_P+", "E8_P+", 80.0, "DESCRIPTIVE_ONLY", "yes", "yes", "common 80 s", "yes"),
    ("CMP-03", "B0 vs B2 (primary reference)", "E5t_P+", "E8_P+", 40.0, "CAUSALLY_COMPARABLE", "yes", "yes", "common 40 s", "yes"),
    ("CMP-03", "B0 vs B2 (primary reference)", "E5t_Q+", "E8_Q+", 40.0, "CAUSALLY_COMPARABLE", "yes", "yes", "common 40 s", "yes"),
    ("CMP-03b", "B0 vs B1_PQ", "E5t_P+", "E7t_P+", 40.0, "CAUSALLY_COMPARABLE", "yes", "yes", "common 40 s", "yes"),
    ("CMP-05", "dispatch effect under fixed B2: C2t -> Vsafe", "E8_P+", "E9B0_Vsafe_P+", 200.0, "DESCRIPTIVE_ONLY", "no", "yes", "yes 200 s", "yes"),
    ("CMP-05", "dispatch effect under fixed B2: Vsafe -> Vsafe_R35", "E9B0_Vsafe_P+", "E9B0_Vsafe_R35_P+", 200.0, "DESCRIPTIVE_ONLY", "no", "yes", "yes 200 s", "yes"),
    ("CMP-05", "dispatch effect under fixed B2: Vsafe_R35 -> Vsafe_R35_040", "E9B0_Vsafe_R35_P+", "E9B0_Vsafe_R35_040_P+", 200.0, "DESCRIPTIVE_ONLY", "no", "yes", "yes 200 s", "yes"),
    ("CMP-05", "dispatch effect under fixed B2: C2t -> Vsafe_R35_040", "E8_P+", "E9B0_Vsafe_R35_040_P+", 200.0, "DESCRIPTIVE_ONLY", "no", "yes", "yes 200 s", "yes"),
    ("CMP-05", "dispatch effect under fixed B2: C2t -> Vsafe_R35_040", "E8_Q+", "E9B0_Vsafe_R35_040_Q+", 200.0, "DESCRIPTIVE_ONLY", "no", "yes", "yes 200 s", "yes"),
    ("CMP-05", "dispatch effect under fixed B2: C2t -> Vsafe_R35_040", "E8_S0", "E9B0_Vsafe_R35_040_S0", 200.0, "DESCRIPTIVE_ONLY", "no", "yes", "yes 200 s", "yes"),
    ("CMP-07", "B3 (privileged knowledge) vs B2, C2t", "E8_P+", "B3_P+", 200.0, "DESCRIPTIVE_ONLY", "yes", "yes", "yes 200 s", "yes"),
    ("CMP-08", "B2 vs B2_QV1 (failed correction), R35_040", "E9B0_Vsafe_R35_040_P+", "B2QV1_P+", 200.0, "CAUSALLY_COMPARABLE", "yes", "yes", "yes 200 s", "yes"),
    ("CMP-08", "B2 vs B2_QV1 (failed correction), R35_040", "E9B0_Vsafe_R35_040_Q+", "B2QV1_Q+", 200.0, "CAUSALLY_COMPARABLE", "yes", "yes", "yes 200 s", "yes"),
]
PW = []
for pid, lab, a, b, win, concl, sd, se, sh, sm in pairs:
    ra, rb = ind(a, win), ind(b, win)
    row = {"pair_id": pid, "contrast": lab, "A": a, "B": b, "window_s": win, "same_dispatch": sd, "same_event": se, "same_horizon": sh, "same_model": sm, "conclusion": concl,
           "label": "effect of dispatch under fixed B2 (not a secondary-algorithm gain)" if pid == "CMP-05" else "effect of controller on identical plant/dispatch/event; two independently tuned designs" if pid in ("CMP-01", "CMP-03", "CMP-03b") else "descriptive"}
    for k in KEYS:
        row[f"A_{k}"], row[f"B_{k}"] = ra[k], rb[k]
        row[f"d_{k}"] = rb[k] - ra[k]
    row["abs_ffinal_A"], row["abs_ffinal_B"] = abs(ra["f_final_error_Hz"]), abs(rb["f_final_error_Hz"])
    row["f_settling_A"], row["f_settling_B"] = ra["f_settling_2mHz_s"], rb["f_settling_2mHz_s"]
    PW.append(row)
with open(A / "IEEE39_DEC053_H2_pairwise.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, list(PW[0].keys()))
    w.writeheader()
    w.writerows(PW)

# ---------- Q-V diagnosis against the real RDC equilibrium (Q+, R35_040, B2, 2000 s)
eq = {r["unit"]: r for r in csv.DictReader(open(A / "IEEE39_DEC051_equilibrium.csv"))}
Veq = np.array([float(eq[u]["V_pu"]) for u in C.UNIT])
d = ALL["DEC050A_Q+"]
t = d["t"]
ub = [list(d["bus_ids"]).index(b) for b in C.UNIT_BUS]
vend = d["V"][t >= t[-1] - 20].mean(axis=0)
qv = {"horizon_s": float(t[-1]), "sample_dt_s": float(np.median(np.diff(t))),
      "unit_bus_V_err_vs_1pu_mean": float(np.abs(vend[ub] - 1).mean()), "unit_bus_V_err_vs_1pu_max": float(np.abs(vend[ub] - 1).max()),
      "all39_V_err_vs_1pu_mean": float(np.abs(vend - 1).mean()), "all39_V_err_vs_1pu_max": float(np.abs(vend - 1).max()),
      "unit_V_at_relative_equilibrium_vs_1pu_mean": float(np.abs(Veq - 1).mean()), "unit_V_at_relative_equilibrium_vs_1pu_max": float(np.abs(Veq - 1).max()),
      "unit_V_t1999_minus_equilibrium_max": float(np.abs(vend[ub] - Veq).max()),
      "DEC050_reported_mean_V_err": 3.2e-3, "DEC050_reported_max_V_err": 8.3e-3}
# tau from distance of Qset/V to the final value (exponential fit on the unit-bus voltage deviation), diagnostic only
dv = np.abs(d["V"][:, ub] - vend[ub]).max(axis=1)
m = (t > 100) & (t < 1200) & (dv > 1e-5)
pf = np.polyfit(t[m], np.log(dv[m]), 1)
qv["tau_fit_s_unit_V_deviation_100_1200s"] = float(-1 / pf[0])
qv["note"] = "V error vs 1 pu is a regulation-quality metric; V error vs the real RDC equilibrium measures non-convergence. The equilibrium lies away from 1 pu by construction (Q consensus/leakage trade-off); both reported separately."
json.dump(qv, open(A / "IEEE39_DEC053_H2_QV_diagnosis.json", "w"), indent=1)
print(json.dumps(qv, indent=1))

# ---------- print key comparisons
for p in PW:
    if p["pair_id"] in ("CMP-01", "CMP-03", "CMP-03b", "CMP-02"):
        print(p["pair_id"], p["A"], p["B"], "nadir", round(p["A_f_nadir_Hz"], 5), round(p["B_f_nadir_Hz"], 5), "rocof", round(p["A_rocof_max_Hz_s"], 4), round(p["B_rocof_max_Hz_s"], 4),
              "|df|", f"{p['abs_ffinal_A']:.2e} {p['abs_ffinal_B']:.2e}", "Verr_unit", round(p["A_V_err_vs_1pu_mean_abs_unitbus_final"], 4), round(p["B_V_err_vs_1pu_mean_abs_unitbus_final"], 4),
              "Pshare", round(p["A_P_share_spread_final"], 4), round(p["B_P_share_spread_final"], 4), "Qshare", round(p["A_Q_share_spread_final"], 3), round(p["B_Q_share_spread_final"], 3))

# ---------- figure (no paper text)
fig, ax = plt.subplots(2, 2, figsize=(12, 8))
col = {"B0": "tab:gray", "B1_PQ": "tab:blue", "B1_P": "tab:cyan", "B2": "tab:red"}
for k, lab, c in (("E5t_P+", "B0 (40 s)", "tab:gray"), ("E6t_P+", "B1 P-only (80 s)", "tab:cyan"), ("E7t_P+", "B1 P+Q (120 s)", "tab:blue"), ("E8_P+", "B2 original RDC (200 s)", "tab:red")):
    d = ALL[k]
    fm = d["f"].mean(axis=1)
    ax[0, 0].plot(d["t"], fm - 60, c=c, lw=1, label=lab)
    ax[0, 1].plot(d["t"], fm - 60, c=c, lw=1)
ax[0, 0].set(xlim=(4, 40), xlabel="t (s)", ylabel="mean bus frequency - 60 (Hz)", title="P+ 58.564 MW, C2t dispatch: transient")
ax[0, 0].legend(fontsize=7)
ax[0, 1].set(xlim=(0, 200), ylim=(-0.012, 0.004), xlabel="t (s)", ylabel="mean bus frequency - 60 (Hz)", title="common dispatch/event, own horizons")
for k, lab, c in (("E7t_Q+", "B1 P+Q", "tab:blue"), ("E8_Q+", "B2", "tab:red")):
    d = ALL[k]
    ax[1, 0].fill_between(d["t"], d["V"].min(axis=1), d["V"].max(axis=1), color=c, alpha=0.25, label=f"{lab}: min-max of 39 buses")
ax[1, 0].axhline(0.95, c="k", ls="--"), ax[1, 0].axhline(1.05, c="k", ls="--")
ax[1, 0].set(xlim=(0, 120), xlabel="t (s)", ylabel="V (pu)", title="Q+ 17.345 MVAr: bus-voltage envelope (C2t dispatch: pre-event V up to 1.0730)")
ax[1, 0].legend(fontsize=7)
for k, lab, c in (("E7t_P+", "B1 P+Q", "tab:blue"), ("E8_P+", "B2", "tab:red")):
    d = ALL[k]
    ax[1, 1].plot(d["t"], np.ptp(d["P"] / lim["pn"], axis=1), c=c, label=f"{lab}: spread of P/Pn")
ax[1, 1].set(xlim=(0, 120), xlabel="t (s)", ylabel="max-min of P_i/Pn_i (10 units)", title="active-power sharing (physical outputs)")
ax[1, 1].legend(fontsize=7)
fig.tight_layout()
fig.savefig(C.FIG / "IEEE39_DEC053_H2_controller_comparison.png", dpi=150)
