"""Versioned, global API selection from externally audited compiler records.

This opt-in policy does not import or change the historical overload policy.
It never infers forwarding, facade status, or semantic equivalence from names,
signatures, documentation, or source text. Its caller supplies the body audit.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from copy import deepcopy
import json
import re
from typing import Any


POLICY_VERSION = "global_max_arity_non_wrapper_v1"
_EXCLUDED_CATEGORIES = frozenset({
    "wrapper", "direct_forwarder", "facade", "abstract", "no_body",
    "abstract_or_empty", "unresolved",
})


def _integer(value: Any, field: str, site_id: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{site_id}: {field} must be an integer >= {minimum}")
    return value


def _json_copy(value: Any, site_id: str, field: str) -> Any:
    try:
        # Reject non-JSON evidence, including NaN, rather than silently losing
        # provenance when the returned receipt is written to disk.
        json.dumps(value, allow_nan=False, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{site_id}: {field} must be JSON-serializable") from exc
    return deepcopy(value)


def _has_evidence(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, list):
        return bool(value)
    return False


def _normalize_record(record: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        raise ValueError("each record must be a mapping")
    site_id = record.get("site_id")
    if not isinstance(site_id, str) or not site_id.strip():
        raise ValueError("each record must have a nonempty string site_id")
    result: dict[str, Any] = {"site_id": site_id}
    for field in ("language", "name", "path"):
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{site_id}: {field} must be a nonempty string")
        result[field] = value
    # An empty owner is permitted for an audited module-level function.
    owner = record.get("owner")
    if not isinstance(owner, str):
        raise ValueError(f"{site_id}: owner must be a string")
    result["owner"] = owner
    result["line"] = _integer(record.get("line"), "line", site_id, 1)
    counts: list[int] = []
    if "parameter_count" in record:
        counts.append(_integer(record["parameter_count"], "parameter_count", site_id))
    if "params" in record:
        params = record["params"]
        if isinstance(params, (list, tuple)):
            counts.append(len(params))
        else:
            counts.append(_integer(params, "params", site_id))
    if not counts:
        raise ValueError(f"{site_id}: parameter_count or params is required")
    if len(set(counts)) != 1:
        raise ValueError(f"{site_id}: parameter_count and params disagree")
    result["parameter_count"] = counts[0]
    result["body_classification"] = _json_copy(
        record.get("body_classification"), site_id, "body_classification"
    )
    if "source_identity" in record:
        result["source_identity"] = _json_copy(
            record["source_identity"], site_id, "source_identity"
        )
    return result


def _audit_exclusion(record: Mapping[str, Any]) -> str | None:
    audit = record["body_classification"]
    if audit is None:
        return "missing_body_classification"
    if not isinstance(audit, Mapping):
        return "invalid_body_classification"
    if audit.get("reviewed") is not True:
        return "unreviewed_body_classification"
    if not _has_evidence(audit.get("evidence")):
        return "missing_body_classification_evidence"
    category = audit.get("category")
    if category == "implementation":
        return None
    if isinstance(category, str) and category in _EXCLUDED_CATEGORIES:
        return f"body_category_{category}"
    return "unknown_body_classification"


def _rank(record: Mapping[str, Any]) -> tuple[Any, ...]:
    return (-record["parameter_count"], record["language"], record["path"],
            record["line"], record["site_id"])


def _site_order(record: Mapping[str, Any]) -> tuple[Any, ...]:
    return (record["language"], record["path"], record["line"], record["site_id"])


def _trusted_identity_targets(
    records: list[dict[str, Any]], eligible: set[str],
) -> dict[str, str]:
    """Validate explicit identity attestations; never discover equivalence.

    Claims must be direct links to a canonical site, not chains or cycles.
    They attest exact source identity, not arbitrary behavioral equivalence.
    Equal arity is required so identity grouping cannot defeat maximum arity.
    """
    by_id = {row["site_id"]: row for row in records}
    targets: dict[str, str] = {}
    for row in records:
        if "source_identity" not in row:
            continue
        site_id = row["site_id"]
        claim = row["source_identity"]
        if not isinstance(claim, Mapping):
            raise ValueError(f"{site_id}: source_identity must be a mapping")
        if (claim.get("relation") != "exact_source_identical"
                or claim.get("trusted") is not True
                or not _has_evidence(claim.get("evidence"))):
            raise ValueError(f"{site_id}: source_identity needs a trusted exact-source attestation")
        target = claim.get("canonical_site_id")
        if not isinstance(target, str) or target not in by_id or target == site_id:
            raise ValueError(f"{site_id}: invalid canonical_site_id")
        if site_id not in eligible or target not in eligible:
            raise ValueError(f"{site_id}: exact-source identity requires two audited implementations")
        if row["parameter_count"] != by_id[target]["parameter_count"]:
            raise ValueError(f"{site_id}: exact-source identity requires equal parameter counts")
        targets[site_id] = target
    if any(target in targets for target in targets.values()):
        raise ValueError("source_identity targets must be direct canonical sites, without chains or cycles")
    return targets


def select_canonical_implementations(
    records: Iterable[Mapping[str, Any]], *, policy_version: str = POLICY_VERSION,
) -> dict[str, Any]:
    """Return a deterministic selection receipt for a reviewed public surface.

    The caller is responsible for compiler provenance, public-production scope,
    and supplying reviewed AST/body evidence. Every record needs site_id,
    language, name, owner, path, line, and parameter_count (or params, either a
    sequence or count). The helper performs no filesystem or model calls.

    A body_classification is eligible only when it is a mapping containing
    category="implementation", reviewed=True, and nonempty evidence. Missing,
    unresolved, unreviewed, wrapper, facade, and bodyless records are excluded.

    Among eligible records, the highest parameter count wins for each exact,
    case-sensitive name across ALL languages. Ties use language/path/line/
    site_id in ascending order. Documentation and owner do not affect rank.
    Same-name losers are policy omissions, not evidence of equivalence.

    Optional source_identity={relation:"exact_source_identical", trusted:true,
    canonical_site_id:..., evidence:...} can collapse equal-arity copies, but
    only when that direct canonical target wins its own name election. An
    unsatisfied canonical target rejects the entire call: silently redirecting
    to a different same-name implementation would invent identity evidence.
    A same-name claim must point to the winner dictated by the normal rank.
    The trust flag is a caller attestation; this helper does not verify source.

    Invalid identities, duplicate IDs, and malformed required fields raise
    ValueError. Unreviewed body records remain visible as excluded decisions.
    Inputs are not mutated. The receipt contains no timestamps or random IDs.
    """
    if policy_version == QUALIFIED_POLICY_VERSION:
        return _select_qualified(records)
    if policy_version != POLICY_VERSION:
        raise ValueError("Unsupported canonical selection policy version")
    normalized = [_normalize_record(row) for row in records]
    ids = [row["site_id"] for row in normalized]
    duplicates = sorted(site_id for site_id, count in Counter(ids).items() if count > 1)
    if duplicates:
        raise ValueError(f"duplicate site_id values: {duplicates}")
    normalized.sort(key=_site_order)
    reasons = {row["site_id"]: _audit_exclusion(row) for row in normalized}
    eligible = {site_id for site_id, reason in reasons.items() if reason is None}
    identity_targets = _trusted_identity_targets(normalized, eligible)
    by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in normalized:
        if row["site_id"] in eligible:
            by_name[row["name"]].append(row)
    elected = {name: min(group, key=_rank) for name, group in by_name.items()}
    elected_ids = {row["site_id"] for row in elected.values()}
    if any(target not in elected_ids for target in identity_targets.values()):
        raise ValueError("source_identity canonical target must win its global name election")

    decisions: list[dict[str, Any]] = []
    for row in normalized:
        site_id, name = row["site_id"], row["name"]
        decision = deepcopy(row)
        if reasons[site_id] is not None:
            decision.update(status="excluded", reason=reasons[site_id])
        elif site_id in identity_targets:
            decision.update(status="omitted", reason="trusted_exact_source_identity",
                            canonical_site_id=identity_targets[site_id],
                            relationship="externally_attested_exact_source_identity")
        elif elected[name]["site_id"] == site_id:
            decision.update(status="selected", reason="global_name_maximum_parameter_count")
        else:
            winner = elected[name]
            decision.update(status="omitted", reason=(
                "same_name_lower_parameter_count" if row["parameter_count"] < winner["parameter_count"]
                else "same_name_deterministic_tie_break"),
                name_election_site_id=winner["site_id"], relationship="name_policy_only")
        decisions.append(decision)

    winners = sorted((row for row in decisions if row["status"] == "selected"),
                     key=lambda row: (row["name"], *_site_order(row)))
    rejected = [row for row in decisions if row["status"] != "selected"]
    by_language: dict[str, dict[str, Any]] = {}
    for language in sorted({row["language"] for row in normalized}):
        local = [row for row in winners if row["language"] == language]
        by_language[language] = {
            "winner_count": len(local),
            "winner_site_ids": [row["site_id"] for row in local],
            "winner_names": [row["name"] for row in local],
        }
    receipt = {
        "schema_version": 1,
        "policy_version": POLICY_VERSION,
        "policy": {
            "scope": "one_global_winner_per_exact_case_sensitive_name",
            "body_evidence": "externally_reviewed_classification_required",
            "rank": ["parameter_count_desc", "language_asc", "path_asc", "line_asc", "site_id_asc"],
            "same_name_omission_claims_equivalence": False,
            "source_identity": "explicit_trusted_direct_target_only",
        },
        "counts": {
            "input_sites": len(normalized),
            "input_names": len({row["name"] for row in normalized}),
            "eligible_sites": len(eligible),
            "excluded_sites": sum(row["status"] == "excluded" for row in decisions),
            "omitted_sites": sum(row["status"] == "omitted" for row in decisions),
            "winner_sites": len(winners),
            "winner_names": len({row["name"] for row in winners}),
            "rejected_sites": len(rejected),
        },
        "winner_site_ids": [row["site_id"] for row in winners],
        "winner_names": [row["name"] for row in winners],
        "winners": deepcopy(winners),
        "rejected_sites": deepcopy(rejected),
        "site_decisions": decisions,
        "by_language": by_language,
        "names_without_winner": sorted({row["name"] for row in normalized}
                                       - {row["name"] for row in winners}),
    }
    _validate_receipt(receipt)
    return receipt


def _validate_receipt(receipt: Mapping[str, Any]) -> None:
    """Internal accounting checks that remain active under python -O."""
    decisions, counts = receipt["site_decisions"], receipt["counts"]
    winner_ids, winner_names = receipt["winner_site_ids"], receipt["winner_names"]
    rejected_ids = [row["site_id"] for row in receipt["rejected_sites"]]
    per_language_ids = [site_id for row in receipt["by_language"].values()
                        for site_id in row["winner_site_ids"]]
    checks = (
        len(decisions) == counts["input_sites"],
        counts["input_sites"] == counts["winner_sites"] + counts["rejected_sites"],
        counts["rejected_sites"] == counts["excluded_sites"] + counts["omitted_sites"],
        counts["eligible_sites"] == counts["winner_sites"] + counts["omitted_sites"],
        len(set(winner_ids)) == len(winner_ids) == counts["winner_sites"],
        len(set(winner_names)) == len(winner_names) == counts["winner_names"],
        set(winner_ids).isdisjoint(rejected_ids),
        set(winner_ids) | set(rejected_ids) == {row["site_id"] for row in decisions},
        sorted(per_language_ids) == sorted(winner_ids),
        all(row["winner_count"] == len(row["winner_site_ids"]) == len(row["winner_names"])
            for row in receipt["by_language"].values()),
    )
    if not all(checks):
        raise RuntimeError("canonical selection receipt invariant failed")


QUALIFIED_POLICY_VERSION = "owner_qualified_max_arity_v2"
QUALIFIED_IDENTITY_VERSION = "language_qualified_api_v1"
SELECTION_EXCLUSIONS_SCHEMA = "source_bound_selection_exclusions/v1"
_SELECTION_FIELDS = ("status", "reason", "relationship", "canonical_site_id",
                     "selection_note", "review_notes")


def reviewed_selection_exclusion_ids(review, records, source_inventory_sha256):
    """Validate an explicit source review before selecting the largest overload.

    The reader independently verifies the bound source files and these spans.
    This review changes study scope, not ownership or implementation semantics;
    it does not infer wrappers from names or claim behavioral equivalence.
    """
    if not isinstance(review, Mapping) or review.get("schema") != SELECTION_EXCLUSIONS_SCHEMA:
        raise ValueError("Unsupported source selection exclusions schema")
    if not isinstance(review.get("review_version"), str) or not review["review_version"].strip():
        raise ValueError("Selection exclusions require a review version")
    if (not isinstance(source_inventory_sha256, str)
            or not re.fullmatch(r"[0-9a-f]{64}", source_inventory_sha256)
            or review.get("source_inventory_sha256") != source_inventory_sha256):
        raise ValueError("Selection exclusions source inventory binding differs")
    entries = review.get("records")
    if not isinstance(entries, list):
        raise ValueError("Selection exclusions records must be a list")
    by_site = {row["site_id"]: row for row in records}
    if len(by_site) != len(records):
        raise ValueError("Duplicate source definition in selection review")
    excluded = set()
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise ValueError("Selection exclusion must be a record")
        site_id = entry.get("site_id")
        if not isinstance(site_id, str) or site_id not in by_site:
            raise ValueError("Selection exclusion names an unknown source site")
        if site_id in excluded:
            raise ValueError("Duplicate site in selection exclusions")
        row = by_site[site_id]
        if row.get("inventory_status") != "candidate":
            raise ValueError("Selection exclusion must name a candidate definition")
        if (entry.get("reason") not in ("wrapper", "unimplemented", "duplicate", "abstract_type")
                or not isinstance(entry.get("evidence"), str) or not entry["evidence"].strip()):
            raise ValueError("Selection exclusion requires a supported reason and source evidence")
        for field in ("source_sha256", "source_span_sha256"):
            value = entry.get(field)
            if (not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
                    or value != row.get(field)):
                raise ValueError("Selection exclusion source hash differs: " + field)
        excluded.add(site_id)
    return excluded


def qualified_api_id(row, language=None):
    """Name a defining API; distinguish compiler-proven Scala companions only.

    The inventory reader verifies source/compiler provenance. The selector also
    requires the claimed companion kinds to exist together in its input ledger.
    A free-form owner-kind label cannot create a second API identity.
    """
    language = str(language or row["language"]).lower()
    qualified = row["qualified_name"]
    kind = row.get("identity_owner_kind")
    if kind is None:
        return language + ":" + qualified
    proof = row.get("identity_disambiguation")
    observed = row.get("defining_owner_kind") or row.get("owner_kind")
    kinds = proof.get("owner_kinds") if isinstance(proof, Mapping) else None
    if (language != "scala" or kind != observed or kind not in {"class", "trait", "object"}
            or not isinstance(kinds, list) or any(not isinstance(value, str) for value in kinds)
            or len(kinds) != len(set(kinds))
            or set(kinds) not in ({"class", "object"}, {"trait", "object"})
            or kind not in kinds or proof.get("method") != "compiler_owner_kind_collision"
            or not row.get("source_span_sha256")
            or proof.get("source_span_sha256") != row["source_span_sha256"]):
        raise ValueError("Owner discriminator lacks compiler-bound companion collision evidence")
    return language + ":" + kind + ":" + qualified


def _qualified_record(record):
    """Keep defining/source evidence; never replace an unknown arity with zero."""
    if not isinstance(record, Mapping):
        raise ValueError("each qualified record must be a mapping")
    row = _json_copy(dict(record), str(record.get("site_id", "")), "record")
    for field in _SELECTION_FIELDS:
        row.pop(field, None)
    for field in ("site_id", "language", "name", "qualified_name", "path"):
        if not isinstance(row.get(field), str) or not row[field].strip():
            raise ValueError("Qualified selection requires a nonempty " + field)
    row["line"] = _integer(row.get("line"), "line", row["site_id"], 1)
    identity = qualified_api_id(row)
    if row.get("api_id") not in (None, identity):
        raise ValueError("Qualified API identity differs from its defining language/name")
    row.update(api_id=identity, identity_version=QUALIFIED_IDENTITY_VERSION)
    arity = row.get("parameter_count")
    status = row.get("parameter_count_status", "declared" if arity is not None else "unknown")
    if str(status).startswith("unknown"):
        if arity is not None:
            row.setdefault("reported_parameter_count", arity)
        arity = None
    if arity is not None:
        _integer(arity, "parameter_count", row["site_id"])
        if isinstance(row.get("params"), list) and len(row["params"]) != arity:
            raise ValueError("Qualified parameter count differs from explicit parameters")
    if isinstance(row.get("params"), list):
        names = [param.get("name") if isinstance(param, Mapping) else None
                 for param in row["params"]]
        if any(not isinstance(name, str) or not name for name in names) or len(set(names)) != len(names):
            raise ValueError("Qualified parameters need unique nonempty names")
    row.update(parameter_count=arity, parameter_count_status=status)
    return row


def _qualified_origin_status(row):
    """Verify the bound origin decision; readers separately recheck source bytes."""
    import hashlib
    origin = row.get("api_origin")
    if not isinstance(origin, Mapping):
        return "unresolved", "missing_defining_origin_receipt"
    payload = dict(origin); claimed = payload.pop("ownership_sha256", None)
    observed = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if claimed != observed:
        return "unresolved", "invalid_defining_origin_digest"
    if origin.get("qualified_name") != row["qualified_name"] or origin.get("site_id") != row["site_id"]:
        return "unresolved", "origin_identity_differs_from_definition"
    if origin.get("status") == "external_defined":
        return "excluded", "dependency_defined_api"
    if origin.get("status") != "library_defined":
        return "unresolved", "unresolved_defining_origin"
    source_hash = row.get("source_sha256") or row.get("file_sha256")
    if not source_hash or origin.get("file_sha256") != source_hash:
        return "unresolved", "origin_source_hash_differs_from_definition"
    return None, None


def _forwarding_target(row, by_id):
    """Accept only an attested unchanged-argument call to a known library site.

    A parser/reader must validate the call expression against the bound source
    span. Calls with callbacks, conversions, constants or side effects cannot
    satisfy this pure argument map merely by looking like ``x.map(...)``.
    """
    proof = row.get("forwarding")
    if not isinstance(proof, Mapping):
        return None
    target = by_id.get(proof.get("target_site_id"))
    if (target is None or target["site_id"] == row["site_id"]
            or proof.get("relation") != "direct_forwarder"
            or proof.get("semantics_preserved") is not True
            or not _has_evidence(proof.get("evidence"))
            or not row.get("source_span_sha256") or not target.get("source_span_sha256")
            or proof.get("source_span_sha256") != row["source_span_sha256"]
            or proof.get("target_source_span_sha256") != target["source_span_sha256"]):
        return None
    source_params, target_params = row.get("params"), target.get("params")
    mapping = proof.get("argument_map")
    if (not isinstance(source_params, list) or not isinstance(target_params, list)
            or not isinstance(mapping, list)
            or row["parameter_count"] is None or target["parameter_count"] is None):
        return None
    if any(not isinstance(item, Mapping) or set(item) != {"source_parameter", "target_parameter"}
           for item in mapping):
        return None
    sources = [item["source_parameter"] for item in mapping]
    targets = [item["target_parameter"] for item in mapping]
    if (any(not isinstance(value, str) for value in sources + targets)
            or len(set(sources)) != len(sources) or len(set(targets)) != len(targets)
            or set(sources) != {p.get("name") for p in source_params}
            or set(targets) - {p.get("name") for p in target_params}):
        return None
    for param in target_params:
        optional = param.get("required") is False or param.get("default") not in (None, "")
        if param.get("name") not in targets and not optional:
            return None
    return target["site_id"]


def _select_qualified(records):
    """Select source-owned callable families while retaining a complete ledger."""
    rows = sorted((_qualified_record(row) for row in records), key=_site_order)
    by_id = {row["site_id"]: row for row in rows}
    if len(by_id) != len(rows):
        raise ValueError("duplicate site_id values in qualified selection")
    observed_kinds = defaultdict(set)
    for row in rows:
        observed_kinds[(row["language"].lower(), row["qualified_name"])].add(
            row.get("defining_owner_kind") or row.get("owner_kind"))
    for row in rows:
        if row.get("identity_owner_kind") is not None:
            actual = observed_kinds[(row["language"].lower(), row["qualified_name"])]
            if set(row["identity_disambiguation"]["owner_kinds"]) != actual:
                raise ValueError("Companion discriminator differs from the input defining-owner family")
    decisions, eligible, notes = {}, {}, {}
    for row in rows:
        site = row["site_id"]
        status, reason = _qualified_origin_status(row)
        if row.get("callable") is False or row.get("is_exposure") is True:
            status, reason = "excluded", "noncallable_or_exposure_record"
        elif (row.get("scope") != "production" or row.get("synthetic") is not False
              or not ((row.get("declared_visibility") == "public" and row.get("public_owner_chain") is True)
                      or row.get("public_exposure_established") is True)):
            status, reason = "excluded", "not_public_production_definition"
        elif row.get("is_abstract") is True or row.get("body_presence") == "absent":
            status, reason = "excluded", "explicit_abstract_or_bodyless_declaration"
        if status:
            decisions[site] = {**row, "status": status, "reason": reason}
        else:
            eligible[site] = row
            body = row.get("body_classification") or {}
            if not isinstance(body, Mapping) or body.get("category") != "implementation":
                notes[site] = ["Body category does not prove duplication; retain the owned callable unless a forwarding target is established."]
    # Do not reinterpret same-qualified-name class/object collisions as overloads.
    groups = defaultdict(list)
    for row in eligible.values():groups[row["api_id"]].append(row)
    for api_id, group in groups.items():
        owner_kinds = {r.get("defining_owner_kind") or r.get("owner_kind") for r in group} - {None, ""}
        constructor_kinds = {"constructor" if "constructor" in str(r.get("kind", r.get("definition_kind", ""))) else "operation" for r in group}
        if len(owner_kinds) > 1 or len(constructor_kinds) > 1:
            for row in group:
                site=row["site_id"];decisions[site]={**row,"status":"unresolved","reason":"conflicting_defining_owner_kind"};eligible.pop(site)
    proofs = {site: _forwarding_target(row, eligible) for site, row in eligible.items()}
    # Direct targets must themselves remain implementation candidates. Chains
    # are retained for review rather than silently redirected to another API.
    removable = {site: target for site, target in proofs.items() if target and not proofs.get(target)}
    def elect(removed):
        families = defaultdict(list)
        for site,row in eligible.items():
            if site not in removed:families[row["api_id"]].append(row)
        winners, unknown = {}, {}
        for api_id, group in families.items():
            conditions = {json.dumps(row.get("conditional_context") or [], sort_keys=True) for row in group}
            if len(group) > 1 and len(conditions) > 1:
                unknown.update({row["site_id"]: "conditional_definition_variant_unresolved" for row in group})
            elif len(group)>1 and any(row["parameter_count"] is None for row in group):
                unknown.update({row["site_id"]: "competing_overload_arity_unknown" for row in group})
            else:
                winners[api_id] = group[0] if len(group)==1 else min(group,key=_rank)
        return winners, unknown
    while True:
        winners, unknown = elect(removable)
        retained = {row["site_id"] for row in winners.values()}
        unsupported = {site for site,target in removable.items() if target not in retained}
        if not unsupported:break
        for site in unsupported:removable.pop(site)
    for site,row in eligible.items():
        if site in removable:
            decision={**row,"status":"omitted","reason":"proven_direct_forwarder","canonical_site_id":removable[site],"relationship":"source_bound_argument_forwarding"}
        elif site in unknown:
            decision={**row,"status":"unresolved","reason":unknown[site]}
        else:
            winner=winners[row["api_id"]]
            if winner["site_id"]==site:
                reason="sole_qualified_callable_arity_unknown" if row["parameter_count"] is None else "qualified_api_maximum_parameter_count"
                decision={**row,"status":"selected","reason":reason}
            else:
                decision={**row,"status":"omitted","reason":"same_api_lower_parameter_count" if row["parameter_count"]<winner["parameter_count"] else "same_api_deterministic_arity_tie","canonical_site_id":winner["site_id"],"relationship":"overload_selection_policy_only"}
        if row.get("forwarding") and site not in removable:
            notes.setdefault(site,[]).append("Forwarding relation was not reduced: it lacks a validated map to an exactly retained library site.")
        if site in notes:decision["review_notes"]=notes[site]
        decisions[site]=decision
    ordered=[decisions[row["site_id"]] for row in rows]
    winners=sorted((r for r in ordered if r["status"]=="selected"),key=lambda r:(r["api_id"],*_site_order(r)))
    counts=Counter(r["status"] for r in ordered)
    receipt={"schema_version":2,"policy_version":QUALIFIED_POLICY_VERSION,"identity_version":QUALIFIED_IDENTITY_VERSION,
             "policy":{"scope":"one_winner_per_defining_language_qualified_api","unknown_body_is_duplicate":False,
                       "singleton_unknown_arity":"retain_without_inventing_zero","competing_unknown_arity":"unresolved",
                       "forwarding":"source_bound_argument_map_to_exact_retained_library_site","same_api_omission_claims_equivalence":False},
             "counts":{"input_sites":len(rows),"input_names":len({r['name'] for r in rows}),"input_api_ids":len({r['api_id'] for r in rows}),
                       "winner_sites":len(winners),"winner_names":len({r['name'] for r in winners}),"winner_api_ids":len(winners),
                       "excluded_sites":counts['excluded'],"omitted_sites":counts['omitted'],"unresolved_sites":counts['unresolved'],
                       "review_note_sites":sum(bool(r.get('review_notes')) for r in ordered)},
             "winner_site_ids":[r['site_id'] for r in winners],"winner_api_ids":[r['api_id'] for r in winners],
             "winner_names":[r['name'] for r in winners],"winners":winners,"site_decisions":ordered,
             "rejected_sites":[r for r in ordered if r['status']!='selected'],
             "by_language":{language:{"winner_count":sum(r['language']==language for r in winners),
                            "winner_site_ids":[r['site_id'] for r in winners if r['language']==language],
                            "winner_api_ids":[r['api_id'] for r in winners if r['language']==language],
                            "winner_names":[r['name'] for r in winners if r['language']==language]}
                            for language in sorted({r['language'] for r in rows})},
             "selection_resolved":counts['unresolved']==0}
    if len({r['api_id'] for r in winners})!=len(winners) or sum(counts.values())!=len(rows):
        raise RuntimeError("Qualified selection accounting failed")
    return receipt
