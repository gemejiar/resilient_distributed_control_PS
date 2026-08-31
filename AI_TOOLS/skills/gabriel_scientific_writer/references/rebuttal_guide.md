# Guia de respuesta a revisores (rebuttal / point-by-point)

Referencia para `gabriel_scientific_writer`. Casi ningun journal Q1 acepta un manuscrito sin al
menos una ronda de revision. Redactar la respuesta a revisores es tarea de esta skill: aplica las
mismas reglas de trazabilidad y sobriedad que el resto del paper, con su propio patron retorico.

## Contenido
- Estructura del documento de respuesta
- Patron por comentario: acknowledge -> action -> evidence -> location
- Tipos de respuesta segun lo que pide el revisor
- Tono: firme sin ser defensivo
- Texto marcado en el manuscrito revisado
- Ejemplos

## Estructura del documento de respuesta

1. Parrafo breve de apertura: agradecimiento y resumen de los cambios principales (3-5 frases,
   sin detalle tecnico todavia).
2. Un bloque por comentario del revisor, en el mismo orden en que el revisor los presento,
   agrupado por revisor (`Reviewer 1, Comment 1`, `Reviewer 1, Comment 2`, ...).
3. Cierre opcional solo si hay cambios transversales que afectan a varios comentarios a la vez.

No reordenes los comentarios del revisor "para que fluyan mejor": el revisor los recorre en su
orden original al verificar la respuesta.

## Patron por comentario: acknowledge -> action -> evidence -> location

Cada comentario respondido sigue el mismo patron de cuatro pasos:

1. **Acknowledge** — cita o parafrasea el comentario sin distorsionarlo.
2. **Action** — que se hizo: se agrego, se corrigio, se aclaro, o por que no se hizo.
3. **Evidence** — el dato, resultado o referencia que sostiene la accion (mismo estandar de
   `SKILL.md` regla 1: cada respuesta tecnica se ancla a algo verificable).
4. **Location** — donde quedo el cambio en el manuscrito revisado (`p. 4, Section III-B`,
   `Eq. (7)`, `Table 3`).

```latex
\textbf{Comment 1:} The authors claim the scheme reduces the frequency nadir but do not report
the baseline case explicitly.

\textbf{Response:} We thank the reviewer for this observation. We added the local-only baseline
(C1) explicitly to Table 3 and to the discussion in Section V-B, reporting a nadir of 59.24~Hz
for C1 versus 59.42~Hz for the wide-area-assisted case under the same 0.15~p.u. load step.
This change appears in Table 3 (p. 7) and Section V-B (p. 8), highlighted in blue.
```

## Tipos de respuesta segun lo que pide el revisor

- **Cambio aceptado y aplicado:** Action = descripcion concreta del cambio + Location.
- **Aclaracion sin cambiar el manuscrito:** cuando el punto ya estaba cubierto pero no se vio
  con claridad, explica donde estaba y considera reforzarlo (a menudo si conviene anadir una
  frase, aunque el revisor solo pidiera claridad).
- **Desacuerdo fundamentado:** permitido, pero exige evidencia o argumento tecnico explicito, no
  una negacion retorica. Sigue la misma regla que un overclaim: sin ancla, no se sostiene.
  ```latex
  \textbf{Response:} We respectfully disagree. The 20~ms delay used here matches the reported
  WAMS latency in [cite], and reducing it further would not reflect realistic communication
  conditions for this benchmark.
  ```
- **Peticion fuera de alcance (nuevo experimento no factible en la ronda actual):** reconoce el
  valor del punto, explica la limitacion honesta (tiempo, alcance, datos no disponibles), y
  ofrecelo como trabajo futuro si aplica. No prometas un resultado que no puedes producir.

## Tono: firme sin ser defensivo

- Sin acusar al revisor de no entender el paper. Si un punto parece un malentendido, la causa
  casi siempre es que el manuscrito no fue lo bastante claro; se corrige la claridad, no se
  corrige al revisor.
- Sin hedging excesivo ("we believe", "we think") en respuestas donde hay un dato que zanja el
  punto: usa el dato directamente.
- Sin `we categorically reject` ni formulas de conflicto. Ver `references/domain_conventions.md`
  y `references/style_rules.md` para el registro de voz y hedging que aplica igual aqui.

## Texto marcado en el manuscrito revisado

Si el journal pide (o el proyecto usa) marcado de cambios, aplica el mismo sistema de colores que
`SKILL.md` regla 3 exige para el resto del documento: `\textcolor{blue}{...}` para texto nuevo o
modificado en respuesta a revision. No inventes un sistema de marcado distinto para el rebuttal.

## Ejemplos

**Comentario sobre comparacion invalida:**
```latex
\textbf{Comment 3:} The comparison with [Author, year] seems unfair given the different
simulation fidelity.

\textbf{Response:} We agree and have rewritten the comparison (Section VI, p. 9) to state
explicitly that [Author, year] used a phasor-domain model while this work uses EMT simulation,
and that the reported numbers characterize performance within each study's own fidelity level
rather than establishing direct superiority.
```

**Comentario que exige un experimento adicional no disponible:**
```latex
\textbf{Comment 5:} Please validate the scheme under communication delay variability.

\textbf{Response:} We thank the reviewer for raising this. The current study assumes a fixed
20~ms wide-area delay (Assumption 2, Section III), consistent with the reported WAMS latency in
[cite]. Evaluating delay variability requires an additional CHIL campaign beyond the scope of
this revision; we have added this explicitly as future work in Section VII (p. 10).
```
