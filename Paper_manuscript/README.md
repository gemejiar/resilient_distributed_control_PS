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

## Objetivo científico

Formular y evaluar, sobre un sistema eléctrico mixto, una estrategia
coordinada CLF--HOCBF para regulación de frecuencia y tensión bajo límites de
operación. Las afirmaciones de seguridad, estabilidad regional y
recuperabilidad son condicionales a los certificados y evidencias definidos en
`../plan_maestro.md`; todavía no constituyen resultados verificados.

## Simulador

ANDES para los estudios fasoriales RMS de secuencia positiva previstos. La
versión efectiva, los modelos disponibles y la configuración del entorno
`../venv/` deben verificarse durante el inventario autorizado antes de E0.

## Sistema principal

El sistema IEEE de 39 barras es el único banco de pruebas. La campaña comienza
con C0 (10 SG) y contempla variantes progresivas SG--GFM y SG--GFM--GFL. Los
sistemas de 10 y 14 buses del artículo de referencia están fuera del alcance
experimental.

## Ubicación de resultados reproducibles

- `cases/`: caso base y variantes.
- `src/`: ejecutor y componentes de control.
- `artifacts/`: series, logs y resultados trazables.
- `figures_main/`: figuras de frecuencia, tensión y paneles complementarios.

Los nombres efectivos y las rutas de evidencia deben corresponder al caso
inspeccionado; los patrones incluidos en el plan no prueban que un archivo
exista.

## Estado

`E2_APROBADA`. E0, E1 y E2 fueron aprobados por el investigador. E2 aplicó un
incremento exclusivamente reactivo del 1% de la demanda inicial en el bus 21 y
superó las comprobaciones automáticas y la revisión humana. La próxima etapa
prevista es E3--C0a, sustituyendo exclusivamente SG32 por GFM32, pendiente de
instrucción para iniciar. Estos resultados no certifican estabilidad no lineal
ni seguridad dinámica.
