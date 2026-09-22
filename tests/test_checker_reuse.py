"""Controls and audience solutions must retain identical checker-resume behavior.

The checker here is a tiny synthetic JSON process. No model or target library
is called, and every generated artifact lives in a temporary directory.
"""
from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from workflow.evaluation import _run_unit
from workflow.evaluation_setup import validate_bank


class CheckerReuseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='aideal-checker-reuse-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.ready = self.root / 'ready'
        self.ready.touch()
        self.calls = self.root / 'calls.txt'
        adapter = self.root / 'adapter.py'
        adapter.write_text('''import json, sys
from pathlib import Path
request=json.load(sys.stdin)
''' + f'calls=Path({str(self.calls)!r})\nready=Path({str(self.ready)!r})\n' + r'''
with calls.open('a') as output:
    output.write(request['code'] + '\n')
if not ready.exists():
    raise RuntimeError('synthetic checker unavailable')
print(json.dumps({'execution_pass':True, 'oracle_pass':request['code']=='correct',
                  'target_reached':True, 'public_feedback':'Synthetic checked outcome'}))
''')
        reference = self.root / 'reference.txt'
        negative = self.root / 'negative.txt'
        negative.write_text('wrong')
        oracle = self.root / 'oracle.json'
        oracle.write_text('{}')
        self.case = {'id': 'case', 'prompt': 'Synthetic task', 'target_apis': ['f'],
                     'reference': str(reference), 'negative_controls': [str(negative)],
                     'oracle': str(oracle)}
        self.cfg = {'adapter': {'command': [sys.executable, str(adapter)]},
                    'model': {'name': 'synthetic-no-model'},
                    'common': {'execution_timeout_s': 5, 'max_snippet_fixes': 0,
                               'temperature': 0, 'max_output_tokens': 10}}

    def call(self, mode, code, output):
        if mode == 'control':
            Path(self.case['reference']).write_text(code)
            with redirect_stdout(io.StringIO()):
                return validate_bank({'config': self.cfg, 'bank': {'cases': [self.case]}}, output)
        frozen = {'config': self.cfg, 'system_prompt': 'Synthetic only', 'study_sha256': 'synthetic'}
        with patch('workflow.evaluation._request_solution', return_value={'code': code}):
            return _run_unit(frozen, 'Original README', self.case, 'trial', 'docs', output)

    def call_count(self):
        return len(self.calls.read_text().splitlines()) if self.calls.exists() else 0

    def process_records(self, output):
        return {path: path.read_bytes() for path in output.glob('**/process.json')}

    def test_both_call_sites_reuse_checked_passes_and_failures(self):
        for mode in ('control', 'solution'):
            for code in ('correct', 'wrong'):
                with self.subTest(mode=mode, code=code):
                    output = self.root / f'{mode}-{code}'
                    first = self.call(mode, code, output)
                    calls = self.call_count()
                    evidence = self.process_records(output)
                    second = self.call(mode, code, output)
                    self.assertEqual(first, second)
                    self.assertEqual(calls, self.call_count())
                    self.assertEqual(evidence, self.process_records(output))
                    expected_prefix = 'attempt_' if mode == 'control' else 'execution_'
                    self.assertTrue(all(path.parent.name == expected_prefix + '001' for path in evidence))
                    if mode == 'control':
                        self.assertEqual(code == 'correct', first['validated'])
                    else:
                        self.assertEqual('pass' if code == 'correct' else 'fail', first['status'])

    def test_both_call_sites_retry_infrastructure_without_erasing_attempts(self):
        for mode in ('control', 'solution'):
            with self.subTest(mode=mode):
                output = self.root / f'{mode}-outage'
                self.ready.unlink()
                first = self.call(mode, 'correct', output)
                failed = self.process_records(output)
                self.assertEqual(1, len(failed))
                self.assertEqual(False if mode == 'control' else 'unverified',
                                 first['validated'] if mode == 'control' else first['status'])
                self.ready.touch()
                recovered = self.call(mode, 'correct', output)
                self.assertEqual(True if mode == 'control' else 'pass',
                                 recovered['validated'] if mode == 'control' else recovered['status'])
                for path, content in failed.items():
                    self.assertEqual(content, path.read_bytes())
                    prefix = 'attempt_' if mode == 'control' else 'execution_'
                    self.assertTrue((path.parent.parent / (prefix + '002') / 'process.json').is_file())
                calls = self.call_count()
                self.call(mode, 'correct', output)
                self.assertEqual(calls, self.call_count())

    def test_both_call_sites_reject_changed_cached_checker_requests(self):
        for mode in ('control', 'solution'):
            with self.subTest(mode=mode):
                output = self.root / f'{mode}-mismatch'
                self.call(mode, 'correct', output)
                calls = self.call_count()
                evidence = self.process_records(output)
                with self.assertRaisesRegex(ValueError, 'Cached process request changed'):
                    self.call(mode, 'wrong', output)
                self.assertEqual(calls, self.call_count())
                self.assertEqual(evidence, self.process_records(output))


if __name__ == '__main__':
    unittest.main()
