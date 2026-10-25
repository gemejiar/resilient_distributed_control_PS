# Resilient Distributed Control for Power Systems

Repositorio de investigación para formular y evaluar un controlador coordinado
CLF--HOCBF aplicado a regulación de frecuencia y tensión bajo restricciones de
operación. El sistema IEEE de 39 barras es el único banco de pruebas de la
campaña experimental. Los resultados y certificados permanecen pendientes
hasta que se ejecuten y validen las etapas definidas en `plan_maestro.md`.

## Fuentes de verdad

- `plan_maestro.md`: alcance, hipótesis, metodología, etapas, gates y acción
  actualmente autorizada.
- `AGENTS.md`: reglas científicas, editoriales y operativas compartidas por los
  agentes.
- `Paper_manuscript/main.tex`: manuscrito canónico.
- `ops/sted/decision_log.md`: decisiones metodológicas y editoriales.
- `ops/sted/traceability_matrix.csv`: trazabilidad de claims y evidencia.

Cuando exista una contradicción, se aplica la jerarquía definida en
`AGENTS.md`; este README es únicamente documentación de entrada para personas.

## Alcance experimental

- Sistema único: IEEE 39 barras.
- Configuración inicial E0--C0: caso original con 10 generadores síncronos y
  simulación sin perturbación.
- Evolución prevista: variantes mixtas SG--GFM y SG--GFM--GFL, incorporadas de
  manera progresiva y con un único cambio principal por gate.
- Fuera de alcance: reproducción experimental de los sistemas de 10 y 14
  buses del artículo de referencia.

El trabajo de Kavvathas y Konstantopoulos se utiliza como antecedente del
controlador RDC. Sus resultados no constituyen evidencia del comportamiento
del IEEE-39.

## Estado actual

E0--C0, E1--C0 y E2--C0 fueron aprobados por el investigador. Se completaron:

1. inventario del caso, modelos y entorno ANDES;
2. ejecución y aprobación humana de E0--C0 sin perturbación;
3. ejecución y aprobación de E1 con un incremento activo del 1% en el bus 4;
4. ejecución y aprobación de E2 con un incremento reactivo del 1% en el bus 21;
5. comprobación de signos físicos y convergencia al reducir el paso temporal;
6. generación de figuras y datos reproducibles de frecuencia, tensión, potencia
   y excitación de los SG.

La próxima etapa prevista es E3--C0a: sustitución exclusiva del SG del bus 32
por un GFM. Su ejecución comenzará cuando el investigador indique continuar.
Las etapas aprobadas no implican que el IEEE-39 esté validado o certificado.

## Organización principal

- `Paper_manuscript/cases/`: caso base y variantes reproducibles, sin alterar
  el archivo fuente original.
- `Paper_manuscript/src/`: código de ejecución, modelos de control y pruebas.
- `Paper_manuscript/artifacts/`: datos, series temporales, logs y matriz de
  resultados.
- `Paper_manuscript/figures_main/`: figuras de supervisión y publicación.
- `Paper_manuscript/ops/`: artefactos operativos propios del manuscrito cuando
  existan.
- `ops/`: controles y trazabilidad transversal del repositorio.
- `AI_TOOLS/`: capacidades reutilizables para agentes; no es evidencia
  científica.

Antes de trabajar, lea `AGENTS.md` y `plan_maestro.md`. No avance a E1 sin la
aprobación humana explícita de E0.
