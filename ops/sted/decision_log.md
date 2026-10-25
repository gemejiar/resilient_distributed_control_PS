# STED Decision Log

STATUS: PENDING_COMPLETION

One entry per gate evaluation, phase transition, or integrator-level decision.
Keep entries short and evidence-anchored. This file is a project record, not scientific evidence.

## Decision Entry Template

```markdown
## DEC-XXX
Date:
Gate:
Decision:
Justification:
Evidence reviewed:
Blockers or limitations:
Responsible:
Status:
Next action:
```

## DEC-000 (EXAMPLE — delete before use)
Date: YYYY-MM-DD
Gate: G0
Decision: Example decision. Replace this entry with the first real project decision.
Justification: Illustrates the expected format; carries no project meaning.
Evidence reviewed: plan_maestro.md
Blockers or limitations: None.
Responsible: Integrator
Status: example
Next action: Remove this entry and log real gate decisions below.

## DEC-001
Date: 2026-08-30
Gate: G1
Decision: Adopt a single canonical status vocabulary for claims, evidence, and references across the template: VERIFIED, PARTIALLY_VERIFIED, PENDING_EVIDENCE, BLOCKED_BY_EVIDENCE, REFERENCE_NOT_VERIFIED, OBSOLETE, OUT_OF_SCOPE. Used identically in prose markers and in the `status` column of `ops/sted/traceability_matrix.csv`. `check_claim_evidence.py` compares case-insensitively; canonical written form is upper-case. Legacy short tokens (verified/pending/blocked/obsolete/out_of_scope) are retired.
Justification: `AGENTS.md` promoted `PENDING_EVIDENCE`, `BLOCKED_BY_EVIDENCE`, `REFERENCE_NOT_VERIFIED` while `check_claim_evidence.py`, `STED-RW_Lean.md` section 13.3, `prompt_maestro_STED_RW.md`, and the IEEE/Elsevier skill used a divergent lowercase set. An agent following AGENTS.md could write a status the checker rejects.
Evidence reviewed: AGENTS.md, ops/checks/check_claim_evidence.py, zPLantilla_STED_RW/STED-RW_Lean.md, zPLantilla_STED_RW/prompt_maestro_STED_RW.md, AI_TOOLS/skills/{sted-rw,ieee_elsevier_paper_skill}/SKILL.md, ops/sted/traceability_matrix.csv.
Blockers or limitations: Real projects created from an earlier template revision must migrate existing matrix rows to the new tokens.
Responsible: Integrator
Status: VERIFIED
Next action: None; applied. Propagate the same vocabulary if new checkers or skills reference claim status.

## DEC-002
Date: 2026-10-25
Gate: Scope approval and E0 authorization
Decision: Adopt the IEEE 39-bus system as the only experimental test system for the project. The 10- and 14-bus systems from the reference article are outside the experimental scope. Authorize read-only inspection followed by E0--C0, with a mandatory stop for human review before E1.
Justification: The investigator explicitly selected IEEE-39 for the full process and requested that the manuscript reflect this scope.
Evidence reviewed: User authorization dated 2026-10-25, plan_maestro.md, Paper_manuscript/main.tex.
Blockers or limitations: No experiment has been executed. IEEE-39 case identity, parameters, frequency base, model inventory, and E0 numerical behavior remain pending verification. Results from the reference article cannot be transferred to IEEE-39.
Responsible: Investigator
Status: VERIFIED
Next action: Perform the authorized read-only inventory and E0--C0; stop after producing the required frequency and voltage figures for human approval.

## DEC-003
Date: 2026-10-25
Gate: E0--C0 automatic gate
Decision: Assign `PASS_AUTO_WAIT_HUMAN` to E0--C0 and stop before E1.
Justification: The instrumented IEEE-39 case completed PFlow and a 10 s flat TDS run with all 39 bus-frequency and voltage signals recorded. The stored maximum frequency and voltage drifts were 0 within numerical resolution, below the provisional thresholds of 0.005 Hz and 0.001 pu. The final maximum algebraic residual was 4.216e-9.
Evidence reviewed: Paper_manuscript/artifacts/IEEE39_E0_C0_summary.json, Paper_manuscript/artifacts/IEEE39_E0_C0_timeseries.npz, Paper_manuscript/artifacts/IEEE39_E0_C0_run.log, Paper_manuscript/figures_main/IEEE39_E0_C0_frequency.png, Paper_manuscript/figures_main/IEEE39_E0_C0_voltage.png, Paper_manuscript/cases/ieee39_base_original.xlsx, Paper_manuscript/cases/ieee39_E0_C0_instrumented.xlsx.
Blockers or limitations: Human figure approval is pending. ANDES reports original-case warnings for `GENROU` instances whose `xl <= xd2`; these parameters were not altered and require review before interpreting perturbed dynamics. E0 does not establish nonlinear stability, safety, or general model validation.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: Investigator reviews both E0 figures and either approves E0 or requests repetition. E1 remains unauthorized.

## DEC-004
Date: 2026-10-25
Gate: E0--C0 human review
Decision: Approve E0--C0 and authorize E1 only.
Justification: The investigator explicitly confirmed review of the E0 frequency and voltage figures and instructed continuation.
Evidence reviewed: Investigator message dated 2026-10-25, DEC-003, E0 summary, raw data, and figures.
Blockers or limitations: Approval applies only to the E0 flat-run configuration. It does not resolve the original-case `GENROU` parameter warnings or establish broader stability or validation claims.
Responsible: Investigator
Status: VERIFIED
Next action: Execute E1 as a 1% active-load increment at bus 4 with the C0 plant and E0 instrumentation frozen; stop for human review before E2.

## DEC-005
Date: 2026-10-25
Gate: E1--C0 automatic gate
Decision: Assign `PASS_AUTO_WAIT_HUMAN` to E1--C0 and stop before E2.
Justification: A 58.564 MW active-load increase at bus 4 produced the expected frequency, governor, electrical-power, and voltage responses. PFlow and both TDS resolutions converged. Comparing `Δt=0.00390625 s` with `Δt/2` gave 0.32% difference in nadir deviation, 0.17% in RoCoF, and less than 1.5e-8 pu in voltage extrema.
Evidence reviewed: Paper_manuscript/artifacts/IEEE39_E1_C0_summary.json, Paper_manuscript/artifacts/IEEE39_E1_C0_timeseries.npz, Paper_manuscript/artifacts/IEEE39_E1_C0_run.log, Paper_manuscript/figures_main/IEEE39_E1_C0_frequency.png, Paper_manuscript/figures_main/IEEE39_E1_C0_voltage.png, Paper_manuscript/figures_main/IEEE39_E1_C0_power.png.
Blockers or limitations: Human figure approval is pending. RoCoF excludes the first 0.1 s after the ideal load step because the algebraic angle jump creates a step-size-dependent derivative impulse. Original-case `GENROU` warnings for `xl <= xd2` remain unresolved. E1 is numerical evidence only.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: Investigator reviews the E1 figures and either approves E1 or requests repetition. E2 remains unauthorized.

## DEC-006
Date: 2026-10-25
Gate: E1--C0 human review
Decision: Approve E1--C0 and authorize E2 only.
Justification: The investigator explicitly confirmed review and approval of the E1 figures and instructed continuation.
Evidence reviewed: Investigator message dated 2026-10-25, DEC-005, E1 summary, raw data, and figures.
Blockers or limitations: Approval applies only to the recorded E1 active-load test. It does not resolve original-case parameter warnings or establish nonlinear stability, robustness, or general model validation.
Responsible: Investigator
Status: VERIFIED
Next action: Execute E2 as a 1% reactive-load increment at bus 21 with `ΔP=0`, retaining C0 and the E0 instrumentation; stop for human review before E3.

## DEC-007
Date: 2026-10-25
Gate: E2--C0 automatic gate
Decision: Assign `PASS_AUTO_WAIT_HUMAN` to E2--C0 and stop before E3.
Justification: A 17.345 MVAr reactive-load increase at bus 21 produced the expected local voltage decrease and increased aggregate SG reactive-power and excitation response. PFlow and both TDS resolutions converged; all bus voltages remained within the case limits, and the refined-step comparison was within the predefined tolerances.
Evidence reviewed: Paper_manuscript/artifacts/IEEE39_E2_C0_summary.json, Paper_manuscript/artifacts/IEEE39_E2_C0_timeseries.npz, Paper_manuscript/artifacts/IEEE39_E2_C0_run.log, Paper_manuscript/figures_main/IEEE39_E2_C0_frequency.png, Paper_manuscript/figures_main/IEEE39_E2_C0_voltage.png, Paper_manuscript/figures_main/IEEE39_E2_C0_reactive_excitation.png.
Blockers or limitations: Human figure approval is pending. Original-case `GENROU` warnings for `xl <= xd2` remain unresolved. E2 is a numerical response test and does not establish voltage stability, nonlinear stability, or robustness.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: Investigator reviews the E2 figures and either approves E2 or requests repetition. E3 remains unauthorized.

## DEC-008
Date: 2026-10-25
Gate: E2--C0 human review
Decision: Approve E2--C0 and make E3--C0a the next eligible stage.
Justification: The investigator explicitly confirmed that the E2 figures were reviewed, consistent with the experiment, and approved.
Evidence reviewed: Investigator message dated 2026-10-25, DEC-007, E2 summary, raw data, and figures.
Blockers or limitations: Approval applies only to the recorded E2 reactive-load test. It does not establish voltage stability, nonlinear stability, robustness, or general model validity. Original-case `GENROU` parameter warnings remain unresolved.
Responsible: Investigator
Status: VERIFIED
Next action: On explicit instruction to continue, prepare and execute E3--C0a by replacing only SG32 with GFM32; stop for human review before E4.

## DEC-009
Date: 2026-10-25
Gate: E3--C0a automatic gate
Decision: Assign `PASS_AUTO_WAIT_HUMAN` to E3--C0a and stop before E4.
Justification: The variant contains nine GENROU units and one REGF1 at bus 32, with the original SG32 dynamic chain removed and PV_3 retained for PFlow initialization. Flat, signed 1% active-load, and signed 1% reactive-load tests converged with physically consistent response signs and step-size refinement. The GFM delivered nonzero P and Q. EIG found no positive-real-part modes.
Evidence reviewed: Paper_manuscript/cases/ieee39_C0a_9SG_1GFM.xlsx, Paper_manuscript/src/run_e3_ieee39.py, Paper_manuscript/artifacts/IEEE39_E3_C0a_summary.json, Paper_manuscript/artifacts/IEEE39_E3_C0a_timeseries.npz, Paper_manuscript/figures_main/IEEE39_E3_C0a_frequency.png, Paper_manuscript/figures_main/IEEE39_E3_C0a_voltage.png, Paper_manuscript/figures_main/IEEE39_E3_C0a_gfm_power.png.
Blockers or limitations: Human figure approval is pending. EIG reported 12 near-zero modes and an ill-conditioned eigenvector calculation, so strict Hurwitz stability is not claimed. Original-case `GENROU` warnings for `xl <= xd2` remain unresolved. REGF1 has no energy/SoC model, and E3 is not a nonlinear safety certificate.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: Investigator reviews the E3 figures and either approves E3 or requests repetition. E4 remains unauthorized.

## DEC-010
Date: 2026-10-25
Gate: E3--C0a human review
Decision: Approve E3--C0a and make E4--C1 the next eligible stage.
Justification: The investigator explicitly confirmed that the corrected E3 figures are coherent and approved them.
Evidence reviewed: Investigator message dated 2026-10-25, DEC-009, E3 summary, raw data, and corrected figures.
Blockers or limitations: Approval applies only to the recorded C0a flat and signed 1% P/Q diagnostic tests. It does not establish nonlinear stability, safety, strict Hurwitz stability, energy adequacy, or general model validity. The EIG near-zero modes and conditioning warning remain documented.
Responsible: Investigator
Status: VERIFIED
Next action: On explicit instruction to continue, prepare and execute E4--C1 by replacing only SG37 with GFM37; stop for human review before E4.1.

## DEC-011
Date: 2026-10-25
Gate: E4--C1 automatic gate
Decision: Assign `PASS_AUTO_WAIT_HUMAN` to E4--C1 and stop before E4.1.
Justification: The variant contains eight GENROU units and two REGF1 units (buses 32 and 37), with the SG37 dynamic chain removed and PV_8 retained. Flat and signed 1% P/Q runs converged, response signs were correct, step-size refinement was consistent, and both GFM delivered nonzero active power. The EIG physical subspace (after removing the degenerate IEEEST A1=A2=0 states) has no positive-real-part modes.
Evidence reviewed: Paper_manuscript/cases/ieee39_C1_8SG_2GFM.xlsx, Paper_manuscript/src/run_hybrid_replacement_ieee39.py, Paper_manuscript/artifacts/IEEE39_E4_C1_summary.json, Paper_manuscript/artifacts/IEEE39_E4_C1_timeseries.npz, Paper_manuscript/figures_main/IEEE39_E4_C1_*.png.
Blockers or limitations: Raw EIG contains spurious +1 modes from degenerate IEEEST blocks; strict Hurwitz stability is not claimed. REGF1 has no energy/SoC model. Diagnostic only, not a nonlinear safety certificate.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: Investigator reviews E4 figures.

## DEC-012
Date: 2026-10-25
Gate: E4--C1 human review
Decision: Approve E4--C1 and make E4.1--C1a (SG34 -> GFM34) the next eligible stage.
Justification: The investigator reviewed the E4 figures, found the behavior correct, and approved, instructing continuation with the plan.
Evidence reviewed: Investigator message dated 2026-10-25, DEC-011, E4 summary, raw data, and figures.
Blockers or limitations: Approval applies only to the recorded C1 flat and signed 1% P/Q diagnostic tests; no nonlinear stability, safety, strict Hurwitz stability, or energy adequacy is established.
Responsible: Investigator
Status: VERIFIED
Next action: Execute E4.1 by replacing only SG34 with GFM34; stop for human review before E4.2.

## DEC-013
Date: 2026-10-25
Gate: E4.1--C1a automatic gate
Decision: Assign `PASS_AUTO_WAIT_HUMAN` to E4.1--C1a (7 SG + 3 GFM; only SG34 replaced by GFM34) and stop before E4.2. Generalize the EIG degeneracy check of the shared runner.
Justification: Flat and signed 1% P/Q runs converged with correct signs and step-size consistency (nadir difference 1.4e-5 Hz); all three GFM deliver nonzero P and Q; the EIG physical subspace has no positive-real-part modes. A first run returned `FAIL` solely because the IEEEST-degeneracy check required all 7 IEEEST F1_y states to be retained, whereas ANDES retained only 3 (the others appear as F2_x2 with zero diagonal). The check now requires every retained F1_y diagonal to equal +1, those states to account for all raw unstable modes (3), and A1=A2=0 for all IEEEST. The physical criterion (no positive modes in the reduced subspace) is unchanged. The failed first run is disclosed here and was overwritten by the rerun.
Evidence reviewed: Paper_manuscript/cases/ieee39_C1a_7SG_3GFM.xlsx, Paper_manuscript/src/run_hybrid_replacement_ieee39.py, Paper_manuscript/artifacts/IEEE39_E4_1_C1a_summary.json, Paper_manuscript/figures_main/IEEE39_E4_1_C1a_*.png.
Blockers or limitations: Human figure approval pending. Raw EIG retains 3 spurious +1 modes and 9 near-zero modes with ill-conditioning; strict Hurwitz stability not claimed. REGF1 has no energy/SoC model. Diagnostic only.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: Investigator reviews E4.1 figures. E4.2 remains unauthorized.

## DEC-014
Date: 2026-10-25
Gate: E4.1--C1a human review
Decision: Approve E4.1--C1a and make E4.2--C2 (SG36 -> GFM36) the next eligible stage.
Justification: The investigator reviewed the E4.1 figures and explicitly approved them.
Evidence reviewed: Investigator message dated 2026-10-25, DEC-013, E4.1 summary, raw data, and figures.
Blockers or limitations: Approval applies only to the recorded C1a flat and signed 1% P/Q diagnostic tests; no nonlinear stability, safety, strict Hurwitz stability, or energy adequacy is established. EIG spurious/near-zero modes remain documented.
Responsible: Investigator
Status: VERIFIED
Next action: Execute E4.2 by replacing only SG36 with GFM36; stop for human review before E5.

## DEC-015
Date: 2026-10-25
Gate: E4.2--C2 automatic gate
Decision: Assign `PASS_AUTO_WAIT_HUMAN` to E4.2--C2 (6 SG + 4 GFM; only SG36 replaced by GFM36) and stop before E5.
Justification: Six GENROU and four REGF1 (buses 32, 34, 36, 37), no duplicate injection. Flat and signed 1% P/Q runs converged with correct signs; step-size nadir difference 2.8e-4 Hz (P+). All four GFM deliver nonzero P and Q. EIG physical subspace has no positive-real-part modes (max 4.6e-14); the 6 raw unstable modes equal the 6 retained degenerate IEEEST F1_y states (diagonal +1), verified under the DEC-013 criterion. Versus C1a: P+ nadir -0.0028 Hz, P+ minimum voltage -0.0093 pu, Q+ minimum voltage -0.0060 pu.
Evidence reviewed: Paper_manuscript/cases/ieee39_C2_6SG_4GFM.xlsx, Paper_manuscript/artifacts/IEEE39_E4_2_C2_summary.json, Paper_manuscript/figures_main/IEEE39_E4_2_C2_*.png.
Blockers or limitations: Human figure approval pending. Strict Hurwitz stability not claimed (spurious and 7 near-zero modes, ill-conditioning). REGF1 has no energy/SoC model; capacity (P2+Q2) and dispatch audits required by the plan for C2 freeze are not yet performed. Diagnostic only.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: Investigator reviews E4.2 figures. E5 remains unauthorized.

## DEC-016
Date: 2026-10-25
Gate: E4.2--C2 human review
Decision: Approve E4.2--C2, freeze the case file `ieee39_C2_6SG_4GFM.xlsx` as the scientific C2 base with ANDES 2.0.0 REGF1 default parameters, and make E5 the next eligible stage. The investigator accepted the post-event voltage oscillation at GFM buses as a documented diagnostic result; no REGF1 tuning is applied.
Justification: Investigator reviewed the E4.2 figures and the oscillation analysis and explicitly accepted the result. The oscillation is damped (about 30x decay within 2 s), the EIG physical subspace shows no new poorly damped mode (electromechanical modes 0.7--1.5 Hz with damping ratio 0.13--0.17, same as C1a), and voltages remain within 0.986--1.085 pu.
Evidence reviewed: DEC-015, E4.2 summary, raw data, figures, and modal comparison C1a vs C2.
Blockers or limitations: The roughly 18x larger post-event voltage ripple at GFM buses versus C1a (std 0.0037 vs 0.0002 pu) is unexplained; the REGF1 inner-loop/low-impedance hypothesis is untested. The plan's C2 capacity (P^2+Q^2<=Smax^2) and dispatch audits are still pending and must precede or accompany E5. No nonlinear stability, safety, or strict Hurwitz claim.
Responsible: Investigator
Status: VERIFIED
Next action: Prepare E5 (separate P-f and Q-V primary-control tests on C2, no secondary); stop for human review before E6.

## DEC-017
Date: 2026-10-25
Gate: E5--C2 event-amplitude screening
Decision: The plan S1 amplitudes (+100 MW at bus 4, +50 MVAr at bus 21, constant-power loads) are not admissible on frozen C2; E5 uses the predeclared alternative of 1 % of total P / Q load (+58.564 MW at bus 4, +17.345 MVAr at bus 21), the amplitudes already used in E3--E4.2. The P-balance check tolerance (10 % of the step) was fixed before running the alternative.
Justification: With the S1 amplitudes, TDS did not converge in either run at t = 5.13 s (bus-32 voltage fell to 0.19 pu); the steps are 22 % of the bus-4 load and 43 % of the bus-21 reactive load. The failed run is preserved as `IEEE39_E5_S1screen_C2_100MW_50MVAr_FAIL_*` and as matrix stage `E5_S1_screening`; its figures were discarded as non-physical. The screening concerns the plant, not a controller, so it does not favor any baseline.
Evidence reviewed: Paper_manuscript/artifacts/IEEE39_E5_S1screen_C2_100MW_50MVAr_FAIL_summary.json.
Blockers or limitations: No larger admissible amplitude was searched; S1 as written in plan_maestro.md Section 6 remains unreached. Later stages that need larger disturbances must define an admissible event (bus, load model, amplitude) before comparing controllers.
Responsible: Integrator
Status: VERIFIED
Next action: See DEC-018.

## DEC-018
Date: 2026-10-25
Gate: E5--C2 automatic gate
Decision: Assign `PASS_AUTO_WAIT_HUMAN` to E5--C2 (native primary control only) and stop before E6.
Justification: Both runs converged; step-size nadir difference <= 1.2e-5 Hz; P+ lowers frequency with every SG and GFM increasing P (total generation change 0.599 pu vs 0.586 pu step); Q+ lowers the local voltage and every GFM raises Q; no GFM P/Q limit or governor VMAX was reached. SG primary droop matches nominal (effective/nominal about 1 for SG30, 33, 35, 38, 39; SG31 shows 1.05). Q-V: GFM delta-Q equals delta-V_terminal / Qdrp (0.045) within about 5 %, i.e. Qdrp acts on system-base pu. P-f finding: all four GFM deliver the same delta-P (0.0072 pu) regardless of Sn, giving an effective droop of 0.0578 pu (system base) versus 0.0031--0.0039 pu if wdrp = 0.033 were scaled to Sn; GFM share of the 58.564 MW step is 4.8 %. Steady-state delta-f = -0.0248 Hz, nadir 59.969 Hz (mean bus frequency), settling 6.1 s, SG-COI max |RoCoF| 0.019 Hz/s.
Evidence reviewed: Paper_manuscript/src/run_e5_ieee39.py, Paper_manuscript/artifacts/IEEE39_E5_C2_summary.json, IEEE39_E5_C2_timeseries.npz, Paper_manuscript/figures_main/IEEE39_E5_C2_frequency.png, _voltage.png, _primary_response.png.
Blockers or limitations: Human figure approval pending. The GFM P-f contribution (4.8 % of the step, not proportional to Sn) is a property of the ANDES 2.0.0 REGF1 defaults, unexplained beyond the above scaling; it is not tuned. Measured delta-P is about 0.57 of wdrp-based expectation from mean bus frequency (cause not isolated). The first-sample frequency spike at the event instant is a numerical step artifact. REGF1 has no energy/SoC model. Diagnostic only; no stability or safety claim.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: Investigator reviews E5 figures. E6 remains unauthorized.
