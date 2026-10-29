# DEC-055 Protocol — Architecture B (frozen at G0)

Status: frozen at gate G0 (Lot L0, no TDS). Every later lot (L1 to L4) requires an explicit authorization from the investigator. `main.tex` is not modified.
Branch: `review/dec055-architecture-b`. Remote: `rdc` only.

## 1. Scientific contributions (architecture B)

| ID | Contribution | Evidence type | Not claimed |
|---|---|---|---|
| C1 | **Instantaneous post-event admissibility.** Within the class of bounded-rate controllers without resets or instantaneous actions, the state at t_e⁺ is an algebraic function of the pre-event state, and therefore of the dispatch (T-A). | Proposition (T-A). Jump map checked against the first stored sample. | Safety after t_e⁺. Exclusivity of redispatch as a preventive mechanism. |
| C2 | **Evaluated transient security** of the preventive dispatch M3 (algebraic jump + predicted excursion + empirical ε). | TDS on frozen, blind TEST cells. | Any invariance or certificate. ε has no proven coverage. |
| C3 | **Conditional local stability** of the post-event relative equilibrium of the DAE with the original RDC (T-B). | Lyapunov certificate of the computed Jacobian (floating point). Existence of the exact root and the exact-Jacobian error are not certified. | Regional stability, region of attraction, stability radius. |
| C4 | **Equilibrium feasibility classification** (T-C): AC feasibility, closed-loop RDC equilibrium and proven infeasibility kept separate. | Proposition + AC solves + ANDES PFlow/TDS.init verification. | PFlow convergence as proof of a closed-loop equilibrium. Solver failure as proof of infeasibility. |
| C5 | **Distributed SG–IBR coordination** with the original RDC: frequency restoration and P sharing. The contribution of the RDC requires the full factorial M0/M3 × B1/B2 (§6). | E8, DEC-050, DEC-053 and the B1 arm (deferred). | A distributed QP. Communication guarantees beyond what is tested. |
| C6 | **Obstruction analysis** of HOCBF/CLF on physical outputs (relative degree 3–4, jump, authority, stiffness). | E9-A…H, DEC-051/052. | Any closed-loop safety filter. |

## 2. Implemented physical constraints

Source: `IEEE39_DEC053_constraints_dictionary.csv`.

| Constraint | Status | In M3 design | In TDS evaluation |
|---|---|---|---|
| Pmin ≤ P ≤ Pmax (case data, system base) | APPROXIMATED. ANDES internal limits (TGOV1N VMAX, REGF1 Sn/100) are 1.1–2× looser. | Pre-event, jump and predicted excursion (+ε) | Every stored sample |
| Qmin ≤ Q ≤ Qmax (case data) | APPROXIMATED | Pre-event only | Every stored sample |
| √(P²+Q²) ≤ Sn/100 (injection apparent power, not a capability curve) | APPROXIMATED | Pre-event only | Every stored sample |
| 0.95 ≤ V ≤ 1.05 pu on all 39 buses | MODELLED | Pre-event, with a 0.005 pu margin | Every stored sample |
| Pset/Qset reference margins (RDC states) | MODELLED | — | Reported separately; never used as physical compliance |
| SG capability curves, OEL/UEL, field/stator thermal limits | NOT_MODELLED | — | No claim |
| REGF1 converter current, sub-cycle limiting | NOT_OBSERVABLE (RMS model) | — | No claim |
| BESS SoC / energy | NOT_MODELLED | — | No claim |
| Ramp rates, protections, unbalance | NOT_MODELLED | — | No claim |
| Compliance between stored samples | NOT_OBSERVABLE (dt = 2⁻⁸ s) | — | Classification on stored samples only |

## 3. Mathematical formulations (definitive)

**Setting.** The model is an index-one DAE: ẋ = f(x,y,u,d) and 0 = g(x,y,u,d).
- u = (Pset, Qset) are the reference states of the RDC.
- z = (p0 of the 9 PV units, v0 of the 10 unit buses) is the pre-event dispatch.
- The pre-event equilibrium is (x⁻, y⁻, u⁻) = Ξ(z, d⁻).
- The event is a step d⁻ → d⁺ of the P demand of one existing load at time t_e.
- The implemented constraints are h_j(x, y, u) ≥ 0, j ∈ 𝓘 (§2), and C(d) = {h_j ≥ 0 ∀j}.

### T-A — Instantaneous post-event admissibility

**Controller class 𝒦.** Controllers that act only through bounded reference rates v = u̇ ∈ [v_min, v_max], with no reset of x or u and no instantaneous (impulsive or algebraic) action at t_e. The original RDC (B2), the PI/consensus secondary (B1) and primary control belong to 𝒦.

**Hypotheses:**
- (A1) x and u are continuous at t_e. The event changes only d.
- (A2) There exists y⁺ with g(x⁻, y⁺, u⁻, d⁺) = 0 and det g_y(x⁻, y⁺, u⁻, d⁺) ≠ 0. y⁺ lies on the branch continued from y⁻ by the integrator's Newton iteration.
- (A3) Every h_j is continuous.

**Conclusion:**
1. By the implicit-function theorem, y⁺ = φ⁺(x⁻, u⁻, d⁺) is locally unique on that branch.
2. For every controller in 𝒦: h_j(ξ(t_e⁺)) = a_j(z, d⁺) := h_j(x⁻(z), φ⁺(x⁻(z), u⁻(z), d⁺), u⁻(z)).
3. ξ(t_e⁺) ∈ C(d⁺) if and only if a_j(z, d⁺) ≥ 0 for every j.
4. Corollary: within 𝒦, only the pre-event state (in particular the dispatch z) determines a_j. The condition a_j ≥ 0 is necessary for any invariance claim of C(d⁺) from t_e⁺ by a controller in 𝒦.

**Not claimed:**
- That redispatch is the only physically possible preventive mechanism. Load shedding, fast switching and instantaneous converter actions lie outside 𝒦 and are not analysed.
- Anything for ramps (y is then continuous), topology changes or limiter-mode changes.

**Use in M3.** M3 imposes a_j(z, d⁺) − ε_J ≥ 0 only for the design contingencies. For TEST contingencies, a_j(z, d⁺) is a verifiable prediction (§5), not a guarantee.

**Numerical verification of (A2) per cell:**
- Newton residual ≤ 1e-9 (THR.jump_newton_tol).
- σ_min(g_y) at the post-jump point ≥ 1e-8 (THR.jump_gy_min_sv), reported together with cond(g_y).
- Otherwise the cell is labelled `UNVERIFIED`.

**Comparison with the first TDS sample** (L3, per TEST run; `dec055_common.jump_vs_first_sample`):
- (i) Predict P⁺ = P(t_e⁺) by Newton (tolerance 1e-11, the same algebraic equations as ANDES, x and u frozen).
- (ii) Take the first stored sample with t > t_e (t = 5.00390625 s).
- (iii) Error e = sample − P⁺, per unit.
- (iv) **Acceptance:** max|e| ≤ 5e-3 pu (THR.jump_vs_first_sample_pu). Otherwise the cell gets `JUMP_VALIDATION_FAILED`.
- (v) **Attribution**, separate from acceptance:
  - The difference is attributed to the integrator only if a one-step replica reproduces the sample to 1e-6 pu. The replica takes one implicit-trapezoid step of the full nonlinear DAE from the same pre-event state, solved by Newton on the ANDES residual functions, and is executed only when an L3 run is authorized.
  - Otherwise the difference is `UNEXPLAINED`.
  - No attribution is made without that replica.

### T-B — Conditional local stability (three separate levels)

ξ* is a relative equilibrium of the reduced augmented DAE with the original RDC (quotient by the common angle; the leak k_ℓ gives a common angle rate of 1.25e-6 rad/s).

| Level | Statement | Hypotheses | Status label |
|---|---|---|---|
| L-a | The **computed** quotient Jacobian J_q is Hurwitz: there is P ≻ 0 with J_qᵀP + PJ_q ≼ −Q, checked in floating point with first-order error bounds and no directed rounding. | J_q as computed | `NUMERICALLY_VERIFIED_FP_BOUNDS` (never `RIGOROUSLY_CERTIFIED`) |
| L-b | An **exact root** of F_q exists near the computed point. | Newton–Kantorovich: needs L ≤ 3.05e3 (not bounded) | `ROOT_NUMERICALLY_VERIFIED` (residual ≤ 1e-10), **not certified** |
| L-c | **Nonlinear** local exponential stability of the reduced DAE at the exact root, modulo the angle shift (Lyapunov indirect method). | L-b, plus ‖J_exact − J_q‖ < δ_tol (2.06e-4 in balanced coordinates; not certified), plus regular g_y and all limiter switches inactive with margin | `CONDITIONALLY_ESTABLISHED` |

- L-a does not imply L-c.
- The radius is not quantified.
- Existing evidence: OC1/Q+ (DEC-051/052). This protocol adds one equilibrium per OC (L4, requires TDS).

### T-C — Equilibrium feasibility (three separate objects)

- **(C-i) AC feasibility.** There exists a static AC operating point of the post-event network with all implemented constraints of §2 (unit P, Q free).
  - Evidence: SLSQP solution with a 1e-6 interior margin, then **ANDES verification**:
    - PFlow at the solution set-points (tolerance 1e-10);
    - TDS.init without steps;
    - |g|∞ ≤ 1e-8;
    - all constraints recomputed from the ANDES state ≥ −1e-9.
  - Label `AC_FEASIBLE`. This proves the existence of a power-flow point at which the open-loop plant initialises. **It does not prove a closed-loop equilibrium.**
- **(C-ii) Closed-loop RDC equilibrium.** A relative equilibrium of the augmented DAE with the original RDC (differs from C-i by the leak and the sharing law).
  - Verified only by Newton on the closed-loop field (DEC-051 procedure, L4).
  - Label `RDC_EQ_VERIFIED`, available only for the T-B equilibria.
- **(C-iii) Proven infeasibility.** If Σ_i Pmax_i < P_load(d⁺), the set E_C(d⁺) is empty (losses ≥ 0, case P limits). Then no controller restores exact frequency with all constraints, because a limit of a trajectory staying in the closed set C would belong to E_C(d⁺).
  - Label `PROVEN_INFEASIBLE`.
- Any other outcome (solver failure, failed ANDES verification) is `AC_UNDETERMINED`.

## 4. Disturbances: feasibility × severity

- **Type:** P step on an existing PQ load at t_e = 5 s, horizon 200 s. Constant-power loads in PFlow and TDS. No load is added and the topology is unchanged.
- **Severities** (ΔP_ref = 0.58564 pu):
  - S1 = 0.5·ΔP_ref (confirmatory);
  - S2 = 1.0·ΔP_ref (confirmatory);
  - S3 = 1.5·ΔP_ref (**stress**, exploratory).
- **Promotion of S3:** an S3 cell becomes confirmatory only if, before any TEST TDS, all three hold: T-C = `AC_FEASIBLE`; the frozen M3 design of its OC is FEASIBLE_PREDICTED or LOCAL_OPTIMUM_FOUND with S3 in its design set; and T-A(M3) = `ADMISSIBLE`. Otherwise it is `STRESS_EXPLORATORY`.
- **Not simulated:** `PROVEN_INFEASIBLE` cells.
- **Exploratory only:** `AC_UNDETERMINED` cells.
- Q steps are outside the M3 claims.

## 5. Partitions and independence

| Set | Content | Use |
|---|---|---|
| DESIGN | Buses {8, 23, 28, 25} × S1–S3, per OC | Constraints of the static design (M0/M3) |
| TUNE | Buses {7, 20, 16, 24} × {S2, S3}, per OC (L2 TDS) | ε calibration, dynamic cuts, design verification |
| TUNE-OC1 (existing) | DEC-054 P3-A, P3-B (DESIGN/TUNE buses of DEC-054) | Provisional ε of the L0 designs |
| Seen, never TEST | DEC-054 TEST buses {3, 29, 15, 12, 27, 26}; historical buses 4 and 18 | Excluded from TEST; DEC-054 cohort is not evidence of this protocol |
| TEST | Buses {21, 31, 39} × S1–S3 × OC1–OC3 | Evaluation only, after G4 freeze |

**Declared exposures of the TEST buses** (`IEEE39_DEC055_test_bus_audit.json`):
- All three were screened algebraically by DEC-051/052 (static PF and post-jump), and a selection rule chose bus 18 among them.
- Bus 21 carried every earlier Q step, including the realisation of the RDC Q channel (DEC-032/034).
- None received a P-step TDS.

## 6. Factorial design and statistics

- **Full factorial (required for C5):** OC × bus × severity × {M0, M3} × {B1, B2}.
- **Scheduled:** {M0, M3} × B2. The B1 arm is `DEFERRED` until a later authorization, with the same frozen design.
- **Safety claim C2:** deterministic and per cell. A single violation by M3+B2 in a confirmatory TEST cell gives `SAFETY_CLAIM_REFUTED`, with the full list of refuting cells. No aggregate rate is used.
- **Comparison M3 vs M0:** paired, per cell (full tables).
- **Secondary inference:**
  - Exact one-sided sign test over the 9 (OC, bus) clusters, α = 0.05.
  - Conditional on this finite set of IEEE-39 conditions; no generalization.
  - Severities are nested within a cluster, and clusters share the network.

## 7. TEST locations

- **Eligible:** PQ buses with an existing load never stepped in P by a TDS: {21, 31, 39}.
- **Criteria:** jump sensitivity per unit (in particular SG31, SG35) and post-jump voltage change, computed statically at OC1 with M0. With three eligible buses, the criteria document coverage; they do not select.

## 8. Frequency metrics

- **f_COI** = 60·Σ M_i Sn_i ω_i / Σ M_i Sn_i over the 6 GENROU units (REGF1 excluded).
  - Caveat: SG39 has M = 100 s on 1199 MVA and dominates the weights (§11).
  - Recorded by `dec055_runner.coi_record`; the bit-for-bit regression is deferred to L1.
- **Mean BusFreq:** unweighted mean of the 39 BusFreq signals, labelled as such; never called COI.
- **Nodal frequency:** per bus, with worst-bus nadir and spread.
- **RoCoF:** least-squares slope of f_COI over [t_e, t_e + 0.1 s]. Nodal RoCoF is reported separately.
- **Restoration:** |f_COI − 60| ≤ 0.01 Hz at 120 s and 200 s.
- The DEC-054 series contain no ω: their COI cannot be computed.

## 9. Gates and stop rules

| Gate | Accept | Stop |
|---|---|---|
| G0 (L0) | Protocol, thresholds, partitions, cells, code, cases and hashes frozen and pushed to `rdc` | Missing element |
| G1 (L1, 5 TDS) | Flat run 20 s with drift ≤ 0.005 Hz and ≤ 1e-3 pu; init residual ≤ 1e-8; Δt/2 check; COI regression bit-for-bit on P/Q/V | Any failure: STOP in that OC |
| G2 (static) | M3 design FEASIBLE_PREDICTED or LOCAL_OPTIMUM_FOUND on DESIGN; I(z) ≤ 1e-9 | Otherwise no TEST for M3 in that OC (cells registered as excluded) |
| G3 (L2, 24 + ≤ 8 TDS) | No TUNE violation by M3; predictor errors within ε | One declared dynamic-cut round; if a violation persists: STOP in that OC |
| G4 | `IEEE39_DEC055_design_frozen.json` (all OCs, one dispatch per method and OC, hashes) committed **before** any TEST TDS; T-A labels and S3 status recomputed with the frozen dispatches and frozen into the cell registry | — |
| G5 (L3, 18 TDS per OC) | Runs stored before the ledger is completed; no retries | (a) Numerical failure → `TDS_NUMERICAL_FAILURE`, STOP the lot. (b) M3+B2 violation in a confirmatory cell → `SAFETY_CLAIM_REFUTED`, the lot finishes unchanged and the refutation is reported first. (c) Jump error > 5e-3 pu → `JUMP_VALIDATION_FAILED`. (d) Protected hash changed or budget exceeded → STOP all. |
| G6 (L4, 6 TDS) | Root residual ≤ 1e-10, J_q Hurwitz, P ≻ 0 within FP bounds | Unstable mode → T-B refuted for that OC |

Human approval is required between G1, G3, each G5 lot and G6.

## 10. Budget

| Lot | Content | TDS |
|---|---|---|
| L0 | Static | 0 |
| L1 | Flat runs OC1–OC3 at the M0 dispatch of each OC (200 s, drift judged on the first 20 s and reported for 200 s) + COI-recording regression (re-run of the stored DEC-054 configuration P3B2_b7P_M3 with the DEC-055 runner and the DEC-054 PFlow tolerance 1e-6 so that only the recording differs; P/Q/V compared bit for bit with the stored series) + Δt/2 run of the same configuration (first 20 s compared with the stored dt run; AC-04 tolerances: nadir 1 %, V 0.005 pu, P 0.005 pu) | 5 |
| L2 | TUNE: 4 buses × {S2, S3} × 3 OC + ≤ 8 for dynamic cuts | 24 (+8) |
| L3 | TEST: 3 buses × 3 severities × {M0, M3} × B2 per OC | 54 |
| L4 | T-B: one 2000 s run + one validation per OC | 6 |
| **Total initial programme** | | **89 (max. 97)** |
| Later (separate authorization) | B1 arm 54; communication 8–12; sensitivity 16; M1 equal-compliance 27 | |

## 11. Declared discrepancies found in L0

- **D1.** The ANDES default PFlow tolerance (1e-6) left |g| = 1.13e-8 at the OC2 reference point, above the 1e-8 validity threshold. DEC-055 sets the PFlow tolerance to 1e-10 for all OCs (recorded attempt: `init_attempt1_pflow_tol_1e-6.json`).
- **D2.** The pre-event reference points (case dispatch) violate the 0.95–1.05 band: OC1 has 21 buses above 1.05 (max 1.0730), OC2 has 29 (max 1.0817) and OC3 has 13 (max 1.0644). The band is enforced only on the OPF dispatches (M0/M3).
- **D3.** SG39 dominates f_COI (M·Sn share computed in the G0 report). f_COI is therefore close to the SG39 speed.
- **D4.** Bus 39 is the PFlow Slack and SG39 terminal: a step there is taken almost entirely by SG39 (weak test of SG31/SG35). Bus 31 is the SG31 terminal (strong test).
- **D5.** The provisional M3 designs of OC2/OC3 use the OC1 ε (TUNE-OC1). ε is recalibrated in L2 before G4.
- **D6.** The first M3 design of OC3, with the DEC-054 operational SLSQP budget N_it = 25, ended as SOLVER_FAILED ("Iteration limit reached"; kept as `m3_OC3_attempt1_Nit25_SOLVER_FAILED.json`). The design was repeated with the declared PROPOSED budget N_it = 200 (same seeds, objective, constraints and ε). This is a numerical budget, not a model or criterion change. No TEST information exists at this point. OC1 and OC2 converged with N_it = 25 and are not repeated.
