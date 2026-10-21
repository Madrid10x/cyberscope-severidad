from pathlib import Path
import sys
import unittest

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class AppFlowTests(unittest.TestCase):
    def app(self):
        app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=30).run()
        self.assertEqual(len(app.exception), 0, str(app.exception))
        return app

    def test_navigation_renders_all_four_pages(self):
        app = self.app()
        self.assertNotIn('Evidencia del modelo', app.radio(key='navigation').options)
        for page in ['Análisis individual', 'Análisis por lotes', 'Casos y explicaciones', 'Inicio']:
            app.radio(key='navigation').set_value(page).run()
            self.assertEqual(len(app.exception), 0, page + ': ' + str(app.exception))

    def test_analysis_lime_and_result_survive_rerun(self):
        app = self.app()
        app.radio(key='navigation').set_value('Análisis individual').run()
        app.button(key='analysis_submit').click().run()
        self.assertEqual(len(app.exception), 0, str(app.exception))
        self.assertEqual(len(app.radio(key='navigation').options), 4)
        self.assertFalse(any(box.label == 'Escenario' for box in app.selectbox))
        result = app.session_state['result']
        self.assertEqual(result.scenario, 'contextual')
        app.button(key='explain_button').click().run()
        self.assertEqual(len(app.exception), 0, str(app.exception))
        self.assertEqual(app.session_state['lime_result']['prediction_id'], result.id)
        app.run()
        self.assertEqual(app.session_state['result'].id, result.id)
        self.assertEqual(len(app.exception), 0, str(app.exception))

    def test_new_category_text_input_and_batch_example(self):
        app = self.app()
        app.radio(key='navigation').set_value('Análisis individual').run()
        app.selectbox(key='input_Vendor').set_value('Otro valor').run()
        app.text_input(key='custom_Vendor').set_value('fabricante empresa nuevo').run()
        app.button(key='analysis_submit').click().run()
        self.assertEqual(len(app.exception), 0, str(app.exception))
        self.assertIn('Vendor', app.session_state['result'].unknown)
        app.radio(key='navigation').set_value('Análisis por lotes').run()
        button = next(b for b in app.button if b.label == 'Procesar ejemplo incluido')
        button.click().run()
        self.assertEqual(len(app.exception), 0, str(app.exception))
        self.assertEqual(len(app.session_state['batch_result']), 12)
        self.assertEqual(len(app.session_state['batch_errors']), 0)

    def test_all_case_graphs_and_both_lime_classes_render(self):
        app = self.app()
        app.radio(key='navigation').set_value('Casos y explicaciones').run()
        for case_id in ['A01','A02','A03','A04','A05','A06','A07','A08','E01','E02','E03','E04']:
            app.selectbox(key='selected_case').set_value(case_id).run()
            self.assertEqual(len(app.exception), 0, case_id + str(app.exception))
            if case_id.startswith('E'):
                selector = app.selectbox(key='case_lime_class')
                self.assertEqual(len(selector.options), 2)
                import pandas as pd
                row = pd.read_csv(ROOT / 'artifacts/casos_8_aciertos_4_errores.csv').set_index('case_id').loc[case_id]
                selector.set_value(row.true_class).run()
                self.assertEqual(len(app.exception), 0, case_id + str(app.exception))

    def test_case_filter_exposes_all_four_failures(self):
        app = self.app()
        app.radio(key='navigation').set_value('Casos y explicaciones').run()
        app.radio(key='case_filter').set_value('Errores').run()
        self.assertEqual(len(app.exception), 0, str(app.exception))
        self.assertEqual(len(app.selectbox(key='selected_case').options), 4)


if __name__ == '__main__':
    unittest.main()
