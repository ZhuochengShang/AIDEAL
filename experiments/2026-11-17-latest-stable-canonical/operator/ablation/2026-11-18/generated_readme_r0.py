#!/usr/bin/env python3
"""Evaluate a completed README with the exact Original R0 engine and API bank.

This study operator does not edit the engine, source checkout or old results.
The spec selects one bank and its pinned evaluator. `--prepare` makes no model
calls. `--run` resumes only this new condition's stable completed API records.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def bind(path):
    path = Path(path).resolve(strict=True)
    return {'path': str(path), 'sha256': sha(path.read_bytes())}


def verify_binding(record):
    if bind(record['path']) != record:
        raise ValueError('Bound input changed: ' + record['path'])


def verify_release(spec):
    """Check bytes before importing any executable code from the release."""
    binding_path = Path(spec['release_binding'])
    if sha(binding_path.read_bytes()) != spec['release_binding_sha256']:
        raise ValueError('Evaluator release binding changed')
    binding, release = read_json(binding_path), Path(spec['release']).resolve(strict=True)
    if release.name != binding['release']:
        raise ValueError('Release directory does not match its binding')
    for relative, expected in binding['files'].items():
        path = (release / relative).resolve(strict=True)
        if not path.is_relative_to(release) or sha(path.read_bytes()) != expected:
            raise ValueError('Frozen release file changed: ' + relative)
    return binding


def load_engine(spec):
    verify_release(spec)
    release = Path(spec['release']).resolve()
    # A process handles one release. Never mix imported f3 and strict modules.
    if any(name == 'aideal' or name.startswith('aideal.') for name in sys.modules):
        raise ValueError('Start a fresh Python process for each pinned evaluator')
    sys.path[:0] = [str(release), str(release / 'vendor/aideal_engine/src')]
    module_spec = importlib.util.spec_from_file_location(
        'pinned_original_micro', release / 'scripts/run_original_micro.py')
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def validate_baseline(result, names):
    """A partial baseline cannot silently define a full matched comparison."""
    run, metrics = result.get('run', {}), result.get('metrics', {})
    fp = run.get('fingerprint_components', {})
    if (not run.get('complete') or set(metrics) != set(names)
            or any(row.get('error_category') == 'llm-error' for row in metrics.values())):
        raise ValueError('Original R0 is incomplete or has a different API bank')
    if (fp.get('doc_source') != 'original' or fp.get('doc_scope') != 'relevant'
            or fp.get('max_fix_rounds') != 0 or fp.get('class_context') is not False):
        raise ValueError('Original result is not the matched relevant-context R0 protocol')
    return fp


def validate_entries(entries, names, completion, content, budget):
    """Require exact coverage and complete entries within the reviewed ceiling."""
    if (completion.get('status') != 'authored_not_execution_validated'
            or completion.get('readme_sha256') != sha(content)
            or completion.get('selected') != len(names)):
        raise ValueError('Authored README has no matching complete receipt')
    counts = Counter(entry.name for entry in entries)
    missing, extra = set(names) - counts.keys(), counts.keys() - set(names)
    duplicated = [name for name, count in counts.items() if count != 1]
    oversize = [(entry.name, len(entry.body)) for entry in entries if len(entry.body) > budget]
    if missing or extra or duplicated or oversize:
        raise ValueError('README coverage/budget mismatch: ' + json.dumps({
            'missing': sorted(missing), 'extra': sorted(extra),
            'duplicates': duplicated, 'oversize': oversize}, sort_keys=True))


def generated_config(raw):
    """The only configuration treatment is the generated documentation file."""
    changed = deepcopy(raw)
    changed['files']['llm_readme'] = 'docs/LLM_readme.md'
    return changed


def check_current_contract(cfg, fp):
    """Match prompt, model transport and interpreter before any model request."""
    from aideal.experiment_identity import prompt_contract, transport_contract
    interpreter = {'executable': sys.executable, 'version': sys.version,
                   'environment_sha256': os.environ.get('AIDEAL_ENV_FINGERPRINT', '')}
    if float(os.environ.get('AIDEAL_GOOGLE_MIN_INTERVAL_S', '0') or 0) != 1.0:
        raise ValueError('Use the reviewed AIDEAL_GOOGLE_MIN_INTERVAL_S=1.0 environment')
    for key, value in [('prompt_contract', prompt_contract(cfg)),
                       ('transport_contract', transport_contract()),
                       ('interpreter', interpreter)]:
        if fp.get(key) != value:
            raise ValueError('Current ' + key + ' differs from the completed Original R0')


def check_materials(cfg, fp):
    """Verify source, fixtures, inventory and runtime inputs without executing."""
    from aideal.doc_check_inputs import _execute_sample_data
    from aideal.doc_check_provenance import _comprehension_fingerprint_components
    ex = cfg.comprehension['execute']
    sample_data, _, _ = _execute_sample_data(cfg, ex)
    current = _comprehension_fingerprint_components(
        cfg, ex=ex, doc_source='original', doc_scope='relevant', max_fix_rounds=0,
        manifest_sha256=fp['manifest_sha256'], document_sha256=fp['document_sha256'],
        scaffold_file=cfg.root / ex['scaffold'], sample_data=sample_data,
        class_context=False, timeout=int(ex.get('timeout_seconds', 600) or 600))
    # Input hashes resolve source symlinks and normalize copied input filenames.
    # Canonical metadata is additionally bound through the identical inventory.
    for key, expected in fp.items():
        if key == 'canonical_requested_targets':
            continue
        if key not in current or current[key] != expected:
            raise ValueError('Prepared ' + key + ' differs from completed Original R0')


def check_baseline_launch_materials(engine, spec, baseline, original_launch):
    """Reproduce the old launch hash, including prebuilt jars/runtime adapters."""
    import glob
    original = engine.load_config(spec['base_config'])
    runtime = engine.inventory_runtime_bindings(original)
    paths = (list(original.original_readme_files) + list(engine.original_document_paths(original))
             + [source for _, source in runtime])
    if original.raw.get('codebase', {}).get('api_inventory'):
        paths.append(baseline / 'inputs/api_inventory.json')
    for pattern in original.source_globs:
        paths.extend(Path(p) for p in glob.glob(str(original.root / pattern), recursive=True))
    prepared = engine.load_config(baseline / 'configs/aideal.yaml')
    for value in prepared.comprehension['execute'].get('sample_data', {}).values():
        value = value.get('path') if isinstance(value, dict) else value
        if value and not str(value).startswith(('http:', 'https:')):
            paths.append(Path(str(value).removeprefix('file://')))
    paths.extend(Path(path) for path in spec.get('runtime_artifacts', []))
    prompt_dir = prepared.raw.get('files', {}).get('prompts_dir')
    if prompt_dir and Path(prompt_dir).exists():
        paths.extend(path for path in Path(prompt_dir).rglob('*') if path.is_file())
    if engine._sha256_files(paths) != original_launch['input_files']:
        raise ValueError('Original source/documents/fixtures/runtime artifacts changed since R0')


def prepare(spec_path, engine):
    """Freeze a new README condition while preserving all baseline inputs."""
    spec_path = Path(spec_path).resolve()
    spec = read_json(spec_path)
    if spec.get('schema') != 1:
        raise ValueError('Expected generated README operator spec schema 1')
    output, baseline, authoring = [Path(spec[key]).resolve() for key in
                                  ('output', 'baseline_output', 'authoring_output')]
    for old in (baseline, authoring):
        if output == old or output.is_relative_to(old) or old.is_relative_to(output):
            raise ValueError('New output must not overlap baseline/authoring evidence')
    catalog = engine.yaml.safe_load(Path(spec['catalog']).read_text())
    library_spec = catalog[spec['library']]
    original_launch = read_json(baseline / 'launch.json')
    if (original_launch.get('sample') is not None or original_launch.get('repairs') != 0
            or original_launch.get('trials') != 1):
        raise ValueError('Expected completed full-bank R0 with one trial')
    cfg, names = engine.prepare(library_spec, output, original_launch['model'], None)
    prepared_launch = read_json(output / 'launch.json')
    for key in ('model', 'sample', 'repairs', 'trials', 'base_config', 'source', 'engine', 'launcher_sha256'):
        if prepared_launch.get(key) != original_launch.get(key):
            raise ValueError('Baseline launcher identity differs: ' + key)
    # This also checks all ordinary configuration settings, not just the model.
    original_cfg = engine.load_config(baseline / 'configs/aideal.yaml')
    if cfg.raw != original_cfg.raw:
        raise ValueError('Prepared configuration differs from completed Original R0')
    for relative in ('inputs/api_manifest.json', 'inputs/api_inventory.json',
                     'configs/project_profile.yaml', cfg.comprehension['execute']['scaffold']):
        if (output / relative).read_bytes() != (baseline / relative).read_bytes():
            raise ValueError('Prepared input differs from Original: ' + relative)
    fp = validate_baseline(read_json(baseline / 'result.json'), names)
    check_baseline_launch_materials(engine, library_spec, baseline, original_launch)
    check_current_contract(cfg, fp)
    check_materials(cfg, fp)
    completion_path = authoring / 'completion.json'
    completion = read_json(completion_path)
    authored = Path(completion['output']).resolve(strict=True)
    if not authored.is_relative_to(authoring):
        raise ValueError('README completion points outside its authoring directory')
    content = authored.read_bytes()
    from aideal.readme_format import parse_readme
    entries = parse_readme(authored)
    budget = int(cfg.comprehension.get('relevant_doc_chars', 12000) or 12000)
    validate_entries(entries, names, completion, content, budget)
    engine.write_once(output / 'docs/LLM_readme.md', content)
    generated_path = output / 'configs/generated_readme.yaml'
    engine.write_once(generated_path, engine.yaml.safe_dump(generated_config(cfg.raw), sort_keys=False).encode())
    generated = engine.load_config(generated_path)
    sources = [spec_path, Path(spec['release_binding']), Path(spec['catalog']),
               baseline / 'launch.json', baseline / 'result.json', baseline / 'configs/aideal.yaml',
               completion_path, authored, generated_path, output / 'docs/LLM_readme.md',
               output / 'launch.json', output / 'inputs/api_manifest.json']
    receipt = {'schema': 1, 'condition': 'generated_readme', 'library': spec['library'],
               'doc_source': 'aideal', 'doc_scope': 'relevant', 'max_fix_rounds': 0,
               'trials': 1, 'class_context': False, 'selected': len(names),
               'relevant_doc_chars': budget, 'model': original_launch['model'],
               'baseline_fingerprint': read_json(baseline / 'result.json')['run']['experiment_fingerprint'],
               'evaluator_release': str(Path(spec['release']).resolve()),
               'bindings': [bind(path) for path in sources],
               'operator_sha256': sha(Path(__file__).read_bytes()),
               'transport_contract': fp['transport_contract'], 'interpreter': fp['interpreter'],
               'google_min_interval_s': 1.0,
               'comparison': 'Same API bank, source, fixtures, executor, prompts, model and R0 budget; '
                             'Original excerpts are replaced by the exact authored API entry. '
                             'Both use the same character ceiling; actual context lengths differ.',
               'score_interpretation': 'Native execution and configured self-check success; '
                                       'not an independent held-out puzzle oracle.'}
    engine.write_once(output / 'GENERATED_LAUNCH.json', (json.dumps(receipt, indent=2) + '\n').encode())
    return generated, names, receipt


def evaluate(cfg, names, receipt, engine):
    """R0 writes once per API, executes, records; resume never shares R0 records."""
    engine.assert_review_released(cfg.root)
    for item in receipt['bindings']:
        verify_binding(item)
    engine.reset_usage()
    os.environ['MPLCONFIGDIR'] = str(cfg.root / 'cache/matplotlib')
    print('Generated README R0 | ' + receipt['library'] + ' | ' + str(len(names)) + ' APIs', flush=True)
    print('Full prompts, responses and execution: ' + str(cfg.root / 'execution'), flush=True)
    with (cfg.root / 'console.log').open('a', buffering=1) as stream, redirect_stdout(stream), redirect_stderr(stream):
        result = engine.comprehension_check(
            cfg, doc_source='aideal', execute=True, show_code=True, class_context=False,
            max_fix_rounds=0, resume=True, doc_scope='relevant', sample=None,
            manifest=str(cfg.root / 'inputs/api_manifest.json'))
        engine.atomic_json(cfg.root / 'result.json', result)
        if result.get('metrics'):
            engine.write_report(cfg, cfg.root / 'result.json', out_path=cfg.root / 'REPORT.md')
    for item in receipt['bindings']:
        verify_binding(item)
    # A supervisor must not confuse a partial result.json with a completed run.
    rows, run = result.get('metrics', {}), result.get('run', {})
    complete = (run.get('complete') is True and set(rows) == set(names)
                and not any(row.get('error_category') == 'llm-error' for row in rows.values()))
    summary = {'condition': 'generated_readme', 'status': 'complete' if complete else 'incomplete',
               'selected': len(names), 'recorded': len(rows),
               'passes': sum(row.get('status') == 'pass' for row in rows.values()),
               'score_with_infra': result.get('score_with_infra'), 'score': result.get('score'),
               'updated_at': datetime.now(timezone.utc).isoformat(),
               'result': bind(cfg.root / 'result.json'), 'launch': bind(cfg.root / 'GENERATED_LAUNCH.json')}
    engine.atomic_json(cfg.root / 'status.json', summary)
    if complete:
        engine.atomic_json(cfg.root / 'completion.json', summary)
    print(json.dumps(summary), flush=True)
    return 0 if complete else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true')
    mode.add_argument('--run', action='store_true')
    args = parser.parse_args()
    spec = read_json(args.spec)
    engine = load_engine(spec)
    with engine.ownership(Path(spec['output']).resolve()):
        cfg, names, receipt = prepare(args.spec, engine)
        if args.prepare:
            print(json.dumps({'status': 'prepared', 'library': spec['library'], 'selected': len(names),
                              'output': str(cfg.root), 'condition': 'generated_readme'}), flush=True)
            return 0
        if not (os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')):
            raise ValueError('Configure provider access through the existing queue environment')
        if not os.getenv('GOOGLE_API_KEY'):
            os.environ['GOOGLE_API_KEY'] = os.environ['GEMINI_API_KEY']
        return evaluate(cfg, names, receipt, engine)


if __name__ == '__main__':
    raise SystemExit(main())
