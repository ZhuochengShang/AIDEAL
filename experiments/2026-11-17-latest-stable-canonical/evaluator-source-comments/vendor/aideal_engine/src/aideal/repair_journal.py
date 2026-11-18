"""Durable document-repair phases and lifetime round state.

A completed phase is reused. A known failed provider call can be retried. An
abandoned in-flight phase is ambiguous and fails closed instead of silently
issuing an extra rewrite. Reconciliation is an explicit future operator action.
"""
from contextlib import contextmanager
import fcntl
import glob
import json
import os
import time
from pathlib import Path

from .experiment_identity import digest, prompt_contract, transport_contract
from .prompts import DEFAULT_PROMPTS, prompts_dir
from .execution import CleanupError


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f'.{os.getpid()}.tmp')
    with tmp.open('w') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    tmp.replace(path)


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f'.{os.getpid()}.tmp')
    with tmp.open('w') as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())
    tmp.replace(path)


@contextmanager
def document_lock(document):
    lock_path = Path(document).with_suffix('.docfix.lock')
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def identity(cfg, policy):
    context = prompt_contract(cfg)
    for name in ('deep_dive', 'docfix_diagnose', 'docfix_rewrite'):
        path = prompts_dir(cfg) / f'aideal/{name}.md'
        if not path.exists():
            path = DEFAULT_PROMPTS / f'aideal/{name}.md'
        context['templates'][name] = digest(path.read_bytes())
    source = {}
    for pattern in [*cfg.source_globs, *cfg.test_globs]:
        for value in glob.glob(str(cfg.root / pattern), recursive=True):
            path = Path(value)
            if path.is_file():
                source[str(path.relative_to(cfg.root))] = digest(path.read_bytes())
    baseline = policy.get('target_source')
    return digest({'schema': 4, 'policy': policy, 'configuration': cfg.raw,
                   'context': context, 'transport': transport_contract(), 'source': source,
                   'baseline': digest(Path(baseline).read_bytes()) if baseline and Path(baseline).is_file() else None,
                   'engine': {name: digest(Path(__file__).with_name(name).read_bytes()) for name in
                              ('docfix.py', 'doc_repair.py', 'repair_journal.py', 'deepdive.py')}})


class UncertainPhase(RuntimeError):
    pass


class RepairJournal:
    def __init__(self, path, identity, initial):
        self.path = Path(path)
        if self.path.exists():
            self.state = json.loads(self.path.read_text())
            if self.state.get('identity') != identity or self.state.get('schema') != 4:
                raise ValueError('Document repair inputs changed; use a new namespace')
        else:
            self.state = {'schema': 4, 'identity': identity, 'initial': initial,
                          'rounds': [], 'context': {}, 'phases': {}}
            self.save()

    def save(self):
        atomic(self.path, self.state)

    def phase(self, number, name, action):
        key = f'{number}:{name}'
        row = self.state['phases'].get(key, {})
        if row.get('status') == 'complete':
            return row['result']
        if row.get('status') in ('started', 'uncertain'):
            raise UncertainPhase(f'{key} has an unacknowledged invocation; inspect before retrying')
        attempts = list(row.get('attempts', []))
        started = time.time()
        previous_end = attempts[-1].get('ended_epoch') if attempts else None
        attempts.append({'status': 'started', 'started_epoch': started,
                         'since_previous_end_s': started - previous_end if previous_end else None})
        row = {'status': 'started', 'attempts': attempts}
        self.state['phases'][key] = row
        self.save()
        try:
            value = action()
        except Exception as exc:
            row.update(status='uncertain' if isinstance(exc, CleanupError) else 'retryable_error',
                       error_type=type(exc).__name__, error=str(exc))
            attempts[-1].update(status='error', error_type=type(exc).__name__,
                                ended_epoch=time.time(), wall_s=time.time()-started)
            self.save()
            raise
        row.update(status='complete', result=value)
        attempts[-1].update(status='complete', ended_epoch=time.time(), wall_s=time.time()-started)
        self.save()
        return value

    def checkpoint(self, rounds, context):
        self.state['rounds'], self.state['context'] = list(rounds), dict(context)
        self.save()
