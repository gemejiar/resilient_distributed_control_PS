# DEC-056 — Resolution of the G1 blockers D7 and D8 and of the OC3 M3 design failure

**Pre-registered protocol:** `ops/sted/DEC056_protocol.md`. Plans sealed before each lot: `IEEE39_DEC056_{D8,D7a,RES1}_plan.json`. Ledger: `IEEE39_DEC056_tds_ledger.csv`.

**TDS used:** 14 of 18 (D8 10, D7 3, reserve 1). Numerical failures: 2 (the same run, executed twice on purpose, see D7).

**Not changed:** plant, cases, B2 law and gains, limits, partitions, acceptance criteria, DEC-050–055 results.

**Not executed:** L2, L3, L4. No push.

Evidence labels used below:
- **DEMONSTRATED** — algebraic or exact statement about the implemented model.
- **VERIFIED** — numerical result with an explicit tolerance and an independent check.
- **OBSERVED** — numerical observation without a convergence or uniqueness guarantee.
- **OPEN** — not established.

---

## 1. D7 — the OPF dispatch is not an equilibrium of plant + B2

### 1.1 Cause (DEMONSTRATED)

At activation the leak term vanishes, because Qset = Qn by construction of `run_b3_ieee39.run`. The B2 reactive rate of unit i is then

    v_Q,i = K_IQ [ K_V gQ,i (V_ref − V_i) − K_Q lQ,i ],   K_IQ K_V = 0.3, K_IQ K_Q = 0.003, V_ref = 1.0.

It is zero only if V_i = 1 − (K_Q/K_V) lQ,i / gQ,i for every unit. These are ten conditions, and the OPF imposes none of them. The P rates vanish identically (ω = 1, Pset = Pn, x_P = P/Pn = 1).

Steady state of B2 with the leak active: K_V gQ (1 − V) = K_Q lQ + (K_LEAK/K_IQ)(Qset − Qn), with K_LEAK/K_IQ = 3.3e-3. A unit voltage error of 0.01 pu would therefore need Qset − Qn ≈ 1 pu per 0.003 of rate. The SG actuator clamp (|z| ≤ 0.10, κ = 0.06) limits Qset − Qn to about 1.7 pu. Hence B2 drives the unit voltages to within a few 1e-3 pu of 1.0 in steady state. The voltage set-points chosen by the OPF (up to 1.045 pu) cannot be sustained by the closed loop.

### 1.2 Residuals at the initialised dispatch (VERIFIED, `dec056_d7.py diag`, 0 TDS)

| Dispatch | Plant max\|f\| | Plant max\|g\| | max\|v_P\| | max\|v_Q\| (pu/s) | Voltage term | Consensus term | max\|V_unit − 1\| |
|---|---|---|---|---|---|---|---|
| OC1 M0 | 2.2e-16 | 2.5e-13 | 0 | 9.71e-3 | 1.02e-2 | 4.04e-3 | 0.045 |
| OC2 M0 | 2.2e-16 | 1.3e-13 | 0 | 9.70e-3 | 1.09e-2 | 4.39e-3 | 0.045 |
| OC3 M0 | 4.4e-16 | 6.0e-14 | 9e-16 | 1.15e-2 | 1.14e-2 | 1.51e-3 | 0.045 |
| OC1 M3 (DEC-055) | 4.6e-16 | 1.1e-13 | 6e-16 | 9.70e-3 | 1.05e-2 | 4.11e-3 | 0.045 |
| OC2 M3 (DEC-055) | 2.2e-16 | 1.7e-13 | 1e-15 | 9.69e-3 | 1.09e-2 | 4.38e-3 | 0.045 |
| OC1 M3 (DEC-054 frozen) | 2.2e-16 | 1.6e-13 | 1e-16 | 9.71e-3 | 1.03e-2 | 4.13e-3 | 0.045 |

The plant itself is an exact equilibrium. The only non-zero equations of the closed loop are the ten B2 Q rates, dominated by the voltage term.

### 1.3 Closed-loop linearisation and settling

**Linear response from ξ(z)** (OBSERVED):
- It predicts the first 20-s drift: 9.6e-3 pu (OC1), 8.2e-3 (OC2), 1.14e-2 (OC3).
- Against the stored L1 flat TDS, the error is ≤ 1.6e-4 pu over the first 20 s. After about 50 s the linear model departs strongly (OC1: 0.015 pu at 100 s), because the capability factors change as Q moves by about 0.8 pu.
- The linear model is therefore **not** used to estimate the settling time.

**Settling measured in TDS (VERIFIED on the stored series):**

| Run | 20-s drift ≤ 1e-3 pu from | 20-s drift ≤ 1e-4 pu from |
|---|---|---|
| L1 flat runs, OC1–OC3 (activation at 5 s, 200 s) | not reached within 200 s (1.15e-3 at 180 s); decay τ = 61–84 s | — |
| D7 pre-settling, OC1 M0 (B2 active from t = 0, 600 s) | **187 s** | **561 s** |

f_COI stays within 1.2e-4 Hz throughout. The 2000 s horizon of DEC-050 is not needed for the frozen G1 criterion.

**Closed-loop spectrum at ξ(z):**
- OC1 and OC2: Hurwitz modulo the common-angle null mode (rightmost −2.9e-3 and −4.2e-3 s⁻¹).
- **OC3: one real eigenvalue +0.0198 s⁻¹.** It is dominated by Qset of SG30, coupled with the Q loop of GFM37 (OBSERVED).
- Mechanism (DEMONSTRATED for the linearisation): ∂v_Q/∂Qset contains K_IQ K_V (1 − V) ∂gQ/∂Qset. For SG30 near Qmax (Q = 1.417 of 1.532 pu) with V_SG30 = 1.0285 > 1, this term is positive, which gives local positive feedback.
- In the L1 flat run (200 s) this eigenvalue does not produce divergence: the trajectory leaves the region.

### 1.4 Does a constraint-consistent closed-loop equilibrium exist? How to initialise it?

**Self-consistent dispatch** (`selfc2`): min ‖v_Q‖² subject to the DEC-054 OPF base constraints (V band with the 0.005 margin; P, Q, S with the 0.01 margin). Local SLSQP.

| OC | v0 free (p0 of M0) | All 19 variables free | v0 free with gQ,raw ≥ 0.2 |
|---|---|---|---|
| OC1 | 2.9e-4, **degenerate** (SG30 at the Q bound, gQ = 0.015, linearisation unstable) | 3.6e-7, degenerate (gQ = 3.6e-5), 1395 MW | 3.2e-3: no self-consistent point |
| OC2 | **7.2e-4**, genuine (gQ,min = 0.34), stable, V ≤ 1.045 active | **3.0e-8**, genuine (gQ,min = 0.195), stable (−2.5e-3 s⁻¹), 520 MW | — |
| OC3 | 2.0e-4, **degenerate** (SG30 at the Q bound, linearisation +0.019 s⁻¹) | 5.1e-6, degenerate (gQ = 1.2e-3), base constraints violated by 2e-4 | 8.0e-3: no self-consistent point |

Values are max |v_Q| in pu/s.

"Degenerate" means that the optimiser drives one unit to the boundary of its capability set, where gQ → 0 cancels its rate trivially. B2 refuses to start there ("Nominal setpoint is not in the interior of W_i"). The unconstrained Newton (`selfc`) reached the same boundary. These are local results: they are not a proof of non-existence.

**TDS check of the genuine OC2 candidate** (VERIFIED, D56T013, G1 settings, activation at 5 s, 200 s): the 20-s drift is ≤ **5.6e-4 pu in every window**, V is in 0.9814–1.0475 pu and f_COI is constant. The frozen G1 voltage criterion is met at a dispatch that is a B2 equilibrium within 7.2e-4 pu/s, without relaxing the criterion. This is not a G1 approval: G1 is defined at the DEC-055 M0 dispatch.

**Pre-settling in OC3** (OBSERVED, D56T012 and reserve D56T014, deterministic: identical failure time). B2 active from t = 0 at the OC3 M0 dispatch:
- it settles smoothly up to about 318 s (the Qset rate of SG30 falls from 5.9e-3 to 1.9e-5 pu/s);
- at t ≈ 318.5 s an oscillation of **1.27 Hz** (P of SG30, Q of SG39) starts abruptly and grows at about 0.59 s⁻¹;
- the TDS fails at **343.4 s** (Newton divergence, V_min 0.36 pu).

The abrupt onset suggests a discrete switching event, a limiter, that triggers or destabilises the mode, rather than a gradual Hopf crossing. **The cause is OPEN.** Characterising the OC3 equilibrium is L4 (T-B) work, which is blocked. The L1 OC3 flat run (200 s) was too short to reveal it.

**Newton for the closed-loop equilibrium ξ*(z) started at ξ(z)** (`cleq`): it did not converge (40 iterations, residual 9e-3, step lengths about 1e-3). The DEC-051 procedure works only from a near-equilibrium start (a TDS end state), so this is not a feasible initialisation route on its own.

### 1.5 Alternatives for D7

| Alternative | Accuracy | Cost | Reproducibility | Changes | Status |
|---|---|---|---|---|---|
| (a) Keep B2 and the protocol; G1 voltage criterion recorded as not met; report post-event V/Q as "event + B2 regulation" | exact description of the frozen design | 0 | full | none, but G1 stays FAIL (the criterion is not relaxed) | always available |
| (b) Pre-settling: B2 active from t = 0, event at T_e ≥ 190 s (1e-3) or ≥ 560 s (1e-4) | removes the regulation transient | +1.0× to +2.8× per TDS (200 → 390 or 760 s) | deterministic | event time; the pre-event state becomes ξ(T_e) ≈ ξ*(z), not z. M0/M3 designs and T-A must be recomputed at that state | **not viable in OC3** (oscillatory failure at 318–343 s) |
| (c) Self-consistent dispatch: OPF with v_Q(z) = 0 as 10 equality constraints | exact (flat by construction) | static; about 6–40 min per OC | deterministic | M0/M3 formulation (new constraints) | genuine only in **OC2**; OC1/OC3 only degenerate points |
| (d) Centered RDC B3 (DEC-039: offset = v_RDC at the pre-event equilibrium; S0 invariance already verified) | flat by construction | 0 | full | controller B2 → B3; no voltage regulation to 1.0 pu | requires authorization (controller change) |
| (e) V_ref of B2 equal to the dispatch voltages | removes only the voltage term (the consensus term of about 4e-3 remains) | 0 | full | B2 parameter | insufficient on its own; not allowed |

**Recommendation:** (a) for the current program, with the G1 voltage criterion reported as not met and the V/Q results labelled "closed loop (event + regulation)". If the investigator wants a clean pre-event equilibrium, (d) is the only option that works in all three OCs without a redesign, but it changes the controller under test. Option (b) is excluded by the OC3 result. Option (c) does not exist in OC1 and OC3 within the constraints.

---

## 2. D8 — step dependence of the post-event transient

**Reference case:** P3B2_b7P_M3 (OC1, bus 7, +0.58564 pu, frozen DEC-054 M3 dispatch), 20 s.
- Trapezoid at dt, dt/2 (reused) and dt/4, dt/8, dt/16.
- Backward Euler at dt to dt/16.
- Trapezoid at dt with Newton tolerance 1e-8.

**Wrapper regression:** bit-identical to the stored run in t, P, Q and V. Analysis: `IEEE39_DEC056_D8_convergence.json`.

### 2.1 Convergence table

Values by step size h = dt/k, with dt = 2^-8 s.

| Quantity | Integrator | k = 1 | 2 | 4 | 8 | 16 | Verdict (pre-registered rule) |
|---|---|---|---|---|---|---|---|
| SG31 max P, 0–0.5 s (pu) | trapezoid | 6.49552 | 6.50040 | 6.50666 | 6.50845 | 6.50945 | CONVERGED, p = 0.84, limit **6.5107** |
| | backward Euler | 6.48806 | 6.49167 | 6.49511 | 6.49853 | 6.50229 | NOT_CONVERGED |
| Minimum Pmax margin, post-event (pu, SG31) | trapezoid | +0.0045 | −0.0004 | −0.0067 | −0.0084 | −0.0094 | CONVERGED, limit −0.0107 |
| | backward Euler | +0.0119 | +0.0083 | +0.0049 | +0.0015 | −0.0023 | NOT_CONVERGED |
| Time of the SG31 maximum after the event | both | 2–4 ms at every level | | | | | sub-cycle |
| 1-cycle (4·dt = 15.6 ms) mean P, minimum margin | trapezoid | 0.0189 | 0.0175 | 0.0169 | 0.0168 | 0.0168 | converged |
| | backward Euler | 0.0217 | 0.0191 | 0.0178 | 0.0172 | 0.0169 | converged; limits agree, about 0.0168 |
| f_COI nadir (Hz) | trapezoid / BE | 59.972195 / 59.972234 | | | | 59.972193 / 59.972196 | CONVERGED, limits agree |
| RoCoF, f_COI over 100 ms (Hz/s) | trapezoid / BE | −0.02083 / −0.02120 | | | | −0.02120 / −0.02123 | converged; 2 % error at dt |
| V_min post-event (pu) | trapezoid / BE | | | | | | CONVERGED, limits agree (0.973564) |
| P, V, f at 0.05 s, 1 s and 5 s after the event | trapezoid / BE | | | | | | CONVERGED, limits agree |
| Period-2h alternation, GFM P, first 50 ms (fraction of steps) | trapezoid | 0.79 | 0.64 | 0.42 | 0.17 | 0.08 | ringing |
| | backward Euler | 0.12 | 0.10 | 0.06 | 0.04 | 0.03 | no ringing |
| First sample − algebraic jump, max over units (pu) | trapezoid | 0.078 | 0.052 | 0.020 | 0.0033 | 0.0029 | not monotone |
| | backward Euler | 0.092 | 0.078 | 0.052 | 0.020 | 0.0033 | |

The algebraic jump at SG31 is P+ = 6.47919 pu (residual 1.1e-13).

**Newton tolerance 1e-8 instead of 1e-4 at dt:**
- extrema change by 3.0e-4 pu;
- P changes by 5.2e-4 pu and V by 2.2e-5 pu, excluding the first 50 ms;
- ANDES halved h at the event step, because Newton needed 15 or more iterations.

### 2.2 Diagnosis

- **H8a (DEMONSTRATED by the sequences):** trapezoidal ringing of stiff modes exists at the protocol step. It decays with h and is absent with backward Euler.
- **H8b (DEMONSTRATED):** the event enters in the step that ends at t_e with f(t_e−) = 0. The first sample of trapezoid with step h therefore equals, to the last digit, the first sample of backward Euler with step h/2 (table: TR k equals BE 2k). The first sample is x_pre advanced by an implicit step of h/2 (trapezoid) or h (backward Euler) under the post-event dynamics. It is not the jump state.
- **H8c (not met as stated):** the Newton tolerance moves the extrema by 3e-4 pu, above the 1e-4 threshold. It is still about 30 times smaller than the step effect.
- **H8d:** all quantities beyond the first cycle converge with both integrators to a common limit. The sub-cycle peak of SG31 (2–4 ms) does not meet the pre-registered rule: backward Euler is not yet asymptotic, and its differences of about 0.0035 per halving are not decreasing.
  - Both finest levels lie above Pmax (trapezoid 6.5094, backward Euler 6.5023).
  - The trapezoid sequence extrapolates to 6.5107, which would be an exceedance of about 1 MW lasting about 2 ms in the RMS model.

### 2.3 Classification of the reference case (rule 2, pre-registered)

The stored-sample margin at the protocol step is +0.0045 pu. Its limit is not accepted, because backward Euler did not converge. The case is therefore **NUMERICALLY_INDETERMINATE**. The observational evidence points to a sub-cycle violation in the converged limit.

The DEC-054 statement "M3, zero violations" is not robust for this case under the per-sample criterion. This confirms and strengthens the DEC-055 caveat D54-REV-001. No DEC-054 or DEC-055 verdict is re-labelled.

### 2.4 Proposed replacement of `jump_vs_first_sample` and of the per-sample criterion

Proposed for investigator approval. Not applied to any existing result.

1. **Jump validation.** Validate P+ against the backward-Euler first sample at h → 0, since the sequence shows that the first sample is a single implicit step from x_pre. The criterion is |P+ − lim_{h→0} P_BE(t_e)| ≤ 1e-3 pu, evaluated once per OC on a refinement sequence.
   - Observed status: at h = dt/16 the deviation is 3.3e-3 pu and not yet monotone. **Jump validation to 1e-3 is OPEN**; it needs h ≤ dt/32 or a direct one-step comparison.
   - The per-run first-sample test is withdrawn, because it is unattainable by construction (H8b).
2. **Power-limit criterion.** Assess Pmax on the **one-cycle (4·dt = 15.6 ms) moving average** of the unit electrical power. Report the instantaneous per-sample maximum as a separate diagnostic.
   - Physical justification: an RMS phasor model is not valid inside one cycle, and Pmax is a quasi-steady thermal and mechanical limit.
   - Numerical justification: the averaged margin converges with both integrators, with an error of about 0.002 pu at the protocol step.
   - Classification for future runs: SAFE if m − U ≥ 0, UNSAFE if m + U < 0, otherwise NUMERICALLY_INDETERMINATE, with U = 0.003 pu (0.0021 observed error at dt plus a factor 1.25 on the limit uncertainty).
   - The reference case would be SAFE under this criterion (m = 0.0189 at dt, limit 0.0168).
   - **This is a change of an acceptance criterion and requires authorization.** Applying it retroactively, or only where it helps, is excluded.
3. **Alternative without a criterion change:** run TEST with trapezoid at dt/16 for [t_e, t_e + 0.5 s] and dt elsewhere (resume with a new tstep), and classify the instantaneous margin with U ≈ 0.002 pu (dt/16 − limit). Cost: about +15 % per 200 s TDS. Needs a runner change, a regression test and authorization.

---

## 3. OC3 — M3 design failure

### 3.1 Causal chain (VERIFIED unless marked)

1. Algorithm 1 never left its first NLP. Both seeds hit `maxiter`: z_ref first, then M0. `iterations: 0` refers to the outer loop; no cut was ever added. The final point is 1.9e-3 MW from M0.
2. In every point examined (M0, the failed point, all finite-difference neighbours), the M3 excursion predictor fails for **b23P_S3 and b28P_S3** (`ok = False`, predicted |D| > 50 pu). It returns E_up = 12 and 20 pu for b23P_S2 and b28P_S2. The algebraic jump converges in all 12 DESIGN scenarios (residual ≤ 3e-13).
3. **Cause of the predictor failure:**
   - the post-jump closed-loop linearisation has a real eigenvalue between +0.018 and +0.32 s⁻¹ in all 12 DESIGN scenarios at M0;
   - the excursion maximum lies at the end of the 195 s horizon, so the growth is exponential;
   - the dominant states are Qset of SG30 (the D7 mechanism), and Pset of GFM36 (b23) or SG38 (b28);
   - those two units end up above Pmax right after the jump (6.22 > 5.95 and 9.00 > 8.65 pu);
   - in OC1 the same predictor is stable except b23P_S3 (+0.0089 s⁻¹).
4. `dec054_opf.margins_d` encodes a failed evaluation as −1e3. SLSQP therefore sees 40 constraints that are flat at −1000 and impossible to satisfy. Finite differences across the success/failure boundary produce "gradients" of 1e5 to 4e7 that depend on h. Result: line-search stagnation and the iteration limit. The linearised feasibility LP at the failed point returns t* = −1000 for every radius.

The failure is therefore neither a classical optimiser issue (scaling, step, tolerance) nor a proof of infeasibility: **the M3 constraint functions are undefined in the whole region explored.**

### 3.2 Feasibility (VERIFIED, exact re-evaluation; local)

- **Jump admissibility of all 12 DESIGN scenarios (S1–S3) in OC3 is feasible.**
  - One minimum-norm LP step (min Σ|dz|/scale subject to jump margins ≥ 0.002 and base constraints) gives a point with minimum jump margin **+0.0019 pu**, base constraints satisfied, and 122.5 MW redispatch from M0 (`oc3_phase1b`).
  - The aggregate condition is not binding: Σ(Pmax − worst jump − ε_J) = 72.59 pu against 64.88 pu dispatched.
  - The maximise-t SLP (`phase1`) stalled because of its acceptance rule and the trust region.
  - Large LP steps (> 350 MW) leave the initialisable region: the TGOV1N VMIN initialisation fails, which is a model limit not represented in the OPF bounds.
- **Lowering the SG30 voltage set-point by 0.01 pu** at that point makes all 12 post-jump linearisations Hurwitz (max Re ≈ 3e-13, the null mode). The jump margin stays ≥ +0.0014 pu and the M3 predictor is defined everywhere. The M3 minimum margin is −0.159 pu (b23P_S3, SG33 excursion, 24 negative rows), the normal situation that Algorithm 1 is designed to handle. Figure: `IEEE39_DEC056_OC3_spectrum.png`.

### 3.3 Least-invasive solution strategy (same M3 formulation and cfg; only a new seed)

- **Reduced test** (N_it 6, K_max 1, 562 s): SOLVER_FAILED, as expected with 6 iterations. The M3 margin improved from −0.159 to −0.122 pu (159 MW), so the solver now makes progress.
- **Full run** (N_it 25, K_max 8; Algorithm 1 always tries z_ref first): **FEASIBLE_PREDICTED** (section 3.4).

### 3.4 Full seeded run (static, 0 TDS; 4551 s wall time, 6 workers)

| k | working set | min M3 margin (pu) | most violated row | J |
|---|---|---|---|---|
| 0 | 80 | −0.1101 | b8P_S3, SG31 P+ (cut added) | 2.589 |
| 1 | 81 | −0.1030 | b8P_S3, GFM32 P+ (cut added) | 2.846 |
| 2 | 82 | **−2.4e-5** | b28P_S3, GFM34 P+ | 3.087 |

- Termination by the frozen DEC-054 rule `min margin ≥ −τ_cut` (τ_cut = 1e-4 pu, unchanged). The KKT residual is 0.107, above `kkt_tol·(1+J)` = 4.1e-3, so the status is FEASIBLE_PREDICTED, **not** LOCAL_OPTIMUM_FOUND.
- Exact re-evaluation over all 12 DESIGN scenarios: minimum margin −2.37e-5 pu (inside τ_cut); base constraints +4.3e-12.
- Redispatch from M0: 207.5 MW. SG30 v0 = 1.0137 pu (seed 1.0185); four voltage set-points at the upper bound 1.045.
- Post-jump closed-loop linearisation at the result: max Re(eig) ≤ 3e-13 s⁻¹ in all 12 DESIGN scenarios (structural null mode only), so every predictor row is defined (`oc3_spectrum_seeded_full`).
- What this shows: **M3 is feasible as designed in OC3 (locally, within the predictor model)**. The SOLVER_FAILED of DEC-055 was an initialisation failure, not infeasibility.
- What it does not show: transient safety in TDS (L2/G3 not run); B2 settling from this dispatch (the D7 issue applies; the OC3 M0 pre-settling run became unstable, section 1); optimality.

### 3.5 Alternatives for OC3 M3

- **(i)** Keep the formulation; seed with a jump-admissible, post-jump-stable point (done here, a solver-level change only). Declare the seeding rule before the L2 freeze.
- **(ii)** Evaluate the excursion rows only where the jump rows are satisfied (hierarchical constraints), and replace the −1e3 sentinel by a smooth exact-penalty value. This is a formulation change.
- **(iii)** Shorten the predictor horizon or reject an unstable linearisation as a design infeasibility. This is a formulation change.
- **(iv)** Accept OC3 without M3. This is not recommended: M3 is now shown to be well posed in part of the OC3 dispatch space.

M0 stays a reference only. It is not a valid substitute for M3: in OC3, M0 is jump-inadmissible in most DESIGN cells and its post-jump closed loop is linearly unstable.

---

## 4. What is demonstrated, observed and open

| Item | Status |
|---|---|
| D7 cause: B2 rates at activation = voltage + consensus terms, leak 0; the OPF imposes no B2 equilibrium condition | DEMONSTRATED |
| Plant is an exact equilibrium at the OPF point (\|f\|, \|g\| ≤ 3e-13); only the 10 Q rates are non-zero | VERIFIED |
| Settling of B2 from the OPF point: 20-s drift ≤ 1e-3 pu after 187 s, ≤ 1e-4 pu after 561 s (OC1) | OBSERVED (one OC, one dispatch) |
| A genuine self-consistent dispatch exists in OC2 and passes the frozen G1 voltage criterion in TDS | VERIFIED (local; one dispatch) |
| No non-degenerate self-consistent dispatch in OC1/OC3 within the constraints | OBSERVED (local optimisation); not proven |
| OC3 + B2 from the M0 dispatch: oscillatory instability of 1.27 Hz after about 318 s, TDS failure at 343.4 s | OBSERVED (deterministic, twice); cause OPEN (L4) |
| D8: trapezoidal ringing at dt; first-sample mechanics; slow quantities converged at dt | DEMONSTRATED / VERIFIED |
| D8: converged sub-cycle peak of SG31 | OPEN (backward Euler not asymptotic); trapezoid limit 6.5107 > Pmax |
| D8: reference-case classification | NUMERICALLY_INDETERMINATE (pre-registered rule) |
| OC3: M3 failure caused by undefined predictor rows (unstable post-jump linearisation) plus the −1e3 sentinel | VERIFIED |
| OC3: jump admissibility of all DESIGN S1–S3 is feasible | VERIFIED (exact re-evaluation) |
| OC3: M3 design feasible from a jump-admissible, post-jump-stable seed (FEASIBLE_PREDICTED, min margin −2.4e-5 within τ_cut, 207 MW) | VERIFIED (static, local; not a TDS safety result) |
| OC3: B2 closed-loop behaviour from the M3 dispatch | OPEN (no TDS) |

## 5. Decisions required from the investigator

1. **D7:** choose (a) or (d); (b) and (c) are not generally viable.
2. **D8:** approve or reject the one-cycle-mean Pmax criterion (2.4-2) or the locally refined step (2.4-3). Both must be declared before any TEST TDS. Jump validation stays OPEN.
3. **OC3:** approve the seeding rule (i) (recommended: it is sufficient, as section 3.4 shows, and leaves the M3 formulation, cfg and τ_cut unchanged), or a formulation change (ii)/(iii), before L2. The seed was built from DESIGN data only (jump rows, base constraints, post-jump spectrum); no TUNE/TEST information was used.
4. **OC3 stability:** authorize L4-type characterisation of the oscillatory loss of stability. It bears directly on T-B for OC3 (the G6 stop rule).
