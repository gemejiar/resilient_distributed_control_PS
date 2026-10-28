# DEC-054 G3 — Predictor audit against ANDES (P3-A)

**Verdict: `PREDICTOR_AUDIT_PASS`** under the criteria sealed in `IEEE39_DEC054_p3a_plan.json` before the first TDS (commit `25a1403`). **TDS used: 8 of 8 in P3-A (ledger 8/48), none failed.** DESIGN buses `{8,23,28,25}` only. Gate 0: investigator waiver (backup not independent).

## Plan executed (predeclared)
| Run | Bus | Event | Dispatch | Purpose |
|---|---|---|---|---|
| P3A_01 | 8 | P +0.58564 pu | z_ref (historical C2t) | predictor |
| P3A_02 | 23 | P | z_ref | predictor |
| P3A_03 | 28 | P | z_ref | predictor |
| P3A_04 | 25 | P | z_ref | predictor |
| P3A_05 | 8 | Q +0.17345 pu | z_ref | P-output response to a Q step |
| P3A_06 | 23 | Q | z_ref | same |
| P3A_07 | 28 | P | z_ref with SG31 −0.10, SG38 +0.10 | dependence on `I(z)` (redispatched point) |
| P3A_08 | 8 | P | z_ref, step 2^-9 s | numerical fidelity vs P3A_01 |
All runs: B2 original, event at 5 s via the `dist_fn` callback, 200 s (195 s post-event), trapezoid `dt=2^-8 s`, DAE residual ≤ 4.7e-8; all were classified `TDS_PHYSICAL_VIOLATION` because the historical C2t dispatch itself violates the voltage band pre-event (21 buses > 1.05 pu, max 1.0730) and SG31 P (not an audit failure). The ledger's `dt` column records the nominal step also for P3A_08 (its actual step was 2^-9 s; stored in the run configuration).

## Alignment discovered and used
With `dist_fn` the load changes **before** the step 4.99609375→5.0, so the stored sample at 5.0 is one trapezoid step after the event; observed sample `t_k` ↔ model time `τ = (t_k−5)+2^-8`; `P_pre = P(4.99609375)`. (ANDES `Alter` events instead insert samples at 4.9999/5.0/5.0001; see the G2 audit.)

## Results (P events T1–T4, T7)
Errors are observed − predicted (positive = optimistic) for the predicted peak `P_pre + dP + E_up` and trough `P_pre + dP − E_dn`:
| Unit | max peak error (pu) | max trough error (pu) | pass |
|---|---|---|---|
| SG30 | +0.0058 | +0.0005 | yes |
| **SG31** | +0.0001 | +0.0005 | yes |
| SG33 | +0.0012 | +0.0002 | yes |
| **SG35** | +0.0010 | +0.0004 | yes |
| SG38 | +0.0013 | +0.0011 | yes |
| SG39 | +0.0027 | +0.0022 | yes |
| GFM32 | −0.0128 | −0.0042 | yes (conservative) |
| GFM37 | +0.0026 | −0.0058 | yes |
| GFM34 | −0.0166 | −0.0023 | yes (conservative) |
| GFM36 | −0.0186 | −0.0035 | yes (conservative) |
Criteria: positive peak/trough error ≤ 0.03 pu for every unit, SG31 and SG35 must pass, ≤ 3 failing units; all met. Times of the maxima agree (e.g. SG31 slow peak 2.6–2.8 s observed vs 2.8 s predicted on the earlier H3-2 check; the fast SG31 peak at the first samples).
Numerical fidelity (P3A_08 vs P3A_01): peak difference 0.0044 pu, trough 0.0083 pu (tolerance 0.01): `ok`.
Q steps (P3A_05/06): the predictor errors on P outputs are ≤ 0.024 pu except GFM36 (−0.022/−0.039, conservative); all positive errors ≤ 0.0002.
Redispatched point (P3A_07): positive peak errors ≤ 0.0058, i.e. the `I(z)`-dependent predictor holds away from `z_ref`.
First stored sample vs model at τ = 2^-8 s (reported, not a criterion): errors up to 0.075 pu for GFM32 (fast GFM states within the first step); the peaks/troughs that determine the margins are unaffected.

## Calibrated margins (DESIGN data only; EMPIRICAL_LOCATION_AWARE_MARGIN, no coverage claim)
`ε_J` = floor 1e-3; `ε_E` = max(1e-3, 1.5 × max positive total peak/trough error): upper side — SG30 0.0087, SG31 0.0010, SG33 0.0017, SG35 0.0015, SG38 0.0019, SG39 0.0040, GFM37 0.0039, GFM32/34/36 0.0010; lower side ≤ 0.0033 (SG39), others ≤ 0.0017 (file `IEEE39_DEC054_p3a_analysis.json`). They come from 5 P events (4 buses, 1 amplitude, 2 dispatches) and are not bounds.

## Limitations
* Only P outputs are modelled: Q/S/V (and ANDES limiter states, not stored by the executor) remain **verification metrics**; Q/S/V constraints are not imposed by the optimisation. Scope decision (taken before any prospective result): the prospective cohort is **6 P scenarios; Q out of scope**.
* Five P events; single amplitude; mostly one dispatch plus one redispatched point; the audit does not certify the predictor elsewhere.
* The linearisation is rebuilt per candidate and event; the audited dispatches are near `z_ref`.

## Files
`IEEE39_DEC054_p3a_plan.json`, `IEEE39_DEC054_p3a_analysis.json`, `IEEE39_DEC054_dynamic_predictor_validation.csv`, `IEEE39_DEC054_algebraic_jump_validation.csv`, `IEEE39_DEC054_tds_ledger.csv`; raw series/configs/hashes per run in `Paper_manuscript/backups/DEC054_runs/P3A_*` (local, Git-excluded; hashes in each `hashes.json`).
