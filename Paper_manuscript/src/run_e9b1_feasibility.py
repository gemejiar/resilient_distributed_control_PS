"""E9-B1: feasibility of the HOCBF filter on the frozen C2t_Vsafe variant, outside the loop (no QP is applied to the plant).

Replays B2 (original RDC, unchanged E8 code, no QP) from C2t_Vsafe in S0, P+ and Q+ and, at chosen instants before and after the load step, builds the frozen-Jacobian
model from the true ANDES state, evaluates the physical barriers h and the auxiliary conditions psi of the strengthened set C_H (physical and reference barriers), audits
the QP (two LP algorithms, two QP solvers, raw-constraint residuals, conflicting rows from the elastic-LP duals), and measures what the frozen model cannot predict:
the trajectory error against the stored nonlinear series (pass 1 of E9-B0) and the error of the output derivatives of order 1-3.  The rate envelope is the observed maximum of the
original RDC in E8 and is an experimental candidate bound, not a hardware limit.  lambda = 2 s^-1 is the a-priori class-K gain; lambda = 1 and 5 are reported for sensitivity only.
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
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import e9a_hocbf as H  # noqa: E402
import e9a_linear as L  # noqa: E402
import e9b_tools as T  # noqa: E402
import run_b3_ieee39 as b  # noqa: E402
import run_e8_ieee39 as e8  # noqa: E402
import select_equilibrium_b3 as b3  # noqa: E402
from run_e0_ieee39 import ARTIFACTS_DIR, FIGURES_DIR, git_commit, sha256  # noqa: E402
from e9b_variant import DELTA, HOOK, TAG, VARIANT  # noqa: E402
from run_e9b0_variant import continuity  # noqa: E402

OUT_JSON = ARTIFACTS_DIR / f"IEEE39_E9B1_feasibility{TAG}.json"
B0_SERIES = ARTIFACTS_DIR / f"IEEE39_E9B0_Vsafe{TAG}_series.npz"
FIGS = {k: FIGURES_DIR / f"IEEE39_E9B1_{k}{TAG}.png" for k in ("CH_membership", "qp_feasibility", "model_error")}
EVENT = e8.EVENT_TIME_S
LAM_MAIN, LAM_SENS = 2.0, (1.0, 5.0)
V_REF = {"S0": (0.616, 0.0154), "P+": (0.616, 0.0154), "Q+": (0.195, 0.0154)}     # pu/s, observed in E8/B3: experimental candidate bound, not hardware
PROBE_T = [4.9, 4.99, 5.00005, 5.004, 5.008, 5.02, 5.05, 5.1, 5.15, 5.25, 5.5, 6.0, 7.0, 7.72, 10.0, 20.0, 50.0, 100.0, 199.0]
if os.environ.get("E9B1_PROBES"):   # smoke tests only
    PROBE_T = [float(x) for x in os.environ["E9B1_PROBES"].split(",")]


class Prober:
    def __init__(self, scenario: str, series: dict[str, np.ndarray]):
        self.sc, self.series, self.done, self.rows = scenario, series, set(), []
        self.vref = H.scale_channels(*V_REF[scenario])
        self.rowset = None
        self.base_rd = None

    def __call__(self, t, sys_, ctx, st, vnom_p, vnom_q):
        for tp in PROBE_T:
            if tp in self.done or t < tp:
                continue
            self.done.add(tp)
            t0c = time.perf_counter()
            if self.rowset is None:
                self.rowset = H.rows_of(sys_, ctx)
            y = sys_.dae.y
            lin = L.linearize(sys_, ctx)
            rs = self.rowset
            p, q, vb = (np.asarray(y[rs[k]], float) for k in ("P", "Q", "Vbus"))
            names = [("SG" if i < ctx["n_sg"] else "GFM") + str(bb) for i, bb in enumerate(ctx["unit_bus"])]
            vnom = np.concatenate([vnom_p, vnom_q]) if t >= EVENT else np.zeros(20)
            rec: dict[str, Any] = {"t_s": float(t), "target_s": tp, "residual_g": lin["g0_norm"], "gy_cond": lin["gy_only_cond"]}
            # structural relative degree and leading coefficients at this state
            allrows = np.concatenate([rs["P"], rs["Q"], rs["Vbus"]])
            rd = H.relative_degrees(lin, allrows)
            if self.base_rd is None:
                self.base_rd = rd
            rec["relative_degree_same_as_first_probe"] = bool(np.array_equal(rd["rd"], self.base_rd["rd"]))
            nz = self.base_rd["lead"] != 0
            rec["leading_coeff_ratio_vs_first_probe"] = {"min": float(np.min(np.abs(rd["lead"][nz] / self.base_rd["lead"][nz]))), "max": float(np.max(np.abs(rd["lead"][nz] / self.base_rd["lead"][nz])))}
            # nodal balance with independent loss
            yb, _, _, _ = b3.network(sys_)
            vc = np.asarray(y[np.asarray(sys_.Bus.v.a)], float) * np.exp(1j * np.asarray(y[np.asarray(sys_.Bus.a.a)], float))
            loss = float((vc * np.conj(yb @ vc)).real.sum())
            pgen = float(np.asarray(y[np.concatenate([np.asarray(sys_.GENROU.Pe.a), np.asarray(sys_.REGF1.Pe.a)])], float).sum())
            rec["power_balance_residual_pu"] = abs(pgen - float(np.sum(sys_.PQ.Ppf.v)) - loss)
            # model error against the stored nonlinear series
            errs = T.predict_outputs(lin, rs, y, t, self.series)
            rec["prediction_error"] = {tau: {**{k: v for k, v in e.items() if k.startswith("max_abs")}, "window_crosses_load_step": bool(t < EVENT <= t + float(tau))} for tau, e in errs.items()}
            if t >= EVENT + 0.4 or t <= EVENT - 0.05:
                ud = (T._interp_u(self.series["cmd_t"], self.series["cmd_pset"], self.series["cmd_qset"], t + 0.004) - T._interp_u(self.series["cmd_t"], self.series["cmd_pset"], self.series["cmd_qset"], t - 0.004)) / 0.008
                rec["derivative_check"] = T.derivative_check(lin, rs, t, self.series, ud)
                rec["derivative_check_wide_window"] = T.derivative_check(lin, rs, t, self.series, ud, half=20, deg=6)
            # strengthened set and QP (lambda main with full audit; sensitivities: authority scale only)
            for lam in (LAM_MAIN, *LAM_SENS):
                ev = H.evaluate(lin, rs, p, q, vb, np.asarray(st["pset"], float), np.asarray(st["qset"], float), ctx["lim"], lam, names, rs["bus_ids"])
                if lam == LAM_MAIN:
                    meta = ev["meta"]
                    outside = [m for m in meta if m["psi_outside"]]
                    kinds = ("P+", "P-", "Q+", "Q-", "S", "V+", "V-")
                    rec["C_H"] = {"n_barriers": len(meta), "n_outside": len(outside), "outside_by_kind": {k: sum(1 for m in outside if m["kind"] == k) for k in kinds},
                                  "h_negative": [m["name"] for m in meta if m["h0"] < 0], "outside_psi0_negative": [m["name"] for m in outside if m["psi"][0] < 0],
                                  "worst_psi_min": sorted([(m["name"], m["psi_min"]) for m in meta], key=lambda x: x[1])[:6], "reference_barriers_outside": [m["name"] for m in ev["meta_ref"] if m["psi_outside"]],
                                  "min_h_by_kind": {k: float(min(m["h0"] for m in meta if m["kind"] == k)) for k in kinds}, "relative_degree_by_kind": {k: sorted({m["r"] for m in meta if m["kind"] == k}) for k in kinds}}
                    rec["audit"] = T.feasibility_audit(ev, vnom, self.vref, meta, ctx["lim"], errs)
                    i31, i35 = names.index("SG31"), names.index("SG35")
                    rec["SG31_P+"] = next(({"r": m["r"], "h0": m["h0"], "psi": m["psi"]} for m in meta if m["name"] == f"P{i31}+"), None)
                    rec["SG35_P+"] = next(({"r": m["r"], "h0": m["h0"], "psi": m["psi"]} for m in meta if m["name"] == f"P{i35}+"), None)
                else:
                    rec[f"lam_{lam:g}_authority_scale"] = H.feasibility(ev, vnom, self.vref)["authority_scale_min"]
            rec["probe_time_s"] = time.perf_counter() - t0c
            self.rows.append(rec)
            print(f"  [{self.sc}] t={t:.4f} outside_CH={rec['C_H']['n_outside']} s*={rec['audit']['authority_scale_min']} qp={rec['audit']['qp']['SLSQP']['converged']} "
                  f"elastic={rec['audit']['elastic_violation_at_s1']} ({rec['probe_time_s']:.1f}s)", flush=True)


def main() -> int:
    z = np.load(B0_SERIES)
    result: dict[str, Any] = {"variant": VARIANT, "incremental_redispatch_delta_pu": DELTA, "git_commit": git_commit(), "andes": andes.__version__, "python": platform.python_version(), "lambda_main": LAM_MAIN,
                              "lambda_sensitivity": list(LAM_SENS), "rate_envelope_pu_per_s": V_REF, "rate_envelope_status": "experimental candidate bound (observed in E8/B3), not a hardware limit",
                              "probe_targets_s": PROBE_T, "B0_series_sha256": sha256(B0_SERIES), "scenarios": {},
                              "code_sha256": {f: sha256(Path(__file__).parent / f) for f in ("e9a_linear.py", "e9a_hocbf.py", "e9b_tools.py", "e9b_variant.py", "run_e9b1_feasibility.py")}}
    scen = sys.argv[1:] or ["S0", "P+", "Q+"]
    for sc in scen:
        series = {k.split("__", 1)[1]: z[k] for k in z.files if k.startswith(sc + "__")}
        pr = Prober(sc, series)
        system, data, diag = b.run("B2", sc, probe=pr, init_hook=HOOK)
        f_new, f_old = data["bus_frequency_hz"].mean(axis=1), series["bus_frequency_hz"].mean(axis=1)
        n = min(len(f_new), len(f_old))
        result["scenarios"][sc] = {"diag": diag, "continuity": continuity(system), "probes": pr.rows, "replay_vs_B0_max_abs_freq_diff_hz": float(np.abs(f_new[:n] - f_old[:n]).max()),
                                   "replay_vs_B0_max_abs_voltage_diff_pu": float(np.abs(data["bus_voltage_pu"][:n] - series["bus_voltage_pu"][:n]).max())}
        OUT_JSON.write_text(json.dumps(result, indent=2, default=float), encoding="utf-8")
    verdicts(result)
    OUT_JSON.write_text(json.dumps(result, indent=2, default=float), encoding="utf-8")
    plots(result)
    return 0


def verdicts(result: dict[str, Any]) -> None:
    """Item 9 of the authorization: stop closed-loop protection for a scenario whose post-event state is outside C_H or whose QP is infeasible."""
    for sc, res in result["scenarios"].items():
        rows = res["probes"]
        pre = [r for r in rows if r["t_s"] < EVENT + 0.00005][-1]
        post = [r for r in rows if r["t_s"] > EVENT + 0.002]
        first_post = post[0] if post else None
        v: dict[str, Any] = {"pre_event_in_CH": bool(pre["C_H"]["n_outside"] == 0 and not pre["C_H"]["h_negative"]), "pre_event_qp_feasible": bool(pre["audit"]["qp"]["SLSQP"]["converged"]),
                             "first_post_jump_probe_t_s": first_post["t_s"] - EVENT if first_post else None,
                             "first_post_jump_barriers_outside_CH": first_post["C_H"]["n_outside"] if first_post else None,
                             "first_post_jump_qp_feasible": bool(first_post["audit"]["qp"]["SLSQP"]["converged"]) if first_post else None}
        feas_after = next((r["t_s"] - EVENT for r in post if r["audit"]["qp"]["SLSQP"]["converged"] and all(rr["audit"]["qp"]["SLSQP"]["converged"] for rr in post if rr["t_s"] >= r["t_s"])), None)
        inch_after = next((r["t_s"] - EVENT for r in post if r["C_H"]["n_outside"] == 0 and all(rr["C_H"]["n_outside"] == 0 for rr in post if rr["t_s"] >= r["t_s"])), None)
        v["QP_feasible_from_s_after_event_on"] = feas_after
        v["state_in_CH_from_s_after_event_on"] = inch_after
        v["solver_agreement_all_probes"] = bool(all(r["audit"]["qp_solvers_agree"] and r["audit"]["independent_check"]["agree"] for r in rows))
        v["closed_loop_protection_authorized_for_scenario"] = bool(v["pre_event_in_CH"] and first_post is not None and first_post["C_H"]["n_outside"] == 0 and v["first_post_jump_qp_feasible"])
        v["reason"] = ("post-event state is outside C_H and/or the QP is infeasible right after the load step; closed-loop protection is NOT authorized for this scenario"
                       if not v["closed_loop_protection_authorized_for_scenario"] else "pre- and post-event states belong to C_H and the QP is feasible")
        res["verdict"] = v


def plots(result: dict[str, Any]) -> None:
    fig, ax = plt.subplots(1, 3, figsize=(18, 5.5))
    for c, (sc, res) in enumerate(result["scenarios"].items()):
        t = [r["t_s"] - EVENT for r in res["probes"]]
        for k in ("P+", "P-", "Q+", "Q-", "S", "V+", "V-"):
            ax[c].plot(t, [r["C_H"]["outside_by_kind"][k] for r in res["probes"]], "o-", ms=3, label=k)
        ax[c].set_xscale("symlog", linthresh=0.01); ax[c].set_title(f"{sc}: barriers outside C_H (lambda = 2)"); ax[c].grid(alpha=.25); ax[c].set_xlabel("Time since event [s]")
        ax[c].axvline(0, color="r", ls=":", lw=.8)
    ax[0].legend(fontsize=7); fig.suptitle(f"E9-B1: strengthened-set membership of {VARIANT} under B2 (frozen-Jacobian psi conditions)"); fig.tight_layout()
    fig.savefig(FIGS["CH_membership"], dpi=300, bbox_inches="tight"); plt.close(fig)
    fig, ax = plt.subplots(2, 2, figsize=(14, 8))
    for sc, res in result["scenarios"].items():
        t = [r["t_s"] - EVENT for r in res["probes"]]
        s = [np.nan if r["audit"]["authority_scale_min"] is None else r["audit"]["authority_scale_min"] for r in res["probes"]]
        ax[0, 0].semilogy(t, np.where(np.isnan(s), 1e6, np.maximum(s, 1e-6)), "o-", ms=3, label=sc)
        ax[0, 1].plot(t, [r["audit"]["n_conflict_rows"] for r in res["probes"]], "o-", ms=3, label=sc)
        ax[1, 0].plot(t, [int(r["audit"]["qp"]["SLSQP"]["converged"]) for r in res["probes"]], "s-", ms=3, label=sc)
        ax[1, 1].semilogy(t, [max(r["audit"]["qp"]["SLSQP"]["time_s"], 1e-4) for r in res["probes"]], "o-", ms=3, label=sc)
    ax[0, 0].axhline(1, color="k", ls="--", lw=.8); ax[0, 0].set_title("minimum authority scale s* (1e6 = infeasible)"); ax[0, 1].set_title("conflicting rows at s = 1 (elastic-LP duals)")
    ax[1, 0].set_title("QP feasible at s = 1"); ax[1, 1].set_title("QP solve time [s] (SLSQP)")
    for a in ax.ravel():
        a.set_xscale("symlog", linthresh=0.01); a.grid(alpha=.25); a.legend(fontsize=7); a.set_xlabel("Time since event [s]")
    fig.suptitle(f"E9-B1: QP audit outside the loop on {VARIANT}"); fig.tight_layout(); fig.savefig(FIGS["qp_feasibility"], dpi=300, bbox_inches="tight"); plt.close(fig)
    fig, ax = plt.subplots(2, 3, figsize=(18, 8))
    for c, (sc, res) in enumerate(result["scenarios"].items()):
        t = [r["t_s"] - EVENT for r in res["probes"]]
        for tau in ("0.05", "0.25", "1.0"):
            ax[0, c].semilogy(t, [max(r["prediction_error"][tau]["max_abs_err_P"], 1e-9) for r in res["probes"] if tau in r["prediction_error"]], "o-", ms=3, label=f"P, tau={tau}")
        ax[0, c].set_title(f"{sc}: frozen-model prediction error of P [pu] vs probe time"); ax[0, c].legend(fontsize=7)
        pts = [(r["t_s"] - EVENT, r["derivative_check"]) for r in res["probes"] if "derivative_check" in r]
        for k in (1, 2, 3):
            ax[1, c].semilogy([x[0] for x in pts], [max(x[1][f"order_{k}"]["median_rel_err"], 1e-9) for x in pts], "o-", ms=3, label=f"order {k} median rel. err")
        ax[1, c].set_title(f"{sc}: derivative check (frozen vs nonlinear)"); ax[1, c].legend(fontsize=7)
        for r in range(2):
            ax[r, c].set_xscale("symlog", linthresh=0.01); ax[r, c].grid(alpha=.25); ax[r, c].set_xlabel("Time since event [s]")
    fig.suptitle(f"E9-B1 ({VARIANT}): what the frozen model cannot predict"); fig.tight_layout(); fig.savefig(FIGS["model_error"], dpi=300, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())
