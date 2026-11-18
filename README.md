# AIDEAL — develop documentation and evaluate its effect

**Current six-library preparation (November 17, 2026):** [experiment guide](experiments/2026-11-17-latest-stable-canonical/EXPERIMENT_GUIDE.md), [all qualified API/task inputs](experiments/2026-11-17-latest-stable-canonical/review/qualified-bank/INDEX.html), [readiness fixes](experiments/2026-11-17-latest-stable-canonical/READINESS_FIXES.md), and [review commands](experiments/2026-11-17-latest-stable-canonical/RUNBOOK.md). Live runs remain paused for input review; earlier results retain their own scope.


**Run readiness checked November 12, 2026:** [automation, study prerequisites and code-review route](docs/AUTOMATION_READINESS.md).

[Codex pilot and shared budget](docs/OPENAI_CODEX_PILOT.md) · [Gemini Flash settings](docs/GEMINI_FLASH.md) · [Legacy-code review](docs/LEGACY_CODE_REVIEW.md)

AIDEAL develops documentation, aliases and failure hints for existing libraries,
then compares how well an LLM uses their APIs. Start with the workflow entrypoints
and follow helper functions when needed.

| Workflow | Main entry points | Current boundary |
|---|---|---|
| **README comparison** | `freeze-evaluation` → `run-evaluation` | Three supplied README versions; one backend and independent bank |
| **Treatment comparison** | `freeze-conditions` → `run-conditions` | Five treatment arms, Original/refactor pair, or six arms; explicit validated library adapters required |
| **Development and versions** | `preview-library` → `propose-library` → bundle/install | Bounded LLM batches, multi-file aliases, evidence-based hints and separate refactor candidates |

There is no default library, language or API count. RDPro and SedonaDB are examples.
The historical three-README RDPro pilot remains paused under its `REVIEW_HOLD.json`.
The current five-condition treatment study has separate inputs, versions and results.

**GitHub:** [public toolkit repository](https://github.com/ZhuochengShang/AIDEAL) · [local publication checkout and update guide](docs/PUBLICATION.md).

**Outputs:** [API test files, logs and study results](docs/OUTPUTS.md).
**Cleanup:** [retired RDPro components and restoration record](docs/LEGACY_RDPRO_CLEANUP.md).

**Start here:** [current implementation and real-study status](docs/CURRENT_STATUS.md),
[library-wide workflow](docs/LIBRARY_TREATMENT_WORKFLOW.md),
[condition/version navigator](docs/VERSION_NAVIGATION.md), and
[score formulas and current saved results](docs/EVALUATION_SCORING.md).
The [system figures](docs/system_design/README.md) are a preserved pre-extension
review snapshot; use the current guides for the newly implemented treatment runner.

## Start your code review

**Shared evaluation and code guide, November 12:** [interactive workflow and source links](docs/EVALUATION_CODE_GUIDE.html) · [reading order and commands](docs/EVALUATION_CODE_GUIDE.md) · [current treatment workflow](docs/TREATMENT_WORKFLOW.md).

Both evaluation commands now enter one schedule, repair loop and evidence checker.
The [workflow map](docs/CODE_MAP.html) opens on those shared entry points, with
helpers collapsed underneath. Canonical evaluation files use the `evaluation_`
prefix so they appear together in the file browser.

| Read first | What it owns |
|---|---|
| [evaluation_runner.py](workflow/evaluation_runner.py) | `run_study`, `run_unit`, `verify_row` and `replay`: scheduling, bounded repair and verified resume |
| [evaluation_conditions.py](workflow/evaluation_conditions.py) | Treatment-specific context and library/backend checks |
| [evaluation_readme.py](workflow/evaluation_readme.py) | Original/Generated/Repaired README selection and shared provider/evidence helpers |

Open `evaluation_freeze.py`, `evaluation_context.py`, `evaluation_inputs.py`
and `evaluation_report.py` when following those responsibilities. The two old
main entry modules remain compatibility aliases. Historical studies retain their
recorded controller; new source requires a new freeze.

Use the **Full function reference** only when following a particular dependency.
The [source index](docs/FUNCTION_INDEX.md) offers clickable locations for Codex.
The [pipeline reference](docs/PIPELINE_REFERENCE.md) explains the boundaries;
[the simplification record](docs/WORKFLOW_SIMPLIFICATION.md) records removals,
consolidations and checks. [Earlier module cleanup](docs/CODE_CLEANUP.md) describes
the split of the two large engine files.

## Three-README evaluation

Supply Original README, Generated README and Repaired README explicitly. The
runner does not generate those documents. It holds the backend, task bank, model,
context budget and repair budget constant across conditions.

`freeze-evaluation` validates independent reference/negative controls and freezes
identities. `run-evaluation` runs or resumes the matched comparison. An adapter
checks execution, independent correctness and target-API use. A successful exit
alone is insufficient. Five branches are not required for this comparison.

Read [the evaluation design](docs/EVALUATING_YOUR_LIBRARY.md),
[the runnable guide](docs/README_EVALUATION_RUNNER.md) and
[the YAML example](configs/readme_evaluation.example.yaml).

## Documentation development

The engine under `vendor/aideal_engine/src/aideal/` discovers APIs, authors
README entries, checks examples and repairs documentation. Its CLI and MCP
interface are separate from the portable controller. The old `readme_agent.py`
and `doc_checks.py` import their implementations from focused modules.

See [development stages and prompts](docs/PIPELINE_REFERENCE.md#3-legacy-document-development-and-its-prompts)
and [configuration rules](docs/CONFIGURATION.md). Model grading, native execution
and independent held-out evaluation are different evidence levels. Development
answers must not leak into the held-out audience inputs.

## Alias, fix-hint and source refactor development

Use `preview-library` to inspect all configured public APIs in bounded batches,
then `propose-library` for recorded, resumable model requests. `bundle-proposals`
combines selected batches without concatenating source files. `install-treatments`
commits the complete version into the applicable isolated branches. For current native hints, use `preview-native-hints` → `propose-native-hints`
→ `validate-native-hints` → `install-native-hints`. Install the README/alias
bundle first, then review, commit and rebuild the native source edits.
Bundles exclude legacy JSON hints unless `--include-legacy-hints` is selected.
The [treatment guide](docs/TREATMENT_WORKFLOW.md) records the full sequence and
the explicitly retained compatibility commands. Generated proposals require
library-specific checks before evaluation.

`scan-duplicates` and `compare-duplicates` suggest refactors for attached
libraries and compare compatible before/after reports. `install-refactor` versions
an explicit source replacement/deletion manifest on a separate branch, preserving
the original five arms. Tests must establish API compatibility. The [RDPro baseline review](docs/SOURCE_REFACTOR_REVIEW.md)
contains concrete candidates for schema decoding, raster validation and URL encoding.
Read [the commands, branch routing and current study inventory](docs/STUDY_TREATMENTS.md)
and [exact README-generation inputs](docs/README_GENERATION_INPUTS.md).

## Matched treatment and refactor evaluation

The treatment design compares Original, README only, Alias only, Error hints only
and Combined. Refactor only can be studied separately or as a sixth condition.
`attach` prepares five isolated worktrees; `versions` shows their exact paths,
commits, current treatment record and any separate refactor version.

`freeze-conditions` validates the actual checker against reference, wrong-output
and no-target controls for every backend. `run-conditions` executes the shared
microtask/puzzle bank and records the delivered README, alias interface and
post-failure hints. Installed code must be built/imported by the configured adapter;
a branch or model proposal alone is not a measured improvement.

Library-specific builds, fixtures, independent oracles and regression checks are
explicit inputs. There is no universal automatic compiler or oracle generator.
Use `freeze-conditions` followed by `run-conditions` with an explicit study.
The [workflow diagram and cleanup guide](docs/EVALUATION_CODE_GUIDE.html)
connects the commands, functions, prompts and saved outputs.

The detailed attachment instructions and planned sequence are in
[Five-condition preparation](docs/FIVE_CONDITION_PREPARATION.md) and
[library treatment workflow](docs/LIBRARY_TREATMENT_WORKFLOW.md).

## Installation and software checks

Use Python 3.10+ with `requirements.txt` in the chosen environment. The portable
launcher works from any directory:

```sh
python3 /path/to/AIDEAL_workflow/scripts/aideal --help
```

From the repository root:

```sh
python3 -m unittest discover -s tests
python3 scripts/build_code_map.py
node --test tests/test_code_map_ui.cjs
```

The Python suite uses synthetic/temporary studies. The Node checks exercise
navigator state with a DOM test double; they do not replace visual browser review.
The map generator parses source without importing the project or running experiments.
`python3 -m workflow verify` compares against the historical artifact manifest;
reviewed source edits can intentionally differ from that snapshot. Do not rewrite
historical identities to make this check pass.

## Operating the project

Respect review holds and existing edits. Use each study's explicit YAML, validated
adapter and protocol; keep attempts and conditions separate. New source identities
require fresh validation/freezing before a new experiment. Preserve actual requests,
responses, execution logs and unresolved outcomes. The included operator skill
provides guidance; it is not automatically sent to the audience model.

The optional MCP server uses `requirements-mcp.txt` and `scripts/aideal serve`.
It exposes attachment, inspection and operating instructions. It is not a Codex
marketplace plugin or a complete evaluation interface.

[Study examples](studies/README.md), [historical reporting](studies/historical/)
and [proposed metrics](docs/EVALUATION_METRICS_PROPOSAL.md) remain separate from
current evaluation results. Historical outcomes are never inserted as new scores.
