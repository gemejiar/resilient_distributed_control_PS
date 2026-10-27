# DEC-054 — Exact commands per stage

Worktree `C:\Users\gemej\dec054_wt` (branch `review/dec054-prospective-preventive-dispatch`). `PY` = the repository venv interpreter (`<original repo>\venv\Scripts\python.exe`; ANDES 2.0.0, Python 3.12.10, NumPy/SciPy installed). All commands run from `Paper_manuscript/src`.

| Stage | Command | Status now |
|---|---|---|
| S0 Git snapshot, protected baseline, bundle, same-disk copy, restore test | `PY dec054_preservation.py` (refuses if `C:\Users\gemej\dec054_preservation_local` exists) | executed (P0, 0 TDS); **independent backup NOT verified** |
| S1 Unit/integration tests (synthetic, no ANDES stepping) | `PY -m unittest -v test_dec054_core` | executed: 36 tests |
| S1b Synthetic pipeline demo (not evidence) | `PY dec054_synth_demo.py` → `IEEE39_DEC054_synthetic_pipeline_demo.csv` | executed |
| Gate check | `PY -c "import dec054_common as c; print(c.backup_gate())"` | `verified: False` |
| S2 Independent backup (investigator) | copy `C:\Users\gemej\dec054_preservation_local` (bundle + `files/` + `MANIFEST_SHA256.json`) to the external destination; verify SHA-256 against `MANIFEST_SHA256.json`; restore ≥2 large `.npz` and the bundle; then set `status=BACKUP_VERIFIED` / `independent_backup_verified=true` in a **new** manifest revision | **pending** |
| S3 P2 technical checks (after S2) | read-only: installed ANDES `TDS` callback/event order; `AndesPlant.evaluate` consistency of `I(z)` vs executor state (`I_vs_executor_max_diff`) on the C2t reference; GFM initial residuals | blocked by S2 |
| S4 Predictor audit P3-A (≤8 TDS) | `ledger.request("P3-A", …)` then `dec054_runner.execute_tds(z, scenario)` per DESIGN scenario (script to be written after S3 with the final scenario list) | blocked |
| S5 Development P3-B (≤16 TDS) | `dec054_opf.algorithm1(AndesPlant(), "M3", DESIGN+TUNE scenarios, eps_J, eps_E)` and dynamic cuts via `Problem.dyn_cuts` | blocked |
| S6 Freeze | `dec054_runner.write_frozen(...)` → commit `IEEE39_DEC054_design_frozen.json` **before** S7 | blocked |
| S7 Prospective cohort P3-C (≤24 TDS) | `dec054_runner.run_prospective_scenario(ledger, frozen, src_dir, scenario, dry_run=False)` for each of the 6 frozen scenarios × M0–M3 | blocked |
| S8 Analysis | `dec054_metrics.violations` on the stored series; ablations M0→M2, M2→M3, with/without correct `I(z)` | blocked |

Nothing in S3–S8 has been run. TDS ledger: header only (**0/48**).
