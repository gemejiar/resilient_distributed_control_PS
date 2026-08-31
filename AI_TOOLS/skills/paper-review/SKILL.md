---
name: paper-review
description: >
  Rigorous scientific peer-review workflow for evaluating manuscripts, revisions,
  methodologies, experiments, figures, tables, claims, novelty, reproducibility,
  and editorial readiness. Use when asked to review, audit, critique, evaluate,
  red-team, or assess a scientific paper or substantial scientific draft.
---

# Paper Review Skill

## Purpose

Perform a rigorous, evidence-based scientific review that behaves like an expert peer reviewer rather than a validator.

The review must identify real weaknesses, distinguish critical from cosmetic issues, and propose the minimum evidence or correction needed to resolve each problem.

The objective is not to maximize criticism. The objective is to maximize:

- scientific validity;
- methodological soundness;
- reproducibility;
- claim-evidence alignment;
- novelty defensibility;
- editorial clarity;
- usefulness of the review to authors or editors.

## When to use

Use this skill when asked to:

- review a scientific manuscript;
- evaluate a journal or conference paper;
- audit a methodology section;
- critique an experimental design;
- assess novelty or contribution;
- review a revision before resubmission;
- compare reviewer comments against a revised manuscript;
- perform a scientific red-team review;
- assess whether results support the conclusions;
- evaluate figures, tables, equations, or reproducibility in context.

## When not to use

Do not invoke the full workflow for:

- minor grammar corrections;
- isolated sentence rewriting;
- formatting-only edits;
- a single citation-format correction;
- casual technical questions that do not require manuscript-level assessment.

For narrow requests, apply only the relevant review dimension.

---

## Core principles

1. **Be critical, not adversarial.**
2. **Evaluate evidence, not author intent.**
3. **Do not invent missing experiments, results, citations, or prior work.**
4. **Do not strengthen or weaken claims without explaining why.**
5. **Separate fatal flaws, major issues, minor issues, and editorial issues.**
6. **Do not treat novelty as established unless closest prior work has been checked.**
7. **Do not infer reproducibility from polished presentation.**
8. **Do not accept a result merely because it is numerically better.**
9. **A fair baseline is part of the evidence.**
10. **A limitation that invalidates a central claim is not a cosmetic limitation.**

---

## Required inputs

Use the material available for the task. Typical inputs include:

- manuscript;
- supplementary material;
- reviewer comments;
- response-to-reviewers document;
- source code;
- figures and tables;
- experiment logs;
- datasets;
- bibliography;
- journal or conference requirements;
- `plan_maestro.md` when reviewing an active project repository.

If a required element is unavailable, explicitly state the limitation.

Do not silently assume access to missing files.

---

## Review modes

Choose the narrowest mode that satisfies the request.

### Mode A — Full peer review

Use for complete manuscript assessment.

Covers:

1. problem definition;
2. contribution;
3. novelty;
4. literature positioning;
5. methodology;
6. theoretical soundness;
7. experimental design;
8. baselines;
9. metrics;
10. statistics;
11. results;
12. reproducibility;
13. threats to validity;
14. figures and tables;
15. writing and organization;
16. claims and conclusions;
17. editorial recommendation.

### Mode B — Methodology audit

Use when the task focuses on scientific design.

Prioritize:

- system definition;
- assumptions;
- data or measurements;
- baselines;
- algorithm;
- implementation;
- scenarios;
- metrics;
- acceptance criteria;
- reproducibility;
- limitations.

### Mode C — Revision audit

Use after peer review.

For each reviewer comment:

1. identify the requested change;
2. locate the manuscript response;
3. determine whether the change is complete;
4. check whether new inconsistencies were introduced;
5. classify as:
   - resolved;
   - partially resolved;
   - unresolved;
   - resolved but creates secondary issue.

### Mode D — Claim audit

Use when asked whether claims are justified.

For each critical claim:

- exact wording;
- required evidence;
- available evidence;
- missing evidence;
- allowed wording;
- excessive wording;
- status.

### Mode E — Figure/table audit

Check:

- source data;
- units;
- labels;
- legends;
- visual scaling;
- statistical representation;
- consistency with text;
- whether caption is self-contained;
- whether the figure actually supports the associated claim.

---

## Review workflow

### Step 1 — Establish the paper's actual claim

Identify:

- problem addressed;
- proposed method or contribution;
- target use case;
- claimed novelty;
- claimed improvement;
- claimed scope of generalization.

Do not rely only on the abstract.

Cross-check abstract, introduction, methodology, results, and conclusion.

### Step 2 — Determine the closest scientific comparison

Ask:

- What prior work is closest in problem formulation?
- What prior work is closest in method?
- What prior work is closest in experimental setup?
- Are the selected baselines scientifically appropriate?
- Is the paper comparing against weak or outdated references?

If literature is not available, mark novelty assessment as limited.

Do not invent omitted references.

### Step 3 — Audit the methodology

Verify as applicable:

1. system or object under study;
2. research question or hypothesis;
3. scope and assumptions;
4. data source or measurement layer;
5. preprocessing;
6. model or algorithm;
7. hyperparameters;
8. implementation platform;
9. execution path;
10. test scenarios;
11. baselines;
12. metrics;
13. acceptance criteria;
14. reproducibility parameters;
15. limitations.

Flag hidden methodological degrees of freedom.

### Step 4 — Audit experimental fairness

Check whether comparisons use:

- equivalent data;
- same train/validation/test split;
- same operating conditions;
- same metrics;
- comparable tuning effort;
- comparable computational budget when relevant;
- equivalent constraints;
- same evaluation horizon.

Flag cherry-picking or asymmetric tuning.

### Step 5 — Audit quantitative evidence

Check:

- units;
- sign conventions;
- denominator choices;
- aggregation rules;
- repeated runs;
- variance or uncertainty;
- confidence intervals when applicable;
- effect size;
- practical significance;
- consistency across text, tables, figures, and source files.

For stochastic methods, verify whether a single run is being presented as representative.

### Step 6 — Audit causal and generalization claims

Reject causal wording when the design only supports association.

Reject broad robustness/generalization claims when testing is narrow.

Distinguish:

- observed in evaluated cases;
- robust within tested perturbation set;
- generalizes to held-out scenarios;
- universal claim.

Only the first three are normally defensible from bounded experiments.

### Step 7 — Audit reproducibility

Check whether a competent third party could reproduce the central results.

Relevant elements may include:

- dataset or data-generation procedure;
- preprocessing;
- source code;
- versions;
- seeds;
- parameter tables;
- solver settings;
- stopping criteria;
- hardware;
- case files;
- scripts generating figures and tables.

### Step 8 — Audit editorial integrity

Check:

- abstract matches actual evidence;
- introduction motivates the problem without overselling;
- contribution list matches demonstrated contributions;
- terminology is consistent;
- notation is consistent;
- figures/tables are referenced correctly;
- discussion separates observation from interpretation;
- limitations are explicit;
- conclusion does not exceed the evidence.

---

## Severity classification

Use one of the following:

### Critical

A flaw that invalidates the central scientific conclusion or makes the work uninterpretable.

Examples:

- invalid experimental design;
- data leakage;
- incorrect formulation;
- missing central baseline that makes the contribution unassessable;
- conclusions contradicted by results;
- fabricated or unverifiable core evidence.

### Major

Substantial issue requiring new analysis, experiments, methodological clarification, or claim reduction.

### Moderate

Important but bounded issue that does not invalidate the central contribution.

### Minor

Presentation, terminology, notation, clarity, or localized completeness issue.

### Editorial

Formatting or venue-alignment issue with little scientific impact.

---

## Evidence discipline

For every major criticism:

1. state the issue;
2. identify where it occurs;
3. explain the scientific consequence;
4. state what evidence supports the criticism;
5. specify the minimum correction.

Avoid vague comments such as:

- "needs more discussion";
- "should improve novelty";
- "more experiments are needed";

unless you specify exactly why and what is required.

---

## Mandatory checks for computational / ML papers

Check, when applicable:

- data leakage;
- temporal leakage;
- train/validation/test contamination;
- tuning on the test set;
- unfair baseline tuning;
- insufficient random seeds;
- inadequate reporting of variance;
- unsupported SOTA claims;
- missing ablations;
- mismatch between optimization metric and reported metric;
- hyperparameter sensitivity;
- computational-cost comparison;
- reproducibility of preprocessing;
- selective reporting of favorable runs.

---

## Mandatory checks for control / power systems papers

Check, when applicable:

- system model and operating point;
- controller inputs/outputs;
- measurement assumptions;
- actuator limits;
- initialization;
- disturbances;
- baselines;
- controller tuning fairness;
- delays/noise if claimed relevant;
- stability interpretation;
- time-domain and/or modal evidence;
- units and per-unit bases;
- case modifications;
- robustness scope;
- whether "stability", "robustness", or "optimality" is being overclaimed.

---

## Output structure

Use this structure for a full review unless the user requests another format.

### 1. Overall assessment

2–5 concise paragraphs covering:

- problem;
- contribution;
- main strength;
- main scientific risk;
- overall readiness.

### 2. Major comments

For each:

**M1 — [short title]**

- **Issue:**  
- **Why it matters:**  
- **Evidence/location:**  
- **Minimum resolution:**  
- **Severity:** Critical | Major | Moderate  

### 3. Minor comments

Numbered and actionable.

### 4. Claim and evidence check

Use a compact table when useful:

| Claim | Evidence | Status | Required change |
|---|---|---|---|

### 5. Reproducibility assessment

State:

- sufficient;
- partially sufficient;
- insufficient;

and why.

### 6. Editorial recommendation

One of:

- Accept;
- Minor revision;
- Major revision;
- Reject;
- Not enough information to judge.

Justify in 2–4 sentences.

---

## Revision-response mode

When helping authors respond to reviewers:

- preserve the reviewer's meaning;
- do not claim a change was made unless verified;
- identify exact section/page/paragraph when available;
- distinguish manuscript change from response wording;
- avoid defensive language;
- state when a reviewer request cannot be fully satisfied;
- propose a scientifically defensible alternative.

Preferred response structure:

1. acknowledge the scientific point;
2. state exactly what changed;
3. state where it changed;
4. state what evidence or clarification was added;
5. avoid claiming more than was actually changed.

---

## Stop conditions

Stop and report `BLOCKED` when:

- the manuscript or relevant section is missing;
- the task requires checking data/code that is unavailable;
- novelty cannot be assessed because no literature evidence is available and the user requires a verified novelty judgment;
- a central numerical claim cannot be traced to evidence;
- the requested review would require inventing missing results.

Do not block for cosmetic missing information.

---

## Final quality gate

Before delivering the review, confirm:

- criticisms are technically specific;
- no citation or prior work was invented;
- severity is proportional to scientific impact;
- mandatory vs optional changes are clearly distinguished;
- claims were checked against evidence;
- reproducibility was assessed;
- limitations and generalization were examined;
- recommendation follows from the identified issues;
- the review is useful enough that an author could act on it without guessing what you mean.
