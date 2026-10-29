# DEC-059 progress report: proposed controller B5′, corrected theorems, R4 and TUNE

Branch `review/dec059-scientific-reorientation` (from 000eb9f). `main`, `main.tex`, ANDES source, historical results and the directory structure are untouched. Written for: the investigator reviewing the gate decisions.

## 1. Status in one table

| Line | Status | Evidence |
|---|---|---|
| R1 theory and matrix | Done | `IEEE39_DEC059_theory.md`, `IEEE39_DEC059_contribution_matrix.csv` |
| R2 numerical closure (10 TDS) | Done | `IEEE39_DEC059_R2_results.json` |
| R3 B5′ (4 smoke TDS) | G-R3 passed in OC1/OC2; OC3 outside T2 hypotheses | `IEEE39_DEC059_R3_smoke_metrics.json` |
| R4 M3+OS design | OC1 and OC2 FEASIBLE_PREDICTED | `DEC059_state/m3os_OC{1,2}.json` (local), predictions committed |
| Gate R4 → TUNE | **PASS 6/6** | `IEEE39_DEC059_gate_R4_TUNE.json` |
| G1-P at M3+OS (2 TDS) | PASS OC1, OC2 | D59T015–016 |
| TUNE (16 TDS) | Executed; G3 **FAIL** in both OC | `IEEE39_DEC059_TUNE_results.json`, F6 |
| Gate TUNE → TEST | **REJECTED**; TEST not opened | `IEEE39_DEC059_gate_TEST.json` |
| R5 TEST, comparison, R6 | **Not run** (blocked by the gate) | — |

TDS ledger: **32 of 120** (R2 10, R3 4, R4 18). Remaining plan lines: R5 62, K4 4, R6 8, reserve 10, plus 4 unspent in R2/R3. An earlier message said 15 at one point; the ledger count (32) is the authority.

## 2. Corrected formal results (R1)

Full statements and proofs are in `IEEE39_DEC059_theory.md`.
- **T1 (proved, unit-tested).** Discrete-time invariance of the reference set W under the QP constraints (Q1)–(Q3): c_j(u_k) ≥ (1 − γ)^k c_j(u₀). T1-F gives an explicit sufficient condition for QP feasibility and uniqueness (v = 0 is feasible on W).
  - Scope: references only. It implies nothing for delivered P, Q, V.
  - 8 unit tests pass, including an independent SLSQP check.
- **T2 (proved conditional).** Local exponential stability of the sampled-data B5′ loop under H1–H5, which are verified numerically per target. The domain N is not quantified; first-order radii are estimates, not certificates.
- **P3 (replaces Th3).** Classification: N1 and N2 are proved necessary conditions, V is a numerically verified local condition, O is observed TDS outcome.
- **Lemma C** (centering) and **T-A / Proposition OS** (post-event admissibility and sub-cycle window are controller-independent in the rate-bounded class).
- Effects on novelty, title and abstract: section 8 of the theory file. In short, "regional" and "physical invariance" must go; "local", "evaluated" and "preventive" replace them.

## 3. R2 numerical closure (reset_tiny = 0)

| Item | Result |
|---|---|
| N1/N2 | D8 transient vs `reset_tiny` 1: max |ΔP| 3.1e-7 pu on [t_e, t_e+0.5]. Repeat run bit-identical |
| N3 | OC3 M3 refutation reproduced: SG31 margin −0.013947 (DEC-057: −0.013947; difference 2.7e-9) |
| G1-P (M0) | PASS OC1, OC2, OC3 (drift ≤ 1.4e-14) |
| B3 flat OC1/OC2 | Deviation ≤ 1e-13: confirmed. It only shows the equilibrium is exact, not that it is stable |
| B3 flat OC3 2000 s | Predicted growth at +0.0198 1/s **refuted**: deviation stays at 1e-13 |
| OC3 B2 at dt/2 | Growth rate 0.447 vs 0.451 (0.7 %); failure at 147.0 vs 147.5 s: confirmed |

The B3 OC3 result is not a contradiction of the linear unstable mode. An exact equilibrium has zero discrete residual, so a flat run cannot excite it. The event runs do (below).

## 4. B5′ (R3)

- Flat OC1 M0: |ΔV| 9e-12, |Δf| 6e-11 Hz, QP on the fast path in 49 920 of 49 921 calls.
- Event b8P_S2: frequency error at 200 s ≤ 5.4e-7 Hz; unit-bus voltage to the E* target within 6.5e-4 (OC1) and 4.1e-4 pu (OC2). No QP fallback. The reference-set margin is never negative (T1 observed).
- OC3 M0: the E* target has an unstable mode (+0.0198 / +0.0207 1/s, SG30 Qset). A deviation grows as exp(+0.0207 t) in the TDS (F5a). The CLF row is not constructible with K = K_nom. This is outside the T2 hypotheses, not a counter-example. Stabilizability holds; adopting an LQR K is a **pending decision** (Addendum A item 2).
- Information assumption A-INFO: B5′ uses the supervisory target ξ*(d⁺) after τ_info = 1 s. This is a stated advantage over B2 and has to be in the paper.

## 5. R4: overshoot term and M3+OS

- The refutation of OC3 M3 (DEC-057) is explained by a time-grid error of the M3 predictor, not by the plant: a dense-time evaluation of the same affine post-jump model reproduces the SG31 peak of 6.514 pu at 2.3 ms, where the dt-grid gave 6.498 (F4a).
- Calibration on 18 DESIGN/TUNE cells: eps_OS = 3.9e-4 pu (up). The dense model error is −6e-5 to −6e-4 pu in margin; the dt-grid error reaches +0.016 pu (F4b).
- M3+OS design: OC1 FEASIBLE_PREDICTED, J 1.759 (was 1.681), 12/12 DESIGN cells predicted SAFE (min +0.0133 pu). OC2 FEASIBLE_PREDICTED, identical to the DEC-055 M3 (the term is not active there; min predicted margin +0.43).

## 6. TUNE (R4, 16 TDS) and gate TUNE → TEST

**Predictions were sealed in git before the TDS** (commits a3eb63e and 24f28b5). All 16 predicted classes match the TDS classes.

| OC | Eligible cells | SAFE | INDETERMINATE | UNSAFE | G3 |
|---|---|---|---|---|---|
| OC1 | b7 S2, b20 S2, b16 S2, b24 S2, b7 S3, b16 S3, b24 S3 | 3 | 1 (b7 S3) | 3 (b20 S2, b16 S3, b24 S3) | FAIL: (i), (iii), (iv) |
| OC2 | all 8 | 8 | 0 | 0 | FAIL: (iii) only |

b20 S3 in OC1 is INADMISSIBLE_AT_EVENT (T-A) and not eligible; its TDS class is UNSAFE (−0.365 pu), as predicted.

**The three error sources, kept apart (Addendum B item 2).**
- OS predictor error: TDS minus predicted margin is between +7e-5 and +3.2e-3 pu, **never negative**. No peak was underpredicted, and the one-sided bound eps_OS = 3.9e-4 is not violated. 5 of 16 cells exceed the pre-registered two-sided tolerance 1e-3: OC1 b20 S2 (1.6e-3) and S3 (2.6e-3); OC2 b20 S2 (1.8e-3), b20 S3 (2.9e-3) and b24 S3 (3.2e-3). All are conservative over-predictions.
- D8 band U_D8 = 0.0109 pu: classifies OC1 b7 S3 (margin +0.004) as NUMERICALLY_INDETERMINATE. It is not counted as safe.
- Physical margin: OC2 minimum +0.27 pu; OC1 SAFE cells +0.076 to +0.089 pu.

**Why (iv) fails in OC1.** In the three S3 cells the unit-bus voltage is still 1.0–1.3e-3 pu from the target at 200 s. The slow mode has ρ_q ≈ 0.99999 (about 350 s time constant), and the criterion is 1e-3. These are stress cells.

**Regulation (all 16 runs).** Frequency error at 200 s ≤ 9.3e-7 Hz, nadir 59.964–59.978 Hz, settling to 0.01 Hz in 5.7–9.9 s after the event, QP fallback never used, reference margin never negative (F7).

**Gate verdict.** REJECTED. No OC passes G3 in full, so no TEST cohort exists. The verdict applies the pre-registered criteria literally. The protocol and the code hashes are unchanged since the TUNE plan (checked in the acta), and TEST is intact (184 plan, ledger, target, prediction and run records scanned, no TEST bus).

**Single OC1 cut cycle (protocol, Addendum B item 4), static part only.**
- The three eligible UNSAFE cells were added to the M3+OS design set: FEASIBLE_PREDICTED, J = 1.876, +22.6 MW redispatch.
- The static prediction at that dispatch gives the three cells SAFE (b20 S2 +0.015, b16 S3 +0.129, b24 S3 +0.134 pu). b20 S3 remains UNSAFE and not eligible.
- The TDS recheck (about 9 TDS from the reserve) was **not run**: criterion (iii) would very likely fail again for the same conservative reason, so it should wait for decision 1 below. These cells are now in-sample.

## 7. Link to the manuscript contributions

| Contribution | State after this work |
|---|---|
| K1 feasibility and saturation | Proof of necessity done. The case with ≥ 2 units at limit and a verified E* exists (OC3 b8P_S2: 7 units pinned, E4 passes) but has an unstable target |
| K2 post-event admissibility | Proved (T-A, OS). TUNE shows the sub-cycle peak is predicted to ≤ 3.2e-3 pu |
| K3 centered exact restoration | Lemma C proved. Observed: frequency within 1e-6 Hz and unit voltages within 1.3e-3 pu of the target at 200 s in 16 runs |
| K4 local stability | T2 proved conditional. Targets of OC1/OC2: all 22 computed (M0 and M3+OS) satisfy E4 and H1–H5. OC3 M0 (2 targets): H4/H5 not satisfied |
| K5 reference safety | T1 proved, unit-tested and observed in all 20 B5′ event and flat runs (min c_j ≥ 0) |
| K6 evaluated transient safety | In sample: OC1 fails at buses not in DESIGN (b20), OC2 passes all 8 cells. **Generalisation over buses is the open issue.** TEST not opened |
| K7 regulation and sharing | B5′ only so far. No comparison with B1s/B2/B4′ yet (R5b) |
| K8 HOCBF obstruction | Unchanged (E9 data) |
| K9 recoverable set | Not started (R6) |

## 8. Decisions required from the investigator

1. **Criterion (iii), predictor tolerance.** It was pre-registered as two-sided |error| ≤ 1e-3. The data show an over-prediction only (conservative; 0 of 16 under-predictions; one-sided bound met; class agreement 16/16). Options: (a) keep it literal: both OC are rejected, and no TEST; (b) amend it to the one-sided form (error ≥ −eps_floor), which is a criterion change made after seeing data and must be recorded as such, with the TEST gate rerun; (c) recalibrate. Recommendation: (b), declared openly, because the tolerance as written penalises conservatism that does not threaten the safety claim. I did not apply it.
2. **OC1 and bus generalisation.** M3+OS designed on buses {8, 23, 28, 25} does not protect bus 20 (SG33). Options: run the TDS recheck of the cut design; or accept that OC1 has no TEST cohort and report it.
3. **Criterion (iv) for S3 stress cells.** The convergence tolerance 1e-3 at 200 s is not reached by three S3 cells. Options: keep (those cells are STRESS_EXPLORATORY by rule when not promoted; here they were promoted); or evaluate convergence at a longer horizon.
4. **OC3 CLF.** Adopt an LQR auxiliary K so the CLF row exists for unstable targets? A new methodological decision.
5. If 1 is (b) and 2 is the recheck, the budget is enough (32 used; the plan lines plus the recheck sum to about 125 if all reserve is used, so some line must be trimmed or authorisation extended).

## 9. Not claimed

No regional stability, no physical invariance, no universal safety. All TDS results are IEEE-39 C2 (SG–GFM) only. The one-cycle mean of D8 and the jump validation of D8 remain open and are not used.
