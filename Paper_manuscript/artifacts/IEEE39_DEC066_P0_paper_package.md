# DEC-066 P0/P1: paper package (Entrega 1, 0 new TDS)

Branch `review/dec066-m3os-closure`. All results come from the 112 historical raw run directories (hashes verified in G0) and the stored dispatch/prediction files; the window-resolved predictions were recomputed with the existing predictor (PF + linearisation, no TDS). Scripts: `dec066_p1.py`, `dec066_paper_tables.py`, `dec066_paper_figures.py`, `dec066_paper_latex_tables.py`. The 36 `IEEE39_DEC066_P1_traj_*.npz` (90 MB: predicted and stored series) are reproducible with `dec066_p1.py` and are excluded from Git.

## Question answered by each item
| Item | File | Scientific question it answers |
|---|---|---|
| T1 | `IEEE39_DEC066_T1_dispatches.csv` | What do the dispatches M0, M1, M2, M3, M3+OS, cut and rev3 cost (J, ΣΔP vs M0 and vs case, status, KKT, time)? |
| T2, T2b | `IEEE39_DEC066_T2_observed_safety.csv`, `_T2b_cells.csv` | Observed class per OC, dispatch and severity; limiting unit, peak time and window (jump/fast/mid/slow); Q/S/V violations |
| T3, T3b, T3c | `IEEE39_DEC066_T3_predictor.csv`, `_T3b_horizon_sweep.csv`, `_T3c_horizon_sweep_cells.csv` | Predictor error (50 ms vs 195 s), false SAFE/UNSAFE, retrospective classifier horizon |
| P1 data | `IEEE39_DEC066_P1_windows_<OC>_<dispatch>.csv` | Jump, 50 ms, 195 s predicted maxima and stored TDS maxima per window, per cell |
| F1 | `figures_main/DEC066_F1_M0_vs_M3OS.{pdf,png}` | Does the preventive dispatch improve observed Pmax compliance in OC1, and why OC2 shows nothing |
| F2 | `DEC066_F2_critical_transients` | What do the critical transients look like in three windows (b21 S2, b39 S2, b31 S2) |
| F3, F3b | `DEC066_F3_predictor_validity`, `DEC066_F3b_predictor_validity_rev3` | Why the 50 ms classifier produced two false SAFE and what the 195 s predictor does |
| F5 | `DEC066_F5_safety_vs_dispatch_effort` | Violations against redispatch effort (DEC-054 cohort: M0…M3; DEC-062 OC1) |
| F6 | `DEC066_F6_dispatch_by_unit` | Where the redispatch moves power and the resulting headroom |
| LaTeX | `Paper_manuscript/IEEE39_DEC066_results_draft.tex` (+ `IEEE39_DEC066_tables.tex`, generated from the CSVs) | Results and discussion draft: setup, dispatch, predictor, ablation (pending), limitations |
F4 (OS ablation) is pending the designs B, C, E (running, 0 TDS).

## Main findings
1. **Preventive dispatch effect (OC1).** 54 runs regenerated with 0 differences. Blind cells (n = 9 per dispatch): M0 1 SAFE / 1 INDET / 7 UNSAFE; M3+OS rev3 7 SAFE / 0 / 2 UNSAFE (b31 S2, S3, inadmissible at the jump). b31 jump margin improves from −0.272 to −0.086 pu (S2) and −0.425 to −0.239 pu (S3) but stays negative. OC2: 9/9 SAFE both dispatches, difference 0.058 MW: no effect shown.
2. **Redispatch.** rev3: ΣΔP = 101.07 MW vs M0 (99.35 MW vs case). Power moves to the slack SG39 (+100.1 MW; headroom 529.7 → 429.6 MW) from SG33 (−40.0), SG35 (−25.6), SG31 (−18.6) and GFM36 (−15.9); headroom of SG31 3.4 → 22.0 MW, SG35 9.5 → 35.1, SG33 29.3 → 69.3, GFM36 14.5 → 30.4 MW.
3. **The false SAFE are a classifier-horizon problem, not (only) predictor error.** The dense 50 ms predictor has bias +1.7e-4 and RMSE 4.5e-4 pu (36 cells), but b39 S2/S3 at M0 violate Pmax at SG31 at 3.40 s and 3.54 s (−0.0156, −0.0451 pu), outside the window. The existing 195 s propagation classifies both UNSAFE, 35/36 cells agree with no false SAFE (1 false UNSAFE: OC1 M0 b39 S1). **But** its worst point is wrong: SG35 at 195 s (−0.25, −0.41 pu), while observed SG35 stays positive; for SG31 the predictor reproduces the first 10 s (error ≈ 0.007 pu at the minimum). Overall RMSE at 195 s: 1.92 pu (0.079 excluding |margin| ≥ 1 pu; 0.011 in OC2). Horizon sweep (retrospective, same 36 cells): T_c = 1, 10, 60 s → 35/36, 0 false SAFE, 0 false UNSAFE.
4. **OS decomposition (design level, no TDS).** M3+OS = dense 50 ms + ε_OS (3.9e-4 pu up / 6.1e-5 down) + U_D8 (0.0109 pu) on both excursion bounds; U_D8 is 28× ε_OS. Design redispatch vs M0: M3 55.3 MW, M3+OS 62.1 MW (same 12 design events). Whether OS adds observed safety is not yet shown.
5. **M0…M3 prospective cohort (DEC-054, different design set, 24 TDS).** Violating scenarios: M0 6/6, M1 0/6, M2 1/6, M3 0/6; ΣΔP vs M0: M1 156.1, M2 15.7, M3 44.2 MW.

## Data gaps (not invented)
- M1 and M2 have no events in common with DEC-062; M3 (DEC-055) and M3+OS (DEC-059, before rev3/cut) have no stored TEST runs: comparisons among them in observed safety are only available for the DEC-054 cohort.
- `min margin (design)` in T1 is as recorded in each state file and its definition differs between DEC-054 (describe) and DEC-059 (`margins_all_cells`, over 20 monitored cells); rev3 shows −0.0096 pu there; not interpreted.
- Time per design depends on the number of workers used in each campaign.
- Q/S/V: only one cell shows an observed violation of that kind (OC1 M0 b31 S3: upper voltage band exceeded by 2e-4 pu; in the same cell the P violation is the dominant one).

## Proposed TDS (ceiling 40, not quota) — Entrega 2
1. Ablation, observed effect: events b21 S2, b39 S2, b39 S3, b31 S2 (OC1) × dispatches A (M3), B, C, D (M3+OS original), E → ≤ 20 runs; designs that coincide within ~1 MW are not duplicated.
2. Timing/integrator pilot: b39 S2, S3 at M0, Δt = 2⁻⁹ and 2⁻¹⁰ → 4 runs.
3. Unused buses: bus 18 and buses used only in DEC-054 (15, 26) × S2, S3 × {M0, rev3} → 12 runs.
4. Reserve: 4.
Prerequisite: the procedural exception for the blocked backup (copy of essential raw files, documented risk) must be recorded before the first new TDS; the historical `BACKUP_BLOCKED` is not edited.
