"""E9-D shadow mode: the per-step HOCBF-QP filter is evaluated at every control step of a B2 run but its output is DISCARDED (the trajectory is the plain B2 one).

This is not closed-loop operation.  It measures (i) how often the nominal B2 command would violate a constraint (QP activations), (ii) the cost of each stage per control step
against the 3.90625 ms period, and (iii) that the fast implementation reproduces e9a_hocbf.evaluate (same constraint matrices) at a probe state.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

os.environ["C2_VARIANT"] = "C2t"

import numpy as np

import e9a_hocbf as H
import e9d_filter as F
import run_b3_ieee39 as b
import run_e8_ieee39 as e8
from e9b_variant import HOOK, TAG, VARIANT
from run_e0_ieee39 import ARTIFACTS_DIR, git_commit, sha256

OUT = ARTIFACTS_DIR / f"IEEE39_E9D_shadow{TAG}.json"
SC = sys.argv[1] if len(sys.argv) > 1 else "S0"
LAM = 2.0
ENVELOPE = {"S0": (0.616, 0.0154), "P+": (0.616, 0.0154), "Q+": (0.195, 0.0154)}[SC]


def main() -> int:
    flt = F.FastHOCBF(LAM, ENVELOPE, refresh_s=5.0)
    act_times, check = [], {}
    h_min = {"t": [], "val": []}

    def probe(t, sys_, ctx, st, vnom_p, vnom_q):
        flt.filter(t, sys_, ctx, st, vnom_p, vnom_q)
        if flt.last["active"]:
            act_times.append(float(t))
        if "done" not in check and t >= 6.0:       # equivalence with the reference implementation at one state
            check["done"] = True
            lin = flt.lin
            y = sys_.dae.y
            rs = flt.rs
            p, q, vb = (np.asarray(y[rs[k]], float) for k in ("P", "Q", "Vbus"))
            names = [("SG" if i < ctx["n_sg"] else "GFM") + str(bb) for i, bb in enumerate(ctx["unit_bus"])]
            ev = H.evaluate(lin, rs, p, q, vb, np.asarray(st["pset"], float), np.asarray(st["qset"], float), ctx["lim"], LAM, names, rs["bus_ids"])
            xdot = np.asarray(sys_.dae.f, float).ravel()[lin["d_idx"]] / lin["tf_d"]
            a_f, b_f, _ = flt.constraints(p, q, vb, np.asarray(st["pset"], float), np.asarray(st["qset"], float), np.concatenate([xdot, np.zeros(20)]), ctx["lim"])
            a_e, b_e = np.vstack([ev["A"], ev["A_ref"]]), np.concatenate([ev["b"], ev["b_ref"]])
            check.update({"t_s": float(t), "max_abs_diff_A": float(np.abs(a_f - a_e).max()), "max_abs_A": float(np.abs(a_e).max()), "max_abs_diff_b": float(np.abs(b_f - b_e).max()),
                          "max_abs_b": float(np.abs(b_e).max()), "xdot_from_dae_f_vs_refresh_max_abs_diff": float(np.abs(xdot - lin["xdot"]).max()),
                          "relative_degree_3_for_all_outputs": flt.r_ok})

    _, data, diag = b.run("B2", SC, probe=probe, init_hook=HOOK)
    ts = np.array(flt.stats["t_step_s"])
    st = flt.stats
    out = {"variant": VARIANT, "scenario": SC, "mode": "shadow (filter output discarded; trajectory = plain B2)", "git_commit": git_commit(), "lambda": LAM, "rate_envelope_pu_per_s": ENVELOPE,
           "n_steps": st["n_steps"], "n_nominal_feasible": st["n_nominal_feasible"], "n_would_activate_qp": st["n_qp"], "fraction_active": st["n_qp"] / max(st["n_steps"], 1),
           "n_qp_infeasible": st["n_qp_infeasible"], "first_activation_times_s": act_times[:30], "violated_constraint_counts_top": sorted(st.get("violated_counts", {}).items(), key=lambda kv: -kv[1])[:20], "activation_time_histogram_10s_bins": np.histogram(act_times, bins=np.arange(0, 210, 10))[0].tolist(), "activation_time_range_s": [min(act_times), max(act_times)] if act_times else None,
           "max_qp_deviation_norm_if_applied": st["max_deviation_norm"], "equivalence_check_vs_evaluate": check,
           "cost_s": {"control_period_s": e8.TIME_STEP_S, "step_mean": float(ts.mean()), "step_median": float(np.median(ts)), "step_p95": float(np.percentile(ts, 95)), "step_p99": float(np.percentile(ts, 99)),
                      "step_max": float(ts.max()), "fraction_of_steps_over_period": float((ts > e8.TIME_STEP_S).mean()), "n_refresh": st["n_refresh"],
                      "refresh_mean": float(np.mean(st["t_refresh_s"])), "refresh_max": float(np.max(st["t_refresh_s"])),
                      "qp_mean": float(np.mean(st["t_qp_s"])) if st["t_qp_s"] else None, "qp_max": float(np.max(st["t_qp_s"])) if st["t_qp_s"] else None},
           "real_time_statement": "NOT demonstrated: Python/SciPy on a desktop; the figures above are the measured costs, no real-time capability is claimed",
           "diag": diag, "code_sha256": {f: sha256(Path(__file__).parent / f) for f in ("e9d_filter.py", "run_e9d_shadow.py", "e9a_hocbf.py", "e9a_linear.py")}}
    OUT.write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("n_steps", "n_nominal_feasible", "n_would_activate_qp", "n_qp_infeasible", "activation_time_range_s", "equivalence_check_vs_evaluate", "cost_s")}, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
