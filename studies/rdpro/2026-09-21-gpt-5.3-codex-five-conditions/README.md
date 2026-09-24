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

## Shared evaluation, separate RDPro source

The five remote condition refs have been verified against their published snapshot commits, whose trees match the measured versions.

AIDEAL holds the shared [development prompt](development_system_prompt.txt), [public task contracts](public_tasks.json), [model/budget settings](protocol.json), [checker and offline tests](harness/README.md), [condition runner](../../../workflow/condition_evaluation.py) and [audited results](RESULTS.md). The companion [AIDEAL-RDPro repository](https://github.com/ZhuochengShang/AIDEAL-RDPro) holds clean source snapshots of the five RDPro conditions below. This keeps one evaluation implementation and protocol across all source versions.

| Condition | RDPro remote branch | Published snapshot commit | Historical measured commit |
|---|---|---|---|
| Original | [`study/2026-09-21-gpt-5.3-codex/original`](https://github.com/ZhuochengShang/AIDEAL-RDPro/tree/study/2026-09-21-gpt-5.3-codex/original) | [`5ee41a6dc37e`](https://github.com/ZhuochengShang/AIDEAL-RDPro/commit/5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8) | `547f7f912131` |
| Generated README only | [`study/2026-09-21-gpt-5.3-codex/readme-only`](https://github.com/ZhuochengShang/AIDEAL-RDPro/tree/study/2026-09-21-gpt-5.3-codex/readme-only) | [`41a302b39dd7`](https://github.com/ZhuochengShang/AIDEAL-RDPro/commit/41a302b39dd7d9260842827d22bf7fa48dadcad7) | `7ab580c744db` |
| Aliases only | [`study/2026-09-21-gpt-5.3-codex/alias-only`](https://github.com/ZhuochengShang/AIDEAL-RDPro/tree/study/2026-09-21-gpt-5.3-codex/alias-only) | [`80ba93d32e9a`](https://github.com/ZhuochengShang/AIDEAL-RDPro/commit/80ba93d32e9aff65fa12e730abb66a67663b9e35) | `dcaff7fbe2ce` |
| Error hints only | [`study/2026-09-21-gpt-5.3-codex/error-hints-only`](https://github.com/ZhuochengShang/AIDEAL-RDPro/tree/study/2026-09-21-gpt-5.3-codex/error-hints-only) | [`1f9e07195264`](https://github.com/ZhuochengShang/AIDEAL-RDPro/commit/1f9e0719526455a6a89751869281df91eabeb5c0) | `bc55f6b312c0` |
| Combined | [`study/2026-09-21-gpt-5.3-codex/combined`](https://github.com/ZhuochengShang/AIDEAL-RDPro/tree/study/2026-09-21-gpt-5.3-codex/combined) | [`cdb03c2e8343`](https://github.com/ZhuochengShang/AIDEAL-RDPro/commit/cdb03c2e8343c80c48ab60d268c9ad3013e3570b) | `0db05e0f5a49` |

**Identical source trees, different commit history.** A malformed historical Git tree (`90b33f9e36ee3d4f833f496f37c50530aba8571c`) has a `duplicateEntries` error. To avoid distributing that invalid ancestry, the companion repository uses a new baseline snapshot commit and four treatment descendants. Each published tree ID equals its measured condition's tree ID, preserving filenames, file bytes and modes; the original historical ancestry is not shipped. Historical measured commits and local `aideal/...` branch names remain unchanged in [source_versions.json](source_versions.json). The new `published_revision` fields identify the downloadable snapshots, not the original measured executions.

The source-root `README.md` and any companion-repository navigation README are **not the selected generated README treatment**. README-only and Combined use `.aideal/treatments/README.md`, whose exact selected bytes are also exported as [GENERATED_README.md](GENERATED_README.md). Original, Aliases-only and Error-hints-only use the separately selected original documentation, still omitted here. Alias-enabled conditions additionally compile `cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/AidealAliases0001.scala` and expose `.aideal/treatments/ALIASES.md`; hint-enabled conditions select `.aideal/treatments/error_hints.json` after a matching checked failure.

### One clone, five worktrees

After the remote refs are available, these commands create five source worktrees at the published snapshot commits. Their trees match the measured versions; their commit identities differ. Run them from an empty parent directory:

```sh
git clone --branch main --no-checkout https://github.com/ZhuochengShang/AIDEAL-RDPro.git AIDEAL-RDPro
git -C AIDEAL-RDPro worktree add -b study/2026-09-21-gpt-5.3-codex/original ../rdpro-original 5ee41a6dc37ebe5f63bf7a3a0b74c5483460b9c8
git -C AIDEAL-RDPro worktree add -b study/2026-09-21-gpt-5.3-codex/readme-only ../rdpro-readme-only 41a302b39dd7d9260842827d22bf7fa48dadcad7
git -C AIDEAL-RDPro worktree add -b study/2026-09-21-gpt-5.3-codex/alias-only ../rdpro-alias-only 80ba93d32e9aff65fa12e730abb66a67663b9e35
git -C AIDEAL-RDPro worktree add -b study/2026-09-21-gpt-5.3-codex/error-hints-only ../rdpro-error-hints-only 1f9e0719526455a6a89751869281df91eabeb5c0
git -C AIDEAL-RDPro worktree add -b study/2026-09-21-gpt-5.3-codex/combined ../rdpro-combined cdb03c2e8343c80c48ab60d268c9ad3013e3570b
```

The checkout names above are examples. These commands provide source worktrees for inspection and building; they do not create AIDEAL attachment/application records, dependency manifests, private inputs or a runnable configuration. Use the shared [harness tests and prerequisites](harness/README.md) for the 16 offline checks. Full repetition still needs the private bank/control programs, original documentation, pinned Java/Scala/Spark dependencies, treatment installation metadata, rebuilt source-bound backends and a new local configuration/freeze. The new commit IDs must be recorded in that new freeze; historical source receipts must not be relabeled or rewritten. The current preparation recipe also expects the historical bank/documentation pointer and selected README provenance described in that guide; there is no automatic bootstrap from this review export.

`run-conditions --condition original` selects an arm in a supplied freeze; it does not switch branches, and the controller still verifies every configured backend. Reusing a run output resumes saved work. A fresh output starts new model generation with the configured shared budget; it is a new stochastic run, not a deterministic replay of the historical outputs.

## What changed across conditions

| Condition | Solver documentation | Library source | Additive public context |
|---|---|---|---|
| Original | Original README | Original | Shared task/helper and checker feedback |
| Generated README only | Fixed Generated README | Original | Shared context |
| Aliases only | Original README | Original plus wrappers | Minimal alias interface |
| Error hints only | Original README | Original | Hints eligible after matching checked failure |
| Combined | Same Generated README | Same wrappers | Same interface and eligible hints |

The separate source-refactor study is excluded. The original source remains at baseline `547f7f912131a8032f6b5d26991415a5faf05cef`. The other measured commits are listed in [source_versions.json](source_versions.json). Those historical measured commits are mapped to new tree-identical snapshot commits in the companion [AIDEAL-RDPro source refs](https://github.com/ZhuochengShang/AIDEAL-RDPro) above, **not commits in the AIDEAL toolkit branch**. Historical ancestry is not shipped; source directories are not duplicated in this evaluation export. The aliases target `cg/src/main/scala/edu/ucr/cs/bdlab/beast/geolite/AidealAliases0001.scala`. Installed README/interface/hint metadata lives under `.aideal/treatments/` in its assigned arms.

The original documentation contains local home paths and is **omitted without rewriting it**. Its exact hash/size remain in the manifest. The included Generated README passed the export path/credential checks and remains byte-identical. It was reused from an earlier artifact, not authored by the Codex proposal and not replaced with the earlier repaired README. It lacks dedicated `readType` coverage; the experiment did not repair that omission after seeing results.

## Prompt, code and independent evaluation

One development request received four bounded source/API windows, package/import context, configuration/profile/catalogue information and four separate development compiler diagnostics. It generated four forwarding aliases, four unverified hints and one refactor review candidate. Only the aliases/hints plus the reused README entered this five-condition bundle; the refactor candidate was not installed here. The proposal had a 4,096-token cap and used 8,779 input / 3,425 output tokens, including 965 reasoning tokens.

The audience model instead received a public task, public helper contract, retrieved README sections, permitted alias interface and any eligible post-failure hints. It returned a Scala 2.12 `solve` body. The trusted local checker compiled against the exact arm's source-bound overlay, ran three private fixtures per case, checked numerical outputs independently, and checked canonical JVM method descriptors/class origins. The model did not invent its own pass criteria. Compiler diagnostics or generic checker feedback could trigger one repair; private expected values stayed outside model prompts. A subprocess runner is not an OS sandbox.

Shared audience limits were 2,048 generated tokens (reasoning included), one repair, one provider attempt per round, low reasoning, and 8,000/2,500/1,500-character documentation/alias/hint caps. Temperature 0 was a controller compatibility placeholder and was omitted from the API call; the provider default is not claimed to be deterministic. Development and audience calls shared one $5 reservation ledger.

**No hint matched or was delivered in the completed run.** Hints-only's extra repaired puzzle cannot be credited to hint content. The exported hints deliberately retain their defects: `ObjectInputStream` framing is not a drop-in fit for the public headerless tag-stream contract; `???` is an unfinished Scala placeholder; and the numTiles hint optionally mentions an alias absent in hints-only. Alias-name mentions in candidate text are not proof that wrappers executed. Canonical target traces include transitive calls and aggregate across fixtures.

## Review code or reproduce a new run

Read the [condition setup](../../../workflow/condition_setup.py), [public-context builder](../../../workflow/condition_context.py), [condition runner](../../../workflow/condition_evaluation.py) and [reporting formulas](../../../workflow/condition_reporting.py), then the frozen local [harness](harness/README.md). Compare filenames/hashes against `protocol.json`; a changed implementation must not be presented as the old frozen study.

The included synthetic tests exercise adapter/configuration contracts without hosted-model or RDPro library execution. Full repetition requires separately provisioning the exact RDPro source versions, permitted dependencies, omitted original documentation and private bank, then building and freezing a **new local configuration**. Absolute runtime paths are part of the historical identity, so this export cannot recreate that identity just by moving files. Do not regenerate fixtures or replace missing inputs and label the result an exact rerun.
