# Where to find outputs and API tests

The controller writes to explicit paths you choose. `STUDY` below is an attached library study, `PREVIEW` a development preview directory, `PROPOSALS` a proposal directory, `FREEZE` a validated protocol directory, and `RUN` an audience-run directory. These are conventions and examples, not bundled experiment results.

## Which API test do you mean?

| Kind | Program/input | Results |
| --- | --- | --- |
| Native README comprehension execution | `<work_dir>/run_<API>/<test_filename>`; defaults to `.aideal_exec/run_<API>/ApiTest.scala` under the native project root | Work-directory checkpoint, configured error log, final JSON printed to stdout |
| Frozen trusted controls | `FREEZE/validation/<condition>/<case>/control_NNN/attempt_NNN/request.json` includes reference or negative-control code | Same attempt's process/log evidence; aggregate `validation/validation.json` |
| Fresh audience solution | `RUN/<condition>/<case>--<trial>/round_NN/provider_NNN/process.json` → `payload.code`; checker request contains the submitted candidate | Unit `result.json`, per-attempt evidence, run `REPORT.md` and `report.json` |

The condition controller does not impose a source filename. The library adapter writes compiled/executed source and raw checks inside its attempt directory; a Scala adapter may use `Solution.scala`, but this is not a universal controller output. Consult the adapter and its `adjudication_artifacts` receipt for exact files. A trusted reference program is not an audience-model result.

## Development README API checks

The native `api-tests` command mines existing repository usage examples and prints JSON. It does **not** generate or execute an API test. Use `comprehension --execute` for configured model-written snippets and actual execution.

Native YAML controls these paths:

```yaml
files:
  llm_readme: docs/LLM_readme.md
  error_log: logs/error_log.jsonl
comprehension:
  execute:
    work_dir: .aideal_exec
    test_filename: ApiTest.scala
```

Paths resolve against the native project root: the configuration file's grandparent, normally `<workspace>/configs/aideal.yaml` → `<workspace>`. Supply the appropriate scaffold and compiler/runtime command too. Change `test_filename` for another language. README generation writes `files.llm_readme`; native execution writes:

```text
<work_dir>/
  run_identity.json
  comprehension_progress.jsonl
  run_<API>/
    <test_filename>
    classes/
```

The native command has no `--output` option here. Save its printed result explicitly:

```sh
# After installing/configuring the native engine; this calls its model/runtime.
python -m aideal.cli --config /path/to/workspace/configs/aideal.yaml \
  comprehension --api API_NAME --execute --show-code \
  > /path/to/existing-output-directory/result.json \
  2> /path/to/existing-output-directory/progress.stderr
```

`--show-code` includes snippet details and output tails. Retries overwrite the per-API test file; this development path does not retain each complete round as a separate source file. Select a different configured work directory for a new experiment; use `--resume` only with the same identity. These checks are separate from held-out condition evaluation.

## Audited README sessions

The explicit [session workflow](README_SESSIONS.md) uses a new directory for each prepared full/refresh plan, separate from the legacy native work directory:

```text
SESSION/
  base.md                              immutable copy of the supplied base
  session.json                         exact inputs, prompts, roles and hashes; no call at preparation
  entry_0000/
    prepared.json
    entry.request.json / entry.state.json       full-author phase
    deep_dive.request.json / deep_dive.state.json  refresh reviewer phase
    rewrite.request.json / rewrite.state.json   refresh fixer phase
    candidate.md                       complete selected entry only
  README.md                            composed only after every selected entry completes
  completion.json                      authored_not_execution_validated; no library executed

STAGE_EVIDENCE/
  contract.json
  call-<UTC>-<unique-id>/
    contract.json / request.json / settings.json / reservation.json
    response.json / result.json / outcome.json
    failure.json                       only when an adapter failure is recorded
```

The two phase layouts are alternatives, not files present in every entry. Interrupted calls may lack response/result files. A shared mutable budget JSON and sibling `.lock` live outside the stage directories; do not bind their changing full bytes into frozen command artifacts. Completed phase state binds exact provider receipts and its settled ledger row. Missing or altered evidence blocks reuse. No generated program, compiler run or numerical pass is implied by `candidate.md` or a complete README.

## Development proposals and versions

| Path | Meaning / creation condition |
| --- | --- |
| `PREVIEW/manifest.json`, `PREVIEW/batch-0001/preview.json` | Coverage and exact bounded API/source/profile/error context from `preview-library`; no model call |
| `PROPOSALS/identity.json`, `collection.json` | Proposal configuration identity and batch status |
| `PROPOSALS/batch-0001/request.json`, `attempt_001/` | Exact request and provider attempt evidence; failures remain present |
| Batch `suggestions.json`, `proposal.json`, `completion.json` | Successful validated output and completion; no-suggestion responses may have no installable proposal |
| Batch `alias_source.<extension>`, `ALIASES.md` | Created only for supported alias suggestions |
| Batch `error_hints.json`, `function_fix_hints.jsonl` | Created only for evidence-based hint suggestions |
| Batch `refactor_suggestions.json` | Review candidates; not an applied patch |
| Bundle `proposal.json`, `alias_NNNN.<extension>`, `ALIASES.md`, `error_hints.json`, `README.md` | `bundle-proposals --output DIRECTORY`; only applicable artifact roles are written |
| Arm source `.aideal/treatments/{README.md,ALIASES.md,error_hints.json}` | Installed metadata in applicable conditions; alias source uses the proposal's explicit new target path |
| `STUDY/treatments/<hash>/application.json`, `treatments/current.json` | Installed treatment-version record and current pointer |
| `STUDY/refactors/<version>.json`, `refactors/current.json`, `Refactor only/<version>/source/` | Separate source-refactor record, pointer and checkout |

Development error logs are explicit inputs; the controller does not invent a universal filename for them. Native logs default to `logs/error_log.jsonl`. Library build logs, source-refactor regression reports, compiled binaries and private fixture layouts are adapter/study-specific. Duplicate report filenames are the exact files passed to `scan-duplicates --output` and `compare-duplicates --output`.

## Frozen controls and audience runs

```text
FREEZE/
  frozen.json                         written only after complete successful controls
  validation/
    identity.json
    validation.json
    <condition>/<case>/control_NNN/attempt_NNN/
      request.json                    private checker request and control code
      process.json                    status, duration and adapter verdict
      stdout.txt
      stderr.txt
      ...                             adapter-owned source and check artifacts

RUN/
  identity.json
  report.json
  REPORT.md
  <condition>/<case>--<trial>/
    result.json
    round_NN/
      context_exposure.json
      provider_NNN/{request.json,process.json,stdout.txt,stderr.txt}
      execution_NNN/{request.json,process.json,stdout.txt,stderr.txt}
      ...                             adapter artifacts live inside execution_NNN/
```

Round numbers start at `00`; provider/execution attempts at `001`. `control_000` is the reference; subsequent controls follow each case's wrong-output and no-target lists. Numbers increase for additional attempts; earlier evidence is retained. A failed provider has no successful candidate; a compile failure may have no runtime check files. Mere directory presence is not a pass.

Open `REPORT.md`, then a unit's `result.json`, then the exact provider/checker requests and verdicts. `context_exposure.json` records documentation/interface/hint delivery. Private oracle paths, checks and answers are evaluator evidence; do not reuse them as authoring inputs or public task text.

## Choose and resume outputs

```sh
python scripts/aideal preview-library --study /path/to/study \
  --output /path/to/study/development/preview_v1
python scripts/aideal freeze-conditions --config /path/to/study/conditions.yaml \
  --output /path/to/study/frozen_v1
python scripts/aideal run-conditions --study /path/to/study/frozen_v1/frozen.json \
  --output /path/to/study/runs/first
```

Replace paths and complete the configurations; these commands are examples, not pre-created outputs. `--output` usually names a directory; duplicate scan/comparison commands use a JSON filename. Installation commands instead take the study and proposal and write their defined version locations. Keep development outputs outside source checkouts.

Repeat the same compatible run output to resume. Use a new output for a changed freeze or independent rerun; never overwrite identities to make old results appear current. The separate three-README evaluator uses its own condition labels and exposure files; do not combine its result directories with this condition protocol.

Implementation: [development commands](../workflow/development_cli.py), [controls](../workflow/condition_setup.py), [audience attempts](../workflow/condition_evaluation.py), [process files](../workflow/execution.py), [reports](../workflow/condition_reporting.py), [native API execution](../vendor/aideal_engine/src/aideal/doc_check_execution.py).
