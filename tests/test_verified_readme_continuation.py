"""Zero-provider continuation guards; prior evidence never becomes a fresh checkpoint."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch
import pytest

PATH = Path(__file__).parent / 'run_verified_readme_continuation.py'
if not PATH.exists():
    PATH = Path(__file__).resolve().parents[1] / 'scripts/run_verified_readme_continuation.py'
spec = importlib.util.spec_from_file_location('continuation', PATH)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def evidence():
    keys = ('project', 'language', 'doc_source', 'doc_scope', 'class_context',
            'manifest_sha256', 'document_sha256', 'original_document_files',
            'source', 'fixtures', 'api_inventory', 'scaffold', 'canonical_requested_targets',
            'prompt_contract', 'owner_overrides', 'execute_config', 'interpreter', 'transport_contract')
    fp = {key: {'test_identity': key} for key in keys}
    fp.update(models={'audience': 'google:test', 'audience_max_output_tokens': 8192})
    old = {'run': {'fingerprint_components': fp}, 'details': {'a': {'status': 'pass'}, 'b': {'status': 'fail'}},
           'metrics': {'a': {'llm_calls': 1, 'input_tokens': 10, 'output_tokens': 2},
                       'b': {'llm_calls': 1, 'input_tokens': 20, 'output_tokens': 4}}}
    replay = {'details': {'a': {'status': 'pass', 'wall_s': 1}, 'b': {'status': 'fail', 'wall_s': 2}},
              'metrics': {'a': {'wall_s': 1}, 'b': {'wall_s': 2}}}
    return old, replay, deepcopy(fp)


def test_only_corrected_saved_pass_is_reused():
    old, replay, fp = evidence()
    reasons = c.reuse_reasons(old, fp, fp['prompt_contract'], 'google:test', [], runtime_verified=True)
    reused, pending = c.choose_rows(old, replay, reasons)
    assert reasons == [] and list(reused) == ['a'] and pending == ['b']
    assert reused['a']['provenance'] == 'reused_verified'
    replay['details']['a']['status'] = 'fail'
    assert c.choose_rows(old, replay, [])[1] == ['a', 'b']


@pytest.mark.parametrize('field', ['source', 'fixtures', 'document_sha256', 'canonical_requested_targets', 'prompt_contract', 'transport_contract'])
def test_changed_input_disallows_saved_pass(field):
    old, replay, fp = evidence()
    fp[field] = 'changed'
    reasons = c.reuse_reasons(old, fp, fp['prompt_contract'], 'google:test', [], runtime_verified=True)
    assert reasons and c.choose_rows(old, replay, reasons)[0] == {}


def test_runtime_or_intended_profile_change_disallows_reuse():
    old, replay, fp = evidence()
    for profile, runtime in [('new profile', []), (fp['prompt_contract'], [{'path': '/new/runtime', 'sha256': 'new'}])]:
        reasons = c.reuse_reasons(old, fp, profile, 'google:test', runtime, runtime_verified=True)
        assert reasons and c.choose_rows(old, replay, reasons)[1] == ['a', 'b']


def test_aggregate_preserves_denominator_and_separates_costs():
    old, replay, _ = evidence()
    fresh = {'run': {'complete': True, 'remaining_api_count': 0},
             'details': {'b': {'code': 'new code'}}, 'metrics': {'b': {'status': 'pass', 'llm_calls': 1, 'input_tokens': 7, 'output_tokens': 3}}}
    condition = {'selected_apis': ['a', 'b'], 'reused_apis': ['a'], 'pending_apis': ['b']}
    result = c.aggregate(old, replay, fresh, condition)
    assert result['passes'] == 2 and result['run']['complete']
    assert result['score_with_infra'] == 1 and not result['paper_fresh_R0_eligible']
    assert result['details']['a']['provenance'] == 'reused_verified'
    assert result['details']['b']['provenance'] == 'fresh_generated'
    assert result['costs']['prior_generation']['input_tokens'] == 30
    assert result['costs']['new_generation']['input_tokens'] == 7
    assert result['costs']['corrected_saved_program_replay']['wall_s'] == 3


def test_all_fresh_changed_protocol_can_report_fresh_r0():
    old, replay, _ = evidence()
    fresh = {'run': {'complete': True, 'remaining_api_count': 0},
             'metrics': {api: {'status': 'pass', 'llm_calls': 1} for api in ('a', 'b')}}
    result = c.aggregate(old, replay, fresh, {'selected_apis': ['a', 'b'], 'reused_apis': [], 'pending_apis': ['a', 'b']})
    assert result['mode'] == 'fresh_corrected_protocol_R0' and result['paper_fresh_R0_eligible']


def test_incomplete_provider_withholds_completion():
    old, replay, _ = evidence()
    fresh = {'run': {'complete': True, 'remaining_api_count': 0},
             'metrics': {'b': {'status': 'fail', 'error_category': 'provider-timeout'}}}
    result = c.aggregate(old, replay, fresh, {'selected_apis': ['a', 'b'], 'reused_apis': ['a'], 'pending_apis': ['b']})
    assert not result['run']['complete'] and result['score_with_infra'] == .5


def test_native_engine_receives_only_pending_subset_no_d2(tmp_path):
    old, replay, _ = evidence()
    old_path, replay_path = tmp_path/'old.json', tmp_path/'replay.json'
    old_path.write_text(json.dumps(old)); replay_path.write_text(json.dumps(replay))
    destination = tmp_path/'new/original'
    destination.mkdir(parents=True)
    condition = {'config': '/unused/config', 'source_result': str(old_path), 'corrected_result': str(replay_path),
                 'selected_apis': ['a', 'b'], 'reused_apis': ['a'], 'pending_apis': ['b']}
    identity = {'bindings': [], 'operator': c.binding(PATH), 'conditions': {'original': condition}, 'scope': 'test'}
    fresh = {'run': {'complete': True, 'remaining_api_count': 0}, 'metrics': {'b': {'status': 'pass', 'llm_calls': 1}}}
    prior_bytes = old_path.read_bytes()
    with patch.object(c, 'prepare', return_value=identity), patch.object(c.common, 'load_config'), \
         patch.object(c.common, 'assert_review_released'), patch.object(c.common, 'comprehension_check', return_value=fresh) as run:
        summary = c.run_condition({'output': str(tmp_path/'new'), 'library': 'synthetic'}, 'original')
    assert summary['status'] == 'complete' and run.call_count == 1
    assert run.call_args.kwargs['manifest'] == str(destination/'inputs/pending_manifest.json')
    assert run.call_args.kwargs['max_fix_rounds'] == 0
    assert old_path.read_bytes() == prior_bytes
    assert json.loads((destination/'fresh_result.json').read_text()) == fresh
    assert 'a' not in json.loads((destination/'fresh_result.json').read_text())['metrics']


def test_output_namespace_cannot_overlap_measured_evidence(tmp_path):
    with pytest.raises(ValueError, match='separate'):
        c.replay.assert_separate(tmp_path/'old', tmp_path/'old/new')


def test_reviewed_bundle_preserves_output_isolation_and_blocks_pending_setup(tmp_path):
    scaffold, fixture, report = (tmp_path/name for name in ('scaffold.py', 'data.txt', 'setup.json'))
    scaffold.write_text('pass'); fixture.write_text('fixture')
    report.write_text(json.dumps({'status': 'pending', 'unresolved_setup': ['missing dependency']}))
    bundle = {'scaffold': c.binding(scaffold), 'sample_data': {'data_path': c.binding(fixture)},
              'support_files': [], 'setup_report': c.binding(report)}
    path = tmp_path/'bundle.json'; path.write_text(json.dumps(bundle))
    value, receipts = c.input_bundle(path)
    assert len(receipts) == 4
    with pytest.raises(ValueError, match='unresolved setup'):
        c.require_bundle_ready(value)
    bundle['sample_data']['output_dir'] = c.binding(fixture)
    path.write_text(json.dumps(bundle))
    with pytest.raises(ValueError, match='writable output'):
        c.input_bundle(path)


def test_no_historical_runtime_proof_means_no_pass_reuse(tmp_path):
    old, replay, fp = evidence()
    reasons = c.reuse_reasons(old, fp, fp['prompt_contract'], 'google:test', [])
    assert 'historical_runtime_not_verified_unchanged' in reasons
    assert c.choose_rows(old, replay, reasons)[0] == {}
    partial = tmp_path/'partial.json'
    partial.write_text(json.dumps({'status': 'partial', 'jdk_version': 'same'}))
    verified, receipts = c.runtime_reuse_proof(partial, [])
    assert not verified and receipts == [c.binding(partial)]


@pytest.mark.parametrize('changed_material', [None, 'source', 'document_sha256', 'fixtures', 'reviewed_bundle', 'reviewed_selection'])
def test_force_fresh_prepares_without_any_replay_files(tmp_path, changed_material):
    from types import SimpleNamespace
    old, _, fp = evidence()
    old['run'].update(complete=True, max_fix_rounds=0)
    if changed_material and changed_material not in ('reviewed_bundle', 'reviewed_selection'):
        fp[changed_material] = 'unreviewed change'
    source = tmp_path/'source'; source.mkdir()
    paths = {}
    for arm in ('original', 'generated'):
        destination = tmp_path/arm
        (destination/'configs').mkdir(parents=True)
        (destination/'inputs').mkdir()
        (destination/'source').symlink_to(source, target_is_directory=True)
        result = destination/'result.json'; result.write_text(json.dumps(old))
        (destination/'launch.json').write_text(json.dumps({'source': str(source)}))
        (destination/'inputs/api_manifest.json').write_text('["a", "b"]')
        for name in ('aideal.yaml', 'generated_readme.yaml'):
            (destination/'configs'/name).write_text('synthetic: true')
        paths[arm] = result
    doc = tmp_path/'generated/README.md'
    doc.write_text('## API Test: `a`\n### Goal\nUse a\n## API Test: `b`\n### Goal\nUse b\n')
    raw = {'files': {}, 'comprehension': {'execute': {}}}
    audience = SimpleNamespace(provider='google', model='test', max_output_tokens=8192)
    def config(path):
        return SimpleNamespace(raw=deepcopy(raw), llm_readme=doc,
                               model_for_role=lambda role: audience)
    def prepare(base, destination, model, sample):
        destination.mkdir(parents=True, exist_ok=True)
        (destination/'launch.json').write_text(json.dumps({'engine': 'same'}))
        return config(destination/'configs/aideal.yaml'), ['a', 'b']
    spec = {'original_result': str(paths['original']), 'generated_result': str(paths['generated']),
            'output': str(tmp_path/'fresh'), 'model': 'test', 'force_fresh': True}
    if changed_material == 'reviewed_selection':
        spec['selection_revision'] = str(make_selection(tmp_path, ['a'], ['b']))
    if changed_material == 'reviewed_bundle':
        scaffold, fixture, report = (tmp_path/name for name in ('reviewed_scaffold.py', 'extra.txt', 'ready.json'))
        scaffold.write_text('pass'); fixture.write_text('new reviewed fixture')
        report.write_text(json.dumps({'status': 'ready', 'unresolved_setup': []}))
        bundle = tmp_path/'bundle.json'
        bundle.write_text(json.dumps({'scaffold': c.binding(scaffold),
            'sample_data': {'extra_path': c.binding(fixture)}, 'support_files': [],
            'setup_report': c.binding(report)}))
        spec['input_bundle'] = str(bundle)
    with patch.object(c.common, 'load_config', side_effect=config), \
         patch.object(c.common.baseline, 'prepare', side_effect=prepare), \
         patch.object(c, 'current_inputs', return_value=fp), \
         patch.object(c, 'prompt_contract', return_value=fp['prompt_contract']), \
         patch.object(c, 'validate_replay', side_effect=AssertionError('must not read replay')):
        if changed_material and changed_material not in ('reviewed_bundle', 'reviewed_selection'):
            with pytest.raises(ValueError, match='Historical base material changed.*' + changed_material):
                c.prepare(spec)
            return
        identity = c.prepare(spec)
    assert identity['force_fresh'] and identity['paper_fresh_R0_eligible']
    for condition in identity['conditions'].values():
        assert condition['corrected_result'] is None and not condition['replay_consumed']
        assert condition['reused_apis'] == []
        assert condition['pending_apis'] == (['a'] if changed_material == 'reviewed_selection' else ['a', 'b'])
        if changed_material == 'reviewed_selection':
            assert condition['historical_count'] == 2
            assert condition['excluded_apis']['b']['status'] == 'excluded_by_selection'
        assert 'explicit_force_fresh_no_replay_consumed' in condition['reuse_blockers']
        if changed_material == 'reviewed_bundle':
            assert 'changed_reviewed_input_bundle' in condition['reuse_blockers']
            raw_config = c.yaml.safe_load(Path(condition['config']).read_text())
            assert raw_config['comprehension']['execute']['sample_data']['extra_path'] == str(fixture)
            assert raw_config['comprehension']['execute']['scaffold'].endswith('reviewed_reviewed_scaffold.py')
    assert not any('replay' in record['path'] for record in identity['bindings'])


def test_force_fresh_aggregate_does_not_invent_replay_results():
    old, _, _ = evidence()
    fresh = {'run': {'complete': True, 'remaining_api_count': 0},
             'metrics': {'a': {'status': 'pass', 'llm_calls': 1}, 'b': {'status': 'fail', 'llm_calls': 1}}}
    result = c.aggregate(old, None, fresh, {'selected_apis': ['a', 'b'], 'reused_apis': [], 'pending_apis': ['a', 'b']})
    assert result['run']['complete'] and result['paper_fresh_R0_eligible']
    assert result['costs']['corrected_saved_program_replay']['status'] == 'not_consumed'
    assert result['costs']['corrected_saved_program_replay']['calls'] == 0
    assert all(row['provenance'] == 'fresh_generated' for row in result['details'].values())



def make_selection(tmp_path, selected, excluded):
    manifest = tmp_path/'selection_manifest.json'
    manifest.write_text(json.dumps(selected))
    source = tmp_path/'private_backend.py'
    source.write_text('def wrapper(x):\n    return backend(x)\n')
    audit = tmp_path/'selection_audit.json'
    audit.write_text(json.dumps({'policy': 'public_owned_nonwrapper', 'excluded': [
        {'api': api, 'reason': 'Private backend forwarding wrapper',
         'source_evidence': [{**c.binding(source), 'line': 1}]} for api in excluded]}))
    revision = tmp_path/'selection_revision.json'
    revision.write_text(json.dumps({'manifest': c.binding(manifest), 'audit': c.binding(audit)}))
    return revision


@pytest.mark.parametrize('selected', [[], ['a', 'new'], ['a', 'b'], ['a', 'a']])
def test_selection_must_be_unique_nonempty_strict_subset(tmp_path, selected):
    revision = make_selection(tmp_path, selected, ['b'])
    with pytest.raises(ValueError, match='nonempty strict subset'):
        c.selection_revision(revision, ['a', 'b'], True)


def test_selection_requires_fresh_run_and_exact_source_backed_audit(tmp_path):
    revision = make_selection(tmp_path, ['a'], ['b'])
    with pytest.raises(ValueError, match='force_fresh'):
        c.selection_revision(revision, ['a', 'b'], False)
    names, excluded, receipts = c.selection_revision(revision, ['a', 'b'], True)
    assert names == ['a'] and excluded['b']['status'] == 'excluded_by_selection'
    c.verify(receipts)
    wrong = make_selection(tmp_path, ['a'], ['not_b'])
    with pytest.raises(ValueError, match='exactly every excluded'):
        c.selection_revision(wrong, ['a', 'b'], True)


def test_selection_denominator_and_excluded_results_remain_distinct():
    old, _, _ = evidence()
    condition = {'selected_apis': ['a'], 'reused_apis': [], 'pending_apis': ['a'], 'historical_count': 2,
                 'excluded_apis': {'b': {'status': 'excluded_by_selection', 'reason': 'private wrapper'}}}
    fresh = {'run': {'complete': True, 'remaining_api_count': 0}, 'metrics': {'a': {'status': 'pass'}}}
    result = c.aggregate(old, None, fresh, condition)
    assert result['selection'] == {'historical_count': 2, 'selected_count': 1, 'excluded_count': 1}
    assert result['score_with_infra'] == 1 and set(result['details']) == {'a'}
    assert result['exclusions']['b']['status'] == 'excluded_by_selection'


def test_runtime_readiness_cannot_be_used_with_wrong_selection(tmp_path):
    revision = make_selection(tmp_path, ['a'], ['b'])
    report = tmp_path/'conditional_setup.json'
    report.write_text(json.dumps({'status': 'ready', 'unresolved_setup': [],
                                  'required_selection_revision': c.binding(revision)}))
    runtime = {'setup_report': c.binding(report)}
    with pytest.raises(ValueError, match='exact reviewed selection'):
        c.verify_required_selection({}, runtime, None)
    c.verify_required_selection({'selection_revision': str(revision)}, runtime, None)
    revision.write_text('{}')
    with pytest.raises(ValueError, match='exact reviewed selection'):
        c.verify_required_selection({'selection_revision': str(revision)}, runtime, None)

@pytest.mark.parametrize('selected, expected', [
    ('original', ['original']), ('generated_d1', ['generated_d1']),
    (None, ['original', 'generated_d1']),
])
def test_run_condition_flag_limits_scheduled_workers(tmp_path, selected, expected):
    """A single-condition request must not silently start another paid arm."""
    from contextlib import nullcontext
    from types import SimpleNamespace
    import sys
    argv = ['continuation', '--spec', str(tmp_path / 'spec.json'), '--run']
    if selected:
        argv.extend(['--condition', selected])
    prepared = {'selected': 1, 'conditions': {
        arm: {'reused_apis': [], 'pending_apis': ['a'], 'reuse_blockers': []}
        for arm in c.ARMS}}
    with patch.object(sys, 'argv', argv), \
         patch.object(c, 'read', return_value={'library': 'synthetic', 'output': str(tmp_path / 'out')}), \
         patch.object(c, 'prepare', return_value=prepared), \
         patch.object(c.common, 'ownership', side_effect=lambda _: nullcontext()), \
         patch.object(c.subprocess, 'run', return_value=SimpleNamespace(returncode=0)) as process:
        assert c.main() == 0
    commands = [call.args[0] for call in process.call_args_list]
    assert [command[command.index('--condition') + 1] for command in commands] == expected

def write_attempt(root, number, *, api='b', status='returned', tokens=(5, 2), provider=True, usage_complete=True):
    folder = root / 'run_b' / f'attempt_{number:04d}'
    folder.mkdir(parents=True)
    (folder / 'request.json').write_text(json.dumps({'api': api, 'round': 0, 'attempt_number': number}))
    if provider:
        (folder / 'provider.json').write_text(json.dumps({'status': status, 'wall_s': 2,
            'category': 'provider-incomplete-output' if status == 'error' else None,
            'usage': {'calls': 1, 'input_tokens': tokens[0], 'output_tokens': tokens[1],
                      'missing_usage_calls': int(not usage_complete), 'usage_complete': usage_complete}}))
    if status == 'returned' and provider:
        (folder / 'execution.json').write_text(json.dumps({'exit_code': 0, 'wall_s': 3}))
    return folder


def test_cumulative_provider_ledger_counts_failed_response_and_resume_once(tmp_path):
    root = tmp_path / 'new' / 'execution'
    write_attempt(root, 1, status='error')
    write_attempt(root, 2, tokens=(7, 3))
    # Historical/replay receipts live elsewhere and cannot enter this ledger.
    write_attempt(tmp_path / 'historical' / 'execution', 1, tokens=(1000, 1000))
    ledger = c.provider_attempt_ledger(root, ['b'], ['b'])
    cost = ledger['totals']
    assert (cost['request_count'], cost['llm_calls'], cost['input_tokens'], cost['output_tokens']) == (2, 2, 12, 5)
    assert cost['usage_complete'] and cost['wall_s'] == 7
    assert all(record['round'] == 0 for record in ledger['attempts'])
    assert ledger == c.provider_attempt_ledger(root, ['b'], ['b'])
    old, replay, _ = evidence()
    fresh = {'run': {'complete': True, 'remaining_api_count': 0},
             'metrics': {'b': {'status': 'pass', 'llm_calls': 1, 'input_tokens': 7, 'output_tokens': 3}}}
    condition = {'selected_apis': ['a', 'b'], 'reused_apis': ['a'], 'pending_apis': ['b']}
    result = c.aggregate(old, replay, fresh, condition, cost)
    assert result['passes'] == 2 and result['score_with_infra'] == 1
    assert result['costs']['new_generation']['llm_calls'] == 2
    assert result['final_target_metric_totals']['llm_calls'] == 1
    assert result['costs']['prior_generation']['llm_calls'] == 2


def test_interrupted_and_unknown_usage_remain_explicit(tmp_path):
    write_attempt(tmp_path, 1, provider=False)
    write_attempt(tmp_path, 2, status='error', usage_complete=False)
    write_attempt(tmp_path, 3)
    cost = c.provider_attempt_ledger(tmp_path, ['b'], ['b'])['totals']
    assert cost['request_count'] == 3 and cost['provider_receipt_count'] == 2
    assert cost['llm_calls'] == 2 and cost['input_tokens'] == 10
    assert cost['missing_usage_attempts'] == 2
    assert not cost['usage_complete'] and not cost['wall_time_complete']


def test_missing_or_foreign_attempt_evidence_cannot_claim_complete_costs(tmp_path):
    cost = c.provider_attempt_ledger(tmp_path, ['b'], ['b'])['totals']
    assert not cost['usage_complete'] and cost['missing_api_receipts'] == ['b']
    write_attempt(tmp_path, 1, api='not_in_this_condition')
    with pytest.raises(ValueError, match='outside this condition'):
        c.provider_attempt_ledger(tmp_path, ['b'])


def test_missing_historical_transport_contract_disallows_reuse():
    old, replay, current = evidence()
    old['run']['fingerprint_components'].pop('transport_contract')
    reasons = c.reuse_reasons(old, current, current['prompt_contract'], 'google:test', [], runtime_verified=True)
    assert 'changed_or_missing_transport_contract' in reasons
    assert c.choose_rows(old, replay, reasons)[0] == {}
