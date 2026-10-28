# DEC-054 — Consolidated report (G7)

Branch `review/dec054-prospective-preventive-dispatch`; IEEE-39 in ANDES 2.0.0, original RDC B2. TDS used: **44/48** (P3-A 8, P3-B 12, P3-C 24; 0 failures). Every number below is from stored runs (`prospective_tests.csv`, `prospective_summary.json`); wording limits are in `claims_matrix.csv`.

## 1. Result (frozen prospective cohort: buses 3, 29, 15, 12, 27, 26; +58.564 MW; 200 s)
| | M0 AC-OPF | M1 static reserve | M2 jump only | M3 jump + excursion + multi-contingency |
|---|---|---|---|---|
| P-limit violating (scenario, unit) pairs | 7 (6/6 scenarios; SG31 always) | 0 | 1 (0.0096 pu) | 0 |
| Total / max P excess (pu) | 0.255 / 0.089 | 0 | 0.0096 / 0.0096 | 0 |
| Min observed Pmax margin (pu) | −0.089 | 0.298 | −0.0096 | 0.0103 |
| Q / S / V (post-event 0.95–1.05 pu) violations | 0 | 0 | 0 | 0 |
| Design cost J (identical objective) | 1.261 | 3.321 | 1.299 | 1.478 |
| Redispatch (Σ|Δp|, MW) | 4.2 | ≈153 | 16.7 | 43.3 |
| Mean frequency nadir (Hz) | 59.9714 | 59.9716 | 59.9714 | 59.9714 |

## 2. G7 items
1. **P/Q/S, 10 units**: only P limits were violated (M0 and M2); no Q or S exceedance (`physical_compliance.csv`, RMS case limits, not capability curves).
2. **Voltages, 39 buses**: all inside [0.95, 1.05] pu post-event in all 24 runs. This depends on a 0.005 pu pre-event design margin introduced after P3-B round 1 (overshoot to 1.0522 pu without it); no voltage predictor exists.
3. **Algebraic jump and electromechanical maxima**: the jump explains most of the M0 excess (M0 → M2: 7 → 1 pairs); the remaining M2 violation is a post-jump excursion (M2 → M3: 1 → 0). Columns `jump_excess_Pmax_pu` / `later_excess_Pmax_pu` in `prospective_tests.csv`.
4. **Reserve and cost**: M3 reaches the compliance of M1 with J 55 % lower (1.478 vs 3.321) and ≈43 vs ≈153 MW redispatched. J is a displacement/pattern cost, not an economic cost. **Equal-cost contrast: NOT_MATCHED** (J differs by > 10 %); equal-compliance contrast: valid for M1 vs M3 only.
5. **Frequency, RoCoF, sharing**: indistinguishable across methods (nadir 59.9712–59.9719 Hz; mean of 39 BusFreq, not a COI). P sharing vs the executed pn(z) < 0.01.
6. **Predictor errors**: DESIGN audit within 0.006 pu optimistic side; empirical location-aware margin ε = max(1e-3, 1.5·max positive error), no coverage claim; first-sample proxy error up to 0.075 pu for GFM32 (reported, not a criterion). Q/S/V outside the model.
7. **Computation**: M0 145.6 s; M1 grid 1643 s + 599 s; M2 1279 s (523 plant evaluations, 4168 event tasks); M3 1452 s (376 evaluations, 3008 event tasks); status FEASIBLE_PREDICTED for M0, M2, M3 (SLSQP, KKT residual ≈0.065–0.07, not a certified optimum). Cuts in `cut_log.csv`.
8. **Ablations** (`ablation.csv`, `ablation_I_of_z.json`): A1 M0→M2 and A2 M2→M3 above; A5: with a stale I(z_ref) the predictor's optimistic peak error on the frozen dispatches reaches 0.155 pu (M3) / 0.377 pu (M1) versus 0.008 with the correct I(z).

## 3. Verdict
Frozen acceptance criteria met: M3 **NUMERICALLY_SUPPORTED** in this cohort (zero observed violations, lower redispatch than M1, M0 and M2 violating). It is not a NEGATIVE_FINDING. It is not a safety certificate: 6 buses, one amplitude, stored-sample classification at dt = 2^-8 s, thin 0.0103 pu margin, empirical ε.

## 4. Limitations and honesty notes
- G0 independent backup **waived by the investigator**; the preservation copy is on the same disk. Raw NPZ exist only locally (hashes published).
- Design constants (p scale, capability margin 0.01 pu, voltage margin 0.005 pu) were set from DESIGN/TUNE evidence before freezing; disclosed, not blind.
- ANDES limiter states are unobserved; limits are the case limits.
- No inferential statistics (6 clusters). No claim about H3/H4-R beyond DEC-052/053.

## 5. Files
Artifacts in `Paper_manuscript/artifacts/IEEE39_DEC054_*`; figures `Paper_manuscript/figures_main/IEEE39_DEC054_{jump_vs_slow,security_cost_pareto,prospective_comparison}.png`; code `Paper_manuscript/src/dec054_*.py`; gates `gate_status_G0_G7.md`; commands `reproduction_commands.md`; decision log `ops/sted/DEC054_decision_log.md`.
