# Read-only test-bank catalog — 2026-11-17

This snapshot retains existing evidence. It starts no models, executions or repairs and changes no bank files. Root owns the separate source-versus-original-document coverage export.

## Viewer payloads

- `native_tasks.json`: six current frozen native manifests, **1,806 tasks**, one saved R0 attempt each. Full delivered system/user request, full response, candidate program, stdout/stderr, source artifacts/hashes and native result records. The only deliberate omission is the large repeated execution command: its original file path, character count and command hash remain. File is about44MB; use an external data script or lazy data load rather than duplicate it in HTML.
- `historical_tasks.json`: **18 bank entries and236 task/design records**. Includes seven empty drafts,161 placeholder targets without prompts, five further draft puzzle candidates and eight task-family designs. These records are searchable but must never be counted as completed evaluation tasks.
- `sql_replay_tasks.json`: **322 historical Sedona SQL examples**, each with three archived setup-variant executions. Source baseline59ec34c differs from the current official0.5.0 native registry. Final configured variant executed320 and errored2. This is execution replay without an independent semantic oracle, not audience-generated microbenchmark evidence.
- `private_oracles.review-only.json`: **separate reviewer-only material**: held-out expected values, reference programs and wrong-output/no-target controls. Do not embed in the public task viewer, audience prompt payload, documentation generation or future blind evaluation context. Public records reference it through `private_review_id`; expected answers remain sequestered.
- `catalog_validation.json`, `secret_pattern_audit.json`: count/identity/artifact checks and zero matches for high-confidence credential formats. No key files were read. Credential pattern checks are not proof against arbitrary secret formats.

All three viewer payloads use top-level `banks[]` and `tasks[]`. Stable join keys are `task_id` and `bank_id`; coverage can join current native tasks on `(library,api)`. Native level is `native-single-api`; source paths are absolute original artifact paths and are not assumed to exist on a viewer machine.

## Current native scope

|Library|Frozen tasks|Raw native passes|Raw native failures|
|---|---:|---:|---:|
|RDPro|16|1|15|
|MDAnalysis|1032|265|767|
|tslearn|235|81|154|
|mir_eval|148|30|118|
|Thumbnailator|149|53|96|
|SedonaDB|226|88|138|

Native pass means the configured execution/assertion-marker gate passed. Expected values were written by the audience; this is not independent semantic validation. Raw counts include infrastructure outcomes among failures; the retained result summary separately preserves infrastructure-adjusted metrics. Every task has its actual delivered documentation context, so source-only targets with no retrieved original section remain visible.

## Historical bank families

|Bank family|Unique cases/designs|State and evidence boundary|
|---|---:|---|
|RDPro broad bank|32 (16micro+16puzzle),96fixture instances|Existing independent expected-value algorithms and reference/wrong-output/no-target controls; current bank SHA matches validation report. Historical five-arm report has3trials per case:480 condition-case-trial units, not480 unique cases.|
|RDPro schema/metadata bank|8 (4micro+4puzzle),24fixture instances|Existing independent controls; bank SHA matches validation report. Separate historical Codex pilot:40 condition-case units.|
|RDPro source-contract development|8micro|Explicit development-only, not evaluation results.|
|RDPro draft candidates|166 (161micro+5puzzle)|Explicit `draft_not_evaluable`;161micro rows have null prompts and pending oracles.|
|RDPro legacy puzzle bank|5|Composition/discovery definitions,28 byte-identical copies grouped. No semantic completion claim.|
|RDPro alias puzzle bank|5|Prepared historical puzzle definitions and expected-output references; fresh validation not established in this audit.|
|Portable pilots|1 each for MDAnalysis,tslearn,mir_eval,Thumbnailator|Four adapter-validation banks with independent comparator definitions and tiny inputs; no completed multi-library audience study evidenced here. Two presentation modes are not two unique tasks.|
|Domain task families|8design records,5declared levels|Planning/design inventory; not eight executable tasks.|
|Empty draft files|7files,0cases|Retained as empty per-library/study entries.|

Historical reported validation is not a new execution of controls. Reports retain their original scope/limitations; observed target method-entry unions do not prove causal use per fixture. Different models, library revisions, task denominators, fixtures and repair budgets must not be pooled as a matched comparison.

## Renderer field guide

Native task: `task_id, bank_id, library, api, target_apis, level, condition, round_budget, status, diagnostic, tokens, document, attempts, original_artifact_path`.

Native attempt: `request.data.system`, `request.data.user`, `response.text`, `candidate_programs[].text`, `stdout.text`, `stderr.text`, `provider.data`, `execution.data`, plus artifact path/hash/size. All these contents are retained in full.

Historical task: `task_text`, `public_context`, `composition_goal`, `requirements`, `public_task_record`, `input_artifacts`, `record_kind`, `status`, `oracle_status`, `private_review_id`. Discovery mode must not receive hidden `target_apis`/composition goals merely because the reviewer can inspect them.

Replay task: `task_text` is original SQL. `attempts[]` has `variant`, original SQL, executed input, stdout/stderr and recorded result. Use final status only as execution status, not correctness.

Recommended filters: library, bank/study, level, state, native status/error category, source/document coverage, API name and full-text search. Show empty banks in the bank list even though they have no case rows. Render untrusted captured text using text nodes/preformatted text, never HTML interpretation. Do not silently turn missing fields or null task text into success/ready states.

## Reuse

`export_remote_native.py` reads only the authorized current study and prints one JSON document. It refuses export when a high-confidence credential format is detected. Run through the existing SSH connection and redirect stdout to a new local snapshot; it writes nothing remotely.

`normalize_historical.py` uses `discovery_files.json` to regroup byte-identical local bank files and produce public/private outputs. `export_sql_replay.py` reads the three archived tar files without extracting or modifying them. `validate_catalog.py` checks identities/counts/artifact completeness and rescans all exported JSON for credential formats.

Discovery covers named bank files across local geoAI repositories, with ignored/hidden bank search additionally performed under AIDEAL_WORKSPACE/03_Experiments and the portable pilots. It is not an inventory of every upstream unit-test function, every historical micro execution ledger or undocumented ad hoc tests. Source repository files and all experiment evidence remain untouched.
