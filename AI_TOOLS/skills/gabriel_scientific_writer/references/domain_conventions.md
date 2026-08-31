# Convenciones de dominio: potencia, electronica de potencia, IBR, control

Referencia para `gabriel_scientific_writer`. Fija terminologia estable, unidades,
especificidad de hardware y la equivalencia exigible antes de comparar con la literatura.

## Contenido
- Terminologia estable (no sustituir por sinonimos)
- Unidades SI y notacion estandar
- Especificidad de hardware y magnitudes
- Fidelidad de modelo y nivel de validacion
- Checklist de equivalencia para comparacion con literatura
- Formulaciones prudentes de comparacion
- Formulaciones condicionadas (cuando falta un dato)

## Terminologia estable (no sustituir por sinonimos)

Elige un termino por concepto y repitelo. No alternes con variantes "elegantes".

| Concepto | Termino canonico | Evita |
|---|---|---|
| Inversor que sigue la red | `grid-following (GFL)` | current-source mode, following converter |
| Inversor que forma la red | `grid-forming (GFM)` | voltage-source formation, forming converter |
| Recurso basado en inversor | `inverter-based resource (IBR)` | inverter unit, power-electronic source |
| Control de area amplia | `wide-area control (WAMC)` | global control, remote control |
| Medicion de area amplia | `wide-area monitoring (WAMS)` | remote sensing |
| Minimo de frecuencia | `frequency nadir` | frequency dip, lowest frequency |
| Tasa de cambio de frecuencia | `RoCoF` | frequency slope, df/dt (en prosa) |
| Respuesta rapida de frecuencia | `fast frequency response (FFR)` | quick frequency support |
| Inercia sintetica | `synthetic inertia` / `virtual inertia` | fake inertia (fija una y usala) |
| Almacenamiento en baterias | `battery energy storage system (BESS)` | battery bank, storage unit |
| Bloqueo de fase | `phase-locked loop (PLL)` | phase tracker |
| Angulo de asistencia de area amplia | `wide-area angular assistance` | angle help, remote angle term |

Aplica la misma estabilidad a variables (`\omega`, `\theta`, `\lambda_g`, `\sigma_g`),
nombres de metodos, metricas y verbos de claim.

## Unidades SI y notacion estandar

- Magnitudes por unidad: `p.u.` (con punto). Potencia: `MW`, `MVA`, `Mvar`. Tension: `kV`, `V`.
- Frecuencia: `Hz`; RoCoF: `Hz/s`. Tiempo: `s`, `ms`, `\mu s`, `ns`.
- Reporta siempre valor + unidad + condicion: `nadir of 59.42~Hz under a 0.15~p.u. load step`.
- Espacio de no separacion antes de la unidad en LaTeX: `282~ns`, `60~Hz`, `2.4~GHz`.
- Porcentaje pegado al numero: `95.49\%`. Nivel de penetracion: `60\% IBR`.
- Notacion consistente para omega base: `\omega_0 = 2\pi \times 60`.

## Especificidad de hardware y magnitudes

Sustituye adjetivos cualitativos por el dato concreto. Nombra modelos cuando el CONTEXTO los da.

| Generico (evita) | Especifico (prefiere) |
|---|---|
| a fast controller | a controller with 282~ns actuation latency |
| a real-time simulator | OPAL-RT OP4510 running at 50~\mu s |
| a DSP | TMS320F28379D |
| high switching frequency | 100~kHz switching (GaN FET) |
| high IBR penetration | 60\% IBR penetration |
| a large battery | a 20~MWh / 10~MW BESS |
| low latency communication | a 20~ms one-way WAMS delay |

Si el CONTEXTO no da el modelo o el numero, no lo inventes: deja `[MISSING: modelo/latencia]`
o reformula condicionado.

## Fidelidad de modelo y nivel de validacion

Declara explicitamente ambos ejes; condicionan cualquier claim de desempeno.

- **Fidelidad:** EMT (electromagnetic transient) vs fasorial/RMS (phasor). Un resultado EMT
  captura dinamica de conmutacion y armonicos que un modelo fasorial no; no son intercambiables.
- **Validacion:** simulacion offline -> CHIL (controller-in-the-loop) -> PHIL (power hardware-in-the-loop)
  -> campo. El nivel alcanzado limita el alcance del claim.

Frases utiles: `The results were obtained in EMT simulation`; `validated in a CHIL setup on OPAL-RT`;
`under phasor-domain assumptions`.

## Checklist de equivalencia para comparacion con literatura

Antes de usar `outperform`, `superior`, `better`, `more robust`, `more effective`,
`significant improvement`, verifica que el trabajo comparado coincide en:

- [ ] sistema / benchmark (p. ej. IEEE 14-bus, Kundur two-area, isla real)
- [ ] topologia y escala
- [ ] nivel de penetracion IBR
- [ ] modo GFL / GFM de las unidades
- [ ] perturbacion evaluada (load step, trip, fault, RoCoF event)
- [ ] retardo de comunicacion / informacion disponible al controlador
- [ ] metrica reportada (nadir, RoCoF, settling time, ITAE, THD...)
- [ ] horizonte temporal del estudio
- [ ] solver y paso de integracion
- [ ] fidelidad de simulacion (EMT vs fasorial)
- [ ] nivel de validacion (simulacion, CHIL, PHIL, campo)
- [ ] restricciones fisicas (limites de corriente, SoC, rampas)
- [ ] condiciones operativas

Si **cualquier** casilla no coincide, no declares superioridad directa.

## Formulaciones prudentes de comparacion

Cuando no hay equivalencia directa:

- `For reference, [Author] reported a 59.6~Hz nadir under a 0.1~p.u. step in a phasor-domain study.`
- `A direct comparison is limited by differences in fidelity (EMT here vs. phasor in [X]) and validation level (PHIL vs. simulation).`
- `Under the evaluated conditions, the assisted case reduces the nadir deviation by 0.18~Hz relative to the local-only baseline.`
- `Within the considered IEEE 14-bus benchmark at 60\% IBR, ...`

Cierra siempre delimitando el alcance: sistema, penetracion, fidelidad y nivel de validacion.

Snippets LaTeX listos:

```latex
For reference, [Author] et al.~\cite{key} reported [metrica] using [metodo]
over [benchmark/condiciones]. A direct comparison is limited by differences in
fidelity ([EMT/phasor]), validation level ([sim/CHIL/PHIL]) and [otro factor].
```

```latex
Given these differences, the [metrica] reported here characterizes performance
within the [benchmark] at [X]\% IBR, rather than establishing cross-study superiority.
```

Frases a EVITAR: `outperforms all existing approaches`; `establishing direct performance parallels`;
cualquier declaracion de superioridad cuando banco, fidelidad o nivel de validacion no coinciden.

## Formulaciones condicionadas (cuando falta un dato)

Usa estas formulaciones para que la oracion funcione sin inventar el dato ausente.

| Situacion | Formulacion |
|---|---|
| Rango no especificado | `under the reported operating range` |
| Setup no detallado | `within the evaluated setup` |
| Generalizacion no probada | `within the tested benchmark` |
| Metrica no calculada | `based on the observed [metrica]` |
| Comparacion limitada | `under comparable evaluation conditions` |

Si el dato es critico y no hay forma de condicionar:
```latex
\textcolor{red}{[MISSING: descripcion precisa del dato necesario]}
```
