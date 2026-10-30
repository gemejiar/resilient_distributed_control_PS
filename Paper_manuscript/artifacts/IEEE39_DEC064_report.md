# DEC-064 report: scientific consolidation, state-of-the-art review and claims proposed for approval

Written for: the investigator who issued DEC-064, who must approve the scientific claims (section 4) before the methodology of `main.tex` is replaced. Branch `review/dec059-scientific-reorientation`. **No TDS was run, no controller, dispatch, criterion, historical result, `main`, `main.tex` or `references.bib` was changed, nothing was pushed, ANDES was not reopened.** New files: `dec064_checks.py`, `IEEE39_DEC064_checks.json` (read-only analysis of stored runs), `IEEE39_DEC064_literature_matrix.csv`, this report. Ledger stays at 112 of 120. Results below keep the negative findings, G-v2 REJECTED, the post-TUNE modification of the TEST gate, the UNSAFE and INDETERMINATE cells, and the A-INFO information advantage.

## 0. Summary

1. **Literature.** Thirteen works were examined; five were read in full or in their relevant sections (level A) and two more in part (level A-), the others at the lower levels declared in the matrix. Among them, the closest precedents change what we may claim: (a) the original RDC (Kavvathas–Konstantopoulos, TPWRS 2025) already guarantees reference-set invariance and uses an eigenvalue-based stability argument; (b) Mo–Liu (arXiv 2025) already couples a distributed secondary controller with a CBF safety corrector. **The CLF–CBF–QP and reference-set invariance are therefore not original contributions**, and T1 is a discrete-time adaptation, not a new idea.
2. **No work among the thirteen was found that treats the post-event instantaneous admissibility of delivered unit P/Q/S/V as a function of the pre-event dispatch (T-A) and designs a dispatch for it.** This is a statement about the examined set only. The search was not systematic (no IEEE Xplore access; 10 web searches plus page and PDF fetches), so **priority or novelty cannot be claimed** (section 1.3).
3. **Two corrections to our own statements emerged from the checks.** (i) Proposition OS as worded ("any rate-bounded controller… at most T·v̄") is not what was verified: B2 moves its references up to **6.27 × T·v̄** in the first 50 ms yet the margins of the four controllers agree within 5.8e-5 pu. The proposition must be restated with the plant gain and the controller's own rate bound. (ii) The nadir and early-reference differences between the centered controllers and B2 appear **before any supervisory target is used** (first second after the event), so they are attributable by elimination to centering, not to A-INFO or to the QP (section 3).
4. **The proposed title** corresponds to T-A, OS, P3 and the dispatch design, but not to T1, T2 or the centered controller, and the dispatch evidence is partial (section 5). Recommendation: keep it with a descriptive subtitle, or use the alternatives given.
5. **Approval is requested for the eight claims C1–C8** (section 4) before any rewrite of the methodology.

## 1. State of the art and originality

### 1.1 Method and verification levels
Local full texts in `references/` were read for L1, L3, L4 (sections listed in the matrix). The arXiv full texts of Mo–Liu (CBF, L5), Paturet et al. (L9) and the survey of She (L10) were downloaded and read by text extraction. L2, L13 were checked at abstract-page level; L6 only abstract and first introduction paragraph; L7 and L8 only abstract (full text exists locally but was not read in this step); L11 and L12 are bibliographic (data verified in the reference list of L10 or in `references.bib`). The reviews on distribution-grid DRL shields (Chen 2023, Zhang 2024 ×2) were not extended: different setting. **Limits:** the examination of IEEE TSG, TSTE and control journals 2021–2026 is not exhaustive; a systematic protocol (databases, query strings, inclusion rules, two-reader screening) has not been executed and needs IEEE Xplore/Scopus access. Search results used here are listed in the matrix; none was invented.

### 1.2 Comparative matrix
Full table with all columns requested (hypotheses, physical model, constraints, guarantees, preventive dispatch, regulation, scalability, evidence): `IEEE39_DEC064_literature_matrix.csv`. Condensed:

| Work (level) | Model / test | Constraint object | Guarantee | Preventive dispatch | Regulation |
|---|---|---|---|---|---|
| Kavvathas–Konstantopoulos TPWRS 2025 (A) | nonlinear DAE, 4th-order SG, DERs; 10- and 14-bus, HIL | set-points in W_i | invariance (Nagumo); eigenvalue stability (numerical) | none | f, P, Q sharing |
| Wang–Chen TPWRS 2026 (A) | linear DC design, EMT validation on IEEE-39 | IBR capacity, line limits, on references | global asymptotic stability (projected primal-dual) | none (nominal from economic dispatch) | f |
| Mo–Liu TPWRS 2026 (A) | linearised SG + governor, 118-bus | capacity on set-points through transients | local asymptotic stability; ISS | embedded economic dispatch only | f |
| Mo–Liu arXiv 2025 (A) | aggregated swing, 3 areas | frequency safe set (CBF), capacity on mechanical power | safety if w(0) in set; asymptotic stability | none | f |
| Tang TSG 2026 (A-) | microgrid frequency | frequency safe set (CBF-QP) | CBF safety | none | f |
| Paturet TPWRS 2020 (A, pre-2021) | aggregate SFR, RTS-96 | RoCoF, nadir, steady-state in UC | MILP-consistent constraints | **system-level frequency preventive** | f |
| She 2026 survey (A-) | taxonomy | static/dynamic security, preventive/corrective | n/a | frames preventive solution ↔ post-contingency initial condition | n/a |
| **This work** | DAE, IEEE-39 C2 (SG–GFM), P/Q/S/V limits | references (T1) and delivered outputs at the event (T-A) | T1 proved; T2 conditional local; T-A, N1, N2 proved | **unit-level admissibility at t_e⁺ (M3+OS)** | f, V, sharing at E* |

### 1.3 What each of our results actually contributes
| Result | Prior art | Real contribution | Statement allowed |
|---|---|---|---|
| T-A | Algebraic jumps of DAE variables at switching instants are standard (consistent re-initialisation); frequency-constrained scheduling uses aggregate models (L9) | Using the jump as an explicit **necessary condition on the dispatch for unit-level limits**, independent of any rate-bounded secondary controller; elementary but not stated in the examined works | "We state and use… ; among the works examined we did not find…" |
| OS | none identified | A bound on how far a rate-bounded secondary controller can alter the first 50 ms; **needs restatement** (section 2) | Only in the corrected form |
| M3+OS dispatch | frequency-secured UC (L9, L11); TS-constrained rescheduling exists (search lead, not read) | Unit-level P/Q/S/V margins with a validated sub-cycle predictor; OC1 evidence partial, bus 31 counter-example | "Design with evaluated predictor", not "protects" |
| RDC centered (Lemma C) | RDC (L1) | Exact steady state at a selected equilibrium E*; needs a supervisory target | Conditional on A-INFO |
| T1 | L1 invariance (Nagumo, continuous time); L3, L4 projection | Discrete-time, rate-limited, centered law; constructive feasibility (T1-F) | "Adapts"; not novel as idea |
| T2 | L1 eigenvalue stability, L4 local stability | Sampled-data local stability of the centered loop at verified targets | Conditional, local |
| P3 | none identified | Classification separating proved, verified and observed levels | Framework |
| CLF-CBF-QP | L5, L6 (CBF correctors on secondary control) | None shown experimentally | Not a contribution |

## 2. Verification of the theory (T-A, OS, T1, T2, P3)

Sources: `IEEE39_DEC059_theory.md`, `dec059_b5.py`, stored runs, `IEEE39_DEC064_checks.json`.

| Item | Statement checked | Hypotheses vs implementation | Consistency with results | Finding / gap |
|---|---|---|---|---|
| **T-A** | For a controller with no reset of x, u at t_e, h_j(ξ(t_e⁺)) = a_j(z, d⁺) | DAE with algebraic variables solved from (x, u, d⁺); event is a PQ step; controller active from t_e; delivered P/Q/S/V margins defined against fixed limits | 7/7 inadmissible cells non-SAFE; four controllers equal in first 50 ms | Mathematically elementary and correct. **The notion of violation is a modelling definition** (limits on delivered power, not on the turbine); measured within numerical band U_D8 = 0.0109 pu |
| **OS** | "For any rate-bounded controller the displacement over [t_e, t_e+T] ≤ T·v̄; the physical difference is bounded by plant gain × T·v̄" | v̄ = 0.01·Sn pu/s is the box of B5′/B4′. **B2 exceeds it: max displacement/(T·v̄) = 6.27 (B2), 0.996 (B5′, B4′), 0.12 (B1s)** | HB1: four controllers within 5.8e-5 pu | The class "v̄-bounded" does not contain B2. Correct statement: for a controller with bound v̄_c the physical difference is ≤ L_T T v̄_c; the **plant gain L_T is not computed**, so the quantitative bound is open. Empirical independence holds up to 6.3 × v̄ in these cells |
| **T1** | u₀ ∈ W, v_k ∈ 𝒰_k ⇒ c_j(u_k) ≥ (1−γ)^k c_j(u₀) ≥ 0; v = 0 feasible (T1-F) | `hard_ok`/`solve_qp` implement (Q1)–(Q3) exactly; disc by second-order cone; fallback by scaling θ (exact by convexity) | min c_j ≥ 0.024 in 42/42 runs, 0 fallbacks | Proof correct. **B2 and B1s also never leave W** (min c ≥ 0.147). **Open question for the manuscript:** whether the centering offset breaks the inward-pointing property of the original RDC (L1); if not, T1 adds only the discrete-time and rate-box versions |
| **T2** | H1–H5 ⇒ neighbourhood N where the QP returns v_nom and the sampled loop converges exponentially modulo the angle | H1, H4, H5 are floating-point verifications; N not quantified; targets 42/42 verified | **36/36 B5′ runs are on the fast path (v = v_nom, CLF row satisfied) after the last solver call, at most 4.29 s after the event** (`dec064_checks.py`); V ratio ≤ 4.2e-4 | Consistent. It is a stability result of the centered sampled RDC; the QP is inactive on N by the proof itself |
| **P3** | N1 (capacity), N2 (= T-A), V (numerical), O (observed) | as T-A and T2 | N2: 7/7, 0 counter-examples; N1 not exercised (no TEST cell fails the capacity inequality) | N2's confirmation is close to tautological given T-A; N1 untested; V does not certify recovery (N unquantified) |

**Separation of box, centering and QP.**
- *Rate box.* In 99.999 % of solver calls the box is saturated; it only reduces |v|. B2 moves 6× faster than the box in the first 50 ms with the same margin to 5.8e-5 pu, so the box has no measurable effect on the first-50-ms safety.
- *Centering.* In OC1/OC2, total P reference displacement over the first second after the event: B5′ = B4′ = 0.166 (OC1 b21 S2) and 0.228 (OC2 b21 S2) pu against B2 = 0.025 and B1s = 0.027 pu; ~6–9× larger. In [t_e, t_e+1) the supervisory target is not yet used (A-INFO delay), the barrier rows cannot bind (gap > 0.11 pu), the CLF row is dropped. By elimination the early difference is attributable to centering (consistent with the offset o = v_RDC(ξ_pre) that B2 carries at activation when the OPF point is not an RDC equilibrium, DEC-055 D7) and not to information or the QP. This is **inference by elimination, not a controlled contrast** (B3 without box is not available).
- *QP / CLF.* ≤ 14.1 mpu, ≤ 1.31 mHz, ≤ 0.20 mpu, no effect at 200 s (DEC-063).
- *Supervisory information (A-INFO).* Needed for the 200 s offsets of B2 (voltage 36–37 mpu, frequency 2.4e-4 Hz) by Lemma C; its empirical separation from centering is not available. B2 and B1s do not have it; every comparison must say so.

## 3. K6 and K7 audit

**K6 as registered:** "Evaluated transient safety with preventive dispatch (M3+OS); not a theorem (prediction)."

| Sub-statement | Evidence | Level | Keep? |
|---|---|---|---|
| K6a. Under the frozen design, in OC1 rev3, 7 of 9 blind cells SAFE; the 2 UNSAFE (b31 S2, S3) are inadmissible at the jump (N2) and are UNSAFE for all four controllers | TEST cohorts A, B | Observation (9 cells, correlated by bus and scenario) | Yes, with the UNSAFE cells |
| K6b. Redispatch of 101 MW changes the class of b21 S2 and b39 S2, S3 from UNSAFE to SAFE with controller B5′ | OC1 M0 vs rev3, same controller, event, solver | **Causal inside the simulation** (single-factor contrast, deterministic), 3 cells | Yes, limited to those cells |
| K6c. The first-50-ms effect of the dispatch holds for any controller | Prop. OS + HB1 | Theory-supported **in corrected form**; observed at M3 only | Only after rewording OS |
| K6d. The predictor class agrees with the TDS class | 34/36 | Observation; 2 false SAFE at M0 (b39 S2, S3) | Yes, with the false SAFE |
| K6e. "Protects the buses" | none | Refuted for bus 31 | **No** |
| K6f. OC2 | M0 and rev3 differ by 0.06 MW | No information on dispatch | Do not use |
Also kept: G-v2 REJECTED (criterion (iv) in three S3 cells), TEST opened under a modified access rule, rev3 designed after TUNE.

**K7 as registered:** "Frequency–voltage regulation and sharing versus B2/B1s/B4′; descriptive."

| Sub-statement | Evidence | Level |
|---|---|---|
| K7a. Frequency nadir of centered controllers is 4–6 mHz higher than B2/B1s and occurs 0.06–0.4 s earlier (59.9759–59.9783 vs 59.9717–59.9730 Hz) | six S2 cells; `dec064_checks.py` | Observation; mechanism (faster early reference displacement) supported by elimination (section 2); not separated from A-INFO for the part after 1 s |
| K7b. B2 leaves 36–37 mpu in unit voltage and 2.4e-4 Hz at 200 s | six cells | Observation; theory (Lemma C) explains it conditional on the supervisory target; not isolated empirically |
| K7c. B5′ ≈ B4′ | six cells | Observation: the CLF row has no measurable effect |
| K7d. B1s has the lowest effort and voltage offset | six cells | Observation |
| K7e. "B5′ is better" | — | **Not supported**: no dominance; A-INFO advantage; comparators with their own gains; B1s is our construct |
Statistical caveat: six deterministic cells (two different systems); no inference beyond description.

## 4. Claims proposed for approval

Each claim states what is asserted and what is not.

| ID | Proposed claim | Evidence level | Not claimed |
|---|---|---|---|
| **C1** (T-A, N2) | For any controller that does not reset x or u at an event, the unit P/Q/S/V margins at t_e⁺ are fixed by the pre-event dispatch and the disturbance; a negative margin there means every such controller violates the limit | Proved; observed 7/7 cells | That the algebraic jump is new in itself; physical (turbine) limits |
| **C2** (OS, corrected) | A controller with reference rate bound v̄_c changes the physical state in the first T s by at most L_T·T·v̄_c; empirically four controllers differ ≤ 5.8e-5 pu over 50 ms, including B2 at 6.3 × v̄ | Corrected statement; L_T not computed; observation | A quantitative bound for T > 50 ms or other plants |
| **C3** (dispatch M3+OS) | Algorithm 1 with a sub-cycle predictor (error −4.0e-5 to +1.84e-3 pu) reduces unit-limit violations at the event for admissible cells of OC1; bus 31 is a counter-example; two false SAFE at M0 after 50 ms | Causal for 3 cells; observation for 36 | Protection of all buses; OC2 evidence; G-v2 pass |
| **C4** (centering, Lemma C) | Given a valid supervisory target (delay τ_info), the centered RDC restores f and V exactly at the selected equilibrium; centering produces faster early reference movement than B2 | Proved (Lemma C); observation; early effect by elimination | Without information; superiority over other controllers |
| **C5** (T1) | The reference set is forward-invariant in discrete time under the rate-box filter with constructive feasibility | Proved; 42/42 consistent | Invariance of delivered outputs; novelty of invariance; that the QP prevents violations (none occurred without it) |
| **C6** (T2) | Local exponential stability of the sampled centered loop at verified equilibria under H1–H5 | Conditional proof; 42/42 targets; fast path after ≤ 4.3 s | Regional stability; stability caused by CLF |
| **C7** (P3) | A classification into proved, verified and observed levels, with an empirically recovered set | Proved N1, N2; numerical V; observed O | A certified recoverable set |
| **C8** (negative results) | HOCBF/CLF obstruction on this DAE; G-v2 REJECTED; falsified pre-registered hypotheses (HA1, strict HA2, HA7); OC3 unstable target; no controller dominates; CLF-QP without measurable effect | Documented | — |

## 5. Title evaluation
Proposed: "Event-Admissibility-Aware Preventive Dispatch for Capability-Constrained Distributed Frequency–Voltage Control".
- *Event-admissibility-aware*: C1, C2, C7 (proved). *Preventive dispatch*: C3 (partially supported; the title promises a dispatch method, the evidence is OC1-only with a counter-example). *Capability-constrained distributed frequency–voltage control*: context (L1, B2) and, partly, C4–C6 (centering, T1, T2) which the title does not name; the claim of control novelty is not in the title, which is appropriate.
- Does not over-claim stability, safety or CLF–CBF. Correspondence: good for C1–C3, partial for C3's evidence, weak for C4–C6.
- Suggested subtitle or alternative (investigator's choice): *"…: Post-Event Admissibility Analysis, Dispatch Design and Local Stability of a Centered Controller in an IEEE 39-Bus Hybrid System"* (long), or "Preventive Dispatch for Event Admissibility in Capability-Constrained Distributed Secondary Control: Analysis and Evaluation on a Hybrid SG–GFM Network" (shorter, states evaluation). "Event-admissibility-aware" is coined here and needs a one-sentence definition in the abstract.

## 6. Manuscript proposal (not applied to `main.tex`)

**Abstract (draft, ≤ 200 words).** Distributed secondary controllers can keep unit references inside capability sets, yet the delivered power of each unit at the instant of a disturbance is fixed by the pre-event dispatch. We show that, for controllers that do not reset states or references at the event, the unit active, reactive, apparent-power and voltage margins at the post-event instant are independent of the controller (T-A), derive a necessary admissibility classification (P3), and bound the controller's influence on the first fifty milliseconds. On this basis we design a preventive dispatch with a sub-cycle margin predictor and evaluate it on a modified IEEE 39-bus SG–GFM system with 36 blind simulations under a pre-registered protocol and a gate modified after tuning. The dispatch converts three unsafe cells to safe with the same controller, one bus remains inadmissible for four controllers, and two cells predicted safe were unsafe after 50 ms without redispatch. We also analyse a centered distributed controller with a supervisory equilibrium target: reference invariance in discrete time and local stability at verified equilibria are proved, and its restoration properties are compared with the original controller, with the information advantage declared. A barrier/Lyapunov quadratic program showed no measurable effect beyond rate limiting. Claims are limited to the tested network, step disturbances and two operating conditions.

**Contributions (final wording after approval of C1–C8).** C1–C3 as primary; C4–C6 as supporting; C7–C8 as methodology and negative results.

**Structure.**
1. Introduction: problem (instant of event), gap framed with L1, L3–L5, L9, L10; contributions C1–C8; limits.
2. Plant and controllers: DAE model, event, B2, B1s, B4′, B5′ with A-INFO declared.
3. Theory: T-A and N2 (C1), corrected OS (C2), P3 (C7), Lemma C (C4), T1 (C5), T2 (C6). Each with hypotheses and what it does not imply.
4. Preventive dispatch design: Algorithm 1, predictor, band U_D8, classification M3V-1.
5. Evaluation protocol: DESIGN/TUNE/TEST, freeze, hashes, gates, modified TEST access rule, budget 112/120.
6. Results: 6.1 admissibility and classes (Tables 2–3, F8, F11, false SAFE, UNSAFE, INDETERMINATE); 6.2 dispatch effect (K6b); 6.3 controller comparison (K7, F9) with attribution table; 6.4 T1/T2 checks (F10); 6.5 QP activity (F12) and HOCBF/CLF obstruction.
7. Discussion: causal vs associative statements; bus 31; G-v2; A-INFO; relation to L1, L3–L5.
8. Limitations and threats; conclusion.
Figures and tables as in DEC-063; plus the attribution table of section 2.

## 7. Gaps that prevent a scientific claim
- **Literature:** no systematic search; TSG, TSTE and control-journal coverage incomplete; L6–L8, L11 not fully read. No priority statement is justified.
- **Theory:** plant gain L_T of OS not computed; domain N of T2 unquantified; whether centering preserves the original RDC's invariance unresolved; floating-point H1/H4/H5.
- **Experiment:** centering, A-INFO and rate box not separable by a controlled contrast (3 runs would be needed; not authorised); no B2/B1s/B4′ at OC1 M0; CLF benefit untested; one event type; OC1 bus-31 counter-example; two correlated bus/scenario families; deterministic simulations (no variance).
- **Process:** TEST opened by a post-TUNE rule modification; rev3 designed after TUNE; G-v2 REJECTED.

## 8. Decisions requested
1. Approve, amend or reject each of C1–C8.
2. Title: keep, subtitle, or an alternative.
3. Authorise a systematic literature protocol (needs database access) before any novelty statement.
4. Authorise the rewrite of the methodology of `main.tex` on a review branch only after item 1.
