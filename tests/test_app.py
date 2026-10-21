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
        self.assertNotIn('Casos y explicaciones', app.radio(key='navigation').options)
        for page in ['Análisis individual', 'Análisis por lotes', 'Evidencia del modelo', 'Inicio']:
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




if __name__ == '__main__':
    unittest.main()
