"""DEC-054 gated runner: frozen-design verification, single frozen dispatch per method, ledger-gated TDS execution and exclusive evidence storage (P3).
Nothing here runs unless
  (1) the independent-backup gate is BACKUP_VERIFIED,
  (2) IEEE39_DEC054_design_frozen.json exists, is sealed, its code hashes match and it holds exactly ONE preventive dispatch per method M0-M3 (19 variables),
  (3) the TDS ledger grants an id (block budgets 8/16/24, total 48, failures counted, no silent retry).
Every run (including failures) is persisted exclusively by dec054_store.save_run before its ledger completion row is written."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import dec054_store as ST
from dec054_common import EVENT_T, N_Z, RUNS_DIR, TDS_STATUS, GateError, TdsLedger, backup_gate, sha_file

METHODS = ("M0", "M1", "M2", "M3")
_DISPATCH_KEYS = {"z", "z_sha256", "status", "J", "note"}


class FrozenError(RuntimeError):
    pass


def z_digest(z) -> str:
    import hashlib
    return hashlib.sha256(np.asarray(z, float).tobytes()).hexdigest()


def make_dispatch_entry(z, **extra) -> dict:
    z = np.asarray(z, float)
    if z.shape != (N_Z,) or not np.all(np.isfinite(z)):
        raise FrozenError("a dispatch must be 19 finite values")
    return {"z": z.tolist(), "z_sha256": z_digest(z), **extra}


def validate_dispatches(dispatches: dict) -> dict:
    """Exactly one frozen dispatch per method, shared by every contingency.  Per-scenario dispatches (any key other than the dispatch fields) are rejected."""
    if set(dispatches) != set(METHODS):
        raise FrozenError(f"dispatches must contain exactly {METHODS}; got {sorted(dispatches)}")
    out = {}
    for m, e in dispatches.items():
        if not isinstance(e, dict) or "z" not in e:
            raise FrozenError(f"dispatch of {m} must be a dict with 'z'")
        extra = set(e) - _DISPATCH_KEYS
        if extra:
            raise FrozenError(f"dispatch of {m} has per-scenario/unknown keys {sorted(extra)}: one dispatch per method is required")
        z = np.asarray(e["z"], float)
        if z.shape != (N_Z,) or not np.all(np.isfinite(z)):
            raise FrozenError(f"dispatch of {m} must hold 19 finite values")
        if e.get("z_sha256") != z_digest(z):
            raise FrozenError(f"dispatch of {m}: z_sha256 missing or inconsistent")
        out[m] = z
    return out


def assert_single_dispatch(plan, frozen_dispatches: dict) -> None:
    """plan: iterable of {'method','scenario','z'}.  All entries of a method must use the same vector, equal to the frozen one."""
    z_frozen = validate_dispatches(frozen_dispatches)
    seen: dict = {}
    for p in plan:
        m, z = p["method"], np.asarray(p["z"], float)
        if m not in z_frozen:
            raise FrozenError(f"unknown method {m}")
        if not np.array_equal(z, z_frozen[m]):
            raise FrozenError(f"{m}: dispatch used for scenario {p.get('scenario')} differs from the frozen dispatch")
        if m in seen and not np.array_equal(seen[m], z):
            raise FrozenError(f"{m}: different dispatches for different scenarios")
        seen[m] = z


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
    validate_dispatches(d["dispatches"])
    return d


def write_frozen(path: Path, src_dir: Path, code_files, partition: dict, params: dict, eps: dict, dispatches: dict, scenarios_test: dict, andes_version: str,
                 hypotheses: str = "", criteria: str = "") -> dict:
    """Create design_frozen.json EXCLUSIVELY (never overwrites).  `dispatches` must be {method: make_dispatch_entry(z)} for M0-M3 (one per method)."""
    validate_dispatches(dispatches)
    path = Path(path)
    d = {"sealed": True, "code_sha256": {f: sha_file(Path(src_dir) / f) for f in code_files}, "partition": partition, "params": params, "eps": eps, "dispatches": dispatches,
         "scenarios_test": scenarios_test, "andes_version": andes_version, "hypotheses": hypotheses, "acceptance_criteria": criteria}
    with open(path, "x", encoding="utf-8") as f:           # 'x': fails if the file already exists
        json.dump(d, f, indent=1, default=float)
    return d


def execute_tds(z, scenario) -> dict:
    """B2 original, 200 s, dt=2^-8, load step at t=5 s through the dist_fn mechanism of run_dec051_h3_sim.py.  UNTESTED_ON_PLANT; ANDES imported lazily.
    A TDS failure returns TDS_NUMERICAL_FAILURE with its diagnostics (it does not raise)."""
    import os
    os.environ.setdefault("C2_VARIANT", "C2t")
    import run_b3_ieee39 as b
    from dec054_metrics import violations
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
        return {"status": "TDS_NUMERICAL_FAILURE", "notes": json.dumps(diag, default=float), "diag": diag, "series": None, "metrics": None}
    t = d["time_s"]
    P = np.hstack([d["sg_p_pu"], d["gfm_p_pu"]])
    Q = np.hstack([d["sg_q_pu"], d["gfm_q_pu"]])
    lim = {k: d[f"unit_{k}"] for k in ("pmax", "pmin", "qmax", "qmin", "smax")}
    v = violations(t, P, Q, d["bus_voltage_pu"], lim, d["unit_pn"])
    bad = v["n_violating_pairs_P"] > 0 or v["V_outside_buses"] > 0 or any(v["unit"][k]["violates"].any() for k in ("Qmax", "Qmin", "Smax"))
    series = {"t": t, "P": P, "Q": Q, "V": d["bus_voltage_pu"], "f_bus_hz": d["bus_frequency_hz"], "unit_pn": d["unit_pn"], "unit_qn": d["unit_qn"],
              "cmd_pset": d.get("cmd_pset", np.zeros(0)), "cmd_qset": d.get("cmd_qset", np.zeros(0)), "cmd_t": d.get("cmd_t", np.zeros(0))}
    return {"status": "TDS_PHYSICAL_VIOLATION" if bad else "TDS_SAFE_OBSERVED", "metrics": v, "diag": diag, "series": series,
            "notes": "stored-sample classification at dt=2^-8 s; not continuous-time safety"}


def run_prospective_scenario(ledger: TdsLedger, frozen_path: Path, src_dir: Path, scenario, methods=METHODS, dry_run: bool = True, executor=execute_tds,
                             store_root: Path | None = None, block: str = "P3-C") -> dict:
    """One scenario x M0-M3.  Verifies the gate, the frozen file (incl. one dispatch per method) and the ledger budget BEFORE any ANDES import.
    dry_run=True returns the plan only.  dry_run=False requests one ledger id per method, executes with the FROZEN dispatch of that method, persists the run
    exclusively (also on failure) and only then writes the ledger completion row."""
    gate = backup_gate(ledger.art_dir)
    if not gate["verified"]:
        raise GateError("STOP_BACKUP_NOT_VERIFIED")
    frozen = verify_frozen(frozen_path, src_dir)
    if scenario["bus"] not in frozen["scenarios_test"]["buses"]:
        raise FrozenError("scenario bus is not in the frozen PROSPECTIVE_TEST list")
    zs = validate_dispatches(frozen["dispatches"])
    plan = [{"method": m, "scenario": scenario["name"], "z": zs[m]} for m in methods]
    assert_single_dispatch(plan, frozen["dispatches"])
    if dry_run:
        return {"plan": [(p["method"], p["scenario"]) for p in plan], "frozen": True}
    root = Path(store_root) if store_root is not None else RUNS_DIR
    out = {}
    for m in methods:
        run_id = f"{block}_{scenario['name']}_{m}"
        tid = ledger.request(block, scenario["name"], m, run_id, "prospective comparison M0-M3 (frozen dispatch)")
        cfg = {"run_id": run_id, "tds_id": tid, "method": m, "scenario": scenario, "z": zs[m], "z_sha256": z_digest(zs[m]), "frozen_file_sha256": sha_file(Path(frozen_path)),
               "code_sha256": frozen["code_sha256"], "andes_version": frozen["andes_version"], "params": frozen["params"]}
        res, err = None, None
        try:
            res = executor(zs[m], scenario)
            status = res.get("status")
            if status not in TDS_STATUS:
                err, status = f"executor returned an invalid status {status!r}", "TDS_NUMERICAL_FAILURE"
        except Exception as ex:      # failure consumes the run and keeps its evidence
            err, status = ex, "TDS_NUMERICAL_FAILURE"
        row = next((r for r in ledger.rows if r["tds_id"] == tid and r["status"] == "REQUESTED"), {})
        res = res or {}
        try:
            ST.save_run(root, run_id, status=status, tds_id=tid, series=res.get("series"), metrics=res.get("metrics"), config=cfg, diag=res.get("diag"),
                        notes=str(res.get("notes", "")), error=err, ledger_row=row)
        except Exception as ex2:     # storage failure: the TDS happened; record it in the ledger, then re-raise
            ledger.complete(tid, status, f"EVIDENCE_NOT_SAVED: {ex2!r}")
            raise
        ledger.complete(tid, status, (str(err) if err else str(res.get("notes", "")))[:500])
        out[m] = {"status": status, "run_dir": str(root / run_id), "saved": True}
    return out
