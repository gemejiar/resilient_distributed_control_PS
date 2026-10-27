"""DEC-053 phase C: HISTORICAL_RULE_REPLAY of R35_040 (static power flow + TDS initialisation, NO time stepping), signed validation table,
SG31/SG35 attribution (C5), nominal-frontier comparison (C6), figure.  Post-processing of stored artefacts otherwise."""
import csv
import json
import os

os.environ["C2_VARIANT"] = "C2t"

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import dec051_core as K
import dec053_core as C
import e9b_variant as EV
import run_dec051_h3_jump as J
from run_e0_ieee39 import git_commit

A = C.ART
NAMES = C.UNIT
EPS_JUMP = 0.00227892616553671  # DEC-051: discrepancy of the jump term only


def jl(n):
    return json.load(open(A / n))


# ------------------------------------------------------------------ C1/C3: audit + replay of the historical rule
var = jl("IEEE39_E9B0_variant.json")
srch = jl("IEEE39_E9B0_redispatch_search.json")
w_recomp = EV.receiver_weights()  # from the stored Vsafe P+ run margins (simulation-derived input)
w_stored = {int(k): v for k, v in srch["receivers_GFM"].items()}
DELTAS = {"R35": 0.015, "R35_040": 0.040}
rep = {"mode": "HISTORICAL_RULE_REPLAY", "git_commit": git_commit(), "tds_steps": 0,
       "rule": "Vsafe initial condition (B3-A d=0 AC selection v1 S0, imposed on PV p0/v0) then p0[SG35] -= delta; p0[GFM_b] += delta*w_b; w_b = max(minPmargin_b(B2,P+,C2t_Vsafe),0)/sum, margins read from IEEE39_E9B0_variant.json",
       "weights_recomputed": {str(k): v for k, v in w_recomp.items()}, "weights_stored_search": {str(k): v for k, v in w_stored.items()},
       "weights_max_abs_diff": max(abs(w_recomp[k] - w_stored[k]) for k in w_recomp),
       "inputs_sha256": {f: C.sha(A / f) for f in ("IEEE39_E9B0_variant.json", "IEEE39_E9B0_redispatch_search.json", "IEEE39_E9B0_variant_R35_040.json", "IEEE39_E9B0_initial_condition_R35_040_units.csv")},
       "code_sha256": {f: C.sha(C.ROOT / "Paper_manuscript/src" / f) for f in ("e9b_variant.py", "run_e9b0_redispatch.py", "run_dec051_h3_jump.py")},
       "provenance": {
           "delta_min_bisection_pu": srch["delta_min_pu"], "delta_R35_frozen_by_rule_pu": srch["delta_frozen_pu"], "rule_for_R35": srch["rule"],
           "delta_R35_040": "0.040 pu was NOT produced by the bisection rule: it is an investigator-selected increase (DEC-044/045) that raises the SG35 transient margin from 4.1e-4 to 2.45e-2 pu (required >= 0.020 pu). It is not an automatic optimum.",
           "simulation_dependence": "(i) the receiver weights use minimum P margins of the GFMs observed in a TDS of the SAME event (P+ 58.564 MW at bus 4) on C2t_Vsafe; (ii) delta_min comes from a 30 s B2 TDS bisection on that event. For that event the rule is in-sample (calibration = event); it is not a pre-event-data-only rule.",
           "separation": {"Vsafe": "voltage set-points v0 and P dispatch of the B3-A AC selection (ANDES PFlow initial condition)", "SG31_correction": "inside Vsafe: SG31 pre-event P lowered from 6.46 to 6.361 pu by the B3-A equilibrium (reserve 0.040 -> 0.1389 pu); no separate hook", "R35": "incremental SG35 -> GFM transfer (delta=0.015 by bisection), R35_040 delta=0.040 (chosen)"}},
       "replay": {}}
cond = {}
for tag, dlt in DELTAS.items():
    s, c = J.make(EV.hook_for(dlt))
    st = K.rdc_state(s, c)
    y = np.asarray(s.dae.y, float)
    P, Q, V = y[st["a_p"]], y[st["a_q"]], y[st["a_v"]]
    cond[tag] = (P, Q, V)
s0, c0 = J.make(J.CONFIGS["C2t_Vsafe"])
st0 = K.rdc_state(s0, c0)
y0 = np.asarray(s0.dae.y, float)
P0 = y0[st0["a_p"]]
csvP = {r["unit"]: float(r["P_pu"]) for r in csv.DictReader(open(A / "IEEE39_E9B0_initial_condition_R35_040_units.csv"))}
P40 = cond["R35_040"][0]
rep["replay"]["R35_040"] = {"unit": NAMES, "P_pre_Vsafe_pu": P0.tolist(), "P_pre_replayed_pu": P40.tolist(), "dP0_pu": (P40 - P0).tolist(),
                            "P_pre_stored_csv_pu": [csvP[u] for u in NAMES], "max_abs_diff_replay_vs_stored_pu": float(np.abs(P40 - np.array([csvP[u] for u in NAMES])).max()),
                            "expected_dP0_pu": [(-0.040 if u == "SG35" else 0.0) + (0.040 * w_recomp[int(u[3:])] if u.startswith("GFM") else 0.0) for u in NAMES]}
rep["replay"]["R35_040"]["slack_and_losses_absorb_difference_pu"] = float(np.abs(np.array(rep["replay"]["R35_040"]["dP0_pu"]) - np.array(rep["replay"]["R35_040"]["expected_dP0_pu"])).max())
pmax = C.limits()["pmax"]
rep["replay"]["R35_040"]["reserve_R_i_pu"] = (pmax - P40).tolist()
rep["replay"]["R35"] = {"P_pre_replayed_pu": cond["R35"][0].tolist(), "reserve_R_i_pu": (pmax - cond["R35"][0]).tolist()}
rep["reproduced"] = bool(rep["replay"]["R35_040"]["max_abs_diff_replay_vs_stored_pu"] < 1e-5 and rep["weights_max_abs_diff"] < 1e-12)
# diagnostic only (NOT a candidate): weights from pre-event static headroom instead of simulated margins
R = pmax - P0
hw = {b: max(R[NAMES.index("GFM%d" % b)], 0) for b in (32, 37, 34, 36)}
tot = sum(hw.values())
rep["diagnostic_static_headroom_weights_NOT_A_CANDIDATE"] = {str(b): v / tot for b, v in hw.items()}
rep["status"] = "REPLAYED_FROM_IDENTIFIED_INPUTS" if rep["reproduced"] else "REPLAY_DISCREPANCY"
json.dump(rep, open(A / "IEEE39_DEC053_reserve_replay.json", "w"), indent=1, default=float)
print("replay", rep["status"], rep["replay"]["R35_040"]["max_abs_diff_replay_vs_stored_pu"], rep["weights_max_abs_diff"], rep["replay"]["R35_040"]["slack_and_losses_absorb_difference_pu"])

# ------------------------------------------------------------------ C4: validation table with signed errors (observed - predicted margin)
rows = []
LIB = "fast/slow increments observed in the R35_040 B2 run, P+ 58.564 MW, bus 4 (library scaled linearly with amplitude)"
for tag, f, role, ev in (("H3-1", "IEEE39_DEC051_H3_sim1.json", "dynamic validation after model screening: same bus as library, amplitude 110 % (extrapolated by linear scaling)", "P+ 64.4204 MW bus 4"),
                         ("H3-2", "IEEE39_DEC051_H3_sim2.json", "dynamic prospective validation after analytic model screening (bus 18 chosen as smallest positive predicted margin)", "P+ 58.564 MW bus 18")):
    d = jl(f)
    for i, u in enumerate(NAMES):
        pm, om, er = d["predicted_margin_to_pmax_pu"][i], d["observed_margin_to_pmax_pu"][i], d["prediction_error_margin_pu"][i]
        cls = "EXACT_WITHIN_EPS_JUMP" if abs(er) <= EPS_JUMP else ("CONSERVATIVE" if er > 0 else "OPTIMISTIC")
        rows.append(dict(run=tag, event=ev, role=role, library=LIB, unit=u, predicted_margin_pu=pm, observed_margin_pu=om, signed_error_pu=er, error_in_eps_units=er / EPS_JUMP, classification=cls,
                         observed_peak_time_s=d["observed_t_of_peak_s"][i], binding=bool(u in ("SG31", "SG35") and om < 0.1), violation=bool(om < 0)))
it = jl("IEEE39_DEC051_H3_summary.json")["inequality_table"]
for cfg, dd in it.items():
    for u in ("SG31", "SG35"):
        r = dd[u]
        rows.append(dict(run="BUS4_58.564_" + cfg, event="P+ 58.564 MW bus 4", role="IN-SAMPLE: library taken from the R35_040 run of this event" if cfg == "C2t_Vsafe_R35_040" else "dispatch transfer of the library (other variants)",
                         library=LIB, unit=u, predicted_margin_pu=r["predicted_min_margin"], observed_margin_pu=r["observed_min_margin"], signed_error_pu=r["observed_min_margin"] - r["predicted_min_margin"],
                         error_in_eps_units=(r["observed_min_margin"] - r["predicted_min_margin"]) / EPS_JUMP,
                         classification="EXACT_WITHIN_EPS_JUMP" if abs(r["observed_min_margin"] - r["predicted_min_margin"]) <= EPS_JUMP else ("CONSERVATIVE" if r["observed_min_margin"] > r["predicted_min_margin"] else "OPTIMISTIC"),
                         observed_peak_time_s="", binding=True, violation=bool(r["observed_min_margin"] < 0)))
with open(A / "IEEE39_DEC053_reserve_validation.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
for tag in ("H3-1", "H3-2"):
    rr = [r for r in rows if r["run"] == tag]
    print(tag, "optimistic:", [(r["unit"], round(r["signed_error_pu"], 4)) for r in rr if r["classification"] == "OPTIMISTIC"], "max|e|", max(abs(r["signed_error_pu"]) for r in rr))

# ------------------------------------------------------------------ C5: dispatch check on stored B2 P+ series (fast jump vs slow maximum)
lim = C.limits()
c5 = {}
for lab, key in (("C2t", "E8_P+"), ("C2t_Vsafe", "E9B0_Vsafe_P+"), ("C2t_Vsafe_R35", "E9B0_Vsafe_R35_P+"), ("C2t_Vsafe_R35_040", "E9B0_Vsafe_R35_040_P+")):
    d = C.load(key)
    t, P = d["t"], d["P"]
    pre = P[t < C.T_EVENT - 1e-9][-1]
    c5[lab] = {}
    for u in ("SG31", "SG35"):
        i = NAMES.index(u)
        post = t > C.T_EVENT + 1e-9  # first sample strictly after the event carries the jump
        marg = lim["pmax"][i] - P[:, i]
        j0 = np.where(post)[0][0]
        jmin = j0 + int(np.argmin(marg[post]))
        c5[lab][u] = {"pre_margin_pu": float(lim["pmax"][i] - pre[i]), "first_sample_after_event_margin_pu": float(marg[j0]), "t_first_sample_s": float(t[j0]),
                      "worst_temporal_margin_pu": float(marg[jmin]), "t_worst_s": float(t[jmin]), "violation_duration_s": float(((marg < 0) & post).sum() * np.median(np.diff(t)))}
jump_alg = jl("IEEE39_DEC051_H3_summary.json")["attribution_voltage_vs_dispatch"]["per_configuration"]
json.dump({"stored_B2_P+_series_metrics": c5, "algebraic_jump_margins_after_jump": {k: {"SG31": v["margin_after_jump_SG31"], "SG35": v["margin_after_jump_SG35"]} for k, v in jump_alg.items()},
           "reading": "SG31 (C2t): algebraic jump margin -0.0465 pu at t=0+ (fast) vs worst temporal margin -0.0699 pu (fast + 0.15 s after); SG35 worst margin occurs ~7.8 s (slow electromechanical). Voltage-only Vsafe does not change SG31 (-0.0490); dispatch-only gives +0.0522: the SG31 benefit is dispatch. R35 adds SG35 margin only. OPEN-SG31-PMAX (original C2t) remains open."},
          open(A / "IEEE39_DEC053_reserve_attribution.json", "w"), indent=1, default=float)
print(json.dumps(c5, indent=0)[:1500])

# ------------------------------------------------------------------ figure
fig, ax = plt.subplots(1, 3, figsize=(15, 4.6))
cfgs = list(jump_alg.keys())
x = np.arange(len(cfgs))
ax[0].bar(x - 0.2, [jump_alg[k]["margin_after_jump_SG31"] for k in cfgs], 0.4, label="SG31", color="tab:blue")
ax[0].bar(x + 0.2, [jump_alg[k]["margin_after_jump_SG35"] for k in cfgs], 0.4, label="SG35", color="tab:orange")
ax[0].axhline(0, c="k", lw=0.8)
ax[0].set_xticks(x, [k.replace("C2t_", "").replace("C2t + ", "").replace(" only", "") for k in cfgs], rotation=35, ha="right", fontsize=7)
ax[0].set(ylabel="Pmax - P(0+) (pu)", title="algebraic jump margin by dispatch/voltage factor (P+ bus 4)")
ax[0].legend(fontsize=7)
lab = list(c5.keys())
xx = np.arange(len(lab))
for off, u, col in ((-0.2, "SG31", "tab:blue"), (0.2, "SG35", "tab:orange")):
    ax[1].bar(xx + off, [c5[l][u]["worst_temporal_margin_pu"] for l in lab], 0.4, label=u, color=col)
ax[1].axhline(0, c="k", lw=0.8)
ax[1].set_xticks(xx, [l.replace("C2t_", "") for l in lab], rotation=25, ha="right", fontsize=7)
ax[1].set(ylabel="worst Pmax - P(t), t>5 s (pu)", title="observed worst transient margin, B2, 200 s")
for i, l in enumerate(lab):
    ax[1].text(i + 0.2, c5[l]["SG35"]["worst_temporal_margin_pu"], f'{c5[l]["SG35"]["t_worst_s"]:.1f}s', fontsize=6, ha="center", va="bottom")
ax[1].legend(fontsize=7)
h2 = [r for r in rows if r["run"] == "H3-2"]
ax[2].bar(np.arange(10) - 0.2, [r["signed_error_pu"] for r in rows if r["run"] == "H3-1"], 0.4, label="H3-1 (bus 4, 110 %)", color="tab:green")
ax[2].bar(np.arange(10) + 0.2, [r["signed_error_pu"] for r in h2], 0.4, label="H3-2 (bus 18)", color="tab:purple")
ax[2].axhline(0, c="k", lw=0.8)
ax[2].axhspan(-EPS_JUMP, EPS_JUMP, color="gray", alpha=0.25, label="+/- eps_jump")
ax[2].set_xticks(range(10), NAMES, rotation=45, fontsize=7)
ax[2].set(ylabel="observed - predicted margin (pu)", title="signed prediction error (negative = optimistic)")
ax[2].legend(fontsize=7)
fig.tight_layout()
fig.savefig(C.FIG / "IEEE39_DEC053_reserve_attribution.png", dpi=150)
