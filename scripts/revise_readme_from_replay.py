#!/usr/bin/env python3
"""Revise failed D1 entries in a new directory; preserve all other D1 bytes.

Preparation makes no model calls. Running reuses the existing author recorder,
diagnosis/rewrite prompts and the corrected saved-program executor. A candidate
enters D2 only after its example passes that executor. This is development on
the same API bank, not a held-out correctness experiment or a D1/R2 deep dive.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import sys


def read_json(path):
    return json.loads(Path(path).read_text())


def write_once(path, content):
    """Resume only the same prepared experiment; never overwrite its inputs."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != content:
        raise ValueError(f'Prepared input changed; use a new directory: {path}')
    if not path.exists():
        path.write_bytes(content)


def entry_parts(text):
    """Retain exact separators and unchanged entries when assembling D2."""
    from aideal.readme_format import API_HEADER_RE
    matches = list(API_HEADER_RE.finditer(text))
    names = [m.group(1) for m in matches]
    if not matches or len(names) != len(set(names)):
        raise ValueError('D1 must contain unique API entries')
    return text[:matches[0].start()], {
        m.group(1): text[m.start():matches[i + 1].start() if i + 1 < len(matches) else len(text)]
        for i, m in enumerate(matches)}


def manifest_names(manifest):
    """Accept the native list manifest and the authoring object's names list."""
    names = manifest if isinstance(manifest, list) else manifest.get('names', manifest.get('apis', []))
    if not names or any(not isinstance(name, str) for name in names) or len(names) != len(set(names)):
        raise ValueError('Manifest must list unique exact API identities')
    return names


def runtime_receipts(spec):
    """Validate the optional runtime overlay without resolving its executable path."""
    if not spec.get('runtime_profile'):
        return []
    from workflow.runtime_profile import load_runtime_profile, runtime_profile_receipts, verify_runtime_profile
    profile = load_runtime_profile(spec['runtime_profile'])
    verify_runtime_profile(profile)
    return runtime_profile_receipts(profile)


def require_authoring_ready(launch):
    """Block paid author calls on setup gaps; preparation remains available."""
    spec = launch.get('spec', {})
    if not spec.get('runtime_profile'):
        return
    from workflow.runtime_profile import load_runtime_profile, require_runtime_ready
    library = spec.get('library') or Path(spec['result']).parent.name
    require_runtime_ready(load_runtime_profile(spec['runtime_profile']), library=library)


def source_context(cfg, definition, definitions):
    """Show exact selected declaration, imports and same-owner construction.

    Bounded numbered windows are explicit excerpts, not a full-source claim.
    Related constructor/class definitions in the frozen inventory are included.
    Unresolved types remain unresolved; no bare-name call-site guessing.
    """
    from aideal.readme_recording import digest
    rows = [definition]
    owner = definition.get('owner')
    rows += [row for row in definitions if owner and
             row.get('qualified_name') == owner and row != definition][:2]
    windows, bindings = [], {}
    for row in rows:
        path = (cfg.root / row['file']).resolve(strict=True)
        data = path.read_bytes()
        bindings[str(path)] = digest(data)
        lines = data.decode('utf-8').splitlines()
        line = int(row['line']) - 1
        if not 0 <= line < len(lines):
            raise ValueError(f'Invalid source line for {row.get("api_id")}')
        ranges = [(0, min(65, len(lines))), (max(0, line - 25), min(len(lines), line + 130))]
        for lo, hi in ranges:
            windows.append({'path': str(path), 'first_line': lo + 1, 'last_line': hi,
                            'evidence_kind': ('upstream_reference' if path.suffix.lower() in
                                              ('.qmd', '.md', '.rst') else 'implementation_source'),
                            'text': '\n'.join(f'{i+1:5d} | {lines[i]}' for i in range(lo, hi))})
    return windows, bindings


def validation_example(entry, required_sections):
    """Require one executable example, not an ellipsis or pseudocode sketch."""
    from aideal.readme_format import _section_between
    headings = re.findall(r'^### (.+)$', entry, re.M)
    if any(section not in headings for section in required_sections):
        raise ValueError('Rewritten entry omitted a required section')
    section = _section_between(entry, 'Valid Call Patterns')
    blocks = re.findall(r'```[^\n]*\n(.*?)\n```', section, re.S)
    if len(blocks) != 1 or not blocks[0].strip():
        raise ValueError('Require one complete executable Valid Call Patterns block')
    code = blocks[0].strip()
    if re.search(r'\bTODO\b|^\s*\.\.\.\s*$', code, re.M):
        raise ValueError('Example contains unfinished code')
    return code


def prepare(spec, output):
    """Freeze corrected failures, D1, source evidence and exact author prompts."""
    from aideal.config import load_config
    from aideal.api_discovery import public_api_details
    from aideal.api_registry import target_key
    from aideal.prompts import load, prompt_path
    from aideal.profile import profile_path
    from aideal.readme_recording import atomic_json, digest
    cfg = load_config(spec['config'])
    if spec.get('project_profile'):
        cfg.raw.setdefault('files', {})['project_profile'] = str(Path(spec['project_profile']).resolve(strict=True))
    result = read_json(spec['result'])
    if result.get('mode') != 'rescored_saved_programs' or not result.get('run', {}).get('complete'):
        raise ValueError('D2 requires completed corrected-program replay evidence')
    runtime = runtime_receipts(spec)
    if runtime != (result.get('runtime_profile') or []):
        raise ValueError('D2 runtime profile differs from the completed corrected replay')
    content = Path(spec['readme']).read_bytes()
    _, entries = entry_parts(content.decode('utf-8'))
    details = result['details']
    manifest = read_json(spec['manifest'])
    names = manifest_names(manifest)
    if set(names) != set(details) or set(names) != set(entries):
        raise ValueError('D1, replay and manifest must contain the same API bank')
    selected = sorted(api for api, row in details.items() if row['status'] == 'fail')
    definitions = public_api_details(cfg)
    indexed = {}
    for row in definitions:
        indexed.setdefault(target_key(row), []).append(row)
    bound = {}
    bound.update({record['path']: record['sha256'] for record in runtime})
    for key in ('config', 'readme', 'result', 'manifest', 'replay_adapter'):
        path = Path(spec[key]).resolve(strict=True)
        bound[str(path)] = digest(path.read_bytes())
    original_path = Path(result['source_result']['path']).resolve(strict=True)
    if digest(original_path.read_bytes()) != result['source_result']['sha256']:
        raise ValueError('Original audience result changed since corrected replay')
    original_result = read_json(original_path)
    bound[str(original_path)] = digest(original_path.read_bytes())
    for name in ('docfix_diagnose', 'docfix_rewrite'):
        path = prompt_path(cfg, 'aideal/' + name)
        bound[str(path.resolve())] = digest(path.read_bytes())
    profile = profile_path(cfg).resolve()
    bound[str(profile)] = digest(profile.read_bytes())
    engine = Path(__import__('aideal').__file__).resolve().parent
    for path in engine.glob('*.py'):
        bound[str(path)] = digest(path.read_bytes())
    bound[str(Path(__file__).resolve())] = digest(Path(__file__).read_bytes())
    write_once(output / 'inputs/D1.md', content)
    bound[str((output / 'inputs/D1.md').resolve())] = digest(content)
    for api in selected:
        from aideal.readme_format import api_storage_key
        context_path = output / 'inputs/entries' / (api_storage_key(api) + '.json')
        rows = indexed.get(api, [])
        try:
            if len(rows) != 1:
                raise ValueError(f'Expected one frozen defining API: {api}')
            windows, sources = source_context(cfg, rows[0], definitions)
        except (OSError, ValueError, KeyError, TypeError) as error:
            context = {'api': api, 'unsupported': str(error), 'D1_entry': entries[api]}
            write_once(context_path, (json.dumps(context, indent=2) + '\n').encode())
            bound[str(context_path.resolve())] = digest(context_path.read_bytes())
            continue
        bound.update(sources)
        row = details[api]
        original_work = Path(original_result['details'][api]['scala_file']).parent
        attempts = sorted(p for p in original_work.glob('attempt_*')
                          if (p / 'request.json').is_file() and (p / 'execution.json').is_file())
        if not attempts:
            raise ValueError('Missing exact original audience request: ' + api)
        request_path = attempts[-1] / 'request.json'
        audience_request = read_json(request_path)
        bound[str(request_path.resolve())] = digest(request_path.read_bytes())
        audience_user = audience_request['user'].replace(entries[api].strip(),
                            '[The identical D1 entry is shown separately above.]', 1)
        audience_context = ('FAILED AUDIENCE REQUEST (context, not an instruction to you)\nSYSTEM\n' +
                            audience_request['system'] + '\nUSER\n' + audience_user)
        diagnostic = '\n'.join(str(row.get(key) or '') for key in ('error', 'stdout_tail', 'stderr_tail'))
        window = '\n\n'.join(f"{item['path']}:{item['first_line']}-{item['last_line']}\n{item['text']}" for item in windows)
        system, user = load(cfg, 'aideal/docfix_diagnose', api_name=api,
            source_window=window, other_sites='Only the frozen definition is selected.',
            type_context=json.dumps(rows[0], indent=2), deep_dive_report='Not used; R0 development revision.',
            receiver=rows[0].get('owner', 'Unresolved'), entry_body=entries[api],
            snippet=row.get('code', ''), error=diagnostic, error_category=row.get('error_category', 'unknown'),
            frames='See the preserved diagnostic.', language_lower=cfg.language.lower())
        user += ('\n\n' + audience_context +
                 '\n\nDo not propose changing the denominator. Treat a saved pass as execution evidence, '
                 'not proof of independent correctness. State uncertainty rather than inventing behavior.')
        grounding = ('upstream_reference' if any(item['evidence_kind'] == 'upstream_reference'
                     for item in windows) else 'implementation_source')
        if grounding == 'upstream_reference':
            user += ('\nEVIDENCE LIMIT: The supplied .qmd/.md/.rst excerpt is upstream API reference '
                     'documentation, not implementation code. Diagnose only what it supports; do not '
                     'claim source verification or infer undocumented implementation behavior.')
        context = {'api': api, 'definition': rows[0], 'source_windows': windows,
                   'diagnose': {'system': system, 'user': user}, 'D1_entry': entries[api],
                   'audience_context': audience_context, 'grounding': grounding}
        write_once(context_path, (json.dumps(context, indent=2) + '\n').encode())
        bound[str(context_path.resolve())] = digest(context_path.read_bytes())
    launch = {'schema': 1, 'study': 'D2_from_corrected_R0_development_failures',
              'selected': selected, 'all_apis': names, 'spec': spec, 'bindings': bound,
              'model': spec.get('model', 'gemini-3.1-flash-lite'),
              'runtime_profile': runtime,
              'provider_settings': {key: os.getenv(key) for key in
                  ('AIDEAL_GOOGLE_REQUEST_TIMEOUT_S', 'AIDEAL_GOOGLE_MAX_RETRIES', 'AIDEAL_GOOGLE_MIN_INTERVAL_S')},
              'validation': 'corrected_native_execution_of_authored_example_not_independent_oracle'}
    launch['identity_sha256'] = digest(launch)
    write_once(output / 'launch.json', (json.dumps(launch, indent=2) + '\n').encode())
    if not (output / 'status.json').exists():
        atomic_json(output / 'status.json', {'status': 'prepared', 'selected': len(selected), 'model_calls': 0})
    return cfg, launch


def verify_inputs(launch):
    from aideal.readme_recording import digest
    for path, expected in launch['bindings'].items():
        if digest(Path(path).read_bytes()) != expected:
            raise ValueError('Bound D2 input changed: ' + path)
    for key, expected in launch.get('provider_settings', {}).items():
        if os.getenv(key) != expected:
            raise ValueError('D2 provider setting changed: ' + key)
    if runtime_receipts(launch.get('spec', {})) != launch.get('runtime_profile', []):
        raise ValueError('D2 runtime profile changed since preparation')


def revise(cfg, launch, output):
    """Record proposals; install only examples accepted by corrected execution."""
    from aideal.config import ModelSpec
    from aideal.prompts import load
    from aideal.readme_format import api_storage_key, _section_between
    from aideal.readme_recording import ReadmeCallRecorder, atomic_json, atomic_bytes, digest
    verify_inputs(launch)
    require_authoring_ready(launch)
    if (output / 'completion.json').exists():
        completed = read_json(output / 'completion.json')
        if digest((output / 'docs/D2.md').read_bytes()) != completed['readme_sha256']:
            raise ValueError('Completed D2 document changed; preserve it and use a new namespace')
    module_spec = importlib.util.spec_from_file_location('d2_replay', launch['spec']['replay_adapter'])
    replay = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(replay)
    spec = ModelSpec(provider='google', model=launch['model'], max_output_tokens=8192)
    recorder = ReadmeCallRecorder(output / 'author_calls', launch['identity_sha256'])
    header, entries = entry_parts((output / 'inputs/D1.md').read_text())
    outcomes = {}
    for number, api in enumerate(launch['selected'], 1):
        context = read_json(output / 'inputs/entries' / (api_storage_key(api) + '.json'))
        case = output / 'entries' / api_storage_key(api)
        case.mkdir(parents=True, exist_ok=True)
        saved = case / 'result.json'
        if saved.exists():
            outcome = read_json(saved)
            for path, expected in outcome.get('evidence', {}).items():
                if digest(Path(path).read_bytes()) != expected:
                    raise ValueError('Saved D2 validation evidence changed: ' + path)
            if outcome['status'] == 'accepted':
                candidate = (case / 'candidate.md').read_bytes()
                if digest(candidate) != outcome['candidate_sha256']:
                    raise ValueError('Saved D2 candidate changed')
                entries[api] = candidate.decode().rstrip() + '\n\n'
            outcomes[api] = outcome
            continue
        print(f'D2 [{number}/{len(launch["selected"])}] {api}', flush=True)
        if context.get('unsupported'):
            outcome = {'status': 'unchanged_unsupported', 'reason': context['unsupported']}
            atomic_json(saved, outcome)
            outcomes[api] = outcome
            continue
        verify_inputs(launch)
        require_authoring_ready(launch)
        diagnosis = recorder.invoke(spec, **context['diagnose'], phase='diagnose')
        verify_inputs(launch)
        atomic_bytes(case / 'diagnosis.txt', diagnosis.encode())
        if diagnosis.strip().upper().startswith('VERDICT: NOT-TESTABLE'):
            outcome = {'status': 'unchanged_unsupported', 'reason': diagnosis}
        else:
            window = '\n\n'.join(item['text'] for item in context['source_windows'])
            system, user = load(cfg, 'aideal/docfix_rewrite', api_name=api, diagnosis=diagnosis,
                deep_dive_report='Not used; corrected R0 development evidence.', source_window=window,
                entry_body=context['D1_entry'], required_sections=', '.join(cfg.required_sections))
            user += ('\n\nVALIDATION REQUIREMENT\nProvide exactly one complete body-statements example '
                     'in Valid Call Patterns, using the supplied execution bindings. No ellipses or placeholders. '
                     f'Include an explicit non-vacuous assertion and print a witness prefixed exactly __CHECK__ {api} . '
                     'Preserve the selected Signature exactly. Do not label the example validated.\n' +
                     context['audience_context'] +
                     '\nCross-check the diagnosis against source. It is a proposal, not authoritative evidence. '
                     'Do not copy a guessed expected value into an assertion.')
            if context.get('grounding') == 'upstream_reference':
                user += ('\nThis SQL entry is grounded in upstream reference documentation, not implementation '
                         'source. Replace the requested source-grounding badge with exactly '
                         '`_Grounding: revised from upstream reference and development feedback._`. '
                         'Do not claim source verification or completed execution validation.')
            verify_inputs(launch)
            require_authoring_ready(launch)
            candidate = recorder.invoke(spec, system, user, phase='rewrite', api=api,
                                        source_docs=[context['definition'].get('description') or ''])
            verify_inputs(launch)
            atomic_bytes(case / 'candidate.md', candidate.encode())
            try:
                introduction, candidate_entries = entry_parts(candidate)
                if introduction.strip() or list(candidate_entries) != [api]:
                    raise ValueError('Rewrite must contain only the exact requested API entry')
                if context.get('grounding') == 'upstream_reference' and (
                        '_Grounding: revised from upstream reference and development feedback._' not in candidate
                        or '_Grounding: doc-repaired from source' in candidate):
                    raise ValueError('Reference-grounded SQL revision incorrectly claims source verification')
                signature = context['definition'].get('signature')
                if not signature or signature not in _section_between(candidate, 'Signature'):
                    raise ValueError('Selected source signature changed')
                code = validation_example(candidate, cfg.required_sections)
                if not re.search(re.escape('__CHECK__ ' + api) + r'''(?=[\s'\"])''', code):
                    raise ValueError('Example omitted the exact target-specific check marker')
                if len(candidate) > int(cfg.comprehension.get('relevant_doc_chars', 12000) or 12000):
                    raise ValueError('Revised entry exceeds the matched audience context limit')
            except ValueError as error:
                outcome = {'status': 'unchanged_rejected_structure', 'reason': str(error)}
            else:
                verify_inputs(launch)
                validation = replay.run_program_case(launch['spec']['result'], api,
                    case / 'example_validation', code_override=code,
                    runtime_profile=launch['spec'].get('runtime_profile'))
                verify_inputs(launch)
                atomic_json(case / 'validation.json', validation)
                stdout = (Path(validation['scala_file']).parent / 'stdout.txt'
                          if validation.get('scala_file') else case / 'example_validation/stdout.txt')
                observed = stdout.read_text() if stdout.exists() else validation.get('stdout_tail', '')
                passed = validation.get('status') == 'pass' and '__CHECK__ ' + api + ' ' in observed
                outcome = {'status': 'accepted' if passed else 'unchanged_example_failed',
                           'candidate_sha256': digest(candidate.encode()),
                           'validation_kind': launch['validation'],
                           'grounding': context.get('grounding', 'implementation_source')}
                if outcome['status'] == 'accepted':
                    entries[api] = candidate.rstrip() + '\n\n'
        verify_inputs(launch)
        outcome['evidence'] = {str(path.resolve()): digest(path.read_bytes())
                               for path in case.rglob('*') if path.is_file() and path != saved}
        atomic_json(saved, outcome)
        outcomes[api] = outcome
        atomic_json(output / 'status.json', {'status': 'running', 'selected': len(launch['selected']),
                    'processed': len(outcomes), 'accepted': sum(r['status'] == 'accepted' for r in outcomes.values())})
    document = (header + ''.join(entries.values())).encode()
    verify_inputs(launch)
    write_once(output / 'docs/D2.md', document)
    completion = {'status': 'complete', 'identity_sha256': launch['identity_sha256'],
                  'readme_sha256': digest(document), 'selected': len(launch['selected']),
                  'output': str((output / 'docs/D2.md').resolve()), 'all_apis_count': len(entries),
                  'runtime_profile': launch.get('runtime_profile', []),
                  'accepted': sum(r['status'] == 'accepted' for r in outcomes.values()),
                  'outcomes': outcomes, 'scope': launch['study'], 'validation': launch['validation']}
    atomic_json(output / 'completion.json', completion)
    atomic_json(output / 'status.json', {key: completion[key] for key in ('status', 'selected', 'accepted')})
    return completion


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--engine', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--run', action='store_true', help='Uses model credits; default only prepares inputs')
    args = parser.parse_args()
    sys.path[:0] = [str(args.engine), str(args.engine / 'vendor/aideal_engine/src')]
    from workflow.execution import ownership
    spec = read_json(args.spec)
    output = args.output.resolve()
    for key in ('readme', 'result'):
        source = Path(spec[key]).resolve().parent
        if output == source or output.is_relative_to(source) or source.is_relative_to(output):
            raise ValueError('Use a separate D2 output outside measured evidence')
    with ownership(output):
        cfg, launch = prepare(spec, output)
        result = revise(cfg, launch, output) if args.run else {'status': 'prepared'}
        print(json.dumps({key: result[key] for key in ('status', 'accepted') if key in result} |
                         {'selected': len(launch['selected']), 'output': str(output)}, indent=2))


if __name__ == '__main__':
    main()
