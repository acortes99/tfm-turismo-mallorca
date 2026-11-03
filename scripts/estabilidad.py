"""Diagnóstico posterior de las predicciones guardadas, sin ajustar modelos."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs' / 'estabilidad'
OUT.mkdir(parents=True, exist_ok=True)
source = ROOT / 'outputs/prueba_final_2025/predicciones_puntuadas.csv'
digest = hashlib.sha256(source.read_bytes()).hexdigest()
predictions = pd.read_csv(source)
assert len(predictions) == 960
rows = []
for (scenario, horizon), group in predictions.groupby(['escenario', 'horizonte']):
    assert group.serie_id.nunique() == 20
    assert group.mes_objetivo.nunique() == 12
    for omitted in sorted(group.mes_objetivo.unique()):
        retained = group[group.mes_objetivo != omitted]
        assert retained.groupby('serie_id').size().eq(11).all()
        metrics = retained.groupby('serie_id').agg(
            MAE=('error_absoluto', 'mean'), MSE=('error_cuadratico', 'mean'))
        metrics['RMSE'] = np.sqrt(metrics.MSE)
        for series, values in metrics.iterrows():
            rows.append(dict(escenario=scenario, horizonte=int(horizon),
                             mes_omitido=omitted, serie_id=series,
                             MAE=values.MAE, RMSE=values.RMSE,
                             puesto_MAE=int(metrics.MAE.rank(method='min')[series]),
                             puesto_RMSE=int(metrics.RMSE.rank(method='min')[series])))
result = pd.DataFrame(rows)
assert len(result) == 960
result.to_csv(OUT / 'estabilidad_omision_un_mes.csv', index=False)
controls = pd.read_csv(ROOT / 'outputs/prueba_final_2025/aportacion_fuentes_control_interno.csv')
summaries = []
for row in controls.itertuples():
    if row.escenario != 'base':
        continue
    group = result[(result.escenario == row.escenario) & (result.horizonte == row.horizonte)]
    variant = group[group.serie_id == row.serie_id].set_index('mes_omitido')
    control = group[group.serie_id == row.control_interno].set_index('mes_omitido')
    reduction = 100 * (1 - variant.RMSE / control.RMSE)
    reduction_mae = 100 * (1 - variant.MAE / control.MAE)
    summaries.append(dict(serie_id=row.serie_id, horizonte=int(row.horizonte),
                          reduccion_RMSE_min=reduction.min(),
                          reduccion_RMSE_max=reduction.max(),
                          omisiones_mejora_RMSE=int((reduction > 0).sum()),
                          omisiones_mejora_MAE=int((reduction_mae > 0).sum())))
pd.DataFrame(summaries).to_csv(OUT / 'estabilidad_fuentes_base.csv', index=False)
assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
naive = result[result.serie_id == 'naive']
report = dict(fecha_analisis_original='2026-10-19', fecha_ejecucion=datetime.now(timezone.utc).isoformat(), fuente=source.relative_to(ROOT).as_posix(), sha256=digest,
              escenarios_horizontes=4, omisiones_por_combinacion=12,
              series=20, meses_por_omision=11,
              naive_primero_MAE=int((naive.puesto_MAE == 1).sum()),
              naive_primero_RMSE=int((naive.puesto_RMSE == 1).sum()),
              modelos_reentrenados=0, fuentes_modificadas=False,
              alcance='Influencia descriptiva; no intervalos ni contrastes de significación')
(OUT / 'protocolo_estabilidad.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
