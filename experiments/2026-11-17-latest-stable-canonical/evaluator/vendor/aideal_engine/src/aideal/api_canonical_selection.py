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
    records: Iterable[Mapping[str, Any]],
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
