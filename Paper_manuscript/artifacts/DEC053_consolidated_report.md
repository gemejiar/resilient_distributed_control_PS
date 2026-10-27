# DEC-053 — Consolidated report (methodological closure)

Branch `review/dec053-methodology-closure` from `a290e87`. Protocol: `ops/sted/DEC053_protocol.md` (SHA-256 `bb512856fc296e0d9424a94a2ca758fdb048e1c814473934e1c9b8ae64173bdb`). **New TDS: 0 executed, 0 failed (counter 0/4 before and after).** Software: Python 3.12.10, ANDES 2.0.0. Scripts: `Paper_manuscript/src/dec053_{core,evidence,h2,reserve,physical,close}.py`. Task states: A PASS · B PASS_WITH_FINDINGS · C PARTIAL · D PASS_WITH_FINDINGS · E PASS.

## 1. Verifiable results

**Evidence (A).** 51 inventoried cases/artefacts (`IEEE39_DEC053_inventory.csv`), all files present; SHA-256 recorded for the 21 files > 10 MB; 7/7 series hashes written in earlier stage JSONs match. B0/B1(P and P+Q)/B2 on C2t share case xlsx (SHA C8BFA9DA…), trapezoid dt = 2^-8 s, event times and amplitudes; pre-event unit P and bus V agree to ≤ 9e-16 (`reproducibility.json`, `pairing_consistency`).

**Controller effect, C2t dispatch (CAUSALLY_COMPARABLE: B1 P+Q vs B2, 120 s window; B0 vs B2, 40 s):**

| Indicator (P+ 58.564 MW bus 4) | B0 (40 s) | B1 P+Q (120 s) | B2 (120 s window) |
|---|---|---|---|
| nadir (Hz) | 59.96935 | 59.97193 | 59.97147 |
| max RoCoF (Hz/s) | 0.0719 | 0.0718 | 0.0720 |
| \|Δf_final\| at window end (Hz) | 2.5e-2 | 5.6e-7 | 3.4e-4 (2.9e-4 at 200 s) |
| 2 mHz settling (s) | not observed in 40 s | 23.5 | 23.0 |
| time outside 0.95–1.05 (S0, no event) | all window | 13.6 s | 110.2 s |
| unit-bus max \|V−1\| at window end (pu) | 0.059 | 0.014 | 0.023 |
| SG31 min P margin (pu) | −0.0700 | −0.0700 | −0.0699 |

B2 does not improve nadir/RoCoF (set by primaries); the tuned B1 restores frequency and the voltage band faster; no secondary controller removes the SG31 excess.

**Dispatch effect under fixed B2 (DESCRIPTIVE_ONLY; label "effect of dispatch under fixed B2"):** SG31 min margin −0.0699 (C2t) → +0.0250 (all Vsafe variants); SG35 +0.0150 → −0.0141 (Vsafe) → +0.0004 (R35) → +0.0245 (R35_040); pre-event band: 21 buses > 1.05 pu (max 1.0730) → 0.9794–1.0444, band time 96–110 s → 0. Pre-event P and V differ, so frequency/sharing differences are not purely controller or purely dispatch.

**Control vs dispatch table**

| Question | Cell(s) | Status |
|---|---|---|
| Controller effect (B1 vs B2) | C2t × {B1,B2} × {S0,P+,Q+} | CAUSALLY_COMPARABLE (two tuned designs) |
| Controller effect (B0 vs B2) | C2t × {B0,B2} × {P+,Q+}, 40 s | CAUSALLY_COMPARABLE |
| Dispatch effect (fixed B2) | {C2t, Vsafe, R35, R35_040} × B2 | DESCRIPTIVE_ONLY |
| Interaction controller × dispatch | missing cell B1 × R35_040 | NOT_EVALUABLE |
| B3 vs B2 | C2t | DESCRIPTIVE_ONLY (privileged information) |
| B2 vs B2_QV1 | R35_040 | CAUSALLY_COMPARABLE: no difference (negative result) |

**H3-R reconstruction.** R35_040 replays from identified inputs with 0.0 pu difference to the stored pre-event table. δ = 0.040 pu is investigator-selected (δ_min by bisection 0.01459, R35 0.015); weights come from a simulation of the same event.

**SG31/SG35 attribution.** SG31 benefit is exclusively dispatch (algebraic jump margin −0.0465 C2t; −0.0490 with Vsafe voltages only; +0.0522 with Vsafe dispatch only). SG31 violation in C2t is the jump at t = 5.004 s (−0.0453 at the first sample, −0.0699 worst, 5.98 s above Pmax); SG35's slow maximum is at 7.7–7.8 s. R35 adds margin to SG35 only.

**Physical audit.** Units × 39 buses: R35_040 shows no simulated violation of P, Q, S or the 0.95–1.05 pu band in S0, P+, Q+ nor in H3-1/H3-2 (min P margin 0.0245, 0.0137, 0.0230 pu; min S margin 0.89–1.0 pu). Historical C2t: SG31 P violated; 21 buses above 1.05 pu pre-event.

**Reference voltage diagnosis (DEC-050 verified):** at the relative equilibrium (Q+, R35_040) unit-bus |V−1| mean 3.2e-3, max 8.3e-3 pu; 39-bus mean 1.4e-2, max 4.1e-2 pu; |V₂₀₀₀ − V_eq| ≤ 6e-5 pu. The offset to 1 pu is a property of the equilibrium, not non-convergence.

## 2. Conditioned results
* **H3-R:** `PREVENTIVE_NUMERICALLY_SUPPORTED`, label `OFFLINE_SCENARIO_CONDITIONED_PREVENTIVE_REDISPATCH`. Predictions of SG31/SG35 exact or conservative in H3-1 (bus 4, 64.4204 MW) and H3-2 (bus 18); optimistic at SG39 (−0.0600 pu = 26 ε) and GFM32 (−0.0366 pu = 16 ε) in H3-2, non-binding. Domain: bus 4 (≤ 64.4 MW), bus 18 (58.564 MW), step, 200 s, B2 frozen; else `OUT_OF_CALIBRATION_DOMAIN`. Nominal frontier 70.278 MW inside dynamic bracket [65.8845, 73.205] MW (not exact).
* **H4-R:** `CONDITIONALLY_ESTABLISHED` / `NUMERICALLY_SUPPORTED_LOCAL_STABILITY` (DEC-052 unchanged): ROOT_NUMERICALLY_VERIFIED, computed matrix Lyapunov-certified, exact Jacobian conditional on δ_A < 2.06e-4, τ = 426.854 s, ζmin = 0.07213.

## 3. Unproven
HOCBF/CLF–HOCBF (H3/H4 original), certified invariant region, joint H3–H4 guarantee, rigorous root and Jacobian bounds, controller × dispatch interaction, prospective policy validation, universal reserve guarantee, EMT/SoC/capability-curve compliance, real-time, GFL, Q/V convergence of C2t cases within 200 s.

## 4. H1–H4

| Hyp. | Status | Limitation |
|---|---|---|
| H1 SG/GFM integration | SUPPORTED | tested variants, RMS limits |
| H2 frequency, P sharing | SUPPORTED (frequency) / PARTIALLY_SUPPORTED (P sharing: 0.9 % on C2t, ≈ 4 % on R35_040) | B2 not better than B1; independent tuning |
| H2 Q/V | PARTIALLY_SUPPORTED | ≈ 400 s time constant, 3.2e-3 pu mean offset to 1 pu; B1 faster in band recovery; Q share not equalised |
| H2 limits | SUPPORTED (nil controller effect on SG31); FAILED as a controller property | the preventive dispatch, not the controller, provides the margin |
| H3-R | NUMERICALLY_SUPPORTED | empirical predictor, in-sample weights |
| H4-R | CONDITIONALLY_ESTABLISHED | DEC-052 |

## 5. Answers to the acceptance questions
1. Comparable B1/B2 pairs: B1(P+Q)–B2 and B0–B2 on C2t, same plant/dispatch/event/solver (S0, P+, Q+), common windows 120/40 s; B1(P)–B2 descriptive; none on R35_040.
2. H2: frequency restored (2.9e-4 Hz at 200 s), P shared (0.9 %), Q/V slow with 3.2e-3 pu mean error vs 1 pu at the real equilibrium (equilibrium itself within 6e-5 pu at 2000 s); limits not secured by any controller on C2t.
3. SG31 benefit entirely dispatch; SG35 benefit from R35 transfer.
4. Calibrated on previous transients (weights, δ and excursion library from the bus-4 event), not deducible from pre-event data alone. Domain in `reserve_policy_spec.md` §4.
5. R35_040 reproduces exactly; no new rule was validated.
6. Modelled: P/Q/S (case data, post-processing), V band, references. Not: capability curves, OEL/UEL, converter current, SoC, rate limits, protections, EMT, N−1.
7. 70.278 MW predictor point vs dynamic bracket [65.8845, 73.205]; exceptions: other buses (8 predicted violators at 58.564 MW), E12 Q-step TDS failure vs ramp success.
8. New TDS: 0 (counter 0 → 0 of 4). None was indispensable: matched controller contrast already existed; no candidate policy defined.
9. 20 raw series > 10 MB are AT_RISK_LOCAL_ONLY (gitignored; folder in a OneDrive-synchronised directory, not verified as backup); hashes recorded; regenerable by the stage runners (byte identity not asserted).
10. Allowed/forbidden wording: `IEEE39_DEC053_claims_final.csv` (24 claims).
