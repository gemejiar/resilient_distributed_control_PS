"""DEC-051 block C1-C3 (no dynamic simulation): audit of the instantaneous algebraic jump and the preventive-reserve inequality.

For each configuration (C2t; C2t with only the Vsafe voltage set-points; C2t with only the Vsafe active-power dispatch; C2t_Vsafe; C2t_Vsafe_R35 (0.015); C2t_Vsafe_R35_040) the pre-event
ANDES state is initialised (power flow + TDS init, no time stepping).  A load step (P+ at bus 4 or Q+ at bus 21, and the amplitude grid below) is applied with ALL differential states held
continuous; the quasi-algebraic states and the algebraic variables are re-solved from g = 0 (Newton, exact ANDES Jacobians).  This gives the physical powers at t = 0+ of every unit.
Reserve  R_i = Pmax_i - P_i(pre);  jump  dP_i^jump(a) = P_i(0+) - P_i(pre);  slow excursion  dP_i^exc = max_t P_i(t) - P_i(0+)  (empirical, from the stored 200 s series of the same event).
Preventive inequality (declared):   R_i >= dP_i^jump(a) + dP_i^exc(a) + eps_i ,  eps_i = discrepancy between the algebraic prediction and the first stored simulation sample (jump) and 0 for the excursion
(an empirical term, scaled linearly with a: declared hypothesis, tested by the 110 % simulation).  Bound classes: jump = 'conservative, computed on the declared amplitude grid, monotonicity checked on the grid';
excursion = 'empirical'.  Nothing here is a universal bound."""

from __future__ import annotations

import csv
import json
import os

os.environ["C2_VARIANT"] = "C2t"

import numpy as np

import dec051_core as C
import run_e8_ieee39 as e8
from e9b_variant import hook_for
from run_e0_ieee39 import ARTIFACTS_DIR as A, git_commit, sha256
from run_e9a_hocbf import V1_JSON, vsafe_hook

NAMES = ["SG30", "SG31", "SG33", "SG35", "SG38", "SG39", "GFM32", "GFM37", "GFM34", "GFM36"]
GRID = (0.25, 0.5, 0.75, 1.0, 1.1, 1.25, 1.5)
P_STEP_PU, Q_STEP_PU = 0.58564, 0.17345


def hook_variant(volt: bool, disp: bool):
    def hook(system, ctx):
        d = json.loads(V1_JSON.read_text(encoding="utf-8"))["scenarios"]["S0"]
        p_star, v_star, unit_bus = np.array(d["P_star"]), np.array(d["V_star"]), json.loads(V1_JSON.read_text(encoding="utf-8"))["unit_bus_order"]
        pos = {bb: i for i, bb in enumerate(unit_bus)}
        for model in ("PV", "Slack"):
            dev = getattr(system, model)
            for k, bb in enumerate(dev.bus.v):
                if volt:
                    dev.v0.v[k] = v_star[pos[int(bb)]]
                if disp and model == "PV":
                    dev.p0.v[k] = p_star[pos[int(bb)]]
    return hook


CONFIGS = {"C2t": lambda s, c: None, "C2t + Vsafe voltages only": hook_variant(True, False), "C2t + Vsafe dispatch only": hook_variant(False, True), "C2t_Vsafe": vsafe_hook,
           "C2t_Vsafe_R35 (0.015)": hook_for(0.015), "C2t_Vsafe_R35_040": hook_for(0.040)}


def make(hook):
    system, ctx = e8.configure("S0", e8.TIME_STEP_S)
    if hook is not None:
        hook(system, ctx)
    system.PFlow.run()
    system.TDS.init()
    return system, ctx


def jump(system, ctx, st, ix, cache, bus, dp, dq):
    x_keep, y_keep = np.array(system.dae.x), np.array(system.dae.y)
    k = [int(b) for b in system.PQ.bus.v].index(bus)
    p0, q0 = float(system.PQ.Ppf.v[k]), float(system.PQ.Qpf.v[k])
    system.PQ.Ppf.v[k] = p0 + dp
    system.PQ.Qpf.v[k] = q0 + dq
    u_nom = np.concatenate([st["pn"], st["qn"]])
    info = C.inner_solve(system, ctx, st, u_nom, ix, cache, tol=1e-11, itmax=40)
    y = system.dae.y
    out = {"P": np.asarray(y[st["a_p"]], float).copy(), "Q": np.asarray(y[st["a_q"]], float).copy(), "V": np.asarray(y[st["a_v"]], float).copy(),
           "Vbus": np.asarray(y[np.asarray(system.Bus.v.a)], float).copy(), "converged": info["converged"], "residual": info["residual_history"][-1]}
    system.PQ.Ppf.v[k], system.PQ.Qpf.v[k] = p0, q0
    C.set_state(system, x_keep, y_keep)
    return out


def trajectory_peaks():
    """Peak physical P of every unit after the event, from the stored 200 s P+ series (historical runs); None when absent."""
    out = {}
    e8s = np.load(A / "IEEE39_E8_C2t_timeseries.npz")
    out["C2t"] = {"t": e8s["P+_time_s"], "p": np.hstack([e8s["P+_sg_p_pu"], e8s["P+_gfm_p_pu"]])}
    for name, f in (("C2t_Vsafe", "IEEE39_E9B0_Vsafe_series.npz"), ("C2t_Vsafe_R35 (0.015)", "IEEE39_E9B0_Vsafe_R35_series.npz"), ("C2t_Vsafe_R35_040", "IEEE39_E9B0_Vsafe_R35_040_series.npz")):
        z = np.load(A / f)
        out[name] = {"t": z["P+__time_s"], "p": np.hstack([z["P+__sg_p_pu"], z["P+__gfm_p_pu"]])}
    return out


def main() -> int:
    peaks = trajectory_peaks()
    res: dict = {"stage": "DEC-051 H3 C1-C3", "git_commit": git_commit(), "doc": __doc__, "configs": {}}
    rows = []
    for name, hook in CONFIGS.items():
        system, ctx = make(hook)
        st = C.rdc_state(system, ctx)
        ix = C.index_sets(system)
        cache: dict = {}
        C.apply_params(system, ctx, st, np.concatenate([st["pn"], st["qn"]]))
        C.L.linearize(system, ctx, cache=cache)
        lim = ctx["lim"]
        pre = {"P": st["pn"].copy(), "Q": st["qn"].copy()}
        cfg = {"P_pre": pre["P"].tolist(), "reserve_P": (lim["pmax"] - pre["P"]).tolist(), "Q_pre": pre["Q"].tolist(), "bus_voltage_pre_max": float(np.asarray(system.dae.y[np.asarray(system.Bus.v.a)]).max()), "events": {}}
        for kind, bus, step in (("P+", 4, P_STEP_PU), ("Q+", 21, Q_STEP_PU)):
            ev = {}
            for g in GRID:
                j = jump(system, ctx, st, ix, cache, bus, step * g if kind == "P+" else 0.0, step * g if kind == "Q+" else 0.0)
                dP = j["P"] - pre["P"]
                s = np.hypot(j["P"], j["Q"])
                ev[f"{g:g}"] = {"amplitude": g * step * 100.0, "converged": j["converged"], "residual": j["residual"], "dP_jump": dP.tolist(), "P_post": j["P"].tolist(), "Q_post": j["Q"].tolist(),
                                "margin_P_post": (lim["pmax"] - j["P"]).tolist(), "margin_Q_post_max": (lim["qmax"] - j["Q"]).tolist(), "margin_Q_post_min": (j["Q"] - lim["qmin"]).tolist(),
                                "margin_S_post": (lim["smax"] - s).tolist(), "bus_voltage_min_max": [float(j["Vbus"].min()), float(j["Vbus"].max())]}
                for i, n in enumerate(NAMES):
                    rows.append([name, kind, g * step * 100.0, n, pre["P"][i], lim["pmax"][i] - pre["P"][i], dP[i], j["P"][i], lim["pmax"][i] - j["P"][i], j["Q"][i], lim["qmax"][i] - j["Q"][i], lim["smax"][i] - s[i]])
            # monotonicity of the jump in the amplitude (grid check)
            arr = np.array([ev[f"{g:g}"]["dP_jump"] for g in GRID])
            ev["monotone_on_grid"] = bool(np.all(np.diff(arr, axis=0) * np.sign(arr[-1])[None, :] >= -1e-9))
            cfg["events"][kind] = ev
        if name in peaks:
            t, p = peaks[name]["t"], peaks[name]["p"]
            post = t > 5.0 + 1e-9                      # samples strictly after the load step
            pk = p[post].max(axis=0)
            fast = (t > 5.0 + 1e-9) & (t <= 5.05)     # subtransient / first electromechanical phase (<= 50 ms, declared)
            slow = t > 5.05
            ex = np.array(cfg["events"]["P+"]["1"]["P_post"])
            cfg["observed_P+_peak"] = pk.tolist()
            cfg["observed_P+_margin_min"] = (lim["pmax"] - pk).tolist()
            cfg["observed_first_sample_after_event"] = p[post][0].tolist()
            cfg["observed_t_first_sample_after_event"] = float(t[post][0])
            cfg["observed_peak_fast_phase"] = p[fast].max(axis=0).tolist()
            cfg["observed_peak_slow_phase"] = p[slow].max(axis=0).tolist()
            cfg["observed_fast_increment_over_jump"] = (p[fast].max(axis=0) - ex).tolist()
            cfg["observed_slow_increment_over_jump"] = (p[slow].max(axis=0) - ex).tolist()
            cfg["observed_t_of_peak"] = [float(t[post][np.argmax(p[post][:, i])]) for i in range(10)]
            cfg["jump_prediction_vs_first_sample_max_abs"] = float(np.abs(ex - p[post][0]).max())
            cfg["jump_prediction_vs_first_sample_by_unit"] = (ex - p[post][0]).tolist()
        res["configs"][name] = cfg
    res["inputs_sha256"] = {"V1_JSON": sha256(V1_JSON)}
    (A / "IEEE39_DEC051_H3_jump.json").write_text(json.dumps(res, indent=2, default=float), encoding="utf-8")
    with (A / "IEEE39_DEC051_safety_margins.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["config", "event", "amplitude_MW_or_MVAr", "unit", "P_pre_pu", "reserve_P_pu", "dP_jump_pu", "P_post_jump_pu", "margin_P_post_jump_pu", "Q_post_jump_pu", "margin_Qmax_post_jump_pu", "margin_S_post_jump_pu"])
        w.writerows(rows)
    sg31, sg35 = NAMES.index("SG31"), NAMES.index("SG35")
    for name, cfg in res["configs"].items():
        e = cfg["events"]["P+"]["1"]
        print(name, "| R31 %.4f R35 %.4f | jump31 %.4f jump35 %.4f | margin_post31 %.4f margin_post35 %.4f" % (cfg["reserve_P"][sg31], cfg["reserve_P"][sg35], e["dP_jump"][sg31], e["dP_jump"][sg35], e["margin_P_post"][sg31], e["margin_P_post"][sg35]),
              "| obs min margin", [round(cfg["observed_P+_margin_min"][i], 4) for i in (sg31, sg35)] if "observed_P+_margin_min" in cfg else None, "| pred-vs-sample", cfg.get("jump_prediction_vs_first_sample_max_abs"), "| monotone", cfg["events"]["P+"]["monotone_on_grid"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
