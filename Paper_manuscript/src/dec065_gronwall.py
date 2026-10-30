"""DEC-065: norm-based (Gronwall) evaluation of Theorem OS-N with constants taken from the frozen linearisation (ESTIMATES, not certified Lipschitz constants).  Shows how informative the
norm bound is compared with the exact-linear bound of dec065_os.py.  Writes IEEE39_DEC065_os_gronwall.json exclusively with 'write'."""
import json
import sys

import numpy as np

import dec055_common as C55
import dec059_eq as EQ
import dec059_tds as T

TT = 0.05


def main(write=False):
    out = {"label": "DEC065_GRONWALL_ESTIMATE_NO_TDS", "cases": {}}
    for oc, d in (("OC1", "M3REV3"), ("OC2", "M3OS")):
        e = EQ.Eq(oc, T.dispatch_z(oc, d))
        lin = e.plant.L.linearize(e.system, e.ctx, cache=e.cache)
        rows = np.concatenate([e.st["a_p"], e.st["a_q"], e.st["a_v"]]).astype(int)
        A, B, Cx, Cu = lin["A"], lin["B_u"], lin["Cy_x"][rows], lin["Cy_u"][rows]
        n = lambda M: float(np.abs(M).sum(axis=1).max())                      # induced inf-norm
        Lx, Lu, lx, lu = max(n(A), 1e-12), n(B), n(Cx), n(Cu)
        vbar = EQ.refset(e.ctx, e.st)["vbar"]
        W = 2.0 * float(vbar.max())                                           # two box-limited controllers: ||Delta u(s)||_inf <= s * 2 vbar_max
        dx = Lu * W * (np.exp(Lx * TT) - 1 - Lx * TT) / Lx ** 2
        out["cases"][f"{oc}_{d}"] = {"L_x_inf_norm_A": Lx, "L_u": Lu, "ell_x": lx, "ell_u": lu, "W_two_box_controllers": W, "gronwall_dx_bound": float(dx), "gronwall_dy_bound": float(lx * dx + lu * TT * W),
                                     "n_dynamic": int(A.shape[0]), "spectral_abscissa": float(np.linalg.eigvals(A).real.max())}
        print(oc, out["cases"][f"{oc}_{d}"], flush=True)
    if write:
        with open(C55.ART / "IEEE39_DEC065_os_gronwall.json", "x", encoding="utf-8") as f:
            json.dump(out, f, indent=1)


if __name__ == "__main__":
    main("write" in sys.argv)
