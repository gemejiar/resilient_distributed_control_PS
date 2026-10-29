"""DEC-055 G1 failure diagnosis (NO TDS: static evaluations and post-processing of stored series).
  rates <OC>   RDC rates (v_P, v_Q) of the original B2 law at the pre-event state of the M0 and M3 dispatches: a non-zero v_Q shows that the OPF point is not a
               closed-loop RDC equilibrium (D7)
  retro        stored DEC-054 / DEC-055 series: pre-event drift (0-5 s) of the unit-bus voltages and time of the minimum Pmax margin relative to the event (D8)"""
from __future__ import annotations

import json
import sys

import numpy as np

import dec054_common as C54
import dec055_common as C


def rates(oc):
    import dec055_oc as OCM
    plant = OCM.make_plant(oc)
    out = {}
    for m in ("m0", "m3"):
        p = C.STATE / f"{m}_{oc}.json"
        if not p.exists():
            continue
        s = json.loads(p.read_text(encoding="utf-8"))
        if not s.get("z") or s["status"] not in ("FEASIBLE_PREDICTED", "LOCAL_OPTIMUM_FOUND"):
            continue
        z = np.array(s["z"])
        system, ctx, _ = plant._make(z)
        st = plant.K.rdc_state(system, ctx)
        u = np.concatenate([st["pn"], st["qn"]])
        v = np.asarray(plant.EQ.rates(system, ctx, st, u), float)
        V = np.asarray(system.dae.y, float)[np.asarray(system.Bus.v.a)]
        vu = np.array([V[b - 1] for b in C.UNIT_BUS])
        out[m.upper()] = {"v_P_pu_s": v[:10].tolist(), "v_Q_pu_s": v[10:].tolist(), "max_abs_v_P": float(np.abs(v[:10]).max()), "max_abs_v_Q": float(np.abs(v[10:]).max()),
                          "unit_V_pre": vu.tolist(), "max_abs_unit_V_minus_1": float(np.abs(vu - 1.0).max())}
    with open(C.STATE / f"g1diag_rates_{oc}.json", "x", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(oc, {m: (round(r["max_abs_v_P"], 6), round(r["max_abs_v_Q"], 6), round(r["max_abs_unit_V_minus_1"], 4)) for m, r in out.items()})


def retro():
    R55 = C54.RUNS_DIR.parent / "DEC055_runs"
    out = {"pre_event_drift": {}, "min_margin_timing": {}}
    for root in (C54.RUNS_DIR, R55):
        for d in sorted(root.iterdir()):
            if not (d / "series.npz").exists():
                continue
            z = np.load(d / "series.npz")
            t, V, P = z["t"], z["V"], z["P"]
            ub = [b - 1 for b in C.UNIT_BUS]
            k5 = int(np.searchsorted(t, C.EVENT_T - 1e-9)) - 1
            out["pre_event_drift"][d.name] = {"unit_V_drift_0_5s_max_pu": float(np.abs(V[k5, ub] - V[0, ub]).max()), "bus_V_drift_0_5s_max_pu": float(np.abs(V[k5] - V[0]).max())}
            if "unit_pn" in z:
                lim = np.array([10.4, 6.5, 6.82, 6.97, 8.65, 11.0, 7.5, 5.64, 5.5, 5.95])          # case Pmax in UNITS order (IEEE39_DEC053_constraints_dictionary.csv)
                post = t >= C.EVENT_T - 1e-9
                mg = lim[None, :] - P[post]
                i, j = np.unravel_index(np.argmin(mg), mg.shape)
                out["min_margin_timing"][d.name] = {"min_margin_pu": float(mg[i, j]), "unit": C.UNITS[j], "t_after_event_s": float(t[post][i] - C.EVENT_T)}
    with open(C.STATE / "g1diag_retro.json", "x", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    sel = {k: v for k, v in out["min_margin_timing"].items() if v["min_margin_pu"] < 0.05}
    print(json.dumps(sel, indent=0)[:3000])
    print("max pre-event unit V drift:", max(v["unit_V_drift_0_5s_max_pu"] for v in out["pre_event_drift"].values()))


if __name__ == "__main__":
    rates(sys.argv[2]) if sys.argv[1] == "rates" else retro()
