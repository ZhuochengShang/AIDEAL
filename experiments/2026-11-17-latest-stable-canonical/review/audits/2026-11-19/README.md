# AIDEAL end-to-end audit and next actions

Audit date: **19 November 2026**. Live execution snapshot: **00:18:42 Pacific / 08:18:42 UTC**. The live queue can advance after this snapshot.

**Verdict: the current native R0 comparison is operating, but the complete paper experiment is not ready.** Source inspection and offline tests found concrete defects in recovery, condition selection and accounting, plus incomplete evaluation and treatment stages. Passing software tests does not prove every API, generated program or README entry is correct.

The current queue uses the frozen November 18 evaluator. The fixes described below belong to a separately reviewed development version. No measured program, README D1, denominator or running release was rewritten. This audit made no new model requests and did not restart a worker.

## 1. What AIDEAL should do

1. **Select a library version and its public APIs.** Keep the defining owner, public access path and signature. Exclude external inherited APIs and proven wrappers; reduce overloads within an owner. Record original-document coverage separately from source discovery.
2. **Prepare data and execution.** Bind fixture roles, path representations, build tools and exact runtime versions. A known correct program must pass and a deliberately incorrect program must fail.
3. **Develop resources using development evidence.** Generate D1 from source-grounded API facts, diagnose development failures, propose aliases, and add validated guidance to existing exceptions. Categorized and distilled error memory supports this development work.
4. **Freeze the evaluation bank and conditions.** Microbenchmarks and puzzles need fixed inputs and independent checks. Keep held-out evaluation answers and failure history out of resource development. All conditions use the same tasks and execution settings.
5. **Run R0, R1 and R2.** R0 writes the initial program. After a checked failure, the audience uses permitted feedback to repair its own program. Stop after success or the second repair. Library resources remain fixed during these rounds.
6. **Develop and evaluate D2 separately.** After the designated development repair rounds, source diagnosis can revise selected README entries. Freeze D2 and start fresh audience programs. A held-out failure must not become training evidence for its own reevaluation.
7. **Report complete evidence.** Keep micro and puzzle results separate, show newly repaired and cumulative successes, and count all provider attempts in resource use. Preserve old measurements when the protocol changes.

```text
Pinned source + original docs + data/configuration
                         |
              API inventory and coverage
                         |
             Runtime and input-contract controls
                         |
         +---------------+----------------+
         |                                |
 DEVELOPMENT                         HELD-OUT EVALUATION
 Failures + source                   Fixed tasks + independent checks
 Categorize/distill memory           Frozen O/R/A/H/RA/RH/AH/RAH
 Generate/validate D1, A, H           R0 -> failure -> R1 -> failure -> R2
         |                                |
 After development R2                Final outcomes + all attempt costs
 Diagnose/revise D2                   |
         +---- freeze D2 ----> fresh R0/R1/R2 follow-up
```

The current queue covers only **Original and existing D1 at native R0**. It does not run the full diagram. Its audience writes its own example and checks, so its score is native acceptance, not independent task accuracy.

## 2. Current execution and data integrity

- **13/14 bank-condition runs complete**; all seven Original arms and six D1 arms have verified completion records.
- MDAnalysis D1 has **602/1,519 recorded target outcomes**, including **253 accepted so far**. Its final percentage remains Pending.
- Across the queue, **4,729/5,646 planned condition-target outcomes** are recorded. Provider receipts and checkpoint rows are different counts from unique completed targets.
- The controller and worker were alive and held the expected locks. There was no duplicate worker. The earlier retained Gemini 503 remains provider history; the bounded check found no new provider error.
- All **146 deployed release files** match the release manifest and its readiness binding. The same code files match the pinned GitHub tree. The previously published review package also matched local, cluster and GitHub at the audit snapshot.
- Mac and Linux execution environments are not claimed to be identical. The cluster is authoritative for the full current execution evidence.

[Live process, completion, lock and hash evidence](live.json) · [Source-scope findings](fallbacks.json) · [Pre-update synchronization evidence](sync.json)

## 3. Findings and fixes

| ID | Finding | Action in this audit | Active experiment consequence |
|---|---|---|---|
| F1 | Incomplete, refused and empty responses could be treated as completed checkpoint rows on resume | Fixed in development; explicit resume preserves old receipts and retries at logical R0 with a bounded provider sequence | The running frozen release is unchanged; current recorded provider interruption was the older 503 path |
| F2 | `--run --condition original` could schedule both arms | Fixed in development; selected-condition regression verifies only the requested arm is scheduled | Current queue intentionally requested both arms; no claim that it made unintended calls |
| F3 | Final target metrics could omit resources consumed by earlier failed provider attempts | Added a separate cumulative provider-attempt ledger with request/response hashes and missing-usage flags | Existing receipts remain valid; historical resource summaries need a separate reconciliation, not a score rewrite |
| F4 | Scala received a `file:///` output URI without an explicit representation contract | Future native execution contract v3 identifies URI versus local path and supplies generic conversion guidance | Four observed failures stay in current results; changed prompts require a new matched protocol |
| F5 | MDAnalysis bank includes three import-failure-only mock classes that are absent when real dependencies are installed | Confirmed from source and the actual runtime; narrow future inventory guard implemented and tested | All three fail in both arms. Keep current 1,519 denominator; a reviewed future selection would remove them |
| F11 | Historical-success reuse did not compare the provider transport contract | Added strict transport identity comparison in development, including missing-contract rejection | Current cohort uses `force_fresh`, so this did not change its scores |
| F6 | Qualified README generation disables repository test-example mining; JVM compiler facts may have empty descriptions | Traced live code and saved D1 receipts; retained as a required authoring fix | Frozen D1 is not silently regenerated. Missing extracted comments do not mean the source has no comments |
| F7 | Native retries can read same-API failures from other runs and deterministic advice | Confirmed the unscoped retrieval; require per-trial isolation or a frozen development-only memory policy before R1/R2 | Current R0 begins with no previous failures; it is not affected by the retry-memory path |
| F8 | Full eight-condition study is not implemented in the condition schema | Current supported designs remain five-arm, six-arm and refactor-pair; recorded as an implementation requirement | Do not populate the paper's eight-condition cells from the native queue |
| F9 | Alias installation is unvalidated, and native hint installation is not a completed versioned build | Recorded explicit admission requirements for behavior, commits, source hashes and builds | Proposal or installation success is not evidence that a treatment is ready for evaluation |
| F10 | Six-library fixed micro/puzzle banks and independent oracles are incomplete | Recorded a required evaluation gate | Missing integration-task files do not block the native queue, but they block the independent condition workflow |

The three MDAnalysis targets are `MDAnalysis.coordinates.GSD.MockHOOMDTrajectory`, `MDAnalysis.coordinates.H5MD.MockH5pyFile` and `MDAnalysis.coordinates.IMD.MockIMDClient`. They are empty classes inside `except ImportError` handlers. The actual runtime has the corresponding real dependencies and does not define these fallback names. This is a selection issue, not a reason to uninstall working dependencies.

Native hints must reach the audience through an actual exception emitted by the modified library. An internal JSON proposal or a source comment alone does not satisfy this requirement. Some failures, such as calls to nonexistent methods, have no suitable existing exception site and must remain classified as unsupported for automatic embedding.

## 4. Step-by-step review route

Paths below are relative to `AIDEAL_workflow/`. The accompanying audit records give function names and checked line numbers. Start at the controller, then follow a single condition and target into its saved attempt directory.

| Step | Code to inspect | Input → output | Verified boundary or open requirement |
|---|---|---|---|
| 1. Select APIs | `vendor/aideal_engine/src/aideal/api_public_inventory.py`, `api_canonical_selection.py` | Pinned source + selection rules → qualified target manifest and exclusion ledger | Keep owners distinct; same-name overload reduction is within an owner; conditional stub issue found |
| 2. Original-doc mapping | `api_public_inventory.py::reconcile_documentation` | Reviewed document corpus + target IDs → exact coverage matches | A match is not proof of complete or correct documentation |
| 3. README authoring | `readme_generation.py::find_or_create` | API facts + configured author context → D1 entries and model receipts | Qualified test mining and JVM descriptions need improvement; validate examples before revision |
| 4. Check deployment | `scripts/run_evaluator_correction.py::verify_release`, `verify_readiness` | Release manifest + runtime/control receipts → permission to launch | Hash checks and positive/negative controls pass for audited inputs; not proof of every API setup |
| 5. Prepare conditions | `scripts/run_verified_readme_continuation.py::prepare` | Original/D1 specs + frozen manifests + input bundle → separate condition configs | Reuse requires matching identities; changed protocol requires new namespace |
| 6. Generate a native program | `doc_check_execution.py::_comprehension_execute` | Target declaration + condition docs + shared scaffold/input contract → saved request and response | This is audience program generation, not README generation; R0 uses no prior failure feedback |
| 7. Execute and check | `native_execution_contract.py`, `doc_check_execution.py` | Complete program → isolated build/run, stdout/stderr, exit status and witness | JVM assertions enabled; target marker alone is not an independent correctness oracle |
| 8. Resume and account | `doc_check_provenance.py::_checkpoint_row_reusable`, continuation aggregation | Saved attempts + current identity → reused results, explicit retries and cumulative resources | Future fixes preserve all evidence and distinguish provider retry from R1/R2 |
| 9. Independent repair loop | `workflow/evaluation_runner.py::run_unit`, `evaluation_context.py::public_context` | Frozen task + permitted docs + previous public failure → R0/R1/R2 | Use this controlled context policy; do not simply turn up repairs in the historical native path |
| 10. Aliases | `workflow/improvement_context.py`, `improvement_suggestions.py` | Development evidence + selected definitions → forwarding proposals and exact requests | Names/targets checked; build and forwarding/default/result/error equivalence still required |
| 11. Embedded hints | `workflow/native_hints.py::prepare_native_hints`, `validate_native_hints`, `install_native_hints` | Supported existing exception + proposed guidance → validated source edit | Four programs run against original/modified code; unsupported syntax is rejected; installation still needs commit/build routing |
| 12. Freeze and report | `workflow/evaluation_freeze.py`, `evaluation_report.py` | Tasks, treatments and controls → frozen study and per-round results | Missing banks fail closed here. Eight-factor support and per-alias behavior admission remain pending |

For a real target, inspect its `request.json`, raw `response.txt`, generated program, `execution_contract.json`, `execution.json`, `stdout.txt`, `stderr.txt` and `provider.json`. Then follow its result row to the condition completion receipt. [Six saved examples](../../../reports/2026-11-18-professor-meeting/real_examples/EXAMPLES.md) show these actual files; they are not fabricated demonstrations.

## 5. What must happen next

| Priority | Task | Completion criterion | State |
|---|---|---|---|
| 1 | Finish current MDAnalysis D1 and queued replay | Complete target reconciliation and bound result/completion files; preserve current denominator | Running / queued |
| 2 | Review and promote the development fixes | New release identity, offline tests, new readiness controls and explicit protocol/version receipts | Development review; not active |
| 3 | Repair qualified authoring evidence | Owner-qualified tests and source comments appear in saved author requests with exact source spans | Pending |
| 4 | Validate D1 and define D2 development evidence | Executable examples and source claims checked; no held-out answers used | Pending |
| 5 | Build fixed micro and puzzle banks | Reference program passes; wrong output and missing target use fail; task data and coverage strata recorded | Pending |
| 6 | Complete treatments and the eight-condition matrix | Validated alias and native-hint versions, identical artifact reuse in combinations, backend/build receipts | Pending |
| 7 | Isolate memory and run R0/R1/R2 | Same repair policy, frozen resources and no cross-condition/trial history leakage | Pending |
| 8 | Develop D2 after the designated development rounds | Revised README passes checks and starts fresh evaluation sessions | Pending |
| 9 | Reconcile costs and update paper | Every attempted call accounted for or explicitly unknown; independent results remain separate from native acceptance | Pending |

The tracker records these as specific open items. The paper's planned experiment must remain labelled pending until these gates pass. The earlier 92/171 RDPro claim also remains unreconciled and must not be promoted to a verified measurement.

## 6. Scope of verification

The audit combines source review, frozen artifact hashes, read-only cluster state, and focused offline tests. It exercises real Java assertion rejection and isolated Python execution, with synthetic model responses for generation/recovery tests. These checks do not certify all optional external-tool APIs or the scientific correctness of model-authored tests.

[Development-path audit](development.md) · [Execution/recovery audit](runner.md) · [Test commands and results](CHECKS.json) · [Action ledger](ACTIONS.json)

## 7. Publication and deployment

The reviewed candidate is published on `development/2026-11-19-evaluation-audit`. It is not an active evaluator release. The running queue remains pinned to `2026-11-18-corrected-r0-d8ba3815cf95`. Study documentation is published separately on `study/2026-11-17-latest-stable-canonical`. Promotion requires a new release manifest, updated preparation and controls, and a separately recorded protocol; copying new source into a running release is not a promotion procedure.

The publication receipt records the exact branch heads, file hashes and cluster review location. The final verification does not claim that a new paid experiment was launched.

## 8. Exact code starting lines

| File and function | Start line |
|---|---:|
| [vendor/aideal_engine/src/aideal/api_public_inventory.py::scan_python_surface](https://github.com/ZhuochengShang/AIDEAL/blob/development/2026-11-19-evaluation-audit/vendor/aideal_engine/src/aideal/api_public_inventory.py#L329) | 329 |
| [vendor/aideal_engine/src/aideal/api_public_inventory.py::reconcile_documentation](https://github.com/ZhuochengShang/AIDEAL/blob/development/2026-11-19-evaluation-audit/vendor/aideal_engine/src/aideal/api_public_inventory.py#L652) | 652 |
| [vendor/aideal_engine/src/aideal/readme_generation.py::find_or_create](https://github.com/ZhuochengShang/AIDEAL/blob/development/2026-11-19-evaluation-audit/vendor/aideal_engine/src/aideal/readme_generation.py#L133) | 133 |
| [scripts/run_evaluator_correction.py::verify_readiness](https://github.com/ZhuochengShang/AIDEAL/blob/development/2026-11-19-evaluation-audit/scripts/run_evaluator_correction.py#L130) | 130 |
| [scripts/run_verified_readme_continuation.py::prepare](https://github.com/ZhuochengShang/AIDEAL/blob/development/2026-11-19-evaluation-audit/scripts/run_verified_readme_continuation.py#L256) | 256 |
| [vendor/aideal_engine/src/aideal/doc_check_execution.py::_comprehension_execute](https://github.com/ZhuochengShang/AIDEAL/blob/development/2026-11-19-evaluation-audit/vendor/aideal_engine/src/aideal/doc_check_execution.py#L133) | 133 |
| [vendor/aideal_engine/src/aideal/native_execution_contract.py::native_check_passed](https://github.com/ZhuochengShang/AIDEAL/blob/development/2026-11-19-evaluation-audit/vendor/aideal_engine/src/aideal/native_execution_contract.py#L142) | 142 |
| [vendor/aideal_engine/src/aideal/doc_check_provenance.py::_checkpoint_row_reusable](https://github.com/ZhuochengShang/AIDEAL/blob/development/2026-11-19-evaluation-audit/vendor/aideal_engine/src/aideal/doc_check_provenance.py#L132) | 132 |
| [scripts/run_verified_readme_continuation.py::provider_attempt_ledger](https://github.com/ZhuochengShang/AIDEAL/blob/development/2026-11-19-evaluation-audit/scripts/run_verified_readme_continuation.py#L396) | 396 |
| [workflow/evaluation_runner.py::run_unit](https://github.com/ZhuochengShang/AIDEAL/blob/development/2026-11-19-evaluation-audit/workflow/evaluation_runner.py#L78) | 78 |
| [workflow/evaluation_context.py::public_context](https://github.com/ZhuochengShang/AIDEAL/blob/development/2026-11-19-evaluation-audit/workflow/evaluation_context.py#L10) | 10 |
| [workflow/native_hints.py::validate_native_hints](https://github.com/ZhuochengShang/AIDEAL/blob/development/2026-11-19-evaluation-audit/workflow/native_hints.py#L348) | 348 |
