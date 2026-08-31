---
name: review-paper
description: Review a scientific paper or draft manuscript in structured journal-review style. Use for journal submissions, conference papers, assigned reviews, literature triage, or revision rounds. Supports quick, standard, revision, targeted, and summary modes.
---

# Review Paper

Use this skill to perform a structured academic review of a scientific paper, manuscript draft, extended abstract, or literature item.

This skill is suitable for:
- your own paper drafts,
- peer-review style evaluation,
- journal or conference readiness checks,
- revision after author response,
- targeted reviews of one weakness,
- structured literature digestion.

## When to use

Use this skill when the user asks to:
- review a paper,
- assess novelty, rigor, clarity, experiments, or writing,
- simulate a journal review,
- evaluate whether a paper is publishable,
- review a revised manuscript,
- summarize a paper in review format.

Typical trigger phrases:
- "review this paper"
- "act as a journal reviewer"
- "evaluate this manuscript"
- "is this ready for submission?"
- "re-review after revision"
- "check the methodology and writing"

## When not to use

Do not use this skill when:
- the task is only to rewrite one section,
- the task is only bibliography formatting,
- the input is code rather than a manuscript,
- the user wants only a short abstract summary with no critical review.

## Review modes

Choose the lightest mode that fits the request.

| Mode | When to use |
|---|---|
| `quick` | Fast triage. Contribution, gap, fatal flaws, go/no-go. |
| `standard` | Full paper review. Methodology, experiments, writing, contribution, evidence. |
| `revision` | Re-review after author response or revised manuscript. |
| `targeted` | Focus on one issue such as baselines, statistics, novelty, or writing. |
| `summary` | Structured digest for literature review context. Not a critical peer review. |

Default:
- use `standard` for own drafts or journal submissions,
- use `quick` for rapid filtering,
- use `revision` only when original review plus revised material exist.

## Required inputs

If not already provided, ask for:
1. Paper content: PDF, pasted text, or section excerpts.
2. Target venue, if relevant.
3. Review mode, if the objective is ambiguous.
4. Any specific concerns the user wants emphasized.

If the user provides no mode and the context is a submission-quality assessment, default to `standard`.

## Review dimensions

Evaluate, when applicable:
- novelty and contribution,
- problem framing and literature positioning,
- methodological rigor,
- experimental design,
- baselines and comparisons,
- reproducibility,
- clarity of figures, tables, and equations,
- quality of writing,
- validity of claims,
- fit to venue.

For engineering and scientific manuscripts, explicitly assess:
- whether assumptions are declared,
- whether metrics and comparisons are adequate,
- whether results support the claims,
- whether threats to validity are addressed,
- whether deployment or practical relevance is overstated.

## Review procedure

### Step 1. Establish context
Summarize:
- paper topic,
- type of contribution,
- target venue if known,
- review mode,
- material received.

### Step 2. Read for structure and central claim
Identify:
- main problem,
- claimed contribution,
- methodological core,
- evidence supporting the contribution.

### Step 3. Evaluate by selected mode
For `quick`:
- assess contribution, gap, and fatal flaws only.

For `standard`:
- review all major sections and logic chain from problem to conclusion.

For `revision`:
- compare original concerns versus current manuscript.

For `targeted`:
- focus deeply on the selected weakness while still noting fatal issues elsewhere.

For `summary`:
- produce a structured digest, but still flag major weaknesses if obvious.

### Step 4. Produce structured findings
Be explicit, critical, and actionable.
Do not validate weak work merely because the topic is interesting.

## Output format

### 1. Overall assessment
- Topic and contribution in 2 to 4 sentences
- Review mode used
- Fit to target venue if relevant

### 2. Main strengths
- Bullet list

### 3. Main weaknesses
- Bullet list

### 4. Section-wise or theme-wise findings
Suggested dimensions:
- Novelty and positioning
- Methodology
- Experimental design / validation
- Results and claims
- Writing and presentation
- Reproducibility

### 5. Recommendation
Use one:
- **Strong accept**
- **Accept**
- **Weak accept**
- **Major revision**
- **Reject**

Then justify clearly.

### 6. Actionable revision list
Group into:
- **Critical**
- **Important**
- **Minor**

## Review rules

- Do not invent missing content.
- If only partial text is provided, state that the review is partial.
- Separate observed weaknesses from inferred concerns.
- Point out unsupported claims directly.
- Preserve reviewer tone: technical, direct, fair.
- When the paper is the user’s own, optimize for improvement, not politeness theater.

## Definition of done

This skill is complete when:
- the selected review mode is clear,
- strengths and weaknesses are explicit,
- methodology and evidence are assessed,
- a recommendation is provided,
- revision actions are prioritized.
