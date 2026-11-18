"""Read source-bound SQL registrations or compiler-declared public method facts.

These are distinct frozen inventory kinds. SQL names are never host-language
definitions, and compiler inventories retain public owner/overload provenance.
"""
import hashlib
import json
from pathlib import Path
import re
from .api_canonical_selection import qualified_api_id



IDENTITY_VERSION = "language_qualified_api_v1"


def target_key(row):
    """Use the stable defining API identity when present, else the legacy name."""
    return row.get("api_id") or row["name"]


def with_api_identity(cfg, rows):
    """Opt in to qualified keys without changing historical registry outputs."""
    mode = (cfg.raw.get("codebase", {}) or {}).get("identity_mode", "legacy")
    if mode not in ("legacy", "qualified"):
        raise ValueError("codebase.identity_mode must be legacy or qualified")
    if mode == "legacy":
        return rows
    result = []
    for row in rows:
        language = str(row.get("language") or cfg.language).lower()
        qualified = row.get("qualified_name")
        if row.get("definition_kind") == "registered_sql":
            language, qualified = "sql", row["name"]
        if not isinstance(qualified, str) or not qualified or (qualified == row["name"] and language != "sql"):
            raise ValueError("Qualified discovery needs defining owner/module evidence: " + row["name"])
        identity = qualified_api_id({**row, "qualified_name": qualified}, language)
        if row.get("api_id") not in (None, identity):
            raise ValueError("API identity differs from its defining language/name")
        result.append({**row, "api_id": identity, "identity_version": IDENTITY_VERSION})
    return result


def configured_api_details(cfg, override_filter=None):
    codebase = cfg.raw.get("codebase", {})
    locator = codebase.get("api_inventory")
    if not locator:
        return None
    if override_filter not in (None, "all"):
        raise ValueError("A frozen API inventory cannot use an override surface filter")
    path = cfg.root / locator
    content = path.read_bytes()
    expected_hash = codebase.get("api_inventory_sha256")
    if not expected_hash or hashlib.sha256(content).hexdigest() != expected_hash:
        raise ValueError("Configured API inventory checksum is missing or changed")
    data = json.loads(content)
    if data.get("kind") == "compiler_declared_methods":
        return with_api_identity(cfg, _compiler_details(cfg, data))
    if data.get("kind") == "source_audited_callables":
        from .api_source_registry import source_audited_details
        return with_api_identity(cfg, source_audited_details(cfg, data))
    if data.get("kind") == "qualified_source_api_inventory":
        if codebase.get("identity_mode") != "qualified":
            raise ValueError("Qualified API inventory requires identity_mode=qualified")
        from .api_public_inventory import qualified_inventory_details
        return with_api_identity(cfg, qualified_inventory_details(cfg, data))
    return with_api_identity(cfg, _sql_details(cfg, data))


def registered_sql_details(cfg):
    """Compatibility entry point for the existing registered-SQL adapter."""
    return configured_api_details(cfg)


def relocated_inventory_binding(cfg):
    """Bind relative provenance locators to their original root for a new run.

    Return replacement manifest bytes and checksum only when relocation is needed.
    Evidence bytes, source-root paths and declaration source paths stay unchanged.
    """
    codebase = cfg.raw.get("codebase", {})
    locator = codebase.get("api_inventory")
    if not locator:
        return None
    content = (cfg.root / locator).read_bytes()
    data = json.loads(content)
    relative = [field for field in ("source_inventory", "canonical_selection", "parser_contract")
                if data.get(field) and not Path(data[field]).is_absolute()]
    if not relative:
        return None
    if hashlib.sha256(content).hexdigest() != codebase.get("api_inventory_sha256"):
        raise ValueError("Configured API inventory checksum is missing or changed")
    for field in relative:
        _bound_json(cfg, data, field)
        data[field] = str((cfg.root / data[field]).resolve())
    content = (json.dumps(data, sort_keys=True, indent=2) + "\n").encode()
    return content, hashlib.sha256(content).hexdigest()


def inventory_runtime_bindings(cfg):
    """List bound conditional-definition evidence that must follow a moved config."""
    codebase = cfg.raw.get('codebase', {})
    locator = codebase.get('api_inventory')
    if not locator:
        return []
    raw = (cfg.root / locator).read_bytes()
    if hashlib.sha256(raw).hexdigest() != codebase.get('api_inventory_sha256'):
        raise ValueError('Configured API inventory checksum changed')
    data = json.loads(raw)
    if data.get('kind') != 'qualified_source_api_inventory':
        return []
    ledger = _bound_json(cfg, data, 'source_inventory')
    result = {}
    for fact in ledger.get('binding_environment', {}).get('facts', {}).values():
        relative = Path(fact['evidence_path'])
        if not relative.is_absolute() and '..' in relative.parts:
            raise ValueError('Runtime evidence cannot escape the prepared directory')
        source = (cfg.root / relative).resolve()
        if hashlib.sha256(source.read_bytes()).hexdigest() != fact['evidence_sha256']:
            raise ValueError('Conditional runtime evidence changed')
        result[str(relative)] = source
    return [(Path(name), source) for name, source in sorted(result.items())]


def _sql_details(cfg, data):
    if data.get("kind") != "registered_sql" or data.get("schema") != 1:
        raise ValueError("Unsupported registered API inventory schema")
    records = data.get("definitions", [])
    registry = data.get("registered_names", [])
    if not records or not registry or cfg.surface_filter != "all":
        raise ValueError("Registered SQL requires a nonempty frozen inventory and surface_filter=all")
    names = [row["name"].lower() for row in records]
    if len(names) != len(set(names)) or set(names) != set(registry):
        raise ValueError("SQL inventory must represent each registered name exactly once")
    details = []
    for row in records:
        source = cfg.root / row["file"]
        if hashlib.sha256(source.read_bytes()).hexdigest() != row["file_sha256"]:
            raise ValueError(f"SQL API source evidence changed: {source}")
        if row["name"] in cfg.exclude_names:
            raise ValueError("Exclusions cannot silently change a frozen SQL registry")
        record = dict(row)
        record.update(visibility="public", qualified_name=row["name"],
                      module="SQL", owner="", definition_kind="registered_sql")
        details.append(record)
    from .api_sql_canonical import canonical_sql_details
    return canonical_sql_details(cfg, data, details)


def _bound_json(cfg, data, field):
    path = cfg.root / data[field]
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != data.get(field + "_sha256"):
        raise ValueError("Compiler provenance checksum changed: " + field)
    return json.loads(content)


def _group(text, start, opening, closing):
    depth = 0
    for end in range(start, len(text)):
        if text[end] == opening:
            depth += 1
        elif text[end] == closing:
            depth -= 1
            if depth == 0:
                return text[start + 1:end], end + 1
    raise ValueError("Unbalanced compiler method signature")


def _parameters(signature, language):
    from .api_signatures import _param_record, _java_param_record
    if not isinstance(signature, str) or not signature.strip():
        raise ValueError("Missing compiler method signature")
    rest, params = signature.strip(), []
    if language == "Scala":
        if not rest.startswith("["):
            raise ValueError("Unknown Scala compiler signature format")
        _, end = _group(rest, 0, "[", "]")
        rest = rest[end:]
    elif not rest.startswith("("):
        # javac serializes generic declarations as T(...):T (or
        # T extends TreeNode(...):T), without angle brackets around type params.
        prefix, separator, tail = rest.partition("(")
        if not separator or not re.fullmatch(r"[A-Za-z_$][\w$]*[^():]*", prefix):
            raise ValueError("Unknown Java compiler signature format")
        rest = "(" + tail
    while rest.startswith("("):
        inner, end = _group(rest, 0, "(", ")")
        parser = _java_param_record if language == "Java" else _param_record
        values, depth, start = [], 0, 0
        for index, char in enumerate(inner):
            if char in ("([{<" if language == "Java" else "([{"): depth += 1
            elif char in (")]}>" if language == "Java" else ")]}" ): depth -= 1
            if char == "," and depth == 0:
                values.append(inner[start:index].strip()); start = index + 1
        if inner[start:].strip(): values.append(inner[start:].strip())
        params.extend(parser(value) for value in values)
        rest = rest[end:]
    if not rest.startswith(":") or not rest[1:].strip():
        raise ValueError("Unknown compiler return signature")
    if any(not p["name"] or not p["type"] for p in params):
        raise ValueError("Incomplete compiler parameter signature")
    returns = rest[1:].strip()
    # Syntax parsers cannot infer unannotated Scala return types. Preserve this
    # uncertainty instead of fabricating a model-facing return type.
    return params, "" if returns == "<type ?>" else returns


def _source_header(segment, name, language):
    pattern = (r"\bdef\s+`?" + re.escape(name) + r"`?(?=\s|[(:\[])" if language == "Scala"
               else r"(?<![\w$@.])" + re.escape(name) + r"\s*(?=\()")
    match = re.search(pattern, segment)
    if not match:
        raise ValueError("Compiler method name is absent from its source declaration")
    depth = 0
    for index in range(match.end(), len(segment)):
        char = segment[index]
        if char in "([": depth += 1
        elif char in ")]": depth -= 1
        if depth == 0 and (char in "{;" or (language == "Scala" and char == "=" and
                                           segment[index:index + 2] != "=>")):
            return " ".join(segment[:index].split()), match.start()
    # Abstract members may end exactly after the declared signature.
    return " ".join(segment.split()), match.start()


def _canonical_selection_ids(cfg, data, inventory):
    """Validate the optional, globally audited replacement selection policy.

    The complete declaration inventory is still mandatory. The new receipt is
    bound to that same inventory and is replayed before any names are removed.
    """
    fields = ("canonical_selection", "canonical_selection_sha256",
              "canonical_selection_policy_version", "canonical_declaration_ids")
    if not any(field in data for field in fields):
        return None
    if not all(field in data for field in fields):
        raise ValueError("Canonical selection requires its receipt, checksum, policy version, and declaration IDs")
    from .api_canonical_selection import POLICY_VERSION, select_canonical_implementations
    if data["canonical_selection_policy_version"] != POLICY_VERSION:
        raise ValueError("Unsupported canonical selection policy version")
    bound = _bound_json(cfg, data, "canonical_selection")
    if (bound.get("schema") != 1 or bound.get("kind") != "compiler_global_canonical_selection"
            or bound.get("policy_version") != POLICY_VERSION
            or bound.get("source_inventory_sha256") != data.get("source_inventory_sha256")):
        raise ValueError("Canonical selection does not bind the required source inventory and policy")
    receipt = bound.get("selection")
    if not isinstance(receipt, dict) or not isinstance(receipt.get("site_decisions"), list):
        raise ValueError("Missing canonical selection decisions")
    if select_canonical_implementations(receipt["site_decisions"]) != receipt:
        raise ValueError("Canonical selection receipt does not replay exactly")
    public = {row["site_id"]: row for row in inventory.get("records", [])
              if row.get("language") in ("Scala", "Java") and row.get("kind") == "method"
              and row.get("scope") == "production" and row.get("declared_visibility") == "public"
              and row.get("public_owner_chain") is True and row.get("synthetic") is False}
    decisions = {row["site_id"]: row for row in receipt["site_decisions"]}
    if set(decisions) != set(public):
        raise ValueError("Canonical selection must audit every global public-production method exactly once")
    for site_id, source in public.items():
        decision = decisions[site_id]
        if any(decision.get(field) != source.get(field)
               for field in ("language", "name", "owner", "path", "line")):
            raise ValueError("Canonical selection declaration evidence differs: " + site_id)
        params, _ = _parameters(source["signature"], source["language"])
        if decision["parameter_count"] != len(params):
            raise ValueError("Canonical selection parameter count differs: " + site_id)
    language = data["language"]
    language_result = receipt.get("by_language", {}).get(language)
    if not isinstance(language_result, dict):
        raise ValueError("Canonical selection has no result for the configured language")
    expected = language_result["winner_site_ids"]
    selected = data["canonical_declaration_ids"]
    if (not isinstance(selected, list) or any(not isinstance(value, str) for value in selected)
            or len(selected) != len(set(selected)) or set(selected) != set(expected)):
        raise ValueError("Canonical declaration IDs must exactly match the global receipt's language winners")
    if any(site_id not in public or public[site_id]["language"] != language for site_id in selected):
        raise ValueError("Canonical winner is not a public-production definition in this language")
    # Use the receipt's deterministic name order, independent of manifest order.
    return expected


def _compiler_details(cfg, data):
    language = data.get("language")
    if data.get("schema") != 1 or language not in ("Scala", "Java") or cfg.language != language:
        raise ValueError("Unsupported compiler API inventory schema/language")
    if cfg.surface_filter != "all" or cfg.exclude_names:
        raise ValueError("Frozen compiler inventory requires surface_filter=all and no name exclusions")
    inventory = _bound_json(cfg, data, "source_inventory")
    contract = _bound_json(cfg, data, "parser_contract")
    if inventory.get("schema_version") != 1 or contract.get("status") != "passed":
        raise ValueError("Compiler inventory requires passed parser provenance")
    records = inventory.get("records", [])
    by_id = {row["site_id"]: row for row in records}
    if len(by_id) != len(records):
        raise ValueError("Duplicate compiler declaration identity")
    public = {row["site_id"] for row in records if row.get("language") == language and
              row.get("kind") == "method" and row.get("scope") == "production" and
              row.get("declared_visibility") == "public" and row.get("public_owner_chain") is True and
              row.get("synthetic") is False}
    selected = data.get("declaration_ids", [])
    if not public or len(selected) != len(set(selected)) or set(selected) != public:
        raise ValueError("Compiler inventory must contain exactly the public-owner production method declarations")
    canonical_ids = _canonical_selection_ids(cfg, data, inventory)
    source_root = Path(data["source_root"])
    if source_root.is_absolute() or ".." in source_root.parts:
        raise ValueError("Compiler source root must be relative to the configured root")
    from .api_signatures import _doc_above
    cache, details = {}, []
    for site_id in selected:
        row = by_id[site_id]
        relative = Path(row["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Invalid compiler source path")
        path = cfg.root / source_root / relative
        if path not in cache:
            content = path.read_bytes()
            cache[path] = (hashlib.sha256(content).hexdigest(), content.decode("utf-8"))
        sha, text = cache[path]
        if sha != row.get("source_sha256"):
            raise ValueError("Compiler API source evidence changed: " + str(path))
        start, end = row["start"], row["end"]
        encoded = text.encode("utf-16-le")
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(encoded) // 2:
            raise ValueError("Invalid compiler source span")
        before = encoded[:start * 2].decode("utf-16-le")
        segment = encoded[start * 2:end * 2].decode("utf-16-le")
        signature, offset = _source_header(segment, row["name"], language)
        start_line = before.count("\n") + 1
        name_line = start_line + segment[:offset].count("\n")
        if not start_line <= row["line"] <= name_line or not row.get("owner") or row.get("qualified_name") != row["owner"] + "." + row["name"]:
            raise ValueError("Compiler owner/name/line evidence does not match source")
        params, returns = _parameters(row["signature"], language)
        details.append({"name": row["name"], "qualified_name": row["qualified_name"],
                        "owner": row["owner"], "owner_kind": row.get("owner_kind", ""),
                        "module": language + ":" + row.get("owner_kind", ""),
                        "definition_kind": "compiler_declared_method", "visibility": "public",
                        "signature": signature, "compiler_signature": row["signature"],
                        "params": params, "returns": returns,
                        "description": _doc_above(text.splitlines(), start_line - 1),
                        "file": str(source_root / relative), "line": name_line,
                        "file_sha256": sha, "site_id": site_id})
    if canonical_ids is None:
        return details
    by_site_id = {row["site_id"]: row for row in details}
    return [by_site_id[site_id] for site_id in canonical_ids]
