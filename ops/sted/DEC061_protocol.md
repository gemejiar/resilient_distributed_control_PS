# DEC-061 protocol v2.0: OC1 design revision 3 and its independent gate TUNE → TEST

Versioned protocol. It does **not** replace `DEC059_protocol.md` (with Addenda A–C), which stays as the historical record of the DEC-059/DEC-060 gates and their REJECTED verdicts. It applies only to the objects named here. Recorded and committed before any DEC-061 TDS.

## 1. Authority and scope

- Authority: DEC-061 (investigator): limited OC1 revision with b20 S3 mandatory in the design set; prospective one-sided criterion (iii); criterion (iv) unchanged; up to 8 additional TDS; independent gate.
- In scope: OC1 only, DESIGN/TUNE buses {8, 23, 28, 25} and {7, 20, 16, 24}. Out of scope: OC2 (no new design, no new TDS), OC3, ANDES, topology, B2/B3 studies, the B5′ controller and its parameters, TEST buses {21, 31, 39}.
- TEST stays sealed. This protocol does not open it.

## 2. Objects under test

1. **Design revision 3** (`DEC059_state/m3os_rev3_OC1.json`): Algorithm 1 of DEC-054 unchanged (formulation, cfg, eps vectors including eps_OS and U_D8, K_max, seed), M3 + overshoot term; design events = 12 DESIGN cells + the three cut cells {b20 S2, b16 S3, b24 S3} + **b20 S3** (16 events). The other four OC1 TUNE cells {b7 S2, b7 S3, b16 S2, b24 S2} are monitors: they must not degrade.
2. **Controller**: B5′ exactly as frozen in DEC-059 (v̄, α, R, ρ_s, τ_info, ε_sel, E* rule, λ = 1/(2 λ_max(H_r))). No parameter is changed (see D4 analysis, `IEEE39_DEC061_settling_analysis.json`).
3. **Eligibility rule**: unchanged. S2 cells are eligible; S3 cells are promoted when `admissible_at_jump` is predicted true at the dispatch under test. All eight OC1 TUNE cells are eligible at rev3 (all admissible).

## 3. Feasibility analysis before the optimiser (D1) — recorded

- Necessary-condition scan (`IEEE39_DEC061_feasibility_scan.json`, 20 cells, no optimiser, no TDS): lowering only the SG33 set-point raises the b20 S3 design margin from −0.226 to −0.094 at −0.15 pu and then saturates at about −0.09 because SG31 becomes the binding unit. The scan is one-dimensional: it is **not** a certificate of infeasibility, and the full-space optimiser showed it (voltage set-points also move).
- Optimiser (`m3os_rev3_OC1.json`): status FEASIBLE_PREDICTED at the first working set, J = 2.399 (cut: 1.876, M3+OS: 1.759), redispatch 99.4 MW against the case (cut 76.8, M3+OS 61.2), pre-event initialisation valid. Relative to the cut dispatch SG33 moves by a further −0.227 pu; every other unit moves by at most 2e-3 pu.
- Predicted margins (pre-TDS, no allowances) of all 20 cells are in section 5. Jump admissibility holds in all 20. No design event has a negative design margin (minimum ≈ 0, within the cut tolerance τ_cut = 1e-4). The monitor cells do not degrade (b7 S2 +0.0756, b7 S3 +0.0037 as before, b16 S2 +0.1674, b24 S2 +0.1682).
- Stability: E* targets (E4, H1–H5) of the dispatch and of the eight TUNE events are computed before the TDS and enter the gate (condition C2).

## 4. Criteria of the gate G-v2 (all obligatory)

| ID | Condition | Status of the rule |
|---|---|---|
| C1 | Design FEASIBLE_PREDICTED with b20 S3 in the design set; monitors do not degrade; init valid | new, prospective |
| C2 | E* targets of d0 and the eight TUNE events satisfy E4 and H1–H5 | unchanged from DEC-059 |
| C3 | G1-P in reduced form (see below) | declared substitution |
| C4 | Rule M3V-1 classification of the 8 cells: (i) no eligible cell UNSAFE; (ii) no TDS failure | unchanged |
| C5 | (iii-U) one-sided predictor criterion, e ≥ −1e-3 pu (`IEEE39_DEC061_criterion_iii.md`) | **post-TUNE modification**, proposed, unvalidated |
| C6 | (iv) B5′ conditions G-R3 in every run, including unit-voltage error ≤ 1e-3 pu at 200 s for targets satisfying T2 | **unchanged, horizon unchanged** |

- Reported but not part of the verdict: (iii-H) the historical two-sided |e| ≤ 1e-3; INDETERMINATE cells (reported NOT_VERIFIED, never counted safe); long-horizon extrapolation of the voltage error (diagnostic only).
- C3 substitution: the 8-TDS cap does not cover a 20-s plant run. G1-P is evaluated on the first 5 s (pre-event) of each of the eight event runs, with the same drift and band criteria (0.005 Hz, 1e-3 pu, buses in [0.95, 1.05]). That segment runs B5′ at the d0 target, so it checks that the dispatch is an equilibrium of the plant under an idle controller, not the plant without secondary control. A full 20-s G1-P needs 1 more TDS; it is not run.
- Mandatory safety blocker: any eligible cell UNSAFE, a TDS failure, or an E* target failing E4. If one is present TEST is not opened, whatever the other criteria say.

## 5. Hypotheses and predictions (static, committed before any DEC-061 TDS)

Files `IEEE39_DEC059_pred_OC1_M3REV3_{design,tune}.json` (the script name is historical).

| Cell | Predicted margin m̂ (pu) | Binding unit | Predicted class | Predicted e200 (pu), from the DEC-059/060 runs | (iv) predicted |
|---|---|---|---|---|---|
| b7 S2 | +0.0756 | SG31 | SAFE | 8.3e-4 | pass |
| b7 S3 | +0.0037 | SG31 | NUMERICALLY_INDETERMINATE | 1.29e-3 | **fail** |
| b20 S2 | +0.1813 | GFM34 | SAFE | 5.8e-4 | pass |
| b20 S3 | +0.0150 | SG33 | SAFE (0.004 above the band) | 9.0e-4 | pass |
| b16 S2 | +0.1674 | SG31 | SAFE | 6.5e-4 | pass |
| b16 S3 | +0.1411 | SG31 | SAFE | 1.01e-3 | **fail (marginal)** |
| b24 S2 | +0.1682 | SG31 | SAFE | 6.5e-4 | pass |
| b24 S3 | +0.1424 | SG31 | SAFE | 1.01e-3 | **fail (marginal)** |

- H1: all eight classes equal the predicted ones.
- H2: e = m_TDS − m̂ ≥ 0 in all eight cells (34/34 so far); (iii-U) holds. Falsifier: any e < −1e-3.
- H3: (iii-H) fails if |e| > 1e-3 in any cell (it did for b20 cells before); reported only.
- H4: the unit-voltage error at 200 s depends on the dispatch by less than 1e-5 pu (b16 S3 and b24 S3: 1.0066e-3 at M3+OS and at the cut). Hence **(iv) is predicted to fail in b7 S3, b16 S3 and b24 S3**, and the gate G-v2 is predicted REJECTED on C6. The D4 analysis explains why no permitted parameter changes it.
- H5: the eight TDS are justified by evidence for the safety side (b20 S3 SAFE, no degradation of other cells, predictor sign), not by an expected PASS of the gate.

## 6. Non-repetition and freeze rules

- One design attempt (rev3), one TDS lot (8 TDS), one gate run. A failed condition is not followed by retuning of the dispatch, eps, cells, thresholds or controller; further work needs a new decision of the investigator.
- If the gate is APPROVED: before any TEST TDS, an annotated git tag `dec061-freeze` and the acta record the hashes of the design file, targets, predictions, code, protocol, criteria document, theory, ANDES/numpy/scipy/kvxopt versions, solver configuration and the metric definitions; TEST intactness is scanned; the R5 plans are sealed and committed before the first TEST TDS.
- If the gate is REJECTED: TEST stays sealed.

## 7. Budget

- Ledger before this protocol: 41 of 120. DEC-061 authorises up to 8 (new block `D61`). The BUDGET table is rebalanced to keep the sum at 120: R6 8 → 0 (secondary, cut first), `D61` +8. R5 stays 62 (TEST 36 + comparison 18 reserved, OC3 6, τ_info 2), K4 4, RES 10 (1 left).
- Reserved for TEST and the main comparison: 54. After the lot: 120 − 49 = 71; minus the 54 reserved leaves 17 for R5C (6), K4 (4) and R5D (2) = 12, with 5 of slack. Those secondary lines run only if justified.

## 8. Post-TUNE and post-DEC-060 changes declared here

(a) rev3 design set; (b) criterion (iii-U); (c) `M3REV3` accepted by `dispatch`/`dispatch_z`; (d) ledger block `D61` and R6 set to 0; (e) C3 substitution; (f) the first feasibility-scan artefact was produced with an indexing bug (the Problem cache is keyed by scenario index) and was replaced by the corrected scan before use.

**Pre-TDS addendum (same commit).** The nine E* targets of the rev3 dispatch (d0 and the eight TUNE events) were computed before the plan: all satisfy E4 and H1-H5 (rightmost closed-loop eigenvalue between -0.00264 and -0.00284 1/s). Condition C2 is therefore met before any TDS; the plan `IEEE39_DEC061_D61_plan.json` seals the eight runs.
