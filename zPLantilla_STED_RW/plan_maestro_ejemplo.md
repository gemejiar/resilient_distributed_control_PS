> **Nota de alcance de gates.** Los gates `G0`–`G7` y `LI-1` de este documento son
> internos a `Paper_1` (ver §31, §27). **No citarlos literalmente** (`G0`, `G1`, …)
> dentro de `README.md`, `CLAUDE.md` o `AGENTS.md` de la raíz del repositorio:
> `ops/checks/session_boot.py` extrae el primer token `\bG[0-4]\b` de esos tres
> archivos raíz para determinar el gate STED-RW activo del repositorio completo, y
> una mención de texto libre produce una falsa `DISCREPANCIA` (ya ocurrió una vez
> en esta sesión al redactar `README.md` y tuvo que corregirse).
>
> **Nota de ubicación.** Este archivo vive hoy en la raíz del repositorio. Según
> §27 su ubicación canónica es `Paper_1/plan_maestro_DDPG_FFC_IEEE39_ANDES.md`
> (mismo nombre, sin renombrar a `plan_maestro.md` — ese nombre está reservado
> para el contrato del paper Wide-Area Control en la raíz). La migración queda
> como acción de la etapa **P1-E0** (ver §31), no se ejecuta aquí.

# Plan maestro experimental Lean — DDPG Fast Frequency Control en IEEE-39 / ANDES

**Proyecto:** `Paper_1`  
**Metodología operativa:** STED-RW Lean  
**Entorno:** ANDES — IEEE 39-bus — simulación RMS / positive-sequence  
**Control evaluado:** Fast Frequency Control (FFC) supervisor basado en DDPG  
**Actuadores:** dos BESS/IBR idénticos, controlando exclusivamente potencia activa  
**Baselines:** No FFC y droop FFC bien sintonizado  
**Estado:** `PLAN_FROZEN` — ronda 3 de correcciones aplicada tras segunda revisión externa: H2/H3 realineados con sus hipótesis, gap de instrumentación de placement corregido, código de inercia desincronizado corregido, escenario de Figura 1 congelado y sección de limitaciones redactada (§32-bis, ver §0.7). 0 de 14 puntos de claridad abiertos; próxima acción autorizada: P1-E0 (§31, §37)  
**Objetivo operativo:** producir únicamente la evidencia mínima indispensable para aceptar o rechazar H1–H3.

---

## 0. Estado de clarificación metodológica

```text
ESTADO DEL PLAN: PLAN_FROZEN
RONDA DE INDAGACIÓN: 3 (correcciones tras segunda revisión externa, ver §0.7)
PUNTOS DE CLARIDAD ABIERTOS: 0 de 14
NEXT AUTHORIZED ACTION: P1-E0 (--stage inspect, §37) — el congelamiento metodológico no implica que
  las acciones de ejecución (mover el documento, correr el pipeline) ya se hayan realizado; §31 sigue
  fijando el orden obligatorio de etapas.
```

Auditoría realizada contra el `PROTOCOLO OBLIGATORIO DE INDAGACIÓN ANTES DE CERRAR EL PLAN` de
`prompt_maestro_STED_RW.md` v1.1 (estados permitidos: `resuelto`, `supuesto_aceptado`, `abierto`,
`no_aplica` — línea 158 y siguientes de ese archivo; el estado `pendiente_redacción` usado en la
ronda 2 de este documento no es uno de ellos y se corrige en esta ronda). La regla general: mientras
esta sección declare puntos `abierto`, el plan no puede describirse como congelado. Con 0/14 puntos
abiertos (checklist de §0.1), esa condición ya se cumple y el plan pasa a `PLAN_FROZEN`. Lo que sigue
pendiente no es el diseño metodológico sino la ejecución: no se autoriza escribir código de
experimentación más allá de la inspección de solo lectura de la etapa P1-E0 hasta que esa etapa se
ejecute y reporte sin blockers.

### 0.1 Checklist de claridad

| # | Aspecto | Estado | Dónde se resuelve o qué falta |
|---|---|---|---|
| 1 | Sistema u objeto de estudio | `resuelto` | §5.2/§5.3. Decisión del usuario (opción B de P-1.1): escalar inercia solo en las 9 máquinas del área (buses 30–38); `GENROU_10`/bus 39 (slack) queda excluido. Ver también el techo cuantificado del 33.9% y la escalera corregida \(k\in\{0.50,0.30\}\) en §5.3 |
| 2 | Objetivo o hipótesis verificable | `resuelto` | §2 (H1–H3) y §22–§24 (gates con condición de falsación explícita) |
| 3 | Líneas base y setup de comparación | `resuelto` | §13/§13.1. Decisión del usuario (opción C de P-1.3): observación de DDPG restringida a los dos buses de conexión BESS (6 señales), simétrica con lo que el droop mide localmente; ver §13.1 para la arquitectura (observación local, reward/métricas system-wide como señal privilegiada de entrenamiento — no es CTDE en sentido MARL, ver corrección de terminología en §13.1) |
| 4 | Datos, evidencia o capa de medición | `resuelto` | §21 (P-1.5, resuelto): reward, métricas y gates usan `BusFreq`/`BusROCOF` en los 10 buses de generación (30–39), misma cadena de filtro `(Tf,Tw,Tr)` que la observación de §13. Requiere añadir `BusROCOF` en esos 10 buses (no viene en el caso stock, ver §0.2) |
| 5 | Núcleo del método | `resuelto` | §15 (reward única), §18 (hiperparámetros), §19 (3 seeds), §20 (presupuesto y early stopping); complementado por S-05 y S-06 |
| 6 | Plataforma de implementación | `supuesto_aceptado` | ANDES 2.0.0 y `gymnasium` verificados; falta `stable-baselines3` y `torch`. Ver S-11 |
| 7 | Adquisición y preprocesamiento | `supuesto_aceptado` | §13 (normalización) y §14 (paso de integración, filtro RoCoF); coherencia observación-métrica fijada en S-06 |
| 8 | Ejecución, actuación o camino de decisión | `resuelto` | §6, §14 y STOP-B; el caso ofrece `ESD1`, `PVD1` y la cadena `REGCA1`/`REECA1`/`REPCA1` como actuadores candidatos |
| 9 | Escenarios de prueba y casos de evaluación | `resuelto` | Regla de re-despacho: §9 (P-1.2). Horizonte: §14 (P-1.6, resuelto) — 6 s inicial, extensión única y condicional a 10 s si LI-1 detecta nadir truncado |
| 10 | Métricas y criterios de aceptación | `resuelto` | §22 (P-1.4, resuelto): margen mínimo relativo de 1% simultáneo en desviación de nadir y en RoCoF, con droop como denominador. §21 (P-1.5, resuelto): conjunto de señales fijado a `BusFreq`/`BusROCOF` en buses 30–39 |
| 11 | Parámetros de reproducibilidad | `resuelto` | §27 corregido para usar el árbol real de `Paper_1`; §20.0 (nuevo) fija el gate de factibilidad computacional que resuelve S-13. Pendiente fuera de alcance de esta ronda: restauración de `plan_maestro.md` de la raíz (ver P-1.7, deferida por decisión explícita del usuario) |
| 12 | Limitaciones y amenazas a la validez | `resuelto` | §32-bis (nueva sección, redactada en esta ronda): limitaciones y amenazas a la validez explícitas, consistentes con §3/§5.2/§12.2/§33 |
| 13 | Alcance de la generalización permitida | `resuelto` | §33 (claims permitidos por hipótesis y lista de prohibidos) |
| 14 | Criterio de cierre del producto | `supuesto_aceptado` | §35 define el cierre de la campaña experimental, no el del producto editorial. Ver S-14 |

### 0.2 Hechos verificados por inspección de solo lectura

Verificados sobre `Paper_1/cases/ieee39/base/ieee39_full.xlsx` con ANDES 2.0.0 (`venv/`), sin modificar el caso:

| Hecho | Valor | Consecuencia para el plan |
|---|---|---|
| Versión y caso | ANDES 2.0.0, `ieee39_full.xlsx`, 39 buses, 46 líneas, 19 cargas `PQ` | Confirma §5.1; el caso base ya está congelado en `cases/ieee39/base/` |
| Máquinas | 10 `GENROU` en buses 30–39, con `TGOV1N`, `IEEEX1` e `IEEEST` | Hay governor y PSS activos: el nadir depende de la respuesta primaria, no solo de la inercia |
| Inercia | \(H=\) 43.7, 25.3, 30.2, 33.6, 28.1, 37.8, 27.1, 23.6, 58.1 y **599.5** | La última máquina (bus 39) aporta ~66% de la inercia total del caso |
| Slack | Bus 39, es decir la misma máquina equivalente de \(H=599.5\) | El equivalente externo es simultáneamente slack y reserva de inercia dominante |
| Medición de frecuencia | `BusFreq` instanciado solo en los buses 30–39 | El screening de §7.2 sobre "todos los buses" exige añadir dispositivos de medición a la variante |
| Evento preexistente | `Toggle` que desconecta `GENROU_1` en \(t=12\,s\) | Queda fuera de la ventana de 6 s; debe desactivarse igualmente en la variante para evitar acoplamiento si el horizonte cambia |
| Control secundario | Un `ACEc` en el bus 1 con sesgo \(-1.0\), 2 áreas | Existe AGC en el caso: se mantiene idéntico en las tres estrategias y se declara (S-09) |
| Carga total | 5856.4 MW nominales | El escalón de §12.2 equivale a \(\Delta P_L\approx 292.8\) MW |
| Actuadores disponibles | `ESD1`, `PVD1`, `REGCA1`, `REECA1`, `REPCA1`, familia `WT*` | P1-E0 puede resolver §6.1 sin implementar un modelo propio; STOP-B sigue vigente |

### 0.3 Supuestos adoptados por defecto

Cada supuesto se adopta porque el plan no lo fija y su ausencia impide ejecutar. Todos son reversibles antes del gate en que se usan.

| ID | Supuesto | Base | Riesgo | Gate que lo consume |
|---|---|---|---|---|
| S-01 | Umbral del criterio 4 del gate LI-1: la contingencia de diseño sin FFC debe producir \(|\Delta f_{nadir}|\ge 0.5\,Hz\) y \(|RoCoF|\ge 0.5\,Hz/s\); si no se alcanza con \(k=0.50\), se pasa a \(k=0.30\) y se congela (escalera corregida en §5.3 tras resolver P-1.1: la original \(\{0.70,0.50\}\) sobre 9/10 máquinas rendía solo −10.2%/−17.0%, con techo del 33.9%) | §5.3 exige "perturbación suficientemente relevante" sin número; sin umbral la elección entre pasos de la escalera sería post hoc | medio | P1-E1 |
| S-02 | \(E_{max}=2P_{max,BESS}(t_f-t_d)\) en el objetivo de tuning \(J_{val}\) | §17.1 usa \(E_{max}\) sin definirlo; es el throughput máximo físicamente alcanzable | bajo | P1-E4 |
| S-03 | La política fija del Paso B de placement es un droop provisional con \(K_d=K_0=P_{max,BESS}/0.5\,Hz\), idéntico en los seis pares | §7.2 permite "pulso o droop provisional" sin elegir | bajo | P1-E2 |
| S-04 | Buses admisibles para BESS: buses 1–29 (carga o transferencia); se excluyen los buses de generación 30–39 y el slack | §7.2 dice "técnicamente admisibles" sin definirlo; los buses 30–39 son terminales de máquina | medio | P1-E2 |
| S-05 | El lazo de control corre desde \(t=0\) con retención de orden cero de 100 ms; en validation y test la política se evalúa determinista, sin ruido OU | §14 no fija el instante de activación ni el modo de evaluación | bajo | P1-E5, P1-E6 |
| S-06 | El RoCoF observado por el agente (§13, BESS POI) y el usado en reward/métricas system-wide (§15/§21, buses 30–39) comparten la misma cascada de filtro `BusROCOF` (`Tf=0.02, Tw=0.02, Tr=0.05`, ver §14 — no un promedio móvil separado de 60 ms, eliminado en la corrección de §14), muestreada en el instante de control | §14 fija un único filtro para toda señal de frecuencia/RoCoF del pipeline; usar cascadas distintas rompería la coherencia observación-métrica | medio | P1-E5, P1-E6 |
| S-07 | Distancia eléctrica: suma de \(|X|\) serie a lo largo del camino de menor reactancia; el mismo criterio y la misma mediana se aplican a \(G_B\) (§8.2) y a \(L_B\) (§12.2) | Ninguna de las dos secciones define la métrica de distancia | bajo | P1-E3 |
| S-08 | Sin ruido de medición ni retardos de comunicación en ninguna de las tres estrategias | Coherente con §3 (excluye retardos); entra como limitación explícita | medio | P1-E4–P1-E6 |
| S-09 | El `ACEc` del caso base se mantiene habilitado e idéntico en las tres estrategias; el `Toggle` de \(t=12\,s\) se desactiva en la variante low-inertia | Preserva el caso stock y mantiene la comparación pareada | bajo | P1-E1 |
| S-10 | La variante low-inertia añade dispositivos `BusROCOF` en los buses 1–29 (S-04, candidatos BESS admisibles) de forma incondicional, para el screening de placement de §7.2 Paso A — independiente de cómo se resolvió P-1.5 (que fija las señales de reward/métricas en los buses 30–39, no las de placement); son dispositivos de medición, no cambian la dinámica | Necesario para calcular \(S_b\) en §7.2 sobre todos los buses admisibles, antes de que existan "los cuatro candidatos" que P1-E2 presupone | bajo | P1-E1 |
| S-11 | Se instalan `stable-baselines3` y `torch` (rueda CPU) en el `venv/` compartido y se re-congela `requirements-lock.txt` | §18 exige SB3; hoy el entorno solo tiene `andes[rl]` y `gymnasium`. Alternativa (venv propio) contradice DEC-020 | bajo | P1-E5 |
| S-12 | Todas las cifras finales se reportan con la mediana de las tres seeds; las seeds individuales solo aparecen en la figura agregada | §22 usa la mediana para el gate; §26 pide mostrar las tres seeds | bajo | P1-E7 |
| S-13 | El benchmark de cómputo de §20.0 (etapa P1-E4.5) mide el tiempo de pared de una TDS de 6 s y de un episodio completo de entrenamiento antes de comprometerse a los 3×8000 episodios; si el presupuesto proyectado se excede, se reduce el máximo de episodios conservando el early stopping y se registra la reducción | §20 fija episodios pero el plan no acota horas de cómputo | medio | P1-E4.5 |
| S-14 | Producto final: manuscrito de journal en inglés generado desde `ffc_results.csv` y el único artefacto temporal `fig1_case.npz` (§26/§27); el venue se decide tras conocer el signo del resultado; el cierre editorial es el checklist de §35 con H1–H3 resueltas explícitamente | §35 cierra la campaña experimental, no el producto | medio | P1-E7 |

### 0.4 Preguntas abiertas de esta ronda

```markdown
P-1.1 [1 Sistema] `RESUELTO` — decisión explícita del usuario: opción (B), escalar
      solo las 9 máquinas del área de New England (`GENROU_1`…`GENROU_9`, buses
      30–38); `GENROU_10`/bus 39 (slack, H=599.5 s) queda excluido y conserva su
      inercia original. Implementado en §5.2.
- Consecuencia cuantificada y ya incorporada en §5.3: con el equivalente excluido,
  la reducción de \(H_{total}\) del sistema está acotada a un máximo de 33.9%
  (techo dado por \(H_{10}=599.5\,\text{s}\) de los 906.92 s totales), y la
  escalera original \(\{0.70,0.50\}\) sobre esas 9 máquinas solo producía entre
  −10.2% y −17.0% — insuficiente. Se corrigió la escalera a \(k\in\{0.50,0.30\}\)
  y se añadió una vía de escalamiento explícita al usuario en STOP-A si \(k=0.30\)
  tampoco basta.
- No se adoptó la opción (C) (factor propio para el equivalente): fuera de
  alcance salvo que STOP-A la active explícitamente tras agotar \(k=0.30\).

P-1.2 [9 Escenarios] `RESUELTO` — decisión explícita del usuario: opción (A),
      escalar la potencia activa de todos los generadores no-slack por \(\lambda_L\),
      dejando al slack solo el residuo de pérdidas. Implementado en §9
      ("Redespacho de generación"), con verificación de que el slack permanece
      dentro de \([0,11]\,pu\) en \(\lambda_L=1.10\). Registrar \(\lambda_L\) y el
      despacho resultante en `ffc_results.csv` sigue vigente.

P-1.3 [3 Líneas base] `RESUELTO` — decisión explícita del usuario: opción (C),
      restringir la observación de DDPG a los dos buses de conexión BESS
      (Δf, RoCoF, potencia propia — 6 señales, ver §13), simétrica con lo que el
      droop mide localmente. H1 se enuncia como "supervisor centralizado
      aprendido, con observación local, frente a droop local convencional" — sin
      asimetría de información que objetar.
- Nota sobre la advertencia original ("se aparta de Stanojev y previsiblemente
  degrada al agente"): es una predicción no verificada, no un hecho establecido.
  El diseño resultante es un DDPG centralizado con observación local en los POI
  y señal privilegiada solo en entrenamiento (ver §13.1 — no es CTDE en sentido
  MARL, pero comparte el principio de usar información privilegiada solo para
  calibración/entrenamiento), no una limitación del agente. Si el entrenamiento
  (P1-E5) muestra evidencia real de degradación por falta de información, se
  documenta como limitación empírica en su momento — no se asume a priori.
- La opción (B) (tercer baseline droop-COI) no se adoptó: el usuario prefirió
  la solución más económica y metodológicamente más limpia.

P-1.4 [10 Métricas] `RESUELTO` — opción (A), margen relativo mínimo de 1% simultáneo en ambas
      métricas, con el baseline droop como denominador (no el valor absoluto de la métrica). Un
      escenario cuenta como "win" solo si:

\[
I_f=\frac{|\Delta f_{nadir}^{droop}|-|\Delta f_{nadir}^{DDPG}|}{|\Delta f_{nadir}^{droop}|}\ge0.01
\quad\text{y}\quad
I_r=\frac{RoCoF_{max}^{droop}-RoCoF_{max}^{DDPG}}{RoCoF_{max}^{droop}}\ge0.01
\]

      Implementado en §22 como el criterio de "win" para P1-H1/P1-H3. El 1% se describe como un
      **umbral mínimo de efecto pre-registrado para este benchmark**, no como un requisito físico o
      regulatorio.
- Por qué era necesario: §22 usaba desigualdades estrictas; una diferencia de 1 mHz o 1e-3 Hz/s,
  dentro del ruido de integración, contaba como victoria y decidía la aceptación de H1.
- No se adoptó (B) (margen absoluto): se prefirió un margen relativo, comparable entre escenarios de
  severidad distinta.

P-1.5 [4 y 10 Señales] `RESUELTO` — opción (A'), una variante afinada de la opción (A) original:
      f_nadir y RoCoF_max (reward §15, métricas §21, gates §22–§24) se calculan sobre `BusFreq`/
      `BusROCOF` en los **10 buses de generación (30–39)**, no sobre `GENROU.omega` directamente y
      no sobre los 29 buses de carga. Esto da la misma cadena de medición (`Lag(Tf)` → `Washout(Tw)`
      → `Washout(Tr)`, con `Tf=0.02, Tw=0.02, Tr=0.05`, ver §14) para la observación de DDPG (§13,
      local a los dos POI de BESS) y para las señales privilegiadas de reward/métricas — evita
      mezclar un estado interno sin filtrar (`omega`) con una señal filtrada en otras partes del
      pipeline. Requiere añadir `BusROCOF` en los 10 buses generadores (el caso stock solo trae
      `BusFreq` ahí, ver §0.2); no se tocan los 29 buses de carga.
- Por qué era necesario: §21 escribía "min sobre i,t" sin fijar el conjunto i; los buses de carga NO
  se usan para el gate (quedan reservados al screening de placement de §7.2).
- No se adoptó (B) (todas las frecuencias de bus, 39): exigía revisar los umbrales de 0.5 Hz/1 Hz/s
  y no aporta valor adicional frente a los 10 buses generadores para este diseño Lean.

P-1.6 [9 y 14 Horizonte] `RESUELTO` — opción (A): mantener \(t_f=6\,s\) inicialmente. Durante el
      Gate LI-1 (§5.3), medir \(t_{nadir}^{NoFFC}\) en la corrida de verificación del criterio 4. Si
      \(t_{nadir}>t_f-0.5\,s\), o la frecuencia todavía está decreciendo en \(t_f\), extender **una
      única vez** a \(t_f=10\,s\) y congelar:

```text
EPISODE_HORIZON_FROZEN = TRUE
```

      Añadido como criterio 5 del Gate LI-1 (§5.3). Si se activa la extensión a 10 s, se propaga a
      §18.1 (conteo de transiciones, ver nota de coherencia corregida) y a S-13 (presupuesto de
      cómputo, §20.0) antes de comprometerse a los 24 000 episodios.
- Por qué era necesario: con TGOV1N activo y H reducido, el nadir de un IEEE-39 puede aparecer entre
  4 y 8 s; si cae fuera de la ventana, f_nadir mide el extremo de la ventana, no el nadir real.
- No se adoptó (C) (10 s desde el inicio): coste innecesario si 6 s bastan; (B) (6 s incondicional):
  riesgo de métrica truncada sin verificación.

P-1.7 [11 Artefactos y gobernanza] `PARCIALMENTE RESUELTO`. La parte del árbol
      de archivos está resuelta: §27 fue corregido para usar el árbol real ya
      registrado (`src/`, `experiments/`, `artifacts/`, `paper/`,
      `cases/ieee39/{base,variants}/`), con el mapeo completo
      `run_ffc_study.py -> Paper_1/src/`, `ffc_results.csv ->
      Paper_1/artifacts/metrics/`, `ddpg_seed*.zip -> Paper_1/artifacts/models/`,
      caso low-inertia -> `Paper_1/cases/ieee39/variants/`. El nombre de este
      documento tras moverse a `Paper_1/` es
      `plan_maestro_DDPG_FFC_IEEE39_ANDES.md`, no `plan_maestro.md` (ver nota de
      ubicación al inicio del documento y §34).
- **Sigue abierta, explícitamente fuera de alcance de esta corrección:** la
  restauración de `plan_maestro.md` de la raíz (contrato del paper Wide-Area
  Control). El usuario indicó que el enfoque de esta sesión es este documento
  (`plan_maestro_DDPG_FFC_IEEE39_ANDES.md`), no la raíz del repositorio — la
  decisión sobre esa restauración se toma por separado.
```

### 0.5 Puntos diferidos a la ronda 2

1. Redacción de la sección de limitaciones y amenazas a la validez (punto 12), que ahora depende solo de P-1.5 y P-1.6 (P-1.1 y P-1.3 ya resueltos arriba).
2. `RESUELTO` — Gobernanza STED de `Paper_1`: decisión explícita del usuario,
   **árbol propio en `Paper_1/ops/sted/`** (`traceability_matrix.csv`,
   `test_plan.md`, `decision_log.md`), registrado como enmienda a DEC-020 vía
   una nueva entrada **DEC-021** en `ops/sted/decision_log.md` de la raíz. Esto
   confirma §34 tal como está escrito; no hace falta revisar DEC-020 en sí, solo
   añadir DEC-021 documentando la enmienda cuando se ejecute P1-E0.
3. Confirmación o sustitución de S-14 (producto editorial y venue) una vez conocido el signo del resultado.

### 0.6 Correcciones aplicadas en esta ronda (revisión externa)

Ronda 2 incorpora una revisión metodológica externa del plan congelado hasta P-1.3. Se aplicaron las
siguientes correcciones, todas dentro del alcance de este documento (no afectan `plan_maestro.md` de
la raíz):

| # | Sección afectada | Corrección | Motivo |
|---|---|---|---|
| C1 | §13.1 | Renombrada de "CTDE" a terminología correcta (no hay ejecución decentralizada: un único actor centralizado produce ambas acciones a partir de observaciones de ambos POI) | "CTDE" es un término de MARL que no aplica aquí; mal etiquetarlo induce a un lector experto a esperar una arquitectura que el diseño no tiene |
| C2 | §10 | Eliminado el mecanismo `set_pref`/`disturbance_fn` duplicado y contradictorio con el `Alter` sobre `paux0` ya verificado empíricamente; queda un único mecanismo (`Alter`) | El documento describía dos mecanismos incompatibles para la misma perturbación; solo uno estaba verificado con evidencia empírica de reinicio correcto entre episodios |
| C3 | §12.2, §31 (P1-E1) | El cambio `constZ`→`constP` del modelo `PQ` se aplica una sola vez, en la construcción del caso experimental (P1-E1), idéntico en training/validation/test — no solo en T5–T8 | Aplicarlo solo en el test de tipo de perturbación confunde "tipo de perturbación no visto" con "dinámica de carga distinta"; T5–T8 dejarían de aislar una sola variable |
| C4 | §5.2/§5.3 | Verificado computacionalmente (ANDES 2.0.0, esta sesión) que las cifras de inercia (\(H_{10}=599.5\,s\), \(\sum H=906.92\,s\)) ya usan `GENROU.M.v` en base de sistema (100 MVA), no `M.vin` en base de máquina; se añade el Test T17 para proteger esta invariante | Sumar \(H_i\) en bases de máquina distintas sería físicamente inválido; se confirmó que el plan ya usaba la conversión correcta, pero la afirmación no estaba protegida por un test |
| C5 | §12.1 | T3/T4 corregidos de \(\{0.80P_{G_A},-10\%\}\)/\(\{0.80P_{G_B},+10\%\}\) a \(\{0.60P_{G_A},-10\%\}\)/\(\{0.60P_{G_B},+10\%\}\), formando pares verdaderamente aislados con T1/T2 (T1↔T3, T2↔T4 cambian solo el operating point) | Con \(\rho=0.80\) en T3/T4 y \(\rho=0.60\) en T1/T2, la comparación cambiaba simultáneamente magnitud de perturbación y operating point; H3 no podía atribuir la degradación a uno u otro factor |

Correcciones adicionales (no críticas, aplicadas por consistencia):

- §18.1: `learning_starts` corregido de 2560 a 600 (10 episodios × 60 pasos/episodio a `dt=0.1s`,
  `t_f=6s`, no 256 pasos — 256 es `batch_size`); conteo total de transiciones corregido de 400 000 a
  480 000 por seed (condicional a 800 000 si P-1.6 extiende a \(t_f=10\,s\)); se elimina la
  afirmación categórica de que el buffer nunca rota.
- §21.2: la degradación relativa \(D_m\) para el nadir se redefine sobre \(\Delta f_{nadir}\)
  (desviación respecto a \(f_0\)) en vez de \(f_{nadir}\) absoluto — un cociente relativo sobre un
  valor absoluto cercano a 60 Hz diluye numéricamente cualquier diferencia real.
- §17.1/§20: droop y DDPG comparten explícitamente el mismo objetivo \(J_{val}\) para la selección
  final (ganancia \(K_d\) y checkpoint por seed), no solo droop.
- §14/§17: se fija explícitamente que el comando de droop pasa por el mismo ZOH de 100 ms hacia
  `Pext0` que el de DDPG (misma interfaz temporal para ambos controladores).
- §26/§27: se autoriza un artefacto temporal adicional, `Paper_1/artifacts/trajectories/
  fig1_case.npz`, como única excepción acotada a "un CSV consolidado" — necesario porque
  `ffc_results.csv` solo contiene métricas escalares y no puede reconstruir las trayectorias
  \(f(t)\), \(RoCoF(t)\), \(P_{BESS}(t)\) de la Figura 1.
- §26: la "seed representativa" de la Figura 1 se congela antes de abrir T1–T8 (mediana de
  \(J_{val}\) entre las 3 seeds), no se elige después de ver el resultado.
- §6.4: se añaden condiciones iniciales explícitas del BESS (\(P_0=Q_0=0\), \(SOC_0=0.5\)).
- §30: se añaden T17 (consistencia de base de la inercia), T18 (mecanismo único de pérdida de
  generación) y T19 (modelo de carga idéntico en train/validation/test).
- §0.3 (S-02…S-14) y líneas sueltas (§0, §6.4): las referencias a `G0`–`G7` se corrigen a
  `P1-E0`–`P1-E7` (§31 ya había renombrado las etapas precisamente para evitar colisión con los
  gates `G0`–`G4` de la raíz, pero la tabla de supuestos no se había actualizado — la inconsistencia
  es del mismo tipo que el documento advierte evitar en su nota de alcance inicial).

No se aplicó el cambio de nombre sugerido de "pérdida de generación" a un término más largo
("reducción de referencia de gobernador") en todo el documento: el plan ya incluye, junto al
mecanismo de §10, la advertencia explícita de que el recorte actúa sobre la referencia del gobernador
y no sobre \(P_e\) medida — se considera suficiente disclosure sin renombrar decenas de referencias.

### 0.7 Correcciones aplicadas en la ronda 3 (segunda revisión externa)

Una segunda revisión externa auditó el resultado de la ronda 2 y encontró seis inconsistencias
adicionales, dos de ellas introducidas por la propia corrección de P-1.5 en la ronda 2. Todas se
corrigen en esta ronda; el plan pasa a `PLAN_FROZEN` (§0).

| # | Sección afectada | Corrección | Motivo |
|---|---|---|---|
| D1 | §2 (H2), §23 | H2 y su gate se reformulan como dominancia tipo Pareto: DDPG apoya H2 en un escenario si no es peor en nadir/RoCoF **y** usa igual o menor energía/potencia — no "seguridad comparable" bajo un filtro de umbral absoluto compartido | Dos controladores dentro del mismo umbral absoluto (p. ej. droop en 0.49 Hz, DDPG en 0.25 Hz) no tienen seguridad comparable; una ventaja de energía en ese caso mezcla "más eficiente a igual seguridad" con "opera en otro punto de la curva esfuerzo-seguridad" |
| D2 | §24 (P1-H3) | El gate se reformula para medir **degradación relativa** (\(D_{\Delta f}\), \(D_{RoCoF}\) de §21.2) entre pares aislados (T1↔T3, T2↔T4, T5↔T7, T6↔T8), no victorias absolutas de DDPG sobre droop en T3/T4/T7/T8 | H3 (§2) afirma "la degradación de DDPG no es mayor que la de droop" — una comparación de degradación entre controladores, no una comparación de desempeño absoluto; el gate anterior probaba una afirmación distinta (más cercana a una extensión de H1 a escenarios OOD) |
| D3 | §31 (P1-E1, P1-E2), §0.3 (S-10) | Corregida la conflación, introducida en la ronda 2, entre los buses de reward/métricas (30–39, P-1.5) y los buses de screening de placement (1–29, S-04, §7.2 Paso A); se añade a P1-E2 el paso explícito que ejecuta el Paso A y produce "los cuatro candidatos" que el resto de la etapa presuponía sin haberlos calculado | La corrección de P-1.5 en la ronda 2 solo mencionó `BusROCOF` en 30–39; el screening de placement (§7.2, sin cambios desde la v1) necesita `BusROCOF` en 1–29, un conjunto de buses distinto y con un propósito distinto |
| D4 | §5.2 | Eliminado \(k=0.70\) del bloque ejecutable (fórmula y código Python); `k` pasa a ser un parámetro que toma el primer valor de la escalera ya congelada en §5.3 (\(k=0.50\), con \(k=0.30\) como reintento) | §5.3 había corregido la escalera de \(\{0.70,0.50\}\) a \(\{0.50,0.30\}\) en la ronda 1, pero el bloque de código ejecutable de §5.2 nunca se actualizó — Codex habría ejecutado literalmente \(k=0.70\), un valor ya descartado por insuficiente |
| D5 | §26, §31 (P1-E5) | Se congela también el escenario de la Figura 1 (`FIG1_SCENARIO = T1`), no solo la seed representativa | La seed ya se congelaba antes de test, pero el escenario seguía sin definirse; elegirlo después de ver T1–T8 sería cherry-picking gráfico aunque el análisis cuantitativo (Fig. 2, Tabla 1) sea correcto |
| D6 | §0 | El estado `pendiente_redacción` (ronda 2) no es uno de los cuatro estados permitidos por `prompt_maestro_STED_RW.md` (`resuelto`, `supuesto_aceptado`, `abierto`, `no_aplica`, verificado en esta ronda); se redacta §32-bis (limitaciones) y el punto 12 pasa a `resuelto`, sin bloquear el paso a `PLAN_FROZEN` por una acción de ejecución (mover el archivo, P1-E0) que no es una ambigüedad metodológica | `PLAN_FROZEN` certifica cierre del diseño, no que las operaciones de filesystem ya ocurrieron |

Correcciones menores adicionales:

- §13: la frase "DDPG observa exclusivamente lo mismo... igual que el droop" sobre-afirmaba una
  simetría que el propio §13.1 corrige (DDPG dispone de RoCoF y potencia propia en ambos POI; droop
  solo de su frecuencia local). Se reformula como igualdad de **ubicaciones de medición**, no de
  contenido de señal.
- §33/§34.1: el texto de claim para H2 y la fila `CLM-H2` se actualizan de "comparable
  frequency-security conditions" a "at least as good as droop", consistente con D1.
- §0.3 (S-14): corregido "generado íntegramente desde `ffc_results.csv`" para incluir el artefacto
  `fig1_case.npz` (ya autorizado en la ronda 2, §26/§27), que la ronda 2 dejó sin propagar a S-14.

---

## 1. Objetivo del proyecto

Implementar y evaluar una estrategia de **Fast Frequency Control (FFC) supervisora basada en DDPG**, conceptualmente basada en Stanojev et al., sobre el caso dinámico IEEE-39 de ANDES, utilizando dos BESS/IBR idénticos como actuadores rápidos de potencia activa.

La experimentación debe ser la **mínima indispensable** para responder la siguiente pregunta científica:

> ¿Puede un controlador DDPG centralizado explotar mejor dos BESS/IBR que un FFC droop convencional en un IEEE-39 de baja inercia, mejorando simultáneamente el nadir y el RoCoF, sin requerir mayor esfuerzo energético/potencia y manteniendo desempeño frente a operating points no vistos?

**Restatement operativo (revisión externa, para falsabilidad):**

> Can a centrally executed DDPG-based FFC policy achieve better transient
> frequency-security performance than tuned local droop, using the same two
> BESS actuators and measurements restricted to their points of connection?

H2 y H3 evalúan, sobre esa misma comparación, eficiencia energética y
robustez frente a operating points no vistos, respectivamente.

No implementar experimentos cuya respuesta no contribuya directamente a esta pregunta.

---

## 2. Decisión científica central

### Este proyecto debe formularse como

> Una evaluación controlada de DDPG como capa supervisora de Fast Frequency Control para dos BESS/IBR en una red IEEE-39 RMS de baja inercia, comparada bajo idénticos recursos y contingencias contra ausencia de FFC y un FFC droop bien sintonizado.

### Este proyecto no debe formularse como

> Una demostración de superioridad universal de reinforcement learning, una nueva teoría de estabilidad, un algoritmo safe-RL, un estudio EMT, un problema de dimensionamiento óptimo de BESS o una comparación exhaustiva de algoritmos RL.

### Hipótesis principal H1

> Bajo las contingencias no vistas evaluadas, DDPG reduce simultáneamente la máxima desviación de frecuencia y el máximo RoCoF respecto al droop convencional en la mayoría de los escenarios.

### Hipótesis secundaria H2

> Cuando DDPG alcanza un nivel de seguridad de frecuencia (nadir y RoCoF) igual o mejor que el de
> droop, requiere igual o menor energía intercambiada y/o potencia pico de los BESS.

**Corrección (revisión externa, ronda 3):** reformulada como una relación de dominancia tipo Pareto
(no peor seguridad, menor o igual esfuerzo) en vez de "niveles comparables de seguridad" — dos
controladores pueden estar ambos dentro de un mismo umbral absoluto sin ser igualmente seguros (ver
§23 para el detalle y el motivo del cambio).

### Hipótesis secundaria H3

> La degradación del desempeño de DDPG ante operating points fuera del intervalo de entrenamiento no es mayor que la observada con droop.

---

## 3. Alcance congelado

### Incluye

- ANDES.
- Caso IEEE-39 dinámico estándar disponible en ANDES.
- Simulación RMS / positive-sequence.
- Red modificada únicamente cuando sea indispensable.
- Red de baja inercia obtenida modificando parámetros de inercia de generadores síncronos.
- Dos BESS/IBR idénticos.
- Control exclusivamente de potencia activa:

\[
a_k=
\begin{bmatrix}
\Delta P^{\star}_{BESS1}\\
\Delta P^{\star}_{BESS2}
\end{bmatrix}
\]

- DDPG centralizado.
- Tres seeds independientes de entrenamiento.
- Training exclusivamente mediante pérdidas de generación.
- Generalización evaluada mediante:
  - generadores no vistos;
  - escalones positivos de carga no usados en entrenamiento;
  - operating points de \(-10\%\) y \(+10\%\) no usados en entrenamiento.
- Tres estrategias:
  - No FFC;
  - Droop FFC;
  - DDPG FFC.

### Excluye

- MPC.
- TD3.
- SAC.
- PPO.
- MARL.
- Physics-informed RL.
- Safe RL.
- Lyapunov RL.
- Fallas trifásicas.
- Pérdida de líneas.
- Contingencias de tensión.
- Control de potencia reactiva.
- SoC detallado/electroquímica.
- Optimización económica.
- Retardos de comunicaciones.
- Cyberattacks.
- EMT.
- HIL/PHIL.
- Estudios N-1 exhaustivos.

Ninguno debe añadirse aunque resulte sencillo de implementar, salvo autorización expresa posterior.

---

## 4. Fuente metodológica

La arquitectura debe seguir el concepto de Stanojev et al.:

\[
[f_i,\dot f_i]
\rightarrow
\boxed{\text{DDPG}}
\rightarrow
\Delta P^\star_{IBR}
\]

La política debe ser una **capa supervisora**. No debe reemplazar los modelos dinámicos existentes del BESS/IBR.

El controlador local del recurso permanece intacto:

\[
\text{DDPG}
\rightarrow
P^\star
\rightarrow
\text{actuador BESS/IBR}
\rightarrow
\text{red}
\]

El principio a reproducir es:

- observaciones basadas en frecuencia y RoCoF;
- acciones continuas;
- modificación directa del setpoint de potencia activa;
- baja carga computacional online;
- entrenamiento offline;
- controlador centralizado.

---

## 5. Caso IEEE-39 base y modificación low-inertia

### 5.1 Regla de preservación

No modificar el caso stock de ANDES.

Crear solo una copia si es necesario:

```text
Paper_1/cases/ieee39_low_inertia.xlsx
```

Toda modificación debe poder reconstruirse desde el script principal.

### 5.2 Primera modificación

Preservar:

- topología;
- líneas;
- transformadores;
- cargas nominales;
- excitadores;
- governors;
- despacho nominal;
- parámetros eléctricos.

**Parámetro verificado (ANDES 2.0.0, `andes/models/synchronous/genbase.py`):** el
caso `ieee39_full.xlsx` usa exclusivamente el modelo **GENROU** (no GENCLS). El
parámetro de inercia se llama **`M`**, no `H`; `M = 2H` ("machine start-up
time"). `M` tiene `power=True`, por lo que ANDES lo convierte de base de
máquina (`Sn`) a base de sistema (100 MVA) al hacer `setup()`:
`ss.GENROU.M.v` ya está en base de sistema; `ss.GENROU.M.vin` conserva el
valor crudo del `.xlsx` en base de máquina.

**Hallazgo que restringe qué máquinas escalar:** el generador `GENROU_10`
(bus 39) es simultáneamente el **Slack** del caso y el equivalente reducido de
la interconexión externa (Nueva York). Su inercia es
\(M_{10}=1199\,\text{pu·s}\) (\(H_{10}=599.5\,\text{s}\)), es decir
**66.1 % de la inercia total del sistema** (\(\sum M = 1813.85\,\text{pu·s}\),
\(\sum H = 906.92\,\text{s}\)). Escalar las 10 máquinas escalaría en su
mayoría un equivalente de red externa, no la flota real del área de estudio.

**Decisión congelada:** escalar la inercia **solo de los 9 generadores del
área** (`GENROU_1`…`GENROU_9`, buses 30–38). `GENROU_10`/bus 39 (Slack)
permanece con su inercia original.

\[
M_i^{LI}=k\,M_i^{base},\quad i=1,\ldots,9
\]

con \(k\) tomado de la escalera **ya congelada en §5.3**,
\(k\in\{0.50,0.30\}\).

**Corrección (revisión externa, ronda 3):** una versión anterior de este
bloque fijaba \(k=0.70\) tanto en la fórmula como en el código — un valor
que §5.3 ya había descartado (rendía solo −10.2% de reducción de
\(H_{total}\), insuficiente) antes de que este documento tuviera su primera
versión ejecutable. El bloque de código nunca se sincronizó con esa
corrección; ejecutarlo literalmente habría aplicado un factor ya conocido
como insuficiente. Se elimina \(0.70\) del bloque ejecutable; `k` se pasa
como parámetro, no hard-coded:

Implementación, después de `ss = andes.load(case, setup=True, ...)` y antes de
`ss.TDS.init()`:

```python
area_idx = [f"GENROU_{i}" for i in range(1, 10)]  # excluye GENROU_10 (bus 39, Slack)
uids = ss.GENROU.idx2uid(area_idx)
k = 0.50  # primer valor de la escalera de §5.3; si LI-1 falla, reintentar con k=0.30 (nunca 0.70)
ss.GENROU.M.v[uids] *= k
```

Con solo 9/10 máquinas escaladas, la reducción de \(\sum H\) del sistema es
menor que si se escalaran las 10 (ver la tabla de §5.3: −17.0 % a \(k=0.50\),
−23.7 % a \(k=0.30\), dado que las 9 máquinas del área suman
\(H=307.4\,\text{s}\) de los 906.92 s totales). Esto es exactamente lo que el
Gate LI-1 siguiente debe verificar empíricamente: si la perturbación
resultante es insuficiente con \(k=0.50\), reintentar con \(k=0.30\) (§5.3);
si tampoco basta, aplicar STOP-A.

### 5.3 Gate LI-1

Antes de continuar:

1. Power flow debe converger.
2. TDS debe inicializar.
3. EIG no debe mostrar modos dinámicos inestables introducidos por la modificación.
4. Una contingencia de diseño sin FFC debe producir una perturbación de frecuencia suficientemente relevante.

Usar para este gate únicamente un generador perteneciente posteriormente al conjunto de **training**, nunca un generador reservado para test.

**Riesgo cuantificado de la escalera original.** Con el equivalente del bus 39
intacto (\(H_{10}=599.5\,\text{s}\)) y escalando solo las 9 máquinas del área
(\(H_{1..9}=307.42\,\text{s}\)) por un factor \(k\):

\[
H_{total}(k) = 599.5 + 307.42\,k \quad [\text{s}]
\]

| \(k\) | \(H_{total}\) | Reducción vs. base (906.92 s) |
|---|---|---|
| 0.70 | 814.7 s | −10.2 % |
| 0.50 | 753.2 s | −17.0 % |
| 0.30 | 691.7 s | −23.7 % |
| →0 (techo) | 599.5 s | −33.9 % |

La reducción de inercia del sistema **está acotada a un máximo de 33.9 %**
aunque las 9 máquinas se anulen por completo — el equivalente del bus 39 fija
un piso. La escalera original \(\{0.70,0.50\}\) produce solo entre −10.2 % y
−17.0 %, casi con certeza insuficiente para excursiones de frecuencia
relevantes en un estudio de FFC. **Se corrige la escalera a:**

\[
k \in \{0.50,\ 0.30\}
\]

Si \(k=0.30\) sigue siendo insuficiente para el criterio 4 del gate,
**detener conforme a STOP-A y escalar la decisión al usuario** — las
opciones autorizadas son (a) de-ratear también el equivalente del bus 39 en
una magnitud acotada y registrada, o (b) reencuadrar el estudio con un piso
de inercia distinto. No seguir bajando \(k\) por debajo de 0.30 sin esa
decisión explícita.

Registrar \(H_{total}\) antes y después, y la fracción aportada por el
equivalente del bus 39, en cada intento del gate.

Después de la decisión final:

> **La inercia queda congelada y no puede volver a ajustarse para mejorar resultados.**

No realizar barridos de \(H\).

Registrar la decisión en `Paper_1/ops/sted/decision_log.md` y
`Paper_1/ops/sted/traceability_matrix.csv` (nunca en el `plan_maestro.md` de
la raíz — ver §27).

---

## 6. Modelo mínimo de los dos BESS/IBR

### 6.1 Principio

Los dos recursos deben ser idénticos:

\[
P_{max,1}=P_{max,2}
\]

\[
\tau_{P,1}=\tau_{P,2}
\]

y deben utilizar idénticos límites/rate constraints.

**Modelo verificado (ANDES 2.0.0, `andes/models/distributed/esd1.py`): usar
`ESD1`.** Es el único modelo de la biblioteca `distributed`/`renewable` que
combina (a) SoC nativo, (b) potencia bidireccional (`pmin = -pmx`) y (c) un
puerto de inyección externa de potencia diseñado exactamente para esto:

- `ESD1.Pext0` es un `ConstService` ("External additional signal added to
  Pext", `esd1.py`/`pvd1.py:375-378`) — el punto de inyección de un
  controlador externo (AGC/FFC). Escribirlo durante TDS surte efecto
  inmediato porque alimenta una ecuación algebraica resuelta cada paso.
- API de grupo (uniforme, ya la usa `AndesEnv`, ver §14):
  `ss.DG.set_paux(ss, idx, value)` escribe `Pext0`.
- `REGCA1`/`REGCP1` (grid-following, sin `RenExciter` adjunto) **no sirven**:
  no tienen `_setpoints` propio, `Ipcmd` está fijado por un `PostInitService`
  y `set_pref` lanza `KeyError` si no hay `REECA1/REECB1` conectado.
- `REGCV1`/`REGF1-3` (grid-forming) sí exponen `Pref` escribible, pero **no
  tienen SoC** — servirían solo si se decide explícitamente prescindir de SoC.

**Prioridad revisada (ya resuelta, no pendiente de inspección):**

1. `ESD1` — modelo por defecto de este plan.
2. Si `ESD1` resulta incompatible con la topología elegida en §7, usar
   `REGCV1`/`REGF1` (sin SoC) como alternativa registrada como decisión.
3. No implementar un wrapper de convertidor desde cero.

**Restricción de acoplamiento verificada:** `ESD1` (heredado de `PVD1`)
requiere un `StaticGen` (`gen`, `IdxParam`, `mandatory=True`, `replaces=True`)
en el mismo bus. No puede conectarse directamente a un bus de carga puro —
primero debe añadirse un `PV`/`StaticGen` en ese bus, y `gammap`/`gammaq` de
los dispositivos dinámicos que comparten ese `StaticGen` deben sumar 1.0. Esto
condiciona qué buses son "técnicamente admisibles" en el screening de §7.2.

**Droop interno de `ESD1` — verificar y congelar explícitamente.** `PVD1`
(base de `ESD1`) trae su propio bloque de respuesta a frecuencia:
`fdbd` (deadband, default `-0.017` pu) y `ddn` (ganancia de droop, **default
`0.0`**) alimentan un `DeadBand1` cuya salida `DB_y` entra directamente en
`Psum = Pext + Pref + DB_y`. Con `ddn=0.0` (el default de ANDES) este término
es inerte y no hay riesgo — pero como los dispositivos se crean
programáticamente (no vienen de un caso stock), debe **fijarse `ddn=0.0`
explícitamente** al instanciar cada `ESD1`, para los tres controladores
(No FFC, Droop, DDPG). Si no se fija así, un `ddn` distinto de cero
activaría un droop oculto: "No FFC" dejaría de ser realmente sin FFC, y
"Droop" tendría droop duplicado (el interno de `ESD1` más el de §17). Único
camino de mando de potencia activa autorizado: `Pext0` vía `set_paux`.

### 6.2 Dimensionamiento congelado

Definir:

\[
\Delta P^{train}_{max}
\]

como la mayor pérdida de potencia considerada dentro del dominio de entrenamiento.

Dimensionar cada BESS como:

\[
P_{max,BESS}=0.25\,\Delta P^{train}_{max}
\]

Por tanto:

\[
P_{max,total}=0.50\,\Delta P^{train}_{max}
\]

Este valor no se optimiza posteriormente.

Ambos controladores —droop y DDPG— reciben exactamente la misma capacidad.

### 6.3 Límites

Acción normalizada:

\[
a_i\in[-1,1]
\]

Conversión:

\[
\Delta P_i^\star=a_iP_{max,BESS}
\]

Aplicar siempre:

\[
|\Delta P_i^\star|\le P_{max,BESS}
\]

Registrar también cualquier rate limit que imponga el modelo nativo.

### 6.4 Energía

No desarrollar modelo electroquímico.

Calcular únicamente el throughput energético:

\[
E_{BESS}=
\int_{t_d}^{t_f}
\left(
|P_{BESS1}(t)|+
|P_{BESS2}(t)|
\right)dt
\]

La energía se utiliza como **métrica de esfuerzo de control**, no como objetivo de dimensionamiento del dispositivo.

**Nota sobre SoC (coherente con la exclusión de §3):** `ESD1` trae SoC
integrado de fábrica (`esd1.py`, estado `pIG_y`, alias `SOC`) y sus límites
`SOCmin`/`SOCmax` **sí bloquean físicamente** `Ipmax`/`Ipmin` si se saturan.
Con episodios de \(t_f=6\,\text{s}\) y BESS del orden de decenas–cientos de
MW, el throughput de energía por episodio es del orden de
\(P\cdot t/3600\ll En\) (p. ej. 200 MW × 5 s ≈ 0.28 MWh frente al
\(En=100\,\text{MWh}\) por defecto), de modo que el SoC no se satura dentro
de un episodio con los valores por defecto de `En`/`SOCmin`/`SOCmax`. No es
necesario modelar electroquímica: basta con **no reducir `En` por debajo de
su valor por defecto**, dejando el SoC presente pero inerte en la escala de
tiempo de FFC. Verificar esto en Gate LI-1/P1-E2 y registrar el valor de `En`
usado.

**Condiciones iniciales del BESS (revisión externa, completa la
especificación).** Al instanciar cada `ESD1`/`PV` auxiliar:

\[
P_{BESS,0}=0,\quad Q_{BESS,0}=0,\quad SOC_0=0.5,\quad SOC_{min}<0.5<SOC_{max}
\]

El `StaticGen`/`PV` auxiliar requerido por §6.1 para acoplar `ESD1` a la red
no debe alterar el despacho base: su potencia neta programada es cero antes
del evento. `Sn` (rating del `ESD1`) y `pmx`/`pmn` (`= ±Sn`, o el límite que
imponga `Ipmax`) deben fijarse de forma consistente con \(P_{max,BESS}\) de
§6.2 — no un valor de plantilla arbitrario. Registrar \(P_0\), \(Q_0\),
\(SOC_0\), `Sn`, `pmx` junto con `En` en `Paper_1/ops/sted/decision_log.md`.

---

## 7. Selección de ubicación de los dos BESS

Esta etapa debe ocurrir **antes de entrenar DDPG**.

Después de seleccionar los buses:

> Queda prohibido modificar la ubicación en función de resultados de training, validation o test.

### 7.1 Prohibiciones

No elegir buses:

- arbitrariamente;
- porque produzcan mejores resultados con DDPG;
- usando escenarios reservados para test;
- usando información del conjunto final.

### 7.2 Procedimiento mínimo de screening

#### Paso A — mapa de estrés sin FFC

Usar dos pérdidas de generación pertenecientes al conjunto de diseño/training, operating point nominal y sistema low-inertia.

Calcular para todos los buses técnicamente admisibles:

\[
S_b=
\frac{1}{2}
\frac{|\Delta f_{nadir,b}|}
{\max_j|\Delta f_{nadir,j}|}
+
\frac{1}{2}
\frac{|RoCoF_{max,b}|}
{\max_j|RoCoF_{max,j}|}
\]

**Precondición verificada:** el caso `ieee39_full.xlsx` solo trae `BusFreq`
(no `BusROCOF`) y únicamente en los 10 buses generadores (30–39). Los buses
de carga candidatos a este screening **no tienen ninguna medición de
frecuencia/RoCoF por defecto**. Antes de correr las simulaciones de este
paso, añadir dispositivos `BusROCOF` (que extiende `BusFreq` y agrega la
salida `Wf_y`, ver §14) en **todos los buses técnicamente admisibles**, no
solo en los 4 finalistas — el ranking \(S_b\) los necesita a todos. Con eso
sí: no son necesarias simulaciones adicionales por bus, extraer todos los
`BusFreq.f`/`BusROCOF.Wf_y` de las mismas trayectorias.

Seleccionar los **cuatro buses candidatos** con mayor \(S_b\), excluyendo:

- slack;
- buses donde la conexión del recurso produzca inconsistencias;
- buses que no permitan inicialización válida del modelo elegido.

#### Paso B — screening de pares

Con cuatro candidatos existen:

\[
\binom{4}{2}=6
\]

pares.

Evaluar esos seis pares usando una política fija, idéntica y **no aprendida**.

Puede usarse un pequeño pulso de soporte o un mismo droop provisional.

Ejecutar los seis pares frente a las mismas dos contingencias de diseño.

Score del par:

\[
J_{place}=
\frac{\Delta f_{max}}{0.5}
+
\frac{RoCoF_{max}}{1.0}
\]

Seleccionar:

\[
(b_1^\star,b_2^\star)
=
\arg\min J_{place}
\]

No incluir energía en esta selección.

### 7.3 Freeze

Antes del primer episodio DDPG registrar:

```text
BESS_BUS_1 = ...
BESS_BUS_2 = ...
PLACEMENT_FROZEN = TRUE
```

en `Paper_1/ops/sted/decision_log.md` y en el CSV consolidado (nunca en el
`plan_maestro.md` de la raíz — ver §27).

No crear un reporte de placement independiente.

---

## 8. Separación de generadores para train / validation / test

La separación se realiza una única vez y antes del entrenamiento.

### 8.1 Excluir slack

Identificar todas las máquinas síncronas online y excluir la unidad que actúe como slack/equivalente externo cuando sea metodológicamente necesario.

### 8.2 Test generators

Seleccionar dos generadores:

#### \(G_A\)

Mayor generador no-slack por potencia activa nominal.

#### \(G_B\)

Generador de mayor potencia restante cuya distancia eléctrica respecto a \(G_A\) sea mayor que la mediana de las distancias entre generadores.

Estos dos generadores:

> **Nunca aparecen durante training o validation.**

### 8.3 Validation generator

Seleccionar el siguiente generador de mayor potencia que no sea:

\[
G_A,\;G_B
\]

Denominarlo:

\[
G_V
\]

### 8.4 Training generators

Todos los generadores restantes admisibles:

\[
\mathcal G_{train}
\]

Registrar los IDs antes de entrenar.

---

## 9. Operating points

Definir un escalar:

\[
\lambda_L
\]

Escalar simultáneamente \(P\) y \(Q\) de las cargas por el mismo factor \(\lambda_L\): esto conserva el factor de potencia **exactamente**, no aproximadamente.

### Redespacho de generación

El caso `ieee39_full.xlsx` no define una regla de rebalanceo de generación al
escalar la carga. Sin una regla explícita, ANDES asignaría por defecto **todo**
el desbalance al Slack (`GENROU_10`/bus 39): en \(\lambda_L=1.10\) esto son
≈586 MW adicionales sobre un despacho nominal de 573 MW en esa máquina —
distorsiona una sola unidad y confunde el efecto que se quiere aislar (el
operating point) con un cambio artificial en la respuesta inercial local del
equivalente externo.

**Decisión congelada:** al aplicar \(\lambda_L\), escalar proporcionalmente la
potencia activa programada de los **generadores no-slack** (`PV_1`…`PV_9`,
buses 30–38) por el mismo factor \(\lambda_L\), y dejar que el Slack absorba
únicamente el residuo de pérdidas del power flow (su función normal). Esto
preserva la forma del despacho y la distribución de inercia entre operating
points — que es justamente lo que H3 necesita aislar. Verificar en el gate de
low-inertia que el Slack permanece dentro de \([p_{min},p_{max}]=[0,11]\,pu\)
en \(\lambda_L=1.10\) (con redespacho proporcional, el residuo de pérdidas es
del orden de las pérdidas nominales del caso, ≈0.37 pu, muy por debajo del
límite).

### Training

\[
\lambda_L\sim U(0.95,1.05)
\]

### Validation

Usar:

\[
\lambda_L\in\{0.95,1.05\}
\]

### Test fuera de distribución

\[
\lambda_L\in\{0.90,1.10\}
\]

Los operating points \(\pm10\%\):

> **No pueden utilizarse en training, validation, selección de buses, tuning de droop ni selección del checkpoint DDPG.**

Si ±10% no converge en power flow o TDS, reducir el extremo solo hasta el valor factible más cercano, en pasos de 2%, registrar la decisión y congelarlo.

No alterar topología.

---

## 10. Perturbaciones de training

Solo se usan pérdidas de generación.

Para cada episodio:

1. seleccionar aleatoriamente:

\[
G_j\in\mathcal G_{train}
\]

2. seleccionar:

\[
\rho\sim U(0.40,0.80)
\]

3. aplicar:

\[
\Delta P_G=-\rho P_{G_j,0}
\]

4. seleccionar:

\[
\lambda_L\sim U(0.95,1.05)
\]

La perturbación ocurre en:

\[
t_d=1.0\,s
\]

**Mecanismo verificado (con \(t_d\) fijo, no aleatorizado):** usar el modelo
nativo `Alter` de ANDES sobre `paux0` del gobernador de turbina
(`_setpoints={'pref':'pref0','paux':'paux0'}`, `paux0` es una señal aditiva
que parte de 0). Para cada generador de `G_train` se crea, **antes de
`setup()`**, un `Alter` con temporizador fijo:

```python
ss.add('Alter', model='TGOV1N', dev=Gj_idx, src='paux0',
       t=1.0, method='=', amount=0.0)   # amount se sobrescribe por episodio
```

**Verificado empíricamente en esta sesión** (3 episodios consecutivos,
`ss.TDS.reinit()` + `ss.TDS.run()`, caso `kundur_full.xlsx`,
`Alter` sobre `TGOV1.paux0` con `t=1.0`): el evento **se reactiva
correctamente en cada episodio** — `TDS.reinit()` llama internamente a
`_reset_integration()`, que reinicia `_switch_idx=0`, de modo que el
mecanismo de eventos vuelve a evaluar `switch_times` desde el principio. No
es necesario re-registrar el timer manualmente ni vigilar `info['t']` desde
el script orquestador.

Selección aleatoria por episodio (dentro de `disturbance_fn`, invocado por
`AndesEnv.reset()` justo después de `reinit()`, ver §14): fijar
`ss.Alter.amount.v[:] = 0.0` para todos los `Alter` de `G_train`, luego
`ss.Alter.amount.v[uid(G_j)] = -\rho \cdot P_{G_j,0}` solo para el generador
elegido ese episodio. `reinit()` restaura `paux0` a su valor post-`setup()`
(0.0) antes de que `disturbance_fn` lo sobrescriba, así que no hay
contaminación entre episodios.

**Nota sobre `Toggle`/`Toggler` (excluido, no contradice lo anterior):**
`Toggle`/`Toggler` solo soporta desconexión completa (invierte `u`), no
reducción parcial — **no sirve para \(\rho\in[0.4,0.8]\)** y por eso no se usa
en ningún punto de este plan. El único mecanismo retenido para la pérdida de
generación de entrenamiento es el `Alter` sobre `paux0` descrito arriba, ya
verificado empíricamente a través de `reinit()`.

**Corrección (revisión externa):** una versión anterior de esta sección
proponía además un segundo mecanismo (`ss.SynGen.set_pref(ss, G_j, (1-rho) *
P_G_j_0)` invocado desde `disturbance_fn`, explícitamente "sin dispositivo
Alter"), presentado como alternativa a lo ya verificado arriba. Los dos
mecanismos son incompatibles entre sí (no pueden coexistir escribiendo el
mismo `paux0`/`pref0`) y solo el basado en `Alter` cuenta con verificación
empírica de reactivación correcta en `reinit()`. Se elimina el mecanismo
`set_pref` y se congela `Alter` sobre `paux0` como único camino (protegido
por el Test T18, §30).

**Nota de precisión física (se conserva):** tanto `paux0` (mecanismo
retenido) como `pref0` (mecanismo descartado) actúan sobre la **referencia
del gobernador**, no sobre la potencia eléctrica medida `Pe`. La perturbación
de entrenamiento es, con precisión, una **reducción abrupta de la referencia
de potencia del gobernador** equivalente a una pérdida parcial de generación,
no una desconexión física de la unidad. Reportar esta distinción en la
sección de metodología del paper; el término "pérdida de generación" usado en
el resto del documento debe entenderse en ese sentido preciso.

No usar load steps en training.

---

## 11. Validation congelada

Crear solamente cuatro escenarios de validation usando \(G_V\):

| Val | \(\rho\) | \(\lambda_L\) |
|---|---:|---:|
| V1 | 0.50 | 0.95 |
| V2 | 0.70 | 0.95 |
| V3 | 0.50 | 1.05 |
| V4 | 0.70 | 1.05 |

Estos cuatro escenarios se usan para:

- tuning de droop;
- selección del mejor checkpoint DDPG;
- early stopping.

Nunca usar test para estas decisiones.

---

## 12. Test final congelado

Usar exactamente **ocho** escenarios.

No agregar más si el gate puede resolverse con estos ocho.

### 12.1 Generación no vista

| Test | Perturbación | OP |
|---|---|---|
| T1 | \(0.60P_{G_A}\) | nominal |
| T2 | \(0.60P_{G_B}\) | nominal |
| T3 | \(0.60P_{G_A}\) | \(-10\%\) |
| T4 | \(0.60P_{G_B}\) | \(+10\%\) |

**Corrección (revisión externa):** T3/T4 usaban originalmente \(\rho=0.80\)
mientras T1/T2 usan \(\rho=0.60\), de modo que T1→T3 y T2→T4 cambiaban
simultáneamente la magnitud de la perturbación **y** el operating point. El
gate de robustez P1-H3 (§24) usa exactamente T3, T4, T7, T8 para aislar el
efecto de un operating point no visto; con \(\rho\) distinto entre T1/T3 y
T2/T4, una degradación observada no podía atribuirse únicamente al operating
point. Se fija \(\rho=0.60\) también en T3/T4, igual que en T1/T2, de modo
que T1↔T3 y T2↔T4 cambian **una sola variable** (el operating point). T5↔T7 y
T6↔T8 ya tenían esta estructura pareada correctamente y no se modifican.
\(\rho=0.60\) sigue dentro del rango de entrenamiento \(U(0.40,0.80)\) (§10),
así que la componente OOD de T3/T4 sigue viniendo exclusivamente de
\(G_A\)/\(G_B\) (generadores no vistos) y de \(\lambda_L=\{-10\%,+10\%\}\)
(operating point no visto), no de la magnitud de \(\rho\).

### 12.2 Tipo de perturbación no visto

Elegir dos buses de carga importantes, \(L_A\) y \(L_B\), distintos de los buses BESS.

Selección:

- \(L_A\): mayor carga activa (excluir bus 39: es el bus del Slack);
- \(L_B\): mayor carga restante eléctricamente separada de \(L_A\).

**Escalón definido relativo a la carga local del bus** (no al total del
sistema): con la carga total en 5856.4 MW y el mayor bus de carga (bus 20) en
680 MW, un 5 % del sistema (292.8 MW) sería un +43 % local en el bus más
grande y +366 % en el más pequeño — físicamente no interpretable como "aumento
de carga" en la mayoría de los buses. Se define en su lugar:

\[
\Delta P_{L}=0.30\,P_{load,bus}^{nom}
\]

aplicado sobre la carga nominal propia de \(L_A\)/\(L_B\) en cada caso (no
sobre el total del sistema).

**Precondición de implementación verificada (ANDES 2.0.0,
`andes/models/static/pq.py`):** el modelo `PQ` viene por defecto en
**impedancia constante** (`config.p2p=0, config.p2z=1.0`). Alterar `Ppf`/`Qpf`
o `p0`/`q0` durante TDS **no tiene ningún efecto** con esta configuración.
Antes de `TDS.init()`, para los buses `L_A`/`L_B`:

```python
ss.PQ.config.p2p = 1.0; ss.PQ.config.p2i = 0.0; ss.PQ.config.p2z = 0.0
ss.PQ.config.q2q = 1.0; ss.PQ.config.q2i = 0.0; ss.PQ.config.q2z = 0.0
ss.PQ.config.pq2z = 0
```

Esto convierte **todo el caso** de impedancia constante a potencia constante
para el modelo `PQ` (es una configuración global del modelo, no por
dispositivo) — endurece la respuesta de frecuencia del sistema completo, no
solo de los buses perturbados.

**Corrección (revisión externa) — momento de aplicación.** Una versión
anterior de este plan aplicaba `PQ.config` a potencia constante solo para
correr T5–T8, dejando training/validation y T1–T4 en impedancia constante
(el default de ANDES). Eso introduce un confound: T5–T8 dejarían de aislar
"tipo de perturbación no visto" y pasarían a mezclarlo con "dinámica de carga
distinta durante toda la simulación", de modo que una diferencia observada en
T5–T8 no podría atribuirse a la perturbación en sí. **Se congela en su lugar
que el caso experimental completo usado en training, validation y test —no
solo T5–T8— use `PQ.config` a potencia constante desde su construcción en
P1-E1** (ver §31), antes de cualquier corrida. El caso base intacto sigue
preservado en `cases/ieee39/base/` (§5.1); la variante experimental
(low-inertia + BESS + `PQ` en potencia constante) es la que se usa en todo el
pipeline a partir de P1-E1. Repetir el Gate LI-1 (PFlow/TDS/EIG) sobre esta
variante después de aplicar `PQ.config`, antes de continuar a P1-E2.
**Registrar esto como decisión de modelado congelada** y reportarlo
explícitamente en el paper como una desviación del caso stock aplicada de
forma uniforme, no solo en un subconjunto de escenarios. Aplicar el escalón
de T5–T8 escribiendo `Ppf`/`Qpf` del bus objetivo en \(t_d\) (mismo mecanismo
que §10: llamada directa desde `disturbance_fn`, sin dispositivo `Alter`,
para evitar el problema de re-registro de tiempos de evento de `reinit()`).

| Test | Perturbación | OP |
|---|---|---|
| T5 | load step en \(L_A\) | nominal |
| T6 | load step en \(L_B\) | nominal |
| T7 | load step en \(L_A\) | \(-10\%\) |
| T8 | load step en \(L_B\) | \(+10\%\) |

No entrenar nuevamente después de observar T1–T8.

---

## 13. Observaciones DDPG

**Decisión revisada (corrige asimetría de información frente al baseline
droop):** la formulación original observaba las 20 señales (Δf, RoCoF) de los
10 generadores síncronos — información *wide-area* que el baseline droop de
§17 no recibe (mide solo la frecuencia local de su propio bus). Un DDPG así
ganaría, al menos en parte, por tener más información, no por ser una mejor
política. Se elimina esa asimetría: **DDPG queda restringido a las mismas
ubicaciones de medición disponibles para los controladores droop** (los dos
puntos de conexión de los BESS), sin acceso a mediciones system-wide durante
la ejecución. Esto es igualdad de **ubicación**, no de contenido exacto de
señal: DDPG dispone además de RoCoF y de la potencia propia entregada en
ambos POI, mientras que cada droop solo necesita su propia frecuencia local
(ver §13.1 para la comparación completa de recursos).

Para cada BESS \(k\in\{1,2\}\), en su bus de conexión:

\[
\Delta f_k = f_k - f_0
\]

y su RoCoF local (ver §14 para la cadena de filtros `BusROCOF`), más
realimentación de la propia potencia entregada:

\[
o_k=
[
\Delta f_1,\ \Delta f_2,\ RoCoF_1,\ RoCoF_2,\ P_{BESS1},\ P_{BESS2}
]
\]

\[
n_o=6
\]

No incluir:

- voltajes;
- ángulos;
- cargas;
- potencia de líneas;
- SoC;
- IDs de contingencia;
- magnitud real de la perturbación;
- frecuencia/RoCoF de generadores u otros buses distintos de los dos puntos
  de conexión BESS.

La política debe inferir la respuesta a partir de la dinámica observada
localmente.

Normalizar:

\[
\widetilde{\Delta f_k}
=
\frac{\Delta f_k}{0.5\,Hz}
\]

\[
\widetilde{RoCoF_k}
=
\frac{RoCoF_k}{1\,Hz/s}
\]

\[
\widetilde{P_{BESS,k}}
=
\frac{P_{BESS,k}}{P_{max,BESS}}
\]

### 13.1 DDPG centralizado con observación local en los POI y señal privilegiada de entrenamiento — leer junto con §15/§21

**Corrección de terminología (revisión externa):** la sección se llamaba
"Centralized-training / decentralized-execution (CTDE)". Es un nombre
incorrecto: CTDE es un término de MARL en el que **múltiples agentes**
decentralizados actúan cada uno solo sobre su propia observación local en
ejecución. Aquí hay un **único actor centralizado** que recibe conjuntamente
\(o=[\Delta f_1,\Delta f_2,RoCoF_1,RoCoF_2,P_{BESS1},P_{BESS2}]\) de **ambos**
puntos de conexión y produce conjuntamente \(a=[\Delta P_1^\star,\Delta
P_2^\star]\). Esto es **ejecución centralizada con observabilidad
espacialmente escasa** (solo dos POI, sin voltajes/ángulos/otros buses), no
ejecución decentralizada. Que las señales provengan únicamente de los dos POI
no cambia quién ejecuta la política.

La arquitectura correcta a describir en el paper es: **DDPG centralizado con
mediciones dispersas en los puntos de conexión y con información privilegiada
solo en entrenamiento**. La **observación** de la política (§13) es local y
de despliegue realista: solo lo medible en los dos puntos de conexión. La
**reward** (§15) y las **métricas de evaluación** (§21) siguen siendo
*system-wide* (peor frecuencia y peor RoCoF de los 10 generadores, ver P-1.5)
porque son señales **privilegiadas**, disponibles solo en simulación durante
entrenamiento y evaluación, no en despliegue — la política nunca *observa* ni
*actúa* usando la señal privilegiada, solo se *entrena* para optimizarla. Esto
es coherente con `AndesEnv`: la reward puede consultar cantidades del sistema
que no forman parte del vector de observación.

El droop de §17 es comparable en recursos, no en arquitectura: usa las mismas
ubicaciones, los mismos actuadores, los mismos límites de potencia y el mismo
conjunto de perturbaciones que DDPG (**same sensing locations, same
actuators, same power limits, same disturbance set**), y también se calibra
(§17.1) con la señal privilegiada system-wide \(J_{val}\) en V1–V4 — pero DDPG
adicionalmente dispone de RoCoF y de la propia potencia entregada en ambos
POI, mientras que droop solo necesita su frecuencia local. Reportar esta
comparación de recursos (no de arquitectura) explícitamente en la sección de
metodología del paper, evitando el término CTDE.

---

## 14. Tiempo de simulación y control

Usar:

\[
t_f=6\,s
\]

\[
t_d=1\,s
\]

\[
T_{control}=100\,ms
\]

Por tanto, con \(t_f=6\,s\) el controlador ejecuta \(N_{step}=t_f/T_{control}=60\) acciones por
episodio en total (desde \(t=0\)), de las cuales \(\approx 50\) son posteriores al evento en
\(t_d=1\,s\). Esta cuenta de 60 pasos/episodio es la que se usa en §18.1 para `learning_starts` y el
conteo de transiciones — no confundir con el subconjunto post-evento.

Usar un timestep interno de TDS suficientemente menor que el control step;
fijar explícitamente (ANDES 2.0.0, `TDS.config`, valores por defecto del
solver estándar):

```text
tstep  = 1/60 s
fixt   = 1        # paso fijo
method = 'trapezoid'
```

No hacer sweep del timestep. Solo reducirlo si existen problemas numéricos
demostrables. **Advertencia verificada:** con `fixt=0` o métodos adaptativos,
`_calc_h_first()` re-deriva el paso en cada frontera de 100 ms de control
(porque `tspan` cambia cada vez que se avanza `TDS.config.tf` para reanudar la
simulación) — riesgo de inconsistencia numérica entre pasos de control. Usar
`fixt=1` evita esto.

**Medición de RoCoF — corrección de doble filtrado.** El plan original pedía
"un promedio móvil cercano a 60 ms" sobre el RoCoF. Verificado en ANDES 2.0.0
(`andes/models/measurement/busrocof.py`): `BusROCOF` ya es una cascada de
tres etapas — `Lag(Tf)` → `Washout(Tw)` → `Washout(Tr)` — y en
`ieee39_full.xlsx` los `BusFreq` existentes traen `Tf=0.02`, `Tw=0.02`
(el default del código ANDES es `Tw=0.1`; **el caso lo sobreescribe**, no citar
0.1 s). Con el default `Tr=0.1 s`, el retardo de grupo del RoCoF ya es del
orden de un período de control completo (100 ms) **antes** de añadir
cualquier promedio móvil adicional.

**Se elimina el promedio móvil de 60 ms.** `BusROCOF` es el único filtro
declarado. Para mantener el retardo por debajo del período de control, fijar:

```text
BusROCOF.Tf = 0.02   # heredado de BusFreq, igual que en el caso
BusROCOF.Tw = 0.02   # heredado de BusFreq, igual que en el caso
BusROCOF.Tr = 0.05   # reducido del default 0.1 s
```

Reportar la cascada completa `(Tf, Tw, Tr)` — tomada de la configuración
real, no de la documentación de ANDES — en la sección de metodología. `Tr` no
se ajusta después de fijado aquí (no es un hiperparámetro de tuning).

`BusROCOF` **no viene en `ieee39_full.xlsx`** (el caso solo trae `BusFreq`, y
solo en los buses 30–39). Debe añadirse con `andes.load(..., setup=False)`,
`ss.add('BusROCOF', bus=..., Tf=0.02, Tw=0.02, Tr=0.05)` en los buses BESS (y,
para el screening de §7.2, en todos los buses candidatos), y solo entonces
llamar `ss.setup()` — `System.add()` lanza `NotImplementedError` si se llama
después de `setup()`.

**Medición system-wide para reward y métricas (resuelve P-1.5).** Además de
los `BusROCOF` en los buses BESS, añadir `BusROCOF` (mismos `Tf=0.02,
Tw=0.02, Tr=0.05`) en los **10 buses de generación (30–39)** — el caso stock
solo trae `BusFreq` ahí (ver §0.2), no `BusROCOF`. La reward (§15) y las
métricas system-wide \(f_{nadir}\)/\(RoCoF_{max}\) (§21) se calculan sobre
estos 10 `BusFreq`/`BusROCOF`, con la misma cascada de filtro que la
observación local de §13 — no sobre `GENROU.omega` sin filtrar. Esto da una
única definición de frecuencia y una única definición de RoCoF para
observación, reward, métricas y gates.

**Paridad temporal droop/DDPG (revisión externa).** Ambos controladores
comandan `Pext0` a través del mismo retenedor de orden cero de
\(T_{control}=100\,ms\): \(P^\star\to\text{ZOH}(100\,ms)\to Pext0\). El droop
de §17 no actualiza continuamente mientras DDPG actúa solo cada 100 ms — las
dos estrategias comparten la misma interfaz temporal de actuación, fijada
aquí como \(T_c^{droop}=T_c^{DDPG}=100\,ms\). `AndesEnv.step()` ya avanza la
simulación en intervalos de `dt` fijos, de modo que aplicar el mismo `dt` a
la evaluación del droop (fuera de `AndesEnv`, en las corridas de No-FFC/
Droop) es la única forma de mantener la comparación libre de esta asimetría.

---

## 15. Reward DDPG

**Nota de alcance (ver §13.1):** a diferencia de la observación
\(o_k\) (§13, local a los dos puntos de conexión), esta reward usa
\(\Delta f_i\)/\(RoCoF_i\) de **los 10 generadores síncronos** — es una señal
privilegiada, disponible solo en simulación, para entrenar la política. La
política nunca observa estas 10 señales; solo se entrena para optimizar una
función de ellas. \(\max_i\) en las fórmulas siguientes recorre los 10
generadores, evaluado en el instante \(k\) del paso de control actual (no un
máximo acumulado sobre el episodio completo).

No realizar búsqueda de reward.

Usar una única reward normalizada:

\[
r_k=
-
\left[
e_f^2+
e_r^2+
0.1e_u
\right]
-
10I_{unsafe}
-
100I_{fail}
\]

donde:

\[
e_f=
\frac{
\max_i|\Delta f_i|
}{0.5}
\]

\[
e_r=
\frac{
\max_i|RoCoF_i|
}{1.0}
\]

\[
e_u=
\frac{|P_{BESS1}|+|P_{BESS2}|}
{2P_{max,BESS}}
\]

y:

\[
I_{unsafe}=1
\]

si:

\[
\max_i|\Delta f_i|>0.5\,Hz
\]

o:

\[
\max_i|RoCoF_i|>1\,Hz/s
\]

Los valores \(0.5\) Hz y \(1\) Hz/s se utilizan aquí como límites experimentales coherentes con Stanojev, no como afirmación de requisitos regulatorios universales.

Si TDS no converge:

\[
I_{fail}=1
\]

y terminar inmediatamente el episodio.

No introducir más términos en la reward.

---

## 16. Baseline 1 — No FFC

Definir:

\[
P_{BESS1}=P_{BESS2}=0
\]

Los BESS pueden permanecer conectados si su modelo lo requiere, pero no prestan soporte FFC.

---

## 17. Baseline 2 — Droop FFC

Usar:

\[
\Delta P_i^\star
=
-K_d(f_{BESS,i}-f_0)
\]

con saturación:

\[
|\Delta P_i^\star|\le P_{max,BESS}
\]

Los dos BESS deben usar el mismo \(K_d\).

### 17.1 Tuning permitido

Definir:

\[
K_0=\frac{P_{max,BESS}}{0.5\,Hz}
\]

Evaluar únicamente:

\[
K_d\in
\{
0.25K_0,\;
0.5K_0,\;
K_0,\;
2K_0,\;
4K_0
\}
\]

Elegir el valor con menor objective sobre los cuatro escenarios V1–V4:

\[
J_{val}=
\frac{\Delta f_{max}}{0.5}
+
\frac{RoCoF_{max}}{1}
+
0.1
\frac{E_{BESS}}{E_{max}}
\]

No hacer un segundo sweep salvo que el mejor valor esté en un extremo de la grilla; en ese caso se permite **una única extensión de un punto**.

**Criterio de selección compartido (revisión externa):** este mismo
\(J_{val}\) —no un criterio distinto— es el que usa §20 para seleccionar el
checkpoint final de cada seed DDPG. Droop y DDPG se seleccionan así con la
misma función objetivo sobre las mismas cuatro escenarios V1–V4.

Después:

```text
DROOP_GAIN_FROZEN = TRUE
```

---

## 18. DDPG

Usar DDPG original, no TD3.

La implementación preferida es Stable-Baselines3 DDPG integrada con el entorno Gymnasium de ANDES.

No implementar el algoritmo desde cero salvo incompatibilidad demostrable.

**Verificado (ANDES 2.0.0):** el paquete sí trae un entorno Gymnasium listo,
`from andes.rl import AndesEnv` (`andes/rl/env.py`), con paso de control por
defecto `dt=0.1 s` (coincide con §14) y API `set_paux`/`set_pref` a nivel de
grupo. **`stable-baselines3` y `torch` NO están instalados y no son
dependencia de ANDES** (los extras declarados son `dev, doc, interop, web,
rl, performance, all`; ninguno instala SB3/torch). Añadir explícitamente a
`requirements.txt`:

```text
stable-baselines3
```

(arrastra `torch`). Nota operativa: instalar `torch` en esta ruta OneDrive
puede volver a chocar con el límite de ruta de Windows (`WinError 206`, ya
ocurrido al instalar `ipywidgets` en esta sesión) — usar el mismo mapeo
`subst Z:` a la raíz del repo si reaparece.

`AndesEnv` construye `observation_space`/`action_space` como `Box` con
límites `±inf` por defecto y **sin normalización propia**: fijar
explícitamente `action_low=-1, action_high=1` (coherente con §6.3) y bounds
finitos de observación (p. ej. `±5` sobre las magnitudes ya normalizadas de
§13), porque SB3 DDPG requiere espacios acotados. `AndesEnv` también fuerza
`TDS.config.save_every=0` — reactivar `save_every>=1` en las corridas de
evaluación (T1–T8 y la corrida de Figura 1), o no habrá trayectorias que
graficar.

### 18.1 Hiperparámetros iniciales

Seguir Stanojev donde resulte directamente compatible:

```text
buffer_size      = 600000
batch_size       = 256
gamma            = 0.99
tau              = 0.001
OU sigma         = 0.02
OU theta         = 0.15      # default SB3, no especificado en Stanojev
actor hidden     = [128, 128]
critic hidden    = [128, 128, 128]
control dt       = 0.1 s
learning_starts  = 600       # 10 episodios de warm-up (10 x 60 pasos/episodio, ver §14; 256 es
                              # batch_size, no pasos por episodio -- corregido, revisión externa)
train_freq       = 1         # step
gradient_steps   = 1
```

Redes asimétricas actor/crítico en SB3:

```python
policy_kwargs = dict(net_arch=dict(pi=[128, 128], qf=[128, 128, 128]))
```

Usar ReLU.

Si la biblioteca obliga a utilizar un único learning rate actor/critic:

```text
learning_rate = 1e-4
```

y documentar esa pequeña desviación respecto al paper.

**Nota de coherencia (corregida, revisión externa):** con \(t_f=6\,s\) hay
\(N_{step}=60\) pasos de control por episodio (§14, no 50 — 50 es solo el
subconjunto posterior al evento), luego 8000 episodios/seed × 60 = 480 000
transiciones máximas por seed, no 400 000. Con `buffer_size=600000` el buffer
**no llega a rotar** en este presupuesto (480 000 < 600 000), pero por un
margen mucho menor que el que sugería el cálculo original. Esta conclusión es
**condicional al horizonte congelado en P-1.6**: si LI-1 activa la extensión
a \(t_f=10\,s\), \(N_{step}=100\) y el total sube a 800 000 transiciones/seed,
superando `buffer_size` — en ese caso el buffer sí empieza a descartar
transiciones antiguas y debe reportarse así, no como "nunca se llena".

No hacer hyperparameter sweep.

---

## 19. Tres seeds

Usar exactamente:

```text
seed = 11
seed = 22
seed = 33
```

Cada seed se entrena completamente independiente.

No elegir la seed que se vea mejor en test.

---

## 20. Presupuesto de entrenamiento y early stopping

### 20.0 Gate previo de factibilidad computacional

Antes de comprometerse al presupuesto completo (3 seeds × 8000 episodios =
24 000 episodios): cronometrar 10 episodios completos de entrenamiento en la
etapa `benchmark` (ver §28), extrapolar linealmente a 24 000 episodios, y si
el tiempo proyectado excede lo operativamente disponible, **reducir el
presupuesto con una decisión registrada antes de entrenar** (nunca reducirlo
a mitad de entrenamiento para "que termine"). Dos causas de lentitud
verificadas en ANDES 2.0.0 a evitar antes de cronometrar:

- `TDS.run()` reconstruye el plotter interactivo (`load_plotter()`) en cada
  invocación si se ejecuta en Jupyter/notebook — **entrenar como script
  plano**, nunca en notebook.
- Cada `TDS.run()` emite una línea de log `INFO` por invocación (~200
  líneas/episodio a `dt=0.1s`, `t_f=6s`) — bajar el nivel de logging antes de
  cronometrar, o el I/O de consola domina el tiempo medido.

Máximo:

\[
8000\;\text{episodios/seed}
\]

Evaluar V1–V4 cada:

\[
200\;\text{episodios}
\]

No habilitar early stopping antes de:

\[
2000\;\text{episodios}
\]

Detener si el score medio de validation no mejora durante:

\[
5
\]

evaluaciones consecutivas, equivalentes a:

\[
1000\;\text{episodios}
\]

Guardar solamente el checkpoint con mejor validation score para cada seed,
usando **el mismo objetivo \(J_{val}\) definido en §17.1** (no un criterio
distinto para droop y para DDPG):

\[
\theta_s^\star=\arg\min_{\theta_{checkpoint}} J_{val}(\theta_{checkpoint})
\]

evaluado sobre V1–V4. Droop y DDPG comparten así el mismo criterio de
selección final; la reward de entrenamiento (§15) puede seguir siendo
distinta de \(J_{val}\) porque es el objetivo de aprendizaje, no el criterio
de selección de modelo.

Eliminar/no conservar checkpoints periódicos.

Al final deben existir solamente tres políticas finales.

---

## 21. Métricas

**Notación unificada:** \(\Delta f_i(t) = f_i(t) - f_0\) para todo el
documento (ya usada en §13/§15). El nadir se reporta como
\(f_{nadir}=f_0+\min_{i,t}\Delta f_i(t)\), equivalente a la definición
original pero explícito en Δf para evitar ambigüedad entre "frecuencia
absoluta" y "desviación". El índice \(i\) recorre los **10 buses de
generación (30–39)**, medidos vía `BusFreq`/`BusROCOF` (P-1.5, resuelto —
ver §14), tanto para \(f_{nadir}\) como para \(RoCoF_{max}\), en la reward de
§15 y en los gates §22–§24.

### 21.1 Primarias

#### Worst-system nadir

\[
f_{nadir}
=
\min_{i,t} f_i(t)
\]

#### Worst-system RoCoF

\[
RoCoF_{max}
=
\max_{i,t}|RoCoF_i(t)|
\]

### 21.2 Secundarias

#### Potencia pico total BESS

\[
P_{peak}
=
\max_t
\left(
|P_1(t)|+|P_2(t)|
\right)
\]

#### Energía/throughput

\[
E=
\int
(|P_1|+|P_2|)
dt
\]

#### Saturación

- número de eventos de saturación;
- porcentaje de la ventana FFC en saturación.

#### Robustez a operating point

Para cada controlador calcular degradación relativa entre nominal y ±10%.

**Corrección (revisión externa):** para el nadir, \(m\) no puede ser la
frecuencia absoluta \(f_{nadir}\) (siempre cercana a \(f_0=60\,Hz\)): un
cociente relativo sobre un valor absoluto de ese tamaño diluye numéricamente
cualquier diferencia real (un cambio de 0.3 Hz sobre ~59.7 Hz da ~0.5%,
independientemente de cuán severa sea la degradación real). Se usa en su
lugar la **desviación** \(\Delta f_{nadir}=\min_{i,t}\Delta f_i(t)\) (ya
definida arriba), coherente con \(e_f\) (§15) y con \(I_f\) (§22).

**Indexación por controlador y por par (revisión externa, ronda 3):** estas
degradaciones se calculan **por controlador \(c\)** y **por par pareado**
\((T_{nom},T_{OOD})\in\{(T1,T3),(T2,T4),(T5,T7),(T6,T8)\}\) (§12.1/§12.2, cada
par cambia solo el operating point) — no como un agregado único sobre "todo
nominal" vs "todo OOD". Es exactamente la comparación que consume el gate de
robustez P1-H3 (§24):

\[
D_{\Delta f}^{(c)}(p)=
\frac{
|\Delta f_{nadir,OOD}^{(c)}|-|\Delta f_{nadir,nom}^{(c)}|
}{
|\Delta f_{nadir,nom}^{(c)}|
}
\]

Para RoCoF, que ya es una magnitud de tipo desviación (\(\max|RoCoF|\), no un
valor absoluto desplazado de un punto de operación), no se requiere el
ajuste de \(m\) a desviación, pero sí la misma indexación por controlador y
por par:

\[
D_{RoCoF}^{(c)}(p)=
\frac{
RoCoF_{max,OOD}^{(c)}-RoCoF_{max,nom}^{(c)}
}{
RoCoF_{max,nom}^{(c)}
}
\]

No crear métricas adicionales salvo que una de estas sea imposible de calcular.

---

## 22. Gate de éxito científico

### Gate principal P1-H1

**Nota de nomenclatura:** el identificador de este gate era `G-FFC` en la
versión original; se renombra a **`P1-H1`** para no colisionar con los gates
STED-RW de la raíz del repositorio (`G0`–`G4`, ver nota al inicio del
documento). El resto de este documento usa el prefijo `P1-` para todo gate
propio de `Paper_1` (ver §31 para la renumeración completa de las etapas de
ejecución).

Utilizar la **mediana de las tres seeds DDPG, calculada por escenario y por
métrica de forma independiente** (la mediana de \(f_{nadir}\) entre las 3
seeds en el escenario T1, la mediana de \(RoCoF_{max}\) entre las 3 seeds en
T1, y así para cada uno de T1–T8). Un escenario cuenta como "win" solo si
**ambas** medianas (nadir y RoCoF) mejoran sobre droop simultáneamente en ese
escenario — no se promedian ni combinan entre escenarios antes de contar.

**Margen mínimo de victoria (P-1.4, resuelto, revisión externa).** Una mejora
nominal no basta: debe superar un margen relativo mínimo del 1%, simultáneo
en ambas métricas, medido contra droop como denominador:

\[
I_f=\frac{|\Delta f_{nadir}^{droop}|-|\Delta f_{nadir}^{DDPG}|}{|\Delta f_{nadir}^{droop}|}\ge0.01
\quad\text{y}\quad
I_r=\frac{RoCoF_{max}^{droop}-RoCoF_{max}^{DDPG}}{RoCoF_{max}^{droop}}\ge0.01
\]

evaluadas sobre las medianas de las 3 seeds. El 1% es un **umbral mínimo de
efecto pre-registrado para este benchmark**, no una afirmación de requisito
físico o regulatorio; existe para que el gate no pueda pasarse por ruido de
integración numérico (una diferencia de 1 mHz o 1e-3 Hz/s no cuenta como
"win"). Este criterio reemplaza las desigualdades estrictas sin margen de la
versión original:

\[
f_{nadir}^{DDPG}>f_{nadir}^{droop}
\quad\text{y}\quad
RoCoF_{max}^{DDPG}<RoCoF_{max}^{droop}
\]

en al menos:

\[
6/8
\]

escenarios finales.

Además:

- al menos 2 de las 3 seeds deben superar simultáneamente droop (mismo criterio de margen \(I_f\ge0.01\), \(I_r\ge0.01\)) en al menos 5/8 escenarios;
- ninguna seed final puede producir fallo de TDS;
- ningún controlador puede exceder los límites de potencia especificados.

Si esto no se cumple:

> **No agregar experimentos para buscar casos favorables.**

El claim H1 queda rechazado o condicionado.

---

## 23. Gate de eficiencia energética (P1-H2)

**Corrección (revisión externa, ronda 3) — de "seguridad comparable" a
dominancia tipo Pareto.** La versión anterior filtraba a los escenarios
donde ambos controladores satisfacían \(|\Delta f|_{max}\le0.5\,Hz\) y
\(RoCoF_{max}\le1\,Hz/s\), y comparaba energía/potencia solo ahí. Eso no
garantiza "seguridad comparable": un droop en 0.49 Hz y un DDPG en 0.25 Hz
pasan igual el umbral pero no son igualmente seguros — si DDPG además usa
menos energía, la comparación queda confundida entre "más eficiente a igual
seguridad" y "opera en un punto distinto de la curva esfuerzo-seguridad". Se
reformula como comparación de dominancia por escenario (H2 revisada, §2),
sin filtro de umbral absoluto y sin necesidad de un experimento adicional de
"matched security".

Un escenario \(s\in\{T1,\ldots,T8\}\) apoya H2 si, simultáneamente (evaluado
sobre la mediana de las 3 seeds, como en §22):

\[
|\Delta f_{nadir}|_s^{DDPG}\le|\Delta f_{nadir}|_s^{droop}
\quad\text{y}\quad
RoCoF_{max,s}^{DDPG}\le RoCoF_{max,s}^{droop}
\]

y, además (al menos una de):

\[
E_{DDPG,s}<E_{droop,s}
\qquad\text{y/o}\qquad
P_{peak,DDPG,s}<P_{peak,droop,s}
\]

Claim fuerte permitido únicamente si esta condición se cumple en la mayoría
de los 8 escenarios.

Si en un escenario DDPG es al menos tan seguro pero usa más energía y más
potencia pico:

> no ocultarlo y no fabricar una comparación adicional que lo disimule.

Ese escenario simplemente no apoya H2. Si la mayoría de los 8 escenarios no
cumple la condición de dominancia, la evidencia no soporta H2 — declararlo
explícitamente en §33/decision log, sin agregar escenarios ni comparaciones
para forzar un resultado favorable.

---

## 24. Gate de robustez (P1-H3)

**Corrección (revisión externa, ronda 3) — el gate no coincidía con el
enunciado de H3.** H3 (§2) afirma que "la degradación de DDPG ante operating
points no vistos no es mayor que la de droop" — una afirmación sobre
**degradación relativa entre controladores**, no sobre desempeño absoluto.
La versión anterior de este gate evaluaba en cambio si DDPG le ganaba a
droop en términos absolutos en T3, T4, T7, T8 — una afirmación distinta, más
cercana a una extensión de H1 a escenarios OOD que a H3 tal como está
enunciada.

Se evalúa H3 sobre los **pares aislados** construidos en §12.1/§12.2 (cada
par cambia una sola variable, el operating point, gracias a la corrección
T3/T4 de la ronda 2):

\[
(T1,T3),\ (T2,T4),\ (T5,T7),\ (T6,T8)
\]

Para cada controlador \(c\) y cada par \(p\), usando \(D_{\Delta f}^{(c)}(p)\)
y \(D_{RoCoF}^{(c)}(p)\) de §21.2 (degradación nominal → OOD del par,
evaluada sobre la mediana de las 3 seeds), un par \(p\) apoya H3 si:

\[
D_{\Delta f}^{DDPG}(p)\le D_{\Delta f}^{droop}(p)+\epsilon_D
\quad\text{y}\quad
D_{RoCoF}^{DDPG}(p)\le D_{RoCoF}^{droop}(p)+\epsilon_D
\]

con \(\epsilon_D=0.01\) — la misma tolerancia pre-registrada de P-1.4/§22, no
un umbral nuevo. H3 se acepta si esto se cumple en al menos:

\[
3/4
\]

pares.

**Nota de alcance:** que DDPG además le gane a droop en términos absolutos en
T3, T4, T7, T8 (desigualdades de §22) es evidencia adicional para **H1** —ya
contabilizada en su 6/8 sobre los ocho escenarios— y puede reportarse como
tal; no es parte del criterio de H3 y no debe re-contarse aquí.

No entrenar en \(\lambda_L=0.90\) ni \(\lambda_L=1.10\).

---

## 25. Matriz experimental final

Esta es la única matriz necesaria.

| Controlador | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 |
|---|---|---|---|---|---|---|---|---|
| No FFC | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Droop | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| DDPG seed 11 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| DDPG seed 22 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| DDPG seed 33 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

Total evaluación final:

\[
8+8+3(8)=40
\]

simulaciones.

No ampliar esta matriz antes de evaluar el gate.

---

## 26. Figuras y tabla mínimas para paper

### Figura 1 — dinámica representativa

**Escenario — congelado antes de test (revisión externa, ronda 3).** Un
único escenario test representativo. Elegirlo después de ver T1–T8 sería
cherry-picking gráfico aunque el análisis cuantitativo (Fig. 2, Tabla 1) sea
correcto — se congela ahora, con un criterio ajeno al desempeño:

```text
FIG1_SCENARIO = T1
FIG1_SCENARIO_FROZEN_BEFORE_TEST = TRUE
```

T1 se elige porque combina generador no visto (\(G_A\)), operating point
nominal y perturbación de generación — el escenario más directamente
alineado con la distribución de entrenamiento pero en una ubicación no
vista, sin depender de qué escenario "se vea mejor" para ningún controlador.

**Seed representativa — congelada antes de test (revisión externa).** La
"seed representativa" de DDPG para la Figura 1 se define y congela **antes**
de abrir T1–T8, usando el mismo \(J_{val}\) de §17.1/§20 evaluado en V1–V4:

\[
s_{rep}=\text{seed con el }J_{val}\text{ mediano entre \{11, 22, 33\}}
\]

```text
REPRESENTATIVE_SEED = ...
REPRESENTATIVE_SEED_FROZEN_BEFORE_TEST = TRUE
```

No elegir posteriormente la trayectoria DDPG que "se vea mejor" en el
escenario de la Figura 1.

**Artefacto de trayectorias (excepción acotada a "un CSV consolidado",
revisión externa).** `ffc_results.csv` (§29) solo contiene métricas
escalares y no puede reconstruir \(f(t)\), \(RoCoF(t)\), \(P_{BESS1}(t)\),
\(P_{BESS2}(t)\) para el escenario de la Figura 1. Se autoriza exactamente un
artefacto adicional, mínimo y acotado a este propósito:

```text
Paper_1/artifacts/trajectories/fig1_case.npz
```

conteniendo solamente `time`, `controller`, `seed`, las trayectorias de
`BusFreq`/`BusROCOF` en los 10 buses de generación, y `P_BESS1`/`P_BESS2`,
para No FFC, Droop y DDPG (\(s_{rep}\)) en el escenario elegido para la
Figura 1. No es un CSV de métricas adicional (no viola §27/§29) y no requiere
guardar trayectorias de los demás escenarios T1–T8.

Tres paneles:

1. **envelope de frecuencia**: banda min–max de \(f_i(t)\) entre los 10
   generadores en cada instante (no una sola "unidad", ya que la peor unidad
   puede cambiar durante el transitorio);
2. RoCoF (misma convención de envelope);
3. potencia de BESS1 y BESS2.

Mostrar:

- No FFC;
- Droop;
- DDPG, seed \(s_{rep}\) congelada arriba.

### Figura 2 — evidencia agregada

Dos paneles:

#### (a)

Mejora de nadir DDPG vs droop para T1–T8.

#### (b)

Mejora de RoCoF DDPG vs droop para T1–T8.

Mostrar tres seeds discretamente y mediana claramente.

Si H2 resulta soportada, añadir en esta misma figura un pequeño panel de:

\[
E_{DDPG}/E_{droop}
\]

No crear otra figura únicamente para energía.

### Tabla 1

Filas T1–T8.

Columnas mínimas:

```text
scenario
controller
f_nadir
RoCoF_max
P_peak
E_BESS
saturation
```

No crear tablas adicionales mientras esta tabla responda las hipótesis.

---

## 27. Estructura mínima de archivos

Reutilizar archivos STED existentes si ya existen.

No duplicarlos.

**Árbol corregido para coincidir con la estructura real ya creada bajo
`Paper_1/`** (ver DEC-020/DEC-021 en `ops/sted/decision_log.md` de la raíz):
la estructura original de este documento (`Paper_1/plan_maestro.md`,
`scripts/`, `results/`, `models/` planos) no coincide con el `Paper_1/` que
ya existe (`cases/`, `src/`, `experiments/`, `artifacts/`, `paper/`). Se usa
la estructura real:

```text
Paper_1/
│
├── README.md
├── plan_maestro_DDPG_FFC_IEEE39_ANDES.md      (este documento)
│
├── cases/ieee39/
│   ├── base/ieee39_full.xlsx                   (congelado, no tocar)
│   └── variants/ieee39_low_inertia.xlsx
│
├── src/
│   ├── run_ffc_study.py
│   └── plot_ffc.py
│
├── experiments/
│
├── artifacts/
│   ├── metrics/ffc_results.csv
│   ├── models/
│   │   ├── ddpg_seed11.zip
│   │   ├── ddpg_seed22.zip
│   │   └── ddpg_seed33.zip
│   ├── trajectories/
│   │   └── fig1_case.npz          (única excepción acotada, ver §26)
│   ├── figures/
│   └── tables/
│
├── paper/
│
└── ops/
    └── sted/
        ├── traceability_matrix.csv
        ├── test_plan.md
        └── decision_log.md
```

**Regla de registro (importante):** todo lo que este documento pedía escribir
en `plan_maestro.md` (§5.3, §7.3, §34) se registra en
**`Paper_1/ops/sted/decision_log.md`**, nunca en el `plan_maestro.md` de la
raíz del repositorio — ese archivo gobierna el paper Wide-Area Control (Gate
G1) y `ops/checks/session_boot.py` extrae de él el gate activo del
repositorio completo (ver nota al inicio de este documento).

No crear:

```text
placement_report.md
training_report.md
validation_report.md
hyperparameter_report.md
seed_report.md
scenario_*.csv
episode_*.csv
metrics_*.csv
```

Toda la evidencia numérica debe entrar en:

```text
ffc_results.csv
```

La única excepción es `Paper_1/artifacts/trajectories/fig1_case.npz` (§26),
necesaria porque las métricas escalares de `ffc_results.csv` no pueden
reconstruir la dinámica temporal de la Figura 1.

---

## 28. Responsabilidad de `run_ffc_study.py`

Un solo script debe ejecutar mediante subcomandos o flags:

```text
--stage inspect
--stage build-case
--stage low-inertia
--stage placement
--stage tune-droop
--stage benchmark
--stage train
--stage validate
--stage test
```

`build-case` (nueva, verificada como necesaria) construye el `System` con
`andes.load(..., setup=False)`, añade los `PV`+`ESD1` de los BESS y los
`BusROCOF` requeridos (§6.1, §7.2, §14), y solo entonces llama `ss.setup()` —
requisito de ANDES 2.0.0, no opcional (`System.add()` falla después de
`setup()`). `benchmark` (nueva) ejecuta el gate de factibilidad computacional
de §20.0.

Debe contener la lógica para:

- localizar caso IEEE-39 stock;
- generar la copia low-inertia (solo generadores del área, buses 30–38);
- construir el `System` con dispositivos BESS y `BusROCOF` antes de `setup()`;
- comprobar PFlow/TDS/EIG;
- identificar generators;
- construir train/validation/test split;
- seleccionar ubicación BESS;
- dimensionar BESS;
- reconfigurar `PQ.config` a potencia constante para los buses de escalón de carga;
- crear el entorno ANDES/Gymnasium (`andes.rl.AndesEnv`, con bounds finitos);
- ejecutar No-FFC;
- ajustar droop;
- cronometrar y proyectar el presupuesto de entrenamiento (`benchmark`);
- entrenar DDPG;
- evaluar;
- calcular métricas;
- escribir resultados consolidados.

No crear un script independiente por fase.

---

## 29. `ffc_results.csv`

Una fila por:

```text
phase × controller × seed × scenario
```

Columnas mínimas:

```csv
phase,
scenario,
controller,
seed,
disturbance_type,
disturbance_bus,
disturbance_mw,
op_scale,
inertia_scope,
inertia_k,
h_total_s,
load_model,
rocof_Tr_s,
bess_bus_1,
bess_bus_2,
bess_pmax_mw,
f_nadir_hz,
rocof_max_hz_s,
p_peak_mw,
energy_mwh,
energy_mj,
soc_excursion,
saturation_fraction,
tds_success,
validation_score
```

`inertia_scope` documenta que la inercia se escaló solo en el área (buses
30–38, ver §5.2); `h_total_s` registra la inercia total del sistema
resultante (incluye el equivalente del bus 39 sin escalar), calculada a
partir de `GENROU.M.v` en base de sistema (T17); `load_model` registra
`constZ`/`constP` (ver §12.2 — tras la corrección de esta ronda, debe ser
`constP` de forma idéntica en todas las filas de fases experimentales; T19
protege esta invariante); `energy_mj` complementa
`energy_mwh` porque el throughput por episodio (\(t_f=6\,s\)) es del orden de
decenas de MWh × 10⁻³, poco legible en MWh; `soc_excursion` verifica que el
SoC de `ESD1` permanece no vinculante (§6.4).

Puede contener también filas de placement y tuning droop usando `phase`.

No generar CSV secundarios.

---

## 30. Tests indispensables

| ID | Test | Aceptación |
|---|---|---|
| T01 | IEEE39 stock | PFlow y TDS convergen |
| T02 | low-inertia | PFlow, TDS y EIG válidos |
| T03 | reproducibilidad | mismo escenario + mismo controller produce misma trayectoria determinista |
| T04 | BESS limits | ninguna acción supera límites |
| T05 | placement freeze | buses se seleccionan antes de training |
| T06 | split freeze | test generators nunca aparecen en train/validation |
| T07 | OP leakage | ±10% nunca aparece antes de test |
| T08 | droop freeze | \(K_d\) elegido solo con V1–V4 |
| T09 | DDPG selection | checkpoint elegido solo con V1–V4 |
| T10 | seed independence | seeds 11, 22 y 33 realmente independientes |
| T11 | consolidated results | toda métrica final está en `ffc_results.csv` |
| T12 | primary gate | evaluación automática de 6/8 (P1-H1) |
| T13 | robustness gate | evaluación automática de 3/4 (P1-H3) |
| T14 | droop interno desactivado | `ESD1.ddn=0.0` verificado en los tres controladores; "No FFC" no produce respuesta a frecuencia, "Droop" no tiene ganancia duplicada |
| T15 | load step efectivo | tras fijar `PQ.config.p2p=1`, el escalón en `Ppf` produce cambio medible en la trayectoria (no un no-op silencioso) |
| T16 | SoC no vinculante | excursión de SoC de `ESD1` dentro de `[SOCmin,SOCmax]` sin saturar en ningún escenario T1–T8 |
| T17 | consistencia de base de inercia | \(H_{total}\) y la contribución de cada máquina se calculan exclusivamente a partir de `GENROU.M.v` (base de sistema, 100 MVA), nunca de `M.vin` (base de máquina); protege las cifras de §5.2/§5.3 |
| T18 | mecanismo único de pérdida de generación | solo existe un dispositivo `Alter` activo sobre `paux0` por generador de entrenamiento; ningún `Toggle`/`Toggler` ni escritura directa de `pref0` coexiste como camino alternativo (§10) |
| T19 | modelo de carga idéntico entre fases | `PQ.config` (potencia constante, §12.2) es el mismo en training, validation y en los ocho escenarios de test — ninguna fase corre con `PQ` en impedancia constante mientras otra corre en potencia constante |

No escribir tests que no protejan directamente estos puntos.

---

## 31. Orden obligatorio de ejecución

**Nota de nomenclatura:** las etapas se identifican `P1-E0`…`P1-E7`
(`E`=execution), en vez de `G0`…`G7` como en la versión original, para no
colisionar con los gates STED-RW de la raíz del repositorio
(`ops/checks/session_boot.py` busca `\bG[0-4]\b` en `plan_maestro.md`,
`README.md` y `final_quality_report.md` de la raíz — un `G0`–`G4` de
`Paper_1` filtrado a esos archivos produciría una falsa `DISCREPANCIA`, como
ya ocurrió una vez en esta sesión). `LI-1` (§5.3) no colisiona con ese patrón
y se mantiene sin cambio.

### P1-E0 — inspección

Codex debe:

1. identificar la versión instalada de ANDES;
2. localizar el caso IEEE-39;
3. listar modelos dinámicos;
4. comprobar qué modelo nativo utilizará para BESS/IBR (`ESD1`, ya decidido
   en §6.1 — confirmar que sigue disponible en la versión instalada);
5. comprobar qué setpoint de potencia activa puede controlar (`Pext0` vía
   `set_paux`, ya verificado);
6. mover este documento a `Paper_1/plan_maestro_DDPG_FFC_IEEE39_ANDES.md`
   (ver nota de ubicación al inicio del documento).

No entrenar nada.

### P1-E1 — caso low-inertia

1. construir el caso con `andes.load(..., setup=False)`; añadir `BusROCOF`
   en los 10 buses de generación (30–39) para reward/métricas system-wide
   (§14/§21, P-1.5) **y, por separado, en todos los buses BESS admisibles
   (1–29, S-04) para el screening de placement de §7.2 Paso A** — son dos
   conjuntos de buses distintos con propósitos distintos, no el mismo (ver
   corrección D3, §0.7: la ronda 2 solo mencionaba 30–39 aquí, lo que
   dejaba sin instrumentar los buses que §7.2 Paso A necesita para calcular
   \(S_b\)); aplicar `PQ.config` a potencia constante (§12.2, aplicado aquí
   y no solo en T5–T8) y solo entonces `setup()`;
2. escalar inercia (§5.2, solo `GENROU_1`…`GENROU_9`), con \(k=0.50\) como
   primer valor de la escalera (§5.3) y usando `M.v` en base de sistema
   para toda cifra reportada (T17);
3. validar (Gate LI-1, §5.3, escalera \(k\in\{0.50,0.30\}\), incluye el
   criterio 5 de horizonte de P-1.6);
4. congelar.

No instalar BESS todavía si el caso low-inertia no es válido.

### P1-E2 — BESS y ubicación

1. dimensionar (§6.2);
2. ejecutar el Paso A de §7.2 sobre los buses BESS admisibles (1–29, S-04),
   usando los `BusROCOF` ya instalados ahí en P1-E1 y las dos pérdidas de
   generación de diseño; calcular \(S_b\) y seleccionar los cuatro
   candidatos (este paso estaba implícito y sin secuenciar en versiones
   anteriores — ver corrección D3, §0.7);
3. añadir `PV`+`ESD1` (con `ddn=0.0` fijado, §6.1) en esos cuatro candidatos
   (ya instrumentados con `BusROCOF` desde el paso anterior);
4. evaluar seis pares (§7.2 Paso B);
5. seleccionar dos buses;
6. congelar buses en `Paper_1/ops/sted/decision_log.md` (§7.3).

### P1-E3 — particiones

Congelar en `Paper_1/ops/sted/decision_log.md`:

```text
G_train
G_validation
G_A
G_B
L_A
L_B
```

y operating points (incluye la regla de redespacho proporcional de §9).

### P1-E4 — baselines

1. No FFC;
2. tune droop solo con validation;
3. freeze droop.

### P1-E4.5 — benchmark de cómputo (§20.0)

Cronometrar 10 episodios, proyectar a 24 000, ajustar presupuesto si es
necesario, registrar la decisión antes de continuar a P1-E5.

### P1-E5 — DDPG

Entrenar seeds:

```text
11
22
33
```

Guardar solo mejor checkpoint de cada una según validation, usando el mismo
\(J_{val}\) de §17.1/§20 (no un criterio distinto al de droop). Congelar la
seed representativa y el escenario de la Figura 1 (§26: mediana de
\(J_{val}\) y `FIG1_SCENARIO = T1`) antes de abrir P1-E6.

### P1-E6 — test único

Ejecutar T1–T8 una sola vez por estrategia.

Después del primer acceso a T1–T8:

> queda prohibido modificar reward, arquitectura, buses, BESS, droop, hiperparámetros o training distribution.

### P1-E7 — figuras

Generar Fig. 1, Fig. 2 y Tabla 1 exclusivamente desde `ffc_results.csv` y las trayectorias necesarias para la única figura dinámica.

---

## 32. Reglas de stop

### STOP-A

Si el IEEE-39 low-inertia no puede estabilizarse razonablemente, o no produce
perturbación de frecuencia relevante, con \(k=0.50\) ni \(k=0.30\) (ver §5.3,
techo de reducción del 33.9 % dado por el equivalente del bus 39):

> detener y **escalar la decisión al usuario** (no solo "reportar bloqueo"):
> presentar las opciones registradas en §5.3 (de-ratear también el
> equivalente del bus 39, o reencuadrar el estudio).

No seguir bajando \(k\) por debajo de 0.30 sin esa decisión explícita.

### STOP-B

Si ninguno de los modelos nativos de ANDES permite una representación razonable del actuador BESS/IBR:

> detener antes de crear un modelo complejo y solicitar decisión.

### STOP-C

Si DDPG falla en las tres seeds:

Se permite **una única ronda de diagnóstico**.

Solo pueden corregirse:

- error de normalización;
- error de signo;
- error de reward;
- error de acción/setpoint;
- bug de reset;
- bug numérico.

No hacer hyperparameter optimization exploratoria.

### STOP-D

Si DDPG no cumple P1-H1 en test:

> conservar resultado negativo.

No crear escenarios adicionales favorables.

---

## 33. Claims permitidos después de los experimentos

### Si P1-H1 pasa

Puede afirmarse:

> Under the evaluated unseen disturbances and operating points, the DDPG-based FFC consistently improved the frequency nadir and maximum RoCoF relative to the tuned droop baseline in the majority of test scenarios.

### Si además H2 pasa

Puede afirmarse:

> At frequency-security performance at least as good as the tuned droop baseline (nadir and RoCoF not worse), the learned policy achieved the improvement without increasing BESS control effort and, in the evaluated scenarios, required lower energy throughput and/or peak power.

### Si P1-H3 pasa

Puede afirmarse:

> The learned policy retained its relative advantage under ±10% unseen operating-point deviations.

### Nunca afirmar

- stability guaranteed;
- universally robust;
- optimal controller;
- best FFC approach;
- deployment ready;
- superior to MPC;
- superior to TD3/SAC;
- generalizes to arbitrary contingencies.

---

## 34. Trazabilidad mínima STED-RW

El proyecto debe reutilizar, si ya existen:

```text
Paper_1/plan_maestro_DDPG_FFC_IEEE39_ANDES.md   (este documento — NO "plan_maestro.md")
Paper_1/ops/sted/traceability_matrix.csv
Paper_1/ops/sted/test_plan.md
Paper_1/ops/sted/decision_log.md
```

**`plan_maestro.md`, sin prefijo, está reservado al contrato del paper
Wide-Area Control en la raíz del repositorio.** No crear un archivo con ese
nombre exacto dentro de `Paper_1/` — usar siempre el nombre completo de este
documento.

### 34.1 Claims mínimos a registrar

| ID | Claim | Evidencia requerida | Gate |
|---|---|---|---|
| CLM-H1 | DDPG mejora simultáneamente nadir y RoCoF frente a droop en mayoría de test | T1–T8, 3 seeds | P1-E6 |
| CLM-H2 | DDPG logra seguridad igual o mejor que droop (nadir y RoCoF no peores) con igual/menor esfuerzo energético (dominancia Pareto, §23) | energía y \(P_{peak}\) en escenarios donde DDPG domina en seguridad | P1-E6 |
| CLM-H3 | DDPG mantiene ventaja bajo OP no vistos | T3, T4, T7, T8 | P1-E6 |
| CLM-PLACEMENT | buses BESS se seleccionaron sin test leakage | evidencia de P1-E2 | P1-E2 |
| CLM-FAIR | droop y DDPG usan mismos BESS y límites | configuración congelada | P1-E4–P1-E6 |

### 34.2 Decisiones mínimas a registrar

- escala final de inercia (\(k\), solo buses 30–38, \(H_{total}\) resultante);
- modelo BESS/IBR elegido (`ESD1`, ver §6.1);
- \(P_{max,BESS}\), `En` (capacidad SoC usada);
- buses BESS seleccionados;
- \(G_A\), \(G_B\), \(G_V\), \(\mathcal G_{train}\);
- \(L_A\), \(L_B\), y el modelo de carga usado (`constP` tras §12.2);
- operating points factibles;
- \(K_d\) final;
- checkpoint seleccionado por seed;
- resultado del gate de factibilidad computacional (§20.0).

No crear reportes separados para ninguna de estas decisiones. Todo se
registra en `Paper_1/ops/sted/decision_log.md` (§27) — nunca en el
`plan_maestro.md` de la raíz.

---

## 35. Criterios de calidad final

Antes de considerar terminada la campaña:

- [ ] IEEE-39 stock preservado.
- [ ] Caso low-inertia reproducible.
- [ ] Dos BESS idénticos.
- [ ] Placement congelado antes de training.
- [ ] Train/validation/test sin leakage.
- [ ] Droop sintonizado solo con validation.
- [ ] DDPG entrenado con exactamente 3 seeds.
- [ ] Checkpoints seleccionados solo con validation.
- [ ] Test T1–T8 ejecutado una sola vez por estrategia.
- [ ] No hubo post-test tuning.
- [ ] Todos los resultados finales están en `ffc_results.csv`.
- [ ] H1 fue aceptada, condicionada o rechazada explícitamente.
- [ ] H2 fue aceptada, condicionada o rechazada explícitamente.
- [ ] H3 fue aceptada, condicionada o rechazada explícitamente.
- [ ] No se agregaron escenarios favorables después de ver test.
- [ ] Figuras y tabla final se generan desde evidencia reproducible.
- [ ] Claims escritos no exceden la evidencia.

---

## 36. Instrucción final para Codex

Trabaja bajo STED-RW Lean.

Tu objetivo no es generar muchos resultados. Tu objetivo es producir la **mínima evidencia reproducible necesaria** para aceptar o rechazar H1–H3.

Antes de programar:

1. inspecciona el repositorio;
2. lee **este documento**
   (`Paper_1/plan_maestro_DDPG_FFC_IEEE39_ANDES.md`) — no el `plan_maestro.md`
   de la raíz del repositorio, que gobierna un paper distinto (Wide-Area
   Control, ver nota al inicio de este documento);
3. lee los archivos STED de `Paper_1/ops/sted/` (traceability_matrix.csv,
   test_plan.md, decision_log.md) existentes;
4. reutiliza estructura existente;
5. no sobrescribas versiones anteriores;
6. coloca cualquier caso IEEE-39 modificado dentro de `Paper_1`;
7. no crees archivos adicionales salvo que sean indispensables para ejecutar el pipeline;
8. no modifiques `plan_maestro.md`, `README.md`, `CLAUDE.md`, `AGENTS.md` ni
   `ops/sted/` de la raíz del repositorio bajo ninguna circunstancia — esos
   gobiernan el otro paper del repositorio.

Principios obligatorios:

```text
freeze before train
validation before test
same BESS for every controller
same scenarios for every controller
no test leakage
no post-test tuning
no cherry picking
one consolidated CSV
three final DDPG checkpoints only
two final figures + one table
```

Cada gate debe finalizar con:

```text
STATUS:
DECISION:
EVIDENCE:
FROZEN PARAMETERS:
BLOCKERS:
NEXT AUTHORIZED ACTION:
```

No avanzar si el gate anterior está bloqueado.

La prioridad científica es, en este orden:

1. nadir;
2. RoCoF;
3. esfuerzo energético/potencia;
4. robustez frente al operating point.

No optimizar ninguna otra métrica.

---

## 37. Próxima acción autorizada

**Nota:** la inspección técnica de ANDES 2.0.0 y `ieee39_full.xlsx` que
motivó las correcciones de este documento (§5, §6, §7.2, §14, §18) ya se
realizó y está incorporada in situ. Los puntos 1–5 siguientes ya tienen
respuesta conocida (versión 2.0.0, caso `ieee39_full.xlsx`, modelos GENROU/
TGOV1N/IEEEX1/IEEEST/BusFreq, `ESD1` con `Pext0`/`set_paux`). `P1-E0` (renombrado
de "inspect") pasa a ser una etapa de **verificación** de esos hechos contra
el entorno de ejecución real, más la migración del documento, no un
descubrimiento desde cero.

La siguiente acción de Codex debe ser exclusivamente:

```text
--stage inspect
```

y debe terminar después de:

1. confirmar versión instalada de ANDES (esperado: 2.0.0; si difiere,
   re-verificar los hallazgos de este documento antes de continuar);
2. confirmar que `Paper_1/cases/ieee39/base/ieee39_full.xlsx` (ya congelado)
   coincide con `andes.get_case('ieee39/ieee39_full.xlsx')`;
3. confirmar los modelos dinámicos listados arriba;
4. confirmar que `ESD1` sigue disponible y con la API `Pext0`/`set_paux`
   documentada en §6.1;
5. confirmar que el setpoint de potencia activa puede modificarse durante
   TDS con el mecanismo de §6.1;
6. mover este documento a `Paper_1/plan_maestro_DDPG_FFC_IEEE39_ANDES.md`;
7. reportar blockers si los hay (cualquier discrepancia con los hallazgos
   verificados de este documento es un blocker que debe resolverse antes de
   P1-E1, no ignorarse).

**No entrenar DDPG, no modificar inercia y no seleccionar buses BESS antes de aprobar P1-E0.**

---

**Fin del plan maestro.**
