"""Native fix hints: change existing exception messages, never repair prompts.

Each proposal names one literal error message inside a known function. Only that
literal can change. Existing guards, exception classes, valid paths and all other
source bytes remain intact. Four paired development controls must validate the
candidate before installation. Compiler errors are deliberately unsupported.
"""
import ast
import json
from pathlib import Path
import re

from .ablation import bind, bytes_sha256, digest, load, seal_record, verify_artifact
from .execution import atomic_json, invoke, ownership
from .source_hints import _identity, _declaration, _python_function

PROTOCOL = 'native_hint_development_v1'
ROLES = ('trigger', 'corrected', 'valid', 'nearby_negative')
MARKER = '[AIDEAL fix:'
PROMPT = Path(__file__).resolve().parents[1] / 'prompts/native_hint_development.md'


def _open(path):
    # Check both the saved record and every referenced file before using their data.
    value = load(path)
    if value.get('sha256') != digest({k: v for k, v in value.items() if k != 'sha256'}):
        raise ValueError('Native hint record changed')
    if not all(verify_artifact(ref) for ref in value['artifacts']):
        raise ValueError('Native hint input or evidence changed')
    return value


def _new_output(root, output):
    # Resolve the requested output path and require a fresh location outside the library.
    output = Path(output).resolve()
    if output.exists() or output == root or output.is_relative_to(root):
        raise ValueError('Choose a new output outside the baseline source')
    return output


def _mask_java(text):
    # Keep offsets/newlines while hiding literals and comments before locating
    # braces and throw statements. Unsupported text blocks fail closed.
    # Reject syntax the scanner cannot safely map back to the original text.
    if '"""' in text or re.search(r'\\u+[0-9a-fA-F]{4}', text):
        raise ValueError('Text blocks and Unicode source escapes need a language adapter')
    tokens = r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
    return re.sub(tokens, lambda m: re.sub(r'[^\n]', ' ', m[0]), text)


def _literal_site(text, path, function_id, error_line):
    """Locate one literal in a real raise/throw inside the named function."""
    # Return the message span as character offsets into text, along with its decoded value.
    # The function ID names the declaration and error_line selects the statement.
    _, declaration_line, name = _identity(function_id)
    lines = text.splitlines(keepends=True)
    if type(error_line) is not int or not 1 <= error_line <= len(lines):
        raise ValueError('Invalid error statement line')
    if Path(path).suffix == '.py':
        function = _python_function(lines, declaration_line - 1, name, path)
        def nodes(node):
            # Walk the selected function body while keeping nested scopes separate.
            yield node
            for child in ast.iter_child_nodes(node):
                if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                    yield from nodes(child)
        raises = [n for n in nodes(function) if isinstance(n, ast.Raise) and n.lineno == error_line]
        if len(raises) != 1:
            raise ValueError('Expected an existing raise inside the selected function')
        call = raises[0].exc
        if (not isinstance(call, ast.Call) or len(call.args) != 1 or call.keywords
                or not isinstance(call.func, (ast.Name, ast.Attribute))
                or not isinstance(call.args[0], ast.Constant) or not isinstance(call.args[0].value, str)):
            raise ValueError('Only single literal exception messages are supported')
        literal = call.args[0]
        # AST columns are UTF-8 byte offsets, not Unicode character indices.
        offset = lambda line, col: sum(len(s) for s in lines[:line - 1]) + len(lines[line - 1].encode()[:col].decode())
        return offset(literal.lineno, literal.col_offset), offset(literal.end_lineno, literal.end_col_offset), literal.value
    if Path(path).suffix not in ('.java', '.scala'):
        raise ValueError('Native message patches currently support Python, Java and Scala')
    actual, _ = _declaration(lines, declaration_line - 1, name)
    if actual != declaration_line - 1:
        raise ValueError('Function identity differs from declaration')
    # Use the masked copy to match braces at their original character offsets.
    masked = _mask_java(text)
    start = sum(len(s) for s in lines[:actual])
    brace = masked.find('{', start)
    if brace < 0:
        raise ValueError('A braced function body is required')
    header = masked[start:brace]
    if (';' in header or re.search(r'\b(?:class|interface|enum|record|object|trait)\b', header)
            or len(re.findall(r'\bdef\b', header)) > 1
            or ('=' in header and header.split('=', 1)[1].strip())):
        raise ValueError('Declaration does not directly introduce a braced function body')
    depth, end = 1, brace + 1
    while end < len(masked) and depth:
        depth += (masked[end] == '{') - (masked[end] == '}')
        end += 1
    at = sum(len(s) for s in lines[:error_line - 1])
    at += len(lines[error_line - 1]) - len(lines[error_line - 1].lstrip())
    if depth or not brace < at < end or not masked[at:].startswith('throw new '):
        raise ValueError('Error statement is not inside the selected function')
    if re.search(r'\b(?:class|interface|enum|record|object|def)\b|->|=>', masked[brace + 1:at]):
        raise ValueError('Nested declarations or lambdas require explicit language ownership checks')
    match = re.match(r'throw\s+new\s+[\w.$]+\s*\(\s*("(?:\\.|[^"\\\n])*?")\s*\)', text[at:])
    if match is None:
        raise ValueError('Only a single literal throw message is supported')
    token = match[1]
    try:
        original = json.loads(token)
    except ValueError as exc:
        raise ValueError('Unsupported string escapes') from exc
    return at + match.start(1), at + match.end(1), original


def _message_edit(text, path, hint):
    # Check the proposed action against the exact file and original diagnostic.
    # Return the span, replacement literal, and message expected at runtime.
    relative, _, _ = _identity(hint['function_id'])
    if relative != path:
        raise ValueError('Function identity belongs to another file')
    requirement = hint['requirement_id']
    action = hint['action']
    if not isinstance(requirement, str) or re.fullmatch(r'[A-Za-z0-9_.-]+', requirement) is None:
        raise ValueError('Invalid requirement identifier')
    if not isinstance(action, str) or not action.strip() or len(action) > 1000 or any(ord(c) < 32 for c in action):
        raise ValueError('Use bounded, single-line corrective guidance')
    start, end, original = _literal_site(text, path, hint['function_id'], hint['error_line'])
    if original != hint['original_message'] or not original or MARKER in original:
        raise ValueError('Original diagnostic differs or this error site already has native guidance')
    message = original + ' ' + MARKER + requirement + '] ' + action
    # One string literal changes. No guard, exception type, argument evaluation,
    # exception cause or valid execution path is rewritten.
    replacement = json.dumps(message, ensure_ascii=True)
    return start, end, replacement, message


def patch_messages(text, path, hints):
    # Collect edits against the original text and require one consistent replacement per span.
    edits = {}
    for hint in hints:
        start, end, replacement, message = _message_edit(text, path, hint)
        key = (start, end)
        if key in edits and edits[key][0] != replacement:
            raise ValueError('Conflicting guidance for the same error site')
        edits[key] = (replacement, message)
    spans = sorted(edits)
    if any(left[1] > right[0] for left, right in zip(spans, spans[1:])):
        raise ValueError('Overlapping native error edits')
    # Apply spans from right to left to preserve the offsets of pending edits.
    edited = text
    for (start, end), (replacement, _) in sorted(edits.items(), reverse=True):
        edited = edited[:start] + replacement + edited[end:]
    if Path(path).suffix == '.py':
        ast.parse(edited)
    return edited


def patch_message(text, path, hint):
    # Return both the edited source and the diagnostic expected from this single hint.
    return patch_messages(text, path, [hint]), _message_edit(text, path, hint)[3]


def prepare_native_hints(source_root, spec_path, output):
    # Check a development hint specification against the exact baseline source.
    # Append guidance only to a supported existing exception message.
    # Write candidate source copies and an unvalidated proposal outside the library.
    # Do not alter the original checkout or claim that the hint has been tested.
    """Prepare message-only source copies; never modify a library checkout."""
    # Use the supplied source hashes to check that each diagnosis refers to this checkout.
    root = Path(source_root).resolve(strict=True)
    output = _new_output(root, output)
    spec = load(spec_path)
    if spec.get('schema_version') != 1 or spec.get('split') != 'development':
        raise ValueError('Use an explicit development-only native hint specification')
    hints = spec.get('hints')
    if not isinstance(hints, list) or not 1 <= len(hints) <= 100:
        raise ValueError('Supply 1 to 100 supported runtime hints')
    refs, sources, records, grouped = [bind(spec_path), bind(__file__),
                                     bind(Path(__file__).with_name('source_hints.py'))], [], [], {}
    for hint in hints:
        relative, _, _ = _identity(hint['function_id'])
        source = root / relative
        resolved = source.resolve(strict=True)
        if not resolved.is_relative_to(root) or source.is_symlink() or source.stat().st_size > 2_000_000:
            raise ValueError('Unsafe or oversized source')
        for field in ('evidence_id', 'trigger_code', 'corrected_code', 'source_quote'):
            if not isinstance(hint.get(field), str) or not hint[field].strip():
                raise ValueError('Native proposal needs ' + field)
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', hint['evidence_id']):
            raise ValueError('Unsafe development evidence ID')
        data = source.read_bytes()
        if spec['source_sha256'].get(relative) != bytes_sha256(data):
            raise ValueError('Baseline source changed')
        text = data.decode('utf-8')
        if hint['source_quote'] not in text:
            raise ValueError('Diagnosis must cite supplied source')
        message = _message_edit(text, relative, hint)[3]
        grouped.setdefault(relative, []).append(hint)
        records.append({**hint, 'emitted_message': message})
    # Combine the message edits per file before saving copies and their file references.
    for relative, entries in grouped.items():
        source = root / relative
        edited = patch_messages(source.read_bytes().decode(), relative, entries)
        sources.append({'path': relative, 'baseline': bind(source), 'candidate_sha256': bytes_sha256(edited.encode()),
                        'candidate_text': edited})
        refs.append(bind(source))
    if set(spec['source_sha256']) != set(grouped):
        raise ValueError('Source hashes must identify exactly the modified files')
    with ownership(output):
        for source in sources:
            path = output / 'source' / source['path']
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(source.pop('candidate_text').encode())
            source['candidate'] = bind(path)
            refs.append(source['candidate'])
        result = seal_record({'schema_version': 1, 'status': 'unvalidated', 'delivery': 'native_exception_message',
                        'source_root': str(root), 'hints': records, 'sources': sources, 'artifacts': refs})
        atomic_json(output / 'proposal.json', result)
    return {'proposal': str(output / 'proposal.json'), 'status': 'unvalidated'}


def propose_native_hints(preview_path, model_config, output):
    # Send the verified Original failure preview to the configured author model.
    # Require each supplied case to produce a supported hint or be marked unsupported.
    # Save the diagnosis and prepare source candidates for supported exceptions.
    # Candidate edits still require paired execution checks before installation.
    """One explicit model call from the existing Original R0 evidence preview."""
    # Open the saved preview and pass the configured model only the cases needed for authoring.
    from .source_hint_development import _open as open_preview
    from .improvement_suggestions import _model_settings
    from .response_status import solution_state
    preview = open_preview(preview_path)
    if not preview['cases']:
        return {'status': 'no_supported_runtime_hints', 'preview': str(preview_path), 'llm_calls': 0}
    output = _new_output(Path(preview['source_root']), output)
    settings = _model_settings(model_config)
    cases = {case['evidence_id']: case for case in preview['cases']}
    request = {'system': PROMPT.read_text(), 'prompt': json.dumps({'cases': [
        {k: v for k, v in case.items() if k not in ('evidence', 'duplicate_case_ids')}
        for case in cases.values()]}), 'model': settings['name'], 'temperature': settings['temperature'],
        'max_output_tokens': settings['max_output_tokens']}
    with ownership(output):
        process = invoke(settings['command'], request, output / 'author', settings['timeout_s'])
        if process.get('status') != 'ok' or not solution_state(process.get('payload') or {}).get('executable'):
            raise ValueError('Incomplete native hint author response')
        raw = process['payload']['code'].strip()
        if raw.startswith('```'):
            raw = re.sub(r'^```[^\n]*\n|\n```$', '', raw)
        value = json.loads(raw)
        if set(value) != {'hints', 'unsupported_evidence_ids'}:
            raise ValueError('Expected hints and unsupported_evidence_ids')
        seen = list(value['unsupported_evidence_ids'])
        hints, hashes = [], {}
        for row in value['hints']:
            identifier = row['evidence_id']
            case = cases[identifier]
            if row['function_id'] != case['function_id'] or row['original_message'] not in case['diagnostic']:
                raise ValueError('Native hint does not match observed function and error')
            if row['source_quote'] not in case['facts']['source_window']:
                raise ValueError('Model cited source outside supplied evidence')
            seen.append(identifier)
            hints.append({**row, 'trigger_code': case['code']})
            hashes[case['facts']['path']] = case['facts']['source']['sha256']
        # Account for each input case exactly once, including cases marked unsupported.
        if len(seen) != len(set(seen)) or set(seen) != set(cases):
            raise ValueError('Each evidence case must be proposed or explicitly unsupported')
        open_preview(preview_path)
        atomic_json(output / 'diagnoses.json', value)
        if not hints:
            return {'status': 'no_supported_runtime_hints', 'diagnoses': str(output / 'diagnoses.json')}
        atomic_json(output / 'spec.json', {'schema_version': 1, 'split': 'development',
                                         'source_sha256': hashes, 'hints': hints})
        result = prepare_native_hints(preview['source_root'], output / 'spec.json', output / 'prepared')
        proposal = _open(result['proposal'])
        proposal['artifacts'] += [bind(preview_path), *preview['artifacts'], bind(model_config), bind(PROMPT),
                                  bind(output / 'author/request.json'), bind(output / 'author/process.json')]
        proposal.pop('sha256')
        atomic_json(Path(result['proposal']), seal_record(proposal))
        return result


def _validation_inputs(proposal, plan):
    # Build a request for each of four controls on each source variant.
    # Keep the pinned adapter and control files as evidence for replay.
    if plan.get('schema_version') != 1 or plan.get('split') != 'development':
        raise ValueError('Validation must use development controls')
    identifiers = [h['evidence_id'] for h in proposal['hints']]
    if len(set(identifiers)) != len(identifiers) or set(plan['controls']) != set(identifiers):
        raise ValueError('Every hint needs one independent validation plan')
    adapter = plan['adapter']
    if (not isinstance(adapter['command'], list) or not adapter['command']
            or type(adapter['timeout_s']) is not int or adapter['timeout_s'] <= 0
            or not adapter.get('artifacts') or not all(verify_artifact(r) for r in adapter['artifacts'])):
        raise ValueError('Pin a trusted execution adapter with a positive timeout')
    refs, requests = list(adapter['artifacts']), []
    for hint in proposal['hints']:
        control = plan['controls'][hint['evidence_id']]
        for field in ('valid_code', 'nearby_code', 'checker_context'):
            if not verify_artifact(control[field]):
                raise ValueError('Validation control changed')
            refs.append(control[field])
        codes = {'trigger': hint['trigger_code'], 'corrected': hint['corrected_code'],
                 'valid': Path(control['valid_code']['path']).read_text(),
                 'nearby_negative': Path(control['nearby_code']['path']).read_text()}
        if len(set(codes.values())) != 4:
            raise ValueError('Four distinct validation programs are required')
        for role, code in codes.items():
            for variant in ('baseline', 'candidate'):
                overrides = {s['path']: s['candidate'] for s in proposal['sources']} if variant == 'candidate' else {}
                request = {'protocol': PROTOCOL, 'case_id': hint['evidence_id'], 'role': role, 'variant': variant,
                           'code': code, 'source_root': proposal['source_root'], 'source_overrides': overrides,
                           'source_bindings': [s['baseline'] for s in proposal['sources']],
                           'checker_context_path': control['checker_context']['path']}
                requests.append((hint, role, variant, request))
    return refs, requests


def _payload(process, request):
    # Accept a checker payload only when it identifies this request and reports explicit outcomes.
    p = process.get('payload')
    if (process.get('status') != 'ok' or not isinstance(p, dict) or p.get('request_sha256') != digest(request)
            or any(type(p.get(k)) is not bool for k in ('execution_pass', 'oracle_pass', 'target_reached'))
            or not all(isinstance(p.get(k), str) for k in ('public_feedback', 'error_type', 'error_message'))):
        raise ValueError('Adapter must bind explicit outcomes and native error fields to its request')
    return p


def _check_pair(hint, role, base, candidate):
    # For passing controls, compare output hashes. For failing controls, compare
    # exception types and check where the hint appears in the diagnostic.
    passed = lambda p: all(p[k] for k in ('execution_pass', 'oracle_pass', 'target_reached'))
    if role in ('corrected', 'valid'):
        return (passed(base) and passed(candidate) and
                re.fullmatch(r'[0-9a-f]{64}', base.get('result_sha256', '')) is not None and
                base['result_sha256'] == candidate.get('result_sha256') and
                all(not p['error_type'] and not p['error_message'] for p in (base, candidate)))
    if base['execution_pass'] or candidate['execution_pass'] or not base['error_type'] or base['error_type'] != candidate['error_type']:
        return False
    if role == 'trigger':
        return (base['error_message'] == hint['original_message'] and
                candidate['error_message'] == hint['emitted_message'] and
                hint['emitted_message'] in candidate['public_feedback'] and MARKER not in base['public_feedback'])
    return (base['error_message'] == candidate['error_message'] and
            all(MARKER not in p['public_feedback'] and MARKER not in p['error_message'] for p in (base, candidate)))


def validate_native_hints(proposal_path, plan_path, output):
    # Run four distinct control programs on both baseline and candidate sources.
    # Check the intended hint, corrected/valid results and an unrelated error.
    # Save execution receipts; validation succeeds only when every pair passes.
    # The supplied adapter owns compilation and execution; no model is called.
    # Use the saved proposal and independent plan to determine every required execution.
    proposal, plan = _open(proposal_path), load(plan_path)
    output = _new_output(Path(proposal['source_root']), output)
    refs, requests = _validation_inputs(proposal, plan)
    refs += [bind(proposal_path), *proposal['artifacts'], bind(plan_path)]
    records, payloads = [], {}
    with ownership(output):
        for hint, role, variant, request in requests:
            directory = output / hint['evidence_id'] / role / variant
            process = invoke(plan['adapter']['command'], request, directory, plan['adapter']['timeout_s'])
            payloads[(hint['evidence_id'], role, variant)] = _payload(process, request)
            record = {'case_id': hint['evidence_id'], 'role': role, 'variant': variant,
                      'request': bind(directory / 'request.json'), 'process': bind(directory / 'process.json')}
            records.append(record)
            refs.extend([record['request'], record['process']])
        checks = [{'case_id': h['evidence_id'], 'role': role, 'valid': bool(_check_pair(h, role,
                   payloads[(h['evidence_id'], role, 'baseline')], payloads[(h['evidence_id'], role, 'candidate')]))}
                  for h in proposal['hints'] for role in ROLES]
        if not all(verify_artifact(r) for r in refs):
            raise ValueError('Development inputs changed during validation')
        result = seal_record({'schema_version': 1, 'protocol': PROTOCOL,
                        'status': 'validated' if all(c['valid'] for c in checks) else 'rejected',
                        'proposal': bind(proposal_path), 'plan': bind(plan_path),
                        'checks': checks, 'records': records, 'artifacts': refs})
        atomic_json(output / 'validation.json', result)
    return {'validation': str(output / 'validation.json'), 'status': result['status']}


def verify_native_validation(path):
    # Reconstruct the requests and verdicts from saved evidence before allowing installation.
    result = _open(path)
    if result.get('status') != 'validated' or result.get('protocol') != PROTOCOL:
        raise ValueError('Native message hints require successful development validation')
    proposal, plan = _open(result['proposal']['path']), load(result['plan']['path'])
    _, requests = _validation_inputs(proposal, plan)
    expected = {(h['evidence_id'], role, variant): (h, request) for h, role, variant, request in requests}
    payloads = {}
    for row in result['records']:
        key = row['case_id'], row['role'], row['variant']
        if key not in expected or key in payloads or load(row['request']['path']) != expected[key][1]:
            raise ValueError('Missing or changed native validation request')
        payloads[key] = _payload(load(row['process']['path']), expected[key][1])
    if set(payloads) != set(expected):
        raise ValueError('Missing native validation executions')
    checks = [{'case_id': h['evidence_id'], 'role': role, 'valid': bool(_check_pair(h, role,
               payloads[(h['evidence_id'], role, 'baseline')], payloads[(h['evidence_id'], role, 'candidate')]))}
              for h in proposal['hints'] for role in ROLES]
    if checks != result['checks'] or not all(c['valid'] for c in checks):
        raise ValueError('Native validation does not establish its claimed outcomes')
    for source in proposal['sources']:
        hints = [h for h in proposal['hints'] if _identity(h['function_id'])[0] == source['path']]
        edited = patch_messages(Path(source['baseline']['path']).read_bytes().decode(), source['path'], hints)
        if edited.encode() != Path(source['candidate']['path']).read_bytes():
            raise ValueError('Candidate changed code beyond the exception message')
    return proposal


def install_native_hints(validation_path, target):
    # Recheck successful validation and exact source in a separate clean checkout.
    # Copy the validated message edits and save the provenance receipt.
    # Leave changes uncommitted for review, commit and rebuild before evaluation.
    """Install into an explicitly supplied clean checkout, never the baseline.

    The user owns branch creation and committing. No historical study is edited
    implicitly. A receipt is private provenance, not an audience hint store.
    """
    # Replay the validation before checking the target. The installed receipt links the
    # source changes to the development checks.
    from .treatment_versions import _run, _check_worktree
    proposal = verify_native_validation(validation_path)
    root = Path(target).resolve(strict=True)
    if root == Path(proposal['source_root']) or Path(_run(root, 'rev-parse', '--show-toplevel')).resolve() != root:
        raise ValueError('Use a separate Git checkout, not the development baseline')
    _check_worktree(root, _run(root, 'rev-parse', 'HEAD'), {})
    receipt = root / '.aideal/treatments/native_hints_validation.json'
    if receipt.exists() or (root / '.aideal/treatments/error_hints.json').exists():
        raise ValueError('Use a fresh checkout without earlier hint treatments')
    for source in proposal['sources']:
        path = root / source['path']
        if path.is_symlink() or not path.resolve().is_relative_to(root) or bytes_sha256(path.read_bytes()) != source['baseline']['sha256']:
            raise ValueError('Target does not match the validated source baseline')
    # Start copying only after every target file matches its validated baseline.
    for source in proposal['sources']:
        (root / source['path']).write_bytes(Path(source['candidate']['path']).read_bytes())
    atomic_json(receipt, {'delivery': 'native_exception_message', 'validation': bind(validation_path)})
    return {'status': 'installed_uncommitted', 'target': str(root), 'receipt': str(receipt),
            'sources': [s['path'] for s in proposal['sources']]}


def native_feedback_receipt(feedback):
    """Observe markers already in execution feedback; never retrieve or add text."""
    # Collect distinct requirement IDs visible in the public error text for the run record.
    identifiers = sorted(set(re.findall(r'\[AIDEAL fix:([A-Za-z0-9_.-]+)\]', feedback)))
    return {'delivery': 'native_execution_feedback', 'observed_requirement_ids': identifiers,
            'guidance_retrieved': False, 'separate_hint_characters': 0,
            'evidence_note': 'Markers in public feedback are observations, not proof of repair or source attribution.'}
