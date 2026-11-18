#!/usr/bin/env python3
"""Fresh matched microbenchmark R0/R1/R2 using the pinned native executor.

One native single-attempt run is one logical round. This preserves an established
R0 if a provider outage interrupts R1. Native request.round=0 is deliberately
retained; ROUND.json supplies the outer logical round. No old R0 is imported.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager, redirect_stdout, redirect_stderr
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys
from repair_context import POLICY, INSTRUCTION, bind, verify, digest, feedback, terminal

CONDITIONS = {'original': ('original', False, False),
    'generated_readme': ('aideal', False, False), 'aliases': ('original', True, False),
    'error_hints': ('original', False, True), 'combined': ('aideal', True, True)}


def read(path):
    return json.loads(Path(path).read_text())


def frozen_json(engine, path, value):
    engine.write_once(path, (json.dumps(value, sort_keys=True, indent=2) + '\n').encode())


def load_engine(spec):
    """Reuse the previously tested release verifier; bind that helper as code."""
    verify(spec['engine_helper'])
    path = spec['engine_helper']['path']
    module_spec = importlib.util.spec_from_file_location('matched_engine_helper', path)
    helper = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(helper)
    return helper.load_engine(spec)


def validate_spec(spec):
    if spec.get('schema') != 1 or spec.get('condition') not in CONDITIONS:
        raise ValueError('Unknown matched repair spec/condition')
    if spec.get('mode', 'live') not in ('live', 'offline_mock'):
        raise ValueError('Unknown execution mode')
    doc_source, aliases, hints = CONDITIONS[spec['condition']]
    if bool(spec.get('generated_readme')) != (doc_source == 'aideal'):
        raise ValueError('Condition documentation does not match its label')
    if bool(spec.get('alias_interfaces')) != aliases:
        raise ValueError('Alias/Combined requires actual installed alias interfaces')
    runtime = spec['runtime']
    if runtime.get('native_hints_installed', False) != hints:
        raise ValueError('Hint/Combined requires an installed native-hint runtime')
    if hints and (runtime.get('native_hint_format') != 'single-line-exception'
                  or not runtime.get('native_hint_messages')
                  or any('\n' in text or '[AIDEAL fix:' not in text
                         for text in runtime['native_hint_messages'])):
        raise ValueError('This pilot requires verified single-line native exception hints')
    if runtime.get('aliases_installed', False) != aliases:
        raise ValueError('Alias interface and runtime installation disagree')
    if runtime.get('status') != 'verified' or not runtime.get('files') or not runtime.get('receipt'):
        raise ValueError('Require reviewed runtime files and import/build verification receipt')
    ids = spec['api_ids']
    if not ids or len(ids) != len(set(ids)):
        raise ValueError('Explicit unique API IDs are required')
    if spec.get('trials', 1) != 1:
        raise ValueError('This initial protocol records one trial per API')
    return doc_source


def configured(spec, engine):
    """Keep baseline inventory/fixtures; select only documentation and runtime."""
    cfg = engine.load_config(spec['prepared_config']['path'])
    cfg = deepcopy(cfg)
    if cfg.model_for_role('audience') != cfg.model_for_role('fixer'):
        raise ValueError('This protocol requires the same model and cap for all rounds')
    ex = cfg.comprehension['execute']
    if ex.get('build') or ex.get('preamble') == 'auto' or ex.get('io_hints') == 'auto':
        raise ValueError('Require a prebuilt runtime and explicit setup')
    output = Path(spec['output']).resolve()
    if output == cfg.root or output.is_relative_to(cfg.root):
        raise ValueError('Use a fresh sibling output, outside prior prepared runs')
    if spec.get('generated_readme'):
        cfg.llm_readme = Path(spec['generated_readme']['path'])
        cfg.raw['files']['llm_readme'] = str(cfg.llm_readme)
    ex.update(command=spec['runtime']['command'], work_dir=str(output / 'preflight'),
              output_dir=str(output / 'preflight/output'), max_fix_rounds=0,
              stop_on_provider_error=True, auto_report=False)
    cfg.comprehension['class_context'] = False
    cfg.raw['comprehension'] = cfg.comprehension
    return cfg


def identity(cfg, spec):
    """Native provenance binds source, fixtures, prompt, model and inventory."""
    from aideal.doc_check_sources import _comprehension_inventory
    from aideal.doc_check_inputs import _execute_sample_data
    from aideal.doc_check_provenance import _comprehension_fingerprint_components
    entries, shared, err = _comprehension_inventory(cfg, CONDITIONS[spec['condition']][0],
        manifest=spec['api_ids'], full_doc=False, doc_scope='relevant')
    if err or shared is not None or {x.name for x in entries} != set(spec['api_ids']):
        raise ValueError('Documentation/API selection is incomplete: ' + str(err))
    ex = cfg.comprehension['execute']
    sample_data, _, _ = _execute_sample_data(cfg, ex)
    return _comprehension_fingerprint_components(cfg, ex=ex,
        doc_source=CONDITIONS[spec['condition']][0], doc_scope='relevant', max_fix_rounds=0,
        manifest_sha256=digest('\n'.join(x.name for x in entries).encode()),
        document_sha256=digest('\n\0\n'.join(f'{x.name}\n{x.body}' for x in entries).encode()),
        scaffold_file=cfg.root / ex['scaffold'], sample_data=sample_data,
        class_context=False, timeout=int(ex.get('timeout_seconds', 600) or 600))


def prepare(spec_path, engine):
    spec = read(spec_path)
    validate_spec(spec)
    bindings = [bind(spec_path), spec['engine_helper'], spec['prepared_config'],
                spec['runtime']['receipt'], *spec['runtime']['files']]
    bindings += [spec[k] for k in ('generated_readme', 'alias_interfaces') if spec.get(k)]
    bindings += [bind(Path(__file__)), bind(Path(__file__).with_name('repair_context.py'))]
    for item in bindings:
        verify(item)
    aliases = read(spec['alias_interfaces']['path']) if spec.get('alias_interfaces') else {}
    if not set(aliases) <= set(spec['api_ids']):
        raise ValueError('Alias interface contains targets outside this bank')
    if any(not isinstance(v, str) or len(v) > POLICY['alias_chars'] for v in aliases.values()):
        raise ValueError('Alias descriptions must be reviewed strings within the common ceiling')
    cfg = configured(spec, engine)
    receipt = {'schema': 1, 'condition': spec['condition'], 'api_ids': spec['api_ids'],
        'bindings': bindings, 'policy': POLICY, 'mode': spec.get('mode', 'live'),
        'native_inputs': identity(cfg, spec),
        'runtime': spec['runtime'], 'fresh_initial_generation': True,
        'score_scope': 'native execution and configured self-check; no held-out oracle',
        'round_mapping': 'Each native round=0 is one outer logical round in ROUND.json'}
    frozen_json(engine, Path(spec['output']) / 'LAUNCH.json', receipt)
    return spec, cfg, receipt, aliases


def verify_inputs(cfg, spec, receipt):
    for item in receipt['bindings']:
        verify(item)
    if identity(cfg, spec) != receipt['native_inputs']:
        raise ValueError('Frozen source, docs, fixtures, runtime or model contract changed')


@contextmanager
def prompt_context(context, alias):
    """Only this target's previous public program/feedback enters a retry."""
    import aideal.prompts as prompts
    original = prompts.load
    def load(cfg, name, **kwargs):
        if name != 'aideal/comprehension_write_exec':
            return original(cfg, name, **kwargs)
        kwargs['known_failures'] = context or '(none; fresh initial attempt)'
        if alias:
            kwargs['api_body'] += '\n\nInstalled alias interface:\n' + alias
        system, user = original(cfg, name, **kwargs)
        return system, user + INSTRUCTION
    prompts.load = load
    try:
        yield
    finally:
        prompts.load = original


def run_chain(api, output, engine, execute, make_feedback):
    """Resume the same round; retain stable prior rounds without rerunning them."""
    previous, rows = None, []
    for number in range(POLICY['max_repairs'] + 1):
        root = output / f'round_{number:02d}'
        context, selection = make_feedback(previous, api, number) if previous else ('', {})
        frozen_json(engine, root / 'ROUND.json', {'api': api, 'logical_round': number,
            'native_round': 0, 'context': context, 'context_receipt': selection})
        complete = root / 'STABLE.json'
        if complete.exists():
            saved = read(complete)
            for item in saved['bindings']:
                verify(item)
            result = read(root / 'result.json')
            if saved['outcome'] != terminal(result['metrics'][api]):
                raise ValueError('Stable outcome disagrees with its result')
        else:
            result = execute(api, number, root, context)
            engine.atomic_json(root / 'result.json', result)
        if set(result.get('metrics', {})) != {api}:
            raise ValueError('Native execution returned no exact target metric')
        row = result['metrics'][api]
        outcome = terminal(row)
        if outcome != 'provider_pending' and not complete.exists():
            evidence = [bind(root / 'result.json'), bind(root / 'ROUND.json')]
            for path in row.get('attempt_evidence', []):
                evidence.extend(bind(p) for p in sorted(Path(path).iterdir()) if p.is_file())
            frozen_json(engine, complete, {'outcome': outcome, 'bindings': evidence})
        rows.append({'logical_round': number, 'outcome': outcome,
                     'result': str(root / 'result.json'), 'metrics': row})
        if outcome != 'fail':
            break
        previous = result
    return rows


def run(spec, cfg, receipt, aliases, engine):
    from aideal.doc_check_inputs import _strip_fences
    root, rows = Path(spec['output']), {}
    def execute(api, number, destination, context):
        verify_inputs(cfg, spec, receipt)
        current = deepcopy(cfg)
        current.error_log = destination / 'error_log.jsonl'
        current.raw['files']['error_log'] = str(current.error_log)
        ex = current.comprehension['execute']
        ex.update(work_dir=str(destination / 'execution'),
                  output_dir=str(destination / 'output'),
                  study_repair_protocol={'policy': POLICY, 'logical_round': number,
                      'context_sha256': digest(context.encode()),
                      'launch_sha256': bind(root / 'LAUNCH.json')['sha256']})
        current.raw['comprehension'] = current.comprehension
        frozen_json(engine, destination / 'api_manifest.json', [api])
        print(f'{spec["condition"]} | {api} | R{number} | {destination}', flush=True)
        with prompt_context(context, aliases.get(api, '')):
            with (destination / 'console.log').open('a') as log, redirect_stdout(log), redirect_stderr(log):
                result = engine.comprehension_check(current, doc_source=CONDITIONS[spec['condition']][0],
                    api=api, execute=True, show_code=True, class_context=False, max_fix_rounds=0,
                    resume=True, doc_scope='relevant', sample=None,
                    manifest=str(destination / 'api_manifest.json'))
        verify_inputs(cfg, spec, receipt)
        return result
    strip = lambda text: _strip_fences(text, strip_imports=bool(cfg.comprehension['execute'].get('strip_snippet_imports', False)))
    verify_inputs(cfg, spec, receipt)
    for api in spec['api_ids']:
        directory = root / 'apis' / digest(api.encode())[:20]
        rows[api] = run_chain(api, directory, engine, execute,
            lambda prior, name, n: feedback(prior, name, n, strip))
        summary = {'condition': spec['condition'], 'mode': spec.get('mode', 'live'),
            'selected': len(spec['api_ids']), 'rows': rows,
            'cumulative_passes': {f'R{n}': sum(any(r['outcome'] == 'pass' and r['logical_round'] <= n
                for r in chain) for chain in rows.values()) for n in range(3)},
            'complete': len(rows) == len(spec['api_ids']) and all(
                chain[-1]['outcome'] != 'provider_pending' for chain in rows.values()),
            'terminal_counts': {status: sum(chain[-1]['outcome'] == status for chain in rows.values())
                for status in ('pass', 'fail', 'infra', 'provider_pending', 'generation_invalid')},
            'score_scope': receipt['score_scope'], 'launch': bind(root / 'LAUNCH.json')}
        engine.atomic_json(root / 'result.json', summary)
        if rows[api][-1]['outcome'] == 'provider_pending':
            return 2
    verify_inputs(cfg, spec, receipt)
    engine.atomic_json(root / 'completion.json', summary)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true')
    mode.add_argument('--run', action='store_true')
    args = parser.parse_args()
    spec = read(args.spec)
    engine = load_engine(spec)
    with engine.ownership(Path(spec['output'])):
        spec, cfg, receipt, aliases = prepare(args.spec, engine)
        if args.prepare:
            print(json.dumps({'status': 'prepared', 'condition': spec['condition'], 'api_ids': spec['api_ids']}))
            return 0
        if spec.get('mode', 'live') != 'live':
            raise ValueError('Offline mock specs require the dedicated mock driver')
        return run(spec, cfg, receipt, aliases, engine)


if __name__ == '__main__':
    raise SystemExit(main())
