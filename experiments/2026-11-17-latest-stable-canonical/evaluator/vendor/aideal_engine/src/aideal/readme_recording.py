"""Exact, durable author-call receipts for isolated README generation.

Successful requests replay only after request/response hash verification. Failed
or interrupted requests retain their own directory; a later invocation creates a
new attempt. One failure always stops the current generation invocation.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
import uuid

from .readme_validation import POLICY, validate_entry


class ReadmeGenerationStopped(RuntimeError):
    """A recorded author call failed or returned an unusable entry."""


def digest(value):
    data = value if isinstance(value, bytes) else json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(data).hexdigest()


def atomic_bytes(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('xb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_json(path, value):
    atomic_bytes(path, (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode())


class ReadmeCallRecorder:
    def __init__(self, directory, binding, replay=None):
        self.directory = Path(directory)
        self.binding = binding
        self.reused_calls = 0
        self.new_calls = 0
        self.replay = replay

    def invoke(self, spec, system, user, *, phase, api=None, source_docs=()):
        from .llm import invoke_text, usage_snapshot, usage_delta
        request = {'schema': 1, 'binding': self.binding, 'provider': spec.provider,
                   'model': spec.model, 'phase': phase, 'api': api,
                   'system': system, 'user': user}
        identity = digest(request)
        root = self.directory / identity
        root.mkdir(parents=True, exist_ok=True)
        attempts = sorted(root.glob('attempt_*'))
        for attempt in attempts:
            saved_request = json.loads((attempt / 'request.json').read_text())
            if saved_request != request:
                raise ValueError('Saved README request changed')
            state_path = attempt / 'provider.json'
            if not state_path.exists():
                continue  # Interrupted before/after the request: preserve uncertainty.
            state = json.loads(state_path.read_text())
            if state.get('request_sha256') != identity:
                raise ValueError('Saved README request binding changed')
            if state.get('status') != 'complete':
                continue
            response = (attempt / 'response.txt').read_bytes()
            if digest(response) != state.get('response_sha256'):
                raise ValueError('Saved README response changed')
            text = response.decode()
            self._validate(text, api, source_docs)
            self.reused_calls += 1
            return text
        if self.replay is not None:
            text = self.replay.lookup(request, source_docs)
            if text is not None:
                self.reused_calls += 1
                return text
        number = max([int(p.name.split('_')[1]) for p in attempts] or [0]) + 1
        attempt = root / f'attempt_{number:04d}'
        attempt.mkdir()
        atomic_json(attempt / 'request.json', request)
        state = {'schema': 1, 'request_sha256': identity, 'status': 'started',
                 'started_at': datetime.now(timezone.utc).isoformat(),
                 'attempt_number': number, 'usage': None, 'validation_policy': POLICY}
        atomic_json(attempt / 'provider.json', state)
        started, before = time.monotonic(), usage_snapshot()
        self.new_calls += 1
        try:
            text = invoke_text(spec, system, user)
            if not isinstance(text, str):
                raise ValueError('Author response must be text')
            response = text.encode()
            atomic_bytes(attempt / 'response.txt', response)
            state['response_sha256'] = digest(response)
            self._validate(text, api, source_docs)
        except BaseException as exc:
            usage = usage_delta(before)
            state.update(status='failed_or_interrupted', error_type=type(exc).__name__,
                         usage=usage if usage.get('calls') else None,
                         finished_at=datetime.now(timezone.utc).isoformat(),
                         seconds=time.monotonic() - started)
            atomic_json(attempt / 'provider.json', state)
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                raise
            raise ReadmeGenerationStopped(
                f'Author call stopped ({type(exc).__name__}); evidence: {attempt}') from exc
        state.update(status='complete', usage=usage_delta(before),
                     finished_at=datetime.now(timezone.utc).isoformat(),
                     seconds=time.monotonic() - started)
        atomic_json(attempt / 'provider.json', state)
        return text

    @staticmethod
    def _validate(text, api, source_docs=()):
        validate_entry(text, api, source_docs)
