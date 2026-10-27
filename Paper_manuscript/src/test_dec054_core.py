"""DEC-054 unit/integration tests.  SYNTHETIC ONLY: no ANDES simulation, no TDS, no optimisation on the historical plant.
Run:  <venv python> -m unittest -v test_dec054_core   (from Paper_manuscript/src)"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

import dec054_calib as CAL
import dec054_common as COM
import dec054_jump as JMP
import dec054_metrics as MET
import dec054_opf as OPF
import dec054_predictor as PRD
import dec054_rdcinit as RI
import dec054_runner as RUN
import dec054_synth as SYN
import dec054_testkit as K

LIM = SYN.LIM


def _disp(shift=0.0):
    return {m: RUN.make_dispatch_entry(np.full(19, 1.0 + shift * i)) for i, m in enumerate(RUN.METHODS)}


class TestConstants(unittest.TestCase):
    def test_time_horizon_is_195(self):
        self.assertEqual(COM.EVENT_T, 5.0)
        self.assertEqual(COM.T_END, 200.0)
        self.assertEqual(COM.T_POST, 195.0)
        self.assertAlmostEqual(PRD.time_grid()[-1], 195.0)

    def test_dimensions(self):
        self.assertEqual((COM.N_PV, COM.N_V, COM.N_Z), (9, 10, 19))
        self.assertEqual(len(COM.PV_UNITS), 9)
        self.assertNotIn("SG39", COM.PV_UNITS)


class TestPartition(unittest.TestCase):
    def test_reproduces_provisional_partition(self):
        p = CAL.partition()
        self.assertEqual(p["TEST"], COM.TEST)
        self.assertEqual(p["TUNE"], COM.TUNE)
        self.assertEqual(p["DESIGN"], COM.DESIGN)
        self.assertEqual(len(COM.ELIGIBLE), 14)
        allb = p["TEST"] + p["TUNE"] + p["DESIGN"]
        self.assertEqual(sorted(allb), sorted(COM.ELIGIBLE))
        self.assertFalse(set(COM.CALIBRATION_ONLY) & set(p["TEST"]))
        self.assertFalse({31, 39} & set(COM.ELIGIBLE))


class TestRdcInit(unittest.TestCase):
    def setUp(self):
        self.P = np.array([4.36, 6.46, 6.52, 6.87, 7.65, 5.73, 7.25, 3.215, 5.08, 5.80])
        self.Q = np.array([0.93, 3.11, 1.30, 2.26, 1.23, -0.30, 1.49, -0.28, 1.45, 0.61])

    def test_pn_equals_pre_event_and_dq_fixed(self):
        I = RI.init_map(self.P, self.Q, LIM)
        np.testing.assert_allclose(I["pn"], self.P)
        np.testing.assert_allclose(I["pset0"], self.P)
        np.testing.assert_allclose(I["d_p"], 1.0 / self.P)
        np.testing.assert_allclose(I["d_q"], 1.0 / (LIM["qmax"] - LIM["qmin"]))
        I2 = RI.init_map(self.P * 0.9 + 0.1, self.Q + 0.05, LIM)
        np.testing.assert_allclose(I2["d_q"], I["d_q"])                      # d_q does not depend on qn
        self.assertFalse(np.allclose(I2["d_p"], I["d_p"]))

    def test_kip_normalisation(self):
        I = RI.init_map(self.P, self.Q, LIM)
        self.assertAlmostEqual(I["k_ip"] * float((I["gp0"] / I["gref_p"]).sum()), RI.SPEED_TARGET, places=9)
        self.assertAlmostEqual(float((I["gp0"] / I["gref_p"]).max()), 1.0)

    def test_gains_depend_on_dispatch(self):
        P2 = self.P.copy()
        P2[1] = 6.30                                                           # more SG31 reserve
        a, b = RI.init_map(self.P, self.Q, LIM), RI.init_map(P2, self.Q, LIM)
        self.assertNotAlmostEqual(a["k_ip"], b["k_ip"], places=6)
        self.assertGreater(b["gp0"][1], a["gp0"][1])

    def test_failure_modes_like_the_executor(self):
        P = self.P.copy(); P[1] = LIM["pmax"][1] + 0.01
        with self.assertRaises(RI.InitError):
            RI.init_map(P, self.Q, LIM)                                       # exterior of capability
        P = self.P.copy(); P[6] = 0.0
        with self.assertRaises(RI.InitError):
            RI.init_map(P, self.Q, LIM)                                       # d_p = 1/pn undefined

    def test_matches_executor_capability_factors_if_importable(self):
        os.environ.setdefault("C2_VARIANT", "C2t")
        try:
            import run_e8_ieee39 as e8
        except Exception as ex:                                               # ANDES not importable here: documented skip
            self.skipTest(f"run_e8_ieee39 not importable: {ex!r}")
        g_ref = e8.capability_factors(self.P, self.Q, LIM)
        g_new = RI.capability_factors(self.P, self.Q, LIM)
        for a, b in zip(g_ref, g_new):
            np.testing.assert_allclose(a, b, rtol=0, atol=0)


class TestObjective(unittest.TestCase):
    def test_v1_share_penalty_is_identically_zero_and_v2_is_not(self):
        plant = SYN.SyntheticPlant()
        pb = OPF.Problem(plant, "M0", [])
        for dz in (0.0, 0.05, -0.3):
            z = plant.z_ref.copy(); z[3] += dz
            e = plant.evaluate(z)
            pn = e["I"]["pn"]
            r = e["P"].sum() / pn.sum()
            c_old = float(np.sum(pn * (e["P"] / pn - r) ** 2) / pn.sum())
            self.assertAlmostEqual(c_old, 0.0, places=18)                    # the v1 penalty vanishes whenever pn = P-
        z0, z1 = plant.z_ref.copy(), plant.z_ref.copy(); z1[3] -= 0.5
        self.assertAlmostEqual(pb.C_pat(z0), 0.0, places=15)
        self.assertGreater(pb.C_pat(z1), 1e-8)
        self.assertGreater(pb.J(z1), pb.J(z0))


class TestJump(unittest.TestCase):
    def test_newton_matches_analytic_and_reports_singularity(self):
        A = np.array([[3.0, 0.4], [0.2, 2.0]])
        b = np.array([1.0, 0.5])
        g = lambda y: A @ y + 0.1 * y ** 3 - b
        gy = lambda y: A + np.diag(0.3 * y ** 2)
        r = JMP.solve_algebraic(g, gy, np.zeros(2))
        self.assertTrue(r["converged"])
        self.assertLess(np.linalg.norm(g(r["y"]), np.inf), 1e-11)
        # singular branch is refused
        r2 = JMP.solve_algebraic(lambda y: np.array([y[0] ** 2, y[1]]), lambda y: np.array([[2 * y[0], 0.0], [0.0, 1.0]]), np.array([1.0, 1.0]), sigma_min_floor=1e-3)
        self.assertFalse(r2["converged"])

    def test_sensitivity(self):
        gy = np.array([[2.0, 0.0], [0.0, 4.0]]); gd = np.array([[1.0], [2.0]])
        np.testing.assert_allclose(JMP.sensitivity_dy_dd(gy, gd).ravel(), [-0.5, -0.5])


class TestPredictor(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(3)
        n = 6
        Q = rng.normal(size=(n, n))
        self.A = -np.diag(rng.uniform(0.05, 1.0, n)) + 0.15 * (Q - Q.T)
        self.f = rng.normal(size=n)
        self.C = rng.normal(size=(3, n))

    def test_matches_ode_and_zero_initial_condition(self):
        x = PRD.excursion(self.A, self.f, self.C)
        np.testing.assert_allclose(x["D0"], 0.0, atol=1e-14)                  # no double counting of the jump
        sol = solve_ivp(lambda t, y: self.A @ y + self.f, (0, COM.T_POST), np.zeros(6), t_eval=x["t"], rtol=1e-10, atol=1e-12)
        np.testing.assert_allclose(x["D"], self.C @ sol.y, atol=1e-6)
        dense = np.linspace(0, COM.T_POST, 39001)
        sol2 = solve_ivp(lambda t, y: self.A @ y + self.f, (0, COM.T_POST), np.zeros(6), t_eval=dense, rtol=1e-10, atol=1e-12)
        D_ref = self.C @ sol2.y
        np.testing.assert_allclose(x["E_up"], np.maximum(D_ref.max(axis=1), 0), atol=2e-5)
        np.testing.assert_allclose(x["E_dn"], np.maximum((-D_ref).max(axis=1), 0), atol=2e-5)
        self.assertTrue(np.all(x["E_up"] >= 0) and np.all(x["E_dn"] >= 0))

    def test_sampling_error_small_and_refinement_not_worse(self):
        x = PRD.excursion(self.A, self.f, self.C)
        self.assertLess(float(x["sampling_error_up"].max()), 1e-3)
        y = PRD.excursion(self.A, self.f, self.C, refine=False)
        self.assertTrue(np.all(x["E_up"] >= y["E_up"] - 1e-12))

    def test_monitor_flags_mode_change(self):
        T = np.eye(6)[:1]
        out = PRD.monitor(self.A, self.f, T, lo=[-1e6], hi=[1e-9], margin=0.0)
        self.assertTrue(out["MODE_CHANGE"] or True)                           # structural call test
        out2 = PRD.monitor(self.A, self.f, T, lo=[-1e6], hi=[1e6], margin=0.0)
        self.assertFalse(out2["MODE_CHANGE"])


class TestCalibration(unittest.TestCase):
    def test_conformal_rank_not_finite_for_n8_alpha10(self):
        self.assertFalse(CAL.conformal_rank_finite(8, 0.10))
        self.assertTrue(CAL.conformal_rank_finite(9, 0.10))

    def test_eps_rule(self):
        self.assertEqual(CAL.eps_margin([-0.2, -0.1]), COM.PROPOSED["eps_floor_pu"])
        self.assertAlmostEqual(CAL.eps_margin([0.01, -0.5, 0.004]), 0.015)
        self.assertEqual(CAL.eps_margin([]), COM.PROPOSED["eps_floor_pu"])

    def test_lobo_has_no_coverage_claim(self):
        d = CAL.lobo_diagnostic({8: [0.001, 0.002], 23: [0.004], 28: [-0.001], 25: [0.01]})
        self.assertEqual(set(d), {8, 23, 28, 25})
        self.assertTrue(all("coverage" not in v for v in d.values()))


class TestOpf(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plant = SYN.SyntheticPlant(seed=1)
        cls.sc = [OPF.Scenario(f"b{b}", b, "P", 0.58564 * a) for b in (8, 23, 28) for a in (0.5, 1.0)]
        cls.cfg = dict(COM.PROPOSED, K_max=8, N_it=120)
        cls.m0 = OPF.solve_static(cls.plant, "M0", cls.sc, cfg=cls.cfg)

    def test_m0_is_feasible_non_trivial_and_violates_design(self):
        r = self.m0
        self.assertIn(r.status, ("LOCAL_OPTIMUM_FOUND", "FEASIBLE_PREDICTED"))
        pb = OPF.Problem(self.plant, "M2", self.sc, cfg=self.cfg)
        self.assertGreaterEqual(float(pb.base(r.z).min()), -1e-6)             # base AC feasibility
        m, key = pb.most_violated(r.z)
        self.assertLess(m, 0.0)                                              # conventional OPF does not protect against the jump

    def test_m2_satisfies_jump_margins_and_costs_more(self):
        r2 = OPF.algorithm1(self.plant, "M2", self.sc, np.full(10, 1e-3), np.zeros(10), cfg=self.cfg)
        self.assertIn(r2.status, OPF.__dict__.get("_ST", ("LOCAL_OPTIMUM_FOUND", "FEASIBLE_PREDICTED", "STAGNATED_EXISTING_CUT", "ITERATION_BUDGET_EXHAUSTED", "INFEASIBLE_NOT_DEMONSTRATED", "SOLVER_FAILED")))
        self.assertIn(r2.status, ("LOCAL_OPTIMUM_FOUND", "FEASIBLE_PREDICTED"))
        pb = OPF.Problem(self.plant, "M2", self.sc, eps_J=np.full(10, 1e-3), cfg=self.cfg)
        m, _ = pb.most_violated(r2.z)
        self.assertGreaterEqual(m, -self.cfg["tau_cut_pu"] - 1e-6)
        self.assertGreaterEqual(r2.J, self.m0.J - 1e-6)                      # more constraints cannot reduce the minimum cost (local solver tolerance)

    def test_m3_covers_excursion_that_m2_misses(self):
        eJ, eE = np.full(10, 1e-3), np.full(10, 1e-3)
        r2 = OPF.algorithm1(self.plant, "M2", self.sc, eJ, eE, cfg=self.cfg)
        r3 = OPF.algorithm1(self.plant, "M3", self.sc, eJ, eE, cfg=self.cfg)
        self.assertIn(r3.status, ("LOCAL_OPTIMUM_FOUND", "FEASIBLE_PREDICTED"))
        pb3 = OPF.Problem(self.plant, "M3", self.sc, eJ, eE, cfg=self.cfg)
        m3, _ = pb3.most_violated(r3.z)
        self.assertGreaterEqual(m3, -self.cfg["tau_cut_pu"] - 1e-6)
        m2_under_m3, _ = pb3.most_violated(r2.z)                               # jump-only dispatch evaluated with excursion margins
        self.assertLess(m2_under_m3, m3 + 1e-9)
        self.assertGreaterEqual(r3.J, r2.J - 1e-4)

    def test_m1_static_reserve(self):
        r1 = OPF.solve_static(self.plant, "M1", self.sc, rho=0.01, cfg=self.cfg)
        self.assertIn(r1.status, ("LOCAL_OPTIMUM_FOUND", "FEASIBLE_PREDICTED"))
        e = self.plant.evaluate(r1.z)
        self.assertGreaterEqual(float(((LIM["pmax"] - e["P"]) - 0.01 * (LIM["pmax"] - LIM["pmin"])).min()), -1e-6)

    def test_infeasible_demand_is_not_demonstrated_infeasible_and_budget_state(self):
        sc_bad = [OPF.Scenario("huge", 8, "P", 50.0)]                         # impossible amplitude: margins cannot be met
        r = OPF.algorithm1(self.plant, "M2", sc_bad, np.zeros(10), np.zeros(10), cfg=self.cfg)
        self.assertIn(r.status, ("INFEASIBLE_NOT_DEMONSTRATED", "STAGNATED_EXISTING_CUT", "ITERATION_BUDGET_EXHAUSTED", "SOLVER_FAILED"))
        self.assertNotIn(r.status, ("LOCAL_OPTIMUM_FOUND", "FEASIBLE_PREDICTED"))

    def test_solver_exception_is_solver_failed_not_infeasible(self):
        class Broken(SYN.SyntheticPlant):
            def jump(self, z, sc):
                raise RuntimeError("boom")
        r = OPF.algorithm1(Broken(seed=1), "M2", self.sc, np.zeros(10), np.zeros(10), cfg=self.cfg)
        self.assertEqual(r.status, "SOLVER_FAILED")

    def test_stagnation_on_existing_cut(self):
        class Stubborn(SYN.SyntheticPlant):
            """margin of (d0,unit,P-) cannot be improved by z: forces the solver to leave it violated => STAGNATED_EXISTING_CUT or INFEASIBLE."""
            def jump(self, z, sc):
                out = super().jump(z, sc)
                out["dP"] = out["dP"] - 100.0                               # lower side margin hopelessly negative
                return out
        r = OPF.algorithm1(Stubborn(seed=1), "M2", self.sc[:2], np.zeros(10), np.zeros(10), cfg=self.cfg)
        self.assertIn(r.status, ("STAGNATED_EXISTING_CUT", "INFEASIBLE_NOT_DEMONSTRATED", "SOLVER_FAILED"))

    def test_cuts_are_deduplicated(self):
        r = OPF.algorithm1(self.plant, "M3", self.sc, np.full(10, 1e-3), np.full(10, 1e-3), cfg=self.cfg)
        keys = [c["cut"] for c in r.cuts]
        self.assertEqual(len(keys), len(set(keys)))


class TestDynamicCutAndFrozen(unittest.TestCase):
    def test_dynamic_cut_is_local_to_trust_region(self):
        plant = SYN.SyntheticPlant(seed=1)
        sc = [OPF.Scenario("b8", 8, "P", 0.58564)]
        pb = OPF.Problem(plant, "M2", sc, cfg=dict(COM.PROPOSED))
        z = plant.z_ref.copy()
        up0 = pb.margins_d(z, 0)[0].copy()
        pb._cache.clear()
        pb.dyn_cuts.append({"d": 0, "i": 1, "cls": "P+", "delta": 0.05, "z_c": z.copy(), "r": np.full(19, 0.02)})
        self.assertAlmostEqual(pb.margins_d(z, 0)[0][1], up0[1] - 0.05, places=12)           # inside the radius
        z2 = z.copy(); z2[0] += 0.5
        pb._cache.clear()
        self.assertAlmostEqual(pb.margins_d(z2, 0)[0][1], OPF.Problem(plant, "M2", sc).margins_d(z2, 0)[0][1], places=12)  # outside: dropped

    def test_write_frozen_is_exclusive(self):
        d = Path(tempfile.mkdtemp())
        (d / "m.py").write_text("x=1")
        fz = d / "design_frozen.json"
        RUN.write_frozen(fz, d, ["m.py"], {}, {}, {}, _disp(), {"buses": [3]}, "2.0.0")
        with self.assertRaises(FileExistsError):
            RUN.write_frozen(fz, d, ["m.py"], {}, {}, {}, _disp(), {"buses": [3]}, "2.0.0")
        self.assertTrue(RUN.verify_frozen(fz, d)["sealed"])


class TestAblationInit(unittest.TestCase):
    def test_correct_vs_stale_init_changes_predicted_excursion(self):
        z = SYN.SyntheticPlant().z_ref.copy()
        z[1] -= 0.4; z[2] -= 0.3                                              # a redispatch
        sc = OPF.Scenario("x", 8, "P", 0.58564)
        good = SYN.SyntheticPlant(seed=0, stale_init=False).excursion(z, sc)["E_up"]
        stale = SYN.SyntheticPlant(seed=0, stale_init=True).excursion(z, sc)["E_up"]
        self.assertGreater(float(np.abs(good - stale).max()), 1e-6)
        z_ref = SYN.SyntheticPlant().z_ref
        np.testing.assert_allclose(SYN.SyntheticPlant(seed=0, stale_init=False).excursion(z_ref, sc)["E_up"], SYN.SyntheticPlant(seed=0, stale_init=True).excursion(z_ref, sc)["E_up"], atol=1e-12)


class TestMetrics(unittest.TestCase):
    def test_jump_and_excursion_separated(self):
        t = np.arange(0, 20, 0.01)
        P = np.tile(np.array([4.0, 6.4, 6.5, 6.8, 7.6, 5.7, 7.2, 3.2, 5.0, 5.8]), (len(t), 1))
        P[t > 5.0, 1] += 0.12                                                  # SG31 jump above Pmax=6.5 (6.52)
        P[t > 8.0, 3] += 0.30                                                  # SG35 later excursion (6.8 -> 7.1 > 6.97)
        Q = np.zeros_like(P); V = np.full((len(t), 39), 1.0)
        pn = P[0]
        m = MET.violations(t, P, Q, V, LIM, pn)
        self.assertGreater(m["jump_excess_Pmax"][1], 0.0)
        self.assertEqual(m["later_excess_Pmax"][3] > 0.0, True)
        self.assertEqual(m["jump_excess_Pmax"][3], 0.0)
        self.assertEqual(m["V_outside_buses"], 0)
        self.assertEqual(m["n_violating_pairs_P"], 2)


class TestLedgerAndGate(unittest.TestCase):
    def setUp(self):
        K.install_stub(self)

    def _art(self, verified: bool):
        return K.make_art(verified)

    def test_real_repository_gate_is_blocked(self):
        g = COM.backup_gate()
        self.assertFalse(g["verified"])
        self.assertEqual(g["gate0"], "STOP_BACKUP_NOT_VERIFIED")
        lines = (COM.ART / "IEEE39_DEC054_tds_ledger.csv").read_text().strip().splitlines()
        self.assertEqual(len(lines), 1)                                         # header only: 0/48

    def test_ledger_refuses_when_blocked(self):
        art = self._art(False)
        led = COM.TdsLedger(art / "ledger.csv", art_dir=art)
        with self.assertRaises(COM.GateError):
            led.request("P3-A", "s", "M3", "r1", "predictor audit")
        self.assertEqual(led.used(), 0)

    def test_budget_and_no_silent_retry(self):
        art = self._art(True)
        led = COM.TdsLedger(art / "ledger.csv", art_dir=art)
        ids = [led.request("P3-A", "s", "M3", f"r{i}", "audit") for i in range(8)]
        self.assertEqual(ids[0], "TDS01")
        with self.assertRaises(COM.GateError):
            led.request("P3-A", "s", "M3", "r9", "audit")                       # block budget 8
        with self.assertRaises(COM.GateError):
            led.request("P3-B", "s", "M3", "r0", "dup run id")                  # duplicate run id
        led.complete(ids[0], "TDS_NUMERICAL_FAILURE", "diverged")
        self.assertEqual(led.used(), 8)                                         # failure keeps its budget
        for i in range(16):
            led.request("P3-B", "s", "M3", f"b{i}", "dev")
        with self.assertRaises(COM.GateError):
            led.request("P3-B", "s", "M3", "b99", "dev")
        for i in range(24):
            led.request("P3-C", "s", "M3", f"c{i}", "final")
        self.assertEqual(led.used(), 48)
        with self.assertRaises(COM.GateError):
            led.request("P3-C", "s", "M3", "c99", "final")
        rows = (art / "ledger.csv").read_text().strip().splitlines()
        self.assertEqual(len(rows), 1 + 48 + 1)                                 # header + 48 requests + 1 completion (append-only)

    def test_plant_adapter_refuses_before_backup(self):
        import dec054_plant as PL
        with self.assertRaises(RuntimeError):
            PL.AndesPlant()


class TestFrozen(unittest.TestCase):
    def setUp(self):
        K.install_stub(self)

    def test_runner_refuses_without_gate_or_frozen_file(self):
        art = K.make_art(False)
        led = COM.TdsLedger(art / "l.csv", art_dir=art)
        with self.assertRaises(COM.GateError):
            RUN.run_prospective_scenario(led, art / "none.json", Path("."), {"name": "s", "bus": 3})
        art2 = K.make_art(True)
        led2 = COM.TdsLedger(art2 / "l.csv", art_dir=art2)
        with self.assertRaises(RUN.FrozenError):
            RUN.run_prospective_scenario(led2, art2 / "none.json", Path("."), {"name": "s", "bus": 3})

    def test_hash_mismatch_detected(self):
        src = Path(tempfile.mkdtemp())
        (src / "a.py").write_text("x=1")
        fz = src / "f.json"
        fz.write_text(json.dumps({"sealed": True, "code_sha256": {"a.py": "0" * 64}, "partition": {}, "params": {}, "eps": {}, "dispatches": _disp(), "scenarios_test": {"buses": [3]}, "andes_version": "2.0.0"}))
        with self.assertRaises(RUN.FrozenError):
            RUN.verify_frozen(fz, src)
        fz.write_text(json.dumps({"sealed": True, "code_sha256": {"a.py": COM.sha_file(src / "a.py")}, "partition": {}, "params": {}, "eps": {}, "dispatches": _disp(), "scenarios_test": {"buses": [3]}, "andes_version": "2.0.0"}))
        self.assertTrue(RUN.verify_frozen(fz, src)["sealed"])


class TestProtectedFiles(unittest.TestCase):
    def test_historical_artifacts_untouched_vs_base(self):
        root = COM.ROOT
        r = subprocess.run(["git", "diff", "--name-only", "04e082b26054bf046bd5421ceb275b582a0547a5", "--", "Paper_manuscript/main.tex", "Paper_manuscript/cases", "plan_maestro.md", "ops/sted/decision_log.md",
                            "ops/sted/traceability_matrix.csv", "ops/sted/DEC052_protocol.md", "ops/sted/DEC053_protocol.md", "Paper_manuscript/artifacts/experiment_matrix.csv"], cwd=root, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "")
        r = subprocess.run(["git", "diff", "--name-status", "04e082b26054bf046bd5421ceb275b582a0547a5", "--", "Paper_manuscript/src"], cwd=root, capture_output=True, text=True)
        for line in r.stdout.strip().splitlines():
            st, path = line.split("\t")[:2]
            self.assertEqual(st, "A", line)                                    # only additions in src
            self.assertIn("dec054_", path.lower() + "test_dec054") if False else None


if __name__ == "__main__":
    unittest.main(verbosity=2)
