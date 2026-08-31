Scientific Coding Skill

Purpose

Produce scientific code that is:

correct;

reproducible;

testable;

readable;

auditable;

modular;

explicit about assumptions;

safe against common methodological errors;

suitable for generating scientific evidence.

Scientific code is not only software.

It is part of the evidence chain:

configuration -> code -> execution -> result -> metric -> figure/table -> claim

Breaking that chain weakens the scientific result even if the code runs.

When to use

Use this skill for:

Python scientific code;

MATLAB scripts/functions;

simulation automation;

data preprocessing;

optimization;

ML/RL;

statistical analysis;

experiment pipelines;

metric computation;

figure/table generation;

code review;

debugging;

reproducibility audits.

Do not apply full software architecture ceremony to tiny exploratory snippets unless they become part of the evidence pipeline.

Operating modes

Use the narrowest mode that matches the task.

Mode A — Code generation

Use when creating new scientific code, experiment scripts, modules, simulation logic,
metrics, preprocessing, or figure/table generators.

Mode B — Code modification

Use when changing existing evidence-producing code while preserving behavior outside
the requested scope.

Mode C — Code review

Use when evaluating whether nontrivial code is scientifically trustworthy enough to
produce or support evidence.

Mode D — Systematic debugging

Use when simulation, training, analysis, HIL/PHIL, metrics, or pipelines fail or
produce inconsistent or nonphysical results.

Mode E — Reproducibility audit

Use when determining whether another researcher could reconstruct the central
computational result from code, configuration, data, and environment information.

Code-generation workflow

For nontrivial scientific code:

identify the scientific objective and expected output;

inspect the existing code/configuration before designing new structure;

determine language, relevant library/runtime versions, inputs, outputs, units,
constraints, and execution context;

design the smallest coherent module/function structure;

implement the scientific logic;

add input and invariant validation where invalid state could silently corrupt evidence;

add the smallest reproducible example or test that demonstrates the intended behavior;

run relevant validation;

confirm that generated outputs are traceable to code and configuration.

Do not require a separate architecture proposal or user confirmation merely because
the code exceeds an arbitrary line count. Ask only when a design choice is materially
ambiguous or changes scientific meaning.

Minimum requirements for evidence-producing code

When applicable, code should make explicit:

input format and provenance;

units and sign conventions;

configurable parameters;

software/runtime assumptions;

random seeds;

solver/integrator settings;

physical constraints;

output schema;

metric definitions;

failure handling.

A standalone example is useful when it protects reproducibility, but do not force
demo boilerplate into modules where tests or documented experiment entry points are
the more appropriate executable specification.

Core engineering principles

1. Single responsibility

Functions and modules should have one clear purpose.

Split code when a function mixes:

I/O;

preprocessing;

model logic;

evaluation;

plotting;

persistence.

2. Descriptive naming

Prefer:

compute_frequency_nadir()

over:

f1()

Names should encode meaning, not implementation trivia.

3. Explicit parameters

Avoid magic constants.

Parameters affecting scientific conclusions must be:

explicit;

centralized;

logged or saved;

traceable to configuration or plan.

4. Boundary validation

Validate inputs where data enters a subsystem.

Examples:

units;

array shape;

missing values;

time ordering;

physical ranges;

expected categories;

solver convergence.

5. Reproducibility

Preserve, when applicable:

random seeds;

software versions;

solver settings;

case files;

configuration;

data version;

preprocessing state;

hardware constraints if they materially affect results.

6. Separation of concerns

Keep distinct:

raw data;

processed data;

configuration;

source code;

trained models;

results;

figures/tables;

manuscript text.

Scientific correctness before optimization

Priority order:

correctness;

reproducibility;

traceability;

clarity;

performance optimization.

Do not optimize code before confirming that the scientific computation is correct.

Recommended project structure

Use only when justified by project complexity.

src/
configs/
tests/
results/

Typical separation:

src/
  domain/
  simulation/
  metrics/
  plotting/
  io/

Do not create one script per figure or one module per trivial function.

Prefer reusable modules plus explicit experiment entry points.

Python standards

Use where appropriate:

type hints;

clear docstrings;

pathlib for paths;

structured logging for nontrivial pipelines;

dataclass or typed configuration objects for complex parameter sets;

explicit exceptions for invalid state;

context managers for files/resources;

vectorized numerical operations when they preserve clarity;

deterministic settings when required.

Avoid:

mutable global state;

hidden environment-dependent behavior;

implicit working-directory assumptions;

silent exception swallowing;

unexplained try/except Exception;

hard-coded absolute paths;

undocumented unit conversions.

Imports

Prefer stable, minimal dependencies.

Do not add a dependency for functionality already available reliably in the standard library or existing stack unless it materially improves the project.

MATLAB standards

Use:

functions for reusable logic;

explicit end;

comments for units and physical meaning;

tables/structs for structured parameters when appropriate;

deterministic random seeds when stochastic code is involved;

explicit solver/options configuration;

paths relative to project root when practical.

Avoid:

eval;

uncontrolled workspace dependencies;

scripts that depend on variable state left by previous scripts;

silent base-workspace mutation;

manual post-processing that is not reproducible.

For Simulink workflows, preserve:

model version;

parameterization scripts;

initialization sequence;

solver settings;

sample times;

variant configuration;

data extraction logic.

Domain-specific generation safeguards

Power systems, converters, microgrids, and BESS

When applicable, declare or trace:

power and voltage bases;

per-unit conventions;

nominal frequency;

sampling/integration step;

controller sample time;

actuator limits;

SoC limits;

current/voltage/power limits;

disturbance timing and magnitude;

solver and fidelity level.

Do not silently clip a physical state merely to make a simulation continue.
If clipping is physically part of the model, make the saturation explicit and
distinguish commanded from applied values.

Reinforcement learning

When applicable:

separate training and evaluation logic;

seed environment and learning stack consistently;

document observation and action scaling;

document reward components and weights;

preserve action constraints;

distinguish termination from truncation;

save the actual trained policy/checkpoint used for reported evidence;

log domain metrics in addition to reward;

avoid evaluation information that would be unavailable at deployment.

Forecasting and supervised ML

When applicable:

split train/validation/test before learned preprocessing;

fit scalers/encoders/selectors only on allowed training data;

respect temporal ordering for time series;

keep the final test set out of tuning;

report final metrics on unseen test data;

preserve preprocessing objects used for the reported model.

Data-processing pipelines

When applicable:

validate missing values and schema before computation;

document source and expected format;

avoid hard-coded machine-specific paths;

preserve transformations that materially affect evidence;

do not silently drop failed or invalid rows without an auditable rule.

Units and dimensional integrity

Scientific code must make units explicit whenever ambiguity is possible.

Use one or more of:

variable suffixes: _hz, _mw, _s, _pu;

comments;

metadata;

typed quantity libraries when justified.

Check dimensional consistency before accepting equations or transformations.

Do not mix:

per-unit and physical units;

RMS and peak values;

phase and line-line quantities;

seconds and milliseconds;

Hz and rad/s;

without explicit conversion.

Configuration discipline

Scientific parameters should not be scattered across scripts.

Prefer one of:

YAML/TOML/JSON configuration;

a typed Python configuration object;

a clearly defined MATLAB parameter struct;

a single experiment configuration module.

Configuration should include, as applicable:

case;

seed;

model;

hyperparameters;

solver;

disturbance;

controller limits;

horizon;

metrics;

output path.

Save the actual configuration used for evidence-producing runs.

Reproducibility protocol

For every evidence-producing execution, preserve enough information to reconstruct:

input/case;

configuration;

code version;

dependency versions;

random seed;

solver/runtime settings;

output;

metric computation;

figure/table generation.

If exact reproduction is impossible, document why and what is still reproducible.

ML/RL safeguards

Data leakage

Split train/validation/test before any learned preprocessing that could leak information.

Fit transformations only on allowed training data.

Temporal leakage

For time series:

respect chronological order;

avoid future information in features;

avoid random splits that invalidate the forecasting/control problem.

Test-set integrity

Never use final test data for:

model selection;

hyperparameter tuning;

early stopping;

normalization fitting.

Baseline fairness

Use, when applicable:

same dataset;

same splits;

same features;

same evaluation metrics;

comparable tuning effort;

same constraints;

same test scenarios.

Randomness

Preserve all relevant seeds:

Python random;

NumPy;

PyTorch;

environment;

simulator when applicable.

Document nondeterministic operations that cannot be fully controlled.

Reporting

Report:

test performance;

multiple runs when stochasticity matters;

variance/dispersion;

failures or instability;

computational cost when relevant.

Do not report only the best seed.

RL-specific checks

Verify:

observation space;

action space;

normalization;

reward definition;

termination conditions;

truncation conditions;

action limits;

environment reset correctness;

seed handling;

train/evaluation mode;

deterministic vs stochastic evaluation;

episode horizon;

replay-buffer contamination across incompatible environments;

reward leakage from unavailable deployment information;

fairness against classical baselines.

A policy that trains successfully is not automatically scientifically valid.

Numerical simulation checks

Before trusting simulation outputs, verify:

initialization;

convergence;

solver success;

event timing;

sampling interval;

numerical tolerances;

model variants;

hidden default parameters;

warm-up/transient exclusion;

physical constraints;

repeatability.

Do not interpret failed or nonconverged simulations as valid scientific evidence.

Metrics

Each metric should define:

formula;

units;

sign convention;

aggregation;

window;

denominator;

missing/invalid handling.

Avoid metric definitions embedded only inside plotting code.

Metrics should be independently testable.

Figures and tables

Generate publication-facing figures/tables from reproducible source data whenever possible.

Check:

axis labels;

units;

legends;

consistent notation;

readable resolution;

no clipped data;

no misleading axis range;

no manual value editing.

Plotting code must not silently recompute a scientifically different metric from the one used in analysis.

Testing strategy

Use the smallest test set that protects scientific validity.

Unit tests

For:

metrics;

transformations;

conversions;

reward functions;

constraints;

parsing;

deterministic domain logic.

Integration tests

For:

simulator loading;

environment reset;

end-to-end experiment path;

model inference;

result serialization.

Regression tests

For:

known benchmark outputs;

solver/case behavior;

critical metrics;

figure/table source consistency.

Smoke tests

For:

package import;

case loading;

solver convergence;

minimal pipeline execution.

Do not create tests merely to increase test count.

Systematic debugging protocol

Scientific debugging must diagnose the cause of invalid evidence, not merely make
the symptom disappear.

Phase 1 — Characterize and reproduce

Before changing model parameters or code:

read the complete error, stack trace, log, or anomalous output;

identify where and when the failure occurs;

reproduce it with the exact configuration when possible;

fix seeds when randomness matters;

inspect recent code, dependency, parameter, and configuration changes;

compare against the last known working case when available.

If the failure cannot yet be reproduced, collect more evidence before proposing a
scientific interpretation of the cause.

Phase 2 — Trace the data/state path

Start from the symptom and trace backward:

what variable or state became invalid?

where was it computed?

what inputs produced it?

where did those inputs originate?

were units, scaling, constraints, and timing correct?

which layer first violated an invariant?

For multi-layer systems such as:

data -> simulator -> controller -> optimizer/RL -> logger -> metric

inspect the boundaries between layers rather than guessing from the final symptom.

Use temporary logging or instrumentation when the origin is not observable.

Phase 3 — Form an explicit causal hypothesis

State the hypothesis in a falsifiable form:

X is the likely root cause because evidence Y would produce symptom Z.

Then design the smallest discriminating test.

Rules:

change one causal factor at a time when possible;

do not mix speculative fixes;

do not treat correlation with the failure as proof of cause;

revise the hypothesis if the test fails.

Phase 4 — Implement the smallest root-cause fix

After the hypothesis is supported:

fix the cause, not only the downstream symptom;

avoid unrelated refactoring in the same change;

preserve previous valid behavior;

add a regression test when recurrence is plausible;

rerun the scientifically relevant validation, not just the failing unit test.

Root-cause tracing

Use root-cause tracing when the symptom appears far from the source.

Trace:

observed failure <- immediate computation <- upstream state <- input/configuration <- origin

Pay special attention to:

unit conversions;

per-unit bases;

array indexing;

stale configuration;

sign conventions;

solver step sizes;

synchronization;

duplicated control paths;

train/test contamination;

state reset logic.

Targeted defense-in-depth

Do not mechanically duplicate the same validation in every layer.

Instead, place validation where it protects an authoritative boundary or prevents
scientifically silent corruption.

Typical locations:

external/API input boundary;

configuration parsing;

physical-domain invariant;

simulator/controller interface;

result serialization;

hardware interface;

metric computation.

Use multiple checks only when distinct code paths could otherwise bypass a critical
invariant.

Debugging anti-patterns

Do not:

patch output files to match expected values;

change several parameters and call success evidence of root cause;

suppress exceptions without understanding them;

clip nonphysical values merely to keep the run alive;

treat a single successful rerun as proof when the failure is stochastic;

continue accumulating fixes when each one reveals a different structural defect.

If repeated small fixes reveal cross-cutting inconsistencies, reassess the model,
data flow, or architecture before continuing.

Code review workflow

Review nontrivial scientific code before it becomes part of frozen or
publication-facing evidence, especially when it changes:

methodology;

preprocessing;

metrics;

constraints;

simulation dynamics;

controller logic;

ML/RL training or evaluation;

figure/table generation.

A review is not required for every trivial edit.

Inputs for review

Inspect, when available:

what was implemented and why;

relevant requirement or plan_maestro.md item;

changed files or git diff;

tests and validation results;

configuration used;

expected scientific behavior.

Review dimensions

Correctness

Check:

algorithm matches intended formulation;

dimensions, indexing, signs, and units are correct;

boundary conditions are handled;

numerical assumptions are valid;

physical constraints are represented correctly.

Reproducibility

Check:

relevant seeds are controlled;

configuration is explicit;

dependencies/runtime are known;

data and case provenance are traceable;

hidden workspace state is not required.

Methodological integrity

Check:

no data or temporal leakage;

no test-set contamination;

no hidden information advantage;

no post-hoc selection embedded in code;

baseline logic is treated fairly;

failed cases are not silently filtered.

Scientific-domain integrity

When applicable, check:

per-unit and physical units;

power/voltage/current limits;

SoC and energy balance;

frequency and angular-frequency conversions;

sample times and solver steps;

actuator saturation;

reset/initialization;

controller measurement availability.

Testing quality

Check:

critical deterministic logic has tests;

tests exercise real logic rather than only mocks;

edge cases relevant to scientific validity are covered;

regression tests exist for previously observed critical bugs;

evidence-producing integration path has at least a smoke/integration check.

Maintainability

Check:

responsibilities are separated coherently;

names communicate scientific meaning;

parameters are not hidden as magic constants;

duplicated scientific logic is minimized;

comments explain assumptions and units, not obvious syntax.

Evidence integrity

Check:

outputs trace to code/configuration;

metrics are reproducible;

figures/tables can be regenerated;

no manual data alteration is required;

reported evidence is not dependent on an untracked local state.

Issue severity

Classify findings by scientific impact.

Critical

Must be fixed before the code is used as evidence.

Examples:

wrong algorithm;

invalid units or dimensions;

data leakage;

corrupted ground truth;

nonphysical state used as valid output;

test-set tuning;

silent failed-run exclusion;

metric implementation error.

Important

Should be fixed before results are frozen.

Examples:

missing validation on a critical boundary;

incomplete reproducibility;

hard-coded scientific parameters;

insufficient tests for a high-risk computation;

mismatch with project specification;

fragile architecture that can change evidence silently.

Minor

Does not materially affect current scientific validity.

Examples:

style;

naming refinement;

local documentation;

noncritical refactoring opportunity.

Acting on review findings

For each substantive issue:

verify that the finding is technically correct in this project;

identify the scientific consequence;

implement one coherent correction;

rerun the relevant test/validation;

check for regressions.

If a reviewer suggestion is technically wrong, preserve evidence and explain the
counterexample, test, or requirement rather than implementing it mechanically.

Stop conditions

Report BLOCKED when:

required input data/case is unavailable;

units or signal meaning are ambiguous and materially affect the result;

expected output cannot be validated;

the simulator/model fails to converge;

the requested implementation would create known leakage or invalid evaluation;

a critical API/version assumption cannot be verified;

a root-cause claim cannot be distinguished from speculation with available evidence;

code review identifies a critical scientific-integrity defect;

the task requires modifying evidence to match a narrative.

Delivery contract

For substantial code work, report:

files changed;

behavior implemented;

configuration assumptions;

tests/validations run;

outputs generated;

unresolved blockers.

Do not claim that code is correct merely because it executes.

Final quality gate

Before declaring scientific code complete, verify:

implementation matches intended method;

parameters are explicit;

units are consistent;

no obvious leakage or unfair comparison exists;

random behavior is controlled when needed;

critical paths are tested;

simulator or numerical method converges when applicable;

outputs are traceable to configuration and code;

metrics are defined consistently;

figures/tables can be reproduced;

failed runs are not hidden;

dependencies and versions are sufficient for reproduction;

critical code paths have been reviewed when they materially affect scientific evidence;

previously fixed critical bugs have regression protection when appropriate;

debugging fixes address demonstrated causes rather than unexplained symptoms;

no manual output manipulation is required to obtain the reported result.