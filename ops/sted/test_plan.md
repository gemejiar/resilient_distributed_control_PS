# STED Test Plan — Multimode BESS and Smooth Wide-Area Angular Assistance (IEEE 14 EMT)

**STATUS:** ACTIVE — Actualizado 2026-05-31 (DEC-009 a DEC-013, 10 casos C0–C9).
**Última actualización:** 2026-05-31
**Responsable:** STED-RW Integrator

---

## Propósito

Definir las pruebas mínimas necesarias para aceptar cada gate del proyecto. Las pruebas se
ejecutan antes de pasar de fase. Ningún claim se marca SUPPORTED sin prueba aprobada.

---

## Tabla de pruebas estructurales y de trazabilidad (Gates G0–G2)

| Test ID | Tipo | Gate | Elemento asociado | Descripción | Criterio de aceptación | Estado |
|---|---|---|---|---|---|---|
| T-001 | structural | G0 | plan_maestro.md, gap_matrix.md, contribution_matrix.md, test_plan.md, traceability_matrix.csv, decision_log.md | Verificar que todos los artefactos mínimos existen y tienen contenido sustantivo | Todos los archivos existen con contenido no vacío; ninguno solo tiene STATUS: PENDING_COMPLETION sin contenido | pending |
| T-002 | compilation | G3 | paper/main.tex | Compilar el manuscript LaTeX sin errores bloqueantes de PDF | pdflatex / latexmk produce PDF sin errores críticos; advertencias menores permitidas | pending |
| T-003 | claim | G4 | CLM-001 a CLM-007 en traceability_matrix.csv | Verificar que cada claim tiene al menos una simulación completada y métrica asociada | Cada CLM-00X tiene status != PENDING_EVIDENCE y figure_or_table apunta a archivo existente en paper/figures/ | pending |
| T-004 | claim | G2 | Todos los claims en traceability_matrix.csv | Verificar que ningún claim está marcado SUPPORTED sin simulación y métrica | No existe ningún row con status=SUPPORTED y figure_or_table vacío o archivo inexistente | pending |
| T-005 | figure | G4 | FIG-001 a FIG-004 | Verificar que cada figura tiene script o fuente de datos en source_path | Cada figura tiene source_path que apunta a script existente; el script es ejecutable | pending |
| T-006 | reference | G2 | Todas las citas en paper/main.tex | Verificar que cada \cite{} tiene entrada en biblio_paper.bib y que ninguna entrada tiene DOI inventado | bibtex/biber sin entradas sin definir; ninguna entrada REFERENCE_NOT_VERIFIED usada en texto final | pending |
| T-007 | editorial | G4 | abstract, introduction, methodology, results, conclusions | Verificar que ningún claim prohibido aparece | Búsqueda de: "guarantees stable", "universally applicable", "outperforms all", "first method", "globally stable" — resultado: ninguna encontrada | pending |
| T-008 | notation | G3 | Sección de metodología | Verificar que variables propias no duplican notación del paper base | Búsqueda de WGFL, WGFM, \Omega_{WGFL}, \Theta_{WGFL} en texto propio — resultado: ninguna encontrada | pending |

---

## Pruebas de modo BESS (DEC-009 a DEC-013) — Gates G3–G4

| Test ID | Tipo | Gate | Elemento | Descripción | Criterio de aceptación | Estado |
|---|---|---|---|---|---|---|
| T-MODE-001 | structural | G3 | Todos los casos C0–C9 | Verificar que cada BESS tiene exactamente un modo (GFL o GFM) por caso | Tabla de casos C0–C9 muestra modo único por BESS por caso; ningún BESS aparece en B_GFL ∩ B_GFM en el mismo caso | pending |
| T-MODE-002 | claim | G3 | Ecuación ωg^a en main.tex | Verificar que la asistencia angular suave aplica solo a recursos en I_GFL | La ecuación de ωg^a tiene la condición "g ∈ I_GFL" explícita; ningún recurso GFM aparece recibiendo esta asistencia | pending |
| T-MODE-003 | claim | G3 | Subsecciones BESS-GFM en main.tex | Verificar que ningún recurso GFM usa sustitución de ángulo PLL | No aparece "θ_GFM = Φc" ni asistencia angular tipo GFL en la subsección BESS-GFM | pending |
| T-MODE-004 | causal | G3 | Bloque PDC en Simulink | Verificar que Ωc se calcula solo desde señales de medición PMU, no desde referencias de control | El bloque PDC en Simulink lee señales de la capa de medición (PMU), no de la capa de control (ωg^a, θg^a); documentar en descripción del modelo | pending |
| T-MODE-005 | consistency | G4 | Todos los casos C0–C9 | Verificar que todos los casos usan el mismo evento de perturbación, ventana de tiempo, configuración de solver y filtros de medición | Script de extracción de métricas aplica los mismos parámetros a todos los casos; tabla comparativa usa las mismas unidades y condiciones | pending |
| T-MODE-006 | metric | G4 | Casos C0–C6 | Verificar que BESS-GFL y BESS-GFM reportan las mismas métricas núcleo | Tabla de resultados incluye: nadir, RoCoF, corriente máxima, Vdc, SoC y energía entregada para ambos modos | pending |
| T-MODE-007 | editorial | G4 | Casos C4 y conclusiones | Verificar que la conmutación dura (C4) se reporta solo como baseline y no como parte del método propuesto | No aparece en el texto ninguna frase que sugiera que C4 es el método propuesto o que es recomendado | pending |

---

## Pruebas de simulación (Gate G4)

| Test ID | Tipo | Elemento | Descripción | Criterio de aceptación | Estado |
|---|---|---|---|---|---|
| T-SIM-001 | code | Simulink modelo C0 | Ejecutar C0 con escalón de carga 5–10% | Modelo C0 converge; frecuencia se estabiliza; señales disponibles | pending |
| T-SIM-002 | code | Simulink modelo C3 | Ejecutar C3 (BESS-GFM, droop local) con mismos eventos que C0 | C3 corre sin divergencia; BESS-GFM inyecta potencia activa | pending |
| T-SIM-003 | code | Simulink modelo C5 | Ejecutar C5 (BESS-GFM + smooth GFL assistance) con falla trifásica | C5 corre sin divergencia; λg evoluciona entre 0 y λmax; θg^a se integra sin salto | pending |
| T-SIM-004 | metric | Comparación C4 vs C5 | Comparar |θ_PLL - Φc| entre C4 (hard) y C5 (smooth) | Diferencia medible entre trayectorias angulares; documentar si favorece C5 o no | pending |
| T-SIM-005 | metric | Caso C7 delay sweep | Ejecutar C7 con τ = 20/50/100/200 ms | Cuatro simulaciones completadas; métricas de nadir y error angular para cada τ | pending |
| T-SIM-006 | metric | Caso C6 mixed mode | Ejecutar C6 (BESS-GFM + BESS-GFL simultáneos) | Modelo converge; cada BESS contribuye según su modo; SoC y Vdc de ambos BESS dentro de límites | pending |

---

## Pruebas bibliográficas (Gate G2)

| Test ID | Tipo | Elemento | Descripción | Criterio de aceptación | Estado |
|---|---|---|---|---|---|
| T-BIB-001 | reference | mahish2025wideareacontrol (base paper) | Verificar autores exactos, año, journal, DOI desde PDF en paper/core_refs/ | Entrada bib con todos los campos correctos y DOI verificable | pending |
| T-BIB-002 | reference | Todas las entradas PENDING_VERIFICATION | Verificar que todas las entradas están actualizadas a VERIFIED antes de G2 | Ninguna entrada con status PENDING_VERIFICATION aparece en el texto activo del manuscrito | pending |

---

## Notas de aplicación

- T-001 y T-004 son pre-condiciones para G2.
- T-MODE-001 a T-MODE-004 y T-006, T-008 son pre-condiciones para G3.
- T-002, T-003, T-005, T-007 y T-SIM-001 a T-SIM-006 son pre-condiciones para G4.
- No avanzar a redacción de resultados cuantitativos sin que T-003 y T-SIM-001 a T-SIM-006 estén aprobadas.
- No redactar conclusiones con números sin que CLM-001 a CLM-007 estén SUPPORTED.
