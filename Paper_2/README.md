# Paper_2

## Objetivo científico

Campaña experimental nueva y metodológicamente independiente de `Paper_1`,
orientada a lograr una mejora **grande y simultánea** de nadir de frecuencia y
RoCoF máximo frente a un baseline droop, usando un controlador híbrido
(componente física explícita + residual TD3), sin penalizar potencia ni
energía del BESS. Ver `plan_maestro_P2_TD3_Hybrid_FFC.md` para el contrato
científico completo, incluida la motivación (hallazgos negativos de `Paper_1`).

`Paper_1` permanece intacto como baseline histórico/resultado negativo
completamente reproducible. `Paper_2` no lee ni escribe ningún artefacto de
`Paper_1`; comparte únicamente el caso base IEEE-39 (copia propia en
`cases/ieee39/base/`) y el venv del repositorio.

## Simulador

- [ANDES](https://github.com/curent/andes) `2.0.0` (extra `rl`, incluye
  `gymnasium`), instalado desde PyPI.
- Python 3.12.10.
- Entorno: `venv/` en la raíz del repositorio (compartido entre papers de
  este workspace; ver `requirements.txt` / `requirements-lock.txt` en la
  raíz).

## Sistema principal

IEEE-39 bus (New England), copia propia (no symlink, no referencia a
`Paper_1/`) de `ieee39_full.xlsx` en
[`cases/ieee39/base/ieee39_full.xlsx`](cases/ieee39/base/ieee39_full.xlsx).
Este archivo nunca se sobrescribe; cualquier modificación de topología o
dispositivos debe crear una variante explícita en `cases/ieee39/variants/`.

## Ubicación de resultados reproducibles

- `Paper_2/cases/`: modelo físico (caso ANDES, copia propia).
- `Paper_2/src/`: código propio de la campaña P2.
- `Paper_2/artifacts/`: datos, modelos, métricas, figuras y tablas producidos
  por el pipeline P2 (`metrics/`, `models/`, `figures/`, `tables/`,
  `trajectories/`, `diagnostics/`, `preflight/`).
- `Paper_2/ops/sted/`: gobernanza propia (`decision_log.md`,
  `traceability_matrix.csv`), independiente de `Paper_1/ops/sted/` y de la
  raíz del repositorio.

## Estado

`PLAN_DRAFT`. Estructura y plan maestro creados; ningún entrenamiento ni test
ejecutado todavía. Ver `Paper_2/ops/sted/decision_log.md` para el estado
derivado (gate activo, próxima acción).
