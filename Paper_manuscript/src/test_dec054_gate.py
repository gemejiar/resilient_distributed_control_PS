"""DEC-054 G0 tests: the independent-backup gate validates NEW evidence (recomputed hashes, device independence, restore tests); a boolean cannot unlock it.
SYNTHETIC/TEMP FOLDERS ONLY.  Run: <venv python> -m unittest -v test_dec054_gate"""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import numpy as np

import dec054_common as COM
import dec054_independent_backup as IB
import dec054_testkit as K


class TestGateFromEvidence(unittest.TestCase):
    def setUp(self):
        K.install_stub(self)

    def test_real_repository_is_blocked_and_says_why(self):
        g = COM.backup_gate()
        self.assertFalse(g["verified"])
        self.assertEqual(g["gate0"], "STOP_BACKUP_NOT_VERIFIED")
        self.assertTrue(any("does not exist" in r for r in g["reasons"]))

    def test_old_p0_booleans_cannot_unlock(self):
        art = K.make_art(False)
        (art / "IEEE39_DEC054_backup_manifest.json").write_text(json.dumps({"status": "BACKUP_VERIFIED", "gate0": "PASS"}))
        (art / "IEEE39_DEC054_preservation_test.json").write_text(json.dumps({"independent_backup_verified": True}))
        self.assertFalse(COM.backup_gate(art)["verified"])

    def test_complete_evidence_passes(self):
        g = COM.backup_gate(K.make_art(True))
        self.assertTrue(g["verified"], g["reasons"])
        self.assertEqual((g["status"], g["gate0"]), ("BACKUP_VERIFIED", "PASS"))

    def test_every_tamper_is_detected(self):
        for t in ("bad_hash", "missing_file", "one_npz", "bundle_hash", "bundle_clone_failed", "no_auth", "bad_kind", "npz_mismatch", "overlap"):
            g = COM.backup_gate(K.make_art(True, tamper=t))
            self.assertFalse(g["verified"], t)
            self.assertTrue(g["reasons"], t)

    def test_same_device_destination_is_not_independent(self):
        art = K.make_art(True, same_device=True)
        g = COM.backup_gate(art)
        self.assertFalse(g["verified"])
        self.assertTrue(any("same device" in r for r in g["reasons"]))

    def test_real_device_check_rejects_temp_copy_on_the_same_disk(self):
        K_old = COM._default_dev_of
        art = K.make_art(True)                         # destination registered as 'device 2' only under the stub
        COM._default_dev_of = lambda p: __import__("os").stat(p).st_dev      # real check (all temp folders share the device)
        try:
            g = COM.backup_gate(art)
        finally:
            COM._default_dev_of = K_old
        self.assertFalse(g["verified"])

    def test_editing_a_copied_file_after_verification_blocks_again(self):
        art = K.make_art(True)
        self.assertTrue(COM.backup_gate(art)["verified"])
        ev = json.loads((art / COM.INDEP_EVIDENCE).read_text())
        (Path(ev["destination_root"]) / "files" / "Paper_manuscript" / "artifacts" / "c.log").write_text("bit rot")
        self.assertFalse(COM.backup_gate(art)["verified"])                  # re-validated on every call

    def test_malformed_evidence_is_never_a_pass(self):
        art = K.make_art(False)
        (art / COM.INDEP_EVIDENCE).write_text("{not json")
        self.assertFalse(COM.backup_gate(art)["verified"])
        (art / COM.INDEP_EVIDENCE).write_text("{}")
        self.assertFalse(COM.backup_gate(art)["verified"])

    def test_ledger_follows_the_new_gate(self):
        art = K.make_art(False)
        led = COM.TdsLedger(art / "l.csv", art_dir=art)
        with self.assertRaises(COM.GateError):
            led.request("P3-A", "s", "M3", "r1", "audit")
        art2 = K.make_art(True)
        led2 = COM.TdsLedger(art2 / "l.csv", art_dir=art2)
        self.assertEqual(led2.request("P3-A", "s", "M3", "r1", "audit"), "TDS01")


def _git(cwd, *a):
    return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *a], cwd=str(cwd), capture_output=True, text=True)


def make_source(tmp: Path):
    """A miniature project-folder preservation: bundle of a tiny repo + files/ + baseline manifest."""
    repo = tmp / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    (repo / "f.txt").write_text("x")
    _git(repo, "add", "f.txt")
    _git(repo, "commit", "-q", "-m", "c1")
    _git(repo, "branch", "review/dec053-methodology-closure")
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    src = tmp / "preservation"
    (src / "files" / "Paper_manuscript" / "artifacts").mkdir(parents=True)
    assert _git(repo, "bundle", "create", str(src / "rdc_all_refs_dec054.bundle"), "--all").returncode == 0
    rels = {}
    for i, nm in enumerate(("a.npz", "b.npz")):
        p = src / "files" / "Paper_manuscript" / "artifacts" / nm
        np.savez_compressed(p, x=np.arange(20 + i))
        rels[f"Paper_manuscript/artifacts/{nm}"] = {"bytes": p.stat().st_size, "sha256": COM.sha_file(p)}
    art = tmp / "art"
    art.mkdir()
    (art / "IEEE39_DEC054_baseline_manifest.json").write_text(json.dumps({"ignored_local_files": rels}))
    return src, art, head, rels


class TestIndependentBackupCreation(unittest.TestCase):
    def setUp(self):
        K.install_stub(self)
        self.tmp = Path(tempfile.mkdtemp())
        self.src, self.art, self.head, self.rels = make_source(self.tmp)
        self.dest = self.tmp / "external" / "DEC054"
        K._DEST_ROOTS.append(str(self.tmp / "external"))

    def test_creates_evidence_and_gate_passes(self):
        ev = IB.create_independent_backup(self.dest, "other_physical_drive", "investigator authorised drive X", source_copy=self.src, art_dir=self.art, head_expected=self.head)
        self.assertEqual(ev["files_bad"], [])
        self.assertTrue(ev["restore_test"]["bundle"]["clone_head_ok"])
        self.assertEqual(len(ev["restore_test"]["npz"]), 2)
        g = COM.backup_gate(self.art)
        self.assertTrue(g["verified"], g["reasons"])

    def test_never_overwrites(self):
        IB.create_independent_backup(self.dest, "other_physical_drive", "auth", source_copy=self.src, art_dir=self.art, head_expected=self.head)
        with self.assertRaises(FileExistsError):
            IB.create_independent_backup(self.dest, "other_physical_drive", "auth", source_copy=self.src, art_dir=self.art, head_expected=self.head)
        d2 = self.tmp / "external" / "DEC054b"
        with self.assertRaises(FileExistsError):
            IB.create_independent_backup(d2, "other_physical_drive", "auth", source_copy=self.src, art_dir=self.art, head_expected=self.head)   # evidence file exists

    def test_same_device_refused_with_real_check(self):
        import os
        with self.assertRaises(RuntimeError):
            IB.create_independent_backup(self.tmp / "same" / "d", "other_physical_drive", "auth", source_copy=self.src, art_dir=self.art, dev_of=lambda p: os.stat(p).st_dev, head_expected=self.head)
        self.assertFalse((self.art / COM.INDEP_EVIDENCE).exists())

    def test_missing_authorisation_or_bad_kind_refused(self):
        with self.assertRaises(ValueError):
            IB.create_independent_backup(self.dest, "other_physical_drive", "  ", source_copy=self.src, art_dir=self.art)
        with self.assertRaises(ValueError):
            IB.create_independent_backup(self.dest, "same_disk_copy", "auth", source_copy=self.src, art_dir=self.art)

    def test_corrupted_source_writes_no_evidence(self):
        (self.src / "files" / "Paper_manuscript" / "artifacts" / "a.npz").write_bytes(b"corrupted")
        with self.assertRaises(RuntimeError):
            IB.create_independent_backup(self.dest, "other_physical_drive", "auth", source_copy=self.src, art_dir=self.art, head_expected=self.head)
        self.assertFalse((self.art / COM.INDEP_EVIDENCE).exists())

    def test_wrong_expected_head_makes_gate_fail(self):
        IB.create_independent_backup(self.dest, "other_physical_drive", "auth", source_copy=self.src, art_dir=self.art, head_expected="0" * 40)
        self.assertFalse(COM.backup_gate(self.art)["verified"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
