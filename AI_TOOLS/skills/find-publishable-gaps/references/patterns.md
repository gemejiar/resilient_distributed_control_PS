# Matriz de extracción y patrones de gaps

## Matriz por paper

| Campo | Pregunta operativa |
|---|---|
| Capacidad objetivo | ¿Qué debe conseguir el sistema o método? |
| Objeto aportado | ¿Teoría, modelo, método, controlador, arquitectura, datos o experimento? |
| Mecanismo | ¿Por qué debería funcionar? |
| Supuestos | ¿Qué debe conocerse, medirse o permanecer constante? |
| Dominio | ¿Red, escala, régimen, topología y rango paramétrico? |
| Baselines | ¿Contra qué alternativas se prueba? |
| Evidencia | ¿Análisis, simulación, EMT, HIL, prototipo o campo? |
| Métricas | ¿Qué variable mejora y cuánto? |
| Ablaciones | ¿Se aísla el efecto del mecanismo nuevo? |
| Frontera del claim | ¿Qué afirmación cubre realmente la validación? |
| Limitación declarada | ¿Qué reconocen los autores? |
| Limitación inferida | ¿Qué amenaza omiten? |
| Próximo bloqueo | ¿Qué impide ampliar la capacidad? |

## Patrones característicos

### Fragmentación conceptual

Señal: teorías separadas describen estructuras semejantes y producen conclusiones incompatibles.

Contribución posible: dualidad, modelo generalizado, taxonomía causal o condición de equivalencia que produzca predicciones nuevas.

### Falla en el borde operacional

Señal: buen desempeño nominal, degradación con saturación, SCR extremo, fallas, desbalance, armónicos, límites térmicos o no linealidad.

Contribución posible: mecanismo que preserve una propiedad crítica bajo el borde, con límites de validez explícitos.

### Dependencia de información irrealista

Señal: exige modelo exacto, parámetros confidenciales, observabilidad completa, pronóstico perfecto o comunicación continua.

Contribución posible: identificación online, estimación, control basado en datos, descentralización o diseño robusto. Verificar que la dependencia no reaparezca en el entrenamiento.

### Conflicto entre objetivos

Señal: protección versus sincronización; eficiencia versus THD; flexibilidad versus degradación; desempeño versus comunicación; optimalidad versus robustez.

Contribución posible: cambiar la frontera de compromiso mediante co-diseño o un mecanismo que desacople parcialmente los objetivos. Una suma ponderada rutinaria es débil.

### Coordinación e interacción

Señal: componentes correctos por separado fallan juntos, operan en escalas distintas o compiten por el mismo recurso.

Contribución posible: coordinación jerárquica, multiescala, multiagente o agregación con restricciones de interacción.

### Gap causal o diagnóstico

Señal: el fenómeno se observa, pero mecanismos competidores producen curvas similares.

Contribución posible: firma medible que diferencie causas, modelo identificable o experimento discriminante.

### Gap de escalabilidad o ejecución

Señal: algoritmo correcto pero demasiado lento, centralizado, sensible al tamaño o dependiente de combinatoria.

Contribución posible: forma cerrada, convexificación, descomposición, surrogate verificable o reducción de mediciones.

### Gap de evidencia

Señal: claims de robustez, tiempo real, resiliencia o generalidad basados en un único caso favorable.

Contribución posible: benchmark, dataset, HIL, prototipo o evidencia de campo que pruebe o refute la afirmación. No presentarlo como gap causal si solo falta validación.

## Pruebas contra falsos gaps

- **Novedad combinatoria:** “A+B+C nunca se combinaron” no implica necesidad.
- **Cambio cosmético:** sustituir optimizador, red neuronal o metaheurística sin nuevo mecanismo.
- **Baseline de paja:** mejora contra PI/PID cuando existen métodos comparables más fuertes.
- **Model-free nominal:** datos generados exclusivamente por el modelo que se afirma evitar.
- **Escalabilidad nominal:** pocos nodos o agentes sin complejidad ni prueba de crecimiento.
- **Robustez nominal:** un solo nivel de ruido, perturbación o incertidumbre.
- **Experimento nominal:** controller-HIL presentado como validación de potencia física.
- **Future work aislado:** una limitación declarada por un solo paper sin corroboración.

## Cadena de trazabilidad

Para cada candidato conserva:

`papers que establecen la capacidad` → `papers que muestran la limitación` → `evidencia del mecanismo` → `soluciones parciales` → `residuo no resuelto`.

Si falta un eslabón, reduce la confianza o formula una búsqueda dirigida para completarlo.
