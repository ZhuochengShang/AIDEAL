#!/usr/bin/env python3
"""Prepare or generate all configured README API entries in isolated outputs."""
from __future__ import annotations

import argparse
from contextlib import nullcontext, redirect_stderr, redirect_stdout
from copy import deepcopy
import glob
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'vendor/aideal_engine/src'))

import yaml
from aideal.config import load_config
from aideal.api_registry import relocated_inventory_binding
from aideal.api_discovery import public_api_details, public_api_surface
from aideal.doc_check_sources import _load_manifest
from aideal.profile import profile_path, require_profile
from aideal.prompts import prompt_path
from aideal.readme_generation import find_or_create
from aideal.readme_format import parse_readme
from aideal.readme_validation import POLICY, is_complete_entry
from aideal.readme_replay import prepare_replay, ReplayStore, verify_replay_receipts
from aideal.readme_recording import ReadmeCallRecorder, ReadmeGenerationStopped, atomic_json, digest
from workflow.execution import ownership


def write_once(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != value:
            raise ValueError(f'Prepared README inputs changed; use a new output: {path}')
    else:
        path.write_bytes(value)


def bindings(paths):
    return [{'path': str(p), 'sha256': digest(p.read_bytes())}
            for p in sorted({Path(p).resolve() for p in paths if Path(p).is_file()}, key=str)]


def inspect(spec, scope='surface', sample=None):
    if not spec.get('base_config'):
        raise ValueError(spec.get('blocked', 'No README input configuration is provided'))
    cfg = load_config(spec['base_config'])
    require_profile(cfg)
    # Static selection prevents implicit intent-ranking provider calls in planning.
    if cfg.surface_filter.lower() in ('intent_score', 'intent', 'intended_llm', 'intent_llm'):
        raise ValueError('README launcher requires an explicit static API scope; freeze intent selection first')
    available = public_api_surface(cfg)
    details = [d for d in public_api_details(cfg) if d['visibility'] == 'public' and d['name'] in available]
    surface = sorted({d['name'] for d in details})
    selected = surface if scope == 'surface' else sorted(_load_manifest(cfg, spec['manifest']))
    if not selected or len(selected) != len(set(selected)) or set(selected) - set(surface):
        raise ValueError('README scope is empty, duplicated, or missing from the current source surface')
    chosen = selected[:sample] if sample is not None else selected
    return cfg, chosen, details, len(selected)


def prepare(spec, destination, model, scope='surface', sample=None, reuse_from=None):
    original, names, details, scope_count = inspect(spec, scope, sample)
    destination = Path(destination).resolve()
    source = Path(spec['source_link']['target']).resolve()
    if not source.is_dir():
        raise ValueError(f'Missing source checkout: {source}')
    destination.mkdir(parents=True, exist_ok=True)
    link = destination / spec['source_link']['name']
    if link.is_symlink() and link.resolve() == source:
        pass
    elif link.exists() or link.is_symlink():
        raise ValueError('README source link has an unexpected target')
    else:
        link.symlink_to(source, target_is_directory=True)
    raw = deepcopy(original.raw)
    raw.pop('extends', None)
    inventory = (raw.get('codebase') or {}).get('api_inventory')
    inventory_path = (original.root / inventory).resolve() if inventory else None
    canonical_bound = False
    if inventory_path is not None:
        relocated_inventory = relocated_inventory_binding(original)
        content = relocated_inventory[0] if relocated_inventory is not None else inventory_path.read_bytes()
        canonical_bound = bool(json.loads(content).get('canonical_selection'))
        write_once(destination / 'inputs/api_inventory.json', content)
        raw['codebase']['api_inventory'] = 'inputs/api_inventory.json'
        if relocated_inventory is not None:
            raw['codebase']['api_inventory_sha256'] = relocated_inventory[1]
    files = raw.setdefault('files', {})
    files['original_readme'] = [str(p) for p in original.original_readme_files]
    files['prompts_dir'] = str((original.root / files.get('prompts_dir', 'prompts')).resolve())
    write_once(destination / 'configs/project_profile.yaml', profile_path(original).read_bytes())
    files.update(project_profile='configs/project_profile.yaml', llm_readme='docs/LLM_readme.md',
                 notes_to_self='docs/notes_to_self.md', error_log='logs/error_log.jsonl',
                 aliases='aliases/aliases.json', integration_tasks='configs/integration_tasks.yaml')
    raw['models'] = {'registry': {'selected': {'provider': 'google', 'model': model}},
                     'roles': {role: 'selected' for role in ('author', 'audience', 'fixer')}}
    # Authoring is static grounding only: no probes, auto hints or execution.
    raw.setdefault('comprehension', {})['execute'] = {
        'probe_on_missing': False, 'preamble': '', 'io_hints': '', 'max_fix_rounds': 0}
    config = destination / 'configs/aideal.yaml'
    write_once(config, yaml.safe_dump(raw, sort_keys=False).encode())
    cfg = load_config(config)
    relocated = public_api_surface(cfg)
    if set(names) - relocated:
        raise ValueError('Relocated source paths no longer contain the frozen README scope')
    manifest = {'identity_kind': 'canonical_selected_target' if canonical_bound else 'bare_name_family',
                'scope': scope, 'sample': sample,
                'scope_count': scope_count, 'selected_count': len(names), 'names': names,
                'note': ('One entry per selected public target. Its exact declaration or registered SQL operation is frozen by the canonical-selection receipt; each definition list contains only that selected target.'
                         if canonical_bound else 'One entry per bare API name; same-name declarations remain grouped. Source definitions are explicit; no overload-complete claim.'),
                'definitions': {name: [d for d in details if d['name'] == name] for name in names}}
    write_once(destination / 'inputs/api_manifest.json', (json.dumps(manifest, indent=2) + '\n').encode())
    inputs = list(original.original_readme_files) + [profile_path(original)]
    if inventory_path is not None:
        inputs.append(inventory_path)
    for pattern in original.source_globs + original.test_globs:
        inputs.extend(Path(p) for p in glob.glob(str(original.root / pattern), recursive=True))
    inputs.extend(prompt_path(original, 'aideal/' + name) for name in ('readme_distill', 'readme_entry'))
    engine = ROOT / 'vendor/aideal_engine/src/aideal'
    inputs.extend(p for p in engine.rglob('*') if p.is_file() and p.suffix in ('.py', '.md', '.yaml'))
    inputs.append(Path(__file__))
    try:
        revision = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], stderr=subprocess.DEVNULL).decode().strip()
    except subprocess.CalledProcessError:
        revision = None
    provider_settings = {key: os.environ.get(key, default) for key, default in (
        ('AIDEAL_GOOGLE_REQUEST_TIMEOUT_S', '300'), ('AIDEAL_GOOGLE_MAX_RETRIES', '2'),
        ('AIDEAL_GOOGLE_MIN_INTERVAL_S', '0'))}
    packages = {}
    for package in ('PyYAML', 'langchain-core', 'langchain-google-genai', 'google-genai'):
        try:
            packages[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            packages[package] = None
    identity = {'schema': 1, 'model': 'google:' + model, 'scope': scope, 'sample': sample,
                'manifest_sha256': digest(manifest), 'source': str(source), 'revision': revision,
                'effective_config_sha256': digest(cfg.raw), 'inputs': bindings(inputs),
                'interpreter': {'executable': os.path.realpath(sys.executable), 'version': sys.version},
                'provider_settings': provider_settings, 'packages': packages,
                'authoring': 'static_grounding_no_execution', 'validation_policy': POLICY}
    if reuse_from is not None:
        _, replay_sha = prepare_replay(reuse_from, destination, identity)
        identity['replay_plan_sha256'] = replay_sha
    identity['identity_sha256'] = digest(identity)
    write_once(destination / 'launch.json', (json.dumps(identity, indent=2) + '\n').encode())
    return cfg, manifest, identity


def run_library(cfg, destination, manifest, identity):
    destination = Path(destination)
    completion_path = destination / 'completion.json'
    state_path = cfg.root / '.aideal_exec/readme_generation_state.json'
    if completion_path.exists():
        completion = json.loads(completion_path.read_text())
        if (completion.get('identity_sha256') != identity['identity_sha256'] or
                digest(cfg.llm_readme.read_bytes()) != completion.get('readme_sha256')):
            raise ValueError('Completed README or its identity changed')
        if digest(bindings((destination / 'author_calls').rglob('*'))) != completion.get('call_evidence_sha256'):
            raise ValueError('Completed README author evidence changed')
        if digest(bindings((destination / 'author_replay').rglob('*'))) != completion.get('replay_evidence_sha256'):
            raise ValueError('Completed README replay evidence changed')
        verify_replay_receipts(destination / 'author_replay')
        return completion
    if state_path.exists():
        previous_state = json.loads(state_path.read_text())
        if previous_state.get('complete') and (
                not cfg.llm_readme.is_file() or
                digest(cfg.llm_readme.read_bytes()) != previous_state.get('readme_sha256')):
            raise ValueError('Completed README changed before completion was recorded')
    if cfg.llm_readme.exists() and not state_path.exists():
        raise ValueError('An existing README without matching generation state cannot be overwritten')
    replay = (ReplayStore(destination / 'inputs/replay_plan.json', identity['replay_plan_sha256'],
                          identity['identity_sha256'], destination / 'author_replay')
              if identity.get('replay_plan_sha256') else None)
    recorder = ReadmeCallRecorder(destination / 'author_calls', identity['identity_sha256'], replay=replay)
    with (destination / 'console.log').open('a', buffering=1) as stream, redirect_stdout(stream), redirect_stderr(stream):
        result = find_or_create(cfg, generate=True, max_generated=0, resume=state_path.exists(),
                                api_names=manifest['names'], recorder=recorder)
    atomic_json(destination / 'result.json', result)
    state = json.loads(state_path.read_text())
    entries = parse_readme(cfg.llm_readme)
    actual = [entry.name for entry in entries]
    if (not state.get('complete') or state.get('completed_count') != len(manifest['names']) or
            sorted(actual) != sorted(manifest['names']) or len(actual) != len(set(actual)) or
            result.get('fallback_to_skeleton') or any(not is_complete_entry(
                entry.body, entry.name, [d.get('description') for d in manifest['definitions'][entry.name]])
                for entry in entries)):
        raise ValueError('README completion gate failed; inspect the retained results and calls')
    completion = {'status': 'authored_not_execution_validated', 'selected': len(actual),
                  'identity_sha256': identity['identity_sha256'], 'readme_sha256': digest(cfg.llm_readme.read_bytes()),
                  'output': str(cfg.llm_readme), 'new_calls': recorder.new_calls,
                  'reused_calls': recorder.reused_calls, 'generation_fingerprint': state['generation_fingerprint'],
                  'call_evidence_sha256': digest(bindings((destination / 'author_calls').rglob('*'))),
                  'replay_evidence_sha256': digest(bindings((destination / 'author_replay').rglob('*'))),
                  'imported_calls': replay.imported_calls if replay else 0,
                  'revalidated_calls': replay.revalidated_calls if replay else 0,
                  'validation_policy': POLICY}
    atomic_json(completion_path, completion)
    return completion


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=ROOT / 'configs/original_micro_libraries.yaml')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--libraries', nargs='+')
    parser.add_argument('--model', default='gemini-3.1-flash-lite')
    parser.add_argument('--reuse-from', type=Path, help='Prior library output; explicit validation-only replay in a new namespace')
    parser.add_argument('--scope', choices=['surface', 'manifest'], default='surface')
    parser.add_argument('--sample', type=int, help='Pilot: first N sorted APIs; use a separate output')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--prepare', action='store_true', help='Prepare immutable inputs without model calls')
    mode.add_argument('--run', action='store_true', help='Generate or resume; uses API credits')
    args = parser.parse_args()
    if args.sample is not None and args.sample < 1:
        parser.error('--sample must be positive')
    catalog = yaml.safe_load(args.catalog.read_text())
    libraries = args.libraries or list(catalog)
    if set(libraries) - set(catalog) or len(libraries) != len(set(libraries)):
        parser.error('Select unique known libraries: ' + ', '.join(catalog))
    if args.reuse_from and (len(libraries) != 1 or not (args.prepare or args.run)):
        parser.error('--reuse-from requires one library and --prepare or --run')
    if args.run and not (os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')):
        parser.error('Set GOOGLE_API_KEY or GEMINI_API_KEY before --run')
    if args.run and not os.getenv('GOOGLE_API_KEY'):
        os.environ['GOOGLE_API_KEY'] = os.environ['GEMINI_API_KEY']
    output = args.output.resolve()
    summary = {name: {'status': 'not_started'} for name in libraries}
    with ownership(output) if (args.prepare or args.run) else nullcontext():
        for name in libraries:
            destination = output / name
            try:
                if args.prepare or args.run:
                    cfg, manifest, identity = prepare(catalog[name], destination, args.model, args.scope, args.sample, args.reuse_from)
                    summary[name] = {'status': 'prepared', 'selected': manifest['selected_count']}
                else:
                    _, names, _, scope_count = inspect(catalog[name], args.scope, args.sample)
                    summary[name] = {'status': 'planned', 'selected': len(names), 'scope_count': scope_count}
                if args.run:
                    summary[name] = run_library(cfg, destination, manifest, identity)
            except ReadmeGenerationStopped as exc:
                summary[name] = {'status': 'provider_stopped', 'reason': str(exc)}
                atomic_json(output / 'summary.json', summary)
                print(f'{name}: provider_stopped; repeat the same command to resume. {exc}', flush=True)
                break
            except (OSError, ValueError, RuntimeError) as exc:
                summary[name] = {'status': 'blocked', 'reason': str(exc)}
            print(f'{name}: {json.dumps(summary[name])}', flush=True)
            if args.prepare or args.run:
                atomic_json(output / 'summary.json', summary)
    return 2 if any(row['status'] in ('blocked', 'provider_stopped', 'not_started') for row in summary.values()) else 0


if __name__ == '__main__':
    raise SystemExit(main())
