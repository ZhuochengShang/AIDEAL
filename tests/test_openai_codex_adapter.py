"""Offline adapter contracts; SDK transport is mocked, never contacted."""
import contextlib
import io
import json
from pathlib import Path
from types import SimpleNamespace as NS
import tempfile
import unittest
from unittest.mock import MagicMock, patch

try:
    import openai
    from openai.types.responses import Response
except ImportError:
    openai = Response = None

from workflow import openai_codex_adapter as adapter

REQUEST = {'model': 'gpt-5.3-codex', 'system': 'Return raw Scala only.',
           'prompt': 'Implement solve.', 'max_output_tokens': 2048, 'temperature': 0}


def message(text='', phase=None, refusal=None):
    parts = [{'type': 'output_text', 'text': text, 'annotations': []}] if refusal is None else [
        {'type': 'refusal', 'refusal': refusal}]
    return {'type': 'message', 'id': 'msg_test', 'role': 'assistant', 'status': 'completed',
            'phase': phase, 'content': parts}


def response(*, output=None, usage=True, status='completed', incomplete=None):
    return Response.model_validate({
        'id': 'resp_test', 'created_at': 0, 'model': 'gpt-5.3-codex', 'object': 'response',
        'status': status, 'output': [message('def solve = 1')] if output is None else output,
        'parallel_tool_calls': False, 'tool_choice': 'none', 'tools': [],
        'incomplete_details': {'reason': incomplete} if incomplete else None,
        'usage': {'input_tokens': 100, 'input_tokens_details': {'cached_tokens': 20},
                  'output_tokens': 30, 'output_tokens_details': {'reasoning_tokens': 23},
                  'total_tokens': 130} if usage else None})


@unittest.skipIf(openai is None, 'openai is an optional provider dependency')
class CodexAdapterTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'budget.json'
        self.client = MagicMock()
        self.client.__enter__.return_value = self.client
        self.client.responses.create.return_value = response()

    def invoke(self, *, request=None, limit='5'):
        output = io.StringIO()
        with patch.object(openai, 'OpenAI', return_value=self.client) as constructor, \
                patch.dict('os.environ', {'OPENAI_API_KEY': 'test-private-key'}, clear=True), \
                patch('sys.stdin', io.StringIO(json.dumps(request or REQUEST))), \
                contextlib.redirect_stdout(output):
            adapter.main(['--budget-ledger=' + str(self.path), '--max-cost-usd=' + limit])
        return json.loads(output.getvalue()), constructor

    def read(self):
        return json.loads(self.path.read_text())

    def test_exact_sdk_request_omits_temperature_and_disables_tools_retries_storage(self):
        result, constructor = self.invoke()
        constructor.assert_called_once_with(api_key='test-private-key', base_url='https://api.openai.com/v1',
                                            max_retries=0, timeout=120.0)
        self.client.responses.create.assert_called_once_with(
            model=REQUEST['model'], instructions=REQUEST['system'], input=REQUEST['prompt'],
            reasoning={'effort': 'low'}, max_output_tokens=2048, store=False, tools=[], tool_choice='none',
            service_tier='default', background=False, stream=False, truncation='disabled')
        settings = result['adapter_settings']
        self.assertEqual(settings['requested_temperature'], 0)
        self.assertFalse(settings['temperature_sent'])
        self.assertEqual(settings['effective_temperature'], 'provider_default_not_explicitly_set')
        self.assertEqual(result['adapter_settings_sha256'], adapter.digest(settings))
        self.assertEqual(result['request_sha256'], adapter.digest(REQUEST))
        self.assertNotIn('test-private-key', json.dumps(result) + self.path.read_text())
        self.assertNotIn(REQUEST['prompt'], self.path.read_text())
        self.assertEqual(self.read()['records'][0]['settings_sha256'], result['adapter_settings_sha256'])

    def test_usage_output_already_includes_reasoning(self):
        result, _ = self.invoke()
        self.assertEqual(result['usage'], {'input_tokens': 100, 'output_tokens': 30,
            'reasoning_tokens': 23, 'non_reasoning_output_tokens': 7, 'cached_input_tokens': 20, 'total_tokens': 130})
        self.assertEqual(result['budget']['charged_nanousd'], 80 * 1750 + 20 * 175 + 30 * 14000)
        self.assertEqual(result['model_version'], 'gpt-5.3-codex')
        self.assertEqual(result['response_id'], 'resp_test')

    def test_final_answer_excludes_commentary_and_preserves_message_metadata(self):
        self.client.responses.create.return_value = response(output=[
            message('I will examine the contract.', 'commentary'), message('def solve = 2', 'final_answer')])
        result, _ = self.invoke()
        self.assertEqual(result['code'], 'def solve = 2')
        self.assertEqual([m['phase'] for m in result['messages']], ['commentary', 'final_answer'])
        self.assertEqual(result['messages'][0]['text'], 'I will examine the contract.')

    def test_unphased_text_remains_compatible(self):
        result, _ = self.invoke()
        self.assertEqual(result['code'], 'def solve = 1')
        self.assertEqual(result['response_kind'], 'solution')

    def test_commentary_only_is_not_executable_code(self):
        self.client.responses.create.return_value = response(output=[message('I will solve it.', 'commentary')])
        result, _ = self.invoke()
        self.assertEqual(result['code'], '')
        self.assertEqual(result['response_kind'], 'empty_model_output')

    def test_empty_response_keeps_usage_and_settles(self):
        self.client.responses.create.return_value = response(output=[])
        result, _ = self.invoke()
        self.assertEqual(result['code'], '')
        self.assertEqual(result['usage']['output_tokens'], 30)
        self.assertEqual(result['budget']['state'], 'settled')

    def test_refusal_is_not_code(self):
        self.client.responses.create.return_value = response(output=[message(refusal='Cannot provide that.')])
        result, _ = self.invoke()
        self.assertEqual(result['code'], '')
        self.assertEqual(result['response_kind'], 'refusal')
        self.assertEqual(result['refusals'], ['Cannot provide that.'])

    def test_incomplete_preserves_partial_code_and_no_retry(self):
        self.client.responses.create.return_value = response(output=[message('def solve =')],
            status='incomplete', incomplete='max_output_tokens')
        result, _ = self.invoke()
        self.assertTrue(result['truncated'])
        self.assertEqual(result['incomplete_reason'], 'max_output_tokens')
        self.assertEqual(result['code'], 'def solve =')
        self.assertEqual(result['budget']['state'], 'settled')
        self.client.responses.create.assert_called_once()

    def test_missing_usage_keeps_entire_reservation(self):
        self.client.responses.create.return_value = response(usage=False)
        result, _ = self.invoke()
        self.assertNotIn('usage', result)
        self.assertEqual(result['budget']['state'], 'uncertain')
        self.assertEqual(result['budget']['reserved_nanousd'], result['budget']['charged_nanousd'])

    def test_failed_cancelled_and_pending_statuses_are_provider_failures(self):
        for status in ('failed', 'cancelled', 'queued', 'in_progress'):
            with self.subTest(status=status):
                self.client.responses.create.return_value = response(status=status)
                with self.assertRaisesRegex(RuntimeError, 'non-solution status'):
                    self.invoke()
                row = self.read()['records'][-1]
                self.assertEqual(row['response_status'], status)
                self.assertEqual(row['state'], 'settled' if status in ('failed', 'cancelled') else 'uncertain')

    def test_error_during_ledger_failure_recording_does_not_leak_original_sdk_error(self):
        self.client.responses.create.side_effect = TimeoutError('test-private-key in raw body')
        with patch.object(adapter.BudgetLedger, 'finish', side_effect=OSError('private ledger error')):
            with self.assertRaises(RuntimeError) as caught:
                self.invoke()
        self.assertNotIn('test-private-key', str(caught.exception))
        self.assertNotIn('private ledger error', str(caught.exception))
        self.assertTrue(caught.exception.__suppress_context__)
        self.assertEqual(self.read()['records'][0]['state'], 'reserved')

    def test_provider_timeout_is_sanitized_and_reservation_retained(self):
        self.client.responses.create.side_effect = TimeoutError('Authorization: Bearer test-private-key')
        with self.assertRaises(RuntimeError) as caught:
            self.invoke()
        self.assertNotIn('test-private-key', str(caught.exception))
        self.assertIn('TimeoutError', str(caught.exception))
        self.assertTrue(caught.exception.__suppress_context__)
        row = self.read()['records'][0]
        self.assertEqual(row['state'], 'uncertain')
        self.assertEqual(row['reserved_nanousd'], row['charged_nanousd'])
        self.assertNotIn('test-private-key', self.path.read_text())
        self.client.responses.create.assert_called_once()

    def test_5xx_records_only_sanitized_type_status_code_and_request_id(self):
        error = RuntimeError('secret SDK body')
        error.status_code, error.code, error.request_id = 503, 'server_error', 'req_abc123'
        self.client.responses.create.side_effect = error
        with self.assertRaises(RuntimeError):
            self.invoke()
        failure = self.read()['records'][0]['failure']
        self.assertEqual(failure, {'type': 'RuntimeError', 'status_code': 503,
                                  'code': 'server_error', 'request_id': 'req_abc123'})
        self.assertNotIn('secret SDK body', self.path.read_text())

    def test_budget_blocks_provider_and_equal_form_parses(self):
        with self.assertRaisesRegex(RuntimeError, 'BudgetError'):
            self.invoke(limit='0.001')
        self.client.responses.create.assert_not_called()
        self.assertEqual(self.read()['records'], [])

    def test_requested_output_cap_is_unchanged_and_request_hash_changes(self):
        result, _ = self.invoke(request={**REQUEST, 'max_output_tokens': 4096})
        self.assertEqual(self.client.responses.create.call_args.kwargs['max_output_tokens'], 4096)
        self.assertEqual(result['adapter_settings']['parameters']['max_output_tokens'], 4096)
        self.assertNotEqual(result['request_sha256'], adapter.digest(REQUEST))

    def test_wrong_model_is_rejected_without_sdk_client(self):
        with patch.object(openai, 'OpenAI') as constructor, \
                patch('sys.stdin', io.StringIO(json.dumps({**REQUEST, 'model': 'gpt-other'}))), \
                self.assertRaisesRegex(ValueError, 'requires model'):
            adapter.main(['--budget-ledger=' + str(self.path)])
        constructor.assert_not_called()

    def test_no_key_creates_no_ledger(self):
        with patch.dict('os.environ', {}, clear=True), patch('sys.stdin', io.StringIO(json.dumps(REQUEST))), \
                self.assertRaisesRegex(RuntimeError, 'OPENAI_API_KEY'):
            adapter.main(['--budget-ledger=' + str(self.path)])
        self.assertFalse(self.path.exists())

    def test_tool_output_and_hidden_reasoning_are_never_executed_or_exposed(self):
        result = response(output=[])
        result.output = [NS(type='reasoning', summary=['private reasoning']),
                         NS(type='function_call', name='dangerous', arguments='{}')]
        self.client.responses.create.return_value = result
        record, _ = self.invoke()
        self.assertEqual(record['code'], '')
        self.assertNotIn('private reasoning', json.dumps(record))
        self.client.responses.create.assert_called_once()


if __name__ == '__main__':
    unittest.main()
