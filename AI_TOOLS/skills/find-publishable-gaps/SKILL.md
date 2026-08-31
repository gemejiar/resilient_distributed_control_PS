---
name: find-publishable-gaps
description: Identifica, verifica y prioriza gaps científicos o tecnológicos remanentes y contribuciones potencialmente publicables a partir de un tópico específico y un corpus de papers. Úsala para revisión crítica, formulación de preguntas de investigación o construcción de agendas; no para revisiones meramente descriptivas o resúmenes artículo por artículo.
---

# Find Publishable Gaps

Produce un mapa defendible de gaps remanentes, no una lista de temas poco estudiados. Un gap aceptable debe vincular una capacidad necesaria, una limitación repetida o demostrable del estado del arte, el mecanismo que causa esa limitación y una consecuencia científica o tecnológica relevante.

## Entradas y alcance

Trabaja con un tópico delimitado, papers de referencia y las restricciones indicadas por el usuario. Si falta una frontera importante, adopta una delimitación razonable y declárala. Pregunta solo cuando diferentes delimitaciones cambiarían materialmente la investigación.

Distingue siempre entre conclusiones respaldadas por el corpus, inferencias razonadas y asuntos que requieren búsqueda o texto completo adicional. No presentes ausencia en el corpus como ausencia en la literatura mundial. Cuando el usuario pida gaps actuales o exhaustivos, verifica mediante búsqueda reciente y fuentes primarias. No uses el resumen como sustituto del texto completo cuando debas juzgar mecanismo, baseline, evidencia o limitaciones.

## Flujo esencial

### 1. Formular la frontera del problema

Convierte el tópico en una frase operacional que incluya sistema, capacidad, condiciones difíciles y restricciones relevantes. Evita dominios excesivamente amplios.

### 2. Construir la matriz de evidencia

Para cada paper extrae capacidad objetivo, supuesto habilitante, método/mecanismo, condiciones de validación, baseline, métricas, resultados, limitaciones declaradas, limitaciones inferidas y frontera real de la evidencia. Usa el esquema de [patterns.md](references/patterns.md).

Excluye o marca reviews/surveys si el objetivo es descubrir contribuciones originales. Pueden orientar la búsqueda, pero no deben contarse como evidencia experimental original.

### 3. Detectar tensiones, no solo vacíos

Busca desempeño nominal que colapsa en condiciones límite; dependencia de modelos o información poco realista; conflicto entre objetivos legítimos; interacción fallida; claims más amplios que la validación; problemas de escalabilidad o ejecución; observaciones sin explicación causal; y atributos como robusto, adaptativo, model-free, resiliente o tiempo real sin evidencia proporcional.

Agrupa los hallazgos por mecanismo de falla, no por coincidencia de palabras.

### 4. Formular cada gap como cadena causal

Un candidato debe poder expresarse así:

> Aunque el estado del arte consigue **capacidad A** bajo **condición B**, falla o pierde **propiedad C** cuando aparece **condición D**, porque **mecanismo E**. Las soluciones disponibles no satisfacen simultáneamente **requisitos F/G**, con la consecuencia **H**.

Si no puede completarse “porque”, clasifica el hallazgo como observación o gap de evidencia, no como gap causal establecido.

### 5. Diseñar una contribución correspondiente

Vincula un solo mecanismo central a cada gap prioritario:

> Introducir **objeto nuevo X**, basado en **mecanismo Y**, que elimine o relaje **supuesto Z**, preserve **propiedad P** bajo **condición Q** y pueda falsarse mediante **evidencia R** frente a **baselines S**.

La contribución puede ser teoría, modelo, método, controlador, arquitectura, firma diagnóstica, reformulación computacional o evidencia experimental. “Aplicar algoritmo X al sistema Y” no basta salvo que la transferencia exija resolver una dificultad estructural nueva.

### 6. Ejecutar una revisión adversarial

Antes de recomendar un gap, intenta refutarlo: comprueba si ya lo resuelve un paper; si es solo una combinación inédita de palabras; si el supuesto eliminado reaparece en los datos; si el baseline está debilitado; si el cambio es paramétrico; si la evidencia factible sostiene el claim; y si el valor desaparecería al incluir saturación, ruido, retrasos, degradación o cambio de distribución. Descarta los candidatos que no sobrevivan.

### 7. Puntuar y priorizar

Aplica la rúbrica de [rubric-and-output.md](references/rubric-and-output.md). Reporta por separado confianza en la existencia del gap, potencial de novedad, factibilidad de validación y madurez de la evidencia. No conviertas la puntuación en falsa precisión: explica el factor decisivo y la amenaza principal.

## Reglas de calidad

- No uses “pocos estudios”, “no encontramos” o “se necesita más investigación” como gap final.
- Separa novedad científica de novedad de aplicación.
- Separa simulación, HIL, prototipo y campo.
- Exige el baseline del estado del arte relevante y ablaciones del mecanismo propuesto.
- Ajusta la amplitud del claim a la amplitud de la validación.
- Reporta condiciones donde la propuesta probablemente no sería superior.
- Prefiere una mejora explicada causalmente a una mejora porcentual aislada.
- Mantén trazabilidad de cada premisa importante a los papers que la sostienen o contradicen.

## Entregable mínimo

Entrega frontera y cobertura del corpus; mapa de patrones; candidatos priorizados con cadena causal y trazabilidad; contribución específica asociada; experimento mínimo decisivo, baselines y métricas; riesgo de rechazo y evidencia faltante; y recomendación de los 1–3 gaps con mejor relación novedad–relevancia–factibilidad.

Si la evidencia no permite afirmar un gap fuerte, dilo y especifica qué papers, datos o pruebas faltan. No rellenes la salida con candidatos débiles.
