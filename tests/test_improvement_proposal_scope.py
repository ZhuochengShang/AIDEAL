"""Verify scoped author requests without invoking a provider or changing source."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from workflow import improvement_batches as batches
from workflow import improvement_suggestions as suggestions


class ProposalScopeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / 'model.yaml'
        self.preview = {'context': {'apis': [], 'development_errors': [], 'alias_destination': None}}
        self.response = {'aliases': [], 'alias_code': '', 'alias_interface': '', 'hints': [],
                         'refactors': [], 'notes': 'No justified alias.'}

    def settings(self, scope='missing'):
        model = {'name': 'test-model', 'command': [sys.executable],
                 'max_output_tokens': 8192, 'timeout_s': 300}
        if scope != 'missing':
            model['proposal_scope'] = scope
        self.config.write_text(json.dumps({'model': model}))
        return suggestions._model_settings(self.config)

    def fake_invoke(self, command, request, output, timeout):
        output = Path(output)
        output.mkdir(parents=True, exist_ok=True)
        result = {'status': 'ok', 'payload': {'code': json.dumps(self.response)}}
        (output / 'request.json').write_text(json.dumps(request))
        (output / 'process.json').write_text(json.dumps(result))
        return result

    def assert_scope(self, request, scope):
        original = suggestions.PROMPT.read_text()
        if scope == 'missing':
            self.assertEqual(original, request['system'])
        else:
            self.assertTrue(request['system'].startswith(original))
            self.assertIn('executable aliases only', request['system'])
            self.assertIn('empty lists for both "hints" and "refactors"', request['system'])
            self.assertIn('Return no alias when none is justified', request['system'])
            self.assertIn('explicit top-level def or async def', request['system'])
            self.assertIn('import renamings, assignments, or __all__ alone', request['system'])
            self.assertIn('public class matching the requested filename and package', request['system'])
            self.assertIn('explicit correctly typed receiver', request['system'])

    def test_python_import_renaming_rejected_but_forwarding_def_accepted(self):
        context = {'apis': [{'id': 'python:lib.validate', 'name': 'validate'}],
                   'development_errors': [], 'alias_destination': 'lib/aliases.py'}
        proposal = {**self.response,
                    'aliases': [{'name': 'validate_beats', 'target_function': 'python:lib.validate',
                                 'rationale': 'Makes the data domain explicit.'}],
                    'alias_interface': 'lib.aliases.validate_beats(reference, estimated)',
                    'alias_code': 'from lib import validate as validate_beats\n'}
        with self.assertRaisesRegex(ValueError, 'does not define each proposed name'):
            suggestions.validate_suggestions(proposal, context)
        proposal['alias_code'] = ('from lib import validate\n'
                                 'def validate_beats(reference, estimated):\n'
                                 '    return validate(reference, estimated)\n')
        accepted = suggestions.validate_suggestions(proposal, context)
        self.assertEqual('validate_beats', accepted['aliases'][0]['name'])

    def test_default_settings_and_prompt_remain_compatible(self):
        settings = self.settings()
        self.assertEqual('all', settings['proposal_scope'])
        self.assertEqual(suggestions.PROMPT.read_text(), suggestions.proposal_system_prompt(settings))
        self.assertEqual(suggestions.PROMPT.read_text(), suggestions.proposal_system_prompt(self.settings('all')))

    def test_unknown_scope_is_rejected_before_any_request(self):
        for invalid in ['aliases', '', None, 1, [], {}]:
            with self.subTest(scope=invalid), self.assertRaisesRegex(ValueError, 'proposal_scope'):
                self.settings(invalid)

    def test_single_preview_records_the_selected_scope(self):
        for scope in ['missing', 'aliases_only']:
            with self.subTest(scope=scope):
                self.settings(scope)
                output = self.root / ('single-' + scope)
                with patch.object(suggestions, '_load_preview', return_value=(self.preview, self.root, {})), \
                     patch.object(suggestions, 'development_destination', side_effect=lambda study, path: Path(path)), \
                     patch.object(suggestions, 'invoke', side_effect=self.fake_invoke), \
                     patch.object(suggestions, '_finish_proposal', return_value={'status': 'review_candidates_only'}):
                    suggestions.propose_improvements(self.root / 'preview.json', self.config, output)
                request = json.loads((output / 'model_attempt/request.json').read_text())
                self.assert_scope(request, scope)

    def test_library_batch_records_the_selected_scope(self):
        for scope in ['missing', 'aliases_only']:
            with self.subTest(scope=scope):
                settings = self.settings(scope)
                output = self.root / ('batch-' + scope)
                with patch.object(batches, '_load_preview', return_value=(self.preview, self.root, {})), \
                     patch.object(batches, 'invoke', side_effect=self.fake_invoke), \
                     patch.object(batches, '_finish_proposal', return_value={'status': 'review_candidates_only'}):
                    result, calls = batches._run_batch(self.root / 'preview.json', settings,
                        output, 'test-identity', [], set())
                self.assertEqual(1, calls)
                self.assertEqual('review_candidates_only', result['status'])
                self.assert_scope(json.loads((output / 'request.json').read_text()), scope)
                self.assertEqual(json.loads((output / 'request.json').read_text()),
                                 json.loads((output / 'attempt_001/request.json').read_text()))


if __name__ == '__main__':
    unittest.main()
