"""Explicit, hash-bound migration of a single legacy checkpoint group.

No implicit engine exceptions or cross-treatment reuse. An operator prepares
the record offline after reproducing the old fingerprint and reviewing the
bookkeeping/transport-only patch. Historical JSONL rows are never rewritten.
"""
import hashlib
import json
from pathlib import Path

from .experiment_identity import digest_native


def fingerprint(parts):
    return digest_native(parts)


def load_compatibility(checkpoint: Path, current: dict) -> dict:
    path = checkpoint.with_name("checkpoint_compatibility.json")
    if not path.exists():
        return {}
    record = json.loads(path.read_text())
    if record.get("schema") != 1 or record.get("checkpoint") != str(checkpoint.resolve()):
        raise ValueError("Checkpoint compatibility scope mismatch")
    if record.get("current_components") != current:
        # Source/config/doc/input changes require new evidence, never an alias.
        return {}
    old = record["legacy_components"]
    if fingerprint(old) != record["legacy_fingerprint"]:
        raise ValueError("Invalid legacy fingerprint proof")
    if record["input_fixtures"] != current["fixtures"]:
        raise ValueError("Input fixture proof mismatch")
    allowed = {"schema", "engine", "fixtures"}
    if {k: v for k, v in old.items() if k not in allowed} != {
            k: v for k, v in current.items() if k not in allowed}:
        raise ValueError("Checkpoint migration changes experimental inputs")
    return {"legacy_fingerprint": record["legacy_fingerprint"],
            "current_fingerprint": fingerprint(current),
            "record": str(path), "record_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "selection_policy": record["selection_policy"],
            "reason": record["reason"]}
