# DEC-059 — Scientific reorientation: proposed controller B5′, corrected theorems, minimal evidence (pre-registered)

Status: registered 2026-10-29 before any DEC-059 TDS and before the B5′ implementation.
- Branch: `review/dec059-scientific-reorientation`, from 000eb9f.
- Authorization: the investigator messages "DEC-059 — Aprobación condicionada del plan científico" and "DEC-059 — Aprobación científica condicionada" (decisions DA–DF, sequence R0–R7).
- Mathematical specification: `Paper_manuscript/artifacts/IEEE39_DEC059_theory.md` (T1, T1-F, Lemma 0, Lemma C, rule E*, T2, Proposition OS, P3).
- Matrix: `Paper_manuscript/artifacts/IEEE39_DEC059_contribution_matrix.csv`.

## Frozen

- Plant and topology.
- Case files, OC1–OC3, limits and partitions DESIGN/TUNE/TEST (DEC-055).
- B2 law and gains; B3 definition.
- Physical acceptance criteria:
  - P, Q, S, V margins;
  - instantaneous Pmax criterion;
  - U_D8 = 0.0109 pu;
  - G1 drift thresholds 0.005 Hz and 1e-3 pu in 20 s;
  - AC-05: 0.01 Hz.
- All results of DEC-050 to DEC-057.
- ANDES 2.0.0 source.
- `main`, `main.tex` and the directory structure.

## Numerical configuration (DE), applied to every DEC-059 TDS

- Interpreter: `<repo>/venv/Scripts/python.exe` (ANDES 2.0.0, numpy 2.5.4, scipy 1.18.1, kvxopt 1.3.3.3). The system `python` on PATH is not used.
- Integrator settings:
  - trapezoid, fixed step dt = 2⁻⁸ s, Newton tol 1e-4, `max_iter` 15;
  - `honest` = 0;
  - **`reset_tiny = 0`** (explicit);
  - PQ loads constant power as in the runners.
- Event runs: local refinement dt/16 on [t_e − dt, t_e + 0.5 s] (DEC-057 wrapper, unchanged).
- Peak margins with |m| < U_D8 are NUMERICALLY_INDETERMINATE. Convergence of instantaneous peaks is not claimed.
- Comparison with earlier (reset_tiny = 1) results is made only where lot R2 shows the difference is negligible for the quantity in question.

## Gates

| Gate | Object | Acceptance (frozen) | Effect of failure |
|---|---|---|---|
| G1-P | Plant without secondary control, per OC and dispatch used later | PFlow converged; init residual ≤ 1e-8; 20-s flat drift ≤ 0.005 Hz and ≤ 1e-3 pu; buses in band | That OC/dispatch is not used |
| G1-C | B5′ at d = 0 (flat, 200 s) | Same drift criteria; QP hard-feasible at all samples; v* = v_nom when inactive; min c_j ≥ 0 | B5′ line stops at R3 |
| G-R3 | B5′ smoke (≤ 6 TDS) | Unit tests pass. In every smoke run: E* residual ≤ 1e-10 and E4 holds or the cell is labelled; T2 hypotheses evaluated; no hard-constraint QP infeasibility; min c_j ≥ 0; no TDS failure; convergence to ξ*(d⁺) within AC-05 at 200 s, \|V_i − V_i*\| ≤ 1e-3 pu, sharing std ≤ 1e-3 | Stop the B5′ line; mathematics and R4 static work continue |
| B2/B3 | Comparators | Reported, never gating (DC) | — |
| G-TUNE | Before any TUNE TDS | M3 with the overshoot term frozen per OC (formulation, parameters, code hashes); M3 dispatch passes G1-P; B5′ parameters frozen | No TUNE |
| G-TEST | Before any TEST TDS | TUNE: no UNSAFE cell (a single DEC-055 cut cycle allowed); predictor errors within the declared bound; freeze file with hashes committed and pushed to rdc | No TEST |

B5′ parameters (declared now; frozen at G-TUNE unless the smoke reveals an implementation defect, which is recorded):
- v̄ = 0.01·Sn_i/100 pu/s;
- α = 1 s⁻¹ (γ = α h);
- R = diag(v̄⁻²), ρ_s = 1e6;
- Q_L = I, λ = 1/(2 λ_max(H_r));
- τ_info = 1.0 s;
- ε_sel = 0.01.

## R2 — numerical closure (cap 12 TDS including 2 reserve; predictions declared now)

| Run | Configuration (reset_tiny = 0 unless stated) | Purpose | Prediction / rule |
|---|---|---|---|
| N1 | P3B2_b8P_M3 (OC1), trapezoid, local dt/16, 20 s | Effect of reset_tiny on the D8 transient | \|ΔP\| ≤ 1e-6 pu against D57D8_b8_trapezoid_loc16 on [t_e, t_e + 0.5]; if larger, the D8 and M3V margins are recomputed only in the runs that use them |
| N2 | N1 repeated | Reproducibility | Bit-identical series |
| N3 | D57M3V_B2_b8P_S3 (OC3 M3, B2, dt/16, 200 s) | Robustness of the OC3 refutation | SG31 margin −0.0140 ± 1e-4 pu, still ≤ −U_D8 (UNSAFE) |
| N4–N6 | Plant only (no secondary), OC1/OC2/OC3 M0, 20 s | G1-P | Drift criteria met |
| N7–N8 | B3 flat, OC1/OC2 M0, 200 s | Audit of the DEC-057 "drift 0.0" (dead zone) | Deviation from ξ(z) ≤ 1e-6 pu over 200 s (R7 stable) |
| N9 | B3 flat, OC3 M0, 2000 s, storage 1/16 | Audit of the DEC-057 R7 prediction | Growth at 0.0198 s⁻¹ ± 15 % from round-off; deviation > 1e-3 pu before 2000 s, or TDS failure |
| N10 | RES4 configuration (B2 from t = 0, OC3 M0) at dt/2, 160 s | Step sensitivity of the OC3 instability | Growth rate within ±15 % of RES4; failure time within ±10 s |

Retrospective audit without TDS (argument recorded in the report):
- DEC-050 long run: the references move every step by ≥ 1e-8 pu ≫ 1e-10, so the dead zone does not freeze the approach.
- DEC-051 ± validation: the decay ratio matched the linear prediction.
- DEC-051/052 equilibria: Newton solves, independent of the TDS.

## R3 — B5′ (after T1/T2 are written; unit tests first)

- Code:
  - `src/dec059_eq.py` (rule E*, T2 hypothesis checks, H_r, λ, first-order radii, static, 0 TDS);
  - `src/dec059_b5.py` (QP layer as a `qp_filter` of `run_b3_ieee39.run`, mode B3 so that the pre-event offset equals ξ*(d⁻));
  - `src/dec059_tds.py` (ledger D59Txxx, plans, runner reusing `dec057_tds.execute` unchanged);
  - `src/test_dec059.py` (no ANDES).
- Unit tests:
  - T1 invariance on random affine/disc instances;
  - 0 ∈ 𝒰_k on W;
  - fast path equals the solver solution;
  - uniqueness;
  - v* = 0 at the target;
  - the CLF row sign convention;
  - the offset switch at t_e + τ_info.
- Smoke (≤ 6 TDS), in this order:
  1. G1-C: B5′ flat OC1 M0 200 s;
  2. B5′ on the DESIGN cell b8P_S2 OC1 M0, 200 s, with the dt/16 local refinement;
  3. idem OC2 M0;
  4. B5′ OC3 M0 flat (demanding: the target is TARGET_UNSTABLE if R7 fails; the outcome is reported);
  5–6. reserve for one implementation repair and its repeat.

  Each step is executed only if the previous one passed G-R3 or was a pre-declared demanding case.

## R4–R7 (plans are sealed later, before their TDS)

- **R4.** Static M3 with the overshoot term (DD):
  - The term is calibrated only on DESIGN and TUNE data.
  - It must carry a declared physical model (dense-time response of the post-jump linearisation in [t_e, t_e + 50 ms], plus an empirical model-error bound).
  - Report its scenario dependence, conservatism (cost and MW against M3 without the term) and computation time.
  - Then G1-P at the new dispatches (2 TDS) and TUNE (16 TDS).
- **R5.**
  - TEST OC1/OC2: 3 buses × 3 severities × {M0, M3} × B5′ (36).
  - Comparison on the TEST S2 cells, M3 × {B1s, B2, B3} (18).
  - OC3 demanding: M0 × S2 × 3 TEST buses × {B2, B5′} (6).
  - τ_info check on one TEST S2 cell: τ and 4τ (2).
  - No redesign after the first TEST TDS.
- **R6.** E* with |𝒜| ≥ 2 (static), and the B5′ frontier at one OC1 location by bisection (≤ 8).
- **K4 illustration.** 4 TDS from perturbed initial states (±e along the slowest mode, two amplitudes). Presented as illustration, not proof.

Predefined comparison metrics (K7):
- f_COI nadir;
- RoCoF (100 ms window from t_e);
- frequency error at 120 s and at 200 s;
- settling time to |Δf| ≤ 0.01 Hz;
- unit voltage error |V_i − V_i,set| at 200 s (mean and max), with V_set the dispatch set-point; B2 is also reported against its own target of 1.0 pu;
- bus V min/max;
- P-sharing error: the std of (P_i − Pⁿ_i)/Pⁿ_i over the units not in 𝒜, at 200 s;
- physical P/Q/S/V margins;
- reference margins min c_j;
- QP status and slack incidence;
- CPU time per step.

## Budget (maximum 120 TDS)

| Line | TDS |
|---|---|
| R2 numerical closure | 10 + 2 reserve |
| R3 smoke | 6 |
| R4 G1-P of the new M3 dispatches + TUNE | 2 + 16 |
| R5 TEST + comparison + OC3 + τ_info | 36 + 18 + 6 + 2 |
| K4 illustration | 4 |
| R6 frontier | 8 |
| Unassigned reserve (logged justification) | 10 |
| **Total** | **120** |

Unassigned resources are kept as reserve and are used only with a ledger justification. No line may borrow from another without being recorded.

## Addendum A (recorded before the R4 and R5 plans; append-only)

Each item was decided before any TDS that it affects.

1. **Rule E* (E2/E3 bands).** The ε_sel-interior bands are widened to contain the pre-event value. This was found in the first static test, before any TDS: SG31 in OC1 M0 is dispatched inside the 1 % margin, and the original rule moved the d = 0 target away from ξ(0). Targets are tagged `r2_`; the revision-1 file `target_OC1_M0_d0` is kept as superseded.
2. **CLF constructibility.** The protocol builds H_r with K = K_nom. When A_r is not Hurwitz (OC3: +0.0198 / +0.0207 s⁻¹, Qset SG30), H_r is indefinite. The CLF row is then dropped and the target is labelled CLF_NOT_CONSTRUCTIBLE.
   - main.tex requires a stabilising auxiliary K for the certificate.
   - The static analysis `DEC059_state/oc3_clf_stabilizability_proposal.json` shows that (A_r, G_r) is stabilizable and that an LQR K (Q = I, R = I) gives H ≻ 0, with ‖ΔK‖ ≈ 490.
   - Adopting such a K is a **new methodological decision left to the investigator**; it is not implemented.
3. **Smoke 4.** It is the OC3 M0 b8P_S2 event instead of the flat run. At an exact equilibrium the discrete residual is exactly zero, so a flat run cannot excite an unstable mode (R2: the 2000-s B3 run stayed at 1e-13).
4. **R4 overshoot term (DD).**
   - Excursion: E = max(E_grid, E_dense), with E_dense the exact-exponential response of the M3 affine post-jump predictor on [0, 50 ms] at step DT/64.
   - Tightening: eps_E ← eps_E + eps_OS + eps_D8, with eps_OS = 3.9e-4 pu (up) / 6.1e-5 pu (down), the maximum underprediction over 18 DESIGN/TUNE cells (`IEEE39_DEC059_OS_calibration.json`), and eps_D8 = U_D8 = 0.0109 pu, so that the design aims at the SAFE class of rule M3V-1.
   - Seed: the DEC-055 M3 dispatch.
   - dec054_opf is unchanged; the term enters through the plant adapter.
5. **R5 comparators.** They follow the main.tex benchmark list:
   - B2 (original RDC);
   - B1s (conventional separately saturated integral controller, defined in `dec059_b5.B1s`: total speed 160 as B2, sharing ∝ Pⁿ, Q/V toward the dispatch set-points, per-reference clamps, no communication);
   - B4′ (barrier-only filter: B5′ without the CLF row).

   B3 is not in the main.tex list and is dropped from the R5 comparison. The 18-TDS allocation is unchanged.
6. **K4 illustration.** The 4 TDS stay reserved. The Lyapunov-function evolution is first read from the smoke and TUNE runs (𝒱 logged at every sample), which already start from perturbed post-event states. The K4 runs are used only if that is insufficient.

## Addendum B (recorded before the G1-P and TUNE TDS of R4; append-only)

**Ledger count at this point:** 14 of 120 TDS (R2 10, R3 4; D59T001–D59T014). An earlier progress message said 15; that was a miscount.

**1. Cell classification (rule M3V-1, applied to every DEC-059 event run, DESIGN, TUNE and TEST alike).**
- P peak margin m₅₀ = min over units of (Pmax − P) on [t_e, t_e + 50 ms] (the dt/16-refined window):
  - SAFE if m₅₀ ≥ U_D8 = 0.0109 pu;
  - UNSAFE if m₅₀ ≤ −U_D8;
  - NUMERICALLY_INDETERMINATE otherwise.
- After 50 ms, P margins use the stored samples, binary: a negative margin is UNSAFE.
- Q, S, V margins use the stored samples, binary: a negative margin, or a bus voltage outside [0.95, 1.05], is UNSAFE.
- The cell class is the worst class over these tests: UNSAFE > NUMERICALLY_INDETERMINATE > SAFE.
- A TDS failure is TDS_NUMERICAL_FAILURE, reported separately and never counted as safe.
- Cells whose pre-TDS T-A prediction is a_j < 0 (not `admissible_at_jump`) are labelled INADMISSIBLE_AT_EVENT. They are outside the safety claim whatever the controller (rate-bounded class), so they map to OUTSIDE_ASSUMPTIONS in the R5 reports, but their TDS class is still recorded.
- `dec059_pred.py` fixes the predictions before the TDS; they are compared afterwards and never replace the TDS class.

**2. Three distinct error sources, never merged.**
- (a) **OS predictor error:** the TDS peak margin minus the dense-model peak margin, per cell. Tolerance for the TUNE check: |error| ≤ eps_floor_pu = 1e-3 pu (the declared floor of `PROPOSED`).
- (b) **D8 numerical uncertainty:** U_D8 = 0.0109 pu, fixed from DEC-057. It is a band of the class, not an error of the model.
- (c) **Physical margin:** the margin itself.
- A cell with |m₅₀| < U_D8 is classified NUMERICALLY_INDETERMINATE, even if the model predicts a sign.

**3. Design criteria of M3+OS (checked at the gate R4 → TUNE).**
- Status FEASIBLE_PREDICTED or LOCAL_OPTIMUM_FOUND;
- min predicted margin ≥ −τ_cut = −1e-4 pu over the DESIGN rows, with eps_E including eps_OS and U_D8;
- pre-event initialisation valid (G1-P);
- seed and cfg as declared in Addendum A item 4.

**4. G3 (TUNE verification) for an OC.**
- The eligible cells are the S2 cells, plus S3 cells promoted by the DEC-055 rule (T-C AC_FEASIBLE, M3 design set contains S3, and `admissible_at_jump` predicted true). Non-promoted S3 cells are STRESS_EXPLORATORY: they are run and reported, with no safety claim.
- G3 PASS requires:
  - (i) no eligible cell UNSAFE;
  - (ii) no TDS failure;
  - (iii) per-cell OS predictor error within the tolerance of item 2(a);
  - (iv) B5′ gate G-R3 conditions in every run (hard QP feasibility, min c_j ≥ 0, no fallback, convergence to the target for the cells whose target satisfies T2).
- NUMERICALLY_INDETERMINATE eligible cells do not fail G3, but they are reported as NOT_VERIFIED and are not counted as safe.
- If G3 fails: **one** dynamic cut cycle for that OC (DEC-055 protocol G3).
  - The violating eligible TUNE scenarios are added to the M3+OS design set;
  - Algorithm 1 is rerun unchanged (same formulation, cfg, eps and seed = the current M3+OS dispatch);
  - the changed dispatch is rechecked: G1-P plus a TDS of the cut cells only (ledger lines R4 remainder and RES).
  - If the cut design is INFEASIBLE_NOT_DEMONSTRATED, or the rechecked cells are still UNSAFE, the OC has no TEST cohort (G3 stop) and is reported with the cause.

**5. Parameters adjustable in TUNE.**
- Only the M3 design quantities of the DEC-055 protocol: eps vectors (including eps_OS) and the cut set.
- B5′ parameters (v̄, α, R, ρ_s, τ_info, ε_sel) and the E* rule are frozen as in the protocol; TUNE does not optimise them.
- The theorem hypotheses (H1–H5), the criteria and the U_D8 band are not changed.
- Every configuration evaluated is recorded in the TUNE report, failed ones included.

**6. TEST intactness check.** No DEC-059 plan, ledger row, target or prediction file before the freeze contains a TEST bus (21, 31, 39). `dec059_gate.py` checks this mechanically and writes the record.

## Addendum C (DEC-060; recorded before the recheck TDS; append-only)

**Authority.** DEC-060 (investigator): TEST stays sealed; original criteria and historical evidence unchanged; up to 9 TDS for the OC1 cut recheck, DESIGN/TUNE only; cumulative cap 120 TDS.

**1. Status of the criteria.** The TUNE verdict stands as recorded: G3 FAIL in OC1 [(i), (iii), (iv)] and OC2 [(iii)]. Criterion (iii) stays two-sided |e| ≤ 1e-3 pu and criterion (iv) stays 1e-3 pu at 200 s. Nothing below is used to declare either met retroactively.

**2. Recheck set (9 TDS, ledger block RES; the R4 block is exhausted, 18/18).** G1-P at the cut dispatch (1) + the eight OC1 TUNE cells b7, b20, b16, b24 × {S2, S3} with B5′ (frozen), local dt/16 (8). Targets E* at the cut dispatch (rule unchanged, tags `r2_OC1_M3CUT_*`) are computed before the TDS. The cut dispatch is the single dynamic cut cycle allowed by item 4 of Addendum B; any further redesign is a **new revision** with its own gate.
- Cut cells (protocol "cut cells only"): b20 S2, b16 S3, b24 S3.
- b20 S3 is added because the pre-TDS prediction at the cut dispatch flips its `admissible_at_jump` from false to true (a_j ≥ 0), so the DEC-055 promotion rule makes it eligible.
- b7 S2, b7 S3, b16 S2, b24 S2 are supplementary regression cells (does the cut damage cells that were fine?).
- This set is wider than the protocol text ("cut cells only"); the extension is conservative and declared.

**3. Hypotheses and predictions (static, committed before any recheck TDS; files `IEEE39_DEC059_pred_OC1_M3CUT_{design,tune}.json`, committed in b37fb7a).**

| Cell | Predicted min Pmax margin (pu) | Predicted class | Binding unit | Eligible (rule at the cut dispatch) |
|---|---|---|---|---|
| b7 S2 | +0.0756 | SAFE | SG31 | yes |
| b7 S3 | +0.0037 | NUMERICALLY_INDETERMINATE | SG31 | yes (admissible) |
| b20 S2 | +0.0150 | SAFE | SG33 | yes (cut cell) |
| b20 S3 | −0.2110 | UNSAFE | SG33 | **yes, newly admissible** |
| b16 S2 | +0.1672 | SAFE | SG31 | yes |
| b16 S3 | +0.1290 | SAFE | SG33 | yes (cut cell) |
| b24 S2 | +0.1681 | SAFE | SG31 | yes |
| b24 S3 | +0.1335 | SAFE | SG33 | yes (cut cell) |

- H-A: G1-P passes at the cut dispatch.
- H-B (mechanism): the cut moves the pre-event SG33 set-point by −0.157 pu (6.511 → 6.354 pu, Pmax 6.82 pu); every other component of the dispatch vector changes by ≤ 6e-4; the binding unit of the cut cells stays SG33 and its post-event peak margin becomes positive.
- H-C: the three cut cells are SAFE (b20 S2 only +0.015 pu above the band U_D8 = 0.0109).
- H-D: b20 S3 is UNSAFE. This is a **pre-registered expected failure of G3 (i) under reading A below**; it is not a choice.
- H-E: the supplementary cells keep their predicted classes.
- H-F (predictor sign): e = m_TDS − m_pred ≥ 0 in every cell, as in 34/34 earlier cells (16 TUNE, 18 calibration); |e| > 1e-3 expected in the b20 cells and S3 cells, so (iii) two-sided is expected to fail again.
- H-G: unit-voltage error at 200 s of the S3 cells is expected at about 1e-3 pu again, so (iv) is expected to fail again.

**4. Decision rule for the new gate (fixed now).**
- Reading A (primary, protocol-literal): eligibility by the rule at the dispatch under test; criteria (i)–(iv) literal over all eligible cells of the recheck set.
- Mandatory safety blocker: any eligible cell UNSAFE, or any TDS failure, keeps TEST sealed under every reading.
- Reading B (reported, not primary): eligibility fixed at the TUNE plan (b20 S3 not eligible).
- Cut-cells-only view and the one-sided criterion (iii) are reported separately and labelled alternative; the latter is a post-TUNE amendment (`dec060_audit.py`) that could only apply to a new revision.
- Longer-horizon voltage convergence (D3) is a diagnostic from the stored 200-s series (exponential fit on 100–200 s, extrapolated), with no extra TDS.
- OC2 has no UNSAFE cell, so no cut cycle exists for it; its G3 verdict from TUNE is final under this protocol and no OC2 TDS is run.
- If the gate passes under reading A: freeze design, code, parameters, metrics and hashes (git tag and acta) before any TEST TDS. Otherwise TEST stays sealed.

**5. Post-TUNE changes (all declared).** (a) `dispatch_z` accepts `M3CUT`; (b) the recheck set is wider than the protocol text; (c) one-sided criterion (iii) study and long-horizon extrapolation, both alternative; (d) ledger block RES used for the recheck.
