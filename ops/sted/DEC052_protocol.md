DEC-052 — Auditoría matemática rigurosa y consolidación de H3-R/H4-R

1. Objetivo y autorización

Ejecuta una auditoría científica final de las demostraciones de H3-R y H4-R desarrolladas en DEC-051.

El objetivo es convertir las evidencias computacionales existentes en certificados matemáticos verificables cuando sea posible, corregir inconsistencias metodológicas y establecer con precisión el nivel de demostración alcanzado.

Esta autorización no permite nuevas simulaciones dinámicas, modificar controladores ni iniciar la redacción del artículo científico.

Los tres resultados prioritarios son:

1. Existencia matemáticamente certificada de un equilibrio relativo del sistema DAE–RDC.
2. Estabilidad exponencial local no lineal certificada, módulo la simetría angular.
3. Auditoría completa de la seguridad preventiva H3-R, incluyendo restricciones de tensión y validez de las predicciones.

Si un certificado formal no puede construirse, conservar los resultados computacionales existentes y declarar explícitamente la limitación. No modificar las hipótesis ni los criterios de aceptación para obtener artificialmente un resultado positivo.

2. Repositorio, rama y reproducibilidad

Repositorio: "gemejiar/resilient_distributed_control_PS"

Punto de partida:

- Rama: "review/h3-h4-verification-dec051"
- Commit: "5719200"
- Nueva rama: "review/h3-h4-mathematical-audit-dec052"
- "main" debe permanecer en "1a023d8".

Antes de comenzar, verificar el SHA remoto, el SHA local y la ascendencia de la rama.

Primera tarea obligatoria: guardar estas instrucciones íntegramente en "ops/sted/DEC052_protocol.md". Registrar su hash SHA-256. Este archivo debe formar parte del commit final para que futuras campañas no dependan del texto de una conversación externa.

Conservar sin alteraciones todos los archivos históricos de E0–E16, DEC-050 y DEC-051.

No reescribir el historial Git ni modificar parámetros físicos, ganancias, capacidades, límites o configuraciones de la planta.

No trabajar en "Paper_Plantilla".

3. Material que debes inspeccionar

Utiliza como fuentes primarias:

- "Paper_manuscript/artifacts/DEC051_consolidated_report.md"
- "Paper_manuscript/artifacts/IEEE39_DEC051_equilibrium.json"
- "Paper_manuscript/artifacts/IEEE39_DEC051_equilibrium_state.npz"
- "Paper_manuscript/artifacts/IEEE39_DEC051_H4_summary.json"
- "Paper_manuscript/artifacts/IEEE39_DEC051_H4_matrices.npz"
- "Paper_manuscript/artifacts/IEEE39_DEC051_H3_summary.json"
- "Paper_manuscript/artifacts/IEEE39_DEC051_H3_jump.json"
- "Paper_manuscript/artifacts/IEEE39_DEC051_H3_predictions.json"
- "Paper_manuscript/artifacts/IEEE39_DEC051_H3_sim1.json"
- "Paper_manuscript/artifacts/IEEE39_DEC051_H3_sim2.json"
- "Paper_manuscript/src/dec051_core.py"
- "Paper_manuscript/src/run_dec051_equilibrium.py"
- "Paper_manuscript/src/run_dec051_h4.py"
- "ops/sted/decision_log.md"

Inspeccionar también los ejecutores de E9-A, E13 y DEC-050 que utilizan la linealización anterior.

Datos iniciales que deben verificarse:

- Sistema con 208 estados dinámicos, incluyendo los PSS, y 20 referencias.
- Dimensión del espacio cociente: 227.
- Residual del equilibrio relativo: aproximadamente 5.1e-12.
- Bloque algebraico regular numéricamente.
- Abscisa espectral: −2.3427e-3 s^-1.
- Amortiguamiento mínimo: 0.0721.
- Constante de tiempo dominante: 426.85 s.
- Región invariante segura: no certificada.
- H3-R: respaldo numérico, sin certificación de seguridad transitoria.

Todos estos valores son resultados previos, no nuevas demostraciones.

---

BLOQUE A — AUDITORÍA ESTRUCTURAL DEL MODELO

A1. Verificar la conservación del PSS

Confirmar que el modelo utilizado en DEC-051 incluye efectivamente la dinámica activa de IEEEST de los seis generadores síncronos.

Auditar:

1. Los dos estados dinámicos genuinos de cada PSS.
2. La eliminación de estados degenerados.
3. La preservación de las relaciones algebraicas de los bloques eliminados.
4. Las conexiones entre potencia eléctrica, PSS, excitatriz y generador.
5. La influencia del PSS en el Jacobiano reducido.

No aceptar la afirmación de eliminación exacta únicamente porque los parámetros de algunos bloques sean cero.

Construir una tabla de correspondencia entre estados del modelo ANDES y estados del sistema reducido.

Criterio A1: confirmar equivalencia de las ecuaciones retenidas y eliminadas, dentro del dominio operativo considerado.

A2. Verificar la simetría angular

Demostrar estructuralmente la invariancia frente a un desplazamiento angular común.

No aceptar como prueba suficiente encontrar un único autovalor próximo a cero.

Comprobar que la reducción:

- Elimina exactamente una dirección de simetría.
- Conserva las restantes dinámicas físicas.
- Preserva los autovalores no asociados a esa simetría.
- Es consistente con el equilibrio relativo de frecuencia angular común distinta de cero.

Especificar claramente las matrices de proyección y reconstrucción utilizadas.

A3. Verificar la regularidad algebraica

Confirmar la estructura del DAE y la invertibilidad local de su bloque algebraico después de eliminar estados degenerados.

Registrar:

- Dimensiones.
- Normas.
- Número de condición.
- Valor singular mínimo.
- Residual algebraico.
- Dependencia respecto al escalamiento.

Una condición numérica favorable no sustituye una prueba validada de invertibilidad, pero puede emplearse como diagnóstico.

GATE A: si el modelo reducido no reproduce fielmente el DAE y el RDC implementado, detener la certificación matemática y documentar el defecto. No intentar certificar un sistema distinto del simulado.

---

BLOQUE B — CERTIFICACIÓN DE EXISTENCIA DEL EQUILIBRIO

B1. Construir el problema estacionario completo

Partir del sistema:

x_dot = f(x,y,u,d)
0 = g(x,y,u,d)
u_dot = v_RDC(x,y,u,d)

Utilizar el equilibrio numérico DEC-051 como aproximación inicial.

Considerar explícitamente el equilibrio relativo, donde las velocidades angulares comunes pueden ser distintas de cero.

Fijar una referencia angular para eliminar la indeterminación de fase.

Construir una función estacionaria reducida F_q(z) que incorpore:

- Dinámica diferencial.
- Restricciones algebraicas.
- Controlador RDC original.
- Relaciones de los actuadores SG/GFM.
- Estados y realimentación del PSS.
- Condiciones de equilibrio relativo.

No congelar artificialmente consignas ni eliminar términos dinámicos que intervienen en el controlador real.

B2. Intentar una prueba validada de existencia

Utilizar preferentemente un método de Newton–Kantorovich, Krawczyk o Newton intervalar.

El objetivo es probar que existe una raíz verdadera dentro de una región pequeña alrededor de la solución numérica.

Para una aplicación basada en contracción, construir:

- Una aproximación z0 a la raíz.
- Un operador precondicionador C.
- Un conjunto X alrededor de z0.
- Una inclusión rigurosa del Jacobiano J(X).

Verificar una condición suficiente del tipo:

||C F_q(z0)|| + sup_{z en X} ||I - C J(z)|| r < r

y

sup_{z en X} ||I - C J(z)|| < 1

para la bola de radio r, usando normas compatibles y cotas validadas.

La evaluación intervalar debe tener redondeo dirigido o un mecanismo equivalente que garantice inclusión.

Incluir la validación de las ecuaciones algebraicas; no construir un certificado del sistema diferencial ignorando el error de eliminación algebraica.

B3. Tratamiento de segundas derivadas

DEC-051 estimó que la condición Newton–Kantorovich sería suficiente si se justificara una cota de segundas derivadas inferior a aproximadamente 1521 en la norma escalada utilizada.

Los máximos obtenidos mediante muestreo fueron considerablemente menores, pero esto NO constituye una cota rigurosa.

Intentar derivar una cota válida mediante:

- Diferenciación automática con intervalos, si la infraestructura lo permite.
- Evaluación intervalar del Jacobiano sobre una caja pequeña.
- Descomposición por bloques y cotas analíticas de las no linealidades.
- Otro método de verificación numérica matemáticamente justificado.

Se permite seleccionar una norma y un escalamiento mejor condicionados, siempre que sean transformaciones invertibles y no modifiquen las ecuaciones físicas.

No utilizar "mpmath" de alta precisión, comparaciones entre pasos o muestreos aleatorios como sustitutos de una cota de inclusión rigurosa.

GATE B:

- "ROOT_CERTIFIED": se verificaron condiciones suficientes de existencia y, cuando corresponda, unicidad local.
- "ROOT_NUMERICALLY_VERIFIED": residual pequeño y convergencia reproducible, sin certificado de existencia.
- "ROOT_INVALID": se detectó inconsistencia en las ecuaciones o en la solución.

Si no puede obtenerse una cota validada, no continuar indefinidamente probando ajustes numéricos.

Conservar el resultado anterior como numérico, sin declararlo formalmente probado.

---

BLOQUE C — CERTIFICACIÓN DEL JACOBIANO Y DE LYAPUNOV

C1. Identificar el Jacobiano correcto

Verificar que la matriz usada en el certificado representa la derivada del campo reducido completo en el equilibrio relativo.

La referencia debe ser el modelo DEC-051 que incluye el PSS, no el Jacobiano E9-A.

Construir una comparación reproducible entre:

- Jacobiano analítico de ANDES con reducción algebraica.
- Jacobiano central del campo no lineal.
- Derivadas de las 20 tasas RDC.
- Derivadas de los mapas de actuación.
- Jacobiano resultante en coordenadas cociente.

Identificar la causa exacta de las discrepancias del 1.7 % detectadas en DEC-051.

Corregir la implementación del Jacobiano en un módulo nuevo si fuera necesario. No modificar ni sobrescribir los resultados históricos.

C2. Obtener una cota verificable del error

Sea A = Ahat + E, donde Ahat es la matriz calculada y A la derivada exacta en el equilibrio verdadero.

Intentar obtener una cota justificada ||E||_2 <= delta_A.

La cota debe considerar:

- Error de derivación.
- Error de redondeo.
- Incertidumbre sobre la localización exacta del equilibrio.
- Eliminación algebraica.
- Error de transformación de coordenadas.

Los ensayos con diferentes pasos de diferencias finitas sirven como comprobación de consistencia, no como cotas rigurosas de delta_A.

Si no se obtiene una cota validada, continuar únicamente con la auditoría de estabilidad numérica.

C3. Certificado robusto de Lyapunov

Reutilizar la matriz P de DEC-051 cuando sea apropiado.

Comprobar P = P^T > 0 y R0 = Ahat^T P + P Ahat + I.

Para el Jacobiano exacto: A^T P + P A = -I + R0 + E^T P + P E

Por tanto, intentar certificar: ||R0||_2 + 2 ||P||_2 delta_A < 1

incluyendo explícitamente las cotas de error aritmético en la evaluación de R0 y en la verificación de P > 0.

No sustituir una estimación estadística de error por delta_A.

Registrar el margen de la desigualdad, no únicamente un indicador booleano.

La matriz P debe permanecer expresada en coordenadas y escalamiento compatibles con A y con la norma utilizada.

C4. Mejorar el condicionamiento si resulta necesario

Si la desigualdad anterior falla debido al condicionamiento:

1. Evaluar un escalamiento invertible de estados.
2. Comprobar si una formulación por bloques o una matriz Q ponderada mejora la certificación.
3. Recalcular P en las nuevas coordenadas, sin modificar la planta ni el controlador.

Permitir como máximo dos estrategias de precondicionamiento justificadas.

No reducir artificialmente el orden dinámico ni eliminar modos lentos o estados del PSS para facilitar el resultado.

C5. Aplicar el método indirecto de Lyapunov

Solo si se han certificado:

- Existencia del equilibrio relativo.
- Regularidad del bloque algebraico.
- Suavidad local del campo reducido.
- Correcta eliminación de la simetría angular.
- Propiedad Hurwitz del Jacobiano exacto.

Entonces formular la conclusión: el equilibrio relativo es localmente exponencialmente estable, módulo la simetría angular, para el sistema no lineal DAE–RDC en una vecindad de radio no necesariamente cuantificado.

No afirmar estabilidad global, regional cuantificada ni seguridad transitoria ante escalones finitos.

Si las condiciones anteriores solo se han verificado en punto flotante, utilizar "NUMERICALLY_SUPPORTED_LOCAL_STABILITY" en vez de "RIGOROUSLY_CERTIFIED_LOCAL_STABILITY".

C6. Región segura: solo comprobación adicional

No convertir esta campaña en una nueva búsqueda extensa de regiones invariantes.

Si las cotas obtenidas permiten certificar fácilmente un conjunto Lyapunov local:

- Comprobar V_dot < 0 en todo el conjunto.
- Comprobar P/Q/S/V para todas las condiciones dentro del conjunto.
- Verificar regularidad y ausencia de cambios de modo.

Si no es posible, conservar "REGION_NOT_CERTIFIED".

No interpretar las 83 direcciones muestreadas en DEC-051 como demostración de invariancia.

GATE C: clasificar separadamente estabilidad lineal numérica, estabilidad lineal rigurosamente certificada, estabilidad no lineal local condicionada y estabilidad no lineal local rigurosamente certificada.

---

BLOQUE D — AUDITORÍA DE H3-R

D1. Corregir la inconsistencia de tensión

DEC-051 modificó el criterio de selección del segundo escenario eliminando el límite superior de tensión porque un flujo de potencia utilizado en el análisis presentaba barras cercanas a 1.07 pu.

Sin embargo, las simulaciones dinámicas H3-1 y H3-2 sobre la variante R35_040 reportan tensiones máximas próximas a 1.0444 pu.

Investigar y documentar la diferencia entre:

- Flujo de potencia estático empleado para seleccionar escenarios.
- Inicialización dinámica de ANDES.
- Despacho C2t original.
- Variante C2t_Vsafe.
- Variante C2t_Vsafe_R35_040.
- Estado previo y posterior a cada perturbación.
- Barras y magnitudes efectivamente comparadas.

Verificar base de tensión, modelos activos, puntos operativos y restricciones impuestas en cada problema.

No asumir que ambos cálculos tienen idénticas condiciones iniciales.

D2. Restablecer los límites físicos originales

El requisito de operación es 0.95 <= V_i <= 1.05 pu para las barras a las cuales se aplica formalmente esa restricción.

No eliminar el límite superior por conveniencia.

Si un caso analítico parte fuera de ese intervalo, debe clasificarse como no admisible bajo el requisito original o analizarse explícitamente bajo una especificación distinta.

Reevaluar mediante procesamiento de datos y cálculos algebraicos:

- Selección de la barra 18.
- Candidatos alternativos.
- Márgenes de tensión.
- Perturbaciones catalogadas como admisibles.
- Comparaciones realizadas entre predicción y simulación.

No ejecutar nuevas simulaciones dinámicas.

D3. Auditar la desigualdad de reserva

Conservar la expresión R_i >= DeltaP_jump_i + DeltaP_exc_i + epsilon_i y documentar por separado:

- Reserva inicial.
- Salto algebraico instantáneo.
- Excursión rápida.
- Excursión electromecánica lenta.
- Error de predicción.
- Dependencia respecto de la ubicación y amplitud de la perturbación.

Diferenciar explícitamente:

Salto algebraico: calculado resolviendo las ecuaciones del DAE con estados diferenciales continuos.

Excursión transitoria: estimación empírica obtenida de simulaciones y escalamiento de amplitud.

Margen de error: debe distinguir el error observado de una cota matemática válida.

No denominar garantía universal a la desigualdad mientras alguno de sus términos dependa de máximos empíricos sin cotas justificadas.

D4. Revisar la precisión predictiva

Revisar independientemente las dos validaciones H3.

Para P+ 64.4204 MW en barra 4:

- Contrastar predicciones y máximos físicos de las diez unidades.
- Confirmar errores de las unidades críticas SG31/SG35.
- Comprobar P/Q/S/V en la trayectoria registrada.

Para P+ 58.564 MW en barra 18:

- Registrar que el máximo error predictivo entre todas las unidades alcanzó aproximadamente 0.06 pu.
- No resumir la precisión global utilizando solamente los errores de SG31 y SG35.
- Explicar por qué la predicción fue conservadora para SG35.
- Determinar si la nueva auditoría de tensión cambia la interpretación de admisibilidad del escenario.

Diferenciar validación independiente en simulaciones dinámicas de certificación matemática.

D5. Revaluar el alcance de H3-R

Asignar uno de los estados:

- "PREVENTIVE_CERTIFIED": únicamente si existen cotas válidas para toda la clase declarada y se verifica el cumplimiento físico correspondiente.
- "PREVENTIVE_NUMERICALLY_SUPPORTED": los escenarios ensayados respetan restricciones, pero las excursiones dependen de observaciones empíricas.
- "PREVENTIVE_PARTIALLY_SUPPORTED": algunas restricciones o condiciones no pueden validarse.
- "PREVENTIVE_NOT_SUPPORTED": los resultados contradicen la hipótesis reformulada.

No afirmar que un redespacho garantiza seguridad para todas las ubicaciones de carga.

No afirmar H3 original demostrado.

---

BLOQUE E — TRAZABILIDAD Y CORRECCIONES CIENTÍFICAS

E1. Matriz de resultados sustituidos

Crear una matriz que compare:

Fuente histórica | Deficiencia identificada | Resultado DEC-051 | Estado científico actualizado
E9-A | Estados PSS omitidos; errores de Jacobiano | Modelo PSS-completo | Sustituido para análisis modal
E13 | Jacobiano heredado y puntos con deriva | Equilibrio relativo verificado | Modal anterior solo diagnóstico
DEC-050 | Resultados modales anteriores | 427 s y ζ 0.072 | Actualizados
DEC-051 | Evidencia computacional sin aritmética validada | Auditoría DEC-052 | Según certificación alcanzada

No sobrescribir los archivos de resultados originales.

Crear correcciones documentales explícitas y referencias al nuevo análisis.

E2. Corregir fechas y registros

Verificar la fecha DEC-051 contra la fecha real del commit y el reloj del entorno.

No modificar fechas históricas sin evidencia.

Si existe una discrepancia, registrar una nota de corrección. No fabricar contenidos para DEC-049, que actualmente figura como un número sin entrada.

E3. Verificar integridad

Comprobar:

- Hashes de archivos originales.
- Equilibrio y matrices DEC-051.
- Archivos H3 y H4.
- Scripts modificados.
- Ausencia de cambios en parámetros físicos.
- Ausencia de modificaciones de resultados históricos.
- Reproducibilidad de los cálculos estáticos.

No reconstruir ni alterar series históricas que no hayan cambiado.

---

4. Presupuesto y reglas de parada

Simulaciones dinámicas nuevas permitidas: CERO.

Se autorizan:

- Resolución de ecuaciones algebraicas.
- Evaluación de Jacobianos.
- Cálculos con aritmética intervalar.
- Diferenciación automática.
- Resolución de ecuaciones Lyapunov.
- Cálculos espectrales.
- Verificaciones de residual y condicionamiento.
- Procesamiento de archivos existentes.

No se autorizan:

- Corridas TDS adicionales.
- Nuevos eventos P/Q.
- Modificación del RDC.
- Optimización de ganancias.
- Nuevas configuraciones de planta.
- Desarrollo de HOCBF, MPC o filtros de seguridad.
- Extensión GFL.

Limitar la búsqueda de certificados a una formulación validada principal y, si existe una razón técnica concreta, una alternativa de precondicionamiento. Evitar iteraciones indefinidas.

Si la validación intervalar resulta inviable para las 227 dimensiones, registrar exactamente qué operación impide la certificación y cerrar con las conclusiones numéricas defendibles.

El fracaso en conseguir un certificado formal no invalida los resultados experimentales previos.

---

5. Entregables

Crear los siguientes archivos:

Protocolo y auditoría
- "ops/sted/DEC052_protocol.md"
- "Paper_manuscript/artifacts/DEC052_consolidated_report.md"
- "Paper_manuscript/artifacts/IEEE39_DEC052_model_audit.json"
- "Paper_manuscript/artifacts/IEEE39_DEC052_integrity.json"

H4
- "Paper_manuscript/artifacts/IEEE39_DEC052_root_certificate.json"
- "Paper_manuscript/artifacts/IEEE39_DEC052_jacobian_certificate.json"
- "Paper_manuscript/artifacts/IEEE39_DEC052_lyapunov_certificate.json"
- "Paper_manuscript/artifacts/IEEE39_DEC052_H4_conclusions.md"

H3
- "Paper_manuscript/artifacts/IEEE39_DEC052_H3_voltage_audit.csv"
- "Paper_manuscript/artifacts/IEEE39_DEC052_H3_reserve_audit.csv"
- "Paper_manuscript/artifacts/IEEE39_DEC052_H3_conclusions.md"

Síntesis
- "Paper_manuscript/artifacts/IEEE39_DEC052_claims_matrix.csv"
- "Paper_manuscript/artifacts/IEEE39_DEC052_reproducibility.json"

Crear los scripts de auditoría necesarios dentro de "Paper_manuscript/src/", sin reemplazar ejecutores históricos.

Si una prueba no produce certificado, el archivo de salida correspondiente debe existir y explicar la razón del fallo, los datos examinados y el nivel de evidencia que permanece válido.

Todos los resultados deben registrar método numérico, precisión, tolerancias, normas, software y versiones.

Actualizar:
- "plan_maestro.md"
- "ops/sted/decision_log.md"
- "ops/sted/traceability_matrix.csv"
- "Paper_manuscript/artifacts/experiment_matrix.csv"

---

6. Matriz de aceptación científica

Al finalizar, presentar esta tabla con evidencia verificable:

Propiedad | Estado mínimo aceptable | Estado ideal
Correspondencia DAE–RDC–PSS | Modelo auditado y coherente | Equivalencia estructural justificada
Existencia de equilibrio | Numéricamente verificada | Certificada por inclusión rigurosa
Jacobiano reducido | Numéricamente validado | Error acotado rigurosamente
Estabilidad lineal local | Fuertemente respaldada | Certificado Lyapunov validado
Estabilidad no lineal local | Condicionada al equilibrio y Jacobiano | Teorema aplicado con hipótesis certificadas
Región invariante segura | No certificada, correctamente identificada | Certificada si resulta factible
Saltos algebraicos de potencia | Consistencia numérica | Cota válida para clase declarada
Reservas SG31/SG35 | Respaldo numérico reproducible | Condición suficiente con cotas válidas
H3-R | Respaldo numérico | Certificación preventiva condicionada
H4-R | Estabilidad local numérica/condicionada | Estabilidad local no lineal certificada

No utilizar "PROVEN" sin indicar si el resultado es una prueba exacta, asistida por computador con cotas validadas o una conclusión matemática condicionada a hipótesis verificadas numéricamente.

---

7. Condición de cierre y GitHub

La campaña DEC-052 se considerará concluida cuando:

1. Se haya auditado la estructura dinámica incluyendo PSS.
2. Se haya intentado una certificación de existencia del equilibrio.
3. Se haya intentado obtener una cota defendible del Jacobiano.
4. Se haya evaluado la desigualdad Lyapunov con errores incluidos.
5. Se haya reconciliado la inconsistencia de tensión de H3.
6. Se hayan actualizado las afirmaciones científicas y la trazabilidad.
7. Se haya verificado la integridad de los resultados históricos.

Crear un commit de cierre y subir exclusivamente "review/h3-h4-mathematical-audit-dec052" al remoto "gemejiar/resilient_distributed_control_PS". Confirmar coincidencia SHA local/remoto.

No modificar "main", no abrir pull request y no comenzar el artículo.

8. Informe final obligatorio para el investigador

Responder directamente:

1. ¿Existe un certificado riguroso de la raíz DAE–RDC?
2. ¿El modelo reducido reproduce fielmente el PSS y las dinámicas físicas?
3. ¿Se obtuvo una cota validada del error del Jacobiano?
4. ¿Se certificó rigurosamente que el Jacobiano exacto es Hurwitz?
5. ¿Puede afirmarse estabilidad exponencial local no lineal sin condiciones pendientes?
6. ¿Existe una región segura invariante certificada?
7. ¿La selección de escenarios H3 respetó los límites de tensión originales?
8. ¿Qué tan precisa es la desigualdad de reservas para todas las unidades?
9. ¿Qué resultados históricos deben quedar sustituidos o reinterpretados?
10. ¿Qué teoremas, proposiciones y resultados experimentales pueden incorporarse legítimamente al futuro artículo IEEE?

Decisión final obligatoria: clasificar cada afirmación como "RIGOROUSLY_CERTIFIED", "CONDITIONALLY_ESTABLISHED", "NUMERICALLY_SUPPORTED", "NOT_CERTIFIED" o "INVALIDATED".

Cerrar DEC-052 aunque no se obtengan todos los certificados ideales.

No proponer otra campaña automáticamente. El objetivo es terminar la validación científica de H3-R/H4-R, no prolongar indefinidamente la investigación.
