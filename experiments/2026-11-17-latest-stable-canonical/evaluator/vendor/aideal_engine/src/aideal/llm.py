"""Provider abstraction with author/audience/fixer role separation.

Author models WRITE documentation and tests (small/cheap is fine).
Audience models CONSUME documentation to write code (the coding agent).
Fixer models repair failing snippets in the fix loop (defaults to audience;
map `roles: fixer` to compare e.g. Gemini-as-fixer vs the audience model).

Supported providers: openai (chat completions), openai-responses/codex (the
Responses API — Codex-style endpoint), anthropic, google, ollama (for
Kimi/Qwen/local open-source models). Imports are lazy so only the used
provider's package is required.
"""

from __future__ import annotations

import os
from pathlib import Path
import time

from .config import ModelSpec


def get_chat_model(spec: ModelSpec, temperature: float = 0.0):
    """Return a LangChain chat model for the given provider/model."""
    provider = spec.provider.lower()
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=spec.model, temperature=temperature)
    if provider in ("openai-responses", "codex"):
        # OpenAI Responses API — the Codex-style endpoint, the "codex api" arm
        # of the backend micro-benchmark (vs plain chat-completions "openai").
        # Codex/reasoning models reject non-default temperature, so none is set.
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=spec.model, use_responses_api=True)
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=spec.model, temperature=temperature)
    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        # A socket waiting for response headers previously blocked an experiment
        # for >80 minutes. Bound each provider request while retaining retries;
        # both knobs are environment-overridable and do not change prompts,
        # scoring, or the logical fix-round treatment.
        timeout = float(os.environ.get("AIDEAL_GOOGLE_REQUEST_TIMEOUT_S", "300"))
        retries = int(os.environ.get("AIDEAL_GOOGLE_MAX_RETRIES", "2"))
        return ChatGoogleGenerativeAI(
            model=spec.model,
            temperature=temperature,
            request_timeout=timeout,
            retries=retries,
        )
    if provider == "ollama":
        import os as _os
        from langchain_ollama import ChatOllama
        # Ollama's DEFAULT context (~4K) silently truncates AIDEAL's prompts
        # (entry + source window + type context ≈ 6-10K tokens) — the local
        # arm would fail for truncation, not model quality. 16K default;
        # override with AIDEAL_OLLAMA_NUM_CTX (raise for 32B models w/ RAM).
        return ChatOllama(model=spec.model, temperature=temperature,
                          num_ctx=int(_os.environ.get("AIDEAL_OLLAMA_NUM_CTX", 16384)))
    raise ValueError(f"Unknown provider: {spec.provider}")


# ---------------------------------------------------------------------------
# Token accounting. Every invoke_text() adds the PROVIDER-REPORTED usage
# (LangChain usage_metadata, not a local tokenizer) to a module accumulator;
# benchmark code snapshots it before/after a unit of work (one API's
# comprehension loop) and stores the delta.
_USAGE: dict = {"calls": 0, "input_tokens": 0, "output_tokens": 0, "by_model": {}}


def _wait_for_provider_slot(spec: ModelSpec) -> None:
    """Process-shared request-start pacing for Google/Gemini.

    Parallel repository workers use the same small state file.  ``flock`` is
    released automatically if a worker crashes, and the timestamp makes a
    restarted worker continue the same minimum-spacing policy.  The gate is
    intentionally applied immediately before ``invoke``; prompt construction
    and local execution remain parallel.
    """
    if spec.provider.lower() != "google":
        return
    interval = float(os.environ.get("AIDEAL_GOOGLE_MIN_INTERVAL_S", "0") or 0)
    if interval <= 0:
        return

    import fcntl

    state_path = Path(os.environ.get(
        "AIDEAL_GOOGLE_RATE_STATE", "/tmp/aideal_google_rate_gate.txt"))
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.open("a+", encoding="utf-8") as state:
        fcntl.flock(state.fileno(), fcntl.LOCK_EX)
        state.seek(0)
        try:
            last_start = float((state.read() or "0").strip())
        except ValueError:
            last_start = 0.0
        delay = interval - (time.time() - last_start)
        if 0 < delay <= interval:
            time.sleep(delay)
        state.seek(0)
        state.truncate()
        state.write(f"{time.time():.9f}\n")
        state.flush()
        os.fsync(state.fileno())
        fcntl.flock(state.fileno(), fcntl.LOCK_UN)


def reset_usage() -> None:
    _USAGE.update({"calls": 0, "input_tokens": 0, "output_tokens": 0, "by_model": {}})


def usage_snapshot() -> dict:
    """Copy of the running usage totals (safe to keep across further calls)."""
    return {"calls": _USAGE["calls"], "input_tokens": _USAGE["input_tokens"],
            "output_tokens": _USAGE["output_tokens"],
            "by_model": {k: dict(v) for k, v in _USAGE["by_model"].items()}}


def usage_delta(before: dict) -> dict:
    """Usage accumulated since `before` (a usage_snapshot()), incl. per-model
    split — in a mixed-role run (writer=openai, fixer=gemini) the split shows
    who spent what."""
    now = usage_snapshot()
    by_model = {}
    for k, v in now["by_model"].items():
        b = before.get("by_model", {}).get(k, {})
        d = {kk: v[kk] - b.get(kk, 0) for kk in ("calls", "input_tokens", "output_tokens")}
        if any(d.values()):
            by_model[k] = d
    return {"calls": now["calls"] - before["calls"],
            "input_tokens": now["input_tokens"] - before["input_tokens"],
            "output_tokens": now["output_tokens"] - before["output_tokens"],
            "by_model": by_model}


def invoke_text(spec: ModelSpec, system: str, user: str) -> str:
    """One-shot text completion; returns the model's text content and adds the
    provider-reported token usage to the module accumulator."""
    llm = get_chat_model(spec)
    _wait_for_provider_slot(spec)
    from .provider_deadline import provider_deadline
    import sys
    budget = 0.0
    if spec.provider.lower() == "google":
        budget = (float(os.environ.get("AIDEAL_GOOGLE_REQUEST_TIMEOUT_S", "300"))
                  * max(1, int(os.environ.get("AIDEAL_GOOGLE_MAX_RETRIES", "2"))) + 30)
    started = time.monotonic()
    print(f"[provider] start model={spec.provider}:{spec.model} wall_limit_s={budget:g}",
          file=sys.stderr, flush=True)
    try:
        with provider_deadline(budget):
            resp = llm.invoke([("system", system), ("user", user)])
    except Exception as exc:
        print(f"[provider] failed type={type(exc).__name__} wall_s={time.monotonic()-started:.1f}",
              file=sys.stderr, flush=True)
        raise
    print(f"[provider] complete wall_s={time.monotonic()-started:.1f}", file=sys.stderr, flush=True)
    u = getattr(resp, "usage_metadata", None) or {}
    _USAGE["calls"] += 1
    _USAGE["input_tokens"] += int(u.get("input_tokens") or 0)
    _USAGE["output_tokens"] += int(u.get("output_tokens") or 0)
    m = _USAGE["by_model"].setdefault(
        f"{spec.provider}:{spec.model}",
        {"calls": 0, "input_tokens": 0, "output_tokens": 0})
    m["calls"] += 1
    m["input_tokens"] += int(u.get("input_tokens") or 0)
    m["output_tokens"] += int(u.get("output_tokens") or 0)
    c = resp.content
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        # Responses-API (codex) and some providers return CONTENT BLOCKS —
        # [{'type':'text','text':...}, ...]. str(list) here poisoned codex
        # snippets ("[{'type': 'text', ...") — join the text blocks instead.
        parts = []
        for b in c:
            if isinstance(b, dict):
                parts.append(b.get("text") or b.get("content") or "")
            elif isinstance(b, str):
                parts.append(b)
        return "".join(parts)
    return str(c)
