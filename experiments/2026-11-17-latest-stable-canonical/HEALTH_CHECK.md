# AIDEAL health check

Checked November 17, 2026, 02:24 PM PST. **The checked software paths pass; the replacement experiment is not ready to launch.** Its source/API selection and documentation mapping still need revision. No model call or subject-library execution occurred during this check.

## What was checked and fixed

| Area | Result | Evidence |
|---|---|---|
| Shared discovery, preparation, evaluation and recovery code | 171 selected offline tests passed before the fix | [Test audit](review/health/tests/AUDIT.md) |
| Direct README resume | Fixed a missing ownership-module fingerprint; 56 affected tests passed afterward | [Post-install results](review/health/tests/POST_INSTALL_RESULTS.json) |
| Six stable library pins | All six remain latest stable; official tag commits match | [Versions and official links](review/health/upstream.md) |
| Subject source checkouts | All six match their pinned commit/tree with clean tracked source files | [Alignment audit](review/health/ALIGNMENT.json) |
| Library branches | All 30 expected condition branches match their untreated baseline snapshots | [Alignment audit](review/health/ALIGNMENT.json) |
| Repository visibility | AIDEAL and all six subject repositories are public | [Visibility audit](review/health/GITHUB_VISIBILITY.json) |
| Review pages and tracker | Corrected stale current counts, historical commands and broken archive navigation | [Documentation audit](review/health/AUDIT.md) |
| Cleanup | Removed 4,936 verified cache/duplicate files, totaling 85,172,087 bytes | [Exact cleanup ledger](review/health/CLEANUP.json) |
| Experiment state | No matching active job; launch remains blocked | [Cluster state in alignment audit](review/health/ALIGNMENT.json) |

The broad and focused test sets overlap; do not add their totals as unique tests. Three controller-copy tests were deliberately excluded because they would copy the credential scratch file. The tests use synthetic adapters and mocked models, not real library or model experiments. Existing setup controls remain historical evidence and do not prove that every API or optional dependency works.

### Resume fix

Direct README generation previously omitted `api_origin.py` from its engine fingerprint. Changing ownership-filter implementation could therefore reuse old README entries when the selected signatures stayed the same. The corrected fingerprint rejects that stale resume before another model call. The launcher already tracked all engine files; this fix covers direct engine/CLI use as well. [Baseline/corrected proof](review/health/tests/ORIGIN_FINGERPRINT_REGRESSION.json).

## Current plan and remaining work

| Order | Required work | State |
|---|---|---|
| 1 | Discover library-owned APIs; retain Beast's custom Spark subpackage | Ownership filter implemented and tested |
| 2 | Reconcile full public exposures, including Cython, re-exports and inheritance | Pending |
| 3 | Reduce overloads within each qualified owner; map wrappers to retained targets | Pending; old global-name selector is not the replacement policy |
| 4 | Carry qualified IDs through README entries, task IDs, completion checks and installation | Pending |
| 5 | Bind corrected original documents to those IDs and freeze the new bank | Pending; 1,695 is superseded preparation data |
| 6 | Rebuild prompts/configurations, cost estimate and launch fingerprints | Pending the approved bank |
| 7 | Review the six small pilot inputs before any live call | User review required |
| 8 | Run approved R0 and README authoring, then the five-condition repair/deep-dive study | Not started |

The [experiment guide](EXPERIMENT_GUIDE.md), [tracker](review/EXPERIMENT_TRACKER.html), [API audit](review/api-audit/API_AUDIT.html) and [read-only runbook](RUNBOOK.md) identify the current state. All five new condition refs still point to untreated baselines. Existing branches alone do not establish README, alias or hint installation.

## Cleanup boundary

Deleted files were regenerable Python/Finder caches or temporary copies whose bytes matched retained canonical files. Seven frozen cluster releases were verified before and after their unmanifested bytecode caches were removed. Measured results, paid model responses, fixtures, source versions, dependencies and Git history were retained. Fifteen unique temporary files were preserved.

The working checkout remains on `main` with pre-existing local changes. This audit did not reset, discard or sweep those changes into a commit. Before the new fix, all 228 approved workflow files matched the published study snapshot. The new two-file fix is published separately on that study branch. The frozen evaluator remains unchanged; current development updates live under `review/api-audit/code_updates/` in the portable review package.

## Verify or repeat safely

From this review folder, `python3 verify_snapshot.py` checks the current portable-file hashes. The final sync manifest identifies the published package. The initial alignment receipt deliberately describes the snapshot at audit start; it is not relabelled as the later commit.

To repeat the focused offline checks on this Mac without overwriting the saved test receipts, copy the runner into a fresh temporary directory:

```bash
AIDEAL_CHECK_DIR=$(mktemp -d /tmp/aideal-check.XXXXXX)
cp "/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_WORKSPACE/03_Experiments/2026-11-17-latest-stable-canonical/review/health/tests/run_post_install_checks.py" "$AIDEAL_CHECK_DIR/"
PYTHONDONTWRITEBYTECODE=1 /Users/clockorangezoe/miniconda3/envs/geo_llm_spark/bin/python "$AIDEAL_CHECK_DIR/run_post_install_checks.py"
```

This runner checks the Mac working checkout and saves receipts in the temporary directory. It does not launch a study. Use VS Code Remote SSH for future approved long runs in the cluster environment; a new native Mac scientific runtime has not been validated.
