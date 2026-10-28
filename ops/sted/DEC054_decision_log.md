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

## DEC-054 / Integration readiness (pre-ANDES)
Date: 2026-10-27
Gate: Authorization "DEC-054 — Corrección de integración previa a ANDES" (start commit 6ba63061c3275dff6094762b20693985cf270ff0). Rule: no ANDES, no optimisation on IEEE-39 before BACKUP_VERIFIED.
Decision: Implemented z_ref from the historical case with an exact 19-variable spec; explicit PFlow/TDS.init/residual validation (never ok=True on invalid init); cache key including dynamic cuts and eps; exactly one frozen dispatch per method M0-M3; exclusive per-run evidence store (also for failures). Details in IEEE39_DEC054_integration_readiness_report.md.
Results: full synthetic battery 67 tests, 0 failures (IEEE39_DEC054_unit_test_report_R4.json). Issues fixed: unclosed ledger file handle; four tests adapted to the new frozen schema; cache regression reproduced with the old key (2 failures) and fixed.
Blockers: independent backup not verified (STOP_BACKUP_NOT_VERIFIED); 0/48 TDS; adapter UNTESTED_ON_PLANT.
Responsible: Integrator
Status: BLOCKED_AT_BACKUP_GATE (integration corrections and tests delivered)
Next action: Investigator decision on the backup gate; then P2 technical checks.

## DEC-054 / Campaign S3-S8 — stopped at G0
Date: 2026-10-27
Gate: Authorization "DEC-054 — Auditoría ANDES y experimentación prospectiva" (reference commit 6ba6306 named; work continued from remote HEAD f1baf54, its descendant). Attached protocol unavailable; message instructions used.
Decision: G0 cannot pass: single physical disk, no external drive and no expressly authorised remote destination. Campaign stopped at G0 with 0/48 TDS and no ANDES/PF/TDS/optimisation on IEEE-39. G0 gate logic corrected: backup_gate() now validates NEW independent evidence (recomputed SHA-256 of all files and bundle at a destination on another device, authorisation, NPZ/bundle restore tests); P0 manifests untouched and no longer consulted. Added dec054_independent_backup.py (not run), dec054_testkit.py, test_dec054_gate.py; adapted existing tests. Synthetic battery 82 tests, 0 failures (IEEE39_DEC054_unit_test_report_R5.json).
Blockers: independent backup destination (investigator).
Responsible: Integrator
Status: BLOCKED_AT_G0
Next action: provide destination + authorisation; run dec054_independent_backup.py; then G2-G7 as authorised.

## DEC-054 / Campaign G0 waiver and G2–G7 execution
Date: 2026-10-27
Gate: `/goal` instruction of the investigator: proceed to the end ignoring the missing independent backup (recorded as BACKUP_WAIVED_NOT_INDEPENDENT; gate logic recomputes hashes on every call).
Decision: G2 adapter audit PASS; G3 predictor audit PASS (8 TDS); G4 offline designs M0–M3 and dynamic verification of M3 at DESIGN/TUNE events (12 TDS). Design corrections made after DESIGN/TUNE evidence only: p scale 0.5 pu and capability margin 0.01 pu (M0 pilot cost scale); pre-event voltage margin 0.005 pu for all 39 buses and all methods (round-1 overshoot to 1.0522 pu); predictor guard against unstable linearisations; process pool with single BLAS thread. Discarded attempts are kept in DEC054_g4_state. Design frozen (14007fb) before G6; G6 ran 24 TDS (6 frozen scenarios × M0–M3), no failures, no repeats, no changes after observing results.
Results: observed P violations in the prospective cohort: M0 7 pairs (6/6 scenarios), M1 0, M2 1 pair (0.0096 pu), M3 0; no Q/S/V violations in any method. M3 min Pmax margin 0.0103 pu. M3 J=1.478 (43 MW redispatch) vs M1 J=3.32 (153 MW): same observed compliance with 55 % lower J; equal-cost contrast NOT_MATCHED. Status NUMERICALLY_SUPPORTED in this cohort only (6 clusters, one amplitude, no inference). TDS used 44/48.
Blockers: none for the campaign; open caveats: no independent backup, thin M3 margin, empirical epsilon, Q/S/V not modelled by the predictor, frequency metrics use the 39-bus mean (not COI), SLSQP gives feasible points not KKT-certified optima.
Responsible: Integrator
Status: COMPLETED_NUMERICALLY_SUPPORTED (no certification claims)
Next action: investigator review; any extension (more buses/amplitudes, independent backup) needs new authorisation.
