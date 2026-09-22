# Recorded five-condition RDPro runner

This standalone wrapper orchestrates the existing reviewed toolkit. It adds no evaluation policy or model provider. It is staged only until the parent reviews and copies it into the toolkit's `scripts/` directory. Keep `main_pipeline.py` and `pipeline_gates.py` together. The main-only scope is 280 README families, one four-entry refresh, four proposal batches and 480 audience units; the additional three-README comparison is excluded.

No provider, Scala compiler or bank check was launched while writing/testing this wrapper. Its regression tests use temporary tiny files and mocked process results. Model-generated shell commands are never executed.

## Commands and directories

Supply all repository locations; the source has no machine-specific path defaults:

```sh
python scripts/main_pipeline.py prepare \
  --engine /path/to/AIDEAL --study /path/to/study \
  --seed-config-dir /path/to/prepared/configs --python /path/to/python
```

Use the same arguments with these stages:

| Stage | Action |
|---|---|
| `prepare` | Copy the seed configurations, pin current controller hashes, prepare exact author requests and original documentation snapshot; no model call |
| `propose` | Run/resume the four proposal batches; may finish before README authoring |
| `source-review` | Invoke the independent helper to validate actual proposal forwarding syntax before authoring |
| `author` | Run the 280-entry author session |
| `refresh` | Verify author completion, calculate fresh spans from actual generated headings, prepare/run the four-entry deep-dive + rewrite session |
| `artifacts` | Reuse completed proposals/README work, combine actual supported proposals and final README, require complete alias interface to fit, write artifact review manifest |
| `install-build --review FILE` | Verify a source/artifact review, install actual treatments and build all five source-bound backends |
| `configure` | Construct and read-validate the five-condition YAML from actual source/build artifacts; no model or control execution |
| `alias-probe` | Prepare and execute independent paired development probes on both installed alias backends |
| `preflight --alias-probes FILE` | Verify independent paired alias probes and positive/negative development hint delivery |
| `freeze` | Recheck gates and run all 480 trusted controls; publish freeze only if valid |
| `publish` | Push/verify five dated source refs atomically to AIDEAL-RDPro, without rewriting existing different refs |
| `run` | Verify/publish/freeze and run/resume 480 audience units; refuse completion if unresolved units remain |
| `status` | Show recorded completed stages and expected result path |
| `advance` | Propose → automatic strict source review → author/refresh → bundle/install/build → automatic paired probes → gates → dated publication → freeze/audience |

All development state is under `STUDY/development/recorded_five_condition_run/`:

- `configs/`: new copied author/proposal settings; original seed files unchanged.
- `prepared.json`: exact immutable configuration/session/script/runtime-dependency bindings. `environment.json` records Python/OS/architecture/SDK and Git identities without hostname or environment variables.
- `telemetry/`: timestamped secret-free snapshots for development and audience scopes separately; never sum overlapping snapshots.
- `authoring/`, `refresh/`: exact saved model prompts, phase receipts, candidate entries, final README and completion receipts.
- `proposals/`: four batch directories and `collection.json`; zero-support batches remain recorded and do not invent a proposal file.
- `bundle/`: complete merged treatment proposal; `artifact_manifest.json` records actual alias target coverage and any untouched targets.
- `provider_evidence/`: author/reviewer/fixer provider records. Proposal records stay inside their batch directories. All paid stages use the existing shared `STUDY/development/shared_budget.json` and its $100 stopping guard.
- `runtime/backends.json`: actual five-arm build mapping.
- `conditions.yaml`, `preflight.json`, `hint_delivery.json`, `frozen/`: real configuration, validation evidence and frozen protocol.
- `events.jsonl`: durable stage-start/failure/completion/wait events with Unix timestamps.
- `stages/STAGE/attempt-NNN/{command.json,stdout.log,stderr.log,process.json}`: complete command logs and duration; `complete.json` binds completed output files.

Audience files go to `STUDY/runs/recorded_five_conditions/`, including `report.json`, `REPORT.md` and every immutable request/code/checker record. The wrapper does not claim an independent final audit or publication; those remain separate parent responsibilities.

Propose first, then author. Their stage locks are independent, so those two processes may run concurrently after `prepare`. For unattended continuation through the actual validation helpers:

```sh
python scripts/main_pipeline.py advance \
  --engine /path/to/AIDEAL --study /path/to/study \
  --seed-config-dir /path/to/prepared/configs --python /path/to/python
```

By default, this invokes the independent source-review helper before spending on long authoring, and the separate paired-probe helper after real treatment builds. It continues only when actual receipts pass. Optional `--review FILE --alias-probes FILE --wait-for-review` can instead wait for named external validation records; time passing is never approval. The user's authorization to install/run already exists. These are implementation validation gates, not additional user-permission requests. Invalid records stop the runner. Without `--wait-for-review`, it returns the necessary next gate. Never launch competing writers to one stage/session or audience run.

## Source review contract

A root-reviewed final manifest can use:

```json
{"status":"validated_for_installation","artifact_manifest":{"path":"...","sha256":"...","bytes":1},"reviewer":"root source review","held_out_bank_used_for_development":false}
```

Alternatively, source review can finish while authoring runs. An automatic strict parser/probe report can be wrapped as:

```json
{"status":"validated_proposal_sources","proposal_bindings":[{"path":".../batch-0001/proposal.json","sha256":"...","bytes":1}],"source_checks":[{"path":".../actual-source-check.json","sha256":"...","bytes":1}],"held_out_bank_used_for_development":false}
```

Include every actual proposal binding, in collection order. The gate verifies source-check hashes and exact proposal provenance, then deterministically binds the final merged artifact manifest. A source-check receipt must reflect real parser/review evidence; this wrapper does not manufacture that evidence. Readme composition is independently protected by its saved completion and span checks.

Aliases need not be generated for every input API: at least one real supported alias is needed for an alias treatment; the manifest records covered and untouched targets. Any alias must name a known target and exist in the saved Scala source. The lexical check is only structural, never a substitute for compilation or runtime probes. No aliases/hints means the intended five-condition design needs review, rather than fabricated treatments.

## Paired alias probe contract

The separate probe producer runs newly authored development examples, never private benchmark fixtures/reference programs. It uses **separate JVMs** for canonical and alias calls. The receipt has:

- `status: verified_alias_behavior`, exact `proposal`, `backends`, `backend_receipts`, and `plan` bindings, and `held_out_bank_used_for_development: false`.
- One row per actual proposed alias **in each of `alias_only` and `combined`**: `arm`, `api`, `alias_name`, exact `alias_event`, exact `canonical_event`, plus bindings for `request`, `process`, `comparison`.
- The request protocol is `independent_development_alias_probe_v1`, with the exact condition backend, one canonical target API and bound program/certificate/trace-policy/plan.
- The process payload records the build/backend hashes, successful execution, paired observations, canonical target reachability, alias-side target reachability, actual alias events and all raw adjudication bindings.
- The comparison binds each run's process/stdout/stderr/trace/classload files. Raw stdout contains exactly one `AIDEAL_DEVELOPMENT_PROBE=` JSON record with mode and a nonempty list of string observations.

The gate reparses those observations, requires equality, checks both the exact canonical and alias events in the **alias-side** trace, and verifies both owners loaded from the bound overlay. Merely seeing the target in the separate canonical run is insufficient. This is finite-input differential evidence, not a proof over every possible input or a causal explanation of later audience outcomes.

## Hint gate and privacy

The actual public-context function is exercised with the four independent development diagnostics. Every emitted hint must match/deliver on at least one applicable diagnostic without clipping. Initial requests, empty-feedback requests and wrong-function requests must deliver no hints. Coverage is recorded; missing hints for some diagnostic APIs are not silently represented as covered. A positive development match does not guarantee that audience errors will match.

Author/proposal phases read only original public source/test/documentation and separate development diagnostics. Only configure/freeze/audience checker phases use the private benchmark. No bank data is copied into development model payloads.

The command wrapper keeps failed attempts; it does not automatically retry a possibly charged provider attempt. Native session receipt validation must reconcile an incomplete phase before further paid execution. Freeze/checker retries reuse only verified evidence. A partial audience report is never marked complete. Changing bound code/config/prompt inputs requires new reviewed preparation rather than overwriting historical evidence.

## Offline tests

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/path/to/AIDEAL \
  python -m unittest discover -s /path/to/orchestration -p test_pipeline.py -v
```

The recorded test run passed 16 tests. This establishes gate behavior on synthetic evidence, not the correctness of future generated wrappers or success of the paid study.

Before audience execution, the runner pushes only clean snapshot ancestry to `study/2026-09-22-gpt-5.3-codex-32tasks/{original,readme-only,alias-only,error-hints-only,combined}` in `ZhuochengShang/AIDEAL-RDPro`. It disables the stalled default credential helper, uses the existing GitHub CLI credential helper, applies a 180-second publication timeout and verifies all remote IDs. Toolkit publication and official-upstream proof are separate root tasks. No force push is used.
