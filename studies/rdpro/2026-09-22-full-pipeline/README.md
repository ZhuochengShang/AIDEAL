# RDPro: broader evaluation and selective README updates

Status: offline preparation. No paid model calls or audience results exist for this study yet. The completed September 21 pilot remains a separate, unchanged experiment.

This study uses GPT-5.3-Codex with low reasoning. It compares five source/documentation conditions and, separately, three README update policies. Every paid stage is planned to share one reservation ledger; its proposed $100 limit requires the operator's approval before execution.

| Estimated API cost, USD | Low usage | Planning case | High-output scenario |
| --- | ---: | ---: | ---: |
| Five-condition study | $19.35 | $25.75 | $54.81 |
| Additional README comparison | $15.52 | $21.24 | $40.18 |
| Both | **$34.87** | **$46.99** | **$94.99** |

These estimates use the actual prepared author/proposal prompt lengths, assumed output sizes and measured earlier-pilot audience usage. They include a conservative allowance for the larger alias interface. They are sensitivities, not confidence intervals or a maximum bill. Unusual input sizes, failures or longer output can make the guard stop before completion. Tax and local computing time are excluded. Rates are $1.75 per million input tokens, $0.175 cached input and $14 output; billed output includes reasoning. See [OpenAI's model pricing](https://developers.openai.com/api/docs/models/gpt-5.3-codex).

## Source and evaluation scope

The source baseline is the public RDPro snapshot `5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8`. Its tree matches the earlier Original condition; its clean publication ancestry has a different commit identity.

The documentation catalogue contains **280 qualified receiver/method families, covering 341 definition sites and 169 distinct method names**. It reconciles the historical 161-name selection with class/object ownership and includes the additional benchmark targets. This is the complete selected catalogue, not every public method in RDPro. Same-named methods on different owners remain separate; overloads on the same owner share an entry.

Execution covers **16 APIs across three rebuilt Scala source files**: Feature, RasterSchemaHelper and RasterMetadata. Scala classes and companion objects can emit multiple bytecode classes. There are 16 micro tasks and 16 puzzle tasks, each with three fresh private fixtures. This is local Scala execution; distributed Spark and the rest of RDPro are outside runtime coverage.

The baseline checks passed 96 trusted programs / 288 fixture checks: 32 reference solutions, 32 deliberately wrong-output solutions, and 32 correct-output solutions that omit the required API. These checks validate the benchmark baseline. They are not audience-model results and do not validate treatments that have not been generated.

## Five-condition comparison

| Condition | README | Source additions | Repair context |
| --- | --- | --- | --- |
| Original | Original | None | Public compiler/runtime feedback |
| README only | Fresh generated baseline D0 | None | Same feedback |
| Alias only | Original | Reviewed alias wrappers | Same feedback |
| Error hints only | Original | None | Same feedback plus matching development hints |
| Combined | Same D0 | Identical aliases | Identical matching hints |

Each condition receives the same 32 tasks and three audience trials: **480 units**. One initial attempt and at most one code repair are allowed per unit. A pass requires successful execution, independent output checks, and evidence that the required target method executed. Alias use and hint delivery are recorded separately; a passing alias/hint arm alone does not establish that the intervention caused the pass.

Report both first-attempt and within-one-repair scores, with unresolved/infrastructure cases reported separately. README context has an 8,000-character cap; both alias arms have the same 12,000-character alias-interface cap, with a pre-freeze check that all generated interfaces fit in full. Error hints are capped at 1,500 characters after an applicable failure. Exact delivered context is saved per attempt.

Alias proposals are generated in four batches covering the 16 source targets. Hints must cite one of four separate development compiler diagnostics; held-out fixture values, expected outputs and reference programs are excluded from model context. Proposal generation does not itself establish correctness. Compilation, wrapper probes, hint-delivery checks and source-bound treatment builds must pass before freezing audience evaluation.

## README update comparison

| Version | Construction | New authoring calls |
| --- | --- | --- |
| D0 — Unchanged generated README | Generate all 280 entries, then one deep-dive/rewrite pair on four selected APIs | 288, shared with the main study |
| D1 — Selected API refresh | Start from D0; apply another deep-dive/rewrite pair to those four sections | 8 |
| D2 — Full README refresh | Independently generate all 280 entries, then one deep-dive/rewrite pair on those same four APIs | 288 |

The selected APIs are Feature.append, Feature.readType, RasterMetadata.rescale (class), and RasterSchemaHelper.inferSchema (object). Selection is fixed from source/development evidence before audience evaluation. Every byte outside D1's four sections is preserved and verified.

This compares **update policies and incremental cost**. D1 intentionally has an extra review pass on its selected entries, so the experiment does not isolate selection scope at equal review depth. Three audience trials repeat evaluation of fixed documents; they do not provide three independent document generations. Report the preregistered task groups separately: seven selected-only cases, one mixed selected/unaffected case, and 24 unaffected cases.

Each whole-catalogue author request uses fixed source facts and shared original-document context. Earlier generated entries are not fed into later requests. Running those requests sequentially therefore does not itself create a chain of documentation dependencies; this experiment changes which sections are regenerated, not their processing order.

The README comparison adds **288 audience units**: the same 32 tasks × three versions × three trials. Documents and treatments must all be frozen before inspecting held-out audience outcomes.

## What is sent to the model

README authoring receives the exact qualified API identity, signatures, source comments, bounded source windows, selected public test examples, examples from original documents, a fixed shared public-document excerpt, the project profile and the authoring prompt. It does not receive the whole source checkout as one request. The 280 prepared requests total about 5.38 million characters; actual billed tokens are known only after provider responses.

Deep-dive requests additionally receive the current selected README section and its separate development diagnostic, when available. Rewriting receives the saved deep-dive result. One deep-dive and one rewrite are allowed per selected entry per pass; no hidden iterative repair loop is included in this budget.

Total-output limits are 4,096 tokens for authoring/rewriting, 8,192 for deep dives/proposals, and 2,048 for audience attempts. Authoring refuses incomplete, empty or refusal responses and does not silently retry them. Authoring checks document structure and provenance; it does not compile or semantically validate its example snippets. Independent runtime evaluation remains a separate stage.

Audience requests receive only the public task contract, selected README context, any applicable alias interface, and—after a failure—public feedback and matching development hints. Private oracles, fixtures and reference solutions stay out of these requests.

## Review and output locations

The shared implementation branch is `evaluation/2026-09-22-rdpro-full-pipeline`. The local study folder is named `2026-09-22-gpt-5.3-codex-broad-study`, under the workspace's `03_Experiments/rdpro/` directory.

| Study-relative location | Contents / state |
| --- | --- |
| `attachment.json` | Five local source worktrees and pinned baseline |
| `development/authoring_inputs/` | Qualified manifest, selected subset, shared context and development diagnostics |
| `development/readme_baseline_authoring/session.json` | Exact 280 prepared author requests; no paid calls yet |
| `development/readme_full_refresh_authoring/session.json` | Same 280 prompt bodies in a separate independent generation session |
| `development/library_improvement_preview/` | Four exact alias/hint request previews; no paid calls yet |
| `development/reference_validation_v1/` | Passed baseline controls and preserved raw evidence |
| `evaluation_assets/` | Source build, execution, trace and checker code |
| `bank/` | Private fixtures, oracles and trusted controls; local only |
| `development/shared_budget.json` | Created on the first authorized reservation; absent during preparation |

Execution will add phase request/response receipts, README outputs, reviewed treatment commits, source-bound runtime manifests, frozen protocols and audience result directories. A run index will link the exact locations once they exist. A planned path is not evidence that its stage has run.

See the shared [configuration guide](../../../docs/CONFIGURATION.md), [output guide](../../../docs/OUTPUTS.md), [scoring definitions](../../../docs/SCORING.md), and [completed pilot](../2026-09-21-gpt-5.3-codex-five-conditions/README.md). The other five libraries are listed in the [study index](../../README.md); they remain baseline preparations without treatment/evaluation results.
