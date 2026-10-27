# DEC-053 — Reserve policy specification (H3-R)

**Label:** `OFFLINE_SCENARIO_CONDITIONED_PREVENTIVE_REDISPATCH` (no independent trial supports a more specific label).
**Status:** `PREVENTIVE_NUMERICALLY_SUPPORTED`. Reconstruction + empirical predictor. No new algorithm is claimed superior; no candidate policy was frozen or tested (`IEEE39_DEC053_reserve_policy_candidate.json` does **not** exist by design: 0 TDS spent, no policy defined that the budget could validate against a comparable baseline).
Reproduction: `Paper_manuscript/src/dec053_reserve.py` → `IEEE39_DEC053_reserve_replay.json`, `_reserve_validation.csv`, `_reserve_attribution.json`.

## 1. What the historical rule R35_040 is (C1 audit of `e9b_variant.py`)

| Layer | Content | Information needed | Origin of the information |
|---|---|---|---|
| Vsafe | AC selection B3-A (d = 0, v1 S0) imposed on PV `p0`/`v0` before the power flow; includes lowering SG31 pre-event P from 6.46 to 6.361 pu (reserve 0.040 → 0.1389 pu) | AC model, unit limits, voltage band, margins asked of the AC problem | pre-event model data (SLSQP local optimum of the selection problem; no optimality claim) |
| R35 transfer | `p0[SG35] -= δ`, `p0[GFM_b] += δ·w_b` | receiver set {32,37,34,36}, δ, weights w_b | **simulation-derived** |
| w_b | `max(min P-margin of GFM_b in the B2 P+ run on C2t_Vsafe, 0)` normalised (GFM37 0.767, GFM34 0.122, GFM32 0.092, GFM36 0.019) | transient margins of a TDS of the **same event** (P+ 58.564 MW, bus 4) | **dependence on the outcome to be predicted** |
| δ = 0.015 (R35) | smallest multiple of 0.005 pu above the bisection threshold `δ_min = 0.014590` pu (30 s B2 TDS bisection, P+) | repeated TDS | simulation-derived |
| δ = 0.040 (R35_040) | chosen by the investigator (DEC-044/045) so that the SG35 transient margin ≥ 0.020 pu (obtained 0.0245) | — | **not computed by the rule**; not an automatic optimum |

Consequences: (i) for the calibration event the rule is **in-sample**; (ii) it is not a rule deducible from pre-event data alone; (iii) 0.040 pu must never be described as an optimum.

## 2. HISTORICAL_RULE_REPLAY (C3)

Static power flow + TDS *initialisation* (no time stepping) with the frozen hook (`e9b_variant.hook_for(0.040)`): replayed pre-event unit P equals the stored initial-condition table (`IEEE39_E9B0_initial_condition_R35_040_units.csv`) with maximum difference **0.0 pu**; weights recomputed from the stored margins equal the stored ones (difference 0.0). Input and code SHA-256 are in the replay JSON. Status `REPLAYED_FROM_IDENTIFIED_INPUTS`.

## 3. Design inequality, as used (C2)

For unit *i* and a P step of amplitude *a* at bus *b*:
`R_i = Pmax_i − P_i^pre` (exact, case data); `ΔP_i^jump(a,b)` (algebraic solve after the event with differential states continuous; floating point, no validated enclosure; linear/monotone on the grid 0.25–1.5 × 58.564 MW); `ΔP_i^exc = (a/58.564 MW)·max(fast_i, slow_i, 0)` (**empirical library**: increments observed in the R35_040 run at bus 4); `ε = 2.28e-3 pu` (discrepancy of the **jump** term only).
Predicted margin = `R_i − ΔP^jump − ΔP^exc`. Condition `margin ≥ ε` is a **calibrated predictor, not a certified safe condition**, because `ΔP^exc` is empirical.
Optional prototype objective (not executed): minimise a pre-declared weighted distance to the original dispatch plus a penalty on lost reserve, subject to AC feasibility, P/Q/S limits, 0.95–1.05 pu on 39 buses and the predicted margins; the AC problem is non-convex, so a solver solution is a local optimum.

## 4. Declared calibration domain (outside → `OUT_OF_CALIBRATION_DOMAIN`)

* plant: `C2t_Vsafe_R35_040` family, B2 original, graph/gains/limits frozen, 6 SG + 4 GFM;
* event: P step at t = 5 s, bus 4 (library location) with 14.6–64.4 MW (0.25–1.10 × 58.564), and one other location (bus 18, 58.564 MW) tested; Q+ 17.345 MVAr at bus 21; step shape only;
* horizon 200 s transient; no N−1; no delay > 0.5 s; no ramps.
* **Known in advance:** the design scenario (bus, amplitude, step). **Not known in advance:** the actual disturbance; protection is only against the declared class.

## 5. Evidence (C4–C6)

| Run | Role | SG31 error | SG35 error | Largest |error| (unit) | Optimistic units |
|---|---|---|---|---|---|
| H3-1 P+ 64.4204 MW, bus 4 | dynamic validation after model screening; same bus as library, amplitude extrapolated | +4.3e-5 | +1.9e-5 | 3.3e-4 (GFM36) | none |
| H3-2 P+ 58.564 MW, bus 18 | dynamic prospective validation after analytic screening of the same model (bus chosen as smallest positive predicted margin) | +8.5e-4 | +1.1e-2 | 0.0600 (SG39) | **SG39 −0.0600 pu (26 ε), GFM32 −0.0366 pu (16 ε)**, both non-binding (margins 4.79, 0.287 pu) |

Errors are observed − predicted margin (negative = optimistic). They are not hidden behind SG31/SG35; ε is not an error bound. This is not an external statistical test and certifies no other location (eight further buses are predicted to violate at 58.564 MW; analytic only, not simulated).

**Dispatch attribution (P+ bus 4, B2, 200 s):** algebraic jump margin of SG31: C2t −0.0465, Vsafe voltages only −0.0490, Vsafe dispatch only +0.0522, Vsafe +0.0495, R35_040 +0.0495 → the SG31 benefit comes **entirely from the dispatch**, none from the voltage set-points. Observed worst transient margins (stored series): SG31 −0.0699 (C2t, violated 5.98 s) → +0.0250; SG35 +0.0150 (C2t) → −0.0141 (Vsafe; 1.47 s violated) → +0.0004 (R35) → +0.0245 (R35_040), with the SG35 minimum at ≈7.7–7.8 s (slow electromechanical) while the SG31 violation is the fast jump at t = 5.004 s plus the first 0.15 s. R35 adds margin to SG35 only. OPEN-SG31-PMAX of the original C2t stays open.

**Nominal frontier:** predictor crossing 70.278 MW (SG31 binding) is a *point estimate*. Dynamic evidence at bus 4: 65.8845 MW respects all limits, 73.205 MW violates SG31, 87.76 MW violates SG31 and SG35 → bracket [65.8845, 73.205] MW; prediction lies inside. Location, dispatch, 40 s horizon and step shape condition it; 70.3 MW is not an exact frontier. Q: step 138.6 MVAr fails in the TDS at 5.2 s (E12, voltage collapse in the integration), whereas the same amplitude as a 5 s ramp respects limits and band (DEC-050); the failure is therefore not attributed to pure numerical error nor to physical instability (the static AC equilibrium exists up to ≈ 277 MVAr).

## 6. Not established
No HOCBF, no certified bound of the excursion term, no safety for other buses/amplitudes/ramps/N−1/delays, no claim that the weights or δ are optimal, no deployable causal policy (the weights use a simulation of the event they protect against).
