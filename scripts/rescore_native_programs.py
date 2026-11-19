#!/usr/bin/env python3
"""Replay recorded native programs with corrected execution; never calls a model.

Old requests, responses and verdicts are immutable inputs. A new result records
which program was replayed, which execution contract changed and every outcome.
The same one-case function validates D2 development examples in separate folders.
"""
from __future__ import annotations

import argparse
from collections import Counter
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'vendor/aideal_engine/src')]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def binding(path):
    p = Path(path).resolve(strict=True)
    return {'path': str(p), 'sha256': digest(p)}


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f'.{os.getpid()}.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    tmp.replace(path)


def write_once(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError('Prepared evidence changed; choose a new output: ' + str(path))
    else:
        path.write_bytes(content)


def load_source(source_result):
    """Invalidate parsed inputs when a saved result or effective config changes."""
    p = Path(source_result).resolve(strict=True)
    files = [p, p.parent / 'configs/aideal.yaml', p.parent / 'configs/generated_readme.yaml']
    stamps = []
    for path in files:
        if path.is_file():
            stat = path.stat()
            stamps.append((str(path), stat.st_dev, stat.st_ino, stat.st_size,
                           stat.st_mtime_ns, stat.st_ctime_ns))
    return _load_source_cached(str(p), tuple(stamps))


@lru_cache(maxsize=16)
def _load_source_cached(source_result, input_stamps):
    from aideal.config import load_config
    p = Path(source_result).resolve(strict=True)
    result = json.loads(p.read_text())
    if result.get('mode') == 'rescored_saved_programs':
        # Development examples are rebuilt from the original saved scaffold.
        return load_source(result['source_result']['path'])
    if not result.get('run', {}).get('complete') or result['run'].get('max_fix_rounds') != 0:
        raise ValueError('Replay requires a completed, zero-repair source result')
    config = p.parent / 'configs' / ('generated_readme.yaml' if result.get('doc_source') == 'aideal' else 'aideal.yaml')
    return p, result, load_config(config), config


def saved_attempt(row):
    work = Path(row['scala_file']).parent
    attempts = sorted(p for p in work.glob('attempt_*') if (p / 'execution.json').is_file())
    if not attempts:
        raise ValueError('No recorded execution for ' + str(work))
    attempt = attempts[-1]
    program = attempt / Path(row['scala_file']).name
    if not program.is_file():
        raise ValueError('Missing immutable attempt program: ' + str(program))
    return work, attempt, program, json.loads((attempt / 'execution.json').read_text())


def assert_separate(old, new):
    old, new = Path(old).resolve(), Path(new).resolve()
    if old == new or new.is_relative_to(old) or old.is_relative_to(new):
        raise ValueError('New execution evidence must be separate from measured source')


def run_program_case(source_result, api, destination, code_override=None, runtime_profile=None):
    """Execute one saved snippet or D2 example, with no model or old-file writes.

    Return the native status plus full provenance. A pass means the program ran
    with enabled assertions and emitted its required markers; it is not an
    independent expected-output oracle. `code_override` is development evidence,
    never counted as a replay of the original audience response.
    """
    from aideal.doc_check_inputs import _execute_sample_data, _fill_scaffold
    from aideal.doc_check_errors import _classify_error
    from aideal.evaluation_scope import bind_python_scaffold_inputs
    from aideal.native_execution_contract import (
        assertion_environment, execution_contract, isolate_output_bindings,
        rebind_output_text, native_check_passed, native_witness_present,
    )
    from aideal.execution import run_command
    from workflow.runtime_profile import (load_runtime_profile, remap_runtime_command,
                                          runtime_profile_receipts)
    profile = load_runtime_profile(runtime_profile) if runtime_profile else None
    runtime_receipts = runtime_profile_receipts(profile) if profile else []
    source, recorded, cfg, config = load_source(str(Path(source_result).resolve()))
    dest = Path(destination).resolve()
    assert_separate(source.parent, dest)
    row = recorded['details'][api]
    old_work, attempt, program, execution = saved_attempt(row)
    ex = cfg.comprehension['execute']
    if ex.get('preamble') == 'auto' or ex.get('io_hints') == 'auto':
        raise ValueError('Replay cannot invoke automatic model-backed setup')
    sample, _, _ = _execute_sample_data(cfg, ex)
    placeholders = {k: str((cfg.root / str(v)).resolve()) if '/' in str(v) and not str(v).startswith('/') else str(v)
                    for k, v in (ex.get('placeholders') or {}).items()}
    contract = execution_contract(cfg.language)
    identity = {'schema': 1, 'api': api, 'source_result': binding(source),
                'source_config': binding(config), 'source_program': binding(program),
                'source_execution': binding(attempt / 'execution.json'),
                'source_request': binding(attempt / 'request.json'),
                'contract': contract, 'operator': binding(__file__),
                'runtime_profile': runtime_receipts,
                'execution_helpers': {name: digest(ROOT / 'vendor/aideal_engine/src/aideal' / name)
                                      for name in ('evaluation_scope.py', 'native_execution_contract.py', 'execution.py')},
                'mode': 'development_example' if code_override is not None else 'saved_program_replay',
                'override_sha256': hashlib.sha256(code_override.encode()).hexdigest() if code_override is not None else None}
    write_once(dest / 'replay_identity.json', (json.dumps(identity, sort_keys=True, indent=2) + '\n').encode())
    completed = dest / 'result.json'
    if (dest / '.aideal_unreconciled_process.json').exists():
        raise ValueError('Unreconciled replay process; do not resume this case')
    if completed.exists():
        completion = json.loads((dest / 'completion.json').read_text())
        if completion['result'] != binding(completed):
            raise ValueError('Completed replay result changed')
        result = json.loads(completed.read_text())
        for rec in result['evidence_bindings']:
            if digest(rec['path']) != rec['sha256']:
                raise ValueError('Completed replay evidence changed: ' + rec['path'])
        return result
    # An interrupted process receives a fresh physical attempt and outputs.
    # Earlier partial evidence is retained, never reused as writable state.
    previous = [int(p.name[8:]) for p in dest.glob('attempt_*')
                if p.is_dir() and p.name[8:].isdigit()]
    physical = dest / f'attempt_{max(previous, default=0) + 1:04d}'
    physical.mkdir()
    _, _, receipt = isolate_output_bindings(sample, physical, placeholders, ex.get('output_bindings'))
    text = program.read_text()
    import textwrap
    markers = ex.get('region', [])
    if code_override is None and len(markers) == 2 and all(m in text for m in markers):
        snippet = textwrap.dedent(text.split(markers[0], 1)[1].split(markers[1], 1)[0]).strip()
    else:
        snippet = row.get('code', '') if code_override is None else code_override
    if code_override is not None:
        text = _fill_scaffold(text, code_override, ex.get('region'), {})
    # Only execution scaffolding/path bindings change in replay. The saved
    # audience snippet remains linked by hash and is never repaired in place.
    text = rebind_output_text(text, receipt)
    if cfg.language.lower() == 'python':
        text = bind_python_scaffold_inputs(text, region=ex.get('region', ['# TODO API_TEST_START', '# TODO API_TEST_END']))
    test_file = physical / program.name
    write_once(test_file, text.encode())
    target = old_work / 'requested_target.json'
    if target.exists():
        write_once(physical / target.name, target.read_bytes())
    (physical / 'classes').mkdir(exist_ok=True)
    cmd = execution['command'].replace(str(old_work), str(physical))
    # The old shared working directory is never used as an execution location.
    cmd = rebind_output_text(cmd, receipt)
    if profile:
        cmd = remap_runtime_command(cmd, profile)
    env = assertion_environment(dict(os.environ), cfg.language, cmd)
    env.update(TMPDIR=str(physical / 'tmp'), MPLCONFIGDIR=str(physical / 'cache/matplotlib'))
    (physical / 'tmp').mkdir(exist_ok=True)
    (physical / 'cache/matplotlib').mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    try:
        proc = run_command(cmd, cwd=physical, env=env, timeout=int(execution['timeout_s']), guard_dir=dest)
        out, err, rc = proc.stdout or '', proc.stderr or '', proc.returncode
        output_decoding = getattr(proc, 'output_decoding', None)
    except subprocess.TimeoutExpired as exc:
        def txt(x): return x.decode('utf-8', errors='backslashreplace') if isinstance(x, bytes) else x or ''
        out, err, rc = txt(exc.stdout), txt(exc.stderr) + '\n[timeout]', 124
        output_decoding = getattr(exc, 'output_decoding', None)
    wall = time.monotonic() - started
    if profile and runtime_profile_receipts(load_runtime_profile(runtime_profile)) != runtime_receipts:
        raise ValueError('Runtime changed during replay; completion withheld')
    write_once(physical / 'stdout.txt', out.encode())
    write_once(physical / 'stderr.txt', err.encode())
    merged = out + '\n' + err
    success, failure = ex.get('success_marker', ''), ex.get('error_marker', '')
    check = ex.get('check_marker') or '__CHECK__'
    passed = native_check_passed(out, err, rc, api, ex)
    category, error, locus = ('', '', '') if passed else _classify_error(merged, rc, failure, language=cfg.language)
    if not passed and rc == 0 and ex.get('require_correctness') and not native_witness_present(out, api, check):
        category, error, locus = 'missing-witness', 'No nonempty stdout witness for the exact target API', ''
    run_record = {'command': cmd, 'cwd': str(physical), 'timeout_s': execution['timeout_s'],
                  'exit_code': rc, 'wall_s': wall, 'contract': contract,
                  'runtime_profile': runtime_receipts,
                  'java_assertions_requested': cfg.language.lower() in ('java', 'scala'),
                  'output_bindings': receipt, 'stdout_file': 'stdout.txt', 'stderr_file': 'stderr.txt',
                  'output_decoding': output_decoding}
    atomic(physical / 'execution.json', run_record)
    result = {'api': api, 'status': 'pass' if passed else 'fail', 'old_status': row['status'],
              'mode': identity['mode'], 'code': snippet, 'scala_file': str(test_file),
              'exit_code': rc, 'stdout_tail': out[-3000:], 'stderr_tail': err[-3000:],
              'error_category': category, 'error': error, 'locus': locus,
              'wall_s': wall, 'llm_calls': 0, 'input_tokens': 0, 'output_tokens': 0,
              'validation_scope': 'native_examples_not_independent',
              'rounds': [{'round': 0, 'status': 'pass' if passed else 'fail'}],
              'source_result': identity['source_result'],
              'runtime_profile': runtime_receipts,
              'evidence_bindings': [binding(dest / 'replay_identity.json'), *[binding(physical / n) for n in [program.name, 'execution.json', 'stdout.txt', 'stderr.txt']]]}
    # Bind binary evidence as well as its human-readable decoded diagnostic.
    result['evidence_bindings'].extend((output_decoding or {}).get('raw_streams', {}).values())
    for name in ('source_result', 'source_config', 'source_program', 'source_execution', 'source_request'):
        if binding(identity[name]['path']) != identity[name]:
            raise ValueError('Saved replay input changed during execution; completion withheld: ' + name)
    atomic(completed, result)
    atomic(dest / 'completion.json', {'result': binding(completed), 'identity': binding(dest / 'replay_identity.json')})
    return result



def frozen_input_state(cfg):
    """Hash original source/fixtures without including writable execution outputs."""
    import glob
    from urllib.parse import unquote, urlparse
    from aideal.doc_check_inputs import _execute_sample_data
    from aideal.doc_check_provenance import _sha256_files
    paths = [Path(p) for pattern in cfg.source_globs
             for p in glob.glob(str(cfg.root / pattern), recursive=True)]
    samples, _, _ = _execute_sample_data(cfg, cfg.comprehension['execute'])
    fixtures = [Path(unquote(urlparse(str(v)).path) if str(v).startswith('file://') else str(v))
                for k, v in samples.items() if k != 'output_dir']
    inventory = cfg.raw.get('codebase', {}).get('api_inventory')
    # Pin external adapters, interpreters and JARs as well as Python engine code.
    # Only runtime paths from the reviewed execution configuration are inspected.
    import shlex
    ex = cfg.comprehension['execute']
    runtime = []
    tokens = shlex.split(ex.get('command', ''))
    for token in tokens:
        if token.startswith('/') and '{' not in token:
            path = Path(token)
            if path.is_file():
                runtime.append(path)
    for key in ('jars', 'spark_jars', 'uberjar'):
        if ex.get(key):
            pattern = str(cfg.root / ex[key])
            runtime.extend(Path(p) for p in glob.glob(pattern) if Path(p).is_file())
    if '--classpath-file' in tokens:
        path = Path(tokens[tokens.index('--classpath-file') + 1])
        def jar_paths(value):
            if isinstance(value, str):
                return [Path(p) for p in value.split(':') if p.endswith('.jar') and Path(p).is_file()]
            if isinstance(value, list):
                return [p for item in value for p in jar_paths(item)]
            if isinstance(value, dict):
                return [p for item in value.values() for p in jar_paths(item)]
            return []
        runtime.extend(jar_paths(json.loads(path.read_text())))
    return {'source': _sha256_files(paths, cfg.root),
            'fixtures': _sha256_files(fixtures, cfg.root),
            'api_inventory': _sha256_files([cfg.root / inventory] if inventory else [], cfg.root),
            'runtime_artifacts': _sha256_files(runtime)}


def run_bank(source_result, output, apis=None, runtime_profile=None):
    """Resume a bank from immutable per-case receipts; every selected API counts."""
    from aideal.native_execution_contract import execution_contract
    from workflow.runtime_profile import load_runtime_profile, runtime_profile_receipts
    runtime_receipts = runtime_profile_receipts(load_runtime_profile(runtime_profile)) if runtime_profile else []
    from aideal.readme_format import api_storage_key
    import fcntl
    p, old, cfg, config = load_source(str(Path(source_result).resolve()))
    output = Path(output).resolve()
    assert_separate(p.parent, output)
    names = apis or list(old['details'])
    if len(names) != len(set(names)) or set(names) - set(old['details']):
        raise ValueError('Select unique APIs from the saved result')
    materials = frozen_input_state(cfg)
    historical = old.get('run', {}).get('fingerprint_components', {})
    for name, value in materials.items():
        if name in historical and value != historical[name]:
            raise ValueError('Frozen source input changed before replay: ' + name)
    identity = {'source_result': binding(p), 'source_config': binding(config),
                'input_fingerprints': materials,
                'runtime_profile': runtime_receipts,
                'selected_apis': names, 'contract': execution_contract(cfg.language),
                'mode': 'rescored_saved_programs', 'new_model_calls': 0,
                'operator': binding(__file__)}
    write_once(output / 'launch.json', (json.dumps(identity, sort_keys=True, indent=2) + '\n').encode())
    with (output / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        details, metrics = {}, {}
        for index, api in enumerate(names, 1):
            if binding(p) != identity['source_result'] or binding(config) != identity['source_config']:
                raise ValueError('Saved source result/config changed during bank replay')
            result = run_program_case(p, api, output / 'execution' / api_storage_key(api),
                                      runtime_profile=runtime_profile)
            details[api] = result
            metrics[api] = {**{k: v for k, v in old['metrics'].get(api, {}).items() if k in ('source', 'source_other_sites', 'codebase_frames')}, **{k: result[k] for k in ['status','old_status','wall_s','llm_calls','input_tokens','output_tokens','error_category','error']}}
            counts = Counter(r['status'] for r in metrics.values())
            atomic(output / 'progress.json', {'selected': len(names), 'recorded': index,
                   'passes': counts['pass'], 'failures': counts['fail'], 'last_api': api})
            print(f'[{index}/{len(names)}] {api}: {result["old_status"]} -> {result["status"]}', flush=True)
        if binding(p) != identity['source_result'] or binding(config) != identity['source_config']:
            raise ValueError('Saved source result/config changed; completion withheld')
        if frozen_input_state(cfg) != materials:
            raise ValueError('Source or input fixtures changed during replay; completion withheld')
        if runtime_profile and runtime_profile_receipts(load_runtime_profile(runtime_profile)) != runtime_receipts:
            raise ValueError('Runtime changed during replay; completion withheld')
        passes = sum(v['status'] == 'pass' for v in metrics.values())
        result = {'check': 'comprehension', 'mode': 'rescored_saved_programs',
                  'doc_source': old.get('doc_source'), 'source_result': binding(p),
                  'runtime_profile': runtime_receipts,
                  'run': {'complete': True, 'api_count': len(names), 'selected_api_count': len(names),
                          'max_fix_rounds': 0, 'new_model_calls': 0, 'contract': identity['contract']},
                  'score_with_infra': round(passes / len(names), 6), 'passes': passes,
                  'old_passes': sum(old['details'][k]['status'] == 'pass' for k in names),
                  'details': details, 'metrics': metrics,
                  'interpretation': 'Replay with corrected execution; not fresh model generation or independent correctness.'}
        atomic(output / 'result.json', result)
        atomic(output / 'completion.json', {'status': 'complete', 'result': binding(output / 'result.json'),
                                           'launch': binding(output / 'launch.json')})
        return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-result', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--apis', nargs='+', help='Optional exact API identities for mechanism checks')
    p.add_argument('--runtime-profile', type=Path, help='Reviewed isolated runtime correction; historical environment stays unchanged')
    args = p.parse_args()
    run_bank(args.source_result, args.output, args.apis, args.runtime_profile)


if __name__ == '__main__':
    main()
