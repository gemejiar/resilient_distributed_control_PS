"""DEC-053 phase A: forensic inventory, comparability matrix, reproducibility manifest (no TDS)."""
import csv
import json
import platform
import subprocess
import sys

import numpy as np

import dec053_core as C

A = C.ART


def git(*a):
    return subprocess.run(["git", *a], cwd=C.ROOT, capture_output=True, text=True).stdout.strip()


tracked = set(git("ls-files", "Paper_manuscript/artifacts").split("\n"))
SUMMARY = {"E5": "E5_C2t", "E6": "E6_C2t", "E7": "E7_C2t", "E8": "E8_C2t"}


def jload(n):
    try:
        return json.load(open(A / n))
    except Exception:
        return {}


def commit_of(s):
    if s["stage"] in SUMMARY:
        return jload(f"IEEE39_{SUMMARY[s['stage']]}_summary.json").get("git_commit", "")
    if s["stage"] == "B3":
        return jload(f"IEEE39_B3_C2t_{'Pplus' if s['scenario']=='P+' else 'Qplus' if s['scenario']=='Q+' else 'S0'}_summary.json").get("git_commit", "")
    if s["stage"] == "E9-B0":
        v = s["variant"].replace("C2t_", "")
        n = "IEEE39_E9B0_variant.json" if v == "Vsafe" else f"IEEE39_E9B0_variant_{v.replace('Vsafe_', '')}.json"
        return jload(n).get("git_commit", "")
    if s["stage"] == "DEC050-B":
        return jload("IEEE39_DEC050_B_summary.json").get("git_commit", "")
    if s["stage"] == "DEC050-A":
        return jload("IEEE39_DEC050_A_summary.json").get("git_commit", "")
    return ""


def solver_of(s):
    if s["stage"] in SUMMARY:
        sv = jload(f"IEEE39_{SUMMARY[s['stage']]}_summary.json").get("solver", {})
        return f"{sv.get('method')} dt={sv.get('time_step_s')} tol={sv.get('tolerance')} itmax={sv.get('maximum_iterations')}"
    return "trapezoid dt=0.00390625 (as E8; stage JSON)" if s["t_end"] <= 200 else "trapezoid; stored decimated series (dt=0.390625 s)"


REF = {"B0": "none (primary P-f/Q-V only)", "B1_P": "consensus PI on P; no Q layer", "B1_PQ": "consensus PI P and Q (rho, offsets, k_V=0.1)",
       "B2": "original RDC Eqs.(26)-(35): Pset/Qset integrators, d_P=1/Pn, d_Q=1/(Qmax-Qmin), v_ref=1.0", "B2_QV1": "B2 with QV1 capability floor (failed correction, retained)",
       "B3": "centred RDC with privileged pre-event knowledge xi* (not deployable)"}
VARNOTE = {
    "C2t": "historic C2t dispatch: pre-event V up to 1.0730 pu (21 buses > 1.05); SG31 Pmax violated at t=0+ under P+ (OPEN-SG31-PMAX)",
    "C2t_Vsafe": "Vsafe dispatch change (initial condition); SG31 margin positive at jump; SG35 transient margin negative",
    "C2t_Vsafe_R35": "Vsafe + R35 transfer; SG35 margin +4.1e-4 pu",
    "C2t_Vsafe_R35_040": "reference physical variant; delta = 0.040 pu transferred (historical tuned value)"}

rows = []
for s in C.SOURCES:
    p = A / s["file"]
    ev = C.EV[s["scenario"]]
    rel = str(p.relative_to(C.ROOT)).replace("\\", "/")
    rows.append(dict(
        run_id=s["key"], source_stage=s["stage"], commit=commit_of(s), case_variant=s["variant"], controller=s["controller"], dispatch_id=s["dispatch"],
        scenario=s["scenario"], event_bus=ev[0] if ev[0] else "", event_deltaP_MW=ev[1], event_deltaQ_MVAr=ev[2], event_time_s=5.0 if ev[0] else "",
        t_start_s=0.0, t_end_s=s["t_end"], solver_settings=solver_of(s), all_units="yes (10)", all_39_buses="yes",
        raw_path=rel, raw_sha256=C.sha(p) if p.exists() else "MISSING",
        reference_definition=REF[s["controller"]], physical_limits_id="E8_unit_limits_system_base_pu (Pmax,Pmin,Qmax,Qmin,Smax; case xlsx sha C8BFA9DA...)",
        comparable_group="", limitations=VARNOTE[s["variant"]] + ("" if rel in tracked else "; series gitignored (local only)")))
for r in rows:
    r["comparable_group"] = "G_C2t_200s" if r["case_variant"] == "C2t" and r["source_stage"] in ("E5", "E6", "E7", "E8") else \
        "G_R35_040_200s_B2" if r["case_variant"] == "C2t_Vsafe_R35_040" else "G_DISPATCH_B2" if r["controller"] == "B2" else "G_" + r["controller"]
extra = [
    ("E0_C0", "E0", "none", "C0_10SG", "ANDES ieee39 flat", "IEEE39_E0_C0_timeseries.npz", "integration control, not controller-comparable"),
    ("E1_C0", "E1", "none", "C0_10SG", "P step 1% bus 4", "IEEE39_E1_C0_timeseries.npz", "integration control"),
    ("E2_C0", "E2", "none", "C0_10SG", "Q step 1% bus 21", "IEEE39_E2_C0_timeseries.npz", "integration control"),
    ("E3_C0a", "E3", "none", "C0a_9SG_1GFM", "flat + small P/Q", "IEEE39_E3_C0a_timeseries.npz", "integration control"),
    ("E4_C1", "E4", "none", "C1_8SG_2GFM", "flat + small P/Q", "IEEE39_E4_C1_timeseries.npz", "integration control"),
    ("E4_1_C1a", "E4.1", "none", "C1a_7SG_3GFM", "flat + small P/Q", "IEEE39_E4_1_C1a_timeseries.npz", "integration control"),
    ("E4_2_C2", "E4.2", "none", "C2_6SG_4GFM", "flat + small P/Q", "IEEE39_E4_2_C2_timeseries.npz", "integration control; original C2 (not C2t)"),
    ("E5_C2", "E5", "B0", "C2_6SG_4GFM", "S1alt 1% P/Q", "IEEE39_E5_C2_timeseries.npz", "original C2 plant (not C2t): not comparable with C2t runs"),
    ("E5_C2_S1screen_FAIL", "E5", "B0", "C2_6SG_4GFM", "100 MW/50 MVAr screen", "IEEE39_E5_S1screen_C2_100MW_50MVAr_FAIL_timeseries.npz", "FAILED screening run retained"),
    ("E6_C2", "E6", "B1_P", "C2_6SG_4GFM", "P+ 1%", "IEEE39_E6_C2_timeseries.npz", "original C2 plant; superseded by C2t"),
    ("E7L_C2", "E7", "B1_PQ", "C2_6SG_4GFM", "S0 P+ Q+", "IEEE39_E7L_C2_timeseries.npz", "original C2 plant; superseded by C2t"),
    ("E9A_replay", "E9-A", "B2", "C2t", "HOCBF diagnostic replay", "IEEE39_E9A_replay_series.npz", "diagnostic replay; no HOCBF controller deployed"),
    ("E9H_error_bounds", "E9-H", "B2", "C2t_Vsafe_R35_040", "predictor error bound S0/P+/Q+", "IEEE39_E9H_error_bounds_R35_040.npz", "predictor-validation series"),
    ("DEC050A_probes", "DEC050-A", "B2", "C2t_Vsafe_R35_040", "Q+ 2000 s probes", "IEEE39_DEC050_A_longrun_Qplus_probes.npz", "Q+ 2000 s only; not P+"),
    ("DEC051_H3_sim1", "DEC051-H3-1", "B2", "C2t_Vsafe_R35_040", "P+ 64.4204 MW bus 4", "IEEE39_DEC051_H3_sim1_series.npz", "reduced series (P,Q,V,f_hz)"),
    ("DEC051_H3_sim2", "DEC051-H3-2", "B2", "C2t_Vsafe_R35_040", "P+ 58.564 MW bus 18", "IEEE39_DEC051_H3_sim2_series.npz", "reduced series (P,Q,V,f_hz)"),
    ("DEC051_H4_perturb_plus", "DEC051-H4", "B2", "C2t_Vsafe_R35_040", "local perturbation +", "IEEE39_DEC051_H4_perturb_plus.npz", "state perturbation series"),
    ("DEC051_H4_perturb_minus", "DEC051-H4", "B2", "C2t_Vsafe_R35_040", "local perturbation -", "IEEE39_DEC051_H4_perturb_minus.npz", "state perturbation series"),
    ("E7_C2_attempt1_FAIL", "E7", "B1_PQ", "C2_6SG_4GFM", "kV 0.5", "IEEE39_E7_C2_attempt1_kV0.5_FAIL_summary.json", "failed tuning attempt retained (summary only)"),
    ("E7_C2_attempt2_FAIL", "E7", "B1_PQ", "C2_6SG_4GFM", "kV 0.1", "IEEE39_E7_C2_attempt2_kV0.1_FAIL_summary.json", "failed tuning attempt retained (summary only)"),
    ("E7_C2t_attempt3_FAIL", "E7", "B1_PQ", "C2t", "undifferentiated P checks", "IEEE39_E7_C2t_attempt3_undifferentiated_P_checks_FAIL_summary.json", "failed attempt retained (summary only)"),
    ("E8_C2t_attempt1_FAIL", "E8", "B2", "C2t", "kIQ 1.2", "IEEE39_E8_C2t_attempt1_kIQ1p2_FAIL_summary.json", "failed attempt retained (summary only)"),
    ("E8_C2t_attempt2_FAIL", "E8", "B2", "C2t", "kIQ 0.3 inner slow", "IEEE39_E8_C2t_attempt2_kIQ0p3_innerslow_FAIL_summary.json", "failed attempt retained (summary only)"),
    ("E8_C2t_attempt3_FAIL", "E8", "B2", "C2t", "inner fast", "IEEE39_E8_C2t_attempt3_innerfast_FAIL_summary.json", "failed attempt retained (summary only)"),
    ("E9H_firstrun_FAIL", "E9-H", "B2", "C2t_Vsafe_R35_040", "S0 cost gate failed", "IEEE39_E9H_b4_R35_040_firstrun_S0_cost_gate_failed.json", "failed gate retained (JSON)"),
    ("E15_firstattempt", "E15", "B2", "C2t_Vsafe_R35_040", "robustness first attempt", "IEEE39_E15_robustness_firstattempt.json", "negative/first attempt retained"),
]
for rid, st, ctl, var, scen, f, lim in extra:
    p = A / f
    rel = str(p.relative_to(C.ROOT)).replace("\\", "/")
    rows.append(dict(run_id=rid, source_stage=st, commit="see experiment_matrix.csv", case_variant=var, controller=ctl, dispatch_id=var, scenario=scen, event_bus="", event_deltaP_MW="", event_deltaQ_MVAr="",
                     event_time_s="", t_start_s="", t_end_s="", solver_settings="see stage JSON", all_units="see file", all_39_buses="see file", raw_path=rel, raw_sha256=C.sha(p) if p.exists() else "MISSING",
                     reference_definition=REF.get(ctl, "none"), physical_limits_id="stage JSON", comparable_group="G_not_comparable", limitations=lim + ("" if rel in tracked else "; gitignored (local only)")))
cols = list(rows[0].keys())
with open(A / "IEEE39_DEC053_inventory.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, cols)
    w.writeheader()
    w.writerows(rows)
missing = [r["run_id"] for r in rows if r["raw_sha256"] == "MISSING"]
print("inventory rows", len(rows), "missing", missing)

cm = []


def add(i, q, a, b, status, why, same):
    cm.append(dict(pair_id=i, question=q, cell_A=a, cell_B=b, status=status, same_plant_dispatch=same[0], same_event=same[1], same_horizon=same[2], same_solver=same[3], explanation=why))


add("CMP-01", "Controller effect B1(PQ) vs B2", "E7t (S0,P+,Q+)", "E8 (S0,P+,Q+)", "AVAILABLE_MATCHED",
    "Same case xlsx (sha C8BFA9DA), same C2t dispatch, same events (+58.564 MW bus 4; +17.345 MVAr bus 21 at 5 s), same trapezoid dt=2^-8 s; horizons 120 s vs 200 s -> compare on common window 0-120 s. Gains were tuned independently per design (comparison of two tuned designs, not of a law class).", ("yes", "yes", "common window 120 s", "yes"))
add("CMP-02", "Controller effect B1(P) vs B2 (P+ only)", "E6t (P+)", "E8 (P+)", "AVAILABLE_PARTIAL", "P-only secondary without Q layer: Q/V objective differs; compare frequency/P only on common window 0-80 s.", ("yes", "yes (P+)", "common window 80 s", "yes"))
add("CMP-03", "Primary reference B0 vs B2", "E5t (P+,Q+)", "E8 (P+,Q+)", "AVAILABLE_MATCHED", "B0 is the physical reference, not a reserve treatment; horizon 40 s common window only.", ("yes", "yes", "common window 40 s", "yes"))
add("CMP-04", "Controller effect B0/B1/B2 under R35_040 dispatch", "B0,B1 on C2t_Vsafe_R35_040", "B2 on C2t_Vsafe_R35_040", "MISSING", "No B0 or B1 run exists on the Vsafe/R35 variants; creating one is the gate-D first-priority TDS but is not needed because CMP-01 already contrasts controllers on identical dispatch and events.", ("n/a", "n/a", "n/a", "n/a"))
add("CMP-05", "Dispatch effect under fixed B2", "E8 (C2t)", "E9B0 Vsafe / Vsafe_R35 / Vsafe_R35_040 (B2)", "AVAILABLE_PARTIAL",
    "Same controller, events, solver, 200 s; dispatch/initial condition differ (Vsafe voltages and SG31 correction; R35 transfer SG35->GFMs). Benefit is attributed to dispatch under fixed B2, never to the secondary algorithm. Pre-event states differ (voltage profile and P0), so frequency metrics are not a pure dispatch effect.", ("no (the factor)", "yes", "yes 200 s", "yes"))
add("CMP-06", "Controller x dispatch factorial 2x2 (B1,B2 x C2t,R35_040)", "B1/C2t, B2/C2t, B2/R35_040", "B1/R35_040", "MISSING", "Three of four cells exist; B1 x R35_040 was never run. Interaction cannot be estimated; no factorial claim. Not filled: marginal value does not justify a TDS (budget default 0).", ("no", "yes", "n/a", "n/a"))
add("CMP-07", "B3 centred vs B2", "B3 (C2t S0,P+,Q+)", "E8 B2 (C2t) and B2replica", "AVAILABLE_PARTIAL", "B3 uses privileged pre-event knowledge xi*; not a deployable causal controller. Retained as an upper reference only.", ("yes", "yes", "yes 200 s", "yes"))
add("CMP-08", "B2 vs B2_QV1 (failed correction)", "E9B0 R35_040 (B2)", "DEC050-B B2_QV1", "AVAILABLE_MATCHED", "Same dispatch, events, solver; B2_QV1 differs by the capability floor in the voltage term; negative result retained.", ("yes", "yes", "yes 200 s", "yes"))
add("CMP-09", "Q+ 2000 s equilibrium diagnosis vs 200 s performance", "DEC050-A (Q+ 2000 s, decimated)", "E8/E9B0 (200 s)", "CONFOUNDED", "2000 s decimated Q+ run only (R35_040, B2): horizon not equivalent to the 200 s transients; there is no P+ 2000 s run (not inferred).", ("yes", "Q+ only", "no", "no (decimated)"))
add("CMP-10", "Voltage of historical C2t vs simulated R35_040", "C2t runs (pre-event up to 1.0730 pu)", "R35_040 runs (0.9794-1.0444 pu)", "CONFOUNDED", "Different initial voltage profiles; band compliance is assessed per simulated plant; static flow of another variant is never used.", ("no", "yes", "yes", "yes"))
with open(A / "IEEE39_DEC053_comparability_matrix.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, list(cm[0].keys()))
    w.writeheader()
    w.writerows(cm)

chk = {}
for a, b in (("E7t_P+", "E8_P+"), ("E5t_P+", "E8_P+"), ("E6t_P+", "E8_P+"), ("E7t_Q+", "E8_Q+"), ("E5t_Q+", "E8_Q+")):
    da, db = C.load(a), C.load(b)
    pa, pb = da["P"][da["t"] < 4.5].mean(axis=0), db["P"][db["t"] < 4.5].mean(axis=0)
    va, vb = da["V"][da["t"] < 4.5].mean(axis=0), db["V"][db["t"] < 4.5].mean(axis=0)
    chk[f"{a}__{b}"] = dict(max_abs_preP_diff_pu=float(np.abs(pa - pb).max()), max_abs_preV_diff_pu=float(np.abs(va - vb).max()),
                            dt_equal=bool(abs(np.median(np.diff(da["t"])) - np.median(np.diff(db["t"]))) < 1e-12))
print(json.dumps(chk, indent=1))
import andes
import scipy

RUN = {"E5": "run_e5_ieee39", "E6": "run_e6_ieee39", "E7": "run_e7_ieee39", "E8": "run_e8_ieee39", "B3": "run_b3_ieee39", "E9-B0": "run_e9b0_variant", "DEC050-B": "run_dec050_b_qv1", "DEC050-A": "run_dec050_a_longrun"}
man = dict(stage="DEC-053 A/E5", git_head=git("rev-parse", "HEAD"), base_commit="a290e87ecff031b0ba7887b41595e471a2978e65", branch=git("branch", "--show-current"),
           remote_main_expected="1a023d8fa333e62eb716e57a4d67561bb63ea3d0", protocol_sha256=C.sha(C.ROOT / "ops/sted/DEC053_protocol.md"),
           python=sys.version.split()[0], andes=andes.__version__, numpy=np.__version__, scipy=scipy.__version__, platform=platform.platform(),
           seeds="none (deterministic ANDES trapezoid TDS; SLSQP start points recorded in stage JSONs)", tds_new_executed=0, tds_new_failed=0, tds_budget_max=4,
           pairing_consistency=chk, missing_files=missing, big_series=[])
seen = set()
for r in rows:
    p = C.ROOT / r["raw_path"]
    if p.exists() and p.stat().st_size > 10e6 and r["raw_path"] not in seen:
        seen.add(r["raw_path"])
        rel = r["raw_path"]
        man["big_series"].append(dict(path=rel, bytes=p.stat().st_size, sha256=r["raw_sha256"], in_git=rel in tracked,
                                       backup="none verified: gitignored, no remote copy; the folder lies in a OneDrive-synchronised directory (sync state not verified here)" if rel not in tracked else "git tracked",
                                       status="AT_RISK_LOCAL_ONLY" if rel not in tracked else "TRACKED",
                                       regenerable="yes in principle: deterministic re-run of the stage runner with the frozen case xlsx and ANDES; byte-identical equality not asserted",
                                       reproduce_cmd=f"python Paper_manuscript/src/{RUN.get(r['source_stage'], '(stage runner)')}.py"))
json.dump(man, open(A / "IEEE39_DEC053_reproducibility.json", "w"), indent=1)
print("big", len(man["big_series"]), [b["status"] for b in man["big_series"]].count("AT_RISK_LOCAL_ONLY"))
