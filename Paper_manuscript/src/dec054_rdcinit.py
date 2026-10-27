"""DEC-054: RDC B2 initialisation map I(z) (pure NumPy; mirrors run_e8_ieee39.py:77-85, 141-154 without editing it).

For a candidate dispatch the executors set pn=Pe(0), qn=Qe(0), pset(0)=pn, qset(0)=qn, then
  gp0,gq0 = capability_factors(pset,qset,lim); gref_p=max gp0; gref_q=max gq0; k_ip = SPEED_TARGET / sum(gp0/gref_p); d_p = 1/pn; d_q = 1/(qmax-qmin).
`d_q` depends only on the case limits.  The RDC code and gains are NOT changed; only their dispatch-dependent initial values are recomputed."""
from __future__ import annotations

import numpy as np

SPEED_TARGET = 160.0        # run_e8_ieee39.SPEED_TARGET (documented there as a priori, not tuned)


def capability_factors(pset, qset, lim):
    """Raw gP, gQ (Eqs. 28-31 with the SG substitution), clipped at 0 outside W_i (same arithmetic as run_e8_ieee39.capability_factors)."""
    pset, qset = np.asarray(pset, float), np.asarray(qset, float)
    circle = 1.0 - (pset ** 2 + qset ** 2) / lim["smax"] ** 2
    box_q = (lim["qmax"] - qset) * (qset - lim["qmin"]) / ((lim["qmax"] - lim["qmin"]) / 2.0) ** 2
    box_p = (lim["pmax"] - pset) * (pset - lim["pmin"])
    sg = lim["is_sg"]
    g_p = box_p * circle * np.where(sg, box_q, 1.0)
    g_q = circle * np.where(sg, box_q, 1.0)
    return np.maximum(g_p, 0.0), np.maximum(g_q, 0.0)


class InitError(RuntimeError):
    pass


def init_map(P_pre, Q_pre, lim, p_floor: float = 0.0) -> dict:
    """I(z) from the pre-event physical outputs (all ten units, Slack included).  Raises InitError where the executor would fail (gp0<=0 or gq0<=0)
    or where d_p = 1/pn would be undefined/negative."""
    P_pre, Q_pre = np.asarray(P_pre, float), np.asarray(Q_pre, float)
    if np.any(P_pre <= max(p_floor, 0.0)):
        raise InitError("pn must be strictly positive (and above P_floor): d_p = 1/pn")
    gp0, gq0 = capability_factors(P_pre, Q_pre, lim)
    if np.any(gp0 <= 0) or np.any(gq0 <= 0):
        raise InitError("Nominal setpoint is not in the interior of W_i")
    gref_p, gref_q = float(gp0.max()), float(gq0.max())
    k_ip = SPEED_TARGET / float((gp0 / gref_p).sum())
    return {"pn": P_pre.copy(), "qn": Q_pre.copy(), "pset0": P_pre.copy(), "qset0": Q_pre.copy(), "gp0": gp0, "gq0": gq0, "gref_p": gref_p, "gref_q": gref_q,
            "k_ip": k_ip, "d_p": 1.0 / P_pre, "d_q": 1.0 / (lim["qmax"] - lim["qmin"]),
            "gain_eff_p": k_ip * gp0 / gref_p}          # effective per-unit integral gain at activation


def stale_init(I_ref: dict) -> dict:
    """The DEC-051 hazard as a reusable object: initialisation frozen at another dispatch (used only by the A5 ablation)."""
    return {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in I_ref.items()}
