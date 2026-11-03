import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import web_service


class WebServiceTests(unittest.TestCase):
    def test_no_report_and_invalid_state(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            self.assertEqual(web_service.read_report(path), (None, None))
            (path / 'raport_ai.txt').write_text('report', encoding='utf-8')
            (path / 'analysis_state.json').write_text('broken', encoding='utf-8')
            self.assertEqual(web_service.read_report(path), ('report', None))

    def test_credentials_only_in_child_environment(self):
        keys = {'OPENAI_API_KEY': 'dummy-openai', 'GARMIN_PERSONAL_API_KEY': 'dummy-garmin'}
        with tempfile.TemporaryDirectory() as folder, patch('web_service.subprocess.run') as run:
            run.return_value = subprocess.CompletedProcess([], 0, 'pominięto analizę OpenAI', '')
            ok, message = web_service.run_pipeline(Path(folder), keys, force=True)
            self.assertTrue(ok)
            self.assertIn('bez nowego', message)
            args, kwargs = run.call_args
            self.assertIn('--force', args[0])
            self.assertNotIn('dummy-openai', repr(args[0]))
            self.assertEqual(kwargs['env']['OPENAI_API_KEY'], 'dummy-openai')

    def test_failed_child_does_not_expose_output(self):
        keys = {'OPENAI_API_KEY': 'dummy', 'GARMIN_PERSONAL_API_KEY': 'dummy'}
        with tempfile.TemporaryDirectory() as folder, patch('web_service.subprocess.run') as run:
            run.return_value = subprocess.CompletedProcess([], 1, 'PRIVATE_MEASUREMENT', 'SECRET_KEY')
            ok, message = web_service.run_pipeline(Path(folder), keys)
            self.assertFalse(ok)
            self.assertNotIn('PRIVATE_MEASUREMENT', message)
            self.assertNotIn('SECRET_KEY', message)

    def test_lock_prevents_second_request(self):
        from filelock import FileLock
        with tempfile.TemporaryDirectory() as folder, patch('web_service.subprocess.run') as run:
            path = Path(folder)
            with FileLock(str(path / 'analysis.lock')):
                ok, _ = web_service.run_pipeline(path, {})
            self.assertFalse(ok)
            run.assert_not_called()


class BrowserTests(unittest.TestCase):
    def test_missing_password_fails_closed(self):
        from streamlit.testing.v1 import AppTest
        with patch.dict(os.environ, {'APP_PASSWORD': ''}):
            app = AppTest.from_file('app.py').run()
            self.assertFalse(app.exception)
            self.assertTrue(app.error)
            self.assertEqual(len(app.button), 0)

    def test_login_gate_and_logout_do_not_call_api(self):
        from streamlit.testing.v1 import AppTest
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {
            'APP_PASSWORD': 'test-only-password-123456789',
            'OPENAI_API_KEY': 'dummy', 'GARMIN_PERSONAL_API_KEY': 'dummy',
            'GARMIN_DATA_DIR': folder,
        }), patch('web_service.run_pipeline') as run:
            (Path(folder) / 'raport_ai.txt').write_text('PRIVATE_REPORT', encoding='utf-8')
            app = AppTest.from_file('app.py').run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.text), 0)
            app.text_input[0].set_value('wrong')
            app.button[0].click().run()
            self.assertFalse(app.exception)
            self.assertTrue(app.error)
            app.text_input[0].set_value('test-only-password-123456789')
            app.button[0].click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.text[0].value, 'PRIVATE_REPORT')
            run.assert_not_called()
            app.button[0].click().run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.text), 0)
            run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
