---
name: editorial-gap-detection
description: Use this skill to identify whether a candidate review topic contains a strong editorial gap that can justify a new review paper. Use it when you need to turn literature evidence into a precise novelty claim, such as a missing taxonomy, benchmarking framework, deployment-oriented synthesis, or operational perspective.
---

# Editorial Gap Detection

## Purpose

This skill determines whether a candidate topic contains a sufficiently strong editorial gap to justify writing a new review article.

Its function is not to count papers or reviews. Its function is to articulate a precise, defensible novelty claim for the prospective review.

Use this skill after bibliometric evidence and a saturation audit are available.

## Core Objective

For a candidate topic, identify whether there is a gap strong enough to support a new review, and formulate that gap as a clear editorial claim.

A strong editorial gap is not simply that the literature is large or growing. A strong editorial gap means that existing reviews fail to organize or interpret the field in a way that researchers and reviewers currently need.

## What Counts as a Strong Editorial Gap

A strong gap may exist if one or more of the following are true:

- no operational taxonomy exists,
- no deployment-oriented synthesis exists,
- benchmarking is inconsistent,
- validation levels are poorly compared,
- reproducibility is weak,
- explainability is discussed abstractly but not operationally,
- practical constraints are underrepresented,
- HIL or field validation is not synthesized,
- cross-domain comparison is missing,
- industry, regulation, or compliance relevance is not integrated,
- the literature is fragmented across communities with no unifying framework.

## What Does Not Count as a Strong Editorial Gap

The following are weak justifications by themselves:

- many papers were published recently,
- there is no review with exactly the same title,
- the topic is popular,
- the topic is trendy on social media,
- the user is personally interested in it.

## Required Workflow

### Stage 1. Define the Intended Review Function

Before detecting a gap, define what kind of review the proposed paper would be. Choose the most plausible type:

- critical review,
- methodological review,
- systematic review,
- taxonomy-driven review,
- benchmarking-oriented review,
- deployment-oriented review,
- operational decision-support review.

The gap must match the intended review function.

### Stage 2. Compare Existing Reviews to Current Needs

Using evidence from existing reviews, ask:

- What do current reviews already do well?
- What questions do they leave unresolved?
- What decision problem would a new review help solve?
- What useful structure is still missing?

### Stage 3. Gap Typing

Classify the gap into one or more categories:

1. Taxonomy gap
2. Benchmarking gap
3. Validation gap
4. Deployment gap
5. Explainability or trustworthiness gap
6. Constraint-awareness gap
7. Cross-domain synthesis gap
8. Reproducibility gap
9. Regulation or compliance gap

### Stage 4. Strength Assessment

Rate the gap as:

- Weak
- Moderate
- Strong
- Strong and strategically attractive

Base the strength rating on:

- relevance to active researchers,
- persistence of the gap across multiple reviews,
- usefulness of the missing synthesis,
- match to the researcher’s expertise,
- likelihood that journals and readers would value the contribution.

### Stage 5. Novelty Claim Formulation

Write the editorial gap as a concise novelty statement.

Examples of good novelty claims:

- Existing reviews summarize algorithms, but no review systematically compares how constraint modeling, benchmark design, and validation realism affect the credibility of RL-based EMS results in hybrid AC/DC microgrids.
- Prior surveys on explainable AI in power systems remain task-agnostic; a new review can provide an operational taxonomy that maps explanation requirements to latency, criticality, and operator involvement.
- The literature contains many reviews on grid-forming converters, but no review synthesizes HIL evidence, compliance testing, and deployment-readiness indicators across converter control families.

### Stage 6. Editorial Asset Design

If the gap is strong enough, propose the central editorial asset that would make the new review useful.

Examples:

- taxonomy table,
- validation-readiness matrix,
- deployment ladder,
- benchmark comparison framework,
- interpretability-by-task map,
- algorithm-versus-constraint matrix,
- operational burden chart.

## Mandatory Output

Generate `editorial_gap_report.md`.

For each assessed topic, include:

- topic statement,
- intended review type,
- existing review limitations,
- gap type,
- gap strength,
- novelty claim,
- proposed central figure or table,
- recommendation on whether the gap justifies a new review.

## Decision Rules

Recommend proceeding only if all of the following are reasonably satisfied:

1. the gap is at least moderate to strong,
2. the gap is not cosmetic,
3. the researcher has strong enough domain fit to exploit it,
4. the proposed editorial asset is concrete and useful,
5. the resulting review would not be redundant.

If these conditions are not satisfied, state that clearly.

## Reasoning Rules

Always separate:

- Observed evidence
- Inference
- Assumption
- Recommendation

Do not claim novelty without tying it to specific deficiencies in existing reviews.

Do not recommend a topic merely because it is broad enough to allow writing many pages.

The gap must correspond to something that readers, reviewers, and editors would actually value.

## Output Style

Be precise, technical, and editorially focused.

Avoid vague claims like “the topic needs more research.”

Prefer strong, testable novelty statements that could be reused directly in a review introduction or cover letter.
