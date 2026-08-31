# Disciplina de escritura matematica

Referencia para `gabriel_scientific_writer`. Un paper de control/potencia Q1 se juzga tanto por su
matematica como por su prosa. Estas reglas cubren lo que la preservacion de LaTeX (SKILL.md regla 3)
no cubre: como redactar alrededor de una ecuacion, no solo como no rompaerla.

## Contenido
- Definicion de simbolos
- Puntuacion de ecuaciones
- Claims formales: solo con respaldo formal
- Supuestos como objetos numerados
- Consistencia notacional entre secciones
- Checklist matematico

## Definicion de simbolos

Cada simbolo se define la primera vez que aparece, con su unidad si es fisico. Una ecuacion sin
`where` completo obliga al revisor a inferir; eso es fallo de escritura, no de contenido.

**Mal:**
```latex
\begin{equation}
\dot{\omega} = -\frac{1}{2H}(P_e - P_m)
\end{equation}
```
(sin definir $H$, $P_e$, $P_m$, ni sus unidades)

**Bien:**
```latex
\begin{equation}
\dot{\omega} = -\frac{1}{2H}(P_e - P_m)
\label{eq:swing}
\end{equation}
where $\omega$ is the per-unit frequency deviation, $H$ is the inertia constant (s), and
$P_e$, $P_m$ are the electrical and mechanical power (p.u.), respectively.
```

Si un simbolo ya fue definido en una seccion anterior, no lo redefinas: referencia la ecuacion
donde se definio (`as defined in (3)`) en vez de repetir la clausula `where`.

## Puntuacion de ecuaciones

La ecuacion es parte de la oracion, no un objeto aislado. Termina con coma o punto segun continue
o cierre la frase; la clausula `where` empieza en minuscula tras la ecuacion.

```latex
The assistance term is added to the local angle reference as
\begin{equation}
\theta_{ref} = \theta_{local} + \lambda_g \, \Delta\theta_{wa},
\label{eq:theta_ref}
\end{equation}
where $\lambda_g \in [0,1]$ is the activation gain and $\Delta\theta_{wa}$ is the wide-area
angular correction.
```

## Claims formales: solo con respaldo formal

Terminos con significado tecnico preciso en control **no se usan como adjetivos retoricos**. Cada
uno exige el argumento correspondiente en el CONTEXTO; si no esta, no se usa el termino.

| Termino | Exige en el CONTEXTO |
|---|---|
| `asymptotically stable` / `stability is guaranteed` | Lyapunov, eigenvalores, o criterio de estabilidad explicito |
| `passive` / `passivity` | funcion de almacenamiento o argumento de pasividad |
| `robust` (en sentido tecnico, no retorico) | analisis de sensibilidad, margen, o rango de incertidumbre acotado |
| `optimal` | formulacion de un problema de optimizacion y su solucion |
| `ISS` (input-to-state stable) | funcion ISS-Lyapunov o cita que lo demuestre |
| `converges` | analisis de convergencia (tasa, condicion, o prueba) |

Si el CONTEXTO no trae el argumento, no escribas el termino: usa una formulacion condicionada
(`simulation results indicate...`, ver `references/domain_conventions.md`) o marca
`[MISSING: analisis de estabilidad/pasividad/...]`. Esto es la version matematica del contrato de
`forbidden_wording`: un overclaim formal es tan grave como un overclaim numerico.

## Supuestos como objetos numerados

Cuando un claim depende de un supuesto (linealizacion, rango de operacion, ausencia de saturacion),
declaralo como objeto explicito, no como inciso perdido en una oracion:

```latex
\begin{assumption}
The GFL converter current remains within its rated limit ($|i| \le 1.2$~p.u.) throughout the
evaluated scenarios.
\label{as:current_limit}
\end{assumption}
```

Referencia el supuesto donde su violacion afectaria el resultado: `Under Assumption~\ref{as:current_limit}, ...`.
Si el documento no usa el entorno `assumption` (revisa el CONTEXTO), integra el supuesto en prosa
con la misma explicitud, sin diluirlo: `This result assumes the GFL current stays within...`.

## Consistencia notacional entre secciones

Un simbolo no cambia de significado entre Methods y Results. Si $\lambda_g$ es la ganancia de
activacion en la Seccion III, no reaparezca como otra cosa en la Seccion V. Si el CONTEXTO trae
una colision notacional real (dos papers fuente usan la misma letra para cosas distintas),
senalala explicitamente en vez de fusionar en silencio; en modo diagnostico, repórtala como hallazgo.

## Checklist matematico

Antes de entregar texto con ecuaciones, verifica:

- [ ] Cada simbolo nuevo tiene clausula `where` con unidad (si aplica)
- [ ] Ningun simbolo se redefine con otro significado en otra seccion
- [ ] La ecuacion esta puntuada como parte de la oracion
- [ ] Ningun termino formal (`stable`, `passive`, `optimal`, `ISS`, `converges`) aparece sin su
      argumento de respaldo en el CONTEXTO
- [ ] Los supuestos criticos estan explicitos (numerados o en prosa clara), no implicitos
- [ ] Las ecuaciones estan numeradas y referenciadas como `(N)`, no repetidas literalmente
