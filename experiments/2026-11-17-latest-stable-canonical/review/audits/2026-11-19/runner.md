# Execution, scoring and resume audit

Audited the current development checkout on 2026-11-19. Four reproducible defects were corrected in development. The focused tests pass. This does not establish that arbitrary library programs are correct or that every environment path has been exercised. No paid model requests, frozen-release edits or measured-result edits occurred.

## Findings and changes

| ID | Priority | Finding | Resolution |
|---|---|---|---|
| RUN-01 | P1 | Incomplete, refused and empty provider replies were treated as reusable completed checkpoints. Restart skipped the API while the continuation controller continued to consider the bank incomplete. | Fixed in development. Provider failures remain retryable on an explicit resume. |
| RUN-02 | P1 | `--run --condition original` scheduled both Original and Generated D1. | Fixed in development. The condition filter now limits the actual workers, with tests for both single conditions and the unfiltered default. |
| RUN-03 | P2 | Final target metrics omitted tokens and calls from earlier failed provider attempts after a successful restart. | Fixed in development. A separate cumulative ledger sums every retained new-generation attempt and marks unavailable usage unknown. |
| RUN-04 | P2 | Strict historical-success reuse does not compare the provider transport contract. | Fixed in development. Changed or missing transport contracts now reject historical-success reuse. The current frozen study uses `force_fresh` and never took this path. |

### RUN-01 — retryable provider evidence

The pre-fix helper accepted every matching-fingerprint checkpoint except `llm-error`. The provider adapter separately emits `provider-incomplete-output`, `provider-refused-output` and `provider-empty-output`. These outputs are never executed, but their rows were considered finished on restart.

The fix in `vendor/aideal_engine/src/aideal/doc_check_provenance.py:132` rejects both `llm-error` and all `provider-*` categories. The native loop itself is unchanged. A new provider attempt still carries round 0 and no repair feedback. A repeated bad response stops that explicit invocation; it does not enter an automatic retry loop. The controller's SDK request policy remains separately bounded, and its supervisor does not automatically relaunch an incomplete job.

The new `tests/test_native_checkpoint_recovery.py:22` exercises the actual native loop with synthetic provider/process boundaries. For each of the three categories it verifies:

- An earlier successful API remains reused.
- Each explicit restart makes exactly one new provider call for the failed API.
- Another unusable reply stops without executing a program.
- A successful later response completes at round 0.
- All older request, response, provider and execution files remain byte-identical.
- Restarting a fully completed bank makes no new calls.

All four new regression cases failed before the correction. They pass after it.

### RUN-02 — single-condition launch scope

`run_verified_readme_continuation.py` accepted a `--condition` argument, but its public `--run` path always iterated over both arms. The offline subprocess spy recorded `['original', 'generated_d1']` for an Original-only request.

At `scripts/run_verified_readme_continuation.py:610`, the loop now uses the requested arm when one is supplied. Tests at `tests/test_verified_readme_continuation.py:287` verify Original only, D1 only and both arms by default. Preparation may still check both condition configurations; only the requested condition starts a model-backed worker.

### RUN-03 — cumulative resource accounting

The real native loop, with mocked provider usage, produced three returned responses across a truncation and restart. Their saved receipts total 15 input and 6 output tokens. Final target metrics retain the latest resolved outcome for each target, so summing those rows returned only two responses, 10 input and 4 output tokens. The omitted evidence was still on disk.

The new `provider_attempt_ledger` at `scripts/run_verified_readme_continuation.py:396` reads the condition's own `execution/run_*/attempt_*` evidence. It records request and provider bindings, includes rejected responses and prior retries, and adds known execution durations. The continuation writes `provider_attempt_ledger.json`; `costs.new_generation` points to that receipt. Historical generation and saved-program replay remain separate scopes. `final_target_metric_totals` preserves the prior per-target view for diagnosis without treating it as cumulative spending.

The same native-loop reproduction now returns all three responses, 15 input and 6 output tokens. The score and selected denominator do not change. Unit tests also verify interrupted requests, missing usage, repeat reads without double counting, and exclusion of historical/replay folders.

The ledger reports known usage, not an exact invoice. A saved request with no provider receipt may have been billed. Transport failures and hidden SDK retries may lack usage. Such cases set `usage_complete=false`. `request_count` counts retained request records; `llm_calls` counts returned responses reported by usage. Recorded provider and execution intervals are summed separately and do not imply total elapsed wall time. Completion checks reverify the ledger and its bound attempt files.

### RUN-04 — historical transport identity

At `scripts/run_verified_readme_continuation.py:82`, `reuse_reasons` compares source, documents, fixtures, target identities, prompt/profile, interpreter, model, output allowance and runtime receipts. Before this correction it omitted `transport_contract`, which includes adapter/policy hashes and request deadlines.

An offline probe changed `transport_contract.adapter_sha256` while retaining the other proof. The function returned no reuse blockers. The correction adds this component to the strict comparison list. Regression tests now reject changed and missing contracts, while the existing matching-contract test still permits an otherwise verified success. Current `force_fresh` studies do not consume historical passes, so this is not evidence that current R0 results reused incompatible programs.

## Checks that passed

| Step | Inspected implementation | Observed protection |
|---|---|---|
| Preserve historical inputs | `run_verified_readme_continuation.py:68` | Source, documentation, fixture, scaffold, API inventory and target hashes are checked before reviewed overrides, including in force-fresh mode. |
| Select the denominator | `run_verified_readme_continuation.py:204` and `:483` | A revised bank must be a nonempty unique subset with an exact source-backed exclusion audit. The reported denominator is the selected bank, with historical and excluded counts kept separate. |
| Require readiness | `run_evaluator_correction.py:130` | Every selected bank requires positive and deliberate-negative controls, matching runtime receipts and no unresolved setup blocker before model-backed phases. |
| Serialize ownership | `run_evaluator_correction.py:197`; `aideal/execution.py:20` | Controller and native execution locks prevent duplicate writers. An actual filesystem-lock probe rejected a second writer before function entry. An unreconciled child-process guard also blocked execution. |
| Isolate attempts | `aideal/native_execution_contract.py` | Each attempt uses a separate working/output directory; Java assertion enabling, exact target witness matching and failure-marker handling have focused tests. |
| Preserve partial status | `run_verified_readme_continuation.py:501` | A missing target, unresolved provider category or incomplete native run prevents a completion receipt. Partial numeric fractions remain available but must not be presented as completed results. |
| Keep repairs separate | `run_verified_readme_continuation.py:527` | Current continuation requests `max_fix_rounds=0`. Provider resume is a new round-0 generation attempt, not R1 or R2 program repair. |
| Bind compatible checkpoints | `aideal/checkpoint_compatibility.py` | Compatibility records must match current components and their legacy digest; non-allowlisted component differences reject the migration. |

## Scientific and operational limits

The current native verdict at `aideal/native_execution_contract.py:142` checks exit status, configured markers and a nonempty witness for the requested API. The audience writes its own program and assertions. A printed witness is not independent proof of API use or output correctness. Preserve the label **native execution/self-check acceptance**; do not insert these percentages into independent-oracle microbenchmark or puzzle tables.

Native `run.complete` alone is not sufficient when using configurations that continue after provider failures. The continuation aggregate adds a required provider-category check. Reporting tools must use the outer result's completion status.

The current frozen experiment is unchanged. These fixes should enter a new reviewed release and namespace, not be substituted into the running or completed release. Historical cost reports can be reconstructed from saved receipts separately; they have not been silently rewritten here. A retry that never returned usage remains unknown rather than zero-cost.

## Validation and artifacts

Working directory for tests was `/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow`. All test commands used the local `geo_llm_spark` interpreter, `PYTHONDONTWRITEBYTECODE=1` and pytest's cache provider disabled. No API credentials were loaded.

- Initial focused suite: **71 tests and 77 subtests passed**.
- New pre-fix resume regression: **4 cases failed**, demonstrating the bug.
- Final focused suite: **83 tests and 79 subtests passed** in 2.07 seconds, including the concurrently updated native contract tests.
- Native-loop usage probe recovered **3 calls, 15 input tokens and 6 output tokens** across truncation and resume.
- File-lock probe passed for competing writers and unreconciled process evidence.

Exact commands, results, source hashes and priorities are in `runner.json`. The bounded patch relative to the files at the start of this audit is `evidence/aideal-audit-runner-fixes.diff`. Before/after reproduction outputs and the final test log are listed in the JSON.

Files changed by this agent:

1. `vendor/aideal_engine/src/aideal/doc_check_provenance.py`
2. `scripts/run_verified_readme_continuation.py`
3. `tests/test_native_checkpoint_recovery.py`
4. `tests/test_verified_readme_continuation.py`

These files were already outside the tracked baseline in the working checkout, except for the newly created checkpoint regression. The audit did not delete or overwrite unrelated user edits, did not commit or push, and did not touch frozen study outputs.
