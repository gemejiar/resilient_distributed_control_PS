# DEC-059 — Corrected formal results for the proposed controller B5′ (R1)

Status: written before any DEC-059 TDS and before the B5′ code; the definitions below are the specification that the implementation (`src/dec059_b5.py`) and its unit tests (`src/test_dec059.py`) must match. Notation follows `main.tex` §2. Nothing here is a certificate unless it says so; every hypothesis that is only checked numerically is marked **(numerical)**.

## 0. What changes with respect to `main.tex`

| `main.tex` | Status in IEEE-39 (evidence) | Replacement here |
|---|---|---|
| Th1 Physical invariance (HOCBF on P, Q, V, I) | Hypotheses fail: relative degree 3–4, post-jump state outside C_H for every tested amplitude, no GFM authority over SG31/SG35 (E9-A…H, DEC-047) | **T1** discrete-time invariance of the *reference* set (exact, explicit sufficient condition for feasibility). Physical constraints: **T-A** (necessary condition at t_e⁺) and evaluated TDS margins. No physical invariance theorem. |
| Th2 Regional convergence (certified Ω_ρ, 𝓜(d,ρ) ≥ 0) | No interval/AD backend; second-derivative bounds unavailable (DEC-052) | **T2** local exponential stability of the *sampled* closed loop with B5′, conditional (three levels), with explicit hypotheses and a qualitative domain of validity; first-order domain estimates labelled as estimates. |
| Th3 Restoration under saturation (D̂_rec certificate) | 𝓜(d,ρ) not computable; at binding limits g_P = 0 | **P3** classification proposition: necessary conditions (proved), verified local conditions (numerical), TDS outcome (observed). No sufficient recovery certificate. |
| Centering at ξ*(d) (eq. centered), "offsets computed after each disturbance" | DEC-057 B3 used the pre-event point only | B5′ uses ξ*(d̂) supplied by a supervisory layer with an information delay τ_info (assumption **A-INFO**, §2). |
| QP with HOCBF rows (eq. usafe) | — | QP with discrete reference-barrier rows, rate box, actuator-clamp rows and a soft CLF row (§2). |

## 1. Sampled-data model of the implemented loop

The TDS step is h = 2⁻⁸ s. At each sample t_k = k h the controller reads (P, Q, V, ω) of the 10 units and the full state (assumption A-STATE, CLF only), computes v_k, and **before** integrating the step applies

  u_k⁺ = u_k + h v_k,  u = (P^s, Q^s) ∈ ℝ²⁰  (exact; `run_b3_ieee39.py` lines 126–128),

then the plant is integrated over [t_k, t_{k+1}] with u_k⁺ held (ZOH through the actuator maps θ(u, y)). Writing x_d for the dynamic states with Tf > 0 (PSS-complete set of `dec051_core.index_sets`), the exact sampled map is

  Φ(x_d, u) = (φ_h(x_d, u + h v(x_d, u)), u + h v(x_d, u)),

with φ_h the flow of the reduced plant (`main.tex` eq. reduced) with references held. Its Jacobian at a fixed point with v = v_nom is the matrix D of `dec057_static.discrete_spectrum` (exact ZOH of the linearised plant).

## 2. Controller B5′

**Reference set.** For unit i (SG or GFM), with case limits p̄_i, p̲_i, q̄_i, q̲_i, s_i = Sn_i/100 (`run_e8_ieee39.configure`):

  c₁ = p̄ − P^s, c₂ = P^s − p̲, c₃ = q̄ − Q^s, c₄ = Q^s − q̲, c₅ = s² − (P^s)² − (Q^s)²,

and for SG units only (exciter actuator: z = κ(Q^s − Q^n) is applied through a clamp ±Z̄, κ = 0.06, Z̄ = 0.10):

  c₆ = Z̄/κ − (Q^s − Q^n), c₇ = Z̄/κ + (Q^s − Q^n).

W = {u : c_j(u) ≥ 0 ∀ j}. c₁…c₄, c₆, c₇ are affine, c₅ is concave.

**Lemma 0.**
- (i) On int W, the capability factors are positive: g_P, g_Q > 0. They are products of factors that are all positive there (`run_e8_ieee39.capability_factors`).
- (ii) On W, the SG reactive actuator map is unsaturated: |z| ≤ Z̄, so θ is affine in Q^s.

**Rate box.** −v̄ ≤ v ≤ v̄ with v̄_{P,i} = v̄_{Q,i} = 0.01·s_i pu/s (1 % of rating per second). This is a declared actuator-rate assumption, not identified from hardware.

**Nominal direction.**

  v_nom,k = v_RDC(ξ_k) − o_k,  o_k = v_RDC(ξ̂*_k)  (main.tex eqs. rdc, centered),

with gains, graph, capability factors and normalisation exactly those of B2 (`dec051_core.rdc_rates`).

**A-INFO (information assumption).**
- A supervisory layer measures the load change at the event bus (telemetry).
- At t_e it marks the current target as invalid.
- At t_e + τ_info it supplies ξ*(d⁺) from the equilibrium-selection rule E* (§4); τ_info = 1.0 s is declared.
- Until then the last valid target ξ*(d⁻) (the pre-event equilibrium, i.e. the B3 offset of DEC-057) is kept.
- The computation time of E* is not modelled; it is reported offline.

This is exactly the main.tex condition "the computed coordination offsets are available". It makes the complete design not fully distributed.

**A-STATE.** The CLF row uses the full dynamic state x_d and its derivative. This is available in simulation only: it is a centralised-state assumption of main.tex ("nominal measurements and the reduced model are assumed available") and is declared as a limitation.

**CLF data.**
- At each target ξ*, take the continuous closed-loop Jacobian A_c of plant plus nominal law. The right and left null vectors r, l of the common-angle mode satisfy l ᵀ r = 1.
- U is an orthonormal basis of ker lᵀ (the stable invariant subspace when the null mode is simple).
- A_r = Uᵀ A_c U.
- H_r ≻ 0 solves A_rᵀ H_r + H_r A_r = −I.
- The quotient error is ê = Uᵀ(e − r lᵀ e) with e = ξ − ξ*, and 𝒱(e) = êᵀ H_r ê.
- λ = ½ λ_min(I)/λ_max(H_r) = 1/(2 λ_max(H_r)).

**QP at sample k** (decision v ∈ ℝ²⁰, slack s ≥ 0):

  min ½ (v − v_nom)ᵀ R (v − v_nom) + ½ ρ_s s²,  R = diag(v̄⁻²), ρ_s = 10⁶,

subject to:
- (Q1) −v̄ ≤ v ≤ v̄;
- (Q2) for affine c_j: a_jᵀ v ≥ −(γ/h) c_j(u_k), γ = h α, α = 1 s⁻¹;
- (Q3) for each unit: ‖u_{k,i} + h v_i‖² ≤ s_i² − (1 − γ) c₅,ᵢ(u_k);
- (Q4) when the target is valid: 2 êᵀ H_r Uᵀ Π [ẋ_d ; v] ≤ −λ 𝒱 + s, with Π = I − r lᵀ.

When the target is invalid ([t_e, t_e + τ_info)), (Q4) is dropped.

Implementation note: (Q1)–(Q3) are linear and second-order cone constraints. The problem is solved as a cone QP (kvxopt `coneqp`). If v = v_nom satisfies (Q1)–(Q4) with s = 0, it is the unique minimiser and is returned without calling the solver.

## 3. T1 — discrete-time invariance of the reference set

**Theorem T1.** Let u₀ ∈ W, γ ∈ (0, 1] and v_k ∈ 𝒰_k := {v : (Q1)–(Q3)} for all k, with u_{k+1} = u_k + h v_k. Then for all k and all j:

  c_j(u_k) ≥ (1 − γ)^k c_j(u₀) ≥ 0.

In particular u_k ∈ W for all k, and u_k ∈ int W if u₀ ∈ int W.

*Proof.*
- Affine j: c_j(u_{k+1}) = c_j(u_k) + h a_jᵀ v_k ≥ c_j(u_k) − γ c_j(u_k) = (1 − γ) c_j(u_k).
- Quadratic: c₅(u_{k+1}) = s² − ‖u_k + h v_k‖² ≥ s² − s² + (1 − γ) c₅(u_k).
- Induction on k. ∎

**Proposition T1-F (explicit sufficient condition for feasibility and well-posedness).** If u_k ∈ W and −v̄ ≤ 0 ≤ v̄, then 0 ∈ 𝒰_k. Hence:
- the QP with (Q1)–(Q3) and the soft row (Q4) is feasible at every sample;
- its minimiser is unique, because the objective is strictly convex in (v, s) and the feasible set is closed, convex and nonempty;
- the closed loop u_{k+1} = u_k + h v*(ξ_k) is well defined for all k.

*Proof.*
- Affine: 0 ≥ −(γ/h) c_j(u_k), since c_j ≥ 0.
- Disc: ‖u_k‖² = s² − c₅(u_k) ≤ s² − (1 − γ) c₅(u_k), since γ c₅ ≥ 0.
- (Q4) is satisfied by any v with s large enough. ∎

**Corollary T1-A.** Along every B5′ trajectory:
- g_P, g_Q stay positive whenever u₀ ∈ int W (Lemma 0);
- the SG exciter actuator never enters its clamp (c₆, c₇ ≥ 0).

**Scope of T1 (what it does NOT say).** T1 concerns the references u only. It implies nothing for the delivered P, Q, S, V during transients. Those depend on the plant response and on the algebraic jump at t_e (T-A). The only link to physical quantities used in this work is at equilibria, and it is checked numerically at ξ*, never inferred from T1 (§4, condition E4). The rate box keeps the safe-input set compact, but the physical meaning of v̄ is an assumption.

## 4. Equilibrium selection E* and the centering lemma

**Rule E*.** Given the pre-event dispatch z, the post-event load d⁺ (constant-power PQ at the event bus), and the parameters of the running system (`rdc_state` at t = 0), find (x_d*, u*) with:

- (E1) plant equilibrium: f(x*, y*, θ(u*, y*), d⁺) = 0 and g(…) = 0 (quasi-algebraic and algebraic variables from `inner_solve`), with one SG rotor angle anchored at its pre-event value.
- (E2) Proportional active sharing, which is the zero set of the RDC consensus term L_P D_P P with D_P = diag(1/Pⁿ): P_i* = (1 + α) Pⁿ_i for i ∉ 𝒜. For i ∈ 𝒜 (the active-limit set), P_i* is pinned at the boundary of the band [min(p̲_i + ε_sel·rng_i, Pⁿ_i), max(p̄_i − ε_sel·rng_i, Pⁿ_i)], with rng_i = p̄_i − p̲_i and ε_sel = 0.01 (the frozen B3-A interior margin). 𝒜 is obtained by iteratively pinning units whose proportional share would leave that band.

*Amendment (before any use, found in the first static test):* the band contains the pre-event value Pⁿ_i. A unit dispatched inside the ε_sel margin (SG31 in OC1 M0) therefore takes no further share toward its limit, and d = 0 returns ξ(0) exactly. The same widening applies to the Q band of E3.
- (E3) Voltage restoration to the dispatch set-points: V_i* = V_i(0) at the 10 unit buses, except units in a reactive active set 𝒜_Q, whose Q^s is pinned at its ε_sel-interior limit (PV→PQ switching).
- (E4) Admissibility, checked after solving: u* ∈ int W; delivered P, Q, S inside the case limits; 0.95 ≤ V_b ≤ 1.05 at all 39 buses; no discrete limiter flag active. If E4 fails, no target exists under E*: the cell is classified, never forced.

(E1)–(E3) are n + 20 equations in n + 20 unknowns. They are solved by Newton with a central-difference Jacobian of the full residual, accepted at residual ≤ 1e-10 **(numerical)**.

By (E1), ω_i* = 1 exactly (δ̇ = ω_b(ω − 1) = 0). The selection is an instance of main.tex eq. eqselection:
- C_i: the quadratic sharing cost Σ(P_i − (1 + α)Pⁿ_i)², restricted to its zero set;
- γ_V → ∞ on the unit-bus deviations from the dispatch set-points.

It is a selection rule, not an economic optimum.

**Lemma C (centering).** If ξ* satisfies (E1) and the target is valid, then v*(ξ*) = 0 and ξ* is a fixed point of the sampled B5′ loop.

*Proof.*
- v_nom(ξ*) = v_RDC(ξ*) − v_RDC(ξ*) = 0.
- v = 0, s = 0 satisfies (Q1)–(Q3) by T1-F and (Q4) with equality (e = 0).
- The objective is 0 there, the minimum, and the minimiser is unique.
- With u⁺ = u* and (E1), φ_h(x*, u*) = x*. ∎

Consequence for regulation: if B5′ converges to ξ*(d⁺), the steady state has:
- ω = 1 exactly;
- unit-bus voltages at the dispatch set-points (units outside 𝒜_Q);
- exact proportional P sharing outside 𝒜.

This is by construction of E*. The evidence needed is convergence (T2 plus TDS), not the steady-state values. B2 instead settles with the voltage offset of DEC-050 (mean 3.2e-3 pu).

## 5. T2 — local exponential stability of the sampled B5′ loop (conditional)

**Hypotheses.**
- (H1) ξ* satisfies E1–E4 with residual ≤ r_root **(numerical; level L-b: root numerically verified, Kantorovich not certified)**.
- (H2) f, g are C² near ξ*, g_y is nonsingular, and every discrete limiter flag is inactive with positive margin. The plant is then smooth near ξ*.
- (H3) c_j(u*) > 0 for all j, and −v̄ < 0 < v̄.
- (H4) Spectral condition of the sampled map on the quotient. D has a simple eigenvalue 1 belonging to the common-angle direction (the map is equivariant under a common angle shift), and every other eigenvalue satisfies |μ| < 1. **(numerical for the computed D; level L-a when validated in floating point; level L-c: ‖D_exact − D_computed‖ small enough, not certified)**
- (H5) A_c has a simple zero eigenvalue and all other eigenvalues have Re < 0; λ = 1/(2 λ_max(H_r)).

**Theorem T2.** Under (H1)–(H5) there is a neighbourhood N of ξ* such that, for every initial state in N with a valid target:
- the B5′ QP returns v*(ξ) = v_nom(ξ);
- the trajectory of the sampled loop converges exponentially, modulo the common angle, to ξ* (more precisely, to the point of the relative-equilibrium orbit fixed by the anchor);
- the rate is at least ln(1/ρ_q)/h − ε for any ε > 0, where ρ_q is the quotient spectral radius.

*Proof.*

1. *QP inactivity.* By (H3) and continuity, for ξ near ξ*:
   - (Q2) holds strictly at v_nom(ξ): v_nom → 0, and the right-hand side is −(γ/h) c_j(u) < 0;
   - (Q3) holds strictly: ‖u + h v_nom‖² → ‖u*‖² < s² − (1 − γ)c₅(u*) when c₅(u*) > 0;
   - (Q1) holds strictly.

   For (Q4) at v = v_nom:
   - A_c r = 0 and lᵀA_c = 0 give Π A_c = A_c Π = A_c, and Π e ∈ ker lᵀ gives Π e = U ê.
   - The common-angle shift is an exact symmetry of plant and law, so F_c vanishes on the equilibrium orbit ξ* + c r and its Jacobian is constant along it. Expanding F_c about the nearest orbit point gives F_c(ξ) = A_c U ê + O(‖ê‖²).
   - Hence 2 êᵀH_rUᵀΠ F_c(ξ) = 2 êᵀH_r A_r ê + O(‖ê‖³) = −‖ê‖² + O(‖ê‖³), with F_c ∈ C².
   - −‖ê‖² ≤ −𝒱/λ_max(H_r) = −2λ 𝒱.
   - So the left side is ≤ −λ 𝒱 − λ𝒱 + O(‖ê‖³) < −λ 𝒱 for 0 < ‖ê‖ small. On the orbit direction ê = 0 the row reads 0 ≤ 0.

   Hence (v_nom, 0) is feasible with zero objective, so it is the unique minimiser: v* = v_nom on N₁.
2. *Local equivalence.* On N₁ the B5′ loop is the sampled centered RDC loop with offset o = v_RDC(ξ*). Its map Φ is C¹ (H2), Φ(ξ*) = ξ* (Lemma C), and its Jacobian is D.
3. *Quotient.* Φ commutes with common angle shifts. Passing to the quotient by the anchor removes the eigenvalue 1 (H4).
4. *Conclusion.* By the discrete-time indirect Lyapunov method (a C¹ map whose Jacobian at a fixed point has spectral radius ρ_q < 1 is locally exponentially stable at every rate above ρ_q), the claim holds on N = N₁ ∩ N₂, with N₂ the basin given by the indirect method. ∎

**Domain of validity.**
- N exists but is **not quantified**: no second-derivative bound is available.
- Reported, as **first-order estimates (not certificates)**:
  - the QP-inactivity radius r_QP, the largest ‖e‖ for which the linearised v_nom = K e satisfies (Q1)–(Q3) strictly;
  - the limiter-margin radius r_lim, the distance in output space to the nearest limiter threshold divided by the output Jacobian norm.
- T2 says nothing about whether the post-event state ξ(t_e⁺), or the state at t_e + τ_info, lies in N. That gap is the reason for P3.
- T2 concerns the exact sampled-data system. The TDS integrates it with the implicit trapezoid (dt), so TDS trajectories are approximations.
- In the continuous-time limit, (H5) is the corresponding condition. Both are reported.

**What the CLF row adds.** Locally nothing: it is inactive on N. Away from N it enforces 𝒱̇ ≤ −λ𝒱 at the sampling instants when feasible with s = 0. Because of sampling and the slack this is not an invariance or convergence guarantee, so its activity (slack incidence) is reported as observed behaviour only.

## 6. T-A (unchanged from the DEC-055 protocol) and the overshoot gap

T-A: for any controller in the rate-bounded class, which includes B5′ (no reset of u, x at t_e), h_j(ξ(t_e⁺)) = a_j(z, d⁺) depends only on the pre-event state. Physical safety at t_e⁺ is therefore a property of the dispatch.

DEC-057 refuted M3 in OC3 by a sub-cycle overshoot beyond a_j (b8P_S3, SG31, −0.0140 pu at 2.2 ms). That is a property of the plant response in [t_e, t_e + 50 ms], which no rate-bounded controller can affect either. The reason: |u(t) − u(t_e)| ≤ h v̄ k over k samples, i.e. at most 0.0005·s_i pu in 50 ms for B5′. The overshoot correction of R4 (DD) therefore belongs to the dispatch design, as T-A predicts.

**Proposition OS (controller-independence bound).** For any rate-bounded controller, the reference displacement over [t_e, t_e + T] is at most T·v̄. Hence the difference between the physical trajectories of two such controllers over that window is bounded by the plant's input-to-output gain times T v̄. For B5′ with T = 50 ms this is a 5e-4·s_i pu reference displacement.

## 7. P3 — classification proposition (replaces Th3)

For a pre-event dispatch z and a post-event constant disturbance d⁺:

- **(N1) Necessary for exact restoration within the constraints (proved).** If the capacity inequality (main.tex eq. capacity-necessary) fails, then 𝓔(d⁺) = ∅. No controller restores ω = 1 within the modelled limits. Label PROVEN_UNRECOVERABLE.
- **(N2) Necessary for physical safety from t_e on, rate-bounded class (proved, T-A).** If a_j(z, d⁺) < 0 for some physical constraint j, every such controller violates j at t_e⁺. Label INADMISSIBLE_AT_EVENT. Restoration may still occur.
- **(V) Verified local conditions for B5′ (numerical).** E* returns ξ* satisfying E1–E4 and (H1)–(H5) hold for the computed matrices. Label TARGET_LOCALLY_STABLE. Then T2 guarantees convergence from a neighbourhood of ξ*. Membership of ξ(t_e + τ_info) in that neighbourhood is **not** certified, so (V) is **not sufficient** for recovery.
- **(U)** None of the above can be decided (E* fails without N1 holding, or (H4)/(H5) fail). Label TARGET_NOT_VERIFIED; it splits into TARGET_UNSTABLE when (H4) or (H5) fails with a right-half-plane eigenvalue.
- **(O) Observed (TDS, never a proof).** RECOVERED_SAFE, RECOVERED_UNSAFE (a physical margin is negative beyond U_D8), NUMERICALLY_INDETERMINATE (|margin| < U_D8) or NOT_RECOVERED.

Logical status:
- N1 and N2 are necessary conditions with proofs.
- V is a set of numerically verified sufficient conditions for *local* convergence only.
- O is observation.

The set {d : V holds and O = RECOVERED_SAFE} is an empirically recovered set, not the certified D̂_rec of main.tex. Cases labelled TARGET_UNSTABLE or INADMISSIBLE_AT_EVENT are outside the hypotheses of T2 and T-A safety respectively. A failure there is not a counterexample to T2. A failure with label V is a counterexample to the empirical recovery claim (it may still be consistent with T2, since N is unquantified) and is reported as such.

## 8. Effect on novelty, title, abstract and contributions

- **Lost (with respect to main.tex as written):**
  - certified regional convergence;
  - physical-output invariance by HOCBF;
  - a certified recoverable-disturbance set;
  - restoration with units *at* binding limits. At the boundary g_P = 0, so H3 fails; E* uses ε_sel-interior pins.
- **Retained or new, and defensible:**
  1. An information-aware centered RDC (B5′) with a safety QP whose reference invariance is exact in discrete time (T1, T1-F, constructive feasibility, which removes the "feasibility is not automatic" caveat for the reference layer).
  2. Exact zero steady-state frequency error, set-point voltage restoration and exact proportional sharing at the selected equilibrium (Lemma C), against the documented offset of the original RDC.
  3. Conditional local exponential stability of the *implemented sampled-data* loop (T2), with the OC3 counterexample of the original law predicted by the same linear test (DEC-057, growth within 1 %).
  4. The post-event admissibility theorem T-A plus Proposition OS. Instantaneous and sub-cycle physical safety is a dispatch property, independent of any rate-bounded secondary controller. This motivates the preventive dispatch with an overshoot term.
  5. The P3 classification with clearly separated proved, verified and observed levels.
  6. The negative result: an HOCBF/CLF obstruction analysis on a stiff DAE.
- **Suggested title (for the investigator):** "Information-Aware Centered Distributed Frequency–Voltage Control with Discrete Reference Invariance and Preventive Post-Event Admissibility in Hybrid SG–GFM Power Systems". The current methodology heading ("Nonlinear Stability, Dynamic Safety, and Feasible Frequency–Voltage Regulation") overstates "dynamic safety" and "nonlinear stability" unless qualified as "local" and "preventive/evaluated".
- **Abstract** must say:
  - local (not regional) stability;
  - evaluated (not certified) transient safety;
  - supervisory equilibrium information;
  - IEEE-39 C2 (SG–GFM) only.
- **Validation paragraph of main.tex** (GFL variants, X/R variation, certified attraction volume, barrier-only filter benchmark) exceeds what will be evaluated. It must be reduced to what R5/R6 run (§`IEEE39_DEC059_contribution_matrix.csv`, column `manuscript_action`).
- **DF check.**
  - GFL/C3: no explicit contribution needs it once the validation paragraph is reduced, so deferral is admissible.
  - Robustness: the information assumption A-INFO is part of contribution 1, so a minimal check of τ_info is indispensable. It is budgeted as 2 TDS (τ_info and 4·τ_info on one TEST S2 cell, after TEST).
  - Communication delays and N−1 are not needed by any contribution.
