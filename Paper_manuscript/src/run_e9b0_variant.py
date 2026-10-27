"""E9-B0: joint initial condition C2t_Vsafe (safe-voltage equilibrium with the preventive SG31 reserve it already carries).

The variant is the B3-A d = 0 AC solution imposed through PV p0 / v0 before the power flow (run_e9a_hocbf.vsafe_hook); the case file, the
ratings (Sn, case pmax/qmin/qmax), the gains, the graph, the actuator maps and the perturbations are the ones of C2t / E8.  This script

  1. records the complete initial condition (dispatch, physical powers, effective actuator references, 39 bus voltages),
  2. verifies the AC/DAE initialization, a 20 s flat run, the nodal power balance and the continuity of the dynamic states,
  3. runs B2 (original RDC, no QP) from this condition in S0, P+ (+58.564 MW, bus 4, t = 5 s) and Q+ (+17.345 MVAr, bus 21), and
  4. evaluates the transient P/Q/S margins of the ten units.

No redispatch is applied here: a minimal incremental redispatch is computed only if a limit is violated (decision of the investigator, DEC-044),
and the variant is frozen (hashes) before any comparison between controllers.
"""

from __future__ import annotations

import json
import os
import platform
from pathlib import Path
from typing import Any

os.environ["C2_VARIANT"] = "C2t"

import andes
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import run_b3_ieee39 as b  # noqa: E402
import run_e7_ieee39 as e7  # noqa: E402
import run_e8_ieee39 as e8  # noqa: E402
import select_equilibrium_b3 as b3  # noqa: E402
from run_e0_ieee39 import ARTIFACTS_DIR, FIGURES_DIR, git_commit, sha256  # noqa: E402
from run_e9a_hocbf import V1_JSON  # noqa: E402
from e9b_variant import DELTA, HOOK, TAG, VARIANT  # noqa: E402

OUT_JSON = ARTIFACTS_DIR / f"IEEE39_E9B0_variant{TAG}.json"
SERIES = ARTIFACTS_DIR / f"IEEE39_E9B0_Vsafe{TAG}_series.npz"
FIG = FIGURES_DIR / f"IEEE39_E9B0_margins{TAG}.png"
EVENT = e8.EVENT_TIME_S
V_BAND = (0.95, 1.05)
FLAT_S = 20.0


def build(hook, scenario="S0", tf: float | None = None):
    system, ctx = e8.configure(scenario, e8.TIME_STEP_S)
    if hook is not None:
        hook(system, ctx)
    if tf is not None:
        system.TDS.config.tf = tf
    return system, ctx


def initial_condition() -> dict[str, Any]:
    system, ctx = build(HOOK)
    system.PFlow.run()
    pflow_res = float(np.abs(system.dae.g).max())
    system.TDS.init()
    y = system.dae.y
    unit_bus, n_sg, lim = ctx["unit_bus"], ctx["n_sg"], ctx["lim"]
    names = [("SG" if i < n_sg else "GFM") + str(bb) for i, bb in enumerate(unit_bus)]
    bus_idx = [int(x) for x in system.Bus.idx.v]
    vb = np.asarray(y[np.asarray(system.Bus.v.a)], float)
    ang = np.asarray(y[np.asarray(system.Bus.a.a)], float)
    p = np.concatenate([np.asarray(y[system.GENROU.Pe.a], float), np.asarray(y[system.REGF1.Pe.a], float)])
    q = np.concatenate([np.asarray(y[system.GENROU.Qe.a], float), np.asarray(y[system.REGF1.Qe.a], float)])
    vu = np.array([vb[bus_idx.index(x)] for x in unit_bus])
    v1 = json.loads(V1_JSON.read_text(encoding="utf-8"))["scenarios"]["S0"]
    # nodal balance with an independent loss computation: loss = Re sum_i V_i conj((Y V)_i)
    yb, bus, pl, ql = b3.network(system)
    vc = vb * np.exp(1j * ang)
    s_inj = vc * np.conj(yb @ vc)
    loss_net = float(s_inj.real.sum())
    pgen, pload = float(p.sum()), float(np.sum(system.PQ.p0.v))
    tab = []
    for i, nm in enumerate(names):
        row = {"unit": nm, "bus": unit_bus[i], "P_pu": float(p[i]), "Q_pu": float(q[i]), "V_bus_pu": float(vu[i]), "pmax_pu": float(lim["pmax"][i]), "qmin_pu": float(lim["qmin"][i]),
               "qmax_pu": float(lim["qmax"][i]), "Sn_pu": float(lim["smax"][i]), "P_margin_to_pmax_pu": float(lim["pmax"][i] - p[i]),
               "P_margin_fraction_of_range": float((lim["pmax"][i] - p[i]) / (lim["pmax"][i] - lim["pmin"][i])), "Q_margin_to_qmax_pu": float(lim["qmax"][i] - q[i]),
               "Q_margin_to_qmin_pu": float(q[i] - lim["qmin"][i]), "S_rel_margin": float(1 - np.hypot(p[i], q[i]) / lim["smax"][i]),
               "AC_selection_P_star_pu": float(v1["P_star"][v1_idx(i, unit_bus)]) if False else float(v1["P_star"][i]), "AC_selection_Q_star_pu": float(v1["Q_star"][i]),
               "AC_selection_V_star_pu": float(v1["V_star"][i])}
        if i < n_sg:
            row.update({"governor_pref_pu": float(system.TGOV1N.pref.v[ctx["tg_pos"][i]]), "exciter_vref_pu": float(system.IEEEX1.vref.v[ctx["ex_pos"][i]]), "Pset_pu": float(p[i]),
                        "Qset_pu": float(q[i]), "TGOV1N_paux0": float(system.TGOV1N.paux0.v[ctx["tg_pos"][i]]), "IEEEX1_vref0": float(system.IEEEX1.vref0.v[ctx["ex_pos"][i]])})
        else:
            j = i - n_sg
            row.update({"REGF1_vref_pu": float(system.REGF1.vref.v[j]), "PIplim_y_pu": float(y[np.asarray(system.REGF1.PIplim_y.a)[j]]),
                        "PIqlim_y_pu": float(y[np.asarray(system.REGF1.PIqlim_y.a)[j]]), "Pset_pu": float(p[i]), "Qset_pu": float(q[i]),
                        "REGF1_Paux0": float(system.REGF1.Paux0.v[j]), "REGF1_Qaux0": float(system.REGF1.Qaux0.v[j]), "REGF1_internal_Pmax_pu": float(system.REGF1.Pmax.v[j])})
        tab.append(row)
    return {"units": tab, "bus_voltages_39": [{"bus": bb, "V_pu": float(v), "angle_rad": float(a), "in_band": bool(V_BAND[0] <= v <= V_BAND[1])} for bb, v, a in zip(bus_idx, vb, ang)],
            "bus_voltage_min_pu": float(vb.min()), "bus_voltage_max_pu": float(vb.max()), "n_buses_outside_band": int(((vb < V_BAND[0]) | (vb > V_BAND[1])).sum()),
            "pflow_residual": pflow_res, "init_max_abs_f": float(np.abs(system.dae.f).max()), "init_max_abs_g": float(np.abs(system.dae.g).max()),
            "power_balance": {"sum_P_gen_pu": pgen, "sum_P_load_pu": pload, "loss_from_generation_minus_load_pu": pgen - pload, "loss_from_Ybus_pu": loss_net,
                              "residual_pu": abs(pgen - pload - loss_net)},
            "max_abs_unit_P_dev_vs_AC_selection_pu": float(np.abs(p - np.array(v1["P_star"])).max()), "max_abs_unit_Q_dev_vs_AC_selection_pu": float(np.abs(q - np.array(v1["Q_star"])).max()),
            "max_abs_unit_V_dev_vs_AC_selection_pu": float(np.abs(vu - np.array(v1["V_star"])).max())}


def v1_idx(i, unit_bus):
    return i


def flat_run() -> dict[str, Any]:
    system, ctx = build(HOOK, tf=FLAT_S)
    system.TDS.callpert = lambda t, s: None      # no controller, no event: plant only
    ok = bool(system.PFlow.run()) and bool(system.TDS.run(no_summary=True))
    y, x, t = system.dae.ts.y, np.asarray(system.dae.ts.x), np.asarray(system.dae.ts.t)
    f = np.asarray(y[:, system.BusFreq.f.a]) * 60.0
    return {"converged": ok, "t_end_s": float(t[-1]), "n_steps": int(len(t)), "max_abs_frequency_drift_hz": float(np.abs(f - 60.0).max()),
            "max_abs_voltage_drift_pu": float(np.abs(y[:, system.Bus.v.a] - y[0, system.Bus.v.a]).max()),
            "max_abs_dynamic_state_drift": float(np.abs(x - x[0]).max()), "max_abs_unit_P_drift_pu": float(np.abs(y[:, system.GENROU.Pe.a] - y[0, system.GENROU.Pe.a]).max()),
            "max_abs_state_step_change": float(np.abs(np.diff(x, axis=0)).max()), "final_residual": float(np.abs(system.dae.g).max())}


def continuity(system, t_event=EVENT) -> dict[str, Any]:
    """Differential states must be continuous at the event and at t = 0; only algebraic variables may jump."""
    x = np.asarray(system.dae.ts.x)
    t = np.asarray(system.dae.ts.t)
    dx = np.abs(np.diff(x, axis=0))
    i_ev = int(np.searchsorted(t, t_event))
    win = slice(max(i_ev - 3, 0), i_ev + 4)
    names = list(system.dae.x_name)
    phys = np.array(["IEEEST" not in n for n in names])
    dxp = dx[:, phys]
    worst = int(dxp[win].max(axis=0).argmax())
    names = [n for n, k in zip(names, phys) if k]
    return {"excluding_degenerate_IEEEST_states": {"max_abs_state_step_global": float(dxp.max()), "max_abs_state_step_window_around_event": float(dxp[win].max()),
                                                   "state_with_largest_step_around_event": names[worst], "n_states": int(phys.sum())},
            "note": "the degenerate IEEEST blocks (A1 = A2 = 0, DEC-013) carry large non-physical states that are excluded from the physical continuity check",
            "max_abs_state_step_global": float(dx.max()), "max_abs_state_step_window_around_event": float(dx[win].max()), "max_abs_state_step_first_10_samples": float(dx[:10].max()), "max_abs_state_step_after_event_window": float(dx[i_ev + 4:].max()) if i_ev + 4 < len(dx) else None}


def margins(d: dict[str, np.ndarray], lim: dict[str, np.ndarray], names: list[str]) -> dict[str, Any]:
    t = d["time_s"]
    p, q, v = e7.unit_series(None, d)
    out: dict[str, Any] = {"units": names}
    rec = {}
    for i, n in enumerate(names):
        rec[n] = {"max_P_pu": float(p[:, i].max()), "t_max_P_s": float(t[p[:, i].argmax()]), "min_P_pu": float(p[:, i].min()), "max_Q_pu": float(q[:, i].max()), "min_Q_pu": float(q[:, i].min()),
                  "max_S_pu": float(np.hypot(p[:, i], q[:, i]).max()), "min_P_margin_to_pmax_pu": float((lim["pmax"][i] - p[:, i]).min()),
                  "min_Q_margin_to_qmax_pu": float((lim["qmax"][i] - q[:, i]).min()), "min_Q_margin_to_qmin_pu": float((q[:, i] - lim["qmin"][i]).min()),
                  "min_S_rel_margin": float((1 - np.hypot(p[:, i], q[:, i]) / lim["smax"][i]).min()),
                  "P_violation_pu": float(max(0.0, p[:, i].max() - lim["pmax"][i])), "P_below_pmin_pu": float(max(0.0, lim["pmin"][i] - p[:, i].min())),
                  "Q_violation_pu": float(max(0.0, q[:, i].max() - lim["qmax"][i], lim["qmin"][i] - q[:, i].min())),
                  "S_violation_pu": float(max(0.0, np.hypot(p[:, i], q[:, i]).max() - lim["smax"][i]))}
    out["per_unit"] = rec
    vb = d["bus_voltage_pu"]
    out["bus_voltage"] = {"min_pu": float(vb.min()), "max_pu": float(vb.max()), "n_buses_ever_outside_band": int(((vb < V_BAND[0]) | (vb > V_BAND[1])).any(axis=0).sum())}
    out["violating_units"] = [n for n, r in rec.items() if r["P_violation_pu"] > 0 or r["P_below_pmin_pu"] > 0 or r["Q_violation_pu"] > 0 or r["S_violation_pu"] > 0]
    f = d["bus_frequency_hz"].mean(axis=1)
    out["frequency"] = {"max_abs_dev_hz": float(np.abs(f - 60.0).max()), "nadir_hz": float(f[t >= EVENT].min())}
    return out


def main() -> int:
    ic = initial_condition()
    print("IC buses outside band:", ic["n_buses_outside_band"], "Vmax", round(ic["bus_voltage_max_pu"], 4), "balance residual", ic["power_balance"]["residual_pu"], flush=True)
    flat = flat_run()
    print("flat:", flat, flush=True)
    result: dict[str, Any] = {"variant": VARIANT, "incremental_redispatch_delta_pu": DELTA, "definition": "B3-A d = 0 AC selection (v1 S0) imposed through PV p0 / v0 before the power flow; case, ratings, gains, graph, actuators, perturbations unchanged",
                              "git_commit": git_commit(), "andes": andes.__version__, "python": platform.python_version(),
                              "initial_condition": ic, "flat_run": flat, "scenarios": {}}
    series: dict[str, np.ndarray] = {}
    names = [r["unit"] for r in ic["units"]]
    lim = e8.configure("S0", e8.TIME_STEP_S)[1]["lim"]
    for sc in ("S0", "P+", "Q+"):
        system, data, diag = b.run("B2", sc, init_hook=HOOK)
        m = margins(data, lim, names)
        m["diagnostics"] = diag
        m["continuity"] = continuity(system)
        result["scenarios"][sc] = m
        for k in ("time_s", "bus_voltage_pu", "bus_frequency_hz", "sg_p_pu", "sg_q_pu", "gfm_p_pu", "gfm_q_pu", "cmd_t", "cmd_pset", "cmd_qset", "bus_ids", "unit_bus_ids"):
            series[f"{sc}__{k}"] = np.asarray(data[k])
        print(sc, "violating:", m["violating_units"], {n: round(r["P_violation_pu"], 4) for n, r in m["per_unit"].items() if r["P_violation_pu"] > 0},
              "SG31 max P", round(m["per_unit"]["SG31"]["max_P_pu"], 4), "min margins P:", {n: round(r["min_P_margin_to_pmax_pu"], 3) for n, r in m["per_unit"].items()}, flush=True)
    np.savez_compressed(SERIES, **series)
    result["series_sha256"] = sha256(SERIES)
    result["vsafe_source_sha256"] = sha256(V1_JSON)
    result["code_sha256"] = {f: sha256(Path(__file__).parent / f) for f in ("run_e9b0_variant.py", "run_e9a_hocbf.py", "run_b3_ieee39.py", "run_e8_ieee39.py")}
    OUT_JSON.write_text(json.dumps(result, indent=2, default=float), encoding="utf-8")
    plots(result, series, names, lim)
    return 0


def plots(result, series, names, lim) -> None:
    fig, ax = plt.subplots(2, 3, figsize=(18, 9))
    for c, sc in enumerate(("S0", "P+", "Q+")):
        pm = result["scenarios"][sc]["per_unit"]
        ax[0, c].bar(range(10), [pm[n]["min_P_margin_to_pmax_pu"] for n in names]); ax[0, c].axhline(0, color="k", lw=.8)
        ax[0, c].set_xticks(range(10)); ax[0, c].set_xticklabels(names, rotation=60, fontsize=8); ax[0, c].set_title(f"{sc}: min (pmax - P) [pu]")
        ax[1, c].bar(range(10), [pm[n]["min_S_rel_margin"] for n in names], color="tab:green"); ax[1, c].set_xticks(range(10)); ax[1, c].set_xticklabels(names, rotation=60, fontsize=8)
        ax[1, c].set_title(f"{sc}: min relative S margin")
        for r in range(2):
            ax[r, c].grid(alpha=.25)
    fig.suptitle("E9-B0: C2t_Vsafe transient physical margins of the ten units under B2 (no QP)"); fig.tight_layout()
    fig.savefig(FIG, dpi=300, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())
