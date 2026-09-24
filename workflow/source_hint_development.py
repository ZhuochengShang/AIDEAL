"""Development-only R0 evidence -> model proposals -> independently checked hints.

Model diagnoses are hypotheses. Only four-role checks by an explicitly configured,
trusted adapter can produce an installable validation receipt. This module never
installs source or learns from held-out failures.
"""
import json
import hashlib
from pathlib import Path
import re

from .ablation import bind, digest, load, verify_artifact
from .execution import atomic_json, invoke, ownership
from .failure_diagnosis import diagnose_failure
from .improvement_suggestions import _model_settings
from .response_status import solution_state
from .source_hints import (_declaration, _identity, index_source_hints, select_source_hints,
                           insert_source_hint, strip_source_hints)
from .source_hint_proposals import prepare_source_hints
from .treatment_versions import _run as git, _check_worktree

PROMPT = Path(__file__).resolve().parents[1] / 'prompts/source_hint_development.md'
ROLES = ('trigger', 'corrected', 'valid', 'nearby_negative')
PROTOCOL = 'source_hint_development_validation_v1'


def _verified(ref):
    if not isinstance(ref, dict) or not verify_artifact(ref):
        raise ValueError('Missing or changed development artifact')
    return load(ref['path'])


def _seal(value):
    return {**value, 'sha256': digest(value)}


def _open(path):
    value = load(path)
    if value.get('sha256') != digest({k: v for k, v in value.items() if k != 'sha256'}):
        raise ValueError('Development record changed')
    if not all(verify_artifact(ref) for ref in value['artifacts']):
        raise ValueError('Development evidence changed')
    _baseline(value['source_root'], value['baseline_revision'])
    return value


def _baseline(root, revision):
    root = Path(root).resolve(strict=True)
    if git(root, 'rev-parse', '--show-toplevel') != str(root) or git(root, 'rev-parse', 'HEAD') != revision:
        raise ValueError('Development source is not the exact pinned Git root/revision')
    _check_worktree(root, revision, {})
    return root


def _destination(root, output):
    output = Path(output).resolve()
    if output == root or output.is_relative_to(root) or output.exists():
        raise ValueError('Use a new development output outside the source checkout')
    return output


def _scope(value):
    if value.get('split') != 'development' or value.get('condition') != 'original' or type(value.get('round')) is not int or value['round'] != 0:
        raise ValueError('Only Original DEVELOPMENT R0 evidence can develop source hints')


def _body(code):
    match = re.fullmatch(r'\s*```[^\n]*\n(.*?)\n```\s*', code, re.S)
    return match[1] if match else code


def _outcome(process):
    payload = process.get('payload')
    keys = ('execution_pass', 'oracle_pass', 'target_reached')
    if process.get('status') != 'ok' or not isinstance(payload, dict) or any(type(payload.get(k)) is not bool for k in keys):
        raise ValueError('Checker did not supply three explicit outcome booleans')
    if not isinstance(payload.get('public_feedback'), str):
        raise ValueError('Checker needs a public diagnostic')
    return payload, all(payload[k] for k in keys)


def _facts(root, identity):
    relative, number, name = _identity(identity)
    candidate = root / relative
    path = candidate.resolve(strict=True)
    if (not path.is_relative_to(root) or any(part.startswith('.') for part in Path(relative).parts)
            or candidate.is_symlink() or path.suffix not in ('.py', '.scala', '.java', '.rs')
            or path.stat().st_size > 2_000_000):
        raise ValueError('Unsafe or oversized development source')
    if relative not in git(root, 'ls-files', '--', relative).splitlines():
        raise ValueError('Development API source must be committed')
    lines = path.read_text().splitlines(keepends=True)
    actual, signature = _declaration(lines, number - 1, name)
    if actual != number - 1:
        raise ValueError('Canonical ID does not identify the exact source declaration')
    window = ''.join(lines[max(0, actual - 8):actual + 72])
    if len(window) > 12000:
        raise ValueError('Source window exceeds bounded authoring input; narrow this development case')
    return {'function_id': identity, 'path': relative, 'line': number, 'signature': signature,
            'source_window': window, 'source_window_start_line': max(0, actual - 8) + 1,
            'namespace_declarations': [{'line': i + 1, 'text': line.rstrip('\r\n')}
                                       for i, line in enumerate(lines[:80])
                                       if re.match(r'^\s*package\s+[A-Za-z_][\w.]*\s*;?\s*$', line)],
            'source': bind(path)}


def build_development_preview(manifest_path, output, *, max_cases=16):
    """Harvest bound Original development R0 failures, excluding private fields."""
    manifest = load(manifest_path)
    if manifest.get('schema_version') != 1:
        raise ValueError('Development manifest needs schema_version 1')
    _scope(manifest)
    root = _baseline(manifest['source_root'], manifest['baseline_revision'])
    output = _destination(root, output)
    apis, documents = manifest['api_function_ids'], manifest['original_documents']
    if not isinstance(apis, dict) or not apis or len(set(apis.values())) != len(apis):
        raise ValueError('Supply distinct canonical API identities')
    if not isinstance(documents, list) or not documents or not all(verify_artifact(d) for d in documents):
        raise ValueError('Pin the Original documentation artifacts')
    held_out = manifest.get('held_out_case_ids')
    attempts = manifest.get('attempts')
    if not isinstance(held_out, list) or not isinstance(attempts, list) or not attempts or len(attempts) > 2000:
        raise ValueError('Supply a bounded development manifest and explicit held-out ID list')
    if type(max_cases) is not int or not 1 <= max_cases <= 100:
        raise ValueError('max_cases must be between 1 and 100')
    controller_refs = [bind(Path(__file__).with_name(name)) for name in (
        'source_hint_development.py', 'source_hints.py', 'source_hint_proposals.py',
        'failure_diagnosis.py', 'response_status.py', 'execution.py', 'ablation.py',
        'treatment_versions.py')]
    refs, cases, skipped, seen_ids, duplicate_groups = [bind(manifest_path), *documents, *controller_refs], [], [], set(), {}
    index = {'api_function_ids': apis, 'records': []}
    for row in attempts:
        _scope(row)
        identifier = row.get('case_id')
        if not isinstance(identifier, str) or not re.fullmatch(r'[\w.-]+', identifier) or identifier in seen_ids or identifier in held_out:
            raise ValueError('Unsafe, duplicate or held-out development case ID')
        seen_ids.add(identifier)
        evidence = {key: row[key] for key in ('provider_request', 'provider_process')}
        values = {key: _verified(ref) for key, ref in evidence.items()}
        refs.extend(evidence.values())
        provider_request = values['provider_request']
        provenance = provider_request.get('context_provenance', {})
        _scope(provenance)
        if (provenance.get('original_documents') != documents
                or provenance.get('source_root') != str(root)
                or provenance.get('source_revision') != manifest['baseline_revision']
                or not all(isinstance(provider_request.get(k), str) for k in ('system', 'prompt'))):
            raise ValueError('Original audience request lacks exact documentation/source provenance')
        if sum(len(provider_request[k]) for k in ('system', 'prompt')) > 60000:
            raise ValueError('Original audience request exceeds 60000 characters; do not truncate its task')
        response = values['provider_process']
        if response.get('status') != 'ok' or not isinstance(response.get('payload'), dict):
            skipped.append({'case_id': identifier, 'reason': 'provider_failure'})
            continue
        state = solution_state(response['payload'])
        if not state['executable']:
            skipped.append({'case_id': identifier, 'reason': 'generation_' + state['status']})
            continue
        for key in ('execution_request', 'execution_process'):
            evidence[key] = row[key]
            values[key] = _verified(row[key])
            refs.append(row[key])
        execution = values['execution_request']
        _scope(execution)
        if execution.get('case_id') != identifier or execution.get('source_revision') != manifest['baseline_revision']:
            raise ValueError('Development checker request has different task/source provenance')
        code = _body(response['payload']['code'])
        if execution.get('code') != code:
            raise ValueError('Checker did not execute the saved model program')
        payload, passed = _outcome(values['execution_process'])
        if passed:
            skipped.append({'case_id': identifier, 'reason': 'passed'})
            continue
        previous = {'code': code, 'feedback': payload['public_feedback']}
        if 'public_failure' in payload:
            previous['public_failure'] = payload['public_failure']
        diagnosis = diagnose_failure(index, previous)
        if diagnosis['status'] != 'identified':
            skipped.append({'case_id': identifier, 'reason': diagnosis['status']})
            continue
        key = digest([diagnosis['function_id'], code, previous['feedback']])
        if key in duplicate_groups:
            duplicate_groups[key]['duplicate_case_ids'].append(identifier)
            continue
        if len(cases) == max_cases:
            skipped.append({'case_id': identifier, 'reason': 'batch_limit'})
            continue
        facts = _facts(root, diagnosis['function_id'])
        facts['qualified_api_names'] = sorted(api for api, identity in apis.items()
                                              if identity == diagnosis['function_id'])
        refs.append(facts['source'])
        item = {'evidence_id': identifier, 'function_id': diagnosis['function_id'],
                'code': code, 'diagnostic': previous['feedback'], 'attribution': diagnosis,
                'audience_request': {k: provider_request[k] for k in ('system', 'prompt')},
                'facts': facts, 'duplicate_case_ids': [], 'evidence': evidence}
        if len(json.dumps(item)) > 90000:
            raise ValueError('Development case exceeds bounded context; do not silently truncate evidence')
        cases.append(item)
        duplicate_groups[key] = item
    if not cases:
        raise ValueError('No attributable complete Original development R0 failures')
    preview = _seal({'schema_version': 1, 'source_root': str(root), 'baseline_revision': manifest['baseline_revision'],
                     'api_function_ids': apis, 'cases': cases, 'skipped': skipped,
                     'split': 'development', 'condition': 'original', 'round': 0,
                     'artifacts': list({r['path']: r for r in refs}.values())})
    output.mkdir(parents=True)
    atomic_json(output / 'preview.json', preview)
    return {'preview': str(output / 'preview.json'), 'cases': len(cases), 'skipped': len(skipped)}


def _diagnoses(value, preview):
    if not isinstance(value, dict) or set(value) != {'diagnoses'} or not isinstance(value['diagnoses'], list):
        raise ValueError('Author must return one structured diagnoses list')
    cases = {case['evidence_id']: case for case in preview['cases']}
    accepted, seen = [], set()
    fields = {'evidence_id', 'classification', 'reason', 'source_quote', 'hint', 'corrected_code'}
    for row in value['diagnoses']:
        if not isinstance(row, dict) or set(row) != fields or row.get('evidence_id') not in cases or row['evidence_id'] in seen:
            raise ValueError('Diagnosis must identify one unique supplied development case')
        seen.add(row['evidence_id'])
        if row['classification'] not in ('api_requirement', 'not_api_requirement', 'uncertain') or not isinstance(row['reason'], str) or not row['reason'].strip():
            raise ValueError('Diagnosis needs a classification and reason')
        if row['classification'] != 'api_requirement':
            if row['hint'] is not None or row['corrected_code'] not in ('', None):
                raise ValueError('Unsupported diagnosis cannot supply installable guidance')
            continue
        case, hint = cases[row['evidence_id']], row['hint']
        required = {'function_id', 'requirement_id', 'requirement', 'diagnostic', 'action', 'validation'}
        if not isinstance(hint, dict) or set(hint) != required or hint['function_id'] != case['function_id']:
            raise ValueError('Hint must address its independently attributed function')
        source_fragments = [case['facts']['source_window'],
                            *(record['text'] for record in case['facts'].get('namespace_declarations', []))]
        if (not isinstance(row['source_quote'], str) or len(row['source_quote'].strip()) < 8
                or not any(row['source_quote'] in fragment for fragment in source_fragments)):
            raise ValueError('A requirement diagnosis must cite an exact supplied source fragment')
        if not isinstance(hint['diagnostic'], str) or hint['diagnostic'] not in case['diagnostic']:
            raise ValueError('Hint diagnostic must occur in its Original R0 failure')
        if not isinstance(row['corrected_code'], str) or not row['corrected_code'].strip():
            raise ValueError('Supply a complete candidate correction for independent validation')
        accepted.append(row)
    if seen != set(cases):
        raise ValueError('Every supplied failure needs a diagnosis, including unsupported ones')
    return accepted


def propose_source_hints(preview_path, model_config, output):
    """One recorded author call; candidate annotations remain unvalidated."""
    preview = _open(preview_path)
    output = _destination(Path(preview['source_root']), output)
    settings = _model_settings(model_config)
    refs = [*preview['artifacts'], bind(preview_path), bind(model_config), bind(PROMPT)]
    refs.extend(bind(p) for p in settings['command'] if Path(p).is_file())
    context = {'cases': [{k: v for k, v in case.items() if k not in ('evidence', 'duplicate_case_ids')}
                         for case in preview['cases']]}
    request = {'system': PROMPT.read_text(), 'prompt': json.dumps(context, ensure_ascii=False),
               'model': settings['name'], 'temperature': settings['temperature'],
               'max_output_tokens': settings['max_output_tokens']}
    with ownership(output):
        process = invoke(settings['command'], request, output / 'author_attempt', settings['timeout_s'])
        refs.extend(bind(output / 'author_attempt' / p) for p in ('request.json', 'process.json', 'stdout.txt', 'stderr.txt'))
        if process.get('status') != 'ok' or not solution_state(process.get('payload') or {}).get('executable'):
            raise ValueError('Author response incomplete or failed; preserve evidence and do not prepare hints')
        _open(preview_path)
        if not all(verify_artifact(ref) for ref in refs):
            raise ValueError('Authoring inputs changed during the request')
        raw = json.loads(_body(process['payload']['code']))
        accepted = _diagnoses(raw, preview)
        atomic_json(output / 'diagnoses.json', raw)
        if not accepted:
            raise ValueError('No source-supported API requirement proposals; diagnoses preserved')
        hints = [row['hint'] for row in _group_hints(accepted)]
        paths = {hint['function_id'].rsplit(':', 2)[0] for hint in hints}
        sources = {case['facts']['path']: case['facts']['source']['sha256'] for case in preview['cases']}
        spec = {'schema_version': 1, 'api_function_ids': preview['api_function_ids'],
                'source_sha256': {path: sources[path] for path in paths}, 'hints': hints}
        atomic_json(output / 'spec.json', spec)
        prepared = prepare_source_hints(preview['source_root'], output / 'spec.json', output / 'annotated')
        refs.extend([bind(output / 'spec.json'), bind(output / 'diagnoses.json'), bind(output / 'annotated/proposal.json')])
        refs.extend(bind(p) for p in prepared['source_artifacts'])
        proposal = _seal({'schema_version': 1, 'status': 'unvalidated', 'source_root': preview['source_root'],
                          'baseline_revision': preview['baseline_revision'], 'preview': bind(preview_path),
                          'source_proposal': bind(output / 'annotated/proposal.json'),
                          'diagnoses': accepted, 'sources': prepared['sources'], 'artifacts': refs})
        atomic_json(output / 'proposal.json', proposal)
    return {'proposal': str(output / 'proposal.json'), 'hints': len(hints), 'status': 'unvalidated'}


def validate_source_hint_development(proposal_path, plan_path, output):
    """Run trusted-adapter trigger/correction/valid/nearby-negative controls."""
    proposal = _open(proposal_path)
    preview = _verified(proposal['preview'])
    plan = load(plan_path)
    if plan.get('schema_version') != 1 or plan.get('split') != 'development':
        raise ValueError('Validation plan must be explicitly development-only')
    root = Path(proposal['source_root'])
    output = _destination(root, output)
    command, timeout = plan['adapter']['command'], plan['adapter']['timeout_s']
    if not isinstance(command, list) or not command or not all(isinstance(p, str) and p for p in command) or type(timeout) is not int or timeout < 1:
        raise ValueError('Declare a trusted adapter command and positive timeout')
    refs = [*proposal['artifacts'], bind(proposal_path), bind(plan_path)]
    adapter_artifacts = plan['adapter'].get('artifacts', [])
    if not adapter_artifacts or not all(verify_artifact(ref) for ref in adapter_artifacts):
        raise ValueError('Validation adapter artifacts must be pinned')
    refs.extend(adapter_artifacts)
    refs.extend(bind(p) for p in command if Path(p).is_file())
    cases = {row['evidence_id']: row for row in preview['cases']}
    controls = plan.get('controls')
    if not isinstance(controls, dict) or set(controls) != {r['evidence_id'] for r in proposal['diagnoses']}:
        raise ValueError('Every proposed hint requires an independent validation plan')
    source_proposal = _verified(proposal['source_proposal'])
    index = index_source_hints(Path(source_proposal['output']) / 'source',
                              [row['path'] for row in proposal['sources']], preview['api_function_ids'])
    checks, expected = [], []
    with ownership(output):
        for diagnosis in proposal['diagnoses']:
            evidence_id, hint = diagnosis['evidence_id'], diagnosis['hint']
            case, control = cases[evidence_id], controls[evidence_id]
            if set(control) != {'valid_code', 'nearby_code', 'checker_context'}:
                raise ValueError('Each hint needs valid_code/nearby_code bindings and private checker_context')
            # Only the trusted validator sees these independent controls/context.
            control_code = {}
            for role, field in [('valid', 'valid_code'), ('nearby_negative', 'nearby_code')]:
                if not verify_artifact(control[field]):
                    raise ValueError('Validation control code changed')
                refs.append(control[field])
                control_code[role] = Path(control[field]['path']).read_text()
            if not verify_artifact(control['checker_context']):
                raise ValueError('Validation checker context changed')
            refs.append(control['checker_context'])
            codes = {'trigger': case['code'], 'corrected': diagnosis['corrected_code'], **control_code}
            if len(set(codes.values())) != 4:
                raise ValueError('Trigger, correction, valid and nearby-negative programs must be distinct')
            expected.append({'function_id': hint['function_id'], 'requirement_id': hint['requirement_id'], 'evidence_id': evidence_id})
            for role in ROLES:
                request = {'protocol': PROTOCOL, 'split': 'development', 'role': role,
                           'case_id': evidence_id, 'code': codes[role], 'source_root': str(root),
                           'source_revision': proposal['baseline_revision'],
                           'checker_context_path': control['checker_context']['path']}
                directory = output / evidence_id / role
                process = invoke(command, request, directory, timeout)
                refs.extend(bind(directory / name) for name in ('request.json', 'process.json', 'stdout.txt', 'stderr.txt'))
                payload, passed = _outcome(process)
                if payload.get('request_sha256') != digest(request) or payload.get('source_revision') != proposal['baseline_revision']:
                    raise ValueError('Validation result lacks request/source identity')
                previous = {'code': codes[role], 'feedback': payload['public_feedback']}
                if 'public_failure' in payload:
                    previous['public_failure'] = payload['public_failure']
                selection = select_source_hints(index, previous)
                matches = {(r['function_id'], r['requirement_id']) for r in selection['matched']}
                key = hint['function_id'], hint['requirement_id']
                valid = _valid_check(role, passed, key, matches, selection)
                checks.append({'evidence_id': evidence_id, 'function_id': key[0], 'requirement_id': key[1],
                               'role': role, 'valid': bool(valid), 'passed': passed,
                               'selection': selection, 'request': bind(directory / 'request.json'),
                               'process': bind(directory / 'process.json')})
        _open(proposal_path)
        if not all(verify_artifact(ref) for ref in refs):
            raise ValueError('Validation evidence changed during checks')
        installable = []
        if all(row['valid'] for row in checks):
            for relative, content in _validated_content(proposal).items():
                path = output / 'validated_source' / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
                binding = bind(path)
                refs.append(binding)
                baseline = next(row['baseline_sha256'] for row in proposal['sources'] if row['path'] == relative)
                installable.append({'path': relative, 'baseline_sha256': baseline, 'artifact': binding})
        result = _seal({'schema_version': 1, 'status': 'validated' if all(r['valid'] for r in checks) else 'rejected',
                       'source_root': str(root), 'baseline_revision': proposal['baseline_revision'],
                       'proposal': bind(proposal_path), 'source_proposal': proposal['source_proposal'],
                       'sources': proposal['sources'], 'expected_hints': expected,
                       'api_function_ids': preview['api_function_ids'], 'installable_sources': installable,
                       'validation_plan': bind(plan_path),
                       'checks': checks, 'artifacts': list({r['path']: r for r in refs}.values()),
                       'meaning': 'Independent development controls passed; no claim of held-out improvement.'})
        atomic_json(output / 'validation.json', result)
    return {'validation': str(output / 'validation.json'), 'status': result['status']}


def _valid_check(role, passed, key, matches, selection):
    return (passed if role in ('corrected', 'valid') else not passed and
            (key in matches if role == 'trigger' else key not in matches and
             selection['diagnosis']['status'] in ('identified', 'unresolved_function', 'ambiguous_function')))



def _group_hints(diagnoses):
    """Consolidate identical requirements while retaining every triggering case."""
    grouped = {}
    for diagnosis in diagnoses:
        hint = diagnosis['hint']
        key = hint['function_id'], hint['requirement_id']
        if key in grouped and grouped[key]['hint'] != hint:
            raise ValueError('Conflicting definitions for the same function and requirement')
        group = grouped.setdefault(key, {'hint': hint, 'evidence_ids': []})
        group['evidence_ids'].append(diagnosis['evidence_id'])
    return list(grouped.values())


def _validated_content(proposal):
    """The source log records measured development checks, not model assertions."""
    root = Path(proposal['source_root'])
    contents = {}
    for row in proposal['sources']:
        original = (root / row['path']).read_bytes()
        if hashlib.sha256(original).hexdigest() != row['baseline_sha256']:
            raise ValueError('Validated source no longer matches its baseline')
        text = original.decode('utf-8')
        for group in _group_hints(proposal['diagnoses']):
            hint = group['hint']
            if hint['function_id'].rsplit(':', 2)[0] != row['path']:
                continue
            fields = {**hint, 'status': 'validated_development',
                      'validation': 'Development checks passed: trigger reproduced; corrected and valid pass; '
                                    'nearby failure does not select this requirement. Evidence: '
                                    + ', '.join(group['evidence_ids']) + '. ' + hint['validation']}
            text = insert_source_hint(text, hint['function_id'], fields, source_path=row['path'])
        if strip_source_hints(text) != strip_source_hints(original.decode('utf-8')):
            raise ValueError('Validated source changed executable content')
        contents[row['path']] = text.encode('utf-8')
    return contents


def verify_development_validation(path):
    """Reconstruct all saved checks and exact installable bytes without rerunning."""
    result = _open(path)
    if result.get('status') != 'validated':
        raise ValueError('Only validated source hints can be installed')
    _verified(result['proposal'])
    proposal = _open(result['proposal']['path'])
    preview, plan = _verified(proposal['preview']), _verified(result['validation_plan'])
    source_proposal = _verified(proposal['source_proposal'])
    if result['source_proposal'] != proposal['source_proposal'] or result['sources'] != proposal['sources']:
        raise ValueError('Validation source proposal differs')
    if result['api_function_ids'] != preview['api_function_ids']:
        raise ValueError('Validation API mapping differs')
    index = index_source_hints(Path(source_proposal['output']) / 'source',
                              [row['path'] for row in proposal['sources']], preview['api_function_ids'])
    cases = {row['evidence_id']: row for row in preview['cases']}
    saved = {(row['evidence_id'], row['role']): row for row in result['checks']}
    expected_keys = {(row['evidence_id'], role) for row in proposal['diagnoses'] for role in ROLES}
    if set(saved) != expected_keys or len(saved) != len(result['checks']):
        raise ValueError('Missing, duplicate or unexpected development validation check')
    expected_hints = []
    for diagnosis in proposal['diagnoses']:
        identifier, hint = diagnosis['evidence_id'], diagnosis['hint']
        expected_hints.append({'function_id': hint['function_id'], 'requirement_id': hint['requirement_id'], 'evidence_id': identifier})
        control = plan['controls'][identifier]
        codes = {'trigger': cases[identifier]['code'], 'corrected': diagnosis['corrected_code'],
                 'valid': Path(control['valid_code']['path']).read_text(),
                 'nearby_negative': Path(control['nearby_code']['path']).read_text()}
        for role in ROLES:
            row = saved[identifier, role]
            request = {'protocol': PROTOCOL, 'split': 'development', 'role': role,
                       'case_id': identifier, 'code': codes[role], 'source_root': proposal['source_root'],
                       'source_revision': proposal['baseline_revision'],
                       'checker_context_path': control['checker_context']['path']}
            if _verified(row['request']) != request:
                raise ValueError('Validation request differs from its bound controls')
            payload, passed = _outcome(_verified(row['process']))
            if payload.get('request_sha256') != digest(request) or payload.get('source_revision') != proposal['baseline_revision']:
                raise ValueError('Validation process identity differs')
            previous = {'code': codes[role], 'feedback': payload['public_feedback']}
            if 'public_failure' in payload:
                previous['public_failure'] = payload['public_failure']
            selection = select_source_hints(index, previous)
            key = hint['function_id'], hint['requirement_id']
            matches = {(r['function_id'], r['requirement_id']) for r in selection['matched']}
            if not _valid_check(role, passed, key, matches, selection) or row['valid'] is not True or row['passed'] != passed or row['selection'] != selection or (row['function_id'], row['requirement_id']) != key:
                raise ValueError('Saved development check does not establish its claimed outcome')
    if result['expected_hints'] != expected_hints:
        raise ValueError('Validated hint scope changed')
    content = _validated_content(proposal)
    installed = {row['path']: row for row in result['installable_sources']}
    if set(installed) != set(content) or len(installed) != len(result['installable_sources']):
        raise ValueError('Installable source list differs')
    for relative, data in content.items():
        row = installed[relative]
        if not verify_artifact(row['artifact']) or Path(row['artifact']['path']).read_bytes() != data:
            raise ValueError('Installable source differs from validated comments')
        baseline = next(item['baseline_sha256'] for item in proposal['sources'] if item['path'] == relative)
        if row['baseline_sha256'] != baseline:
            raise ValueError('Installable baseline source differs')
    return result
