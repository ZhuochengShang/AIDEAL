"""Prepare a library-independent five-condition study without running models."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

from .ablation import ARMS, bind, load, preflight, save


CONDITION_FOLDERS = {
    "original": "Original",
    "readme_only": "README only",
    "alias_only": "Alias only",
    "error_hints_only": "Error hints only",
    "combined": "Combined",
}


def _engine_config_module():
    """Load the pinned engine's YAML loader, without importing its model clients."""
    name = "_aideal_workflow_engine_config"
    if name not in sys.modules:
        path = Path(__file__).resolve().parents[1] / "vendor/aideal_engine/src/aideal/config.py"
        spec = spec_from_file_location(name, path)
        module = module_from_spec(spec)
        sys.modules[name] = module  # dataclasses needs the module registered.
        try:
            spec.loader.exec_module(module)
        except Exception:
            del sys.modules[name]
            raise
    return sys.modules[name]


def prepare_study(config, output):
    """Read the archived engine's YAML schema and create five isolated drafts.

    No new source-path schema: cfg.root and source/test globs retain the archived
    loader's path rules. JSON files below are generated records, not replacement
    user configuration. No commands or model clients from the YAML are executed.
    """
    config = Path(config).expanduser().resolve()
    output = Path(output).expanduser().resolve()
    if not config.is_file():
        raise ValueError(f"Missing AIDEAL YAML configuration: {config}")
    if output.exists():
        raise FileExistsError(f"Study output already exists; inspect it or choose a new path: {output}")
    engine = _engine_config_module()
    cfg = engine.load_config(config)
    if not cfg.source_globs:
        raise ValueError("Set codebase.source_globs in the AIDEAL YAML")
    if not cfg.original_readme_files:
        raise ValueError("files.original_readme did not resolve to any documentation files")
    if output == cfg.root or output in cfg.root.parents:
        raise ValueError("Study output cannot contain the configuration workspace")
    project_raw = engine.yaml.safe_load(config.read_text(encoding="utf-8")) or {}
    layers = [engine.DEFAULTS_PATH] if engine.DEFAULTS_PATH.is_file() else []
    for name in project_raw.get("extends", []) or []:
        adapter = engine._resolve_adapter(name, config.parent)
        if adapter is None:
            raise ValueError(f"Unknown extends adapter: {name}")
        layers.append(adapter)
    layers.append(config)
    source = {
        "configuration": bind(config), "configuration_layers": [bind(p) for p in layers],
        "workspace_root": str(cfg.root), "project": cfg.project_name,
        "language": cfg.language, "source_globs": cfg.source_globs,
        "test_globs": cfg.test_globs, "snapshot_frozen": False,
        "original_documentation": [bind(p) for p in cfg.original_readme_files],
        "loader": bind(Path(engine.__file__)),
    }
    # Keep the loader's complete ordered documentation bundle, including its
    # file headers, so a multi-file baseline is not reduced to its first README.
    original_text = cfg.original_readme_text()
    evaluation = cfg.raw.get("evaluation", {}) or {}
    plan = {
        "schema_version": 1, "study_id": output.name, "status": "draft_not_running",
        "configuration_path": str(config), "source_revision": None,
        "api_names": [], "development_case_ids": [], "shared_artifacts": [],
        "common": {
            "model": None, "temperature": None, "max_output_tokens": None,
            "max_snippet_fixes": None, "provider_attempt_limit": None,
            "execution_timeout_s": None, "trial_ids": None, "prompt_sha256": None,
        },
        "arms": {
            arm: dict(zip(("readme", "aliases", "error_hints"), flags))
            for arm, flags in ARMS.items()
        },
        "treatments": {
            "original_readme": None, "improved_readme": None,
            "alias_interface": None, "error_hints": None,
        },
        "adapter_validation": None,
        "limitations": [
            "Source/test globs use the archived YAML loader; no backend snapshot is frozen.",
            "No API inventory, task bank, model call or measured result is produced by setup.",
            "Combined must reuse the exact individual treatment artifacts.",
        ],
    }
    for key in plan["common"]:
        plan["common"][key] = evaluation.get(key)
    # Validate inputs before creating any output. Exclusive creation prevents
    # replacing an existing study or its measurements.
    output.mkdir(parents=True, exist_ok=False)
    original = output / "original_documentation.txt"
    original.write_text(original_text, encoding="utf-8")
    plan["treatments"]["original_readme"] = bind(original)
    save(output / "source.json", source)
    save(output / "plan.draft.json", plan)
    save(output / "bank.draft.json", {"schema_version": 1, "cases": []})
    for arm, folder in CONDITION_FOLDERS.items():
        save(output / folder / "condition.json", {
            "arm": arm, **plan["arms"][arm], "shared_plan": "../plan.draft.json",
            "shared_bank": "../bank.draft.json", "backend_path": None,
            "state": "configuration_only_not_measured",
        })
        (output / folder / "README.md").write_text(
            f"# {folder}\n\nRead `condition.json` for this condition. All conditions use\n"
            "the parent study's shared plan and task bank. No backend has been\n"
            "provisioned and no evaluation has run.\n", encoding="utf-8",
        )
    (output / "README.md").write_text(
        "# Prepared AIDEAL study\n\n"
        "1. Inspect `source.json`: the YAML layers, workspace, source globs and documentation bindings.\n"
        "2. Set user inputs in the original YAML; plan.draft.json is the generated preparation record.\n"
        "3. Complete and validate `bank.draft.json`: shared microtasks and puzzles.\n"
        "4. Provision isolated backends, validate the adapter and freeze the study.\n"
        "5. Evaluate Original, README only, Alias only, Error hints only and Combined.\n\n"
        "The five folders select conditions; they are not copies of the source or Git branches.\n"
        "Setup has not generated treatments, called a model or produced results.\n"
        "Follow the AIDEAL repository README for the full operating sequence.\n",
        encoding="utf-8",
    )
    return prepared_study_status(output)


def prepared_study_status(directory):
    """Report generic draft readiness without implying adapter execution exists."""
    directory = Path(directory).expanduser().resolve()
    plan = load(directory / "plan.draft.json")
    bank = load(directory / "bank.draft.json")
    return {
        "study_directory": str(directory), "source": load(directory / "source.json"),
        "conditions": CONDITION_FOLDERS, "selected_apis": len(plan["api_names"]),
        "candidate_cases": len(bank["cases"]), "preflight_issues": preflight(plan, bank),
        "launched": False, "matched_results": None,
        "limitation": "Draft inspection only; source snapshots, adapters and approval admission remain to be implemented/validated.",
    }
