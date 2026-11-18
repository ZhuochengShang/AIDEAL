#!/usr/bin/env python3
"""Resume interrupted tslearn R0 using its frozen supervisor and inputs."""
from contextlib import ExitStack
from pathlib import Path
import argparse, datetime, fcntl, hashlib, importlib.util, json, os, subprocess, sys

STUDY = Path('/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical')
ORIGINAL = STUDY / 'qualified/launch'
ROOT = Path(__file__).resolve().parent
JOBS = ('tslearn-r0',)

def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def check():
    original = load_module('original_launch', ORIGINAL / 'start_authorized.py')
    plan, release, study = original.verified_inputs(ORIGINAL)
    assert study == STUDY
    jobs = [j for j in plan['jobs'] if j['id'] in JOBS]
    assert {j['id'] for j in jobs} == set(JOBS)
    # Load recorded non-secret execution settings; credentials go only to the
    # existing supervisor through its explicit key-file argument.
    runtime = json.loads((ORIGINAL / 'RUNTIME_ENV.json').read_text())
    assert not any(k in runtime for k in ('GOOGLE_API_KEY', 'GEMINI_API_KEY'))
    os.environ.update(runtime)
    for key in ('AIDEAL_TRANSPORT_ADAPTER_SHA256', 'AIDEAL_TRANSPORT_POLICY_SHA256', 'AIDEAL_SETUP_POLICY_SHA256'):
        assert not os.environ.get(key)
    assert float(os.environ.get('AIDEAL_GOOGLE_REQUEST_TIMEOUT_S', '300')) == 300
    assert int(os.environ.get('AIDEAL_GOOGLE_MAX_RETRIES', '2')) == 2
    assert float(os.environ.get('AIDEAL_GOOGLE_MIN_INTERVAL_S', '0')) == 1
    identity = json.loads((STUDY / 'qualified/runs/original/tslearn/tslearn/execution/run_identity.json').read_text())
    assert identity['fingerprint_components']['interpreter']['environment_sha256'] == os.environ.get('AIDEAL_ENV_FINGERPRINT', '')
    for job in jobs:
        assert json.loads((STUDY / 'qualified/supervisor' / job['id'] / 'state.json').read_text())['status'] == 'failed'
    return dict(root=str(STUDY), release=str(release), jobs=jobs), release

def worker(key_file):
    state = dict(status='CHECKING', pid=os.getpid(), started_at=stamp(), jobs=list(JOBS))
    owns_resume = False
    try:
        with ExitStack() as stack:
            # Exclude older queue controllers while this subset owns its outputs.
            for path in (ROOT / 'resume.lock', ORIGINAL / 'launch.lock',
                         STUDY / 'qualified/supervisor/queue.lock',
                         STUDY / 'qualified-raptor/supervisor/queue.lock'):
                lock = stack.enter_context(path.open('a+'))
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                if path == ROOT / 'resume.lock':
                    owns_resume = True
            save(ROOT / 'STATE.json', state)
            plan, release = check()
            if (STUDY / 'supervisor/plan_binding.json').exists():
                assert json.loads((STUDY / 'supervisor/plan_binding.json').read_text())['plan'] == plan
            save(ROOT / 'PLAN.json', plan)
            baseline = STUDY / 'qualified/runs/original/tslearn/tslearn/result.json'
            if not (ROOT / 'BASELINE.json').exists():
                saved = json.loads(baseline.read_text())
                stable = {name: row for name, row in saved['metrics'].items() if row.get('error_category') != 'llm-error'}
                save(ROOT / 'BASELINE.json', dict(result_path=str(baseline),
                    result_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),
                    completed_count=len(stable), completed_metrics=stable))
            # Preparation revalidates copied configs and fingerprints without
            # making model calls; existing outcomes and README entries stay put.
            checks = []
            for job in plan['jobs']:
                command = ['--prepare' if arg == '--run' else arg for arg in job['command']]
                result = subprocess.run(command, cwd=release, capture_output=True, text=True)
                (ROOT / (job['id'] + '-preflight.log')).write_text(result.stdout + result.stderr)
                checks.append(dict(job=job['id'], returncode=result.returncode))
                assert result.returncode == 0, job['id'] + ' immutable-input check failed'
            save(ROOT / 'CHECKS.json', dict(status='PASS', observed_at=stamp(), jobs=checks, model_calls=0))
            sys.path[:0] = [str(release), str(release / 'vendor/aideal_engine/src')]
            queue = load_module('frozen_resume_queue', release / 'scripts/run_cluster_experiment.py')
            state.update(status='RUNNING', workers=1, queue_started_at=stamp(), release=str(release))
            save(ROOT / 'STATE.json', state)
            result = queue.supervise(plan, key_file, workers=1)
            state.update(status='COMPLETE' if result['complete'] else 'STOPPED_WITH_INCOMPLETE_JOBS',
                         finished_at=stamp(), outcomes={k:v['status'] for k,v in result['jobs'].items()})
            save(ROOT / 'STATE.json', state)
            return 0 if result['complete'] else 2
    except BaseException as exc:
        state.update(status='BLOCKED', finished_at=stamp(), error_type=type(exc).__name__)
        if owns_resume:
            save(ROOT / 'STATE.json', state)
        return 2

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--key-file', type=Path, required=True)
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    if args.worker:
        return worker(args.key_file)
    check()
    with (ROOT / 'console.log').open('a') as log:
        process = subprocess.Popen([sys.executable, '-u', str(Path(__file__).resolve()),
                                    '--worker', '--key-file', str(args.key_file)], cwd=ROOT,
                                   stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                                   env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    receipt = dict(pid=process.pid, started_at=stamp(), state=str(ROOT / 'STATE.json'))
    save(ROOT / 'PROCESS.json', receipt)
    print(json.dumps(receipt))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
