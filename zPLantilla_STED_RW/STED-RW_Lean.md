# STED-RW Lean: Spec–Test–Evidence-Driven Research and Writing Workflow

**Versión:** 2.0 Lean  
**Propósito:** metodología operativa para coordinar agentes IA en investigación académica, redacción de artículos, libros técnicos, capítulos, software científico y pipelines reproducibles, manteniendo alta calidad con el mínimo número de artefactos indispensables.  
**Principio rector:** maximizar calidad final verificable, no maximizar documentación.

---

## 0. Resumen ejecutivo

**STED-RW Lean** es una versión optimizada de **Spec–Test–Evidence-Driven Research and Writing Workflow**. Integra especificación, evidencia, pruebas, ejecución controlada y cierre de calidad, reduciendo la cantidad de archivos generados y concentrando el control en pocos artefactos de alta densidad.

El flujo conserva el núcleo metodológico:

$$
\text{Specification} \rightarrow \text{Evidence} \rightarrow \text{Tests} \rightarrow \text{Execution} \rightarrow \text{Verification} \rightarrow \text{Writing}
\tag{1}
$$

La versión Lean incorpora:

1. **Agente integrador obligatorio**.
2. **Gates de fase**.
3. **Matriz única de trazabilidad**.
4. **Plan maestro como fuente de verdad**.
5. **Regla estricta de creación mínima de archivos**.
6. **Claims permitidos, condicionados y prohibidos**.
7. **Jerarquía de evidencia para resolver conflictos**.
8. **Alcance congelado y decisión editorial central**.

---

## 1. Principio central

Ningún agente debe redactar, programar, analizar, integrar, modificar o concluir sin haber revisado:

1. Objetivo y alcance.
2. Evidencia disponible.
3. Claims permitidos, condicionados y prohibidos.
4. Pruebas requeridas.
5. Gate activo.
6. Criterios de aceptación.

Regla operativa:

```text
Spec first.
Evidence before claims.
Tests before execution.
Gates before phase transition.
Integrator before final delivery.
```

En español:

> Ningún agente redacta sin especificación.  
> Ningún dato entra sin evidencia.  
> Ningún resultado se acepta sin prueba.  
> Ninguna conclusión se fortalece sin trazabilidad.  
> Ningún cambio mayor avanza sin aprobación del agente integrador.

---

## 2. Objetivos de STED-RW Lean

STED-RW Lean busca:

1. Reducir alucinaciones de agentes IA.
2. Evitar claims no soportados.
3. Evitar deriva de alcance.
4. Reducir archivos accesorios.
5. Mantener trazabilidad entre evidencia, texto, figuras, tablas y conclusiones.
6. Concentrar el control de calidad en pocos artefactos.
7. Facilitar la integración entre Claude, Codex, Cursor, Gemini CLI u otros agentes.
8. Coordinar agentes especializados bajo un integrador.
9. Asegurar que el producto final cumpla el objetivo científico, editorial o técnico.
10. Permitir auditoría humana rápida y confiable.

---

## 3. Alcance de uso

STED-RW Lean aplica a:

- Artículos científicos Q1.
- Revisiones críticas.
- Libros técnicos.
- Capítulos académicos.
- Software científico.
- Pipelines computacionales.
- Bancos de figuras y tablas.
- Auditoría de versiones de manuscritos.
- Proyectos de escritura con agentes IA.

No obliga a usar todos los módulos en todos los proyectos. Cada proyecto debe activar solo los componentes necesarios para cumplir su objetivo.

---

## 4. Arquitectura mínima recomendada

La estructura base debe ser compacta:

```text
project/
  AGENTS.md
  CLAUDE.md
  README.md
  plan_maestro.md

  ops/
    sted/
      traceability_matrix.csv
      test_plan.md
      decision_log.md
      final_quality_report.md
      agents_catalog.md

  paper/
    main.tex
    figures/
    tables/
    bibliography/

  research/
    sources/
    notes/
    corpus/

  reviews/
    audit.md

  scripts/
    tests/
    figures/
    tables/

  .agents/
    skills/
      sted-rw/
        SKILL.md

  .claude/
    agents/
      sted_integrator.md
    commands/
      sted-init.md
      sted-gate.md
      sted-audit.md
      sted-verify.md

  .codex/
    prompts/
      sted-execute.md
      sted-verify.md
```

Esta estructura es compatible con plantillas de paper, libro o software. No todos los proyectos necesitan todas las carpetas. El integrador debe eliminar o no crear lo que no sea necesario.

---

## 5. Archivos mínimos indispensables

STED-RW Lean reduce el núcleo obligatorio a cinco archivos operativos y un catálogo de agentes.

| Archivo | Función |
|---|---|
| `plan_maestro.md` | Fuente de verdad del proyecto. Contiene identidad, tesis, alcance, fases, gates, contribuciones, claims permitidos/prohibidos y criterios de calidad. |
| `ops/sted/traceability_matrix.csv` | Matriz única de trazabilidad. Une claims, evidencia, figuras, tablas, fuentes, pruebas, estado y acción. |
| `ops/sted/test_plan.md` | Pruebas mínimas necesarias para aceptar código, datos, figuras, tablas, referencias, claims o texto. |
| `ops/sted/decision_log.md` | Decisiones, supuestos, bloqueos, cambios de alcance y autorizaciones del integrador. |
| `ops/sted/final_quality_report.md` | Reporte de cierre de calidad y decisión final del integrador. |
| `ops/sted/agents_catalog.md` | Catálogo de roles de agentes. No se crea un archivo por agente salvo para el integrador. |

Solo el archivo del **agente integrador** debe existir por separado:

```text
.claude/agents/sted_integrator.md
```

---

## 6. Regla de creación mínima de artefactos

Un agente solo puede crear un archivo nuevo si cumple al menos una condición:

1. Desbloquea un gate.
2. Contiene evidencia no representable en la matriz única.
3. Es producto final o parte directa del producto final.
4. Es un script ejecutable necesario para reproducibilidad.
5. Es un reporte final solicitado por el integrador.

Si no cumple una de estas condiciones, la información debe integrarse en uno de estos archivos:

```text
plan_maestro.md
ops/sted/traceability_matrix.csv
ops/sted/test_plan.md
ops/sted/decision_log.md
ops/sted/final_quality_report.md
```

Esta regla evita proliferación de archivos, duplicación de reportes y consumo innecesario de tokens.

---

## 7. Documento rector: `plan_maestro.md`

El archivo `plan_maestro.md` debe reemplazar múltiples documentos secundarios. Debe concentrar la definición estratégica y operativa del proyecto.

### 7.1 Estructura recomendada

```markdown
# Plan maestro STED-RW Lean

## 1. Identidad del proyecto
- Tipo:
- Título provisional:
- Producto final:
- Audiencia:
- Journal/editorial/uso objetivo:
- Idioma del producto final:
- Idioma de control interno:

## 2. Decisión científica/editorial central
- Este proyecto debe formularse como:
- Este proyecto no debe formularse como:
- Tesis principal:
- Versión conservadora de la tesis:

## 3. Alcance congelado

### Incluye
- 

### Excluye
- 

### No prometer
- 

### Interpretación permitida
- 

## 4. Contribuciones defendibles

| ID | Contribución | Evidencia requerida | Condición de validez |
|---|---|---|---|
| C1 |  |  |  |

## 5. Claims permitidos, condicionados y prohibidos

### Permitidos
- 

### Condicionados
- 

### Prohibidos
- 

## 6. Jerarquía de evidencia

## 7. Fases y gates

## 8. Plan de ejecución por fases

## 9. Pruebas requeridas

## 10. Criterios de calidad

## 11. Estado actual del proyecto

## 12. Próxima acción autorizada
```

---

## 8. Decisión científica o editorial central

Todo proyecto debe iniciar con una decisión central. Esta decisión evita que el agente convierta el trabajo en un producto distinto al deseado.

### 8.1 Plantilla

```markdown
## Decisión científica/editorial central

Este trabajo debe formularse como:
> ...

Este trabajo no debe formularse como:
> ...

Tesis principal:
> ...

Versión conservadora:
> ...
```

### 8.2 Ejemplo para un artículo experimental

```markdown
Este trabajo debe formularse como:
> Una metodología experimental para validar un lazo externo asistido por PMU orientado a restaurar transferencia activa programada entre áreas.

Este trabajo no debe formularse como:
> Un controlador AGC industrial, una optimización de mercado, una prueba de estabilidad global o una solución universal para cualquier red.

Tesis principal:
> El lazo externo asistido por PMU mejora el seguimiento de transferencia activa programada frente al control local bajo las perturbaciones evaluadas.

Versión conservadora:
> La evidencia experimental disponible soporta una mejora condicionada al sistema de prueba, escenarios y restricciones de laboratorio.
```

### 8.3 Ejemplo para un libro técnico

```markdown
Este libro debe formularse como:
> Un libro técnico y didáctico sobre electrónica de potencia aplicada a redes eléctricas modernas, con énfasis en modelado, control, integración de convertidores y aplicaciones en sistemas eléctricos.

Este libro no debe formularse como:
> Una colección enciclopédica de temas inconexos o un manual de simulación sin hilo conceptual.

Tesis principal:
> La electrónica de potencia moderna debe estudiarse desde la interacción entre convertidores, control y red eléctrica.

Versión conservadora:
> El libro introduce y organiza los conceptos esenciales para conectar diseño de convertidores, control y operación de redes modernas.
```

---

## 9. Alcance congelado

El alcance congelado define qué entra, qué queda fuera y qué no debe prometerse.

### 9.1 Plantilla

```markdown
## Alcance congelado

### Incluye
- 

### Excluye
- 

### No prometer
- 

### Interpretación permitida
- 
```

### 9.2 Reglas

1. Ningún agente puede expandir el alcance sin registrar decisión en `decision_log.md`.
2. Ningún texto puede prometer elementos incluidos en “No prometer”.
3. Si una contribución requiere evidencia fuera del alcance, debe rebajarse o eliminarse.
4. Si el usuario autoriza cambio de alcance, el integrador actualiza `plan_maestro.md` y `decision_log.md`.

---

## 10. Jerarquía de evidencia

La jerarquía de evidencia resuelve conflictos entre texto, scripts, figuras, resultados y literatura.

### 10.1 Jerarquía universal

```text
1. Datos crudos o experimentales reproducibles.
2. Scripts ejecutables y configuraciones activas.
3. Resultados generados desde scripts.
4. Figuras y tablas generadas desde resultados.
5. Protocolo experimental o metodológico.
6. Matriz única de trazabilidad.
7. Bibliografía verificada.
8. Notas técnicas.
9. Texto del manuscrito.
```

### 10.2 Regla ante conflictos

Si el texto contradice la evidencia, se corrige el texto.

Si una figura contradice los datos, se revisa el script o se bloquea la figura.

Si una tabla contradice el CSV fuente, se corrige la tabla.

Si un claim no puede verificarse, se marca como:

```text
BLOCKED_BY_EVIDENCE
```

Si una referencia no puede verificarse, se marca como:

```text
REFERENCE_NOT_VERIFIED
```

---

## 11. Claims permitidos, condicionados y prohibidos

### 11.1 Objetivo

Controlar la fuerza del lenguaje científico y evitar conclusiones no soportadas.

### 11.2 Categorías

| Categoría | Significado | Acción |
|---|---|---|
| Permitido | Está soportado por evidencia suficiente. | Puede usarse. |
| Condicionado | Depende de contexto, escenario, muestra, corpus o restricción. | Usar con condición explícita. |
| Prohibido | No está soportado o excede el alcance. | No usar. |

### 11.3 Plantilla

```markdown
## Claims permitidos, condicionados y prohibidos

### Claims permitidos
- 

### Claims condicionados
- 

### Claims prohibidos
- 

### Redacciones permitidas
- 

### Redacciones prohibidas
- 
```

### 11.4 Reglas de intensidad

| Intensidad | Término permitido | Evidencia mínima |
|---|---|---|
| Baja | suggests, is consistent with, may indicate | Evidencia diagnóstica o parcial. |
| Media | indicates, shows | Métrica, figura o tabla verificable. |
| Alta | demonstrates | Métrica, baseline, protocolo y evidencia reproducible. |
| Muy alta | consistently outperforms | Evaluación multi-escenario con soporte estadístico. |
| Prohibida | universal, state-of-the-art, best overall, deployment-ready | No usar salvo demostración externa exhaustiva y explícita. |

### 11.5 Regla de reescritura

Si un claim es útil pero excesivo, el agente debe suavizarlo.

Ejemplo:

```text
No permitido:
The proposed method guarantees stable operation under all disturbances.

Permitido:
The tested results indicate improved stability margins under the evaluated disturbances.
```

---

## 12. Unidad mínima de trazabilidad

La unidad mínima de trazabilidad debe unir claim, evidencia, fuente, ubicación, prueba y redacción permitida.

```text
claim_id + evidence_id + source_path + figure/table + section_or_module + permitted_wording + forbidden_wording + test_id + status
```

Esta unidad reemplaza matrices separadas de claims, evidencia, figuras, tablas y verificación.

---

## 13. Matriz única de trazabilidad

Archivo:

```text
ops/sted/traceability_matrix.csv
```

### 13.1 Columnas recomendadas

```csv
id,type,text_or_item,section_or_module,evidence_id,source_path,figure_or_table,permitted_wording,forbidden_wording,test_id,status,action,owner,gate
```

### 13.2 Tipos permitidos

| Tipo | Uso |
|---|---|
| `claim` | Afirmación científica, técnica, bibliográfica o editorial. |
| `evidence` | Dato, script, resultado, protocolo, referencia o archivo fuente. |
| `figure` | Figura usada o propuesta. |
| `table` | Tabla usada o propuesta. |
| `equation` | Ecuación o formulación matemática. |
| `reference` | Referencia bibliográfica. |
| `decision` | Decisión metodológica o editorial relevante. |
| `test` | Prueba asociada a una condición de aceptación. |

### 13.3 Estados permitidos

| Estado | Significado |
|---|---|
| `verified` | Verificado y usable. |
| `partially_verified` | Parcialmente soportado. Requiere condición. |
| `pending` | Pendiente de revisión. |
| `blocked` | No puede usarse hasta resolver evidencia. |
| `obsolete` | Reemplazado por evidencia más reciente. |
| `out_of_scope` | Fuera del alcance congelado. |

### 13.4 Ejemplo

```csv
id,type,text_or_item,section_or_module,evidence_id,source_path,figure_or_table,permitted_wording,forbidden_wording,test_id,status,action,owner,gate
CLM-001,claim,"The benchmark shows target-dependent behavior.",Introduction,EV-010,results/summary.csv,Fig.3,"shows target-dependent behavior","proves universal superiority",T-003,verified,keep,integrator,G2
FIG-001,figure,"performance heatmap",Results,EV-011,scripts/figures/plot_heatmap.py,Fig.4,"shows comparative error patterns","proves best model",T-004,pending,verify,figure-table-auditor,G3
REF-001,reference,"Foundational paper for method X",Related Work,EV-020,paper/bibliography/references.bib,,"supports background","supports our result",T-006,verified,keep,literature-auditor,G2
```

---

## 14. Fases STED-RW Lean

STED-RW Lean usa seis fases.

| Fase | Nombre | Objetivo | Gate |
|---:|---|---|---|
| 0 | Inicialización | Crear estructura mínima, definir tipo de proyecto y activar integrador. | G0 |
| 1 | Especificación y alcance | Congelar tesis, alcance, contribuciones y claims permitidos/prohibidos. | G1 |
| 2 | Evidencia y trazabilidad | Registrar evidencia, claims, figuras, tablas, fuentes y estado. | G2 |
| 3 | Plan y pruebas | Definir tareas, pruebas, criterios de aceptación y responsables. | G3 |
| 4 | Ejecución controlada | Redactar, programar, analizar, integrar o auditar. | G4 |
| 5 | Cierre de calidad | Revisar cumplimiento contra plan, trazabilidad y pruebas. | G5 |

---

## 15. Gates de fase

Los gates impiden avanzar cuando falta información crítica.

### 15.1 Tabla de gates

| Gate | Permite avanzar a | Condición mínima |
|---|---|---|
| G0 | Fase 1 | Existe estructura mínima, integrador activo y producto identificado. |
| G1 | Fase 2 | Decisión central, alcance congelado y contribuciones defendibles definidos. |
| G2 | Fase 3 | Claims críticos y evidencia mínima trazados en la matriz única. |
| G3 | Fase 4 | Tareas y pruebas mínimas definidas. |
| G4 | Fase 5 | Producto o modificación ejecutada con trazabilidad actualizada. |
| G5 | Entrega | El integrador aprueba el cierre o indica bloqueos. |

### 15.2 Estados de gate

| Estado | Significado |
|---|---|
| `open` | La fase está activa. |
| `passed` | Puede avanzar. |
| `passed_with_caveats` | Puede avanzar con limitaciones registradas. |
| `blocked` | No puede avanzar. |
| `rework_required` | Requiere corrección antes de avanzar. |

### 15.3 Regla de gate

Todo paso de fase debe registrarse en `decision_log.md`.

Formato:

```markdown
## DEC-001
Fecha:
Gate:
Decisión:
Justificación:
Evidencia revisada:
Limitaciones:
Responsable:
Estado:
```

---

## 16. Fase 0: Inicialización

### 16.1 Objetivo

Crear o verificar la estructura mínima del proyecto y activar el integrador.

### 16.2 Entradas

- Solicitud del usuario.
- Tipo de producto.
- Repositorio o carpeta base.
- Archivos existentes.

### 16.3 Salidas mínimas

```text
plan_maestro.md
ops/sted/traceability_matrix.csv
ops/sted/test_plan.md
ops/sted/decision_log.md
ops/sted/final_quality_report.md
ops/sted/agents_catalog.md
.claude/agents/sted_integrator.md
.agents/skills/sted-rw/SKILL.md
```

### 16.4 Criterios de aceptación

- Existe `plan_maestro.md`.
- Existe matriz única de trazabilidad.
- Existe `decision_log.md`.
- Existe `test_plan.md`.
- El integrador está definido.
- El producto final está identificado.

---

## 17. Fase 1: Especificación y alcance

### 17.1 Objetivo

Congelar el propósito del proyecto antes de ejecutar.

### 17.2 Contenido obligatorio en `plan_maestro.md`

- Identidad del proyecto.
- Decisión científica/editorial central.
- Alcance incluido.
- Alcance excluido.
- No prometer.
- Tesis principal.
- Versión conservadora.
- Contribuciones defendibles.
- Claims permitidos, condicionados y prohibidos.

### 17.3 Criterios de aceptación

- El agente puede distinguir qué debe hacer y qué no debe hacer.
- La tesis principal no contradice el alcance.
- Las contribuciones tienen evidencia requerida.
- Los claims prohibidos están explícitos.
- El integrador aprueba G1.

---

## 18. Fase 2: Evidencia y trazabilidad

### 18.1 Objetivo

Registrar la evidencia mínima que soportará claims, figuras, tablas, ecuaciones y decisiones.

### 18.2 Acciones

1. Identificar manuscritos, datos, scripts, figuras, tablas, referencias y resultados.
2. Registrar cada elemento relevante en `traceability_matrix.csv`.
3. Vincular claims con evidencia.
4. Marcar elementos no verificados como `pending` o `blocked`.
5. Bloquear claims sin evidencia.

### 18.3 Criterios de aceptación

- Los claims críticos están en la matriz.
- La evidencia principal tiene ruta o fuente.
- Las figuras y tablas principales tienen fuente.
- Los claims prohibidos no aparecen como permitidos.
- El integrador aprueba G2.

---

## 19. Fase 3: Plan y pruebas

### 19.1 Objetivo

Definir tareas y pruebas mínimas antes de ejecutar.

### 19.2 `test_plan.md`

El archivo debe contener solo pruebas necesarias para el objetivo actual. No debe convertirse en inventario exhaustivo irrelevante.

Plantilla:

```markdown
# Test Plan

| Test ID | Tipo | Elemento asociado | Descripción | Criterio de aceptación | Estado | Responsable |
|---|---|---|---|---|---|---|
| T-001 | claim | CLM-001 | Verificar que el claim tiene evidencia trazada. | Claim con evidencia verified o partially_verified. | pending | integrator |
```

### 19.3 Tipos de prueba

| Tipo | Qué verifica |
|---|---|
| `claim` | La afirmación no excede la evidencia. |
| `data` | Datos presentes, consistentes y no alterados. |
| `metric` | Métricas calculadas correctamente. |
| `figure` | Figura trazada a datos y script. |
| `table` | Tabla trazada a fuente. |
| `equation` | Variables, unidades y supuestos definidos. |
| `reference` | Referencia verificable. |
| `text` | Coherencia entre secciones. |
| `code` | Código ejecutable y reproducible. |
| `editorial` | Estilo, siglas, terminología y estructura. |

### 19.4 Criterios de aceptación

- Cada tarea crítica tiene prueba o criterio de aceptación.
- No se diseñan pruebas innecesarias.
- Las pruebas están asociadas a elementos de la matriz.
- El integrador aprueba G3.

---

## 20. Fase 4: Ejecución controlada

### 20.1 Objetivo

Ejecutar redacción, análisis, código, revisión o integración bajo control de trazabilidad.

### 20.2 Reglas

1. No crear archivos nuevos sin justificarlo.
2. No introducir claims nuevos sin registrarlos.
3. No fortalecer claims sin evidencia.
4. No modificar metodología sin registrar decisión.
5. No cambiar resultados sin regenerar evidencia.
6. No modificar datos crudos.
7. Actualizar matriz de trazabilidad después de cambios relevantes.
8. Registrar decisiones en `decision_log.md`.

### 20.3 Salidas posibles

- Sección redactada.
- Código modificado.
- Figura generada.
- Tabla generada.
- Capítulo redactado.
- Auditoría puntual.
- Revisión editorial.
- Matriz actualizada.
- Decisión registrada.

### 20.4 Criterios de aceptación

- La salida cumple la tarea.
- La salida respeta el alcance.
- Los claims nuevos están trazados.
- Las pruebas necesarias se ejecutaron o revisaron.
- El integrador aprueba G4.

---

## 21. Fase 5: Cierre de calidad

### 21.1 Objetivo

Consolidar el producto final y registrar la decisión de calidad del integrador.

### 21.2 `final_quality_report.md`

Plantilla mínima:

```markdown
# Final Quality Report

## 1. Producto evaluado

## 2. Archivos relevantes

## 3. Gates

| Gate | Estado | Observación |
|---|---|---|
| G0 |  |  |
| G1 |  |  |
| G2 |  |  |
| G3 |  |  |
| G4 |  |  |
| G5 |  |  |

## 4. Cumplimiento de alcance

## 5. Claims críticos

## 6. Evidencia usada

## 7. Pruebas revisadas

## 8. Bloqueos pendientes

## 9. Decisión final

- [ ] Aprobado
- [ ] Aprobado con salvedades
- [ ] Requiere revisión
- [ ] Bloqueado

## 10. Observaciones del integrador
```

### 21.3 Criterios de aceptación

- El integrador emite decisión final.
- Los bloqueos quedan explícitos.
- Las salvedades quedan registradas.
- El producto no contradice el alcance congelado.
- La matriz de trazabilidad refleja el estado final.

---

## 22. Agente integrador obligatorio

El **STED-RW Integrator** es el agente principal del flujo. Coordina agentes especializados, reduce archivos, resuelve conflictos y controla gates.

### 22.1 Archivo recomendado

```text
.claude/agents/sted_integrator.md
```

### 22.2 Definición

```markdown
# STED-RW Integrator

## Misión

Coordinar el flujo completo STED-RW Lean, reducir artefactos innecesarios, resolver conflictos entre agentes y garantizar que el producto final cumpla objetivo, evidencia, pruebas, alcance y calidad editorial.

## Responsabilidades

1. Mantener `plan_maestro.md` como fuente de verdad.
2. Autorizar el paso entre fases.
3. Consolidar outputs de agentes especializados.
4. Evitar archivos redundantes.
5. Resolver conflictos usando la jerarquía de evidencia.
6. Mantener `traceability_matrix.csv`.
7. Verificar que cada fase produzca valor real.
8. Bloquear redacción o implementación si falta evidencia crítica.
9. Registrar decisiones en `decision_log.md`.
10. Emitir decisión final en `final_quality_report.md`.

## Límites

- No inventa evidencia.
- No fortalece claims.
- No reemplaza al experto humano.
- No aprueba una fase con claims críticos no verificados.
- No crea archivos nuevos salvo que desbloqueen un gate o sean productos finales.

## Entradas obligatorias

- `plan_maestro.md`
- `ops/sted/traceability_matrix.csv`
- `ops/sted/test_plan.md`
- `ops/sted/decision_log.md`
- Producto o tarea solicitada.

## Salidas obligatorias

- Actualización de `plan_maestro.md` si cambia el alcance.
- Actualización de `traceability_matrix.csv` si hay claims, evidencias, figuras, tablas o referencias nuevas.
- Actualización de `decision_log.md` si se toma una decisión.
- Actualización de `final_quality_report.md` en cierre.

## Decisiones posibles

- avanzar
- avanzar con salvedades
- bloquear
- solicitar evidencia
- solicitar aclaración
- reducir alcance
- dividir tarea
- fusionar archivos
- eliminar artefacto redundante
```

---

## 23. Catálogo de agentes

En lugar de crear un archivo por agente, los roles se registran en:

```text
ops/sted/agents_catalog.md
```

### 23.1 Roles recomendados

| Agente | Función | Crear archivo separado |
|---|---|---|
| STED-RW Integrator | Coordina todo el flujo y aprueba gates. | Sí |
| Spec Manager | Apoya especificación y alcance. | No |
| Evidence Auditor | Verifica evidencia. | No |
| Literature Auditor | Verifica referencias cuando aplique. | No |
| Methodology Reviewer | Revisa método, supuestos y validez. | No |
| Statistical Reviewer | Revisa métricas y claims cuantitativos. | No |
| Code/Test Engineer | Diseña o ejecuta pruebas. | No |
| Figure/Table Auditor | Verifica figuras y tablas. | No |
| Scientific Writer | Redacta texto trazable. | No |
| Style Editor | Ajusta estilo sin cambiar significado. | No |
| Critical Reviewer | Evalúa solidez y debilidades. | No |
| Final Verifier | Apoya cierre, subordinado al integrador. | No |

### 23.2 Plantilla de entrada en `agents_catalog.md`

```markdown
## Evidence Auditor

Responsabilidad:
Verificar existencia, validez y vigencia de datos, scripts, resultados, figuras, tablas y fuentes.

Entradas:
- plan_maestro.md
- traceability_matrix.csv
- archivos del repositorio

Salidas:
- filas actualizadas en traceability_matrix.csv
- observaciones para decision_log.md

Límites:
- No interpreta resultados sin evidencia suficiente.
- No inventa rutas.
- No aprueba claims sin soporte.

Criterio de éxito:
Cada evidencia crítica queda clasificada como verified, partially_verified, pending, blocked, obsolete u out_of_scope.
```

---

## 24. Skill única para agentes

Para evitar múltiples skills fragmentadas, se recomienda una sola skill:

```text
.agents/skills/sted-rw/SKILL.md
```

### 24.1 Contenido recomendado

```markdown
---
name: sted-rw
description: Use for academic research, scientific writing, technical books, software, and reproducible pipelines under the STED-RW Lean workflow.
---

# STED-RW Lean Skill

## Mandatory protocol

Before writing, coding, auditing, or modifying:

1. Read `plan_maestro.md`.
2. Read `ops/sted/traceability_matrix.csv`.
3. Read `ops/sted/test_plan.md`.
4. Read `ops/sted/decision_log.md`.
5. Identify the active phase and gate.
6. Check whether the requested task is within scope.
7. Do not create new files unless they satisfy the minimal artifact rule.

## Rules

1. Do not invent data, references, DOI, URLs, paths, results, figures, tables, or claims.
2. Every quantitative claim must be traceable.
3. Every figure and table must have a source.
4. Every conclusion must be limited by evidence.
5. Do not strengthen claims beyond evidence.
6. Do not modify raw data.
7. Register major decisions.
8. Use the hierarchy of evidence when conflicts appear.
9. Update the traceability matrix when claims, evidence, figures, tables, equations, references, or tests change.
10. The integrator controls gates.

## Output expectation

For any substantial task, report:

- Active phase.
- Gate status.
- Files inspected.
- Changes made.
- Traceability updates.
- Pending blockers.
- Recommended next step.
```

---

## 25. Comandos Claude recomendados

### 25.1 `.claude/commands/sted-init.md`

```markdown
# sted-init

Initialize STED-RW Lean.

Steps:
1. Create missing minimal files only.
2. Do not overwrite existing content.
3. Ensure `plan_maestro.md` exists.
4. Ensure `ops/sted/` exists.
5. Ensure traceability, test plan, decision log, final quality report, and agents catalog exist.
6. Create `.claude/agents/sted_integrator.md` if missing.
7. Create `.agents/skills/sted-rw/SKILL.md` if missing.
8. Report created files and skipped existing files.
```

### 25.2 `.claude/commands/sted-gate.md`

```markdown
# sted-gate

Evaluate current STED-RW gate.

Steps:
1. Read `plan_maestro.md`.
2. Read `ops/sted/traceability_matrix.csv`.
3. Read `ops/sted/test_plan.md`.
4. Read `ops/sted/decision_log.md`.
5. Determine active gate.
6. Decide:
   - passed
   - passed_with_caveats
   - blocked
   - rework_required
7. Register decision in `decision_log.md`.
```

### 25.3 `.claude/commands/sted-audit.md`

```markdown
# sted-audit

Audit current product under STED-RW Lean.

Steps:
1. Check whether current task is within scope.
2. Identify claims, figures, tables, references, equations, or code affected.
3. Update `traceability_matrix.csv`.
4. Identify unsupported or excessive claims.
5. Propose minimal corrections.
6. Do not create extra reports unless requested by the integrator.
```

### 25.4 `.claude/commands/sted-verify.md`

```markdown
# sted-verify

Verify current output before delivery.

Steps:
1. Read plan, traceability matrix, test plan and decision log.
2. Check active gate.
3. Check pending blocked items.
4. Check claims introduced by the output.
5. Check figure/table/source consistency if applicable.
6. Update `final_quality_report.md`.
7. Return final decision.
```

---

## 26. Prompts operativos compactos

### 26.1 Prompt general

```text
Trabaja bajo STED-RW Lean.

Antes de ejecutar:
1. Lee plan_maestro.md.
2. Lee ops/sted/traceability_matrix.csv.
3. Lee ops/sted/test_plan.md.
4. Lee ops/sted/decision_log.md.
5. Identifica fase y gate activo.
6. Verifica si la tarea está dentro del alcance congelado.
7. No crees archivos nuevos salvo que desbloqueen un gate o sean producto final.

Durante la ejecución:
1. No inventes datos, referencias, rutas, resultados ni claims.
2. Registra claims nuevos en la matriz única.
3. No fortalezcas afirmaciones sin evidencia.
4. Usa la jerarquía de evidencia para resolver conflictos.
5. Si falta evidencia crítica, bloquea el claim.

Al entregar:
1. Indica archivos revisados.
2. Indica cambios realizados.
3. Indica filas de trazabilidad afectadas.
4. Indica pruebas revisadas.
5. Indica bloqueos pendientes.
6. Recomienda el siguiente paso.
```

### 26.2 Prompt para artículo científico

```text
Actúa bajo STED-RW Lean como equipo coordinado por el STED-RW Integrator.

Tarea:
Auditar, mejorar o redactar una sección de artículo científico.

Proceso:
1. Verifica decisión editorial central y alcance congelado en plan_maestro.md.
2. Revisa claims permitidos, condicionados y prohibidos.
3. Usa solo evidencia registrada o registra nueva evidencia en traceability_matrix.csv.
4. Redacta sin introducir claims no trazados.
5. Mantén estilo IEEE/Elsevier.
6. No uses lenguaje más fuerte que la evidencia.
7. Actualiza decision_log.md si se toma una decisión metodológica o editorial.
8. Reporta gate activo y estado de la tarea.
```

### 26.3 Prompt para libro técnico

```text
Actúa bajo STED-RW Lean como arquitecto editorial y experto técnico.

Tarea:
Diseñar, auditar o redactar contenido de libro técnico.

Proceso:
1. Revisa tesis editorial y audiencia en plan_maestro.md.
2. Verifica profundidad esperada y alcance congelado.
3. Asegura progresión conceptual.
4. No conviertas capítulos en listas inconexas.
5. Introduce ecuaciones solo si agregan capacidad analítica.
6. Registra conceptos, figuras, ejemplos o claims clave en traceability_matrix.csv.
7. Mantén coherencia terminológica.
8. Reporta decisiones en decision_log.md.
```

### 26.4 Prompt para software o pipeline

```text
Actúa bajo STED-RW Lean como Code/Test Engineer coordinado por el integrador.

Tarea:
Diseñar, auditar o modificar código científico o pipeline reproducible.

Proceso:
1. Revisa objetivo, alcance y restricciones.
2. No modifiques datos crudos.
3. No cambies lógica experimental sin decisión registrada.
4. Diseña o actualiza pruebas mínimas en test_plan.md.
5. Registra outputs, scripts, métricas, tablas o figuras en traceability_matrix.csv.
6. Ejecuta cambios mínimos.
7. Reporta pruebas revisadas y bloqueos.
```

---

## 27. Integración con estructura existente

Para una plantilla como:

```text
PAPER_PLANTILLA/
  .agents/
  .claude/
  .codex/
  ops/
  paper/
  research/
  reviews/
  scripts/
  venv/
  .gitignore
  AGENTS.md
  CLAUDE.md
  plan_maestro.md
  README.md
```

La integración recomendada es:

```text
PAPER_PLANTILLA/
  AGENTS.md
  CLAUDE.md
  plan_maestro.md
  README.md

  ops/
    sted/
      traceability_matrix.csv
      test_plan.md
      decision_log.md
      final_quality_report.md
      agents_catalog.md

  .agents/
    skills/
      sted-rw/
        SKILL.md

  .claude/
    agents/
      sted_integrator.md
    commands/
      sted-init.md
      sted-gate.md
      sted-audit.md
      sted-verify.md

  .codex/
    prompts/
      sted-execute.md
      sted-verify.md
```

### 27.1 Qué no duplicar

No repetir todo STED-RW en:

- `AGENTS.md`
- `CLAUDE.md`
- `.agents/skills/sted-rw/SKILL.md`
- prompts de Codex
- comandos de Claude

Cada archivo debe tener función distinta:

| Archivo | Contenido recomendado |
|---|---|
| `AGENTS.md` | Reglas universales breves. |
| `CLAUDE.md` | Comportamiento específico para Claude. |
| `plan_maestro.md` | Fuente de verdad del proyecto. |
| `SKILL.md` | Protocolo operativo reutilizable. |
| `sted_integrator.md` | Rol del integrador. |
| `.codex/prompts/` | Prompts prácticos de ejecución y verificación. |

---

## 28. Contenido mínimo para `AGENTS.md`

```markdown
# AGENTS.md

This repository follows STED-RW Lean.

Before writing, coding, auditing, or modifying, agents must read:

1. `plan_maestro.md`
2. `ops/sted/traceability_matrix.csv`
3. `ops/sted/test_plan.md`
4. `ops/sted/decision_log.md`

Rules:

1. Do not invent data, references, DOI, URLs, paths, results, figures, tables, or claims.
2. Do not create new files unless they unlock a gate, contain non-representable evidence, are executable scripts, or are final products.
3. Every claim must be traceable.
4. Every figure and table must have a source.
5. Do not strengthen claims beyond evidence.
6. Use the hierarchy of evidence.
7. The STED-RW Integrator controls gates and final approval.
```

---

## 29. Contenido mínimo para `CLAUDE.md`

```markdown
# CLAUDE.md

## Operating model

Use STED-RW Lean.

## Mandatory inspection before substantial work

- `plan_maestro.md`
- `ops/sted/traceability_matrix.csv`
- `ops/sted/test_plan.md`
- `ops/sted/decision_log.md`

## Mandatory behavior

1. Identify active phase and gate.
2. Check scope before acting.
3. Avoid unnecessary files.
4. Register decisions.
5. Update traceability when claims, evidence, figures, tables, equations, references, tests, or outputs change.
6. Escalate to the STED-RW Integrator when evidence is missing or scope changes.

## Forbidden

- Inventing evidence.
- Creating unneeded reports.
- Strengthening claims.
- Modifying raw data.
- Changing methodology without decision log.
```

---

## 30. Criterio de calidad final

Un proyecto gestionado con STED-RW Lean es aceptable si:

1. El objetivo está definido.
2. El alcance está congelado.
3. La decisión editorial o técnica central está clara.
4. Los claims críticos están trazados.
5. Las figuras y tablas principales tienen fuente.
6. Las pruebas mínimas están definidas.
7. Las decisiones importantes están registradas.
8. El producto final no contradice el alcance.
9. El integrador emite decisión final.
10. No hay archivos accesorios que no aporten al proceso.

---

## 31. Diferencia frente a STED-RW completo

| Aspecto | STED-RW completo | STED-RW Lean |
|---|---|---|
| Fases | 9 | 6 |
| Archivos obligatorios | Muchos | 5 + catálogo de agentes |
| Matrices | Varias | Una matriz única |
| Agentes | Muchos archivos posibles | Un integrador obligatorio + catálogo |
| Reportes | Varios reportes específicos | Reporte final único salvo necesidad |
| Enfoque | Control exhaustivo | Control suficiente y trazable |
| Mejor uso | Proyectos grandes con auditoría extensa | Flujo diario de papers, libros y software con agentes |

---

## 32. Recomendación de uso por nivel

| Nivel | Uso | Archivos mínimos |
|---|---|---|
| Ligero | Tarea puntual o sección corta | `plan_maestro.md`, `traceability_matrix.csv`, `decision_log.md` |
| Intermedio | Paper, capítulo, pipeline pequeño | Núcleo completo STED-RW Lean |
| Completo | Paper Q1, libro, software científico | Núcleo + módulos específicos según necesidad |

---

## 33. Regla final

STED-RW Lean debe impedir dos extremos:

1. **Improvisación sin evidencia.**
2. **Burocracia sin impacto en el producto final.**

La regla final es:

> Crear solo lo necesario. Verificar todo lo importante. Integrar antes de entregar.

---

**Fin del documento.**
