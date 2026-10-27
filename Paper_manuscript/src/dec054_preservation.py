"""DEC-054 phase P0: Git snapshot, protected-file baseline, bundle, raw-series copy and restore test.
Read-only on the original repository; creates new files only (exclusive creation; aborts if a destination exists)."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MAIN = Path(r"c:/onedrive/OneDrive - Universidad del Valle/05_Univalle_Investigacion/02_Publicaciones/En_Preparacion/Proyectos_Latex/Resilient_distributed_control_PS")
WT = Path(r"C:/Users/gemej/dec054_wt")
ART = WT / "Paper_manuscript" / "artifacts"
DEST = Path(r"C:/Users/gemej/dec054_preservation_local")  # same physical disk: NOT an independent backup
BASE = "04e082b26054bf046bd5421ceb275b582a0547a5"
REMOTE_MAIN = "1a023d8fa333e62eb716e57a4d67561bb63ea3d0"
EXCLUDE = ("venv/", ".claude/settings.local.json")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git(*a, cwd=MAIN):
    r = subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True)
    return r.stdout.strip(), r.returncode, r.stderr.strip()


def excl(path):
    return any(path.startswith(e) or "/__pycache__/" in path or path.endswith(".pyc") for e in EXCLUDE) or "__pycache__" in path


def out(name, obj):
    p = ART / name
    assert not p.exists(), f"refuse to overwrite {p}"
    p.write_text(json.dumps(obj, indent=1, default=str), encoding="utf-8")


assert not DEST.exists(), "destination exists: refuse"
# ---------------------------------------------------------------- 1. git snapshot
refs = git("for-each-ref", "--format=%(refname) %(objectname)")[0].splitlines()
remote = git("ls-remote", "rdc")[0].splitlines()
status = git("status", "--porcelain")[0]
snap = {"local_refs": refs, "remote_rdc": remote, "status_porcelain_main_repo": status, "head_main_repo": git("rev-parse", "HEAD")[0],
        "worktree_head": git("rev-parse", "HEAD", cwd=WT)[0], "base_expected": BASE, "base_matches": git("rev-parse", "HEAD", cwd=WT)[0] == BASE,
        "remote_main_expected": REMOTE_MAIN, "remote_main_matches": any(l.startswith(REMOTE_MAIN) and l.endswith("refs/heads/main") for l in remote),
        "remote_urls_redacted": [l.split()[0] + " " + l.split()[1].split("//")[-1].split("@")[-1] for l in git("remote", "-v")[0].splitlines()]}
# ---------------------------------------------------------------- 2. protected-file baseline (read-only, before running anything else)
tree = git("ls-tree", "-r", BASE)[0].splitlines()
blobs = {l.split("\t")[1]: l.split()[2] for l in tree}
prot = {}
for rel in blobs:
    if rel.startswith(("Paper_manuscript/artifacts/", "Paper_manuscript/src/", "Paper_manuscript/cases/", "ops/", "Paper_manuscript/main.tex", "plan_maestro.md")):
        p = MAIN / rel
        prot[rel] = {"git_blob": blobs[rel], "sha256_workdir": sha(p) if p.exists() else "MISSING"}
ign = [f for f in git("ls-files", "--others", "--ignored", "--exclude-standard")[0].splitlines() if not excl(f)]
ign = [f for f in ign if (MAIN / f).is_file()]
ignored = {f: {"bytes": (MAIN / f).stat().st_size, "sha256": sha(MAIN / f)} for f in ign}
out("IEEE39_DEC054_baseline_manifest.json", {"stage": "DEC-054 P0 baseline", "snapshot": snap, "n_tracked_files_at_base": len(blobs), "protected_tracked": prot, "ignored_local_files": ignored,
                                             "note": "hashes computed read-only on the original working tree before any new code ran; .claude/settings.local.json and venv/ excluded"})
print("baseline", len(prot), "protected tracked;", len(ignored), "ignored local files;", sum(v["bytes"] for v in ignored.values()) // 10**6, "MB")
# compare with DEC-053 manifest
rep = json.load(open(MAIN / "Paper_manuscript/artifacts/IEEE39_DEC053_reproducibility.json"))
mis = []
for b in rep["big_series"]:
    rel = b["path"]
    cur = ignored.get(rel) or {"sha256": sha(MAIN / rel)}
    if cur["sha256"] != b["sha256"]:
        mis.append(rel)
print("DEC-053 big-series hash mismatches:", mis, "of", len(rep["big_series"]))
# ---------------------------------------------------------------- 3. bundle
DEST.mkdir(parents=True)
bundle = DEST / "rdc_all_refs_dec054.bundle"
r = git("bundle", "create", str(bundle), "--all")
ver = git("bundle", "verify", str(bundle))
tmp = Path(tempfile.mkdtemp(prefix="dec054_clone_"))
cl = subprocess.run(["git", "clone", "-q", str(bundle), str(tmp / "clone")], capture_output=True, text=True)
clone_head = git("rev-parse", "origin/review/dec053-methodology-closure", cwd=tmp / "clone")[0] if cl.returncode == 0 else ""
clone_main = git("rev-parse", "origin/main", cwd=tmp / "clone")[0] if cl.returncode == 0 else ""
bundle_info = {"bundle_bytes": bundle.stat().st_size, "bundle_sha256": sha(bundle), "verify_rc": ver[1], "verify_msg": (ver[0] or ver[2]).splitlines()[-1] if (ver[0] or ver[2]) else "",
               "clone_rc": cl.returncode, "clone_dec053_head": clone_head, "clone_matches_dec053": clone_head == BASE, "clone_contains_local_main_commits": bool(git("cat-file", "-t", "acab954", cwd=tmp / "clone")[0])}
print("bundle", bundle_info)
# ---------------------------------------------------------------- 4. raw-series copy (same disk) + per-file manifest
copies = {}
for rel, meta in ignored.items():
    d = DEST / "files" / rel
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(MAIN / rel, d)
    copies[rel] = {"bytes": d.stat().st_size, "sha256_copy": sha(d), "sha256_source": meta["sha256"], "match": sha(d) == meta["sha256"]}
# also the tracked small manifests/cases needed to interpret the raw series
for rel in ("Paper_manuscript/artifacts/IEEE39_DEC053_reproducibility.json", "Paper_manuscript/artifacts/IEEE39_DEC053_inventory.csv", "Paper_manuscript/cases"):
    p = MAIN / rel
    files = [p] if p.is_file() else [q for q in p.rglob("*") if q.is_file()]
    for q in files:
        rr = q.relative_to(MAIN).as_posix()
        d = DEST / "files" / rr
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(q, d)
        copies[rr] = {"bytes": d.stat().st_size, "sha256_copy": sha(d), "sha256_source": sha(q), "match": sha(d) == sha(q)}
(DEST / "MANIFEST_SHA256.json").write_text(json.dumps(copies, indent=1), encoding="utf-8")
# ---------------------------------------------------------------- 5. restore test from the copy
restore = Path(tempfile.mkdtemp(prefix="dec054_restore_"))
big = sorted((r for r in copies if r.endswith(".npz")), key=lambda r: -copies[r]["bytes"])[:3]
rt = {}
import numpy as np

for rel in big:
    shutil.copyfile(DEST / "files" / rel, restore / Path(rel).name)
    h = sha(restore / Path(rel).name)
    z = np.load(restore / Path(rel).name)  # real readability test
    k = z.files[0]
    rt[rel] = {"sha256_restored": h, "matches_original_manifest": h == ignored.get(rel, {}).get("sha256"), "npz_readable": True, "first_array": k, "shape": list(z[k].shape)}
bundle_restore = restore / "bundle_clone"
rc = subprocess.run(["git", "clone", "-q", str(bundle), str(bundle_restore)], capture_output=True, text=True).returncode
rt["bundle_clone_rc"] = rc
rt["bundle_clone_head_dec053"] = git("rev-parse", "origin/review/dec053-methodology-closure", cwd=bundle_restore)[0]
all_ok = all(c["match"] for c in copies.values()) and all(v.get("matches_original_manifest") for k, v in rt.items() if isinstance(v, dict)) and bundle_info["verify_rc"] == 0 and bundle_info["clone_matches_dec053"]
status_backup = "BACKUP_BLOCKED"  # no independent destination (other physical drive / remote) is available or authorised
out("IEEE39_DEC054_backup_manifest.json", {"stage": "DEC-054 P0 backup", "status": status_backup, "gate0": "STOP_BACKUP_NOT_VERIFIED",
                                           "reason": "The only physical disk is the OS NVMe (C:); no external drive, remote destination or authorised service was provided. A second copy was made on the same physical disk and is NOT an independent backup.",
                                           "logical_destination": "local folder outside the repository tree and outside OneDrive (path not published)", "storage_type": "SAME_PHYSICAL_DISK_COPY (NVMe C:)",
                                           "bundle": bundle_info, "files_copied": len(copies), "all_copy_hashes_match_source": all(c["match"] for c in copies.values()), "per_file": copies,
                                           "dec053_at_risk_series_covered": [b["path"] for b in rep["big_series"] if b["path"] in copies], "dec053_series_hash_mismatches": mis})
out("IEEE39_DEC054_preservation_test.json", {"stage": "DEC-054 P0 restore test", "restored_from": "same-disk copy (not independent)", "large_series_restore": {k: v for k, v in rt.items() if isinstance(v, dict)},
                                              "bundle": {"verify_rc": bundle_info["verify_rc"], "clone_head": rt["bundle_clone_head_dec053"], "clone_ok": rc == 0}, "all_ok_on_same_disk": all_ok,
                                              "independent_backup_verified": False, "gate0": "STOP_BACKUP_NOT_VERIFIED"})
print("restore test", all_ok, rt["bundle_clone_head_dec053"])
shutil.rmtree(tmp, ignore_errors=True)
shutil.rmtree(restore, ignore_errors=True)
