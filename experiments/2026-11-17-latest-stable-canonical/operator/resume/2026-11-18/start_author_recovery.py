"""Start the prepared validation-only README replay with the frozen supervisor."""
from pathlib import Path
import argparse, datetime, fcntl, hashlib, importlib.util, json, os, subprocess, sys

STUDY = Path('/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical')
ROOT = STUDY / 'qualified-readme-source-note'

def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)

def worker(key_file):
    with (ROOT / 'launch.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = dict(status='CHECKING', pid=os.getpid(), started_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
        save(ROOT / 'STATE.json', state)
        try:
            checks = json.loads((ROOT / 'PREPARATION.json').read_text())
            assert checks['status'] == 'PASS'
            plan = json.loads((ROOT / 'QUEUE.json').read_text())
            assert [j['id'] for j in plan['jobs']] == ['mdanalysis-readme']
            binding = json.loads((ROOT / 'author-release.json').read_text())
            release = Path(plan['release'])
            assert release.name == binding['release']
            assert all(hashlib.sha256((release / p).read_bytes()).hexdigest() == h for p,h in binding['files'].items())
            env = json.loads((STUDY / 'qualified/launch/RUNTIME_ENV.json').read_text())
            assert 'GOOGLE_API_KEY' not in env and 'GEMINI_API_KEY' not in env
            os.environ.update(env)
            sys.path[:0] = [str(release), str(release / 'vendor/aideal_engine/src')]
            spec = importlib.util.spec_from_file_location('frozen_author_supervisor', release / 'scripts/run_cluster_experiment.py')
            queue = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(queue)
            state.update(status='RUNNING', workers=1, release=str(release))
            save(ROOT / 'STATE.json', state)
            result = queue.supervise(plan, key_file, workers=1)
            state.update(status='COMPLETE' if result['complete'] else 'STOPPED_WITH_INCOMPLETE_JOBS',
                         finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                         outcomes={k:v['status'] for k,v in result['jobs'].items()})
        except BaseException as exc:
            state.update(status='BLOCKED', error_type=type(exc).__name__)
        save(ROOT / 'STATE.json', state)
        return 0 if state['status'] == 'COMPLETE' else 2

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--key-file', type=Path, required=True)
    p.add_argument('--worker', action='store_true')
    a = p.parse_args()
    if a.worker:
        return worker(a.key_file)
    with (ROOT / 'launch.log').open('a') as log:
        child = subprocess.Popen([sys.executable, '-u', str(Path(__file__).resolve()), '--worker', '--key-file', str(a.key_file)],
                                 cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                                 env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    receipt = dict(pid=child.pid, state=str(ROOT / 'STATE.json'))
    save(ROOT / 'PROCESS.json', receipt)
    print(json.dumps(receipt))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
