"""DEC-050 block C analysis (post-processing only, no simulation): C3 local stability around verified equilibria, C4 benefit of the preventive reserve, C5 classification of what is
numerical, what is locally demonstrable and what is not available.

C3.  Admissible linearisation points (declared): (i) the 2000 s post-event state of block A (drift max|v0| 4.6e-6 pu/s < 5e-5, remaining displacement < 2e-3 pu; criterion of
analyse_dec050_a.py); (ii) the pre-event state of the B3-S0 reference, which is an equilibrium of the centered RDC (invariance residual ~1e-8, DEC-039) and has the same Jacobian as B2 (the offset is a constant).
E13's post-event points at t = 199 s are NOT admissible: the RDC rates there are 4e-4 pu/s (> 5e-5) and the remaining displacement is 0.17 pu.  The common rotor-angle shift is the only marginal
direction (checked on the null vector); the claim is local exponential stability of the linearisation on the quotient by that shift, built from the frozen-Jacobian model of e9a_linear (index-1
elimination of the algebraic and quasi-algebraic variables, degenerate IEEEST states excluded).  It is not a statement about the full nonlinear DAE beyond Lyapunov's indirect method, saturations or regions.
C4.  Benefit of the preventive reserve from available runs only (E5t, E8, E9-B0, E11, DEC-050 C): P+ margins of SG31 and SG35 and the largest tolerated dynamic P step.
"""

from __future__ import annotations

import json
import os

os.environ["C2_VARIANT"] = "C2t"

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import run_e11_limits as E11  # noqa: E402
from run_e0_ieee39 import ARTIFACTS_DIR as A, FIGURES_DIR, git_commit, sha256  # noqa: E402


def main() -> int:
    a = json.loads((A / "IEEE39_DEC050_A_summary.json").read_text(encoding="utf-8"))
    pr = np.load(A / "IEEE39_DEC050_A_longrun_Qplus_probes.npz")
    e13 = json.loads((A / "IEEE39_E13_stability.json").read_text(encoding="utf-8"))["points"]
    cdyn = json.loads((A / "IEEE39_DEC050_C_dynamic.json").read_text(encoding="utf-8"))
    cstat = json.loads((A / "IEEE39_DEC050_C1_static.json").read_text(encoding="utf-8"))
    ramp = json.loads((A / "IEEE39_DEC050_C_ramp_diagnostic.json").read_text(encoding="utf-8"))
    e11 = json.loads((A / "IEEE39_E11_summary.json").read_text(encoding="utf-8"))["runs"]
    lim = E11.limits()
    out: dict = {"stage": "DEC-050 C analysis", "git_commit": git_commit(), "doc": __doc__}
    # ---------------- C3
    M = pr["t1999_M"]
    u, s, vt = np.linalg.svd(M)
    nv = vt[-1]
    big = np.abs(nv) > 1e-3 * np.abs(nv).max()
    c3 = {"admissible_points": {}, "inadmissible_points": {}}
    mod = a["modal_at_verified_equilibrium"]
    c3["admissible_points"]["R35_040 Q+ post-event, t = 1999 s (B2 original RDC)"] = {
        "drift_max_abs_v0_pu_per_s": a["newton"]["t1999"]["v0_inf_pu_per_s"], "remaining_ref_displacement_pu": a["newton"]["t1999"]["remaining_ref_displacement_inf_pu"],
        "closed_loop": {k: mod["closed_loop_with_RDC"][k] for k in ("n_states", "n_unstable_Re_gt_1e-6", "n_marginal", "spectral_abscissa_stable_part", "min_zeta_oscillatory", "least_damped", "slowest_modes", "lyapunov")},
        "plant_frozen_references": {k: mod["plant_frozen_references"][k] for k in ("n_states", "n_unstable_Re_gt_1e-6", "n_marginal", "spectral_abscissa_stable_part", "min_zeta_oscillatory", "lyapunov")},
        "marginal_mode_check": {"smallest_singular_value": float(s[-1]), "second_smallest": float(s[-2]), "n_entries_above_1e-3_of_max": int(big.sum()), "relative_spread_of_those_entries": float(np.std(np.abs(nv[big])) / np.mean(np.abs(nv[big]))),
                                "interpretation": "single null direction supported on a few equal-magnitude entries = common rotor-angle shift (the DAE is invariant to it); state ordering inferred from structure"},
        "valid_for": "approximate equilibrium within the stated tolerances; local exponential stability of the linearisation on the quotient by the angle shift; Lyapunov function V = x^T P x with a very weak guaranteed decay rate (see lyapunov.V_decay_rate_lower_bound_per_s)"}
    for name in ("C2t_Vsafe_R35_040 S0 equilibrium (t=4.9 s)", "C2t historical S0 equilibrium (t=4.9 s)"):
        p = e13[name]
        c3["admissible_points"][f"{name} - equilibrium of the CENTERED RDC (B3-S0 invariance); not an equilibrium of the original B2 law (v_nom != 0 at S0)"] = {
            "closed_loop": {k: p["closed_loop_with_RDC"][k] for k in ("n_unstable_Re_gt_1e-6", "n_marginal", "min_zeta_oscillatory", "slowest_modes")}, "plant_frozen_references": {k: p["plant_frozen_references"][k] for k in ("n_unstable_Re_gt_1e-6", "n_marginal", "min_zeta_oscillatory")}}
    for name in ("R35_040 post-event P+ (t=199 s)", "R35_040 post-event Q+ (t=199 s)"):
        c3["inadmissible_points"][name] = "drifting state (max|v0| ~ 4e-4 pu/s at 199 s); E13's stability statement for this point is withdrawn as a claim; it is a modal diagnostic of a transient state"
    out["C3"] = c3
    # ---------------- C4
    names = ["SG30", "SG31", "SG33", "SG35", "SG38", "SG39", "GFM32", "GFM37", "GFM34", "GFM36"]
    rng = lim["pmax"] - lim["pmin"]
    sg31, sg35 = names.index("SG31"), names.index("SG35")
    v = json.loads((A / "IEEE39_E9B0_variant.json").read_text(encoding="utf-8"))["scenarios"]["P+"]
    r = json.loads((A / "IEEE39_E9B0_variant_R35_040.json").read_text(encoding="utf-8"))["scenarios"]["P+"]
    rows = {
        "C2t (E8 B2, historical)": {"SG31_min_P_margin_pu": e11["E8_B2 P+"]["min_normalised_margin_by_unit"]["SG31"] * rng[sg31], "SG35_min_P_margin_pu": e11["E8_B2 P+"]["min_normalised_margin_by_unit"]["SG35"] * rng[sg35],
                                   "pre_event_headroom_SG31_pu": e11["E8_B2 P+"]["pre_event_headroom_pu"]["SG31"], "pre_event_headroom_SG35_pu": e11["E8_B2 P+"]["pre_event_headroom_pu"]["SG35"], "crossing_at_58.5MW": ["SG31"]},
        "C2t_Vsafe (SG31 reserve)": {"SG31_min_P_margin_pu": v["per_unit"]["SG31"]["min_P_margin_to_pmax_pu"], "SG35_min_P_margin_pu": v["per_unit"]["SG35"]["min_P_margin_to_pmax_pu"], "crossing_at_58.5MW": v["violating_units"]},
        "C2t_Vsafe_R35_040 (SG31 + SG35 reserve)": {"SG31_min_P_margin_pu": r["per_unit"]["SG31"]["min_P_margin_to_pmax_pu"], "SG35_min_P_margin_pu": r["per_unit"]["SG35"]["min_P_margin_to_pmax_pu"], "crossing_at_58.5MW": r["violating_units"]}}
    ok_p = [x["amplitude"] for x in cdyn["P"] if not x["violating_units"] and not x["tds_failed"]]
    bad_p = [x["amplitude"] for x in cdyn["P"] if x["violating_units"] or x["tds_failed"]]
    e12 = json.loads((A / "IEEE39_E12_frontier.json").read_text(encoding="utf-8"))["dynamic_runs"]
    ok_all = sorted([x["amplitude"] for x in e12 if x["kind"] == "P" and not x["violating_units"] and not x["tds_failed"]] + ok_p)
    bad_all = sorted([x["amplitude"] for x in e12 if x["kind"] == "P" and (x["violating_units"] or x["tds_failed"])] + bad_p)
    lo, hi = max(ok_all), min(bad_all)
    c4 = {"p_plus_margins": rows, "dynamic_P_step_frontier_R35_040_MW": [lo, hi], "C2t_original_dynamic_P_step": "violates SG31 already at 58.564 MW (E5t, E8, B3) - tolerated amplitude < 58.564 MW (not bracketed: no further simulation)",
          "tolerated_amplitude_gain_lower_bound_MW": lo - 58.564 if lo > 58.564 else 0.0,
          "static_fixed_share_ceiling_MW": {k: v["frontier_amplitude_MW"] for k, v in cstat["cases"].items()},
          "reading": "the reserve changes the TRANSIENT margins (the 0.07 pu electrical jump of SG31 no longer crosses pmax; SG35 no longer crosses at 58.5 MW) and the dynamic frontier; the static end-state ceiling is nearly the same "
                     "(~104-107 MW with physical limits) because it is set by total capacity, not by the transient"}
    out["C4"] = c4
    # ---------------- C1 summary, C2 summary
    qlo = max([x["amplitude"] for x in e12 if x["kind"] == "Q" and not x["tds_failed"] and not x["violating_units"] and x["n_buses_outside_band"] == 0] + [x["amplitude"] for x in cdyn["Q"] if not x["tds_failed"] and not x["violating_units"] and x["n_buses_outside_band"] == 0])
    qhi = min(x["amplitude"] for x in cdyn["Q"] + [y for y in e12 if y["kind"] == "Q"] if (x["tds_failed"] or x["violating_units"] or x["n_buses_outside_band"] > 0))
    out["C1"] = {"P_dynamic_frontier_R35_040_MW_between": [lo, hi], "Q_dynamic_frontier_voltage_band_MVAr_between": [qlo, qhi], "Q_unit_limit_crossings_up_to_MVAr": max(x["amplitude"] for x in cdyn["Q"] if not x["violating_units"]),
                 "Q_step_failure_E12_138MVAr": {"step": "TDS failure at 5.2 s, residual 238", "same_amplitude_as_5s_ramp": {k: ramp[k] for k in ("tds_failed", "violating_units", "n_buses_outside_band", "bus_voltage_min_pu")}},
                 "static_dispatch_conditioned_ceilings": {k: {"MW": v["frontier_amplitude_MW"], "first_infeasible_binding": v["first_infeasible_binding"]} for k, v in cstat["cases"].items()},
                 "E12_correction": "E12 static P frontier (117 MW) is dispatch-independent (free redispatch with 1 % interior margins) and is a ceiling for any redispatch; with physical limits and the observed RDC sharing the end-state "
                                   "ceiling is 104-107 MW, and the dynamic step frontier is 66-73 MW (transient overshoot).  E12's Q 'collapse' at 138.6 MVAr was a step-integration failure: the same amplitude as a 5 s ramp respects all limits and the band."}
    out["C2"] = {"delay_tolerance": {str(x["delay_s"]): {"tds_ok": x["tds_ok"], "n_buses_outside_band": x["n_buses_outside_band"], "bus_voltage_min_max_pu": [x["bus_voltage_min_pu"], x["bus_voltage_max_pu"]], "units_crossing_limits": x["units_crossing_limits"],
                                                       "frequency_oscillation_last_20s_hz": x["frequency_oscillation_last_20s_hz"]} for x in cdyn["delay"]}, "from_E15": "0.2 s ok; 1.0 s limits and band violated; 5 s TDS failure"}
    # ---------------- C5 classification
    out["C5"] = {
        "numerical_results": ["2000 s run: references converge toward an equilibrium (max|v0| 4.1e-4 -> 4.6e-6 pu/s); Newton estimates from 199/500/1000 s approach the final state (0.17 -> 0.02 pu of Qset)",
                              "B2_QV1 drift reduction 3-5 % in the max-drift metric; mean unit-voltage error 12-18 % lower; no new crossings (negative by the declared criterion)",
                              "dynamic P step frontier 66-73 MW; Q band frontier 69-87 MVAr; delay: 0.5 s ok, 0.75 s degraded, 1.0 s limits, 5 s TDS failure"],
        "locally_demonstrable": ["linearisation of the plant+RDC loop has no unstable eigenvalue at the 2000 s post-event state and at the S0 equilibrium of the centered RDC; single marginal rotor-angle direction (local exponential stability on the quotient)",
                                 "a verified equilibrium of the original B2 law exists for Q+ on R35_040 (numerically, within tolerances); unit voltages at it deviate from 1 pu by up to 8.3e-3 pu (mean 3.2e-3) - a steady-state offset set by the Q-consensus term"],
        "not_available": ["any closed-loop safety guarantee (no HOCBF/CLF-HOCBF filter in the loop, Option B)", "regional stability / region of attraction", "global or nonlinear stability beyond Lyapunov's indirect method",
                          "real-time capability", "robustness outside the tested cases (inertia, loads, delays, one N-1)", "extension to grid-following resources", "convergence to V = 1 pu: the equilibrium itself has a voltage offset"]}
    (A / "IEEE39_DEC050_C_summary.json").write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
    # ---------------- figure
    fig, ax = plt.subplots(1, 3, figsize=(20, 6))
    ev = np.linalg.eigvals(M)
    ax[0].scatter(ev.real, ev.imag, s=10, color="tab:blue"); ax[0].set_xscale("symlog", linthresh=1e-2); ax[0].axvline(0, color="k", lw=.6)
    ax[0].set_title("eigenvalues of plant+RDC at the 2000 s state (all Re <= 0; 1 marginal = angle shift)"); ax[0].set_xlabel("Re"); ax[0].set_ylabel("Im")
    x = np.arange(3)
    ax[1].bar(x - 0.2, [rows[k]["SG31_min_P_margin_pu"] for k in rows], 0.4, label="SG31"); ax[1].bar(x + 0.2, [rows[k]["SG35_min_P_margin_pu"] for k in rows], 0.4, label="SG35")
    ax[1].axhline(0, color="k", lw=.8); ax[1].set_xticks(x); ax[1].set_xticklabels(["C2t", "C2t_Vsafe", "R35_040"]); ax[1].set_title("min P margin to pmax at P+ 58.5 MW [pu] (negative = crossing)"); ax[1].legend()
    ax[2].barh(["C2t (<58.5)", "R35_040 dyn. step", "static end-state ceiling (shared)", "static ceiling free redispatch (E12)"], [58.564, hi, max(c["frontier_amplitude_MW"] for c in cstat["cases"].values()), 117.0], color=["tab:red", "tab:orange", "tab:gray", "lightgray"])
    ax[2].axvspan(lo, hi, color="tab:green", alpha=.2); ax[2].set_title("P-step amplitude [MW]: dynamic frontier band (green) vs static ceilings")
    for a in ax:
        a.grid(alpha=.25)
    fig.suptitle("DEC-050 C: local modal analysis at a verified equilibrium, benefit of the preventive reserve, dynamic vs static P frontier"); fig.tight_layout()
    fig.savefig(FIGURES_DIR / "IEEE39_DEC050_C_analysis.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    print(json.dumps({k: out[k] for k in ("C1", "C4", "C2")}, indent=1, default=float)[:4500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
