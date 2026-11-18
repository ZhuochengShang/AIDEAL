"""Verify saved alias inputs, then start/resume the single-worker review queue."""
import argparse
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

op = Path(__file__).resolve().parent
plan_path = op / 'PLAN.json'
plan = json.loads(plan_path.read_text())
spec = importlib.util.spec_from_file_location('alias_review', op / 'alias_authoring_review.py')
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
a, e, b, suggestions = review.modules(Path(plan['release']))
checks = []
for job in plan['jobs']:
    command = job['command']
    continuation_path = Path(command[command.index('--continuation') + 1])
    c = a.load(continuation_path)
    assert c['continuation_sha256'] == a.digest({k: v for k, v in c.items() if k != 'continuation_sha256'})
    assert c['release'] == plan['release']
    for ref in [c['full_manifest'], c['model_configuration'], c['recorded_attempt_map'], *c['prefix_revalidations']]:
        assert a.verify_artifact(ref), ref['path']
    full = review.verified_manifest(c['full_manifest']['path'], a)
    names = set()
    for ref in c['prefix_revalidations']:
        review.verify_review(a.load(ref['path']), a, names)
    review.verify_partition(c['full_api_ids'], c['prefix_api_ids'], c['remaining_api_ids'])
    assert c['full_api_ids'] == [api for batch in full['batches'] for api in batch['api_ids']]
    checks.append({'bank': job['library'], 'continuation': a.bind(continuation_path),
                   'full_apis': c['full_api_count'], 'remaining_apis': c['subset_api_count'],
                   'remaining_batches': len(c['batches'])})
args = argparse.ArgumentParser(description=__doc__)
args.add_argument('--launch', action='store_true')
args = args.parse_args()
receipt = {'observed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'status': 'inputs_verified', 'plan': a.bind(plan_path), 'banks': checks}
if args.launch:
    # The supervisor also holds this queue lock for its complete lifetime.
    supervisor = Path(plan['root']) / 'supervisor'
    supervisor.mkdir(parents=True, exist_ok=True)
    with (supervisor / 'queue.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        env = dict(os.environ, AIDEAL_GOOGLE_REQUEST_TIMEOUT_S='300', AIDEAL_GOOGLE_MAX_RETRIES='2',
                   AIDEAL_GOOGLE_MIN_INTERVAL_S='1.0', PYTHONDONTWRITEBYTECODE='1',
                   OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', NUMBA_NUM_THREADS='1')
        for name in ['GOOGLE_API_KEY', 'GEMINI_API_KEY']:
            env.pop(name, None)
        command = ['/home/zshan011/apps/aideal/venv/bin/python',
                   str(Path(plan['release']) / 'scripts/run_cluster_experiment.py'),
                   '--plan', str(plan_path), '--key-file', '/home/zshan011/gemini-apikey-aideal.txt', '--workers', '1']
        with (op / 'console.log').open('ab') as log:
            child = subprocess.Popen(command, cwd=plan['release'], env=env, stdin=subprocess.DEVNULL,
                                     stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        receipt.update(status='launched', pid=child.pid, command=command)
    e.atomic_json(op / 'LAUNCH.json', receipt)
else:
    e.atomic_json(op / 'PREFLIGHT.json', receipt)
print(json.dumps(receipt, indent=2))
