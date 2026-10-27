"""E9-C Phase 3: validation of the Lie derivatives (orders 1-4) used by the HOCBF constraints against the nonlinear DAE.

Method.  The B2 replay is run until t_f = t0 - 0.0625 s; from t_f the references are held constant (v = 0, the controller of the replay is frozen, free flow of the full nonlinear ANDES
DAE with the E8 actuator maps).  The k-th time derivative of every output (P, Q of the ten units, 39 bus voltages) and of every barrier function h_j(t) at t0 is estimated by a
polynomial fit over t0 +- 0.0625 s of the free-flow series (degrees 5, 6, 7 give an uncertainty).  This is the true L_F^k h of the nonlinear reduced system (curvature of the DAE,
algebraic effects and the quadratic S barrier included) along the free flow.  It is compared with

  frozen         c A^{k-1} z_dot0 (frozen Jacobian at t0, the approximation used in E9-A/E9-B1), for the linear barriers and for S as in E9-B1 (gradient only);
  frozen + curv  the same output derivatives combined with the exact Leibniz rule for S = smax^2 - P^2 - Q^2 (barrier curvature terms).

Decoupling coefficients (the coefficient multiplying v in the HOCBF constraint) are tested by a constant-rate ramp on one reference channel from t0 (Pset SG31, Pset GFM32, Qset GFM36):
the nonlinear response difference (ramp run minus free run) against the frozen linear prediction.  Numerical scaling (singular values of the decoupling matrix, row norms) and the cost of
each pipeline stage are recorded.  Nothing here is a certificate; it quantifies the approximation.

Gate criteria for the S0 closed-loop test (declared before running): at the S0 probe, (i) for every barrier the frozen and the true psi_k (k < r) have the same sign and are positive, and (ii) the
frozen h^(1), h^(2), h^(3) are consistent with the truth within three times the fit uncertainty or are smaller than 1e-3 of the corresponding barrier margin scale.
"""

from __future__ import annotations

import json
import os
import platform
import sys
import time
from math import comb
from pathlib import Path
from typing import Any

os.environ["C2_VARIANT"] = "C2t"

import andes
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import e9a_hocbf as H  # noqa: E402
import e9a_linear as L  # noqa: E402
import e9b_tools as T  # noqa: E402
import run_b3_ieee39 as b  # noqa: E402
import run_e8_ieee39 as e8  # noqa: E402
from e9b_variant import HOOK, TAG, VARIANT  # noqa: E402
from run_e0_ieee39 import ARTIFACTS_DIR, FIGURES_DIR, git_commit, sha256  # noqa: E402

OUT = ARTIFACTS_DIR / os.environ.get("E9C_OUT", f"IEEE39_E9C_lie_validation{TAG}.json")
FIG = FIGURES_DIR / os.environ.get("E9C_FIG", f"IEEE39_E9C_lie_validation{TAG}.png")
HALF = 0.0625
LAM = 2.0
RAMPS = {"Pset_SG31": (1, 0.5), "Pset_GFM32": (6, 0.5), "Qset_GFM36": (19, 0.2)}   # (channel, rate pu/s)
FACT = [1.0, 1.0, 2.0, 6.0, 24.0, 120.0, 720.0, 5040.0]


def poly_derivs(t: np.ndarray, y: np.ndarray, t0: float, deg: int, kmax: int = 4) -> np.ndarray:
    sel = np.abs(t - t0) <= HALF + 1e-9
    tt = t[sel] - t0
    coef, *_ = np.linalg.lstsq(np.vander(tt, deg + 1, increasing=True), y[sel], rcond=None)
    return np.stack([coef[k] * FACT[k] for k in range(kmax + 1)])    # (kmax+1, n_signals)


def barrier_series(kind: str, unit: int | None, bus: int | None, p, q, v, lim):
    if kind == "P+":
        return lim["pmax"][unit] - p[:, unit]
    if kind == "P-":
        return p[:, unit] - lim["pmin"][unit]
    if kind == "Q+":
        return lim["qmax"][unit] - q[:, unit]
    if kind == "Q-":
        return q[:, unit] - lim["qmin"][unit]
    if kind == "S":
        return lim["smax"][unit] ** 2 - p[:, unit] ** 2 - q[:, unit] ** 2
    return (1.05 - v[:, bus]) if kind == "V+" else (v[:, bus] - 0.95)


class FreeProbe:
    def __init__(self, t0: float):
        self.t0, self.done, self.rec = t0, False, None

    def __call__(self, t, sys_, ctx, st, vnom_p, vnom_q):
        if self.done or t < self.t0:
            return
        self.done = True
        tt0 = time.perf_counter()
        lin = L.linearize(sys_, ctx)
        t_lin = time.perf_counter() - tt0
        rs = H.rows_of(sys_, ctx)
        y = sys_.dae.y
        idx = np.concatenate([rs["P"], rs["Q"], rs["Vbus"]])
        a_z, b_v, c_z = L.augmented(lin, idx)
        zdot = np.concatenate([lin["xdot"], np.zeros(20)])
        pred = np.zeros((5, len(idx)))
        cur = zdot.copy()
        for k in range(1, 5):
            pred[k] = c_z @ cur
            cur = a_z @ cur
        names = [("SG" if i < ctx["n_sg"] else "GFM") + str(bb) for i, bb in enumerate(ctx["unit_bus"])]
        pset, qset = np.asarray(st["pset"], float), np.asarray(st["qset"], float)
        p, q, vb = (np.asarray(y[rs[k]], float) for k in ("P", "Q", "Vbus"))
        t1 = time.perf_counter()
        ev = H.evaluate(lin, rs, p, q, vb, pset, qset, ctx["lim"], LAM, names, rs["bus_ids"])
        t_eval = time.perf_counter() - t1
        t2 = time.perf_counter()
        fe = T.feasibility_audit(ev, np.zeros(20), H.scale_channels(0.616, 0.0154), ev["meta"], ctx["lim"], None)
        t_audit = time.perf_counter() - t2
        a_mat = ev["A"]
        sv = np.linalg.svd(a_mat / np.linalg.norm(a_mat, axis=1, keepdims=True), compute_uv=False)
        self.rec = {"t0_actual_s": float(t), "pred": pred, "y0": np.asarray(y[idx], float).copy(), "lin": {k: lin[k] for k in ("A", "B_u", "Cy_x", "Cy_u")}, "rows": rs, "idx": idx,
                    "meta": ev["meta"], "names": names, "lim": ctx["lim"], "ev_b": ev["b"],
                    "cost_s": {"linearize": t_lin, "assemble_hocbf": t_eval, "audit_lp_qp": t_audit, "qp_slsqp": fe["qp"]["SLSQP"]["time_s"], "qp_trust_constr": fe["qp"]["trust-constr"]["time_s"]},
                    "scaling": {"row_norm_min": float(np.linalg.norm(a_mat, axis=1).min()), "row_norm_max": float(np.linalg.norm(a_mat, axis=1).max()),
                                "decoupling_matrix_singular_values_normalized_rows": sv[:6].tolist(), "decoupling_condition_number": float(sv[0] / sv[-1]), "decoupling_rank_1e-8": int((sv > 1e-8 * sv[0]).sum()),
                                "n_rows": int(a_mat.shape[0]), "lead_coefficient_min_abs": float(np.abs(a_mat[np.abs(a_mat) > 0]).min()), "lead_coefficient_max_abs": float(np.abs(a_mat).max())}}


def run_free(scenario: str, t0: float, ramp=None, probe: FreeProbe | None = None):
    def hook(system, ctx):
        HOOK(system, ctx)
        system.TDS.config.tf = t0 + 0.32
        if os.environ.get("E9C_TOL"):   # solver-tolerance experiment (DEC-046): tighter Newton tolerance of the TDS
            system.TDS.config.tol = float(os.environ["E9C_TOL"])
            system.TDS.config.max_iter = int(os.environ.get("E9C_ITERS", system.TDS.config.max_iter))

    _, data, diag = b.run("B2", scenario, probe=probe, init_hook=hook, freeze_t=t0 - HALF, ramp=ramp)
    return data, diag


def series_pqv(data):
    ids = list(data["bus_ids"])
    cols = [ids.index(bb) for bb in data["unit_bus_ids"]]
    p = np.hstack([data["sg_p_pu"], data["gfm_p_pu"]])
    q = np.hstack([data["sg_q_pu"], data["gfm_q_pu"]])
    return p, q, data["bus_voltage_pu"]


def ramp_response(rec: dict[str, Any], channel: int, rate: float, taus=(0.05, 0.1, 0.2)) -> dict[float, np.ndarray]:
    a, bu, cx, cu = (rec["lin"][k] for k in ("A", "B_u", "Cy_x", "Cy_u"))
    n = a.shape[0]
    m = np.zeros((2 * n, 2 * n)); m[:n, :n], m[:n, n:] = a, np.eye(n)
    e = T.expm(m * T.SUBSTEP)
    phi, gam = e[:n, :n], e[:n, n:]
    idx = rec["idx"]
    delta, out = np.zeros(n), {}
    steps = {int(round(tau / T.SUBSTEP)): tau for tau in taus}
    for k in range(1, max(steps) + 1):
        du = np.zeros(20); du[channel] = rate * (k - 1) * T.SUBSTEP
        delta = phi @ delta + gam @ (bu @ du)
        if k in steps:
            du_k = np.zeros(20); du_k[channel] = rate * k * T.SUBSTEP
            out[steps[k]] = cx[idx] @ delta + cu[idx] @ du_k
    return out


def analyse(scenario: str, t0: float) -> dict[str, Any]:
    pr = FreeProbe(t0)
    data, diag = run_free(scenario, t0, probe=pr)
    rec = pr.rec
    t = data["time_s"]
    p, q, vb = series_pqv(data)
    lim = rec["lim"]
    t0a = rec["t0_actual_s"]
    # truth derivatives of the outputs (for reference) and of every barrier function
    truth_out = {deg: poly_derivs(t, np.hstack([p, q, vb]), t0a, deg) for deg in (5, 6, 7)}
    meta = rec["meta"]
    nb = len(meta)
    h_series = np.stack([barrier_series(m["kind"], m.get("unit"), m.get("bus"), p, q, vb, lim) for m in meta], axis=1)
    tr = {deg: poly_derivs(t, h_series, t0a, deg) for deg in (5, 6, 7)}
    truth = tr[6]
    unc = np.maximum(np.abs(tr[5] - tr[7]), np.abs(tr[6] - tr[7]))
    # frozen predictions of the barrier derivatives (no curvature, as in E9-B1) and with curvature (Leibniz) for S
    pred = rec["pred"]
    pP, pQ, pV = pred[:, :10], pred[:, 10:20], pred[:, 20:]
    y0 = rec["y0"]
    P0, Q0, V0 = y0[:10], y0[10:20], y0[20:]
    fro = np.zeros((5, nb)); frc = np.zeros((5, nb))
    for j, m in enumerate(meta):
        kd, u, bu_ = m["kind"], m.get("unit"), m.get("bus")
        for k in range(1, 5):
            if kd in ("P+", "P-"):
                s = -1.0 if kd == "P+" else 1.0
                fro[k, j] = frc[k, j] = s * pP[k, u]
            elif kd in ("Q+", "Q-"):
                s = -1.0 if kd == "Q+" else 1.0
                fro[k, j] = frc[k, j] = s * pQ[k, u]
            elif kd in ("V+", "V-"):
                s = -1.0 if kd == "V+" else 1.0
                fro[k, j] = frc[k, j] = s * pV[k, bu_]
            else:
                fro[k, j] = -2.0 * P0[u] * pP[k, u] - 2.0 * Q0[u] * pQ[k, u]
                # Leibniz: d^k(P^2) = sum_i C(k,i) P^(i) P^(k-i); P^(0) = P0
                dP = [P0[u]] + [pP[i, u] for i in range(1, k + 1)]
                dQ = [Q0[u]] + [pQ[i, u] for i in range(1, k + 1)]
                frc[k, j] = -sum(comb(k, i) * (dP[i] * dP[k - i] + dQ[i] * dQ[k - i]) for i in range(k + 1))
    h0 = np.array([m["h0"] for m in meta])
    r = np.array([m["r"] for m in meta])

    def psi_set(d, jx):
        rj = int(r[jx])
        h = [h0[jx]] + [d[k, jx] for k in range(1, rj)]
        return [sum(comb(k, i) * LAM ** (k - i) * h[i] for i in range(k + 1)) for k in range(rj)]

    def rhs(d, jx):
        rj = int(r[jx])
        return -(sum(comb(rj, k) * LAM ** (rj - k) * ([h0[jx]] + [d[i, jx] for i in range(1, rj + 1)])[k] for k in range(rj)) + d[rj, jx])

    kinds = ("P+", "P-", "Q+", "Q-", "S", "V+", "V-")
    res: dict[str, Any] = {"scenario": scenario, "t0_s": t0a, "tds_ok": diag["tds_ok"], "per_kind": {}, "membership": {}}
    mem_diff = {"frozen": [], "frozen_curv": []}
    rhs_sign_diff = {"frozen": 0, "frozen_curv": 0}
    for kd in kinds:
        js = [j for j, m in enumerate(meta) if m["kind"] == kd]
        rec_k = {}
        for k in (1, 2, 3, 4):
            scale = np.maximum(np.abs(truth[k, js]), 1e-3 * max(1e-12, np.abs(truth[k]).max()))
            ef = np.abs(fro[k, js] - truth[k, js]) / scale
            ec = np.abs(frc[k, js] - truth[k, js]) / scale
            cons_f = np.abs(fro[k, js] - truth[k, js]) <= 3 * unc[k, js] + 1e-12
            cons_c = np.abs(frc[k, js] - truth[k, js]) <= 3 * unc[k, js] + 1e-12
            rec_k[f"order_{k}"] = {"median_rel_err_frozen": float(np.median(ef)), "max_rel_err_frozen": float(ef.max()), "median_rel_err_curv": float(np.median(ec)), "max_rel_err_curv": float(ec.max()),
                                   "consistent_within_3_unc_frozen": float(cons_f.mean()), "consistent_within_3_unc_curv": float(cons_c.mean()), "truth_fit_uncertainty_median": float(np.median(unc[k, js])),
                                   "truth_abs_median": float(np.median(np.abs(truth[k, js])))}
        res["per_kind"][kd] = rec_k
    for j, m in enumerate(meta):
        pt, pf, pc = psi_set(truth, j), psi_set(fro, j), psi_set(frc, j)
        in_t, in_f, in_c = min(pt) >= 0, min(pf) >= 0, min(pc) >= 0
        if in_t != in_f:
            mem_diff["frozen"].append(m["name"])
        if in_t != in_c:
            mem_diff["frozen_curv"].append(m["name"])
        bt, bf, bc = rhs(truth, j), rhs(fro, j), rhs(frc, j)
        rhs_sign_diff["frozen"] += int((bt > 0) != (bf > 0)); rhs_sign_diff["frozen_curv"] += int((bt > 0) != (bc > 0))
    res["membership"] = {"n_barriers": nb, "inside_CH_truth": int(sum(min(psi_set(truth, j)) >= 0 for j in range(nb))), "inside_CH_frozen": int(sum(min(psi_set(fro, j)) >= 0 for j in range(nb))),
                         "inside_CH_frozen_curv": int(sum(min(psi_set(frc, j)) >= 0 for j in range(nb))), "decisions_differing_frozen": len(mem_diff["frozen"]),
                         "decisions_differing_frozen_curv": len(mem_diff["frozen_curv"]), "examples_differing_frozen": mem_diff["frozen"][:8], "rhs_activation_sign_differences": rhs_sign_diff}
    # gate criterion for S0 (i) and (ii)
    same_pos = all((min(psi_set(truth, j)) >= 0) and (min(psi_set(fro, j)) >= 0) for j in range(nb))
    consistent = True
    for j, m in enumerate(meta):
        for k in (1, 2, 3):
            scale_m = max(abs(m["h0"]), 1e-3)
            ok = abs(fro[k, j] - truth[k, j]) <= 3 * unc[k, j] + 1e-12 or abs(fro[k, j] - truth[k, j]) <= 1e-3 * scale_m
            consistent &= bool(ok)
    res["gate_S0_criteria"] = {"psi_same_sign_and_positive_all_barriers": bool(same_pos), "h_derivatives_1_3_consistent_all_barriers": bool(consistent), "both": bool(same_pos and consistent)}
    # output-level order 1..4 errors (all 59 outputs)
    tout = truth_out[6]
    res["outputs"] = {f"order_{k}": {"median_rel_err": float(np.median(np.abs(pred[k] - tout[k]) / np.maximum(np.abs(tout[k]), 1e-3 * np.abs(tout[k]).max() + 1e-12))),
                                     "max_abs_diff": float(np.abs(pred[k] - tout[k]).max()), "truth_abs_max": float(np.abs(tout[k]).max())} for k in (1, 2, 3, 4)}
    # decoupling coefficients: ramp tests
    y_free = np.hstack(series_pqv(data))
    ramps = {}
    for nm, (ch, rate) in RAMPS.items():
        d2, g2 = run_free(scenario, t0, ramp=(t0a, ch, rate))
        y_r = np.hstack(series_pqv(d2))
        n = min(len(y_r), len(y_free))
        pr_resp = ramp_response(rec, ch, rate)
        rr = {}
        for tau, yp in pr_resp.items():
            dtr = np.array([np.interp(t0a + tau, t[:n], (y_r[:n, i] - y_free[:n, i])) for i in range(y_free.shape[1])])
            nrm = np.linalg.norm(dtr)
            rr[f"{tau}"] = {"rel_err_norm": float(np.linalg.norm(yp - dtr) / nrm) if nrm > 1e-9 else None, "response_norm": float(nrm), "max_abs_diff": float(np.abs(yp - dtr).max())}
        ramps[nm] = rr
    res["decoupling_ramp_test"] = ramps
    res["cost_s"] = rec["cost_s"]
    res["scaling"] = rec["scaling"]
    print(f"{scenario} t0={t0a:.3f}: membership truth/frozen/curv = {res['membership']['inside_CH_truth']}/{res['membership']['inside_CH_frozen']}/{res['membership']['inside_CH_frozen_curv']} "
          f"differing {res['membership']['decisions_differing_frozen']}/{res['membership']['decisions_differing_frozen_curv']}  gate={res['gate_S0_criteria']}", flush=True)
    return res


def main() -> int:
    plan = [(a.split(":")[0], float(a.split(":")[1])) for a in sys.argv[1:]] or [("S0", 30.0), ("P+", 5.5), ("P+", 7.72), ("P+", 20.0)]
    result: dict[str, Any] = {"variant": VARIANT, "git_commit": git_commit(), "andes": andes.__version__, "python": platform.python_version(), "lambda": LAM, "window_half_s": HALF, "ramps": RAMPS,
                              "method_doc": __doc__, "cases": []}
    for sc, t0 in plan:
        result["cases"].append(analyse(sc, t0))
        OUT.write_text(json.dumps(result, indent=2, default=float), encoding="utf-8")
    result["code_sha256"] = {f: sha256(Path(__file__).parent / f) for f in ("run_e9c_lie_validation.py", "e9a_linear.py", "e9a_hocbf.py", "e9b_tools.py", "run_b3_ieee39.py")}
    OUT.write_text(json.dumps(result, indent=2, default=float), encoding="utf-8")
    plots(result)
    return 0


def plots(result: dict[str, Any]) -> None:
    cases = result["cases"]
    fig, ax = plt.subplots(1, 3, figsize=(18, 5.5))
    labels = [f"{c['scenario']}\nt0={c['t0_s']:.2f}" for c in cases]
    x = np.arange(len(cases))
    for k, col in zip((1, 2, 3), ("tab:blue", "tab:orange", "tab:green")):
        ax[0].bar(x + 0.25 * (k - 2), [max(1e-6, np.median([c["per_kind"][kd][f"order_{k}"]["median_rel_err_frozen"] for kd in c["per_kind"]])) for c in cases], 0.25, label=f"order {k}", color=col)
    ax[0].set_yscale("log"); ax[0].set_title("median relative error of the frozen barrier derivatives (all kinds)"); ax[0].legend()
    ax[1].bar(x - 0.15, [c["membership"]["decisions_differing_frozen"] for c in cases], 0.3, label="frozen (gradient only)")
    ax[1].bar(x + 0.15, [c["membership"]["decisions_differing_frozen_curv"] for c in cases], 0.3, label="frozen + S curvature")
    ax[1].set_title("C_H membership decisions that differ from the nonlinear truth (of 128)"); ax[1].legend()
    for i, nm in enumerate(RAMPS):
        ax[2].bar(x + 0.25 * (i - 1), [min(100, (c["decoupling_ramp_test"][nm]["0.1"]["rel_err_norm"] or 0.0)) for c in cases], 0.25, label=nm)
    ax[2].set_title("decoupling test: relative error of the ramp response at 0.1 s"); ax[2].legend(fontsize=8)
    for a in ax:
        a.set_xticks(x); a.set_xticklabels(labels, fontsize=8); a.grid(alpha=.25)
    fig.suptitle(f"E9-C: frozen-Jacobian HOCBF derivatives versus the nonlinear DAE ({result['variant']})"); fig.tight_layout()
    fig.savefig(FIG, dpi=300, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())
