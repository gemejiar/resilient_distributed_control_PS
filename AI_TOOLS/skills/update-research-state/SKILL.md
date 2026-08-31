---
name: update-research-state
description: Update progress.md, research_state.md, and test_oracle.md in a controlled way after a research session, literature scan, benchmark run, or editorial decision. Use when the project state must be synchronized, failed paths preserved, and next actions clarified without losing traceability.
---

# Update Research State

Use this skill to update the research-control artifacts of an active project in a disciplined and auditable way.

This skill is designed for projects that maintain:
- `08_session_memory/progress.md`
- `08_session_memory/research_state.md`
- `08_session_memory/test_oracle.md`

It keeps project state synchronized across short-term progress, long-term research state, and validation criteria.

## When to use

Use this skill when the user asks to:
- update project state after a session,
- register progress after literature exploration,
- record benchmark progress,
- preserve failed attempts and decisions,
- synchronize open questions and next actions,
- revise the test oracle after methodology or result changes,
- avoid repeating dead ends across sessions.

Typical trigger phrases:
- "update the research state"
- "log today's progress"
- "sync progress and research state"
- "record what changed"
- "update the oracle"
- "register failures and next steps"

## When not to use

Do not use this skill when:
- the task is only to summarize a document,
- the task is only manuscript drafting,
- the project does not use these state files,
- there is no new information to record,
- the user wants free-form notes rather than structured project state.

## Files this skill manages

Expected files:
- `08_session_memory/progress.md`
- `08_session_memory/research_state.md`
- `08_session_memory/test_oracle.md`

If one or more files do not exist:
1. report it explicitly,
2. do not invent prior state,
3. propose minimal safe initialization only if the user requests it.

## Core purpose of each file

### `progress.md`
Short-horizon operational progress.
Use it to record:
- current objective,
- recent literature reviewed,
- candidate hypotheses,
- benchmark status,
- completed tasks,
- failed attempts,
- decisions,
- open questions,
- next actions.

### `research_state.md`
Durable project state.
Use it to record:
- stable project identity,
- current phase and strategic status,
- literature state,
- candidate contributions,
- benchmark and reproducibility state,
- failed paths,
- decisions with consequences,
- known limitations,
- expert-level open questions.

### `test_oracle.md`
Validity and completion criteria.
Use it to record:
- what counts as valid output,
- what artifacts must be reproducible,
- quantitative or qualitative thresholds,
- failure conditions,
- claim-evidence checks,
- stop conditions that block declaring success.

## Required inputs

If not already provided, request the minimum needed:
1. What was completed?
2. What is still in progress?
3. What failed, stalled, or was rejected?
4. What decisions were made?
5. Did the validation criteria or success criteria change?
6. Are there new open questions or new next actions?

If the user says "update directly", proceed with best-effort extraction from the available conversation or materials, but explicitly mark uncertain updates.

## Update strategy

### Step 1. Read current state
Read the existing versions of:
- `08_session_memory/progress.md`
- `08_session_memory/research_state.md`
- `08_session_memory/test_oracle.md`

Before editing, identify:
- stale sections,
- contradictions,
- duplicated information,
- missing status changes,
- newly invalid assumptions.

### Step 2. Build an update map
Classify new information into:
- completed work,
- ongoing work,
- blocked work,
- failed attempts,
- decisions,
- state changes,
- oracle changes.

Do not mix these categories.

### Step 3. Preserve history correctly
Apply these rules:
- do not erase failed paths,
- do not silently overwrite strategic decisions,
- compress old information if needed, but preserve the meaning,
- promote tentative claims only if evidence now supports them,
- remove or downgrade unsupported claims when needed.

### Step 4. Update each file deliberately

#### 4A. Update `progress.md`
Update:
- Current objective
- Current status snapshot
- Literature reviewed
- Candidate hypotheses
- Benchmark status
- Completed tasks
- Failed attempts and why they failed
- Decisions taken
- Known limitations
- Open questions
- Next actions

#### 4B. Update `research_state.md`
Update:
- Current objective
- State summary
- Literature state
- Candidate hypotheses and contribution options
- Experimental or benchmark state
- Failed paths
- Decisions taken
- Known limitations
- Open questions requiring expert judgment
- Immediate next steps

Only update project identity if the project itself changed.

#### 4C. Update `test_oracle.md`
Update this file only if the criteria for validity changed.

Examples:
- a new benchmark is now required,
- an artifact became mandatory to regenerate,
- a threshold changed for justified reasons,
- a new failure condition was discovered,
- a claim-evidence dependency became clearer,
- a previous acceptance criterion is no longer valid.

Do not modify thresholds casually after seeing results. If a threshold changes, record why.

## Output behavior

Before writing, present a concise structured update plan.

Use this format:

### Proposed updates
#### `progress.md`
- ...
- ...

#### `research_state.md`
- ...
- ...

#### `test_oracle.md`
- ...
- ...

Then:
- if the user requested review before writing, wait for confirmation,
- if the user requested direct update, apply the changes.

## Write policy

When editing:
- preserve headings unless there is a strong reason to change them,
- keep formatting consistent,
- prefer updates inside existing sections over ad hoc appendices,
- keep entries factual and audit-friendly,
- use explicit uncertainty markers when the source state is incomplete.

## Consistency checks

Before finalizing, verify:
- completed tasks in `progress.md` are reflected in `research_state.md` when strategically relevant,
- failed attempts are not erased,
- open questions and next actions are not contradictory,
- `test_oracle.md` still matches the current benchmark or manuscript logic,
- no claim is upgraded without evidence.

## Output format after writing

Return:
1. What changed in `progress.md`
2. What changed in `research_state.md`
3. What changed in `test_oracle.md`
4. Any unresolved uncertainty
5. Any manual follow-up needed

## Rules

- Do not invent progress that did not happen.
- Do not erase failed attempts to make the project look cleaner.
- Do not update the oracle unless the validation logic truly changed.
- Do not convert uncertain ideas into settled decisions.
- Do not overwrite strategic history without preserving its rationale.

## Definition of done

This skill is complete when:
- the three state files are synchronized with the latest known project state,
- failed paths and decisions remain traceable,
- next actions are explicit,
- the oracle reflects the current definition of valid progress,
- uncertainties are clearly marked rather than hidden.
