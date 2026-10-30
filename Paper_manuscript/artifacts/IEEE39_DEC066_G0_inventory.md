# DEC-066 G0: integrity audit, inventory and reproduction (read-only)

Branch `review/dec066-m3os-closure`, created from `review/dec059-scientific-reorientation` at SHA **705919bc9acfd18dd2de82bdb4b324ad12aa426e** (2026-10-30 11:47, "DEC-065: corrected OS…"). Local and `rdc` remote refs of the parent branch coincide (rdc last fetched OK before this session; a later fetch failed with "could not resolve host", transient). Tag `dec062-freeze` → 2ba22d6, untouched. Work done in the worktree `C:\Users\gemej\dec055_wt` (the primary checkout is on `review/dec053-methodology-closure` and was not modified). Raw (Git-excluded) data are read from `Paper_manuscript/backups/` of the primary checkout. **No TDS, no PF/OPF run, nothing historical written.** Tool outputs: `IEEE39_DEC066_G0_manifest.json`, `_regression.csv`, `_alignment.csv`; code `dec066_g0.py`, `dec066_g0b.py`.

## 1. Verdict

| Item | Result |
|---|---|
| Frozen files unmodified | **PASS**: 373 tracked files (artifacts DEC05x/06x, src dec05x/dec06x/run_*/e8*/e9*/test_*, ops/sted, cases, `main.tex`, references, `main_revision_DEC065.tex`) with SHA-256; 0 differ from HEAD |
| Original `main.tex` | blob `afbaf8616444d8d416d051fe5f566af6527e8f3575` at HEAD and at 0db386b (identical) |
| ANDES | 2.0.0, package aggregate SHA-256 in manifest (not modified); Python 3.12.10, NumPy 2.5.4, SciPy 1.18.1, kvxopt 1.3.3.3, Windows 11, 8 cores, no random numbers (deterministic; SLSQP) |
| Raw runs | 112 run directories in `DEC059_runs`, **672 files, 0 hash mismatches** against their `hashes.json` |
| 36 + 18 equivalence | plan ids (R5A/R5B) = 54 = run directories on disk; none missing, none extra |
| Regression of metrics from raw series | `dec062_test.main(write=False)` recomputed from the raw series vs `IEEE39_DEC062_TEST_results.json`: **3 843 numeric/string leaves, 0 mismatches**; 54 rows; classes SAFE 41, UNSAFE 12, INDETERMINATE 1 (cohort A: 26/9/1; cohort B: 15/3/0) |
| Historical replay | **HISTORICAL_REPLAY_NOT_EXECUTED** (no new TDS; see backup) |
| Unit tests | 119 historical tests run without touching sources: core 36 (1 fail, explained §5), gate 20, integration 31, p3a 4, dec055 22 pass; dec059 6 pass |
| Independent backup (DEC-054 gate) | **BLOCKED (inherited)**: see §4 |
| **G0** | **PASS for read-only work; BLOCKER for any new TDS until §4 is resolved by the investigator** |

## 2. Event/sample alignment (answer to the dist_fn question)
Across all 54 DEC-062 runs: the step before the event is Δt/16 = 2.44e-4 s (the local refinement starts at t_e − Δt = 4.99609375 s); last pre-event sample **4.999755859375**; the event is applied inside the callback before the step ending at 5.0, so **the stored sample t = 5.0 is the first post-jump point, one Δt/16 step (2.44e-4 s) after the pre-event sample**, and it is *not* the step starting at 4.99609375. The first change of the commanded references appears at **5.000244 s**, i.e. the controller reacts to post-jump measurements, which is exactly H-C at the stored jump sample (this was already fixed in `dec055_common.jump_vs_first_sample`, D9).
Three objects must stay distinct: (i) the theoretical algebraic jump (x frozen, PF at t_e⁺): `jump_pmax_margin_min` of the prediction files; (ii) the first numerical step; (iii) the first stored point. `IEEE39_DEC066_G0_alignment.csv` (36 cells): the stored first-sample Pmax margin minus the predicted jump margin ranges **−2.80e-3 … +4.87e-3 pu** (mean +5.2e-4), inside U_D8 = 0.0109 pu but **larger than ε_OS = 3.88e-4**; the first-step response must therefore not be double counted in G3/G4.

## 3. Flow map of M3+OS (real code)
```
scenario sc=(bus,kind=P,amp[pu, 100 MVA]; S1 = 0.29282, S2 = 0.58564, S3 = 0.87846) and z = (p0[9], v0[10]) pu   (slack SG39 balances)
 -> dec054_plant.AndesPlant._make(z): hook_for_z sets p0/v0 on the PV generators, ANDES PFlow + TDS.init, check_initialisation (residual)   [evaluate(z): P,Q,V,S]
 -> jump(z,sc): load step d+, algebraic re-solve with x(t_e)=x(t_e-) and u frozen -> dP_jump_i, Q, S, V at t_e+            (T-A, exact algebraic)
 -> affine(z,sc): linearisation (A, f, C) at the post-jump point, references frozen (NO secondary controller in the predictor)
 -> excursion(z,sc) [dec054_predictor]: propagate on [0,1] Δt=2^-8 (trap), [1,10] 0.05, [10,195] 0.5 (exact exponential); E_up/E_dn per unit, parabolic refinement, sampling-error check
 -> dec059_os.os_excursion (M3+OS): E = max(E_grid(0-195 s), E_dense(0-50 ms, H_OS)); margins M+ = Pmax - P- - dP - E - eps_J - eps_E ; eps_E includes eps_OS(3.88e-4, up; calibration set 18 cells) + U_D8 (0.0109)
 -> dec054_opf.algorithm1 (SLSQP over z in R^19, J = displacement cost scale p=0.5 pu + pattern cost; working-set cuts by most violated (event,unit,side)) -> z_design (FEASIBLE_PREDICTED / LOCAL_OPTIMUM_FOUND / ...)
 -> dec059_pred.predict(oc,m,set): CLASSIFIER: jump margins + DENSE 50 ms predictor for P; Q/S/V only at the jump (rule M3V-1, U_D8 band)       <- the 195 s excursion is NOT used here
 -> dec059_tds.execute -> run_b3_ieee39.run(e8.configure): trapezoid Δt=2^-8, local Δt/16 on [t_e-Δt, t_e+0.5], tol 1e-4, reset_tiny=0, event t_e=5 s, controller active from t_e
 -> dec059_metrics (m50 = min Pmax margin over [t_e, t_e+50 ms]; m_after_50ms; Q/S/V; f_COI; V_bus) -> classes (U_D8 band) -> dec062_test / dec063 / dec064 / dec065 analyses and figures
```
Units: P, Q, S in pu on the 100 MVA system base (×100 = MW/MVAr); V in pu; time in s with t_e = 5 s; margin = limit − value (>0 safe).

## 4. Backup state and its consequence
`IEEE39_DEC054_backup_manifest.json`: `BACKUP_BLOCKED`, `SAME_PHYSICAL_DISK_COPY` (NVMe C:), 89 files, hashes match; `preservation_test`: `independent_backup_verified: False`, gate `STOP_BACKUP_NOT_VERIFIED`. Since then no independent destination has been recorded, and the 3.2 GB of `DEC059_runs` (including the 54 DEC-062 runs, 1.80 GB) were created after that manifest, with only per-run `hashes.json` for integrity. The primary checkout lives under a OneDrive path, which is not evidence of a verified second copy (DEC-054 §1.2). **Decision needed:** provide an independent destination (external drive/remote) so that the backup can be completed and verified, or accept explicitly in the protocol that G2+ proceeds with `BACKUP_BLOCKED`. Until then no new TDS is run.

## 5. Unit-test finding
`test_dec054_core.TestProtectedFiles.test_historical_artifacts_untouched_vs_base` fails because the diff against the DEC-054 base lists files **added or appended after DEC-054 by design** (two DEC-055 OC2/OC3 case workbooks, `ops/sted/decision_log.md`, `ops/sted/traceability_matrix.csv`, one more csv). It is a scope limit of that test, not a regression: the content of those files is covered by the manifest above. Not edited.

## 6. Reusable code, missing data, modifications needed
**Reusable without change** (wrap, do not mutate): `dec054_opf` (Problem, solve_nlp, algorithm1, kkt_residual), `dec054_predictor` (propagate, excursion, monitor), `dec054_plant.AndesPlant` (evaluate, jump, affine, excursion), `dec054_pool.PooledPlant`, `dec055_oc` (make_plant, OC cases), `dec055_common` (classifiers, `jump_vs_first_sample`, `f_coi_hz`, `rocof_window`), `dec059_os` (os_excursion, make_os_plant, calibration), `dec059_pred`, `dec059_tds`/`dec057_tds.execute` (ledger and runner), `dec059_eq`, `dec059_metrics`, `dec062_test`, `dec065_os`, `run_b3_ieee39.run`, `run_e8_ieee39.configure`.
**Findings that shape G3–G6:**
1. The false SAFE of DEC-062 (OC1 M0 b39 S2/S3) come from the **classifier** (`dec059_pred`), which uses the dense 50 ms predictor for P; the optimiser's `os_excursion` already takes the maximum over 0–195 s. The first G3 test is to apply the existing 195 s excursion to those two cells (no TDS).
2. Beyond 10 s the excursion grid has a 0.5 s step with parabolic refinement: it is not a certified continuous maximum (G3 must report the sampling error component).
3. The predictor freezes the references (no secondary controller): the controller dependence after the jump is outside it (CONTROL_AWARE item).
4. Q/S/V are evaluated only at the jump in the classifier and are not optimiser constraints beyond static margins (`SCOPE_P_ONLY` is the current reality).
5. Rev3 status in `m3os_rev3_OC1.json`: `FEASIBLE_PREDICTED`, `iterations: 0`, KKT residual 3.39: **not** a stationary point (G5 must not call it locally optimal).
**Redispatch reconciliation (resolved from stored dispatches; no new data):** rev3 Σ|ΔP| over the 9 decision units is **99.353 MW vs the original case dispatch** (`redispatch_MW_abs_sum_vs_case`, state file) and **101.068 MW vs the M0 AC-OPF dispatch** (recomputed from `dispatch_z`); vs M3OS 38.98 MW, vs the cut dispatch 23.17 MW. Both numbers are right; their baselines differ (base case vs M0). The manuscript must state the baseline.
**Missing data / decisions for later gates:**
- G1: unit limit provenance (`e7.static_limits`, case workbooks) and whether REGF1 (grid-forming) models an internal current limiter (state `PIplim_y` exists) — to be audited, not assumed.
- G2: dt = 2⁻⁹…2⁻¹¹ runs and integrator contrasts do not exist as stored series (new TDS or new ledger needed); the earlier D8 local refinement (DEC-057) is the only precedent.
- G8: the 19 load buses of the case are 3, 4, 7, 8, 12, 15, 16, 18, 20, 21, 23, 24, 25, 26, 27, 28, 29, 31, 39. Buses already used: DESIGN 8, 23, 28, 25; TUNE 7, 20, 16, 24; TEST 21, 31, 39; OC2 validation 3, 4, 12 (and DEC-054 data). **Only 15, 18, 26, 27, 29 were never used**, so a blind cohort with ≥ 100 independent SAFE predictions is not available from new buses alone; effective N will be limited by spatial dependence. New operating conditions or severities are needed to widen it.
- TDS budget: the historical cap (112/120) is closed; the plan defines a new ledger but no cap for G2, G6, G7, G8: to be proposed and authorised.
**Modifications that will be required (new modules only):** `dec066_predictor.py` (windowed full-horizon predictor), `dec066_uncertainty.py`, `dec066_opf.py`, `dec066_ablation.py`, `dec066_tds.py/metrics.py/figures.py`; no edits to `dec054_*`, `dec059_*`, `dec062_*`.

## 7. Items for REVISIÓN HUMANA 0
1. Independent backup destination, or explicit acceptance of `BACKUP_BLOCKED` for G2+.
2. TDS budget/cap and ledger rules for DEC-066.
3. Confirmation that G1 proceeds on `SCOPE_P_ONLY` unless predictors for Q/S/V are built.
4. Policy for the shortage of unseen buses in G8 (extra operating conditions vs reduced statistical claim).
