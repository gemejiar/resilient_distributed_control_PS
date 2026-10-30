# DEC-062 protocol v3.0: independent evaluation of the frozen design

Versioned. It does not replace `DEC059_protocol.md` (Addenda A–C) or `DEC061_protocol.md` (v2.0). Their verdicts stay as recorded: gate TUNE → TEST REJECTED (DEC-059), REJECTED (DEC-060), **G-v2 REJECTED (DEC-061)**, with every failed criterion preserved. Recorded and committed before any DEC-062 TDS.

## 1. Authority and purpose

DEC-062 (investigator): stop adjusting the design; run an independent evaluation of the contributions T1, T2, P3 and of B5′ with M3+OS, with a blind TEST that is authorised although G-v2 stays REJECTED. Objective: definitive evidence, not retroactive approval.

## 2. Frozen objects (no change after this commit)

| Object | Frozen as |
|---|---|
| Controller B5′ | `dec059_b5.py`, parameters v̄ = 0.01·Sn pu/s, α = 1/s, R = diag(v̄⁻²), ρ_s = 1e6, τ_info = 1 s, ε_sel = 0.01, λ = 1/(2 λ_max(H_r)), E* rule (`dec059_eq.py`) |
| Preventive design | OC1: rev3 (`DEC059_state/m3os_rev3_OC1.json`, M3+OS with b20 S3 in the design set). OC2: M3+OS (`m3os_OC2.json`). M0 (the DEC-055 static dispatch) is the no-redispatch reference. Both M3+OS dispatches come from the same Algorithm 1, eps and overshoot term |
| Predictor | dense post-jump model without allowances (`dec059_pred.py`, T_OS 50 ms) |
| Classification | rule M3V-1 (Addendum B item 1), U_D8 = 0.0109 pu; eligibility rule of Addendum B item 4 (S1/S2 confirmatory, S3 promoted when admissible at the jump), applied at the dispatch under test |
| Solver | ANDES 2.0.0 unmodified, trapezoid dt = 2⁻⁸, local dt/16 on [t_e − dt, t_e + 0.5 s], tol 1e-4, `reset_tiny = 0` |
| Comparators | B2 (original RDC), B1s (separately saturated integral controller), B4′ (B5′ without the CLF row); B3 is not part of the comparison |
| Topology, limits, gains, historical results, OC definitions | unchanged; OC3 is not run |

## 3. Status of the criteria

- (iii-H) two-sided |e| ≤ 1e-3 pu: kept as the historical criterion; reported everywhere.
- (iii-U) one-sided e ≥ −1e-3 pu: alternative, **post-TUNE in origin**, proposed in DEC-061, unvalidated. Its first prospective evidence is the OC2 fresh-bus lot of section 4 and then TEST. The 16 TUNE, 8 recheck and 8 rev3 cells motivated it and are not evidence of validation.
- (iv) unit-voltage error ≤ 1e-3 pu at 200 s: unchanged. The three S3 cells of OC1 rev3 that failed it stay recorded: b7 S3 (1.278e-3), b16 S3 (1.015e-3), b24 S3 (1.011e-3). Settling time (0.01 Hz for frequency; time to 1e-3 pu for unit voltage, extrapolated when not reached) is reported as complementary information.

## 4. Pre-TEST validation (9 TDS, ledger block `D62V`)

- **D62A (1 TDS):** G1-P of OC1 at the rev3 dispatch, plant without secondary control, 20 s (completes the reduced G1-P of DEC-061).
- **D62B (8 TDS):** OC2 at the frozen M3+OS with B5′: fresh buses {3, 4, 12} × {S2, S3} (6) — never in DESIGN, TUNE or TEST, and not used to motivate (iii-U); buses 3 and 12 were observed in the older DEC-054 campaign, which does not touch this design or this criterion — plus two exact repeats of OC2 TUNE runs (b20 S3, b7 S3) to test reproducibility (2).
- No parameter, dispatch, eps or cell is adjusted from these results.

Checks (all obligatory for the access acta; they are integrity and physical-consistency checks, not safety outcomes):

| ID | Check | Prediction |
|---|---|---|
| V1 | G1-P OC1 rev3 passes (0.005 Hz, 1e-3 pu, buses in band) | pass |
| V2 | the two repeats are bit-identical to the TUNE runs | pass |
| V3 | E* targets of the six fresh events satisfy E4 and H1–H5; no QP fallback; min c_j ≥ 0 (T1) in every run | pass |
| V4 | no TDS failure | pass |
| V5 | no false SAFE (cell predicted SAFE and UNSAFE in TDS) | pass |
| V6 | T2 local behaviour: the Lyapunov value decays (V_end/V_first < 1) in every run | pass |

Reported but not blocking: classes of the fresh cells (predicted SAFE in all six: m̂ = +0.619, +0.588 (b3 S2, S3), +0.566, +0.510 (b4), +0.542, +0.473 (b12), binding unit SG31, all admissible at the jump), (iii-U), (iii-H), (iv), settling. An UNSAFE fresh cell that was predicted UNSAFE or INDETERMINATE is a result, not a blocker; a false SAFE is a blocker (V5).

## 5. Modification of the TEST access rule (recorded, post-TUNE)

The original rule (Addendum B item 4 and DEC-055) opens TEST for an OC only after G3 passes. All three attempts failed: DEC-059 (OC1 and OC2), DEC-060 (OC1 cut), DEC-061 G-v2 (OC1 rev3). By DEC-062 the access rule becomes: **TEST opens as an independent evaluation if checks V1–V6 pass and the freeze of section 6 is complete.** This is a change made after observing TUNE. It does not approve G3 retroactively and does not make the original protocol fulfilled. Every TEST result is reported with the label `EVALUATION_UNDER_MODIFIED_ACCESS_RULE`, next to the failed G3/G-v2 verdicts.

## 6. Freeze before any TEST file exists

Before any target, prediction, plan or TDS that contains a TEST bus (21, 31, 39) is created: an annotated tag `dec062-freeze`, and the acta `IEEE39_DEC062_gate_TEST_access.json` with hashes of the design files, targets used so far, predictions, code, protocol files, criteria document, theory, versions and the metric/classification rules; TEST intactness scan. TEST targets are computed after the freeze with the frozen E* rule; TEST predictions and the cohort plan are committed before the first TEST TDS of that cohort (A: 36 blind runs; B: 18 comparison runs).

## 7. TEST design (summary; predictions are registered at the freeze, per cohort)

- **Cohort A (36 TDS):** OC1 and OC2 × buses {21, 31, 39} × {S1, S2, S3} × {M0, M3+OS} with B5′. Separates the dispatch effect (M0 vs M3+OS, same controller).
- **Cohort B (18 TDS):** the three S2 TEST cells at the M3+OS dispatch of each OC with B2, B1s and B4′. Separates the controller effect (same dispatch, event, solver) and, against cohort A, the CLF row (B4′ vs B5′).
- Evaluation: T1 (min c_j ≥ 0 in B5′/B4′ runs and the discrete bound), T2 (target labels, local decay of the Lyapunov value), P3 (N1/N2 predicted vs observed; labels TARGET_UNSTABLE/NOT_VERIFIED), physical safety (P, Q, S, V margins; class by M3V-1), frequency (nadir, RoCoF over 100 ms, error at 120 and 200 s, settling), voltage (unit-bus error to the target and to 1 pu, bus band), control effort (total variation and peak rate of the P and Q set-points), sharing.
- Original criteria (G3 (i)–(iv)) and the alternative (iii-U) are reported separately, per OC and per cell, plus all failures and indeterminacies.
- TEST is not used to change anything. A negative result is documented, and no method change follows.

## 8. Levels of the final matrix

DEMONSTRATED (proof in the repository and unit tests); VALIDATED (observed on TEST within the stated domain with the pre-registered hypotheses holding); PARTIALLY SUPPORTED (analytic result with evidence only in the design/tuning cells, or TEST evidence with failed or indeterminate cells); REFUTED (a pre-registered hypothesis falsified).

## 9. Budget

Ledger before this protocol: 49 of 120. Committed: D62V 9 + cohort A 36 + cohort B 18 = 63 → **112**, leaving 8. `BUDGET`: R5 62 → 54, K4 4 → 0 (K4 is read from the logs of the existing runs), `D62V` 9. OC3, R5C, R5D, R6 are not run.

## 10. Not claimed

No physical invariance beyond the reference set (T1), no regional stability (T2), no general safety from a few TDS, no retroactive compliance with the original protocol, no validation of (iii-U) before TEST.

## 11. Post-TUNE changes declared here

(a) the TEST access rule of section 5; (b) `dec059_pred.py` accepts the `val` set and its `test` set now lists S1, S2, S3 (before: S1, S2); (c) BUDGET edit; (d) `dec062_*` modules.

## Addendum A (recorded after the freeze and before any TEST TDS; append-only)

Freeze: tag `dec062-freeze`, acta `IEEE39_DEC062_gate_TEST_access.json` (`ACCESS_AUTHORIZED_FREEZE_COMPLETE`, V1-V6 pass, TEST intact before the freeze). The 36 E* targets of cohort A (computed with the frozen rule) all satisfy E4 and H1-H5. Predictions `IEEE39_DEC059_pred_{OC1_M0,OC1_M3REV3,OC2_M0,OC2_M3OS}_test.json` are committed with this addendum. The plans `IEEE39_DEC059_R5A_plan.json` and `R5B_plan.json` are sealed in the same commit.

**Predicted classes (pre-TDS, dense model without allowances; margin = min Pmax margin in the first 50 ms, pu).**

| OC | Dispatch | Cell | Predicted margin | Unit | Class | Admissible at the jump |
|---|---|---|---|---|---|---|
| OC1 | M0 | b21P_S1 | +0.011 | SG31 | INDET | yes |
| OC1 | M0 | b21P_S2 | -0.062 | SG35 | UNSAFE | NO (N2) |
| OC1 | M0 | b21P_S3 | -0.140 | SG35 | UNSAFE | NO (N2) |
| OC1 | M0 | b31P_S1 | -0.125 | SG31 | UNSAFE | NO (N2) |
| OC1 | M0 | b31P_S2 | -0.285 | SG31 | UNSAFE | NO (N2) |
| OC1 | M0 | b31P_S3 | -0.444 | SG31 | UNSAFE | NO (N2) |
| OC1 | M0 | b39P_S1 | +0.031 | SG31 | SAFE | yes |
| OC1 | M0 | b39P_S2 | +0.027 | SG31 | SAFE | yes |
| OC1 | M0 | b39P_S3 | +0.024 | SG31 | SAFE | yes |
| OC1 | M3REV3 | b21P_S1 | +0.196 | SG31 | SAFE | yes |
| OC1 | M3REV3 | b21P_S2 | +0.172 | SG31 | SAFE | yes |
| OC1 | M3REV3 | b21P_S3 | +0.113 | SG35 | SAFE | yes |
| OC1 | M3REV3 | b31P_S1 | +0.060 | SG31 | SAFE | yes |
| OC1 | M3REV3 | b31P_S2 | -0.099 | SG31 | UNSAFE | NO (N2) |
| OC1 | M3REV3 | b31P_S3 | -0.259 | SG31 | UNSAFE | NO (N2) |
| OC1 | M3REV3 | b39P_S1 | +0.216 | SG31 | SAFE | yes |
| OC1 | M3REV3 | b39P_S2 | +0.213 | SG31 | SAFE | yes |
| OC1 | M3REV3 | b39P_S3 | +0.209 | SG31 | SAFE | yes |
| OC2 | M0 | b21P_S1 | +0.656 | SG31 | SAFE | yes |
| OC2 | M0 | b21P_S2 | +0.612 | GFM36 | SAFE | yes |
| OC2 | M0 | b21P_S3 | +0.540 | SG35 | SAFE | yes |
| OC2 | M0 | b31P_S1 | +0.523 | SG31 | SAFE | yes |
| OC2 | M0 | b31P_S2 | +0.365 | SG31 | SAFE | yes |
| OC2 | M0 | b31P_S3 | +0.209 | SG31 | SAFE | yes |
| OC2 | M0 | b39P_S1 | +0.676 | SG31 | SAFE | yes |
| OC2 | M0 | b39P_S2 | +0.673 | SG31 | SAFE | yes |
| OC2 | M0 | b39P_S3 | +0.669 | SG31 | SAFE | yes |
| OC2 | M3OS | b21P_S1 | +0.656 | SG31 | SAFE | yes |
| OC2 | M3OS | b21P_S2 | +0.612 | GFM36 | SAFE | yes |
| OC2 | M3OS | b21P_S3 | +0.540 | SG35 | SAFE | yes |
| OC2 | M3OS | b31P_S1 | +0.523 | SG31 | SAFE | yes |
| OC2 | M3OS | b31P_S2 | +0.365 | SG31 | SAFE | yes |
| OC2 | M3OS | b31P_S3 | +0.209 | SG31 | SAFE | yes |
| OC2 | M3OS | b39P_S1 | +0.676 | SG31 | SAFE | yes |
| OC2 | M3OS | b39P_S2 | +0.673 | SG31 | SAFE | yes |
| OC2 | M3OS | b39P_S3 | +0.669 | SG31 | SAFE | yes |

Notes fixed before the runs:
- OC2: the M3+OS dispatch differs from M0 by at most 1.1e-4 in the design vector (0.06 MW in total), so the two OC2 dispatches give the same predictions. The OC2 M0 runs are near-duplicates and test sensitivity to a negligible dispatch change; they are kept because the cohort was committed that way.
- OC1: at M0 the cells b21 S2, b21 S3 and b31 S1-S3 are predicted UNSAFE (b21 S1 INDETERMINATE); at rev3 the cells b31 S2 and b31 S3 stay inadmissible at the jump (predicted UNSAFE for any controller of the rate-bounded class, label INADMISSIBLE_AT_EVENT, outside the safety claim), and b31 S1 is SAFE at +0.060.

**Hypotheses and falsifiers (all pre-registered).**
- HA1: the TDS class equals the predicted class in all 36 cohort-A cells. Falsifier: any mismatch; a false SAFE (predicted SAFE, UNSAFE in TDS) refutes the predictor.
- HA2: e = m_TDS - m_pred >= 0 in every cell with a prediction (the dense model is conservative). (iii-U) holds; falsifier: any e < -1e-3.
- HA3 (T1): min_j c_j >= 0 and no QP fallback in all 36 B5' runs and in the B4' runs.
- HA4 (T2): every target is VERIFIED_LOCAL and the Lyapunov value ends below its first valid value (ratio < 1) in all B5' runs. T2 makes no claim beyond the neighbourhood actually visited.
- HA5 (P3, N2): a cell with a_j < 0 predicted is never SAFE in TDS, for any controller (cohort B included).
- HA6: OC2 M0 vs M3+OS: |difference| <= 1e-3 pu in the 50-ms margin and the same class.
- HA7 (iv): the unit-voltage error at 200 s exceeds 1e-3 pu in the OC1 S3 cells that are eligible (b21 S3, b39 S3 at rev3) as in the TUNE S3 cells, and stays below 1e-3 pu in OC2 and in S1/S2 cells. These failures are recorded, not corrected.
- HB1 (Proposition OS, controller independence of the sub-cycle window): in cohort B, |m50(B2/B1s/B4') - m50(B5')| <= 1e-3 pu for each cell. Falsifier: any difference above 1e-3.
- HB2: B5' and B4' differ by the CLF row only; their 200-s frequency errors are within 1e-3 Hz of each other.
- HB3: the controller effect is separated from the dispatch effect by construction: cohort B uses the same dispatch for the four controllers; the dispatch effect is read from B5' at M0 vs M3+OS (cohort A). The B2/B1s/B4' arms at M0 do not exist (budget), so the dispatch effect for them is not measured.

**Reporting rules.** All 36 + 18 results are reported, including failures, indeterminates and TDS failures. Original criteria (G3 (i)-(iv)) and the alternative (iii-U) are reported separately per OC and dispatch, always labelled `EVALUATION_UNDER_MODIFIED_ACCESS_RULE`. The label of the OC1 dispatch is M3+OS rev3. No parameter, cell, threshold or dispatch changes after this commit.
