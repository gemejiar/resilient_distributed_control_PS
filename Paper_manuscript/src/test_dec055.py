"""DEC-055 L0 unit tests (no ANDES, no TDS).  Run: <venv python> -m unittest -v test_dec055"""
from __future__ import annotations

import math
import shutil
import tempfile
import types
import unittest
from pathlib import Path

import numpy as np

import dec054_common as C54
import dec055_common as C


def lim10():
    return {"pmax": np.full(10, 5.0), "pmin": np.zeros(10), "qmax": np.full(10, 2.0), "qmin": np.full(10, -2.0), "smax": np.full(10, 6.0)}


def jump_ok(P=3.0, Q=0.5, V=1.0, res=1e-12, sv=1e-3):
    return {"ok": True, "residual": res, "gy_min_sv": sv, "P_plus": np.full(10, P), "Q_plus": np.full(10, Q), "V_plus": np.full(39, V)}


class TestPartitionsAndCells(unittest.TestCase):
    def test_disjoint_partitions(self):
        D, T, X = set(C.DESIGN), set(C.TUNE), set(C.TEST)
        self.assertFalse(D & T or D & X or T & X)
        self.assertFalse(X & set(C.SEEN_NOT_TEST))
        self.assertFalse(X & (set(C54.DESIGN) | set(C54.TUNE) | set(C54.TEST)))

    def test_cell_counts(self):
        rows = C.enumerate_cells()
        self.assertEqual(len(rows), 3 * (4 * 3 + 4 * 2 + 3 * 3 * 4))
        self.assertEqual(len({r["cell_id"] for r in rows}), len(rows))
        test = [r for r in rows if r["partition"] == "TEST"]
        self.assertEqual(sum(r["schedule"] == "SCHEDULED" for r in test), 54)
        self.assertEqual(sum(r["schedule"] == "DEFERRED" for r in test), 54)

    def test_amplitudes(self):
        self.assertAlmostEqual(C.oc_amp("S1"), 0.29282)
        self.assertAlmostEqual(C.oc_amp("S3"), 0.87846)


class TestTC(unittest.TestCase):
    def test_capacity(self):
        self.assertTrue(C.capacity_necessary(74.9, 65.3))
        self.assertFalse(C.capacity_necessary(60.0, 65.3))

    def test_classes(self):
        good = {"success": True, "eq_residual": 1e-12, "ineq_min": 0.0, "andes_verified": True}
        self.assertEqual(C.classify_tc(True, good), "AC_FEASIBLE")
        self.assertEqual(C.classify_tc(False, good), "PROVEN_INFEASIBLE")
        self.assertEqual(C.classify_tc(True, dict(good, andes_verified=False)), "AC_UNDETERMINED")
        self.assertEqual(C.classify_tc(True, dict(good, success=False)), "AC_UNDETERMINED")      # solver failure is not a proof
        self.assertEqual(C.classify_tc(True, dict(good, eq_residual=1e-6)), "AC_UNDETERMINED")
        self.assertEqual(C.classify_tc(True, None), "AC_UNDETERMINED")


class TestTA(unittest.TestCase):
    def test_admissible(self):
        self.assertEqual(C.classify_ta(jump_ok(), lim10())["label"], "ADMISSIBLE")

    def test_not_admissible_lists_limit(self):
        r = C.classify_ta(jump_ok(P=5.01), lim10())
        self.assertEqual(r["label"], "NOT_ADMISSIBLE")
        self.assertIn("Pmax", r["violated"])
        r = C.classify_ta(jump_ok(V=1.051), lim10())
        self.assertEqual(r["violated"], ["Vmax"])

    def test_unverified(self):
        self.assertEqual(C.classify_ta(jump_ok(res=1e-6), lim10())["label"], "UNVERIFIED")
        self.assertEqual(C.classify_ta(jump_ok(sv=1e-12), lim10())["label"], "UNVERIFIED")
        self.assertEqual(C.classify_ta({"ok": False}, lim10())["label"], "UNVERIFIED")
        self.assertEqual(C.classify_ta(None, lim10())["label"], "UNVERIFIED")

    def test_s3_rule(self):
        self.assertEqual(C.classify_s3("AC_FEASIBLE", "FEASIBLE_PREDICTED", "ADMISSIBLE"), "S3_PROMOTED_CONFIRMATORY")
        for args in (("AC_UNDETERMINED", "FEASIBLE_PREDICTED", "ADMISSIBLE"), ("AC_FEASIBLE", "SOLVER_FAILED", "ADMISSIBLE"), ("AC_FEASIBLE", "FEASIBLE_PREDICTED", "NOT_ADMISSIBLE")):
            self.assertEqual(C.classify_s3(*args), "STRESS_EXPLORATORY")

    def test_confirmatory(self):
        base = {"partition": "TEST", "tc_class": "AC_FEASIBLE", "severity": "S2"}
        self.assertTrue(C.confirmatory(base))
        self.assertFalse(C.confirmatory(dict(base, severity="S3", s3_status="STRESS_EXPLORATORY")))
        self.assertTrue(C.confirmatory(dict(base, severity="S3", s3_status="S3_PROMOTED_CONFIRMATORY")))
        self.assertFalse(C.confirmatory(dict(base, tc_class="AC_UNDETERMINED")))
        self.assertFalse(C.confirmatory(dict(base, exclusion_reason="x")))
        self.assertFalse(C.confirmatory(dict(base, partition="TUNE")))


class TestVerdicts(unittest.TestCase):
    def rows(self, statuses):
        return [{"cell_id": f"c{i}", "strategy": "M3B2", "confirmatory": True, "tds_status": s} for i, s in enumerate(statuses)]

    def test_single_violation_refutes(self):
        v = C.safety_verdict(self.rows(["TDS_SAFE_OBSERVED"] * 17 + ["TDS_PHYSICAL_VIOLATION"]))
        self.assertEqual(v["verdict"], "SAFETY_CLAIM_REFUTED")
        self.assertEqual(v["refuting_cells"], ["c17"])

    def test_incomplete_and_pass(self):
        self.assertEqual(C.safety_verdict(self.rows(["TDS_SAFE_OBSERVED", None]))["verdict"], "INCOMPLETE")
        self.assertEqual(C.safety_verdict(self.rows(["TDS_SAFE_OBSERVED", "TDS_NUMERICAL_FAILURE"]))["verdict"], "INCOMPLETE")
        self.assertEqual(C.safety_verdict(self.rows(["TDS_SAFE_OBSERVED"] * 3))["verdict"], "NOT_REFUTED_IN_TESTED_CELLS")

    def test_sign_test(self):
        r = C.cluster_sign_test({i: 1 for i in range(9)})
        self.assertAlmostEqual(r["p_one_sided"], 2 ** -9)
        self.assertTrue(r["significant"])
        r = C.cluster_sign_test({0: 1, 1: -1, 2: 0, 3: 1})
        self.assertEqual(r["n_nonzero"], 3)
        self.assertAlmostEqual(r["p_one_sided"], 0.5)
        self.assertFalse(C.cluster_sign_test({})["significant"])


class TestFrequency(unittest.TestCase):
    def test_coi_weights(self):
        om = np.array([[1.0, 1.0], [1.01, 0.99]])
        f = C.f_coi_hz(om, M=[100.0, 1.0], Sn=[1.0, 1.0])
        self.assertAlmostEqual(f[0], 60.0)
        self.assertAlmostEqual(f[1], 60.0 * (1.01 * 100 + 0.99) / 101)

    def test_mean_busfreq_is_unweighted(self):
        self.assertTrue(np.allclose(C.mean_busfreq_hz(np.array([[59.0, 61.0, 60.0]])), [60.0]))

    def test_rocof_window(self):
        t = np.arange(0, 10, 2 ** -8)
        f = 60.0 - 0.2 * np.clip(t - 5.0, 0, None)
        self.assertAlmostEqual(C.rocof_window(t, f), -0.2, places=6)


class TestJumpVsSample(unittest.TestCase):
    def setUp(self):
        self.t = np.array([4.99609375, 5.0, 5.00390625])
        self.P = np.array([[1.0, 2.0], [1.0, 2.0], [1.3, 2.1]])

    def test_acceptance_without_attribution(self):
        r = C.jump_vs_first_sample(self.t, self.P, [1.299, 2.1])
        self.assertEqual(r["t_sample"], 5.00390625)
        self.assertTrue(r["accepted"])
        self.assertEqual(r["attribution"], "NOT_ATTEMPTED")

    def test_attribution_rules(self):
        r = C.jump_vs_first_sample(self.t, self.P, [1.296, 2.1], one_step_P=[1.3 + 5e-7, 2.1])
        self.assertEqual(r["attribution"], "ONE_INTEGRATOR_STEP")
        r = C.jump_vs_first_sample(self.t, self.P, [1.296, 2.1], one_step_P=[1.297, 2.1])
        self.assertEqual(r["attribution"], "UNEXPLAINED")
        self.assertFalse(C.jump_vs_first_sample(self.t, self.P, [1.29, 2.1])["accepted"])


class TestOCCases(unittest.TestCase):
    def test_scale_rule(self):
        import dec055_oc as O
        out = O.scale_rule([6.46, 4.0], [6.5, 10.0], 1.1)
        self.assertAlmostEqual(out[0], 6.5 - C.PV_CAP_BACKOFF_PU)
        self.assertAlmostEqual(out[1], 4.4)

    def test_build_case_preserves_base_and_pf(self):
        import pandas as pd

        import dec055_oc as O
        tmp = Path(tempfile.mkdtemp())
        try:
            src = tmp / "base.xlsx"
            shutil.copy(C.BASE_CASE, src)
            h = C54.sha_file(src)
            rec = O.build_case("OC3", src=src, dst=tmp / "oc3.xlsx")
            self.assertEqual(C54.sha_file(src), h)
            with self.assertRaises(FileExistsError):
                O.build_case("OC3", src=src, dst=tmp / "oc3.xlsx")
            a, b = pd.read_excel(src, sheet_name=None), pd.read_excel(tmp / "oc3.xlsx", sheet_name=None)
            self.assertTrue(np.allclose(b["PQ"].p0, 1.1 * a["PQ"].p0) and np.allclose(b["PQ"].q0, 1.1 * a["PQ"].q0))
            for s in a:
                if s not in ("PQ", "PV"):
                    self.assertTrue(a[s].fillna(-999).equals(b[s].fillna(-999)), s)
            self.assertTrue(a["PV"].drop(columns="p0").fillna(-999).equals(b["PV"].drop(columns="p0").fillna(-999)))
            self.assertTrue(np.all(b["PV"].p0 <= b["PV"].pmax - C.PV_CAP_BACKOFF_PU + 1e-12))
            self.assertEqual(rec["source_sha256"], h)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestLedger(unittest.TestCase):
    def test_budget_and_no_retry(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            L = C.Ledger(tmp / "l.csv")
            ids = [L.request("L1", "s", "m", f"r{i}", "p") for i in range(C.BUDGET["L1"])]
            self.assertEqual(ids[0], "D55T001")
            with self.assertRaises(C54.GateError):
                L.request("L1", "s", "m", "r9", "p")
            with self.assertRaises(C54.GateError):
                L.request("L2", "s", "m", "r0", "p")            # same run_id: no silent retry
            with self.assertRaises(C54.GateError):
                L.request("LX", "s", "m", "rx", "p")
            L.complete(ids[0], "TDS_SAFE_OBSERVED")
            self.assertEqual(C.Ledger(tmp / "l.csv").used(), C.BUDGET["L1"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestCoiRecord(unittest.TestCase):
    def test_mock_system(self):
        import dec055_runner as R
        x = np.array([[0.0, 1.0, 0.0, 1.0], [0.0, 1.002, 0.0, 0.998]])
        ns = types.SimpleNamespace
        sysm = ns(dae=ns(ts=ns(x=x)), GENROU=ns(omega=ns(a=np.array([1, 3])), M=ns(v=np.array([10.0, 10.0])), Sn=ns(v=np.array([100.0, 100.0])), fn=ns(v=np.array([60.0]))))
        r = R.coi_record(sysm)
        self.assertTrue(np.allclose(r["f_coi_hz"], [60.0, 60.0]))
        self.assertEqual(r["sg_omega_pu"].shape, (2, 2))


if __name__ == "__main__":
    unittest.main()
