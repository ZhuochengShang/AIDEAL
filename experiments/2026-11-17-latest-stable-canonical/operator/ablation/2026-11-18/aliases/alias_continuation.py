"""Study-only continuation of unchanged preview batches after offline revalidation."""
import argparse
from pathlib import Path
import json
import sys


def verify_partition(full, prefix, remaining):
    if (len(full) != len(set(full)) or len(prefix) != len(set(prefix))
            or len(remaining) != len(set(remaining)) or set(prefix) & set(remaining)
            or set(prefix) | set(remaining) != set(full)):
        raise ValueError('Prefix and remaining batches must be a disjoint exact partition of the full API bank')


def verify_alias_names(names, public_names):
    if len(names) != len(set(names)) or set(names) & set(public_names):
        raise ValueError('Full-bank aliases contain duplicate or existing public names')


def modules(release):
    sys.path[:0] = [str(release), str(release / 'vendor/aideal_engine/src')]
    from workflow import ablation, execution, improvement_batches, improvement_suggestions
    return ablation, execution, improvement_batches, improvement_suggestions


def verified_manifest(path, ablation):
    value = ablation.load(path)
    if value['manifest_sha256'] != ablation.digest({k: v for k, v in value.items() if k != 'manifest_sha256'}):
        raise ValueError('Original full-bank manifest changed')
    if not all(ablation.verify_artifact(ref) for ref in value['artifacts']):
        raise ValueError('Original full-bank source/context evidence changed')
    for batch in value['batches']:
        if not ablation.verify_artifact(batch['preview']):
            raise ValueError('Original preview bytes changed')
    return value


def prepare(args, a, e, b, suggestions):
    manifest_path = Path(args.full_manifest).resolve()
    manifest = verified_manifest(manifest_path, a)
    settings = suggestions._model_settings(args.model_config)
    if settings['proposal_scope'] != 'aliases_only':
        raise ValueError('Continuation is restricted to aliases_only')
    full_ids = [api for batch in manifest['batches'] for api in batch['api_ids']]
    if type(args.prefix_batches) is not int or not 0 <= args.prefix_batches <= len(manifest['batches']):
        raise ValueError('prefix_batches must be an integer from zero through the full batch count')
    prefix_batches, remaining = manifest['batches'][:args.prefix_batches], manifest['batches'][args.prefix_batches:]
    prefix_ids = [api for batch in prefix_batches for api in batch['api_ids']]
    remaining_ids = [api for batch in remaining for api in batch['api_ids']]
    verify_partition(full_ids, prefix_ids, remaining_ids)
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    public_names = {row['name'] for row in manifest['api_catalog']}
    receipts = []
    for batch in prefix_batches:
        preview, _, attachment = suggestions._load_preview(batch['preview']['path'])
        attempt = Path(args.recorded_collection) / batch['batch_id'] / 'attempt_001'
        result = a.load(attempt / 'process.json')
        request = a.load(attempt / 'request.json')
        expected = {'system': suggestions.proposal_system_prompt(settings),
                    'prompt': json.dumps(preview['context'], ensure_ascii=False, indent=2),
                    'model': settings['name'], 'temperature': settings['temperature'],
                    'max_output_tokens': settings['max_output_tokens']}
        if request != expected or result.get('status') != 'ok':
            raise ValueError('Recorded model request differs from the exact current generation request')
        if result['payload'].get('solution_state', {}).get('status') != 'complete':
            raise ValueError('Incomplete provider output cannot be imported')
        raw = json.loads(result['payload']['code'])
        normalized = suggestions.validate_suggestions(raw, preview['context'], reserved_names=public_names)
        if {k: v for k, v in normalized.items() if k not in ['notes', 'refactors']} != {
                k: v for k, v in raw.items() if k not in ['notes', 'refactors']}:
            raise ValueError('Functional proposal content changed during metadata normalization')
        destination = output / 'revalidated' / batch['batch_id']
        destination.mkdir(parents=True)
        emitted = suggestions._finish_proposal(preview, attachment, destination, result, None, attempt)
        receipt = {'status': 'schema_revalidated_unvalidated_code', 'batch_id': batch['batch_id'],
                   'api_ids': batch['api_ids'], 'new_model_calls': 0,
                   'source_preview': batch['preview'], 'source_request': a.bind(attempt / 'request.json'),
                   'source_process': a.bind(attempt / 'process.json'),
                   'source_rejection': a.bind(attempt / 'rejected.json') if (attempt / 'rejected.json').exists() else None,
                   'normalizations': [] if 'notes' in raw else [{'field': 'notes', 'operation': 'absent_to_empty_string'}],
                   'validator': a.bind(Path(args.release) / 'workflow/improvement_suggestions.py'),
                   'proposal': a.bind(emitted['proposal']) if emitted.get('proposal') else None,
                   'suggestions': a.bind(destination / 'suggestions.json'),
                   'alias_count': len(normalized['aliases']), 'installed': False}
        e.atomic_json(destination / 'REVALIDATION.json', receipt)
        receipts.append(a.bind(destination / 'REVALIDATION.json'))
    names = [alias['name'] for ref in receipts for alias in a.load(a.load(ref['path'])['suggestions']['path'])['aliases']]
    verify_alias_names(names, public_names)
    continuation = {'kind': 'study_alias_continuation', 'bank': args.bank,
                    'full_manifest': a.bind(manifest_path), 'full_api_ids': full_ids,
                    'prefix_api_ids': prefix_ids, 'remaining_api_ids': remaining_ids,
                    'full_api_count': len(full_ids), 'subset_api_count': len(remaining_ids),
                    'prefix_revalidations': receipts, 'batches': remaining,
                    'source_preview_bytes_unchanged': True, 'new_model_calls_during_preparation': 0,
                    'model_configuration': a.bind(args.model_config), 'release': str(Path(args.release).resolve()),
                    'installed': False, 'full_bank_complete': False}
    continuation['continuation_sha256'] = a.digest(continuation)
    e.atomic_json(output / 'CONTINUATION.json', continuation)
    print(json.dumps({'bank': args.bank, 'full_api_count': len(full_ids),
                      'revalidated_api_count': len(prefix_ids), 'remaining_api_count': len(remaining_ids),
                      'remaining_batches': len(remaining), 'new_model_calls': 0,
                      'continuation': str(output / 'CONTINUATION.json')}))


def run(args, a, e, b, suggestions):
    continuation_path = Path(args.continuation).resolve()
    continuation = a.load(continuation_path)
    if continuation['continuation_sha256'] != a.digest({k: v for k, v in continuation.items() if k != 'continuation_sha256'}):
        raise ValueError('Continuation manifest changed')
    if str(Path(args.release).resolve()) != continuation['release']:
        raise ValueError('Continuation release changed')
    for ref in [continuation['full_manifest'], continuation['model_configuration'], *continuation['prefix_revalidations']]:
        if not a.verify_artifact(ref):
            raise ValueError('Bound continuation input changed')
    full = verified_manifest(continuation['full_manifest']['path'], a)
    if continuation['full_api_ids'] != [api for row in full['batches'] for api in row['api_ids']]:
        raise ValueError('Continuation full-bank identities differ from the original manifest')
    full_batches = {row['batch_id']: row for row in full['batches']}
    if any(full_batches.get(row['batch_id']) != row for row in continuation['batches']):
        raise ValueError('Remaining batches changed from original saved bytes')
    settings = suggestions._model_settings(continuation['model_configuration']['path'])
    b._integer(settings.get('provider_attempt_limit', 1), 'model.provider_attempt_limit', 1, 100)
    if settings.get('artifacts'):
        raise ValueError('This study continuation requires the recorded adapter without extra artifact overrides')
    prefix = []
    for ref in continuation['prefix_revalidations']:
        row = a.load(ref['path'])
        for field in ['source_preview', 'source_request', 'source_process', 'validator', 'suggestions']:
            if not a.verify_artifact(row[field]):
                raise ValueError('Offline revalidation evidence changed')
        if row['proposal'] and not a.verify_artifact(row['proposal']):
            raise ValueError('Revalidated proposal changed')
        if full_batches[row['batch_id']]['api_ids'] != row['api_ids']:
            raise ValueError('Revalidated API identities changed')
        prefix.append(row)
    verify_partition(continuation['full_api_ids'], [api for row in prefix for api in row['api_ids']],
                     [api for row in continuation['batches'] for api in row['api_ids']])
    public_names = {row['name'] for row in full['api_catalog']}
    identity = {'continuation': a.bind(continuation_path), 'model_configuration': continuation['model_configuration'],
                'implementation': b._implementation_bindings(), 'operator': a.bind(__file__),
                'model_command_artifacts': [a.bind(p) for p in settings['command'] if Path(p).is_absolute() and Path(p).is_file()],
                'prompt': a.bind(suggestions.PROMPT)}
    identity_sha = a.digest(identity)
    refs = [identity['continuation'], identity['model_configuration'], identity['operator'], identity['prompt'],
            *identity['implementation'], *identity['model_command_artifacts']]
    output = suggestions.development_destination(full['study'], args.output)
    with e.ownership(output):
        frozen = output / 'identity.json'
        if frozen.exists() and a.load(frozen) != identity:
            raise ValueError('Continuation execution identity changed')
        if not frozen.exists():
            if any(p.name != '.lock' for p in output.iterdir()):
                raise ValueError('Unbound output already contains files')
            e.atomic_json(frozen, identity)
        completed, calls, stopped = [], 0, None
        for batch in continuation['batches']:
            if not all(a.verify_artifact(ref) for ref in refs):
                raise ValueError('Continuation implementation/configuration changed')
            result, used = b._run_batch(batch['preview']['path'], settings, output / batch['batch_id'],
                                        a.digest({'run': identity_sha, 'batch': batch}), refs, public_names)
            calls += used
            if result['status'] in ['attempt_budget_exhausted', 'model_attempt_failed', 'invalid_suggestions']:
                stopped = result
                break
            completed.append({'batch_id': batch['batch_id'], 'api_ids': batch['api_ids'],
                              'completion': a.bind(output / batch['batch_id'] / 'completion.json'),
                              'proposal': a.bind(result['proposal']) if result.get('proposal') else None})
            e.atomic_json(output / 'PROGRESS.json', {'bank': continuation['bank'],
                          'remaining_batches_completed': len(completed), 'remaining_batches_total': len(continuation['batches']),
                          'new_model_calls_this_invocation': calls, 'full_bank_complete': False})
        report = {'status': 'incomplete', 'bank': continuation['bank'], 'continuation': a.bind(continuation_path),
                  'full_api_count': continuation['full_api_count'], 'subset_api_count': continuation['subset_api_count'],
                  'revalidated_batches': continuation['prefix_revalidations'], 'new_batches': completed,
                  'stopped': stopped, 'new_model_calls_this_invocation': calls, 'installed': False,
                  'full_bank_complete': False, 'requires_build_and_behavior_validation': True}
        if stopped is None and len(completed) == len(continuation['batches']):
            verify_partition(continuation['full_api_ids'], [api for row in prefix for api in row['api_ids']],
                             [api for row in completed for api in row['api_ids']])
            proposals = [row['proposal'] for row in prefix + completed if row['proposal']]
            names = [alias['name'] for ref in proposals for alias in a.load(ref['path'])['aliases']]
            verify_alias_names(names, public_names)
            report.update(status='alias_proposals_complete_unvalidated', full_bank_complete=True,
                          alias_count=len(names), proposals=proposals,
                          exact_disjoint_full_bank_coverage=True)
            e.atomic_json(output / 'DEVELOPMENT_COMPLETION.json', report)
        e.atomic_json(output / 'BANK_UNION.json', report)
        print(json.dumps({k: report[k] for k in ['status','bank','full_api_count','subset_api_count','full_bank_complete','new_model_calls_this_invocation']}))
        return 0 if report['full_bank_complete'] else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'run'])
    parser.add_argument('--release', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--full-manifest')
    parser.add_argument('--model-config')
    parser.add_argument('--recorded-collection')
    parser.add_argument('--prefix-batches', type=int)
    parser.add_argument('--bank')
    parser.add_argument('--continuation')
    args = parser.parse_args()
    a, e, b, suggestions = modules(Path(args.release))
    if args.action == 'prepare':
        prepare(args, a, e, b, suggestions)
        return 0
    return run(args, a, e, b, suggestions)


if __name__ == '__main__':
    raise SystemExit(main())
