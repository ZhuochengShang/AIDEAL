# AIDEAL execution and paper checklist

Observed **19 November 2026, 00:18:42 Pacific** (**19 November, 08:18:42 UTC**). This is a timestamped review, not a live monitor. The active namespace is `evaluator-correction-2026-11-18/explicit-inputs-r0`. Preserve older namespaces and their measured results.

## Current execution

The active controller and MDAnalysis worker were alive. **13 of 14 condition runs are complete.** The current run uses `gemini-3.1-flash-lite`, one initial audience program per selected API, zero program repairs and the existing generated README D1. D1 authoring and D2 revision do not run in this queue.

| Bank | Selected APIs | Original R0 accepted | Generated D1 R0 accepted | Status |
|---|---:|---:|---:|---|
| RDPro Java | 69 | 12 | 4 | Both complete |
| RDPro Scala | 261 | 20 | 14 | Both complete; shared URI issue limits interpretation |
| SedonaDB | 217 | 87 | 96 | Both complete |
| MDAnalysis | 1,519 | 592 | Pending | D1 running |
| tslearn | 354 | 211 | 221 | Both complete |
| mir_eval | 178 | 134 | 144 | Both complete |
| Thumbnailator | 225 | 109 | 97 | Both complete |

At this observation, the MDAnalysis D1 checkpoint contained **602 unique targets with recorded outcomes**, including 253 accepted programs. Its final percentage remains **Pending**. There were 603 returned provider receipts because the next target was in progress. One earlier 503 receipt remains preserved. The checkpoint has 603 rows because the failed provider attempt and its later retry refer to the same target. Do not equate checkpoint rows, provider requests and unique completed target outcomes.

Across the study, **4,729 of 5,646 planned target outcomes** had been recorded at this snapshot. The earlier 503 was a temporary capacity response, not evidence of depleted credits. Resume preserved completed tasks and created a new physical attempt for the interrupted request. A provider retry stays logical R0.

## End-to-end audit on November 19

**The complete paper study is not ready.** The current native R0 queue is active. The [detailed audit](../../review/audits/2026-11-19/README.md) traces the inputs, code functions, checks and output evidence at each stage. The [action ledger](../../review/audits/2026-11-19/ACTIONS.json) records completion criteria.

Development fixes address provider-response recovery, selected-condition scope, cumulative retry resources, transport-identity reuse, output URI/path wording and import-failure-only empty API stubs. These fixes do not alter the active frozen release or existing scores. The current MDAnalysis bank retains its1,519 denominator; three conditional mock classes are a disclosed scope limitation.

Before the full study, complete the qualified README evidence and example validation, independent micro/puzzle banks, eight-condition support, alias behavior admission, versioned native-hint builds and repair-memory isolation. Native retries currently retrieve same-API failures without a run/condition filter. Current R0 does not use that retrieval.

## Completed and remaining work

| Status | Work item | Evidence or completion requirement |
|---|---|---|
| Frozen; scope correction required for a future bank | Freeze 2,823 current API targets | Current ledger retained; three MDAnalysis import-failure mock classes identified in this audit |
| Done | Prepare all seven banks | Bound configuration, source, documentation, fixture and runtime receipts |
| Done | Check matched prompt exposure | Fourteen sampled Original/D1 requests match outside documentation |
| Done | Check execution mechanisms | Enabled JVM assertions, isolated attempt outputs, Python fixture binding and exact target witness |
| Done | Preserve prior runs | Historical results and the stopped initial run remain separate from current results |
| Done | Complete 13 condition runs | Completion receipts and result hashes for all Original arms and six D1 arms |
| Running | Finish MDAnalysis D1 | Native worker running at the timestamp above; require final completion receipt before a final score |
| Queued | Replay saved historical programs | The current controller schedules a separate zero-model `rescore` phase after continuation; do not replace original verdicts |
| Fixed in development; not deployed | Resolve RDPro Scala URI contract | Native contract v3 distinguishes local paths and URIs; a new matched protocol and readiness receipt are still required |
| Review required | Validate existing D1 claims and examples | Check constructors, callable expressions, receivers and behavioral claims against actual source and executable examples |
| Pending | Independent microbenchmark oracles | Fixed task inputs, expected outputs and target-use checks independent of the audience-generated assertions |
| Pending | Fixed puzzle bank for the main comparison | Document task levels, input/output contract, reference checks and development/evaluation separation for all six libraries |
| Pending | Full eight-condition implementation and validation | O, R, A, H, RA, RH, AH and RAH with identical tasks/runtime/repair settings; the current generic runner alone does not establish a complete eight-arm study |
| Pending | R1/R2 measurement | Record initial passes, newly repaired passes per round and cumulative R2 separately; current run has no program repairs |
| Pending | D2 development and fresh evaluation | Diagnose designated development failures after the planned repair rounds, validate the revised README and start fresh audience trials |
| Pending | Validate alias and native hint treatments | Build and paired behavior checks, installed source hashes and branch manifests before audience evaluation |
| Pending | Reconcile historical RDPro 92/171 | The earlier presentation reports this value; the located generated result records 73/171 and the revised README result records 132/171 |
| Done locally; publication recorded separately | Align all “current” entry points | Guide, current-study/current-launch pointers, tracker, review status and start page now use the current cohort; old navigation files are preserved in navigation-history |

## Gates before the next controlled run

1. **Choose and freeze the measurement.** Keep native acceptance separate from independently checked task accuracy. Model-authored assertions and a target marker do not prove that a fixed task was solved correctly.
2. **Freeze a matched task bank.** Retain canonical owners and signatures, data roles, reference programs, independent checks and coverage strata. Keep documented and no-reviewed-excerpt APIs in the bank instead of silently dropping difficult cases.
3. **Resolve confirmed shared setup ambiguities.** RDPro Scala has four recorded URI/path failures across both conditions. Preserve those results and review the common contract before launching a new comparison. Wrong generated API calls are not automatically environment defects.
4. **Validate D1 before treating it as improved documentation.** The current saved authoring pass had no selected test snippets, and all 555 JVM API fact records had null extracted source comments. Those extractor outputs do not prove that the source lacks comments. Corrected future author prompts do not retroactively repair frozen D1.
5. **Keep development evidence separate.** Alias proposals, embedded exception guidance and D2 may use development failures. Do not expose held-out evaluation answers or accumulating cross-trial memory to later evaluation tasks.
6. **Run deterministic positive and negative controls.** Check every configured execution family and fixture format required by the selected tasks. Passing one example per library does not certify every API.
7. **Freeze treatment versions.** Bind source commits, README D0/D1/D2, alias code, native exception-message edits, model settings and permitted context. R0/R1/R2 are attempts inside a condition, not Git branches.
8. **Check reporting arithmetic and completeness.** Use the selected denominator. Separate provider retries, program repairs, documentation revision, model request time and compile/run time. Publish complete arms or explicitly marked partial progress.

## Current interpretation and known issues

- Current native paired results have 118 gained passes and 115 lost passes across 1,304 APIs with both arms complete. These are differences between independently generated R0 programs, not 118 successful repairs.
- RDPro D1 contains confirmed inaccurate constructor guidance for `GeoTiffMetadata.getGeoKey` and an incorrect initial-state claim for `Statistics.isValid`. The audience reproduces those errors in inspected attempts. This does not explain every regression.
- RDPro Scala supplies `output_dir` as a `file:///` URI while the prompt describes only a writable directory. Four inspected traces consume it as an ordinary path. Their original scores remain unchanged.
- The two MDAnalysis D1 `dependency-unverified` rows reviewed at this snapshot use invented module paths, `MDAnalysis.auxiliary.auxreader` and `MDAnalysis.converters.PDBConverter`. Those labels do not establish that an optional dependency is missing. This bounded review found no new confirmed setup blocker.
- The old RDPro bank used 171 bare names and Gemini 3.1 Pro Preview. The current bank has 330 qualified raster/support targets and Gemini 3.1 Flash Lite. Only 48 old names lexically match 58 current qualified targets, with ambiguous owners. Treat these as separate studies.

## Navigation audit

This table records the stale navigation found before the refresh. The guide, pointers and review snapshots have now been updated locally, with all replaced versions preserved in [navigation history](navigation-history/). No immutable experiment evidence was changed. Publication and cluster synchronization have their own receipt.

| File | Stale or conflicting content observed | Needed update |
|---|---|---|
| `EXPERIMENT_GUIDE.md`, section 1 | Queued banks, mir_eval 41 responses, Thumbnailator 39 responses and “no completed bank score” | Replace the stage column with the timestamped current completion table |
| `EXPERIMENT_GUIDE.md`, section 2 | Paid execution row still reports 80 responses | Use the same snapshot and distinguish current execution from sampled readiness checks |
| `CURRENT_STUDY.json` | 2,850 targets, earlier evaluator and earlier ablation state | Preserve prior state as history and expose the corrected current namespace/count/release |
| `CURRENT_LAUNCH.json` | 5,307 targets and an old launch PID | Mark this historical and point navigation to the active corrected launch |
| `review/EXPERIMENT_TRACKER.json` | 5,307 targets and `OFFLINE_VALIDATED_REVIEW_HOLD` | Keep this as an older preparation record or add an explicit superseded marker/current link |
| `evaluator-correction-2026-11-18/REVIEW_STATUS.json` | 80 responses and zero complete banks at 00:10 UTC | Refresh the navigation snapshot without changing readiness or measurement receipts |
| `AIDEAL_workflow/docs/CURRENT_STATUS.md` | September 21 Codex pilot presented as current | Retain the pilot under historical results and link the current six-library study |

## Where to inspect evidence

- [Meeting report](MEETING_REPORT.md) explains methods, all library results, historical counts and code review starting lines.
- [Frozen result snapshot](evidence/CURRENT_RESULTS.json) contains exact per-arm result paths and hashes. It is the earlier 23:44:56 Pacific meeting snapshot, so MDAnalysis progress differs from the live check above.
- [Current API identity bank](../../evaluator-correction-2026-11-18/review/final-scope/SELECTED_API_BANK.tsv) lists the 2,823 selected targets. This is a native API target bank, not a completed independently scored puzzle bank.
- [Recorded native execution progress](../../evaluator-correction-2026-11-18/review/run-checks/PROGRESS.md) preserves the result interpretation and provider resume history.
- [Six real usage-test examples](real_examples/EXAMPLES.md) link exact saved prompts, code, inputs and outputs for all six libraries. These are native usage probes; independent task oracles remain pending.
- [RDPro failure audit](evidence/RDPRO_FAILURE_AUDIT.json) links exact source, prompt and failure receipts.
- [Historical result provenance](evidence/HISTORICAL_171_RECORDS.json) and [API overlap audit](evidence/HISTORICAL_API_OVERLAP.json) support the old/new count distinction.

Cluster active root: `/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/explicit-inputs-r0/`.

Use `continuation/<bank>/<condition>/configs/continuation.yaml` for the effective condition configuration, `inputs/` for its bound bank/resources, `execution/` for per-target attempts, and `completion.json` plus `result.json` for completed results. Read the full saved `request.json`, `response.txt`, executable program, `execution.json`, `stdout.txt` and `stderr.txt` when auditing a task. A stale status file does not prove a worker is stopped.

This review made no provider calls, changed no frozen input or output, and did not restart the controller.
