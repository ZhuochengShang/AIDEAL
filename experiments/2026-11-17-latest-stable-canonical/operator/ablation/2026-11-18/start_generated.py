"""Launch the prepared README comparison using the existing trusted supervisor."""
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = Path('/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical')


def main():
    plan = json.loads((HERE / 'QUEUE.json').read_text())
    checks = json.loads((HERE / 'PREFLIGHT.json').read_text())
    if len(checks) != len(plan['jobs']) or any(row['returncode'] for row in checks):
        raise ValueError('All seven preparation checks must pass before launch')
    # These are the recorded transport settings, not model credentials.
    recorded = json.loads((ROOT / 'qualified/launch/RUNTIME_ENV.json').read_text())
    expected = {'AIDEAL_GOOGLE_REQUEST_TIMEOUT_S': '300',
                'AIDEAL_GOOGLE_MAX_RETRIES': '2', 'AIDEAL_GOOGLE_MIN_INTERVAL_S': '1.0'}
    if any(str(recorded.get(k)) != value for k, value in expected.items()):
        raise ValueError('Original transport settings differ')
    os.environ.update(expected)
    release = Path(plan['release'])
    sys.path.insert(0, str(release))
    module_spec = importlib.util.spec_from_file_location('pinned_supervisor', release / 'scripts/run_cluster_experiment.py')
    supervisor = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(supervisor)
    with (HERE / 'launch.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = {'status': 'RUNNING', 'pid': os.getpid(),
                 'started_at': datetime.now(timezone.utc).isoformat(),
                 'queue_sha256': hashlib.sha256((HERE / 'QUEUE.json').read_bytes()).hexdigest(),
                 'workers': 2, 'jobs': [j['id'] for j in plan['jobs']]}
        supervisor.atomic(HERE / 'STATE.json', state)
        # Only the existing supervisor reads the permitted credential file.
        try:
            result = supervisor.supervise(plan, Path('/home/zshan011/gemini-apikey-aideal.txt'), workers=2)
        except Exception:
            state.update(status='STOPPED_WITH_ERROR', finished_at=datetime.now(timezone.utc).isoformat())
            supervisor.atomic(HERE / 'STATE.json', state)
            raise
        state.update(status='COMPLETE' if result['complete']
                     else 'STOPPED_WITH_INCOMPLETE_JOBS',
                     finished_at=datetime.now(timezone.utc).isoformat(),
                     outcomes={k: v['status'] for k, v in result['jobs'].items()})
        supervisor.atomic(HERE / 'STATE.json', state)


if __name__ == '__main__':
    main()
