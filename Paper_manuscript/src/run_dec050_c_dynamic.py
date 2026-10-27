"""DEC-050 block C (dynamic part): refinement of the P/Q dynamic frontiers and two additional delay tests (dynamic simulations 6-12 of 12 at most).

Declared before running (nothing is tuned; B2 original on C2t_Vsafe_R35_040, 40 s step runs exactly as in E12, so the new points are directly comparable with the E12 points):
  P frontier : E12 brackets it between 58.5 MW (no violation) and 87.8 MW (SG31/SG35 cross).  One simulation at the midpoint (73.2 MW = 1.25 x), then one at the midpoint of the remaining half.
  Q frontier : E12 brackets it between 69.3 MVAr (ok) and 138.6 MVAr (TDS failure at 5.2 s).  One simulation at the midpoint (104 MVAr = 6.0 x), then one at the midpoint of the remaining half
               (5.0 x or 7.0 x).
  delays     : 0.50 s and 0.75 s (E15 tested 0.2 s: ok, 1.0 s: limits/band violated, 5 s: divergence), same ring-buffer implementation and P+ 100 s run as E15.
  diagnostic : only if a Q step ends in a TDS failure, ONE run of the lowest failing Q amplitude with the same load applied as a 5 s quintic ramp (dist_fn) to separate "the instantaneous step
               cannot be integrated / has no short-term solution" from "the system cannot withstand the amplitude".  A TDS failure is never read as physical instability or as the non-existence
               of an equilibrium: the static AC equilibrium exists up to ~277 MVAr (E12), and the failure time/residual are reported.
Classification as in E12: (iii) respects limits and the 0.95-1.05 pu band; (ii) otherwise.
"""

from __future__ import annotations

import json
import os

os.environ["C2_VARIANT"] = "C2t"
os.environ.setdefault("E9B0_VARIANT", "C2t_Vsafe_R35_040")
os.environ.setdefault("E9B0_DELTA", "0.040")

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import run_b3_ieee39 as b  # noqa: E402
import run_e12_frontier as E12  # noqa: E402
import run_e15_robustness as E15  # noqa: E402
import e9f_engine as E  # noqa: E402
from run_e9f_feasibility import make_dist_fn  # noqa: E402
from e9b_variant import HOOK, VARIANT  # noqa: E402
from run_e0_ieee39 import ARTIFACTS_DIR as A, FIGURES_DIR, git_commit  # noqa: E402

assert VARIANT == "C2t_Vsafe_R35_040", VARIANT


def ok(r: dict) -> bool:
    return (not r.get("tds_failed")) and not r.get("violating_units") and r.get("n_buses_outside_band", 1) == 0


def ramp_run(mult: float, lim) -> dict:
    """Q load applied as a 5 s quintic ramp (diagnostic)."""
    amp = E12.Q_STEP_PU * mult

    def hook(system, ctx):
        HOOK(system, ctx)
        system.TDS.config.tf = E12.HORIZON
    try:
        _, d, diag = b.run("B2", "S0", init_hook=hook, dist_fn=make_dist_fn(E.Disturbance("Q", amp, 5.0, 5.0)))
    except Exception as exc:
        return {"kind": "Q ramp 5 s", "multiple": mult, "amplitude": amp * 100, "tds_failed": True, "error": repr(exc)[:200]}
    t = d["time_s"]
    p = np.hstack([d["sg_p_pu"], d["gfm_p_pu"]]); q = np.hstack([d["sg_q_pu"], d["gfm_q_pu"]]); vb = d["bus_voltage_pu"]
    s_rel = 1 - np.hypot(p, q) / lim["smax"]
    viol = [i for i in range(10) if (p[:, i].max() > lim["pmax"][i] or p[:, i].min() < lim["pmin"][i] or q[:, i].max() > lim["qmax"][i] or q[:, i].min() < lim["qmin"][i] or s_rel[:, i].min() < 0)]
    return {"kind": "Q ramp 5 s", "multiple": mult, "amplitude": amp * 100, "tds_failed": not (diag["tds_ok"] and diag["t_end_s"] >= E12.HORIZON - 1e-6), "t_end_s": diag["t_end_s"], "violating_units": viol,
            "n_buses_outside_band": int(((vb < 0.95) | (vb > 1.05)).any(axis=0).sum()), "bus_voltage_min_pu": float(vb.min()), "bus_voltage_max_pu": float(vb.max()), "final_residual": diag["final_residual"]}


def main() -> int:
    ctx = E12.static_setup()
    lim = ctx[0]
    out: dict = {"stage": "DEC-050 C dynamic", "git_commit": git_commit(), "doc": __doc__, "variant": VARIANT, "P": [], "Q": [], "delay": [], "diagnostic_ramp": None}
    r = E12.dynamic("P", 1.25, lim); out["P"].append(r); print("P", r["amplitude"], ok(r), r.get("violating_units"), flush=True)
    m2 = 1.125 if not ok(r) else 1.375
    r = E12.dynamic("P", m2, lim); out["P"].append(r); print("P", r["amplitude"], ok(r), r.get("violating_units"), flush=True)
    r = E12.dynamic("Q", 6.0, lim); out["Q"].append(r); print("Q", r["amplitude"], ok(r), r.get("tds_failed"), r.get("t_end_s"), flush=True)
    m2 = 5.0 if not ok(r) else 7.0
    r2 = E12.dynamic("Q", m2, lim); out["Q"].append(r2); print("Q", r2["amplitude"], ok(r2), r2.get("tds_failed"), r2.get("t_end_s"), flush=True)
    for dl in (0.5, 0.75):
        r = E15.run_case(f"delay {dl} s", "P+", None, dl, None, None)
        r.pop("_series", None)
        out["delay"].append({"delay_s": dl, **r}); print("delay", dl, r.get("tds_ok"), r.get("units_crossing_limits"), flush=True)
    failing = [x for x in out["Q"] if x.get("tds_failed")]
    if failing:
        low = min(failing, key=lambda x: x["multiple"])
        out["diagnostic_ramp"] = ramp_run(low["multiple"], lim)
        print("ramp", out["diagnostic_ramp"], flush=True)
    out["dynamic_simulations_in_this_script"] = 2 + 2 + 2 + (1 if failing else 0)
    (A / "IEEE39_DEC050_C_dynamic.json").write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
    e12 = json.loads((A / "IEEE39_E12_frontier.json").read_text(encoding="utf-8"))["dynamic_runs"]
    fig, ax = plt.subplots(1, 2, figsize=(14, 5.5))
    for a, kind in ((ax[0], "P"), (ax[1], "Q")):
        pts = [(x["amplitude"], ok(x), "E12") for x in e12 if x["kind"] == kind] + [(x["amplitude"], ok(x), "DEC-050") for x in out[kind]]
        for amp, good, src in pts:
            a.scatter([amp], [1 if good else 0], color=("tab:green" if good else "tab:red"), marker=("o" if src == "E12" else "s"), s=60)
        a.set_yticks([0, 1]); a.set_yticklabels(["violates / fails", "respects limits and band"]); a.set_xlabel(f"{kind} step amplitude [{'MW' if kind == 'P' else 'MVAr'}]"); a.grid(alpha=.25)
        a.set_title(f"{kind} step: dynamic frontier (circles E12, squares DEC-050)")
    fig.suptitle("DEC-050 C1: dynamic frontiers of B2 on C2t_Vsafe_R35_040 (40 s steps)"); fig.tight_layout()
    fig.savefig(FIGURES_DIR / "IEEE39_DEC050_C_frontier.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
