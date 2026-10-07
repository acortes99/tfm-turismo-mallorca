# Revisión bibliográfica sobre predicción turística en Mallorca

Este protocolo organiza la selección y evaluación de estudios para fundamentar los modelos y las variables externas del TFM. La revisión se centrará en predicción de demanda turística, comparaciones con referencias estacionales, disponibilidad de los predictores y evaluación temporal. Fecha de la búsqueda inicial: 7 de octubre de 2026.

El protocolo adapta la metodología híbrida de VIU de abril de 2025. Las decisiones que siguen son una propuesta de trabajo para revisión del alumno y la tutora. Las búsquedas realizadas están en `registro_busquedas.md`; las fichas iniciales, en `estudios.md`. La memoria Word no se modifica.

## Objetivos de la revisión

1. Identificar los modelos estadísticos y de aprendizaje automático empleados para predecir demanda turística y las condiciones en que funcionan mejor.
2. Examinar la aportación de tráfico aéreo, actividad hotelera, meteorología y otras variables externas, incluidos resultados sin mejora predictiva.
3. Identificar prácticas de evaluación temporal, selección de retardos, tratamiento de pandemia y prevención de fuga de información.
4. Fundamentar la comparación de modelos de referencia, SARIMA/SARIMAX, Random Forest y XGBoost a uno y tres meses.
5. Reconocer limitaciones de los estudios y justificar qué aspectos pueden trasladarse a una serie mensual de Mallorca con 123 observaciones.

## Preguntas para la búsqueda bibliográfica

Estas preguntas describen evidencia publicada. No sustituyen las preguntas experimentales de la memoria. La selección final corresponde al alumno. La guía VIU propone contrastar y refinar las preguntas en dos herramientas generales; esta propuesta se ha elaborado con una sola y esa segunda vía sigue pendiente.

| Código | Pregunta | Versión inglesa para buscar |
|---|---|---|
| PB1 | ¿Qué modelos estadísticos y de aprendizaje automático se han utilizado para predecir demanda turística mensual y cómo se comparan con modelos de referencia? | Which statistical and machine learning models have been used to forecast monthly tourism demand, and how do they compare with benchmark models? |
| PB2 | ¿En qué condiciones las variables externas mejoran o no mejoran la predicción frente al uso exclusivo del histórico de demanda? | Under what conditions do exogenous variables improve or fail to improve forecasting compared with demand history alone? |
| PB3 | ¿Cómo se incorporan tráfico aéreo, actividad hotelera y meteorología, y cómo se comprueba que esas variables estaban disponibles al emitir el pronóstico? | How are air traffic, hotel activity and weather incorporated, and how is predictor availability at the forecast origin verified? |
| PB4 | ¿Qué diseños de validación y métricas se emplean para comparar horizontes de predicción y evitar fuga de información? | Which validation designs and accuracy metrics are used to compare forecast horizons and prevent data leakage? |
| PB5 | ¿Cómo se trata la estacionalidad, la escasez de observaciones y las rupturas asociadas a la pandemia, y qué limitaciones afectan a destinos insulares o españoles? | How are seasonality, small samples and pandemic-related structural breaks handled, and what limitations affect island or Spanish destinations? |

## Inclusión y exclusión

El periodo de los datos del TFM y el periodo de publicación de la bibliografía son distintos. No se exige que un estudio utilice exactamente 2015–2025 ni que trate exclusivamente Mallorca.

| Aspecto | Inclusión | Exclusión o tratamiento |
|---|---|---|
| Fechas | Publicaciones de 2015 al 7 de octubre de 2026. Estudios anteriores pueden incluirse como antecedentes si justifican una técnica o tratan directamente Baleares y las variables del TFM. | Los anteriores se registran como excepción justificada; no se mezclan con el recuento de literatura reciente. No incluir publicaciones posteriores a la fecha de corte. |
| Tema | Pronóstico de turistas, llegadas, visitantes, pernoctaciones o demanda/ocupación hotelera; revisiones directamente relacionadas. | Clasificación de opiniones, recomendación de destinos o descripción del turismo sin relación con pronósticos. |
| Métodos | Series temporales, econometría, aprendizaje automático, modelos híbridos y evaluación comparativa. | Propuestas sin evaluación ni método interpretable, salvo referencias teóricas identificadas aparte. |
| Frecuencia | Prioridad mensual. Diaria, semanal o trimestral si aportan evidencia sobre variables, validación o rupturas. | No descartar automáticamente otra frecuencia; marcar su transferibilidad limitada. |
| Territorio | Prioridad Mallorca, Baleares y España; otros destinos comparables y evidencia metodológica internacional. | No exigir geografía local, porque sesgaría y reduciría excesivamente la revisión. |
| Idioma | Español e inglés. | Otros idiomas si no puede revisarse el contenido con suficiente fiabilidad. |
| Publicación | Artículos y actas científicas con revisión por pares; revisiones académicas verificables. | TFG/TFM, preprints sin versión publicada y documentos de trabajo se guardan como material complementario; no se contabilizan como artículos revisados por pares. |
| Acceso | Texto completo disponible o recuperable por biblioteca/repositorio autorizado. | Sin texto completo: conservar como candidato pendiente. No asignar calidad definitiva ni excluir por pago antes de intentar el acceso institucional. |
| Duplicados | Una ficha por estudio, con todas las vías de descubrimiento. | Unificar por DOI; si falta, título normalizado, autores y año. La versión publicada sustituye al preprint como referencia principal. |
| Resultado | Mejoras, ausencia de mejora y resultados mixtos. | Nunca excluir porque contradiga la hipótesis del TFM. |

## Bases y herramientas

| Vía | Recursos | Uso |
|---|---|---|
| Manual | Scopus y Web of Science desde la [Biblioteca VIU](https://biblioteca.universidadviu.com/); IEEE Xplore y ScienceDirect para ampliar por disciplinas/editoriales. | Ejecutar consultas en título, resumen y palabras clave; exportar resultados y filtros. |
| Complementaria | Google Académico y Semantic Scholar; repositorios de autores e instituciones. | Buscar versiones accesibles, comprobar metadatos y explorar citas. No confundir sus resultados con una búsqueda ejecutada en Scopus. |
| IA especializada | SciSpace y Consensus. | Aplicar las cinco preguntas con los mismos criterios. Guardar candidatos y contrastar cada referencia con el editor o un repositorio académico. |
| IA general | Dos herramientas generales para iterar preguntas; una para apoyar búsqueda y extracción. | Conservar prompts, fechas y respuestas; el alumno confirma la selección y las interpretaciones. |
| Gestión | Zotero o Mendeley. | Carpetas Manual, IA especializada e IA general; colección final sin duplicados. La instalación/importación no se ha realizado en esta búsqueda. |

Las vías institucionales y especializadas quedan pendientes de ejecución. La búsqueda inicial se ha realizado mediante búsqueda web asistida por IA general y consultas a editores/repositorios. No se han utilizado cuentas de Scopus, Web of Science, SciSpace, Consensus o Gemini.

## Términos y consultas reproducibles

Bloque de tema: `"tourism demand" OR "tourist arrivals" OR "tourist flows" OR "hotel demand" OR "overnight stays"`.

Bloque de predicción: `forecast* OR predict*`.

Bloque de métodos: `SARIMA OR SARIMAX OR "random forest" OR XGBoost OR "gradient boosting" OR "machine learning"`.

Bloque externo: `exogenous OR "external variables" OR weather OR meteorolog* OR "air traffic" OR "air passengers" OR "hotel occupancy"`.

Bloque de validación: `"rolling origin" OR "rolling window" OR "time series cross validation" OR "out-of-sample" OR leakage OR horizon*`.

Ejemplos para Scopus, pendientes de ejecutar con el acceso de VIU:

```text
TITLE-ABS-KEY(("tourism demand" OR "tourist arrivals" OR "hotel demand") AND (forecast* OR predict*))

TITLE-ABS-KEY(("tourism demand" OR "tourist arrivals") AND (forecast* OR predict*) AND (SARIMA OR SARIMAX OR "random forest" OR XGBoost OR "machine learning"))

TITLE-ABS-KEY(("tourism demand" OR "tourist arrivals" OR "overnight stays") AND (forecast* OR predict*) AND (weather OR meteorolog* OR "air traffic" OR "hotel occupancy" OR exogenous))

TITLE-ABS-KEY(("tourism demand" OR "tourist arrivals") AND (forecast* OR predict*) AND (Mallorca OR Majorca OR Balearic* OR Spain OR Spanish))

TITLE-ABS-KEY(("tourism demand" OR "tourist arrivals") AND (forecast* OR predict*) AND ("rolling origin" OR "out-of-sample" OR leakage OR horizon* OR COVID))
```

En Web of Science, adaptar a `TS=(...)`; en IEEE y ScienceDirect, comprobar los campos y operadores admitidos antes de reutilizar la consulta. Para motores web y Google Académico, utilizar consultas más cortas, sin asumir que admiten la sintaxis de Scopus. Complementar con `predicción demanda turística mensual`, `Baleares meteorología predicción turística` y `variables exógenas turismo SARIMAX`.

La consulta general va primero. Después se añaden métodos, variables o geografía en búsquedas separadas. No exigir todos los bloques a la vez ni añadir NOT de forma automática: podrían perderse artículos relevantes. Para cada consulta guardar plataforma, texto exacto, fecha, filtros y número de registros cuando la plataforma lo proporcione.

## Búsqueda iterativa y extracción

1. Ejecutar las consultas generales; cribar título y resumen. Registrar decisión y motivo de exclusión.
2. Refinar consultas hacia evidencia insuficiente: tráfico aéreo/hoteles, Baleares, horizontes y disponibilidad de predictores. Conservar las consultas anteriores.
3. Leer textos completos y explorar sus referencias y citas posteriores. Marcar el artículo semilla del que procede cada incorporación.
4. Aplicar la vía especializada según VIU: cinco candidatos de cada herramienta por pregunta, ampliando cuando sea necesario. Los resultados repetidos conservan una única ficha.
5. Ejecutar un prompt por pregunta en la vía general; verificar cada título, año, DOI y publicación. Un resumen generado no sustituye la fuente.
6. Consolidar las tres vías, puntuar con evidencias y seleccionar los estudios que responden a las preguntas. Documentar los motivos para incluir o excluir y los textos no recuperados.

La ficha recogerá: ID, referencia, DOI/URL, año de publicación y año de depósito si difieren, vía de descubrimiento, consulta, fecha, pregunta respondida, territorio, variable objetivo, fuente de datos, frecuencia, periodo, número de observaciones, predictores, retardos, disponibilidad temporal, modelos, horizontes, particiones, preprocesamiento, métricas, resultados, limitaciones, calidad y localización de evidencias. Lo desconocido se registra como pendiente, no se deduce.

## Calidad metodológica

La escala sigue el ejemplo VIU: 0, 0,5 o 1. `NP` significa no evaluado y no equivale a cero. Toda puntuación lleva sección/página y justificación. La revisión crítica final corresponde al alumno; las puntuaciones asistidas son preliminares.

| Criterio | 0 | 0,5 | 1 |
|---|---|---|---|
| Q1 Respuesta a las preguntas | No aporta evidencia pertinente. | Aporte indirecto o contextual. | Aporta evidencia directa a una o más preguntas identificadas. |
| Q2 Datos y trazabilidad | No define datos/objetivo. | Fuente, periodo o unidad incompletos. | Objetivo, procedencia, frecuencia y periodo claramente descritos. |
| Q3 Método reproducible | Método no descrito. | Explicación parcial o faltan decisiones relevantes. | Modelos, preparación, entradas y configuración suficientemente detallados. |
| Q4 Evaluación válida | No permite evaluar predicciones futuras o presenta una separación temporal inadecuada. | Validación descrita con información insuficiente sobre cortes, preprocesamiento o disponibilidad de entradas. | Evaluación temporal explícita, referencias y métricas comparables; tratamiento de entradas compatible con el origen del pronóstico. |
| Q5 Robustez y limitaciones | No examina ni reconoce limitaciones relevantes. | Comprobaciones o limitaciones parciales. | Examina sensibilidad/robustez y discute límites relevantes o facilita reproducción verificable. |

Para revisiones, Q2 evalúa bases/consultas/fechas; Q3, selección y extracción; Q4, evaluación crítica de los estudios; Q5, cobertura, sesgos y límites. No exigirles un experimento predictivo propio.

El total sobre cinco sirve para ordenar lecturas; no se impone un umbral automático. Un artículo pertinente con debilidades puede aportar una limitación útil. Q4=0 impide usar sus cifras como prueba sólida de mejora futura, aunque pueda citarse como antecedente.

## Resultado inicial y tareas pendientes

Se han reunido 15 fichas de candidatos con enlaces verificables, incluidas tres incorporaciones sobre comparación de modelos de referencia, estadísticos y basados en árboles. Tres fichas incluyen una evaluación preliminar de secciones metodológicas y resultados. No son todavía 15 estudios definitivamente incluidos ni una revisión terminada. No se dispone de un recuento exhaustivo de todos los resultados web: no se inventan cifras para un diagrama de selección.

Un antecedente de 2010 aborda directamente Baleares y meteorología. Se incorpora como excepción explícita al intervalo reciente. El artículo español de Claveria, Monte y Torra se cita como publicación de 2016; el depósito en arXiv es de 2018 y no constituye otro estudio.

Pendientes: revisión y selección de preguntas por el alumno; segunda herramienta general; búsquedas institucionales y especializadas; importación al gestor; recuperación y lectura completa de candidatos; evaluación definitiva; ampliación hasta al menos 30 referencias pertinentes conforme a los apuntes. La cifra no justifica incluir estudios irrelevantes ni contar duplicados.

## Registro del apoyo de IA

Conservar este protocolo, las consultas y las respuestas relevantes junto con fecha, herramienta y finalidad. La guía VIU exige consensuar el uso de IA con la tutora y declararlo en la memoria. El registro que acompaña esta entrega no reemplaza el historial de las interacciones anteriores del ETL y la redacción. No se atribuyen al alumno lecturas o decisiones que siguen pendientes.
