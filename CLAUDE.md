# CLAUDE.md

## Purpose

This file contains Claude Code-specific instructions for projects governed by STED-RW Lean.

Shared rules for all agents are defined in `AGENTS.md`.  
Project-specific scientific, technical, or editorial decisions are defined in `plan_maestro.md`.

Do not duplicate those documents here.

## Read first

Before substantial work, read:

1. `AGENTS.md` — shared agent rules and repository governance.
2. `plan_maestro.md` — project scope, methodology, claims, gates, acceptance criteria, and current authorized action.
3. Only the files directly relevant to the requested task.

Read additional artifacts only when required by the task, for example:

- `ops/sted/traceability_matrix.csv` when claims, evidence, figures, tables, references, or tests are affected.
- `ops/sted/decision_log.md` when a methodological, scientific, technical, or editorial decision is being changed or introduced.
- source code, configurations, tests, results, literature, or manuscript files directly relevant to the task.

Do not load the full STED-RW specification during normal work.

Consult `zPLantilla_STED_RW/STED-RW_Lean.md` or `zPLantilla_STED_RW/prompt_maestro_STED_RW.md` only when:

- initializing a project;
- creating or substantially restructuring `plan_maestro.md`;
- resolving ambiguity about STED-RW gates or workflow rules.

## Session bootstrap

If the project provides a session-bootstrap script (for example under `ops/checks/`), run it before substantial work and use its output as derived project state.

If no such script exists, do not create one automatically. Derive the required state from `plan_maestro.md` and the task-relevant artifacts.

## Working model

For each substantial task:

1. Identify the requested outcome.
2. Verify that it is within the scope defined in `plan_maestro.md`.
3. Identify the minimum files needed to perform the task.
4. Inspect the relevant evidence before making scientific or quantitative claims.
5. Make the smallest coherent change that satisfies the task.
6. Run relevant tests or validations when executable artifacts are modified.
7. Update traceability only when the change affects tracked evidence or claims.
8. Update the decision log only when a significant decision is made.
9. Report unresolved blockers instead of inventing missing information.

Do not create additional reports, notes, matrices, or helper files unless they are necessary for execution, reproducibility, traceability, or the final product.

## Writing rules

When producing publication-ready scientific or technical text:

- Use technical English unless the project specifies another language.
- Prefer concise scientific prose appropriate to the target venue.
- Preserve existing LaTeX labels, citations, equations, and cross-references.
- Do not invent references, DOI, results, metrics, or evidence.
- Avoid unsupported novelty, superiority, robustness, optimality, or generalization claims.
- Match claim strength to the available evidence.
- Distinguish clearly between verified results, assumptions, interpretation, and pending evidence.

## Methodology and study-design checks

When the task involves methodology, implementation, experiments, evaluation, or study design, verify the applicable elements defined in `plan_maestro.md`, including as relevant:

1. system or object under study;
2. objective or hypothesis;
3. assumptions and scope;
4. baselines or comparison setup;
5. data, evidence, or measurement layer;
6. core method, model, algorithm, or intervention;
7. implementation platform;
8. acquisition and preprocessing;
9. execution or decision path;
10. evaluation scenarios;
11. metrics and acceptance criteria;
12. reproducibility parameters;
13. limitations and threats to validity.

Do not require an element that the project explicitly marks as not applicable.

## Blocking conditions

Report `BLOCKED` when the requested task cannot be completed reliably because, for example:

- required evidence is missing;
- the requested claim exceeds the available evidence;
- a critical methodological decision remains unresolved;
- required inputs or files cannot be located;
- an executable change cannot be validated sufficiently;
- the requested action conflicts with the frozen project scope.

Do not report `BLOCKED` merely because an optional artifact such as a gap matrix, manuscript, bibliography, or test suite does not exist.

## Repository discipline

- Treat `plan_maestro.md` as the project-specific operational contract.
- Treat `AGENTS.md` as the shared agent-governance contract.
- Prefer modifying existing files over creating new ones.
- Do not silently replace canonical evidence or historical artifacts.
- Keep source code, configuration, evidence, generated results, and publication text logically separated.
- Do not modify raw evidence to make it agree with a desired narrative.
- Do not infer that a file or folder is mandatory unless `AGENTS.md` or `plan_maestro.md` requires it.

## Validation

Use project-provided checks when they exist.

Do not assume that a specific validation command exists in every project.

Run only validations relevant to the files or behavior changed by the current task.

## Delivery

For substantial work, summarize concisely:

- what was inspected;
- what changed;
- validations performed;
- evidence or traceability affected;
- unresolved blockers, if any;
- the next relevant action when it follows directly from the project plan.