"""SedonaDB-only prompt inspection, separate from the general workflow CLI."""
import json
from pathlib import Path

from workflow.ablation import load, save


def trace(root, api):
    """Save an explicitly labeled SQL prompt preview and link recorded outcomes."""
    root = Path(root)
    entries = load(root / "studies/sedonadb/evidence/sql_reference_inventory.json")
    item = next((row for row in entries if row["api"] == api and row["kind"] == "function_reference"), None)
    if item is None:
        raise ValueError(f"Unknown SQL documentation API: {api}")
    docs = root / "studies/sedonadb/evidence/reference" / Path(item["source"]).name
    out = root / ".runs/traces" / api
    out.mkdir(parents=True, exist_ok=True)
    template = (root / "prompts/comprehension_write_exec.md").read_text()
    values = {"language": "Rust", "execution_context": "A SedonaContext named ctx is provided inside an async function.",
              "project_context": "SedonaDB pinned Rust-hosted SQL surface; code must materialize its results.",
              "api_body": docs.read_text(), "available_inputs": "Literal inputs from the documented example; no secret or remote data.",
              "receiver": "Call SQL function " + api + " through ctx.sql(...).await, then collect the result.",
              "known_failures": "", "api_name": api, "io_hints": "", "exec_hints": ""}
    prompt = template.format(**values)
    (out / "audience_prompt_preview.txt").write_text(prompt)
    (out / "documentation.qmd").write_text(docs.read_text())
    if item["examples"]:
        (out / "documented_example_001.sql").write_text(item["examples"][0])
    result = {"api": api, "mode": "inspectable_prompt_preview_and_recorded_execution",
              "model_called": False, "preview_is_not_a_historical_delivered_prompt": True,
              "prompt_template": "prompts/comprehension_write_exec.md", "prompt_preview": str(out / "audience_prompt_preview.txt"),
              "documentation": str(docs), "harness": "studies/sedonadb/harnesses/configured/src/main.rs",
              "operator_skill": "skills/aideal-experiment-operator.SKILL.md",
              "operator_skill_injected_into_audience": False,
              "recorded_examples": []}
    for variant in ("default_results.jsonl", "configured_results.jsonl"):
        path = root / "studies/sedonadb/evidence" / variant
        if path.exists():
            result["recorded_examples"].extend({"variant": variant, **row} for row in
                [json.loads(line) for line in path.read_text().splitlines()] if row["api"] == api)
    save(out / "trace.json", result)
    return result
