"""Study identity and latest completion semantics; no network is used."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from workflow import openai_codex_adapter as adapter
from workflow.provider_budget import BudgetLedger, BudgetError, digest
from test_openai_codex_adapter import openai, REQUEST, message, response


class StudyBudgetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'study.json'

    def ledger(self, cap='8', study='offline-test', policy='study-v2'):
        return BudgetLedger(self.path, cap, policy=policy, study_id=study)

    def reserve(self, ledger):
        return ledger.reserve('system', 'prompt', 8192, digest('request'), digest('settings'))

    def test_same_study_resumes_but_identity_cap_and_policy_cannot_change(self):
        ledger = self.ledger()
        first = self.reserve(ledger)
        ledger.finish(first, usage={'input_tokens': 50, 'cached_input_tokens': 0,
                                   'output_tokens': 12}, status='completed')
        self.reserve(self.ledger())
        before = self.path.read_bytes()
        for ledger in [self.ledger('9'), self.ledger(study='different-study'),
                       BudgetLedger(self.path, '5')]:
            with self.assertRaisesRegex(BudgetError, 'automatic reset'):
                self.reserve(ledger)
            self.assertEqual(self.path.read_bytes(), before)
        saved = json.loads(before)
        self.assertEqual(saved['schema_version'], 2)
        self.assertEqual(saved['study_id'], 'offline-test')
        self.assertEqual(saved['policy'], 'study-v2')

    def test_study_cannot_convert_existing_legacy_ledger(self):
        self.reserve(BudgetLedger(self.path, '5'))
        original = self.path.read_bytes()
        with self.assertRaisesRegex(BudgetError, 'automatic reset'):
            self.reserve(self.ledger('5'))
        self.assertEqual(self.path.read_bytes(), original)

    def test_explicit_policy_and_valid_study_identity_required(self):
        for kwargs in [{'max_cost_usd': '8'}, {'max_cost_usd': '101', 'policy': 'study-v2', 'study_id': 'test'},
                       {'policy': 'study-v2'}, {'policy': 'study-v2', 'study_id': '../unsafe'},
                       {'policy': 'legacy-v1', 'study_id': 'test'}, {'policy': 'unknown'}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(BudgetError):
                BudgetLedger(self.path, **kwargs)
        self.assertFalse(self.path.exists())

    def test_reserved_or_uncertain_capacity_is_not_released_by_resume(self):
        ledger = self.ledger('0.15')
        first = self.reserve(ledger)
        receipt = ledger.finish(first, failure={'type': 'TimeoutError'})
        self.assertEqual(receipt['state'], 'uncertain')
        with self.assertRaisesRegex(BudgetError, 'cannot cover'):
            self.reserve(self.ledger('0.15'))
        saved = json.loads(self.path.read_text())
        self.assertEqual(len(saved['records']), 1)
        self.assertEqual(saved['records'][0]['charged_nanousd'], saved['records'][0]['reserved_nanousd'])


@unittest.skipIf(openai is None, 'Optional SDK unavailable')
class StudyAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'study.json'
        self.audit_counter = 0
        self.client = MagicMock()
        self.client.__enter__.return_value = self.client
        self.client.responses.create.return_value = response()

    def invoke(self, cap='8'):
        self.audit_counter += 1
        output = io.StringIO()
        with patch.object(openai, 'OpenAI', return_value=self.client), \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'fake-private-value'}, clear=True), \
             patch('sys.stdin', io.StringIO(json.dumps({**REQUEST, 'max_output_tokens': 8192}))), \
             contextlib.redirect_stdout(output):
            adapter.main(['--budget-ledger=' + str(self.path), '--max-cost-usd=' + cap,
                          '--budget-policy=study-v2', '--study-id=offline-study-test',
                          '--audit-directory=' + str(self.path.parent / ('audit_' + str(self.audit_counter)))])
        return json.loads(output.getvalue())

    def test_study_identity_is_bound_into_provider_settings(self):
        result = self.invoke()
        identity = result['adapter_settings']['budget_policy_identity']
        self.assertEqual(identity['study_id'], 'offline-study-test')
        self.assertEqual(identity['max_cost_nanousd'], 8_000_000_000)
        self.assertEqual(result['adapter_settings_sha256'], digest(result['adapter_settings']))
        self.assertEqual(self.client.responses.create.call_args.kwargs['max_output_tokens'], 8192)

    def test_budget_rejection_precedes_provider_call(self):
        with self.assertRaisesRegex(RuntimeError, 'BudgetError'):
            self.invoke('0.001')
        self.client.responses.create.assert_not_called()
        self.assertEqual(json.loads(self.path.read_text())['records'], [])

    def test_study_adapter_retains_incomplete_and_refusal_metadata_without_retry(self):
        examples = [
            (response(output=[message('partial body')], status='incomplete', incomplete='max_output_tokens'),
             'incomplete', 'partial body'),
            (response(output=[message(refusal='Cannot provide it.')]), 'refusal', ''),
            (response(output=[message('pending body', status='incomplete')]), 'incomplete', 'pending body')]
        for value, expected, code in examples:
            with self.subTest(expected=expected):
                self.client.responses.create.reset_mock()
                self.client.responses.create.return_value = value
                result = self.invoke()
                self.assertEqual(result['solution_state']['status'], expected)
                self.assertFalse(result['solution_state']['executable'])
                self.assertEqual(result['code'], code)
                self.assertEqual(result['usage']['output_tokens'], 30)
                self.assertEqual(result['budget']['state'], 'settled')
                self.client.responses.create.assert_called_once()

    def test_study_provider_failure_redacts_raw_error_and_keeps_reservation(self):
        error = RuntimeError('Authorization: Bearer fake-private-value; raw response body')
        error.status_code, error.code, error.request_id = 503, 'server_error', 'req_test'
        self.client.responses.create.side_effect = error
        with self.assertRaises(RuntimeError) as caught:
            self.invoke()
        record = json.loads(self.path.read_text())['records'][0]
        self.assertEqual(record['state'], 'uncertain')
        self.assertEqual(record['failure']['code'], 'server_error')
        self.assertEqual(record['charged_nanousd'], record['reserved_nanousd'])
        evidence = str(caught.exception) + self.path.read_text()
        self.assertNotIn('fake-private-value', evidence)
        self.assertNotIn('raw response body', evidence)
        self.assertTrue(caught.exception.__suppress_context__)
        self.client.responses.create.assert_called_once()


if __name__ == '__main__':
    unittest.main()
