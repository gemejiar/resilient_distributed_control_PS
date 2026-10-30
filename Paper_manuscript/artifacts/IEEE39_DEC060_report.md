# DEC-060 report: controlled resolution of the gate TUNE → TEST

Written for: the investigator who issued DEC-060. Branch `review/dec059-scientific-reorientation`. `main`, `main.tex`, ANDES source, historical results, directory structure and TEST are untouched. TEST was **not opened**.

## 1. Verdict

**Gate REJECTED, TEST sealed.** Acta: `IEEE39_DEC060_gate_TEST.json` (`REJECTED_TEST_SEALED`). Two independent reasons:
- **Mandatory safety blocker.** The OC1 cell b20 S3 becomes eligible at the cut dispatch (its T-A admissibility flips to true) and is UNSAFE in TDS (min Pmax margin −0.2084 pu), exactly as pre-registered (H-D).
- **Protocol criteria.** G3 fails in OC1 on (i), (iii) and (iv) and in OC2 on (iii) (TUNE). The criteria were applied literally and unchanged.

## 2. Three groups, kept apart

| Group | Content |
|---|---|
| 1. Original protocol | OC1 (reading A, rule applied at the dispatch under test): FAIL (i) b20 S3 UNSAFE; (iii) b20 S2 e = 1.58e-3 and b20 S3 e = 2.6e-3 exceed 1e-3; (iv) b7 S3, b16 S3, b24 S3 unit-V error at 200 s above 1e-3. OC2: FAIL (iii) at TUNE, no cut cycle exists. TEST cohort: none |
| 2. Alternative criteria (not used for the verdict) | Eligibility fixed at TUNE (b20 S3 not eligible): fail (iii), (iv). Cut cells only: fail (iii), (iv). One-sided (iii): (iii) met, (i) and (iv) still fail. None passes |
| 3. Post-TUNE changes | `dispatch_z` accepts M3CUT; recheck set wider than the protocol text (8 cells); one-sided criterion study; long-horizon extrapolation; ledger block RES. All declared in Addendum C before the TDS |

## 3. The OC1 cells (D2)

Prediction files and Addendum C were committed (50018f9) before the first recheck TDS. All eight predicted classes match the TDS classes.

| Cell (TUNE) | Class at M3+OS (before) | Eligible at M3+OS | Predicted margin at cut | TDS margin at cut | Class at cut | Eligible at cut |
|---|---|---|---|---|---|---|
| b20 S2 | UNSAFE | yes | +0.0150 | +0.0166 | SAFE (above U_D8 = 0.0109) | yes |
| b16 S3 | UNSAFE | yes | +0.1290 | +0.1297 | SAFE | yes |
| b24 S3 | UNSAFE | yes | +0.1335 | +0.1339 | SAFE | yes |
| b20 S3 | UNSAFE, INADMISSIBLE_AT_EVENT | no | −0.2110 | **−0.2084** | **UNSAFE** | **yes (newly admissible)** |
| b7 S2, b16 S2, b24 S2 | SAFE | yes | +0.076 / +0.167 / +0.168 | +0.076 / +0.167 / +0.168 | SAFE | yes |
| b7 S3 | NUMERICALLY_INDETERMINATE | yes | +0.0037 | +0.0040 | NUMERICALLY_INDETERMINATE (not counted safe) | yes |

The three target cells are SAFE at the cut dispatch. The cut does not damage the supplementary cells.

**Mechanism (H-B confirmed).** The cut lowers the pre-event SG33 set-point by 0.157 pu (6.511 → 6.354 pu; Pmax 6.82 pu); every other component of the dispatch vector moves by at most 6e-4. SG33 stays the binding unit in the b20 and S3 cells. Sub-cycle: in the b7 and b20 cells the 50-ms peak is the binding margin (m50 below the margin after 50 ms); in the b16 and b24 cells it is not. G1-P at the cut dispatch passes (20 s, drift and band criteria of the protocol).

**Why b20 S3 matters.** The cut cycle added only the three cells that were eligible and UNSAFE at TUNE. By lowering SG33 it also made b20 S3 admissible at the jump, which promotes it under the DEC-055 rule, and its amplitude exceeds what the dispatch can absorb. Excluding it would require changing the eligibility rule after seeing the data; I did not do that (reading B is reported only as an alternative). A second cut cycle is not allowed by the protocol, so a design that includes b20 S3 would be a **new revision** with its own gate.

## 4. Sign of the prediction error (D1)

Convention: m = Pmax − P; e = m_TDS − m_pred; e > 0 means a pessimistic prediction (`IEEE39_DEC060_sign_audit.json`).
- The 50-ms minimum margin recomputed from the raw series of all 16 TUNE runs equals the stored metric (max difference 0.0).
- TUNE: 16/16 e > 0 (7.3e-5 to 3.2e-3), none optimistic; 5 cells exceed 1e-3, all conservative. Recheck: 8/8 e > 0 (6e-5 to 2.6e-3); 2 exceed 1e-3 (b20 S2, b20 S3).
- Calibration: the dense model is conservative in 18/18 cells (6e-5 to 6.4e-4); the dt-grid M3 predictor is optimistic in 18/18 (e down to −0.0159). The one-sided criterion e ≥ −1e-3 rejects the dt-grid predictor in 16/18 cells and accepts the dense one, so it does penalise optimistic errors. The calibration cells include the TUNE cells, so this check is in-sample.
- False-SAFE bound: if a cell is predicted SAFE (m_pred ≥ U_D8) and e ≥ −1e-3, then m_TDS ≥ 0.0099 > −U_D8, so the TDS class cannot be UNSAFE; the worst case is a downgrade to INDETERMINATE. Data: 0 cells predicted SAFE and UNSAFE in TDS. The bound covers the 50-ms Pmax peak only.
- Conclusion: a one-sided criterion would accept no false SAFE. It was chosen after seeing the data and is a post-TUNE amendment; it is **not** used to declare (iii) met. It does not bound over-conservatism (that costs dispatch cost J, not safety).

## 5. Criteria (iii) and (iv)

- **(iii) two-sided, primary:** not met (TUNE OC1 and OC2; recheck OC1).
- **(iv) 1e-3 pu at 200 s, primary:** not met in the three S3 cells (errors 1.29e-3, 1.01e-3, 1.01e-3).
- **Long-horizon diagnostic (no TDS):** an exponential fit on 100–200 s extrapolates to 1e-3 pu at about 245 s (b7 S3), 202 s (b16 S3) and 201 s (b24 S3). This suggests slow convergence rather than divergence, but it is an extrapolation and does not replace the criterion.

## 6. TDS budget (D5)

Ledger: **41 of 120** (R2 10, R3 4, R4 18, RES 9). My earlier "about 125" assumed the recheck on top of the full reserve; the recheck now consumes RES.

| Line | Plan | Priority | Cumulative if run |
|---|---|---|---|
| Used | 41 | | 41 |
| R5A blind TEST (OC × 3 buses × S1–S3 × M0, M3+OS) | 36 (18 per OC) | 1 | 77 |
| R5B comparison B2, B1s, B4′ | 18 (9 per OC) | 1 | 95 |
| R5C OC3 demanding case | 6 | 2 | 101 |
| K4 illustration | 4 (first read from existing logs) | 2 | 105 |
| R5D τ_info | 2 | 3 (cut first) | 107 |
| R6 frontier | 8 | 3 (cut first) | 115 |

Slack: 5. The priority-1 plan reaches 95, 25 below the cap. Cut order: R6, R5D, K4, R5C. TEST runs only for OCs with a cohort, so no line is authorised now.

## 7. Decision on opening TEST

TEST stays sealed. No OC meets the protocol and there is a safety blocker. Rerunning the gate on the same data cannot change that. The remaining routes are new decisions: a **new revision** (a design that includes b20 S3 or a different eligibility rule, with new TUNE and gate), or a **new protocol revision** with the one-sided criterion (iii) and a justified horizon for (iv), declared as post-TUNE and gated on fresh cells. OC3 is unchanged: out of hypothesis, no LQR integrated. Alternative described without TDS: an LQR auxiliary gain for the CLF row would make H_r definite at the unstable OC3 target; it needs its own methodological decision.

## 8. Not claimed

No regional stability, no physical invariance, no universal safety. B5′ evidence stands at TUNE/recheck level on IEEE-39 C2 (SG–GFM); no TEST evidence exists.
