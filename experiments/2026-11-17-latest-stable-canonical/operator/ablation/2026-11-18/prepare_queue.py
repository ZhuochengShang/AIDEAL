"""Prepare this study's Generated README queue; no credentials or model calls."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path('/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical')
HERE = ROOT / 'operator/ablation/2026-11-18'
RUN = ROOT / 'ablation-2026-11-18'
PYTHON = '/home/zshan011/apps/aideal/venv/bin/python'


def write_once(path, value):
    data = (json.dumps(value, indent=2) + '\n').encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != data:
        raise ValueError('Prepared inputs changed: ' + str(path))
    if not path.exists():
        path.write_bytes(data)


def main():
    recorded = json.loads((ROOT / 'qualified/launch/RUNTIME_ENV.json').read_text())
    expected = {'AIDEAL_GOOGLE_REQUEST_TIMEOUT_S': '300',
                'AIDEAL_GOOGLE_MAX_RETRIES': '2', 'AIDEAL_GOOGLE_MIN_INTERVAL_S': '1.0'}
    if any(str(recorded.get(k)) != value for k, value in expected.items()):
        raise ValueError('Original transport settings differ')
    os.environ.update(expected)
    jobs = []
    for library in ('mir_eval', 'thumbnailator', 'sedonadb', 'tslearn',
                    'rdpro_java', 'rdpro_scala', 'mdanalysis'):
        corrected = library in ('thumbnailator', 'rdpro_java', 'rdpro_scala')
        namespace = 'qualified-raptor' if corrected else 'qualified'
        old_queue = json.loads((ROOT / namespace / 'launch/QUEUE.json').read_text())
        old_job = next(j for j in old_queue['jobs'] if j['library'] == library and j['stage'] == 'r0')
        command = old_job['command']
        binding = ROOT / ('review_snapshot/review/raptor-scope/operator/EVALUATOR_RELEASE.json'
                          if corrected else 'review_snapshot/EVALUATOR_RELEASE.json')
        author_namespace = 'qualified-readme-source-note' if library == 'mdanalysis' else namespace
        spec = {'schema': 1, 'library': library, 'release': old_queue['release'],
                'release_binding': str(binding),
                'release_binding_sha256': hashlib.sha256(binding.read_bytes()).hexdigest(),
                'catalog': command[command.index('--catalog') + 1],
                'baseline_output': str(ROOT / namespace / 'runs/original' / library / library),
                'authoring_output': str(ROOT / author_namespace / 'authoring' / library / library),
                'output': str(RUN / 'generated-readme-r0' / library)}
        spec_path = HERE / 'specs' / (library + '.json')
        write_once(spec_path, spec)
        argv = [PYTHON, str(HERE / 'generated_readme_r0.py'), '--spec', str(spec_path)]
        jobs.append({'id': library + '-generated-r0', 'library': library,
                     'stage': 'r0', 'condition': 'generated_readme',
                     'command': argv + ['--run'], 'output': spec['output'],
                     'complete_artifact': str(Path(spec['output']) / 'completion.json')})
    plan = {'root': str(RUN), 'release': str(Path('/home/zshan011/apps/aideal/current').resolve()),
            'condition': 'generated_readme', 'repairs': 0, 'trials': 1,
            'jobs': jobs}
    write_once(HERE / 'QUEUE.json', plan)
    checks = []
    for job in jobs:
        argv = job['command'][:-1] + ['--prepare']
        result = subprocess.run(argv, capture_output=True, text=True)
        record = {'library': job['library'], 'returncode': result.returncode,
                  'stdout': result.stdout, 'stderr': result.stderr}
        checks.append(record)
        print(job['library'], 'PASS' if result.returncode == 0 else 'FAIL', flush=True)
        if result.returncode:
            print(result.stderr[-3000:], flush=True)
    write_once(HERE / 'PREFLIGHT.json', checks)
    if any(row['returncode'] for row in checks):
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
