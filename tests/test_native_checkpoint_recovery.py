"""A resumed provider retry stays at R0 and preserves previous attempt evidence."""
from contextlib import ExitStack, redirect_stderr
import io
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'vendor/aideal_engine/src')]
from aideal import doc_check_execution, doc_check_provenance, llm
from aideal.readme_agent import ApiEntry
import test_doc_check_modules as native_fixtures


@pytest.mark.parametrize('category', [
    'provider-incomplete-output', 'provider-refused-output', 'provider-empty-output',
])
def test_provider_output_retry_keeps_round_and_reuses_finished_api(category):
    fixture = native_fixtures.DocCheckModuleTests()
    fixture.setUp()
    try:
        cfg = fixture.cfg
        cfg.comprehension['execute']['stop_on_provider_error'] = True
        inventory = [ApiEntry(name, 'Return input', '', 'Documentation') for name in ('f', 'g')]
        error = llm.ProviderOutputError(category, 'partial response', {'finish_reason': category})

        def run(responses, resume=False):
            with ExitStack() as stack:
                stack.enter_context(redirect_stderr(io.StringIO()))
                provider = stack.enter_context(patch('aideal.llm.invoke_text', side_effect=responses))
                executor = stack.enter_context(patch('aideal.execution.run_command',
                    return_value=subprocess.CompletedProcess('synthetic', 0, 'DONE', '')))
                stack.enter_context(patch('subprocess.run', side_effect=AssertionError('Unexpected process')))
                stack.enter_context(patch.object(doc_check_execution, 'public_api_details', return_value=[]))
                stack.enter_context(patch.object(doc_check_execution, 'public_api_surface', return_value={'f', 'g'}))
                stack.enter_context(patch('aideal.readme_agent.public_api_details', return_value=[]))
                result = doc_check_execution._comprehension_execute(
                    cfg, inventory, 0, 42, 'original', max_fix_rounds=0, resume=resume)
                return result, provider.call_count, executor.call_count

        first, calls, executions = run(['print("DONE")', error])
        assert (calls, executions) == (2, 1)
        assert not first['run']['complete']
        preserved = {p: p.read_bytes() for p in (fixture.root / 'work').glob('**/attempt_*/*') if p.is_file()}

        # A second refusal/truncation/empty reply stops this explicit invocation.
        # It must not spin in an automatic retry or consume a program repair round.
        repeated, calls, executions = run([error], resume=True)
        assert (calls, executions) == (1, 0)
        assert not repeated['run']['complete']
        assert repeated['run']['resumed_apis'] == 1

        recovered, calls, executions = run(['print("DONE")'], resume=True)
        assert (calls, executions) == (1, 1)
        assert recovered['run']['complete'] and recovered['run']['resumed_apis'] == 1
        assert recovered['metrics']['g']['pass_round'] == 0
        assert recovered['metrics']['g']['status'] == 'pass'
        for path, content in preserved.items():
            assert path.read_bytes() == content
        attempts = sorted((fixture.root / 'work').glob('**/attempt_*/request.json'))
        assert len(attempts) == 4
        assert {json.loads(path.read_text())['round'] for path in attempts} == {0}
        assert {Path(p).name for p in recovered['metrics']['g']['attempt_evidence']} == {'attempt_0003'}

        # An already finished bank does not spend another model call on resume.
        finished, calls, executions = run([], resume=True)
        assert (calls, executions) == (0, 0)
        assert finished['run']['complete'] and finished['run']['resumed_apis'] == 2
    finally:
        fixture.doCleanups()


def test_checkpoint_reuse_requires_same_identity_and_terminal_provider_state():
    reusable = doc_check_provenance._checkpoint_row_reusable
    assert reusable({'experiment_fingerprint': 'x', 'status': 'pass'}, 'x')
    assert reusable({'experiment_fingerprint': 'x', 'status': 'fail', 'error_category': 'compile'}, 'x')
    assert not reusable({'experiment_fingerprint': 'changed', 'status': 'pass'}, 'x')
    assert not reusable({'experiment_fingerprint': 'x', 'error_category': 'llm-error'}, 'x')
    for category in ('provider-incomplete-output', 'provider-refused-output', 'provider-empty-output'):
        assert not reusable({'experiment_fingerprint': 'x', 'status': 'fail', 'error_category': category}, 'x')
