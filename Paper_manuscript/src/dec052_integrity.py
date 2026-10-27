"""DEC-052 E3: integrity of the historical results and reproducibility of the static calculations.  No simulation.
Compares (i) the SHA-256 recorded in IEEE39_DEC051_consolidation.json with the files on disk, (ii) the working tree with commit 5719200, (iii) a second execution of the three audit scripts with the first one.
Outputs: IEEE39_DEC052_integrity.json, IEEE39_DEC052_reproducibility.json."""
from __future__ import annotations

import json
import subprocess
import sys

import dec052_common as K
from run_e0_ieee39 import ARTIFACTS_DIR as A, PROJECT_ROOT

BASE = "5719200"
OUT = ["IEEE39_DEC052_model_audit.json", "IEEE39_DEC052_jacobian_certificate.json", "IEEE39_DEC052_lyapunov_certificate.json", "IEEE39_DEC052_root_certificate.json", "IEEE39_DEC052_H3_audit.json",
       "IEEE39_DEC052_H3_voltage_audit.csv", "IEEE39_DEC052_H3_reserve_audit.csv", "IEEE39_DEC052_H3_location_scan.csv"]
SCRIPTS = ["dec052_model_audit.py", "dec052_certificates.py", "dec052_h3_audit.py"]


def git(*a):
    return subprocess.run(["git", "-C", str(PROJECT_ROOT), *a], capture_output=True, text=True).stdout


def flat(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from flat(v, p + "/" + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from flat(v, p + f"[{i}]")
    else:
        yield p, o


def compare(a, b, tol=1e-9):
    da, db = dict(flat(a)), dict(flat(b))
    diffs = []
    for k in sorted(set(da) | set(db)):
        x, y = da.get(k), db.get(k)
        if isinstance(x, (int, float)) and isinstance(y, (int, float)) and not isinstance(x, bool):
            if abs(x - y) > tol * max(1.0, abs(x), abs(y)):
                diffs.append((k, x, y))
        elif x != y:
            diffs.append((k, x, y))
    return diffs


def main() -> int:
    cons = json.loads((A / "IEEE39_DEC051_consolidation.json").read_text(encoding="utf-8"))
    src_dir, fig_dir = A.parent / "src", A.parent / "figures_main"
    rec = {}
    for name, h in cons["hashes_sha256"].items():
        if name == "IEEE39_DEC051_consolidation.json":
            continue                                                # a file cannot contain its own hash
        f = next((p / name for p in (A, src_dir, fig_dir) if (p / name).exists()), None)
        rec[name] = {"recorded": h.lower(), "on_disk": K.sha(f).lower() if f else None, "match": bool(f and K.sha(f).lower() == h.lower())}
    mism = {k: v for k, v in rec.items() if not v["match"]}
    status = git("status", "--porcelain").splitlines()
    modified_tracked = [l[3:] for l in status if l[:2].strip() in ("M", "D", "R")]
    untracked = [l[3:] for l in status if l.startswith("??")]
    diff_names = git("diff", "--name-status", BASE).splitlines()
    protected = ("Paper_manuscript/artifacts/IEEE39_E", "Paper_manuscript/artifacts/IEEE39_B", "Paper_manuscript/artifacts/IEEE39_DEC050", "Paper_manuscript/artifacts/IEEE39_DEC051", "Paper_manuscript/artifacts/DEC050",
                 "Paper_manuscript/artifacts/DEC051", "Paper_manuscript/figures_main", "Paper_manuscript/src/run_", "Paper_manuscript/src/dec051", "Paper_manuscript/src/e9", "Paper_manuscript/src/analyse_",
                 "Paper_manuscript/src/finalize_", "Paper_manuscript/src/select_", "Paper_manuscript/src/validate_", "Paper_manuscript/src/audit_")
    touched = [l for l in diff_names if any(l.split("\t", 1)[-1].startswith(p) for p in protected)]
    plant_files = ["Paper_manuscript/src/run_e8_ieee39.py", "Paper_manuscript/src/run_b3_ieee39.py", "Paper_manuscript/src/e9b_variant.py", "Paper_manuscript/src/e9h_predictor.py", "Paper_manuscript/src/e9a_linear.py"]
    plant_diff = git("diff", "--name-only", BASE, "--", *plant_files).split()
    integrity = {"stage": "DEC-052 E3 integrity", "git_commit": K.git_commit(), "software": K.env(), "base_commit": BASE, "base_commit_sha": git("rev-parse", BASE).strip(),
                 "DEC051_recorded_hashes_vs_disk": {"n_files": len(rec), "n_match": len(rec) - len(mism), "mismatches": mism, "detail": rec,
                                                    "note": "IEEE39_DEC051_consolidation.json itself is excluded (it holds the other hashes); gitignored raw series are checked from the local files"},
                 "tracked_files_modified_vs_base_at_time_of_check": modified_tracked, "new_untracked_files_at_time_of_check": untracked, "diff_vs_base_name_status": diff_names,
                 "historical_or_protected_files_touched": touched, "plant_parameter_sources_checked": plant_files, "plant_parameter_sources_changed_vs_base": plant_diff,
                 "legitimately_updated_records_in_DEC052": ["plan_maestro.md", "ops/sted/decision_log.md", "ops/sted/traceability_matrix.csv", "Paper_manuscript/artifacts/experiment_matrix.csv"],
                 "DEC049": "no entry exists in decision_log.md (the number appears only inside the DEC-050 text); nothing was fabricated"}
    commit_date = git("log", "-1", "--format=%ad", "--date=iso", "5719200").strip()
    log = (PROJECT_ROOT / "ops/sted/decision_log.md").read_text(encoding="utf-8")
    i = log.index("## DEC-051")
    logged = [l for l in log[i:i + 400].splitlines() if l.startswith("Date:")][0]
    integrity["DEC051_date_check"] = {"decision_log_date": logged, "commit_5719200_author_date": commit_date, "commit_c07c482_author_date": git("log", "-1", "--format=%ad", "--date=iso", "c07c482").strip(),
                                      "environment_clock_at_DEC052": "Tue Oct 27 2026 (system date)",
                                      "discrepancy": "the log says 2026-10-28; the commit and the clock say 2026-10-27 (one-day error in the log entry; no evidence for 2026-10-28). The historical entry is not edited: a correction note is appended in DEC-052."}
    integrity["status"] = "OK" if (not mism and not touched and not plant_diff) else "CHECK"
    K.dump("IEEE39_DEC052_integrity.json", integrity)
    first = {f: K.sha(A / f) for f in OUT}
    first_json = {f: json.loads((A / f).read_text(encoding="utf-8")) for f in OUT if f.endswith(".json")}
    repro = {"stage": "DEC-052 reproducibility", "git_commit": K.git_commit(), "software": K.env(), "scripts": SCRIPTS, "first_run_sha256": first, "second_run_sha256": {}, "identical_bytes": {}, "numerical_differences": {}, "return_codes": {}}
    for sc in SCRIPTS:
        r = subprocess.run([sys.executable, str(A.parent / "src" / sc)], cwd=str(A.parent / "src"), capture_output=True, text=True)
        repro["return_codes"][sc] = r.returncode
    for f in OUT:
        h2 = K.sha(A / f)
        repro["second_run_sha256"][f] = h2
        repro["identical_bytes"][f] = bool(h2 == first[f])
        if h2 != first[f] and f.endswith(".json"):
            d = compare(first_json[f], json.loads((A / f).read_text(encoding="utf-8")))
            repro["numerical_differences"][f] = {"n_differences_above_1e-9_relative": len(d), "examples": [[k, x, y] for k, x, y in d[:8]]}
    repro["all_identical_or_within_1e-9"] = bool(all(repro["identical_bytes"][f] or repro["numerical_differences"].get(f, {}).get("n_differences_above_1e-9_relative", 1) == 0 for f in OUT) and all(v == 0 for v in repro["return_codes"].values()))
    repro["static_recomputation_of_the_equilibrium_residual"] = json.loads((A / "IEEE39_DEC052_root_certificate.json").read_text(encoding="utf-8"))["residuals_recomputed_now"]
    K.dump("IEEE39_DEC052_reproducibility.json", repro)
    print(json.dumps({"integrity": integrity["status"], "hash_mismatches": list(mism), "touched": touched, "plant_diff": plant_diff, "repro": repro["all_identical_or_within_1e-9"], "ident": repro["identical_bytes"], "diffs": repro["numerical_differences"], "rc": repro["return_codes"]}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
