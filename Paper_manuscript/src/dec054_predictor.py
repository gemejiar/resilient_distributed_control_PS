"""DEC-054 post-event affine predictor anchored at t_e^+ (v2 sec 2.4, 3.3, 3.4).

  delta_xi' = A d_xi + f,  d_xi(t_e^+) = 0,   D_i(t) = C_i d_xi(t)   (so D_i(0) = 0 by construction: the algebraic jump is NOT recomputed)
  E_i^+ = max(0, max_{t in [0, T_post]} D_i),   E_i^- = max(0, max_t -D_i),   T_post = 195 s (event at 5 s, run to 200 s).
Propagation uses the action of the matrix exponential of the augmented matrix M = [[A, f],[0, 0]] on e_{n+1} (scipy expm_multiply: scaling-and-squaring
Taylor, no eigenvector expansion), on predeclared grids plus bounded local refinement.  A grid/refined maximum is NOT a certified global time maximum;
an estimate of the sampling error (denser grid) is returned."""
from __future__ import annotations

import numpy as np
from scipy.sparse.linalg import expm_multiply

from dec054_common import PROPOSED, T_POST


def time_grid(segments=None) -> np.ndarray:
    segments = segments or PROPOSED["t_grid_segments"]
    ts = []
    for a, b, n in segments:
        seg = np.linspace(a, b, int(n))
        ts.append(seg if not ts else seg[1:])
    return np.concatenate(ts)


def _traj(M, n, t):
    """delta_xi(t) for uniformly spaced t (t[0] may be 0): last column of expm(M t) restricted to the first n rows."""
    v0 = np.zeros(M.shape[0])
    v0[-1] = 1.0
    if len(t) == 1:
        return expm_multiply(M * t[0], v0)[None, :n]
    X = expm_multiply(M, v0, start=t[0], stop=t[-1], num=len(t), endpoint=True)
    return X[:, :n]


def propagate(A, f, C, segments=None):
    """D(t) (m x n_t) on the declared grid. A (n,n), f (n,), C (m,n)."""
    A, f, C = np.asarray(A, float), np.asarray(f, float), np.atleast_2d(np.asarray(C, float))
    n = A.shape[0]
    M = np.zeros((n + 1, n + 1))
    M[:n, :n] = A
    M[:n, n] = f
    segments = segments or PROPOSED["t_grid_segments"]
    ts, D = [], []
    for a, b, num in segments:
        X = _traj(M, n, np.linspace(a, b, int(num)))
        t = np.linspace(a, b, int(num))
        if ts:
            X, t = X[1:], t[1:]
        ts.append(t)
        D.append(X @ C.T)
    return np.concatenate(ts), np.vstack(D).T, M


def excursion(A, f, C, segments=None, refine: bool = True, check_density: int = 2) -> dict:
    """Ehat^+/Ehat^- per output with a local refinement around grid maxima and a sampling-error estimate (dense-grid difference)."""
    t, D, M = propagate(A, f, C, segments)
    n = np.asarray(A).shape[0]
    Cm = np.atleast_2d(np.asarray(C, float))

    def refine_one(k, sign):
        row = D[k] * sign
        j = int(np.argmax(row))
        best, tb = row[j], t[j]
        if refine and 0 < j < len(t) - 1:
            lo, hi = t[j - 1], t[j + 1]
            for _ in range(24):   # golden-section on a unimodal bracket (not a global guarantee)
                m1, m2 = lo + 0.382 * (hi - lo), lo + 0.618 * (hi - lo)
                v1 = sign * (Cm[k] @ _traj(M, n, [m1])[0])
                v2 = sign * (Cm[k] @ _traj(M, n, [m2])[0])
                if v1 > v2:
                    hi = m2
                else:
                    lo = m1
                if max(v1, v2) > best:
                    best, tb = max(v1, v2), (m1 if v1 > v2 else m2)
        return max(best, 0.0), float(tb)

    m = D.shape[0]
    up = [refine_one(k, 1.0) for k in range(m)]
    dn = [refine_one(k, -1.0) for k in range(m)]
    # sampling-error estimate: same maxima on a grid `check_density` times denser
    seg2 = [[a, b, (int(num) - 1) * check_density + 1] for a, b, num in (segments or PROPOSED["t_grid_segments"])]
    _, D2, _ = propagate(A, f, C, seg2)
    e_up2, e_dn2 = np.maximum(D2.max(axis=1), 0.0), np.maximum((-D2).max(axis=1), 0.0)
    E_up, E_dn = np.array([u[0] for u in up]), np.array([d[0] for d in dn])
    return {"E_up": E_up, "E_dn": E_dn, "t_up": np.array([u[1] for u in up]), "t_dn": np.array([d[1] for d in dn]),
            "sampling_error_up": np.abs(np.maximum(E_up, e_up2) - E_up), "sampling_error_dn": np.abs(np.maximum(E_dn, e_dn2) - E_dn),
            "D0": D[:, 0].copy(), "t": t, "D": D}


def monitor(A, f, T_rows, lo, hi, margin: float = 0.0, segments=None) -> dict:
    """Validity monitor: predicted trajectory of limiter-related rows R delta_xi + base must stay inside (lo, hi) by `margin`; flags MODE_CHANGE otherwise.
    T_rows: (k, n) rows, lo/hi: (k,) bounds on those rows relative to the post-jump point."""
    t, D, _ = propagate(A, f, T_rows, segments)
    worst = np.minimum((D - np.asarray(lo)[:, None]).min(axis=1), (np.asarray(hi)[:, None] - D).min(axis=1))
    return {"MODE_CHANGE": bool(np.any(worst < margin)), "worst_distance": worst}
