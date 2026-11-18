"""Portable, frozen puzzle plans for AIDEAL integration evaluation.

The test bank describes tasks and API combinations.  The sample-data manifest
describes repository-owned fixtures.  ``freeze_puzzle_plan`` joins the two and
records resolved paths plus content hashes so every documentation/alias
ablation can run exactly the same cases and bytes.
"""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any

import yaml


VALID_MODES = {"composition", "discovery"}
VALID_STAGES = {"load", "transform", "analytics", "output"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_structured(path: Path) -> dict[str, Any]:
    """Load a JSON or YAML mapping with one consistent error contract."""
    text = path.read_text(encoding="utf-8")
    data = json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a mapping at the top level")
    return data


def _datasets(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = manifest.get("datasets") or {}
    if isinstance(raw, dict):
        return {
            str(name): ({**value, "id": str(name)} if isinstance(value, dict) else {})
            for name, value in raw.items()
        }
    if isinstance(raw, list):
        return {
            str(item.get("id", "")): dict(item)
            for item in raw
            if isinstance(item, dict) and item.get("id")
        }
    return {}


def normalize_apis(case: dict[str, Any]) -> list[dict[str, str]]:
    raw = case.get("candidate_apis") or case.get("apis") or []
    result: list[dict[str, str]] = []
    for item in raw:
        if isinstance(item, str):
            result.append({"name": item, "stage": ""})
        elif isinstance(item, dict):
            result.append({
                "name": str(item.get("name", "")).strip(),
                "stage": str(item.get("stage", "")).strip(),
                "receiver": str(item.get("receiver", "")).strip(),
            })
    return result


def validate_bank(
    bank: dict[str, Any],
    sample_manifest: dict[str, Any],
    *,
    documented_apis: set[str] | None = None,
) -> list[str]:
    """Validate portable structure and cross-links without invoking an LLM."""
    errors: list[str] = []
    cases = bank.get("cases") or bank.get("puzzles") or []
    datasets = _datasets(sample_manifest)
    if not isinstance(cases, list) or not cases:
        return ["test bank has no cases"]
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            errors.append("test bank contains a non-mapping case")
            continue
        case_id = str(case.get("id", "")).strip()
        if not case_id:
            errors.append("case is missing id")
            continue
        if case_id in seen:
            errors.append(f"duplicate case id: {case_id}")
        seen.add(case_id)
        if not str(case.get("goal") or case.get("user_prompt") or "").strip():
            errors.append(f"{case_id}: goal or user_prompt is required")
        modes = set(case.get("modes") or ["composition"])
        unknown_modes = modes - VALID_MODES
        if unknown_modes:
            errors.append(f"{case_id}: invalid modes: {sorted(unknown_modes)}")
        apis = normalize_apis(case)
        if not apis:
            errors.append(f"{case_id}: no APIs configured")
        for api in apis:
            name = api["name"]
            if not name:
                errors.append(f"{case_id}: API is missing name")
            elif documented_apis is not None and name not in documented_apis:
                errors.append(f"{case_id}: API is not documented: {name}")
            stage = api.get("stage", "")
            if stage and stage not in VALID_STAGES:
                errors.append(f"{case_id}: invalid stage for {name}: {stage}")
        for dataset_id in case.get("datasets") or []:
            if dataset_id not in datasets:
                errors.append(f"{case_id}: unknown dataset: {dataset_id}")
        output = case.get("output") or case.get("output_contract") or {}
        if output and not str(output.get("file", "")).strip():
            errors.append(f"{case_id}: output contract requires file")
    return errors


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def _resolved_dataset(root: Path, dataset: dict[str, Any]) -> dict[str, Any]:
    dataset_id = str(dataset["id"])
    value = str(dataset.get("path", "")).strip()
    if not value:
        raise ValueError(f"dataset {dataset_id} is missing path")
    path = _resolve(root, value)
    if not path.is_file():
        raise FileNotFoundError(f"dataset {dataset_id} does not exist: {path}")
    companions: list[dict[str, Any]] = []
    for item in dataset.get("companions") or []:
        companion = _resolve(root, str(item))
        if not companion.is_file():
            raise FileNotFoundError(
                f"dataset {dataset_id} companion does not exist: {companion}"
            )
        companions.append({
            "path": str(companion),
            "sha256": sha256_file(companion),
            "bytes": companion.stat().st_size,
        })
    return {
        **dataset,
        "id": dataset_id,
        "path": str(path),
        "uri": path.as_uri(),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "companions": companions,
    }


def _resolved_oracle(root: Path, value: str) -> dict[str, Any] | None:
    if not value:
        return None
    path = _resolve(root, value)
    if not path.exists():
        raise FileNotFoundError(f"puzzle oracle does not exist: {path}")
    if path.is_dir():
        raise ValueError(f"puzzle oracle must be one normalized file, not a directory: {path}")
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def freeze_puzzle_plan(
    *,
    root: Path,
    bank_path: Path,
    sample_data_path: Path,
    mode: str = "composition",
    case_ids: list[str] | None = None,
    sample: int | None = None,
    seed: int = 42,
    documented_apis: set[str] | None = None,
) -> dict[str, Any]:
    """Create an immutable-by-content plan shared by every ablation arm."""
    if mode not in VALID_MODES:
        raise ValueError(f"mode must be one of {sorted(VALID_MODES)}, got {mode!r}")
    bank_path = bank_path.resolve()
    sample_data_path = sample_data_path.resolve()
    bank = load_structured(bank_path)
    manifest = load_structured(sample_data_path)
    errors = validate_bank(bank, manifest, documented_apis=documented_apis)
    if errors:
        raise ValueError("invalid puzzle bank:\n- " + "\n- ".join(errors))

    cases = [
        dict(case)
        for case in (bank.get("cases") or bank.get("puzzles") or [])
        if mode in (case.get("modes") or ["composition"])
    ]
    by_id = {str(case["id"]): case for case in cases}
    if case_ids:
        missing = [case_id for case_id in case_ids if case_id not in by_id]
        if missing:
            raise ValueError(f"cases not available in {mode} mode: {', '.join(missing)}")
        selected = [by_id[case_id] for case_id in case_ids]
    elif sample is not None and sample < len(cases):
        if sample < 1:
            raise ValueError("sample must be at least 1")
        selected = random.Random(seed).sample(cases, sample)
    else:
        selected = cases
    if not selected:
        raise ValueError(f"no puzzle cases support mode={mode}")

    datasets = _datasets(manifest)
    resolved_cases: list[dict[str, Any]] = []
    for case in selected:
        resolved_cases.append({
            "id": str(case["id"]),
            "goal": str(case.get("goal", "")).strip(),
            "user_prompt": str(case.get("user_prompt", "")).strip(),
            "mode": mode,
            "api_policy": str(case.get("api_policy", "exact")),
            "apis": normalize_apis(case),
            "datasets": [
                _resolved_dataset(root, datasets[dataset_id])
                for dataset_id in (case.get("datasets") or [])
            ],
            "output": dict(case.get("output") or case.get("output_contract") or {}),
            "oracle": _resolved_oracle(root, str(case.get("oracle", "")).strip()),
            "tags": list(case.get("tags") or []),
        })

    return {
        "schema_version": 1,
        "kind": "aideal_frozen_puzzle_plan",
        "bank_id": str(bank.get("bank_id") or bank.get("suite") or bank_path.stem),
        "bank_path": str(bank_path),
        "bank_sha256": sha256_file(bank_path),
        "sample_data_path": str(sample_data_path),
        "sample_data_sha256": sha256_file(sample_data_path),
        "mode": mode,
        "seed": seed,
        "selection": "explicit" if case_ids else ("sample" if sample is not None else "all"),
        "case_ids": [case["id"] for case in resolved_cases],
        "cases": resolved_cases,
    }


def write_plan(plan: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def verify_plan_inputs(plan: dict[str, Any]) -> list[str]:
    """Detect fixture drift before an expensive LLM/Spark run."""
    errors: list[str] = []
    for case in plan.get("cases") or []:
        for dataset in case.get("datasets") or []:
            path = Path(str(dataset.get("path", "")))
            if not path.is_file():
                errors.append(f"{case.get('id')}: missing dataset {path}")
                continue
            expected = str(dataset.get("sha256", ""))
            if expected and sha256_file(path) != expected:
                errors.append(f"{case.get('id')}: dataset hash changed: {path}")
            for companion in dataset.get("companions") or []:
                cpath = Path(str(companion.get("path", "")))
                if not cpath.is_file():
                    errors.append(f"{case.get('id')}: missing companion {cpath}")
                elif companion.get("sha256") and sha256_file(cpath) != companion["sha256"]:
                    errors.append(f"{case.get('id')}: companion hash changed: {cpath}")
        oracle = case.get("oracle")
        if isinstance(oracle, dict) and oracle.get("path"):
            opath = Path(str(oracle["path"]))
            if not opath.is_file():
                errors.append(f"{case.get('id')}: missing oracle {opath}")
            elif oracle.get("sha256") and sha256_file(opath) != oracle["sha256"]:
                errors.append(f"{case.get('id')}: oracle hash changed: {opath}")
    return errors
