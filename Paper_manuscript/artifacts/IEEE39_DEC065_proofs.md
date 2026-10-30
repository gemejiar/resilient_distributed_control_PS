# DEC-065 audited proofs: T-A, N2, Lemma C, T1, T2, P3 and the corrected Proposition OS

Scope: mathematical statements only. Each item carries its hypotheses, a proof or the reason none is given, its audit result, and a classification (PROVED, PROVED-CONDITIONAL, NUMERICAL-ESTIMATE, EMPIRICAL). Numerical files: `IEEE39_DEC065_os_check.json`, `IEEE39_DEC065_os_gronwall.json`, `IEEE39_DEC064_checks.json`. Nothing here extends beyond the stated hypotheses.

## 0. Standing hypotheses

- **(H-DAE)** The plant is a DAE ẋ = f(x, y, u, d), 0 = g(x, y, u, d) in which the quasi-algebraic states are absorbed in y, with g_y nonsingular on the region visited (index 1). Then y = ψ(x, u, d) locally and ẋ = F(x, u, d) := f(x, ψ(x, u, d), u, d).
- **(H-E)** The event is a step of the constant disturbance d⁻ → d⁺ at t_e (a PQ load step); the dispatch z fixes (x(t_e⁻), u(t_e⁻)).
- **(H-C)** *Continuity of states and control actions at the event:* x(t_e⁺) = x(t_e⁻) and u(t_e⁺) = u(t_e⁻). In the sampled implementation the controller updates u_k⁺ = u_k + h v_k before integrating the step that contains t_e, so H-C holds only up to η = u(t_e⁺) − u(t_e⁻), |η_k| ≤ h v̄_{c,k}, with v̄_c the rate bound of controller c; section 1 treats η explicitly.
- **(H-L)** Limits are constraints on *delivered* unit quantities y_j = H_j(x, y, u) (P, Q, S, V), through margins h_j := (limit) − (value) ≥ 0. A "violation" is h_j < 0 as a modelling definition.

## 1. T-A and N2 (post-event instant)

**Theorem A (PROVED, H-DAE, H-E, H-C).** Let c₁, c₂ be any two controllers that satisfy H-C. Then the post-event outputs coincide: y(t_e⁺) = ψ(x⁻, u⁻, d⁺) for both, hence h_j(t_e⁺) = a_j(z, d⁺) := h_j evaluated at (x⁻, ψ(x⁻, u⁻, d⁺), u⁻), independent of the controller.

*Proof.* Both trajectories have the same (x(t_e⁺), u(t_e⁺), d⁺) by H-C and H-E. y(t_e⁺) is the unique solution of g = 0 near the pre-event algebraic point (H-DAE, implicit function theorem). h_j is a function of (x, y, u). ∎

**Corollary A.1 (sampled-data form, PROVED).** If u^a(t_e⁺) − u^b(t_e⁺) = η^a − η^b with |η^c_k| ≤ h v̄_{c,k}, then |h_j^a(t_e⁺) − h_j^b(t_e⁺)| ≤ Σ_k |C_u,jk| h (v̄_{a,k} + v̄_{b,k}) + R₂, where C_u = ∂y/∂u at the pre-event point and R₂ is the second-order remainder (not bounded here). In the estimates below ‖C_u‖ ≈ 0 (no direct feedthrough: ℓ_u = 3.3e-16 and 1.5e-16 for OC1/OC2), so the correction is numerically nil.

**Corollary A.2 = N2 (PROVED, same hypotheses).** If a_j(z, d⁺) < 0 for some j, every controller satisfying H-C violates constraint j at t_e⁺. *Audit:* the statement is a consequence of Theorem A; its experimental confirmation (7 of 7) is therefore a consistency check, not independent evidence. Content restriction: it says nothing about turbine-side limits or about t > t_e⁺.

**Audit of the previous T-A.** The earlier statement omitted H-C and the sampled-data update at the event sample. Correct, with H-C made explicit.

## 2. Corrected Proposition OS (evolution after the jump)

**Errors in the previous version.**
1. It asserted a common bound v̄ (that of B5′/B4′) for "any rate-bounded controller". B2 reaches 6.27 × T·v̄ in the first 50 ms (`dec064_checks.py`); B2 does not belong to the class with the box bound.
2. "Bounded by the plant's input-to-output gain × T v̄" left the gain, the norm and the dependence on t undefined.
3. The reported independence "within 5.8e-5 pu" concerned the minimum Pmax margin only. Over all unit P, Q and V outputs at t_e + 50 ms the controllers differ by up to 5.0e-4 pu (B1s) and 3.8e-4 pu (B2); both are about 20 times below the numerical band U_D8 = 0.0109 pu.
4. It was silent on the jump versus the later evolution: the jump is controller independent (Theorem A); the evolution is not.

**Setting.** After t_e, ẋ = F(x, u, d⁺), y = ψ(x, u, d⁺). Two controllers a, b share x(t_e⁺) and u(t_e⁺) (H-C, η dealt with in Corollary A.1) and satisfy |u^a_k(s) − u^b_k(s)| ≤ s w_k for s ∈ [0, T] (time from t_e⁺), with w_k = w^a_k + w^b_k, w^c the rate bound of controller c.

**Controller-specific rate bounds (PROVED from the laws; B2 and B1s with a stated dependence on the jump).**
- B5′, B4′: |v_k| ≤ v̄_k = 0.01·s_k by constraint (Q1), at every sample.
- B1s: v_P,i = k_i (1 − ω_i), with ω_i a state (continuous at t_e): |v_P,i(t)| ≤ k_i |1 − ω_i(t)| → 0 as t → t_e⁺. v_Q,i = K_IQ K_V (V_i(0) − V_i): V_i is algebraic and jumps, so |v_Q,i(t_e⁺)| = K_IQ K_V |V_i(0) − V_i(t_e⁺)| = K_IQ K_V |jump of V_i| (determined by Theorem A); then clipped to the box.
- B2 (original RDC): v = R(ω, P, Q, V, u) of `dec051_core.rdc_rates`; the P-, Q-, V-dependent terms jump with the algebraic outputs, so |v_k(t_e⁺)| = |R_k(post-jump outputs)| is computable from Theorem A; over [t_e, t_e + T] |v_k(t)| ≤ |v_k(t_e⁺)| + Lip(R)·‖ξ(t) − ξ(t_e⁺)‖. **No numerical bound is derived for B2**; the measured 50 ms maximum (0.9–6.27 × v̄ by component) is used as empirical rate bound and flagged.

**Theorem OS-L (PROVED for the linearised DAE).** Let (A, B, C_x, C_u) be the reduced matrices of the linearisation at the pre-event point (algebraic variables eliminated by g_y⁻¹): Δẋ = A Δx + B Δu, Δy = C_x Δx + C_u Δu, Δx(0) = 0. For |Δu_k(s)| ≤ s w_k,
 |Δy_j(T)| ≤ Σ_k w_k ( ∫₀ᵀ |[C_x e^{A(T−s)} B]_{jk}| s ds + |C_u,jk| T ).
*Proof.* Variation of constants gives Δy_j(T) = Σ_k ∫₀ᵀ [C_x e^{A(T−s)}B]_{jk} Δu_k(s) ds + [C_u]_{jk}Δu_k(T); apply |Δu_k(s)| ≤ s w_k. ∎ For the nonlinear plant the statement holds up to the linearisation remainder, which is **not bounded**.

**Theorem OS-N (PROVED-CONDITIONAL).** Suppose, on a set containing both trajectories on [0, T], ‖F(x, u) − F(x′, u′)‖ ≤ L_x‖x − x′‖ + L_u‖u − u′‖ and |H_j(x, u) − H_j(x′, u′)| ≤ ℓ_x‖x − x′‖ + ℓ_u‖u − u′‖ (H_j = h_j∘(x, ψ(x,u,d⁺), u)), and ‖Δu(s)‖ ≤ s W. Then
 ‖Δx(t)‖ ≤ L_u W (e^{L_x t} − 1 − L_x t)/L_x²,  |Δh_j(t)| ≤ ℓ_x ‖Δx(t)‖ + ℓ_u t W.
*Proof.* ‖Δx(t)‖ ≤ ∫₀ᵗ (L_x‖Δx(s)‖ + L_u s W) ds; Gronwall in integral form. ∎
**Status of the constants:** with the frozen linearisation of OC1/OC2 (208 dynamic states) the induced ∞-norms are L_x ≈ 2.9e4 s⁻¹, L_u ≈ 120, ℓ_x ≈ 314, ℓ_u ≈ 0; the bound overflows (e^{L_x T} with T = 0.05 s). **The norm-based nonlinear bound is vacuous**; certified Lipschitz constants over the visited region are not available.

**Numerical validation (NUMERICAL-ESTIMATE, no TDS; 18 controller pairs, 6 S2 cells, outputs P, Q, V of the 10 units at t_e + 50 ms).**
- The OS-L worst-case bound (B5′ vs B4′, B2, B1s) holds in 18/18 pairs; bound/observed maximum is 1.6–5.6 where the observed difference is non-negligible (B2 b39 cells, B1s cells) and much larger where it is ≤ 1e-5.
- The linear model driven by the actual command difference reproduces the observed output differences (e.g. 3.82e-4 vs 3.84e-4 and 2.46e-4 vs 2.47e-4 pu).
- Bounds: 0.8–1.8e-3 pu, below U_D8 = 0.0109 pu.

**Classification of OS.** (i) OS-L: PROVED for the linearised DAE, with a NUMERICAL-ESTIMATE of its matrices. (ii) OS-N: PROVED-CONDITIONAL, VACUOUS with norm constants; a useful nonlinear bound is **not demonstrated**. (iii) The empirical statement "the four controllers differ ≤ 5.0e-4 pu in unit outputs 50 ms after the event in six cells" is EMPIRICAL. The manuscript states (i)–(iii) separately; it does not claim a nonlinear bound.

## 3. Lemma C (centering)

**Statement.** Let ξ* satisfy (E1) (plant equilibrium for d⁺, anchored angle) and let the supervisory target be exact, ξ̂* = ξ*(d⁺) of the actual plant. Then v_nom(ξ*) = v_RDC(ξ*) − o = 0 with o = v_RDC(ξ̂*); v = 0, s = 0 is feasible for (Q1)–(Q4) (T1-F; (Q4) with equality), is the unique minimiser, and ξ* is a fixed point of the sampled loop.
**Audit (PROVED, with one added hypothesis).** The proof is correct. It needs *exactness of the target*: if ξ̂* ≠ ξ*(d⁺) (model mismatch, stale d), the offset o differs from v_RDC(ξ*) and the fixed point moves; robustness to mismatch is not covered. In all experiments E* is computed with the same ANDES model as the plant. The steady-state properties (ω = 1, unit voltages at the dispatch set-points, proportional P sharing outside the active set) hold by construction of E*; convergence to ξ* is not given by Lemma C (it is the object of T2 and of the simulations).

## 4. T1 (discrete reference invariance)

**Statement (PROVED).** If u₀ ∈ W, γ_k = α h_k ∈ (0, 1] and v_k satisfies (Q1)–(Q3), then c_j(u_k) ≥ ∏(1 − γ_i) c_j(u₀) ≥ 0. With feasibility of v = 0 (T1-F).
**Audit.** Correct; the induction is valid for a variable step h_k ≤ 1/α (the simulation uses dt = 2⁻⁸ s and dt/16 near the event). The disc row uses the second-order cone ‖u + hv‖ ≤ (s² − (1 − γ) c₅(u))^{1/2}. This is the discrete-time barrier condition c(u + hv) ≥ (1 − γ)c(u), standard in the sampled-data/discrete-time barrier literature (e.g. Breeden, Garg, Panagou, arXiv 2103.03677, whose full text was read), and the original RDC already keeps u in W by an inward-pointing vector-field argument (Kavvathas–Konstantopoulos 2025). **Classification:** discrete-time adaptation, not original in idea. **Open:** whether the centering offset o preserves the inward-pointing property of the original RDC; if it does, T1 is redundant in continuous time and only supplies the sampled/rate-bounded version.

## 5. T2 (local stability of the centered sampled loop)

**Statement (PROVED-CONDITIONAL).** Under (H1)–(H5): v* = v_nom on a neighbourhood N₁ (the QP rows are strictly satisfied), and the sampled centered loop converges exponentially, modulo the common angle, in N = N₁ ∩ N₂ at any rate above ρ_q.
**Audit.** The proof is the discrete indirect Lyapunov method plus QP inactivity; hypotheses H1 (root), H4 (spectral condition of the sampled map) and H5 (A_c) are verified in floating point, not certified; N is not quantified; T2 holds for the exact sampled system while the TDS uses the trapezoidal rule. Consistency with data: 42/42 targets verified; 36/36 B5′ runs are on the QP fast path after the last solver call (at most 4.29 s after the event); V(end)/V(first) ≤ 4.2e-4. **Attribution:** T2 is a property of the centered RDC; the QP and the CLF row are inactive on N by the proof. Whether ξ(t_e + τ_info) ∈ N is not certified.

## 6. P3 (classification)

N1 (capacity inequality; PROVED, elementary), N2 (Corollary A.2; PROVED), V (numerical local conditions; NUMERICAL), O (observed class; EMPIRICAL). **Audit:** the logical layering is consistent; V does not imply recovery (N unquantified); N1 was not exercised by any TEST cell; the empirically recovered set is not a certified recoverable set. P3 is a classification, not a certificate.
