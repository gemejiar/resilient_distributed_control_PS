DEC-054-R1 — Corrección científica del diseño preventivo, sin implementación ni TDS

Instrucciones operativas para Codex. Fecha de referencia: 2026-10-27. Repositorio exclusivo: "gemejiar/resilient_distributed_control_PS". Rama: "review/dec054-prospective-preventive-dispatch". Punto de partida verificado: "20650745be4da506b043824f2599dc27b526ef7f". Base histórica inmutable: DEC-053 "04e082b26054bf046bd5421ceb275b582a0547a5"; "main" remoto "1a023d8fa333e62eb716e57a4d67561bb63ea3d0".

0. Alcance y puertas de seguridad

Continuar exclusivamente en modo lectura, razonamiento matemático y edición documental en la rama DEC-054. P0 sigue "STOP_BACKUP_NOT_VERIFIED"; "independent_backup_verified=false"; TDS "0/48". El respaldo de 1,026 MB en el mismo disco no es independiente. No declarar completado P0/P1/P2/P3, no adelantar implementación, no ejecutar optimizaciones, inicializaciones ANDES ni TDS, ni abrir la cohorte prospectiva. No cambiar la planta, CASE XLSX, el RDC B2, los controladores, los valores de Sn/Pmax/Pmin/Qmax/Qmin, PSS, grafo, solver histórico, manuscrito "main.tex", históricos ni sus hashes. No cambiar "main" local/remoto, no hacer merge, PR, force-push, reset ni limpieza destructiva.

Primero verificar "git status", ramas y SHAs. Usar el worktree "C:\Users\gemej\dec054_wt" ya creado; no generar otro salvo necesidad justificada. Leer el protocolo "ops/sted/DEC054_protocol.md" y el borrador "Paper_manuscript/artifacts/IEEE39_DEC054_preliminary_policy_design.md" sin sobrescribirlos. Guardar esta autorización también en "ops/sted/DEC054_R1_review_instructions.md", con SHA-256.

Crear versiones nuevas: "Paper_manuscript/artifacts/IEEE39_DEC054_preliminary_policy_design_v2.md" y "Paper_manuscript/artifacts/IEEE39_DEC054_design_review_matrix.csv". Mantener íntegra la versión v1 como evidencia de auditoría. Si una explicación no puede confirmarse en el código, marcar "UNRESOLVED", sin completar con suposiciones.

1. GATE R1 — Corregir el modelo de información e inicialización del RDC

Revisar, con rutas y números de línea, "Paper_manuscript/src/run_e8_ieee39.py" (en particular "configure", "rdc"), "run_b3_ieee39.py" ("run", "field", callback), "dec051_core.py" ("rdc_state", "apply_params"), "run_e9b0_variant.py", "e9b_variant.py" y los artefactos DEC-052/DEC-053 relevantes.

Hallazgo comprobado que debe incorporarse: los ejecutores inicializan "pn", "qn" con las potencias físicas P/Q del estado del candidato, y "pset(0)=pn", "qset(0)=qn"; "d_p=1/pn", "d_q=1/(qmax-qmin)"; "gref_p", "gref_q" y el "k_ip" efectivo se vuelven a calcular a partir de los factores de capacidad en ese estado. La fórmula de control y ganancias de código permanecen sin editar, pero sus referencias, normalizaciones y ciertos parámetros efectivos dependen del despacho. "d_q" permanece fijo si no cambian los límites; no describirlo como dependiente de "qn".

Analizar el efecto sobre toda evaluación de candidato "z", y escribir el mapa de inicialización

"I(z):= (x^-(z), y^-(z), pn(z), qn(z), gref_p(z), gref_q(z), d_p(z), d_q, k_ip(z), u^-(z), y0(z), y0q(z), vref0(z))".

Verificar en el código la convención temporal exacta: las tasas de actualización de "pset/qset" operan a partir de "t_e=5 s", pero las señales de actuación pueden calcularse antes. El evento "Alter" y la habilitación de las tasas ocurren en el mismo instante nominal; la semántica exacta de orden de eventos/sampling debe quedar "TO_VERIFY_IN_P2", no inventarse.

Tests lógicos documentales (sin ejecutarlos): (i) "pn(z)=P_i^-(z)" y "qn(z)=Q_i^-(z)" bajo la convención de medición usada; (ii) "pset(t_e^-)=pn(z)", "qset(t_e^-)=qn(z)" salvo evidencia de otra inicialización; (iii) "k_ip(z)" y los factores de capacidad se recomputan y se pasan a los Jacobianos; (iv) chequear positividad de "pn", interior de capacidad y ausencia de división por cero; (v) el SG39/Slack no es una variable "p0" libre pero sí debe cumplir límites físicos P/Q/S y participar en las métricas.

Consecuencia científica adicional: si "Pn(z)=P_i^-(z)", entonces la penalización del borrador "C^P_share=Σ Pn_i(P_i^-/Pn_i-r)^2/ΣPn" con "r=ΣP^-/ΣPn" es idénticamente cero ("r=1") en la inicialización correcta. No constituye un objetivo de reparto. El borrador debe corregir esta degeneración, no solo mencionar que "Pn" cambia. También "C_red" con denominadores "Pn_i(z)" utiliza una escala móvil y puede distorsionar comparaciones.

Adoptar escalas positivas, congeladas antes de optimizar (ej. Sn, rango de P o "Pnom" histórico estrictamente positivo) para "C_red". Distinguir explícitamente: (a) costo de desplazamiento del despacho y de tensión, (b) desviación del patrón de participación preevento respecto a participaciones de diseño congeladas, y (c) error de reparto postevento del RDC (métrica pronosticada o medida para cada "d" y "t", solo agregada a "J" si el predictor pertinente es auditado). Evitar confundirlos. Para Q usar límites/rangos válidos y manejar Q de signo mixto. Mantener "J" idéntico para M0–M3, con pesos definidos por regla a priori; no imponer una penalización que se anula por construcción.

No cambiar retroactivamente la observación DEC-053 de que el reparto empeoró (~4% en R35_040); retirar la atribución no verificada a "Pn" estático y formular hipótesis causales que requerirían una auditoría específica, sin TDS ahora.

GATE R1: v2 reproduce conceptualmente el RDC/DAE realmente ejecutado; no se autoriza continuar la definición de un predictor sobre referencias congeladas erróneamente.

2. GATE R2 — Modelo híbrido evento/control y predictor anclado en "0+"

En el instante nominal "t_e" hay dos cambios: perturbación eléctrica y habilitación del lazo de actualización RDC. Diferenciar tres estados:

- "ξ^-(z)": condición preevento coherente (incluye estados del PSS, estados del actuador y "u^-=[pn(z),qn(z)]").
- "ξ^+_d(z)": mismos estados diferenciales y referencias continuos tras el evento, y nuevas algebraicas "y_d^+" obtenidas resolviendo "g_d(x^-,y_d^+,u^-,z)=0".
- "ξ_d(t;z)", "t>t_e": evolución bajo el campo posevento, con el RDC activado, sin retocar el código B2.

Corregir la inconsistencia entre anclar el salto en "y_d^+" y linealizar el predictor sobre el sistema preevento agregando simultáneamente "B_d d", que puede duplicar la entrada o el salto. Especificar una sola formulación consistente, recomendada:

"F_d^+(ξ;z)" = campo DAE reducido (con algebraicas eliminadas en la rama posevento y tasas B2 activadas), parametrizado por el evento d;

"ξ_0=ξ_d^+(z)", "δξ(t_e^+)=0";

"δξ_dot = A_d^+(z) δξ + f_d^+(z)", donde "A_d^+=∂F_d^+/∂ξ|_{ξ_0}", "f_d^+=F_d^+(ξ_0;z)";

"P_hat_i(t;z,d)=P_i(ξ_0;z,d)+C_{i,d}^+(z)δξ(t)", con "C" como derivada de la salida física después de la eliminación algebraica.

"D_hat_i(t_e^+)=0" y "E_hat_i^+=max_{t∈[t_e,t_e+T]} max(0,D_hat_i(t))". Construir también el máximo descendente a partir de "min(0,D_hat_i(t))". Definir de forma explícita el error de truncamiento y el riesgo del uso de una matriz fija por 200 s. Si se prefiere linealizar preevento, presentar una derivación alternativa completa consistente que reproduzca el salto exactamente una vez, pero no mezclarla con la posevento.

Advertir que el modelo incluye 12 PSS genuinos, 20 referencias y las variables físicas que correspondan; no usar la matriz espectral del equilibrio Q+ de DEC-052 indiscriminadamente en otros despachos o eventos. Recalcular "A" por candidato y evento conforme a las reglas; comprobar regularidad de "g_y" para cada rama y sensibilidad local. "σ_min(g_y)" de DEC-052 es del caso anterior, no garantía uniforme.

Por el mal condicionamiento modal histórico, preferir exponenciales matriciales/Schur o integración lineal estable sobre propagación mediante descomposición de autovectores sin control de condicionamiento; declarar procedimientos de cálculo de máximos, tolerancias y error de muestreo. "T=200 s" es horizonte de evaluación, no infinito.

GATE R2: ecuaciones y pseudocódigo reproducen la secuencia preevento → salto no lineal → deriva + transitorio B2 posterior, sin doble conteo.

3. GATE R3 — Revisar la proposición matemática de seguridad

Reformular la Proposición S sobre la planta ANDES RMS modelada, no sobre cualquier red física ni protección EMT, y sobre el horizonte finito "[t_e,t_e+T]", "T=200 s". La versión actual afirma "∀t≥t_e" aunque las excursiones se maximizan solo en los 200 s siguientes.

Para cada unidad i, despacho z y evento d en un conjunto FINITO "D_design", exigir como hipótesis explícita

"ΔP_i^{jump,true}(z,d) ≤ ΔP_i^{jump,model}(z,d)+ε_i^J(z,d)" y

"sup_{t∈[t_e,t_e+T]}[P_i(t)-P_i(t_e^+)] ≤ Ehat_i(z,d)+ε_i^E(z,d)".

Si las dos cotas son válidas y "P_i^-(z)+ΔP_i^{jump,model}+Ehat_i+ε_i^J+ε_i^E≤Pmax_i", se deduce solo "P_i(t)≤Pmax_i" sobre ese horizonte. Para el límite inferior imponer las cotas de signo opuesto y una desigualdad independiente. Para Q y S usar salidas físicas propias y no sumar máximos separados de P y Q para inferir un límite aparente sin una desigualdad justificable.

La hipótesis sobre "ε" no ha sido probada por muestreo ni LOBO; registrar "CONDITIONAL_PROPOSITION", nunca "SAFE_GUARANTEED". Una TDS de malla "dt" no permite concluir invariancia entre muestras; no elevar "TDS_SAFE_OBSERVED" a seguridad continua. Explicitar alteraciones del modo de limitadores, estabilidad del integrador numérico, eventual deriva post-200 s y que "AC_FEASIBLE_FOUND" no implica recuperación.

GATE R3: ninguna frase de garantía se extiende más allá del horizonte, el conjunto de escenarios y el modelo definido.

4. GATE R4 — Revisión del algoritmo de separación de restricciones

Corregir la afirmación de “terminación finita porque W crece”. La iteración no puede crecer si la restricción más violada "(d,i,class)" ya pertenece a W, o si el NLP local no la satisface. Adicionalmente, añadir una restricción no garantiza descenso monótono del error, convergencia a un punto factible ni optimalidad global para un problema AC no convexo.

Proponer los estados de salida explícitos: "FEASIBLE_PREDICTED", "LOCAL_OPTIMUM_FOUND" (solo si condición KKT documentada), "STAGNATED_EXISTING_CUT", "ITERATION_BUDGET_EXHAUSTED", "SOLVER_FAILED", "INFEASIBLE_NOT_DEMONSTRATED". Definir criterio de ingreso de restricciones nuevas, deduplicación de cuts, comprobación de factibilidad real del problema actual y registro de violaciones restantes. Si la más negativa ya está en W y sigue violada, no volver a insertar; diagnosticar incumplimiento de solver/gradiente o limitar alcance. "K_max" y "N_iter" declarados, sin “cortes infinitos” ni afirmar garantía de terminación exitosa.

Si el corte se deduce de una TDS en DESIGN/TUNE, etiquetarlo como restricción local/empírica con radio de confianza o dominio de despacho, no como corte global válido para el espacio no convexo. Las predicciones de máximos sobre una malla temporal y refinamiento local no aseguran un máximo global en tiempo; documentar esto.

Auditar dimensiones y complejidad: no afirmar "O(n_y^1.5)" para factorización dispersa como cota general; el tiempo real depende de estructura y ordenamiento. Dar expresiones de costos simbólicos o presupuesto por llamadas (PF, Jacobiano, simulación lineal, evaluación de escenarios y NLP), a medir luego.

5. GATE R5 — Comparadores, costo y validez prospectiva

Revisar M0–M3 para que TODOS cumplan el mismo AC-OPF y los mismos límites modelados de base, incluidos límites físicos del SG39/Slack, 39 tensiones preevento y balance. La configuración histórica C2t, con 21 barras >1.05 pu, no debe ser un M0 “factible” bajo banda 0.95–1.05.

Mantener idéntico objetivo "J" (no degenerado) para todos los métodos. M1 deberá ajustarse solo en DESIGN/TUNE sin exigir simultáneamente igualdad exacta de costo y de cumplimiento, que en general son metas distintas. Definir dos contrastes independientes: desempeño a costo equivalente (tolerancia definida antes) y mínimo costo observado para un umbral de cumplimiento previsto (si no existen puntos comparables, "NOT_MATCHED", sin extrapolar). Cualquier ajuste de M1 para igualar un resultado de M3 debe congelarse antes de abrir PROSPECTIVE_TEST y no usar resultados de test.

Revisar la partición por barra, sin tocar datos de prueba. Mostrar que el conjunto de 14 barras elegibles y el filtro de 31/39 provienen de reglas físicas predefinidas, sin descartar escenarios por saber que serán desfavorables. Los datos históricos de barras 4 y 18 (P) y 21 (Q) no pueden pasar a la cohorte ciega. Explicitar que 6 escenarios prospectivos equivalen a muy pocas observaciones independientes y que usar varias amplitudes en una barra crea correlación; una selección estratificada por resultado de M0 sería una muestra intencionada, no aleatoria. Antes de sellar P1, enumerar clases P/Q y buses exactos de prueba por regla reproducible, sin examinar rendimientos test.

Calibración LOBO: en el borrador se propone "α=0.10" con 4 DESIGN + 4 TUNE buses. Para n=8 unidades independientes por barra, el cuantil conforme usual de rango "ceil((n+1)(1-α))=9" cae fuera de las 8 observaciones y la cota distribución-libre no es finita (se usaría +∞). Además, no se ha establecido intercambiabilidad espacial ni una verdadera partición conformal train/calibration. No declarar “90% de cobertura” ni etiquetar como garantía conforme: usar "EMPIRICAL_LOCATION_AWARE_MARGIN", presentar máximo residuo observado, LOBO diagnóstico y análisis de sensibilidad. Cualquier "ε" no certificado sigue siendo un margen calibrado. El valor numérico y criterio deben fijarse antes de TDS de holdout.

Predeclarar la cohorte "6 escenarios × M0–M3 = 24 TDS", reservar el presupuesto total 48 y registrar fallos. No forzar Q a una cohorte si el predictor Q no está auditado: decidir alcance antes de abrir resultados y registrar desviaciones del preregistro. No reutilizar test como calibración tras fallos.

6. GATE R6 — Factibilidad física y variables de decisión

Conservar como hipótesis inicial las 19 entradas "z=(p0_PV^9,v0_PV/Slack^10)", pero distinguir entre consignas de flujo de potencia y acciones realmente controlables: Q de cada SG/GFM surge del balance AC y no es "Qset" libre antes del evento; las entradas dinámicas de Q están en los mapas "IEEEX1.vref0" y "REGF1.Qaux0", y se actualizan desde "qset-qn" en B2. Evitar hablar de “despacho Q independiente” sin un actuador adicional implementado. Identificar todas las inyecciones y restricciones sobre SG39, estado slack, pérdidas, límites de tensión de 39 barras y coherencia de inicialización TDS.

Las referencias originales de generación (Pn/Qn) se recomputan por candidato como ya indica R1; verificar si la activación de RDC ocurre con transitorios preevento residuales. Cualquier condición "||f||≤1e-8" debe referirse al residual correcto: equilibrio de la planta (si corresponde) y del DAE, no forzar la tasa "v_RDC" a cero antes de ser activada. Distinguir V-setpoint de tensión física, e incluir chequeo explícito de P/Q/S output modelado, no solo sus consignas.

No inferir cumplimiento de curva de capacidad completa SG, corriente instantánea IBR, OEL/UEL, SoC, EMT ni protecciones desde restricciones de caso RMS.

7. GATE R7 — Novedad bibliográfica (documental)

Comparar con los nueve artículos adjuntos del proyecto y, si Codex dispone de búsqueda pública, ampliar la revisión a OPF con estabilidad transitoria, OPF preventivo con respuesta de frecuencia descompuesta, dynamic security constrained OPF, response-constrained economic dispatch, robust optimization with contingencies, surrogate-assisted preventive control y control de reservas SG/GFM. Usar solamente referencias reales verificables con título, revista, año y DOI/URL de editor, sin inventar metadatos. Especificar novedad a nivel de mecanismo/algoritmo, no afirmar que “OPF robusto + reducción dinámica” es nuevo por sí mismo. Si no hay capacidad de búsqueda, marcar "EXTERNAL_LITERATURE_NOT_VERIFIED" y mantener "NOVELTY_NOT_ESTABLISHED".

Proponer una tabla de cercanía técnica que distinga trabajos sobre márgenes estáticos, frecuencia, potencia física instantánea, excursiones lentas y pruebas prospectivas.

8. Entregables y decisión de cierre

Crear solo estos archivos nuevos en DEC-054:

1. "ops/sted/DEC054_R1_review_instructions.md" — autorización íntegra, SHA.
2. "Paper_manuscript/artifacts/IEEE39_DEC054_preliminary_policy_design_v2.md" — borrador corregido completo; conservar secciones y numeración v1 cuando sea posible, y mantener ecuaciones, algoritmos y supuestos explícitos.
3. "Paper_manuscript/artifacts/IEEE39_DEC054_design_review_matrix.csv" — columnas: "issue_id,source_file,source_lines,error_or_gap,physical_consequence,correction,verification_proposed,status,gate".
4. "Paper_manuscript/artifacts/IEEE39_DEC054_R1_review_report.md" — tabla de gates R1–R7 PASS/OPEN/BLOCKED y preguntas científicas que permanecen.

No reescribir el documento v1; no crear fuentes "dec054_*.py" ni archivos "design_frozen.json"; no modificar "DEC054_protocol.md" ni los manifiestos de P0 salvo agregar documento nuevo de esta autorización; no abrir un PR ni modificar artículo. Verificar que los archivos protegidos no cambiaron, confirmar "tds_ledger" todavía 0/48, "BACKUP_BLOCKED" y el mismo "main" remoto. Hacer commit y push solamente de estos cuatro archivos en "review/dec054-prospective-preventive-dispatch"; confirmar SHA local=remoto.

Resultado final solicitado a Codex: (1) qué corrigió de "Pn/Qn", "d_P/d_Q" y "k_IP"; (2) ecuación consistente post-salto sin doble conteo; (3) Proposición S restringida al horizonte; (4) algoritmo de cortes sin promesas injustificadas; (5) comparadores justos con SG39 y tensión 39 barras; (6) ε y LOBO correctamente delimitados; (7) evaluación de originalidad; (8) qué debe aprobar el investigador para P1; (9) evidencia de integridad y "0/48".

Condición de parada: después de entregar v2, detenerse a la espera de revisión humana. P0 permanece "STOP_BACKUP_NOT_VERIFIED". No hay autorización para simulación, optimización ni implementación experimental.
