# DEC-056 — Resolution of the G1 blockers D7, D8 and of the OC3 M3 design failure (pre-registered)

Status: registered 2026-10-29 before any DEC-056 TDS. Branch `review/dec055-architecture-b`. Nothing is pushed or published without authorization.

## Frozen elements (not changed)

- Plant and case files (C2t, OC1/OC2/OC3).
- RDC B2 law, gains and activation rule.
- Limits, partitions and cells.
- DEC-055 acceptance criteria. The G1 voltage drift criterion stays at 1e-3 pu in 20 s.
- Results of DEC-050 to DEC-055.

No L2, L3 or L4 TDS is run under DEC-056. The DEC-056 runs are diagnostic: none is a TUNE or TEST run, and none uses a TUNE or TEST bus.

## D7 — closed-loop equilibrium (V/Q)

**Hypothesis H7:** the OPF dispatch is not an equilibrium of plant + B2. At activation, Qset = Qn makes the leak term zero. Then v_Q,i = K_IQ (K_V gQ,i (1 − V_i) − K_Q lQ,i), which vanishes only if each unit voltage cancels its Q-consensus term. The OPF imposes no such condition.

**Static work (0 TDS):**
- residuals by model and term-by-term RDC rates at xi(z);
- closed-loop eigenvalues;
- linear response from xi(z);
- self-consistent dispatch search: min ||v_Q||^2 subject to the OPF base constraints, first with v0 free and then with all 19 variables;
- closed-loop equilibrium xi*(z) by the DEC-051 Newton.

**TDS lot D7 (at most 6, sealed in a separate plan before launch):**
- (i) Pre-settling run, OC1 M0: RDC active from t = 0, no event, 600 s. It measures the time at which the 20-s drift falls below 1e-3 pu and 1e-4 pu, and gives the start point for the Newton polish of xi*(z).
- (ii) Flat runs (protocol settings, RDC activated at 5 s, 200 s) at each self-consistent dispatch found. They test whether the frozen G1 voltage criterion is met without being relaxed.
- These runs are evidence for a decision. They do not approve G1, because G1 is defined at the DEC-055 M0 dispatch.

## D8 — numerical convergence of the post-event transient

**Reference configuration (worst case of DEC-054/055):** P3B2_b7P_M3, OC1, bus 7, +0.58564 pu, the frozen DEC-054 M3 dispatch, PFlow tol 1e-6 (as stored), horizon 20 s. The existing runs at dt = 2^-8 s and dt/2 (trapezoid, tol 1e-4) are reused.

**Hypotheses:**
- H8a: the alternation of period 2h seen in the stored post-event samples is trapezoidal ringing of stiff modes. Predicted: it is absent with backward Euler (L-stable) and persists with trapezoid refinement.
- H8b: with the event applied in the step that ends at t_e, the first stored sample differs from the algebraic jump (x continuous) by O(h). Predicted: the difference extrapolates to zero as h → 0.
- H8c: the Newton tolerance of the TDS (1e-4) does not explain the step dependence. Predicted: changing tol to 1e-8 at dt moves the extrema by less than 1e-4 pu.
- H8d: the continuous-time post-event extrema of P (SG31) and the frequency and voltage extrema converge, and the trapezoid and backward Euler sequences share the same limit.

**TDS lot D8 (at most 10):**

| Integrator | Step sizes | Newton tol |
|---|---|---|
| Trapezoid | dt/4, dt/8, dt/16 | 1e-4 |
| Backward Euler | dt, dt/2, dt/4, dt/8, dt/16 | 1e-4 |
| Trapezoid | dt | 1e-8 |

All runs: tf = 20 s, same event mechanism.

**Declared decision rules:**
1. A quantity q is CONVERGED for a sequence if the last three levels give monotone differences with observed order p = log2(|q_h − q_h/2| / |q_h/2 − q_h/4|) in [0.7, 2.5].
   - Its numerical uncertainty at level h is U_h = Fs |q_h − q_h/2| / (2^p − 1) + |q_h − q_h/2|, with Fs = 1.25.
   - If the trapezoid and backward Euler limits agree within the sum of their uncertainties, the limit is accepted.
   - Otherwise q is NOT_CONVERGED and no error estimate is reported.
2. Classification of a stored-sample margin m at the protocol step:
   - SAFE if m − U ≥ 0;
   - UNSAFE if m + U < 0;
   - NUMERICALLY_INDETERMINATE otherwise.
   U is the converged |m(dt) − m(0)| of the reference case. Its extension to other cells is an assumption, declared as such.
3. Replacement of jump_vs_first_sample (proposed, not applied retroactively): the algebraic jump P+ is validated against the h → 0 limit of the simulated value at t_e from the refinement sequence, |P+ − lim P_h(t_e)| ≤ 1e-3 pu. The per-run first-sample comparison is withdrawn as an acceptance test.
   - No DEC-054/055 verdict is re-labelled.
   - Any new classification applies only to future runs, and only after the investigator approves it.

## OC3 M3

**Static work only (0 TDS):**
- diagnosis at the failed point: constraints, active set, finite-difference gradient noise for steps 1e-3 to 1e-6, conditioning, scaling, stopping rules;
- feasibility check through a phase-1 sequential LP that maximizes the minimum margin over the M3 design constraints, with exact re-evaluation;
- least-invasive solver strategies in order: seed, scaling, phase-1 start, then algorithm settings.

OC3 and S3 are kept. M0 remains a reference and never stands in for M3. No long run is started without a reduced test.

## Budget

Ledger `Paper_manuscript/artifacts/IEEE39_DEC056_tds_ledger.csv`, ids D56Txxx.

| Lot | Budget |
|---|---|
| D8 | 10 |
| D7 | 6 |
| Reserve | 2 (requires a logged justification) |
| **Total** | **18** |
