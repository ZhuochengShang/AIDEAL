"""Frozen source-audit callable inventories, including class constructors.

This reader is opt-in and performs no imports of audited packages, source
execution, compilation, network access, or model calls. Body classifications
are external audit attestations, bound by the inventory's checksum.
"""
from __future__ import annotations

import ast
from copy import deepcopy
import glob
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tokenize

from .api_canonical_selection import POLICY_VERSION, select_canonical_implementations


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _relative(value):
    if not isinstance(value, str) or not value:
        raise ValueError("Source audit requires a relative source path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Source audit paths must stay inside their configured root")
    return path


def _git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                            text=True, timeout=30, check=False)
    if result.returncode:
        raise ValueError("Cannot validate pinned source Git identity")
    return result.stdout.strip()


def _python_params(node, classes, *, constructor=False):
    text = lambda value: ast.unparse(value) if value is not None else ""
    positional = [*node.args.posonlyargs, *node.args.args]
    defaults = [None] * (len(positional) - len(node.args.defaults)) + list(node.args.defaults)
    declared = []
    def add(arg, kind, default=None):
        declared.append({"name": arg.arg, "kind": kind, "annotation": text(arg.annotation),
                         "default": text(default) if default is not None else None,
                         "required": default is None and kind not in ("var_positional", "var_keyword")})
    for index, (arg, default) in enumerate(zip(positional, defaults)):
        add(arg, "positional_only" if index < len(node.args.posonlyargs) else "positional_or_keyword", default)
    if node.args.vararg:
        add(node.args.vararg, "var_positional")
    for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
        add(arg, "keyword_only", default)
    if node.args.kwarg:
        add(node.args.kwarg, "var_keyword")
    params = list(declared)
    decorators = [text(value) for value in node.decorator_list]
    receiver = None
    if classes and positional and ("staticmethod" not in decorators or constructor and node.name == "__new__"):
        receiver = params.pop(0)
    return {"params": params, "declared_params": declared, "implicit_receiver": receiver,
            "parameter_count": len(params)}


def _python_declarations(path, source, excluded_names):
    """Re-read public identity and signatures with AST; do not reclassify bodies."""
    tree = ast.parse(source, filename=str(path), type_comments=True)
    parts = [] if path.stem == "__init__" else [path.stem]
    parent = path.parent
    while (parent / "__init__.py").is_file():
        parts.append(parent.name); parent = parent.parent
    module = ".".join(reversed(parts)) or path.stem
    lines = source.splitlines(keepends=True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line))
    def offset(line, column):
        return starts[line - 1] + len(lines[line - 1].encode("utf-8")[:column].decode("utf-8"))
    result = {}
    def visit(body, classes=(), public=True):
        for node in body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                is_class = isinstance(node, ast.ClassDef)
                if public and not node.name.startswith("_") and node.name not in excluded_names:
                    row = {"name": node.name, "owner": ".".join(classes), "module": module,
                           "qualified_name": ".".join((module, *classes, node.name)),
                           "line": node.lineno, "end_line": node.end_lineno,
                           "kind": "class_constructor" if is_class else "method" if classes else "function"}
                    if is_class:
                        bases = [ast.unparse(value) for value in [*node.bases, *node.keywords]]
                        row["signature"] = "class " + node.name + ("(" + ", ".join(bases) + ")" if bases else "")
                        ctors = [value for value in node.body if isinstance(value, (ast.FunctionDef, ast.AsyncFunctionDef))
                                 and value.name in ("__init__", "__new__")]
                        row["declared_constructors"] = [
                            {"name": value.name, "line": value.lineno, "end_line": value.end_lineno,
                             "signature": "def " + value.name + "(" + ast.unparse(value.args) + ")",
                             **_python_params(value, classes + (node.name,), constructor=True)} for value in ctors]
                        inits = [value for value in row["declared_constructors"] if value["name"] == "__init__"]
                        news = [value for value in row["declared_constructors"] if value["name"] == "__new__"]
                        chosen = inits[0] if len(inits) == 1 else news[0] if len(news) == 1 else None
                        row.update({key: chosen[key] for key in ("params", "declared_params", "implicit_receiver", "parameter_count")}
                                   if chosen else {"params": [], "declared_params": [], "implicit_receiver": None, "parameter_count": 0})
                        row["parameter_count_status"] = "declared_constructor_only" if chosen else "unknown_inherited_or_generated"
                        row["returns"] = row["qualified_name"]
                        row["constructor_signature"] = chosen["signature"] if chosen else ""
                    else:
                        row["returns"] = ast.unparse(node.returns) if node.returns is not None else ""
                        row["signature"] = ("async def " if isinstance(node, ast.AsyncFunctionDef) else "def ") + node.name + "(" + ast.unparse(node.args) + ")" + (" -> " + row["returns"] if row["returns"] else "")
                        row.update(_python_params(node, classes))
                    row["description"] = ast.get_docstring(node) or ""
                    key = (offset(node.lineno, node.col_offset), offset(node.end_lineno, node.end_col_offset))
                    result[key] = row
                if is_class:
                    visit(node.body, classes + (node.name,), public and not node.name.startswith("_"))
                # Function-local declarations never become public target names.
            else:
                for field in ("body", "orelse", "finalbody"):
                    values = getattr(node, field, None)
                    if isinstance(values, list):
                        visit(values, classes, public)
                for arm in [*getattr(node, "handlers", []), *getattr(node, "cases", [])]:
                    visit(arm.body, classes, public)
    visit(tree.body)
    return result


def source_audited_details(cfg, data):
    from .api_registry import _bound_json, _group, _parameters, _source_header
    language = data.get("language")
    if data.get("schema") != 1 or language not in ("Python", "Java") or cfg.language != language:
        raise ValueError("Unsupported source-audited inventory schema/language")
    if cfg.surface_filter != "all":
        raise ValueError("Frozen source-audited inventory requires surface_filter=all")
    ledger = _bound_json(cfg, data, "source_inventory")
    receipt = ledger.get("receipt", {})
    policy = ledger.get("discovery_policy", {})
    if ledger.get("schema") != 1 or ledger.get("language") != language or receipt.get("passed") is not True:
        raise ValueError("Source-audited inventory requires a passed matching-language audit")
    source_relative = _relative(data["source_root"])
    root = (cfg.root / source_relative).resolve()
    snapshot = ledger.get("source_snapshot", {})
    if (not snapshot.get("commit") or not snapshot.get("tree") or snapshot.get("tracked_worktree_clean") is not True
            or snapshot.get("commit") != data.get("source_commit") or snapshot.get("tree") != data.get("source_tree")
            or _git(root, "rev-parse", "HEAD") != snapshot["commit"]
            or _git(root, "rev-parse", "HEAD^{tree}") != snapshot["tree"]
            or _git(root, "status", "--porcelain", "--untracked-files=no")):
        raise ValueError("Source root commit/tree differs from the frozen clean audit")
    patterns = policy.get("source_globs", [])
    if (not patterns or policy.get("surface_filter", "all") != "all"
            or sorted(cfg.exclude_names) != sorted(policy.get("exclude_names", []))
            or sorted(cfg.source_globs) != sorted(str(source_relative / _relative(pattern)) for pattern in patterns)):
        raise ValueError("Configured discovery scope differs from the frozen source audit")
    bindings = ledger.get("source_files", [])
    if not bindings or _digest(bindings) != receipt.get("source_file_binding_sha256"):
        raise ValueError("Source-file binding digest is missing or changed")
    if data.get("source_file_binding_sha256") != receipt["source_file_binding_sha256"]:
        raise ValueError("Manifest source-file digest differs from the source audit")
    by_path = {row["path"]: row for row in bindings}
    if len(by_path) != len(bindings):
        raise ValueError("Duplicate audited source path")
    excluded = [re.compile(pattern) for pattern in policy.get("exclude_paths", [])]
    found = {Path(value).relative_to(root).as_posix() for pattern in patterns
             for value in glob.glob(str(root / pattern), recursive=True)
             if Path(value).is_file() and not any(regex.search(Path(value).relative_to(root).as_posix()) for regex in excluded)}
    if found != set(by_path):
        raise ValueError("Current source-file scope differs from the audited file set")
    sources, python_nodes = {}, {}
    for relative, binding in by_path.items():
        path = root / _relative(relative)
        if not path.resolve().is_relative_to(root):
            raise ValueError("Audited source path escapes its frozen root")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != binding.get("sha256") or len(raw) != binding.get("bytes"):
            raise ValueError("Source audit file evidence changed: " + relative)
        encoding = tokenize.detect_encoding(io.BytesIO(raw).readline)[0] if language == "Python" else "utf-8"
        if language == "Python" and binding.get("encoding") != encoding:
            raise ValueError("Audited source encoding differs")
        sources[relative] = raw.decode(encoding)
        if language == "Python":
            python_nodes[relative] = _python_declarations(path, sources[relative], set(cfg.exclude_names))
    rows = ledger.get("records", [])
    if "public_callable_sites" in receipt and receipt["public_callable_sites"] != len(rows):
        raise ValueError("Audited callable count differs from the declaration ledger")
    by_id = {row["site_id"]: row for row in rows}
    if len(by_id) != len(rows):
        raise ValueError("Duplicate audited declaration identity")
    selected = data.get("declaration_ids", [])
    if len(selected) != len(set(selected)) or set(selected) != set(by_id):
        raise ValueError("Source inventory must retain every audited declaration ID")
    if language == "Python":
        actual = {(path, start, end) for path, nodes in python_nodes.items() for start, end in nodes}
        frozen = {(row["path"], row["start"], row["end"]) for row in rows}
        if actual != frozen or len(frozen) != len(rows):
            raise ValueError("Python source audit omits or duplicates a public declaration")
    details = {}
    for row in rows:
        classification = row.get("body_classification")
        if (isinstance(classification, dict) and classification.get("category") == "implementation"
                and (row.get("residual_unknown") is True or row.get("receiver_anomaly") is True
                     or row.get("parameter_count_status") == "unknown_inherited_or_generated")):
            raise ValueError("Unresolved source binding cannot be an eligible implementation")
        if (row.get("language") != language or row.get("scope") != "production"
                or row.get("declared_visibility") != "public" or row.get("public_owner_chain") is not True
                or row.get("synthetic") is not False or row.get("kind") not in ("function", "method", "class_constructor")
                or row["path"] not in sources or row.get("source_sha256") != by_path[row["path"]]["sha256"]):
            raise ValueError("Invalid public source declaration evidence")
        text = sources[row["path"]]
        start, end = row.get("start"), row.get("end")
        expected_unit = "Unicode code points in decoded source" if language == "Python" else "UTF-16 code units in decoded UTF-8 source"
        units = text if language == "Python" else text.encode("utf-16-le")
        length = len(units) if language == "Python" else len(units) // 2
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= length or row.get("offset_unit") != expected_unit:
            raise ValueError("Invalid source-audit declaration span")
        segment = text[start:end] if language == "Python" else units[2 * start:2 * end].decode("utf-16-le")
        if hashlib.sha256(segment.encode("utf-8")).hexdigest() != row.get("source_span_sha256"):
            raise ValueError("Source-audit declaration span checksum differs")
        if language == "Python":
            observed = python_nodes[row["path"]][(start, end)]
            for field in ("name", "owner", "module", "qualified_name", "kind", "line", "end_line", "signature", "returns",
                          "params", "declared_params", "implicit_receiver", "parameter_count"):
                if row.get(field) != observed[field]:
                    raise ValueError("Python audited declaration metadata differs: " + field)
            if row["kind"] == "class_constructor" and any(row.get(field) != observed[field] for field in ("declared_constructors", "parameter_count_status")):
                raise ValueError("Python audited constructor evidence differs")
            signature = observed["signature"]
            if row["kind"] == "class_constructor" and observed["constructor_signature"]:
                signature += "; " + observed["constructor_signature"]
            params = [{**param, "type": param["annotation"]} for param in observed["params"]]
            description = observed["description"]
            returns = observed["returns"]
        else:
            signature, offset = _source_header(segment, row["name"], language)
            before = units[:2 * start].decode("utf-16-le")
            if row["line"] != before.count("\n") + 1 or row.get("qualified_name") != (row["owner"] if row["kind"] == "class_constructor" else row["owner"] + "." + row["name"]):
                raise ValueError("Java source-audit owner/name/line mismatch")
            if row["kind"] == "class_constructor" and row["owner"].split(".")[-1] != row["name"]:
                raise ValueError("Java constructor name differs from its owner")
            params, returns = _parameters(row["signature"], "Java")
            if len(params) != row["parameter_count"]:
                raise ValueError("Java audited arity differs from its compiler signature")
            opening = segment.index("(", offset)
            source_parameters, _ = _group(segment, opening, "(", ")")
            source_params, _ = _parameters("(" + source_parameters + "):void", "Java")
            compact = lambda values: [(value["name"], re.sub(r"\s+", "", value["type"]).replace("...", "[]")) for value in values]
            if compact(source_params) != compact(params):
                raise ValueError("Java audited parameters differ from the source declaration")
            from .api_signatures import _doc_above
            description = _doc_above(text.splitlines(), row["line"] - 1)
            if row["kind"] == "class_constructor":
                returns = row["qualified_name"]
        details[row["site_id"]] = {
            "name": row["name"], "qualified_name": row["qualified_name"], "owner": row["owner"],
            "module": row.get("module", language), "owner_kind": row.get("owner_kind", ""),
            "definition_kind": "source_audited_" + row["kind"], "visibility": "public",
            "signature": signature, "params": params, "returns": returns, "description": description,
            "file": str(source_relative / row["path"]), "line": row["line"],
            "file_sha256": row["source_sha256"], "site_id": row["site_id"],
        }
    if data.get("canonical_selection_policy_version") != POLICY_VERSION:
        raise ValueError("Unsupported source-audit canonical policy")
    bound = _bound_json(cfg, data, "canonical_selection")
    if (bound.get("schema") != 1 or bound.get("kind") != "source_audit_global_canonical_selection"
            or bound.get("policy_version") != POLICY_VERSION
            or bound.get("source_inventory_sha256") != data.get("source_inventory_sha256")):
        raise ValueError("Canonical source-audit receipt binding differs")
    expected = select_canonical_implementations(rows)
    if bound.get("selection") != expected:
        raise ValueError("Canonical selection does not replay from the frozen source audit")
    winner_ids = expected["by_language"].get(language, {}).get("winner_site_ids", [])
    winners = data.get("canonical_declaration_ids", [])
    if len(winners) != len(set(winners)) or set(winners) != set(winner_ids):
        raise ValueError("Canonical IDs differ from the frozen source-audit winners")
    return [details[site_id] for site_id in winner_ids]
