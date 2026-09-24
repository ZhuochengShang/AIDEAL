# Audited README authoring and selective refresh

This path prepares exact authoring requests offline, then runs them through an explicitly configured budgeted provider. It creates documentation candidates, not execution-validated API examples. The new full-pipeline study is prepared offline; these implementation instructions do not claim that its model calls or audience evaluation completed. The earlier completed pilot remains a separate study.

| Stage | Receives | Produces / calls |
| --- | --- | --- |
| Inspect | Immutable base README | Byte offsets and qualified API headings; no model |
| Prepare | Pinned source, explicit definition manifest, base README, frozen context, profile and optional development errors | Exact prompts, input hashes and provider contracts; no model |
| Full authoring | Prepared API facts and bounded source/test/original-doc evidence | One author call per selected API family |
| Refresh | Existing selected entry, the same source facts, optional development errors | One fresh reviewer deep-dive, then one fixer rewrite per selected family |
| Compose | Completed candidates and immutable base | Replaces only selected spans; every other base byte remains unchanged |
| Evaluate | Frozen task bank (public prompts, private checks), candidate documents and independent trusted checker | Separate audience solutions and execution/oracle/reachability results |

“Full” and “selected” describe the explicit manifest selection. No bare-name grouping silently merges different receivers. Scala facts identify the lexical class/object/trait and nested owner; local or unsupported declarations cannot become a qualified README family. Alias/hint previews retain such discovery sites as explicitly unresolved instead of guessing their owner.

## Configure the audited native route

Use a local POSIX environment. Run from the full toolkit checkout, or place its root on `PYTHONPATH`; installing only the native engine does not install the sibling `workflow` package. Install the base requirements, `requirements-openai.txt`, and the native engine if needed. The provider reads only `OPENAI_API_KEY` from the environment.

Native YAML uses `models.registry` and `models.roles`. A registry entry must specify `provider: aideal-codex-audited`, `model: gpt-5.3-codex`, and this exact bridge mapping:

```yaml
models:
  registry:
    author:
      provider: aideal-codex-audited
      model: gpt-5.3-codex
      bridge:
        policy: study-v2
        study_id: your-new-study-identity
        stage: author
        budget_ledger: /absolute/study/development/shared-budget.json
        max_cost_usd: '100'  # Explicit ceiling; choose a smaller cap if appropriate.
        max_output_tokens: 4096
        evidence_dir: /absolute/study/development/provider/author
        controller_sha256:
          workflow/provider_budget.py: REPLACE_WITH_ACTIVE_SHA256
          workflow/openai_codex_adapter.py: REPLACE_WITH_ACTIVE_SHA256
          workflow/native_provider_bridge.py: REPLACE_WITH_ACTIVE_SHA256
          vendor/aideal_engine/src/aideal/llm.py: REPLACE_WITH_ACTIVE_SHA256
          vendor/aideal_engine/src/aideal/config.py: REPLACE_WITH_ACTIVE_SHA256
  roles:
    author: author
```

This is an incomplete example. Obtain the active hash mapping without calling a model:

```sh
python -c 'import json; from workflow.native_provider_bridge import active_controller_hashes; print(json.dumps(active_controller_hashes(), indent=2))'
```

For refresh, add explicit `reviewer` and `fixer` registry/role entries using the same ledger and study policy, but different `stage` labels and `evidence_dir` paths. Their contracts are checked before preparation. Reuse neither an old ledger with changed identity nor a stage directory with changed settings. The bridge reserves before HTTP, records exact prompts/settings/results, requires a complete nonempty answer with settled usage, and never falls back to another provider. See the [provider and budget guide](OPENAI_CODEX_PILOT.md).

## Prepare the exact scope

Use a clean pinned source commit. The manifest contains `schema_version: 1`, `repository`, full `revision`, `mode` (`full` or `refresh`), `cache_policy: isolated_no_legacy_cache`, `entries`, and `selected_ids`. Each entry has a stable qualified `id`, its exact README `heading`, a `{start_byte, end_byte}` span, and one or more exact source `definitions` with `path`, one-based `line`, `name`, `receiver`, and `signature`. Scala definitions also require `owner_kind`; include `owner_path` and `qualified_receiver` as explicit reviewed identities. The authoring guard checks the lexical owner path and qualified-name suffix; it does not independently validate the manifest package prefix. Review that prefix against source declarations. One family cannot merge different files, receivers, owner kinds or methods.

```sh
# Offline inspection/preparation; replace every example path.
python -m workflow.readme_authoring inspect --base /absolute/base.md
python -m workflow.readme_authoring prepare \
  --config /absolute/workspace/configs/aideal.yaml \
  --manifest /absolute/scope.json --base /absolute/base.md \
  --context /absolute/frozen-context.md --output /absolute/new-session
```

The base must already contain the complete qualified heading skeleton. Preparation does not invent scope or silently add sections. For full authoring, prepare a complete skeleton and explicitly select all intended families. A refresh session always uses an explicit immutable generated base. In the prepared three-condition recipe, D1 refreshes selected entries of D0. D2 independently authors the complete inventory again from the same skeleton/facts, then refreshes the same selected entries of that newly authored document. `mode: full` and `mode: refresh` with every ID selected are different procedures; do not interchange them. Exact section offsets can be obtained by inspection and must be reviewed with the definition bindings.

The frozen context file is supplied explicitly; preparation does not call distillation or reuse legacy notes/journals. Source windows include up to 30 preceding and 160 following lines per definition, then the combined source context is capped at 14,000 characters. Existing test examples and original examples are mined as evidence; they are not executed or type-checked here. Optional `--diagnostics` accepts only explicitly identified development records. Never supply held-out answers or audience failures to this stage.

## Run and review candidates

```sh
# This command calls the configured provider. It does not execute the library.
python -m workflow.readme_session --session /absolute/new-session --max-entries 1
```

`--max-entries` processes at most that many entries from the prepared order; it does not alter the selected manifest. Omit it to process all selected entries. Completed phases resume only after their exact provider receipt files, prompt/result linkage and settled budget row validate. A started, failed or uncertain phase stops for explicit reconciliation; it does not automatically retry a possibly charged call.

Each successful entry gets a candidate file. A final `README.md` and `completion.json` appear only when all selected entries complete. Their status is `authored_not_execution_validated`. The session never overwrites the configured native `files.llm_readme`, rewrites the base, or imports old generation/error journals. See [output locations](OUTPUTS.md#audited-readme-sessions) and [readme_session.py](../workflow/readme_session.py).

## Compare the refresh strategies

Use the separate three-document evaluator with `readme_evaluation.design: selective_refresh`:

| Ordered condition | Supplied document |
| --- | --- |
| `Unchanged generated README` | The shared immutable generated base; comparison baseline |
| `Selected API refresh` | That base with only the explicitly selected entries refreshed |
| `Full README refresh` | Fresh full-inventory authoring from the common skeleton/facts, followed by the same selected-entry refresh |

For the prepared broad-study D2 recipe, the two full-author sessions have the same skeleton and saved prompts; the second is a separate generation. The subsequent selected refresh uses its newly generated base. A different recipe such as refreshing every existing entry needs a separately described protocol even if a display label is similar. These are three document conditions on the same backend, not alias/hint treatment branches. The controller validates the explicit names; it does not prove that document provenance matches the descriptions. Bind session/base/completion evidence and record this review in `holdout_review`. Use [the selective-refresh example](../configs/readme_selective_refresh.example.yaml). Omitting `design`, or setting `three_readme`, preserves `Original README`, `Generated README`, `Repaired README`.

Freeze only after all three actual documents, independent bank and checker are ready. Changing controller code, retrieval policy, documents or model configuration requires a new freeze; never rename or rebind old measured records. Shared denominators and paired comparisons use the frozen design order. Authoring cost and audience cost are separate ledger records even when they share one overall ceiling.

Review entry points: [preparation](../workflow/readme_authoring.py), [span preservation](../workflow/readme_spans.py), [provider receipt checks](../workflow/readme_receipts.py), [audited bridge](../workflow/native_provider_bridge.py), [design validation](../workflow/evaluation_setup.py). These controls are implemented and tested offline; scientific conclusions require completed independent evaluation.
