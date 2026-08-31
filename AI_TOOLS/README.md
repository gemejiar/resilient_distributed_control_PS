# AI_TOOLS/ — Reusable capability library

`AI_TOOLS/` is the canonical project-local library of reusable agent
capabilities: skills, agents, subagents, commands, prompts, hooks, and the
user profile.

It is **operational tooling, not scientific source of truth**. Nothing here
overrides `plan_maestro.md`, `AGENTS.md`, or project evidence. A capability
must never silently create optional artifacts, change scope, strengthen
claims, or override evidence.

## Discovery discipline

- Do **not** preload or scan the whole tree.
- Before a substantial task, decide whether one capability materially matches
  the work. If yes, open that capability and only the files it explicitly
  requires. If no, work directly under `AGENTS.md` and `plan_maestro.md`.
- Combine capabilities only when the task genuinely needs distinct ones.
- Physical presence here does not mean the runtime has natively registered a
  skill. When native skill discovery is unavailable, read and follow the
  capability file directly.

## Layout

| Path | Contents | Use |
|------|----------|-----|
| `skills/` | Packaged skills, one folder per skill with `SKILL.md` (+ optional `references/`, `templates/`, `agents/`, `examples/`). | Primary capability set. Authoritative inventory: [`skills/README.md`](skills/README.md). |
| `agents/` | Standalone agent definitions: `*.toml` (Codex-style, with `developer_instructions`) and `sted_integrator.md` (the mandatory STED-RW gate integrator). | Delegated, self-contained roles run with a clean context. |
| `subagents/` | Prompt bodies invoked *by* a command or skill (e.g. `code_reviewer.md` for `/review-code`), not launched directly. | Internal building blocks. |
| `commands/` | Slash-command entry points (`*.md`) that orchestrate a skill / subagent and prompt the user for the inputs it needs. | User-triggered workflows. |
| `prompts/` | Short reusable operating prompts (`sted-execute.md`, `sted-verify.md`). | Session bootstrap / mode-setting. |
| `hooks/` | Advisory, non-blocking edit-time checks (`pre_edit_check`, `post_edit_check`) with `.py` implementation and `.md` spec. Wired in `.claude/settings.json`. | Guardrails during editing. |
| `profile/` | User profile, expertise map, writing style, quick reference. | Personalization context for writing/review tasks. |

## Routing

| Task | Capability |
|------|------------|
| Methodology or experiment design | `skills/scientific_methodology` |
| Scientific code generation, debugging, review | `skills/scientific-coding` (or `/review-code`) |
| Manuscript peer review | `skills/paper-review` |
| Scientific writing / rewriting | `skills/gabriel_scientific_writer` |
| Citation verification, bibliography | `skills/citation-management` |
| Literature search / topic scouting | `skills/bibliometric-search`, `agents/literature-scout.toml` |
| Publishable-gap analysis | `skills/find-publishable-gaps`, `skills/editorial-gap-detection` |
| STED-RW phase-gate decision | `agents/sted_integrator.md` |
| LaTeX build (IEEE/Elsevier) | `skills/latex-paper-en`, `skills/ieee_elsevier_paper_skill` |
| Figures / statistics | `skills/scientific-visualization`, `skills/statistical-analysis` |

When routing conflicts with `plan_maestro.md`, `AGENTS.md`, or evidence, the
project documents win.

## Maintenance

- Adding or removing a skill requires updating [`skills/README.md`](skills/README.md).
- A skill folder without a `SKILL.md` in the standard `--- name / description ---`
  frontmatter format is not a formal runtime capability.
- Loose `*.md` notes at the root of `skills/` are notes, not skills.
