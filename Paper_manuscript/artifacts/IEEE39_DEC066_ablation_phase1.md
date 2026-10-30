# DEC-066 ablation, phase 1 (OPF level, 0 new TDS)

Scripts: `dec066_abl_analysis.py` (raw predictions, 5 designs × 28 events), `dec066_abl_tables.py` (T4, T4b, T4b2, T4c, T4d), `dec066_abl_figures.py` (F4 preliminary). Data: `IEEE39_DEC066_ablation_raw.json`, `IEEE39_DEC066_T4*.csv`, `IEEE39_DEC066_F4_data.csv`, `figures_main/DEC066_F4_prelim.{pdf,png}`. Designs B, C, E finished normally (FEASIBLE_PREDICTED; state files `backups/DEC066_state/abl_{B,C,E}_OC1.json`); none was re-run. A and D are the historical states, unmodified.

## A0 check
| Item | Result |
|---|---|
| B, C, E state files | present, status FEASIBLE_PREDICTED, `init_ok` true, 12 design events, same cfg (K_max 8, N_it 25, ftol 1e-6, k0 4), seed = DEC-055 M3 |
| `iterations` field | 0 in all five designs, including historical A and D: not informative, not reported as evidence of convergence |
| KKT residual | A 0.062, B **0.598**, C 0.060, D 0.058, E 0.062. B is not a converged point; none is called optimal |
| Initialisation | A optimised with M0 as extra seed; B, C, D, E from M3. Common-initialisation control not yet run (open) |

## T4 (design level; "external" = dense + grid excursion, no ε, same 12 events for all)
| | Design | J | ΣΔP vs case (MW) | vs A (MW) | KKT | ext. min margin (pu) | grid-only view (pu) |
|---|---|---|---|---|---|---|---|
| A | M3 | 1.6815 | 55.70 | 0 | 0.062 | **−0.0150** (SG31, b8 S3) | +0.0020 |
| B | +dense | 1.7055 | 57.16 | 2.25 | 0.598 | +0.0020 | +0.0020 |
| C | +dense+ε_OS | 1.7073 | 57.23 | 2.41 | 0.060 | +0.0024 | +0.0024 |
| D | M3+OS | 1.7592 | 61.19 | 6.83 | 0.058 | +0.0133 | +0.0133 |
| E | U_D8 only | 1.7309 | 58.82 | 3.48 | 0.062 | **−0.0041** (SG31, b8 S3) | +0.0129 |

## T4d (pairwise)
| Contrast | ΣΔP between (MW) | ΔJ | Δ ext. margin (pu) |
|---|---|---|---|
| B−A dense | 2.25 | +0.024 | +0.0171 |
| C−B ε_OS | 0.17 | +0.0018 | +0.0004 |
| D−C U_D8 | 4.44 | +0.052 | +0.0109 |
| E−A U_D8 alone | 3.48 | +0.049 | +0.0109 |
| D−E dense+ε_OS under U_D8 | 3.35 | +0.028 | +0.0174 |

## What explains the differences (design level, predictor-based)
1. **The dense 0–50 ms term changes the constraint, in few places**: ΔE_dense > 0 in 21 unit/event pairs, largest at SG31 (0.017 pu, b8 S3), SG33 (0.013, b23 S3), GFM32, GFM37. At the A dispatch the grid-only view says +0.002 pu at b8 S3 SG31 but the dense view says −0.015 pu: A violates its own design event once the sub-step peak is evaluated. B recovers +0.002 pu with 2.25 MW.
2. **ε_OS is negligible**: 0.17 MW and +0.0004 pu between B and C. The active set is identical (b8 S3 SG31; b23 S3 SG31, SG33, SG35, GFM36). ε_OS (3.9e-4 pu) is below the resolution of the predictor-based margins and of the SLSQP tolerance.
3. **U_D8 dominates dispatch and cost**: 3.5–4.4 MW and +0.05 J, i.e. most of the D−A difference (6.8 MW).
4. **E (band only) does not cover the dense peak**: E has +0.013 pu in the grid view but −0.004 pu in the dense view at SG31 b8 S3. So a uniform band is not equivalent to evaluating the 0–50 ms response; D−E = +0.017 pu for 3.35 MW more redispatch. This is a prediction at the design events, not an observed result.
5. Interpretation by the plan's rule G: dense term has predicted value; ε_OS predicted null; U_D8 is a reserve increase. D vs E at comparable effort (58.8 vs 61.2 MW) favours D by the predictor, not yet by simulation.

## Prediction register for the candidate TDS (written before any TDS; T4c)
Margins are Pmax margins of delivered power (pu), min over units. Classes from the predictor (U_D8 band) over 0–10 s; the 10–195 s window is not used for classification because the predictor diverges there (SG35, F3).
| Event | A | B | C | D | E | Informativeness |
|---|---|---|---|---|---|---|
| b8 S3 (design, active) | −0.015 | +0.002 | +0.002 | +0.013 | −0.004 | **1**: crosses 0 between variants; direct test of dense term and of E vs D |
| b23 S3 (design, active) | 0.000 | +0.002 | +0.002 | +0.013 | +0.002 | 3: small differences |
| b21 S3 (50 ms) | −0.011 | −0.008 | −0.007 | +0.004 | −0.010 | **1**: A UNSAFE_BY_VALID_PREDICTOR; others INDET (in band) |
| b15 S3 (50 ms) | −0.007 | −0.003 | −0.003 | +0.008 | −0.005 | 2: all INDET |
| b31 S2 (jump) | −0.115 | −0.098 | −0.097 | −0.086 | −0.104 | 5: UNSAFE_BY_JUMP in all; negative case, D least bad |
| b20 S3 (jump) | −0.064 | −0.061 | −0.060 | −0.049 | −0.063 | 5: UNSAFE_BY_JUMP in all |
| b21 S2, b18 S2/S3, b26, b15 S2 | ≥ +0.06 | | | | | **low**: PREDICTED_SAFE in all variants (expected null) |
| b39 S2/S3 | 0–10 s margins +0.10…+0.20 in all; 10–195 s window predictor-diverged | | | | | low for 0–10 s; the historical violation at 3.4 s was an M0 dispatch effect |
| b31 S3 | PREDICTOR_INVALID in all variants | | | | | cannot be used as evidence |
Consequence: the four events proposed initially (b21 S2, b39 S2, b39 S3, b31 S2) are mostly non-discriminating among A–E (predicted SAFE with margin ≥ 0.09 pu, or inadmissible at the jump for all). I propose replacing them as follows.

## Proposed E1 (≤ 20 TDS), not executed
Controller B5′ (same parameters), OC1, rule M3V-1, same solver settings as DEC-062 (dt 2⁻⁸, local dt/16, tol 1e-4, reset_tiny 0), ledger `IEEE39_DEC066_tds_ledger.csv`.
1. b8 S3 × A, B, C, D, E (5): dense term and U_D8-vs-dense contrast; predicted ordering of the SG31 margin A < E < B ≈ C < D.
2. b21 S3 × A, B, D, E (4; C omitted as it coincides with B within 0.0004 pu): crossing of the INDET band.
3. b15 S3 × A, D (2): second band-crossing event, on a bus used only in DEC-054.
4. b23 S3 × A, D (2): second design-active event.
5. b31 S2 × A, D (2): impossibility case (UNSAFE_BY_JUMP predicted for both; keeps the negative result).
6. b21 S2 × A, D (2): predicted-safe control (expected null; a violation would refute the predictor).
Total 17. Three left for E2 timing refinement of the b8 S3 peak. E3 (new buses b18) and E4 stay unplanned until E1 is read; b18 S2/S3 are predicted safe for every variant, so they only add value as an external-validity check of M3-family dispatches, not of OS.
Reuse: no historical run has the same (z, event, controller) for A–E, so no reuse is expected; DEC-062 M0/rev3 runs remain external references only (rev3 ≠ D).

## Caveats
- All numbers above are predictor values; no observed benefit of OS is shown yet.
- Design events are in-sample for every variant; b8 S3 and b23 S3 are chosen because they are the active constraints, and this selection is disclosed. They test the predictor-consistent claim (the dense term removes a sub-step violation), not generalisation.
- ε_OS and U_D8 are empirical and numerical; the J difference is a displacement/pattern cost, not an economic one. Dispatch differences are 2–7 MW out of ~57 MW: the observed differences may be within numerical noise; the TDS must show that.
- Common-initialisation control (B.3 of the plan) and a same-budget control are open.

## Backup gate (blocks E1 until you decide)
`STOP_BACKUP_NOT_VERIFIED` is still in force. To run E1 without editing the historical `BACKUP_BLOCKED` verdict, the plan requires a procedural exception with a physical/mounted copy of the critical raw results and a risk record approved by the investigator. Draft risk record: (i) only same-disk copies exist; (ii) a disk or OneDrive failure would lose the 112 historical raw run directories and the new ones; (iii) mitigation: copy `backups/DEC059_runs`, `DEC066_state` and the new run directories to a second location at the end of each batch with hashes, and write new runs only to new directories (exclusive writes). **No TDS has been launched.** I need your explicit approval of this record (and, if available, a destination path on another disk) before E1.
