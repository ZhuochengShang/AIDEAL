"""Generate reviewable alias source and function-specific hints from explicit inputs."""
import ast
import json
import math
from pathlib import Path
import re
import shutil

from .ablation import bind, digest, load, verify_artifact
from .evaluation_setup import assert_review_released
from .execution import atomic_json, invoke
from .improvement_context import alias_target, original_checkout, development_destination
from .preparation import _engine_config_module
from .refactor_proposals import validate_refactors

PROMPT = Path(__file__).resolve().parents[1] / 'prompts/improvement_suggestions.md'


def _text(value, field, empty=False):
    if not isinstance(value, str) or (not empty and not value.strip()):
        raise ValueError(field + ' must be ' + ('text' if empty else 'nonempty text'))
    return value


def _model_settings(path):
    config = _engine_config_module().yaml.safe_load(Path(path).read_text())
    if not isinstance(config, dict) or not isinstance(config.get('model'), dict):
        raise ValueError('Model configuration needs a model mapping')
    model = config['model']
    _text(model.get('name'), 'model.name')
    command = model.get('command')
    if not isinstance(command, list) or not command or any(not isinstance(c, str) or not c for c in command):
        raise ValueError('model.command must be a nonempty argument list')
    for field in ('max_output_tokens', 'timeout_s'):
        if type(model.get(field)) is not int or model[field] <= 0:
            raise ValueError(f'model.{field} must be a positive integer')
    temperature = model.get('temperature', 0)
    if type(temperature) not in (int, float) or not math.isfinite(temperature) or temperature < 0:
        raise ValueError('model.temperature must be finite and nonnegative')
    return {**model, 'temperature': temperature}


def proposal_response_error(result, model=None):
    """Do not install syntactically valid partial/refused provider suggestions."""
    payload = result.get('payload')
    if result.get('status') != 'ok' or not isinstance(payload, dict):
        return 'provider_attempt_failed'
    if not isinstance(payload.get('code'), str) or not payload['code'].strip():
        return 'provider_empty_or_invalid_output'
    status = payload.get('response_status')
    if ((status is not None and status != 'completed') or payload.get('truncated')
            or payload.get('incomplete_reason')):
        return 'provider_incomplete_or_noncompleted'
    if payload.get('refusals') or payload.get('response_kind') in ('refusal', 'empty_model_output'):
        return 'provider_refusal_or_empty_output'
    if model == 'gpt-5.3-codex':
        if status != 'completed':
            return 'provider_completion_status_missing'
        if not isinstance(payload.get('budget'), dict) or payload['budget'].get('state') != 'settled':
            return 'provider_usage_unsettled'
    return None


def validate_suggestions(value, context, *, reserved_names=None):
    """Validate referential/schema integrity, without claiming code correctness."""
    if not isinstance(value, dict):
        raise ValueError('Model suggestions must be a JSON object')
    expected = {'aliases', 'alias_code', 'alias_interface', 'hints', 'notes'}
    if set(value) not in (expected, expected | {'refactors'}):
        raise ValueError('Model response must contain aliases, alias_code, alias_interface, hints, notes and optional refactors')
    value = {**value, 'refactors': value.get('refactors', [])}
    functions = {row['id']: row for row in context['apis']}
    evidence = {row['id']: row for row in context['development_errors']}
    aliases, hints = value['aliases'], value['hints']
    if not isinstance(aliases, list) or len(aliases) > 20 or not isinstance(hints, list) or len(hints) > 100:
        raise ValueError('aliases/hints must be bounded lists')
    for field in ('alias_code', 'alias_interface', 'notes'):
        _text(value[field], field, empty=True)
    names = set()
    original_names = {row['name'] for row in functions.values()} | set(reserved_names or [])
    for alias in aliases:
        if not isinstance(alias, dict) or set(alias) != {'name', 'target_function', 'rationale'}:
            raise ValueError('Invalid alias record')
        name = _text(alias['name'], 'alias.name')
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', name) or name in names or name in original_names:
            raise ValueError('Alias name must be a distinct new identifier')
        names.add(name)
        if _text(alias['target_function'], 'target_function') not in functions:
            raise ValueError('Alias target was not in the model input')
        _text(alias['rationale'], 'alias.rationale')
    if aliases:
        if alias_target(context['alias_destination']) is None:
            raise ValueError('No alias destination was requested')
        _text(value['alias_code'], 'alias_code')
        _text(value['alias_interface'], 'alias_interface')
        if context['alias_destination'].endswith('.py'):
            tree = ast.parse(value['alias_code'])
            defined = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
            if not names <= defined:
                raise ValueError('Python alias source does not define each proposed name')
    elif value['alias_code'].strip() or value['alias_interface'].strip():
        raise ValueError('Alias source/interface supplied without alias records')
    for hint in hints:
        required = {'function_id', 'evidence_ids', 'error_contains', 'likely_cause',
                    'fix_steps', 'suggested_fix_code', 'validation'}
        if not isinstance(hint, dict) or set(hint) != required:
            raise ValueError('Invalid hint record')
        if _text(hint['function_id'], 'function_id') not in functions:
            raise ValueError('Hint function was not in the model input')
        refs = hint['evidence_ids']
        if not isinstance(refs, list) or not refs or any(not isinstance(r, str) or r not in evidence for r in refs):
            raise ValueError('Hint must cite supplied development evidence')
        if any(evidence[r]['function_id'] != hint['function_id'] for r in refs):
            raise ValueError('Hint evidence belongs to a different function')
        pattern = _text(hint['error_contains'], 'error_contains')
        if any(pattern not in evidence[r]['error'] for r in refs):
            raise ValueError('Hint match text must occur in every cited diagnostic')
        for field in ('likely_cause', 'validation'):
            _text(hint[field], field)
        _text(hint['suggested_fix_code'], 'suggested_fix_code', empty=True)
        if not isinstance(hint['fix_steps'], list) or not hint['fix_steps']:
            raise ValueError('Hint needs concrete fix_steps')
        for step in hint['fix_steps']:
            _text(step, 'fix_steps')
    validate_refactors(value['refactors'], functions)
    return value


def _load_preview(preview_path):
    """Revalidate the pinned source and development inputs before any request."""
    preview_path = Path(preview_path).resolve()
    preview = load(preview_path)
    expected = preview.get('preview_sha256')
    if expected != digest({k: v for k, v in preview.items() if k != 'preview_sha256'}):
        raise ValueError('Development preview changed')
    study, root, attachment = original_checkout(preview['study'])
    assert_review_released(study)
    if preview['baseline_revision'] != attachment['revision'] or preview['source_root'] != str(root):
        raise ValueError('Preview does not match the attached baseline')
    if not all(verify_artifact(ref) for ref in preview['artifacts']):
        raise ValueError('Preview input artifacts changed; build a new preview')
    return preview, study, attachment


def propose_improvements(preview_path, model_config, output, *, readme=None):
    """One recorded model request, producing a complete unvalidated treatment bundle.

    Nothing is installed by this command. Existing provider command contract is
    reused: stdout JSON with a `code` string containing the suggestion JSON.
    """
    preview, study, attachment = _load_preview(preview_path)
    settings = _model_settings(model_config)
    readme_ref = bind(readme) if readme else None
    output = development_destination(study, output)
    output.mkdir(parents=True, exist_ok=False)
    atomic_json(output / 'preview.json', preview)
    atomic_json(output / 'model_configuration_identity.json', bind(model_config))
    request = {'system': PROMPT.read_text(), 'prompt': json.dumps(preview['context'], ensure_ascii=False, indent=2),
               'model': settings['name'], 'temperature': settings['temperature'],
               'max_output_tokens': settings['max_output_tokens']}
    # invoke stores exact system/user messages and full adapter stdout/stderr.
    result = invoke(settings['command'], request, output / 'model_attempt', settings['timeout_s'])
    error = proposal_response_error(result, settings['name'])
    if error:
        atomic_json(output / 'model_attempt/rejected.json', {'status': 'invalid_provider_response', 'reason': error})
        raise ValueError('Development model response rejected: ' + error + '; attempt evidence is preserved')
    return _finish_proposal(preview, attachment, output, result, readme_ref, output / 'model_attempt')


def _finish_proposal(preview, attachment, output, result, readme_ref, attempt):
    """Persist review artifacts from a recorded result; never install or execute them."""
    if proposal_response_error(result):
        raise ValueError('Incomplete, refused or invalid proposal response')
    if not all(verify_artifact(ref) for ref in preview['artifacts']):
        raise ValueError('Source changed during generation; do not install these suggestions')
    original_checkout(preview['study'])
    suggestions = validate_suggestions(json.loads(result['payload']['code']), preview['context'])
    atomic_json(output / 'suggestions.json', suggestions)
    batch_id = preview['context'].get('batch_id')
    aliases = [{**row, 'alias_id': digest(row)[:20], 'source_batch': batch_id} for row in suggestions['aliases']]
    hints = [{**row, 'hint_id': digest(row)[:20], 'source_batch': batch_id} for row in suggestions['hints']]
    artifacts = {}
    if readme_ref:
        if not verify_artifact(readme_ref):
            raise ValueError('Supplied README changed during generation')
        shutil.copyfile(readme_ref['path'], output / 'README.md')
        artifacts['readme'] = bind(output / 'README.md')
    if suggestions['aliases']:
        target = preview['context']['alias_destination']
        code = output / ('alias_source' + Path(target).suffix)
        code.write_text(suggestions['alias_code'])
        interface = output / 'ALIASES.md'
        interface.write_text(suggestions['alias_interface'])
        artifacts['alias'] = {**bind(code), 'target': target}
        artifacts['alias_interface'] = {**bind(interface), 'source_batch': batch_id,
                                        'alias_ids': [row['alias_id'] for row in aliases]}
    if suggestions['hints']:
        path = output / 'error_hints.json'
        atomic_json(path, {'schema_version': 1, 'status': 'unverified',
                          'source': 'development evidence only',
                          'hints': [{**row, 'status': 'unverified'} for row in hints]})
        artifacts['error_hints'] = bind(path)
        # A companion per-function log connects each suggestion to the exact
        # development record; existing error logs and evaluation records are immutable.
        (output / 'function_fix_hints.jsonl').write_text(''.join(
            json.dumps({'function': row['function_id'], 'status': 'suggested_unverified', **row}, ensure_ascii=False) + '\n'
            for row in hints))
    refactors = None
    if suggestions['refactors']:
        path = output / 'refactor_suggestions.json'
        atomic_json(path, {'schema_version': 1, 'status': 'unverified_review_candidates',
                          'preview_sha256': preview['preview_sha256'],
                          'source_batch': preview['context'].get('batch_id'),
                          'refactors': [{**row, 'refactor_id': digest(row)[:20], 'status': 'unverified'}
                                        for row in suggestions['refactors']]})
        refactors = bind(path)
    if not artifacts and not refactors:
        return {'status': 'no_supported_suggestions', 'output': str(output), 'notes': suggestions['notes'], 'llm_calls': 1}
    proposal = {'schema_version': 1, 'baseline_revision': attachment['revision'],
                'study': preview['study'], 'status': 'proposed_unvalidated', 'artifacts': artifacts,
                'preview_sha256': preview['preview_sha256'], 'aliases': aliases, 'notes': suggestions['notes'],
                'model_attempt': bind(attempt / 'process.json'),
                'request': bind(attempt / 'request.json'),
                'scope': preview['context']['coverage'], 'requires_validation': True,
                'source_batch': preview['context'].get('batch_id'), 'refactor_suggestions': refactors}
    if not artifacts:
        proposal['status'] = 'review_candidates_only'
    atomic_json(output / 'proposal.json', proposal)
    return {'status': proposal['status'], 'proposal': str(output / 'proposal.json'),
            'alias_count': len(suggestions['aliases']), 'hint_count': len(suggestions['hints']),
            'refactor_count': len(suggestions['refactors']), 'llm_calls': 1}


def matching_fix_hints(bundle, function_id, error):
    """Return only same-function literal matches; hints never become verified here."""
    return [{**hint, 'status': 'unverified'} for hint in bundle.get('hints', [])
            if hint.get('function_id') == function_id and isinstance(hint.get('error_contains'), str)
            and hint['error_contains'] and hint['error_contains'] in error]
