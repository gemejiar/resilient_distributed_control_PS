# Rúbrica de publicabilidad y formato de salida

## Puntuación por candidato

Puntúa 0–2 y justifica cada dimensión.

| Dimensión | 0 | 1 | 2 |
|---|---|---|---|
| Relevancia | Consecuencia marginal | Relevancia contextual | Bloquea una capacidad importante |
| Especificidad causal | Ausencia genérica | Condición o causa parcial | Condición, mecanismo y consecuencia precisos |
| Evidencia del gap | Conjetura | Uno o dos indicios | Convergencia de papers/datos independientes |
| Novedad potencial | Cambio rutinario | Extensión no trivial | Nuevo principio, mecanismo o capacidad |
| Necesidad | Ya hay solución suficiente | Soluciones incompletas | Limitación estructural no resuelta |
| Falsabilidad | Claim vago | Prueba posible | Experimento decisivo y métricas claras |
| Baselines | Débiles o ausentes | Convencionales | Estado del arte, ablaciones y límites |
| Factibilidad | Recursos inaccesibles | Riesgo moderado | Validación viable con recursos identificados |
| Generalización | Caso favorable | Varias condiciones | Dominio y límites examinables |
| Trazabilidad | Sin fuentes | Parcial | Premisas vinculadas a evidencia específica |

Interpretación orientativa sobre 20:

- 16–20: candidato fuerte; realizar búsqueda final de anterioridad.
- 13–15: prometedor; reforzar mecanismo o validación.
- 9–12: incremental, inmaduro o dependiente de evidencia faltante.
- 0–8: no recomendar como gap publicable en su forma actual.

No uses el total sin discusión. Un cero en evidencia, falsabilidad o factibilidad puede invalidar un candidato aunque la suma sea alta.

## Registro de candidato

Para cada gap priorizado presenta:

- **Cadena causal:** condición → mecanismo → variable afectada → consecuencia.
- **Estado del arte:** qué puede hacer y bajo qué supuestos.
- **Gap remanente:** formulación completa y delimitada.
- **Trazabilidad:** papers que lo apoyan, soluciones parciales y contradicciones.
- **Contribución publicable posible:** objeto nuevo y mecanismo central.
- **Diferencia frente a lo existente:** supuesto eliminado o capacidad añadida.
- **Experimento mínimo decisivo:** escenario que podría refutar la propuesta.
- **Baselines y ablaciones:** comparadores necesarios.
- **Métricas:** técnicas, computacionales, económicas o de seguridad.
- **Nivel de evidencia requerido:** análisis, simulación, EMT, HIL, prototipo o campo.
- **Riesgo de rechazo:** principal objeción probable de revisores.
- **Confianza:** alta, media o baja y su causa.
- **Puntuación:** total y dimensiones decisivas.

## Resumen ejecutivo recomendado

| Prioridad | Gap causal | Contribución candidata | Evidencia decisiva | Riesgo principal | Confianza |
|---:|---|---|---|---|---|

Después recomienda solo 1–3 candidatos. Para cada uno explica por qué importa, por qué sigue abierto, cuál sería la unidad mínima de novedad, qué resultado convertiría la idea en publicable y qué resultado obligaría a abandonarla.

## Búsquedas dirigidas posteriores

Cuando queden premisas sin verificar, genera queries por mecanismo, no solo por tópico:

- `"método dominante" AND limitation AND "condición límite"`
- `"capacidad" AND (failure OR instability OR degradation) AND "mecanismo"`
- `"método" AND (experimental OR hardware OR field) AND benchmark`
- `"claim" AND (counterexample OR sensitivity OR robustness)`
- `"sistema" AND "supuesto eliminado" AND control`

Especifica qué afirmación debe confirmar o refutar cada búsqueda.
