"""Verify optional runtime guards at the native provider/execution boundaries."""
from unittest.mock import patch
import unittest

import test_doc_check_modules as native_fixture
from aideal import doc_check_execution
from aideal.readme_agent import ApiEntry


class NativeRuntimeProfileTests(unittest.TestCase):
    def setUp(self):
        self.fixture = native_fixture.DocCheckModuleTests('test_native_success_repair_timeout_and_provider_failure_keep_contract')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.cfg.comprehension['execute']['runtime_profile'] = '/synthetic/runtime.json'

    def test_native_execution_revalidates_runtime_and_fingerprints_receipt(self):
        receipt = [{'path': '/synthetic/runtime.json', 'sha256': 'a' * 64}]
        with patch('workflow.runtime_profile.load_runtime_profile', return_value={'schema': 1}), \
             patch('workflow.runtime_profile.runtime_profile_receipts', return_value=receipt), \
             patch('workflow.runtime_profile.require_runtime_ready'), \
             patch('workflow.runtime_profile.verify_runtime_profile') as verify:
            result, prompts, calls = self.fixture._mocked_native_run(doc_check_execution, 'success')
        self.assertEqual(len(prompts), 1)
        self.assertEqual(calls, 1)
        self.assertGreaterEqual(verify.call_count, 4)
        self.assertEqual(result['run']['fingerprint_components']['runtime_profile'], receipt)

    def test_unresolved_setup_blocks_before_any_provider_request(self):
        with patch('workflow.runtime_profile.load_runtime_profile', return_value={'schema': 1}), \
             patch('workflow.runtime_profile.verify_runtime_profile'), \
             patch('workflow.runtime_profile.require_runtime_ready', side_effect=ValueError('unresolved setup')), \
             patch('aideal.llm.invoke_text') as provider:
            with self.assertRaisesRegex(ValueError, 'unresolved setup'):
                doc_check_execution._comprehension_execute(self.fixture.cfg,
                    [ApiEntry('f', '', '', 'Documentation')], 0, 42, 'aideal', max_fix_rounds=0)
        provider.assert_not_called()


if __name__ == '__main__':
    unittest.main()
