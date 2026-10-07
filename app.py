from pathlib import Path
from html import escape
import json

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import Predictor, Prediction, MISSING, PENDING, CLASS_NAMES, FAMILY_NAMES, FEATURE_NAMES, RECOMMENDATIONS, visible_value, safe_csv, read_batch
from reports import report_pdf, proposal_pdf

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title='CyberScope | Severidad cibernética', page_icon='🛡️', layout='wide')
st.markdown('<style>' + (ROOT / 'assets' / 'styles.css').read_text(encoding='utf-8') + '</style>', unsafe_allow_html=True)


@st.cache_resource
def load_predictor():
    return Predictor(ROOT)


@st.cache_data
def evidence(name):
    return pd.read_csv(ROOT / 'artifacts' / name)


try:
    predictor = load_predictor()
except (OSError, ValueError, KeyError) as error:
    st.error('No se pudieron cargar los artefactos de la tesis. Extrae el ZIP completo y conserva la carpeta artifacts/.')
    st.code(str(error))
    st.stop()

meta = predictor.metadata
NAVIGATION = ['Inicio', 'Análisis individual', 'Análisis por lotes', 'Evidencia del modelo', 'Casos y explicaciones', 'Propuesta empresarial']
PALETTE = ['#76a9bc', '#7dbab1', '#248f93', '#e6b454', '#e28850', '#cb6267']


def goto(page):
    st.session_state['navigation'] = page


def page_title(eyebrow, title, subtitle):
    st.markdown(f'<div class="page-top"><div><div class="eyebrow">{escape(eyebrow)}</div><h1>{escape(title)}</h1><p>{escape(subtitle)}</p></div><span class="version-pill">V3 · Piloto supervisado</span></div>', unsafe_allow_html=True)


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


def evaluation_for(scenario):
    key = 'Contextual' if scenario == 'contextual' else 'Familia'
    return next(row for row in meta['evaluation'] if row['escenario'] == key)


def render_explanation(explanation):
    weights = pd.DataFrame(explanation['weights'])
    fig = go.Figure(go.Bar(x=weights.weight, y=weights.condition, orientation='h',
                           marker_color=['#087e82' if value >= 0 else '#cb6267' for value in weights.weight],
                           hovertemplate='%{y}<br>Peso: %{x:.4f}<extra></extra>'))
    fig.update_layout(xaxis_title='Peso local LIME', yaxis=dict(autorange='reversed'))
    st.plotly_chart(chart_layout(fig, 300), width='stretch')
    a, b, c = st.columns(3)
    a.metric('R² de la aproximación local', f'{explanation["r2"]:.3f}')
    b.metric('Diferencia con el modelo', f'{explanation["gap"]:.3f}')
    c.metric('Registros de referencia', explanation['background_rows'])
    st.caption('Los pesos describen asociaciones locales del modelo. Un peso positivo favorece la clase explicada; uno negativo la reduce. No son causas del incidente.')
    if explanation['r2'] < .7 or explanation['gap'] > .1:
        st.warning('La aproximación local tiene fidelidad limitada. Interpreta los pesos junto con el R² y la diferencia con el modelo.')


with st.sidebar:
    st.markdown('<div class="brand"><svg class="brand-mark" viewBox="0 0 42 48" aria-hidden="true"><path d="M21 2 L39 9 V23 C39 34 30 41 21 46 C12 41 3 34 3 23 V9 Z" fill="#087e82"/><path d="M12 24 L18 30 L30 17" stroke="#e9fffa" stroke-width="3" fill="none"/></svg><div><div class="brand-name">CyberScope</div><div class="brand-tag">Cyber risk intelligence</div></div></div>', unsafe_allow_html=True)
    page = st.radio('Navegación', NAVIGATION, key='navigation', label_visibility='collapsed')
    st.divider()
    st.caption('MODELO CONTEXTUAL EVALUADO')
    st.write('**Regresión Logística**')
    st.caption('Cuatro variables · Seis clases de severidad')
    st.caption('v3.0.0 · Selección mediante validación temporal')
    st.divider()
    st.image(str(ROOT / 'assets' / 'bryan_madrid.png'), width=82)
    st.write('**Bryan Madrid**')
    st.caption('Ingeniería Civil Informática\n\nUniversidad Andrés Bello')
    st.caption('Proyecto de tesis · Propuesta de piloto empresarial')


def home():
    page_title('Análisis con evidencia', 'Una visión clara de la severidad.', 'Un flujo para revisar hallazgos, contrastar resultados y documentar decisiones.')
    st.markdown('<div class="hero"><div class="eyebrow">CyberScope / Decision support</div><h2>Severidad cibernética,<br>con evidencia.</h2><p>Explora una estimación de severidad, entiende qué variables influyen en el modelo y comparte un informe que facilite la revisión del equipo de seguridad.</p><div class="hero-tags"><span>Análisis individual</span><span>Procesamiento por lotes</span><span>Explicaciones LIME</span><span>Modelo trazable</span></div></div>', unsafe_allow_html=True)
    a, b = st.columns([1, 3])
    a.button('Iniciar análisis', type='primary', width='stretch', on_click=goto, args=('Análisis individual',))
    b.button('Ver propuesta de piloto', on_click=goto, args=('Propuesta empresarial',))
    st.write('')
    metrics = evaluation_for('contextual')
    a, b, c, d = st.columns(4)
    a.metric('Accuracy en test temporal', f'{metrics["accuracy"]:.1%}')
    b.metric('F1-Macro · seis clases', f'{metrics["f1_macro_6"]:.3f}')
    c.metric('Registros del test', meta['selection']['n_test'])
    d.metric('Registros reconstruidos', meta['dataset_rows'])
    st.caption('Resultados del modelo congelado de la tesis. La utilidad en una empresa se debe medir con sus datos y su rúbrica de severidad.')
    st.subheader('Un flujo de trabajo para el analista')
    columns = st.columns(3)
    with columns[0]: feature('01 / CAPTURAR', 'Describe el hallazgo', 'Selecciona fabricante, plataforma, producto y macrofamilia. Incluye una referencia del activo para el informe.')
    with columns[1]: feature('02 / CONTRASTAR', 'Revisa la estimación', 'Consulta la distribución por clase, las categorías nuevas y una explicación local de las variables.')
    with columns[2]: feature('03 / DOCUMENTAR', 'Comparte la evidencia', 'Exporta el reporte o procesa un lote. La prioridad operativa queda a cargo del equipo de seguridad.')
    st.markdown('<div class="rule-note">La estimación utiliza etiquetas de referencia de CISA y MITRE. Su interpretación en el negocio requiere validar la exposición y criticidad del activo.</div>', unsafe_allow_html=True)


def set_demo(case_id):
    row = evidence('contextual_8_aciertos_4_errores.csv').set_index('case_id').loc[case_id]
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
        cases = evidence('contextual_8_aciertos_4_errores.csv')
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
        scenario = st.selectbox('Escenario', ['contextual', 'familia'], key='scenario',
                                format_func=lambda value: 'Contextual · cuatro variables' if value == 'contextual' else 'Solo macrofamilia · comparación')
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
    if result.label == 'low/medium':
        st.warning('Esta clase no tuvo registros en el test temporal. Su desempeño no está validado en ese conjunto.')
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
        if st.button('Generar explicación LIME', key='explain_button'):
            with st.spinner('Calculando la aproximación local...'):
                st.session_state['lime_result'] = predictor.explain(result, background)
        explanation = st.session_state.get('lime_result')
        if explanation and explanation['prediction_id'] == result.id:
            st.caption('Referencia usada en la explicación guardada: ' + explanation['background'])
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
        scenario = st.selectbox('Escenario del lote', ['contextual', 'familia'], key='batch_scenario',
                                format_func=lambda value: 'Contextual · cuatro variables' if value == 'contextual' else 'Solo macrofamilia')
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
    page_title('Evidencia del modelo', 'Resultados que se pueden contrastar.', 'Selección en desarrollo y evaluación final con fechas y entidades separadas.')
    tabs = st.tabs(['Comparación de modelos', 'Evaluación final', 'Validación temporal', 'Dataset y alcance'])
    with tabs[0]:
        scenario = st.selectbox('Escenario comparado', ['contextual', 'familia'], key='evidence_scenario',
                                format_func=lambda value: 'Contextual' if value == 'contextual' else 'Solo macrofamilia')
        name = 'tabla_comparativa_modelos_contextual.csv' if scenario == 'contextual' else 'tabla_comparativa_modelos_familia.csv'
        frame = evidence(name)
        winner = frame[frame.Seleccionado.eq('MEJOR MODELO')].iloc[0]
        st.success(f'Modelo seleccionado: {winner.Modelo} · F1-Macro CV: {winner["F1 Macro CV (6 clases)"]:.4f}')
        st.caption('Mejor configuración elegible por algoritmo. Criterio: F1-Macro medio de seis clases en cuatro folds; desempate por menor error ordinal y luego identificador de configuración.')
        st.dataframe(frame, hide_index=True, width='stretch')
        complete = frame[frame.Estado.eq('Completo')]
        fig = go.Figure(go.Bar(x=complete.Modelo, y=complete['F1 Macro CV (6 clases)'],
                               error_y=dict(type='data', array=complete['F1 Macro desviación']),
                               marker_color=['#087e82' if v == 'MEJOR MODELO' else '#abc7d2' for v in complete.Seleccionado.fillna('')]))
        fig.update_layout(yaxis_title='F1-Macro medio ± desviación entre folds')
        st.plotly_chart(chart_layout(fig), width='stretch')
        st.download_button('Descargar tabla comparativa', safe_csv(frame), name, 'text/csv', on_click='ignore')
        with st.expander('Ver todas las configuraciones evaluadas'):
            name = 'contexto_seleccion_solo_desarrollo.csv' if scenario == 'contextual' else 'seleccion_modelos_solo_desarrollo.csv'
            all_configurations = evidence(name)
            st.dataframe(all_configurations, hide_index=True, width='stretch')
            st.download_button('Exportar configuraciones', safe_csv(all_configurations), name, 'text/csv', on_click='ignore')
    with tabs[1]:
        summary = evidence('resumen_modelos_finales_completo.csv')
        st.dataframe(summary, hide_index=True, width='stretch')
        st.caption('Resultados de los dos modelos seleccionados antes de consultar el test. El modelo utilizado en la web es exactamente el evaluado, entrenado sobre desarrollo.')
        left, right = st.columns(2)
        for column, title, name in [(left, 'Contextual', 'reporte_contextual_exploratorio.csv'), (right, 'Solo macrofamilia', 'reporte_clasificacion_test.csv')]:
            with column:
                st.subheader(title)
                st.dataframe(evidence(name), hide_index=True, width='stretch')
        st.warning('La clase low/medium no tiene soporte en el test temporal. Las métricas globales no validan su desempeño.')
        st.subheader('Intervalos bootstrap del modelo contextual')
        st.dataframe(evidence('contextual_intervalos_bootstrap.csv'), hide_index=True, width='stretch')
        with st.expander('Matrices de confusión y métricas por clase'):
            a, b = st.columns(2)
            a.image(str(ROOT / 'artifacts/figuras/restaurado_04_matriz_confusion_contextual.png'), caption='Modelo contextual', width='stretch')
            b.image(str(ROOT / 'artifacts/figuras/restaurado_03_metricas_por_clase_contextual.png'), caption='Métricas de las seis clases', width='stretch')
    with tabs[2]:
        st.markdown('**Cuatro ventanas de validación temporal con purga por entidad.** El holdout final comienza el ' + meta['selection']['test_start'] + '.')
        st.dataframe(evidence('auditoria_folds_temporales.csv'), hide_index=True, width='stretch')
        st.dataframe(evidence('validacion_cruzada_modelos_seleccionados.csv'), hide_index=True, width='stretch')
        st.image(str(ROOT / 'artifacts/figuras/cv_01_modelos_seleccionados_por_fold.png'), width='stretch')
        with st.expander('Todos los resultados por fold y los candidatos no elegibles'):
            for name in ['contexto_validacion_temporal_detalle.csv', 'validacion_temporal_detalle.csv', 'contexto_candidatos_no_elegibles.csv', 'candidatos_no_elegibles.csv']:
                st.caption(name)
                st.dataframe(evidence(name), hide_index=True, width='stretch')
                st.download_button('Exportar ' + name, (ROOT / 'artifacts' / name).read_bytes(), name, 'text/csv', on_click='ignore', key='download_' + name)
    with tabs[3]:
        a, b, c = st.columns(3)
        a.metric('Registros reconstruidos', len(predictor.dataset))
        b.metric('Desarrollo', len(predictor.development))
        c.metric('Test', len(predictor.test))
        st.caption('Las columnas de auditoría no son predictores. El modelo contextual utiliza cuatro variables.')
        st.dataframe(predictor.dataset.head(15), hide_index=True, width='stretch')
        distributions = predictor.dataset.risk_family_6.fillna(PENDING).value_counts()
        fig = go.Figure(go.Bar(y=[visible_value(value) for value in distributions.index], x=distributions.values,
                               orientation='h', marker_color='#087e82'))
        st.plotly_chart(chart_layout(fig), width='stretch')
        with st.expander('Calidad y características de los datos'):
            for name in ['eda_01_dimensiones.csv', 'eda_02_variables.csv', 'eda_03_nulos.csv', 'eda_04_duplicados.csv']:
                path = ROOT / 'artifacts' / name
                if path.is_file():
                    st.caption(name)
                    st.dataframe(evidence(name), hide_index=True, width='stretch')
        st.download_button('Descargar dataset reconstruido', (ROOT / 'artifacts/dataset_macroclases_6_v2.csv').read_bytes(), 'dataset_macroclases_6_v2.csv', 'text/csv', on_click='ignore')
        st.subheader('Alcance de esta versión')
        for limit in meta['limits']:
            st.write('• ' + limit)


def case_page():
    page_title('Casos y explicaciones', 'Aprender de aciertos y errores.', 'Doce casos reales seleccionados de forma aleatoria y reproducible para el modelo contextual.')
    cases = evidence('contextual_8_aciertos_4_errores.csv')
    a, b, c = st.columns(3)
    a.metric('Aciertos seleccionados', int(cases.contextual_correct.sum()))
    b.metric('Errores seleccionados', int((~cases.contextual_correct).sum()))
    c.metric('Clases representadas', cases.true_class.nunique())
    outcome = st.radio('Mostrar', ['Todos', 'Aciertos', 'Errores'], horizontal=True, key='case_filter')
    filtered = cases if outcome == 'Todos' else cases[cases.contextual_correct.eq(outcome == 'Aciertos')]
    st.dataframe(filtered[['case_id', 'Attack_or_Vuln', 'Source', 'true_class', 'contextual_predicted_class', 'contextual_correct', 'contextual_probability']], hide_index=True, width='stretch')
    case_id = st.selectbox('Examinar caso', filtered.case_id, key='selected_case')
    row = filtered.set_index('case_id').loc[case_id]
    st.subheader(case_id + ' · ' + str(row.Attack_or_Vuln))
    a, b = st.columns(2)
    with a:
        st.write('**Etiqueta de referencia:** ' + CLASS_NAMES[row.true_class])
        st.write('**Predicción:** ' + CLASS_NAMES[row.contextual_predicted_class])
        st.dataframe(pd.DataFrame([{'Variable': FEATURE_NAMES[column], 'Valor': visible_value(predictor.normalize(row.to_dict())[column])} for column in predictor.features]), hide_index=True, width='stretch')
    with b:
        st.plotly_chart(probabilities_chart([float(row['ctx_p_' + label]) for label in predictor.labels]), width='stretch')
    lime = evidence('lime_contexto_explicaciones.csv')
    weights = lime[lime.case_id.eq(case_id) & lime.explained_class.eq(row.contextual_predicted_class)]
    explanation = {'weights': [{'condition': r.condicion, 'weight': r.peso_lime} for _, r in weights.iterrows()],
                   'r2': weights.r2_local.iloc[0], 'gap': weights.gap_absoluto.iloc[0],
                   'background_rows': int(weights.n_background.iloc[0])}
    st.subheader('Explicación LIME guardada de la evaluación')
    st.caption('Fondo de desarrollo condicionado por fuente: ' + str(weights.fondo_condicional_fuente.iloc[0]))
    render_explanation(explanation)
    with st.expander('Estabilidad entre semillas y explicación completa'):
        stability = evidence('lime_contexto_estabilidad_resumen.csv')
        st.dataframe(stability[stability.case_id.eq(case_id)], hide_index=True, width='stretch')
        path = ROOT / 'artifacts/lime_contexto' / (case_id + '_contexto_lime.html')
        st.download_button('Descargar explicación LIME HTML', path.read_bytes(), path.name, 'text/html', on_click='ignore')
    st.subheader('Patrones sobre todo el test')
    patterns = evidence('contextual_patrones_error_test.csv')
    st.dataframe(patterns[patterns.variable.isin(['Source', 'Severity_clean', 'risk_family_6'])], hide_index=True, width='stretch')
    st.caption('Los patrones son asociaciones descriptivas del test completo. Los doce casos ilustran comportamientos y no sustituyen las métricas globales.')
    with st.expander('Comparar con los ocho aciertos y cuatro errores del modelo de familia'):
        family_cases = evidence('casos_8_aciertos_4_errores.csv')
        st.dataframe(family_cases[['case_id', 'Attack_or_Vuln', 'true_class', 'predicted_class', 'correct']], hide_index=True, width='stretch')


def proposal_page():
    page_title('Propuesta empresarial', 'Un piloto con objetivos medibles.', 'Evaluar el aporte del asistente en un flujo real de análisis, con criterios acordados antes de medir.')
    st.markdown('<div class="hero"><div class="eyebrow">Propuesta / Piloto de cuatro semanas</div><h2>Validar valor en el contexto de tu organización.</h2><p>Una muestra autorizada, una rúbrica compartida y un equipo de seguridad que contraste cada resultado. La decisión de continuidad se apoya en evidencia local.</p><div class="hero-tags"><span>Alcance acordado</span><span>Revisión humana</span><span>Métricas por clase</span><span>Resultados exportables</span></div></div>', unsafe_allow_html=True)
    st.subheader('Plan de trabajo propuesto')
    plan = pd.DataFrame([
        {'Etapa': 'Semana 1', 'Actividad': 'Acordar caso de uso, activos, responsables y rúbrica.', 'Entregable': 'Alcance y criterios de evaluación.'},
        {'Etapa': 'Semana 2', 'Actividad': 'Preparar y revisar una muestra local autorizada.', 'Entregable': 'Datos y etiquetas revisados por especialistas.'},
        {'Etapa': 'Semana 3', 'Actividad': 'Medir desempeño con un conjunto separado y revisar errores.', 'Entregable': 'Resultados por clase y subestimaciones.'},
        {'Etapa': 'Semana 4', 'Actividad': 'Comparar tiempos, concordancia y utilidad del flujo.', 'Entregable': 'Informe y decisión de continuidad.'},
    ])
    st.dataframe(plan, hide_index=True, width='stretch')
    a, b = st.columns(2)
    with a:
        feature('EVALUACIÓN', 'Qué se medirá', 'F1-Macro, recall por clase, subestimaciones graves, categorías nuevas, tiempo de revisión y utilidad para el analista.')
    with b:
        feature('COLABORACIÓN', 'Qué requiere la empresa', 'Responsable de seguridad, muestra autorizada, rúbrica de severidad y entorno restringido para ejecutar el prototipo.')
    st.subheader('Capacidades disponibles y siguientes etapas')
    scope = pd.DataFrame([
        {'Capacidad': 'Análisis individual y por lotes', 'Estado': 'Disponible en este prototipo'},
        {'Capacidad': 'Reportes y explicaciones LIME', 'Estado': 'Disponible en este prototipo'},
        {'Capacidad': 'Evidencia y código reproducible', 'Estado': 'Disponible en este prototipo'},
        {'Capacidad': 'Validación con datos propios de la empresa', 'Estado': 'Objetivo del piloto'},
        {'Capacidad': 'Acceso corporativo, auditoría y almacenamiento', 'Estado': 'Fase posterior según requisitos'},
        {'Capacidad': 'Integración con SOC, SIEM o gestión de tickets', 'Estado': 'Fase posterior según requisitos'},
    ])
    st.dataframe(scope, hide_index=True, width='stretch')
    st.download_button('Descargar propuesta empresarial PDF', (ROOT / 'Propuesta_Piloto_Empresarial.pdf').read_bytes(),
                       'Propuesta_Piloto_Empresarial.pdf', 'application/pdf', on_click='ignore', type='primary', width='stretch')
    with st.expander('Operación y datos del piloto'):
        st.write('Los archivos se procesan en memoria durante la sesión. El prototipo no incorpora cuentas, una base de datos de usuarios ni remediación automática. Para acceso compartido se debe usar un entorno restringido por la organización.')
        st.write('El despliegue incluye modelos congelados y un procedimiento de reproducción de la tesis. Las integraciones y los niveles de servicio se definirían después de la validación local.')
    st.caption('Propuesta de Bryan Madrid · Universidad Andrés Bello. El beneficio operativo aún debe medirse; no se afirma una reducción de incidentes o de tiempo ya comprobada.')


{'Inicio': home, 'Análisis individual': individual, 'Análisis por lotes': batch_page,
 'Evidencia del modelo': model_evidence, 'Casos y explicaciones': case_page,
 'Propuesta empresarial': proposal_page}[page]()

st.markdown('<div class="footer"><strong>CyberScope · Bryan Madrid</strong><br>Ingeniería Civil Informática · Universidad Andrés Bello<br>Modelo experimental para revisión humana. La validación local define su utilidad operativa.</div>', unsafe_allow_html=True)
