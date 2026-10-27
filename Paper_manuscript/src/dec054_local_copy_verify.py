"""DEC-054: verify the project-folder copy of the P0 preservation (read-only on the source; restore test in a temporary folder inside backups/, removed afterwards).
Writes IEEE39_DEC054_local_copy_manifest.json exclusively.  Status stays LOCAL_PROJECT_COPY_VERIFIED_NOT_INDEPENDENT (same disk / same synchronised tree): BACKUP_VERIFIED is NOT declared."""
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(r"c:/onedrive/OneDrive - Universidad del Valle/05_Univalle_Investigacion/02_Publicaciones/En_Preparacion/Proyectos_Latex/Resilient_distributed_control_PS")
SRC = Path(r"C:/Users/gemej/dec054_preservation_local")
BK = ROOT / "Paper_manuscript" / "backups"
DST = BK / "DEC054_P0_preservation"
OUT = Path(r"C:/Users/gemej/dec054_wt/Paper_manuscript/artifacts/IEEE39_DEC054_local_copy_manifest.json")
BASE = "04e082b26054bf046bd5421ceb275b582a0547a5"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


for stale in list(BK.glob("restore_*")) + list(BK.glob("r*")):                      # leftovers of my own failed verification run only
    if stale.is_dir() and stale.parent == BK and stale.name != DST.name:
        shutil.rmtree(stale)
man = json.load(open(DST / "MANIFEST_SHA256.json"))
src_n = sum(1 for p in SRC.rglob("*") if p.is_file())
dst_n = sum(1 for p in DST.rglob("*") if p.is_file())
n = bad = 0
for rel, m in man.items():
    d = DST / "files" / rel
    n += 1
    if (not d.exists()) or sha(d) != m["sha256_source"]:
        bad += 1
        print("BAD", rel)
bund = DST / "rdc_all_refs_dec054.bundle"
same_bundle = sha(bund) == sha(SRC / "rdc_all_refs_dec054.bundle")
ver = subprocess.run(["git", "bundle", "verify", str(bund)], capture_output=True, text=True, cwd=str(ROOT))
tmp = Path(tempfile.mkdtemp(prefix="r", dir=str(BK))).resolve()
big = sorted([r for r in man if r.endswith(".npz")], key=lambda r: -man[r]["bytes"])[:3]
rt = {}
for rel in big:
    t = tmp / Path(rel).name
    shutil.copyfile(DST / "files" / rel, t)
    z = np.load(t)
    rt[rel] = {"sha256_ok": sha(t) == man[rel]["sha256_source"], "readable": True, "first_array": z.files[0]}
    z.close()
cl = subprocess.run(["git", "-c", "core.longpaths=true", "clone", "-q", str(bund), str(tmp / "c")], capture_output=True, text=True)
head = subprocess.run(["git", "rev-parse", "origin/review/dec053-methodology-closure"], cwd=str(tmp / "c"), capture_output=True, text=True).stdout.strip() if cl.returncode == 0 else ""
print("clone rc", cl.returncode, cl.stderr[:300])
shutil.rmtree(tmp, ignore_errors=True)
out = {"stage": "DEC-054 local project copy", "location_logical": "Paper_manuscript/backups/DEC054_P0_preservation (inside the paper folder; excluded from Git via .git/info/exclude)",
       "authorised_by": "investigator instruction: store locally inside the paper folder", "files_in_source": src_n, "files_in_copy": dst_n, "files_verified": n, "files_bad": bad,
       "bundle_identical_to_source": same_bundle, "bundle_sha256": sha(bund), "bundle_verify_rc": ver.returncode, "restore_test": rt, "bundle_clone_rc": cl.returncode,
       "bundle_clone_dec053_head": head, "bundle_head_ok": head == BASE, "independent_of_original_disk": False, "independent_backup_verified": False,
       "status": "LOCAL_PROJECT_COPY_VERIFIED_NOT_INDEPENDENT",
       "note": "same physical disk and same OneDrive-synchronised tree as the originals; OneDrive sync state not verified; BACKUP_VERIFIED not declared; gate unchanged"}
with open(OUT, "x", encoding="utf-8") as f:
    json.dump(out, f, indent=1)
print({k: out[k] for k in ("files_in_source", "files_in_copy", "files_verified", "files_bad", "bundle_identical_to_source", "bundle_verify_rc", "bundle_clone_rc", "bundle_head_ok", "status")})
print({k: v["sha256_ok"] for k, v in rt.items()})
