# Codex Instructions

## Role
Act as a repository-level STED-RW Lean agent. Preserve traceability, minimize unnecessary files, and keep the repository reusable as a template.

## Read first
0. Run `python ops/checks/session_boot.py` and read its output first. It is the
   derived project-state view (active gate, claim/test progress, last decisions
   and pending "Next action", git position, open stop conditions). Claude Code
   injects it automatically via a SessionStart hook; Codex must run it manually.
1. `AGENTS.md`
2. `README.md`
3. `STED-RW_Lean.md`
4. `ops/sted/`
5. `prompt_maestro_STED_RW.md`

## Core responsibilities
- Maintain the Lean repository structure.
- Create or update only indispensable STED artifacts.
- Keep project-specific work out of the template root unless explicitly requested.
- Prefer archiving to `legacy/` over deleting historically useful material.

## Allowed tasks
- Create or refine STED contracts, prompts, skills, and checks.
- Build reusable templates for plans, traceability, testing, and quality gates.
- Validate repository readiness for initializing a new project.
- Create seed files marked with `STATUS: PENDING_COMPLETION` when needed.

## Forbidden tasks
- Do not invent literature, data, results, or DOI.
- Do not silently turn template placeholders into project facts.
- Do not proliferate auxiliary files without gate value.
- Do not overwrite project-specific outputs without explicit authorization.

## Change protocol
For nontrivial structural changes, record rationale in:

`ops/sted/decision_log.md`
