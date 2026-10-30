# DEC-062 report: independent evaluation of the frozen design (blind TEST)

Written for: the investigator who issued DEC-062, and as the evidence base for the manuscript. Branch `review/dec059-scientific-reorientation`. `main`, `main.tex`, ANDES, topology, limits, gains, historical results and the directory structure are untouched. Nothing was pushed. Every TEST result below is labelled `EVALUATION_UNDER_MODIFIED_ACCESS_RULE`.

## 1. What was done and what it means

- **Preserved verdicts.** G-v2 (DEC-061) stays REJECTED, with criterion (iv) failing in OC1 rev3 b7 S3 (1.278e-3), b16 S3 (1.015e-3) and b24 S3 (1.011e-3 pu). The DEC-059 and DEC-060 verdicts stay as recorded. TEST was opened by a **post-TUNE modification of the access rule** (protocol v3.0 section 5), recorded in `IEEE39_DEC062_gate_TEST_access.json` before any TEST file existed. It is not a retroactive approval and not full compliance with the original protocol.
- **Frozen design (tag `dec062-freeze`).** B5′ and its parameters, M3+OS (OC1 rev3, OC2 M3+OS), predictor, classification rule M3V-1, eligibility rule, solver, comparators. Nothing was changed after the freeze; the analysis scripts for the matrix, figures and hypotheses (`dec062_hyp.py`, `dec062_figs.py`) were added after the TEST runs and only evaluate statements registered before them.
- **Pre-TEST validation (9 TDS), all pass:** G1-P of OC1 rev3 at 20 s; the two repeats are bit-identical to the TUNE runs; the six OC2 fresh-bus cells (buses 3, 4, 12 × S2, S3) have E* targets satisfying E4 and H1–H5, no QP fallback, min c_j ≥ 0, no false SAFE, and the Lyapunov value decays.
- **TEST (54 TDS).** Cohort A: 36 blind B5′ runs (OC1, OC2 × buses 21, 31, 39 × S1–S3 × M0 and M3+OS). Cohort B: 18 comparison runs (S2 cells, B2, B1s, B4′ at the M3+OS dispatch). Predictions, hypotheses and falsifiers were committed in f42fb9a before the first TEST TDS. **Ledger: 112 of 120**, 8 unspent.

## 2. Results of the blind TEST (cohort A, 36 cells)

| OC / dispatch | SAFE | INDET | UNSAFE | Predicted = observed | Notes |
|---|---|---|---|---|---|
| OC1 M0 | 1 | 1 | 7 | 7 of 9 | 5 cells inadmissible at the jump; **2 false SAFE** (b39 S2, S3: Pmax after 50 ms −0.0156 and −0.0451) |
| OC1 M3+OS rev3 | 7 | 0 | 2 | 9 of 9 | both UNSAFE cells (b31 S2, S3) are inadmissible at the jump (T-A) |
| OC2 M0 | 9 | 0 | 0 | 9 of 9 | |
| OC2 M3+OS | 9 | 0 | 0 | 9 of 9 | dispatch differs from M0 by 0.06 MW in total: the two OC2 arms are near-duplicates |

**Cell classes by the pre-registered scheme.** SAFE: 26. UNSAFE and predicted: 7 (all with a_j < 0, i.e. OUTSIDE_ASSUMPTIONS by N2). UNSAFE and not predicted: 2 (OC1 M0 b39 S2, S3). INDETERMINATE: 1 (OC1 M0 b21 S1). TDS failures: 0.

**Interpretation, with its limits.**
- The sub-cycle predictor is accurate: e = m_TDS − m_pred is in [−4.0e-5, +1.84e-3] pu over the 36 cells. It is not always conservative (9 cells with e between −4.0e-5 and 0), so the pre-registered "e ≥ 0" is false, while the (iii-U) falsifier (e < −1e-3) did not occur.
- The two false SAFE are at OC1 M0, the dispatch **without** preventive redispatch. They are caused by a Pmax violation after 50 ms (first-swing peak), outside the window of the dense model. At the M3+OS dispatch of the same cells, b39 S2 and S3 are SAFE (+0.2126, +0.2090 in the first 50 ms; +0.157, +0.126 after). The finding refutes "class predicted by the 50-ms model equals the TDS class" as a general statement; it does not show a violation at the M3+OS dispatch.
- OC1 rev3 b31 S2 is eligible by the S2 rule but inadmissible at the jump (a_j = −0.099), so it is outside the safety claim for every controller of the rate-bounded class, as T-A states, and indeed all four controllers fail there. The preventive dispatch designed on buses 8, 23, 28, 25 and tuned on 7, 20, 16, 24 does not make bus 31 recoverable: this is a limit of the design, not of the controller.
- OC2 is SAFE everywhere with a large margin (min +0.209) at both dispatches; it shows B5′ performance in a case with headroom, not the value of the redispatch.

## 3. Criteria, reported separately (G3 (i)–(iv) and alternatives)

| OC / dispatch | (i) no eligible UNSAFE | (ii) no TDS failure | (iii-H) two-sided | (iii-U) one-sided | (iv) 1e-3 pu at 200 s |
|---|---|---|---|---|---|
| OC1 M0 | fail (5 eligible cells, 3 inadmissible) | pass | pass | pass | pass |
| OC1 M3+OS rev3 | fail (b31 S2, inadmissible) | pass | pass | pass | pass (b21 S3 0.951, b39 S3 0.899 mpu: narrow) |
| OC2 M0 | pass | pass | **fail** (b21 S2, e = 1.84e-3) | pass | pass |
| OC2 M3+OS | pass | pass | **fail** (b21 S2, e = 1.84e-3) | pass | pass |

Neither the original G3 nor G-v2 is declared met. (iii-U) holds in 42 of 42 prospective cells (36 TEST + 6 fresh-bus OC2): this is the first evidence on cells that did not motivate the rule, still limited to one event kind and the first 50 ms. Settling is complementary information: frequency to 0.01 Hz in 5.7–6.9 s for B5′ and 7.6–7.7 s for B2 and B1s; unit-bus voltage within 1e-3 pu of its final value in 9–37 s for B5′ (B2 175 s, B1s 12–28 s).

## 4. Contributions evaluated on TEST

**T1 (reference invariance).** min_j c_j ≥ 0 and no QP fallback in 42 of 42 runs (B5′ 36, B4′ 6); the minimum is 0.024 pu. T1 concerns references only and nothing is inferred for delivered P, Q, V (e.g. the nine UNSAFE cells have c_j ≥ 0). Figure F10a.

**T2 (local stability).** 42 of 42 TEST targets satisfy E4 and H1–H5; the Lyapunov value ends at most 4.2e-4 of its first valid value in the 36 B5′ runs. The statement is local and its domain is not quantified. Figure F10b.

**P3 (classification).** N2: the 7 cells predicted inadmissible at the jump are all non-SAFE in TDS, and the three b31 S2 comparison cells are non-SAFE for B2, B1s and B4′ too; 0 counter-examples. V is the E* verification above; O is the observed class. Figures F8, F11.

**Controller effect and dispatch effect (cohort B, six S2 cells).**
- The first-50-ms margin is the same for B5′, B4′, B2 and B1s within 5.8e-5 pu: Proposition OS holds on TEST.
- B5′ and B4′ are nearly identical in every metric: the CLF row has no measurable effect in these events.
- B2 leaves a unit-voltage offset of 36.5–37.3 mpu and a 2.4e-4 Hz frequency error at 200 s (B5′ and B1s: 0.13–0.62 mpu and 0.05–0.13 mpu; ≤ 4e-7 Hz and 1e-7 Hz).
- B5′ has the best frequency nadir (59.9759–59.9783 Hz vs 59.9717–59.9730) and the best sharing (std ≤ 5.6e-6 vs 3.5e-5–2.7e-4). B1s has the lowest control effort (P total variation 0.60 vs 1.64–1.76 for B5′ and 2.14–2.74 for B2) and the smallest voltage offset. There is no dominant controller.
- B5′ uses the supervisory target after τ_info = 1 s (A-INFO), which B2 and B1s do not have. The comparison is under equal events, dispatch and solver, not under equal information.
- The dispatch effect is read from B5′ at M0 vs M3+OS: large in OC1 (101 MW redispatch turns b21 S2 and b39 S2, S3 from UNSAFE to SAFE; it cannot fix b31 S2, S3), null in OC2. It is not measured for B2, B1s or B4′ (no M0 arms).
- Figures F9 (a)–(d).

## 5. Pre-registered hypotheses (Addendum A)

| Hypothesis | Result |
|---|---|
| HA1 classes equal predictions | **Falsified** (34 of 36; 2 false SAFE at OC1 M0) |
| HA2 e ≥ 0, and (iii-U) | e ≥ 0 **falsified** (9 cells, min −4.0e-5); (iii-U) not falsified |
| HA3 T1, no fallback | holds |
| HA4 T2 targets and V decay | holds |
| HA5 inadmissible never SAFE | holds |
| HA6 OC2 dispatch effect null | holds (max |Δm50| 7.5e-5) |
| HA7 OC1 S3 cells fail (iv) | **Falsified**, favourably (0.951 and 0.899 mpu pass) |
| HB1 controller independence of the 50-ms margin | holds (max 5.8e-5) |
| HB2 B5′ vs B4′ frequency | holds (max 6.2e-10 Hz) |

## 6. Contribution matrix

`IEEE39_DEC062_contribution_status.csv`. Summary: **demonstrated:** T1, T2 (conditional, local), K8. **Validated within their domain:** P3 (N2), K2 (T-A and Proposition OS), K3 (centered restoration). **Partially supported:** K1, K6 (preventive dispatch: OC1 admissible cells yes, bus 31 no; false SAFE at M0), K7 (no dominance), (iii-U). **Refuted (as pre-registered):** HA1, strict HA2, HA7.

## 7. What can be claimed and what cannot

- Claimable: T1 as invariance of the reference set; T2 as local stability of the sampled loop at verified targets; P3 as a classification whose N2 prediction has no counter-example on TEST; sub-cycle predictor accuracy of about 2e-3 pu in the first 50 ms; centered restoration at the declared information assumption; a descriptive comparison without dominance.
- Not claimable: physical invariance (T1 does not imply safe P, Q, V); regional stability (T2 is local); general safety from 90 TDS; OC3 (documented limit: unstable target); that the preventive redispatch protects every bus (bus 31 in OC1 is a counter-example); validation of (iii-U) beyond the cells tested.
- Limits: IEEE-39 C2 (SG–GFM) only; P-step events; one dispatch design per OC; numerical band U_D8 = 0.0109 pu.

## 8. Disclosures

- The TEST access rule was changed after TUNE (protocol v3.0 section 5). The OC1 dispatch used is rev3, not the original M3+OS of DEC-059.
- The first TEST file creation (targets, predictions, plans) followed the freeze; the TEST intactness scan passed before it.
- `dec059_pred.py` now lists S1, S2, S3 for the `test` set (before: S1, S2) and accepts the `val` set; `BUDGET` was changed (R5 54, K4 0, R6 0, D61 8, D62V 9).
- Buses 3 and 12 (used for OC2 validation) were observed in the older DEC-054 campaign, which does not touch this design or criterion.
- A B4′ run has no Lyapunov value by construction, so the T2 decay check applies to the 36 B5′ runs only.
- 8 TDS of the 120 cap remain unspent; no secondary studies (OC3, R5C, R5D, K4, R6) were run.
