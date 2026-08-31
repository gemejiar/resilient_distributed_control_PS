---
name: audit-methodology
description: Perform a rigorous methodology audit for a proposed or ongoing study. Use for research design, experiments, validation plans, forecasting, control, optimization, machine learning, or comparative studies. Identifies hidden assumptions, leakage risks, weak baselines, invalid metrics, and design gaps.
---

# Audit Methodology

Use this skill to perform a rigorous methodological audit of a research study, proposal, experiment, or planned paper.

This skill is especially useful for:
- machine learning experiments,
- forecasting studies,
- control and optimization studies,
- benchmark design,
- simulation or HIL validation planning,
- paper methods sections before submission.

## When to use

Use this skill when the user asks to:
- audit a methodology,
- check whether an experimental design is rigorous,
- identify hidden assumptions,
- detect leakage or split errors,
- verify whether baselines and metrics are appropriate,
- stress-test the validity of a proposed study.

Typical trigger phrases:
- "audit this methodology"
- "check my experimental design"
- "is this method rigorous?"
- "find methodological weaknesses"
- "look for leakage and baseline problems"
- "review this research design"

## When not to use

Do not use this skill when:
- the user only wants writing polish,
- the task is only full-paper review,
- there is no study design, plan, or method to evaluate,
- the task is purely implementation review.

## Required inputs

If not already provided, ask for:
1. Description of the study or proposed methodology.
2. Type of problem: classification, control, optimization, prediction, comparison, etc.
3. Whether there is a paper draft, formal proposal, or only an idea.

Optional but helpful:
- data split strategy,
- metrics,
- baselines,
- validation environment,
- timeline or deployment target,
- target venue.

## Audit objectives

Explicitly assess:
- undeclared assumptions,
- risk of data leakage,
- absence or weakness of baselines,
- invalid train, validation, or test partitioning,
- temporal split problems,
- inappropriate metrics,
- weak validation protocol,
- threats to internal validity,
- threats to external validity,
- gaps in reproducibility,
- mismatch between claims and evidence plan.

For engineering and power or energy studies, also consider:
- physical realism,
- operational constraints,
- units and dimensional consistency when relevant,
- deployment realism,
- adequacy of simulation versus HIL or field validation,
- robustness across operating conditions.

## Audit procedure

### Step 1. Establish methodological context
Summarize:
- study goal,
- problem type,
- available material,
- claimed method,
- validation strategy if provided.

### Step 2. Inspect assumptions
List explicit and implicit assumptions.
Highlight assumptions that are untested, unrealistic, or hidden.

### Step 3. Inspect design quality
Assess:
- dataset or scenario selection,
- baseline appropriateness,
- split strategy,
- ablation logic,
- metric-task consistency,
- fairness of comparisons,
- statistical validity where relevant.

### Step 4. Inspect validation and claims
Check whether:
- evaluation supports the claims,
- robustness is tested,
- the protocol is reproducible,
- deployment implications are justified.

### Step 5. Produce actionable audit
Do not merely say "needs work." Identify where and how it fails.

## Output format

### 1. Methodology summary
- Study goal
- Problem type
- Claimed approach
- Validation plan

### 2. Main risks
- Bullet list of the most serious weaknesses

### 3. Detailed audit
Use these categories when applicable:
- Assumptions
- Data leakage / partitioning
- Baselines and comparisons
- Metrics
- Validation protocol
- Internal validity
- External validity
- Reproducibility
- Claim-evidence alignment

### 4. Recommended fixes
Group into:
- **Critical**
- **Important**
- **Optional improvements**

### 5. Bottom-line verdict
Choose one:
- **Methodologically solid**
- **Promising but under-specified**
- **Needs substantial redesign**
- **Methodologically weak in current form**

Then justify the verdict clearly.

## Audit rules

- Do not validate if there are real flaws.
- Be direct about leakage, weak comparisons, or invalid metrics.
- Distinguish between confirmed flaws and likely risks.
- Do not invent experimental details.
- Prefer actionable criticism over generic caution.

## Definition of done

This skill is complete when:
- the study is clearly framed,
- methodological risks are explicitly identified,
- critical design flaws are not softened,
- recommendations are actionable,
- a bottom-line verdict is given.
