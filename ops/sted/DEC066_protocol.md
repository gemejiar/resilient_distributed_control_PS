# DEC-066 protocol (v0.1, G0): closure of M3+OS

Authority: investigator instruction "DEC-066 M3+OS" and `PLAN_MAESTRO_DEC066_M3OS_CIERRE.md` (the plan text is the investigator's message of 2026-10-30; this file records the operative contract and the state of each gate, and is append-only). Working branch `review/dec066-m3os-closure`, created from `review/dec059-scientific-reorientation` at 705919bc9acfd18dd2de82bdb4b324ad12aa426e. Parent branch, tag `dec062-freeze`, `main` and the original `main.tex` are not modified.

## 1. Non-negotiable rules (summary of plan §0)
- Existing tree only: new modules `Paper_manuscript/src/dec066_*.py`, tests `test_dec066_*.py`, protocols `ops/sted/DEC066_*.md`, reports `Paper_manuscript/artifacts/IEEE39_DEC066_*`, figures `Paper_manuscript/figures_main/DEC066_*`. Frozen modules are wrapped, never edited.
- Historical files byte-identical (manifest `IEEE39_DEC066_G0_manifest.json`, 373 files); corrections are new implementations with a recorded difference.
- Exclusive writes; every experiment has an id, hash, controller, dispatch, solver, status and raw-data location; failed and interrupted attempts are recorded; new ledger `IEEE39_DEC066_tds_ledger.csv` (the DEC-059…065 ledger of 112/120 is not altered).
- No new TEST before freezing code, parameters, predictor, classification, scenarios, hypotheses and criteria; DEC-062 is HISTORICAL_OBSERVED and cannot serve as a blind set for DEC-066 calibration.
- Independent-backup gate of DEC-054 is respected (see §3).
- No claim that a Pmax of the case is a physical instantaneous protection, that an ANDES RMS response is EMT, or that a numerical result proves invariance. No `guaranteed`, `certified`, `global`, `all contingencies` without a verified bound.
- Commits per gate `DEC-066 Gx — …`; no push or merge without authorisation; after each gate the investigator reviews (REVISIÓN HUMANA) before the next gate.

## 2. Gate sequence (as in the plan)
G0 integrity and reproduction · G1 physical definition and scope · G2 temporal/numerical validation of peaks · G3 full-horizon predictor · G4 error budget and honest classes · G5 preventive optimisation · G6 OS ablation · G7 controller × dispatch trajectories · G8 prospective external evaluation · G9 originality, theory and paper · GF closure matrix (Level A empirical / Level B conditional certified / rejected).

## 3. G0 record (executed read-only)
- Start: SHA 705919b, clean tree on the parent branch; remotes `origin` (template), `rdc` (project).
- Integrity: 373 frozen files, 0 modified; ANDES 2.0.0 aggregate hash recorded; 112 raw run directories, 672 files, 0 mismatches; 54 DEC-062 runs = plan ids.
- Regression: DEC-062 analysis recomputed from raw series reproduces the stored results (3 843 leaves, 0 mismatches).
- Unit tests: 119 historical tests, 1 failure explained (scope limit of a DEC-054 protected-file test).
- Alignment: stored t = 5.0 is the first post-jump sample (one Δt/16 step after the last pre-event sample 4.999755859375); first reference change at 5.000244 s; first-sample margin differs from the algebraic-jump margin by −2.80e-3…+4.87e-3 pu.
- **Backup:** `BACKUP_BLOCKED` (same-disk copy only) since DEC-054; `STOP_BACKUP_NOT_VERIFIED` for TDS-producing work remains in force. G0 closes as PASS for read-only work; **no TDS (including historical replay) is authorised until the investigator provides an independent destination or accepts the blocked state explicitly in an addendum to this file.**
- Replay: HISTORICAL_REPLAY_NOT_EXECUTED.
- Findings recorded for later gates (see `IEEE39_DEC066_G0_inventory.md` §6): classifier vs optimiser predictor mismatch (the 195 s excursion is not used by the classifier), 0.5 s grid after 10 s, frozen-reference predictor, rev3 KKT residual 3.39 with 0 iterations, redispatch baselines (99.353 MW vs case; 101.068 MW vs M0), 5 unused load buses (15, 18, 26, 27, 29).

## 4. Pending decisions (REVISIÓN HUMANA 0)
1. Independent backup destination or explicit acceptance of the blocked state.
2. TDS cap and ledger rules for G2, G6, G7, G8.
3. G1 scope default `SCOPE_P_ONLY` (P decided preventively; Q, S, V monitored).
4. Policy for the lack of unseen buses in G8.

## Addendum A (2026-10-30): PAPER-FIRST reorientation (investigator instruction; append-only)
`DEC066_ADENDA_PAPER_FIRST_M3OS.md` prevails over the priorities and sequence of the master plan: priority is reproducible paper tables and figures on M3+OS; no requirement of certified nonlinear safety, global optimality, formal statistical coverage, ~100 independent blind cells, EMT/HIL or exhaustive Q/S/V; automatic advance between non-destructive tasks; at most 40 new TDS (ceiling, not quota); retrospective evidence is valid and labelled; DEC-054 `BACKUP_BLOCKED` verdict is not edited, and new TDS require a documented procedural exception (to be recorded before the first new TDS, with a same-disk copy of the essential raw files and its risk).
Errata to the G0 inventory (found while building P0; the G0 files are not rewritten):
1. "Only buses 15, 18, 26, 27, 29 were never used" is wrong: buses 3, 12, 15, 26, 27, 29 were simulated in the DEC-054 prospective cohort (`IEEE39_DEC054_prospective_tests.csv`) and 3, 4, 12 in the DEC-062 OC2 validation. Among the 19 load buses, the only one with no TDS found in the DEC-054…062 data is bus 18 (to be verified for earlier E-series runs).
2. "The predictor freezes the references (no secondary controller)" is inexact: `AndesPlant.affine` adds the RDC reference rates at the post-jump point as a constant forcing term of the affine model (`f = [plant xdot; RDC rates]`). References therefore drift at a constant rate over the horizon; this is a candidate cause of the linear divergence of the 195 s prediction (not verified).
