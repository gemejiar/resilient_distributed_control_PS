# DEC-066 ablation: paper package (20 new TDS of 40)

Ledger `IEEE39_DEC066_tds_ledger.csv` (D66T001-D66T020; E1a 5, E1b 12, E2 3; 20 of 40, 0 failures of the numerical solver). Plans with registered predictions: `IEEE39_DEC066_E1a_plan.json`, `_E1b_plan.json`, `_E2_plan.json` (sealed and committed before each lot). Raw runs: `backups/DEC066_runs` (git-excluded). Backup: waived by the investigator; same-disk copy hash-verified; no independent backup (ops/sted/DEC066_protocol.md Addendum C).

| Item | File |
|---|---|
| T4 designs A-E (+T4b active constraints, T4b2 dense effect, T4c prediction register, T4d pairwise, design level) | `IEEE39_DEC066_T4*.csv` |
| T5 observed metrics, 20 runs | `IEEE39_DEC066_T5_observed.csv` |
| T5b predicted vs observed | `IEEE39_DEC066_T5b_pred_vs_obs.csv` |
| T6 observed contrasts | `IEEE39_DEC066_T6_contrasts.csv` |
| F4 final, F7 transients | `figures_main/DEC066_F4_final.*`, `DEC066_F7_transients.*` (F4_prelim kept) |
| LaTeX | `IEEE39_DEC066_ablation_results.tex`, `IEEE39_DEC066_ablation_tables.tex` (generated), integrated in `IEEE39_DEC066_results_draft.tex` (compiles, IEEEtran check) |

## Findings
1. Bus 8 S3 (active constraint, SG31, peak 2.2 ms): observed margin A -0.0148 (UNSAFE, 1.5 ms), E -0.0038 (violation inside band), B +0.0023, C +0.0027, D +0.0136 (SAFE). Registered predictions: -0.0150, -0.0041, +0.0020, +0.0024, +0.0133.
2. Bus 21 S3: A -0.0110, B -0.0072, E -0.0094, D +0.0041. Bus 15 S3: A -0.0068, D +0.0082. Bus 23 S3: A +0.0006, D +0.0156. Bus 21 S2 (control): both safe. Bus 31 S2: both violate (A -0.128, D -0.099): inadmissible at the jump.
3. A violated Pmax in 4/6 events; D only in bus 31 S2.
4. Attribution: dense +0.017 pu (bus 8), eps_OS +0.0004 pu (null), U_D8 +0.0109 pu (= band); U_D8 alone (E) does not remove the violation; dense under the same band (D vs E) does, for 2.4 MW more redispatch.
5. Predictor: observed - predicted +4.3e-4 pu on average, max +2.4e-3, always conservative (15 admissible cells). Step sensitivity (3 TDS): <= 1.3e-4 pu, sign and class unchanged.
6. System-wide frequency nadir and bus voltage are equal across designs (1e-5 Hz, 1e-4 pu): differences are in the sub-cycle power peak.

## Limits kept
B not converged (KKT 0.60); A initialised with M0; bus 8 and 23 are design-set events; 5 designs, not factorial; OC1 only; 20 runs; RMS not EMT; Pmax temporal tolerance unknown; violations within +-U_D8 are reported as INDETERMINATE, not safe; eps_OS null; no independent backup.

## Not run (budget left 20)
E3 new buses (b18, b26), E4 reserve, common-initialisation control, OC2/OC3, controllers other than B5'. Common-initialisation and a same-budget control remain open and are the main reviewer-facing gaps.
