---
name: metadata-pipeline
description: Extracts, cleans, normalizes, and deduplicates bibliographic metadata (title, authors, year, venue, DOI, document type, keywords) from raw literature records into an analysis-ready table. Use when preparing paper, review, or dataset records for clustering, trend analysis, review-topic scouting, or bibliometric analysis, or when merging metadata from multiple sources that may contain duplicates or inconsistent fields.
---

# Metadata Pipeline

Converts raw literature records (search exports, reference managers, manual lists) into a
normalized, analysis-ready metadata table. Optimizes for downstream bibliometric analysis, not
prose.

## When to use and when not

Use when the input is a batch of bibliographic records that need cleaning, normalization,
deduplication, or structuring before downstream analysis (clustering, trend analysis,
review-topic scouting, bibliometric-search).

Do not use for: finding new papers (-> `paper-lookup`, `bibliometric-search`), formatting a
single citation for a manuscript (-> `citation-management`), or drafting manuscript text
(-> `gabriel_scientific_writer`).

## Fields

Extract when available: title, authors, year, venue, DOI, document type, keywords, abstract
snippet, review/survey flag, topic label or provisional family, notes on relevance.

## Processing rules

- Normalize venue names consistently across records.
- Preserve original fields alongside cleaned versions when useful.
- Identify duplicates and near-duplicates by DOI, title similarity, and metadata overlap.
- Mark missing values explicitly (`[MISSING: field]`) instead of guessing.
- Preserve provenance when records come from multiple sources.
- Do not fabricate DOI, author lists, or venues.
- Do not silently drop uncertain records -- flag them for manual verification instead.

## Output

Return or write:
1. A cleaned metadata table.
2. Duplicate/ambiguity report.
3. Missing-field report.
4. Notes on records needing manual verification.
