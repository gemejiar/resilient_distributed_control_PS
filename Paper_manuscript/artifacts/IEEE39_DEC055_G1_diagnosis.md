# DEC-055 — Gate G1: result, diagnosis and decisions required

L1 used 5 of 5 TDS (ledger `IEEE39_DEC055_tds_ledger.csv`, D55T001–D55T005), with no numerical failure. Results are in `IEEE39_DEC055_L1_results.json`. Figures: `figures_main/IEEE39_DEC055_L1_{frequency,voltage,numerics}.png`.

**G1 = FAIL**, against the criteria frozen at G0. By the stop rule, L2 and L3 are **not executed**.

## Verdicts

| Run | Criterion | Value | Verdict |
|---|---|---|---|
| Flat OC1 / OC2 / OC3 (M0 dispatch, 200 s) | f_COI drift ≤ 0.005 Hz in 20 s | 1.0e-4 / 5.8e-5 / 1.2e-4 Hz | met |
| | mean-BusFreq drift ≤ 0.005 Hz | 1.1e-4 / 6.3e-5 / 1.3e-4 Hz | met |
| | Bus-voltage drift ≤ 1e-3 pu in 20 s | **7.5e-3 / 6.3e-3 / 8.9e-3 pu** (3.7e-2 pu at 200 s) | **not met** |
| | V inside 0.95–1.05 pu | 0.969–1.0456 pu | met |
| | No unit-limit violation | none | met |
| Regression (re-run of P3B2_b7P_M3 with the COI recording) | P, Q, V bit-identical to the stored DEC-054 series; COI present | identical (max diff 0.0) | **PASS** |
| Δt/2 (same configuration, first 20 s) | V ≤ 0.005 pu; nadir ≤ 1 % | 2.1e-3 pu; 2.0e-5 relative | met |
| | P ≤ 0.005 pu (added in DEC-055) | **0.041 pu**, confined to the first 50 ms after the event (≤ 6.4e-4 pu after 0.5 s) | **not met** |
| | Same stored-sample classification | dt: SG31 margin +0.0045 pu; dt/2: **−0.0004 pu** (violation) | **not met** |

## D7 — The OPF dispatch is not a closed-loop equilibrium of the RDC in voltage/reactive power

- **Static evidence** (no TDS, `dec055_g1diag.py rates`): at the pre-event state of the M0 and M3 dispatches, the original B2 law gives v_P = 0 (to 1e-15) but max|v_Q| = 0.0097 pu/s (OC1/OC2) and 0.0115 pu/s (OC3).
- **Cause:** the OPF places unit voltages up to 0.045 pu away from the RDC reference V_ref = 1.0 pu (DEC-033).
- **Dynamic evidence:** the RDC is activated at t = 5 s (zero drift in 0–5 s in all 44 DEC-054 and 5 DEC-055 runs). From that moment it moves Qset (up to 0.76 pu in 200 s) and relaxes the voltages towards 1.0 pu.
- **Not a numerical drift.** It is the designed action of the controller.
- **Consequences:**
  - In every TEST run, the post-event voltage and reactive-power trajectories superpose this regulation transient on the event response. The transient is common to M0 and M3.
  - This also applies retrospectively to DEC-054: the round-1 voltage overshoot (1.0522 pu) and the v_margin choice of 0.005 pu were made without separating this effect.
- **It confirms the separation in T-C:** an AC-feasible point (C-i) is not a closed-loop RDC equilibrium (C-ii).

**Alternatives:**
- **(a)** Keep B2 and the frozen protocol. Re-classify the flat criterion as "frequency and initialisation" only, and report the voltage drift as controller action (G1 voltage criterion recorded as not met).
  - Advantage: no change to the method.
  - Risk: post-event V/Q compliance mixes the event and the regulation transient.
- **(b)** Event after the regulation transient: activate the RDC at t = 0 and apply the event once v_Q ≈ 0 (DEC-050: τ ≈ 430 s, so around 2000 s).
  - Advantage: clean separation.
  - Cost: about 10× per TDS. Changes the event time of the protocol.
- **(c)** Constrain the OPF unit voltages to V_ref = 1.0 pu.
  - Changes the M0/M3 design. DEC-026 showed that 1.0 pu at all unit buses destabilises C2 with default REGF1, and C2t needed KPv × 1.5. Feasibility within the 0.95–1.05 band is not guaranteed.
- **(d)** Set V_ref of the RDC to the dispatch voltages.
  - Modifies B2 (not allowed).

**Recommendation: (a), with the voltage results reported separately as "closed-loop (event + RDC regulation)"; or (b) if the investigator requires the isolated event response.**

## D8 — Step-size dependence of the fast post-jump transient

**Observation.** After the algebraic jump (x continuous), P of the SG units keeps rising for a few milliseconds through fast electrical states.
- SG31 in the P3B2_b7P_M3 configuration:
  - algebraic P(t_e⁺) = 6.4792 pu;
  - sample at 5.0 s = 6.4878 pu;
  - sample at 5.0039 s = 6.4955 pu (dt);
  - sample at 5.00195 s = 6.5004 pu (dt/2), above Pmax = 6.50.
- The P peak is therefore not converged with dt = 2⁻⁸ s. Halving dt raises it by about 0.005 pu, and the converged value is unknown with two step sizes only.

**Consequences:**
- (i) Stored-sample classification at dt = 2⁻⁸ s is **not robust for margins below about 0.01–0.02 pu** when the extremum occurs within ~50 ms of the event.
- (ii) Retrospectively for DEC-054, the M3 minimum margin of 0.0103 pu (bus 12, SG31) occurred 3.9 ms after the event, inside this unresolved transient. **Its robustness to Δt is NOT_ESTABLISHED.** The DEC-054 claim "M3 zero violations" must carry this caveat.
- (iii) The T-A acceptance "|P⁺ − first sample| ≤ 5e-3 pu" is not attainable. The first stored sample is one implicit step after t_e⁺, and fast states move up to 0.078 pu in that step (GFM32; DEC-054 had already reported 0.075 pu). The criterion would fail in every TEST run for reasons unrelated to the jump map.

**Alternatives:**
- **(a)** Convergence study before TEST, on one TUNE configuration: dt/4 and dt/8 over a short horizon (about 3 TDS). Then fix the step for TEST and a numerical uncertainty band u_dt.
- **(b)** Keep dt = 2⁻⁸ s and label every cell whose minimum margin lies within ±u_dt (with u_dt from (a)) as `NUMERICALLY_INDETERMINATE`.
- **(c)** Replace the T-A acceptance test by a comparison of P⁺ with the dt → 0 extrapolation of the sample at fixed model time (Richardson on dt, dt/2, dt/4).

**Recommendation: (a) + (b) + (c), declared before any TEST TDS.** This changes thresholds and adds TDS, so it requires authorization.

## D9 — Code defect corrected (no effect on any verdict)

`dec055_common.jump_vs_first_sample` took the sample after t_e as the first post-event sample. In ANDES with the dist_fn mechanism, the sample at t_e already contains the event (callback before the step t_e − dt → t_e). The function was corrected and its unit test updated before any use.

## What remains valid

- G0 (protocol, partitions, cell registry, T-C classification, audits).
- The COI recording, verified bit for bit: f_COI is available for every new run.
- SG39 carries 75 % of the COI weight (M = 100 s on 1199 MVA), so f_COI is close to the SG39 speed.

## Blocked pending a decision

- L2 (TUNE, ε recalibration) and L3 (TEST cohort).
- L4 (T-B) can be authorized independently. It also relates to D7, because the closed-loop equilibrium that T-B needs is the one the voltages relax to.
