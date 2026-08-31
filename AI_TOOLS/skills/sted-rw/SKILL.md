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
1. `STED-RW_Lean.md`
2. `prompt_maestro_STED_RW.md`
3. `ops/sted/`
4. `AGENTS.md`

## Core rules
- Keep the active structure minimal.
- Prefer updating an existing core artifact over creating a new file.
- Use `STATUS: PENDING_COMPLETION` for empty but required templates.
- Use `PENDING_EVIDENCE` when a claim or field lacks verification.
- Escalate to the integrator when scope or project type changes.

## Minimum active artifacts
- `ops/sted/traceability_matrix.csv`
- `ops/sted/decision_log.md`

## Stop conditions
- Missing source-of-truth contracts
- Conflicting active plans
- Unjustified artifact proliferation
