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
