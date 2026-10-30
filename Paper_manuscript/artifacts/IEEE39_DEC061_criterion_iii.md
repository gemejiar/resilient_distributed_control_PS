# DEC-061 D3: one-sided conservative predictor criterion (iii-U)

Status: **proposed after TUNE, prospective, not validated.** The two-sided criterion (iii-H) |e| ≤ 1e-3 pu stays as the historical metric and is reported in every table. Nothing here changes a verdict already issued (DEC-059 gate, DEC-060 gate).

## 1. Objects

- Margin of the active-power limit inside the sub-cycle window: m_c = min over units i and t ∈ [t_e, t_e + 50 ms] of (Pmax_i − P_i(t)), for a cell c (bus, severity).
- Prediction m̂_c: the dense post-jump affine model of the M3+OS design at the dispatch under test, **without** the design allowances (eps_J, eps_E, eps_OS, U_D8). It is computed before any TDS of the cell.
- Reference m_c^TDS: the locally refined (dt/16, [t_e − dt, t_e + 0.5 s]) trapezoid run, `reset_tiny = 0`, tolerance 1e-4.
- Signed error e_c = m_c^TDS − m̂_c. **Sign:** e_c > 0 means the prediction is pessimistic (the simulated peak is lower than predicted); e_c < 0 is optimistic.

## 2. Criterion

(iii-U) For every cell of the verification set: e_c ≥ −δ, with δ = 1e-3 pu (the floor already declared in the protocol as eps_floor; it is not tuned to the new data).

Over-prediction is not penalised by (iii-U). It is reported through e_c and through the redispatch cost J, so over-conservatism stays visible.

## 3. Statements and proof

**Proposition U.** Let U_D8 = 0.0109 pu be the numerical band of the classification (a cell is SAFE if m^TDS ≥ U_D8, UNSAFE if m^TDS ≤ −U_D8, otherwise NUMERICALLY_INDETERMINATE). If m̂_c ≥ U_D8 and (iii-U) holds at c, then m_c^TDS ≥ U_D8 − δ = 0.0099 > −U_D8. Hence the cell cannot be UNSAFE; the worst case is NUMERICALLY_INDETERMINATE.

*Proof.* m^TDS = m̂ + e ≥ U_D8 − δ, and U_D8 − δ > 0 > −U_D8 because δ < U_D8. ∎

**Consequences and limits.**
1. No false SAFE of the UNSAFE kind can pass (iii-U). A cell predicted SAFE and simulated INDETERMINATE can pass, and it is then not counted as safe by the classification.
2. Uncertainty. The reference m^TDS carries the numerical uncertainty U_D8, which is 11 times δ. (iii-U) therefore compares the predictor with the same numerical scheme, not with the continuous plant; the claim stays "evaluated by TDS at declared resolution", never "physically safe".
3. Hypotheses for the domain of validity:
   - (H-U1) P-step events on the partition buses, amplitudes up to S3, OC1 and OC2 plants, dispatches from M3+OS designs;
   - (H-U2) the first 50 ms after the event only; Q, S, V margins and margins after 50 ms are classified on stored samples and are outside (iii-U);
   - (H-U3) the post-jump affine model of the dispatch under test is the predictor (the sub-cycle window is controller independent in the rate-bounded class, Proposition OS);
   - (H-U4) solver configuration as in DEC-059 DE (trapezoid, dt = 2⁻⁸, local dt/16, `reset_tiny = 0`).
   Outside this domain (OC3, other event kinds, other solvers) the criterion makes no statement.
4. The criterion holds for the minimum over units; it does not bound per-unit optimism of the peaks (the calibrated per-unit optimism reaches 3.9e-4 pu, which is why eps_OS enters the design margin).

## 4. Evidence status

- The sign pattern (all e_c ≥ 0 in 16 TUNE cells, 8 recheck cells and 18 calibration cells) is the observation that motivated the rule. It is **not** a validation of (iii-U).
- Validation can only come from cells that were not used to motivate or design with it. Within the current partitions that means the blind TEST cells. The falsifier is fixed now: one TEST cell with e_c < −δ refutes (iii-U) on its domain.
- Until then (iii-U) is "proposed, post-TUNE, unvalidated" in every document.
