#!/usr/bin/env python3
"""Stage a portable SedonaDB native R0 study without any model calls.

Requires the small api_registry engine patch supplied beside this script.
The historical pinned source and official wheel runtime retain separate identities.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import yaml


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sql_argument(argument, index):
    if isinstance(argument, dict):
        return {"name": argument.get("name", f"arg{index}"),
                "type": str(argument.get("type", "")),
                **({"default": str(argument["default"])} if "default" in argument else {})}
    return {"name": f"arg{index}", "type": str(argument)}


def sql_signature(name, kernel):
    arguments = [sql_argument(arg, i) for i, arg in enumerate(kernel.get("args", []), 1)]
    return name + "(" + ", ".join(arg["name"] + ": " + arg["type"] for arg in arguments) + ") -> " + str(kernel.get("returns", ""))


def write_once(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != content:
        raise ValueError(f"Prepared input changed; use a fresh setup directory: {path}")
    path.write_bytes(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--preflight", type=Path)
    parser.add_argument("--source-revision", help="Exact source commit, required for source archives without Git metadata")
    parser.add_argument("--source-provenance", type=Path, help="Optional official source archive provenance JSON")
    args = parser.parse_args()
    workflow, source, output = (p.resolve() for p in (args.workflow, args.source, args.output))
    git_revision = None
    if (source / ".git").exists():
        git_revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    provenance = json.loads(args.source_provenance.read_text()) if args.source_provenance else {}
    source_revision = args.source_revision or git_revision or provenance.get("commit")
    if not source_revision or not re.fullmatch(r"[0-9a-f]{40}", source_revision):
        raise ValueError("Supply the exact source commit with --source-revision or --source-provenance")
    for observed in (git_revision, provenance.get("commit")):
        if observed and observed != source_revision:
            raise ValueError("Source revision conflicts with Git/archive provenance")
    output.mkdir(parents=True, exist_ok=True)
    link = output / "source"
    if not link.exists():
        link.symlink_to(source, target_is_directory=True)
    if link.resolve() != source:
        raise ValueError("Source link mismatch")
    expected_registry = workflow / "studies/sedonadb/evidence/configured_registry.json"
    registry = json.loads(expected_registry.read_text())
    scalars = set(registry["sedona_scalar_functions"])
    aggregates = {n for n in registry["all_aggregate_functions_including_datafusion"]
                  if n.startswith(("st_", "rs_", "s2_", "sd_"))}
    registered = scalars | aggregates
    preflight = None
    if args.preflight:
        preflight = json.loads(args.preflight.read_text())
        if not preflight.get("ready"):
            raise ValueError("Runtime preflight is not ready")
        scalars = set(preflight["scalar_names"])
        aggregates = set(preflight["aggregate_names"])
        registered = scalars | aggregates
    records_by_name = {}
    docs_by_name = {}
    all_documented_names = set()
    for page in sorted((source / "docs/reference/sql").glob("*.qmd")):
        body = page.read_text()
        front = yaml.safe_load(body.split("---", 2)[1])
        name = front.get("title", "")
        if re.fullmatch(r"(?:ST|RS|S2|SD)_[A-Za-z_0-9]+", name, re.I):
            all_documented_names.add(name)
        if not name or name.lower() not in registered:
            continue
        kernels = front.get("kernels", [])
        signature = " | ".join(sql_signature(name, kernel) for kernel in kernels)
        primary_args = max((kernel.get("args", []) for kernel in kernels), key=len, default=[])
        records_by_name[name.lower()] = {
            "name": name, "signature": signature or name,
            "params": [sql_argument(arg, i) for i, arg in enumerate(primary_args, 1)], "returns": " | ".join(sorted({str(k.get("returns", "")) for k in kernels})),
            "description": body,
            "file": "source/" + str(page.relative_to(source)), "line": next(i for i,l in enumerate(body.splitlines(),1) if l.startswith("title:")),
            "file_sha256": digest(page), "registration_kind": "aggregate" if name.lower() in aggregates else "scalar",
            "evidence_kind": "upstream_sql_reference"}
        docs_by_name[name.lower()] = str(page.relative_to(source))
    # These registered names have no individual upstream SQL reference page.
    # Bind actual registration source; never invent a public Python definition.
    missing_sources = {
        "sd_simplifystorage": "rust/sedona-functions/src/sd_simplifystorage.rs",
        "st_geomfromwkbunchecked": "rust/sedona-functions/src/st_geomfromwkb.rs",
        "st_longestline": "c/sedona-s2geography/src/kernels.rs",
        "st_shortestline": "c/sedona-s2geography/src/kernels.rs",
        "st_numinteriorring": "c/sedona-geos/src/register.rs",
    }
    for name in sorted(registered - set(records_by_name)):
        literal = re.compile(r'"' + re.escape(name) + r'"', re.I)
        if name not in missing_sources:
            candidates = sorted(p for subtree in ("rust", "c") for p in (source / subtree).glob("*/src/**/*.rs")
                                if literal.search(p.read_text()))
            if not candidates:
                if not preflight:
                    raise ValueError(f"SQL name {name!r} has no documentation or source registration evidence, and no live runtime registry is supplied")
                records_by_name[name] = {
                    "name": name, "signature": name + "(parameters not documented in the configured SQL reference)",
                    "params": [], "returns": "", "description": "Name verified in the measured runtime SQL registry. No individual original SQL reference page or literal registration site was found in the supplied source. Do not invent an undocumented contract.",
                    "file": str(output / "inputs/runtime_identity.json"), "line": 1,
                    "file_sha256": digest(args.preflight), "registration_kind": "aggregate" if name in aggregates else "scalar",
                    "evidence_kind": "measured_runtime_registry_no_literal_source_site"}
                continue
            path = candidates[0]
        else:
            path = source / missing_sources[name]
        lines = path.read_text().splitlines()
        line = next(i for i,l in enumerate(lines,1) if literal.search(l))
        records_by_name[name] = {
            "name": name, "signature": name + "(parameters not documented in the configured SQL reference)",
            "params": [], "returns": "", "description": "Registered SQL function with no individual page in the configured original SQL reference. Do not invent an undocumented contract.",
            "file": "source/" + str(path.relative_to(source)), "line": line,
            "file_sha256": digest(path), "registration_kind": "scalar",
            "evidence_kind": "upstream_registration_source"}
    definitions = [records_by_name[name] for name in sorted(registered)]
    live_registry = {"scalar_names": sorted(scalars), "aggregate_names": sorted(aggregates)}
    inventory = {"schema": 1, "kind": "registered_sql", "source_revision": source_revision,
                 "source_provenance": provenance,
                 "registry_sha256": hashlib.sha256(json.dumps(live_registry,sort_keys=True).encode()).hexdigest(),
                 "registry_origin": "runtime_preflight" if preflight else "historical_reference_unvalidated",
                 "runtime_preflight_sha256": digest(args.preflight) if preflight else None,
                 "historical_registry_sha256": digest(expected_registry), "registered_names": sorted(registered),
                 "definitions": definitions, "documented_but_not_registered": sorted(n for n in all_documented_names if n.lower() not in registered),
                 "scope": "Configured Sedona SQL scalar and aggregate registry; excludes DataFusion builtins and Rust public methods."}
    inventory_path = output / "inputs/sql_api_inventory.json"
    write_once(inventory_path, (json.dumps(inventory, indent=2) + "\n").encode())
    write_once(output / "inputs/api_manifest.json", (json.dumps([d["name"] for d in definitions], indent=2) + "\n").encode())
    write_once(output / "inputs/expected_registry.json", expected_registry.read_bytes())
    helpers = Path(__file__).resolve().parent
    for filename in ("sedona_runtime.py", "run_snippet.py", "api_test_scaffold.py", "preflight.py"):
        write_once(output / "runtime" / filename, (helpers / filename).read_bytes())
    for filename in ("cea.tif", "test4.tiff"):
        write_once(output / "fixtures" / filename, (workflow / "studies/sedonadb/evidence" / filename).read_bytes())
    if preflight:
        write_once(output / "inputs/runtime_identity.json", args.preflight.read_bytes())
    profile = {
        "role": "A Python developer using SedonaDB SQL for geospatial computation.",
        "project": {"name": "SedonaDB registered SQL surface", "language": "Python and SQL", "description": "SedonaDB SQL scalar and aggregate functions called through the official Python SQL connection."},
        "domain": "Geospatial vector and raster analysis", "target_users": ["Python developers using SedonaDB SQL"],
        "use_cases": ["Run small SQL queries and verify materialized geometry, raster, scalar, and aggregate results."],
        "constraints": ["Use the original SQL API and original documentation only.", "Write Python statements using sd.sql(query).to_arrow_table(); assert known documented results and print the __CHECK__ witness.", "Use tiny literal inputs or the supplied local raster files. No remote datasets or services."]}
    write_once(output / "configs/project_profile.yaml", yaml.safe_dump(profile,sort_keys=False).encode())
    config = {"extends": [], "project": {"name": "SedonaDB configured SQL Original R0", "language": "Python"},
        "codebase": {"source_globs": ["source/rust/*/src/**/*.rs", "source/c/*/src/**/*.rs", "source/docs/reference/sql/*.qmd"],
                     "test_globs": [], "surface_filter": "all", "intent": {"use_llm": False},
                     "api_inventory": str(inventory_path), "api_inventory_sha256": digest(inventory_path)},
        "files": {"project_profile": "configs/project_profile.yaml", "original_readme": ["source/README.md", "source/docs/reference/sql/*.qmd"],
                  "llm_readme": "docs/LLM_readme.md", "notes_to_self": "docs/notes_to_self.md", "error_log": "logs/error_log.jsonl"},
        "models": {"registry": {"selected": {"provider": "google", "model": "gemini-3.1-flash-lite"}}, "roles": {"author": "selected", "audience": "selected", "fixer": "selected"}},
        "coverage": {"documentation_call_patterns": [r"\b{name}\s*\(", r"(?m)^title:\s*{name}\s*$"]},
        "comprehension": {"class_context": False, "relevant_doc_chars": 12000, "execute": {
            "scaffold": "runtime/api_test_scaffold.py", "test_filename": "ApiTest.py",
            "region": ["# TODO API_TEST_START", "# TODO API_TEST_END"], "build": "",
            "command": f'"{args.python.absolute()}" "{output / "runtime/run_snippet.py"}" "{{test_file}}"',
            "work_dir": "execution", "output_dir": "execution/output", "local_uris": False,
            "sample_data": {"raster_cea_tif": "fixtures/cea.tif", "raster_test4_tif": "fixtures/test4.tiff"},
            "preamble": "", "io_hints": "", "max_fix_rounds": 0, "require_correctness": True,
            "timeout_seconds": 60, "success_marker": "__DONE__", "error_marker": "__RUN_ERR__", "check_marker": "__CHECK__",
            "execution_context": "Write Python statements only. A SedonaDB connection named sd is already provided. The target is a SQL function, not a Python method: call it inside sd.sql(\"SELECT ...\"). Materialize with .to_arrow_table(), which returns a real pyarrow.Table. Read a scalar with table.column(\"name\")[0].as_py() or rows with table.to_pylist(). Setup SQL may use sd.sql(...).execute(). The adapter requires the target SQL function to be called and materialized. Do not import another database or replace sd. Use Python assert with a falsifiable documented expectation and then print the exact target __CHECK__ witness.",
            "exec_hints": "Use individual SQL statements. Paths raster_cea_tif and raster_test4_tif are available local fixture files; output_dir is available for tiny outputs. Use only these paths when a documented operation needs a file. Tiny SQL VALUES and documented constructors are available for in-memory inputs. Do not use remote URLs. No repairs are permitted in this R0 run."}}}
    write_once(output / "configs/aideal.yaml", yaml.safe_dump(config,sort_keys=False).encode())
    artifacts = [str(inventory_path), str(output / "inputs/expected_registry.json")]
    artifacts += [str(output / "runtime" / n) for n in ("sedona_runtime.py", "run_snippet.py", "api_test_scaffold.py")]
    if preflight:
        artifacts += [str(output / "inputs/runtime_identity.json"), preflight["extension"]["path"]]
        for key in ("pyproj_database", "rasterio_database"):
            if key in preflight.get("native_dependencies", {}):
                artifacts.append(preflight["native_dependencies"][key]["path"])
    catalog = {"sedonadb": {"base_config": str(output / "configs/aideal.yaml"),
        "manifest": str(output / "inputs/api_manifest.json"), "source_link": {"name": "source", "target": str(source)},
        "runtime_artifacts": artifacts,
        "scope_note": f"{len(registered)} configured registered SQL names ({len(scalars)} scalar and {len(aggregates)} aggregate), including {len(registered)-len(docs_by_name)} names without individual original SQL reference pages. Source revision {source_revision}; runtime wheel, native databases and original source evidence are fingerprinted. One audience-written R0 assertion snippet per name; operator smoke tests are separate."}}
    if not preflight:
        catalog["sedonadb"]["blocked"] = "Run preflight in the measured environment and rebuild setup with --preflight before paid execution."
    write_once(output / "catalog.yaml", yaml.safe_dump(catalog,sort_keys=False).encode())
    print(json.dumps({"output": str(output), "apis": len(definitions), "documented": len(docs_by_name), "runtime_validated": bool(preflight)}))


if __name__ == "__main__":
    main()
