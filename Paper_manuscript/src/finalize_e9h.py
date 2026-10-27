"""E9-H: consolidate the predictive safety filter results (error bounds, S0 test, shadow selection) into one summary, a figure and the experiment-matrix rows (no simulation)."""

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


def main() -> int:
    bounds = json.loads((A / f"IEEE39_E9H_error_bounds{T}.json").read_text(encoding="utf-8"))
    z = np.load(A / f"IEEE39_E9H_error_bounds{T}.npz")
    eps, emax, q99 = z["eps"], z["emax"], z["q99"]
    b4 = json.loads((A / f"IEEE39_E9H_b4{T}.json").read_text(encoding="utf-8"))
    first = json.loads((A / f"IEEE39_E9H_b4{T}_firstrun_S0_cost_gate_failed.json").read_text(encoding="utf-8"))
    tau = np.arange(eps.shape[0]) * 0.1
    fig, ax = plt.subplots(1, 3, figsize=(18, 5))
    for i in range(10):
        ax[0].plot(tau[1:], eps[1:, i], lw=.9, label=f"unit {i}")
        ax[1].plot(tau[1:], eps[1:, 10 + i], lw=.9)
    ax[2].plot(tau[1:], eps[1:, 20:], lw=.5, color="tab:blue", alpha=.5)
    ax[0].set_title("P error bound eps (1.5 x max observed) [pu]"); ax[1].set_title("Q error bound [pu]"); ax[2].set_title("bus-voltage error bound [pu] (39 buses)")
    ax[0].legend(fontsize=6, ncol=2)
    for a in ax:
        a.set_xlabel("prediction time tau [s]"); a.grid(alpha=.25)
    fig.suptitle("E9-H: empirical bound of the 3 s prediction error (windows from t = 5.5 s of S0, P+, Q+; excludes the first 0.5 s after an event)"); fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"IEEE39_E9H_error_bounds{T}.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    s0 = b4["stages"]["S0"]
    sh = b4["stages"]["shadow"]
    status = "FINDINGS_WAIT_HUMAN"
    figs = {"error_bounds": f"Paper_manuscript/figures_main/IEEE39_E9H_error_bounds{T}.png", "S0_B2_vs_B4": f"Paper_manuscript/figures_main/IEEE39_E9H_S0{T}.png"}
    summary = {"stage": "E9-H", "status_auto": status, "status_human": "PENDING", "git_commit": git_commit(), "python": platform.python_version(),
               "design": {"horizon_s": 3.0, "update_s": 0.1, "inputs": "eight GFM reference rates, constant offset over the horizon", "SG": "original RDC inside the prediction", "predictor": "closed-loop (plant + RDC) frozen-Jacobian affine model, exact discretisation, refreshed every update (parameter derivatives every 1 s)",
                          "safety_condition": "predicted margin - empirical error bound - 15 % sensitivity error >= 0 on the 3 s grid; minimal-intervention LP", "enforceable_rule": "achievable margin change >= 10 % of the bound",
                          "no_hocbf_derivatives": True},
               "error_bound": {"is_mathematically_justified": False, "nature": "empirical: 1.5 x the maximum observed over 156 windows (S0, P+, Q+; from 0.5 s after the event); sensitivity error 15 % from the E9-C ramp tests",
                               "summary": bounds["bound_summary"], "per_scenario_max_error": {k: {"P": v["max_error_P"], "Q": v["max_error_Q"], "V": v["max_error_V"]} for k, v in bounds["per_scenario"].items()},
                               "q99_P_at_3s_pu": float(q99[30, :10].max()), "table": "IEEE39_E9H_error_bounds_R35_040.npz"},
               "cost": {"validation_mean_update_s": bounds["cost"]["mean_update_wall_s"], "S0_B4_mean_update_s": s0["cost"]["mean_update_s"], "S0_B4_p95_s": s0["cost"]["p95_update_s"], "S0_first_run_mean_update_s_before_vectorising": first["stages"]["S0"]["cost"]["mean_update_s"],
                        "shadow_P+_mean_update_s": sh["P+"]["cost"]["mean_update_s"], "shadow_Q+_mean_update_s": sh["Q+"]["cost"]["mean_update_s"], "declared_requirement_s": 0.5, "update_period_s": 0.1,
                        "dominant_term": "linearization of the DAE (0.33 s in S0, 0.45-0.47 s in the disturbed cases)", "real_time_claim": False},
               "S0": {"gate": s0["gate"], "lp_feasible_all_updates": True, "zero_action": True, "difference_B4_minus_B2": s0["difference_B4_minus_B2"], "coverage_first_0.3s": s0["coverage_first_0.3s_of_each_window"], "n_updates": s0["filter"]["n_updates"]},
               "shadow_selection": {"rule": b4["selection_rule"], "selected": b4.get("selected_scenario"),
                                    "P+": {k: sh["P+"]["filter"][k] for k in ("n_updates", "n_updates_nominal_violates_enforceable", "n_lp_infeasible", "n_updates_monitored_reserve_violated", "worst_enforceable_margin_minus_eps_min")},
                                    "Q+": {k: sh["Q+"]["filter"][k] for k in ("n_updates", "n_updates_nominal_violates_enforceable", "n_lp_infeasible", "n_updates_monitored_reserve_violated", "worst_enforceable_margin_minus_eps_min")},
                                    "B2_min_P_margins_P+": sh["P+"]["B2"]["min_P_margin_pu"], "B2_violations": {"P+": sh["P+"]["B2"]["violating_units"], "Q+": sh["Q+"]["B2"]["violating_units"]}},
               "closed_loop_decisive_test_executed": False,
               "reason": "no known event (P+, Q+) activates an enforceable tightened constraint from t = 5.5 s on, B2 respects all physical constraints in both, and the binding limits (SG31, SG35 power) are not influenced by the GFM within the horizon; the cost requirement is also exceeded in the disturbed cases (0.52 s)",
               "figures": figs, "raw_sha256": {f: sha256(A / f) for f in (f"IEEE39_E9H_error_bounds{T}.npz",)},
               "artifacts_sha256": {f.name: sha256(f) for f in sorted(A.glob("IEEE39_E9H_*")) if f.suffix == ".json"},
               "code_sha256": {f: sha256(SRC / f) for f in ("e9h_predictor.py", "validate_e9h_predictor.py", "run_e9h_b4.py", "finalize_e9h.py", "e9a_linear.py", "run_b3_ieee39.py")}}
    (A / "IEEE39_E9H_summary.json").write_text(json.dumps(summary, indent=2, default=float), encoding="utf-8")
    with MATRIX_FILE.open("r", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames or [])
        rows = [r for r in reader if r.get("stage") not in ("E9H1", "E9H2")]
    new = []
    for stage, scen, note in (("E9H1", "predictor_error_bound_S0_P+_Q+", "empirical 3 s prediction error bound (P 0.012, Q 0.14, V 0.0066 pu); mean update 0.43 s (DEC-047)."),
                              ("E9H2", "predictive_filter_S0_and_shadow_P+_Q+", "S0 B4 identical to B2, zero action; no known event activates an enforceable constraint; decisive test not executed; option B (DEC-047).")):
        row = {k: "" for k in fields}
        row.update({"run_id": f"{stage}_Vsafe_R35_040", "stage": stage, "case": "C2t_Vsafe_R35_040 (initial-condition variant of C2t)", "scenario": scen, "baseline": "E8_C2t_B2", "git_commit": git_commit(), "simulation_tf": 60.0,
                    "event_time": 5.0, "status_auto": status, "status_human": "PENDING", "frequency_figure": figs["S0_B2_vs_B4"], "voltage_figure": figs["error_bounds"],
                    "raw_file": f"Paper_manuscript/artifacts/IEEE39_E9H_error_bounds{T}.npz", "decision_note": note})
        new.append(row)
    with MATRIX_FILE.open("w", newline="", encoding="utf-8") as stream:
        w = csv.DictWriter(stream, fieldnames=fields)
        w.writeheader()
        w.writerows(rows + new)
    print(summary["cost"], summary["shadow_selection"]["selected"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
