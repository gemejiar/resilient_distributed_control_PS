---
name: review-saturation-audit
description: Use this skill to audit the existing review landscape for a candidate topic and determine whether a new review would be redundant or whether a meaningful niche remains. Use it when you need to assess review saturation, competing surveys, scope overlap, and residual opportunity.
---

# Review Saturation Audit

## Purpose

This skill evaluates whether a candidate topic is already saturated by existing reviews and whether a new review could still be justified.

It is not a general literature summary skill. Its job is to analyze the review landscape around a topic and determine whether there is meaningful editorial space left.

Use it after a bibliometric scan has identified a potentially relevant topic.

## Core Objective

For a given candidate topic, identify the main cluster of existing reviews and answer:

1. Is the topic already saturated?
2. If it is saturated, is there still a viable niche?
3. What exact angle remains undercovered?
4. Would a new review likely become useful and citable, or would it be redundant?

## Scope of Analysis

Focus on review-like publications, including:

- narrative reviews,
- systematic reviews,
- survey papers,
- bibliometric reviews,
- taxonomy-oriented reviews,
- state-of-the-art papers that function as reviews.

The analysis must not stop at the first few obvious papers. It must identify the real review cluster around the topic.

## Required Workflow

### Stage 1. Define the Topic Boundary

Write a one-paragraph scope statement for the candidate topic, including:

- the intended technical boundary,
- the likely neighboring fields,
- likely inclusion terms,
- likely exclusion terms.

This is necessary to avoid false saturation caused by overly broad searches.

### Stage 2. Collect Existing Reviews

Search for review papers using multiple query types:

- broad review query,
- systematic review query,
- survey query,
- state-of-the-art query,
- bibliometric query,
- deployment-oriented query,
- benchmarking-oriented query.

Capture the main reviews that materially overlap the candidate topic.

### Stage 3. Review-by-Review Audit

For each relevant existing review, record:

- year,
- venue,
- review type,
- stated scope,
- technical depth,
- breadth,
- methodological rigor,
- whether it includes benchmarking or reproducibility,
- whether it addresses validation realism,
- whether it addresses HIL or field deployment,
- whether it addresses explainability or trustworthiness,
- main strengths,
- main limitations.

### Stage 4. Overlap Assessment

Compare the candidate new review against the review cluster.

Assess overlap at four levels:

1. topic overlap,
2. methodological overlap,
3. application overlap,
4. editorial overlap.

A topic may be broad enough to host several useful reviews. The key issue is whether the new review would duplicate existing editorial value.

### Stage 5. Saturation Diagnosis

Classify the topic into one of the following states:

- Low saturation
- Moderate saturation
- High saturation but niche remains
- High saturation and weak residual opportunity

The classification must be justified.

### Stage 6. Residual Opportunity Statement

If a niche remains, define it precisely.

Good residual opportunity statements look like:

- existing reviews are broad and narrative, but no review compares validation levels and deployment realism,
- reviews discuss algorithms, but not reproducibility or benchmarking,
- existing surveys cover ML methods but not operational constraints,
- there is no deployment-oriented synthesis linking explainability to operator-facing power-system tasks.

Bad residual opportunity statements look like:

- more papers have been published recently,
- no one has reviewed this exact title before.

## Mandatory Output

Generate `review_competitors.md`.

For each relevant competing review include:

- citation or bibliographic identifier,
- scope summary,
- strengths,
- weaknesses,
- overlap with proposed new review,
- residual niche left uncovered.

Then include a final diagnostic section with:

- saturation level,
- exact residual opportunity,
- redundancy risk,
- recommendation.

## Evaluation Criteria

A topic should be penalized if:

- multiple recent reviews already cover nearly the same angle,
- recent reviews are high quality and still current,
- the proposed new review adds little more than updated references,
- there is no distinctive taxonomy, framework, benchmark, or operational angle left.

A topic can still be viable even with many reviews if:

- prior reviews are too broad,
- they ignore validation realism,
- they lack methodological rigor,
- they omit deployment or HIL,
- they fail to compare explainability, constraints, or benchmarking,
- the field has shifted meaningfully in the last 18 to 24 months.

## Reasoning Rules

Always separate:

- Observed evidence
- Inference
- Assumption
- Recommendation

Do not equate high popularity with low opportunity.
Do not equate low review count with high opportunity.

The correct question is whether the proposed review would create new editorial value.

## Red Flags

Flag the topic if:

- several recent reviews already propose very similar taxonomies,
- recent Q1 review papers already dominate the space,
- the only remaining distinction is a cosmetic change in wording,
- the proposed new review would mainly update the bibliography rather than the editorial contribution.

## Output Style

Be direct and evidence-based.

Use comparison tables whenever useful.

Make the saturation diagnosis explicit and defensible.
