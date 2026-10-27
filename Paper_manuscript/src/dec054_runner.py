"""DEC-054 gated runner: frozen-design verification and ledger-gated TDS execution (P3).  Nothing here runs unless
  (1) the independent-backup gate is BACKUP_VERIFIED, (2) IEEE39_DEC054_design_frozen.json exists, is sealed and its code/parameter hashes match, and
  (3) the TDS ledger grants an id (block budgets 8/16/24, total 48, failures counted, no silent retry).
The prospective cohort additionally requires that M0-M3 dispatches are the frozen ones and that all four methods are run on the same event without reading other prospective outputs."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from dec054_common import ART, EVENT_T, GateError, TdsLedger, backup_gate, sha_file


class FrozenError(RuntimeError):
    pass


def verify_frozen(frozen_path: Path, src_dir: Path) -> dict:
    p = Path(frozen_path)
    if not p.exists():
        raise FrozenError("design_frozen.json does not exist: the design is not frozen")
    d = json.loads(p.read_text(encoding="utf-8"))
    if not d.get("sealed", False):
        raise FrozenError("design_frozen.json is not sealed")
    for name, h in d["code_sha256"].items():
        if sha_file(Path(src_dir) / name) != h:
            raise FrozenError(f"code hash mismatch: {name}")
    for k in ("partition", "params", "eps", "dispatches", "scenarios_test", "andes_version"):
        if k not in d:
            raise FrozenError(f"frozen file lacks {k}")
    return d


def write_frozen(path: Path, src_dir: Path, code_files, partition: dict, params: dict, eps: dict, dispatches: dict, scenarios_test: dict, andes_version: str, hypotheses: str = "", criteria: str = "") -> dict:
    """Create design_frozen.json EXCLUSIVELY (never overwrites).  To be called once at P1/P3-C entry; the file must be committed to Git before the first TDS of the
    prospective cohort.  Records code hashes, partition+seed, parameters, eps, working sets/dispatches M0-M3, test scenarios and criteria."""
    path = Path(path)
    d = {"sealed": True, "code_sha256": {f: sha_file(Path(src_dir) / f) for f in code_files}, "partition": partition, "params": params, "eps": eps, "dispatches": dispatches,
         "scenarios_test": scenarios_test, "andes_version": andes_version, "hypotheses": hypotheses, "acceptance_criteria": criteria}
    with open(path, "x", encoding="utf-8") as f:           # 'x': fails if the file already exists
        json.dump(d, f, indent=1, default=float)
    return d


def run_prospective_scenario(ledger: TdsLedger, frozen_path: Path, src_dir: Path, scenario, methods=("M0", "M1", "M2", "M3"), dry_run: bool = True):
    """One scenario x 4 methods (P3-C).  Verifies the gate, the frozen file and the ledger budget BEFORE any ANDES import.  dry_run=True only reserves nothing and
    returns the plan (used by tests); dry_run=False requests one ledger id per method and executes (not exercised before BACKUP_VERIFIED)."""
    gate = backup_gate(ledger.art_dir)
    if not gate["verified"]:
        raise GateError("STOP_BACKUP_NOT_VERIFIED")
    frozen = verify_frozen(frozen_path, src_dir)
    if scenario["bus"] not in frozen["scenarios_test"]["buses"]:
        raise FrozenError("scenario bus is not in the frozen PROSPECTIVE_TEST list")
    if dry_run:
        return {"plan": [(m, scenario["name"]) for m in methods], "frozen": True}
    out = {}
    for m in methods:
        tid = ledger.request("P3-C", scenario["name"], m, f"P3C_{scenario['name']}_{m}", "prospective comparison M0-M3 (frozen)")
        try:
            res = execute_tds(frozen["dispatches"][m][str(scenario["name"])]["z"], scenario)
            ledger.complete(tid, res["status"], res.get("notes", ""))
            out[m] = res
        except Exception as ex:      # failure consumes the run and is kept
            ledger.complete(tid, "TDS_NUMERICAL_FAILURE", repr(ex))
            out[m] = {"status": "TDS_NUMERICAL_FAILURE", "notes": repr(ex)}
    return out


def execute_tds(z, scenario) -> dict:
    """B2 original, 200 s, dt=2^-8, load step at t=5 s through the dist_fn mechanism of run_dec051_h3_sim.py.  UNTESTED_ON_PLANT; ANDES imported lazily."""
    import os
    os.environ.setdefault("C2_VARIANT", "C2t")
    import run_b3_ieee39 as b
    from dec054_plant import hook_for_z
    bus, amp, kind = int(scenario["bus"]), float(scenario["amp"]), scenario["kind"]
    state = {"done": False}

    def step(t, s):
        if not state["done"] and t >= EVENT_T:
            k = [int(x) for x in s.PQ.bus.v].index(bus)
            (s.PQ.Ppf if kind == "P" else s.PQ.Qpf).v[k] += amp
            state["done"] = True
    system, d, diag = b.run("B2", "S0", init_hook=hook_for_z(z), dist_fn=step)
    if not diag["tds_ok"]:
        return {"status": "TDS_NUMERICAL_FAILURE", "notes": json.dumps(diag, default=float), "data": None}
    from dec054_metrics import violations
    t = d["time_s"]
    P = np.hstack([d["sg_p_pu"], d["gfm_p_pu"]])
    Q = np.hstack([d["sg_q_pu"], d["gfm_q_pu"]])
    lim = {k: d[f"unit_{k}"] for k in ("pmax", "pmin", "qmax", "qmin", "smax")}
    v = violations(t, P, Q, d["bus_voltage_pu"], lim, d["unit_pn"])
    bad = v["n_violating_pairs_P"] > 0 or v["V_outside_buses"] > 0 or any(v["unit"][k]["violates"].any() for k in ("Qmax", "Qmin", "Smax"))
    return {"status": "TDS_PHYSICAL_VIOLATION" if bad else "TDS_SAFE_OBSERVED", "metrics": v, "diag": diag, "series": {"t": t, "P": P, "Q": Q, "V": d["bus_voltage_pu"]},
            "notes": "stored-sample classification at dt=2^-8 s; not continuous-time safety"}
