"""Resumable, no-LLM execution of pinned SQL documentation through Rust."""
from __future__ import annotations
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time
from collections import Counter

from workflow.ablation import bind, digest, file_hash, load, save


def _resume_records(journal, fingerprint, expected_cases):
    """Reject incompatible or damaged evidence before skipping any execution."""
    if not journal.exists():
        return {}
    done = {}
    for line_number, line in enumerate(journal.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid journal JSON at line {line_number}; retain it for recovery") from exc
        if not isinstance(row, dict):
            raise ValueError(f"Invalid journal record at line {line_number}")
        case_id = row.get("case_id")
        if not isinstance(case_id, str) or case_id not in expected_cases:
            raise ValueError(f"Unknown journal case at line {line_number}: {case_id}")
        if case_id in done:
            raise ValueError(f"Duplicate journal case: {case_id}")
        if row.get("fingerprint") != fingerprint:
            raise ValueError(f"Incompatible journal fingerprint: {case_id}")
        if (row.get("api"), row.get("example_index")) != expected_cases[case_id]:
            raise ValueError(f"Journal case metadata differs from catalog: {case_id}")
        if row.get("status") not in (
            "external_fixture_pending", "statement_review_required", "outer_timeout",
            "runner_error", "invalid_runner_output", "executed", "error", "timeout",
        ):
            raise ValueError(f"Unknown journal status: {case_id}")
        done[case_id] = row
    return done


def _execute(binary, attempt, timeout, environment):
    """Run one Rust process and retain complete stdout/stderr on every outcome."""
    proc = subprocess.Popen(
        [str(binary), str(attempt / "input.json")], cwd=attempt,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={**os.environ, **environment}, text=True, start_new_session=True,
    )
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass  # The process exited between the deadline and the kill.
        stdout, stderr = proc.communicate()
        timed_out = True
    (attempt / "stdout.txt").write_text(stdout)
    (attempt / "stderr.txt").write_text(stderr)
    row = {"returncode": proc.returncode, "stdout": bind(attempt / "stdout.txt"),
           "stderr": bind(attempt / "stderr.txt")}
    if timed_out:
        row.update(status="outer_timeout", error="Complete Rust process group killed at outer deadline")
    elif proc.returncode:
        row.update(status="runner_error", error=stderr)
    else:
        try:
            payload = json.loads(stdout)
            result = payload.get("result") if isinstance(payload, dict) else None
            if not isinstance(result, dict) or result.get("status") not in ("executed", "error", "timeout"):
                raise ValueError("Expected result object with executed, error or timeout status")
            row.update(status=result["status"], rust_result=result)
        except ValueError as exc:
            row.update(status="invalid_runner_output", error=str(exc))
    return row


def run(catalog_path, binary, output, *, timeout=25, environment=None, supporting_files=()):
    catalog_path, binary, output = (Path(p).resolve() for p in (catalog_path, binary, output))
    catalog = load(catalog_path)
    functions = [r for r in catalog if r["kind"] == "function_reference"]
    if any(not isinstance(r.get("api"), str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", r["api"]) for r in functions):
        raise ValueError("Unsafe or missing SQL API name")
    if len({r["api"] for r in functions}) != len(functions):
        raise ValueError("Duplicate API names")
    expected_cases = {
        f"{entry['api']}__{index:03d}": (entry["api"], index)
        for entry in functions for index, _ in enumerate(entry["examples"], 1)
    }
    output.mkdir(parents=True, exist_ok=True)
    with (output / "run.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        environment = dict(environment or {})
        identity = {"catalog": bind(catalog_path), "binary": bind(binary), "outer_timeout_s": timeout,
                    "driver_sha256": file_hash(__file__), "environment": environment,
                    "supporting_files": [bind(p) for p in supporting_files],
                    "method": "each documentation SQL block, fresh Rust process, all returned frames materialized",
                    "network_examples": "deferred_explicitly", "semantic_oracle": "absent", "llm_calls": 0}
        fingerprint = digest(identity)
        identity_path = output / "identity.json"
        if identity_path.exists() and load(identity_path)["fingerprint"] != fingerprint:
            raise ValueError("Different input/runner identity; use a new output directory")
        journal = output / "results.jsonl"
        done = _resume_records(journal, fingerprint, expected_cases)
        save(identity_path, {"fingerprint": fingerprint, **identity})
        for entry in functions:
            for index, sql in enumerate(entry["examples"]):
                case_id = entry["api"] + "__" + str(index + 1).zfill(3)
                if case_id in done:
                    continue
                case = output / "cases" / case_id
                # Interrupted work is retained, with a new attempt namespace.
                previous = [int(p.name.removeprefix("attempt_")) for p in case.glob("attempt_*")
                            if p.name.removeprefix("attempt_").isdigit()]
                attempt = case / f"attempt_{max(previous, default=0) + 1:03d}"
                attempt.mkdir(parents=True, exist_ok=False)
                inp = {"api": entry["api"], "example_index": index + 1, "sql": sql}
                save(attempt / "input.json", inp)
                (attempt / "original.sql").write_text(sql)
                row = {"case_id": case_id, "api": entry["api"], "example_index": index + 1,
                       "fingerprint": fingerprint, "input": bind(attempt / "input.json"),
                       "target_mentioned": bool(re.search(r"\b" + re.escape(entry["api"]) + r"\s*\(", sql, re.I)),
                       "semantic_correctness_verified": False, "llm_calls": 0}
                start = time.monotonic()
                if re.search(r"https?://|s3://|gs://", sql, re.I):
                    row.update(status="external_fixture_pending", error="Remote fixture must be downloaded/pinned before measured use")
                elif not re.match(r"\s*(?:--[^\n]*\n\s*)*(?:SELECT|WITH|VALUES|EXPLAIN)\b", sql, re.I):
                    row.update(status="statement_review_required", error="Non-query statement requires its setup/side-effect contract")
                else:
                    row.update(_execute(binary, attempt, timeout, environment))
                row["wall_s"] = time.monotonic() - start
                save(attempt / "result.json", row)
                with journal.open("a") as f:
                    f.write(json.dumps(row) + "\n")
                    f.flush()
                    os.fsync(f.fileno())
                done[case_id] = row
                if len(done) % 40 == 0:
                    print(json.dumps({"completed_example_records": len(done), "statuses": dict(Counter(r["status"] for r in done.values()))}), flush=True)
        per_api = []
        for entry in functions:
            rows = [r for r in done.values() if r["api"] == entry["api"]]
            n, ok = len(entry["examples"]), sum(r["status"] == "executed" for r in rows)
            status = "no_sql_examples" if n == 0 else "all_examples_executed" if ok == n else "some_examples_executed" if ok else "no_example_executed_successfully"
            per_api.append({"api": entry["api"], "examples": n, "executed": ok, "status": status,
                            "example_statuses": dict(Counter(r["status"] for r in rows)),
                            "runtime_default": entry["runtime_default"]})
        summary = {"fingerprint": fingerprint, "function_pages": len(functions),
                   "example_blocks": sum(len(r["examples"]) for r in functions),
                   "recorded_examples": len(done), "example_statuses": dict(Counter(r["status"] for r in done.values())),
                   "api_statuses": dict(Counter(r["status"] for r in per_api)),
                   "apis": per_api, "semantic_correctness_verified": False,
                   "llm_calls": 0, "method": identity["method"],
                   "limitations": ["Executed means the documented SQL block materialized without error; it is not a verified numerical answer.",
                                   "Examples may intentionally show errors; an execution error is not automatically a library defect.",
                                   "All 201 function pages remain in the API inventory, including unavailable/default-feature and no-example cases.",
                                   "Remote examples are deferred explicitly; no live network input enters this run.",
                                   "Individual blocks do not inherit setup from another example. Errors preserve missing-setup evidence."]}
        save(output / "summary.json", summary)
        return summary
