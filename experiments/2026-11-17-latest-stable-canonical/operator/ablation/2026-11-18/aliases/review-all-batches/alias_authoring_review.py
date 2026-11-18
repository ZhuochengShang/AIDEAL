"""Review every selected API batch; reject invalid proposals without installing them."""
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


def complete_model_response(process):
    return (process.get('status') == 'ok'
            and isinstance(process.get('payload'), dict)
            and isinstance(process['payload'].get('code'), str)
            and process['payload'].get('solution_state', {}).get('status') == 'complete')


def review_response(process, context, public_names, accepted_names, validate):
    """Only complete provider output can be accepted or rejected as a reviewed batch."""
    if not complete_model_response(process):
        return {'status': 'provider_or_incomplete_pause', 'accepted': False, 'exposure_reviewed': False}, None
    try:
        raw = json.loads(process['payload']['code'])
        normalized = validate(raw, context, reserved_names=set(public_names) | set(accepted_names))
        if normalized['hints'] or normalized.get('refactors'):
            raise ValueError('This authoring queue admits alias candidates only')
        names = [row['name'] for row in normalized['aliases']]
        verify_alias_names(names, set(public_names) | set(accepted_names))
        if {k: v for k, v in normalized.items() if k not in ['notes', 'refactors']} != {
                k: v for k, v in raw.items() if k not in ['notes', 'refactors']}:
            raise ValueError('Revalidation changed functional proposal content')
        return {'status': 'accepted_candidate_unvalidated', 'accepted': True, 'exposure_reviewed': True,
                'alias_names': names, 'normalizations': [] if 'notes' in raw else [
                    {'field': 'notes', 'operation': 'absent_to_empty_string'}]}, normalized
    except (ValueError, TypeError, SyntaxError) as exc:
        return {'status': 'rejected_candidate', 'accepted': False, 'exposure_reviewed': True,
                'reason': str(exc), 'alias_names': []}, None


def accepted_proposals(rows):
    """Candidate source from a rejected response never enters the installation list."""
    return [row['proposal'] for row in rows if row['accepted'] and row.get('proposal')]


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
    recorded = a.load(args.recorded_attempts)
    attempts = recorded['attempts']
    count = len(attempts)
    if count > len(manifest['batches']) or [r['batch_id'] for r in attempts] != [r['batch_id'] for r in manifest['batches'][:count]]:
        raise ValueError('Recorded attempts must cover one exact contiguous prefix in original batch order')
    if not a.verify_artifact(recorded['full_manifest']) or recorded['full_manifest'] != a.bind(manifest_path):
        raise ValueError('Recorded-attempt map binds a different full manifest')
    prefix_batches, remaining = manifest['batches'][:count], manifest['batches'][count:]
    prefix_ids = [api for batch in prefix_batches for api in batch['api_ids']]
    remaining_ids = [api for batch in remaining for api in batch['api_ids']]
    verify_partition(full_ids, prefix_ids, remaining_ids)
    output = suggestions.development_destination(manifest['study'], args.output)
    output.mkdir(parents=True, exist_ok=False)
    public_names = {row['name'] for row in manifest['api_catalog']}
    receipts, accepted_names = [], set()
    for batch, recorded_attempt in zip(prefix_batches, attempts):
        preview, _, attachment = suggestions._load_preview(batch['preview']['path'])
        attempt = Path(recorded_attempt['attempt'])
        if not all(a.verify_artifact(recorded_attempt[field]) for field in ['request', 'process']):
            raise ValueError('Mapped recorded request/process changed')
        if recorded_attempt['request'] != a.bind(attempt / 'request.json') or recorded_attempt['process'] != a.bind(attempt / 'process.json'):
            raise ValueError('Mapped recorded-attempt paths differ from their bindings')
        result = a.load(attempt / 'process.json')
        request = a.load(attempt / 'request.json')
        expected = {'system': suggestions.proposal_system_prompt(settings),
                    'prompt': json.dumps(preview['context'], ensure_ascii=False, indent=2),
                    'model': settings['name'], 'temperature': settings['temperature'],
                    'max_output_tokens': settings['max_output_tokens']}
        if request != expected or result.get('status') != 'ok':
            raise ValueError('Recorded model request differs from the exact current generation request')
        if not complete_model_response(result):
            raise ValueError('Incomplete provider output cannot be imported')
        decision, normalized = review_response(result, preview['context'], public_names,
                                                accepted_names, suggestions.validate_suggestions)
        destination = output / 'revalidated' / batch['batch_id']
        destination.mkdir(parents=True)
        emitted = suggestions._finish_proposal(preview, attachment, destination, result, None, attempt) if decision['accepted'] else {}
        child_artifacts = []
        if emitted.get('proposal'):
            child_artifacts = list(a.load(emitted['proposal'])['artifacts'].values())
        receipt = {**decision, 'batch_id': batch['batch_id'],
                   'api_ids': batch['api_ids'], 'new_model_calls': 0,
                   'source_preview': batch['preview'], 'source_request': a.bind(attempt / 'request.json'),
                   'source_process': a.bind(attempt / 'process.json'),
                   'source_rejection': a.bind(attempt / 'rejected.json') if (attempt / 'rejected.json').exists() else None,
                   'validator': a.bind(Path(args.release) / 'workflow/improvement_suggestions.py'),
                   'proposal': a.bind(emitted['proposal']) if emitted.get('proposal') else None,
                   'suggestions': a.bind(destination / 'suggestions.json') if decision['accepted'] else None,
                   'accepted_artifacts': child_artifacts,
                   'alias_count': len(normalized['aliases']) if decision['accepted'] else 0,
                   'prior_alias_names_sha256': a.digest(sorted(accepted_names)), 'installed': False}
        accepted_names.update(decision.get('alias_names', []))
        e.atomic_json(destination / 'REVALIDATION.json', receipt)
        receipts.append(a.bind(destination / 'REVALIDATION.json'))
    verify_alias_names(list(accepted_names), public_names)
    continuation = {'kind': 'study_alias_authoring_review', 'bank': args.bank,
                    'full_manifest': a.bind(manifest_path), 'full_api_ids': full_ids,
                    'prefix_api_ids': prefix_ids, 'remaining_api_ids': remaining_ids,
                    'full_api_count': len(full_ids), 'subset_api_count': len(remaining_ids),
                    'prefix_revalidations': receipts, 'batches': remaining, 'recorded_attempt_map': a.bind(args.recorded_attempts),
                    'source_preview_bytes_unchanged': True, 'new_model_calls_during_preparation': 0,
                    'model_configuration': a.bind(args.model_config), 'release': str(Path(args.release).resolve()),
                    'installed': False, 'full_api_exposure_complete': False,
                    'rejection_policy': 'Record complete rejected candidates and continue; provider/incomplete output pauses.'}
    continuation['continuation_sha256'] = a.digest(continuation)
    e.atomic_json(output / 'CONTINUATION.json', continuation)
    prefix_rows = [a.load(ref['path']) for ref in receipts]
    e.atomic_json(output / 'ACCEPTED_CANDIDATES.json', {
        'bank': args.bank, 'status': 'schema_valid_candidates_runtime_validation_pending',
        'accepted_proposals': accepted_proposals(prefix_rows),
        'reviewed_api_count': len(prefix_ids), 'full_api_count': len(full_ids),
        'rejected_batches': sum(not row['accepted'] for row in prefix_rows),
        'full_api_exposure_complete': False, 'installed': False})
    print(json.dumps({'bank': args.bank, 'full_api_count': len(full_ids),
                      'revalidated_api_count': len(prefix_ids), 'remaining_api_count': len(remaining_ids),
                      'remaining_batches': len(remaining), 'new_model_calls': 0,
                      'continuation': str(output / 'CONTINUATION.json')}))


def verify_review(row, a, accepted_names):
    fields = ['source_preview', 'source_request', 'source_process', 'validator',
              'source_rejection', 'suggestions', 'proposal']
    refs = [row[field] for field in fields if row.get(field)] + row.get('accepted_artifacts', [])
    if not all(a.verify_artifact(ref) for ref in refs):
        raise ValueError('Reviewed source, response, or candidate artifacts changed')
    if row['prior_alias_names_sha256'] != a.digest(sorted(accepted_names)):
        raise ValueError('Earlier accepted aliases changed')
    if not row['exposure_reviewed'] or not complete_model_response(a.load(row['source_process']['path'])):
        raise ValueError('Reviewed batch has no complete model response')
    if not row['accepted'] and (row.get('proposal') or row.get('alias_names')):
        raise ValueError('Rejected candidate cannot supply accepted aliases')
    accepted_names.update(row.get('alias_names', []))


def recorded_complete_attempt(folder, load):
    # Recover a response after interruption without calling the provider again.
    for attempt in sorted(folder.glob('attempt_[0-9][0-9][0-9]')):
        if (attempt / 'process.json').is_file() and complete_model_response(load(attempt / 'process.json')):
            return attempt
    return None


def run(args, a, e, b, suggestions):
    continuation_path = Path(args.continuation).resolve()
    continuation = a.load(continuation_path)
    if continuation['continuation_sha256'] != a.digest({k: v for k, v in continuation.items() if k != 'continuation_sha256'}):
        raise ValueError('Continuation manifest changed')
    if str(Path(args.release).resolve()) != continuation['release']:
        raise ValueError('Continuation release changed')
    for ref in [continuation['full_manifest'], continuation['model_configuration'],
                continuation['recorded_attempt_map'], *continuation['prefix_revalidations']]:
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
    prefix, accepted_names = [], set()
    for ref in continuation['prefix_revalidations']:
        row = a.load(ref['path'])
        verify_review(row, a, accepted_names)
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
        reviewed, calls, stopped = [], 0, None
        for batch in continuation['batches']:
            if not all(a.verify_artifact(ref) for ref in refs):
                raise ValueError('Continuation implementation/configuration changed')
            folder = output / batch['batch_id']
            if folder.is_symlink() or folder.resolve().parent != output:
                raise ValueError('Batch output must be an ordinary child of the owned output')
            review_path = folder / 'REVIEW.json'
            batch_identity = a.digest({'run': identity_sha, 'batch': batch})
            if review_path.exists():
                row = a.load(review_path)
                if (row['identity'] != batch_identity or row['review_sha256'] != a.digest({
                        k: v for k, v in row.items() if k != 'review_sha256'})):
                    raise ValueError('Saved review receipt changed')
                verify_review(row, a, accepted_names)
                reviewed.append(row)
                continue
            preview, _, attachment = suggestions._load_preview(batch['preview']['path'])
            attempt = recorded_complete_attempt(folder, a.load)
            result = None
            if attempt is None:
                result, used = b._run_batch(batch['preview']['path'], settings, folder,
                                            batch_identity, refs, public_names | accepted_names)
                calls += used
                attempt = recorded_complete_attempt(folder, a.load)
            if attempt is None:
                stopped = {'status': 'provider_or_incomplete_pause', 'batch_id': batch['batch_id'],
                           'core_result': result, 'candidate_admitted': False}
                e.atomic_json(folder / 'PAUSE.json', stopped)
                break
            process = a.load(attempt / 'process.json')
            request = a.load(attempt / 'request.json')
            expected = {'system': suggestions.proposal_system_prompt(settings),
                        'prompt': json.dumps(preview['context'], ensure_ascii=False, indent=2),
                        'model': settings['name'], 'temperature': settings['temperature'],
                        'max_output_tokens': settings['max_output_tokens']}
            if request != expected:
                raise ValueError('Recorded response request differs from the bound model context')
            decision, normalized = review_response(process, preview['context'], public_names,
                                                    accepted_names, suggestions.validate_suggestions)
            if not decision['exposure_reviewed']:
                stopped = decision
                e.atomic_json(folder / 'PAUSE.json', decision)
                break
            # Rejected code may remain in a core proposal file for audit, but it is
            # never referenced by the accepted candidate set or an install plan.
            emitted = suggestions._finish_proposal(preview, attachment, folder, process, None, attempt) if decision['accepted'] else {}
            child_artifacts = list(a.load(emitted['proposal'])['artifacts'].values()) if emitted.get('proposal') else []
            row = {**decision, 'identity': batch_identity, 'batch_id': batch['batch_id'],
                   'api_ids': batch['api_ids'], 'source_preview': batch['preview'],
                   'source_request': a.bind(attempt / 'request.json'), 'source_process': a.bind(attempt / 'process.json'),
                   'source_rejection': a.bind(attempt / 'rejected.json') if (attempt / 'rejected.json').exists() else None,
                   'validator': a.bind(Path(args.release) / 'workflow/improvement_suggestions.py'),
                   'proposal': a.bind(emitted['proposal']) if emitted.get('proposal') else None,
                   'suggestions': a.bind(folder / 'suggestions.json') if decision['accepted'] else None,
                   'accepted_artifacts': child_artifacts,
                   'alias_count': len(normalized['aliases']) if decision['accepted'] else 0,
                   'prior_alias_names_sha256': a.digest(sorted(accepted_names)), 'installed': False}
            row['review_sha256'] = a.digest(row)
            e.atomic_json(review_path, row)
            verify_review(row, a, accepted_names)
            reviewed.append(row)
            e.atomic_json(output / 'PROGRESS.json', {'bank': continuation['bank'],
                          'remaining_batches_reviewed': len(reviewed), 'remaining_batches_total': len(continuation['batches']),
                          'accepted_batches': sum(r['accepted'] for r in prefix + reviewed),
                          'rejected_batches': sum(not r['accepted'] for r in prefix + reviewed),
                          'new_model_calls_this_invocation': calls, 'full_api_exposure_complete': False})
        report = {'status': 'incomplete', 'bank': continuation['bank'], 'continuation': a.bind(continuation_path),
                  'full_api_count': continuation['full_api_count'], 'subset_api_count': continuation['subset_api_count'],
                  'revalidated_batches': continuation['prefix_revalidations'],
                  'new_batch_reviews': [a.bind(output / r['batch_id'] / 'REVIEW.json') for r in reviewed],
                  'stopped': stopped, 'new_model_calls_this_invocation': calls, 'installed': False,
                  'full_api_exposure_complete': False, 'requires_build_and_behavior_validation': True,
                  'accepted_proposals': accepted_proposals(prefix + reviewed),
                  'accepted_batches': sum(r['accepted'] for r in prefix + reviewed),
                  'rejected_batches': sum(not r['accepted'] for r in prefix + reviewed),
                  'reviewed_api_count': sum(len(r['api_ids']) for r in prefix + reviewed),
                  'api_count_in_accepted_batches': sum(len(r['api_ids']) for r in prefix + reviewed if r['accepted']),
                  'alias_count': sum(r['alias_count'] for r in prefix + reviewed if r['accepted'])}
        if stopped is None and len(reviewed) == len(continuation['batches']):
            verify_partition(continuation['full_api_ids'], [api for row in prefix for api in row['api_ids']],
                             [api for row in reviewed for api in row['api_ids']])
            names = [alias['name'] for ref in report['accepted_proposals'] for alias in a.load(ref['path'])['aliases']]
            verify_alias_names(names, public_names)
            report.update(status='reviewed_with_rejections' if report['rejected_batches'] else 'alias_authoring_complete',
                          full_api_exposure_complete=True, exact_disjoint_full_bank_coverage=True,
                          all_candidates_valid=report['rejected_batches'] == 0)
            e.atomic_json(output / 'AUTHORING_COMPLETION.json', report)
        e.atomic_json(output / 'BANK_UNION.json', report)
        e.atomic_json(output / 'ACCEPTED_CANDIDATES.json', {
            'bank': continuation['bank'], 'status': 'schema_valid_candidates_runtime_validation_pending',
            'accepted_proposals': report['accepted_proposals'],
            'reviewed_api_count': report['reviewed_api_count'], 'full_api_count': report['full_api_count'],
            'rejected_batches': report['rejected_batches'],
            'full_api_exposure_complete': report['full_api_exposure_complete'], 'installed': False})
        print(json.dumps({k: report[k] for k in ['status','bank','full_api_count','subset_api_count','full_api_exposure_complete','new_model_calls_this_invocation','accepted_batches','rejected_batches']}))
        return 0 if report['full_api_exposure_complete'] else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'run'])
    parser.add_argument('--release', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--full-manifest')
    parser.add_argument('--model-config')
    parser.add_argument('--recorded-attempts')
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
