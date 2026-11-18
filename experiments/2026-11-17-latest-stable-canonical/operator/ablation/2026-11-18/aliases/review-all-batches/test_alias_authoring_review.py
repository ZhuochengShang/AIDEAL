"""Exercise the real review loop with temporary source studies and mocked providers."""
from argparse import Namespace
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(os.environ.get('AIDEAL_TEST_ROOT',
    '/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow')).resolve()
sys.path.insert(0, str(ROOT))
from workflow import ablation as a, execution as e
from workflow import improvement_batches as b, improvement_suggestions as suggestions

spec = importlib.util.spec_from_file_location('_proposal_fixture', ROOT / 'tests/test_improvement_batches.py')
fixture_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture_module)
spec = importlib.util.spec_from_file_location('_review_operator', Path(__file__).with_name('alias_authoring_review.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class AuthoringReviewLoopTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture_module.LibraryProposalTests(
            'test_every_public_api_has_one_bounded_preview_with_profile_and_safe_config')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.settings['model']['proposal_scope'] = 'aliases_only'
        self.fixture.model_config.write_text(json.dumps(self.fixture.settings))
        self.root = self.fixture.root
        self.calls = []
        self.behavior = {}
        self.names = {}
        # This deliberately avoids enumerating unrelated local workflow files.
        # The provider script is a stable bound fixture and is never executed.
        guard = patch.object(b, '_implementation_bindings',
                             return_value=[a.bind(self.fixture.model_script)])
        guard.start()
        self.addCleanup(guard.stop)

    def proposal(self, context):
        api = context['apis'][0]
        name = self.names.get(context['batch_id'], 'friendly_' + api['name'])
        return {'aliases': [{'name': name, 'target_function': api['id'],
                             'rationale': 'A clear alternative name.'}],
                'alias_code': f"from .ops import {api['name']}\ndef {name}(v, scale=2):\n    return {api['name']}(v, scale)\n",
                'alias_interface': name + '(v, scale=2) forwards to the existing operation.',
                'hints': [], 'refactors': [], 'notes': 'Synthetic unvalidated candidate.'}

    def fake_invoke(self, command, request, directory, timeout):
        directory = Path(directory)
        if (directory / 'process.json').exists():
            self.assertEqual(request, a.load(directory / 'request.json'))
            return a.load(directory / 'process.json')
        directory.mkdir(parents=True, exist_ok=False)
        context = json.loads(request['prompt'])
        kind = self.behavior.get(context['batch_id'], 'valid')
        self.calls.append(context['batch_id'])
        e.atomic_json(directory / 'request.json', request)
        if kind == 'timeout':
            result = {'status': 'timeout', 'returncode': None, 'payload': None}
        else:
            proposal = self.proposal(context)
            if kind == 'wrong_target':
                proposal['aliases'][0]['target_function'] = 'outside_supplied_context'
            if kind == 'import_only':
                proposal['alias_code'] = 'from .ops import alpha as friendly_alpha\n'
            result = {'status': 'ok', 'returncode': 0, 'payload': {
                'code': json.dumps(proposal),
                'solution_state': {'status': 'incomplete' if kind == 'incomplete' else 'complete'}}}
            if kind == 'missing_completion_metadata':
                result['payload'].pop('solution_state')
        e.atomic_json(directory / 'process.json', result)
        return result

    def make_protocol(self, *, prefix=0, one_api=False):
        self.manifest_path = self.fixture.plan(**({'apis': ['alpha']} if one_api else {}))
        self.manifest = a.load(self.manifest_path)
        self.public_names = {row['name'] for row in self.manifest['api_catalog']}
        mapping = {'full_manifest': a.bind(self.manifest_path), 'attempts': []}
        settings = suggestions._model_settings(self.fixture.model_config)
        for batch in self.manifest['batches'][:prefix]:
            preview = a.load(batch['preview']['path'])
            request = {'system': suggestions.proposal_system_prompt(settings),
                       'prompt': json.dumps(preview['context'], ensure_ascii=False, indent=2),
                       'model': settings['name'], 'temperature': settings['temperature'],
                       'max_output_tokens': settings['max_output_tokens']}
            attempt = self.root / 'previous' / batch['batch_id'] / 'attempt_001'
            self.fake_invoke([], request, attempt, 1)
            mapping['attempts'].append({'batch_id': batch['batch_id'], 'attempt': str(attempt),
                                        'request': a.bind(attempt / 'request.json'),
                                        'process': a.bind(attempt / 'process.json')})
        recorded = self.root / 'recorded-attempts.json'
        e.atomic_json(recorded, mapping)
        self.preparation = self.root / 'review-preparation'
        prepare = Namespace(full_manifest=str(self.manifest_path), model_config=str(self.fixture.model_config),
                            recorded_attempts=str(recorded), output=str(self.preparation),
                            release=str(ROOT), bank='fixture')
        with contextlib.redirect_stdout(io.StringIO()):
            m.prepare(prepare, a, e, b, suggestions)
        self.output = self.root / 'review-output'
        self.args = Namespace(continuation=str(self.preparation / 'CONTINUATION.json'),
                              output=str(self.output), release=str(ROOT))
        self.calls.clear()

    def run_review(self, *, forbidden_core=False, core=None):
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(b, 'invoke', side_effect=self.fake_invoke))
            if forbidden_core:
                stack.enter_context(patch.object(b, '_run_batch', side_effect=AssertionError('unexpected new model attempt')))
            if core:
                stack.enter_context(patch.object(b, '_run_batch', side_effect=core))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            result = m.run(self.args, a, e, b, suggestions)
        return result, a.load(self.output / 'BANK_UNION.json')

    def test_complete_schema_rejection_continues_and_exact_exposure_completes(self):
        self.behavior['batch-0001'] = 'wrong_target'
        self.make_protocol()
        code, report = self.run_review()
        self.assertEqual(0, code)
        self.assertEqual(['batch-0001', 'batch-0002', 'batch-0003'], self.calls)
        self.assertEqual('reviewed_with_rejections', report['status'])
        self.assertEqual((2, 1, 3), (report['accepted_batches'], report['rejected_batches'], report['reviewed_api_count']))
        self.assertTrue(report['full_api_exposure_complete'])
        self.assertFalse(report['all_candidates_valid'])
        self.assertFalse(report['installed'])
        self.assertEqual(2, len(report['accepted_proposals']))
        first = a.load(self.output / 'batch-0001/REVIEW.json')
        self.assertFalse(first['accepted'])
        self.assertIsNone(first['proposal'])
        self.assertTrue((self.output / 'AUTHORING_COMPLETION.json').exists())
        candidates = a.load(self.output / 'ACCEPTED_CANDIDATES.json')
        self.assertEqual(report['accepted_proposals'], candidates['accepted_proposals'])
        self.assertEqual('schema_valid_candidates_runtime_validation_pending', candidates['status'])
        self.assertFalse(candidates['installed'])
        self.assertTrue(all(Path(ref['path']).parent.name != 'batch-0001'
                            for ref in candidates['accepted_proposals']))

    def test_rejected_prefix_and_valid_remaining_preserve_disjoint_coverage(self):
        self.behavior['batch-0002'] = 'wrong_target'
        self.make_protocol(prefix=2)
        first_process = a.bind(self.root / 'previous/batch-0002/attempt_001/process.json')
        code, report = self.run_review()
        self.assertEqual(0, code)
        self.assertEqual(['batch-0003'], self.calls)
        self.assertEqual((2, 1, 3), (report['accepted_batches'], report['rejected_batches'], report['reviewed_api_count']))
        self.assertTrue(report['exact_disjoint_full_bank_coverage'])
        self.assertTrue(a.verify_artifact(first_process))
        self.assertEqual(1, report['new_model_calls_this_invocation'])
        prefix_candidates = a.load(self.preparation / 'ACCEPTED_CANDIDATES.json')
        self.assertEqual(1, len(prefix_candidates['accepted_proposals']))
        self.assertEqual('batch-0001', Path(prefix_candidates['accepted_proposals'][0]['path']).parent.name)
        self.assertFalse(prefix_candidates['full_api_exposure_complete'])
        self.assertFalse(prefix_candidates['installed'])

    def test_timeout_pauses_without_later_calls_or_completion(self):
        self.behavior['batch-0001'] = 'timeout'
        self.make_protocol()
        code, report = self.run_review()
        self.assertEqual(2, code)
        self.assertEqual(['batch-0001'], self.calls)
        self.assertFalse(report['full_api_exposure_complete'])
        self.assertEqual(0, report['reviewed_api_count'])
        self.assertFalse((self.output / 'AUTHORING_COMPLETION.json').exists())

    def test_incomplete_response_cannot_be_admitted_even_if_core_emitted_proposal(self):
        self.behavior['batch-0001'] = 'incomplete'
        self.make_protocol()
        code, report = self.run_review()
        self.assertEqual(2, code)
        self.assertTrue((self.output / 'batch-0001/proposal.json').exists())
        self.assertTrue((self.output / 'batch-0001/completion.json').exists())
        self.assertEqual([], report['accepted_proposals'])
        self.assertEqual(['batch-0001'], self.calls)
        self.assertFalse((self.output / 'AUTHORING_COMPLETION.json').exists())

    def test_missing_provider_completion_metadata_pauses(self):
        self.behavior['batch-0001'] = 'missing_completion_metadata'
        self.make_protocol()
        code, report = self.run_review()
        self.assertEqual(2, code)
        self.assertEqual(0, report['reviewed_api_count'])
        self.assertEqual([], report['accepted_proposals'])

    def test_duplicate_candidate_is_excluded_even_when_core_already_emitted_it(self):
        self.names.update({'batch-0001': 'same_friendly_name', 'batch-0002': 'same_friendly_name'})
        self.make_protocol()
        original_core = b._run_batch

        def core_with_original_public_names(*arguments):
            # Simulate a cached/core proposal emitted before cross-batch review.
            return original_core(*arguments[:-1], self.public_names)

        code, report = self.run_review(core=core_with_original_public_names)
        self.assertEqual(0, code)
        self.assertTrue((self.output / 'batch-0002/proposal.json').exists())
        second = a.load(self.output / 'batch-0002/REVIEW.json')
        self.assertFalse(second['accepted'])
        self.assertIsNone(second['proposal'])
        accepted = [alias['name'] for ref in report['accepted_proposals'] for alias in a.load(ref['path'])['aliases']]
        self.assertEqual(['same_friendly_name', 'friendly_gamma'], accepted)
        self.assertEqual(1, report['rejected_batches'])
        candidates = a.load(self.output / 'ACCEPTED_CANDIDATES.json')
        self.assertEqual(report['accepted_proposals'], candidates['accepted_proposals'])
        self.assertTrue(all(Path(ref['path']).parent.name != 'batch-0002'
                            for ref in candidates['accepted_proposals']))
        self.assertFalse(candidates['installed'])

    def test_saved_rejected_review_resume_makes_zero_calls(self):
        self.behavior['batch-0001'] = 'wrong_target'
        self.make_protocol()
        self.run_review()
        self.calls.clear()
        code, report = self.run_review(forbidden_core=True)
        self.assertEqual(0, code)
        self.assertEqual([], self.calls)
        self.assertEqual(0, report['new_model_calls_this_invocation'])
        self.assertEqual('reviewed_with_rejections', report['status'])

    def test_complete_raw_response_recovers_offline_after_publication_interruption(self):
        self.make_protocol(one_api=True)
        with patch.object(b, '_finish_proposal', side_effect=RuntimeError('simulated publication interruption')):
            with self.assertRaisesRegex(RuntimeError, 'publication interruption'):
                self.run_review()
        self.assertEqual(['batch-0001'], self.calls)
        self.assertTrue((self.output / 'batch-0001/attempt_001/process.json').exists())
        self.assertFalse((self.output / 'batch-0001/REVIEW.json').exists())
        self.calls.clear()
        code, report = self.run_review(forbidden_core=True)
        self.assertEqual(0, code)
        self.assertEqual([], self.calls)
        self.assertEqual(0, report['new_model_calls_this_invocation'])

    def test_changed_accepted_child_artifact_blocks_zero_call_resume(self):
        self.make_protocol()
        self.run_review()
        proposal = a.load(self.output / 'batch-0001/proposal.json')
        Path(proposal['artifacts']['alias']['path']).write_text('def changed(): pass\n')
        self.calls.clear()
        with self.assertRaisesRegex(ValueError, 'artifacts changed'):
            self.run_review(forbidden_core=True)
        self.assertEqual([], self.calls)

    def test_batch_symlink_blocks_resume_before_model_call_or_external_write(self):
        self.make_protocol()
        self.run_review()
        original = self.output / 'batch-0002'
        outside = self.root / 'outside-batch'
        original.rename(outside)
        original.symlink_to(outside, target_is_directory=True)
        before = {str(path.relative_to(outside)): path.read_bytes() for path in outside.rglob('*') if path.is_file()}
        self.calls.clear()
        with self.assertRaisesRegex(ValueError, 'ordinary child'):
            self.run_review(forbidden_core=True)
        self.assertEqual([], self.calls)
        after = {str(path.relative_to(outside)): path.read_bytes() for path in outside.rglob('*') if path.is_file()}
        self.assertEqual(before, after)

    def test_prepare_output_inside_source_is_rejected_without_writes(self):
        self.make_protocol()
        source = self.fixture.study / 'Original/source'
        prohibited = source / 'review-output'
        before = {str(path.relative_to(source)): path.read_bytes() for path in source.rglob('*') if path.is_file()}
        args = Namespace(full_manifest=str(self.manifest_path), model_config=str(self.fixture.model_config),
                         recorded_attempts=str(self.root / 'recorded-attempts.json'),
                         output=str(prohibited), release=str(ROOT), bank='fixture')
        with self.assertRaisesRegex(ValueError, 'outside source checkouts'):
            m.prepare(args, a, e, b, suggestions)
        self.assertFalse(prohibited.exists())
        self.assertEqual([], self.calls)
        after = {str(path.relative_to(source)): path.read_bytes() for path in source.rglob('*') if path.is_file()}
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
