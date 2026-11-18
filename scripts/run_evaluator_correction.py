#!/usr/bin/env python3
"""Run corrected replays, validated D2 authoring, then fresh matched R0 studies.

All stage directories are new. The existing supervisor alone handles the
configured credential; this controller never reads it or logs environment values.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]
import run_cluster_experiment as supervisor

BANKS = ('mir_eval', 'thumbnailator', 'sedonadb', 'rdpro_java', 'rdpro_scala', 'tslearn', 'mdanalysis')


def immutable_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    content = (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
    if path.exists() and path.read_bytes() != content:
        raise ValueError('Prepared correction plan changed: ' + str(path))
    if not path.exists():path.write_bytes(content)


def binding(path):
    return {'path': str(path.resolve()), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def verify_release():
    path = ROOT / 'EVALUATOR_RELEASE.json'
    release = json.loads(path.read_text())
    for relative, expected in release['files'].items():
        source = (ROOT / relative).resolve(strict=True)
        if not source.is_relative_to(ROOT) or hashlib.sha256(source.read_bytes()).hexdigest() != expected:
            raise ValueError('Frozen evaluator changed: ' + relative)
    return binding(path)


def prepare(study, output, banks=BANKS, runtime_profiles=None, input_overrides=None):
    release = verify_release()
    runtime_profiles = runtime_profiles or {}
    input_overrides = input_overrides or {}
    from workflow.runtime_profile import load_runtime_profile, runtime_profile_receipts
    profiles = {bank: runtime_profile_receipts(load_runtime_profile(path))
                for bank, path in runtime_profiles.items() if bank in banks}
    plans = {phase: {'root': str(output / phase), 'release': str(ROOT), 'jobs': []}
             for phase in ('rescore', 'continuation', 'd2', 'matched')}
    bank_inputs = {}
    for bank in banks:
        old_spec = json.loads((study / 'operator/ablation/2026-11-18/specs' / (bank + '.json')).read_text())
        original = Path(old_spec['baseline_output']) / 'result.json'
        generated = Path(old_spec['output']) / 'result.json'
        bank_paths = {'original_result': str(original), 'generated_result': str(generated)}
        for condition, source in [('original', original), ('generated_readme', generated)]:
            folder = output / 'rescore' / condition / bank
            plans['rescore']['jobs'].append({
                'id': bank + '-' + condition, 'library': bank, 'stage': 'r0',
                'command': [sys.executable, str(ROOT / 'scripts/rescore_native_programs.py'),
                            '--source-result', str(source), '--output', str(folder)] +
                           (['--runtime-profile', str(runtime_profiles[bank])] if bank in runtime_profiles else []),
                'output': str(folder), 'complete_artifact': str(folder / 'completion.json')})
        changes = input_overrides.get(bank, {})
        if set(changes) - {'project_profile', 'execution_overrides', 'input_bundle', 'runtime_reuse_evidence', 'force_fresh', 'selection_revision'}:
            raise ValueError('Unknown reviewed input override for ' + bank)
        continuation = output / 'continuation' / bank
        spec = {'library': bank, **bank_paths, 'output': str(continuation),
                'corrected_original_result': str(output / 'rescore/original' / bank / 'result.json'),
                'corrected_generated_result': str(output / 'rescore/generated_readme' / bank / 'result.json'),
                'model': 'gemini-3.1-flash-lite', **changes}
        if bank in runtime_profiles:
            spec['runtime_profile'] = str(runtime_profiles[bank])
        path = output / 'operator/specs/continuation' / (bank + '.json')
        immutable_json(path, spec)
        plans['continuation']['jobs'].append({'id': bank + '-continuation', 'library': bank, 'stage': 'r0',
            'command': [sys.executable, str(ROOT / 'scripts/run_verified_readme_continuation.py'),
                        '--spec', str(path), '--run'],
            'output': str(continuation), 'complete_artifact': str(continuation / 'generated_d1/completion.json')})
        old_generated = generated.parent
        d2_folder = output / 'd2' / bank
        d2_spec = {'library': bank, 'config': str(old_generated / 'configs/generated_readme.yaml'),
                   'readme': str(old_generated / 'docs/LLM_readme.md'),
                   'manifest': str(old_generated / 'inputs/api_manifest.json'),
                   'result': str(output / 'rescore/generated_readme' / bank / 'result.json'),
                   'replay_adapter': str(ROOT / 'scripts/rescore_native_programs.py'),
                   'model': 'gemini-3.1-flash-lite'}
        if bank in runtime_profiles:
            d2_spec['runtime_profile'] = str(runtime_profiles[bank])
        path = output / 'operator/specs/d2' / (bank + '.json')
        immutable_json(path, d2_spec)
        plans['d2']['jobs'].append({'id': bank + '-d2', 'library': bank, 'stage': 'readme',
            'command': [sys.executable, str(ROOT / 'scripts/revise_readme_from_replay.py'),
                        '--engine', str(ROOT), '--spec', str(path), '--output', str(d2_folder), '--run'],
            'output': str(d2_folder), 'complete_artifact': str(d2_folder / 'completion.json')})
        matched = output / 'matched' / bank
        spec = {'library': bank, **bank_paths, 'd2_completion': str(d2_folder / 'completion.json'),
                'output': str(matched), 'model': 'gemini-3.1-flash-lite'}
        if bank in runtime_profiles:
            spec['runtime_profile'] = str(runtime_profiles[bank])
        path = output / 'operator/specs/matched' / (bank + '.json')
        immutable_json(path, spec)
        plans['matched']['jobs'].append({'id': bank + '-matched', 'library': bank, 'stage': 'r0',
            'command': [sys.executable, str(ROOT / 'scripts/run_corrected_readme_comparison.py'),
                        '--spec', str(path), '--run'],
            'output': str(matched), 'complete_artifact': str(matched / 'revised_d2/completion.json')})
        bank_inputs[bank] = {**bank_paths, 'original_binding': binding(original), 'generated_binding': binding(generated)}
    for phase, plan in plans.items():
        immutable_json(output / 'operator' / (phase.upper() + '_QUEUE.json'), plan)
    immutable_json(output / 'operator/PLAN.json', {
        'schema': 1, 'evaluator': release, 'banks': bank_inputs, 'phases': list(plans),
        'runtime_profiles': profiles, 'input_overrides': input_overrides, 'unlaunched_banks': [bank for bank in BANKS if bank not in banks],
        'policy': {'preserve_historical_measurements': True, 'rescore_model_calls': 0,
                   'requested_arms': ['original','generated_d1'], 'requested_repairs': 0,
                   'reuse': 'verified_passes_only_when_inputs_and_historical_runtime_match',
                   'd2_and_triple_comparison': 'deferred_unless_explicitly_launched',
                   'fresh_arms': ['original','generated_d1','revised_d2'], 'fresh_trials': 1,
                   'fresh_repairs': 0, 'model': 'gemini-3.1-flash-lite',
                   'd2_scope': 'corrected_R0_development_examples_not_post_R2_deep_dive',
                   'score_scope': 'native_execution_and_self_checks_not_independent_oracle',
                   'rdpro_reporting': 'Java_69_and_Scala_261_separate_plus_combined'}})
    return plans


def verify_readiness(output, banks, phases, profiles):
    """Require runtime proof for each bank; recheck it before each stage."""
    ready_path = output / 'operator/READINESS.json'
    ready = json.loads(ready_path.read_text())
    if ready.get('status') != 'passed' or ready.get('evaluator') != verify_release():
        raise ValueError('Corrected evaluator mechanism checks must pass before launch')
    if not ready.get('checks') or any(ready.get('banks', {}).get(bank, {}).get('status') != 'passed'
                                      for bank in banks):
        raise ValueError('Every selected bank needs verified runtime controls before launch')
    for bank in banks:
        controls = {(row.get('role'), row.get('expected')) for row in ready['checks'] if row.get('bank') == bank}
        if not {('positive', 'pass'), ('negative', 'fail')}.issubset(controls):
            raise ValueError('Missing positive/negative runtime controls for ' + bank)
    if any(phase != 'rescore' for phase in phases):
        blocked = {bank: ready['banks'][bank].get('unresolved_setup', []) for bank in banks
                   if ready['banks'][bank].get('unresolved_setup')}
        if blocked:
            raise ValueError('Resolve setup blockers before model-backed stages: ' + json.dumps(blocked))
    from workflow.runtime_profile import load_runtime_profile, runtime_profile_receipts
    active = {bank: runtime_profile_receipts(load_runtime_profile(profiles[bank])) if bank in profiles else []
              for bank in banks}
    for check in ready['checks']:
        if check.get('bank') not in banks:
            continue
        result = json.loads(Path(check['result']['path']).read_text())
        if result.get('status') != check.get('expected'):
            raise ValueError('Runtime control did not produce its expected verdict')
        if result.get('runtime_profile', []) != active[check['bank']]:
            raise ValueError('Runtime control used a different dependency environment')
        if check.get('role') == 'negative':
            diagnostic = check.get('required_diagnostic')
            observed = str(result.get('stdout_tail', '')) + str(result.get('stderr_tail', ''))
            if (check['expected'] != 'fail' or result.get('exit_code', 0) == 0
                    or not diagnostic or diagnostic not in observed):
                raise ValueError('Negative control did not reach the deliberate assertion')
        if binding(Path(check['result']['path'])) != check['result']:
            raise ValueError('Mechanism-check evidence changed')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--study', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--key-file', type=Path)
    p.add_argument('--run', action='store_true')
    p.add_argument('--banks', nargs='+', choices=BANKS, default=list(BANKS),
                   help='Launch only explicitly ready banks; others remain listed as unlaunched')
    p.add_argument('--runtime-profiles', type=Path, help='JSON mapping of banks to reviewed isolated runtime profiles')
    p.add_argument('--input-overrides', type=Path, help='JSON mapping of banks to reviewed profile/context/data overrides')
    p.add_argument('--phases', nargs='+', choices=('rescore','continuation','d2','matched'), default=['rescore','continuation'])
    args = p.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(args.study.resolve()) or output == args.study.resolve():
        p.error('Use a new correction subdirectory under the study')
    if len(args.banks) != len(set(args.banks)) or len(args.phases) != len(set(args.phases)):
        p.error('Banks and phases must be unique')
    profiles = json.loads(args.runtime_profiles.read_text()) if args.runtime_profiles else {}
    overrides = json.loads(args.input_overrides.read_text()) if args.input_overrides else {}
    plans = prepare(args.study.resolve(), output, args.banks, profiles, overrides)
    selected_phases = list(args.phases)
    if not args.run:
        print(json.dumps({'status':'prepared','output':str(output),'banks':len(args.banks),'phases':selected_phases}));return
    if args.key_file is None:p.error('--run requires a configured credential-file path')
    verify_readiness(output, args.banks, selected_phases, profiles)
    os.environ.update(AIDEAL_GOOGLE_REQUEST_TIMEOUT_S='300', AIDEAL_GOOGLE_MAX_RETRIES='2',
                      AIDEAL_GOOGLE_MIN_INTERVAL_S='1.0')
    with (output / 'operator/launch.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for phase in selected_phases:
            verify_readiness(output, args.banks, [phase], profiles)
            plan = plans[phase]
            state = {'status':'running','phase':phase,'pid':os.getpid(),
                     'updated_at':datetime.now(timezone.utc).isoformat()}
            supervisor.atomic(output / 'operator/STATE.json', state)
            result = supervisor.supervise(plan, args.key_file, workers=2)
            state.update(status='phase_complete' if result['complete'] else 'stopped_with_incomplete_jobs',
                         updated_at=datetime.now(timezone.utc).isoformat())
            supervisor.atomic(output / 'operator/STATE.json', state)
            if not result['complete']:raise SystemExit(2)
        supervisor.atomic(output / 'operator/STATE.json', {'status':'complete',
            'updated_at':datetime.now(timezone.utc).isoformat(), 'phases':selected_phases})


if __name__ == '__main__':main()
