#!/usr/bin/env python3
"""Fresh matched Original/D1/D2 native R0 runs with the corrected evaluator.

--prepare freezes inputs without model calls. --run processes the three arms
in separate child processes, stopping on an incomplete arm. A batch spec may
contain {"banks": {"library": <bank spec>}}; all banks are prepared first.
Saved programs rescored offline are development evidence, not these fresh runs.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts'), str(ROOT / 'vendor/aideal_engine/src')]
import yaml
import run_original_micro as baseline
from aideal.config import load_config
from aideal.doc_check_comprehension import comprehension_check
from aideal.doc_check_sources import _filled_entries
from aideal.fixreport import write_report
from aideal.experiment_identity import extra_components
from aideal.llm import reset_usage
from aideal.readme_format import parse_readme
from workflow.execution import atomic_json, ownership
from workflow.evaluation_setup import assert_review_released
from workflow.runtime_profile import (load_runtime_profile, remap_runtime_command,
    runtime_profile_receipts, verify_runtime_profile, require_runtime_ready)

ARMS = ('original', 'generated_d1', 'revised_d2')


def read(path):
    return json.loads(Path(path).read_text())


def binding(path):
    path = Path(path).resolve(strict=True)
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def verify(records):
    for record in records:
        if binding(record['path']) != record:
            raise ValueError('Frozen comparison input changed: ' + record['path'])


def validate_evidence(spec):
    """Require matched completed old runs and a complete, hash-bound D2."""
    old_path, gen_path, d2_path = [Path(spec[key]).resolve(strict=True) for key in
                                  ('original_result', 'generated_result', 'd2_completion')]
    old, gen, d2 = read(old_path), read(gen_path), read(d2_path)
    runtime = load_runtime_profile(spec['runtime_profile']) if spec.get('runtime_profile') else None
    runtime_receipts = runtime_profile_receipts(runtime)
    names = set(old.get('details', {}))
    for result in (old, gen):
        run = result.get('run', {})
        if (not names or set(result.get('details', {})) != names or not run.get('complete')
                or run.get('remaining_api_count') != 0 or run.get('max_fix_rounds') != 0):
            raise ValueError('Original and D1 must be complete matched R0 banks')
    for key in ('source', 'fixtures', 'api_inventory', 'scaffold', 'canonical_requested_targets'):
        left = old['run']['fingerprint_components'].get(key)
        if left is None or left != gen['run']['fingerprint_components'].get(key):
            raise ValueError('Old Original/D1 inputs differ: ' + key)
    if (d2.get('status') != 'complete'
            or d2.get('scope') != 'D2_from_corrected_R0_development_failures'
            or d2.get('validation') != 'corrected_native_execution_of_authored_example_not_independent_oracle'):
        raise ValueError('D2 must finish the corrected development/validation workflow first')
    document = Path(d2.get('output') or d2_path.parent / 'docs/D2.md').resolve(strict=True)
    if hashlib.sha256(document.read_bytes()).hexdigest() != d2.get('readme_sha256'):
        raise ValueError('D2 document hash differs from its completion receipt')
    launch_path = d2_path.parent / 'launch.json'
    launch = read(launch_path)
    if d2.get('identity_sha256') != launch.get('identity_sha256'):
        raise ValueError('D2 completion belongs to a different authoring launch')
    if set(launch.get('all_apis', [])) != names:
        raise ValueError('D2 API bank differs from the Original/D1 bank')
    outcomes = d2.get('outcomes', {})
    if (set(outcomes) != set(launch.get('selected', [])) or d2.get('selected') != len(outcomes)
            or d2.get('accepted') != sum(r.get('status') == 'accepted' for r in outcomes.values())):
        raise ValueError('D2 completion does not account for every development target')
    corrected = read(launch['spec']['result'])
    source_result = corrected.get('source_result', {})
    if {key: source_result.get(key) for key in ('path', 'sha256')} != binding(gen_path):
        raise ValueError('D2 was not developed from this D1 result')
    if d2.get('runtime_profile', []) != runtime_receipts or corrected.get('runtime_profile', []) != runtime_receipts:
        raise ValueError('D2 and corrected replay must use the same runtime profile as fresh evaluation')
    receipts = [binding(p) for p in (old_path, gen_path, d2_path, document, launch_path)] + runtime_receipts
    for path, expected in launch.get('bindings', {}).items():
        item = binding(path)
        if item['sha256'] != expected:
            raise ValueError('D2 development input changed: ' + path)
        receipts.append(item)
    # Bind paired runtime validation evidence, not merely the authoring status.
    for outcome in outcomes.values():
        if outcome.get('status') == 'accepted':
            validations = [path for path in outcome.get('evidence', {}) if Path(path).name == 'validation.json']
            if len(validations) != 1 or read(validations[0]).get('status') != 'pass':
                raise ValueError('Accepted D2 revision lacks a passing recorded example')
        for path, expected in outcome.get('evidence', {}).items():
            item = binding(path)
            if item['sha256'] != expected:
                raise ValueError('D2 validation evidence changed: ' + path)
            receipts.append(item)
    return old_path, gen_path, document, names, receipts


def condition_raw(raw, destination, document, runtime_profile=None):
    """Relocate output-bearing paths while keeping fixtures and runtime inputs."""
    raw = deepcopy(raw)
    raw['files'].update(llm_readme='docs/README.md',
                        notes_to_self='logs/notes_to_self.md', error_log='logs/error_log.jsonl')
    execution = raw['comprehension']['execute']
    execution.update(work_dir='execution', output_dir='execution/output', max_fix_rounds=0,
                     auto_report=False, stop_on_provider_error=True)
    if runtime_profile is not None:
        execution['command'] = remap_runtime_command(execution['command'], runtime_profile)
        execution['runtime_profile'] = runtime_profile['profile_binding']['path']
    for key, value in execution.get('sample_data', {}).items():
        if key.lower() in {'output', 'output_path', 'output_file', 'output_dir'}:
            if not isinstance(value, str):
                raise ValueError('Output sample binding must be an explicit path: ' + key)
            name = Path(value.removeprefix('file://')).name if key != 'output_dir' else ''
            execution['sample_data'][key] = str(destination / 'execution/output' / name)
    if document is not None:
        baseline.write_once(destination / 'docs/README.md', document.read_bytes())
    return raw


def verify_original_materials(cfg, result):
    """The evaluator may change; library source, fixtures and documents may not."""
    from aideal.doc_check_inputs import _execute_sample_data
    from aideal.doc_check_provenance import _comprehension_fingerprint_components
    frozen = result['run']['fingerprint_components']
    execution = cfg.comprehension['execute']
    data, _, _ = _execute_sample_data(cfg, execution)
    current = _comprehension_fingerprint_components(cfg, ex=execution,
        doc_source='original', doc_scope='relevant', max_fix_rounds=0,
        manifest_sha256=frozen['manifest_sha256'], document_sha256=frozen['document_sha256'],
        scaffold_file=cfg.root / execution['scaffold'], sample_data=data,
        class_context=False, timeout=int(execution.get('timeout_seconds', 600) or 600))
    for key in ('source', 'fixtures', 'api_inventory', 'scaffold', 'original_document_files'):
        if current[key] != frozen[key]:
            raise ValueError('Original material changed before fresh comparison: ' + key)


def prepare_comparison(spec):
    """Freeze all three arms before any audience request can begin."""
    old, gen, d2, names, receipts = validate_evidence(spec)
    runtime = load_runtime_profile(spec['runtime_profile']) if spec.get('runtime_profile') else None
    output = Path(spec['output']).resolve()
    for previous in (old.parent, gen.parent, d2.parent.parent):
        if output == previous or output.is_relative_to(previous) or previous.is_relative_to(output):
            raise ValueError('Comparison output must not overlap prior evidence')
    original_cfg = old.parent / 'configs/aideal.yaml'
    generated_cfg = gen.parent / 'configs/generated_readme.yaml'
    original, generated = load_config(original_cfg), load_config(generated_cfg)
    verify_original_materials(original, read(old))
    d2_launch = read(Path(spec['d2_completion']).parent / 'launch.json')
    if Path(d2_launch['spec']['readme']).read_bytes() != generated.llm_readme.read_bytes():
        raise ValueError('D2 was developed from a different D1 document')
    manifest = old.parent / 'inputs/api_manifest.json'
    source = Path(read(old.parent / 'launch.json')['source']).resolve(strict=True)
    source_link = next((p.name for p in old.parent.iterdir() if p.is_symlink() and p.resolve() == source), None)
    if not source_link:
        raise ValueError('Original source checkout link is missing')
    model = spec.get('model') or original.model_for_role('audience').model
    base_spec = {'base_config': str(original_cfg), 'manifest': str(manifest),
                 'source_link': {'name': source_link, 'target': str(source)}}
    receipts.extend(binding(p) for p in (original_cfg, generated_cfg, manifest, generated.llm_readme))
    if set(e.name for e in parse_readme(generated.llm_readme)) != names:
        raise ValueError('D1 document no longer matches the API bank')
    configs, common = {}, None
    for arm, document in zip(ARMS, (None, generated.llm_readme, d2)):
        destination = output / arm
        cfg, selected = baseline.prepare(base_spec, destination, model, None)
        if set(selected) != names:
            raise ValueError('Prepared API bank drifted')
        raw = condition_raw(cfg.raw, destination, document, runtime)
        config = destination / 'configs/comparison.yaml'
        baseline.write_once(config, yaml.safe_dump(raw, sort_keys=False).encode())
        final = load_config(config)
        audience = final.model_for_role('audience')
        contract = {**extra_components(final),
                    'runtime_profile': runtime_profile_receipts(runtime),
                    'interpreter': {'executable': sys.executable, 'version': sys.version,
                                    'environment_sha256': os.getenv('AIDEAL_ENV_FINGERPRINT', '')},
                    'audience': {'provider': audience.provider, 'model': audience.model,
                                 'max_output_tokens': audience.max_output_tokens},
                    'engine': read(destination / 'launch.json')['engine']}
        if common is not None and contract != common:
            raise ValueError('Conditions have different evaluator/model/prompt contracts')
        common = contract
        if document is not None:
            entries = _filled_entries(final)
            if Counter(entry.name for entry in entries) != Counter(names):
                raise ValueError('D1/D2 must contain exactly one complete entry per API')
            budget = final.comprehension.get('relevant_doc_chars', 12000)
            if any(len(entry.body) > budget for entry in entries):
                raise ValueError('D1/D2 entry exceeds matched context budget')
        configs[arm] = str(config)
        receipts.extend([binding(config), binding(destination / 'launch.json')])
        if document is not None:
            receipts.append(binding(destination / 'docs/README.md'))
    identity = {'schema': 'aideal.corrected-readme-comparison/v1', 'conditions': configs,
                'selected': len(names), 'model': model, 'trials': 1, 'max_fix_rounds': 0,
                'doc_scope': 'relevant', 'class_context': False,
                'common_contract': common,
                'bindings': sorted({r['path']: r for r in receipts}.values(), key=lambda r: r['path']),
                'operator': binding(__file__),
                'scope': 'Fresh native execution/configured self-checks; no independent oracle; '
                         'D2 uses development failures from the same API bank.'}
    baseline.write_once(output / 'comparison.json', (json.dumps(identity, indent=2) + '\n').encode())
    return identity


def run_condition(spec, arm):
    """Resume only this fresh condition; original measurement directories are inputs."""
    identity = prepare_comparison(spec)
    runtime = load_runtime_profile(spec['runtime_profile']) if spec.get('runtime_profile') else None
    destination = Path(spec['output']).resolve() / arm
    with ownership(destination):
        verify(identity['bindings'] + [identity['operator']])
        verify_runtime_profile(runtime)
        complete = destination / 'completion.json'
        if complete.exists():
            summary = read(complete)
            verify([summary['result']])
            return summary
        assert_review_released(destination)
        require_runtime_ready(runtime)
        cfg = load_config(identity['conditions'][arm])
        os.environ['MPLCONFIGDIR'] = str(destination / 'cache/matplotlib')
        reset_usage()
        with (destination / 'console.log').open('a', buffering=1) as stream, redirect_stdout(stream), redirect_stderr(stream):
            result = comprehension_check(cfg, doc_source='original' if arm == 'original' else 'aideal',
                execute=True, show_code=True, class_context=False, max_fix_rounds=0,
                resume=True, doc_scope='relevant', sample=None,
                manifest=str(destination / 'inputs/api_manifest.json'))
            atomic_json(destination / 'result.json', result)
            if result.get('metrics'):
                write_report(cfg, destination / 'result.json', out_path=destination / 'REPORT.md')
        verify(identity['bindings'] + [identity['operator']])
        verify_runtime_profile(runtime)
        metrics, run = result.get('metrics', {}), result.get('run', {})
        complete = (run.get('complete') is True and run.get('remaining_api_count') == 0
                    and len(metrics) == identity['selected']
                    and not any(str(r.get('error_category', '')).startswith(('provider-', 'llm-error'))
                                for r in metrics.values()))
        summary = {'condition': arm, 'status': 'complete' if complete else 'incomplete',
                   'selected': identity['selected'], 'recorded': len(metrics),
                   'passes': sum(r.get('status') == 'pass' for r in metrics.values()),
                   'input_tokens': sum(r.get('input_tokens') or 0 for r in metrics.values()),
                   'output_tokens': sum(r.get('output_tokens') or 0 for r in metrics.values()),
                   'model_calls': sum(r.get('llm_calls') or 0 for r in metrics.values()),
                   'run_wall_s': run.get('wall_s'), 'max_fix_rounds': 0,
                   'result': binding(destination / 'result.json'), 'scope': identity['scope']}
        atomic_json(destination / 'status.json', summary)
        if complete:
            atomic_json(destination / 'completion.json', summary)
        return summary


def run_children(spec_path, bank, spec):
    """Use separate processes and stop the dependent queue on an incomplete arm."""
    for arm in ARMS:
        command = [sys.executable, str(Path(__file__).resolve()), '--spec', str(spec_path),
                   '--worker', '--condition', arm]
        if bank is not None:
            command.extend(['--bank', bank])
        result = subprocess.run(command, check=False)
        if result.returncode:
            return result.returncode
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--bank')
    parser.add_argument('--condition', choices=ARMS)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--prepare', action='store_true')
    modes.add_argument('--run', action='store_true')
    modes.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    document = read(args.spec)
    banks = document.get('banks') or {None: document}
    if args.bank is not None:
        if args.bank not in banks:
            parser.error('Unknown bank')
        banks = {args.bank: banks[args.bank]}
    if args.worker:
        if not args.condition or len(banks) != 1:
            parser.error('A worker requires one bank and one condition')
        summary = run_condition(next(iter(banks.values())), args.condition)
        print(json.dumps(summary), flush=True)
        return 0 if summary['status'] == 'complete' else 2
    # Validate every bank first; one missing D2 cannot silently become a partial study.
    for bank, spec in banks.items():
        with ownership(Path(spec['output']).resolve()):
            identity = prepare_comparison(spec)
        print(json.dumps({'bank': bank, 'status': 'prepared', 'selected': identity['selected'],
                          'conditions': list(ARMS), 'output': spec['output']}), flush=True)
    if args.run:
        for bank, spec in banks.items():
            with ownership(Path(spec['output']).resolve()):
                code = run_children(args.spec.resolve(), bank, spec)
                if code:
                    return code
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
