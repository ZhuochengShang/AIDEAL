"""Language-specific diagnostic classification and source-stack-frame attribution."""
from __future__ import annotations

import re


_FRAME_RE = re.compile(r"\(([A-Za-z0-9_$]+\.(?:scala|java)):(\d+)\)"
                       r"|File \"[^\"]*?([A-Za-z0-9_]+\.py)\", line (\d+)")


def _classify_error_py(merged: str, rc: int, error_marker: str) -> tuple[str, str, str]:
    """Classify observed diagnostics without claiming an environmental cause.

    An unavailable import may be a missing dependency, a nonexistent model-chosen
    module, or a version error. Only a separate setup probe can distinguish them.
    Keep these failures in the selected denominator pending that evidence.
    """
    import re as _re
    invalid_symbol = _re.search(r"ImportError: cannot import name (.+)", merged)
    if invalid_symbol:
        return "api-import", invalid_symbol.group(0)[:300], ""
    m = _re.search(r"(?:ModuleNotFoundError|ImportError)[:\s]+(.+)", merged)
    if m:
        return "dependency-unverified", f"missing module/import: {m.group(1).strip()[:200]}", ""
    m = _re.search(r"^(?:SyntaxError|IndentationError|TabError)[:\s]+(.+)$", merged, _re.M)
    if m:
        loc = _re.search(r'File "([^"]+)", line (\d+)', merged)
        return "compile", m.group(0).strip()[:300], (f"{loc.group(1)}:{loc.group(2)}" if loc else "")
    if error_marker and error_marker in merged:
        line = next((l for l in merged.splitlines() if error_marker in l), "").strip()
        msg = line.split(error_marker, 1)[-1].strip()
        frames = _re.findall(r'File "([^"]+\.py)", line (\d+)', merged)
        locus = f"{frames[-1][0]}:{frames[-1][1]}" if frames else ""
        return "runtime", msg or "runtime error", locus
    m = _re.search(r"^(\w*(?:Error|Exception)\b.*)$", merged, _re.M)
    if m:
        return "runtime", m.group(1).strip()[:300], ""
    return "unknown", (merged.strip()[-300:] or f"exit {rc}"), ""


def _classify_error_java(merged: str, rc: int, error_marker: str) -> tuple[str, str, str]:
    """Java flavor: distinguish javac diagnostics, missing classpath entries,
    and exceptions raised by an otherwise runnable harness."""
    import re as _re
    im = _re.search(
        r"(?:NoClassDefFoundError|ClassNotFoundException)[:\s]+([\w/.$]+)", merged)
    if im:
        return "dependency-unverified", f"missing dependency on classpath: {im.group(1)}", ""
    cm = _re.search(r"^([^\n]+\.java):(\d+): error: (.+)$", merged, _re.M)
    if cm:
        return "compile", cm.group(0).strip()[:300], f"{cm.group(1)}:{cm.group(2)}"
    if error_marker and error_marker in merged:
        line = next((line for line in merged.splitlines() if error_marker in line), "").strip()
        msg = line.split(error_marker, 1)[-1].strip()
        frame = _re.search(r"\bat [\w.$]+\(([^:()]+\.java):(\d+)\)", merged)
        locus = f"{frame.group(1)}:{frame.group(2)}" if frame else ""
        return "runtime", msg or "runtime exception", locus
    exc = _re.search(r"^(?:Exception in thread \"[^\"]+\" )?([\w.$]+(?:Exception|Error): .+)$",
                     merged, _re.M)
    if exc:
        return "runtime", exc.group(1).strip()[:300], ""
    return "unknown", (merged.strip()[-300:] or f"exit {rc}"), ""


def _classify_error(merged: str, rc: int, error_marker: str,
                    language: str = "scala") -> tuple[str, str, str]:
    """Return (category, message, locus) from the run output.
    Categories describe symptoms; dependency-unverified needs a setup probe.
    No diagnostic substring alone proves a setup failure."""
    import re as _re
    if rc == 124:
        return "timeout", "execution timed out", ""
    if language.lower() == "python":
        return _classify_error_py(merged, rc, error_marker)
    if language.lower() == "java":
        return _classify_error_java(merged, rc, error_marker)
    # A generated program may request a nonexistent class. Class-loading errors
    # flag dependency review; they do not by themselves remove a trial from the
    # denominator or prove that the configured classpath is incomplete.
    im = _re.search(r"(?:NoClassDefFoundError|ClassNotFoundException)[:\s]+([\w/.$]+)", merged)
    if im:
        return "dependency-unverified", f"missing dependency on classpath: {im.group(1)}", ""
    # compile-time classpath gap: scalac can't read a referenced class from the jars
    # (inner-class / version mismatch). Confirm with an independent setup probe.
    if _re.search(r"Unable to locate class corresponding to inner class|"
                  r"class file needed by .* is missing|missing or invalid dependency detected", merged):
        return "dependency-unverified", "compile-time classpath/version gap (missing or mismatched jar)", ""
    # runtime: the scaffold prints __RUN_ERR__ <Class>: <msg>
    if error_marker and error_marker in merged:
        line = next((l for l in merged.splitlines() if error_marker in l), "").strip()
        msg = line.split(error_marker, 1)[-1].strip()
        # first app stack frame = the failing call site
        frame = next((l.strip() for l in merged.splitlines()
                      if l.strip().startswith("at ") and ".scala" in l), "")
        return "runtime", msg or "runtime error", frame
    # compile: scalac prints `<file>.scala:NN: error: <msg>`
    cm = _re.search(r"^(.*\.scala:\d+: error: .*)$", merged, _re.MULTILINE)
    if cm:
        return "compile", cm.group(1).strip(), cm.group(1).split(":")[0:2] and cm.group(1).split(" error:")[0].strip()
    return "unknown", (merged.strip()[-300:] or f"exit {rc}"), ""


def _codebase_frames(merged: str, file_index: dict[str, str], limit: int = 5) -> list[str]:
    """Extract the CODEBASE source lines exercised by a failing run: JVM stack
    frames `at pkg.Cls.m(File.scala:123)` whose file basename belongs to the
    target repo (via `file_index` basename→relative-path). Answers "which
    RDPro line did the snippet actually reach" for runtime failures."""
    out: list[str] = []
    seen: set[str] = set()
    for m in _FRAME_RE.finditer(merged):
        base, ln = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
        rel = file_index.get(base)
        if not rel:
            continue
        key = f"{rel}:{ln}"
        if key not in seen:
            seen.add(key)
            out.append(key)
            if len(out) >= limit:
                break
    return out
