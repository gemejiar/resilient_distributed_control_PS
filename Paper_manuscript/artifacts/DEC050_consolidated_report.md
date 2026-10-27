# DEC-050 — Complementary RDC campaign: consolidated report

Branch `review/rdc-recovery-dec050` (from `4710e76`). Plant: C2t_Vsafe_R35_040 (frozen). Controller: original B2 RDC unless stated. 12 of 12 allowed dynamic simulations used (list in
`IEEE39_DEC050_consolidation.json`). The protocol file `CAMPANA_COMPLEMENTARIA_RDC_DEC050.md` could not be located; the text of the authorization was used as the specification.

## A. Diagnosis of the Qset / voltage drift

| Item | Result |
|---|---|
| Does a closed-loop equilibrium exist? | **Yes, numerically.** In a single 2000 s run (Q+) the RDC rates fall from 4.1e-4 (199 s) to 5.2e-5 (1000 s) and 4.6e-6 pu/s (1999 s); the declared criterion (max rate < 5e-5 pu/s, Newton-predicted remaining reference displacement < 2e-3 pu, remaining unit-voltage change < 2e-3 pu) holds at 1999 s. Final tail slopes: Qset 5.2e-6 pu/s, unit voltage 1.6e-7 pu/s, frequency error 3.2e-7 Hz. |
| Newton extrapolation from the drifting state | Predictions made at 199, 500 and 1000 s approach the later state: remaining Qset displacement 0.167, 0.077, 0.022, 0.002 pu; the 199 s prediction is within 0.028 pu of the 1999 s prediction (first-order estimate, ~17 % error). |
| Slow modes vs E10 residuals | Modal slowest time constant 561 s (199 s) -> 428 s (1999 s); observed decay of the distance of Qset to the final state: 418 s. Remaining displacement at 200 s, drift x tau ~ 0.17-0.24 pu, explains the residual E10 errors; the "non-convergence" of E10 was slowness, not absence of an equilibrium. |
| Where the equilibrium sits | The Q-channel balance at the equilibrium is voltage term ~ -consensus term (1e-3 pu/s scale); the leak is <= 2.5e-4. Unit voltages end between 0.9917 and 1.0048 pu (mean error 3.2e-3, max 8.3e-3): the equilibrium has a **steady-state voltage offset set by the reactive-power consensus term**; it is larger than the 2.4e-3 mean error seen at 200 s. Qset ends up to 0.25 pu from the nominal value. |
| Slowest non-leak modes | tau 432 s and 311 s, localised on the Q references of SG31 and GFM32 (the two units with the smallest capability factor g_Q: 0.15 and 0.27 vs median 0.76); the 1000 s mode is the leak-only Pset mode of SG39. |

## B. Single correction B2_QV1 (negative by the declared criterion)

Correction: in the voltage term only, g_Q,i -> max(g_Q,i, 0.758) (median nominal factor). Prediction before running: slowest Q mode 432 s -> ~185 s.
Result against the stored B2 runs (same variant, events, 200 s):

| Scenario | Qset drift (20 s, max) new/old | Mean unit-voltage error new/old | New limit crossings | Frequency final error change |
|---|---|---|---|---|
| S0 | 0.973 | 0.883 | none | -1.0e-6 Hz |
| P+ | 0.948 | 0.823 | none | +1.7e-6 Hz |
| Q+ | 0.970 | 0.868 | none | -1.1e-6 Hz |

The criterion required a >= 30 % reduction of the maximum Qset drift in P+ and Q+: **not met** (3-5 %). The mechanism acted where intended (drift of the SG31 reference falls from -4.9e-3 to +1.0e-3 pu per 20 s in P+, GFM32 also falls),
but the maximum drift at 200 s is carried by the GFM37 and GFM36 references (7.3e-3 and 8.3e-3 pu per 20 s), whose capability factors are not small. The mean voltage error is 12-18 % lower, the convergence verdict is unchanged (Qset and voltage channels still outside tolerance), frequency and margins are unchanged.
Recorded as a negative result; no second round was made.

## C. Scientific validation

**C1 Frontiers.** (i) The static P ceiling of E12 (117 MW) is dispatch-independent (free redispatch, 1 % interior margins): it bounds any redispatch and was not comparable with the dynamic runs. With the physical limits and the RDC sharing observed in the 58.5 MW runs, the end-state ceiling is 106.6 MW (C2t dispatch) and 104.1 MW (R35_040), with SG35 binding. (ii) Dynamic step frontier of B2 on R35_040: P between **65.9 MW** (no violation) and **73.2 MW** (SG31 crosses pmax); Q: unit limits not crossed up to 104 MVAr, 0.95 pu band violated between **69.3 and 86.7 MVAr**. (iii) E12's "collapse" at 138.6 MVAr was a step-integration failure (TDS stopped at 5.2 s, residual 238): the same amplitude applied as a 5 s ramp respects all limits and the band (min voltage 0.963 pu). The failure is therefore not evidence of physical instability or of the absence of an equilibrium (the static AC equilibrium exists to ~277 MVAr).
**C2 Delays** (P+, 100 s): 0.5 s -> as nominal; 0.75 s -> completes but oscillates (frequency oscillation 0.057 Hz in the last 20 s, bus voltages 0.897-1.080 pu, 22 buses outside the band, no unit limit crossed). With E15: 0.2 s ok, 1.0 s limits crossed, 5 s TDS failure. Tolerance boundary for the band/oscillation: between 0.5 and 0.75 s.
**C3 Local stability, only at verified equilibria.** At the 2000 s state (approximate equilibrium within the stated tolerances): no unstable eigenvalue, one marginal direction (common rotor-angle shift, single null direction), minimum damping 0.073 (plant with frozen references 0.142), slowest mode 428 s; the Lyapunov equation on the stable subspace (dimension 215) has a positive definite solution with a guaranteed decay rate of only 2.4e-8 s^-1. Also admissible: the S0 equilibrium of the centered RDC (E13 numbers, same Jacobian as B2). **Withdrawn as stability claims:** E13's post-event points at 199 s (drifting states).
**C4 Preventive reserve (P+ 58.5 MW).** SG31 minimum P margin: -0.070 pu (C2t) -> +0.025 (Vsafe, R35_040); SG35: -0.014 (Vsafe) -> +0.025 (R35_040); only R35_040 crosses no limit. Dynamic P step tolerated: R35_040 >= 65.9 MW (+7.3 MW over the 58.5 MW at which C2t already fails). The static end-state ceiling is nearly unchanged (104-107 MW): the reserve acts on the transient.
**C5 Separation.** Numerical results: the 2000 s convergence, the B2_QV1 comparison, the frontiers and delay observations. Locally demonstrable: stability of the linearisation at the verified equilibria; existence of an equilibrium of the original B2 law (numerically). **Not available:** closed-loop safety guarantee, regional stability, nonlinear stability beyond Lyapunov's indirect method, real-time capability, robustness beyond the tested cases, GFL extension, convergence to 1 pu (the equilibrium itself has a voltage offset).

## Limits and disclosures

- Newton estimates are first order; the equilibrium is verified within tolerances, not to machine precision. The frozen-Jacobian linearisation eliminates algebraic/quasi-algebraic states and excludes degenerate IEEEST states (E9-A).
- The replication of the first 200 s of the long run against the stored Q+ series shows a 8.6e-5 pu Qset difference attributable to the thinned logging (0.39 s sampling) at a drift of 4e-4 pu/s.
- One accidental overwrite of the E15 artifacts by a rerun with the default (non-R35_040) variant was detected and restored from commit `4710e76` before use.
- Code touched: `run_b3_ieee39.py` (optional `log_every`), `e9h_predictor.py` (additive return keys); defaults and historical results unchanged (hashes rechecked).
