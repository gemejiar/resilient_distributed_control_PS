# DEC-052 — H4-R conclusions (local stability of the DAE–RDC relative equilibrium)

Scope: plant C2t_Vsafe_R35_040, original B2 RDC, post-event Q+ relative equilibrium of DEC-051 (`IEEE39_DEC051_equilibrium_state.npz`). Static evaluation only; zero dynamic simulations. Software: Python 3.12.10, NumPy 2.5.4, SciPy 1.18.1, SymPy 1.14.0, ANDES 2.0.0, IEEE-754 binary64. Validation level of every number is stated; "validated" means first-order Higham floating-point error bounds on the computed matrices, **not** directed-rounding interval arithmetic.

## 1. Model (Block A) — GATE A: PASSED
* **PSS.** The ANDES IEEEST equations were extracted and the parameters substituted (A1…A6 = T1 = T2 = T3 = 0, lead-lag flags F2/LL1 = 1; T4 = 0.75 s, T5 = 1 s, T6 = 4.2 s, KS = −2, MODE 3). Symbolic solution (SymPy, exact): F1_y = F2_x2 = F2_y = LL1_x = LL1_y = sig, and LL2_x obeys T4·LL2_x′ = sig − LL2_x. The retained equations see the eliminated variables only through one entry per SG (LL2_x ← LL1_y, value 1), which is replaced by sig. Forced-row residuals are 0 at the equilibrium and at three perturbed points (1e-2). The unreduced ANDES block is singular (index-2 chain: smallest singular value 5e-15, 12 values below 1e-12 relative); the reduction yields a regular index-1 block. Twelve genuine PSS states (LL2_x, WO_x, six SG) are kept. sig ← te/(Sn/Sb) and vsout → vi of IEEEX1 are confirmed in the ANDES Jacobians.
* **Limit.** Equivalence holds on the constraint manifold for smooth trajectories; at an algebraic jump of sig the integrator produces an impulse in F1_x/F2_x1 that feeds no retained equation.
* **Symmetry.** 88 angle-like states (delta GENROU, delta REGF1, BusFreq L_y and WO_x) form the null vector. Shifting them and all 39 bus angles by 0.5 rad changes every ANDES residual by < 5e-13 (equilibrium and two perturbed points). Projection: S = I without the SG31 angle column; Qm = I − v e_pinᵀ without the SG31 row; Qm S = I exactly; reconstruction ξ = S e + ξ_pin v. In the basis [S v] the Jacobian is block triangular with M v = 0 (relative 2.5e-10), and eig(M)∖{0} matches eig(A_q) to 7.4e-9. The reduction removes exactly one direction and keeps the physical dynamics; a relative equilibrium with c = 1.249e-6 rad/s is consistent with F = c·v.
* **Algebraic block.** Dimension 456 (12 quasi-algebraic states + 444 algebraic variables), σ_min = 2.10e-3, κ₂ = 5.3e5 (235 after Ruiz equilibration), residual 6e-14. Nonsingularity of the computed matrix is validated (‖I − RK‖∞ + γ‖|R||K|‖∞ = 2.7e-10 < 1). This is a diagnostic/validation for the floating matrix, not a proof for the exact Jacobian.
* **Fidelity to the simulated system.** The 1000 s full-ANDES runs of DEC-051 (±0.02 pu along the slowest mode) agree with expm(A_q t)e(0) to 0.02–0.5 % of the scaled state norm up to 200 s, 1.0 % at 400 s and 1.5–1.6 % at 1000 s (both signs). The RDC replica reproduces the stored rates of the original run exactly (0.0 difference, DEC-051).

## 2. Jacobian (C1–C2)
* **Cause of the 1.7 % discrepancy found.** `e9h_predictor.build()` evaluates the RDC law at u0 = [st['pset'], st['qset']]. DEC-051's `load_eq()` rebuilt `st` from the pre-event state (largest error 0.249 pu in Qset) and never wrote the equilibrium references into it, so the capability factors g_P, g_Q were taken at the wrong point. With the references corrected the analytic ANDES assembly and the central-difference Jacobian agree to a Frobenius-relative 1.3e-7 (stale: 1.3e-3), and both give max Re λ = −2.3427e-3 s⁻¹, τ = 426.854 s, ζ_min = 0.07213. **The DEC-051 statement that the E9/E13/DEC-050 analytic assembly has entry errors up to 1.7 % is withdrawn (INVALIDATED).** E13 and DEC-050 call `build()` inside a live B2 replay where the references are the live ones; their remaining defect is the omission of the PSS states.
* **PSS effect** (same references): without PSS τ = 426.89 s, ζ_min = 0.07340; with PSS 426.85 s and 0.07213. Twelve modes carry PSS participation > 0.2; the slowest six have participation <= 2e-4 and the 7th and 8th 8e-4 and 4e-3.
* **Error bound δ_A: NOT_CERTIFIED.** A validated ‖E‖₂ needs interval/AD enclosures of the first and second derivatives of the 706 ANDES equations (compiled callables, no interval or AD backend installed), of the implicit elimination of the algebraic block, of the RDC law with positive parts and limiter logic, and of the finite-difference truncation and equilibrium-location errors. None is available. Step studies are only consistency checks: in the balanced coordinates below, ‖A(h) − A(10h)‖ = 8.7e-6, ‖A(h) − A(h/10)‖ = 2.9e-4 (rounding-dominated), ‖A_numerical − A_analytic‖ = 3.6e-4.

## 3. Root (Block B) — GATE B: ROOT_NUMERICALLY_VERIFIED
Quotient residual 5.07e-12 (recomputed now), algebraic residual 6.0e-14, quadratic final Newton steps, same root from two perturbed starts, nonsingular Jacobian. Newton–Kantorovich quantities in the scaled 2-norm: β = ‖A_s⁻¹‖ = 1.34e4, η = ‖A_s⁻¹F‖ = 1.22e-8 (root would lie within 1.2e-8 of z0), required Lipschitz constant of the Jacobian L ≤ 1/(2βη) = 3.05e3 (cond(A_s) = 6.0e8). L is not bounded: no validated inclusion of J(X) exists (same blocked operation as δ_A); high-precision arithmetic, step comparisons and sampling (ratios ≤ 160 in DEC-051) are excluded as substitutes. The elimination error of the inner solve (6e-14) is not enclosed in the interval sense. **Existence of the exact root remains NOT_CERTIFIED.**

## 4. Lyapunov (C3–C4)
`A_sᵀP + P A_s = −I + R0 + EᵀP + PE`; condition `‖R0‖₂ + 2‖P‖₂δ_A < 1`.

| Coordinates | ‖R0‖₂ upper bound | λ_min(P) ≥ | ‖P‖₂ ≤ | tolerable δ_A | certificate for the computed matrix |
|---|---|---|---|---|---|
| natural | 5.9e-6 | 6.2e-4 | 2.9e6 | 1.7e-7 | yes |
| DEC-051 scaling D (strategy 1) | 4.2e-5 | 5.7e-4 | 4.3e6 | 1.2e-7 | yes |
| balancing similarity, P recomputed (strategy 2) | 2.2e-9 | 1.0e-3 | 2.4e3 | **2.06e-4** | **yes** |

* P ≻ 0 and the bound on R0 are validated for the **stored floating matrices** (Cholesky shift test with Higham backward error, Frobenius bound with γ_{n+3}). Hence the computed A is Hurwitz with a Lyapunov certificate. Balanced coordinates: ‖A‖₂ = 2.27e3, complex stability radius r_C = 1.8e-3 (numerical, unvalidated); in the DEC-051 scaling r_C = 7.4e-5 (the matrix is far from normal there; strategy 2 removes most of that).
* The inequality for the **exact** Jacobian cannot be closed: δ_A is unavailable. Conditional theorem that is validated: if ‖Tb⁻¹(A − Â)Tb‖₂ < 2.06e-4, then A is Hurwitz. The empirical finite-difference uncertainty (8.7e-6 to 3.6e-4) is of the same order as that tolerance, so even an empirical δ_A would not close the margin comfortably; finite differences are insufficient and an exact/AD Jacobian would be required.
* Limits of the validation: no directed rounding; Â is the matrix computed by central differences from ANDES, not the derivative of the exact equations.

## 5. Indirect method and region (C5–C6) — GATE C
| Item | Status |
|---|---|
| Linear stability, numerical | **NUMERICALLY_SUPPORTED** (eigenvalues, two independent Jacobian assemblies, 2 full-ANDES runs) |
| Linear stability, rigorous, computed matrix | **certified** (validated floating bounds; not interval arithmetic) |
| Linear stability, rigorous, exact Jacobian | **NOT_CERTIFIED** (δ_A unavailable) |
| Nonlinear local exponential stability modulo the angle shift | **CONDITIONALLY_ESTABLISHED**; label `NUMERICALLY_SUPPORTED_LOCAL_STABILITY`. Conditions: root exists near z0 (not certified), algebraic block regular (computed matrix), field C¹ near z0 (142 switches inactive, margin 0.087), exact Jacobian within the Lyapunov tolerance (not certified) |
| Nonlinear local stability, rigorous | **NOT_CERTIFIED** (`RIGOROUSLY_CERTIFIED_LOCAL_STABILITY` not claimed) |
| Safe invariant region | **REGION_NOT_CERTIFIED** (no second-derivative bound; the 83 sampled directions are not a proof) |

The word PROVEN used in DEC-051 for H4-1/H4-2 is withdrawn; the replacement statuses are in the table. No global, regional-quantified or finite-step transient claim is made.
