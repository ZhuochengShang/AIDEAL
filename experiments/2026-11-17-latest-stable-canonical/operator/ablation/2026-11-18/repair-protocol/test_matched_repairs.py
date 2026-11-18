"""Offline protocol checks: no provider access or mutation of an experiment."""
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import sys
import repair_context as context
import matched_repairs as runner


class Engine:
    @staticmethod
    def write_once(path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_bytes() != content:
            raise ValueError('Immutable input changed')
        path.write_bytes(content)
    @staticmethod
    def atomic_json(path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(content))


class ProtocolTests(unittest.TestCase):
    def test_long_stdout_keeps_exact_native_hint(self):
        hint = 'ValueError: lengths differ. [AIDEAL fix:length] Match lengths.'
        selected, receipt = context.bounded_diagnostics('noise\n' * 20000,
            'trace\n' * 10000 + hint + '\n' + 'tail\n' * 10000, 'lengths differ', 8000)
        self.assertIn(hint, selected)
        self.assertLessEqual(len(selected), 8000)
        self.assertTrue(receipt['truncated'])
        self.assertTrue(receipt['exact_error_preserved'])

    def test_oversize_hint_fails_closed(self):
        with self.assertRaises(ValueError):
            context.bounded_diagnostics('', '[AIDEAL fix:x]' + 'x' * 10000, '', 8000)

    def test_resume_provider_failure_at_r1_does_not_repeat_r0(self):
        with TemporaryDirectory() as tmp:
            calls, outage = [], [True]
            def execute(api, number, root, feedback):
                calls.append(number)
                if number == 1 and outage[0]:
                    outage[0] = False
                    cat, status = 'llm-error', 'fail'
                else:
                    cat, status = ('runtime', 'fail') if number == 0 else (None, 'pass')
                return {'metrics': {api: {'status': status, 'error_category': cat}}}
            make = lambda p, a, n: (f'preceding R{n-1}', {})
            one = runner.run_chain('A', Path(tmp), Engine, execute, make)
            self.assertEqual([r['outcome'] for r in one], ['fail', 'provider_pending'])
            two = runner.run_chain('A', Path(tmp), Engine, execute, make)
            self.assertEqual(calls, [0, 1, 1])
            self.assertEqual([r['outcome'] for r in two], ['fail', 'pass'])
            runner.run_chain('A', Path(tmp), Engine, execute, make)
            self.assertEqual(calls, [0, 1, 1])

    def test_two_repair_limit_and_previous_round_only(self):
        with TemporaryDirectory() as tmp:
            seen = []
            def execute(api, number, root, feedback):
                seen.append((number, feedback))
                return {'metrics': {api: {'status': 'fail', 'error_category': 'runtime', 'n': number}}}
            def make(previous, api, number):
                self.assertEqual(previous['metrics'][api]['n'], number - 1)
                return f'R{number - 1}', {}
            rows = runner.run_chain('A', Path(tmp), Engine, execute, make)
            self.assertEqual(seen, [(0, ''), (1, 'R0'), (2, 'R1')])
            self.assertEqual(len(rows), 3)

    def test_completed_result_tampering_is_rejected(self):
        with TemporaryDirectory() as tmp:
            execute = lambda a, n, r, c: {'metrics': {a: {'status': 'pass'}}}
            runner.run_chain('A', Path(tmp), Engine, execute, None)
            (Path(tmp) / 'round_00/result.json').write_text('{}')
            with self.assertRaises(ValueError):
                runner.run_chain('A', Path(tmp), Engine, execute, None)

    def test_infra_and_incomplete_generation_do_not_enter_repair(self):
        self.assertEqual(context.terminal({'error_category': 'provider-incomplete'}), 'generation_invalid')
        for cat in ('infra', 'provider-incomplete'):
            with TemporaryDirectory() as tmp:
                calls = []
                def execute(a, n, r, c):
                    calls.append(n)
                    return {'metrics': {a: {'status': 'fail', 'error_category': cat}}}
                runner.run_chain('A', Path(tmp), Engine, execute, None)
                self.assertEqual(calls, [0])

    def test_only_bound_public_feedback_not_private_or_memory(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp)
            artifacts = {'request.json': json.dumps({'api': 'A'}), 'response.txt': 'a = f()\n',
                'stdout.txt': 'output', 'stderr.txt': 'ValueError: bad',
                'execution.json': json.dumps({'exit_code': 1}),
                'private_checker.json': 'SECRET_EXPECTED_123', 'error_log.jsonl': 'GENERIC_FIX_999'}
            for name, value in artifacts.items(): (p / name).write_text(value)
            result = {'metrics': {'A': {'attempt_evidence': [str(p)], 'error': 'bad'}}}
            text, receipt = context.feedback(result, 'A', 1, lambda x: x)
            self.assertIn('a = f()', text)
            self.assertNotIn('SECRET_EXPECTED', text)
            self.assertNotIn('GENERIC_FIX', text)
            self.assertEqual(len(receipt['bindings']), 5)
            with self.assertRaises(ValueError):
                context.feedback({'metrics': {'B': result['metrics']['A']}}, 'B', 1, lambda x: x)

    def test_context_hook_overrides_generic_memory_and_restores_loader(self):
        seen = []
        def load(cfg, name, **kw):
            seen.append(kw)
            return 'system', kw.get('api_body', '') + str(kw.get('known_failures'))
        fake = SimpleNamespace(load=load)
        package = SimpleNamespace(prompts=fake)
        with patch.dict(sys.modules, {'aideal': package, 'aideal.prompts': fake}):
            with runner.prompt_context('ONLY_PREVIOUS_PROGRAM', 'validated alias signature'):
                system, user = fake.load(None, 'aideal/comprehension_write_exec',
                    api_body='DOC', known_failures='GENERIC_GEOTIFF_MEMORY')
            self.assertIs(fake.load, load)
            self.assertIn('ONLY_PREVIOUS_PROGRAM', user)
            self.assertIn('validated alias signature', user)
            self.assertNotIn('GENERIC_GEOTIFF_MEMORY', user)
            self.assertIn(context.INSTRUCTION, user)

    def test_condition_labels_require_installed_treatments(self):
        base = {'schema': 1, 'condition': 'original', 'api_ids': ['A'],
            'runtime': {'status': 'verified', 'files': [{}], 'receipt': {}}}
        base['runtime']['receipt'] = {'path': 'proof'}
        self.assertEqual(runner.validate_spec(base), 'original')
        for condition in ('aliases', 'error_hints', 'combined', 'generated_readme'):
            candidate = deepcopy(base); candidate['condition'] = condition
            with self.assertRaises(ValueError): runner.validate_spec(candidate)
        base['runtime']['native_hints_installed'] = True
        with self.assertRaises(ValueError): runner.validate_spec(base)

    def test_binding_detects_runtime_or_document_change(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / 'source.py'; p.write_text('original')
            record = context.bind(p); context.verify(record)
            p.write_text('changed')
            with self.assertRaises(ValueError): context.verify(record)


if __name__ == '__main__': unittest.main()
