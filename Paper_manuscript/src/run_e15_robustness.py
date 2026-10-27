"""E15 (Option B): robustness of B2 (original RDC) on the frozen variant C2t_Vsafe_R35_040 to uncertainties, delays and a selected N-1 contingency.

Fixed list, declared before running, no search:
  U1/U2  load uncertainty: the P+ event with amplitude 0.8x and 1.2x;
  D1-D3  delay of the RDC reference-rate command (applied rates equal the rates computed D seconds earlier; zero before the activation) D = 0.2, 1.0, 5.0 s, P+ event;
  I1     inertia uncertainty: all GENROU inertias M x 0.8 (runtime change of the parameter before initialisation; the case file is untouched), P+ event;
  N1     N-1: the line with the largest approximate flow among the lines whose removal keeps the network connected is opened at t = 5 s with an ANDES Toggle event, without load event
         (a first attempt that changed the line status parameter from the callback had no effect and is discarded; its result is kept in the JSON as invalid);
  GFL    extension to a grid-following resource: technically evaluated, not run (see the report in the JSON).
Each run is 100 s with B2 only.  Reported: TDS convergence, frequency, 39-bus voltages, units crossing P/Q/S limits, minimum P margins, setpoint drift (Qset) and the comparison with the
nominal B2 run of the same variant.  Negative results are reported; nothing is tuned and no controller parameter is changed.
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

import run_b3_ieee39 as b  # noqa: E402
import run_e8_ieee39 as e8  # noqa: E402
import select_equilibrium_b3 as b3  # noqa: E402
from e9b_variant import HOOK, VARIANT  # noqa: E402
from run_e0_ieee39 import ARTIFACTS_DIR as A, FIGURES_DIR, git_commit  # noqa: E402

HORIZON = 100.0
EVENT = 5.0
P_MW = 58.564


def pick_line() -> dict[str, Any]:
    s = b3.load_plant()
    s.PFlow.run()
    y, bus, _, _ = b3.network(s)
    vc = np.asarray(s.Bus.v.v, float) * np.exp(1j * np.asarray(s.Bus.a.v, float))
    n = len(bus)
    adj = (np.abs(y) > 1e-9) & ~np.eye(n, dtype=bool)
    best = None
    for i in range(n):
        for j in range(i + 1, n):
            if not adj[i, j]:
                continue
            a2 = adj.copy(); a2[i, j] = a2[j, i] = False
            seen, stack = {0}, [0]
            while stack:
                k = stack.pop()
                for m in np.where(a2[k])[0]:
                    if int(m) not in seen:
                        seen.add(int(m)); stack.append(int(m))
            if len(seen) < n:
                continue
            flow = abs(y[i, j]) * abs(vc[i] - vc[j]) * abs(vc[i])
            if best is None or flow > best[0]:
                best = (flow, bus[i], bus[j])
    b1, b2 = [int(x) for x in s.Line.bus1.v], [int(x) for x in s.Line.bus2.v]
    idx = [k for k in range(len(b1)) if {b1[k], b2[k]} == {best[1], best[2]}]
    return {"bus_pair": [int(best[1]), int(best[2])], "approx_flow_pu": float(best[0]), "line_position": idx[0] if idx else None, "line_idx": str(s.Line.idx.v[idx[0]]) if idx else None}


def metrics(d, lim, diag) -> dict[str, Any]:
    t = d["time_s"]
    p = np.hstack([d["sg_p_pu"], d["gfm_p_pu"]]); q = np.hstack([d["sg_q_pu"], d["gfm_q_pu"]])
    vb = d["bus_voltage_pu"]
    s_rel = 1 - np.hypot(p, q) / lim["smax"]
    f = d["bus_frequency_hz"].mean(axis=1)
    fin = t >= t[-1] - 10
    viol = {i: [k for k, v in (("P+", p[:, i].max() > lim["pmax"][i]), ("P-", p[:, i].min() < lim["pmin"][i]), ("Q+", q[:, i].max() > lim["qmax"][i]), ("Q-", q[:, i].min() < lim["qmin"][i]), ("S", s_rel[:, i].min() < 0)) if v] for i in range(10)}
    viol = {k: v for k, v in viol.items() if v}
    qs = d["cmd_qset"]
    sel = d["cmd_t"] >= d["cmd_t"][-1] - 20
    return {"tds_ok": bool(diag["tds_ok"] and diag["t_end_s"] >= HORIZON - 1e-6), "t_end_s": diag["t_end_s"], "final_residual": diag["final_residual"], "frequency_nadir_hz": float(f[t >= EVENT].min()), "frequency_max_dev_hz": float(np.abs(f - 60.0).max()),
            "frequency_final_error_hz": float(f[fin].mean() - 60.0), "frequency_oscillation_last_20s_hz": float(np.ptp(f[t >= t[-1] - 20])), "bus_voltage_min_pu": float(vb.min()), "bus_voltage_max_pu": float(vb.max()),
            "n_buses_outside_band": int(((vb < 0.95) | (vb > 1.05)).any(axis=0).sum()), "units_crossing_limits": {k: v for k, v in viol.items()}, "min_P_margin_pu": (lim["pmax"] - p).min(axis=0).tolist(),
            "qset_drift_last_20s_pu": float(np.abs(qs[sel][-1] - qs[sel][0]).max()), "max_abs_z": float(np.abs(d["cmd_z"]).max())}


def run_case(label: str, scenario: str, amp: float | None, delay: float | None, inertia: float | None, line: dict | None) -> dict[str, Any]:
    name = scenario
    if amp is not None:
        name = f"P+x{amp}"
        e8.SCENARIOS[name] = {"p_mw": P_MW * amp}
    cap: dict[str, Any] = {}

    def hook(system, ctx):
        HOOK(system, ctx)
        system.TDS.config.tf = HORIZON
        if inertia is not None:
            system.GENROU.M.v[:] = np.asarray(system.GENROU.M.v, float) * inertia
        cap["ctx"] = ctx

    kw: dict[str, Any] = {}
    if delay:
        buf: list = []

        def filt(t, sys_, ctx, st, vp, vq):
            buf.append((float(t), np.array(vp, float), np.array(vq, float)))
            tt = t - delay
            for tb, a, c in reversed(buf):
                if tb <= tt:
                    return a, c
            return np.zeros_like(vp), np.zeros_like(vq)
        kw["qp_filter"] = {"fn": filt}
    if line is not None:
        name = "N1"
        e8.SCENARIOS[name] = {"toggle_line": line["line_idx"]}
    try:
        _, d, diag = b.run("B2", name, init_hook=hook, **kw)
    except Exception as exc:
        return {"label": label, "tds_ok": False, "error": repr(exc)[:300]}
    out = metrics(d, cap["ctx"]["lim"], diag)
    out["label"] = label
    print(label, {k: out[k] for k in ("tds_ok", "frequency_nadir_hz", "frequency_final_error_hz", "n_buses_outside_band", "units_crossing_limits")}, flush=True)
    out["_series"] = (d["time_s"], d["bus_frequency_hz"].mean(axis=1), d["bus_voltage_pu"].min(axis=1), d["bus_voltage_pu"].max(axis=1))
    return out


def main() -> int:
    line = pick_line()
    print("N-1 line:", line, flush=True)
    cases = [("nominal P+", "P+", None, None, None, None), ("U1 load x0.8", "P+", 0.8, None, None, None), ("U2 load x1.2", "P+", 1.2, None, None, None),
             ("D1 delay 0.2 s", "P+", None, 0.2, None, None), ("D2 delay 1.0 s", "P+", None, 1.0, None, None), ("D3 delay 5.0 s", "P+", None, 5.0, None, None),
             ("I1 inertia x0.8", "P+", None, None, 0.8, None), ("N1 line outage (S0)", "S0", None, None, None, line), ("nominal S0", "S0", None, None, None, None)]
    if os.environ.get("E15_ONLY_N1"):
        cases = [c for c in cases if c[0].startswith("N1")]
    runs = [run_case(*c) for c in cases]
    series = {r["label"]: r.pop("_series") for r in runs if "_series" in r}
    gfl = {"status": "not run", "reason": "no grid-following case exists in the repository (C3 was never built) and a GFL resource (e.g. REGCA1 with REECA1) would need a new validated case, initialisation, flat/P/Q/EIG gates and its own limits; this is a new development line and is outside the closing scope",
           "classification": "not applicable / pending"}
    out = {"stage": "E15", "git_commit": git_commit(), "variant": VARIANT, "horizon_s": HORIZON, "n1_line": line, "runs": runs, "GFL_extension": gfl, "doc": __doc__}
    (A / os.environ.get("E15_OUT", "IEEE39_E15_robustness.json")).write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
    fig, ax = plt.subplots(1, 3, figsize=(19, 5.5))
    for lab, (t, f, vmin, vmax) in series.items():
        ax[0].plot(t, (f - 60.0) * 1e3, lw=.9, label=lab)
        ax[1].plot(t, vmin, lw=.9, label=lab)
        ax[2].plot(t, vmax, lw=.9, label=lab)
    ax[0].set_title("mean frequency deviation [mHz]"); ax[1].set_title("minimum bus voltage [pu]"); ax[2].set_title("maximum bus voltage [pu]")
    ax[1].axhline(0.95, color="k", ls=":"); ax[2].axhline(1.05, color="k", ls=":")
    for a in ax:
        a.set_xlabel("Time [s]"); a.grid(alpha=.25); a.axvline(EVENT, color="tab:red", ls=":", lw=.8)
    ax[0].legend(fontsize=6)
    fig.suptitle(f"E15: robustness of B2 on {VARIANT} (uncertainty, delay, inertia, N-1)"); fig.tight_layout()
    fig.savefig(FIGURES_DIR / "IEEE39_E15_robustness.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
