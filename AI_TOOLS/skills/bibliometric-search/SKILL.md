---
name: bibliometric-search
description: Use this skill to collect, normalize, and summarize bibliometric evidence for candidate review topics in power systems, power electronics, microgrids, AI for energy, and related fields. Use it when the task requires objective evidence about topic momentum, publication growth, review density, venue patterns, or citation signals.
---

# Bibliometric Search

## Purpose

This skill collects objective bibliometric evidence for candidate review topics. It is designed to support editorial strategy, topic scouting, and evidence-based prioritization of future review papers.

Use this skill when the task is to estimate whether a candidate topic shows enough momentum, breadth, and citation potential to justify a new review article.

Do not use this skill alone to recommend a final topic. It is an evidence collection and normalization skill. It should usually feed downstream skills such as saturation auditing and editorial gap detection.

## Core Objective

For each candidate topic, gather recent and traceable evidence about:

1. publication volume and growth,
2. review density,
3. citation signals,
4. venue concentration,
5. recency and thematic momentum,
6. adjacent terms that indicate practical or methodological relevance.

The output must be structured, comparable across topics, and suitable for later scoring.

## Domain Focus

Prioritize topics related to:

- hybrid AC/DC microgrids,
- BESS and SoC-aware operation,
- inverter-based resources and grid-forming control,
- EMS and DERMS,
- reinforcement learning in energy systems,
- explainable or trustworthy AI for operational power systems,
- HIL validation,
- realistic benchmarking and deployment-oriented control.

## Evidence Sources

Use multiple reliable bibliographic sources whenever available. Prefer sources with structured metadata.

Recommended priority:

1. OpenAlex
2. Crossref
3. Semantic Scholar
4. Scopus or Web of Science, if available
5. Google Scholar for manual cross-checking only

Do not rely on a single source unless tool limitations make that unavoidable. If a source is unavailable, state that explicitly.

## Required Workflow

### Stage 1. Topic Intake

For each topic, record:

- topic label,
- short topic statement,
- main technical scope,
- likely adjacent communities,
- likely synonyms.

Then generate at least five query families:

1. broad topic query,
2. precise technical query,
3. review-oriented query,
4. methodological or benchmarking query,
5. deployment or HIL query.

### Stage 2. Query Expansion

Expand each topic with synonyms, abbreviations, and neighboring terms. Keep the queries technically meaningful.

Examples of useful expansions:

- EMS ↔ energy management system,
- DERMS ↔ distributed energy resource management,
- GFM ↔ grid-forming,
- BESS ↔ battery energy storage system,
- HIL ↔ hardware-in-the-loop,
- XAI ↔ explainable AI,
- RL ↔ reinforcement learning,
- AC/DC microgrid ↔ hybrid microgrid.

Avoid uncontrolled query drift. The expanded queries must remain relevant to the intended topic.

### Stage 3. Evidence Collection

For each topic, collect at minimum:

- number of papers per year over the last 5 to 7 years,
- number of reviews per year,
- count of reviews in the last 24 months,
- top journals or venues,
- top cited recent reviews,
- indicative citation ranges for recent reviews,
- recurring application areas,
- recurring methodological keywords,
- recurring validation keywords such as real-time, HIL, field, deployment, benchmark, reproducibility.

Where possible, separate:

- original research articles,
- review articles,
- surveys,
- systematic reviews,
- bibliometric reviews.

### Stage 4. Normalization

Normalize metadata before summarizing:

- unify journal names,
- standardize year fields,
- standardize topic labels,
- separate true reviews from ordinary articles that include the word review in the abstract or title but are not review papers.

Document any heuristic used to classify records.

### Stage 5. Topic Snapshot Construction

For each topic, produce a compact evidence snapshot including:

- total papers in recent window,
- annual growth trend,
- review intensity,
- review recency,
- leading journals,
- evidence of cross-disciplinary spread,
- signs of applied or deployment relevance.

### Stage 6. Export

Generate structured outputs suitable for later analysis.

## Mandatory Outputs

### 1. `bibliometric_snapshot.csv`

Minimum columns:

- topic_id
- topic_label
- year
- total_papers
- total_reviews
- recent_reviews_24m
- top_journals
- top_keywords
- notes

### 2. `topic_evidence_notes.md`

For each topic include:

- key observations,
- unusual findings,
- possible ambiguities,
- source limitations,
- early interpretation.

### 3. `queries.yaml`

If not already present, generate or update structured search queries for each topic.

## Interpretation Rules

Separate clearly:

- Observed evidence
- Inference
- Assumption

Do not infer editorial opportunity only from high publication counts.

A topic with high volume and high review density may actually be a weak candidate if the field is saturated.

A topic with moderate volume but a recent rise in technically serious papers may be stronger, especially if it shows multiple adjacent communities and few strong reviews.

## Quality Checks

Before concluding, verify:

- query relevance,
- consistency of publication counts across sources,
- whether review classification is plausible,
- whether the topic is truly active in the last 24 months,
- whether the signal comes from one niche cluster only or from multiple communities.

## Red Flags

Flag any of the following:

- topic counts dominated by irrelevant subfields,
- misleading acronyms,
- inflated counts from duplicate records,
- apparent growth caused by broad query drift,
- absence of identifiable recent review papers,
- lack of evidence that the topic reaches beyond a tiny subcommunity.

## Output Style

Be concise, technical, and traceable.

Prefer tables and compact bullet lists.

State unknowns explicitly.

Do not recommend a final topic unless specifically asked. This skill supports evidence collection for downstream prioritization.
