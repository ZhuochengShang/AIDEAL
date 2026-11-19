# AIDEAL execution and paper checklist

Observed November 19, 2026 at 09:24:19 Pacific. [Detailed follow-through](../../review/followthrough-2026-11-19/README.md). Snapshots do not update automatically.

## Current result

All 14 current R0 arms are complete. These are native acceptance measurements with model-written assertions, one trial and zero repairs; independent micro/puzzle accuracy remains pending.

| Bank | Targets | Original R0 | Existing D1 R0 |
|---|---:|---:|---:|
| RDPro Scala | 261 | 20/261 (7.7%) | 14/261 (5.4%) |
| RDPro Java | 69 | 12/69 (17.4%) | 4/69 (5.8%) |
| MDAnalysis | 1,519 | 592/1519 (39.0%) | 621/1519 (40.9%) |
| tslearn | 354 | 211/354 (59.6%) | 221/354 (62.4%) |
| mir_eval | 178 | 134/178 (75.3%) | 144/178 (80.9%) |
| Thumbnailator | 225 | 109/225 (48.4%) | 97/225 (43.1%) |
| SedonaDB | 217 | 87/217 (40.1%) | 96/217 (44.2%) |

## Work and acceptance gates

| Status | Work | Evidence or next acceptance condition |
|---|---|---|
| Complete | Frozen current Original/D1 R0 | 5,646 outcomes and14 bound completion/result receipts |
| Complete | R0 attempt and resource audit | 5,647 attempts; one unknown-usage 503 retained explicitly |
| Complete | Historical MDAnalysis Original replay recovery | 1538/1538 programs; no model calls; 13,847 unique evidence files verified |
| Complete | Other historical replay arms | 13 bound results; kept separate from current R0 |
| Deployed for isolated replay | Binary diagnostic recording | 19 cluster tests + 7 subtests; 3 real preflight verdicts |
| Development tests passed | Exact-owner author comments/test excerpts | Review all-library coverage and allowed source-test scope; execute README examples |
| Development tests passed | Eight-condition routing and alias controls | Freeze and validate actual library treatments and independent banks |
| Still required | D1 claims and examples | Validate constructors, signatures, receivers, outputs and behavioral claims |
| Still required | Fixed micro/puzzle tasks | Independent expected outputs and reference/wrong-output/no-target controls |
| Still required | Alias and native hint builds | Per-alias forwarding/default/error tests and native exception message comparisons |
| Still required | Memory isolation | Verify actual repair backend exposure; no cross-trial or cross-condition history |
| Not launched | R1/R2 and D2 | Preceding gates must pass; keep development and held-out evaluation separate |
| Preserved limitation | Four Scala URI failures; three MDAnalysis mock targets | Correct only in a newly frozen protocol; never rewrite measured denominators |

The complete independent paper study is **not ready**. Software test success does not establish correctness of every installed treatment or of every generated program. AIDEAL failures and model-program failures must remain distinct.

The recovery completed independently on the cluster at 09:15:39 Pacific. Logs and completion receipts are saved; no recovery worker remains active and no unvalidated paid stage started. Local Codex work may pause when the laptop sleeps.

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
