"""DEC-053 phase D: constraints dictionary, physical compliance table (10 units, 39 buses), voltage reconciliation, figure.  Post-processing only."""
import csv
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import dec053_core as C

A = C.ART
lim = C.limits()
NAMES = C.UNIT
LIMD = {"u_" + k: v for k, v in lim.items()}

# ------------------------------------------------------------ runs audited (post-processing of stored series)
RUNS = [("E8_P+", "C2t B2 P+"), ("E8_Q+", "C2t B2 Q+"), ("E7t_P+", "C2t B1(PQ) P+"), ("E5t_P+", "C2t B0 P+"),
        ("E9B0_Vsafe_R35_040_P+", "R35_040 B2 P+"), ("E9B0_Vsafe_R35_040_Q+", "R35_040 B2 Q+"), ("E9B0_Vsafe_R35_040_S0", "R35_040 B2 S0"), ("DEC050A_Q+", "R35_040 B2 Q+ 2000 s")]
SERIES = {}
for k, lab in RUNS:
    d = C.load(k)
    C._fill_limits(d, LIMD)
    SERIES[k] = (lab, d["t"], d["P"], d["Q"], d["V"], d["bus_ids"])
for tag, f, ev in (("DEC051_H3_sim1", "IEEE39_DEC051_H3_sim1_series.npz", "R35_040 B2 P+ 64.4204 MW bus 4"), ("DEC051_H3_sim2", "IEEE39_DEC051_H3_sim2_series.npz", "R35_040 B2 P+ 58.564 MW bus 18")):
    z = np.load(A / f)
    SERIES[tag] = (ev, z["time_s"], z["P"], z["Q"], z["bus_voltage_pu"], np.arange(1, 40))

QOBS = {"SG": "GENROU terminal Q (bus injection, system-base pu)", "GFM": "REGF1 bus injection Q (system-base pu)"}
rows = []
for k, (lab, t, P, Q, V, bids) in SERIES.items():
    dt = float(np.median(np.diff(t)))
    pre = t < C.T_EVENT - 1e-9
    post = t > C.T_EVENT + 1e-9
    j1 = np.where(post)[0][0]
    S = np.hypot(P, Q)
    for i, u in enumerate(NAMES):
        kind = "SG" if u.startswith("SG") else "GFM"
        for q, x, lo, hi in (("P", P[:, i], lim["pmin"][i], lim["pmax"][i]), ("Q", Q[:, i], lim["qmin"][i], lim["qmax"][i]), ("S", S[:, i], 0.0, lim["smax"][i])):
            marg = np.minimum(x - lo, hi - x) if q != "S" else hi - x
            xp = x[post]
            iex = int(np.argmax(np.abs(xp - x[pre][-1])))
            tv = float((marg[post] < 0).sum() * dt)
            rows.append(dict(run=k, run_label=lab, item_type="unit", item=u, quantity=q, limit_lo_pu=lo, limit_hi_pu=hi, base="system-base pu (100 MVA)",
                             sign_convention="generation positive", measured_quantity=QOBS[kind], pre_event=x[pre][-1], first_sample_after_event=x[j1], extreme_after_event=xp[iex],
                             t_extreme_s=float(t[post][iex]), last_value=x[-1], min_margin_pu=float(marg[post].min()), t_min_margin_s=float(t[post][int(np.argmin(marg[post]))]),
                             t_violation_s=tv, simulated_violation=bool(tv > 0), model_status="APPROXIMATED" if q != "S" else "APPROXIMATED",
                             certificate_status="NOT_CERTIFIED (simulated sample at dt=%.3g s; no inter-sample bound)" % dt))
    for j, b in enumerate(bids):
        v = V[:, j]
        out = (v < C.VLO) | (v > C.VHI)
        rows.append(dict(run=k, run_label=lab, item_type="bus", item=f"bus{int(b)}", quantity="V", limit_lo_pu=C.VLO, limit_hi_pu=C.VHI, base="pu nominal", sign_convention="-", measured_quantity="ANDES Bus.v",
                         pre_event=v[pre][-1], first_sample_after_event=v[j1], extreme_after_event=float(v[post].min() if abs(v[post].min() - 1) > abs(v[post].max() - 1) else v[post].max()),
                         t_extreme_s=float(t[post][int(np.argmax(np.abs(v[post] - 1)))]), last_value=v[-1], min_margin_pu=float(min((v - C.VLO).min(), (C.VHI - v).min())),
                         t_min_margin_s=float(t[int(np.argmin(np.minimum(v - C.VLO, C.VHI - v)))]), t_violation_s=float(out.sum() * dt), simulated_violation=bool(out.any()),
                         model_status="MODELLED (assessed on the simulated plant of the run; static flow of another variant never used)", certificate_status="NOT_CERTIFIED"))
cols = list(rows[0].keys())
with open(A / "IEEE39_DEC053_physical_compliance.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, cols)
    w.writeheader()
    w.writerows(rows)

# ------------------------------------------------------------ constraints dictionary
D = [
    ("C-P-max", "P <= Pmax_i", "10 units", "case PV/Slack pmax (e.g. SG31 6.50, SG35 6.97 pu)", "APPROXIMATED", "Checked in post-processing against the case data; ANDES TGOV1N VMAX (1.05 Sn: SG31 8.778 pu) and REGF1 internal Pmax=Sn/100 are 1.1-2.0x looser, so ANDES itself does not enforce the case Pmax.", "violation_simulated is a statement about this case limit only"),
    ("C-P-min", "P >= Pmin_i", "10 units", "case pmin = 0", "APPROXIMATED", "Same as Pmax (post-processing); GFM REGF1 allows negative P (-Sn/100).", ""),
    ("C-Q-max-min", "Qmin_i <= Q <= Qmax_i", "10 units", "case qmax/qmin", "APPROXIMATED", "Checked in post-processing; SG excitation limited only through IEEEX1 VRMAX/VRMIN; REGF1 internal Q limit Sn/100.", ""),
    ("C-S-max", "sqrt(P^2+Q^2) <= Smax_i = Sn_i/100", "10 units", "GENROU/REGF1 Sn", "APPROXIMATED", "Apparent power of the bus injection; not a stator-current/field-current capability curve.", "S margin does not prove capability-curve compliance"),
    ("C-V-band", "0.95 <= V_b <= 1.05 pu", "39 buses", "original band", "MODELLED", "Assessed for every bus of the simulated plant (positive sequence RMS). Pre-event: historical C2t 0.9808-1.0730 pu (21 buses > 1.05); C2t_Vsafe_R35_040 0.9794-1.0444 pu.", "Band compliance is a simulated outcome, not a protection function"),
    ("C-Pref-Qref", "Pset/Qset reference margins", "10 units", "RDC internal references", "MODELLED", "References are RDC states; margins of references are reported separately and are never used to claim physical compliance.", ""),
    ("C-RoCoF-rate", "unit ramp-rate / governor rate limits", "10 units", "-", "NOT_MODELLED", "Rates (e.g. max dPset/dt 0.6 pu/s) are reported; no rate limit is defined in the E8 realisation.", ""),
    ("C-field-OEL", "field-current / over-excitation limiter, UEL, stator thermal", "6 SG", "-", "NOT_MODELLED", "GENROU+IEEEX1 without OEL/UEL; Q limits are not capability-curve based.", "No claim on SG capability curves"),
    ("C-converter-I", "converter current limit, sub-cycle behaviour", "4 GFM", "-", "NOT_OBSERVABLE", "REGF1 is a positive-sequence RMS model; sub-cycle/EMT current limiting is invisible.", "No EMT protection claim"),
    ("C-SoC-energy", "BESS state of charge / energy / DC link", "4 GFM", "-", "NOT_MODELLED", "REGF1 has no energy storage state; energy and SoC indicators are not available.", "Do not assume unlimited energy as a result"),
    ("C-protection", "frequency/voltage relays, tripping, load shedding", "system", "-", "NOT_MODELLED", "No protection or tripping logic in the plant.", ""),
    ("C-unbalance", "unbalanced faults / negative sequence", "system", "-", "NOT_MODELLED", "Positive-sequence only.", ""),
    ("C-N-1", "N-1 contingencies and topology changes", "system", "-", "NOT_MODELLED", "Topology fixed; no N-1 tested.", ""),
    ("C-comm-delay", "communication delay / loss", "RDC graph", "ring buffer (E15, DEC-050 C)", "APPROXIMATED", "Fixed delays 0.2, 0.5 (ok), 0.75 (degraded: 22 buses outside band), 1.0 (violated), 5 s (diverged); no packet loss or time-varying delay.", ""),
    ("C-sampling", "between-sample compliance", "all", "dt = 2^-8 s", "NOT_OBSERVABLE", "Violations between stored samples cannot be excluded; fixed-step trapezoid.", "No safety-between-samples claim"),
    ("C-cert", "certified forward invariance of the safe set", "system", "-", "NOT_MODELLED", "No CLF/HOCBF certificate exists (DEC-052: region NOT_CERTIFIED); only simulated and predicted compliance.", "Distinguish simulated violation from unavailable certificate"),
]
UN = [(u, lim["pn"][i], lim["pmin"][i], lim["pmax"][i], lim["qmin"][i], lim["qmax"][i], lim["smax"][i], "GENROU+TGOV1N+IEEEX1+IEEEST (PSS)" if u.startswith("SG") else "REGF1 (GFM)") for i, u in enumerate(NAMES)]
with open(A / "IEEE39_DEC053_constraints_dictionary.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["row_type", "id", "description", "scope", "source", "status", "implementation_note", "claim_limit", "Pn_pu", "Pmin_pu", "Pmax_pu", "Qmin_pu", "Qmax_pu", "Smax_pu", "device_model", "pu_base"])
    for r in D:
        w.writerow(["constraint", *r, "", "", "", "", "", "", "", "system base 100 MVA"])
    for u, pn, pmn, pmx, qmn, qmx, sm, mdl in UN:
        w.writerow(["unit_limits", u, "unit P/Q/S limits (case data, system base)", u, "E8 unit arrays / PV-Slack / GENROU-REGF1 Sn", "APPROXIMATED", "", "", pn, pmn, pmx, qmn, qmx, sm, mdl, "system base 100 MVA"])
    for b in range(1, 40):
        w.writerow(["bus_limits", f"bus{b}", "0.95 <= V <= 1.05 pu", f"bus{b}", "original band", "MODELLED", "", "", "", "", "", "", "", "", "positive-sequence bus", "pu nominal"])

# ------------------------------------------------------------ summary + figure
summ = {}
for k in ("E8_P+", "E9B0_Vsafe_R35_040_P+", "E9B0_Vsafe_R35_040_Q+", "E8_Q+", "DEC051_H3_sim1", "DEC051_H3_sim2"):
    rr = [r for r in rows if r["run"] == k]
    un = [r for r in rr if r["item_type"] == "unit"]
    mn = {q: min((r for r in un if r["quantity"] == q), key=lambda r: r["min_margin_pu"]) for q in "PQS"}
    vb = [r for r in rr if r["item_type"] == "bus"]
    summ[k] = {"label": rr[0]["run_label"], "violating_unit_quantities": sorted({f'{r["item"]}:{r["quantity"]}' for r in un if r["simulated_violation"]}),
               "min_margin": {q: {"unit": mn[q]["item"], "margin_pu": mn[q]["min_margin_pu"], "t_s": mn[q]["t_min_margin_s"]} for q in mn},
               "V_min_pu_all_39_after_start": min(min(r["pre_event"], r["last_value"], r["extreme_after_event"]) for r in vb), "n_buses_ever_outside_band": sum(r["simulated_violation"] for r in vb)}
json.dump(summ, open(A / "IEEE39_DEC053_physical_summary.json", "w"), indent=1, default=float)
print(json.dumps({k: (v["violating_unit_quantities"], v["n_buses_ever_outside_band"], {q: round(m["margin_pu"], 4) for q, m in v["min_margin"].items()}) for k, v in summ.items()}, indent=0))

fig, ax = plt.subplots(1, 2, figsize=(13, 4.8))
for off, k, c in ((-0.27, "E8_P+", "tab:red"), (0.0, "E9B0_Vsafe_R35_040_P+", "tab:green"), (0.27, "DEC051_H3_sim2", "tab:purple")):
    un = [r for r in rows if r["run"] == k and r["item_type"] == "unit" and r["quantity"] == "P"]
    ax[0].bar(np.arange(10) + off, [r["min_margin_pu"] / (lim["pmax"][i] - lim["pmin"][i]) * 100 for i, r in enumerate(un)], 0.27, color=c, label=SERIES[k][0])
ax[0].axhline(0, c="k", lw=0.8)
ax[0].set_xticks(range(10), NAMES, rotation=45, fontsize=7)
ax[0].set(ylabel="min (Pmax-P) after the event, % of (Pmax-Pmin)", title="physical P margin per unit (negative = case Pmax exceeded)")
ax[0].legend(fontsize=7)
for k, c in (("E8_P+", "tab:red"), ("E9B0_Vsafe_R35_040_P+", "tab:green")):
    vb = [r for r in rows if r["run"] == k and r["item_type"] == "bus"]
    ax[1].plot(range(1, 40), [r["pre_event"] for r in vb], "o", ms=3, c=c, label=SERIES[k][0] + " pre-event")
    ax[1].plot(range(1, 40), [r["extreme_after_event"] for r in vb], "x", ms=4, c=c, label=SERIES[k][0] + " extreme after event")
ax[1].axhline(0.95, c="k", ls="--"), ax[1].axhline(1.05, c="k", ls="--")
ax[1].set(xlabel="bus", ylabel="V (pu)", title="39-bus voltages vs the original band")
ax[1].legend(fontsize=6)
fig.tight_layout()
fig.savefig(C.FIG / "IEEE39_DEC053_physical_limits.png", dpi=150)
