# STED Decision Log

STATUS: PENDING_COMPLETION

One entry per gate evaluation, phase transition, or integrator-level decision.
Keep entries short and evidence-anchored. This file is a project record, not scientific evidence.

## Decision Entry Template

```markdown
## DEC-XXX
Date:
Gate:
Decision:
Justification:
Evidence reviewed:
Blockers or limitations:
Responsible:
Status:
Next action:
```

## DEC-000 (EXAMPLE — delete before use)
Date: YYYY-MM-DD
Gate: G0
Decision: Example decision. Replace this entry with the first real project decision.
Justification: Illustrates the expected format; carries no project meaning.
Evidence reviewed: plan_maestro.md
Blockers or limitations: None.
Responsible: Integrator
Status: example
Next action: Remove this entry and log real gate decisions below.

## DEC-001
Date: 2026-08-30
Gate: G1
Decision: Adopt a single canonical status vocabulary for claims, evidence, and references across the template: VERIFIED, PARTIALLY_VERIFIED, PENDING_EVIDENCE, BLOCKED_BY_EVIDENCE, REFERENCE_NOT_VERIFIED, OBSOLETE, OUT_OF_SCOPE. Used identically in prose markers and in the `status` column of `ops/sted/traceability_matrix.csv`. `check_claim_evidence.py` compares case-insensitively; canonical written form is upper-case. Legacy short tokens (verified/pending/blocked/obsolete/out_of_scope) are retired.
Justification: `AGENTS.md` promoted `PENDING_EVIDENCE`, `BLOCKED_BY_EVIDENCE`, `REFERENCE_NOT_VERIFIED` while `check_claim_evidence.py`, `STED-RW_Lean.md` section 13.3, `prompt_maestro_STED_RW.md`, and the IEEE/Elsevier skill used a divergent lowercase set. An agent following AGENTS.md could write a status the checker rejects.
Evidence reviewed: AGENTS.md, ops/checks/check_claim_evidence.py, zPLantilla_STED_RW/STED-RW_Lean.md, zPLantilla_STED_RW/prompt_maestro_STED_RW.md, AI_TOOLS/skills/{sted-rw,ieee_elsevier_paper_skill}/SKILL.md, ops/sted/traceability_matrix.csv.
Blockers or limitations: Real projects created from an earlier template revision must migrate existing matrix rows to the new tokens.
Responsible: Integrator
Status: VERIFIED
Next action: None; applied. Propagate the same vocabulary if new checkers or skills reference claim status.
