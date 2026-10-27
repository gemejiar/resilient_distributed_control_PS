"""E13 (Option B): local stability of the linearization - modal analysis and Lyapunov equation.  NO regional certificate is attempted or claimed.

Linear models built at the ANDES state of a B2 replay (frozen Jacobians, algebraics and quasi-algebraic states eliminated, degenerate IEEEST states excluded as in E9):
  plant   A_plant (196 dynamic states) with the references frozen;
  loop    M (216 states: dynamic states + 20 references) of plant + original RDC (the RDC law linearised by finite differences).
Operating points (declared): the pre-event equilibrium of C2t (historical dispatch) and of C2t_Vsafe_R35_040 (t = 4.9 s) and the quasi-steady post-event states of B2 on C2t_Vsafe_R35_040 for P+
and Q+ at t = 199 s.  For every model: eigenvalues, number of unstable / marginal modes (marginal: |Re| <= 1e-6, expected: the rotor-angle shift), least-damped oscillatory modes, slowest modes
and their time constants (cross-checked with the E10 frequency time constants), and the solution P of the Lyapunov equation A_s^T P + P A_s = -I on the stable invariant subspace (real Schur
ordering).  V = x_s^T P x_s decreases along the LINEARISED stable dynamics with rate >= 1 / lambda_max(P).  This is local exponential stability of the linearisation on the stable subspace, not
a statement about the nonlinear DAE, the saturations, the QP or any region.
"""

from __future__ import annotations

import json
import os
from typing import Any

os.environ["C2_VARIANT"] = "C2t"

import matplotlib
import numpy as np
import scipy.linalg as sl

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import e9h_predictor as PR  # noqa: E402
import run_b3_ieee39 as b  # noqa: E402
import run_e8_ieee39 as e8  # noqa: E402
from e9b_variant import HOOK, VARIANT  # noqa: E402
from run_e0_ieee39 import ARTIFACTS_DIR as A, FIGURES_DIR, git_commit  # noqa: E402

MARG = 1e-6


def modal(mat: np.ndarray) -> dict[str, Any]:
    ev = np.linalg.eigvals(mat)
    re, im = ev.real, ev.imag
    n_unst = int((re > MARG).sum())
    n_marg = int((np.abs(re) <= MARG).sum())
    stab = ev[re < -MARG]
    osc = stab[np.abs(stab.imag) > 1e-9]
    zeta = -osc.real / np.abs(osc)
    order = np.argsort(zeta)
    least = [{"re": float(osc[i].real), "im": float(osc[i].imag), "freq_hz": float(abs(osc[i].imag) / (2 * np.pi)), "zeta": float(zeta[i])} for i in order[:10]]
    slow = stab[np.argsort(-stab.real)]
    slowest = [{"re": float(s.real), "im": float(s.imag), "tau_s": float(-1.0 / s.real)} for s in slow[:10]]
    # Lyapunov on the stable invariant subspace
    T, Z, sdim = sl.schur(mat, output="real", sort=lambda x, y: x < -MARG)
    As = T[:sdim, :sdim]
    P = sl.solve_continuous_lyapunov(As.T, -np.eye(sdim))
    wP = np.linalg.eigvalsh(0.5 * (P + P.T))
    res = As.T @ P + P @ As + np.eye(sdim)
    return {"n_states": int(len(ev)), "n_unstable_Re_gt_1e-6": n_unst, "n_marginal": n_marg, "spectral_abscissa_stable_part": float(stab.real.max()), "max_real_part_all": float(re.max()),
            "min_zeta_oscillatory": float(zeta.min()) if len(zeta) else None, "least_damped": least, "slowest_modes": slowest,
            "lyapunov": {"stable_subspace_dim": int(sdim), "lambda_min_P": float(wP.min()), "lambda_max_P": float(wP.max()), "positive_definite": bool(wP.min() > 0), "residual_inf_norm": float(np.abs(res).max()),
                         "V_decay_rate_lower_bound_per_s": float(1.0 / wP.max()), "cond_P": float(wP.max() / wP.min()) if wP.min() > 0 else None}, "eigenvalues_sample": [[float(x.real), float(x.imag)] for x in ev[np.argsort(-ev.real)][:40]]}


class StateProbe:
    def __init__(self, t_probe: float):
        self.t, self.done, self.out = t_probe, False, None
        self.pred = PR.LinearPredictor(None)

    def __call__(self, t, sys_, ctx, st, vp, vq):
        if self.done or t < self.t:
            return
        self.done = True
        self.pred.ctx, self.pred.lim = ctx, ctx["lim"]
        p = self.pred.build(sys_, st, vp, vq, float(t), refresh_params=True)
        self.out = {"t_s": float(t), "M": p["M"], "A_plant": p["A_plant"]}


def analyse(label: str, scenario: str, t_probe: float, horizon: float, hook) -> dict[str, Any]:
    pr = StateProbe(t_probe)

    def h(system, ctx):
        if hook is not None:
            hook(system, ctx)
        system.TDS.config.tf = horizon

    b.run("B2", scenario, probe=pr, init_hook=h)
    o = pr.out
    res = {"label": label, "scenario": scenario, "t_probe_s": o["t_s"], "plant_frozen_references": modal(o["A_plant"]), "closed_loop_with_RDC": modal(o["M"])}
    c = res["closed_loop_with_RDC"]
    print(f"{label}: plant unstable={res['plant_frozen_references']['n_unstable_Re_gt_1e-6']} marginal={res['plant_frozen_references']['n_marginal']} zeta_min={res['plant_frozen_references']['min_zeta_oscillatory']:.3f} | "
          f"loop unstable={c['n_unstable_Re_gt_1e-6']} marginal={c['n_marginal']} slowest tau={c['slowest_modes'][0]['tau_s']:.1f}s P>0={c['lyapunov']['positive_definite']} resid={c['lyapunov']['residual_inf_norm']:.1e}", flush=True)
    return res


def main() -> int:
    out: dict[str, Any] = {"stage": "E13", "git_commit": git_commit(), "variant": VARIANT, "doc": __doc__, "points": {}}
    out["points"]["C2t historical S0 equilibrium (t=4.9 s)"] = analyse("C2t historical S0", "S0", 4.9, 6.0, None)
    out["points"]["C2t_Vsafe_R35_040 S0 equilibrium (t=4.9 s)"] = analyse("R35_040 S0", "S0", 4.9, 6.0, HOOK)
    out["points"]["R35_040 post-event P+ (t=199 s)"] = analyse("R35_040 P+ t=199", "P+", 199.0, 200.0, HOOK)
    out["points"]["R35_040 post-event Q+ (t=199 s)"] = analyse("R35_040 Q+ t=199", "Q+", 199.0, 200.0, HOOK)
    e10 = json.loads((A / "IEEE39_E10_summary.json").read_text(encoding="utf-8"))["runs"]
    out["cross_check_with_E10"] = {k: {"frequency_tau_s_from_series": e10[k]["frequency_tau_s"]} for k in e10 if k.startswith("R35_040")}
    (A / "IEEE39_E13_stability.json").write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
    fig, ax = plt.subplots(1, 3, figsize=(18, 5.5))
    for (name, r), col in zip(out["points"].items(), ("tab:gray", "tab:blue", "tab:orange", "tab:green")):
        ev = np.array(r["closed_loop_with_RDC"]["eigenvalues_sample"])
        ax[0].scatter(ev[:, 0], ev[:, 1], s=10, color=col, label=name)
        sl_ = r["closed_loop_with_RDC"]["slowest_modes"]
        ax[1].plot(range(1, len(sl_) + 1), [s["tau_s"] for s in sl_], "o-", color=col, label=name)
        lz = r["closed_loop_with_RDC"]["least_damped"]
        ax[2].plot(range(1, len(lz) + 1), [z["zeta"] for z in lz], "o-", color=col, label=name)
    ax[0].set_xscale("symlog", linthresh=1e-2); ax[0].set_title("eigenvalues of plant + RDC (40 rightmost)"); ax[0].set_xlabel("Re"); ax[0].set_ylabel("Im")
    ax[1].set_yscale("log"); ax[1].set_title("slowest stable modes: time constant [s]"); ax[2].set_title("least-damped oscillatory modes: damping ratio")
    for a in ax:
        a.grid(alpha=.25); a.legend(fontsize=6)
    fig.suptitle("E13: local modal analysis of the linearisation (Lyapunov equation on the stable subspace; no regional claim)"); fig.tight_layout()
    fig.savefig(FIGURES_DIR / "IEEE39_E13_stability.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
