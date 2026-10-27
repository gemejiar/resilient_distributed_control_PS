"""E9-F: consolidate the nonlinear-consistent HOCBF reformulation results (engine validation, feasibility on S0 / steps / smooth ramps, cost) into tables, figures and one summary (no simulation)."""

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


def main() -> int:
    slow = json.loads((A / f"IEEE39_E9F_feasibility{T}_slow.json").read_text(encoding="utf-8"))
    raw = json.loads((A / f"IEEE39_E9F_feasibility{T}.json").read_text(encoding="utf-8"))
    val_s = json.loads((A / f"IEEE39_E9F_engine_validation_slow{T}.json").read_text(encoding="utf-8"))
    val_u = json.loads((A / f"IEEE39_E9F_engine_validation_unprojected{T}.json").read_text(encoding="utf-8"))
    cases = {}
    rows_csv = []
    for n, c in slow["cases"].items():
        pr = c["probes"]
        cases[n] = {"verdict": c["verdict"], "disturbance": c["disturbance"],
                    "protection_may_start_absolute_s": None if c["verdict"]["protection_may_start_at_s_after_event"] is None else EVENT + c["verdict"]["protection_may_start_at_s_after_event"],
                    "unsafe_interval_s": c["verdict"]["protection_may_start_at_s_after_event"],
                    "time_series": [{"t_after_event_s": p["t_s"] - EVENT, "n_outside_CH": p["C_H"]["n_outside"], "outside_by_kind": p["C_H"]["outside_by_kind"], "worst_psi": p["C_H"]["worst_psi"][:3],
                                     "authority_scale_min": p["audit"]["authority_scale_min"], "qp_feasible_slsqp": p["audit"]["qp"]["SLSQP"]["converged"], "qp_feasible_trust_constr": p["audit"]["qp"]["trust-constr"]["converged"],
                                     "nominal_satisfies_all": p["audit"]["nominal_satisfies_all"], "conflict_set_top": p["audit"]["conflict_set_top"][:3], "disturbance_pu": p["disturbance_value_pu"],
                                     "relative_degree_3": p["relative_degree_check"]["relative_degree_3_all_outputs"], "M0_max": p["relative_degree_check"]["M0_max"], "M1_max": p["relative_degree_check"]["M1_max"],
                                     "M2_min_row_max": p["relative_degree_check"]["M2_min_row_max"], "eps_consistency_rhs_median_rel": p["eps_consistency_rhs_median_rel"],
                                     "projection_state_shift": p["projection"]["max_abs_state_shift"] if p["projection"] else None, "cost_s": p["cost_s"]} for p in pr]}
        for p in pr:
            rows_csv.append({"case": n, "t_after_event_s": p["t_s"] - EVENT, "n_outside_CH": p["C_H"]["n_outside"], "authority_scale_min": p["audit"]["authority_scale_min"], "qp_feasible": p["audit"]["qp"]["SLSQP"]["converged"],
                             "nominal_satisfies_all": p["audit"]["nominal_satisfies_all"], "cost_total_s": p["cost_s"]["total"], "cost_linearize_s": p["cost_s"]["linearize"], "cost_jets_s": p["cost_s"]["exact_jets_two_eps_each"]})
    with (A / f"IEEE39_E9F_feasibility{T}_slow.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_csv[0])); w.writeheader(); w.writerows(rows_csv)
    unproj_S0 = [{"t_after_event_s": p["t_s"] - EVENT, "n_outside_CH": p["C_H"]["n_outside"], "authority_scale_min": p["audit"]["authority_scale_min"], "qp_feasible": p["audit"]["qp"]["SLSQP"]["converged"],
                  "conflict_detail": p.get("conflict_detail", [])[:1]} for p in raw["cases"]["S0"]["probes"]]
    # validation tables
    def vrow(v):
        return {k: {f"order_{o}": {"engine_vs_truth_median_rel": r[f"order_{o}"]["engine_vs_truth_median_rel"], "frozen_vs_truth_median_rel": r[f"order_{o}"]["frozen_vs_truth_median_rel"],
                                   "engine_vs_truth_max_abs": r[f"order_{o}"]["engine_vs_truth_max_abs"], "frozen_vs_truth_max_abs": r[f"order_{o}"]["frozen_vs_truth_max_abs"], "truth_abs_max": r[f"order_{o}"]["truth_abs_max"],
                                   "truth_fit_uncertainty_median": r[f"order_{o}"]["truth_fit_uncertainty_median"], "engine_eps_consistency_median_rel": r[f"order_{o}"]["engine_eps_consistency_median_rel"]} for o in (1, 2, 3)}
                | {"jets_time_s": r["jets_time_s"], "n_solves": r["n_solves"], "newton_residual": r["newton_residual"]} for k, r in v.items()}
    # figures
    fig, ax = plt.subplots(2, 3, figsize=(19, 9))
    for n, c in cases.items():
        t = [x["t_after_event_s"] for x in c["time_series"]]
        ax[0, 0].plot(t, [x["n_outside_CH"] for x in c["time_series"]], "o-", ms=3, label=n)
        ax[0, 1].plot(t, [int(x["qp_feasible_slsqp"] and x["qp_feasible_trust_constr"]) for x in c["time_series"]], "s-", ms=3, label=n)
        ax[0, 2].plot(t, [x["cost_s"]["total"] for x in c["time_series"]], "o-", ms=3, label=n)
    ax[0, 0].set_title("barriers outside C_H (of 128), slow-manifold nonlinear jets"); ax[0, 1].set_title("QP feasible (two solvers) with the eight GFM channels"); ax[0, 2].set_title("cost of one evaluation [s]")
    ax[0, 2].axhline(3.90625e-3, color="r", ls="--", label="control period"); ax[0, 2].set_yscale("log")
    for a in ax[0]:
        a.set_xscale("symlog", linthresh=0.01); a.grid(alpha=.25); a.legend(fontsize=7); a.set_xlabel("Time since event start [s]")
    keys = list(val_s)
    x = np.arange(len(keys))
    for o, col in zip((1, 2, 3), ("tab:blue", "tab:orange", "tab:green")):
        ax[1, 0].bar(x + 0.13 * (o - 2) * 2 - 0.0, [max(val_s[k][f"order_{o}"]["engine_vs_truth_median_rel"], 1e-4) for k in keys], 0.25, label=f"engine (projected) order {o}", color=col)
    ax[1, 0].set_yscale("log"); ax[1, 0].set_xticks(x); ax[1, 0].set_xticklabels(keys, fontsize=7); ax[1, 0].set_title("derivatives vs ANDES free-flow truth: engine on the slow manifold"); ax[1, 0].legend(fontsize=7)
    for o, col in zip((1, 2, 3), ("tab:blue", "tab:orange", "tab:green")):
        ax[1, 1].bar(x + 0.13 * (o - 2) * 2, [max(val_s[k][f"order_{o}"]["frozen_vs_truth_median_rel"], 1e-4) for k in keys], 0.25, label=f"frozen Jacobian order {o}", color=col)
    ax[1, 1].set_yscale("log"); ax[1, 1].set_xticks(x); ax[1, 1].set_xticklabels(keys, fontsize=7); ax[1, 1].set_title("same states: frozen Jacobian (E9-B1/E9-C formulation)"); ax[1, 1].legend(fontsize=7)
    ku = list(val_u)
    xu = np.arange(len(ku))
    for o, col in zip((1, 2, 3), ("tab:blue", "tab:orange", "tab:green")):
        ax[1, 2].bar(xu + 0.13 * (o - 2) * 2, [max(val_u[k][f"order_{o}"]["engine_vs_truth_median_rel"], 1e-4) for k in ku], 0.25, label=f"engine NOT projected order {o}", color=col)
    ax[1, 2].set_yscale("log"); ax[1, 2].set_xticks(xu); ax[1, 2].set_xticklabels(ku); ax[1, 2].set_title("engine without slow-manifold projection (noise-dominated)"); ax[1, 2].legend(fontsize=7)
    for a in ax[1]:
        a.grid(alpha=.25)
    fig.suptitle("E9-F: reformulated HOCBF conditions (nonlinear jets, eight GFM inputs) on C2t_Vsafe_R35_040: feasibility, cost and derivative validation"); fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"IEEE39_E9F_summary{T}.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    status = "FINDINGS_WAIT_HUMAN"
    s0_costs = [p["cost_s"] for p in slow["cases"]["S0"]["probes"]]
    summary = {"stage": "E9-F", "status_auto": status, "status_human": "PENDING", "git_commit": git_commit(), "python": platform.python_version(),
               "formulation": {"inputs": "eight GFM rate channels (Pset, Qset of GFM32, GFM37, GFM34, GFM36); SG references under the original RDC, entering the drift", "derivatives": "nested central directional differences along the flow of the nonlinear reduced DAE with exact algebraics (Newton 1e-13), exact Leibniz rule for the S barrier, disturbance clock in the state",
                               "slow_manifold_projection_lambda_c": 100.0, "lambda": 2.0, "relative_degree": "3 for every barrier with respect to the eight selected channels (M0, M1 = 0 and M2 > 0 verified at every probe)",
                               "ramps": "quintic C2 smoothstep 5 s, t = 5-10 s, final value = original step (58.564 MW bus 4; 17.345 MVAr bus 21), derivatives of the disturbance in the conditions"},
               "engine_validation": {"projected": vrow(val_s), "unprojected": vrow(val_u)},
               "unprojected_S0_feasibility": unproj_S0,
               "feasibility_cases": cases,
               "cost": {"control_period_s": 3.90625e-3, "linearize_mean_s": float(np.mean([c["linearize"] for c in s0_costs])), "exact_jets_two_eps_mean_s": float(np.mean([c["exact_jets_two_eps_each"] for c in s0_costs])),
                        "single_jet_evaluation_s": float(np.mean([r["jets_time_s"] for r in val_s.values()])), "algebraic_solve_mean_s": float(np.mean([c["solve_total"] / c["n_algebraic_solves"] for c in s0_costs])),
                        "evaluation_total_mean_s_incl_audit": float(np.mean([c["total"] for c in s0_costs]))},
               "closed_loop_B4_executed": False,
               "closed_loop_reason": "authorization condition (satisfactory mathematical validation) not met: derivatives of order 2-3 differ from the free-flow truth by 4-110 % at the transient states and are noise level near equilibrium; and the filter is feasible only 1-15 s after the event start",
               "figures": {"summary": f"Paper_manuscript/figures_main/IEEE39_E9F_summary{T}.png"},
               "raw_sha256": {f: sha256(A / f) for f in (f"IEEE39_E9B0_Vsafe{T}_series.npz",)},
               "artifacts_sha256": {f.name: sha256(f) for f in sorted(A.glob("IEEE39_E9F_*")) if f.name != "IEEE39_E9F_summary.json"},
               "code_sha256": {f: sha256(SRC / f) for f in ("e9f_engine.py", "run_e9f_feasibility.py", "test_e9f_engine.py", "run_e9g_b4.py", "finalize_e9f.py", "run_b3_ieee39.py", "run_e9c_lie_validation.py")}}
    (A / "IEEE39_E9F_summary.json").write_text(json.dumps(summary, indent=2, default=float), encoding="utf-8")
    with MATRIX_FILE.open("r", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames or [])
        rows = [r for r in reader if r.get("stage") not in ("E9F1", "E9F2")]
    new = []
    for stage, scen, note in (("E9F1", "engine_validation_S0_P+", "nonlinear Lie-derivative engine validated against ANDES free flow: orders 2-3 not within tolerance at transient states (DEC-046)."),
                              ("E9F2", "feasibility_S0_P+_Q+_steps_and_5s_ramps", "reformulated HOCBF (eight GFM inputs) feasible only 1-15 s after the event start; B4 closed loop not executed (DEC-046).")):
        row = {k: "" for k in fields}
        row.update({"run_id": f"{stage}_Vsafe_R35_040", "stage": stage, "case": "C2t_Vsafe_R35_040 (initial-condition variant of C2t)", "scenario": scen, "baseline": "E8_C2t_B2", "git_commit": git_commit(), "simulation_tf": 60.0,
                    "event_time": 5.0, "status_auto": status, "status_human": "PENDING", "frequency_figure": summary["figures"]["summary"], "voltage_figure": summary["figures"]["summary"],
                    "raw_file": f"Paper_manuscript/artifacts/IEEE39_E9B0_Vsafe{T}_series.npz", "decision_note": note})
        new.append(row)
    with MATRIX_FILE.open("w", newline="", encoding="utf-8") as stream:
        w = csv.DictWriter(stream, fieldnames=fields); w.writeheader(); w.writerows(rows + new)
    print({n: c["verdict"]["protection_may_start_at_s_after_event"] for n, c in cases.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
