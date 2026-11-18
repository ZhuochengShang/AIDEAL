# Readiness fixes and current limits

**Status: offline integration verified; inputs ready for review; live authoring/evaluation held.** This report describes code and input repairs. It does not certify that all studies have run, all scientific protocols are complete, or all bugs/wrappers have been eliminated.

[Experiment guide](EXPERIMENT_GUIDE.html) · [All API/task inputs](review/qualified-bank/INDEX.html) · [Tracker](review/EXPERIMENT_TRACKER.html) · [Historical evidence](HISTORY.md)

## Concrete defects addressed

| Defect | Replacement behavior | Recorded evidence |
|---|---|---|
| Global short-name selection merged unrelated owners | Stable defining API identity; maximum arity only within the same owner/API; proven Scala companion kinds remain distinct | Selected-site receipt and exact identity lists |
| Python-only source scan missed Cython and public exposure relationships | Source/public exposure ledger includes source language, defining owner, alias/inheritance relationships and visible unresolved cases | Final six-library ledgers and reader validation |
| Unresolved classification was treated as a reason to discard an API | Unknown body classification remains a review note; established singleton callable with unknown arity remains visibly unknown | Per-site disposition and arity metadata |
| README generation, catalogue and repair used bare-name lookup | Exact identity persists through headings, requests, completion, catalogue, retrieval, repair and deep-dive artifacts | Qualified identity regression and integrated pipeline receipts |
| A complete-looking existing README could bypass current source/document identity checks | Qualified generation requires forced regeneration or fingerprint-validated resume; inspection remains read-only | Direct-command refusal and resume regression |
| Broad original-doc globs admitted dataset payloads/stubs and missing files were skipped | Reviewed source-bound manifest declares every corpus/excerpt file; hashes and UTF-8 payloads checked; missing input fails | Document manifests and payload validation |
| Distillation silently discarded the corpus tail | Deterministic recorded chunks cover all characters; exact target excerpts remain complete; cache binds model/messages/manifest | Chunk receipt and full-tail regression |
| Original retrieval credited same-named APIs or silently cut text | Exact qualified mappings plus explicitly declared shared README; no shared-text coverage credit; explicit undocumented/unresolved dispositions; budget overflow is an error | Source/document crosswalk and retrieval tests |
| Runtime adapter inferred target from its folder name | Safe storage key plus explicit `requested_target.json`; requested identity is fingerprinted separately | Adapter integration and native request tests |
| Private defining module could lose its verified public re-export | Keep defining identity and expose verified public access paths to author and audience | Exposure-resolution evidence and regression |

The old source filters, reduced bank and historical documents remain frozen as their own cohorts. Their omissions are not retrospectively relabeled as valid wrapper removal.

## Input provenance and fairness

Original default context is the pinned top-level README verbatim, followed by the reviewed exact API excerpt or an explicit no-excerpt note. The same shared-README rule applies to all six libraries. Shared text has no effect on exact API-documentation coverage status; other setup pages are not added implicitly. The author sees the whole reviewed corpus through distillation plus complete target excerpts. Full-document audience mode is a different explicitly frozen exposure setting.

Beast payload preparation verified 21 tracked documents. Thumbnailator preparation verified 83 content documents and 349 declared member anchors against official 0.4.21 Javadoc provenance. Sedona preparation verified 214 tracked documents. These are corpus/member counts, not final selected or documented target counts. Python documentation consists of 265 version-checked API pages plus three pinned repository READMEs; the qualified target mapping is validated separately from these page counts.

## Validation evidence and remaining gates

| Item | Current status |
|---|---|
| Qualified README/document code contracts | 75 offline tests passed, including 33 new contracts; model/process boundaries mocked |
| Original corpus and exact target mappings | All 5,307 target contexts load; 1,903 have exact mapped excerpts and 3,404 have no exact mapped excerpt; shared README text earns no coverage credit |
| Full integrated regression | [Final checks](review/qualified-checks/FINAL_VALIDATION.json) — 684 tests and 365 subtests passed on both Mac and lab cluster |
| Final staged selection counts | 5,307 identities; counts/selected IDs/document dispositions agree with the final inventory receipts; user approval remains separate |
| Final evaluator release | `evaluator-qualified/` · `2026-11-17-qualified-api-f3c6fd6fe802` · `f3c6fd6fe802716592df2d1342fc1b5bc9de5ca372aac880c196a240b2cb1838`; prior evaluator preserved |
| Current cluster preflight | `review/qualified-checks/preflight/PREFLIGHT.json`; earlier native controls remain separate |
| Current bank/config preparation | 5,307 rows in the browser; seven-bank qualified catalog, 14 held R0/authoring jobs; review-only preparation commands in RUNBOOK.md |
| New owner-qualified live six pilots | Not run; review hold |
| Complete README authoring and Original R0 | Not run; review hold |
| New aliases, embedded hints and Combined installation | Pending development/validation; five branch names alone are not treatment evidence |
| Full matched five-condition micro/puzzle oracle and protocol | Not certified complete |
| Native Mac scientific runtime | Not certified; validated cluster runtime is the intended execution location |
| Local/cluster/GitHub identical final package | Portable package identified by `SYNC_MANIFEST.json`; verify locally and on the cluster; Git study tree carries the same frozen files |

The selected snapshot still carries review limits: Beast has 581 earlier forwarder/wrapper/facade labels plus 951 unresolved-body labels; Thumbnailator has 26 forwarder/wrapper labels plus 69 unresolved-body labels. These retained notes are not a proof of safe wrapper elimination. MDAnalysis/tslearn retain 29/7 unknown-arity singleton APIs and 41/1 unresolved public exposure paths. Sedona retains one dynamic registration boundary. The full ledger records these separately from a resolved within-owner arity election.

The shared-README rule produces maximum target-context sizes of 20,044 / 90,555 / 33,098 / 5,258 / 15,446 / 16,642 characters for Beast / MDAnalysis / tslearn / mir_eval / Thumbnailator / Sedona. Forty-one MDAnalysis and seven tslearn targets exceed 24,000 characters. Final bank configs use explicit adequate limits and all target contexts passed loading; the loader does not silently cut oversized excerpts.

A passing offline test suite establishes the tested contracts. Earlier 25 native expected outcomes establish setup controls, including deliberate failures; they are not 25 measured benchmark successes. Six pilot previews are not six new end-to-end model runs.

## Review decision

Before any paid call, review the final selected identities and exclusions, exact documentation strata, per-library fixtures/scaffolds, pilot prompts, repair policy, scoring/oracle source, output namespace, cost estimate and frozen plan. R0/R1/R2 are separate recorded program attempts. Later deep-dive document changes require a fresh audience evaluation.

The hold remains active. Readiness is a receipt-backed decision about the concrete replacement package, not a claim of complete semantic uniqueness or universal correctness.

## Final repairs and direct review route

| Area | Fix | Source to review |
|---|---|---|
| Original preparation | Copy already-absolute inventory bindings and fingerprint the copy | `scripts/run_original_micro.py`, `prepare` |
| Runtime scope | Compile the two missing Beast owners plus their source dependency into a separate supplemental JAR | [Build evidence](review/qualified-checks/spatialtest/BUILD_RECEIPT.json) |
| Native R0 to embedded hints | Preserve every intake disposition; verify target/prompts/source; distinguish requested API from actual failing function; verify installed Python source mapping | `workflow/native_r0_evidence.py`; [workflow and limits](review/qualified-checks/NATIVE_HINT_INTAKE.md) |
| Output handling | Explicit 8,192-token caps; preserve and reject known incomplete, refused or empty answers before execution | `vendor/aideal_engine/src/aideal/llm.py`; `doc_check_execution.py`; `readme_recording.py` |
| Usage accounting | Mark missing provider usage as unknown instead of treating it as a measured zero | `vendor/aideal_engine/src/aideal/llm.py`, `usage_snapshot` / `usage_delta` |
| Release completeness | Include referenced templates and all offline regression fixtures | [Exact release files](EVALUATOR_RELEASE.json) |

[All six full R0 prompt previews](review/qualified-pilots/INDEX.html) · [Cost scenarios](review/qualified-plan/COST_SCOPE.md). The frozen evaluator contains 270 explicit files. The final combined suite passed on both environments: 684 tests and 365 subtests passed on both Mac and lab cluster. Earlier targeted tests remain separately recorded; they are not added to this count. No new provider or scientific subject run was performed.

The cluster initially exposed a newer OpenAI SDK mock schema and a missing test dependency. The response fixture now includes `cache_write_tokens`, and the test requirements explicitly include pytest. The final identical release passed both environments. See [local log](review/qualified-checks/LOCAL_COMPLETE_TESTS.log) and [cluster log](review/qualified-checks/CLUSTER_COMPLETE_TESTS.log).
