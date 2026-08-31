---
name: review-code
description: Review scientific and engineering code with a structured technical review. Use when assessing implementation quality, correctness, testing, scientific rigor, reproducibility, or alignment against requirements, plans, diffs, or changed files. Best for Python, MATLAB, simulation, optimization, control, and research code.
---

# Review Code

Use this skill when the user wants a rigorous review of scientific or engineering code, especially when the task requires:
- checking correctness against a plan or specification,
- identifying methodological or implementation flaws,
- reviewing diffs or changed files,
- assessing testing quality,
- evaluating reproducibility or scientific rigor,
- producing a final verdict with explicit issues and recommendations.

## When to use

Use this skill when the user asks to:
- review code,
- assess whether an implementation is correct,
- compare code against a plan, spec, manuscript, method, or intended workflow,
- identify bugs, weaknesses, design flaws, or missing tests,
- perform a scientific or engineering code audit,
- review a diff before merge or submission.

Typical trigger phrases:
- "review this code"
- "audit this implementation"
- "check whether this matches the method"
- "look for bugs and methodological issues"
- "review the diff"
- "does this implementation follow the plan?"

## When not to use

Do not use this skill when:
- the user mainly wants code generation from scratch,
- the task is primarily manuscript review rather than code review,
- the user wants only a high-level explanation of an algorithm,
- there is no code, diff, file list, or implementation context to inspect.

## Required inputs

If not already provided, ask for the minimum necessary context:
1. What was implemented? A brief description.
2. What requirements, plan, method, or target behavior should it satisfy?
3. What code should be reviewed? Provide diff, files, commit range, or a clear description.
4. What tests exist, and what is their current status?

If one or more items are missing, proceed as far as possible but mark uncertainty explicitly.

## Review objectives

Your review must evaluate:
- correctness,
- alignment with intended requirements,
- scientific or engineering validity,
- code structure and maintainability,
- edge-case handling,
- testing sufficiency,
- reproducibility and traceability,
- potential hidden failure modes.

For research code, explicitly consider:
- units and dimensional consistency when relevant,
- leakage risks,
- time-split or train/test discipline,
- deterministic seeds when appropriate,
- reproducibility of outputs,
- consistency between manuscript claims and implementation.

## Review procedure

### Step 1. Establish scope
Summarize:
- implementation goal,
- expected behavior,
- files or code under review,
- available evidence.

### Step 2. Inspect implementation
Review the relevant code carefully.
Look for:
- logical errors,
- silent failure risks,
- mismatches between code and specification,
- brittle assumptions,
- missing validation,
- unsafe defaults,
- incomplete exception handling,
- dead code or inconsistent interfaces.

### Step 3. Inspect scientific or methodological soundness
When applicable, check:
- whether the implementation matches the described method,
- whether preprocessing, normalization, or scaling is handled correctly,
- whether temporal splits or evaluation protocols avoid leakage,
- whether metrics match the task,
- whether simulation setup preserves physical meaning,
- whether numerical assumptions are explicit and defensible.

### Step 4. Inspect testing
Evaluate:
- whether tests exist,
- whether they exercise critical paths,
- whether edge cases are covered,
- whether regression tests exist,
- whether test names and assertions are meaningful,
- whether the reported testing evidence is enough to trust the implementation.

### Step 5. Produce findings
Each issue must include:
- severity,
- file and line reference when available,
- why it matters,
- a concrete recommendation.

Do not be vague. If something is acceptable, say so clearly.

## Severity scale

Use this scale:
- **Critical**: likely incorrect result, unsafe behavior, severe methodological flaw, or invalid scientific conclusion.
- **Major**: important defect, weak design, missing validation, or significant risk of incorrect use.
- **Minor**: improvement needed, but not likely to invalidate results by itself.
- **Note**: useful suggestion or positive observation.

## Output format

Use this structure:

### 1. Scope reviewed
- Goal
- Reference requirements or plan
- Files / diff / implementation reviewed
- Testing evidence available

### 2. What is working well
- Short bullet list of strengths

### 3. Findings
For each finding use:

**[Severity] Title**  
- Location: `path/to/file:line` or equivalent
- Problem: ...
- Why it matters: ...
- Recommendation: ...

### 4. Testing assessment
- Existing tests
- Gaps
- Confidence level

### 5. Final verdict
Choose one:
- **Acceptable as is**
- **Acceptable with minor changes**
- **Needs substantial revision**
- **Not acceptable in current form**

Then justify the verdict in 3 to 6 sentences.

## Review rules

- Do not invent file names, line numbers, or tests.
- If line numbers are unavailable, state that explicitly.
- Distinguish observed defects from inferred risks.
- Do not approve weak scientific code just because it runs.
- Recognize what is done well.
- If evidence is incomplete, state the limits of the review.

## Definition of done

This skill is complete when:
- the implementation goal is restated,
- findings are specific and actionable,
- methodological risks are explicitly addressed,
- testing adequacy is assessed,
- a final verdict is given without ambiguity.
