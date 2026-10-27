"""DEC-054 empirical margin (EMPIRICAL_LOCATION_AWARE_MARGIN) and partition.  No conformal coverage is claimed (v2 sec 3.5)."""
from __future__ import annotations

import hashlib
import math

import numpy as np

from dec054_common import ELIGIBLE, PROPOSED, SEED


def conformal_rank_finite(n: int, alpha: float) -> bool:
    """Split-conformal one-sided quantile is finite only if ceil((n+1)(1-alpha)) <= n.  For n=8, alpha=0.10 the rank is 9 > 8 (+inf)."""
    return math.ceil((n + 1) * (1 - alpha)) <= n


def eps_margin(residuals, kappa=None, floor=None) -> float:
    """eps = max(floor, kappa * max positive residual).  residuals: observed - predicted (signed, >0 = prediction optimistic)."""
    kappa = PROPOSED["kappa"] if kappa is None else kappa
    floor = PROPOSED["eps_floor_pu"] if floor is None else floor
    r = np.asarray(residuals, float)
    worst = float(np.max(r)) if r.size else 0.0
    return max(floor, kappa * max(worst, 0.0))


def lobo_diagnostic(res_by_bus: dict) -> dict:
    """Leave-one-bus-out DIAGNOSTIC: the margin built from all other buses vs the held-out residuals; reports signed errors and violations (no coverage claim)."""
    out = {}
    for b, r in res_by_bus.items():
        rest = np.concatenate([np.asarray(v, float).ravel() for k, v in res_by_bus.items() if k != b]) if len(res_by_bus) > 1 else np.array([])
        eps = eps_margin(rest)
        held = np.asarray(r, float).ravel()
        out[b] = {"eps_from_others": eps, "max_heldout_residual": float(held.max()) if held.size else 0.0, "n_exceed": int((held > eps).sum())}
    return out


def partition(seed: str = SEED, buses=None, n_test: int = 6, n_tune: int = 4) -> dict:
    """Deterministic split by bus (unit of analysis = bus): rank by SHA-256(seed|bus); first n_test -> TEST, next n_tune -> TUNE, rest -> DESIGN."""
    buses = list(ELIGIBLE if buses is None else buses)
    rank = sorted(buses, key=lambda b: hashlib.sha256(f"{seed}|{b}".encode()).hexdigest())
    return {"rank": rank, "TEST": rank[:n_test], "TUNE": rank[n_test:n_test + n_tune], "DESIGN": rank[n_test + n_tune:]}
