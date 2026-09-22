"""Bounded JSON subprocess adapters, atomic evidence, and exclusive ownership."""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from .ablation import load


def atomic_json(path, value):
    """Replace a complete checkpoint atomically; never leave half-written JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    os.replace(temporary, path)


@contextmanager
def ownership(directory):
    """Hold one OS lock for the writer; process exit releases a stale lock."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / '.lock').open('a+') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError('Another worker owns this output directory') from exc
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def _stop_process_group(process):
    """Stop descendants in this invocation's private group, returning cleanup errors."""
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return None  # The group has already exited.
    except PermissionError as exc:
        # Some host sandboxes deny group signals. Still stop our direct child,
        # and record that descendant cleanup could not be confirmed.
        if process.poll() is None:
            process.kill()
        return str(exc)
    return None


def invoke(command, request, directory, timeout):
    """No shell. Keep full logs, including failed and interrupted attempts.

    Commands are trusted local adapters, not model-provided commands. Adapter
    implementations must isolate generated programs themselves.
    """
    directory = Path(directory)
    if (directory / 'process.json').exists():
        result = load(directory / 'process.json')
        if load(directory / 'request.json') != request:
            raise ValueError('Cached process request changed')
        return result
    directory.mkdir(parents=True, exist_ok=False)
    atomic_json(directory / 'request.json', request)
    started = time.monotonic()
    status, payload = 'adapter_error', None
    with (directory / 'stdout.txt').open('w') as stdout, (directory / 'stderr.txt').open('w') as stderr:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                                   cwd=directory, text=True, start_new_session=True)
        try:
            process.communicate(json.dumps(request, allow_nan=False), timeout=timeout)
            if process.returncode == 0:
                try:
                    payload = json.loads((directory / 'stdout.txt').read_text())
                    if isinstance(payload, dict):
                        status = 'ok'
                except (ValueError, UnicodeError):
                    pass
        except subprocess.TimeoutExpired:
            status = 'timeout'
            _stop_process_group(process)
            process.communicate()
        except BaseException:
            _stop_process_group(process)
            process.wait()
            raise
        finally:
            # Nested compilers/debuggers can leave children after adapter failure.
            # Every invocation owns a new process group, so cleanup is scoped.
            cleanup_error = _stop_process_group(process)
    result = {'status': status, 'returncode': process.returncode,
              'seconds': time.monotonic() - started, 'payload': payload}
    if cleanup_error:
        result['cleanup_error'] = cleanup_error
    atomic_json(directory / 'process.json', result)
    return result


def next_directory(parent, prefix):
    """Never overwrite partial work left by a killed process."""
    parent = Path(parent)
    numbers = [int(p.name[len(prefix):]) for p in parent.glob(prefix + '*')
               if p.is_dir() and p.name[len(prefix):].isdigit()]
    return parent / f'{prefix}{max(numbers, default=0) + 1:03d}'
