# Offline software audit — November 17, 2026

**171 selected tests passed** in Python 3.10.19, with zero failures, errors or skips. Three additional tests were intentionally excluded because they copy the complete `workflow` directory, which can include the forbidden scratch file.

The run used temporary synthetic source repositories, small JSON adapters and mocked author responses. It made no real model call, accessed no network, installed no dependencies, and ran no library experiment. It did execute the inspected synthetic fixture adapters and temporary Git commands. The main process denied network access, scratch/credential-file reads and source-tree writes; no guard violation occurred.

## Coverage

| Test module | Passed |
|---|---:|
| `test_api_origin` | 24 |
| `test_api_canonical_selection` | 16 |
| `test_compiler_api_registry` | 9 |
| `test_compiler_canonical_selection` | 10 |
| `test_source_audit_registry` | 11 |
| `test_sql_canonical_aliases` | 5 |
| `test_canonical_prompt_targets` | 7 |
| `test_canonical_launch_relocation` | 6 |
| `test_readme_modules` | 11 |
| `test_readme_launcher` | 10 |
| `test_readme_replay` | 10 |
| `test_original_micro_launcher` | 3 |
| `test_evaluation` | 22 |
| `test_condition_evaluation` | 9 |
| `test_shared_evaluation` | 4 |
| `test_evaluation_recovery` | 9 |
| `test_incomplete_evaluation` | 5 |

## Confirmed integration defect — fixed

Previously, direct `find_or_create(..., resume=True)` did not include `api_origin.py` in its engine fingerprint. A controlled change to the bytes observed for this module left the fingerprint unchanged and reused two README entries. The launcher route already fingerprints every engine file; the missing binding affects the direct engine/CLI route.

The root agent installed the checked fix, adding `api_origin.py` to the existing `_engine_files` tuple and one regression test. The pre-install demonstration changed no actual source file. After installation, **56 affected README generation, replay and origin tests passed**, including the new regression. No failures, errors, skips, network attempts or real model/library calls occurred. Exact checked source/test hashes and command are in [POST_INSTALL_RESULTS.json](POST_INSTALL_RESULTS.json).

The 171-test broad run preceded the fix; the 56-test focused run followed it. These totals overlap and must not be added as unique test cases. The stored baseline/candidate proof records the previous defect and is not a fresh failure of the installed code.

- Baseline/candidate proof: [ORIGIN_FINGERPRINT_REGRESSION.json](ORIGIN_FINGERPRINT_REGRESSION.json)

- Installed patch: [patch/origin_fingerprint.patch](patch/origin_fingerprint.patch)

- Regression proof: [patch/REGRESSION_TEST_RESULT.json](patch/REGRESSION_TEST_RESULT.json)

## Readiness limits

The tests of global bare-name canonical selection intentionally preserve the historical policy. They do **not** establish that the newer owner-qualified policy is implemented. The current README catalog still has one entry per bare-name family, even when underlying source facts preserve distinct owners. Passing this suite must not be reported as completion of the replacement bank or approval to launch it.

No fresh production-library build, full API execution, model-access check, or treatment run was performed. Existing runtime evidence must remain separate from this software audit.

## Reproduce the selected checks

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/clockorangezoe/miniconda3/envs/geo_llm_spark/bin/python /tmp/aideal-followup-health-2026-11-17/tests/run_offline_checks.py
```

The runner has an explicit allowlist and writes [RESULTS.json](RESULTS.json), [TEST_LOG.txt](TEST_LOG.txt), and [TEST_SELECTION.json](TEST_SELECTION.json). Running it after code changes produces a new validation record; preserve the current receipt if needed for publication.


## Reproduce the installed fix checks

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/clockorangezoe/miniconda3/envs/geo_llm_spark/bin/python /tmp/aideal-followup-health-2026-11-17/tests/run_post_install_checks.py
```

This focused runner writes `POST_INSTALL_RESULTS.json` and `POST_INSTALL_TEST_LOG.txt`. It checks four affected test modules and does not rerun the entire 171-test selection.
