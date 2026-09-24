"""Offline transport mocks and durable native prompt/budget contract checks."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'vendor/aideal_engine/src'))
from aideal.config import ModelSpec, load_config
from aideal import llm
from workflow import native_provider_bridge as bridge
from workflow.provider_budget import BudgetError, BudgetLedger, digest
import test_openai_codex_adapter as fixtures


class StudyBudgetPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'budget.json'

    def reserve(self, ledger):
        return ledger.reserve('s', 'p', 100, digest('r'), digest('s'))

    def test_schema_one_identity_remains_exact_and_cannot_upgrade(self):
        ledger = BudgetLedger(self.path)
        self.assertEqual(set(ledger.identity), {'schema_version', 'model', 'max_cost_nanousd',
                                              'prices_nanousd_per_token', 'framing_tokens'})
        self.assertEqual(ledger.identity['schema_version'], 1)
        self.reserve(ledger)
        old = self.path.read_bytes()
        with self.assertRaisesRegex(BudgetError, 'schema changed'):
            self.reserve(BudgetLedger(self.path, '100', policy='study-v2', study_id='new-study'))
        self.assertEqual(self.path.read_bytes(), old)

    def test_new_policy_accepts_100_but_identity_and_cap_are_immutable(self):
        self.reserve(BudgetLedger(self.path, '100', policy='study-v2', study_id='study-one'))
        old = self.path.read_bytes()
        for kwargs in ({'max_cost_usd': '99', 'policy': 'study-v2', 'study_id': 'study-one'},
                       {'max_cost_usd': '100', 'policy': 'study-v2', 'study_id': 'study-two'},
                       {'max_cost_usd': '5'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(BudgetError):
                self.reserve(BudgetLedger(self.path, **kwargs))
            self.assertEqual(self.path.read_bytes(), old)

    def test_explicit_policy_required_and_invalid_limits_rejected(self):
        for cap, options in [('100', {}), ('100.0001', {'policy': 'study-v2', 'study_id': 'x'}),
                             ('100', {'policy': 'study-v2'}), ('5', {'policy': 'legacy-v1', 'study_id': 'x'})]:
            with self.subTest(cap=cap, options=options), self.assertRaises(BudgetError):
                BudgetLedger(self.path, cap, **options)
        self.assertFalse(self.path.exists())


@unittest.skipIf(fixtures.openai is None, 'openai is an optional provider dependency')
class NativeBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.spec = ModelSpec(provider=bridge.PROVIDER, model='gpt-5.3-codex', bridge={
            'policy': 'study-v2', 'study_id': 'rdpro-offline-test', 'stage': 'readme-author',
            'budget_ledger': str(self.root / 'ledger.json'), 'max_cost_usd': '100', 'max_output_tokens': 2048,
            'evidence_dir': str(self.root / 'author_evidence'), 'controller_sha256': bridge.active_controller_hashes()})
        self.client = MagicMock()
        self.client.__enter__.return_value = self.client
        self.client.responses.create.return_value = fixtures.response(output=[fixtures.message('Exact returned text.\n')])
        llm.reset_usage()

    def invoke(self, system='System Ω\nexact', user='User input\n\twith spaces'):
        with patch.object(fixtures.openai, 'OpenAI', return_value=self.client), \
                patch.dict('os.environ', {'OPENAI_API_KEY': 'offline-test-secret'}, clear=True), \
                patch.object(llm, 'get_chat_model', side_effect=AssertionError('Direct provider fallback')):
            return llm.invoke_text(self.spec, system, user)

    def call_dir(self):
        return next((self.root / 'author_evidence').glob('call-*'))

    def ledger(self):
        return json.loads((self.root / 'ledger.json').read_text())

    def test_settings_and_reservation_persist_before_http_and_exact_prompts_return(self):
        response = self.client.responses.create.return_value
        def transport(**kwargs):
            call = self.call_dir()
            self.assertTrue((call / 'settings.json').exists())
            self.assertTrue((call / 'reservation.json').exists())
            self.assertEqual(self.ledger()['records'][0]['state'], 'reserved')
            request = json.loads((call / 'request.json').read_text())
            self.assertEqual(request['system'], kwargs['instructions'])
            self.assertEqual(request['prompt'], kwargs['input'])
            return response
        self.client.responses.create.side_effect = transport
        self.assertEqual(self.invoke(), 'Exact returned text.\n')
        call = self.call_dir()
        result = json.loads((call / 'result.json').read_text())
        request = json.loads((call / 'request.json').read_text())
        self.assertEqual(result['request_sha256'], digest(request))
        self.assertEqual(result['adapter_settings_sha256'], digest(json.loads((call / 'settings.json').read_text())))
        self.assertEqual(result['usage']['reasoning_tokens'], 23)
        self.assertEqual(result['usage']['cached_input_tokens'], 20)
        self.assertEqual(llm.usage_snapshot()['output_tokens'], 30)
        self.assertEqual(llm.usage_snapshot()['calls'], 1)
        self.assertNotIn('offline-test-secret', ''.join(p.read_text() for p in call.iterdir()))

    def test_budget_exhaustion_never_calls_transport(self):
        self.spec.bridge['max_cost_usd'] = '0.001'
        with self.assertRaises(bridge.NativeBridgeError):
            self.invoke()
        self.client.responses.create.assert_not_called()
        self.assertEqual(self.ledger()['records'], [])
        self.assertEqual(json.loads((self.call_dir() / 'outcome.json').read_text())['status'], 'failed_closed')

    def test_uncertain_transport_retains_charge_and_exact_request(self):
        self.client.responses.create.side_effect = TimeoutError('offline-test-secret raw error')
        with self.assertRaises(bridge.NativeBridgeError) as caught:
            self.invoke()
        self.assertNotIn('offline-test-secret', str(caught.exception))
        row = self.ledger()['records'][0]
        self.assertEqual(row['state'], 'uncertain')
        self.assertEqual(row['charged_nanousd'], row['reserved_nanousd'])
        self.assertTrue((self.call_dir() / 'request.json').exists())
        self.assertTrue((self.call_dir() / 'failure.json').exists())

    def test_incomplete_response_is_saved_but_never_returned_or_retried(self):
        self.client.responses.create.return_value = fixtures.response(status='incomplete', incomplete='max_output_tokens')
        with self.assertRaises(bridge.NativeBridgeError):
            self.invoke()
        self.client.responses.create.assert_called_once()
        record = json.loads((self.call_dir() / 'result.json').read_text())
        self.assertTrue(record['truncated'])
        self.assertEqual(record['budget']['state'], 'settled')
        self.assertEqual(llm.usage_snapshot()['calls'], 0)

    def test_missing_usage_is_saved_but_native_text_rejected(self):
        self.client.responses.create.return_value = fixtures.response(usage=False)
        with self.assertRaises(bridge.NativeBridgeError):
            self.invoke()
        self.assertEqual(self.ledger()['records'][0]['state'], 'uncertain')
        self.assertTrue((self.call_dir() / 'result.json').exists())

    def test_changed_contract_or_implementation_fails_before_provider(self):
        self.spec.bridge['controller_sha256']['workflow/provider_budget.py'] = '0' * 64
        with self.assertRaisesRegex(bridge.NativeBridgeError, 'implementation differs'):
            self.invoke()
        self.client.responses.create.assert_not_called()
        self.assertFalse((self.root / 'author_evidence').exists())

    def test_evidence_directory_contract_cannot_change(self):
        self.invoke()
        self.client.responses.create.reset_mock()
        self.spec.bridge['max_output_tokens'] = 4096
        with self.assertRaisesRegex(bridge.NativeBridgeError, 'different immutable contract'):
            self.invoke()
        self.client.responses.create.assert_not_called()
        self.assertEqual(len(self.ledger()['records']), 1)

    def test_bridge_configuration_cannot_fall_back_to_direct_provider(self):
        self.spec.provider = 'openai-responses'
        with self.assertRaisesRegex(ValueError, 'cannot use a direct provider'):
            self.invoke()
        self.client.responses.create.assert_not_called()

    def test_contract_is_read_only_and_config_loader_preserves_bridge(self):
        config = self.root / 'configs/aideal.yaml'
        config.parent.mkdir()
        import yaml
        config.write_text(yaml.safe_dump({'models': {'registry': {'guard': {
            'provider': self.spec.provider, 'model': self.spec.model, 'bridge': self.spec.bridge}},
            'roles': {'author': 'guard'}}}))
        loaded = load_config(config).model_for_role('author')
        self.assertEqual(bridge.guarded_native_contract(loaded), bridge.guarded_native_contract(self.spec))
        self.assertFalse((self.root / 'ledger.json').exists())
        self.assertFalse((self.root / 'author_evidence').exists())


if __name__ == '__main__':
    unittest.main()
