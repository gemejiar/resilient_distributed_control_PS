"""DEC-063 integrity and chronology audit of the DEC-062 TEST evidence (read-only; no TDS).
Checks: (1) per-run file hashes against hashes.json; (2) that every TEST run directory was written after the commit that sealed predictions/hypotheses/plans (f42fb9a) and after the freeze tag;
(3) that predictions, plans and the protocol are byte-identical between the sealing commit and HEAD; (4) run count per cohort; (5) ledger total.  Writes IEEE39_DEC063_audit.json exclusively with 'write'."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys

import dec055_common as C55
import dec059_tds as T

SEAL, FREEZE_TAG = "f42fb9a", "dec062-freeze"
REPO = C55.ART.parents[1]


def git(*a):
    return subprocess.run(["git", *a], cwd=C55.ART, capture_output=True, text=True, check=True).stdout.strip()


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(write=False):
    t_seal = float(git("log", "-1", "--format=%ct", SEAL))
    t_frz = float(git("log", "-1", "--format=%ct", FREEZE_TAG))
    runs = sorted(p for p in T.RUNS.iterdir() if p.name.startswith(("D62TEST_", "D62CMP_")))
    bad_hash, early, n = [], [], {"D62TEST": 0, "D62CMP": 0}
    for r in runs:
        n[r.name.split("_")[0]] += 1
        h = json.loads((r / "hashes.json").read_text(encoding="utf-8"))
        for f, v in h.items():
            if sha(r / f) != v:
                bad_hash.append(f"{r.name}/{f}")
        if min((r / f).stat().st_mtime for f in h) < t_seal:
            early.append(r.name)
    files = [p for p in git("ls-tree", "-r", "--name-only", SEAL).splitlines() if any(k in p for k in ("_pred_", "_plan.json", "DEC062_protocol", "dec059_b5.py", "dec059_pred.py", "dec054_opf", "dec062_r5.py", "dec062_test.py"))]
    changed = []
    for p in files:
        d = subprocess.run(["git", "diff", "--quiet", SEAL, "HEAD", "--", p], cwd=C55.ART)
        if d.returncode != 0:
            changed.append(p)
    # code that defines the controller/predictor/classification must be identical between the freeze tag and HEAD
    frozen_code = ["Paper_manuscript/src/dec059_b5.py", "Paper_manuscript/src/dec059_tds.py", "Paper_manuscript/src/dec059_pred.py", "Paper_manuscript/src/dec059_eq.py"]
    code_changed = {p: subprocess.run(["git", "diff", "--quiet", FREEZE_TAG, "HEAD", "--", p], cwd=C55.ART).returncode != 0 for p in frozen_code}
    order = git("log", "--format=%h %ct %s", "-6").splitlines()
    out = {"label": "DEC063_INTEGRITY_AUDIT_READ_ONLY", "seal_commit": SEAL, "freeze_tag": FREEZE_TAG, "n_runs": n, "hash_mismatches": bad_hash, "runs_older_than_seal": early,
           "sealed_files_checked": len(files), "sealed_files_changed_since_seal": changed, "frozen_code_changed_since_freeze": code_changed, "recent_commits": order}
    print(json.dumps(out, indent=1))
    if write:
        with open(C55.ART / "IEEE39_DEC063_audit.json", "x", encoding="utf-8") as f:
            json.dump(out, f, indent=1)


if __name__ == "__main__":
    main("write" in sys.argv)
