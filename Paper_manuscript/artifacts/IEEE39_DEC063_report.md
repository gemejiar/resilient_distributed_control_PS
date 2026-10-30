# DEC-063 report: scientific closure and manuscript readiness

Written for: the investigator who issued DEC-063, as the basis for deciding the claims of the manuscript. Branch `review/dec059-scientific-reorientation`. **No TDS was run** (ledger stays at 112 of 120, 8 unspent). No controller, dispatch, criterion, historical result, `main` or `main.tex` was touched; nothing was pushed. New files: `dec063_qp.py`, `dec063_audit.py`, `dec063_figs.py`, `IEEE39_DEC063_qp_analysis.json`, `IEEE39_DEC063_qp_binding.json`, `IEEE39_DEC063_audit.json`, figure `IEEE39_DEC063_F12_QP_activity.png`, this report. The new analyses read stored series of the 54 DEC-062 TEST runs and build the reference set W with a power flow only.

## 0. Headline

1. **The scientific core that the evidence supports is not the CLF–HOCBF–QP of `main.tex`.** It is an *information-aware centered distributed controller* (centering on a post-event equilibrium E*, supplied after τ_info) whose reference layer is kept in a box by a rate-limiting filter, together with the *post-event admissibility theorem (T-A) and a dispatch-level preventive design with a validated sub-cycle predictor*.
2. **The QP does not demonstrably improve any metric.** In 100 % of the solver calls the rate box is saturated; the barrier rows cannot bind in any of the 33 runs at the M3 dispatches (OC1 rev3, OC2 both) or in the OC2 M0 runs; the CLF row changes the commanded P by at most 14 mpu, the frequency by at most 1.3 mHz and the unit voltage by at most 0.2 mpu, with no effect at 200 s, and its sign as a benefit is untested. T2 itself proves the QP is inactive near ξ*.
3. **Dispatch is the dominant, causally attributable effect** (B5′ at M0 vs M3+OS in OC1), and by Proposition OS it applies to the first 50 ms of any rate-bounded controller.
4. **The manuscript is ready to be written only with the reframed scope** (section 7). It is not ready under the original three-theorem framing of `main.tex`.

## 1. Contribution audit

"Evidence" is numerical observation; "proof" is mathematics. Levels follow IEEE39_DEC062_contribution_status.csv, re-examined here against `main.tex` (Th1 physical invariance, Th2 regional convergence, Th3 restoration under saturation; title, abstract and conclusions are placeholders, Results is empty).

| ID | Exact statement (source: IEEE39_DEC059_theory.md) | Hypotheses / domain | Proof status and gaps | Implementation | Supporting experiments | Contrary evidence / limits | Defensible claim for the paper |
|---|---|---|---|---|---|---|---|
| **main Th1** | Physical invariance of P, Q, V, I by HOCBF | relative degree constant, post-jump state in C_H | **Not applicable** here: relative degree 3–4, post-jump state outside C_H, no GFM authority over SG31/SG35 (E9-A…H) | none (HOCBF rows excluded) | E9 diagnostics | refuted for this plant | Do **not** claim. Replace by T1 + T-A |
| **main Th2** | Regional exponential convergence in Ω_ρ | certified Lyapunov sublevel set | **Not provable** with available tools (no interval/AD backend, DEC-052) | none | none | — | Do **not** claim regional stability |
| **main Th3** | Restoration with several units at limits | certified D̂_rec | **Not provable** (g_P = 0 at binding limits) | none | none | OC3 target unstable | Do **not** claim; use P3 classification |
| **T1** | u₀ ∈ W, v_k ∈ 𝒰_k ⇒ c_j(u_k) ≥ (1−γ)^k c_j(u₀) ≥ 0; feasibility of v = 0 (T1-F) | discrete rows (Q1)–(Q3), α h ≤ 1 | **Proved**, elementary (one-line induction). Gap: none mathematically; physical meaning of v̄ and W is an assumption | `solve_qp` rows, fast path | min c_j ≥ 0.024 in 42/42 TEST runs, 0 fallbacks; unit tests | **B2 and B1s also stay in W (min c = 0.147 / 0.156 at M3 cells)**: the observation does not discriminate the filter. T1 says nothing about delivered P, Q, V | "The reference set is forward-invariant in discrete time under the filter (proof); the evaluated runs are consistent (42/42)". Say it is a design guarantee, not a performance difference |
| **T2** | Under H1–H5 there is a neighbourhood N of ξ*: QP returns v_nom, trajectories converge exponentially modulo common angle at rate ≥ ln(1/ρ_q)/h − ε | H1 root numerical (L-b), H4 spectrum numerical (L-a/c), N unquantified | **Proved conditionally**; H1/H4/H5 are floating-point verifications, N is not quantified. **The proof makes the QP inactive on N: it is a stability result for the centered sampled RDC, not for the CLF-QP** | centered RDC + `Filter` | 42/42 TEST targets satisfy E4, H1–H5; V(end)/V(first) ≤ 4.2e-4 in the 36 B5′ runs | **B4′ (no CLF row) has the same behaviour** (f error at 200 s differs by 6.2e-10 Hz); OC3 target unstable (outside H4) | "Local exponential stability of the sampled centered loop at verified equilibria, conditional on H1–H5". Do not attribute stability to the CLF row |
| **P3** | N1 (capacity inequality fails ⇒ no restoring controller), N2 (a_j < 0 ⇒ every rate-bounded controller violates j at t_e⁺), V (numerical local conditions), O (observed) | rate-bounded class, P-step events | N1, N2 **proved** (N2 is T-A); V numerical; O observation. Gap: no sufficient recovery certificate; frontier in ΔP not computed | `dec054_opf` + classifier | 7/7 inadmissible cells non-SAFE, 3 comparison cells non-SAFE for four controllers; 0 counter-examples | N2 is a necessary-condition test; its confirmation is close to tautological once T-A is accepted. 2 false SAFE (M0, b39 S2/S3) show V/O can disagree after 50 ms | "A classification with proved necessary conditions; empirically recovered set, not a certified one" |
| **K1** | Equilibrium feasibility, multiple saturation (T-C) | E(d) ≠ ∅ | N1 proved (trivial) | E* selection | E* exists in 42 TEST targets | ≥ 2 saturated units only in OC3 (unstable target) | Claim feasibility check; **no** multiple-saturation restoration claim |
| **K2** | T-A and Proposition OS: h_j(ξ(t_e⁺)) = a_j; reference displacement ≤ T v̄ | algebraic reset, rate-bounded class | **Proved**. Gap: Prop. OS bounds reference displacement; the plant-gain step to the physical difference is stated, not quantified | `dec054_opf` Algorithm 1 | 4 controllers equal in first 50 ms within 5.8e-5 pu; e ∈ [−4.0e-5, +1.84e-3] pu | first swing after 50 ms uncovered (2 false SAFE at M0); U_D8 = 0.0109 pu band | **Strongest original element**: safety at t_e⁺ is a dispatch property |
| **K3** | Lemma C: v*(ξ*) = 0, ξ* fixed point; exact f/V restoration at E* | valid target, A-INFO | **Proved** (algebraic) | centered offset, switch at t_e + τ_info | f error ≤ 7.5e-7 Hz and V error ≤ 1e-3 pu in 36 runs; B2 leaves 36–37 mpu | uses the supervisory target (information B2 lacks); gain from centering alone vs from information is **not separable** (section 3) | "Restoration to the selected equilibrium given the supervisory target" |
| **K6** | Preventive dispatch M3+OS makes the post-event state safe (prediction, not a theorem) | OC1/OC2, P steps | not a theorem | Algorithm 1 | OC1 rev3 7/9 SAFE; OC2 9/9 | bus 31 counter-example (both cells inadmissible); G-v2 REJECTED (3 cells fail (iv)); OC2 dispatch = 0.06 MW so OC2 says nothing about dispatch | Partially supported; report bus 31 |
| **K7** | Regulation and sharing vs B2/B1s/B4′ | one event kind, 6 cells | descriptive | all four controllers | nadir, settling, sharing, V offset | no dominance (B1s lowest effort and V offset); B5′ has A-INFO | Descriptive comparison with A-INFO declared |
| **K8** | HOCBF/CLF obstruction analysis | — | diagnostic | E9 | E9 | negative result by design | Report as a negative result |
| **K9** | Empirical recoverable set | — | see P3 | — | — | R6 not run | Do not claim a frontier |
| **CRIT (iii-U)** | Proposition U: a cell predicted SAFE cannot be UNSAFE if e ≥ −1e-3 | first 50 ms | proof in IEEE39_DEC061_criterion_iii.md | classifier | 42/42 not falsified | registered post-TUNE; one event kind | Prospective alternative criterion, not validated |

## 2. Differential analysis of B5′ vs B4′ (the specific contribution of the QP)

Data: stored series of 36 B5′ TEST runs and 6 B4′ runs (same event, dispatch, solver, information; only the CLF row differs). Figure F12. Script `dec063_qp.py`; results `IEEE39_DEC063_qp_analysis.json`, `IEEE39_DEC063_qp_binding.json`.

**(a) Where and when the QP acts.** In all 36 B5′ runs the solver path is used, only in a window ending at most 4.29 s after the event (t ≤ 9.29 s); afterwards 100 % of calls take the fast path (v = v_nom, QP inactive). For the reference cell OC1 rev3 b21 S2: 1874 solver calls in [5, 6) s, 293 in [6, 10) s, none after 8.06 s.

**(b) What the solver does.** In 99.999 % of solver calls (all but one of ~98 000) at least one rate component is saturated at v̄. For all 33 runs at OC1 rev3, OC2 M3+OS and OC2 M0 the distance of every box barrier row to its binding threshold (c_j − v̄_k/α) is ≥ +0.113 pu: **no box barrier row can bind there**, so the activations are the rate box. Only the nine OC1 M0 runs have a row that could bind (SG31 Pmax, gap down to −0.060 pu; minimum reference margin of the run 0.024–0.029 pu). "Could bind" is not "does bind": the logs do not record which row is active, and the controller does not log multipliers. With a diagonal quadratic cost and non-binding rows, the QP solution reduces to the component-wise clip of v_nom to ±v̄ (B4′), which is the same operation B1s applies as anti-windup. B4′ solver calls differ from B5′ by 2–10 per run.

**(c) What the CLF row adds.** The soft CLF slack is positive in 32 of 36 B5′ runs (62–701 calls in the same 3–4 s window, max 2.2e-6 normalised): the CLF decay condition is saturated by the rate box and met only up to a small slack, i.e. the CLF row is *active but not satisfiable in full*, so V̇ ≤ −λV is not enforced at those instants. The resulting B5′ − B4′ difference over six S2 cells: commanded P ≤ 14.1 mpu (at t ≈ 8–10 s), f_COI ≤ 1.31 mHz, unit V ≤ 0.20 mpu, at 200 s f error differs by ≤ 6.2e-10 Hz. These differences are small compared with the effect of the dispatch (101 MW) and of centering (B2 offset 36 mpu), but they are not zero.

**(d) Does the QP evaluate better?** Not demonstrable with the data:
- **No violation avoided:** B2 and B1s, which have no barrier rows, never leave W at M3 cells (min c ≥ 0.147). At OC1 M0, where the barrier could matter, no B2/B1s/unfiltered-centered runs exist, so a counterfactual is missing.
- **No improvement attributable to the CLF:** the five metrics are within the differences above, and the data give no sign test (B4′ does not log the Lyapunov value, which depends on states not stored).
- **Theory agrees:** T2's proof shows that near ξ* the QP returns v_nom; the stability result is a property of the centered loop.

Statement to carry into the paper: *the filter guarantees reference-set invariance by construction and acts as a rate limiter during the first ~4 s; no experiment here shows that the CLF row improves stability, safety or regulation.*

## 3. Attribution of improvements

| Effect | Evidence in hand | Design | Conclusion level |
|---|---|---|---|
| **Dispatch (M3+OS vs M0)** | B5′ at M0 vs M3+OS in OC1, 9 cells; Prop. OS makes the first 50 ms controller-independent (HB1: 4 controllers within 5.8e-5 pu) | same controller, event, solver; only z changes (deterministic simulation) | **Causal within the simulation** for B5′ and, by Prop. OS and HB1, for the first 50 ms of any rate-bounded controller. Not measured at M0 for B2/B1s/B4′, so effects after 50 ms at M0 for them are not measured |
| **Centering + supervisory target (A-INFO)** | B2 vs B4′/B5′ at M3: V offset 36 mpu vs 0.1–0.6 mpu, f error 2.4e-4 vs ≤ 4e-7 Hz | B2 has neither; B4′ has both | **Association**. Separating the centering from the information requires a centered controller with the *pre-event* target (B3, DEC-057) under the TEST events, which does not exist. Older B3-vs-B2 data (DEC-055/056 P+, Q+, with exact-disturbance reference) point the same way but are a different campaign |
| **Rate limiting / barrier (QP hard rows)** | B4′ vs B1s partially: both clip rates; B1s lacks centering, barrier rows and A-INFO | not an isolated contrast | **Not separable** from centering and A-INFO; barrier rows not observed binding at M3 |
| **CLF row** | B5′ vs B4′ | single-factor contrast | **Causal but small and of unknown sign for benefit**: ≤ 1.3 mHz, ≤ 14 mpu command, none at 200 s |
| **Dispatch vs controller on safety classes** | OC1: dispatch changes classes (7 → 1 UNSAFE at b21/b39); the 4 controllers fail together at b31 | | The safety outcome is explained by dispatch and T-A, not by the controller |

OC2 cannot support the dispatch effect (0.06 MW redispatch); it supports only controller behaviour at a case with headroom.

## 4. Results audit

- **G-v2 stays REJECTED** (criterion (iv) fails in OC1 rev3 b7 S3 1.278e-3, b16 S3 1.015e-3, b24 S3 1.011e-3 pu); DEC-059/060 verdicts unchanged; TEST was opened by a post-TUNE modification of the access rule, recorded in `IEEE39_DEC062_gate_TEST_access.json` (commit 6d2d320, tag `dec062-freeze`) and labelled `EVALUATION_UNDER_MODIFIED_ACCESS_RULE`.
- **Chronology (IEEE39_DEC063_audit.json, `dec063_audit.py`):** freeze 08:03:26; predictions, hypotheses, falsifiers, plans sealed in f42fb9a 08:43:14; all 54 TEST/CMP run directories written after the seal (0 older); SHA-256 of every stored file of the 54 runs matches `hashes.json` (0 mismatches); 38 sealed files (predictions, plans, protocol, code) unchanged between f42fb9a and HEAD; `dec059_b5.py`, `dec059_tds.py`, `dec059_pred.py`, `dec059_eq.py` unchanged since the freeze tag. Run counts: 36 TEST + 18 CMP. Limits of this audit: git timestamps are local-clock and not externally notarised; the sealing is by commit, not by a third party.
- **Classification and uncertainty:** classes by M3V-1 with the numerical band U_D8 = 0.0109 pu; one INDETERMINATE cell (OC1 M0 b21 S1) kept visible.
- **Cases to keep visible in the paper:** OC1 rev3 b31 S2/S3 UNSAFE (inadmissible at the jump, outside the hypotheses of the safety claim, failing for B5′, B4′, B2, B1s); OC1 M0 b39 S2/S3 **false SAFE** (Pmax after 50 ms −0.0156 and −0.0451); OC1 M0 b21 S1 INDETERMINATE; pre-registered hypotheses HA1, strict HA2 and HA7 falsified; OC3 documented as unstable target and out of scope; G-v2 failures.
- **Unchanged weaknesses:** the unit-voltage criterion (iv) passes narrowly in two S3 cells (0.951, 0.899 mpu); (iii-U) was proposed after seeing TUNE; the 54 TEST runs share a single event type.

## 5. Manuscript preparation

**Reframed contributions (each tied to evidence):**
1. *T-A and Proposition OS:* the post-event physical admissibility of any rate-bounded secondary controller is fixed by the pre-event dispatch; verified controller independence over the first 50 ms (K2). Strongest.
2. *Preventive dispatch design with a sub-cycle predictor* (Algorithm 1; accuracy ≈ 2e-3 pu in 50 ms; OC1: class changes at b21/b39; bus-31 counter-example reported) (K6, partially supported).
3. *Centered restoration with supervisory target (A-INFO):* Lemma C, exact f/V restoration at E*, with the information assumption declared (K3).
4. *Discrete reference invariance with constructive feasibility* (T1, T1-F) — a design guarantee, standard in technique, not an observed performance gain.
5. *Conditional local stability of the sampled centered loop* (T2).
6. *P3 classification and the negative HOCBF/CLF obstruction result* (K8).
7. *Methodological:* pre-registered blind evaluation with reported falsifications.

**Recommended title direction (investigator to decide):** based on the DEC-059 suggestion, "Information-Aware Centered Distributed Frequency–Voltage Control with Discrete Reference Invariance and Preventive Post-Event Admissibility in Hybrid SG–GFM Power Systems". Remove "Nonlinear Stability", "Dynamic Safety" and "CLF–HOCBF" from heading, abstract and keywords unless qualified (local; evaluated; reference-level).

**Abstract and conclusions must not say:** regional or certified stability; physical-output invariance; restoration under multiple saturation; a certified recoverable set; that the CLF–QP improves stability or safety; that preventive dispatch protects every bus; superiority of B5′ (no dominance); universal safety. Each remaining statement needs its domain (IEEE-39 C2, SG–GFM, P steps, OC1/OC2, first 50 ms, U_D8).

**Sections of `main.tex` to rewrite:** the methodology subsections on HOCBF (149–258), regional certificate (316–363) and CLF–HOCBF controller with the three theorems (363–490) correspond to the abandoned formulation; T1, T2, T-A, P3 replace them (IEEE39_DEC059_theory.md §0 already maps this). Current text is a methodology draft for the original formulation.

**Comparison with the literature.** Restricted to the 11 entries of `references.bib`, read at abstract and introduction level; a systematic search has **not** been done, so "first" or "novel" cannot be asserted yet.

| Work | What it provides | Relation to this paper |
|---|---|---|
| Kavvathas 2025 (distributed integral controller, capability curves via invariant sets) | the baseline RDC (B2); capability limits enforced without saturation units; stability study | B2 here. This paper adds centering on a post-event equilibrium, a rate-box filter, and the dispatch/jump-admissibility analysis. The overlap in constraint handling must be argued explicitly |
| Wang 2026 (GFM/GFL projected primal-dual, capacity and thermal limits); Mo 2026 (projected PDGD, capacity limits throughout transients) | distributed restoration with capacity guarantees by projection | alternative constraint mechanism; no jump-admissibility theorem in their abstracts. Not benchmarked here |
| Tang 2026 (CBF-based distributed safe frequency, microgrids) | CBF-QP on frequency safe set | closest in technique (barrier QP); on frequency, not on unit P/Q/S/V limits of a DAE with an algebraic reset |
| Ma 2026 (MPC with nodal frequency/RoCoF) | constrained frequency control | different objective |
| Zhuang 2026 (GFM/GFL small-signal decoupling) | stability conditions of converter mixes | context for the plant |
| Chen 2023; Zhang 2024 ×2 (shielded/projected DRL, distribution voltage) | safe action projection in learning controllers | different setting |
| Ames 2017; Xiao–Belta 2022 | CBF-QP, HOCBF | methodological sources; HOCBF found inapplicable here (K8) |

Original positioning that the data can defend: (i) T-A/Proposition OS and its use for preventive dispatch, with an externally checkable predictor; (ii) the evidence package (blind evaluation, falsified hypotheses, negative results). Novelty of (i) against literature outside the bib is **unverified**.

**Final tables and figures.**
- Table 1 contribution matrix (IEEE39_DEC062_contribution_status.csv, read together with the corrections in section 1 of this report; the CSV is a historical DEC-062 artifact and is not edited).
- Table 2 TEST class table by OC and dispatch (DEC-062 §2), including false SAFE and UNSAFE cells.
- Table 3 criteria G3 (i)–(iv), (iii-H), (iii-U) separately, G-v2 REJECTED.
- Table 4 controller comparison on six S2 cells (K7), with A-INFO noted.
- Table 5 QP activity: window, rate-box saturation, barrier-binding feasibility, CLF slack, B5′−B4′ differences (this report §2).
- Figures: F8 margins M0 vs M3+OS (dispatch effect), F11 predicted vs observed, F9 comparison, F10 T1/T2 checks, **F12 QP activity (new)**, plus the architecture diagram and the T-A/jump figure (F0, F4) of the DEC-059 plan, not yet produced.

## 6. Theoretical and experimental gaps

Theory: (1) N (T2 domain) unquantified; (2) H1/H4/H5 are floating-point checks, no certified enclosures; (3) no result tying the CLF row to a guarantee: T2 proves the QP inactive near ξ*, and the CLF slack is positive in 32/36 runs; (4) Prop. OS stops at the reference displacement, the physical bound needs a plant gain; (5) regional or recovery-set certificates unavailable; (6) multiple saturation (K1) only in OC3.

Experiment: (1) no unfiltered centered controller (B3 without QP) and no pre-event-target B3 under the TEST events, so QP, centering and information cannot be separated; (2) no B2/B1s/B4′ at OC1 M0, the only place where a barrier row could bind; (3) the Lyapunov value of B4′ is not logged; (4) one event kind, one plant, two OCs; (5) OC1 bus 31 unrecoverable by dispatch; (6) dependence of the dispatch effect after 50 ms at M0 for other controllers.

## 7. Proposal for one limited ablation (awaits authorization; not run)

Only if the investigator wants to keep the QP as a contribution; otherwise gap (1)–(3) are reported as limitations and the paper stays on the reframed scope.

- **Hypotheses.** HQ1: with the barrier rows removed, the centered loop with the same rate box (B3-clip) differs from B4′ by < 1e-3 pu in min reference margin and in unit P/V (barrier rows never act). HQ2: replacing the post-event target by the pre-event one (B3-pre) leaves a voltage offset ≥ 10 mpu at 200 s (offset due to information, not to centering). HQ3: the Lyapunov decay inequality is violated in B4′ at instants where B5′ has positive slack by less than the observed slack scale (the CLF row has no protective role).
- **Falsifiers.** HQ1 false if B3-clip min margin < 0 or differs > 1e-3 from B4′ at OC1 M0 b21/b39; HQ2 false if the offset < 1 mpu; HQ3 false if V̇ + λV ≤ 0 throughout in B4′.
- **Scenarios and budget (6 TDS, ledger 118 of 120).** (1) B3-clip at OC1 M0 b21 S2 and b39 S2 (2 TDS); (2) B3-pre at OC1 rev3 b21 S2 and OC2 M3+OS b21 S2 (2 TDS); (3) B4′ re-run with a pure observer logging V at OC1 rev3 b21 S2 and OC2 b21 S2 (2 TDS; the observer must not change the dynamics, checked bit-for-bit on the stored series).
- **Closure criterion.** Hypotheses and falsifiers registered and committed before any TDS; the result is reported whatever it shows; no further runs; the matrix entries for QP, centering and A-INFO are closed at "separated", "not separated" or "refuted".
- **Needs:** small additions to the comparator code (an unfiltered-barrier variant, a pre-target variant, a V observer), to be listed in the protocol and not to alter the frozen controller.

## 8. Is the manuscript ready to be written?

- **Yes, with the reframed scope (section 5).** The mathematical statements (T1, T2 conditional, T-A, Prop. OS, Lemma C, N1/N2) are consistent with the evidence, and every limiting case is documented.
- **No, with the original `main.tex` framing**: Th1–Th3 and the CLF–HOCBF controller as the central contribution are not supported (relative-degree obstruction, no regional certificate, QP not shown to matter).
- **Before drafting:** investigator decisions on (a) title and the role of the QP (contribution vs implementation detail), (b) whether to authorise the 6-TDS ablation, (c) whether to extend the literature search beyond the 11 bib entries, (d) acceptance of the weaker, domain-bounded claims for K6 and K7.
