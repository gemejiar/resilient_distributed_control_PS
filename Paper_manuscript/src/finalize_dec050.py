"""DEC-050 closure: tables (CSV), hashes, integrity re-check, simulation budget and the consolidated report.  No simulation."""

from __future__ import annotations

import csv
import json
import os

os.environ["C2_VARIANT"] = "C2t"

from run_e0_ieee39 import ARTIFACTS_DIR as A, git_commit, sha256

NAMES = ["SG30", "SG31", "SG33", "SG35", "SG38", "SG39", "GFM32", "GFM37", "GFM34", "GFM36"]


def J(n):
    return json.loads((A / n).read_text(encoding="utf-8"))


def main() -> int:
    a, b, c, cd, cs, ramp = J("IEEE39_DEC050_A_summary.json"), J("IEEE39_DEC050_B_summary.json"), J("IEEE39_DEC050_C_summary.json"), J("IEEE39_DEC050_C_dynamic.json"), J("IEEE39_DEC050_C1_static.json"), J("IEEE39_DEC050_C_ramp_diagnostic.json")
    # ---- CSV: equilibrium estimate
    eq = a["equilibrium_estimate"]; dec = a["Q_channel_decomposition"]["t1999"]
    with (A / "IEEE39_DEC050_A_equilibrium.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["unit", "Qset_minus_Qn_pu", "Pset_minus_Pn_pu", "unit_voltage_pu", "g_Q", "voltage_term", "consensus_term", "leak_term"])
        for i, n in enumerate(NAMES):
            w.writerow([n, eq["Qset_minus_Qn_pu"][i], eq["Pset_minus_Pn_pu"][i], eq["unit_voltage_pu"][i], dec["g_Q"][i], dec["voltage_term"][i], dec["consensus_term"][i], dec["leak_term"][i]])
    # ---- CSV: paired comparison B
    with (A / "IEEE39_DEC050_B_paired.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        keys = ["qset_drift_20s_max_abs_pu", "pset_drift_20s_max_abs_pu", "unit_voltage_mean_abs_error_to_1pu", "bus_voltage_final_min_pu", "bus_voltage_final_max_pu", "frequency_final_error_hz", "frequency_nadir_hz", "bus_voltage_tail_slope_max_abs_pu_per_s", "P_over_Pn_final_spread"]
        w.writerow(["scenario", "controller"] + keys + ["converged", "not_converged_channels", "units_crossing_limits", "GFM_share_of_delivered_dP", "min_margin_SG31", "min_margin_SG35"])
        for sc, d in b["scenarios"].items():
            for ctl in ("B2", "B2_QV1"):
                cv, lm = d[ctl]["convergence"], d[ctl]["limits"]
                w.writerow([sc, ctl] + [cv[k] for k in keys] + [cv["converged"], "|".join(cv["not_converged_channels"]), json.dumps(lm["units_crossing_a_limit"]), lm["GFM_share_of_delivered_dP"], lm["min_normalised_margin_by_unit"]["SG31"], lm["min_normalised_margin_by_unit"]["SG35"]])
    # ---- CSV: frontier / delay observations
    e12 = J("IEEE39_E12_frontier.json")["dynamic_runs"]
    with (A / "IEEE39_DEC050_C_observations.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["source", "kind", "amplitude", "unit", "outcome", "violating_units", "n_buses_outside_band", "bus_voltage_min_pu", "tds_failed", "t_end_s"])
        for x in e12:
            w.writerow(["E12", x["kind"], x["amplitude"], "MW" if x["kind"] == "P" else "MVAr", x["class"][:5], x["violating_units"], x["n_buses_outside_band"], x["bus_voltage_min_pu"], x["tds_failed"], x["t_end_s"]])
        for k in ("P", "Q"):
            for x in cd[k]:
                w.writerow(["DEC-050", k, x["amplitude"], "MW" if k == "P" else "MVAr", x["class"][:5], x["violating_units"], x["n_buses_outside_band"], x["bus_voltage_min_pu"], x["tds_failed"], x["t_end_s"]])
        w.writerow(["DEC-050 ramp diagnostic", "Q ramp 5 s", ramp["amplitude"], "MVAr", "respects" if not ramp["tds_failed"] else "fails", ramp["violating_units"], ramp["n_buses_outside_band"], ramp["bus_voltage_min_pu"], ramp["tds_failed"], ramp["t_end_s"]])
        for x in cd["delay"]:
            w.writerow(["DEC-050", f"delay {x['delay_s']} s", x["delay_s"], "s", "ok" if x["tds_ok"] and not x["units_crossing_limits"] and x["n_buses_outside_band"] == 0 else "degraded", x["units_crossing_limits"], x["n_buses_outside_band"], x["bus_voltage_min_pu"], not x["tds_ok"], x["t_end_s"]])
    # ---- hashes and integrity
    new = ["IEEE39_DEC050_A_longrun_Qplus_series.npz", "IEEE39_DEC050_A_longrun_Qplus_probes.npz", "IEEE39_DEC050_A_summary.json", "IEEE39_DEC050_A_equilibrium.csv", "IEEE39_DEC050_B_B2QV1_series.npz", "IEEE39_DEC050_B_summary.json",
           "IEEE39_DEC050_B_paired.csv", "IEEE39_DEC050_C1_static.json", "IEEE39_DEC050_C_dynamic.json", "IEEE39_DEC050_C_ramp_diagnostic.json", "IEEE39_DEC050_C_summary.json", "IEEE39_DEC050_C_observations.csv"]
    hashes = {n: sha256(A / n) for n in new}
    b3 = J("IEEE39_B3_C2t_Pplus_summary.json")
    e9c = J("IEEE39_E9C_summary.json")
    hist = {"E8 raw": (b3.get("e8_raw_sha256"), sha256(A / "IEEE39_E8_C2t_timeseries.npz")), "B3-S0 raw": (b3.get("b3_s0_raw_sha256"), sha256(A / "IEEE39_B3_C2t_S0_timeseries.npz"))}
    f = "IEEE39_E9B0_Vsafe_R35_040_series.npz"
    hist["R35_040 B0 raw"] = (e9c["raw_sha256"].get(f), sha256(A / f))
    unchanged = {k: v[0] == v[1] for k, v in hist.items()}
    sims = [{"id": 1, "what": "8 s smoke test of run_dec050_a_longrun.py (output discarded)"}, {"id": 2, "what": "block A: 2000 s B2 Q+ on R35_040"}, {"id": 3, "what": "block B: B2_QV1 S0 200 s"}, {"id": 4, "what": "block B: B2_QV1 P+ 200 s"},
            {"id": 5, "what": "block B: B2_QV1 Q+ 200 s"}, {"id": 6, "what": "C1: P step 73.2 MW, 40 s"}, {"id": 7, "what": "C1: P step 65.9 MW, 40 s"}, {"id": 8, "what": "C1: Q step 104.1 MVAr, 40 s"}, {"id": 9, "what": "C1: Q step 86.7 MVAr, 40 s"},
            {"id": 10, "what": "C2: delay 0.50 s, P+ 100 s"}, {"id": 11, "what": "C2: delay 0.75 s, P+ 100 s"}, {"id": 12, "what": "C1 diagnostic: Q 138.6 MVAr as 5 s ramp, 40 s"}]
    cr = b["criteria"]
    n1999 = a["newton"]["t1999"]
    summary = {"stage": "DEC-050 consolidation", "git_commit": git_commit(), "branch": "review/rdc-recovery-dec050 (from 4710e76)", "dynamic_simulations": {"limit": 12, "used": len(sims), "list": sims},
               "A": {"equilibrium_exists_numerically": True, "verified_by_declared_criterion": a["verified_equilibrium_criterion"]["verified"], "drift_v0_199_to_1999": [a["newton"][f"t{k}"]["v0_inf_pu_per_s"] for k in (199, 500, 1000, 1999)],
                     "tau_observed_s": a["observed_decay_tau_s_of_distance_Qset_to_final"], "tau_modal_s": [a["newton"][f"t{k}"]["tau_slowest_s"] for k in (199, 500, 1000, 1999)], "final_tail": a["tail_last_100s"]},
               "B": {"improves_by_declared_criteria": b["improves_by_declared_criteria"], "criteria": cr, "g_floor": b["scenarios"]["S0"]["g_floor"]}, "C": {"C1": c["C1"], "C2": c["C2"], "C3_admissible_points": list(c["C3"]["admissible_points"]), "C4": {k: c["C4"][k] for k in ("dynamic_P_step_frontier_R35_040_MW", "tolerated_amplitude_gain_lower_bound_MW")}, "C5": c["C5"]},
               "hashes_sha256": hashes, "historical_hashes_recheck": {k: {"recorded": v[0], "now": v[1], "unchanged": unchanged[k]} for k, v in hist.items()},
               "code_changes_to_existing_files": ["run_b3_ieee39.py: optional log_every (default 1)", "e9h_predictor.py: build() additionally returns xdot, v0, Cz (additive)"], "scratch_note": "E15 artifacts were accidentally overwritten by a rerun with the default (non-R35_040) variant and restored from commit 4710e76 before any use"}
    (A / "IEEE39_DEC050_consolidation.json").write_text(json.dumps(summary, indent=2, default=float), encoding="utf-8")
    print(json.dumps({"unchanged": unchanged, "sims": len(sims), "B": b["improves_by_declared_criteria"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
