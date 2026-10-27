"""E9-C Phase 2: amplitude search for disturbances compatible with the HOCBF filter (diagnostic, QP outside the loop).

For each family (P+: bus 4; Q+: bus 21) and each fraction of the original disturbance (0.5, 1, 2, 5, 10, 20, 50, 100 %), same bus and instant (t = 5 s), the frozen variant
(E9B0_VARIANT, default C2t_Vsafe_R35_040) is replayed under B2 (original RDC, no QP) for 30 s and probed before and after the event (same machinery as E9-B1).

Selection criteria, declared BEFORE running (largest fraction that meets all of them is frozen, per family, before any comparison between B2 and the filter):
  C1  pre-event state inside C_H (no barrier outside, no negative h) and the QP feasible;
  C2  the first probe containing the load jump (>= 2 ms after the event) has no barrier outside C_H and no negative h;
  C3  the QP is feasible at s = 1 (SLSQP and trust-constr agree) at every probe after the event (up to 20 s);
  C4  B2 without QP violates no P/Q/S limit and no bus voltage in 0.95-1.05 pu during the 30 s.
The rate envelope is the one of E9-B1 (experimental candidate bound, same for all fractions).  Whether the perturbation activates a safety constraint is recorded: the QP is
'inactive' at a probe when the nominal B2 command already satisfies every constraint; if inactive everywhere the result is a consistency test, not evidence of protection.
Horizon 30 s (instead of 200 s) is a declared reduction for the scan: the load-jump transient and the recovery of C_H occur within the first seconds (E9-B1).
"""

from __future__ import annotations

import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

os.environ["C2_VARIANT"] = "C2t"

import andes
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import run_b3_ieee39 as b  # noqa: E402
import run_e8_ieee39 as e8  # noqa: E402
import run_e9b1_feasibility as R  # noqa: E402
from e9b_variant import DELTA, HOOK, TAG, VARIANT  # noqa: E402
from run_e0_ieee39 import ARTIFACTS_DIR, FIGURES_DIR, git_commit, sha256  # noqa: E402
from run_e9b0_variant import margins  # noqa: E402

OUT = ARTIFACTS_DIR / f"IEEE39_E9C_amplitude_search{TAG}.json"
FIG = FIGURES_DIR / f"IEEE39_E9C_amplitude_search{TAG}.png"
FRACTIONS = (0.005, 0.01, 0.02, 0.05, 0.10, 0.20, 0.50, 1.00)
FAMILIES = {"P+": ("p_mw", 58.564, (0.616, 0.0154)), "Q+": ("q_mvar", 17.345, (0.195, 0.0154))}
HORIZON = 30.0
EVENT = 5.0
PROBES = [4.99, 5.00005, 5.004, 5.008, 5.02, 5.05, 5.1, 5.15, 5.25, 5.5, 6.0, 7.0, 10.0, 20.0]


def run_one(family: str, frac: float) -> dict[str, Any]:
    key, base, envelope = FAMILIES[family]
    name = f"{family}@{frac:g}"
    e8.SCENARIOS[name] = {key: base * frac}

    def hook(system, ctx):
        HOOK(system, ctx)
        system.TDS.config.tf = HORIZON

    R.PROBE_T = PROBES
    pr = R.Prober(name, None, vref=envelope)
    _, data, diag = b.run("B2", name, probe=pr, init_hook=hook)
    lim = e8.configure("S0", e8.TIME_STEP_S)[1]["lim"]
    names = [("SG" if i < 6 else "GFM") + str(bb) for i, bb in enumerate(data["unit_bus_ids"])]
    m = margins(data, lim, names)
    rows = pr.rows
    pre = [r for r in rows if r["t_s"] < EVENT + 0.00005][-1]
    post = [r for r in rows if r["t_s"] > EVENT + 0.002]
    first = post[0]
    ok = lambda r: bool(r["C_H"]["n_outside"] == 0 and not r["C_H"]["h_negative"])  # noqa: E731
    qp_ok = lambda r: bool(r["audit"]["qp"]["SLSQP"]["converged"] and r["audit"]["qp"]["trust-constr"]["converged"] and r["audit"]["qp_solvers_agree"])  # noqa: E731
    crit = {"C1_pre_event_inside_CH_and_QP_feasible": bool(ok(pre) and qp_ok(pre)), "C2_first_post_jump_inside_CH": ok(first),
            "C3_QP_feasible_at_all_post_event_probes": bool(all(qp_ok(r) for r in post)),
            "C4_B2_no_limit_violation_and_voltage_in_band": bool(not m["violating_units"] and m["bus_voltage"]["n_buses_ever_outside_band"] == 0)}
    out = {"family": family, "fraction": frac, "amplitude": base * frac, "unit": key, "tds_ok": diag["tds_ok"], "final_residual": diag["final_residual"], "criteria": crit, "meets_all": all(crit.values()),
           "violating_units": m["violating_units"], "bus_voltage": m["bus_voltage"], "frequency": m["frequency"],
           "min_P_margin_pu": {n: r["min_P_margin_to_pmax_pu"] for n, r in m["per_unit"].items()},
           "first_post_jump": {"t_after_event_s": first["t_s"] - EVENT, "barriers_outside_CH": first["C_H"]["n_outside"], "outside_by_kind": first["C_H"]["outside_by_kind"], "h_negative": first["C_H"]["h_negative"],
                               "worst_psi": first["C_H"]["worst_psi_min"][:4], "qp_feasible": qp_ok(first), "authority_scale_min": first["audit"]["authority_scale_min"],
                               "elastic_violation": first["audit"]["elastic_violation_at_s1"], "conflict_set_top": first["audit"]["conflict_set_top"][:3]},
           "probes": [{"t_after_event_s": r["t_s"] - EVENT, "n_outside_CH": r["C_H"]["n_outside"], "h_negative": r["C_H"]["h_negative"][:4], "authority_scale_min": r["audit"]["authority_scale_min"], "qp_feasible": qp_ok(r),
                       "nominal_satisfies_all": r["audit"]["nominal_satisfies_all"], "min_psi": r["C_H"]["worst_psi_min"][0][1], "qp_time_s": r["audit"]["qp"]["SLSQP"]["time_s"]} for r in rows],
           "QP_inactive_at_all_probes": bool(all(r["audit"]["nominal_satisfies_all"] for r in rows if r["t_s"] > EVENT)),
           "qp_active_probe_times_s": [r["t_s"] - EVENT for r in rows if r["t_s"] > EVENT and not r["audit"]["nominal_satisfies_all"]]}
    print(f"{name}: meets_all={out['meets_all']} {crit} outside@first={first['C_H']['n_outside']} qp_inactive={out['QP_inactive_at_all_probes']}", flush=True)
    return out


def main() -> int:
    fams = sys.argv[1:] or list(FAMILIES)
    result: dict[str, Any] = {"variant": VARIANT, "incremental_redispatch_delta_pu": DELTA, "git_commit": git_commit(), "andes": andes.__version__, "python": platform.python_version(),
                              "horizon_s": HORIZON, "fractions": list(FRACTIONS), "probe_targets_s": PROBES, "criteria_doc": __doc__, "families": {}}
    for fam in fams:
        runs = [run_one(fam, f) for f in FRACTIONS]
        passing = [r for r in runs if r["meets_all"]]
        sel = max(passing, key=lambda r: r["fraction"]) if passing else None
        mono = all(r["meets_all"] == (r["fraction"] <= (sel["fraction"] if sel else 0)) for r in runs)
        result["families"][fam] = {"runs": runs, "selected_fraction": sel["fraction"] if sel else None, "selected_amplitude": sel["amplitude"] if sel else None,
                                   "selection_is_monotonic": bool(mono), "selected_activates_a_constraint": (not sel["QP_inactive_at_all_probes"]) if sel else None,
                                   "interpretation": ("consistency test: the QP is inactive at every probe, no protection is demonstrated" if sel and sel["QP_inactive_at_all_probes"]
                                                      else "the QP is active at some probe" if sel else "no fraction meets the criteria")}
        OUT.write_text(json.dumps(result, indent=2, default=float), encoding="utf-8")
    result["code_sha256"] = {f: sha256(Path(__file__).parent / f) for f in ("run_e9c_amplitudes.py", "run_e9b1_feasibility.py", "e9b_tools.py", "e9a_hocbf.py", "e9a_linear.py", "e9b_variant.py")}
    OUT.write_text(json.dumps(result, indent=2, default=float), encoding="utf-8")
    plots(result)
    return 0


def plots(result: dict[str, Any]) -> None:
    fig, ax = plt.subplots(1, 3, figsize=(18, 5.5))
    for fam, res in result["families"].items():
        fr = [r["fraction"] * 100 for r in res["runs"]]
        ax[0].semilogx(fr, [r["first_post_jump"]["barriers_outside_CH"] for r in res["runs"]], "o-", label=fam)
        ax[1].semilogx(fr, [sum(1 for p in r["probes"] if p["t_after_event_s"] > 0.002 and not p["qp_feasible"]) for r in res["runs"]], "o-", label=fam)
        ax[2].semilogx(fr, [min(r["min_P_margin_pu"].values()) for r in res["runs"]], "o-", label=fam)
        sf = res["selected_fraction"]
        if sf:
            for a in ax:
                a.axvline(sf * 100, ls=":", lw=.8, color="tab:green" if fam == "P+" else "tab:purple")
    ax[0].set_title("barriers outside C_H at the first probe after the jump"); ax[1].set_title("probes after the event with infeasible QP (of 14 probes, before 20 s)")
    ax[2].set_title("minimum P margin to pmax over the ten units under B2 [pu]")
    for a in ax:
        a.set_xlabel("fraction of the original disturbance [%]"); a.grid(alpha=.25); a.legend(fontsize=8)
    fig.suptitle(f"E9-C: admissible disturbance amplitude search on {result['variant']} (dotted: selected fraction)"); fig.tight_layout()
    fig.savefig(FIG, dpi=300, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())
