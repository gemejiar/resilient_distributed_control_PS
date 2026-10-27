"""DEC-054 common definitions: constants, proposed (NOT sealed) parameters, status vocabularies, hashing, and the TDS ledger/gate.

Nothing here runs ANDES.  The ledger refuses every TDS request unless the independent-backup gate is BACKUP_VERIFIED."""
from __future__ import annotations

import csv
import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# persistent per-run evidence goes to an exclusive folder inside the paper folder (excluded from Git locally: .git/info/exclude)
RUNS_DIR = Path(os.environ.get("DEC054_RUNS_DIR", r"c:/onedrive/OneDrive - Universidad del Valle/05_Univalle_Investigacion/02_Publicaciones/En_Preparacion/Proyectos_Latex/Resilient_distributed_control_PS/Paper_manuscript/backups/DEC054_runs"))
ART = ROOT / "Paper_manuscript" / "artifacts"
FIG = ROOT / "Paper_manuscript" / "figures_main"

# ---- time convention (corrected before any execution): event at 5 s, run to 200 s => post-event horizon 195 s
EVENT_T = 5.0
T_END = 200.0
T_POST = T_END - EVENT_T            # 195 s (v2 used 200 s after the event: inconsistent with a 200 s run)
DT = 2.0 ** -8
VLO, VHI = 0.95, 1.05

UNITS = ["SG30", "SG31", "SG33", "SG35", "SG38", "SG39", "GFM32", "GFM37", "GFM34", "GFM36"]
UNIT_BUS = [30, 31, 33, 35, 38, 39, 32, 37, 34, 36]
SLACK = "SG39"
PV_UNITS = [u for u in UNITS if u != SLACK]          # 9 p0 variables (SG30,31,33,35,38 and GFM32,37,34,36)
PV_IDX = [UNITS.index(u) for u in PV_UNITS]
SLACK_IDX = UNITS.index(SLACK)
N_PV, N_V, N_Z = 9, 10, 19

BUDGET = {"P3-A": 8, "P3-B": 16, "P3-C": 24}
BUDGET_TOTAL = 48

# ---- partition (provisional, unsealed; reproduced by dec054_partition.py)
SEED = "DEC054-R1-provisional-seed-v1"
ELIGIBLE = [3, 7, 8, 12, 15, 16, 20, 23, 24, 25, 26, 27, 28, 29]
DESIGN = [8, 23, 28, 25]
TUNE = [7, 20, 16, 24]
TEST = [3, 29, 15, 12, 27, 26]
CALIBRATION_ONLY = [4, 18, 21]                         # historical dynamic results: never blind

# ---- PROPOSED parameters (v2 sec 3.5, 4, 5): NOT SEALED until P1; the frozen file will copy them
PROPOSED = {
    "kappa": 1.5, "eps_floor_pu": 1e-3, "tau_cut_pu": 1e-4, "K_max": 15, "N_it": 200, "kkt_tol": 1e-3,
    "r_tr_p0_pu": 0.05, "r_tr_v0_pu": 0.01, "P_floor_pu": 0.05, "lambda_pat": 1.0, "v_scale_pu": 0.05,
    "alpha_diag": 0.10, "m1_rho_grid_note": "rho fixed on DESIGN/TUNE statics only",
    "t_grid_segments": [[0.0, 1.0, 101], [1.0, 10.0, 91], [10.0, T_POST, 186]],
    "init_tol": 1e-8, "status": "PROPOSED_NOT_SEALED",
}

# ---- status vocabularies (protocol)
OPF_STATUS = ("FEASIBLE_PREDICTED", "LOCAL_OPTIMUM_FOUND", "STAGNATED_EXISTING_CUT", "ITERATION_BUDGET_EXHAUSTED", "SOLVER_FAILED", "INFEASIBLE_NOT_DEMONSTRATED")
TDS_STATUS = ("TDS_SAFE_OBSERVED", "TDS_PHYSICAL_VIOLATION", "TDS_NUMERICAL_FAILURE")


def sha_file(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sha_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ------------------------------------------------------------------ gate + ledger
class GateError(RuntimeError):
    pass


def backup_gate(art_dir: Path | None = None) -> dict:
    """The only source of truth for the independent-backup gate: backup manifest + preservation test of P0."""
    art_dir = art_dir or ART
    bm = json.loads((art_dir / "IEEE39_DEC054_backup_manifest.json").read_text(encoding="utf-8"))
    pt = json.loads((art_dir / "IEEE39_DEC054_preservation_test.json").read_text(encoding="utf-8"))
    ok = bm.get("status") == "BACKUP_VERIFIED" and pt.get("independent_backup_verified") is True
    return {"verified": bool(ok), "status": bm.get("status"), "gate0": bm.get("gate0"), "independent": pt.get("independent_backup_verified")}


LEDGER_COLS = ["tds_id", "block", "scenario", "method", "run_id", "purpose", "status", "t_start", "dt", "solver", "notes"]   # same header as the P0 ledger file (header only)


@dataclass
class TdsLedger:
    """Append-only ledger.  `request` is the only way to obtain a TDS id; it enforces the backup gate and the 8/16/24/48 budgets.  Failed runs
    are recorded by `complete` (a second append-only row); nothing is ever edited or deleted."""
    path: Path
    art_dir: Path | None = None
    rows: list = field(default_factory=list)

    def __post_init__(self):
        self.path = Path(self.path)
        if not self.path.exists():
            with open(self.path, "x", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(LEDGER_COLS)
        with open(self.path, encoding="utf-8") as f:
            self.rows = list(csv.DictReader(f))

    def used(self, block: str | None = None) -> int:
        reqs = [r for r in self.rows if r["status"] == "REQUESTED"]
        return len(reqs) if block is None else sum(r["block"] == block for r in reqs)

    def _append(self, row: dict):
        row = {c: row.get(c, "") for c in LEDGER_COLS}
        fd = os.open(self.path, os.O_WRONLY | os.O_APPEND)
        try:
            with os.fdopen(fd, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([row[c] for c in LEDGER_COLS])
        except Exception:
            raise
        self.rows.append(row)

    def request(self, block: str, scenario: str, method: str, run_id: str, purpose: str, solver: str = "trapezoid dt=2^-8") -> str:
        if block not in BUDGET:
            raise GateError(f"unknown block {block}")
        if not purpose.strip() or not run_id.strip():
            raise GateError("a TDS needs a run_id and a justification before launch")
        if not backup_gate(self.art_dir)["verified"]:
            raise GateError("STOP_BACKUP_NOT_VERIFIED: no TDS may be requested before BACKUP_VERIFIED")
        if any(r["run_id"] == run_id and r["status"] == "REQUESTED" for r in self.rows):
            raise GateError(f"run_id {run_id} already requested (no silent retries)")
        if self.used() >= BUDGET_TOTAL:
            raise GateError("global TDS budget exhausted")
        if self.used(block) >= BUDGET[block]:
            raise GateError(f"block {block} budget exhausted")
        tid = f"TDS{self.used() + 1:02d}"
        self._append({"tds_id": tid, "block": block, "scenario": scenario, "method": method, "run_id": run_id, "purpose": purpose, "status": "REQUESTED", "dt": DT, "solver": solver})
        return tid

    def complete(self, tds_id: str, status: str, notes: str = ""):
        if status not in TDS_STATUS:
            raise GateError(f"status must be one of {TDS_STATUS}")
        req = [r for r in self.rows if r["tds_id"] == tds_id and r["status"] == "REQUESTED"]
        if not req:
            raise GateError("unknown tds_id")
        r = req[0]
        self._append({"tds_id": tds_id, "block": r["block"], "scenario": r["scenario"], "method": r["method"], "run_id": r["run_id"], "purpose": r["purpose"], "status": status, "notes": notes, "dt": DT})
