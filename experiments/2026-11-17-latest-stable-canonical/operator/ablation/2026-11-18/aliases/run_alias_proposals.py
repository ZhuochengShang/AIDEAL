"""Run one exact-bank alias-only collection with the existing proposal workflow."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['release', 'model-config', 'preview', 'output', 'bank', 'preparation-progress',
                 'original-config', 'original-manifest']:
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--expected-apis', type=int, required=True)
    parser.add_argument('--wait-preview-seconds', type=int, default=3600)
    args = parser.parse_args()
    release = Path(args.release).resolve()
    sys.path[:0] = [str(release), str(release / 'vendor/aideal_engine/src')]
    from workflow.improvement_batches import propose_library_improvements
    from workflow.improvement_suggestions import _model_settings
    from workflow.execution import atomic_json
    from workflow.preparation import _engine_config_module
    from aideal.doc_check_sources import _load_manifest
    if _model_settings(args.model_config)['proposal_scope'] != 'aliases_only':
        raise ValueError('This development collection requires proposal_scope=aliases_only')
    preview = Path(args.preview)
    deadline = time.monotonic() + args.wait_preview_seconds
    while not preview.is_file():
        progress = Path(args.preparation_progress)
        if progress.exists():
            rows = json.loads(progress.read_text())['banks']
            failed = next((r for r in rows if r['bank'] == args.bank and r['status'] == 'preparation_failed'), None)
            if failed:
                raise ValueError('Alias preview preparation failed: ' + failed['error'])
        if time.monotonic() >= deadline:
            raise TimeoutError('Alias preview did not become ready; no model call was made')
        print(json.dumps({'bank': args.bank, 'status': 'waiting_for_preview', 'model_calls': 0}), flush=True)
        time.sleep(15)
    manifest = json.loads(preview.read_text())
    if manifest.get('context_policy') != 'calling-facts-and-source-v1':
        raise ValueError('This collection requires the recorded compact-context policy')
    cfg = _engine_config_module().load_config(args.original_config)
    expected = _load_manifest(cfg, args.original_manifest)
    listed = [api for batch in manifest['batches'] for api in batch['api_ids']]
    if (manifest['coverage']['requested_definitions'] != args.expected_apis
            or manifest['coverage']['planned_definitions'] != args.expected_apis
            or manifest['coverage']['omitted_requested_definitions'] != 0
            or len(expected) != args.expected_apis or len(set(expected)) != len(expected)
            or len(listed) != len(expected) or set(listed) != set(expected)):
        raise ValueError('Alias preview differs from the exact approved Original API identity set')
    result = propose_library_improvements(preview, args.model_config, args.output)
    collection_path = Path(result['collection'])
    collection = json.loads(collection_path.read_text())
    print(json.dumps(result), flush=True)
    if (collection['status'] != 'complete_unvalidated' or collection['alias_collisions']
            or collection['completed_batches'] != collection['coverage']['batch_count']):
        return 2
    proposals = [json.loads(Path(r['proposal']['path']).read_text())
                 for r in collection['batches'] if r['proposal']]
    atomic_json(Path(args.output) / 'DEVELOPMENT_COMPLETION.json', {
        'status': 'alias_proposals_complete_unvalidated', 'bank': args.bank,
        'selected': args.expected_apis, 'completed_batches': collection['completed_batches'],
        'alias_count': sum(len(p['aliases']) for p in proposals),
        'installed': False, 'requires_build_and_behavior_validation': True,
        'proposal_scope': 'aliases_only', 'release': str(release),
        'original_manifest': args.original_manifest,
        'original_manifest_sha256': hashlib.sha256(Path(args.original_manifest).read_bytes()).hexdigest(),
        'collection': str(collection_path),
        'collection_sha256': hashlib.sha256(collection_path.read_bytes()).hexdigest(),
        'llm_calls_this_invocation': result['llm_calls']})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
