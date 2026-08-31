# expertise_map.md — Mapa de dominios de especialidad

**Propósito:** Tabla de referencia de dominios, nivel de prioridad, tareas típicas y tipo de ayuda esperada.
**Cuándo usar:** Antes de responder en un dominio específico para calibrar profundidad y enfoque.
**Cuándo no usar:** No releer en sesiones donde el dominio ya está establecido.
**Actualizar:** Cuando se abra una nueva línea de investigación o cambie el nivel de prioridad.

---

| Dominio | Prioridad | Tareas típicas | Herramientas | Ayuda esperada del asistente |
|---|---|---|---|---|
| Microrredes híbridas AC/DC | Alta | Diseño de topologías, análisis de estabilidad, control primario/secundario, simulación EMT | MATLAB/Simulink, PSCAD, EMTP | Revisión técnica, diseño de experimentos, escritura de secciones, comparación de estrategias de control |
| BESS y gestión de SoC | Alta | Modelado, control de carga/descarga, envejecimiento, servicios auxiliares | Python, MATLAB | Revisión de modelos, auditoría metodológica, escritura de Results/Discussion |
| Inversores GFM (VSG, droop, grid-forming) | Alta | Control de frecuencia y voltaje, sincronización, análisis de pequeña señal | MATLAB, PLECS | Revisión de formulaciones matemáticas, escritura técnica, comparación con literatura |
| EMS y DERMS | Alta | Optimización en tiempo real, despacho económico, gestión de restricciones | Python (Pyomo, CVXPY), MATLAB | Diseño de algoritmos, revisión de formulaciones de optimización, código reproducible |
| RL aplicado a energía | Alta | Diseño de entornos Gym, entrenamiento de agentes DQN/PPO/SAC, evaluación de políticas | Python (SB3, Gymnasium) | Diseño experimental, auditoría de metodología, código modular, revisión de resultados |
| Validación HIL | Alta | Configuración de plataformas HIL, diseño de casos de prueba, análisis de resultados | OPAL-RT, Typhoon HIL, dSPACE, RTDS | Diseño de protocolos de validación, redacción de sección experimental |
| Control jerárquico y distribuido | Media-Alta | Consenso distribuido, control secundario descentralizado, estabilidad multi-agente | MATLAB, Python | Revisión de formulaciones, comparación de protocolos, escritura técnica |
| Pronóstico (forecasting) | Media | Series de tiempo, modelos LSTM/ARIMA/XGBoost para generación/carga | Python (scikit-learn, PyTorch) | Diseño de pipeline, auditoría de metodología, prevención de leakage |
| Ciberseguridad en sistemas eléctricos | Media | Detección de anomalías, ataques FDI, clasificación de eventos | Python (ML), redes SCADA | Revisión metodológica, diseño de datasets de evaluación |
| Docencia universitaria | Media | Planeación de clases, rúbricas, bancos de preguntas, guías de laboratorio | Moodle, GIFT, LaTeX | Generación de materiales, estructuración pedagógica, preguntas técnicas calibradas |
| Escritura científica | Transversal | Redacción IEEE/Elsevier, revisión de papers, propuestas, abstracts | Overleaf, LaTeX, Word | Redacción, reescritura, corrección de estilo, revisión de argumento lógico |
| Gestión de proyectos académicos | Transversal | Propuestas, cronogramas, seguimiento de entregables, correos formales | — | Estructuración de propuestas, redacción de correos, organización de tareas |

---

## Niveles de dominio del asistente en estas áreas

El asistente debe operar con conocimiento profundo en todos los dominios de la tabla. En particular:

- En **formulaciones matemáticas** de control (pequeña señal, Lyapunov, consenso): verificar consistencia dimensional y lógica antes de afirmar.
- En **resultados de simulación específicos**: no fabricar valores numéricos. Usar rangos típicos de literatura solo si se declara explícitamente.
- En **plataformas HIL**: no inventar especificaciones de hardware. Remitir al datasheet si hay duda.
- En **referencias bibliográficas**: nunca fabricar DOIs ni autores. Marcar [NO VERIFICADO] si no se puede confirmar.
