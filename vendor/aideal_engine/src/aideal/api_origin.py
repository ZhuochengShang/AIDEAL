"""Opt-in definition ownership; never infer ownership from a called API name."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

POLICY_VERSION = "source_file_and_declaring_namespace_v1"


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def origin_enabled(cfg):
    return "api_origin" in (cfg.raw.get("codebase", {}) or {})


def _namespace_match(value, prefix):
    return value == prefix or value.startswith(prefix + ".") or value.startswith(prefix + "::")


def _within(path, root):
    return path == root or root in path.parents


def _policy(cfg):
    raw = (cfg.raw.get("codebase", {}) or {}).get("api_origin")
    if not isinstance(raw, dict):
        raise ValueError("codebase.api_origin must be an explicit ownership policy")
    policy = {"version": POLICY_VERSION}
    for key in ("source_roots", "library_namespaces", "external_namespaces"):
        value = raw.get(key)
        if (not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value)
                or (key != "external_namespaces" and not value)):
            raise ValueError("api_origin requires string lists: " + key)
        policy[key] = sorted(set(value))
    roots = []
    for value in policy["source_roots"]:
        root = (Path(cfg.root) / value).resolve(strict=True)
        if not root.is_dir():
            raise ValueError("api_origin source root is not a directory: " + str(root))
        roots.append(root)
    policy["resolved_source_roots"] = sorted(map(str, roots))
    return policy, roots


def audit_api_origins(cfg, rows):
    """Return included rows and an explicit audit of every supplied definition.

    Existing readers supply verified declaration ``file``/``qualified_name``
    facts. Exposure-oriented readers may instead supply ``defining_file`` and
    ``defining_owner``/``declaring_owner``. Inherited/import-only exposures need
    those explicit defining facts; an importing file is not a definition.
    """
    if not origin_enabled(cfg):
        return {"enabled": False, "included": rows, "decisions": [], "counts": {}}
    policy, roots = _policy(cfg)
    policy_hash = _hash(policy)
    files = {}
    included, decisions = [], []
    for row in rows:
        owner_claims = {key: row[key] for key in ("defining_owner", "declaring_owner", "defining_module") if row.get(key)}
        normalized_owners = []
        for key in ("defining_owner", "declaring_owner"):
            owner = owner_claims.get(key)
            if not owner:
                continue
            module = owner_claims.get("defining_module")
            same_file = False
            try:
                same_file = (not row.get("defining_file") or
                             (Path(cfg.root) / row["defining_file"]).resolve() ==
                             (Path(cfg.root) / row.get("file", "")).resolve())
            except (OSError, RuntimeError, ValueError):
                pass  # The defining-path check below records unresolved evidence.
            if not module and same_file and row.get("module") and row.get("qualified_name"):
                candidate = row["module"] + "." + owner
                if _namespace_match(row["qualified_name"], candidate):
                    module = row["module"]
            if module:
                candidate = module + "." + owner
                if (("." not in owner and "::" not in owner) or
                        (same_file and _namespace_match(row.get("qualified_name", ""), candidate))):
                    owner = candidate
            normalized_owners.append(owner)
        explicit_owner = next(iter(normalized_owners), owner_claims.get("defining_module"))
        namespace = explicit_owner or row.get("qualified_name") or row.get("module") or ""
        if namespace == row.get("name"):
            namespace = row.get("module") or row.get("owner") or ""
        file_value = row.get("defining_file") or row.get("file")
        decision = {"name": row.get("name"), "qualified_name": row.get("qualified_name"),
                    "site_id": row.get("site_id"), "file": row.get("file"), "line": row.get("line"),
                    "signature": row.get("signature"), "definition_kind": row.get("definition_kind"),
                    "defining_owner_claims": owner_claims,
                    "defining_namespace": namespace, "defining_file": file_value,
                    "policy_sha256": policy_hash, "status": "unresolved", "reason": "missing_defining_evidence"}
        own = [p for p in policy["library_namespaces"] if _namespace_match(namespace, p)]
        external = [p for p in policy["external_namespaces"] if _namespace_match(namespace, p)]
        decision.update(library_namespace_matches=own, external_namespace_matches=external)
        exposure_only = bool(row.get("inherited") or row.get("import_only") or row.get("is_inherited"))
        module_claim = owner_claims.get("defining_module")
        owner_conflict = (len(set(normalized_owners)) > 1 or
                          (module_claim and normalized_owners and
                           not all(_namespace_match(value, module_claim) for value in normalized_owners)))
        if owner_conflict:
            decision["reason"] = "conflicting_defining_owner_evidence"
        elif own and external:
            decision["reason"] = "conflicting_namespace_rules"
        elif external:
            decision.update(status="external_defined", reason="external_declaring_namespace")
        elif row.get("definition_kind") == "registered_sql" and not (explicit_owner and row.get("defining_file")):
            decision["reason"] = "registered_sql_requires_defining_source_binding"
        elif exposure_only and not (explicit_owner and row.get("defining_file")):
            decision["reason"] = "exposure_without_defining_source"
        elif not own:
            decision["reason"] = "namespace_not_classified"
        elif file_value:
            lexical = Path(cfg.root) / file_value
            try:
                resolved = lexical.resolve(strict=True)
                decision["resolved_defining_file"] = str(resolved)
                if not any(_within(resolved, root) for root in roots):
                    decision["reason"] = "defining_file_outside_source_roots"
                    decision["symlink_escape"] = lexical.absolute() != resolved
                elif not resolved.is_file():
                    decision["reason"] = "defining_path_is_not_file"
                else:
                    if resolved not in files:
                        files[resolved] = hashlib.sha256(resolved.read_bytes()).hexdigest()
                    digest = files[resolved]
                    claims = {}
                    if row.get("defining_file_sha256"):
                        claims["defining_file_sha256"] = row["defining_file_sha256"]
                    if (not row.get("defining_file") or
                            (Path(cfg.root) / row.get("file", "")).resolve() == resolved):
                        claims.update({key: row[key] for key in ("file_sha256", "source_sha256") if row.get(key)})
                    expected = next(iter(claims.values()), None)
                    decision.update(file_sha256=digest, declared_file_sha256=expected, declared_hashes=claims)
                    if any(digest != claim for claim in claims.values()):
                        decision["reason"] = "defining_file_hash_mismatch"
                    else:
                        decision.update(status="library_defined", reason="owned_source_and_declaring_namespace")
            except (OSError, RuntimeError, ValueError) as error:
                decision.update(reason="unreadable_defining_source", error=str(error))
        decision["ownership_sha256"] = _hash(decision)
        decisions.append(decision)
        if decision["status"] == "library_defined":
            included.append({**row, "api_origin": decision})
    return {"enabled": True, "policy": policy, "policy_sha256": policy_hash,
            "included": included, "decisions": decisions,
            "counts": dict(Counter(row["status"] for row in decisions))}


def filter_api_origins(cfg, rows):
    return audit_api_origins(cfg, rows)["included"]
