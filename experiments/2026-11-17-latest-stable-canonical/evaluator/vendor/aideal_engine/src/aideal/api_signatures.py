"""Source signatures, documentation comments, and Python qualified identities."""
from __future__ import annotations

import glob as globmod
import ast
import re
from pathlib import Path
from .config import AidealConfig


def _split_top_level(inner: str) -> list[str]:
    """Split a parameter list on top-level commas (ignoring nested []/<>/()/{})."""
    out, depth, cur = [], 0, ""
    for ch in inner:
        if ch in "([{<":
            depth += 1
        elif ch in ")]}>":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip()); cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def _param_record(raw: str) -> dict:
    """Parse one parameter into {name, type, default}. Splits the default on a
    top-level `=` that is NOT the `=>` of a function type (e.g. `f: Int => Int`)."""
    parts = re.split(r"=(?!>)", raw, maxsplit=1)
    left = parts[0].strip()
    default = parts[1].strip() if len(parts) > 1 else ""
    if ":" in left:
        nm, typ = left.split(":", 1)
        return {"name": nm.strip(), "type": typ.strip(), "default": default}
    return {"name": left, "type": "", "default": default}


def _java_param_record(raw: str) -> dict:
    """Parse a Java parameter into the common structured form.

    Java places the type before the name rather than using Scala/Python's
    ``name: type`` form. Keep annotations/modifiers in the type evidence; the
    final whitespace-delimited token is the declared parameter name.
    """
    value = raw.strip()
    parts = value.rsplit(None, 1)
    if len(parts) == 1:
        return {"name": parts[0], "type": "", "default": ""}
    typ, name = parts
    # Java also permits ``String value[]``. Normalize the brackets onto the
    # type so downstream prompts see the actual identifier as ``value``.
    brackets = ""
    while name.endswith("[]"):
        brackets += "[]"
        name = name[:-2]
    return {"name": name, "type": typ + brackets, "default": ""}


_JAVA_MEMBER_MODIFIERS = {
    "public", "protected", "private", "static", "final", "abstract",
    "synchronized", "native", "strictfp", "default",
}


def _java_return_type(raw_signature: str, name: str) -> str:
    """Recover a Java method return type; constructors intentionally have none."""
    head = raw_signature.split("(", 1)[0].rstrip()
    if not head.endswith(name):
        return ""
    before = head[:-len(name)].strip()
    tokens = before.split()
    while tokens and tokens[0] in _JAVA_MEMBER_MODIFIERS:
        tokens.pop(0)
    if tokens and tokens[0].startswith("<"):
        # Generic method type parameters may contain spaces; consume through
        # the token whose angle brackets balance.
        depth = 0
        while tokens:
            token = tokens.pop(0)
            depth += token.count("<") - token.count(">")
            if depth <= 0:
                break
    return " ".join(tokens)


def _signature_at(lines: list[str], idx: int, def_pos: int, name_end: int
                  ) -> tuple[str, list[dict], str]:
    """From the def line return (raw_signature, params, return_type).

    Reads a forward window so multi-line parameter lists work. A `(...)` group
    counts as the value-parameter list ONLY if it sits immediately after the
    name (after optional `[type params]`); otherwise the def is paren-less
    (`def foo: T = body(...)`) and has no value parameters — this avoids
    grabbing parentheses from the method body. params are structured dicts.
    """
    window = lines[idx][def_pos:]
    for j in range(idx + 1, min(idx + 12, len(lines))):
        window += "\n" + lines[j]

    cur = name_end - def_pos                       # index in window right after the name
    n = len(window)

    def _skip_ws(c):
        while c < n and window[c].isspace():
            c += 1
        return c

    def _skip_balanced(c, open_ch, close_ch):
        depth = 0
        while c < n:
            if window[c] == open_ch:
                depth += 1
            elif window[c] == close_ch:
                depth -= 1
                if depth == 0:
                    return c + 1
            c += 1
        return c

    cur = _skip_ws(cur)
    if cur < n and window[cur] == "[":            # generic type params, e.g. [T]
        cur = _skip_balanced(cur, "[", "]")
    cur = _skip_ws(cur)

    params: list[dict] = []
    if cur < n and window[cur] == "(":            # value parameter list
        start = cur
        cur = _skip_balanced(cur, "(", ")")
        inner = window[start + 1:cur - 1].strip()
        params = [_param_record(p) for p in _split_top_level(inner)] if inner else []

    rm = re.match(r"\s*:\s*([^\n={]+)", window[cur:])
    ret = rm.group(1).strip() if rm else ""
    sig_end = cur + (rm.end() if rm else 0)
    raw = " ".join(window[:sig_end].split())
    return raw, params, ret


def _doc_below_py(lines: list[str], idx: int) -> str:
    """Python: the docstring sits BELOW the def line. Walk past the (possibly
    multi-line) signature to the line ending with `:`, then capture a
    triple-quoted docstring if it opens there. Returns '' when absent.

    (Before this existed, the `documented` intent signal fired 0x on Python
    codebases — Sedona audit 2026-07-06 — because _doc_above looks up.)"""
    j, n = idx, len(lines)
    # end of signature: first line at/after idx whose code part ends with ':'
    while j < n:
        code = lines[j].split("#", 1)[0].rstrip()
        if code.endswith(":"):
            break
        j += 1
        if j - idx > 20:                      # runaway guard: not a normal signature
            return ""
    j += 1
    while j < n and not lines[j].strip():
        j += 1
    if j >= n:
        return ""
    m = re.match(r'^\s*[rRbBuU]{0,2}("""|\'\'\')(.*)$', lines[j])
    if not m:
        return ""
    quote, rest = m.group(1), m.group(2)
    if quote in rest:                          # one-line docstring
        return rest.split(quote, 1)[0].strip()
    parts = [rest.strip()]
    for k in range(j + 1, min(n, j + 60)):
        if quote in lines[k]:
            parts.append(lines[k].split(quote, 1)[0].strip())
            break
        parts.append(lines[k].strip())
    return " ".join(p for p in parts if p).strip()


#: where each language's API docs live relative to the definition line.
#: "above" = comment block above (Scala/Java javadoc, Kotlin KDoc, Rust ///,
#: Go doc comments, C# XML docs...); "below" = docstring under the def
#: (Python). Extend here (or teach _doc_at a new style) for new languages.
_DOC_POSITION: dict[str, str] = {"python": "below"}


def _doc_at(cfg: AidealConfig, lines: list[str], idx: int) -> str:
    """Language-aware doc extraction for the def at line idx (see _DOC_POSITION)."""
    if _DOC_POSITION.get(cfg.language.lower(), "above") == "below":
        return _doc_below_py(lines, idx) or _doc_above(lines, idx)
    return _doc_above(lines, idx)


def _doc_above(lines: list[str], idx: int) -> str:
    """Capture a doc/comment block (/** */, ///, #) immediately above line idx."""
    out, j = [], idx - 1
    while j >= 0 and not lines[j].strip():
        j -= 1
    if j >= 0 and lines[j].strip().endswith("*/"):
        while j >= 0:
            out.append(lines[j].strip());
            if lines[j].strip().startswith("/*"):
                break
            j -= 1
        out.reverse()
        txt = " ".join(l.strip("/*").strip() for l in out if l.strip("/* ").strip())
        return txt.strip()
    block = []
    while j >= 0 and re.match(r"^\s*(///|//!|#)\s?", lines[j]):
        block.append(re.sub(r"^\s*(///|//!|#)\s?", "", lines[j]).strip()); j -= 1
    block.reverse()
    return " ".join(block).strip()


def _python_module_name(path: Path) -> str:
    """Return the importable module path for a Python source file.

    Walk upward while ``__init__.py`` files make parents part of the package.
    This is source-layout agnostic: ``src/pkg/a.py`` and ``package/pkg/a.py``
    both become ``pkg.a`` without project-specific configuration.
    """
    stem = path.stem
    parts = [] if stem == "__init__" else [stem]
    parent = path.parent
    while (parent / "__init__.py").is_file():
        parts.append(parent.name)
        parent = parent.parent
    return ".".join(reversed(parts)) or stem


def _python_qualified_identities(cfg: AidealConfig) -> dict[tuple[str, int, str], dict]:
    """AST-derived identity for each importable Python API definition.

    Keys match the existing regex scanner by ``(relative file, line, bare
    name)``. Nested local functions are deliberately absent: they are not
    addressable public APIs. Nested classes remain addressable through their
    owner chain. No domain/package names are hard-coded.
    """
    out: dict[tuple[str, int, str], dict] = {}
    seen: set[Path] = set()
    for pattern in cfg.source_globs:
        for raw in globmod.glob(str(cfg.root / pattern), recursive=True):
            path = Path(raw)
            if path in seen or path.suffix != ".py" or not path.is_file():
                continue
            seen.add(path)
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"),
                                 filename=str(path))
            except (OSError, SyntaxError):
                continue
            rel = str(path.relative_to(cfg.root)).replace("\\", "/")
            module = _python_module_name(path)

            def function_signature(node) -> tuple[str, list[dict], str]:
                args_text = ast.unparse(node.args)
                parts = [p for p in _split_top_level(args_text)
                         if p.strip() not in ("/", "*")]
                params = [_param_record(p) for p in parts]
                returns = ast.unparse(node.returns) if node.returns is not None else ""
                prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
                suffix = f" -> {returns}" if returns else ""
                return f"{prefix} {node.name}({args_text}){suffix}", params, returns

            def class_signature(node: ast.ClassDef) -> str:
                bases = [ast.unparse(base) for base in node.bases]
                bases.extend(
                    f"{kw.arg}={ast.unparse(kw.value)}" if kw.arg else f"**{ast.unparse(kw.value)}"
                    for kw in node.keywords
                )
                return f"class {node.name}" + (f"({', '.join(bases)})" if bases else "")

            def visit(body, classes: tuple[str, ...] = (), inside_function: bool = False):
                for node in body:
                    if isinstance(node, ast.ClassDef) and not inside_function:
                        owners = classes + (node.name,)
                        qn = ".".join(filter(None, (module, *owners)))
                        out[(rel, node.lineno, node.name)] = {
                            "qualified_name": qn, "module": module,
                            "owner": ".".join(classes), "kind": "class",
                            "signature": class_signature(node),
                            "params": [], "returns": "",
                        }
                        visit(node.body, owners, False)
                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if not inside_function:
                            qn = ".".join(filter(None, (module, *classes, node.name)))
                            signature, params, returns = function_signature(node)
                            out[(rel, node.lineno, node.name)] = {
                                "qualified_name": qn, "module": module,
                                "owner": ".".join(classes),
                                "kind": "method" if classes else "function",
                                "signature": signature,
                                "params": params, "returns": returns,
                            }
                        # Do not expose definitions local to a function/method.
                    elif not inside_function:
                        # Definitions can appear under module/class conditionals.
                        nested = []
                        for attr in ("body", "orelse"):
                            value = getattr(node, attr, None)
                            if isinstance(value, list):
                                nested.extend(value)
                        if nested:
                            visit(nested, classes, False)

            visit(tree.body)
    return out
