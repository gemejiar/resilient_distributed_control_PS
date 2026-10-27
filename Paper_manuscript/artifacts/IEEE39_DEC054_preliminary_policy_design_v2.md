# DEC-054-R1 — Preliminary design v2 of an ex-ante robust preventive dispatch policy (SG–GFM, fixed B2)

**Status:** `DESIGN_ONLY` · supersedes **v1** (`IEEE39_DEC054_preliminary_policy_design.md`, kept intact as audit evidence) · branch `review/dec054-prospective-preventive-dispatch` · starting commit `20650745be4da506b043824f2599dc27b526ef7f`.
**Gate state:** `STOP_BACKUP_NOT_VERIFIED` maintained (`independent_backup_verified=false`; the 1,026 MB copy is on the same disk). P0/P1/P2/P3 **not** approved. **TDS 0/48. No optimisation, ANDES initialisation, TDS or implementation was run.** The only computation done for this revision is read-only NumPy post-processing of already stored arrays (item F-1 below) and hashing for the provisional partition (§5.1).
**Section numbering follows v1.** Corrections are tagged `[R1-n]`; open points `UNRESOLVED` / `TO_VERIFY_IN_P2`. Every number is either cited from an existing artefact or is a *proposal* to be sealed at P1.

---

## 0. Verified facts and corrections to v1

| Fact (verified in code, path:lines in `Paper_manuscript/src/`) | Consequence |
|---|---|
| `run_e8_ieee39.py:141-143` (and `run_b3_ieee39.py:91-92`, `dec051_core.py:94,102`): at TDS initialisation `pn = Pe(0)`, `qn = Qe(0)` of the **candidate's** state, `pset(0)=pn`, `qset(0)=qn` | `Pn,Qn` are **not constants of the RDC**; they equal the pre-event physical outputs of each candidate `z` **[R1-1]** |
| `run_e8_ieee39.py:148-152` (`run_b3:95-99`, `dec051_core:97-100`): `gp0,gq0 = capability_factors(pset, qset, lim)`; `gref_p = max gp0`, `gref_q = max gq0`; `k_ip = 160 / Σ(gp0/gref_p)` | `gref`, `k_ip` and the **effective per-unit integral gains** `k_ip·gp_i/gref_p` are recomputed from the candidate → reserve `Pmax−P⁻` and `Q` position set the integral action (`capability_factors`, lines 77-85: `box_p=(Pmax−pset)(pset−Pmin)`, circle `1−(P²+Q²)/Smax²`, SG `box_q`) **[R1-1]** |
| `run_e8:153` `d_p = 1/pn` (depends on `z`); `run_e8:154` `d_q = 1/(Qmax−Qmin)` (**fixed**: case limits only, not a function of `qn`) | correct the v1 statement; `d_P(z)` moves, `d_Q` does not **[R1-1]** |
| `run_e8:164-166`: capability factors are evaluated at every callback with the current references; the reference **update** (`pset += dt·dpset`, `qset += dt·dqset`, lines 170-173) happens only if `t ≥ EVENT_TIME_S = 5 s` | RDC *integrators* start at `t_e`; before `t_e` `pset=pn` |
| `run_e8:175-181`: actuator maps `TGOV1N.paux0 = (pset−pn)[SG]`, `REGF1.Paux0 = KC·(y0+(pset−pn)[GFM]−PIplim_y)`, `IEEEX1.vref0 = vref0 + clip(KAPPA·(qset−qn), ±Z_CLAMP)`, `REGF1.Qaux0 = KCQ·(y0q+(qset−qn)[GFM]−PIqlim_y)` are written at **every** callback (also `t<t_e`, where `pset−pn=0`) | the actuators see references **relative to `pn(z)`, `qn(z)`** |
| Update law (`run_e8:167-173`, `dec051_core.rdc_rates` 109-120): `dpset = k_ip(gp(1−ω) − K_P·Lp(d_p·P)) − K_LEAK(pset−pn)`; `dqset = K_IQ(K_V gq(V_REF−V) − K_Q Lq(d_q·Q)) − K_LEAK(qset−qn)`; explicit Euler with `dt=h=2^-8 s` using the quantities read at that callback | sharing consensus acts on `P_i/pn_i(z)`: its native target is **proportional to each unit's own pre-event output**; the leakage pulls `pset` to `pn(z)` (the *candidate's* pre-event point), **not** to a historical dispatch **[R1-1]** |
| `run_e9b0_variant.py:49-61`, `e9b_variant.py`: the hook (PV `p0`, `v0`) is applied **before** `PFlow.run()` and `TDS.init()`, so `pn,qn,k_ip,gref` are computed on the hooked state | the historical R35_040 runs already used `pn(z)`, not C2t `Pn` |
| Stored series (read-only check, F-1): B2 runs on R35_040 store `unit_pn` equal to the pre-event P (max diff 1.7e-13) and different from the C2t vector | confirms the previous row |
| **F-1 correction of a DEC-053 interpretation** (see §0.1) | DEC-053's "≈4 % sharing spread / Pn not updated" is a **metric-definition mismatch**, not an RDC property **[R1-1]** |

### 0.1 F-1 — the DEC-053 sharing figure (non-retroactive correction; no DEC-053 file was edited)
`dec053_core.py:138-139,147` normalised physical `P` and `Pset` by the E8 vector `unit_pn` (the **C2t** `pn`) for *every* run, including the R35_040 runs, whose own `pn(z)` equals their pre-event `P`. The statement "P/Pn spread ≈ 4.2–4.4 % on R35_040 because the RDC weights Pn were not updated" (DEC-053 report §4, claim F04, gap G7) is therefore **withdrawn as an attribution**. The numerical value computed against the C2t vector is a true property of *that* metric, but it does not measure RDC sharing accuracy on R35_040. Read-only recomputation from the stored arrays (200 s window, last 5 s): `ptp(P/pn(z)) = 0.0028` on R35_040 P+ (vs `0.0094` on C2t P+; `Pset/pn(z)` spread `0.0026`; `max|Pset−pn(z)|=0.082 pu`). Status `VERIFIED_READ_ONLY` as an arithmetic fact about stored series; its causal reading (e.g. effect of capability factors/leakage) is **UNRESOLVED**, not to be investigated with TDS now.

---

## 1. Problem statement and information model

**Goal.** Compute, before any disturbance, one operating point `z` such that the frozen B2-controlled ANDES plant keeps unit powers (and secondarily voltages) inside the case limits after any disturbance of a declared **finite** family `𝒟`, at limited displacement cost and with a declared participation pattern.

**Ex-ante information:** network and unit data/limits; the historical reference dispatch `z_ref` (C2t case data) and loads; the DAE model; the RDC *code* (gains, graph, constants) — **not** `pn,qn,k_ip,gref`, which are functions of the candidate (below); the family `𝒟`; calibration data from DESIGN/TUNE scenarios only.
**Never used:** the realised test disturbance or any TDS of a PROSPECTIVE_TEST bus; R35_040 weights/δ; the bus-4 excursion library as a bound elsewhere.
**Taxonomy:** `AC_FEASIBLE_FOUND`, `NOT_FOUND`; `TDS_SAFE_OBSERVED`, `TDS_PHYSICAL_VIOLATION`, `TDS_NUMERICAL_FAILURE` (an integration failure proves neither AC infeasibility nor physical instability; `TDS_SAFE_OBSERVED` is a statement about stored samples at `dt=2^-8 s`, never continuous-time safety).

### 1.1 Initialisation map `I(z)` [R1-1]
`I(z) := ( x⁻(z), y⁻(z), pn(z), qn(z), gref_p(z), gref_q(z), d_p(z), d_q, k_ip(z), u⁻(z), y0(z), y0q(z), vref0(z) )`
* `pn(z)=Pe⁻(z)`, `qn(z)=Qe⁻(z)` (from `y` at `TDS.init`; for the SG39/Slack unit too);
* `u⁻(z)=(pset⁻,qset⁻)=(pn(z),qn(z))` — the 20 RDC references at activation;
* `gp0(z), gq0(z) = capability_factors(pn(z), qn(z), lim)`; `gref_p(z)=max gp0`, `gref_q(z)=max gq0`; `k_ip(z)=160/Σ(gp0/gref_p)`; `d_p(z)=1/pn(z)`; `d_q = 1/(Qmax−Qmin)` (fixed);
* `y0(z)=PIplim_y`, `y0q(z)=PIqlim_y` of the four GFM; `vref0(z)=IEEEX1.vref0` of the six SG at initialisation.
All of `I(z)` are recomputed for each candidate and **passed to every Jacobian** `A⁺(z), C⁺(z), f⁺(z)` (the DEC-051 stale-reference hazard, repeated here as a design rule).

### 1.2 Documentary logic tests (not executed; to be run in P2 only)
(i) `pn(z)=P⁻(z)`, `qn(z)=Q⁻(z)` under the code's measurement convention: **confirmed by code reading** (`run_e8:141-142`), numerically confirmed on stored data (F-1). (ii) `pset(t_e⁻)=pn(z)`, `qset(t_e⁻)=qn(z)`: confirmed by code (`run_e8:143`); no other initialisation was found. (iii) `k_ip(z)` and the capability factors depend on `z` and enter `f⁺`, `A⁺`: **design requirement**. (iv) positivity of `pn`, interior of capability (`gp0,gq0>0`), no division by zero: the code **raises** `RuntimeError` if `gp0≤0` or `gq0≤0` (`run_e8:149-150`); `d_p=1/pn` requires `pn_i>0` (a GFM with `P⁻≈0` would blow up `d_p`): to be added as hard constraints `P⁻_i ≥ P_floor` in the OPF (`P_floor` to be sealed, proposal 0.05 pu), and `qset` strictly inside `(Qmin,Qmax)` for SG (`box_q>0`). (v) the SG39/Slack output is not a free `p0` variable (the Slack closes the active balance) but is a unit of `𝒰`: its `P⁻,Q⁻`, limits, `pn`, `gp`, margins and metrics are part of every constraint and metric (case values: Slack `Pmax=11.0 pu`, `Qmax=5.7485`, `Qmin=−1.7326`).

### 1.3 Event/activation timing — TO_VERIFY_IN_P2
Code facts: the `Alter` load event is scheduled at `EVENT_TIME_S=5 s` (`run_e8:98`); the reference update is gated by `t ≥ EVENT_TIME_S` (`run_e8:166`); the callback `rdc` is invoked from `TDS.callpert` once per integration step with explicit-Euler reference integration of step `h`; the callback reads `dae.y` at its call time. **Not determined from the code:** whether, at the step where `t=5.0`, the callback sees `y` before or after the algebraic re-solve that includes the load change, i.e. whether the first reference increment uses pre- or post-event measurements. `UNRESOLVED / TO_VERIFY_IN_P2` (by reading ANDES `TDS` event/callpert order in the installed package and a unit test on stored series, not by assumption). The continuous-time model below neglects (a) the Euler discretisation and (b) this one-step ordering; both are listed as predictor error sources, to be bounded in the P3-A audit.

---

## 2. Mathematical formulation

### 2.1 Notation
`𝒰={SG30,SG31,SG33,SG35,SG38,SG39,GFM32,GFM37,GFM34,GFM36}` (system-base pu); `d=(b,κ,a)`; `𝒟` finite. `ξ=(x,u)`: reduced differential/quasi-algebraic state `x` (12 genuine PSS states, DEC-052) plus the 20 RDC references `u=(pset,qset)`; common-angle quotient understood.

### 2.2 Decision variables and feasible set
`z=(p0∈R^9, v0∈R^10)` (hypothesis, to be confirmed; see §2.2.1). `y0` solves `g_AC(z,y0)=0`. Feasible set `𝒵_phys` (**the same for M0–M3**): `Pmin_i ≤ p0_i ≤ Pmax_i` (PV); **Slack** `P_slack ∈ [Pmin,Pmax]`, `Q_slack ∈ [Qmin,Qmax]`; all unit `Q⁻_i ∈ [Qmin_i,Qmax_i]`, `S⁻_i ≤ Smax_i`; `0.95 ≤ V⁻_k ≤ 1.05` on **all 39 buses**; PF converges; nodal balance and losses by the AC solution; `P⁻_i ≥ P_floor`; `gp0,gq0>0`; TDS initialisation succeeds (residual criterion on the correct equations, §2.2.2).
#### 2.2.1 What is actually actuable [R1-6]
`p0` (9 PV devices) and `v0` (PV/Slack voltage set-points). Unit `Q⁻` is **not** a free reactive dispatch before the event: it results from the AC balance given `v0`. The dynamic Q actuation is only through the B2 maps `IEEEX1.vref0` and `REGF1.Qaux0` driven by `qset−qn`. No independent "Q dispatch" variable exists without an additional actuator, which is out of scope. The Q constraints are therefore *consequences* of `v0,p0`.
#### 2.2.2 Residual conditions [R1-6]
Pre-activation: plant/DAE residual `‖f_plant‖_∞, ‖g‖_∞ ≤ 1e-8` at `TDS.init` (the plant must be in equilibrium before `t_e`). The RDC rate `v_RDC` is **not** required to vanish (the loop is inactive before `t_e`; after activation it acts and its non-zero value is part of the predicted drift `f⁺`, §3). Residual transients present before `t_e` are checked on the stored init; `UNRESOLVED` whether ANDES initialisation leaves non-trivial dynamic residuals at the GFM `PI` states (to be measured in P2, not assumed). `V` set-point `v0` and physical voltage `V⁻` are distinct: the constraint is on `V⁻`.

### 2.3 Algebraic jump
Differential states and references continuous (`ξ⁺=ξ⁻` in `x,u`, no reset); algebraic variables jump: `g(x⁻, y⁺_d, u⁻, z, d)=0` (regular `g_y`; DEC-052's `σ_min=2.1e-3` is a property of *that* case, **not** a uniform guarantee: regularity is checked per `(z,d)`, per branch, with `σ_min` and condition number recorded; a candidate with `σ_min` below a sealed threshold is rejected and reported).
`ΔP^{jump}_{i,d}(z)=P_i(x⁻,y⁺_d)−P_i(x⁻,y⁻)` and analogous `Q,S,V`. Computed by the **nonlinear** algebraic solve. Sensitivities `∂y⁺/∂d=−g_y⁻¹g_d` are local; finite changes are bounded by the evaluation grid.

### 2.4 Hybrid event/control model and predictor anchored at `0⁺` [R1-2]
At `t_e` two things happen simultaneously: the electrical disturbance and the **enabling of the RDC update** (`run_e8:166`). Three objects:
* `ξ⁻(z)`: coherent pre-event condition (PSS, actuator states, `u⁻=(pn(z),qn(z))`).
* `ξ⁺_d(z)=(x⁻,u⁻)` with algebraic `y⁺_d` from §2.3. **Differential states and references are continuous**, so the post-jump point is `ξ_0:=ξ⁺_d(z)`.
* `ξ_d(t;z)`, `t>t_e`: evolution under the **post-event field** `F⁺_d`: reduced DAE with the post-event load `d` and the **RDC active**, algebraic variables eliminated on the post-event branch: `ẋ = f(x,y(ξ;d),u)`, `u̇ = v_RDC(ξ,y(ξ;d); I(z))`, `y(ξ;d)` solving `g(x,y,u,z,d)=0`.
**One single formulation (no duplication of the jump):**
`δξ̇ = A⁺_d(z) δξ + f⁺_d(z)`, `δξ(t_e⁺)=0`,
`A⁺_d = ∂F⁺_d/∂ξ |_{ξ_0}` (with `∂y/∂ξ=−g_y⁻¹g_x` evaluated at the post-event point), `f⁺_d = F⁺_d(ξ_0;z)`,
`P̂_i(t;z,d) = P_i(ξ_0;z,d) + C⁺_{i,d}(z) δξ(t)`, `C⁺_{i,d}=∂h_i/∂ξ − (∂h_i/∂y) g_y⁻¹ g_x` at `ξ_0`.
There is **no `B_d d` term**: the event enters only through the post-event branch (`g(…,d)`), the jump and the forcing `f⁺_d`. `f⁺_d` contains (i) the plant transient forcing at the post-jump point (derivative of the plant states right after the algebraic jump) and (ii) the RDC rates `v_RDC(ξ_0;I(z))`, i.e. the drift caused by the activation (leakage `−K_LEAK(pset−pn)` vanishes at `ξ_0`; the consensus, frequency and capability-factor terms do not).
`D̂_i(t)=P̂_i(t)−P̂_i(t_e⁺)=C⁺_{i,d}δξ(t)`, `D̂_i(t_e⁺)=0`.
`Ê⁺_{i,d}=max_{t∈[t_e,t_e+T]} max(0, D̂_i(t))`, `Ê⁻_{i,d}=max_{t}max(0,−D̂_i(t))` (downward), `T=200 s` (evaluation horizon, **not** infinity; the slowest closed-loop time constant seen is 427 s).
*Alternative (pre-event linearisation), if later preferred:* `δξ̇ = A⁻δξ + B_d d` with output `P_i⁻ + ∂h/∂ξ δξ + (∂h/∂d)d`, whose value at `0⁺` is the **linear** jump; to avoid double counting the jump must then be taken from the nonlinear solve and `D̂` from the *difference* `P̂(t)−P̂(t_e⁺)` of that same linear model. It is **not** mixed with the post-event form.
*Sources of predictor error (declared, to be bounded in the P3-A audit):* linearisation error (including limiter mode changes: TGOV1N `VMAX/VMIN`, IEEEX1 `VRMAX/VRMIN`, REGF1 internal limits, `clip` of `z` at `Z_CLAMP=0.10`), **fixed `A⁺` over 200 s** (references move up to ≈0.08 pu, which changes the capability factors and therefore the effective gains; optional piecewise-affine re-linearisation at predeclared checkpoints, chosen in P3-A before P3-B), Euler discretisation and callback ordering (§1.3), time-grid maximum, matrix-function error.
*Not reused:* the DEC-052 spectrum of the Q+ equilibrium is **not** a model of other dispatches/events; `A⁺_d(z)` is rebuilt per candidate and event.

### 2.5 Reserve constraints (horizon-limited)
`R_i(z)=Pmax_i−P⁻_i(z)`.
Upper: `M^{P+}_{i,d}(z)=R_i(z)−ΔP^{jump}_{i,d}(z)−Ê⁺_{i,d}(z)−ε^{J}_{i,d}−ε^{E}_{i,d} ≥ 0`.
Lower: `M^{P−}_{i,d}(z)=P⁻_i(z)−Pmin_i+min(0,ΔP^{jump}_{i,d})−Ê⁻_{i,d}(z)−ε^{J−}_{i,d}−ε^{E−}_{i,d} ≥ 0`.
`Q`, `S`, `V`: each uses its **own physical output** `Q̂_i(t)`, `Ŝ_i(t)=√(P̂_i²+Q̂_i²)` (from the same affine model), `V̂_k(t)`; **no** sum of separately maximised `P` and `Q` excursions is used to bound `S` (their maxima occur at different times). They are *imposed* only if the corresponding predictor passes the P3-A audit; otherwise explicit post-checks, never advertised as guaranteed.
`ε` terms: `EMPIRICAL_LOCATION_AWARE_MARGIN` (§3.5).

### 2.6 Objective [R1-3] — non-degenerate, identical for M0–M3
**Why v1's `C^P_share` was wrong.** With `pn(z)=P⁻(z)`, `r=ΣP⁻/Σpn=1` and `C^P_share≡0` for every candidate. Also `Pn_i(z)` in the denominator of `C_red` is a moving scale.
**Replacement (frozen scales, strictly positive, independent of `z`):**
`J(z)=C_disp(z)+λ_pat C_pat(z)`  (+ optional `λ_RDC C_RDC` only if the predictor behind it is audited).
* (a) **Displacement cost** `C_disp=Σ_{i∈PV}((p0_i−p_ref,i)/(Pmax_i−Pmin_i))² + Σ_k((v0_k−v_ref,k)/0.05)²`, `z_ref` = historical C2t case values; scales are case limits (system base), reported also in MW and pu of voltage.
* (b) **Pre-event participation-pattern deviation** `C_pat=Σ_i(P⁻_i/ΣP⁻ − π_i)²+Σ_i(Q⁻_i/(Qmax_i−Qmin_i) − κ_i)²` with **design shares frozen a priori** `π_i=p_ref,i/Σp_ref`, `κ_i=q_ref,i/(Qmax_i−Qmin_i)` (`q_ref` may be of either sign; the range normalisation is positive). This is a *design* participation target, *not* the RDC's (the RDC's native sharing target is `P_i/pn_i(z)`, trivially satisfied pre-event).
* (c) **Post-event RDC sharing error** `E_share(d,t)=ptp_i(P̂_i(t)/pn_i(z))` (and Q with `d_q`): predicted/measured outcome per `(z,d)`; reported as a **metric**, added to `J` only after a predictor audit, never mixed with (a),(b).
`λ_pat` by a predeclared rule: `λ_pat=1` after normalising `C_disp` and `C_pat` by their values at the extreme feasible redispatch of the DESIGN-static study (the normalisation constants are computed on DESIGN statics only and sealed). `J` is a regulariser/tie-breaker; sharing *performance* is an outcome metric (c), not part of the acceptance of the safety constraints.

### 2.7 Robust problem (finite family, common `z`)
`(P) min_{z,y0} J(z) s.t. g_AC(z,y0)=0, z∈𝒵_phys, M^{P±}_{i,d}(z)≥0 ∀(i,d)∈𝒟_W` (+ audited `Q,S,V` classes). Non-convex; solver output at best `LOCAL_OPTIMUM_FOUND` (KKT documented) or `FEASIBLE_PREDICTED`.

### 2.8 Proposition S — conditional, horizon-limited [R1-4]
*Scope.* The ANDES RMS positive-sequence plant **as modelled** (frozen B2, PSS, limits, `dt=2^-8 s` trapezoid), a **finite** family `𝒟_design`, step shape, horizon `[t_e,t_e+T]`, `T=200 s`. Not EMT, not protections, not any physical network.
*Hypothesis H_err (not proven).* For `(i,d)∈𝒟_design` and the evaluated `z`:
`ΔP^{jump,true}_{i,d}(z) ≤ ΔP^{jump,model}_{i,d}(z)+ε^{J}_{i,d}` and `sup_{t∈[t_e,t_e+T]}[P_i(t)−P_i(t_e⁺)] ≤ Ê⁺_{i,d}(z)+ε^{E}_{i,d}`.
*Claim.* H_err and `P⁻_i+ΔP^{jump,model}+Ê⁺+ε^J+ε^E ≤ Pmax_i` imply `P_i(t) ≤ Pmax_i` for all `t∈[t_e,t_e+T]` (continuous time **of the model solution**).
*Proof.* `P_i(t)=P⁻_i+ΔP^{jump,true}+(P_i(t)−P_i(t_e⁺)) ≤ P⁻_i+ΔP^{jump,true}+sup(...) ≤ P⁻_i+ΔP^{jump,model}+ε^J+Ê⁺+ε^E ≤ Pmax_i`. ∎
*Lower side:* symmetric with `Ê⁻`, `min(0,ΔP^{jump})`, opposite-sign `ε` (independent inequality). *Q/S/V:* own-output inequalities only; `S` not obtained by adding `P` and `Q` maxima.
*Status:* `CONDITIONAL_PROPOSITION`; never `SAFE_GUARANTEED`. H_err has not been tested (no LOBO, no sampling). Further limits of the statement: (i) limiter mode changes may violate the affine predictor; (ii) behaviour after `t_e+T` (slow drift, 427 s modal time constant) is **not** covered; (iii) a stored-sample TDS (`dt=2^-8 s`) cannot establish inter-sample safety, so `TDS_SAFE_OBSERVED ≠` continuous safety; (iv) `AC_FEASIBLE_FOUND` says nothing about post-event recovery; (v) the proposition does not cover disturbances outside `𝒟_design`, other shapes (ramps), N−1 or delays. Highest status of any outcome: `CONDITIONALLY_ESTABLISHED` for the proposition, `NUMERICALLY_SUPPORTED` for observations.

---

## 3. Predictor design (DAE + PSS + consistent references)

### 3.1 Model and reuse
Reduced DAE of DEC-052 (12 genuine PSS states, degenerate IEEEST chain eliminated exactly, quotient by common angle, 20 reference states) rebuilt **per candidate**; libraries `dec051_core.py`, `dec052_*.py`, `run_dec051_h3_jump.py` used read-only.

### 3.2 Per-candidate preconditions
1. PF converges; `TDS.init` (no stepping) with residual ≤1e-8 on plant/DAE equations (§2.2.2).
2. `I(z)` (§1.1) computed and **passed** to `A⁺,C⁺,f⁺` — in particular `pset=pn(z)`, `qset=qn(z)`, `k_ip(z)`, `gref(z)`, `d_p(z)` — **before** any Jacobian (DEC-051 stale-reference defect).
3. Analytic vs central-difference Jacobian agreement ≤1e-6 relative (DEC-052 achieved 1.3e-7 on another case).
4. `g_y` regularity per `(z,d)` branch with recorded `σ_min`, condition number; threshold sealed at P1.
5. Interior of capability (`gp0,gq0>0`), `pn_i ≥ P_floor`.

### 3.3 Time propagation
The affine system is embedded as `ζ̇=Mζ`, `M=[[A⁺,f⁺],[0,0]]`, `ζ=[δξ;1]`, and propagated with a **scaling-and-squaring matrix exponential or a real Schur-based stable linear integrator** (no eigenvector expansion without a conditioning check, given the historical modal ill-conditioning). Output `D̂_i(t)=C⁺ δξ(t)` is evaluated on a fixed log-spaced grid over `[0,T]` plus a refinement around local maxima (Brent). A grid maximum is **not** a certified global maximum in time: a **sampling/refinement error** term is estimated by a denser grid and reported; no maximum time (e.g. 7.8 s) is pre-assigned. Optional piecewise-affine re-linearisation (§2.4) is decided in P3-A and frozen.

### 3.4 Validity monitor
Flag `MODE_CHANGE` if the predicted trajectory approaches a limiter (TGOV1N, IEEEX1, REGF1 limits, `Z_CLAMP`), if the amplitude exceeds the calibrated range, or if the Jacobian at the predicted peak state differs from `A⁺` beyond a sealed tolerance. Flagged candidates are verified with ANDES only in DESIGN/TUNE; in PROSPECTIVE_TEST they are labelled `OUT_OF_CALIBRATION_DOMAIN` and not corrected afterwards.

### 3.5 Uncertainty — `EMPIRICAL_LOCATION_AWARE_MARGIN` [R1-6, R1-5]
* **Why a conformal quantile cannot be used (correction of v1).** The v1 proposal `α=0.10` with 4 DESIGN + 4 TUNE buses gives `n=8` exchangeable observations at best; the split-conformal rank is `⌈(n+1)(1−α)⌉=⌈9·0.9⌉=9>8`, so the distribution-free bound is `+∞`. Moreover units of one event are not independent, buses are not exchangeable (different locations), and there is no genuine train/calibration split. **No 90 % coverage is claimed and the term "conformal" is dropped.**
* **Rule.** Signed residuals `e^J_{i,d}=ΔP^{jump,obs}−ΔP^{jump,model}` (observed = first stored sample after the event minus the pre-event sample; the proxy includes one step `dt` of dynamics, a declared proxy error absorbed in `ε^J`) and `e^E_{i,d}=E^{obs}−Ê`. For each unit and class: `ε=max(ε_floor, κ·max_{events}(e)^+)`, with proposal `κ=1.5`, `ε_floor=1e-3 pu` (sealed at P1, before any holdout TDS). Reported: signed errors, worst positive and negative residual, leave-one-bus-out (LOBO) residuals **as a diagnostic**, and a sensitivity of the DESIGN dispatch to `κ∈{1,1.5,2}` (static, not a sweep of test data). `ε` is an engineering margin, not a bound.
* Bus 4/18 (P) and bus 21 (Q) may enter TUNE as **calibration/diagnostic** data (results exist) — never in the blind cohort; the bus-4 excursion library is **not** used as a bound for other locations.
* Out-of-domain flag from amplitude, `‖∂y⁺/∂d‖` range and `MODE_CHANGE`.

### 3.6 Predictor audit (P3-A, ≤8 TDS)
Predicted vs ANDES on DESIGN buses for SG31/SG35 (P, and Q if feasible): jump error, excursion error, time of maximum; limited integration-fidelity check (counts in the budget). Class `P/Q/S/V` is imposed only if its LOBO residuals are small compared with the margin the cost allows; otherwise scope is degraded.

---

## 4. Algorithm [R1-4]

### 4.1 Algorithm 1 — multi-contingency separation with explicit exit states
```
Input : 𝒟_design (list), z_ref, limits, RDC constants, seeds, ε (sealed), J, τ_cut=1e-4 pu,
        K_max (cuts), N_it (NLP iterations per solve), r_tr (trust radius for empirical cuts)
Output: z*, status, cut log, margin table for ALL (i,d,class)

W ← initial set 𝒟_0 chosen by STATIC jump-only severity at z_ref (rule, no TDS data)
for k = 0..K_max:
  (z_k, s_k) ← solve (P) over W by multi-start {z_ref-feasible-seed, z_{k-1}, fixed seed set}   # s_k solver status
  if s_k = SOLVER_FAILED          → status = SOLVER_FAILED (no infeasibility claim); stop
  if no feasible start / (P) infeasible in the evaluated model:
        status = INFEASIBLE_NOT_DEMONSTRATED (record whether: solver non-convergence | cut budget | AC-infeasible in model); stop
  evaluate M_{i,d,class}(z_k) for EVERY d∈𝒟_design (nonlinear jump + predictor)
  v ← most violated (i*,d*,class*,t*), margin m*
  if m* ≥ −τ_cut :
        status = LOCAL_OPTIMUM_FOUND if KKT residual of the working-set NLP ≤ tol (documented)
                 else FEASIBLE_PREDICTED ;  z* ← z_k ; stop
  if (i*,d*,class*) ∈ W  (already imposed) and still violated:
        status = STAGNATED_EXISTING_CUT                      # do NOT re-insert
        diagnose: solver tolerance / gradient error / predictor non-smoothness / contradictory constraints
        report remaining violations ; stop
  W ← W ∪ {(i*,d*,class*)}  after deduplication (key = (d,i,class); also merge cuts with identical active (d,i) and weaker margin)
  log: (unit, class, event, t*, margin, validity flag, AC-feasible after adding? )
status = ITERATION_BUDGET_EXHAUSTED (k = K_max) ; report the least-violating z_k and the violation vector
```
**Termination.** The loop ends in **one of the six states** or by `K_max`; there is **no claim of successful termination**. v1's "finite termination because `W` grows" is withdrawn: a cut is inserted only if not already in `W`; if the most violated constraint is already imposed and violated, the algorithm **stops** (`STAGNATED_EXISTING_CUT`) instead of growing; adding a cut guarantees neither monotone decrease of the violation, nor convergence to feasibility, nor optimality for the non-convex AC problem. `K_max`, `N_it` and `r_tr` are sealed at P1.

### 4.2 Dynamic (TDS) cuts in P3-B
A cut derived from an ANDES run on a DESIGN/TUNE event is a **local, empirical restriction**: `δ_{i,d} ← max(0, observed_excess+τ_cut)` added to that `(i,d,class)` margin **only inside a trust region** `‖z−z_k‖_∞ ≤ r_tr` (proposal 0.05 pu on `p0`, 0.01 pu on `v0`); outside it the cut is dropped and re-validated. It is not a globally valid cut of the non-convex feasible set. The time maximum is taken on a grid with local refinement (not a certified global time maximum).

### 4.3 Complexity — symbolic budget (to be measured, not asserted) [R1-4]
Per candidate `z`: `1×PF + 1×TDS.init` (cost `C_pf`), `|𝒟|` nonlinear algebraic post-event solves (`C_alg` each, Newton with a sparse factorisation whose cost depends on structure/ordering, **no `O(n_y^{1.5})` bound is asserted**), one reduced Jacobian assembly per `(z,d)` (`C_jac(n_param)` with finite-difference columns for the RDC parameters), one matrix-function propagation `C_exp(n_x=227)` per `(z,d)` plus `n_t` output evaluations. Per NLP iteration with finite-difference gradients over `n_z=19`: `(n_z+1)·[C_pf+|W|(C_alg+C_jac+C_exp)]`; per cut step additionally `|𝒟_design|(C_alg+C_jac+C_exp)`. Total `≈ K·N_it·(n_z+1)·[…]`. Budget stated in **calls** (PF, init, algebraic, Jacobian, expm); wall-clock to be measured on the first static run in P2; **none of it uses TDS** (the TDS budget is only the 48).

---

## 5. Experimental design

### 5.1 Scenario family and partition [R1-5]
Family: P steps at `t_e=5 s`, amplitudes `a∈{0.5,1.0}×58.564 MW`; Q steps (if the Q module is audited) `a∈{0.5,1.0}×17.345 MVAr`; horizon 200 s; `dt=2^-8 s`.
**Eligibility rule (physical, fixed in advance, outcome-blind):** PQ load buses (19 in the case; `IEEE39_DEC052_H3_location_scan.csv`) **excluding** (i) buses that host a unit terminal (31, 39 — a load step electrically at a generator/slack terminal) and (ii) buses with prior dynamic results (4, 18 for P; 21 for Q) which cannot enter the blind cohort. 19 − 2 − 3 = **14 eligible buses**: `{3,7,8,12,15,16,20,23,24,25,26,27,28,29}`. No bus was removed because of expected performance.
**Hash split by bus** (unit of analysis = bus): rank by `SHA-256(seed‖bus)`; first 6 → PROSPECTIVE_TEST, next 4 → TUNE, last 4 → DESIGN; buses 4, 18, 21 enter TUNE as calibration only.
**PROVISIONAL (not sealed) enumeration** with the single a-priori seed string `DEC054-R1-provisional-seed-v1` (one draw, no alternative seeds tried, computed without any performance data): TEST `{3,29,15,12,27,26}`, TUNE `{7,20,16,24}` (+4,18,21 calibration), DESIGN `{8,23,28,25}`. The investigator may replace the seed *before* looking at the ranks; sealing happens at P1.
**Caveats (declared).** (i) 6 test buses are 6 clusters; the two amplitudes of one bus are correlated (not independent observations); effective independent `n≤6`. (ii) An *informativeness* rule (≥2 test scenarios where M0 is **statically** predicted to violate on the jump alone, ≥2 where it is not) would make the cohort **purposive**, not random: it is therefore **optional and flagged**; if applied, it uses only static quantities, is logged with its fallback ranks, and any resulting cohort is described as purposive. (iii) The scan file was produced with R35_040 values and is used only for eligibility.
**P/Q classes.** The Q scope (6P vs 4P+2Q) is decided at P2 **before any prospective result is opened** and recorded as a deviation from the pre-registration if changed; Q cannot be forced into the cohort if the Q predictor is not audited.

### 5.2 Budget (48 TDS ceiling, not a target)
P3-A ≤8 (predictor audit on DESIGN), P3-B ≤16 (dynamic cuts on DESIGN/TUNE), P3-C ≤24 (**6 scenarios × M0–M3**). Failures count. HIST R35_040 is not in the blind cohort (retrospective, in-sample).

### 5.3 Freezing and anti-leakage
Before the first P3-C TDS: Git-committed frozen file with code hashes, ANDES version, partition + seed, `ε` rule and values, `κ`, `λ_pat`, scales, working sets, M0–M3 dispatches and predictions, trust radii, thresholds. The runner recomputes hashes, aborts on mismatch, runs M0–M3 on the same event without reading other prospective outputs. A discovered bug ⇒ `TEST_INVALIDATED` (new cohort needs a new authorisation); no re-tune/re-test on the same cases; failures never replaced; test data never used for calibration after failures.

### 5.4 Comparators — fairness [R1-5]
All methods solve **the same AC-OPF base problem**: same `𝒵_phys` (including Slack `P,Q` limits, all-unit `P/Q/S`, **39 pre-event voltages in [0.95,1.05]**, balance/losses, `P_floor`), same `J`, same demand, solver, tolerances and seeds. The historical C2t dispatch has 21 buses >1.05 pu (max 1.0730) and is **not** a feasible M0: `z_ref` serves only as the distance anchor in `C_disp,C_pat`; M0 is a *new* AC-OPF solution inside the band.
| ID | Added reserve term | Parameter fixed on |
|---|---|---|
| M0 | none (base AC-OPF) | — |
| M1 | static `R_i(z) ≥ ρ·(Pmax_i−Pmin_i)` (uniform) or proportional variant; one parameter `ρ` | DESIGN/TUNE only |
| M2 | jump-only margins over `𝒟_W`, `ε^J` | same cut procedure |
| M3 | jump + excursion + multi-contingency, `ε^J+ε^E` | DESIGN/TUNE |
| HIST R35_040 | historical dispatch, `RETROSPECTIVE_IN_SAMPLE` | historical |
**Two independent contrasts** (not forced to coincide): **(C-1) equal cost**: compare outcomes at `J` equal within a tolerance `δ_J` fixed before; **(C-2) minimum cost for a predicted-compliance threshold** (threshold fixed before): the cheapest member of each method meeting it on DESIGN/TUNE statics; if no comparable point exists, `NOT_MATCHED`, no extrapolation. Any tuning of M1 to match M3 is done on DESIGN/TUNE and frozen before PROSPECTIVE_TEST is opened; no test result is used.

### 5.5 Endpoints and acceptance (proposals, to be sealed)
Primary: number of `(scenario,unit)` pairs with `P` outside `[Pmin,Pmax]` at any stored sample; total/maximum excess (violation = margin `<0`; a tolerance class of 1e-3 pu is reported separately). Secondary: `Q/S/V` violations (39 buses), `t=0⁺` vs later maximum, `C_disp`, `C_pat`, minimum reserve per unit, post-event sharing error `E_share` (metric (c)), nadir/zenith, RoCoF (filtered and raw, both labelled), final frequency error, DAE residual, runtime. Mean of the 39 BusFreq is **not** a COI (COI only with documented inertia weights).
`NUMERICALLY_SUPPORTED` only if all of: (i) M3 is new w.r.t. R35_040 and uses only ex-ante data; (ii) on the sealed cohort M3 has no more violating pairs than each of M0, M1, M2 and, under (C-1), strictly fewer than the best comparator, **or** under (C-2) equal (zero) violations with `C_disp` at least 20 % lower than the cheapest comparator reaching zero; (iii) no unacceptable deterioration: voltage band respected, `E_share` not worse than the comparator at equal cost by more than 2 percentage points, no `TDS_NUMERICAL_FAILURE` attributable to M3 only. Otherwise `NEGATIVE_FINDING` reported in full. With ≤6 clusters no inferential statistics are claimed.

### 5.6 Ablations
A1 M0→M2 (value of the jump); A2 M2→M3 (excursion + multi-contingency; static intermediates M3a = single-contingency + excursion, M3b = multi-contingency jump-only, **not run in TDS**); A3 M1→M3 at equal cost and at equal predicted compliance; A4 `ε` rule (jump-only vs full, `κ` sensitivity, static); A5 predictor ablation (with/without `f⁺` drift, with/without correct `I(z)` — the DEC-051 hazard as a unit test; with/without `k_ip(z)`, `gref(z)` update).

---

## 6. Originality — verified-neighbour table [R1-7]
**External literature status:** `EXTERNAL_LITERATURE_PARTIALLY_VERIFIED`. Public search was available; the items below were located by search (title/venue/year/URL as returned); **DOI/publisher metadata were not individually confirmed** and the full texts were not read beyond abstracts/excerpts. **`NOVELTY_NOT_ESTABLISHED`.** No claim that "robust OPF + dynamic reduction" is new in itself.

| Class (closest first) | Work (as located by search; metadata to be confirmed) | What it constrains | Relation to this design |
|---|---|---|---|
| Dynamic-security OPF with trajectory sensitivities / rescheduling loops | Tang & McCalley (trajectory-sensitivity transient-stability constraints from time-domain simulation); Pai-group review of rescheduling with iterative constraint addition (search results: certs.lbl.gov, pserc.wisc.edu, 2003) | rotor-angle/transient-stability limits via simulation + sensitivities | closest *mechanism* (simulate → sensitivity → add constraint → reschedule); differs in the constrained quantity (unit **power-limit exceedance** of a fixed secondary controller, split jump/excursion), SG–GFM plant, prospective test |
| TSC-OPF | Xu, Dong, Xu, Zhang, Wong, "Power system transient stability-constrained optimal power flow: a comprehensive review", IEEE PES, 2012 (research.polyu.edu.hk); Gan, Thomas, Zimmerman, "Stability-constrained optimal power flow", IEEE TPWRS, 2000; Zárate-Miñano, Van Cutsem, Milano, Conejo (time-domain simulation within an OPF), IEEE TPWRS, 2010 (orbi.uliege.be) | transient (angle) stability inside OPF; time-domain simulation embedded | known framework; here the limit is a **physical output limit**, not angle stability |
| Preventive rescheduling | Yuan, Zuo, Kubokawa, Sasaki, PSCC 2005 (generation rescheduling, interior point); Ruiz-Vega et al. chapter on preventive/emergency transient-stability control | preventive generation rescheduling | known preventive paradigm |
| Frequency-constrained scheduling | Paturet et al., IEEE Trans. 2020 (stochastic UC with nadir/RoCoF incl. grid-forming inverters, ktisis.cut.ac.cy); 2025 arXiv on frequency-constrained operation with hydro and inverters; Comillas 2026 ML-surrogate nadir constraint | frequency nadir/RoCoF/steady-state | frequency, not physical unit power excursion |
| Surrogate-assisted dynamic constraints | arXiv 2006.16186 (analytic DL surrogate for dynamic TTC constraints); arXiv 2012.13110 (surrogate/NN transient-constrained OPF) | learned surrogate of dynamic constraint | alternative to the physics-based predictor used here |
| Constraint generation in SCOPF | arXiv 2110.01669 (realistic SCOPF); Benders-type decompositions | static N−1 contingencies | the finite-set cut loop is standard; novelty is not claimed there |
| Project references (nine, abstracts read) | online controllers with capability/safety guarantees (B2 itself; CBF frequency control; multi-slot / GFM-GFL primal-dual dynamics with capacity constraints; MPC with nodal frequency/RoCoF); DNN-projection and physics-shielded/safe MADRL for voltage; GFM/GFL small-signal conditions | online action enforcing constraints | contrast class (offline operating point with a **fixed** controller) |
**Technical-closeness axes:** static margins (M1) — known; frequency — known, not this quantity; **instantaneous physical power (algebraic jump)** — not found as an explicit separated reserve term in the located works (*absence of evidence in a partial search*); slow excursions via a model predictor — related to trajectory-sensitivity work; prospective tests with a frozen cohort and negative-result policy — methodological rather than algorithmic.
**Candidate mechanism-level contributions (falsifiable):** C1 separation of the nonlinear algebraic jump from the model-predicted excursion in one reserve constraint for a **fixed** secondary controller on an SG–GFM network with PSS; C2 predictor anchored at the post-jump point that includes the RDC activation drift and recomputes `I(z)` per candidate (the dependence of `pn,k_ip,gref` on the dispatch makes the controller part of the design problem); C3 explicit participation-pattern objective that is non-degenerate under `pn(z)=P⁻(z)`; C4 empirical location-aware margin with declared loss of exchangeability. Each can fail (§8).

---

## 7. Risks and threats to validity
R1 small cohort (≤6 clusters, correlated amplitudes). R2 predictor linearity vs limiters; fixed `A⁺` over 200 s. R3 callback ordering / Euler discretisation (§1.3, `TO_VERIFY_IN_P2`). R4 non-convex OPF, local optima. R5 `ε` from ≤11 buses; no coverage claim. R6 comparator unfairness (equal-cost vs equal-compliance are different targets). R7 leakage through the eligibility scan (used only statically). R8 Q module unreliable → scope decision before opening results. R9 numerical failures at aggressive dispatches (counted). R10 RMS limits ≠ real capability (OEL/UEL, converter current, SoC, EMT). R11 backup not independent (blocker). R12 novelty unsupported (`NOT_ESTABLISHED`). R13 dependence of `pn,k_ip,gref,d_p` on `z` (the controller changes with the candidate; handled by `I(z)`). R14 `pn_i→0` for a GFM (blow-up of `d_p`): `P_floor`. R15 DEC-053's sharing figure was a metric artefact (§0.1): any claim about the cost of redispatch to sharing must be re-derived with `pn(z)`.

## 8. Falsifiable contributions
**H-A** (jump): M2 has fewer predicted-and-observed `Pmax` violations than M0 where the jump dominates. **H-B** (excursion): M3 has fewer violations than M2, or equal compliance at lower `C_disp`, where the slow term dominates. **H-C** (cost): at equal compliance M3 needs lower `C_disp` than M1; at equal cost fewer violations. **H-D** (predictor): H_err is refuted for any test case with `M≥0` and an observed violation; LOBO residuals reported. **H-E** (RDC dependence): ablation A5 shows whether recomputing `I(z)` changes the predicted maxima (if not, the added complexity is unjustified). Failure of any is a `NEGATIVE_FINDING` with unchanged criteria.

## 9. Conditions to authorise P1 (for the investigator)
1. P0 resolved: **independent** backup destination read back and restored (`BACKUP_VERIFIED`).
2. Approve or modify the objective `J` (§2.6): scales, `λ_pat` rule, `P_floor`.
3. Approve the predictor formulation (§2.4), including whether piecewise-affine re-linearisation is allowed, and the plan to resolve `UNRESOLVED` items in P2: callback ordering (§1.3), GFM initial dynamic residuals (§2.2.2), Euler-vs-continuous mismatch.
4. Approve `ε` rule (`κ`, `ε_floor`), trust radii, `K_max`, `N_it`, `τ_cut`, thresholds of §5.5.
5. Approve or replace the partition seed and the eligibility rule (§5.1); decide whether the optional informativeness rule is used (purposive cohort).
6. Decide Q scope policy (decision at P2, before opening results).
7. Accept the revised proposition (§2.8) as the strongest claim attainable.
8. Authorise the external literature check to be completed (DOIs, full texts) before any novelty statement.
9. Acknowledge the DEC-053 sharing correction (§0.1) for the manuscript line.

## 10. Architecture (modules to be created only after authorisation)
`dec054_data` → `dec054_acpf` (candidate PF/init, `I(z)`) → `dec054_jump` → `dec054_predictor` (post-event branch, `A⁺,f⁺,C⁺`, expm/Schur, validity monitor) → `dec054_calib` → `dec054_opf` (M0–M3, Algorithm 1) → `dec054_runner` (hash-frozen, ledger-gated) → `dec054_report`. Outputs `IEEE39_DEC054_*`; large series to an external exclusive directory.

## 11. Declaration
No TDS, optimisation, ANDES initialisation or implementation; no change to the RDC, plant, PSS, limits, cases, historical results, `main.tex`, `main`, manifests or backups; the original v1 document is preserved. `STOP_BACKUP_NOT_VERIFIED` remains in force; stop for human review.
