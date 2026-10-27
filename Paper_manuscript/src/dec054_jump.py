"""DEC-054 algebraic jump solver (v2 sec 2.3): with differential states and RDC references continuous, solve g(x^-, y^+, u^-, z, d) = 0 for y^+.

Generic damped Newton with a backtracking line search on ||g||; reports convergence, the smallest singular value of g_y at the solution (branch regularity)
and refuses (converged=False) rather than returning a value near singularity.  The plant adapter supplies g and g_y."""
from __future__ import annotations

import numpy as np


def solve_algebraic(g, gy, y0, tol: float = 1e-11, itmax: int = 40, sigma_min_floor: float = 1e-8) -> dict:
    y = np.array(y0, float)
    r = g(y)
    res0 = float(np.linalg.norm(r, np.inf))
    hist = [res0]
    for _ in range(itmax):
        if hist[-1] <= tol:
            break
        J = gy(y)
        try:
            dy = np.linalg.solve(J, -r)
        except np.linalg.LinAlgError:
            return {"converged": False, "y": y, "residual": hist[-1], "history": hist, "sigma_min": 0.0, "reason": "singular g_y"}
        a = 1.0
        while a > 1e-6:
            r_new = g(y + a * dy)
            if np.linalg.norm(r_new, np.inf) < (1 - 1e-4 * a) * hist[-1]:
                break
            a *= 0.5
        y = y + a * dy
        r = g(y)
        hist.append(float(np.linalg.norm(r, np.inf)))
    sig = np.linalg.svd(gy(y), compute_uv=False)
    smin = float(sig[-1])
    ok = bool(hist[-1] <= tol and smin > sigma_min_floor)
    return {"converged": ok, "y": y, "residual": hist[-1], "history": hist, "sigma_min": smin, "cond": float(sig[0] / max(smin, 1e-300)),
            "reason": "" if ok else ("near-singular branch" if hist[-1] <= tol else "no convergence")}


def jump_of(P_of_y, y_minus, y_plus):
    """Delta = h(y^+) - h(y^-) for the output map h (the algebraic jump of a physical output); differential states are unchanged."""
    return np.asarray(P_of_y(y_plus), float) - np.asarray(P_of_y(y_minus), float)


def sensitivity_dy_dd(gy_at, gd_at):
    """dy^+/dd = -g_y^{-1} g_d (local; finite amplitude changes are bounded by the evaluation grid)."""
    return -np.linalg.solve(gy_at, gd_at)
