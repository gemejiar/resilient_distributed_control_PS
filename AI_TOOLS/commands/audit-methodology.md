Realiza una auditoría metodológica rigurosa de una investigación propuesta o en curso.

Sigue el SOP en `02_routines/sop_methodology_check.md`.
Usa el template en `03_templates/template_methodology_audit.md`.

Solicita al usuario:
1. Descripción del estudio o metodología propuesta
2. Tipo de problema (clasificación, control, optimización, predicción, comparación, etc.)
3. ¿Hay paper, propuesta o solo una idea?

Evalúa y reporta explícitamente:
- Supuestos no declarados
- Riesgo de data leakage
- Ausencia de baselines
- Problemas de partición temporal
- Métricas inadecuadas para el tipo de problema
- Amenazas a la validez interna y externa
- Vacíos en el diseño experimental

No validar si hay problemas. Señalarlos directamente con recomendaciones accionables.
