"""E9-A helper: frozen-Jacobian linearization of the C2t DAE augmented with the reference states (Pset, Qset).

The reference rate v = d(Pset, Qset)/dt is the input.  The E8 actuator maps are part of the augmented model:
  SG   TGOV1N.paux0 = Pset - Pn                       (direct)
       IEEEX1.vref0 = vref0(0) + kappa (Qset - Qn)    (direct; the +-Z_CLAMP clamp is nonsmooth and is flagged, not linearized)
  GFM  REGF1.Paux0  = KC  (y0  + Pset - Pn - PIplim_y)   (feedback on the algebraic PIplim_y)
       REGF1.Qaux0  = KCQ (y0q + Qset - Qn - PIqlim_y)   (feedback on the algebraic PIqlim_y)
Outputs are algebraic variables of the DAE (P, Q of each unit, bus voltages).  Everything is evaluated at a frozen
operating point; Lie derivatives of order >= 2 along a transient are therefore a local-linear approximation
(curvature terms are neglected); relative degrees are structural and do not depend on this approximation.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from kvxopt import matrix as kv_matrix

import run_e8_ieee39 as e8

FD_EPS = 1.0e-6


def _refresh(system: Any) -> None:
    system.dae.clear_fg()
    system.g_update(system.exist.pflow_tds)
    system.f_update(system.exist.pflow_tds)
    system.fg_to_dae()


def _fg(system: Any) -> tuple[np.ndarray, np.ndarray]:
    _refresh(system)
    return np.array(system.dae.f, dtype=float).copy(), np.array(system.dae.g, dtype=float).copy()


def input_channels(system: Any, ctx: dict[str, Any]) -> list[dict[str, Any]]:
    """The 20 reference channels: 10 Pset then 10 Qset (units ordered SG then GFM), each with its parameter slot(s)."""
    n_sg = ctx["n_sg"]
    ch = []
    for i in range(10):
        if i < n_sg:
            ch.append({"kind": "P", "unit": i, "param": (system.TGOV1N.paux0, ctx["tg_pos"][i]), "gain": 1.0, "fb": None})
        else:
            ch.append({"kind": "P", "unit": i, "param": (system.REGF1.Paux0, i - n_sg), "gain": e8.KC_GFM,
                       "fb": (np.asarray(system.REGF1.PIplim_y.a)[i - n_sg], e8.KC_GFM)})
    for i in range(10):
        if i < n_sg:
            ch.append({"kind": "Q", "unit": i, "param": (system.IEEEX1.vref0, ctx["ex_pos"][i]), "gain": e8.KAPPA_SG, "fb": None})
        else:
            ch.append({"kind": "Q", "unit": i, "param": (system.REGF1.Qaux0, i - n_sg), "gain": e8.KCQ_GFM,
                       "fb": (np.asarray(system.REGF1.PIqlim_y.a)[i - n_sg], e8.KCQ_GFM)})
    return ch


def output_indices(system: Any, ctx: dict[str, Any]) -> dict[str, np.ndarray]:
    n_sg = ctx["n_sg"]
    bus_idx = list(system.Bus.idx.v)
    return {"P": np.concatenate([np.asarray(system.GENROU.Pe.a), np.asarray(system.REGF1.Pe.a)]).astype(int),
            "Q": np.concatenate([np.asarray(system.GENROU.Qe.a), np.asarray(system.REGF1.Qe.a)]).astype(int),
            "Vbus": np.asarray(system.Bus.v.a).astype(int), "bus_ids": np.array([int(b) for b in bus_idx]),
            "Vunit": np.array([np.asarray(system.Bus.v.a)[bus_idx.index(b)] for b in ctx["unit_bus"]]).astype(int)}


def linearize(system: Any, ctx: dict[str, Any], eps: float = FD_EPS) -> dict[str, Any]:
    """Frozen linearization at the current (x, y) of ``system``: returns A (n_d x n_d), B_u (n_d x 20), output maps.

    States with a zero time constant (Tf = 0) are quasi-algebraic: they are eliminated together with the algebraic
    variables y, so the dynamic state xd has dimension n_d = #{Tf > 0}.
    """
    dae = system.dae
    system.j_update(system.exist.pflow_tds)
    fx, fy, gx, gy = (np.array(kv_matrix(m), dtype=float) for m in (dae.fx, dae.fy, dae.gx, dae.gy))
    tf = np.array(kv_matrix(dae.Tf), dtype=float).ravel()
    f0, g0 = _fg(system)
    chans = input_channels(system, {**ctx})
    m = len(chans)
    fp = np.zeros((fx.shape[0], m))
    gp = np.zeros((gy.shape[0], m))
    for j, c in enumerate(chans):
        arr, pos = c["param"]
        old = float(arr.v[pos])
        arr.v[pos] = old + eps
        f1, g1 = _fg(system)
        arr.v[pos] = old
        fp[:, j] = (f1 - f0) / eps
        gp[:, j] = (g1 - g0) / eps
    _refresh(system)  # restore residuals at the unperturbed parameters
    fy_c, gy_c = fy.copy(), gy.copy()
    for j, c in enumerate(chans):
        if c["fb"] is not None:
            col, kc = c["fb"]
            fy_c[:, col] += fp[:, j] * (-kc)
            gy_c[:, col] += gp[:, j] * (-kc)
    gains = np.array([c["gain"] for c in chans])
    fu, gu = fp * gains[None, :], gp * gains[None, :]
    # The IEEEST blocks of the case are degenerate (A1 = A2 = 0; DEC-013): their quasi-algebraic states make the
    # algebraic Jacobian singular and carry no physical dynamics, so they are held at their operating value (dropped).
    ieeest = np.array(["IEEEST" in n for n in dae.x_name])
    d_idx = np.where((tf > 0) & ~ieeest)[0]
    z_idx = np.where((tf == 0) & ~ieeest)[0]
    raw = {"fx": fx, "fy": fy_c, "gx": gx, "gy": gy_c, "fu": fu, "gu": gu, "tf": tf, "d_idx": d_idx, "z_idx": z_idx}
    out = reduce(raw)
    out.update({"raw": raw, "xdot": f0[d_idx] / tf[d_idx], "g0_norm": float(max(np.abs(g0).max(), np.abs(f0[z_idx]).max() if len(z_idx) else 0.0)),
                "n_x": fx.shape[0], "n_y": gy.shape[0], "n_dropped_IEEEST_states": int(ieeest.sum()), "gy_only_cond": float(np.linalg.cond(gy_c))})
    return out


def reduce(raw: dict[str, Any]) -> dict[str, Any]:
    """Eliminate algebraic variables and quasi-algebraic states: A, B_u (dynamic states) and output maps of y."""
    fx, fy, gx, gy, fu, gu, tf = (raw[k] for k in ("fx", "fy", "gx", "gy", "fu", "gu", "tf"))
    d_idx, z_idx = raw["d_idx"], raw["z_idx"]
    nz = len(z_idx)
    kmat = np.block([[fx[np.ix_(z_idx, z_idx)], fy[z_idx]], [gx[:, z_idx], gy]])
    r_x = -np.vstack([fx[np.ix_(z_idx, d_idx)], gx[:, d_idx]])
    r_u = -np.vstack([fu[z_idx], gu])
    sv = np.linalg.svd(kmat, compute_uv=False)
    w_x = np.linalg.solve(kmat, r_x)
    w_u = np.linalg.solve(kmat, r_u)
    fzy_d = np.hstack([fx[np.ix_(d_idx, z_idx)], fy[d_idx]])
    a_dd = (fx[np.ix_(d_idx, d_idx)] + fzy_d @ w_x) / tf[d_idx, None]
    b_du = (fu[d_idx] + fzy_d @ w_u) / tf[d_idx, None]
    return {"A": a_dd, "B_u": b_du, "Cy_x": w_x[nz:], "Cy_u": w_u[nz:], "d_idx": d_idx, "z_idx": z_idx,
            "gy_cond": float(sv[0] / sv[-1]), "gy_min_sv": float(sv[-1]), "gy_max_sv": float(sv[0]), "n_dynamic": len(d_idx),
            "n_quasi_algebraic": nz, "Tf_min_positive": float(tf[d_idx].min())}


def generic(raw: dict[str, Any], seed: int = 7, tol: float = 1e-9) -> dict[str, Any]:
    """Same sparsity, random O(1) values: exposes the structural (generic) zero pattern free of weak-coupling ambiguity."""
    rng = np.random.default_rng(seed)
    g = dict(raw)
    for k in ("fx", "fy", "gx", "fu", "gu"):
        mat = raw[k]
        g[k] = np.where(np.abs(mat) > tol, rng.uniform(0.5, 1.5, mat.shape) * np.sign(mat), 0.0)
    g["gy"] = np.where(np.abs(raw["gy"]) > tol, rng.uniform(0.5, 1.5, raw["gy"].shape) * np.sign(raw["gy"]), 0.0)
    g["gy"] = g["gy"] + np.diag(np.where(np.diag(raw["gy"]) != 0, 0.0, 0.0))
    g["tf"] = np.where(raw["tf"] > 0, rng.uniform(0.5, 1.5, raw["tf"].shape), 0.0)
    return g


def augmented(lin: dict[str, Any], rows: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (A_z, B_v, C_z) for the outputs given by algebraic-variable rows: z = (x, Pset, Qset), v = dz_ref/dt."""
    n_x, m = lin["A"].shape[0], lin["B_u"].shape[1]
    a_z = np.zeros((n_x + m, n_x + m))
    a_z[:n_x, :n_x] = lin["A"]
    a_z[:n_x, n_x:] = lin["B_u"]
    b_v = np.zeros((n_x + m, m))
    b_v[n_x:, :] = np.eye(m)
    c_z = np.hstack([lin["Cy_x"][rows], lin["Cy_u"][rows]])
    return a_z, b_v, c_z


def markov(a_z: np.ndarray, b_v: np.ndarray, c_z: np.ndarray, kmax: int = 8) -> np.ndarray:
    """M[k] = C A^k B for k = 0..kmax-1 (shape kmax x n_out x m)."""
    out = np.zeros((kmax,) + (c_z.shape[0], b_v.shape[1]))
    cur = c_z.copy()
    for k in range(kmax):
        out[k] = cur @ b_v
        cur = cur @ a_z
    return out
