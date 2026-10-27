"""DEC-054 test support (synthetic only): builds a self-consistent independent-backup evidence set in temporary folders so that the gate logic can be exercised
without a second physical device.  The device check is replaced by a stub that places registered destinations on 'device 2'."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np

import dec054_common as COM

_DEST_ROOTS: list = []


def _stub_dev_of(p) -> int:
    p = str(Path(p).resolve())
    return 2 if any(p.startswith(str(Path(d).resolve())) for d in _DEST_ROOTS) else 1


def install_stub(testcase) -> None:
    old = COM._default_dev_of
    COM._default_dev_of = _stub_dev_of
    testcase.addCleanup(lambda: setattr(COM, "_default_dev_of", old))


def make_art(verified: bool, tamper: str | None = None, same_device: bool = False, kind: str = "other_physical_drive", authorized_by: str = "test authorisation") -> Path:
    """Returns an artifacts-like directory.  verified=False: no evidence file.  verified=True: complete evidence (optionally tampered)."""
    art = Path(tempfile.mkdtemp())
    root = Path(tempfile.mkdtemp())
    src, dest = root / "src", root / "dest"
    (src / "files").mkdir(parents=True)
    (dest / "files" / "Paper_manuscript" / "artifacts").mkdir(parents=True)
    rels = {}
    for i, nm in enumerate(("a.npz", "b.npz")):
        p = dest / "files" / "Paper_manuscript" / "artifacts" / nm
        np.savez_compressed(p, x=np.arange(10 + i))
        rels[f"Paper_manuscript/artifacts/{nm}"] = {"bytes": p.stat().st_size, "sha256": COM.sha_file(p)}
    log = dest / "files" / "Paper_manuscript" / "artifacts" / "c.log"
    log.write_text("log")
    rels["Paper_manuscript/artifacts/c.log"] = {"bytes": 3, "sha256": COM.sha_file(log)}
    bundle = dest / "rdc_all_refs_dec054.bundle"
    bundle.write_bytes(b"fake-bundle-bytes")
    (art / "IEEE39_DEC054_baseline_manifest.json").write_text(json.dumps({"ignored_local_files": rels}))
    if not verified:
        return art
    ev = {"schema_version": 1, "destination_kind": kind, "authorized_by": authorized_by, "destination_root": str(dest), "source_root": str(src),
          "restore_test": {"npz": [{"path": r, "readable": True, "sha256_restored": m["sha256"], "sha256_expected": m["sha256"]} for r, m in rels.items() if r.endswith(".npz")],
                           "bundle": {"sha256": COM.sha_file(bundle), "verify_rc": 0, "clone_rc": 0, "clone_head_ok": True}}}
    if tamper == "bad_hash":
        (dest / "files" / "Paper_manuscript" / "artifacts" / "c.log").write_text("changed")
    elif tamper == "missing_file":
        (dest / "files" / "Paper_manuscript" / "artifacts" / "c.log").unlink()
    elif tamper == "one_npz":
        ev["restore_test"]["npz"] = ev["restore_test"]["npz"][:1]
    elif tamper == "bundle_hash":
        ev["restore_test"]["bundle"]["sha256"] = "0" * 64
    elif tamper == "bundle_clone_failed":
        ev["restore_test"]["bundle"]["clone_head_ok"] = False
    elif tamper == "no_auth":
        ev["authorized_by"] = "  "
    elif tamper == "bad_kind":
        ev["destination_kind"] = "same_disk_copy"
    elif tamper == "npz_mismatch":
        ev["restore_test"]["npz"][0]["sha256_restored"] = "1" * 64
    elif tamper == "overlap":
        ev["destination_root"] = str(src / "inner")
        (src / "inner" / "files").mkdir(parents=True)
    (art / COM.INDEP_EVIDENCE).write_text(json.dumps(ev))
    if not same_device:
        _DEST_ROOTS.append(ev["destination_root"] if tamper != "overlap" else str(dest))
    return art
