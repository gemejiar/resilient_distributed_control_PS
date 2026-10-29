"""DEC-059 unit tests of the B5' QP layer (no ANDES).  Run:  <venv python> -m pytest -q test_dec059.py   (or python test_dec059.py)
Checks T1 (discrete reference invariance), T1-F (0 feasible on W, uniqueness), fast path = solver, optimality against an independent solver,
v* = 0 at the target (Lemma C), the CLF-row sign convention, and the A-INFO schedule."""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

import dec059_b5 as B5

N, NSG = 10, 6
H = 2.0 ** -8


def instance(seed):
    rng = np.random.default_rng(seed)
    pmax = rng.uniform(3, 9, N)
    lim = {"pmax": pmax, "pmin": np.zeros(N), "qmax": rng.uniform(1, 4, N), "qmin": -rng.uniform(1, 4, N), "smax": pmax * rng.uniform(1.05, 1.3, N)}
    qn = rng.uniform(lim["qmin"] * 0.5, lim["qmax"] * 0.5)
    rs = B5.refset(lim, NSG, qn)
    for _ in range(1000):                                      # interior starting point
        u = np.concatenate([rng.uniform(0.05, 0.98) * pmax, qn + rng.normal(0, 0.1, N)])
        ca, cd = B5.margins(rs, u)
        if ca.min() > 0 and cd.min() > 0:
            return rs, u, rng
    raise RuntimeError


def test_zero_feasible_on_W():
    for seed in range(20):
        rs, u, _ = instance(seed)
        assert B5.hard_ok(rs, u, np.zeros(2 * N), H)
        assert B5.theta(rs, u, np.zeros(2 * N), H) == 1.0


def test_T1_invariance_random_walk():
    """Adversarial nominal commands pushing toward the boundaries: c_j(u_k) >= (1 - gamma)^k c_j(u_0) for all k, so u_k stays in W."""
    for seed in range(6):
        rs, u, rng = instance(100 + seed)
        ca0, cd0 = B5.margins(rs, u)
        g = B5.ALPHA * H
        direction = rng.choice([-1.0, 1.0], 2 * N)
        for k in range(1, 401):
            vnom = direction * rs["vbar"] * rng.uniform(1.0, 50.0, 2 * N)
            v, s, info = B5.solve_qp(rs, u, vnom, H)
            assert B5.hard_ok(rs, u, v, H, tol=1e-12), (seed, k, info)
            u = u + H * v
            ca, cd = B5.margins(rs, u)
            assert ca.min() >= 0 and cd.min() >= 0
            assert np.all(ca >= (1 - g) ** k * ca0 - 1e-9) and np.all(cd >= (1 - g) ** k * cd0 - 1e-9)


def test_fast_path_equals_solver():
    rs, u, rng = instance(7)
    vnom = 0.3 * rs["vbar"] * rng.uniform(-1, 1, 2 * N)
    v0, _, i0 = B5.solve_qp(rs, u, vnom, H)
    v1, _, i1 = B5.solve_qp(rs, u, vnom, H, force_solver=True)
    assert i0["path"] == 0 and i1["path"] == 1
    assert np.abs(v0 - v1).max() <= 1e-7 * rs["vbar"].max()


def test_optimality_against_slsqp():
    """Infeasible nominal command; the cone-QP minimiser equals an independent SLSQP minimiser (objective within 1e-6 relative)."""
    for seed in range(5):
        rs, u, rng = instance(200 + seed)
        vnom = rs["vbar"] * rng.uniform(-3, 3, 2 * N)
        v, s, info = B5.solve_qp(rs, u, vnom, H)
        R = 1 / rs["vbar"] ** 2
        obj = lambda w: 0.5 * np.sum(R * (w - vnom) ** 2)                      # noqa: E731
        ca, cd = B5.margins(rs, u)
        g = B5.ALPHA * H
        cons = [{"type": "ineq", "fun": lambda w: rs["A"] @ w + B5.ALPHA * ca},
                {"type": "ineq", "fun": lambda w: rs["s"] ** 2 - (1 - g) * cd - (u[:N] + H * w[:N]) ** 2 - (u[N:] + H * w[N:]) ** 2}]
        bnds = [(-b, b) for b in rs["vbar"]]
        ref = minimize(obj, np.zeros(2 * N), method="SLSQP", bounds=bnds, constraints=cons, options={"ftol": 1e-14, "maxiter": 500})
        assert ref.success
        assert abs(obj(v) - ref.fun) <= 1e-6 * max(1.0, ref.fun), (obj(v), ref.fun)
        assert B5.hard_ok(rs, u, v, H, tol=1e-12)


def test_target_fixed_point():
    """Lemma C: v_nom = 0 and the CLF row 0 <= 0 at e = 0 give v* = 0, s = 0."""
    rs, u, rng = instance(9)
    g = rng.normal(size=2 * N)
    v, s, info = B5.solve_qp(rs, u, np.zeros(2 * N), H, clf=(g / np.linalg.norm(g), 0.0))
    assert np.all(v == 0) and s == 0.0 and info["path"] == 0


def test_clf_row_enforced_when_feasible():
    """Nominal violates g'v <= bc with a feasible correction available: the solution meets the row up to a small slack (rho_s large)."""
    rs, u, rng = instance(11)
    vnom = 0.5 * rs["vbar"] * rng.uniform(-1, 1, 2 * N)
    g = rng.normal(size=2 * N)
    g /= np.linalg.norm(g)
    bc = float(g @ vnom) - 0.02 * float(np.abs(g) @ rs["vbar"])            # violated by v_nom, reachable inside the box
    v, s, info = B5.solve_qp(rs, u, vnom, H, clf=(g, bc))
    assert info["path"] == 1
    assert float(g @ v) <= bc + s + 1e-9
    scale = 0.02 * float(np.abs(g) @ rs["vbar"])
    assert s <= 1e-2 * scale                                               # soft row: s ~ multiplier / rho_s, small against the row scale
    v2, s2, _ = B5.solve_qp(rs, u, vnom, H, clf=(g, bc), rho_s=1e8)
    assert s2 < s                                                          # and decreasing in rho_s
    assert B5.hard_ok(rs, u, v, H, tol=1e-12)


def test_schedule():
    assert B5.schedule(4.9, 5.0, 1.0, True) == ("pre", True)
    assert B5.schedule(5.0, 5.0, 1.0, True) == ("pre", False)
    assert B5.schedule(5.99, 5.0, 1.0, True) == ("pre", False)
    assert B5.schedule(6.0, 5.0, 1.0, True) == ("post", True)
    assert B5.schedule(50.0, 5.0, 1.0, False) == ("pre", True)


def test_theta_scaling_exact():
    rs, u, rng = instance(13)
    v = rs["vbar"] * rng.uniform(-40, 40, 2 * N)
    t = B5.theta(rs, u, v, H)
    assert 0 <= t <= 1
    assert B5.hard_ok(rs, u, t * v * (1 - 1e-12), H)


if __name__ == "__main__":
    import sys
    fails = 0
    for name, f in list(globals().items()):
        if name.startswith("test_") and callable(f):
            try:
                f()
                print("PASS", name)
            except AssertionError as ex:
                fails += 1
                print("FAIL", name, ex)
    sys.exit(1 if fails else 0)
