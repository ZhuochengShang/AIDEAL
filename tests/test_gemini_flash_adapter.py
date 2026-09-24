"""Offline contracts; the provider client is always replaced by a mock."""
import contextlib
import hashlib
import io
import json
import unittest
from unittest.mock import MagicMock, patch

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = types = None
from workflow import gemini_flash_adapter as adapter


REQUEST = {'model': 'gemini-3-flash-preview', 'system': 'Return Scala code only.',
           'prompt': 'Implement solve.', 'temperature': 0.0, 'max_output_tokens': 2048}


def response(text='def solve = 1', *, reason='STOP', thoughts=23, visible=7):
    return types.GenerateContentResponse(
        model_version='gemini-3-flash-preview',
        candidates=[types.Candidate(
            content=types.Content(parts=[types.Part(text=text)]), finish_reason=reason)],
        usage_metadata=types.GenerateContentResponseUsageMetadata(
            prompt_token_count=100, candidates_token_count=visible,
            thoughts_token_count=thoughts, cached_content_token_count=10,
            total_token_count=100 + (visible or 0) + (thoughts or 0)))


@unittest.skipIf(genai is None, 'google-genai is an optional provider dependency')
class FlashAdapterTests(unittest.TestCase):
    def invoke(self, argv=(), *, result=None, request=None, error=None, env=None):
        output = io.StringIO()
        client = MagicMock()
        client.__enter__.return_value = client
        client.models.generate_content.return_value = result or response()
        client.models.generate_content.side_effect = error
        with patch.object(genai, 'Client', return_value=client) as constructor, \
                patch.dict('os.environ', env or {'GEMINI_API_KEY': 'test-secret'}, clear=True), \
                patch('sys.stdin', io.StringIO(json.dumps(request or REQUEST))), \
                contextlib.redirect_stdout(output):
            adapter.main(list(argv))
        return json.loads(output.getvalue()), constructor, client

    def test_low_default_transmits_exact_request_and_one_attempt(self):
        record, constructor, client = self.invoke()
        options = constructor.call_args.kwargs['http_options']
        self.assertEqual(options.retry_options.attempts, 1)
        self.assertEqual(options.timeout, 120000)
        self.assertEqual(options.api_version, 'v1beta')
        self.assertEqual(options.base_url, 'https://generativelanguage.googleapis.com')
        self.assertFalse(constructor.call_args.kwargs['vertexai'])
        client.models.generate_content.assert_called_once()
        sent = client.models.generate_content.call_args.kwargs
        self.assertEqual(sent['model'], REQUEST['model'])
        self.assertEqual(sent['contents'], REQUEST['prompt'])
        config = sent['config']
        self.assertEqual(config.system_instruction, REQUEST['system'])
        self.assertEqual(config.temperature, 0.0)
        self.assertEqual(config.max_output_tokens, 2048)
        self.assertEqual(config.candidate_count, 1)
        self.assertEqual(config.thinking_config.thinking_level, types.ThinkingLevel.LOW)
        self.assertFalse(config.thinking_config.include_thoughts)
        self.assertIsNone(config.thinking_config.thinking_budget)
        client.__exit__.assert_called_once()
        self.assertEqual(record['adapter_settings']['thinking_level'], 'low')
        self.assertNotIn('test-secret', json.dumps(record))

    def test_minimal_timeout_and_cap_are_explicit(self):
        record, constructor, client = self.invoke(
            ['--thinking-level', 'minimal', '--timeout-ms', '90000'],
            request={**REQUEST, 'max_output_tokens': 512})
        self.assertEqual(constructor.call_args.kwargs['http_options'].timeout, 90000)
        config = client.models.generate_content.call_args.kwargs['config']
        self.assertEqual(config.thinking_config.thinking_level, types.ThinkingLevel.MINIMAL)
        self.assertEqual(config.max_output_tokens, 512)
        self.assertEqual(record['adapter_settings']['max_output_tokens'], 512)
        self.assertEqual(record['adapter_settings']['thinking_level'], 'minimal')

    def test_usage_breakdown_keeps_legacy_total(self):
        record = adapter.response_record(response())
        self.assertEqual(record['usage'], {
            'input_tokens': 100, 'output_tokens': 30, 'visible_output_tokens': 7,
            'thinking_tokens': 23, 'cached_input_tokens': 10,
            'tool_use_prompt_tokens': None, 'total_tokens': 130})
        self.assertEqual(record['finish_reason'], 'STOP')
        self.assertFalse(record['truncated'])

    def test_empty_reasoning_only_retains_billed_usage(self):
        record = adapter.response_record(response('', reason='MAX_TOKENS', visible=0))
        self.assertEqual(record['code'], '')
        self.assertEqual(record['response_kind'], 'incomplete_model_output')
        self.assertFalse(record['solution_state']['executable'])
        self.assertEqual(record['usage']['output_tokens'], 23)
        self.assertEqual(record['usage']['thinking_tokens'], 23)
        self.assertTrue(record['truncated'])

    def test_truncated_code_is_preserved_without_retry(self):
        record, _, client = self.invoke(result=response('def solve =', reason='MAX_TOKENS'))
        self.assertEqual(record['code'], 'def solve =')
        self.assertEqual(record['response_kind'], 'incomplete_model_output')
        self.assertEqual(record['solution_state']['reason'], 'max_output_tokens')
        self.assertFalse(record['solution_state']['executable'])
        self.assertTrue(record['truncated'])
        client.models.generate_content.assert_called_once()

    def test_blocked_response_records_reason_without_fabricated_usage(self):
        blocked = types.GenerateContentResponse(prompt_feedback=
            types.GenerateContentResponsePromptFeedback(block_reason='SAFETY'))
        record = adapter.response_record(blocked)
        self.assertEqual(record['prompt_block_reason'], 'SAFETY')
        self.assertEqual(record['code'], '')
        self.assertIsNone(record['finish_reason'])
        self.assertFalse(record['truncated'])
        self.assertNotIn('usage', record)
        self.assertEqual(record['solution_state']['status'], 'refusal')
        self.assertFalse(record['solution_state']['executable'])

    def test_unreported_breakdown_remains_unknown(self):
        record = adapter.response_record(response(thoughts=None, visible=None))
        self.assertIsNone(record['usage']['thinking_tokens'])
        self.assertIsNone(record['usage']['visible_output_tokens'])
        self.assertEqual(record['usage']['output_tokens'], 0)  # Existing contract.

    def test_effective_settings_are_reproducibly_hashed(self):
        low, _, _ = self.invoke()
        minimal, _, _ = self.invoke(['--thinking-level', 'minimal'])
        expected = hashlib.sha256(json.dumps(low['adapter_settings'], sort_keys=True,
            separators=(',', ':')).encode()).hexdigest()
        self.assertEqual(low['adapter_settings_sha256'], expected)
        self.assertNotEqual(expected, minimal['adapter_settings_sha256'])
        self.assertEqual(low['adapter_settings']['sdk_version'], genai.__version__)

    def test_provider_exception_propagates_once_and_closes_client(self):
        client = MagicMock()
        client.__enter__.return_value = client
        client.models.generate_content.side_effect = TimeoutError('offline timeout')
        with patch.object(genai, 'Client', return_value=client), \
                patch.dict('os.environ', {'GEMINI_API_KEY': 'test'}, clear=True), \
                patch('sys.stdin', io.StringIO(json.dumps(REQUEST))), \
                self.assertRaisesRegex(TimeoutError, 'offline timeout'):
            adapter.main([])
        client.models.generate_content.assert_called_once()
        client.__exit__.assert_called_once()

    def test_wrong_model_rejected_before_client(self):
        with patch.object(genai, 'Client') as client, \
                patch('sys.stdin', io.StringIO(json.dumps({**REQUEST, 'model': 'another-model'}))), \
                self.assertRaisesRegex(ValueError, 'requires model'):
            adapter.main([])
        client.assert_not_called()

    def test_invalid_caps_rejected_before_client(self):
        for cap in (0, -1, True, 2.5, '2048'):
            with self.subTest(cap=cap), patch.object(genai, 'Client') as client, \
                    patch('sys.stdin', io.StringIO(json.dumps({**REQUEST, 'max_output_tokens': cap}))), \
                    self.assertRaisesRegex(ValueError, 'positive integer'):
                adapter.main([])
            client.assert_not_called()

    def test_invalid_cli_rejected_before_input_or_client(self):
        for argv in (['--thinking-level', 'high'], ['--timeout-ms', '0']):
            with self.subTest(argv=argv), patch.object(genai, 'Client') as client, \
                    contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                adapter.main(argv)
            client.assert_not_called()

    def test_missing_key_rejected_before_client(self):
        with patch.dict('os.environ', {}, clear=True), patch.object(genai, 'Client') as client, \
                patch('sys.stdin', io.StringIO(json.dumps(REQUEST))), \
                self.assertRaisesRegex(RuntimeError, 'GOOGLE_API_KEY or GEMINI_API_KEY'):
            adapter.main([])
        client.assert_not_called()

    def test_google_key_precedence_is_unchanged(self):
        _, constructor, _ = self.invoke(env={'GOOGLE_API_KEY': 'preferred', 'GEMINI_API_KEY': 'other'})
        self.assertEqual(constructor.call_args.kwargs['api_key'], 'preferred')


if __name__ == '__main__':
    unittest.main()
