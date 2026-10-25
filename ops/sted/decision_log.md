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

## DEC-019
Date: 2026-10-25
Gate: E4.2--C2 (post-approval diagnostic)
Decision: Accept the frozen C2 with ANDES 2.0.0 default REGF1 parameters, without recalibration, and record the cause of the voltage oscillation as a lightly damped linear small-signal mode of the REGF1 voltage/droop loops.
Justification: The mode (about 2.28 Hz; EIG -1.83 +/- j14.35, zeta 0.13; TDS 2.27 Hz, zeta 0.107) is present in the constant-power EIG of E4.2 and absent in E4.1 (C1a), so it is not a phasor-formulation artifact and it needs the coupling of four GFM. Diagnostic parameter variations applied only in memory (frozen case file untouched): EIG-predicted shifts match TDS for Tpm x0.5 (1.98 Hz) and wdrp x0.5 (1.71 Hz); KPv x2 and Qdrp x2 remove the lightly damped mode (ripple 0.0075 -> 0.0004-0.0006); all four GFM contribute (GFM32 > GFM36 > GFM34 > GFM37). Qdrp x0.75, KPv x0.5, KIv x0.5 and wdrp x2 did not complete (instability or non-convergence not distinguished), so defaults lie near a boundary on the low-gain side. Final frequency deviation unchanged (-0.0246 Hz). Retuning would require repeating E3--E4.2 and would change the ANDES-defaults policy (DEC-016); it is not adopted. Amplitude check (step scaled by 1, 0.1, 0.01 of the 1 % load step): 2.266, 2.284, 2.284 Hz with sigma -1.53, -1.79, -1.82, i.e. the frequency is amplitude-independent and the damping approaches the EIG value at small amplitude (scratchpad run, not archived).
Correction: an earlier statement in this session that the C2 EIG lacked the 2.28 Hz mode was wrong; the ad hoc scripts used the ANDES default load model instead of the constant-power configuration (p2p=q2q=1) of the repository runners. Any ad hoc near-zero-mode count, participation or condition-number figures obtained with those scripts are void; the repository summaries (constant-power) are the only valid EIG record.
Evidence reviewed: Paper_manuscript/src/diagnostics/e4_2_c2_regf1_diagnostic.py, Paper_manuscript/artifacts/IEEE39_E4_2_C2_regf1_diagnostic_log.txt, IEEE39_E4_2_C2_summary.json, IEEE39_E4_1_C1a_summary.json.
Blockers or limitations: Diagnostic only. Capacity (P^2+Q^2 <= Smax^2), current limits (REGF1 has none) and SG capability curves are not verified; strict Hurwitz stability and nonlinear stability are not established; "Hallazgo 4" wording must not claim more than damped-simulation consistency. Q sharing and limits in the modified variants were not checked.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: Investigator reviews E5 figures (DEC-018). E6 remains unauthorized.

## DEC-020
Date: 2026-10-25
Gate: E5--C2 human review
Decision: Investigator approved the E5--C2 figures (frequency, voltage, primary response); E5 status APROBADA. E6 becomes the next eligible stage.
Justification: Explicit investigator approval given after being informed of the 4.8 % GFM P-f share, the 1 % step amplitudes (S1 amplitudes not admissible on C2, DEC-017) and the DEC-019 caveats.
Evidence reviewed: IEEE39_E5_C2_frequency.png, _voltage.png, _primary_response.png; DEC-018, DEC-019.
Blockers or limitations: Approval does not certify stability, capacity or current limits. The weak GFM P-f share remains unexplained and is not tuned.
Responsible: Investigator
Status: VERIFIED
Next action: Define E6 scope (conventional PI/consensus secondary, identical primary) before implementing.

## DEC-021
Date: 2026-10-25
Gate: E6--C2 automatic gate
Decision: Assign `PASS_AUTO_WAIT_HUMAN` to E6--C2 (primary identical to E5 plus conventional consensus secondary on P) and stop before E7. Structure chosen by the investigator: consensus on a communication graph already in E6; actuation by an external loop. Sharing weights chosen by the Integrator: D_P = diag(1/Sn_i), consensus on the secondary increment.
Justification: (1) Actuators. REGF1.Pref is used only in `v_str` (initialization), so an `Alter` on it has no effect (verified: Pe unchanged). The effective GFM input is REGF1.Paux0, which acts as an integral-type input to PIplim; used as Paux0 = KC (y0 + dPset - PIplim_y) with KC = 0.05 and smooth targets, GFM Pe follows the command 1:1 (a step command or KC >= 1 diverges; a constant Paux0 ramps P until Pmax and the TDS fails). SG: TGOV1N.paux0 in system-base pu, delivered Pe follows it about 1:1; GENROU.Pe is also system-base pu. (2) Graph (design_e6_graph.py): 4 nearest units by network hop count, symmetrized, unit weights, 24 edges, lambda_2 = 1.54, connected, tolerant to any single link or unit loss; k = 2 and 3 were rejected as not tolerant (bridges 31-32, 31-39, 32-33). Bus 30 has degree 9 (hub). (3) Law dPset_i/dt = k_I[(1 - omega_i) - k_P sum_j a_ij (dPset_i/Sn_i - dPset_j/Sn_j)], k_I = 20, k_P = 0.5, local BusFreq, secondary on from t = 5 s; gains fixed a priori, not tuned. (4) Result (+58.564 MW at bus 4, 80 s): final frequency error -5.5e-7 Hz, nadir 59.9730 Hz (E5 59.9692), 2 mHz settling 16.9 s, delivered total 0.599 pu vs event 0.586, per-rating sharing spread 8.4 % (all units increase P), command tracking within tolerance, Vmin 0.9871 pu (E5 0.9861), no limit reached, step-halving differences <= 3e-6 Hz and 2.1e-5 pu. k_I diagnostics: 10 -> settling 35.7 s, 40 -> 10.3 s, both restore f.
Disclosure: two earlier runs of this stage were discarded as implementation errors, not evidence: (a) the hook stored `dae.t` by reference, so the integrator never updated (FAIL, frequency equal to E5); (b) SG commands were scaled by 100/Sn although paux0 and GENROU.Pe are system-base, so SG delivered about one tenth of the command (FAIL: sharing and balance). Neither changed the case, graph or gains.
Evidence reviewed: Paper_manuscript/src/run_e6_ieee39.py, design_e6_graph.py, artifacts/IEEE39_E6_C2_summary.json, IEEE39_E6_C2_timeseries.npz, IEEE39_E6_C2_communication_graph.json, figures_main/IEEE39_E6_C2_frequency.png, _voltage.png, _secondary.png.
Blockers or limitations: Human figure approval pending. Conventional baseline (g_P = 1, no leakage, no capability factors); the frequency spike at the event instant is a numerical step artifact; ideal measurement and zero communication delay; the external hook is a modeling device, not an ANDES controller; no Q/V secondary; no stability or capacity certification. The graph is frozen for E6 only: its use in E7 needs the plan's connectivity/observability review, and the hub at bus 30 should be reported.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: Investigator reviews E6 figures. E7 remains unauthorized.

## DEC-022
Date: 2026-10-25
Gate: E6--C2 human review
Decision: Investigator approved the E6--C2 figures (frequency, voltage, secondary); E6 status APROBADA. E7 becomes the next eligible stage; its scope is not yet defined.
Justification: Explicit investigator approval after being informed of DEC-021 (actuator deviation, graph hub, discarded implementation-error runs, baseline limitations).
Evidence reviewed: IEEE39_E6_C2_frequency.png, _voltage.png, _secondary.png; DEC-021.
Blockers or limitations: Approval does not certify stability, capacity or the graph for E7.
Responsible: Investigator
Status: VERIFIED
Next action: Define E7 scope (coordinated P/Q secondary) before implementing.
