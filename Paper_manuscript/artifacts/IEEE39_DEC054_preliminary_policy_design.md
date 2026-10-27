# DEC-054 — Preliminary design of an ex-ante robust preventive dispatch policy (SG–GFM, fixed B2)

**Status:** `DESIGN_ONLY` · authorisation "DEC-054 — diseño metodológico sin TDS" · branch `review/dec054-prospective-preventive-dispatch` (historical reference commit `04e082b`, immutable).
**Gate state:** `STOP_BACKUP_NOT_VERIFIED` is **maintained**. P0 is **not** approved, `BACKUP_VERIFIED` is **not** declared, P2/P3 are **not** started. **New TDS: 0 (ledger 0/48). No optimisation was run, nothing was implemented, no historical file or parameter was touched.**
**Nature of this document:** a pre-registration draft for scientific review. Every number below is either (a) taken from existing artefacts (cited), or (b) a *proposal* to be sealed in `IEEE39_DEC054_design_frozen.json` at P1 before any new TDS. Nothing here is a result.

---

## 0. What the repository already fixes (verified inputs, not assumptions)

| Fact | Value | Source |
|---|---|---|
| Plant | IEEE-39, 6 SG + 4 GFM (C2t), ANDES 2.0.0 RMS positive sequence, PSS IEEEST active; frozen B2 (original RDC), graph, gains, Sn, limits | DEC-052/053 |
| Manipulable by the ANDES executor | PV `p0` for 9 PV buses (SG30, SG31, SG33, SG35, SG38 and GFM32/34/36/37 are PV devices), PV/Slack `v0` (10 unit buses); Slack (bus 39, SG39) closes the active balance and losses; unit Q is a *consequence* of `v0` (power-flow PV rule). `Pn`, `Qn` of the RDC (weights `d_P=1/Pn`, `d_Q=1/(Qmax−Qmin)`) stay at the C2t values and cannot change | `e9b_variant.py`, `run_e9a_hocbf.vsafe_hook`, `IEEE39_E8_C2t_summary.json` |
| Decision space (physical) | `z = (p0 ∈ R^9, v0 ∈ R^10)` → 19 variables, plus AC states `y0` | derived from the above |
| Fast jump, SG31 (C2t, P+ 58.564 MW bus 4) | algebraic margin −0.0465 pu at `t=0+`; worst temporal −0.0699 pu | DEC-053 `reserve_attribution.json` |
| Slow excursion, SG35 | worst margin at ≈ 7.7–7.8 s | same |
| Historical R35_040 | δ=0.040 chosen by the investigator; weights from a TDS of the same event → **in-sample** | DEC-053 `reserve_replay.json` |
| Predictor transfer | library of bus 4 was optimistic at SG39 (−0.0600 pu) and GFM32 (−0.0366 pu) for bus 18 | `IEEE39_DEC053_reserve_validation.csv` |
| Sharing penalty of redispatch | P/Pn spread ≈ 4.2–4.4 % on R35_040 (0.9 % on C2t) | `IEEE39_DEC053_H2_metrics.csv` |
| Reduced model | DEC-052 model: 12 genuine PSS states retained, degenerate IEEEST chain eliminated exactly, quotient by the common angle shift (dim. 227), fidelity 0.02–1.6 % to full ANDES up to 1000 s; algebraic block 456×456 (σ_min 2.1e-3, κ 5.3e5) | `IEEE39_DEC052_model_audit.json` |
| Harness hazard | DEC-051 evaluated capability factors with stale `st['pset']`, `st['qset']` (1.7 % Jacobian error, 504 s artefact) | DEC-052 |
| Eligible load buses (static, existing scan) | 3, 4, 7, 8, 12, 15, 16, 18, 20, 21, 23, 24, 25, 26, 27, 28, 29, 31, 39 | `IEEE39_DEC052_H3_location_scan.csv` |

The historical rule is therefore **not** reused as a method: its receivers, weights, δ and excursion library use simulation output of the event they protect against (see DEC-053 spec §1).

---

## 1. Problem statement and information model

**Goal.** Compute, *before* any disturbance, one operating point `z` (dispatch + voltage set-points) such that the frozen B2-controlled plant keeps unit powers (and, secondarily, voltages) inside the case limits after any disturbance of a declared finite family `𝒟`, at minimum redispatch cost and bounded loss of power-sharing accuracy.

**Information available to the policy (ex-ante):** AC network and unit data and limits; the nominal pre-event dispatch `z_nom` (C2t) and loads; the RDC constants (`Pn`, `Qn`, gains, graph); the DAE model; the declared family `𝒟` (bus, type P/Q, amplitude, step at `t_e`); calibration data generated **only** on DESIGN/TUNE scenarios.
**Never used:** the realised test disturbance, any TDS of a PROSPECTIVE_TEST bus, any R35_040 weight or δ, the bus-4 excursion library as a bound for other buses.

**Taxonomy fixed in the protocol:** `AC_FEASIBLE_FOUND`, `NOT_FOUND`, `LOCAL_OPTIMUM_FOUND`, `FEASIBLE_POINT_FOUND`, `INFEASIBLE_NOT_DEMONSTRATED` (solver failure ≠ proof of infeasibility); `TDS_SAFE_OBSERVED`, `TDS_PHYSICAL_VIOLATION`, `TDS_NUMERICAL_FAILURE` (an integration failure proves neither AC infeasibility nor physical instability).

---

## 2. Mathematical formulation

### 2.1 Notation
Units `i ∈ 𝒰 = {SG30,SG31,SG33,SG35,SG38,SG39,GFM32,GFM37,GFM34,GFM36}` (system-base pu). `d = (b, κ, a)`: bus, kind `κ∈{P,Q}`, amplitude `a`; `d ∈ 𝒟`. `g_AC(z, y0)=0` pre-event power-flow + algebraic equations; `x⁻(z)` pre-event differential/quasi-algebraic state (including the 12 PSS states and the 20 RDC references at activation); `y⁻(z)` pre-event algebraic variables.

### 2.2 Decision variables
`z = (p0, v0)`, `p0∈R^9` (PV buses), `v0∈R^10`; `y0` solves `g_AC(z,y0)=0` (Slack P and all Q follow). Feasible set `𝒵_phys`: `p0_i ∈ [Pmin_i, Pmax_i]`, `v0_k ∈ [0.95,1.05]`, PF converges, TDS initialisation succeeds with residual `‖f‖,‖g‖ ≤ 1e-8`, flat pre-event drift criterion (§4.4).

### 2.3 Algebraic jump (instantaneous)
Differential states are continuous at `t_e` (`x⁺=x⁻`, no physical reset). The algebraic variables jump to `y⁺_d(z)` solving
`g(x⁻(z), y⁺, z, d)=0`  (regular: `g_y` nonsingular, DEC-052).
`ΔP^{jump}_{i,d}(z) = P_i(x⁻, y⁺_d(z)) − P_i(x⁻, y⁻(z))`, analogous `ΔQ`, `ΔS`, `ΔV` (signed, both directions).
Local sensitivities (finite perturbations bounded by the grid, never extrapolated): `∂y⁺/∂d = −g_y⁻¹ g_d`; `∂ΔP/∂z` by the implicit function theorem through `g_y⁻¹[∂g/∂z]` (finite-difference fallback). The jump is computed by the **nonlinear** algebraic solve, not by the linearisation.

### 2.4 Electromechanical excursion (after the jump) — no double counting
Predicted trajectory for `t ≥ t_e`:
`P̂_{i,d}(t;z) = P_i(0+) + D_{i,d}(t;z)`, with `D_{i,d}(0+)=0` by construction,
where `D` is the incremental output of the affine model of §3 started from `x⁺=x⁻` **after** the algebraic jump. The excursion is
`Ê_{i,d}(z) = max( 0, max_{t∈[t_e,t_e+T]} D_{i,d}(t;z) )`, `T=200 s`.
Thus the constraint adds `ΔP^{jump}` (nonlinear, exact algebraic) and `Ê` (dynamic, relative to `P_i(0+)`): the quantity already contained in the jump is excluded from `D` by the zero initial condition. `D` **includes** the RDC drift that the activation at `t_e` produces from a redispatched point (the RDC pulls references toward the `Pn`-proportional equilibrium); a drift-free variant (`D^{event} = D − D^{S0}`) is computed only as a diagnostic decomposition, because the plant that is simulated contains both.

### 2.5 Reserve constraints
`R_i(z) = Pmax_i − P_i⁻(z)`.
Upper side: `M^{P+}_{i,d}(z) = R_i(z) − ΔP^{jump}_{i,d}(z) − Ê_{i,d}(z) − ε^{P}_{i,d} ≥ 0`.
Lower side: `M^{P−}_{i,d}(z) = P_i⁻(z) − Pmin_i + min(0, ΔP^{jump}_{i,d}) − Ê^{−}_{i,d}(z) − ε^{P−}_{i,d} ≥ 0`, `Ê^−` the largest downward excursion.
`Q`, `S`, `V`: the same jump + excursion + ε margin structure **is imposed** only if the corresponding predictor passes its audit (§3.6); otherwise they are *explicit post-checks* (never advertised as guaranteed). `S` margin: `Smax_i − sqrt(P̂²+Q̂²)` evaluated on the joint predicted trajectory. Voltage band 0.95–1.05 pu: pre-event `V⁻_k(z)` as hard constraint; post-jump `V⁺_{k,d}(z)` from the algebraic solve as hard constraint; post-excursion `V` predicted and used as a check.
`ε^{•}_{i,d}` is calibrated per class on DESIGN/TUNE only (§3.5). Its historical value 0.00228 pu (jump discrepancy only) is **not** reused.

### 2.6 Objective
Predeclared, homogeneous for M0–M3:
`J(z) = C_red(z) + λ_P C^P_share(z) + λ_Q C^Q_share(z)`
* `C_red = Σ_i ((p0_i − p_nom,i)/Pn_i)² + Σ_k (v0_k − v_nom,k)²·w_v` (dimensionless; reported separately in MW and in pu of voltage). `Pn_i` the RDC weight, so the cost is expressed in the units the RDC itself uses. `w_v` fixed so that 0.01 pu of voltage costs as 1 % of Pn.
* `C^P_share = Σ_i Pn_i (P_i⁻/Pn_i − r)² / ΣPn`, `r = ΣP_i⁻/ΣPn_i` — the pre-event mismatch with the RDC's proportional-sharing target (the RDC weights cannot be changed, so the mismatch is *penalised*, not removed).
* `C^Q_share` likewise with `d_Q = 1/(Qmax−Qmin)`.
Economic cost is reported only if coefficients are justified from case data (none are available in the repository → not reported).
`λ_P, λ_Q` are chosen by a **predeclared rule** (not by test data): the smallest values on the grid `{0, 0.1, 1}` for which, on DESIGN, the predicted pre-event P-share spread is ≤ 5 % of Pn (the level observed on R35_040); evaluated with the static model only.

### 2.7 Robust problem (finite family, one common `z`)
`(P)  min_{z,y0} J(z)  s.t.  g_AC(z,y0)=0, z∈𝒵_phys, V⁻(z)∈[0.95,1.05], M_{i,d}(z) ≥ 0 ∀ i∈𝒰, d∈𝒟_W, class∈{P+,P−,(Q,S,V if audited)}`
with `𝒟_W ⊆ 𝒟_design` the working set of Algorithm 1. Non-convex (AC equations, implicit predictor): any solver output is `LOCAL_OPTIMUM_FOUND` or `FEASIBLE_POINT_FOUND`, never a global-optimum claim.

### 2.8 Sufficient safety condition — conditional (Proposition S)
*Hypothesis H_err.* For every `(i,d)` in the evaluated family: `ΔP^{jump,true}_{i,d} ≤ ΔP^{jump}_{i,d} + ε^{J}_{i,d}` and `E^{true}_{i,d} := sup_{t≥t_e}(P_i(t)−P_i(0+))⁺ ≤ Ê_{i,d} + ε^{E}_{i,d}`, with `ε = ε^J+ε^E`.
*Claim.* Under H_err, `M^{P+}_{i,d}(z) ≥ 0` ⇒ `P_i(t) ≤ Pmax_i` for all `t ≥ t_e`.
*Proof.* `P_i(t) = P_i⁻ + ΔP^{jump,true} + (P_i(t)−P_i(0+)) ≤ P_i⁻ + ΔP^{jump,true} + E^{true} ≤ P_i⁻ + ΔP^{jump}+Ê+ε ≤ Pmax_i`. ∎
*Scope.* Continuous-time statement for the true plant only if H_err holds; H_err is **not** proven (the predictor is linear, ANDES has limiter modes, `ε` is empirical). It is also restricted to disturbances in the family, step shape, horizon `T`, and the RDC/plant frozen configuration. Status of any outcome: at most `CONDITIONALLY_ESTABLISHED` for the proposition and `NUMERICALLY_SUPPORTED` for observations; never `RIGOROUSLY_CERTIFIED`.

---

## 3. Predictor design (DAE + PSS + consistent references)

### 3.1 Model
Reduced DAE of DEC-052 (index-1 elimination of the algebraic and quasi-algebraic variables; degenerate IEEEST chain eliminated exactly; 12 genuine PSS states kept; common-angle quotient), augmented with the 20 RDC reference states. Reuse as *read-only libraries*: `dec051_core.py`, `dec052_*.py`, `run_dec051_h3_jump.py`. No edit of historical modules; new code only in `dec054_*.py`.

### 3.2 Per-candidate consistency (precondition checks, before any prediction)
1. PF converges; TDS initialisation (`TDS.init`, **no stepping**) succeeds with `‖f‖,‖g‖≤1e-8`.
2. **References first:** set `st['pset']`, `st['qset']` to the candidate's *actual* initial RDC references (verified against `run_e8_ieee39` activation convention — open item **V1**) *before* building any Jacobian (the DEC-051 defect).
3. Relative drift `F(z)` of the pre-event plant is reported; the plant itself must be in equilibrium before activation (check `‖f_plant‖≤1e-8`); the RDC drift after activation is **expected non-zero** for `z≠Pn`-proportional and is modelled (affine term), never treated as an equilibrium.
4. Fixed-point test of Jacobian: analytic vs central difference ≤ 1e-6 relative (DEC-052 achieved 1.3e-7).

### 3.3 Incremental affine model
`δẋ = A(z) δx + f0(z) + B_d(z) d`, `δx(0+)=0`, outputs `δP_i = C_i δx + (D_i^y)·δy`, where `A, B` are the reduced closed-loop Jacobians at `(x⁻(z),y⁻(z))` with correct references, `f0(z)` the RDC/plant drift vector field at the pre-event point, `δy` obtained from the algebraic relation `δy = −g_y⁻¹(g_x δx + g_d d)`. The `D(t)` of §2.4 is `δP_i(t) − δP_i(0+)`, so that the jump (computed nonlinearly in §2.3) is not recomputed by the linear model. Time evolution through the eigen-decomposition/matrix exponential of `A(z)` on a fixed log-spaced grid refined around local maxima by Brent search; a maximum is not pre-assigned to any time (7.8 s is *not* assumed).

### 3.4 Validity monitor
Flags the candidate `MODE_CHANGE` if the predicted trajectory approaches a limiter active in ANDES (TGOV1N `VMAX/VMIN`, IEEEX1 `VRMAX/VRMIN`, REGF1 internal `Pmax/Qmax`), if amplitude exceeds the calibration range, or if the linearisation changes by more than a declared tolerance between `x⁻` and the predicted peak state. Flagged candidates are verified with ANDES on DESIGN/TUNE only and labelled; on PROSPECTIVE_TEST they are labelled `OUT_OF_CALIBRATION_DOMAIN` and **not** corrected after the fact.

### 3.5 Uncertainty treatment (empirical, ex-ante)
* Errors: signed `e^J = ΔP^{jump,ANDES} − ΔP^{jump}` (first sample after the event vs algebraic solve) and `e^E = E^{ANDES} − Ê`, per unit and class.
* Calibration set: only DESIGN/TUNE events; **out-of-sample inside the set** via leave-one-bus-out (LOBO) cross-validation (all amplitudes of a bus held out together). `ε^{J}_i, ε^{E}_i` = one-sided quantile of the LOBO errors at level `1−α` (proposed `α=0.10`; split-conformal rank rule `⌈(n+1)(1−α)⌉/n`) with a per-unit scale-normalisation by predicted magnitude to avoid pooling heteroscedastic errors. If `n < ⌈1/α⌉−1`, fall back to the maximum observed positive error plus a stated margin.
* Reported alongside: signed error, worst positive and negative error, observed coverage in LOBO. **Exchangeability across buses is not satisfied** (different locations); the quantile is therefore an empirical calibration, not a universal bound, and the coverage statement is nominal only.
* An out-of-domain score (range of `‖∂y⁺/∂d‖`, amplitude, distance to calibrated sensitivities) triggers `OUT_OF_CALIBRATION_DOMAIN`.
* Bus 4 and bus 18 may enter TUNE as *calibration/diagnostic* data (their results exist) but never as blind tests; the bus-4 library is **not** used as a bound elsewhere.

### 3.6 Predictor audit (Gate P2, before any policy claim)
Compare predicted vs ANDES (P3-A, ≤ 8 TDS, DESIGN buses) for SG31, SG35 and, if feasible, Q: jump error, excursion error, time of maximum. Accept a class (P, Q, S, V) as *imposed* only if its LOBO errors are bounded by the margin that the cost permits; otherwise degrade scope (Q/S/V → post-check, or P only). The first 8 TDS also include a limited integration-fidelity check (tolerance/step), which counts against the budget.

---

## 4. Algorithm

### 4.1 Algorithm 1 — multi-contingency policy with adaptive constraint separation (M3)

```
Input : 𝒟_design (fixed list), z_nom, unit data/limits, RDC constants, frozen seeds,
        calibrated ε (DESIGN/TUNE only), λ_P, λ_Q, tolerances (τ_cut = 1e-4 pu), K_max, N_it_max
Output: z*, status ∈ {LOCAL_OPTIMUM_FOUND, FEASIBLE_POINT_FOUND, INFEASIBLE_NOT_DEMONSTRATED},
        cut log, certificate-of-evaluation table (margins for ALL d ∈ 𝒟_design)

1  W ← initial working set: fixed subset 𝒟_0 ⊂ 𝒟_design (fixed by rule: most severe by the
        STATIC jump-only margin at z_nom; ties by bus number) – no TDS data
2  for k = 0 .. K_max:
3     z_k ← solve (P) with 𝒟_W = W, multi-start {z_nom, z_{k-1}, fixed Vsafe-like seed};
          report solver status; if no feasible start → go to 9
4     for every d ∈ 𝒟_design:            (including d ∉ W)
5         compute ΔP^jump_{i,d}(z_k) (nonlinear algebraic), Ê_{i,d}(z_k) (§3), margins M_{i,d}
6     v ← (i*, d*, class*, t*) = argmin margin over all (i,d,class)
7     if min margin ≥ -τ_cut: z* ← z_k; status ← LOCAL_OPTIMUM_FOUND (if solver KKT satisfied)
          else FEASIBLE_POINT_FOUND; break
8     W ← W ∪ {(d*, i*, class*)}  and log the cut (unit, class, event, instant t*, margin, validity, AC-feasible after cut?)
9  if loop ended without z*: status ← INFEASIBLE_NOT_DEMONSTRATED
       (distinguish: solver non-convergence | cut budget exhausted | AC infeasible *in the evaluated model*) ; relax via
       ℓ1 slack on margins (reported, never silently) and return the least-violating z with the violation vector
10 (P3-B only) dynamic verification cut: run ANDES on a DESIGN/TUNE event for z*; if the observed excess on any unit exceeds
       the predicted margin, add an additive correction δ_{i,d} ← max(0, observed_excess + τ_cut) to that (i,d) constraint
       (cut log: unit, restriction, event, instant, validity, AC feasibility) and repeat from 2 within the P3-B budget.
```
Convergence criterion: no violated margin over all `d ∈ 𝒟_design` within `τ_cut`; finite termination because `W` grows over the finite set `𝒟_design×𝒰×classes`. This is empirical verification on the *tested* events, **not** certification over a continuum of disturbances.

### 4.2 Comparators (identical plant, B2, topology, limits, demand, events, solver, horizon, objective `J`)
| ID | Definition | Constraints on reserve | Parameters selected on |
|---|---|---|---|
| M0 | AC-OPF minimising `J` (distance to `z_nom` + sharing mismatch), PF/limits only | none transient | — |
| M1 | M0 + static reserve `R_i(z) ≥ ρ_i`, with uniform `ρ_i=ρ` (pu of `Pmax`) or proportional to `Pmax_i−Pmin_i`; one parameter `ρ` | uniform/proportional | DESIGN/TUNE: smallest `ρ` meeting (a) equal cost to M3 and (b) separately, equal predicted DESIGN compliance |
| M2 | M0 + `M_{i,d}` with **jump only** (`Ê=0`, `ε=ε^J`) over `𝒟_W` | algebraic jump | same cut procedure |
| M3 | Algorithm 1 with jump + excursion + `ε^J+ε^E` + multi-contingency | proposed | DESIGN/TUNE |
| HIST R35_040 | the historical dispatch, labelled `RETROSPECTIVE_IN_SAMPLE`, never part of the blind comparison (no budget for it in the 24 TDS) | — | historical |

Equal-cost comparison: M1 is re-parameterised so that `J(z_M1)=J(z_M3)`; minimum-cost-for-equal-compliance: bisection on `ρ` (and on the constraint margin for M2/M3) over **static** predictions of DESIGN only; M3 is never given more reserve than the comparator it is compared with at that cost level.

### 4.3 Inputs/outputs and determinism
All seeds fixed and recorded; solver (SLSQP, as used by the project; interior-point only if installed and declared) and tolerances declared at P1; outputs: `z*`, status, `J` terms, per-unit reserves, margin table for every `(i,d,class)`, cut log, runtime.

### 4.4 Handling infeasibility and bad candidates
Candidates failing PF/initialisation or with unacceptable pre-event drift are rejected and reported (not retried indefinitely). A flat pre-event TDS drift limit (proposed `max|ẋ|≤1e-6` over the 5 s before activation, tested in the P3 runs, and by the initialisation residual statically) is predeclared. A TDS integration failure is `TDS_NUMERICAL_FAILURE`; it is stored and counts in the budget.

### 4.5 Expected complexity (asymptotic; actual times are to be measured, not asserted)
Per evaluation of `z`: PF + TDS initialisation (sparse, `O(n_y^{1.5})` typical for sparse LU, `n_y=456` block); `|𝒟|` algebraic solves (Newton, a few sparse factorisations each); one reduced linearisation (finite-difference parameter columns scale with the number of parameters, ≈ 20 + variables) and one dense eigen-decomposition `O(n_x³)` with `n_x=227` (≈ 1e7 flops); trajectory evaluation `O(|𝒟|·n_x·n_t)`. Gradient by finite differences: ×(19+1) evaluations per NLP iteration. The nominal total is `O(N_it · 20 · (|𝒟| · C_alg + C_lin))`; all of it is static (no TDS) and thus free of the 48-TDS budget.

---

## 5. Experimental design

### 5.1 Scenario family and partition (sealed at P1)
Family: P steps at `t_e=5 s`, amplitudes `a ∈ {0.5, 1.0}×58.564 MW`, and (if the Q module passes the audit) Q steps `a ∈ {0.5,1.0}×17.345 MVAr·(scale)`; horizon 200 s, `dt=2^-8 s`, same solver.
Eligible buses (static, existing scan, no TDS data from test buses): `{3,7,8,12,15,16,20,23,24,25,26,27,28,29}` after removing the buses with prior dynamic results (4, 18; 21 for Q+) and the two buses adjacent to the largest units (31 terminal of SG31, 39 the slack bus), which are extreme/trivial; **14 eligible buses** (to be re-derived and sealed at P1, with the criteria and the seed).
Deterministic split by bus (not by row): rank buses by `SHA-256(seed ‖ bus)` with a fixed seed written at P1; first **6** → PROSPECTIVE_TEST (the protocol asks for ≥ 4 unseen buses), next **4** → TUNE, remaining **4** → DESIGN; buses 4, 18, 21 enter TUNE as *calibration only*. Stratification rule fixed before ranking: the final test set must contain at least two scenarios for which M0 is **statically** predicted to violate on the jump alone and at least two for which it is not (to avoid a trivial or an uninformative cohort); if the hash split cannot meet it, fall back to the next ranks, and the fallback is logged.
Q scope: decided at P2 *before opening any prospective result* (protocol): Q module reliable → 4 P + 2 Q test scenarios; else 6 P and Q declared out of scope.

### 5.2 Budget mapping (48 TDS, a ceiling, not a target)
| Block | ≤ TDS | Use | Gate |
|---|---|---|---|
| P3-A | 8 | predictor audit on DESIGN buses (jump + excursion, SG31/SG35, P and Q if feasible) + limited fidelity check | predictor valid or scope degraded |
| P3-B | 16 | dynamic verification cuts and parameter fixing on DESIGN/TUNE only | policy frozen |
| P3-C | 24 | 6 test scenarios × M0–M3 | analysis only |
HIST R35_040 is **not** run in the blind cohort (it would exceed the 24); it stays as the retrospective reference.

### 5.3 Freezing and anti-leakage
Before the first P3-C TDS commit (Git) a frozen file: code hashes, ANDES version, DESIGN/TUNE/TEST partition and seed, `ε`, `λ`, working sets, M0–M3 dispatches, constraints and predictions. The test runner recomputes the hashes and aborts on any mismatch; it runs the four methods for the same event without reading other prospective outputs. Any post-hoc change to code/weights/scenarios invalidates the cohort (`TEST_INVALIDATED`; a new cohort needs a new authorisation). A bug discovered after opening → `TEST_INVALIDATED`, no re-tune/re-test on the same cases. Failed runs are never replaced.

### 5.4 Endpoints and acceptance (predeclared)
Primary: number of (scenario, unit) pairs with `P` exceeding `Pmax` (or below `Pmin`) at any stored sample, and total/maximum excess; secondary: Q/S/V violations (39 buses, [0.95,1.05]), `t=0+` vs later maximum, redispatch cost `C_red` (MW), `J`, minimum reserve per unit, P/Q sharing spread, nadir/zenith, RoCoF (filtered and unfiltered, both labelled; **plain mean of the 39 BusFreq is not a COI**; COI used only if inertia weights are extracted and documented), final frequency error, DAE residual, runtime.
`SUPPORTED` (policy-level, `NUMERICALLY_SUPPORTED` at most) only if **all**: (i) M3 is new w.r.t. R35_040 and uses only ex-ante data; (ii) on the sealed cohort M3 has no more violating scenario–unit pairs than each of M0, M1, M2 **and** at least one of: strictly fewer violations than the best comparator at equal cost, or equal (zero) violations with `C_red` at least 20 % lower than the cheapest comparator achieving zero in the same cohort; (iii) no unacceptable operational deterioration: voltage band respected, P-sharing spread not worse than the comparator at equal cost by more than 2 percentage points of Pn, no `TDS_NUMERICAL_FAILURE` attributable to M3 only. Anything else → `NEGATIVE_FINDING` reported in full; a 6/6 clean cohort is not universal safety (small sample; scenarios listed). Thresholds are proposals to be sealed at P1.

### 5.5 Ablations (static first; TDS only inside the 24)
* A1 M0→M2: value of modelling the algebraic jump.
* A2 M2→M3: value of excursion + multi-contingency. Separation by two static intermediates **not** run in TDS: M3a (single contingency + excursion), M3b (multi-contingency, jump only); their dispatches and predicted margins are compared with M2/M3; a TDS comparison only if budget remains in P3-C is not re-planned (the 24 are M0–M3 only).
* A3 M1→M3 at equal cost and at equal predicted compliance.
* A4 `ε` on/off and calibration source (jump-only ε vs full ε) — static.
* A5 predictor ablation: with/without drift term `f0`, with/without the correct references (replicating the DEC-051 hazard as a unit test).

---

## 6. Originality matrix (honest status)

Literature: the nine project references (abstracts read) plus classical areas named *without citations* because no external search was run in this authorisation. **Novelty is `NOT_ESTABLISHED`** until a systematic search is done.

| Component | Known / where | Possible contribution here | Falsifying experiment |
|---|---|---|---|
| Online distributed control with capability-curve invariance (B2; *Resilient Distributed Control … Capability Curve Requirements*) | known; used unmodified | none (kept as the fixed plant) | — |
| Online safety/projection (*CBF frequency control for networked microgrids*; *Multi-Slot Distributed Frequency Control*; *Distributed Coordination GFM/GFL*, projected primal-dual dynamics with capacity constraints; MPC with nodal frequency/RoCoF; DNN-projection DRL and physics-shielded/safe MADRL for voltage control) | known: online controllers/learning enforcing constraints | none; contrast class (online action vs offline preventive operating point) | not a comparison of controllers (B2 fixed); the original CLF–HOCBF stays out of scope |
| GFM/GFL stability conditions (*Quantitative Parameter Conditions … GFM/GFL*) | known small-signal results | none; GFL not in scope | — |
| AC-OPF, security-constrained OPF, constraint generation, dynamic-security OPF | classical (not searched) | the combination is not new in itself | — |
| Conformal / quantile calibration of a surrogate error | classical (not searched) | used as tool, not claimed new | LOBO coverage check |
| **C1** Reserve constraint that separates the *nonlinear algebraic jump at `t_e⁺`* from a *model-predicted electromechanical excursion* for a **fixed secondary controller** on a hybrid SG–GFM network with PSS | candidate | formulation + evidence that the two terms act at different times/units (fast SG31 vs slow SG35) | A2 and A1: M2 vs M3 vs M0 on unseen buses |
| **C2** Excursion predictor on the reduced DAE with the 12 PSS states, references corrected, drift term of the RDC and an explicit zero-initial-condition separation from the jump | candidate | removes the in-sample bus-4 library | P3-A predictor audit; A5 ablation |
| **C3** Ex-ante multi-contingency separation (finite-set constraint generation) with *explicit* penalty of the mismatch to the unmodifiable RDC weights `Pn` | candidate | quantified cost–security–sharing trade-off | Pareto in security–cost; compare M1 at equal cost |
| **C4** Leave-one-bus-out empirical error calibration with explicit loss of exchangeability and domain flag | candidate (tool known) | honest, location-aware margin | LOBO coverage on TUNE; test cohort errors signed |
| **C5** Conditional sufficiency (Proposition S) under bounded predictor error | elementary | clarity of what is and is not guaranteed | counter-example search is part of the cohort: any violation with `M≥0` falsifies H_err for that case |

---

## 7. Risks and threats to validity

| ID | Risk | Mitigation / declared limitation |
|---|---|---|
| R1 | Only 14 eligible buses; 6 test scenarios → no statistical power, ties likely | report as small-sample; descriptive/exact counts, no p-values as proof; scenarios listed |
| R2 | Predictor linearity vs ANDES limiters/saturations | validity monitor; ANDES verification on DESIGN/TUNE; test cases labelled, never patched |
| R3 | RDC drift for redispatch (pull toward `Pn`) not captured | drift term, check **V1**; ablation A5 |
| R4 | Non-convex OPF: local optima, solver sensitivity | multi-start with fixed seeds; status reported, no global claim |
| R5 | ε from few TUNE events (bus-4/18 inclusion) | LOBO + fallback to max error; nominal coverage only |
| R6 | Comparator unfairness (M3 given more reserve) | equal-cost and equal-compliance protocols; parameters fixed on DESIGN/TUNE |
| R7 | Information leakage: scan file computed with R35_040 values | used only for static eligibility; no TDS of test buses; stratification declared before ranking |
| R8 | Q module unreliable | scope decision before opening results |
| R9 | `TDS_NUMERICAL_FAILURE` at aggressive dispatches | counted; reported; no inference about physics/AC feasibility |
| R10 | Mismatch between RMS limits and real capability (OEL/UEL, converter current, SoC, EMT) | stated; `S` is not a capability curve |
| R11 | Backup not independent | blocker maintained; no P3 until resolved |
| R12 | Novelty claim unsupported | status `NOT_ESTABLISHED` pending literature search |

## 8. Falsifiable contributions (summary)
* **H-A** (jump matters): M2 has fewer predicted-and-observed Pmax violations than M0 on unseen buses where the jump dominates (SG31-type).
* **H-B** (excursion matters): M3 has fewer violations than M2 or equal compliance at lower reserve cost where the slow term dominates (SG35-type).
* **H-C** (cost): at equal compliance, M3 needs less redispatch (`C_red`) than M1; at equal cost, fewer violations.
* **H-D** (predictor): LOBO excursion error and observed coverage are reported; H_err is considered refuted for any test case with `M_{i,d} ≥ 0` and an observed violation.
Each can fail; failure is a `NEGATIVE_FINDING` with unchanged criteria.

## 9. Items to resolve *before* P1 (not done here)
V1: verify RDC reference initialisation/activation convention in `run_e8_ieee39.py` (read-only); V2: extract inertia weights if COI is desired; V3: verify which Q set-points are actually actuable (`v0` vs references); V4: decide seeds, α, `λ` grid, tolerances and thresholds in `IEEE39_DEC054_design_frozen.json`; V5: independent backup destination (P0); V6: external literature search for the originality claim.

## 10. Architecture (modules, to be created only after authorisation)
`dec054_data` (read-only loaders of historical series via absolute paths) → `dec054_acpf` (PF/TDS-init wrapper per candidate) → `dec054_jump` (algebraic solve, sensitivities) → `dec054_predictor` (reduced model, references, affine propagation, validity monitor) → `dec054_calib` (LOBO ε) → `dec054_opf` (M0–M3, Algorithm 1) → `dec054_runner` (frozen hash check, ledger-gated TDS) → `dec054_report`. Every output uses the `IEEE39_DEC054_*` prefix; large series go to an external exclusive directory.

## 11. Declaration
No TDS, no optimisation, no implementation, no modification of `main.tex`, models, controllers, cases, historical results, manifests or backups. `STOP_BACKUP_NOT_VERIFIED` stays in force; the document stops here for scientific review.
