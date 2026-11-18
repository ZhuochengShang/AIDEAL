"""Offline checks for source-note validation and explicit revision replay."""
from copy import deepcopy
import fcntl
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import test_readme_launcher as fixture
launcher, entry = fixture.launcher, fixture.entry
from aideal.readme_recording import ReadmeGenerationStopped, ReadmeCallRecorder, digest
from aideal.readme_replay import compatible, ReplayStore, _documentation_ast
from aideal.readme_validation import validate_entry

SOURCE_NOTE = 'TODO: update docs to property doc'


def documented(name):
    return (f'## API Test: `{name}`\n\n### Signature\n```python\n{name}(x)\n```\n'
            f'_Source doc:_ {SOURCE_NOTE}\n\n### Goal\nCompute a small number.\n')


class ValidationTests(unittest.TestCase):
    def test_exact_source_note_is_allowed_and_preserved(self):
        text = documented('Charges')
        validate_entry(text, 'Charges', [SOURCE_NOTE])
        self.assertIn(SOURCE_NOTE, text)

    def test_authored_placeholder_and_invented_quote_are_rejected(self):
        for text, docs in [(documented('Charges'), []),
                           (documented('Charges') + '\nTODO: finish example', [SOURCE_NOTE]),
                           (entry('Charges') + '\n> TODO: describe goal', [SOURCE_NOTE]),
                           (entry('Charges') + '\n_Source doc:_ ' + SOURCE_NOTE, [SOURCE_NOTE]),
                           (entry('Charges') + '\n```python\n# todo: finish\n```', [])]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                validate_entry(text, 'Charges', docs)

    def test_documentation_only_ast_does_not_allow_behavior_changes(self):
        before = 'def f():\n    "old docs"\n    return 1\np.add_argument("--set", default="shared", help="old")'
        after = before.replace('old docs', 'new docs').replace('help="old"', 'help="new"')
        self.assertEqual(_documentation_ast(before), _documentation_ast(after))
        self.assertNotEqual(_documentation_ast(before), _documentation_ast(after.replace('return 1', 'return 2')))
        self.assertNotEqual(_documentation_ast(before), _documentation_ast(after.replace('default="shared"', 'default="surface"')))

    def test_wrong_headers_and_empty_responses_still_fail(self):
        for text in ['', entry('wrong'), entry('Charges') + entry('Charges')]:
            with self.assertRaises(ValueError):
                validate_entry(text, 'Charges', [SOURCE_NOTE])


class ReplayTests(unittest.TestCase):
    setUp = fixture.ReadmeLauncherTests.setUp
    prepare = fixture.ReadmeLauncherTests.prepare
    generate = fixture.ReadmeLauncherTests.generate

    def old_failure(self):
        (self.source / 'api.py').write_text(
            'def alpha(x):\n    return x\n\ndef beta(x):\n'
            '    """TODO: update docs to property doc"""\n    return x+1\n')
        prepared = self.prepare()
        def old_validator(text, api, source_docs=()):
            if api is not None and 'TODO' in text:
                raise ValueError('old blanket TODO gate')
            validate_entry(text, api)
        with patch.object(ReadmeCallRecorder, '_validate', staticmethod(old_validator)), \
             patch('aideal.llm.usage_delta', return_value={'calls': 1, 'input_tokens': 100, 'output_tokens': 50}):
            with self.assertRaises(ReadmeGenerationStopped):
                self.generate(prepared, ['summary', entry('alpha'), documented('beta')])
        (self.destination.parent / '.lock').touch()
        return prepared

    def revision(self):
        destination = self.root / 'revision/demo'
        return destination, launcher.prepare(self.library, destination, 'gemini-3.1-flash-lite',
                                             reuse_from=self.destination)

    def test_failed_source_note_revalidated_without_provider_or_old_edits(self):
        self.old_failure()
        saved = {p: p.read_bytes() for p in self.destination.rglob('*') if p.is_file()}
        destination, prepared = self.revision()
        with patch('aideal.llm.invoke_text', side_effect=AssertionError('Must replay')) as model:
            result = launcher.run_library(prepared[0], destination, prepared[1], prepared[2])
        self.assertEqual(0, model.call_count)
        self.assertEqual((3, 1, 0), (result['imported_calls'], result['revalidated_calls'], result['new_calls']))
        self.assertEqual([], list(destination.rglob('provider.json')))
        self.assertEqual(3, len(list(destination.rglob('replay_receipt.json'))))
        self.assertTrue(all(p.read_bytes() == data for p, data in saved.items()))
        with patch('aideal.llm.invoke_text', side_effect=AssertionError('Already complete')):
            self.assertEqual(result, launcher.run_library(prepared[0], destination, prepared[1], prepared[2]))
        response = next(self.destination.rglob('response.txt'))
        response.write_text('tampered')
        with self.assertRaisesRegex(ValueError, 'replay evidence changed'):
            launcher.run_library(prepared[0], destination, prepared[1], prepared[2])

    def test_model_source_and_prompt_changes_are_not_compatible(self):
        old = self.old_failure()[2]
        for field in ['model', 'manifest_sha256', 'effective_config_sha256', 'packages']:
            current = deepcopy(old); current[field] = 'changed'
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'incompatible'):
                compatible(old, current)
        for label in [str(self.source / 'api.py'), '/old/vendor/aideal_engine/src/aideal/default_prompts/aideal/readme_entry.md']:
            previous, current = deepcopy(old), deepcopy(old)
            previous['inputs'].append({'path': label, 'sha256': 'old'})
            current['inputs'].append({'path': label, 'sha256': 'new'})
            with self.assertRaises(ValueError):
                compatible(previous, current)

    def test_form_and_inventory_keep_source_note_but_reject_placeholders(self):
        from aideal.doc_check_sources import form_check, _comprehension_inventory
        cfg = self.old_failure()[0]
        cfg.required_sections = ['Signature', 'Goal']
        cfg.llm_readme.parent.mkdir(parents=True, exist_ok=True)
        text = documented('beta')
        cfg.llm_readme.write_text(text)
        self.assertTrue(form_check(cfg)['passed'])
        inventory, _, error = _comprehension_inventory(cfg, 'aideal')
        self.assertIsNone(error)
        self.assertEqual([text.rstrip()], [e.body for e in inventory])
        cfg.llm_readme.write_text(text + '\nTODO: finish goal')
        self.assertFalse(form_check(cfg)['passed'])
        self.assertIsNotNone(_comprehension_inventory(cfg, 'aideal')[2])

    def test_active_previous_worker_prevents_snapshot(self):
        self.old_failure()
        with (self.destination.parent / '.lock').open('r+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(ValueError, 'active worker'):
                self.revision()

    def test_exact_rendered_request_is_required(self):
        self.old_failure()
        destination, prepared = self.revision()
        replay = ReplayStore(destination / 'inputs/replay_plan.json', prepared[2]['replay_plan_sha256'],
                             prepared[2]['identity_sha256'], destination / 'author_replay')
        request = json.loads(next(self.destination.rglob('request.json')).read_text())
        request['binding'] = prepared[2]['identity_sha256']
        request['user'] += '\nchanged prompt'
        self.assertIsNone(replay.lookup(request, [SOURCE_NOTE]))

    def test_unfinished_returned_response_is_never_replayed(self):
        self.old_failure()
        request_path = next(p for p in self.destination.rglob('request.json')
                            if json.loads(p.read_text()).get('api') == 'beta')
        response = request_path.with_name('response.txt')
        response.write_text(documented('beta') + '\nTODO: finish examples')
        provider = request_path.with_name('provider.json')
        state = json.loads(provider.read_text()); state['response_sha256'] = digest(response.read_bytes())
        provider.write_text(json.dumps(state))
        destination, prepared = self.revision()
        with patch('aideal.llm.invoke_text', return_value=documented('beta')) as model:
            result = launcher.run_library(prepared[0], destination, prepared[1], prepared[2])
        self.assertEqual(1, model.call_count)
        self.assertEqual(0, result['revalidated_calls'])


if __name__ == '__main__':
    unittest.main()
