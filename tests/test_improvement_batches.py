"""Synthetic adapters only: complete coverage, evidence integrity and safe resume."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from workflow.ablation import digest, load
from workflow.execution import atomic_json
from workflow.improvement_batches import preview_library_improvements, propose_library_improvements
from workflow.improvement_suggestions import validate_suggestions
from workflow.worktrees import attach


class LibraryProposalTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.repo = self.root / 'library'
        (self.repo / 'src').mkdir(parents=True)
        (self.repo / 'src/ops.py').write_text('raise RuntimeError("TARGET_MUST_NOT_RUN")\n\n' + ''.join(
            f'def {name}(v, scale=2):\n    """Public value transformation."""\n'
            '    result = v * scale\n    return result\n\n' for name in ('alpha', 'beta', 'gamma')))
        (self.repo / 'README.md').write_text('Public library documentation')
        (self.repo / 'private_answers.txt').write_text('PRIVATE_ANSWER_MUST_NOT_APPEAR')
        config = self.repo / 'configs/aideal.yaml'
        config.parent.mkdir()
        config.write_text('extends: [python]\nproject: {name: Example, language: Python}\n'
                          'codebase: {source_globs: [src/**/*.py]}\nfiles: {original_readme: README.md}\n'
                          'models: {secret: DO_NOT_SEND_MODEL_SETTINGS}\n')
        (config.parent / 'project_profile.yaml').write_text('project: {description: Numeric utility APIs}\n'
                                                         'domain: research\nconstraints: [Preserve original APIs]\n')
        def git(*args):
            return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.DEVNULL)
        git('init', '-q'); git('config', 'user.name', 'Test'); git('config', 'user.email', 'test@example.invalid')
        git('add', '.'); git('commit', '-qm', 'Fixture')
        self.study = self.root / 'study'
        attach(self.repo, config, self.study)
        self.errors = self.root / 'development.jsonl'
        self.errors.write_text(''.join(json.dumps({'function': name, 'status': 'fail', 'split': 'development',
                                                 'error': 'bad scale: must be numeric'}) + '\n'
                                       for name in ('alpha', 'beta', 'gamma')))
        self.model_script = self.root / 'provider.py'
        self.model_script.write_text('raise RuntimeError("USE_THE_MOCK_ONLY")\n')
        self.model_config = self.root / 'model.json'
        self.settings = {'model': {'name': 'synthetic', 'command': [sys.executable, str(self.model_script)],
                                   'temperature': 0, 'max_output_tokens': 4000, 'timeout_s': 1,
                                   'provider_attempt_limit': 2}}
        self.model_config.write_text(json.dumps(self.settings))
        self.calls = []
        self.collide = False
        self.fail_once = False

    def plan(self, **kwargs):
        kwargs = {'alias_path_template': 'src/aliases_{batch}.py', 'batch_size': 1,
                  'development_errors': self.errors, **kwargs}
        return Path(preview_library_improvements(self.study, self.root / 'preview', **kwargs)['manifest'])

    def suggestions(self, context):
        aliases, code, hints, refactors = [], [], [], []
        for api in context['apis']:
            if context['alias_destination']:
                name = 'friendly' if self.collide else 'alias_' + api['name']
                aliases.append({'name': name, 'target_function': api['id'], 'rationale': 'Clear entry name'})
                code.append(f"from .ops import {api['name']}\n\ndef {name}(v, scale=2):\n    return {api['name']}(v, scale)\n")
            refactors.append({'title': 'Review internal naming', 'function_ids': [api['id']],
                'source_evidence': [{'function_id': api['id'], 'start_line': api['line'],
                                     'end_line': api['line'], 'quote': 'def ' + api['name']}],
                'rationale': 'The source exposes an intermediate result.',
                'proposed_change': 'Review whether an internal helper would improve readability.',
                'preservation_plan': 'Preserve public signature, defaults, returns and exceptions.',
                'regression_checks': ['Compare numeric, invalid-input and side-effect behavior.'],
                'risks': 'Bounded source is insufficient to prove equivalence.'})
        for error in context['development_errors']:
            hints.append({'function_id': error['function_id'], 'evidence_ids': [error['id']],
                          'error_contains': 'bad scale', 'likely_cause': 'Scale may have the wrong type.',
                          'fix_steps': ['Inspect the scale value and documented contract.'],
                          'suggested_fix_code': '', 'validation': 'Check valid and invalid numeric inputs.'})
        return {'aliases': aliases, 'alias_code': '\n'.join(code),
                'alias_interface': 'Delegates to canonical APIs.' if aliases else '',
                'hints': hints, 'refactors': refactors, 'notes': 'Unverified synthetic proposal.'}

    def fake_invoke(self, command, request, directory, timeout):
        directory = Path(directory)
        if (directory / 'process.json').exists():
            self.assertEqual(request, load(directory / 'request.json'))
            return load(directory / 'process.json')
        directory.mkdir(parents=True, exist_ok=False)
        self.calls.append(directory)
        atomic_json(directory / 'request.json', request)
        if self.fail_once:
            self.fail_once = False
            result = {'status': 'timeout', 'payload': None}
        else:
            result = {'status': 'ok', 'payload': {'code': json.dumps(self.suggestions(json.loads(request['prompt'])))}}
        atomic_json(directory / 'process.json', result)
        return result

    def run_plan(self, manifest, **kwargs):
        with patch('workflow.improvement_batches.invoke', side_effect=self.fake_invoke):
            return propose_library_improvements(manifest, self.model_config, self.root / 'proposals', **kwargs)

    def test_every_public_api_has_one_bounded_preview_with_profile_and_safe_config(self):
        manifest = load(self.plan())
        self.assertEqual(3, manifest['coverage']['planned_definitions'])
        ids = [identifier for batch in manifest['batches'] for identifier in batch['api_ids']]
        self.assertEqual(3, len(set(ids)))
        for batch in manifest['batches']:
            preview = load(batch['preview']['path']); context = preview['context']
            self.assertEqual('research', context['project_profile']['domain'])
            self.assertIn('public_def_regex', context['configuration'])
            self.assertEqual(3, len(context['library_overview']['api_catalog']))
            self.assertEqual(0, context['library_overview']['omitted_catalog_entries'])
            text = json.dumps(context, ensure_ascii=False, indent=2)
            self.assertEqual(batch['context_characters'], len(text))
            self.assertLessEqual(len(text), manifest['settings']['max_context_characters'])
            self.assertNotIn('PRIVATE_ANSWER_MUST_NOT_APPEAR', text)
            self.assertNotIn('DO_NOT_SEND_MODEL_SETTINGS', text)
            self.assertEqual(1, len(context['development_errors']))
        self.assertIn('TARGET_MUST_NOT_RUN', json.dumps(load(manifest['batches'][0]['preview']['path'])))
        self.assertFalse(self.calls)

    def test_resume_preserves_exact_requests_and_completed_batches(self):
        manifest = self.plan()
        first = self.run_plan(manifest, max_batches=1)
        self.assertEqual(('incomplete', 1, 1), (first['status'], first['completed_batches'], first['llm_calls']))
        second = self.run_plan(manifest)
        self.assertEqual(('complete_unvalidated', 3, 2), (second['status'], second['completed_batches'], second['llm_calls']))
        third = self.run_plan(manifest)
        self.assertEqual(0, third['llm_calls']); self.assertEqual(3, len(self.calls))
        collection = load(third['collection'])
        for batch in collection['batches']:
            proposal = load(batch['proposal']['path'])
            self.assertEqual(batch['batch_id'], proposal['source_batch'])
            self.assertNotIn('refactor_suggestions', proposal['artifacts'])
            self.assertTrue(Path(proposal['refactor_suggestions']['path']).exists())
            request = load(proposal['request']['path'])
            preview = load(Path(batch['proposal']['path']).parent / 'preview.json')
            self.assertEqual(preview['context'], json.loads(request['prompt']))
        self.assertFalse((self.study / 'Alias only/source/src/aliases_0001.py').exists())

    def test_failed_attempt_resumes_without_repeating_successes(self):
        manifest = self.plan(); self.fail_once = True
        first = self.run_plan(manifest)
        self.assertEqual('incomplete', first['status']); self.assertEqual(1, first['llm_calls'])
        second = self.run_plan(manifest)
        self.assertEqual('complete_unvalidated', second['status'])
        self.assertEqual(4, len(self.calls))
        self.assertTrue((self.root / 'proposals/batch-0001/attempt_001/process.json').exists())
        self.assertTrue((self.root / 'proposals/batch-0001/attempt_002/process.json').exists())

    def test_valid_json_in_incomplete_response_is_preserved_but_not_published(self):
        self.settings['model']['provider_attempt_limit'] = 1
        self.model_config.write_text(json.dumps(self.settings))
        manifest = self.plan()
        def partial(command, request, directory, timeout):
            result = self.fake_invoke(command, request, directory, timeout)
            result['payload']['response_status'] = 'incomplete'
            result['payload']['truncated'] = True
            atomic_json(Path(directory) / 'process.json', result)
            return result
        with patch('workflow.improvement_batches.invoke', side_effect=partial):
            first = propose_library_improvements(manifest, self.model_config, self.root / 'proposals')
        batch = self.root / 'proposals/batch-0001'
        self.assertEqual('incomplete', first['status'])
        self.assertTrue((batch / 'attempt_001/rejected.json').is_file())
        self.assertFalse((batch / 'proposal.json').exists())
        self.assertFalse((batch / 'completion.json').exists())
        second = self.run_plan(manifest)
        self.assertEqual('incomplete', second['status'])
        self.assertEqual(0, second['llm_calls'])
        self.assertEqual(1, len(self.calls))

    def test_attempt_limit_bounds_failed_and_interrupted_calls(self):
        self.settings['model']['provider_attempt_limit'] = 1
        self.model_config.write_text(json.dumps(self.settings))
        manifest = self.plan(); self.fail_once = True
        self.run_plan(manifest)
        result = self.run_plan(manifest)
        self.assertEqual(0, result['llm_calls'])
        self.assertEqual('attempt_budget_exhausted', load(result['collection'])['stopped']['status'])
        self.assertEqual(1, len(self.calls))

    def test_changed_model_command_artifact_blocks_resume(self):
        manifest = self.plan(); self.run_plan(manifest, max_batches=1)
        self.model_script.write_text('raise RuntimeError("CHANGED_COMMAND")\n')
        with self.assertRaisesRegex(ValueError, 'identity changed'):
            self.run_plan(manifest)
        self.assertEqual(1, len(self.calls))

    def test_completed_response_recovers_after_interrupted_publication_without_model_repeat(self):
        manifest = self.plan()
        with patch('workflow.improvement_batches._finish_proposal', side_effect=RuntimeError('publication interrupted')):
            with self.assertRaisesRegex(RuntimeError, 'interrupted'):
                self.run_plan(manifest)
        result = self.run_plan(manifest)
        self.assertEqual('complete_unvalidated', result['status'])
        self.assertEqual(2, result['llm_calls']); self.assertEqual(3, len(self.calls))

    def test_changed_configuration_or_completed_evidence_blocks_resume(self):
        manifest = self.plan(); self.run_plan(manifest, max_batches=1)
        original = self.model_config.read_text()
        self.settings['model']['temperature'] = 1
        self.model_config.write_text(json.dumps(self.settings))
        with self.assertRaisesRegex(ValueError, 'identity changed'):
            self.run_plan(manifest)
        self.model_config.write_text(original)
        (self.root / 'proposals/batch-0001/suggestions.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'evidence changed'):
            self.run_plan(manifest)
        self.assertEqual(1, len(self.calls))

    def test_alias_collisions_are_flagged_across_batches(self):
        manifest = self.plan(); self.collide = True
        result = self.run_plan(manifest)
        self.assertEqual('alias_collisions_require_review', result['status'])
        self.assertEqual(2, len(result['alias_collisions']))

    def test_refactors_require_actual_quote_and_each_function_evidence(self):
        manifest = load(self.plan(batch_size=2))
        context = load(manifest['batches'][0]['preview']['path'])['context']
        valid = self.suggestions(context)
        validate_suggestions(valid, context)
        for field, value in [('quote', 'invented source'), ('start_line', 999999), ('function_id', 'unknown')]:
            changed = deepcopy(valid)
            changed['refactors'][0]['source_evidence'][0][field] = value
            with self.assertRaises(ValueError): validate_suggestions(changed, context)
        changed = deepcopy(valid)
        changed['refactors'][0]['function_ids'].append(context['apis'][1]['id'])
        with self.assertRaisesRegex(ValueError, 'Every refactored function'):
            validate_suggestions(changed, context)

    def test_cross_batch_public_name_is_reserved_even_when_overview_omits_it(self):
        manifest = load(self.plan(max_catalog_characters=500))
        context = load(manifest['batches'][0]['preview']['path'])['context']
        overview = context['library_overview']
        self.assertLessEqual(len(json.dumps(overview, ensure_ascii=False, indent=2)), 500)
        self.assertGreater(overview['omitted_catalog_entries'], 0)
        valid = self.suggestions(context)
        valid['aliases'][0]['name'] = 'beta'
        valid['alias_code'] = 'def beta(v, scale=2):\n    return alpha(v, scale)\n'
        with self.assertRaisesRegex(ValueError, 'distinct new identifier'):
            validate_suggestions(valid, context, reserved_names={row['name'] for row in manifest['api_catalog']})

    def test_insufficient_budget_never_silently_drops_apis(self):
        with self.assertRaisesRegex(ValueError, 'max_batches'):
            self.plan(max_batches=2)
        self.assertFalse((self.root / 'preview').exists())
        with self.assertRaisesRegex(ValueError, 'context budget'):
            self.plan(max_context_characters=1000)
        self.assertFalse((self.root / 'preview').exists())

    def test_hold_blocks_proposals_but_preview_still_allowed(self):
        (self.study / 'REVIEW_HOLD.json').write_text('{}')
        manifest = self.plan()
        with self.assertRaisesRegex(ValueError, 'paused'):
            self.run_plan(manifest)
        self.assertFalse(self.calls)
        self.assertFalse((self.root / 'proposals').exists())

    def test_manifest_cannot_redirect_a_batch_directory_even_with_a_new_digest(self):
        path = self.plan(); manifest = load(path)
        manifest['batches'][0]['batch_id'] = '../escaped'
        manifest['manifest_sha256'] = digest({k: v for k, v in manifest.items() if k != 'manifest_sha256'})
        atomic_json(path, manifest)
        with self.assertRaisesRegex(ValueError, 'safe directory names'):
            self.run_plan(path)
        self.assertFalse(self.calls)
        self.assertFalse((self.root / 'proposals').exists())


if __name__ == '__main__':
    unittest.main()
