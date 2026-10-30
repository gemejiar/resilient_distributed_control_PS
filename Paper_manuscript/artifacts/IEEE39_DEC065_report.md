# DEC-065 report: theoretical consolidation, originality and restructuring of the manuscript

Written for: the investigator who issued DEC-065. Branch `review/dec059-scientific-reorientation`. **No TDS (ledger 112/120), no change to ANDES, controllers, dispatches, criteria, historical files, `main` or the original `main.tex`; nothing pushed.** New: `dec065_litsearch.py`, `dec065_os.py`, `dec065_gronwall.py` (read-only analyses of stored runs; power flow and Jacobians only), `IEEE39_DEC065_{search_log.json, search_candidates.csv, os_check.json, os_gronwall.json, proofs.md, literature_matrix.csv, originality_matrix.csv, report.md}`, `Paper_manuscript/main_revision_DEC065.tex` and `Paper_manuscript/references_dec065.bib`. The original `main.tex` is preserved byte-identical (git blob `afbaf8616444d8d416d051fe5f566af6527e8f3575`, commit 0db386b); the revision is a separate file and is **not** the definitive version.

## 1. Decisions C1–C8 as applied

| ID | Decision | Applied as |
|---|---|---|
| C1 | approved, restricted to the post-event instant with explicit continuity | Theorem T-A states H-DAE and H-C; the sampled update $\eta\le h\bar v$ is treated (Corollary A.1) |
| C2 | pending: derive OS | see section 2: proved for the linearised plant, nonlinear bound not obtained |
| C3 | approved, bounded | Sec. 4 and 7.1: single-factor contrast on three cells, bus 31 and false SAFE kept |
| C4 | conditional | Sec. 5.1: how E* is obtained and what the supervisor needs; exact-target hypothesis added |
| C5 | auxiliary adaptation | Theorem 2 with the Breeden et al. reference; no originality claimed |
| C6 | local, conditional, not due to the QP | Theorem 3 and Sec. 7.3–7.4 |
| C7 | classification, not certificate | Remark in proofs file; P3 not promoted in the manuscript beyond that |
| C8 | keep everything negative | Sec. 6, 7.2, 7.6 and 8 |

## 2. Proposition OS: what was wrong and what can be proved
Details and proofs: `IEEE39_DEC065_proofs.md`. **Incorrect hypotheses of the previous version:** (1) a common bound $\bar v$ for all rate-bounded controllers (B2 reaches 6.27 × $T\bar v$); (2) an undefined plant gain and norm; (3) the 5.8e-5 pu "independence" referred only to the minimum-Pmax margin, whereas unit P/Q/V outputs at $t_e+50$ ms differ by up to **5.0e-4 pu** (B1s) and 3.8e-4 pu (B2); (4) no separation of the jump (controller independent) from the evolution (not). **Derived:**
- *Theorem OS-L* (proved): output bound for the linearised DAE, $\sum_k w_k(\int_0^T|[C_xe^{A(T-s)}B]_{jk}|\,s\,ds+|C_{u,jk}|T)$, with per-controller rate bounds: box for B5′/B4′; B1s from the state continuity of ω and the jump of V; B2 from the jump of the algebraic outputs at $t_e^+$ (computable) but **no bound over the interval for B2** (empirical rate used).
- *Theorem OS-N* (proved, conditional on Lipschitz constants): Gronwall bound. With the norm constants of the frozen linearisation (208 states, $L_x\approx2.9\times10^4$ s⁻¹) it overflows: **vacuous**. A useful nonlinear bound is not demonstrated.
- *Numerics* (estimates, not certificates): the OS-L bound holds in 18/18 controller pairs (0.78–1.76 mpu against $U_{D8}$ = 10.9 mpu); bound/observed 1.6–5.6 where the difference is non-negligible; the linear model reproduces observed output differences (3.82e-4 vs 3.84e-4; 2.46e-4 vs 2.47e-4 pu). Feedthrough $\|C_u\|\approx10^{-16}$.
**Classification:** PROVED for the linearised plant + NUMERICAL-ESTIMATE + EMPIRICAL; not a nonlinear theorem. Needs your decision whether the manuscript keeps it as a proposition (as written) or as an empirical observation only.

## 3. Audit of the other proofs (summary)
T-A, N2: correct; needed H-C and the sampled-data qualification (omitted before); N2's confirmation is a consistency check. Lemma C: correct; **added hypothesis: exact target** (mismatch not covered). T1: correct, valid for variable step; the core inequality is the standard discrete barrier condition; open whether centering preserves the RDC's inward-pointing property. T2: conditional; H1, H4, H5 floating point; N unquantified; QP inactive on N by the proof; consistent with 36/36 runs on the fast path after ≤ 4.29 s. P3: N1 and N2 proved; N1 not exercised; V does not imply recovery.

## 4. Literature (reproducible search)
`dec065_litsearch.py` queries Crossref (10 queries × top 25, ISSN-filtered to TPWRS, TSG, TSTE, TEC, TPEL, Automatica, TAC, TCST, IJEPES, EPSR, 2021–2026) and arXiv (3 queries); log with date and every record in `IEEE39_DEC065_search_log.json` and `_search_candidates.csv` (260 unique, 202 pass a rule-based title screen). After manual title screening, about a dozen additional candidates were identified and their Crossref/arXiv records verified (DOI, venue, year, authors); **only the arXiv texts could be read** (Breeden et al. and Delimpaltadakis et al., abstract and introduction). IEEE/Elsevier full texts are not accessible here; those candidates are marked "not read" in `IEEE39_DEC065_literature_matrix.csv` (R16–R21). **Consequently the originality matrix cannot support a priority claim.** Not accessed: IEEE Xplore, Scopus, Web of Science; OpenAlex not used (shared anonymous budget); only the top 25 per query.
Findings that matter for the claims: (a) the discrete barrier condition behind T1 is standard (Breeden et al.), the RDC already guarantees reference invariance (R1); (b) CBF correctors on secondary control exist (Mo–Liu arXiv 2025; Tang 2026); (c) preventive dispatch with dynamic criteria exists at system level (Paturet 2020) and as candidates (Yuan 2022, not read); (d) none of the works read states Theorem A for unit-level limits. **Four candidates must be read before any statement of novelty:** R16 (preventive dispatch against transient instability), R18 (bounded integral controller, lineage of the RDC), R17 and R19.

## 5. Originality table
`IEEE39_DEC065_originality_matrix.csv` contrasts T-A, OS, M3+OS, centering, T1, T2, P3 and the QP with the closest antecedents, what they do, the overlap, the difference claimed, the basis of comparison, the allowed wording and what is pending. Permitted wording throughout: "we state and prove…; among the works examined we did not find…".

## 6. Revised manuscript (`main_revision_DEC065.tex`)
Structure: Introduction and gap; system model and constraints; post-event admissibility (T-A, N2, OS); preventive dispatch and predictor; centered regulation and conditional guarantees; experimental design and traceability (gates, modified access rule, A-INFO); results (classes, criteria and hypotheses, T1/T2 checks, comparison with attribution, QP activity, negative results); discussion, limits, conclusions. It compiles (8 pages, 0 undefined references; minor overfull boxes in two long formulas/tables) with `references.bib` plus `references_dec065.bib` (six verified entries). Title as instructed. Original `main.tex` untouched.

## 7. Items that require the investigator's review (exact list)
1. **OS status:** keep as "Proposition (linearised) + numerical estimate" or demote to empirical only (section 2).
2. **Redispatch magnitude:** DEC-061 records 99.4 MW for rev3, DEC-062 reports 101 MW; the manuscript says "about 100 MW". Confirm the figure and its definition.
3. **Algorithm 1 and ε_OS:** Section 4 of the draft is a summary of what was implemented ("calibrated on design and tuning events"; requirement $a_j\ge\varepsilon_{OS}+U_{D8}$ for the design events); the formal statement must be written from `dec054_opf` and checked.
4. **ANDES and case citations:** `\todo` in Sec. 2.1; no source for the case or for ANDES is in the bibliography.
5. **Information assumption:** the statement that the supervisor needs the load change and a model identical to the plant, and that this favours the centered controllers.
6. **Abstract numbers and wording:** 7 of 9 safe, 2 at bus 31, 2 false SAFE; "gate modified after tuning"; one-sided criterion proposed after tuning.
7. **Open mathematical question:** whether centering preserves the original RDC's inward-pointing property (T1 redundancy).
8. **U_D8 provenance:** "estimated in the numerical audit of the algebraic jump" is a summary; confirm.
9. **Literature:** authorise reading R16–R19 (access needed) before the novelty paragraph is finalised; the "Literature search note" is a placeholder.
10. **Unit-output differences up to 5.0e-4 pu** (versus the 5.8e-5 pu quoted before): confirm that the manuscript quotes both with their definitions (it does).
