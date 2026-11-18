# Validated native-hint conditions

Two libraries now contain one validated source-embedded exception hint each. The
Error Hints only and Combined branches use identical hint source bytes and
validation receipts within each library. The runtime receives guidance through
the raised exception. The JSON installation receipt is provenance, not a hint
retrieval mechanism.

| Library | Condition | Commit | Installed resources |
|---|---|---|---|
| mir_eval | Error Hints only | `4906acce7dedff49af5d33ce854548169c6b2361` | Original documentation and one native hint |
| mir_eval | Combined | `b1e3c200cddd4bbb03d26d8d4992d47ec2566b8e` | Generated README and the same native hint; aliases pending |
| MDAnalysis | Error Hints only | `9a34377a60a346e47265a3845dd3b9c3b68e5481` | Original documentation and one native hint |
| MDAnalysis | Combined | `88f27c4a4143cb15ad4ee68738d17e4590792daa` | Generated README and the same native hint; aliases pending |

All branches use `study/2026-11-17-latest-stable-canonical/` followed by
`error-hints-only` or `combined`. The Original, README only and Alias only refs
remain unchanged. Combined does not yet represent the complete three-resource
treatment.

## What changed and what passed

`mir_eval/transcription.py:137` appends a reference-interval/pitch length hint to
the existing `ValueError`. `package/MDAnalysis/lib/util.py:2652` appends a
non-None unit-cell input hint to the existing `ValueError`. Neither patch changes
the condition, exception class, or valid-path computation.

Each patch passed four controls against both baseline and candidate, producing
eight executions. The controls cover the recorded trigger, a corrected caller,
an independent valid input, and a nearby error that must not receive the hint.
Independent replays also passed. Installed-runtime smoke tests passed in every
condition checkout. The MDAnalysis smoke verifies native feedback through both
`check_box(None)` and `distances.transform_RtoS(..., None)`.

These are development and installation checks, not audience evaluation results.
The mir_eval corrected caller uses two notes per side. The MDAnalysis corrected
caller uses a synthetic 50-unit cell. Neither preserves the original task's
complete fixture or proves successful repair of that original task. No held-out
or audience-performance improvement follows from these checks.

## Source and evidence locations

The cluster study root is
`/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical`.

| Item | Path below the study root |
|---|---|
| Isolated condition source | `runtime-conditions/native-hints-2026-11-18/<library>/<condition>/` |
| Per-condition installation and smoke records | `operator/ablation/2026-11-18/native-install/<library>/<condition>/` |
| MDAnalysis pre-import runtime selector | `operator/ablation/2026-11-18/native-install/mdanalysis/mdanalysis_condition_runtime.py` |
| mir_eval paired validation | `native-hint-authoring-2026-11-18/mir_eval/caller-correction/validation/transcription/checks/validation.json` |
| MDAnalysis paired validation | `native-hint-authoring-2026-11-18/mdanalysis/caller-correction/validation/check-box/checks/validation.json` |

Each condition contains `.aideal/treatments/native_hints_validation.json`.
There is no legacy `.aideal/treatments/error_hints.json` treatment. Source hashes,
preserved README hashes, validation paths and synchronization proofs are in
`ADDITIONAL_PUBLICATIONS.json`, together with the earlier mir_eval Error Hints
only `PUBLICATION.json` record.

Local branch and tracking refs reside in
`/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/.local/library_publications/<library>/`.
Their current checkout and index were preserved. The branch refs identify the
condition; a repository's current working directory does not automatically
switch when a ref is updated.

## Selecting the runtime

The pinned interpreter is
`/home/zshan011/apps/aideal/envs/2026-11-17-latest-stable/bin/python`.
Use a fresh process for each program. Replace `PROGRAM.py` and `OUTPUT` with
reviewed paths; create the output directory first.

For mir_eval, choose the complete condition source with `PYTHONPATH`.

```bash
env PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH=/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/runtime-conditions/native-hints-2026-11-18/mir_eval/error-hints-only \
  /home/zshan011/apps/aideal/envs/2026-11-17-latest-stable/bin/python PROGRAM.py
```

MDAnalysis needs its pinned compiled extensions. Its selector imports the
condition's `MDAnalysis.lib.util` source before the first MDAnalysis import and
uses the installed baseline package for the remaining modules and extensions.
It rejects an already imported library or mismatched source hashes and verifies
that `MDAnalysis.lib.distances.check_box` binds the selected function.

```bash
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 \
  /home/zshan011/apps/aideal/envs/2026-11-17-latest-stable/bin/python \
  /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/operator/ablation/2026-11-18/native-install/mdanalysis/mdanalysis_condition_runtime.py \
  --source-root /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/runtime-conditions/native-hints-2026-11-18/mdanalysis/error-hints-only \
  --receipt OUTPUT/runtime-selection.json PROGRAM.py
```

Replace only the source-root condition with `combined` to select its identical
native hint source. Generated README exposure belongs to the audience request;
this runtime selector does not add documentation or other prompt material.
Neither command installs over the Original environment. A paid experiment still
needs a fresh frozen plan binding its source commit, runtime, prompts and outputs.
