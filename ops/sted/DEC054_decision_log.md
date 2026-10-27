# DEC-054 decision log (new file; earlier logs are not rewritten)

## DEC-054 / P0
Date: 2026-10-27
Gate: Authorization "DEC-054 — Preservación inmutable, nueva política preventiva SG–GFM y validación prospectiva" (full protocol saved in ops/sted/DEC054_protocol.md). Branch review/dec054-prospective-preventive-dispatch, git worktree isolated outside the original tree, created from 04e082b26054bf046bd5421ceb275b582a0547a5. The first two authorisation messages arrived without the protocol; execution started only after the full text was supplied.
Decision: Phase P0 executed (Git snapshot, protected-file baseline, bundle, same-disk copy of all 80 ignored local files with per-file SHA-256, restore test). No independent backup destination exists (single NVMe disk C:, no external drive or authorised remote). Per protocol: GATE 0 = STOP_BACKUP_NOT_VERIFIED; BACKUP_BLOCKED. **New TDS: 0 (ledger 0/48).** No policy development beyond this gate, no simulation, no changes to protected files.
Results: DEC-053 big-series hashes: 0 mismatches of 21; bundle verifies (rc 0) and clones with DEC-053 head = 04e082b and the six local-main commits present; same-disk copy hashes match source (all files); two largest series + one more restored and read with numpy; main local/remote divergence documented in IEEE39_DEC054_git_divergence.md (local main 6 ahead of remote main, unchanged).
Blockers: external backup destination required (see backup_manifest "reason" and the user manual in the report).
Responsible: Integrator
Status: BLOCKED (STOP_BACKUP_NOT_VERIFIED)
Next action: Investigator provides an independent destination (other physical drive or authorised remote) or explicit authorisation of another location; then re-run dec054_preservation.py logic against it, verify, and only then P1/P2/P3.

## DEC-054 / Implementation (pre-backup)
Date: 2026-10-27
Gate: Authorization "DEC-054 — implementar y validar la nueva política preventiva" (start commit b0dfb6d14782e5d11811fb748f43fc37e3e8f117). Rule in force: implement and run only synthetic isolated unit tests before BACKUP_VERIFIED; no TDS, no optimisation on the historical plant.
Decision: Implemented modules dec054_{common,rdcinit,jump,predictor,calib,opf,metrics,runner,plant,synth,synth_demo}.py and test_dec054_core.py (36 synthetic tests, all passing, see IEEE39_DEC054_unit_test_report.json). Corrections applied before execution (IEEE39_DEC054_design_fixes_R3.md): post-event horizon 195 s (event at 5 s, run to 200 s); signed jump on the lower margin; per-unit eps; I(z) arithmetic verified identical to run_e8_ieee39.capability_factors; non-degenerate objective; six algorithm exit states; gated ledger and frozen-design runner. The ANDES adapter is UNTESTED_ON_PLANT and refuses instantiation before BACKUP_VERIFIED.
Results: no plant results exist (0/48 TDS). Synthetic demo (not evidence) shows the M0-M3 bookkeeping only.
Blockers: no independent backup destination (STOP_BACKUP_NOT_VERIFIED); P2 technical checks, predictor audit, development, freeze and prospective cohort not started.
Responsible: Integrator
Status: BLOCKED_AT_BACKUP_GATE (code and synthetic tests delivered)
Next action: Investigator provides the independent backup destination; then S3-S8 in IEEE39_DEC054_reproduction_commands.md.
