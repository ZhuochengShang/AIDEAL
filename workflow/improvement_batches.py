"""Bounded library-wide proposal plans and independently resumable model batches."""
import json
from collections import Counter
from pathlib import Path

from .ablation import bind, digest, load, verify_artifact
from .execution import atomic_json, invoke, ownership
from .improvement_context import (alias_target, development_destination, _development_errors,
                                  _library_inputs, _semantic_context, _source_windows)
from .improvement_suggestions import (PROMPT, _finish_proposal, _load_preview, _model_settings,
                                     proposal_response_error)


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be between {low} and {high}')


def _alias_destination(template, number):
    if template is None:
        return None
    if not isinstance(template, str) or template.count('{batch}') != 1:
        raise ValueError('alias_path_template must contain exactly one {batch} placeholder')
    value = template.replace('{batch}', f'{number:04d}')
    if '{' in value or '}' in value:
        raise ValueError('Only the {batch} placeholder is supported')
    return alias_target(value)


def _library_overview(public, max_characters):
    """Bound the cross-batch orientation, while retaining the full catalogue on disk."""
    counts = Counter(row.get('module') or row['file'] for row in public)
    overview = {'module_count': len(counts), 'modules': [], 'omitted_modules': len(counts),
                'api_catalog': [], 'omitted_catalog_entries': len(public),
                'scope': 'Compact cross-batch orientation only; source evidence remains batch-local.'}
    module_budget = max_characters // 3
    for module, count in sorted(counts.items()):
        candidate = overview['modules'] + [{'module': module, 'public_definitions': count}]
        if len(json.dumps(candidate, ensure_ascii=False, indent=2)) > module_budget:
            break
        overview['modules'] = candidate
        overview['omitted_modules'] -= 1
    for row in public:
        entry = {key: row[key] for key in ('id', 'name', 'signature')}
        candidate = {**overview, 'api_catalog': overview['api_catalog'] + [entry],
                     'omitted_catalog_entries': overview['omitted_catalog_entries'] - 1}
        if len(json.dumps(candidate, ensure_ascii=False, indent=2)) <= max_characters:
            overview = candidate
    return overview


def preview_library_improvements(study, output, *, alias_path_template=None, apis=None,
                                 development_errors=None, batch_size=12,
                                 max_context_characters=60000, max_batches=1000,
                                 max_error_characters=12000, max_catalog_characters=6000):
    """Partition every selected public API exactly once; save contexts without calls.

    Source discovery is static and bounded by the configured tracked file scope.
    Refactor evidence is batch-local; this is not an all-pairs semantic comparison.
    """
    _integer(batch_size, 'batch_size', 1, 100)
    _integer(max_context_characters, 'max_context_characters', 1000, 250000)
    _integer(max_batches, 'max_batches', 1, 10000)
    _integer(max_error_characters, 'max_error_characters', 0, 100000)
    _integer(max_catalog_characters, 'max_catalog_characters', 500, 25000)
    _alias_destination(alias_path_template, 1)
    study, root, attachment, cfg, public, refs = _library_inputs(study)
    output = development_destination(study, output)
    if output.exists():
        raise FileExistsError('Library preview output already exists')
    definitions = public
    if apis:
        known = {row[k] for row in public for k in ('id', 'name', 'qualified_name')}
        if set(apis) - known:
            raise ValueError('Requested API not found: ' + ', '.join(sorted(set(apis) - known)))
        definitions = [row for row in public if {row['id'], row['name'], row['qualified_name']}.intersection(apis)]
    source_refs = _source_windows(root, definitions)
    semantics, profile_refs = _semantic_context(cfg, root, attachment)
    errors, error_ref, omitted_errors = _development_errors(
        development_errors, public, max_characters=max_error_characters * max_batches)
    catalog = [{key: row[key] for key in ('id', 'name', 'qualified_name', 'file', 'line', 'signature')}
               for row in public]
    common = {'project': cfg.project_name, 'language': cfg.language,
              'baseline_revision': attachment['revision'], **semantics,
              'library_overview': _library_overview(public, max_catalog_characters),
              'library_scope': {'public_definitions': len(public), 'requested_definitions': len(definitions),
                                'catalog_sha256': digest(catalog),
                                'limitations': 'Cross-batch bodies are not supplied. Discovery can miss syntax unsupported by the configured adapter.'}}

    def context(rows, number):
        ids = {row['id'] for row in rows}
        selected_errors, used, omitted = [], 0, 0
        for error in errors:
            if error['function_id'] not in ids:
                continue
            size = len(json.dumps(error, ensure_ascii=False))
            if used + size > max_error_characters:
                omitted += 1
            else:
                selected_errors.append(error)
                used += size
        return {**common, 'batch_id': f'batch-{number:04d}',
                'alias_destination': _alias_destination(alias_path_template, number),
                'apis': rows, 'development_errors': selected_errors,
                'coverage': {'matching_definitions': len(definitions), 'selected_definitions': len(rows),
                             'omitted_definitions': len(definitions) - len(rows),
                             'omitted_error_rows': omitted,
                             'source_window_policy': 'Three preceding and up to sixty following lines; not complete function bodies.'}}

    groups, current = [], []
    for row in definitions:
        candidate = current + [row]
        value = context(candidate, len(groups) + 1)
        if current and (len(candidate) > batch_size or len(json.dumps(value, ensure_ascii=False, indent=2)) > max_context_characters):
            groups.append(current)
            current = []
            value = context([row], len(groups) + 1)
        if len(json.dumps(value, ensure_ascii=False, indent=2)) > max_context_characters:
            raise ValueError('One API plus shared context exceeds the context budget: ' + row['id'])
        current.append(row)
    if current:
        groups.append(current)
    if len(groups) > max_batches:
        raise ValueError('Full API coverage exceeds max_batches; raise the explicit limit or narrow the API scope')
    contexts = [context(rows, number) for number, rows in enumerate(groups, 1)]
    for value in contexts:
        if value['alias_destination'] and (root / value['alias_destination']).exists():
            raise ValueError('Aliases must be new modules, not replace baseline code')
    shared_refs = refs + profile_refs + ([error_ref] if error_ref else [])
    # Detect input changes during preparation before publishing any manifest.
    if not all(verify_artifact(ref) for ref in source_refs + shared_refs):
        raise ValueError('Development inputs changed during preview')
    output.mkdir(parents=True, exist_ok=False)
    batches = []
    for value in contexts:
        paths = {str(root / row['file']) for row in value['apis']}
        preview = {'schema_version': 1, 'study': str(study), 'source_root': str(root),
                   'baseline_revision': attachment['revision'], 'context': value,
                   'artifacts': [ref for ref in source_refs if ref['path'] in paths] + shared_refs,
                   'error_scope': 'operator-designated development logs only', 'llm_calls': 0}
        preview['preview_sha256'] = digest(preview)
        path = output / value['batch_id'] / 'preview.json'
        atomic_json(path, preview)
        batches.append({'batch_id': value['batch_id'], 'preview': bind(path),
                        'api_ids': [row['id'] for row in value['apis']],
                        'context_characters': len(json.dumps(value, ensure_ascii=False, indent=2))})
    manifest = {'schema_version': 1, 'kind': 'library_improvement_preview',
                'study': str(study), 'baseline_revision': attachment['revision'],
                'settings': {'batch_size': batch_size, 'max_context_characters': max_context_characters,
                             'max_batches': max_batches, 'max_error_characters': max_error_characters,
                             'max_catalog_characters': max_catalog_characters,
                             'alias_path_template': alias_path_template, 'apis': apis},
                'coverage': {'public_definitions': len(public), 'requested_definitions': len(definitions),
                             'planned_definitions': sum(len(rows) for rows in groups),
                             'omitted_requested_definitions': 0, 'batch_count': len(batches),
                             'omitted_or_unmatched_development_rows': omitted_errors},
                'api_catalog': catalog, 'artifacts': source_refs + shared_refs,
                'batches': batches, 'llm_calls': 0}
    manifest['manifest_sha256'] = digest(manifest)
    atomic_json(output / 'manifest.json', manifest)
    return {'manifest': str(output / 'manifest.json'), 'coverage': manifest['coverage'], 'llm_calls': 0}


def _implementation_bindings():
    root = Path(__file__).resolve().parents[1]
    paths = sorted((root / 'workflow').glob('*.py'))
    paths += sorted((root / 'vendor/aideal_engine/src/aideal').glob('*.py'))
    return [bind(path) for path in paths]


def _verified_completion(path, identity):
    record = load(path)
    if (record.get('identity') != identity
            or record.get('completion_sha256') != digest({k: v for k, v in record.items() if k != 'completion_sha256'})
            or not all(verify_artifact(ref) for ref in record['artifacts'])):
        raise ValueError('Completed proposal batch evidence changed; preserve it and use a new output')
    return record['result']


def _run_batch(preview_path, settings, output, identity, run_artifacts, public_names):
    preview, _, attachment = _load_preview(preview_path)
    complete = output / 'completion.json'
    if complete.exists():
        return _verified_completion(complete, identity), 0
    output.mkdir(parents=True, exist_ok=True)
    atomic_json(output / 'preview.json', preview)
    request = {'system': PROMPT.read_text(), 'prompt': json.dumps(preview['context'], ensure_ascii=False, indent=2),
               'model': settings['name'], 'temperature': settings['temperature'],
               'max_output_tokens': settings['max_output_tokens']}
    atomic_json(output / 'request.json', request)
    limit = settings.get('provider_attempt_limit', 1)
    calls = 0
    attempts = sorted(output.glob('attempt_[0-9][0-9][0-9]'))
    # Reuse a successful recorded response after interruption during publication.
    attempt = next((path for path in reversed(attempts)
                    if (path / 'process.json').is_file() and not (path / 'rejected.json').exists()
                    and load(path / 'process.json').get('status') == 'ok'), None)
    if attempt is None:
        if len(attempts) >= limit:
            return {'status': 'attempt_budget_exhausted', 'output': str(output)}, 0
        attempt = output / f'attempt_{len(attempts) + 1:03d}'
        calls = 1
    result = invoke(settings['command'], request, attempt, settings['timeout_s'])
    if not all(verify_artifact(ref) for ref in run_artifacts):
        raise ValueError('Library proposal inputs changed during generation; preserve this output')
    if result['status'] != 'ok' or not isinstance(result.get('payload'), dict) or not isinstance(result['payload'].get('code'), str):
        return {'status': 'model_attempt_failed', 'output': str(output), 'attempt': str(attempt)}, calls
    error = proposal_response_error(result, settings['name'])
    if error:
        atomic_json(attempt / 'rejected.json', {'reason': error, 'status': 'invalid_provider_response'})
        return {'status': 'invalid_suggestions', 'output': str(output), 'attempt': str(attempt)}, calls
    # Validate outside the emission helper so schema failures are retryable, while
    # changed source/evidence remains a hard error rather than a new model attempt.
    from .improvement_suggestions import validate_suggestions
    try:
        validate_suggestions(json.loads(result['payload']['code']), preview['context'], reserved_names=public_names)
    except (ValueError, SyntaxError, TypeError) as exc:
        atomic_json(attempt / 'rejected.json', {'reason': str(exc), 'status': 'invalid_suggestions'})
        return {'status': 'invalid_suggestions', 'output': str(output), 'attempt': str(attempt)}, calls
    value = _finish_proposal(preview, attachment, output, result, None, attempt)
    artifacts = [bind(p) for p in sorted(output.iterdir()) if p.is_file()]
    artifacts += [bind(p) for p in sorted(attempt.rglob('*')) if p.is_file()]
    record = {'identity': identity, 'result': value, 'artifacts': artifacts}
    record['completion_sha256'] = digest(record)
    atomic_json(complete, record)
    return value, calls


def propose_library_improvements(manifest_path, model_config, output, *, max_batches=None):
    """Run/resume a bounded proposal collection; install nothing and preserve failures.

    max_batches limits new batches attempted in this invocation. The model config's
    provider_attempt_limit (default one) bounds lifetime calls per batch, including
    failed or interrupted attempts. Resume always requires the same exact identity.
    """
    manifest_path = Path(manifest_path).resolve()
    manifest = load(manifest_path)
    if (manifest.get('kind') != 'library_improvement_preview'
            or manifest.get('manifest_sha256') != digest({k: v for k, v in manifest.items() if k != 'manifest_sha256'})):
        raise ValueError('Library preview manifest changed')
    if not all(verify_artifact(ref) for ref in manifest['artifacts']):
        raise ValueError('Library preview input artifacts changed')
    batch_ids = []
    for number, batch in enumerate(manifest['batches'], 1):
        if batch.get('batch_id') != f'batch-{number:04d}':
            raise ValueError('Library batch IDs must be ordered safe directory names')
        if not verify_artifact(batch['preview']):
            raise ValueError('Library batch preview changed')
        preview = load(batch['preview']['path'])
        if (preview.get('study') != manifest['study']
                or preview.get('baseline_revision') != manifest['baseline_revision']
                or preview.get('preview_sha256') != digest({k: v for k, v in preview.items() if k != 'preview_sha256'})
                or preview['context'].get('batch_id') != batch['batch_id']
                or [row['id'] for row in preview['context']['apis']] != batch['api_ids']):
            raise ValueError('Library batch identity or API coverage does not match its manifest')
        batch_ids.extend(batch['api_ids'])
    if (not batch_ids or len(batch_ids) != len(set(batch_ids))
            or len(batch_ids) != manifest['coverage']['planned_definitions']
            or len(manifest['batches']) != manifest['coverage']['batch_count']):
        raise ValueError('Library batch API coverage is empty, duplicated or inconsistent')
    if max_batches is not None:
        _integer(max_batches, 'max_batches', 1, 10000)
    settings = _model_settings(model_config)
    _integer(settings.get('provider_attempt_limit', 1), 'model.provider_attempt_limit', 1, 100)
    # Recheck the attachment and review hold even when every batch is cached.
    _load_preview(manifest['batches'][0]['preview']['path'])
    output = development_destination(manifest['study'], output)
    command_files = [bind(p) for p in settings['command'] if Path(p).is_absolute() and Path(p).is_file()]
    extra_files = settings.get('artifacts', [])
    if not isinstance(extra_files, list) or any(not isinstance(p, str) for p in extra_files):
        raise ValueError('model.artifacts must be a list of filenames')
    command_files += [bind(Path(model_config).resolve().parent / p) for p in extra_files]
    identity = {'manifest': bind(manifest_path), 'model_configuration': bind(model_config),
                'model_command_artifacts': command_files, 'prompt': bind(PROMPT),
                'implementation': _implementation_bindings()}
    identity_hash = digest(identity)
    run_artifacts = [identity['manifest'], identity['model_configuration'], identity['prompt'],
                     *identity['model_command_artifacts'], *identity['implementation']]
    with ownership(output):
        identity_path = output / 'identity.json'
        if identity_path.exists():
            if load(identity_path) != identity:
                raise ValueError('Library proposal identity changed; use a new output directory')
        elif any(p.name != '.lock' for p in output.iterdir()):
            raise ValueError('Existing library output has no identity; preserve it and use a new output')
        else:
            atomic_json(identity_path, identity)
        completed, attempted, calls, stopped = [], 0, 0, None
        public_names = {row['name'] for row in manifest['api_catalog']}
        alias_owners = {}
        collisions = []
        for batch in manifest['batches']:
            folder = output / batch['batch_id']
            if folder.is_symlink() or folder.resolve().parent != output:
                raise ValueError('Batch output must be inside the owned output directory')
            if not (folder / 'completion.json').exists():
                if max_batches is not None and attempted >= max_batches:
                    stopped = 'invocation_batch_limit'
                    break
                attempted += 1
            batch_identity = digest({'run': identity_hash, 'batch': batch})
            if not all(verify_artifact(ref) for ref in run_artifacts):
                raise ValueError('Library proposal inputs changed during generation')
            result, used = _run_batch(batch['preview']['path'], settings, folder, batch_identity, run_artifacts, public_names)
            calls += used
            if result['status'] in ('attempt_budget_exhausted', 'model_attempt_failed', 'invalid_suggestions'):
                stopped = result
                break
            item = {'batch_id': batch['batch_id'], 'api_ids': batch['api_ids'], 'status': result['status'],
                    'completion': bind(folder / 'completion.json'),
                    'proposal': bind(result['proposal']) if result.get('proposal') else None}
            if item['proposal']:
                proposal = load(item['proposal']['path'])
                for alias in proposal['aliases']:
                    name = alias['name']
                    if name in alias_owners or name in public_names:
                        collisions.append({'name': name, 'batch': batch['batch_id'],
                                           'other': alias_owners.get(name, 'existing_public_api')})
                    alias_owners[name] = batch['batch_id']
            completed.append(item)
        report = {'schema_version': 1, 'kind': 'library_improvement_proposal_collection',
                  'study': manifest['study'], 'baseline_revision': manifest['baseline_revision'],
                  'identity_sha256': identity_hash, 'manifest': bind(manifest_path),
                  'status': 'alias_collisions_require_review' if collisions else
                            'complete_unvalidated' if len(completed) == len(manifest['batches']) else 'incomplete',
                  'coverage': manifest['coverage'], 'completed_batches': len(completed),
                  'batches': completed, 'alias_collisions': collisions, 'stopped': stopped,
                  'llm_calls_this_invocation': calls, 'installed': False, 'requires_validation': True}
        atomic_json(output / 'collection.json', report)
    return {'collection': str(output / 'collection.json'), 'status': report['status'],
            'completed_batches': len(completed), 'total_batches': len(manifest['batches']),
            'llm_calls': calls, 'alias_collisions': collisions,
            'proposals': [item['proposal']['path'] for item in completed if item['proposal']]}
