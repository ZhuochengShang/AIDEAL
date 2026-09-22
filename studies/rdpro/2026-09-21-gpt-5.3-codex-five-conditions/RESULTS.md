# Audited RDPro Codex results

All **40 audience units** reached verified terminal outcomes; all **120 trusted controls** passed their expected validation criteria. The native report and independently calculated metrics agree. Frozen study: `ed877ae454bc10bc69e27ed7cdc42b59d398f7919ad10ad94084b3dd08706f95`.

| Condition | Micro first | Micro within one repair | Puzzle first | Puzzle within one repair | Total first → within |
|---|---:|---:|---:|---:|---:|
| Original | 3/4 | 3/4 | 1/4 | 1/4 | 4/8 → 4/8 |
| Generated README only | 3/4 | 3/4 | 2/4 | 2/4 | 5/8 → 5/8 |
| Aliases only | 3/4 | 3/4 | 1/4 | 1/4 | 4/8 → 4/8 |
| Error hints only | 3/4 | 3/4 | 1/4 | 2/4 | 4/8 → 5/8 |
| Combined | 3/4 | 3/4 | 1/4 | 1/4 | 4/8 → 4/8 |

Each condition has **four microtasks and four puzzles**, one trial each. First-attempt percentage is `first-attempt passes / 4 × 100` per kind; within-budget percentage is `passes by the permitted repair / 4 × 100`. Thus all micro scores are 75%; puzzle scores are 25% or 50%. Across conditions, 21 units passed immediately and one additional unit passed after repair, for 22/40 within budget. This overall total is a cross-condition count, not an independent 40-case accuracy sample.

Against Original, README-only and hints-only each recover one puzzle with no regressions: +25 percentage points for puzzles. They recover **different** puzzles; their direct comparison has one recovery and one regression, despite equal final totals. Complete paired lift is `(recoveries − regressions) / 4 × 100` per kind. With one trial and four cases per kind, one outcome changes the percentage by 25 points. These observations do not establish a stable or general treatment effect.

## Actual exposure limits

- **Hints:** each hint-enabled condition had four eligible repair rounds, but zero matches and zero delivered hint characters. Hints-only's one repaired success cannot be attributed to generated hint content. This run tested the matching policy, without observing the effect of a delivered hint.
- **Aliases:** interface context was delivered in all 12 rounds for Aliases only and all 12 for Combined, without interface clipping. Four candidate outputs in four units in each arm mention at least one alias name. This is lexical evidence, possibly in comments/strings, not proof of wrapper execution. The observer records canonical target methods, not wrapper calls.
- **Documents versus responses:** all 59 audience prompts used clipped documentation under the 8,000-character cap. There were zero truncated/incomplete model responses, empty-code responses or refusals. Document clipping is distinct from response truncation. The Generated README is fixed historical input with missing dedicated readType sections.
- **Checker scope:** target reachability is unioned across fixtures and includes transitive calls; it does not prove causal target use in each numerical answer. Private numerical checks remain independent of model-written code.

## Failures

The 18 final failing units comprise 11 compilation failures, six runtime failures and one executed solution that failed both the numerical/output contract and required-method reachability. Across 59 executions including repairs there were 22 passes, 24 compilation failures, 12 runtime failures and one combined numerical/target failure.

Recurring fixed diagnostic labels include an incorrect package reference for `RasterSchemaHelper` and class-lookup/reflection failures. These identify review targets, not proof that a README caused an error. `results.json` includes aggregate categories only; no raw diagnostics, private fixture values, reference code or expected arrays are published.

## Usage and cost

| Scope | Settled calls | Input tokens | Output tokens, including reasoning | Usage-based cost |
|---|---:|---:|---:|---:|
| Development proposal | 1 | 8,779 | 3,425 | $0.06331325 |
| Audience | 59 | 154,280 | 35,520 | $0.64590680 |
| Combined | 60 | 163,059 | 38,945 | **$0.70922005** |

The 59 audience calls are 40 initial requests plus 19 repair requests. All 60 reservations settled; none remain uncertain. Cached-input pricing was applied to 77,056 audience input tokens; output reasoning is included once. Total cost remained below the shared $5 cap. These are estimates from saved provider usage at the recorded prices, not an invoice.

The independent audit also verified 30 protected historical hashes and the exact source/runtime/request–response–candidate–checker chains. Its aggregate facts and source-file hashes are exported in [results.json](results.json); local paths and the private full evidence collection are omitted. The earlier original/refactor study and held three-README pilot remain separate.
