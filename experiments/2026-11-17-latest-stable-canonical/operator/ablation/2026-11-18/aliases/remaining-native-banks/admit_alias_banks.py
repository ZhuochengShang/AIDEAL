"""Study-local serial admission; existing immutable supervisors own model calls."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def stamp():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2) + '\n')
    tmp.replace(path)


def exact_ids(expected, listed, coverage, count):
    if (len(expected) != count or len(set(expected)) != count
            or len(listed) != count or len(set(listed)) != count
            or set(expected) != set(listed)
            or coverage['requested_definitions'] != count
            or coverage['planned_definitions'] != count
            or coverage['omitted_requested_definitions'] != 0):
        raise ValueError('Preview differs from the exact Original API identity set')


def preflight(plan):
    """Validate every prepared source/context binding before credentialed launch."""
    release = Path(plan['release'])
    sys.path[:0] = [str(release), str(release / 'vendor/aideal_engine/src')]
    from workflow.ablation import digest, verify_artifact
    from workflow.improvement_suggestions import _load_preview, _model_settings
    from workflow.preparation import _engine_config_module
    from aideal.doc_check_sources import _load_manifest
    job = plan['jobs'][0]
    args = job['command']
    get = lambda flag: args[args.index(flag) + 1]
    manifest_path = Path(get('--preview'))
    manifest = json.loads(manifest_path.read_text())
    if manifest['context_policy'] != 'calling-facts-and-source-v1':
        raise ValueError('Unexpected preview context policy')
    if _model_settings(get('--model-config'))['proposal_scope'] != 'aliases_only':
        raise ValueError('Unexpected proposal scope')
    if manifest['manifest_sha256'] != digest({k: v for k, v in manifest.items() if k != 'manifest_sha256'}):
        raise ValueError('Manifest digest changed')
    cfg = _engine_config_module().load_config(get('--original-config'))
    expected = _load_manifest(cfg, get('--original-manifest'))
    listed = [a for b in manifest['batches'] for a in b['api_ids']]
    exact_ids(expected, listed, manifest['coverage'], int(get('--expected-apis')))
    for ref in manifest['artifacts']:
        if not verify_artifact(ref):
            raise ValueError('Prepared input changed: ' + ref['path'])
    for batch in manifest['batches']:
        if not verify_artifact(batch['preview']):
            raise ValueError('Prepared batch changed')
        _load_preview(batch['preview']['path'])
    return {'selected': len(expected), 'batches': len(manifest['batches']),
            'manifest_sha256': sha(manifest_path), 'all_input_hashes_verified': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--operator', type=Path, required=True)
    parser.add_argument('--key-file', required=True)
    parser.add_argument('--wait-seconds', type=int, default=3600)
    args = parser.parse_args()
    operator = args.operator.resolve()
    directory = operator / 'serial-admission'
    directory.mkdir(exist_ok=True)
    banks = ['rdpro_java', 'rdpro_scala', 'tslearn', 'mdanalysis', 'thumbnailator']
    plans = {bank: operator / ('ALIASES_ONLY_PLAN.' + bank + '.json') for bank in banks}
    binding = {'order': banks, 'plans': {bank: sha(path) for bank, path in plans.items()},
               'controller_sha256': sha(__file__), 'workers': 1}
    status = {'started_at': stamp(), 'pid': os.getpid(), 'banks': [], 'status': 'running',
              'source_installation': False}
    with (directory / 'queue.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        frozen = directory / 'binding.json'
        if frozen.exists() and json.loads(frozen.read_text()) != binding:
            raise ValueError('Admission inputs changed; preserve this queue and use a new operator path')
        if not frozen.exists():
            write(frozen, binding)
        current = None
        try:
            for bank, path in plans.items():
                current = {'bank': bank, 'status': 'preflight', 'started_at': stamp()}
                status['banks'].append(current)
                write(directory / 'state.json', status)
                if sha(path) != binding['plans'][bank]:
                    raise ValueError('Bank plan changed')
                plan = json.loads(path.read_text())
                job = plan['jobs'][0]
                folder = Path(plan['root']) / 'supervisor'
                state_file = folder / job['id'] / 'state.json'
                # Respect the existing supervisor lock, including a worker inheriting it.
                deadline = time.monotonic() + args.wait_seconds
                while (folder / 'queue.lock').exists():
                    with (folder / 'queue.lock').open('a') as other:
                        try:
                            fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)
                            break
                        except BlockingIOError:
                            if time.monotonic() >= deadline:
                                raise TimeoutError('An existing bank worker is still active')
                            time.sleep(15)
                old = json.loads(state_file.read_text()) if state_file.exists() else {}
                if old.get('status') == 'complete':
                    if sha(old['artifact']) != old['artifact_sha256']:
                        raise ValueError('Completed artifact changed')
                    current['preflight'] = preflight(plan)
                    complete = json.loads(Path(old['artifact']).read_text())
                    if sha(complete['collection']) != complete['collection_sha256']:
                        raise ValueError('Completed collection changed')
                    if sha(complete['original_manifest']) != complete['original_manifest_sha256']:
                        raise ValueError('Completed Original manifest changed')
                    current.update(status='complete', reused=True, artifact=old['artifact'],
                                   finished_at=old['finished_at'])
                    write(directory / 'state.json', status)
                    continue
                if old.get('status') in ('failed', 'running'):
                    raise ValueError('Prior bank job requires diagnosis; automatic retry disabled')
                command_args = job['command']
                argument = lambda flag: Path(command_args[command_args.index(flag) + 1])
                preview_path = argument('--preview')
                deadline = time.monotonic() + args.wait_seconds
                while not preview_path.is_file():
                    if time.monotonic() >= deadline:
                        raise TimeoutError('Prepared preview is missing; no model call was made')
                    current['status'] = 'waiting_for_preview'
                    write(directory / 'state.json', status)
                    time.sleep(15)
                current['preflight'] = preflight(plan)
                receipt_path = argument('--preparation-progress')
                if receipt_path.name != 'PREPARATION.json':
                    raise ValueError('New jobs must bind an immutable per-bank preparation receipt')
                receipt = {'banks': [{'bank': bank, 'status': 'previewed_unvalidated',
                                      **current['preflight']}], 'model_calls': 0}
                if receipt_path.exists() and json.loads(receipt_path.read_text()) != receipt:
                    raise ValueError('Immutable preparation receipt changed')
                if not receipt_path.exists():
                    write(receipt_path, receipt)
                current['status'] = 'running'
                write(directory / 'state.json', status)
                command = [job['command'][0], str(Path(plan['release']) / 'scripts/run_cluster_experiment.py'),
                           '--plan', str(path), '--key-file', args.key_file, '--workers', '1']
                with (directory / (bank + '.log')).open('a') as log:
                    child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                             stdin=subprocess.DEVNULL, pass_fds=(lock.fileno(),))
                    current['supervisor_pid'] = child.pid
                    write(directory / 'state.json', status)
                    code = child.wait()
                result = json.loads(state_file.read_text()) if state_file.exists() else {}
                if code or result.get('status') != 'complete':
                    current.update(supervisor_exit=code, supervisor_state=result)
                    raise RuntimeError('Bank did not complete; later banks were not launched')
                if sha(result['artifact']) != result['artifact_sha256']:
                    raise ValueError('Completed artifact changed')
                current.update(status='complete', artifact=result['artifact'], finished_at=stamp())
                write(directory / 'state.json', status)
            status.update(status='complete_unvalidated', finished_at=stamp())
            write(directory / 'state.json', status)
            return 0
        except Exception as exc:
            if current:
                current.update(status='stopped', error=str(exc), error_type=type(exc).__name__)
            status.update(status='stopped', finished_at=stamp())
            write(directory / 'state.json', status)
            return 2


if __name__ == '__main__':
    raise SystemExit(main())
