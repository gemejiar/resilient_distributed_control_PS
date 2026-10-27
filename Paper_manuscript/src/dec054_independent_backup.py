"""DEC-054 G0: create and verify an INDEPENDENT backup, and write the NEW evidence file consumed by dec054_common.backup_gate().

Usage (after the investigator provides a destination on another physical drive, or a remote location mounted/read back as a local path):
    python dec054_independent_backup.py <destination_root> <kind: other_physical_drive|authorized_remote_readback> "<authorisation text>"

It copies the project-folder preservation (bundle + files/ + manifest) to <destination_root> (which must not exist), recomputes the SHA-256 of every file
from the DESTINATION, restores >= 2 NPZ and the Git bundle in a temporary folder, and writes IEEE39_DEC054_independent_backup_verification.json
exclusively (the historical P0 manifests are never touched).  It refuses a destination on the same device as the source."""
from __future__ import annotations

import datetime as _dt
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

import dec054_common as COM

SOURCE_COPY = Path(r"c:/onedrive/OneDrive - Universidad del Valle/05_Univalle_Investigacion/02_Publicaciones/En_Preparacion/Proyectos_Latex/Resilient_distributed_control_PS/Paper_manuscript/backups/DEC054_P0_preservation")
BASE_DEC053_HEAD = "04e082b26054bf046bd5421ceb275b582a0547a5"


def create_independent_backup(dest_root, kind: str, authorized_by: str, source_copy: Path = SOURCE_COPY, art_dir: Path | None = None, dev_of=None, head_expected: str = BASE_DEC053_HEAD) -> dict:
    art_dir = Path(art_dir or COM.ART)
    dev_of = dev_of or COM._default_dev_of
    dest = Path(dest_root)
    if kind not in COM.INDEP_KINDS:
        raise ValueError(f"kind must be one of {COM.INDEP_KINDS}")
    if not authorized_by.strip():
        raise ValueError("an explicit authorisation text is required")
    if dest.exists():
        raise FileExistsError(f"destination exists: {dest}")
    if (art_dir / COM.INDEP_EVIDENCE).exists():
        raise FileExistsError("independent-backup evidence already exists: it is never overwritten")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dev_of(dest.parent) == dev_of(source_copy):
        raise RuntimeError("destination is on the same device as the source: not an independent backup")
    base = json.loads((art_dir / "IEEE39_DEC054_baseline_manifest.json").read_text(encoding="utf-8"))
    files = base["ignored_local_files"]
    shutil.copytree(source_copy, dest)                                   # fails if dest exists; source is never modified
    bad = [rel for rel, m in files.items() if not (dest / "files" / rel).is_file() or COM.sha_file(dest / "files" / rel) != m["sha256"]]
    if bad:
        raise RuntimeError(f"{len(bad)} files failed SHA-256 verification at the destination; evidence NOT written")
    bundle = dest / "rdc_all_refs_dec054.bundle"
    ver = subprocess.run(["git", "bundle", "verify", str(bundle)], capture_output=True, text=True)
    tmp = Path(tempfile.mkdtemp(prefix="dr"))
    npz_tests = []
    try:
        big = sorted([r for r in files if r.endswith(".npz")], key=lambda r: -files[r]["bytes"])[:3]
        for rel in big:
            t = tmp / Path(rel).name
            shutil.copyfile(dest / "files" / rel, t)
            z = np.load(t)
            npz_tests.append({"path": rel, "readable": True, "first_array": z.files[0], "sha256_restored": COM.sha_file(t), "sha256_expected": files[rel]["sha256"]})
            z.close()
        cl = subprocess.run(["git", "-c", "core.longpaths=true", "clone", "-q", str(bundle), str(tmp / "c")], capture_output=True, text=True)
        head = subprocess.run(["git", "rev-parse", "origin/review/dec053-methodology-closure"], cwd=str(tmp / "c"), capture_output=True, text=True).stdout.strip() if cl.returncode == 0 else ""
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    ev = {"schema_version": 1, "stage": "DEC-054 G0 independent backup", "destination_kind": kind, "authorized_by": authorized_by, "destination_root": str(dest), "source_root": str(source_copy),
          "files_checked": len(files), "files_bad": bad, "created_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
          "restore_test": {"npz": npz_tests, "bundle": {"sha256": COM.sha_file(bundle), "verify_rc": ver.returncode, "clone_rc": cl.returncode, "clone_head": head, "clone_head_ok": head == head_expected}}}
    if bad:
        raise RuntimeError(f"{len(bad)} files failed SHA-256 verification at the destination; evidence NOT written")
    with open(art_dir / COM.INDEP_EVIDENCE, "x", encoding="utf-8") as f:       # exclusive: never overwrites
        json.dump(ev, f, indent=1)
    return ev


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    r = create_independent_backup(sys.argv[1], sys.argv[2], sys.argv[3])
    print(json.dumps({k: r[k] for k in ("files_checked", "files_bad", "destination_kind")}), COM.backup_gate())
