"""DEC-054 integration-readiness regression tests.  SYNTHETIC/MOCK ONLY: no ANDES import, no PF/TDS, no optimisation on the historical plant.
Run: <venv python> -m unittest -v test_dec054_integration   (from Paper_manuscript/src)"""
import inspect
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

import numpy as np

import dec054_common as COM
import dec054_opf as OPF
import dec054_plant as PL
import dec054_runner as RUN
import dec054_store as ST
import dec054_synth as SYN
import dec054_testkit as K


def ns_arr(v):
    return NS(v=np.asarray(v, float))


def mock_case(shuffle=False, drop_pv=None, p0=None):
    """A mock of the loaded historical case: PV devices (9) and Slack (SG39) with p0/v0 arrays."""
    buses = list(PL.PV_BUS)
    pvals = list(p0 if p0 is not None else np.linspace(4.0, 7.0, 9))
    v0 = list(np.linspace(0.99, 1.01, 9))
    if shuffle:
        order = [4, 0, 8, 2, 6, 1, 7, 3, 5]
        buses, pvals, v0 = [buses[i] for i in order], [pvals[i] for i in order], [v0[i] for i in order]
    if drop_pv is not None:
        i = buses.index(drop_pv)
        buses.pop(i); pvals.pop(i); v0.pop(i)
    return NS(PV=NS(bus=NS(v=np.array(buses)), p0=ns_arr(pvals), v0=ns_arr(v0)), Slack=NS(bus=NS(v=np.array([39])), v0=ns_arr([1.0002])))


def good_system(f=0.0, g=0.0):
    return NS(PFlow=NS(converged=True), TDS=NS(initialized=True, test_ok=True), dae=NS(f=np.full(5, f), g=np.full(7, g), x=np.zeros(5), y=np.ones(7)))


class TestVariablesAndZref(unittest.TestCase):
    def test_exactly_19_variables_in_the_expected_order(self):
        sp = PL.variable_spec()
        self.assertEqual(sp["n"], 19)
        self.assertEqual(len(sp["names"]), 19)
        self.assertEqual(sp["names"][:9], [f"p0_{u}" for u in COM.PV_UNITS])
        self.assertEqual(sp["names"][9:], [f"v0_{u}" for u in COM.UNITS])
        self.assertNotIn("p0_SG39", sp["names"])                       # Slack closes the balance: not a p0 variable
        self.assertIn("v0_SG39", sp["names"])                          # but its voltage set-point is
        self.assertEqual(sp["p0_buses"], [30, 31, 33, 35, 38, 32, 37, 34, 36])

    def test_zref_from_case_is_19_and_ordered_independently_of_device_order(self):
        a, b = PL.z_ref_from_system(mock_case(False)), PL.z_ref_from_system(mock_case(True))
        self.assertEqual(a.shape, (19,))
        np.testing.assert_allclose(a, b)
        np.testing.assert_allclose(a[:9], np.linspace(4.0, 7.0, 9))
        self.assertAlmostEqual(a[9 + COM.UNITS.index("SG39")], 1.0002)  # Slack v0 mapped to SG39

    def test_zref_needs_only_the_system_no_contingency_information(self):
        params = list(inspect.signature(PL.z_ref_from_system).parameters)
        self.assertEqual(params, ["system"])

    def test_structural_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            PL.z_ref_from_system(mock_case(drop_pv=33))
        bad = mock_case()
        bad.PV.p0 = ns_arr(np.r_[np.linspace(4, 7, 8), np.nan])
        with self.assertRaises(ValueError):
            PL.z_ref_from_system(bad)

    def test_hook_requires_19_finite_values(self):
        with self.assertRaises(ValueError):
            PL.hook_for_z(np.ones(18))
        with self.assertRaises(ValueError):
            PL.hook_for_z(np.r_[np.ones(18), np.nan])

    def test_hook_writes_p0_and_v0_to_the_right_devices(self):
        sys = mock_case()
        z = np.r_[np.arange(9) + 10.0, 0.9 + 0.01 * np.arange(10)]
        PL.hook_for_z(z)(sys, None)
        np.testing.assert_allclose(sys.PV.p0.v, z[:9])
        self.assertAlmostEqual(float(sys.Slack.v0.v[0]), z[9 + COM.UNITS.index("SG39")])
        for k, b in enumerate(sys.PV.bus.v):
            self.assertAlmostEqual(float(sys.PV.v0.v[k]), z[9 + COM.UNIT_BUS.index(int(b))])

    def test_adapter_refuses_without_backup(self):
        import unittest.mock as M
        with M.patch.object(PL, "backup_gate", return_value={"verified": False}):
            with self.assertRaises(RuntimeError):
                PL.AndesPlant()


class TestInitValidity(unittest.TestCase):
    def test_valid_system_is_ok(self):
        self.assertTrue(PL.check_initialisation(good_system(1e-12, 1e-10), True)["ok"])

    def test_each_failure_mode_blocks_ok(self):
        base = lambda **kw: good_system(**kw)
        cases = {
            "pf_run_false": (base(), False),
            "pf_not_converged": (NS(PFlow=NS(converged=False), TDS=NS(initialized=True, test_ok=True), dae=base().dae), True),
            "pf_flag_missing": (NS(PFlow=NS(), TDS=NS(initialized=True, test_ok=True), dae=base().dae), True),
            "tds_not_initialised": (NS(PFlow=NS(converged=True), TDS=NS(initialized=False, test_ok=True), dae=base().dae), True),
            "tds_test_failed": (NS(PFlow=NS(converged=True), TDS=NS(initialized=True, test_ok=False), dae=base().dae), True),
            "tds_test_unverifiable": (NS(PFlow=NS(converged=True), TDS=NS(initialized=True), dae=base().dae), True),
            "residual_g": (base(g=1e-6), True),
            "residual_f": (base(f=1e-6), True),
            "nan_residual": (base(g=np.nan), True),
        }
        for name, (sysm, pf_ok) in cases.items():
            rep = PL.check_initialisation(sysm, pf_ok)
            self.assertFalse(rep["ok"], name)
            self.assertTrue(rep["reasons"], name)
        s = good_system()
        s.dae.y = np.array([1.0, np.inf, 1, 1, 1, 1, 1])
        self.assertFalse(PL.check_initialisation(s, True)["ok"])

    def test_adapter_never_reports_ok_on_invalid_initialisation(self):
        plant = object.__new__(PL.AndesPlant)               # bypass __init__ (no ANDES)
        report = {"ok": False, "reasons": ["PFlow.converged is False"]}
        plant._make = lambda z: (_ for _ in ()).throw(PL.InitInvalid(report))
        e = plant.evaluate(np.ones(19))
        self.assertFalse(e["ok"])
        self.assertEqual(e["reason"], "INIT_INVALID")
        self.assertFalse(plant.jump(np.ones(19), OPF.Scenario("s", 3, "P", 0.1))["ok"])
        self.assertFalse(plant.excursion(np.ones(19), OPF.Scenario("s", 3, "P", 0.1))["ok"])

    def test_opf_treats_failed_excursion_as_invalid_margin(self):
        class NoExc(SYN.SyntheticPlant):
            def excursion(self, z, sc):
                return {"ok": False}
        pb = OPF.Problem(NoExc(seed=1), "M3", [OPF.Scenario("b8", 8, "P", 0.58564)])
        up, dn, info = pb.margins_d(pb.plant.z_ref, 0)
        self.assertFalse(info["ok"])
        self.assertLess(float(up.max()), -100.0)


class TestCacheInvalidation(unittest.TestCase):
    def setUp(self):
        self.plant = SYN.SyntheticPlant(seed=1)
        self.sc = [OPF.Scenario("b8", 8, "P", 0.58564)]
        self.pb = OPF.Problem(self.plant, "M2", self.sc, cfg=dict(COM.PROPOSED))
        self.z = self.plant.z_ref.copy()

    def test_new_cut_modifies_the_constraint_without_manual_cache_clearing(self):
        base = self.pb.margins_d(self.z, 0)[0].copy()              # warms the cache
        self.assertEqual(len(self.pb._cache), 1)
        self.pb.add_dynamic_cut(0, 1, "P+", 0.05, self.z, np.full(19, 0.02))
        after = self.pb.margins_d(self.z, 0)[0]
        self.assertAlmostEqual(after[1], base[1] - 0.05, places=12)
        np.testing.assert_allclose(np.delete(after, 1), np.delete(base, 1))       # only the targeted constraint
        W = {(0, 1, "P+")}
        c = self.pb.constraints(self.z, W)
        self.assertAlmostEqual(float(c[-1]), float(after[1]), places=12)           # the NLP constraint reflects the cut

    def test_direct_mutation_of_dyn_cuts_also_invalidates(self):
        base = self.pb.margins_d(self.z, 0)[1].copy()
        self.pb.dyn_cuts.append({"d": 0, "i": 2, "cls": "P-", "delta": 0.03, "z_c": self.z.copy(), "r": np.full(19, 0.02)})
        after = self.pb.margins_d(self.z, 0)[1]
        self.assertAlmostEqual(after[2], base[2] - 0.03, places=12)

    def test_cut_outside_trust_region_has_no_effect(self):
        base = self.pb.margins_d(self.z, 0)[0].copy()
        z2 = self.z.copy(); z2[0] += 0.5
        self.pb.add_dynamic_cut(0, 1, "P+", 0.05, self.z, np.full(19, 0.02))
        far = self.pb.margins_d(z2, 0)[0]
        ref = OPF.Problem(self.plant, "M2", self.sc, cfg=dict(COM.PROPOSED)).margins_d(z2, 0)[0]
        np.testing.assert_allclose(far, ref)

    def test_eps_change_invalidates(self):
        a = self.pb.margins_d(self.z, 0)[0].copy()
        self.pb.eps_J = np.full(10, 0.01)
        b = self.pb.margins_d(self.z, 0)[0]
        np.testing.assert_allclose(b, a - 0.01)


def _art(verified: bool):
    return K.make_art(verified)


def _frozen(src, disp):
    (src / "a.py").write_text("x=1")
    fz = src / "design_frozen.json"
    RUN.write_frozen(fz, src, ["a.py"], {"DESIGN": [8]}, {}, {}, disp, {"buses": [3, 29]}, "2.0.0")
    return fz


def disp_ok():
    return {m: RUN.make_dispatch_entry(np.full(19, 1.0 + 0.01 * i)) for i, m in enumerate(RUN.METHODS)}


def fake_series():
    t = np.arange(0, 10, 0.5)
    return {"t": t, "P": np.ones((len(t), 10)), "Q": np.zeros((len(t), 10)), "V": np.ones((len(t), 39))}


class TestSingleDispatchPerMethod(unittest.TestCase):
    def test_per_scenario_dispatches_are_rejected(self):
        bad = disp_ok()
        bad["M3"] = {"z": bad["M3"]["z"], "z_sha256": bad["M3"]["z_sha256"], "bus3": {"z": [0.0] * 19}}
        with self.assertRaises(RUN.FrozenError):
            RUN.validate_dispatches(bad)
        bad2 = disp_ok()
        bad2["M0"] = {"3": bad2["M0"], "29": bad2["M0"]}                      # dispatch keyed by scenario
        with self.assertRaises(RUN.FrozenError):
            RUN.validate_dispatches(bad2)

    def test_missing_wrong_size_or_inconsistent_hash_rejected(self):
        d = disp_ok(); del d["M2"]
        with self.assertRaises(RUN.FrozenError):
            RUN.validate_dispatches(d)
        d = disp_ok(); d["M1"]["z"] = d["M1"]["z"][:18]
        with self.assertRaises(RUN.FrozenError):
            RUN.validate_dispatches(d)
        d = disp_ok(); d["M1"]["z"][0] += 1e-3
        with self.assertRaises(RUN.FrozenError):
            RUN.validate_dispatches(d)

    def test_differences_between_scenarios_are_rejected(self):
        d = disp_ok()
        z = np.asarray(d["M3"]["z"])
        plan = [{"method": "M3", "scenario": "s1", "z": z}, {"method": "M3", "scenario": "s2", "z": z + 1e-9}]
        with self.assertRaises(RUN.FrozenError):
            RUN.assert_single_dispatch(plan, d)
        RUN.assert_single_dispatch([{"method": "M3", "scenario": "s1", "z": z}, {"method": "M3", "scenario": "s2", "z": z.copy()}], d)

    def test_write_frozen_refuses_invalid_dispatches(self):
        src = Path(tempfile.mkdtemp())
        (src / "a.py").write_text("x=1")
        bad = disp_ok(); bad["M0"]["per_scenario"] = {}
        with self.assertRaises(RUN.FrozenError):
            RUN.write_frozen(src / "f.json", src, ["a.py"], {}, {}, {}, bad, {"buses": [3]}, "2.0.0")
        self.assertFalse((src / "f.json").exists())


class TestStore(unittest.TestCase):
    def test_exclusive_and_hashes(self):
        root = Path(tempfile.mkdtemp())
        h = ST.save_run(root, "r1", status="TDS_SAFE_OBSERVED", tds_id="TDS01", series=fake_series(), metrics={"a": np.arange(3)}, config={"z": np.ones(19)}, diag={"d": 1}, ledger_row={"x": 1})
        for name in ("series.npz", "metrics.json", "config.json", "diag.json", "status.json", "ledger_row.json"):
            self.assertIn(name, h)
        self.assertTrue((root / "r1" / "hashes.json").exists())
        self.assertTrue(ST.verify_run(root, "r1")["ok"])
        with self.assertRaises(FileExistsError):
            ST.save_run(root, "r1", status="TDS_SAFE_OBSERVED")                  # no overwrite
        (root / "r1" / "metrics.json").write_text("{}")                          # tampering is detected
        self.assertFalse(ST.verify_run(root, "r1")["ok"])

    def test_failure_keeps_evidence(self):
        root = Path(tempfile.mkdtemp())
        try:
            raise RuntimeError("diverged at 5.2 s")
        except RuntimeError as ex:
            ST.save_run(root, "rf", status="TDS_NUMERICAL_FAILURE", tds_id="TDS02", error=ex, diag={"t_end_s": 5.2}, config={"z": [0] * 19})
        st = json.loads((root / "rf" / "status.json").read_text())
        self.assertEqual(st["status"], "TDS_NUMERICAL_FAILURE")
        self.assertIn("diverged at 5.2 s", st["error"])
        self.assertTrue((root / "rf" / "series_missing.json").exists())
        self.assertTrue(ST.verify_run(root, "rf")["ok"])


class TestRunnerPersistence(unittest.TestCase):
    def setUp(self):
        K.install_stub(self)
        self.art = _art(True)
        self.src = Path(tempfile.mkdtemp())
        self.disp = disp_ok()
        self.fz = _frozen(self.src, self.disp)
        self.ledger = COM.TdsLedger(self.art / "ledger.csv", art_dir=self.art)
        self.store = Path(tempfile.mkdtemp())
        self.sc = {"name": "bus3_a1", "bus": 3, "kind": "P", "amp": 0.58}

    def test_blocked_gate_refuses_before_anything(self):
        art = _art(False)
        led = COM.TdsLedger(art / "l.csv", art_dir=art)
        with self.assertRaises(COM.GateError):
            RUN.run_prospective_scenario(led, self.fz, self.src, self.sc, dry_run=False, executor=lambda z, s: 1 / 0, store_root=self.store)
        self.assertEqual(led.used(), 0)
        self.assertEqual(list(self.store.iterdir()), [])

    def test_each_method_uses_its_single_frozen_dispatch_and_evidence_is_saved(self):
        seen = []

        def ex(z, sc):
            seen.append(np.asarray(z).copy())
            return {"status": "TDS_SAFE_OBSERVED", "series": fake_series(), "metrics": {"n": 0}, "diag": {"tds_ok": True}, "notes": "mock"}
        out = RUN.run_prospective_scenario(self.ledger, self.fz, self.src, self.sc, dry_run=False, executor=ex, store_root=self.store)
        self.assertEqual(set(out), set(RUN.METHODS))
        for m, z in zip(RUN.METHODS, seen):
            np.testing.assert_array_equal(z, np.asarray(self.disp[m]["z"]))
        self.assertEqual(self.ledger.used(), 4)
        for m in RUN.METHODS:
            rid = f"P3-C_bus3_a1_{m}"
            self.assertTrue(ST.verify_run(self.store, rid)["ok"])
            cfg = json.loads((self.store / rid / "config.json").read_text())
            self.assertEqual(cfg["z_sha256"], self.disp[m]["z_sha256"])
            self.assertEqual(cfg["method"], m)
        comp = [r for r in self.ledger.rows if r["status"] == "TDS_SAFE_OBSERVED"]
        self.assertEqual(len(comp), 4)

    def test_failure_is_persisted_and_budgeted(self):
        def ex(z, sc):
            raise RuntimeError("solver blew up")
        out = RUN.run_prospective_scenario(self.ledger, self.fz, self.src, self.sc, dry_run=False, executor=ex, store_root=self.store)
        self.assertTrue(all(v["status"] == "TDS_NUMERICAL_FAILURE" for v in out.values()))
        self.assertEqual(self.ledger.used(), 4)                                  # failures keep their budget
        for m in RUN.METHODS:
            st = json.loads((self.store / f"P3-C_bus3_a1_{m}" / "status.json").read_text())
            self.assertIn("solver blew up", st["error"])

    def test_invalid_executor_status_is_a_failure(self):
        out = RUN.run_prospective_scenario(self.ledger, self.fz, self.src, self.sc, methods=("M0",), dry_run=False, executor=lambda z, s: {"status": "WEIRD"}, store_root=self.store)
        self.assertEqual(out["M0"]["status"], "TDS_NUMERICAL_FAILURE")

    def test_rerun_of_same_scenario_is_refused_before_execution(self):
        ok = lambda z, s: {"status": "TDS_SAFE_OBSERVED", "series": fake_series()}
        RUN.run_prospective_scenario(self.ledger, self.fz, self.src, self.sc, dry_run=False, executor=ok, store_root=self.store)
        calls = []
        with self.assertRaises(COM.GateError):
            RUN.run_prospective_scenario(self.ledger, self.fz, self.src, self.sc, dry_run=False, executor=lambda z, s: calls.append(1), store_root=self.store)
        self.assertEqual(calls, [])
        self.assertEqual(self.ledger.used(), 4)

    def test_storage_collision_records_the_run_and_raises(self):
        (self.store / "P3-C_bus3_a1_M0").mkdir()                                   # pre-existing evidence directory
        with self.assertRaises(FileExistsError):
            RUN.run_prospective_scenario(self.ledger, self.fz, self.src, self.sc, methods=("M0",), dry_run=False,
                                         executor=lambda z, s: {"status": "TDS_SAFE_OBSERVED", "series": fake_series()}, store_root=self.store)
        last = self.ledger.rows[-1]
        self.assertEqual(last["status"], "TDS_SAFE_OBSERVED")
        self.assertIn("EVIDENCE_NOT_SAVED", last["notes"])

    def test_scenario_outside_frozen_test_list_refused(self):
        with self.assertRaises(RUN.FrozenError):
            RUN.run_prospective_scenario(self.ledger, self.fz, self.src, {"name": "x", "bus": 8, "kind": "P", "amp": 0.1}, dry_run=True)

    def test_dry_run_reserves_nothing(self):
        r = RUN.run_prospective_scenario(self.ledger, self.fz, self.src, self.sc, dry_run=True)
        self.assertEqual(len(r["plan"]), 4)
        self.assertEqual(self.ledger.used(), 0)


class TestRealRepositoryStateUnchanged(unittest.TestCase):
    def test_gate_never_independent_and_ledger_has_header(self):
        self.assertFalse(COM.backup_gate()["independent"])
        lines = (COM.ART / "IEEE39_DEC054_tds_ledger.csv").read_text().strip().splitlines()
        self.assertTrue(lines[0].startswith("tds_id,block"))
        self.assertLessEqual(sum(1 for l in lines[1:] if ",REQUESTED," in l), 48)

    def test_runs_dir_is_inside_the_paper_folder(self):
        self.assertIn("Paper_manuscript", str(COM.RUNS_DIR).replace("\\", "/"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
