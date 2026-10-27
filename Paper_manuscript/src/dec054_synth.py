"""DEC-054 synthetic test plant (isolated; no ANDES, no historical data beyond the public case limits).  It exercises the full chain
z -> I(z) -> pre-event outputs -> algebraic jump -> affine post-event predictor -> margins, so that unit tests can verify the algorithms
(M0-M3, Algorithm 1, ablation of I(z)) without touching the plant.  It is NOT a model of IEEE-39 and its numbers are not evidence."""
from __future__ import annotations

import numpy as np

import dec054_rdcinit as RI
import dec054_predictor as PRD
from dec054_common import N_PV, N_V, N_Z, PV_IDX, SLACK_IDX, UNITS

LIM = {  # case limits (system base pu), same values as the E8 unit arrays
    "pmax": np.array([10.4, 6.5, 6.82, 6.97, 8.65, 11.0, 7.5, 5.64, 5.5, 5.95]), "pmin": np.zeros(10),
    "qmax": np.array([1.5318, 4.29804, 5.48208, 5.93788, 8.34775, 5.7485, 4.46722, 4.43468, 6.11495, 5.68372]),
    "qmin": np.array([-0.58084, -1.22665, -2.1378, -2.34972, -3.56889, -1.73261, -1.80218, -2.16122, -1.88028, -2.49132]),
    "smax": np.array([10.4, 8.36, 11.748, 10.857, 16.841, 11.99, 8.437, 9.702, 10.802, 10.252]), "is_sg": np.arange(10) < 6}


class SyntheticPlant:
    units = UNITS

    def __init__(self, seed: int = 0, stale_init: bool = False):
        rng = np.random.default_rng(seed)
        self.limits = LIM
        p_ref = np.array([4.36, 6.46, 6.52, 6.87, 7.65, 5.73, 7.25, 3.215, 5.08, 5.80])           # C2t-like pre-event P (Slack = SG39)
        q_ref = np.array([0.93, 3.11, 1.30, 2.26, 1.23, -0.30, 1.49, -0.28, 1.45, 0.61])
        self.p_tot = p_ref.sum()
        self.q_ref = q_ref
        self.z_ref = np.concatenate([p_ref[PV_IDX], np.ones(N_V)])
        self.z_lo = np.concatenate([np.maximum(LIM["pmin"][PV_IDX], 0.05), 0.95 * np.ones(N_V)])
        self.z_hi = np.concatenate([LIM["pmax"][PV_IDX], 1.05 * np.ones(N_V)])
        W = rng.uniform(0.2, 1.0, (39, N_V))
        self.Mv = W / W.sum(axis=1, keepdims=True)                      # bus voltage = weighted mean of unit set-points
        self.Mp = 0.002 * rng.normal(size=(39, N_PV))
        self.Bq = np.diag(rng.uniform(2.0, 6.0, N_V))
        # modal data for the post-event predictor (5 damped oscillators => 10 states) and output map
        self.w = rng.uniform(0.3, 2.5, 5)
        self.zeta0 = rng.uniform(0.04, 0.2, 5)
        self.C = rng.normal(size=(NU, 10)) * 0.15
        self.stale = None
        self._ref_I = None
        self.use_stale = stale_init
        self.n_eval = 0

    # ------------------------------------------------------------------ pre-event
    def _outputs(self, z):
        p0, v0 = z[:N_PV], z[N_PV:]
        P = np.empty(NU)
        P[PV_IDX] = p0
        loss = 0.004 * float(np.sum(p0 ** 2)) / 10.0
        P[SLACK_IDX] = self.p_tot + loss - p0.sum()
        Q = self.q_ref + self.Bq @ (v0 - 1.0)
        V = self.Mv @ v0 + self.Mp @ (p0 - self.z_ref[:N_PV])
        return P, Q, V

    def evaluate(self, z):
        self.n_eval += 1
        z = np.asarray(z, float)
        if np.any(z < self.z_lo - 1e-9) or np.any(z > self.z_hi + 1e-9):
            return {"ok": False}
        P, Q, V = self._outputs(z)
        try:
            I = RI.init_map(P, Q, self.limits, p_floor=0.0)
        except RI.InitError:
            return {"ok": False}
        return {"ok": True, "P": P, "Q": Q, "V": V, "I": I}

    # ------------------------------------------------------------------ event
    def _sens(self, sc):
        r = np.random.default_rng(1000 + sc.bus + (0 if sc.kind == "P" else 500))
        s = r.uniform(0.0, 0.14, NU)
        s[r.integers(0, NU, 2)] += 0.12
        return s

    def jump(self, z, sc):
        e = self.evaluate(z)
        if not e["ok"]:
            return {"ok": False}
        s = self._sens(sc)
        dP = sc.amp * s * (1.0 + 0.15 * (e["P"] - self._ref_P()) / self._ref_P())          # mild dependence on z (nonlinear)
        dQ = 0.3 * dP
        return {"ok": True, "dP": dP, "dQ": dQ, "P_plus": e["P"] + dP, "Q_plus": e["Q"] + dQ, "V_plus": e["V"] - 0.01 * sc.amp * np.ones(39), "sigma_min": 0.1}

    def _ref_P(self):
        return np.array([4.36, 6.46, 6.52, 6.87, 7.65, 5.73, 7.25, 3.215, 5.08, 5.80])

    def affine(self, z, sc):
        """A+(z,d), f+(z,d), C: depend on I(z) through the effective integral gains (the controller is part of the design model)."""
        e = self.evaluate(z)
        I = e["I"]
        if self.use_stale:                      # A5 ablation: initialisation frozen at z_ref (the DEC-051 hazard)
            if self._ref_I is None:
                self._ref_I = self.evaluate(self.z_ref)["I"]
            I = RI.stale_init(self._ref_I)
        g = float(np.mean(I["gain_eff_p"][[1, 3]]))        # SG31/SG35 effective integral gains (the mean over units is constant by construction of k_ip)
        A = np.zeros((10, 10))
        for k in range(5):
            zeta = self.zeta0[k] / (0.5 + 0.02 * g)                          # more integral gain -> less damping
            A[2 * k:2 * k + 2, 2 * k:2 * k + 2] = [[0.0, 1.0], [-self.w[k] ** 2, -2 * zeta * self.w[k]]]
        s = self._sens(sc)
        f = np.zeros(10)
        f[1::2] = sc.amp * s[:5] * 0.8
        return A, f, self.C

    def excursion(self, z, sc):
        A, f, C = self.affine(z, sc)
        x = PRD.excursion(A, f, C)
        return {"E_up": x["E_up"], "E_dn": x["E_dn"], "t_up": x["t_up"], "sampling_error": x["sampling_error_up"]}


NU = 10
