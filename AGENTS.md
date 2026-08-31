# AGENTS.md

## Purpose

This repository follows **STED-RW Lean** for scientific, technical, computational, and editorial projects.

This file defines the **shared operating contract for all AI agents** working in the repository. Its purpose is to preserve scientific rigor, editorial quality, reproducibility, traceability, and minimal repository complexity.

Project-specific objectives, hypotheses, methodology, scope, baselines, claims, gates, acceptance criteria, and current status belong in `plan_maestro.md`.

Do not duplicate project-specific information here.

---

## 1. Read first

Before substantial work, read:

1. `plan_maestro.md`.
2. Only the files directly relevant to the requested task.

Read additional operational artifacts only when needed:

- `ops/sted/traceability_matrix.csv` when claims, evidence, figures, tables, equations, references, tests, or results are affected.
- `ops/sted/decision_log.md` when a methodological, scientific, technical, or editorial decision is introduced or changed.
- Source code, configurations, tests, results, literature, manuscript, or other final-product files relevant to the current task.

Do **not** load the full repository, historical material, examples, or STED-RW documentation unless the task requires them.

If `zPLantilla_STED_RW/STED-RW_Lean.md` or `zPLantilla_STED_RW/prompt_maestro_STED_RW.md` exist, consult them only when:

- initializing a project;
- creating or substantially restructuring `plan_maestro.md`;
- resolving ambiguity about STED-RW gates or workflow rules.

---

## 2. Source-of-truth hierarchy

When information conflicts, use the following hierarchy according to the type of claim:

1. Raw or reproducible experimental evidence.
2. Executable code and active configurations.
3. Results reproducibly generated from them.
4. Figures and tables generated from verified results.
5. `plan_maestro.md` for intended methodology, scope, hypotheses, gates, and authorized work.
6. `ops/sted/traceability_matrix.csv`.
7. Verified primary literature, standards, and authoritative external sources.
8. Notes and internal documentation.
9. Manuscript or other narrative text.
10. `README.md`.

If manuscript text contradicts reproducible evidence, correct the manuscript rather than the evidence.

If a figure or table contradicts its source data, verify the generation pipeline before changing the underlying evidence.

---

## 3. Core scientific rules

- Do not invent data, references, DOI, URLs, paths, results, figures, tables, equations, metrics, or claims.
- Do not strengthen claims beyond the available evidence.
- Do not modify evidence to fit a desired narrative.
- Distinguish verified facts, assumptions, interpretations, hypotheses, pending evidence, and blocked claims.
- Use the canonical status vocabulary for claims, evidence, and references, in both prose markers and the `status` column of `ops/sted/traceability_matrix.csv`: `VERIFIED`, `PARTIALLY_VERIFIED`, `PENDING_EVIDENCE`, `BLOCKED_BY_EVIDENCE`, `REFERENCE_NOT_VERIFIED`, `OBSOLETE`, `OUT_OF_SCOPE`. Do not introduce other status labels.
- Keep project scope consistent with `plan_maestro.md`.
- Register significant methodological, scientific, technical, or editorial decisions in `ops/sted/decision_log.md`.
- Update traceability when tracked claims or evidence materially change.
- Preserve canonical source files unless an explicit task requires migration or replacement.
- Run relevant validation or tests after modifying executable code, configurations, data-processing logic, quantitative results, figures, or tables.

---

## 4. Evidence and claims

Every important scientific or technical claim must be supported by one or more of:

- reproducible data or experimental results;
- executable analysis, simulation, or computation;
- mathematical or theoretical justification;
- verified primary literature or standards;
- another explicitly identified and auditable source of evidence.

Claims without sufficient support must remain conditional, pending, or blocked.

### Claim strength

Do not use strong terms such as:

- `demonstrates`
- `guarantees`
- `optimal`
- `state-of-the-art`
- `universally robust`
- `best`
- `deployment-ready`
- `consistently outperforms`

unless the evidence, comparison scope, statistics, and validation protocol explicitly justify them.

Prefer wording proportional to evidence strength:

- partial or diagnostic evidence: `suggests`, `is consistent with`, `may indicate`;
- verified quantitative evidence: `indicates`, `shows`;
- strong reproducible evidence with fair baselines and protocol: `demonstrates`;
- broad superiority claims require multi-scenario evidence and appropriate statistical support.

---

## 5. References and citation integrity

The following rules are mandatory for publication-facing work:

- Never fabricate bibliographic metadata.
- Never fabricate or guess DOI values.
- Never attribute a numerical result, method detail, or conclusion to a source unless it was verified in that source.
- Unverified references must remain explicitly marked as unverified and must not be used as publication-ready evidence.
- Prefer primary peer-reviewed literature, standards, and authoritative technical sources.
- Avoid using blogs, unsourced web pages, Wikipedia, or secondary summaries as primary scientific evidence when primary sources are available.
- A reference supplied by the user may be used as provided, but obvious metadata inconsistencies must be flagged before publication.
- If a state-of-the-art statement lacks a verified source, mark it as requiring a primary citation rather than inventing one.
- Citation style must follow the target venue or `plan_maestro.md`; do not enforce IEEE, APA, or another style unless the project requires it.

---

## 6. Methodology and study-design integrity

When a task affects methodology, implementation, experiments, evaluation, or study design, verify the applicable elements in `plan_maestro.md`:

1. system or object under study;
2. objective, research question, or falsifiable hypothesis;
3. assumptions and frozen scope;
4. baselines and fairness of comparison;
5. data, evidence, or measurement layer;
6. core method, model, algorithm, or intervention;
7. implementation platform and relevant versions;
8. acquisition, preprocessing, normalization, or feature construction;
9. execution, actuation, or decision path;
10. evaluation scenarios, edge cases, and adverse cases;
11. metrics, units, aggregation rules, and acceptance criteria;
12. reproducibility parameters;
13. limitations and threats to validity;
14. allowed scope of generalization.

Do not require an element explicitly marked `not applicable`, but do not omit an applicable element merely because it is inconvenient.

### Fair comparison

When comparing methods:

- use the same data partitions where applicable;
- use the same operating conditions and evaluation metrics;
- document baseline tuning;
- do not optimize only the proposed method while leaving baselines materially undertuned;
- isolate variables when claiming causal or comparative effects;
- avoid changing multiple experimental factors at once unless the design explicitly studies their interaction.

---

## 7. Statistical and quantitative quality

When quantitative conclusions are involved:

- verify that metrics match the scientific objective;
- preserve units and sign conventions;
- report variability, repeated runs, confidence intervals, or equivalent uncertainty measures when applicable;
- distinguish statistical significance from practical or engineering significance;
- do not select favorable runs while hiding failed or adverse runs;
- do not tune on the final test set;
- do not use post-hoc thresholds without documenting and justifying them;
- ensure reported numbers are consistent across text, tables, figures, and source results.

If results are based on stochastic methods, preserve seeds or equivalent reproducibility controls when applicable.

---

## 8. Scientific code and computational reproducibility

When executable scientific code is affected:

- prefer modular, explicit, testable implementations;
- use descriptive names;
- avoid magic constants in algorithmic logic;
- keep configurable parameters explicit and centralized;
- validate inputs at system boundaries;
- use type hints and docstrings where they materially improve clarity;
- avoid mutable global state when practical;
- record dependencies and relevant versions;
- preserve random seeds or equivalent controls when stochastic behavior matters;
- keep raw data, processing code, configurations, generated results, and manuscript text logically separated;
- include units in variables, comments, labels, or metadata where ambiguity is possible;
- run the smallest relevant test or validation after changes.

### ML/RL safeguards

When machine learning, reinforcement learning, optimization, or data-driven modeling is involved:

- split train/validation/test before preprocessing when required to prevent leakage;
- fit scalers or learned preprocessing only on the permitted training data;
- respect temporal ordering for time-series problems;
- do not use test data for model selection or hyperparameter tuning;
- use fair baseline datasets, partitions, and metrics;
- document tuning procedures for both proposed methods and baselines;
- report test performance, not only training or validation performance;
- preserve seeds and repeated-run protocol when stochasticity affects conclusions.

---

## 9. Figures and tables

Publication-facing figures and tables must be traceable to verified source data or reproducible generation code when applicable.

Check:

- consistency with source data;
- axis labels and units;
- legends;
- captions that are sufficiently self-contained for the target venue;
- consistent notation and terminology;
- no visual exaggeration or misleading scaling;
- no manual editing that changes the scientific meaning of results.

Aesthetic edits are permitted only if they do not alter evidence.

---

## 10. Scientific and editorial review standard

When asked to review, evaluate, audit, or critique a scientific manuscript or methodology, act as a **critical expert reviewer**, not as a validator.

Review, as applicable:

1. problem definition and significance;
2. contribution and novelty;
3. coverage of the closest prior work;
4. theoretical or methodological soundness;
5. assumptions and boundary conditions;
6. experimental design;
7. baselines and comparison fairness;
8. metrics and statistical support;
9. consistency of results;
10. reproducibility;
11. limitations and threats to validity;
12. unsupported generalization;
13. quality of figures, tables, equations, and notation;
14. abstract-body-conclusion consistency;
15. clarity, concision, and technical precision.

For major weaknesses:

- state the problem precisely;
- explain why it matters scientifically or editorially;
- identify the minimum change or evidence needed to resolve it.

Do not soften mandatory corrections into optional suggestions.

---

## 11. Editorial quality

For publication-ready scientific or technical text:

- use the language specified in `plan_maestro.md` or requested by the user;
- default to technical English for journal-facing text unless specified otherwise;
- prefer concise, precise, domain-appropriate prose;
- avoid rhetorical or promotional language;
- preserve established terminology and notation consistently;
- preserve valid LaTeX labels, citations, equations, and cross-references;
- ensure the abstract reflects the actual scope and evidence;
- ensure conclusions do not exceed results;
- separate observed results from interpretation;
- state limitations explicitly when they materially constrain the claim;
- do not introduce novelty claims that are not supported by verified literature comparison.

Publication-ready text must not contain unresolved placeholders unless explicitly requested.

---

## 12. Handling ambiguity and missing information

Ask a clarifying question only when:

- a missing datum materially changes the scientific, technical, or editorial outcome;
- the task is ambiguous in a way that produces incompatible valid outputs;
- a real trade-off requires user authorization.

Otherwise, use a reasonable explicit assumption and continue.

When an assumption is necessary, mark it clearly:

`[ASSUMPTION: ...]`

Do not present assumptions as verified facts.

If the required information can be obtained by inspecting the repository, data, code, results, or provided sources, inspect them before asking the user.

---

## 13. Blocking conditions

Report `BLOCKED` when the requested task cannot be completed reliably because, for example:

- required evidence is missing;
- the requested claim exceeds the available evidence;
- a critical methodological decision remains unresolved;
- required inputs or files cannot be located;
- an executable change cannot be validated sufficiently;
- the requested action conflicts with the frozen project scope;
- the requested workflow would introduce a serious methodological flaw;
- a contradiction between canonical evidence sources cannot be resolved.

Do not report `BLOCKED` merely because an optional artifact does not exist.

---

## 14. File and folder discipline

Before creating a new artifact, verify that it is necessary for at least one of:

1. execution;
2. reproducibility;
3. verification or testing;
4. evidence preservation;
5. traceability;
6. final delivery.

If none applies, do not create it.

Additional rules:

- Prefer modifying an existing appropriate file over creating a new one.
- Do not automatically create missing optional files or folders.
- Do not create redundant reports, matrices, logs, or agent files.
- A missing artifact is not an error unless `plan_maestro.md`, the requested task, or an executable dependency requires it.
- Historical, example, legacy, or archived material must not be treated as active project truth.
- Git history should carry routine edit history; `decision_log.md` should contain only decisions that matter to scientific, technical, methodological, or editorial interpretation.

---

## 15. Workflow for substantial tasks

1. Determine the requested outcome.
2. Verify alignment with `plan_maestro.md`.
3. Identify the minimum relevant files.
4. Inspect the necessary evidence.
5. Identify risks, missing evidence, or methodological conflicts.
6. Execute the smallest coherent change.
7. Validate the result when applicable.
8. Check scientific and editorial consistency.
9. Update traceability only when materially affected.
10. Update the decision log only when a significant decision was made.
11. Report unresolved blockers instead of guessing.

Do not expand scope merely because additional work appears useful.

---

## 16. Forbidden actions

- Fabricating or altering scientific evidence.
- Inventing references or citation metadata.
- Guessing DOI values.
- Attributing unverified numbers or conclusions to literature.
- Presenting assumptions as verified facts.
- Hiding failed runs, contradictory results, or adverse evidence.
- Changing data or results to support a preferred narrative.
- Expanding frozen scope without recording the decision.
- Silently changing methodology, baselines, metrics, acceptance criteria, or hypotheses.
- Silently replacing canonical evidence.
- Using test data for tuning when the protocol requires an untouched test set.
- Claiming validation when the relevant test or evidence was not actually checked.
- Creating redundant documentation that increases context without improving quality.
- Strengthening novelty, superiority, robustness, causality, optimality, or generalization beyond what the evidence supports.

---

## 17. Agent-specific instructions

Shared rules belong in this file.

Tool-specific behavior belongs in the corresponding configuration, for example:

```text
CLAUDE.md
.claude/
.codex/
```

Those files should contain only tool-specific instructions and should not duplicate this document unless duplication is technically required.

Reusable specialized procedures such as paper review, citation management, scientific coding, statistics, or methodology auditing should preferably live in reusable skills rather than being copied into every project.

---

## 18. Language and communication

Default internal coordination and planning language: **Spanish**.

Publication-ready or externally delivered content should use the language specified in `plan_maestro.md` or requested by the user.

Communication should be:

- direct;
- technically precise;
- concise without omitting necessary rigor;
- explicit about uncertainty;
- free of filler or promotional language.

When a requested approach contains a serious technical or methodological problem:

1. identify the problem;
2. explain its consequence;
3. propose the minimum correct alternative;
4. continue only in a way that preserves scientific validity.

---

## 19. Delivery

For substantial work, report concisely:

- files or evidence inspected;
- changes made;
- validations performed;
- claims or traceability affected;
- assumptions introduced;
- unresolved blockers;
- next action only when it follows directly from `plan_maestro.md` or the task.

Do not generate an additional report file unless one is explicitly required.

---

## 20. Final quality check

Before considering a scientific or editorial task complete, verify as applicable:

- the output is within scope;
- no evidence was fabricated or altered;
- claims match the strength of evidence;
- citations and DOI values are verified or explicitly marked otherwise;
- baselines and comparisons are fair;
- quantitative results are internally consistent;
- uncertainty or variability is handled appropriately;
- figures and tables match their source data;
- methodology is sufficiently specified for the intended claim;
- reproducibility information is adequate;
- limitations and threats to validity are not hidden;
- abstract, results, discussion, and conclusions are mutually consistent;
- no unsupported novelty, superiority, robustness, or generalization claim remains;
- required tests or validations were actually performed;
- no unnecessary files or reports were created.

If any critical item fails, do not declare the task complete.
