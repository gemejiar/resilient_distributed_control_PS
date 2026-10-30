"""DEC-061 D1/D2: OC1 design revision 3 (b20 S3 mandatory in the design set).  DESIGN/TUNE buses only; TEST untouched.  Same formulation, cfg, eps and M3 predictor + OS term as the
DEC-059 cut cycle; the only change is the scenario set.  Cells: DESIGN12 + cut cells {b20 S2, b16 S3, b24 S3} + b20 S3 (16 events); the other four OC1 TUNE cells are MONITORS
(they are evaluated at the candidate dispatch and must not degrade).
  scan   [write]    feasibility analysis BEFORE the optimisation: design margins of all 20 cells at the cut dispatch and along a SG33 set-point ray (no TDS, no optimiser)
  design            Algorithm 1 on the 16-event set, seed = the DEC-059 cut dispatch (and the M3+OS dispatch); writes DEC059_state/m3os_rev3_OC1.json exclusively
  <venv python> dec061_design.py scan|design"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

import dec054_common as C54
import dec054_g4_design as G4
import dec054_opf as OPF
import dec055_common as C55
import dec055_l0 as L0
import dec055_oc as OCM
import dec059_os as OS

STATE = OS.STATE
OC = "OC1"
CUT = ("b20P_S2", "b16P_S3", "b24P_S3")
MANDATORY = "b20P_S3"
MONITORS = ("b7P_S2", "b7P_S3", "b16P_S2", "b24P_S2")


def cell(name):
    b = int(name.split("P_")[0][1:])
    return OPF.Scenario(name, b, "P", float(C55.oc_amp(name.split("_")[1])))


def design_set():
    return L0.design_scenarios() + [cell(n) for n in CUT] + [cell(MANDATORY)]


def build(workers=3):
    cal = json.loads((C55.ART / "IEEE39_DEC059_OS_calibration.json").read_text(encoding="utf-8"))["summary"]
    OCM._init_worker = OS._init_worker_os
    plant = OCM.OCPooledPlant(OC, int(workers))
    eJ, eEu, eEd = G4.eps_vectors()
    eEu2, eEd2 = eEu + cal["eps_OS_up"] + OS.U_D8, eEd + cal["eps_OS_dn"] + OS.U_D8
    cfg = dict(C54.PROPOSED, K_max=8, N_it=int(os.environ.get("DEC059_NIT", "25")), ftol=1e-6, verbose=False)
    return plant, eJ, eEu2, eEd2, cfg, cal


ALL = [s.name for s in L0.design_scenarios()] + list(CUT) + [MANDATORY] + list(MONITORS)


def monitor_set():
    return L0.design_scenarios() + [cell(n) for n in CUT + (MANDATORY,) + MONITORS]


def cell_margins(pb, plant, z, names):
    """pb must be built on monitor_set() (the Problem cache is keyed by the scenario index, so one Problem = one scenario list)."""
    assert [s.name for s in pb.sc] == ALL
    plant.prefetch([z], pb.sc, True)
    out = {}
    for n in names:
        up, dn, info = pb.margins_d(np.asarray(z, float), ALL.index(n))
        iu, idn = int(np.argmin(up)), int(np.argmin(dn))
        out[n] = {"min_up": float(up.min()), "unit_up": C55.UNITS[iu], "min_dn": float(dn.min()), "unit_dn": C55.UNITS[idn], "ok": bool(info.get("ok", True))}
    return out


def scan(write=False):
    t0 = time.time()
    plant, eJ, eEu2, eEd2, cfg, cal = build()
    try:
        names = ALL
        pb = OPF.Problem(plant, "M3", monitor_set(), eJ, eEu2, cfg=cfg, eps_E_dn=eEd2)
        z_cut = np.array(json.loads((STATE / "m3os_cut_OC1.json").read_text(encoding="utf-8"))["z"])
        z_os = np.array(json.loads((STATE / "m3os_OC1.json").read_text(encoding="utf-8"))["z"])
        out = {"stage": "DEC-061 D1 feasibility scan (no optimiser, no TDS)", "convention": "design margin = Pmax - P0 - jump - excursion(OS) - eps_J - eps_E (eps_E includes eps_OS and U_D8); >= 0 is design-feasible",
               "dispatches": {}, "ray": []}
        for lab, z in (("M3OS", z_os), ("CUT", z_cut)):
            out["dispatches"][lab] = cell_margins(pb, plant, z, names)
        # ray: lower the SG33 pre-event set-point (index 2 of z), the rest unchanged (the slack unit absorbs the difference)
        for th in (0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40):
            z = z_cut.copy()
            z[2] -= th
            e = plant.evaluate(z)
            row = {"theta_pu": th, "init_ok": bool(e["ok"])}
            if e["ok"]:
                m = cell_margins(pb, plant, z, names)
                worst = min(m, key=lambda n: min(m[n]["min_up"], m[n]["min_dn"]))
                row.update({"P_pre": e["P"].tolist(), "V_min": float(e["V"].min()), "V_max": float(e["V"].max()), "cells": m, "worst_cell": worst, "worst_margin": min(m[worst]["min_up"], m[worst]["min_dn"]),
                            "b20P_S3": m[MANDATORY]})
            out["ray"].append(row)
            print("theta", th, row.get("worst_cell"), row.get("worst_margin"), row.get("b20P_S3"), flush=True)
        out["seconds"] = round(time.time() - t0, 1)
        out["note"] = "one-dimensional necessary-condition scan, not a global infeasibility certificate; the optimiser (design stage) is the full-space attempt"
        if write:
            with open(C55.ART / "IEEE39_DEC061_feasibility_scan.json", "x", encoding="utf-8") as f:
                json.dump(out, f, indent=1, default=float)
    finally:
        plant.close()


def design():
    t0 = time.time()
    scen = design_set()
    plant, eJ, eEu2, eEd2, cfg, cal = build()
    seeds = [np.array(json.loads((STATE / f"{n}.json").read_text(encoding="utf-8"))["z"]) for n in ("m3os_cut_OC1", "m3os_OC1")]
    try:
        r = OPF.algorithm1(plant, "M3", scen, eJ, eEu2, cfg=cfg, z_seeds=seeds, k0=4, eps_E_dn=eEd2, log=lambda x: print(OC, "  iter", {k: x[k] for k in ("k", "W", "min_margin", "J")}, flush=True))
        out = {"oc": OC, "method": "M3+OS+rev3", "design_events": [s.name for s in scen], "status": r.status, "J": r.J, "kkt": r.kkt_residual, "iterations": r.iterations, "detail": r.detail, "cuts": r.cuts, "log": r.log,
               "z": None if r.z is None else r.z.tolist(), "seeds": ["m3os_cut_OC1", "m3os_OC1"], "event_tasks": plant.n_event_tasks, "plant_evaluations": plant.n_eval, "seconds": round(time.time() - t0, 1),
               "eps": {"J": eJ.tolist(), "E_up": eEu2.tolist(), "E_dn": eEd2.tolist(), "eps_OS_up": cal["eps_OS_up"], "eps_OS_dn": cal["eps_OS_dn"], "eps_D8": OS.U_D8}}
        if r.z is not None:
            e = plant.evaluate(r.z)
            names = ALL
            pb = OPF.Problem(plant, "M3", monitor_set(), eJ, eEu2, cfg=cfg, eps_E_dn=eEd2)
            out.update({"init_ok": bool(e["ok"]), "margins_all_cells": cell_margins(pb, plant, r.z, names),
                        "redispatch_MW_abs_sum_vs_case": float(np.abs(r.z[:9] - plant.z_ref[:9]).sum() * 100),
                        "redispatch_MW_abs_sum_vs_M3OS": float(np.abs(r.z[:9] - np.array(json.loads((STATE / "m3os_OC1.json").read_text(encoding="utf-8"))["z"])[:9]).sum() * 100),
                        "redispatch_MW_abs_sum_vs_cut": float(np.abs(r.z[:9] - np.array(json.loads((STATE / "m3os_cut_OC1.json").read_text(encoding="utf-8"))["z"])[:9]).sum() * 100)})
        with open(STATE / "m3os_rev3_OC1.json", "x", encoding="utf-8") as f:
            json.dump(out, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else float(o))
        print(OC, "M3+OS+rev3", r.status, r.J, round(time.time() - t0, 1), "s", flush=True)
    finally:
        plant.close()


if __name__ == "__main__":
    {"scan": lambda: scan("write" in sys.argv), "design": design}[sys.argv[1]]()
