# Plan Maestro P2 — Physics-Informed TD3 Hybrid FFC (IEEE-39 / ANDES)

STATUS: `PLAN_DRAFT` — presentado para aprobación del usuario. **No se ha entrenado ni ejecutado
ningún test P2 todavía.** Rama de trabajo: `p2_td3_hybrid_ffc`.

**REENCUADRE MAYOR (esta ronda, tras `STOP-P2-A = FAIL DEFINITIVO` — ver `DEC-P2-025`/`DEC-P2-026`):**
la arquitectura principal original de este plan, **`Physical F+R + TD3 residual`** (§4 original,
`P_ff = -K_f*Delta_f - K_r*RoCoF`), queda **DESCARTADA** como arquitectura principal — el componente
físico `F+R`, correctamente retuneado bajo la configuración final (`Tc=tstep=5ms`, buses `16/20`,
`Pmax=293.4MW`), **no supera al droop tuned** en ninguna de las 13 combinaciones `K_f/K_r` estables
evaluadas (`DEC-P2-025`). La arquitectura candidata revisada es **`tuned droop + TD3 residual`**
(`Kd*=4694.4 MW/Hz`, congelado en `DEC-P2-024`). `Physical F+R` se conserva únicamente como
baseline/ablation científica, no como componente de la arquitectura principal. Ver §2/§4/§14.2/§15/
§16/§20 para el texto revisado y `DEC-P2-026` para el registro formal completo. **Ningún valor físico
congelado (`Tc` candidato, buses, `Pmax`, splits) cambia por este reencuadre** — son propiedades de
la planta/diseño experimental, no de la ley de control. No se ha entrenado TD3 bajo ninguna
arquitectura todavía.

**Revisión (esta ronda, tras hallazgo de escalamiento de potencia — ver DEC-P2-004/005/006):** el
primer sweep de autoridad de potencia BESS (`alpha_P`, `Paper_2/artifacts/diagnostics/
p2e3_alpha_p_sweep.csv`, DEC-P2-004) se ejecutó con una convención de conversión de potencia heredada
de `Paper_1` que **no escalaba la potencia realmente entregada a la red** con `P_max,BESS`. Ese
artefacto queda marcado permanentemente:

```text
p2e3_alpha_p_sweep.csv (primer intento, pre-corrección) = INVALID / DO_NOT_USE / POWER_SCALING_BUG
```

No se borra (transparencia del proceso — DEC-P2-004), pero no se usa para ninguna decisión de
congelamiento. La corrección de convención (§0-bis) ya está aplicada en `Paper_2/src/p2_common.py`
(DEC-P2-005) y verificada con un gate de calibración de actuador dedicado (§7-bis, P2-E3A) antes de
reabrir el sweep de autoridad. Esta ronda también reordena las etapas de diseño (§25), separa `K_f`/
`K_r` como ganancias independientes (§14), separa la autoridad de potencia (`P_max,BESS`) del tuning
de ganancias (§13/§14), añade una etapa de caracterización dinámica del ESD1 (§7-bis, P2-E3B), y
redefine `STOP-P2-A` (§20) como un design target multicriterio en vez de un umbral rígido de 20-40%.
Ningún valor de `Tc`, `P_max,BESS`, `K_f`, `K_r` queda congelado por esta revisión — sigue pendiente
de las etapas de diseño correspondientes.

Este documento es el contrato científico de la campaña **P2**, independiente de
`Paper_1/plan_maestro_DDPG_FFC_IEEE39_ANDES.md`. Gobernanza propia en
`Paper_2/ops/sted/{decision_log.md,traceability_matrix.csv}` — nunca se registran decisiones de P2
en `Paper_1/ops/sted/` ni en la raíz del repositorio.

---

## 0. Relación con Paper_1 (no negociable)

`Paper_1` está **cerrado** y se conserva intacto como baseline histórico / resultado negativo
completamente reproducible (P1-H1 rechazada, P1-H2 no soportada, P1-H3 rechazada — ver
`Paper_1/ops/sted/decision_log.md` DEC-P1-021).

**Prohibido en toda la campaña P2:**
- modificar o eliminar artefactos, resultados T1–T8, modelos DDPG, figuras finales, `ffc_results.csv`,
  splits congelados, reward, o checkpoints de `Paper_1`;
- reescribir entradas existentes de `Paper_1/ops/sted/decision_log.md` (solo se permite **una**
  entrada nueva, ya añadida como `DEC-P1-023`, que referencia el nacimiento de P2 a partir de los
  hallazgos de P1 — ver ese archivo);
- reutilizar carpetas de artefactos de `Paper_1` como entrada/salida de código P2 (`Paper_2` tiene
  su propia copia del caso base y su propio árbol de `artifacts/`).

`Paper_2` es una estructura nueva y completamente separada:

```text
Paper_2/
    README.md
    plan_maestro_P2_TD3_Hybrid_FFC.md      (este documento)
    src/
    cases/ieee39/{base,variants}/           (copia propia, no symlink a Paper_1)
    artifacts/{metrics,models,figures,tables,trajectories,diagnostics,preflight}/
    ops/sted/{decision_log.md,traceability_matrix.csv}
```

**Decisión de gobernanza explícita del usuario, ya ejecutada:** T1–T8 de P1 **ya no son test ciego**.
Pueden usarse únicamente como referencia histórica o como escenarios de *diagnóstico/design* de P2
(por ejemplo, para verificar que un cambio corrige un fallo conocido de P1), nunca como evidencia
confirmatoria de P2-H1/H2. La evidencia confirmatoria de P2 debe venir exclusivamente de una batería
nueva y congelada (§13).

---

## 0-bis. Convención obligatoria de potencia (`Sb = 100 MVA`)

**Regla no negociable, vigente para todo código y todo artefacto de P2 a partir de esta revisión.**
ANDES resuelve `PVD1`/`ESD1` enteramente en base de sistema; **no existe ningún factor `Sn` en la
cadena algebraica que va de `Pext0` a la potencia inyectada al bus** (verificado contra el código
fuente de `andes/models/distributed/pvd1.py`, `Psum = Pext+Pref+DB_y` → `Ipul` → `Ipcmd` → `Ipout`,
todo en pu de sistema; ver DEC-P1-024/DEC-P2-004/DEC-P2-005 para la traza completa del hallazgo).

```text
Sb_MVA = 100.0

Pext0_command_pu = P_command_MW / Sb_MVA
pmx_pu           = Pmax_BESS_MW / Sb_MVA
P_delivered_MW   = Ipout_y * v * Sb_MVA
```

- `Sn` se mantiene como rating nominal del dispositivo para bookkeeping/etiquetado (`ESD1.Sn`,
  `PV.Sn`), pero **nunca** se usa como base de conversión de `Pext0` ni para reconstruir la potencia
  activa entregada.
- `pmx` (límite físico duro de `ESD1`, en pu de sistema) debe fijarse explícitamente a
  `Pmax_BESS_MW/100.0` al instanciar el dispositivo — nunca dejarse en el valor de plantilla `1.0`
  salvo que `Pmax_BESS_MW` sea exactamente 100 MW.
- Prohibido en cualquier código o artefacto activo de P2 (verificado por PF2-ACT-01/02/06, §23):
  - `dp_mw / Pmax_BESS` (o cualquier variable equivalente) como conversión de comando a pu;
  - `Ipout_y * v * Sn` como lectura de potencia entregada;
  - `pmx = 1.0` hardcodeado cuando `Pmax_BESS_MW != 100`.
- Implementación de referencia ya corregida: `Paper_2/src/p2_common.py::add_bess_pair()` (`pmx`) y
  `run_physical_scenario()`/`run_command_step_response()` (`set_paux(..., dp_mw/100.0)`, lectura
  `Ipout_y.v*v.v*100.0`) — ver docstrings inline citando esta sección.
- El primer sweep de autoridad de potencia (`p2e3_alpha_p_sweep.csv`, pre-corrección) queda marcado
  permanentemente `INVALID / DO_NOT_USE / POWER_SCALING_BUG` (ver nota de revisión al inicio del
  documento). No se borra; no se reinterpreta como evidencia de ninguna claim de P2.

---

## 1. Objetivo general

Crear una campaña experimental **P2**, separada y metodológicamente independiente de P1, cuyo
objetivo principal es maximizar simultáneamente la mejora de:

1. nadir de frecuencia;
2. RoCoF máximo;

respecto al baseline droop.

En P2 **no importa** minimizar potencia pico del BESS, energía inyectada, throughput, ni eficiencia
energética. La prioridad científica es obtener una respuesta de frecuencia claramente superior y
robusta.

---

## 2. Motivación científica

P1 produjo un hallazgo importante:

- los 3 checkpoints DDPG superaron al droop en `J_val` de validation;
- sin embargo, en el test final H1 solo pasó 1/8 escenarios;
- DDPG mejoró RoCoF en varios escenarios, pero empeoró nadir en 7/8;
- los mayores fallos ocurrieron especialmente ante load steps no vistos durante training;
- algunas políticas DDPG usaron mucha potencia BESS sin transformar esa agresividad en mejor nadir.

P2 debe atacar explícitamente cuatro problemas:

- **A.** mismatch entre reward y métricas finales;
- **B.** training distribution demasiado estrecha;
- **C.** control de 100 ms potencialmente demasiado lento para FFC agresivo;
- **D.** fragilidad/inestabilidad de DDPG.

**Hipótesis científica P2 — REVISADA tras `STOP-P2-A = FAIL DEFINITIVO` (`DEC-P2-025`/`DEC-P2-026`;
no afirmar como cierta hasta el test final):**

> Una política TD3 residual, sumada sobre un controlador droop convencional fuertemente retuneado
> (`Kd*`, `DEC-P2-024`), podría aportar una mejora adicional de nadir y RoCoF bajo diversidad de
> perturbaciones y puntos de operación no vistos por el droop durante su tuning — sin asumir que esa
> mejora existe o es material hasta el test final congelado.

**Hipótesis original (DESCARTADA, conservada por transparencia del proceso — no afirmar, no
reutilizar como si siguiera vigente):**

> ~~Un controlador híbrido basado en una componente física explícita frecuencia/RoCoF (`F+R`) más una
> política TD3 residual... puede lograr mejoras grandes y simultáneas frente a un droop ajustado.~~
> Descartada: el componente físico `F+R`, correctamente retuneado, no supera al droop tuned bajo
> ninguna configuración `K_f/K_r` evaluada (`DEC-P2-025`) — no tiene sentido pedirle a una política
> residual TD3 que "arregle" una componente física de partida que ya es inferior a la alternativa más
> simple.

---

## 3. Principio de gobernanza: tres dominios estrictamente separados

- **A. DESIGN** — escoger arquitectura física, `Tc` y presupuesto de potencia. No se usa para
  entrenar la política final ni como test final.
- **B. TRAIN / VALIDATION** — entrenar TD3 y escoger checkpoints; validation puede usarse para early
  stopping; no puede acceder al test final.
- **C. FINAL TEST** — completamente congelado antes del entrenamiento final; no se consulta durante
  desarrollo; se ejecuta una sola vez al final (single-shot, mismo principio que P1 SS31/STOP-D).

---

## 4. Controlador principal P2 — REVISADO (`DEC-P2-026`, tras `STOP-P2-A = FAIL DEFINITIVO`)

### 4.revised. Arquitectura candidata (vigente)

TD3 + droop retuneado (componente física) + residual RL:

```text
P_total,i = P_droop,i + P_RL,i

P_droop,i = -K_d* * Delta_f_i,local        (K_d* = 4694.4 MW/Hz, congelado en DEC-P2-024)

P_RL,i = a_i * P_RL,max,     a_i in [-1, 1]

P_total,i = clip(P_droop,i + P_RL,i, -P_max,BESS, +P_max,BESS)
```

Los dos BESS siguen siendo idénticos, usan realimentación LOCAL de frecuencia (mismo patrón que el
droop retuneado en `DEC-P2-024`, no la variante `global` diagnóstica de `DEC-P2-014/015`). La
componente física (`droop`) proporciona el soporte de nadir ya demostrado competitivo frente a `F+R`
(`DEC-P2-024/025`); el término TD3 residual debe demostrar, en el test final, que aporta algo que el
droop por sí solo no aporta — coordinación adaptativa, compensación no lineal, o robustez bajo
perturbaciones/operating points no vistos durante el tuning de `Kd*` (que se ajustó únicamente sobre
`gen_severe`/`load_severe` DESIGN, §2 hipótesis revisada).

**`K_f`/`K_r` NO se reutilizan en esta arquitectura** — no hay término RoCoF explícito en la
componente física principal. `RoCoF` puede seguir estando disponible como parte de la observación de
TD3 (§9, sin cambios) aunque ya no forme parte de la ley de control física de base.

### 4.original. Arquitectura original (DESCARTADA — conservada por transparencia, no reutilizar)

```text
P_i* = P_ff,i + P_RL,i
P_ff,i = -K_f * Delta_f_i - K_r * RoCoF_i          (Physical F+R, DESCARTADA como base principal)
P_RL,i = a_i * P_RL,max,     a_i in [-1, 1]
P_i* = clip(P_ff,i + P_RL,i, -P_max,BESS, +P_max,BESS)
```

Descartada en `DEC-P2-025`/`DEC-P2-026`: el componente `F+R`, correctamente retuneado bajo la
configuración final, no supera al droop tuned en ninguna de las 13 combinaciones `K_f/K_r` estables
evaluadas. `Physical F+R` se conserva como baseline/ablation científica (§15/§16), no como componente
de `P_total`.

---

## 5. No penalizar potencia ni energía

Eliminar completamente cualquier penalización sobre `|P_BESS|`, `P_peak`, `energy`, `throughput`, o
excursión de SoC (mientras SoC permanezca físicamente factible). No usar términos equivalentes a
`0.1 * e_u` ni `0.1 * E_BESS / E_max` en reward o validation (a diferencia de P1 SS15/SS17.1, que sí
los usaba). `P_peak` y `E_BESS` se siguen registrando para auditoría, pero no influyen en selección
de política.

---

## 6. Reward P2

```text
e_f = max_i |Delta_f_i| / f_ref      (max sobre los 10 generadores síncronos de métricas)
e_r = max_i |RoCoF_i| / r_ref

f_ref = 0.5 Hz   (escala de normalización, no límite regulatorio)
r_ref = 1.0 Hz/s (escala de normalización, no límite regulatorio)

r_k = -[ e_f^2 + e_r^2 + 2.0 * max(e_f, e_r)^2 ]
```

El término `2.0 * max(e_f,e_r)^2` es **obligatorio** en la configuración principal — evita que una
gran mejora de RoCoF "compense" un nadir malo o viceversa.

Penalización terminal de episodio:

```text
r_terminal = -2.0 * [ (Delta_f_peak/f_ref)^2 + (RoCoF_peak/r_ref)^2 ]
r_T += r_terminal
```

donde `Delta_f_peak`/`RoCoF_peak` son el máximo durante el episodio y sobre generadores de
`|Delta_f|`/`|RoCoF|`.

Mantener `I_fail` para fallos numéricos (mismo mecanismo que P1 SS15). `I_unsafe` se conserva
**solo** como guardrail extremo (`|Delta_f| > 0.5 Hz` o `|RoCoF| > 1.0 Hz/s`), no para modelar
comportamiento normal. **No realizar reward sweep después del primer test final** (mismo principio
que STOP-D de P1).

---

## 7. Criterio de validation `J_val_P2`

```text
J_val_P2(escenario) =
    max( |Delta_f_peak|/f_ref, RoCoF_peak/r_ref )
    + 0.25 * [ |Delta_f_peak|/f_ref + RoCoF_peak/r_ref ]

J_val_P2(global) = mean( J_val_P2(escenario) sobre escenarios de validation )
```

Selección de checkpoint exclusivamente por `argmin J_val_P2`. **No** usar training return, energy,
`P_peak`, actor loss, ni critic loss para seleccionar el mejor modelo (a diferencia de nada en P1,
que ya evitaba esto — se mantiene el mismo principio, con `J_val` redefinido sin energía).

---

## 7-bis. Etapas P2-E3A/P2-E3B — actuator calibration gate y dynamic response characterization

Ambas etapas son **obligatorias y deben pasar antes de P2-E4** (diseño de `Tc`, §8). Ninguna usa el
test final; ambas usan exclusivamente escenarios/pruebas de actuador abiertas (sin lazo de frecuencia
cerrado, sin `Alter`/contingencia — el sistema permanece en frecuencia nominal). Motivación: antes de
atribuir cualquier limitación de desempeño a `Tc`, `K_f`/`K_r` o `P_max,BESS`, hay que demostrar que
el actuador BESS entrega la potencia comandada y caracterizar su propia dinámica interna
comando→potencia — de lo contrario cualquier conclusión posterior sobre `Tc` es especulativa.

### P2-E3A — BESS actuator calibration gate

Para cada BESS, de forma independiente, aplicar comandos constantes (lazo abierto, sin `Alter`) en
0/25/50/75/100% de un `Pmax,BESS` provisional, en ambos signos, y dejar asentar la respuesta antes de
leer la potencia entregada en régimen (`P_delivered_MW = Ipout_y*v*100.0`, §0-bis). Repetir un
subconjunto con un `Pmax,BESS` **distinto** para confirmar que el techo de saturación realmente se
mueve con el rating configurado (no solo que la variable de comando cambia).

Por cada punto, registrar: `command_MW`, `Pext0_pu`, `pmx_pu`, `Ipout_y`, `bus_voltage`,
`P_delivered_MW`, `absolute_error_MW`, `relative_error`, `saturation_flag`, `TDS_success`.

Criterio de paso: `|relative_error|` pequeño y consistente en todos los puntos no saturados (banda
específica a definir empíricamente en la primera ejecución, no un número asumido a priori); saturación
ocurre exactamente en `|command_MW| >= Pmax,BESS`, ni antes ni después; `TDS_success=True` en todos los
puntos. Si este gate falla: **detener P2 y no continuar con `Tc`, `K_f`, `K_r` ni TD3.**

Artefactos: `Paper_2/artifacts/preflight/p2_actuator_calibration.csv` (implementado en
`Paper_2/src/stage_p2e3a_actuator_calibration.py`, driver compartido
`p2_common.run_command_step_response()`) y figura `commanded_MW` vs. `delivered_MW` con línea 1:1
(`Paper_2/artifacts/figures/p2_actuator_calibration.png`).

### P2-E3B — BESS dynamic response characterization

Sin lazo de frecuencia cerrado (mismo driver de lazo abierto que P2-E3A). Aplicar escalones de
potencia de amplitud moderada (dentro del rango, lejos de saturación) al comando de cada BESS por
separado y registrar `P_command(t)`/`P_delivered(t)` a resolución fina (más fina que cualquier `Tc`
candidato, para no perder la dinámica interna por sub-muestreo). Medir: effective delay, 10-90% rise
time, settling time, steady-state error, overshoot.

**Verificación obligatoria del parámetro `Tf` de `ESD1`.** `Tf` (`andes/models/distributed/esd1.py`,
default `1.0`) es el **"Integrator constant for SOC model"** — alimenta únicamente el integrador de
estado de carga (`pIG`, `T=Tf, K=sys_mva/3600/En`) y **no participa en ninguna ecuación de la cadena
comando→potencia activa**. El parámetro que sí gobierna esa cadena es `tip`
(`andes/models/distributed/pvd1.py`, "Inverter active current lag time constant", default `0.02 s`):
`Ipout = Lag(Ipcmd_y, T=tip)`, un retardo de primer orden puro aplicado a la corriente activa de
salida, después de un camino puramente algebraico (`Psum`→`PHL`→`Ipul`→`Ipcmd`). **No modificar `Tf`
ni `tip` en esta etapa** — el objetivo es medir si la dinámica observada corresponde a la configurada
(`tip` por defecto), no ajustarla.

Conclusión obligatoria de esta etapa: determinar si el cuello de botella de FFR a `Tc=100ms` está
dominado por (a) el tiempo de muestreo/actualización `Tc`, (b) la dinámica interna de `ESD1` (el lazo
`tip`), o (c) ambas — comparando el settling time medido contra `Tc`. **No atribuir la ausencia de
mejora de RoCoF a `Tc` sin esta prueba.**

Artefactos: `Paper_2/artifacts/diagnostics/p2_dynamic_response.csv` (métricas por escalón) y
`Paper_2/artifacts/trajectories/p2e3b_step_traces.npz` (trayectorias crudas), implementados en
`Paper_2/src/stage_p2e3b_dynamic_response.py`.

---

## 8. Tiempo de control `Tc` — etapa de diseño obligatoria (P2-E4, requiere P2-E3A/P2-E3B PASS)

P1 usó `Tc = 100 ms`. P2 debe investigar explícitamente una respuesta más rápida:

```text
Tc in {100 ms, 50 ms, 20 ms}
```

Esta prueba usa **únicamente escenarios DESIGN**, nunca el test final. Para cada `Tc` verificar:
TDS estable; wrapper Gymnasium correcto; número exacto de acciones; carga computacional; RoCoF
medido sin artefactos numéricos; `BusROCOF` consistente; potencia BESS aplicada correctamente;
ninguna duplicación temporal; ningún `success=False` espurio; `itm_step()` correctamente usado
(mismo mecanismo validado en P1, ver §28).

Seleccionar el menor `Tc` que (1) sea numéricamente robusto, (2) mantenga una medición RoCoF
confiable, (3) permita entrenamiento computacionalmente razonable. Prioridad esperada
`20 ms > 50 ms > 100 ms` en desempeño dinámico, **pero medirlo, no asumirlo**. Si 20 ms es estable y
viable, congelarlo; si presenta problemas, usar 50 ms. No regresar a 100 ms salvo evidencia clara.

### Filtro RoCoF

Revisar coherencia entre `Tf`, `Tw`, `Tr` de `BusROCOF` (P1: `Tf=0.02, Tw=0.02, Tr=0.05` — nótese que
este `Tf` es el del bloque `Lag` de `BusROCOF`, un objeto **distinto y sin relación** con el `Tf` de
`ESD1` documentado en §7-bis, que es la constante del integrador de SOC; evitar confundirlos en
código o prosa) y el nuevo `Tc`. Mantener **inicialmente los mismos parámetros de `BusROCOF`** para
poder comparar `Tc` de forma aislada (no cambiar simultáneamente `Tc` y el filtro). No cambiar
arbitrariamente el filtro. Prueba de consistencia obligatoria: misma perturbación física, mismo
controlador, mismo filtro, distintos `Tc` — comparar las trayectorias de RoCoF resultantes y
comprobar que la mejora aparente no provenga de aliasing o cambio de sampling, conservando idéntico
modelo físico de `BusROCOF` entre controladores. Si `Tc` se vuelve menor que algunas constantes del
filtro, documentar explícitamente que el control muestrea más rápido que la dinámica del estimador.

Si, después de seleccionar `Tc` (P2-E4) y completar el tuning físico (P2-E5), el término RoCoF sigue
sin aportar mejora medible, realizar un diagnóstico específico del estimador: puede evaluarse un
pequeño conjunto preregistrado de configuraciones de `(Tf,Tw,Tr)` de `BusROCOF`, pero **únicamente
dentro de DESIGN** — nunca usando escenarios de VALIDATION final ni el test P2-T1..T12. Evitar filtros
extremadamente rápidos que amplifiquen ruido o produzcan spikes artificiales de RoCoF: el filtrado
introduce un compromiso conocido ruido/delay (síntesis de inercia) que debe medirse en esta etapa, no
suponerse. No optimizar el filtro usando el test final.

---

## 9. Observación P2 — CONGELADA (`P2-E6b`, `DEC-P2-031/032`)

**Observación final congelada: `OBS-A` (6 señales, local, buses `16`/`20`):**

```text
[ df_16, RoCoF_16, P_BESS1,
  df_20, RoCoF_20, P_BESS2 ]
```

Normalización congelada (idéntica a la usada en la ablation `P2-E6b`, `DEC-P2-031`):
`df / F_REF_HZ(0.5Hz)`, `RoCoF / R_REF_HZ_S(1.0Hz/s)`, `P_BESS / P_max,BESS(293.4MW)`.

**Justificación de la selección (decisión explícita del usuario, `DEC-P2-032`):** en la ablation de
observación (`P2-E6b`, 1 seed, `3000` steps idénticos por variante, evaluada en los 6 escenarios de
validation), las diferencias de `J_val_P2` entre `OBS-A` (`0.5769`), `OBS-B` (`0.5743`) y `OBS-C`
(`0.5688`) son todas `<1.5%` relativo -- sin base estadística (una sola seed) para atribuir
superioridad de desempeño a `OBS-B`/`OBS-C`. Ante desempeño comparable, se prefiere `OBS-A` por
deployability (no requiere información wide-area/`COI`) y menor dependencia informacional, tal como
preveía la regla de selección pre-registrada.

**Limitación registrada explícitamente (no oculta):** `OBS-A` mostró `saturation_fraction` no nula
durante la ablation (`~0.092` promedio, hasta `~0.187` en escenarios `gen_severe`), mientras `OBS-B`/
`OBS-C` mostraron `0.000`. **No se interpreta como inestabilidad ni como inferioridad demostrada de
`OBS-A`** -- no existía un criterio pre-registrado para seleccionar observación por
`saturation_fraction`, P2 no penaliza potencia/saturación (§5), y la comparación proviene de una sola
seed con políticas no convergidas (presupuesto corto, `3000` steps).

`f_COI`/`RoCoF_COI` (usadas en `OBS-B`, y en `OBS-C` implícitamente vía los 10 canales
`Delta_f`/`RoCoF` por generador) quedan congeladas para toda P2 como la media **NO ponderada** sobre
los 10 `GEN_BUSES` -- ninguna COI ponderada por `H_i` está implementada (declarado explícitamente
desde `DEC-P2-019` en adelante, formalizado en `DEC-P2-031`).

**Ablation ejecutada (`P2-E6b`, ya completa, ver `DEC-P2-031`):**

- **OBS-A**: 6 señales locales -- **CONGELADA como observación principal**.
- **OBS-B**: 8 señales, POI + COI -- registrada como ablation, no configuración principal.
- **OBS-C**: observación global (`Delta_f`/`RoCoF` de los 10 generadores de métricas +
  `P_BESS1`/`P_BESS2`, 22 señales) -- registrada como ablation, no configuración principal.

No se reabre esta ablation ni se repite el entrenamiento para decidir observación (instrucción
explícita del usuario, `DEC-P2-032`).

---

## 10. Training distribution P2

P1 entrenaba solo pérdidas de generación. P2 usa diversidad explícita: por episodio, 50% generation
deficit / 50% load increase.

**Generation deficit**: generador únicamente de `G_train_P2`; `rho ~ U(0.30, 0.90)`; mecanismo
`Alter` ya validado en P1 (`TGOV1N.paux0`).

**Load increase**: carga únicamente de `L_train_P2`; `DeltaP_L = alpha_L * P_L0`,
`alpha_L ~ U(0.10, 0.50)`; escalar Q consistentemente (`DeltaQ_L = alpha_L * Q_L0`) para mantener
factor de potencia; mecanismo `Alter` ya validado en P1 (`PQ.Ppf`).

**Operating point**: training `lambda_L ~ U(0.90, 1.10)` siempre que power flow y TDS sean viables
(mayor diversidad que P1). Validation con valores discretos internos distintos de la mayoría de
samples. Test con operating points todavía no vistos. No usar el test final para reducir este rango.

---

## 11. Splits P2 (nuevos, no reutilizar T1–T8 como test)

No reutilizar directamente los escenarios T1–T8 de P1 como test. Mantener algunos generadores y
cargas completamente fuera de train. **Congelado en P2-E2** (`Paper_2/ops/sted/decision_log.md`
DEC-P2-003, distancia eléctrica Dijkstra desde `BESS_BUS_1=13`/`BESS_BUS_2=12`, mismo criterio que
P1 SS7.2/§7):

```text
G_train_P2      = GENROU_1, GENROU_2, GENROU_4, GENROU_5, GENROU_7, GENROU_8   (6)
G_validation_P2 = GENROU_6                                                     (bus 35, dist mediana)
G_test_P2       = GENROU_9 (bus 38, may. capacidad, may. distancia),
                  GENROU_3 (bus 32, min. distancia)                            (2)

L_train_P2      = PQ_2,3,4,6,7,8,9,11,12,13,14,15,17,18,19                     (15)
L_validation_P2 = PQ_10                                                        (bus 21, dist mediana)
L_test_P2       = PQ_1 (bus 3, may. potencia), PQ_16 (bus 28, may. distancia)  (2)
L_excluded_P2   = PQ_5                                        (bus 12 == BESS_BUS_2, co-localizada)

OP_train_range_P2  = U(0.90, 1.10)          (continuo)
OP_validation_P2   = {0.95, 1.00, 1.05}     (discreto, dentro del rango)
OP_test_outside_P2 = {0.88, 1.12}           (discreto, fuera del rango)
```

El test incluye generadores no vistos, cargas no vistas, y operating points fuera de
`OP_train_range_P2`. `L_A`/`L_B` de P1 (bus 20/29) caen deliberadamente en `L_train_P2`, no en
`L_test_P2`, para maximizar independencia del test de P2 (ver DEC-P2-003 para el detalle de la
coincidencia no deliberada en `G_validation_P2`).

---

## 12. Test final P2 — batería nueva y congelada (≥12 escenarios)

Propuesta inicial (verificar power flow/TDS/límites y congelar antes de usar; una vez congelados, no
acceder hasta finalizar training). "Gen no visto A/B" y "carga no vista A/B" quedaron mapeados a IDs
concretos en P2-E2 (`Paper_2/ops/sted/decision_log.md` DEC-P2-003):
`gen A = GENROU_9` (bus 38, mayor capacidad, más lejano al BESS), `gen B = GENROU_3` (bus 32, más
cercano al BESS), `carga A = PQ_1` (bus 3), `carga B = PQ_16` (bus 28).

| ID | Descripción |
|---|---|
| P2-T1 | GENROU_9 (gen A), rho=0.60, lambda=1.00 |
| P2-T2 | GENROU_3 (gen B), rho=0.60, lambda=1.00 |
| P2-T3 | GENROU_9 (gen A), rho=0.85, lambda=0.88 |
| P2-T4 | GENROU_3 (gen B), rho=0.85, lambda=1.12 |
| P2-T5 | PQ_1 (carga A), +30%, lambda=1.00 |
| P2-T6 | PQ_16 (carga B), +30%, lambda=1.00 |
| P2-T7 | PQ_1 (carga A), +50%, lambda=0.88 |
| P2-T8 | PQ_16 (carga B), +50%, lambda=1.12 |
| P2-T9 | déficit de generación (GENROU_9 o GENROU_3) + incremento de carga (PQ_1 o PQ_16), combinado |
| P2-T10 | déficit de generación + incremento de carga, combinado (segunda combinación, distinta de P2-T9) |
| P2-T11 | déficit de generación extremo pero factible (rho a definir en verificación de viabilidad) |
| P2-T12 | escalón de carga extremo pero factible (alpha_L a definir en verificación de viabilidad) |

Estos valores son propuesta inicial de partida — antes de usarlos, verificar viabilidad numérica
(incluye el mecanismo de perturbación combinada para P2-T9/T10, nunca probado en P1, ver riesgo en
§27) y congelarlos formalmente en `Paper_2/ops/sted/decision_log.md`. Los `rho`/`alpha_L` exactos de
P2-T9 a P2-T12 quedan pendientes de esa verificación, no de una nueva ronda de diseño.

---

## 13. Autoridad de potencia BESS — `alpha_P` design sweep (etapa P2-E6, **después** de `Tc`/`K_f`/`K_r`)

**Reordenado en esta revisión (ver §25):** este sweep ya NO ocurre antes de `Tc`/`K_f`/`K_r` — corre
como P2-E6, **después** de P2-E4 (`Tc`, §8) y P2-E5 (`K_f`/`K_r`, §14), usando el `Tc` ya seleccionado
y un controlador físico ya estabilizado. Motivo: los resultados de P2-E3 (diagnóstico previo,
DEC-P2-005) mostraron que estabilidad y desempeño dependen conjuntamente de `Tc`, `K_f`, `K_r` y
`P_max,BESS` — no es científicamente limpio elegir `P_max,BESS` con un `Tc` provisional y ganancias no
estabilizadas.

El objetivo no penaliza potencia, así que se hace un DESIGN sweep limitado, **antes** del
entrenamiento final, usando únicamente el controlador físico (sin RL):

```text
alpha_P = P_max,total / DeltaP_max_train   in {1.0, 1.5, 2.0}   (o al menos tres niveles de autoridad)
P_max,BESS = alpha_P * DeltaP_max_train / 2   (dos BESS idénticos)
```

**Regla obligatoria de aislamiento de variable (nueva en esta revisión):** al variar `P_max,BESS`,
mantener `K_f` y `K_r` **físicamente constantes** (mismos MW/Hz y MW/(Hz/s), no un múltiplo relativo
de `P_max,BESS`). El sweep original (pre-corrección, DEC-P2-004) escalaba `K_f`/`K_r`
proporcionalmente a `P_max,BESS` a la vez que escalaba `P_max,BESS` mismo, lo que hacía imposible
distinguir si un cambio de desempeño provenía de mayor autoridad física o de mayor ganancia de
realimentación. Con `K_f`/`K_r` fijos, para cada nivel de `P_max,BESS` medir: `fraction of time
saturated`, `frequency nadir`, `RoCoF max`, `Ppeak`, `delivered power`, `settling`.

Interpretación (obligatoria, no opcional):
- si aumentar `P_max,BESS` no cambia el desempeño y no hay saturación, la autoridad adicional no
  aporta — no está limitando el desempeño actual;
- si aumentar `P_max,BESS` mejora el desempeño porque el controlador anterior saturaba, existe un
  beneficio real de autoridad;
- si aumentar `P_max,BESS` empeora el desempeño sin que haya saturación, el problema no es la
  autoridad física sino la ley de control/dinámica (`K_f`/`K_r`/`Tc`/filtro), no `P_max,BESS`.

Congelar el `P_max,BESS` **mínimo** que capture prácticamente todo el beneficio físico observado (no
necesariamente el nivel de mejor desempeño puntual si un nivel menor ya captura el beneficio). No usar
costo económico como criterio. Verificar `Sn`, `pmax`/`pmin`, límites de corriente, SoC, y estabilidad
numérica a la escala mayor probada (riesgo técnico identificado — ver §29). No modificar `E_max` si
SoC sigue no vinculante.

**Headroom para el residual TD3 (§11 de la corrección de usuario, no renumerada como sección
independiente):** al congelar `P_max,BESS`, verificar que el controlador físico (`K_f*`/`K_r*` ya
congelados) no opere continuamente cerca de saturación en los escenarios DESIGN — si el físico usa
prácticamente toda la autoridad disponible, la política residual TD3 no dispondrá de espacio de
control útil. Registrar la fracción de tiempo saturado del controlador físico final junto con la
decisión de `P_max,BESS`.

---

## 14. Tuning del controlador físico (`K_f`, `K_r`) — segundo baseline obligatorio (etapa P2-E5, requiere `Tc` ya seleccionado en P2-E4)

`K_f` y `K_r` **deben ajustarse independientemente** — no como estrategia principal un único
`gain_mult` escalar aplicado a ambos simultáneamente (ese fue el atajo usado en el tanteo informal de
DEC-P2-005; útil como diagnóstico rápido, pero no sustituye una grilla `K_f`×`K_r` independiente).
Razón física: `K_f` (soporte de desviación de frecuencia/nadir) y `K_r` (respuesta asociada a
RoCoF/synthetic inertia) cumplen funciones distintas; la evidencia disponible hasta ahora muestra
mejora de nadir pero prácticamente ninguna mejora de RoCoF (DEC-P2-005: hasta +8.8% nadir, +0.0%
RoCoF en todo el rango de ganancia estable probado a `Tc=100ms`), y solo una grilla independiente
puede distinguir si `K_r` es demasiado pequeño, demasiado grande, si el RoCoF llega demasiado tarde,
si el filtro elimina la ventaja temporal, o si la dinámica `ESD1` (§7-bis) es demasiado lenta para el
`Tc` elegido.

### 14.0 Diagnóstico obligatorio previo: F-only / R-only / F+R

Antes de la grilla completa, construir tres controladores de diagnóstico y compararlos en los mismos
escenarios DESIGN:

```text
F-only:  K_r = 0
R-only:  K_f = 0
F+R:     ambos activos
```

Este experimento es obligatorio antes del tuning completo — aísla qué término (frecuencia, RoCoF, o
la interacción de ambos) produce el comportamiento observado.

### 14.1 Grilla `K_f`/`K_r` independiente

```text
K_f0 = P_max,BESS / 0.5 Hz
K_r0 = P_max,BESS / 1.0 Hz/s

K_f/K_f0 in {0.25, 0.50, 0.75, 1.00}
K_r/K_r0 in {0.00, 0.25, 0.50, 0.75, 1.00}      (20 combinaciones)

J_phys = max(df_norm, rocof_norm) + 0.25*(df_norm + rocof_norm)   (sin energía)
```

Grilla **conservadora** (no la `{0.5,1.0,2.0}` original, que DEC-P2-005 mostró desestabilizante cerca
de `1.0x` en varios escenarios). No incluir multiplicadores mayores que `1.0` salvo evidencia de que
el borde superior probado sigue siendo estable. Para cada combinación evaluar: `frequency nadir`,
`RoCoF max`, `settling time`, `saturation fraction`, `Ppeak`, `TDS success`. `Ppeak` no se usa para
elegir el ganador principal, solo como diagnóstico de saturación/comportamiento patológico.

Eliminar automáticamente del conjunto elegible cualquier combinación con: `TDS failure`, oscilación
sostenida, saturación patológica, o deterioro de frecuencia respecto a No-FFC. Entre las combinaciones
elegibles, seleccionar por el criterio de desempeño simultáneo de nadir y RoCoF definido para P2 (§21).

Seleccionar un único `K_f*`, `K_r*` y congelarlo. **Este controlador físico es también un baseline
obligatorio de comparación** ("Physical Hybrid-only", §15) — no permitir que TD3 sea el único
controlador comparado contra droop.

### 14.2 Punto de control obligatorio antes de invertir en TD3 (prioridad explícita del usuario)

**Movido en esta revisión:** este checkpoint ahora ocurre **después** de P2-E6 (autoridad de potencia,
§13), no inmediatamente después de P2-E5 — necesita `P_max,BESS` ya congelado, no solo `K_f*`/`K_r*`,
porque el margen físico depende conjuntamente de los tres (ver §25 para el orden completo y §20 para
la redefinición de `STOP-P2-A` como design target multicriterio en vez de un umbral rígido).

Antes de gastar horas de cómputo entrenando TD3, P2-E4+P2-E5+P2-E6 (`Tc` + tuning físico + autoridad
de potencia) se ejecutan como una secuencia de diseño barata y rápida que culmina en el gate
`STOP-P2-A`:

- Si el controlador **Physical Hybrid-only** (con `Tc`, `K_f*`/`K_r*` y `P_max,BESS` ya congelados),
  evaluado sobre los escenarios DESIGN, **no** logra una mejora simultánea reproducible de nadir y
  RoCoF frente al droop, el cuello de botella probablemente está en la dinámica/modelado del sistema
  (autoridad de potencia, ubicación de BESS, `Tc`, dinámica `ESD1`, filtro RoCoF), no en el algoritmo
  de RL — **no tiene sentido pedirle a TD3 que resuelva ese déficit**. En ese caso: no entrenar TD3
  todavía; identificar cuál causa domina (§20) y escalar la decisión al usuario.
- Si el controlador físico demuestra un margen simultáneo material y reproducible, ese margen se
  documenta como el objetivo cuantitativo que TD3 debe explotar y, si es posible, mejorar — entonces
  se procede a P2-E7 (ablation de observación) y P2-E10 (entrenamiento TD3).

Esto se registra como una etapa formal del orden de ejecución (§25) y como una condición de stop
(§20, `STOP-P2-A`).

**CIERRE (`DEC-P2-023/024/025`, esta ronda):** este checkpoint se ejecutó formalmente para
`Physical F+R` (con `K_f*`/`K_r*` retuneados bajo `Tc=tstep=5ms`/buses `16,20`/`Pmax=293.4MW` ya
congelados) y el resultado es **`STOP-P2-A = FAIL DEFINITIVO`** — `F+R` no logra una mejora
simultánea reproducible de nadir y RoCoF frente al droop tuned (`Kd*=4694.4MW/Hz`) en ninguna de 13
combinaciones estables evaluadas. Por instrucción explícita del usuario, **no se reabre este
checkpoint para `F+R`** — el resultado queda cerrado y `F+R` pasa a ser ablation/baseline únicamente
(§4.revised, §15, §16). El checkpoint equivalente para la arquitectura revisada (`droop* + TD3`)
tiene un significado distinto, no idéntico a este — ver §20 para la propuesta de redefinición,
pendiente de confirmación del usuario.

---

## 15. Controladores a comparar en P2 — REVISADO (`DEC-P2-026`)

Como mínimo:

1. No FFC
2. Droop retuneado para P2 (`Kd*=4694.4MW/Hz`, `DEC-P2-024`) — **ahora también la componente física
   de la arquitectura principal** (§4.revised)
3. Physical `F+R` (`K_f*`/`K_r*`, §14) — **ablation/baseline únicamente, DESCARTADO como arquitectura
   principal** (`STOP-P2-A = FAIL DEFINITIVO`, `DEC-P2-025`); se conserva porque ya está ejecutado y
   documentado, no porque siga siendo candidato
4. DDPG-P1, solo como referencia histórica, si la compatibilidad de escenarios lo permite (misma
   red/BESS; ejecutarlo sobre P2-T1..T12 es válido como referencia, no como parte del gate de P2)
5. **TD3 residual sobre droop** (arquitectura principal revisada, §4.revised) —
   `P_total = P_droop(Kd*) + P_RL`

Opcionalmente: 6. pure TD3 sin componente física (ablation A2, §16) — permite separar el efecto del
algoritmo del efecto del conocimiento físico. 7. TD3 residual sobre `F+R` (arquitectura ORIGINAL,
`P_total = P_ff(Kf*,Kr*) + P_RL`) — ablation opcional únicamente, no obligatoria para el gate
principal; interesante solo como comparación científica (¿ayuda TD3 más a una base ya inferior?), no
como candidato a arquitectura de producción.

---

## 16. Ablations científicas — REVISADO (`DEC-P2-026`)

Renumeradas en esta revisión para reflejar el diagnóstico F-only/R-only/F+R obligatorio de §14.0 y el
reencuadre de arquitectura de `DEC-P2-026`:

- **A1**: Droop vs. `F-only` (`K_r=0`) — ya ejecutado (`P2-E5`/`DEC-P2-011` a `017`).
- **A2**: `F-only` vs. `F+R` (aísla el aporte del término RoCoF) — ya ejecutado.
- **A3 (REVISADA, es ahora la comparación central del gate)**: droop tuned (`Kd*`) vs. droop + TD3
  residual — arquitectura principal revisada (§4.revised). Requiere entrenamiento TD3 (no ejecutado
  todavía).
- **A3-original (ablation científica, YA NO es la comparación central)**: Physical `F+R` vs. Physical
  `F+R` + TD3 residual — se conserva como curiosidad científica opcional (¿el residual TD3 ayuda más
  a una base ya inferior que a una base competitiva?), no forma parte del gate principal de P2.
- **A4**: `Tc=100ms` vs. `Tc` elegido — nota: la evidencia disponible ya usa `Tc=tstep=5ms` como
  candidato (`DEC-P2-020`); esta ablation formal sigue pendiente si se requiere para el paper.
- **A5**: local observation vs. local+COI (si se ejecuta OBS-A vs. OBS-B) — solo si esta comparación
  sigue siendo relevante.
- **A8 (nueva, `DEC-P2-026`)**: droop + TD3 residual (arquitectura revisada) vs. `F+R` + TD3 residual
  (arquitectura original, A3-original) — si ambas llegan a entrenarse, compara directamente si partir
  de una base física inferior (`F+R`) pero con un término RoCoF explícito en la observación/estructura
  puede compensarse por RL tan bien como partir de una base física superior (`droop`) sin ese término
  explícito. Opcional, no obligatoria para el gate principal.

Opcional (no obligatoria para el gate de P2):
- **A6** (antes A2): Pure TD3 vs. droop + TD3 residual — separa el efecto del algoritmo del efecto
  del conocimiento físico (droop).
- **A7** (antes A5): generation-only training vs. mixed disturbance training — **solo si se
  preregistra antes del test final**.

---

## 17. TD3 (stable-baselines3)

```text
actor:              [256, 256]
critic:              [256, 256] x twin critic (TD3)
learning_rate:       1e-4
gamma:               0.99
tau:                 0.005
batch_size:          256
buffer_size:         1_000_000
learning_starts:     >= 1000 transitions
train_freq:          1
gradient_steps:      1
policy_delay:        default validado de SB3
target_policy_noise: default validado de SB3
target_noise_clip:   default validado de SB3
action space:        [-1,1]^2 (residual)
```

No realizar HPO masivo. Antes del training final, solo smoke/preflight. Si algún hiperparámetro se
cambia, debe ser por fallo de implementación, no por observar el test final (mismo principio que
STOP-C de P1).

---

## 18. Seeds — CONGELADO (`P2-E7`, `DEC-P2-033`)

**`FINAL_SEEDS = {11, 22, 33, 44, 55}`** (5 seeds, congelado). No reducir posteriormente el número por
resultados desfavorables (instrucción explícita del usuario). Selección de checkpoint exclusivamente
por `J_val_P2`.

---

## 19. Early stopping y duración de episodio

Evaluación cada 200 episodios (o equivalente en steps si `Tc` cambia el número de transiciones por
episodio). Early stopping no antes de 2000 episodios; patience de 5 evaluaciones consecutivas sin
mejorar. **No copiar ciegamente el presupuesto de episodios de P1**: si `Tc=20 ms`,
`N_steps = 6/0.02 = 300` acciones por episodio (~5x las 60 de P1 a 100 ms) — recalcular replay
buffer, `learning_starts`, y costo computacional en consecuencia (riesgo de costo, ver §29/§30).

Episodio: mantener inicialmente `tf=6 s`, `td=1 s`, pero verificar que la recuperación del
controlador híbrido ocurre antes del final; no reducir `tf` para mejorar artificialmente métricas;
extender únicamente si el nadir o la recuperación están truncados.

---

## 20. Reglas de stop P2

### STOP-P2-A (prioridad explícita del usuario, §14.2 — redefinido en esta revisión)

**Redefinición (esta revisión):** ya no se usa un umbral rígido de 20–40% de mejora como condición de
paso/fallo binaria. Ese rango pasa a ser un **design target orientativo**, no un requisito duro. El
gate exige en cambio, todo simultáneamente, evaluado con `Tc`, `K_f*`/`K_r*` y `P_max,BESS` ya
congelados (P2-E4/E5/E6):

1. mejora simultánea **reproducible** de nadir y RoCoF frente al droop tuneado (no un resultado
   puntual de un solo escenario);
2. estabilidad numérica (sin `TDS failure`, sin oscilación sostenida);
3. ausencia de saturación patológica del controlador físico;
4. consistencia del margen a través de varios escenarios DESIGN/VALIDATION, no solo uno.

Si el controlador **Physical Hybrid-only** no cumple estas cuatro condiciones simultáneamente:

> detener antes de entrenar TD3 y escalar la decisión al usuario. **No entrenar TD3 "a ver si
> mejora" sin ese margen físico demostrado.**

En ese caso, identificar cuál de estas causas domina antes de proponer una salida (no asumir la causa
sin evidencia — usar §7-bis/§8/§14 para diagnosticar cada una):

```text
actuator bandwidth (dinámica ESD1, tip -- §7-bis)
RoCoF estimator (filtro BusROCOF, Tf/Tw/Tr -- §8)
Tc (tiempo de control -- §8)
Kf/Kr structure (estructura de ganancias -- §14)
Pmax saturation (autoridad de potencia -- §13)
BESS location (ubicación, congelada en P2-E1/DEC-P2-002)
model limitations (límites del modelo ESD1/PVD1 en sí)
```

Solo después de identificar la causa dominante se decide con el usuario si continuar (revisando la
causa) o reencuadrar el alcance del estudio. El gate confirmatorio final `P2-H1` (§21) se mantiene
separado y no se relaja por haber pasado `STOP-P2-A` — `STOP-P2-A` es un gate de diseño barato que
autoriza invertir en TD3, no una promesa de que el test final pasará.

### STOP-P2-A — CERRADO para `F+R` (`DEC-P2-025`) y significado revisado, CONFIRMADO por el usuario
### (`DEC-P2-026` propuesta → `DEC-P2-027` confirmación: `STOP-P2-A_REVISED = PASS`)

**Estado del `STOP-P2-A` original:** evaluado formalmente contra `Physical F+R` con `Tc`, `K_f*`/
`K_r*` y `Pmax` congelados → **FAIL DEFINITIVO** (`DEC-P2-025`). Este resultado queda **cerrado y no
se reabre** para `F+R` — no se vuelve a retunear `K_f`/`K_r` buscando un veredicto distinto (punto 12
de la autorización del usuario en `DEC-P2-026`).

**Por qué el `STOP-P2-A` original no puede repetirse literalmente para la arquitectura revisada:**
bajo `P_total = P_droop(Kd*) + P_RL` (§4.revised), el "componente físico" de la arquitectura ES el
droop tuned — preguntar "¿el componente físico supera al droop tuned?" es ahora una tautología
(droop vs. sí mismo), no una pregunta empírica. El checkpoint necesita una redefinición para seguir
siendo útil como gate de pre-entrenamiento.

**Redefinición CONFIRMADA por el usuario (`DEC-P2-027`) — cuatro criterios, todos evaluados con
evidencia ya existente, sin nuevas simulaciones:**

```text
A. Baseline fisico correctamente optimizado y congelado.
   PASS -- droop* Kd=4694.4MW/Hz (DEC-P2-024).
B. Baseline estable y reproducible en DESIGN.
   PASS -- STABLE en gen_severe y load_severe, antes de la region LIMIT_CYCLE (Kd>=12x, DEC-P2-024).
C. Existe autoridad residual disponible para que TD3 module la accion del droop.
   PASS PROVISIONAL -- saturation_fraction de droop* practicamente nula en ambos probes DESIGN
   (0.000 gen_severe, 0.004 load_severe), el actuador no opera permanentemente en Pmax. Marcado
   explicitamente como PROVISIONAL -- no es un analisis de headroom formal y dedicado.
D. No existe patologia fisica conocida que inutilice el residual.
   PASS -- ripple de tension descartado como oscilacion sostenida (DEC-P2-023, decaimiento
   verificado a horizonte extendido); actuador y timing ya validados (DEC-P2-007/008/019/020).

STOP_P2_A_REVISED = PASS
TD3_DESIGN_PIPELINE_AUTHORIZED = TRUE
```

**Alcance explícito (aclarado por el usuario):** este `PASS` es una declaración de **justificación
física suficiente para invertir en probar** si un residual aprendido aporta mejora adicional sobre
`droop*` — **no** predice ni garantiza que TD3 vaya a superar al droop en el test final. El gate
confirmatorio real sigue siendo `P2-H1`/§21, sin relajarse por este `PASS`. **Tampoco autoriza
automáticamente ninguna etapa de ejecución concreta** (`P2-E7`, freeze, preflight, entrenamiento) —
cada una requiere su propia autorización explícita separada, igual que el resto de la campaña.

### STOP-P2-B (equivalente a STOP-C de P1)

Si TD3 falla en todas las seeds: se permite una única ronda de diagnóstico, limitada a error de
normalización, error de signo, error de reward, error de acción/setpoint, bug de reset, o bug
numérico. No hacer hyperparameter optimization exploratoria.

### STOP-P2-C (equivalente a STOP-D de P1)

Si TD3 no cumple el gate de §21 en test: conservar el resultado negativo. No crear escenarios
adicionales favorables, no reentrenar, no ajustar reward/observación/`Tc`/gate después del primer
acceso a P2-T1..T12.

### Prohibiciones explícitas (todas las etapas)

No modificar P1 para que parezca exitoso; no reescribir T1–T8 de P1; no usar T1–T8 como test ciego
P2; no seleccionar P2-T1..T12 después de ver resultados; no entrenar con el test P2; no cambiar
reward, buses, BESS sizing, `Tc`, o hiperparámetros TD3 después del test final; no añadir escenarios
favorables después de ver fallos; no eliminar seeds "malas"; no elegir únicamente la mejor seed para
claims agregados.

---

## 21. Gate científico P2

```text
I_f = (|df_droop| - |df_P2|) / |df_droop|
I_r = (RoCoF_droop - RoCoF_P2) / RoCoF_droop

WIN(escenario)  <=>  I_f >= 0.10  Y  I_r >= 0.10

Gate principal:   >= 10/12 escenarios WIN
Además:           median(I_f) >= 0.15  Y  median(I_r) >= 0.15

Criterio seed-level: al menos 3/5 seeds (o 2/3 si se mantienen 3 seeds) deben satisfacer
                     I_f >= 0.10 Y I_r >= 0.10 en al menos 8/12 escenarios.
```

Si se cumplen valores más altos, reportarlos, pero no relajar el gate posteriormente una vez
congelado (mismo principio que P1 SS22-SS24).

---

## 22. Métricas obligatorias

Registrar por escenario: `f_nadir`, `|Delta_f_nadir|`, `RoCoF_max`, `time_to_nadir`,
`settling_time`, `P_BESS1_peak`, `P_BESS2_peak`, `P_total_peak`, `E_BESS`, `saturation_fraction`,
excursión de SoC, `TDS_success`. Solo `|Delta_f_nadir|` y `RoCoF_max` se usan para el claim
principal (§21); el resto es auditoría, no criterio de selección (§5).

---

## 23. Preflight P2 (26 checks, ninguno puede omitirse)

**Ampliado en esta revisión** con 10 checks nuevos de actuador/dinámica (`PF2-ACT-*`, `PF2-DYN-*`),
que se ejecutan como parte de P2-E3A/P2-E3B (§7-bis) y deben pasar antes de continuar a P2-E4:

```text
PF2-ACT-01  MW command conversion correct (Pext0_pu = command_MW/100.0, Sb=100MVA -- §0-bis)
PF2-ACT-02  pmx scaling correct (pmx_pu = Pmax_BESS_MW/100.0, no hardcode = 1.0)
PF2-ACT-03  commanded vs delivered power calibration pass (P2-E3A, p2_actuator_calibration.csv)
PF2-ACT-04  positive and negative power verified (ambos signos, ambos BESS)
PF2-ACT-05  saturation occurs at intended physical limit (ni antes ni después de Pmax,BESS)
PF2-ACT-06  power readout uses system base (P_delivered_MW = Ipout_y*v*100.0, nunca *Sn)
PF2-DYN-01  command-to-power response characterized (P2-E3B, delay/rise/settling/overshoot)
PF2-DYN-02  Tc timing verified (número exacto de actualizaciones, sin duplicar/perder pasos)
PF2-DYN-03  RoCoF sampling consistent across Tc (prueba de consistencia de §8)
PF2-DYN-04  no hidden dependence on TDS.plt (patrón itm_step()+lectura en vivo, DEC-P2-002)
```

Preflight original (16 checks, sin cambios de contenido, renumerados con prefijo explícito para
evitar colisión con los nuevos):

```text
PF2-01  reloj correcto y número exacto de decisiones
PF2-02  reset limpio
PF2-03  sampling de disturbance correcto
PF2-04  observation exacta
PF2-05  action residual exacta
PF2-06  P_total = P_droop + P_RL (arquitectura revisada, DEC-P2-026), verificada numéricamente
PF2-07  saturación física correcta
PF2-08  reward recomputada exactamente
PF2-09  terminal reward correcta
PF2-10  TD3 model.learn funcional
PF2-11  twin critics sin NaN/Inf
PF2-12  validation no entra al replay buffer
PF2-13  checkpoint logic correcta
PF2-14  deterministic=True en validation/test
PF2-15  ningún test P2 accesible desde training code
PF2-16  hash/config frozen
```

No autorizar TD3 training si alguno de los 26 falla. `PF2-ACT-*`/`PF2-DYN-*` se verifican en P2-E3A/
P2-E3B (diseño temprano); `PF2-01..16` se verifican en la etapa de preflight formal (ahora P2-E9, ver
§25), mismo estándar que P1-E5 (`Paper_1/artifacts/preflight/p1_e5_preflight.json`).

---

## 24. Figuras P2

- **Fig P2-1**: dinámica representativa (No FFC / Droop / Physical / TD3 Hybrid) — envelope
  frecuencia, envelope RoCoF, potencia BESS.
- **Fig P2-2**: `I_f` por P2-T1..T12.
- **Fig P2-3**: `I_r` por P2-T1..T12.
- **Fig P2-4**: scatter `I_f` vs `I_r`, cuadrante superior derecho = mejoras simultáneas.
- **Fig P2-5**: `J_val` de validation vs. training steps/seeds.
- **Fig P2-6**: ablation de arquitectura de controlador.
- **Fig P2-7**: desempeño vs. `Tc`.
- **Fig P2-8**: desempeño vs. autoridad de potencia BESS.

No esconder resultados negativos.

---

## 25. Orden de ejecución P2

**Reordenado en esta revisión.** Cambios respecto al orden original: (1) se insertan P2-E3A/P2-E3B
(actuator calibration + dynamic response) antes de todo diseño de `Tc`/ganancias/autoridad; (2) el
sweep de autoridad de potencia (`alpha_P`, antes P2-E3) se mueve a P2-E6, **después** de `Tc` (P2-E4)
y del tuning `K_f`/`K_r` (P2-E5); (3) `STOP-P2-A` se mueve a después de P2-E6, no entre P2-E5 y la
ablation de observación; (4) todas las etapas posteriores se renumeran en consecuencia (antiguo
P2-E6→P2-E7, P2-E7→P2-E8, ..., P2-E13→P2-E14).

```text
P2-E0    Crear estructura, gobernanza y plan.                          [COMPLETA]
P2-E1    Reusar/verificar caso low-inertia congelado físicamente, sin modificar P1.  [COMPLETA]
P2-E2    Definir nuevos splits train/validation/test.                  [COMPLETA]
P2-E3A   BESS actuator calibration gate (§7-bis).                      [ESTA RONDA]
P2-E3B   BESS dynamic response characterization (§7-bis).              [ESTA RONDA]
         --- REPORTE AL USUARIO Y ESPERA DE APROBACIÓN (§ orden de ejecución inmediato) ---
P2-E4    Diseño de Tc: 100/50/20 ms (§8, requiere P2-E3A/E3B PASS).
P2-E5    Tuning físico K_f/K_r independiente, con diagnóstico F-only/R-only/F+R previo (§14).
P2-E6    Sweep de autoridad BESS: alpha_P >= 3 niveles, Kf/Kr físicamente constantes (§13).
         --- STOP-P2-A: checkpoint de margen físico, multicriterio (§14.2/§20) ---
P2-E7    Ablation limitada de observación.
P2-E8    Congelar: Pmax, Tc, K_f, K_r, observación, reward, training distribution,
         validation, final test, hiperparámetros TD3, seeds.
         [SUPERADO -- ver FREEZE FINAL abajo (`P2-E7` de esta ronda, `DEC-P2-033`), que ya cubre todo
         el contenido de este bookkeeping. `P2-E8` formal (renombrar/consolidar en el paper) se reduce
         a confirmar que nada de lo listado abajo cambió antes de correr preflight.]
P2-E9    Preflight 26/26 (16 originales + 10 PF2-ACT-*/PF2-DYN-*, §23).
```

### FREEZE FINAL pre-preflight (`P2-E7` de esta ronda, `DEC-P2-033` -- congelado, no confundir con
### el `P2-E7` "ablation de observación" de la lista original de arriba, ya absorbido en `P2-E6b`)

```text
arquitectura:      droop* + TD3 residual (P_total = clip(P_droop + P_RL, -Pmax, +Pmax))
BESS buses:        16, 20
Kd*:                4694.4 MW/Hz               (DEC-P2-024)
Pmax:               293.4 MW/BESS
P_RL,max:           73.35 MW/BESS  (0.25*Pmax)  FROZEN FINAL, sin sweep (DEC-P2-033)
Tc:                 5 ms
tstep:              5 ms
observation:        OBS-A, 6 senales locales     (DEC-P2-032)
normalization:      df/0.5Hz, RoCoF/1.0Hz/s, P_BESS/293.4MW
seeds:              {11, 22, 33, 44, 55}          FROZEN FINAL (DEC-P2-033, SS18)
reward:             definicion vigente SS6 de Paper_2
train/val/test:     splits ya congelados (DEC-P2-003)
```

**NOTA (esta ronda, tras el reencuadre de arquitectura -- `DEC-P2-026` en adelante): la secuencia
efectivamente ejecutada diverge de la lista de arriba** (que documenta el orden ORIGINAL, previo al
`STOP-P2-A=FAIL DEFINITIVO` de `F+R`). Lo realmente ejecutado, en orden: `P2-E4`(`Tc`) →
`P2-E5`(`Kf`/`Kr` diagnóstico) → `P2-E6`(reubicación BESS) → `STOP-P2-A` original (FAIL para `F+R`,
`DEC-P2-025`) → reencuadre de arquitectura (`DEC-P2-026`) → `P2-E5bis`(retuning droop, `DEC-P2-024`)
→ `P2-E5ter`(retuning final `F+R` vs. droop, cierre `STOP-P2-A`, `DEC-P2-025`) →
`STOP-P2-A_REVISED`(`DEC-P2-027`, PASS) → `P2-E6a`(arquitectura `droop*+TD3`, smoke tests,
`DEC-P2-028`) → `P2-E6b`(ablation de observación, `OBS-A` congelada, `DEC-P2-031/032`). **Próximo
paso pendiente: `P2-E8`** (freeze bookkeeping), con la lista de parámetros a congelar ACTUALIZADA
respecto al texto original de abajo (ya no `K_f`/`K_r` como componente física principal, sino
`Kd*`+`P_RL,max`; observación ya es `OBS-A`, no pendiente):
```text
P2-E10   Training TD3.
P2-E11   Freeze checkpoints.
P2-E12   Single-shot final test (P2-T1..T12).
P2-E13   Evaluar gates.
P2-E14   Figuras/tablas/paper.
```

**Orden de ejecución inmediato de esta ronda (instrucción explícita del usuario):** tras actualizar
este plan, ejecutar únicamente P2-E3A y P2-E3B, reportar los resultados al usuario, y **detenerse
ahí**. No iniciar el sweep de `Tc` (P2-E4) hasta que el usuario revise: la calibración del actuador,
la velocidad de respuesta efectiva de `ESD1`, una posible limitación de ancho de banda, y este plan
revisado.

**Autorización requerida:** el usuario debe aprobar explícitamente antes de iniciar P2-E4 o
cualquier entrenamiento (misma disciplina de "esperar confirmación en cada etapa" que rigió toda la
campaña P1). No entrenar TD3; no ejecutar P2-T1 a P2-T12; no cambiar splits, buses BESS, low-inertia
case o reward TD3; no hacer HPO; no modificar simultáneamente `Tc`, filtro RoCoF, `Pmax` y `K_f`/`K_r`;
no congelar `Pmax` basándose en los sweeps ya realizados (el `p2e3_alpha_p_sweep.csv` pre-corrección
sigue `INVALID`, §0-bis); no borrar resultados negativos o inválidos.

---

## 26. Lecciones heredadas de P1 (obligatorio reutilizar, no redescubrir)

P1 encontró y corrigió cinco bugs de implementación no triviales que **deben** reutilizarse
idénticos en el código de P2, no redescubrirse:

1. **`andes.io.dump()` serializa `M.vin`, no `M.v`** — al escalar inercia hay que escalar ambos
   (`Paper_1/ops/sted/decision_log.md` DEC-P1-005).
2. **`Bus.v0` (parámetro estático) vs `Bus.v.v` (solución real de PFlow)** — el `v0` de un nuevo
   dispositivo `PV`/`ESD1` debe tomarse de `Bus.v.v` tras resolver `PFlow`, nunca de `Bus.v0`, o
   `PFlow` demanda cientos de MVAr (DEC-P1-006/`add_bess_pair`).
3. **`TDS.run()` no soporta llamadas incrementales de forma confiable** — usar `TDS.itm_step()`
   manualmente con `do_switch()`/`calc_h()`/`dae.t += h`, replicado en cada `step()` del entorno
   Gymnasium (DEC-P1-007). Este es el mecanismo que P2-E4 debe validar a `Tc` más rápido.
4. **`Pext0`/`DG.set_paux()` escribe en pu de la base propia del dispositivo (`Sn`), no en base de
   sistema** — dividir siempre por `P_max,BESS` del actuador, nunca por una constante fija
   (bug crítico de P1, DEC-P1-016, causó ~2.9x sobre-entrega de potencia durante gran parte de la
   sesión hasta ser detectado). **Verificar este patrón explícitamente en PF2-06.**
5. **Sobre-suscripción de hilos de `torch` en entrenamiento paralelo** — fijar
   `OMP_NUM_THREADS`/`MKL_NUM_THREADS`/`NUMEXPR_NUM_THREADS`/`OPENBLAS_NUM_THREADS=2` y
   `torch.set_num_threads(2)` por proceso antes de lanzar seeds en paralelo (DEC-P1-017).

### Funciones de `Paper_1/src/run_ffc_study.py` reutilizables sin modificación (como referencia de
### implementación; P2 debe tener su propia copia en `Paper_2/src/`, no importar desde `Paper_1/`)

- `build_case()`, `h_report()`, `_find_ordered()`, `worst_bus_freq_rocof()` — utilidades genéricas.
- `add_bess_pair()` — instalador de par ESD1 con el fix de `Bus.v0`/`Bus.v.v` ya incorporado.
- `natural_bus_voltages()` / `natural_bus_voltages_at_lambda()` — utilidades genéricas.
- El patrón de bucle de control con `itm_step()` de `run_test_scenario()`/`FFCEnv.step()` — la
  estructura del bucle es reutilizable; el contenido (reward, observación, composición
  física+residual de la acción, `Tc`) es específico de P2 y debe reescribirse.

### Funciones que NO se reutilizan, deben reescribirse para P2

`compute_reward` (P1-specific), `FFCEnv` (Tc=100ms fijo, 6-dim obs, sin componente física),
`make_ddpg_model`/`train_seed` (DDPG, no TD3), `TEST_SCENARIOS`/`STRATEGIES`/`run_test_scenario`
(T1-T8 específicos de P1), `evaluate_validation` (`J_val` con término de energía), `dimension_bess`/
`tune_droop` (sizing y droop de P1, reemplazados por §13/§14 de este plan).

---

## 27. Riesgos técnicos identificados (§29.5)

| Riesgo | Descripción | Mitigación propuesta |
|---|---|---|
| **BESS a `alpha_P=2.0`** | Hasta 580 MW por unidad (1160 MW total) sobre un sistema de prueba IEEE-39; riesgo de infactibilidad de PFlow, límites de corriente de `ESD1` (`Ipmax`), o inestabilidad numérica a esa escala. | Verificar explícitamente `Sn`, `pmax`/`pmin`, límites de corriente y convergencia de PFlow en P2-E3 antes de congelar `alpha_P`; si `2.0` es infactible, documentar y usar `1.5`. |
| **`Tc=20 ms` vs. filtro RoCoF** | `Tf=Tw=0.02s`, `Tr=0.05s` quedan en el mismo orden de magnitud que `Tc=20ms` — riesgo de que el control muestree más rápido que la dinámica del estimador, o de aliasing. | Prueba de consistencia obligatoria en P2-E4 (§8): comparar RoCoF medido entre `Tc` sin cambiar el filtro; documentar explícitamente si el control queda más rápido que el estimador. |
| **Mecanismo de perturbación combinada (P2-T9/T10)** | P1 solo validó `Alter` sobre `TGOV1N.paux0` (gen) y `PQ.Ppf` (carga) por separado; activar dos `Alter` simultáneos en el mismo episodio es nuevo. | Validar en DESIGN (P2-E1/E2) antes de usarlo en el test final; confirmar que no hay colisión de orden/tiempo entre los dos dispositivos `Alter`. |
| **Costo computacional de `Tc=20ms`** | ~5x más transiciones por episodio que P1 (300 vs 60 pasos) — el presupuesto de episodios/tiempo de pared de P1 no es directamente transferible. | Recalcular `learning_starts`/buffer/episodios en P2-E8 (freeze) antes de congelar; ver benchmark de cómputo obligatorio (equivalente a P1-E4.5) antes de P2-E10 (training). |
| **`DDPG-P1` como referencia** | El checkpoint DDPG de P1 fue entrenado con `Tc=100ms` y 6-dim obs; si P2 cambia `Tc`/observación, el modelo no es directamente ejecutable sobre el entorno P2 sin adaptar el wrapper de observación/acción. | Usar el entorno de P1 (`Paper_1/src/run_ffc_study.py`, sin modificar) para ejecutar DDPG-P1 sobre los escenarios P2-T1..T12 traducidos a la parametrización de P1, no forzarlo dentro del entorno P2. |
| **TD3 en `stable-baselines3`** | Ya instalado (mismo paquete que DDPG de P1); riesgo bajo. | Ninguna mitigación especial requerida; validar en preflight (PF2-10/11). |
| **COI (`f_COI`/`RoCoF_COI`)** | Requiere pesos `H_i` consistentes con la inercia ya escalada (`GENROU.M.v`, base de sistema — mismo patrón que el test T17 de P1); riesgo bajo si se reutiliza ese patrón. | Definir `RoCoF_COI` una sola vez en P2-E1/E6 (derivada filtrada vs. combinación ponderada) y no cambiarlo después. |

---

## 28. Estimación de duración por etapa (orden de magnitud, no comprometida)

Basado en los tiempos reales observados en P1 (build+P1-E1..E5 ≈ 1 sesión intensiva;
entrenamiento DDPG 3 seeds en paralelo ≈ 3h43min pared; test T1-T8, 40 celdas, minutos):

| Etapa | Estimación | Nota |
|---|---|---|
| P2-E0 | ~1 sesión | Estructura + plan (completa). |
| P2-E1 | 15–30 min | Reusar caso low-inertia (completa, DEC-P2-002). |
| P2-E2 | 30–45 min | Definir y congelar splits (completa, DEC-P2-003). |
| P2-E3A | 10–20 min cómputo + análisis | Actuator calibration gate, sin RL, sin `Alter` (esta ronda). |
| P2-E3B | 10–20 min cómputo + análisis | Dynamic response characterization, sin RL, sin `Alter` (esta ronda). |
| P2-E4 | 45–90 min | Validación de `Tc`, más delicada por el riesgo de filtro (§27); requiere P2-E3A/E3B PASS. |
| P2-E5 | 45–75 min | Diagnóstico F-only/R-only/F+R + grilla 20 combinaciones `K_f`/`K_r`, sin RL. |
| P2-E6 | 30–60 min cómputo + análisis | Sweep `alpha_P` >= 3 niveles, `K_f`/`K_r` fijos, sin RL. |
| **Checkpoint STOP-P2-A** | — | Decisión del usuario si el margen físico multicriterio (§20) es insuficiente. |
| P2-E7 | 30–60 min | Ablation de observación (OBS-A/B/C), sin test final. |
| P2-E8 | trivial | Bookkeeping de congelamiento. |
| P2-E9 | 45–90 min | Preflight 26/26 (16 originales + 10 `PF2-ACT-*`/`PF2-DYN-*`, §23). |
| P2-E10 | **mayor incertidumbre** | Si `Tc=20ms` se congela, ~5x más transiciones/episodio que P1 → posible escalamiento significativo del tiempo de pared por seed; requiere el benchmark de cómputo de P2-E8/E9 antes de comprometer una cifra. Con 5 seeds en paralelo (vs. 3 en P1) también compite más por CPU. |
| P2-E11 | trivial | |
| P2-E12 | 30–60 min | Hasta ~12 escenarios x ~7-9 controladores/seeds — más celdas que P1 (40) pero cada una es rápida. |
| P2-E13 | trivial | Script de gates. |
| P2-E14 | ~1 sesión | Más figuras que P1-E7 (8 vs 2) y ablations adicionales. |

La mayor incertidumbre real sigue siendo **P2-E10** (entrenamiento TD3), condicionada al resultado de
`Tc` en P2-E4 — se reportará una estimación concreta recién en el benchmark de cómputo de P2-E8/E9, no
antes (mismo principio de no fabricar cifras que rigió P1-E4.5).

---

## 29. Reproducibilidad y trazabilidad

- Todas las decisiones de congelamiento se registran en `Paper_2/ops/sted/decision_log.md` (mismo
  template que P1: Date/Stage-Gate/Decision/Justification/Evidence reviewed/Frozen
  parameters/Blockers or limitations/Responsible/Status/Next action).
- `Paper_2/ops/sted/traceability_matrix.csv` registra los claims P2-H1 (mejora simultánea grande) y
  P2-H2 (robustez bajo condiciones no vistas), con el mismo formato de columnas que
  `Paper_1/ops/sted/traceability_matrix.csv`.
- Un único artefacto de trayectorias por figura dinámica, mismo principio acotado que
  `Paper_1/artifacts/trajectories/fig1_case.npz` (SS26 de P1). Excepción registrada en esta ronda:
  `Paper_2/artifacts/trajectories/p2e3b_step_traces.npz` (P2-E3B, §7-bis) agrupa las 12 trayectorias
  de escalón comando→potencia en un único archivo, mismo principio de acotar a un artefacto por
  etapa de caracterización.
- Artefactos nuevos de esta ronda: `Paper_2/artifacts/preflight/p2_actuator_calibration.csv` +
  `Paper_2/artifacts/figures/p2_actuator_calibration.png` (P2-E3A); `Paper_2/artifacts/diagnostics/
  p2_dynamic_response.csv` + `Paper_2/artifacts/trajectories/p2e3b_step_traces.npz` +
  `Paper_2/artifacts/figures/p2_dynamic_response_example.png` (P2-E3B).
- Figuras generadas con el skill `ieee-elsevier-benchmark-figures` (mismo estilo que P1-E7), rutas
  ajustadas a `Paper_2/artifacts/{figures,tables}/`.

---

## 30. Decisiones congelables ahora vs. pendientes

### Ya congelable con este plan (no requiere experimento adicional)

- Estructura de carpetas y gobernanza (§0), rama `p2_td3_hybrid_ffc`.
- Forma funcional del controlador híbrido (§4) y de la reward (§6).
- `J_val_P2` (§7), sin término de energía.
- Forma de la training distribution (§10) y splits (§11) — **congelado en P2-E2**
  (`Paper_2/ops/sted/decision_log.md` DEC-P2-003): `G_train_P2`/`G_validation_P2`/`G_test_P2`,
  `L_train_P2`/`L_validation_P2`/`L_test_P2`, `OP_*_P2`.
- Forma del gate científico (§21): `I_f/I_r >= 0.10`, `>=10/12`, medianas `>=0.15` — pendiente solo
  de confirmar el número de seeds (§18) antes de congelar el criterio seed-level exacto.
- Hiperparámetros TD3 iniciales (§17) — sujetos a smoke/preflight, no a HPO.
- STOP-P2-A/B/C (§20).

### Ya congelable con esta revisión (nuevo)

- Convención de potencia `Sb=100 MVA` (§0-bis) — ya aplicada en código (DEC-P2-005) y verificada
  empíricamente (P2-E3A, esta ronda).
- Orden de etapas revisado (§25): `P2-E3A` → `P2-E3B` → `P2-E4` (`Tc`) → `P2-E5` (`K_f`/`K_r`) →
  `P2-E6` (`alpha_P`) → `STOP-P2-A` → `P2-E7`...`P2-E14`.
- `STOP-P2-A` redefinido como design target multicriterio, no umbral rígido de 20-40% (§20).

### Pendiente de una etapa de diseño explícita (no se puede fijar en este documento)

- `Tc` final (P2-E4, requiere P2-E3A/E3B PASS — **PASS confirmado esta ronda**, ver reporte de cierre
  de turno).
- `K_f*`/`K_r*` final, con diagnóstico F-only/R-only/F+R previo (P2-E5).
- `alpha_P`/`P_max,BESS` final, con `K_f`/`K_r` físicamente constantes (P2-E6, **después** de `Tc` y
  `K_f`/`K_r` — reordenado, ver §13/§25). El sweep pre-corrección (`p2e3_alpha_p_sweep.csv`) sigue
  `INVALID` (§0-bis) y no cuenta como P2-E6 ya ejecutado.
- Definición exacta de `RoCoF_COI` (P2-E1/E7).
- Configuración de observación final: OBS-A/B/C (P2-E7).
- Valores finales de `rho`/`alpha_L` de P2-T9..T12, tras verificación de viabilidad numérica (antes
  de congelar la batería completa).

### Pendiente de decisión explícita del usuario

- **Número de seeds**: 3 (comparabilidad directa con P1) vs. 5 (recomendado por el usuario para un
  paper más robusto, con mayor costo computacional). Definir antes de P2-E8 (freeze).
- Si el nivel superior de `alpha_P` probado en P2-E6 resulta numéricamente infactible, decidir entre
  un nivel menor o una revisión de ubicación de BESS.
- Qué hacer si `STOP-P2-A` se activa (margen físico insuficiente bajo el criterio multicriterio de
  §20): revisar autoridad/ubicación BESS, revisar `Tc`, revisar la estructura `K_f`/`K_r`, o
  reencuadrar el estudio — el usuario decide entre esas opciones si ocurre.

---

## 31. Próxima acción

Este plan queda en estado `PLAN_DRAFT`, revisado esta ronda. **P2-E3A y P2-E3B ya se ejecutaron en
esta misma ronda** (ver reporte de cierre de turno para resultados numéricos completos); **no se
ejecuta P2-E4 (diseño de `Tc`) en adelante sin confirmación explícita del usuario.** No se ha
entrenado ni ejecutado ningún test P2 (P2-T1..T12); no se ha tocado ningún split, bus BESS, caso
low-inertia, ni reward TD3.
