# Patrones retoricos por seccion, plantillas y frases tipo

Referencia para `gabriel_scientific_writer`. Detalla el patron `framework -> method -> verification`
por seccion, con plantillas rellenables y frases tipo (EN/ES). Los ejemplos usan el dominio de
potencia/control; adaptalos al CONTEXTO. Guia flexible, no molde rigido: ajusta al venue.

## Contenido
- Title, Highlights, keywords
- Abstract
- Introduction
- Methods (los 12 puntos de CLAUDE.md)
- Results
- Discussion
- Conclusion
- Captions de figuras y tablas
- Frases tipo de transicion (EN / ES)

## Title, Highlights, keywords

Esta es la parte que decide el desk-reject: editor y revisor triagen por titulo, highlights,
abstract y figuras antes de leer el cuerpo. No es una seccion menor.

**Title:** especifico, sin retorica. Nombra el mecanismo o el sistema, no una promesa vacia.
- Mal: `A Novel and Robust Approach for Enhanced Grid Stability`
- Bien: `Wide-Area Angular Assistance for Grid-Following BESS Under High IBR Penetration`

**Highlights** (Elsevier, `cas-dc` y similares): 3-5 bullets, **maximo 85 caracteres cada uno**
(incluyendo espacios), un claim verificable por bullet, sin adjetivos sin metrica.
```latex
\begin{Highlights}
\item Wide-area angular assistance reduces frequency nadir deviation by 0.18 Hz.
\item Validated on the IEEE 14-bus benchmark at 60% IBR penetration.
\item GFL current stays within 1.2 p.u. under the evaluated load steps.
\end{Highlights}
```
Cada highlight se ancla a un resultado real del CONTEXTO (nunca a una aspiracion). Si no hay
un resultado que sostenga el bullet, no lo escribas: faltan datos, no adjetivos.

**Keywords:** 4-6 terminos, del vocabulario estable del campo (ver `domain_conventions.md`), sin
inventar terminologia nueva. Orden: mas general -> mas especifico.

## Captions de figuras y tablas

El caption es autocontenido: un lector debe entender la figura/tabla sin volver al texto.
Incluye siempre: que se muestra, condicion/escenario, y unidad de los ejes o columnas relevantes.

**Mal:** `Fig. 3. Simulation results.`
**Bien:** `Fig. 3. Frequency response at bus 5 under a 0.15 p.u. load step at $t=1$~s, comparing the
wide-area-assisted case (solid) against the local-only baseline (dashed). Nadir values in Hz.`

No describas en el caption mas de lo que la figura muestra (ver Coherencia cruzada en SKILL.md).

## Abstract

Orden: problema -> brecha -> contribucion -> metodo -> verificacion (metrica/condicion) -> implicacion prudente.

Una a dos frases por elemento. Sin citas. Sin acronimos no definidos salvo los del titulo.

Plantillas:
- Problema: `The [problema] in [dominio] limits [consecuencia].`
- Brecha: `Existing approaches [limitacion], which restricts [aspecto].`
- Contribucion: `This work proposes [sistema/metodo] that [accion concreta].`
- Verificacion: `In [EMT/phasor] simulation on [benchmark] at [X]% IBR, the [metodo] achieved [metrica] under [condicion].`
- Implicacion: `These results indicate that [conclusion condicionada, p. ej. within the evaluated benchmark].`

La verificacion lleva al menos una metrica con condicion. La implicacion es condicionada:
`within the evaluated benchmark`, nunca `in all grids`.

## Introduction

Orden: contexto -> limitacion del estado del arte con evidencia -> objetivo/contribucion -> organizacion.

El gap se sustenta con evidencia, no con retorica: nombra que falta y por que importa.

Plantillas para definir el gap:
- `Despite advances in [area], there is limited evidence of [aspecto especifico] validated with [EMT/CHIL/PHIL] under [condiciones].`
- `Most existing results assume [supuesto], and the gap between [aspecto teorico] and [aspecto operativo] requires validation at [nivel de fidelidad/validacion].`
- `While [metodo] has been proposed for [aplicacion], it requires [limitacion concreta].`

Contribuciones: patron **preferente en IEEE** cuando el usuario pide una introduccion completa de
articulo. No es obligatorio en todo venue, formato corto o estructura ya aprobada.
- `The main contributions of this work are:` + `\begin{enumerate}` con items concretos.
- Cada contribucion: un verbo de accion + un resultado medible o una capacidad verificable.
- Cierra con: `The remainder of this paper is organized as follows.`

## Methods (los 12 puntos de CLAUDE.md)

`CLAUDE.md` exige que una seccion de metodologia cubra, cuando aplique, estos 12 elementos. No
todos necesitan un parrafo propio; varios se resuelven en 1-2 frases, pero ninguno debe faltar
en silencio si el CONTEXTO trae la informacion. Orden sugerido (adaptalo al flujo natural):

1. **Sistema bajo estudio** — benchmark, topologia, escala: `The scheme is evaluated on the IEEE 14-bus system with two GFL BESS units at buses 5 and 9.`
2. **Baselines / supuestos de comparacion** — que se compara contra que: `Three baselines are considered: local-only control (C1), ... (C3).`
3. **Capa de datos / medicion** — que se mide, con que sensor o canal: `Frequency is measured via PMU streams at 50 samples/cycle.`
4. **Workflow / algoritmo central** — el nucleo tecnico; aqui van las ecuaciones (ver `math_writing.md`).
5. **Objetivo / hipotesis** — que se espera demostrar: `The hypothesis is that earlier angular correction reduces the nadir without violating current limits.`
6. **Plataforma de implementacion** — software/hardware: `Implemented in MATLAB/Simulink and validated in CHIL on an OPAL-RT OP4510.`
7. **Adquisicion / preprocesamiento** — de donde vienen los datos de entrada, cualquier filtrado: `RoCoF is estimated from the PMU frequency signal using a [N]-sample moving window.`
8. **Ejecucion / actuacion** — como se aplica la decision: `The activation gain $\lambda_g$ modulates the angle reference in real time (Section III-B).`
9. **Escenarios de prueba** — perturbaciones evaluadas: `Three load steps (0.05, 0.10, 0.15 p.u.) and one generator trip are evaluated.`
10. **Metricas de desempeno** — que se reporta: `Frequency nadir, RoCoF, and settling time are reported for each scenario.`
11. **Parametros de reproducibilidad** — solver, paso, semillas, versiones: `Simulations use a variable-step ode23tb solver with a maximum step of 1~ms.`
12. **Limitaciones del metodo** — que el metodo no cubre (breve, tecnico, no retorico): `The formulation assumes a single wide-area link without communication delay variability.`

Si el CONTEXTO no trae informacion para uno de estos puntos y es relevante para el claim del
paper, no lo omitas silenciosamente: marca `[MISSING: parametro de reproducibilidad]` o similar,
igual que con cualquier otro dato faltante.

Introduce cada ecuacion con su rol antes de escribirla: `The assistance term is defined as` (1).
La configuracion fija: sistema/benchmark, fidelidad (EMT/fasorial), solver y paso, hardware
(ver `domain_conventions.md`) y nivel de validacion.

## Results

Orden: escenario -> metrica -> comparacion valida -> interpretacion causal corta.

Un escenario por bloque; nombra la perturbacion y las condiciones. Describe exactamente lo que
muestran figuras/tablas; no amplifiques. La comparacion respeta la equivalencia de banco/fidelidad
(`domain_conventions.md`).

Plantillas:
- `On [benchmark] at [X]% IBR, the [metodo] reduced the [metrica] by [valor+unidad] under a [perturbacion] (Fig.~\ref{...}).`
- `The largest deviation ([valor]) occurred under [escenario], consistent with [mecanismo].`

La interpretacion causal es breve y anclada: `The earlier angular assistance limits the nadir because ...`.

## Discussion

Orden: interpretacion -> limites -> generalizacion condicionada -> trabajo futuro.

Separa lo demostrado de lo plausible. Nombra limites reales: fidelidad, escala del benchmark,
supuestos, latencias no modeladas.

Plantilla:
- `These results are specific to [benchmark], [fidelidad] and [nivel de validacion]; generalization to [otro contexto] was not assessed.`

## Conclusion

- 2-4 hallazgos verificables (cada uno reconducible a un resultado del paper).
- 1 implicacion practica condicionada. Sin claims nuevos que no aparezcan en Results.

Plantilla:
- `This work validated [sistema] for [aplicacion] under [condiciones]. Future work will address [aspecto concreto].`

## Frases tipo de transicion

Usa un conector solo cuando introduzca un paso logico real con anclaje concreto.

**EN:** `however`, `thus`, `therefore`, `since`, `consequently`, `in contrast`, `notably`,
`In this context,`, `Nevertheless` (para marcar el gap), `Aiming to [verb], ...` (proposito).

**ES:** `sin embargo`, `asi`, `por lo tanto`, `dado que`, `en consecuencia`, `en contraste`,
`cabe destacar`, `con el fin de`.

Anclajes concretos preferidos sobre conectores genericos:
`Under constraint (3)...`, `Given the measured RoCoF...`, `At 60\% IBR penetration...`,
`This configuration...`.
