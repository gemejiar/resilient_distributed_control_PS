"""DEC-059 pre-TDS predictions for a dispatch and a set of cells (static, 0 TDS).  Per cell and unit: algebraic jump P+, dense-time post-jump peak (the OS model of dec059_os),
the predicted instantaneous Pmax/Pmin margin, the Q/S margins and the bus-voltage band at the jump, and the predicted class by rule M3V-1 (U_D8 band).
  <venv python> dec059_pred.py <OC> <M3OS|M0|M3> <tune|test|design> [write]      writes IEEE39_DEC059_pred_<OC>_<M>_<set>.json exclusively with 'write'
The predicted class is a PREDICTION (T-A + OS model); it is compared with the TDS class afterwards and never replaces it."""
from __future__ import annotations

import json
import sys

import numpy as np

import dec054_common as C54
import dec054_opf as OPF
import dec054_predictor as PRD
import dec055_common as C55
import dec055_oc as OCM
import dec059_eq as EQ
import dec059_os as OS

U_D8 = 0.0109


def cells(which):
    if which == "tune":
        return [(b, s) for b in C55.TUNE for s in C55.TUNE_SEVERITIES]
    if which == "test":
        return [(b, s) for b in C55.TEST for s in C55.CONFIRMATORY_SEVERITIES]
    return [(b, s) for b in C55.DESIGN for s in C55.SEVERITY]


def klass(m):
    return "SAFE" if m >= U_D8 else "UNSAFE" if m <= -U_D8 else "NUMERICALLY_INDETERMINATE"


def predict(oc, m, which):
    z, _ = EQ.dispatch(oc, m)
    plant = OCM.make_plant(oc)
    lim = plant.limits
    ev = plant.evaluate(np.asarray(z, float))
    out = {"oc": oc, "dispatch": m, "set": which, "z": np.asarray(z).tolist(), "pre_event": {"P": ev["P"].tolist(), "Q": ev["Q"].tolist(), "V_min": float(ev["V"].min()), "V_max": float(ev["V"].max()),
                                                                                              "pmax_margin_min": float((lim["pmax"] - ev["P"]).min())}, "cells": []}
    for bus, sev in cells(which):
        amp = round(C55.oc_amp(sev), 5)
        sc = OPF.Scenario(f"b{bus}P_{sev}", bus, "P", amp)
        jp = plant.jump(np.asarray(z, float), sc)
        rec = {"name": sc.name, "bus": bus, "severity": sev, "amp": amp}
        if not jp["ok"]:
            rec["ok"] = False
            out["cells"].append(rec)
            continue
        A, f, Cm = plant.affine(np.asarray(z, float), sc)
        _, D, _ = PRD.propagate(A, f, Cm, OS.DENSE)
        Pp, Qp = jp["P_plus"], jp["Q_plus"]
        up = Pp + np.maximum(D.max(axis=1), 0.0)
        dn = Pp - np.maximum((-D).max(axis=1), 0.0)
        mup, mdn = lim["pmax"] - up, dn - lim["pmin"]
        iu, idn = int(mup.argmin()), int(mdn.argmin())
        sm = lim["smax"] - np.hypot(Pp, Qp)
        rec.update({"ok": True, "jump_pmax_margin_min": float((lim["pmax"] - Pp).min()), "jump_unit": C55.UNITS[int((lim["pmax"] - Pp).argmin())],
                    "pred_pmax_margin_min": float(mup.min()), "pred_pmax_unit": C55.UNITS[iu], "pred_pmin_margin_min": float(mdn.min()), "pred_pmin_unit": C55.UNITS[idn],
                    "jump_qmax_margin_min": float((lim["qmax"] - Qp).min()), "jump_qmin_margin_min": float((Qp - lim["qmin"]).min()), "jump_s_margin_min": float(sm.min()),
                    "jump_V_min": float(jp["V_plus"].min()), "jump_V_max": float(jp["V_plus"].max()), "residual": float(jp["residual"]),
                    "pred_class_pmax": klass(min(float(mup.min()), float(mdn.min())))})
        qsv = min(float((lim["qmax"] - Qp).min()), float((Qp - lim["qmin"]).min()), float(sm.min()), float(jp["V_plus"].min() - 0.95), float(1.05 - jp["V_plus"].max()))
        rec["jump_qsv_binary_margin_min"] = qsv                    # rule M3V-1: Q, S and V are classified on the samples, binary (the U_D8 band is a P-peak uncertainty)
        rec["pred_class_all"] = "UNSAFE" if qsv < 0 else rec["pred_class_pmax"]
        # promotion of S3 cells (DEC-055 protocol section 4 (c)): a_j >= 0 predicted at the algebraic jump for every physical constraint
        rec["admissible_at_jump"] = bool(float((lim["pmax"] - Pp).min()) >= 0 and float((Pp - lim["pmin"]).min()) >= 0 and qsv >= 0)
        out["cells"].append(rec)
        print(oc, m, sc.name, {k: (round(v, 5) if isinstance(v, float) else v) for k, v in rec.items() if k.startswith("pred_")}, flush=True)
    out["n_pred_safe"] = sum(c.get("pred_class_all") == "SAFE" for c in out["cells"])
    out["n_pred_unsafe"] = sum(c.get("pred_class_all") == "UNSAFE" for c in out["cells"])
    out["n_pred_indeterminate"] = sum(c.get("pred_class_all") == "NUMERICALLY_INDETERMINATE" for c in out["cells"])
    out["note"] = "prediction (jump + dense post-jump model, 0 TDS); the U_D8 band is the D8 numerical uncertainty; Q/S/V are evaluated at the algebraic jump only"
    return out


if __name__ == "__main__":
    oc, m, which = sys.argv[1:4]
    r = predict(oc, m, which)
    if "write" in sys.argv:
        with open(C55.ART / f"IEEE39_DEC059_pred_{oc}_{m}_{which}.json", "x", encoding="utf-8") as f:
            json.dump(r, f, indent=1, default=float)
    print({k: r[k] for k in ("n_pred_safe", "n_pred_unsafe", "n_pred_indeterminate")})
