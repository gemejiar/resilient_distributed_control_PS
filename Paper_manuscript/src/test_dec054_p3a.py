"""DEC-054 P3-A analysis tests (synthetic: the 'observation' is generated from a known linear system with the dist_fn alignment; no ANDES, no TDS)."""
import unittest

import numpy as np

import dec054_common as COM
import dec054_p3a_audit as AUD
import dec054_predictor as PRD


class TestCompareRun(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(5)
        n = 8
        Q = rng.normal(size=(n, n))
        self.A = -np.diag(rng.uniform(0.05, 1.5, n)) + 0.2 * (Q - Q.T)
        self.f = rng.normal(size=n) * 0.1
        self.C = rng.normal(size=(10, n)) * 0.3
        self.dP = rng.normal(size=10) * 0.05
        self.x = PRD.excursion(self.A, self.f, self.C)

    def synth_series(self, shift=0.0):
        """Stored series of an event applied before the step 4.99609375->5.0: sample t_k holds P_pre + dP + D(tau_k), tau_k = t_k - 5 + DT."""
        dt = COM.DT
        t = np.arange(0, 200 + dt / 2, dt)
        Ppre = np.linspace(4, 6, 10)
        tau = np.maximum(t - 5.0 + dt, 0.0)
        P = np.tile(Ppre, (len(t), 1))
        post = t >= 5.0 - 1e-9
        D = np.array([np.interp(tau[post], self.x["t"], self.x["D"][i]) for i in range(10)]).T
        P[post] = Ppre + self.dP + D + shift
        return t, P, Ppre

    def test_perfect_prediction_has_zero_errors(self):
        t, P, Ppre = self.synth_series()
        r = AUD.compare_run(t, P, self.dP, self.x["t"], self.x["D"])
        np.testing.assert_allclose(r["Ppre"], Ppre)
        self.assertLess(float(np.abs(r["e_peak"]).max()), 2e-3)           # parabolic refinement vs sampled maximum
        self.assertLess(float(np.abs(r["e_trough"]).max()), 2e-3)
        self.assertLess(float(r["first_sample_error"].max() if False else np.abs(r["first_sample_error"]).max()), 1e-9)
        self.assertLess(float(r["traj_max_abs"].max()), 1e-9)

    def test_optimistic_and_conservative_signs(self):
        t, P, _ = self.synth_series(shift=0.04)                           # observation 0.04 pu higher than predicted
        r = AUD.compare_run(t, P[:, :], self.dP, self.x["t"], self.x["D"])
        self.assertTrue(np.all(r["e_peak"] > 0.03))                          # peak above prediction -> positive (optimistic) error
        self.assertTrue(np.all(r["e_trough"] < -0.03))                       # trough above prediction -> negative (conservative) on the lower side
        t, P, _ = self.synth_series(shift=-0.04)
        r = AUD.compare_run(t, P, self.dP, self.x["t"], self.x["D"])
        self.assertTrue(np.all(r["e_peak"] < -0.03))
        self.assertTrue(np.all(r["e_trough"] > 0.03))

    def test_alignment_offset_matters(self):
        """A model whose time origin is mis-aligned by one step produces a first-sample error: the alignment tau = t - 5 + dt is what the code implements."""
        t, P, _ = self.synth_series()
        i0 = int(np.argmin(np.abs(t - 5.0)))
        P2 = P.copy(); P2[i0:] = P[i0 - 1:-1]                                  # series delayed by one step
        r = AUD.compare_run(t, P2, self.dP, self.x["t"], self.x["D"])
        self.assertGreater(float(np.abs(r["first_sample_error"]).max()), 1e-4)

    def test_plan_constants(self):
        self.assertEqual(AUD.CRITERIA["binding_units"], ["SG31", "SG35"])
        sc = AUD.scenarios(np.zeros(19), np.zeros(19))
        self.assertEqual(len(sc), 8)
        self.assertTrue(all(s[1] in COM.DESIGN for s in sc))                  # DESIGN buses only
        self.assertEqual(len({s[0] for s in sc}), 8)


if __name__ == "__main__":
    unittest.main(verbosity=2)
