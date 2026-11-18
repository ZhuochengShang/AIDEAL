"""Generated snippets must not inherit the controller's provider credentials."""
import json
import os
from pathlib import Path
import shlex
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'vendor/aideal_engine/src'))
from aideal.execution import run_command


class CredentialBoundaryTest(unittest.TestCase):
    def test_real_test_process_has_runtime_settings_but_no_provider_keys(self):
        env = dict(os.environ, GOOGLE_API_KEY='synthetic-google',
                   GEMINI_API_KEY='synthetic-gemini', OPENAI_API_KEY='synthetic-openai',
                   ANTHROPIC_API_KEY='synthetic-anthropic', AIDEAL_RUNTIME_TEST='retained')
        code = ('import json,os; print(json.dumps({k:os.getenv(k) for k in '
                '["GOOGLE_API_KEY","GEMINI_API_KEY","OPENAI_API_KEY",'
                '"ANTHROPIC_API_KEY","AIDEAL_RUNTIME_TEST"]}))')
        with tempfile.TemporaryDirectory() as work:
            result = run_command(shlex.join([sys.executable, '-c', code]),
                                 cwd=work, env=env, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        child = json.loads(result.stdout)
        self.assertEqual(child.pop('AIDEAL_RUNTIME_TEST'), 'retained')
        self.assertTrue(all(value is None for value in child.values()))
        self.assertEqual(env['GOOGLE_API_KEY'], 'synthetic-google')


if __name__ == '__main__':
    unittest.main()
