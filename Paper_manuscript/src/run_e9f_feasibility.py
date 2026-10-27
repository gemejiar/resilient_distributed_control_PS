"""E9-F validation: nonlinear-consistent HOCBF conditions with the eight GFM rate channels as the only QP inputs (SG references stay under the original RDC and enter the drift).

At chosen instants of the B2 replay (S0, the original P+ and Q+ steps, and the two smooth 5 s load ramps defined below) the engine of e9f_engine builds
  * the exact (nonlinear, algebraics and curvature included) time derivatives h^(1..3) of every barrier along the flow with v_GFM = 0, the SG references moving at their RDC rates
    and the load following its known profile (its time derivatives enter through the clock state);
  * the relative-degree check of every output with respect to the eight selected channels (C A^k B_v for k = 0, 1 must vanish, k = 2 must not);
  * the psi-conditions of C_H and the affine HOCBF constraints A v_GFM >= b with the degree-one GFM reference barriers;
  * the independent feasibility audit (two LP algorithms, two QP solvers, conflicting rows).
Declared before running: lambda = 2 s^-1; rate envelope = observed RDC maxima (experimental candidate bound, not hardware); smooth ramps = quintic C2 smoothstep from t = 5 s to
t = 10 s whose final value equals the original step (58.564 MW at bus 4, 17.345 MVAr at bus 21); protection of an event may start only at the first probe after which the state is in C_H
and the QP is feasible at all later probes (no invariance is claimed for the interval before it).  The QP is NOT applied to the plant here.
"""

from __future__ import annotations

import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

os.environ["C2_VARIANT"] = "C2t"

import andes
import numpy as np

import e9a_hocbf as H
import e9a_linear as L
import e9b_tools as T
import e9f_engine as E
import run_b3_ieee39 as b
import run_e8_ieee39 as e8
from e9b_variant import HOOK, TAG, VARIANT
from run_e0_ieee39 import ARTIFACTS_DIR, git_commit, sha256

PROJECT = float(os.environ.get("E9F_PROJECT_FAST", "0"))      # lambda_c [1/s] of the slow-manifold projection (0 = off)
OUT = ARTIFACTS_DIR / f"IEEE39_E9F_feasibility{TAG}{'_slow' if PROJECT else ''}.json"
EVENT = 5.0
LAM = 2.0
EPS1, EPS2 = 3.0e-4, 6.0e-4
HORIZON = 60.0
PROBES = [4.9, 4.99, 5.004, 5.02, 5.1, 5.5, 6.0, 7.0, 7.72, 8.5, 10.0, 12.0, 15.0, 20.0, 30.0, 45.0, 59.0]
ENVELOPE = {"S0": (0.616, 0.0154), "P+ step": (0.616, 0.0154), "Q+ step": (0.195, 0.0154), "P+ ramp": (0.616, 0.0154), "Q+ ramp": (0.195, 0.0154)}
CASES = {"S0": ("S0", None), "P+ step": ("P+", None), "Q+ step": ("Q+", None),
         "P+ ramp": ("S0", E.Disturbance("P", 0.58564, EVENT, 5.0)), "Q+ ramp": ("S0", E.Disturbance("Q", 0.17345, EVENT, 5.0))}


def make_dist_fn(dist: E.Disturbance | None):
    if dist is None or dist.kind is None:
        return None
    state: dict[str, Any] = {}

    def fn(t, s):
        if "base" not in state:
            bus = [int(x) for x in s.PQ.bus.v]
            state["i"] = bus.index(4 if dist.kind == "P" else 21)
            state["base"] = float((s.PQ.Ppf if dist.kind == "P" else s.PQ.Qpf).v[state["i"]])
        (s.PQ.Ppf if dist.kind == "P" else s.PQ.Qpf).v[state["i"]] = state["base"] + dist.value(float(t))
    return fn


class NLProber:
    def __init__(self, name: str, dist: E.Disturbance | None):
        self.name, self.dist, self.done, self.rows = name, dist, set(), []
        self.vref = np.concatenate([np.full(4, ENVELOPE[name][0]), np.full(4, ENVELOPE[name][1])])

    def __call__(self, t, sys_, ctx, st, vnom_p, vnom_q):
        for tp in PROBES:
            if tp in self.done or t < tp:
                continue
            self.done.add(tp)
            self.rows.append(self.evaluate(t, sys_, ctx, st, vnom_p, vnom_q))
            print(f"  [{self.name}] t={t:.4f} outside={self.rows[-1]['C_H']['n_outside']} s*={self.rows[-1]['audit']['authority_scale_min']} qp={self.rows[-1]['audit']['qp']['SLSQP']['converged']} "
                  f"({self.rows[-1]['cost_s']['total']:.2f}s)", flush=True)

    def evaluate(self, t, sys_, ctx, st, vnom_p, vnom_q) -> dict[str, Any]:
        t_all = time.perf_counter()
        t1 = time.perf_counter()
        lin = L.linearize(sys_, ctx)
        t_lin = time.perf_counter() - t1
        eng = E.Engine(sys_, ctx, st, lin, self.dist, t_now=float(t))
        proj = eng.project_fast(PROJECT) if PROJECT else None
        y_base = eng.y_base.copy()
        y_s, fd = eng.solve(eng.xt0())
        rec: dict[str, Any] = {"t_s": float(t), "target_s": None, "projection": proj, "base_solve_max_y_diff": float(np.abs(y_s - y_base).max()), "newton_residual": eng.last_residual}
        t2 = time.perf_counter()
        D1 = eng.jets(3, EPS1)
        t_jets = time.perf_counter() - t2
        D2 = eng.jets(3, EPS2)
        coeff = eng.gfm_coefficients()
        pset, qset = np.asarray(st["pset"], float), np.asarray(st["qset"], float)
        A, b_, meta, A_ref, b_ref, meta_ref = E.hocbf_rows(D1, coeff, ctx["lim"], LAM, pset, qset)
        # eps consistency of the third derivatives of the barrier functions (two differencing steps)
        A2, b2, meta2, *_ = E.hocbf_rows(D2, coeff, ctx["lim"], LAM, pset, qset)
        sc = np.maximum(np.abs(b_), 1e-6)
        rec["eps_consistency_rhs_median_rel"] = float(np.median(np.abs(b_ - b2) / sc))
        rec["eps_consistency_rhs_max_abs"] = float(np.abs(b_ - b2).max())
        rec["relative_degree_check"] = {k: coeff[k] for k in ("M0_max", "M1_max", "M2_min_row_max", "relative_degree_3_all_outputs")}
        kinds = ("P+", "P-", "Q+", "Q-", "S", "V+", "V-")
        outside = [m for m in meta if not m["inside"]]
        rec["C_H"] = {"n_barriers": len(meta), "n_outside": len(outside), "outside_by_kind": {k: sum(1 for m in outside if m["kind"] == k) for k in kinds},
                      "h_negative": [m["name"] for m in meta if m["h0"] < 0], "worst_psi": sorted([(m["name"], m["psi_min"]) for m in meta], key=lambda x: x[1])[:5],
                      "reference_barriers_outside": [m["name"] for m in meta_ref if not m["inside"]], "min_h_by_kind": {k: float(min(m["h0"] for m in meta if m["kind"] == k)) for k in kinds}}
        vnom = np.concatenate([vnom_p[6:10], vnom_q[6:10]]) if t >= EVENT else np.zeros(8)
        ev = {"A": A, "b": b_, "A_ref": A_ref, "b_ref": b_ref, "meta": [{"name": m["name"], "r": 3} for m in meta], "meta_ref": [{"name": m["name"], "r": 1} for m in meta_ref]}
        t3 = time.perf_counter()
        rec["audit"] = T.feasibility_audit(ev, vnom, self.vref, ev["meta"], ctx["lim"], None)
        t_audit = time.perf_counter() - t3
        names_idx = {m["name"]: i for i, m in enumerate(meta)}
        rec["conflict_detail"] = []
        for c_ in rec["audit"]["conflict_set_top"][:3]:
            j = names_idx.get(c_["name"])
            if j is not None:
                rec["conflict_detail"].append({"name": c_["name"], "h_jets": meta[j]["h"], "psi": meta[j]["psi"], "b": float(b_[j]), "lead_norm": float(np.linalg.norm(A[j])), "A_times_vnom": float(A[j] @ vnom),
                                               "max_possible_A_v": float(np.abs(A[j] * self.vref).sum())})
        rec["SG31_P+"] = next(({"h0": m["h0"], "psi": m["psi"]} for m in meta if m["name"] == "P+1"), None)
        rec["SG35_P+"] = next(({"h0": m["h0"], "psi": m["psi"]} for m in meta if m["name"] == "P+3"), None)
        rec["disturbance_value_pu"] = self.dist.value(float(t)) if self.dist else None
        eng.close()
        rec["cost_s"] = {"linearize": t_lin, "exact_jets_two_eps_each": t_jets, "n_algebraic_solves": eng.n_solves, "solve_total": eng.t_solve, "audit_lp_qp": t_audit, "total": time.perf_counter() - t_all}
        return rec


def run_case(name: str) -> dict[str, Any]:
    sc, dist = CASES[name]
    pr = NLProber(name, dist)

    def hook(system, ctx):
        HOOK(system, ctx)
        system.TDS.config.tf = HORIZON

    _, data, diag = b.run("B2", sc, probe=pr, init_hook=hook, dist_fn=make_dist_fn(dist))
    rows = pr.rows
    for r, tp in zip(rows, [p for p in PROBES if p <= HORIZON]):
        r["target_s"] = tp
    pre = [r for r in rows if r["t_s"] < EVENT - 0.001][-1]
    post = [r for r in rows if r["t_s"] > EVENT + 0.002]
    ok = lambda r: bool(r["C_H"]["n_outside"] == 0 and not r["C_H"]["h_negative"] and not r["C_H"]["reference_barriers_outside"])  # noqa: E731
    qp = lambda r: bool(r["audit"]["qp"]["SLSQP"]["converged"] and r["audit"]["qp"]["trust-constr"]["converged"] and r["audit"]["qp_solvers_agree"])  # noqa: E731
    first = post[0] if post else None
    start = next((r["t_s"] - EVENT for r in post if all(ok(q) and qp(q) for q in post if q["t_s"] >= r["t_s"])), None)
    v = {"pre_event_in_CH_and_QP_feasible": bool(ok(pre) and qp(pre)), "first_probe_after_event_s": first["t_s"] - EVENT if first else None,
         "first_probe_after_event_in_CH": ok(first) if first else None, "first_probe_after_event_QP_feasible": qp(first) if first else None,
         "protection_may_start_at_s_after_event": start,
         "nominal_satisfies_all_after_start": bool(all(r["audit"]["nominal_satisfies_all"] for r in post if start is not None and r["t_s"] - EVENT >= start)) if start is not None else None,
         "relative_degree_3_verified_all_probes": bool(all(r["relative_degree_check"]["relative_degree_3_all_outputs"] for r in rows)),
         "solvers_agree_all_probes": bool(all(r["audit"]["qp_solvers_agree"] and r["audit"]["independent_check"]["agree"] for r in rows)),
         "inside_CH_and_feasible_at_every_probe_after_event": bool(all(ok(r) and qp(r) for r in post))}
    return {"scenario": sc, "disturbance": None if dist is None else {"kind": dist.kind, "amplitude_pu": dist.amp, "t_start_s": dist.t0, "duration_s": dist.T, "profile": "quintic C2 smoothstep"},
            "diag": diag, "probes": rows, "verdict": v}


def main() -> int:
    names = sys.argv[1:] or list(CASES)
    result: dict[str, Any] = {"variant": VARIANT, "git_commit": git_commit(), "andes": andes.__version__, "python": platform.python_version(), "lambda": LAM, "eps": [EPS1, EPS2],
                              "horizon_s": HORIZON, "probe_targets_s": PROBES, "inputs": "eight GFM rate channels (Pset, Qset of GFM32, GFM37, GFM34, GFM36); SG references under the original RDC",
                              "rate_envelope_pu_per_s": ENVELOPE, "doc": __doc__, "cases": {}}
    for n in names:
        result["cases"][n] = run_case(n)
        OUT.write_text(json.dumps(result, indent=2, default=float), encoding="utf-8")
    result["code_sha256"] = {f: sha256(Path(__file__).parent / f) for f in ("e9f_engine.py", "e9a_linear.py", "e9a_hocbf.py", "e9b_tools.py", "run_e9f_feasibility.py", "run_b3_ieee39.py")}
    OUT.write_text(json.dumps(result, indent=2, default=float), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
