#!/usr/bin/env python3
"""Start only the two reviewed mir_eval mechanism jobs through the trusted queue."""
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
STUDY = Path('/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical')
ENVIRONMENT = {'AIDEAL_GOOGLE_REQUEST_TIMEOUT_S': '300',
    'AIDEAL_GOOGLE_MAX_RETRIES': '2', 'AIDEAL_GOOGLE_MIN_INTERVAL_S': '1.0',
    'PYTHONDONTWRITEBYTECODE': '1', 'OMP_NUM_THREADS': '1',
    'OPENBLAS_NUM_THREADS': '1', 'NUMBA_NUM_THREADS': '1',
    'KERAS_BACKEND': 'torch', 'CUDA_VISIBLE_DEVICES': ''}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = json.loads((HERE / 'PILOT_QUEUE.json').read_text())
    if len(plan['jobs']) != 2 or plan['scope'] != 'same-bank-mir-transcription-mechanism-pilot':
        raise ValueError('This launcher may run only the two reviewed mechanism checks')
    for proof in plan['offline_proofs']:
        if digest(proof['path']) != proof['sha256']:
            raise ValueError('Offline validation proof changed')
        checked = json.loads(Path(proof['path']).read_text())
        if checked.get('status') != 'pass' or checked.get('actual_model_calls') != 0:
            raise ValueError('Missing successful offline native repair-loop validation')
    for job in plan['jobs']:
        launch = json.loads((Path(job['output']) / 'LAUNCH.json').read_text())
        if launch.get('mode') != 'live' or launch['api_ids'] != ['python:mir_eval.transcription.validate']:
            raise ValueError('Unexpected pilot input or mode')
    # Match preparation exactly. Credentials are loaded only by the existing supervisor.
    os.environ.update(ENVIRONMENT)
    release = Path(plan['release'])
    sys.path.insert(0, str(release))
    location = importlib.util.spec_from_file_location('pilot_supervisor', release / 'scripts/run_cluster_experiment.py')
    supervisor = importlib.util.module_from_spec(location)
    location.loader.exec_module(supervisor)
    with (HERE / 'pilot-launch.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = {'status': 'RUNNING', 'pid': os.getpid(), 'workers': 1,
                 'started_at': datetime.now(timezone.utc).isoformat(),
                 'queue_sha256': digest(HERE / 'PILOT_QUEUE.json'),
                 'scope': plan['scope'], 'automatic_full_bank_expansion': False}
        supervisor.atomic(HERE / 'PILOT_STATE.json', state)
        try:
            result = supervisor.supervise(plan, Path('/home/zshan011/gemini-apikey-aideal.txt'), workers=1)
        except Exception:
            state.update(status='STOPPED_WITH_ERROR', finished_at=datetime.now(timezone.utc).isoformat())
            supervisor.atomic(HERE / 'PILOT_STATE.json', state)
            raise
        state.update(status='COMPLETE' if result['complete'] else 'STOPPED_WITH_INCOMPLETE_JOBS',
                     finished_at=datetime.now(timezone.utc).isoformat(),
                     outcomes={key: value['status'] for key, value in result['jobs'].items()})
        supervisor.atomic(HERE / 'PILOT_STATE.json', state)


if __name__ == '__main__':
    main()
