# DEC-061 report: OC1 revision 3, criterion (iii-U), gate G-v2

Written for: the investigator who issued DEC-061. Branch `review/dec059-scientific-reorientation`. `main`, `main.tex`, ANDES, topology, limits, the B5′ controller and its parameters, OC3 and TEST are untouched. Nothing was pushed.

## 1. Verdict

**Gate G-v2 REJECTED, TEST stays sealed** (`IEEE39_DEC061_gate_TEST.json`, `REJECTED_TEST_SEALED`). Six of seven obligatory conditions pass. The one that fails is criterion (iv), unit-voltage error ≤ 1e-3 pu at 200 s, in the three S3 cells, exactly as pre-registered. No mandatory safety blocker is present.

| Condition | Result |
|---|---|
| C1 design FEASIBLE_PREDICTED with b20 S3, monitors not degraded | pass |
| C2 E* targets (d0 + 8 events) satisfy E4 and H1–H5 | pass (9/9; rightmost eigenvalue −0.00264 to −0.00284 1/s) |
| C3 G1-P, reduced form (first 5 s of the event runs) | pass (8/8) |
| C4 (i) no eligible cell UNSAFE; (ii) no TDS failure | pass |
| C5 (iii-U) one-sided, e ≥ −1e-3 pu | pass (8/8 e > 0), **post-TUNE, unvalidated** |
| C6 (iv) 1e-3 pu at 200 s | **fail** in b7 S3 (1.278e-3), b16 S3 (1.015e-3), b24 S3 (1.011e-3) |
| Historical (iii-H) two-sided | fail in b20 S2 (e = 5.2e-3) and b20 S3 (2.6e-3), both conservative; reported only |

## 2. OC1 feasibility and b20 S3 (D1, D2)

- **Analysis before the optimiser** (`IEEE39_DEC061_feasibility_scan.json`, no TDS). Lowering only the SG33 set-point raises the b20 S3 design margin from −0.226 to −0.094 at −0.15 pu and then saturates (SG31 binds). That scan is one-dimensional and is not a certificate: the full-space optimiser found a feasible point because the voltage set-points move too.
- **Design rev3** (b20 S3 mandatory; same formulation, cfg, eps, seed; 16 events): FEASIBLE_PREDICTED at the first working set, J = 2.399 (M3+OS 1.759, cut 1.876), redispatch 99.4 MW against the case (61.2, 76.8). Against the cut dispatch only SG33 moves materially (−0.227 pu to 6.127 pu); every other unit moves by at most 2e-3 pu. Jump admissibility holds in all 20 cells.
- **Pre-registered predictions and TDS** (all eight classes match):

| Cell | Predicted margin | TDS margin | Class | e = TDS − pred |
|---|---|---|---|---|
| b20 S3 | +0.0150 | **+0.0176** | SAFE (0.0067 above the band) | +2.6e-3 |
| b20 S2 | +0.1813 | +0.1865 | SAFE | +5.2e-3 |
| b16 S3, b24 S3 | +0.1411, +0.1424 | +0.1412, +0.1425 | SAFE | +1.4e-4, +1.3e-4 |
| b7 S2, b16 S2, b24 S2 | +0.0756, +0.1674, +0.1682 | +0.0758, +0.1675, +0.1683 | SAFE | ≤ 1.4e-4 |
| b7 S3 | +0.0037 | +0.0040 | NUMERICALLY_INDETERMINATE (not counted safe) | +2.7e-4 |

b20 S3 is no longer a violation, and no other cell was degraded to buy it (the largest change in the other cells' predicted margin versus the cut dispatch is +0.012). The b20 S3 margin is thin and is classified only against the 0.0109 band; it is evidence at the declared numerical resolution, not a physical-safety claim.

## 3. Criterion (iii-U) (D3)

Document: `IEEE39_DEC061_criterion_iii.md`. Sign convention e = m_TDS − m̂ (e > 0 pessimistic). Proposition U: if m̂ ≥ U_D8 and e ≥ −δ (δ = 1e-3), then m_TDS ≥ U_D8 − δ > −U_D8, so a cell cannot be UNSAFE. Hypotheses: P-step events, OC1/OC2, first 50 ms, dense post-jump model at the dispatch under test, solver configuration of DEC-059. Uncertainty: the TDS reference carries U_D8 (11 times δ), so the criterion compares predictor and TDS under the same scheme only. Status: **post-TUNE, proposed, not validated**. The sign pattern (all e ≥ 0 in 16 TUNE, 8 recheck, 8 rev3 and 18 calibration cells) is what motivated the rule. The only valid test is the blind TEST; the falsifier is one TEST cell with e < −1e-3. The two-sided (iii-H) stays as the historical metric in every table.

## 4. Criterion (iv) and controller adjustments (D4)

Analysis `IEEE39_DEC061_settling_analysis.json` over 24 stored runs plus the 8 rev3 runs (no TDS):
- After about 9 s the QP is off (0 non-fast-path calls in the last 100 s of every run). The late dynamics is the centred RDC itself; Q-set-point rates are about 1e-3 pu/s, far below the rate bound v̄. The late decay rate of the voltage error is 2.1–2.3 times the target's slowest eigenvalue, set by the RDC gains of the reference controller.
- The CLF rate λ = 1/(2 λ_max(H_r)) is 2e-6 of 2σ_slow. The permitted parameters (v̄, α, R, ρ_s, τ_info, ε_sel) act on the first seconds and on the target selection, not on the tail, so **no permitted adjustment can change the 200-s error by the 1%–28% needed**. The only lever that acts on the tail is a CLF rate of order 10³–10⁴ times the T2 value, outside the hypotheses of T2 (the row would be active near the target); it was neither adopted nor tested and would need its own theorem and gate.
- The error at 200 s depends on the dispatch by less than 1e-5 (b16 S3: 1.0066e-3 at M3+OS and at the cut, 1.015e-3 at rev3), which is why H4 predicted the failure. Extrapolated times to reach 1e-3 pu: 183–243 s for the S3 cells (b20 S3 passes at 9.1e-4). This is slow convergence, not divergence and not a safety issue, but it is a diagnostic only and does not replace the criterion.

## 5. Computational cost and budget

- Design rev3: 641 s with 3 workers, 1760 event tasks and 435 plant evaluations (cut cycle: 1354 s, 3631 and 792). Scan 64 s. Targets: 9, computed 3 at a time. TDS: 8, about 25 min wall at 4 workers.
- Ledger: **49 of 120** (R2 10, R3 4, R4 18, RES 9, D61 8). Remaining: 71. Reserved for TEST and the main comparison: 54 (36 + 18). Free: 17; R5C (6), K4 (4) and R5D (2) = 12 would still fit with 5 of slack. R6 was set to 0 in the BUDGET table (secondary, cut first). A TEST for OC1 alone needs 27 (18 + 9).

## 6. Recommendation on TEST

**Do not open TEST.** C6 failed and the protocol forbids retuning after a failed gate. Nothing was adjusted afterwards. What the evidence supports today: for OC1 at the rev3 dispatch, B5′ is SAFE at the declared resolution in 7 of 8 cells and INDETERMINATE (not counted safe) in the stress cell b7 S3, with the predictor conservative in every cell, E* targets locally stable, and regulation as in DEC-059; this is TUNE-level evidence on cells that were used for design, not a verification.

The single open question is (iv) in the S3 stress cells. It is a new decision, not something I can resolve:
1. **Keep (iv) as is:** OC1 has no TEST cohort; B5′ is reported with TUNE-level evidence only.
2. **Prospective redefinition of (iv)** (for example S3 cells reported as stress with a stated horizon), declared post-TUNE and not applied to the cells that motivated it. It relaxes a criterion after seeing the failure; I recommend it only if you accept that, and then with the rev3 acta kept as REJECTED under v2.0.
3. **CLF-rate revision of B5′** with a new theorem and gate (new controller revision).
OC2 has no new design or TDS in this protocol; its DEC-059 verdict stands. A cohort for OC2 would need 8 new TDS under (iii-U), if you authorise them.

## 7. Disclosures

- The first feasibility-scan file was produced with an indexing bug (the Problem cache is keyed by scenario index) and I deleted that untracked file and regenerated it. This is the only deletion, and it was my own erroneous output, not evidence.
- The G1-P was run in reduced form (first 5 s of the event runs) because the 8-TDS cap did not cover a 20-s plant run. A full G1-P needs 1 more TDS.
- The D61 plan hashes the protocol before a one-paragraph note about the E* targets was appended in the same commit; the content that governs the gate is unchanged.
- `BUDGET` in `dec059_tds.py` was edited (R6 8 → 0, D61 8); `M3REV3` was added to `dispatch`/`dispatch_z`.

## 8. Not claimed

No regional stability, no physical invariance, no universal safety, no validation of (iii-U), no OC3 result, no TEST evidence.
