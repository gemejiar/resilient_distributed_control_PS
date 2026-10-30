"""DEC-066 G0: read-only integrity audit, environment registry, regression of the DEC-062 metrics from raw series, and event/sample alignment.
No TDS, no PF beyond importing modules, nothing historical is written.  Writes IEEE39_DEC066_G0_manifest.json and IEEE39_DEC066_G0_regression.csv exclusively with 'write'.
Run: <venv python> dec066_g0.py [write]"""
from __future__ import annotations

import contextlib
import csv
import datetime
import hashlib
import io
import json
import os
import platform
import re
import subprocess
import sys

import numpy as np

import dec055_common as C55
import dec059_tds as T

REPO = C55.ART.parents[1]                                   # worktree root (git)
FROZEN = ("Paper_manuscript/artifacts/IEEE39_DEC05", "Paper_manuscript/artifacts/IEEE39_DEC06", "Paper_manuscript/src/dec05", "Paper_manuscript/src/dec06", "Paper_manuscript/src/test_",
          "Paper_manuscript/src/run_", "Paper_manuscript/src/e8", "Paper_manuscript/src/e9", "ops/sted/", "Paper_manuscript/cases/", "Paper_manuscript/main.tex", "Paper_manuscript/main_revision_DEC065.tex",
          "Paper_manuscript/references")
EXCLUDE_NEW = ("dec066_", "test_dec066_", "IEEE39_DEC066_", "DEC066_")


def git(*a):
    return subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True, check=True).stdout.strip()


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def flat(o, pre=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from flat(v, f"{pre}/{k}")
    elif isinstance(o, (list, tuple)):
        for i, v in enumerate(o):
            yield from flat(v, f"{pre}[{i}]")
    else:
        yield pre, o


def main(write=False):
    out = {"label": "DEC066_G0_READ_ONLY", "date": datetime.datetime.now().astimezone().isoformat(timespec="seconds")}
    # ---------------- environment
    import andes
    import scipy
    out["environment"] = {"python": sys.version.split()[0], "executable": sys.executable, "os": platform.platform(), "cpu_count": os.cpu_count(), "andes": andes.__version__, "numpy": np.__version__, "scipy": scipy.__version__,
                          "threads_env": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")}, "seed": "none (deterministic; no random numbers in controllers/solver; SLSQP deterministic)"}
    try:
        import kvxopt
        out["environment"]["kvxopt"] = kvxopt.__version__
    except Exception:
        out["environment"]["kvxopt"] = None
    out["git"] = {"head": git("rev-parse", "HEAD"), "branch": git("branch", "--show-current"), "head_date": git("log", "-1", "--format=%ci"), "head_subject": git("log", "-1", "--format=%s"),
                  "dec059_branch": git("rev-parse", "review/dec059-scientific-reorientation"), "freeze_tag_commit": git("rev-list", "-n", "1", "dec062-freeze"), "status_porcelain": git("status", "--porcelain")}
    # ---------------- frozen file hashes (tracked files only)
    files = [f for f in git("ls-files").splitlines() if f.startswith(FROZEN) and not any(x in f for x in EXCLUDE_NEW)]
    man, dirty = {}, []
    for f in files:
        p = REPO / f
        man[f] = {"sha256": sha(p), "bytes": p.stat().st_size}
        if subprocess.run(["git", "diff", "--quiet", "HEAD", "--", f], cwd=REPO).returncode != 0:
            dirty.append(f)
    out["frozen_files"] = {"n": len(man), "modified_vs_HEAD": dirty, "sha256_of_manifest": hashlib.sha256(json.dumps(man, sort_keys=True).encode()).hexdigest(), "files": man}
    out["original_main_tex"] = {"git_blob_0db386b": git("rev-parse", "0db386b:Paper_manuscript/main.tex"), "git_blob_HEAD": git("rev-parse", "HEAD:Paper_manuscript/main.tex"), "sha256_worktree": sha(REPO / "Paper_manuscript/main.tex")}
    # ---------------- ANDES package aggregate hash
    root = os.path.dirname(andes.__file__)
    hs = []
    for dp, _, fn in os.walk(root):
        for n in sorted(fn):
            if n.endswith((".py", ".json", ".xlsx", ".cfg")):
                hs.append((os.path.relpath(os.path.join(dp, n), root), sha(os.path.join(dp, n))))
    hs.sort()
    out["andes_package"] = {"root": root, "n_files": len(hs), "aggregate_sha256": hashlib.sha256(json.dumps(hs).encode()).hexdigest()}
    # ---------------- run directories (raw data, Git-excluded)
    runs = sorted(p for p in T.RUNS.iterdir() if p.is_dir())
    bad, nfile = [], 0
    for r in runs:
        hp = r / "hashes.json"
        if not hp.exists():
            continue
        for f, v in json.loads(hp.read_text(encoding="utf-8")).items():
            nfile += 1
            if not (r / f).exists() or sha(r / f) != v:
                bad.append(f"{r.name}/{f}")
    d62 = [r.name for r in runs if r.name.startswith(("D62TEST_", "D62CMP_"))]
    out["raw_runs"] = {"root": str(T.RUNS), "n_dirs": len(runs), "n_files_verified": nfile, "hash_mismatches_or_missing": bad, "D62_test": sum(n.startswith("D62TEST_") for n in d62), "D62_cmp": sum(n.startswith("D62CMP_") for n in d62),
                       "D62_total_bytes": int(sum(f.stat().st_size for r in runs if r.name in d62 for f in r.iterdir()))}
    # ---------------- plan equivalence (36 + 18)
    plan_ids = set()
    for pn in ("IEEE39_DEC059_R5A_plan.json", "IEEE39_DEC059_R5B_plan.json"):
        plan_ids |= set(re.findall(r"D62(?:TEST|CMP)_[A-Za-z0-9_]+", (C55.ART / pn).read_text(encoding="utf-8")))
    out["plan_equivalence"] = {"plan_ids": len(plan_ids), "run_dirs": len(d62), "in_plan_not_on_disk": sorted(plan_ids - set(d62)), "on_disk_not_in_plan": sorted(set(d62) - plan_ids)}
    # ---------------- regression of the DEC-062 analysis from raw series (read-only)
    import dec062_test as D62
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        new = D62.main(write=False)
    old = json.loads((C55.ART / "IEEE39_DEC062_TEST_results.json").read_text(encoding="utf-8"))
    fo, fn = dict(flat(old)), dict(flat(new))
    keys = sorted(set(fo) | set(fn))
    diffs = []
    for k in keys:
        a, b = fo.get(k, "<missing>"), fn.get(k, "<missing>")
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
            if not (a == b or (a != a and b != b) or abs(a - b) <= 1e-12 * max(1.0, abs(a))):
                diffs.append((k, a, b))
        elif a != b:
            diffs.append((k, a, b))
    out["regression"] = {"leaves_compared": len(keys), "leaf_mismatches": len(diffs), "first_mismatches": [(k, str(a)[:60], str(b)[:60]) for k, a, b in diffs[:10]]}
    rows = []
    for key, v in new["A"].items():
        for c in v["cells"]:
            o = next(x for x in old["A"][key]["cells"] if x["run_id"] == c["run_id"])
            rows.append([c["run_id"], c["class"], o["class"], c["m50"], o["m50"], abs(c["m50"] - o["m50"]), c["pred_margin"], c["e"], o["e"], c["false_SAFE"], c["class_matches_prediction"]])
    for oc, cells in new["B"].items():
        for cell, d in cells.items():
            for ctl, c in d.items():
                o = old["B"][oc][cell][ctl]
                rows.append([c["run_id"], c["class"], o["class"], c["m50"], o["m50"], abs(c["m50"] - o["m50"]), c["pred_margin"], c["e"], o["e"], c["false_SAFE"], c["class_matches_prediction"]])
    out["regression"]["rows"] = len(rows)
    out["regression"]["classes_recomputed"] = {k: sum(r[1] == k for r in rows) for k in sorted({r[1] for r in rows})}
    # ---------------- event / sample alignment over the 54 runs
    al = []
    for n in d62:
        z = np.load(T.RUNS / n / "series.npz", allow_pickle=True)
        t, P, V = z["t"], z["P"], z["V"]
        d = np.abs(P - P[0][None, :]).max(axis=1)
        k = int(np.argmax(d > 1e-9))
        ct, ps = z["cmd_t"], z["cmd_pset"]
        dc = np.abs(ps - ps[0][None, :]).max(axis=1)
        kc = int(np.argmax(dc > 1e-12))
        al.append({"run": n, "t_prev": float(t[k - 1]), "t_first_changed": float(t[k]), "dt_prev_step": float(t[k] - t[k - 1]), "max_dP_first_sample": float(d[k]), "t_first_cmd_change": float(ct[kc]),
                   "dt_refined_ok": bool(abs((t[k] - t[k - 1]) - 2 ** -8 / 16) < 1e-12)})
    out["event_alignment"] = {"t_e": 5.0, "n": len(al), "first_changed_sample_times": sorted({a["t_first_changed"] for a in al}), "prev_sample_times": sorted({a["t_prev"] for a in al}), "step_before_event_s": sorted({a["dt_prev_step"] for a in al}),
                              "first_cmd_change_times": sorted({a["t_first_cmd_change"] for a in al}), "all_refined_step_before_event": all(a["dt_refined_ok"] for a in al),
                              "interpretation": "event applied at the end of the dt/16 step [4.99975586, 5.0]; stored sample t=5.0 is the first post-jump point; controller update uses post-jump measurements from the step starting at t=5.0"}
    print(json.dumps({k: out[k] for k in ("raw_runs", "plan_equivalence", "event_alignment")}, indent=1, default=str)[:2600])
    print("regression", {k: out["regression"][k] for k in ("leaves_compared", "leaf_mismatches", "rows", "classes_recomputed")}, "frozen modified:", dirty, "n frozen", len(man))
    if write:
        with open(C55.ART / "IEEE39_DEC066_G0_manifest.json", "x", encoding="utf-8") as f:
            json.dump(out, f, indent=1, default=str)
        with open(C55.ART / "IEEE39_DEC066_G0_regression.csv", "x", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["run_id", "class_recomputed", "class_stored", "m50_recomputed", "m50_stored", "abs_diff", "pred_margin", "e_recomputed", "e_stored", "false_SAFE", "class_matches_prediction"])
            w.writerows(rows)
    return out


if __name__ == "__main__":
    main("write" in sys.argv)
