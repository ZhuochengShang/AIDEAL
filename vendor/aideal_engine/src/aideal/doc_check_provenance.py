"""Native check input hashes and checkpoint reuse identity.

Implementation files stay beside this module, preserving resource roots.
The split implementation files are explicitly hashed so a refactor never
reuses an old engine checkpoint as though its implementation were unchanged."""
from __future__ import annotations

import sys
from pathlib import Path
from .config import AidealConfig


def _sha256_files(paths: list[Path], root: Path | None = None) -> dict:
    """Hash file names and contents deterministically for run provenance."""
    import hashlib

    digest = hashlib.sha256()
    files: list[Path] = []
    for path in paths:
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(p for p in path.rglob("*") if p.is_file())
    unique = sorted(set(p.resolve() for p in files), key=str)
    for path in unique:
        try:
            label = path.relative_to(root.resolve()) if root else path
        except ValueError:
            label = path
        digest.update(str(label).encode("utf-8"))
        digest.update(b"\0")
        try:
            with path.open("rb") as src:
                for chunk in iter(lambda: src.read(1024 * 1024), b""):
                    digest.update(chunk)
        except OSError as exc:
            digest.update(f"<unreadable:{type(exc).__name__}>".encode("utf-8"))
        digest.update(b"\0")
    return {"sha256": digest.hexdigest(), "file_count": len(unique)}


def _comprehension_fingerprint_components(
        cfg: AidealConfig, *, ex: dict, doc_source: str, doc_scope: str,
        max_fix_rounds: int, manifest_sha256: str, document_sha256: str,
        scaffold_file: Path, sample_data: dict, class_context: bool,
        timeout: int) -> dict:
    """Return every material input that makes a checkpoint reusable.

    A checkpoint is experimental evidence, not merely a performance cache. A
    model, YAML, scaffold, source, fixture, interpreter, or engine change must
    create a new fingerprint so an overnight watchdog cannot silently mix
    conditions after a restart.
    """
    import glob
    import os

    source_paths: list[Path] = []
    for pattern in cfg.source_globs:
        source_paths.extend(Path(p) for p in glob.glob(
            str(cfg.root / pattern), recursive=True))
    # output_dir is a writable destination supplied to snippets, not input
    # evidence. Its location remains in execute_config; its changing contents
    # must never invalidate completed API checkpoints.
    from urllib.parse import unquote, urlparse
    fixture_paths = [Path(unquote(urlparse(str(value)).path)
                          if str(value).startswith("file://") else str(value))
                     for key, value in sample_data.items() if key != "output_dir"]
    engine_dir = Path(__file__).resolve().parent
    engine_paths = [engine_dir / name for name in (
        "config.py", "doc_checks.py", "llm.py", "prompts.py", "readme_agent.py",
        "checkpoint_compatibility.py", "provider_deadline.py", "experiment_identity.py",
        "profile.py", "execution.py", "native_execution_contract.py", "evaluation_scope.py",
        # The facade no longer contains these implementations. Keep all moved
        # code in the checkpoint identity; historical journals remain unchanged.
        "doc_check_provenance.py", "doc_check_sources.py", "doc_check_inputs.py",
        "doc_check_errors.py", "doc_check_comprehension.py", "doc_check_execution.py",
        "doc_check_puzzles.py", "readme_format.py", "readme_evidence.py",
        "readme_catalogue.py", "api_visibility.py", "api_examples.py",
        "scaffold_generation.py", "api_intent.py", "api_overloads.py",
        "api_signatures.py", "api_discovery.py", "api_origin.py", "api_registry.py", "api_sql_canonical.py", "api_source_registry.py", "api_canonical_selection.py", "api_public_inventory.py", "api_coverage.py",
        "readme_generation.py", "readme_recording.py",
        "readme_validation.py", "readme_replay.py", "original_documentation.py")]
    from .experiment_identity import extra_components
    from .original_documentation import original_document_paths
    runtime_identity = {}
    if ex.get("runtime_profile"):
        from workflow.runtime_profile import load_runtime_profile, runtime_profile_receipts
        profile = load_runtime_profile((cfg.root / ex["runtime_profile"]).resolve())
        runtime_identity = {"runtime_profile": runtime_profile_receipts(profile)}
    audience = cfg.model_for_role("audience")
    fixer = cfg.model_for_role("fixer")
    return {
        "schema": 4,
        **runtime_identity,
        **extra_components(cfg),
        "project": cfg.project_name,
        "language": cfg.language,
        "doc_source": doc_source,
        "doc_scope": doc_scope,
        "max_fix_rounds": max_fix_rounds,
        "manifest_sha256": manifest_sha256,
        "document_sha256": document_sha256,
        "original_document_files": _sha256_files(original_document_paths(cfg), cfg.root),
        "models": {
            "audience": f"{audience.provider}:{audience.model}",
            "fixer": f"{fixer.provider}:{fixer.model}",
            **({"audience_max_output_tokens": audience.max_output_tokens}
               if audience.max_output_tokens is not None else {}),
            **({"fixer_max_output_tokens": fixer.max_output_tokens}
               if fixer.max_output_tokens is not None else {}),
        },
        "class_context": bool(class_context),
        # Receiver overrides affect audience prompts and must invalidate resume.
        "owner_overrides": cfg.comprehension.get("owner_overrides", {}),
        "timeout_s": timeout,
        "execute_config": ex,
        "scaffold": _sha256_files([scaffold_file], cfg.root),
        "source": _sha256_files(source_paths, cfg.root),
        "api_inventory": _sha256_files(
            [cfg.root / cfg.raw["codebase"]["api_inventory"]]
            if cfg.raw.get("codebase", {}).get("api_inventory") else [], cfg.root),
        "fixtures": _sha256_files(fixture_paths, cfg.root),
        "engine": _sha256_files(engine_paths, engine_dir),
        "interpreter": {
            "executable": sys.executable,
            "version": sys.version,
            "environment_sha256": os.environ.get("AIDEAL_ENV_FINGERPRINT", ""),
        },
    }


def _checkpoint_row_reusable(row: dict, experiment_fingerprint: str) -> bool:
    """Only stable terminal rows may suppress work after a restart."""
    # Transport errors and returned but unusable responses both need a new
    # provider attempt on an explicit resume. They are not program repairs.
    category = str(row.get("error_category") or "")
    return (row.get("experiment_fingerprint") == experiment_fingerprint
            and category != "llm-error" and not category.startswith("provider-"))
