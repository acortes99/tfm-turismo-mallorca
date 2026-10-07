"""Build and execute the project's documented notebook without a Jupyter server."""
import contextlib, io, json, sys, traceback
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[1]
cells = []
def md(text):
    cells.append({'cell_type':'markdown','metadata':{},'source':text.strip().splitlines(True)})
def code(text):
    cells.append({'cell_type':'code','metadata':{},'source':text.strip().splitlines(True), 'execution_count':None,'outputs':[]})

md('''# ETL y revisión de datos del TFM
**Predicción del flujo turístico en Mallorca mediante modelos de inteligencia artificial y variables externas**

Este notebook documenta y ejecuta la extracción, limpieza e integración de las fuentes del proyecto. Los Excel originales permanecen intactos. Cada ejecución genera el dataset maestro y evidencias de calidad en `outputs/etl/`.

## 1. Alcance y decisiones metodológicas
La variable objetivo es el número mensual de turistas cuyo destino principal es Mallorca, para el agregado de residencia «Mundo (excluida Illes Balears)». No se suman países y agregados porque se solapan. El periodo de estudio es octubre de 2015–diciembre de 2025: 123 meses antes de crear retardos. Los datos anteriores a 2025 se destinan al entrenamiento y validación temporal; 2025 se reserva para la evaluación final.

Las variables externas son pasajeros y operaciones del aeropuerto de Palma, viajeros hoteleros, pernoctaciones, estancia media y ocupación. Las estadísticas aeroportuarias incluyen llegadas y salidas; los viajeros de hoteles y los turistas de FRONTUR son poblaciones distintas. No se interpretan como medidas equivalentes ni como relaciones causales.

AEMET está pendiente de acceso. No se fabrican columnas meteorológicas ni se sustituyen por ceros. La integración meteorológica será una ampliación del ETL.

## 2. Reproducción
Desde la raíz del repositorio: `python -m pip install -r requirements.txt` y `jupyter lab`. Abrir este notebook y ejecutar **Restart Kernel and Run All Cells**. Requiere las carpetas originales `Datasets/Tráfico aéreo`, `Datasets/Alojamiento` y `Datasets/Dataset Principal.xlsx`. Las rutas son relativas al proyecto. No requiere red ni claves de API para procesar las descargas actuales.

El resultado se guarda al final, únicamente si pasan las comprobaciones estructurales. Los ausentes documentados no impiden exportar; permanecen identificados para decidir su tratamiento en la fase de modelización.''')
code('''from pathlib import Path
import hashlib
import importlib.metadata
import json
import platform
import re
import unicodedata
import pandas as pd
from openpyxl import load_workbook
import xlrd

# Si se ejecuta desde otra carpeta, indicar aquí la raíz del repositorio.
PROJECT_ROOT = Path.cwd()
assert (PROJECT_ROOT / "Datasets").is_dir(), "Ejecutar desde la raíz del repositorio."
DATA_ROOT = PROJECT_ROOT / "Datasets"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "etl"
START, END = "2015-10-01", "2025-12-01"
EXPECTED = pd.date_range(START, END, freq="MS")
AIR_EXPECTED = pd.date_range("2015-01-01", END, freq="MS")
versions = {p: importlib.metadata.version(p) for p in ["pandas", "openpyxl", "xlrd"]}
print("Python:", platform.python_version(), "Dependencias:", versions)
print("Periodo:", EXPECTED.min().date(), "a", EXPECTED.max().date(), "Meses:", len(EXPECTED))''')
md('''## 3. Fuentes y trazabilidad
| Fuente | Archivo o carpeta | Selección | Unidad |
|---|---|---|---|
| IBESTAT / FRONTUR | Dataset Principal.xlsx | Mallorca, TURISTAS, 5000_XIB | Personas |
| AENA | Tráfico aéreo / año / informe mensual | PALMA DE MALLORCA, pasajeros y operaciones | Movimientos de pasajeros / aterrizajes y despegues |
| IBESTAT / ocupación hotelera | Alojamiento / Grado de ocupación… | Mallorca, categoría HOTEL | Porcentaje |
| IBESTAT / demanda hotelera | Alojamiento / Viajeros entrados… | Mallorca, residencia _T (Total) | Viajeros / noches / noches por viajero |

Fuentes de descarga: [AENA](https://www.aena.es/es/estadisticas/informes-mensuales.html), [IBESTAT](https://ibestat.es/edatos/apps/catalogo/es/dataset/?groups=turismo) y [AEMET OpenData, pendiente](https://opendata.aemet.es/centrodedescargas/productosAEMET).

Se registra una huella SHA-256 por archivo para identificar exactamente las descargas empleadas. La huella no acredita la exactitud estadística; permite detectar cambios en los archivos. La fecha de descarga no se conoce y no se inventa.''')
code('''tourism_path = DATA_ROOT / "Dataset Principal.xlsx"
occupancy_path = DATA_ROOT / "Alojamiento" / "Grado de ocupación hotelera por categoría, isla y mes.xlsx"
hotel_path = DATA_ROOT / "Alojamiento" / "Viajeros entrados, pernoctaciones y estancia media en establecimientos hoteleros.xlsx"
air_paths = sorted((DATA_ROOT / "Tráfico aéreo").rglob("*.xls*"))
source_paths = [tourism_path, occupancy_path, hotel_path, *air_paths]
assert air_paths, "No se encontraron informes AENA."
assert all(p.is_file() for p in source_paths), "Falta una fuente requerida."
manifest = pd.DataFrame([{
    "archivo": p.relative_to(PROJECT_ROOT).as_posix(),
    "bytes": p.stat().st_size,
    "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
} for p in source_paths])
print("Archivos incluidos:", len(manifest), "Informes AENA:", len(air_paths))
display(manifest.head())''')
md('''## 4. Reglas comunes de limpieza
Se seleccionan los periodos con código `AAAA-Mmm`; las filas anuales se excluyen. Cada tabla filtrada debe tener una sola fila por mes. Las conversiones numéricas rechazan textos inesperados, en lugar de ocultarlos como ausentes. Los vacíos permanecen como valores ausentes; un cero numérico permanece como cero.

Se conservan los estados de observación de la fuente: `A` = valor normal, `P` = valor provisional, `U` = baja fiabilidad y `O` = valor no disponible. Un valor ausente y su estado se revisan por separado. El ETL no interpola, no normaliza, no elimina la pandemia y no calcula medias con el conjunto de evaluación.''')
code('''def number(values):
    clean = values.replace(r"^\\s*$", pd.NA, regex=True)
    return pd.to_numeric(clean, errors="raise")

def select_monthly(frame, filters):
    required = {"TIME_PERIOD_CODE", "OBS_VALUE", "ESTADO_OBSERVACION_CODE", *filters}
    assert required <= set(frame.columns), f"Faltan columnas: {required - set(frame.columns)}"
    mask = frame["TIME_PERIOD_CODE"].astype(str).str.fullmatch(r"\\d{4}-M\\d{2}")
    for column, value in filters.items():
        mask &= frame[column].eq(value)
    selected = frame.loc[mask].copy()
    assert not selected.empty, f"Selección vacía: {filters}"
    selected["fecha"] = pd.to_datetime(selected["TIME_PERIOD_CODE"].str.replace("-M", "-", regex=False), format="%Y-%m")
    selected["valor"] = number(selected["OBS_VALUE"])
    assert not selected["fecha"].duplicated().any(), f"Meses duplicados: {filters}"
    return selected.sort_values("fecha").set_index("fecha")

def source_series(selected, name):
    return selected[["valor", "ESTADO_OBSERVACION_CODE"]].rename(columns={
        "valor": name, "ESTADO_OBSERVACION_CODE": name + "_estado"
    })''')
md('''## 5. Extracción de la variable objetivo
Se utiliza el agregado total disponible de Mallorca. Las tasas de variación se excluyen: no son recuentos de turistas y su importación presenta problemas de escala. Los valores provisionales y los ceros de baja fiabilidad se conservan con su estado. La evaluación posterior deberá explicar esta limitación de calidad y el uso de una descarga revisada, no de las versiones históricas disponibles en cada fecha.''')
code('''tourism_raw = pd.read_excel(tourism_path, sheet_name=0, engine="openpyxl")
tourism_selected = select_monthly(tourism_raw, {
    "TERRITORIO_CODE": "ES532", "MEDIDAS_CODE": "TURISTAS", "LUGAR_RESIDENCIA_CODE": "5000_XIB"
})
tourism = source_series(tourism_selected, "turistas")
assert tourism.reindex(EXPECTED)["turistas"].notna().all(), "Faltan turistas en el periodo de estudio."
print("Histórico objetivo:", tourism.index.min().date(), "a", tourism.index.max().date())
display(tourism.loc[START:END].head())''')
md('''## 6. Extracción de AENA y revisión de formatos
Los informes antiguos son `.xls` y los recientes `.xlsx`. Las hojas y las columnas cambian entre años. Se ignoran las hojas técnicas «Mozart Reports», se identifica la hoja estadística y se comprueba el mes y año de su cabecera frente al nombre del archivo. Se detiene la lectura antes del bloque acumulado, cuando aparece.

Los tres bloques horizontales corresponden a pasajeros, operaciones y mercancías. Se localiza Palma en cada bloque y se toma el primer número a su derecha, admitiendo las columnas vacías de las versiones antiguas. Se comprueban los rótulos y el orden de los bloques; se excluyen mercancías y porcentajes de variación. Se registra archivo, hoja y posición de cada cifra extraída. Cualquier formato inesperado detiene la ejecución.''')
code('''def norm(value):
    text = unicodedata.normalize("NFKD", str(value))
    return "".join(c for c in text if not unicodedata.combining(c)).upper().strip()

MONTH_NAMES = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]

def air_sheets(path):
    if path.suffix.lower() == ".xls":
        book = xlrd.open_workbook(path)
        return [(s.name, [s.row_values(i) for i in range(s.nrows)]) for s in book.sheets()
                if s.name != "Mozart Reports" and "ACUMUL" not in norm(s.name)]
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        return [(s.title, list(s.values)) for s in book
                if s.title != "Mozart Reports" and "ACUMUL" not in norm(s.title)]
    finally:
        book.close()

def extract_air(path):
    year = int(path.parent.name)
    month = int(re.match(r"\\d+", path.name).group())
    assert 1 <= month <= 12
    candidates = []
    for name, rows in air_sheets(path):
        header = " ".join(norm(v) for row in rows[:10] for v in row if v is not None)
        if "ACUMULADO" in header:
            continue
        if "PASAJEROS" not in header or "OPERACIONES" not in header:
            continue
        assert str(year) in header and MONTH_NAMES[month - 1] in header, f"Cabecera/archivo no coinciden: {path.name}"
        block_positions = {}
        for row in rows[:12]:
            for column, value in enumerate(row):
                for block in ["PASAJEROS", "OPERACIONES", "MERCANC"]:
                    if norm(value).startswith(block):
                        block_positions.setdefault(block, column)
        assert len(block_positions) == 3, f"Bloques desconocidos: {path.name}"
        assert block_positions["PASAJEROS"] < block_positions["OPERACIONES"] < block_positions["MERCANC"]
        hits = []
        for i, row in enumerate(rows):
            if any("ACUMULADO" in norm(v) for v in row if v is not None):
                break
            for j, value in enumerate(row):
                if norm(value) == "PALMA DE MALLORCA":
                    numbers = [(j+k+1, v) for k, v in enumerate(row[j+1:j+4])
                               if isinstance(v, (int, float)) and not isinstance(v, bool)]
                    assert numbers, f"Sin cifra de Palma: {path.name}"
                    c, amount = numbers[0]
                    assert amount >= 0 and float(amount).is_integer(), f"Recuento inválido: {path.name}"
                    hits.append((j, i, c, int(amount)))
        hits.sort()
        assert len(hits) == 3 and len({h[0] for h in hits}) == 3, f"Bloques Palma ambiguos: {path.name}"
        # Primera columna de aeropuertos: pasajeros; segunda: operaciones.
        candidates.append({"fecha": pd.Timestamp(year, month, 1), "pasajeros_aena": hits[0][3],
                           "operaciones_aena": hits[1][3], "archivo_aena": path.relative_to(PROJECT_ROOT).as_posix(),
                           "hoja_aena": name, "fila_pasajeros": hits[0][1]+1, "columna_pasajeros": hits[0][2]+1,
                           "fila_operaciones": hits[1][1]+1, "columna_operaciones": hits[1][2]+1,
                           "estado_cabecera": "provisional" if "PROVISIONAL" in header else "definitivo" if "DEFINITIV" in header else "no identificado"})
    assert len(candidates) == 1, f"Hoja mensual ambigua/ausente: {path.name}"
    return candidates[0]

air_audit = pd.DataFrame([extract_air(path) for path in air_paths]).sort_values("fecha")
assert not air_audit["fecha"].duplicated().any(), "Informes mensuales duplicados."
assert set(air_audit["fecha"]) == set(AIR_EXPECTED), "Faltan o sobran meses AENA 2015–2025."
air = air_audit.set_index("fecha")[["pasajeros_aena", "operaciones_aena", "estado_cabecera"]].rename(columns={"estado_cabecera":"aena_estado"})
print("Informes mensuales comprobados:", len(air))
display(air_audit.loc[air_audit["fecha"].dt.month.eq(1), ["fecha", "pasajeros_aena", "operaciones_aena", "hoja_aena"]])''')
md('''## 7. Actividad hotelera y comprobación de decimales
La ocupación se selecciona para Mallorca y la categoría agregada `HOTEL`; los porcentajes no se suman entre categorías. Viajeros y pernoctaciones se seleccionan para Mallorca y residencia `_T` (Total), sin volver a sumar países.

La estancia media importada debe verificarse contra `pernoctaciones / viajeros`. Para cada mes con denominador positivo se contrasta tanto el valor original como el valor dividido entre 100. Solo se corrige cuando la segunda interpretación coincide con el cociente dentro de 0,015 noches, tolerancia para el redondeo de la estadística a dos decimales. No se aplica una división indiscriminada. Los casos sin referencia verificable permanecen ausentes y los casos incompatibles detienen la ejecución. Se conserva el valor original y se exporta la decisión de cada fila.''')
code('''occupancy_raw = pd.read_excel(occupancy_path, sheet_name=0, engine="openpyxl")
occupancy_measures = {
    "GRADO_OCUPACION_HABITACION_TURISTICA": "ocupacion_habitaciones_pct",
    "GRADO_OCUPACION_PLAZA_TURISTICA": "ocupacion_plazas_pct",
    "GRADO_OCUPACION_PLAZA_TURISTICA_FIN_SEMANA": "ocupacion_fin_semana_pct",
}
occupancy_parts = []
for measure, name in occupancy_measures.items():
    selected = select_monthly(occupancy_raw, {"TERRITORIO_CODE":"ES532", "ALOJAMIENTOS_TURISTICOS_CODE":"HOTEL", "MEDIDAS_CODE":measure})
    assert selected["valor"].dropna().between(0, 100).all(), f"Ocupación fuera de rango: {name}"
    occupancy_parts.append(source_series(selected, name))
occupancy = pd.concat(occupancy_parts, axis=1)

hotel_raw = pd.read_excel(hotel_path, sheet_name=0, engine="openpyxl")
hotel_measures = {"VIAJEROS":"viajeros_hoteles", "PERNOCTACION_TURISTICA":"pernoctaciones_hoteles", "ESTANCIA_MEDIA":"estancia_media_original"}
hotel_parts = []
for measure, name in hotel_measures.items():
    selected = select_monthly(hotel_raw, {"TERRITORIO_CODE":"ES532", "LUGAR_RESIDENCIA_CODE":"_T", "MEDIDAS_CODE":measure})
    hotel_parts.append(source_series(selected, name))
hotel = pd.concat(hotel_parts, axis=1)
ratio = hotel["pernoctaciones_hoteles"].div(hotel["viajeros_hoteles"].where(hotel["viajeros_hoteles"] > 0))
original = hotel["estancia_media_original"]
direct = original.sub(ratio).abs().le(0.015)
scaled = original.div(100).sub(ratio).abs().le(0.015) & ~direct
verifiable = original.notna() & ratio.notna()
assert (direct | scaled | ~verifiable).all(), "Hay estancias medias incompatibles: revisar la fuente."
hotel["estancia_media_noches"] = original.where(direct).combine_first(original.div(100).where(scaled))
hotel["estancia_media_noches_estado"] = hotel["estancia_media_original_estado"]
hotel["estancia_media_ajuste"] = "sin referencia o valor ausente"
hotel.loc[direct, "estancia_media_ajuste"] = "original verificado"
hotel.loc[scaled, "estancia_media_ajuste"] = "división entre 100 verificada"
decimal_audit = hotel[["viajeros_hoteles", "pernoctaciones_hoteles", "estancia_media_original", "estancia_media_noches", "estancia_media_ajuste"]].assign(cociente=ratio)
print("Correcciones de escala en el periodo de estudio:", int(scaled.reindex(EXPECTED, fill_value=False).sum()))
display(decimal_audit.loc[START:END].head())''')
md('''## 8. Integración y controles de calidad
Se construye un calendario maestro de 123 meses y se incorporan las tablas con una unión por fecha, sin eliminar meses por tener ausentes. Se comprueba la cobertura de cada fuente por separado para distinguir un periodo ausente de una observación presente sin valor. Se controlan fechas duplicadas, valores no negativos, recuentos enteros y límites de ocupación.

El informe presenta los meses con ausentes y los estados de calidad. La presencia de una fila no significa que su valor sea fiable. Los meses de la pandemia permanecen en el histórico para que los experimentos posteriores puedan evaluar su impacto.''')
code('''for name, table in {"turistas":tourism, "aena":air, "ocupacion":occupancy, "hoteles":hotel}.items():
    assert table.index.is_unique, f"Índice duplicado: {name}"
    assert set(EXPECTED) <= set(table.index), f"Faltan periodos en {name}"
master = pd.DataFrame(index=EXPECTED).join(tourism).join(air).join(occupancy).join(hotel)
master.index.name = "fecha"
assert len(master) == 123 and master.index.is_monotonic_increasing
VALUE_COLUMNS = ["turistas", "pasajeros_aena", "operaciones_aena", "viajeros_hoteles", "pernoctaciones_hoteles", "estancia_media_noches", *occupancy_measures.values()]
assert (master[VALUE_COLUMNS].dropna(how="all").ge(0) | master[VALUE_COLUMNS].isna()).all().all(), "Valores negativos."
for column in ["turistas", "pasajeros_aena", "operaciones_aena", "viajeros_hoteles", "pernoctaciones_hoteles"]:
    assert master[column].dropna().mod(1).eq(0).all(), f"Recuento no entero: {column}"
quality = pd.DataFrame({"variable":VALUE_COLUMNS,
    "observaciones": [int(master[c].notna().sum()) for c in VALUE_COLUMNS],
    "ausentes": [int(master[c].isna().sum()) for c in VALUE_COLUMNS]})
missing_details = pd.DataFrame([{"fecha":d, "variable":c, "estado":master.loc[d, c+"_estado"] if c+"_estado" in master else "sin estado"}
                               for c in VALUE_COLUMNS for d in master.index[master[c].isna()]])
state_columns = [c for c in master if c.endswith("_estado")]
states = pd.concat([master[c].value_counts(dropna=False).rename_axis("estado").reset_index(name="meses").assign(variable=c) for c in state_columns], ignore_index=True)
print("Controles estructurales y de rango superados.")
display(quality)
display(missing_details)
display(master[["turistas", "viajeros_hoteles", "pernoctaciones_hoteles", "ocupacion_plazas_pct"]].loc["2020-03-01":"2020-12-01"])''')
md('''## 9. Disponibilidad temporal y prevención de fuga de información
El dataset maestro contiene medidas observadas del mismo mes, útiles para exploración y trazabilidad; **no es todavía una matriz de predictores válida para pronosticar ese mes**. Predecir julio con las cifras observadas de julio produciría fuga de información.

Los retardos deberán considerar el horizonte y el calendario de publicación de cada fuente. Un retardo de un mes no garantiza disponibilidad real: las estadísticas de turismo y alojamiento pueden publicarse después del cierre del mes. No se conocen aquí las fechas históricas de publicación ni las versiones disponibles en cada origen de pronóstico; por ello, la evaluación será retrospectiva con datos revisados y deberá declarar esta limitación, o reconstruir esa disponibilidad antes de afirmar un uso operativo.

La generación de retardos, imputación y ajuste de modelos se hará en otra etapa. Las transformaciones que aprendan parámetros se ajustarán solo en entrenamiento y en cada partición temporal. No se usarán meses posteriores para interpolar predictores, elegir modelos o ajustar hiperparámetros. El cociente de estancia media es una comprobación determinista entre medidas del mismo registro, no un parámetro aprendido del conjunto de evaluación.''')
code('''split_summary = pd.DataFrame([
    {"uso":"Entrenamiento y validación temporal", "inicio":master.loc[:"2024-12-01"].index.min(), "fin":pd.Timestamp("2024-12-01"), "meses":len(master.loc[:"2024-12-01"])},
    {"uso":"Evaluación final reservada", "inicio":pd.Timestamp("2025-01-01"), "fin":pd.Timestamp("2025-12-01"), "meses":len(master.loc["2025-01-01":])},
])
assert split_summary["meses"].tolist() == [111, 12]
display(split_summary)''')
md('''## 10. Exportación y conclusiones de la revisión
Se exportan el dataset maestro, el inventario de fuentes, la extracción AENA, la auditoría de decimales, los ausentes y las marcas de calidad. El CSV conserva las columnas de estado y deja vacíos los valores ausentes. Los archivos de salida se regeneran al ejecutar el notebook; los originales no se modifican.

La tabla de calidad anterior es la evidencia de cobertura de esta ejecución. La integración de meteorología y la preparación para pronósticos quedan pendientes. Las tasas de variación hoteleras se excluyen por alcance y por problemas de escala; no se necesitan para construir el conjunto inicial. Si se cambia una selección, una fuente o el periodo, hay que volver a ejecutar todos los controles.''')
code('''OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
master.reset_index().to_csv(OUTPUT_DIR / "dataset_maestro_mallorca.csv", index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
manifest.to_csv(OUTPUT_DIR / "inventario_fuentes.csv", index=False, encoding="utf-8-sig")
air_audit.to_csv(OUTPUT_DIR / "auditoria_aena.csv", index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
decimal_audit.loc[START:END].reset_index().to_csv(OUTPUT_DIR / "auditoria_decimales.csv", index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
quality.to_csv(OUTPUT_DIR / "calidad_variables.csv", index=False, encoding="utf-8-sig")
missing_details.to_csv(OUTPUT_DIR / "valores_ausentes.csv", index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
states.to_csv(OUTPUT_DIR / "estados_observacion.csv", index=False, encoding="utf-8-sig")
metadata = {"python":platform.python_version(), "dependencias":versions, "periodo":[START, END],
            "filas":len(master), "archivos_fuente":len(manifest), "aemet":"pendiente",
            "imputacion":"no realizada", "disponibilidad_historica":"no reconstruida"}
(OUTPUT_DIR / "ejecucion.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
check_saved = pd.read_csv(OUTPUT_DIR / "dataset_maestro_mallorca.csv", parse_dates=["fecha"])
assert len(check_saved) == len(master)
assert check_saved[VALUE_COLUMNS].isna().sum().tolist() == master[VALUE_COLUMNS].isna().sum().tolist()
for column in VALUE_COLUMNS:
    pd.testing.assert_series_equal(check_saved[column].reset_index(drop=True), master[column].reset_index(drop=True), check_dtype=False, check_names=False)
print("Dataset exportado y contrastado con la tabla en memoria:", len(check_saved), "meses.")
print("Salidas:", OUTPUT_DIR.relative_to(PROJECT_ROOT).as_posix())''')
md('''## 11. Resultado de la ejecución revisada
Se han integrado 135 archivos originales, incluidos 132 informes mensuales AENA de enero de 2015 a diciembre de 2025. El dataset maestro contiene 123 meses del periodo común seleccionado. Turistas, pasajeros y operaciones tienen cobertura numérica completa.

Los ausentes hoteleros se concentran en 2020: viajeros y pernoctaciones en mayo; estancia media en abril y mayo; los tres indicadores de ocupación en mayo y diciembre. Se preservan estos valores vacíos y su marca `U` (baja fiabilidad). Los ceros de turistas de abril y mayo de 2020 también llevan `U`; conservarlos no implica considerarlos plenamente fiables.

Se han corregido 121 registros de estancia media cuya escala original era cien veces la compatible con el cociente de pernoctaciones y viajeros. La auditoría conserva el valor original, el cociente y la corrección. Las cabeceras de los 12 informes AENA de 2025 indican datos provisionales; esta característica debe declararse al interpretar la evaluación final.

**Conclusión:** las fuentes permiten construir el histórico mensual y comenzar el análisis exploratorio. Para los modelos quedan pendientes meteorología, tratamiento de los ausentes y definición de predictores disponibles en cada fecha de pronóstico. Los recuentos anteriores corresponden a las descargas actuales; ante cambios de archivos debe volver a revisarse la tabla de calidad y las auditorías.''')

notebook = {'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':sys.version.split()[0]}},'nbformat':4,'nbformat_minor':5}
for n, cell in enumerate(cells):cell['id']=f'etl-{n:02}'
path=ROOT/'tfm-turismo-viu.ipynb'
path.write_text(json.dumps(notebook,ensure_ascii=False,indent=1),encoding='utf-8')

# Execute the same code cells and persist their actual outputs. No alternate ETL implementation.
sys.path.insert(0,str(ROOT/'work'/'pydeps'))
import os
os.chdir(ROOT)
namespace={}
count=0
for cell in cells:
    if cell['cell_type']!='code':continue
    count+=1
    print(f'Executing ETL cell {count}',flush=True)
    outputs=[]
    def display(value):
        data={'text/plain':str(value)}
        if hasattr(value,'to_html'):data['text/html']=value.to_html(index=True)
        outputs.append({'output_type':'display_data','data':data,'metadata':{}})
    namespace['display']=display
    buffer=io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):exec(compile(''.join(cell['source']),f'notebook-cell-{count}','exec'),namespace)
    except Exception:
        print(buffer.getvalue())
        traceback.print_exc()
        raise
    if buffer.getvalue():outputs.insert(0,{'output_type':'stream','name':'stdout','text':buffer.getvalue()})
    cell['execution_count']=count;cell['outputs']=outputs
    path.write_text(json.dumps(notebook,ensure_ascii=False,indent=1),encoding='utf-8')
    print(buffer.getvalue(),end='',flush=True)
print('Notebook execution completed successfully.')
