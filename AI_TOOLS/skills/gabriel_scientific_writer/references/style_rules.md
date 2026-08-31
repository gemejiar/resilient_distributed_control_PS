# Reglas de estilo funcionales con ejemplos (dominio de potencia/control)

Referencia para `gabriel_scientific_writer`. Amplia las reglas criticas del `SKILL.md`
con su justificacion y ejemplos antes/despues del dominio. Reglas **funcionales**: no
hay cuotas numericas ni heuristicas anti-deteccion. El objetivo es prosa publicable en
IEEE/Elsevier, no evadir detectores de IA.

## Contenido
- Prosa sobria vs inflada
- Adjetivos sin metrica
- Estabilidad terminologica
- Verbos de claim (no rotar por rotar)
- Voz y uso de `we`
- Hedging por tipo de afirmacion
- Conectores con anclaje
- Division de oraciones
- Comparacion prudente
- Interferencia ES->EN (errores frecuentes de hispanohablantes)
- Division de oraciones
- Comparacion prudente

## Prosa sobria vs inflada

Los revisores detectan de inmediato la prosa grandilocuente. Misma informacion, menos palabras, cero adjetivos vacios.

**Inflada:**
```latex
Ultimately, the empirical verification explicitly demonstrates that coupling a wide-area angular
assistance scheme to a conventional grid-following battery guarantees robust and stable frequency
support under all operating conditions, thereby solidifying the operational viability of the proposal.
```
**Sobria:**
```latex
In EMT simulation on the IEEE 14-bus benchmark at 60\% IBR, the wide-area angular assistance reduces
the frequency nadir deviation by 0.18~Hz under a 0.15~p.u. load step, relative to the local-only baseline.
```

## Adjetivos sin metrica

Sustituye cada adjetivo cualitativo por su dato.

| Evita | Prefiere |
|---|---|
| a robust controller | a controller that keeps RoCoF below 0.5~Hz/s |
| a significant improvement | a 0.18~Hz reduction in nadir deviation |
| an efficient response | a 282~ns actuation latency |
| strong damping | a damping ratio of 0.32 |

## Estabilidad terminologica

Cambiar el nombre de un concepto entre parrafos confunde al revisor.

**Mal:** el texto alterna `grid-forming control`, `forming mode`, `voltage-source formation`.
**Bien:** `grid-forming control` en todo el texto. Ver tabla en `domain_conventions.md`.

## Verbos de claim (no rotar por rotar)

Cada verbo implica un nivel de evidencia distinto; no son sinonimos.

- `proposes` / `presents` -> introduce una idea o metodo (sin evidencia aun)
- `formulates` / `derives` -> construye el modelo
- `evaluates` / `assesses` -> mide bajo condiciones
- `demonstrates` / `shows` -> respalda con resultados
- `validates` / `confirms` -> verifica frente a una referencia o hardware

Repite el verbo tecnicamente correcto cuando corresponda. Varia solo cuando cambie la accion
o el nivel de evidencia. No sustituyas `validates` por `demonstrates` solo para "no repetir".

## Voz y uso de `we`

Prefiere el sujeto tecnico o la voz activa impersonal. Usa `we` con moderacion cuando aclare
una decision autoral y evite repetir `this work` tres veces seguidas.

**Repetitivo:** `This work proposes... This work evaluates... This work compares...`
**Mejor:** `This work proposes... We then evaluate the scheme under three load steps and compare it against a local-only baseline.`

Pasiva selectiva para implementacion/medicion: `was implemented on OPAL-RT`, `were measured at the PCC`.

## Hedging por tipo de afirmacion

- **Dato medido / definicion:** lenguaje firme. `The nadir is 59.42~Hz.` No `may be around`.
- **Interpretacion causal:** moderado. `The earlier assistance likely limits the nadir because ...`
- **Generalizacion:** condicionado. `Within the evaluated benchmark, the scheme can ...`
- **Extrapolacion:** explicitamente limitado. `Extending this to meshed HVDC grids remains untested.`

No acumules hedging en serie (`may potentially be likely to`).

## Conectores con anclaje

Usa un conector solo si en la misma oracion hay un anclaje concreto (condicion, restriccion,
metrica, comparacion). No inicies todos los parrafos con conector.

**Ornamental:** `Furthermore, the method is very effective. Moreover, it is robust.`
**Anclado:** `Under constraint (3), the current stays below 1.2~p.u.; consequently, the GFL unit avoids saturation.`

## Division de oraciones

Divide cuando la oracion acumule varias relaciones causales independientes, demasiadas
condiciones o una secuencia dificil de seguir. No dividas una derivacion que necesita
subordinacion para su precision.

**Sobrecargada:** `Because the delay is 20~ms and the penetration is 60\% and the GFL unit
saturates at 1.2~p.u., the nadir degrades, so the wide-area term is added, which restores it.`
**Dividida:** `The 20~ms delay and 60\% penetration drive the GFL unit to its 1.2~p.u. current limit,
degrading the nadir. The wide-area angular term is added to restore it.`

## Comparacion prudente

Ver el checklist de equivalencia en `domain_conventions.md`. Regla corta: no declares
superioridad si el banco de pruebas, la fidelidad (EMT vs fasorial) o el nivel de validacion
(simulacion/CHIL/PHIL/campo) no coinciden. Usa `For reference, ...` o `A direct comparison is limited by ...`.

## Interferencia ES->EN (errores frecuentes de hispanohablantes)

Cuando el CONTEXTO o el borrador vienen del espanol, revisa estos calcos frecuentes. Corrigelos
sin cambiar el significado tecnico.

| Calco del espanol | Correccion en EN |
|---|---|
| `allows to obtain` / `allows to reduce` | `allows [gerund]: obtaining / reducing` o `makes it possible to obtain` |
| `the equation (3) shows` | `Equation (3) shows` / `(3) shows` (sin articulo antes del numero) |
| `an information` / `a research` (incontables usados como contables) | `information`, `research` (sin articulo, o `a piece of information`) |
| `actual conditions` (falso amigo: `actual`=real, no `current`) | `current conditions` si el sentido es "presentes" |
| `realize an experiment` (calco de "realizar") | `perform an experiment` / `conduct an experiment` |
| `the proposed methodology pretends to` (calco de "pretende") | `the proposed methodology aims to` |
| `data is` (tratado como singular por analogia con "el dato es") | en registro formal de journal, `data are` (plural) salvo que el venue acepte `data is` |
| Oraciones de una sola frase muy larga con multiples "que" subordinados encadenados | dividir siguiendo la regla de "Division de oraciones" arriba |
| Uso sistematico de gerundio donde el ingles prefiere infinitivo (`for reducing the nadir` cuando el proposito es `to reduce`) | `to reduce the nadir` para proposito; gerundio solo tras preposicion o como sujeto |

Si tienes duda entre dos formas y ambas son gramaticales, prefiere la mas corta y la que ya
aparece en el CONTEXTO o en las referencias citadas del mismo campo.
