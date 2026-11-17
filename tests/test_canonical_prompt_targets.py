"""Native request identity tests with mocked providers and execution only."""
from contextlib import ExitStack, redirect_stderr
from copy import deepcopy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/aideal_engine/src'))
from aideal.config import load_config
from aideal import doc_check_execution
from aideal.experiment_identity import digest_native
from aideal.readme_agent import ApiEntry


def target():
    result = {'schema_version': 1, 'selection_policy_version': 'global_max_arity_non_wrapper_v1',
              'selection_receipt_sha256': 'a' * 64, 'selected_site_id': 'chosen-site',
              'qualified_name': 'selected.Owner.f', 'owner': 'selected.Owner',
              'signature': 'def f(x: Int, y: Int): Int', 'parameter_count': 2,
              'parameters': [{'name': 'x', 'type': 'Int'}, {'name': 'y', 'type': 'Int'}]}
    result['target_fingerprint'] = digest_native(result)
    return result


class CanonicalPromptTargetTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='aideal-canonical-request-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / 'configs').mkdir()
        (self.root / 'source.py').write_text('def f(x):\n    return x\n')
        (self.root / 'README.md').write_text('Use f.')
        (self.root / 'scaffold.py').write_text('# AIDEAL_DATA_BINDINGS\n# START\n# END\n')
        (self.root / 'runtime').mkdir()
        (self.root / 'runtime/mock.jar').write_bytes(b'mocked boundary only')
        config = {
            'project': {'name': 'canonical-request-fixture', 'language': 'Python'},
            'codebase': {'source_globs': ['source.py']},
            'files': {'original_readme': 'README.md'},
            'models': {'registry': {'fake': {'provider': 'synthetic', 'model': 'no-provider'}},
                       'roles': {'audience': 'fake', 'author': 'fake'}},
            'comprehension': {'execute': {'command': 'synthetic {test_file}', 'scaffold': 'scaffold.py',
                'region': ['# START', '# END'], 'work_dir': 'work', 'test_filename': 'Generated.py',
                'success_marker': 'DONE', 'spark_jars': 'runtime/*.jar', 'max_fix_rounds': 0,
                'execution_context': 'Fixed execution instructions.', 'local_uris': False,
                'output_dir': str(self.root / 'output')}},
        }
        (self.root / 'configs/aideal.yaml').write_text(yaml.safe_dump(config))
        self.cfg = load_config(self.root / 'configs/aideal.yaml')

    def run_request(self, targets, doc_source='original', document='Treatment document'):
        with ExitStack() as stack:
            stack.enter_context(redirect_stderr(io.StringIO()))
            provider = stack.enter_context(patch('aideal.llm.invoke_text', return_value='print("DONE")'))
            stack.enter_context(patch('aideal.execution.run_command',
                return_value=subprocess.CompletedProcess('synthetic', 0, 'DONE', '')))
            stack.enter_context(patch('subprocess.run', side_effect=AssertionError('Unexpected external process')))
            stack.enter_context(patch.object(doc_check_execution, '_canonical_prompt_targets', return_value=targets))
            stack.enter_context(patch.object(doc_check_execution, 'public_api_details', return_value=[]))
            stack.enter_context(patch.object(doc_check_execution, 'public_api_surface', return_value={'f'}))
            stack.enter_context(patch('aideal.readme_agent.public_api_details', return_value=[]))
            result = doc_check_execution._comprehension_execute(
                self.cfg, [ApiEntry('f', 'Call f', '', document)], 0, 42, doc_source, max_fix_rounds=0)
            request_path = Path(result['metrics']['f']['attempt_evidence'][0]) / 'request.json'
            request = json.loads(request_path.read_text())
            self.assertEqual(provider.call_args.args[1:], (request['system'], request['user']))
        return result, request

    def test_legacy_request_and_context_have_no_new_target_fields(self):
        result, request = self.run_request(None)
        self.assertNotIn('requested_target_declaration', request)
        self.assertNotIn('Requested target declaration', request['system'] + request['user'])
        self.assertNotIn('canonical_requested_targets', result['run']['fingerprint_components'])
        self.assertEqual('old context', doc_check_execution._requested_target_context('old context', None))

    def test_target_owner_signature_parameters_and_digest_reach_actual_saved_request(self):
        selected = target()
        result, request = self.run_request({'f': selected})
        self.assertEqual(selected, request['requested_target_declaration'])
        for text in ('Requested target declaration', selected['qualified_name'], selected['signature'],
                     'Parameters in declaration order (2): x: Int; y: Int'):
            self.assertIn(text, request['system'] + request['user'])
        components = result['run']['fingerprint_components']['canonical_requested_targets']
        self.assertEqual(digest_native({'f': selected}), components['targets_sha256'])
        self.assertNotIn('call_verified', request)

    def test_same_target_context_is_used_for_every_document_treatment(self):
        selected = target()
        block = doc_check_execution._requested_target_context('', selected)
        for condition in ('original', 'readme-only', 'alias-only', 'error-hints-only', 'combined'):
            self.cfg.comprehension['execute']['work_dir'] = 'work-' + condition
            _, request = self.run_request({'f': selected}, 'original' if condition == 'original' else 'aideal', condition)
            self.assertEqual(1, (request['system'] + request['user']).count(block))
            self.assertEqual(selected, request['requested_target_declaration'])

    def test_selected_definition_change_changes_the_run_fingerprint(self):
        first, _ = self.run_request({'f': target()})
        changed = target(); changed['selected_site_id'] = 'another-site'
        changed['target_fingerprint'] = digest_native({key: value for key, value in changed.items() if key != 'target_fingerprint'})
        second, _ = self.run_request({'f': changed})
        self.assertNotEqual(first['run']['experiment_fingerprint'], second['run']['experiment_fingerprint'])

    def test_missing_requested_target_fails_before_provider_request_even_for_empty_binding(self):
        for targets in ({}, {'other': target()}):
            with self.subTest(targets=targets), patch('aideal.llm.invoke_text', side_effect=AssertionError('No paid calls')):
                with self.assertRaisesRegex(ValueError, 'lack a canonical target'):
                    self.run_request(targets)

    def test_real_registry_binding_exposes_only_the_selected_public_declaration(self):
        from test_compiler_canonical_selection import CompilerCanonicalSelectionTests
        fixture = CompilerCanonicalSelectionTests()
        fixture.setUp(); self.addCleanup(fixture.doCleanups)
        targets = doc_check_execution._canonical_prompt_targets(fixture.cfg)
        self.assertEqual(['add'], list(targets))
        selected = targets['add']
        self.assertEqual('jlong', selected['selected_site_id'])
        self.assertEqual('Tools.add', selected['qualified_name'])
        self.assertEqual(3, selected['parameter_count'])
        self.assertIn('int z', selected['signature'])
        self.assertNotIn('return', selected['signature'])
        self.assertNotIn('body_classification', selected)
        self.assertNotIn('description', selected)
        self.assertNotIn('jshort', json.dumps(selected))
        fingerprint = selected.pop('target_fingerprint')
        self.assertEqual(digest_native(selected), fingerprint)

    def test_absent_binding_returns_none_and_changed_manifest_hash_is_rejected(self):
        self.assertIsNone(doc_check_execution._canonical_prompt_targets(self.cfg))
        from test_compiler_canonical_selection import CompilerCanonicalSelectionTests
        fixture = CompilerCanonicalSelectionTests()
        fixture.setUp(); self.addCleanup(fixture.doCleanups)
        fixture.definition_path.write_text(fixture.definition_path.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            doc_check_execution._canonical_prompt_targets(fixture.cfg)


if __name__ == '__main__':
    unittest.main()
