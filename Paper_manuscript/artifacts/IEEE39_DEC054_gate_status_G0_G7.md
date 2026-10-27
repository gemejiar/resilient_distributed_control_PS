# DEC-054 — Gate status G0–G7 (campaign S3–S8)

Branch `review/dec054-prospective-preventive-dispatch`. The authorisation names `6ba6306…` as reference commit; the remote HEAD was `f1baf54…` (descendant that already contains the integration corrections); work continues from the remote HEAD. The attached protocol file was not available; the instructions of the message were used as operative authorisation.
**Campaign state: STOPPED AT G0. TDS ledger: header only (0/48). No ANDES import, PF, TDS or optimisation on IEEE-39 was run. Historical files, plant, B2, PSS, limits, cases, `main.tex` and `main` untouched (338 original-tree files re-hashed: 0 changed).**

| Gate | Status | Evidence |
|---|---|---|
| **G0 — independent preservation** | **BLOCKED (`STOP_BACKUP_NOT_VERIFIED`)** | The machine has a single physical disk (NVMe `C:`; recovery/support partitions only); no external drive and no remote destination expressly authorised. The project-folder copy (`Paper_manuscript/backups/DEC054_P0_preservation`) is verified but is on the same disk/synchronised tree, so it cannot satisfy G0. |
| G0 gate logic | **PASS (code)** | `backup_gate()` no longer reads a boolean from the P0 manifests: it validates a **new** evidence file `IEEE39_DEC054_independent_backup_verification.json` against the baseline manifest and **recomputes on every call** the SHA-256 of every ignored local file and of the Git bundle at the destination, requires a destination on a different device (not overlapping the source), an explicit authorisation string, ≥2 NPZ restore tests consistent with the baseline hashes and a successful bundle verify/clone. P0 manifests are not consulted and not modified. |
| G0 procedure | ready, not executed | `dec054_independent_backup.py <destination_root> <kind> "<authorisation>"` copies the preservation to the destination (never overwriting), re-hashes from the destination, restores NPZ and the bundle, and writes the evidence file exclusively. Refuses same-device destinations. |
| **G1 — software integration** | **PASS (synthetic)** | items 1–7 below |
| G2 real adapter audit | NOT STARTED (blocked by G0) | — |
| G3 predictor audit (≤8 TDS) | NOT STARTED | — |
| G4 OPF on IEEE-39 (≤16 TDS) | NOT STARTED | — |
| G5 freeze | NOT STARTED | — |
| G6 prospective cohort (≤24 TDS) | NOT STARTED | — |
| G7 final comparison | NOT STARTED | — |

## G1 items
1. `AndesPlant.z_ref` from the historical case, 19 variables in exact order (`z_ref_from_system`, `variable_spec`): implemented, mock-tested (previous round).
2. PFlow/TDS.init/residual verification, never `ok=True` on invalid init (`check_initialisation`): implemented, mock-tested (previous round).
3. `I(z)` vs executor state per dispatch (`evaluate` fails on `>1e-9` mismatch): implemented; verified on real data only after G0.
4. Cache invalidation with dynamic cuts (`_state_sig`, `add_dynamic_cut`): implemented, regression-tested (old key fails 2 of 4).
5. One frozen dispatch per method: `validate_dispatches`, `assert_single_dispatch`, `write_frozen`/`verify_frozen`: implemented and tested.
6. Exclusive persistent run store (`dec054_store.py`, runner saves before ledger completion, failures keep evidence): implemented and tested.
7. Synthetic battery: **82 tests, 0 failures** (`IEEE39_DEC054_unit_test_report_R5.json`; core 36 + integration 31 + gate 15; the gate tests cover missing evidence, old booleans, every tamper type, same-device refusal with the real device check, re-validation after bit rot, malformed evidence, ledger coupling, creation script incl. refusal to overwrite, corrupted-source refusal and wrong bundle head).

## What the investigator must provide to continue
An independent destination: another physical drive or a remote location that can be read back as a local path, plus the authorisation text. Then:
`PY dec054_independent_backup.py <destination_root> other_physical_drive "<authorisation>"` → the gate turns `BACKUP_VERIFIED` only if the recomputed hashes and restore tests are consistent; G2–G7 then run sequentially as authorised.
