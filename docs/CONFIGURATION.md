# Configuration and input contracts

Use explicit inputs for each stage. AIDEAL does not choose a library, hosted model, credential file or runtime environment. Examples contain placeholders and must be completed before execution.

| Configuration | Used by | Responsibilities |
| --- | --- | --- |
| [aideal.example.yaml](../configs/aideal.example.yaml) | `attach`, `prepare-study`, native engine | Source/tests, original docs, outputs, native model roles and development scaffold |
| [improvements.example.yaml](../configs/improvements.example.yaml) | `propose-library`, `propose-improvements` | Development command/model, output and transport budgets |
| [condition_evaluation.example.yaml](../configs/condition_evaluation.example.yaml) | `freeze-conditions`, `run-conditions` | Matched conditions, bank/model/budgets, source/runtime identities and adapters |
| [readme_evaluation.example.yaml](../configs/readme_evaluation.example.yaml) / [selective refresh](../configs/readme_selective_refresh.example.yaml) | `freeze-evaluation`, `run-evaluation` | Explicit three-document design on one backend |
| [Audited README sessions](README_SESSIONS.md) | `workflow.readme_authoring`, `workflow.readme_session` | Pinned definition/base/context manifest, exact author/reviewer/fixer contracts and shared budget |

## Library configuration

Place native configuration at `<workspace>/configs/aideal.yaml`. Its project root is the configuration file's grandparent. Relative source/test patterns, documents and outputs use that root; absolute paths can select a separate checkout. `--repo` selects the clean Git repository to attach; configured source files must belong to it.

Native loading order is packaged `defaults.yaml`, each directly named adapter in `extends`, then the project YAML. Mappings merge recursively; scalar/list values replace prior values. Adapter inheritance is not recursively followed. The native loader can ignore missing adapters or individual documentation paths; study preparation adds stricter checks, including missing explicit adapters and an empty resolved documentation bundle.

`files.original_readme` accepts a path or list of files/directories/globs. Supported text files are expanded deterministically and de-duplicated. Attachment saves the full resolved bundle. Inspect `source.json` and preview coverage before treating the scope as complete.

The project profile supplies domain, audience, use cases and constraints. `models.registry` and `models.roles` configure native author/audience/fixer roles. `comprehension.execute` specifies its scaffold, command, data bindings and retry/output settings. These do not override a condition study's `common` budgets.

Attachment creates draft scaffolds and `.aideal/` instrumentation in isolated worktrees. A draft harness is not evaluation-ready; build/import dependencies and independent checks must be supplied and validated.

## Development proposals

`preview-library` writes coverage and bounded batch contexts from the attachment. Batch size, context/catalogue/error budgets are command options; omissions are disclosed. Use exact `file:line:name` IDs when names are ambiguous. Development errors are optional explicit inputs and must not come from held-out evaluation. Scala rows also carry source-backed `receiver`, `owner_kind`, `owner_path`, `qualified_receiver`, `source_qualified_name` and `qualification_status`. These facts preserve original discovery IDs and filters. Local or unsupported sites remain explicitly unresolved; a bare `qualified_name` is not receiver proof.

`propose-library --preview PREVIEW/manifest.json --model-config MODEL.yaml --output PROPOSALS` calls the configured development adapter. `--max-batches` bounds one invocation. Provider-attempt limits persist per batch across resumption. Exact requests, failed attempts and completion bindings are retained; changed identities require a new output directory.

The model command receives `system`, `prompt`, `model`, `temperature`, and `max_output_tokens` JSON on stdin. It returns `code` containing suggestion JSON, plus optional usage/model-version fields. Alias source/interface, hints and refactor evidence have separate roles. Application remains a separate reviewed step.

## Held-out bank and condition configuration

Paths within `condition_evaluation` resolve relative to its YAML file. Case reference/control/oracle paths resolve relative to the bank JSON. Source revisions and command/artifact paths must identify existing inputs before freeze.

A bank declares `api_names` and `cases`. Each case has a unique ID, `kind` (`micro` or `puzzle`), `split: held_out`, public prompt/context, targets, reference and oracle files, wrong-output controls and no-target controls. Microcases have one target and cover the declared API scope; at least one puzzle is required. Private fixture/oracle schemas belong to the trusted adapter. Independent expectations must be designed and checked, not inferred from a model answer.

`design` is `five_arm`, `refactor_pair` or `six_arm`; see [VERSIONS.md](VERSIONS.md). Common settings fix the model/temperature, candidate token cap, repair count, transport/execution timeouts, trials, order and context character caps. `api_function_ids` maps public bank targets to qualified development hint IDs when needed. `development_case_ids` and `holdout_review` record the declared separation.

Each condition binds documents, source worktree/revision, runtime artifacts and adapter command. Individual and combined treatments must match. Aliases are additive; the Refactor only condition must preserve the public API. Artifact checks do not replace behavior tests.

The checker receives code, private case/oracle/target information and a backend identity. It returns:

```json
{
  "backend_sha256": "digest of the verified requested backend",
  "execution_pass": true,
  "oracle_pass": true,
  "target_reached": true,
  "public_feedback": "Diagnostic text safe to show to the solver"
}
```

It may publish `adjudication_artifacts`: exact path/hash/size bindings to raw verdict evidence, verified during validation/resume. Public feedback must not reveal hidden answers. A receipt is an attestation by the trusted adapter; source/build correspondence, runtime origins and library regressions must substantiate its routing.

## Audited native authoring and README designs

The optional `aideal-codex-audited` native provider requires an exact bridge contract, active controller hashes, a new `study-v2` ledger identity, explicit stage/output limits, and a separate evidence directory per phase role. `study-v2` permits a configured ceiling up to $100; legacy schema-1 ledgers retain their original maximum of $5 and cannot be upgraded in place. Preparation is offline; executing a session calls the provider and remains fail-closed on incomplete or uncertain responses. See [README_SESSIONS.md](README_SESSIONS.md) for the full portable schema and commands.

The separate `readme_evaluation.design` is `three_readme` by default or `selective_refresh` explicitly. Selective refresh requires exactly `Unchanged generated README`, `Selected API refresh`, and `Full README refresh`, in that comparison order. Names are selected from the frozen config, including `--condition` filters, paired reports and the unchanged-document baseline. Never mix names or rewrite an older freeze. For the new prepared recipe, the last condition means fresh full authoring from the common skeleton/facts followed by the same selected-entry refresh. The label alone does not enforce or prove that provenance. This design does not add alias/hint branches.

## Optional qualified-section retrieval

Both evaluation protocols accept an explicit `common.documentation_selection` mapping:

```yaml
common:
  documentation_selection:
    policy: qualified_sections
    api_headings:
      library.Reader.readType: library.Reader.readType [object]
      library.Grid.resize: library.Grid.resize [class]
```

This is a fragment: map **every** declared bank API exactly, using its full API spelling plus ` [class]` or ` [object]`. The mapping is reviewed provenance; it does not infer receiver ownership. Omission preserves the prior retrieval policy and prompt/exposure bytes.

An exact API heading wins over repeated method names elsewhere. Duplicate exact headings reject the selection, and fenced headings do not count. If an exact heading is absent, only unstructured sections can match the full API, receiver/method or bare method in specificity order; a different explicitly qualified API section cannot substitute. One matched section is selected per target. Distinct target sections receive balanced character quotas, with unused space from short sections redistributed. Oversized sections are clipped with exact source ranges and full/clipped coverage in the receipt. When relevant sections fit, unrelated filler is omitted. With no match, the original ordered prefix is supplied within the cap and missing target coverage stays explicit.

Use the same frozen policy/mapping/cap across compared documents. Changing this policy changes model exposure and requires a new freeze. See [documentation_selection.py](../workflow/documentation_selection.py); character caps do not guarantee equal token counts.

## Credentials and execution

The included Google command reads `GOOGLE_API_KEY` or `GEMINI_API_KEY` from the environment. Keep secrets out of YAML, source, prompts and committed outputs. Another provider can implement the same JSON interface. Portable model/checker commands are argument lists invoked without a shell; native development commands have separate semantics.

See [SUMMARY.md](SUMMARY.md) for prompts and harness boundaries, and [OUTPUTS.md](OUTPUTS.md) for paths and resumption.
