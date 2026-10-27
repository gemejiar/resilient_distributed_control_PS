# DEC-053 — Scientific gaps

## A. Gaps that limit claims of the reformulated paper (H1–H4-R, preventive reserves)

| ID | Gap | Effect on the claim | Evidence |
|---|---|---|---|
| G1 | Cell B1 × R35_040 (and B0 on R35_040) never run | Controller × dispatch interaction not estimable; controller effect only on historical C2t | `IEEE39_DEC053_comparability_matrix.csv` CMP-04/06 |
| G2 | B1 and B2 tuned independently | The controller contrast compares two tuned designs, not the control law class | CMP-01 |
| G3 | No P+ run longer than 200 s; Q+ 2000 s only for R35_040 (decimated, dt 0.39 s) | Q/V convergence of B1 and of C2t-B2 not observed within horizon (NOT_OBSERVED_WITHIN_HORIZON) | `IEEE39_DEC053_H2_metrics.csv` |
| G4 | Reserve excursion term is empirical (one library location, 200 s) | H3-R stays a calibrated predictor; optimistic at SG39/GFM32 in the bus-18 run | `IEEE39_DEC053_reserve_validation.csv` |
| G5 | Reserve weights and δ derived from a simulation of the protected event; δ = 0.040 chosen, not computed | Rule is in-sample for the calibration event, not deployable causal | `IEEE39_DEC053_reserve_replay.json` |
| G6 | No prospective policy frozen and validated on held-out events | No claim of a new algorithm | `IEEE39_DEC053_reserve_policy_spec.md` |
| G7 | RDC weights Pn remain C2t values after redispatch | P-sharing spread ≈ 4 % on R35_040 | `IEEE39_DEC053_H2_metrics.csv` |
| G8 | Jacobian error δ_A not bounded; root not certified; region NOT_CERTIFIED | H4-R stays conditional, no joint H3–H4 guarantee | DEC-052 |
| G9 | SG capability curves, OEL/UEL, converter current, SoC/energy, rate limits, protections, EMT, N−1 not modelled | Physical compliance is limited to represented P/Q/S/V limits | `IEEE39_DEC053_constraints_dictionary.csv` |
| G10 | Violations between samples (dt 2^-8 s) not bounded | No safety-between-samples statement | same |
| G11 | 20 raw series > 10 MB are local-only (AT_RISK_LOCAL_ONLY); no verified independent backup | Hashes only; regeneration by re-running stage runners | `IEEE39_DEC053_reproducibility.json` |
| G12 | OPEN-SG31-PMAX (DEC-031) for the original C2t | Original C2t violates SG31 Pmax in P+ under all controllers tested | CMP-01/03/07 |
| G13 | COI frequency not computed (inertia weights not in the series) | Frequency metrics are unweighted means of 39 BusFreq signals | `dec053_core.py` |

## B. Requirements of the original CLF–HOCBF not pursued (outside the reformulated scope)

HOCBF/CLF–HOCBF closed-loop filter (B4/B5), certified forward invariance, regional stability certificate, QP feasibility certificate under actuator limits, MPC, GFL extension, real-time (computation-time) claims, EMT-level protection, rigorous interval enclosure of the root and Jacobian (DEC-052, blocked: no AD/interval backend for the 706 ANDES equations).
