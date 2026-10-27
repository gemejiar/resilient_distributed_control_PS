DEC-053 — Cierre metodológico, contraste causal y política preventiva de reservas
Autorización para Codex — Proyecto Resilient_Distributed_Control_PS
Alcance: terminar los pendientes de H2, formalización de reservas H3-R, restricciones físicas y trazabilidad reproducible. No reabrir HOCBF/CLF–HOCBF ni perseguir certificados intervalares de H4.
Punto de partida verificado: gemejiar/resilient_distributed_control_PS, rama review/h3-h4-mathematical-audit-dec052, commit a290e87ecff031b0ba7887b41595e471a2978e65.
Nueva rama: review/dec053-methodology-closure.
0. Mandato, condiciones estrictas y nomenclatura
Ejecuta consecutivamente las fases A–E sin esperar instrucciones entre fases, siempre que no aparezca un bloqueo de integridad, falta de datos imprescindibles o necesidad de modificar el modelo. Presupuesto ordinario: cero simulaciones dinámicas nuevas; máximo absoluto autorizado: cuatro TDS nuevas, sujetas al gate D descrito abajo. Un intento fallido consume una TDS; no ocultar pruebas de descarte, smoke tests ni repeticiones. No existe obligación de gastar las cuatro.
Antes de cualquier análisis:
Comprobar git status, el remoto rdc y los SHA de las ramas main, review/h3-h4-mathematical-audit-dec052, y la nueva rama. Crear la rama desde el commit exacto anterior; no realizar cambios en main, rebase de evidencia, force-push ni PR.
Copiar este texto completo, sin condensarlo, a ops/sted/DEC053_protocol.md dentro del repositorio y registrar su SHA-256. Si Codex recibe solo texto de chat, crear físicamente el archivo. No declarar que falta un protocolo externo: la autorización es este texto.
Auditar las versiones disponibles y los manifiestos de evidencia, incluidas series voluminosas que permanecen locales. Confirmar qué archivos se pueden leer y qué datos se perdieron. No inferir rutas de series por sus títulos; verificar existencia física y SHA-256.
Congelar el inventario previo y una matriz de qué comparación/hipótesis se puede calcular antes de añadir cualquier prueba.
Invariantes: misma planta IEEE-39 y versiones históricas; 6 SG/4 GFM en C2t; controlador B2 original; capacidades Sn, Pmax, Pmin, Qmax, Qmin, Smax; primarios, PSS, grafo, ganancias, limitadores y modos ANDES inalterados; P+ = +58.564 MW bus 4 y Q+ = +17.345 MVAr bus 21 en t=5 s, separados. Variante física de referencia C2t_Vsafe_R35_040. No modificar casos originales, sobreescribir gráficos históricos, cambiar controladores, ajustar ganancias, diseñar HOCBF/MPC/GFL, ni empezar el manuscrito.
Resultados no negociables de DEC-052: ROOT_NUMERICALLY_VERIFIED, Jacobiano exacto sin cota certificada, H4-R CONDITIONALLY_ESTABLISHED/NUMERICALLY_SUPPORTED_LOCAL_STABILITY, región invariante NOT_CERTIFIED, H3-R PREVENTIVE_NUMERICALLY_SUPPORTED; error de Jacobiano del 1.7 % inicialmente atribuido a E9 fue un defecto de referencias desactualizadas del arnés DEC-051; τ dominante ≈ 426.854 s y ζmín ≈ 0.07213 con el PSS incluido. La matriz calculada tiene certificado Lyapunov validado, pero el Jacobiano físico exacto no está certificado Hurwitz. Mantener OPEN-SG31-PMAX para C2t original.
A. Inventario forense y matriz de comparabilidad (sin TDS)
Inspeccionar antes de trabajar: plan_maestro.md; ops/sted/{decision_log.md,traceability_matrix.csv,DEC052_protocol.md}; Paper_manuscript/artifacts/{experiment_matrix.csv,IEEE39_DEC052_claims_matrix.csv,IEEE39_DEC052_superseded_results.csv,DEC052_consolidated_report.md,IEEE39_DEC050_consolidation.json,IEEE39_DEC051_consolidation.json,IEEE39_E16_consolidation.json,IEEE39_E8_C2t_summary.json,IEEE39_E7_C2t_summary.json,IEEE39_E9B0_variant.json,IEEE39_E9B0_variant_R35_040.json,IEEE39_E10_summary.json,IEEE39_E14_transition.json} y las series crudas que sus JSON indiquen.
Inspeccionar los ejecutores reales, sin asumir que nombres distintos representan un mismo controlador: run_e8_ieee39.py, run_b3_ieee39.py, e9b_variant.py, select_equilibrium_b3.py, ejecutores de E7/E9-B0/E10/DEC-050/DEC-051 y utilidades de extracción. Registrar archivos realmente existentes; si alguno de los sugeridos falta, localizar el equivalente antes de reportarlo como faltante.
Construir IEEE39_DEC053_inventory.csv, una fila por caso disponible, con campos mínimos:
run_id,source_stage,commit,case_variant,controller,dispatch_id,scenario,event_bus,event_deltaP_MW,event_deltaQ_MVAr,event_time_s,t_start_s,t_end_s,solver_settings,all_units,all_39_buses,raw_path,raw_sha256,reference_definition,physical_limits_id,comparable_group,limitations.
Taxonomía: B0 = control primario; B1 = PI convencional; B2 = RDC original; B3 = RDC centrado (cuando aplica usa conocimiento privilegiado del evento; no es método causal desplegable); B2_QV1 = corrección fallida conservada. IEEE39_E9B0... es un nombre histórico de variante de planta, no implica que sea el controlador B0: inspeccionar la implementación antes de clasificar. C2t_Vsafe y C2t_Vsafe_R35_040 son cambios del despacho y/o inicialización, no controladores nuevos.
Definir comparabilidad estricta: misma planta, despacho/preestado AC, restricciones, evento, modelo PSS, configuración TDS, horizonte y definición de señales. Distinguir pares:
Efecto del controlador: B1 contra B2, misma planta y despacho.
Efecto del despacho: B2 en despachos históricos distintos, sin adjudicar el beneficio al RDC.
Interacción controlador × despacho: comparación factorial solo cuando existan las cuatro celdas correspondientes bajo las mismas especificaciones.
Primario B0: referencia física, no tratamiento de reserva por sí solo.
Construir IEEE39_DEC053_comparability_matrix.csv con AVAILABLE_MATCHED, AVAILABLE_PARTIAL, CONFOUNDED o MISSING; explicar falta de comparabilidad. No comparar desempeño en 200 s con el estado Q+ de 2000 s como si fueran horizontes equivalentes. No convertir una observación Q+ de 2000 s en resultado P+ de 2000 s.
GATE A: inventario auditado, pareos clasificados y hashes comprobados. Si las series críticas no están accesibles, informar EVIDENCE_GAP y pasar a los cálculos que sí se puedan verificar; prohibido reconstruir series inventadas.
B. Cierre cuantitativo de H2 y comparación causal
B1. Definir indicadores con código central único, señales y unidades auditadas, para cada corrida factible: (i) frecuencia media y, si corresponde, COI justificando ponderaciones; nadir, zenith, error de frecuencia final en ventana declarada, máximo |RoCoF| con metodología de diferenciación y filtrado explicada; (ii) por barra, mínimos/máximos, tiempo fuera de [0.95, 1.05] pu, error de tensión al valor de referencia; (iii) potencias físicas P/Q/S y margen mínimo por unidad, tiempo de violación y coincidencia temporal; (iv) Pset/Qset y desviación de reparto ponderado usando pesos realmente implementados, separando reparto de referencias y reparto de potencias físicas; (v) Q/V error estacionario frente al equilibrio real del RDC y error frente a 1 pu, que no son la misma métrica; (vi) energía o SoC solo si está modelada; (vii) residuales DAE, calidad de datos, frecuencia de registro y horizonte; (viii) CPU únicamente como diagnóstico, sin afirmar tiempo real.
B2. Definir explícitamente qué significa “regulación”: frecuencia restaurada, reparto activo, consenso reactivo, regulación de tensión aproximada y factibilidad de límites. Usar como diagnóstico DEC-050 Q+ ≈ 2000 s (τ observada 417–419 s/418 s; modal ≈ 427 s), error medio de tensión ≈ 3.2e-3 pu y máximo ≈ 8.3e-3 pu. Verificar estos valores en datos antes de reportarlos; no llamar error frente a 1 pu «ausencia de convergencia al equilibrio».
B3. Tiempos de establecimiento: evitar informar establecimiento cuando el horizonte termina antes de alcanzarlo; usar NOT_OBSERVED_WITHIN_HORIZON y una cota unilateral si apropiado. Qset y reparto Q pueden converger con desplazamientos por consenso y leakage; definir objetivos admisibles explícitos. El error final de frecuencia para un equilibrio relativo con tasa angular común no debe redondearse a cero exacto.
B4. Recalcular indicadores para B0/B1/B2/B3 y variantes cuando existan, sin tocar series. Emitir IEEE39_DEC053_H2_metrics.csv y IEEE39_DEC053_H2_pairwise.csv; cada fila pareada debe incluir same_dispatch, same_event, same_horizon, same_model, y una conclusión CAUSALLY_COMPARABLE, DESCRIPTIVE_ONLY o NOT_COMPARABLE. Para pares bajo igual despacho, diferencias de nadir, RoCoF, |Δf_final|, V, reparto, restricciones y calidad. Para RDC con/sin reserva, etiquetar «efecto del despacho bajo RDC fijo», no «ganancia del algoritmo secundario».
B5. Gráficas: comparación pareada frecuencia (zoom transitorio y horizonte consistente), 39 tensiones agregadas con barras críticas y límites, reparto P/Q por SG/GFM, tasa de Qset y desviación respecto al equilibrio, márgenes Pmax de SG31/SG35 con instante de evento. Incorporar bandas, bases, escala real y notas de diferencias de despacho.
GATE B: H2 clasificada por subobjetivos SUPPORTED, PARTIALLY_SUPPORTED, FAILED, NOT_EVALUABLE con evidencia explícita, sin exigir convergencia exacta a V=1 pu. Si falta un PI pareado imprescindible, remitir al presupuesto opcional del bloque D, no improvisar varias pruebas.
C. Regla preventiva de reservas H3-R: método reproducible, sin fabricar garantía
C1. Auditar e9b_variant.py: la versión histórica mueve una delta desde SG35 a GFM32/37/34/36 ponderada por márgenes transitorios obtenidos en el evento P+ sobre C2t_Vsafe. Exponer qué información requiere, qué proviene de la simulación previa, y si existe dependencia del resultado a predecir. Separar Vsafe (reajuste de tensiones y despacho inicial), la corrección SG31 obtenida mediante un equilibrio previo y el ajuste adicional R35. No describir el ajuste histórico delta=0.040 como óptimo calculado automáticamente.
C2. Establecer un procedimiento offline, acotado y causal en cuanto a los datos disponibles al decidir:
Entradas: modelo y límites SG/GFM, escenario(s) de diseño conocidos de antemano, margen disponible de potencias físicas, banda de tensión, estado operativo medido, grafo RDC fijo, y biblioteca etiquetada de excursiones previamente observadas. Declarar explícitamente cuándo el escenario de diseño se conoce por anticipado y cuándo no.
Decisiones: cambios en P0 entre unidades, con balance de potencia AC y reevaluación de pérdidas, opcionalmente Q0/consignas de tensión solo si se justifica; no modificar Sn, límites, controles ni topología.
Restricciones: P/Q/S de la planta, tensiones [0.95,1.05] pu en 39 barras, factibilidad AC, márgenes de maniobra y restricciones de unidades SG/GFM conforme a lo realmente modelado. Declarar límites de tasa/frecuencia y estado BESS si faltan: no suponerlos disponibles.
Margen de diseño: R_i = Pmax_i - P_i^pre; predictor ΔP_i^jump obtenido por solución algebraica posevento; ΔP_i^exc estimado a partir de biblioteca temporal etiquetada; ε_jump observado ≈ 2.28e-3 pu NO es cota para excursión ni error universal. No denominar seguro certificado a R_i >= ΔP_i^jump + ΔP_i^exc + ε mientras ΔP_i^exc sea empírico.
Función objetivo propuesta para prototipo de diseño, solo si verificable: minimizar distancia ponderada del despacho original y penalización de reducción de reserva, sujeto a restricciones de AC y márgenes predictivos. Declarar que el problema AC es no convexo y la solución del solver no prueba optimalidad global. Predefinir pesos y parámetros antes de evaluar validaciones.
Dominio: especificar bus, rango de amplitud, forma temporal (escalón/rampa), 200 s de evaluación transitoria y parámetros congelados. No extrapolar a cualquier barra ni a N−1 o retardos. El predictor debe indicar OUT_OF_CALIBRATION_DOMAIN cuando se use fuera de su biblioteca.
C3. Implementar dos modos separados si son útiles:
HISTORICAL_RULE_REPLAY: reconstruir exactamente el reparto R35_040 y sus márgenes, con parámetros congelados y hash, sin autooptimización.
PROSPECTIVE_POLICY_CANDIDATE: generar un despacho alternativo con las restricciones y datos anteriores, sin mirar su simulación de validación. Si se prueba, el algoritmo, pesos, conjunto de formación, escenario objetivo, predicción y commit/hash deben congelarse antes de ejecutar TDS. No modificar esta política después de ver el resultado y seguir llamándolo validación prospectiva.
C4. Los resultados de barra 18 son simulaciones dinámicas independientes del calibrador principal de barra 4, pero la barra fue seleccionada mediante cribado analítico preevento del mismo modelo. Llamarlas «validación dinámica prospectiva tras cribado del modelo», no una prueba estadística externa ni una certificación de todas las ubicaciones. La predicción fue optimista en SG39 (−0.0600 pu) y GFM32 (−0.0366 pu); ambos no vinculantes en ese caso. Incorporar error con signo, por unidad, y no esconderlo tras el comportamiento favorable de SG31/SG35.
C5. Reportar un chequeo histórico por despachos C2t, C2t_Vsafe, C2t_Vsafe_R35_040 bajo B2; demostrar la separación de: salto algebraico rápido SG31 (C2t viola a t=0+) y máximo transitorio lento SG35 (~7.8 s). Diferenciar margen SG31 original ≈ −0.047 pu en el salto de su peor margen temporal ≈ −0.070 pu. La mejora de SG31 proviene del despacho, no de las consignas de tensión; el cambio R35 añade margen a SG35. No cerrar OPEN-SG31-PMAX del caso original.
C6. Comparar frontera de predictor nominal ≈70.3 MW con intervalo observado ≈65.8845–73.205 MW, indicando punto vs intervalo y dependencia de ubicación, despacho, horizonte y forma temporal. No decir que 70.3 MW es frontera exacta. Preservar los fallos de E12 (escalón Q 138.6 MVAr) y el éxito con rampa de 5 s, sin atribuir universalmente el fallo a un error numérico puro.
Emitir IEEE39_DEC053_reserve_policy_spec.md, IEEE39_DEC053_reserve_replay.json, IEEE39_DEC053_reserve_policy_candidate.json (si existe candidato), IEEE39_DEC053_reserve_validation.csv. Etiquetar la metodología como OFFLINE_SCENARIO_CONDITIONED_PREVENTIVE_REDISPATCH a menos que un ensayo independiente soporte algo más específico.
GATE C: la regla debe ser 100 % reproducible desde entradas identificadas y debe indicar cuando no tiene evidencia suficiente. Si no es posible validar prospectivamente con el presupuesto disponible, la contribución se limita a reconstrucción y formulación de un predictor empírico; no proclamar superioridad de un nuevo algoritmo.
D. Auditoría física y, solo si es indispensable, simulaciones TDS acotadas
D1. Generar una tabla maestra por unidad SG30, SG31, SG33, SG35, SG38, SG39, GFM32, GFM37, GFM34 y GFM36 y por los 39 buses:
Límite de P y Q, Smax, tipo/modelo de dispositivo, base de conversión de pu, signo de variables y cantidad física realmente medida (GENROU/REGF1).
S=sqrt(P^2+Q^2) como límite aparente del modelo; reconocer que no demuestra por sí solo curvas de capacidad de campo/estator SG, corrientes de convertidor a subciclo, temperatura, SoC/energía ni límites EMT.
En cada evento: valor preevento, inmediatamente posevento algebraico (si existe), máximo transitorio y tiempo del máximo, último valor y margen mínimo; zonas fuera de [0.95,1.05] pu para tensión de cada barra.
Separar márgenes de referencias Pset/Qset y salidas físicas P/Q/S; no usar referencias para afirmar cumplimiento físico transitorio.
D2. Repetir en posprocesamiento la auditoría de tensión DEC-052: el cribado C2t histórico alcanza 1.073 pu (21 barras >1.05), pero la planta simulada C2t_Vsafe_R35_040 está en la banda. Mantener SIEMPRE ambos límites de tensión. Las dos pruebas H3 DEC-051 permanecen dentro de banda. No usar flujo estático de otra variante para definir admisibilidad de la variante de validación.
D3. Crear IEEE39_DEC053_constraints_dictionary.csv y IEEE39_DEC053_physical_compliance.csv; cada fila debe señalar MODELLED, APPROXIMATED, NOT_MODELLED, o NOT_OBSERVABLE, y separar violación física simulada de incumplimiento de un certificado no disponible.
GATE D: presupuesto de nuevas TDS — máximo 4, solo si necesario. Evaluar, registrar y aprobar automáticamente una lista CONGELADA antes de la primera TDS:
Primera prioridad: rellenar celdas B1–B2 pareadas en R35_040 (preferentemente P+ y Q+), únicamente si los datos disponibles no permiten contrastar controladores con despacho y eventos idénticos. Antes: comprobar B1 reproducible y que no necesita calibración nueva. Una TDS = una sola combinación de escenario/controlador/variante.
Segunda prioridad: validar un candidato de política preventiva congelado en eventos separados del conjunto de calibración, únicamente cuando exista una política realmente definida y un baseline comparable. Seleccionar eventos antes de correr; máximo dos TDS adicionales, con máximo una corrida por política/evento. Si hacen falta más celdas para comparación causal, reportar INSUFFICIENT_BUDGET y no declarar mejora causal.
Si no existe caso PI verdaderamente pareado o no puede construirse sin modificar el controlador histórico, declarar NOT_COMPARABLE y no crear un controlador sustituto.
Si faltan datos crudos históricos, no gastar simulaciones en recuperar indicadores secundarios por conveniencia; priorizar el par que comprueba una hipótesis realmente central.
Para ejecutar cualquiera de esas TDS: documentar antes run_id, hipótesis, archivos y hashes del caso, B0/B1/B2 seleccionado, despacho, amplitud, bus, horizonte, tolerancias, predicción, umbrales PASS/FAIL, costo presupuestario y decisión gate. Guardar log y series. El fracaso del solver consume una corrida y se conserva. Prohibidos barridos de parámetros, reintentos no contados, ampliaciones tácitas y ajuste posterior de política. No ejecutar ninguna TDS si el valor científico marginal no justifica gasto. Por defecto, mantener cero.
D4. Antes de cualquier ejecución, verificar que los eventos y restricciones están implementados de forma congruente. No interpretar una falta de convergencia TDS como prueba de inexistencia de equilibrio, y no afirmar seguridad entre muestras sin suficiente resolución.
E. Síntesis científica, congelación y reproducibilidad
E1. Crear matriz final de afirmaciones, reutilizando la de 25 claims de DEC-052 como base. Cada afirmación tendrá: claim_id,methodological_step,claim,evidence_type,evidence_ref,scenario,variant,controller,baseline,validated_domain,limitations,status,allowed_paper_wording,forbidden_wording.
E2. Congelar estas conclusiones máximas salvo evidencia nueva:
H1 integración SG/GFM respaldada para variantes ensayadas y límites RMS representados.
H2 frecuencia y reparto P respaldados bajo escenarios evaluados; Q/V lento con error estacionario frente a 1 pu; comparar objetivos y ponderaciones explícitas.
H3-R redispatch preventivo numéricamente respaldado; desigualdad de reserva empírica y sensible a ubicación; NO HOCBF demostrado.
H4-R estabilidad exponencial local condicionada a existencia de la raíz y error del Jacobiano (DEC-052), no formalmente certificada para el modelo exacto ni regional.
Ninguna región segura invariante ni garantía conjunta H3–H4; estado después de un escalón fuera de la región local muestreada; no tiempo real, no protección EMT, no GFL validado.
Incluir resultados negativos E9, E15, B2_QV1 y correcciones E13/DEC-050/DEC-051/DEC-052 sin borrarlos.
E3. Crear un mapa método → algoritmo real → parámetros → evidencia → limitación, de forma que cada parte de la metodología reformulada sea reproducible:
DAE con SG/GFM/PSS y simulación ANDES positiva secuencia.
Control RDC B2 original, referencia B0/B1, actuación y grafo.
Factibilidad AC / elección de puntos operativos (SLSQP si aplica, solamente óptimo local).
Predicción posevento del salto algebraico con estados diferenciales continuos.
Identificación de excursión electromecánica empírica y restricción de reserva.
Redespacho preventivo offline condicionado al escenario, sin certificado general.
Simulación y auditoría física P/Q/S/V y fronteras dinámicas.
Equilibrio relativo calculado y estabilidad local condicionada del sistema DAE–RDC.
Sensibilidad a retardos, E14 y limitaciones; controles fallidos conservados.
Este mapa es una especificación metodológica para posterior redacción del manuscrito; no editar Paper_manuscript/main.tex ni generar secciones para publicación.
E4. IEEE39_DEC053_master_metrics.csv: normalizar nombre de las unidades, bases, señales, bandas, escenarios y ventanas; incluir not_available_reason en lugar de fabricar resultados. IEEE39_DEC053_scientific_gaps.md debe enumerar únicamente las brechas que limitan afirmaciones del artículo reformulado, y por separado los requisitos no perseguidos del CLF–HOCBF original.
E5. Preservar manifiesto con SHA-256, Git SHA, versión de Python, ANDES, NumPy/SciPy, archivos de entrada, semillas cuando apliquen, solver y parámetros TDS. Para cada serie grande (>10 MB) registrar existencia física, tamaño, SHA-256, ubicación de respaldo real verificada, posibilidad de regeneración y comandos de reproducción. Si solo existe en una máquina y no hay respaldo, marcar AT_RISK_LOCAL_ONLY: un hash sin bytes disponibles no asegura reproducibilidad. No publicar binarios grandes ni afirmar una copia remota inexistente.
E6. Reporte final con tres secciones separadas: «resultado verificable», «resultado condicionado» y «resultado no probado». Incluir tabla control vs despacho y H1–H4 con limitaciones. Gráficas listas para ilustrar los resultados científicos pero sin texto de paper, preferiblemente en Paper_manuscript/figures_main/:
IEEE39_DEC053_H2_controller_comparison.png (si hay pares válidos),
IEEE39_DEC053_reserve_attribution.png,
IEEE39_DEC053_physical_limits.png,
IEEE39_DEC053_method_evidence_map.png (opcional; no generar si no añade valor).
F. Entregables exactos y estado de cierre
Protocolo y auditoría
ops/sted/DEC053_protocol.md
Paper_manuscript/artifacts/DEC053_consolidated_report.md
Paper_manuscript/artifacts/IEEE39_DEC053_inventory.csv
Paper_manuscript/artifacts/IEEE39_DEC053_comparability_matrix.csv
Paper_manuscript/artifacts/IEEE39_DEC053_reproducibility.json
H2
Paper_manuscript/artifacts/IEEE39_DEC053_H2_metrics.csv
Paper_manuscript/artifacts/IEEE39_DEC053_H2_pairwise.csv
Reservas y física
Paper_manuscript/artifacts/IEEE39_DEC053_reserve_policy_spec.md
Paper_manuscript/artifacts/IEEE39_DEC053_reserve_replay.json
Paper_manuscript/artifacts/IEEE39_DEC053_reserve_validation.csv
Paper_manuscript/artifacts/IEEE39_DEC053_constraints_dictionary.csv
Paper_manuscript/artifacts/IEEE39_DEC053_physical_compliance.csv
Paper_manuscript/artifacts/IEEE39_DEC053_reserve_policy_candidate.json solo si existe un candidato congelado; no crear uno ficticio.
Cierre científico
Paper_manuscript/artifacts/IEEE39_DEC053_master_metrics.csv
Paper_manuscript/artifacts/IEEE39_DEC053_claims_final.csv
Paper_manuscript/artifacts/IEEE39_DEC053_method_evidence_map.md
Paper_manuscript/artifacts/IEEE39_DEC053_scientific_gaps.md
Paper_manuscript/artifacts/IEEE39_DEC053_closure.json con gate A–E, presupuesto TDS (ejecutadas + fallidas ≤4), hashes y bloqueo/limitación.
Actualizar, sin sobrescribir historia:
ops/sted/decision_log.md (nuevo DEC-053; sin inventar DEC-049),
ops/sted/traceability_matrix.csv,
Paper_manuscript/artifacts/experiment_matrix.csv,
plan_maestro.md (anotar estado real; si el encabezado histórico «E8_APROBADA» ya no representa el estado final, incorporar corrección explícita sin borrar decisiones previas).
No inflar el repositorio con scripts duplicados. Reutilizar utilidades y crear solo los módulos mínimos de análisis. No comenzar el paper, no modificar Paper_manuscript/main.tex.
G. Aceptación y reporte a investigador
Codex debe contestar con cifras, rutas y categorías, sin proponer otra campaña automáticamente:
¿Cuáles pares B1/B2 son realmente comparables y en qué condiciones?
¿Qué componentes de H2 se cumplen o no y cuál es el compromiso Q–V frente al equilibrio real?
¿Qué parte del beneficio en SG31/SG35 proviene exclusivamente del despacho preventivo?
¿La política de reservas se deduce prospectivamente de datos preevento o está calibrada en transitorios previos? ¿Cuál es el dominio explícito?
¿La regla histórica R35_040 se reproduce? ¿Se validó una regla nueva sin reutilizar la prueba de validación para ajustarla?
¿Qué límites físicos están modelados y cuáles no (SG, GFM, EMT, SoC)?
¿Qué evidencia sostiene la frontera nominal de 70.3 MW y cuáles son sus excepciones?
¿Cuántas TDS nuevas se ejecutaron y por qué cada una era indispensable? Mostrar contador antes/después.
¿Cuáles series voluminosas están solo en local y cómo se garantiza efectivamente su recuperación?
¿Cuáles son las afirmaciones permitidas y prohibidas para un futuro IEEE Journal paper?
Estados por tarea: PASS, PASS_WITH_FINDINGS, PARTIAL, NEGATIVE, BLOCKED_MISSING_DATA, NOT_APPLICABLE. Una prueba negativa es válida si está documentada y no altera la historia. Se permite cerrar DEC-053 con resultados parciales; no se permite declarar validación causal de pares confundidos ni una garantía matemática inexistente.
Cierre Git: crear commit(s) solo en review/dec053-methodology-closure, realizar push exclusivamente a gemejiar/resilient_distributed_control_PS, verificar SHA remoto/local y confirmar main=1a023d8fa333e62eb716e57a4d67561bb63ea3d0. No PR ni merge. Detenerse tras enviar al investigador resumen, rutas y bloqueos. Toda nueva modificación sustantiva del controlador, ampliación experimental o redacción del paper requiere autorización posterior.
