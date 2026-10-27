"""DEC-050 block B: the single Q/V correction "B2_QV1" (dynamic simulations 3-5 of 12), evaluated on S0, P+ and Q+ of C2t_Vsafe_R35_040 against the stored B2 runs (E9-B0 series, reused).

Cause identified in block A (analyse_dec050_a.py, IEEE39_DEC050_A_summary.json).  The closed loop has a verified equilibrium (reached at ~2000 s).  Its slowest non-leak modes (tau 432 s and 311 s)
live on the Q references of SG31 and GFM32, the two units whose normalised capability factor g_Q is smallest at the operating point (0.12 and 0.27 versus a median of 0.76): in the original law
the voltage term is v_Q,i = K_IQ [ K_V g_Q,i (V_ref - V_i) - K_Q l_Q,i ] - K_LEAK (Qset_i - Qn_i), so the integral rate of the voltage correction of a unit is proportional to its g_Q.
The correction.  In the VOLTAGE term only, g_Q,i is replaced by max(g_Q,i, g_floor) with g_floor = median of the ten nominal normalised factors (a rule fixed before running; 0.758).  The consensus
term, the leak, the P channel, the graph, the gains K_IQ, K_V, K_Q, K_LEAK, the capability definitions and the actuator maps are those of B2.  Prediction from the quasi-static reduced model at the
block-A equilibrium (before running): slowest Q mode 432 s -> ~185 s, all modes stable.
Implementation: the b.run ``qp_filter`` hook adds  K_IQ K_V (max(g_Q,g_floor) - g_Q)(V_ref - V)  to the Q rates after the event; B2 itself (b.run without the hook) is untouched.
Improvement criteria (declared before running): in P+ and Q+ the 20 s Qset drift at 200 s is reduced by at least 30 %; the mean unit-voltage error does not grow by more than 10 %; no unit crosses a
limit that B2 did not cross; the final frequency error does not worsen by more than 1e-4 Hz; S0 does not get worse (drift and voltage error).  Otherwise the correction is recorded as negative and
no second round is made.
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
import run_e8_ieee39 as e8  # noqa: E402
import run_e10_convergence as E10  # noqa: E402
import run_e11_limits as E11  # noqa: E402
from e9b_variant import HOOK, VARIANT  # noqa: E402
from run_e0_ieee39 import ARTIFACTS_DIR as A, FIGURES_DIR, git_commit, sha256  # noqa: E402

assert VARIANT == "C2t_Vsafe_R35_040", VARIANT
NAMES = ["SG30", "SG31", "SG33", "SG35", "SG38", "SG39", "GFM32", "GFM37", "GFM34", "GFM36"]
SCEN = ("S0", "P+", "Q+")


def make_filter():
    state: dict = {}

    def fn(t, sys_, ctx, st, vp, vq):
        _, gq_raw = e8.capability_factors(st["pset"], st["qset"], ctx["lim"])
        gq = gq_raw / st["gref_q"]
        if "floor" not in state:    # first active call: references still at the nominal setpoint
            state["floor"] = float(np.median(gq))
        volt = np.asarray(sys_.dae.y[st["a_v"]], float)
        return vp, vq + e8.K_IQ * e8.K_V * (np.maximum(gq, state["floor"]) - gq) * (e8.V_REF - volt)
    fn.state = state
    return fn


def main() -> int:
    base = E10.load_runs()
    lim = E11.limits()
    res: dict = {"stage": "DEC-050 B", "git_commit": git_commit(), "doc": __doc__, "variant": VARIANT, "scenarios": {}}
    raw = {}
    for sc in SCEN:
        flt = make_filter()
        _, d, diag = b.run("B2", sc, init_hook=HOOK, qp_filter={"fn": flt})
        raw[sc] = d
        print(sc, diag, "floor", flt.state.get("floor"), flush=True)
        a_b = E10.analyse(f"B2_QV1 {sc}", d)
        a_o = E10.analyse(f"R35_040_B2 {sc}", base[f"R35_040_B2 {sc}"])
        e_b = E11.evaluate(f"B2_QV1 {sc}", d, lim, NAMES)[0]
        e_o = E11.evaluate(f"R35_040_B2 {sc}", base[f"R35_040_B2 {sc}"], lim, NAMES)[0]
        res["scenarios"][sc] = {"diag_new": diag, "g_floor": flt.state.get("floor"), "B2_QV1": {"convergence": a_b, "limits": e_b}, "B2": {"convergence": a_o, "limits": e_o}}
    np.savez_compressed(A / "IEEE39_DEC050_B_B2QV1_series.npz", **{f"{sc}__{k}": v for sc, d in raw.items() for k, v in d.items() if isinstance(v, np.ndarray)})
    res["series_sha256"] = sha256(A / "IEEE39_DEC050_B_B2QV1_series.npz")
    crit = {}
    for sc in SCEN:
        n, o = res["scenarios"][sc]["B2_QV1"], res["scenarios"][sc]["B2"]
        cn, co, ln, lo = n["convergence"], o["convergence"], n["limits"], o["limits"]
        crit[sc] = {"qset_drift_20s_new_over_old": cn["qset_drift_20s_max_abs_pu"] / max(co["qset_drift_20s_max_abs_pu"], 1e-12), "unit_V_error_new_over_old": cn["unit_voltage_mean_abs_error_to_1pu"] / max(co["unit_voltage_mean_abs_error_to_1pu"], 1e-12),
                    "new_limit_crossings": sorted(set(ln["units_crossing_a_limit"]) - set(lo["units_crossing_a_limit"])), "freq_final_error_change_hz": abs(cn["frequency_final_error_hz"]) - abs(co["frequency_final_error_hz"])}
    c = crit
    ok = (all(c[s]["qset_drift_20s_new_over_old"] <= 0.70 for s in ("P+", "Q+")) and all(c[s]["unit_V_error_new_over_old"] <= 1.10 for s in SCEN) and all(not c[s]["new_limit_crossings"] for s in SCEN)
          and all(c[s]["freq_final_error_change_hz"] <= 1e-4 for s in SCEN) and c["S0"]["qset_drift_20s_new_over_old"] <= 1.0)
    res["criteria"] = crit
    res["improves_by_declared_criteria"] = bool(ok)
    (A / "IEEE39_DEC050_B_summary.json").write_text(json.dumps(res, indent=2, default=float), encoding="utf-8")
    fig, ax = plt.subplots(3, 4, figsize=(21, 13))
    for r, sc in enumerate(SCEN):
        d_n, d_o = raw[sc], base[f"R35_040_B2 {sc}"]
        for d, ls, lab in ((d_o, "-", "B2"), (d_n, "--", "B2_QV1")):
            ax[r, 0].plot(d["time_s"], (d["bus_frequency_hz"].mean(axis=1) - 60.0) * 1e3, ls, label=lab)
            p, q, v = E10.unit_arrays(d)
            ax[r, 1].plot(d["time_s"], np.abs(v - 1.0).mean(axis=1), ls, label=lab)
            ax[r, 2].plot(d["cmd_t"], np.abs(np.gradient(d["cmd_qset"], d["cmd_t"], axis=0)).max(axis=1), ls, label=lab)
            ax[r, 3].plot(d["cmd_t"], (d["cmd_qset"] - d["cmd_qset"][0])[:, [1, 6]], ls, lw=.9)
        ax[r, 0].set_title(f"{sc}: frequency deviation [mHz]"); ax[r, 1].set_title(f"{sc}: mean |V_unit - 1| [pu]"); ax[r, 2].set_title(f"{sc}: max |dQset/dt| [pu/s]"); ax[r, 2].set_yscale("log")
        ax[r, 3].set_title(f"{sc}: Qset - Qset(0), SG31 and GFM32 (solid B2, dashed QV1)")
        ax[r, 0].legend(fontsize=7)
    for a in ax.ravel():
        a.grid(alpha=.25)
    fig.suptitle("DEC-050 B: B2 vs B2_QV1 (capability-factor floor in the voltage term) on C2t_Vsafe_R35_040"); fig.tight_layout()
    fig.savefig(FIGURES_DIR / "IEEE39_DEC050_B_qv1.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    print(json.dumps({"criteria": crit, "improves": ok}, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
