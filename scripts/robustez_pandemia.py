"""Sensibilidad posterior al tratamiento de la pandemia, sin volver a puntuar 2025.

Ejecutar desde la raíz: python scripts/robustez_pandemia.py
Requiere las salidas previas del notebook. No altera el maestro ni el experimento final.
"""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import warnings
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from statsmodels.tsa.statespace.sarimax import SARIMAX

ROOT = Path.cwd()
OUT = ROOT / 'outputs' / 'robustez_pandemia'
SERIES = ['naive', 'sarima', 'sarimax_aena', 'rf_ajustado', 'rf_hoteles', 'xgb_ajustado', 'xgb_hoteles']
POLICIES = ['conservar', 'omitir_ceros', 'omitir_ventana']
ZERO_DATES = pd.DatetimeIndex(['2020-04-01', '2020-05-01'])
WINDOW_START, WINDOW_END = pd.Timestamp('2020-03-01'), pd.Timestamp('2021-12-01')
EVAL_START, EVAL_END = pd.Timestamp('2022-01-01'), pd.Timestamp('2024-12-01')

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path, dates=None, index=None):
    return pd.read_csv(ROOT / path, parse_dates=dates, index_col=index, float_precision='round_trip')
def omitted(index, policy):
    index = pd.DatetimeIndex(index)
    if policy == 'omitir_ceros': return index.isin(ZERO_DATES)
    if policy == 'omitir_ventana': return (index >= WINDOW_START) & (index <= WINDOW_END)
    return np.zeros(len(index), dtype=bool)

def run():
    OUT.mkdir(parents=True, exist_ok=True)
    protected = {str(p.relative_to(ROOT)): sha(p) for p in (ROOT / 'outputs').rglob('*')
                 if p.is_file() and OUT not in p.parents}
    protocol = dict(fecha_definicion=datetime.now(timezone.utc).isoformat(),
        naturaleza='Sensibilidad descriptiva posterior a la prueba; no validación independiente ni nueva selección.',
        evaluacion=[str(EVAL_START.date()), str(EVAL_END.date())], meses_por_comparacion=36,
        horizontes=[1, 3], escenarios=['base', 'espera_adicional'], series=SERIES,
        tratamientos=POLICIES, ceros_omitidos=[str(d.date()) for d in ZERO_DATES],
        ventana_omitida=[str(WINDOW_START.date()), str(WINDOW_END.date())],
        justificacion_ventana='Ventana fija de sensibilidad que abarca la ruptura de 2020 y 2021; no es una cronología oficial de restricciones.',
        seleccion='Parámetros ya fijados con selección anterior a 2025; no se buscan nuevos hiperparámetros.',
        tratamiento_ml='Se excluyen únicamente filas por la fecha de su etiqueta; retardos y entradas observadas se conservan.',
        tratamiento_secuencial='Se enmascara únicamente el objetivo del ajuste con NaN; se conserva el calendario mensual y el filtro trata observaciones ausentes.',
        hoteles='Medianas y marcas de ausencia ajustadas solo con las filas retenidas de cada entrenamiento.',
        sarimax='Escalado ajustado solo con objetivos observados retenidos; AENA sigue disponible con los retardos originales.',
        naive='No estima parámetros: se mantiene el mismo pronóstico en los tres tratamientos.',
        control='Conservar reutiliza pronósticos guardados y se reproduce el primer mes de cada serie, horizonte y escenario.',
        limites=['Comparación posterior sobre meses ya usados para selección y diagnóstico.',
                'Omitir etiquetas reduce el tamaño de entrenamiento y mantiene información de la pandemia en los predictores.',
                'No evalúa anticipación de la pandemia ni demuestra causalidad.',
                'No modifica el maestro, las configuraciones definitivas ni los resultados de 2025.'])
    (OUT / 'protocolo.json').write_text(json.dumps(protocol, ensure_ascii=False, indent=2), encoding='utf-8')
    master = read('outputs/etl/dataset_maestro_mallorca.csv', ['fecha'], 'fecha').loc[:EVAL_END].copy()
    assert master.index.equals(pd.date_range('2015-10-01', EVAL_END, freq='MS'))
    assert master.index[master.turistas.eq(0)].equals(ZERO_DATES)
    plan = read('outputs/evaluacion/plan_pronosticos.csv', ['mes_origen', 'mes_objetivo', 'fecha_corte', 'ultimo_y_para_estimacion'])
    plan = plan.loc[plan.mes_objetivo.between(EVAL_START, EVAL_END)].copy()
    assert len(plan) == 144 and plan.mes_objetivo.dt.year.lt(2025).all()
    indices = read('outputs/evaluacion/indices_entrenamiento.csv', ['mes_origen_pronostico', 'mes_origen_entrenamiento'])
    catalog = read('outputs/predictores/catalogo_predictores.csv')
    fixed = json.loads((ROOT / 'outputs/configuraciones_finales/configuraciones_fijadas.json').read_text(encoding='utf-8'))
    configs = {(r['serie_id'], r['horizonte']): r for r in fixed['configuraciones']}
    joint = read('outputs/comparacion_modelos/predicciones_conjuntas.csv', ['mes_origen', 'mes_objetivo'])
    joint = joint.loc[joint.mes_objetivo.between(EVAL_START, EVAL_END) & joint.serie_id.isin(SERIES)].copy()
    assert len(joint) == 1008
    inputs = {}
    for scenario in ['base', 'espera_adicional']:
        for horizon in [1, 3]:
            X = read(f'outputs/predictores/X_{scenario}_h{horizon}.csv', ['mes_origen'], 'mes_origen')
            meta = read(f'outputs/predictores/etiquetas_{scenario}_h{horizon}.csv',
                        ['mes_origen', 'mes_objetivo', 'fecha_publicacion_objetivo'], 'mes_origen')
            # No se utilizan filas ni etiquetas de 2025 en este experimento.
            inputs[(scenario, horizon)] = (X.loc[X.index < pd.Timestamp('2025-01-01')],
                                           meta.loc[meta.index < pd.Timestamp('2025-01-01')])
    rows, audits, reproductions, attempts = [], [], [], []

    def forecast(row, sid, policy):
        scenario, h, origin = row.escenario, row.horizonte, row.mes_origen
        params = configs[(sid, h)]['parametros']
        audit = dict(serie_id=sid, escenario=scenario, horizonte=h, mes_origen=origin,
                     mes_objetivo=row.mes_objetivo, tratamiento=policy, fecha_corte=row.fecha_corte)
        if sid.startswith(('rf_', 'xgb_')):
            X, meta = inputs[(scenario, h)]
            idx = indices.loc[indices.escenario.eq(scenario) & indices.horizonte.eq(h) &
                              indices.mes_origen_pronostico.eq(origin), 'mes_origen_entrenamiento']
            all_origins = pd.DatetimeIndex(idx)
            all_labels = meta.loc[all_origins]
            assert all_labels.fecha_publicacion_objetivo.le(row.fecha_corte).all()
            assert all_labels.mes_objetivo.lt(row.mes_objetivo).all()
            mask = omitted(all_labels.mes_objetivo, policy)
            kept = all_origins[~mask]
            assert len(kept) >= 24
            groups = ['turistas', 'calendario'] + (['hoteles'] if sid.endswith('hoteles') else [])
            cat = catalog.loc[catalog.horizonte.eq(h) & catalog.espera_adicional.eq(int(scenario == 'espera_adicional'))]
            # El orden forma parte de la reproducibilidad del muestreo del bosque.
            cols = cat.loc[cat.grupo.isin(['turistas', 'calendario']), 'predictor'].tolist()
            if sid.endswith('hoteles'):
                cols += cat.loc[cat.grupo.eq('hoteles'), 'predictor'].tolist()
            hotels = cat.loc[cat.grupo.eq('hoteles') & cat.predictor.isin(cols), 'predictor'].tolist()
            train, query = X.loc[kept, cols].copy(), X.loc[[origin], cols].copy()
            medians = train[hotels].median()
            assert medians.notna().all()
            for c in hotels:
                for frame in [train, query]:
                    frame[c + '__ausente'] = frame[c].isna().astype('int8')
                    frame[c] = frame[c].fillna(medians[c])
            y = meta.loc[kept, 'turistas_objetivo'].astype(float)
            assert np.isfinite(train.to_numpy()).all() and np.isfinite(query.to_numpy()).all()
            assert y.notna().all() and y.ge(0).all()
            model = (RandomForestRegressor(**params) if sid.startswith('rf_') else XGBRegressor(**params)).fit(train, y)
            raw = float(model.predict(query)[0])
            audit.update(n_original=len(all_origins), n_retenidas=len(kept), n_omitidas=int(mask.sum()),
                         ceros_retenidos=int(y.eq(0).sum()), ultimo_objetivo_ajuste=meta.loc[kept, 'mes_objetivo'].max(),
                         ultima_publicacion_ajuste=meta.loc[kept, 'fecha_publicacion_objetivo'].max(),
                         medianas=json.dumps(medians.to_dict()), predictores=json.dumps(train.columns.tolist()),
                         parametros=json.dumps(params, sort_keys=True))
        else:
            end = row.ultimo_y_para_estimacion
            assert end < row.mes_objetivo and end < pd.Timestamp('2025-01-01')
            history = master.loc[:end, 'turistas'].astype(float).asfreq('MS') / 1_000_000.
            exog, future = None, None
            if sid == 'sarimax_aena':
                lag = h + 1 + int(scenario == 'espera_adicional')
                start = master.index.min() + pd.DateOffset(months=lag)
                idx = pd.date_range(start, row.mes_objetivo, freq='MS')
                refs = idx - pd.DateOffset(months=lag)
                assert (refs + pd.offsets.MonthEnd(1) + pd.offsets.MonthEnd(1 + int(scenario == 'espera_adicional')) <=
                        (idx - pd.DateOffset(months=h)).to_period('M').end_time.normalize()).all()
                raw_x = pd.DataFrame({'pasajeros_aena': master.pasajeros_aena.reindex(refs).to_numpy()}, index=idx)
                history = history.reindex(idx[idx <= end]).asfreq('MS')
            mask = omitted(history.index, policy)
            history = history.mask(mask)
            assert history.notna().sum() >= 36
            if sid == 'sarimax_aena':
                known = history.index[history.notna()]
                means, stds = raw_x.loc[known].mean(), raw_x.loc[known].std(ddof=0)
                assert stds.gt(1e-12).all()
                scaled = (raw_x - means) / stds
                exog = scaled.loc[history.index]
                future = scaled.loc[scaled.index > end]
                audit.update(medias=json.dumps(means.to_dict()), desviaciones=json.dumps(stds.to_dict()))
            fitted = None
            for method in params['metodos_en_orden']:
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter('always')
                    try:
                        attempt = SARIMAX(history, exog=exog, order=tuple(params['order']),
                            seasonal_order=tuple(params['seasonal_order']), trend=params['trend'],
                            enforce_stationarity=params['enforce_stationarity'],
                            enforce_invertibility=params['enforce_invertibility']).fit(method=method, maxiter=params['maxiter'], disp=False)
                        ok = bool(attempt.mle_retvals.get('converged', False)) and np.isfinite(attempt.params).all() and np.isfinite(attempt.llf)
                        attempts.append(dict(**audit, metodo=method, convergencia=bool(ok), avisos=' | '.join(str(w.message) for w in caught)))
                        if ok: fitted = attempt
                    except Exception as exc:
                        attempts.append(dict(**audit, metodo=method, convergencia=False, excepcion=str(exc)))
                if fitted is not None: break
            audit.update(n_original=len(history), n_retenidas=int(history.notna().sum()), n_omitidas=int(mask.sum()),
                         ceros_retenidos=int(history.eq(0).sum()), ultimo_objetivo_ajuste=history.index[history.notna()].max(),
                         meses_calendario=len(history), frecuencia='MS', parametros=json.dumps(params, sort_keys=True))
            if fitted is None:
                audit['estado_ejecucion'] = 'ajuste_no_convergente';audits.append(audit)
                return np.nan
            steps = row.mes_objetivo.to_period('M').ordinal - end.to_period('M').ordinal
            predicted = fitted.get_forecast(steps=steps, exog=future).predicted_mean
            assert predicted.index[-1] == row.mes_objetivo
            raw = float(predicted.iloc[-1] * 1_000_000.)
        assert np.isfinite(raw)
        audit.update(prediccion_bruta=raw, prediccion=max(0., raw), estado_ejecucion='ok')
        audits.append(audit)
        return max(0., raw)

    for scenario in ['base', 'espera_adicional']:
        for h in [1, 3]:
            block = plan.loc[plan.escenario.eq(scenario) & plan.horizonte.eq(h)].sort_values('mes_objetivo')
            for sid in SERIES:
                reference = joint.loc[joint.escenario.eq(scenario) & joint.horizonte.eq(h) & joint.serie_id.eq(sid)].set_index('mes_objetivo')
                assert reference.index.equals(pd.date_range(EVAL_START, EVAL_END, freq='MS'))
                for i, row in enumerate(block.itertuples(index=False)):
                    original = float(reference.at[row.mes_objetivo, 'prediccion'])
                    assert float(reference.at[row.mes_objetivo, 'observado']) == master.at[row.mes_objetivo, 'turistas']
                    if sid != 'naive' and i == 0:
                        reproduced = forecast(row, sid, 'conservar')
                        difference = abs(reproduced - original)
                        assert difference < 1., f'Control distinto: {sid}, {scenario}, h={h}: {difference}'
                        reproductions.append(dict(serie_id=sid, escenario=scenario, horizonte=h, mes_objetivo=row.mes_objetivo,
                                                   original=original, reproducido=reproduced, diferencia=difference))
                    for policy in POLICIES:
                        value = original if policy == 'conservar' or sid == 'naive' else forecast(row, sid, policy)
                        rows.append(dict(serie_id=sid, etiqueta=reference.at[row.mes_objetivo,'etiqueta'],
                            escenario=scenario, horizonte=h, mes_origen=row.mes_origen, mes_objetivo=row.mes_objetivo,
                            tratamiento=policy, observado=master.at[row.mes_objetivo,'turistas'], prediccion=value,
                            estado_ejecucion='ok' if np.isfinite(value) else 'ajuste_no_convergente'))
                print(f'{scenario} h={h} {sid}: 36 meses, tres tratamientos.', flush=True)
                pd.DataFrame(rows).to_csv(OUT / 'predicciones.csv', index=False)
                pd.DataFrame(audits).to_csv(OUT / 'auditoria_entrenamientos.csv', index=False)
                pd.DataFrame(attempts).to_csv(OUT / 'auditoria_convergencia.csv', index=False)
    predictions = pd.DataFrame(rows)
    assert len(predictions) == 3024 and not predictions.duplicated(['serie_id','escenario','horizonte','mes_objetivo','tratamiento']).any()
    predictions['error'] = predictions.observado - predictions.prediccion
    predictions['ano'] = predictions.mes_objetivo.dt.year
    predictions.to_csv(OUT / 'predicciones.csv', index=False)
    grouping = ['serie_id','etiqueta','escenario','horizonte','tratamiento']
    def metrics(frame, groups):
        results=[]
        for key, b in frame.groupby(groups):
            e=b.error.dropna()
            # Solo se presentan métricas comparables si se cubren todos los meses.
            complete=len(e)==len(b)
            results.append(dict(zip(groups,key), n_esperados=len(b), n_puntuados=len(e), cobertura=len(e)/len(b),
                MAE=float(e.abs().mean()) if complete else np.nan, RMSE=float(np.sqrt((e**2).mean())) if complete else np.nan,
                sesgo=float(e.mean()) if complete else np.nan))
        return pd.DataFrame(results)
    summary=metrics(predictions,grouping)
    base=summary.loc[summary.tratamiento.eq('conservar'),grouping[:-1]+['RMSE','MAE']].rename(columns={'RMSE':'RMSE_conservar','MAE':'MAE_conservar'})
    summary=summary.merge(base,on=grouping[:-1],validate='many_to_one')
    summary['cambio_RMSE_pct']=100*(summary.RMSE/summary.RMSE_conservar-1)
    summary['cambio_MAE_pct']=100*(summary.MAE/summary.MAE_conservar-1)
    summary.to_csv(OUT/'metricas_2022_2024.csv',index=False)
    metrics(predictions,grouping+['ano']).to_csv(OUT/'metricas_anuales.csv',index=False)
    pd.DataFrame(reproductions).to_csv(OUT/'auditoria_reproduccion_controles.csv',index=False)
    # Calendario puntuado idéntico, ninguna fila de prueba, y datos históricos intactos.
    assert predictions.groupby(grouping).size().eq(36).all()
    assert predictions.mes_objetivo.max()<pd.Timestamp('2025-01-01')
    changed=[p for p,digest in protected.items() if sha(ROOT/p)!=digest]
    assert not changed, changed
    for scenario in ['base','espera_adicional']:
        fig, axes=plt.subplots(1,2,figsize=(13,5),constrained_layout=True)
        for ax,h in zip(axes,[1,3]):
            part=summary.loc[summary.escenario.eq(scenario)&summary.horizonte.eq(h)]
            pivot=part.pivot(index='etiqueta',columns='tratamiento',values='RMSE').reindex(columns=POLICIES)
            pivot.plot.barh(ax=ax,color=['#777777','#e1812c','#3274a1'])
            ax.set_title(f'Horizonte {h} '+('mes' if h == 1 else 'meses'));ax.set_xlabel('RMSE en turistas · 2022–2024');ax.set_ylabel('')
            ax.get_legend().remove()
        handles, _ = axes[0].get_legend_handles_labels()
        fig.legend(handles, ['Conservar','Omitir dos ceros','Omitir ventana 2020–2021'],
                   loc='outside lower center', ncol=3, fontsize=9)
        fig.suptitle(f'Sensibilidad al objetivo usado en entrenamiento · {scenario}')
        fig.savefig(OUT/f'rmse_{scenario}.png',dpi=150);plt.close(fig)
    execution=dict(fecha_ejecucion=datetime.now(timezone.utc).isoformat(), emisiones=len(predictions), grupos=len(summary),
        controles_reproducidos=len(reproductions), archivos_previos_verificados=len(protected), archivos_previos_modificados=changed,
        fallos_ajuste=int(predictions.prediccion.isna().sum()), versiones={p:importlib.metadata.version(p) for p in ['pandas','numpy','scikit-learn','xgboost','statsmodels','matplotlib']},
        hashes_entradas=protected, hash_script=sha(Path(__file__)), protocolo_sha256=sha(OUT/'protocolo.json'))
    (OUT/'ejecucion.json').write_text(json.dumps(execution,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Finalizado: 3.024 emisiones; ningún resultado previo modificado.',flush=True)
    return summary

if __name__=='__main__':run()
