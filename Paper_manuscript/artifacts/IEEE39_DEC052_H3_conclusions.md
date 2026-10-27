# DEC-052 — H3-R conclusions (preventive reserve safety)

Static algebraic solves and post-processing of stored DEC-051 data only; zero dynamic simulations. Software as in the H4 file. Files: `IEEE39_DEC052_H3_voltage_audit.csv`, `IEEE39_DEC052_H3_reserve_audit.csv`, `IEEE39_DEC052_H3_location_scan.csv`, `IEEE39_DEC052_H3_audit.json`.

## D1/D2 — Voltage inconsistency reconciled
* **Cause.** The DEC-051 admissibility screen called `select_equilibrium_b3.load_plant`, which loads the **historical C2t** case without the Vsafe/R35 hook. Its pre-event voltages reach 1.0730 pu at bus 6 and 21 of 39 buses exceed 1.05 pu (static power flow and ANDES TDS initialisation agree exactly, difference 0.0). The H3 simulations ran **C2t_Vsafe_R35_040**, whose pre-event voltages are 0.9794–1.0444 pu (0 buses outside 0.95–1.05; again static = TDS initialisation, difference 0.0). The two problems have different initial conditions; the 1.07 pu of the screen belongs to the C2t dispatch, not to the simulated plant. The 1.0444 pu maximum of the simulations is the pre-event value at bus 6.
* **Original band restored.** For each of the 19 PQ-load buses (bus 4 and 18 candidates) the post-event state was evaluated on the simulated plant: (a) static power flow, (b) algebraic post-jump state with continuous differential states. All 19 converge and stay inside 0.95–1.05 pu: static 0.979–1.0446, post-jump 0.978–1.0443. Re-applying the DEC-051 selection rule (smallest positive predicted margin) with the **original two-sided band** on the correct plant selects **bus 18 again** (predicted margin 0.0118 pu, SG35 binding): the selection does not change. The relaxation in DEC-051 was unnecessary and did not affect the result.
* **Dynamic runs.** H3-1: bus voltages 0.9721–1.0425 pu after the event (0.9794–1.0444 before); H3-2: 0.9725–1.0434 pu after the event (0.9772–1.0444 before); 0 buses outside 0.95–1.05 over the full 200 s of both runs. The voltage requirement is met in the tested scenarios.

## D3 — Reserve inequality: term classes
`R_i ≥ ΔP_jump,i + ΔP_exc,i + ε`.

| Term | Class | Value / behaviour |
|---|---|---|
| R_i | exact (limit − pre-event power) | SG31 0.1389, SG35 0.1097 pu |
| ΔP_jump | **algebraic** (ANDES re-solve, differential states continuous); floating point, no validated enclosure; monotone and linear in amplitude on the grid 0.25–1.5 (SG31 0.0224→0.1339 pu, SG35 0.0055→0.0332 pu) | strongly **location dependent**: at 58.564 MW the SG31 jump ranges 0.0005 (bus 39) to 0.316 pu (bus 31), the SG35 jump 0.0001 to 0.117 pu (bus 23) |
| ΔP_exc fast (≤ 50 ms), slow (> 50 ms, 200 s) | **empirical**: from the bus-4 58.564 MW run, scaled linearly with amplitude | location transfer untested except by the bus-18 run |
| ε = 2.3e-3 pu | observed discrepancy of the **jump** term only | not a bound of the excursion terms, not a mathematical bound |

The inequality is therefore **not a universal guarantee**; it is a calibrated predictor for the tested class.

## D4 — Predictive accuracy for all ten units
Error = observed margin − predicted margin (negative: the prediction was optimistic).

| Run | SG31 error | SG35 error | max abs error (unit) | non-conservative units |
|---|---|---|---|---|
| H3-1, P+ 64.4204 MW, bus 4 | +4.3e-5 | +1.9e-5 | 3.3e-4 (GFM36) | SG30, SG33, GFM32, GFM37, GFM34, all ≤ 9.0e-5 pu |
| H3-2, P+ 58.564 MW, bus 18 | +8.5e-4 | +1.1e-2 | **0.0600 (SG39)** | **SG39 −0.0600 (margin 4.79 pu), GFM32 −0.0366 (margin 0.287 pu)** |

* H3-1: SG31/SG35 observed margins 0.0137/0.0160 pu equal the predictions; P, Q, S and V stay inside limits (min P margin 0.0137 pu at SG31, Q to Qmax 0.494, Q to Qmin 1.179, S 0.886 pu; buses 0.9721–1.0425 after the event). Consistent.
* H3-2: SG31/SG35 predicted 0.0768/0.0118, observed 0.0777/0.0230 pu. The prediction is conservative for SG35 because the bus-4 excursion used as empirical term (0.0630 pu) exceeds the excursion actually produced by a disturbance at bus 18 (0.0519 pu); for SG31 the used and observed excursions nearly coincide (0.0245 / 0.0237 pu). **The global accuracy is not summarised by SG31/SG35**: at SG39 and GFM32 the bus-4 empirical term was exceeded (observed excursion 0.383 vs 0.324 pu used at SG39; 0.0389 vs 0.0023 pu at GFM32), so the prediction was optimistic by 26 × ε (SG39) and 16 × ε (GFM32). Neither unit is binding (margins 4.79 and 0.287 pu) and no constraint was violated, but the inequality with ε is not an error bound.
* The new voltage audit does not change the admissibility of the bus-18 scenario (it satisfies the original band on the simulated plant).
* These two runs are independent **dynamic validations**, not mathematical certification. Eight buses (31, 23, 21, 24, 16, 7, 15, 8) are predicted to violate at 58.564 MW (analytic prediction only, not simulated).

## D5 — Status
**PREVENTIVE_NUMERICALLY_SUPPORTED** (same level as DEC-051, narrower wording). The tested scenarios respect P, Q, S and the original 0.95–1.05 pu band; the binding units SG31/SG35 were predicted conservatively or exactly in both runs; the excursion terms are empirical (one location, 200 s horizon) and were exceeded at non-binding units for another location. Not certified: no valid bound for the excursion terms and no enclosure of the algebraic jump. No claim is made that a redispatch guarantees safety for all load locations, and the original H3 (HOCBF) is not claimed.
