from pathlib import Path
import json
import sys
import unittest

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import Predictor, read_batch, safe_csv
from reports import report_pdf


class ModelContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.predictor = Predictor(ROOT)

    def test_complete_test_predictions_match_thesis(self):
        predictor = self.predictor
        for scenario, filename, prefix, prediction_col in [('contextual', 'predicciones_test_completas.csv', 'p_', 'predicted_class')]:
            saved = pd.read_csv(ROOT / 'artifacts' / filename)
            self.assertEqual(saved.record_id.tolist(), predictor.test.record_id.tolist())
            probabilities = predictor.probability(predictor.test, scenario)
            np.testing.assert_allclose(probabilities, saved[[prefix + label for label in predictor.labels]], atol=1e-9)
            model = predictor.bundles[scenario]['model']
            predicted = model.predict(predictor.frame(predictor.test, scenario))
            self.assertEqual([predictor.labels[int(k)] for k in predicted], saved[prediction_col].tolist())

    def test_all_twelve_case_inputs_reproduce_outputs(self):
        cases = pd.read_csv(ROOT / 'artifacts/casos_8_aciertos_4_errores.csv')
        for _, row in cases.iterrows():
            result = self.predictor.predict(row.to_dict())
            self.assertEqual(result.label, row.predicted_class)
            np.testing.assert_allclose(result.probabilities, [row['p_' + label] for label in self.predictor.labels], atol=1e-9)

    def test_unknown_categories_are_detected(self):
        result = self.predictor.predict({'Vendor': ' Empresa nueva ', 'Platform': 'plataforma nueva',
                                         'Product_normalized': 'producto nuevo', 'risk_family_6': self.predictor.families[0]})
        self.assertEqual(set(result.unknown), {'Vendor', 'Platform', 'Product_normalized'})
        self.assertEqual(result.profile_count, 0)
        self.assertAlmostEqual(sum(result.probabilities), 1, places=6)

    def test_batch_preserves_valid_rows_and_identifies_invalid_rows(self):
        rows = pd.read_csv(ROOT / 'ejemplo_lote.csv').head(2).copy()
        bad = rows.iloc[0].copy()
        bad['risk_family_6'] = 'familia inventada'
        frame = pd.concat([rows, pd.DataFrame([bad])], ignore_index=True)
        results, errors = self.predictor.batch(frame)
        self.assertEqual(len(results), 2)
        self.assertEqual(errors.fila_csv.tolist(), [4])
        for i, row in rows.iterrows():
            self.assertEqual(results.iloc[i].severidad_estimada, self.predictor.predict(row.to_dict()).label)

    def test_batch_rejects_missing_columns_and_empty_files(self):
        with self.assertRaises(ValueError):
            self.predictor.batch(pd.DataFrame([{'Vendor': 'vendor'}]))
        with self.assertRaises(ValueError):
            read_batch(b'')
        with self.assertRaises(ValueError):
            read_batch(b'x' * (5 * 1024 * 1024 + 1))

    def test_csv_formula_export_is_safe(self):
        content = safe_csv(pd.DataFrame({'case_id': ['=1+1', '@SUM(1)', 'normal']})).decode('utf-8-sig')
        self.assertIn("'=1+1", content)
        self.assertIn("'@SUM(1)", content)

    def test_lime_explains_the_same_model_output(self):
        row = pd.read_csv(ROOT / 'artifacts/casos_8_aciertos_4_errores.csv').iloc[0]
        result = self.predictor.predict(row.to_dict())
        explanation = self.predictor.explain(result, background=row.Source, samples=1000)
        self.assertAlmostEqual(explanation['model_probability'], result.probabilities[self.predictor.labels.index(result.label)])
        self.assertEqual(len(explanation['weights']), 4)
        self.assertTrue(np.isfinite(explanation['r2']))
        unknown = self.predictor.predict({'Vendor': 'nuevo', 'Platform': 'nuevo', 'Product_normalized': 'nuevo',
                                         'risk_family_6': self.predictor.families[0]})
        explained = self.predictor.explain(unknown, samples=1000)
        self.assertEqual(explained['explained_class'], unknown.label)

    def test_three_classes_and_mapping_match_all_rows(self):
        predictor = self.predictor
        self.assertEqual(predictor.labels, ['low', 'medium', 'high'])
        mapped = predictor.dataset.Severity_original.map(predictor.metadata['severity_mapping'])
        self.assertEqual(mapped.tolist(), predictor.dataset.Severity_clean.tolist())
        self.assertEqual(list(predictor.bundles), ['contextual'])

    def test_lime_can_explain_reference_class_on_failure(self):
        cases = pd.read_csv(ROOT / 'artifacts/casos_8_aciertos_4_errores.csv')
        row = cases[~cases.correct].iloc[0]
        prediction = self.predictor.predict(row.to_dict())
        explanation = self.predictor.explain(prediction, background=row.Source, class_label=row.true_class, samples=1000)
        self.assertEqual(explanation['explained_class'], row.true_class)
        self.assertAlmostEqual(explanation['model_probability'], prediction.probabilities[self.predictor.labels.index(row.true_class)])

    def test_pdf_handles_long_and_special_inputs(self):
        row = pd.read_csv(ROOT / 'ejemplo_lote.csv').iloc[0]
        result = self.predictor.predict(row.to_dict(), context={'empresa': '<Empresa & compañía>', 'activo': 'Activo extenso ' * 18})
        metrics = self.predictor.metadata['evaluation'][0]
        self.assertTrue(report_pdf(result, self.predictor.labels, metrics).startswith(b'%PDF'))
        self.assertEqual(self.predictor.labels, ['low', 'medium', 'high'])


if __name__ == '__main__':
    unittest.main()
