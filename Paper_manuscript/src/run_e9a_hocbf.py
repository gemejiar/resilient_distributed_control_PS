"""E9-A driver: DAE regularity, relative degrees, HOCBF constraint matrices and QP feasibility along B2 trajectories (diagnostic only).

Nominal controller: B2 (original RDC, unchanged E8 code via run_b3_ieee39.run mode "B2").  CLF off.  The QP is NOT applied to the plant: at
chosen instants the frozen-Jacobian model is built from the true ANDES state, the HOCBF/reference constraints are assembled and feasibility is
tested against the rate envelope observed in the original RDC (an assumption, not a hardware limit).  Two initial conditions are used:
  "C2t"       historical pre-event equilibrium (bus voltages up to 1.073 pu, outside the 0.95--1.05 pu band);
  "C2t_Vsafe" independent variant: the B3-A AC solution for d = 0 (all 39 bus voltages in the band) imposed through PV p0 / v0 before the power
              flow, exactly as in the B3 selection scripts; the case file and the historical runs are untouched.
"""

from __future__ import annotations

import json
import os
import platform
import sys
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
import run_b3_ieee39 as b  # noqa: E402
import run_e8_ieee39 as e8  # noqa: E402
from run_e0_ieee39 import ARTIFACTS_DIR, FIGURES_DIR, git_commit, sha256  # noqa: E402

OUT_JSON = ARTIFACTS_DIR / "IEEE39_E9A_hocbf_diagnostic.json"
FIG_RD = FIGURES_DIR / "IEEE39_E9A_relative_degree.png"
FIG_QP = FIGURES_DIR / "IEEE39_E9A_qp_feasibility.png"
FIG_FV = FIGURES_DIR / "IEEE39_E9A_frequency_voltage.png"
EVENT = e8.EVENT_TIME_S
LAM_MAIN, LAM_SENS = 2.0, (1.0, 5.0)              # s^-1, fixed a priori; the sensitivity values are reported, not used for tuning
V_REF = {"P+": (0.616, 0.0154), "Q+": (0.195, 0.0154)}   # pu/s: observed maxima of the original RDC / centered RDC (E8, B3); NOT hardware limits
PROBE_T = [4.9, 5.00005, 5.004, 5.02, 5.1, 5.15, 5.5, 6.0, 7.0, 7.72, 10.0, 20.0, 50.0, 100.0, 199.0]
V1_JSON = ARTIFACTS_DIR / "IEEE39_B3_C2t_equilibrium_selection.json"


def vsafe_hook(system, ctx):
    d = json.loads(V1_JSON.read_text(encoding="utf-8"))
    s0 = d["scenarios"]["S0"]
    p_star, v_star, unit_bus = np.array(s0["P_star"]), np.array(s0["V_star"]), d["unit_bus_order"]
    pos = {bb: i for i, bb in enumerate(unit_bus)}
    for model in ("PV", "Slack"):
        dev = getattr(system, model)
        for k, bb in enumerate(dev.bus.v):
            dev.v0.v[k] = v_star[pos[int(bb)]]
            if model == "PV":
                dev.p0.v[k] = p_star[pos[int(bb)]]


def static_report(hook) -> dict[str, Any]:
    """Regularity, relative degrees and sensitivity at the pre-event equilibrium (S0 initialization)."""
    system, ctx = e8.configure("S0", e8.TIME_STEP_S)
    if hook is not None:
        hook(system, ctx)
    system.PFlow.run()
    system.TDS.init()
    lin = L.linearize(system, ctx)
    rowset = H.rows_of(system, ctx)
    allrows = np.concatenate([rowset["P"], rowset["Q"], rowset["Vbus"]])
    rd = H.relative_degrees(lin, allrows)
    ev = np.linalg.eigvals(lin["A"])
    names = [("SG" if i < ctx["n_sg"] else "GFM") + str(bb) for i, bb in enumerate(ctx["unit_bus"])]
    y = system.dae.y
    vb = np.asarray(y[rowset["Vbus"]], float)
    out = {"dae": {"n_x": lin["n_x"], "n_y": lin["n_y"], "n_dynamic": lin["n_dynamic"], "n_quasi_algebraic": lin["n_quasi_algebraic"],
                   "n_dropped_degenerate_IEEEST_states": lin["n_dropped_IEEEST_states"], "algebraic_jacobian_gy_cond": lin["gy_only_cond"],
                   "extended_algebraic_block_cond": lin["gy_cond"], "extended_algebraic_block_min_sv": lin["gy_min_sv"],
                   "residual_inf_norm_at_operating_point": lin["g0_norm"], "max_real_eig_A": float(ev.real.max()),
                   "n_eig_re_gt_1e-6": int((ev.real > 1e-6).sum()), "regular_index_one": bool(lin["gy_min_sv"] > 1e-8)},
           "pre_event_bus_voltage": {"max_pu": float(vb.max()), "min_pu": float(vb.min()), "n_above_1p05": int((vb > 1.05).sum()), "n_below_0p95": int((vb < 0.95).sum()),
                                     "buses_above_1p05": [int(bb) for bb, v in zip(rowset["bus_ids"], vb) if v > 1.05]},
           "unit_names": names, "markov_abs_max_by_order": rd["markov_abs_max"]}
    own = {}
    rdm, lead = rd["rd"], rd["lead"]
    for i, nm in enumerate(names):
        for lab, orow, chans in (("P", i, (i, 10 + i)), ("Q", 10 + i, (i, 10 + i))):
            own[f"{lab}_{nm}"] = {"own_Pset": int(rdm[orow, i]), "own_Qset": int(rdm[orow, 10 + i]), "min_over_all_20_channels": int(rdm[orow][rdm[orow] > 0].min()),
                                  "lead_coeff_own_Pset": float(lead[orow, i]), "lead_coeff_own_Qset": float(lead[orow, 10 + i])}
    out["relative_degree_units"] = own
    out["relative_degree_buses_min_over_channels"] = {int(bb): int(rdm[20 + k][rdm[20 + k] > 0].min()) for k, bb in enumerate(rowset["bus_ids"])}
    out["relative_degree_matrix_P_Q_V"] = rdm.tolist()
    return out


class Prober:
    def __init__(self, scenario: str):
        self.scenario, self.done, self.rows = scenario, set(), []
        self.vref = H.scale_channels(*V_REF[scenario])
        self.rowset = None

    def __call__(self, t, sys_, ctx, st, vnom_p, vnom_q):
        for tp in PROBE_T:
            if tp in self.done or t < tp:
                continue
            self.done.add(tp)
            if self.rowset is None:
                self.rowset = H.rows_of(sys_, ctx)
            y = sys_.dae.y
            lin = L.linearize(sys_, ctx)
            p = np.asarray(y[self.rowset["P"]], float)
            q = np.asarray(y[self.rowset["Q"]], float)
            vb = np.asarray(y[self.rowset["Vbus"]], float)
            names = [("SG" if i < ctx["n_sg"] else "GFM") + str(bb) for i, bb in enumerate(ctx["unit_bus"])]
            vnom = np.concatenate([vnom_p, vnom_q]) if t >= EVENT else np.zeros(20)
            rec: dict[str, Any] = {"t_s": float(t), "target_t_s": tp, "max_residual": lin["g0_norm"], "gy_cond": lin["gy_only_cond"]}
            for lam in (LAM_MAIN, *LAM_SENS):
                ev = H.evaluate(lin, self.rowset, p, q, vb, np.asarray(st["pset"], float), np.asarray(st["qset"], float), ctx["lim"], lam, names, self.rowset["bus_ids"])
                fe = H.feasibility(ev, vnom, self.vref)
                key = f"lam_{lam:g}"
                rec[key] = fe
                if lam == LAM_MAIN:
                    meta = ev["meta"]
                    outside = [m["name"] for m in meta if m["psi_outside"]]
                    outside_ref = [m["name"] for m in ev["meta_ref"] if m["psi_outside"]]
                    rec["barriers_outside_CH"] = outside
                    rec["reference_barriers_outside"] = outside_ref
                    rec["n_barriers"] = len(meta)
                    rec["no_authority_barriers"] = [m["name"] for m in ev["no_authority"]]
                    rec["relative_degree_by_kind"] = {k: sorted({m["r"] for m in meta if m["kind"] == k}) for k in ("P+", "P-", "Q+", "Q-", "S", "V+", "V-")}
                    rec["min_h0_by_kind"] = {k: float(min(m["h0"] for m in meta if m["kind"] == k)) for k in ("P+", "P-", "Q+", "Q-", "S", "V+", "V-")}
                    i31 = names.index("SG31")
                    rec["SG31_P+"] = next(({"r": m["r"], "h0": m["h0"], "psi_min": m["psi_min"]} for m in meta if m["name"] == f"P{i31}+"), None)
            self.rows.append(rec)
            print(f"  probe {self.scenario} t={t:.4f}: outside C_H={len(rec['barriers_outside_CH'])} s*={rec['lam_2']['authority_scale_min']} "
                  f"qp_ok={rec['lam_2']['qp_converged']}", flush=True)


def replay(scenario: str, hook) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    pr = Prober(scenario)
    _, data, diag = b.run("B2", scenario, probe=pr, init_hook=hook)
    return {"diag": diag, "probes": pr.rows}, data


def main() -> int:
    result: dict[str, Any] = {"git_commit": git_commit(), "andes": andes.__version__, "python": platform.python_version(),
                              "lambda_main": LAM_MAIN, "lambda_sensitivity": list(LAM_SENS), "observed_rate_envelope_pu_per_s": V_REF,
                              "probe_targets_s": PROBE_T, "model_note": "frozen-Jacobian local-linear HOCBF diagnostic; higher-order Lie derivatives neglect curvature",
                              "runner_sha256": {"e9a_linear": sha256(Path(L.__file__)), "e9a_hocbf": sha256(Path(H.__file__)), "run_e9a_hocbf": sha256(Path(__file__))},
                              "static": {}, "dynamic": {}}
    for variant, hook in (("C2t", None), ("C2t_Vsafe", vsafe_hook)):
        result["static"][variant] = static_report(hook)
        print("static", variant, result["static"][variant]["dae"], result["static"][variant]["pre_event_bus_voltage"], flush=True)
    series = {}
    only = sys.argv[1:] or ["C2t:P+", "C2t:Q+", "C2t_Vsafe:P+", "C2t_Vsafe:Q+"]
    for key in only:
        variant, sc = key.split(":")
        hook = vsafe_hook if variant == "C2t_Vsafe" else None
        res, data = replay(sc, hook)
        result["dynamic"][key] = res
        series[key] = {"t": data["time_s"], "f": data["bus_frequency_hz"].mean(axis=1), "vbus": data["bus_voltage_pu"]}
        OUT_JSON.write_text(json.dumps(result, indent=2, default=float), encoding="utf-8")
        np.savez_compressed(ARTIFACTS_DIR / "IEEE39_E9A_replay_series.npz", **{f"{k}__{kk}": vv for k, v in series.items() for kk, vv in v.items()})
    plots(result, series)
    return 0


def plots(result: dict[str, Any], series: dict[str, dict[str, np.ndarray]]) -> None:
    st = result["static"]["C2t"]
    rdm = np.array(st["relative_degree_matrix_P_Q_V"])
    names = st["unit_names"]
    fig, ax = plt.subplots(1, 2, figsize=(15, 7))
    sub = rdm[:20].astype(float)
    sub[sub == 0] = np.nan
    im = ax[0].imshow(sub, aspect="auto", cmap="viridis_r", vmin=2, vmax=8)
    ax[0].set_xticks(range(20)); ax[0].set_xticklabels([f"Pset {n}" for n in names] + [f"Qset {n}" for n in names], rotation=70, fontsize=7)
    ax[0].set_yticks(range(20)); ax[0].set_yticklabels([f"P {n}" for n in names] + [f"Q {n}" for n in names], fontsize=7)
    for r in range(20):
        for c in range(20):
            ax[0].text(c, r, "-" if np.isnan(sub[r, c]) else f"{int(sub[r, c])}", ha="center", va="center", fontsize=6, color="w")
    ax[0].set_title("Relative degree of P_i, Q_i with respect to each reference rate (structural, C2t)")
    vb_min = np.array([min(r for r in rdm[20 + k] if r > 0) for k in range(rdm.shape[0] - 20)])
    ax[1].bar(range(len(vb_min)), vb_min); ax[1].set_title("Relative degree of the 39 bus voltages (min over the 20 channels)"); ax[1].set_xlabel("bus index (order of Bus.idx)")
    fig.colorbar(im, ax=ax[0], shrink=.7); fig.tight_layout(); fig.savefig(FIG_RD, dpi=300, bbox_inches="tight"); plt.close(fig)
    fig, ax = plt.subplots(2, 2, figsize=(14, 8))
    for k, (key, res) in enumerate(result["dynamic"].items()):
        t = [r["t_s"] - EVENT for r in res["probes"]]
        s = [np.nan if r["lam_2"]["authority_scale_min"] is None else r["lam_2"]["authority_scale_min"] for r in res["probes"]]
        out = [len(r["barriers_outside_CH"]) + len(r["reference_barriers_outside"]) for r in res["probes"]]
        ax[0, 0].semilogy(t, np.where(np.isnan(s), 1e6, s), "o-", label=key)
        ax[0, 1].plot(t, out, "o-", label=key)
        ax[1, 0].plot(t, [r["lam_2"]["elastic_violation_at_s1"] if r["lam_2"]["elastic_violation_at_s1"] is not None else np.nan for r in res["probes"]], "o-", label=key)
        ax[1, 1].plot(t, [int(r["lam_2"]["qp_converged"]) for r in res["probes"]], "s-", label=key)
    ax[0, 0].axhline(1.0, color="k", ls="--", lw=.8); ax[0, 0].set_title("minimum rate-authority scale s* (1 = observed RDC envelope; 1e6 = infeasible)")
    ax[0, 1].set_title("barriers outside the strengthened set C_H (physical + reference)"); ax[1, 0].set_title("elastic violation at s = 1 (normalised)")
    ax[1, 1].set_title("QP feasible at s = 1 (1 = yes)")
    for a in ax.ravel():
        a.set_xscale("symlog", linthresh=0.01); a.grid(alpha=.25); a.set_xlabel("Time since event [s]"); a.legend(fontsize=7)
    fig.suptitle("E9-A: HOCBF-QP feasibility diagnostic along the B2 trajectories (frozen-Jacobian; QP not applied to the plant)"); fig.tight_layout()
    fig.savefig(FIG_QP, dpi=300, bbox_inches="tight"); plt.close(fig)
    fig, ax = plt.subplots(2, 2, figsize=(14, 8))
    for col, sc in enumerate(("P+", "Q+")):
        for key, ls in ((f"C2t:{sc}", "-"), (f"C2t_Vsafe:{sc}", "--")):
            if key not in series:
                continue
            s_ = series[key]
            ax[0, col].plot(s_["t"], s_["f"] - 60.0, ls=ls, label=key)
            ax[1, col].plot(s_["t"], s_["vbus"].max(axis=1), ls=ls, label=key + " max bus V")
            ax[1, col].plot(s_["t"], s_["vbus"].min(axis=1), ls=ls, lw=.8, label=key + " min bus V")
        ax[0, col].set_title(f"{sc}: mean bus frequency - 60 Hz (B2)"); ax[0, col].set_xlim(0, 60); ax[0, col].set_ylabel("Hz")
        ax[1, col].axhline(1.05, color="k", ls=":", lw=.8); ax[1, col].axhline(0.95, color="k", ls=":", lw=.8); ax[1, col].set_title(f"{sc}: 39-bus voltage extremes (dotted: 0.95/1.05)")
        for r in range(2):
            ax[r, col].axvline(EVENT, color="tab:red", ls=":", lw=.8); ax[r, col].grid(alpha=.25); ax[r, col].set_xlabel("Time [s]"); ax[r, col].legend(fontsize=6)
    fig.suptitle("E9-A: original C2t equilibrium versus independent safe-voltage initial condition (B2 nominal controller)"); fig.tight_layout()
    fig.savefig(FIG_FV, dpi=300, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())
