"""Run one local test in an owned POSIX process group.

This is lifecycle isolation, not a sandbox. Descendants that deliberately leave
the process group need OS/container containment; unsupported platforms fail closed.
"""
import os
import json
from pathlib import Path
from functools import wraps
import fcntl
import signal
import subprocess
import time
import hashlib
import tempfile


class CleanupError(RuntimeError):
    """The runner cannot certify that its timed-out process group stopped."""


def exclusive_work_dir(function):
    """Hold one checkpoint/test-file writer for the entire native evaluation."""
    @wraps(function)
    def wrapped(cfg, *args, **kwargs):
        execute = (cfg.comprehension or {}).get('execute', {})
        if not execute:
            return function(cfg, *args, **kwargs)
        work = (cfg.root / execute.get('work_dir', '.aideal_exec')).resolve()
        work.mkdir(parents=True, exist_ok=True)
        with (work / '.aideal_execution.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if (work / '.aideal_unreconciled_process.json').exists():
                raise CleanupError('Unreconciled process evidence; evaluation blocked before model work')
            return function(cfg, *args, **kwargs)
    return wrapped



def _decode_output(stdout, stderr, cwd):
    """Decode process bytes without discarding invalid bytes or changing verdicts.

    Keep exact bytes only for invalid UTF-8 streams, with a hash-bound receipt.
    Printable backslash escapes make diagnostics safe to store as JSON/text.
    Universal newlines preserve the previous text-mode behavior on valid output.
    """
    values, raw_streams = [], {}
    for name, raw in (("stdout", stdout), ("stderr", stderr)):
        raw = raw or b""
        if isinstance(raw, str):  # Supports existing process doubles in tests.
            raw = raw.encode("utf-8")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="backslashreplace")
            # A unique file prevents a generated program from selecting a
            # symlink destination for the operator's binary evidence.
            with tempfile.NamedTemporaryFile(prefix=f"aideal-{name}-", suffix=".raw",
                                             dir=cwd, delete=False) as saved:
                saved.write(raw)
                path = Path(saved.name).resolve()
            raw_streams[name] = {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
                                 "bytes": len(raw)}
        values.append(text.replace("\r\n", "\n").replace("\r", "\n"))
    return (*values, {"version": "utf8-backslashreplace-v1", "encoding": "utf-8",
                     "errors": "backslashreplace", "raw_streams": raw_streams})

def run_command(command, *, cwd, env, timeout, guard_dir=None):
    if os.name != 'posix':
        raise RuntimeError('Process-group execution requires POSIX; configure a supported runner')
    # A per-attempt cwd still shares the evaluation's process-cleanup guard.
    blocked = Path(guard_dir or cwd) / '.aideal_unreconciled_process.json'
    if blocked.exists():
        raise CleanupError(f'Unreconciled process evidence at {blocked}; execution blocked')
    # The controller needs provider credentials; generated test programs do not.
    # Copy first so removing credentials never changes the model caller's env.
    child_env = dict(env)
    for name in tuple(child_env):
        if name.endswith(('_API_KEY', '_API_TOKEN', '_ACCESS_TOKEN', '_SECRET_ACCESS_KEY')):
            child_env.pop(name)
    proc = subprocess.Popen(command, shell=True, cwd=cwd, env=child_env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=False, start_new_session=True)
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        stdout, stderr, receipt = _decode_output(stdout, stderr, cwd)
        result = subprocess.CompletedProcess(command, proc.returncode, stdout, stderr)
        result.output_decoding = receipt
        return result
    except BaseException as exc:
        def uncertain(message, cause):
            temporary = blocked.with_suffix(f'.{os.getpid()}.tmp')
            temporary.write_text(json.dumps({'process_group': proc.pid, 'reason': message,
                                            'recorded_epoch': time.time()}) + '\n')
            temporary.replace(blocked)
            raise CleanupError(message) from cause
        # Kill the group even if its shell has already exited: children may remain.
        denied = None
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(proc.pid, sig)
            except ProcessLookupError:
                pass
            except PermissionError as error:
                denied = error
                break
            if sig == signal.SIGTERM:
                time.sleep(.1)
        try:
            stdout, stderr = proc.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            # An escaped process may hold a pipe. Never wait without a bound.
            proc.stdout.close()
            proc.stderr.close()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                uncertain(f'Process group {proc.pid} did not stop; manual reconciliation required', exc)
            stdout, stderr = '', 'Output pipe remained open outside the owned process group'
        if denied is not None:
            uncertain(f'Permission denied stopping process group {proc.pid}; '
                      'do not resume this output namespace until reconciled', denied)
        if isinstance(exc, subprocess.TimeoutExpired):
            exc.output, exc.stderr, receipt = _decode_output(stdout, stderr, cwd)
            exc.output_decoding = receipt
            exc.cleanup = {'process_group': proc.pid, 'termination_requested': True,
                           'shell_reaped': proc.returncode is not None}
        raise
