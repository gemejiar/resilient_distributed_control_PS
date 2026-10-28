"""DEC-054 post-event affine predictor anchored at t_e^+ (v2 sec 2.4, 3.3, 3.4).

  delta_xi' = A d_xi + f,  d_xi(t_e^+) = 0,   D_i(t) = C_i d_xi(t)   (so D_i(0) = 0 by construction: the algebraic jump is NOT recomputed)
  E_i^+ = max(0, max_{t in [0, T_post]} D_i),   E_i^- = max(0, max_t -D_i),   T_post = 195 s (event at 5 s, run to 200 s).
Propagation uses the exact per-segment discretisation exp(M h) of the augmented matrix M = [[A, f],[0, 0]] (dense scaling-and-squaring Pade, no eigenvector
expansion) on predeclared piecewise-uniform grids (first segment = implicit trapezoid at the TDS sample step, i.e. what the stored ANDES samples are) plus a parabolic refinement.  A grid/refined maximum is NOT a certified global time maximum;
an estimate of the sampling error (denser grid) is returned."""
from __future__ import annotations

import numpy as np
from scipy.linalg import expm

from dec054_common import PROPOSED, T_POST


def time_grid(segments=None) -> np.ndarray:
    segments = segments or PROPOSED["t_grid_segments"]
    ts = []
    for a, b, h, *_ in segments:
        n = int(round((b - a) / h))
        seg = a + h * np.arange(n + 1)
        ts.append(seg if not ts else seg[1:])
    return np.concatenate(ts)


def propagate(A, f, C, segments=None):
    """D(t) (m x n_t) on the declared piecewise-uniform grid.  Exact discretisation per segment: one dense matrix exponential Phi=expm(M h) per distinct step
    (scaling-and-squaring Pade) and matrix-vector products; M = [[A, f],[0, 0]], state [d_xi; 1], d_xi(0)=0."""
    A, f, C = np.asarray(A, float), np.atleast_1d(np.asarray(f, float)), np.atleast_2d(np.asarray(C, float))
    n = A.shape[0]
    M = np.zeros((n + 1, n + 1))
    M[:n, :n] = A
    M[:n, n] = f
    segments = segments or PROPOSED["t_grid_segments"]
    v = np.zeros(n + 1)
    v[n] = 1.0
    ts, X = [0.0], [v[:n].copy()]
    t_cur = 0.0
    for a, b, h, *meth in segments:
        assert abs(a - t_cur) < 1e-9, "segments must be contiguous from 0"
        k = int(round((b - a) / h))
        if meth and meth[0] == "trap":      # the integrator ANDES actually uses on the stored samples (implicit trapezoid at step h)
            I = np.eye(n + 1)
            Phi = np.linalg.solve(I - 0.5 * h * M, I + 0.5 * h * M)
        else:
            Phi = expm(M * h)
        for _ in range(k):
            v = Phi @ v
            t_cur += h
            ts.append(t_cur)
            X.append(v[:n].copy())
        t_cur = a + k * h
    X = np.array(X)
    return np.array(ts), (X @ C.T).T, M


def excursion(A, f, C, segments=None, refine: bool = True, check_density: int = 2) -> dict:
    """Ehat^+/Ehat^- per output with a local refinement around grid maxima and a sampling-error estimate (dense-grid difference)."""
    t, D, M = propagate(A, f, C, segments)
    n = np.asarray(A).shape[0]
    Cm = np.atleast_2d(np.asarray(C, float))

    def refine_one(k, sign):
        """Grid maximum refined by the vertex of the parabola through the three samples around it (cheap; not a certified global time maximum)."""
        row = D[k] * sign
        j = int(np.argmax(row))
        best, tb = row[j], t[j]
        if refine and 0 < j < len(t) - 1:
            t0, t1, t2 = t[j - 1], t[j], t[j + 1]
            y0, y1, y2 = row[j - 1], row[j], row[j + 1]
            d01, d12, d02 = (y1 - y0) / (t1 - t0), (y2 - y1) / (t2 - t1), None
            c2 = (d12 - d01) / (t2 - t0)                      # second divided difference
            if c2 < 0:
                tv = 0.5 * (t0 + t1) - d01 / (2 * c2) if False else (t0 + t1 - d01 / c2) / 2.0
                tv = min(max(tv, t0), t2)
                yv = y0 + d01 * (tv - t0) + c2 * (tv - t0) * (tv - t1)
                if yv > best:
                    best, tb = yv, tv
        return max(best, 0.0), float(tb)

    m = D.shape[0]
    up = [refine_one(k, 1.0) for k in range(m)]
    dn = [refine_one(k, -1.0) for k in range(m)]
    # sampling-error estimate: same maxima on a grid `check_density` times denser
    seg2 = [[a, b, (h if (m and m[0] == "trap") else h / check_density), *m] for a, b, h, *m in (segments or PROPOSED["t_grid_segments"])]
    _, D2, _ = propagate(A, f, C, seg2)
    e_up2, e_dn2 = np.maximum(D2.max(axis=1), 0.0), np.maximum((-D2).max(axis=1), 0.0)
    E_up, E_dn = np.array([u[0] for u in up]), np.array([d[0] for d in dn])
    ok = bool(np.all(np.isfinite(D)) and np.abs(D).max() <= 50.0)          # a predicted excursion of 50 pu is a model failure (unstable linearisation), never a margin
    if not ok:
        E_up, E_dn = np.zeros_like(E_up), np.zeros_like(E_dn)
    return {"ok": ok, "E_up": E_up, "E_dn": E_dn, "t_up": np.array([u[1] for u in up]), "t_dn": np.array([d[1] for d in dn]),
            "sampling_error_up": np.abs(np.maximum(E_up, e_up2) - E_up), "sampling_error_dn": np.abs(np.maximum(E_dn, e_dn2) - E_dn),
            "D0": D[:, 0].copy(), "t": t, "D": D}


def monitor(A, f, T_rows, lo, hi, margin: float = 0.0, segments=None) -> dict:
    """Validity monitor: predicted trajectory of limiter-related rows R delta_xi + base must stay inside (lo, hi) by `margin`; flags MODE_CHANGE otherwise.
    T_rows: (k, n) rows, lo/hi: (k,) bounds on those rows relative to the post-jump point."""
    t, D, _ = propagate(A, f, T_rows, segments)
    worst = np.minimum((D - np.asarray(lo)[:, None]).min(axis=1), (np.asarray(hi)[:, None] - D).min(axis=1))
    return {"MODE_CHANGE": bool(np.any(worst < margin)), "worst_distance": worst}
