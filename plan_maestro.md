# Plan maestro experimental progresivo — ANDES / IEEE 39 / SG–GFM–GFL / CLF–HOCBF

**ESTADO DEL PLAN: `E8_APROBADA` (planta C2t, DEC-036; E4.2 congeló C2)**  
**Versión:** 2.0 · **Fecha:** 2026-10-25  
**Repositorio:** `Resilient_distributed_control_PS` · **Manuscrito:** `Paper_manuscript/main.tex`  
**Origen:** revisión de `plan_maestro_experimentacion_progresiva_ANDES.md` (v1) más el adjunto «IEEE 39 barras en ANDES» y la secuencia E0–E15 solicitada.  
**Responsable de aprobación:** investigador; ningún experimento posterior se ejecuta hasta recibir aprobación explícita del anterior.  
**Próxima acción autorizada:** revisión humana de la opción B adoptada (DEC-047: filtro predictivo H = 3 s con cota de error empírica, consistente en S0, sin escenario conocido que lo active y costo 0.52 s en casos perturbados; reducción de alcance con limitaciones verificadas); E10, E13, seguridad en lazo cerrado, sensibilidad de pesos y E9 no autorizados; OPEN-SG31-PMAX (DEC-031) sigue abierta.

> **DECISIÓN DE ALCANCE APROBADA (2026-10-25):** el sistema IEEE de 39 barras es el único banco de pruebas de todo el proceso experimental. Los casos de 10 y 14 buses no forman parte del alcance de validación ni de reproducción. El trabajo de Kavvathas y Konstantopoulos (2025) se conserva como antecedente del controlador RDC y referencia metodológica, sin presentar el IEEE-39 como reproducción de sus casos. Se autoriza la inspección de solo lectura y la etapa E0--C0; ninguna etapa posterior queda autorizada hasta la revisión humana de las gráficas obligatorias de E0.

---

## 0. Principios científicos y operativos innegociables

1. **Avance observable:** al cerrar *cada* etapa dinámica se entregan **dos gráficas obligatorias**, `frecuencia vs tiempo` y `magnitud de voltaje vs tiempo`, más un dictamen automático y uno humano. Si las curvas no son físicamente coherentes, no seguir.
2. **Cambio único por prueba:** una sola sustitución SG→GFM/GFL, un solo lazo adicional, una sola perturbación o un solo grupo explícito de parámetros a la vez. Todos los demás elementos se congelan.
3. **Base del sistema inmutable:** preservar caso original, topología, líneas y transformadores. Crear variantes versionadas **solo dentro de `Paper_manuscript/cases/`**; no editar el archivo base. No sustituir arbitrariamente posiciones de generadores por otros buses.
4. **Mismo preevento para comparar controladores:** dentro de una configuración dada (especialmente C2), congelar despacho AC, modelos primarios, evento, tiempos, filtros y límites. No confundir efecto de cambiar la planta (C0→C2) con el efecto de cambiar el controlador (PI→RDC→HOCBF).
5. **Separación de evidencias:** curvas de TDS prueban comportamiento *numérico del modelo*, EIG prueba *estabilidad lineal local*, y una cota verificada sobre la **región completa** es necesaria para afirmar estabilidad no lineal regional o invariancia certificada.
6. **Modos del inversor:** «sin controles adicionales» significa sin **secundario/terciario ni filtro CLF–HOCBF externo**. Un GFM **no puede** operar sin su control formador interno; REGF1 ya incorpora droop. Comparar activación o sintonía primaria solo después de comprobar su respuesta nativa.
7. **Factibilidad:** si falta capacidad de potencia/energía o el QP resulta infactible, se detiene la garantía; nunca fabricar una restauración ideal por saturación oculta, compensación no modelada o `Slack` ilimitado.
8. **ANDES RMS de secuencia positiva:** no usar resultados de este modelo para afirmar protección de semiconductores en escalas subciclo/EMT; el círculo de potencia aparente no sustituye la curva real de capacidad de un SG. Toda variable declarada «protegida» debe existir y ser observable en el modelo.
9. **Documentación mínima STED-RW Lean:** reutilizar planes, matrices, scripts, registros y carpetas **ya existentes**. No crear un script por etapa, carpetas paralelas ni reportes redundantes.

## 1. Contexto verificable y divergencia con `main.tex`

**Alcance del manuscrito:** el sistema físico se formula como DAE `ẋ=f(x,y,u,d), 0=g(x,y,u,d)`; se amplían referencias `u=(P_set,Q_set)` como estados con comandos `v=du/dt`; se integran RDC, barreras HOCBF sobre salidas físicas, factibilidad de equilibrio, QP coordinado y CLF regional. Toda la validación prevista se realizará sobre el sistema IEEE de 39 barras y sus variantes C0--C3. Los resultados de 39 barras NO deben presentarse como reproducción de los casos ni del hardware HIL del artículo de referencia.

**Datos del adjunto IEEE-39:** propuesta C0 original 10 SG; C1 8 SG + 2 GFM sustituyendo los SG de buses 32 y 37; C2 6 SG + 4 GFM, añadiendo sustituciones en 34 y 36; C3 5 SG + 4 GFM + 1 GFL sustituyendo también 35. Las localizaciones son **hipótesis iniciales**: no están justificadas por un estudio óptimo de emplazamiento. Conservar 30 y 39 como SG es una preferencia de diseño; el bus de referencia real se **determina leyendo el archivo de caso**, no de una generalización sobre IEEE-39.

**Estado real del repositorio:** solo se ha visto su árbol en capturas y se han recibido los archivos de manuscrito y protocolos. **No se han inspeccionado los contenidos reales de `cases/`, `src/` ni la instalación del `venv/`; no hay corridas ni resultados confirmados.** Todo sigue `PENDIENTE`.

### 1.1 Hipótesis experimentales refutables

- **H1 — integridad física y control primario:** cada variante C0→C2 conserva un PFlow viable e inicialización TDS sin deriva artificial; al aplicar escalones moderados, SG/GFM muestran signos y reservas de P/Q coherentes. Refutable por fallo de convergencia, potencias duplicadas, señales no físicas o inestabilidad inesperada.
- **H2 — regulación nominal y reparto:** con equilibrio factible, el secundario coordinado regula frecuencia y objetivos locales/admisibles de tensión y distribuye P/Q conforme a pesos declarados. Refutable por error estacionario, reparto incoherente o violación de límites bajo evento de diseño.
- **H3 — seguridad incremental:** respecto a RDC nominal y PI con las mismas condiciones, HOCBF reduce o evita las violaciones **de salidas físicas modeladas** cuando su QP es factible y se satisfacen hipótesis del certificado. Refutable mediante margen negativo no explicado o fallo de QP en caso declarado certificable.
- **H4 — recuperación y convergencia regional:** con saturación simultánea y perturbación perteneciente al conjunto recuperable certificado, CLF–HOCBF mantiene las restricciones y converge al equilibrio admisible; fuera de él la metodología detecta pérdida de certificado sin afirmar restauración garantizada. Refutable mediante contraejemplo en la región **formalmente verificada**, no mediante el solo fracaso de un caso fuera de hipótesis.

## 2. No modificar la estructura de archivos existente

```text
Resilient_distributed_control_PS/
├── .claude/                   # existente; respetar
├── .codex/                    # existente; respetar
├── AI_TOOLS/                  # existente; respetar
├── ops/                       # existente; protocolos transversales
├── Paper_manuscript/
│   ├── artifacts/             # series crudas, logs, tabla única de resultados
│   ├── cases/                 # caso IEEE-39 original y variantes sin cambiar directorio
│   ├── figures_main/          # figuras obligatorias de cada fase
│   ├── ops/                   # plan y trazabilidad reutilizados
│   ├── references/            # fuentes existentes
│   ├── src/                   # ejecutor parametrizable, modelos de control y tests necesarios
│   ├── main.tex               # NO modificar durante la auditoría / la fase E0
│   ├── references.bib
│   └── README.md
├── venv/                      # NO recrear
├── zPLantilla_STED_RW/        # NO reorganizar
├── AGENTS.md / CLAUDE.md / README.md
└── .gitattributes / .gitignore
```

**Ubicación al integrar:** `Paper_manuscript/ops/plan_experimental_ANDES.md`, **solo si no existe** un plan del artículo equivalente; si existe, fusionar sin borrar contenido y sin duplicar fuentes de verdad. El presente `.md` es un archivo de descarga: **no se ha copiado al repositorio del usuario**.

**Reutilización obligatoria:** `cases` para bases y variantes, `src` para un ejecutor único dirigido por parámetros/casos, `artifacts` para series y matríz consolidada, `figures_main` para gráficos de supervisión, `Paper_manuscript/ops` para el estado de gates y decisiones. No crear directorios `paper/`, `scripts/`, `experiments/` ni `research/` adicionales.

**Convención de salida sin carpetas nuevas** (solo si no existen equivalentes):

```text
Paper_manuscript/cases/ieee39_base_original.xlsx   # nombre ilustrativo, solo si tal archivo no existe
Paper_manuscript/cases/ieee39_C0a_9SG_1GFM.xlsx    # variante reproducible; no tocar base
Paper_manuscript/cases/ieee39_C1_8SG_2GFM.xlsx
Paper_manuscript/cases/ieee39_C1a_7SG_3GFM.xlsx
Paper_manuscript/cases/ieee39_C2_6SG_4GFM.xlsx
Paper_manuscript/cases/ieee39_C3_5SG_4GFM_1GFL.xlsx
Paper_manuscript/figures_main/IEEE39_E01_C0_frequency.png
Paper_manuscript/figures_main/IEEE39_E01_C0_voltage.png
Paper_manuscript/artifacts/IEEE39_E01_C0_timeseries.npz
Paper_manuscript/artifacts/experiment_matrix.csv
```

Las rutas superiores son **patrones de nombre**; no son evidencia de que esos archivos ya existan. Conservar nombres actuales cuando estén disponibles.

## 3. Escalera de redes y sustitución correcta SG → IBR

| Código | SG | GFM | GFL | Sustituciones acumuladas | Uso en etapas |
|---|---:|---:|---:|---|---|
| **C0** | 10 | 0 | 0 | Ninguna | E0–E2, referencia física |
| **C0a** | 9 | 1 | 0 | SG32 → GFM32 | E3, etapa intermedia técnica |
| **C1** | 8 | 2 | 0 | C0a + SG37 → GFM37 | E4, primera red híbrida |
| **C1a** | 7 | 3 | 0 | C1 + SG34 → GFM34 | E4.1, etapa intermedia técnica |
| **C2** | 6 | 4 | 0 | C1a + SG36 → GFM36 | E4.2 y E5–E14; **red principal** |
| **C3** | 5 | 4 | 1 | C2 + SG35 → GFL35 | E15, extensión heterogénea |

**SG que permanecen en C2:** 30, 31, 33, 35, 38, 39.  
**SG que permanecen en C3:** 30, 31, 33, 38, 39.  
**GFM principales:** 32, 34, 36, 37. **GFL principal:** 35.  
**Importante:** los buses indicados son IDs de barras del caso IEEE-39 que debe verificarse, **no** índices internos de los objetos ANDES.

**Procedimiento obligatorio por cada sustitución individual:**

1. Auditar el generador SG original: bus real, identificador `idx`, vínculo al generador estático (`gen`), `P0`, `Q0`, `V0`, `Sn`, governor, AVR, PSS, transformador y conexión a red. Identificar `Slack` de flujo de potencia y máquina de referencia dinámica separadamente. Auditar y desactivar **solo en la variante experimental** cualquier secundario AGC/ACEc previamente incluido cuando el experimento exija «solo control primario», manteniendo los gobernadores, AVR y PSS declarados; conservar intacto el caso stock.
2. Guardar copia reproducible de la configuración anterior; **no borrar líneas, barras ni transformadores**.
3. Deshabilitar el generador dinámico SG sustituido y sus reguladores asociados, evitando inyecciones duplicadas; **no deshabilitar sin criterio el generador estático** que ANDES usa para PFlow e inicialización del recurso dinámico.
4. Vincular nuevo modelo `RenGen` al generador estático correcto mediante `gen` y `bus`. Verificar `Sn` y el reparto de contribuciones (`gammap`, `gammaq` o mecanismo efectivo de la versión) si coexisten dispositivos dinámicos asociados a una fuente estática. La documentación de ANDES advierte que un `Sn` inapropiado puede impedir la inicialización.
5. Preservar, si el nuevo equipo lo permite, **el punto de operación activo inicial**; conservar la demanda total y contabilizar cualquier redistribución de `Q0`, tensión y pérdidas. Nunca suponer iguales los transitorios C0/C2: se eliminó inercia física.
6. Ejecutar **PFlow → TDS.init → TDS sin evento → TDS con ΔP pequeño → TDS con ΔQ pequeño → EIG**; cada subprueba debe conservar f/V. Diagnosticar problemas antes de añadir el siguiente conversor.
7. Verificar potencias **entregadas**, no solo `Pset`. Registrar `P_GFM/Q_GFM`, estados de droop, frecuencia propia interpretable, corriente RMS representada, voltaje del POI, reservas activas/reactivas y si hay limitadores de modelo que cambien el campo vectorial.
8. Definir disponibilidad energética: un GFM respaldado por BESS con reserva puede aumentar potencia activa; una fuente renovable al MPPT sin almacenamiento ni margen activo **no** garantiza potencia adicional. `REGF1` por sí solo no es modelo de SoC. Si se invoca un límite de energía, crear/usar dinámica energética validada antes de la garantía.

**Modelos candidatos documentados en ANDES 2.0.0:** `GENROU` con gobernador/excitatriz para SG; `REGF1` (GFM droop) como candidato principal; `REGF2` (GFM VSM) como comparación secundaria; `REGCA1` asociado a su control eléctrico/planta o `REGCP1` si se modela explícitamente PLL para GFL. No afirmar que `REGCA1` aislado incluye todos los controles externos ni que `REGF1` permite intervenir directamente cualquier `Qset`; verificar API y ecuaciones de la versión instalada. Fuente: https://docs.andes.app/en/stable/reference/models/RenGen.html.

**Riesgo del caso IEEE-39:** algunas variantes presentan un SG equivalente externo con `H` muy superior a las demás máquinas. Antes de reclamar «baja inercia» por número de SG sustituidos, calcular `Σ H_i S_i` y su distribución por bus. El porcentaje de unidades, el porcentaje de generación activa IBR y la reducción de energía cinética síncrona **no son métricas intercambiables**. Si un equivalente domina la inercia, tratar un escenario alternativo con justificación explícita en E15, sin manipular retrospectivamente C0/C2.

La penetración basada en potencia despachada se define como

\[
\eta_{\mathrm{IBR}}^{P}=100\frac{\sum_{i\in\mathrm{IBR}}P_i^{\mathrm{disp}}}{\sum_{i\in\mathrm{IBR}}P_i^{\mathrm{disp}}+\sum_{i\in\mathrm{SG}}P_i^{\mathrm{disp}}}\,[\%].
\]

Reportar por separado potencia instalada, potencia despachada e inercia síncrona retirada.

## 4. Instrumentación común: figura de frecuencia y figura de tensión en CADA gate

**FIG-F (`frequency.png`):** eje `Tiempo [s]`, `Frecuencia [Hz]`; frecuencia nodal medida y filtrada (`BusFreq`) en **4, 21, 32, 34, 36, 37 y 39**, más todas las máquinas SG y frecuencia propia del GFM si la señal existe/está validada. Curvas de peor bus, banda/nominal y marca del evento. `f_COI` solamente para máquinas SG con ponderación correcta `H_i S_i`; no confundir `GENROU.omega` con `BusFreq.f`. Si hay sobrecarga visual: panel de buses críticos **y panel suplemento de los restantes**; todo el conjunto se conserva en series crudas.

**FIG-V (`voltage.png`):** eje `Tiempo [s]`, `Voltaje |V| [pu]`; medir voltaje **en las 39 barras**. Mostrar líneas de buses 4, 21, 32, 34, 36, 37, 39 y trayectorias `V_min(t)`, `V_max(t)`; los restantes en complemento legible. Mostrar bandas de operación acordadas con el caso, no asumir universalmente 0.95–1.05 pu. Si el bus perturbado tiene comportamiento dependiente de topología, no exigir caída de todas las tensiones.

**Cada etapa E0–E15 produce ambas figuras**, incluidas E12–E13 y E14 (más sus diagnósticos físicos), usando **mismo horizonte, filtros y escala en comparaciones pareadas**. Reportar conjunto de barras medido, señales faltantes y motivo; un gráfico generado de señales equivocadas **no** aprueba el gate.

**Paneles complementarios por fase:**

| Panel | Variables y objeto de inspección |
|---|---|
| `PQ` | `P_i(t), Q_i(t)` reales; `Pset_i/Qset_i` vs entregadas; reparto, tendencia y potencia total |
| `CAP` | curvas de capacidad SG validadas, `P²+Q²≤Smax²` de GFM si procede, corrientes, márgenes `h_cap,h_S,h_I,h_P±,h_V±` |
| `QP` | `v_nom`, `v_QP`, restricciones activas, residuos del solver, tiempo de cómputo, eventos `INFEASIBLE` |
| `LYAP` | `𝒱(t)`, `𝒱̇(t)+λ𝒱(t)`, umbral `ρ`, cumplimiento dentro/fuera de `Ωρ` |
| `EIG` | polos linealizados de la DAE reducida; amortiguamiento y participación modal **solo local** |
| `DISPATCH` | costos declarados, potencias pre/post terciario, nuevas referencias y restricciones |

**Unidades:** identificar la frecuencia nominal en el *archivo real* IEEE-39 (comúnmente 60 Hz, pero pendiente de verificación en el caso efectivo). `BusFreq.f` es por unidad, no Hz; multiplicar por `f_base`, verificando la variable usada y filtros. En ANDES 2.0.0 `BusFreq.fn` tiene por defecto 60 Hz: configurarlo acorde con el caso. `BusROCOF` requiere igual caracterización, y no debe derivarse RoCoF de una frecuencia con filtro distinto al usado para el control.

## 5. Secuencia obligatoria E0–E15: experimentación supervisada

La siguiente tabla es **el orden normativo**. En E4 se ejecutan además E4.1 y E4.2 antes de E5, porque C2 necesita cuatro GFM; no se salta directamente de dos a cuatro. `+P` y `+Q` son eventos independientes. Las cifras de carga se congelan **después** de comprobar reservas y la dinámica base.

| Etapa | Configuración | Experimento/único cambio | Lo que deben revelar las gráficas f(t) y V(t) | Regla de paso (además del panel común) |
|---|---|---|---|---|
| **E0** | C0: 10SG | Sistema sin perturbaciones y prueba instrumental | f prácticamente nominal; V constante en cada bus (no necesariamente 1 pu) | PFlow/TDS convergen, sin deriva numérica, topología y potencias verificadas |
| **E1** | C0 | Incremento moderado **solo P de carga** | f cae, gobernadores responden y se alcanza nuevo equilibrio; V responde coherentemente | Signos correctos, sin eventos invisibles ni inestabilidad; `P_m` y `P_e` físicamente consistentes |
| **E2** | C0 | Incremento **solo Q de carga** | V local cambia y AVR reacciona; f puede presentar acoplamiento transitorio pero no se exige respuesta solo de f | `Q_g`, excitación y tensiones verificadas; sin desbordar límites inicialmente elegidos |
| **E3** | C0a: 9SG+1GFM | Reemplazar exclusivamente SG32 por **GFM32**; sin secundario externo | Flat run del nuevo equilibrio y respuesta pequeña ±P/±Q sin oscilación numérica | P/Q/V originales compatibles, GFM realmente inyecta, sin doble SG+GFM y con reserva plausible |
| **E4** | C1: 8SG+2GFM | Reemplazar SG37 por **GFM37** | Ambos GFM participan; f/V coherentes frente a E3 | Inicialización, flat, cargas P/Q y EIG repetidos y aceptados |
| **E4.1** | C1a: 7SG+3GFM | Reemplazar SG34 por **GFM34**, **un recurso por prueba** | Inestabilidades/resonancias identificables en etapa concreta | Gate independiente con FIG-F, FIG-V y análisis modal local |
| **E4.2** | C2: 6SG+4GFM | Reemplazar SG36 por **GFM36**; congelar caso científico C2 | Red de cuatro GFM y seis SG estable sin externo secundario; f/V medibles | C2 supera PFlow/TDS/EIG, pruebas separadas P/Q, capacidad y despachos auditados |
| **E5** | C2 | Ajuste/contraste de **primario P–f y Q–V** sin secundario; probar cada canal por separado | Desviación de f acorde a droop, Q y V coherentes; distribución entre SG y GFM | Medir pendientes, tiempos, RoCoF, actuación y ausencia de saturación no reportada |
| **E6** | C2 | Activar **secundario convencional PI/consenso** de referencia; primaria idéntica | f converge a nominal solo si factible; V sin deterioro indebido | Mandos `Pset/Vref/Qref` probados efectivamente, error estacionario especificado |
| **E7** | C2 | Activar **secundario P/Q coordinado** | f restaurada y tensión/compartición de Q compatibles con objetivos; P/Q proporcionales a pesos | Error de reparto y objetivos de voltaje definidos; comunicación y actuadores probados |
| **E8** | C2 | Sustituir secundario por **RDC original con restricciones de referencia** y ejecutar `v_nom` centrado como variante separada | f/V recuperan equilibrio factible; referencias permanecen en dominio original | Separar RDC original puro vs centrado; verificar `g_P/g_Q` y fronteras, no atribuir seguridad de salida física |
| **E9** | C2 | Añadir **HOCBF de seguridad**, CLF apagada; QP sobre tasas reales `v=du/dt` | f/V y márgenes muestran reducción/eliminación de violaciones modeladas en casos factibles | Diagnóstico de grados relativos, QP viable, `min h≥−tol`; no prometer seguridad de barreras no modeladas |
| **E10** | C2 | Activar **CLF–HOCBF–QP completo** | f/V muestran recuperación y `𝒱` decrece hacia equilibrio factible en trayectorias de prueba | `𝒱̇+λ𝒱≤tol`, QP viable; llamar evidencia *numérica* hasta certificar región |
| **E11** | C2 | Forzar **dos límites simultáneos** de unidades diferentes, con reserva colectiva factible | f/V se recuperan si hay capacidad; otras unidades asumen P/Q adicional | Identificar dispositivos saturados y redistribución física sin violaciones en región certificada |
| **E12** | C2 | Incrementar déficit hasta probar **frontera de factibilidad** | Curvas muestran pérdida de restauración donde es físicamente imposible; sin ‘retorno mágico’ | Distinguir (i) equilibrio inexistente, (ii) existe equilibrio pero fuera de región certificada, (iii) QP local infactible |
| **E13** | C2 | Verificar **estabilidad regional** por análisis analítico/intervalar + perturbaciones iniciales | Simulaciones dentro/fuera de `Ωρ` concuerdan con la prueba; evolución de V y f | Certificado válido para región **completa**, regularidad DAE y compatibilidad de QP; si no, `NO_CERTIFICADO` |
| **E14** | C2 | Añadir **despacho terciario lento** como cambio de equilibrio objetivo | f/V experimentan transitorio y convergen al nuevo equilibrio, sin saltos no modelados | Recalcular factibilidad/certificado después del redespacho; no heredar `Ωρ` anterior |
| **E15** | C2 y C3 | **Robustez**: incertidumbres, retardos, N−1 seleccionada; luego SG35→GFL35 y repetir gates físicos | f/V permiten aislar pérdida de desempeño y acoplamiento SG/GFM/GFL | C3 primero pasa flat/P/Q/EIG sin seguridad; distinguir casos formalmente cubiertos y no certificados |

**Lectura estricta de E4.1 y E4.2:** son *subetapas técnicas necesarias* para la secuencia solicitada, no experimentos adicionales que violen la economía del plan. En C3, incorporar primero el GFL sin control secundario, **repetir E0/E1/E2 equivalentes para C3**, y solo después probar las políticas ya implementadas; nunca introducir al mismo tiempo un nuevo PLL y un nuevo QP.

### 5.1 Definición operacional y posibles perturbaciones

- Evento inicial estándar propuesto: `t_event=5 s`; simulación inicial `0–30 s` para respuesta SG/GFM si no hay razones numéricas para modificar. La duración se adapta **antes** de comparaciones finales para captar el régimen de secundario/terciario (estos operan más lentamente). Los tiempos son **provisionales**, no resultados.
- E1 C0: comenzar con `ΔP_load≈1%` de la demanda total como prueba de sensibilidad, después `2%` y `5%` si la red permanece operable; no interpretar automáticamente un 5% de carga como «+100 MW» sin comprobar la demanda real.
- E2 C0: comenzar con `ΔQ_load≈1%` de Q cargado, después `2%` o una carga en MVAr físicamente equivalente; no añadir `ΔP` en el mismo test.
- Para C2 y comparaciones finales, **S1 propuesto por el adjunto**: `ΔP_load=+100 MW` en **bus 4**, prueba separada `ΔQ_load=+50 MVAr` en **bus 21**. Estos puntos y amplitudes se admiten **solo después de verificar que ambos buses admiten la perturbación y que reserva/voltajes/base del caso hacen el evento significativo y no triviales los resultados**. Si no, detener y definir una alternativa documentada predeclarada, no ajustar post hoc para favorecer un controlador.
- Para saturaciones, no reducir nominal `Sn` ni inventar límites hasta conseguir fallos. Definir `Smax`, `Pmax`, `Qmax`, corriente, `Pmin`, energía/SoC (si se modela) según tecnología plausible, despacho y reserva; fijar límites **antes** de comparar estrategias.
- Línea N−1: determinar por screening un ramal no radial y cuyo disparo preserve el problema matemático contemplado; documentar cuándo la topología/isla invalida la hipótesis del certificado. Fault/Toggle/Alter preexistentes se inventarían y desactivarían en las variantes si no pertenecen al escenario actual.

### 5.2 Pruebas atómicas antes de activar E9/E10

**Prueba A (entradas):** ante un pequeño cambio de `Pset` de SG/GFM, `P_real` responde con signo correcto, retardo/plausibilidad física; ante `Qset` comprobar interfaz real a excitatriz SG (`Vref` o la que corresponda) y Q/V del GFM. En ningún caso asumir que editar `PV.p0` durante TDS controla la potencia de una `GENROU` activa. ANDES documenta TDS multietapas para variar referencias: https://docs.andes.app/en/stable/tutorials/10-dynamic-control.html.

**Prueba B (salidas físicas):** extraer por dispositivo `P`, `Q`, `|I|` representada, `|V|`; contrastar con balances AC; diferenciar `u=(Pset,Qset)` de salidas `(P,Q)`. Marcar `UNMODELED` para la curva SG, corriente de convertidor o capacidad dinámica que el modelo no represente.

**Prueba C (reducción DAE):** verificar fijación de referencia angular y ausencia de singularidad de `g_y` en región contemplada; validar jacobianos y coherencia de estado modelo ANDES vs modelo teórico reducido.

**Prueba D (HOCBF):** determinar grado relativo de cada `h_j` sobre dinámica reducida aumentada, construir recursión de barrera, verificar signo/residual de todas las desigualdades y factibilidad del QP frente a límites `v_min≤v≤v_max`. No suponer grado relativo 1 para todos los límites físicos.

**Prueba E (CLF):** estabilizabilidad de `(A*,G)`; obtener `H≻0` de LMI coherente con ganancia fija o síntesis adecuada; calcular `𝒱` y derivada del **campo no lineal real**. Comprobar compatibilidad CLF/HOCBF **sobre toda** `Ωρ`, no en una malla finita únicamente.

**Prueba F (muestreo y cambios de modo):** el QP continuo y su certificado no implican automáticamente seguridad entre instantes de control o durante bloqueos/limitación de estados del REGF1. Con muestreo, necesitar cotas robustas de discretización y tratamiento separado de modos híbridos si se pretende una garantía.

## 6. Matriz mínima de escenarios finales (no multiplicar innecesariamente simulaciones)

| Escenario | Red | Intervención | Baselines necesarios | Evidencia científica |
|---|---|---|---|---|
| **S0** | C0→C0a→C1→C1a→C2→C3 | Flat, ΔP pequeño y ΔQ pequeño tras cada sustitución | Mismo caso sin secundario externo | Correcta integración e inicialización |
| **S1** | C2 | +100 MW bus 4, +50 MVAr bus 21 **en corridas distintas y condicionados a factibilidad** | Primario, PI, RDC, CLF–HOCBF | f/V, reparto y recuperación nominal |
| **S2** | C2 | Evento que activa límite físico modelado | PI con saturación, RDC original, RDC+HOCBF, completo | Valor incremental del safety filter |
| **S3** | C2 | GFM32 y GFM37 cerca de fronteras y demanda adicional | RDC, HOCBF, completo | Saturación doble y redistribución de SG/GFM restantes |
| **S4** | C2 | Barrido incremental de déficit cercano a frontera de equilibrio/recuperabilidad | RDC, completo y detector de factibilidad | Separación de restauración posible/imposible |
| **S5** | C2→C3 | Condiciones iniciales, N−1, variación de parámetros y SG35→GFL | RDC y completo, con primarios congelados | Robustez y alcance condicionado |

**Comparación interna del C2:** etiquetas inmutables `B0` sin secundario (solo primarios); `B1` PI/consenso; `B2` RDC original; `B3` RDC centrado si distinto; `B4` RDC + HOCBF; `B5` CLF–HOCBF completo. En el caso de una variante `PI` con saturaciones independientes, designarla `B1s`. La referencia original y la acción centrada no deben fusionarse como si fueran el mismo algoritmo.

**Grafo de comunicación:** antes de E7, inventariar la topología física y definir, justificar y congelar un grafo **cibernético conectado** para las unidades participantes del C2, con matriz de adyacencia simétrica y pesos explícitos. La matriz del artículo 10/14 no debe trasplantarse a 10 unidades sin redefinir y verificar conectividad, observabilidad, pérdida de vecinos y los términos Laplacianos `L_P/L_Q`. Comparar alternativas de comunicación solo como escenario de robustez, no durante la puesta en marcha de E7.

**GFL de C3:** el `main.tex` actual define formalmente SG + GFM, **no** GFL como tercera clase con su dinámica/entradas en CLF–HOCBF. Usar GFL35 como fuente exógena controlada bajo sus propios límites o ampliar explícitamente el modelo y la prueba antes de reclamar en C3 las garantías teóricas de C2. No enviar órdenes de droop GFM a un modelo GFL por semejanza de nombre de señal.

**No ejecutar todas las combinaciones** `C0–C3 × E0–E15 × B0–B5`: ejecutar únicamente celdas que desbloquean un gate o comprueban H1–H4. C2 es el sistema experimental principal, C0–C1 sirven para control de integración y C3 para generalización técnica.

## 7. Métricas y criterios de aceptación por puerta

**Se define por corrida**, con datos brutos antes de filtros/gráficas: `f_nadir`, `f_zenith`, `max|RoCoF|`, error de frecuencia a régimen, tiempo de establecimiento, `V_min/V_max`, tiempo de violación de tensión, `P_i/Q_i`, error de reparto ponderado, márgenes `min h_j`, tiempo de restricción activa, número y tiempo de QP infactible, `𝒱`/derivada, energía BESS si está modelada, residuales DAE, eigenvalores, tiempo de CPU y resoluciones numéricas.

| Gate | Criterio previo a aprobación | Condición de fallo/bloqueo |
|---|---|---|
| **AC-00 PFlow** | PFlow converge; dispositivos y buses esperados; balance `ΣPgen−ΣPload−P_loss≈0` con tolerancia registrada; ninguna inyección duplicada | PFlow falla, potencia fantasma, `Sn` incoherente |
| **AC-01 flat** | TDS inicializada y `f,V` sin deriva más allá de tolerancia numérica prefijada; diagnóstico inicial propuesto `max|Δf|≤0.005 Hz`, `max|V(t)−V(0)|≤10⁻³ pu` en 10 s **solo como umbrales de depuración** | Deriva, NaN, solver no converge |
| **AC-02 excitación física** | ΔP de carga causa déficit con signo correcto, governor responde; ΔQ separado produce variación local de tensión y acción de AVR | Señal invertida, perturbación mal aplicada, controlador oculto |
| **AC-03 cambio de modelo** | SG sustituido inactivo, IBR correcto, carga y predespacho justificados; PFlow/flat/EIG y P/Q validados | Dos generadores dinámicos aportan potencia por error o IBR no responde |
| **AC-04 numérico** | Comparación entre pasos `Δt` y `Δt/2` y tolerancias TDS documenta convergencia de nadir/extremos; tolerancia provisional: 1% en nadir significativo, 0.005 pu en V, 5% RoCoF | Resultado depende notablemente del paso/filtrado |
| **AC-05 secundario** | Si existe equilibrio admisible, `|f_final−f_nom|≤0.01 Hz` provisional y reparto dentro de tolerancias fijadas antes de la campaña | No restaura, solo actúa una fuente, las potencias saturan sin aviso |
| **AC-06 seguridad** | `h_j≥−tol_j` por todas las señales modeladas en la trayectoria y QP factible; comprobar efecto de muestreo | Violación física en región presuntamente garantizada o QP infeasible oculto |
| **AC-07 CLF** | `𝒱(t)≥0`, `𝒱̇(t)+λ𝒱(t)≤tol_CLF` en trayectorias ensayadas y validación del subnivel `Ωρ` | `𝒱` crece en dominio declarado certificado |
| **AC-08 certificado** | Cota rigurosa de no vaciedad del QP en **todo** `Ωρ`, DAE regular, región `ρ>0`, hipótesis de modo/sampling satisfechas | Resultado solo por muestreo, eigenvalores, Monte Carlo o solver local ⇒ `NO_CERTIFICADO` |
| **AC-09 factibilidad** | Separar equilibrio admisible, recuperabilidad desde estado preevento y factibilidad local del QP | Confundir QP infactible con imposibilidad física global |
| **AC-10 revisión humana** | Dos PNG inspeccionados, métricas y causa documentadas; investigador indica `APROBADA` | Sin aprobación ⇒ **STOP**, aun si tests automáticos pasan |

**Dos condiciones matemáticas de interpretación esenciales:**

- Que no exista solución a **un QP de controlador** no implica que la red carezca de un equilibrio físico bajo otro control. Documentar `NO_QP_FEASIBLE` y buscar por separado existencia de equilibrio AC/DAE con restricciones.
- En el manuscrito, la funcional `𝓜(d,ρ)=inf_{ξ∈Ωρ} max_{v∈U_safe} [−λ𝒱−2eᵀH(F+Gv)]` incluye el equilibrio donde vale **cero**; por ello una certificación correcta de compatibilidad suele probar `𝓜=0`, **no** exigir un margen global estrictamente positivo. Evitar pruebas numéricas ingenuas que declaren `FAIL` por ese cero inevitable.

Todos los umbrales de depuración que aparecen arriba son **provisionales** y deben fijarse definitivamente según paso de simulación, bases y equipo antes de los experimentos comparativos de publicación.

## 8. Estado de cada etapa, registro y reproducción

**Estados permitidos:** `PENDIENTE`, `RUNNING`, `PASS_AUTO_WAIT_HUMAN`, `APROBADA`, `REPETIR`, `FAIL`, `BLOCKED`, `NO_CERTIFICADO` (este último **solo** para alcance teórico, nunca convertirlo silenciosamente en `APROBADA`). Si el control de las etapas ya está en un CSV del proyecto, **reutilizar ese CSV** en vez de crear otro.

**Campos mínimos de una fila de la matriz única STED-RW**:

```csv
run_id,stage,case,scenario,baseline,source_sha256,variant_sha256,andes_version,git_commit,seed,simulation_t0,simulation_tf,solver_settings,event_time,event_bus,event_P_MW,event_Q_MVAr,fn_Hz,bus_freq_set,bus_volt_set,f_nadir_Hz,max_RoCoF_Hz_s,min_V_pu,max_V_pu,min_h,qp_infeasible_count,dae_residual,status_auto,status_human,frequency_figure,voltage_figure,raw_file,decision_note
```

**Protocolo por gate:** (1) revisar `main.tex` y estado gate; (2) inspeccionar datos y cambios de código respecto de anterior; (3) generar variante **sin alterar fuente**; (4) verificar PFlow y flat antes del evento; (5) correr un único experimento; (6) guardar series/figuras y validaciones; (7) generar una ficha breve `qué cambió / esperado / observado / límites / PASS|FAIL`; (8) obtener validación humana explícita; (9) recién entonces autorizar fase siguiente. Las gráficas deben marcar instante de evento y tener identificación legible de todas las señales críticas.

**Conservación de evidencia:** guardar entradas/hashes, versiones Python/ANDES, número de ecuaciones DAE, solver/pasos/tolerancias, ID de dispositivos y modos, series de f/V/P/Q/estados relevantes, logs de fallo, fronteras y resultados del certificado. No subir bibliografía, PDF, tablas o figures a una ubicación diferente de sus carpetas existentes.

## 9. Riesgos técnicos y cómo impedir conclusiones falsas

1. **Escala 39:** el sistema puede comportarse distinto del 10/14 de referencia por gobernadores, excitatrices, área equivalente e inercia concentrada; no transferir sintonías ni comparar magnitudes de nadir sin normalizar eventos/reservas.
2. **Slack/equivalente externo:** verificar papel del bus 39 y del 31 en **el caso efectivo**; no proclamar que ambos sean slack. Si inercia H muy elevada domina COI, documentarlo y no extrapolar a red altamente dominada por IBR sin escenario adicional.
3. **Inversor representado:** `REGF1/REGF2` son modelos positivos de secuencia. Comprobar saturaciones, congelamientos, current limiter y si el campo dinámico deja de ser suave. No extrapolar CLF/HOCBF de modelo continuo a cambios de modo sin justificación.
4. **Referencias Q en SG:** un AVR controla referencia de voltaje/campo según su modelo; no existe correspondencia trivial universal `Qset→Qreal`. Identificar o diseñar lazos de seguimiento consistentes, incluso con dinámica de actuador.
5. **Control terciario E14:** el manuscrito contempla una *selección de equilibrio* pero no un despachador económico online completamente definido. Implementar primero variante de redespacho lento con objetivo/costos AC y comprobar restricciones; nunca presentar óptimo económico global sin prueba.
6. **Seguridad entre muestras:** si se implementa QP con retención ZOH, las desigualdades de barrera evaluadas solo en los tiempos de control no demuestran invariancia continua. Certificar cota adicional o etiquetar resultado como evidencia muestreada.
7. **Estado post-contingencia:** una topología nueva modifica DAE, región de atracción y equilibrio; recomputar `Ωρ` y revisar pertenencia del estado de salto. No heredar certificados de topología anterior.
8. **Reemplazo SG→GFL:** añadir PLL y sensibilidad a SCR puede cambiar de modo/respuesta aun manteniendo P0; ejecutar en E15 sus pruebas propias sin la capa de seguridad, antes de compararlo con C2.
9. **Experimento físicamente infactible:** si la demanda supera reservas, `Slack`/controlador implícito no debe aportar generación ilimitada inadvertida. Auditar `P_i` y reservas en cada comparación.
10. **Círculo IBR ≠ curva SG:** no usar `P²+Q²≤Smax²` como prueba de límites térmicos/corriente de campo del SG salvo modelo equivalente validado.

## 10. Qué resultados son defendibles para el paper

**Claim permitido si hay evidencia reproducible:** «En el IEEE-39 modificado C2, la respuesta temporal numérica muestra restauración de frecuencia bajo la perturbación S1 y los límites de salida modelados se respetan con el controlador B5 durante las trayectorias evaluadas».

**Claim condicionado a certificado formal:** «La región `Ωρ` es positiva e invariante, CLF–HOCBF es factible en ella y las trayectorias con condiciones iniciales en esa región convergen al equilibrio seleccionado» **solo** después de probarlo sobre el dominio completo y asegurar que el modelo ANDES se corresponde con las hipótesis de la prueba.

**Claim prohibido sin evidencia adicional:** «seguridad física garantizada para cualquier falla», «control totalmente distribuido» cuando el QP es coordinado, «protección de semiconductores EMT», «ausencia de límites energéticos sin modelar BESS», «estabilidad global» por EIG/TDS, «GFL conserva garantías GFM» automáticamente o «20/40/50% de penetración IBR» por contar número de unidades.

**Cierre científico:** documentar H1–H4 con comparaciones pareadas sobre C2 y al menos una extensión C3. Si no se consigue un certificado riguroso en IEEE-39, reportar únicamente la evidencia numérica efectivamente obtenida y no formular una afirmación formal de estabilidad regional o invariancia.

## 11. Delimitación respecto de los casos 10/14 del artículo de referencia

- Los sistemas de 10 y 14 buses de Kavvathas--Konstantopoulos quedan `OUT_OF_SCOPE` para la campaña experimental y no se reproducirán en este proyecto.
- El artículo de referencia se utilizará para definir y contextualizar el controlador RDC, sujeto a la verificación bibliográfica correspondiente.
- No se transferirán automáticamente al IEEE-39 sus ubicaciones de recursos, frecuencia base, parámetros, resultados HIL ni conclusiones experimentales.
- Toda afirmación de desempeño, seguridad, estabilidad o recuperabilidad del presente trabajo deberá sustentarse exclusivamente en análisis o evidencia generados para IEEE-39 y sus variantes autorizadas.

## 12. Instrucción exacta para Codex/Claude — primera etapa y STOP

```text
Actúa como integrador STED-RW Lean del repositorio
Resilient_distributed_control_PS.

Contrato de trabajo:
- Lee AGENTS.md, CLAUDE.md, Paper_manuscript/main.tex y el plan experimental
  v2 IEEE-39 situado en Paper_manuscript/ops/ (si todavía no está allí,
  solicítalo o usa el archivo provisto explícitamente en el chat).
- NO cambies la estructura de directorios ni renombres archivos existentes.
- NO borres o sobrescribas referencias, el modelo base IEEE-39, el historial de
  decisiones ni archivos raíz. Reutiliza src/cases/artifacts/figures_main/ops.
- `main.tex` ya refleja IEEE-39 como único banco de pruebas; no reintroduzcas
  campañas de 10/14 buses sin una nueva decisión de alcance registrada.
- NO inventes nombres del caso existente ni supongas qué bus es Slack.

ETAPA AUTORIZADA = INSPECCION SOLO LECTURA + E0 C0 IEEE-39.
1. Lee carpetas Paper_manuscript/cases, src, ops y artifacts; identifica el caso
   real de IEEE-39, su versión/idioma/base, buses 30-39, 10 SG, dinámicas
   GENROU, gobernadores, excitatrices, PSS, monitores y eventos preexistentes.
2. Detecta Python/ANDES efectivos dentro de venv/ y verifica documentación
   del caso, modelos REGF1/REGF2, BusFreq, BusROCOF, PFlow, TDS y EIG.
3. Verifica y registra SHA256 del caso y estado de git; NO lo modifiques.
4. Construye exclusivamente E0: PFlow, TDS SIN perturbación, sin agregar
   aún GFM/GFL, secundario, terciario, RDC ni CLF/HOCBF.
5. Si faltan monitores, decide la mínima variante instrumental que conserva
   el caso base intacto. NO cambies despacho físico para obtener gráficas.
6. Genera DOS gráficas de calidad: 39-bus frecuencia(t) [Hz] y voltaje(t) [pu],
   incluyendo buses 4,21,32,34,36,37,39 y todos los máximos/mínimos de V.
   Además registra todas las series de 39 buses, y f de los 10 SG.
7. Reporta: nombre de entrada verificado, potencias totales, referencias,
   ajustes/estados del modelo, paso solver, error PFlow/TDS, drift de f/V,
   versión ANDES, timestamps de eventuales eventos ocultos y diagnóstico.
8. Si E0 FALLA, reporta causa y STOP. Si E0 PASA automáticamente,
   espera aprobación explícita del investigador tras examinar las dos gráficas.
9. No programes E1 ni siguientes y NO indiques que están completadas.
10. Usa estado PASS_AUTO_WAIT_HUMAN hasta recibir la aprobación humana.

Entrega: rutas de ambas PNG y datos brutos, tabla de criterios cumplidos,
lista concreta de bloqueos y propuesta de siguiente acción E1 solamente.
```

## 13. Fuentes del plan y nivel de confirmación

1. **`Paper_manuscript/main.tex`, metodología y subsección `Certification and Reproducible Numerical Evaluation`:** alcance teórico y validación prevista exclusivamente sobre IEEE-39. *Decisión editorial aprobada; no implica corrida ejecutada.*
2. **Adjunto del usuario `Texto pegado.txt` («IEEE 39 barras en ANDES»):** configuración C0–C3, sustituciones 32, 37, 34, 36 y 35, eventos sugeridos y escenarios S0–S5. *Propuestas experimentales, no resultados medidos.*
3. **Plan maestro anterior v1:** política de uso de carpetas existentes, gates humanos, medición f/V y evaluación CLF/HOCBF. *En v2 se conserva lo pertinente y se sustituye la red principal.*
4. **ANDES stable 2.0.0**, primer ensayo https://docs.andes.app/en/stable/tutorials/02-first-simulation.html ; control multietapa https://docs.andes.app/en/stable/tutorials/10-dynamic-control.html ; EIG https://docs.andes.app/en/stable/tutorials/07-eigenvalue-analysis.html ; modelos https://docs.andes.app/en/stable/reference/models/RenGen.html ; medición https://docs.andes.app/en/stable/reference/models/FreqMeasurement.html . *Fuente pública verificada, su ejecución depende del `venv` real.*
5. **Kavvathas and Konstantopoulos, IEEE TPWRS 2025**, DOI https://doi.org/10.1109/TPWRS.2024.3510924. *Marco experimental y controlador RDC de referencia; no equiparar casos HIL al IEEE-39.*

---

**ESTADO FINAL:** `E3_APROBADA`. Se creó C0a retirando únicamente `GENROU_3`, `TGOV1_3`, `IEEEX1_3` e `IEEEST_3`, conservando `PV_3`, y vinculando `REGF1_32` al bus 32 y al generador estático 3 (`Sn=843.7 MVA`, `fn=60 Hz`). La corrida plana no mostró deriva; PFlow y TDS convergieron para perturbaciones independientes de `±58.564 MW` en el bus 4 y `±17.345 MVAr` en el bus 21. El GFM entregó aproximadamente `7.25 pu` y `1.491 pu` en el preevento, sin doble inyección dinámica. La comparación con `Δt/2` fue consistente. EIG no encontró modos con parte real positiva, pero presentó 12 modos cercanos a cero y una advertencia de mala condición; por ello no se formula una afirmación estricta de matriz Hurwitz. El investigador revisó las figuras, las consideró coherentes y aprobó E3. E3 constituye evidencia numérica diagnóstica, no certificación no lineal. **Próxima acción autorizada:** E4--C1, sustitución exclusiva SG37→GFM37, pendiente de instrucción para iniciar.
