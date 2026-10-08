# tfm-turismo-mallorca
Predicción del flujo turístico mensual en Mallorca mediante series temporales y aprendizaje automático. Incluye ETL reproducible, integración de variables externas, comparación de modelos e interpretabilidad, como parte de un TFM en Big Data y Ciencia de Datos.

## ETL documentado

El notebook `tfm-turismo-viu.ipynb` contiene la explicación, el código y los resultados de revisión del ETL. Lee los archivos originales de `Datasets/` mediante rutas relativas y genera `outputs/etl/` sin modificar las fuentes.

```shell
python -m pip install -r requirements.txt
jupyter lab
```

Abrir el notebook desde la raíz del repositorio y ejecutar todas las celdas en orden con un kernel nuevo. Los archivos de salida se regeneran con cada ejecución. El notebook comprueba los formatos mensuales de AENA, la cobertura de Mallorca, los duplicados, las unidades, los ausentes y la escala de estancia media. La meteorología está pendiente; no se requiere una API key para esta etapa.

El periodo de estudio es octubre de 2015–diciembre de 2025. Los datos de 2025 se reservan para evaluación final. El dataset maestro contiene observaciones contemporáneas: antes de entrenar hay que definir retardos según la disponibilidad de publicación y tratar los ausentes dentro de las particiones de entrenamiento. No se han entrenado modelos ni imputado valores en este notebook.

## Análisis exploratorio

Las secciones 12–18 del notebook incluyen seis gráficas comentadas: evolución de turistas, estacionalidad mensual, caída y recuperación respecto a 2019, relaciones con aeropuerto y hoteles, correlaciones y mapa de ausentes. Se guardan también las figuras y cinco tablas de apoyo en `outputs/eda/`, junto con los parámetros y versiones de la ejecución.

Las relaciones y los perfiles estacionales se calculan con datos hasta diciembre de 2024. El año 2025 aparece únicamente como contexto en la evolución general y la revisión de cobertura; esta inspección descriptiva se declara como limitación del aislamiento del conjunto de prueba. Las conclusiones orientan el calendario, los retardos, el tratamiento de la pandemia y los ausentes, sin transformar todavía el dataset para entrenar modelos. La meteorología sigue pendiente; las reglas de disponibilidad se concretan en el bloque siguiente.

## Disponibilidad de los predictores

Las secciones 19–21 documentan las fuentes oficiales de publicación y fijan el pronóstico al cierre de cada mes. La regla base permite AENA y hoteles hasta el mes anterior y turistas hasta dos meses antes; distingue los retardos respecto al origen de los retardos respecto a los objetivos a uno y tres meses. Se comprueban los desplazamientos, el bloqueo ante una publicación tardía y la conservación de ausentes y ceros.

`outputs/disponibilidad/` contiene la política, la evidencia de fechas efectivas y previstas, los retardos mínimos, la auditoría y dos vistas por origen (regla base y un mes adicional de espera). Estas vistas no son todavía matrices definitivas de entrenamiento. Las fechas de primera publicación y las versiones históricas no se han reconstruido para todo 2015–2025: la evaluación será una simulación retrospectiva bajo esta política, con la limitación de revisiones posteriores. La meteorología sigue pendiente.
