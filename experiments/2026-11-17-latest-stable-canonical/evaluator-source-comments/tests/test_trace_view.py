"""Offline evidence-viewer checks: recorded events, source snapshots and HTML safety."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('aideal_trace_view_under_test', ROOT / 'scripts/trace_view.py')
viewer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(viewer)


class TraceViewTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='aideal-trace-view-test-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.run = self.root / 'run'
        self.run.mkdir()
        self.repo = self.root / 'repo'
        (self.repo / 'scripts').mkdir(parents=True)
        (self.repo / 'docs/templates').mkdir(parents=True)
        (self.repo / 'vendor/aideal_engine/src/aideal').mkdir(parents=True)
        self.prepare_source = self.repo / 'scripts/run_original_micro.py'
        self.prepare_source.write_text(
            '"""Minimal source fixture, never executed."""\n\n'
            'def prepare(spec):\n'
            '    """Prepare isolated inputs."""\n'
            '    return spec\n')
        (self.repo / 'docs/templates/trace_view.html').write_text(
            '<!doctype html><html><body>'
            '<script id="trace-data" type="application/json">__TRACE_DATA__</script>'
            '</body></html>')
        self.write(self.run / 'launch.json', {
            'api': 'detectType', 'model': 'offline-rdpro-trace', 'mode': 'trace-mock',
            'repairs': 2})

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def attempt(self, folder='attempt_0001', round_number=0, provider='mock', user='Original prompt'):
        directory = self.run / 'execution/run_detectType' / folder
        self.write(directory / 'request.json', {
            'api': 'detectType', 'round': round_number, 'attempt_number': int(folder[-4:]),
            'provider': provider, 'model': 'gemini-test' if provider == 'google' else 'offline-rdpro-trace',
            'system': 'Exact system prompt', 'user': user})
        return directory

    @staticmethod
    def payload(html):
        found = re.search(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', html, re.S)
        if not found:
            raise AssertionError('Missing JSON evidence script')
        return json.loads(found.group(1))

    def test_request_round_is_authoritative_and_unobserved_rounds_are_absent(self):
        directory = self.attempt(folder='attempt_0004', round_number=1)
        self.write(directory / 'provider.json', {'status': 'returned', 'usage': {'calls': 0}})
        (directory / 'response.txt').write_text('val actual = RasterSchemaHelper.detectType(1)')
        (directory / 'ApiTest.scala').write_text('object Program {}')
        self.write(directory / 'execution.json', {'exit_code': 1, 'wall_s': 0.2})
        (directory / 'stdout.txt').write_text('')
        (directory / 'stderr.txt').write_text('Assertion failed')
        self.write(self.run / 'result.json', {
            'run': {'complete': False},
            'details': {'detectType': {'rounds': [{'round': 1, 'status': 'fail', 'category': 'runtime'}]}}})
        data = viewer.read_run(self.run)
        self.assertEqual(1, len(data['attempts']))
        attempt = data['attempts'][0]
        self.assertEqual('attempt_0004', attempt['id'])
        self.assertEqual(1, attempt['round'])
        self.assertEqual('fixer', attempt['role'])
        self.assertEqual('runtime', attempt['verdict']['category'])
        self.assertEqual('', attempt['stdout'])  # Empty recorded output differs from missing output.
        self.assertFalse(data['complete'])

    def test_provider_denial_does_not_invent_response_execution_or_repairs(self):
        self.write(self.run / 'launch.json', {'api': 'detectType', 'mode': 'trace-live', 'model': 'gemini-test'})
        directory = self.attempt(provider='google')
        self.write(directory / 'provider.json', {
            'status': 'error', 'error': '403 PERMISSION_DENIED',
            'usage': {'calls': 0, 'input_tokens': 0, 'output_tokens': 0}})
        self.write(self.run / 'summary.json', {
            'api': 'detectType', 'mode': 'live', 'complete': False, 'status': 'fail',
            'score_with_infra': None, 'error_category': 'llm-error'})
        self.write(self.run / 'result.json', {
            'run': {'complete': False},
            'metrics': {'detectType': {'status': 'fail', 'error_category': 'llm-error'}},
            'details': {'detectType': {'rounds': [{'round': 0, 'status': 'fail', 'category': 'llm-error'}]}}})
        data = viewer.read_run(self.run)
        self.assertEqual('provider error', data['status'])
        self.assertFalse(data['complete'])
        self.assertEqual([0], [a['round'] for a in data['attempts']])
        attempt = data['attempts'][0]
        for field in ('response', 'program', 'execution', 'stdout', 'stderr'):
            self.assertIsNone(attempt[field], field)
        self.assertEqual('403 PERMISSION_DENIED', attempt['provider_result']['error'])
        self.assertIsNone(data['summary']['score_with_infra'])
        self.assertNotIn('response.txt', [a['name'] for a in attempt['artifacts']])

    def test_exact_prompts_survive_html_embedding_without_script_injection(self):
        danger = '</script><script>alert("not executed")</script> & <tag> \u2028 \u2029'
        directory = self.attempt(user='User input\n' + danger)
        request = json.loads((directory / 'request.json').read_text())
        request['system'] = 'System input\n' + danger
        self.write(directory / 'request.json', request)
        output = viewer.build_trace_view([self.run], self.root / 'view.html', repo=self.repo)
        html = output.read_text()
        self.assertNotIn(danger, html)
        self.assertNotIn('<script>alert(', html)
        self.assertIn('\\u003c/script\\u003e', html)
        payload = self.payload(html)
        saved = payload['runs'][0]['attempts'][0]['request']
        self.assertEqual(request['system'], saved['system'])
        self.assertEqual(request['user'], saved['user'])
        self.assertFalse(output.with_suffix('.html.tmp').exists())

    def test_pre_request_snapshot_has_real_lines_and_remains_stable(self):
        source = self.prepare_source.read_text()
        function = next(n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.FunctionDef))
        viewer.snapshot_sources(self.run, self.repo)
        snapshot_path = self.run / 'trace_sources.json'
        first_snapshot = snapshot_path.read_bytes()
        record = json.loads(first_snapshot)['sources']['setup']
        self.assertEqual(function.lineno, record['start'])
        self.assertEqual('\n'.join(source.splitlines()[function.lineno - 1:function.end_lineno]), record['text'])
        self.assertEqual(hashlib.sha256(source.encode()).hexdigest(), record['sha256'])
        self.assertEqual(str(self.prepare_source), record['path'])
        self.assertEqual([], viewer.read_run(self.run)['attempts'])
        self.prepare_source.write_text('\n\n' + source.replace('return spec', 'return None'))
        viewer.snapshot_sources(self.run, self.repo)
        self.assertEqual(first_snapshot, snapshot_path.read_bytes())
        data = viewer.read_run(self.run)
        self.assertEqual(record, data['sources']['setup'])
        self.assertIn('captured before requests', data['source_note'])
        rendered = self.payload(viewer.build_trace_view([self.run], self.root / 'snapshot.html', repo=self.repo).read_text())
        self.assertEqual(record, rendered['runs'][0]['sources']['setup'])
        self.assertNotEqual(record['sha256'], rendered['sources']['setup']['sha256'])

    def test_resumed_round_verdict_belongs_to_the_matching_attempt(self):
        self.write(self.run / 'launch.json', {'api': 'detectType', 'mode': 'trace-live', 'model': 'gemini-test'})
        denied = self.attempt(provider='google')
        self.write(denied / 'provider.json', {'status': 'error', 'error': '403 PERMISSION_DENIED'})
        completed = self.attempt(folder='attempt_0004', round_number=0, provider='google')
        self.write(completed / 'provider.json', {'status': 'returned'})
        self.write(completed / 'execution.json', {'exit_code': 0, 'wall_s': 0.2})
        (completed / 'response.txt').write_text('println("__CHECK__ detectType integer")')
        self.write(self.run / 'summary.json', {
            'api': 'detectType', 'mode': 'live', 'complete': True, 'status': 'pass'})
        self.write(self.run / 'result.json', {
            'run': {'complete': True},
            'metrics': {'detectType': {'status': 'pass', 'attempt_evidence': [str(completed)]}},
            'details': {'detectType': {'rounds': [{'round': 0, 'status': 'pass'}]}}})
        data = viewer.read_run(self.run)
        self.assertEqual([0, 0], [a['round'] for a in data['attempts']])
        earlier, final = data['attempts']
        self.assertNotEqual('pass', earlier['verdict']['status'])
        self.assertEqual('llm-error', earlier['verdict']['category'])
        self.assertEqual('pass', final['verdict']['status'])
        self.assertEqual('pass', data['status'])
        self.assertTrue(data['complete'])

    def test_tiny_demo_is_scripted_before_any_request_exists(self):
        (self.run / 'launch.json').unlink()
        self.write(self.run / 'api_manifest.json', ['double'])
        data = viewer.read_run(self.run)
        self.assertEqual('scripted', data['mode'])
        self.assertEqual('mock', data['provider'])
        self.assertEqual('double', data['api'])
        self.assertEqual([], data['attempts'])
        self.assertFalse(data['complete'])

    def test_installed_template_renders_the_recorded_payload(self):
        danger = '</script><script>alert("not executed")</script>'
        self.attempt(user=danger)
        output = viewer.build_trace_view([self.run], self.root / 'installed-template.html', repo=ROOT)
        html = output.read_text()
        saved = self.payload(html)['runs'][0]['attempts'][0]['request']['user']
        self.assertEqual(danger, saved)
        self.assertNotIn('<script>alert(', html)
        self.assertNotIn('__TRACE_DATA__', html)

    def test_feedback_is_an_exact_prompt_difference_not_inferred_guidance(self):
        first = self.attempt(user='Original documentation\nWrite a test.')
        self.write(first / 'provider.json', {'status': 'returned'})
        second = self.attempt(folder='attempt_0002', round_number=1,
                              user='Original documentation\nPrior failure: expected StringType, got IntegerType\nWrite a test.')
        self.write(second / 'provider.json', {'status': 'returned'})
        data = viewer.read_run(self.run)
        self.assertEqual('', data['attempts'][0]['feedback_added'])
        self.assertEqual('Prior failure: expected StringType, got IntegerType',
                         data['attempts'][1]['feedback_added'])


if __name__ == '__main__':
    unittest.main()
