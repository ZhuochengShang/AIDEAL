"""Prepare three fresh matched mir_eval conditions; no model calls."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

ROOT = Path('/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical')
OP = ROOT / 'operator/ablation/2026-11-18/repair-protocol'
PYTHON = '/home/zshan011/apps/aideal/venv/bin/python'
RELEASE = '/home/zshan011/apps/aideal/releases/2026-11-18-compact-ablation-authoring-82c60d34f332'


def bind(path):
    path = Path(path).resolve(strict=True)
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def once(path, value):
    content = json.dumps(value, indent=2) + '\n'
    if path.exists():
        if path.read_text() != content:
            raise ValueError('Prepared input changed: ' + str(path))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


def main():
    manifest = ROOT / 'qualified/runs/original/mir_eval/mir_eval/inputs/api_manifest.json'
    names = json.loads(manifest.read_text())
    names = names['apis'] if isinstance(names, dict) else names
    assert len(names) == len(set(names)) == 178
    generated = ROOT / 'ablation-2026-11-18/generated-readme-r0/mir_eval/docs/LLM_readme.md'
    namespace = ROOT / 'ablation-2026-11-18/matched-repairs/mir_eval'
    plan = {'schema_version': 1, 'root': str(namespace), 'release': RELEASE,
        'scope': 'fresh matched mir_eval Original/Generated README/Error Hints R0 through R2',
        'protocol': 'matched-native-repair-1', 'workers': 1, 'selected_apis_per_condition': 178,
        'maximum_logical_model_requests': 1602, 'prior_result_reuse': False,
        'score_pooling_with_previous_R0': False, 'automatic_other_library_expansion': False,
        'pending_conditions': ['aliases', 'combined'], 'bank': bind(manifest),
        'estimate': {'observed_preparation_seconds_per_attempt': 6.96,
                     'upper_elapsed_hours_at_pilot_rate': 5.2,
                     'note': 'Successful targets stop early; provider retries or slower tasks can increase elapsed time.'},
        'interpretation': 'Native execution and self-check, same-bank development comparison; not held-out oracle accuracy.',
        'jobs': []}
    env = dict(os.environ)
    env.update(AIDEAL_GOOGLE_REQUEST_TIMEOUT_S='300', AIDEAL_GOOGLE_MAX_RETRIES='2',
        AIDEAL_GOOGLE_MIN_INTERVAL_S='1.0', PYTHONDONTWRITEBYTECODE='1',
        OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', NUMBA_NUM_THREADS='1',
        KERAS_BACKEND='torch', CUDA_VISIBLE_DEVICES='')
    checks = []
    for condition in ('original', 'generated_readme', 'error_hints'):
        base = 'error_hints' if condition == 'error_hints' else 'original'
        spec = json.loads((OP / 'specs' / f'mir_eval.{base}.json').read_text())
        spec.update(condition=condition, api_ids=names, output=str(namespace / condition), mode='live')
        if condition == 'generated_readme':
            spec['generated_readme'] = bind(generated)
        path = OP / 'specs' / f'mir_eval.full.{condition}.json'
        once(path, spec)
        command = [PYTHON, str(OP / 'matched_repairs.py'), '--spec', str(path)]
        result = subprocess.run(command + ['--prepare'], env=env, text=True,
                                capture_output=True, timeout=300)
        checks.append({'condition': condition, 'exit_code': result.returncode,
                       'stdout': result.stdout, 'stderr': result.stderr[-4000:], 'spec': bind(path)})
        print(json.dumps(checks[-1]), flush=True)
        if result.returncode:
            raise ValueError('Full condition preflight failed: ' + condition)
        plan['jobs'].append({'id': 'mir-full-' + condition.replace('_', '-') + '-r0-r2',
            'library': 'mir_eval', 'stage': 'development', 'condition': condition,
            'protocol': 'matched-native-repair-1', 'command': command + ['--run'],
            'output': spec['output'], 'complete_artifact': str(Path(spec['output']) / 'completion.json')})
    once(OP / 'FULL_MIR_QUEUE.json', plan)
    sys.path.insert(0, RELEASE)
    location = importlib.util.spec_from_file_location('matched_supervisor', Path(RELEASE) / 'scripts/run_cluster_experiment.py')
    supervisor = importlib.util.module_from_spec(location)
    location.loader.exec_module(supervisor)
    _, _, _, binding = supervisor.prepare(plan, None)
    once(OP / 'FULL_MIR_PREFLIGHT.json', {'status': 'pass', 'checks': checks,
         'queue': bind(OP / 'FULL_MIR_QUEUE.json'), 'binding': binding})


if __name__ == '__main__':
    main()
