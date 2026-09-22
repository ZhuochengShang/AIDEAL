"""Bound an entire blocking provider invocation on POSIX main threads.

SDK socket timeouts alone do not bound retries or slow response streams.
Other platforms/threads retain the SDK timeout. No background request remains
running after the deadline. Model prompts and generation settings are unchanged.
"""
from contextlib import contextmanager
import signal
import threading


class _DeadlineExpired(BaseException):
    """Bypass SDK retry handlers so the entire invocation unwinds."""


@contextmanager
def provider_deadline(seconds):
    supported = hasattr(signal, "setitimer") and threading.current_thread() is threading.main_thread()
    if not supported or seconds <= 0:
        yield
        return
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    # Do not steal an existing caller's alarm; its deadline already bounds us.
    if previous_timer[0] > 0:
        yield
        return

    def expire(signum, frame):
        raise _DeadlineExpired()

    signal.signal(signal.SIGALRM, expire)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    except _DeadlineExpired:
        raise TimeoutError(f"Provider invocation exceeded total wall deadline {seconds:g}s") from None
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
