---
name: scientific-methodology
description: >
  Rigorous methodology-design and methodology-audit skill for scientific research,
  computational experiments, simulation studies, control and power systems, ML/RL,
  forecasting, optimization, HIL/PHIL validation, and algorithm comparisons.
  Use when designing, auditing, revising, or validating a research methodology,
  experiment plan, evaluation protocol, baseline comparison, metric set, or
  evidence chain before results are treated as scientific evidence.
---

# Scientific Methodology

## Purpose

Design and audit scientific methodologies so that the resulting evidence is:

- falsifiable;
- measurable;
- reproducible;
- internally coherent;
- fair to competing methods;
- quantitatively defensible;
- appropriately scoped;
- traceable from research question to conclusion.

This skill protects the scientific chain:

`research question -> hypothesis/objective -> assumptions -> variables -> data/model -> method -> baselines -> scenarios -> metrics -> analysis -> evidence -> claim`

A break in this chain must be exposed before the study is treated as complete.

The goal is not to maximize methodology documentation. The goal is to ensure that every methodological choice required to interpret, reproduce, compare, or challenge the central result is explicit and defensible.

---

## When to use

Use this skill when asked to:

- design a scientific experiment;
- design a simulation campaign;
- audit a Methods section;
- evaluate a research methodology;
- prepare the methodological part of `plan_maestro.md`;
- define hypotheses or measurable objectives;
- select baselines;
- define evaluation scenarios;
- select metrics;
- establish acceptance criteria;
- audit ML/RL experimental validity;
- audit forecasting validation;
- evaluate control-system experiments;
- design HIL/PHIL validation;
- assess threats to validity;
- determine whether evidence supports a proposed claim;
- determine whether an experiment is ready to execute;
- determine whether results are scientifically interpretable.

---

## When not to use

Do not use the full workflow for:

- grammar-only editing;
- citation-format cleanup;
- trivial code fixes;
- purely editorial restructuring;
- software debugging that does not affect the scientific design.

Route those tasks to the appropriate writing, citation, coding, or review skill.

---

# 1. Governing principles

## 1.1 Evidence before narrative

Do not change the methodology, metric, baseline, scenario, threshold, or data-processing rule merely because the current result does not support the desired narrative.

If the design changes after results are observed, label the change as post-hoc and reassess the validity of the affected claims.

## 1.2 Falsifiability

A central hypothesis or performance claim must be capable of failing.

Avoid objectives such as:

- "demonstrate that the proposed method is effective";
- "show superior performance";
- "validate the robustness of the method";

unless "effective", "superior", or "robust" are operationally defined before evaluation.

## 1.3 Explicit assumptions

Assumptions that materially affect interpretation must be stated.

Examples:

- measurement availability;
- communication delay assumptions;
- actuator saturation;
- model fidelity;
- disturbance class;
- grid topology;
- train/test distribution;
- observability;
- perfect synchronization;
- ideal sensors;
- parameter uncertainty;
- hardware limitations.

An unstated assumption that creates an advantage for the proposed method is a methodological defect.

## 1.4 Fair comparison

A comparison is scientifically meaningful only when competing methods are evaluated under conditions that make the comparison interpretable.

Do not weaken baselines to create an artificial improvement.

## 1.5 Reproducibility

A competent third party should be able to reconstruct the central experiment from the documented methodology and executable artifacts.

## 1.6 Scope discipline

The demonstrated scope is defined by the evaluated evidence, not by the intended application.

A study evaluated on one benchmark does not automatically generalize to:

- another benchmark;
- another grid topology;
- another fidelity level;
- another disturbance class;
- field deployment;
- unseen operating regimes.

---

# 2. Methodology modes

Choose the narrowest mode that satisfies the task.

## Mode A — Methodology design

Use before experiments are executed.

Output a complete, executable scientific design.

## Mode B — Methodology audit

Use to identify:

- missing elements;
- hidden assumptions;
- bias;
- leakage;
- confounders;
- unfair comparisons;
- inadequate metrics;
- insufficient scenarios;
- reproducibility gaps.

## Mode C — Experiment design

Use when the scientific question is already defined and the task is to specify:

- variables;
- baselines;
- scenarios;
- measurements;
- metrics;
- execution protocol;
- acceptance criteria.

## Mode D — Evidence-readiness audit

Use immediately before treating simulation, experimental, ML/RL, HIL, or computational outputs as scientific evidence.

## Mode E — Claim-to-method audit

Use when a claim is already proposed and the question is whether the methodology is sufficient to support it.

---

# 3. Required context

Inspect, when available:

1. `plan_maestro.md`;
2. research question or objective;
3. hypothesis or expected claim;
4. system/model/data description;
5. proposed method;
6. baseline definitions;
7. scenario definitions;
8. metrics;
9. execution code/configuration;
10. results or pilot results;
11. target venue or publication constraints.

Do not require artifacts that are irrelevant to the study.

If a critical input is unavailable, explicitly state the methodological consequence.

---

# 4. Classify the study before auditing

Determine the dominant study type.

Typical categories:

- forecasting / regression;
- classification / detection;
- control;
- optimization;
- reinforcement learning;
- algorithm comparison;
- system identification;
- model validation;
- simulation study;
- HIL / PHIL / experimental validation;
- system design / sizing / topology;
- literature-based quantitative synthesis.

A study can combine categories.

Different categories create different validity threats.

---

# 5. Research question, objective, and hypothesis

## 5.1 Research question

The research question should identify:

- object/system;
- intervention or proposed method;
- comparison or reference where applicable;
- outcome;
- conditions.

## 5.2 Objective

The main objective must be measurable.

Reject objectives whose completion cannot be determined from evidence.

## 5.3 Hypothesis

Use a hypothesis when appropriate.

A useful experimental hypothesis typically specifies:

`method/intervention -> expected effect -> metric -> comparator -> conditions`

Example structure:

> Under conditions C, method X is expected to reduce metric M relative to baseline B.

Do not insert an arbitrary numerical improvement threshold unless it is scientifically justified.

## 5.4 Multiple objectives

If several objectives exist:

- identify the primary objective;
- identify secondary objectives;
- map each objective to evidence and metrics.

Do not allow multiple unrelated objectives to share one vague evaluation criterion.

---

# 6. Define the system under study

Specify, as applicable:

- physical system;
- mathematical model;
- benchmark;
- topology;
- nominal operating point;
- model fidelity;
- component models;
- controller hierarchy;
- measurement layer;
- actuator layer;
- communication layer;
- constraints;
- initialization;
- solver;
- time resolution;
- hardware interface.

For power-system studies, explicitly distinguish when relevant:

- phasor vs EMT;
- transmission vs distribution;
- grid-connected vs islanded;
- GFL vs GFM;
- simulation vs CHIL vs PHIL vs field;
- local vs wide-area measurements.

Do not allow the manuscript to imply a higher fidelity or validation level than was actually used.

---

# 7. Assumptions and frozen scope

Create an explicit list of assumptions that materially affect the study.

For each assumption ask:

1. Why is it needed?
2. Is it realistic?
3. Does it advantage the proposed method?
4. Does it restrict generalization?
5. Is it tested or only assumed?

Examples:

- perfect communication;
- fixed topology;
- known model parameters;
- no sensor noise;
- no saturation;
- full-state measurement;
- deterministic disturbances;
- identical training and deployment distributions.

If the active project has a frozen scope, do not silently expand or relax it.

---

# 8. Variables and confounders

For experimental and simulation studies, identify when applicable:

## Independent variables

What is deliberately changed.

Examples:

- controller;
- algorithm;
- gain;
- policy;
- disturbance magnitude;
- communication delay;
- penetration level.

## Dependent variables

What is measured as outcome.

Examples:

- frequency nadir;
- settling time;
- cost;
- SoC;
- MAE;
- F1;
- energy;
- stability margin.

## Controlled variables

What must remain fixed to isolate the comparison.

Examples:

- topology;
- load;
- initial conditions;
- solver settings;
- data split;
- evaluation horizon;
- observation set.

## Confounders

Factors that can explain the apparent performance difference independently of the proposed method.

Examples:

- different information available to methods;
- different tuning effort;
- different initialization;
- different data preprocessing;
- unequal constraint enforcement;
- different simulation fidelity;
- test-set contamination.

Every major confounder should be controlled, randomized, stratified, modeled, or explicitly acknowledged.

---

# 9. Data and evidence layer

## 9.1 Real datasets

Document as applicable:

- source;
- collection process;
- period;
- sampling resolution;
- number of observations;
- missingness;
- outliers;
- preprocessing;
- inclusion/exclusion criteria;
- train/validation/test split;
- temporal ordering;
- class balance;
- distribution shift;
- licensing/access restrictions.

Do not treat basic descriptive statistics as a substitute for understanding data provenance.

## 9.2 Simulation-generated data

Document:

- benchmark/model source;
- parameter source;
- modifications to the canonical case;
- initialization;
- solver;
- simulation horizon;
- disturbance generation;
- randomization;
- constraints;
- failed-run handling.

A simulated result is only interpretable if the simulation conditions are traceable.

## 9.3 Experimental / HIL / PHIL data

Document:

- hardware models;
- firmware/software versions;
- sampling rates;
- communication interfaces;
- calibration;
- synchronization;
- scaling;
- sensor accuracy when relevant;
- acquisition path;
- filtering;
- dropped samples;
- experiment repetition protocol.

---

# 10. Leakage and evaluation contamination

This is mandatory for ML, RL, forecasting, system identification, and data-driven studies.

Check:

- train/validation/test separation;
- preprocessing fitted only on allowed training data;
- temporal ordering;
- feature engineering contamination;
- hyperparameter tuning on validation rather than test;
- test reuse;
- model selection using final test results;
- target leakage;
- data duplication across splits;
- normalization leakage;
- future information in features.

For time series, random k-fold cross-validation is not automatically valid.

Use a split strategy that reflects the intended deployment setting.

---

# 11. Baseline design and fairness

## 11.1 Baseline purpose

A baseline should answer a scientific question.

Possible roles:

- conventional practice;
- classical method;
- closest prior method;
- strong modern comparator;
- ablation;
- no-control/no-intervention reference;
- oracle or theoretical upper bound when justified.

Do not impose a fixed number of baselines.

Include enough comparators to make the central contribution interpretable and justify important omissions.

## 11.2 Fairness dimensions

Check whether compared methods share, when scientifically appropriate:

- same data;
- same train/test split;
- same measurements;
- same observation information;
- same actuator limits;
- same physical constraints;
- same disturbance;
- same operating point;
- same benchmark;
- same evaluation horizon;
- same metric implementation;
- comparable tuning effort;
- comparable computational budget when relevant.

## 11.3 Tuning

Do not optimize only the proposed method.

For each baseline record, when relevant:

- source;
- implementation;
- parameterization;
- tuning process;
- search space;
- tuning budget;
- deviations from original publication.

A poor baseline implementation can invalidate a superiority claim.

---

# 12. Scenario design

Scenarios must be chosen to test the claim, not merely to produce visually different plots.

Include the scenarios necessary to evaluate:

- nominal behavior;
- the central disturbance or task;
- relevant uncertainty;
- failure modes;
- claimed robustness;
- boundary conditions;
- deployment-relevant conditions.

Do not require a fixed "base + disturbance + extreme" structure when the scientific question does not justify it.

For every scenario specify:

- initial condition;
- changed parameter/event;
- event time;
- magnitude;
- duration;
- constraints;
- stochastic seed if applicable;
- expected purpose.

---

# 13. Metrics

For each metric define:

1. name;
2. mathematical definition;
3. units;
4. sign convention;
5. evaluation window;
6. aggregation rule;
7. interpretation;
8. failure/invalid handling.

When relevant define:

- primary metric;
- secondary metrics;
- safety/constraint metrics.

Do not select metrics merely because they favor the proposed method.

## 13.1 Control

Possible metrics include, depending on the claim:

- nadir;
- RoCoF;
- overshoot;
- settling time;
- ITAE / IAE / ISE / ITSE;
- voltage deviation;
- control effort;
- energy use;
- constraint violations;
- stability/damping metrics.

Use only metrics that correspond to the actual objective.

## 13.2 Forecasting

Common metrics:

- MAE;
- RMSE;
- nRMSE;
- MAPE only when its denominator behavior is appropriate;
- probabilistic calibration metrics when applicable.

## 13.3 Classification / detection

For imbalanced problems, accuracy alone is normally insufficient.

Consider:

- precision;
- recall;
- F1;
- PR-AUC;
- ROC-AUC;
- false-positive rate;
- false-negative rate;
- detection delay.

## 13.4 RL

Reward alone is insufficient when deployment objectives are physical or operational.

Report domain metrics such as:

- frequency;
- SoC;
- cost;
- constraint violations;
- energy;
- recovery time;
- safety events.

---

# 14. Statistical and quantitative validity

When stochasticity, sampling variability, or repeated runs matter:

- use multiple independent runs/seeds;
- report central tendency;
- report dispersion;
- use confidence intervals when meaningful;
- distinguish statistical from practical significance;
- avoid selecting the best run as representative;
- predefine aggregation rules.

Do not claim significance merely because a numerical difference exists.

If inferential statistics are used:

- state the test/model;
- state assumptions;
- justify sample independence;
- report effect size when useful;
- account for multiple comparisons when relevant.

---

# 15. Acceptance criteria

Define acceptance criteria before final evaluation when the study requires pass/fail interpretation.

Acceptance criteria should be:

- tied to the hypothesis/objective;
- measurable;
- scientifically justified;
- independent of the observed final result.

Do not invent a threshold after seeing the result and present it as pre-specified.

If no threshold is scientifically defensible, use comparative or descriptive evidence instead.

---

# 16. Computational reproducibility

For computational evidence preserve, as applicable:

- code version;
- dependency versions;
- configuration;
- case files;
- seeds;
- solver settings;
- hardware when material;
- preprocessing state;
- trained model;
- result-generation scripts;
- figure/table generation scripts.

Do not rely on manual editing of result files.

A publication figure should be regenerable from traceable data whenever practical.

---

# 17. Scientific code readiness

Before code-generated outputs become evidence, verify:

- implementation matches intended method;
- dimensions and units are correct;
- physical constraints are respected;
- parameters are explicit;
- seeds are controlled when relevant;
- train/test integrity is preserved;
- numerical solver converges when applicable;
- tests or benchmark checks cover critical computations;
- failed runs are not silently discarded.

For nontrivial evidence-producing code, independent code review is strongly recommended before publication-facing results are frozen.

---

# 18. Debugging evidence-producing workflows

A bug in scientific code can invalidate evidence.

Use this sequence:

`symptom -> reproduction -> evidence collection -> root-cause hypothesis -> minimal discriminating test -> single fix -> regression validation`

Rules:

- characterize the failure before changing the model;
- reproduce with exact configuration where possible;
- inspect recent code/config changes;
- trace invalid values backward to their origin;
- test one causal hypothesis at a time;
- avoid simultaneous speculative fixes;
- create a minimal failing case when practical;
- verify the fix does not change unrelated scientific behavior;
- rerun affected evidence after the fix.

Do not patch output data to match an expected result.

Do not treat "the simulation runs" as proof of scientific correctness.

---

# 19. Validity threats

Assess at least the following categories when applicable.

## Internal validity

Could another uncontrolled factor explain the result?

Examples:

- different tuning;
- different input information;
- initialization;
- data leakage;
- hidden constraint differences.

## Construct validity

Do the metrics and experimental manipulations actually represent the scientific concept being claimed?

Example:

A reward increase does not necessarily imply better frequency regulation.

## External validity

To what systems, operating conditions, populations, or benchmarks can the result reasonably generalize?

## Statistical conclusion validity

Are sample size, seeds, variance, uncertainty, and statistical procedures adequate for the conclusion?

## Implementation validity

Could software, solver, numerical, measurement, or hardware implementation choices explain the result?

## Reproducibility validity

Could an independent researcher reproduce the experiment with the available information?

---

# 20. Power systems and control checklist

When applicable, verify:

- benchmark identity and modifications;
- power/voltage bases;
- per-unit conventions;
- operating point;
- disturbance definition;
- controller inputs;
- controller outputs;
- actuator saturation;
- measurement assumptions;
- delay/noise assumptions;
- controller tuning;
- solver/fidelity;
- initialization;
- stability interpretation;
- frequency/voltage sign conventions;
- physical constraints;
- HIL/PHIL interface;
- scenario realism.

Do not use "stable", "robust", "optimal", or "secure" beyond the evidence actually established.

---

# 21. ML/RL checklist

When applicable, verify:

- data split before learned preprocessing;
- no test-set tuning;
- no future leakage;
- same information across baselines;
- reward does not include unavailable deployment information;
- observation/action spaces are documented;
- normalization is documented;
- termination/truncation rules are documented;
- seeds are controlled;
- evaluation is separate from training;
- repeated runs are reported when stochasticity matters;
- physical/domain metrics accompany reward;
- failure and constraint violations are reported;
- hyperparameter tuning is fair.

---

# 22. HIL/PHIL checklist

When applicable, verify:

- validation type: CHIL, PHIL, or other;
- real hardware identified;
- real-time simulator identified;
- sample time;
- communication rate;
- interface scaling;
- signal conditioning;
- amplifier/interface dynamics for PHIL;
- delay;
- stability limitations of interface;
- controller hardware;
- measured vs simulated variables;
- synchronization;
- repeatability;
- safety/constraint handling.

Do not describe CHIL evidence as PHIL or field validation.

---

# 23. Claim-to-method mapping

For every central claim, determine:

| Element | Question |
|---|---|
| Claim | What exactly is asserted? |
| Required evidence | What experiment/analysis would support it? |
| Available evidence | What evidence actually exists? |
| Conditions | Under what conditions was it obtained? |
| Comparator | Against what reference? |
| Metric | What measure supports it? |
| Uncertainty | What variability/error is present? |
| Scope | How far can it generalize? |
| Status | Supported / Partially supported / Pending / Blocked |

If required evidence does not exist, narrow the claim or mark it pending.

---

# 24. Methodology audit severity

## Critical

A flaw that can invalidate the central conclusion.

Examples:

- test leakage;
- impossible or inconsistent units;
- unfair information advantage;
- invalid ground truth;
- wrong implementation of the evaluated method;
- central metric computed incorrectly;
- corrupted or non-traceable evidence.

## Major

A substantial gap requiring additional experiment, analysis, baseline, or methodological clarification.

## Moderate

Important but bounded issue that affects interpretation or generalization.

## Minor

Localized documentation or presentation issue with little effect on scientific validity.

---

# 25. Output: methodology design mode

Use this structure when designing a methodology.

## Scientific objective

## Hypothesis / measurable question

## Scope and assumptions

## System / data / evidence source

## Variables and confounders

## Proposed method

## Baselines and fairness protocol

## Scenarios

## Metrics

## Statistical / repeated-run protocol

## Platform and reproducibility

## Acceptance criteria

## Threats to validity

## Claim boundaries

## Execution readiness

End with one of:

- `READY_FOR_EXECUTION`
- `READY_WITH_MINOR_OPEN_ITEMS`
- `BLOCKED`

---

# 26. Output: methodology audit mode

Use this structure.

## Overall assessment

Short statement on methodological readiness.

## Critical / major findings

For each finding:

- **Issue**
- **Evidence/location**
- **Scientific consequence**
- **Minimum correction**
- **Severity**

## Moderate / minor findings

Concise and actionable.

## Claim-evidence risks

List claims that exceed the current methodology.

## Reproducibility assessment

- sufficient;
- partially sufficient;
- insufficient.

## Verdict

One of:

- methodology sound for current scope;
- minor corrections required;
- major redesign required;
- evidence insufficient to judge.

---

# 27. Stop conditions

Report `BLOCKED` when any of the following is true:

- the central research question cannot be determined;
- the main claim is not falsifiable;
- required data or system definition is missing;
- comparison fairness cannot be established;
- test data has contaminated training or tuning;
- the metric does not measure the stated objective;
- critical units or signal meanings are unresolved;
- evidence-producing code is known to be invalid;
- a frozen project assumption conflicts with the requested experiment;
- the requested claim requires evidence that the design does not generate.

Do not block for optional formatting or documentation artifacts.

---

# 28. Final methodology quality gate

Before declaring the methodology ready, verify:

- the main objective is measurable;
- the central claim is falsifiable;
- assumptions are explicit;
- system/data provenance is clear;
- variables and important confounders are identified;
- no known leakage exists;
- baselines are scientifically appropriate and fairly treated;
- scenario selection tests the actual claim;
- metrics are mathematically and physically defined;
- units and sign conventions are explicit;
- repeated runs/statistical treatment are adequate when needed;
- acceptance criteria are pre-specified when appropriate;
- software/configuration required for reproduction is identified;
- failed runs and adverse cases cannot be silently hidden;
- threats to validity are stated;
- the permitted scope of generalization is explicit;
- each central claim can be mapped to evidence the methodology is capable of producing.

If any critical item fails, do not label the methodology complete.
