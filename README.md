# tfm-turismo-mallorca
Predicción del flujo turístico mensual en Mallorca mediante series temporales y aprendizaje automático. Incluye ETL reproducible, integración de variables externas, comparación de modelos e interpretabilidad, como parte de un TFM en Big Data y Ciencia de Datos.

## ETL documentado

El notebook `tfm-turismo-viu.ipynb` contiene la explicación, el código y los resultados de revisión del ETL. Lee los archivos originales de `Datasets/` mediante rutas relativas y genera `outputs/etl/` sin modificar las fuentes.

```shell
python -m pip install -r requirements.txt
jupyter lab
```

Abrir el notebook desde la raíz del repositorio y ejecutar todas las celdas en orden con un kernel nuevo. Los archivos de salida se regeneran con cada ejecución. El notebook comprueba los formatos mensuales de AENA, la cobertura de Mallorca, los duplicados, las unidades, los ausentes y la escala de estancia media. La meteorología está pendiente; no se requiere una API key para esta etapa.

El periodo de estudio es octubre de 2015–diciembre de 2025. Los datos de 2025 se reservan para evaluación final. El notebook construye los retardos según la disponibilidad de publicación, define la evaluación temporal y comprueba la imputación hotelera dentro de cada entrenamiento. Incluye Seasonal Naïve y SARIMA; la puntuación final de 2025 permanece desactivada.

## Análisis exploratorio

Las secciones 12–18 del notebook incluyen seis gráficas comentadas: evolución de turistas, estacionalidad mensual, caída y recuperación respecto a 2019, relaciones con aeropuerto y hoteles, correlaciones y mapa de ausentes. Se guardan también las figuras y cinco tablas de apoyo en `outputs/eda/`, junto con los parámetros y versiones de la ejecución.

Las relaciones y los perfiles estacionales se calculan con datos hasta diciembre de 2024. El año 2025 aparece únicamente como contexto en la evolución general y la revisión de cobertura; esta inspección descriptiva se declara como limitación del aislamiento del conjunto de prueba. Las conclusiones orientan el calendario, los retardos, el tratamiento de la pandemia y los ausentes, sin transformar todavía el dataset para entrenar modelos. La meteorología sigue pendiente; las reglas de disponibilidad se concretan en el bloque siguiente.

## Disponibilidad de los predictores

Las secciones 19–21 documentan las fuentes oficiales de publicación y fijan el pronóstico al cierre de cada mes. La regla base permite AENA y hoteles hasta el mes anterior y turistas hasta dos meses antes; distingue los retardos respecto al origen de los retardos respecto a los objetivos a uno y tres meses. Se comprueban los desplazamientos, el bloqueo ante una publicación tardía y la conservación de ausentes y ceros.

`outputs/disponibilidad/` contiene la política, la evidencia de fechas efectivas y previstas, los retardos mínimos, la auditoría y dos vistas por origen (regla base y un mes adicional de espera). Estas vistas no son todavía matrices definitivas de entrenamiento. Las fechas de primera publicación y las versiones históricas no se han reconstruido para todo 2015–2025: la evaluación será una simulación retrospectiva bajo esta política, con la limitación de revisiones posteriores. La meteorología sigue pendiente.

## Google Trends

Las secciones 7 bis y 22–24 incorporan los cuatro CSV de `Datasets/Google Trends`: Mallorca/Majorca en Alemania/Reino Unido, categoría Viajes, enero de 2015–diciembre de 2025. Se comprueban cabeceras, calendario, duplicados y rango 0–100; se conservan los índices por separado. El maestro incluye los 123 meses comunes y la extracción auxiliar conserva 132 meses. El inventario registra SHA256 y el catálogo deja sin completar los metadatos no acreditados en los CSV.

La exploración añade tres figuras y cuatro tablas hasta 2024: evolución, perfiles mensuales, correlaciones en niveles/diferencias interanuales con retardos y redundancia entre índices. No selecciona predictores ni ajusta modelos. La disponibilidad adopta t−1 como supuesto conservador y t−2 como sensibilidad; no son plazos oficiales comprobados. La descarga posterior, el muestreo y la normalización sobre 2015–2025 impiden reconstruir exactamente la información histórica por origen, aun excluyendo las filas de 2025 de las relaciones exploradas.

## SARIMA

Las secciones 33–36 implementan SARIMA con la serie de turistas, sin variables externas. Se conservan los ceros de la pandemia. Ocho configuraciones con estacionalidad de 12 meses se comparan mediante validación progresiva de enero de 2020 a julio de 2024. Se exige cobertura y convergencia completas; se elige el menor RMSE por horizonte y escenario de disponibilidad. El diagnóstico de agosto–diciembre de 2024 es retrospectivo y no equivale a una prueba independiente.

Los horizontes de uno y tres meses se evalúan sobre los mismos meses que Seasonal Naïve. El retardo de publicación del objetivo requiere tres y cinco pasos internos en el escenario base. En 2025 se permite actualizar el estado con observaciones ya publicadas; los parámetros se estiman únicamente con historia anterior a 2025. `EVALUATE_FINAL_2025=False` genera los pronósticos reservados sin calcular sus errores ni métricas.

`outputs/modelos/sarima/` guarda la búsqueda, las configuraciones seleccionadas, los pronósticos, las métricas por bloque/año/periodo, la comparación con Seasonal Naïve, los avisos y parámetros de cada ajuste y una figura de validación. Las predicciones negativas se limitan a cero según una regla previa; también se exportan las predicciones originales y sus métricas. Los controles verifican el calendario, la ausencia de datos futuros en una emisión y la conservación de las fuentes. La primera ejecución puede tardar varios minutos por los ajustes repetidos de la búsqueda; dentro de cada ejecución se reutilizan ajustes con la misma configuración e historia disponible.
