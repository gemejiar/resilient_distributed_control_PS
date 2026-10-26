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

## DEC-023
Date: 2026-10-25
Gate: C2 capacity and dispatch audit (pre-E7)
Decision: Record the C2 audit as PARTIALLY_VERIFIED. C2 stays frozen (no change to the case or to E4.2--E6 results); the audit adds a capability definition and three findings that constrain E7.
Justification: Capability is defined from the case's own plant data (static pmax/qmin/qmax) intersected with S <= Sn/100 (script Paper_manuscript/src/audit_c2_capacity.py, artifact IEEE39_C2_capacity_audit.json). (1) Static dispatch: no violation of P, Q or S for any of the 10 units (S/Sn <= 0.89); tight P headroom at SG31 (0.040 pu), SG35 (0.100), GFM36 (0.150), GFM32 (0.250), SG33 (0.300). (2) Voltage target: holding all ten unit buses at 1.0 pu is steady-state feasible (PFlow, with and without +1 % P/Q), all units inside Q limits, all-bus voltage 0.979--1.045 pu; SG31 would sit at 89 % of its Q range (0.59 pu up-headroom), the binding unit; base unit-bus voltages are 1.013--1.060 pu. (3) Dynamic envelope: REGF1's internal limits (Pmax = Qmax = Sn/100) are 1.1--2.0x (P) and 1.8--2.2x (Q) looser than the case data, so "no limit reached" in E3--E6 did not imply capability compliance. SG31 exceeds the case pmax by 0.074 pu (7.4 MW) in E5 P+ under primary control alone and in E6 (secondary sharing by Sn does not use headroom); SG35 by 0.008 pu in E5 P+. Maximum S/Sn is 0.89, so the apparent-power rating is not binding.
Evidence reviewed: Paper_manuscript/artifacts/IEEE39_C2_capacity_audit.json; IEEE39_E5_C2 and IEEE39_E6_C2 time series.
Blockers or limitations: Case pmax/qmin/qmax are IEEE-39 plant data used as capability proxies, not manufacturer curves; SG rotor/stator/underexcitation limits and REGF1 current limits are not modeled; PFlow puts the active imbalance on the slack; only 1 % events were audited. E3--E6 conclusions on convergence and response remain valid; statements about "no saturation" must read as model limits only.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: Investigator reviews the E7 strategy in DEC-024.

## DEC-024
Date: 2026-10-25
Gate: E7 scope (proposal, not yet approved)
Decision: PROPOSED E7 design: capability-aware coordinated P/Q consensus secondary on the E6 graph, voltage target 1.0 pu at the ten unit buses and frequency 60 Hz (investigator's targets), with headroom-based sharing and P-over-Q priority. Implementation is not authorized until the investigator approves this scope.
Justification: (a) Capability set per unit: P in [0, pmax_case], Q in [qmin_case, qmax_case], S <= Sn (DEC-023). (b) Priority: active power has priority for frequency restoration; Q may use only the apparent power left, Qavail = min(qmax, sqrt(S_n^2 - P^2)) (and symmetric for absorption). Steady-state secondary only; Q-priority during voltage dips (REGF1 Vdip 0.8) and ride-through are out of scope. (c) P sharing: equalize the used fraction of upward headroom, dPset_i / h_i with h_i = pmax_i - P_i0, so no unit exceeds pmax if the total need is below total headroom; this replaces E6's Sn-proportional weights and addresses the SG31 exceedance. (d) Q sharing: consensus on utilization (Q_i - qmin_i)/(qmax_i - qmin_i) with weights from the same range, plus a voltage term k_V (1.0 - V_i) on each unit bus, following the structure of Eq. (rdc)--(laplacians) with g_P, g_Q set by the headroom and zeroed at the capability boundary; the sum of both terms yields a bounded steady voltage residual that must be reported, not hidden. (e) Actuators to prove first: GFM P by REGF1.Paux0 (E6), GFM Q by REGF1.Qaux0 (or vref), SG Q by exciter vref0; Qref/Pref are initialization-only. (f) Acceptance (to be frozen before running): f within 1 mHz; max |V_i - 1.0| <= 0.02 pu and mean |V_i - 1.0| below E6 at the end; no P, Q or S capability violation in the DEC-023 sense with 5 % margin; P sharing spread of dPset/h within 10 %; no unit above 90 % of its Q range; command tracking within 10 %; step-halving convergence. (g) Graph: reuse E6 graph; review connectivity of the effective sharing graph when several g_i approach zero, and report the bus-30 hub.
Norms: IEEE Std 2800-2022 (reactive capability and voltage control of IBR plants) and IEEE Std 1547-2018 (priority and reactive-power modes) are design references only; their requirements must be read from the standards before any citation or compliance claim; no reference is added to the manuscript here.
Evidence reviewed: DEC-023, DEC-021, main.tex Eqs. (rdc)--(laplacians).
Blockers or limitations: Unit-bus voltage and Q-sharing objectives conflict in general (both cannot be exact), so a residual is expected; steady-state PFlow shows 1.0 pu is feasible but not that the dynamic loop will reach it; Q-aux actuators are untested.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: Investigator approves or amends the E7 scope; then E7.0 actuator tests for Qaux0 / exciter vref0.

## DEC-025
Date: 2026-10-25
Gate: E7.0 actuator test and E7 scope approval
Decision: Investigator approved the DEC-024 scope and accepts a bounded unit-bus voltage residual with tolerance 0.02 pu. Refinement by the Integrator: capability acceptance is gated on the final steady state; transient P excess caused by the unchanged primary control (SG31: 0.074 pu in E5) is reported and E7 must not exceed the E5 value, because the secondary cannot remove a primary-only transient.
Justification: Q actuators tested on C2 with smooth ramps (script Paper_manuscript/src/diagnostics/e7_0_q_actuator_test.py), all converged and acted symmetrically with P and f unchanged: REGF1.Qaux0 tracking (KC 0.05) of the PIqlim reference moved GFM32 Q by +0.088 / -0.088 pu for a +/-0.2 reference ramp (Q reference acts through the Q-V droop); REGF1.vref (+0.01 pu) moved GFM32 Q by +0.113 pu and V by +0.0047 pu; IEEEX1.vref0 at SG31 (+/-0.01 pu) moved Q by +/-0.17 pu and V by +/-0.006 pu. E7 therefore realizes the Q/V secondary as a voltage-setpoint offset per unit (REGF1.vref for GFM, IEEEX1.vref0 for SG), uniform across the ten units; this is a deviation from the manuscript's Q_set input and must be reported as such.
Evidence reviewed: qact test output (scratchpad) and the diagnostics script above.
Blockers or limitations: Actuator test on one GFM and one SG only; sensitivities dQ/dvref differ by unit and network; no E7 run yet.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: Implement and run E7 with a-priori gains; E7 figures need human review.

## DEC-026
Date: 2026-10-25
Gate: E7--C2 automatic gate
Decision: E7 is BLOCKED. Its voltage target (1.0 pu at the ten unit buses) is statically feasible but dynamically unstable on the frozen C2 with ANDES default REGF1 parameters. No E7 figures are offered for review and the stage is not approved. C2 and the ANDES-defaults policy (DEC-016) are unchanged.
Justification: (1) Two a-priori runs failed (summaries kept: IEEE39_E7_C2_attempt1_kV0.5_FAIL_summary.json, IEEE39_E7_C2_attempt2_kV0.1_FAIL_summary.json). In S0 (no disturbance, secondary targets only) and in P+/Q+, the TDS diverged between 14 s and 18 s once the unit-bus voltage setpoints had moved about 60 % toward 1.0 pu, with growing oscillation; the 5x slower gains of attempt 2 delayed but did not avoid it, so the cause is not gain speed. (2) Linearization at the shifted operating point (script Paper_manuscript/src/diagnostics/e7_voltage_target_stability.py, constant-power loads): the least-damped oscillatory mode of C2 (about 2.3 Hz, REGF1 voltage/droop loops, DEC-019) has zeta 0.123 at the case setpoints, 0.041 at 25 % of the way to 1.0 pu, becomes unstable at about 40 % (zeta -0.067 at 50 %) and reaches +5.05 +/- j14.19 at 1.0 pu. (3) The 0.02 pu voltage tolerance needs at least about 67 % of the way for the highest-voltage buses (35 and 36 at 1.060 pu), so no stable partial target satisfies the investigator's acceptance. (4) With the same linearization at 1.0 pu, raising REGF1 KPv by 1.25 (or Qdrp by 1.5) restores zeta >= 0.12 (KPv x2: 0.14). This is a diagnostic only; no case was modified. (5) A second finding: simultaneous +1 % P and +1 % Q steps do not converge on C2 even without any secondary (t about 5.17 s), so P and Q channels are tested separately as in E5.
Evidence reviewed: the two FAIL summaries; the EIG scans above; DEC-019, DEC-023, DEC-025.
Blockers or limitations: The EIG scan changes only the static-generator voltage setpoints; the dynamic runs support it (divergence near the predicted threshold). Stability at intermediate offsets was not verified by TDS. The instability concerns this model with default REGF1 parameters, not the control law.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: Investigator decision required: (A) accept a documented REGF1 retune (for example KPv x1.25 or x1.5) as a new case C2-t, repeating the base C2 checks and E5/E6 on it before E7; (B) change the voltage target to a stable band (stated tolerance would be relaxed to about 0.04 pu); (C) keep C2 and run E7 with voltage regulation limited to what is stable, accepting no 1.0 pu claim. E7 stays unauthorized.

## DEC-027
Date: 2026-10-25
Gate: E7 unblocking (investigator's decision on DEC-026)
Decision: The investigator approved pursuing the DEC-026 options A, B and C ("desde A hasta C los recomendados"), read here as running all three. Option A is executed first: a new plant case C2t = C2 with REGF1 KPv x1.5 (3 -> 4.5; KIv, Qdrp, Tpm, wdrp unchanged), stored as a separate file ieee39_C2t_6SG_4GFM_KPv1p5.xlsx; the frozen C2 and its E4.2--E6 evidence are not modified. C2t is a documented departure from the ANDES-defaults policy of DEC-016, limited to this one parameter.
Justification: DEC-026 showed that KPv x1.5 keeps the 2.3 Hz mode at zeta >= 0.14 when the setpoints move to 1.0 pu, and KPv x1.25 does not improve on the case-setpoint damping (0.122 at 1.0 pu). x1.5 was chosen before any E7 run on C2t and is not tuned further. Every stage compared against E7 (E5, E6 and the capacity audit) is re-run on C2t so that all controllers share the same plant (runners select the plant with the C2_VARIANT environment variable; default C2 reproduces the earlier runs).
Evidence reviewed: DEC-026; Paper_manuscript/src/variant.py; validate_c2t.py.
Blockers or limitations: The interpretation of A--C as all three options is the Integrator's; options B and C are run on C2 after A. C2t changes the physical plant story: results on C2t cannot be mixed with C2 results in the same comparison table.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: Validate C2t (PFlow, flat TDS, EIG), then E5t, E6t, capacity audit and E7t.

## DEC-028
Date: 2026-10-25
Gate: Option A (plant C2t) -- validation, E5t, E6t, capacity audit and E7t automatic gates
Decision: Assign `PASS_AUTO_WAIT_HUMAN` to E5t, E6t and E7t on the retuned plant C2t (REGF1 KPv x1.5, DEC-027). C2 and its E4.2--E6 evidence are unchanged and remain the default-parameter record. Results on C2 and C2t are kept in separate stages (E5/E6 vs E5t/E6t/E7t) and must not share a comparison table.
Justification: (1) Base validation (validate_c2t.py, artifact IEEE39_C2t_base_validation.json): PFlow identical to C2 (max |dV| = 0, |dA| = 0), flat 20 s TDS without drift, no unstable physical modes; the least-damped oscillatory mode has zeta 0.141 (C2: 0.123) and stays at zeta >= 0.140 for setpoints moved 0, 25, 50, 75 and 100 % toward 1.0 pu, whereas C2 is unstable from about 40 %. (2) E5t: P+ nadir 59.9694 Hz, steady-state delta f -0.0248 Hz, minimum voltage 0.9971 pu (C2: 0.9861), the GFM P-f share is unchanged at 4.8 % (the P-f weakness of DEC-018 is not tuning-related). (3) E6t: frequency restored to -5.2e-7 Hz, nadir 59.9732 Hz, same sharing spread as E6. (4) Audit on C2t: no static violation; the same SG31 transient P excess of 0.070 pu over the case pmax appears with primary control alone (E5t) and in E6t. (5) E7t (gains K_IP 60, K_P 0.1, K_V 0.1, K_Q 0.001, KC 0.05, fixed a priori in DEC-026 attempt 2; scenarios S0, P+ and Q+ separately, 120 s): all runs converge; frequency error 0.0 Hz in all; unit-bus voltage within 0.0139 pu of 1.0 (mean 0.005 pu vs 0.031 pu in E6 on C2); Q utilization 0.28--0.81 (limit 0.90); final P margin to pmax >= 0.049 pu; the P+ increments divide equally by headroom (dPset/h = 0.0373 for all ten units, differential P+ minus S0), delivered differential total 0.595 pu vs event 0.586; step-halving differences <= 7e-9 Hz and 1.7e-7 pu.
Disclosure: the first E7t run (summary IEEE39_E7_C2t_attempt3_undifferentiated_P_checks_FAIL_summary.json) failed only two P checks that I had defined on absolute delivered Pe; for low-headroom SG31 and SG35 the terminal Pe also moves with the voltage setpoints (S0 shows -0.01 to -0.02 pu with no event), so those two checks were redefined as differential (P+ minus S0) and commanded sharing, then the run was repeated unchanged otherwise. The redefinition followed the failing result, so it is a post-hoc refinement, not a pre-registered criterion; the original absolute values remain in both summaries. Figure titles of the C2t stages were generated by runners that still printed "C2"; they were regenerated from the saved series (replot_c2t.py) with the correct variant label; no data changed.
Evidence reviewed: IEEE39_C2t_base_validation.json, IEEE39_E5_C2t_summary.json, IEEE39_E6_C2t_summary.json, IEEE39_C2t_capacity_audit.json, IEEE39_E7_C2t_summary.json and the nine C2t figures.
Blockers or limitations: Human review of the C2t figures is pending. C2t is a retuned plant (one parameter), not the ANDES-default plant; transient SG31 excess over the case pmax comes from the unchanged primary control and is reported, not removed. Capability proxies, ideal measurements, zero delay, hub at bus 30 as in DEC-021/023. The voltage target holds only with the setpoints this controller moves (offsets up to -0.065 pu), not a certificate of stability for other disturbances.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: Run E7L on C2 (options B/C), then request investigator review of all figures.

## DEC-029
Date: 2026-10-25
Gate: Options B/C (E7L on the unmodified C2) automatic gate
Decision: Assign `PASS_AUTO_WAIT_HUMAN` to E7L, the coordinated P/Q secondary on the frozen C2 (ANDES defaults) with voltage-setpoint offsets limited, per unit, to 25 % of the way to 1.0 pu (the stable region, DEC-026), and a declared voltage tolerance of 0.05 pu. Options B (stable band) and C (limited regulation) are merged into this one run because they coincide: the band is the residual left by the limit. Option A is DEC-028.
Justification: Same controller and gains as E7t; only the clamp changes (ALPHA_MAX = 0.25, set before the run; the 0.05 pu tolerance is the largest residual the 25 % limit leaves for buses 35/36, 0.045 pu, rounded up). All runs converge (S0, P+, Q+ and the step-halved P+); frequency error 0.0 Hz; maximum unit-bus voltage error 0.0459 pu (S0), mean 0.023 pu (E6: 0.031 pu); P+ increments equal by headroom (dPset/h = 0.0373 for ten units); Q utilization within limits; the SG31 transient excess over pmax is 0.074 pu, as in E5 (primary control only).
Evidence reviewed: IEEE39_E7L_C2_summary.json and the E7L figures.
Blockers or limitations: The voltage improvement over E6 is modest (mean error 0.031 -> 0.023 pu) and the tolerance 0.05 pu is wide compared with the investigator's 0.02 pu; the 1.0 pu claim holds only on C2t (DEC-028). With the offsets at 25 % the least-damped 2.3 Hz mode has zeta 0.041 (C2 case setpoints: 0.123), so the margin is thin and was verified by the EIG scan and these three runs only, not under other disturbances. Human figure review is pending.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: Investigator reviews the C2t (E5t, E6t, E7t) and C2 (E7L) figures and chooses the plant for E8 onward; E8 stays unauthorized.

## DEC-030
Date: 2026-10-25
Gate: E5t, E6t, E7t, E7L human review; plant selection
Decision: The investigator approved the figures of E5t, E6t and E7t (plant C2t) as numerical evidence of the observed behavior, with the documented limitations; accepted E7L (C2, limited regulation) exclusively as a reference that does not meet the original +/-0.02 pu target; and selected C2t as the main experimental plant for E8 and later stages (RDC, CLF-HOCBF). The approval authorizes progressive implementation and validation; it is not a certification of safety or stability.
Mandatory conditions (verbatim in substance): (1) keep C2 and all its results unmodified; keep C2t as an explicit variant with REGF1.KPv 3 -> 4.5 and no other primary parameter changed; (2) use C2t for all main comparisons (primary, PI/consensus, P/Q secondary, original RDC, modified RDC, CLF-HOCBF); never compare controllers on different plants as if they shared one dynamic; (3) keep in the manuscript the justification of the KPv calibration from the modal analysis and the recorded experiments, and never present C2t as a default-parameter plant; (4) register and address the transient pmax violation of SG31 before claiming dynamic safety, and do not accept that a pre-existing violation is justified merely because the primary control also shows it; (5) align the Q/V actuation variables implemented in ANDES with the manuscript equations, distinguishing voltage references from reactive-power references; (6) implement E8 with the original RDC clearly separated from any modification, keep the same scenarios and plant parameters, and stop at the corresponding human review; (7) do not state regional stability, physical P/Q invariance or general limit compliance until the mathematical proofs and checks exist. Keep the repository structure, reuse the experiment matrix and STED-RW records, and keep the evidence of failed and successful simulations.
Justification: Investigator decision after reviewing the figures and results in DEC-028 and DEC-029.
Evidence reviewed: the twelve C2t/E7L figures; DEC-026 to DEC-029.
Blockers or limitations: Conditions 4, 5 and 7 are open obligations tracked in DEC-031 and DEC-032; E7 used a voltage-setpoint offset as the Q/V actuator (DEC-025), which condition 5 requires to be distinguished from the manuscript's Q_set.
Responsible: Investigator
Status: VERIFIED
Next action: Record the SG31 pmax issue (DEC-031), align the Q/V actuation (DEC-032), implement E8 (original RDC on C2t).

## DEC-031
Date: 2026-10-25
Gate: Open issue -- transient pmax violation of SG31 (condition 4 of DEC-030)
Decision: Register the SG31 transient active-power excess over the case pmax as an OPEN safety issue. No claim of dynamic safety, physical P invariance or general limit compliance is made for any stage until it is closed, and it is not accepted as justified by also appearing under primary control.
Justification: SG31 (bus 31) dispatches 6.46 pu against a case pmax of 6.50 pu (headroom 0.040 pu). Under the +58.564 MW step its terminal power peaks at 6.574 pu (+0.074 pu, 7.4 MW over pmax) in E5 and E6, and +0.070 pu in E5t, E6t and E7t (audit IEEE39_C2t_capacity_audit.json; E7L: 0.074 pu). The ANDES governor limit of SG31 is TGOV1N.VMAX 8.78 pu (1.05 Sn), 2.3 pu above the case pmax, so the plant model itself does not enforce the case limit and the primary droop (R 0.006) adds up to about 0.11 pu to SG31 against 0.04 pu of headroom. SG35 shows a smaller case in E5 (0.008 pu). The secondary layer cannot remove this primary-only transient; an RDC limits Pset, not the instantaneous droop response.
Closure criteria (all required before any safety claim): (a) quantify the excess for every controller on C2t (E5t..E8, E9...) with the same scenarios; (b) run a labeled sensitivity plant with the SG31 (and SG35) governor VMAX aligned to the case pmax, without altering the main C2t (condition 1), or re-dispatch SG31 with a documented margin, and report the effect on frequency nadir and recovery; (c) state which mechanism (setpoint limitation, primary-limit alignment, dispatch margin) removes the excess, with evidence; (d) the barrier layer of the modified RDC and CLF-HOCBF must treat the instantaneous P output, not only Pset.
Evidence reviewed: DEC-023, DEC-028, DEC-029; IEEE39_C2t_capacity_audit.json; TGOV1N data of C2t.
Blockers or limitations: The case pmax is IEEE-39 plant data used as a capability proxy; a manufacturer limit could differ. The open issue blocks safety wording in the manuscript.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: E8 reports the SG31 excess side by side with E5t, E6t and E7t; closure tracked in traceability row OPEN-SG31-PMAX.

## DEC-032
Date: 2026-10-25
Gate: Q/V actuation alignment (condition 5 of DEC-030)
Decision: Distinguish three different quantities in all implementations and reports: (i) the voltage reference V_ref of the manuscript's voltage-error term (a constant, 1.0 pu in E7/E8), (ii) the reactive-power reference Q_set, a controller state with v_Q = dQ_set/dt, and (iii) the ANDES actuation variables (REGF1.vref or IEEEX1.vref0, REGF1.Qaux0), which are inner-loop devices that realize Q_set and are not controller states. E7/E7t/E7L used (iii) as the controller state (a voltage-setpoint offset integrated from a voltage error and a utilization-sharing term); this is a documented deviation from Eq. (rdc) of main.tex and must be reported as such. From E8 on, Q_set is the controller state and the actuation is an inner tracking loop of the measured Q.
Justification: Manuscript: u = col(P_set, Q_set), v = dot u, v_Q^RDC = k_IQ k_V diag(g_Q)(V_ref - V) - k_IQ k_Q L_Q D_Q Q - k_l (Q_set - Q_set^n). Reference paper Eqs. (7)--(8), (13): at steady state Q_e = Q_set. ANDES realization chosen: GFM Qaux0 = KCq (Q_set - Q_e), an integral action on the PIqlim reference; SG: dvref0/dt = KZ (Q_set - Q_e) (integral of the Q error on the exciter voltage reference). P_set is realized as in E6/E7 (SG paux0 = P_set - P_set(0); GFM Paux0 tracking of the PIplim reference). Inner gains are fixed a priori from the E7.0 actuator tests (KC 0.05; KCq 0.02; KZ 0.02).
Evidence reviewed: main.tex Sec. 2.3; the reference paper Eqs. (26)--(35); DEC-025; E7.0 actuator test.
Blockers or limitations: ANDES IEEEX1 has no Q loop, so the SG Q tracking is an external loop added around the exciter, like the P secondary; with it, Q_e = Q_set only in quasi-steady state. E7 results are not re-run with this alignment; the E7 versus E8 comparison therefore mixes the controller law and the Q actuation structure and must say so.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: Implement E8 with Q_set as the state; consider an aligned E7a only if the investigator requests a like-for-like comparison.

## DEC-033
Date: 2026-10-25
Gate: E8 design (original RDC on C2t), declared before the run
Decision: E8 implements the original RDC of the reference paper, Eqs. (26)--(35) (equal to Eq. (rdc)--(laplacians) of main.tex without centering, barrier or CLF layers), on the plant C2t only, with the same scenarios (S0, P+ +58.564 MW at bus 4, Q+ +17.345 MVAr at bus 21, t = 5 s), graph, step sizes and primary parameters as E7t; modifications (centered v_nom, HOCBF, CLF) are reserved for later stages and are not mixed into E8. The runner refuses any plant other than C2t.
Declared choices and adaptations (fixed before any E8 run): (1) Capability set W_i: GFM exactly as Eqs. (30)--(31) with Smax = Sn/100, Pmax = case pmax, Pmin = 0 (so Q is limited only by the apparent-power disc, as in the paper, and the case qmin/qmax are not enforced for GFM); SG as Eqs. (28)--(29) with the excitation-limit and iron-core terms (24)--(25) replaced by the case qmin/qmax in a dimensionless box factor, because ANDES has no SG capability-curve data. (2) Sharing coefficients d_P,i = 1/Pn_i (the nominal dispatch is the sharing equilibrium, so the base dispatch is not redistributed) and d_Q,i = 1/(qmax_i - qmin_i). (3) g_P and g_Q are divided by one scalar each (their nominal maximum) and k_IP is set so that k_IP times the sum of normalized g_P equals 160, the integral speed of E7; k_P 0.1, k_IQ 1.2, k_V 1.0, k_Q 0.01 (voltage restoration prioritized, as in the paper's discussion of Eq. (39)), leakage k = 1e-3, V_ref = 1.0 pu, omega_S = 1 pu. (4) Initial states Pset(0) = Pn, Qset(0) = Qn measured at the nominal operating point; the nominal point lies in the interior of every W_i (checked at start). (5) Actuation per DEC-032: Pset realized by paux0 / Paux0 tracking; Qset realized by inner tracking of the measured Q (GFM Qaux0, KCQ 0.02; SG exciter vref0 integral, KZ 0.02). (6) Gates (checked automatically): convergence at both step sizes; |final frequency error| <= 1 mHz; setpoints remain inside W_i throughout; final P_i/Pn_i spread <= 0.02 in P+; Q tracks Qset within 0.02 pu; final P below case pmax; mean unit-bus voltage error below E6t; step-halving consistency. Information only (no gate): attainment of the 0.02 pu voltage target, the SG31 transient excess, GFM Q beyond the case limits, and a side-by-side table against E5t, E6t and E7t.
Justification: Investigator conditions 1, 2, 5 and 6 (DEC-030) and the equations read in the reference paper; no tuning against results.
Evidence reviewed: reference paper Sec. IV (Eqs. 26--35) and main.tex Sec. 2.3.
Blockers or limitations: The paper's SG capability curve terms are not reproduced; if the investigator requires them, the SG excitation and stability parameters (E_max, delta_max) are missing in ANDES and must be assumed in a separate decision.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: Run E8, then stop at the human review of its figures (condition 6).

## DEC-034
Date: 2026-10-26
Gate: E8 attempts and revisions of the Q realization
Decision: Record three failed E8 attempts and the revision of the Q_set actuation that followed. The RDC law (Eqs. 26--35), the capability set, d_P, d_Q, the graph, the scenarios and the plant C2t were not changed between attempts; only the realization of Q_set in ANDES (DEC-032) and the Q-loop speed were.
Justification: Attempt 1 (K_IQ 1.2; inner tracking KCQ and KZ 0.02): converged but showed a sustained 45 s oscillation of the ten unit-bus voltages (0.94--1.06 pu) and a final frequency error of -2.2 to -2.6 mHz (summary IEEE39_E8_C2t_attempt1_kIQ1p2_FAIL_summary.json). Attempt 2 (K_IQ 0.3, 150 s): worse, a ~100 s oscillation with the SG voltage-reference offsets saturating at the 0.10 pu clamp and unit voltages 1.07--1.14 pu at the end (attempt2_kIQ0p3_innerslow_FAIL_summary.json). Attempt 3 (inner loops 5x faster): divergence, unit voltages 0.88--0.95 pu, SG33 transient P excess 0.9 pu, a run that did not finish (attempt3_innerfast_FAIL_summary.json). Diagnosis: with an integral Q-tracking loop inside the integral Q_set loop of the RDC the cascade has two integrators; the slow inner loop gives a low-frequency oscillation and the fast one couples with the network voltage dynamics, so no inner speed was adequate. Attempt 4 replaces the inner integral by the proportional/reference-tracking forms validated in E7.0: SG vref0 = vref0(0) + kappa (Qset - Qn) with kappa 0.06 pu/pu (from dQ/dvref about 17 pu/pu), GFM Qaux0 = KCQ (y0q + Qset - Qn - PIqlim_y) with KCQ 0.05, K_IQ 0.3, 200 s. A short diagnostic S0 run (100 s, not archived) was stable with voltages converging monotonically toward 1.0 pu before the full run.
Consequences of attempt 4: Q_e = Q_set holds only approximately (kappa is a nominal sensitivity, not a loop), so the earlier gate "Q tracks Qset within 0.02 pu" was dropped and the tracking error is reported as information; the equilibrium is set by the outer voltage and sharing terms, not by the actuation map. Four tunings are a degree of freedom: the E8 result must not be read as an optimized RDC; the conventional comparison with E7t also differs in Q structure (DEC-032).
Evidence reviewed: the three FAIL summaries and their time series (inspected before deletion); the E7.0 actuator test.
Blockers or limitations: The attempts are partly informed by observed failures, so the final gains are not blind a-priori values; this is a disclosed iterative adjustment of the actuation realization, not of the RDC law. No stability claim.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: Evaluate attempt 4 against the DEC-033 gates (minus the dropped Q-tracking gate) and stop at human review.

## DEC-035
Date: 2026-10-26
Gate: E8--C2t automatic gate
Decision: Assign `PASS_AUTO_WAIT_HUMAN` to E8--C2t (original RDC, fourth attempt, DEC-034) and stop at the human review of its figures (condition 6 of DEC-030). No E9, modified-RDC or CLF-HOCBF work was started.
Justification: Plant C2t, same scenarios, graph and primary parameters as E7t; 200 s runs converge, including the step-halved P+ run (differences <= 1.8e-8 Hz, 1.3e-7 pu). Gates passed: frequency error within 1 mHz in S0, P+ and Q+ (-0.1, -0.3, -0.1 mHz); setpoints Pset, Qset remain inside W_i throughout (minimum margin positive); final P_i/Pn_i spread 0.0093 in P+ (equal scaling of the nominal dispatch); final P below the case pmax; mean unit-bus voltage error 0.0057 pu (E6t 0.0311, E7t 0.0051). Information: the 0.02 pu voltage target is met (max error 0.0147 pu); final Q does not exceed the case qmin/qmax for any unit; Q_e differs from Q_set by up to 1.03 pu because the Q realization is proportional (DEC-034); GFM Q-limit behavior follows Eq. (31) only. Side-by-side on C2t for P+ (summary comparison_on_C2t_P+): primary-only E5t error -24.8 mHz, nadir 59.9694 Hz, mean voltage error 0.0310 pu; E6t error -0.0005 mHz, nadir 59.9732 Hz, 0.0311 pu; E7t error +0.0006 mHz, nadir 59.9719 Hz, 0.0051 pu; E8 error -0.3 mHz, nadir 59.9715 Hz, 0.0057 pu.
SG31: the transient excess over the case pmax is 0.0699 pu in P+, identical to E5t, E6t and E7t. The original RDC limits the setpoint states but does not remove the primary-droop transient, so OPEN-SG31-PMAX (DEC-031) stays open and no dynamic-safety claim is made.
Evidence reviewed: IEEE39_E8_C2t_summary.json, the time series (local, >10 MB), IEEE39_E8_C2t_frequency.png, _voltage.png, _secondary.png; the three FAIL summaries.
Blockers or limitations: The Q_set states were still drifting at 200 s (for example GFM37 rising, SG30/35/38 and GFM36 falling slowly in the secondary figure) while voltages are within tolerance: the run is near, not at, a steady state, and the slow Q sharing mode was not characterized. The setpoint margin in W_i is positive but only checked at the TDS step (Euler); no proof of invariance or stability is claimed (condition 7). The capability set of the SG substitutes the paper's curve terms; four tunings were needed (DEC-034). Human figure review is pending.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: Investigator reviews the E8 figures; E9 (centered/modified RDC as a separate variant) stays unauthorized until then.

## DEC-036
Date: 2026-10-26
Gate: E8--C2t human review
Decision: The investigator approved the E8--C2t figures ("ok, apruebo continua") as numerical evidence of the original RDC on C2t. E8 matrix status APROBADA; E8-001 stays PARTIALLY_VERIFIED. Approval is not a certification of safety or stability (DEC-030, condition 7).
Justification: The investigator reported that the frequency disturbance was not visible in the figure. The disturbance is visible in the P+ panel (nadir 59.9715 Hz) but S0 and Q+ move by about 0.2 and 1 mHz, which the +-0.02 Hz axis hides. The frequency figure was regenerated from the saved series (no new simulation, no data changed) with a second row showing f-60 Hz in mHz over 3-45 s with independent axes. S0 shows a -0.2 mHz drift after t=5 s with no load event (activation transient of the RDC, within the 1 mHz gate).
Evidence reviewed: IEEE39_E8_C2t_frequency.png (regenerated), run_e8_ieee39.py plot_frequency.
Blockers or limitations: OPEN-SG31-PMAX still open. Next plan step is the separate centered variant v_nom (Eq. centered, B3) before E9; its reference equilibrium xi*(d) (Eq. eqselection) is not yet defined for the ANDES model and needs an investigator decision (centering about the RDC's own settled state would be nearly a null change).
Responsible: Investigator (approval); Integrator
Status: VERIFIED
Next action: Define xi*(d) for the centered variant (B3); do not start E9 until B3 is reviewed.

## DEC-037
Date: 2026-10-26
Gate: B3 (centered RDC) step 1, reference equilibrium xi*(d); documentary reconciliation
Decision: Prepare B3 by selecting xi*(d) for S0, P+ and Q+ on plant C2t, following the investigator's eight conditions; stop at human review of the equilibrium table. No dynamic B3 and no E9 were run. OPEN-SG31-PMAX stays open.
Selection problem (script select_equilibrium_b3.py, a static AC problem, not a controller simulation): minimize sum over the ten units of ((P_i-P_i^pre)/R_P,i)^2 + ((Q_i-Q_i^pre)/R_Q,i)^2 + ((V_i-1.0)/0.05)^2, with R_P = pmax-pmin and R_Q = qmax-qmin of the case plant data (pmin = 0), unit weights 1, subject to the AC power balance of the 39 buses with the scenario's constant-power loads, omega = 1, losses included; P and Q box limits and S <= Sn/100 each tightened by a 1 % interior margin of their range; 0.95 <= V_bus <= 1.05 at all buses. 1.0 pu is a soft reference, not an equality. Weights, scales and margins are frozen before any B3-versus-B2 comparison. The E8 end state is not used as reference (condition 1); the sharing is not proportional to Pn or to the Q range (condition 2). Pre-event reference xi_pre is the C2t power flow without disturbance; post-event xi*(d) uses the exact disturbance, which is privileged information, available only from the event onward (condition 7).
Parameter history disclosed: a first trial with a voltage scale of 0.02 pu made the unit voltages equal 1.0 pu within about 0.001 pu (an equality in practice) and used numerical gradients that hit the iteration limit; the scale was set to 0.05 pu (half-width of the bus-voltage band) and analytic Jacobians were added, before any dynamic comparison. SLSQP then converged in 30-255 iterations.
Results (validation, JSON/CSV in artifacts): equilibrium residual <= 1.3e-13; inequality margins >= 0 (one active: SG35 at pmax minus the margin); bus voltages 0.979-1.044 pu; unit voltages within 0.0012 pu of 1.0 pu. ANDES power flow with P*, V* matches the selection (voltage 1.9e-7 pu, angle 2.8e-7 rad; unit P 6.3e-6, Q 3.7e-6 pu); dynamic initialization residuals |f| 4e-16 and |g| 6e-10; a 20 s flat run converges with dynamic-state drift 1.2e-9. Pset* = P* and Qset* = Q* by the omega = 1 convention. Actuator consistency: GFM PIplim_y and PIqlim_y change exactly by dP* and dQ*; SG governor reference changes by dP* within 0.026 pu (SG31 and SG35 differ by about 0.015 and 0.025 pu; cause not diagnosed); the SG exciter reference required by initialization differs from the E8 proportional map kappa*(Qset-Qn) by up to 0.057 pu (for example SG38 requires -0.0525 pu versus -0.0028 pu), so the E8 Q realization cannot reproduce xi* and a dynamic B3 would need its own actuator mapping. P+ values: dP* in [-0.062, 0.213] pu, dQ* in [-0.42, 0.71] pu; SG31 P margin to the case pmax 0.087 pu (pre-event 0.040), SG31 S at 88 % of Sn and Q margin to qmax 0.62 pu; SG35 P margin 0.070 pu.
Centering magnitude (condition 5): the original RDC field at xi*, v_RDC(xi*,d), is dominated by the P consensus term because P*/Pn is not uniform: max |vP| 0.257 (P+), 0.196 (Q+), 0.214 (S0) pu/s, against an E8 peak |dPset/dt| after the event of 0.394 (P+), 0.043 (Q+) and 0.0009 (S0) pu/s; |vQ| <= 0.004 pu/s. Centering would therefore subtract a rate of the order of the original dynamics in P+ and far above it in S0 and Q+, i.e. B3 would materially differ from B2. Information only: xi* differs from the E8 end state by up to 0.16 pu in P, 0.30 pu in Q and 0.014 pu in V (P+).
Documentary reconciliation (condition 8): the summary JSON files of reviewed stages kept the run-time status_human (PENDING) while the experiment matrix recorded the approval; for the 13 affected summaries status_human now equals the matrix value, with status_human_at_run and status_human_source added, and no run data changed. The plan header state is E8_APROBADA. E8 raw series: IEEE39_E8_C2t_timeseries.npz is present locally (116 882 987 bytes, SHA-256 fe59f362ceb3f96a17e4dc90249031c5cb7d37a495da8786f886d5d5547f2422, 90 arrays, S0/P+/Q+ 200 s, all finite); it is excluded from git by the >10 MB policy. The E5_S1_screening matrix row keeps status_human PENDING for a FAIL run (left unchanged).
Evidence reviewed: select_equilibrium_b3.py output, IEEE39_B3_C2t_equilibrium_selection.json/.csv, IEEE39_E8_C2t_timeseries.npz (reference scales only), main.tex Eqs. (centered) and (eqselection).
Blockers or limitations: the weights are a modeling choice (range-normalized P and Q terms make P redispatch cheap relative to voltage regulation; in S0, P changes by up to 0.12 pu from the pre-event dispatch); the SG capability is the case-box proxy (DEC-024); SG governor mismatch and the SG exciter mapping are open; xi* is a local optimum of a nonconvex problem, not certified; no stability or safety claim.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: Investigator reviews the equilibrium table and the frozen weights; then dynamic B3 versus B2 on C2t with the same gains, scenarios and horizon. E9 stays unauthorized.

## DEC-038
Date: 2026-10-26
Gate: B3-A equilibrium verification (revision of DEC-037, investigator conditions 1-6)
Decision: Keep the v1 AC selection and its frozen weights as candidate B3-A (provisional approval; not approved as the definitive equilibrium). Verify it against the C2t DAE with the real E8 actuators, add the effective references, fix the S0 rule, quantify the centering, and stop. The v1 files (IEEE39_B3_C2t_equilibrium_selection.json/.csv, commit 4fb8ab5) are unchanged; the revision is IEEE39_B3A_C2t_equilibrium_v2.json/.csv, IEEE39_B3A_C2t_frozen_reference_convergence.json and IEEE39_B3A_C2t_verification_log.txt (script verify_b3a_equilibrium.py). Commit 4fb8ab5 was pushed, as authorized, to the separate review branch review/b3-equilibrium of the project remote; main is untouched.
1. Dynamic consistency. xi* initializes in ANDES with |f| <= 3e-16 and |g| <= 6e-10, and a 20 s flat run drifts by 1e-9. Pset* = P*, Qset* = Q* is no longer imposed; the references the E8 actuators need were derived. SG governor: the required reference change differs from dP* because the governor also supplies the armature losses (pref = tm = Pe + ra*I^2; ra 0.0032 for SG31 and 0.0057 for SG35, losses 0.16 and 0.26 pu): dpref - dP = 0.015 (SG31) and 0.025 (SG35) pu at P+. SG exciter: dvref in [-0.061, 0.006] pu (clamp margin >= 0.039 of Z_CLAMP 0.10), far from the E8 map kappa*dQ. GFM: E8 acts only on PIqlim_y and leaves vref at its pre-event value; since vref2 = (PIqlim_y - Qsen)*Qdrp + vref and vd = vref2 at steady state, the y needed is y_eff = Q* + (V* - vref_pre)/Qdrp (GFM36: -0.84 for Q* = 0.49). This also explains the Q_e - Q_set mismatch of up to 1.03 pu in E8 (a 0.046 pu voltage offset over Qdrp 0.045). The effective RDC setpoints Pset_eff, Qset_eff (E8 maps) are listed per unit in the v2 files; all lie inside W_i (g_P, g_Q > 0; min raw g_P 0.076, min raw g_Q 0.165). A first frozen-reference run that used the init-required y alone settled 0.59 pu away in Q and 0.033 pu in V (this is the evidence behind the y_eff correction; it is recorded only here because its output files were overwritten by the corrected run). Frozen-reference check with the corrected references (event load step and effective references together at t = 5 s, E8 actuators, no RDC, 150 s): P+ and Q+ settle at xi* with errors P 3.0e-5, Q 1.9e-5, V 9.4e-7 pu, f 1.6e-6 Hz and last-5 s drift < 1e-6 pu; the maximum Q error is 0.53 pu at 6 s and 0.001 pu at 90 s. A variant that also wrote the GFM vref (an extra channel not used in E8) failed numerically at t = 5.06 s (time step reduced to zero, simultaneous reference and load step); it is kept as a failed attempt in the log and JSON and not pursued. This check settles the DAE equilibrium and its reachability with the actuators; it is not the B2-B3 comparison.
2. S0. Reference rule: d = 0 uses the validated pre-event equilibrium xi_pre. This makes xi*(d) discontinuous at d = 0: the AC selection at d = 0 (kept in v1 as evidence) moves P by up to 0.12 pu and Q by up to 0.7 pu because the voltage and Q terms pull the unit voltages to 1.0 pu. The S0 scenario therefore checks that the centered controller leaves the nominal equilibrium invariant. Consequence: v_nom is zero at xi_pre, so B3 in S0 will not regulate voltage toward 1.0 pu, unlike B2 (E8), whose S0 run drifts toward 1.0 pu; this difference is by construction and must be read as such. xi_pre is not inside the 0.95-1.05 pu bus band of the AC selection (case voltages reach 1.073 pu).
3. Weights. B3-A weights kept (W_P = W_Q = W_V = 1, voltage scale 0.05 pu, margin 1 %). Influence at the solution (P+): P redispatch term 1.5e-3, Q term 3.8e-2, V term 2.4e-3, so the Q and voltage terms dominate and the P redispatch is weak, which is why P moves by up to 0.2 pu and SG31 and SG33 decrease while the load increases. The sensitivity test is prepared, not run: select_equilibrium_b3.py reads B3_W_P, B3_W_Q, B3_W_V, B3_DV and B3_TAG (defaults reproduce B3-A).
4. Centering. v_nom(xi) = v_RDC(xi) - v_RDC(xi*) is exactly 0 at xi* (0.0e+00 numerically) and nonzero away from it (max 0.115 and 0.083 pu/s halfway between xi_pre and xi*). v_RDC(xi*) with effective setpoints: max |vP| 0.257 (P+) and 0.182 (Q+) pu/s, i.e. 25.7 and 18.1 MW/s on SG30, and |vQ| <= 0.0037 pu/s (0.37 MVAr/s); with Pset = P*, Qset = Q* the values are 0.257/0.0039 and 0.196/0.0040. Reference update: v_nom at xi_pre against xi*(d) equals the offset jump v_RDC(xi*) - v_RDC(xi_pre), up to 0.257 pu/s (P+) and 0.182 pu/s (Q+) in P and 0.015 pu/s in Q, applied as a step at the instant the reference switches; for S0 it is 0. Units: pu/s on the 100 MVA base. Capacity margins to pmax at P* and at the effective setpoint: SG31 0.087 and 0.071 pu, SG35 0.070 and 0.045 pu (P+).
5. SG31. OPEN-SG31-PMAX stays open. The larger static margin (0.087 pu against 0.040 pu pre-event) does not prove transient power safety: in the frozen-reference check with feedforward references SG31 still exceeds the case pmax by 0.070 pu in P+ (0.0 in Q+).
6. Traceability. B3-001 kept and B3-002 added; DEC-037 and the v1 results are preserved; C2t and the original E8 results are not modified (E8 raw series read only).
Evidence reviewed: IEEE39_B3A_C2t_equilibrium_v2.json/.csv, IEEE39_B3A_C2t_frozen_reference_convergence.json, IEEE39_B3A_C2t_verification_log.txt, regf1.py equations (vref2, Qdrp), run_e8_ieee39.py actuation.
Blockers or limitations: xi*(d) is a candidate from a nonconvex local solve and uses exact disturbance knowledge (privileged information); it is discontinuous at d = 0; the effective Q references of the GFM (for example -0.84 pu for Q* 0.49 pu) are far from the physical Q because of the Qdrp/voltage relation, so W_i evaluated on setpoints does not represent the physical Q capability of the GFM in this actuation structure; the SG capability remains the case-box proxy; no stability, safety or invariance claim.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: Investigator review of the revised equilibria; then, if authorized, the weight sensitivity and the dynamic B2-B3 comparison on C2t. E9 stays unauthorized.

## DEC-039
Date: 2026-10-26
Gate: B3-S0 (centered RDC, scenario S0 only) automatic gate and the preconditions set with the approval of B3-A
Decision: Approval received for B3-A as a candidate operating equilibrium of C2t (weights and S0 rule unchanged), and for pushing commit 0d9da24 to the review branch only; it was pushed to review/b3-equilibrium (main untouched, nothing merged). B3-S0 was run and assigned PASS_AUTO_WAIT_HUMAN; the run stops at human review before P+ and Q+. No weight sensitivity, no P+/Q+, no E9.
Formalization (condition 1), three layers kept apart. Control reference (Pset, Qset): the RDC states in E8 actuator coordinates. Actuator signal: SG TGOV1N.paux0 = Pset - Pn; SG IEEEX1.vref0 = vref0(0) + z with z = clip(kappa (Qset - Qn), +-Z_CLAMP); GFM Paux0 and Qaux0 tracking forms that drive PIplim_y to y0 + Pset - Pn and PIqlim_y to y0q + Qset - Qn. Physical power at omega = 1: SG P = Pset minus the change of armature losses (pref = tm = Pe + ra I^2), SG Q from the network and the exciter; GFM P = Pset; GFM Q = PIqlim_y - (V - vref_pre)/Qdrp (vref2 = (y - Q) Qdrp + vref, vd = vref2). Hence Pset* and Qset* of B3-A differ from the physical P*, Q* (DEC-038): the manuscript variables Pset, Qset are control references, not physical powers.
Equivalent realization (condition 3): B3 uses the E8 actuator maps unchanged; centering only subtracts a constant vector from the integrator input, so no mapping change and no separate B2-aligned reference were needed. To prove that B2 and B3 share one realization, the runner reproduces B2 with the same controller code (offset 0) and compares it with the stored E8 S0 series: 51 201 samples, differences of 0.0 in frequency, unit voltage, P, Q, Pset and Qset. The original E8 results are untouched.
Limits and margins (condition 2): static check of the B3-A equilibria in IEEE39_B3A_C2t_margin_check.json (script check_b3a_margins.py). Margins as a fraction of the case P and Q ranges; the B3-A selection imposed 1 % only on the physical P*, Q*. SG35: physical P* margin to pmax 0.0697 pu (1.0 % of range, the imposed margin) but the effective reference Pset_eff is 0.045 pu (0.65 % of range) from pmax in P+ and 0.044 pu in Q+, below the 1 % margin; in the pre-event equilibrium SG35 has 0.100 pu. SG31 is at 0.040 pu (0.6 % of range) from pmax already in the validated pre-event equilibrium and in the S0 reference. The S0 run records margins on both physical powers and references (summary metrics).
B3-S0 run (C2t, graph, gains, 200 s, 0.00390625 s step, activation at t = 5 s, all frozen from E8; script run_b3_ieee39.py; reference xi_pre so the offset is v_RDC(xi_pre)): predeclared invariance gates (a check of invariance of the nominal equilibrium, not an improvement test) passed. v_nom at the activation step 1.1e-10 pu/s (B2 original field: 0.0133 pu/s in Q, 0.0009 in P); frequency deviation after activation 0.0 Hz (B2: 0.22 mHz); unit-voltage change from the pre-activation value 7.8e-15 pu (B2: 0.050 pu); physical P and Q changes 1.3e-11 and 1.1e-10 pu (B2: 0.0054 and 0.598 pu); Pset - Pn and Qset - Qn at most 1.8e-8 and 9.3e-9 pu (B2: 0.019 and 0.993 pu); actuator signals: |paux| 2.4e-10, |qaux| 5.7e-11, |z| 5.6e-10 pu (B2: 4e-6, 6e-3, 0.054), no clamp hit (clamp margin 0.100; B2 0.046), references inside W_i (min g_P 0.0026 normalized, min g_Q 0.200; B2 0.0024, 0.200). No saturation and no transient excess over pmax in either run (SG31 physical margin 0.040 pu, SG35 0.100 pu in B3; 0.098 in B2). DAE residual 4e-9 (B3) and 4e-7 (B2 replica).
Reading of the result: B3-S0 stays at the pre-event equilibrium to numerical precision, which is the intended property of the S0 rule and is largely by construction (the initial state is the reference, so the centered field is zero up to round-off). It does not show performance, stability or safety. Against B2 the difference is that B2 drifts toward 1.0 pu voltage (unit voltages move up to 0.05 pu, Q up to 0.6 pu) while B3 does not regulate voltage in S0; this difference is by construction (DEC-038) and must not be read as a quality ranking.
Next stages (condition 6, not run): P+ and Q+ one at a time with figures and review, using the B3-A xi*(d). The reference switch from xi_pre to xi*(d) at the event will be recorded (offset jump up to 0.257 pu/s in P, 0.015 pu/s in Q, DEC-038) with the continuity of the physical references and rate limits; the SG35 effective-reference margin (0.65 % of range) and SG31 will be tracked.
Evidence reviewed: IEEE39_B3_C2t_S0_summary.json, the five S0 figures, IEEE39_B3A_C2t_margin_check.json, run_b3_ieee39.py, E8 S0 series (read only).
Blockers or limitations: S0 only; the B3-S0 gate is invariance, not performance; the S0 raw series (67.6 MB) is local only by the >10 MB policy; no stability, regional-stability, dynamic-safety or physical P/Q invariance claim; OPEN-SG31-PMAX stays open and E9 blocked.
Responsible: Integrator
Status: PARTIALLY_VERIFIED
Next action: Investigator reviews the B3-S0 figures and metrics; if approved, B3 on P+ with its own figures and review, then Q+.
