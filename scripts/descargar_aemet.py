"""Descarga climatologías mensuales de AEMET. Clave solo en AEMET_API_KEY."""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

BASE = "https://opendata.aemet.es/opendata"


def fetch(url, key=None):
    if urlparse(url).scheme != "https" or urlparse(url).hostname != "opendata.aemet.es":
        raise ValueError("La descarga debe proceder de HTTPS de AEMET")
    headers = {"Accept": "application/json", "User-Agent": "TFM-turismo-Mallorca/1.0"}
    if key:
        headers["api_key"] = key
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=45) as response:
                raw = response.read()
                encoding = response.headers.get_content_charset() or "utf-8"
            try:
                parsed = json.loads(raw.decode("utf-8-sig"))
            except UnicodeDecodeError:
                parsed = json.loads(raw.decode(encoding if encoding.lower() != "utf-8" else "iso-8859-1"))
            return raw, parsed
        except urllib.error.HTTPError as error:
            if error.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(10 * (attempt + 1))
                continue
            raise RuntimeError(f"AEMET devolvió HTTP {error.code}; no se registran credenciales") from None
        except (urllib.error.URLError, TimeoutError):
            if attempt < 3:
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError("No se pudo conectar con AEMET tras cuatro intentos") from None


def product(endpoint, key, folder, name):
    _, envelope = fetch(BASE + endpoint, key)
    if envelope.get("estado") != 200:
        raise RuntimeError(f"AEMET: estado {envelope.get('estado')}; producto {name}")
    raw, data = fetch(envelope["datos"])
    filename = folder / (name + ".json")
    filename.write_bytes(raw)
    files = {filename.name: hashlib.sha256(raw).hexdigest()}
    if envelope.get("metadatos"):
        meta_raw, _ = fetch(envelope["metadatos"])
        meta_file = folder / (name + "_metadatos.json")
        meta_file.write_bytes(meta_raw)
        files[meta_file.name] = hashlib.sha256(meta_raw).hexdigest()
    return data, {"endpoint": endpoint, "archivos_sha256": files,
                  "filas": len(data) if isinstance(data, list) else None}


def prepare_monthly(records, station, folder, start, end):
    import pandas as pd
    fields = {"tm_mes": "temperatura_media_c", "tm_max": "temperatura_media_maximas_c",
              "tm_min": "temperatura_media_minimas_c", "p_mes": "precipitacion_mm",
              "hr": "humedad_relativa_pct", "inso": "insolacion_media_diaria_h",
              "w_med": "viento_medio_kmh", "n_llu": "dias_lluvia",
              "np_010": "dias_precipitacion_ge_1mm", "nt_30": "dias_maxima_ge_30c"}
    monthly, annual = [], []
    for record in records:
        year, month = map(int, record["fecha"].split("-"))
        if record["indicativo"] != station:
            raise ValueError("Indicativo distinto del solicitado")
        if month == 13:
            annual.append(record)
            continue
        if not 1 <= month <= 12 or not start <= year <= end:
            raise ValueError("Fecha fuera del periodo solicitado")
        row = {"fecha": pd.Timestamp(year, month, 1), "estacion": station}
        for field, name in fields.items():
            value = record.get(field)
            text = "" if value is None else str(value).strip()
            numeric = bool(re.fullmatch(r"[+-]?\d+(?:[.,]\d+)?", text))
            row[name] = float(text.replace(",", ".")) if numeric else float("nan")
            row[name + "_estado"] = "observado" if numeric else ("ausente" if not text else "no_numerico")
            row[name + "_original"] = text
        monthly.append(row)
    frame = pd.DataFrame(monthly).set_index("fecha").sort_index()
    if not frame.index.is_unique:
        raise ValueError("Meses duplicados")
    expected = pd.date_range(f"{start}-01-01", f"{end}-12-01", freq="MS")
    missing_months = expected.difference(frame.index)
    frame = frame.reindex(expected)
    frame.index.name = "fecha"
    frame["estacion"] = station
    for name in fields.values():
        frame[name + "_estado"] = frame[name + "_estado"].fillna("mes_no_recibido")
    for name in ["precipitacion_mm", "viento_medio_kmh", "dias_lluvia", "dias_precipitacion_ge_1mm", "dias_maxima_ge_30c"]:
        if (frame[name].dropna() < 0).any():
            raise ValueError("Valor negativo inesperado: " + name)
    if not frame.humedad_relativa_pct.dropna().between(0, 100).all():
        raise ValueError("Humedad fuera de rango")
    if not frame.insolacion_media_diaria_h.dropna().between(0, 24).all():
        raise ValueError("Insolación diaria fuera de rango")
    for name in ["dias_lluvia", "dias_precipitacion_ge_1mm", "dias_maxima_ge_30c"]:
        if (frame[name] > frame.index.days_in_month).any():
            raise ValueError("Número de días fuera de rango: " + name)
    filename = folder / f"mensual_limpio_{station}_{start}_{end}.csv"
    frame.to_csv(filename, encoding="utf-8-sig")
    annual_file = folder / f"anuales_{station}_{start}_{end}.json"
    annual_file.write_text(json.dumps(annual, ensure_ascii=False, indent=2), encoding="utf-8")
    report = {"estacion": station, "meses_esperados": len(expected), "meses_recibidos": len(monthly),
              "meses_no_recibidos": [str(d.date()) for d in missing_months], "registros_anuales_separados": len(annual),
              "ausentes_por_variable": frame[list(fields.values())].isna().sum().to_dict(),
              "campos": fields, "csv_sha256": hashlib.sha256(filename.read_bytes()).hexdigest(),
              "imputacion": False, "trazas_o_valores_no_numericos": "conservar original y marcar; no convertir automaticamente en cero",
              "insolacion": "media diaria del mes en horas, no total mensual"}
    print("Cobertura:", station, len(monthly), "/", len(expected), "meses; ausentes:", report["ausentes_por_variable"], flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inicio", type=int, default=2015)
    parser.add_argument("--fin", type=int, default=2025)
    parser.add_argument("--estaciones", nargs="+", default=["B278", "B228"])
    parser.add_argument("--salida", type=Path, default=Path(__file__).resolve().parents[1] / "Datasets" / "Meteorologia" / "AEMET")
    args = parser.parse_args()
    key = os.environ.get("AEMET_API_KEY", "").strip()
    if not key:
        parser.error("Definir AEMET_API_KEY en el entorno; no guardar la clave en el código")
    if not 1900 <= args.inicio <= args.fin <= datetime.now().year:
        parser.error("Intervalo de años incorrecto")
    if any(not s.isalnum() for s in args.estaciones):
        parser.error("Indicativos de estación incorrectos")
    args.salida.mkdir(parents=True, exist_ok=True)
    manifest = {"fuente": "AEMET OpenData", "descarga_utc": datetime.now(timezone.utc).isoformat(),
                "inicio": args.inicio, "fin": args.fin, "estaciones": args.estaciones,
                "documentacion": "https://opendata.aemet.es/dist/", "productos": [],
                "clave_guardada": False, "tipo": "observaciones climatologicas mensuales revisadas, no pronosticos"}
    stations, entry = product("/api/valores/climatologicos/inventarioestaciones/estaciones/" + ",".join(args.estaciones), key, args.salida, "estaciones")
    manifest["productos"].append(entry)
    for station in stations:
        print("Estación:", station.get("indicativo"), station.get("nombre"), flush=True)
    manifest["calidad_mensual"] = []
    for station in args.estaciones:
        records = []
        # AEMET limita cada petición de este producto a 36 meses.
        for first in range(args.inicio, args.fin + 1, 3):
            last = min(first + 2, args.fin)
            endpoint = f"/api/valores/climatologicos/mensualesanuales/datos/anioini/{first}/aniofin/{last}/estacion/{station}"
            data, entry = product(endpoint, key, args.salida, f"mensuales_{station}_{first}_{last}")
            manifest["productos"].append(entry)
            records.extend(data)
            print("Descargado:", station, first, last, "registros:", len(data), flush=True)
        manifest["calidad_mensual"].append(prepare_monthly(records, station, args.salida, args.inicio, args.fin))
    (args.salida / "descarga.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Descarga terminada:", args.salida)


if __name__ == "__main__":
    main()
