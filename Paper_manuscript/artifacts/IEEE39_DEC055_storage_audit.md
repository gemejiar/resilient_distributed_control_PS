# DEC-055 — Storage audit (nothing deleted)

Measured on 2026-10-28 with `du`/`find`. `R` = `C:\onedrive\OneDrive - Universidad del Valle\05_Univalle_Investigacion\02_Publicaciones\En_Preparacion\Proyectos_Latex\Resilient_distributed_control_PS`.

| Path | Size | Content | Dependencies | Candidate? | Justification |
|---|---|---|---|---|---|
| `R\Paper_manuscript\backups\DEC054_P0_preservation\` | 1.2 GB (files 979 MB + bundle 163 MB) | Same-disk preservation copy of the 36 ignored NPZ series and the Git bundle (DEC-054 P0) | `backup_gate()` re-hashes it on every call (DEC-054 waiver); referenced by `IEEE39_DEC054_local_copy_manifest.json` | **Yes, after an independent backup exists** | Exact duplicate of `R\Paper_manuscript\artifacts\*.npz` and of `C:\Users\gemej\dec054_preservation_local\` on the same disk. It gives no protection against disk loss. Deleting it invalidates the DEC-054 waiver gate (code change needed). |
| `C:\Users\gemej\dec054_preservation_local\` | 1.14 GB (files 979 MB + bundle 164 MB) | Second same-disk copy (P0 preservation source) | `IEEE39_DEC054_backup_manifest.json` | **Yes, after an independent backup exists** | Third copy of the same bytes on the same disk. |
| `R\Paper_manuscript\artifacts\*.npz` (36 files) | 1.02 GB | Canonical raw series of E0–E16, B3, E9, DEC-050…053 (Git-ignored) | Hashes in `IEEE39_DEC053_inventory.csv` and the DEC-054 baseline manifest; figure scripts of every stage | **No** | Canonical evidence, local only (no independent copy). Recommended: archive externally (e.g. Zenodo or an institutional drive). |
| `R\Paper_manuscript\artifacts\IEEE39_DEC050_B_B2QV1_series.npz` | 139 MB | B2_QV1 negative result (DEC-050 B) | DEC-050 B summary, F22 claim | Low priority | Largest single file; supports a negative result only. Keep unless archived. |
| `R\Paper_manuscript\backups\DEC054_runs\` | 1.2 GB | 44 DEC-054 runs (series, config, metrics, hashes) | DEC-054 analyses, figures, claims; DEC-055 L1 regression reference (`P3B2_b7P_M3`) | **No** | Canonical DEC-054 evidence. |
| `R\Paper_manuscript\backups\DEC055_runs\` | 149 MB | 5 DEC-055 L1 runs | `IEEE39_DEC055_L1_results.json` | **No** | Canonical L1 evidence. |
| `R\Paper_manuscript\backups\DEC054_g4_state\`, `DEC055_state\` | 97 kB, ~0.2 MB | Design and state files (incl. discarded attempts) | G4/G0 manifests (hashes) | No | Small; provenance of designs. |
| `C:\Users\gemej\dec054_wt\`, `C:\Users\gemej\dec055_wt\` | 95 MB each | Git worktrees of the review branches | Pushed to `rdc` (`3c58634`, `cbb70cc`) | Yes, once the branches are reviewed (`git worktree remove`) | Tracked content is on `rdc`; untracked outputs were written to the original tree. |
| `C:\Users\gemej\*.py`, `*.log` (37 files) | 7.6 MB | DEC-054 probe, patch and log scratch files | None (not referenced by any manifest) | **Yes** | Session scratch; no evidence role. |
| `C:\Users\gemej\dec055_logs\` | 7.2 MB | stdout logs of the DEC-055 static stages | None (results are in the state files) | Yes | Mostly repeated ANDES `xl <= xd2` warnings. |
| `R\scratch_*.log`, `R\scratch_pred_hash.txt` | 0.2 MB | Earlier session logs in the repository root (untracked) | None | Yes | Untracked scratch. |
| `R\venv\` | 617 MB | Python environment (ANDES 2.0.0) | Every runner | No | Required. |

**Total that could be freed without loss of information:** about 2.3 GB (the two same-disk preservation copies). This is valid only after the raw series are archived on an independent medium. Until then, those copies are the only protection against accidental overwrite (not against disk loss).
