---
name: review-topic-scout
description: Identify, compare, and rank candidate scientific review topics for short-term publication using bibliometric evidence, review saturation audits, editorial-gap detection, and multi-criteria scoring. Use when the task is to decide what review to write next in power systems, power electronics, hybrid AC/DC microgrids, BESS, EMS/DERMS, reinforcement learning for energy, trustworthy AI/XAI, grid-forming converters, or HIL validation. Do not use for writing the review itself, doing a narrow literature summary, or reviewing a single manuscript.
---

# Review Topic Scout

## Purpose

Use this skill to determine which review topic should be written in the short term based on objective evidence rather than intuition. The skill is designed for repeated use in scientific strategy workflows where the goal is to maximize publication relevance, editorial differentiation, and expected citation value.

The skill is optimized for a researcher profile centered on:

- hybrid AC/DC microgrids,
- BESS and SoC-aware operation,
- inverter-based resources,
- grid-forming control,
- VSG and droop control,
- EMS and DERMS,
- reinforcement learning for energy management and control,
- HIL validation using OPAL-RT, Typhoon HIL, dSPACE, and RTDS,
- rigorous scientific writing and methodological review.

## When to use this skill

Use this skill when the task is to:

- choose the best topic for a future review paper,
- compare several review-topic candidates,
- estimate whether a topic is too saturated,
- identify an editorial gap strong enough to justify a new review,
- rank topics by fit, momentum, citation potential, and feasibility,
- build a repeatable scouting process that can be rerun every 2 to 3 months.

## When not to use this skill

Do not use this skill when the task is to:

- write the actual review paper,
- summarize one topic without comparing alternatives,
- review a single manuscript draft,
- perform deep full-text extraction for one narrowly fixed topic,
- generate a bibliography without strategic ranking.

## Core objective

Determine which review topic has the best balance of:

1. thematic fit with the researcher profile,
2. current momentum,
3. unmet editorial gap,
4. expected citation potential after publication,
5. differentiation from already existing reviews,
6. feasibility for high-quality execution in the short term.

A popular but saturated topic must be penalized. A moderately hot topic with a strong editorial gap and strong fit may rank above a hotter but redundant one.

## Central question

Answer this question:

**Which review topic should be written in the short term, based on objective evidence about topic momentum, saturation, editorial gaps, and expected citation value, while matching the researcher’s strongest expertise?**

## Required analytical posture

You must:

- operate with technical rigor,
- distinguish facts, inferences, and assumptions,
- avoid vague conclusions,
- avoid invented numbers, DOIs, URLs, references, or venue names,
- mark unknowns explicitly,
- use multiple bibliographic sources when possible,
- prefer reproducible, traceable outputs.

You must not:

- recommend a topic based on intuition alone,
- stop after finding one review paper,
- confuse publication volume with opportunity,
- treat broad and narrow topics as directly comparable without normalization,
- recommend an overly broad topic unless you identify a precise differentiating angle.

## Inputs expected

The skill works best when given:

- a researcher profile or domain prior,
- one or more candidate areas of interest,
- a target time horizon such as short-term publication,
- optional access to bibliographic sources or scripts,
- optional preference for review type, for example critical, systematic, methodological, deployment-oriented, or benchmarking-oriented.

If some of these inputs are missing, proceed conservatively and state assumptions.

## Outputs required

Produce these outputs whenever feasible:

- `reports/candidate_topics.md`
- `queries/queries.yaml`
- `results/bibliometric_snapshot.csv`
- `reports/review_competitors.md`
- `results/opportunity_scoring.csv`
- `reports/final_recommendation.md`

If file generation is not possible in the current environment, still structure the answer conceptually using the same sections and file logic.

## Workflow overview

Complete all six stages below. Do not skip a stage. If evidence is incomplete, document the limitation and proceed conservatively.

1. Candidate topic generation.
2. Query design and semantic expansion.
3. Evidence collection and bibliometric snapshot.
4. Saturation audit and editorial gap detection.
5. Multi-criteria scoring and ranking.
6. Final editorial recommendation.

---

# Stage 1 — Candidate topic generation

## Goal

Generate an initial space of 12 to 20 candidate review topics connected to the researcher’s expertise.

## Rules

The list must include:

- broad themes,
- medium-scope themes,
- narrowly differentiated review angles,
- topics combining methodology with deployment,
- topics combining AI or RL with power-system operation,
- topics combining validation, benchmarking, explainability, trustworthiness, or deployment constraints.

## Candidate topic families to consider

Include candidates across these families when relevant:

- grid-forming converters and inverter-dominated systems,
- reinforcement learning for EMS or control,
- trustworthy AI for operational power systems,
- explainable AI for power-system applications,
- BESS operation and ancillary services,
- HIL validation of advanced control or AI-enabled control,
- EMS or DERMS under uncertainty,
- multi-agent coordination and DER orchestration,
- cyber-resilient energy management,
- benchmarking and reproducibility in AI-enabled microgrid control,
- deployment-oriented AI for real-time energy systems,
- constraint-aware AI in hybrid AC/DC microgrids.

## Required output format

Create `reports/candidate_topics.md` with this structure:

```md
# Candidate Review Topics

## Topic 01
Name:
Family:
Scope:
Why relevant to the researcher profile:
Why potentially citable:
Initial risks:

## Topic 02
...
```

## Screening note required

For each topic, add a preliminary note such as:

- too broad,
- likely saturated,
- promising,
- high differentiation potential,
- low fit,
- high effort.

---

# Stage 2 — Query design and semantic expansion

## Goal

Design structured search queries for each candidate topic so that evidence collection is systematic and reproducible.

## Required query types per topic

For each topic, generate at least:

1. Broad query.
2. Precise query.
3. Review query.
4. Methodological gap query.
5. Deployment or validation query.
6. Saturation query.

## Query layers to use

Build the queries using these five layers.

### Layer A. Core theme
Examples:

- `hybrid AC/DC microgrid EMS review`
- `grid-forming inverter review power systems`
- `reinforcement learning review microgrid energy management`
- `trustworthy AI review power systems`

### Layer B. Methodological gap
Examples:

- `benchmarking reproducibility review`
- `systematic comparison`
- `evaluation protocol`
- `deployment constraints`
- `real-time validation`
- `hardware-in-the-loop`

### Layer C. Operational constraints
Examples:

- `latency`
- `safety-critical`
- `constraint-aware`
- `SoC-aware`
- `degradation-aware`
- `operator trust`

### Layer D. Explainability and trustworthiness
Examples:

- `explainable AI power systems review`
- `trustworthy AI energy systems review`
- `human-in-the-loop operational decision support`

### Layer E. Saturation and review density
Examples:

- `survey`
- `state of the art`
- `systematic review`
- `bibliometric review`

## Required output format

Create `queries/queries.yaml` in this structure:

```yaml
topic_01:
  label: "RL for EMS in hybrid AC/DC microgrids"
  broad_query:
    - "reinforcement learning EMS hybrid AC/DC microgrid"
  precise_query:
    - "reinforcement learning energy management hybrid AC/DC microgrid battery dispatch"
  review_query:
    - "reinforcement learning microgrid EMS review"
  gap_query:
    - "benchmarking reproducibility reinforcement learning microgrid EMS"
  deployment_query:
    - "hardware-in-the-loop reinforcement learning microgrid control"
  saturation_query:
    - "survey review reinforcement learning microgrid energy management"
```

## Query quality rules

Queries must:

- be technically precise,
- avoid being too generic,
- include synonyms where needed,
- reflect the deployment angle when relevant,
- reflect benchmarking or validation gaps when relevant,
- be reusable across runs.

---

# Stage 3 — Evidence collection and bibliometric snapshot

## Goal

Collect objective evidence for each candidate topic using multiple sources whenever possible.

## Preferred data sources

Use, in this priority order where available:

1. OpenAlex,
2. Crossref,
3. Semantic Scholar,
4. Google Scholar manual support when needed,
5. Scopus or Web of Science if accessible in the working environment.

## Data to extract per topic

At minimum, extract:

- number of papers by year,
- number of review-type papers by year,
- number of recent reviews in the last 24 months,
- recent citation signals for key reviews,
- recurring journals,
- dominant authors or labs if strongly concentrated,
- co-occurrence with practical terms such as `benchmarking`, `HIL`, `deployment`, `constraints`, `explainability`, `real-time`, `grid code`, `operator`, `safety`.

## Required output files

Create:

- `results/bibliometric_snapshot.csv`
- optionally `data/raw/` exports per source,
- optionally `data/processed/normalized_records.csv`

## Minimum columns for `bibliometric_snapshot.csv`

- `topic_id`
- `topic_label`
- `year`
- `total_papers`
- `total_reviews`
- `recent_reviews_24m`
- `top_journals`
- `notes`

## Data normalization rules

Normalize consistently:

- publication year,
- document type,
- journal titles,
- topic labels,
- review vs non-review records.

Keep raw files separate from processed files.

## Evidence integrity rules

If counts are estimated or incomplete, label them as such. Do not present rough numbers as exact facts.

---

# Stage 4 — Saturation audit and editorial gap detection

## Goal

Determine whether each topic is saturated, undercovered, or still open for a differentiated review.

## Saturation audit procedure

For each candidate topic, identify the cluster of existing reviews. Do not stop after finding one review. Inspect the main competing reviews and characterize them.

For each relevant existing review, evaluate:

- year,
- journal,
- scope,
- methodology type,
- technical depth,
- operational relevance,
- validation relevance,
- whether benchmarking or reproducibility is covered,
- whether deployment or HIL is covered,
- whether explainability or trustworthiness is covered.

## Mandatory questions

For each topic, answer explicitly:

1. Is the topic already saturated?
2. If yes, is there still a meaningful niche left?
3. What exact angle remains undercovered?
4. Could a new review become a reference, or would it likely be redundant?

## Editorial gap definition

A strong editorial gap is not merely “few papers exist”. A strong editorial gap means one or more of these conditions hold:

- no useful operational taxonomy exists,
- no deployment-oriented synthesis exists,
- benchmarking is inconsistent,
- validation levels are poorly compared,
- reproducibility is weak,
- explainability is discussed abstractly but not operationally,
- practical constraints are underrepresented,
- industry or regulatory relevance is not integrated,
- the field lacks a review that connects algorithmic claims with real implementation and validation burden.

## Required output format

Create `reports/review_competitors.md` with this structure:

```md
# Review Competitor Audit

## Topic 01 — [label]
### Existing review 1
Year:
Journal:
Scope:
Type:
Strengths:
Weaknesses:
What remains uncovered:

### Existing review 2
...

### Saturation verdict
...

### Editorial gap claim
...
```

## Critical rule

State the gap as a precise novelty claim that could support the future review paper.

---

# Stage 5 — Multi-criteria scoring and ranking

## Goal

Score all candidate topics using a transparent, reproducible multi-criteria framework.

## Scoring formula

Use:

\[
S = 0.25A + 0.20M + 0.20G + 0.15C + 0.10D + 0.10F
\]

Where:

- `A` = affinity with researcher profile,
- `M` = current momentum,
- `G` = editorial gap,
- `C` = cross-community citation potential,
- `D` = differentiation from existing reviews,
- `F` = short-term feasibility.

Each component must be scored from 1 to 5.

## Detailed scoring guidance

### A. Affinity
Score 5 if the topic falls directly in:

- hybrid AC/DC microgrids,
- EMS or DERMS,
- BESS,
- inverter control,
- RL in energy,
- HIL validation.

### M. Momentum
Consider:

- growth in papers over the last 5 years,
- visible publication activity in 2024–2026,
- recurrence in technical reports, energy transition agendas, or standards discussion,
- interdisciplinarity and present relevance.

### G. Editorial gap
Score high if, despite existing literature, a new review could fill a real synthesis gap such as:

- benchmarking,
- deployment-readiness synthesis,
- validation hierarchy,
- explainability under operational constraints,
- realistic implementation burden,
- compliance and engineering limits.

### C. Citation potential
Score high if the review could be cited by multiple communities such as:

- power systems,
- microgrids,
- control,
- AI or RL,
- BESS,
- HIL,
- trustworthy AI,
- regulation or compliance.

### D. Differentiation
Score high only if the proposed review angle is concretely distinct and can offer at least one of these:

- a new taxonomy,
- a reusable comparison framework,
- a benchmarking map,
- a deployment-readiness matrix,
- a validation ladder,
- a domain-aware interpretability matrix,
- an operational burden classification.

### F. Feasibility
Score high if:

- literature is sufficient but not impossible to cover,
- the researcher already dominates the area,
- the topic can realistically become a near-term review,
- the scope can be bounded well.

## Additional scoring rules

Apply the following:

- a topic with many papers but many recent strong reviews must lose points in `D` and `G`,
- a topic with moderate volume but a strong missing synthesis can still rank first,
- a topic with weak fit cannot rank first unless its citation advantage is overwhelming,
- feasibility must reflect both literature tractability and user expertise,
- popularity alone is insufficient.

## Required output format

Create `results/opportunity_scoring.csv` with at least these columns:

- `topic_id`
- `topic_label`
- `affinity_score`
- `momentum_score`
- `gap_score`
- `citation_score`
- `differentiation_score`
- `feasibility_score`
- `final_score`
- `confidence`
- `rationale_short`

## Ranking output requirements

Produce a descending ranking and explicitly mark:

- top 1,
- top 3,
- top 5,
- topics eliminated due to saturation,
- topics eliminated due to low fit.

---

# Stage 6 — Final editorial recommendation

## Goal

Produce a final, actionable editorial recommendation grounded in all prior evidence.

## Mandatory deliverable

Create `reports/final_recommendation.md`.

## Required structure

The file must contain the following sections.

### A. Executive summary
Provide:

- one primary topic recommendation,
- two backup topics,
- short justification for each.

### B. Full ranking table
Summarize all candidate topics with final score and verdict.

### C. Top-5 topic analysis
For each of the top 5 topics, summarize:

- momentum,
- saturation,
- editorial gap,
- citation opportunity,
- main risk.

### D. Competitor review landscape
Summarize the strongest existing reviews and what they fail to cover.

### E. Editorial recommendation for top topics
For each of the three recommended topics, provide:

- exact topic statement,
- why it matches the researcher profile,
- why it has citation potential,
- why it is not redundant,
- what makes it differentiable,
- what the central taxonomy, matrix, table, or figure should be,
- three possible review titles,
- likely target journals,
- expected risks if the review is executed poorly.

### F. Recommendation on review type
For the primary topic, recommend the most suitable review format from:

- critical review,
- systematic review,
- methodological review,
- deployment-oriented review,
- benchmarking-oriented review.

Explain why.

### G. Immediate next step
Recommend the next action, such as:

- launch exhaustive literature collection,
- narrow scope further,
- define taxonomy,
- convert into systematic review protocol,
- build seed bibliography.

---

# Reasoning format required

Throughout the workflow, always separate:

- Observed evidence,
- Inference,
- Assumption,
- Recommendation.

Do not jump from counts to conclusions without explaining the logic.

---

# Deliverables and file structure

Generate the following structure whenever script or file creation is in scope:

```text
review_topic_scout/
├── README.md
├── config/
│   ├── candidate_topic_rules.yaml
│   ├── scoring_weights.yaml
│   └── source_priority.yaml
├── data/
│   ├── raw/
│   ├── processed/
│   └── exports/
├── queries/
│   └── queries.yaml
├── scripts/
│   ├── generate_candidate_topics.py
│   ├── expand_queries.py
│   ├── collect_openalex.py
│   ├── collect_crossref.py
│   ├── normalize_records.py
│   ├── detect_reviews.py
│   ├── score_topics.py
│   └── build_final_report.py
├── reports/
│   ├── candidate_topics.md
│   ├── review_competitors.md
│   ├── final_recommendation.md
│   └── figures/
└── results/
    ├── bibliometric_snapshot.csv
    └── opportunity_scoring.csv
```

If script generation is not requested, still preserve file naming and section logic conceptually.

---

# Fixed configurations

## Source priority

Use this default priority:

1. OpenAlex
2. Crossref
3. Semantic Scholar
4. Google Scholar manual support
5. Scopus or Web of Science if available

## Review-type detection

When possible, classify a paper as review-like using title and metadata patterns such as:

- review,
- survey,
- state of the art,
- systematic review,
- bibliometric,
- tutorial.

Do not rely on title alone if metadata offers stronger type signals.

## Time horizon

Prefer recent evidence, especially from the last 5 years. Track review saturation particularly in the last 24 months.

---

# Signals to seek explicitly

## Positive signals

- strong recent growth,
- moderate or high volume with insufficient synthesis,
- fragmented literature needing integration,
- lack of deployment-oriented review,
- lack of benchmarking review,
- weak validation comparability,
- strong cross-disciplinary relevance,
- alignment with journals that publish high-visibility reviews.

## Negative signals

- too many recent strong reviews already covering the same angle,
- topic too broad to differentiate,
- low engineering depth,
- little fit with the researcher profile,
- low tractability,
- field too immature for a meaningful review.

---

# Target-journal logic

When suggesting target journals, do not guess arbitrarily. Infer them from:

- where related reviews are already appearing,
- technical breadth,
- relevance to power systems, energy, control, AI-enabled engineering, microgrids,
- likely readership fit.

Always explain why the proposed journal is suitable.

---

# Topic recommendation rules

At the end, recommend:

- one primary topic,
- two backup topics.

For each recommended topic, include:

- exact topic framing,
- reason for fit with the researcher profile,
- reason for citation potential,
- reason it is not too saturated,
- differentiating angle,
- central taxonomy or matrix,
- three possible review titles,
- likely target journals,
- major risks.

---

# Quality-control checklist

Before finalizing, verify:

1. Did you generate 12 to 20 candidate topics?
2. Did each topic receive structured queries?
3. Did you collect objective evidence from more than one source when possible?
4. Did you audit existing reviews instead of merely counting them?
5. Did you identify a precise editorial gap for top topics?
6. Did you apply the scoring formula consistently?
7. Did you avoid recommending a saturated topic without a defensible niche?
8. Did you produce one primary and two backup recommendations?
9. Did you propose an editorial angle, not just a topic label?
10. Did you distinguish facts, inferences, and assumptions?

If any answer is no, revise before finalizing.

---

# Recommended execution strategy

Run the workflow in two passes.

## Pass 1 — Broad opportunity scan

- generate 12 to 20 topics,
- score all of them coarsely,
- identify top 5,
- eliminate obviously weak or saturated topics.

## Pass 2 — Deep audit of top 5

For the top 5 topics:

- inspect the strongest competing reviews in detail,
- refine the exact niche,
- determine whether a new review could plausibly become a reference paper,
- choose the best review type,
- update scores and final recommendation.

This two-pass strategy is preferred over deep analysis of all initial topics.

---

# Recurrent-use requirement

Design the outputs so that the workflow can be rerun every 2 to 3 months with updated data. Preserve previous rankings when possible and highlight trend changes over time.

This skill is intended to support repeated future review-topic scouting, not just a one-time decision.

---

# Compact internal execution prompt

If a compact execution prompt is needed internally, use:

```text
Determine which review topics should be written in the short term, based on objective evidence and not intuition.

Use the researcher profile centered on hybrid AC/DC microgrids, BESS, inverter-based resources, grid-forming control, EMS/DERMS, reinforcement learning for energy, and HIL validation.

Workflow:
1. Propose 12 to 20 candidate review topics.
2. Build structured search queries for each topic.
3. Search objective evidence across bibliographic sources.
4. Quantify momentum and saturation.
5. Audit existing reviews and identify undercovered editorial gaps.
6. Score each topic using:
   S = 0.25*A + 0.20*M + 0.20*G + 0.15*C + 0.10*D + 0.10*F
7. Rank all topics.
8. Recommend one primary topic and two backup topics.

Required outputs:
- candidate_topics.md
- queries.yaml
- bibliometric_snapshot.csv
- review_competitors.md
- opportunity_scoring.csv
- final_recommendation.md

For each recommended topic, include:
- exact recommended angle,
- why it is citable,
- why it is not redundant,
- central taxonomy or figure idea,
- three candidate titles,
- target journals,
- major execution risks.
```

---

# Practical installation note

Place this file at one of these locations:

- project-scoped: `.codex/skills/review-topic-scout/SKILL.md`
- user-scoped: `~/.codex/skills/review-topic-scout/SKILL.md`

Codex uses the skill `name` and `description` for discovery. Keep the `name` stable and keep the `description` explicit.
