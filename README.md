# tfm-turismo-mallorca
Predicción del flujo turístico mensual en Mallorca mediante series temporales y aprendizaje automático. Incluye ETL reproducible, integración de variables externas, comparación de modelos e interpretabilidad, como parte de un TFM en Big Data y Ciencia de Datos.

## ETL documentado

El notebook `tfm-turismo-viu.ipynb` contiene la explicación, el código y los resultados de revisión del ETL. Lee los archivos originales de `Datasets/` mediante rutas relativas y genera `outputs/etl/` sin modificar las fuentes.

```shell
python -m pip install -r requirements.txt
jupyter lab
```

Abrir el notebook desde la raíz del repositorio y ejecutar todas las celdas en orden con un kernel nuevo. Los archivos de salida se regeneran con cada ejecución. El notebook comprueba los formatos mensuales de AENA, la cobertura de Mallorca, los duplicados, las unidades, los ausentes y la escala de estancia media. La meteorología de B278 está integrada con sus estados y una política de disponibilidad explícita. No se requiere una API key para ejecutar el ETL con las fuentes locales.

El periodo de estudio es octubre de 2015–diciembre de 2025. Los datos de 2025 se reservan para evaluación final. El notebook construye los retardos según la disponibilidad de publicación, define la evaluación temporal y comprueba la imputación hotelera dentro de cada entrenamiento. Incluye Seasonal Naïve, SARIMA y SARIMAX; la puntuación final de 2025 permanece desactivada.

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

Las cuatro matrices de predicción añaden seis candidatos: temperatura media y precipitación, cada una con el primer retardo permitido, un mes adicional y un año adicional. Las otras ocho variables meteorológicas quedan en el maestro, sin introducirse automáticamente en modelos ni imputarse mediante la regla hotelera. Los modelos existentes mantienen sus listas de entradas; no se ha entrenado todavía ningún modelo con meteorología y las métricas finales de 2025 permanecen desactivadas.

`outputs/meteorologia/` conserva las reconstrucciones de 132 meses, las dos estaciones recortadas a los 123 del TFM, la calidad por variable, los ausentes de B278, las asociaciones calculadas solo hasta 2024, una figura comparativa y el registro de integración. Los controles contrastan los desplazamientos, las publicaciones tardías y la conservación de los valores originales.
