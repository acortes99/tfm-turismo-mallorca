"""Ejecuta el notebook en una copia nueva y contrasta los resultados guardados.

Desde la raíz, con las dependencias instaladas en un entorno virtual:
python scripts/verificar_reproduccion.py --destino ../tfm-reproduccion
La carpeta de destino no debe existir. Los resultados originales no se modifican.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import sys
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contrast_outputs(root, destination):
    """Contrasta una ejecución ya terminada; no entrena ni escribe resultados."""
    import numpy as np
    import pandas as pd
    comparisons = []
    reference_files = [
        'outputs/etl/dataset_maestro_mallorca.csv',
        'outputs/prueba_final_2025/predicciones_puntuadas.csv',
        'outputs/prueba_final_2025/metricas_2025.csv',
        'outputs/interpretacion_modelos/predicciones_explicadas.csv',
        'outputs/interpretacion_modelos/importancia_grupos.csv',
        'outputs/robustez_pandemia/metricas_2022_2024.csv',
    ]
    for name in reference_files:
        original = pd.read_csv(root / name, float_precision='round_trip')
        reproduced = pd.read_csv(destination / name, float_precision='round_trip')
        assert original.shape == reproduced.shape, (name, original.shape, reproduced.shape)
        assert list(original.columns) == list(reproduced.columns), name
        max_delta = 0.0
        for column in original:
            x, y = original[column], reproduced[column]
            if pd.api.types.is_bool_dtype(x) or pd.api.types.is_bool_dtype(y):
                assert x.equals(y), (name, column, 'Valores booleanos distintos')
            elif pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
                np.testing.assert_allclose(x, y, rtol=1e-9, atol=1e-5, equal_nan=True,
                                           err_msg=f'{name}: {column}')
                delta = (x - y).abs().max()
                if pd.notna(delta): max_delta = max(max_delta, float(delta))
            else:
                assert x.fillna('').astype(str).equals(y.fillna('').astype(str)), (name, column)
        comparisons.append(dict(archivo=name, filas=len(original),
                                            diferencia_absoluta_maxima=max_delta, coincide=True))
    original_config = json.loads((root / 'outputs/configuraciones_finales/configuraciones_fijadas.json').read_text(encoding='utf-8'))
    reproduced_config = json.loads((destination / 'outputs/configuraciones_finales/configuraciones_fijadas.json').read_text(encoding='utf-8'))
    # Incluye decisiones, huellas de entradas y código anterior a la fijación.
    assert original_config == reproduced_config, 'El registro de configuraciones difiere del original.'
    return comparisons


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destino', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    destination = args.destino.resolve()
    if destination.exists():
        parser.error('El destino ya existe. Elige una carpeta nueva para conservar las ejecuciones anteriores.')
    if root == destination or root in destination.parents:
        parser.error('El destino debe estar fuera del repositorio original.')
    import nbformat
    from nbclient import NotebookClient
    import numpy as np
    import pandas as pd

    protected = {str(p.relative_to(root)).replace('\\', '/'): sha(p)
                 for p in (root / 'outputs').rglob('*') if p.is_file()}
    source = root / 'tfm-turismo-viu.ipynb'
    source_sha = sha(source)
    destination.mkdir(parents=True)
    for name in ['Datasets', 'scripts']:
        shutil.copytree(root / name, destination / name,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copy2(source, destination / source.name)
    kernel_root = destination / '.jupyter' / 'kernels' / 'tfm-reproduccion'
    kernel_root.mkdir(parents=True)
    kernel = dict(argv=[sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
                  display_name='TFM reproducción aislada', language='python',
                  env={'PYTHONPATH': '', 'PYTHONNOUSERSITE': '1', 'MPLBACKEND': 'Agg',
                       'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1',
                       'MKL_NUM_THREADS': '1', 'NUMEXPR_NUM_THREADS': '1'})
    (kernel_root / 'kernel.json').write_text(json.dumps(kernel), encoding='utf-8')
    os.environ['JUPYTER_PATH'] = str(destination / '.jupyter')
    os.environ['JUPYTER_CONFIG_DIR'] = str(destination / '.jupyter-config')
    os.environ['JUPYTER_DATA_DIR'] = str(destination / '.jupyter-data')
    os.environ['PYTHONNOUSERSITE'] = '1'
    notebook = nbformat.read(source, as_version=4)
    for cell in notebook.cells:
        if cell.cell_type == 'code':
            cell.outputs = []
            cell.execution_count = None
    notebook.metadata.kernelspec = dict(name='tfm-reproduccion', display_name='TFM reproducción aislada', language='python')
    started = time.time()
    log_path = destination / 'progreso.jsonl'

    def progress(cell, cell_index, **kwargs):
        if cell.cell_type != 'code':
            return
        event = dict(celda=cell_index, segundos=round(time.time() - started, 1))
        with log_path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(event) + '\n')
        print(f"Celda {cell_index}: {event['segundos']} s", flush=True)

    client = NotebookClient(notebook, timeout=3600, kernel_name='tfm-reproduccion',
                            resources={'metadata': {'path': str(destination)}},
                            on_cell_start=progress)
    report = dict(fecha_comprobacion=datetime.now(timezone.utc).isoformat(), python=platform.python_version(),
                  sistema=platform.platform(), notebook_sha256=source_sha,
                  celdas_codigo=sum(c.cell_type == 'code' for c in notebook.cells),
                  kernel=sys.executable, entorno_aislado=sys.prefix != sys.base_prefix,
                  configuraciones_cambiadas=False, resultados_originales_modificados=False,
                  rtol=1e-9, atol=1e-5, comparaciones=[])
    try:
        client.execute()
        nbformat.write(notebook, destination / 'notebook_ejecutado.ipynb')
        report['comparaciones'] = contrast_outputs(root, destination)
        report['configuraciones_originales_identicas'] = True
        report['estado'] = 'completado'
    except Exception as exc:
        report['estado'] = 'fallo'
        report['error'] = f'{type(exc).__name__}: {exc}'
        nbformat.write(notebook, destination / 'notebook_ejecutado.ipynb')
        raise
    finally:
        assert sha(source) == source_sha
        assert all(sha(root / name) == value for name, value in protected.items())
        report['segundos'] = round(time.time() - started, 1)
        report['dependencias'] = {d.metadata['Name']: d.version
                                  for d in importlib.metadata.distributions() if d.metadata.get('Name')}
        (destination / 'verificacion.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'dependencias'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
