"""Session close: reconcile governed edits against the decision log.

STED-RW Lean (AGENTS.md, CLAUDE.md) requires that nontrivial changes to the
governed artifacts be justified in ops/sted/decision_log.md. That rule lived
only in prose and in an advisory PostToolUse nudge, so it was easy to skip.

This script turns the rule into an executable check. It compares the working
tree against HEAD and, if any governed artifact changed without a matching
touch to decision_log.md, it prints a reminder naming the exact files and the
next free DEC number. It is advisory (always exits 0) to match the repository's
existing hook convention; the actionable, edit-time enforcement lives in
.claude/hooks/post_edit_check.py.

Intended to run at the Claude Code Stop hook. Also runnable by hand:
    python ops/checks/session_close.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Governed artifacts: a change here is "nontrivial" and needs a DEC entry.
# Keep this list in sync with the prefixes in .claude/hooks/post_edit_check.py.
GOVERNED_PREFIXES = (
    "plan_maestro.md",
    "paper/main.tex",
    "paper/biblio_paper.bib",
    "ops/sted/traceability_matrix.csv",
    "ops/sted/test_plan.md",
    "research/",
)
DECISION_LOG = "ops/sted/decision_log.md"


def changed_paths() -> list[str]:
    """Paths that differ from HEAD, including untracked, as POSIX strings."""
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=ROOT, capture_output=True, text=True, timeout=8,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    paths: list[str] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        # porcelain: XY<space>path  (rename shows "old -> new")
        raw = line[3:].strip()
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        paths.append(raw.strip().strip('"').replace("\\", "/"))
    return paths


def is_governed(path: str) -> bool:
    return any(path == p or path.startswith(p) for p in GOVERNED_PREFIXES)


def next_dec_number() -> str:
    try:
        text = (ROOT / DECISION_LOG).read_text(encoding="utf-8-sig")
    except OSError:
        return "DEC-018"
    nums = [int(m) for m in re.findall(r"## DEC-(\d{3})\b", text)]
    return f"DEC-{(max(nums) + 1) if nums else 1:03d}"


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass

    changed = changed_paths()
    governed = sorted({p for p in changed if is_governed(p)})
    dec_touched = DECISION_LOG in changed

    if not governed:
        print("[session_close] Sin cambios en artefactos gobernados. OK.")
        return 0
    if dec_touched:
        print(
            "[session_close] "
            f"{len(governed)} artefacto(s) gobernado(s) modificado(s); "
            "decision_log.md tambien fue tocado. OK."
        )
        return 0

    print("[session_close] AVISO (advisory): artefactos gobernados modificados "
          "SIN entrada en el decision log.")
    for p in governed:
        print(f"  - {p}")
    print(f"  Registra {next_dec_number()} en {DECISION_LOG} antes de cerrar "
          "(AGENTS.md: no cambiar artefactos gobernados sin registrarlo).")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # never break the Stop hook
        print(f"[session_close] fallo no fatal: {exc}")
        sys.exit(0)
