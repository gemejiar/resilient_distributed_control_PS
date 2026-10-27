"""E9-A SG31 authority audit on C2t (open-loop tests, no controller, no QP in the loop).

(1) Single-channel reference steps: a step of +0.05 pu (P channels) or +0.2 pu (Q channels) on one reference at the event instant
    (t = 5 s, together with the +58.564 MW load step), through the unchanged E8 actuator maps; the difference with the no-reference
    baseline is the step response of every physical output to that channel (small-signal; superposition is used only to reason about
    authority).
(2) Preventive redispatch: SG31 pre-event P lowered by delta and the same amount moved to the other PV units (proportional to headroom,
    or to the GFM only); PV p0 is modified before the power flow exactly as in the B3 selection scripts, the case file is never changed.
Both use primary control only (Pset = Pn), the plant C2t, the original perturbation and the E8 step size.  Outputs: JSON + figure.
"""

from __future__ import annotations

import json
import os
import platform
from typing import Any

os.environ["C2_VARIANT"] = "C2t"

import andes
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import run_e8_ieee39 as e8  # noqa: E402
from run_e0_ieee39 import ARTIFACTS_DIR, FIGURES_DIR, extract_time_series, git_commit  # noqa: E402

OUT_JSON = ARTIFACTS_DIR / "IEEE39_E9A_sg31_authority.json"
FIG = FIGURES_DIR / "IEEE39_E9A_sg31_authority.png"
EVENT = e8.EVENT_TIME_S
HORIZON_S = 40.0
STEP_P, STEP_Q = 0.05, 0.2
DELTAS = (0.05, 0.07, 0.08, 0.10, 0.15)
RESPONSE_TIMES = (0.004, 0.05, 0.15, 0.5, 1.0, 2.0, 2.7, 5.0, 10.0)
V_RATE_OBSERVED = 0.616   # pu/s: largest dPset/dt produced by the original RDC in P+ (E8); an observed rate, not a hardware limit


def simulate(scenario: str = "P+", step: tuple[int, float] | None = None, redispatch: tuple[float, str] | None = None, horizon: float = HORIZON_S):
    """Primary control only; optional single-reference step (channel index 0..19, size) at the event; optional preventive redispatch."""
    system, ctx = e8.configure(scenario, e8.TIME_STEP_S)
    system.TDS.config.tf = horizon
    n_sg, unit_bus = ctx["n_sg"], ctx["unit_bus"]
    lim = ctx["lim"]
    info: dict[str, Any] = {}
    if redispatch is not None:
        delta, mode = redispatch
        pv_p0 = {int(b): k for k, b in enumerate(system.PV.bus.v)}
        pn_case = {b: float(system.PV.p0.v[k]) for b, k in pv_p0.items()}
        head = {b: max(lim["pmax"][unit_bus.index(b)] - pn_case[b], 0.0) for b in pv_p0 if b != 31 and (mode == "all" or b in (32, 34, 36, 37))}
        tot = sum(head.values())
        system.PV.p0.v[pv_p0[31]] -= delta
        for b, h in head.items():
            system.PV.p0.v[pv_p0[b]] += delta * h / tot
        info["share_pu"] = {int(b): float(delta * h / tot) for b, h in head.items()}
    st: dict[str, Any] = {"init": False, "last_t": -1.0}

    def cb(t, sys_):
        t = float(t)
        y = sys_.dae.y
        if not st["init"]:
            st["a_p"] = np.concatenate([np.asarray(sys_.GENROU.Pe.a), np.asarray(sys_.REGF1.Pe.a)])
            st["a_y"], st["a_yq"] = np.asarray(sys_.REGF1.PIplim_y.a), np.asarray(sys_.REGF1.PIqlim_y.a)
            st["y0"], st["y0q"] = np.asarray(y[st["a_y"]], float).copy(), np.asarray(y[st["a_yq"]], float).copy()
            st["vref0_sg"] = np.asarray(sys_.IEEEX1.vref0.v, float).copy()
            st["init"] = True
        if t <= st["last_t"]:
            return
        st["last_t"] = t
        dp, dq = np.zeros(10), np.zeros(10)
        if step is not None and t >= EVENT:
            ch, size = step
            (dp if ch < 10 else dq)[ch % 10] = size
        sys_.TGOV1N.paux0.v[ctx["tg_pos"]] = dp[:n_sg]
        sys_.REGF1.Paux0.v[:] = e8.KC_GFM * (st["y0"] + dp[n_sg:] - np.asarray(y[st["a_y"]], float))
        z = np.clip(e8.KAPPA_SG * dq[:n_sg], -e8.Z_CLAMP, e8.Z_CLAMP)
        sys_.IEEEX1.vref0.v[ctx["ex_pos"]] = st["vref0_sg"][ctx["ex_pos"]] + z
        sys_.REGF1.Qaux0.v[:] = e8.KCQ_GFM * (st["y0q"] + dq[n_sg:] - np.asarray(y[st["a_yq"]], float))

    system.TDS.callpert = cb
    ok = bool(system.PFlow.run()) and bool(system.TDS.run(no_summary=True))
    data = extract_time_series(system)
    y = system.dae.ts.y
    p = np.hstack([np.asarray(y[:, system.GENROU.Pe.a], float), np.asarray(y[:, system.REGF1.Pe.a], float)])
    q = np.hstack([np.asarray(y[:, system.GENROU.Qe.a], float), np.asarray(y[:, system.REGF1.Qe.a], float)])
    ids = list(system.Bus.idx.v)
    v = np.asarray(data["bus_voltage_pu"])[:, [ids.index(b) for b in unit_bus]]
    return {"ok": ok, "t": data["time_s"], "p": p, "q": q, "v": v, "vbus": data["bus_voltage_pu"], "f": data["bus_frequency_hz"].mean(axis=1), "lim": lim,
            "unit_bus": unit_bus, "info": info, "final_residual": float(np.max(np.abs(system.dae.g)))}


def main() -> int:
    base = simulate()
    names = [("SG" if i < 6 else "GFM") + str(b) for i, b in enumerate(base["unit_bus"])]
    i31, i35 = names.index("SG31"), names.index("SG35")
    t, lim = base["t"], base["lim"]
    result: dict[str, Any] = {"units": names, "git_commit": git_commit(), "andes": andes.__version__, "python": platform.python_version(), "horizon_s": HORIZON_S,
                              "step_sizes": {"P_pu": STEP_P, "Q_pu": STEP_Q}, "response_times_s_after_event": list(RESPONSE_TIMES)}
    over = (base["p"][:, i31] > lim["pmax"][i31]) & (t >= EVENT)
    result["baseline_primary_only"] = {"ok": base["ok"], "peak_P31": float(base["p"][:, i31].max()), "pmax31": float(lim["pmax"][i31]),
                                       "t_first_exceed_after_event_s": float(t[over][0] - EVENT) if over.any() else None}
    resp, tab = {}, {}
    for ch in range(20):
        size = STEP_P if ch < 10 else STEP_Q
        sim = simulate(step=(ch, size))
        d31 = (sim["p"][:, i31] - base["p"][:, i31]) / size
        d35 = (sim["p"][:, i35] - base["p"][:, i35]) / size
        resp[ch] = (d31, d35)
        lab = ("Pset" if ch < 10 else "Qset") + "_" + names[ch % 10]
        tab[lab] = {"dP31_per_unit_step": {f"{tau}": float(np.interp(EVENT + tau, t, d31)) for tau in RESPONSE_TIMES},
                    "dP35_per_unit_step": {f"{tau}": float(np.interp(EVENT + tau, t, d35)) for tau in RESPONSE_TIMES}, "ok": sim["ok"]}
        print("step", lab, tab[lab]["dP31_per_unit_step"]["2.7"], flush=True)
    result["channel_step_response"] = tab
    # reduction of P31 at the slow excursion (about 2.7 s after the event) by a ramp of slope V_RATE_OBSERVED (superposition of the step response)
    ramp = {}
    for ch in range(10):
        grid = np.linspace(0.0, 2.7, 400)
        integ = float(np.trapezoid(np.interp(EVENT + grid, t, resp[ch][0]), grid))
        head = float(lim["pmax"][ch] - base["p"][t < EVENT, ch][-1])
        ramp[names[ch]] = {"dP31_at_2.7s_for_ramp_pu": V_RATE_OBSERVED * integ, "headroom_to_pmax_pu": head, "time_to_exhaust_headroom_at_observed_rate_s": head / V_RATE_OBSERVED}
    result["ramp_authority_at_t_2p7s"] = {"rate_pu_per_s": V_RATE_OBSERVED, "per_channel": ramp}
    sweep, series = {}, {}
    for mode in ("all", "gfm"):
        for dlt in DELTAS:
            sim = simulate(redispatch=(dlt, mode))
            p, q = sim["p"], sim["q"]
            tt = sim["t"]
            pre = (tt >= EVENT - 1) & (tt < EVENT)
            series[(mode, dlt)] = (tt, p[:, i31])
            rec = {"ok": sim["ok"], "final_residual": sim["final_residual"], "share_pu": sim["info"].get("share_pu", {}),
                   "pre_P_pu": p[pre].mean(axis=0).tolist(), "pre_margin_to_pmax_pu": (lim["pmax"] - p[pre].mean(axis=0)).tolist(),
                   "min_margin_to_pmax_pu": (lim["pmax"] - p).min(axis=0).tolist(), "excess_pu": np.maximum(0.0, p.max(axis=0) - lim["pmax"]).tolist(),
                   "min_Q_to_qmax_pu": (lim["qmax"] - q).min(axis=0).tolist(), "min_Q_to_qmin_pu": (q - lim["qmin"]).min(axis=0).tolist(),
                   "final_P_pu": p[tt >= tt[-1] - 2].mean(axis=0).tolist(), "bus_voltage_pre_max_pu": float(sim["vbus"][pre].mean(axis=0).max()),
                   "bus_voltage_global_min_pu": float(sim["vbus"].min()), "units_with_pmax_violation": [names[i] for i in np.where(p.max(axis=0) > lim["pmax"])[0]],
                   "SG31_peak_pu": float(p[:, i31].max()), "SG31_violation_duration_s": float((p[:, i31] > lim["pmax"][i31]).sum() * np.median(np.diff(tt)))}
            sweep[f"{mode}_{dlt}"] = rec
            print("redispatch", mode, dlt, round(rec["SG31_peak_pu"], 4), rec["units_with_pmax_violation"], flush=True)
    result["redispatch_sweep"] = sweep
    OUT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")
    fig, ax = plt.subplots(2, 2, figsize=(14, 9))
    for ch in range(10):
        ax[0, 0].plot(t - EVENT, resp[ch][0], lw=.9, ls="-" if ch < 6 else "--", label=f"Pset {names[ch]}")
        ax[0, 1].plot(t - EVENT, resp[ch + 10][0], lw=.9, ls="-" if ch < 6 else "--", label=f"Qset {names[ch]}")
    ax[0, 0].set_title("SG31 P response to a unit step of each Pset (at the event)"); ax[0, 1].set_title("SG31 P response to a unit step of each Qset")
    for a in ax[0]:
        a.set_xlim(-0.2, 8); a.legend(ncol=2, fontsize=6); a.set_xlabel("Time since event [s]"); a.set_ylabel("dP31 / d(reference)")
    for mode, a in (("all", ax[1, 0]), ("gfm", ax[1, 1])):
        for dlt in DELTAS:
            tt, p31 = series[(mode, dlt)]
            a.plot(tt - EVENT, p31, lw=.9, label=f"delta {dlt:.2f} pu")
        a.plot(t - EVENT, base["p"][:, i31], "k", lw=1.0, label="C2t dispatch"); a.axhline(lim["pmax"][i31], color="r", ls="--", lw=.8, label="pmax")
        a.set_xlim(-0.5, 12); a.set_ylim(lim["pmax"][i31] - 0.3, lim["pmax"][i31] + 0.12); a.legend(fontsize=7); a.set_xlabel("Time since event [s]"); a.set_ylabel("P31 [pu]")
        a.set_title("SG31 P after preventive redispatch (primary only), " + ("others by headroom" if mode == "all" else "GFM only"))
    for a in ax.ravel():
        a.grid(alpha=.25)
    fig.suptitle("E9-A: SG31 control authority and preventive-redispatch test (open loop, C2t, P+)"); fig.tight_layout()
    fig.savefig(FIG, dpi=300, bbox_inches="tight"); plt.close(fig)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
