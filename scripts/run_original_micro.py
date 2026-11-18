#!/usr/bin/env python3
"""Plan, prepare, or run Original-document microbenchmarks with zero repairs."""
from __future__ import annotations

import argparse
import glob
from contextlib import nullcontext, redirect_stderr, redirect_stdout
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shlex
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'vendor/aideal_engine/src'))

import yaml
from aideal.config import load_config
from aideal.api_registry import relocated_inventory_binding, inventory_runtime_bindings
from aideal.doc_check_comprehension import comprehension_check
from aideal.doc_check_sources import _load_manifest
from aideal.original_documentation import original_document_paths
from aideal.doc_check_provenance import _sha256_files
from aideal.fixreport import write_report
from aideal.llm import reset_usage
from workflow.execution import atomic_json, ownership
from workflow.evaluation_setup import assert_review_released


def write_once(path, content):
    """A prepared run can resume only with the same settings and copied inputs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError(f'Prepared input changed. Choose a new output root: {path}')
    else:
        path.write_bytes(content)


def prepare(spec, destination, model, sample, *, max_fix_rounds=0, api=None, mode='baseline'):
    """Isolate run outputs; optionally scope a review trace to one exact API.

    The batch launcher uses the unchanged R0 defaults. Trace callers must name
    their mode so mock responses and live repairs cannot look like baseline data.
    """
    if mode not in ('baseline', 'trace-mock', 'trace-live'):
        raise ValueError('mode must be baseline, trace-mock, or trace-live')
    if not isinstance(max_fix_rounds, int) or max_fix_rounds < 0:
        raise ValueError('max_fix_rounds must be a non-negative integer')
    if mode == 'baseline' and max_fix_rounds != 0:
        raise ValueError('Baseline launches use zero repairs; select a trace mode for repairs')
    if api is not None and sample is not None:
        raise ValueError('Use sample=None when selecting an exact API')
    if mode != 'baseline' and not api:
        raise ValueError('A trace mode requires one exact API name')
    original = load_config(spec['base_config'])
    names = _load_manifest(original, spec['manifest'])
    if not names:
        raise ValueError('The API manifest is empty')
    if api is not None and api not in names:
        raise ValueError(f'API {api!r} is not in the configured manifest: {names}')
    documentation_paths = original_document_paths(original)
    if not original.original_readme_files and not documentation_paths:
        raise ValueError('No original documentation resolved')
    source = Path(spec['source_link']['target']).resolve()
    if not source.is_dir():
        raise ValueError(f'Missing source checkout: {source}')
    # Fail before any model request if a listed Java executable or dependency is absent.
    runtime_artifacts = [Path(p) for p in spec.get('runtime_artifacts', [])]
    missing = [str(p) for p in runtime_artifacts if not p.is_file()]
    if missing:
        raise ValueError('Missing runtime artifacts: ' + ', '.join(missing))
    destination.mkdir(parents=True, exist_ok=True)
    link = destination / spec['source_link']['name']
    if link.is_symlink() and link.resolve() == source:
        pass
    elif link.exists() or link.is_symlink():
        raise ValueError(f'Source link has an unexpected target: {link}')
    else:
        link.symlink_to(source, target_is_directory=True)

    raw = deepcopy(original.raw)
    raw.pop('extends', None)
    runtime_bindings = inventory_runtime_bindings(original)
    for relative, source_file in runtime_bindings:
        if not relative.is_absolute():
            write_once(destination / relative, source_file.read_bytes())
    # Source ownership is fixed at preparation; relocation must not widen it.
    origin = raw.get('codebase', {}).get('api_origin') or {}
    if origin.get('source_roots'):
        origin['source_roots'] = [str((original.root / p).resolve()) for p in origin['source_roots']]
    inventory = (raw.get('codebase') or {}).get('api_inventory')
    inventory_path = (original.root / inventory).resolve() if inventory else None
    if inventory_path is not None:
        # Even an already absolute provenance binding must be copied into the
        # new run. Relocation returning None means the bytes need no edit.
        relocated = relocated_inventory_binding(original)
        content = relocated[0] if relocated is not None else inventory_path.read_bytes()
        write_once(destination / 'inputs/api_inventory.json', content)
        raw['codebase'].update(api_inventory='inputs/api_inventory.json',
                               api_inventory_sha256=hashlib.sha256(content).hexdigest())
    files = raw.setdefault('files', {})
    # Retain original documentation inputs. All output-bearing paths are new.
    files['original_readme'] = [str(p) for p in original.original_readme_files]
    if files.get('original_doc_manifest'):
        files['original_doc_manifest'] = str((original.root / files['original_doc_manifest']).resolve())
    for field in ('prompts_dir', 'integration_tasks', 'aliases'):
        if files.get(field):
            files[field] = str((original.root / files[field]).resolve())
    profile = original.root / files['project_profile']
    write_once(destination / 'configs/project_profile.yaml', profile.read_bytes())
    files.update(project_profile='configs/project_profile.yaml',
                 llm_readme='docs/catalog-unused-for-original.md',
                 notes_to_self='docs/notes_to_self.md', error_log='logs/error_log.jsonl')
    provider = 'mock' if mode == 'trace-mock' else 'google'
    if mode == 'trace-mock':
        model = 'offline-rdpro-trace'
    # Keep an explicitly reviewed cap for this model; otherwise allow up to
    # 8192 output tokens. Input distillation does not set this output allowance.
    selected_spec = original.registry.get(original.roles.get('audience', ''))
    cap = (selected_spec.max_output_tokens if selected_spec is not None and selected_spec.model == model
           and selected_spec.provider == provider else None) or 8192
    raw['models'] = {'registry': {'selected': {'provider': provider, 'model': model,
                                            'max_output_tokens': cap}},
                     'roles': {role: 'selected' for role in ('author', 'audience', 'fixer')}}
    execution = raw['comprehension']['execute']
    scaffold = (original.root / execution['scaffold']).resolve()
    write_once(destination / 'inputs' / scaffold.name, scaffold.read_bytes())
    execution.update(scaffold=f'inputs/{scaffold.name}', work_dir='execution',
                     output_dir='execution/output', max_fix_rounds=max_fix_rounds,
                     stop_on_provider_error=True, auto_report=False)
    if spec.get('execute_command'):
        execution['command'] = spec['execute_command']
    for field in ('build_cwd', 'jars', 'spark_jars'):
        if execution.get(field):
            if not isinstance(execution[field], str):
                raise ValueError(f'execute.{field} must be a path or glob string')
            execution[field] = str(original.root / execution[field])
    if execution.get('build'):
        raise ValueError('This launch needs a prebuilt runtime; inspect its build configuration first')
    if execution.get('preamble') == 'auto' or execution.get('io_hints') == 'auto':
        raise ValueError('Use explicit execution setup for an Original R0 run')
    for name, value in execution.get('sample_data', {}).items():
        if isinstance(value, str):
            execution['sample_data'][name] = str((original.root / value).resolve())
        elif isinstance(value, dict) and value.get('path'):
            value['path'] = str((original.root / value['path']).resolve())
    raw['comprehension']['class_context'] = False
    # Preserve the reviewed context budget. Some versioned API reference
    # entries exceed the legacy 12,000-character default and must not be cut.
    raw['comprehension']['relevant_doc_chars'] = original.comprehension.get('relevant_doc_chars', 12000)
    # Refuse resume if code, documentation, fixtures, or runner contents changed.
    # Symlinks save disk space; these hashes bind their contents to this run.
    inputs = (list(original.original_readme_files) + list(documentation_paths)
              + [source_file for _, source_file in runtime_bindings])
    if inventory_path is not None:
        inputs.append(destination / 'inputs/api_inventory.json')
    for pattern in original.source_globs:
        inputs.extend(Path(p) for p in glob.glob(str(original.root / pattern), recursive=True))
    for value in execution.get('sample_data', {}).values():
        value = value.get('path') if isinstance(value, dict) else value
        if value and not str(value).startswith(('http:', 'https:')):
            inputs.append(Path(str(value).removeprefix('file://')))
    inputs.extend(runtime_artifacts)
    if files.get('prompts_dir') and Path(files['prompts_dir']).exists():
        inputs.extend(p for p in Path(files['prompts_dir']).rglob('*') if p.is_file())
    engine = ROOT / 'vendor/aideal_engine'
    engine_files = [p for p in engine.rglob('*')
                    if p.is_file() and p.suffix in ('.py', '.md', '.txt', '.j2', '.jinja2', '.yaml')]
    # Bind launch options so a pilot cannot silently become a different run.
    identity = {'model': model, 'sample': sample, 'repairs': max_fix_rounds, 'trials': 1,
                'documentation': 'original', 'doc_scope': 'relevant',
                'base_config': spec['base_config'], 'source': str(source),
                'input_files': _sha256_files(inputs), 'engine': _sha256_files(engine_files),
                'launcher_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    if api is not None or mode != 'baseline':
        identity.update(api=api, mode=mode)
    write_once(destination / 'launch.json', (json.dumps(identity, indent=2) + '\n').encode())
    manifest_bytes = ((json.dumps([api]) + '\n').encode() if api is not None
                      else Path(spec['manifest']).read_bytes())
    write_once(destination / 'inputs/api_manifest.json', manifest_bytes)
    config = destination / 'configs/aideal.yaml'
    write_once(config, yaml.safe_dump(raw, sort_keys=False).encode())
    cfg = load_config(config)
    selected = _load_manifest(cfg, str(destination / 'inputs/api_manifest.json'))
    return cfg, selected


def run_library(cfg, destination, sample):
    """Use the existing native R0 engine and save its returned JSON explicitly."""
    assert_review_released(destination)
    log = destination / 'console.log'
    print(f'  Progress log: {log}', flush=True)
    os.environ['MPLCONFIGDIR'] = str(destination / 'cache/matplotlib')
    reset_usage()
    with log.open('a', buffering=1) as stream, redirect_stdout(stream), redirect_stderr(stream):
        result = comprehension_check(
            cfg, doc_source='original', execute=True, show_code=True,
            class_context=False, max_fix_rounds=0, resume=True,
            doc_scope='relevant', sample=sample,
            manifest=str(destination / 'inputs/api_manifest.json'))
        atomic_json(destination / 'result.json', result)
        if result.get('metrics'):
            write_report(cfg, destination / 'result.json', out_path=destination / 'REPORT.md')
    metrics = result.get('metrics', {})
    expected = result.get('run', {}).get('api_count', 0)
    provider_errors = sum(row.get('error_category') == 'llm-error' for row in metrics.values())
    complete = (bool(expected) and len(metrics) == expected and not provider_errors
                and result.get('run', {}).get('complete', True))
    return {'status': 'completed' if complete else 'incomplete', 'selected': expected,
            'recorded': len(metrics), 'provider_errors': provider_errors,
            'passes': sum(row.get('status') == 'pass' for row in metrics.values()),
            'score_with_infra': result.get('score_with_infra'), 'output': str(destination)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=ROOT / 'configs/original_micro_libraries.yaml')
    parser.add_argument('--output', type=Path, required=True, help='New batch directory; reuse to resume')
    parser.add_argument('--model', default='gemini-3.1-flash-lite')
    parser.add_argument('--libraries', nargs='+', help='Default includes all catalog libraries')
    parser.add_argument('--sample', type=int, help='Optional small pilot API count per library')
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--prepare', action='store_true', help='Write isolated configurations without model calls')
    modes.add_argument('--run', action='store_true', help='Prepare and execute R0 microbenchmarks; uses API credits')
    args = parser.parse_args()
    if args.sample is not None and args.sample < 1:
        parser.error('--sample must be positive')
    catalog = yaml.safe_load(args.catalog.read_text())
    libraries = args.libraries or list(catalog)
    unknown = set(libraries) - set(catalog)
    if unknown or len(libraries) != len(set(libraries)):
        parser.error('Select unique known libraries: ' + ', '.join(catalog))
    if args.run and not (os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')):
        parser.error('Set GOOGLE_API_KEY or GEMINI_API_KEY in this terminal before --run')
    if args.run and not os.getenv('GOOGLE_API_KEY'):
        os.environ['GOOGLE_API_KEY'] = os.environ['GEMINI_API_KEY']
    output = args.output.resolve()
    print(f'Original documentation | microbenchmarks | R0 only | one trial | {args.model}')
    print(f'Batch output: {output}', flush=True)
    results = {name: {'status': 'not_started'} for name in libraries}
    # Planning reads existing inputs only. Preparation/execution owns a fresh namespace.
    with ownership(output) if (args.prepare or args.run) else nullcontext():
        for name in libraries:
            spec = catalog[name]
            destination = output / name
            if spec.get('blocked'):
                results[name] = {'status': 'blocked', 'reason': spec['blocked']}
                print(f'{name}: BLOCKED — {spec["blocked"]}', flush=True)
                continue
            try:
                if args.prepare or args.run:
                    cfg, names = prepare(spec, destination, args.model, args.sample)
                else:
                    cfg = load_config(spec['base_config'])
                    names = _load_manifest(cfg, spec['manifest'])
                count = min(args.sample, len(names)) if args.sample else len(names)
                print(f'{name}: {count}/{len(names)} API names; output {destination}', flush=True)
                if spec.get('scope_note'):
                    print('  ' + spec['scope_note'], flush=True)
                command = [sys.executable, '-m', 'aideal.cli', '--config', str(destination / 'configs/aideal.yaml'),
                           'comprehension', '--doc', 'original', '--doc-scope', 'relevant',
                           '--execute', '--show-code', '--max-fix-rounds', '0', '--class-context', 'off',
                           '--manifest', str(destination / 'inputs/api_manifest.json'), '--resume']
                if args.sample:
                    command.extend(['--sample', str(args.sample)])
                print('  Engine command: ' + shlex.join(command), flush=True)
                results[name] = {'status': 'prepared' if args.prepare else 'planned',
                                 'selected': count, 'manifest_names': len(names), 'output': str(destination)}
                if args.run:
                    results[name]['status'] = 'running'
                    atomic_json(output / 'summary.json', results)
                    results[name] = run_library(cfg, destination, args.sample)
                    print(f'  {name}: {results[name]["status"]}', flush=True)
            except (OSError, ValueError, RuntimeError) as exc:
                results[name] = {'status': 'blocked', 'reason': str(exc)}
                print(f'{name}: BLOCKED — {exc}', flush=True)
            if args.prepare or args.run:
                atomic_json(output / 'summary.json', results)
            if results[name].get('provider_errors'):
                print('Provider access failed. Fix access and repeat the same command to resume.', flush=True)
                break
        if args.prepare or args.run:
            atomic_json(output / 'summary.json', results)
    return 2 if any(row['status'] in ('blocked', 'incomplete') for row in results.values()) else 0


if __name__ == '__main__':
    raise SystemExit(main())
