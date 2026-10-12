# tfm-turismo-mallorca
Predicción del flujo turístico mensual en Mallorca mediante series temporales y aprendizaje automático. Incluye ETL reproducible, integración de variables externas, comparación de modelos e interpretabilidad, como parte de un TFM en Big Data y Ciencia de Datos.

## ETL documentado

El notebook `tfm-turismo-viu.ipynb` contiene la explicación, el código y los resultados de revisión del ETL. Lee los archivos originales de `Datasets/` mediante rutas relativas y genera `outputs/etl/` sin modificar las fuentes.

```shell
python -m pip install -r requirements.txt
jupyter lab
```

Abrir el notebook desde la raíz del repositorio y ejecutar todas las celdas en orden con un kernel nuevo. Los archivos de salida se regeneran con cada ejecución. El notebook comprueba los formatos mensuales de AENA, la cobertura de Mallorca, los duplicados, las unidades, los ausentes y la escala de estancia media. La meteorología de B278 está integrada con sus estados y una política de disponibilidad explícita. No se requiere una API key para ejecutar el ETL con las fuentes locales.

El periodo de estudio es octubre de 2015–diciembre de 2025. Los datos de 2025 se reservan para evaluación final. El notebook construye los retardos según la disponibilidad de publicación, define la evaluación temporal y comprueba la imputación hotelera dentro de cada entrenamiento. Incluye Seasonal Naïve, SARIMA, SARIMAX y Random Forest; la puntuación final de 2025 permanece desactivada.

## Análisis exploratorio

Las secciones 12–18 del notebook incluyen seis gráficas comentadas: evolución de turistas, estacionalidad mensual, caída y recuperación respecto a 2019, relaciones con aeropuerto y hoteles, correlaciones y mapa de ausentes. Se guardan también las figuras y cinco tablas de apoyo en `outputs/eda/`, junto con los parámetros y versiones de la ejecución.

Las relaciones y los perfiles estacionales se calculan con datos hasta diciembre de 2024. El año 2025 aparece únicamente como contexto en la evolución general y la revisión de cobertura; esta inspección descriptiva se declara como limitación del aislamiento del conjunto de prueba. Las conclusiones orientan el calendario, los retardos, el tratamiento de la pandemia y los ausentes, sin transformar todavía el dataset para entrenar modelos. La meteorología se incorpora en el ETL y se explora también en el bloque final; las reglas de disponibilidad se concretan en los bloques siguientes.

## Disponibilidad de los predictores

Las secciones 19–21 documentan las fuentes oficiales de publicación y fijan el pronóstico al cierre de cada mes. La regla base permite AENA y hoteles hasta el mes anterior y turistas hasta dos meses antes; distingue los retardos respecto al origen de los retardos respecto a los objetivos a uno y tres meses. Se comprueban los desplazamientos, el bloqueo ante una publicación tardía y la conservación de ausentes y ceros.

`outputs/disponibilidad/` contiene la política, la evidencia de fechas efectivas y previstas, los retardos mínimos, la auditoría y dos vistas por origen (regla base y un mes adicional de espera). Estas vistas no son todavía matrices definitivas de entrenamiento. Las fechas de primera publicación y las versiones históricas no se han reconstruido para todo 2015–2025: la evaluación será una simulación retrospectiva bajo esta política, con la limitación de revisiones posteriores. Para AEMET se adopta t−2 y sensibilidad t−3 como supuesto experimental; no es un plazo mensual verificado.

## Google Trends

Las secciones 7 bis y 22–24 incorporan los cuatro CSV de `Datasets/Google Trends`: Mallorca/Majorca en Alemania/Reino Unido, categoría Viajes, enero de 2015–diciembre de 2025. Se comprueban cabeceras, calendario, duplicados y rango 0–100; se conservan los índices por separado. El maestro incluye los 123 meses comunes y la extracción auxiliar conserva 132 meses. El inventario registra SHA256 y el catálogo deja sin completar los metadatos no acreditados en los CSV.

La exploración añade tres figuras y cuatro tablas hasta 2024: evolución, perfiles mensuales, correlaciones en niveles/diferencias interanuales con retardos y redundancia entre índices. No selecciona predictores ni ajusta modelos. La disponibilidad adopta t−1 como supuesto conservador y t−2 como sensibilidad; no son plazos oficiales comprobados. La descarga posterior, el muestreo y la normalización sobre 2015–2025 impiden reconstruir exactamente la información histórica por origen, aun excluyendo las filas de 2025 de las relaciones exploradas.

## SARIMA

Las secciones 33–36 implementan SARIMA con la serie de turistas, sin variables externas. Se conservan los ceros de la pandemia. Ocho configuraciones con estacionalidad de 12 meses se comparan mediante validación progresiva de enero de 2020 a julio de 2024. Se exige cobertura y convergencia completas; se elige el menor RMSE por horizonte y escenario de disponibilidad. El diagnóstico de agosto–diciembre de 2024 es retrospectivo y no equivale a una prueba independiente.

Los horizontes de uno y tres meses se evalúan sobre los mismos meses que Seasonal Naïve. El retardo de publicación del objetivo requiere tres y cinco pasos internos en el escenario base. En 2025 se permite actualizar el estado con observaciones ya publicadas; los parámetros se estiman únicamente con historia anterior a 2025. `EVALUATE_FINAL_2025=False` genera los pronósticos reservados sin calcular sus errores ni métricas.

`outputs/modelos/sarima/` guarda la búsqueda, las configuraciones seleccionadas, los pronósticos, las métricas por bloque/año/periodo, la comparación con Seasonal Naïve, los avisos y parámetros de cada ajuste y una figura de validación. Las predicciones negativas se limitan a cero según una regla previa; también se exportan las predicciones originales y sus métricas. Los controles verifican el calendario, la ausencia de datos futuros en una emisión y la conservación de las fuentes. La primera ejecución puede tardar varios minutos por los ajustes repetidos de la búsqueda; dentro de cada ejecución se reutilizan ajustes con la misma configuración e historia disponible.

## SARIMAX con AENA y hoteles

Las secciones 37–39 comparan histórico solo, pasajeros de AENA, viajeros hoteleros y ocupación de plazas, y la combinación de ambas fuentes. Las cuatro variantes mantienen los órdenes elegidos para SARIMA y la misma ventana histórica por horizonte y escenario. El control de histórico solo se vuelve a estimar con esa ventana común para aislar la aportación de las entradas externas.

Los indicadores se alinean con el objetivo mediante un retardo de `horizonte + 1 + espera adicional`. Se comprueba su publicación en cada fila, incluidos los pasos intermedios del pronóstico, sin introducir valores futuros. La imputación hotelera utiliza medianas y marcas de ausencia; medianas, medias y desviaciones se ajustan únicamente con filas de entrenamiento cuyo objetivo está publicado y es anterior a 2025. Las columnas constantes se excluyen del ajuste y se registran. Los ceros se conservan y un ausente de AENA provoca un error explícito.

`outputs/modelos/sarimax/` contiene los pronósticos de las cuatro variantes, las métricas por bloque/año/periodo, la comparación con el histórico común, la clasificación de selección, los parámetros y avisos de cada ajuste y las auditorías de preprocesamiento y disponibilidad de los pasos futuros. Las métricas finales de 2025 permanecen desactivadas con el mismo interruptor del resto de modelos. La clasificación utiliza solo variantes con los 55 pronósticos de selección convergentes y puntuados; no constituye una prueba independiente de generalización.

## Descarga meteorológica de AEMET

`scripts/descargar_aemet.py` obtiene las climatologías mensuales de [AEMET OpenData](https://opendata.aemet.es/dist/), autora de los datos, para 2015–2025. Utiliza la variable de entorno `AEMET_API_KEY`; la clave no se guarda en el código ni en los productos. Para repetir la descarga, definir esa variable en la sesión local y ejecutar:

```shell
python scripts/descargar_aemet.py
```

Los productos se guardan en `Datasets/Meteorologia/AEMET/`. Cada consulta abarca como máximo 36 meses. El script reintenta los fallos transitorios y reutiliza productos completos ya guardados; para obtener una nueva versión, elegir otra carpeta con `--salida`. Se conservan los JSON originales, sus metadatos y los registros anuales por separado: el mes 13 de la respuesta es un resumen anual y se excluye de la serie mensual. `descarga.json` registra consultas, fecha, hashes y cobertura.

Las estaciones son **B278, Palma de Mallorca, Aeropuerto**, como serie principal propuesta, y **B228, Palma, Puerto**, como alternativa para comprobar sensibilidad espacial. Se mantienen separadas y no se rellenan huecos de una con valores de la otra. Ambas proporcionan 132 meses, de enero de 2015 a diciembre de 2025; el periodo del maestro, octubre de 2015–diciembre de 2025, utiliza 123. Una estación de Palma es una aproximación local a la meteorología del destino, no una medida de toda Mallorca.

Los CSV `mensual_limpio_B278_2015_2025.csv` y `mensual_limpio_B228_2015_2025.csv` incluyen temperaturas medias (general, máximas y mínimas), precipitación total, humedad, insolación media diaria, viento y recuentos de días. Cada variable conserva su valor original y una marca de estado. Temperatura y precipitación están completas en ambas estaciones. En B278 faltan dos valores de humedad y uno de insolación; en B228 faltan cuatro de humedad, once de insolación y veinte de días de lluvia. Se conservan los ceros y no se imputan ausentes ni se convierten trazas o valores no numéricos en ceros. La insolación se expresa como horas diarias medias del mes, no como horas totales mensuales.

Estos son datos observados revisados, no predicciones meteorológicas emitidas históricamente. El bloque 7 ter del notebook reconstruye la serie desde los JSON originales, comprueba sus hashes y la contrasta con los CSV limpios. Integra diez variables y sus estados en los 123 meses del maestro. Las temperaturas pueden ser negativas, los ceros se conservan y los tres huecos secundarios de B278 quedan sin imputar. B228 se conserva separada para sensibilidad espacial.

El bloque 40 documenta la disponibilidad: las [FAQ oficiales de AEMET](https://opendata.aemet.es/centrodedescargas/docs/FAQs220424.pdf), apartado 4.2, indican aproximadamente cuatro días para las climatologías diarias, pero no acreditan el plazo de las mensuales. La actualización diaria del producto mensual tampoco demuestra la fecha de su primera publicación. Por ello t−2 y t−3 se declaran como supuestos de la simulación, con bloqueo si se acredita una publicación posterior. Los retardos respecto al objetivo son 3/5 meses para h=1/h=3 en la base y 4/6 en sensibilidad.

Las cuatro matrices de predicción añaden seis candidatos: temperatura media y precipitación, cada una con el primer retardo permitido, un mes adicional y un año adicional. Las otras ocho variables meteorológicas quedan en el maestro, sin introducirse automáticamente en modelos ni imputarse mediante la regla hotelera. Los modelos anteriores mantienen sus listas de entradas. El bloque 41 añade una comparación específica con temperatura y precipitación; las métricas finales de 2025 permanecen desactivadas.

`outputs/meteorologia/` conserva las reconstrucciones de 132 meses, las dos estaciones recortadas a los 123 del TFM, la calidad por variable, los ausentes de B278, las asociaciones calculadas solo hasta 2024, una figura comparativa y el registro de integración. Los controles contrastan los desplazamientos, las publicaciones tardías y la conservación de los valores originales.


## SARIMAX con meteorología

El bloque 41 compara el histórico solo con temperatura media y precipitación de B278, completas y sin imputación. Reutiliza los órdenes seleccionados para SARIMA y el calendario de evaluación a uno y tres meses. Ambas variantes comparten la ventana de historia necesaria para AEMET; este control se estima de nuevo y difiere del de AENA/hoteles.

El retardo respecto al objetivo es `h + 2 + espera adicional`: 3/5 meses en la base y 4/6 en sensibilidad. La publicación se comprueba en cada fila y paso interno del pronóstico bajo el supuesto mensual t−2/t−3. La normalización se ajusta solo con etiquetas publicadas de entrenamiento anteriores a 2025; una entrada meteorológica no disponible bloquea la preparación. Los ceros de precipitación y de turistas se conservan.

`outputs/modelos/sarimax_meteorologia/` guarda predicciones, métricas, comparación con el histórico común, auditorías de ajustes, escalado y disponibilidad, y una figura de validación. La selección utiliza los mismos 55 meses hasta julio de 2024 y el diagnóstico retrospectivo los cinco restantes de 2024. Con `EVALUATE_FINAL_2025=False`, se generan pronósticos de 2025 sin observaciones objetivo, errores ni métricas finales. Los controles verifican la igualdad del calendario y las ventanas, la invariancia ante datos aún no publicados y el bloqueo de publicaciones tardías.


En esta ejecución se completaron 576 emisiones sin fallos. En los 55 meses de selección, la meteorología reduce el RMSE base un 1,00 % a un mes y lo aumenta un 1,28 % a tres meses. Con espera adicional, aumenta el error un 5,87 % y un 2,22 %, respectivamente. El bloque incluye la interpretación y los resultados del diagnóstico: la mejora es pequeña y no se mantiene entre escenarios; no se ha puntuado 2025.


## Random Forest con turistas y calendario

El bloque 42 incorpora la primera referencia de ML mediante predicción directa por horizonte. Utiliza los diez predictores turísticos y las cuatro variables de calendario del catálogo existente, excluyendo fuentes externas. La configuración inicial es fija: 300 árboles, un mínimo de tres observaciones por hoja, todas las columnas disponibles en cada división, bootstrap y semilla 42; no hay búsqueda de hiperparámetros ni validación aleatoria.

Cada emisión utiliza exactamente los índices supervisados del protocolo: objetivos desde abril de 2017, ya publicados al cierre del origen y anteriores a 2025. No se escalan ni imputan entradas; un ausente inesperado bloquea el pronóstico. Los ceros se conservan. Los retardos publicados de 2025 pueden actualizar las entradas, pero los objetivos de 2025 no entran en ningún ajuste. La historia supervisada es más corta que la historia secuencial de SARIMA; las comparaciones mantienen los mismos meses objetivo y declaran esa diferencia.

`outputs/modelos/random_forest/` guarda los pronósticos, las métricas por bloque/año/periodo, la comparación con Seasonal Naïve y SARIMA, el catálogo de 14 predictores, los índices de entrenamiento y las auditorías de ajustes y disponibilidad. El bloque comprueba reproducibilidad con semilla fija, invariancia ante datos aún no publicados y bloqueo de publicaciones tardías. `EVALUATE_FINAL_2025=False` genera las 12 predicciones finales por horizonte y escenario sin observaciones, errores ni métricas de prueba.


La ejecución inicial completa las 288 emisiones sin fallos. En los 55 meses de selección base, el RMSE de Random Forest es 603.704 turistas a un mes y 681.873 a tres meses, frente a 588.182 de Seasonal Naïve y 404.429/515.841 de SARIMA. Esta configuración inicial no supera las referencias; el notebook comenta también el diagnóstico, la pandemia y la diferencia de historia de entrenamiento. Se mantienen reservadas las 48 predicciones de 2025, sin calcular sus errores.


## Búsqueda acotada de Random Forest

El bloque 43 prueba seis combinaciones de tamaño mínimo de hoja (1, 3, 5) y profundidad máxima (5, sin límite), conservando los 300 árboles y el resto de la configuración inicial. Selecciona una configuración por horizonte exclusivamente por RMSE en los 55 objetivos de selección del escenario base; MAE y una preferencia por mayor regularización resuelven empates exactos. La configuración inicial está incluida y se comprueba su reproducción.

Las configuraciones elegidas se mantienen fijas en los cinco meses de diagnóstico, el escenario con espera adicional y las emisiones de 2025. El escenario de espera adicional no tiene una nueva búsqueda. La congelación de octubre de 2024 representa una regla de la simulación retrospectiva. Las métricas de selección están sujetas a optimismo por haber participado en la elección y el diagnóstico ya se ha inspeccionado: ninguno se presenta como prueba final independiente.

`outputs/modelos/random_forest_optimizado/` guarda las configuraciones, 660 emisiones de búsqueda, la clasificación y selección por horizonte, 288 emisiones de evaluación con configuración fija, métricas, comparaciones frente al bosque inicial, Seasonal Naïve y SARIMA, y auditorías. Los índices de entrenamiento y 14 entradas se mantienen; el bosque inicial se conserva separado. `EVALUATE_FINAL_2025=False` evita consultar los objetivos o calcular los errores finales durante toda la búsqueda y evaluación.


La búsqueda completó las 660 emisiones y la evaluación fija las 288, sin fallos. Seleccionó hoja mínima 1 y profundidad sin límite a un mes, y hoja mínima 1 con profundidad 5 a tres meses. Los RMSE base de selección bajaron a 584.641 y 674.365 turistas, un 3,16 % y un 1,10 % frente al bosque inicial. La mejora es limitada y no se mantiene en todos los escenarios; SARIMA conserva un menor error de selección. El notebook comenta el diagnóstico, la sensibilidad y el optimismo de selección. Las 48 predicciones finales de 2025 siguen sin puntuar.


## Fuentes externas en Random Forest

El bloque 44 compara turistas y calendario con la incorporación por separado de AENA, hoteles, meteorología o Google Trends. Mantiene los parámetros seleccionados por horizonte en el bloque 43, sin una búsqueda por fuente o escenario. Cada variante usa los mismos índices de entrenamiento y las 288 emisiones del protocolo; el control se reproduce y contrasta con el bosque optimizado anterior.

Se incorporan los tres retardos del catálogo por variable (primer mes permitido, un mes adicional y un año adicional). AENA aporta pasajeros y operaciones; hoteles, los seis indicadores disponibles; meteorología, temperatura y precipitación de B278; Google Trends, las cuatro series recogidas. Los tamaños preparados son 14 columnas en el control, 20 en AENA y meteorología, 26 en Google Trends y 50 en hoteles, incluyendo sus 18 marcas de ausencia. La comparación mantiene hiperparámetros, pero cambia la dimensionalidad: las diferencias no se interpretan como efectos causales.

Las medianas hoteleras y sus marcas se ajustan exclusivamente con filas supervisadas de ese entrenamiento y etiquetas publicadas anteriores a 2025. Los valores ausentes o bloqueados por una publicación tardía se sustituyen con la mediana de entrenamiento y su marca. El resto de las fuentes bloquea las entradas ausentes; no se imputa automáticamente. Los valores observados y los ceros se conservan, sin escalado ni eliminación de meses.

`outputs/modelos/random_forest_externas/` conserva 1.440 emisiones, métricas y comparaciones por bloque, clasificación base de selección, catálogo, índices y auditorías de entrenamiento, imputación y disponibilidad, y dos figuras. Se comprueba que alterar datos no publicados no cambie matrices, medianas ni pronósticos. Los supuestos de disponibilidad mensual de AEMET y Google Trends, sus versiones revisadas y la normalización retrospectiva de Trends se declaran como limitaciones. No se prueban combinaciones de fuentes. La puntuación de 2025 permanece desactivada.


La ejecución completa las 1.440 emisiones sin fallos y reproduce el control optimizado. En selección base, AENA reduce el RMSE un 5,18 %/3,68 % a uno/tres meses; hoteles, un 4,41 %/0,90 %. Meteorología empeora un 0,95 % a un mes y mejora un 7,38 % a tres; Google Trends empeora un 1,35 %/2,42 %. Las ventajas no son uniformes en diagnóstico y espera adicional, por lo que no se declara una fuente ganadora general. Las 240 predicciones finales de las cinco variantes permanecen sin puntuar. El notebook incluye las dos figuras, comentarios y las cifras de imputación por emisión.


## Comparación conjunta de modelos

El bloque 49 se ejecuta al final del notebook, después de generar todas las variantes, y reúne 20 series de Seasonal Naïve, SARIMA, SARIMAX, Random Forest y XGBoost. Incluye las versiones iniciales y ajustadas y cada fuente externa; los controles repetidos de los modelos supervisados aparecen una sola vez. Se mantienen los mismos meses, horizontes, escenarios, orígenes y cortes de información. La agregación no reentrena y reproduce todas las métricas originales.

`outputs/comparacion_modelos/` conserva 5.760 emisiones, catálogo y calendario común, procedencia con hashes, métricas por bloque/año/periodo, diagnóstico sin U, diferencias frente a Seasonal Naïve y aportación externa frente al control interno con RMSE y MAE. Cuatro figuras muestran las 20 series por bloque y la evolución de cinco ejemplos fijados, uno por familia. Selección, diagnóstico y espera adicional se mantienen separados.

La incorporación de XGBoost no cambia los menores RMSE conjuntos: SARIMAX con AENA a un mes en selección base (400.413 turistas), SARIMA a tres (515.841) y SARIMA en ambos horizontes con espera adicional (462.528/548.747). Seasonal Naïve obtiene el menor RMSE en el diagnóstico de cinco meses en ambos escenarios (95.636). XGBoost ajustado mejora el RMSE base de su versión inicial y del bosque ajustado, pero no el de SARIMA. Las variantes de Trends a un mes y meteorología a tres son las mejores de ML en selección base (501.443/596.571), sin superar los mínimos secuenciales; a tres meses tampoco superan a la referencia estacional.

Las mejoras no son uniformes: el ajuste de XGBoost aumenta el MAE base a un mes y el RMSE de diagnóstico a tres. La meteorología mejora su selección a tres meses pero empeora el diagnóstico; Trends mejora su RMSE base, aunque empeora parte de la sensibilidad. Las discrepancias por métrica, horizonte, periodo y disponibilidad se documentan sin declarar un ganador final. Las 960 emisiones de 2025 siguen sin puntuar. Los controles comprueban la conservación de ceros, maestros y productos anteriores. Se mantienen las reservas sobre selección retrospectiva, distintas historias de entrenamiento, ventanas comunes de SARIMAX, datos revisados, plazo supuesto de AEMET y Trends retrospectivo.


## XGBoost con turistas y calendario

El bloque 46 añade una referencia inicial de predicción directa con los mismos 14 predictores turísticos y de calendario, índices supervisados y 288 emisiones del bosque. Cada entrenamiento utiliza etiquetas publicadas desde abril de 2017 y anteriores a 2025. No se escalan ni imputan entradas; un ausente inesperado bloquea la emisión. Los ceros reales se conservan.

La configuración fija utiliza 200 árboles, tasa de aprendizaje 0,05, profundidad 3, `min_child_weight=3`, L2 de 1 y L1 de 0, todas las filas y columnas, pérdida cuadrática y método `hist` en CPU. La semilla es 42 y se utiliza un hilo. No hay búsqueda, validación aleatoria, `eval_set` ni parada temprana. El límite inferior a cero conserva los valores brutos y sus marcas, sin limitar al rango del bosque. El registro guarda la versión de XGBoost utilizada, 3.2.0 en esta ejecución.

`outputs/modelos/xgboost/` contiene predicciones, métricas por bloque/año/periodo y sin objetivos U, comparación con Seasonal Naïve, SARIMA y Random Forest ajustado, catálogo, índices y auditorías de ajuste y disponibilidad. Se completan las 288 emisiones sin fallos, con entre 28 y 93 filas de entrenamiento, 258 ajustes y 30 reutilizaciones; no aparecen pronósticos negativos. Se comprueban reproducibilidad, invariancia ante datos no publicados, bloqueo de publicaciones tardías y separación de etiquetas de 2025. Las fuentes, el maestro y los productos anteriores permanecen intactos.

En selección base, el RMSE es 568.154 turistas a un mes y 683.127 a tres. A un mes mejora al bosque ajustado y a Seasonal Naïve, pero no a SARIMA; a tres su RMSE es mayor que el de esas referencias. El MAE de tres meses, 512.522, es menor que el del bosque ajustado pese al mayor RMSE. Diagnóstico y sensibilidad se presentan por separado en el notebook, sin declarar un ganador final. Las 48 emisiones de 2025 permanecen sin puntuar. Los bloques posteriores documentan la optimización, las fuentes externas y la comparación conjunta.


## Búsqueda acotada de XGBoost

El bloque 47 cruza profundidades máximas de 2, 3 y 4 con 100 o 200 árboles: seis configuraciones, incluida la inicial. Conserva tasa de aprendizaje 0,05, regularización, 14 entradas, índices supervisados y cortes de disponibilidad. Elige por horizonte solo en los 55 objetivos de selección base, minimizando RMSE; los empates se resuelven por MAE, menor profundidad, menos árboles e identificador. No se utiliza validación aleatoria, parada temprana ni fuentes externas.

La configuración por horizonte se mantiene fija en diagnóstico, sensibilidad y las emisiones de 2025, sin una nueva búsqueda. El ajuste utiliza únicamente etiquetas publicadas anteriores a 2025. La selección es retrospectiva y sus métricas contienen optimismo por haber intervenido en la elección; los cinco meses de diagnóstico ya se han inspeccionado y tampoco constituyen una prueba independiente. No se afirma un óptimo global.

`outputs/modelos/xgboost_optimizado/` conserva las seis configuraciones, 660 emisiones de búsqueda y 288 de evaluación fija, clasificación, selección, métricas por bloque/año/periodo y sin objetivos U, comparación con el XGBoost inicial, Seasonal Naïve, SARIMA y Random Forest ajustado, catálogo, índices, auditoría y figura comentada. Las comprobaciones reproducen la configuración inicial y los resultados de selección, mantienen los ceros, y verifican que diagnóstico, sensibilidad y 2025 no cambien la elección. Las fuentes, el maestro y los modelos anteriores permanecen intactos.

Se selecciona a 1 mes(es), profundidad 2 y 200 árboles (RMSE base de selección: 539.205 turistas); a 3 mes(es), profundidad 2 y 200 árboles (RMSE base de selección: 665.260 turistas). El notebook presenta además los cambios de diagnóstico y sensibilidad frente a la referencia inicial. Las 48 emisiones finales de 2025 siguen sin observaciones objetivo, errores ni métricas. Las fuentes externas y la comparación conjunta se documentan en los bloques posteriores.


## Fuentes externas en XGBoost

El bloque 48 compara turistas y calendario con AENA, hoteles, temperatura y precipitación, o Google Trends por separado. Mantiene los parámetros seleccionados en el bloque 47 por horizonte: profundidad 2, 200 árboles y aprendizaje 0,05, con el resto de opciones iniciales. No hay nueva búsqueda por fuente o escenario ni combinaciones de grupos. Cada variante comparte los índices supervisados y las 288 emisiones del protocolo.

Se utilizan los tres retardos del catálogo por variable, respetando el primer mes permitido, un mes adicional y un año adicional. El control tiene 14 columnas; AENA y meteorología, 20; Trends, 26; hoteles, 50, incluidas sus 18 marcas de ausencia. Las medianas hoteleras se calculan solo con las filas admisibles del entrenamiento y se aplican a sus huecos y a las entradas ausentes del pronóstico. Las publicaciones tardías no se utilizan: hoteles recibe mediana y marca, y las otras fuentes bloquean ausentes. No hay escalado, imputación del objetivo ni sustitución de ceros.

`outputs/modelos/xgboost_externas/` conserva 1.440 emisiones, métricas por bloque/año/periodo y sin objetivos U, comparación frente al control con reducciones de RMSE y MAE, clasificación de selección base, catálogo, índices y auditorías de disponibilidad, ajustes e imputación. El control reproduce los 288 pronósticos ajustados y los controles comprueban invariancia ante datos no publicados, bloqueo o marca de publicaciones tardías, medianas por entrenamiento y reproducibilidad. Las figuras y su interpretación se incluyen en el notebook.

Las reducciones del RMSE de selección base a uno/tres meses son: AENA: 1,37 %/2,97 %; Hoteles: 2,70 %/-1,46 %; Temperatura y precipitación: -4,32 %/10,33 %; Google Trends: 7,00 %/2,06 %. Los signos negativos indican empeoramiento. No hay una fuente que reduzca el RMSE del control en todos los horizontes, bloques y disponibilidades. Diagnóstico y espera adicional se presentan por separado, sin volver a elegir parámetros. Las 240 emisiones finales de 2025 siguen sin puntuar y sus etiquetas no participan en los ajustes o medianas. Se mantienen las reservas sobre datos revisados, publicación mensual de AEMET, Google Trends retrospectivo, cambio de dimensionalidad y selección de fuentes. El bloque 49 incorpora estas variantes a la comparación conjunta.
