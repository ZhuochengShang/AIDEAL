# SedonaDB — five-condition setup · 2026-09-21

**Preparation only. Five source versions start at one baseline. Treatments, validated evaluation and results are pending; no model is selected and this setup made zero model calls.**
The date identifies the setup start, 2026-09-21; preparation continued after midnight without changing the identifier.

[Companion source repository](https://github.com/ZhuochengShang/AIDEAL-SedonaDB) · [Portable identities](setup.json) · [Configuration example](configs/aideal.example.yaml) · [All prepared libraries](../../README.md)

## What is shared and what differs

Shared AIDEAL owns [workflow design](../../../docs/SUMMARY.md), [prompts](../../../prompts), [language harness skeletons](../../../templates/harness), [settings](../../../docs/CONFIGURATION.md), [scoring](../../../docs/SCORING.md), [version handling](../../../docs/VERSIONS.md) and [output conventions](../../../docs/OUTPUTS.md). The private companion repository owns the five library source branches. Access to AIDEAL does not grant access to that repository.
Companion GitHub Actions remain disabled during preparation; existing upstream workflows are not a validated study pipeline.

| Condition | Intended difference from original | Actual state |
| --- | --- | --- |
| [Original](https://github.com/ZhuochengShang/AIDEAL-SedonaDB/tree/preparation/2026-09-21-five-conditions/original) | Original documentation and APIs | Baseline; not evaluated |
| [README only](https://github.com/ZhuochengShang/AIDEAL-SedonaDB/tree/preparation/2026-09-21-five-conditions/readme-only) | Select a reviewed generated README | Same baseline; treatment pending; not evaluated |
| [Alias only](https://github.com/ZhuochengShang/AIDEAL-SedonaDB/tree/preparation/2026-09-21-five-conditions/alias-only) | Add tested delegating aliases and their interface | Same baseline; treatment pending; not evaluated |
| [Error hints only](https://github.com/ZhuochengShang/AIDEAL-SedonaDB/tree/preparation/2026-09-21-five-conditions/error-hints-only) | Deliver matched development-error hints on repair | Same baseline; treatment pending; not evaluated |
| [Combined](https://github.com/ZhuochengShang/AIDEAL-SedonaDB/tree/preparation/2026-09-21-five-conditions/combined) | Combine the same README, aliases, and error hints | Same baseline; treatment pending; not evaluated |

Source snapshot `255a2cdc9528f3908ae097f2b498c27d48d4b7d7` has exactly upstream `59ec34c79594222891b1dbaf106bfa9de14a5b99`'s tree `1df3708ef1d66d3bcbeabbc7bf292a4740290cfd`, with new snapshot ancestry. No historical treatment is imported. Source-root READMEs are unchanged; a future installed generated document is selected from `.aideal/treatments/README.md`, not the source root README or companion `main` navigation page.

## Declared discovery scope

- Source discovery: `rust/*/src/**/*.rs`, `c/*/src/**/*.rs`
- Test evidence: `rust/*/tests/**/*.rs`, `c/*/tests/**/*.rs`
- Original documentation: `README.md`, `examples/sedonadb-rust/README.md`

These globs select inputs for future discovery, not an API count or evidence of API coverage. Rust crate and native-wrapper Rust source scope; other language bindings and submodule internals excluded from initial discovery. Historical 320/322 SQL examples executed without an independent semantic oracle; not a five-condition LLM result. Four submodules uninitialized; no Rust build validation in this setup.

## Get and inspect the five source versions

Use the [companion clone/worktree guide](https://github.com/ZhuochengShang/AIDEAL-SedonaDB#get-the-source). Its five distinct branch names intentionally share the baseline commit. Check out a preparation branch for source; companion `main` contains navigation. Forking is optional when you need your own writable remote; cloning is sufficient to inspect or create local worktrees.

## Prepare your own local study

Install shared AIDEAL's base dependencies as described in its [README](../../../README.md). Clone the companion's `preparation/2026-09-21-five-conditions/original` branch. Copy this example to a separate preparation workspace and replace every `/absolute/path/to/source` with that clean checkout's absolute path. The config must remain in a `configs/` directory; native relative paths resolve from its grandparent.

```sh
# Run from the shared AIDEAL checkout; fill these paths first.
source_path=/absolute/path/to/source
config_path=/absolute/path/to/preparation/configs/aideal.yaml
study_path=/absolute/path/to/new-study
python scripts/aideal attach --repo "$source_path" --config "$config_path" --output "$study_path"
python scripts/aideal status --study "$study_path"
```

Choose a new output outside the source checkout. `attach` pins a clean checkout and creates its own isolated bare clone plus five worktrees; the manual review worktrees are optional. It writes `attachment.json`, `source.json`, `original_documentation.txt`, `plan.draft.json`, an empty `bank.draft.json`, condition records and uncommitted `.aideal/` instrumentation. The language skeleton fails closed until a real library checker is configured. This step calls no model and validates neither source behavior nor semantic outcomes.

Before any paid generation: provision dependencies/submodules; validate runtime and checks; create independent microtasks/puzzles with reference, wrong-output and no-target controls; develop and regression-test treatments using development evidence; build each condition; select identical audience settings/budgets; then validate all controls and freeze the explicit condition protocol. Keep held-out answers and controls out of treatment-development prompts. No legacy library-specific runner is selected implicitly by this example.

## Future outputs and API tests

The following are **future output locations**, not bundled results. Pick a study path and run ID explicitly.

| Stage | Location relative to your chosen study | Meaning |
| --- | --- | --- |
| Development | `development/<name>/` chosen through `--output` | Source preview, exact proposal requests/responses and reviewed treatment artifacts |
| Installed versions | `treatments/<hash>/application.json`, `treatments/current.json` | Versioned installation receipts; applicable branch `.aideal/treatments/` contains selected artifacts |
| Validated controls | `frozen/<version>/validation/validation.json` | Reference/negative-control evidence; `frozen.json` is created only after successful validation |
| Audience summary | `runs/<run-id>/REPORT.md`, `report.json` | Matched per-condition outcomes and unresolved counts |
| One API/task | `runs/<run-id>/<condition>/<case>--<trial>/result.json` | Terminal verdict and evidence links |
| Exact generation | Unit `round_NN/provider_NNN/{request.json,process.json}` | Public prompt, returned candidate and usage |
| Actual API execution | Unit `round_NN/execution_NNN/` | Checker request/logs plus adapter-specific source and checks |
| Delivered context | Unit `round_NN/context_exposure.json` | README, alias interface and matched hint exposure |

Controller filenames are shared; generated program names and runtime artifacts are library-adapter-specific. Native README comprehension checks are separate; see [which API test and where](../../../docs/OUTPUTS.md#which-api-test-do-you-mean). Merely switching branches or finding a log is not a successful evaluation.

After a validated freeze exists, `run-conditions --study PATH/frozen.json --output PATH/runs/RUN_ID` executes/resumes it. `--condition` filters scheduled units, while identity checks still validate all frozen backends. Reusing a compatible run directory resumes its saved state; a new run directory permits fresh, potentially paid stochastic generation. Replaying a saved candidate through a validated deterministic checker is a different operation. This setup supplies no complete one-command bootstrap, frozen bank or result.

Implementation review: [attachment](../../../workflow/worktrees.py), [scaffolding](../../../workflow/scaffolding.py), [freeze/controls](../../../workflow/condition_setup.py), [audience loop](../../../workflow/condition_evaluation.py), [code map](../../../docs/CODE_MAP.html).
