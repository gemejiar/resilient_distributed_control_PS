# Evaluaciones de `gabriel_scientific_writer`

Casos de prueba de la skill. No se cargan en contexto durante el uso normal: son para
validar la skill cuando se modifica.

## Como ejecutarlos

No hay runner automatico (skill-creator no provee uno). Se ejecutan como **dry-run**:

1. Abre una sesion limpia con la skill cargada.
2. Pasa el `query` del caso (y los `files` si los declara).
3. Compara la salida contra cada linea de `expected_behavior`.
4. El caso **aprueba** solo si se cumplen todas las lineas. Un solo fallo lo reprueba.

## Que cubre cada caso

| Caso | Que verifica |
|---|---|
| `EVAL-01-forbidden-wording` | Respeta `permitted_wording` y rechaza `forbidden_wording` de la matriz de trazabilidad |
| `EVAL-02-blocked` | Reporta `BLOCKED` cuando el claim excede la evidencia, en vez de redactar |
| `EVAL-03-missing-no-resoluble` | No inventa datos; conserva `[MISSING]` o condiciona |
| `EVAL-04-comparacion-no-equivalente` | No declara superioridad entre EMT y fasorial |
| `EVAL-05-pulido-quirurgico` | Modo 2: no reestructura, no toca `\cite`/`\ref`, quita adjetivos sin metrica |
| `EVAL-06-diagnostico-no-reescribe` | Modo 4: diagnostica sin reescribir |
| `EVAL-07-estabilidad-terminologica` | No introduce sinonimos artificiales para terminos tecnicos |
| `EVAL-08-claim-formal-sin-respaldo` | No escribe `stable`/`passive`/etc. sin argumento formal (rigor matematico) |
| `EVAL-09-highlights-longitud` | Highlights de Elsevier: 3-5 bullets, <=85 caracteres, claim verificable |

## Al modificar la skill

Vuelve a correr los 9 casos. Los mas fragiles son `EVAL-01` y `EVAL-02`: dependen de que la skill
consulte `ops/sted/traceability_matrix.csv` antes de afirmar un claim. Si esos dos fallan, la skill
perdio su garantia principal. `EVAL-08` guarda el mismo tipo de garantia para claims matematicos
formales (no numericos).
