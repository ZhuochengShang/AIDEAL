# RDPro · GPT-5.3-Codex · five-condition pilot · 2026-09-21

**Study name:** `2026-09-21-rdpro-gpt-5.3-codex-five-conditions`

The name records the experiment date in America/Los_Angeles, library, model and comparison design. The five conditions are Original, Generated README only, Aliases only, Error hints only and Combined. Each has four microtasks and four puzzles: 40 task-condition evaluations, with one trial and at most one repair.

Older `_v1` filenames in the local evidence are historical storage labels. They are not RDPro versions or model versions. Their paths stay unchanged because the frozen study binds them. Use this descriptive study name and frozen identity `ed877ae454bc10bc69e27ed7cdc42b59d398f7919ad10ad94084b3dd08706f95` when comparing future experiments.

This package records a completed **five-condition, eight-case, one-trial pilot** using GPT-5.3-Codex. The independent audit verified all **40 terminal audience outcomes**, all **120 trusted controls**, and the saved source/runtime/request/checker identities. Completed includes failures: **22 of 40 units passed within the one-repair budget**.

This is a **portable review export, not a standalone rerun configuration**. Private fixtures, expected answers, reference/negative-control programs, runtime binaries and local absolute paths are omitted. `protocol.json` describes the measured protocol; it cannot be passed to `freeze-conditions`. The full local audit is identified by hash, not copied with its machine-specific paths.

## Start here

| File | What to review |
|---|---|
| [RESULTS.md](RESULTS.md) | Actual first-attempt/within-budget scores, costs, failures and interpretation limits |
| [results.json](results.json) | Audited aggregate metrics, paired comparisons, usage and exposure counts |
| [protocol.json](protocol.json) | Safe model/budget settings and the exact frozen/source/controller identities |
| [source_versions.json](source_versions.json) | The five real RDPro library commits and study-relative source mapping |
| [public_tasks.json](public_tasks.json) | Only the public task/contract/required-API fields; no test inputs or answers |
| [aliases.scala](aliases.scala), [ALIASES.md](ALIASES.md), [error_hints.json](error_hints.json) | Actual installed generated artifacts, copied byte-identically |
| [development_system_prompt.txt](development_system_prompt.txt) | Exact saved development system instruction, extracted without alteration |
| [GENERATED_README.md](GENERATED_README.md) | Exact selected historical Generated README, reused by this pilot |
| [artifact_manifest.json](artifact_manifest.json) | Byte hashes, original-README omission and export exclusions |
| [harness/README.md](harness/README.md) | Frozen checker/build sources and offline tests; requirements for a separately provisioned rerun |

The branch `evaluation/2026-09-21-rdpro-gpt-5.3-codex-five-conditions` adds this study export and its reviewed harness to the published toolkit. Its **complete branch inventory** is maintained separately by the branch publication process and includes study-export files. The `main` branch retains its original toolkit/source-only manifest policy. This package's artifact manifest covers the named evidence artifacts; it is not a substitute for that complete branch inventory.

## What changed across conditions

| Condition | Solver documentation | Library source | Additive public context |
|---|---|---|---|
| Original | Original README | Original | Shared task/helper and checker feedback |
| Generated README only | Fixed Generated README | Original | Shared context |
| Aliases only | Original README | Original plus wrappers | Minimal alias interface |
| Error hints only | Original README | Original | Hints eligible after matching checked failure |
| Combined | Same Generated README | Same wrappers | Same interface and eligible hints |

The separate source-refactor study is excluded. The original source remains at baseline `547f7f912131a8032f6b5d26991415a5faf05cef`. The other measured commits are listed in [source_versions.json](source_versions.json). Those are commits in the separate RDPro library repository, **not commits in the AIDEAL toolkit branch**; source directories are not silently bundled here. The aliases target `cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/AidealAliases0001.scala`. Installed README/interface/hint metadata lives under `.aideal/treatments/` in its assigned arms.

The original documentation contains local home paths and is **omitted without rewriting it**. Its exact hash/size remain in the manifest. The included Generated README passed the export path/credential checks and remains byte-identical. It was reused from an earlier artifact, not authored by the Codex proposal and not replaced with the earlier repaired README. It lacks dedicated `readType` coverage; the experiment did not repair that omission after seeing results.

## Prompt, code and independent evaluation

One development request received four bounded source/API windows, package/import context, configuration/profile/catalogue information and four separate development compiler diagnostics. It generated four forwarding aliases, four unverified hints and one refactor review candidate. Only the aliases/hints plus the reused README entered this five-condition bundle; the refactor candidate was not installed here. The proposal had a 4,096-token cap and used 8,779 input / 3,425 output tokens, including 965 reasoning tokens.

The audience model instead received a public task, public helper contract, retrieved README sections, permitted alias interface and any eligible post-failure hints. It returned a Scala 2.12 `solve` body. The trusted local checker compiled against the exact arm's source-bound overlay, ran three private fixtures per case, checked numerical outputs independently, and checked canonical JVM method descriptors/class origins. The model did not invent its own pass criteria. Compiler diagnostics or generic checker feedback could trigger one repair; private expected values stayed outside model prompts. A subprocess runner is not an OS sandbox.

Shared audience limits were 2,048 generated tokens (reasoning included), one repair, one provider attempt per round, low reasoning, and 8,000/2,500/1,500-character documentation/alias/hint caps. Temperature 0 was a controller compatibility placeholder and was omitted from the API call; the provider default is not claimed to be deterministic. Development and audience calls shared one $5 reservation ledger.

**No hint matched or was delivered in the completed run.** Hints-only's extra repaired puzzle cannot be credited to hint content. The exported hints deliberately retain their defects: `ObjectInputStream` framing is not a drop-in fit for the public headerless tag-stream contract; `???` is an unfinished Scala placeholder; and the numTiles hint optionally mentions an alias absent in hints-only. Alias-name mentions in candidate text are not proof that wrappers executed. Canonical target traces include transitive calls and aggregate across fixtures.

## Review code or reproduce a new run

Read the [condition setup](../../../workflow/condition_setup.py), [public-context builder](../../../workflow/condition_context.py), [condition runner](../../../workflow/condition_evaluation.py) and [reporting formulas](../../../workflow/condition_reporting.py), then the frozen local [harness](harness/README.md). Compare filenames/hashes against `protocol.json`; a changed implementation must not be presented as the old frozen study.

The included synthetic tests exercise adapter/configuration contracts without hosted-model or RDPro library execution. Full repetition requires separately provisioning the exact RDPro source versions, permitted dependencies, omitted original documentation and private bank, then building and freezing a **new local configuration**. Absolute runtime paths are part of the historical identity, so this export cannot recreate that identity just by moving files. Do not regenerate fixtures or replace missing inputs and label the result an exact rerun.
