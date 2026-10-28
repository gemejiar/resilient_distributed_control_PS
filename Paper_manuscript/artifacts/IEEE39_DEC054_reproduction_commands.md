# DEC-054 — Exact commands per stage (executed)

Worktree `C:\Users\gemej\dec054_wt`. `PY` = repository venv interpreter (ANDES 2.0.0, Python 3.12.10). Run from `Paper_manuscript/src`, with single-thread BLAS (`OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, `MKL_NUM_THREADS=1`); the pooled plant sets this in each worker. All outputs are created exclusively (`open(..., "x")`): re-running refuses to overwrite.

| Stage | Command | TDS |
|---|---|---|
| Preservation (P0) | `PY dec054_preservation.py` | 0 |
| Unit/integration tests | `PY -m unittest test_dec054_core test_dec054_integration test_dec054_gate test_dec054_p3a` | 0 |
| G2 adapter audit | `PY dec054_adapter_audit.py` | 0 |
| G3 predictor audit | `PY dec054_p3a_audit.py plan` → `run` → `analyze` | 8 |
| G4 offline designs | `PY dec054_g4_design.py m0`, `m1`, `m1b`, `m2`, `m3` | 0 |
| G4 verification | `PY dec054_p3b.py plan1` → `run1` → `analyze1` → `plan2` → `run2` → `analyze2` | 12 |
| G5 freeze | `PY dec054_g5_freeze.py` (commit the JSON before G6) | 0 |
| G6 cohort | `PY dec054_p3c.py` (parallel cohort, frozen dispatches only) | 24 |
| G7 analysis | `PY dec054_g7_analysis.py`; `PY dec054_a5_ablation.py`; `PY dec054_g7_figures.py`; `PY dec054_g7_claims.py` | 0 |

Raw series: `Paper_manuscript/backups/DEC054_runs/<run_id>/{series.npz,config.json,metrics.json,diag.json,status.json,hashes.json}` (Git-excluded, local only). Total TDS: 44/48.
