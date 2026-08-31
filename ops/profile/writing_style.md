# writing_style.md — Reglas de estilo para escritura científica y técnica

**Propósito:** Guía de estilo para toda producción escrita generada en este workspace.
**Cuándo usar:** Antes de redactar o reescribir cualquier texto académico o técnico.
**Cuándo no usar:** No aplica para notas de sesión ni capture.md (esos son informales).
**Actualizar:** Solo si el usuario cambia preferencias de estilo o publica en un nuevo tipo de venue.

---

## Principios generales

1. **Técnico y verificable.** Cada afirmación debe ser respaldable por datos, ecuaciones o referencias. Evitar afirmaciones vagas como "el método es efectivo" sin evidencia cuantitativa.
2. **Frases directas.** Sujeto + verbo + complemento. Divide una oración cuando acumule varias relaciones causales independientes, demasiadas condiciones o una secuencia difícil de seguir; no midas por conteo de palabras (ver `gabriel_scientific_writer`, que fija esta misma regla y evita umbrales numéricos sin respaldo de corpus).
3. **Sin adornos.** No usar frases como "es importante destacar que", "cabe mencionar que", "resulta evidente que". Ir directo al punto.
4. **Definir siglas la primera vez.** Format: nombre completo (SIGLA). Ejemplo: *energy management system* (EMS). No redefinir en el mismo documento.
5. **Separar hechos de inferencias.** En papers: los hechos en Results, las inferencias y su justificación en Discussion. No mezclar.
6. **Consistencia terminológica.** Elegir un término y usarlo siempre. No alternar *microgrid* / *micro-grid* / *MG* sin razón.
7. **Unidades SI siempre.** kW no KW. V no v. Hz no hz. Espacio entre número y unidad: 100 kW, no 100kW.
8. **Tiempo verbal consistente.** Methods: pasado simple. Results: pasado simple. Discussion/Conclusion: presente para afirmaciones generales.

---

## Estilo IEEE

- Evitar primera persona singular ("I propose"). Usar primera persona plural o voz pasiva: "This paper proposes...", "The results show...", "A control strategy is developed..."
- Abstract: máximo 250 palabras. Estructura: contexto, problema, método, resultados principales, conclusión principal.
- Sin subsecciones en el abstract.
- Ecuaciones numeradas secuencialmente: (1), (2), ...
- Figuras: Fig. 1, Fig. 2 (no Figure).
- Tablas: TABLE I, TABLE II (versalitas).
- Referencias: formato IEEE ([1], [2]...). No usar autor-año en texto.

---

## Estilo Elsevier (Applied Energy, EPSR, IJEPES)

- Primera persona permitida en algunos journals. Verificar instrucciones del journal específico.
- Abstract estructurado cuando se requiera: Background, Methods, Results, Conclusions.
- Referencias: formato autor-año si el journal lo requiere, o numérico si lo requiere.
- Secciones numeradas: 1. Introduction, 2. System Model, etc.

---

## Estructura de un párrafo técnico bien escrito

```
[Oración temática: la idea central del párrafo]
[Soporte técnico: evidencia, ecuación, dato o referencia que la respalda]
[Elaboración: explicación o desarrollo necesario]
[Implicación o transición: qué significa para el argumento o qué sigue]
```

Cada párrafo debe tener una sola idea central. Si tiene dos, separar.

---

## Errores frecuentes a evitar

| Error | Corrección |
|---|---|
| "The results are good" | "The proposed controller reduces frequency deviation by 42% compared to [ref]" |
| "As mentioned before" | Eliminar o reformular |
| "It is worth noting that" | Eliminar. Decir directamente. |
| "In order to" | Reemplazar por "To" |
| "Due to the fact that" | Reemplazar por "Because" |
| Mezclar tiempos verbales | Verificar consistencia por sección |
| Siglas sin definir | Definir siempre en la primera aparición |
| Números solos sin unidad | Siempre incluir unidad o contexto |
| Referencias a futuros trabajos sin concretar | Eliminar o concretar |

---

## Para textos en español (docencia, correos)

- Tono formal, sin tuteo salvo instrucción explícita.
- Evitar anglicismos innecesarios cuando existe equivalente en español técnico establecido.
- Excepciones aceptadas: *feedback*, *hardware*, *software*, *benchmark* (uso extendido en la disciplina).
- Tildes y ortografía correctas. Sin excepción.
- Correos formales: apertura formal + cuerpo conciso + cierre formal.
