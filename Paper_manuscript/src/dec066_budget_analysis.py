"""DEC-066 controls: external diagnostic (identical to dec066_abl_analysis.main) of the equal-effort designs EQ1 and DQ1 (and any bud_<label> state) -> artifacts/IEEE39_DEC066_budget_raw.json (exclusive).
Run: <venv python> dec066_budget_analysis.py write EQ1 DQ1"""
from __future__ import annotations

import json
import sys
import time

import numpy as np

import dec054_common as C54
import dec054_predictor as PRD
import dec055_common as C55
import dec055_oc as OCM
import dec059_os as OS
import dec066_abl_analysis as AA

STATE = C54.RUNS_DIR.parent / "DEC066_state"


def main(write, labels):
    t0 = time.time()
    plant = OCM.make_plant(AA.OC)
    lim = plant.limits
    Z = {k: np.array(json.loads((STATE / f"bud_{k}_OC1.json").read_text(encoding="utf-8"))["z"]) for k in labels}
    ev = AA.events()
    out = {"units": C55.UNITS, "pmax": np.asarray(lim["pmax"]).tolist(), "pmin": np.asarray(lim["pmin"]).tolist(), "events": [{"role": r, "name": s.name, "bus": s.bus, "amp": s.amp} for r, s in ev],
           "z": {k: v.tolist() for k, v in Z.items()}, "rows": {}}
    for k, z in Z.items():
        e = plant.evaluate(z)
        out["rows"][k] = {"P_pre": np.asarray(e["P"]).tolist(), "ok": bool(e["ok"]), "events": []}
        for role, sc in ev:
            jp = plant.jump(z, sc)
            rec = {"name": sc.name, "role": role, "jump_ok": bool(jp["ok"])}
            try:
                A, f, Cm = plant.affine(z, sc)
                x = PRD.excursion(A, f, Cm)
                tg, Dg, _ = PRD.propagate(A, f, Cm)
                _, Dd, _ = PRD.propagate(A, f, Cm, OS.DENSE)
                tg = np.asarray(tg)
                mid, slow = (tg > OS.T_OS) & (tg <= 10.0), tg > 10.0
                w = lambda m: np.maximum(Dg[:, m].max(axis=1), 0.0).tolist() if m.any() else [0.0] * 10
                wl = lambda m: np.maximum((-Dg[:, m]).max(axis=1), 0.0).tolist() if m.any() else [0.0] * 10
                rec.update({"P_plus": np.asarray(jp["P_plus"]).tolist(), "dP": np.asarray(jp["dP"]).tolist(), "pred_ok": bool(x["ok"] and np.all(np.isfinite(Dd))),
                            "E_grid_up": np.asarray(x["E_up"]).tolist(), "E_grid_dn": np.asarray(x["E_dn"]).tolist(), "t_up": np.asarray(x["t_up"]).tolist(),
                            "E_dense_up": np.maximum(Dd.max(axis=1), 0.0).tolist(), "E_dense_dn": np.maximum((-Dd).max(axis=1), 0.0).tolist(),
                            "win_mid_up": w(mid), "win_slow_up": w(slow), "win_mid_dn": wl(mid), "win_slow_dn": wl(slow), "D_abs_max": float(np.abs(Dg).max())})
            except Exception as ex:
                rec.update({"pred_ok": False, "reason": repr(ex)})
            out["rows"][k]["events"].append(rec)
        print(k, "done", round(time.time() - t0), "s", flush=True)
    out["seconds"] = round(time.time() - t0, 1)
    if write:
        with open(C55.ART / "IEEE39_DEC066_budget_raw.json", "x", encoding="utf-8") as fh:
            json.dump(out, fh, default=lambda o: o.tolist() if hasattr(o, "tolist") else float(o))


if __name__ == "__main__":
    a = sys.argv[1:]
    main("write" in a, [x for x in a if x != "write"])
