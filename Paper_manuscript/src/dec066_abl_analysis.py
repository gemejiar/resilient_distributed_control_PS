"""DEC-066 A1/D: common external diagnostic of the five OPF designs A..E (0 TDS; PF + linearisation only).
Designs (OC1, same 12 DESIGN events dec055_l0.design_scenarios()): A=DEC-055 M3, B=dense, C=dense+eps_OS, D=DEC-059 M3+OS, E=U_D8 only.
For every design z and every event (12 design + candidate evaluation events) it stores, per unit: algebraic jump P+, E_grid (M3 grid 0-195 s, refined), E_dense (0-50 ms),
and window maxima of the predicted excursion (0-50 ms, 50 ms-10 s, 10-195 s).  Writes artifacts/IEEE39_DEC066_ablation_raw.json (exclusive) and
backups/DEC066_state/abl_diag_raw.npz.  Tables are built by dec066_abl_tables.py from this file.
Run: <venv python> dec066_abl_analysis.py write"""
from __future__ import annotations

import json
import sys
import time

import numpy as np

import dec054_common as C54
import dec054_g4_design as G4
import dec054_opf as OPF
import dec054_predictor as PRD
import dec055_common as C55
import dec055_l0 as L0
import dec055_oc as OCM
import dec059_os as OS

OC = "OC1"
STATE = C54.RUNS_DIR.parent
SRC = {"A": STATE / "DEC055_state" / "m3_OC1.json", "B": STATE / "DEC066_state" / "abl_B_OC1.json", "C": STATE / "DEC066_state" / "abl_C_OC1.json",
       "D": STATE / "DEC059_state" / "m3os_OC1.json", "E": STATE / "DEC066_state" / "abl_E_OC1.json"}
EVAL = [(21, "S1"), (21, "S2"), (21, "S3"), (39, "S1"), (39, "S2"), (39, "S3"), (31, "S1"), (31, "S2"), (31, "S3"), (18, "S2"), (18, "S3"), (20, "S3"), (15, "S2"), (15, "S3"), (26, "S2"), (26, "S3")]


def events():
    ev = [("design", s) for s in L0.design_scenarios()]
    ev += [("eval", OPF.Scenario(f"b{b}P_{s}", b, "P", round(C55.oc_amp(s), 5))) for b, s in EVAL]
    return ev


def main(write=False):
    t0 = time.time()
    plant = OCM.make_plant(OC)
    lim = plant.limits
    Z = {k: np.array(json.loads(p.read_text(encoding="utf-8"))["z"]) for k, p in SRC.items()}
    ev = events()
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
        with open(C55.ART / "IEEE39_DEC066_ablation_raw.json", "x", encoding="utf-8") as fh:
            json.dump(out, fh, default=lambda o: o.tolist() if hasattr(o, "tolist") else float(o))


if __name__ == "__main__":
    main("write" in sys.argv)
