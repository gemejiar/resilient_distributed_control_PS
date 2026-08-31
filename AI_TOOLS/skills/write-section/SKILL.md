---
name: write-section
description: Draft or rewrite a scientific paper section in journal style. Use for Introduction, Methods, Results, Discussion, Conclusion, or Abstract, especially for IEEE or Elsevier-style manuscripts. Produces text ready to paste, with uncertainty markers where user verification is required.
---

# Write Section

Use this skill to draft, rewrite, compress, or refine a scientific manuscript section in formal journal style.

This skill is intended for:
- article drafting from scratch,
- rewriting weak paragraphs,
- strengthening logic and flow,
- adapting text to IEEE or Elsevier style,
- producing paste-ready manuscript text.

## When to use

Use this skill when the user asks to:
- write a section from zero,
- rewrite a manuscript section,
- improve technical style,
- compress or expand a section,
- make the writing more journal-like,
- produce text ready for LaTeX or manuscript insertion.

Typical trigger phrases:
- "write the introduction"
- "rewrite this methods section"
- "improve the discussion"
- "draft a conclusion"
- "make this sound like a journal paper"
- "compress this section without losing rigor"

## When not to use

Do not use this skill when:
- the task is full-paper peer review,
- the task is only grammar correction with no structural rewriting,
- the task is email drafting,
- the task is code generation.

## Required inputs

If not already provided, ask for:
1. Which section: Introduction, Methods, Results, Discussion, Conclusion, or Abstract.
2. Whether there is an existing draft or the section must be written from scratch.
3. Language. Default to English for papers unless the user states otherwise.
4. Any length restriction or target word count.

Optional but useful:
- target venue,
- key claims,
- list of figures, tables, or equations the section must reference,
- preferred tone or degree of compression.

## Writing objectives

The output must be:
- technically precise,
- logically coherent,
- concise but complete,
- ready to paste,
- aligned with scientific journal style,
- explicit about uncertain facts or missing data.

When a value, citation, or claim cannot be safely inferred, mark it as:
- `[REVISAR: motivo]`

## Writing procedure

### Step 1. Establish scope
Restate:
- target section,
- source material available,
- language,
- length constraints,
- target style if known.

### Step 2. Extract content logic
Identify:
- purpose of the section,
- central claims,
- supporting evidence available,
- missing elements that must not be invented.

### Step 3. Draft or rewrite
Apply these rules:
- prioritize strong topic sentences,
- preserve causal and argumentative logic,
- avoid redundancy,
- prefer direct statements,
- define abbreviations the first time they appear,
- keep transitions functional, not ornamental,
- maintain consistency with the manuscript’s technical vocabulary.

### Step 4. Mark uncertainty
Use `[REVISAR: ...]` only where the user must verify:
- numerical values,
- exact citations,
- unconfirmed claims,
- dataset names or parameter values not provided.

## Output format

### 1. Section draft
Provide the section text ready to paste.

### 2. Optional short notes
Only if useful:
- missing information that should be confirmed,
- elements that should be cross-checked with figures, tables, or references.

## Writing rules

- Do not invent citations or numeric values.
- Do not overuse rhetorical flourishes.
- Do not turn technical writing into promotional writing.
- Keep sentence structure clean and controlled.
- Preserve technical meaning when rewriting.
- If source text is weak or confused, fix the logic, not just the wording.

## Definition of done

This skill is complete when:
- the requested section is delivered in paste-ready form,
- language and scope match the request,
- uncertainty is explicitly marked where needed,
- the text is journal-appropriate and technically coherent.
