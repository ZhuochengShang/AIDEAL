"""Offline evidence contracts: local synthetic subprocesses, never a provider."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from workflow.execution import invoke, atomic_json
from workflow.improvement_suggestions import proposal_response_error
from workflow.task_telemetry import collect_telemetry
from workflow.readme_session import phase
from workflow.native_provider_bridge import NativeBridgeError


class ExecutionTelemetryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_adapter(self, script, timeout=3):
        return invoke([sys.executable, '-c', script], {'system': 's', 'prompt': 'p'},
                      self.root / 'attempt_001', timeout)

    def test_exact_request_logs_timing_and_cache_does_not_spawn(self):
        script = 'import json,sys; r=json.load(sys.stdin); print(json.dumps({"code":r["prompt"]})); print("diagnostic",file=sys.stderr)'
        result = self.run_adapter(script)
        folder = self.root / 'attempt_001'
        self.assertEqual('ok', result['status'])
        self.assertLessEqual(result['started_at'], result['finished_at'])
        self.assertGreaterEqual(result['seconds'], 0)
        self.assertEqual({'system': 's', 'prompt': 'p'}, json.loads((folder / 'request.json').read_text()))
        self.assertEqual('diagnostic\n', (folder / 'stderr.txt').read_text())
        self.assertEqual([sys.executable, '-c', script], json.loads((folder / 'invocation.json').read_text())['command'])
        with patch('workflow.execution.subprocess.Popen', side_effect=AssertionError('must use cache')):
            self.assertEqual(result, self.run_adapter(script))

    def test_nonzero_exit_keeps_stdout_and_error_category(self):
        result = self.run_adapter('import sys; print("partial"); sys.exit(7)')
        self.assertEqual(('adapter_error', 7, 'adapter_nonzero_exit'),
                         (result['status'], result['returncode'], result['error_category']))
        self.assertEqual('partial\n', (self.root / 'attempt_001/stdout.txt').read_text())

    def test_invalid_json_and_nonobject_are_distinct(self):
        for index, (value, category) in enumerate([('not JSON', 'adapter_output_not_json'), ('[]', 'adapter_output_not_object')]):
            result = invoke([sys.executable, '-c', 'print(' + repr(value) + ')'], {}, self.root / str(index), 3)
            self.assertEqual(category, result['error_category'])

    def test_launch_failure_is_saved_without_raw_exception_body(self):
        with patch('workflow.execution.subprocess.Popen', side_effect=FileNotFoundError('private body')):
            result = self.run_adapter('unused')
        self.assertEqual('adapter_launch_or_io_error', result['error_category'])
        self.assertEqual('FileNotFoundError', result['error_type'])
        self.assertNotIn('private body', json.dumps(result))
        self.assertTrue((self.root / 'attempt_001/process.json').is_file())

    def test_timeout_saved_as_unresolved_adapter_status_not_candidate_fail(self):
        result = self.run_adapter('import time; time.sleep(2)', timeout=.05)
        self.assertEqual(('timeout', 'adapter_timeout', None), (result['status'], result['error_category'], result['payload']))

    def test_keyboard_interrupt_preserves_receipt_and_reraises(self):
        process = MagicMock(returncode=-9)
        process.communicate.side_effect = KeyboardInterrupt()
        process.poll.return_value = -9
        with patch('workflow.execution.subprocess.Popen', return_value=process), \
                patch('workflow.execution._stop_process_group', return_value=None), self.assertRaises(KeyboardInterrupt):
            self.run_adapter('unused')
        result = json.loads((self.root / 'attempt_001/process.json').read_text())
        self.assertEqual(('interrupted', 'KeyboardInterrupt'), (result['status'], result['error_type']))


class ProposalCompletionTests(unittest.TestCase):
    def result(self, **extras):
        return {'status': 'ok', 'payload': {'code': '{"aliases": []}', 'response_status': 'completed',
                'budget': {'state': 'settled'}, **extras}}

    def test_codex_complete_settled_required(self):
        self.assertIsNone(proposal_response_error(self.result(), 'gpt-5.3-codex'))
        for extras in ({'response_status': 'incomplete'}, {'truncated': True}, {'incomplete_reason': 'max_output_tokens'},
                       {'response_status': None}, {'budget': {'state': 'uncertain'}}, {'refusals': ['no']}, {'code': ''}):
            with self.subTest(extras=extras):
                self.assertIsNotNone(proposal_response_error(self.result(**extras), 'gpt-5.3-codex'))

    def test_legacy_generic_adapter_without_status_is_compatible_but_explicit_partial_rejected(self):
        self.assertIsNone(proposal_response_error({'status': 'ok', 'payload': {'code': '{}'}}, 'synthetic'))
        self.assertIsNotNone(proposal_response_error(self.result(response_status='incomplete'), 'synthetic'))


class NativePhaseTelemetryTests(unittest.TestCase):
    def test_failed_phase_keeps_timing_and_link_without_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            error = NativeBridgeError('sanitized failure')
            error.call_directory = str(directory / 'call-001')
            callback = MagicMock(side_effect=error)
            request = {'system': 's', 'prompt': 'p'}
            with self.assertRaises(NativeBridgeError):
                phase(directory, 'entry', request, callback, {})
            state = json.loads((directory / 'entry.state.json').read_text())
            self.assertEqual('failed_or_uncertain', state['status'])
            self.assertEqual(error.call_directory, state['provider_call_directory'])
            self.assertGreaterEqual(state['seconds'], 0)
            self.assertLessEqual(state['started_at'], state['finished_at'])
            with self.assertRaisesRegex(ValueError, 'explicit reconciliation'):
                phase(directory, 'entry', request, callback, {})
            callback.assert_called_once()


class TelemetryIndexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def save(self, path, value):
        path = self.root / path
        atomic_json(path, value)
        return path

    def test_retries_fix_rounds_unknown_usage_and_failed_provider_audit_are_distinct(self):
        for number in (1, 2):
            folder = f'runs/alias_only/task--trial-1/round_01/provider_{number:03}'
            self.save(folder + '/request.json', {'system': 's', 'prompt': 'SECRET_PROMPT', 'model': 'm'})
        self.save('runs/alias_only/task--trial-1/round_01/provider_001/process.json',
                  {'status': 'adapter_error', 'seconds': 2, 'payload': None})
        self.save('runs/alias_only/task--trial-1/round_01/provider_001/provider_audit/result.json',
                  {'response_status': 'failed', 'response_id': 'resp_known',
                   'usage': {'input_tokens': 10, 'cached_input_tokens': 3, 'output_tokens': 7,
                             'reasoning_tokens': 5, 'non_reasoning_output_tokens': 2, 'total_tokens': 17}})
        self.save('runs/alias_only/task--trial-1/result.json',
                  {'arm': 'alias_only', 'case_id': 'task', 'trial_id': 'trial-1', 'status': 'provider_pending'})
        result = collect_telemetry(self.root)
        self.assertEqual(2, result['provider_attempts'])
        self.assertEqual([1, 1], [a['fix_round'] for a in result['attempts']])
        self.assertEqual(['code_repair', 'code_repair'], [a['phase'] for a in result['attempts']])
        self.assertEqual({'reported_sum': 5, 'calls_without_value': 1}, result['reported_tokens']['reasoning_tokens'])
        self.assertEqual({'reported_sum': 7, 'calls_without_value': 1}, result['reported_tokens']['output_tokens'])
        self.assertNotIn('SECRET_PROMPT', json.dumps(result))
        self.assertEqual('provider_pending', result['tasks'][0]['status'])

    def test_native_receipt_associates_entry_phase_and_does_not_double_count(self):
        call = self.root / 'development/provider_evidence/dd/call-001'
        self.save('development/session/entry_0000/prepared.json', {'id': 'Owner.method', 'phases': {'deep_dive': {}, 'rewrite': {}}})
        self.save('development/session/entry_0000/deep_dive.state.json',
                  {'status': 'complete', 'provider_evidence': {'call_directory': str(call)}})
        self.save('development/provider_evidence/dd/call-001/request.json',
                  {'system': 's', 'prompt': 'p', 'native_context': {'stage': 'dd'}})
        self.save('development/provider_evidence/dd/call-001/result.json', {'code': 'report',
                  'response_status': 'completed', 'usage': {'input_tokens': 6, 'output_tokens': 4}})
        self.save('development/provider_evidence/dd/call-001/outcome.json', {'status': 'completed', 'seconds': 1})
        result = collect_telemetry(self.root)
        self.assertEqual(1, result['provider_attempts'])
        self.assertEqual('Owner.method', result['attempts'][0]['entry_id'])
        self.assertEqual('deep_dive', result['attempts'][0]['entry_phase'])
        self.assertEqual(['complete', 'not_started'], [t['state_status'] for t in result['tasks']])

    def test_corrupt_partial_receipt_reported_and_private_bank_pruned(self):
        path = self.save('x/provider_001/request.json', {})
        path.write_text('{')
        self.save('bank/provider_001/request.json', {'system': 'hidden', 'prompt': 'answer'})
        result = collect_telemetry(self.root)
        self.assertEqual(1, len(result['scan_errors']))
        self.assertEqual(0, result['provider_attempts'])
        self.assertNotIn('answer', json.dumps(result))

    def test_checker_boolean_categories_do_not_change_verdict(self):
        folder = 'runs/original/task--t1/round_00/execution_001'
        self.save(folder + '/request.json', {'case_id': 'task', 'code': 'x', 'oracle_path': '/private/oracle.json'})
        self.save(folder + '/process.json', {'status': 'ok', 'seconds': 1,
                  'payload': {'execution_pass': True, 'oracle_pass': False, 'target_reached': False}})
        result = collect_telemetry(self.root)
        row = result['attempts'][0]
        self.assertEqual(['oracle_mismatch', 'required_target_not_observed'], row['error_categories'])
        self.assertFalse(row['verdict']['oracle_pass'])
        self.assertNotIn('/private/oracle.json', json.dumps(result))

    def test_diagnostic_tags_keep_evidence_without_claiming_root_cause_or_leaking_text(self):
        folder = 'runs/original/task--t1/round_00/execution_001'
        self.save(folder + '/request.json', {'case_id': 'task', 'code': 'x'})
        self.save(folder + '/process.json', {'status': 'ok', 'payload': {
                  'execution_pass': False, 'oracle_pass': False, 'target_reached': False}})
        log = self.root / folder / 'compile.stderr'
        log.write_text('type mismatch; private_fixture_82467\nnot found: value input\nnot enough arguments\n'
                       'value foo is not a member of Bar\nSyntaxError: unexpected token\n')
        (self.root / folder / 'run.stderr').write_text('Exception in thread main java.lang.IllegalStateException: hidden\n'
                                                     'TimeoutExpired: hidden runtime\n')
        row = collect_telemetry(self.root)['attempts'][0]
        self.assertEqual({'type_mismatch', 'missing_name_or_import', 'wrong_argument_count',
                          'wrong_receiver_or_member', 'syntax_error', 'runtime_exception', 'timeout'},
                         {t['tag'] for t in row['diagnostic_tags']})
        self.assertTrue(all(t['basis'] == 'heuristic_pattern_not_verified_root_cause' and t['line_numbers']
                            for t in row['diagnostic_tags']))
        self.assertNotIn('private_fixture_82467', json.dumps(row))
        self.assertFalse(row['verdict']['execution_pass'])


if __name__ == '__main__':
    unittest.main()
