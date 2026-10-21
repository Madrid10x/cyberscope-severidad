from pathlib import Path
from html import escape
import json
import hashlib

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import Predictor, Prediction, MISSING, PENDING, CLASS_NAMES, FAMILY_NAMES, FEATURE_NAMES, RECOMMENDATIONS, visible_value, safe_csv, read_batch
from reports import report_pdf

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title='CyberScope | Severidad cibernética', page_icon='🛡️', layout='wide')
st.markdown('<style>' + (ROOT / 'assets' / 'styles.css').read_text(encoding='utf-8') + '</style>', unsafe_allow_html=True)


@st.cache_resource
def load_predictor(release_digest):
    return Predictor(ROOT)


@st.cache_data
def evidence(name, release='4.2.0'):
    return pd.read_csv(ROOT / 'artifacts' / name)


try:
    predictor = load_predictor(hashlib.sha256((ROOT / 'artifacts/manifest.json').read_bytes()).hexdigest())
except (OSError, ValueError, KeyError, ImportError) as error:
    st.error('No se pudo cargar el modelo de CyberScope. Extrae el ZIP completo y conserva la carpeta artifacts/.')
    st.code(str(error))
    st.stop()

meta = predictor.metadata
if st.session_state.get('model_release') != meta['version']:
    st.session_state.clear()
    st.session_state['model_release'] = meta['version']
NAVIGATION = ['Inicio', 'Análisis individual', 'Análisis por lotes', 'Evidencia del modelo']
PALETTE = ['#62a69a', '#dfaa42', '#cb6267']


def goto(page):
    st.session_state['navigation'] = page


def page_title(eyebrow, title, subtitle):
    st.markdown(f'<div class="page-top"><div><div class="eyebrow">{escape(eyebrow)}</div><h1>{escape(title)}</h1><p>{escape(subtitle)}</p></div><span class="version-pill">V4.2 · Análisis asistido</span></div>', unsafe_allow_html=True)


def feature(number, title, description):
    st.markdown(f'<div class="feature-card"><div class="step">{escape(number)}</div><h3>{escape(title)}</h3><p>{escape(description)}</p></div>', unsafe_allow_html=True)


def chart_layout(fig, height=350):
    fig.update_layout(height=height, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      font=dict(family='Arial, sans-serif', color='#142c42', size=12),
                      margin=dict(l=12, r=12, t=25, b=20), legend=dict(orientation='h', y=-.2))
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor='#e2eaf0')
    return fig


def probabilities_chart(values):
    names = [CLASS_NAMES[label] for label in predictor.labels]
    fig = go.Figure(go.Bar(x=values, y=names, orientation='h', marker_color=PALETTE,
                           text=[f'{value:.1%}' for value in values], textposition='auto',
                           hovertemplate='%{y}: %{x:.2%}<extra></extra>'))
    fig.update_layout(yaxis=dict(autorange='reversed'), xaxis=dict(range=[0, 1], tickformat='.0%'))
    return chart_layout(fig)


def evaluation_for(scenario='contextual'):
    return meta['evaluation'][0]


def render_explanation(explanation):
    weights = pd.DataFrame(explanation['weights']).sort_values('weight')
    fig = go.Figure(go.Bar(x=weights.weight, y=weights.condition, orientation='h',
        marker_color=['#087e82' if value >= 0 else '#cb6267' for value in weights.weight],
        hovertemplate='%{y}<br>Peso: %{x:.4f}<extra></extra>'))
    fig.update_layout(xaxis_title='Peso local LIME', yaxis=dict(automargin=True),
                      title='Clase explicada: ' + CLASS_NAMES[explanation['explained_class']])
    st.plotly_chart(chart_layout(fig, 370), width='stretch')
    a, b, c = st.columns(3)
    a.metric('R² local', f'{explanation["r2"]:.3f}')
    b.metric('Diferencia modelo y aproximación', f'{explanation["gap"]:.3f}')
    c.metric('Registros de referencia', explanation['background_rows'])
    d, e = st.columns(2)
    d.metric('Probabilidad del modelo', f'{explanation["model_probability"]:.2%}')
    e.metric('Valor de la aproximación LIME', f'{explanation["surrogate_probability"]:.3f}')
    st.dataframe(weights.rename(columns={'condition': 'Condición', 'weight': 'Peso LIME'}),
                 hide_index=True, width='stretch')


with st.sidebar:
    st.markdown('<div class="brand"><svg class="brand-mark" viewBox="0 0 42 48" aria-hidden="true"><path d="M21 2 L39 9 V23 C39 34 30 41 21 46 C12 41 3 34 3 23 V9 Z" fill="#087e82"/><path d="M12 24 L18 30 L30 17" stroke="#e9fffa" stroke-width="3" fill="none"/></svg><div><div class="brand-name">CyberScope</div><div class="brand-tag">Cyber risk intelligence</div></div></div>', unsafe_allow_html=True)
    page = st.radio('Navegación', NAVIGATION, key='navigation', label_visibility='collapsed')
    st.divider()
    st.caption('ASISTENTE DE SEVERIDAD')
    st.write('**Baja · Media · Alta**')
    st.caption('Análisis individual y por lotes')
    st.caption('v4.2.0 · Revisión asistida para equipos de seguridad')
    st.divider()
    st.image(str(ROOT / 'assets' / 'bryan_madrid.png'), width=82)
    st.write('**Bryan Madrid**')
    st.caption('Ingeniería Civil Informática\n\nUniversidad Andrés Bello')
    st.caption('Desarrollado por Bryan Madrid')


def home():
    page_title('Para equipos de seguridad', 'Convierte hallazgos en información para actuar.', 'Estima la severidad, revisa cada resultado y comparte informes con tu equipo.')
    st.markdown('<div class="hero"><div class="eyebrow">CyberScope / Decision support</div><h2>Severidad cibernética,<br>con evidencia.</h2><p>Analiza hallazgos de forma individual o por lotes, consulta su severidad estimada y documenta la revisión con resultados explicables e informes exportables.</p><div class="hero-tags"><span>Análisis individual</span><span>Procesamiento por lotes</span><span>Explicaciones LIME</span><span>Modelo trazable</span></div></div>', unsafe_allow_html=True)
    a, b = st.columns([1, 3])
    a.button('Iniciar análisis', type='primary', width='stretch', on_click=goto, args=('Análisis individual',))
    b.button('Analizar un lote', on_click=goto, args=('Análisis por lotes',))
    st.write('')
    a, b, c, d = st.columns(4)
    a.metric('Niveles de severidad', '3')
    b.metric('Variables de entrada', '4')
    c.metric('Hallazgos por lote', 'Hasta 1.000')
    d.metric('Formatos de exportación', '3')
    d.caption('PDF · CSV · JSON')
    st.caption('Estimaciones para apoyar la revisión del equipo de seguridad. Confirma exposición, impacto y controles antes de definir la prioridad operativa.')
    st.subheader('Un flujo de trabajo para el analista')
    columns = st.columns(3)
    with columns[0]: feature('01 / CAPTURAR', 'Describe el hallazgo', 'Selecciona fabricante, plataforma, producto y macrofamilia. Incluye una referencia del activo para el informe.')
    with columns[1]: feature('02 / CONTRASTAR', 'Revisa la estimación', 'Consulta la distribución por clase, las categorías nuevas y una explicación local de las variables.')
    with columns[2]: feature('03 / DOCUMENTAR', 'Comparte la evidencia', 'Exporta el reporte o procesa un lote. La prioridad operativa queda a cargo del equipo de seguridad.')
    st.markdown('<div class="rule-note">La estimación utiliza etiquetas de referencia de CISA y MITRE. Su interpretación en el negocio requiere validar la exposición y criticidad del activo.</div>', unsafe_allow_html=True)


def set_demo(case_id):
    row = evidence('casos_8_aciertos_4_errores.csv').set_index('case_id').loc[case_id]
    normalized = predictor.normalize(row.to_dict())
    for column, value in normalized.items():
        st.session_state['input_' + column] = value
    st.session_state['asset'] = str(row.Attack_or_Vuln)


def select_input(column):
    key = 'input_' + column
    options = [MISSING] + sorted(value for value in predictor.categories[column] if value != MISSING)
    current = st.session_state.get(key)
    if current and current not in options and current != 'Otro valor':
        options.insert(1, current)
    options.append('Otro valor')
    choice = st.selectbox(FEATURE_NAMES[column], options, key=key, format_func=visible_value)
    if choice == 'Otro valor':
        return st.text_input('Escribir ' + FEATURE_NAMES[column].lower(), key='custom_' + column, max_chars=500)
    return choice


def individual():
    page_title('Análisis individual', 'Del hallazgo a la evidencia.', 'Confirma las entradas y revisa la estimación antes de definir una prioridad operativa.')
    with st.expander('Cargar un caso real del test de la tesis'):
        cases = evidence('casos_8_aciertos_4_errores.csv')
        case_id = st.selectbox('Caso de demostración', cases.case_id, key='demo_case',
                               format_func=lambda value: value + ' · ' + str(cases.set_index('case_id').loc[value, 'Attack_or_Vuln'])[:90])
        st.button('Cargar en el formulario', on_click=set_demo, args=(case_id,))
        st.caption('Son registros de la evaluación temporal; se presentan como demostraciones con etiqueta conocida.')
    with st.container(border=True):
        left, right = st.columns(2)
        with left:
            vendor = select_input('Vendor')
            product = select_input('Product_normalized')
        with right:
            platform = select_input('Platform')
            family = st.selectbox('Macrofamilia', predictor.families + [PENDING], key='input_risk_family_6', format_func=visible_value)
        st.caption('Fabricante y plataforma son variables distintas. Puedes dejar un campo como No informado cuando no aplique.')
        with st.expander('Datos para el reporte'):
            organization = st.text_input('Organización', max_chars=150, key='organization')
            asset = st.text_input('Activo o referencia del hallazgo', max_chars=250, key='asset')
            st.caption('Estos campos documentan el informe y no modifican la predicción.')
        scenario = 'contextual'
        submitted = st.button('Analizar hallazgo', key='analysis_submit', type='primary', width='stretch')
    if submitted:
        try:
            result = predictor.predict({'Vendor': vendor, 'Platform': platform, 'Product_normalized': product, 'risk_family_6': family},
                                       scenario, {'empresa': organization, 'activo': asset})
            st.session_state['result'] = result
            st.session_state.pop('lime_result', None)
            history = st.session_state.get('history', [])
            st.session_state['history'] = (history + [result])[-20:]
        except ValueError as error:
            st.error(str(error))
    result = st.session_state.get('result')
    if result:
        render_result(result)
    history = st.session_state.get('history', [])
    if history:
        with st.expander(f'Historial de esta sesión · {len(history)} análisis'):
            records = pd.DataFrame([{'ID': item.id, 'Fecha': item.timestamp, 'Activo': item.context.get('activo', ''),
                                    'Escenario': item.scenario, 'Severidad': CLASS_NAMES[item.label]} for item in history])
            st.dataframe(records, hide_index=True, width='stretch')
            st.download_button('Exportar historial CSV', safe_csv(records), 'historial_cyberscope.csv', 'text/csv', on_click='ignore')
            st.button('Borrar análisis de esta sesión', on_click=clear_session)


def clear_session():
    for key in ['history', 'result', 'lime_result', 'batch_result', 'batch_errors']:
        st.session_state.pop(key, None)


def render_result(result):
    index = predictor.labels.index(result.label)
    probability = result.probabilities[index]
    st.divider()
    st.caption(f'ÚLTIMO ANÁLISIS CONFIRMADO · {result.id} · {result.timestamp}')
    st.markdown(f'<div class="result-panel"><div class="eyebrow">Severidad estimada / {escape(result.scenario)}</div><h2>{escape(CLASS_NAMES[result.label])}</h2><p>{escape(RECOMMENDATIONS[result.label])}</p></div>', unsafe_allow_html=True)
    a, b, c = st.columns(3)
    a.metric('Probabilidad estimada de la clase', f'{probability:.1%}')
    b.metric('Diferencia entre las dos primeras', f'{result.margin:.1%}')
    c.metric('Perfiles idénticos en desarrollo', result.profile_count)
    st.caption('La probabilidad y la diferencia describen la distribución del modelo; no son garantías de acierto ni niveles de servicio.')
    if result.unknown:
        st.warning('Categorías nuevas en ' + ', '.join(FEATURE_NAMES[column] for column in result.unknown) + '. El modelo no vio estos valores durante su entrenamiento.')
    if result.values['risk_family_6'] == PENDING:
        st.warning('La macrofamilia está pendiente de clasificación. Revísala con un especialista.')
    if result.profile_count == 0:
        st.info('Esta combinación exacta no aparece en desarrollo. Revisa su compatibilidad con el contexto del activo.')
    first, second = st.columns([1.15, 1])
    with first:
        st.subheader('Distribución por clase')
        st.plotly_chart(probabilities_chart(result.probabilities), width='stretch')
    with second:
        st.subheader('Entradas confirmadas')
        selected = predictor.bundles[result.scenario]['features']
        st.dataframe(pd.DataFrame([{'Variable': FEATURE_NAMES[column], 'Valor': visible_value(result.values[column])} for column in selected]), hide_index=True, width='stretch')
        st.markdown('<div class="rule-note">La prioridad y los plazos se definen con los procedimientos de la organización. Confirma criticidad, exposición y controles existentes.</div>', unsafe_allow_html=True)
    with st.expander('Explicar este resultado con LIME', expanded='lime_result' in st.session_state):
        st.caption('Selecciona el conjunto de referencia para la explicación. La fuente no se utiliza como predictor.')
        background = st.selectbox('Referencia para LIME', ['global', 'cisa', 'mitre'], key='lime_background',
                                  format_func=lambda value: {'global': 'Todos los registros de desarrollo', 'cisa': 'Registros CISA de desarrollo', 'mitre': 'Registros MITRE de desarrollo'}[value])
        explained_class = st.selectbox('Clase a explicar', predictor.labels,
            index=predictor.labels.index(result.label), format_func=lambda value: CLASS_NAMES[value], key='live_lime_class')
        if st.button('Generar explicación LIME', key='explain_button'):
            with st.spinner('Calculando la aproximación local...'):
                st.session_state['lime_result'] = predictor.explain(result, background, class_label=explained_class)
        explanation = st.session_state.get('lime_result')
        if explanation and explanation['prediction_id'] == result.id:
            st.caption('Referencia: ' + explanation['background'] + ' · Clase: ' + CLASS_NAMES[explanation['explained_class']])
            render_explanation(explanation)
    explanation = st.session_state.get('lime_result')
    if explanation and explanation['prediction_id'] != result.id:
        explanation = None
    pdf = report_pdf(result, predictor.labels, evaluation_for(result.scenario), explanation)
    left, right = st.columns(2)
    left.download_button('Descargar informe PDF', pdf, f'cyberscope_{result.id}.pdf', 'application/pdf', on_click='ignore', width='stretch')
    right.download_button('Descargar resultado JSON', json.dumps(result.as_dict(), ensure_ascii=False, indent=2),
                          f'cyberscope_{result.id}.json', 'application/json', on_click='ignore', width='stretch')


def process_batch(data, scenario):
    try:
        frame = read_batch(data)
        results, errors = predictor.batch(frame, scenario)
        st.session_state['batch_result'] = results
        st.session_state['batch_errors'] = errors
    except ValueError as error:
        st.error(str(error))


def batch_page():
    page_title('Análisis por lotes', 'Una revisión consistente a escala.', 'Procesa un CSV y exporta resultados con probabilidades y validaciones por fila.')
    a, b = st.columns(2)
    a.download_button('Descargar plantilla CSV', (ROOT / 'plantilla_lote.csv').read_bytes(), 'plantilla_lote.csv', 'text/csv', on_click='ignore', width='stretch')
    b.download_button('Descargar ejemplo con casos reales', (ROOT / 'ejemplo_lote.csv').read_bytes(), 'ejemplo_lote.csv', 'text/csv', on_click='ignore', width='stretch')
    st.caption('CSV UTF-8 con comas · hasta 1.000 filas y 5 MB · columnas: Vendor, Platform, Product_normalized, risk_family_6; case_id es opcional.')
    with st.container(border=True):
        uploaded = st.file_uploader('Seleccionar CSV', type=['csv'], key='batch_upload', max_upload_size=5)
        scenario = 'contextual'
        left, right = st.columns(2)
        if left.button('Procesar archivo', type='primary', disabled=uploaded is None, width='stretch'):
            process_batch(uploaded.getvalue(), scenario)
        if right.button('Procesar ejemplo incluido', width='stretch'):
            process_batch((ROOT / 'ejemplo_lote.csv').read_bytes(), scenario)
    st.caption('Los datos se procesan en memoria durante la sesión. No se envían a servicios externos ni se incorporan al entrenamiento.')
    result = st.session_state.get('batch_result')
    errors = st.session_state.get('batch_errors')
    if result is not None:
        if len(result):
            a, b, c = st.columns(3)
            a.metric('Filas analizadas', len(result))
            b.metric('Filas con categorías nuevas', int(result.categorias_nuevas.ne('').sum()))
            c.metric('Filas rechazadas', len(errors))
            counts = result.severidad_estimada.value_counts().reindex(predictor.labels, fill_value=0)
            fig = go.Figure(go.Bar(x=[CLASS_NAMES[label] for label in predictor.labels], y=counts.values, marker_color=PALETTE))
            fig.update_layout(yaxis_title='Hallazgos por severidad estimada')
            st.plotly_chart(chart_layout(fig, 290), width='stretch')
            st.dataframe(result, hide_index=True, width='stretch')
            st.download_button('Exportar resultados CSV', safe_csv(result), 'resultados_lote_cyberscope.csv', 'text/csv', on_click='ignore', width='stretch')
            st.caption('Los resultados corresponden al escenario ' + str(result.modelo.iloc[0]) + '. La revisión humana determina la prioridad operativa.')
        else:
            st.warning('No hubo filas válidas para analizar.')
        if errors is not None and len(errors):
            st.subheader('Filas que requieren corrección')
            st.dataframe(errors, hide_index=True, width='stretch')
            st.download_button('Exportar errores CSV', safe_csv(errors), 'errores_lote.csv', 'text/csv', on_click='ignore')


def model_evidence():
    page_title('Evidencia del modelo', 'Resultados que se pueden contrastar.',
               'Macrofamilia y contexto tecnológico · Tres severidades · Selección en desarrollo.')
    tabs = st.tabs(['Comparación de modelos', 'Evaluación final', 'Validación temporal', 'Dataset y alcance'])
    with tabs[0]:
        name = 'tabla_comparativa_modelos.csv'
        frame = evidence(name)
        winner = frame[frame.Seleccionado.eq('MEJOR MODELO')].iloc[0]
        st.success(f'Modelo seleccionado: {winner.Modelo} · F1-Macro CV: {winner["F1 Macro CV (3 clases)"]:.4f}')
        st.caption('Mejor configuración elegible por algoritmo. Selección por F1-Macro medio de tres clases en cuatro folds; desempate por error ordinal y configuración.')
        st.dataframe(frame, hide_index=True, width='stretch')
        complete = frame[frame.Estado.eq('Completo')]
        fig = go.Figure(go.Bar(x=complete.Modelo, y=complete['F1 Macro CV (3 clases)'],
            error_y=dict(type='data', array=complete['F1 Macro desviación']),
            marker_color=['#087e82' if v == 'MEJOR MODELO' else '#abc7d2' for v in complete.Seleccionado.fillna('')]))
        fig.update_layout(yaxis_title='F1-Macro medio y desviación entre folds')
        st.plotly_chart(chart_layout(fig), width='stretch')
        st.download_button('Descargar tabla comparativa', safe_csv(frame), name, 'text/csv', on_click='ignore')
        with st.expander('Ver todas las configuraciones evaluadas'):
            all_configurations = evidence('seleccion_modelos_solo_desarrollo.csv')
            st.dataframe(all_configurations, hide_index=True, width='stretch')
            st.download_button('Exportar configuraciones', safe_csv(all_configurations), 'configuraciones.csv', 'text/csv', on_click='ignore')
    with tabs[1]:
        st.dataframe(evidence('resumen_final.csv'), hide_index=True, width='stretch')
        st.caption('El modelo de la web conserva los parámetros del XGBoost evaluado y está entrenado exclusivamente con desarrollo.')
        a, b = st.columns(2)
        a.metric('Accuracy medio de validación cruzada', f'{meta["cv"]["accuracy_cv_media"]:.2%}')
        b.metric('Accuracy en test', f'{meta["evaluation"][0]["accuracy"]:.2%}')
        report = evidence('metricas_por_clase.csv')
        st.dataframe(report, hide_index=True, width='stretch')
        st.info('low: 5 casos de test y 1 acierto. high integra high y critical.')
        left, right = st.columns(2)
        with left:
            predictions = evidence('predicciones_test_completas.csv')
            confusion = pd.crosstab(predictions.true_class, predictions.predicted_class).reindex(
                index=predictor.labels, columns=predictor.labels, fill_value=0).fillna(0).astype(int)
            fig = go.Figure(go.Heatmap(z=confusion.values, x=[CLASS_NAMES[v] for v in predictor.labels],
                y=[CLASS_NAMES[v] for v in predictor.labels], text=confusion.values,
                texttemplate='%{text}', colorscale='Blues', showscale=False))
            fig.update_layout(xaxis_title='Predicción', yaxis_title='Referencia', title='Matriz de confusión')
            st.plotly_chart(chart_layout(fig), width='stretch')
        with right:
            fig = go.Figure()
            for col, label, color in [('precision', 'Precisión', '#abc7d2'), ('recall', 'Recall', '#087e82'), ('f1-score', 'F1', '#dfaa42')]:
                fig.add_bar(x=report.clase.map(CLASS_NAMES), y=report[col], name=label, marker_color=color)
            fig.update_layout(barmode='group', yaxis=dict(range=[0, 1]), title='Métricas por clase')
            st.plotly_chart(chart_layout(fig), width='stretch')
        st.subheader('Intervalos bootstrap por fecha')
        st.dataframe(evidence('intervalos_bootstrap_por_fecha.csv'), hide_index=True, width='stretch')
        with st.expander('Procedencia y calidad de los datos'):
            for name in ['metricas_test_por_fuente.csv', 'categorias_desconocidas_test.csv', 'sensibilidad_calidad_datos.csv', 'proxy_fuente.csv']:
                st.caption(name)
                st.dataframe(evidence(name), hide_index=True, width='stretch')
    with tabs[2]:
        st.caption('Cuatro ventanas temporales con purga de entidades. El test comienza el ' + meta['selection']['test_start'] + '.')
        st.dataframe(evidence('auditoria_folds_temporales.csv'), hide_index=True, width='stretch')
        folds = evidence('validacion_cruzada_modelo_seleccionado.csv')
        st.dataframe(folds, hide_index=True, width='stretch')
        fig = go.Figure()
        for key, label, color in [('accuracy', 'Accuracy', '#087e82'), ('f1_macro_3', 'F1 macro', '#dfaa42')]:
            fig.add_bar(x=folds.fold.astype(str), y=folds[key], name=label, marker_color=color)
        fig.update_layout(barmode='group', yaxis=dict(range=[0, 1]), xaxis_title='Fold temporal')
        st.plotly_chart(chart_layout(fig), width='stretch')
        st.dataframe(evidence('resumen_validacion_cruzada.csv'), hide_index=True, width='stretch')
        st.caption('Los folds evalúan períodos distintos. El primero no tiene registros low en validación; revisa el soporte por clase al comparar F1 macro.')
        with st.expander('Todas las configuraciones por fold y candidatos no elegibles'):
            for name in ['validacion_temporal_detalle.csv', 'candidatos_no_elegibles.csv']:
                st.dataframe(evidence(name), hide_index=True, width='stretch')
                st.download_button('Exportar ' + name, (ROOT / 'artifacts' / name).read_bytes(), name,
                                   'text/csv', on_click='ignore', key='download_' + name)
    with tabs[3]:
        a, b, c, d = st.columns(4)
        a.metric('Registros reconstruidos', len(predictor.dataset))
        b.metric('Columnas del dataset', len(predictor.dataset.columns))
        c.metric('Variables predictoras', len(predictor.features))
        d.metric('Test', len(predictor.test))
        st.caption('Desarrollo: 1.520 registros. Las columnas de identidad, fecha y severidad no se usan como predictores.')
        st.subheader('Agrupación de severidades')
        st.dataframe(pd.DataFrame([
            {'Etiquetas originales': 'low y low/medium', 'Severidad actual': 'low'},
            {'Etiquetas originales': 'medium y medium/high', 'Severidad actual': 'medium'},
            {'Etiquetas originales': 'high y critical', 'Severidad actual': 'high'}]), hide_index=True, width='stretch')
        st.dataframe(evidence('auditoria_recodificacion_severidad.csv'), hide_index=True, width='stretch')
        st.dataframe(predictor.dataset.head(15), hide_index=True, width='stretch')
        left, right = st.columns(2)
        with left:
            distributions = predictor.dataset.risk_family_6.fillna(PENDING).value_counts()
            fig = go.Figure(go.Bar(y=[visible_value(v) for v in distributions.index], x=distributions.values,
                                   orientation='h', marker_color='#087e82'))
            fig.update_layout(title='Registros por macrofamilia')
            st.plotly_chart(chart_layout(fig, 390), width='stretch')
        with right:
            counts = predictor.dataset.Severity_clean.value_counts().reindex(predictor.labels, fill_value=0)
            fig = go.Figure(go.Bar(x=[CLASS_NAMES[v] for v in counts.index], y=counts.values, marker_color=PALETTE))
            fig.update_layout(title='Registros por severidad')
            st.plotly_chart(chart_layout(fig, 390), width='stretch')
        with st.expander('Variables, nulos, duplicados y valores más frecuentes'):
            for name in ['eda_01_dimensiones.csv', 'eda_02_variables.csv', 'eda_03_nulos.csv', 'eda_04_duplicados.csv',
                         'eda_06_fabricantes.csv', 'eda_06_plataformas.csv', 'eda_07_productos.csv', 'eda_07_tipos_ataque.csv']:
                st.caption(name)
                st.dataframe(evidence(name), hide_index=True, width='stretch')
        st.download_button('Descargar dataset de tres severidades', (ROOT / 'artifacts/dataset_contexto_3clases.csv').read_bytes(),
                           'dataset_contexto_3clases.csv', 'text/csv', on_click='ignore')
        st.subheader('Alcance de esta versión')
        for limit in meta['limits']:
            st.write('• ' + limit)


{'Inicio': home, 'Análisis individual': individual, 'Análisis por lotes': batch_page,
 'Evidencia del modelo': model_evidence}[page]()

st.markdown('<div class="footer"><strong>CyberScope · Bryan Madrid</strong><br>Ingeniería Civil Informática · Universidad Andrés Bello<br>Modelo experimental para revisión humana. La validación local define su utilidad operativa.</div>', unsafe_allow_html=True)
