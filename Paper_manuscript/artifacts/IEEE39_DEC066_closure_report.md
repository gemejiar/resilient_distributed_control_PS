# DEC-066 — Experimental closure report (M3+OS ablation, equal-effort controls, validation)

Branch `review/dec066-m3os-closure`, local, parent commit on remote `3338c30`. OC1, controller B5', ANDES 2.0.0 RMS/phasor. All numbers are in the CSV files named below; the LaTeX tables are generated from them.
Governing document: `DEC066_PLAN_CIERRE_EXPERIMENTAL_PAPER.md` was **not found** in the repository or the worktree; the investigator's order of 2026-10-30 was followed as written.

## 1. Budget and ledger (`IEEE39_DEC066_tds_ledger.csv`)

34 of 40 TDS used, none with a solver failure: E1 17, E2 3 (ablation lots, already pushed), F2 4 (equal effort), F3 5 (out-of-design and counter-condition), F4 4 (fixed fine step), F5 1 (step robustness of A at b21 S3).
Reassignment (documented in `dec066_tds2.py` and the protocol): the unused quota of E1 (3), E3 (12) and E4 (4) funds F2–F5; the total ceiling of 40 is unchanged; 6 TDS are unused. Plans F2–F4 were sealed with the hash of `dec066_tds2.py` before the F5 quota line was added (the only change is the budget table).
Deviations from the order: (i) F3 uses b18 S3 (A, D), b18 S2 (D only) and b39 S2 (A, D) = 5 TDS instead of b18 S2 and S3 for A and D, to include a predicted counter-condition; the b18 S2 cell of A was not run. (ii) F4 is a fixed step Δt/16 over 20 s; the historical executor already uses Δt/16 in 0–0.5 s, so F4 reproduces it by construction. (iii) F5 (1 TDS) was added to decide the robustness of the UNSAFE label of A at b21 S3. (iv) The control EQ2 ended with `SOLVER_FAILED`.

## 2. Hypothesis and evidence matrix

| Id | Hypothesis (sealed before the run) | Evidence | Outcome |
|---|---|---|---|
| H1 | At equal effort, dense evaluation (DQ1) beats a uniform band (E) at b8 S3 by ≥ 0.0025 pu | DQ1 +0.0071 vs E −0.0038 pu | CONFIRMED (+0.0109) |
| H2 | At equal effort, D beats the uniform band EQ1 at b8 S3 by ≥ 0.0025 pu | D +0.0136 vs EQ1 +0.0046 | CONFIRMED (+0.0090) |
| H3 | b21 S3 order D > EQ1 > DQ1 > E, claims only for ≥ 0.0025 pu | D +0.0041, EQ1 −0.0010, DQ1 −0.0025, E −0.0094 | PARTLY: D−EQ1 +0.0050 and DQ1−E +0.0069 confirmed; EQ1 vs DQ1 not distinguishable (+0.0015) |
| H4 | Observed − predicted in [0, +0.0025] pu | F2: +0.0003 in 4/4 | CONFIRMED for F2 |
| G1 | b18 S3: A and D SAFE, D larger | +0.0606 / +0.0756 | CONFIRMED (no violation to avoid) |
| G2 | b18 S2 (D): SAFE | +0.1536 | CONFIRMED |
| G3 | b39 S2: 0–10 s order D > A; 10–195 s compared with its prediction | 0–10 s D 0.1611 > A 0.1338; 10–195 s observed 0.1571/0.1283 vs predicted 0.0048/0.0137 | 0–10 s CONFIRMED; **long-horizon predictor REFUTED** (error +0.115/+0.152 pu, order reversed) |
| G4 | F3 errors in [0, +0.0025] | b18 S2 D +0.0033, b39 S2 A +0.0058, D +0.0056 | REFUTED for 3 cells (all conservative) |
| N1 | Fixed Δt/16 reproduces historical margins to ≤ 0.0005 pu | differences ≤ 1e-5 pu, same peak instant | CONFIRMED (trivial: local step already Δt/16) |
| R1/R2 | A at b21 S3, Δt/2: change ≤ 1.3e-4 pu and class kept | −0.01097 → −0.01114 (−1.7e-4) | R1 marginally REFUTED; class UNSAFE kept at both steps, 2.4e-4 pu from the threshold |
| Ablation (earlier) | dense > ε_OS; U_D8 alone does not avoid the violation | b8 S3: dense +0.0171, ε_OS +0.0004, U_D8 +0.0109; E violates | CONFIRMED; ε_OS null |

## 3. Main findings

1. **Equal effort (T7, T7c, F8).** D keeps +0.0090 (b8 S3) and +0.0050 pu (b21 S3) more margin than EQ1 (uniform band, 61.3 vs 61.2 MW); DQ1 keeps +0.0109 and +0.0069 pu more than E (58.6 vs 58.8 MW). D is cheaper than EQ1 in J (1.759 vs 1.771), DQ1 cheaper than E (1.728 vs 1.731). Equal redispatch is not equal cost.
2. **Attribution (T8).** The observed excursion of the limiting unit is the same for all designs (0.2062–0.2064 pu at b8 S3, 0.3048–0.3049 pu at b21 S3); margin differences equal pre-event headroom differences to within 2e-4 pu. The benefit is a redistribution of preventive headroom, not a change of the excursion. No design reduces the peak.
3. **Convergence (T4e).** No design passes the local-optimum test. A, B, DQ1 are reproduced from other start points (Δz ≤ 1.7e-4, ΔJ ≤ 1.3e-6). The KKT residual of B (0.598) is an artefact of the finite-difference residual (the same point gives 0.027 from another start): it is neither evidence for nor against convergence. Algorithm 1 starts from the case dispatch and uses the seed only on failure, so the initialisation was already common; the earlier statement "A was seeded with M0" is withdrawn.
4. **Active sets.** The draft statement that A–E have the same active constraints was wrong: at b23 S3, A has SG31, SG35, GFM36 active, B–E add SG33, D has GFM32 within 1.4e-4 pu.
5. **Out-of-design.** Only bus 18 is out-of-design; all designs predict it safe, so it cannot show an avoided violation (generalisation of the predictor and absence of harm only).
6. **Prediction quality (T8).** 24 cells admissible at the jump: error +9.4e-4 pu mean, +1.2e-4 to +5.8e-3 pu, all conservative at 0–10 s. The 10–195 s predictor is unreliable (b39 S2; b18 S3 of A is 0.010 pu non-conservative).
7. **Step sensitivity.** Δt/2, Δt/4 (E2, F5): ≤ 1.7e-4 pu; Δt/16 fixed (F4): identical. The UNSAFE class of A at b21 S3 is marginal; the physical violation (0.011 pu) is robust.

## 4. Contributions

- **Demonstrated (within OC1, two to six events, RMS):** (a) dense 0–50 ms evaluation anticipates sub-cycle power excursions that the 3.9 ms-grid predictor does not represent and the 0–10 s predictor is conservative; (b) it redistributes preventive headroom to the critical units and at equal redispatch effort gives 0.005–0.011 pu more observed margin than a uniform band, with lower J; (c) this benefit is entirely headroom (excursion unchanged).
- **Conditional:** that M3+OS avoids the Pmax violations that M3 shows (4 of 6 events vs 1 of 6) — the events are mostly design-set or previously observed, most violations lie inside the numerical band (INDETERMINATE), and the effect is a few percent of Pmax in ≤ 3 ms with unknown physical tolerance; the margins at equal effort rest on two events.
- **Not supported:** a contribution of ε_OS (null, +0.0004 pu); generalisation to unseen buses or other operating conditions (only bus 18, non-discriminating); OC2/OC3; instantaneous protection, EMT or converter-level claims; that M3+OS damps overshoot; the 10–195 s predictor; restoration of admissibility at b31 S2; optimality or KKT certification of any design; independent backup of the raw series.

## 5. Backup status

Unchanged: independent backup waived by the investigator; same-disk SHA-256-verified copy only (`C:\Users\gemej\dec066_backup_samedisk`, Addendum C). `backups/` lies inside the OneDrive folder (files flagged "always keep on this device"), which suggests a cloud copy; its presence and restorability have **not** been verified. No independent backup is declared.

## 6. File index (tables T1–T8, figures F1–F8)

T1–T3 `IEEE39_DEC066_T1..T3*.csv` (P0); T4 `T4_OPF_ablation`, `T4b*`, `T4c`, `T4d`, T4e `T4e_convergence`; T5 `T5_observed`, `T5_F2..F5_observed`, `T5b_pred_vs_obs`; T6 `T6_contrasts`; T7 `T7_equal_effort`, `T7b`, `T7c_equal_effort_observed`; T8 `T8_all_cells`. Figures in `figures_main/`: F1 `M0_vs_M3OS`, F2 `critical_transients`, F3 `predictor_validity`, F4 `F4_final` (ablation), F5 `safety_vs_dispatch_effort`, F6 `dispatch_by_unit`, F7 `transients`, F8 `F8_equal_effort` (`F8_prelim` is superseded). LaTeX: `IEEE39_DEC066_results_draft.tex` (inputs `IEEE39_DEC066_ablation_results.tex`, `IEEE39_DEC066_ablation_tables.tex`, `IEEE39_DEC066_closure_tables.tex`); compiles with IEEEtran (9 pages, no undefined references).
Scripts: `dec066_budget.py`, `dec066_budget_analysis.py`, `dec066_t7.py`, `dec066_tds2.py`, `dec066_obs2.py`, `dec066_close.py`, `dec066_conv.py`, `dec066_close_latex.py` (plus the earlier `dec066_abl_*`, `dec066_tds.py`).
Raw runs and states are in `backups/` (not versioned).

## 7. Stop criteria

Optimisation controls interpretable and documented; the advantage over a uniform reserve at equal effort confirmed on two events; temporal sensitivity of the critical results checked; generalisation evidence delimited (one non-discriminating bus); tables, figures and text generated from the result files. No further TDS recommended; optional work (not done): a second out-of-design bus with a predicted violation (none found among the evaluated buses), OC2.
