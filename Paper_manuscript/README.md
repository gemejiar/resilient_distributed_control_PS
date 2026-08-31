# Paper_manuscript

Canonical manuscript workspace for this project.

## Canonical files

| File | Role |
|------|------|
| `Paper_manuscript/main.tex` | Single main LaTeX manuscript entry point |
| `Paper_manuscript/references.bib` | Project BibTeX bibliography |

These exact paths are what the checks expect:

- `ops/checks/check_bib_entries.py` -> `Paper_manuscript/references.bib`
- `ops/checks/check_latex_structure.py` -> `--main-file` / `--bib-file` defaults
- `AI_TOOLS/hooks/post_edit_check.py` -> `GOVERNED_PREFIXES`

## Structure

Section names, ordering, and whether the manuscript splits into
`\input{}` / `\include{}` files are governed by the **target venue** and
`plan_maestro.md`. `check_latex_structure.py` only verifies that the two
canonical files exist and are non-empty; it is not an editorial gate.

## Objetivo cientifico

## Simulador

## Sistema principal

## Ubicacion de resultados reproducibles

## Estado
