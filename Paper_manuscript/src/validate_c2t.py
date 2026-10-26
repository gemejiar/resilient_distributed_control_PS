"""Base validation of the retuned plant C2t (REGF1 KPv x1.5) against the frozen C2.

Checks (constant-power loads, as in the E3--E7 runners): identical PFlow solution,
flat TDS without drift, eigenvalues of the physical subspace, the least-damped
oscillatory modes at the case setpoints, and the stability scan when all static
generator voltage setpoints move toward 1.0 pu (the E7 target, DEC-026).
"""

from __future__ import annotations

import json

import andes
import numpy as np

from run_e0_ieee39 import ARTIFACTS_DIR, PROJECT_ROOT, sha256

CASES = {"C2": "ieee39_C2_6SG_4GFM.xlsx", "C2t": "ieee39_C2t_6SG_4GFM_KPv1p5.xlsx"}
OUT = ARTIFACTS_DIR / "IEEE39_C2t_base_validation.json"
ALPHAS = (0.0, 0.25, 0.5, 0.75, 1.0)


def load(name: str, alpha: float = 0.0) -> andes.System:
    s = andes.load(str(PROJECT_ROOT / "Paper_manuscript" / "cases" / CASES[name]), setup=False,
                   default_config=True, no_output=True)
    s.PQ.config.p2p, s.PQ.config.p2i, s.PQ.config.p2z = 1.0, 0.0, 0.0
    s.PQ.config.q2q, s.PQ.config.q2i, s.PQ.config.q2z = 1.0, 0.0, 0.0
    s.setup()
    for model in ("PV", "Slack"):
        d = getattr(s, model)
        d.v0.v[:] = d.v0.v + alpha * (1.0 - d.v0.v)
    return s


def modes(s: andes.System) -> dict[str, object]:
    s.EIG.run()
    mu = np.asarray(s.EIG.mu)
    # IEEEST degenerate states appear as +1 real modes (DEC-013); exclude them.
    degenerate = (np.abs(mu.imag) < 1e-9) & (np.abs(mu.real - 1.0) < 1e-2)
    phys = mu[~degenerate]
    osc = [m for m in phys if 1.0 < m.imag < 100.0]  # electromechanical and converter-loop band
    least = min(osc, key=lambda m: -m.real / abs(m))
    return {"physical_max_real": float(phys.real.max()), "excluded_degenerate_count": int(degenerate.sum()),
            "unstable_physical_modes": [f"{m.real:.3f}{m.imag:+.3f}j" for m in phys if m.real > 1e-6],
            "least_damped_oscillatory": {"real": float(least.real), "imag": float(least.imag),
                                         "zeta": float(-least.real / abs(least))}}


def main() -> int:
    result: dict[str, object] = {"case_sha256": {k: sha256(PROJECT_ROOT / "Paper_manuscript" / "cases" / v) for k, v in CASES.items()}}
    pflow = {}
    for name in CASES:
        s = load(name)
        ok = bool(s.PFlow.run())
        pflow[name] = {"ok": ok, "v": np.asarray(s.Bus.v.v).copy(), "a": np.asarray(s.Bus.a.v).copy()}
    result["pflow_max_abs_voltage_difference_pu"] = float(np.abs(pflow["C2"]["v"] - pflow["C2t"]["v"]).max())
    result["pflow_max_abs_angle_difference_rad"] = float(np.abs(pflow["C2"]["a"] - pflow["C2t"]["a"]).max())
    for name in CASES:
        s = load(name)
        s.PFlow.run()
        s.TDS.config.tf, s.TDS.config.tstep, s.TDS.config.fixt, s.TDS.config.no_tqdm = 20.0, 0.00390625, 1, 1
        ok = bool(s.TDS.run(no_summary=True))
        f = np.asarray(s.dae.ts.y[:, s.BusFreq.f.a]) * 60.0
        v = np.asarray(s.dae.ts.y[:, s.Bus.v.a])
        result[f"flat_run_{name}"] = {"converged": ok, "t_end_s": float(s.dae.ts.t[-1]),
                                       "max_abs_frequency_drift_hz": float(np.abs(f - 60.0).max()),
                                       "max_abs_voltage_drift_pu": float(np.abs(v - v[0]).max())}
    scan = {}
    for name in CASES:
        scan[name] = {}
        for alpha in ALPHAS:
            s = load(name, alpha)
            s.PFlow.run()
            scan[name][f"{alpha:.2f}"] = modes(s)
    result["eigen_scan_toward_1p0pu"] = scan
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("pflow dV", result["pflow_max_abs_voltage_difference_pu"], "dA", result["pflow_max_abs_angle_difference_rad"])
    for name in CASES:
        print(name, "flat", result[f"flat_run_{name}"])
        for a, m in scan[name].items():
            z = m["least_damped_oscillatory"]
            print(f"  alpha={a} phys_max_real={m['physical_max_real']:+.3f} excluded={m['excluded_degenerate_count']} "
                  f"least damped {z['real']:+.2f}{z['imag']:+.2f}j zeta={z['zeta']:.3f} unstable={m['unstable_physical_modes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
