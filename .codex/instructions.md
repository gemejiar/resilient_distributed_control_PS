# Codex Instructions

Codex operates under the same governance as every other agent in this repository.

## Read first

1. `AGENTS.md` — shared agent rules and repository governance.
2. `plan_maestro.md` — project scope, methodology, claims, gates, and current authorized action.
3. Only the files directly relevant to the requested task.

Consult `zPLantilla_STED_RW/STED-RW_Lean.md` or `zPLantilla_STED_RW/prompt_maestro_STED_RW.md`
only when initializing a project, substantially restructuring `plan_maestro.md`, or
resolving ambiguity about STED-RW gates.

## Working rules

- Follow the source-of-truth hierarchy defined in `AGENTS.md`.
- Make the smallest coherent change that satisfies the task.
- Prefer modifying existing files over creating new ones.
- Update `ops/sted/traceability_matrix.csv` and `ops/sted/decision_log.md` only when the
  change affects tracked evidence/claims or introduces a significant decision.
- Do not invent literature, data, results, or DOI.
- Report `BLOCKED` instead of inventing missing information.
