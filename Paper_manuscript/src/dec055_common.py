"""DEC-055 common definitions (architecture B): operating conditions, partitions, severities, thresholds, the cell registry and the pure
classification / statistics helpers.  Nothing here runs ANDES; every function is unit-tested (test_dec055.py)."""
from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np

import dec054_common as C54

ROOT = C54.ROOT
ART, FIG, CASES = C54.ART, C54.FIG, ROOT / "Paper_manuscript" / "cases"
SRC = ROOT / "Paper_manuscript" / "src"
STATE = C54.RUNS_DIR.parent / "DEC055_state"           # local, Git-excluded (Paper_manuscript/backups/)
UNITS, UNIT_BUS, PV_UNITS = C54.UNITS, C54.UNIT_BUS, C54.PV_UNITS
EVENT_T, T_END, DT = C54.EVENT_T, C54.T_END, C54.DT

# ---------------------------------------------------------------- operating conditions (point 7 of the authorization)
BASE_CASE = CASES / "ieee39_C2t_6SG_4GFM_KPv1p5.xlsx"   # frozen C2t case; never modified
OC = {
    "OC1": {"load_scale": 1.00, "case": BASE_CASE},
    "OC2": {"load_scale": 0.90, "case": CASES / "ieee39_C2t_6SG_4GFM_KPv1p5_DEC055_OC2_load090.xlsx"},
    "OC3": {"load_scale": 1.10, "case": CASES / "ieee39_C2t_6SG_4GFM_KPv1p5_DEC055_OC3_load110.xlsx"},
}
# OC generation rule (declared before any computation): PQ p0 and q0 scaled by s (power factor preserved); PV p0 scaled by s and capped at
# pmax - PV_CAP_BACKOFF_PU; v0, Sn, Vn, all dynamic parameters and the topology unchanged; the Slack balances the remainder in PFlow.
# This only fixes the reference point z_ref of the OC; the pre-event dispatch of every method is recomputed by the static OPF (M0) or Algorithm 1 (M3).
PV_CAP_BACKOFF_PU = 0.02

# ---------------------------------------------------------------- disturbances
DP_REF_PU = 0.58564                                       # 1 % of the C2t total P load (58.564 MW)
SEVERITY = {"S1": 0.5, "S2": 1.0, "S3": 1.5}              # S3 = stress (exploratory unless promoted by the rule in classify_s3)
CONFIRMATORY_SEVERITIES = ("S1", "S2")

# ---------------------------------------------------------------- partitions (point 5/6)
DESIGN = [8, 23, 28, 25]
TUNE = [7, 20, 16, 24]
TUNE_SEVERITIES = ("S2", "S3")
TEST = [21, 31, 39]
SEEN_NOT_TEST = {3: "DEC-054 TEST (observed)", 29: "DEC-054 TEST (observed)", 15: "DEC-054 TEST (observed)", 12: "DEC-054 TEST (observed)",
                 27: "DEC-054 TEST (observed)", 26: "DEC-054 TEST (observed)", 4: "historical P+ event (E1-E16, DEC-050..053)", 18: "DEC-051 H3-2 validation run"}
STRATEGIES = {"M0B2": "SCHEDULED", "M3B2": "SCHEDULED", "M0B1": "DEFERRED", "M3B1": "DEFERRED"}   # full factorial kept; B1 arm needs a later authorization

# ---------------------------------------------------------------- thresholds (frozen with the protocol)
THR = {
    "init_residual": 1e-8,            # PFlow/TDS.init residual for a valid initialisation
    "flat_drift_hz": 0.005, "flat_drift_pu": 1e-3, "flat_horizon_s": 20.0,     # L1
    "violation_tol_pu": 0.0,          # stored-sample violation of an implemented limit
    "ac_eq_residual": 1e-8,           # T-C (C-i) AC feasibility: equality residual after the ANDES PFlow verification
    "ac_ineq_tol": 1e-9,
    "jump_newton_tol": 1e-9,          # T-A (A2): post-jump algebraic residual
    "jump_gy_min_sv": 1e-8,           # T-A (A2): smallest singular value of g_y at the post-jump point (regularity diagnostic)
    "jump_vs_first_sample_pu": 5e-3,  # acceptance (not attribution) of the jump map against the first stored post-event sample
    "one_step_attribution_pu": 1e-6,  # a jump/sample difference is attributed to one integrator step only if the one-step replica reproduces the sample to this
    "f_restore_hz": 0.01, "f_restore_t_s": (120.0, 200.0),
    "rocof_window_s": 0.1,
    "tb_root_residual": 1e-10,
    "sign_test_alpha": 0.05,
}


def oc_amp(sev: str) -> float:
    return SEVERITY[sev] * DP_REF_PU


# ---------------------------------------------------------------- cell registry (point 9)
CELL_COLS = ["cell_id", "oc", "partition", "bus", "severity", "amp_pu", "strategy", "schedule", "tc_class", "ta_M0", "ta_M3", "s3_status",
             "confirmatory", "exclusion_reason", "notes"]


def enumerate_cells() -> list[dict]:
    """Every (OC, partition, bus, severity[, strategy]) cell of the protocol, including those that will never be simulated."""
    rows = []
    for oc in OC:
        for part, buses, sevs in (("DESIGN", DESIGN, tuple(SEVERITY)), ("TUNE", TUNE, TUNE_SEVERITIES), ("TEST", TEST, tuple(SEVERITY))):
            for b in buses:
                for s in sevs:
                    base = {"oc": oc, "partition": part, "bus": b, "severity": s, "amp_pu": oc_amp(s)}
                    if part == "TEST":
                        for st, sch in STRATEGIES.items():
                            rows.append(dict(base, cell_id=f"{oc}_{part}_b{b}_{s}_{st}", strategy=st, schedule=sch))
                    else:
                        rows.append(dict(base, cell_id=f"{oc}_{part}_b{b}_{s}", strategy="M3B2" if part == "TUNE" else "static",
                                         schedule="SCHEDULED_L2" if part == "TUNE" else "STATIC_ONLY"))
    return rows


# ---------------------------------------------------------------- classifications
def classify_tc(capacity_ok: bool, ac: dict | None) -> str:
    """T-C (C-i)/(C-iii) label of one disturbance (controller-independent).  PROVEN_INFEASIBLE only from the necessary capacity condition;
    AC_FEASIBLE only with a verified AC point (residual and limits); everything else is AC_UNDETERMINED (a solver failure is not a proof)."""
    if not capacity_ok:
        return "PROVEN_INFEASIBLE"
    if ac and ac.get("success") and ac.get("eq_residual", math.inf) <= THR["ac_eq_residual"] and ac.get("ineq_min", -math.inf) >= -THR["ac_ineq_tol"] and ac.get("andes_verified") is True:
        return "AC_FEASIBLE"
    return "AC_UNDETERMINED"


def capacity_necessary(pmax_total: float, load_total_post: float) -> bool:
    """Necessary condition (eq:capacity-necessary with A empty and P_loss >= 0): sum Pmax >= P_load.  False proves E_C(d) empty."""
    return pmax_total >= load_total_post


def classify_ta(jump: dict | None, lim: dict, vlo=C54.VLO, vhi=C54.VHI) -> dict:
    """T-A label of one (dispatch, disturbance): margins a_j of every implemented limit at t_e+ (P, Q, S of the 10 units, V of the 39 buses).
    UNVERIFIED if (A2) cannot be checked (Newton not converged, residual above tolerance or singular g_y)."""
    if not jump or not jump.get("ok") or not (jump.get("residual", math.inf) <= THR["jump_newton_tol"]) or not (jump.get("gy_min_sv", 0.0) >= THR["jump_gy_min_sv"]):
        return {"label": "UNVERIFIED", "reason": "A2 not verified" if jump else "no jump"}
    P, Q, V = (np.asarray(jump[k], float) for k in ("P_plus", "Q_plus", "V_plus"))
    m = {"Pmax": lim["pmax"] - P, "Pmin": P - lim["pmin"], "Qmax": lim["qmax"] - Q, "Qmin": Q - lim["qmin"], "Smax": lim["smax"] - np.hypot(P, Q),
         "Vmax": vhi - V, "Vmin": V - vlo}
    worst = {k: float(np.min(v)) for k, v in m.items()}
    lab = "ADMISSIBLE" if min(worst.values()) >= -THR["violation_tol_pu"] else "NOT_ADMISSIBLE"
    return {"label": lab, "worst": worst, "violated": sorted(k for k, v in worst.items() if v < -THR["violation_tol_pu"])}


def classify_s3(tc: str, m3_design_status: str, ta_m3: str) -> str:
    """S3 (stress) cells become confirmatory only if all three pre-TDS conditions hold."""
    ok = tc == "AC_FEASIBLE" and m3_design_status in ("FEASIBLE_PREDICTED", "LOCAL_OPTIMUM_FOUND") and ta_m3 == "ADMISSIBLE"
    return "S3_PROMOTED_CONFIRMATORY" if ok else "STRESS_EXPLORATORY"


def confirmatory(row: dict) -> bool:
    if row["partition"] != "TEST" or row["tc_class"] != "AC_FEASIBLE" or row.get("exclusion_reason"):
        return False
    return row["severity"] in CONFIRMATORY_SEVERITIES or row.get("s3_status") == "S3_PROMOTED_CONFIRMATORY"


# ---------------------------------------------------------------- refutation per cell (point 9 of the previous correction)
def safety_verdict(test_rows: list[dict]) -> dict:
    """Claim C2 ('M3+B2 shows no stored-sample violation in every confirmatory TEST cell').  A single violating cell refutes it; the list of
    refuting cells is returned in full (never an aggregate rate)."""
    conf = [r for r in test_rows if r.get("strategy") == "M3B2" and r.get("confirmatory")]
    pending = [r["cell_id"] for r in conf if r.get("tds_status") is None]
    refuting = [r["cell_id"] for r in conf if r.get("tds_status") == "TDS_PHYSICAL_VIOLATION"]
    failed = [r["cell_id"] for r in conf if r.get("tds_status") == "TDS_NUMERICAL_FAILURE"]
    if refuting:
        v = "SAFETY_CLAIM_REFUTED"
    elif pending or failed:
        v = "INCOMPLETE"
    else:
        v = "NOT_REFUTED_IN_TESTED_CELLS"
    return {"verdict": v, "refuting_cells": refuting, "numerical_failures": failed, "pending": pending, "n_confirmatory": len(conf)}


def cluster_sign_test(cluster_scores: dict) -> dict:
    """Exact one-sided sign test over (OC, location) clusters; score > 0 favours M3.  Ties are dropped.  Conditional on the finite set of clusters."""
    s = [v for v in cluster_scores.values() if v != 0]
    n, k = len(s), sum(1 for v in s if v > 0)
    p = sum(math.comb(n, i) for i in range(k, n + 1)) / 2 ** n if n else 1.0
    return {"n_nonzero": n, "n_positive": k, "p_one_sided": p, "alpha": THR["sign_test_alpha"], "significant": bool(n and p <= THR["sign_test_alpha"])}


# ---------------------------------------------------------------- frequency metrics (point 8)
def f_coi_hz(omega_sg: np.ndarray, M: np.ndarray, Sn: np.ndarray, fn: float = 60.0) -> np.ndarray:
    """Centre-of-inertia frequency of the synchronous machines: fn * sum(M_i Sn_i omega_i) / sum(M_i Sn_i) (M = 2H on machine base)."""
    w = np.asarray(M, float) * np.asarray(Sn, float)
    return fn * (np.asarray(omega_sg, float) @ w) / w.sum()


def mean_busfreq_hz(f_bus_hz: np.ndarray) -> np.ndarray:
    """Unweighted mean of the BusFreq signals (labelled 'mean BusFreq'; never a COI)."""
    return np.asarray(f_bus_hz, float).mean(axis=1)


def rocof_window(t: np.ndarray, f: np.ndarray, t_event: float = EVENT_T, window: float | None = None) -> float:
    """RoCoF as the least-squares slope of f over [t_event, t_event + window] (declared window; no derivative of the first sample)."""
    window = THR["rocof_window_s"] if window is None else window
    t, f = np.asarray(t, float), np.asarray(f, float)
    m = (t >= t_event - 1e-12) & (t <= t_event + window + 1e-12)
    if m.sum() < 2:
        return float("nan")
    return float(np.polyfit(t[m] - t_event, f[m], 1)[0])


# ---------------------------------------------------------------- jump versus first sample (point 5 of the final corrections)
def jump_vs_first_sample(t, P, P_plus_pred, one_step_P=None, t_event: float = EVENT_T) -> dict:
    """Compare the algebraic jump prediction at t_e+ with the first stored post-event sample.  Attribution of the difference to one integrator step is made
    only if a one-step replica (computed separately with the same integrator, from the same pre-event state) reproduces the stored sample to
    THR['one_step_attribution_pu']; otherwise the difference stays UNEXPLAINED.  Acceptance uses THR['jump_vs_first_sample_pu'] and is independent of attribution."""
    t, P = np.asarray(t, float), np.asarray(P, float)
    k = int(np.searchsorted(t, t_event + 1e-12))
    sample = P[k]
    err = sample - np.asarray(P_plus_pred, float)
    out = {"t_sample": float(t[k]), "err": err.tolist(), "max_abs_err": float(np.abs(err).max()), "accepted": bool(np.abs(err).max() <= THR["jump_vs_first_sample_pu"])}
    if one_step_P is None:
        out["attribution"] = "NOT_ATTEMPTED"
    else:
        rep = float(np.abs(np.asarray(one_step_P, float) - sample).max())
        out["one_step_replica_err"] = rep
        out["attribution"] = "ONE_INTEGRATOR_STEP" if rep <= THR["one_step_attribution_pu"] else "UNEXPLAINED"
    return out


BUDGET = {"L1": 5, "L2": 32, "L3": 54, "L4": 6}
BUDGET_TOTAL = 97
LEDGER = ART / "IEEE39_DEC055_tds_ledger.csv"


class Ledger(C54.TdsLedger):
    """Append-only DEC-055 TDS ledger (same columns as DEC-054); budgets per lot; no silent retries.  The independent-backup requirement was waived by the
    investigator (DEC-054 waiver); the gate of DEC-054 is therefore not re-checked here."""

    def request(self, block, scenario, method, run_id, purpose, solver="trapezoid dt=2^-8"):
        if block not in BUDGET:
            raise C54.GateError(f"unknown lot {block}")
        if not purpose.strip() or not run_id.strip():
            raise C54.GateError("a TDS needs a run_id and a justification before launch")
        if any(r["run_id"] == run_id and r["status"] == "REQUESTED" for r in self.rows):
            raise C54.GateError(f"run_id {run_id} already requested (no silent retries)")
        if self.used() >= BUDGET_TOTAL or self.used(block) >= BUDGET[block]:
            raise C54.GateError(f"budget exhausted ({block})")
        tid = f"D55T{self.used() + 1:03d}"
        self._append({"tds_id": tid, "block": block, "scenario": scenario, "method": method, "run_id": run_id, "purpose": purpose, "status": "REQUESTED", "dt": C54.DT, "solver": solver})
        return tid


def write_cells(path: Path, rows: list[dict]) -> None:
    with open(path, "x", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, CELL_COLS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in CELL_COLS})
