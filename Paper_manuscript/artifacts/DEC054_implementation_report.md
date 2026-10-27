# DEC-054 — Implementation report (policy M3 and comparators M0–M2)

Branch `review/dec054-prospective-preventive-dispatch`; start commit `b0dfb6d14782e5d11811fb748f43fc37e3e8f117`. **Gate: `STOP_BACKUP_NOT_VERIFIED` (independent backup not verified). TDS ledger: header only, 0/48. No ANDES stepping, no optimisation on the historical plant, no plant adapter instantiated.** The methodology is **not validated**: there are no prospective tests.

## 1. What was implemented (`Paper_manuscript/src/`, new files only)
| Module | Content | Executed/tested |
|---|---|---|
| `dec054_common.py` | constants (`EVENT_T=5`, `T_END=200`, **`T_POST=195`**), proposed parameters (not sealed), unit/PV sets (9+10 variables), status vocabularies, backup gate, **append-only TDS ledger** with 8/16/24/48 budgets | tests |
| `dec054_rdcinit.py` | `I(z)`: `pn,qn,pset0,qset0,gp0,gq0,gref_p,gref_q,k_ip,d_p,d_q` (arithmetic identical to `run_e8_ieee39.capability_factors`, verified with `atol=0`) | tests |
| `dec054_jump.py` | damped Newton for `g(x⁻,y⁺,u⁻,z,d)=0`, branch regularity (`σ_min`), refusal near singularity, `dy/dd` | tests |
| `dec054_predictor.py` | post-event affine predictor `δξ̇=A⁺δξ+f⁺`, `δξ(0⁺)=0`, `expm_multiply` on `[[A,f],[0,0]]`, grids + refinement + sampling-error estimate, validity monitor | tests vs `solve_ivp` |
| `dec054_calib.py` | `ε = max(floor, κ·max positive residual)`, LOBO diagnostic, conformal-rank check, hash-based bus partition | tests |
| `dec054_opf.py` | `Problem` (non-degenerate `J`, base AC constraints incl. Slack and 39 voltages, M1/M2/M3 margins, dynamic cuts), SLSQP, KKT (NNLS), **Algorithm 1** with six exit states, `solve_static` (M0, M1) | tests (synthetic plant) |
| `dec054_metrics.py` | violations (P/Q/S, 39 voltages), jump vs excursion split, sharing vs executed `pn(z)` | tests |
| `dec054_runner.py` | `write_frozen` (exclusive), `verify_frozen` (code hashes), gated prospective runner, `execute_tds` (B2, 200 s, step at 5 s) | gate/frozen tests; **`execute_tds` never run** |
| `dec054_plant.py` | ANDES adapter (`hook_for_z`, `evaluate`, `jump`, `affine`, `excursion`) reusing validated helpers; refuses instantiation before backup | refusal tested; **UNTESTED_ON_PLANT** |
| `dec054_synth.py`, `dec054_synth_demo.py` | synthetic plant and pipeline demo (`IEEE39_DEC054_synthetic_pipeline_demo.csv`, labelled SYNTHETIC_NOT_EVIDENCE) | executed |
| `test_dec054_core.py` | 36 unit/integration tests (see `IEEE39_DEC054_unit_test_report.json`) | executed |
| `dec054_preservation.py` | P0 (previous step) | executed |

## 2. Test content (synthetic only)
Time convention (195 s); partition reproduces DESIGN `{8,23,28,25}`, TUNE `{7,20,16,24}`, TEST `{3,29,15,12,27,26}`, 14 eligible buses, no overlap with 4/18/21 or 31/39; `I(z)` (`pn=P⁻`, `d_q` fixed, `d_p` and `k_ip` move with the dispatch, executor failure modes, equality with `run_e8_ieee39.capability_factors`); v1 sharing penalty is identically zero while the v2 pattern term is not; Newton jump and singular-branch refusal; predictor equals the ODE solution and has `D(0)=0`; `ε` rule and non-finite conformal rank for `n=8, α=0.1`; M0 violates design margins on the synthetic plant, M2 satisfies jump margins, M3 covers the excursion that M2 misses, M1 static reserve, infeasible demand never reported as success, plant exceptions → `SOLVER_FAILED`, stagnation state, cut deduplication; correct vs stale `I(z)` changes the predicted excursion; jump/excursion metrics; ledger refusal while blocked, budgets 8/16/24/48, failures keep their budget, duplicate run ids refused, append-only; frozen file hash mismatch detection; historical files unchanged against `04e082b`.

## 3. Synthetic pipeline demo (NOT evidence)
M0 violates 4 jump-only and 6 jump+excursion design margins; M1 (ρ=0.02) 1 and 2; M2 0 and 2; M3 0 and 0; costs `J` increase M0 < M1 < M2 < M3 (2.7e-18, 2.3e-4, 2.5e-4, 2.9e-4). This only shows the bookkeeping works on a toy plant built to behave that way; **it says nothing about IEEE-39**.

## 4. Why nothing else was run
Per the authorisation, new TDS and optimisations on the historical plant are allowed only after `BACKUP_VERIFIED`. The only available disk is the OS NVMe; no external destination was provided. The same-disk copy and bundle (P0) are not an independent backup.

## 5. What is needed to proceed
1. An independent destination (other physical drive or authorised remote); copy `dec054_preservation_local`, verify against `MANIFEST_SHA256.json`, restore ≥2 large series and the bundle; issue a new manifest revision with `BACKUP_VERIFIED`.
2. Then S3 (P2 technical checks: callback/event order, `I(z)` vs executor state, GFM residuals), S4 predictor audit (≤8 TDS), S5 development (≤16), S6 freeze + commit, S7 prospective cohort (≤24), S8 analysis (`IEEE39_DEC054_reproduction_commands.md`).

## 6. Not claimed
No validation of M3, no superiority over M0–M2, no predictor accuracy on the plant, no `ε` values for the plant, no dispatches for IEEE-39 (none were computed), no figure or table of plant results (none exists). Positive/negative results: none yet; limitations: all items in `IEEE39_DEC054_design_fixes_R3.md` "Still open".
