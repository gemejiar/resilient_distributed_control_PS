# DEC-054 G2 — Real-plant adapter audit

Gate 0: `BACKUP_WAIVED_NOT_INDEPENDENT` (investigator waiver; copy NOT independent). **TDS used: 0.** Static only: PFlow, TDS.init without stepping, algebraic jumps and Jacobians on DESIGN buses `[8, 23, 28, 25]`.
**Overall: PASS** (ANDES 2.0.0, 50.4 s).

| Check | Status |
|---|---|
| C01_variable_and_unit_mapping | PASS |
| C02_limits_bases_slack | PASS |
| C03_initialisation_validity | PASS |
| C04_RDC_initialisation_matches_executor | PASS |
| C05_AC_balance_and_slack | PASS |
| C06_DESIGN_jumps_and_algebraic_Jacobian | PASS |
| C07_post_jump_anchoring_no_double_count | PASS |
| C08_PSS_12_genuine_states_and_reduced_structure | PASS |
| C09_event_callback_algebraic_order_at_t5 | PASS |
| C10_horizon_5_to_200s | PASS |

## Evidence (see the JSON for all numbers)
### C01_variable_and_unit_mapping — PASS
```
{
 "n_vars": 19,
 "names": [
  "p0_SG30",
  "p0_SG31",
  "p0_SG33",
  "p0_SG35",
  "p0_SG38",
  "p0_GFM32",
  "p0_GFM37",
  "p0_GFM34",
  "p0_GFM36",
  "v0_SG30",
  "v0_SG31",
  "v0_SG33",
  "v0_SG35",
  "v0_SG38",
  "v0_SG39",
  "v0_GFM32",
  "v0_GFM37",
  "v0_GFM34",
  "v0_GFM36"
 ],
 "unit_bus_ctx": [
  30,
  31,
  33,
  35,
  38,
  39,
  32,
  37,
  34,
  36
 ],
 "pv_buses": [
  30,
  31,
  32,
  33,
  34,
  35,
  36,
  37,
  38
 ],
 "slack_bus": [
  39
 ],
 "n_buses": 39,
 "n_SG": 6,
 "n_GFM": 4,
 "z_ref": [
  4.36086385,
  6.45999998,
  6.51999998,
  6.86999998,
  7.64783381,
  7.24999998,
  3.21521338,
  5.07999998,
  5.79999998,
  1.035534,
  1.013246,
  1.01343,
  1.06,
  1.052803,
  1.03,
  1.020528,
  1.013996,
  1.019109,
  1.06
 ],
 "P_pre_PV_equals_p0_max_diff": 1.7763568394002505e-15
}
```
### C02_limits_bases_slack — PASS
```
{
 "max_abs_diff_vs_E8_stored_limits": {
  "pmax": 0.0,
  "pmin": 0.0,
  "qmax": 0.0,
  "qmin": 0.0,
  "smax": 0.0
 },
 "base_MVA": 100.0,
 "Sn_pu_equals_smax": true,
 "slack_limits": {
  "pmax": 11.0,
  "pmin": 0.0,
  "qmax": 5.7485,
  "qmin": -1.73261
 },
 "lim_SG39": {
  "pmax": 11.0,
  "pmin": 0.0,
  "qmax": 5.7485,
  "qmin": -1.73261,
  "smax": 11.99
 }
}
```
### C03_initialisation_validity — PASS
```
{
 "valid_candidates": {
  "z_ref": {
   "ok": true,
   "reason": null,
   "init_report": {
    "ok": true,
    "reasons": [],
    "pf_ok": true,
    "pf_converged": true,
    "tds_initialized": true,
    "tds_test_ok": true,
    "residual_f_inf": 2.220446049250313e-16,
    "residual_g_inf": 4.215672255725167e-09,
    "finite": true,
    "tol": 1e-08
   },
   "I_vs_executor": 0.0,
   "k_ip": 57.21380351909574,
   "Vmin": 1.0018570383987089,
   "Vmax": 1.0729898322851823,
   "P_slack": 5.731104244528378,
   "Q_slack": -0.2962704801493684
  },
  "SG35-0.30_GFM34+0.30": {
   "ok": true,
   "reason": null,
   "init_report": {
    "ok": true,
    "reasons": [],
    "pf_ok": true,
    "pf_converged": true,
    "tds_initialized": true,
    "tds_test_ok": true,
    "residual_f_inf": 4.440892098500626e-16,
    "residual_g_inf": 4.223858596219543e-09,
    "finite": true,
    "tol": 1e-08
   },
   "I_vs_executor": 0.0,
   "k_ip": 57.24815271729646,
   "Vmin": 1.001632242982419,
   "Vmax": 1.0730133857022244,
   "P_slack": 5.732890030647369,
   "Q_slack": -0.29699004082156644
  },
  "v0-0.01": {
   "ok": true,
   "reason": null,
   "init_report": {
    "ok": true,
    "reasons": [],
    "pf_ok": true,
    "pf_converged": true,
    "tds_initialized": true,
    "tds_test_ok": true,
    "residual_f_inf": 2.7842311789427754e-16,
    "residual_g_inf": 1.7819576925148795e-09,
    "finite": true,
    "tol": 1e-08
   },
   "I_vs_executor": 0.0,
   "k_ip": 54.26439317652364,
   "Vmin": 0.9912307117803467,
   "Vmax": 1.0607181120655589,
   "P_slack": 5.739155028421013,
   "Q_slack": -0.1898958711769133
  },
  "SG31-0.10_SG38+0.10": {
   "ok": true,
   "reason": null,
   "init_report": {
    "ok": true,
    "reasons": [],
    "pf_ok": true,
    "pf_converged": true,
    "tds_initialized": true,
    "tds_test_ok": true,
    "residual_f_inf": 4.440892098500626e-16,
    "residual_g_inf": 4.258316810279439e-09,
    "finite": true,
    "tol": 1e-08
   },
   "I_vs_executor": 0.0,
   "k_ip": 57.4141002046974,
   "Vmin": 1.0018486135002262,
   "Vmax": 1.0730242986373122,
   "P_slack": 5.734106412604436,
   "Q_slack": -0.2936118439272639
  }
 },
 "invalid_candidates": {
  "SG31_p0_above_pmax": {
   "ok": false,
   "reason": "INIT_MAP_ERROR",
   "detail": "InitError('Nominal setpoint is not in the interior of W_i')"
  },
  "v0_all_0.3": {
   "ok": false,
   "reason": "INIT_INVALID",
   "detail": "{'ok': False, 'reasons': ['PFlow.run() returned False', 'PFlow.converged is False', 'TDS.initialized is False', 'TDS.test_ok is None', '|f|_inf = nan exceeds 1.0e-08', '|g|_inf = 6.650e+02 exceeds 1.0e-08'], 'pf_ok': False, 'pf_converged': False, 'tds_initialized': False, 'tds_test_ok': None, 'resid"
  }
 },
 "seconds_per_evaluate_mean": 0.18995261192321777
}
```
### C04_RDC_initialisation_matches_executor — PASS
```
{
 "I_vs_executor_max_diff": {
  "z_ref": 0.0,
  "SG35-0.30_GFM34+0.30": 0.0,
  "v0-0.01": 0.0,
  "SG31-0.10_SG38+0.10": 0.0
 },
 "k_ip_zref": 57.21380351909574,
 "k_ip_E8_stored": 57.21380351909574,
 "pn_vs_E8_max_diff": 0.0,
 "qn_vs_E8_max_diff": 0.0,
 "gref_p": 17.569319798466488,
 "gref_q": 0.8893657837446092,
 "d_p": [
  0.2293123643380886,
  0.1547987620891603,
  0.15337423359930744,
  0.14556040799289782,
  0.13075597938496522,
  0.17448644403122204,
  0.13793103486325803,
  0.31102134813833104,
  0.19685039447578895,
  0.1724137936979786
 ],
 "d_q": [
  0.47334141169342625,
  0.18100563108518308,
  0.13123566250387145,
  0.12066219412133791,
  0.08391627170074786,
  0.13367000351552108,
  0.15950489680033178,
  0.1516093330705438,
  0.12507457571577052,
  0.12232356049634009
 ],
 "d_q_independent_of_dispatch": true,
 "k_ip_by_candidate": {
  "z_ref": 57.21380351909574,
  "SG35-0.30_GFM34+0.30": 57.24815271729646,
  "v0-0.01": 54.26439317652364,
  "SG31-0.10_SG38+0.10": 57.4141002046974
 }
}
```
### C05_AC_balance_and_slack — PASS
```
{
 "residual_g_inf": {
  "z_ref": 4.215672255725167e-09,
  "SG35-0.30_GFM34+0.30": 4.223858596219543e-09,
  "v0-0.01": 1.7819576925148795e-09,
  "SG31-0.10_SG38+0.10": 4.258316810279439e-09
 },
 "residual_f_inf": {
  "z_ref": 2.220446049250313e-16,
  "SG35-0.30_GFM34+0.30": 4.440892098500626e-16,
  "v0-0.01": 2.7842311789427754e-16,
  "SG31-0.10_SG38+0.10": 4.440892098500626e-16
 },
 "slack_P_Q": {
  "z_ref": [
   5.731104244528378,
   -0.2962704801493684
  ],
  "SG35-0.30_GFM34+0.30": [
   5.732890030647369,
   -0.29699004082156644
  ],
  "v0-0.01": [
   5.739155028421013,
   -0.1898958711769133
  ],
  "SG31-0.10_SG38+0.10": [
   5.734106412604436,
   -0.2936118439272639
  ]
 },
 "note": "nodal P/Q balance is the algebraic residual g (incl. losses); the Slack closes the active balance"
}
```
### C06_DESIGN_jumps_and_algebraic_Jacobian — PASS
```
{
 "buses": [
  8,
  23,
  28,
  25
 ],
 "scenarios": 16,
 "min_gy_sv": 0.0020993355832745653,
 "max_cond": 562741.4632328204,
 "max_jump_residual": 2.6290081223123707e-13,
 "nonlinearity_max_abs_dP_1x_minus_2x_half": 0.00021115445521413534,
 "note": "only DESIGN buses were used; TUNE/TEST buses were not touched"
}
```
### C07_post_jump_anchoring_no_double_count — PASS
```
{
 "max_anchor_diff": 0.0,
 "max_D0": 0.0,
 "reading": "the affine model is built at the post-jump point (x and references continuous, algebraic re-solved); P(xi_0)=pn+jump to <=1e-8 and D(0+)=0 exactly"
}
```
### C08_PSS_12_genuine_states_and_reduced_structure — PASS
```
{
 "n_dynamic": 208,
 "n_quasi_algebraic": 12,
 "n_dropped_IEEEST_states": 30,
 "M_shape": [
  228,
  228
 ],
 "n_reference_states": 20,
 "pss_states_per_SG": 2,
 "n_SG": 6,
 "genuine_PSS_states": 12,
 "pss_state_names": [
  "LL2_x IEEEST 1",
  "LL2_x IEEEST 2",
  "LL2_x IEEEST 4",
  "LL2_x IEEEST 6",
  "LL2_x IEEEST 9",
  "LL2_x IEEEST 10",
  "WO_x IEEEST 1",
  "WO_x IEEEST 2",
  "WO_x IEEEST 4",
  "WO_x IEEEST 6",
  "WO_x IEEEST 9",
  "WO_x IEEEST 10"
 ],
 "n_x": 220,
 "n_y": 444
}
```
### C09_event_callback_algebraic_order_at_t5 — PASS
```
{
 "andes_version": "2.0.0",
 "code_order_in_TDS_run": "callpert(t) -> itm_step() -> store -> do_switch() (events are applied AFTER the step of the event time is solved and stored)",
 "stored_times_around_event_s": [
  4.99609375,
  4.9999,
  5.0,
  5.0001,
  5.00400625,
  5.0079125,
  5.01181875
 ],
 "first_post_event_stored_sample_s": 5.0001,
 "first_sample_with_electrical_change_s": 5.0001,
 "first_RDC_reference_change_s": 5.00400625,
 "reading": "ANDES shortens the step around the event (stored times ..., 4.9999, 5.0, 5.0001, then 5.0001+k*2^-8): the algebraic jump is visible at the first stored sample t_e+1e-4 s (proxy of 0+), the RDC references first change at t_e+1e-4+2^-8 s. The RDC callback uses a constant dt=2^-8 s in its Euler update even for the 1e-4 s steps (run_e8_ieee39.py:171-173) and sees the event in its measurements one callback after the jump. These effects are neglected by the continuous-time predictor and are bounded in the G3 audit."
}
```
### C10_horizon_5_to_200s — PASS
```
{
 "event_s": 5.0,
 "end_s": 200.0,
 "post_event_horizon_s": 195.0,
 "grid_last_s": 195.0,
 "first_step_s": 0.00390625,
 "grid_points": 807
}
```
