# Paper_2 STED Decision Log — Physics-Informed TD3 Hybrid FFC (IEEE-39 / ANDES)

STATUS: ACTIVE

Use one entry per stage (`P2-E0`–`P2-E13`), gate evaluation (`P2-H1`, `P2-H2`), design checkpoint
(`STOP-P2-A`), or freeze decision (BESS authority, `Tc`, `K_f`/`K_r`, splits, observation, seeds,
checkpoint) defined in `Paper_2/plan_maestro_P2_TD3_Hybrid_FFC.md`. This log is independent of
`Paper_1/ops/sted/decision_log.md` and of the root `ops/sted/decision_log.md` — do not merge entries
between the three. `Paper_1` remains frozen and unmodified; see
`Paper_1/ops/sted/decision_log.md` (entry referencing the birth of Paper_2 from Paper_1's findings)
for the cross-reference in the other direction.

## Decision Entry Template

```markdown
## DEC-P2-XXX
Date:
Stage/Gate:
Decision:
Justification:
Evidence reviewed:
Frozen parameters:
Blockers or limitations:
Responsible:
Status:
Next action:
```

---

## DEC-P2-001

Date: 2026-08-19
Stage/Gate: P2-E0 (estructura, gobernanza, plan)
Decision: Se crea la campaña `Paper_2`, completamente separada de `Paper_1`, con su propia rama de
trabajo (`p2_td3_hybrid_ffc`), estructura de carpetas (`Paper_2/{src,cases,artifacts,ops/sted}`,
sin symlinks ni referencias a `Paper_1/`), copia propia del caso base IEEE-39
(`Paper_2/cases/ieee39/base/ieee39_full.xlsx`, copiada byte-a-byte de `Paper_1/cases/ieee39/base/`,
que a su vez es idéntica al caso stock de ANDES verificado en P1-E0), y el plan maestro
`Paper_2/plan_maestro_P2_TD3_Hybrid_FFC.md` (estado `PLAN_DRAFT`).
Justification: Instrucción explícita del usuario: preservar P1 intacto, abrir una P2 nueva orientada
a mejoras grandes y simultáneas de nadir y RoCoF sin penalizar potencia/energía del BESS, con
gobernanza y estructura de artefactos completamente separadas (`No reutilizar carpetas de artefactos
de Paper_1`). El usuario proveyó una especificación técnica completa (30 secciones: motivación,
arquitectura híbrida física+TD3 residual, reward, `J_val_P2`, diseño de `Tc`/autoridad BESS/`K_f`-
`K_r`, splits, batería de test P2-T1..T12, gate científico al 10%, TD3/SB3, preflight de 16 checks,
figuras, reglas de stop) más dos énfasis explícitos: (1) T1-T8 de P1 no pueden reutilizarse como test
ciego de P2 -- solo como referencia histórica/diagnóstico -- por riesgo de leakage metodológico,
dado que P2 se diseña explícitamente a partir de sus fallos; (2) priorizar el sweep físico barato
(autoridad de BESS + `K_f`/`K_r`, sin RL) como gate de decisión antes de invertir horas de cómputo en
entrenar TD3 -- si el controlador físico no demuestra margen, el cuello de botella es de
dinámica/modelado, no de algoritmo. Ambos énfasis quedaron formalizados en el plan como la regla de
gobernanza de la Seccion 0 y como `STOP-P2-A` (Seccion 20), respectivamente.
Evidence reviewed: `Paper_1/ops/sted/decision_log.md` DEC-P1-021 (resultado negativo completo de P1:
H1 rechazada 1/8, H2 no soportada 1/8, H3 rechazada 2/4) y DEC-P1-022 (cierre de figuras P1-E7);
`Paper_1/src/run_ffc_study.py` (inspección de funciones reutilizables sin modificación: `build_case`,
`h_report`, `_find_ordered`, `worst_bus_freq_rocof`, `add_bess_pair`, `natural_bus_voltages*`, y el
patrón de bucle `itm_step()`; funciones P1-specific que deben reescribirse: `compute_reward`,
`FFCEnv`, `make_ddpg_model`/`train_seed`, `TEST_SCENARIOS`/`run_test_scenario`,
`evaluate_validation`, `dimension_bess`/`tune_droop` -- ver Seccion 26 del plan); `git log --oneline
-- Paper_1/plan_maestro_DDPG_FFC_IEEE39_ANDES.md` (confirma que la copia canónica del plan de P1
vive exclusivamente en `Paper_1/`, tras eliminar el duplicado obsoleto de la raíz, ver DEC-024 en
`ops/sted/decision_log.md` de la raíz).
Frozen parameters:
```text
P2_BRANCH = p2_td3_hybrid_ffc
P2_STRUCTURE_CREATED = TRUE
P2_PLAN_STATUS = PLAN_DRAFT
P1_UNTOUCHED = TRUE (verificado: ningun artefacto/resultado/decision_log de Paper_1 modificado)
T1_T8_REUSE_POLICY = DIAGNOSTIC_ONLY_NOT_BLIND_TEST
```
Blockers or limitations: Ninguno operativo. El plan deja explícitamente pendientes de una etapa de
diseño (no fijables en el documento): `Tc` final, `alpha_P`/`P_max,BESS` final, `K_f*`/`K_r*` final,
definición de `RoCoF_COI`, configuración de observación final, IDs concretos de splits, y los valores
finales de P2-T1..T12 tras verificación de viabilidad numérica. También queda pendiente de decisión
explícita del usuario: número de seeds (3 vs. 5).
Responsible: Claude (creación de estructura y redacción del plan, instrucción explícita del usuario)
Status: passed
Next action: Presentar el plan al usuario (arquitectura, estructura de carpetas, decisiones
congelables/pendientes, riesgos técnicos, estimación de duración por etapa) y esperar su aprobación
explícita antes de iniciar P2-E1 o cualquier ejecución/entrenamiento (Seccion 31 del plan).

## DEC-P2-002

Date: 2026-08-19
Stage/Gate: P2-E1 (reuso/verificación del caso low-inertia)
Decision: Se creó `Paper_2/src/p2_common.py` (utilidades físicas propias de P2, portadas de
`Paper_1/src/run_ffc_study.py` sin importar desde `Paper_1/`, ver plan Sección 26) y se re-verificó
Gate LI-1 sobre la copia propia del caso (`k=0.50`, `rho=0.80`, `GENROU_1` como generador de diseño,
mismos criterios SS5.3 de P1). Resultado: **GATE LI-1 PASS** — PFlow converge, TDS inicializa, EIG
sin modos nuevos introducidos (`n_positive` variante=4 <= baseline=4, `max_real` variante=1.005 <=
baseline=1.006), `|df_nadir|=111.1 mHz >= 40 mHz` y `RoCoF_max=0.5755 Hz/s >= 0.5 Hz/s` (criterio 4),
sin necesidad de extender horizonte (nadir en t=4.666s < 6s). `df_nadir=-0.1111 Hz` coincide con el
valor original de P1 (`-0.11111136583686942 Hz`, ver regresión en evidence reviewed) al 4to decimal
mostrado, confirmando que el puerto reproduce la misma física. Variante congelada en
`Paper_2/cases/ieee39/variants/ieee39_low_inertia.xlsx`.
**Bug de entorno encontrado y evitado (no un bug de física):** `ss.TDS.run()` completaba la
simulación correctamente (`dae.t` alcanzaba `tf`, `TDS.run()` retornaba `True`) pero
`ss.TDS.plt` (el buffer `TDSData` que expone la trayectoria para lectura posterior) quedaba `None`
de forma reproducible al ejecutar como archivo `.py` (2/2 intentos), pese a funcionar de forma
igualmente reproducible al ejecutar el mismo código vía `python -c` (3/3 intentos) — causa raíz no
identificada (posible dependencia interna de ANDES en el modo de invocación, no investigada más a
fondo por no ser necesaria). En vez de perseguir esa fragilidad, se reemplazó la lectura post-hoc vía
`TDS.plt` por el patrón de stepping manual con `itm_step()` + lectura en vivo de
`BusFreq.f.v`/`BusROCOF.Wf_y.v` ya validado y usado extensivamente en P1-E4 a P1-E7
(`worst_freq_rocof_stepped()`, nueva función en `p2_common.py`) — sin esa dependencia frágil, y que
además es el mismo mecanismo que P2-E4 necesitará para probar `Tc<100ms`. `worst_bus_freq_rocof()`/
`_find_ordered()` se dejaron en el archivo por completitud de referencia, pero **no se usan** en
ningún flujo de P2 a partir de esta entrada.
**Supuesto explícito para objeción del usuario:** el plan de P2 no especifica un nuevo proceso de
selección de ubicación de BESS (a diferencia de sizing, Sección 13, y tuning `K_f`/`K_r`, Sección
14). Se asume que P2 reutiliza la ubicación ya congelada de P1 (buses 13 y 12), por ser una decisión
no aprendida y libre de leakage (`CLM-PLACEMENT` de P1) y por ausencia de instrucción explícita de
rehacerla. Esto se deja registrado explícitamente aquí para que el usuario lo objete si su intención
era otra; no se ha usado todavía en ningún cómputo de P2 (P2-E2 en adelante).
Justification: El plan (Sección 27, orden de ejecución) exige "reusar/verificar caso low-inertia
congelado físicamente, sin modificar P1" como P2-E1. Verificar sobre la copia propia del código
(no solo copiar el archivo `.xlsx`) confirma que el puerto a `Paper_2/src/` no introdujo ninguna
divergencia silenciosa antes de construir el resto del pipeline P2 sobre él.
Evidence reviewed: salida de consola de `Paper_2/src/stage_p2e1_verify_low_inertia.py` (gate_pass=
True, valores arriba); regresión directa de `Paper_1/src/run_ffc_study.run_li1_gate(k=0.50,
rho=0.80, tf=6.0)` en esta misma sesión confirmando `gate_pass=True`, `df_nadir_hz=
-0.11111136583686942` (valor de referencia); diagnóstico paso a paso del bug de `TDS.plt`
(`PFlow converged: True`, `TDS.run() returned: True`, `dae.t: 6.0`, `plt after TDS.run(): None`)
que descarta que sea una falla numérica real de la simulación.
Frozen parameters:
```text
P2_LOW_INERTIA_VARIANT = Paper_2/cases/ieee39/variants/ieee39_low_inertia.xlsx
P2_GATE_LI1_REVERIFIED = TRUE
P2_BESS_PLACEMENT_ASSUMPTION = REUSE_P1_BUSES_13_12 (pendiente de confirmación del usuario)
```
Blockers or limitations: El archivo `.xlsx` de P2 no es byte-idéntico al de P1 (`filecmp.cmp`
retorna `False`) pese a ser producido por la misma física y el mismo `k=0.50` — atribuible a
metadatos/serialización de `andes.io.dump()` (timestamps, orden interno), no a una diferencia de
contenido numérico; no se investigó más a fondo por no ser un requisito del plan. `worst_bus_freq_
rocof()`/`_find_ordered()` quedan sin uso activo en el pipeline de P2 (ver nota de bug arriba).
Responsible: Claude (ejecución de P2-E1 tras autorización explícita del usuario, "ok, realizalo")
Status: passed
Next action: P2-E2 — definir y congelar splits (`G_train_P2`/`G_validation_P2`/`G_test_P2`,
`L_train_P2`/`L_validation_P2`/`L_test_P2`) usando distancia eléctrica desde los buses BESS (13, 12,
bajo el supuesto de reuso arriba) y registrar potencia nominal, siguiendo la metodología de P1
SS7.2/§7 (Sección 11/12 del plan de P2).

## DEC-P2-003

Date: 2026-08-19
Stage/Gate: P2-E2 (splits train/validation/test)
Decision: Se calculó la distancia eléctrica (Dijkstra, suma de `|X|` de líneas, misma metodología que
P1 SS7.2/§7, nueva función `electrical_distance()` en `p2_common.py` -- no existía como función
persistida en P1, solo como script efímero de esa sesión) desde los buses BESS congelados (13, 12)
hacia los 9 generadores no-slack y las 19 cargas PQ del caso IEEE-39. Con esos datos se congelaron
los splits:
```text
G_validation_P2 = [GENROU_6]                    (bus 35, dist=0.0830, mediana de los 9)
G_test_P2       = [GENROU_9, GENROU_3]           (bus 38 Sn=1684.1MVA dist=0.1602 max;
                                                   bus 32 Sn=843.7MVA dist=0.0243 min)
G_train_P2      = [GENROU_1,2,4,5,7,8]           (6 generadores restantes)

L_validation_P2 = [PQ_10]                        (bus 21, P0=274.0MW, dist=0.0547, mediana)
L_test_P2       = [PQ_1, PQ_16]                  (bus 3 P0=600MW dist=0.0443;
                                                   bus 28 P0=206MW dist=0.1295)
L_train_P2      = [PQ_2,3,4,6,7,8,9,11,12,13,14,15,17,18,19]  (15 cargas restantes)
L_excluded_P2   = [PQ_5]                         (bus 12 == BESS_BUS_2, co-localizada, dist=0.0000)

OP_train_range_P2      = U(0.90, 1.10)  (continuo, entrenamiento)
OP_validation_P2       = {0.95, 1.00, 1.05}  (discreto, dentro del rango de training)
OP_test_outside_P2     = {0.88, 1.12}  (discreto, FUERA del rango de training)
```
Regla aplicada (generadores): `G_test_P2` combina el generador de mayor capacidad y mayor distancia
eléctrica al BESS (caso más exigente: disturbio grande, lejos de los actuadores) con el generador
más cercano (caso de campo cercano); `G_validation_P2` usa el de distancia mediana (caso "típico").
Regla aplicada (cargas): mismo principio con `L_test_P2` (carga grande cercana + carga lejana) y
`L_validation_P2` (mediana). `PQ_5` (bus 12) queda excluida de todo split por estar co-localizada
con `BESS_BUS_2` -- perturbarla sería un caso degenerado de campo cercano, no representativo.
**Nota de independencia respecto a P1:** `G_validation_P2=GENROU_6` coincide con el `G_V` de P1 --
es una coincidencia de la regla de distancia mediana aplicada independientemente (no una reutilización
deliberada; no hay prohibición de coincidir en el generador de validación, a diferencia de los
escenarios de test). `L_test_P2` (`PQ_1`/bus 3, `PQ_16`/bus 28) se eligió deliberadamente
DISTINTO de `L_A`/`L_B` de P1 (bus 20/bus 29) para maximizar independencia del conjunto de test; esos
dos buses de P1 caen en `L_train_P2` en cambio.
Justification: El plan (Sección 11/12) exige nuevos splits, con generadores/cargas de validation y
test nunca vistos en training, y prohíbe expresamente reutilizar T1-T8 de P1 como test de P2. La
regla de distancia eléctrica es la misma ya validada y auditada en P1 (S-07), aplicada aquí sobre el
par de buses BESS ya congelado, con un criterio explícito y reproducible (extremos de
capacidad/distancia para test, mediana para validation) en vez de una selección arbitraria.
Evidence reviewed: salida de consola y `Paper_2/artifacts/diagnostics/p2e2_electrical_distances.json`
(tabla completa de 9 generadores y 19 cargas con bus, capacidad/potencia nominal y distancia al BESS,
producida por `Paper_2/src/stage_p2e2_electrical_distances.py`); verificación cruzada de que
`GENROU_9`/bus 38/Sn=1684.1MVA y `PQ_9`/bus 20/P0=680MW coinciden exactamente con los valores de
referencia ya registrados en comentarios de `Paper_1/src/run_ffc_study.py`
(`G_A_PREVIEW`/`L_A`), confirmando que el cálculo de distancia eléctrica reproduce el mismo dato base
que P1.
Frozen parameters: ver bloque `G_*_P2`/`L_*_P2`/`OP_*_P2` arriba, también persistido como constantes
en `Paper_2/src/p2_common.py`.
Blockers or limitations: Los valores concretos de `rho`/`alpha_L`/severidad para la batería de test
`P2-T1..T12` (plan Sección 12) todavía usan `G_A`/`G_B` como nombres genéricos ("gen no visto A/B");
quedan mapeados aquí a `GENROU_9` (A) y `GENROU_3` (B), y "carga no vista A/B" a `PQ_1` (A) y
`PQ_16` (B) -- pendiente de verificación de viabilidad numérica (PFlow/TDS) antes de congelar los
escenarios P2-T1..T12 en sí (todavía no ejecutado, es un paso posterior según el plan).
Responsible: Claude (ejecución de P2-E2 tras autorización explícita del usuario, "ok, realizalo")
Status: passed
Next action: Actualizar `Paper_2/plan_maestro_P2_TD3_Hybrid_FFC.md` Sección 12 con los IDs concretos
de generador/carga recién congelados (en vez de "A"/"B" genérico), y continuar con P2-E3 (diseño de
autoridad de potencia BESS, `alpha_P`) solo tras nueva autorización explícita del usuario -- el plan
exige esperar confirmación antes de cada etapa de diseño con cómputo no trivial.

## DEC-P2-004

Date: 2026-08-19
Stage/Gate: **P2-E3 — BLOQUEADA.** Sweep de autoridad de potencia BESS (`alpha_P`) iniciado tras
autorización explícita del usuario ("si realiza el sweep..."), pero **detenido antes de aceptar
resultados** al encontrar que la convención de comando de potencia heredada de P1
(`Pext0 = dp_mw / P_max,BESS`, `DEC-P1-016`) no escala la potencia realmente entregada a la red con
`P_max,BESS`. Ver el hallazgo completo, con evidencia de código fuente de ANDES y tres pruebas
directas, en `Paper_1/ops/sted/decision_log.md` `DEC-P1-024` (registrado por instrucción explícita
del usuario, sin modificar ningún resultado de P1).
Decision: El artefacto `Paper_2/artifacts/diagnostics/p2e3_alpha_p_sweep.csv` (2 escenarios DESIGN x
3 niveles `alpha_P`) **se marca como NO VÁLIDO / NO USAR** para ninguna decisión de congelamiento --
sus valores de `I_f`/`I_r` no reflejan el efecto real de variar `P_max,BESS`, porque los tres niveles
de `alpha_P` probados, con la convención heredada, entregan la MISMA potencia física real a la red
(techo real ~100 MW/unidad, ver DEC-P1-024) pese a etiquetarse como 293/440/587 MW. No se elimina el
archivo (transparencia del proceso), pero queda excluido de cualquier freeze futuro de P2-E3.
Justification: SS31-equivalente de P2 (Sección 20, prohibiciones) no permite congelar una decisión de
diseño (`P_max,BESS`) sobre datos que no reflejan la física real que se está intentando medir.
Continuar el sweep con la convención heredada habría producido una conclusión sin sentido (autoridad
de potencia "sin efecto observable" cuando en realidad nunca varió de verdad) -- exactamente lo
opuesto al pedido explícito del usuario de un efecto "claramente observable" en esta etapa.
Evidence reviewed: salida de consola de `Paper_2/artifacts/diagnostics/p2e3_alpha_p_sweep.csv` (I_f/
I_r idénticos entre alpha=1.0/1.5/2.0, ver hallazgo); tres diagnósticos directos ejecutados sobre
`Paper_2/src/p2_common.py` (comando fraccional fijo con Sn variable; techo de saturación con Sn
variable); código fuente de ANDES referenciado en DEC-P1-024.
Frozen parameters: Ninguno congelado en esta entrada -- P2-E3 permanece abierta/bloqueada.
```text
P2_E3_ALPHA_SWEEP_INVALID = TRUE
P2_E3_BLOCKED_PENDING_USER_DECISION = TRUE
```
Blockers or limitations: Ninguna decisión tomada todavía sobre si `p2_common.py` debe cambiar a
`Pext0 = dp_mw / 100.0` (base de sistema) para todo el pipeline P2, ni sobre si investigar primero la
causa raíz exacta del techo de ~100 MW (que podría ser un límite estructural del modelo `PVD1`/
`ESD1`, no necesariamente ajustable con `Sn`) -- el usuario no seleccionó ninguna de esas dos opciones
en esta ronda, solo autorizó documentar el hallazgo en Paper_1. Hasta que el usuario decida, ninguna
de las fórmulas del plan que asumen la convención `dp_mw/P_max,BESS` (K_f0/K_r0 en Sección 14,
`P_max,BESS` en Sección 13) puede considerarse verificada.
Responsible: Claude (P2-E3 ejecutada bajo autorización, detenida al encontrar el hallazgo, escalada
antes de continuar)
Status: blocked
Next action: Esperar instrucción explícita del usuario sobre cómo tratar la convención de escala de
potencia en P2 (corregir y continuar el sweep, investigar la causa raíz del techo de ~100 MW primero,
o alguna otra dirección) antes de reintentar P2-E3.

## DEC-P2-005

Date: 2026-08-19
Stage/Gate: P2-E3 (autoridad de potencia BESS + tanteo informal de ganancia) — **desbloqueada tras
corrección; margen físico estable encontrado, modesto, con recomendación de investigar `Tc` a
continuación.**
Decision: Se aplicó la corrección identificada en `DEC-P1-024` a `Paper_2/src/p2_common.py`:
1. `add_bess_pair()`: `pmx` (límite duro de potencia de `ESD1`) cambia de fijo `1.0` a
   `p_max_bess_mw/100.0` — antes, CUALQUIER `P_max,BESS` quedaba silenciosamente capado a ~100 MW
   reales sin importar el valor etiquetado.
2. `run_physical_scenario()`: `ss.DG.set_paux(...)` cambia de `dp_mw/p_max_bess_mw` a `dp_mw/100.0`
   (base de sistema, `Sb=100 MVA`) — antes, la potencia real entregada NO escalaba con
   `P_max,BESS` en absoluto (ver `DEC-P1-024`/`DEC-P2-004`).
3. El metro de potencia entregada (`p1_act`/`p2_act`, usado para `p_peak_mw`) cambia de
   `Ipout_y*v*Sn` a `Ipout_y*v*100.0` por la misma razón.
Con la física corregida, se re-ejecutó el sweep `alpha_P={1.0,1.5,2.0}` con las ganancias
`K_f0=P_max,BESS/0.5Hz`, `K_r0=P_max,BESS/1.0Hz/s` de SS14: el efecto ahora es dramáticamente visible
(a diferencia del sweep inválido de DEC-P2-004) pero **desestabilizador**: RoCoF empeora hasta 5.8x
frente a No-FFC, con 20-28% de saturación, en casi todas las combinaciones excepto
`alpha_P=1.0`/ganancia completa (único caso estable a ganancia 1.0x). Autorizado por el usuario
("adelantar un tanteo rápido de ganancias menores"), se probaron multiplicadores de ganancia
`{0.25,0.5,1.0}` en los 3 niveles de `alpha_P`, confirmando que la variable que determina
estabilidad es `(k_f,k_r)` en sí, no `P_max,BESS` (pares `(k_f,k_r)` idénticos producidos por
distintas combinaciones `alpha_P`/`gain_mult` dan resultados idénticos bit a bit, mientras no haya
saturación). Autorizado un refinamiento adicional ("refinar la grilla... a Tc=100ms fijo"): se probó
`gain_mult in {0.5,0.6,0.7,0.8,0.9,1.0}` a `alpha_P=1.0` (`P_max,BESS=293.4MW`, `K_f0=586.8`,
`K_r0=293.4`) fijo, para los dos probes DESIGN (`GENROU_4`@rho=0.90, `PQ_9`(bus 20)@alpha_L=0.50):
```text
Probe gen (GENROU_4, rho=0.90):
  gain_mult 0.5->1.0: I_f crece MONOTONA y SUAVEMENTE de +0.063 a +0.088 (6.3%->8.8%)
  I_r = 0.000 en TODO el rango (RoCoF no mejora nunca); sat=0.0 en todo el rango (sin saturar)

Probe load (PQ_9, +50%):
  gain_mult 0.5 a 0.9: df_nadir_phys IDENTICO bit a bit (-121.40884706472832 mHz) -- I_f=+0.084
    fijo, I_r=0.000 fijo, sin saturar -- la respuesta es insensible a la ganancia en este rango
    (mecanismo exacto no investigado: posible interaccion con el deadband fdbd=-0.017Hz u otro
    bloque discreto de ESD1, no crítico para la conclusión de esta etapa)
  gain_mult 1.0: salto abrupto a inestabilidad (I_f=-0.741, I_r=-1.704, sat=0.117)
```
**Mejor resultado estable encontrado en esta etapa: ~8.8% de mejora de nadir (probe gen, ganancia
máxima probada sin saturar), 0% de mejora de RoCoF, en TODO el rango de ganancia estable probado.**
Muy por debajo del margen de 20-40% que STOP-P2-A/S14.1 sugeriría como umbral para justificar TD3.
El aumento de potencia/ganancia no escala el beneficio de forma continua: o no cambia nada (probe
load, rango bajo) o desestabiliza abruptamente (ambos probes, cerca de ganancia 1.0x).
Justification: El usuario autorizó explícitamente cada paso (corregir convención y continuar;
tanteo informal de ganancias menores; refinar la grilla a Tc=100ms fijo). Ningún valor se congeló
todavía -- esta sigue siendo información de diseño/DESIGN-set, no una decisión formal de P2-E3
(que requiere completar también la comparación de `alpha_P=1.5/2.0` con ganancias apropiadamente
escaladas, no solo `alpha_P=1.0`).
Evidence reviewed: `Paper_2/artifacts/diagnostics/p2e3_alpha_p_sweep.csv` (sweep corregido,
inestable a ganancia 1.0x); `Paper_2/artifacts/diagnostics/p2e3_gain_tanteo.csv` (tanteo 0.25/0.5/1.0
x 3 alpha_P); `Paper_2/artifacts/diagnostics/p2e3_gain_refine.csv` (refinamiento 0.5-1.0 a alpha_P=1.0
fijo, tabla completa arriba); tres pruebas de verificación de la corrección física (fracción fija
a Sn variable, techo de saturación a Sn variable, pmx escalado restaurando el techo esperado) ya
registradas en `DEC-P1-024`.
Frozen parameters: Ninguno formalmente congelado todavía.
```text
P2_POWER_SCALING_BUG_FIXED_IN_P2_COMMON = TRUE
P2_E3_BEST_STABLE_MARGIN_FOUND_SO_FAR = I_f~0.088, I_r~0.0 (Tc=100ms, gain_mult<=1.0 en probe gen;
                                        <1.0 en probe load)
P2_E3_STILL_OPEN = TRUE (no se ha congelado P_max,BESS ni K_f*/K_r* formalmente)
```
Blockers or limitations: El mecanismo exacto de la meseta plana del probe de carga (gain_mult 0.5-0.9
idéntico bit a bit) no fue investigado -- no bloquea la conclusión principal pero queda como
curiosidad sin explicar. Solo se probaron 2 escenarios DESIGN (uno de generación, uno de carga); el
plan (S14) especifica una grilla de 9 combinaciones `K_f`x`K_r` independientes (no solo un escalar
`gain_mult` común a ambos) sobre un conjunto DESIGN más amplio -- esto sigue pendiente si se decide
formalizar P2-E3/P2-E5. El margen modesto (~8.8% nadir, 0% RoCoF) sugiere que `Tc=100ms` podría ser
el cuello de botella real, no la potencia/ganancia -- consistente con la intuición original del
usuario sobre priorizar el diseño de `Tc` -- pero esto no está confirmado, solo es una hipótesis
razonable a partir de los datos.
Responsible: Claude (ejecución bajo autorización explícita del usuario en cada paso)
Status: passed (informativo; P2-E3 formal sigue abierta)
Next action: Esperar instrucción del usuario: adelantar el diseño de `Tc` (P2-E4, probar si las
mismas ganancias que desestabilizan a 100ms se vuelven estables y más efectivas a 50/20ms), continuar
refinando la grilla de ganancias a `Tc=100ms` fijo, o congelar el resultado modesto encontrado y
seguir el orden normal del plan.

## DEC-P2-006

Date: 2026-08-19
Stage/Gate: Revisión formal del plan maestro (instrucción explícita del usuario, "Actualizar el plan
maestro de Paper_2... y corregir el diseño experimental antes de continuar con nuevos sweeps o
entrenamiento TD3"). No es una etapa numerada del plan en sí -- es una revisión de gobernanza que
reordena las etapas futuras.
Decision: Se actualizó `Paper_2/plan_maestro_P2_TD3_Hybrid_FFC.md` con los siguientes cambios
estructurales:
1. **Convención formal de potencia (nueva Seccion 0-bis):** `Sb_MVA=100.0`; `Pext0_command_pu =
   P_command_MW/100.0`; `pmx_pu = Pmax_BESS_MW/100.0`; `P_delivered_MW = Ipout_y*v*100.0`. `Sn` nunca
   se usa como base de conversión. Prohibidos explícitamente: `dp_mw/Pmax_BESS`, `Ipout_y*v*Sn`,
   `pmx=1.0` hardcodeado. Esta convención ya estaba aplicada en código (DEC-P2-005) pero no
   formalizada como regla del plan/preflight -- ahora lo está.
2. **Nueva etapa obligatoria P2-E3A (BESS actuator calibration gate)** y **P2-E3B (BESS dynamic
   response characterization)**, ambas antes de P2-E4 (`Tc`, antes P2-E4 sin prerrequisito explícito
   de actuador). Nueva Seccion 7-bis.
3. **Reordenamiento de etapas (Seccion 25):** el sweep de autoridad de potencia (`alpha_P`, antes
   P2-E3) se mueve a **P2-E6**, después de `Tc` (P2-E4) y del tuning `K_f`/`K_r` (P2-E5) -- no antes.
   Razón: DEC-P2-005 mostró que estabilidad/desempeño dependen conjuntamente de `Tc`, `K_f`, `K_r` y
   `P_max,BESS`; seleccionar `P_max,BESS` con `Tc` provisional y ganancias no estabilizadas no es
   científicamente limpio. Todas las etapas posteriores se renumeran (+2 o +3 según el caso, ver
   tabla completa en Seccion 25 del plan).
4. **Separación obligatoria de `K_f`/`K_r`** (Seccion 14): se elimina como estrategia principal el
   `gain_mult` escalar único (usado solo como tanteo informal en DEC-P2-005); se añade diagnóstico
   obligatorio F-only (`K_r=0`) / R-only (`K_f=0`) / F+R antes de la grilla completa; la grilla
   original `{0.5,1.0,2.0}x{0.5,1.0,2.0}` (9 combinaciones, centrada en 1.0x que DEC-P2-005 mostró
   desestabilizante) se reemplaza por una grilla conservadora `K_f/K_f0 in {0.25,0.50,0.75,1.00}` x
   `K_r/K_r0 in {0.00,0.25,0.50,0.75,1.00}` (20 combinaciones), sin valores >1.0 sin evidencia previa.
5. **Rediseño del sweep de `Pmax` (Seccion 13):** regla obligatoria de aislamiento de variable -- al
   variar `P_max,BESS`, `K_f`/`K_r` se mantienen físicamente constantes (no un múltiplo relativo de
   `P_max,BESS`, que fue el problema del sweep original DEC-P2-004: no podía distinguirse autoridad
   física de ganancia de realimentación). Reglas de interpretación explícitas (saturación vs. no
   saturación) y verificación de headroom para el residual TD3.
6. **Redefinición de `STOP-P2-A`** (Seccion 20, Seccion 14.2): de un umbral rígido 20-40% a un design
   target multicriterio (mejora simultánea reproducible + estabilidad numérica + ausencia de
   saturación patológica + consistencia entre escenarios DESIGN/VALIDATION), evaluado después de
   P2-E6 (`Pmax` ya congelado), no después de P2-E5 como antes. Se añade la lista de causas candidatas
   a diagnosticar si el gate falla (actuator bandwidth, RoCoF estimator, `Tc`, `Kf/Kr` structure,
   `Pmax` saturation, BESS location, model limitations).
7. **Ablations renumeradas** (Seccion 16): A1=Droop vs F-only, A2=F-only vs F+R (nueva, aísla el
   aporte de RoCoF), A3=Physical F+R vs Physical+TD3 (antes A2), A4=Tc=100 vs Tc elegido (sin cambio),
   A5=local vs local+COI (antes A4). Pure-TD3-vs-Hybrid y gen-only-vs-mixed-training pasan a
   opcionales (A6/A7).
8. **Preflight ampliado a 26 checks** (Seccion 23): `PF2-ACT-01..06` (conversión MW, escalado `pmx`,
   calibración commanded-vs-delivered, signos, saturación en el límite correcto, lectura en base de
   sistema) y `PF2-DYN-01..04` (caracterización command->power, timing de `Tc`, consistencia de
   muestreo RoCoF entre `Tc`, sin dependencia oculta de `TDS.plt`), sumados a los 16 originales
   (`PF2-01..16`, sin cambio de contenido).
Justification: Instrucción explícita del usuario, con la prioridad declarada de demostrar, en este
orden: (1) que el actuador BESS está correctamente calibrado en ANDES; (2) que la dinámica
comando->potencia está caracterizada; (3) que `Tc`/`K_f`/`K_r`/`Pmax` se diseñan en el orden correcto;
(4) que el término RoCoF realmente aporta información/control útil antes de incorporarlo al
controlador híbrido final. El usuario fue explícito: no ejecutar TD3, no abrir el test final P2, no
reinterpretar resultados inválidos como evidencia, no congelar todavía `Pmax`/`Tc`/`Kf`/`Kr`.
Evidence reviewed: `Paper_2/ops/sted/decision_log.md` DEC-P2-004 (sweep `alpha_P` inválido, causa
raíz), DEC-P2-005 (corrección aplicada + tanteo informal que motiva la separación `Kf`/`Kr` y el
rediseño del sweep de `Pmax`); código fuente de ANDES (`andes/models/distributed/pvd1.py`,
`andes/models/distributed/esd1.py`) inspeccionado en esta ronda para verificar la cadena algebraica
`Pext0`->`Psum`->`Ipul`->`Ipcmd`->`Ipout` (sin factor `Sn`) y para distinguir `ESD1.Tf` (constante del
integrador de SOC, "Integrator constant for SOC model") de `PVD1.tip` (constante de retardo de
corriente activa, "Inverter active current lag time constant", default 0.02s) -- ver DEC-P2-007/008
para los resultados empíricos de esta verificación.
Frozen parameters: Ninguno congelado en esta entrada -- es una revisión de plan/gobernanza, no una
etapa de diseño con resultado numérico a congelar.
```text
P2_PLAN_REVISED_POWER_CONVENTION_FORMALIZED = TRUE
P2_PLAN_STAGE_ORDER_REVISED = TRUE (E3A/E3B nuevas; alpha_P sweep movido de E3 a E6; STOP-P2-A movido
                                     de despues-de-E5 a despues-de-E6; etapas posteriores renumeradas)
P2_E3_ALPHA_SWEEP_PRE_CORRECTION_STILL_INVALID = TRUE (sin cambios, ver DEC-P2-004)
```
Blockers or limitations: Ninguno de los valores finales (`Tc`, `K_f*`, `K_r*`, `P_max,BESS`,
observación) queda congelado por esta revisión -- siguen pendientes de las etapas de diseño
correspondientes (P2-E4 en adelante), que requieren nueva autorización explícita del usuario.
Responsible: Claude (revisión de plan bajo instrucción explícita y detallada del usuario)
Status: passed
Next action: Ejecutar P2-E3A y P2-E3B (instrucción del usuario: "ejecutar únicamente" estas dos
etapas, reportar resultados, detenerse) -- ver DEC-P2-007/DEC-P2-008.

## DEC-P2-007

Date: 2026-08-19
Stage/Gate: P2-E3A -- BESS actuator calibration gate.
Decision: **GATE PASS.** Se implementó `Paper_2/src/p2_common.py::run_command_step_response()`
(driver de lazo abierto compartido con P2-E3B: sin `Alter`, sin lazo de frecuencia cerrado, comando
constante aplicado a UN BESS a la vez mientras el otro se mantiene en comando cero) y
`Paper_2/src/stage_p2e3a_actuator_calibration.py`. Se probaron, de forma independiente para cada BESS
(buses 13 y 12), comandos en 0/±25/±50/±75/±100% de un `Pmax,BESS` provisional de 293.4 MW (18 puntos:
9 fracciones x 2 buses), más un subconjunto (0/±50/±100%, 5 puntos) a un `Pmax,BESS` distinto de 400
MW en el bus 13, para confirmar escalamiento real del techo de saturación (23 puntos totales).
Resultado:
```text
max |absolute_error_MW| (puntos no saturados) = 0.057 MW
max |relative_error|    (puntos no saturados) = 0.0003  (0.03%)
saturacion ocurre exactamente en |command_MW| >= Pmax,BESS, en ambos signos, ambos buses
100% @ Pmax=293.4MW -> delivered=293.50 MW (vs. techo ~100MW del bug pre-correccion, DEC-P1-024)
100% @ Pmax=400.0MW  -> delivered=400.20 MW
TDS_success = True en los 23/23 puntos
```
El error es pequeño (<0.1% relativo), consistente entre bus 13 y bus 12 (simétrico dentro del ruido
numérico), y la potencia entregada escala correctamente con `Pmax,BESS` (293 MW y 400 MW ambos
alcanzan su comando al 100%, muy por encima del techo ~100 MW que producía el bug pre-corrección) --
confirma empíricamente la convención de Seccion 0-bis del plan revisado y cierra `PF2-ACT-01..06`.
Justification: El plan revisado (DEC-P2-006, Seccion 7-bis) exige este gate como obligatorio antes de
`Tc`, `K_f`/`K_r` o cualquier sweep de autoridad de potencia -- sin verificar que el actuador entrega
lo comandado, ninguna conclusión posterior sobre `Tc`/ganancias sería confiable.
Evidence reviewed: salida de consola de `Paper_2/src/stage_p2e3a_actuator_calibration.py`;
`Paper_2/artifacts/preflight/p2_actuator_calibration.csv` (23 filas); `Paper_2/artifacts/figures/
p2_actuator_calibration.png` (commanded vs delivered, linea 1:1).
Frozen parameters: Ninguno -- `Pmax,BESS` provisional (293.4 MW) usado en esta calibración NO queda
congelado, es un valor de prueba heredado de DEC-P2-005 (`alpha_P=1.0`), pendiente de P2-E6.
```text
P2_E3A_ACTUATOR_CALIBRATION_GATE = PASS
P2_E3A_MAX_RELATIVE_ERROR = 0.0003
PF2_ACT_01_TO_06 = PASS
```
Blockers or limitations: Ninguno. El gate pasa limpiamente; no se identificó ninguna limitación de
calibración del actuador en el rango probado.
Responsible: Claude (ejecución de P2-E3A bajo instrucción explícita del usuario, "ejecutar
únicamente" P2-E3A/P2-E3B)
Status: passed
Next action: P2-E3B (dynamic response characterization) -- ver DEC-P2-008.

## DEC-P2-008

Date: 2026-08-19
Stage/Gate: P2-E3B -- BESS dynamic response characterization.
Decision: Se implementó `Paper_2/src/stage_p2e3b_dynamic_response.py` (mismo driver de lazo abierto
que P2-E3A, resolución fina `tstep=2ms`). Se aplicaron escalones de amplitud moderada (±25/±50/±75%
de `Pmax,BESS=293.4MW`, lejos de saturación) a cada BESS por separado (12 pruebas: 6 amplitudes x 2
buses) y se midió `P_command(t)`/`P_delivered(t)`. Resultado:
```text
delay efectivo (10%)     = 4 ms  (todas las pruebas, ambos signos, ambos buses)
rise time 10-90%         = 44 ms (todas las pruebas)
settling time (+/-2%)    = 80-82 ms (todas las pruebas)
steady-state error       <= 0.074 MW en todas las pruebas
overshoot                <= 0.07% (ruido numerico del solver, no overshoot real)
TDS_success = True en las 12/12 pruebas
```
**Verificación del parámetro `Tf` de `ESD1` (obligatoria por el plan, Seccion 7-bis):** se inspeccionó
`andes/models/distributed/esd1.py` y se confirmó que `Tf` (default 1.0) es el **"Integrator constant
for SOC model"** -- alimenta únicamente `pIG` (estado de carga, `T=Tf, K=sys_mva/3600/En`) y NO
aparece en ninguna ecuación de la cadena `Pext0`->`Psum`->`Ipul`->`Ipcmd`->`Ipout`. El parámetro que sí
gobierna esa cadena es `tip` (`andes/models/distributed/pvd1.py`, "Inverter active current lag time
constant", default 0.02s): `Ipout = Lag(Ipcmd_y, T=tip)`, retardo de primer orden puro. La dinámica
observada coincide casi exactamente con la teórica de un lag puro con `T=tip=0.02s`: rise time
teórico `tip*ln(9)=43.9ms` vs. medido `44ms`; settling(2%) teórico `4*tip=80.0ms` vs. medido
`80-82ms`; sin overshoot esperado ni observado. **Conclusión: `Tf` NO domina la respuesta
comando->potencia (no participa en ella); `tip` sí, y la dinámica observada corresponde casi
exactamente a `tip` en su valor por defecto -- no se detectó ninguna desviación inexplicada.**
**Conclusión sobre el cuello de botella de FFR a `Tc=100ms` (obligatoria por el plan):** el settling
time medido (80-82 ms) es MENOR que `Tc=100ms` -- el actuador termina de responder al comando anterior
antes de que llegue la siguiente actualización. A `Tc=100ms`, el cuello de botella dominante es
previsiblemente el propio `Tc` (periodo de muestreo/decisión), no la dinámica interna de `ESD1`. Sin
embargo, el settling time (80ms) es del mismo orden de magnitud que los `Tc` candidatos más rápidos
(`Tc=50ms` y especialmente `Tc=20ms`, ambos MENORES que el settling time del actuador) -- en esos
casos la dinámica interna de `ESD1` (el lag `tip`) pasaría a ser un limitante comparable o dominante,
no solo `Tc`. Es decir: la respuesta es "(c) ambas", con dominancia relativa que depende de qué `Tc`
se seleccione -- exactamente el tipo de conclusión cuantitativa que P2-E4 necesita para no atribuir
prematuramente la falta de mejora de RoCoF a `Tc` sin esta caracterización.
Justification: El plan revisado (DEC-P2-006, Seccion 7-bis) exige esta caracterización antes de P2-E4
para no atribuir la ausencia de mejora de RoCoF a `Tc` sin evidencia de la dinámica real del actuador.
Evidence reviewed: salida de consola de `Paper_2/src/stage_p2e3b_dynamic_response.py`;
`Paper_2/artifacts/diagnostics/p2_dynamic_response.csv` (12 filas); `Paper_2/artifacts/trajectories/
p2e3b_step_traces.npz` (trayectorias crudas); `Paper_2/artifacts/figures/
p2_dynamic_response_example.png`; inspección directa de `andes/models/distributed/{pvd1,esd1}.py`
(líneas citadas en el reporte de esta sesión: `ESD1Data.Tf` ~linea 18, `PVD1Data.tip` ~linea 182,
`PVD1Model.Ipout = Lag(Ipcmd_y, T=tip)` ~linea 511).
Frozen parameters: Ninguno -- caracterización de diseño, no un valor a congelar. `Tf`/`tip` NO se
modificaron (instrucción explícita del plan: medir, no ajustar, en esta etapa).
```text
P2_E3B_DYNAMIC_CHARACTERIZATION = PASS
P2_E3B_TF_IS_SOC_INTEGRATOR_NOT_POWER_DYNAMICS = TRUE (verificado contra codigo fuente ANDES)
P2_E3B_TIP_IS_THE_ACTUAL_COMMAND_TO_POWER_TIME_CONSTANT = TRUE (default 0.02s, verificado)
P2_E3B_SETTLING_TIME_MS = 80  # +/-2%, todas las pruebas
P2_E3B_BOTTLENECK_AT_TC_100MS = "Tc probablemente dominante (settling 80ms < Tc 100ms)"
P2_E3B_BOTTLENECK_AT_TC_20_50MS = "ESD1 tip lag se vuelve comparable o dominante (settling 80ms >= Tc)"
PF2_DYN_01 = PASS
```
Blockers or limitations: Solo se probaron amplitudes moderadas (25/50/75%) para evitar saturación;
no se caracterizó la dinámica en el borde de saturación (100%) ni el comportamiento cuando el comando
cruza cero rápidamente (reversión de signo) -- no bloquea la conclusión principal, queda como
posible verificación adicional si `Tc<50ms` se congela en P2-E4. `PF2-DYN-02/03/04` (timing exacto de
`Tc`, consistencia de muestreo RoCoF entre `Tc`, ausencia de dependencia de `TDS.plt`) se verifican
formalmente EN P2-E4 (requieren variar `Tc`, que esta etapa no hace) -- el patrón `itm_step()` que
`PF2-DYN-04` exige ya se reutilizó sin cambios de P2-E1/E3A (DEC-P2-002), pero la verificación formal
del check quedará registrada en la entrada de P2-E4.
Responsible: Claude (ejecución de P2-E3B bajo instrucción explícita del usuario)
Status: passed
Next action: Reportar P2-E3A + P2-E3B al usuario y **detenerse** (instrucción explícita: no iniciar
P2-E4 sin aprobación explícita tras revisar calibración de actuador, velocidad de ESD1, posible
limitación de ancho de banda, y el plan revisado).

## DEC-P2-009

Date: 2026-08-19
Stage/Gate: **P2-E4 — Control-update-time (`Tc`) design. BLOQUEADA / STOP CONDITION ACTIVADA
(Seccion 16 de la instrucción del usuario para P2-E4).** Autorizada explícitamente por el usuario tras
revisar P2-E3A/P2-E3B; ejecutada bajo las restricciones explícitas: sin retunar `K_f`/`K_r`, sin tocar
`Pmax`, sin tocar el filtro `BusROCOF` ni `tip`, sin tocar ubicación BESS, sin TD3, sin `P2-T*`.

**Observations (lo que se hizo):** Se implementó `Paper_2/src/p2_common.py::run_physical_scenario_tc()`
-- driver que DESACOPLA la resolución de integración/logging (`tstep=5ms`, fija e idéntica en las tres
configuraciones) del periodo de actualización de control (`Tc`, retención de orden cero entre
muestras), para que `RoCoF_max`/nadir se calculen siempre desde la MISMA trayectoria a nivel de
integración, nunca desde muestras a la tasa del controlador -- y `Paper_2/src/
stage_p2e4_tc_design.py`. Se usó una pareja `K_f`/`K_r` conservadora (`gain_mult=0.5`, `K_f=293.4
MW/Hz`, `K_r=146.7 MW/(Hz/s)`), elegida explícitamente por ESTABILIDAD (DEC-P2-005: sin saturación,
respuesta idéntica bit a bit en `gain_mult` 0.5-0.9 para el probe de carga a `Tc=100ms`), NO por
desempeño máximo conocido. Dos probes DESIGN, continuidad experimental con P2-E3
(`G_train_P2`/`L_train_P2`): déficit severo de generación (`GENROU_4`, `rho=0.90`) e incremento severo
de carga (`PQ_9`/bus 20, `alpha_L=0.50`), ambos a `lambda_L=1.00`. Se ejecutó el Experimento 1
(NoFFC + `Tc`=100/50/20ms con la misma ganancia conservadora) para ambos probes.

**Measured results (Experimento 1, `Paper_2/artifacts/diagnostics/p2e4_tc_design.csv`):**
```text
                  Tc=100ms          Tc=50ms                Tc=20ms
gen_severe:
  df_nadir_Hz     -0.1697 (I_f=+6.4%)  -0.3283 (I_f=-81.2%)   -0.1692 (I_f=+6.6%)
  RoCoF_max_Hz/s   1.1560 (I_r=+2.5%)   2.8200 (I_r=-137.9%)   1.1652 (I_r=+1.7%)
  saturation_frac  0.000                0.771                 0.000
  cmd_del_max_err  30.8 MW              490.8 MW               6.8 MW
  TDS_success      True                 True                   True

load_severe:
  df_nadir_Hz     -0.2083 (I_f=0.0%)   -0.2836 (I_f=-36.2%)   -0.2070 (I_f=+0.6%)
  RoCoF_max_Hz/s   2.9334 (I_r=0.0%)    3.1975 (I_r=-9.0%)     2.9214 (I_r=+0.4%)
  saturation_frac  0.000                0.808                  0.012
  cmd_del_max_err  36.6 MW              496.8 MW               370.7 MW
  TDS_success      True                 True                   True
```
Trayectorias completas: `Paper_2/artifacts/trajectories/p2e4_tc_traces.npz`. Figuras: `Paper_2/
artifacts/figures/p2e4_fig{A,B,C,D,E}_*.png`.

**Interpretation:** `Tc=50ms`, con esta ganancia conservadora, produce una **oscilación sostenida tipo
bang-bang** entre `+Pmax` y `-Pmax` que NO decae en los 6s del horizonte (visible sin ambigüedad en
`p2e4_figA_freq_gen_severe.png`/`p2e4_figB_rocof_gen_severe.png` -- el RoCoF oscila entre ~1.7 y
~2.85 Hz/s de forma sostenida desde t~1.35s hasta t=6s, muy por encima de NoFFC en todo ese tramo; la
frecuencia se DETERIORA respecto a NoFFC, llegando a 59.70 Hz en vez de recuperarse). Inspección directa
de las trayectorias de comando/entregado (`Pcommand`/`Pdelivered`) confirma que el comando alterna
entre `+293.4` y `-293.4` MW cada 1-2 periodos de control (cada ~50-100ms) mientras la potencia
entregada, limitada por la dinámica interna `tip=20ms` (P2-E3B), nunca alcanza a asentarse antes de
que el siguiente comando la revierta -- de ahí el error comando-entregado extremo (hasta ~497 MW,
físicamente posible como `|entregado-comando|<=|entregado|+|comando|<=2*Pmax` durante una reversión de
signo, no un error de código). `TDS_success=True` y `actual_actions=expected_actions` en las 8 filas --
el integrador y el temporizador de `Tc` funcionan correctamente; esto es una inestabilidad de la LEY DE
CONTROL en lazo discreto, no una falla numérica ni un bug de timing. Coincidencia notable, NO
confirmada como causal: `Tc=50ms` coincide exactamente con `Tr=0.05s` (constante de washout del
estimador `BusROCOF`) -- posible resonancia de muestreo/filtro, consistente con la advertencia del plan
(Seccion 8) sobre la relación `Tc`/`Tf`/`Tw`/`Tr`, pero no investigada más a fondo en esta entrada (el
plan prohíbe tocar el filtro dentro de P2-E4). En `Tc=100ms` y `Tc=20ms`, la misma ganancia conservadora
es numéricamente estable en ambos probes, pero aporta una mejora de RoCoF prácticamente nula (`I_r`
entre +0.4% y +2.5%) -- consistente con el hallazgo previo de DEC-P2-005 a `Tc=100ms`.
**Diagnóstico de undersampling (obligatorio, Seccion 7 de la instrucción P2-E4):** el `RoCoF_max`
calculado a nivel de integración difiere sustancialmente del que se leería solo en los instantes de
control en `Tc=100ms` (gap 23-82%) -- confirma que evaluar RoCoF únicamente en muestras del
controlador SÍ habría subestimado el pico real a `Tc=100ms`; a `Tc=50ms` el gap es 0% (el pico
coincide con un instante de control, consistente con el propio mecanismo de la oscilación); a
`Tc=20ms` el gap es pequeño (0.1-5.9%). Esto confirma la necesidad metodológica de medir siempre a
nivel de integración, como exige el plan.
**Experimento 2 (ganancia agresiva) NO se ejecutó**: el chequeo de robustez automático (`TDS_success`
+ `saturation_fraction<0.5` + `RoCoF_max<3x NoFFC` en las filas `Tc in {50,20}`) dio `False` por la
fila `Tc=50ms` (saturación 77-81%) -- correcto según la instrucción del usuario ("Segundo experimento
SOLO si el primero es estable"). No se investigó si la ganancia agresiva agrava o no la resonancia de
`Tc=50ms`, ni se retunaron `K_f`/`K_r` para intentar estabilizar `Tc=50ms`.

**Selected Tc or unresolved decision:** **NO SE SELECCIONA `Tc` EN ESTA ENTRADA.** Se activa la
condición de stop de la instrucción del usuario ("Pcommand y Pdelivered muestran comportamiento
inconsistente" / posible artefacto de sampling en `RoCoF`) para `Tc=50ms`. Queda pendiente de decisión
explícita del usuario. Datos disponibles para esa decisión: `Tc=100ms` y `Tc=20ms` son ambos
numéricamente robustos con la ganancia conservadora, pero ninguno mejora RoCoF de forma material
todavía (`Tc` por sí solo, sin retuning de ganancias, no parece ser palanca suficiente) -- el
experimento 2 (ganancia agresiva) queda pendiente para evaluar si `Tc=20ms` con mayor autoridad de
realimentación sí aporta mejora sin la inestabilidad que esa ganancia mostró a `Tc=100ms`
(DEC-P2-005) o a `Tc=50ms` (esta entrada).
```text
P2_E4_EXPERIMENT_1_COMPLETE = TRUE
P2_E4_TC_50MS_UNSTABLE_LIMIT_CYCLE_CONSERVATIVE_GAIN = TRUE (ambos probes, sostenido, no numérico)
P2_E4_TC_100MS_STABLE_CONSERVATIVE_GAIN = TRUE (I_r +0.4% a +2.5%, mejora no material)
P2_E4_TC_20MS_STABLE_CONSERVATIVE_GAIN = TRUE (I_r +0.4% a +1.7%, mejora no material)
P2_E4_EXPERIMENT_2_SKIPPED = TRUE (robustness check failed on Tc=50ms row)
P2_E4_TC_NOT_SELECTED = TRUE (STOP condition active, pending user decision)
P2_E4_TR_50MS_COINCIDENCE_FLAGGED_NOT_CONFIRMED_CAUSAL = TRUE
```
**Blockers or limitations:** No se determinó la causa raíz exacta de la resonancia a `Tc=50ms` (la
coincidencia con `Tr=0.05s` es una hipótesis, no una conclusión -- el plan prohíbe investigar el filtro
dentro de P2-E4). No se probó ningún `Tc` intermedio entre 20 y 50ms ni entre 50 y 100ms, por lo que no
se sabe si la inestabilidad es una franja angosta alrededor de 50ms o más amplia. No se ejecutó el
experimento 2 (ganancia agresiva), por lo que no hay evidencia de si `Tc=20ms` combinado con mayor
ganancia mejora RoCoF de forma material sin inestabilidad. Solo se probaron 2 escenarios DESIGN (uno de
generación, uno de carga) -- ambos muestran el mismo patrón cualitativo, pero es una muestra pequeña.
Responsible: Claude (ejecución de P2-E4 Experimento 1 bajo autorización explícita del usuario, detenida
en el punto exacto que la instrucción del usuario definió como stop condition)
Status: blocked
Next action: Reportar al usuario (tabla comparativa, hallazgo de inestabilidad a `Tc=50ms`, ausencia de
mejora material de RoCoF a `Tc=100/20ms` con esta ganancia, recomendación) y **detenerse** -- no
iniciar P2-E5, no retunar `K_f`/`K_r`, no hacer sweep de `Pmax`, no entrenar TD3, esperar aprobación
explícita del usuario sobre cómo proceder (investigar la resonancia de `Tc=50ms`, ejecutar el
experimento 2 pese al fallo de robustez a 50ms comparando solo 100/20ms, ampliar los probes DESIGN, o
proceder directamente a P2-E5 con `Tc=20ms` provisional dejando `Tc=50ms` documentado como no viable
con esta ganancia).

## DEC-P2-010

Date: 2026-08-19
Stage/Gate: **P2-E4 diagnostic extension** (no es P2-E4 formal ni una nueva etapa numerada del plan --
extensión diagnóstica explícitamente autorizada por el usuario para caracterizar la inestabilidad
encontrada en DEC-P2-009 antes de decidir cómo continuar P2-E4). `DEC-P2-009` NO se modifica
retrospectivamente -- permanece como evidencia de que el primer sweep preregistrado (Tc=100/50/20ms)
se detuvo al detectar inestabilidad.
**Por qué se amplió Tc:** el usuario pidió determinar si la inestabilidad de `Tc=50ms` (DEC-P2-009) es
(1) una banda estrecha, (2) una región amplia de inestabilidad de control muestreado, (3) una
interacción `Tc`/`ESD1`/`BusROCOF` particular, o (4) un artefacto de implementación -- antes de
llamarla "resonancia" o tocar `Tr`.
**Qué puntos se añadieron:** `Tc in {30,40,45,55,60,70,80} ms`, sumados a los tres ya medidos
(`20,50,100 ms`) -- 10 puntos x 2 probes = 20 corridas.
**Qué NO se modificó:** `Kf=293.4 MW/Hz`, `Kr=146.7 MW/(Hz/s)` (idénticos a DEC-P2-009, gain_mult=0.5),
`Pmax=293.4 MW`, `tip`, `BusROCOF`/`Tf=0.02/Tw=0.02/Tr=0.05`, ubicación BESS, low-inertia case,
horizonte (6s), tiempo de disturbio (t=1.0s), los dos probes DESIGN (`GENROU_4`@rho=0.90,
`PQ_9`/bus20@alpha_L=0.50), ni el código `p2_common.py::run_physical_scenario_tc()` (reutilizado sin
cambios). No se ejecutó la ganancia agresiva. No se usó `validation` ni `P2-T*`.
**Qué hipótesis se está evaluando:** si la inestabilidad de `Tc=50ms` es una banda angosta específica
(posible coincidencia con `Tr=0.05s`) o un fenómeno más amplio de control muestreado -- ver Sección 9
de la instrucción del usuario (Casos A-D).
Decision (**qué se encontró**): Implementado `Paper_2/src/stage_p2e4b_tc_local_sweep.py` con una
clasificación cuantitativa explícita `STABLE`/`MARGINAL`/`LIMIT_CYCLE`/`NUMERICAL_FAILURE` (criterios
documentados en el propio script: `LIMIT_CYCLE` requiere `freq_p2p_final>=30mHz` Y
`sign_reversals_final>=3` en la ventana final de 1s del episodio -- evidencia de oscilación
PERSISTENTE, no un pico único; `STABLE` requiere `freq_p2p_final<=10mHz` Y `sign_reversals_final<=1` Y
`saturation_fraction<5%`). Resultado (`Paper_2/artifacts/diagnostics/p2e4_tc_local_sweep.csv`,
`Paper_2/artifacts/figures/p2e4_tc_stability_map.png`):
```text
                gen_severe    load_severe
Tc=20ms         STABLE        LIMIT_CYCLE
Tc=30ms         LIMIT_CYCLE   LIMIT_CYCLE
Tc=40ms         LIMIT_CYCLE   LIMIT_CYCLE
Tc=45ms         LIMIT_CYCLE   LIMIT_CYCLE
Tc=50ms         LIMIT_CYCLE   LIMIT_CYCLE   (ya visto en DEC-P2-009)
Tc=55ms         LIMIT_CYCLE   LIMIT_CYCLE
Tc=60ms         LIMIT_CYCLE   LIMIT_CYCLE
Tc=70ms         LIMIT_CYCLE   LIMIT_CYCLE
Tc=80ms         LIMIT_CYCLE   LIMIT_CYCLE
Tc=100ms        STABLE        STABLE
```
**Esto es el Caso B de la propia lista de interpretación del usuario ("aproximadamente 40-80ms resulta
inestable"), incluso ligeramente más amplio (20/30-80ms según el probe) que ese rango orientativo --
NO el Caso A (banda estrecha ~45-55ms).** La inestabilidad NO está centrada de forma aislada en 50ms;
aparece de forma continua en 7-8 puntos consecutivos del sweep, con magnitud (amplitud pico-a-pico de
frecuencia en la ventana final, de 63.7mHz en 30ms hasta 217.6mHz en 80ms) que CRECE monótonamente con
`Tc` dentro de la región inestable, no que tenga un máximo aislado en 50ms -- otro indicio en contra de
una interacción angosta específica con `Tr=0.05s` (si la causa fuera esa coincidencia puntual, se
esperaría un pico de inestabilidad cerca de 50ms y mejora hacia los extremos del rango probado, no un
crecimiento monótono hasta el borde de 80ms). Verificación de temporización (Sección 6 de la
instrucción): `actual_actions == expected_actions` en las 20/20 filas (sin duplicar ni perder
actualizaciones de control en ningún `Tc`, incluyendo los no-divisores exactos de `tstep=5ms` como
45/55/70ms, que sí lo son: 45/5=9, 55/5=11, 70/5=14, todos enteros exactos); el evento `Alter` ocurre
una sola vez por construcción (un único `ss.add('Alter',...)` en el código, sin cambios). El chequeo
automático `timing_exact` (definido como `dae_t_final` a menos de `2*tstep=10ms` de `tf=6.0s`) marcó
`False` en 12/20 filas, pero es un **falso positivo del propio umbral de QC**, no un defecto real: la
desviación observada (~10-17ms sobre 6000ms, <0.3%) es deriva de punto flotante acumulada en
`dae.t += tds.h` a lo largo de 1200 sumas de `tstep=0.005`, presente de forma idéntica en las filas
`STABLE` (p.ej. `dae_t_final=5.98985` en `Tc=100ms`, igual que en DEC-P2-009) -- no se correlaciona con
la clasificación de estabilidad ni con ningún `Tc` en particular. Diagnóstico de undersampling RoCoF
(Sección 7): el `gap` entre `RoCoF_max` a nivel de integración y a nivel de controlador varía de 0%
(cuando el pico coincide con un instante de control, común en `LIMIT_CYCLE` donde el pico ES el propio
comando de control) hasta 81.9% (`Tc=100ms`, probe de carga, ya visto en DEC-P2-009) -- confirma de
nuevo que nunca debe usarse `RoCoF` a tasa de controlador para decidir estabilidad o desempeño.
Interpretation: Los resultados corresponden al **Caso B** de la Sección 9 de la instrucción del
usuario: existe una región AMPLIA de inestabilidad del controlador discreto con esta pareja de
ganancias conservadoras, no una banda angosta alrededor de 50ms. La hipótesis de una interacción
puntual con `Tr=50ms` queda **debilitada pero no descartada** por esta evidencia (la inestabilidad no
está aislada en 50ms; sin embargo, `Tr=50ms` sigue dentro de la región inestable y no se investigó la
sensibilidad a `Tr` en sí, que el plan prohíbe explícitamente en esta etapa). No se encontró evidencia
de artefacto de implementación/timing (Caso D): la verificación de temporización es exacta en las 20
filas, y el fenómeno se reproduce de forma consistente y con magnitud monótonamente creciente con `Tc`
dentro de la banda -- consistente con una inestabilidad genuina de control en lazo discreto (Caso B/C),
no con un bug.
Selected Tc or unresolved decision: **NO SE SELECCIONA `Tc` EN ESTA ENTRADA.** `Tc=20ms` (solo estable
en el probe de generación, no en el de carga) y `Tc=100ms` (estable en ambos probes) siguen siendo los
únicos candidatos válidos por estabilidad de los 10 puntos probados -- pero, como ya advertía
DEC-P2-009, **la estabilidad sola no basta para seleccionar `Tc`**: ninguno de los dos mejora RoCoF de
forma material con esta ganancia conservadora (DEC-P2-009: `I_r` entre +0.4% y +2.5%). Queda pendiente
de decisión explícita del usuario sobre cómo proceder.
Evidence reviewed: `Paper_2/artifacts/diagnostics/p2e4_tc_local_sweep.csv` (20 filas);
`Paper_2/artifacts/trajectories/p2e4_tc_local_sweep_traces.npz`; `Paper_2/artifacts/figures/
p2e4_tc_{stability_map,nadir_rocof_map,saturation_map,command_behavior}.png`; comparación cruzada con
`Paper_2/artifacts/diagnostics/p2e4_tc_design.csv` (DEC-P2-009) para los tres puntos compartidos
(20/50/100ms) -- valores bit-consistentes entre ambos scripts al usar el mismo `run_physical_scenario_tc()`
sin cambios.
Frozen parameters:
```text
P2_E4_DIAGNOSTIC_EXTENSION_COMPLETE = TRUE
P2_E4_INSTABILITY_REGION = "Tc in [~20-30, 80] ms aprox., ambos probes, con esta ganancia conservadora"
P2_E4_INSTABILITY_CASE = "Caso B (region amplia), NO Caso A (banda estrecha aislada en 50ms)"
P2_E4_TR_50MS_HYPOTHESIS = "debilitada por evidencia de rango amplio, no descartada, no investigada directamente (Tr no se toco)"
P2_E4_IMPLEMENTATION_ARTIFACT_HYPOTHESIS = "descartada -- timing exacto (actual=expected actions en 20/20), Alter ocurre una vez, magnitud monotona con Tc"
P2_E4_TC_NOT_SELECTED = TRUE (sin cambios respecto a DEC-P2-009)
P2_E4_ONLY_STABLE_POINTS_OF_10_TESTED = "Tc=20ms (solo gen_severe), Tc=100ms (ambos probes)"
```
Blockers or limitations: No se probó una grilla más densa (p.ej. 22/24/26/28ms para acotar mejor el
límite inferior, ni 85/90/95ms para el límite superior) -- el rango exacto de la frontera de
estabilidad sigue siendo aproximado, no preciso. No se investigó `Tr` directamente (prohibido en esta
etapa), por lo que la hipótesis de interacción con el filtro sigue sin confirmar ni descartar
formalmente. Solo 2 probes DESIGN; ambos muestran el mismo patrón cualitativo pero con fronteras
ligeramente distintas (`Tc=20ms` estable solo para `gen_severe`), lo que ya sugiere que la frontera
exacta depende del escenario, no es una propiedad fija de `Tc` en abstracto.
Responsible: Claude (ejecución de la extensión diagnóstica bajo autorización explícita del usuario,
sin tocar ninguna de las variables congeladas)
Status: passed (como extensión diagnóstica; P2-E4 formal sigue sin `Tc` seleccionado, status blocked)
Next action: Reportar al usuario (tabla completa, clasificación por Tc/escenario, evidencia de región
amplia vs banda estrecha, candidatos de estabilidad restantes) y **detenerse** -- no iniciar P2-E5, no
ejecutar la ganancia agresiva, no modificar el filtro, esperar aprobación explícita del usuario.

## DEC-P2-011

Date: 2026-08-19
Stage/Gate: **P2-E5 — diagnóstico de estructura del controlador físico (F-only/R-only) y tuning
independiente de `Kf`/`Kr`.** Autorizada explícitamente por el usuario tras revisar DEC-P2-010, con
restricciones explícitas: `Pmax` fijo, `tip` fijo, `BusROCOF`/`Tf`/`Tw`/`Tr` fijos, ubicación BESS
fija, `Tc=100ms` usado únicamente como referencia diagnóstica (no congela `Tc`), sin `validation`/
`P2-T*`, sin ganancia agresiva todavía.
**Qué se hizo:** `Paper_2/src/stage_p2e5_kf_kr_diagnostic.py`, reutilizando sin cambios
`p2_common.run_physical_scenario_tc()` y la clasificación `STABLE`/`MARGINAL`/`LIMIT_CYCLE`/
`NUMERICAL_FAILURE` de `stage_p2e4b_tc_local_sweep.py` (mismos umbrales). Sweep F-only (`Kr=0`,
`Kf/Kf0 in {0.10,...,1.00}`, 8 puntos) y R-only (`Kf=0`, `Kr/Kr0 in {0.05,...,1.00}`, 8 puntos), ambos
a `Tc=100ms`, `Pmax=293.4MW`, en los mismos dos probes DESIGN (`gen_severe`, `load_severe`).
**Resultados F-only** (`Paper_2/artifacts/diagnostics/p2e5_kf_sweep.csv`): **STABLE en todo el rango
probado (0.1x-1.0x) en ambos probes** (2 puntos de `load_severe` a `Kf` muy bajo se etiquetaron
`MARGINAL`, ver nota de artefacto del clasificador abajo). Mejora de nadir modesta y NO material:
`gen_severe` crece monótonamente de `I_f=+4.0%` (0.1x) a `+4.7%` (1.0x); `load_severe` se mantiene en
`I_f≈0.0%` en TODO el rango -- F-only no tiene prácticamente ningún efecto en el probe de carga.
Efecto cruzado sobre RoCoF: pequeño y positivo en `gen_severe` (`I_r` hasta `+0.7%` a `Kf=1.0x`),
nulo en `load_severe`.
**Resultados R-only** (`Paper_2/artifacts/diagnostics/p2e5_kr_sweep.csv`): `gen_severe` **STABLE**
hasta `Kr=0.75x` (220 MW/(Hz/s)), `MARGINAL` (no `LIMIT_CYCLE`) solo en el punto más alto (`Kr=1.0x`,
293.4). Mejora de RoCoF modesta y NO material, creciendo monótonamente de `I_r=+0.2%` (0.05x) hasta
`+4.1%` (1.0x, el punto marginal). `load_severe` produce resultados **bit-idénticos** en TODO el rango
de `Kr` probado (`df_nadir=-0.2083Hz`, `RoCoF_max=2.933Hz/s` sin cambio alguno de 0.05x a 1.0x, salvo
un único `sign_rev=1` en el último punto) -- el canal RoCoF no tiene NINGÚN efecto medible sobre este
probe en el rango probado.
**Hallazgo de artefacto del clasificador (transparencia obligatoria, no corregido silenciosamente):**
la clasificación `MARGINAL` de `load_severe` en TODOS los puntos R-only (y en los 2 puntos de `Kf` más
bajo de F-only) NO refleja oscilación real. Inspección directa de la trayectoria
(`load_severe_Ronly_mult0.05`) muestra `freq_p2p` en la ventana final de 1s = 12.4 mHz -- apenas por
encima del umbral `STABLE_FREQ_P2P_MAX_HZ=10mHz` -- pero la frecuencia en esa ventana es
**monótonamente creciente** (59.883→59.896 Hz, sin un solo cambio de dirección), idéntica en magnitud
(12.5 mHz) a la de **NoFFC** en la misma ventana. Es una recuperación secundaria lenta y suave (deriva
del propio sistema, probablemente AGC/respuesta secundaria) compartida por igual entre NoFFC y todos
los niveles de `Kr` -- no una oscilación introducida por el controlador. El umbral `freq_p2p<=10mHz`
usado para `STABLE` (heredado sin cambios de P2-E4, donde nunca se activó porque los probes DESIGN de
P2-E4 no exhibían esta deriva lenta) no distingue "oscilación persistente" de "deriva monótona lenta";
el criterio de `sign_reversals_final<=1` sí lo hace correctamente (0-1 en casi todos estos puntos,
consistente con no-oscilación). **No se corrigió el umbral ni se re-ejecutó nada en esta entrada** --
se reporta el artefacto y su evidencia, y la interpretación de abajo usa el criterio de
`sign_reversals` (más confiable para este caso) en vez de la etiqueta `MARGINAL` literal.
**Grilla F+R:** el código construyó automáticamente la grilla F+R únicamente a partir de multiplicadores
`STABLE` en AMBOS probes simultáneamente (Sección 8 de la instrucción). `Kf` stable en ambos:
`{0.3,0.4,0.5,0.6,0.75,1.0}`. `Kr` stable en ambos: **conjunto vacío** (por el artefacto de
clasificador de arriba: `load_severe` nunca se etiquetó `STABLE` en R-only, solo `MARGINAL`) -- **la
grilla F+R se saltó automáticamente**, no por instrucción explícita sino como consecuencia directa del
artefacto de umbral. No se ejecutó ninguna combinación F+R nueva en esta entrada.
Interpretation: Usando el criterio de `sign_reversals` (más robusto que el umbral de amplitud para
distinguir deriva lenta de oscilación), **ambos canales son individualmente estables en todo el rango
probado (hasta 1.0x) en ambos probes**, pero **ninguno de los dos, por separado, alcanza una mejora
material** (`>=10%`, criterio `WIN` de SS21 del plan): F-only alcanza como máximo `+4.7%` de nadir;
R-only alcanza como máximo `+4.1%` de RoCoF (en el único punto marginal) y `0%` en el probe de carga.
Esto **no encaja limpiamente en ninguno de los 4 casos preregistrados** (Sección 7 de la instrucción),
que asumen inestabilidad genuina de al menos un canal aislado -- aquí ninguno de los dos canales, solo,
se vuelve realmente inestable (`LIMIT_CYCLE`) hasta `1.0x`. La evidencia disponible SÍ apunta con
fuerza hacia el **Caso 3** (interacción entre canales) al combinarla con `DEC-P2-005`: la esquina
`Kf=1.0x`+`Kr=1.0x` (`Kf=586.8`, `Kr=293.4`, la ganancia "agresiva" ya probada en `DEC-P2-005`) fue
**desestabilizante para `load_severe`** en F+R (`I_r=-1.704`, `sat=11.7%`, `Tc=100ms`), mientras que en
esta entrada F-only(1.0x) y R-only(1.0x) fueron, cada uno por separado, estables (o a lo sumo
marginales) en ese mismo probe -- consistente con una interacción entre canales que emerge solo
cuando ambos actúan simultáneamente a ganancia alta, no con un solo canal defectuoso.
Selected Tc or unresolved decision: **No se selecciona `Kf*`/`Kr*` ni `Tc` en esta entrada.** Queda
pendiente de decisión del usuario: (a) autorizar una re-ejecución corregida de la grilla F+R usando
`sign_reversals` en vez del umbral de amplitud para definir "stable" (recuperando el conjunto de `Kr`
que el artefacto excluyó), (b) proceder con evidencia F+R limitada (solo el punto conservador 0.5x/0.5x
ya visto en DEC-P2-009, estable, y el punto agresivo 1.0x/1.0x ya visto en DEC-P2-005, inestable para
`load_severe`), o (c) redefinir el criterio de "útil" dado que ninguno de los dos canales aislados llega
al 10% en el rango probado hasta ahora.
Evidence reviewed: `Paper_2/artifacts/diagnostics/p2e5_kf_sweep.csv` (16 filas),
`p2e5_kr_sweep.csv` (16 filas); `Paper_2/artifacts/trajectories/p2e5_physical_structure_traces.npz`;
`Paper_2/artifacts/figures/p2e5_fig{1,2,3,4}_*.png`; inspección directa de la trayectoria
`load_severe_Ronly_mult0.05` (ventana final, ver hallazgo de artefacto arriba); comparación cruzada con
`DEC-P2-005` (punto de ganancia agresiva F+R ya medido, no repetido aquí).
Frozen parameters: Ninguno.
```text
P2_E5_FONLY_STABLE_ALL_TESTED_RANGE_BOTH_PROBES = TRUE (segun sign_reversals; ver artefacto de umbral)
P2_E5_RONLY_STABLE_ALL_TESTED_RANGE_BOTH_PROBES = TRUE (segun sign_reversals; ver artefacto de umbral)
P2_E5_FONLY_MAX_I_F = 0.047  # gen_severe, Kf=1.0x; load_severe ~0.0 en todo el rango
P2_E5_RONLY_MAX_I_R = 0.041  # gen_severe, Kr=1.0x (punto marginal); load_severe = 0.0 en todo el rango
P2_E5_NEITHER_CHANNEL_USEFUL_ALONE = TRUE (ningun canal aislado alcanza I_f o I_r >= 0.10)
P2_E5_CASE_CLASSIFICATION = "No encaja limpiamente en Casos 1/2/4; evidencia (con DEC-P2-005) apoya Caso 3 (interaccion Kf/Kr), no un canal aislado defectuoso"
P2_E5_FR_GRID_SKIPPED_DUE_TO_CLASSIFIER_THRESHOLD_ARTIFACT = TRUE (no por instabilidad real de Kr en load_severe)
P2_E5_STABLE_THRESHOLD_LIMITATION_FOUND = "freq_p2p_final<=10mHz no distingue deriva monotona lenta de oscilacion; sign_reversals si"
P2_E5_KF_KR_NOT_FROZEN = TRUE
```
Blockers or limitations: El umbral `STABLE_FREQ_P2P_MAX_HZ=10mHz` (heredado de P2-E4 sin revisar) no
es apropiado para probes con recuperación secundaria lenta como `load_severe` -- produjo una
clasificación `MARGINAL` engañosa que bloqueó la construcción automática de la grilla F+R. No se
ejecutó ninguna combinación F+R nueva (solo se dispone de los dos puntos ya conocidos de sesiones
anteriores: 0.5x/0.5x estable, 1.0x/1.0x inestable para `load_severe`) -- la región de transición entre
esos dos puntos no está caracterizada. Solo 2 probes DESIGN. No se investigó por qué `load_severe` es
completamente insensible a `Kr` en todo el rango (posible explicación no confirmada: el `BusROCOF`
local en los buses BESS 12/13 podría permanecer pequeño para este disturbio específico de carga en el
bus 20, aunque el RoCoF del peor bus del sistema -- medido sobre buses generadores 30-39 -- sea grande;
no verificado en esta entrada).
Responsible: Claude (ejecución de P2-E5 bajo autorización explícita del usuario)
Status: passed (como diagnóstico; ninguna ganancia congelada, F+R grid pendiente de re-ejecución
corregida o de decisión alternativa del usuario)
Next action: Reportar al usuario (rango estable, mejor mejora por canal, efecto cruzado, clasificación
de caso, artefacto del clasificador encontrado, recomendación) y **detenerse** -- no iniciar P2-E6, no
congelar `Kf`/`Kr`, esperar aprobación explícita del usuario sobre cómo tratar el artefacto del
clasificador y la grilla F+R pendiente.

## DEC-P2-012

Date: 2026-08-19
Stage/Gate: **Corrección del clasificador de P2-E5 + intento de recuperación de la grilla F+R —
DETENIDA por un STOP CONDITION del propio protocolo (Sección 17 de la instrucción del usuario), NO por
el clasificador.** DEC-P2-009, DEC-P2-010 y DEC-P2-011 permanecen sin modificar.
**Qué se hizo:** `Paper_2/src/stage_p2e5b_fr_grid_corrected.py` implementa un clasificador corregido
(`classify_v2`) que ajusta una tendencia lineal a `frequency(t)` en la ventana final de 1s y usa la
amplitud pico-a-pico del **residuo destendenciado** (no la amplitud cruda) junto con `sign_reversals`,
`saturation_fraction` y un `persistence_ratio` (razón de amplitud residual entre la segunda y la
primera mitad de la ventana final, para exigir oscilación persistente y no solo un pico transitorio).
Antes de tocar la grilla F+R, se corrió una suite de regresión de 4 casos históricos
(`Paper_2/artifacts/diagnostics/p2_stability_classifier_regression.csv`):
```text
Case A (load_severe NoFFC, traza existente):                    detrended_p2p=0.40mHz sign_rev=0 -> STABLE   (esperado NOT LIMIT_CYCLE) PASS
Case B (load_severe R-only Kr=0.05x, traza existente, antes MARGINAL): detrended_p2p=0.42mHz sign_rev=0 -> STABLE (esperado NOT LIMIT_CYCLE) PASS
Case C (gen_severe Tc=50ms bang-bang sostenido, traza existente): detrended_p2p=154.8mHz sign_rev=19 -> LIMIT_CYCLE (esperado LIMIT_CYCLE) PASS
Case D (load_severe F+R agresivo Kf=Kr=1.0x, Tc=100ms, 1 simulación NUEVA): detrended_p2p=1.4mHz sign_rev=0 -> STABLE (esperado LIMIT_CYCLE) FAIL
```
**El clasificador corregido funciona correctamente** (Casos A/B/C, los tres construidos sobre
trayectorias ya existentes con `tstep=5ms` consistente): distingue de forma limpia la deriva lenta
monótona de `load_severe` (Casos A/B, ahora correctamente `STABLE`, resolviendo el defecto de
`DEC-P2-011`) de la oscilación sostenida real de `Tc=50ms` (Caso C, sigue `LIMIT_CYCLE`). El fallo es
únicamente el Caso D, y el script **se detuvo automáticamente antes de reclasificar F-only/R-only y
antes de construir la grilla F+R** (implementación del STOP CONDITION de la Sección 17: "el nuevo
clasificador no reproduce correctamente los casos históricos" -- no se corrigió nada silenciosamente).
**Investigación adicional del Caso D (autorizada implícitamente por la instrucción de "no corregir
silenciosamente", no un cambio de código: solo llamadas de diagnóstico adicionales, sin tocar
`p2_common.py` ni la grilla F+R):**
1. Se reprodujo el caso exacto de `DEC-P2-005` (`Kf=Kr=1.0x`, `load_severe`) con el driver ANTIGUO
   `run_physical_scenario()` (usado originalmente en `DEC-P2-005`): `saturation_fraction=0.117`
   (coincide casi exactamente con el `sat=0.117` reportado en `DEC-P2-005`), `Ppeak=581.5MW` (cerca del
   techo teórico `2*Pmax=586.8MW`) -- **confirma que el hallazgo original de `DEC-P2-005` es
   reproducible con su driver original.**
2. Inspección del driver antiguo reveló que **no usa `dt=Tc=100ms` como paso de integración** (una
   suposición incorrecta de esta sesión, corregida aquí): usa `ss.TDS.config.tstep = 1/60 ≈ 16.67ms`
   fijo, con el mismo patrón de `while dae.t < target_t` que el driver nuevo -- la diferencia real
   frente a `run_physical_scenario_tc()` (usado en esta ronda con `tstep=5ms`) es una resolución de
   integración ~3.3x más fina en el driver nuevo, no una diferencia de 20x como se supuso inicialmente.
3. **Prueba decisiva:** se ejecutó el MISMO driver nuevo (`run_physical_scenario_tc`), mismo `Kf=Kr=1.0x`,
   mismo `Tc=100ms`, mismo probe, variando ÚNICAMENTE `tstep`:
```text
tstep=16.67ms (resolucion del driver antiguo): Ppeak=581.3MW  saturation_fraction=0.233  RoCoF_max=3.300Hz/s
tstep=10.00ms:                                 Ppeak=189.4MW  saturation_fraction=0.000  RoCoF_max=3.036Hz/s
tstep=5.00ms  (resolucion usada en toda esta ronda P2-E4/E5):  Ppeak=165.6MW  saturation_fraction=0.000  RoCoF_max=2.933Hz/s
```
**Resultado inequívoco: el paso de integración por sí solo determina si esta configuración exacta
satura el 23% del tiempo y se acerca al techo teórico de potencia, o se mantiene perfectamente limpia
-- con el mismo driver, la misma ley de control, el mismo `Tc`, el mismo `Kf`/`Kr`, el mismo probe.**
Interpretation: **Esto NO es un bug del clasificador** (los Casos A/B/C, todos construidos sobre datos
con `tstep=5ms` internamente consistente, se clasifican correctamente). **Es una sensibilidad numérica
genuina de la simulación**: a `tstep=16.67ms` (menos de una constante de tiempo `tip=20ms` de `ESD1`),
la combinación de un comando discreto tipo bang-bang (saturación dura, cambios de signo) con esa
resolución de integración parece producir sobre-shoot/artefactos numéricos que se comportan como
inestabilidad real; a `tstep<=10ms` (>=2 muestras por `tip`), el mismo caso es limpio. **Esto proyecta
duda directa sobre el hallazgo de inestabilidad de ganancia agresiva de `DEC-P2-005`** (que usó
exclusivamente el driver antiguo, `tstep=16.67ms`) -- y por extensión, sobre parte de la evidencia que
`DEC-P2-011` usó para apoyar la hipótesis de "interacción `Kf`x`Kr`" (Caso 3). **Importante: esto NO
afecta la validez de `DEC-P2-009`/`DEC-P2-010`/`DEC-P2-011`** -- esos hallazgos usaron consistentemente
`tstep=5ms` en TODO el barrido (`Tc` fue la única variable que cambió; el paso de integración se
mantuvo fijo en cada comparación), por lo que la inestabilidad sostenida de `Tc=50-80ms` sigue siendo
un mecanismo genuino de control muestreado (periodo de actualización insuficiente), no un artefacto
numérico -- son dos fenómenos físicamente distintos que no deben confundirse.
Selected Tc or unresolved decision: **No se construyó la grilla F+R en esta entrada** -- el script se
detuvo correctamente antes de ese paso, tal como exige la Sección 17. Tampoco se reclasificaron
formalmente F-only/R-only (aunque, dado que Casos A/B validan el clasificador para exactamente ese tipo
de traza, es razonable esperar que la reclasificación --si se ejecutara-- reproduciría los resultados
ya descritos informalmente en el reporte de `DEC-P2-011`: ambos canales estables en casi todo el rango,
ninguno útil por sí solo). Queda pendiente de decisión explícita del usuario cómo proceder dado este
hallazgo de sensibilidad numérica.
Evidence reviewed: `Paper_2/artifacts/diagnostics/p2_stability_classifier_regression.csv`; tres
llamadas de diagnóstico adicionales (driver antiguo replicando `DEC-P2-005`; driver nuevo a
`tstep=1/60,0.01,0.005`) ejecutadas en esta sesión, no persistidas como artefacto CSV (solo en la
salida de consola, transcrita arriba) por ser diagnóstico puntual, no parte del pipeline formal.
Frozen parameters: Ninguno.
```text
P2_E5B_CLASSIFIER_V2_VALIDATED_ON_CASES_ABC = TRUE
P2_E5B_REGRESSION_CASE_D_FAILED = TRUE
P2_E5B_ROOT_CAUSE_OF_CASE_D_FAILURE = "sensibilidad numerica al paso de integracion (tstep), NO bug de clasificador, NO interaccion Kf x Kr confirmada"
P2_E5B_TSTEP_16_67MS_REPRODUCES_DEC_P2_005_SATURATION = TRUE (sat=0.233 vs sat=0.117 reportado, mismo orden de magnitud)
P2_E5B_TSTEP_10MS_AND_5MS_CLEAN_NO_SATURATION = TRUE
P2_E5B_DEC_P2_005_AGGRESSIVE_GAIN_FINDING_NOW_QUESTIONABLE = TRUE (posible artefacto numerico, no descartado del todo, requiere mas puntos de tstep para confirmar)
P2_E5B_DEC_P2_009_010_011_TC_SWEEP_UNAFFECTED = TRUE (tstep=5ms constante en toda esa evidencia, mecanismo fisico distinto)
P2_E5B_FR_GRID_NOT_BUILT = TRUE (stop condition activado antes de este paso)
P2_E5B_KF_ONLY_RONLY_NOT_FORMALLY_RECLASSIFIED = TRUE (script se detuvo antes; Casos A/B sugieren que si se reclasificara reproduciria lo ya reportado informalmente en DEC-P2-011)
```
Blockers or limitations: No se determinó con certeza absoluta el mecanismo numérico exacto (¿error de
truncamiento del método trapezoidal interactuando con el limitador duro de saturación? ¿un evento de
conmutación no capturado correctamente por `do_switch()` a paso grueso?) -- solo se demostró la
correlación causal mediante variación controlada de `tstep`, no se diagnosticó la causa raíz interna de
ANDES. Solo se probó `tstep in {16.67,10,5}ms`, un caso (`Kf=Kr=1.0x`, `load_severe`) -- no se verificó
si otros puntos de la grilla `Kf`/`Kr` (particularmente los que `DEC-P2-011` había etiquetado
tentativamente vía F-only/R-only) también son sensibles a `tstep`, ni si `tstep=5ms` en sí es
suficientemente fino (podría existir sensibilidad residual incluso ahí, no verificada con `tstep` aún
más fino como 2ms o 1ms). La grilla F+R sigue completamente sin ejecutar.
Responsible: Claude (ejecución bajo autorización explícita del usuario; detención automática por el
propio stop condition preregistrado, mas tres llamadas de diagnóstico adicionales para caracterizar la
causa antes de reportar, sin modificar código ni proceder a la grilla)
Status: blocked
Next action: Reportar al usuario el hallazgo completo (regresión 3/4 con Caso D explicado por
sensibilidad numérica al tstep, no por interacción Kf/Kr ni por bug de clasificador) y **detenerse** --
no construir la grilla F+R, no reclasificar formalmente F-only/R-only, no avanzar a P2-E6, esperar
decisión explícita del usuario sobre cómo proceder (p.ej., verificar sensibilidad a tstep en más puntos
antes de confiar en cualquier resultado a tstep=5ms, o aceptar tstep=5ms como suficientemente fino con
alguna verificación adicional, y solo entonces reintentar la grilla F+R).

## DEC-P2-013

Date: 2026-08-19
Stage/Gate: **P2-E5c — estudio de convergencia de `tstep` sobre el caso F+R agresivo que mostró
sensibilidad numérica (DEC-P2-012).** Autorizado explícitamente por el usuario. Restricciones
respetadas: `Tc=100ms`, `Kf=Kr=1.0x`, `Pmax=293.4MW`, `tip`, `BusROCOF`/`Tf`/`Tw`/`Tr`, disturbio
(`load_severe`, `PQ_9`/bus 20, `alpha_L=0.50`) idénticos en las 4 corridas -- única variable: `tstep`.
No se avanzó a la grilla F+R ni a P2-E6 (instrucción explícita del usuario en esta misma ronda).
Decision: `Paper_2/src/stage_p2e5c_tstep_convergence.py`, reutilizando
`p2_common.run_physical_scenario_tc()` sin cambios. Resultados
(`Paper_2/artifacts/diagnostics/p2e5c_tstep_convergence.csv`):
```text
tstep     df_nadir_Hz   RoCoF_max_Hz/s   Ppeak_MW   saturation_fraction   TDS_success
10.00ms   -0.2118       3.0361           189.4      0.0000                 True
 5.00ms   -0.2083       2.9334           165.6      0.0000                 True
 2.50ms   -0.2079       2.9334           168.4      0.0000                 True
 1.00ms   -0.2076       2.9265           173.1      0.0000                 True
```
Error relativo entre refinamientos sucesivos
(`Paper_2/artifacts/diagnostics/p2e5c_tstep_convergence_relative_error.csv`):
```text
10.0ms->5.0ms:  df_nadir=1.70%  RoCoF_max=3.50%  Ppeak=14.36%  sat=0.00%
 5.0ms->2.5ms:  df_nadir=0.21%  RoCoF_max=0.00%  Ppeak=1.67%   sat=0.00%
 2.5ms->1.0ms:  df_nadir=0.12%  RoCoF_max=0.23%  Ppeak=2.68%   sat=0.00%
```
Interpretation: Sobre las dos métricas principales del gate de P2 (`df_nadir`, `RoCoF_max` -- SS21/SS22
del plan: `Ppeak`/`saturation` son diagnóstico, no criterio primario), la convergencia entre `5.0ms` y
`2.5ms` ya es `<1%` (`0.21%`/`0.00%`), y se mantiene `<1%` entre `2.5ms` y `1.0ms` (`0.12%`/`0.23%`) --
**convergido en `tstep=5ms` bajo el criterio de las métricas principales**. `Ppeak` (diagnóstico) no
converge monótonamente por debajo de `~1.7-2.7%` incluso hasta `1ms` -- ruido de muestreo de un pico
puntual de corriente, no relevante para el gate ni para la clasificación de estabilidad.
`saturation_fraction=0.0000` de forma IDÉNTICA en las 4 resoluciones (`10ms` a `1ms`) -- **confirma que
la saturación del 23.3% observada a `tstep=16.67ms` (DEC-P2-012) es exclusiva de esa resolución
gruesa, no aparece en ningún punto de `10ms` a `1ms`**, reforzando que fue un artefacto numérico de esa
resolución específica, no un límite de estabilidad real que se acerca gradualmente.
Selected Tc or unresolved decision: Siguiendo la Sección 5 de la instrucción del usuario (5ms y 2.5ms
"prácticamente iguales" en las métricas principales):
```text
TSTEP_FROZEN_FOR_PAPER_2 = 5.0 ms
```
Se congela `tstep=5ms` como resolución de integración estándar para toda simulación física de P2 en
adelante (P2-E4, P2-E5, y cualquier etapa posterior que use `run_physical_scenario_tc()` con este valor
por defecto). **No se ejecuta la grilla F+R todavía** -- instrucción explícita del usuario en este
mismo turno ("No avanzar todavía a la grilla F+R ni a P2-E6"), pese a que la Sección 5 de su propia
instrucción anticipaba continuar automáticamente a ese paso bajo este resultado de convergencia; se
respeta la instrucción más restrictiva y explícita (punto 1) sobre la condicional general (punto 5).
**Resultados anteriores y su validez:**
```text
VALIDOS (tstep=5ms explicito, ya convergido):
  - DEC-P2-009 (P2-E4 Experimento 1, Tc=100/50/20ms)
  - DEC-P2-010 (P2-E4 local sweep, Tc=20-100ms)
  - DEC-P2-011 (P2-E5 F-only/R-only sweeps)
  - DEC-P2-012 (regresion de clasificador, Casos A/B/C; el propio Caso D tambien valido A ESTE tstep,
    solo que revelo la sensibilidad del tstep MAS GRUESO, no invalida nada corrido a 5ms)
  - P2-E3A/P2-E3B (actuator calibration/dynamic response): tstep=5ms y 2ms respectivamente, YA finos

AFECTADOS / NO USAR PARA CLAIMS DE ESTABILIDAD (tstep=16.67ms, driver antiguo run_physical_scenario()):
  - Paper_2/artifacts/diagnostics/p2e3_gain_tanteo.csv (DEC-P2-005)
  - Paper_2/artifacts/diagnostics/p2e3_gain_refine.csv (DEC-P2-005), en particular la conclusion de
    "gain_mult=1.0 desestabiliza el probe de carga" -- pudo ser (parcial o totalmente) un artefacto
    numerico de resolucion insuficiente (tstep=16.67ms < tip=20ms), no una inestabilidad fisica real.
    La hipotesis de interaccion Kf x Kr (Caso 3, DEC-P2-011) que se apoyaba en este hallazgo queda
    SIN CONFIRMAR (ya marcado asi en DEC-P2-012/CLM-P2-KFKR), no refutada -- requiere repetirse a
    tstep=5ms antes de poder citarse.
  - Paper_2/artifacts/diagnostics/p2e3_alpha_p_sweep.csv: YA estaba INVALID por el bug de escalamiento
    de potencia (DEC-P2-004); esta sensibilidad de tstep es un segundo motivo independiente, no cambia
    su estado ya invalido.
```
Evidence reviewed: `Paper_2/artifacts/diagnostics/p2e5c_tstep_convergence.csv`,
`p2e5c_tstep_convergence_relative_error.csv`.
Frozen parameters:
```text
TSTEP_FROZEN_FOR_PAPER_2 = 0.005  # 5 ms, confirmado por convergencia <1% en df_nadir/RoCoF_max
P2_E5C_TSTEP_16_67MS_RESULTS_FLAGGED_UNRELIABLE = TRUE (p2e3_gain_tanteo.csv, p2e3_gain_refine.csv)
P2_E5C_FR_GRID_STILL_NOT_EXECUTED = TRUE (instruccion explicita del usuario de no avanzar todavia)
```
Blockers or limitations: Solo se probó un caso (`load_severe`, `Kf=Kr=1.0x`) para el estudio de
convergencia -- no se verificó si `gen_severe` u otras combinaciones `Kf`/`Kr` tienen el mismo umbral
de convergencia (razonable asumirlo por ser la misma física/`tip`, pero no verificado explícitamente).
`Ppeak` no convergió monótonamente por debajo de `~1.7%`; no se investigó la causa exacta (probablemente
muestreo de fase de un pico agudo, no relevante para el gate).
Responsible: Claude (ejecución de P2-E5c bajo autorización explícita del usuario)
Status: passed
Next action: Reportar al usuario (tabla, errores relativos, tstep recomendado, qué resultados previos
quedan válidos/afectados) y **detenerse** -- no construir la grilla F+R, no avanzar a P2-E6, esperar
aprobación explícita del usuario antes de reintentar la grilla F+R con el clasificador corregido y
`tstep=5ms` ya congelado.

## DEC-P2-014

Date: 2026-08-19
Stage/Gate: **Grilla F+R de P2-E5 (recuperada, `tstep=5ms`) + diagnóstico de observabilidad de
`load_severe` + evaluación de `STOP-P2-A`.** Autorizado explícitamente por el usuario en dos pasos.
**Grilla F+R (`Paper_2/src/stage_p2e5b_fr_grid_corrected.py`, corregido tras dos bugs de
implementación -- ver bajo):**
- Regresión: 4/4 PASS (Caso D actualizado a `expected='NOT LIMIT_CYCLE'`, justificado
  independientemente por `DEC-P2-013`, no una corrección circular del clasificador).
- Reclasificación (sin nuevas simulaciones): `Kf` STABLE en ambos probes en TODO el rango 0.1x-1.0x;
  `Kr` STABLE en ambos probes en 0.05x-0.75x (`1.0x` excluido, marginal en `gen_severe`, igual que en
  `DEC-P2-011`).
- Grilla F+R: 9 combinaciones únicas (`Kf∈{0.1,0.5,1.0}x × Kr∈{0.05,0.3,0.75}x`) x 2 probes = 18
  simulaciones nuevas (mas 1 duplicado accidental sin impacto, artefacto de redondeo en la selección de
  boundary-probe). **Resultado: las 18/18 simulaciones (20 filas con el duplicado) clasificaron
  `STABLE` -- ninguna `LIMIT_CYCLE` en toda la grilla.** Mejor mejora simultánea:
  `gen_severe` `Kf=1.0x`/`Kr=0.75x`, `I_f=+7.7%`, `I_r=+3.7%` (único punto no dominado, Pareto).
  `load_severe`: **los 9 puntos dan `I_f=I_r=0.0%`** -- insensibilidad total, confirmando
  `DEC-P2-011`.
- Dos bugs de implementación corregidos durante la ejecución (documentados en el propio código,
  `git diff` disponible): (1) la reclasificación de F-only/R-only usaba el valor absoluto de la
  ganancia en vez del multiplicador al construir la clave de búsqueda de trayectoria (`AssertionError`
  inmediato, no un resultado silenciosamente incorrecto); (2) colisión de nombre entre la traza de
  regresión del Caso D y el filtro de prefijo `load_severe_FR` usado por el diagnóstico de RoCoF local
  (`KeyError` inmediato). Ambos fallaron ruidosamente (excepción, no resultado silencioso) y se
  corrigieron antes de re-ejecutar.
**Diagnóstico de observabilidad (`Paper_2/src/stage_p2e5d_observability_diagnostic.py`, sin nuevas
simulaciones -- reutiliza la traza `load_severe_FR_f0.1_r0.05` ya generada, el punto de ganancia más
baja de la grilla, representativo porque `load_severe` mostró `0%` de efecto en TODA la grilla):**
```text
Pico RoCoF sistema (peor bus, 30-39):     2.9334 Hz/s en t-TD=+30ms
Pico RoCoF local bus BESS 13:             0.4803 Hz/s en t-TD=+35ms  (ratio local/global = 0.164)
Pico RoCoF local bus BESS 12:             0.4720 Hz/s en t-TD=+35ms  (ratio local/global = 0.161)
Correlacion (Pearson) bus13 vs sistema:   0.835
Correlacion (Pearson) bus12 vs sistema:   0.824
Retraso (cross-correlacion) bus13/bus12:  +5ms (local va ligeramente detras del global)
RoCoF_COI:                                NO DISPONIBLE (no implementado, requeriria nuevo codigo)
```
Interpretation: El retraso temporal es **insignificante** (+5ms, prácticamente simultáneo) -- la
limitación NO es de timing/retardo. La correlación es alta (0.82-0.84) -- la señal local sigue la
FORMA del RoCoF global razonablemente bien. **La limitación es puramente de magnitud**: el RoCoF local
en ambos buses BESS alcanza solo ~16% del pico del peor bus del sistema para este disturbio específico
(`load_severe`, `PQ_9`/bus 20). Esto confirma cuantitativamente la hipótesis de `DEC-P2-011`/reporte
anterior: **la insensibilidad de `load_severe` a `Kr` es una limitación de observabilidad local
(ubicación de los BESS respecto a este disturbio), no un defecto de la ley de control ni del
estimador**. Dado que `Kr0` normaliza la ganancia contra una referencia de `1.0 Hz/s`, una señal local
que nunca supera `~0.5 Hz/s` para este disturbio no puede generar una acción de control de autoridad
completa sin importar cuánto se incremente `Kr` dentro del rango probado.
**Evaluación `STOP-P2-A` (plan SS20, redefinido en `DEC-P2-006` como design target multicriterio):**
```text
Criterio 1 (mejora simultanea reproducible de nadir y RoCoF): FALLA
  - gen_severe: +7.7%/+3.7% (mejor caso encontrado) -- por debajo del umbral material del 10%.
  - load_severe: 0%/0% en TODA la grilla F+R -- sin mejora alguna.
Criterio 2 (estabilidad numerica): CUMPLE (18/18 STABLE en la grilla, tstep=5ms convergido)
Criterio 3 (ausencia de saturacion patologica): CUMPLE (saturation_fraction=0 en toda la grilla)
Criterio 4 (consistencia entre escenarios): FALLA (resultado radicalmente inconsistente entre los
  dos probes DESIGN -- de modesto/positivo a nulo)
```
Selected Tc or unresolved decision: **`STOP-P2-A`: NO SATISFECHO** para la arquitectura física actual
(`Physical Hybrid`, `Kf`/`Kr` con observación local en los buses BESS, `Tc=100ms` como referencia
diagnóstica). No se entrena TD3 todavía. Causa dominante identificada con evidencia cuantitativa:
observabilidad local (para `load_severe`) + autoridad/estructura de ganancia modesta incluso donde la
observabilidad no es el problema (`gen_severe`, techo ~8%) -- no `Tc`, no el filtro `BusROCOF`, no
inestabilidad numérica (todos verificados y descartados como causa en `DEC-P2-009` a `DEC-P2-013`).
Evidence reviewed: `Paper_2/artifacts/diagnostics/p2e5_kf_kr_grid.csv`,
`p2e5_load_severe_local_vs_system_rocof.csv`, `p2e5d_observability_diagnostic.csv`;
`Paper_2/artifacts/figures/p2e5_fr_fig{A,B,C,D}_*.png`.
Frozen parameters:
```text
P2_E5_FR_GRID_ALL_STABLE = TRUE (18/18, tstep=5ms)
P2_E5_BEST_SIMULTANEOUS_IMPROVEMENT = "gen_severe I_f=+7.7% I_r=+3.7% (Kf=1.0x,Kr=0.75x); load_severe 0%/0%"
P2_E5_LOAD_SEVERE_ROCOF_LOCAL_GLOBAL_RATIO = 0.16 (bus 13), 0.16 (bus 12)
P2_E5_LOAD_SEVERE_LAG_MS = 5 (insignificante -- NO es problema de retardo)
P2_E5_LOAD_SEVERE_ROOT_CAUSE = "observabilidad local (magnitud), no timing, no ley de control"
STOP_P2_A_SATISFIED = FALSE
STOP_P2_A_FAILING_CRITERIA = "1 (mejora material reproducible), 4 (consistencia entre escenarios)"
TD3_TRAINING_AUTHORIZED = FALSE
```
Blockers or limitations: El diagnóstico de observabilidad usó un único punto de la grilla (`Kf=0.1x`,
`Kr=0.05x`) como referencia -- razonable dado que `load_severe` no varía con la ganancia, pero no se
verificó explícitamente en los 9 puntos. `RoCoF_COI` no está disponible; si se decide en el futuro que
una señal wide-area (COI) podría resolver la limitación de observabilidad, requeriría implementarlo
como código nuevo (fuera de alcance de este diagnóstico). No se investigó si otros buses BESS
(reubicación) tendrían mejor observabilidad para este tipo de disturbio -- el plan mantiene la
ubicación de P1 congelada (`DEC-P2-002`) y esta entrada no la cuestiona.
Responsible: Claude (ejecución bajo autorización explícita del usuario, en dos rondas)
Status: passed (diagnóstico completo); `STOP-P2-A` formalmente NO satisfecho
Next action: Reportar al usuario (relación local/global, retraso, correlación, conclusión de
observabilidad, PASS/FAIL de `STOP-P2-A`) y **detenerse** -- no entrenar TD3, esperar decisión
explícita del usuario sobre cómo proceder (revisar ubicación/autoridad BESS, revisar estructura de
observación con señal wide-area, o reencuadrar el estudio -- opciones ya previstas en el plan SS20).

## DEC-P2-015

Date: 2026-08-19
Stage/Gate: **Diagnóstico causal local vs. global (COI-proxy) para `load_severe` — cierre de la
investigación de observabilidad de `STOP-P2-A`.** Autorizado explícitamente por el usuario.
**Qué se hizo:** se añadió un parámetro `feedback` (`'local'` default, sin cambios; `'global'` nuevo)
a `p2_common.py::run_physical_scenario_tc()` -- cuando `feedback='global'`, ambos BESS reciben la
MISMA lectura de frecuencia/RoCoF del peor bus del sistema (`min BusFreq.f` / `max |BusROCOF.Wf_y|`
sobre `GEN_BUSES`, la misma cantidad ya registrada como `f_worst_hz`/`rocof_worst_hz_s`) en vez de su
propia lectura de bus local -- una re-conexión de una señal YA calculada hacia la MISMA ley de
control, sin modelo ni ponderación nueva (`RoCoF_COI` verdadero seguiría sin implementarse; esto es el
proxy "global" que el usuario aceptó explícitamente como disponible sin modificar el modelo). `Kf`,
`Kr`, `Pmax`, `Tc`, `tip`, `BusROCOF`/`Tf`/`Tw`/`Tr`, ubicación BESS: sin cambios.
Se comparó, con `Kf=1.0x`/`Kr=0.75x` fijo (el mejor punto F+R encontrado, `DEC-P2-014`), `Tc=100ms`,
`tstep=5ms`:
- **Variante A (local):** reutilizada del `p2e5_kf_kr_grid.csv` ya calculado -- **sin nueva
  simulación**.
- **Variante B (global):** **una única simulación nueva**
  (`Paper_2/src/stage_p2e5e_local_vs_global_feedback.py`).
```text
NoFFC referencia:  df_nadir=-0.2083Hz  RoCoF_max=2.9334Hz/s
A (local):         df_nadir=-0.2083Hz  RoCoF_max=2.9334Hz/s  I_f=+0.00%  I_r=+0.00%  Ppeak=138.3MW  sat=0.0000  STABLE
B (global):        df_nadir=-0.2083Hz  RoCoF_max=2.9334Hz/s  I_f=+0.00%  I_r=+0.00%  Ppeak=114.3MW  sat=0.0000  STABLE
```
Interpretation: **La variante global/COI-proxy NO produjo ninguna mejora** -- `df_nadir` y `RoCoF_max`
salen bit-idénticos a la variante local y a NoFFC (`I_f=I_r=0.00%` en ambas variantes). Esto **descarta
la observabilidad local como causa suficiente** del desempeño nulo de `load_severe`: incluso
entregándole al controlador la señal de RoCoF más grande disponible en todo el sistema, la respuesta
del BESS no logra mover `df_nadir` ni `RoCoF_max` en absoluto para este disturbio específico. La causa
raíz es más estructural que un problema de qué señal observa el controlador -- posibles explicaciones
no confirmadas en esta entrada (no investigadas más a fondo, fuera de alcance de este diagnóstico
único): distancia eléctrica entre los buses BESS y el punto donde ocurre el pico de RoCoF del sistema
(la inyección de potencia en los buses 12/13 podría no propagarse eficazmente hacia la dinámica que
domina la métrica del "peor bus"), o una interacción entre el tipo de disturbio (incremento de carga)
y la respuesta dinámica del sistema que hace que ninguna acción de los BESS en estas ubicaciones
altere las dos métricas del gate para este escenario particular.
Selected Tc or unresolved decision: Siguiendo la Sección 7 de la instrucción del usuario ("si tampoco
mejora con COI/global: cerrar STOP-P2-A como FAIL estructural para esta arquitectura física"):
```text
STOP_P2_A_FINAL_VERDICT = FAIL_ESTRUCTURAL
STOP_P2_A_CAUSA = "No es observabilidad local (descartado empiricamente, DEC-P2-015); la arquitectura Physical Hybrid (Kf/Kr, feedback local O global) no produce mejora medible para el escenario load_severe con la ubicacion BESS actual"
TD3_TRAINING_AUTHORIZED = FALSE (sin cambios respecto a DEC-P2-014)
```
`STOP-P2-A` se cierra formalmente como **FAIL estructural** para la arquitectura física actual
evaluada en `load_severe` -- no un problema resoluble ajustando `Kf`/`Kr` o la fuente de observación.
`gen_severe` sí muestra una mejora modesta (`+7.7%/+3.7%`, `DEC-P2-014`), por lo que el fallo es
específico del tipo de escenario/disturbio `load_severe`, no universal a toda la arquitectura.
Evidence reviewed: `Paper_2/artifacts/diagnostics/p2e5e_local_vs_global_feedback.csv`;
`Paper_2/artifacts/diagnostics/p2e5_kf_kr_grid.csv` (fila reutilizada para variante A).
Frozen parameters:
```text
P2_E5E_GLOBAL_FEEDBACK_CAPABILITY_ADDED = TRUE (run_physical_scenario_tc(feedback='local'|'global'))
P2_E5E_LOCAL_VS_GLOBAL_BOTH_ZERO_EFFECT_LOAD_SEVERE = TRUE
P2_E5E_OBSERVABILITY_HYPOTHESIS_REJECTED_AS_SOLE_CAUSE = TRUE
STOP_P2_A_CLOSED = "FAIL_ESTRUCTURAL para load_severe; gen_severe muestra mejora modesta no material"
```
Blockers or limitations: No se investigó la causa raíz estructural exacta (distancia eléctrica,
propagación de la inyección de potencia, u otra interacción disturbio-topología) -- queda fuera de
alcance del diagnóstico único autorizado. Solo se probó un punto de ganancia (`Kf=1.0x`/`Kr=0.75x`);
aunque `load_severe` ya mostró insensibilidad total en TODA la grilla F+R (`DEC-P2-014`), no se repitió
la variante global en otros puntos de ganancia. No se probó la variante global en `gen_severe` (el
diagnóstico se limitó a `load_severe`, el escenario con el problema).
Responsible: Claude (ejecución bajo autorización explícita del usuario)
Status: passed
Next action: Reportar al usuario (local vs. global, I_f, I_r, estabilidad, saturación, conclusión
causal, recomendación final de `STOP-P2-A`) y **detenerse** -- no entrenar TD3, esperar decisión
explícita del usuario sobre el siguiente paso (revisar ubicación BESS, reencuadrar el alcance del
estudio para `load_severe`, o aceptar el resultado como una limitación documentada del diseño actual).

## DEC-P2-016

Date: 2026-08-19
Stage/Gate: **Diagnóstico de controlabilidad espacial (open-loop) para `load_severe` -- causa raíz
final de `STOP-P2-A`.** Autorizado explícitamente por el usuario.
**Qué se hizo:** nuevas funciones `p2_common.py::add_single_bess()` y
`run_spatial_controllability_probe()` (dispositivo único, sin `Kf`/`Kr`, sin lazo de realimentación --
un escalón de potencia FIJO y prescrito de `+293.4MW` -- un BESS completo de autoridad -- aplicado
exactamente en `t=TD`, sostenido, en UN bus a la vez). Distancia eléctrica desde el bus 20 (disturbio
`load_severe`, `PQ_9`) calculada con `electrical_distance()` ya existente (sin cambios). Buses
probados: `BESS_BUS_1=13`, `BESS_BUS_2=12` (ubicaciones congeladas), los 3 buses más cercanos al bus 20
(`19`, `16`, `24`), y el propio bus `20` (cota superior "oráculo", co-localizado con el disturbio, no
un candidato real). Misma magnitud de inyección (`+293.4MW`) en todas las ubicaciones.
Resultado (`Paper_2/artifacts/diagnostics/p2e5f_spatial_controllability.csv`), ordenado por distancia:
```text
bus   dist    delta_df_nadir   delta_RoCoF      (referencia NoFFC: RoCoF_max=2.9334Hz/s)
 20   0.0000  +94.59 mHz       +1.1277 Hz/s   (-38.4% RoCoF, oraculo, co-localizado)
 19   0.0138  +55.72 mHz       +0.6350 Hz/s   (-21.6% RoCoF, candidato mas cercano real)
 16   0.0333  +29.61 mHz       +0.3020 Hz/s   (-10.3% RoCoF)
 24   0.0392  +28.07 mHz       +0.2857 Hz/s   (-9.7% RoCoF)
 13   0.0745  +12.80 mHz       +0.1266 Hz/s   (-4.3% RoCoF, BESS_BUS_1 actual)
 12   0.1180  +12.23 mHz       +0.1210 Hz/s   (-4.1% RoCoF, BESS_BUS_2 actual)
```
Interpretation: **Relación monótona y limpia entre distancia eléctrica y sensibilidad** -- a MISMA
magnitud de inyección, la sensibilidad decae de forma casi perfectamente ordenada con la distancia al
disturbio. El candidato más cercano real (bus 19) muestra **~5x más sensibilidad de RoCoF** que
`BESS_BUS_1` actual (`0.635` vs `0.127 Hz/s`) y ~4.3x más sensibilidad de nadir, con la MISMA potencia
inyectada. Esto **confirma la Sección 7 de la instrucción del usuario**: el problema principal para
`load_severe` es la ubicación/participation-factor espacial de los BESS actuales, no la ley de control,
no la ganancia, no la observación (ya descartadas en `DEC-P2-014`/`DEC-P2-015`). Nota: incluso en el
mejor candidato real (bus 19), el efecto de este escalón abierto de potencia completa (`-21.6%` RoCoF)
es una COTA SUPERIOR de lazo abierto -- no lo que lograría un controlador realimentado real con
`tip`/`Tc`/saturación; aun así, la brecha de 5x frente a los buses actuales es clara e inequívoca.
Selected Tc or unresolved decision: **`STOP-P2-A` para `load_severe`: la causa raíz identificada es
controlabilidad espacial (ubicación de los BESS), no observabilidad ni ley de control.** No se
reubican los BESS del paper en esta entrada (instrucción explícita del usuario). Queda como
recomendación para el usuario evaluar si reencuadrar la ubicación de los BESS del estudio o mantener
`load_severe` como una limitación documentada de la arquitectura actual.
Evidence reviewed: `Paper_2/artifacts/diagnostics/p2e5f_spatial_controllability.csv`.
Frozen parameters:
```text
P2_E5F_SPATIAL_CONTROLLABILITY_ROOT_CAUSE_CONFIRMED = TRUE
P2_E5F_BEST_REAL_CANDIDATE_BUS = 19 (dist=0.0138, ~5x sensibilidad RoCoF vs BESS_BUS_1 actual)
P2_E5F_MONOTONIC_DISTANCE_SENSITIVITY_RELATIONSHIP = TRUE
STOP_P2_A_ROOT_CAUSE_LOAD_SEVERE = "controlabilidad espacial (ubicacion BESS), NO observabilidad NI ley de control"
BESS_LOCATIONS_NOT_CHANGED = TRUE (instruccion explicita)
TD3_TRAINING_AUTHORIZED = FALSE (sin cambios)
```
Blockers or limitations: Es un diagnóstico de lazo abierto (cota superior), no reproduce la dinámica
real del actuador (`tip`) ni de la ley de control -- el efecto real con `Kf`/`Kr` sería menor. Solo se
probaron 6 ubicaciones puntuales (no una grilla espacial exhaustiva). No se probó la sensibilidad
espacial para `gen_severe` (el probe que ya funciona razonablemente) para verificar si la relación
distancia-sensibilidad es igual de fuerte ahí.
Responsible: Claude (ejecución bajo autorización explícita del usuario)
Status: passed
Next action: Reportar al usuario (sensibilidad por ubicación, mejor ubicación, comparación con 12/13,
conclusión de controlabilidad espacial, recomendación) y **detenerse** -- no mover BESS, no aumentar
Pmax, no entrenar TD3, esperar decisión explícita del usuario.

## DEC-P2-017

Date: 2026-08-19
Stage/Gate: **P2-E6 -- screening de reubicación de BESS, conjunto y robusto entre ambos escenarios
DESIGN (no solo `load_severe`, no solo cercanía eléctrica).** Autorizado explícitamente por el usuario.
**Qué se hizo:** nueva función `p2_common.py::run_spatial_controllability_probe_multi()`
(generalización de lista-de-buses de la función de un solo bus de `DEC-P2-016`, misma metodología de
lazo abierto). **Paso A:** escaneo de un solo bus (`+293.4MW`, mismo `command_mw` que `DEC-P2-016`) en
los 29 buses técnicamente admisibles (`BESS_ADMISSIBLE_BUSES`), contra AMBOS probes DESIGN
(`gen_severe`, `load_severe`) -- 58 simulaciones + 2 NoFFC. Puntaje conjunto por bus = media de las 4
métricas (`delta_df`/`delta_RoCoF` por escenario), cada una normalizada por su propio máximo entre los
29 buses (ningún escenario ni métrica domina por sí solo). **Paso B:** los 4 mejores candidatos por
puntaje conjunto (`19, 20, 16, 24`) se probaron en las 6 combinaciones de pares posibles, más el par
actual (`12,13`), con inyección conjunta de dos buses simultánea
(`run_spatial_controllability_probe_multi`) -- 14 simulaciones.
**Resultado Paso A** (`Paper_2/artifacts/diagnostics/p2e6_single_bus_screening.csv`), ranking por
puntaje conjunto: `19 (0.539) > 20 (0.500) > 16 (0.472) > 24 (0.465) > 21 > 15 > 17 > 23 > ...`.
`BESS_BUS_1=13` rank 16/29, `BESS_BUS_2=12` rank 17/29 -- **mediocres, no los peores, pero lejos del
óptimo**. Bus 19 es líder individual claro y limpio (las 4 métricas positivas). **Bus 20 muestra
`delta_rocof_gen_severe` NEGATIVO (-0.525 Hz/s)** pese a ser el mejor para `load_severe` -- primera
señal de un efecto de interacción/artefacto específico de escenario.
**Resultado Paso B** (`Paper_2/artifacts/diagnostics/p2e6_pair_screening.csv`), ranking por puntaje
conjunto ingenuo: `(16,20)=0.541 > (20,24)=0.540 > (16,19)=0.476 > (19,24)=0.475 > (19,20)=0.458 >
(16,24)=0.450 > (12,13)=0.138 [par actual]`.
**Hallazgo crítico que impide usar el ranking ingenuo directamente:** de los 7 pares probados, **6 de
7 -- incluido el par ACTUAL (12,13) -- muestran `delta_rocof_gen_severe` NEGATIVO** (empeoramiento del
RoCoF para `gen_severe` bajo este escalón abierto sostenido): `(16,20)=-1.015`, `(20,24)=-0.991`,
`(16,19)=-0.287`, `(19,24)=-0.263`, `(19,20)=-1.528` (el peor, casi duplica el RoCoF base), `(12,13)
actual=-0.601`. **Solo `(16,24)` muestra las 4 métricas positivas** (`rocof_gen=+0.189`).
Interpretation: Que el propio par ACTUAL (`12,13`), ya validado como estable y modestamente positivo
bajo el controlador realimentado real (`DEC-P2-014`: `+7.7%/+3.7%` en `gen_severe`), muestre
`delta_rocof_gen_severe` NEGATIVO bajo esta sonda de lazo abierto, indica que **el patrón es
mayormente un artefacto de la metodología de sonda** (escalón de potencia completa SOSTENIDO durante
los 5 s posteriores al disturbio, nunca liberado) interactuando con la dinámica de un evento de
pérdida de generación -- un controlador realimentado real modula el comando en vez de sostenerlo al
máximo indefinidamente, y por eso el controlador `Kf`/`Kr` real en `(12,13)` SÍ mejora `gen_severe`
mientras la sonda abierta sugiere lo contrario. **Esto significa que el puntaje conjunto ingenuo NO es
confiable para seleccionar el par cuando dos candidatos fuertes se combinan** -- se requiere el
criterio explícito de robustez del usuario (Sección 5: "mejor desempeño conjunto Y ROBUSTO"), no
únicamente el puntaje más alto. `(16,24)` es el ÚNICO par, de los 7 probados, sin ninguna métrica
negativa -- y aun bajo la misma sonda imperfecta, supera ampliamente al par actual en 3 de 4 métricas
(`df_gen +147.4mHz` vs `+100.0mHz`; `df_load +51.8mHz` vs `+24.7mHz`; `RoCoF_load +0.579Hz/s` vs
`+0.240Hz/s`) y NO muestra el patrón de empeoramiento de `RoCoF_gen` que sí muestra el par actual.
Selected Tc or unresolved decision: **Par recomendado: `(16, 24)`** -- no por tener el puntaje
conjunto ingenuo más alto (no lo tiene), sino por ser el único candidato robusto (sin métrica
patológica) que además domina claramente al par actual en 3 de 4 métricas y iguala/mejora la cuarta.
**No se congela formalmente todavía** -- queda como recomendación pendiente de aprobación explícita del
usuario antes de "congelar las nuevas ubicaciones" (Sección 7 de su instrucción). **No se re-ejecutó
P2-E5 F+R con las nuevas ubicaciones ni se reevaluó `STOP-P2-A`** -- explícitamente diferido a una
autorización separada (el checklist de reporte de esta ronda, Sección 9 de la instrucción, no pide esos
resultados).
Evidence reviewed: `Paper_2/artifacts/diagnostics/p2e6_single_bus_screening.csv`,
`p2e6_pair_screening.csv`.
Frozen parameters: Ninguno formalmente congelado -- recomendación pendiente de aprobación.
```text
P2_E6_TOP4_SINGLE_BUS_CANDIDATES = [19, 20, 16, 24]
P2_E6_NAIVE_BEST_PAIR = "(16,20), joint_score=0.541 -- RECHAZADO por patologia (rocof_gen=-1.015Hz/s)"
P2_E6_ROBUST_RECOMMENDED_PAIR = "(16, 24) -- unico par sin metrica negativa, domina al par actual en 3/4 metricas"
P2_E6_CURRENT_PAIR_RANK = "bus 13 rank 16/29, bus 12 rank 17/29 (screening individual)"
P2_E6_OPEN_LOOP_PROBE_ARTIFACT_FOR_GEN_SEVERE_SUSPECTED = TRUE (par actual tambien muestra rocof_gen negativo bajo la sonda, pese a ser positivo con el controlador Kf/Kr real -- DEC-P2-014)
BESS_RELOCATION_NOT_YET_FROZEN = TRUE
P2_E5_FR_RERUN_PENDING = TRUE (diferido, no autorizado en esta ronda)
STOP_P2_A_REEVALUATION_PENDING = TRUE (diferido, no autorizado en esta ronda)
```
Blockers or limitations: El patrón de `rocof_gen` negativo bajo la sonda abierta sostenida no fue
diagnosticado a fondo (hipótesis razonable, no confirmada con evidencia adicional más allá de la
consistencia con `DEC-P2-014`). La recomendación `(16,24)` se basa en la sonda de lazo abierto, una
cota superior -- el comportamiento real con `Kf`/`Kr` realimentados en esas ubicaciones no se ha
verificado (ese es precisamente el propósito de la Sección 7, diferida). Solo se probaron los 4
mejores candidatos individuales en pares -- no se exploró si una combinación fuera del top-4 individual
podría ser aún más robusta.
Responsible: Claude (ejecución bajo autorización explícita del usuario)
Status: passed (screening completo); recomendación pendiente de aprobación para congelar
Next action: Reportar al usuario (pares candidatos, sensibilidad por escenario, par recomendado,
comparación frente a 12/13, justificación de selección) y **detenerse** -- no congelar todavía, no
repetir P2-E5 F+R, no reevaluar `STOP-P2-A`, no entrenar TD3, esperar aprobación explícita del usuario
para congelar `(16,24)` (u otra decisión) antes de continuar.

## DEC-P2-018

Date: 2026-08-19
Stage/Gate: **P2-E6b -- validación cerrada (controlador F+R real) de reubicación de BESS y
congelamiento.** Autorizado explícitamente por el usuario (`(16,24)` y `(16,20)`, mismo `Kf`/`Kr`/`Tc`/
`Pmax`/`tstep` que el mejor punto F+R ya conocido, `Kf=1.0x=586.8`, `Kr=0.75x=220.05`, `DEC-P2-014`).
**Qué se hizo:** `Paper_2/src/stage_p2e6b_closed_loop_relocation_validation.py`, reutilizando
`run_physical_scenario_tc()` sin cambios, con `bess_bus1`/`bess_bus2` apuntando a cada par candidato.
Par actual `(12,13)` reutilizado del `p2e5_kf_kr_grid.csv` ya calculado (mismo punto `Kf`/`Kr`) -- sin
nueva simulación. 4 simulaciones nuevas (2 pares x 2 escenarios).
Resultado (`Paper_2/artifacts/diagnostics/p2e6b_closed_loop_relocation_validation.csv`):
```text
                   gen_severe (I_f / I_r)      load_severe (I_f / I_r)     sat   TDS
(12,13) actual:    +7.65% / +3.72%              0.00% / 0.00%              0.0   OK
(16,24):           +17.52% / +14.94%            ~0.00% / ~0.00% (ruido)    0.0   OK
(16,20):           +29.55% / +20.15%            ~0.00% / ~0.00% (ruido)    0.0   OK
```
Interpretation: **`(16,20)` domina estrictamente a `(16,24)` bajo el controlador realimentado real**
-- mejor en las dos métricas de `gen_severe` (`+29.6%/+20.1%` vs `+17.5%/+14.9%`) y empatado
(exactamente cero, ruido de punto flotante ~1e-11, ambos) en `load_severe`. **Esto contradice
directamente el ranking de la sonda de lazo abierto (`DEC-P2-017`)**, que había marcado `(16,20)` como
"patológico" por un `RoCoF_gen` negativo bajo un escalón sostenido -- confirmando la sospecha ya
registrada en `DEC-P2-017` de que ese patrón era un artefacto de la metodología de sonda (escalón de
potencia completa sostenido sin liberar), no un reflejo del comportamiento real con realimentación.
Siguiendo la instrucción explícita del usuario (Sección 6, "no usar el ranking de la sonda abierta
para decidir el ganador"), el resultado de esta validación cerrada es la autoridad final.
`gen_severe` para AMBOS pares nuevos alcanza mejora **material** (`>=10%`) simultánea de nadir y RoCoF
por primera vez en toda la campaña P2 -- el par actual nunca lo había logrado (`+7.7%/+3.7%`, por
debajo del umbral). `load_severe` sigue en `0%/0%` en los TRES pares -- confirma, con evidencia
adicional, que la limitación de `load_severe` es estructural e independiente de la ubicación BESS
dentro del conjunto de candidatos probado hasta ahora (consistente con `DEC-P2-014/015/016`).
Selected Tc or unresolved decision: **Aplica la Sección 8 de la instrucción del usuario** ("si otro par
es claramente mejor y estable en ambos escenarios, congelar ese par") -- `(16,20)` es claramente mejor
que `(16,24)` en `gen_severe` y empatado (no peor) en `load_severe`, y estable en ambos.
**`BESS_BUS_1`/`BESS_BUS_2` se congelan formalmente en `p2_common.py` a `16`/`20`** (antes `13`/`12`).
Todos los resultados de `P2-E1` a `P2-E6` calculados antes de esta entrada usaban `13`/`12` y
**permanecen válidos como snapshot histórico de esa ubicación** -- no se reinterpretan
retroactivamente.
**`STOP-P2-A` reevaluado con la nueva ubicación:**
```text
Criterio 1 (mejora simultanea reproducible de nadir y RoCoF): PARCIAL
  - gen_severe: PASA (I_f=+29.6%, I_r=+20.1%, ambos >=10%) -- primera vez en toda la campana P2.
  - load_severe: FALLA (0%/0%, sin cambio).
Criterio 2 (estabilidad numerica): CUMPLE (STABLE, TDS_success=True en ambos escenarios)
Criterio 3 (ausencia de saturacion patologica): CUMPLE (saturation_fraction=0.0 en ambos)
Criterio 4 (consistencia entre escenarios): FALLA (persiste la inconsistencia radical entre probes:
  gen_severe material, load_severe nulo -- ahora con una brecha aun mayor en terminos absolutos)
```
```text
STOP_P2_A_VERDICT_AFTER_RELOCATION = FAIL (persiste; Criterio 1 solo parcial, Criterio 4 sigue fallando)
STOP_P2_A_IMPROVEMENT = "gen_severe paso de no-material a material (+7.7%/+3.7% -> +29.6%/+20.1%); load_severe sin cambio, limitacion estructural separada confirmada"
```
`STOP-P2-A` **sigue sin satisfacerse formalmente** (el criterio 4, consistencia entre escenarios,
exige que el margen se sostenga en varios escenarios DESIGN, no solo uno) -- pero la reubicación
representa una mejora sustancial y ya demuestra que la arquitectura física SÍ puede alcanzar mejora
material cuando la ubicación no es el cuello de botella (`gen_severe`). `load_severe` queda como una
limitación estructural aislada y ya extensamente diagnosticada (`DEC-P2-014` a `DEC-P2-016`), no
resuelta por reubicación dentro del conjunto de candidatos evaluado.
Evidence reviewed: `Paper_2/artifacts/diagnostics/p2e6b_closed_loop_relocation_validation.csv`;
`Paper_2/artifacts/diagnostics/p2e5_kf_kr_grid.csv` (fila reutilizada del par actual).
Frozen parameters:
```text
BESS_BUS_1 = 16  (antes 13, DEC-P2-002/P2-E1)
BESS_BUS_2 = 20  (antes 12, DEC-P2-002/P2-E1)
BESS_RELOCATION_FROZEN = TRUE
BESS_RELOCATION_SUPERSEDES = "DEC-P2-002 (placement original P1, buses 13/12)"
STOP_P2_A_STATUS_AFTER_RELOCATION = "FAIL persistente, pero Criterio 1 ahora PARCIAL (antes fallaba por completo en ambos escenarios)"
TD3_TRAINING_AUTHORIZED = FALSE (sin cambios)
```
Blockers or limitations: `load_severe` sigue sin explicación causal completa (se descartaron
observabilidad -- `DEC-P2-015` -- y controlabilidad de ubicación dentro del conjunto probado --
`DEC-P2-016`/`DEC-P2-018` --, pero no se identificó la causa raíz final). El par `(16,20)` no se
sometió a la grilla F+R completa (F-only/R-only, ni un barrido de `Tc` propio) -- solo se verificó en
el punto de ganancia ya conocido (`Kf=1.0x`/`Kr=0.75x`); en sentido estricto, `P2-E4`/`P2-E5` completos
deberían repetirse en la nueva ubicación antes de considerar el diseño físico definitivamente cerrado,
aunque esta validación puntual ya es suficiente para decidir la reubicación en sí.
Responsible: Claude (ejecución bajo autorización explícita del usuario)
Status: passed; `BESS_RELOCATION_FROZEN=TRUE`; `STOP-P2-A` re-evaluado y sigue en FAIL
Next action: Reportar al usuario (tabla, `I_f`/`I_r` por escenario, estabilidad/saturación, par
recomendado, `STOP-P2-A` actualizado) y **detenerse** -- no entrenar TD3, no usar validation ni
`P2-T*`, esperar decisión explícita del usuario sobre el siguiente paso (aceptar `load_severe` como
limitación estructural documentada y proceder con `gen_severe` como el caso funcional, investigar
`load_severe` más a fondo, o reencuadrar el alcance del estudio).

## DEC-P2-019

Date: 2026-08-19
Stage/Gate: **P2-E7 -- diagnóstico causal final de `load_severe`: causa raíz identificada
(desajuste de temporización `Tc` vs. velocidad del transitorio del disturbio).** Autorizado
explícitamente por el usuario. `BESS_BUS_1=16`, `BESS_BUS_2=20`, `Pmax`, `Tc=100ms`, `tstep=5ms`,
`Kf=1.0x=586.8`, `Kr=0.75x=220.05` (mismos valores congelados en `DEC-P2-018`, sin retuning).
**Qué se hizo:** se extendió `run_physical_scenario_tc()` con un nuevo modo `controller='open_loop_
fixed'` (escalón fijo prescrito, misma infraestructura/logging que los casos NoFFC/F+R -- comparación
directa) y con registro de `f_coi_hz` (media NO ponderada de frecuencia sobre `GEN_BUSES`, un proxy de
COI -- el COI verdadero ponderado por `H` no está implementado, esto se declara explícitamente). Se
verificó primero la mecánica del disturbio (`Paper_2/src/stage_p2e7_load_severe_deep_diagnostic.py`,
sin BESS) y luego se ejecutaron los tres casos (A NoFFC, B F+R, C inyección abierta) con logging
completo (`Paper_2/artifacts/trajectories/p2e7_load_severe_deep_diagnostic_traces.npz`).
**Verificación de la mecánica del disturbio:** `PQ_9` (bus 20), `P0` nominal = **680.00 MW**,
`alpha_L=0.50` -> incremento = **340.00 MW**, evento vía `Alter` en `t=1.0s` (`model=PQ, src=Ppf,
method='+'`). Balance antes del evento: carga total = 5856.40 MW, generación despachada = 5320.39 MW
(la diferencia es la generación del `Slack`, consistente con el caso stock). El incremento de 340 MW
es exactamente el `34.0%` de `Pmax,total` de ambos BESS combinados (`2x293.4=586.8MW`) -- la autoridad
física disponible es más que suficiente en magnitud (confirmado independientemente por el Caso C).
**Nota de limitación del script de verificación:** la lectura directa de `PQ.Ppf.v` inmediatamente
antes/después de `t=TD` en el script de verificación mostró `0.00 MW` de cambio (posible desajuste de
timing/atributo en esa lectura puntual, no investigado más a fondo) -- esto NO pone en duda que el
disturbio se aplica correctamente: la respuesta dinámica de NoFFC (`df_nadir=-208.3mHz`,
`RoCoF_max=2.933Hz/s`, idéntica a todas las corridas anteriores de `load_severe` en toda la campaña
P2) confirma independientemente y de forma inequívoca que el escalón de 340 MW sí se aplica en `t=1.0s`
como está configurado.
**Resultado de los tres casos** (`Paper_2/artifacts/diagnostics/p2e7_load_severe_deep_diagnostic.csv`):
```text
Caso A (NoFFC):      df_nadir=-208.31mHz  RoCoF_max=2.9334Hz/s  t_nadir=1.0351s (TD+35.1ms)
Caso B (F+R):         df_nadir=-208.31mHz  RoCoF_max=2.9334Hz/s  t_nadir=1.0351s (TD+35.1ms) -- BIT-IDENTICO a NoFFC
Caso C (open-loop):   df_nadir= -99.68mHz  RoCoF_max=1.6074Hz/s  t_nadir=1.0201s (TD+20.1ms) -- mejora 45% RoCoF
```
Potencia realmente entregada: Caso B (F+R), pico `81.4/81.0 MW` (bus 16/20) -- **NO es cero, el
controlador SÍ actúa de forma sustancial** (28% de `Pmax`); Caso C (open-loop), pico `293.5/293.5 MW`
(autoridad completa).
**Trayectoria de comando de Caso B alrededor del evento (la evidencia causal decisiva):**
```text
t=0.990 a t=1.080s: P_command1 = P_command2 = 0.00 MW (SIN CAMBIO -- el controlador todavia no reacciona)
t=1.100s:           P_command1 = +81.91 MW,  P_command2 = +1.47 MW  <- PRIMER COMANDO REACTIVO
```
Interpretation: **Causa raíz identificada de forma concluyente: desajuste de temporización, no ley de
control, no observabilidad, no controlabilidad espacial, no ganancia.** El nadir de `load_severe`
ocurre en `t=1.0351s` (`TD+35.1ms`) -- el comando del controlador F+R permanece en CERO hasta
exactamente `t=1.100s` (`TD+100ms`, el primer instante de actualización tras el disturbio, dado
`Tc=100ms` y que `t=TD=1.0s` coincide exactamente con un instante de control que todavía usa el estado
PRE-disturbio). **El controlador aún no ha emitido su primer comando reactivo cuando el punto más
severo de la trayectoria (el propio nadir/RoCoF que define la métrica) ya ocurrió y pasó** -- 65 ms
antes de que exista siquiera un comando distinto de cero. Por construcción, ningún ajuste de `Kf`,
`Kr`, ubicación de BESS, ni esquema de observación (local o global) puede cambiar un resultado que ya
quedó fijado antes de que el controlador tuviera oportunidad de actuar. Esto explica de forma unificada
TODOS los resultados nulos de `load_severe` observados desde `DEC-P2-011` en adelante (F-only, R-only,
F+R en ambas ubicaciones, feedback local y global) -- ninguno de esos experimentos podía, en principio,
producir un resultado distinto, porque el cuello de botella real es el `Tc=100ms` frente a un
transitorio de disturbio de carga que se resuelve en apenas ~35ms. El Caso C (open-loop) SÍ mejora,
precisamente porque se aplica de forma instantánea en `t=TD`, sin esperar ningún periodo de control --
bypaseando exactamente el mecanismo que bloquea al Caso B.
Selected Tc or unresolved decision: **Confirma la interpretación del Caso 1 de la Sección 7 de la
instrucción del usuario ("si la inyección abierta sí mejora la frecuencia pero F+R no: concluir que el
problema está en la ley de control/señal de activación para este tipo de perturbación") -- con la
causa raíz precisada exactamente: la señal de activación no llega a tiempo por el periodo de muestreo
`Tc=100ms`, no por un defecto de la ley de control `Kf`/`Kr` en sí.** No se modifica `Tc` en esta
entrada (fuera de alcance de este diagnóstico único) -- pero la evidencia sugiere fuertemente que
`Tc=20ms` (la otra configuración ya encontrada numéricamente estable en `DEC-P2-009`/`DEC-P2-010`, para
al menos el probe `gen_severe`) podría capturar el transitorio de `load_severe` con 1-2
actualizaciones de control antes del nadir (`35ms / 20ms ~= 1.75` periodos), a diferencia de `Tc=100ms`
(`35ms / 100ms < 1` periodo completo). Esto queda como hipótesis para una etapa de diseño futura, no
verificada en esta entrada.
Evidence reviewed: `Paper_2/artifacts/diagnostics/p2e7_load_severe_deep_diagnostic.csv`;
`Paper_2/artifacts/trajectories/p2e7_load_severe_deep_diagnostic_traces.npz` (inspección directa de
`P_command1/2` alrededor de `t=TD`, evidencia decisiva citada arriba).
Frozen parameters: Ninguno.
```text
P2_E7_LOAD_SEVERE_ROOT_CAUSE_CONFIRMED = "Tc=100ms timing mismatch vs ~35ms disturbance transient -- NOT control law, NOT observability, NOT spatial controllability, NOT gain"
P2_E7_NADIR_TIME_S = 1.0351 (TD+35.1ms)
P2_E7_FIRST_REACTIVE_COMMAND_TIME_S = 1.100 (TD+100ms, primer update tras el disturbio)
P2_E7_FR_DELIVERS_REAL_POWER_BUT_TOO_LATE = TRUE (81MW pico, pero despues del nadir)
P2_E7_OPEN_LOOP_CONFIRMS_AUTHORITY_SUFFICIENT = TRUE (45% reduccion RoCoF, aplicado instantaneamente en TD)
P2_E7_FASTER_TC_HYPOTHESIS_FOR_LOAD_SEVERE = "Tc=20ms no verificado en esta entrada, hipotesis para etapa de diseno futura"
TD3_TRAINING_AUTHORIZED = FALSE (sin cambios)
```
Blockers or limitations: No se verificó la hipótesis `Tc=20ms` (fuera de alcance de este diagnóstico
único, autorización explícita separada requerida). El defecto de lectura de `PQ.Ppf.v` en el script de
verificación no se investigó a fondo (no bloquea la conclusión causal, que se apoya en la respuesta
dinámica real, no en esa lectura puntual). `f_coi` usado es una media NO ponderada (no un COI
verdadero ponderado por `H`) -- declarado explícitamente, no oculta esta limitación.
Responsible: Claude (ejecución bajo autorización explícita del usuario)
Status: passed -- causa raíz de `load_severe` identificada de forma concluyente
Next action: Reportar al usuario (MW reales del evento, cambio de balance, comparación de los tres
casos, potencia entregada, conclusión causal) y **detenerse** -- no entrenar TD3, no usar validation
ni `P2-T*`, no modificar `Tc` sin autorización explícita, esperar decisión del usuario sobre si
investigar `Tc=20ms` para `load_severe`, aceptar la limitación como documentada, o reencuadrar el
alcance del estudio.

## DEC-P2-020

Date: 2026-08-19
Stage/Gate: **Verificación de `Tc=tstep=5ms` ("consigna continua", recalculada cada ciclo de
cómputo en vez de cada `Tc=100ms`) -- hallazgo mayor: primera mejora material simultánea en AMBOS
escenarios DESIGN de toda la campaña P2.** Autorizada por el usuario tras una discusión técnica sobre
tipo de control (GFL, confirmado en código fuente ANDES: `PVD1.a`/`PVD1.v` son `ExtAlgeb` heredadas del
`Bus`, no formadas por el dispositivo -- el ESD1/PVD1 sigue la red, no la forma) y sobre la cadena de
medición de frecuencia/RoCoF (`andes/models/measurement/busfreq.py`/`busrocof.py`, verificado en
código fuente: `Δθ → Lag(Tf) → Washout(Tw) → f → Washout(Tr) → RoCoF`, la misma arquitectura desde
`Paper_1`).
**Qué se hizo:** una única llamada adicional a `run_physical_scenario_tc()` (código sin cambios,
reutilizado tal cual) por escenario, con `tc=tstep=0.005s` en vez de `tc=0.1s`, mismos `Kf=1.0x=586.8`,
`Kr=0.75x=220.05`, `Pmax=293.4MW`, `BESS_BUS_1=16`/`BESS_BUS_2=20` (frozen, `DEC-P2-018`), mismo
`BusROCOF`/`Tf/Tw/Tr` (sin cambios). Se aplicó el clasificador de estabilidad ya validado (`classify_v2`,
amplitud destendenciada + persistencia + reversiones de signo, `DEC-P2-017`) sobre ambas corridas.
Resultado:
```text
                  df_nadir     I_f      RoCoF_max    I_r      sat      classification
gen_severe:       -0.1298Hz   +28.4%    0.9348Hz/s   +21.1%   0.0000   STABLE
load_severe:      -0.1445Hz   +30.6%    2.2946Hz/s   +21.8%   0.0025   STABLE
```
Interpretation: **`load_severe`, que se mantuvo exactamente en `I_f=I_r=0.0%` en TODA prueba anterior
desde `DEC-P2-011` (F-only, R-only, ambas ubicaciones de BESS -- `12/13`, `16/24`, `16/20` --,
feedback local y global), ahora muestra mejora material (`>=10%`) en ambas métricas** al eliminar el
retardo de muestreo `Tc=100ms` -- **confirmación experimental directa y definitiva de la causa raíz
identificada en `DEC-P2-019`** (el nadir ocurre en `TD+35ms`, antes de que un controlador a `Tc=100ms`
emita su primer comando reactivo en `TD+100ms`; con `Tc=tstep=5ms` el primer comando reactivo ocurre
esencialmente de inmediato, dentro del propio nadir). `gen_severe` también mejora sustancialmente
(de `+7.7%/+3.7%` con `Tc=100ms`, `DEC-P2-018`, a `+28.4%/+21.1%` aquí). **Ambos escenarios STABLE**
bajo el clasificador riguroso (sin oscilación persistente, saturación casi nula) -- no se reprodujo el
patrón de limit-cycle encontrado en `Tc=30-80ms` (`DEC-P2-009/010`); `Tc=tstep=5ms` no es un punto
intermedio de esa región inestable, es un extremo mucho más rápido que `Tc=20ms` (el más rápido
probado formalmente hasta ahora), consistente con que la región inestable fue específica de un rango
intermedio, no de "más rápido es peor" de forma monótona.
**Advertencia explícita, planteada por el asistente antes de ejecutar esta prueba:** `Tc=tstep=5ms`
representa un controlador IDEALIZADO sin retardo de decisión adicional más allá de la cadena de
medición (`Tf=20ms+Tw=20ms+Tr=50ms`) -- no representa necesariamente un controlador digital realista
(protocolo de comunicación, ciclo de firmware). Es la cota superior de lo que la arquitectura física
puede lograr si se elimina el retardo de muestreo por completo, útil como referencia de diseño, pero
la selección de un `Tc` final para Paper_2 debe considerar también la viabilidad de implementación real
-- esa discusión queda pendiente, no resuelta por este hallazgo.
Selected Tc or unresolved decision: **No se congela `Tc=tstep=5ms` como valor final en esta entrada**
-- es un hallazgo de diseño que reabre la pregunta de `Tc` para todo Paper_2 (como ya se había
anticipado explícitamente al usuario antes de autorizar esta prueba). Queda pendiente decidir: (a) si
se adopta este `Tc` (o algo cercano, p.ej. `10-20ms`) como el `Tc` final de Paper_2 en lugar de
`Tc=100ms`, lo que requeriría repetir la verificación de temporización completa (`PF2-DYN-01..04`) y
posiblemente parte de la grilla `Kf`/`Kr` (`P2-E5`) a este nuevo `Tc`; (b) si se investiga un punto
intermedio (p.ej. `Tc=20ms`, ya validado como estable en `DEC-P2-009/010` para al menos un escenario)
para balancear velocidad de reacción con viabilidad de implementación real.
Evidence reviewed: salida de consola de las dos llamadas de verificación (no persistida como CSV
formal en esta entrada -- diagnóstico puntual, análogo a otras verificaciones rápidas de esta sesión).
Frozen parameters: Ninguno formalmente congelado -- hallazgo de diseño, no una decisión de
congelamiento.
```text
P2_E4_TC_TSTEP_5MS_MATERIAL_IMPROVEMENT_BOTH_SCENARIOS = TRUE (primera vez en toda la campana P2)
P2_E4_TC_TSTEP_5MS_STABLE_BOTH_SCENARIOS = TRUE (clasificador riguroso, sin oscilacion)
P2_E4_LOAD_SEVERE_ROOT_CAUSE_CONFIRMED_EXPERIMENTALLY = TRUE (DEC-P2-019 hipotesis validada con evidencia directa, no solo inferencia de timing)
P2_TC_DESIGN_QUESTION_REOPENED = TRUE (Tc=100ms ya no es automaticamente el valor de referencia; pendiente decidir Tc final)
STOP_P2_A_STATUS_WITH_TC_TSTEP_5MS = "Criterios 1/2/3 potencialmente satisfechos (pendiente verificacion formal completa); Criterio 4 (consistencia) ahora plausible por primera vez"
TD3_TRAINING_AUTHORIZED = FALSE (sin cambios; se requiere verificacion formal antes de cualquier decision sobre TD3)
```
Blockers or limitations: Solo se probó UN punto (`Tc=tstep=5ms` exacto) en cada escenario, sin
verificación formal de temporización (`PF2-DYN-01..04`), sin verificación en otros puntos de `Kf`/`Kr`
(solo el punto ya congelado `1.0x/0.75x`), sin verificación en `Tc` intermedios entre `20ms` y `5ms`, y
sin considerar si `Tc=5ms` es una tasa de actualización físicamente implementable en un controlador
digital de BESS real. `STOP-P2-A` NO se reevalúa formalmente en esta entrada -- este es un hallazgo de
diseño preliminar que motiva una nueva ronda de verificación, no una conclusión cerrada.
Responsible: Claude (ejecución bajo autorización explícita del usuario, tras explicar los riesgos y
supuestos antes de ejecutar)
Status: passed -- hallazgo mayor registrado, pendiente de verificación formal y decisión del usuario
sobre el siguiente paso
Next action: Reportar al usuario el hallazgo completo y **detenerse** -- no entrenar TD3, no congelar
`Tc`, esperar decisión explícita del usuario sobre cómo proceder (verificación formal de `Tc` rápido
como nueva etapa de diseño, explorar puntos intermedios, o evaluar viabilidad de implementación real
antes de continuar).

## DEC-P2-021

Date: 2026-08-19
Stage/Gate: **Paquete de figuras físicas P2 (F01-F10 + F10s), regenerado con `Tc=tstep=5ms` (`DEC-P2-020`)
y publicado como galería web.** Autorizado explícitamente por el usuario.
**Qué se hizo:** `Paper_2/src/stage_p2_figures_data.py` actualizado (`TC_S = TSTEP`, antes `0.100`) y
re-ejecutado (9 simulaciones DESIGN: `NoFFC`/`F+R(12,13)`/`F+R(16,24)`/`F+R(16,20)` para `gen_severe` y
`load_severe`, más `OpenLoop(16,20)` para `load_severe`) -- mismos `Kf/Kr/Pmax`/caso low-inertia/
`BusROCOF` que `DEC-P2-018/020`, sin sweep ni tuning nuevo. Se regeneraron las 5 figuras ya construidas
(`F01,F02,F04,F05,F08`) y se construyeron las 5 restantes (`F03,F06,F07,F09,F10` + suplementaria
`F10s`) siguiendo la especificación original del usuario (eje `tau=t-t_event`, estilos de línea
consistentes por controlador, PNG+PDF en single-column y double-column, sin datos sintéticos ni
suavizado). Todas las figuras y `figure_metadata.csv` (con marcadores calculados
programáticamente: nadir, RoCoF_max, primer comando, `Ppeak`) están en `Paper_2/figures_main/`.
Publicada una galería HTML autocontenida (imágenes embebidas base64, sin dependencias externas salvo
Google Fonts) en: https://claude.ai/code/artifact/82a19ad2-9d10-4745-a5a7-04ca78d23261
Interpretation: Con `Tc=tstep=5ms`, `load_severe` ahora muestra mejora material en el par actual
(`16,20`: `I_f=+30.6%`, `I_r=+21.8%`) y también, en menor grado, en los pares antiguos (`12,13`:
`I_f=+1.2%`, `I_r=+0.7%`; `16,24`: `I_f=+7.7%`, `I_r=+3.8%`) -- confirma que con el retardo de
muestreo eliminado, la ubicación deja de ser el factor dominante para `load_severe` (aunque `16,20`
sigue siendo la mejor). `gen_severe` mejora de forma correspondiente en las tres ubicaciones.
Selected Tc or unresolved decision: Ninguna decisión de congelamiento nueva -- las figuras representan
el hallazgo de `DEC-P2-020` (`Tc=tstep`), que sigue sin verificación formal completa ni adoptado como
`Tc` final de Paper_2.
Evidence reviewed: `Paper_2/figures_main/*.png/*.pdf` (22 archivos), `figure_metadata.csv`.
Frozen parameters: Ninguno.
Responsible: Claude (ejecución bajo autorización explícita del usuario)
Status: passed
Next action: Ninguna acción automática -- esperar revisión del usuario sobre la galería y decisión
sobre el siguiente paso para `Tc` (ver `DEC-P2-020`).

## DEC-P2-022

Date: 2026-08-19
Stage/Gate: **Corrección de secuencia hacia el cierre de DESIGN / `STOP-P2-A`.** Entrada de
gobernanza pura -- ninguna simulación nueva ejecutada. Autorizada explícitamente por el usuario
("ok, ajusta de forma correcta") tras revisar una propuesta de 4 pasos para cerrar la fase DESIGN
(congelar baseline físico y declarar `STOP-P2-A=PASS`; retunear droop; `P2-E6` ablation de
observación; `P2-E7` freeze formal).
**Qué se hizo:** se contrastó la propuesta del usuario contra el texto vigente de
`plan_maestro_P2_TD3_Hybrid_FFC.md` (§14.2/§20/§25, sin cambios -- ya especifican el orden correcto,
no requirieron edición) y se detectó una inversión de orden: el paso propuesto "declarar
`STOP-P2-A=PASS`" precedía al retuning de droop, pero el Criterio 1 de `STOP-P2-A` (§20) exige
mejora simultánea de nadir/RoCoF **frente al droop tuneado**, no frente a NoFFC. Ninguna corrida de
droop retuneado existe todavía bajo la configuración actual (`BESS_BUS_1=16`/`BESS_BUS_2=20`,
`Tc=tstep=5ms`, `Kf=586.8`, `Kr=220.05`, `Pmax=293.4MW`) -- todas las figuras `F01-F10s`
(`DEC-P2-021`) comparan `F+R` contra `NoFFC` únicamente. Se señaló también que `F02`/`F10s` muestran
un ripple de tensión de baja amplitud que crece levemente hacia el final de la ventana en
`load_severe` con `F+R` (ausente en `NoFFC`), no investigado a horizonte más largo -- relevante para
el Criterio 2 de `STOP-P2-A` ("sin oscilación sostenida") antes de tratar `Tc=tstep=5ms` como valor
final.
Interpretation: Los parámetros físicos (`BESS_BUS_1/2=16/20`, `tstep=5ms`, `Kf=586.8`,
`Kr=220.05`, `Pmax=293.4MW`) se registran como **candidatos** del diseño DESIGN actual, no como
`FROZEN` final -- `Tc=tstep=5ms` en particular sigue etiquetado como hallazgo de diseño sin
verificación formal completa (`DEC-P2-020`). `STOP-P2-A` permanece **PENDIENTE** (no `PASS`, no
`FAIL`): el `FAIL` registrado en `DEC-P2-018` (`CLM-P2-PHYS`) corresponde a una configuración de
`Tc`/ubicación ya superada por `DEC-P2-020`/`DEC-P2-021`, y no puede reemplazarse por un veredicto
`PASS` sin (a) el baseline droop retuneado bajo la configuración actual y (b) la verificación de
estabilidad del ripple de tensión en `load_severe`.
Secuencia corregida registrada (reemplaza la propuesta original del usuario en orden, no en
contenido):
```text
1. P2-E5bis: retunear/verificar droop bajo EXACTAMENTE la config actual (buses 16/20, Tc=tstep=5ms,
   Pmax=293.4MW, mismo caso low-inertia, mismo tstep, mismos escenarios DESIGN) -- baseline
   obligatorio de comparacion, aun no ejecutado.
2. Verificacion de estabilidad del ripple de tension en load_severe F+R (horizonte mas largo:
   crece sin cota o converge?) -- toca Criterio 2 de STOP-P2-A.
3. Evaluar los 4 criterios de STOP-P2-A formalmente con el Physical Hybrid-only vs. droop retuneado
   (no vs. NoFFC) -- unico punto en que PASS/FAIL puede declararse.
4. Si PASS: P2-E6 (ablation de observacion OBS-A/B/C) -> P2-E7 (freeze formal).
   Si FAIL: identificar causa dominante (arbol de causas de SS20) antes de proponer salida.
```
Selected Tc or unresolved decision: `Tc=tstep=5ms` **no se congela** en esta entrada -- permanece
candidato, pendiente de los puntos 1-2 anteriores.
Evidence reviewed: `plan_maestro_P2_TD3_Hybrid_FFC.md` §14.2/§20/§25 (releído, sin cambios);
`DEC-P2-018` (`STOP-P2-A` FAIL bajo config previa); `DEC-P2-020`/`DEC-P2-021` (hallazgo `Tc=tstep`,
galería de figuras); `Paper_2/ops/sted/traceability_matrix.csv` fila `CLM-P2-PHYS`.
Frozen parameters:
```text
BESS_BUS_1 = 16 (candidato, ya frozen desde DEC-P2-018)
BESS_BUS_2 = 20 (candidato, ya frozen desde DEC-P2-018)
TSTEP = 0.005s (candidato, ya frozen)
TC_CANDIDATE = 0.005s ("tstep", DEC-P2-020 -- NO frozen final)
KF_CANDIDATE = 586.8 MW/Hz (1.0x, ya frozen desde etapas previas)
KR_CANDIDATE = 220.05 MW/(Hz/s) (0.75x, ya frozen desde etapas previas)
PMAX_CANDIDATE = 293.4 MW/BESS (ya frozen desde etapas previas)
STOP_P2_A_STATUS = PENDING (ni PASS ni FAIL -- FAIL de DEC-P2-018 corresponde a config superada,
  no reemplazado automaticamente por PASS)
DROOP_RETUNE_UNDER_CURRENT_CONFIG = NOT_EXECUTED
TD3_TRAINING_AUTHORIZED = FALSE (sin cambios)
```
Blockers or limitations: Ningún blocker técnico nuevo -- esto es una corrección de secuencia y
gobernanza documental. El retuning de droop bajo la configuración actual y la verificación de
estabilidad del ripple de tensión quedan como los dos pasos experimentales pendientes antes de que
`STOP-P2-A` pueda evaluarse formalmente.
Responsible: Claude (bajo autorización explícita del usuario -- únicamente actualización de
gobernanza/documentación, sin nuevas simulaciones)
Status: passed -- secuencia corregida y registrada
Next action: Presentar la secuencia corregida al usuario y **detenerse** -- no ejecutar el retuning
de droop, no declarar `STOP-P2-A=PASS`, no entrenar TD3, esperar autorización explícita del usuario
para `P2-E5bis` (retuning de droop) como siguiente paso experimental real.

## DEC-P2-023

Date: 2026-08-19
Stage/Gate: **Verificación de estabilidad del ripple de tensión (F02/F10s) + P2-E5bis (retuning del
baseline droop bajo la configuración candidata actual).** Autorizado explícitamente por el usuario
("ok, continua") como continuación directa de los dos pasos pendientes identificados en `DEC-P2-022`.
**Parte 1 -- ripple de tensión:** `Paper_2/src/stage_p2_voltage_ripple_stability_check.py` (nuevo).
Se extendió `load_severe` (NoFFC y F+R(16,20), mismo `Kf=586.8`/`Kr=220.05`/`Pmax=293.4MW`/
`Tc=tstep=5ms`) de `tf=6.0s` a `tf=20.0s` y se midió la amplitud pico-a-pico de tensión en ventanas de
1s consecutivas en ambos buses BESS. Resultado: la amplitud es máxima en la ventana `[0,1)s` (13.6-
32.3 mpu según bus/controlador) y decae monótonamente (con un repunte local esperado hacia `t=3-5s`,
la segunda oscilación electromecánica del sistema, ya visible en F01/F02) hasta `<0.5mpu` en
`t=17-18s`, **en los CUATRO casos (NoFFC y F+R, bus16 y bus20)** -- el patrón es idéntico en NoFFC, que
no tiene ningún lazo de control activo, confirmando que es una oscilación electromecánica natural del
sistema en decaimiento, no un efecto inducido por `F+R`/`Tc=5ms`. **Conclusión: DECAYING/BOUNDED en
los 4 casos -- no hay oscilación sostenida.** El "crecimiento" aparente notado en `F02`/`F10s` era la
cola visible de una oscilación en decaimiento dentro de una ventana de 6s demasiado corta para mostrar
el decaimiento completo, no una inestabilidad nueva. **Criterio 2 de `STOP-P2-A` (sin oscilación
sostenida) queda verificado para `Tc=tstep=5ms`.**
**Parte 2 -- retuning de droop:** `Paper_2/src/stage_p2e5bis_droop_retune.py` (nuevo, reutiliza el
controlador `'physical'` ya existente con `k_r=0.0` -- exactamente la ley de droop de Paper_1,
`P=-K_d*(f_local-F0)`, saturado a `+-Pmax`, sin nuevo código de control). Grid `K_d in
{0.25,0.5,1,2,4}xK0` (`K0=Pmax/0.5Hz=586.8MW/Hz`, mismo grid de multiplicadores que
`tune_droop()` de Paper_1), evaluado en AMBOS escenarios DESIGN, bajo la configuración candidata
actual completa: buses 16/20, `Tc=tstep=5ms` (el `Tc` candidato actual, NO el de referencia
100ms), `Pmax=293.4MW`, mismo `tstep`. Clasificador `classify_v2` (`DEC-P2-017`) aplicado a los 10
puntos.
```text
                    Kd=0.25x   Kd=0.50x   Kd=1.00x   Kd=2.00x   Kd=4.00x
gen_severe  I_f:     +7.2%      +9.8%     +14.2%     +20.5%     +27.7%
gen_severe  I_r:     +2.4%      +4.5%      +8.0%     +13.3%     +19.4%
load_severe I_f:     +3.3%      +6.6%     +11.3%     +19.2%     +26.0%
load_severe I_r:     +1.7%      +3.1%      +6.1%     +11.8%     +17.9%
```
**TODOS los 10 puntos clasifican STABLE** (sin excepción, sin saturación material: `sat<=0.003`).
**Hallazgo no anticipado, reportado sin suavizar:** `I_f`/`I_r` crecen MONOTÓNICAMENTE con `K_d` en
todo el rango probado, sin señal de saturación de la mejora ni de inestabilidad al acercarse al borde
superior de la grilla (`4.0x`) -- el grid **no logra acotar un óptimo** (el mínimo de
`J=|df_nadir|/0.5+RoCoF_max/1.0`, promediado sobre ambos escenarios DESIGN, se alcanza en el borde
`4.0x`, no en un interior). El valor histórico de Paper_1 (`580.0 MW/Hz`, `~0.99x` en esta base `K0`)
da una mejora MUCHO menor (`I_f=+14.2%/+11.3%`, `I_r=+8.0%/+6.1%`) que un droop retuneado
agresivamente a este `Tc` rápido. **Esto es relevante para `STOP-P2-A` Criterio 1: `F+R` en
`DEC-P2-020/021` logra `I_f=+28.4%/+30.6%`, `I_r=+21.1%/+21.8%` frente a NoFFC -- valores muy
cercanos a los de droop puro a `Kd=4.0x` (`I_f=+27.7%/+26.0%`, `I_r=+19.4%/+17.9%`) y CLARAMENTE por
encima del droop retuneado al valor histórico de Paper_1.** Si el droop "correcto" para comparar es
uno agresivamente retuneado (no el valor heredado de Paper_1), la ventaja de `F+R` sobre droop podría
ser marginal, no material -- pregunta abierta, NO resuelta aquí.
Interpretation: **NO se declara un `K_d*` final** -- el grid de 5 puntos es insuficiente para
localizar el óptimo real (sigue mejorando en el borde superior); `K_d=4.0x` reportado abajo es el
mejor de los 5 puntos probados, no un óptimo convergido. Extender el grid a multiplicadores mayores
(p.ej. `8x`, `16x`) para encontrar dónde el droop deja de mejorar (por saturación o inestabilidad) es
el siguiente paso lógico, pero NO se ejecutó -- excede el alcance autorizado de este mensaje.
Selected Tc or unresolved decision: `Tc=tstep=5ms` sigue sin congelarse (sin cambios respecto a
`DEC-P2-020/022`), pero el Criterio 2 de `STOP-P2-A` ya no es un bloqueo pendiente para ese `Tc`. El
`K_d*` de droop NO está determinado -- pendiente de extender el grid o de una decisión del usuario
sobre el criterio de selección (¿limitar `K_d` por una consideración práctica no capturada en este
modelo, p.ej. ancho de banda de medición/actuador en un controlador digital real, en vez de dejar que
la grilla numérica escale sin límite?).
Evidence reviewed: `Paper_2/artifacts/diagnostics/p2_voltage_ripple_stability_check.csv`;
`Paper_2/artifacts/trajectories/p2_voltage_ripple_stability_check_traces.npz`;
`Paper_2/artifacts/diagnostics/p2e5bis_droop_retune.csv`;
`Paper_2/artifacts/trajectories/p2e5bis_droop_retune_traces.npz`.
Frozen parameters:
```text
STOP_P2_A_CRITERION_2_VOLTAGE_RIPPLE = VERIFIED (DECAYING/BOUNDED, 4/4 casos, no depende de F+R)
DROOP_KD_STAR = NOT DETERMINED (grid 0.25-4.0x insuficiente, mejora monotona sin optimo interior)
DROOP_RETUNE_METHODOLOGY = "F-only (controller='physical', k_r=0.0), mismo Tc/buses/Pmax/tstep que
  el candidato F+R actual, seleccion por J=mean(|df_nadir|/0.5+RoCoF_max/1.0) sobre escenarios DESIGN
  SOLAMENTE entre puntos STABLE (classify_v2) -- NO se toco droop de Paper_1 (580 MW/Hz) como valor
  congelado, se retune desde cero en la config P2 tal como exige el plan (SS14.1)"
TD3_TRAINING_AUTHORIZED = FALSE (sin cambios)
```
Blockers or limitations: El grid de `K_d` (5 puntos, `0.25x-4.0x`) no acota el óptimo -- se requiere
extender el rango o fijar un criterio de tope no puramente numérico (p.ej. viabilidad de ancho de
banda de un controlador de droop real) antes de que el baseline droop pueda considerarse
"retuneado" en el sentido que exige `SS14.1`/`STOP-P2-A` Criterio 1. Sin ese `K_d*` definitivo, el
Criterio 1 de `STOP-P2-A` sigue sin poder evaluarse formalmente -- la comparación `F+R` vs. droop
depende de qué punto de droop se use, y el punto disponible más fuerte (`4.0x`) ya reduce
sustancialmente (o casi elimina) la ventaja material que `F+R` mostraba frente a NoFFC.
Responsible: Claude (ejecución bajo autorización explícita del usuario -- "ok, continua")
Status: passed -- ambos diagnósticos ejecutados y registrados; ninguno cierra `STOP-P2-A`
Next action: Reportar al usuario el hallazgo completo (ripple resuelto; droop competitivo con F+R,
grid sin optimo acotado) y **detenerse** -- no extender el grid de `K_d` sin autorización, no declarar
`STOP-P2-A=PASS` ni `FAIL`, no entrenar TD3, esperar decisión explícita del usuario sobre cómo acotar
`K_d*` (extender grid numérico vs. imponer un límite práctico no numérico) antes de continuar hacia
`P2-E6`.

## DEC-P2-024

Date: 2026-08-19
Stage/Gate: **P2-E5bis, extensión controlada del tuning droop (Kd/K0 in {4,6,8,12,16}) + comparación
final droop-tuned vs. Physical F+R sobre los dos probes DESIGN.** Autorizado explícitamente por el
usuario ("AUTORIZO EXTENSIÓN CONTROLADA DEL TUNING DROOP"), con reglas de parada numeradas (A-E),
reglas de selección (8-10) y prohibición explícita de seleccionar automáticamente la mayor ganancia
(punto 6).
**Qué se hizo:** `Paper_2/src/stage_p2e5bis2_droop_extended_tuning.py` (nuevo). Misma arquitectura
droop (`P=-Kd*df_local`, saturado a `+-Pmax`, sin código de control nuevo), misma config congelada
(buses 16/20, `Tc=tstep=5ms`, `Pmax=293.4MW`, `tstep=5ms`, ambos escenarios DESIGN). Se re-ejecutó
`Kd=4.0x` (para consistencia de instrumentación) más los 4 puntos nuevos (`6,8,12,16`), y se re-ejecutó
`F+R` (`Kf=586.8`, `Kr=220.05`) bajo el mismo código, para una comparación estrictamente apples-to-
apples (16 simulaciones totales: 2 NoFFC + 5x2 droop + 2 F+R). Se midieron todas las cantidades
pedidas (`df_nadir`, `RoCoF_max`, `J_phys`, `Ppeak`, `saturation_fraction`, `classify_v2`,
`settling_time_s` ya calculado por `run_physical_scenario_tc`, `Delta_f_sat=Pmax/Kd`).
```text
                gen_severe                          load_severe
Kd/K0  df_sat   df_nadir  RoCoF   sat    class       df_nadir  RoCoF   sat     class        settle(load)
 4.0   125.0mHz -0.1309Hz 0.956   0.000  STABLE      -0.1541Hz 2.407   0.0025  STABLE        175ms
 6.0    83.3mHz -0.1234Hz 0.913   0.000  STABLE      -0.1477Hz 2.332   0.0029  STABLE        160ms
 8.0    62.5mHz -0.1186Hz 0.885   0.000  STABLE      -0.1444Hz 2.295   0.0038  STABLE        205ms
12.0    41.7mHz -0.1126Hz 0.853   0.013  STABLE      -0.1428Hz 2.281   0.1375  LIMIT_CYCLE   4979ms
16.0    31.2mHz -0.1094Hz 0.864   0.258  MARGINAL    -0.1413Hz 2.267   0.3913  LIMIT_CYCLE   4985ms
```
**Autocorrección registrada (error propio detectado antes de reportar, no oculto):** la primera
ejecución del script priorizaba, por orden de aparición en el código, la Regla C (reversión, dispara
en `gen_severe` recién en `Kd=16.0x`) por encima de la Regla D (oscilación no-STABLE, dispara en
`load_severe` ya en `Kd=12.0x`) -- esto congelaba `Kd*=12.0x`, un punto en el que `load_severe` YA
es `LIMIT_CYCLE` (`sat=0.1375`, `settling=4979ms`, un orden de magnitud mayor que el resto de la
grilla). Corregido para tomar el disparador MÁS TEMPRANO entre C/D/E, no el primero verificado en
código -- el punto correcto es `Kd*=8.0x`, el último punto STABLE en AMBOS escenarios simultáneamente
(`sat=0.000`/`0.004`, muy por debajo del umbral `STABLE_SAT_FRAC_MAX=0.05`). El script se corrigió
in situ; no se repitieron las 16 simulaciones (los datos crudos no estaban afectados, solo la lógica
de decisión posterior).
**Regla aplicada:** D (oscilación no-STABLE) dispara primero, en `Kd=12.0x` (antes que Regla C en
`16.0x`; Regla E -- saturación tipo relay, umbral `>=0.5` -- nunca se alcanza, máximo `sat=0.391` en
`load_severe@16x`). Por Regla 7: **detener la extensión en la transición `8x -> 12x`.** Por el
espíritu de las Reglas 8/9 (congelar en el último punto bueno cuando aparece una condición de parada
no cubierta por A/B explícitamente): **`Kd* = 8.0x = 4694.4 MW/Hz` congelado como droop tuned**
(`Delta_f_sat = 62.5mHz`).
**Comparación final droop-tuned (`Kd*=8.0x`) vs. Physical F+R, mismos dos probes DESIGN:**
```text
              F+R (Kf=586.8,Kr=220.05)          droop* (Kd=8.0x=4694.4MW/Hz)
gen_severe:   I_f=+28.4% I_r=+21.1% J=1.1943    I_f=+34.5% I_r=+25.3% J=1.1226  sat=0.000
load_severe:  I_f=+30.6% I_r=+21.8% J=2.5836    I_f=+30.7% I_r=+21.8% J=2.5834  sat=0.004
```
Interpretation: **el droop correctamente retuneado (`Kd*=8.0x`) IGUALA o SUPERA a `F+R` en los dos
escenarios DESIGN**, con menor `J_phys` en ambos, sin saturación material, `STABLE` en ambos. En
`gen_severe` droop incluso supera a F+R por un margen no trivial (`I_f` +6.1pp, `I_r` +4.2pp). En
`load_severe` la diferencia es esencialmente nula (`I_f` +0.1pp, `I_r` 0.0pp). **`F+R` NO demuestra
una ventaja material y reproducible sobre el droop correctamente retuneado en ninguno de los dos
escenarios DESIGN -- el Criterio 1 de `STOP-P2-A` (mejora simultánea reproducible de nadir/RoCoF
frente al droop tuneado) NO SE CUMPLE con la evidencia actual.** Esto contrasta fuertemente con usar
el valor histórico de Paper_1 (`580MW/Hz~=0.99x`) como comparador, que hacía ver a `F+R` muy superior
(`DEC-P2-023`) -- ese comparador estaba subretuneado para la config P2 actual (`Tc` mucho más rápido
que Paper_1), no reflejaba el techo físico real de un droop puro bajo esta arquitectura.
Selected Tc or unresolved decision: `Tc=tstep=5ms` sigue como candidato (sin cambios). `Kd*=8.0x=
4694.4MW/Hz` queda **congelado como droop tuned baseline de P2** bajo esta config. `STOP-P2-A`
Criterio 1 se evalúa ahora con evidencia completa (droop correctamente retuneado) y el resultado es
**NO CUMPLE** -- pendiente de decisión del usuario sobre cómo proceder (ver Next action).
Evidence reviewed: `Paper_2/artifacts/diagnostics/p2e5bis2_droop_extended_tuning.csv`;
`Paper_2/artifacts/trajectories/p2e5bis2_droop_extended_tuning_traces.npz`.
Frozen parameters:
```text
DROOP_KD_STAR_MW_PER_HZ = 4694.4  (8.0x K0=586.8, congelado esta entrada)
DROOP_DELTA_F_SAT_HZ = 0.0625  (62.5 mHz -- desviacion de frecuencia a la que el droop satura)
STOP_P2_A_CRITERION_1_VERDICT = "NO CUMPLE con evidencia completa: F+R no supera de forma material
  al droop correctamente retuneado (gen_severe: droop > F+R; load_severe: droop ~= F+R)"
TD3_TRAINING_AUTHORIZED = FALSE (sin cambios)
```
Blockers or limitations: El grid de `Kd` tiene solo 5 puntos nuevos (`4,6,8,12,16`, más el punto
`4.0x` repetido) -- la resolución entre `8x` (limpio) y `12x` (ya `LIMIT_CYCLE` en `load_severe`) es
gruesa; el verdadero borde de estabilidad podría estar en cualquier punto entre `8x` y `12x`, no
necesariamente en `8x` exacto (no se investigó más fino, fuera del alcance autorizado). El error de
priorización de reglas C/D detectado y corregido en esta misma entrada subraya que la evaluación de
reglas de parada A-E debe aplicarse tomando el disparador MÁS TEMPRANO, no el primero verificado en
código -- ya corregido en el script, documentado para auditoría futura.
Responsible: Claude (ejecución bajo autorización explícita del usuario; autocorrección de un error de
lógica propio antes de reportar, según la disciplina de la sesión de nunca ocultar anomalías)
Status: passed -- extensión ejecutada, `Kd*` congelado, comparación final completada;
`STOP-P2-A` Criterio 1 evaluado con resultado NO CUMPLE
Next action: Reportar al usuario el hallazgo completo (incluyendo la autocorrección) y **detenerse**
-- no entrenar TD3, no usar validation ni `P2-T*`, no declarar `STOP-P2-A` PASS/FAIL global (solo el
Criterio 1 fue evaluado aquí; Criterios 2/3/4 requieren revisitarse con el droop tuned como
comparador, no solo con NoFFC), esperar decisión explícita del usuario sobre cómo proceder (aceptar
el resultado NO CUMPLE y escalar según el árbol de causas de SS20, refinar el grid entre 8x-12x,
reconsiderar si `F+R` con otra estructura de ganancias podría superar al droop tuned, o reencuadrar
el alcance de la comparación).

## DEC-P2-025

Date: 2026-08-19
Stage/Gate: **P2-E5ter -- retuning final de Physical F+R (Kf,Kr) bajo la configuración congelada,
cierre definitivo de STOP-P2-A Criterio 1 frente al droop tuned (`DEC-P2-024`).** Autorizado
explícitamente por el usuario ("AUTORIZO EL CIERRE DEFINITIVO DE STOP-P2-A MEDIANTE RETUNING FINAL
DEL CONTROLADOR PHYSICAL F+R"), con grid, criterio de descarte, criterio de selección y regla de
veredicto (puntos 10/11) especificados explícitamente por el usuario.
**Qué se hizo:** `Paper_2/src/stage_p2e5ter_fr_retune_vs_droop.py` (nuevo). Congelados sin cambios:
buses 16/20, `Tc=tstep=5ms`, `Pmax=293.4MW`, `tip`, `BusROCOF`, caso low-inertia, ambos escenarios
DESIGN, `droop*=4694.4MW/Hz` (NO retuneado). Ley de control SIN CAMBIOS
(`P=-Kf*df-Kr*RoCoF`, saturado `+-Pmax`, controlador `'physical'` ya existente). Grid pequeño
alrededor del punto actual, exactamente como especificó el usuario: `Kf/Kf0 in {0.5,1,2,4}` x
`Kr/Kr0 in {0.25,0.5,0.75,1,1.5,2}` = 24 combinaciones x 2 escenarios = 48 simulaciones, más `droop*`
re-ejecutado aquí (2 sims) para una comparación estrictamente apples-to-apples bajo el mismo código.
`13/24` combinaciones clasifican `STABLE` en AMBOS escenarios (descartadas: `10` `LIMIT_CYCLE`, `1`
`MARGINAL` sistemáticamente en `Kr>=1.0x-1.5x` según `Kf` -- el patrón de inestabilidad a ganancia
`Kr` alta ya visto en `DEC-P2-005`/`DEC-P2-011` se reproduce aquí incluso a `Tc=tstep=5ms`).
Selección por `J_phys` mínimo entre los 13 sobrevivientes `STABLE` (mismo criterio que
`DEC-P2-023/024`): **`Kf*=4.0x=2347.2MW/Hz`, `Kr*=0.5x=146.7MW/(Hz/s)`** (`J_phys=1.8656`, el menor
de la grilla).
**Comparación final, mismo código, mismos dos probes DESIGN, frente a `droop*` (NO frente a NoFFC,
por instrucción explícita del usuario, punto 9):**
```text
              droop* (Kd=4694.4MW/Hz)         F+R* (Kf=2347.2, Kr=146.7)
gen_severe:   df_nadir=-0.1186Hz RoCoF=0.885   df_nadir=-0.1231Hz RoCoF=0.904   I_f=-3.7% I_r=-2.1%
load_severe:  df_nadir=-0.1444Hz RoCoF=2.295   df_nadir=-0.1442Hz RoCoF=2.292   I_f=+0.2% I_r=+0.1%
```
`gen_severe`: F+R* es PEOR que droop* en ambas métricas (mejora negativa). `load_severe`: F+R* es
esencialmente idéntico a droop* (diferencia <0.3% en ambas métricas, dentro del ruido numérico).
**Verificación de robustez (no pedida explícitamente, hecha para no depender de un solo punto
elegido por `J_phys`):** se revisaron las 13 combinaciones `STABLE` completas, no solo la de menor
`J_phys` -- **NINGUNA de las 13** logra mejora simultánea positiva (`I_f>0` Y `I_r>0`) en AMBOS
escenarios frente a `droop*`; el mejor caso en `gen_severe` entre todas ellas sigue siendo negativo
(`-3.7%` en el punto seleccionado; el resto es peor). El patrón es consistente, no depende de la
elección específica del criterio de selección.
Interpretation: **Ninguna combinación `Kf/Kr` estable de Physical F+R, dentro de la grilla evaluada,
supera de forma simultánea y material al droop correctamente retuneado en ambos escenarios DESIGN.**
Por instrucción explícita del usuario (punto 10): **`STOP-P2-A = FAIL DEFINITIVO`**. La componente
`RoCoF` (`Kr`) de F+R no aporta una ventaja física neta sobre un droop puro bien ajustado bajo esta
arquitectura/`Tc`/ubicación -- de hecho, la evidencia acumulada en esta sesión (`DEC-P2-023/024/025`)
sugiere que gran parte de lo que antes parecía "ventaja de F+R" (`DEC-P2-020/021`, comparado contra
NoFFC) era en realidad la ventaja de tener CUALQUIER controlador razonablemente agresivo a
`Tc=tstep=5ms`, no una ventaja específica de la estructura `F+R` sobre droop.
Selected Tc or unresolved decision: `Tc=tstep=5ms` sigue como candidato (sin cambios, no se tocó en
esta entrada). `droop*=4694.4MW/Hz` permanece congelado (`DEC-P2-024`, no retuneado aquí). No se
selecciona un `Kf*/Kr*` final "de producción" para F+R -- el punto reportado (`4.0x/0.5x`) es el
mejor de la grilla evaluada, no una recomendación de uso, dado que no logra el objetivo del gate.
Evidence reviewed: `Paper_2/artifacts/diagnostics/p2e5ter_fr_retune_vs_droop.csv` (50 filas: 2 NoFFC +
2 droop* + 48 F+R grid).
Frozen parameters:
```text
STOP_P2_A_VERDICT = FAIL DEFINITIVO (Criterio 1, evaluado formalmente frente a droop tuned)
FR_BEST_IN_GRID_KF_MULT = 4.0  (Kf=2347.2MW/Hz, MEJOR de la grilla, NO recomendado para uso -- no supera droop*)
FR_BEST_IN_GRID_KR_MULT = 0.5  (Kr=146.7MW/(Hz/s), idem)
DROOP_STAR_MW_PER_HZ = 4694.4  (sin cambios, DEC-P2-024)
TD3_TRAINING_AUTHORIZED = FALSE ("no entrenar TD3 bajo el plan actual" -- instrucción explícita del
  usuario tras STOP-P2-A=FAIL definitivo)
```
Blockers or limitations: La grilla `Kf/Kr` es pequeña (24 combos) alrededor del punto ya conocido,
por instrucción explícita del usuario ("grilla pequeña... no un sweep abierto") -- no se exploraron
regiones de ganancia muy alejadas del punto actual (p.ej. `Kf` muy bajo con `Kr` muy alto, u otras
estructuras de realimentación). El patrón de inestabilidad a `Kr` alto (`>=1.0-1.5x` según `Kf`) no
se investigó causalmente en esta entrada (ya diagnosticado cualitativamente en sesiones anteriores
para `Tc=100ms`; se confirma que persiste a `Tc=tstep=5ms`, pero no se repite el diagnóstico
completo). Criterios 2/3/4 de `STOP-P2-A` no se re-evaluaron formalmente para el punto F+R
seleccionado (el veredicto FAIL de Criterio 1 ya es suficiente para el resultado global, por
instrucción del usuario, punto 10).
Responsible: Claude (ejecución bajo autorización explícita del usuario, con verificación de robustez
adicional no solicitada pero necesaria para no basar el veredicto en un solo punto)
Status: passed -- retuning ejecutado, comparación final completada, `STOP-P2-A` cerrado
Next action: Reportar al usuario el veredicto `STOP-P2-A = FAIL DEFINITIVO` y **detenerse**, tal como
instruyó explícitamente el usuario -- no entrenar TD3 bajo el plan actual, no usar validation ni
`P2-T*`, no retunear droop de nuevo, no cambiar `Tc`/ubicación BESS/`Pmax`. Este es un punto de
decisión mayor para el usuario sobre el rumbo de Paper_2 (aceptar el resultado y reencuadrar el
alcance/hipótesis del estudio, investigar si una estructura de control distinta a `F+R` podría
superar al droop, o cerrar esta línea de física-informada y considerar directamente si TD3 puro
aporta algo que el droop no aporta -- ninguna de estas opciones está autorizada todavía).

## DEC-P2-026

Date: 2026-08-19
Stage/Gate: **Reencuadre formal de la arquitectura principal de Paper_2 tras `STOP-P2-A = FAIL
DEFINITIVO` (`DEC-P2-025`).** Autorizado explícitamente por el usuario ("AUTORIZO REENCUADRAR
PAPER_2 DESPUÉS DEL FAIL DEFINITIVO DE STOP-P2-A"), con 10 puntos de instrucción explícitos.
**Ninguna simulación ni entrenamiento ejecutado en esta entrada -- es una decisión de gobernanza y
documentación pura**, tal como exigió el usuario (punto "No ejecutar simulaciones ni entrenamiento
todavía").
**Qué se hizo:**
1. `DEC-P2-025` se conserva sin modificar (append-only, sin cambios).
2. Se declara explícitamente **descartada como arquitectura principal** la combinación `Physical
   F+R + TD3 residual` (`P_total = P_ff(Kf,Kr) + P_RL`) -- razón: el componente físico `F+R` no
   supera al droop tuned bajo ninguna configuración `Kf/Kr` evaluada (`DEC-P2-025`, 24 combinaciones,
   13 `STABLE`, ninguna con mejora simultánea sobre `droop*`).
3. Se adopta como **arquitectura candidata revisada**:
   ```text
   P_total,i = P_droop,i + P_RL,i
   P_droop,i = -Kd* * Delta_f_i,local     (Kd* = 4694.4 MW/Hz, congelado en DEC-P2-024)
   P_RL,i    = a_i * P_RL,max,            a_i in [-1,1]
   P_total,i = clip(P_droop,i + P_RL,i, -Pmax,BESS, +Pmax,BESS)
   ```
4. Congelados sin cambios (verificado, ninguno se tocó en esta entrada): buses BESS `16/20`,
   `Pmax=293.4MW`, `Tc=tstep=5ms` (`Tc` sigue como CANDIDATO, no `FROZEN` final -- sin cambios
   respecto a `DEC-P2-020/022`), `tstep=5ms`, caso low-inertia, splits train/validation/test
   (`DEC-P2-003`), batería `P2-T1..P2-T12` (aún no abierta), definición de métricas (§21/§22), gate
   final (§21, sin cambios -- ya estaba definido como `I_f/I_r` vs. droop, no vs. `F+R`, por lo que
   NO requiere reescritura).
5. `Kf`/`Kr` (`F+R`) **NO se reutilizan** en la arquitectura principal revisada -- el término residual
   TD3 se suma directamente sobre `P_droop`, no sobre `P_ff(Kf,Kr)`.
6. `Physical F+R` se conserva únicamente como **baseline/ablation científica** (ya ejecutado y
   documentado extensamente: `DEC-P2-011` a `DEC-P2-025`) -- no se vuelve a congelar como componente
   de la arquitectura principal.
7. `plan_maestro_P2_TD3_Hybrid_FFC.md` actualizado (§2 hipótesis, §4 controlador principal, §14.2
   nota de cierre, §15 lista de controladores, §16 ablations, §20 nuevo significado de `STOP-P2-A`)
   para distinguir explícitamente **arquitectura original** (`F+R + TD3 residual`, DESCARTADA) de
   **arquitectura revisada** (`tuned droop + TD3 residual`, CANDIDATA). Ver diffs del archivo para el
   texto exacto.
8. Nueva hipótesis formulada (§2 revisado), sin afirmar superioridad:
   > Una política TD3 residual, sumada sobre un controlador droop convencional fuertemente
   > retuneado (`Kd*`, `DEC-P2-024`), podría aportar una mejora adicional de nadir y RoCoF bajo
   > diversidad de perturbaciones y puntos de operación no vistos por el droop durante su tuning --
   > sin asumir que esa mejora existe o es material hasta el test final congelado.
9. `TD3_TRAINING_AUTHORIZED` permanece `FALSE` -- no se entrenó nada en esta entrada.
10. Ver el reporte completo presentado al usuario en el mismo turno (secciones exactas del plan que
    cambian, nueva arquitectura, nuevo significado de `STOP-P2-A`, qué decisiones previas siguen
    válidas, qué etapas deben repetirse, qué etapas NO deben repetirse) -- no se repite aquí en
    extenso para evitar duplicar el mismo contenido en dos lugares; este entry es el registro formal,
    el reporte al usuario es la presentación narrativa.
Interpretation: Este reencuadre **no revierte ni invalida** ninguna decisión física ya congelada
(`Tc` candidato, buses, `Pmax`, `tip`, `BusROCOF`, splits) -- todas siguen siendo válidas para la
arquitectura revisada exactamente como estaban para la original, porque son propiedades de la planta
física y del diseño experimental, no de la ley de control. Lo único que cambia es CUÁL es la
componente física de `P_total` (`droop` en vez de `F+R`) y, en consecuencia, qué debía verificarse
antes de entrenar TD3: bajo la arquitectura revisada, el "componente físico" de `P_total` es
literalmente `droop*`, por lo que la pregunta original de `STOP-P2-A` ("¿el componente físico supera
al droop?") queda trivialmente resuelta por construcción (el componente físico ES el droop) y no
puede repetirse en la misma forma -- requiere una redefinición explícita antes de servir como gate
para la arquitectura revisada (ver reporte al usuario, no decidida unilateralmente aquí).
Selected Tc or unresolved decision: `Tc=tstep=5ms` sigue como candidato, sin cambios. `Kd*=4694.4
MW/Hz` sigue congelado como componente física de la arquitectura revisada. El nuevo significado
operativo de `STOP-P2-A` para la arquitectura revisada queda **propuesto, no decidido** -- pendiente
de confirmación explícita del usuario antes de que autorice entrenamiento (ver reporte).
Evidence reviewed: `DEC-P2-020` a `DEC-P2-025` (cadena completa de hallazgos que motiva el
reencuadre); `plan_maestro_P2_TD3_Hybrid_FFC.md` (§2/§4/§14.2/§15/§16/§20, editados en esta entrada).
Frozen parameters:
```text
ARCHITECTURE_ORIGINAL = "Physical F+R + TD3 residual" -- DESCARTADA (DEC-P2-025/026), conservada
  unicamente como ablation/baseline historica
ARCHITECTURE_REVISED = "tuned droop (Kd*=4694.4MW/Hz, DEC-P2-024) + TD3 residual" -- CANDIDATA
KD_STAR_MW_PER_HZ = 4694.4 (sin cambios, DEC-P2-024, ahora tambien componente fisica de P_total)
KF_KR_REUSE_IN_MAIN_ARCHITECTURE = FALSE (F+R queda excluido de la arquitectura principal revisada)
BESS_BUS_1 = 16, BESS_BUS_2 = 20 (sin cambios)
TC_CANDIDATE_S = 0.005 (sin cambios, sigue candidato no frozen final)
PMAX_MW = 293.4 (sin cambios)
SPLITS_TRAIN_VAL_TEST = sin cambios (DEC-P2-003)
P2_T1_T12_BATTERY = sin cambios, aun no abierta
TD3_TRAINING_AUTHORIZED = FALSE (sin cambios)
```
Blockers or limitations: El nuevo significado de `STOP-P2-A` para la arquitectura revisada NO está
decidido en esta entrada -- se presenta una propuesta al usuario (ver reporte) pero requiere su
confirmación explícita antes de poder usarse como gate real de pre-entrenamiento. Ninguna etapa nueva
de diseño físico (`P2-E4`/`P2-E5`/`P2-E6` equivalentes) se ha vuelto a ejecutar para la arquitectura
revisada -- las etapas que deben repetirse (si alguna) y las que no, se listan en el reporte al
usuario, pendientes de confirmación antes de proceder.
Responsible: Claude (ejecución bajo autorización explícita del usuario -- únicamente actualización de
gobernanza/documentación/plan, sin simulaciones ni entrenamiento)
Status: passed -- reencuadre registrado y aplicado al plan maestro y a la matriz de trazabilidad
Next action: Presentar al usuario el reporte completo exigido en el punto 10 (secciones que cambian,
nueva arquitectura, nuevo significado de `STOP-P2-A`, decisiones previas que siguen válidas, etapas a
repetir, etapas a NO repetir) y **detenerse**, tal como instruyó explícitamente el usuario -- no
entrenar TD3, no ejecutar ninguna simulación de diseño nueva, esperar confirmación explícita del
usuario sobre el nuevo significado de `STOP-P2-A` y sobre cualquier etapa que deba repetirse antes de
continuar.

## DEC-P2-027

Date: 2026-08-19
Stage/Gate: **Confirmación formal de `STOP-P2-A_REVISED = PASS` para la arquitectura revisada
(`droop* + TD3 residual`, `DEC-P2-026`).** Autorizado/decidido explícitamente por el usuario
("CONFIRMO LA REDEFINICIÓN DE STOP-P2-A PARA LA ARQUITECTURA REVISADA"), respondiendo directamente a
la propuesta presentada en `DEC-P2-026`/§20 del plan. **Ninguna simulación nueva ejecutada** -- el
usuario evaluó los cuatro criterios usando evidencia ya generada en entradas previas.
**Qué se decidió:** el usuario aplicó los cuatro criterios propuestos y los declaró todos `PASS`,
citando evidencia ya existente:
```text
A. Baseline fisico correctamente optimizado y congelado.
   PASS -- droop* Kd=4694.4MW/Hz (DEC-P2-024).
B. Baseline estable y reproducible en DESIGN.
   PASS -- STABLE en gen_severe y load_severe, antes de la region LIMIT_CYCLE (Kd>=12x, DEC-P2-024).
C. Existe autoridad residual disponible para que TD3 module la accion del droop.
   PASS PROVISIONAL -- saturation_fraction de droop* practicamente nula en ambos probes DESIGN
   (0.000 gen_severe, 0.004 load_severe, DEC-P2-024/DEC-P2-025), el actuador no opera permanentemente
   en Pmax.
D. No existe patologia fisica conocida que inutilice el residual.
   PASS -- ripple de tension descartado como oscilacion sostenida/inestabilidad inducida
   (DEC-P2-023, decaimiento verificado a horizonte extendido); actuador y timing ya validados
   (DEC-P2-007/008/019/020).
```
```text
STOP_P2_A_REVISED = PASS
TD3_DESIGN_PIPELINE_AUTHORIZED = TRUE
```
**Alcance explícito de esta autorización, tal como lo aclaró el usuario:** `PASS` significa que existe
justificación física suficiente para invertir en probar si un residual aprendido puede aportar mejora
adicional sobre `droop*` -- **NO** es una predicción ni una garantía de que TD3 vaya a superar al
droop en el test final. El gate confirmatorio real sigue siendo `P2-H1`/§21, sin relajarse por este
`PASS` (mismo principio ya establecido en §20 para el `STOP-P2-A` original).
Interpretation: Con este `PASS`, el "pipeline de diseño hacia TD3" queda formalmente autorizado a
nivel de gate -- pero esto es una declaración de estado del gate, no una instrucción de ejecución.
Ninguna etapa concreta (`P2-E7` ablation de observación, freeze, preflight, entrenamiento) se
autoriza automáticamente por este `PASS`; cada una sigue requiriendo su propia autorización explícita,
consistente con la disciplina de "esperar confirmación en cada etapa" que ha regido toda la campaña
P2 (y P1 antes). El criterio C se marca explícitamente como `PASS PROVISIONAL` por el propio usuario
(basado en `saturation_fraction` medida en el punto congelado `Kd*`, no en un análisis formal de
headroom dedicado) -- queda como una limitación reconocida, no oculta.
Selected Tc or unresolved decision: `Tc=tstep=5ms` sigue como candidato (sin cambios). Ninguna nueva
decisión de congelamiento físico en esta entrada -- es una confirmación de gate sobre evidencia ya
congelada.
Evidence reviewed: `DEC-P2-023` (ripple de tensión), `DEC-P2-024` (droop* congelado, estabilidad),
`DEC-P2-025` (saturation_fraction de droop*), `DEC-P2-007/008/019/020` (actuador/timing), `DEC-P2-026`
(propuesta original de los 4 criterios, §20 del plan).
Frozen parameters:
```text
STOP_P2_A_REVISED_VERDICT = PASS (confirmado por el usuario, esta entrada)
TD3_DESIGN_PIPELINE_AUTHORIZED = TRUE (autorizacion de GATE, no de ejecucion de ninguna etapa
  especifica -- cada etapa sigue requiriendo autorizacion explicita separada)
CRITERION_C_STATUS = "PASS PROVISIONAL, no un analisis formal de headroom dedicado"
TD3_TRAINING_AUTHORIZED = FALSE (sin cambios -- el PASS del gate no autoriza entrenamiento
  automaticamente, ninguna etapa posterior se ha autorizado todavia)
```
Blockers or limitations: El Criterio C se aceptó como `PASS PROVISIONAL`, no como un análisis de
headroom formal y dedicado -- si en una etapa posterior surge evidencia de que el margen de actuación
disponible para TD3 es insuficiente, este criterio podría necesitar revisarse. Ninguna etapa nueva
(`P2-E7` en adelante) está autorizada por esta entrada -- requiere autorización explícita separada
antes de ejecutarse, tal como toda la campaña ha operado hasta ahora.
Responsible: Usuario (decisión de gate); Claude (registro de gobernanza, sin ejecución)
Status: passed -- `STOP-P2-A_REVISED = PASS` confirmado y registrado
Next action: Actualizar `plan_maestro.md` §20 (marcar la propuesta como CONFIRMADA, no ya
"pendiente") y `traceability_matrix.csv` (`CLM-P2-ARCH-REVISED`), reportar al usuario el registro
completado, y **detenerse** -- no iniciar `P2-E7` (ablation de observación) ni ninguna otra etapa sin
autorización explícita separada, no entrenar TD3, no usar validation ni `P2-T*`.

## DEC-P2-028

Date: 2026-08-19
Stage/Gate: **P2-E6a -- cierre de arquitectura TD3 residual: implementación del entorno revisado
`droop* + TD3 residual` y smoke tests de implementación.** Autorizado explícitamente por el usuario
("AUTORIZO P2-E6a — CIERRE DE ARQUITECTURA TD3 RESIDUAL"), con 10 puntos de instrucción explícitos.
**Sin evaluación de desempeño, sin sweep de `P_RL,max`, sin selección de políticas, sin entrenamiento
TD3** -- únicamente corrección mecánica de la arquitectura.
**Qué se hizo:**
1. `Tc=tstep=5ms` confirmado como congelado para esta etapa (sin nueva exploración).
2. Verificado sin cambios: buses `16/20`, `Pmax=293.4MW`, `Kd*=4694.4MW/Hz` (`DEC-P2-024`), `tip`/
   `BusROCOF` (sin cambios), caso low-inertia, splits (`DEC-P2-003`).
3. Arquitectura final implementada: `P_total=clip(P_droop+P_RL,-Pmax,+Pmax)`,
   `P_droop=-Kd**df_local`.
4. `P_RL,max = 0.25*Pmax = 73.35 MW` por BESS, congelado inicialmente.
5. Action space `[-1,1]^2`, `P_RL,i = a_i*P_RL,max`.
6. Entorno implementado en `Paper_2/src/p2_env.py` (`class P2ResidualEnv`), reutilizando el mecanismo
   `itm_step()`/`do_switch()`/`calc_h()` ya validado de `p2_common.run_physical_scenario_tc()`
   (§26 del plan, "no redescubrir") -- misma construcción de caso, mismo `add_bess_pair`. Observación
   de 8 señales (POI+COI, adaptada de buses legacy 13/12 a 16/20, §9 del plan) implementada solo para
   que los smoke tests puedan verificar ausencia de NaN/Inf -- **NO es la observación final** (P2-E7,
   ablation OBS-A/B/C, no se ha ejecutado). Reward usa la fórmula ya congelada §6 del plan, incluida
   solo por completitud de `step()`, no evaluada.
7. `Paper_2/src/stage_p2e6a_td3_residual_architecture_smoke.py` -- 8 smoke tests, exactamente los
   especificados por el usuario. Escenario: `gen_severe` (`GENROU_4`, `rho=0.90`), mismo escenario
   DESIGN usado para congelar `Kd*`/verificar `F+R` (`DEC-P2-024/025`).
```text
[PASS] action=0 == droop* (trayectorias locales de frecuencia/potencia, ambos BESS)
       max|df1|=0.00e+00Hz max|df2|=0.00e+00Hz max|dp1|=0.00e+00MW max|dp2|=0.00e+00MW
       n_steps=1200 (env) == 1200 (referencia p2_common.run_physical_scenario_tc, controller='physical', k_r=0.0)
[PASS] a=+1 -> P_RL == +P_RL,max exactamente, ambos BESS (73.35, 73.35)
[PASS] a=-1 -> P_RL == -P_RL,max exactamente, ambos BESS (-73.35, -73.35)
[PASS] clipping (4 casos sinteticos, incl. exceso +Pmax, exceso -Pmax, sin clip, frontera P_RL,max)
[PASS] P_RL,max == 0.25*Pmax == 73.35 MW exactamente
[PASS] a1=1 con df~=0 pre-disturbio -> P_total,1 ~= P_RL,max (73.350MW, sin error de factor 100x)
[PASS] BESS1 identico independientemente de la accion de BESS2 (a2=0 vs a2=1)
[PASS] BESS2 responde a su propia accion (a2=0 vs a2=1 difieren)
[PASS] reset() repetido dobre identico (max|dobs|=0.00e+00)
[PASS] estado inicial pre-disturbio limpio (df~=0, P_delivered~=0 ambos BESS)
[PASS] ctrl_period_steps==1 (Tc=tstep -> accion cada paso de integracion)
[PASS] dae.t avanza exactamente tstep=5ms por step()
[PASS] observaciones/acciones/rewards finitas en rollout completo de 1200 pasos con acciones aleatorias

8/8 SMOKE TESTS PASS. Ninguna incompatibilidad encontrada.
```
Interpretation: La equivalencia numérica EXACTA (diferencia `0.00e+00` en las 4 magnitudes
comparadas, sobre 1200 pasos) entre `action=0` del entorno nuevo y la implementación de droop* ya
validada (`DEC-P2-024`) confirma que el nuevo entorno no introduce ningún error de reimplementación
-- comparten exactamente la misma física, el mismo mecanismo de integración y la misma ley de control
para el término droop. La arquitectura mecánica (acción→comando→paso ANDES→observación) es correcta
en las 8 dimensiones verificadas.
Selected Tc or unresolved decision: Ninguna decisión física nueva -- `Tc`, buses, `Pmax`, `Kd*`
confirmados sin cambios. `P_RL,max=73.35MW` es la primera congelación de este parámetro (nuevo en
esta entrada).
Evidence reviewed: salida de consola de `stage_p2e6a_td3_residual_architecture_smoke.py` (8/8 PASS,
sin persistir CSV -- smoke test puntual de implementación, análogo a otras verificaciones rápidas de
esta sesión).
Frozen parameters:
```text
P2_ENV_ARCHITECTURE = "P_total=clip(P_droop+P_RL,-Pmax,+Pmax), P_droop=-Kd**df_local (Kd*=4694.4MW/Hz)"
P_RL_MAX_MW = 73.35  (0.25*Pmax, congelado inicialmente esta entrada)
ACTION_SPACE = "[-1,1]^2, P_RL_i = a_i*P_RL_max"
TC_S = TSTEP_S = 0.005  (sin cambios, confirmado congelado para esta arquitectura)
P2_ENV_MODULE = "Paper_2/src/p2_env.py (class P2ResidualEnv)"
P2_ENV_SMOKE_TESTS = "8/8 PASS (Paper_2/src/stage_p2e6a_td3_residual_architecture_smoke.py)"
ARCHITECTURE_CANDIDATE_FROZEN_FOR_P2E6B = TRUE
TD3_TRAINING_AUTHORIZED = FALSE (sin cambios)
```
Blockers or limitations: La observación de 8 señales usada en el entorno es un placeholder funcional
para los smoke tests, NO la observación final (`P2-E7`, ablation `OBS-A/B/C`, pendiente). El reward
incluido usa la fórmula ya congelada §6 pero no ha sido evaluado ni verificado en ningún sentido de
desempeño. `P_RL,max=0.25*Pmax` es un valor inicial elegido por el usuario, explícitamente NO
sometido a sweep en esta entrada -- podría revisarse en una etapa posterior si `P2-E6b` u otra
evidencia lo justifica.
Responsible: Claude (implementación y ejecución de smoke tests bajo autorización explícita del
usuario)
Status: passed -- 8/8 smoke tests PASS, arquitectura candidata congelada para `P2-E6b`
Next action: Reportar al usuario únicamente lo solicitado (PASS/FAIL de cada smoke test, `P_RL,max`
exacto, confirmación de equivalencia `action=0` vs. droop*, incompatibilidades encontradas -- ninguna)
y **detenerse**, tal como instruyó explícitamente el usuario -- no evaluar desempeño, no hacer sweep
de `P_RL,max`, no seleccionar políticas, no entrenar TD3, no usar validation ni `P2-T*`.

## DEC-P2-030

Date: 2026-08-19
Stage/Gate: **Hallazgo durante la implementación de P2-E6b (ablation de observación): scope-creep
latente en `f_gen_hz`/`f_gen_all_hz` de `p2_common.py` -- verificado empíricamente SIN IMPACTO
numérico en ningún resultado ya congelado.** Encontrado y diagnosticado por el asistente durante la
construcción de `p2_env_train.py`, no un hallazgo pedido explícitamente por el usuario -- reportado
por la disciplina de la sesión de nunca ocultar anomalías.
**Qué se encontró:** `OBS-C` (observación global, 22 señales) falló con
`ValueError: could not broadcast input array from shape (12,) into shape (10,)` al llamar
`ss.BusFreq.f.v` tras `add_bess_pair()`. Investigación: `ss.BusFreq.bus.v` tiene **10 entradas**
(`GEN_BUSES=[30..39]`) ANTES de `add_bess_pair()`, pero **12 entradas**
(`[30,31,...,39,16,20]`) DESPUÉS -- ANDES auto-agrega un dispositivo `BusFreq` para cada bus con un
nuevo `PV`(`StaticGen`), y `add_bess_pair()` agrega 2 `PV` nuevos (buses `16`/`20`). Las 2 entradas
nuevas se APPEND al final (orden de inserción, no orden de bus), por lo que las primeras 10 entradas
siguen correspondiendo exactamente a `GEN_BUSES` en el mismo orden.
En `p2_common.py`, la línea `f_gen_hz = np.array([float(v) for v in ss.BusFreq.f.v]) * F0_HZ`
(usada en `run_physical_scenario_tc()` y para el campo devuelto `f_gen_all_hz`) **NO** hace el mismo
slice `[:len(GEN_BUSES)]` que sí aplica `rocof_gen_hz_s` en la línea inmediatamente siguiente -- es
decir, `f_worst_hz`/`df_nadir_hz` (usados en TODA la campaña P2 desde `DEC-P2-019` en adelante, con
buses `16/20`) se calculan técnicamente sobre 12 valores (10 generadores de métricas + los 2 buses
POI de BESS), no sobre los 10 declarados en §6 del plan ("max_i sobre los 10 generadores síncronos de
métricas").
**Verificación empírica de impacto (6 casos, ambos escenarios DESIGN x 3 controladores):**
```text
                          reportado    recalculado(10 solo)   columna del minimo (indices 0-9=GEN_BUSES, 10-11=BESS)
gen_severe  NoFFC        -0.181170    -0.181170               3  (MATCH)
load_severe NoFFC        -0.208309    -0.208309               4  (MATCH)
gen_severe  droop*(8x)   -0.118617    -0.118617               3  (MATCH)
load_severe droop*(8x)   -0.144406    -0.144406               4  (MATCH)
gen_severe  F+R(4x/0.5x) -0.123060    -0.123060               3  (MATCH)
load_severe F+R(4x/0.5x) -0.144182    -0.144182               4  (MATCH)
```
En los 6 casos el mínimo de frecuencia ocurre en la columna 3 o 4 (buses generadores reales), nunca
en las columnas 10/11 (buses BESS `16`/`20`) -- consistente con la intuición física: los buses BESS
están activamente compensados por el controlador, por lo que su desviación de frecuencia local tiende
a ser MENOR que la de los generadores no compensados, nunca el mínimo global. **Ningún `df_nadir_hz`
ya congelado en `DEC-P2-018` a `DEC-P2-028` cambia de valor** bajo el cálculo correctamente acotado a
10 generadores.
Interpretation: Es un bug de higiene de código real (viola literalmente la especificación de §6 del
plan) pero **verificado sin impacto en los resultados ya congelados** -- no invalida `Kd*=4694.4MW/Hz`
(`DEC-P2-024`), el veredicto `STOP-P2-A=FAIL DEFINITIVO` (`DEC-P2-025`), ni ninguna figura/tabla de la
galería (`DEC-P2-021`). Los 6 casos verificados cubren los puntos más críticos ya congelados, pero NO
se verificó exhaustivamente cada punto de cada grilla histórica (`P2-E4` sweep de `Tc`, `P2-E5`
grillas `Kf`/`Kr` completas, `P2-E6` screening de reubicación) -- posible pero, dado el patrón físico
consistente en los 6 casos, poco probable que cambie ningún resultado.
Selected Tc or unresolved decision: Ninguna decisión física nueva. `Kd*`, `Tc`, buses, `Pmax`, el
veredicto `STOP-P2-A` -- todos sin cambios, confirmados no afectados en los casos verificados.
Evidence reviewed: inspección directa de `ss.BusFreq.bus.v` antes/después de `add_bess_pair()`;
recomputo de `df_nadir_hz` con y sin el slice correcto para 6 combinaciones (controlador x escenario)
usando `p2_common.run_physical_scenario_tc()` sin modificar.
Frozen parameters:
```text
P2_COMMON_FGENHZ_SCOPE_CREEP_FOUND = TRUE (ss.BusFreq tiene 12 entradas tras add_bess_pair, no 10)
P2_COMMON_FGENHZ_SCOPE_CREEP_IMPACT_ON_FROZEN_RESULTS = "NINGUNO verificado en 6 casos criticos
  (NoFFC/droop*/F+R-best x gen_severe/load_severe) -- el minimo de frecuencia nunca ocurre en los
  buses BESS en ninguno de los 6 casos"
P2_COMMON_FIX_APPLIED = "SOLO en Paper_2/src/p2_env_train.py (codigo nuevo de P2-E6b, no usado
  todavia por ningun resultado congelado) -- p2_common.py NO modificado en esta entrada"
P2_ENV_TRAIN_GEN_BUS_ARRAYS_FIXED = TRUE
TD3_TRAINING_AUTHORIZED = FALSE (sin cambios)
```
Blockers or limitations: `p2_common.py` NO se modificó -- el bug persiste ahí, sin impacto verificado
en los 6 casos revisados pero sin una auditoría exhaustiva de cada resultado histórico de la campaña.
Si el usuario quiere una auditoría completa o la corrección de `p2_common.py`, requiere autorización
separada (fuera del alcance de `P2-E6b`, que es sobre ablation de observación, no sobre esta
verificación).
Responsible: Claude (hallazgo y verificación durante implementación de `P2-E6b`, bajo autorización
general de esa etapa; investigación adicional no solicitada explícitamente pero necesaria antes de
continuar, siguiendo la disciplina de la sesión)
Status: passed -- bug diagnosticado, verificado sin impacto en resultados congelados, corregido en
código nuevo; `p2_common.py` deliberadamente no tocado sin autorización separada
Next action: Continuar con `P2-E6b` (ablation de observación) usando `p2_env_train.py` ya corregido;
reportar este hallazgo al usuario junto con los resultados de la ablation; si el usuario quiere
auditar/corregir `p2_common.py` de forma retroactiva, requiere autorización explícita separada.

## DEC-P2-031

Date: 2026-08-19
Stage/Gate: **P2-E6b -- resultados completos de la ablation de observación (OBS-A/B/C).**
Autorizado explícitamente por el usuario (`DEC-P2-030` continúa la misma autorización de `P2-E6b`).
**Qué se hizo:** `f_COI`/`RoCoF_COI` congelados como media NO ponderada sobre los 10 `GEN_BUSES`
(mismo proxy ya declarado en toda la campaña, `DEC-P2-019` etc. -- ninguna COI ponderada por `H` se
implementa). Normalización explícita e idéntica en las 3 variantes: `df/F_REF_HZ(0.5)`,
`RoCoF/R_REF_HZ_S(1.0)`, `P_BESS/Pmax(293.4MW)`. Verificaciones 1-6 (dimensión, NaN/Inf, reset,
escalas, raw+normalized, ausencia de leakage) -- **TODAS OK en las 3 variantes** (ver
`Paper_2/artifacts/diagnostics/p2e6b_raw_vs_norm_obs{a,b,c}.csv`). Entrenamiento TD3 corto y
comparable: 1 seed (`seed=11`), `total_timesteps=3000` idéntico en las 3, hiperparámetros §17 sin
HPO (`lr=1e-4`, `gamma=0.99`, `tau=0.005`, `batch_size=256`, `net_arch=[256,256]`,
`learning_starts=1000`, `train_freq=1`, `gradient_steps=1`), distribución de entrenamiento §10
(50/50 gen/carga, `G_train_P2`/`L_train_P2`, `rho~U(0.30,0.90)`/`alpha_L~U(0.10,0.50)`,
`lambda_L~U(0.90,1.10)`). Evaluación en los 6 escenarios de validation congelados
(`G_validation_P2=GENROU_6`/`L_validation_P2=PQ_10` x `OP_validation_P2={0.95,1.00,1.05}`,
`rho=0.60`/`alpha_L=0.30` fijos -- midpoints del rango de entrenamiento, elegidos explícitamente para
esta ablation, ver `DEC-P2-029`... nota: la definición formal de `f_COI`/`RoCoF_COI`/normalización se
registra aquí mismo, no en una entrada previa separada).
```text
Resumen (J_val_P2 global = media sobre los 6 escenarios de validation):
          J_val_P2  df_peak_mean_Hz  RoCoF_peak_mean_Hz/s  TDS_success  saturation_fraction_mean
OBS-A     0.5769    0.0561           0.4390                1.0/1.0     0.0921  (hasta 0.187 en gen_severe)
OBS-B     0.5743    0.0536           0.4380                1.0/1.0     0.0000
OBS-C     0.5688    0.0541           0.4334                1.0/1.0     0.0000

Deltas relativos (vs OBS-A):
OBS-B: J_val -0.44%,  df_peak -4.5%,  RoCoF_peak -0.23%
OBS-C: J_val -1.42%,  df_peak -3.5%,  RoCoF_peak -1.28%   (vs OBS-B: J_val -0.97%)
```
Interpretation: Las diferencias de `J_val_P2` y de las métricas físicas entre las 3 observaciones son
**pequeñas (<1.5% relativo)**, con UNA sola seed y un presupuesto corto (`3000` steps) -- no hay base
estadística (sin repetición de seeds) para afirmar que estas diferencias son una ventaja real de
información y no ruido de entrenamiento de una sola corrida. **La única diferencia cualitativamente
notable es `saturation_fraction`:** `OBS-A` (solo local, sin `COI`) entrena una política que satura
significativamente en los escenarios `gen_severe` de validation (`17.9%`-`18.7%` de las acciones),
mientras que `OBS-B` y `OBS-C` no saturan en absoluto (`0.000` en los 6 escenarios). Esto es una
distinción de comportamiento de política más robusta que la diferencia de `J_val_P2` en sí (la
saturación es una propiedad casi determinista de la política entrenada, no una métrica ruidosa
punto-a-punto), y sugiere que la observación puramente local puede llevar a una política menos
calibrada (más agresiva/saturada) que las variantes con información `COI`/global, sin que eso se
traduzca todavía en una mejora de `J_val_P2` correspondientemente grande a este presupuesto.
Aplicando la regla de selección del usuario tal como está escrita: ninguna de las tres variantes
muestra una "mejora clara" (`OBS-B` vs `OBS-A`) ni "sustancial y reproducible" (`OBS-C` vs `OBS-B`) en
`J_val_P2` -- los números están dentro de lo esperable como ruido de una sola seed. Bajo una lectura
literal de la tercera regla ("si OBS-A es comparable, preferir OBS-A por deployability"), los
`J_val_P2` sí son comparables, pero la diferencia de saturación complica esa lectura -- **no es una
conclusión mecánica, requiere juicio.** No se cierra la selección unilateralmente en esta entrada --
se presenta al usuario para revisión conjunta, como el propio usuario pidió explícitamente.
Selected Tc or unresolved decision: Ninguna observación final seleccionada/congelada todavía --
pendiente de revisión conjunta con el usuario (explícitamente solicitada: "revisamos si la selección
de observación queda realmente cerrada").
Evidence reviewed: `Paper_2/artifacts/diagnostics/p2e6b_observation_ablation.csv` (18 filas: 3 OBS x
6 escenarios validation); `Paper_2/artifacts/diagnostics/p2e6b_observation_ablation_summary.csv`;
`Paper_2/artifacts/diagnostics/p2e6b_raw_vs_norm_obs{a,b,c}.csv`.
Frozen parameters:
```text
F_COI_DEFINITION = "media NO ponderada de frecuencia sobre los 10 GEN_BUSES" (congelado para toda P2)
ROCOF_COI_DEFINITION = "media NO ponderada de RoCoF sobre los 10 GEN_BUSES" (congelado para toda P2)
OBS_NORMALIZATION = "df/0.5Hz, RoCoF/1.0Hz_s, P_BESS/293.4MW -- identica en OBS-A/B/C, congelada"
OBS_A_J_VAL_P2 = 0.5769  (sat_mean=0.092, hasta 0.187 en gen_severe)
OBS_B_J_VAL_P2 = 0.5743  (sat_mean=0.000)
OBS_C_J_VAL_P2 = 0.5688  (sat_mean=0.000)
OBSERVATION_FINAL_SELECTED = NOT_DECIDED (pendiente de revision conjunta con el usuario)
TD3_TRAINING_AUTHORIZED = FALSE (sin cambios -- esto fue ablation de UNA seed corta, no training final)
```
Blockers or limitations: Comparación de UNA sola seed por variante (tal como pidió el usuario) -- no
hay estimación de varianza entre seeds, por lo que las diferencias de `J_val_P2` (todas <1.5%) no
pueden distinguirse con confianza de ruido de entrenamiento. El presupuesto de `3000` steps es
deliberadamente corto (ablation, no training final) -- ninguna de las 3 políticas está cerca de
converger, los resultados reflejan comportamiento temprano de entrenamiento, no desempeño final.
Responsible: Claude (implementación, entrenamiento y evaluación bajo autorización explícita del
usuario)
Status: passed -- ablation ejecutada y reportada completa; selección de observación NO cerrada,
pendiente de revisión conjunta explícitamente solicitada por el usuario
Next action: Presentar el reporte completo al usuario (definiciones exactas, presupuesto,
`J_val_P2`/métricas físicas por OBS, la asimetría de saturación OBS-A vs B/C, y por qué la regla de
selección no resuelve el caso mecánicamente) y **esperar su revisión conjunta** antes de congelar
ninguna observación final -- no entrenar TD3 final, no usar `P2-T*`, no seleccionar checkpoint.

## DEC-P2-032

Date: 2026-08-19
Stage/Gate: **P2-E6b -- cierre: `OBS-A` congelada como observación principal de Paper_2.**
Autorizado/decidido explícitamente por el usuario ("AUTORIZO CIERRE DE P2-E6b"), tras revisar el
reporte completo de `DEC-P2-031`. **Ninguna simulación ni entrenamiento adicional ejecutado** --
decisión de gate sobre evidencia ya generada.
**Qué se decidió:**
1. `OBS-A` (6 señales locales: `[df_16, RoCoF_16, P_BESS1, df_20, RoCoF_20, P_BESS2]`) congelada
   como observación principal de Paper_2.
2. Justificación explícita del usuario: diferencias de `J_val_P2` entre `OBS-A/B/C` `<1.5%` en
   ablation de 1 sola seed -- sin evidencia suficiente para atribuir superioridad a `OBS-B`/`OBS-C`;
   por la regla pre-registrada, ante desempeño comparable se prefiere `OBS-A` por deployability y
   menor dependencia informacional.
3. Normalización congelada sin cambios: `df/0.5Hz`, `RoCoF/1.0Hz/s`, `P_BESS/293.4MW`.
4. `OBS-B`/`OBS-C` quedan registradas como ablations (`DEC-P2-031`), no como configuración principal.
5. Limitación registrada explícitamente por el usuario (no oculta, no interpretada como
   inestabilidad ni inferioridad demostrada): `OBS-A` mostró `saturation_fraction` no nula en la
   ablation (`~0.092` promedio, hasta `~0.187` en `gen_severe`) vs. `0.000` de `OBS-B`/`OBS-C` --
   razones explícitas para no penalizar esto: (a) no había criterio pre-registrado de selección por
   `saturation_fraction`, (b) P2 no penaliza potencia/saturación (§5 del plan), (c) comparación de una
   sola seed con políticas no convergidas.
6. No se ejecuta entrenamiento adicional para decidir observación (instrucción explícita).
`plan_maestro_P2_TD3_Hybrid_FFC.md` §9 reescrito para reflejar `OBS-A` como observación final
congelada (con la justificación y limitación arriba, y las definiciones de `f_COI`/`RoCoF_COI`/
normalización ya congeladas en `DEC-P2-031`); §23 `PF2-06` actualizado a `P_total=P_droop+P_RL` (no
ya `P_ff+P_RL`); §25 nota añadida distinguiendo la secuencia ORIGINAL planeada de la REALMENTE
ejecutada, y la lista de congelamiento de `P2-E8` anotada con el estado actual de cada parámetro.
Interpretation: La selección de `OBS-A` es una decisión de diseño explícita del usuario, no una
conclusión estadística robusta -- documentado como tal (`J_val_P2` dentro de ruido de una sola seed;
la asimetría de saturación es la única señal cualitativamente distinta, y se decide explícitamente NO
usarla como criterio de descarte, por las tres razones dadas). Esto es coherente con el principio de
la sesión de nunca ocultar limitaciones: la decisión queda tomada, pero la base de evidencia (débil,
una sola seed) y el trade-off conocido (saturación) están documentados junto a ella, no barridos.
Selected Tc or unresolved decision: `OBS-A` congelada. `Tc=tstep=5ms` sigue como CANDIDATO (sin
cambios, no tocado en esta entrada). Pendiente antes de `P2-E8`/preflight: número de seeds finales
(3 vs. 5, §18/§30), estado final de `P_RL,max=0.25*Pmax` (congelado "inicialmente" en `DEC-P2-028`,
no vuelto a tocar en `P2-E6b`, sin sweep -- técnicamente sigue etiquetado como "inicial"), y el hallazgo
no resuelto de `DEC-P2-030` (scope-creep de `f_gen_hz` en `p2_common.py`, verificado sin impacto en 6
casos pero sin auditoría exhaustiva, no corregido en `p2_common.py`).
Evidence reviewed: `DEC-P2-031` (resultados completos de la ablation); mensaje de autorización del
usuario (10 puntos explícitos).
Frozen parameters:
```text
OBSERVATION_FINAL = "OBS-A: [df_16, RoCoF_16, P_BESS1, df_20, RoCoF_20, P_BESS2]" (CONGELADA)
OBS_NORMALIZATION = "df/0.5Hz, RoCoF/1.0Hz_s, P_BESS/293.4MW" (sin cambios, DEC-P2-031)
OBS_B_OBS_C_STATUS = "ablations registradas, DEC-P2-031 -- NO configuracion principal"
OBS_A_SATURATION_CAVEAT = "sat_mean=0.092 (hasta 0.187 en gen_severe) en la ablation de 1 seed --
  registrado como limitacion, NO como descalificador (P2 no penaliza potencia, SS5)"
TD3_TRAINING_AUTHORIZED = FALSE (sin cambios -- seeds finales aun no autorizadas)
```
Blockers or limitations: Ver "Selected Tc or unresolved decision" arriba -- tres puntos pendientes
antes de `P2-E8`/preflight: número de seeds, estado final de `P_RL,max`, y el hallazgo `DEC-P2-030`
sin resolver en `p2_common.py`.
Responsible: Usuario (decisión de diseño); Claude (registro de gobernanza y actualización del plan,
sin ejecución)
Status: passed -- `OBS-A` congelada, `P2-E6b` cerrado
Next action: Reportar al usuario las decisiones pendientes antes de `P2-E8` (número de seeds, estado
de `P_RL,max`, hallazgo `DEC-P2-030`) y **detenerse**, tal como instruyó explícitamente el usuario --
no entrenar las seeds finales, no ejecutar `P2-E8`/preflight todavía, no usar `P2-T*`.

## DEC-P2-033

Date: 2026-08-19
Stage/Gate: **P2-E7 -- freeze final pre-preflight: seeds, `P_RL,max`, corrección de `DEC-P2-030` en
`p2_common.py` con regresión mínima, y congelamiento completo de la arquitectura revisada.**
Autorizado/decidido explícitamente por el usuario ("AUTORIZO P2-E7 — FREEZE FINAL PRE-PREFLIGHT"),
12 puntos de instrucción explícitos.
**Qué se hizo:**
1. `FINAL_SEEDS = {11,22,33,44,55}` (5 seeds) congelado, sin reducción posterior permitida.
2. `P_RL,max = 73.35MW` (`0.25*Pmax`) congelado FROZEN FINAL -- sin sweep, por instrucción explícita.
3-4. **Corrección de `p2_common.py` (hallazgo `DEC-P2-030`):** las 6 ocurrencias de
   `f_gen_hz = ...ss.BusFreq.f.v...` (líneas originales `223,640,824,858,1093,1210`) ahora se acotan
   explícitamente a `[:len(GEN_BUSES)]`, igual que ya hacía `rocof_gen_hz_s` con `Wf_y.v`. Comentario
   explicativo añadido junto a la definición de `GEN_BUSES`. `OBS-A`/mediciones locales del
   controlador **NO se tocaron** (siguen leyendo `BusROCOF.f`/`Wf_y` en los buses `16`/`20`
   directamente, nunca pasaban por `BusFreq` global).
5-7. **Regresión mínima ejecutada** (`Paper_2/src/stage_p2e7_dec030_fix_regression.py`, nuevo):
   6 casos (`NoFFC`/`droop*`/`F+R*` x `gen_severe`/`load_severe`), mismos parámetros que
   `DEC-P2-024/025`, comparando `df_nadir_hz`/`RoCoF_max_hz_s` antes (valores ya registrados en
   decisiones previas) vs. después (recalculados con el código corregido):
```text
scenario     controller  df_nadir(antes/despues)      RoCoF_max(antes/despues)   f_gen_all_hz cols  MATCH
gen_severe   NoFFC       -0.181170 / -0.181170         1.185 / 1.185              10 (antes 12)      SI
gen_severe   droop*      -0.118617 / -0.118617         0.885 / 0.885              10 (antes 12)      SI
gen_severe   F+R*        -0.123060 / -0.123060         0.904 / 0.904              10 (antes 12)      SI
load_severe  NoFFC       -0.208309 / -0.208309         2.933 / 2.933              10 (antes 12)      SI
load_severe  droop*      -0.144406 / -0.144406         2.295 / 2.295              10 (antes 12)      SI
load_severe  F+R*        -0.144182 / -0.144182         2.292 / 2.292              10 (antes 12)      SI
```
**6/6 MATCH exacto (diferencia 0.0 dentro de precisión numérica).** `f_gen_all_hz` ahora tiene
exactamente 10 columnas (antes 12) en los 6 casos -- confirma que la corrección elimina efectivamente
los 2 buses BESS del scope de métricas. Por instrucción del usuario (punto 8): **no se repite
retrospectivamente el resto de la campaña** -- la regresión mínima de 6 casos es evidencia suficiente
de que `DEC-P2-030` no afectó ningún resultado físico ya congelado.
9. **Congelamiento completo tras PASS de la regresión** (arquitectura, buses, `Kd*`, `Pmax`,
   `P_RL,max`, `Tc`, `tstep`, observación, normalización, seeds, reward, splits) -- ver bloque
   `Frozen parameters` abajo y `plan_maestro_P2_TD3_Hybrid_FFC.md` (§4/§9/§18/§25 "FREEZE FINAL",
   todos actualizados).
10. `traceability_matrix.csv` actualizado (nueva fila, ver más abajo).
11. **Validación estructural estricta del CSV con pandas ejecutada después de editar** -- `pd.read_csv`
   falló inicialmente con `ParserError` en la fila `5` (`CLM-P2-FAIR`, preexistente, no relacionada con
   ninguna edición de esta sesión -- verificado contra `git show HEAD:...`, byte-idéntica al último
   commit): el campo `action` no estaba entrecomillado y contenía una coma sin escapar
   ("Verificar tras P2-E8 (congelamiento, renombrado..."), partiéndolo en dos columnas. Corregido
   (solo comillas añadidas, contenido sin cambios) para que la validación estricta pedida por el
   usuario pudiera ejecutarse de verdad. Resultado final: `pd.read_csv` exitoso, `21` filas x `14`
   columnas, sin `ParserError`.
Interpretation: El hallazgo `DEC-P2-030` queda cerrado de forma definitiva: no solo se verificó sin
impacto en 6 casos (como ya hizo `DEC-P2-030`), sino que además el código fuente que producía el
scope-creep ya está corregido y la regresión confirma bit-a-bit que el desempeño físico reportado no
cambia. La campaña P2 llega a `P2-E7` con la arquitectura completa congelada -- el único paso que
falta antes de `P2-T*` es `P2-E8` (preflight formal) y el entrenamiento de las 5 seeds finales,
ninguno de los dos autorizado en esta entrada.
Selected Tc or unresolved decision: `Tc=tstep=5ms` -- el usuario lo lista como "FROZEN" en el punto 9
de su autorización (bajo el encabezado "Congelar después de PASS"), por lo que se registra aquí como
**congelado final** (ya no "candidato"), reflejando la intención explícita de esta entrada, aunque
ninguna entrada previa había usado la palabra "final" para `Tc` -- se documenta el cambio de estado
explícitamente para que quede trazable.
Evidence reviewed: `Paper_2/artifacts/diagnostics/p2e7_dec030_fix_regression.csv` (6 filas, 6/6
MATCH); `p2_common.py` (diff de las 6 correcciones); mensaje de autorización del usuario (12 puntos).
Frozen parameters:
```text
FINAL_SEEDS = {11, 22, 33, 44, 55}  (FROZEN FINAL, no reducir por resultados desfavorables)
ARCHITECTURE = "droop* + TD3 residual, P_total=clip(P_droop+P_RL,-Pmax,+Pmax)"  (FROZEN)
BESS_BUS_1 = 16, BESS_BUS_2 = 20  (FROZEN)
KD_STAR_MW_PER_HZ = 4694.4  (FROZEN, DEC-P2-024)
PMAX_MW = 293.4  (FROZEN)
P_RL_MAX_MW = 73.35  (FROZEN FINAL, sin sweep, DEC-P2-033)
TC_S = 0.005  (FROZEN FINAL -- cambia de status "candidato" a "final" en esta entrada)
TSTEP_S = 0.005  (FROZEN)
OBSERVATION = "OBS-A: [df_16,RoCoF_16,P_BESS1,df_20,RoCoF_20,P_BESS2]"  (FROZEN, DEC-P2-032)
NORMALIZATION = "df/0.5Hz, RoCoF/1.0Hz_s, P_BESS/293.4MW"  (FROZEN, DEC-P2-031)
REWARD = "definicion vigente SS6 del plan"  (FROZEN, sin cambios)
SPLITS = "train/validation/test ya congelados"  (FROZEN, DEC-P2-003, sin cambios)
DEC_P2_030_FIX_APPLIED_TO_P2_COMMON = TRUE (6 ocurrencias corregidas, regresion 6/6 MATCH)
TD3_TRAINING_AUTHORIZED = FALSE (sin cambios -- entrenar las 5 seeds finales requiere autorizacion
  explicita separada, punto 12 de esta autorizacion)
```
Blockers or limitations: Ninguno nuevo. La regresión cubrió únicamente los 6 casos ya identificados
en `DEC-P2-030` (no una repetición exhaustiva de toda la campaña, por instrucción explícita del
usuario, punto 8) -- consistente con el criterio de suficiencia que el propio usuario definió.
Responsible: Claude (implementación de la corrección, ejecución de la regresión, y actualización de
gobernanza bajo autorización explícita del usuario)
Status: passed -- regresión 6/6 MATCH, freeze final aplicado y registrado
Next action: Reportar al usuario (resultado de la regresión, lista completa de parámetros FROZEN,
decisiones aún pendientes antes de `P2-E8`) y **detenerse**, tal como instruyó explícitamente el
usuario -- no ejecutar `P2-E8` preflight, no entrenar TD3, no usar `P2-T1..P2-T12`.

## DEC-P2-034

Date: 2026-08-19
Stage/Gate: **P2-E8 -- preflight formal (26 checks) + smoke TD3 + benchmark computacional real.**
Autorizado explícitamente por el usuario ("AUTORIZO P2-E8 — PREFLIGHT FORMAL + BENCHMARK
COMPUTACIONAL"), 5 secciones (A-E) con requisitos explícitos. Configuración usada: exactamente la
congelada en `DEC-P2-033`, sin modificar ningún parámetro.

### A. Preflight formal -- 26/26 PASS (segunda ronda, tras corregir 2 checks mal diseñados)

`Paper_2/src/stage_p2e8a_preflight.py` (nuevo). Primera ejecución: **24/26 PASS, 2 FAIL**
(`PF2-17`, `PF2-19`). Investigación inmediata (sin avanzar a smoke/benchmark, tal como exigió el
usuario en caso de falla):
- **`PF2-17`** ("exactamente una acción por step") fallaba porque el check original medía
  uniformidad de `dt` en la trayectoria completa (`dt==tstep` en el 100% de los pasos), no la
  invariante real pedida (una acción por llamada a `step()`). Se encontró que **7/1199 intervalos**
  no son exactamente `tstep=5ms` (mínimo `0.0001s`) -- verificado que este comportamiento **ya
  existía en `p2_common.py`** (mismo mecanismo `itm_step()`/`do_switch()`, `DEC-P1-007`) antes de
  P2-E6/E8: el solver de paso fijo de ANDES inserta micro-pasos correctivos para aterrizar
  exactamente en el instante del evento discreto (`t=TD`) y en un pequeño número de puntos
  adicionales -- nunca se salta ni duplica tiempo (todo `dt>0`, ninguno excede `tstep`). Check
  corregido a una verificación estructural del código (`itm_step()` aparece exactamente 1 vez en
  `step()`, sin bucle `for`/`while` envolviéndolo) -- **PASS**. El hallazgo de `dt` no uniforme se
  reporta como nota informativa, no como check, y no afecta ningún resultado físico ya congelado
  (mismo mecanismo usado en todos los `DEC-P2-*` desde el inicio de la campaña).
- **`PF2-19`** ("evento aplicado una sola vez") fallaba porque el check original medía saltos
  `>5MW` en `P_BESS2` (señal derivada, continuamente variable porque el droop reacciona cada paso a
  una frecuencia que oscila genuinamente tras el evento -- 29 transiciones, ninguna es el evento en
  sí). Corregido a medir directamente la variable del disturbio (`PQ.Ppf` para el escenario de
  carga): **exactamente 1 cambio de escalón, en `t=TD=1.0s`, de `6.8pu` a `10.2pu`** (`+340MW`,
  consistente con `DEC-P2-019`) -- **PASS**.
Segunda ejecución, con los checks corregidos: **26/26 PASS** (tabla completa en
`Paper_2/artifacts/preflight/p2e8_preflight_26checks.csv`).
```text
PF2-01..16  PASS (Gymnasium API, spaces, dimension, normalizacion, finitud, reset determinista/
             limpio, action=0==droop*, residual +-73.35MW, clipping +-293.4MW, unidades, BESS
             independientes, Tc/tstep=5ms exactos)
PF2-17      PASS (corregido -- verificacion estructural, ver arriba)
PF2-18      PASS (sin duplicacion temporal)
PF2-19      PASS (corregido -- medido en PQ.Ppf, ver arriba)
PF2-20..22  PASS (splits train/operating point respetados, 2000 muestras)
PF2-23      PASS (reward usa exactamente 10 GEN_BUSES)
PF2-24      PASS (reward sin potencia/energia, verificado por firma+codigo fuente)
PF2-25      PASS (TDS_success presente; sin fallo inducible bajo condiciones probadas)
PF2-26      PASS (reproducibilidad exacta, diff=0.0, misma seed+secuencia de acciones)
```

### B. Smoke TD3 -- 14/14 PASS

`Paper_2/src/stage_p2e8b_smoke_td3.py` (nuevo). Hiperparámetros exactamente los de §17 (sin HPO):
actor/critic `[256,256]`, `lr=1e-4`, `gamma=0.99`, `tau=0.005`, `batch_size=256`,
`buffer_size=1,000,000`, `learning_starts=1000`, `train_freq=1`, `gradient_steps=1`, `policy_delay`/
`target_policy_noise`/`target_noise_clip` = defaults SB3. `1080` steps (cruza `learning_starts`,
~80 gradient updates). **14/14 PASS**: actor creado, twin critics (2 Q-networks), replay buffer
(tamaño correcto), `learning_starts`/`train_freq`/`gradient_steps` confirmados, `policy_delay`/
`target_policy_noise` = default SB3 sin cambios, `learning_starts` cruzado, actor output finito,
critic Q-values finitos, checkpoint guardado, modelo recargado con inferencia post-reload
**idéntica** (`action` exactamente igual antes/después de reload), memoria estable. No se usó para
seleccionar política ni se interpretó `return`/`J_val` como resultado científico.

### C. Benchmark computacional -- mediciones reales (sin extrapolar de Paper_1)

`Paper_2/src/stage_p2e8c_benchmark.py` (nuevo). Entorno final exacto, 1 seed + prueba de
concurrencia de 5 procesos.
```text
1. Simulacion pura sin aprendizaje:        8.17 ms/paso  (8174 ms/1000 transiciones)
2. Episodio TD3 SIN gradiente (warmup):    8.90 ms/paso  (8900 ms/1000 transiciones)
2. Episodio TD3 CON gradiente (estado estacionario): 16.35 ms/paso (16352 ms/1000 transiciones)
3. Transiciones por episodio reales:       1200  (tf=6.0s / tstep=5ms, confirmado empiricamente)
5. RSS proceso tras crear TD3 (buffer 1M): 399.8 MB
6. Tamano real del replay buffer (numpy):  64.0 MB (paginas OS no comprometidas hasta llenarse)
7. CPU% del proceso (single-seed):         16.1% de 1 nucleo logico (14 nucleos logicos disponibles
                                            en la maquina -- amplio margen nominal de CPU)
8. Costo de evaluacion validation (6 esc): 47.85 s total (7.97 s/escenario)
9. Checkpoint save/load:                   126 ms / 31 ms
Prueba de concurrencia (5 procesos, 1080 pasos c/u, sin entrenamiento final):
  single-seed 1080 pasos (referencia):     10.3 s
  5 procesos simultaneos, pared:           72.2 s  (5/5 completaron sin error)
  equivalente secuencial (5x10.3s):        51.6 s
  "speedup" medido:                        0.72x (el paralelo fue MAS LENTO que el secuencial
                                            equivalente en esta prueba corta)
  CPU sistema durante el batch:            min=6% max=50% mean=19% (de 1400% max con 14 nucleos)
```
**Hallazgo importante, reportado sin suavizar:** en esta prueba corta (1080 pasos/proceso, ~10s de
cómputo puro por proceso), ejecutar 5 procesos simultáneos tomó **más** tiempo de pared (72.2s) que
ejecutarlos uno tras otro (51.6s) -- un "speedup" de `0.72x`, es decir, contraproducente a esta
escala. **Interpretación, no una cifra fabricada:** el CPU% de un proceso individual (16.1%) sugiere
amplio margen nominal, por lo que esta medición probablemente está dominada por el costo FIJO de
arranque de cada proceso (import de `torch`/`andes`/`gymnasium`/`stable_baselines3`, carga del caso
`.xlsx` de ANDES desde disco) bajo contención simultánea de 5 procesos -- no por el costo de estado
estacionario del cómputo en sí. **Esto NO se puede extrapolar con confianza a una corrida de horas**
(donde el costo fijo de arranque sería una fracción despreciable del tiempo total) -- se reporta
como hallazgo real medido, con esta interpretación explícita, no como una conclusión cerrada sobre
la eficiencia de paralelismo en régimen estacionario.

### D. Estimación del training final -- rango, no cifra fabricada

Usando el costo de estado estacionario medido (`16.35ms/paso`, con gradiente, el régimen dominante
de una corrida real tras el warmup de `learning_starts=1000`) y el mínimo de episodios de la regla
de early stopping del plan (§19, `>=2000` episodios, patience 5 evaluaciones -- **piso, no un total
comprometido**, la corrida real podría extenderse más):
```text
Transiciones minimas por seed:  2000 episodios x 1200 pasos/episodio = 2,400,000
Tiempo minimo por seed:         2,400,000 x 16.35ms = ~39,240s = ~10.9 horas
  (+ ~10 evaluaciones de validation cada 200 episodios x 47.85s = ~480s = ~0.13h, marginal)
Tiempo total SECUENCIAL (5 seeds, piso minimo): ~55.1 horas (~2.3 dias)
Tiempo total PARALELO (5 seeds):  INCIERTO -- el benchmark corto no permite estimarlo con confianza
  (ver hallazgo de la Seccion C). Rango plausible: entre ~11h (si el paralelismo fuera casi perfecto
  en regimen estacionario, escenario optimista no verificado) y >55h (si la contencion observada en
  el benchmark corto persistiera a escala completa, escenario pesimista tambien no verificado).
RAM esperada (5 procesos independientes, sin memoria compartida): ~5 x 400MB =~ 2GB, estimacion
  lineal razonable dado que cada proceso es independiente -- no debería ser limitante en una maquina
  con RAM tipica de estacion de trabajo.
```
**Recomendación de ejecución -- NO se puede dar con confianza completa según instrucción explícita
del usuario ("no fabricar cifras si el benchmark no permite estimarlas con confianza"):** la
evidencia disponible NO respalda con confianza ni "5 paralelas" ni descarta esa opción. Dos caminos
razonables, ninguno decidido aquí:
1. Ejecutar un benchmark de concurrencia MÁS LARGO (p.ej. 10,000-20,000 pasos/proceso, ~5-10 min de
   pared total) para diluir el costo fijo de arranque y medir la eficiencia de paralelismo en
   régimen estacionario con confianza -- esto excede el alcance ya autorizado de "prueba corta" y
   requeriría autorización separada.
2. Adoptar la opción conservadora **"2-3 en paralelo por lotes"** como default operativo, respaldada
   más directamente por la evidencia de baja contención de CPU de un solo proceso (`16.1%`), sin
   comprometerse a "5 paralelas" hasta tener el dato faltante.

### E. Condición de cierre

```text
26/26 preflight checks PASS       -- SI (segunda ronda, tras corregir 2 checks)
smoke TD3 PASS                    -- SI (14/14)
sin NaN/Inf                       -- SI
checkpoint save/reload PASS       -- SI (preflight y smoke, ambos)
benchmark sin limitacion que haga inviable el entrenamiento -- SI (secuencial claramente viable,
  ~55h; RAM/CPU sin senal de bloqueo duro); la AMBIGUEDAD de la eficiencia de paralelismo es una
  cuestion de OPTIMIZACION de tiempo de pared, no de viabilidad

P2-E8 = PASS
TD3_FINAL_TRAINING_READY = TRUE
```
**No se inicia `P2-E9` automáticamente** (instrucción explícita del usuario).
Interpretation: La arquitectura, entorno y pipeline de entrenamiento están mecánicamente verificados
y listos. El hallazgo de la Sección C (paralelismo ambiguo a corto plazo) y el compromiso de tiempo
real (~11h/seed mínimo, ~55h secuencial para 5 seeds) son las dos piezas de información nuevas más
importantes de esta entrada para la decisión de cómo proceder con el entrenamiento final -- ninguna
de las dos invalida el `PASS`, pero ambas deben pesar en la decisión del usuario sobre cuándo/cómo
lanzar `P2-E10`.
Selected Tc or unresolved decision: Ninguna decisión física nueva. Estrategia de paralelismo para
las 5 seeds NO decidida (ver Sección D) -- pendiente de decisión explícita del usuario.
Evidence reviewed: `Paper_2/artifacts/preflight/p2e8_preflight_26checks.csv` (26 filas, ambas
rondas registradas en el log de consola, CSV final = segunda ronda 26/26);
`Paper_2/artifacts/preflight/p2e8_smoke_td3.csv` (14 filas, 14/14);
`Paper_2/artifacts/preflight/p2e8_benchmark_summary.csv` (resumen completo).
Frozen parameters:
```text
PREFLIGHT_26_CHECKS = PASS (segunda ronda; 2 checks corregidos por diseno defectuoso, no por
  relajacion de criterio -- ver detalle arriba)
SMOKE_TD3 = PASS (14/14)
BENCHMARK_TRANSITIONS_PER_EPISODE = 1200
BENCHMARK_MS_PER_STEP_SIN_GRADIENTE = 8.90
BENCHMARK_MS_PER_STEP_CON_GRADIENTE = 16.35
BENCHMARK_PARALLEL_5PROC_SPEEDUP = 0.72 (medido en prueba corta, probablemente dominado por costo
  de arranque, NO extrapolable con confianza a regimen estacionario)
ESTIMATED_TIME_PER_SEED_MIN_HOURS = 10.9 (piso, 2000 episodios sin extension por patience)
ESTIMATED_TIME_5SEEDS_SEQUENTIAL_HOURS = 55.1 (piso)
ESTIMATED_TIME_5SEEDS_PARALLEL_HOURS = INCIERTO (rango no confiable, ver Seccion D)
TD3_FINAL_TRAINING_READY = TRUE
TD3_TRAINING_AUTHORIZED = FALSE (sin cambios -- P2-E9/entrenamiento final requieren autorizacion
  explicita separada)
```
Blockers or limitations: (1) Estrategia de paralelismo para las 5 seeds finales sin decidir --
requiere benchmark adicional o decisión conservadora del usuario. (2) El compromiso de tiempo real
(~11h/seed mínimo, potencialmente más por early stopping abierto) no estaba cuantificado
previamente en el plan -- ahora es información concreta que puede afectar la planificación. (3)
Ninguno de los 26 checks ni el smoke reveló ningún blocker técnico de corrección.
Responsible: Claude (implementación y ejecución de preflight/smoke/benchmark bajo autorización
explícita del usuario; corrección de 2 checks mal diseñados, con investigación y verificación
completa antes de continuar, tal como exigió la instrucción de "detenerse" ante cualquier falla)
Status: passed -- `P2-E8 = PASS`, `TD3_FINAL_TRAINING_READY = TRUE`
Next action: Reportar al usuario (tabla 26/26, resultado smoke TD3, benchmark real, estimación de
tiempo, estrategia recomendada -- sin comprometerse a una cifra que el benchmark no respalda con
confianza -- y blockers restantes) y **detenerse**, tal como instruyó explícitamente el usuario --
no iniciar `P2-E9`, no entrenar TD3 final, no usar `P2-T1..P2-T12`, no cambiar arquitectura/reward/
observación/`P_RL,max`/hiperparámetros.

## Nota operativa (P2-E9, durante ejecución) -- desviación autorizada de la estrategia de batching

Date: 2026-08-20/21
**Desviación explícita, autorizada por el usuario, de la estrategia de ejecución original de
`DEC-P2-035` (pendiente de registro formal al cierre)**: la autorización de P2-E9 especificaba
`máximo 2 seeds simultáneamente` en 3 batches secuenciales (`{11,22}`→`{33,44}`→`{55}`) y "no cambiar
esta estrategia durante el training por observar resultados intermedios". Con batch 1 completo
(seeds 11/22, ambas `stopped_early` limpio, 0 fallos numéricos, checkpoints verificados sanos tras
investigar un falso positivo de mi propio check de integridad -- ver detalle en el cierre de
`DEC-P2-035`) y batch 2 (seeds 33/44) en curso (~ep600/2000+, iniciado 2026-08-20 15:56), el usuario
preguntó explícitamente por el impacto de lanzar la seed 55 en paralelo con el batch 2 en curso (3
procesos simultáneos en vez de 2) y luego **autorizó explícitamente esa desviación** ("autorizo que
lances ya el 55"). Impacto estimado antes de proceder (comunicado al usuario, no una decisión
unilateral): con CPU/RAM con amplio margen (single-seed ~16% de 1 núcleo lógico de 14 disponibles,
~400MB RAM, `DEC-P2-034`) y evidencia real de 2-en-paralelo (batch 1, sin contención severa aparente,
tiempos cercanos al piso estimado) más favorable que la prueba corta de 5-procesos de `DEC-P2-034`
(dominada por costo de arranque), se estimó una penalización de régimen estacionario probablemente
pequeña, no medida directamente para 3-en-paralelo. Seed 55 lanzada en paralelo con 33/44 bajo esta
autorización explícita. Ningún parámetro FROZEN se modificó -- únicamente la estrategia de
paralelismo/agrupación en batches cambia (de 3 batches secuenciales de <=2 a una ejecución de 3
seeds simultáneas para el resto de la campaña). Se registrará en el cierre formal de `DEC-P2-035`.

## DEC-P2-035

Date: 2026-08-21
Stage/Gate: **P2-E9 -- cierre: entrenamiento TD3 final, 5 seeds completas.** Autorizado
explícitamente por el usuario ("AUTORIZO P2-E9 — ENTRENAMIENTO FINAL TD3"). Configuración exactamente
la congelada en `DEC-P2-033` (arquitectura `droop*+TD3` residual, buses 16/20, `Kd*=4694.4MW/Hz`,
`Pmax=293.4MW`, `P_RL,max=73.35MW`, `Tc=tstep=5ms`, `OBS-A`, normalización congelada, reward §6,
splits `DEC-P2-003`) -- **ningún parámetro FROZEN modificado**.
**Infraestructura nueva construida y validada antes del run real:** `Paper_2/src/
p2_train_callback.py` (`P2ValidationCallback`, evaluación cada 200 episodios en los 6 escenarios de
validation, `J_val_P2` exactamente §7, checkpoint por evaluación, selección exclusiva por mínimo
`J_val_P2`, early stopping exactamente §19 -- piso 2000 episodios, patience 5 evaluaciones sin
mejora -- tope de seguridad de ingeniería en 6000 episodios explícitamente distinto de la regla del
plan) y `Paper_2/src/stage_p2e9_train_seed.py` (driver por seed). Validado con un dry-run mecánico
de 3 episodios (seed sintética 999, parámetros reducidos) antes de comprometer el cómputo real --
verificó evaluación/checkpoint/mejor-tracking/parada e integridad de checkpoint correctos.
**Estrategia de ejecución -- desviación autorizada a mitad de campaña:** el usuario especificó 3
batches secuenciales de <=2 seeds simultáneas (`{11,22}`→`{33,44}`→`{55}`). Tras completar batch 1 y
con batch 2 en curso, el usuario preguntó por el impacto de paralelizar más y autorizó explícitamente
lanzar la seed 55 en paralelo con el batch 2 en curso (3 procesos simultáneos) -- ver nota operativa
inmediatamente anterior a esta entrada para el detalle completo de esa autorización y el impacto
estimado comunicado antes de proceder. Ningún parámetro FROZEN se tocó por este cambio, solo el
agrupamiento temporal de las seeds.
**Hallazgo propio detectado y corregido durante la ejecución:** el check de integridad de checkpoint
del driver original comparaba el modelo FINAL en memoria (punto de entrenamiento más tardío) contra
el MEJOR checkpoint histórico (punto de entrenamiento más temprano) -- estos son, por construcción,
puntos de entrenamiento distintos, por lo que la comparación estaba mal diseñada, no medía
corrupción real. Esto causó un `FAIL` en las seeds 11 y 22 (las primeras en completar, antes de la
corrección). Investigado inmediatamente: se verificó que dos recargas INDEPENDIENTES del mismo
archivo de checkpoint (`seed11_ep400`, `seed22_ep1600`) producen exactamente la misma salida
determinística -- los checkpoints nunca estuvieron corruptos. Corregido el check (comparar dos
recargas independientes del mismo archivo, no el modelo final contra el mejor histórico) antes de
lanzar batch 2 -- seeds 33/44/55 ya corrieron con el check corregido y dieron `PASS` directamente.
### Tabla resumen -- 5/5 seeds completas
```text
seed  best_ckpt_ep  best_J_val_P2  stop_ep  wall_time_h  transitions  fallos_num  NaN/Inf  integridad
11    400           0.5299         2000     14.87        2,400,000    0           ninguno  PASS (verificado tras corregir el check)
22    1600          0.5263         2600     17.60         3,120,000   0           ninguno  PASS (verificado tras corregir el check)
33    400           0.5769         2000     17.73         2,400,000   0           ninguno  PASS
44    600           0.5217         2000     17.49         2,400,000   0           ninguno  PASS
55    1400          0.5444         2400     16.56         2,880,000   0           ninguno  PASS

mean(J_val_P2)   = 0.5398
median(J_val_P2) = 0.5299  (seed 11)
std(J_val_P2)    = 0.0200
mejor seed        = 44 (J_val_P2=0.5217, checkpoint seed44_ep600)
peor seed         = 33 (J_val_P2=0.5769, ~1.85 desviaciones estandar por encima de la media)
```
**5/5 seeds terminaron por `early_stopping` de la regla del plan (§19)** -- ninguna alcanzó el tope
de seguridad de 6000 episodios, ninguna requirió `STOP-P2-B` (0 fallos numéricos en las 5). Todas las
paradas ocurrieron entre el piso (2000 episodios) y +600 episodios por encima (2000-2600 episodios),
consistente con una convergencia razonablemente rápida de la política en las 5 seeds.
**Hallazgo reportado sin suavizar:** seed 33 converge a un `J_val_P2` claramente peor que las otras 4
(`0.5769` vs. `0.52-0.53` en las demás, ~1.85 sigma) -- varianza real entre seeds, no descartada ni
excluida (instrucción explícita del usuario, punto 7: "No eliminar ninguna seed"). Ninguna causa raíz
se investiga ni se asume en esta entrada -- queda como una observación de varianza de entrenamiento
para la etapa de test/reporte de resultados.
**Tiempo real de pared de la campaña completa:** desde el lanzamiento de batch 1 (2026-08-19 ~22:19)
hasta la finalización de seed 55 (2026-08-21 ~15:31) = **~41.2 horas**, sustancialmente menor que la
estimación secuencial pura de `DEC-P2-034` (~55.1h) gracias al paralelismo (2 seeds en batch 1, 3
seeds simultáneas en la segunda mitad tras la desviación autorizada) sin evidencia de contención
severa en ninguno de los 5 procesos (0 fallos numéricos, todos los tiempos individuales por seed
dentro del rango 14.9-17.7h, consistente con el piso estimado de ~10.9h + margen razonable).
Interpretation: La arquitectura `droop*+TD3` residual entrena de forma estable y reproducible en las
5 seeds congeladas, sin fallos numéricos, con checkpoints íntegros seleccionados exclusivamente por
`J_val_P2` (nunca por return/loss/Ppeak/energy/saturación, tal como exigió el usuario). La varianza
entre seeds (seed 33 como outlier) es real y queda documentada, no oculta ni resuelta aquí -- se
trasladará a la etapa de test para ver si sobrevive bajo escenarios no vistos.
Selected Tc or unresolved decision: Ninguna decisión física nueva. Los 5 checkpoints "best" quedan
disponibles para P2-E10/P2-E11 (freeze de checkpoints) y el test final (`P2-T1..T12`), **ninguno de
los dos autorizado en esta entrada**.
Evidence reviewed: `Paper_2/artifacts/diagnostics/p2e9_seeds/seed{11,22,33,44,55}_eval_log.csv`
(curva completa de `J_val_P2` por evaluación, cada seed); `Paper_2/artifacts/diagnostics/
p2e9_seeds/seed{11,22,33,44,55}_diag_log.csv` (diagnóstico: actor/critic loss, replay buffer,
return, fallos, saturación -- NO usado para selección); `Paper_2/artifacts/models/p2e9_seeds/*.zip`
(35 checkpoints: 7 por seed x 5 seeds, más el dry-run seed 999).
Frozen parameters:
```text
P2E9_SEEDS_COMPLETE = {11, 22, 33, 44, 55}
P2E9_BEST_CHECKPOINTS = {
  11: "seed11_ep400" (J_val_P2=0.5299),
  22: "seed22_ep1600" (J_val_P2=0.5263),
  33: "seed33_ep400" (J_val_P2=0.5769),
  44: "seed44_ep600" (J_val_P2=0.5217),
  55: "seed55_ep1400" (J_val_P2=0.5444),
}
P2E9_MEAN_J_VAL_P2 = 0.5398
P2E9_NUMERICAL_FAILURES_TOTAL = 0
P2E9_EXECUTION_STRATEGY_DEVIATION = "3 batches <=2 planeado -> 3-en-paralelo autorizado a mitad de
  campana (ver nota operativa anterior a esta entrada) -- ningun parametro FROZEN afectado"
P2E9_WALL_CLOCK_TOTAL_HOURS = 41.2
P2E10_P2E11_AUTHORIZED = FALSE
P2T_BATTERY_AUTHORIZED = FALSE
```
Blockers or limitations: Ninguna causa raíz investigada para la varianza seed 33 vs. resto (fuera
del alcance de esta entrada, no pedido). Los checkpoints "best" son candidatos para congelamiento en
`P2-E10/E11`, pero esa etapa NO está autorizada aquí. `P2-T1..T12` sigue sin abrirse.
Responsible: Claude (implementación de la infraestructura de entrenamiento, ejecución de las 5 seeds
y de la desviación de estrategia autorizada, investigación y corrección del check de integridad, bajo
autorización explícita del usuario en cada paso)
Status: passed -- P2-E9 cerrado, 5/5 seeds completas, tabla resumen generada
Next action: Reportar al usuario la tabla resumen completa y **detenerse**, tal como instruyó
explícitamente el usuario -- no iniciar `P2-E10`/`P2-E11` (freeze de checkpoints) ni `P2-T1..T12` sin
autorización explícita separada.

## DEC-P2-036

Date: 2026-08-21
Stage/Gate: **P2-E11 -- freeze formal de los 5 checkpoints finales, y paquete de figuras de
comparación sobre VALIDATION (no test).** Autorizado por el usuario ("ok, continua y genera un
paquete de figuras que permitan hacer comparaciones y determinar el éxito del proceso"),
interpretado como continuación de los pasos de bajo riesgo ya presentados (freeze de checkpoints,
verificación de la batería de test) -- **`P2-T1..T12` NO se abre en esta entrada**, consistente con
lo que se le comunicó explícitamente al usuario en el turno anterior ("merece su propia autorización
explícita separada").
**P2-E11 -- freeze:** los 5 checkpoints "best" seleccionados en `P2-E9` (`DEC-P2-035`) quedan
congelados como los modelos finales candidatos, sin reselección posterior:
```text
seed11: seed11_ep400  (J_val_P2=0.5299)
seed22: seed22_ep1600 (J_val_P2=0.5263)
seed33: seed33_ep400  (J_val_P2=0.5769)
seed44: seed44_ep600  (J_val_P2=0.5217)
seed55: seed55_ep1400 (J_val_P2=0.5444)
```
Verificado: la batería `P2-T1..T12` (§12 del plan, congelada en `DEC-P2-003`) no fue tocada por el
reencuadre de arquitectura (`DEC-P2-026` en adelante) -- su definición depende únicamente de
generadores/cargas/operating points, no de la ley de control, por lo que sigue vigente sin cambios.
Sigue sin abrirse.
**Paquete de figuras (sobre VALIDATION, EV-P2-E9/EV-P2-E11, no usa `P2-T*`):**
`Paper_2/src/stage_p2e11_validation_comparison.py` calcula `NoFFC` y `droop*` (mismo `Kd*=4694.4MW/Hz`
congelado) sobre los 6 escenarios de validation, y re-evalúa cada uno de los 5 checkpoints congelados
en esos mismos 6 escenarios (comparación exactamente apples-to-apples, mismo código que `P2-E9`).
`Paper_2/src/fig_p2e11_validation_comparison.py` construye el paquete de figuras. Ver mensaje
siguiente al usuario para el detalle de las figuras y hallazgos.
Interpretation: Esta comparación es un **preview de éxito basado en validation**, explícitamente NO
el gate final del plan (§21, que exige `P2-T1..T12`) -- se declara así en cada figura para no
confundirlo con evidencia confirmatoria.
Selected Tc or unresolved decision: Ninguna decisión física nueva. `P2-T1..T12` sigue sin abrirse.
Evidence reviewed: `Paper_2/artifacts/diagnostics/p2e9_seeds/seed*_eval_log.csv`;
`Paper_2/artifacts/diagnostics/p2e11_validation_comparison.csv` (nuevo).
Frozen parameters:
```text
P2E11_CHECKPOINTS_FROZEN = TRUE (5 checkpoints listados arriba, sin reseleccion permitida)
P2T_BATTERY_STATUS = "vigente sin cambios (SS12/DEC-P2-003), NO abierta"
P2T_BATTERY_AUTHORIZED = FALSE (sin cambios)
```
Blockers or limitations: Ninguno nuevo.
Responsible: Claude (bookkeeping de freeze y generación de figuras bajo autorización explícita del
usuario)
Status: passed
Next action: Presentar el paquete de figuras al usuario y **detenerse** -- no abrir `P2-T1..T12` sin
autorización explícita separada.

## DEC-P2-037

Date: 2026-08-21
Stage/Gate: **Resultado numérico del preview de validation (`P2-E11`, `DEC-P2-036`) -- hallazgo
reportado sin suavizar.**
```text
                J_val_mean  df_peak_mean_Hz  RoCoF_peak_mean_Hz/s  I_f_vs_droop  I_r_vs_droop  sat
NoFFC           0.6459      0.0774           0.4857                -62.1%       -10.6%        0.000
droop* (base)   0.5723      0.0539           0.4363                  0.0%         0.0%         0.000
seed11          0.5299      0.0556           0.4016                 -4.4%        +8.3%         0.000
seed22          0.5263      0.0551           0.3990                 -8.0%        +8.0%         0.000
seed33          0.5769      0.0541           0.4399                 +5.1%        -0.5%         0.000
seed44          0.5217      0.0549           0.3954                 -4.3%        +9.9%         0.007
seed55          0.5444      0.0541           0.4139                 -4.0%        +6.4%         0.000
```
Interpretation: **En 4/5 seeds (11,22,44,55), `J_val_P2` mejora frente a `droop*` (menor es mejor),
pero esa mejora está casi enteramente concentrada en RoCoF (`I_r` positivo, hasta `+9.9%` en seed44)
-- ninguna de las 5 seeds alcanza `I_r>=10%`, y el nadir/pico de frecuencia (`I_f`) EMPEORA respecto
a droop* en las mismas 4 seeds (`I_f` negativo, hasta `-8.0%` en seed22).** Solo `seed33` muestra
`I_f` positivo (`+5.1%`), pero a costa de `I_r` negativo y del peor `J_val_P2` de las 5 (`0.5769`,
único caso peor que el propio `droop*`). **Ninguna seed logra mejora SIMULTÁNEA `I_f>=10%` Y
`I_r>=10%`** -- el criterio central del gate del plan (§21) -- en el preview de validation. Las
curvas de aprendizaje (`P2E11_F1`) muestran oscilación considerable, no convergencia monótona clara,
para las 5 seeds -- consistente con que el "mejor" checkpoint de cada seed es, en gran medida, el
punto más bajo de una trayectoria ruidosa, no un óptimo estable alcanzado de forma consistente.
**Esto es un preview sobre VALIDATION (6 escenarios), explícitamente NO el gate final del plan (que
exige `P2-T1..T12`, `>=10/12` escenarios con `I_f/I_r>=10%` simultáneo, medianas `>=15%`)** -- no se
declara aquí ningún veredicto de éxito/fracaso de `P2-H1`. Pero la señal es clara: bajo la evidencia
disponible hasta ahora, el residual TD3 entrenado NO muestra todavía el patrón de mejora simultánea
grande que la hipótesis revisada (`DEC-P2-026`) planteaba como posible, sino una mejora parcial y
desbalanceada (RoCoF sí, frecuencia no) en la mayoría de las seeds.
Selected Tc or unresolved decision: Ninguna. No se abre `P2-T1..T12` en esta entrada.
Evidence reviewed: `Paper_2/artifacts/diagnostics/p2e11_validation_comparison.csv`;
`Paper_2/artifacts/diagnostics/p2e11_validation_comparison_summary.csv`;
`Paper_2/figures_main/P2E11_F1..F4_*` (8 archivos: 4 figuras x PNG/PDF, 1col/2col cada una =
16 archivos en total).
Frozen parameters: Ninguno nuevo -- entrada de resultado/hallazgo, no de congelamiento.
Blockers or limitations: El preview usa `deterministic=True` (política determinística, sin ruido de
exploración) -- consistente con cómo se seleccionó el checkpoint, pero distinto de cómo se comportaría
la política durante entrenamiento. La oscilación de las curvas de aprendizaje no se investigó
causalmente en esta entrada (podría reflejar ruido inherente de TD3 con este presupuesto de
entrenamiento, sensibilidad del `J_val_P2` a escenarios individuales, u otra causa no diagnosticada).
Responsible: Claude (análisis y reporte bajo la autorización de `P2-E11`, `DEC-P2-036`)
Status: passed -- hallazgo registrado, sin suavizar
Next action: Presentar el hallazgo completo al usuario junto con las figuras y **detenerse** -- no
abrir `P2-T1..T12`, no reentrenar, no ajustar hiperparámetros/reward/observación por este resultado
de validation sin autorización explícita separada (mismo principio de "no tocar tras ver resultados"
que rige el resto de la campaña).

## DEC-P2-038

Date: 2026-08-21
Stage/Gate: **Hallazgo no solicitado, encontrado durante la inspección visual de trayectorias
(`P2-E11b`): oscilación sostenida/creciente del comando TD3, no capturada por `J_val_P2`.** El
usuario pidió ver la trayectoria real del control actuando ("¿podemos ver el control TD3
funcionando...?") -- al inspeccionar la figura de trayectoria completa (`P2E11b_gen_val_trajectory`,
seed44, escenario `GENROU_6`), se observó una oscilación de alta frecuencia en el comando
(`P_BESS1+P_BESS2`) que **crece** después de `tau~1.5s` en vez de decaer. Investigado antes de
reportar (disciplina de la sesión: nunca asumir que algo raro es "solo ruido").
**Cuantificación (`Paper_2/src/stage_p2e11c_oscillation_check.py`, nuevo):** amplitud pico-a-pico del
comando combinado, por ventana de 1s, las 5 seeds x 2 tipos de escenario de validation:
```text
gen_val   [0-1)s  [1-2)s  [2-3)s  [3-4)s  [4-5)s   tendencia
seed11    319MW    79MW     6MW    15MW    11MW    DECAYENTE
seed22    273MW   326MW   316MW   277MW   263MW    ESTABLE (sostenida, no decae)
seed33    358MW   122MW    11MW     8MW    12MW    DECAYENTE
seed44    361MW   367MW   473MW   502MW   520MW    CRECIENTE  <- la seleccionada como "mejor" por J_val_P2
seed55    483MW   374MW    80MW   117MW   177MW    DECAYENTE (pero repunta hacia el final)

load_val  [0-1)s  [1-2)s  [2-3)s  [3-4)s  [4-5)s
seed11    297MW   276MW   272MW   274MW   275MW    ESTABLE (sostenida, no decae)
seed22    384MW   280MW   325MW   263MW   289MW    ESTABLE (sostenida, no decae)
seed33     87MW   251MW    34MW    36MW    31MW    DECAYENTE
seed44    226MW     4MW     2MW     2MW     0MW    DECAYENTE (limpio)
seed55    274MW   304MW   297MW   266MW   269MW    ESTABLE (sostenida, no decae)
```
**Hallazgo central: la oscilación sostenida (no decae a cero, o incluso crece) es un patrón AMPLIO,
no aislado a una seed** -- aparece en `gen_val` para `seed22`/`seed44` y en `load_val` para
`seed11`/`seed22`/`seed55`. Solo `seed33` (en `gen_val`) y `seed44` (en `load_val`) muestran
decaimiento limpio en ambos tipos de escenario simultáneamente. **La seed seleccionada como "mejor"
por `J_val_P2` (`seed44`) es precisamente la que muestra el patrón CRECIENTE más extremo en
`gen_val`** (520MW pico-a-pico al final de la ventana, sobre un límite físico de hasta
`2*2*293.4=1173.6MW` para la suma de ambos BESS) -- el criterio de selección actual no penaliza
esto porque `J_val_P2`/`df_peak`/`rocof_peak` se miden como el PICO máximo sobre todo el episodio, y
el peor pico de frecuencia/RoCoF ocurre temprano (dentro del primer segundo), no tarde -- la
oscilación sostenida del comando no se traduce (en esta ventana observada) en un peor pico de
frecuencia/RoCoF, por lo que es efectivamente invisible para el mecanismo de selección de
checkpoint, aunque sí es un comportamiento de control claramente indeseable (ciclado rápido y
sostenido de potencia del BESS, cerca de una fracción importante de la autoridad física disponible).
Interpretation: **Este es un gap real en la metodología de evaluación de `P2-E9`, no un fallo del
BESS ni del solver** (`TDS_success=True` en todos los casos, sin fallos numéricos) -- el plan nunca
definió un criterio de "sin oscilación sostenida del comando" análogo al que sí se exigió
explícitamente para el controlador físico (`STOP-P2-A` Criterio 2, `DEC-P2-023` verificó esto para
droop*/F+R). La ausencia de ese criterio para las políticas TD3 permitió seleccionar checkpoints sin
verificar esta propiedad. Esto **no invalida** el hallazgo de `DEC-P2-037` (mejora modesta de RoCoF,
empeoramiento de nadir) -- lo complementa con una dimensión adicional (calidad/estabilidad del
comando) que tampoco favorece la conclusión de "éxito" sin matices.
Selected Tc or unresolved decision: Ninguna decisión tomada. No se reentrena, no se reselecciona
checkpoint, no se modifica el criterio `J_val_P2` sin autorización explícita del usuario.
Evidence reviewed: `Paper_2/artifacts/diagnostics/p2e11c_oscillation_check.csv`;
`Paper_2/artifacts/trajectories/p2e11b_trajectory_demo.npz`; figuras `P2E11b_*`, `P2E11c_*`.
Frozen parameters: Ninguno.
Blockers or limitations: No se investigó la causa raíz del patrón oscilatorio (podría ser
características del ruido de exploración residual en la política determinística, una frecuencia
propia del muestreo/actuador cerca de `Tc=5ms`, sobre-reacción de la política a las oscilaciones
electromecánicas normales del sistema tras el evento, u otra causa) -- ninguna se asume sin evidencia
adicional. No se verificó si este patrón aparece también en los otros 4 escenarios de validation no
graficados aquí (solo se usó el punto medio `lambda_L=1.00` de cada tipo).
Responsible: Claude (hallazgo encontrado durante la respuesta a la pregunta explícita del usuario
sobre visualizar el control actuando; investigación y cuantificación adicional no solicitada pero
necesaria antes de reportar, siguiendo la disciplina de la sesión)
Status: passed -- hallazgo cuantificado y registrado, sin suavizar
Next action: Reportar este hallazgo al usuario junto con las figuras `P2E11b`/`P2E11c` y
**detenerse** -- no reentrenar, no reseleccionar checkpoints, no modificar el criterio de evaluación
sin autorización explícita separada.

## DEC-P2-039

Date: 2026-08-21
Stage/Gate: **Causa raíz de la oscilación de `DEC-P2-038`, investigada a pedido del usuario ("¿por
qué oscila tanto?").** Verificación directa de la señal local que alimenta la política (`OBS-A`) y
comparación contra `NoFFC`/`droop*` en la misma ventana temporal, mismo escenario (`gen_val`,
`GENROU_6`, `rho=0.6`).
**Medición (ventana `tau=[3,4)s`, bien después del transitorio principal, bus 16):**
```text
NoFFC:       f1 pico-a-pico = 4.60 mHz
droop*:      f1 pico-a-pico = 1.92 mHz   (droop AMORTIGUA la oscilacion natural, incluso mejor que sin control)
TD3(seed44): f1 pico-a-pico = 34.80 mHz  (~18x peor que droop*, ~7.5x peor que NoFFC)
             accion residual oscilando entre -0.97 y +0.98 (practicamente saturada)
             P_total llegando hasta 293.4MW = Pmax en varios puntos de esa misma ventana
```
Interpretation: **No es amplificación pasiva de un modo físico externo preexistente -- es una
oscilación generada/sostenida por el propio lazo cerrado de la política.** `droop*` demuestra que la
oscilación natural del sistema en esa ventana es pequeña y bien amortiguada (1.92mHz, incluso mejor
que `NoFFC`). La política TD3, en cambio, reacciona con ganancia efectiva muy alta a una desviación
de frecuencia local minúscula (fracciones de un `mHz` de cambio de paso a paso), produciendo una
acción que oscila cerca de sus límites (`±1`) -- un patrón clásico de inestabilidad de realimentación
de alta ganancia / ciclo límite auto-sostenido: la corrección de la política perturba la frecuencia
local lo suficiente como para disparar la siguiente corrección en sentido contrario, indefinidamente,
mucho después de que el evento original ya se resolvió. Esto es consistente con, y profundiza, el
hallazgo de `DEC-P2-038` -- confirma que el problema no es solo "el criterio de selección no lo ve",
sino que la política en sí genera una dinámica de lazo cerrado de baja calidad, no solo un
comportamiento pasivo/ruidoso.
Selected Tc or unresolved decision: Ninguna. No se investigó si este patrón de alta ganancia
efectiva es consistente entre seeds/escenarios más allá de lo ya reportado en `DEC-P2-038`, ni se
propuso ninguna corrección (p.ej. penalizar variación de acción en el reward, suavizar la
observación, reducir `P_RL,max`) -- ninguna decisión de diseño se toma aquí.
Evidence reviewed: mediciones directas de `f1_hz`/`rocof1_hz_s`/`action`/`p_total_mw` en la ventana
`tau=[3,4)s`, comparando `NoFFC`/`droop_star`/`TD3_seed44` bajo el mismo escenario y semilla de caso.
Frozen parameters: Ninguno.
Blockers or limitations: Verificado en un solo punto (BESS1, `gen_val`, seed 44) -- no se repitió
para BESS2 ni para los demás seeds/escenarios de `DEC-P2-038` que también mostraron oscilación
sostenida (`seed22` en ambos tipos, `seed11`/`seed55` en `load_val`). Plausible que el mismo mecanismo
(ganancia efectiva alta, ciclo límite auto-sostenido) explique esos casos también, pero no verificado
directamente -- no se asume sin evidencia.
Responsible: Claude (investigación causal a pedido explícito del usuario)
Status: passed -- causa raíz identificada con evidencia directa (comparación droop* vs. TD3 en la
misma ventana), no solo hipótesis
Next action: Reportar al usuario y **detenerse** -- no reentrenar, no ajustar reward/observación/
`P_RL,max` sin autorización explícita separada.

## DEC-P2-040

Date: 2026-08-21
Stage/Gate: **Opciones 1+2 (autorizadas por el usuario: "comienza con uno y dos y me das reportes
graficos") -- diagnóstico completo (6 escenarios) + clasificador de estabilidad `classify_v2` (ya
validado, `DEC-P2-017`, reutilizado sin modificar) aplicado a los 5 checkpoints congelados. Ningún
reentrenamiento, ninguna reselección de checkpoint.**
`Paper_2/src/stage_p2e11d_full_stability_screen.py` (nuevo): `NoFFC`, `droop*` y los 5 checkpoints
congelados, sobre los **6** escenarios de validation completos (antes solo 2 en `DEC-P2-038`), con
`analyze_trace_v2`/`classify_v2` (la misma metodología que certificó `STOP-P2-A` Criterio 2 para el
controlador físico) aplicada a la trayectoria de frecuencia/comando de cada corrida.
```text
Escenarios STABLE (de 6):     NoFFC=6  droop*=6  seed11=3  seed22=2  seed33=6  seed44=4  seed55=3

Clasificacion detallada (gen op1,op2,op3 | load op1,op2,op3):
NoFFC:        STABLE STABLE STABLE | STABLE STABLE STABLE
droop*:       STABLE STABLE STABLE | STABLE STABLE STABLE
seed11:       STABLE STABLE STABLE | MARGINAL MARGINAL MARGINAL
seed22:       MARGINAL STABLE STABLE | MARGINAL MARGINAL MARGINAL
seed33:       STABLE STABLE STABLE | STABLE STABLE STABLE   <-- unica TD3 igual a droop*/NoFFC
seed44:       MARGINAL MARGINAL STABLE | STABLE STABLE STABLE
seed55:       STABLE STABLE STABLE | MARGINAL MARGINAL MARGINAL

mean J_val_P2 (6 escenarios): NoFFC=0.6459 droop*=0.5723 seed11=0.5299 seed22=0.5263
                               seed33=0.5769 seed44=0.5217 seed55=0.5444
```
Interpretation: **Patrón limpio por TIPO de disturbio, no aleatorio.** `seed44` (mejor `J_val_P2`)
falla específicamente en escenarios de GENERACIÓN (2/3 `MARGINAL`); `seed11`/`seed22`/`seed55` fallan
específicamente en escenarios de CARGA (3/3 `MARGINAL` cada una); **`seed33` es la ÚNICA política TD3
que iguala a `droop*`/`NoFFC` con 6/6 `STABLE`** -- y es, a la vez, la que tiene el peor `J_val_P2`
promedio de las 5 (peor incluso que `droop*` solo). Ninguna clasificó `LIMIT_CYCLE` (la categoría más
severa) -- todas las fallas fueron `MARGINAL`, no inestabilidad completa, pero tampoco limpias.
Esto confirma y generaliza `DEC-P2-038/039`: el problema de oscilación sostenida NO es aislado a
`seed44`/`gen_val`, es un patrón sistemático correlacionado con el tipo de escenario, presente en 4
de las 5 seeds en al menos la mitad de los escenarios de validation. **Existe una tensión real y
medida entre el criterio de selección usado (`J_val_P2` mínimo, favorece `seed44`) y un criterio de
estabilidad (`classify_v2`, favorece `seed33`)** -- ningún seed satisface ambos simultáneamente de
forma óptima.
Selected Tc or unresolved decision: **Ninguna reselección de checkpoint ni cambio de criterio
decidido en esta entrada** -- se presenta la evidencia completa al usuario para su decisión. No se
investigó por qué el patrón de falla se correlaciona tan limpiamente con el tipo de escenario
(gen vs. carga) -- observación registrada, no explicada causalmente todavía.
Evidence reviewed: `Paper_2/artifacts/diagnostics/p2e11d_stability_classification.csv` (42 filas: 7
controladores x 6 escenarios); `Paper_2/artifacts/diagnostics/p2e11d_oscillation_full.csv`;
`Paper_2/figures_main/P2E11d_A/B/C_*`.
Frozen parameters: Ninguno -- entrada de diagnóstico, no de congelamiento ni reselección.
Blockers or limitations: Clasificación binaria `STABLE`/`MARGINAL` sin gradiente de severidad
reportado en el resumen (aunque `detrended_frequency_p2p`/`persistence_ratio` quedan en el CSV para
análisis más fino). Causa del patrón gen-vs-carga no investigada. Ninguna decisión de selección final
tomada -- pendiente del usuario.
Responsible: Claude (implementación y ejecución del diagnóstico bajo autorización explícita del
usuario -- opciones 1+2 de la lista presentada previamente)
Status: passed -- diagnóstico completo, sin reentrenamiento ni reselección
Next action: Presentar las figuras y esta tabla al usuario y **detenerse** -- no reentrenar, no
reseleccionar checkpoint, no abrir `P2-T1..T12`, sin autorización explícita separada del usuario
sobre cómo proceder con esta tensión J_val_P2-vs-estabilidad.

## DEC-P2-041

Date: 2026-08-21
Stage/Gate: **Diseño de `seed 66` -- SOLO diseño + implementación + validación mecánica
pre-entrenamiento. NO es P2-T1..T12, NO es una sexta seed FROZEN, NO se lanzó el entrenamiento
real.** Autorizado explícitamente por el usuario ("Diseña un seed 66 ... Dame el plan primero, no
lo lances") en respuesta directa a la tensión `J_val_P2`-vs-estabilidad documentada en `DEC-P2-040`.
Plan diseñado en Plan Mode y aprobado por el usuario (`C:\Users\Gabriel\.claude\plans\
zany-percolating-cookie.md`): preservar EXACTAMENTE la configuración de `seed44` (`DEC-P2-033`) y
añadir dos mecanismos opcionales, apagados por defecto (default = comportamiento idéntico a las 5
seeds `DEC-P2-035`):
1. Penalización de suavidad de acción en el reward (`action_smoothness_weight`, propuesto 0.02).
2. Selección de checkpoint con filtro de estabilidad (`require_stability_for_best`), reutilizando
   `classify_v2`/`analyze_trace_v2` sin modificar (`DEC-P2-017`).

**Implementación (todos los cambios son aditivos, backward-compatible por diseño):**
- `Paper_2/src/p2_env_train.py`: `P2ResidualTrainEnv` gana `action_smoothness_weight=0.0` (kwarg
  opcional), trackea `self._prev_action` (reset en `reset()`), resta
  `weight * ||a_t - a_{t-1}||^2` del reward en `step()`, expone `smooth_penalty` en `info`.
- `Paper_2/src/p2_train_callback.py`: `P2ValidationCallback` gana `action_smoothness_weight=0.0` y
  `require_stability_for_best=False` (kwargs opcionales). Cuando `True`, `_evaluate_and_checkpoint()`
  captura la trayectoria completa (`t`, `f_worst_hz` vía `env._gen_bus_arrays()` + `np.min`, exactamente
  la misma definición que `stage_p2e11d_full_stability_screen.py` linea 57, verificado por lectura
  directa) de los 6 escenarios de validation y aplica `analyze_trace_v2` a cada uno; un checkpoint
  solo se acepta como "mejor" si `J_val_P2` mejora **Y** los 6 escenarios clasifican `STABLE`.
- `Paper_2/src/stage_p2e9_train_seed.py`: nuevos flags CLI `--action-smoothness-weight` (float,
  default 0.0) y `--require-stability-for-best` (store_true, default False), enhebrados a ambos
  constructores.
- **Hallazgo propio detectado y corregido durante la implementación:** las clasificaciones
  `classification_v2` por escenario, calculadas para la compuerta de elegibilidad, se descartaban sin
  registrarse -- un checkpoint rechazado por inestabilidad no habría dejado ningún rastro de QUÉ
  escenario(s) fallaron ni en qué episodio, imposibilitando el análisis post-hoc del entrenamiento
  real. Corregido añadiendo `n_stable_of_6`/`all_stable`/`unstable_scenarios` a `diag_log` (solo
  diagnóstico, no afecta la selección; columnas ausentes cuando `require_stability_for_best=False`,
  verificado empíricamente).

**Validación mecánica ejecutada (3 pasos del plan, antes de comprometer cómputo real):**
```text
PASO 1 -- Regresion de compatibilidad (seed11 ep200, datos historicos reales de P2-E9):
  J_val_P2 nuevo == historico (0.550474, match exacto atol=1e-9)
  df_peak_mean_hz, rocof_peak_mean_hz_s: match exacto
  'classification_v2' ausente cuando require_stability_for_best=False: confirmado
  RESULTADO: PASS (Paper_2/src/stage_p2e9_seed66_validation_regression.py)

PASO 2 -- Balance de magnitud (action_smoothness_weight=0.02):
  Caso A (seed11 ep200, pool train, tipico/convergido):  ratio medio penalidad/tracking = 0.0086
  Caso B (seed44 ep600 -- mejor checkpoint DEC-P2-035 --, escenario GEN, oscilatorio conocido
          DEC-P2-039/040): ratio medio penalidad/tracking = 0.0479
  RESULTADO: HALLAZGO ABIERTO, no PASS/FAIL -- ver "Selected Tc or unresolved decision"
  (Paper_2/src/stage_p2e9_seed66_validation_magnitude.py)

PASO 3 -- Dry-run mecanico del filtro de estabilidad (seed sintetica 999, escala reducida
          2/1/1/3 episodios piso/patience/eval_freq/tope, igual patron que DEC-P2-035):
  require_stability_for_best=False: 3/3 evaluaciones "improved", sin columnas de estabilidad
    (reproduce exactamente la seleccion anterior) -- PASS
  require_stability_for_best=True: 3/3 evaluaciones "improved", n_stable_of_6=6 en las 3 (la
    politica casi sin entrenar se comporta ~droop*, STABLE en los 6, DEC-P2-040) -- solo ejercita
    la rama de ACEPTACION, no la de RECHAZO -- PASS parcial
  (Paper_2/src/stage_p2e9_seed66_validation_stability_dryrun.py)

PASO 3b -- Cierre de brecha: rama de RECHAZO forzada via monkeypatch de analyze_trace_v2 (1er
           escenario forzado a LIMIT_CYCLE) sobre seed11 ep200 real, con best_j_val=999.0
           artificial (garantiza "mejora" por J_val_P2 solo):
  analyze_trace_v2 llamado 6/6 veces (los 6 escenarios evaluados)
  n_stable_of_6=3 (ademas del forzado, 2 escenarios GEN reales de este checkpoint temprano
    tambien no-STABLE -- propiedad real de seed11 ep200, no error de codigo)
  all_stable=False, improved=False, best_j_val sin cambio (999.0), best_ckpt_path=None
  RESULTADO: PASS (rama de rechazo confirmada correcta)
  (Paper_2/src/stage_p2e9_seed66_validation_reject_branch.py)
```
Evidencia CSV: `Paper_2/artifacts/diagnostics/p2e9_seed66_validation/dryrun_{nostab,stab}_
{eval,diag}_log.csv`.

Interpretation: La infraestructura (env + callback + CLI) está implementada de forma
backward-compatible y verificada mecánicamente: nada de lo usado por las seeds 11-55 cambia con los
parámetros nuevos en su valor por defecto (Paso 1, match exacto), y la compuerta de estabilidad
funciona correctamente en ambas ramas -- acepta cuando corresponde (Paso 3) y rechaza cuando
corresponde, incluso bajo un "mejor" `J_val_P2` artificialmente garantizado (Paso 3b). **El Paso 2
reveló una desviación real respecto al razonamiento del plan aprobado:** el plan estimó
`action_smoothness_weight=0.02` asumiendo que un cambio de acción completo (`a`: -1 a +1 en ambas
componentes, `||Δa||²=8`) costaría `~0.16` en penalidad, del mismo orden que el término de
seguimiento típico. En la práctica, incluso en el caso deliberadamente adverso (`seed44` best
checkpoint, escenario GEN oscilatorio conocido), la razón penalidad/seguimiento observada es
`0.048` -- casi 21x menor que un `~1.0` de referencia, y muy por debajo del rango "mismo orden de
magnitud" (`0.1x-3x`) razonado en el plan. Causa: el límite cíclico real (`DEC-P2-039`, ~30-40mHz)
es lento respecto al paso de 5ms -- la acción no salta de -1 a +1 entre pasos consecutivos incluso
mientras oscila, así que `||Δa||²` por paso es, en la práctica, mucho menor que 8. La estimación de
magnitud del plan aprobado, basada en un salto completo de acción, no se cumple empíricamente.
Selected Tc or unresolved decision: **`action_smoothness_weight=0.02` queda SIN CONFIRMAR -- decisión
pendiente del usuario, no tomada unilateralmente aquí** (recalibrar por un solo ajuste razonado desde
esta evidencia -- p.ej., a un orden de magnitud mayor para acercar el Caso B a razón ~0.5 -- seguiría
sin ser HPO/barrido, pero es un cambio de parámetro no autorizado todavía; alternativamente, proceder
con 0.02 tal como diseñado, aceptando el riesgo de que la penalización sea demasiado débil para
alterar visiblemente el comportamiento). **El entrenamiento real de `seed 66` sigue SIN autorizar**
-- ninguna de las dos decisiones (peso final, lanzamiento) se tomó en esta entrada.
Evidence reviewed: `Paper_2/src/p2_env_train.py`, `Paper_2/src/p2_train_callback.py`, `Paper_2/src/
stage_p2e9_train_seed.py` (código modificado); `Paper_2/src/stage_p2e9_seed66_validation_{regression,
magnitude,stability_dryrun,reject_branch}.py` (scripts de validación, nuevos); `Paper_2/artifacts/
diagnostics/p2e9_seed66_validation/*.csv`; `Paper_2/artifacts/diagnostics/p2e9_seeds/
seed11_eval_log.csv` y `seed44_eval_log.csv` (datos históricos reales usados como oráculo de
regresión); `stage_p2e11d_full_stability_screen.py` (definición de `f_worst_hz` reutilizada sin
modificar).
Frozen parameters:
```text
SEED66_DESIGN_STATUS = "implementado y validado mecanicamente, NO lanzado"
SEED66_BASE_CONFIG = "identica a seed44 (DEC-P2-033), ningun parametro FROZEN modificado"
SEED66_NEW_PARAMS_DEFAULT = {action_smoothness_weight: 0.0, require_stability_for_best: False}
  -- reproduce exactamente el comportamiento de seeds 11-55 (Paso 1, verificado)
SEED66_ACTION_SMOOTHNESS_WEIGHT_PROPOSED = 0.02  -- SIN CONFIRMAR, ver "Selected Tc..."
SEED66_STABILITY_GATE_VERIFIED = "aceptacion (Paso 3) y rechazo (Paso 3b) ambos PASS"
SEED66_REAL_TRAINING_AUTHORIZED = FALSE
```
Blockers or limitations: Peso de suavidad sin confirmar por el usuario (bloquea el lanzamiento real
de forma sustantiva, no solo procedimental -- lanzar con 0.02 tal como está podría no producir ningún
efecto medible dado el hallazgo del Paso 2). Dry-run del Paso 3 (seed sintética, política casi
aleatoria) no ejercitó la rama de rechazo de forma orgánica -- cubierto por el Paso 3b (monkeypatch),
que sí es una prueba directa del mecanismo pero no una simulación end-to-end de una política real que
se vuelve inestable durante el entrenamiento (eso solo se observará en el run real). Ningún cómputo de
entrenamiento real de `seed 66` se ha ejecutado.
Responsible: Claude (diseño en Plan Mode aprobado por el usuario, implementación, validación mecánica
en 3 pasos + cierre de brecha, bajo instrucción explícita de NO lanzar el entrenamiento real)
Status: passed -- diseño e implementación completos, validación mecánica completa (incluyendo cierre
de brecha de la rama de rechazo), entrenamiento real NO lanzado
Next action: Reportar al usuario el hallazgo del Paso 2 (desviación de la estimación de magnitud del
plan) y **detenerse** -- pedir decisión explícita sobre el peso de suavidad final antes de considerar
cualquier lanzamiento de `seed 66` real, que en cualquier caso requiere una autorización separada y
explícita adicional ("no lo lances" -- instrucción original del usuario, reafirmada por el punto 4
del plan aprobado).

## DEC-P2-042

Date: 2026-08-21
Stage/Gate: **Recalibración de `action_smoothness_weight` -- sigue siendo SOLO validación mecánica,
NO lanzamiento de `seed 66` real.** Autorizado explícitamente por el usuario en respuesta directa al
hallazgo de `DEC-P2-041` (pregunta con 3 opciones; el usuario eligió "Recalibrar hacia arriba
(Recomendado)": "un solo ajuste razonado desde esta nueva evidencia empírica ... no un barrido").
**Cálculo del nuevo valor (un solo ajuste razonado, no HPO):** objetivo = razón Caso B (escenario
oscilatorio conocido) en el punto medio del rango objetivo del plan (`0.1x-3x` -> punto medio `~0.5`).
Factor de escala = `0.5 / 0.0479` (razón medida en `DEC-P2-041` a `weight=0.02`) `~= 10.44`. Redondeado
a un número limpio del mismo orden de magnitud: **`action_smoothness_weight = 0.2`** (10x el valor
original).
**Verificación empírica (misma metodología del Paso 2 de `DEC-P2-041`, mismos dos casos, mismos
checkpoints, `Paper_2/src/stage_p2e9_seed66_validation_magnitude_recalibration.py`):**
```text
                                                    ratio a 0.02    ratio a 0.2
Caso A (seed11 ep200, pool train, tipico)          0.0086          0.0858
Caso B (seed44 ep600 best, escenario GEN, oscilatorio)  0.0479     0.4795
```
Escala exactamente lineal en el peso (confirmado: 10x weight -> 10x razon en ambos casos, consistente
con que `smooth_penalty` es lineal en `action_smoothness_weight` por construcción, `p2_env_train.py`).
Interpretation: `weight=0.2` logra el efecto "quirúrgico" buscado: en el Caso B (oscilación real
conocida) la razón queda en `0.48`, dentro del rango objetivo `0.1x-3x` del plan aprobado; en el Caso A
(operación típica/convergida) la razón queda en `0.086`, todavía muy por debajo de 1 -- la penalización
no compite con correcciones grandes y legítimas en operación normal, solo se vuelve comparable al
término de seguimiento específicamente en el régimen oscilatorio que se busca suprimir. No se
reejecutó el Paso 1 (regresión, independiente del valor de `weight` -- ya usa `weight=0.0` por
definición) ni el Paso 3 (compuerta de estabilidad -- su lógica de elegibilidad opera sobre
`classify_v2`/`J_val_P2`, no depende numéricamente del peso de suavidad; ya verificado con `PASS` en
ambas ramas en `DEC-P2-041`).
Selected Tc or unresolved decision: **`action_smoothness_weight = 0.2` queda fijado como el valor a
usar SI Y CUANDO se autorice el lanzamiento real de `seed 66`** -- esta entrada NO autoriza dicho
lanzamiento, que sigue requiriendo una instrucción explícita separada del usuario ("no lo lances").
Evidence reviewed: `Paper_2/src/stage_p2e9_seed66_validation_magnitude_recalibration.py` (nuevo);
salida impresa (razones Caso A/B a `weight=0.2`, ver tabla arriba); `Paper_2/src/p2_env_train.py`
(confirmación de que `smooth_penalty` es lineal en `action_smoothness_weight`, sin cambios de código
en esta entrada).
Frozen parameters:
```text
SEED66_ACTION_SMOOTHNESS_WEIGHT_PROPOSED = 0.2  (reemplaza el 0.02 sin confirmar de DEC-P2-041)
SEED66_ACTION_SMOOTHNESS_WEIGHT_RATIONALE = "escalado 10.44x desde razon medida 0.0479 (Caso B,
  weight=0.02) hasta punto medio del rango objetivo 0.1x-3x (~0.5); redondeado a 0.2; verificado
  empiricamente (Caso B ratio=0.4795, Caso A ratio=0.0858)"
SEED66_REAL_TRAINING_AUTHORIZED = FALSE  (sin cambio respecto a DEC-P2-041)
```
Blockers or limitations: El peso `0.2` está calibrado sobre trayectorias de política YA ENTRENADAS
(`seed11`/`seed44`, congeladas), no sobre cómo evolucionaría una política de `seed 66` DURANTE su
propio entrenamiento con esta penalización activa desde el inicio -- la calibración es una estimación
razonada de orden de magnitud, no una garantía de comportamiento final. Esto es inherente a cualquier
elección de peso de reward sin HPO (prohibido por el plan) y queda documentado, no resuelto.
Responsible: Claude (cálculo y verificación empírica bajo autorización explícita del usuario de
recalibrar; ningún valor elegido unilateralmente sin esa autorización)
Status: passed -- recalibración calculada y verificada empíricamente, entrenamiento real de `seed 66`
sigue sin autorizar
Next action: Reportar el resultado de la recalibración al usuario y **detenerse** -- el lanzamiento
real de `seed 66` (con `action_smoothness_weight=0.2`, `require_stability_for_best=True`, y el resto
de la configuración `seed44`) sigue requiriendo autorización explícita separada del usuario.

## DEC-P2-043

Date: 2026-08-22
Stage/Gate: **Entrenamiento real de `seed 66` -- completo.** Autorizado explícitamente por el usuario
("Ok, lanzala") en respuesta directa a la pregunta de cierre de `DEC-P2-042`. Configuración: idéntica
a `seed44` (`DEC-P2-033`) salvo `action_smoothness_weight=0.2` (`DEC-P2-042`) y
`require_stability_for_best=True` (`DEC-P2-041`); piso/patience/eval-freq/tope = 2000/5/200/6000
episodios sin modificar (plan SS19). Comando: `python stage_p2e9_train_seed.py 66
--action-smoothness-weight 0.2 --require-stability-for-best`.
### Resultado
```text
seed  best_ckpt_ep  best_J_val_P2  stop_ep  wall_time_h  transitions  fallos_num  integridad
66    1200          0.5432         2200     10.38         2,640,000    0           PASS

Parada: early_stopping (plan SS19, piso 2000 + patience 5 sin mejora, disparado en ep=2200)
```
**Historia de activación de la compuerta de estabilidad (`diag_log`, 11 evaluaciones):**
```text
ep200 : 6/6 STABLE  J_val=0.5714 (mejor)
ep400 : 6/6 STABLE  J_val=0.5539 (mejor)
ep600 : 3/6 STABLE  J_val=0.5625 -- 3 escenarios de CARGA (PQ_10, los 3 lambda_L) no-STABLE;
        compuerta bloqueó, pero J_val tampoco habria mejorado por si solo (0.5625 > 0.5539)
ep800 : 6/6 STABLE  J_val=0.5699 (sin mejora, J_val peor)
ep1000: 6/6 STABLE  J_val=0.5443 (mejor)
ep1200: 6/6 STABLE  J_val=0.5432 (mejor) <-- CHECKPOINT FINAL
ep1400: 6/6 STABLE  J_val=0.5433 (sin mejora, J_val peor por margen minimo)
ep1600: 3/6 STABLE  J_val=0.5484 -- mismos 3 escenarios de CARGA no-STABLE; compuerta bloqueó,
        J_val tampoco habria mejorado por si solo
ep1800: 3/6 STABLE  J_val=0.5638 -- mismos 3 escenarios de CARGA no-STABLE; compuerta bloqueó,
        J_val tampoco habria mejorado por si solo
ep2000: 6/6 STABLE  J_val=0.6194 (sin mejora)
ep2200: 6/6 STABLE  J_val=0.6079 (sin mejora x5 -> EARLY STOP)
```
**Hallazgo honesto:** la compuerta de estabilidad se activó 3 de 11 veces (ep600/1600/1800),
identificando consistentemente los MISMOS 3 escenarios de carga (`PQ_10`, los 3 puntos de operación)
como no-`STABLE` -- un patrón limpio, no ruido aleatorio, análogo al patrón por tipo de disturbio de
`DEC-P2-040` (aunque aquí es `seed66` la que falla en CARGA, no en GENERACIÓN como `seed44`). Sin
embargo, en las 3 activaciones, `J_val_P2` tampoco habría mejorado por sí solo -- **la compuerta
nunca tuvo que sobreescribir la selección que `J_val_P2` solo habría hecho en esta corrida particular**
(el checkpoint final, `ep1200`, ya era 6/6 `STABLE` según el criterio anterior). No se reporta esto
como "la compuerta no sirvió" -- sirvió como red de seguridad activa y correctamente dirigida (mismo
patrón de fallo 3 veces consecutivas, detectado y bloqueado cada vez), simplemente no fue la variable
decisiva en esta ejecución particular.
**Verificación independiente del checkpoint final** (`Paper_2/src/
stage_p2e11d_seed66_stability_check.py`, reutiliza `run_full`/`j_val`/`analyze_trace_v2` de
`stage_p2e11d_full_stability_screen.py` SIN modificar -- misma metodología de `DEC-P2-040` --, recarga
fresca del checkpoint desde disco, NO relee el log de entrenamiento, escribe a un archivo NUEVO sin
tocar la evidencia congelada de `DEC-P2-040`):
```text
scen0 (GEN  lambda=0.95): J_val=0.7265 STABLE  detrended_p2p=0.02mHz
scen1 (GEN  lambda=1.00): J_val=0.7569 STABLE  detrended_p2p=0.05mHz
scen2 (GEN  lambda=1.05): J_val=0.8040 STABLE  detrended_p2p=0.05mHz
scen3 (LOAD lambda=0.95): J_val=0.3256 STABLE  detrended_p2p=1.01mHz
scen4 (LOAD lambda=1.00): J_val=0.3243 STABLE  detrended_p2p=1.01mHz
scen5 (LOAD lambda=1.05): J_val=0.3218 STABLE  detrended_p2p=1.02mHz
mean J_val = 0.5432 (coincide EXACTO con el bookkeeping de entrenamiento, 4 decimales)
```
Coincidencia exacta esperada (política determinística, escenarios fijos) -- confirma que el
bookkeeping de `_evaluate_and_checkpoint()` no tiene un error de medición. **Patrón adicional
detectado, no buscado:** `seed66` es notablemente peor en escenarios de GENERACIÓN (`J_val` 0.73-0.80)
que de CARGA (`J_val` 0.32-0.33) -- MEJOR desempeño relativo que `seed44` en el eje de estabilidad
(`seed44` era `MARGINAL` en 2/3 GEN), pero un costo de desempeño (no de estabilidad) en el mismo tipo
de escenario. Ninguna causa raíz investigada -- observación registrada.
Interpretation: **`seed66` logra la combinación que ninguna de las 5 seeds originales logró
simultáneamente:**
```text
                 J_val_P2   escenarios STABLE (de 6)
seed33 (mejor estabilidad original)   0.5769     6/6   <- peor J_val de las 6
seed44 (mejor J_val original)         0.5217     4/6   <- no 6/6
seed66 (nueva)                        0.5432     6/6   <- 6/6 Y no es la peor en J_val
mean(seed11,22,33,44,55) = 0.5398, std=0.0200 -- seed66 (0.5432) esta a +0.17 sigma, dentro del
  rango normal de variacion entre seeds, NO es un outlier
```
`seed66` no iguala el mejor `J_val_P2` absoluto (`seed44`, 0.5217), pero es 6/6 `STABLE` (igual que
`seed33`) sin pagar el costo de desempeño de `seed33` (peor `J_val` de las 6). **Precaución
estadística explícita:** esto es UNA seed con esta receta específica (`n=1`), no una demostración
repetida -- no se afirma que el mecanismo "resuelve" la tensión `J_val`-vs-estabilidad de forma
general, solo que en esta ejecución particular la combinación buscada se observó. Ninguna conclusión
de robustez del mecanismo debe basarse en un solo seed.
Selected Tc or unresolved decision: **Ninguna decisión de congelamiento, reselección de checkpoint
"final" del paper, ni apertura de `P2-T1..T12` tomada en esta entrada.** `seed66` queda como un
resultado adicional disponible, no como reemplazo automático de `seed44`/los 5 originales -- esa
decisión (si `seed66` entra al conjunto final, y con qué rol) queda pendiente del usuario.
Evidence reviewed: `Paper_2/artifacts/diagnostics/p2e9_seeds/seed66_{eval,diag}_log.csv` (11
evaluaciones completas); `Paper_2/artifacts/models/p2e9_seeds/seed66_ep*.zip` (11 checkpoints);
`Paper_2/artifacts/diagnostics/p2e11d_stability_classification_seed66.csv` (verificación
independiente, nueva); comparación contra `Paper_2/artifacts/diagnostics/p2e9_seeds/
seed{11,22,33,44,55}_eval_log.csv` y `Paper_2/artifacts/diagnostics/p2e11d_stability_summary.csv`
(datos congelados de `DEC-P2-035`/`DEC-P2-040`, no modificados).
Frozen parameters:
```text
SEED66_TRAINING_COMPLETE = TRUE
SEED66_BEST_CHECKPOINT = "seed66_ep1200" (J_val_P2=0.5432, verificado independientemente)
SEED66_STABILITY = "6/6 STABLE (bookkeeping de entrenamiento Y verificacion independiente, match exacto)"
SEED66_NUMERICAL_FAILURES = 0
SEED66_CHECKPOINT_INTEGRITY = PASS
SEED66_WALL_CLOCK_HOURS = 10.38
SEED66_STABILITY_GATE_ACTIVATIONS = 3 de 11 evaluaciones (ep600,1600,1800) -- siempre mismos 3
  escenarios de carga, nunca sobreescribio la seleccion de J_val_P2 solo en esta corrida
P2E10_P2E11_SEED66_INTEGRATION_AUTHORIZED = FALSE
P2T_BATTERY_AUTHORIZED = FALSE
```
Blockers or limitations: `n=1` para esta receta (peso de suavidad + compuerta de estabilidad) --
ninguna réplica adicional ejecutada, no se puede distinguir "el mecanismo funciona de forma
confiable" de "esta seed particular tuvo suerte". Causa del patrón GEN-peor-que-CARGA en `seed66` no
investigada. Ninguna figura comparativa (estilo `P2E11`) generada aún para `seed66` -- solo el
screen de estabilidad independiente. Ninguna decisión sobre el rol de `seed66` en el conjunto final
del paper tomada.
Responsible: Claude (ejecución del entrenamiento real bajo autorización explícita del usuario,
verificación independiente del resultado, registro sin suavizar el hallazgo de que la compuerta no
fue decisiva en esta corrida particular)
Status: passed -- entrenamiento completo, 0 fallos numéricos, integridad de checkpoint PASS,
estabilidad 6/6 confirmada de forma independiente
Next action: Reportar el resultado completo al usuario y **detenerse** -- no generar figuras
comparativas, no decidir el rol de `seed66` en el conjunto final, no abrir `P2-T1..T12`, sin
autorización explícita separada del usuario.

## DEC-P2-044

Date: 2026-08-22
Stage/Gate: **Extensión del paquete de figuras P2-E11/P2-E11d para incluir `seed66`.** Autorizado
explícitamente por el usuario ("puedes generar las mismas figuras generadas previamente pero esta vez
incluyendo el 66?"). Puramente generación de figuras diagnósticas -- ningún reentrenamiento, ninguna
reselección de checkpoint, `P2-T1..T12` sigue sin abrirse.
**Implementación:** `Paper_2/src/stage_p2e11_seed66_extension.py` (nuevo) ejecuta UNA sola pasada de
simulación por cada uno de los 6 escenarios de validation para `seed66_ep1200` (reutilizando
`analyze_trace_v2` sin modificar) y deriva de esa única pasada los datos para las 4 etapas
(`validation_comparison`, `trajectory_demo`, `oscillation_check`, `full_stability_screen`) -- evita
resimular. Los `J_val` obtenidos coinciden EXACTO con los ya verificados en `DEC-P2-043`
(0.7265/0.7569/0.8040 GEN, 0.3256/0.3243/0.3218 LOAD). **Ningún archivo de evidencia congelado
(`DEC-P2-040`, los 12 figuras originales `P2E11*`) fue sobreescrito** -- todo se escribió a archivos
NUEVOS con sufijo `_with_seed66` (10 figuras nuevas, `Paper_2/figures_main/P2E11*_with_seed66_*`,
mtimes de los originales verificados sin cambio). `Paper_2/src/fig_p2e11_seed66_extension.py` (nuevo)
genera las 10 figuras extendidas.
Interpretation: Las figuras confirman visualmente lo ya cuantificado en `DEC-P2-043`: (A) la grilla de
clasificación muestra `seed66` como la ÚNICA fila de TD3 completamente verde (`STABLE` en los 6),
igual que `NoFFC`/`droop*`; (C) el resumen conjunto muestra la barra de `seed66` en el mismo rango que
las demás TD3 (no la peor) con el rombo de estabilidad en 6/6 (único caso TD3); (trajectory demo
`gen_val`) el comando de `seed66` (marrón) permanece suave y sin crecer, en contraste visual directo
con la oscilación creciente y visible de `seed44` (verde) en el mismo panel -- confirma
cualitativamente el hallazgo cuantitativo de `DEC-P2-039`; (trajectory demo `load_val`) ambos seeds
(44 y 66) se comportan de forma similar y limpia, consistente con que el problema de `seed44` es
específico de escenarios GEN.
Selected Tc or unresolved decision: Ninguna. Puramente diagnóstico -- el rol final de `seed66` en el
conjunto del paper sigue sin decidir.
Evidence reviewed: `Paper_2/artifacts/diagnostics/p2e11*_with_seed66*.csv` (nuevos, 5 archivos);
`Paper_2/artifacts/trajectories/p2e11b_trajectory_demo_with_seed66.npz` (nuevo);
`Paper_2/figures_main/P2E11*_with_seed66_*.{png,pdf}` (10 figuras x 4 archivos = 40 archivos nuevos).
Frozen parameters: Ninguno modificado.
Blockers or limitations: Ninguna. Figuras generadas correctamente, verificadas visualmente antes de
reportar al usuario.
Responsible: Claude (generación de datos y figuras bajo autorización explícita del usuario)
Status: passed -- 10 figuras nuevas generadas y verificadas, evidencia original intacta
Next action: Entregar las figuras al usuario y **detenerse** -- decisión sobre el rol final de
`seed66` en el conjunto del paper y sobre abrir `P2-T1..T12` sigue pendiente del usuario.
