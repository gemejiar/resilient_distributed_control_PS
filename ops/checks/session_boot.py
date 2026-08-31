"""Session boot: derived project-state view for STED-RW Lean.

Prints a compact, always-current snapshot of where the project stands, computed
directly from the governed artifacts (never stored, so it cannot go stale):

  - active gate            <- plan_maestro.md / README.md / final_quality_report.md
  - claims / equations /   <- ops/sted/traceability_matrix.csv
    figures / references
  - test progress          <- ops/sted/test_plan.md
  - recent decisions and   <- ops/sted/decision_log.md
    the last pending "Next action"
  - git position           <- git
  - open stop conditions    <- CLAUDE.md contract (light checks)

Intended to be injected at session start (Claude Code SessionStart hook and the
Codex "Read first" step 0). Output is ASCII-only so it survives a Windows
console. Every section degrades to a warning line instead of crashing, so the
hook can never block a session.

Usage:
    python ops/checks/session_boot.py
"""

from __future__ import annotations

import csv
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Status tokens, normalized upper-case, grouped by meaning.
DONE_TOKENS = {"VERIFIED", "SUPPORTED", "PASSED", "PASS", "DONE", "OK", "CLOSED"}
FAIL_TOKENS = {"FAIL", "FAILED", "BLOCKED"}
# Anything else (PENDING, PENDING_EVIDENCE, PENDING_COMPLETION, PENDING_VERIFICATION,
# passed_with_caveats, ...) counts as not-done.


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _rule(title: str) -> str:
    return f"== {title} " + "=" * max(0, 58 - len(title))


def gate_line() -> str:
    """Active gate, cross-checked across the three files that declare it."""
    sources = {
        "plan_maestro.md": ROOT / "plan_maestro.md",
        "README.md": ROOT / "README.md",
        "final_quality_report.md": ROOT / "ops" / "sted" / "final_quality_report.md",
    }
    found: dict[str, str] = {}
    for name, path in sources.items():
        try:
            m = re.search(r"\bG([0-4])\b", _read(path))
            if m:
                found[name] = "G" + m.group(1)
        except OSError:
            continue
    if not found:
        return "GATE ACTIVO: (no declarado) [!] revisar plan_maestro.md"
    values = set(found.values())
    gate = sorted(values)[0]
    if len(values) > 1:
        detail = ", ".join(f"{k}={v}" for k, v in found.items())
        return f"GATE ACTIVO: {gate} [!] DISCREPANCIA entre fuentes -> {detail}"
    return f"GATE ACTIVO: {gate} (fuente: plan_maestro.md, coherente en 3 archivos)"


def _classify(status: str) -> str:
    s = status.strip().upper()
    if s in DONE_TOKENS:
        return "done"
    if s in FAIL_TOKENS:
        return "fail"
    return "pending"


def traceability_lines() -> list[str]:
    path = ROOT / "ops" / "sted" / "traceability_matrix.csv"
    try:
        with path.open(encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
    except OSError as exc:
        return [f"TRAZABILIDAD: [!] no se pudo leer ({exc})"]

    buckets = {"claim": [0, 0, 0], "equation": [0, 0, 0], "figure": [0, 0, 0], "reference": [0, 0, 0]}
    idx = {"done": 0, "pending": 1, "fail": 2}
    for row in rows:
        rtype = (row.get("type") or "").strip().lower()
        if rtype == "decision":
            continue  # scaffold row, not project evidence
        if rtype not in buckets:
            continue
        buckets[rtype][idx[_classify(row.get("status", ""))]] += 1

    out = ["CLAIMS / EVIDENCIA (traceability_matrix.csv):"]
    labels = {"claim": "claims   ", "equation": "ecuaciones", "figure": "figuras  ", "reference": "refs     "}
    for key in ("claim", "equation", "figure", "reference"):
        done, pending, fail = buckets[key]
        total = done + pending + fail
        if total == 0:
            continue
        flag = " [!]" if (key == "claim" and done < total) else ""
        failtxt = f" - {fail} fail" if fail else ""
        out.append(f"  {labels[key]}: {done}/{total} listos - {pending} pendientes{failtxt}{flag}")
    return out


def test_lines() -> list[str]:
    path = ROOT / "ops" / "sted" / "test_plan.md"
    try:
        text = _read(path)
    except OSError as exc:
        return [f"TESTS: [!] no se pudo leer ({exc})"]

    done = pending = fail = 0
    pending_ids: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not re.match(r"^\|\s*T-", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        test_id, status = cells[0], cells[-1]
        kind = _classify(status)
        if kind == "done":
            done += 1
        elif kind == "fail":
            fail += 1
            pending_ids.append(test_id + "(FAIL)")
        else:
            pending += 1
            pending_ids.append(test_id)
    total = done + pending + fail
    if total == 0:
        return ["TESTS: [!] no se detectaron filas T- en test_plan.md"]
    head = f"TESTS (test_plan.md): {done}/{total} passed - {pending} pendientes"
    if fail:
        head += f" - {fail} FAIL"
    lines = [head]
    if pending_ids:
        shown = ", ".join(pending_ids[:8])
        more = f" (+{len(pending_ids) - 8} mas)" if len(pending_ids) > 8 else ""
        lines.append(f"  pendientes: {shown}{more}")
    return lines


def decision_lines(n: int = 3) -> list[str]:
    path = ROOT / "ops" / "sted" / "decision_log.md"
    try:
        text = _read(path)
    except OSError as exc:
        return [f"DECISIONES: [!] no se pudo leer ({exc})"]

    blocks = re.split(r"^## (DEC-[\w-]+)\s*$", text, flags=re.MULTILINE)
    # blocks = [preamble, id1, body1, id2, body2, ...]
    entries: list[tuple[str, str, str]] = []
    for i in range(1, len(blocks), 2):
        dec_id = blocks[i].strip()
        body = blocks[i + 1] if i + 1 < len(blocks) else ""
        date = _field(body, "Date")
        nxt = _field(body, "Next action")
        entries.append((dec_id, date, nxt))
    if not entries:
        return ["DECISIONES: [!] ninguna entrada DEC- encontrada"]

    out = [f"ULTIMAS DECISIONES ({len(entries)} en total):"]
    for dec_id, date, _ in entries[-n:]:
        out.append(f"  {dec_id} ({date or 's/f'})")
    # last non-empty Next action = the live pointer for what to do next
    for dec_id, _, nxt in reversed(entries):
        if nxt:
            out.append(f"  -> Next action ({dec_id}): {_truncate(nxt, 140)}")
            break
    return out


def _field(body: str, name: str) -> str:
    m = re.search(rf"^{re.escape(name)}:\s*(.+)$", body, flags=re.MULTILINE)
    return m.group(1).strip() if m else ""


def _truncate(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def git_line() -> str:
    def run(args: list[str]) -> str:
        return subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=8
        ).stdout.strip()

    try:
        branch = run(["rev-parse", "--abbrev-ref", "HEAD"]) or "?"
        head = run(["rev-parse", "--short", "HEAD"]) or "?"
        porcelain = run(["status", "--porcelain"])
        dirty = len([ln for ln in porcelain.splitlines() if ln.strip()])
    except (OSError, subprocess.SubprocessError) as exc:
        return f"GIT: [!] no disponible ({exc})"
    state = "limpio" if dirty == 0 else f"{dirty} archivo(s) sin commitear"
    return f"GIT: {branch} @ {head} - {state}"


def stop_condition_lines() -> list[str]:
    """Light checks against the CLAUDE.md stop-condition contract."""
    issues: list[str] = []

    gap = ROOT / "research" / "gap_matrix.md"
    if not gap.exists():
        issues.append("no existe research/gap_matrix.md (stop: sin gap matrix)")
    else:
        try:
            body = _read(gap)
            if "PENDING_COMPLETION" in body and len(body.strip()) < 400:
                issues.append("research/gap_matrix.md aun es plantilla vacia")
        except OSError:
            pass

    # README promises reproducible artifacts under these paths.
    for rel in ("outputs", "scripts"):
        if not (ROOT / rel).exists():
            issues.append(f"{rel}/ prometido en README pero no existe")

    if not issues:
        return ["STOP CONDITIONS: ninguna activa"]
    return ["STOP CONDITIONS / HUECOS:"] + [f"  [!] {i}" for i in issues]


def next_read_line(gate_text: str) -> str:
    hint = {
        "G0": "STED-RW_Lean.md (definir contexto y evidencia)",
        "G1": "plan_maestro.md (cerrar arquitectura, casos, variables y metricas)",
        "G2": "research/gap_matrix.md + traceability_matrix.csv (cerrar claims/bib)",
        "G3": "paper/main.tex + test_plan.md (metodologia y pruebas de modo)",
        "G4": "test_plan.md (T-SIM-*) + traceability (marcar SUPPORTED con evidencia)",
    }
    m = re.search(r"\bG[0-4]\b", gate_text)
    gate = m.group(0) if m else "G1"
    return f"SIGUIENTE LECTURA: {hint.get(gate, hint['G1'])}"


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass

    g = gate_line()
    sections: list[str] = []
    sections.append(_rule("STED-RW SESSION BOOT (estado derivado, no almacenado)"))
    sections.append(g)
    sections.append("")
    sections.extend(traceability_lines())
    sections.append("")
    sections.extend(test_lines())
    sections.append("")
    sections.extend(decision_lines())
    sections.append("")
    sections.append(git_line())
    sections.extend(stop_condition_lines())
    sections.append("")
    sections.append(next_read_line(g))
    sections.append("Contexto completo bajo demanda: CLAUDE.md 'Read first'.")
    sections.append(_rule(""))

    print("\n".join(sections))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # never break the SessionStart hook
        print(f"[session_boot] fallo no fatal: {exc}")
        sys.exit(0)
