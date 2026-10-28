"""DEC-054 outcome metrics (post-processing of stored series; v2 sec 5.5).  Violation = margin < 0 at any stored sample (tolerance class 1e-3 pu reported separately).
Jump and excursion are reported separately: first stored sample strictly after t_e (proxy of t_e^+) vs the later maximum.  Sharing is measured against the
executed pn(z) (never against another dispatch's Pn: DEC-053 sharing artefact).  The plain mean of BusFreq is NOT a COI."""
from __future__ import annotations

import numpy as np

from dec054_common import EVENT_T, VHI, VLO


def violations(t, P, Q, V, lim, pn, t_event: float = EVENT_T, tol: float = 1e-3, include_event_sample: bool = False) -> dict:
    t, P, Q, V = (np.asarray(a, float) for a in (t, P, Q, V))
    # events applied through the dist_fn mechanism (callback at t_e before the step) are already in the sample AT t_e (include_event_sample=True);
    # events applied through ANDES `Alter` appear from the first sample after t_e (default)
    post = (t >= t_event - 1e-9) if include_event_sample else (t > t_event + 1e-9)
    S = np.hypot(P, Q)
    j0 = int(np.where(post)[0][0])
    dt = float(np.median(np.diff(t)))
    marg = {"Pmax": lim["pmax"] - P, "Pmin": P - lim["pmin"], "Qmax": lim["qmax"] - Q, "Qmin": Q - lim["qmin"], "Smax": lim["smax"] - S}
    out = {"unit": {}}
    for nm, a in marg.items():
        ap = a[post]
        out["unit"][nm] = {"min_margin": ap.min(axis=0), "max_excess": np.maximum(-ap, 0).max(axis=0), "t_violation_s": (ap < 0).sum(axis=0) * dt,
                           "violates": (ap < 0).any(axis=0), "violates_tol": (ap < -tol).any(axis=0)}
    pm = marg["Pmax"]
    out["jump_excess_Pmax"] = np.maximum(-pm[j0], 0)                          # at the first sample after the event
    out["later_excess_Pmax"] = np.maximum(-pm[j0 + 1:], 0).max(axis=0) if len(t) > j0 + 1 else np.zeros(P.shape[1])
    out["V_outside_buses"] = int(((V < VLO) | (V > VHI)).any(axis=0).sum())
    out["V_outside_buses_post"] = int(((V[post] < VLO) | (V[post] > VHI)).any(axis=0).sum())
    out["V_min_post"], out["V_max_post"] = float(V[post].min()), float(V[post].max())
    out["V_t_outside_s"] = float(((V < VLO) | (V > VHI)).any(axis=1).sum() * dt)
    fin = t >= t[-1] - 5.0
    out["E_share_P_vs_pn"] = float(np.ptp(P[fin].mean(axis=0) / np.asarray(pn, float)))
    out["n_violating_pairs_P"] = int(out["unit"]["Pmax"]["violates"].sum() + out["unit"]["Pmin"]["violates"].sum())
    return out
