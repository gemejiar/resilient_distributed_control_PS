# DEC-057 — Execution of the authorized DEC-056 decisions: D8 local refinement, D7 centered RDC B3, OC3 instability mechanism, OC3 M3 validation

**Authorization:** investigator message "DEC-057 — Decisiones autorizadas y ejecución" (2026-10-29).
**Pre-registered protocol:** `ops/sted/DEC057_protocol.md`. Every lot plan (`IEEE39_DEC057_{RES1,RES2,D8,D7,INS,RES3,RES4,M3V}_plan.json`) was committed before its TDS. Ledger: `IEEE39_DEC057_tds_ledger.csv`.
**TDS used:** 60 of 60.

| Lot | TDS | Notes |
|---|---|---|
| D8 | 22 | |
| D7 | 6 | |
| INS | 2 | |
| M3V | 26 | |
| RES | 4 | 2 smoke tests, of which one failed on a wrapper defect fixed before any lot; 2 discriminating runs |

**Not changed:** plant, cases, topology, B2 law and gains, B3 definition (DEC-039), limits, partitions, acceptance criteria, the M3 formulation and cfg, S3, the results of DEC-050 to DEC-056, `main`.

**Not executed:** L2 and L3.

**G1 status:** still BLOCKED (section 6).

**Evidence labels:**
- **DEMONSTRATED** — exact statement about the implemented model or code.
- **VERIFIED** — numerical result with a tolerance and an independent check.
- **OBSERVED** — numerical observation without a convergence or uniqueness guarantee.
- **OPEN** — not established.
- **PREDICTIVE** — a static design-model result, never TDS evidence.

---

## 0. Integrity before any work (VERIFIED)

**G0 freeze hashes:** 56 of 58 match. The two that differ, `dec055_common.py` and `test_dec055.py`, carry the D9 correction of `jump_vs_first_sample`, documented in DEC-055 L1 (commit cbb70cc). There are no other changes.

**Push of the DEC-056 commits:** the decision log and traceability matrix were append-only, no file exceeded 136 kB, and neither `main` nor `main.tex` was touched. The four reviewed DEC-056 commits were then pushed to `rdc/review/dec055-architecture-b` (e79364f → 68cb717). `rdc/main` = 1a023d8 is unchanged.

---

## 1. D8 — local refinement up to dt/16 on [t_e − dt, t_e + 0.5 s]

### 1.1 Implementation (DEMONSTRATED / VERIFIED)

**Mechanism.** A wrapper of `TDS.callpert` shortens the pending step to dt/k and sets the RDC update step `ctx["h"]` to the same value. The event enters in the step that ends at t_e, so the refined interval starts at t_e − dt; the pre-event state is stationary.

**Smoke test (D57T002).** On the produced grid:
- h is exactly dt/16 on [4.99609375, 5.5];
- the event falls at 5.0;
- h is dt afterwards.

Snapshots, the flag log and the end state work.

**Rule D8-1.**
- Local k = 16 versus the uniform DEC-056 dt/16 runs on [t_e, t_e + 0.5 s]: max |ΔP| = 6.1e-13 (trapezoid) and 1.4e-13 (backward Euler), on the same grid. **PASS** (threshold 1e-9).
- After the window the step returns to dt. This changes the slow quantities by at most 3.6e-5 Hz (f_COI nadir, backward Euler).

**Regression.** The new uniform trapezoid runs of b8 and bus12 are bit-identical to the stored DEC-054 runs (t, P, Q, V).

### 1.2 Cases and convergence (rule D8-2, unchanged from DEC-056)

The three DEC-054 M3 runs whose stored Pmax margin was below 0.02 pu within 50 ms of the event (OC1, frozen DEC-054 M3 dispatch):

| Case | Integrator | k = 1 | 2 | 4 | 8 | 16 | Verdict |
|---|---|---|---|---|---|---|---|
| P3B2_b7P_M3 (bus 7) | trapezoid | +0.0045 | −0.0004 | −0.0067 | −0.0084 | −0.0094 | CONVERGED, p = 0.84, limit −0.0107 |
| | backward Euler | +0.0119 | +0.0083 | +0.0049 | +0.0015 | −0.0023 | NOT_CONVERGED |
| P3B2_b8P_M3 (bus 8) | trapezoid | +0.0104 | +0.0058 | −0.0003 | −0.0022 | −0.0030 | CONVERGED, p = 1.12, limit −0.0038 |
| | backward Euler | +0.0177 | +0.0142 | +0.0108 | +0.0075 | +0.0039 | NOT_CONVERGED |
| P3-C_bus12P_M3 (bus 12) | trapezoid | +0.0103 | +0.0056 | −0.0022 | −0.0040 | −0.0053 | NOT_CONVERGED |
| | backward Euler | +0.0221 | +0.0172 | +0.0134 | +0.0092 | +0.0043 | NOT_CONVERGED |

- Values are the minimum instantaneous Pmax margin after the event (pu); the critical unit is SG31 in every case. Levels are h = dt/k on [t_e − dt, t_e + 0.5 s].
- The peak occurs 2–4 ms after the event at every level.
- Backward Euler decreases by about 0.0035 pu per halving without asymptotic behaviour in all three cases.
- At dt/16 the two methods disagree in sign for b8 and bus12.
- Slow quantities converge with both methods: f_COI nadir, V_min, P at 1 s, f_COI at 5 s.

### 1.3 Classification (rule D8-3, instantaneous Pmax criterion kept)

**All three cases are NUMERICALLY_INDETERMINATE**, because no case has an accepted limit (backward Euler is not converged).

| Case | Trapezoid dt/16 | BE dt/16 | Class |
|---|---|---|---|
| b7 | −0.0094 | −0.0023 | NUMERICALLY_INDETERMINATE |
| b8 | −0.0030 | +0.0039 | NUMERICALLY_INDETERMINATE |
| bus12 | −0.0053 | +0.0043 | NUMERICALLY_INDETERMINATE |

**Observed trend:** every trapezoid sequence and every backward-Euler sequence decreases monotonically with refinement. The DEC-054 statement "M3 without violations" for these three runs is therefore not robust under the frozen instantaneous criterion. No earlier verdict is re-labelled.

**Rule D8-4 (for lot M3V):**
- U_D8 = max over the cases of |m16,TR − m16,BE| + |m16,TR − m8,TR| = **0.0109 pu** (bus12).
- This is an empirical method-and-step spread, declared as such in the protocol.

**Complementary one-cycle mean** (not used for any classification):
- It converges with both methods to +0.0168 (b7), +0.0223 (b8) and +0.0246 (bus12).
- Definition: the trailing mean over [t − 4·dt, t] by trapezoidal quadrature on the stored grid, made explicit in `dec057_d8.py`.

**Jump validation (|P+ − lim P_BE(t_e)| ≤ 1e-3): stays OPEN.** It needs h < dt/16, which is outside the authorization.

Figures: `IEEE39_DEC057_D8_peaks.png`, `IEEE39_DEC057_D8_convergence.png`. Data: `IEEE39_DEC057_D8_convergence.json`.

---

## 2. D7 — centered RDC B3 (provisional option d)

### 2.1 Is ξ(z) a realizable equilibrium of the complete system? (rules R1–R7, static, VERIFIED)

At each dispatch:

| Dispatch | R1 \|f\|, \|g\| | R2 B3 rates | R3 actuators | R4 min g_P, g_Q | R5 limiters active | R6 case limits | R7 rightmost (1/s) |
|---|---|---|---|---|---|---|---|
| OC1 M0 | 2e-16, 2.5e-13 | 0 | 0 (clamp margin 0.1) | 0.055, 0.226 | none | PASS | −2.89e-3 ± 1.7e-4 i, **PASS** |
| OC2 M0 | 2e-16, 1.3e-13 | 0 | 0 | 1.75, 0.384 | none | PASS | −4.20e-3, **PASS** |
| OC3 M0 | 4e-16, 6.0e-14 | 0 | 0 | 0.017, 0.133 | none | PASS | **+1.98e-2, FAIL** (Qset SG30, participation 0.987) |
| OC1 M3 (DEC-055) | 5e-16, 1.1e-13 | 0 | 0 | 0.332, 0.226 | none | PASS | −2.85e-3, PASS |
| OC2 M3 (DEC-055) | 2e-16, 1.7e-13 | 0 | 0 | 1.75, 0.384 | none | PASS | −4.20e-3, PASS |
| OC3 M3 (DEC-056 seeded) | 4e-16, 8.9e-14 | 0 | 0 | 0.189, 0.148 | none | PASS | −2.35e-3, PASS |

Facts behind the table:
- **R2 (DEMONSTRATED):** the B3 rates are exactly zero, because the offset equals v_B2 at ξ(z) by construction. For comparison, B2 has |v_Q| ≈ 1e-2 pu/s at the same points.
- **R7 (DEMONSTRATED):** the closed-loop Jacobian of B3 equals that of B2, since the offset is constant.
- **The R7 numbers are VERIFIED:** an independent finite-difference Jacobian at OC3 M0, t = 0, reproduces +0.019828 to a relative 1.4e-7 (`ins_fdcheck`).

### 2.2 TDS (VERIFIED on the stored series)

**Flat runs, G1 settings, frozen G1 metrics (exactly as DEC-055 L1):**

| OC | B3: 20-s drift | B3 verdict | B2 (DEC-055 L1): 20-s drift | B2 verdict |
|---|---|---|---|---|
| OC1 | 0.0 pu | PASS | 7.5e-3 | FAIL |
| OC2 | 0.0 pu | PASS | 6.3e-3 | FAIL |
| OC3 | 0.0 pu | PASS | 8.9e-3 | FAIL |

For B3 the rolling 20-s drift over 200 s and the f_COI drift (7e-15 Hz) are also zero.

**Pre-registered R7 prediction: REFUTED as formulated.** In the B3 OC3 M0 run over 2000 s (D57T006) the state did not move at all (max |ΔV| = 0.0 exactly, so no growth). Section 3.4 explains why: the ANDES `reset_tiny` dead zone freezes an exact equilibrium. **A flat TDS from an exact equilibrium therefore cannot test its stability in this solver configuration.** The zero drifts above are consequences of exactness plus the dead zone. They are not stability evidence.

**Reference event P3B2_b7P_M3 (OC1), B3 versus B2:**

| Quantity | B3 | B2 |
|---|---|---|
| Pmax margin (pu) | +0.00448 | +0.00448 |
| f_COI nadir (Hz) | 59.97222 | 59.97220 |
| V_min (pu) | 0.97355 | 0.97355 |
| Final f_COI error, 120–200 s (Hz) | 2.3e-4 | 2.7e-4 |
| Final bus-V change from pre-event (pu) | 0.0021 | 0.0372 |

B3 does not regulate unit voltages to 1.0 pu (by construction, DEC-038/039).

**AC-04 (dt versus dt/2):** **FAIL** for B3, exactly as for B2.
- max |ΔP| = 0.041 pu, confined to the first 50 ms (0.0054 pu afterwards);
- ΔV = 2.1e-3 pu;
- nadir difference 2e-5.

The D8 issue does not depend on the controller.

### 2.3 Decision rule D7

| OC | R1–R6 | R7 | Flat G1 (B3) | D7 |
|---|---|---|---|---|
| OC1 | yes | yes | PASS | **RESOLVED** |
| OC2 | yes | yes | PASS | **RESOLVED** |
| OC3 | yes | **no** (+0.0198 s⁻¹) | PASS | **NOT_RESOLVED** |

- In OC3, B3 reaches an exact equilibrium, but that equilibrium is linearly unstable. The rule therefore applies: "R7 fails ⇒ NOT_RESOLVED, whatever the drift."
- At the OC3 M3 dispatch the B3 equilibrium is linearly stable (R7 PASS). This is not the G1 definition, which uses M0.

Figures: `IEEE39_DEC057_D7_flat.png`, `IEEE39_DEC057_D7_growth.png` (the flat 2000-s line), `IEEE39_DEC057_D7_event.png`. Data: `IEEE39_DEC057_D7_results.json`.

---

## 3. OC3 instability (focused L4-type study; T-B not approved)

Configuration: D56T012, i.e. OC3 M0, B2 active from t = 0, no event.

### 3.1 Runs

| Run | Solver change | Onset (1.25 Hz amplitude > 1e-6 after its minimum) | Growth after onset | Failure | Discrete-flag changes before onset |
|---|---|---|---|---|---|
| D56T014 (stored) | default (trapezoid dt, tol 1e-4, lazy Jacobian, reset_tiny 1) | 318 s | ≈ 0.6 1/s | 343.4 s | — |
| INS (i) D57T009 | default, with snapshots and flag log | 318 s | same | (stopped at 330 s) | 0 |
| INS (ii) D57T010 | dt/2 | 339 s | ≈ 0.7 1/s | none by 345 s | 0 |
| RES3 D57T033 | Jacobian refreshed every iteration, tol 1e-8 | 317 s | same | (330 s) | 0 |
| RES4 D57T034 | **reset_tiny = 0** (only change) | **117 s** (minimum at 60 s) | **0.45 1/s** | **147.5 s** | 0 (all 530 changes lie in the last 6 ms before the failure) |

- INS (i) is bit-identical to D56T014 up to 330 s (regression PASS).
- The onset can be read from the noise floor of about 1e-8 in the default runs and about 1e-11 in RES4.

### 3.2 Frozen-time linearisation along the trajectory (VERIFIED)

The snapshots of RES3 and INS (i) were linearised with the state, discrete flags and references exactly as in the TDS.

**Independent check.** At t = 0, 200 and 300 s a central finite-difference Jacobian of the reduced DAE + B2 (algebraic variables re-solved at every evaluation) agrees with the predictor M to a relative 1.3e-7, and gives the same eigenvalues to 7 digits.

**Critical mode:** a 1.30–1.37 Hz pair.
- Participation: rotor ω and δ of SG30 (GENROU 1) 0.61, Pset SG30 0.14, the SG30 governor lag 0.04.
- Re = −0.873 at t = 0, −0.764 at 10 s, −0.038 at 60 s, +0.093 at 70 s, +0.36 at 100 s, +0.58 at 200 s, +0.587 at 300–325 s.
- **Continuous crossing of Re = 0 at about 62.9 s.**

**Discrete versus continuous.** The explicit, one-step-delayed B2 update at h = dt, dt/2 and dt/4 shifts Re by at most 1.2e-5 1/s. It is not the cause.

**RES4 growth versus frozen-time Re:**

| t | TDS growth rate (RES4) | Frozen-time Re |
|---|---|---|
| 95 s | 0.331 | 0.329 |
| 105 s | 0.390 | 0.392 |
| 115 s | 0.438 | 0.440 |
| 125 s | 0.474 | 0.477 |

Agreement is within 1 %.

### 3.3 Mechanism (DEMONSTRATED for the linearisation; OBSERVED along the TDS)

1. The B2 frequency channel of unit i has integral gain k_ip · g_P,i / g_ref,P, with k_ip from SPEED_TARGET = 160.
2. g_P,i is the capability factor evaluated at (Pset, Qset). It grows as Qset moves away from the capability boundary.
3. As B2 regulates the voltages towards 1.0 pu, Qset of SG30 falls (by 0.68 pu at 200 s). g_P,raw of SG30 rises from 4.23 at t = 0 to 13.4 at the crossing and 19.8 at 200 s. The Pset SG30 row of the closed-loop Jacobian grows from 91 to 397.
4. **Sensitivity of the critical pair at 200 s** (linearisation only):
   - ∂Re = +0.0170 1/s per +1 % of K_P;
   - ∂Re = +0.0170 1/s per +1 % of k_ip;
   - |∂Re| < 6e-7 for K_IQ, K_V, K_Q and K_LEAK.

   The P-channel (frequency/consensus) gain is therefore the control parameter. The Q gains act only through the slow drift of Qset.
5. In short: the voltage regulation of B2 releases the Q headroom of SG30, which raises the frequency gain that B2 assigns to SG30, which destabilizes the SG30 electromechanical mode.

### 3.4 Why the default TDS showed the onset at about 318 s (DEMONSTRATED in the code; VERIFIED by RES4)

- ANDES 2.0.0 sets Newton increments with |inc| < tol_zero = tol/1e6 to zero (`reset_tiny = 1`, default). With tol = 1e-4 this is 1e-10, fixed when the TDS object is built, so RES3 kept the same threshold.
- A 1.3 Hz component of amplitude A produces per-step increments of about A·ω·h ≈ 0.03 A (at dt). Below A ≈ 1e-8 the plant part of the mode is not integrated, the loop is cut, and the mode cannot grow.
- Halving h halves the increments, which delays the onset (339 s at dt/2).
- With `reset_tiny = 0` the mode decays while Re < 0, grows from about 70 s, and the TDS fails at 147.5 s. The growth matches the frozen-time Re (table in 3.2).

### 3.5 Hypotheses

| Hypothesis | Status |
|---|---|
| H9a limiter switch | NOT SUPPORTED. No discrete flag changed before the onset in any run. |
| H9b smooth crossing (frozen-time) | SUPPORTED. Continuous crossing at about 62.9 s, FD-verified Jacobian. |
| H9c numerical origin of the growth | REJECTED for the instability itself. The pre-registered dt/2 rule (onset within ±5 s) was not met, and the onset time is indeed numerical. |
| H9e reset_tiny dead zone (added before RES4, prediction sealed) | SUPPORTED. |
| Hopf bifurcation | NOT CLAIMED. The crossing occurs along a slowly drifting non-equilibrium trajectory; no equilibrium, transversality or first Lyapunov coefficient was established. |
| T-B for OC3 M0 + B2 | NOT APPROVED. The trajectory activated from the M0 dispatch loses stability; no stable post-activation equilibrium is identified. |

**Consequence for earlier evidence (OPEN, not re-labelled).** Every TDS-based statement of the form "no growth / flat / settled" that concerns small amplitudes may be affected by the dead zone. This includes the DEC-050 2000-s run, the DEC-056 pre-settling runs and the B3 flat runs. Transient extrema after a large event are not affected, because their increments are orders of magnitude above 1e-10. Amplitudes below about 1e-8 after the decay are.

Figures: `IEEE39_DEC057_INS_onset_v2.png`, `IEEE39_DEC057_INS_mechanism_v2.png`. Data: `IEEE39_DEC057_INS_results_v2.json`.
- The v1 files of these three are superseded and kept unmodified. Their onset definition caught the B2 activation transient at 7 s.
- Static data: `DEC057_state/ins_snapshots*.json`, `ins_fdcheck.json` (local).

---

## 4. OC3 M3 validation (seed rule (i); formulation, cfg and S3 unchanged)

### 4.1 Reproducible seed algorithm (VERIFIED, DESIGN data only, 0 TDS)

1. Run the DEC-056 phase-1b minimum-norm sequential LP on the jump (M2) rows of the 12 DESIGN scenarios from the OC3 M0 point.
   - Settings: τ = 0.002, cost scales p 0.5 / v 0.05, FD h = 1e-4.
   - Re-executed in a fresh process, it reproduces the stored point **exactly** (max |Δz| = 0.0): minimum jump margin +0.00192 pu, 122.5 MW.
2. Every DESIGN post-jump linearisation has a real eigenvalue of +0.0204 to +0.0217 1/s. The reference state with the largest summed participation is **Qset SG30**. Its unit's v0 is lowered by r_tr_v0_pu = 0.01 pu, the cfg trust radius.
3. After one step, all 12 post-jump linearisations are Hurwitz modulo the null mode, and the rule stops. The result equals the DEC-056 seed (max |Δ| = 0.0).
   - Changed variable: `v0_SG30` only (1.0285 → 1.0185 pu), inside [0.95, 1.05].
   - Jump margin +0.00144 pu; base constraints −8.9e-16 (numerically 0).
   - v0 is an M3 decision variable, so the change is allowed by the problem.

### 4.2 Separate reporting categories

| Category | Result | Evidence type |
|---|---|---|
| (a) Predictive feasibility | Algorithm 1 FEASIBLE_PREDICTED; exact minimum design margin −2.4e-5 pu, inside the frozen τ_cut = 1e-4; base +4.3e-12 | PREDICTIVE |
| (b) Dynamic safety, in sample (12 DESIGN cells, B2, local dt/16, rule M3V-1 with U_D8 = 0.0109) | 8 SAFE (all S1, S2), **1 UNSAFE (b8P_S3: SG31 −0.0140 pu at 2.2 ms after the event)**, 3 NUMERICALLY_INDETERMINATE (b23P_S3 SG33 −0.0084 at 2.4 ms; b28P_S3 SG39 −0.0006 at 0.63 s; b25P_S3 GFM34 +0.0046 at 195 s). No Q/S/V violation. **Rule M3V-2: M3_DYNAMIC_FEASIBILITY_REFUTED (in sample).** B3: identical classification. | TDS (VERIFIED on the stored samples; refined step) |
| (c) Stability | Pre-event closed loop at ξ(z_M3): Hurwitz modulo the null mode (−2.35e-3). Frozen-time spectra at the 200-s end state of every run: rightmost −2.5e-3 (B2) and −2.3e-3 (B3); the 1.3 Hz pair at −0.86 to −1.01 1/s. | Static at a non-equilibrium state; indicative only; no T-B claim |
| (d) Optimality | KKT residual 0.107 against the tolerance 4.1e-3: **not** a local optimum | PREDICTIVE |
| (e) Redispatch cost | J = 3.087 against J(M0) = 0.700; 207.5 MW of redispatch versus M0 | PREDICTIVE |

**Cause of the UNSAFE cell (OBSERVED).**
- At b8P_S3 the algebraic jump of SG31 leaves +0.0335 pu of margin, and the M3 jump row (with ε_J) is satisfied.
- The sub-cycle overshoot after the jump (2.2 ms) is about 0.047 pu larger and is not represented by the jump map or the excursion predictor.
- This is the D8 phenomenon inside the design: the M3 constraints do not bound the instantaneous sub-cycle peak that the frozen criterion classifies.

**M3 is therefore NOT approved for OC3.** It is predictively feasible but dynamically refuted in sample under the instantaneous criterion.

Figures: `IEEE39_DEC057_M3V_margins_v2.png` (v1 superseded: the band hid the bars inside it), `IEEE39_DEC057_M3V_traces.png`. Data: `IEEE39_DEC057_M3V_results.json`. Static: `DEC057_state/oc3_seedrule.json`, `b3eq_*.json` (local).

---

## 5. What is demonstrated, verified, observed and open

| Item | Status |
|---|---|
| Local refinement wrapper reproduces uniform dt/16 (6e-13) and is bit-identical at k = 1 | VERIFIED |
| D8: the three critical DEC-054 M3 cases | NUMERICALLY_INDETERMINATE (instantaneous criterion); both integrators trend towards smaller margins |
| D8: jump validation to 1e-3 | OPEN (needs h < dt/16) |
| B3 makes ξ(z) an exact equilibrium (R1–R6) in all dispatches examined | DEMONSTRATED / VERIFIED |
| B3 equilibrium linearly stable: OC1, OC2, OC3-M3 yes; OC3-M0 no (+0.0198) | VERIFIED (FD-checked) |
| D7 | RESOLVED for OC1 and OC2; NOT_RESOLVED for OC3 |
| AC-04 step check (dt/2) | FAIL for B3 and B2 (D8 transient) |
| OC3 + B2 from M0: SG30 electromechanical pair crosses into instability at about 63 s because the capability-factor-scaled frequency gain grows | VERIFIED (FD Jacobian; RES4 growth within 1 %) |
| Onset at about 318 s in the default TDS is a reset_tiny dead-zone artifact | VERIFIED (RES4) |
| Flat or long TDS runs from an exact or near equilibrium as stability evidence | NOT VALID in the default solver configuration; earlier uses OPEN |
| Hopf bifurcation, T-B for OC3 | NOT CLAIMED / NOT APPROVED |
| OC3 M3 seed rule reproducible, DESIGN only, inside the variables and bounds | VERIFIED |
| OC3 M3: predictive feasibility / dynamic safety (in sample) / optimality | FEASIBLE_PREDICTED / REFUTED (b8P_S3) / not a local optimum |

## 6. Status of each blocker

- **G1: BLOCKED.**
  - D7 is resolved only in OC1 and OC2, and only with B3, which is still provisional.
  - AC-04 fails for both controllers.
  - The D8 transient classification is indeterminate.
  - L2 and L3 are not opened.
- **D8: NUMERICALLY_INDETERMINATE retained** (the protocol's rule when uncertainty persists).
- **OC3:**
  - the M0 + B2 closed loop is unstable from about 63 s;
  - the M0 + B3 equilibrium is linearly unstable;
  - M3 is not approved (in-sample refutation).

## 7. Decisions required (new methodological decisions; work stopped here)

1. **TDS solver setting.** Whether `reset_tiny = 0` (or tol_zero ≪ 1e-10) becomes mandatory for every TDS used as stability or settling evidence, and whether the affected earlier statements (DEC-050 2000 s, DEC-056 pre-settling, the B3 flat runs) are re-examined. The TDS budget is exhausted, so this needs a new budget.
2. **OC3.** The instability of B2 at M0 is a property of the B2 law combined with this OC (capability-factor-scheduled frequency gain), not of numerics. The options all change the controller, the dispatch rule or the scope:
   - (i) accept OC3 as a documented instability case outside C2/C3;
   - (ii) a B2 parameter or normalization change, which would change approved gains;
   - (iii) restrict the OC set.
3. **D7.** Whether B3 is confirmed as the controller under test. It is RESOLVED in OC1 and OC2 only, and it drops the voltage regulation to 1.0 pu.
4. **D8 / M3.** The sub-cycle peak is not bounded by the M3 jump/excursion rows. Three ways forward:
   - (a) add a sub-cycle overshoot term to the design rows (a formulation change);
   - (b) authorize h < dt/16 to establish the limit (and the jump validation);
   - (c) reconsider the instantaneous criterion on the RMS model, which was explicitly kept frozen.
5. **Publication.** Approval to push the DEC-057 commits to `rdc/review/dec055-architecture-b`. This push is covered by the DEC-057 authorization after verification and is done at the end of this session.
