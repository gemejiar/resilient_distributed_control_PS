---
name: sted-rw
description: Run work under the STED-RW Lean template using minimum artifacts, traceability, gates, and an integrator-first workflow.
---

# STED-RW Lean Skill

## Use this skill when
- Initializing a new project from this template
- Auditing whether a repository still follows Lean structure
- Deciding whether a new artifact is justified
- Checking if scope, evidence, tests, and writing are aligned

## Read first
1. `AGENTS.md`
2. `plan_maestro.md`
3. Only the artifacts directly relevant to the task (for example `ops/sted/traceability_matrix.csv`, `ops/sted/decision_log.md`).
4. `zPLantilla_STED_RW/STED-RW_Lean.md` and `zPLantilla_STED_RW/prompt_maestro_STED_RW.md` only when initializing a project, substantially restructuring `plan_maestro.md`, or resolving ambiguity about STED-RW gates.

## Core rules
- Keep the active structure minimal.
- Prefer updating an existing core artifact over creating a new file.
- Use `STATUS: PENDING_COMPLETION` for empty but required templates.
- For claim/evidence/reference status, use only the canonical vocabulary (`VERIFIED`, `PARTIALLY_VERIFIED`, `PENDING_EVIDENCE`, `BLOCKED_BY_EVIDENCE`, `REFERENCE_NOT_VERIFIED`, `OBSOLETE`, `OUT_OF_SCOPE`), both in prose and in the `status` column of the traceability matrix.
- Escalate to the integrator when scope or project type changes.

## Minimum active artifacts
- `ops/sted/traceability_matrix.csv`
- `ops/sted/decision_log.md`

## Stop conditions
- Missing source-of-truth contracts
- Conflicting active plans
- Unjustified artifact proliferation
