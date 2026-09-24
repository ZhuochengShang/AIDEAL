"""Offline regression cases for completion evidence, independent of provider SDKs."""
from copy import deepcopy
from types import SimpleNamespace as NS
import unittest

from workflow.model_adapter import response_record as gemini_record
from workflow.response_status import classify_record, solution_state


class ResponseStateTests(unittest.TestCase):
    def assert_state(self, record, status, reason=None):
        original = deepcopy(record)
        result = solution_state(record)
        self.assertEqual(result['status'], status)
        self.assertEqual(result['executable'], status == 'complete')
        self.assertEqual(record, original)
        if reason:
            self.assertEqual(result['reason'], reason)
        return result

    def test_legacy_nonempty_remains_compatible_but_marked_unverified(self):
        self.assert_state({'code': 'print(1)'}, 'complete', 'legacy_nonempty_unverified')

    def test_legacy_empty_and_whitespace_are_not_executable(self):
        for code in ('', ' \n\t'):
            self.assert_state({'code': code}, 'empty', 'no_model_code')

    def test_openai_complete(self):
        self.assert_state({'code': 'print(1)', 'response_status': 'completed'},
                          'complete', 'provider_completed')

    def test_partial_and_empty_output_hit_cap_before_empty_classification(self):
        for code in ('print(', ''):
            for metadata in ({'response_status': 'incomplete', 'incomplete_reason': 'max_output_tokens'},
                             {'incomplete_details': {'reason': 'max_output_tokens'}},
                             {'finish_reason': 'MAX_TOKENS'}, {'truncated': True}):
                with self.subTest(code=code, metadata=metadata):
                    self.assert_state({'code': code, **metadata}, 'incomplete', 'max_output_tokens')

    def test_completed_response_does_not_override_nonfinal_selected_message(self):
        for status in ('incomplete', 'in_progress', None):
            self.assert_state({'code': 'print(1)', 'response_status': 'completed', 'messages': [
                {'phase': 'final_answer', 'status': status}]}, 'incomplete')

    def test_final_message_selection_ignores_nonselected_commentary_status(self):
        self.assert_state({'code': 'print(1)', 'response_status': 'completed', 'messages': [
            {'phase': 'commentary', 'status': 'incomplete'},
            {'phase': 'final_answer', 'status': 'completed'}]}, 'complete')

    def test_refusals_and_content_blocks_are_not_code(self):
        for metadata in ({'refusals': ['Declined']}, {'prompt_block_reason': 'SAFETY'},
                         {'finish_reason': 'SAFETY'}, {'incomplete_reason': 'content_filter'}):
            self.assert_state({'code': 'partial', **metadata}, 'refusal')

    def test_terminal_provider_failure_and_pending_response_differ(self):
        for status in ('failed', 'cancelled'):
            self.assert_state({'code': 'print(1)', 'response_status': status}, 'provider_failure')
        for status in ('queued', 'in_progress', 'unknown_status'):
            self.assert_state({'code': 'print(1)', 'response_status': status}, 'incomplete')

    def test_explicit_nonexecutable_kind_never_falls_back_to_legacy(self):
        self.assert_state({'code': 'partial', 'response_kind': 'incomplete_model_output'}, 'incomplete')
        self.assert_state({'code': 'partial', 'response_kind': 'provider_failure'}, 'provider_failure')

    def test_nonstop_gemini_finish_cannot_execute(self):
        for reason in ('FINISH_REASON_UNSPECIFIED', 'OTHER', 'MALFORMED_FUNCTION_CALL',
                       'UNEXPECTED_TOOL_CALL'):
            self.assert_state({'code': 'partial', 'finish_reason': reason}, 'incomplete')

    def test_provider_missing_completion_metadata_is_not_legacy(self):
        self.assert_state({'code': 'print(1)', 'completion_metadata_expected': True},
                          'incomplete', 'missing_completion_metadata')

    def test_preserves_partial_code_and_usage_does_not_trust_cached_state(self):
        record = {'code': 'print(', 'finish_reason': 'MAX_TOKENS',
                  'usage': {'input_tokens': 32, 'output_tokens': 2048},
                  'solution_state': {'status': 'complete', 'executable': True}}
        result = classify_record(record)
        self.assertEqual(result['code'], 'print(')
        self.assertEqual(result['usage']['output_tokens'], 2048)
        self.assertFalse(result['solution_state']['executable'])
        self.assertEqual(result['response_kind'], 'incomplete_model_output')

    def test_classification_recomputes_the_same_specific_reason(self):
        for record in ({'code': 'partial', 'finish_reason': 'SAFETY'},
                       {'code': 'partial', 'messages': [{'phase': None, 'status': 'incomplete'}]}):
            classify_record(record)
            self.assertEqual(solution_state(record), record['solution_state'])

    def test_base_gemini_adapter_retains_finish_reason_for_partial_output(self):
        response = NS(text='print(', model_version='stub',
                      candidates=[NS(finish_reason=NS(value='MAX_TOKENS'), finish_message='limit')],
                      prompt_feedback=None,
                      usage_metadata=NS(prompt_token_count=10, candidates_token_count=20,
                                        thoughts_token_count=100))
        record = gemini_record(response)
        self.assertEqual(record['code'], 'print(')
        self.assertEqual(record['finish_message'], 'limit')
        self.assertEqual(record['usage'], {'input_tokens': 10, 'output_tokens': 120})
        self.assertEqual(record['solution_state']['reason'], 'max_output_tokens')
        self.assertFalse(record['solution_state']['executable'])


if __name__ == '__main__':
    unittest.main()
