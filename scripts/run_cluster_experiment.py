#!/usr/bin/env python3
"""Run a pinned prepared experiment queue with at most two concurrent jobs."""
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import threading


def stamp():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data if isinstance(data, bytes) else json.dumps(data, sort_keys=True).encode()).hexdigest()


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def prepare(plan, secret):
    root, release = Path(plan['root']).resolve(), Path(plan['release']).resolve()
    if not release.is_dir():
        raise ValueError('Pinned release directory is missing')
    if secret and secret in json.dumps(plan):
        raise ValueError('Credentials must not appear in the plan')
    jobs, names, files, outputs = plan['jobs'], set(), {}, []
    if not isinstance(jobs, list) or not jobs:
        raise ValueError('Plan requires an explicit nonempty jobs list')
    for job in jobs:
        name = job['id']
        if not isinstance(name, str) or not name.replace('-', '').replace('_', '').isalnum() or name in names:
            raise ValueError('Job IDs must be unique simple names')
        names.add(name)
        if job['stage'] not in ('r0', 'readme') or not isinstance(job.get('library'), str):
            raise ValueError('Each job requires a library and r0/readme stage')
        command = job['command']
        if not isinstance(command, list) or not command or not all(isinstance(x, str) and x for x in command):
            raise ValueError('Commands must be nonempty argument lists')
        output = Path(job['output']).resolve()
        artifact = Path(job.get('complete_artifact', output / ('completion.json' if job['stage'] == 'readme' else 'result.json'))).resolve()
        if not output.is_relative_to(root) or output == root or not artifact.is_relative_to(output):
            raise ValueError('Each output must be below the study root and contain its completion artifact')
        if any(output == other or output.is_relative_to(other) or other.is_relative_to(output) for other in outputs):
            raise ValueError('Job output directories must not overlap')
        outputs.append(output)
        for argument in command:
            path = Path(argument)
            if path.is_absolute() and path.is_file() and not path.resolve().is_relative_to(output):
                files[str(path.resolve())] = digest(path.read_bytes())
    binding = {'plan': plan, 'release_resolved': str(release), 'command_files': files,
               'supervisor_sha256': digest(Path(__file__).read_bytes())}
    return root, release, jobs, binding


def supervise(plan, key_file, workers=2):
    if workers not in (1, 2):
        raise ValueError('Concurrency must be one or two')
    secret = Path(key_file).read_text().strip()
    if not secret or '\n' in secret or '\r' in secret:
        raise ValueError('Key file must contain one nonempty credential')
    root, release, jobs, binding = prepare(plan, secret)
    directory = root / 'supervisor'
    directory.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.pop('GEMINI_API_KEY', None)
    env['GOOGLE_API_KEY'] = secret
    stopped, processes, mutex = threading.Event(), {}, threading.Lock()
    def stop(_signum=None, _frame=None):
        stopped.set()
        with mutex:
            for process in processes.values():
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
    with (directory / 'queue.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        frozen = directory / 'plan_binding.json'
        if frozen.exists() and json.loads(frozen.read_text()) != binding:
            raise ValueError('Prepared plan, release or command files changed; use a new study root')
        if not frozen.exists():
            atomic(frozen, binding)
        statuses, pending = {}, []
        for job in jobs:
            receipt = directory / job['id'] / 'state.json'
            state = json.loads(receipt.read_text()) if receipt.exists() else {}
            if state.get('status') == 'complete':
                artifact = Path(state['artifact'])
                if not artifact.is_file() or digest(artifact.read_bytes()) != state['artifact_sha256']:
                    raise ValueError('Completed output changed for job ' + job['id'])
                statuses[job['id']] = state
            else:
                statuses[job['id']] = {'status': 'pending'}
                pending.append(job)
        def run(job):
            name, folder = job['id'], directory / job['id']
            folder.mkdir(exist_ok=True)
            attempts = [int(p.name[8:]) for p in folder.glob('attempt_*') if p.name[8:].isdigit()]
            attempt = folder / f'attempt_{max(attempts, default=0) + 1:04d}'
            attempt.mkdir()
            state = {'job': name, 'library': job['library'], 'stage': job['stage'], 'status': 'running',
                     'started_at': stamp(), 'attempt': attempt.name, 'command_sha256': digest(job['command'])}
            atomic(attempt / 'command.json', {'command': job['command'], 'cwd': str(release)})
            atomic(folder / 'state.json', state)
            artifact = Path(job.get('complete_artifact', Path(job['output']) / ('completion.json' if job['stage'] == 'readme' else 'result.json'))).resolve()
            try:
                with mutex:
                    if stopped.is_set():
                        raise InterruptedError('Queue stopped')
                    process = subprocess.Popen(job['command'], cwd=release, env=env, stdout=subprocess.PIPE,
                                               stderr=subprocess.STDOUT, text=True, errors='replace',
                                               start_new_session=True, pass_fds=(lock.fileno(),))
                    processes[name] = process
                with (attempt / 'console.log').open('a', buffering=1) as log:
                    for line in process.stdout:
                        log.write(line.replace(secret, '[REDACTED]'))
                process.stdout.close()
                result = process.wait()
                state.update(exit_code=result, status='complete' if result == 0 and artifact.is_file() else 'failed')
                if state['status'] == 'complete':
                    state.update(artifact=str(artifact), artifact_sha256=digest(artifact.read_bytes()))
            except Exception as exc:
                state.update(status='failed', error_type=type(exc).__name__)
            finally:
                with mutex:
                    processes.pop(name, None)
            state['finished_at'] = stamp()
            atomic(attempt / 'result.json', state)
            atomic(folder / 'state.json', state)
            return state
        handlers = {}
        if threading.current_thread() is threading.main_thread():
            for sig in (signal.SIGINT, signal.SIGTERM):
                handlers[sig] = signal.signal(sig, stop)
        try:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                active = {}
                while pending or active:
                    while pending and len(active) < workers and not stopped.is_set():
                        job = pending.pop(0)
                        active[pool.submit(run, job)] = job['id']
                        statuses[job['id']] = {'status': 'running'}
                    atomic(directory / 'summary.json', {'updated_at': stamp(), 'jobs': statuses})
                    if not active:
                        break
                    ready, _ = wait(active, timeout=5, return_when=FIRST_COMPLETED)
                    for future in ready:
                        statuses[active.pop(future)] = future.result()
        finally:
            for sig, handler in handlers.items():
                signal.signal(sig, handler)
        summary = {'updated_at': stamp(), 'jobs': statuses, 'complete': all(s['status'] == 'complete' for s in statuses.values())}
        atomic(directory / 'summary.json', summary)
        return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--key-file', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    result = supervise(json.loads(args.plan.read_text()), args.key_file, args.workers)
    print(json.dumps({'complete': result['complete'], 'jobs': {k: v['status'] for k, v in result['jobs'].items()}}))
    return 0 if result['complete'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
