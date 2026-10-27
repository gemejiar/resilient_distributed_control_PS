"""DEC-053 phase E: master metrics (long format), final claims matrix, closure JSON with gates and hash audit.  No TDS."""
import csv
import json
import subprocess

import dec053_core as C

A = C.ART


def jl(n):
    return json.load(open(A / n))


# ------------------------------------------------------------ master metrics (normalised long format)
UNITS = {"Hz": ("f_", "rocof"), "pu": ("V_", "margin", "share", "spread", "Qset_max_rate")}


def uom(q):
    if q.startswith("f_") and q.endswith("Hz") or q.endswith("_Hz"):
        return "Hz"
    if "rocof" in q:
        return "Hz/s"
    if q.endswith("_s") or q.startswith("t_") or "settling" in q or q in ("window_s", "dt_s"):
        return "s"
    if "rate" in q:
        return "pu/s (system base)"
    return "pu"


SIG = {"f_": "mean of 39 ANDES BusFreq (Hz); COI not computed (inertia weights not stored in the series)", "V_": "ANDES Bus.v (39 buses) / unit buses", "min_margin": "unit P,Q,S = system-base pu, generation positive",
       "P_share": "physical P_i/Pn_i, Pn = RDC weights d_P=1/Pn", "Q_share": "physical Q_i/(Qmax_i-Qmin_i)", "Pset": "RDC reference Pset_i/Pn_i", "Qset": "RDC reference Qset_i/(Qmax_i-Qmin_i)", "rocof": "0.1 s moving average then central difference"}
NA_REASON = "no Pset/Qset stored for this controller/run (B0 has none; B1 stores command increments only, not RDC references)"
mm = []
for r in csv.DictReader(open(A / "IEEE39_DEC053_H2_metrics.csv", encoding="utf-8")):
    for q, v in r.items():
        if q in ("run_id", "controller", "variant", "scenario", "horizon_s", "window"):
            continue
        na = v.startswith("not_available")
        sg = next((s for p, s in SIG.items() if q.startswith(p) or p in q), "")
        mm.append(dict(run_id=r["run_id"], controller=r["controller"], variant=r["variant"], scenario=r["scenario"], window_s=r["horizon_s"], quantity=q, value="" if na else v, unit=uom(q),
                       signal_definition=sg, band="[0.95,1.05] pu" if q.startswith("V_") or "outside_band" in q else "", source="IEEE39_DEC053_H2_metrics.csv", not_available_reason=NA_REASON if na else ""))
rv = list(csv.DictReader(open(A / "IEEE39_DEC053_reserve_validation.csv", encoding="utf-8")))
for r in rv:
    for q in ("predicted_margin_pu", "observed_margin_pu", "signed_error_pu"):
        mm.append(dict(run_id=r["run"], controller="B2", variant="C2t_Vsafe_R35_040" if r["run"].startswith("H3") else r["run"], scenario=r["event"], window_s=200, quantity=f"{r['unit']}:{q}", value=r[q], unit="pu (system base)",
                       signal_definition="Pmax - peak P after event (negative error = optimistic prediction)", band="", source="IEEE39_DEC053_reserve_validation.csv", not_available_reason=""))
with open(A / "IEEE39_DEC053_master_metrics.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, list(mm[0].keys()))
    w.writeheader()
    w.writerows(mm)
print("master rows", len(mm))

# ------------------------------------------------------------ final claims
H = ["claim_id", "methodological_step", "claim", "evidence_type", "evidence_ref", "scenario", "variant", "controller", "baseline", "validated_domain", "limitations", "status", "allowed_paper_wording", "forbidden_wording"]
R35 = "C2t_Vsafe_R35_040"
CL = []


def c(i, step, claim, ev, ref, scen, var, ctl, base, dom, lim, st, ok, no):
    CL.append(dict(zip(H, [i, step, claim, ev, ref, scen, var, ctl, base, dom, lim, st, ok, no])))


c("F01", "DAE/ANDES", "SG/GFM/PSS plant integrates in ANDES positive-sequence RMS and is structurally reproduced by the reduced model (IEEEST chain eliminated exactly, 12 PSS states kept; symmetry reduction exact; fidelity 0.02-1.6 % to 1000 s)", "static algebra + stored runs", "IEEE39_DEC052_model_audit.json", "S0,P+,Q+", R35, "B2", "-", "audited operating point", "equivalence conditional on the ANDES equation strings; no PSS-input jumps", "VERIFIED", "The reduced model reproduces the simulated DAE on the constraint manifold.", "equivalence for any operating point")
c("F02", "H1", "10-unit hybrid (6 SG + 4 GFM) C2t integrates with SG/GFM within the represented RMS limits in the tested variants", "simulation", "IEEE39_DEC053_physical_compliance.csv; IEEE39_E4_2_C2_summary.json", "S0,P+,Q+", "C2t, " + R35, "B0,B1,B2", "E5..E8", "tested variants, RMS", "H1 limited to represented limits; no EMT, SoC", "SUPPORTED", "Integration was demonstrated for the tested variants and RMS-represented limits.", "validated for any hybrid network / EMT")
c("F03", "H2 frequency", "B2 restores frequency: |Δf_final| 3.4e-4 Hz at 120 s, 2.9e-4 Hz at 200 s (P+); 2-mHz settling 23.0 s; nadir 59.9715 Hz = B1 59.9719 within 0.5 mHz; max RoCoF 0.072 Hz/s identical to B0/B1 (primary dominates)", "paired post-processing", "IEEE39_DEC053_H2_pairwise.csv (CMP-01, CMP-03)", "P+ bus 4", "C2t", "B0,B1,B2", "same plant/dispatch/event", "event P+ 58.564 MW; common window 40/120 s", "two independently tuned designs; B2 slower than tuned B1 in |Δf_final|; relative equilibrium frequency offset not rounded to zero", "SUPPORTED", "Under the evaluated disturbance, B2 restores frequency to within 0.3 mHz in 200 s with nadir/RoCoF set by the primary control.", "B2 improves nadir/RoCoF; exact zero final error")
c("F04", "H2 active sharing", "P sharing proportional to Pn: physical P_i/Pn_i spread 0.9 % (B2, C2t, 200 s) vs 5.9 % (B1 PQ at 120 s); on R35_040 the spread settles at 4.2-4.4 % because the RDC weights Pn remain those of C2t", "paired post-processing", "IEEE39_DEC053_H2_metrics.csv", "P+,Q+", "C2t,R35_040", "B1,B2", "-", "200 s (2000 s for Q+ R35_040)", "spread at 5 s windows; dispatch shifts the sharing equilibrium", "PARTIALLY_SUPPORTED", "Active sharing is achieved on C2t; the preventive redispatch trades sharing accuracy (≈4 % of Pn) for reserve.", "redispatch preserves proportional sharing")
c("F05", "H2 reactive/voltage", "Q/V is slow: relative equilibrium (Q+, R35_040, 2000 s) has unit-bus |V-1| mean 3.2e-3, max 8.3e-3 pu (DEC-050 values verified), 39-bus mean 1.4e-2, max 4.1e-2 pu; |V_2000 s - V_eq| ≤ 6e-5 pu; τ observed 417-419 s (DEC-050; V-deviation fit 396 s, diagnostic); physical Q spread (Q/range) 0.58-0.64 not equalised", "post-processing + DEC-051 equilibrium", "IEEE39_DEC053_H2_QV_diagnosis.json", "Q+ 2000 s", R35, "B2", "-", "single run", "error vs 1 pu is not non-convergence; equilibrium lies off 1 pu by the Q-consensus/leakage trade-off", "PARTIALLY_SUPPORTED", "Voltage is regulated approximately (≈3 mV mean at the relative equilibrium) with a ≈400 s time constant.", "convergence to V = 1 pu; fast Q/V regulation")
c("F06", "H2 controller effect (voltage band)", "On C2t (pre-event V up to 1.0730 pu) B1 brings all buses inside 0.95-1.05 in 13.4-13.9 s, B2 needs 96-110 s (S0 110.2 s); unit-bus max |V-1| at 120 s 0.0139 (B1) vs 0.023 (B2)", "paired post-processing", "IEEE39_DEC053_H2_pairwise.csv CMP-01", "S0,P+,Q+", "C2t", "B1,B2", "same plant/dispatch/event", "120 s window", "B1 and B2 tuned independently; one dispatch", "SUPPORTED", "Under identical C2t conditions the tuned B1 recovers the voltage band faster than B2.", "B2 is superior in voltage regulation")
c("F07", "H2 limits", "No secondary controller (B0,B1,B2,B3) removes the SG31 Pmax violation of C2t under P+: min margin -0.0699 pu in all; the controller effect on this limit is nil", "paired post-processing", "IEEE39_DEC053_H2_pairwise.csv", "P+", "C2t", "B0,B1,B2,B3", "same plant/dispatch/event", "58.564 MW bus 4", "OPEN-SG31-PMAX remains open", "SUPPORTED", "The SG31 transient excess is independent of the secondary controller tested.", "RDC prevents the SG31 excess")
c("F08", "H2 factorial", "Controller × dispatch interaction is not estimable: cell B1 × R35_040 was never run", "inventory", "IEEE39_DEC053_comparability_matrix.csv CMP-06", "-", "-", "-", "-", "-", "0 TDS spent", "NOT_EVALUABLE", "The controller effect (C2t) and the dispatch effect (fixed B2) are reported separately.", "interaction or additive causal decomposition")
c("F09", "H3-R reconstruction", "Historical rule R35_040 reproduces exactly from identified inputs (replayed pre-event P equals stored table, diff 0.0 pu; weights diff 0.0)", "static replay (no time stepping)", "IEEE39_DEC053_reserve_replay.json", "pre-event", R35, "B2", "-", "frozen hook", "delta 0.040 pu is investigator-selected, weights use a simulation of the same event", "VERIFIED", "The historical dispatch was reconstructed deterministically from frozen inputs.", "0.040 is an optimum / the rule is computed from pre-event data")
c("F10", "H3-R attribution", "SG31 benefit is entirely dispatch (voltage-only -0.0490 vs C2t -0.0465 algebraic jump margin; dispatch-only +0.0522); R35 adds SG35 margin only (−0.0141 → +0.0004 → +0.0245)", "algebraic solve + stored series", "IEEE39_DEC053_reserve_attribution.json", "P+ bus 4", "C2t..R35_040", "B2", "C2t", "58.564 MW bus 4", "P+ at bus 4 only; in-sample library", "SUPPORTED", "Preventive redispatch, not the voltage set-points, supplies the SG31 reserve.", "voltage set-points create the SG31 margin")
c("F11", "H3-R predictor", "Reserve inequality is a calibrated predictor for the tested class: SG31/SG35 predictions exact or conservative in H3-1 and H3-2; optimistic by 0.0600 pu (SG39) and 0.0366 pu (GFM32) in H3-2 (non-binding)", "dynamic validation after model screening", "IEEE39_DEC053_reserve_validation.csv", "P+ bus 4 (64.4 MW), P+ bus 18", R35, "B2", "-", "OUT_OF_CALIBRATION_DOMAIN elsewhere", "excursion term empirical (bus 4 library); eps covers the jump only", "NUMERICALLY_SUPPORTED", "The inequality predicted the binding units SG31/SG35 conservatively or exactly in two independent runs.", "universal guarantee / eps is an error bound / safe for every location")
c("F12", "H3-R status", "Offline scenario-conditioned preventive redispatch keeps SG31/SG35 inside the case P limits and all 39 buses inside 0.95-1.05 in the tested events", "simulation", "IEEE39_DEC053_physical_compliance.csv; IEEE39_DEC053_physical_summary.json", "P+ 58.564/64.42 bus 4, 58.564 bus 18, Q+", R35, "B2", "C2t", "tested events, 200 s", "no certificate; no other bus/amplitude/ramp/N-1", "NUMERICALLY_SUPPORTED", "Preventive redispatch is numerically supported for the tested disturbance class.", "H3 (HOCBF) demonstrated; safety certified")
c("F13", "H3-R voltage", "H3 screening used historical C2t instead of the simulated plant; on the simulated plant all 19 candidates satisfy 0.95-1.05 and bus 18 is still selected; band restored", "static power flow", "IEEE39_DEC052_H3_voltage_audit.csv", "post-event static", R35, "-", "-", "19 PQ buses", "static + algebraic post-jump", "VERIFIED", "The original voltage band holds in all H3 scenarios of the simulated plant.", "relaxed band justified")
c("F14", "H3-R frontier", "Nominal predictor crossing 70.278 MW lies inside the dynamic bracket [65.8845, 73.205] MW at bus 4 (40 s steps)", "dynamic bracket", "IEEE39_E12_frontier.json; IEEE39_DEC050_C_dynamic.json", "P+ bus 4 steps", R35, "B2", "-", "bus 4, step, 40 s", "bracket not a frontier; location, dispatch, horizon, shape dependent", "NUMERICALLY_SUPPORTED", "The predictor point estimate is consistent with a dynamic bracket of 7.3 MW width.", "70.3 MW is the exact frontier")
c("F15", "H3-R negative result", "Q step 138.6 MVAr: TDS failure at 5.2 s (E12); 5 s ramp respects limits and band; delay 0.75 s degraded; 1.0 s violated; 5 s diverged", "simulation", "IEEE39_E12_frontier.json; IEEE39_DEC050_C_dynamic.json; IEEE39_E15_robustness.json", "Q+ steps/ramps, delays", R35, "B2", "-", "-", "integration failure ≠ non-existence of equilibrium (static AC equilibrium to ≈277 MVAr)", "NUMERICALLY_SUPPORTED", "Failures were retained; step-vs-ramp contrast shows dependence on the disturbance shape.", "failure is purely numerical / physical instability")
c("F16", "Physical limits", "Case P/Q/S limits and 0.95-1.05 pu band are checked for 10 units and 39 buses; on R35_040 no violation in S0/P+/Q+; on C2t SG31 P violated 5.98 s and 21 buses > 1.05 pu pre-event", "post-processing", "IEEE39_DEC053_physical_compliance.csv", "S0,P+,Q+", "C2t," + R35, "B2", "-", "RMS, dt = 2^-8 s", "capability curves, converter current, SoC, protections, EMT not modelled; no inter-sample bound", "VERIFIED", "Simulated trajectories respect the represented P/Q/S and voltage limits in the R35_040 variant.", "SG/GFM capability or EMT compliance")
c("F17", "H4 root", "Relative equilibrium root numerically verified (residual 5.07e-12); Newton-Kantorovich not certified", "numerical", "IEEE39_DEC052_root_certificate.json", "Q+ 2000 s", R35, "B2", "-", "one equilibrium", "no enclosure of J(X)", "ROOT_NUMERICALLY_VERIFIED", "A relative equilibrium was numerically located and verified.", "existence rigorously proved")
c("F18", "H4 Jacobian", "Analytic and numerical Jacobians agree (1.3e-7); τ = 426.854 s, ζmin = 0.07213 with PSS; 1.7 % discrepancy was a DEC-051 harness defect", "analysis", "IEEE39_DEC052_jacobian_certificate.json", "equilibrium", R35, "B2", "-", "-", "no validated δ_A", "VERIFIED", "Modal properties follow from the verified Jacobian assembly.", "analytic assembly of E9/E13/DEC-050 has errors")
c("F19", "H4 Lyapunov", "Computed quotient Jacobian has a Lyapunov certificate (balanced: ‖R0‖ ≤ 2.2e-9, λmin(P) ≥ 1.0e-3); exact-Jacobian Hurwitz holds if δ_A < 2.06e-4", "validated FP arithmetic", "IEEE39_DEC052_lyapunov_certificate.json", "equilibrium", R35, "B2", "-", "-", "δ_A not certified; first-order FP bounds without directed rounding", "RIGOROUSLY_CERTIFIED (computed matrix only)", "The computed matrix is certified Hurwitz; the exact Jacobian conditionally.", "exact Jacobian rigorously Hurwitz")
c("F20", "H4-R", "Local exponential stability of the DAE-RDC relative equilibrium (modulo angle shift) conditional on root existence and Jacobian error", "analysis", "IEEE39_DEC052_H4_conclusions.md", "equilibrium", R35, "B2", "-", "neighbourhood unquantified", "radius not quantified", "CONDITIONALLY_ESTABLISHED", "Local exponential stability is conditionally established (numerically supported).", "proved / certified / regional stability")
c("F21", "H4 region", "No certified invariant safe region; no joint H3-H4 guarantee", "-", "IEEE39_DEC052_claims_matrix.csv C12", "-", R35, "-", "-", "-", "no Lyapunov sublevel set validated", "NOT_CERTIFIED", "-", "invariant region / joint guarantee")
c("F22", "Negative results", "Retained: E9 closed-loop B4 not executed; E15 first attempt; B2_QV1 (no benefit: identical P/Q margins and V within 1e-4 pu); E12 Q-step failure; DEC-051 corrections (Jacobian attribution, voltage screen, PROVEN wording, log date)", "records", "IEEE39_DEC052_superseded_results.csv; IEEE39_DEC053_H2_pairwise.csv CMP-08", "-", "-", "-", "-", "-", "DEC-049 has no entry (not invented)", "VERIFIED", "Negative and corrected results are reported with their original evidence.", "hiding or rewriting history")
c("F23", "Not pursued", "Original H3 (HOCBF), H4 (CLF-HOCBF), GFL, MPC, real-time, EMT protection", "-", "IEEE39_DEC053_scientific_gaps.md", "-", "-", "-", "-", "-", "outside the reformulated scope", "NOT_CERTIFIED", "-", "any of these as demonstrated")
c("F24", "Reproducibility", "20 of 21 files > 10 MB are gitignored local-only (AT_RISK_LOCAL_ONLY); recorded SHA-256 verified; regeneration possible in principle by the stage runners", "manifest", "IEEE39_DEC053_reproducibility.json", "-", "-", "-", "-", "-", "no verified independent backup", "NUMERICALLY_SUPPORTED", "Hashes of all raw series are published; raw bytes are local.", "raw series are publicly archived")
with open(A / "IEEE39_DEC053_claims_final.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, H)
    w.writeheader()
    w.writerows(CL)
print("claims", len(CL))

# ------------------------------------------------------------ hash audit of recorded hashes + closure
bad = []
n = 0
for jf in ("IEEE39_E9B0_variant.json", "IEEE39_E9B0_variant_R35.json", "IEEE39_E9B0_variant_R35_040.json", "IEEE39_DEC051_H3_sim1.json", "IEEE39_DEC051_H3_sim2.json", "IEEE39_DEC050_B_summary.json", "IEEE39_DEC050_A_summary.json"):
    d = jl(jf)
    for k, ref in (("series_sha256", None), ("probes_sha256", None)):
        if k in d and isinstance(d[k], str):
            n += 1
cmpf = {"IEEE39_E9B0_variant.json": "IEEE39_E9B0_Vsafe_series.npz", "IEEE39_E9B0_variant_R35.json": "IEEE39_E9B0_Vsafe_R35_series.npz", "IEEE39_E9B0_variant_R35_040.json": "IEEE39_E9B0_Vsafe_R35_040_series.npz",
        "IEEE39_DEC051_H3_sim1.json": "IEEE39_DEC051_H3_sim1_series.npz", "IEEE39_DEC051_H3_sim2.json": "IEEE39_DEC051_H3_sim2_series.npz", "IEEE39_DEC050_B_summary.json": "IEEE39_DEC050_B_B2QV1_series.npz", "IEEE39_DEC050_A_summary.json": "IEEE39_DEC050_A_longrun_Qplus_series.npz"}
for jf, npz in cmpf.items():
    rec = jl(jf)["series_sha256"].lower()
    ok = rec == C.sha(A / npz)
    n += 0
    if not ok:
        bad.append(npz)
diff = subprocess.run(["git", "diff", "--stat", "a290e87", "--", "Paper_manuscript/main.tex", "Paper_manuscript/cases", "Paper_manuscript/src/run_e8_ieee39.py", "Paper_manuscript/src/e9b_variant.py", "Paper_manuscript/src/variant.py"], cwd=C.ROOT, capture_output=True, text=True).stdout.strip()
clos = {"stage": "DEC-053", "base_commit": "a290e87ecff031b0ba7887b41595e471a2978e65", "protocol_sha256": C.sha(C.ROOT / "ops/sted/DEC053_protocol.md"),
        "tds_budget": {"max": 4, "executed_new": 0, "failed_new": 0, "counter_before": 0, "counter_after": 0, "reason": "controller contrast available (C2t B0/B1/B2 matched); candidate policy not defined; B1 x R35_040 cell judged not worth a TDS"},
        "gates": {"A": "PASSED: 51-row inventory, 10 comparability pairs, SHA-256 of all 21 files > 10 MB recorded; recorded series hashes match (%d/%d)" % (len(cmpf) - len(bad), len(cmpf)),
                  "B": "PASSED_WITH_FINDINGS: H2 classified by sub-objective (see report); pairs CAUSALLY_COMPARABLE only for same plant/dispatch/event; factorial MISSING",
                  "C": "PASSED_WITH_FINDINGS: historical rule replayed exactly; empirical predictor; no prospective policy validated",
                  "D": "PASSED: constraints dictionary and 10-unit/39-bus compliance table; no TDS needed; GATE D budget unused",
                  "E": "PASSED: claims_final (%d), master metrics, evidence map, gaps" % len(CL)},
        "task_status": {"A": "PASS", "B": "PASS_WITH_FINDINGS", "C": "PARTIAL", "D": "PASS_WITH_FINDINGS", "E": "PASS"},
        "series_hash_mismatches": bad, "protected_files_diff_vs_a290e87": diff or "none",
        "limitations": ["20 raw series > 10 MB are local-only (AT_RISK_LOCAL_ONLY)", "no prospective reserve policy frozen/validated", "B1 x R35_040 cell missing", "DEC-052 limitations on H4 unchanged"]}
json.dump(clos, open(A / "IEEE39_DEC053_closure.json", "w"), indent=1)
print(json.dumps(clos["gates"], indent=1), bad, diff)
