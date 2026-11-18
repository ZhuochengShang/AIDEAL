"""Offline safety checks for the study operator; no provider or library runs."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

SPEC = importlib.util.spec_from_file_location('generated_operator', Path(__file__).with_name('generated_readme_r0.py'))
operator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(operator)


class GeneratedR0Tests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.names = ['python:pkg.alpha', 'python:pkg.beta']
        self.content = b'complete reviewed documentation'
        self.entries = [SimpleNamespace(name=name, body='complete entry') for name in self.names]
        self.completion = {'status': 'authored_not_execution_validated', 'selected': 2,
                           'readme_sha256': operator.sha(self.content)}

    def validate(self, **changes):
        args = dict(entries=self.entries, names=self.names, completion=self.completion,
                    content=self.content, budget=12000)
        args.update(changes)
        operator.validate_entries(**args)

    def test_complete_exact_entries_accepted(self):
        self.validate()

    def test_changed_readme_is_rejected_before_model_call(self):
        with self.assertRaisesRegex(ValueError, 'receipt'):
            self.validate(content=self.content + b'changed')

    def test_missing_target_cannot_fall_back_to_original(self):
        with self.assertRaisesRegex(ValueError, 'missing'):
            self.validate(entries=self.entries[:1])

    def test_duplicate_or_extra_target_rejected(self):
        for addition in (self.entries[0], SimpleNamespace(name='python:pkg.other', body='entry')):
            with self.subTest(name=addition.name), self.assertRaisesRegex(ValueError, 'mismatch'):
                self.validate(entries=self.entries + [addition])

    def test_oversize_entry_is_not_silently_cut(self):
        with self.assertRaisesRegex(ValueError, 'oversize'):
            self.validate(budget=5)

    def test_partial_authoring_receipt_rejected(self):
        for field, value in [('selected', 1), ('status', 'running')]:
            completion = {**self.completion, field: value}
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'receipt'):
                self.validate(completion=completion)

    def test_config_changes_only_readme_and_does_not_mutate_original(self):
        baseline = {'files': {'llm_readme': 'unused.md', 'original_readme': ['README.md']},
                    'models': {'audience': 'reviewed-model'},
                    'comprehension': {'execute': {'max_fix_rounds': 0, 'sample_data': {'data': '/fixture'}}}}
        before = deepcopy(baseline)
        generated = operator.generated_config(baseline)
        self.assertEqual(baseline, before)
        self.assertEqual(generated['files']['llm_readme'], 'docs/LLM_readme.md')
        generated['files']['llm_readme'] = 'unused.md'
        self.assertEqual(generated, baseline)

    def result(self, *, complete=True, provider_error=False):
        rows = {name: {'status': 'pass', 'error_category': None} for name in self.names}
        if provider_error:
            rows[self.names[0]] = {'status': 'fail', 'error_category': 'llm-error'}
        return {'metrics': rows, 'run': {'complete': complete, 'fingerprint_components': {
            'doc_source': 'original', 'doc_scope': 'relevant', 'max_fix_rounds': 0, 'class_context': False}},
                'score': 1.0, 'score_with_infra': 1.0}

    def test_incomplete_or_repaired_original_is_not_a_matched_baseline(self):
        for result in (self.result(complete=False), self.result(provider_error=True)):
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                operator.validate_baseline(result, self.names)
        repaired = self.result()
        repaired['run']['fingerprint_components']['max_fix_rounds'] = 2
        with self.assertRaisesRegex(ValueError, 'protocol'):
            operator.validate_baseline(repaired, self.names)

    def test_release_tamper_rejected_before_imports(self):
        release = self.root / 'frozen-release'
        release.mkdir()
        code = release / 'module.py'
        code.write_text('raise AssertionError("must not execute")\n')
        binding = self.root / 'release.json'
        binding.write_text(json.dumps({'release': release.name, 'files': {'module.py': operator.sha(code.read_bytes())}}))
        spec = {'release': str(release), 'release_binding': str(binding),
                'release_binding_sha256': operator.sha(binding.read_bytes())}
        operator.verify_release(spec)
        code.write_text('changed engine')
        with self.assertRaisesRegex(ValueError, 'Frozen release file changed'):
            operator.load_engine(spec)

    def execute(self, result):
        (self.root / 'GENERATED_LAUNCH.json').write_text('{}')
        def atomic(path, value):
            Path(path).write_text(json.dumps(value))
        engine = SimpleNamespace(assert_review_released=Mock(), reset_usage=Mock(),
                                 comprehension_check=Mock(return_value=result),
                                 atomic_json=atomic, write_report=Mock())
        status = operator.evaluate(SimpleNamespace(root=self.root), self.names,
                                   {'library': 'fixture', 'bindings': []}, engine)
        return status, engine

    def test_run_uses_generated_r0_protocol_and_writes_completion(self):
        status, engine = self.execute(self.result())
        self.assertEqual(status, 0)
        args = engine.comprehension_check.call_args.kwargs
        self.assertEqual(args['doc_source'], 'aideal')
        self.assertEqual(args['doc_scope'], 'relevant')
        self.assertIs(args['class_context'], False)
        self.assertEqual(args['max_fix_rounds'], 0)
        self.assertIs(args['resume'], True)
        self.assertIsNone(args['sample'])
        self.assertEqual(args['manifest'], str(self.root / 'inputs/api_manifest.json'))
        self.assertEqual(json.loads((self.root / 'completion.json').read_text())['status'], 'complete')

    def test_provider_interruption_preserves_result_without_completion(self):
        status, _ = self.execute(self.result(complete=False, provider_error=True))
        self.assertEqual(status, 2)
        self.assertTrue((self.root / 'result.json').exists())
        self.assertFalse((self.root / 'completion.json').exists())
        self.assertEqual(json.loads((self.root / 'status.json').read_text())['status'], 'incomplete')

    def test_document_tampering_stops_before_model_call(self):
        path = self.root / 'README.md'
        path.write_bytes(self.content)
        binding = operator.bind(path)
        path.write_bytes(b'altered')
        engine = SimpleNamespace(assert_review_released=Mock(), comprehension_check=Mock())
        with self.assertRaisesRegex(ValueError, 'Bound input changed'):
            operator.evaluate(SimpleNamespace(root=self.root), self.names,
                              {'library': 'fixture', 'bindings': [binding]}, engine)
        engine.comprehension_check.assert_not_called()


if __name__ == '__main__':
    unittest.main()
