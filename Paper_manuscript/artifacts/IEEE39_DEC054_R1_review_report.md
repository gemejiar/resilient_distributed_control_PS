# DEC-054-R1 — Review report (documentary; 0 TDS, no optimisation, no implementation)

Branch `review/dec054-prospective-preventive-dispatch`; start commit `20650745be4da506b043824f2599dc27b526ef7f`. Instructions saved in `ops/sted/DEC054_R1_review_instructions.md`. v1 (`IEEE39_DEC054_preliminary_policy_design.md`) is untouched; the corrected design is `…_v2.md`; issue list `IEEE39_DEC054_design_review_matrix.csv` (21 issues). P0 remains `STOP_BACKUP_NOT_VERIFIED`; `independent_backup_verified=false`; TDS ledger 0/48.

## 1. Gates R1–R7

| Gate | Result | Basis | What remains |
|---|---|---|---|
| R1 — RDC information/initialisation | **PASS (documentary)** | `pn,qn,pset(0),qset(0),gref,k_ip,d_p` recomputed per candidate (`run_e8_ieee39.py:141-154`, `run_b3_ieee39.py:91-100`, `dec051_core.py:94-102`); `d_q` fixed; `C^P_share≡0` corrected; DEC-053 sharing attribution withdrawn | callback/event ordering `UNRESOLVED` (`TO_VERIFY_IN_P2`) |
| R2 — hybrid model, predictor at `0⁺` | **PASS (documentary)** | single post-event formulation `δξ̇=A⁺δξ+f⁺`, no `B_d d`, zero initial condition, drift included, Schur/expm | not validated numerically; fixed `A⁺` over 200 s and limiter modes are declared error sources |
| R3 — safety proposition | **PASS (documentary)** | horizon `[t_e,t_e+200 s]`, ANDES RMS model, finite `𝒟_design`, `H_err` explicit, lower side separate, no `S` from separate maxima, `CONDITIONAL_PROPOSITION` | `H_err` untested |
| R4 — separation algorithm | **PASS (documentary)** | six exit states, deduplication, `STAGNATED_EXISTING_CUT`, local empirical cuts with trust region, symbolic cost in calls | K_max/N_it/r_tr/τ_cut to be sealed |
| R5 — comparators and validity | **OPEN** | common `Z_phys` (Slack, 39 voltages), non-degenerate common `J`, two independent contrasts, partition rule, LOBO/conformal correction (`⌈9·0.9⌉=9>8`) | seed, thresholds, `κ`, purposive-cohort decision and cohort enumeration need investigator approval at P1 |
| R6 — physical feasibility/decision variables | **OPEN** | 19 variables kept as hypothesis; Q is a PF consequence; Slack limits; correct residual condition | GFM initial dynamic residuals and Euler-vs-continuous mismatch `UNRESOLVED` |
| R7 — novelty | **OPEN (partial)** | public search done (TSC-OPF, trajectory-sensitivity DSOPF, frequency-constrained scheduling, surrogate-assisted, SCOPF) + nine project references | DOI/publisher metadata and full texts not confirmed → `EXTERNAL_LITERATURE_PARTIALLY_VERIFIED`, `NOVELTY_NOT_ESTABLISHED` |
| P0 backup | **BLOCKED** | no independent destination | investigator action |

## 2. Required final items
1. **Pn/Qn, d_P/d_Q, k_IP.** Code sets `pn=Pe(0)`, `qn=Qe(0)` and `pset(0)=pn`, `qset(0)=qn` from the candidate state; `d_p=1/pn` moves with `z`, `d_q=1/(Qmax−Qmin)` is fixed; `gref_p,gref_q` and `k_ip=160/Σ(gp0/gref_p)` are recomputed from the capability factors at that state, so reserve and Q position set the effective integral gains. Map `I(z)` in v2 §1.1.
   **Finding F-1 (beyond the instruction, flagged):** the DEC-053 "≈4 % sharing spread / Pn not updated" came from normalising R35_040 by the C2t `unit_pn` (`dec053_core.py:138-139,147`). Read-only recomputation from stored arrays with the executed `pn(z)`: spread `0.0028` (R35_040 P+) vs `0.0094` (C2t P+). The attribution is withdrawn; the original files were **not** edited; the causal reading is `UNRESOLVED`.
2. **Post-jump equation without double counting:** `ξ_0=ξ⁺_d(z)`, `δξ(t_e⁺)=0`, `δξ̇=A⁺_d(z)δξ+f⁺_d(z)`, `P̂_i=P_i(ξ_0)+C⁺_{i,d}δξ`, `D̂_i(t_e⁺)=0`, `Ê^±` from `max(0,±D̂_i)` over `[t_e,t_e+200 s]`; no `B_d d` term (v2 §2.4).
3. **Proposition S** restricted to the ANDES RMS model, finite `𝒟_design`, `[t_e,t_e+200 s]`, under `H_err`; `CONDITIONAL_PROPOSITION` (v2 §2.8).
4. **Cut algorithm:** explicit statuses `FEASIBLE_PREDICTED`, `LOCAL_OPTIMUM_FOUND` (KKT documented), `STAGNATED_EXISTING_CUT`, `ITERATION_BUDGET_EXHAUSTED`, `SOLVER_FAILED`, `INFEASIBLE_NOT_DEMONSTRATED`; no finite-termination or success claim (v2 §4).
5. **Fair comparators:** same AC-OPF base for M0–M3 incl. Slack limits and 39 pre-event voltages; historical C2t (21 buses >1.05 pu) is only a distance anchor; identical non-degenerate `J`; contrasts C-1 (equal cost) and C-2 (minimum cost for a threshold, `NOT_MATCHED` if none) (v2 §5.4).
6. **ε and LOBO:** conformal rank 9>8 ⇒ `+∞`; replaced by `EMPIRICAL_LOCATION_AWARE_MARGIN` (`ε=max(1e-3, κ·max positive residual)`, `κ=1.5`, proposals); LOBO diagnostic only; no coverage statement (v2 §3.5).
7. **Originality:** `NOVELTY_NOT_ESTABLISHED`. Closest mechanism in the literature located: trajectory-sensitivity dynamic-security OPF/rescheduling loops; frequency-constrained scheduling and TSC-OPF constrain other quantities. Candidate mechanism-level contributions C1–C4 are falsifiable (v2 §6, §8).
8. **To be approved by the investigator for P1:** v2 §9 (independent backup; objective `J`; predictor formulation and re-linearisation policy; `ε`, trust radii, `K_max`, thresholds; partition seed/eligibility rule and cohort purposiveness; Q scope policy; the strongest attainable claim; completion of the literature check; acknowledgement of the sharing correction).
9. **Integrity:** see §3.

## 3. Integrity and budget (verified at close)
Protected historical files unchanged against `04e082b` (git diff empty for `Paper_manuscript/artifacts/IEEE39_{E*,B3*,DEC050..DEC053}*`, `Paper_manuscript/src/*` existing files, `Paper_manuscript/cases`, `Paper_manuscript/main.tex`, `plan_maestro.md`, `ops/sted/DEC05[0-3]*`, `decision_log.md`, `traceability_matrix.csv`); P0 manifests and `DEC054_protocol.md` unchanged; `IEEE39_DEC054_tds_ledger.csv` header only (**0/48**); `backup_manifest` status `BACKUP_BLOCKED`; remote `main` `1a023d8fa333e62eb716e57a4d67561bb63ea3d0`; local `main` untouched. Only four new files are committed by this revision.

## 4. Scientific questions that remain open
Is `H_err` plausible for the excursion term on unseen buses? How large is the predictor error with the correct post-event branch (and does recomputing `I(z)` change the predicted maxima, hypothesis H-E)? What explains the stored sharing behaviour on R35_040 once `pn(z)` is used (capability-factor/leakage coupling)? Is a piecewise-affine predictor needed over 200 s? Is the Q module reliable enough to be in the cohort? Can an informativeness rule be avoided without a trivial cohort? What do complete DOIs/full texts say about the nearest dynamic-security OPF works?

## 5. Stop condition
v2 delivered; stopping for human scientific review. No P0/P1/P2/P3 approval, no simulation, optimisation or implementation.
