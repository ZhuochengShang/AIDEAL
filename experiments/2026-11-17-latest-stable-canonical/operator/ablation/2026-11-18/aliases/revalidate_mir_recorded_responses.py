"""Revalidate preserved MIR model output offline; never fabricate a generation call."""
import argparse
from pathlib import Path
import json
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', required=True)
    args = parser.parse_args()
    release = Path(args.release).resolve()
    sys.path[:0] = [str(release), str(release / 'vendor/aideal_engine/src')]
    from workflow.improvement_suggestions import _load_preview, validate_suggestions, _finish_proposal
    from workflow.ablation import bind, verify_artifact
    from workflow.execution import atomic_json
    study = Path('/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical')
    original = study / 'ablation-2026-11-18/development/aliases-explicit-wrappers/mir_eval/collection'
    manifest_path = study / 'ablation-2026-11-18/development/aliases/mir_eval/preview-compact/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    reserved_names = {row['name'] for row in manifest['api_catalog']}
    output = study / 'ablation-2026-11-18/development/aliases-revalidated-metadata/mir_eval'
    output.mkdir(parents=True, exist_ok=False)
    results = []
    for batch in manifest['batches'][:3]:
        if not verify_artifact(batch['preview']):
            raise ValueError('Original saved preview changed')
        preview, _, attachment = _load_preview(batch['preview']['path'])
        # Reuse the earliest recorded complete response. Later rejected retries stay
        # untouched and remain part of the historical authoring cost.
        attempt = original / batch['batch_id'] / 'attempt_001'
        process_path = attempt / 'process.json'
        result = json.loads(process_path.read_text())
        raw_request = json.loads((attempt / 'request.json').read_text())
        expected_prompt = json.dumps(preview['context'], ensure_ascii=False, indent=2)
        if raw_request['prompt'] != expected_prompt or result.get('status') != 'ok':
            raise ValueError('Recorded response does not match the bound preview')
        payload = result['payload']
        if payload.get('solution_state', {}).get('status') != 'complete':
            raise ValueError('Only complete recorded responses can be revalidated')
        raw = json.loads(payload['code'])
        normalized = validate_suggestions(raw, preview['context'], reserved_names=reserved_names)
        normalizations = [] if 'notes' in raw else [{'field': 'notes', 'operation': 'absent_to_empty_string',
                                                     'scope': 'narrative metadata only'}]
        if {k: v for k, v in normalized.items() if k not in ['notes', 'refactors']} != {
                k: v for k, v in raw.items() if k not in ['notes', 'refactors']}:
            raise ValueError('Revalidation unexpectedly changed functional proposal content')
        destination = output / batch['batch_id']
        destination.mkdir()
        emitted = _finish_proposal(preview, attachment, destination, result, None, attempt)
        receipt = {'status': 'schema_revalidated_unvalidated_code', 'new_model_calls': 0,
                   'source_preview': batch['preview'], 'source_request': bind(attempt / 'request.json'),
                   'source_process': bind(process_path), 'source_rejection': bind(attempt / 'rejected.json')
                       if (attempt / 'rejected.json').exists() else None,
                   'normalizations': normalizations, 'validator': bind(release / 'workflow/improvement_suggestions.py'),
                   'proposal': bind(emitted['proposal']), 'api_ids': batch['api_ids'],
                   'alias_count': len(normalized['aliases']), 'installed': False,
                   'requires_build_and_behavior_validation': True}
        atomic_json(destination / 'REVALIDATION.json', receipt)
        results.append(receipt)
    atomic_json(output / 'REVALIDATION.json', {'status': 'partial_bank_offline_revalidation',
                'manifest': bind(manifest_path), 'release': str(release), 'new_model_calls': 0,
                'batches': results, 'api_count': sum(len(r['api_ids']) for r in results),
                'remaining_batch_count': len(manifest['batches']) - len(results),
                'alias_count': sum(r['alias_count'] for r in results),
                'full_bank_complete': False, 'installed': False})
    print(json.dumps({'output': str(output), 'new_model_calls': 0,
                      'api_count': sum(len(r['api_ids']) for r in results),
                      'alias_count': sum(r['alias_count'] for r in results), 'full_bank_complete': False}))


if __name__ == '__main__':
    main()
