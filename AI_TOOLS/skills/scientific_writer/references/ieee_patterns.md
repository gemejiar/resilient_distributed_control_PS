# IEEE Patterns Reference

Referencia rapida de patrones, frases tipo y errores frecuentes para redaccion IEEE/Elsevier.
Consulta este archivo cuando necesites orientacion sobre formulaciones especificas por seccion.

## Table of Contents
1. Frases tipo por seccion
2. Patrones de comparacion con literatura
3. Formulaciones condicionadas (cuando falta un dato)
4. Errores frecuentes y correcciones
5. Checklist de revision final

---

## 1. Frases tipo por seccion

### Abstract
- Problema: "The [problem] in [domain] limits [consequence]."
- Brecha: "Existing approaches require [limitation], which restricts [aspect]."
- Contribucion: "This work proposes [system/method] that [accion concreta]."
- Resultado: "Under [protocol], the [model] achieved [metric]% [measure] across [scope]."
- Implicacion: "These results indicate that [conclusion condicionada]."

### Introduction — definir el gap
- "Despite advances in [area], there is limited documentation of [aspecto especifico] validated with [tipo de datos] in [contexto]."
- "Most existing results stem from [tipo de benchmark], and the gap between [aspecto teorico] and [aspecto practico] requires empirical evidence."
- "While [metodo/tecnologia] has been proposed for [aplicacion], it requires [limitacion concreta]."

### Introduction — contribuciones
- "The main contributions of this work are:"
- Usar `\begin{enumerate}` con items concretos y verificables
- Cada contribucion debe tener un verbo de accion y un resultado medible
- Ejemplo: "A comparative evaluation of five classifiers, confirming that [model] achieves [metric]% under [conditions]."

### Methods — describir pipeline
- "The methodology follows [N] stages: [lista breve]."
- "The [component] was configured with [parametros especificos]."
- "Hyperparameter selection was performed via [metodo] over the ranges listed in Table~\ref{tableX}."

### Results — reportar hallazgos
- "The [model] achieved [metric]% $\pm$ [std]% under [protocol] (Table~\ref{tableX})."
- "Misclassifications were concentrated between classes [X] and [Y], suggesting [interpretacion breve]."
- "The highest error rate ([N] out of [M] observations) was observed in [model/clase]."

### Discussion — delimitar alcance
- "These results are specific to the tested [entorno] and [condiciones]; generalization to [otro contexto] was not assessed."
- "The [N]-observation dataset is moderate compared to [benchmark]; temporal stability under varying conditions requires further investigation."

### Conclusion — cerrar
- "This work validated [sistema] for [aplicacion] in [contexto]."
- "Future work will focus on [aspecto concreto] and [aspecto concreto]."

---

## 2. Patrones de comparacion con literatura

### Comparacion prudente (recomendado)
```latex
For reference, [Author] et al.~\cite{key} reported [metric]\% [measure]
using [method] over [dataset/conditions]. Direct comparison is limited
by differences in [factor1], [factor2], and [factor3].
```

### Contextualizacion sin declarar superioridad
```latex
Independent evaluations report varying capabilities depending on sensing
infrastructure and evaluation protocol. [Author]~\cite{key} achieved
[X]\% using [N] APs in a [description] setup, while [Author]~\cite{key}
reported [Y]\% with [different conditions].
```

### Cierre de comparacion
```latex
Given these methodological differences, the [metric]\% reported here
characterizes performance within the [specific scope], rather than
establishing cross-dataset superiority.
```

### Frases a EVITAR en comparaciones
- "Our method outperforms all existing approaches"
- "establishing direct performance parallels"
- "fundamental operational gaps across architecture granularity"
- "prevailing datasets" (usar nombre especifico del dataset)
- "explicit infrastructure footprints" (decir "number of APs" o similar)

---

## 3. Formulaciones condicionadas

Cuando un dato falta pero la oracion necesita funcionar:

| Situacion | Formulacion |
|-----------|------------|
| Rango no especificado | "under the reported operating range" |
| Setup no detallado | "within the evaluated setup" |
| Generalizacion no probada | "within the tested environment" |
| Metrica no calculada | "based on the observed [metric]" |
| Comparacion limitada | "under comparable evaluation conditions" |

Si el dato es critico y no hay forma de condicionar, usa:
```latex
\textcolor{red}{[MISSING: descripcion precisa del dato necesario]}
```

---

## 4. Errores frecuentes y correcciones

### Prosa inflada -> Correccion sobria

| Inflado | Sobrio |
|---------|--------|
| "the empirical verification explicitly demonstrates" | "the results show" o "the [model] achieved" |
| "solidifies the operational viability" | "confirms the feasibility" |
| "guarantees stable functional zone separation" | "achieves zone-level classification" |
| "resource-constrained asset tracking arrays" | "low-cost asset tracking" |
| "radically refactoring the problem estimation model" | "redesigning the classification approach" |
| "strategically validates zone-level functional clustering" | "validates zone-level classification" |
| "coupling a conventional four-node Wi-Fi architecture to a standard edge framework" | "using four APs and a [model] sensing module" |

### Sinonimos innecesarios -> Termino estable

| Variaciones problematicas | Termino unico recomendado |
|---------------------------|---------------------------|
| "functional clustering" / "area identification" / "location boundary inference" | "zone-level classification" |
| "signal strength profiling" / "radio map construction" | "RSS fingerprinting" |
| "edge framework" / "sensing platform" / "IoT node" | "sensing module" (o el nombre del hardware) |
| "classification margins" / "prediction accuracy" / "localization precision" | "classification accuracy" (o la metrica especifica) |

### Conectores naturales (estandar en papers publicados)

Los conectores "However", "Moreover", "Furthermore", "To overcome this", "On the other hand" son aceptables cuando conectan ideas sustantivas. No los elimines por defecto. Lo que debes evitar es la cascada mecanica (3+ consecutivos sin contenido) o el conector vacio sin ancla concreta.

---

## 5. Checklist de revision final

Verificar antes de entregar cualquier seccion:

**Contenido**
- [ ] Cada afirmacion tecnica tiene ancla (dato, tabla, figura, referencia)
- [ ] No hay informacion inventada fuera del contexto
- [ ] Las cifras coinciden con las tablas/figuras
- [ ] Las contribuciones del abstract/intro coinciden con los resultados

**Terminologia**
- [ ] El mismo concepto usa el mismo termino en todo el texto
- [ ] Acronimos definidos al primer uso, reutilizados despues
- [ ] Unidades SI con formato consistente

**Prosa**
- [ ] Sin adjetivos vacios ("robust", "efficient") sin metrica
- [ ] Sin reformulaciones consecutivas de la misma idea
- [ ] Sin conectores formando cascadas mecanicas sin contenido
- [ ] Sin nominalizaciones innecesarias

**LaTeX**
- [ ] Todas las `\cite{key}` corresponden a entradas del .bib
- [ ] Todas las `\ref{label}` corresponden a `\label{}` existentes
- [ ] `Fig.~\ref{}` y `Table~\ref{}` con non-breaking space
- [ ] Sistema de revision preservado (`\textcolor{blue/red}{}`)
- [ ] Entornos abiertos y cerrados correctamente
