# DEC-057 — Execution of the authorized DEC-056 decisions (pre-registered)

Status: registered 2026-10-29 before any DEC-057 TDS. Branch `review/dec055-architecture-b`. Authorization: investigator message "DEC-057 — Decisiones autorizadas y ejecución".

## Authorized scope

- **D7:** option (d), the centered RDC B3, provisionally. B2 stays the comparative reference.
- **D8:** local time refinement up to dt/16 on [t_e, t_e + 0.5 s], with initial conditions, event and parameters unchanged. The instantaneous Pmax criterion stays the acceptance criterion. The one-cycle mean is a complementary metric only.
- **OC3:** the initialization rule (i), using DESIGN data only. Formulation unchanged and S3 kept. Dynamic feasibility must be verified by TDS before M3 is approved.
- **OC3 instability:** a focused, early L4-type study of the mechanism of the 1.27 Hz oscillation. T-B is not approved by it.
- **Git:** push of reviewed commits to `rdc/review/dec055-architecture-b` only.

## Frozen elements (not changed)

- Plant, case files, topology, B2 law and gains, B3 definition of DEC-039, limits, partitions, cells.
- All acceptance criteria, including the G1 voltage drift criterion (1e-3 pu in 20 s), the instantaneous Pmax criterion and τ_cut.
- The M3 formulation, its cfg and the DESIGN set (S1–S3).
- The results of DEC-050 to DEC-056.

G1 stays BLOCKED until its original criteria are met. No L2 (TUNE) or L3 (TEST) TDS is run. The DEC-057 TDS are diagnostic or in-sample (DESIGN cells) verification runs.

## Implementation notes (no model change)

- **Local refinement.** A wrapper of `TDS.callpert` shortens the pending step. The event enters in the step that ends at t_e (DEC-056 H8b), so that step must be refined. The refined interval is therefore [t_e − dt, t_e + 0.5 s]; before t_e the state is stationary (B2/B3 inactive, plant at an exact equilibrium).
  - Inside the interval, h = dt/k and `ctx["h"]` (the step used by the RDC forward update) is set to the same value. Outside it, h = dt.
  - Every switching time is a multiple of dt, and dt/k is dyadic, so the event time, the RDC activation time and the coarse grid after t_e + 0.5 s are exact.
- **Controller B3.** `run_b3_ieee39.run("B3", ...)` with `ref = None`: the offset is v_RDC at the pre-event equilibrium (DEC-039). At a given state the closed-loop Jacobian of B3 equals that of B2, because the offset is constant.
- **Diagnostics recorded without effect on the dynamics:**
  - full-state snapshots (x, y) at declared times;
  - the log of discrete-limiter flag changes (zu, zl, zi of every discrete block, read before each step);
  - the end state;
  - storage thinning (`save_every`, `log_every`) for the 2000 s run only.
- **Regression:** the snapshot run must reproduce D56T014 bit for bit up to its end.

## D8 — local refinement (lot D8, 22 TDS, tf = 20 s)

**Cases:** the three M3 runs of DEC-054 whose stored Pmax margin is below 0.02 pu within 50 ms of the event. All are OC1, frozen DEC-054 M3 dispatch, PFlow tol 1e-6:
- P3B2_b7P_M3 (reference, +0.0045);
- P3B2_b8P_M3 (+0.0104);
- P3-C_bus12P_M3 (+0.0103).

**Runs:**
- Reference: local trapezoid and local backward Euler at k = 16. This validates the implementation against the uniform DEC-056 dt/16 runs.
- b8 and bus12:
  - trapezoid at k = 1 (uniform), which is also the regression against the stored run;
  - trapezoid at k = 2, 4, 8, 16 (local);
  - backward Euler at k = 1 (uniform) and 2, 4, 8, 16 (local).

**Rules:**
- **Implementation check (rule D8-1):** the local k = 16 run and the uniform dt/16 run agree to ≤ 1e-9 pu in P on [t_e, t_e + 0.5 s].
- **Convergence (rule D8-2):** the DEC-056 rule is used unchanged. A quantity converges if the last three levels have monotone differences with p in [0.7, 2.5]. A limit is accepted only if the trapezoid and backward Euler limits agree within their uncertainties.
- **Classification (rule D8-3):** the instantaneous Pmax margin m16 at k = 16 (trapezoid) is classified per case:
  - With an accepted limit L: U = |m16 − L| + U_finest. The case is SAFE if m16 − U ≥ 0, UNSAFE if m16 + U < 0, and NUMERICALLY_INDETERMINATE otherwise.
  - Without an accepted limit: NUMERICALLY_INDETERMINATE.
- **Derived uncertainty (rule D8-4, used by lot M3V):**
  - U_D8 = max over the three cases of (|m16 − L| + U_finest) where a limit is accepted.
  - Otherwise U_D8 = max over the cases of |m16,TR − m16,BE| + |m16,TR − m8,TR|. This is an empirical method-and-step spread, declared as such.
- **Complementary metric:** the one-cycle (4·dt) moving-average margin is reported, never used for classification.

## D7 — centered RDC B3 (static + lot D7, 6 TDS)

**Static checks (0 TDS).** At ξ(z) for OC1–OC3 M0, OC1/OC2 M3 (DEC-055) and OC3 M3 (DEC-056 seeded), the B3 equilibrium is "realizable" if all of the following hold:
- (R1) plant residuals |f|, |g| ≤ 1e-10;
- (R2) B3 rates ≤ 1e-10 pu/s;
- (R3) actuator signals at their pre-event values, with SG z inside the clamp;
- (R4) references in the interior of W_i (g_P, g_Q > 0);
- (R5) no discrete limiter flag active;
- (R6) unit P/Q/S and bus V inside the case limits;
- (R7) the closed-loop Jacobian is Hurwitz modulo the angle null mode.

R1–R6 make it an equilibrium. R7 makes it linearly stable, and only that pair of results is called "equilibrium reached and stable".

**TDS:**
- B3 flat runs OC1/OC2/OC3 M0 with the G1 settings (activation at 5 s, 200 s).
- B3 flat OC3 M0, 2000 s, storage thinned 1/16.
  - Pre-registered prediction: if R7 fails in OC3 (eigenvalue +0.0198 s⁻¹), the deviation from ξ(z) grows from round-off and exceeds 1e-3 pu before 2000 s.
  - If it does not, the linear prediction is refuted for that horizon.
- B3 on the reference event P3B2_b7P_M3 (OC1) at dt and dt/2: comparison with the stored B2 runs, and the AC-04 step check of G1.

**Decision rule (D7):**
- D7 is RESOLVED in an OC only if R1–R7 hold and the flat TDS meets the frozen G1 drift criterion.
- If R7 fails, D7 is NOT_RESOLVED in that OC, whatever the drift.
- B3 reducing the drift without R1–R7 is NOT_RESOLVED.

## OC3 instability (lot INS, 2 TDS + static)

**Hypotheses:**
- **H9a (switch):** a discrete limiter changes state at the onset (about 305–318 s) and makes the 1.25 Hz mode unstable.
- **H9b (smooth crossing):** with no flag change, the frozen-time linearisation along the trajectory has a complex pair near 1.25 Hz whose real part crosses zero continuously before the onset.
- **H9c (numerical):** the growth is an integration artifact.

**Runs:**
- (i) The D56T012 configuration (OC3 M0, B2 active from t = 0, flat, trapezoid dt) to 330 s. It records snapshots at 200, 250, 280, 290 s, every second from 295 to 325 s, and at 330 s, plus the full flag-change log.
- (ii) The same at dt/2 to 345 s or the failure, with the flag log.

**Rules:**
- H9c is rejected if (ii) reproduces the onset time within ±5 s and the growth rate within ±15 %.
- H9a is supported only if a flag change occurs within the onset interval AND the frozen-time spectrum changes from stable to unstable across that change.
- H9b is supported only if no flag changes in the interval AND the spectrum crosses continuously.
- "Hopf bifurcation" is not claimed. A Hopf claim would need the transversality and first-Lyapunov-coefficient conditions at a true equilibrium, which this study does not establish.

**Static analysis:**
- eigenvalues, participation factors and dominant states of the critical mode at each snapshot;
- the limiter flags and the margins of the limiter involved;
- first-order eigenvalue sensitivity of the critical mode to the B2 gains and the actuator gains, computed in the linearisation only, with no parameter changed in any TDS.

## OC3 M3 validation (lot M3V, 26 TDS + static)

**Seed rule (i), reproducible, DESIGN data only (0 TDS):**
1. From the OC3 M0 point, run the DEC-056 phase-1b minimum-norm sequential LP on the M2 (jump) rows of the 12 DESIGN scenarios.
   - Settings: τ = 0.002 pu, objective scales p 0.5 / v 0.05 (the cost scales), FD h = 1e-4, backtracking on initialisation validity.
   - It must be deterministic: re-executed, it must reproduce the stored point to ≤ 1e-9.
2. At that point, compute the rightmost eigenvalue of every DESIGN post-jump closed-loop linearisation.
   - If any has Re > 1e-9, take the reference state with the largest participation in the rightmost mode.
   - Lower the voltage set-point v0 of the unit that owns that state by r_tr_v0_pu = 0.01 pu, the cfg trust radius for v0.
   - Repeat while any Re > 1e-9, to at most 5 steps, and only while v0 stays inside [z_lo, z_hi] and the base and jump constraints stay satisfied.
3. The result is the seed. It must equal the DEC-056 seed. Every change must be a change of an M3 decision variable inside its bounds.

**Reporting categories (kept separate):**
- (a) predictive feasibility: Algorithm 1 status, exact margins;
- (b) dynamic safety: TDS of the 12 DESIGN cells;
- (c) stability: pre-event closed-loop spectrum at ξ(z_M3) and frozen-time spectrum at the TDS end state;
- (d) optimality: KKT;
- (e) redispatch cost: J and MW versus M0.

**TDS:**
- the 12 DESIGN cells (buses 8, 23, 28, 25 × S1–S3) at the OC3 M3 dispatch, with the protocol controller B2 and, separately, with B3;
- local trapezoid refinement k = 16 on [t_e − dt, t_e + 0.5 s], 200 s;
- flat runs at the M3 dispatch with B2 and B3.

These are in-sample (DESIGN) runs. They are not TUNE or TEST evidence and do not open L2.

**Classification per cell (rule M3V-1):**
- Instantaneous Pmax margin m with U_D8 (rule D8-4): SAFE if m ≥ U_D8, UNSAFE if m ≤ −U_D8, NUMERICALLY_INDETERMINATE otherwise.
- Q, S and V are classified on the stored samples. A Q/S/V violation is UNSAFE.

**Approval rule (M3V-2):**
- M3 in OC3 is DYNAMICALLY_VERIFIED_IN_SAMPLE only if all 12 B2 cells are SAFE.
- One UNSAFE cell gives M3_DYNAMIC_FEASIBILITY_REFUTED (in sample).
- Any NUMERICALLY_INDETERMINATE cell, with no UNSAFE cell, gives NOT_VERIFIED.
- The B3 cells are reported as comparison.

## Budget

| Lot | TDS |
|---|---|
| D8 | 22 |
| D7 | 6 |
| INS | 2 |
| M3V | 26 |
| RES (reserve, logged justification) | 4 |
| **Total** | **60** |

A plan file is sealed (written exclusively and committed) before the TDS of each lot. No retry is run without a ledger entry.
