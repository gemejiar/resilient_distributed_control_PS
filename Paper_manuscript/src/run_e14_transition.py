"""E14 (Option B): transition between two admissible operating dispatches (slow tertiary-like change of the target equilibrium).

Both dispatches are admissible AC/DAE equilibria validated in E9-B0: A = C2t_Vsafe and B = C2t_Vsafe_R35_040 (0.040 pu moved from SG35 to the GFM).  The dispatch is changed on the running
plant, without any load event and with primary control only (no RDC, no filter), by moving the active-power references through the unchanged E8 actuator maps (SG TGOV1N.paux0, GFM Paux0
tracking of PIplim_y) with the C2 profile  sigma(s) = 10 s^3 - 15 s^4 + 6 s^5  over 30 s starting at t = 5 s (declared before running), by dP_i = P_i(B) - P_i(A) per unit, for A->B and the
reverse B->A.  Reported: residual of the physical powers with respect to the target dispatch, frequency, voltages, limit margins, largest single-step change of the physical power (no unmodelled
jumps) and the largest reference rate.  The certificate of the previous dispatch is not inherited: nothing is claimed about regions, only about these two transitions.
"""

from __future__ import annotations

import json
import os
from typing import Any

os.environ["C2_VARIANT"] = "C2t"

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import run_e8_ieee39 as e8  # noqa: E402
from e9b_variant import hook_for  # noqa: E402
from e9f_engine import quintic  # noqa: E402
from run_e0_ieee39 import ARTIFACTS_DIR as A, FIGURES_DIR, extract_time_series, git_commit  # noqa: E402

T_START, T_RAMP, HORIZON = 5.0, 30.0, 100.0


def dispatches() -> tuple[np.ndarray, np.ndarray]:
    a = json.loads((A / "IEEE39_E9B0_variant.json").read_text(encoding="utf-8"))["initial_condition"]["units"]
    b = json.loads((A / "IEEE39_E9B0_variant_R35_040.json").read_text(encoding="utf-8"))["initial_condition"]["units"]
    return np.array([u["P_pu"] for u in a]), np.array([u["P_pu"] for u in b])


def simulate(delta_variant: float, dP: np.ndarray) -> dict[str, Any]:
    system, ctx = e8.configure("S0", e8.TIME_STEP_S)
    hook_for(delta_variant)(system, ctx)
    system.TDS.config.tf = HORIZON
    n_sg = ctx["n_sg"]
    st: dict[str, Any] = {"init": False, "last": -1.0}
    log: dict[str, list] = {"t": [], "u": []}

    def cb(t, sys_):
        t = float(t)
        y = sys_.dae.y
        if not st["init"]:
            st["a_y"], st["a_yq"] = np.asarray(sys_.REGF1.PIplim_y.a), np.asarray(sys_.REGF1.PIqlim_y.a)
            st["y0"], st["y0q"] = np.asarray(y[st["a_y"]], float).copy(), np.asarray(y[st["a_yq"]], float).copy()
            st["vref0"] = np.asarray(sys_.IEEEX1.vref0.v, float).copy()
            st["init"] = True
        if t <= st["last"]:
            return
        st["last"] = t
        u = dP * quintic((t - T_START) / T_RAMP)[0]
        sys_.TGOV1N.paux0.v[ctx["tg_pos"]] = u[:n_sg]
        sys_.REGF1.Paux0.v[:] = e8.KC_GFM * (st["y0"] + u[n_sg:] - np.asarray(y[st["a_y"]], float))
        sys_.IEEEX1.vref0.v[ctx["ex_pos"]] = st["vref0"][ctx["ex_pos"]]
        sys_.REGF1.Qaux0.v[:] = e8.KCQ_GFM * (st["y0q"] - np.asarray(y[st["a_yq"]], float))
        log["t"].append(t); log["u"].append(u.copy())

    system.TDS.callpert = cb
    ok = bool(system.PFlow.run()) and bool(system.TDS.run(no_summary=True))
    d = extract_time_series(system)
    yy = system.dae.ts.y
    p = np.hstack([np.asarray(yy[:, system.GENROU.Pe.a], float), np.asarray(yy[:, system.REGF1.Pe.a], float)])
    q = np.hstack([np.asarray(yy[:, system.GENROU.Qe.a], float), np.asarray(yy[:, system.REGF1.Qe.a], float)])
    return {"ok": ok, "t": d["time_s"], "p": p, "q": q, "vbus": d["bus_voltage_pu"], "f": d["bus_frequency_hz"].mean(axis=1), "lim": ctx["lim"], "residual": float(np.abs(system.dae.g).max()),
            "u_t": np.array(log["t"]), "u": np.array(log["u"])}


def metrics(name: str, r: dict[str, Any], p_target: np.ndarray) -> dict[str, Any]:
    t, p, q, vb, f, lim = r["t"], r["p"], r["q"], r["vbus"], r["f"], r["lim"]
    fin = t >= t[-1] - 10
    pre = (t >= T_START - 1) & (t < T_START)
    s_rel = 1 - np.hypot(p, q) / lim["smax"]
    viol = [i for i in range(10) if (p[:, i].max() > lim["pmax"][i] or p[:, i].min() < lim["pmin"][i] or q[:, i].max() > lim["qmax"][i] or q[:, i].min() < lim["qmin"][i] or s_rel[:, i].min() < 0)]
    du = np.abs(np.diff(r["u"], axis=0) / np.diff(r["u_t"])[:, None]).max(axis=0)
    return {"transition": name, "tds_ok": r["ok"], "t_end_s": float(t[-1]), "final_residual_dae": r["residual"], "max_abs_P_error_vs_target_pu": float(np.abs(p[fin].mean(axis=0) - p_target).max()),
            "P_error_by_unit_pu": (p[fin].mean(axis=0) - p_target).tolist(), "max_abs_P_change_commanded_pu": float(np.abs(p_target - p[pre].mean(axis=0)).max()),
            "frequency_max_dev_hz": float(np.abs(f - 60.0).max()), "frequency_final_error_hz": float(f[fin].mean() - 60.0), "bus_voltage_min_pu": float(vb.min()), "bus_voltage_max_pu": float(vb.max()),
            "n_buses_outside_0.95_1.05": int(((vb < 0.95) | (vb > 1.05)).any(axis=0).sum()), "violating_units": viol, "min_P_margin_to_pmax_pu": (lim["pmax"] - p).min(axis=0).tolist(),
            "max_single_step_change_P_pu": float(np.abs(np.diff(p, axis=0)).max()), "max_single_step_change_V_pu": float(np.abs(np.diff(vb, axis=0)).max()), "max_reference_rate_pu_per_s": float(du.max()),
            "total_P_change_sum_pu": float((p[fin].mean(axis=0) - p[pre].mean(axis=0)).sum())}


def main() -> int:
    pa, pb = dispatches()
    dP = pb - pa
    res = {"stage": "E14", "git_commit": git_commit(), "profile": "quintic C2, 30 s from t = 5 s", "dispatch_change_pu": dP.tolist(), "dispatch_A_P_pu": pa.tolist(), "dispatch_B_P_pu": pb.tolist(), "runs": {}}
    fa = simulate(0.0, dP)
    fb = simulate(0.040, -dP)
    res["runs"]["A_to_B (C2t_Vsafe -> C2t_Vsafe_R35_040)"] = metrics("A_to_B", fa, pb)
    res["runs"]["B_to_A (C2t_Vsafe_R35_040 -> C2t_Vsafe)"] = metrics("B_to_A", fb, pa)
    (A / "IEEE39_E14_transition.json").write_text(json.dumps(res, indent=2, default=float), encoding="utf-8")
    fig, ax = plt.subplots(2, 3, figsize=(19, 9))
    names = ["SG30", "SG31", "SG33", "SG35", "SG38", "SG39", "GFM32", "GFM37", "GFM34", "GFM36"]
    for r, ls, lab, target in ((fa, "-", "A->B", pb), (fb, "--", "B->A", pa)):
        t = r["t"]
        ax[0, 0].plot(t, (r["f"] - 60.0) * 1e3, ls, label=lab)
        ax[0, 1].plot(t, r["vbus"].max(axis=1), ls, label=f"{lab} max"); ax[0, 1].plot(t, r["vbus"].min(axis=1), ls, lw=.8, label=f"{lab} min")
        for i in (3, 9):
            ax[0, 2].plot(t, r["p"][:, i] - target[i], ls, label=f"{lab} {names[i]} P - P_target")
        ax[1, 0].plot(t, (r["lim"]["pmax"] - r["p"]).min(axis=1), ls, label=f"{lab} min(pmax-P)")
        ax[1, 1].plot(r["u_t"], r["u"][:, 3], ls, label=f"{lab} SG35 reference")
    ax[0, 0].set_title("frequency deviation [mHz]"); ax[0, 1].set_title("39-bus voltage extremes"); ax[0, 2].set_title("physical P minus target dispatch [pu]")
    ax[1, 0].set_title("minimum P margin to pmax over the ten units [pu]"); ax[1, 1].set_title("SG35 active-power reference [pu]")
    x = np.arange(10)
    ax[1, 2].bar(x - 0.2, res["runs"]["A_to_B (C2t_Vsafe -> C2t_Vsafe_R35_040)"]["P_error_by_unit_pu"], 0.4, label="A->B final P error")
    ax[1, 2].bar(x + 0.2, res["runs"]["B_to_A (C2t_Vsafe_R35_040 -> C2t_Vsafe)"]["P_error_by_unit_pu"], 0.4, label="B->A")
    ax[1, 2].set_xticks(x); ax[1, 2].set_xticklabels(names, rotation=60, fontsize=7); ax[1, 2].set_title("final physical P minus target [pu] (SG armature losses included)")
    for a in ax.ravel():
        a.grid(alpha=.25)
    for a in (ax[0, 0], ax[0, 1], ax[0, 2], ax[1, 0], ax[1, 1], ax[1, 2]):
        a.legend(fontsize=6)
    fig.suptitle("E14: smooth transition between two admissible dispatches (primary control only, E8 actuator maps)"); fig.tight_layout()
    fig.savefig(FIGURES_DIR / "IEEE39_E14_transition.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    for k, m in res["runs"].items():
        print(k, {x: (round(v, 5) if isinstance(v, float) else v) for x, v in m.items() if x in ("tds_ok", "max_abs_P_error_vs_target_pu", "frequency_max_dev_hz", "bus_voltage_min_pu", "bus_voltage_max_pu", "violating_units", "max_single_step_change_P_pu", "max_reference_rate_pu_per_s")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
