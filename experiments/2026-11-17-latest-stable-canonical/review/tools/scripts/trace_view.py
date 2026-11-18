#!/usr/bin/env python3
"""Build a local evidence viewer. Reading this report never invokes a model."""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(os.environ.get('AIDEAL_TOOLKIT', str(Path(__file__).resolve().parents[1]))).resolve()


def _text(path):
    return path.read_text(encoding='utf-8', errors='replace') if path.is_file() else None


def _json(path):
    text = _text(path)
    if text is None:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None  # A running writer can be between creating and filling a file.


def capture_sources(repo=ROOT):
    """Capture review excerpts and actual line numbers without importing runtime code."""
    engine = repo / 'vendor/aideal_engine/src/aideal'
    specs = {
        'setup': (repo / 'scripts/run_original_micro.py', 'prepare', None, None),
        'prompt': (engine / 'doc_check_execution.py', '_comprehension_execute',
                   'for attempt in range(', 'raw_response = invoke_text'),
        'model': (engine / 'llm.py', 'invoke_text', None, None),
        'observer': (Path(__file__).with_name('trace_original_micro.py'), 'trace_model', None, None),
        'scaffold': (engine / 'doc_check_inputs.py', '_fill_scaffold', None, None),
        'execution': (engine / 'doc_check_execution.py', '_comprehension_execute',
                      'scala = _fill_scaffold', 'if ran:'),
        'process': (engine / 'execution.py', 'run_command', None, None),
        'feedback': (engine / 'doc_check_execution.py', '_comprehension_execute',
                     'if ran:', 'metrics[entry.name] = {'),
        'history': (engine / 'error_log.py', 'failures_for', None, None),
        'summary': (engine / 'doc_check_execution.py', '_comprehension_execute',
                    'metrics[entry.name] = {', 'if (last.get('),
    }
    result = {}
    for key, (path, name, begin, end) in specs.items():
        source = _text(path)
        if source is None:
            continue
        lines = source.splitlines()
        node = next((n for n in ast.walk(ast.parse(source))
                     if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name), None)
        if node is None:
            continue
        start, stop = node.lineno, node.end_lineno
        if begin:
            # In this function an earlier resume branch also assigns metrics;
            # take the final assignment for the aggregation review excerpt.
            matches = [i + 1 for i in range(start - 1, stop) if begin in lines[i]]
            if matches:
                start = matches[-1] if key == 'summary' else matches[0]
        if end:
            matches = [i + 1 for i in range(start, stop) if end in lines[i]]
            stop = matches[0] if matches else min(stop, start + 75)
        result[key] = {
            'path': str(path), 'start': start, 'text': '\n'.join(lines[start - 1:stop]),
            'sha256': hashlib.sha256(source.encode()).hexdigest(),
            'highlights': [i + 1 for i in range(start - 1, stop)
                           if any(term in lines[i] for term in (
                               'for attempt in range(', 'known =', 'load_prompt(',
                               'invoke_text(', 'run_command(', '_classify_error(',
                               'log.append(', 'if ran:', 'break', 'metrics[entry.name] ='))],
        }
    return result


def snapshot_sources(root, repo=ROOT):
    """Bind new trace views to the source that existed before their first request."""
    path = root / 'trace_sources.json'
    if not path.exists():
        path.write_text(json.dumps({'captured_at': datetime.now(timezone.utc).isoformat(),
                                   'sources': capture_sources(repo)}, indent=2) + '\n')


def _artifacts(directory, names):
    return [{'name': name, 'path': str(directory / name), 'uri': (directory / name).as_uri()}
            for name in names if (directory / name).is_file()]


def read_run(root):
    """Load observed records only; absent programs and attempts stay absent."""
    root = root.resolve()
    summary = _json(root / 'summary.json') or {}
    launch = _json(root / 'launch.json') or {}
    result = _json(root / 'result.json') or {}
    state = _json(root / 'trace_state.json') or {}
    requests = sorted((root / 'execution').glob('run_*/attempt_*/request.json'))
    if not requests and not summary and not launch:
        # The tiny Python trace does not have launch.json; its manifest still
        # permits a useful input view before the first request exists.
        manifest = _json(root / 'api_manifest.json')
        if not manifest:
            raise ValueError(f'No trace inputs or request evidence found: {root}')
    first = _json(requests[0]) if requests else {}
    api = summary.get('api') or launch.get('api') or (first or {}).get('api') or 'double'
    metric = result.get('metrics', {}).get(api, {})
    detail = result.get('details', {}).get(api, {})
    rounds = detail.get('rounds', []) if isinstance(detail, dict) else []
    mode = summary.get('mode') or state.get('mode') or ('scripted' if launch.get('mode') == 'trace-mock'
                                 or (first or {}).get('provider') == 'mock'
                                 or (not launch and _json(root / 'api_manifest.json') == ['double']) else 'live')
    attempts = []
    latest = {}
    for request_path in requests:
        request = _json(request_path) or {}
        if request.get('api') == api:
            latest[request.get('round', 0)] = request_path.parent
    bound = set(metric.get('attempt_evidence') or [])
    previous = ''
    for path in requests:
        req = _json(path)
        if not req or req.get('api') != api:
            continue
        directory = path.parent
        program = next(iter(sorted(directory.glob('*.scala')) + sorted(directory.glob('*.java')) + sorted(directory.glob('*.py'))), None)
        provider = _json(directory / 'provider.json')
        observation = _json(directory / 'trace_provider.json')
        process = _json(directory / 'execution.json')
        process_observation = _json(directory / 'trace_execution.json')
        response = _text(directory / 'response.txt')
        if response is None:
            response = _text(directory / 'trace_response.txt')
        number = req.get('round', 0)
        # A resumed R0 may have several attempt directories. Never apply a
        # later success to an earlier denied request with the same round number.
        eligible = str(directory) in bound if bound else latest.get(number) == directory
        verdict = next((r for r in rounds if r.get('round') == number), None) if eligible else None
        if provider and provider.get('status') == 'error':
            verdict = {'round': number, 'status': 'fail', 'category': 'llm-error',
                       'error': provider.get('error', 'Provider request failed')}
        # Exact prompt differences expose what really reached the model. They
        # do not infer a diagnosis, add hidden source context, or fabricate hints.
        changes = '\n'.join(line[2:] for line in difflib.ndiff(previous.splitlines(), req.get('user', '').splitlines())
                            if line.startswith('+ ')) if previous else ''
        previous = req.get('user', '')
        attempts.append({
            'id': directory.name, 'round': number, 'role': 'audience' if number == 0 else 'fixer',
            'request': req, 'response': response, 'program': _text(program) if program else None,
            'stdout': _text(directory / 'stdout.txt'), 'stderr': _text(directory / 'stderr.txt'),
            'execution': process or (process_observation.get('process') if process_observation else None),
            'provider_result': provider, 'trace_provider': observation,
            'trace_execution': process_observation, 'verdict': verdict,
            'feedback_added': changes, 'pending': mode != 'preview' and provider is None and process is None,
            'artifacts': _artifacts(directory, ['request.json', 'response.txt', 'trace_response.txt',
                'provider.json', 'ApiTest.scala', 'Generated.py', 'execution.json', 'command.txt',
                'stdout.txt', 'stderr.txt', 'trace_provider.json', 'trace_execution.json'] + ([program.name] if program else [])),
        })
        if attempts[-1]['stdout'] is None and process_observation:
            attempts[-1]['stdout'] = process_observation.get('stdout')
            attempts[-1]['stderr'] = process_observation.get('stderr')
    complete = summary.get('complete', result.get('run', {}).get('complete', False))
    status = summary.get('status') or metric.get('status') or 'in progress'
    if not complete and (metric.get('error_category') == 'llm-error' or any(
            (a['provider_result'] or {}).get('status') == 'error' for a in attempts)):
        status = 'provider error'
    label = ('Preview only · no model or execution' if mode == 'preview' else
             'Scripted replies + real execution' if mode == 'scripted' else 'Live Gemini')
    if mode == 'live' and status == 'provider error':
        label += ' · provider error'
    elif mode == 'live' and complete:
        label += ' · completed'
    model = summary.get('model') or launch.get('model') or (first or {}).get('model', 'not requested')
    provider = (first or {}).get('provider', 'mock' if mode == 'scripted' else 'google')
    snapshot = _json(root / 'trace_sources.json')
    scaffold = next(iter(sorted((root / 'inputs').glob('*scaffold*'))), root / 'scaffold.py')
    return {
        'id': root.name, 'label': label, 'root': str(root), 'api': api, 'mode': mode,
        'model': model, 'provider': provider, 'complete': complete, 'status': status,
        'stop_reason': summary.get('stop_reason') or state.get('label') or 'No final result recorded yet.',
        'summary': summary, 'documentation': _text(root / 'inputs/selected_documentation.txt'),
        'scaffold': _text(scaffold), 'trace_log': _text(root / 'trace.log') or '',
        'attempts': attempts,
        'artifacts': _artifacts(root, ['SUMMARY.md', 'summary.json', 'result.json', 'REPORT.md',
            'trace.log', 'launch.json', 'configs/aideal.yaml', 'inputs/api_manifest.json',
            'inputs/selected_documentation.txt', 'logs/error_log.jsonl', 'logs/errors.jsonl',
            'trace_sources.json', 'trace_state.json', 'review_notes.json', 'preview.json']),
        'review_notes': _json(root / 'review_notes.json') or [],
        'sources': snapshot.get('sources') if snapshot else None,
        'source_note': (f'Source snapshot captured before requests at {snapshot["captured_at"]}. '
                        'Open-in-editor links point to the current working file.' if snapshot else
                        'Historical trace: source excerpts are from the checkout when this viewer was built. '
                        'They are review aids, not a recorded observer-source snapshot.'),
    }


def build_trace_view(roots, output, repo=ROOT):
    """Render a self-contained report; JSON escaping prevents evidence becoming HTML."""
    runs = [read_run(Path(root)) for root in roots]
    payload = {'built_at': datetime.now(timezone.utc).isoformat(), 'runs': runs,
               'sources': capture_sources(repo), 'source_note': 'Read each run’s source-snapshot note.'}
    template_path = repo / 'docs/templates/trace_view.html'
    if not template_path.is_file():
        template_path = Path(__file__).with_name('trace_view.html')
    template = template_path.read_text()
    encoded = json.dumps(payload, ensure_ascii=False).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    encoded = encoded.replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    if template.count('__TRACE_DATA__') != 1:
        raise ValueError('Trace template must contain one data placeholder')
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.html.tmp')
    temporary.write_text(template.replace('__TRACE_DATA__', encoded), encoding='utf-8')
    temporary.replace(output)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, action='append', required=True, help='Saved trace folder; repeat to compare runs')
    parser.add_argument('--output', type=Path, help='Default is TRACE.html in the first run folder')
    args = parser.parse_args()
    print(build_trace_view(args.run, args.output or args.run[0] / 'TRACE.html'))


if __name__ == '__main__':
    main()
