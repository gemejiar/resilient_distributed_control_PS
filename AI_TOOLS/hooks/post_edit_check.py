"""PostToolUse hook: advisory checks after an Edit/Write/MultiEdit.

Reads the hook payload from stdin to see which file was touched. If it is a
governed artifact, it emits a targeted, edit-time reminder to register a
decision-log entry -- this is the actionable moment, while the agent is still
working. For any other file it falls back to the generic advisory checks.
Always non-blocking.
"""

import json
import sys

GOVERNED_PREFIXES = (
    "plan_maestro.md",
    "paper/main.tex",
    "paper/biblio_paper.bib",
    "ops/sted/traceability_matrix.csv",
    "research/",
)

GENERIC = (
    "post_edit_check (advisory, non-blocking): (1) Verify labels, references "
    "and filenames remain consistent. (2) Update ops/sted/decision_log.md if "
    "the change was nontrivial. (3) Report any remaining PENDING_EVIDENCE or "
    "BLOCKED items."
)


def _file_path(payload: dict) -> str:
    ti = payload.get("tool_input") or {}
    path = ti.get("file_path") or ti.get("path") or ""
    return path.replace("\\", "/")


def _repo_tail(path: str) -> str:
    """Best-effort repo-relative path for the governed-prefix match below."""
    for marker in ("plan_maestro.md", "paper/", "ops/", "research/"):
        idx = path.find(marker)
        if idx != -1:
            return path[idx:]
    return path


def _is_governed(path: str) -> bool:
    tail = _repo_tail(path)
    return any(tail == pref or tail.startswith(pref) for pref in GOVERNED_PREFIXES)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    path = _file_path(payload)
    if path and _is_governed(path):
        tail = _repo_tail(path)
        context = (
            f"post_edit_check (advisory): '{tail}' is a GOVERNED artifact. "
            "Per AGENTS.md/CLAUDE.md, a nontrivial change here needs a DEC "
            "entry in ops/sted/decision_log.md before the session closes. "
            "Also confirm the edit "
            "does not assert a claim beyond its evidence status in "
            "ops/sted/traceability_matrix.csv, and preserve LaTeX "
            "labels/cites/refs."
        )
    else:
        context = GENERIC

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": context,
        }
    }))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Never break the tool pipeline; emit the generic advisory.
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": GENERIC,
            }
        }))
        sys.exit(0)
