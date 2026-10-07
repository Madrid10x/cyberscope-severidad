from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from zoneinfo import ZoneInfo
import hashlib
import json
import re
import uuid

import joblib
import numpy as np
import pandas as pd
from lime.lime_tabular import LimeTabularExplainer

ROOT = Path(__file__).resolve().parent
MISSING = '__NO_INFORMADO__'
PENDING = '__PENDIENTE_FAMILIA__'
FEATURE_NAMES = {'Vendor': 'Fabricante', 'Platform': 'Plataforma',
                 'Product_normalized': 'Producto', 'risk_family_6': 'Macrofamilia'}
CLASS_NAMES = {'low': 'Baja', 'low/medium': 'Baja / media', 'medium': 'Media',
               'medium/high': 'Media / alta', 'high': 'Alta', 'critical': 'Crítica'}
FAMILY_NAMES = {
    'Code Execution & Injection': 'Ejecución de código e inyección',
    'Identity, Access & Persistence': 'Identidad, acceso y persistencia',
    'Memory & Software Safety': 'Memoria y seguridad del software',
    'Reconnaissance & Attack Operations': 'Reconocimiento y operaciones de ataque',
    'Data Collection & Exfiltration': 'Recolección y exfiltración de datos',
    'Impact & Availability': 'Impacto y disponibilidad',
    PENDING: 'Pendiente de clasificación',
}
RECOMMENDATIONS = {
    'critical': 'Solicitar revisión prioritaria al equipo de seguridad y confirmar exposición, impacto y mitigaciones del activo.',
    'high': 'Revisar con el equipo de seguridad las medidas de contención y la criticidad del activo afectado.',
    'medium/high': 'Confirmar impacto y exposición; preparar una propuesta de mitigación para revisión del analista.',
    'medium': 'Registrar el hallazgo y evaluar las medidas de mitigación en el contexto del activo.',
    'low/medium': 'Revisar exposición y controles existentes antes de definir la prioridad del hallazgo.',
    'low': 'Documentar el hallazgo, revisar controles y monitorear cambios en la exposición.',
}


def visible_value(value):
    return 'No informado' if value == MISSING else FAMILY_NAMES.get(value, str(value))


def safe_csv(frame):
    result = frame.copy()
    for column in result.select_dtypes(include=['object', 'string']).columns:
        result[column] = result[column].map(
            lambda v: "'" + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')) else v)
    return result.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')


def read_batch(content):
    if len(content) > 5 * 1024 * 1024:
        raise ValueError('El archivo supera el límite de 5 MB.')
    try:
        frame = pd.read_csv(BytesIO(content), encoding='utf-8-sig', dtype=str, keep_default_na=False)
    except (UnicodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as error:
        raise ValueError('Usa un CSV UTF-8 separado por comas y con encabezados.') from error
    if not 1 <= len(frame) <= 1000:
        raise ValueError('El lote debe contener entre 1 y 1.000 filas.')
    if len(frame.columns) > 20:
        raise ValueError('El lote admite hasta 20 columnas.')
    return frame


@dataclass
class Prediction:
    id: str
    timestamp: str
    scenario: str
    candidate: str
    values: dict
    label: str
    probabilities: list
    unknown: list
    profile_count: int
    margin: float
    normalized_entropy: float
    context: dict

    def as_dict(self):
        return dict(self.__dict__)


class Predictor:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.artifacts = self.root / 'artifacts'
        self.metadata = json.loads((self.root / 'metadata.json').read_text(encoding='utf-8'))
        manifest = json.loads((self.artifacts / 'manifest.json').read_text(encoding='utf-8'))
        for name, expected in manifest['sha256'].items():
            if hashlib.sha256((self.artifacts / name).read_bytes()).hexdigest() != expected:
                raise ValueError(f'El artefacto {name} cambió. Ejecuta export_model.py para mantener la trazabilidad.')
        self.bundles = {
            'contextual': joblib.load(self.artifacts / 'modelo_contextual_exploratorio.joblib'),
            'familia': joblib.load(self.artifacts / 'modelo_severidad_evaluado.joblib'),
        }
        self.labels = list(self.bundles['contextual']['labels'])
        self.families = list(self.bundles['contextual']['families'])
        self.features = list(self.bundles['contextual']['features'])
        if self.features != ['Vendor', 'Platform', 'Product_normalized', 'risk_family_6']:
            raise ValueError('Contrato de predictores inesperado.')
        data = pd.read_csv(self.artifacts / 'dataset_macroclases_6_v2.csv')
        data['Date_available'] = pd.to_datetime(data.Date_available)
        cutoff = pd.Timestamp(self.bundles['contextual']['selection']['test_start'])
        self.test = data[data.Date_available >= cutoff].copy()
        test_entities = set(self.test.entity_id)
        self.development = data[(data.Date_available < cutoff) & ~data.entity_id.isin(test_entities)].copy()
        self.dataset = data
        for scenario, bundle in self.bundles.items():
            if bundle['labels'] != self.labels:
                raise ValueError('Orden de clases incompatible entre escenarios.')
            if len(self.development) != bundle['selection']['n_dev'] or len(self.test) != bundle['selection']['n_test']:
                raise ValueError('El dataset no coincide con la evaluación del modelo.')
        encoder = self.bundles['contextual']['model'].named_steps['prep'].named_transformers_['cat']
        self.categories = {c: list(map(str, values)) for c, values in zip(self.features, encoder.categories_)}

    def frame(self, frame, scenario='contextual'):
        features = self.bundles[scenario]['features']
        result = frame.reindex(columns=features).copy()
        for column in features:
            result[column] = result[column].fillna(PENDING if column == 'risk_family_6' else MISSING).astype(str)
        return result

    def normalize(self, values):
        result = {}
        for column in self.features:
            value = values.get(column)
            if value is None or pd.isna(value) or not str(value).strip():
                result[column] = PENDING if column == 'risk_family_6' else MISSING
                continue
            value = re.sub(r'\s+', ' ', str(value).strip())
            if len(value) > 500:
                raise ValueError(f'{FEATURE_NAMES[column]} admite hasta 500 caracteres.')
            if any(ord(char) < 32 for char in value):
                raise ValueError(f'{FEATURE_NAMES[column]} contiene caracteres no válidos.')
            if column == 'risk_family_6':
                aliases = {f.lower(): f for f in self.families + [PENDING]}
                aliases.update({v.lower(): k for k, v in FAMILY_NAMES.items()})
                if value.lower() not in aliases:
                    raise ValueError('Macrofamilia no válida. Usa la plantilla o una de las seis categorías.')
                result[column] = aliases[value.lower()]
            else:
                result[column] = MISSING if value in {MISSING, 'No informado'} else value.lower()
        return result

    def probability(self, frame, scenario='contextual'):
        model = self.bundles[scenario]['model']
        probabilities = model.predict_proba(self.frame(frame, scenario))
        aligned = np.zeros((len(frame), len(self.labels)))
        aligned[:, np.asarray(model.classes_, dtype=int)] = probabilities
        if not np.allclose(aligned.sum(axis=1), 1, atol=1e-6):
            raise ValueError('Distribución de probabilidades inválida.')
        return aligned

    def predict(self, values, scenario='contextual', context=None):
        normalized = self.normalize(values)
        frame = pd.DataFrame([normalized])
        model = self.bundles[scenario]['model']
        pred = int(model.predict(self.frame(frame, scenario))[0])
        probabilities = self.probability(frame, scenario)[0]
        relevant = self.bundles[scenario]['features']
        unknown = [column for column in relevant if normalized[column] not in self.categories[column]]
        train = self.frame(self.development, scenario)
        count = int(train.eq(pd.Series({column: normalized[column] for column in relevant})).all(axis=1).sum())
        ordered = np.sort(probabilities)
        entropy = -float(np.sum(probabilities * np.log(np.maximum(probabilities, 1e-15)))) / np.log(len(self.labels))
        return Prediction(uuid.uuid4().hex[:12], datetime.now(ZoneInfo('America/Santiago')).isoformat(timespec='seconds'),
                          scenario, self.bundles[scenario]['selection']['candidate'], normalized, self.labels[pred],
                          probabilities.tolist(), unknown, count, float(ordered[-1] - ordered[-2]), entropy, context or {})

    def batch(self, frame, scenario='contextual'):
        frame = frame.reset_index(drop=True).copy()
        features = self.bundles[scenario]['features']
        missing = [column for column in features if column not in frame.columns]
        if missing:
            raise ValueError('Faltan columnas obligatorias: ' + ', '.join(missing))
        if not 1 <= len(frame) <= 1000:
            raise ValueError('El lote debe contener entre 1 y 1.000 filas.')
        normalized = []
        errors = []
        indices = []
        for index, row in frame.iterrows():
            try:
                normalized.append(self.normalize(row.to_dict()))
                indices.append(index)
            except ValueError as error:
                errors.append({'fila_csv': int(frame.index.get_loc(index)) + 2, 'error': str(error)})
        rows = []
        if normalized:
            inputs = pd.DataFrame(normalized)
            model = self.bundles[scenario]['model']
            predictions = model.predict(self.frame(inputs, scenario))
            probabilities = self.probability(inputs, scenario)
            for i, index in enumerate(indices):
                values = normalized[i]
                unknown = [FEATURE_NAMES[c] for c in features if values[c] not in self.categories[c]]
                row = {'fila_csv': int(frame.index.get_loc(index)) + 2,
                       'case_id': str(frame.loc[index].get('case_id', index + 1)), **values,
                       'severidad_estimada': self.labels[int(predictions[i])],
                       'probabilidad_clase': float(probabilities[i, int(predictions[i])]),
                       'categorias_nuevas': ', '.join(unknown), 'modelo': self.bundles[scenario]['selection']['candidate']}
                row.update({'p_' + label: float(probabilities[i, k]) for k, label in enumerate(self.labels)})
                rows.append(row)
        return pd.DataFrame(rows), pd.DataFrame(errors, columns=['fila_csv', 'error'])

    def explain(self, prediction, background='global', samples=3000, seed=42):
        if background not in {'global', 'cisa', 'mitre'}:
            raise ValueError('Fondo LIME no válido.')
        if not 500 <= samples <= 10000:
            raise ValueError('LIME admite entre 500 y 10.000 muestras.')
        scenario = prediction.scenario
        features = self.bundles[scenario]['features']
        background_data = self.development if background == 'global' else self.development[self.development.Source.eq(background)]
        train = self.frame(background_data, scenario)
        row = self.frame(pd.DataFrame([prediction.values]), scenario)
        voc = {column: sorted(set(train[column]) | set(row[column])) for column in features}
        encoding = {column: {value: i for i, value in enumerate(voc[column])} for column in features}

        def encode(data):
            return np.column_stack([data[column].map(encoding[column]).to_numpy() for column in features]).astype(int)

        def query(z):
            z = np.rint(np.asarray(z)).astype(int)
            decoded = pd.DataFrame({column: np.asarray(voc[column], dtype=object)[z[:, j]] for j, column in enumerate(features)})
            return self.probability(decoded, scenario)

        encoded_row = encode(row)[0]
        if not np.allclose(query([encoded_row])[0], prediction.probabilities, atol=1e-8):
            raise ValueError('LIME no reproduce la predicción del modelo.')
        explainer = LimeTabularExplainer(encode(train), mode='classification', feature_names=features,
            class_names=self.labels, categorical_features=list(range(len(features))),
            categorical_names={j: voc[column] for j, column in enumerate(features)},
            discretize_continuous=False, feature_selection='none', random_state=seed)
        label = self.labels.index(prediction.label)
        explanation = explainer.explain_instance(encoded_row, query, labels=(label,),
                                                  num_features=len(features), num_samples=samples)
        local = float(np.ravel(explanation.local_pred)[0])
        result = {'prediction_id': prediction.id, 'explained_class': prediction.label,
                  'background': background, 'background_rows': len(train), 'samples': samples, 'seed': seed,
                  'r2': float(explanation.score), 'surrogate_probability': local,
                  'model_probability': prediction.probabilities[label],
                  'gap': abs(local - prediction.probabilities[label]),
                  'weights': [{'condition': condition, 'weight': float(weight)}
                              for condition, weight in explanation.as_list(label=label)]}
        return result
