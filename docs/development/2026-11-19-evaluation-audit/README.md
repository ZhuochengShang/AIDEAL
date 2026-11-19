# Reviewed evaluation fixes, 19 November 2026

This branch contains reviewed development changes. **It is not the evaluator running the current experiment.** The current cluster job remains pinned to `2026-11-18-corrected-r0-d8ba3815cf95` and execution contract `native-execution-v2`. The candidate uses `native-execution-v3` because the shared output-path instructions change.

## Changes

| Area | Behavior in this candidate |
|---|---|
| Provider interruption | An explicit resume retries incomplete, refused or empty output at the same logical round. Previous terminal programs and attempt evidence remain intact. |
| Condition selection | A request for Original only or Generated README only schedules that condition. |
| Cost accounting | The condition-local receipt ledger sums retained provider attempts, including retries. Missing usage remains unknown; SDK retries without individual receipts cannot be counted exactly. |
| Saved-success reuse | A changed or missing transport contract prevents reuse. |
| Output inputs | Both documentation arms receive an explicit distinction between a local filesystem path and a file URI. Input fixtures are not changed. |
| Future API inventory | Empty, undecorated, base-free classes defined solely in explicit import-failure handlers are classified as placeholders. Ordinary marker classes, nonempty fallback implementations, inherited classes and ambiguous handlers remain eligible for review. |

## Verification

The runner regression suite passed **83 tests and 79 subtests**. The inventory suite passed **161 tests and 78 subtests**. Additional shared-runner and native-contract checks passed. These suites overlap and should not be added into one total. The [status record](STATUS.json) binds the exact candidate files and test-log hashes. Tests use local fixtures and mocked provider responses; this candidate made no paid model calls.

Only the nine listed code/test files and these two candidate documents are included. The branch starts at study commit `7ac965c80f390fb8cf0403c1c8f7a0d810823d3b`; unrelated working-copy edits are not published here.

## Deployment boundary

The cluster copy under `study/review/development-2026-11-19` is a review package, not an installed runtime. Do not point an ongoing job at it. Adoption requires a new versioned evaluator, reviewed selection and prompt/input contracts, validation and a new matched experiment namespace. Existing scores, denominators and failure records remain unchanged.

The current native acceptance metric is not independent task accuracy. Generated README validation, independent correctness checks and the full ablation study remain separate work.
