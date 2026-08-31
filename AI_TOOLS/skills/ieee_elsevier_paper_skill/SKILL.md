---
name: ieee-elsevier-paper-architect
description: >
  Use this skill to plan, draft, audit, revise, or prepare an original research
  article, review, benchmark, experimental/HIL-PHIL paper, data-driven modeling
  paper, control-design paper, short communication, or conference-to-journal
  extension for IEEE or Elsevier journals in electrical engineering, power
  systems, power electronics, and automatic control.
language: Spanish for agent coordination; English for manuscript text.
manuscript_policy: Agents may modify LaTeX manuscript text only. They must not
  alter experimental results, source data, executable experiment code, figures,
  tables, captions, references, or bibliography unless a work order explicitly
  authorizes that exact artifact.
---

# IEEE / Elsevier Paper Architect

## 0. Mission and non-negotiable outcome

Build a defensible scientific manuscript, not merely polished prose.

A manuscript is acceptable only when its central thesis, contributions, claims,
figures, tables, equations, references, limitations, and conclusion are mutually
consistent and traceable to verified evidence. The manuscript language is English;
all internal coordination may be in Spanish.

This skill applies to:
1. original research articles;
2. systematic, critical, or narrative reviews;
3. short communications and letters;
4. conference-to-journal extensions;
5. benchmark and comparative studies;
6. control-design and control-validation studies;
7. data-driven dynamic modeling studies;
8. experimental, HIL, CHIL, PHIL, and field-validation studies.

It prioritizes, in this order:
1. power systems;
2. power electronics;
3. automatic control;
4. microgrids, DER, BESS, and IBR;
5. data-driven identification, machine learning, reinforcement learning, PINNs,
   Koopman, and SINDy;
6. cyber-physical security, HIL/PHIL, and experimental validation.

## 1. Authority hierarchy

Resolve conflicts in this order:
1. Target journal’s current Guide for Authors, submission system instructions,
   ethics policy, and template.
2. Target publisher’s current official author policies.
3. This skill.
4. Project `plan_maestro.md`.
5. Verified project evidence and approved decisions.
6. Existing manuscript wording.

Journal-specific requirements always override generic IEEE/Elsevier conventions.
Do not assume page limits, reference style, mandatory declarations, supplementary
materials, highlights, graphical abstracts, or AI disclosure wording without
checking the target journal.

## 2. Required inspection before substantial work

Before planning, drafting, auditing, or editing, inspect the first existing file in
each group:

### Project governance
- `plan_maestro.md`
- `ops/sted/traceability_matrix.csv`
- `ops/sted/decision_log.md`

### Manuscript evidence
- `paper/main.tex` or the actual single main LaTeX file
- figure registry and table registry, if they exist
- the available final figures and tables
- source CSVs, result summaries, and protocols that support those figures/tables
- verified bibliography files and literature evidence matrices

### Editorial constraints
- target journal name and publisher;
- Guide for Authors / journal template;
- submission type;
- word/page limit;
- scope and audience;
- required declarations;
- conference-paper overlap constraints, where applicable.

If a critical input is absent, do not invent it. Create a concise blocker entry in the
traceability matrix or decision log, state the missing input, and work only within
the verified scope.

## 3. Mandatory operating principles

1. Do not invent data, numerical values, test conditions, parameter values,
   references, DOIs, URLs, citations, figures, tables, outcomes, or code behavior.
2. Do not strengthen a scientific claim beyond its evidence.
3. Do not change experimental results, data, figures, tables, captions,
   bibliography, or references unless explicitly authorized.
4. Treat each central result as a figure/table → verified observation → bounded
   claim → interpretation → limitation → implication chain.
5. Every central claim must map to a traceability record.
6. Every central result must appear in at least one figure or table.
7. Every novelty claim must be contrasted with recent, directly related literature.
8. State no more than three contributions. Each contribution must be distinct,
   measurable or auditable, and tied to the actual novelty of the work.
9. Begin the Introduction with concrete technical/operational relevance, never a
   generic definition of the field.
10. Design the figure/table storyline before drafting Results and Discussion.
11. Keep Results factual; use Discussion for interpretation, limitations, and
    conditional implications.
12. Do not introduce new results, equations, citations, or claims in Conclusions.
13. Use the target journal’s style guide for technical formatting. Preserve
    notation already defined in equations unless an approved global change is made.
14. Use conservative wording whenever evidence is partial, scenario-specific,
    simulated, or open-loop.
15. Manuscript text must be in precise technical English; internal reports and
    instructions must be in Spanish unless the work order says otherwise.

## 4. Minimal project inputs

The project must contain or explicitly mark as unavailable:

| Input | Required use |
|---|---|
| Target journal or journal family | Controls scope, format, and editorial constraints. |
| Article type | Activates the correct blueprint. |
| Core research question | Controls the narrative and avoids scope drift. |
| Central thesis | One bounded sentence that the evidence can support. |
| Figures and tables | Establish the results storyline. |
| Result sources / protocols | Verify interpretation and wording. |
| Verified literature set | Establish the gap and comparison logic. |
| LaTeX source | Receives approved text only. |
| Approved claims | Controls phrasing strength. |
| Known limitations | Prevents overclaiming. |

When figures/tables and reference papers are already supplied, treat them as the
primary drafting inputs. Do not request an unneeded prose outline before inspecting
them.

## 5. Required structured outputs

Create or update only the artifacts needed to unblock the current phase.

### 5.1 `paper_blueprint.yaml`
Must define:
- article type and target journal;
- central problem, thesis, audience, and scope;
- up to three contributions;
- section/subsection sequence;
- word/page budget;
- paragraph purpose and evidence for every subsection;
- planned figures/tables/equations;
- known limitations;
- journal-specific submission checklist.

### 5.2 `claim_evidence_matrix.csv`
Minimum columns:

```csv
claim_id,claim_text,claim_class,section,evidence_id,source_path,figure_or_table,allowed_wording,forbidden_wording,scope_condition,status,owner
```

Use `claim_class` values:
`background`, `literature`, `method`, `result`, `interpretation`, `limitation`,
`operational_implication`, `editorial`.

Use `status` values:
`verified`, `partially_verified`, `pending`, `blocked`, `obsolete`, `out_of_scope`.

### 5.3 `section_blueprints.md`
For every section/subsection, include:
- editorial purpose;
- question answered;
- word budget;
- target paragraph count;
- paragraph-by-paragraph function;
- mandatory ideas;
- equations/figures/tables required;
- evidence required;
- frequent failure modes;
- transition sentence objective;
- exit checklist.

### 5.4 `submission_readiness.md`
Must conclude with one of:
- `ready`
- `ready-with-revisions`
- `not-ready`

### 5.5 `cover_letter.md` (only when submitting to a journal)
Use `templates/cover_letter.md`. Draft only after G1 scope is frozen and G5
closure is in sight; the letter must not claim more than the manuscript's
approved contributions and evidence support.

### 5.6 Do not proliferate artifacts
Prefer updating `plan_maestro.md`, the single traceability matrix, and the files
above. Do not create separate reports merely to restate existing information.

## 6. Workflow and gates

### G0 — Initialize
Required:
- article type;
- target journal or journal family;
- main LaTeX path;
- governance files identified.

### G1 — Editorial decision and frozen scope
Required:
- one-sentence thesis;
- explicit inclusions, exclusions, and prohibited claims;
- no more than three defendable contributions;
- target reader and journal fit;
- declared paper type.

### G2 — Evidence and storyline
Required:
- available figures/tables registered;
- each central figure/table linked to source data and a claim;
- literature claims verified;
- missing evidence marked `blocked` or `partially_verified`;
- results storyline ordered before prose drafting.

### G3 — Section architecture
Required:
- section blueprint approved;
- paragraph budgets assigned;
- equation/figure/table placement planned;
- journal constraints checked;
- reference and declaration requirements identified.

### G4 — Controlled drafting
Required:
- agents edit manuscript LaTeX text only;
- claims are limited to approved wording;
- all substantive changes are traceable;
- no unapproved modification to data, results, figures, tables, captions, or bibliography.

### G5 — Editorial and scientific closure
Required:
- technical consistency check;
- claim/evidence audit;
- figure/table/caption cross-check;
- language/style audit;
- journal-specific compliance check;
- red-team review;
- final readiness state.

A gate may be `passed`, `passed_with_caveats`, `blocked`, or `rework_required`.

## 7. Claim-intensity rules

| Level | Allowed wording | Minimum evidence |
|---|---|---|
| Exploratory | `suggests`, `is consistent with`, `may indicate` | Diagnostic or partial evidence. |
| Descriptive | `shows`, `reports`, `quantifies`, `is observed in` | Verified figure/table/metric. |
| Comparative | `achieves lower`, `improves relative to`, `outperforms under the evaluated cases` | Relevant baseline, common protocol, quantitative metric. |
| Strong | `demonstrates` | Reproducible evidence, appropriate baseline, scenario coverage, traceability. |
| Very strong | `consistently outperforms`, `robustly improves` | Multi-scenario evidence and uncertainty/statistical support where appropriate. |
| Prohibited by default | `universal`, `best overall`, `state-of-the-art`, `guarantees`, `deployment-ready` | Do not use unless an explicit, exhaustive evidentiary case is documented. |

Never use:
- `significant/significantly` without a defined statistical or engineering
  significance criterion;
- `robust` without perturbation/uncertainty evidence;
- `scalable` without scaling evidence;
- `real-time` without implementation platform, execution time, sampling period,
  and resource evidence;
- `low-cost` without a stated cost basis;
- `stable` without clearly identified analytical or empirical stability evidence;
- `generalizes` without out-of-sample or out-of-distribution evidence.

## 8. Universal manuscript blueprint: original research article

Adapt the exact headings to the target journal. Do not force a heading when the
journal template or article logic makes it unnecessary.

### 8.1 Title
**Target:** 12–18 words; one line of novelty plus application/context.

**Must express:** object/system + technical action + distinctive method or evidence.
**Must avoid:** marketing, generic phrases, unexplained acronyms, `novel`, `first`,
`optimal` unless proven and central.

Checklist:
- identifies the engineering system or task;
- distinguishes the work from generic literature;
- matches the actual evidence and not merely the intended contribution.

### 8.2 Abstract
**Target:** 180–250 words unless journal specifies otherwise; one compact paragraph.

Use a five-move sequence:
1. concrete technical context and unresolved limitation (1–2 sentences);
2. objective/question (1 sentence);
3. method, model/system, and validation setting (2–3 sentences);
4. principal verified quantitative findings (2–3 sentences);
5. bounded conclusion and contribution (1–2 sentences).

Must contain:
- the system/task;
- the methodological distinction;
- evaluation setting;
- key evidence;
- a bounded implication.

Must not contain:
- citations;
- undefined acronyms;
- claims unsupported by the manuscript;
- generic promises;
- results not shown later.

### 8.3 Keywords
**Target:** 4–8 non-redundant terms.
Use terms from the title, method family, engineering system, and validation mode.
Avoid broad duplicates such as both `power systems` and `electric power systems`.

### 8.4 Nomenclature
Use only where equations/variables are dense enough to materially improve reading.
List symbols, units, and abbreviations consistently with the manuscript.

### 8.5 Introduction
**Target:** 4–6 paragraphs; typically 800–1,300 words for a full journal paper.
Use 4 paragraphs only for a short paper; use 5 as the default.

| Paragraph | Function | Mandatory ideas |
|---|---|---|
| P1 | Concrete technical relevance | Physical/operational consequence, affected system, why existing practice is insufficient. |
| P2 | Specific scientific/technical challenge | Mechanism, uncertainty, limitation, or design tension; not a generic field history. |
| P3 | Focused state of the art | Directly related approaches grouped by decision-relevant dimensions; identify their unresolved limitation. |
| P4 | Precise gap and paper positioning | What is not yet established; why this study is needed; what this paper is and is not. |
| P5 | Contributions and paper organization | Maximum three contributions; bounded evidence; concise roadmap. |

Introduction checklist:
- opens with concrete relevance;
- defines the exact gap, not a vague “few works exist” claim;
- distinguishes novelty from implementation effort;
- uses recent directly related references plus foundational sources;
- contains no results discussion beyond a restrained preview;
- ends with no more than three auditable contributions.

### 8.6 System description / problem formulation
**Target:** 2–4 subsections; 3–6 paragraphs plus equations/figure as needed.

Purpose: establish the physical system, variables, assumptions, objective, constraints,
and performance criteria before presenting the method.

Recommended order:
1. system/testbed and operating context;
2. variables, signals, measurements, and actuation;
3. mathematical formulation or identification/control objective;
4. assumptions, constraints, and boundary conditions.

Must include:
- units and consistent notation;
- scope-valid assumptions;
- practical limits: ratings, latency, sampling, constraints, noise, delays, or
  data availability when relevant;
- explicit distinction between measured, estimated, commanded, and simulated quantities.

Do not:
- repeat textbook derivations that do not support the contribution;
- hide key assumptions in captions or appendices;
- state theoretical guarantees unavailable to the method.

### 8.7 Proposed method
**Target:** 3–6 subsections; 6–12 paragraphs depending on complexity.

Recommended sequence:
1. method overview and design rationale;
2. core formulation/architecture;
3. algorithm/training/identification/control synthesis;
4. constraints, stability/safety logic, and implementation details;
5. computational procedure or pseudocode only if it materially improves reproducibility.

Every subsection must answer:
- What does this component do?
- Why is it needed for the stated problem?
- Which input/output variables does it use?
- Which assumptions/limits apply?
- Which part is genuinely distinctive versus established?

Equations:
- define each symbol on first use;
- use numbered equations only when cited later;
- preserve unit consistency;
- explain engineering meaning, not just algebra.

### 8.8 Experimental, simulation, or validation setup
**Target:** 3–5 subsections; 5–9 paragraphs.

Purpose: allow a qualified reader to judge fairness, reproducibility, and scope.

Recommended sequence:
1. case system/testbed/data set and baseline configuration;
2. scenarios, disturbances, operating points, train/validation/test splits, or
   experimental protocol;
3. baselines and fairness conditions;
4. metrics, constraints, statistical/uncertainty procedure;
5. hardware/software, sampling, solvers, seeds, compute platform, and code/data
   availability where relevant.

Minimum disclosure by study type:
- **simulation:** model fidelity, solver, time step, parameters, scenarios;
- **experimental:** hardware, sensors, calibration, acquisition, safety limits,
  repetitions and uncertainty;
- **HIL/PHIL:** real-time platform, step size, interface/latency, power level,
  protection and coupling method;
- **data-driven:** data provenance, split chronology, preprocessing fitted on
  training data only, hyperparameter selection, seeds, leakage controls;
- **control:** controller sampling, saturation/constraints, baselines, disturbance
  design, performance metrics and failure criteria;
- **benchmark:** datasets/tasks, common protocol, tuning budget, compute metrics,
  fairness choices, statistical treatment.

### 8.9 Results
**Target:** organize by scientific question, not by chronological experiment order.
Use 2 paragraphs per central figure/table as a default.

For each result package:
1. **Observation paragraph:** identify scenario, comparison, figure/table, and
   verified numerical pattern. Do not interpret beyond what the evidence shows.
2. **Meaning paragraph:** explain the engineering relevance, contrast with a
   baseline or mechanism, state the scope condition, and transition to the next
   question.

Recommended results sequence:
1. baseline behavior / sanity check;
2. main comparative or performance result;
3. robustness, sensitivity, generalization, or constraint behavior;
4. computational/implementation implications, when evidence exists;
5. synthesis table or multi-criterion interpretation.

Results checklist:
- every figure/table has a unique argumentative job;
- no duplicate visualization of the same claim unless it adds a new dimension;
- captions state what is shown, scenario, definitions, and comparison basis;
- main claims quote exact figure/table evidence;
- failures or adverse cases are not hidden;
- reported metrics use consistent precision and units.

### 8.10 Discussion and limitations
**Target:** 3–5 paragraphs or a separate Discussion plus a 1–2 paragraph
Limitations subsection, depending on the journal and materiality.

Recommended sequence:
1. synthesize the central result across figures/tables;
2. explain why the observed pattern is technically plausible, without converting
   correlation into causal proof;
3. compare the contribution against directly related literature;
4. state practical applicability and explicit boundaries;
5. state material limitations and the most direct next validation step.

Discussion must:
- interpret; it must not repeat the Results narrative;
- distinguish evidence, inference, and speculation;
- state limitations when they materially affect scope;
- never convert simulation-only evidence into deployment claims;
- avoid future-work lists unrelated to the demonstrated limitation.

### 8.11 Conclusion
**Target:** 2 paragraphs; typically 150–300 words.

P1: restate the objective, method, and 2–3 central verified findings.
P2: state bounded engineering implication, scope conditions, and one substantive
next step if useful.

Do not add:
- citations;
- equations;
- unreported data;
- a broader claim than the Discussion supports;
- new contribution language.

### 8.12 Declarations and end matter
Add only what the target journal requires:
- CRediT authorship contribution statement;
- funding;
- conflicts of interest / competing interests;
- acknowledgments;
- data availability;
- code availability;
- ethics statements where applicable;
- supplementary material statement.

Use `templates/declarations_block.md` as the fill-in scaffold for this subsection.
Populate only the declarations the target journal requires; leave the rest absent
rather than inserting boilerplate.

#### CRediT authorship contribution statement
Use the standard 14-role CRediT taxonomy: Conceptualization, Methodology, Software,
Validation, Formal analysis, Investigation, Resources, Data curation, Writing –
original draft, Writing – review & editing, Visualization, Supervision, Project
administration, Funding acquisition.

Build an author × role matrix first (who genuinely performed each role), then
convert it to prose only if the target journal requires a narrative statement
instead of a table. Do not assign a role to an author who did not perform it, and
do not omit a role that materially affects credit or accountability.

#### Authorship criteria and AI-as-author policy
Apply the ICMJE authorship criteria (widely referenced outside medicine as well)
to resolve who qualifies as an author before building the CRediT matrix. All four
conditions must be met:
1. substantial contribution to conception/design, or to acquisition, analysis, or
   interpretation of data;
2. drafting the manuscript or critically revising it for important intellectual
   content;
3. final approval of the version to be published;
4. agreement to be accountable for all aspects of the work, including questions
   about accuracy or integrity.

AI tools do not meet these criteria — they cannot give final approval or be held
accountable — and must never be listed as an author or co-author. Both IEEE and
Elsevier publisher policies state this explicitly; verify the current wording
against section 1's authority hierarchy before finalizing the disclosure.

#### AI-assisted writing disclosure
Do not automatically insert a disclosure merely because an agent was used. Verify the
current target journal/publisher policy. When a publisher requires disclosure, use the
prescribed location and wording; otherwise prepare a disclosure candidate for author
approval. For Elsevier manuscripts, policy commonly requires a separate statement
immediately before References when generative AI or AI-assisted technologies were
used in manuscript preparation. Authors remain responsible for all content.

A conservative candidate, only after approval and policy verification:

> During the preparation of this manuscript, the authors used [TOOL] solely to
> improve grammar, spelling, and language clarity. The authors subsequently
> reviewed and edited the text and take full responsibility for the final content.

### 8.13 References
Use only verified sources. The project must maintain:
- bibliographic metadata;
- functional role of each reference;
- allowed use;
- prohibited use;
- verification status.

Never cite a source for a claim not supported by that source. Never use a literature
citation to validate the paper’s own numerical results.

Before closing gate G5, run these hygiene checks:
- **zero orphans** — every in-text citation appears in the reference list and
  every reference list entry is cited at least once;
- **self-citation ratio** — flag, do not silently block, if self-citations exceed
  roughly 15% of total citations;
- **DOI format** — `https://doi.org/xxxxx`, not `dx.doi.org` or a bare `doi:`
  prefix; no trailing period after a DOI or URL;
- **retraction screening** — cross-check cited sources against a retraction
  database (e.g., Retraction Watch). If a cited source was retracted: remove the
  citation if it is not essential; if the paper specifically discusses the
  retracted finding or the retraction event itself, keep it with an explicit
  `[Retracted]` or `[Partial retraction; cited findings unaffected]` notation
  instead of silently dropping it.

### 8.14 Appendices and supplementary material
Place derivations, extensive parameter tables, extra scenarios, additional figures,
algorithmic details, and reproducibility material here only when they are necessary
but would interrupt the main argument. The main paper must remain independently
understandable.

## 9. Article-type adaptations

### 9.1 Benchmark / comparative study
Mandatory additions:
- benchmark question and decision context;
- data/task definitions;
- common evaluation protocol;
- baseline selection and tuning fairness;
- leakage controls;
- performance, dispersion, robustness, and compute cost;
- interpretation that avoids declaring a universal winner.

Suggested sequence:
Introduction → Related work and benchmark gap → Data/tasks → Protocol and models →
Results by task/question → Trade-offs and limitations → Conclusion.

### 9.2 Control design and validation
Mandatory additions:
- control objective, architecture, measurements, actuators, constraints;
- stability/performance logic appropriate to the claim;
- baseline controller;
- disturbance scenarios;
- saturation, delay, sampling, and communications treatment where relevant;
- closed-loop metrics and failure criteria.

Do not present prediction error alone as proof of control value. Control relevance may
be claimed only to the extent supported by actual closed-loop evidence.

### 9.3 Data-driven dynamic modeling
Mandatory additions:
- data-generating conditions and excitation coverage;
- input/output/state selection;
- split protocol and out-of-sample condition;
- model order/hyperparameter selection;
- physical consistency and interpretability;
- prediction, frequency/domain behavior, and downstream control relevance only if
  actually evaluated.

Do not require downstream control validation when it is not the article’s scope, but
do not imply it either.

### 9.4 Experimental / HIL / PHIL
Mandatory additions:
- hardware/testbed;
- calibration and acquisition;
- real-time platform and step;
- interface delays and timing;
- safety/protection constraints;
- repeatability and uncertainty;
- correspondence between experimental and model/simulation results, if claimed.

### 9.5 Review / systematic review
Mandatory additions:
- review question and scope;
- search sources, search strings, dates, inclusion/exclusion criteria;
- screening flow and coding protocol;
- taxonomy/rubric;
- synthesis of evidence rather than paper-by-paper summaries;
- limitations of corpus and threats to validity.

Suggested sequence:
Introduction → Review protocol → Corpus → Taxonomy → Synthesis by theme →
Research gaps / agenda → Limitations → Conclusion.

### 9.6 Short communication / letter
Compress to:
Introduction (2–3 paragraphs) → concise formulation/method → compact validation →
Conclusion. Preserve the same claim/evidence discipline. Do not merely remove
methodological detail; select one focused contribution.

### 9.7 Conference-to-journal extension
Before drafting, document:
- prior conference paper;
- new technical contribution;
- new analysis/validation;
- percentage/extent of reuse in text, figures, and data;
- required citation to the conference version;
- publisher-specific policy.

The journal manuscript must offer substantial new technical value, not expanded prose
or reformatted figures alone.

## 10. Editorial and language rules

### 10.1 Paragraph design
Every paragraph needs:
1. a topic sentence tied to the section question;
2. verified technical development;
3. a closing implication or transition.

Avoid paragraphs that only list papers, equations, or figure observations.

### 10.2 Sentence design
- Prefer subject–verb–object structure for core claims.
- Keep one principal claim per sentence.
- Use active voice when it clarifies responsibility; use passive voice when the
  procedure or object matters more than the actor.
- Define acronyms at first use; do not overload the abstract with acronyms.
- Use articles, units, symbols, and tense consistently.
- Use present tense for established knowledge and the paper’s organization;
  use past tense for experimental procedures and observed outcomes.
- Avoid rhetorical fillers: `remarkably`, `clearly`, `obviously`, `it is worth
  noting`, `in recent years`, `very`, `highly`, `state-of-the-art`.

### 10.3 Evidence-aware verbs
- For verified data: `shows`, `reports`, `quantifies`, `exhibits`.
- For bounded interpretation: `indicates`, `suggests`, `is consistent with`.
- For comparison: `achieves lower [metric] under [scenario]`.
- For limitations: `is limited to`, `was not evaluated under`, `does not establish`.

### 10.4 Common failure modes
- generic opening;
- vague gap;
- contribution list that restates tasks;
- method before problem definition;
- results ordered by execution rather than argument;
- duplicated figures;
- captions that do not define scenario/metrics;
- discussion that repeats results;
- causal language based on correlation;
- universal claims from one benchmark;
- conclusion stronger than evidence;
- hidden limitations;
- inconsistent notation, units, or baseline conditions;
- citation padding or unverified references.

### 10.5 Prose quality watchlist
These are prose-quality checks, not detection evasion. Apply them during self-review
of drafted or revised text, subordinate to 10.1–10.3 and to journal style.

Inflated or vague terms to replace with a precise technical alternative unless the
term is standard vocabulary in the sub-field (e.g., `robust estimator` in
statistics, `real-time` with a stated sampling period, `paradigm shift` in
philosophy of science):
`delve`, `pivotal`, `crucial`, `showcase`, `leverage` (as a verb), `underscore` (as
a verb), `multifaceted`, `nuanced`, `comprehensive`, `intricate`, `cornerstone`,
`synergy`, `holistic`, `streamline`, `cutting-edge`, `groundbreaking`, `tapestry`,
`realm`, `embark`, `testament`, `landscape` (non-literal). This list extends, and
must be read together with, the rhetorical fillers already banned in 10.2.

Throat-clearing openers to delete, not soften: `It is important to note that…`,
`It is worth mentioning that…`, `In today's rapidly evolving…`, `It goes without
saying that…`, `As a matter of fact…`. Also cut meta-commentary that announces what
a passage will do instead of doing it (`This section will discuss…`, `We now turn
our attention to…`); the Introduction roadmap sentence (`Section III presents the
proposed method; Section IV reports EMT results`) is standard practice and stays.

Terminology consistency overrides lexical variety: once a variable, signal, system,
or method name is defined (e.g., `wide-area angular assistance`, `BESS-GFM`), reuse
the exact term throughout. Do not cycle synonyms for a defined technical object —
that degrades precision, not just style. Vary connective and framing language
instead (10.2 sentence design), never the name of the technical object itself. This
directly conflicts with generic "avoid repetition" advice; the engineering-precision
rule wins.

Punctuation discipline: treat em dashes and semicolon-chained clauses as a signal to
re-read the sentence, not a hard limit — a manuscript enumerating parallel
conditions or scenarios legitimately uses semicolons more densely than generic prose
guidance allows (see, e.g., 9.2–9.4 disclosure lists). Prefer a period or a
restructured sentence only when the em dash/semicolon is masking two unrelated
claims.

Rhythm and structure: avoid forcing every subsection into an identical paragraph
count or every list into exactly three items — let the paragraph plan in
`templates/section_blueprints.md` drive structure, not a rule of three. Uniform,
metronomic paragraph length across a long Discussion is a signal to re-read for
padding, particularly where 8.10 calls for distinguishing evidence, inference, and
speculation in separate moves.

## 11. Journal-specific checks

### Journal selection due diligence
Verify before committing further drafting effort:
- scope and audience alignment with the manuscript's actual contribution;
- journal legitimacy (check against DOAJ, Cabells, or the publisher's own
  indexed-journal list; treat an unfamiliar or unverifiable venue as a blocker,
  not a convenience);
- open-access status and article processing charges, if relevant to the author;
- typical review timeline and a realistic fit given the manuscript's rejection
  risk;
- whether the journal permits the article type and prior-publication history
  (relevant for conference-to-journal extensions, section 9.7).

### IEEE baseline checks
- use the relevant IEEE template;
- follow IEEE editorial style for headings, equations, abbreviations, numbers,
  figures, and references;
- verify author eligibility, prior-publication and multiple-submission policies;
- use the target transaction’s author instructions over generic IEEE guidance.

### Elsevier baseline checks
- use the target journal’s Guide for Authors and LaTeX template/class;
- check whether highlights, graphical abstract, CRediT, data statement, conflict
  declaration, and AI-use disclosure are required;
- confirm reference style and section numbering;
- follow artwork and supplementary-data requirements for that journal.

## 12. Red-team audit before release

Audit from the standpoint of a demanding Q1 associate editor/reviewer.

Ask:
1. Is the technical gap concrete, current, and directly supported by literature?
2. Are the three contributions genuinely distinct and evidence-backed?
3. Does every central result have a visible figure/table and a source?
4. Are the baselines appropriate and fairly configured?
5. Do claims match validation level: simulation, HIL, experiment, or field?
6. Are constraints, adverse cases, and limitations disclosed?
7. Is causal or theoretical language stronger than evidence?
8. Is the title/abstract/conclusion consistent with the actual contribution?
9. Is journal scope fit demonstrated?
10. Are all end-matter declarations verified against the target journal policy?

## 13. Deliverable format for every substantial task

Return:
1. active gate and status;
2. files inspected;
3. verified evidence used;
4. LaTeX sections changed or proposed;
5. claim IDs introduced/modified;
6. blockers and claims downgraded;
7. exact next authorized action;
8. current readiness: `ready`, `ready-with-revisions`, or `not-ready`;
9. when processing reviewer or editor comments (section 15): revision roadmap
   status (P1/P2/P3 counts, resolved/deferred/disputed counts) and the location of
   the response-letter draft.

## 14. Default instruction to agents

```text
Work under IEEE / Elsevier Paper Architect and STED-RW Lean.

Before editing, inspect the plan, traceability matrix, test plan, decision log,
single main LaTeX manuscript, available final figures/tables, result sources, and
verified bibliography. Determine article type, active gate, journal constraints, and
approved claim scope.

Edit only manuscript LaTeX text unless the work order explicitly authorizes another
artifact. Do not alter results, data, figures, tables, captions, references,
bibliography, or experimental code. Do not invent citations, numbers, assumptions,
or outcomes. Write manuscript prose in technical English.

For each substantive claim, identify evidence, allowable wording, scope condition,
and the figure/table or source that supports it. If evidence is insufficient, mark
the claim as blocked or soften it. Preserve the scientific argument, notation, and
journal compliance. Finish with gate status, traceability updates, blockers, and
submission readiness.
```

## 15. Reviewer response and rebuttal

This section governs the post-submission phase: parsing editor/reviewer decisions,
producing a revision roadmap, drafting the response letter, and feeding approved
manuscript changes back through gate G4. Reviewer response is a designated task for
this skill (see the project's `AGENTS.md` agent roles).

### 15.1 Principles
1. No comment left behind — every reviewer and editor comment must appear in the
   revision response matrix, even if the disposition is "no action, disputed."
2. Classification and section mapping happen before drafting any response text.
3. Every substantive response that changes the manuscript must cite the same
   `claim_id` / `evidence_id` / `figure_or_table` discipline as section 5.2 — a
   response is itself a claim about what changed and why.
4. Manuscript changes made while responding to reviewers still fall under gate G4:
   agents edit manuscript LaTeX text only, and do not alter results, data, figures,
   tables, captions, or bibliography unless the response explicitly authorizes it.
5. Disagreeing with a reviewer is permitted and sometimes correct; it must be
   justified with evidence, not asserted.

### 15.2 Processing pipeline
1. **Collect** — editor decision letter and all reviewer reports, in whatever
   format supplied (pasted email, PDF text, bullet list).
2. **Parse** — split into individual comments using reviewer labels, numbering, or
   topic shifts. Extract raw text and a one-sentence paraphrase per comment.
3. **Classify** — `major` (affects core argument, method, or claims; would block
   acceptance if unaddressed), `minor` (affects quality, not validity), `editorial`
   (wording, formatting, typos), `positive` (acknowledge only).
4. **Map to section** — use this skill's own section taxonomy (8.5–8.14), not a
   generic IMRaD mapping: Introduction, System description/problem formulation,
   Proposed method, Validation setup, Results, Discussion and limitations,
   Conclusion, Declarations, References.
5. **Link to evidence** — where a comment concerns a claim, method detail, or
   result, attach the relevant `claim_id`/`figure_or_table` from
   `claim_evidence_matrix.csv`. If no matching claim exists, note that the
   response requires a new or revised claim entry.
6. **Prioritize** — `P1 must_fix` (editor-flagged or major; blocks acceptance),
   `P2 should_fix` (minor, or raised by multiple reviewers), `P3 consider`
   (editorial or optional). A comment raised independently by more than one
   reviewer is promoted one level.
7. **Detect cross-reviewer patterns** — comments converging on the same weakness
   across reviewers are the strongest signal of a real defect; surface these first.
8. **Draft the revision roadmap and response letter** using
   `templates/revision_response_matrix.md`. Respond to every comment even when the
   disposition is `disputed` — silence reads as evasion. Reference the specific
   section, equation, or figure changed for every item, not just "addressed."
   Prepare both a clean copy and a tracked-changes copy of the revised manuscript
   unless the journal's submission system handles diffing automatically.

### 15.3 Disposition states
- `resolved` — manuscript changed; verified against the linked claim/evidence.
- `deferred` — acknowledged as a limitation (8.10), not fixed this round; state why.
- `disputed` — author disagrees; the matrix's disputed-items table must contain a
  reasoned justification, not a bare refusal.
- `open` — not yet addressed; blocks closure of gate G5 if any P1 item is `open`.

### 15.4 Desk-reject and rejection triage
If the decision is a rejection rather than a revision request, do not proceed to
15.2 — go to section 17 (Post-decision recovery playbook) first to classify the
rejection cause, then return here only if a revise-and-resubmit is chosen.

## 16. Companion skills

This skill governs planning, drafting, and editorial audit of the manuscript. It
deliberately does not duplicate capabilities that live in adjacent skills in this
workspace. Invoke them directly rather than reimplementing their function here.

| Need | Skill | Boundary with this skill |
|---|---|---|
| Independent simulated peer review before submission | `academic-paper-reviewer` | This skill's G5 red-team audit is a self-check by the drafting agent; use the reviewer skill for an adversarial second opinion with a distinct persona set. |
| Publication-ready figures (matplotlib/seaborn, IEEE/Elsevier column widths, colorblind-safe palettes) | `ieee-elsevier-benchmark-figures` | This skill specifies what each figure must argue (8.9) and its placement; the figures skill produces the actual plotting code and layout. |
| Citation lookup, DOI/BibTeX verification | `citation-management` | This skill forbids inventing or misusing citations (8.13, 3.1, 3.7); use the citation skill to locate and verify sources before they enter `claim_evidence_matrix.csv`. |
| Literature search and gap synthesis feeding `research/gap_matrix.md` | `deep-research` | Evidence gathering for G2 happens upstream in `deep-research`; this skill consumes the verified gap/literature set, it does not (re)search the literature itself. |
| Author-voice calibration of drafted prose | `gabriel_scientific_writer` | Apply after this skill's claim-intensity and structural rules (sections 7, 10) are satisfied; voice calibration must never override claim wording or evidence discipline. |
| Broader pre-submission manuscript audit outside this skill's LaTeX/STED-RW scope | `paper-audit` | Use when a reviewer-style pass over format (PDF/Typst/LaTeX) is needed independent of the STED-RW gate structure. |

Do not invoke a companion skill to re-derive something this skill already produces
(e.g., do not ask `deep-research` to re-justify a gap already frozen at G1, and do
not ask a general reviewer skill to redo the claim/evidence audit in 5.2 — refer it
to `claim_evidence_matrix.csv` instead).

## 17. Post-decision recovery playbook

Applies when the editor's decision is a desk-reject, a full rejection after review,
or a rejected conference-to-journal extension. Diagnose the cause before revising
anything; the correct recovery differs by cause.

### 17.1 Desk-reject
| Cause | Diagnostic signal | Recovery |
|---|---|---|
| Scope mismatch | Editor cites "outside journal scope" or "not aligned with aims" | Re-check journal fit against section 1 (authority hierarchy) and the journal's current scope statement; identify 2–3 alternative journals before touching the manuscript. Do not reframe contributions merely to fit a scope they do not have. |
| Insufficient novelty | "Incremental contribution," "well-established" | Re-examine the gap and the ≤3 contributions (rule 8, section 1) against current literature; strengthen only claims the evidence actually supports (section 7) — do not inflate wording to compensate. |
| Formatting non-compliance | Rejected for template/length/style before review | Re-verify the target journal's current Guide for Authors/template (section 1, item 1) and reformat; this is usually resubmittable to the same journal once corrected. |
| Weak opening | No specific reason given; abstract/introduction likely failed to establish relevance | Re-audit the Introduction against 8.5 (P1 concrete technical relevance, P4 precise gap) and the Abstract against 8.2's five-move sequence. |

General protocol: read the decision letter fully before acting; classify against
the table above; if scope mismatch, change the target journal rather than the
paper; if novelty/opening, revise and prefer resubmitting to a different venue;
document the cause and decision in the project's own record (not in this skill).

### 17.2 Rejection after review
Route through section 15 first to classify every comment. Then determine whether
the rejection stems from:
- a structural problem (architecture needs rework) → return to gate G3;
- an evidence gap (missing baseline, missing scenario, missing validation level)
  → return to gate G2;
- a writing/argument problem → rework within G4 without reopening evidence;
- a scope/fit problem → treat as 17.1 scope mismatch and reconsider the target
  journal.
Do not resubmit to the same venue without addressing the root cause identified
here — a second rejection on the same grounds is costlier than the diagnosis time.

### 17.3 Conference-to-journal extension rejected
Common causes and required fixes, building on section 9.7:

| Cause | Fix |
|---|---|
| Insufficient extension (journals typically expect ~30–50% genuinely new material) | Add extended related work, additional scenarios/validation, deeper analysis, or a new discussion dimension — not padding. |
| Self-overlap flag | Explicitly cite the conference version in the Introduction ("This paper extends [conf-citation] with…"); verify textual overlap is below the target journal's stated threshold. |
| Stale baseline/results | If the conference version is old, update baselines and results to current conditions; acknowledge temporal limitations explicitly (8.10). |
| Missing journal-level rigor | Add what conference papers typically omit: full reproducibility detail (8.8), explicit limitations (8.10), complete declarations (8.12). |

Before resubmitting: confirm the conference version is cited, the new-content
proportion is genuine and documented, and the target journal's policy permits
conference-to-journal conversion at all (some prohibit it outright — verify in
section 1 before investing further effort).
