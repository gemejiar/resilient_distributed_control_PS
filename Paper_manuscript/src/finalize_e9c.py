"""E9-C/E9-D: consolidate Phases 1-3 (variant C2t_Vsafe_R35_040, amplitude search, Lie-derivative validation) and the shadow-mode filter test (no simulation)."""

from __future__ import annotations

import csv
import json
import os
import platform

os.environ["C2_VARIANT"] = "C2t"

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from run_e0_ieee39 import ARTIFACTS_DIR as A, FIGURES_DIR, MATRIX_FILE, PROJECT_ROOT, git_commit, sha256

SRC = PROJECT_ROOT / "Paper_manuscript" / "src"
T = "_R35_040"
EVENT = 5.0
SG35_MIN_MARGIN_PU = 0.020      # required by the investigator for P+ (Phase 1, item 4)


def main() -> int:
    v0 = json.loads((A / "IEEE39_E9B0_variant.json").read_text(encoding="utf-8"))
    v1 = json.loads((A / "IEEE39_E9B0_variant_R35.json").read_text(encoding="utf-8"))
    v2 = json.loads((A / f"IEEE39_E9B0_variant{T}.json").read_text(encoding="utf-8"))
    amp = json.loads((A / f"IEEE39_E9C_amplitude_search{T}.json").read_text(encoding="utf-8"))
    lie = json.loads((A / f"IEEE39_E9C_lie_validation{T}.json").read_text(encoding="utf-8"))
    shadow = json.loads((A / f"IEEE39_E9D_shadow{T}.json").read_text(encoding="utf-8"))
    ic = v2["initial_condition"]
    units = ic["units"]
    cols = sorted({k for u in units for k in u}, key=lambda k: (k != "unit", k != "bus", k))
    with (A / f"IEEE39_E9B0_initial_condition{T}_units.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(units)
    with (A / f"IEEE39_E9B0_initial_condition{T}_buses.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["bus", "V_pu", "angle_rad", "in_band"]); w.writeheader(); w.writerows(ic["bus_voltages_39"])
    names = [u["unit"] for u in units]
    # margins table across the three variants
    table = []
    for label, v in (("C2t_Vsafe", v0), ("C2t_Vsafe_R35 (delta 0.015)", v1), ("C2t_Vsafe_R35_040 (delta 0.040)", v2)):
        for sc, m in v["scenarios"].items():
            for n in names:
                r = m["per_unit"][n]
                table.append({"variant": label, "scenario": sc, "unit": n, "max_P_pu": r["max_P_pu"], "min_P_margin_to_pmax_pu": r["min_P_margin_to_pmax_pu"], "min_Q_margin_to_qmax_pu": r["min_Q_margin_to_qmax_pu"],
                              "min_Q_margin_to_qmin_pu": r["min_Q_margin_to_qmin_pu"], "min_S_rel_margin": r["min_S_rel_margin"], "P_violation_pu": r["P_violation_pu"], "Q_violation_pu": r["Q_violation_pu"],
                              "S_violation_pu": r["S_violation_pu"]})
    with (A / "IEEE39_E9C_margins_all_variants.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0])); w.writeheader(); w.writerows(table)
    sg35 = v2["scenarios"]["P+"]["per_unit"]["SG35"]["min_P_margin_to_pmax_pu"]
    phase1 = {"variant": v2["variant"], "delta_pu": v2["incremental_redispatch_delta_pu"], "SG35_min_margin_P+_pu": sg35, "required_pu": SG35_MIN_MARGIN_PU, "SG35_requirement_met": bool(sg35 >= SG35_MIN_MARGIN_PU),
              "violating_units": {sc: m["violating_units"] for sc, m in v2["scenarios"].items()},
              "bus_voltage": {sc: m["bus_voltage"] for sc, m in v2["scenarios"].items()}, "AC_DAE": {k: ic[k] for k in ("pflow_residual", "init_max_abs_f", "init_max_abs_g", "power_balance", "bus_voltage_min_pu", "bus_voltage_max_pu", "n_buses_outside_band")},
              "flat_run_20s": v2["flat_run"], "frozen_reference_variants_untouched": ["C2t_Vsafe", "C2t_Vsafe_R35"],
              "min_P_margin_by_unit_P+": {n: v2["scenarios"]["P+"]["per_unit"][n]["min_P_margin_to_pmax_pu"] for n in names},
              "all_checks_pass": bool(sg35 >= SG35_MIN_MARGIN_PU and not any(m["violating_units"] for m in v2["scenarios"].values())
                                      and all(m["bus_voltage"]["n_buses_ever_outside_band"] == 0 for m in v2["scenarios"].values()) and ic["n_buses_outside_band"] == 0)}
    # phase 2 table
    rows2 = []
    for fam, f in amp["families"].items():
        for r in f["runs"]:
            pr = [p for p in r["probes"] if p["t_after_event_s"] > 0.002]

            def first_ok(cond):
                for i, p in enumerate(pr):
                    if all(cond(q) for q in pr[i:]):
                        return p["t_after_event_s"]
                return None
            rows2.append({"family": fam, "fraction": r["fraction"], "amplitude": r["amplitude"], "unit": r["unit"], **{k: v for k, v in r["criteria"].items()}, "meets_all": r["meets_all"],
                          "barriers_outside_CH_first_post_jump": r["first_post_jump"]["barriers_outside_CH"], "worst_psi_first_post_jump": r["first_post_jump"]["worst_psi"][0][1],
                          "CH_recovered_from_s": first_ok(lambda p: p["n_outside_CH"] == 0 and not p["h_negative"]), "QP_feasible_from_s": first_ok(lambda p: p["qp_feasible"]),
                          "nominal_satisfies_constraints_from_s": first_ok(lambda p: p["nominal_satisfies_all"]), "QP_inactive_at_all_probes": r["QP_inactive_at_all_probes"],
                          "min_P_margin_pu_B2": min(r["min_P_margin_pu"].values()), "B2_violating_units": ";".join(r["violating_units"])})
    with (A / f"IEEE39_E9C_amplitude_search{T}.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows2[0])); w.writeheader(); w.writerows(rows2)
    # phase 3 summary
    cases = []
    for c in lie["cases"]:
        cases.append({"scenario": c["scenario"], "t0_s": c["t0_s"], "membership": c["membership"], "gate_S0_criteria": c["gate_S0_criteria"],
                      "median_rel_err_by_order_frozen_all_kinds": {f"order_{k}": float(np.median([c["per_kind"][kd][f"order_{k}"]["median_rel_err_frozen"] for kd in c["per_kind"]])) for k in (1, 2, 3, 4)},
                      "S_curvature_effect_order2_median_rel_err": {"gradient_only": c["per_kind"]["S"]["order_2"]["median_rel_err_frozen"], "with_curvature": c["per_kind"]["S"]["order_2"]["median_rel_err_curv"]},
                      "output_derivatives": c["outputs"], "decoupling_ramp_rel_err": {n: {t: x["rel_err_norm"] for t, x in r.items()} for n, r in c["decoupling_ramp_test"].items()},
                      "cost_s": c["cost_s"], "scaling": {k: v for k, v in c["scaling"].items() if k != "decoupling_matrix_singular_values_normalized_rows"}})
    gate_s0 = all(c["gate_S0_criteria"]["both"] for c in lie["cases"] if c["scenario"] == "S0")
    # shadow figure
    fig, ax = plt.subplots(1, 3, figsize=(18, 5))
    h = shadow["activation_time_histogram_10s_bins"]
    ax[0].bar(np.arange(len(h)) * 10 + 5, h, width=9); ax[0].set_title(f"S0 shadow: steps where the nominal B2 command would violate a constraint\n({shadow['n_would_activate_qp']} of {shadow['n_steps']}, {100 * shadow['fraction_active']:.2f} %)")
    ax[0].set_xlabel("Time [s]"); ax[0].set_ylabel("steps per 10 s")
    vc = shadow["violated_constraint_counts_top"][:8]
    ax[1].barh([x[0] for x in vc][::-1], [x[1] for x in vc][::-1]); ax[1].set_title("most frequently violated constraints (P+8 = GFM34 pmax barrier, margin 0.43 pu)")
    cs = shadow["cost_s"]
    keys = ["step_median", "step_p95", "step_p99", "qp_mean", "refresh_mean"]
    ax[2].bar(keys, [cs[k] * 1e3 for k in keys]); ax[2].axhline(cs["control_period_s"] * 1e3, color="r", ls="--", label="control period 3.906 ms"); ax[2].set_yscale("log")
    ax[2].set_title("cost per control step [ms]"); ax[2].legend()
    for a in ax:
        a.grid(alpha=.25)
    fig.suptitle(f"E9-D: per-step HOCBF-QP filter in shadow mode on S0 ({v2['variant']}); output discarded, trajectory = B2"); fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"IEEE39_E9D_shadow{T}.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    status = "FINDINGS_WAIT_HUMAN"
    figs = {"margins": f"Paper_manuscript/figures_main/IEEE39_E9B0_margins{T}.png", "amplitude_search": f"Paper_manuscript/figures_main/IEEE39_E9C_amplitude_search{T}.png",
            "lie_validation": f"Paper_manuscript/figures_main/IEEE39_E9C_lie_validation{T}.png", "shadow_S0": f"Paper_manuscript/figures_main/IEEE39_E9D_shadow{T}.png"}
    summary = {"stage": "E9-C/E9-D", "status_auto": status, "status_human": "PENDING", "git_commit": git_commit(), "python": platform.python_version(),
               "phase1_variant": phase1,
               "phase2_amplitude_search": {"criteria": "C1-C4 declared in run_e9c_amplitudes.py before running", "horizon_s": amp["horizon_s"], "fractions": amp["fractions"],
                                           "selected": {fam: f["selected_fraction"] for fam, f in amp["families"].items()}, "interpretation": {fam: f["interpretation"] for fam, f in amp["families"].items()},
                                           "table": f"IEEE39_E9C_amplitude_search{T}.csv",
                                           "finding": "worst psi right after the jump scales with the amplitude (S barrier: -7e3 at 0.5 % to -1.6e6 at 100 % in P+); the number of barriers outside C_H is almost amplitude independent (64-75 in P+, 62-80 in Q+). A relative-degree-3 set with lambda = 2 s^-1 cannot contain a state immediately after an algebraic step of the load for any practical amplitude; C_H and the QP recover 0.25-2 s after the event",
                                           "post_transient_information_not_a_selection": [{k: r[k] for k in ("family", "fraction", "CH_recovered_from_s", "QP_feasible_from_s", "nominal_satisfies_constraints_from_s")} for r in rows2]},
               "phase3_lie_validation": {"cases": cases, "gate_S0": {"criteria": "declared in run_e9c_lie_validation.py: (i) frozen and true psi_k same sign and positive for all barriers; (ii) frozen h^(1..3) consistent with the truth within 3 fit uncertainties or below 1e-3 of the margin scale",
                                                                        "met_at_all_S0_probes": bool(gate_s0)},
                                         "structural_findings": ["decoupling matrix of the relative-degree-3 constraints has rank 8 (the four GFM Pset and four GFM Qset channels); SG channels enter at order 4 only, so the r = 3 HOCBF cannot use the SG references (SG31 own channel has the largest authority over P31)",
                                                                 "row norms of the constraint matrix span 0.03 to 2.7e4 (ratio about 8e5)"]},
               "phase4_shadow_S0": {k: shadow[k] for k in ("mode", "n_steps", "n_nominal_feasible", "n_would_activate_qp", "fraction_active", "n_qp_infeasible", "violated_constraint_counts_top", "activation_time_histogram_10s_bins",
                                                          "equivalence_check_vs_evaluate", "cost_s", "real_time_statement")},
               "closed_loop_S0_executed": False,
               "closed_loop_S0_reason": "the Phase 3 gate declared before running is not met at the S0 probes (frozen order-3 derivatives are not consistent with the nonlinear truth), and in shadow mode the filter would act in 1.3 % of the S0 steps (2 infeasible), mainly through the pmax barrier of GFM34 which has 0.43 pu of margin: spurious activations from the derivative terms; the investigator's condition 'after passing the previous verifications' is not satisfied",
               "figures": figs, "tables": ["IEEE39_E9B0_initial_condition_R35_040_units.csv", "IEEE39_E9B0_initial_condition_R35_040_buses.csv", "IEEE39_E9C_margins_all_variants.csv", f"IEEE39_E9C_amplitude_search{T}.csv"],
               "raw_sha256": {f: sha256(A / f) for f in ("IEEE39_E9B0_Vsafe_series.npz", "IEEE39_E9B0_Vsafe_R35_series.npz", f"IEEE39_E9B0_Vsafe{T}_series.npz")},
               "artifacts_sha256": {f.name: sha256(f) for f in sorted(A.glob("IEEE39_E9C*")) if f.name != "IEEE39_E9C_summary.json"} | {f"IEEE39_E9D_shadow{T}.json": sha256(A / f"IEEE39_E9D_shadow{T}.json")},
               "code_sha256": {f: sha256(SRC / f) for f in ("e9b_variant.py", "e9b_tools.py", "e9d_filter.py", "run_e9b0_variant.py", "run_e9c_amplitudes.py", "run_e9c_lie_validation.py", "run_e9d_shadow.py", "finalize_e9c.py", "run_b3_ieee39.py")},
               "open": ["OPEN-SG31-PMAX open for the original C2t", "no perturbation frozen for the B2-versus-filter comparison", "E9-B2 closed loop not executed; P+/Q+ with QP not executed; E10-E15 and weight sensitivity not run",
                        "no certificate: frozen-Jacobian derivatives, assumed rate envelope, sampled controller not validated, no real-time capability demonstrated"]}
    (A / "IEEE39_E9C_summary.json").write_text(json.dumps(summary, indent=2, default=float), encoding="utf-8")
    with MATRIX_FILE.open("r", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames or [])
        rows = [r for r in reader if r.get("stage") not in ("E9C1", "E9C2", "E9C3", "E9D1")]
    new = []
    for stage, scen_txt, note in (("E9C1", "Vsafe_R35_040_B2_S0_P+_Q+", "variant C2t_Vsafe_R35_040 validated: SG35 margin P+ %.4f pu (>= 0.020), no violations (DEC-045)." % sg35),
                                  ("E9C2", "amplitude_search_P+_Q+_0.5-100pct", "no fraction meets the declared criteria; no perturbation frozen (DEC-045)."),
                                  ("E9C3", "lie_validation_S0_P+", "frozen-Jacobian derivatives of order >= 2 not reliable; decoupling errors 7-14 % at 0.1 s; gate not met (DEC-045)."),
                                  ("E9D1", "shadow_filter_S0", "shadow mode: 1.3 % of the S0 steps would activate the QP; closed-loop S0 not executed (DEC-045).")):
        row = {k: "" for k in fields}
        row.update({"run_id": f"{stage}_Vsafe_R35_040", "stage": stage, "case": "C2t_Vsafe_R35_040 (initial-condition variant of C2t)", "scenario": scen_txt, "baseline": "E8_C2t_B2", "git_commit": git_commit(),
                    "simulation_tf": 200.0 if stage in ("E9C1", "E9D1") else 30.0, "event_time": 5.0, "status_auto": status, "status_human": "PENDING", "frequency_figure": figs["margins"],
                    "voltage_figure": figs["amplitude_search"], "raw_file": f"Paper_manuscript/artifacts/IEEE39_E9B0_Vsafe{T}_series.npz", "decision_note": note})
        new.append(row)
    with MATRIX_FILE.open("w", newline="", encoding="utf-8") as stream:
        w = csv.DictWriter(stream, fieldnames=fields); w.writeheader(); w.writerows(rows + new)
    print(phase1["all_checks_pass"], sg35, amp["families"]["P+"]["selected_fraction"], amp["families"]["Q+"]["selected_fraction"], gate_s0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
